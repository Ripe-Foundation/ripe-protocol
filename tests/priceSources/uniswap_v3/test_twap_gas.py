"""Required canonical-runtime stress; large synthetic rings are built once/reused."""
import time
import json
import platform
from types import SimpleNamespace

import boa
import pytest
from conf_utils import advance_timelock_blocks

from .graph import make_graph,source,admit,params,temporary_desk,register,weth_price_source
from .helpers import settings
from .pools import organic_pool,seed_ring,search_indices,assert_runtime,SLOTS
from .gas_tools import cold,calls,storage_reads,walk,assert_source_budget,assert_deployed_size
from .raw import Raw,words,word,selector

pytestmark=pytest.mark.gas


@pytest.fixture(scope='module')
def gas_lab():
    started=time.monotonic()
    g=make_graph();f,p,a,w,actor,ref=organic_pool(g)
    ring=seed_ring(p,65535)
    anchor=boa.load('contracts/mock/MockChainlinkFeed.vy',2500*10**18)
    weth_price_source(g,w,anchor)
    s=source(g,f.address)
    admit(g,s,a.address,params(p,window=14400))
    g.desk.syncTokenScale(a.address,sender=g.local)
    print(f'TWAP_GAS_SETUP python={platform.python_version()} machine={platform.machine()} seconds={time.monotonic()-started:.3f} pool_runtime_sha256={assert_runtime(p)} source_bytes={len(boa.env.get_code(s.address))} synthetic_ring=65535')
    return SimpleNamespace(g=g,s=s,p=p,a=a,w=w,anchor=anchor,ring=ring)


def set_config(lab,window=14400):
    if settings(lab.s.feedConfig(lab.a.address))!=params(lab.p,window=window):
        lab.s.updatePriceFeed(lab.a.address,*params(lab.p,window=window),sender=lab.g.gov)
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
    # Independent model predicts a subset of touched slots, not live search order.
    assert set(expected_indices)<=touched
    assert len(touched)>=20 and len(expected_indices)//2>=10
    assert child.msg.gas==250000 and not child.is_error
    assert child.output==words(2500*10**18,1)
    assert_source_budget(child.get_gas_used())
    print(f'TWAP_COLD ring={count} index={ring["index"]} initialized={ring["initialized"]} window={window} model_depth={len(expected_indices)//2} observation_slots={len(touched)} source={child.get_gas_used()} desk={comp.get_gas_used()} observe={observe.get_gas_used()} source_target_overrun={max(0,child.get_gas_used()-210000)}')


@pytest.mark.parametrize('target',['source','desk'])
def test_cold_and_in_transaction_warm_paths(gas_lab,target):
    l=gas_lab;set_config(l)
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
    # Canonical desk resolution, scale guard (HQ + desk), four pool reads, quote desk.
    assert len(source_call.children)==8
    assert_source_budget(source_call.get_gas_used())
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
    for cost in source_costs:assert_source_budget(cost)
    assert source_costs[1]<source_costs[0]
    dependency_costs=[[{'selector':bytes(d.msg.data[:4]).hex(),'gas':d.get_gas_used()} for d in calls(c,l.s)[0].children] for c in children]
    print('TWAP_DEPENDENCIES '+json.dumps({'target':target,'call_counts':list(map(len,dependency_costs)),'cold_warm_calls':dependency_costs},sort_keys=True))
    print(f'TWAP_WARM target={target} source_cold={source_call.get_gas_used()} direct_total={direct.get_gas_used()} transaction_children={child_costs} source_children={source_costs} wrapper_overhead={root.get_gas_used()-sum(child_costs)}')


@pytest.mark.parametrize('fault',['stale','empty','invalid_round','burn'])
def test_expensive_successful_observe_then_late_weth_failure(gas_lab,fault):
    l=gas_lab
    rounds={'stale':words(1,2500*10**8,0,boa.env.timestamp-86401,1),'empty':b'','invalid_round':words(0,2500*10**8,0,boa.env.timestamp,1),'burn':None}
    Raw({'decimals()':word(8),'latestRoundData()':rounds[fault]},address=l.anchor.address)
    cold(l.g.desk)
    assert l.g.desk.getPrice(l.a.address)==0
    comp=l.g.desk._computation;child=calls(comp,l.s)[0]
    observe=[c for c in calls(child,l.p) if bytes(c.msg.data[:4])==selector('observe(uint32[])')][0]
    assert not observe.is_error and len(observe.output)==256 and observe.get_gas_used()>80000
    if fault=='burn':
        # the desk's WETH leg burns its stipend; the desk isolates whatever fails and still returns 0
        assert child.is_error or child.output==words(0,1)
    else:
        assert not child.is_error and child.output==words(0,1)
        assert_source_budget(child.get_gas_used())
    print(f'TWAP_LATE_FAILURE kind={fault} observe={observe.get_gas_used()} source={child.get_gas_used()} desk={comp.get_gas_used()}')


def test_legitimate_old_reverts_the_source_and_the_desk_isolates_it(gas_lab):
    l=gas_lab
    seed_ring(l.p,8,spacing=1)
    cold(l.g.desk)
    assert l.g.desk.getPrice(l.a.address)==0
    child=calls(l.g.desk._computation,l.s)[0]
    observe=[c for c in calls(child,l.p) if bytes(c.msg.data[:4])==selector('observe(uint32[])')][0]
    assert observe.is_error and b'OLD' in observe.output
    assert child.is_error and child.msg.gas==250000
    with boa.reverts('has price config, no price'):l.g.desk.getPrice(l.a.address,True)


def test_cold_current_desk_rotation(gas_lab):
    l=gas_lab;g=l.g
    with temporary_desk(g):
        register(g.desk,g.chainlink,g.gov)
        register(g.desk,l.s,g.gov)
        g.desk.syncTokenScale(l.a.address,sender=g.local)
        cold(g.desk)
        assert g.desk.getPrice(l.a.address,True)==2500*10**18
        child=calls(g.desk._computation,l.s)[0]
        assert child.output==words(2500*10**18,1)
        assert_source_budget(child.get_gas_used())
        print(f'TWAP_ROTATED source={child.get_gas_used()} desk={g.desk._computation.get_gas_used()}')


def test_final_deployed_size_coverage_and_noop_snapshot(gas_lab):
    l=gas_lab
    deployed=len(boa.env.get_code(l.s.address))
    assert_deployed_size(deployed)
    cold(l.s)
    assert l.s.hasPriceFeed(l.a.address,gas=75000)
    coverage=l.s._computation.get_gas_used()
    assert l.s._computation.children==[]
    cold(l.s)
    assert not l.s.addPriceSnapshot(l.a.address,gas=150000)
    snapshot=l.s._computation.get_gas_used()
    assert l.s._computation.children==[]
    print(f'TWAP_SIZE deployed={deployed} eip170_headroom={24576-deployed} target_overrun={max(0,deployed-22500)} coverage={coverage} snapshot={snapshot} compiler=Vyper-0.4.3 optimize=codesize evm=prague action_delay=2 expiration_duration=100')


@pytest.mark.parametrize('tick,reverse',[(524287,False),(-524287,True)])
def test_deep_ring_with_dense_tick_bits_and_both_quote_precision_branches(gas_lab,tick,reverse):
    """Nineteen selected multiplier bits; positive quotes in both token orders."""
    from .compiled import deploy
    l=gas_lab;g=l.g
    seed_ring(l.p,65535,tick=tick)
    asset,weth=(l.w,l.a) if reverse else (l.a,l.w)
    with temporary_desk(g):
        register(g.desk,weth_price_source(g,weth,l.anchor) if reverse else g.chainlink,g.gov)
        s=source(g,l.p.factory())
        ref=deploy('v3','Reference')
        sqrt=ref.sqrt(tick)
        assert (sqrt>2**128-1)==(not reverse)
        expected=ref.quote(tick,10**36,asset.address,weth.address)*2500//10**18
        assert admit(g,s,asset.address,params(l.p,window=14400))==expected>0
        g.desk.syncTokenScale(asset.address,sender=g.local)
        cold(s)
        assert s.getPriceAndHasFeed(asset.address)==(expected,True)
        direct=s._computation.get_gas_used()
        assert_source_budget(direct)
        cold(g.desk)
        assert g.desk.getPrice(asset.address,True)==expected
        comp=g.desk._computation;child=calls(comp,s)[0]
        assert child.msg.gas==250000 and child.output==words(expected,1) and not child.is_error
        assert_source_budget(child.get_gas_used())
        print(f'TWAP_DENSE_TICK tick={tick} reverse={reverse} direct_source={direct} forwarded_source={child.get_gas_used()} desk={comp.get_gas_used()} source_target_overrun={max(0,direct-210000,child.get_gas_used()-210000)}')


# D20's warm budget is measured against transaction-cold reads; passing a
# governance callback alone is deliberately not claimed to qualify every route.
from .gas_tools import qualification_meter, qualification_touch_set, warm_qualification_ceiling
from .graph import ZERO, quote_price_source
from .raw import Pool


def admission_lab(slot_count=0,metadata_warm=False):
    g=make_graph()
    a=boa.load('contracts/mock/MockChainlinkFeed.vy',10**18);a.setDecimals(18)
    w=boa.load('contracts/mock/MockChainlinkFeed.vy',10**18);w.setDecimals(18)
    q=boa.load('tests/priceSources/uniswap_v3/StorageQuoteSource.vy',ZERO if metadata_warm else w,slot_count,metadata_warm)
    if metadata_warm:w=q
    register(g.desk,q,g.gov)
    f=boa.load('contracts/mock/MockUniV3Factory.vy')
    p=Pool(a,w,f);f.setPool(a,w,10000,p.address)
    s=source(g,f)
    return SimpleNamespace(g=g,a=a,w=w,q=q,p=p,s=s)


def propose_for_gas(l,kind):
    if kind=='update':
        count=l.q.loadCount()
        l.q.configure(0)
        admit(l.g,l.s,l.a,params(l.p))
        l.q.configure(count)
        l.s.updatePriceFeed(l.a,*params(l.p),sender=l.g.gov)
    else:
        l.s.addNewPriceFeed(l.a,*params(l.p),sender=l.g.gov)
    advance_timelock_blocks(2)
    return l.s.confirmPriceFeedUpdate if kind=='update' else l.s.confirmNewPriceFeed


@pytest.mark.parametrize('kind',['add','update'])
@pytest.mark.parametrize('slots',[40,58,59,60,80,100])
def test_confirm_then_cold_desk_read_stays_under_target(kind,slots):
    l=admission_lab(slots)
    confirm=propose_for_gas(l,kind)
    pending=l.s.pendingUpdates(l.a)
    cold(l.s,sender=l.g.gov)
    with qualification_meter(l.s) as meter:
        try:
            result=confirm(l.a,sender=l.g.gov)
        except boa.BoaError as exc:
            with boa.reverts('route too expensive'):
                raise exc
            assert len(meter)==2
            warm=meter[0]['gas']-meter[1]['gas']
            assert warm>warm_qualification_ceiling(l.s)
            assert l.s.pendingUpdates(l.a)==pending and l.s.pendingQuoteCount(l.w)==1
            print(f'TWAP_ADMISSION kind={kind} slots={slots} rejected warm={warm}')
            return
    assert result and len(meter)==2
    warm=meter[0]['gas']-meter[1]['gas']
    assert warm<=warm_qualification_ceiling(l.s)
    if l.g.desk.getRegId(l.s)==0:register(l.g.desk,l.s,l.g.gov)
    cold(l.g.desk)
    assert l.g.desk.getPrice(l.a,True)==10**18
    child=calls(l.g.desk._computation,l.s)[0]
    assert child.msg.gas==250000 and not child.is_error
    assert_source_budget(child.get_gas_used())
    print(f'TWAP_ADMISSION kind={kind} slots={slots} confirmed warm={warm} cold={child.get_gas_used()} delta={child.get_gas_used()-warm}')


@pytest.mark.parametrize('kind',['add','update'])
@pytest.mark.parametrize('slots',[0,40,58])
def test_warm_to_cold_delta_is_within_margin(kind,slots):
    l=admission_lab(slots)
    confirm=propose_for_gas(l,kind)
    touches=qualification_touch_set(l.g,l.s,l.p,l.a.address)
    cold(l.s,sender=l.g.gov)
    with storage_reads() as before_reads:
        with qualification_meter(l.s,touches,before_reads) as meter:
            assert confirm(l.a,sender=l.g.gov)
    assert len(meter)==2 and all(meter[0]['warm_addresses'].values())
    assert all(meter[0]['warm_slots'])
    warm=meter[0]['gas']-meter[1]['gas']
    if l.g.desk.getRegId(l.s)==0:register(l.g.desk,l.s,l.g.gov)
    cold(l.g.desk)
    with storage_reads() as cold_reads:
        assert l.g.desk.getPrice(l.a,True)==10**18
    child=calls(l.g.desk._computation,l.s)[0]
    expected={(bytes.fromhex(address[2:]),slot) for address,slot,label in touches['storage']}
    overlap=set(before_reads[:meter[0]['read_index']]) & set(cold_reads)
    assert overlap==expected, 'enumerate every overlapping slot, including staging writes'
    pre_addresses=meter[0]['called_addresses']
    cold_addresses={c.msg.code_address for c in walk(l.g.desk._computation)}
    assert pre_addresses & cold_addresses=={bytes.fromhex(a[2:]) for a in touches['addresses'].values()}
    delta=child.get_gas_used()-warm
    ceiling=warm_qualification_ceiling(l.s)
    assert ceiling<=170000 and delta<=210000-ceiling
    print('TWAP_WARM_TOUCH_SET '+json.dumps(touches,sort_keys=True))
    print(f'TWAP_WARM_DELTA kind={kind} slots={slots} warm={warm} cold={child.get_gas_used()} delta={delta} ceiling={ceiling} ceiling_plus_delta={ceiling+delta}')


def test_confirmation_is_not_cold_qualification():
    # The quote token's decimals() warms its own price-source SLOADs. Those
    # metadata-induced slots lie outside the enumerated standard touch set.
    l=admission_lab(100,metadata_warm=True)
    confirm=propose_for_gas(l,'add')
    cold(l.s,sender=l.g.gov)
    with qualification_meter(l.s) as meter:
        assert confirm(l.a,sender=l.g.gov)
    warm=meter[0]['gas']-meter[1]['gas']
    assert warm<=warm_qualification_ceiling(l.s)
    register(l.g.desk,l.s,l.g.gov)
    cold(l.g.desk)
    assert l.g.desk.getPrice(l.w,True)==10**18
    quote_call=calls(l.g.desk._computation,l.q)[0]
    assert not quote_call.is_error and quote_call.msg.gas==250000
    assert quote_call.get_gas_used()<250000  # quote alone fits its own stipend
    cold(l.g.desk)
    assert l.g.desk.getPrice(l.a)==0
    child=calls(l.g.desk._computation,l.s)[0]
    assert child.msg.gas==250000
    assert child.is_error or child.output==words(0,1)  # combined route fails outer stipend
    print(f'TWAP_EXTRA_WARMING warm={warm} quote_alone={quote_call.get_gas_used()} combined_cold={child.get_gas_used()} unavailable=True')


def registry_lab(gas_lab,source_first=False,fat=False):
    # A new actual desk preserves the canonical V3 pool's 65535-slot cold path.
    l=gas_lab;g=l.g
    if source_first:register(g.desk,l.s,g.gov)
    misses=[]
    for _ in range(10 if fat else 2):
        mock=boa.load('contracts/mock/MockRawPriceSource.vy')
        mock.configure(0,False)
        register(g.desk,mock,g.gov)
        misses.append(mock)
    chainlink_id=register(g.desk,g.chainlink,g.gov)
    if not source_first:register(g.desk,l.s,g.gov)
    # RH-shaped route: Chainlink first, then Curve/V2-like no-feed sources, V3 last.
    if not fat:
        g.mc.setPriorityPriceSourceIds([chainlink_id,1],sender=g.actor.address)
    return misses


def test_rh_shaped_registry_source_last_cold_read_under_target(gas_lab):
    l=gas_lab
    with temporary_desk(l.g):
        # The live ordering is Chainlink, Curve-like, V2-like, V3; priority [1,2].
        register(l.g.desk,l.g.chainlink,l.g.gov)
        for _ in range(2):
            mock=boa.load('contracts/mock/MockRawPriceSource.vy');mock.configure(0,False)
            register(l.g.desk,mock,l.g.gov)
        register(l.g.desk,l.s,l.g.gov)
        l.g.mc.setPriorityPriceSourceIds([1,2],sender=l.g.actor.address)
        cold(l.g.desk)
        assert l.g.desk.getPrice(l.a,True)==2500*10**18
        child=calls(l.g.desk._computation,l.s)[0]
        assert_source_budget(child.get_gas_used())
        print(f'TWAP_REGISTRY shape=RH source_last={child.get_gas_used()} priority=[1,2]')


def test_fat_registry_source_first_fails_cold_documented(gas_lab):
    l=gas_lab
    with temporary_desk(l.g):
        registry_lab(l,source_first=True,fat=True)
        cold(l.g.desk)
        assert l.g.desk.getPrice(l.a)==0
        child=calls(l.g.desk._computation,l.s)[0]
        assert child.is_error or child.output==words(0,1)
        print(f'TWAP_REGISTRY shape=fat source_first={child.get_gas_used()} unavailable=True')


def test_fat_registry_source_last_succeeds(gas_lab):
    l=gas_lab
    with temporary_desk(l.g):
        registry_lab(l,source_first=False,fat=True)
        cold(l.g.desk)
        assert l.g.desk.getPrice(l.a,True)==2500*10**18
        child=calls(l.g.desk._computation,l.s)[0]
        assert_source_budget(child.get_gas_used())
        print(f'TWAP_REGISTRY shape=fat source_last={child.get_gas_used()} unavailable=False')


@pytest.mark.parametrize('kind',['add','update'])
def test_warm_to_cold_delta_is_within_margin_canonical(gas_lab,kind):
    """The same touch-set proof on the compiled 65535-slot pool and Chainlink."""
    l=gas_lab;g=l.g
    with temporary_desk(g):
        register(g.desk,g.chainlink,g.gov)
        s=source(g,l.p.factory())
        if kind=='update':
            admit(g,s,l.a,params(l.p,window=14400))
            s.updatePriceFeed(l.a,*params(l.p,window=14400),sender=g.gov)
            confirm=s.confirmPriceFeedUpdate
        else:
            s.addNewPriceFeed(l.a,*params(l.p,window=14400),sender=g.gov)
            confirm=s.confirmNewPriceFeed
        advance_timelock_blocks(2)
        touches=qualification_touch_set(g,s,l.p,l.a.address)
        cold(s,sender=g.gov)
        with storage_reads() as before_reads:
            with qualification_meter(s,touches,before_reads) as meter:
                assert confirm(l.a,sender=g.gov)
        assert len(meter)==2 and all(meter[0]['warm_addresses'].values())
        assert all(meter[0]['warm_slots'])
        warm=meter[0]['gas']-meter[1]['gas']
        if g.desk.getRegId(s)==0:register(g.desk,s,g.gov)
        cold(g.desk)
        with storage_reads() as cold_reads:
            assert g.desk.getPrice(l.a,True)==2500*10**18
        child=calls(g.desk._computation,s)[0]
        expected={(bytes.fromhex(address[2:]),slot) for address,slot,label in touches['storage']}
        assert set(before_reads[:meter[0]['read_index']]) & set(cold_reads)==expected
        cold_addresses={c.msg.code_address for c in walk(g.desk._computation)}
        assert meter[0]['called_addresses'] & cold_addresses=={bytes.fromhex(a[2:]) for a in touches['addresses'].values()}
        delta=child.get_gas_used()-warm
        ceiling=warm_qualification_ceiling(s)
        assert ceiling<=170000 and delta<=210000-ceiling
        assert_source_budget(child.get_gas_used())
        print('TWAP_WARM_TOUCH_SET '+json.dumps(touches,sort_keys=True))
        print(f'TWAP_WARM_DELTA kind={kind} route=canonical warm={warm} cold={child.get_gas_used()} delta={delta} ceiling={ceiling} ceiling_plus_delta={ceiling+delta}')
