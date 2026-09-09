"""Owner-locked D1-D20 regressions, exercising public lifecycle and actual desk.

T11/T22 live in test_twap_gas.py. Canonical pools cover liquidity and ring
claims; raw pools isolate ABI faults and governance state transitions.
"""
from fractions import Fraction
import math as pymath
from types import SimpleNamespace

import boa
import pytest
from eth_abi import encode
from conf_utils import advance_timelock_blocks, filter_logs

from .compiled import deploy
from .graph import make_graph, source, admit, params, register, quote_price_source, weth_price_source
from .helpers import state, unavailable
from .pools import organic_pool
from .raw import Pool, Raw, Revert, selector, word, words
from .test_twap_lifecycle import start, CONFIRM, CANCEL, CANCELLED_EVENT


def canonical(liquidity=10**20):
    g=make_graph()
    f,p,a,w,actor,ref=organic_pool(g,cardinality=3601)
    if liquidity!=10**20:
        actor.remove(p.address,10**20-liquidity)
        boa.env.time_travel(seconds=3600)
        actor.add(p.address,1);actor.remove(p.address,1)
    quote_price_source(g,w,10**18)
    s=source(g,f.address)
    return SimpleNamespace(g=g,s=s,pool=p,asset=a,weth=w,actor=actor,ref=ref)


def batch_at_governor(g):
    # The test governor is a contract at the existing authorized HQ address.
    return boa.load_partial('tests/priceSources/uniswap_v3/BatchGovernance.vy').stomp(g.gov)


def sync_and_confirm(batch,l,method='confirmPriceFeedUpdate'):
    return batch.execute([l.g.desk.address,l.s.address],
                         [l.g.desk.syncTokenScale.prepare_calldata(l.asset),
                          getattr(l.s,method).prepare_calldata(l.asset)])


def test_zero_floor_is_impossible_on_canonical_pool():
    l=canonical(liquidity=2)
    assert admit(l.g,l.s,l.asset,params(l.pool))==10**18
    c=l.s.feedConfig(l.asset)
    assert c.baseLiquidity==1 and c.minLiquidity==1
    l.actor.remove(l.pool.address,2)
    assert l.pool.liquidity()==0
    unavailable(l)
    l.actor.move(l.pool.address,False,l.ref.sqrt(800000))
    assert l.pool.slot0()[1]==800000
    boa.env.time_travel(seconds=1800)
    unavailable(l)


@pytest.mark.parametrize('liquidity',[2,3,10001])
@pytest.mark.parametrize('ratio',[1,5000,10000])
def test_positive_ratio_never_rounds_to_zero_floor(lab,liquidity,ratio):
    lab.s.setFeedDefaults(3600,1800,ratio,sender=lab.g.gov)
    lab.pool.set_history(liquidity=liquidity)
    lab.s.addNewPriceFeed(lab.asset,*params(lab.pool),sender=lab.g.gov)
    c=lab.s.pendingUpdates(lab.asset).config
    assert c.baseLiquidity>0
    assert c.minLiquidity==(c.baseLiquidity*ratio+9999)//10000>=1


def test_scale_poisoning_confirm_while_unset_then_hostile_sync_goes_dark(lab):
    admit(lab.g,lab.s,lab.asset,params(lab.pool))
    assert lab.g.desk.tokenScale(lab.asset)==0
    lab.asset.setDecimals(6)
    lab.g.desk.syncTokenScale(lab.asset,sender=boa.env.generate_address())
    assert lab.g.desk.tokenScale(lab.asset)==10**6
    unavailable(lab)
    lab.asset.setDecimals(18)
    unavailable(lab)
    lab.g.desk.syncTokenScale(lab.asset,sender=lab.g.gov)
    assert lab.g.desk.getPrice(lab.asset,True)==10**18


def test_update_confirm_with_stale_nonzero_scale_reverts_and_keeps_pending(active):
    l=active
    l.g.desk.syncTokenScale(l.asset,sender=l.g.gov)
    l.asset.setDecimals(6)
    assert l.s.updatePriceFeed(l.asset,*params(l.pool),sender=l.g.gov)
    before=state(l.s,l.asset)
    advance_timelock_blocks(2)
    with boa.reverts('invalid feed'):
        l.s.confirmPriceFeedUpdate(l.asset,sender=l.g.gov)
    assert state(l.s,l.asset)==before
    assert l.s.pendingQuoteCount(l.weth)==1
    # The active snapshot still matches the desk until governance syncs.
    assert l.s.getPrice(l.asset)==10**18


def test_disable_readd_confirm_with_stale_scale_reverts(lab):
    admit(lab.g,lab.s,lab.asset,params(lab.pool))
    lab.g.desk.syncTokenScale(lab.asset,sender=lab.g.gov)
    lab.s.disablePriceFeed(lab.asset,sender=lab.g.gov)
    advance_timelock_blocks(2)
    assert lab.s.confirmDisablePriceFeed(lab.asset,sender=lab.g.gov)
    lab.asset.setDecimals(6)
    assert lab.s.addNewPriceFeed(lab.asset,*params(lab.pool),sender=lab.g.gov)
    advance_timelock_blocks(2)
    before=state(lab.s,lab.asset)
    with boa.reverts('invalid feed'):
        lab.s.confirmNewPriceFeed(lab.asset,sender=lab.g.gov)
    assert state(lab.s,lab.asset)==before and not lab.s.hasPriceFeed(lab.asset)


@pytest.mark.parametrize('mismatch_timing',['before_proposal','after_proposal'])
def test_batch_sync_then_confirm_recovers_pricing(active,mismatch_timing):
    l=active
    l.g.desk.syncTokenScale(l.asset,sender=l.g.gov)
    batch=batch_at_governor(l.g)
    if mismatch_timing=='before_proposal':
        l.asset.setDecimals(6)
    assert l.s.updatePriceFeed(l.asset,*params(l.pool),sender=l.g.gov)
    assert l.s.getPrice(l.asset)==10**18
    if mismatch_timing=='after_proposal':
        l.asset.setDecimals(6)
        l.g.desk.syncTokenScale(l.asset,sender=l.g.gov)
        l.asset.setDecimals(18)
        unavailable(l)
    advance_timelock_blocks(2)
    # A transient failure rolls back the earlier scale sync in the same batch.
    original_scale=l.g.desk.tokenScale(l.asset)
    pending=l.s.pendingUpdates(l.asset)
    with boa.env.anchor():
        l.anchor.setMockData(0)
        with boa.reverts('price source not executable'):
            sync_and_confirm(batch,l)
        assert l.g.desk.tokenScale(l.asset)==original_scale
        assert l.s.pendingUpdates(l.asset)==pending
        assert batch._computation.get_log_entries()==()
    result=sync_and_confirm(batch,l)
    assert result==[b'',word(1)]
    assert len(filter_logs(batch,'UniV3FeedUpdated'))==1
    decimals=6 if mismatch_timing=='before_proposal' else 18
    assert l.g.desk.tokenScale(l.asset)==10**decimals
    assert l.s.feedConfig(l.asset).assetDecimals==decimals
    assert l.g.desk.getPrice(l.asset,True)==10**decimals
    assert l.s.pendingQuoteCount(l.weth)==0


def test_identity_cancel_after_sync_leaves_scale_and_darkens_feed(active):
    l=active
    l.g.desk.syncTokenScale(l.asset,sender=l.g.gov)
    l.asset.setDecimals(6)
    l.s.updatePriceFeed(l.asset,*params(l.pool),sender=l.g.gov)
    l.asset.setDecimals(7)
    advance_timelock_blocks(2)
    batch=batch_at_governor(l.g)
    assert sync_and_confirm(batch,l)==[b'',word(0)]
    assert len(filter_logs(batch,'TokenScaleSet'))==1
    assert len(filter_logs(batch,'UniV3FeedUpdateCancelled'))==1
    assert not filter_logs(batch,'UniV3FeedUpdated')
    assert l.g.desk.tokenScale(l.asset)==10**7
    assert l.s.feedConfig(l.asset).assetDecimals==18
    assert l.s.pendingUpdates(l.asset).actionId==0 and l.s.pendingQuoteCount(l.weth)==0
    unavailable(l)


@pytest.mark.parametrize('quote_decimals',[0,6])
@pytest.mark.parametrize('quote_usd',[1,100])
def test_low_decimal_quote_economic_precision(lab,math,quote_decimals,quote_usd):
    lab.weth.setDecimals(quote_decimals)
    g=make_graph()
    quote_price=quote_usd*10**18
    quote_price_source(g,lab.weth,quote_price)
    s=source(g,lab.factory)
    ratio=1e-3/quote_usd*10**quote_decimals/10**18
    tick=round(pymath.log(ratio)/pymath.log(1.0001))
    lab.pool.set_history(tick=tick)
    actual=admit(g,s,lab.asset,params(lab.pool))
    # Independent exact rational ideal; no source result enters the reference.
    ideal=Fraction(10001,10000)**tick
    expected=10**18*ideal*quote_price/10**quote_decimals
    sqrt=math.sqrt(tick)
    assert Fraction((sqrt-1)**2,2**192)<ideal<=Fraction(sqrt*sqrt,2**192)
    tick_bound=Fraction(2*sqrt+1,2**192)*10**18*quote_price/10**quote_decimals
    tolerance=Fraction(quote_price*10**quote_decimals,10**18)+tick_bound+1
    assert abs(actual-expected)<=tolerance
    assert 9*10**14<actual<11*10**14  # a sub-cent asset, approximately $0.001
    assert g.desk.getPrice(lab.asset,True)==actual


@pytest.mark.parametrize('tick',[-887272,0,443636,443637,887272])
@pytest.mark.parametrize('order',[True,False])
def test_scaled_quote_domain_at_tick_extremes_both_orders(lab,math,tick,order):
    ref=deploy('v3','Reference')
    sqrt=ref.sqrt(tick)
    if sqrt<=2**128-1:
        ratio,unit=sqrt*sqrt,2**192
    else:
        assert (sqrt*sqrt).bit_length()<=512
        ratio,unit=sqrt*sqrt//2**64,2**128
    numerator,denominator=(ratio,unit) if order else (unit,ratio)
    assert (numerator*10**36).bit_length()<=512
    expected=numerator*10**36//denominator
    assert expected<2**256
    assert math.quote(tick,10**36,order)==expected
    a,b=('0x'+'01'.zfill(40),'0x'+'02'.zfill(40))
    assert ref.quote(tick,10**36,a if order else b,b if order else a)==expected
    if tick in (443636,443637):
        assert (sqrt>2**128-1)==(tick==443637)
    if (tick,order) in [(-887272,True),(887272,False)]:
        assert expected==0  # unavailable, with no revert or arithmetic truncation
    asset,quote=(lab.asset,lab.weth) if order else (lab.weth,lab.asset)
    g=make_graph();quote_price_source(g,quote,10**18)
    s=source(g,lab.factory)
    admit(g,s,asset,params(lab.pool))
    lab.pool.set_history(tick=tick)
    assert s.getPriceAndHasFeed(asset)==(expected//10**18,True)
    assert g.desk.getPrice(asset)==expected//10**18


def test_final_usd_overflow_is_unavailable(lab):
    g=make_graph()
    q=quote_price_source(g,lab.weth,10**18)
    s=source(g,lab.factory)
    admit(g,s,lab.asset,params(lab.pool))
    q.setPrice(lab.weth,2**256-1)
    lab.pool.set_history(tick=1)
    assert s.getPriceAndHasFeed(lab.asset)==(0,True)
    assert g.desk.getPrice(lab.asset)==0


@pytest.mark.parametrize('stale_time',[0,300])
def test_supplied_desk_is_rejected_unless_canonical_with_zero_and_nonzero_stale_time(active,stale_time):
    l=active
    hostile=Raw({'getPrice(address,bool)':word(2**255),'tokenScale(address)':word(0)})
    for method in ('getPrice','getPriceAndHasFeed'):
        fn=getattr(l.s,method)
        assert fn(l.asset,stale_time,hostile.address)==(0 if method=='getPrice' else (0,True))
        assert fn(l.asset,stale_time,l.g.desk.address)==(10**18 if method=='getPrice' else (10**18,True))


@pytest.mark.parametrize('window',[1800,3600,14400])
def test_age_must_not_exceed_window_per_feed_and_in_defaults(lab,window):
    s=lab.s
    assert s.isValidFeedDefaults(window,window,5000)
    assert not s.isValidFeedDefaults(window,window+1,5000)
    with boa.reverts('invalid defaults'):
        s.setFeedDefaults(window,window+1,5000,sender=lab.g.gov)
    lab.pool.set_history(window=window)
    assert s.isValidNewFeed(lab.asset,*params(lab.pool,window,window))
    assert not s.isValidNewFeed(lab.asset,*params(lab.pool,window,window+1))
    with boa.reverts('invalid feed'):
        s.addNewPriceFeed(lab.asset,*params(lab.pool,window,window+1),sender=lab.g.gov)
    admit(lab.g,s,lab.asset,params(lab.pool,window,window))
    before=state(s,lab.asset)
    with boa.reverts('invalid feed'):
        s.updatePriceFeed(lab.asset,*params(lab.pool,window,window+1),sender=lab.g.gov)
    assert state(s,lab.asset)==before


def test_one_second_liquidity_hole_pins_harmonic_floor_for_window():
    l=canonical()
    admit(l.g,l.s,l.asset,params(l.pool))
    floor=l.s.feedConfig(l.asset).minLiquidity
    start_time=boa.env.timestamp
    l.actor.remove(l.pool.address,10**20)
    boa.env.time_travel(seconds=1)
    l.actor.add(l.pool.address,10**20)
    for elapsed in (1,900,1800,2700,3599,3600):
        boa.env.time_travel(seconds=start_time+elapsed-boa.env.timestamp)
        l.actor.add(l.pool.address,1);l.actor.remove(l.pool.address,1)
        current,harmonic,active_floor=l.s.getFeedLiquidity(l.asset)
        assert current==10**20 and active_floor==floor
        assert harmonic<=3600<floor
        unavailable(l)
    boa.env.time_travel(seconds=1)
    l.actor.add(l.pool.address,1);l.actor.remove(l.pool.address,1)
    assert l.s.getFeedLiquidity(l.asset)[1]>=floor
    assert l.g.desk.getPrice(l.asset,True)==10**18


@pytest.mark.parametrize('window',[1800,3600,14400])
@pytest.mark.parametrize('offset',[-1,0,1])
def test_admission_requires_cardinality_above_window(lab,window,offset):
    lab.pool.set_history(window=window,cardinality=window+offset)
    valid=offset==1
    assert lab.s.isValidNewFeed(lab.asset,*params(lab.pool,window))==valid
    if valid:
        assert admit(lab.g,lab.s,lab.asset,params(lab.pool,window))==10**18
    else:
        with boa.reverts('invalid feed'):
            lab.s.addNewPriceFeed(lab.asset,*params(lab.pool,window),sender=lab.g.gov)


def test_hot_pool_ring_overwrite_after_admission_stays_priceable():
    g=make_graph()
    f,p,a,w,actor,ref=organic_pool(g,cardinality=3601,writes=3600,spacing=1)
    quote_price_source(g,w,10**18)
    s=source(g,f.address)
    assert p.slot0()[3]==3601
    assert admit(g,s,a,params(p))==10**18
    first_index=p.slot0()[2]
    for i in range(3601):
        boa.env.time_travel(seconds=1)
        actor.add(p.address,1);actor.remove(p.address,1)
        if i in (0,1,1799,3599,3600):
            assert g.desk.getPrice(a,True)==10**18
            assert p.observe([3600,0])[0]==[0,0]
    assert p.slot0()[2]==first_index
    assert p.slot0()[3]==3601


def test_explicit_window_update_rechecks_cardinality(lab):
    lab.pool.set_history(window=1800,cardinality=1801)
    admit(lab.g,lab.s,lab.asset,params(lab.pool,1800))
    before=state(lab.s,lab.asset)
    with boa.reverts('invalid feed'):
        lab.s.updatePriceFeed(lab.asset,*params(lab.pool,3600),sender=lab.g.gov)
    assert state(lab.s,lab.asset)==before
    lab.pool.set_history(window=3600,cardinality=3601)
    lab.s.updatePriceFeed(lab.asset,*params(lab.pool,3600),sender=lab.g.gov)
    advance_timelock_blocks(2)
    assert lab.s.confirmPriceFeedUpdate(lab.asset,sender=lab.g.gov)
    assert lab.s.feedConfig(lab.asset).twapWindow==3600


def test_defaults_setter_is_pause_gated_and_rejects_ratio_zero(lab):
    s=lab.s
    assert tuple(s.feedDefaults())==(3600,1800,5000)
    with boa.reverts('invalid defaults'):
        s.setFeedDefaults(3600,1800,0,sender=lab.g.gov)
    assert not s.isValidFeedDefaults(3600,1800,0)
    s.pause(True,sender=lab.g.actor.address)
    with boa.reverts('contract paused'):
        s.setFeedDefaults(1800,900,1,sender=lab.g.gov)
    assert tuple(s.feedDefaults())==(3600,1800,5000)
    s.pause(False,sender=lab.g.actor.address)
    assert s.setFeedDefaults(1800,900,1,sender=lab.g.gov)
    event=filter_logs(s,'FeedDefaultsSet')[0]
    assert (event.twapWindow,event.maxObservationAge,event.minLiquidityRatio)==(1800,900,1)


@pytest.mark.parametrize('kind',[1,2])
def test_mid_timelock_defaults_change_does_not_alter_in_flight_proposal(lab,kind):
    start(lab,kind)
    pending=lab.s.pendingUpdates(lab.asset)
    assert pending.config.twapWindow==3600
    assert pending.config.maxObservationAge==(1800 if kind==1 else 1799)
    lab.s.setFeedDefaults(14400,1,10000,sender=lab.g.gov)
    assert lab.s.pendingUpdates(lab.asset)==pending
    advance_timelock_blocks(2)
    assert getattr(lab.s,CONFIRM[kind])(lab.asset,sender=lab.g.gov)
    event=filter_logs(lab.s,'NewUniV3FeedAdded' if kind==1 else 'UniV3FeedUpdated')[0]
    assert lab.s.feedConfig(lab.asset)==pending.config
    assert (event.twapWindow,event.maxObservationAge,event.minLiquidity)==(pending.config.twapWindow,pending.config.maxObservationAge,pending.config.minLiquidity)


def test_post_confirm_defaults_change_does_not_alter_feed_floor_window_or_age(active):
    l=active
    config=l.s.feedConfig(l.asset)
    l.s.setFeedDefaults(14400,1,10000,sender=l.g.gov)
    l.pool.set('observations(uint256)',words(boa.env.timestamp-1800,0,0,1))
    l.pool.set('liquidity()',word(config.minLiquidity))
    assert l.s.feedConfig(l.asset)==config
    assert l.s.getFeedLiquidity(l.asset)[2]==config.minLiquidity
    assert l.g.desk.getPrice(l.asset,True)==10**18
    l.pool.set('observations(uint256)',words(boa.env.timestamp-1801,0,0,1))
    unavailable(l)


@pytest.mark.parametrize('kind',[1,2])
@pytest.mark.parametrize('identity',['asset_decimals','quote_decimals','fee','factory','pool_gone'])
def test_identity_drift_cancels_with_event_for_add_and_update(lab,kind,identity):
    start(lab,kind)
    p=lab.s.pendingUpdates(lab.asset)
    active=lab.s.feedConfig(lab.asset)
    if identity=='asset_decimals':lab.asset.setDecimals(6)
    elif identity=='quote_decimals':lab.weth.setDecimals(6)
    elif identity=='fee':lab.pool.set('fee()',word(3000))
    elif identity=='factory':lab.factory.setPool(lab.asset,lab.weth,10000,boa.env.generate_address())
    else:boa.env.set_code(lab.pool.address,b'')
    # Identity cancellation deliberately precedes the timelock check.
    assert not getattr(lab.s,CONFIRM[kind])(lab.asset,sender=lab.g.gov)
    events=filter_logs(lab.s,CANCELLED_EVENT[kind])
    assert len(events)==1 and events[0].pool==p.config.pool
    assert lab.s.pendingUpdates(lab.asset).actionId==0
    assert not lab.s.hasPendingAction(p.actionId)
    assert lab.s.pendingQuoteCount(lab.weth)==0
    assert lab.s.feedConfig(lab.asset)==active


@pytest.mark.parametrize('broken',['metadata','dependencies'])
def test_disable_confirms_with_event_when_metadata_or_dependencies_are_broken(active,broken):
    l=active
    l.s.disablePriceFeed(l.asset,sender=l.g.gov)
    if broken=='metadata':
        l.asset.setDecimals(255);l.weth.setDecimals(255)
    else:
        for dependency in (l.pool,l.anchor,l.factory,l.g.desk):
            Raw({},address=dependency.address)
    advance_timelock_blocks(2)
    assert l.s.confirmDisablePriceFeed(l.asset,sender=l.g.gov)
    assert len(filter_logs(l.s,'UniV3FeedDisabled'))==1
    assert not l.s.hasPriceFeed(l.asset)
    assert l.s.pendingQuoteCount(l.weth)==0


def transient(lab,fault):
    if fault=='liquidity':
        lab.pool.set('liquidity()',word(lab.s.pendingUpdates(lab.asset).config.minLiquidity-1))
    elif fault=='OLD':
        lab.pool.set('observe(uint32[])',Revert(selector('Error(string)')+encode(['string'],['OLD'])))
    elif fault=='locked':
        lab.pool.set('slot0()',words(2**96,0,0,65535,65535,0,0))
    elif fault=='zero_quote':
        lab.anchor.setMockData(0)
    elif fault=='callback':
        Raw({'tokenScale(address)':word(0),'getPrice(address,bool)':word(10**18),
             'qualifyCallerPriceSource(address)':words(0,1)},address=lab.g.desk.address)
    elif fault=='scale':
        lab.asset.setDecimals(6)
        lab.g.desk.syncTokenScale(lab.asset,sender=lab.g.gov)
        lab.asset.setDecimals(18)
    return 'invalid feed' if fault=='scale' else 'price source not executable'


@pytest.mark.parametrize('kind',[1,2])
@pytest.mark.parametrize('fault',['liquidity','OLD','locked','zero_quote','callback','scale'])
def test_transient_failure_reverts_and_keeps_pending(lab,kind,fault):
    start(lab,kind)
    advance_timelock_blocks(2)
    before=state(lab.s,lab.asset)
    count=lab.s.pendingQuoteCount(lab.weth)
    with boa.env.anchor():
        reason=transient(lab,fault)
        with boa.reverts(reason):getattr(lab.s,CONFIRM[kind])(lab.asset,sender=lab.g.gov)
        assert lab.s._computation.get_log_entries()==()
        assert state(lab.s,lab.asset)==before
        assert lab.s.pendingQuoteCount(lab.weth)==count==1
    assert getattr(lab.s,CONFIRM[kind])(lab.asset,sender=lab.g.gov)
    assert lab.s.pendingQuoteCount(lab.weth)==0


@pytest.mark.parametrize('kind',[1,2])
def test_reverted_confirmation_leaves_state_and_logs_unchanged(lab,kind):
    start(lab,kind)
    advance_timelock_blocks(2)
    before=state(lab.s,lab.asset)
    lab.anchor.setMockData(0)
    with boa.reverts('price source not executable'):
        getattr(lab.s,CONFIRM[kind])(lab.asset,sender=lab.g.gov)
    assert lab.s._computation.get_log_entries()==()
    assert state(lab.s,lab.asset)==before
    assert lab.s.pendingQuoteCount(lab.weth)==1


@pytest.mark.parametrize('kind',[1,2,3])
def test_explicit_cancel_emits_once(lab,kind):
    start(lab,kind)
    assert getattr(lab.s,CANCEL[kind])(lab.asset,sender=lab.g.gov)
    assert len(filter_logs(lab.s,CANCELLED_EVENT[kind]))==1
    assert sum(len(filter_logs(lab.s,event)) for event in CANCELLED_EVENT.values())==1
    assert lab.s.pendingQuoteCount(lab.weth)==0


def third_token(lab):
    token=boa.load('contracts/mock/MockChainlinkFeed.vy',10**18)
    token.setDecimals(18)
    quote_price_source(lab.g,token,10**18)
    return token


def test_asset_that_is_a_pending_quote_is_rejected(lab):
    c=third_token(lab)
    pool=Pool(lab.weth,c,lab.factory)
    lab.factory.setPool(lab.weth,c,10000,pool.address)
    assert lab.s.isValidNewFeed(lab.weth,*params(pool))
    lab.s.addNewPriceFeed(lab.asset,*params(lab.pool),sender=lab.g.gov)
    assert lab.s.pendingQuoteCount(lab.weth)==1
    assert not lab.s.isValidNewFeed(lab.weth,*params(pool))
    with boa.reverts('invalid feed'):
        lab.s.addNewPriceFeed(lab.weth,*params(pool),sender=lab.g.gov)


@pytest.mark.parametrize('kind',[1,2])
@pytest.mark.parametrize('exit_kind',['confirm','cancel','identity','revert','expiry_then_cancel'])
def test_pending_quote_count_on_every_exit(lab,kind,exit_kind):
    start(lab,kind)
    assert lab.s.pendingQuoteCount(lab.weth)==1
    if exit_kind=='confirm':
        advance_timelock_blocks(2)
        assert getattr(lab.s,CONFIRM[kind])(lab.asset,sender=lab.g.gov)
    elif exit_kind=='identity':
        lab.asset.setDecimals(6)
        assert not getattr(lab.s,CONFIRM[kind])(lab.asset,sender=lab.g.gov)
    elif exit_kind=='revert':
        advance_timelock_blocks(2)
        lab.anchor.setMockData(0)
        with boa.reverts('price source not executable'):
            getattr(lab.s,CONFIRM[kind])(lab.asset,sender=lab.g.gov)
        assert lab.s.pendingQuoteCount(lab.weth)==1
        getattr(lab.s,CANCEL[kind])(lab.asset,sender=lab.g.gov)
    else:
        if exit_kind=='expiry_then_cancel':advance_timelock_blocks(102)
        getattr(lab.s,CANCEL[kind])(lab.asset,sender=lab.g.gov)
    assert lab.s.pendingQuoteCount(lab.weth)==0
    # Two proposals share a quote. Finishing either must release just its count.
    if exit_kind=='identity':lab.asset.setDecimals(18)
    if exit_kind=='revert':lab.anchor.setMockData(10**8)
    c=third_token(lab)
    pool=Pool(c,lab.weth,lab.factory)
    lab.factory.setPool(c,lab.weth,10000,pool.address)
    if lab.s.hasPriceFeed(lab.asset):
        lab.s.updatePriceFeed(lab.asset,*params(lab.pool),sender=lab.g.gov)
        cancel='cancelPriceFeedUpdate'
    else:
        lab.s.addNewPriceFeed(lab.asset,*params(lab.pool),sender=lab.g.gov)
        cancel='cancelNewPendingPriceFeed'
    lab.s.addNewPriceFeed(c,*params(pool),sender=lab.g.gov)
    assert lab.s.pendingQuoteCount(lab.weth)==2
    getattr(lab.s,cancel)(lab.asset,sender=lab.g.gov)
    assert lab.s.pendingQuoteCount(lab.weth)==1
    advance_timelock_blocks(2)
    assert lab.s.confirmNewPriceFeed(c,sender=lab.g.gov)
    assert lab.s.pendingQuoteCount(lab.weth)==0


def test_pending_quote_count_on_every_exit_when_update_changes_quote(active):
    l=active
    c=third_token(l)
    pool=Pool(l.asset,c,l.factory)
    l.factory.setPool(l.asset,c,10000,pool.address)
    l.s.updatePriceFeed(l.asset,*params(pool),sender=l.g.gov)
    assert l.s.pendingQuoteCount(c)==1 and l.s.pendingQuoteCount(l.weth)==0
    # The old quote stays protected by the active feed until replacement commits.
    reverse=Pool(l.weth,c,l.factory)
    l.factory.setPool(l.weth,c,10000,reverse.address)
    assert not l.s.isValidNewFeed(l.weth,*params(reverse))
    advance_timelock_blocks(2)
    assert l.s.confirmPriceFeedUpdate(l.asset,sender=l.g.gov)
    assert l.s.pendingQuoteCount(c)==0
    assert l.s.isValidNewFeed(l.weth,*params(reverse))


@pytest.mark.parametrize('route',['cross_instance','wrapper'])
def test_cross_instance_and_wrapper_cycles_fail_closed_when_fallback_removed(lab,route):
    g=make_graph()
    independent=quote_price_source(g,lab.asset,10**18)
    if route=='cross_instance':
        other=source(g,lab.factory)
        admit(g,other,lab.weth,params(lab.pool))
    else:
        other=boa.load('tests/priceSources/uniswap_v3/WrapperQuoteSource.vy',lab.weth,lab.asset,g.desk)
        register(g.desk,other,g.gov)
    s=source(g,lab.factory)
    assert admit(g,s,lab.asset,params(lab.pool))==10**18
    assert g.desk.getPrice(lab.weth,True)==10**18
    rid=g.desk.getRegId(independent)
    g.desk.startAddressDisableInRegistry(rid,sender=g.gov)
    advance_timelock_blocks(g.desk.registryChangeTimeLock())
    assert g.desk.confirmAddressDisableInRegistry(rid,sender=g.gov)
    assert g.desk.getPrice(lab.asset)==0
    assert g.desk.getPrice(lab.weth)==0
