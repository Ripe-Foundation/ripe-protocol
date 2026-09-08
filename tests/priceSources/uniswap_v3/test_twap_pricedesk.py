import boa
from contextlib import nullcontext
import pytest
from conf_utils import advance_timelock_blocks

from .graph import admit,params,register,temporary_desk,source,ZERO
from .raw import words,word,Raw
from .helpers import unavailable,state


@pytest.mark.parametrize('decimals',[0,6,9,18])
def test_whole_token_price_and_both_amount_conversions(lab,decimals):
    lab.asset.setDecimals(decimals)
    expected=10**decimals  # tick 0: raw asset unit = raw WETH unit; $1 ETH anchor
    assert admit(lab.g,lab.s,lab.asset,params(lab.pool))==expected
    assert lab.s.getBoundAssetDecimals(lab.asset)==(True,decimals)
    assert lab.g.desk.tokenScale(lab.asset)==0
    assert lab.g.desk.getPrice(lab.asset,True)==expected
    for method in ('getUsdValue','getAssetAmount'):
        fn=getattr(lab.g.desk,method)
        assert fn(lab.asset,0,True)==0
        assert fn(lab.asset,1)==0
        with boa.reverts('missing token scale'):fn(lab.asset,1,True)
    outsider=boa.env.generate_address()
    lab.g.desk.syncTokenScale(lab.asset,sender=outsider)
    assert lab.g.desk.tokenScale(lab.asset)==10**decimals
    assert lab.g.desk.getUsdValue(lab.asset,3*10**decimals,True)==3*expected
    assert lab.g.desk.getAssetAmount(lab.asset,3*expected,True)==3*10**decimals


@pytest.mark.parametrize('rotate',[False,True])
@pytest.mark.parametrize('repair',['governor','switchboard'])
def test_permissionless_scale_poisoning_restoration_and_explicit_recovery(lab,rotate,repair):
    g,s,a=lab.g,lab.s,lab.asset
    admit(g,s,a,params(lab.pool))
    old_desk=g.desk
    with temporary_desk(g) if rotate else nullcontext():
        if rotate:register(g.desk,s,g.gov)
        assert g.desk.tokenScale(a)==0
        outsider=boa.env.generate_address()
        a.setDecimals(6)
        assert s.getPriceAndHasFeed(a)==(0,True)
        assert g.desk.hasPriceFeed(a)
        g.desk.syncTokenScale(a,sender=outsider)
        assert g.desk.tokenScale(a)==10**6
        a.setDecimals(18)
        unavailable(lab)
        assert s.getPriceAndHasFeed(a,0,old_desk.address,sender=old_desk.address)==(0,True)
        for method,amount in [('getUsdValue',10**18),('getAssetAmount',10**18)]:
            fn=getattr(g.desk,method)
            assert fn(a,amount)==0
            with boa.reverts('has price config, no price'):fn(a,amount,True)
        # ensure_token_scale and Golf's zero-only auto-sync cannot repair this state.
        with boa.reverts('already set'):g.desk.syncTokenScale(a,sender=outsider)
        caller=g.local if repair=='governor' else g.actor.address
        g.desk.syncTokenScale(a,sender=caller)
        assert g.desk.tokenScale(a)==10**18
        assert s.getPrice(a)==10**18
        assert g.desk.getUsdValue(a,10**18,True)==10**18  # never erroneous 10**30
        assert g.desk.getAssetAmount(a,10**18,True)==10**18
        if rotate:
            assert s.getPriceAndHasFeed(a,86400,old_desk.address,sender=old_desk.address)==(0,True)
            assert s.getPriceAndHasFeed(a,86400,g.desk.address,sender=g.desk.address)==(10**18,True)
            assert s.getPrice(a,0,old_desk.address,sender=old_desk.address)==10**18



def test_current_desk_rotation_checks_existing_wrong_scale(active):
    l=active;g=l.g;old=g.desk
    new=boa.load('contracts/registries/PriceDesk.vy',g.hq,g.local,old.ETH(),1,100)
    l.asset.setDecimals(6);new.syncTokenScale(l.asset,sender=g.local);l.asset.setDecimals(18)
    with temporary_desk(g,new):
        assert l.s.getPriceAndHasFeed(l.asset)==(0,True)
        register(new,l.s,g.gov)
        assert new.getPrice(l.asset)==0
        new.syncTokenScale(l.asset,sender=g.local)
        assert new.getUsdValue(l.asset,10**18,True)==10**18
        assert new.getAssetAmount(l.asset,10**18,True)==10**18
        assert old.getPrice(l.asset)==0



@pytest.mark.parametrize('initial',[0,6,9,18])
def test_permanent_binding_survives_disable_readd_and_restoration(lab,initial):
    lab.asset.setDecimals(initial)
    admit(lab.g,lab.s,lab.asset,params(lab.pool))
    for anchor_drift in (False,True):
        target=lab.anchor if anchor_drift else lab.asset
        old=8 if anchor_drift else initial
        target.setDecimals(old+1)
        unavailable(lab)
        target.setDecimals(old)
        assert lab.s.getPrice(lab.asset)==10**initial
    lab.asset.setDecimals((initial+6)%19)
    with boa.reverts('asset decimals changed'):lab.s.updatePriceFeed(lab.asset,params(lab.pool,age=4000),sender=lab.g.gov)
    lab.s.disablePriceFeed(lab.asset,sender=lab.g.gov);advance_timelock_blocks(2)
    assert lab.s.confirmDisablePriceFeed(lab.asset,sender=lab.g.gov)
    assert lab.s.getBoundAssetDecimals(lab.asset)==(True,initial)
    assert lab.s.getFeedConfig(lab.asset).params.pool==ZERO
    with boa.reverts('asset decimals changed'):lab.s.addNewPriceFeed(lab.asset,params(lab.pool),sender=lab.g.gov)
    lab.asset.setDecimals(initial)
    assert admit(lab.g,lab.s,lab.asset,params(lab.pool))==10**initial


def test_zero_decimal_less_than_one_wei_quote_remains_unavailable(lab):
    """At tick -1, one raw token0 unit quotes less than one wei WETH: floor is 0."""
    lab.asset.setDecimals(0)
    lab.pool.set_history(tick=-1)
    with boa.reverts('invalid feed'):lab.s.addNewPriceFeed(lab.asset,params(lab.pool),sender=lab.g.gov)
    assert lab.s.getBoundAssetDecimals(lab.asset)==(False,0)
    assert lab.s.getPendingFeed(lab.asset).actionId==0
    lab.pool.set_history(tick=0)
    assert admit(lab.g,lab.s,lab.asset,params(lab.pool))==1
    lab.g.desk.syncTokenScale(lab.asset,sender=lab.g.gov)
    lab.pool.set_history(tick=-1)
    unavailable(lab)
    assert lab.g.desk.getUsdValue(lab.asset,1)==0
    with boa.reverts('has price config, no price'):lab.g.desk.getAssetAmount(lab.asset,1,True)


def test_existing_desk_dust_and_checked_intermediate_limits(active):
    """Source mulDiv does not change PriceDesk's checked price*amount intermediates."""
    l=active
    l.g.desk.syncTokenScale(l.asset,sender=l.g.gov)
    l.anchor.setMockData(1)
    assert l.s.getPrice(l.asset)==10**10
    assert l.g.desk.getUsdValue(l.asset,1,True)==1
    assert l.g.desk.getAssetAmount(l.asset,1,True)==10**8
    for method in ('getUsdValue','getAssetAmount'):
        with boa.reverts():getattr(l.g.desk,method)(l.asset,2**256-1,True)


@pytest.mark.parametrize('status',['no_feed','unavailable','revert','malformed'])
def test_actual_desk_failure_and_fallback_matrix(lab,status):
    g,s,a=lab.g,lab.s,lab.asset
    register(g.desk,s,g.gov)
    if status!='no_feed':
        admit(g,s,a,params(lab.pool))
        if status=='unavailable':lab.anchor.setMockData(0)
        elif status=='revert':Raw({},address=s.address)
        else:Raw({'getPriceAndHasFeed(address,uint256,address)':words(10**18,0)},address=s.address)
    assert g.desk.getPrice(a)==0
    if status=='no_feed':assert g.desk.getPrice(a,True)==0
    else:
        with boa.reverts('has price config, no price'):g.desk.getPrice(a,True)
    healthy=boa.load('contracts/mock/MockRawPriceSource.vy');healthy.configure(3*10**18,True)
    register(g.desk,healthy,g.gov)
    assert g.desk.getPrice(a,True)==3*10**18


def test_registered_fallback_cannot_rescue_unregistered_candidate_callback(lab):
    healthy=boa.load('contracts/mock/MockRawPriceSource.vy');healthy.configure(3*10**18,True)
    register(lab.g.desk,healthy,lab.g.gov)
    observer=boa.load('tests/priceSources/uniswap_v3/StagingAnchor.vy')
    s=source(lab.g,lab.factory,lab.weth,observer)
    observer.watch(s,lab.asset,0,True)
    assert s.addNewPriceFeed(lab.asset,params(lab.pool),sender=lab.g.gov)
    pending=s.getPendingFeed(lab.asset)
    advance_timelock_blocks(2)
    assert lab.g.desk.getPrice(lab.asset,True)==3*10**18
    with boa.reverts('price source not executable'):s.confirmNewPriceFeed(lab.asset,sender=lab.g.gov)
    assert s.getPendingFeed(lab.asset)==pending
    assert s.getBoundAssetDecimals(lab.asset)==(False,0)
    assert lab.g.desk.getRegId(s)==0


def test_snapshot_and_coverage_are_storage_only_even_during_outage(active):
    l=active
    Raw({},address=l.pool.address);Raw({},address=l.anchor.address);Raw({},address=l.g.hq.address)
    before=l.s.getFeedConfig(l.asset)
    assert not l.s.addPriceSnapshot(l.asset,gas=150000)
    assert l.s._computation.children==[] and l.s._computation.get_log_entries()==()
    assert l.s.hasPriceFeed(l.asset,gas=75000)
    assert l.s._computation.children==[]
    assert l.s.getFeedConfig(l.asset)==before


def test_reverse_order_lifecycle_poisoning_and_amount_recovery(lab):
    from .compiled import deploy
    a,w=lab.weth,lab.asset
    s=source(lab.g,lab.factory,w,lab.anchor)
    lab.pool.set_history(tick=37)
    expected=deploy('v3','Reference').quote(37,10**18,a.address,w.address)
    assert admit(lab.g,s,a,params(lab.pool))==expected
    assert not s.getFeedConfig(a).assetIsToken0
    a.setDecimals(6)
    lab.g.desk.syncTokenScale(a,sender=boa.env.generate_address())
    a.setDecimals(18)
    from types import SimpleNamespace
    unavailable(SimpleNamespace(s=s,asset=a,g=lab.g))
    for method in ('getUsdValue','getAssetAmount'):
        assert getattr(lab.g.desk,method)(a,10**18)==0
        with boa.reverts('has price config, no price'):
            getattr(lab.g.desk,method)(a,10**18,True)
    lab.g.desk.syncTokenScale(a,sender=lab.g.gov)
    assert lab.g.desk.getUsdValue(a,3*10**18,True)==3*expected
    assert lab.g.desk.getAssetAmount(a,3*expected,True)==3*10**18
    s.disablePriceFeed(a,sender=lab.g.gov);advance_timelock_blocks(2)
    assert s.confirmDisablePriceFeed(a,sender=lab.g.gov)
    assert s.getBoundAssetDecimals(a)==(True,18) and not s.hasPriceFeed(a)
    a.setDecimals(6)
    with boa.reverts('asset decimals changed'):s.addNewPriceFeed(a,params(lab.pool),sender=lab.g.gov)
    a.setDecimals(18)
    assert admit(lab.g,s,a,params(lab.pool))==expected
    assert s.getPricedAssets()==[a.address]
    assert lab.g.desk.getUsdValue(a,3*10**18,True)==3*expected
    assert lab.g.desk.getAssetAmount(a,3*expected,True)==3*10**18


def test_actual_desk_coverage_and_snapshot_forward_fixed_stipends(active):
    from .gas_tools import calls,cold
    from .raw import selector
    l=active
    before=state(l.s,l.asset)
    Raw({},address=l.pool.address);Raw({},address=l.anchor.address)
    cold(l.g.desk)
    assert l.g.desk.hasPriceFeed(l.asset)
    coverage=calls(l.g.desk._computation,l.s)
    assert len(coverage)==1
    assert coverage[0].msg.gas==75000 and coverage[0].output==word(1)
    assert coverage[0].children==[] and not coverage[0].is_error
    cold(l.g.desk)
    assert not l.g.desk.addPriceSnapshot(l.asset,sender=l.g.mc.address)
    trace=l.g.desk._computation
    children=calls(trace,l.s)
    assert [(bytes(c.msg.data[:4]),c.msg.gas,c.output) for c in children]==[
        (selector('hasPriceFeed(address)'),75000,word(1)),
        (selector('addPriceSnapshot(address)'),150000,word(0))]
    assert all(c.children==[] and not c.is_error for c in children)
    assert trace.get_log_entries()==() and state(l.s,l.asset)==before


def test_temporary_desk_restores_python_and_registry_on_failure(lab):
    from .graph import temporary_desk
    old=lab.g.desk
    with pytest.raises(AssertionError,match='injected failure'):
        with temporary_desk(lab.g) as replacement:
            assert lab.g.desk is replacement
            assert lab.g.hq.getAddr(7)==replacement.address
            raise AssertionError('injected failure')
    assert lab.g.desk is old and lab.g.hq.getAddr(7)==old.address
