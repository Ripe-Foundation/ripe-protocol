import boa
import pytest
from .helpers import state,settings
from conf_utils import advance_timelock_blocks,filter_logs

from .graph import SOURCE,source,params,admit,make_graph,register,ZERO,ETH
from .raw import Pool,Raw,word,words
from .gas_tools import calls

WITNESS='tests/priceSources/uniswap_v3/StagingWethSource.vy'
CONFIRM={1:'confirmNewPriceFeed',2:'confirmPriceFeedUpdate',3:'confirmDisablePriceFeed'}
CANCEL={1:'cancelNewPendingPriceFeed',2:'cancelPriceFeedUpdate',3:'cancelDisablePriceFeed'}
PENDING_EVENT={1:'NewUniV3FeedPending',2:'UniV3FeedUpdatePending',3:'DisableUniV3FeedPending'}
CONFIRMED_EVENT={1:'NewUniV3FeedAdded',2:'UniV3FeedUpdated',3:'UniV3FeedDisabled'}
CANCELLED_EVENT={1:'NewUniV3FeedCancelled',2:'UniV3FeedUpdateCancelled',3:'DisableUniV3FeedCancelled'}
NO_PENDING={1:'no pending new feed',2:'no pending update feed',3:'no pending disable feed'}
DEFAULTS=(3600,1800,50_00)


def start(lab,kind):
    if kind!=1:admit(lab.g,lab.s,lab.asset,params(lab.pool))
    if kind==1:lab.s.addNewPriceFeed(lab.asset,*params(lab.pool),sender=lab.g.gov)
    elif kind==2:lab.s.updatePriceFeed(lab.asset,*params(lab.pool,age=1799),sender=lab.g.gov)
    else:lab.s.disablePriceFeed(lab.asset,sender=lab.g.gov)
    return filter_logs(lab.s,PENDING_EVENT[kind])[0]


def staged_graph(lab,reject):
    """A fresh graph whose WETH source witnesses the V3 source's staged state."""
    g=make_graph()
    witness=boa.load(WITNESS,lab.weth)
    register(g.desk,witness,g.gov)
    s=source(g,lab.factory)
    witness.watch(s,lab.asset,0,reject)
    return g,s,witness


def test_constructor_and_empty_state(lab):
    s=lab.s
    assert s.actionTimeLock()==2 and s.expiration()==100
    assert not s.isPaused()
    assert s.getPricedAssets()==[]
    assert s.getPriceAndHasFeed(lab.asset)==(0,False)
    assert s.feedConfig(lab.asset).pool==ZERO
    assert s.pendingUpdates(lab.asset).actionId==0
    assert s.FACTORY()==lab.factory.address
    assert tuple(s.feedDefaults())==DEFAULTS
    assert s.getFeedLiquidity(lab.asset)==(0,0,0)
    assert lab.g.desk.getRegId(s)==0
    # like every other source, the action delay is set once after deployment
    fresh=source(lab.g,lab.factory,delay=0)
    assert fresh.actionTimeLock()==0
    assert fresh.setActionTimeLockAfterSetup(sender=lab.g.gov)
    assert fresh.actionTimeLock()==2
    with boa.reverts('already set'):fresh.setActionTimeLockAfterSetup(3,sender=lab.g.gov)


def test_constructor_rejects_empty_factory(lab):
    with boa.reverts('invalid factory'):boa.load(SOURCE,lab.g.hq,lab.g.local,2,100,ZERO)


@pytest.mark.parametrize('minimum,maximum',[(0,100),(100,100),(101,100),(2,2**256-1)])
def test_constructor_retains_module_validation(lab,minimum,maximum):
    with boa.reverts('invalid time lock boundaries'):
        boa.load(SOURCE,lab.g.hq,lab.g.local,minimum,maximum,lab.factory)


def test_feed_defaults_permissions_domains_and_event(lab):
    s=lab.s
    with boa.reverts('no perms'):s.setFeedDefaults(1800,1800,50_00,sender=boa.env.generate_address())
    for bad in [(1799,1800,50_00),(14401,3600,50_00),(1800,0,50_00),(1800,1801,50_00),(1800,1800,100_01),(1800,1800,0)]:
        assert not s.isValidFeedDefaults(*bad)
        with boa.reverts('invalid defaults'):s.setFeedDefaults(*bad,sender=lab.g.gov)
    for good in [(1800,1,1),(14400,14400,100_00)]:
        assert s.isValidFeedDefaults(*good)
        assert s.setFeedDefaults(*good,sender=lab.g.gov)
        event=filter_logs(s,'FeedDefaultsSet')[0]
        assert (event.twapWindow,event.maxObservationAge,event.minLiquidityRatio)==good
        assert tuple(s.feedDefaults())==good
    assert tuple(s.feedDefaults())!=DEFAULTS


@pytest.mark.parametrize('kind',[1,2,3])
@pytest.mark.parametrize('boundary',[-1,0,99,100,101])
def test_confirmation_interval_and_events(lab,kind,boundary):
    s,a,g=lab.s,lab.asset,lab.g
    pending_event=start(lab,kind)
    p=s.pendingUpdates(a);action=s.pendingActions(p.actionId)
    assert action.confirmBlock==boa.env.evm.patch.block_number+2
    assert action.expiration==action.confirmBlock+100
    assert (pending_event.asset,pending_event.pool)==(a.address,lab.pool.address)
    assert (pending_event.confirmationBlock,pending_event.actionId)==(action.confirmBlock,p.actionId)
    if kind!=3:
        assert pending_event.quoteAsset==lab.weth.address
        assert pending_event.baseLiquidity==p.config.baseLiquidity>0
    assert s.hasPendingPriceFeedUpdate(a)
    before=state(s,a)
    advance_timelock_blocks(2+boundary)
    if boundary<0 or boundary>=100:
        with boa.reverts('time lock not reached'):getattr(s,CONFIRM[kind])(a,sender=g.gov)
        assert s._computation.get_log_entries()==()
        assert state(s,a)==before
        assert s.hasPendingAction(p.actionId)
    else:
        assert getattr(s,CONFIRM[kind])(a,sender=g.gov)
        event=filter_logs(s,CONFIRMED_EVENT[kind])[0]
        assert (event.asset,event.pool)==(a.address,lab.pool.address)
        assert s.pendingUpdates(a).actionId==0 and not s.hasPendingAction(p.actionId)
        assert not s.hasPendingPriceFeedUpdate(a)
        assert s.hasPriceFeed(a)==(kind!=3)
        with boa.reverts(NO_PENDING[kind]):getattr(s,CONFIRM[kind])(a,sender=g.gov)


@pytest.mark.parametrize('kind',[1,2,3])
def test_wrong_selectors_pending_collision_and_expired_cancel(lab,kind):
    s,a,g=lab.s,lab.asset,lab.g
    start(lab,kind)
    before=state(s,a)
    for other in (1,2,3):
        if other!=kind:
            with boa.reverts(NO_PENDING[other]):getattr(s,CONFIRM[other])(a,sender=g.gov)
            with boa.reverts(NO_PENDING[other]):getattr(s,CANCEL[other])(a,sender=g.gov)
            assert state(s,a)==before
    proposals=[lambda:s.addNewPriceFeed(a,*params(lab.pool),sender=g.gov),
               lambda:s.updatePriceFeed(a,*params(lab.pool,age=1798),sender=g.gov),
               lambda:s.disablePriceFeed(a,sender=g.gov)]
    for expired in (False,True):
        if expired:advance_timelock_blocks(102)
        for propose in proposals:
            with boa.reverts('pending feed action'):propose()
        assert state(s,a)==before
        assert s.hasPendingPriceFeedUpdate(a)
    # cancellation, even of an expired action, needs no pool, feed or desk
    Raw({},address=lab.pool.address);Raw({},address=lab.anchor.address);Raw({},address=g.desk.address)
    assert getattr(s,CANCEL[kind])(a,sender=g.gov)
    event=filter_logs(s,CANCELLED_EVENT[kind])[0]
    assert (event.asset,event.pool)==(a.address,lab.pool.address)
    assert s.pendingUpdates(a).actionId==0 and not s.hasPendingPriceFeedUpdate(a)
    assert s.feedConfig(a)==before[0]


@pytest.mark.parametrize('kind',[1,2,3])
def test_pause_and_permissions_for_all_feed_selectors(lab,kind):
    s,a,g=lab.s,lab.asset,lab.g
    start(lab,kind)
    outsider=boa.env.generate_address()
    mutations=[lambda sender:s.addNewPriceFeed(a,*params(lab.pool),sender=sender),lambda sender:s.updatePriceFeed(a,*params(lab.pool),sender=sender),lambda sender:s.disablePriceFeed(a,sender=sender),lambda sender:getattr(s,CONFIRM[kind])(a,sender=sender),lambda sender:getattr(s,CANCEL[kind])(a,sender=sender)]
    before=state(s,a)
    for call in mutations:
        with boa.reverts('no perms'):call(outsider)
    s.pause(True,sender=g.actor.address)
    for call in mutations:
        with boa.reverts('contract paused'):call(g.gov)
    assert state(s,a)==before
    assert s.getPrice(a)==(0 if kind==1 else 10**18)
    s.pause(False,sender=g.actor.address)
    assert getattr(s,CANCEL[kind])(a,sender=g.gov)


@pytest.mark.parametrize('field,value',[(1,1799),(1,14401),(2,86401)])
def test_numeric_admission_domains(lab,field,value):
    p=list(params(lab.pool));p[field]=value
    before=state(lab.s,lab.asset)
    assert not lab.s.isValidNewFeed(lab.asset,*p)
    with boa.reverts('invalid feed'):lab.s.addNewPriceFeed(lab.asset,*p,sender=lab.g.gov)
    assert state(lab.s,lab.asset)==before


@pytest.mark.parametrize('window,age',[(0,0),(1800,1),(14400,14400),(3600,3600)])
def test_inclusive_admission_domains(lab,window,age):
    # Synthetic raw observations match the chosen lookback; this tests domains.
    lab.pool.set_history(window=window or 3600)
    assert lab.s.isValidNewFeed(lab.asset,*params(lab.pool,window=window,age=age))
    assert admit(lab.g,lab.s,lab.asset,params(lab.pool,window=window,age=age))==10**18
    assert settings(lab.s.feedConfig(lab.asset))==params(lab.pool,window=window or 3600,age=age or 1800)


@pytest.mark.parametrize('asset_kind',['zero','native','eoa','not_in_pool'])
def test_assets_the_pool_does_not_hold_are_rejected(lab,asset_kind):
    a={'zero':ZERO,'native':ETH,'eoa':boa.env.generate_address(),'not_in_pool':lab.anchor.address}[asset_kind]
    assert not lab.s.isValidNewFeed(a,*params(lab.pool))
    with boa.reverts('invalid feed'):lab.s.addNewPriceFeed(a,*params(lab.pool),sender=lab.g.gov)


@pytest.mark.parametrize('pool_kind',['eoa','wrong_fee','not_canonical'])
def test_pool_identity_is_bound_to_the_factory(lab,pool_kind):
    p=list(params(lab.pool))
    if pool_kind=='eoa':p[0]=boa.env.generate_address()
    elif pool_kind=='wrong_fee':lab.pool.set('fee()',word(3000))
    else:
        other=Pool(lab.asset,lab.weth,lab.factory)  # a real-looking pool the factory does not map to
        p[0]=other.address
    assert not lab.s.isValidNewFeed(lab.asset,*p)
    with boa.reverts('invalid feed'):lab.s.addNewPriceFeed(lab.asset,*p,sender=lab.g.gov)


@pytest.mark.parametrize('cardinality',[3599,3600,3601])
def test_observation_cardinality_floor_is_an_admission_check(lab,cardinality):
    lab.pool.set_history(cardinality=cardinality)
    valid=cardinality>=3601
    assert lab.s.isValidNewFeed(lab.asset,*params(lab.pool))==valid
    if not valid:
        with boa.reverts('invalid feed'):lab.s.addNewPriceFeed(lab.asset,*params(lab.pool),sender=lab.g.gov)
        return
    admit(lab.g,lab.s,lab.asset,params(lab.pool))
    # a shrunk ring later does not stop reads; a raised floor applies to new proposals
    lab.pool.set_history(cardinality=1)
    assert lab.g.desk.getPrice(lab.asset,True)==10**18
    lab.s.setFeedDefaults(cardinality,1800,50_00,sender=lab.g.gov)
    lab.pool.set_history(cardinality=cardinality)
    assert not lab.s.isValidUpdateFeed(lab.asset,*params(lab.pool))


def test_no_v3_feed_may_depend_on_another_v3_feed(lab):
    s,g,a,w=lab.s,lab.g,lab.asset,lab.weth
    # pending A/WETH already blocks a WETH feed quoted in A (the same pool, reversed)
    s.addNewPriceFeed(a,*params(lab.pool),sender=g.gov)
    assert not s.isValidNewFeed(w,*params(lab.pool))
    with boa.reverts('invalid feed'):s.addNewPriceFeed(w,*params(lab.pool),sender=g.gov)
    advance_timelock_blocks(2);assert s.confirmNewPriceFeed(a,sender=g.gov)
    # active A/WETH: WETH is the quote of an active feed, and A is v3-priced
    assert not s.isValidNewFeed(w,*params(lab.pool))
    with boa.reverts('invalid feed'):s.addNewPriceFeed(w,*params(lab.pool),sender=g.gov)
    # a second asset quoted in A would depend on this source too
    b=boa.load('contracts/mock/MockChainlinkFeed.vy',10**18);b.setDecimals(18)
    pool=Pool(b,a,lab.factory);lab.factory.setPool(b,a,10000,pool.address)
    assert not s.isValidNewFeed(b,*params(pool))
    with boa.reverts('invalid feed'):s.addNewPriceFeed(b,*params(pool),sender=g.gov)


@pytest.mark.parametrize('dependency',['pool','factory','fee','asset_decimals','quote_decimals'])
def test_metadata_drift_after_proposal_cancels_at_confirmation(lab,dependency):
    lab.s.addNewPriceFeed(lab.asset,*params(lab.pool),sender=lab.g.gov)
    aid=lab.s.pendingUpdates(lab.asset).actionId
    if dependency=='pool':boa.env.set_code(lab.pool.address,b'')
    elif dependency=='factory':lab.factory.setPool(lab.asset,lab.weth,10000,boa.env.generate_address())
    elif dependency=='fee':lab.pool.set('fee()',word(3000))
    elif dependency=='asset_decimals':lab.asset.setDecimals(6)
    else:lab.weth.setDecimals(6)
    advance_timelock_blocks(2)
    # like the other sources, a proposal whose reviewed identity drifted is cancelled, not confirmed
    assert not lab.s.confirmNewPriceFeed(lab.asset,sender=lab.g.gov)
    assert lab.s.pendingUpdates(lab.asset).actionId==0 and not lab.s.hasPendingAction(aid)
    assert not lab.s.hasPriceFeed(lab.asset) and lab.s.getPricedAssets()==[]
    if dependency=='asset_decimals':
        # decimals are re-snapshotted by a fresh proposal
        assert admit(lab.g,lab.s,lab.asset,params(lab.pool))==10**6
        assert lab.s.feedConfig(lab.asset).assetDecimals==6
    elif dependency=='quote_decimals':
        assert admit(lab.g,lab.s,lab.asset,params(lab.pool))==10**30
        assert lab.s.feedConfig(lab.asset).quoteDecimals==6
    else:
        assert not lab.s.isValidNewFeed(lab.asset,*params(lab.pool))
        with boa.reverts('invalid feed'):lab.s.addNewPriceFeed(lab.asset,*params(lab.pool),sender=lab.g.gov)


def test_update_replaces_settings_and_rebaselines_liquidity(active,math):
    l=active;s=l.s;a=l.asset
    base=s.feedConfig(a).baseLiquidity
    # the same settings are a valid update: it re-baselines the liquidity floor
    l.pool.set_history(liquidity=4*10**20)
    assert s.isValidUpdateFeed(a,*params(l.pool))
    p=params(l.pool,window=1800,age=1600)
    l.pool.set_history(window=1800,liquidity=4*10**20)
    s.updatePriceFeed(a,*p,sender=l.g.gov)
    assert settings(s.feedConfig(a))==params(l.pool,window=3600,age=1800) and s.feedConfig(a).baseLiquidity==base
    pending=s.pendingUpdates(a).config
    assert settings(pending)==p and pending.baseLiquidity==math.harmonic(0,1800*2**128//(4*10**20),1800)>base
    advance_timelock_blocks(2)
    assert s.confirmPriceFeedUpdate(a,sender=l.g.gov)
    assert settings(s.feedConfig(a))==p and s.feedConfig(a).baseLiquidity==pending.baseLiquidity
    assert s.getFeedLiquidity(a)==(4*10**20,pending.baseLiquidity,(pending.baseLiquidity+1)//2)


def test_update_transient_quote_failure_keeps_the_proposal(active):
    l=active
    l.s.updatePriceFeed(l.asset,*params(l.pool,age=1600),sender=l.g.gov)
    aid=l.s.pendingUpdates(l.asset).actionId
    advance_timelock_blocks(2)
    l.anchor.setMockData(0)
    with boa.reverts('price source not executable'):
        l.s.confirmPriceFeedUpdate(l.asset,sender=l.g.gov)
    assert l.s.pendingUpdates(l.asset).actionId==aid and l.s.hasPendingAction(aid)
    assert settings(l.s.feedConfig(l.asset))==params(l.pool,window=3600,age=1800)
    l.anchor.setMockData(10**8)
    assert l.g.desk.getPrice(l.asset,True)==10**18


@pytest.mark.parametrize('decimals',[0,18])
@pytest.mark.parametrize('reject',[False,True])
def test_first_add_callback_staging_and_complete_rollback(lab,decimals,reject):
    lab.asset.setDecimals(decimals)
    g,s,witness=staged_graph(lab,reject)
    assert s.addNewPriceFeed(lab.asset,*params(lab.pool),sender=g.gov)
    assert filter_logs(s,'NewUniV3FeedPending')[0].pool==lab.pool.address
    before=state(s,lab.asset)
    advance_timelock_blocks(2)
    if reject:
        with boa.reverts('price source not executable'):s.confirmNewPriceFeed(lab.asset,sender=g.gov)
        assert s._computation.get_log_entries()==()
        assert state(s,lab.asset)==before
        assert s.hasPendingAction(before[1].actionId)
    else:
        assert s.confirmNewPriceFeed(lab.asset,sender=g.gov)
        trace=s._computation
        assert s.getPricedAssets()==[lab.asset.address]
        assert s.feedConfig(lab.asset).assetDecimals==decimals
        assert s.getPrice(lab.asset)==10**decimals
        # The unchanged desk really made the price callback under the hard cap.
        qualification=[c for c in calls(trace,g.desk) if bytes(c.msg.data[:4])==bytes(g.desk.qualifyCallerPriceSource.prepare_calldata(lab.asset)[:4])]
        assert len(qualification)==1 and qualification[0].output==words(10**decimals,1)
        price_children=[c for c in qualification[0].children if c.msg.code_address==bytes.fromhex(s.address[2:])]
        assert len(price_children)==1 and price_children[0].msg.gas==250000
    assert g.desk.getRegId(s)==0


def test_failed_update_callback_rolls_back_staged_config(lab):
    g,s,witness=staged_graph(lab,False)
    admit(g,s,lab.asset,params(lab.pool))
    witness.watch(s,lab.asset,1,True)
    s.updatePriceFeed(lab.asset,*params(lab.pool,age=1600),sender=g.gov)
    before=state(s,lab.asset)
    advance_timelock_blocks(2)
    with boa.reverts('price source not executable'):s.confirmPriceFeedUpdate(lab.asset,sender=g.gov)
    assert s._computation.get_log_entries()==()
    assert state(s,lab.asset)==before
    assert settings(s.feedConfig(lab.asset))==params(lab.pool,window=3600,age=1800)


def test_disable_during_market_outage(active):
    l=active
    Raw({},address=l.pool.address);Raw({},address=l.anchor.address);Raw({},address=l.g.desk.address)
    l.s.disablePriceFeed(l.asset,sender=l.g.gov)
    advance_timelock_blocks(2)
    assert l.s.confirmDisablePriceFeed(l.asset,sender=l.g.gov)
    assert l.s.getPriceAndHasFeed(l.asset)==(0,False)
    assert l.s.getPricedAssets()==[]


def test_capacity_competing_pending_and_first_middle_last_removal(lab):
    tokens=[]
    for i in range(51):
        token=boa.load('contracts/mock/MockChainlinkFeed.vy',10**18);token.setDecimals(18)
        pool=Pool(token,lab.weth,lab.factory)
        lab.factory.setPool(token,lab.weth,10000,pool.address)
        tokens.append((token,pool))
        if i<49:admit(lab.g,lab.s,token,params(pool),register_source=False)
    for token,pool in tokens[49:]:lab.s.addNewPriceFeed(token,*params(pool),sender=lab.g.gov)
    advance_timelock_blocks(2)
    assert lab.s.confirmNewPriceFeed(tokens[49][0],sender=lab.g.gov)
    # a pending add holds no capacity; the module's cap fires at confirmation and reverts everything
    before=state(lab.s,tokens[50][0])
    with boa.reverts('too many assets'):lab.s.confirmNewPriceFeed(tokens[50][0],sender=lab.g.gov)
    assert lab.s._computation.get_log_entries()==()
    assert state(lab.s,tokens[50][0])==before
    assert len(lab.s.getPricedAssets())==50 and lab.s.numAssets()==51
    lab.s.cancelNewPendingPriceFeed(tokens[50][0],sender=lab.g.gov)
    for index in (0,24,49):
        asset=lab.s.getPricedAssets()[index]
        token,pool=next((t,p) for t,p in tokens if t.address==asset)
        lab.s.disablePriceFeed(token,sender=lab.g.gov);advance_timelock_blocks(2)
        lab.s.confirmDisablePriceFeed(token,sender=lab.g.gov)
        assert len(lab.s.getPricedAssets())==49 and lab.s.indexOfAsset(token)==0
        admit(lab.g,lab.s,token,params(pool),register_source=False)
        assert lab.s.indexOfAsset(token)==50
        assets=lab.s.getPricedAssets()
        assert len(assets)==len(set(assets))==50
        for i,a in enumerate(assets,1):assert lab.s.indexOfAsset(a)==i


@pytest.mark.parametrize('operation',['add','update','disable'])
def test_active_feed_predicates_reject_without_any_state_change(lab,operation):
    s,a,g=lab.s,lab.asset,lab.g
    if operation=='add':
        admit(g,s,a,params(lab.pool))
    before=state(s,a)
    reason='invalid asset' if operation=='disable' else 'invalid feed'
    with boa.reverts(reason):
        if operation=='add':s.addNewPriceFeed(a,*params(lab.pool),sender=g.gov)
        elif operation=='update':s.updatePriceFeed(a,*params(lab.pool),sender=g.gov)
        else:s.disablePriceFeed(a,sender=g.gov)
    assert s._computation.get_log_entries()==()
    assert state(s,a)==before
    assert not (s.isValidNewFeed(a,*params(lab.pool)) if operation=='add' else s.isValidUpdateFeed(a,*params(lab.pool)) if operation=='update' else s.isValidDisablePriceFeed(a))


def test_pending_window_update_keeps_old_price_until_confirmation(lab):
    from .compiled import deploy
    ref=deploy('v3','Reference')
    # Fixed cumulative delta gives mean tick 100 at 1800s and 50 at 3600s.
    lab.pool.set_history(tick=100,window=1800)
    old=ref.quote(100,10**18,lab.asset.address,lab.weth.address)
    new=ref.quote(50,10**18,lab.asset.address,lab.weth.address)
    assert old!=new and admit(lab.g,lab.s,lab.asset,params(lab.pool,window=1800))==old
    lab.s.updatePriceFeed(lab.asset,*params(lab.pool,window=3600),sender=lab.g.gov)
    assert lab.s.pendingUpdates(lab.asset).config.twapWindow==3600
    assert lab.s.feedConfig(lab.asset).twapWindow==1800
    assert lab.s.getPrice(lab.asset)==lab.g.desk.getPrice(lab.asset,True)==old
    advance_timelock_blocks(2)
    assert lab.s.confirmPriceFeedUpdate(lab.asset,sender=lab.g.gov)
    assert lab.s.feedConfig(lab.asset).twapWindow==3600
    assert lab.s.getPrice(lab.asset)==lab.g.desk.getPrice(lab.asset,True)==new


@pytest.mark.parametrize('kind',[1,2,3])
def test_defensive_confirmation_active_state_guards(lab,kind):
    from eth_utils import keccak
    start(lab,kind)
    # Synthetic storage fault: public lifecycle/pending collision rules prevent
    # these states. Exercise the confirm-time defense independently of proposal.
    position=lab.s.compiler_data.storage_layout['storage_layout']['feedConfig']['slot']
    slot=int.from_bytes(keccak(words(position,lab.asset.address)),'big')
    pool=lab.pool.address if kind==1 else ZERO
    boa.env.evm.set_storage(lab.s.address,slot,int(pool,16))
    assert lab.s.feedConfig(lab.asset).pool==pool
    advance_timelock_blocks(2)
    before=state(lab.s,lab.asset)
    with boa.reverts(NO_PENDING[kind]):
        getattr(lab.s,CONFIRM[kind])(lab.asset,sender=lab.g.gov)
    assert lab.s._computation.get_log_entries()==()
    assert state(lab.s,lab.asset)==before
