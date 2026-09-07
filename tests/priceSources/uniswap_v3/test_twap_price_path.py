import json
from pathlib import Path

import boa
import pytest

from .graph import admit,params,set_policy,ZERO
from .raw import Raw,words,word,selector
from .gas_tools import cold,calls,walk

ROOT=Path(__file__).resolve().parents[3]


def unavailable(lab):
    s,a,g=lab.s,lab.asset,lab.g
    assert s.getPriceAndHasFeed(a)==(0,True)
    assert s.hasPriceFeed(a)
    assert g.desk.getPrice(a)==0
    with boa.reverts('has price config, no price'):
        g.desk.getPrice(a,True)


@pytest.mark.parametrize('age,ceiling,valid',[(1799,3600,True),(1800,3600,True),(1801,3600,True),(3000,3600,True),(3600,3600,True),(3601,3600,False),(1801,1800,False),(8*3600,86400,True)])
def test_observation_age_is_independent_of_lookback(lab,age,ceiling,valid):
    admit(lab.g,lab.s,lab.asset,params(lab.pool,age=ceiling))
    lab.pool.set('observations(uint256)',words((boa.env.timestamp-age)%2**32,0,0,1))
    if valid:
        assert lab.s.getPrice(lab.asset)==10**18
        assert lab.g.desk.getPrice(lab.asset,True)==10**18
    else:
        unavailable(lab)


@pytest.mark.parametrize('timestamp',[0,2**32-5,2**32+5])
def test_observation_uint32_timestamp_wrap(lab,timestamp):
    boa.env.evm.patch.timestamp=2**32+10
    lab.anchor.setMockData(10**8)
    lab.pool.set_history(age=0)
    admit(lab.g,lab.s,lab.asset,params(lab.pool))
    lab.pool.set('observations(uint256)',words(timestamp%2**32,0,0,1))
    assert lab.s.getPrice(lab.asset)==10**18


@pytest.mark.parametrize('kind', ['constant_zero','cancelling','int56_positive_wrap','int56_negative_wrap','uint160_wrap'])
def test_zero_delta_and_modular_accumulators(active,kind,math):
    p=active.pool;past=0;current=0;lp=0;ln=1800*2**128//10**20
    if kind=='cancelling':past=current=1800*12345
    if kind=='int56_positive_wrap':past=2**55-10;current=-2**55+1790
    if kind=='int56_negative_wrap':past=-2**55+10;current=2**55-1790
    if kind=='uint160_wrap':lp=2**160-10;ln-=10
    p.set('observe(uint32[])',words(64,160,2,past,current,2,lp,ln))
    delta=(current-past+2**55)%2**56-2**55
    tick=delta//1800
    expected=math.quote(tick,10**18,True)
    assert active.s.getPriceAndHasFeed(active.asset)==(expected,True)
    assert active.g.desk.getPrice(active.asset,True)==expected


@pytest.mark.parametrize('leg,offset',[(leg,offset) for leg in ('current','harmonic') for offset in (-1,0,1)])
def test_independent_liquidity_thresholds(lab,leg,offset,math):
    spl=1800*2**128//10**20
    h=math.harmonic(0,spl,1800)
    admit(lab.g,lab.s,lab.asset,params(lab.pool,current=10**20 if leg=='current' else 1,harmonic=h if leg=='harmonic' else 1))
    if leg=='current':
        lab.pool.set('liquidity()',word(10**20+offset))
    else:
        # Change the denominator, not the configured threshold. Larger denominator
        # decreases harmonic liquidity. At-threshold value is exact integer math.
        lab.pool.set('observe(uint32[])',words(64,160,2,0,0,2,0,spl-offset))
    if offset<0:unavailable(lab)
    else:assert lab.g.desk.getPrice(lab.asset,True)==10**18


@pytest.mark.parametrize('index,value',[(0,0),(0,4295128738),(0,1461446703485210103287273052203988822378723970342),(0,2**160),(1,887273),(1,-887273),(1,2**24-1),(2,1),(2,2**16),(3,0),(3,65536),(4,0),(4,65536),(5,256),(6,0),(6,2)])
def test_slot0_invalid_values_fail_unavailable(active,index,value):
    fields=[2**96,0,0,1,1,0,1];fields[index]=value
    active.pool.set('slot0()',words(*fields))
    unavailable(active)


def test_tick_boundary_and_uninitialized_next_capacity_are_accepted(active):
    # Canonical boundaries need not be a fresh inverse sqrt calculation.
    active.pool.set('slot0()',words(2**96,-1,0,1,65535,0,1))
    assert active.g.desk.getPrice(active.asset,True)==10**18


@pytest.mark.parametrize('index,value',[(0,2**32),(1,2**55),(1,-2**55-1),(1,2**56-1),(2,2**160),(3,0),(3,2)])
def test_current_observation_abi_and_initialized_guards(active,index,value):
    fields=[boa.env.timestamp%2**32,0,0,1];fields[index]=value
    active.pool.set('observations(uint256)',words(*fields))
    unavailable(active)


@pytest.mark.parametrize('index,value',[(0,0),(0,160),(1,64),(1,192),(2,1),(2,3),(3,2**55),(3,2**56-1),(4,-2**55-1),(5,1),(5,3),(6,2**160),(7,2**160),(7,0),(7,1),(4,887273*1800)])
def test_observe_offsets_lengths_widths_and_math(active,index,value):
    fields=[64,160,2,0,0,2,0,1800*2**128//10**20];fields[index]=value
    active.pool.set('observe(uint32[])',words(*fields))
    unavailable(active)


@pytest.mark.parametrize('signature', ['slot0()','liquidity()','observations(uint256)','observe(uint32[])'])
@pytest.mark.parametrize('fault',['revert','empty','short','extra','burn','eoa'])
def test_pool_dependency_exact_lengths_and_bounded_failures(active,signature,fault):
    data=active.pool.responses[signature]
    if fault=='eoa':
        boa.env.set_code(active.pool.address,b'')
    else:
        # Absent selector reverts; None is an actual infinite gas loop.
        result={'empty':b'','short':data[:-1],'extra':data+b'\x00','burn':None}.get(fault)
        if fault=='revert':
            del active.pool.responses[signature];active.pool.install()
        else:active.pool.set(signature,result)
    cold(active.g.desk)
    assert active.g.desk.getPrice(active.asset)==0
    c=calls(active.g.desk._computation,active.s)[0]
    assert not c.is_error and c.output==words(0,1)
    unavailable(active)


@pytest.mark.parametrize('age,policy,valid',[(299,300,True),(300,300,True),(301,300,False),(2958,2958,True),(2958,1800,False),(604800,604800,True),(604801,604800,False)])
def test_anchor_age_boundaries(active,age,policy,valid):
    set_policy(active.g,policy)
    active.anchor.setMockData(10**8,1,1,0,boa.env.timestamp-age)
    if valid:assert active.g.desk.getPrice(active.asset,True)==10**18
    else:unavailable(active)


@pytest.mark.parametrize('answer,round_id,answered,timestamp',[(0,1,1,'now'),(-1,1,1,'now'),(10**8,0,1,'now'),(10**8,2,1,'now'),(10**8,1,1,'zero'),(10**8,1,1,'future'),(2**255-1,1,1,'now')])
def test_anchor_round_answer_and_normalization(active,answer,round_id,answered,timestamp):
    updated={'now':boa.env.timestamp,'zero':0,'future':boa.env.timestamp+1}[timestamp]
    active.anchor.setMockData(answer,round_id,answered,0,updated)
    unavailable(active)


def test_phase_encoded_round_and_started_at_are_valid(active):
    rid=2**64+2037
    active.anchor.setMockData(10**8,rid,rid,2**256-1,boa.env.timestamp)
    assert active.g.desk.getPrice(active.asset,True)==10**18


@pytest.mark.parametrize('signature', ['decimals()','latestRoundData()'])
@pytest.mark.parametrize('fault', ['empty','short','extra','width','burn','revert'])
def test_anchor_canonical_abi(active,signature,fault):
    baseline={'decimals()':word(8),'latestRoundData()':words(1,10**8,0,boa.env.timestamp,1)}
    data=baseline[signature]
    if fault=='revert':del baseline[signature]
    elif fault=='burn':baseline[signature]=None
    elif fault=='width':baseline[signature]=word(256) if signature=='decimals()' else words(2**80,10**8,0,boa.env.timestamp,2**80)
    else:baseline[signature]={'empty':b'','short':data[:-1],'extra':data+b'\x00'}[fault]
    Raw(baseline,address=active.anchor.address)
    unavailable(active)


@pytest.mark.parametrize('local,global_age,age,valid',[(0,0,0,False),(0,604801,0,False),(0,1,1,True),(300,0,200,True),(7200,3600,5400,True),(3600,7200,5400,False)])
def test_local_override_and_inheritance(lab,local,global_age,age,valid):
    admit(lab.g,lab.s,lab.asset,params(lab.pool,quote_age=local))
    set_policy(lab.g,global_age)
    lab.anchor.setMockData(10**8,1,1,0,boa.env.timestamp-age)
    if valid:assert lab.g.desk.getPrice(lab.asset,True)==10**18
    else:unavailable(lab)


def test_caller_and_registry_are_both_authenticated(active):
    a,s,g=active.asset,active.s,active.g
    outsider=boa.env.generate_address()
    for sender,registry in [(outsider,g.desk.address),(g.desk.address,outsider),(outsider,outsider)]:
        assert s.getPriceAndHasFeed(a,300,registry,sender=sender)==(0,True)
    assert s.getPriceAndHasFeed(a,300,g.desk.address,sender=g.desk.address)==(10**18,True)
    assert s.getPriceAndHasFeed(a,0,outsider,sender=outsider)==(10**18,True)
    assert s.getPriceAndHasFeed(outsider,300,outsider)==(0,False)


@pytest.mark.parametrize('target', ['hq','mc','desk_scale','asset_decimals'])
@pytest.mark.parametrize('fault', ['empty','short','extra','burn','revert','eoa'])
def test_required_identity_policy_and_scale_fail_closed(active,target,fault):
    g=active.g
    obj={'hq':g.hq,'mc':g.mc,'desk_scale':g.desk,'asset_decimals':active.asset}[target]
    signature={'hq':'getAddr(uint256)','mc':'getPriceStaleTime()','desk_scale':'tokenScale(address)','asset_decimals':'decimals()'}[target]
    data=word(18 if target=='asset_decimals' else 86400 if target=='mc' else 0)
    responses={signature: {'empty':b'','short':data[:-1],'extra':data+b'\x00','burn':None}.get(fault,b'')}
    if fault=='revert':responses={}
    Raw(responses,address=obj.address)
    if fault=='eoa':boa.env.set_code(obj.address,b'')
    cold(active.s)
    assert active.s.getPriceAndHasFeed(active.asset)==(0,True)
    assert not active.s._computation.is_error


def test_explicit_override_ignores_unreadable_mc_inside_source_only(lab):
    admit(lab.g,lab.s,lab.asset,params(lab.pool,quote_age=300))
    Raw({},address=lab.g.mc.address)
    assert lab.s.getPrice(lab.asset)==10**18
    with boa.reverts():
        lab.g.desk.getPrice(lab.asset)


@pytest.mark.parametrize('asset_index',range(4))
@pytest.mark.parametrize('vector_index',range(3))
def test_frozen_rows_through_source_and_actual_desk(lab,asset_index,vector_index):
    """Frozen cumulative/anchor inputs plus explicitly SYNTHETIC missing metadata."""
    data=json.loads((ROOT/'docs/priceSources/uniswap-v3-twap-reference-vectors.json').read_text())
    a=data['assets'][asset_index];v=a['vectors'][vector_index]
    boa.env.evm.patch.timestamp=data['block_timestamp']
    token=lab.asset if a['asset_is_token0'] else lab.weth
    weth=lab.weth if a['asset_is_token0'] else lab.asset
    from .raw import Pool
    from .graph import source
    pool=Pool(token,weth,lab.factory)
    lab.factory.setPool(token,weth,10000,pool.address)
    # Unknown original startedAt/answeredInRound remain null in the frozen file.
    anchor=data['anchor']
    lab.anchor.setMockData(int(anchor['answer']),int(anchor['round_id']),int(anchor['round_id']),0,anchor['updated_at'])
    pool.set('observe(uint32[])',words(64,160,2,*map(int,v['tick_cumulatives']),2,*map(int,v['seconds_per_liquidity_cumulative_x128'])))
    s=source(lab.g,lab.factory,weth,lab.anchor)
    expected=int(v['usd_price18'])
    assert admit(lab.g,s,token,params(pool,window=v['window_seconds']))==expected
    lab.g.desk.syncTokenScale(token,sender=lab.g.gov)
    assert lab.g.desk.getPrice(token,True)==expected
    assert lab.g.desk.getUsdValue(token,10**18,True)==expected
    set_policy(lab.g,1800)
    assert s.getPriceAndHasFeed(token)==(0,True)
    assert lab.g.desk.getPrice(token)==0
