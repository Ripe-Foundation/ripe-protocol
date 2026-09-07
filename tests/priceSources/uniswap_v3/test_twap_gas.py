"""Required canonical-runtime stress; large synthetic rings are built once/reused."""
import time
import json
import platform
from types import SimpleNamespace

import boa
import pytest
from conf_utils import advance_timelock_blocks

from .graph import make_graph,source,admit,params,rotate_desk,register
from .pools import organic_pool,seed_ring,search_indices,assert_runtime,SLOTS
from .gas_tools import cold,calls,storage_reads,walk
from .raw import Raw,words,word,selector

pytestmark=pytest.mark.gas


@pytest.fixture(scope='module')
def gas_lab():
    started=time.monotonic()
    g=make_graph();f,p,a,w,actor,ref=organic_pool(g)
    ring=seed_ring(p,65535)
    anchor=boa.load('contracts/mock/MockChainlinkFeed.vy',2500*10**18)
    s=source(g,f.address,w,anchor)
    admit(g,s,a.address,params(p,window=14400))
    g.desk.syncTokenScale(a.address,sender=g.local)
    print(f'TWAP_GAS_SETUP python={platform.python_version()} machine={platform.machine()} seconds={time.monotonic()-started:.3f} pool_runtime_sha256={assert_runtime(p)} source_bytes={len(boa.env.get_code(s.address))} synthetic_ring=65535')
    return SimpleNamespace(g=g,s=s,p=p,a=a,w=w,anchor=anchor,ring=ring)


def set_config(lab,window=14400,local=0):
    if tuple(lab.s.getFeedConfig(lab.a.address).params)!=params(lab.p,window=window,quote_age=local):
        lab.s.updatePriceFeed(lab.a.address,params(lab.p,window=window,quote_age=local),sender=lab.g.gov)
        advance_timelock_blocks(lab.s.actionTimeLock())
        assert lab.s.confirmPriceFeedUpdate(lab.a.address,sender=lab.g.gov)


def test_gas_instrumentation_cold_warm_cold_and_transaction_addresses():
    probe=boa.loads('# @version 0.4.3\na: public(uint256)\n@deploy\ndef __init__():\n    self.a=42\n')
    for _ in range(2):
        cold(probe)
        state=boa.env.evm.vm.state
        assert state.is_address_warm(bytes.fromhex(probe.address[2:]))
        assert state.is_address_warm(bytes.fromhex(str(boa.env.eoa)[2:]))
        assert all(state.is_address_warm(i.to_bytes(20,'big')) for i in range(1,10))
        assert not state.is_storage_warm(bytes.fromhex(probe.address[2:]),0)
        assert probe.a()==42;cold_gas=probe._computation.get_gas_used()
        assert probe.a()==42;warm_gas=probe._computation.get_gas_used()
        assert cold_gas-warm_gas==2000
    print(f'TWAP_SLOAD_CONTROL cold={cold_gas} warm={warm_gas} reset_cold={cold_gas}')


@pytest.mark.parametrize('count,index,initialized',[(65535,None,None),(20000,None,None),(65535,12345,None),(65535,None,30000)])
@pytest.mark.parametrize('window',[1800,14400])
def test_canonical_deep_cold_ring_reads(gas_lab,count,index,initialized,window):
    l=gas_lab
    ring=l.ring if count==65535 and index is None and initialized is None else seed_ring(l.p,count,index=index,initialized=initialized)
    set_config(l,window)
    expected_indices=search_indices(ring,window)
    cold(l.g.desk)
    with storage_reads() as reads:
        assert l.g.desk.getPrice(l.a.address,True)==2500*10**18
    comp=l.g.desk._computation
    child=calls(comp,l.s)[0]
    observe=[c for c in calls(child,l.p) if bytes(c.msg.data[:4])==selector('observe(uint32[])')][0]
    touched={slot-SLOTS['observations'] for address,slot in reads if address==bytes.fromhex(l.p.address[2:]) and slot>=SLOTS['observations']}
    assert set(expected_indices)<=touched
    assert len(touched)>=20 and len(expected_indices)//2>=10
    assert child.msg.gas==250000 and not child.is_error
    assert child.output==words(2500*10**18,1)
    assert child.get_gas_used()<250000
    print(f'TWAP_COLD ring={count} index={ring["index"]} initialized={ring["initialized"]} window={window} depth={len(expected_indices)//2} observation_slots={len(touched)} source={child.get_gas_used()} desk={comp.get_gas_used()} observe={observe.get_gas_used()} source_target_overrun={max(0,child.get_gas_used()-210000)}')


@pytest.mark.parametrize('local',[0,3600])
@pytest.mark.parametrize('target',['source','desk'])
def test_cold_and_in_transaction_warm_policy_paths(gas_lab,local,target):
    l=gas_lab;set_config(l,local=local)
    probe=boa.load('tests/priceSources/uniswap_v3/WarmProbe.vy')
    dest=l.s if target=='source' else l.g.desk
    data=l.s.getPriceAndHasFeed.prepare_calldata(l.a.address) if target=='source' else l.g.desk.getPrice.prepare_calldata(l.a.address,True)
    cold(dest)
    if target=='source':
        assert l.s.getPriceAndHasFeed(l.a.address)==(2500*10**18,True)
        direct=l.s._computation
    else:
        assert l.g.desk.getPrice(l.a.address,True)==2500*10**18
        direct=l.g.desk._computation
    source_call=calls(direct,l.s)[0]
    assert len(source_call.children)==(11 if target=='source' and local==0 else 9)
    assert source_call.get_gas_used()<250000
    cold(probe)
    before=boa.env.evm.vm.state
    assert not before.is_address_warm(bytes.fromhex(dest.address[2:]))
    result=probe.twice(dest.address,data)
    assert result[0]==result[1] and len(result[0]) in (32,64)
    root=probe._computation
    children=root.children
    assert len(children)==2
    child_costs=[c.get_gas_used() for c in children]
    source_costs=[calls(c,l.s)[0].get_gas_used() for c in children]
    assert source_costs[1]<source_costs[0]
    dependency_costs=[[{'selector':bytes(d.msg.data[:4]).hex(),'gas':d.get_gas_used()} for d in calls(c,l.s)[0].children] for c in children]
    print('TWAP_DEPENDENCIES '+json.dumps({'target':target,'local':local,'call_counts':list(map(len,dependency_costs)),'cold_warm_calls':dependency_costs},sort_keys=True))
    print(f'TWAP_WARM target={target} local={local} source_cold={source_call.get_gas_used()} direct_total={direct.get_gas_used()} transaction_children={child_costs} source_children={source_costs} wrapper_overhead={root.get_gas_used()-sum(child_costs)}')


@pytest.mark.parametrize('fault',['burn','empty','extra','invalid_round'])
def test_expensive_successful_observe_then_late_dependency_failure(gas_lab,fault):
    l=gas_lab
    rounds={'burn':None,'empty':b'','extra':words(1,2500*10**8,0,boa.env.timestamp,1)+b'\x00','invalid_round':words(0,2500*10**8,0,boa.env.timestamp,1)}
    Raw({'decimals()':word(8),'latestRoundData()':rounds[fault]},address=l.anchor.address)
    cold(l.g.desk)
    assert l.g.desk.getPrice(l.a.address)==0
    comp=l.g.desk._computation;child=calls(comp,l.s)[0]
    observe=[c for c in calls(child,l.p) if bytes(c.msg.data[:4])==selector('observe(uint32[])')][0]
    assert not observe.is_error and len(observe.output)==256 and observe.get_gas_used()>80000
    assert not child.is_error and child.output==words(0,1)
    assert child.get_gas_used()<250000
    print(f'TWAP_LATE_FAILURE kind={fault} observe={observe.get_gas_used()} source={child.get_gas_used()} desk={comp.get_gas_used()}')


def test_legitimate_old_is_distinct_from_exhausted_observe(gas_lab):
    l=gas_lab
    seed_ring(l.p,8,spacing=1)
    cold(l.g.desk)
    assert l.g.desk.getPrice(l.a.address)==0
    child=calls(l.g.desk._computation,l.s)[0]
    observe=[c for c in calls(child,l.p) if bytes(c.msg.data[:4])==selector('observe(uint32[])')][0]
    assert observe.is_error and b'OLD' in observe.output
    assert observe.get_gas_used()<120000
    assert child.output==words(0,1)


def test_cold_current_desk_rotation(gas_lab):
    l=gas_lab;g=l.g;old=g.desk
    rotate_desk(g);register(g.desk,l.s,g.gov)
    g.desk.syncTokenScale(l.a.address,sender=g.local)
    cold(g.desk)
    assert g.desk.getPrice(l.a.address,True)==2500*10**18
    child=calls(g.desk._computation,l.s)[0]
    assert child.output==words(2500*10**18,1)
    print(f'TWAP_ROTATED source={child.get_gas_used()} desk={g.desk._computation.get_gas_used()}')
    g.desk=old


def test_final_deployed_size_coverage_and_noop_snapshot(gas_lab):
    l=gas_lab
    deployed=len(boa.env.get_code(l.s.address))
    assert deployed<=24576
    cold(l.s)
    assert l.s.hasPriceFeed(l.a.address,gas=75000)
    coverage=l.s._computation.get_gas_used()
    assert l.s._computation.children==[]
    cold(l.s)
    assert not l.s.addPriceSnapshot(l.a.address,gas=150000)
    snapshot=l.s._computation.get_gas_used()
    assert l.s._computation.children==[]
    print(f'TWAP_SIZE deployed={deployed} eip170_headroom={24576-deployed} target_overrun={max(0,deployed-22500)} coverage={coverage} snapshot={snapshot} compiler=Vyper-0.4.3 optimize=gas evm=prague constructor_action_delay=2 expiration_duration=100')


@pytest.mark.parametrize('fault',['hq_burn','policy_burn','scale_mismatch','scale_burn'])
def test_early_dependency_failure_reserve_at_real_call_positions(gas_lab,fault):
    l=gas_lab
    if fault in ('hq_burn','policy_burn'):
        mock=boa.load('tests/priceSources/uniswap_v3/EarlyFault.vy',l.g.desk,l.g.mc)
        target=l.g.hq if fault=='hq_burn' else l.g.mc
        boa.env.set_code(target.address,boa.env.get_code(mock.address))
    elif fault=='scale_mismatch':
        # Actual desk's real scale getter cannot burn gas: poison the scale with
        # an explicitly synthetic storage write, preserving its full runtime.
        position=l.g.desk.compiler_data.storage_layout['storage_layout']['tokenScale']['slot']
        from eth_utils import keccak
        slot=int.from_bytes(keccak(words(position,l.a.address)),'big')
        boa.env.evm.set_storage(l.g.desk.address,slot,10**6)
        assert l.g.desk.tokenScale(l.a.address)==10**6
    else:
        # A malformed desk getter is a separate direct-source fault fixture.
        Raw({'tokenScale(address)':None},address=l.g.desk.address)
        cold(l.s)
        assert l.s.getPriceAndHasFeed(l.a.address,gas=250000)==(0,True)
        child=l.s._computation
        assert not child.is_error and child.get_gas_used()<250000
        print(f'TWAP_EARLY_FAILURE fault={fault} source={child.get_gas_used()}')
        return
    cold(l.g.desk)
    assert l.g.desk.getPrice(l.a.address)==0
    child=calls(l.g.desk._computation,l.s)[0]
    assert child.msg.gas==250000 and child.output==words(0,1) and not child.is_error
    assert calls(child,l.p)==[]
    print(f'TWAP_EARLY_FAILURE fault={fault} source={child.get_gas_used()} desk={l.g.desk._computation.get_gas_used()}')


@pytest.mark.parametrize('tick,reverse',[(524287,False),(-524287,True)])
def test_deep_ring_with_dense_tick_bits_and_both_quote_precision_branches(gas_lab,tick,reverse):
    """Nineteen selected multiplier bits; positive quotes in both token orders."""
    from .compiled import deploy
    l=gas_lab;g=l.g;old=g.desk
    seed_ring(l.p,65535,tick=tick)
    asset,weth=(l.w,l.a) if reverse else (l.a,l.w)
    try:
        rotate_desk(g)
        s=source(g,l.p.factory(),weth,l.anchor)
        ref=deploy('v3','Reference')
        sqrt=ref.sqrt(tick)
        assert (sqrt>2**128-1)==(not reverse)
        expected=ref.quote(tick,10**18,asset.address,weth.address)*2500
        assert admit(g,s,asset.address,params(l.p,window=14400))==expected>0
        g.desk.syncTokenScale(asset.address,sender=g.local)
        cold(s)
        assert s.getPriceAndHasFeed(asset.address)==(expected,True)
        direct=s._computation.get_gas_used()
        cold(g.desk)
        assert g.desk.getPrice(asset.address,True)==expected
        comp=g.desk._computation;child=calls(comp,s)[0]
        assert child.msg.gas==250000 and child.output==words(expected,1) and not child.is_error
        assert child.get_gas_used()<250000
        print(f'TWAP_DENSE_TICK tick={tick} reverse={reverse} direct_source={direct} forwarded_source={child.get_gas_used()} desk={comp.get_gas_used()} source_target_overrun={max(0,direct-210000,child.get_gas_used()-210000)}')
    finally:
        g.desk=old
