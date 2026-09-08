import boa
import pytest
from .helpers import state
from conf_utils import advance_timelock_blocks,filter_logs

from .graph import SOURCE,source,params,admit,ZERO,ETH
from .raw import Pool,Raw,word,words
from .gas_tools import calls,walk

CONFIRM={1:'confirmNewPriceFeed',2:'confirmPriceFeedUpdate',3:'confirmDisablePriceFeed'}
CANCEL={1:'cancelNewPendingPriceFeed',2:'cancelPriceFeedUpdate',3:'cancelDisablePriceFeed'}


def start(lab,kind):
    if kind!=1:admit(lab.g,lab.s,lab.asset,params(lab.pool))
    if kind==1:lab.s.addNewPriceFeed(lab.asset,params(lab.pool),sender=lab.g.gov)
    elif kind==2:lab.s.updatePriceFeed(lab.asset,params(lab.pool,age=3601,quote_age=300),sender=lab.g.gov)
    else:lab.s.disablePriceFeed(lab.asset,sender=lab.g.gov)


def test_constructor_empty_state_and_nonzero_delay(lab):
    s=lab.s
    assert s.actionTimeLock()==2 and s.expiration()==100
    assert not s.isPaused()
    assert s.getPricedAssets()==[]
    assert s.getBoundAssetDecimals(lab.asset)==(False,0)
    assert s.getPriceAndHasFeed(lab.asset)==(0,False)
    assert s.getFeedConfig(lab.asset).params.pool==ZERO
    assert s.getPendingFeed(lab.asset).actionId==0
    assert s.factory()==lab.factory.address and s.weth()==lab.weth.address
    assert s.ethUsdFeed()==lab.anchor.address and s.anchorDecimals()==8
    with boa.reverts('already set'):s.setActionTimeLockAfterSetup(sender=lab.g.gov)
    with boa.reverts('already set'):s.setActionTimeLockAfterSetup(3,sender=lab.g.gov)
    assert lab.g.desk.getRegId(s)==0


@pytest.mark.parametrize('position', [0,4,5,6])
@pytest.mark.parametrize('bad',['zero','eoa'])
def test_constructor_dependency_identities(lab,position,bad):
    args=[lab.g.hq,lab.g.local,2,100,lab.factory,lab.weth,lab.anchor]
    args[position]=ZERO if bad=='zero' else boa.env.generate_address()
    with boa.reverts('invalid dependencies'):boa.load(SOURCE,*args)


@pytest.mark.parametrize('which,value',[('weth',0),('weth',17),('weth',19),('anchor',19),('anchor',255)])
def test_constructor_dependency_decimals(lab,which,value):
    getattr(lab,which).setDecimals(value)
    with boa.reverts('invalid dependencies'):source(lab.g,lab.factory,lab.weth,lab.anchor)


@pytest.mark.parametrize('minimum,maximum',[(0,100),(100,100),(101,100),(2,2**256-1)])
def test_constructor_retains_module_validation(lab,minimum,maximum):
    with boa.reverts('invalid time lock boundaries'):
        boa.load(SOURCE,lab.g.hq,lab.g.local,minimum,maximum,lab.factory,lab.weth,lab.anchor)


@pytest.mark.parametrize('kind',[1,2,3])
@pytest.mark.parametrize('boundary',[-1,0,99,100,101])
def test_confirmation_interval_and_atomicity(lab,kind,boundary):
    s,a,g=lab.s,lab.asset,lab.g
    start(lab,kind)
    p=s.getPendingFeed(a);action=s.pendingActions(p.actionId)
    assert action.confirmBlock==boa.env.evm.patch.block_number+2
    assert action.expiration==action.confirmBlock+100
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
        event=filter_logs(s,'UniV3FeedConfirmed')[0]
        assert (event.asset,event.actionId,event.kind)==(a.address,p.actionId,kind)
        assert (event.confirmationBlock,event.expirationBlock)==(action.confirmBlock,action.expiration)
        assert event.pool==p.config.params.pool
        assert s.getPendingFeed(a).actionId==0 and not s.hasPendingAction(p.actionId)
        assert s.hasPriceFeed(a)==(kind!=3)
        assert s.getBoundAssetDecimals(a)==(True,18)
        with boa.reverts('no pending feed action'):getattr(s,CONFIRM[kind])(a,sender=g.gov)


@pytest.mark.parametrize('kind',[1,2,3])
def test_pending_operation_collision_wrong_selectors_and_expired_cancel(lab,kind):
    s,a,g=lab.s,lab.asset,lab.g
    start(lab,kind)
    before=state(s,a)
    for other in (1,2,3):
        if other!=kind:
            for method in (CONFIRM[other],CANCEL[other]):
                with boa.reverts('wrong feed operation'):getattr(s,method)(a,sender=g.gov)
                assert state(s,a)==before
    # The active-state predicate precedes pending collision for ADD/UPDATE.
    initiate=(lambda:s.addNewPriceFeed(a,params(lab.pool),sender=g.gov)) if kind==1 else (lambda:s.updatePriceFeed(a,params(lab.pool,age=3602),sender=g.gov))
    for expired in (False,True):
        if expired:advance_timelock_blocks(102)
        with boa.reverts('pending feed action'):initiate()
        assert state(s,a)==before
    Raw({},address=lab.pool.address);Raw({},address=lab.anchor.address);Raw({},address=g.desk.address)
    assert getattr(s,CANCEL[kind])(a,sender=g.gov)
    event=filter_logs(s,'UniV3FeedCancelled')[0]
    assert (event.actionId,event.kind)==(before[1].actionId,kind)
    assert s.getPendingFeed(a).actionId==0
    assert s.getFeedConfig(a)==before[0]


@pytest.mark.parametrize('kind',[1,2,3])
def test_pause_and_permissions_for_all_feed_selectors(lab,kind):
    s,a,g=lab.s,lab.asset,lab.g
    start(lab,kind)
    outsider=boa.env.generate_address()
    mutations=[lambda sender:s.addNewPriceFeed(a,params(lab.pool),sender=sender),lambda sender:s.updatePriceFeed(a,params(lab.pool),sender=sender),lambda sender:s.disablePriceFeed(a,sender=sender),lambda sender:getattr(s,CONFIRM[kind])(a,sender=sender),lambda sender:getattr(s,CANCEL[kind])(a,sender=sender)]
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


@pytest.mark.parametrize('field,value',[(1,1799),(1,14401),(2,0),(3,0),(4,0),(4,86401),(5,1),(5,299),(5,604801)])
def test_numeric_admission_domains(lab,field,value):
    p=list(params(lab.pool));p[field]=value
    before=state(lab.s,lab.asset)
    with boa.reverts('invalid feed'):lab.s.addNewPriceFeed(lab.asset,tuple(p),sender=lab.g.gov)
    assert state(lab.s,lab.asset)==before


@pytest.mark.parametrize('window,age,quote_age',[(1800,1,0),(14400,86400,604800),(3600,3600,300)])
def test_inclusive_admission_domains(lab,window,age,quote_age):
    # Synthetic raw observations match the chosen lookback; this tests domains.
    lab.pool.set_history(window=window)
    assert admit(lab.g,lab.s,lab.asset,params(lab.pool,window=window,age=age,quote_age=quote_age))==10**18


@pytest.mark.parametrize('asset_kind',['zero','native','weth'])
def test_forbidden_assets(lab,asset_kind):
    a={'zero':ZERO,'native':ETH,'weth':lab.weth.address}[asset_kind]
    with boa.reverts('invalid asset'):lab.s.addNewPriceFeed(a,params(lab.pool),sender=lab.g.gov)


@pytest.mark.parametrize('dependency', ['pool','factory','token0','token1','fee','asset_decimals','anchor_decimals'])
def test_admission_metadata_identity_and_revalidation(lab,dependency):
    lab.s.addNewPriceFeed(lab.asset,params(lab.pool),sender=lab.g.gov)
    before=state(lab.s,lab.asset)
    if dependency=='pool':boa.env.set_code(lab.pool.address,b'')
    elif dependency=='factory':lab.pool.set('factory()',word(boa.env.generate_address()))
    elif dependency in ('token0','token1'):lab.pool.set(dependency+'()',word(boa.env.generate_address()))
    elif dependency=='fee':lab.pool.set('fee()',word(2**24))
    elif dependency=='asset_decimals':lab.asset.setDecimals(6)
    else:lab.anchor.setDecimals(9)
    advance_timelock_blocks(2)
    with boa.reverts('feed metadata changed'):lab.s.confirmNewPriceFeed(lab.asset,sender=lab.g.gov)
    assert state(lab.s,lab.asset)==before
    lab.s.cancelNewPendingPriceFeed(lab.asset,sender=lab.g.gov)
    if dependency!='asset_decimals':
        with boa.reverts('invalid feed'):lab.s.addNewPriceFeed(lab.asset,params(lab.pool),sender=lab.g.gov)


def test_pending_update_is_full_tuple_and_zero_restores_inheritance(active):
    l=active
    with boa.reverts('no change'):l.s.updatePriceFeed(l.asset,params(l.pool),sender=l.g.gov)
    p=params(l.pool,window=3600,current=2,harmonic=3,age=4000,quote_age=300)
    l.s.updatePriceFeed(l.asset,p,sender=l.g.gov)
    assert tuple(l.s.getFeedConfig(l.asset).params)==params(l.pool)
    advance_timelock_blocks(2)
    assert l.s.confirmPriceFeedUpdate(l.asset,sender=l.g.gov)
    assert tuple(l.s.getFeedConfig(l.asset).params)==p
    l.s.updatePriceFeed(l.asset,params(l.pool),sender=l.g.gov)
    advance_timelock_blocks(2)
    assert l.s.confirmPriceFeedUpdate(l.asset,sender=l.g.gov)
    assert tuple(l.s.getFeedConfig(l.asset).params)==params(l.pool)


@pytest.mark.parametrize('decimals',[0,18])
@pytest.mark.parametrize('reject',[False,True])
def test_first_add_callback_staging_and_complete_rollback(lab,decimals,reject):
    lab.asset.setDecimals(decimals)
    observer=boa.load('tests/priceSources/uniswap_v3/StagingAnchor.vy')
    s=source(lab.g,lab.factory,lab.weth,observer)
    observer.watch(s,lab.asset,0,reject)
    assert s.addNewPriceFeed(lab.asset,params(lab.pool),sender=lab.g.gov)
    proposal_event=filter_logs(s,'UniV3FeedProposed')[0]
    assert proposal_event.kind==1 and proposal_event.assetDecimals==decimals
    before=state(s,lab.asset)
    advance_timelock_blocks(2)
    if reject:
        with boa.reverts('price source not executable'):s.confirmNewPriceFeed(lab.asset,sender=lab.g.gov)
        assert s._computation.get_log_entries()==()
        assert state(s,lab.asset)==before
        assert s.getBoundAssetDecimals(lab.asset)==(False,0)
    else:
        assert s.confirmNewPriceFeed(lab.asset,sender=lab.g.gov)
        trace=s._computation
        assert s.getBoundAssetDecimals(lab.asset)==(True,decimals)
        assert s.getPricedAssets()==[lab.asset.address]
        assert s.getPrice(lab.asset)==10**decimals
        # The unchanged desk really made the price callback under the hard cap.
        desk_calls=calls(trace,lab.g.desk)
        qualification=[c for c in desk_calls if bytes(c.msg.data[:4])==bytes(lab.g.desk.qualifyCallerPriceSource.prepare_calldata(lab.asset)[:4])]
        assert len(qualification)==1 and qualification[0].output==words(10**decimals,1)
        price_children=[c for c in qualification[0].children if c.msg.code_address==bytes.fromhex(s.address[2:])]
        assert len(price_children)==1 and price_children[0].msg.gas==250000
    assert lab.g.desk.getRegId(s)==0


@pytest.mark.parametrize('fault',['round','scale','desk','callback'])
def test_failed_update_preserves_active_pending_binding_enumeration_and_logs(lab,fault):
    s=lab.s
    if fault=='callback':
        observer=boa.load('tests/priceSources/uniswap_v3/StagingAnchor.vy')
        s=source(lab.g,lab.factory,lab.weth,observer)
        observer.watch(s,lab.asset,0,False)
    admit(lab.g,s,lab.asset,params(lab.pool))
    if fault=='callback':observer.watch(s,lab.asset,1,True)
    s.updatePriceFeed(lab.asset,params(lab.pool,age=4000),sender=lab.g.gov)
    before=state(s,lab.asset)
    advance_timelock_blocks(2)
    if fault=='round':lab.anchor.setMockData(0)
    elif fault=='scale':
        lab.asset.setDecimals(6);lab.g.desk.syncTokenScale(lab.asset,sender=lab.g.gov);lab.asset.setDecimals(18)
    elif fault=='desk':boa.env.set_code(lab.g.desk.address,b'')
    reason={'round':'invalid feed','scale':'token scale mismatch','desk':'invalid price desk','callback':'price source not executable'}[fault]
    with boa.reverts(reason):s.confirmPriceFeedUpdate(lab.asset,sender=lab.g.gov)
    assert s._computation.get_log_entries()==()
    assert state(s,lab.asset)==before


def test_disable_during_market_outage_retains_permanent_binding(active):
    l=active
    Raw({},address=l.pool.address);Raw({},address=l.anchor.address);Raw({},address=l.g.desk.address)
    l.s.disablePriceFeed(l.asset,sender=l.g.gov)
    advance_timelock_blocks(2)
    assert l.s.confirmDisablePriceFeed(l.asset,sender=l.g.gov)
    assert l.s.getPriceAndHasFeed(l.asset)==(0,False)
    assert l.s.getBoundAssetDecimals(l.asset)==(True,18)
    assert l.s.getPricedAssets()==[]


def test_capacity_competing_pending_and_first_middle_last_removal(lab):
    tokens=[]
    for i in range(51):
        token=boa.load('contracts/mock/MockChainlinkFeed.vy',10**18);token.setDecimals(18)
        pool=Pool(token,lab.weth,lab.factory)
        lab.factory.setPool(token,lab.weth,10000,pool.address)
        tokens.append((token,pool))
        if i<49:admit(lab.g,lab.s,token,params(pool),register_source=False)
    for token,pool in tokens[49:]:lab.s.addNewPriceFeed(token,params(pool),sender=lab.g.gov)
    advance_timelock_blocks(2)
    assert lab.s.confirmNewPriceFeed(tokens[49][0],sender=lab.g.gov)
    before=state(lab.s,tokens[50][0])
    with boa.reverts('too many assets'):lab.s.confirmNewPriceFeed(tokens[50][0],sender=lab.g.gov)
    assert state(lab.s,tokens[50][0])==before
    assert len(lab.s.getPricedAssets())==50 and lab.s.numAssets()==51
    lab.s.cancelNewPendingPriceFeed(tokens[50][0],sender=lab.g.gov)
    with boa.reverts('too many assets'):lab.s.addNewPriceFeed(tokens[50][0],params(tokens[50][1]),sender=lab.g.gov)
    # Capacity is deliberately checked before numeric/metadata validation.
    before=state(lab.s,tokens[50][0])
    with boa.reverts('too many assets'):
        lab.s.addNewPriceFeed(tokens[50][0],params(ZERO,window=0),sender=lab.g.gov)
    assert lab.s._computation.get_log_entries()==()
    assert state(lab.s,tokens[50][0])==before
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
    reason='feed already exists' if operation=='add' else 'no active feed'
    with boa.reverts(reason):
        if operation=='add':s.addNewPriceFeed(a,params(lab.pool),sender=g.gov)
        elif operation=='update':s.updatePriceFeed(a,params(lab.pool),sender=g.gov)
        else:s.disablePriceFeed(a,sender=g.gov)
    assert s._computation.get_log_entries()==()
    assert state(s,a)==before


@pytest.mark.parametrize('kind',[1,2])
def test_bound_decimals_drift_after_proposal_reaches_confirmation_guard(active,kind):
    l=active
    if kind==1:
        l.s.disablePriceFeed(l.asset,sender=l.g.gov)
        advance_timelock_blocks(2)
        l.s.confirmDisablePriceFeed(l.asset,sender=l.g.gov)
        l.s.addNewPriceFeed(l.asset,params(l.pool),sender=l.g.gov)
    else:
        l.s.updatePriceFeed(l.asset,params(l.pool,age=4000),sender=l.g.gov)
    before=state(l.s,l.asset)
    l.asset.setDecimals(6)
    advance_timelock_blocks(2)
    with boa.reverts('asset decimals changed'):
        getattr(l.s,CONFIRM[kind])(l.asset,sender=l.g.gov)
    assert l.s._computation.get_log_entries()==()
    assert state(l.s,l.asset)==before
    l.asset.setDecimals(18)
    assert getattr(l.s,CONFIRM[kind])(l.asset,sender=l.g.gov)


def test_pending_window_update_keeps_old_price_until_confirmation(lab):
    from .compiled import deploy
    ref=deploy('v3','Reference')
    # Fixed cumulative delta gives mean tick 100 at 1800s and 50 at 3600s.
    lab.pool.set_history(tick=100)
    old=ref.quote(100,10**18,lab.asset.address,lab.weth.address)
    new=ref.quote(50,10**18,lab.asset.address,lab.weth.address)
    assert old!=new and admit(lab.g,lab.s,lab.asset,params(lab.pool))==old
    lab.s.updatePriceFeed(lab.asset,params(lab.pool,window=3600),sender=lab.g.gov)
    assert lab.s.getPendingFeed(lab.asset).config.params.twapWindowSeconds==3600
    assert lab.s.getFeedConfig(lab.asset).params.twapWindowSeconds==1800
    assert lab.s.getPrice(lab.asset)==lab.g.desk.getPrice(lab.asset,True)==old
    advance_timelock_blocks(2)
    assert lab.s.confirmPriceFeedUpdate(lab.asset,sender=lab.g.gov)
    assert lab.s.getFeedConfig(lab.asset).params.twapWindowSeconds==3600
    assert lab.s.getPrice(lab.asset)==lab.g.desk.getPrice(lab.asset,True)==new


@pytest.mark.parametrize('decimals',[0,18])
def test_constructor_accepts_anchor_decimal_endpoints_and_normalizes(lab,decimals):
    lab.anchor.setDecimals(decimals)
    lab.anchor.setMockData(3*10**decimals)
    s=source(lab.g,lab.factory,lab.weth,lab.anchor)
    assert s.anchorDecimals()==decimals
    assert admit(lab.g,s,lab.asset,params(lab.pool))==3*10**18
    assert lab.g.desk.getPrice(lab.asset,True)==3*10**18


def test_matching_nonzero_scale_accepts_first_add_and_update(lab):
    lab.g.desk.syncTokenScale(lab.asset,sender=lab.g.gov)
    assert lab.g.desk.tokenScale(lab.asset)==10**18
    assert admit(lab.g,lab.s,lab.asset,params(lab.pool))==10**18
    lab.s.updatePriceFeed(lab.asset,params(lab.pool,age=4000),sender=lab.g.gov)
    advance_timelock_blocks(2)
    assert lab.s.confirmPriceFeedUpdate(lab.asset,sender=lab.g.gov)
    assert lab.g.desk.getUsdValue(lab.asset,2*10**18,True)==2*10**18


@pytest.mark.parametrize('kind',[1,2,3])
def test_defensive_confirmation_active_state_guards(lab,kind):
    from eth_utils import keccak
    start(lab,kind)
    # Synthetic storage fault: public lifecycle/pending collision rules prevent
    # these states. Exercise the confirm-time defense independently of proposal.
    position=lab.s.compiler_data.storage_layout['storage_layout']['configs']['slot']
    slot=int.from_bytes(keccak(words(position,lab.asset.address)),'big')
    pool=lab.pool.address if kind==1 else ZERO
    boa.env.evm.set_storage(lab.s.address,slot,int(pool,16))
    assert lab.s.getFeedConfig(lab.asset).params.pool==pool
    advance_timelock_blocks(2)
    before=state(lab.s,lab.asset)
    with boa.reverts('feed already exists' if kind==1 else 'no active feed'):
        getattr(lab.s,CONFIRM[kind])(lab.asset,sender=lab.g.gov)
    assert lab.s._computation.get_log_entries()==()
    assert state(lab.s,lab.asset)==before
