import json
from pathlib import Path

import boa
import pytest
from .helpers import unavailable,isolated

from .graph import admit,params,set_policy,source,make_graph,weth_price_source,ZERO
from .raw import Pool,words,word

ROOT=Path(__file__).resolve().parents[3]
WINDOW=3600  # the source's default window; mock histories are built for it


@pytest.mark.parametrize('age,ceiling,valid',[(1799,3600,True),(3599,3600,True),(3600,3600,True),(3601,3600,False),(1801,1800,False)])
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
    active.anchor.setMockData(3*10**8)
    p=active.pool;past=0;current=0;lp=0;ln=WINDOW*2**128//10**20
    if kind=='cancelling':past=current=WINDOW*12345
    if kind=='int56_positive_wrap':past=2**55-10;current=-2**55+WINDOW-10
    if kind=='int56_negative_wrap':past=-2**55+10;current=2**55-WINDOW+10
    if kind=='uint160_wrap':lp=2**160-10;ln-=10
    p.set('observe(uint32[])',words(64,160,2,past,current,2,lp,ln))
    delta=(current-past+2**55)%2**56-2**55
    tick=delta//WINDOW
    expected=math.quote(tick,10**36,True)*3//10**18
    assert active.s.getPriceAndHasFeed(active.asset)==(expected,True)
    assert active.g.desk.getPrice(active.asset,True)==expected


def test_liquidity_floors_are_a_ratio_of_the_proposal_baseline(active,math):
    l=active;s=l.s;a=l.asset
    spl=WINDOW*2**128//10**20
    base=s.feedConfig(a).baseLiquidity
    assert base==math.harmonic(0,spl,WINDOW) and 0.99*10**20<base<=10**20
    assert s.feedDefaults().minLiquidityRatio==50_00
    floor=(base*50_00+9999)//100_00
    assert s.getFeedLiquidity(a)==(10**20,base,floor)
    # current liquidity: exact integer boundary
    l.pool.set('liquidity()',word(floor-1));unavailable(l)
    l.pool.set('liquidity()',word(floor));assert l.g.desk.getPrice(a,True)==10**18
    # harmonic liquidity over the window: a larger accumulator delta means less liquidity
    l.pool.set('observe(uint32[])',words(64,160,2,0,0,2,0,3*spl));unavailable(l)
    l.pool.set('observe(uint32[])',words(64,160,2,0,0,2,0,spl))
    # Later defaults cannot change this active proposal-bound floor.
    s.setFeedDefaults(WINDOW,1800,100_00,sender=l.g.gov)
    l.pool.set('liquidity()',word(floor));assert l.g.desk.getPrice(a,True)==10**18
    with boa.reverts('invalid defaults'):
        s.setFeedDefaults(WINDOW,1800,0,sender=l.g.gov)
    l.pool.set('liquidity()',word(1));unavailable(l)
    assert s.getFeedLiquidity(a)==(1,base,floor)


def test_feeds_bind_defaults_at_proposal_time(active):
    l=active;s=l.s;a=l.asset
    assert s.feedConfig(a).twapWindow==3600 and s.feedConfig(a).maxObservationAge==1800
    l.pool.set('observations(uint256)',words((boa.env.timestamp-50)%2**32,0,0,1))
    assert l.g.desk.getPrice(a,True)==10**18
    s.setFeedDefaults(WINDOW,10,50_00,sender=l.g.gov)
    assert l.g.desk.getPrice(a,True)==10**18


def test_explicit_settings_override_defaults(lab):
    lab.pool.set_history(window=1800)
    admit(lab.g,lab.s,lab.asset,params(lab.pool,window=1800,age=60))
    assert (lab.s.feedConfig(lab.asset).twapWindow,lab.s.feedConfig(lab.asset).maxObservationAge)==(1800,60)
    lab.pool.set('observations(uint256)',words((boa.env.timestamp-61)%2**32,0,0,1))
    unavailable(lab)
    lab.s.setFeedDefaults(3600,3600,50_00,sender=lab.g.gov)
    unavailable(lab)  # the explicit age still governs


def test_locked_pool_and_uninitialized_observation_are_unavailable(active):
    active.pool.set('slot0()',words(2**96,0,0,1,1,0,0))
    unavailable(active)
    active.pool.set('slot0()',words(2**96,0,0,1,1,0,1))
    active.pool.set('observations(uint256)',words(boa.env.timestamp%2**32,0,0,0))
    unavailable(active)


def test_tick_boundary_and_uninitialized_next_capacity_are_accepted(active):
    # Canonical boundaries need not be a fresh inverse sqrt calculation.
    active.pool.set('slot0()',words(2**96,-1,0,1,65535,0,1))
    assert active.g.desk.getPrice(active.asset,True)==10**18


@pytest.mark.parametrize('index,value',[(1,887273*WINDOW),(1,-887273*WINDOW)])
def test_out_of_domain_mean_tick_is_unavailable(active,index,value):
    fields=[64,160,2,0,0,2,0,WINDOW*2**128//10**20];fields[3+index]=value
    active.pool.set('observe(uint32[])',words(*fields))
    unavailable(active)


@pytest.mark.parametrize('signature,payload',[
    ('slot0()',words(2**96,0,0,1,1,0,2)),
    ('slot0()',words(2**160,0,0,1,1,0,1)),
    ('liquidity()',word(2**128)),
    ('observations(uint256)',words(2**32,0,0,1)),
    ('observations(uint256)',words(0,2**55,0,1)),
    ('observations(uint256)',words(0,0,0,2)),
    ('observe(uint32[])',words(64,192,3,0,0,0,2,0,1)),
    ('observe(uint32[])',words(64,160,2,0,0,2,0,2**160)),
])
def test_malformed_pool_responses_revert_and_are_isolated_by_the_desk(active,signature,payload):
    """Typed decoding rejects noncanonical words; the desk isolates the reverting source."""
    active.pool.set(signature,payload)
    isolated(active)


@pytest.mark.parametrize('signature',['slot0()','liquidity()','observations(uint256)','observe(uint32[])'])
@pytest.mark.parametrize('fault',['revert','empty','short','eoa'])
def test_pool_dependency_failures_are_isolated_by_the_desk(active,signature,fault):
    data=active.pool.responses[signature]
    if fault=='eoa':
        boa.env.set_code(active.pool.address,b'')
    elif fault=='revert':
        del active.pool.responses[signature];active.pool.install()
    else:
        active.pool.set(signature,{'empty':b'','short':data[:-1]}[fault])
    isolated(active)


@pytest.mark.parametrize('age,policy,valid',[(299,300,True),(300,300,True),(301,300,False),(2958,2958,True),(2958,1800,False),(604800,604800,True),(604801,604800,False)])
def test_quote_freshness_follows_the_desk_policy(active,age,policy,valid):
    set_policy(active.g,policy)
    active.anchor.setMockData(10**8,1,1,0,boa.env.timestamp-age)
    if valid:assert active.g.desk.getPrice(active.asset,True)==10**18
    else:unavailable(active)


@pytest.mark.parametrize('answer,round_id,answered,timestamp',[(0,1,1,'now'),(-1,1,1,'now'),(10**8,0,1,'now'),(10**8,2,1,'now'),(10**8,1,1,'zero'),(10**8,1,1,'future'),(2**255-1,1,1,'now')])
def test_quote_feed_round_validation_makes_feed_unavailable(active,answer,round_id,answered,timestamp):
    updated={'now':boa.env.timestamp,'zero':0,'future':boa.env.timestamp+1}[timestamp]
    active.anchor.setMockData(answer,round_id,answered,0,updated)
    unavailable(active)


def test_quote_price_scales_the_quote(active):
    active.anchor.setMockData(0)
    unavailable(active)
    active.anchor.setMockData(3*10**8)
    assert active.g.desk.getPrice(active.asset,True)==3*10**18
    assert active.s.getPrice(active.asset)==3*10**18


def test_stale_time_is_ignored_and_the_desk_argument_is_authenticated(active):
    a,s,g=active.asset,active.s,active.g
    outsider=boa.env.generate_address()
    assert s.getPriceAndHasFeed(a,300,g.desk.address,sender=outsider)==(10**18,True)
    assert s.getPriceAndHasFeed(a,300,ZERO,sender=outsider)==(10**18,True)
    assert s.getPriceAndHasFeed(a,0,outsider)==(0,True)
    assert s.getPriceAndHasFeed(outsider,300,outsider)==(0,False)
    assert g.desk.getPrice(a,True)==10**18


@pytest.mark.parametrize('asset_index',range(4))
@pytest.mark.parametrize('vector_index',range(3))
def test_frozen_rows_through_source_and_actual_desk(lab,asset_index,vector_index):
    """Frozen cumulative/anchor inputs plus explicitly SYNTHETIC missing metadata."""
    data=json.loads((ROOT/'docs/priceSources/uniswap-v3-twap-reference-vectors.json').read_text())
    a=data['assets'][asset_index];v=a['vectors'][vector_index]
    boa.env.evm.patch.timestamp=data['block_timestamp']
    token=lab.asset if a['asset_is_token0'] else lab.weth
    weth=lab.weth if a['asset_is_token0'] else lab.asset
    pool=Pool(token,weth,lab.factory)
    lab.factory.setPool(token,weth,10000,pool.address)
    # Unknown original startedAt/answeredInRound remain null in the frozen file.
    anchor=data['anchor']
    lab.anchor.setMockData(int(anchor['answer']),int(anchor['round_id']),int(anchor['round_id']),0,anchor['updated_at'])
    pool.set('observe(uint32[])',words(64,160,2,*map(int,v['tick_cumulatives']),2,*map(int,v['seconds_per_liquidity_cumulative_x128'])))
    pool.set('liquidity()',word(10**24))  # current liquidity is synthetic; it must clear the frozen harmonic baseline
    g=make_graph()
    weth_price_source(g,weth,lab.anchor)
    s=source(g,lab.factory)
    from .compiled import deploy
    expected=deploy('v3','Reference').quote(v['mean_tick'],10**36,token.address,weth.address)*int(anchor['price18'])//10**36
    assert admit(g,s,token,params(pool,window=v['window_seconds']))==expected
    assert s.feedConfig(token).quoteAsset==weth.address
    g.desk.syncTokenScale(token,sender=g.gov)
    assert g.desk.getPrice(token,True)==expected
    assert g.desk.getUsdValue(token,10**18,True)==expected
    # the anchor is 2,958s old: a tighter desk policy makes the quote leg, and so this feed, unavailable
    set_policy(g,1800)
    assert s.getPriceAndHasFeed(token)==(0,True)
    assert g.desk.getPrice(token)==0
