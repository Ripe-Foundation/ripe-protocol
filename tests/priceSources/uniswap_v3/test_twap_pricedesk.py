import boa
import pytest
from conf_utils import advance_timelock_blocks

from .graph import admit,params,register,temporary_desk,source,make_graph,weth_price_source,quote_price_source,ZERO
from .raw import Pool,words,word,Raw
from .helpers import unavailable,state

WITNESS='tests/priceSources/uniswap_v3/StagingWethSource.vy'


@pytest.mark.parametrize('decimals',[0,6,9,18])
def test_whole_token_price_and_both_amount_conversions(lab,decimals):
    lab.asset.setDecimals(decimals)
    expected=10**decimals  # tick 0: raw asset unit = raw WETH unit; $1 ETH anchor
    assert admit(lab.g,lab.s,lab.asset,params(lab.pool))==expected
    assert lab.s.feedConfig(lab.asset).assetDecimals==decimals
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


@pytest.mark.parametrize('quote_decimals',[6,18])
def test_any_desk_priced_quote_asset(lab,math,quote_decimals):
    """A stablecoin-quoted pool: the pool decides the quote asset; the desk prices it."""
    usdc=boa.load('contracts/mock/MockChainlinkFeed.vy',10**18);usdc.setDecimals(quote_decimals)
    pool=Pool(lab.asset,usdc,lab.factory);lab.factory.setPool(lab.asset,usdc,10000,pool.address)
    asset_is_token0=int(lab.asset.address,16)<int(usdc.address,16)
    # 1 asset = 2 quote tokens: raw ratio 2*10**quote_decimals / 10**18, as a tick
    import math as pymath
    ratio=2*10**quote_decimals/10**18
    tick=round(pymath.log(ratio if asset_is_token0 else 1/ratio)/pymath.log(1.0001))
    pool.set_history(tick=tick)
    g=make_graph()
    s=source(g,lab.factory)
    # the quote asset must be priced by the desk before the pool can be admitted
    assert not s.isValidNewFeed(lab.asset,*params(pool))
    with boa.reverts('invalid feed'):s.addNewPriceFeed(lab.asset,*params(pool),sender=g.gov)
    quote_price_source(g,usdc,10**18)  # $1
    expected=math.quote(tick,10**36,asset_is_token0)//10**quote_decimals
    assert 199*10**16<expected<201*10**16
    assert admit(g,s,lab.asset,params(pool))==expected
    config=s.feedConfig(lab.asset)
    assert (config.quoteAsset,config.quoteDecimals,config.assetIsToken0)==(usdc.address,quote_decimals,asset_is_token0)
    g.desk.syncTokenScale(lab.asset,sender=g.gov)
    assert g.desk.getPrice(lab.asset,True)==expected
    assert g.desk.getUsdValue(lab.asset,10**18,True)==expected
    assert s.getPoolLiquidity(pool.address)==(10**20,config.baseLiquidity)


def test_zero_decimal_less_than_one_wei_quote_remains_unavailable(lab):
    """At tick -1, one raw token0 unit quotes less than one wei WETH: floor is 0."""
    lab.asset.setDecimals(0)
    lab.pool.set_history(tick=-1)
    with boa.reverts('invalid feed'):lab.s.addNewPriceFeed(lab.asset,*params(lab.pool),sender=lab.g.gov)
    assert lab.s.pendingUpdates(lab.asset).actionId==0
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
    g=make_graph()
    # a registered source already prices the asset (only the asset: WETH stays with the witness)
    healthy=boa.load('contracts/mock/MockPriceSource.vy',g.hq,1,100);healthy.setPrice(lab.asset,3*10**18)
    register(g.desk,healthy,g.gov)
    witness=boa.load(WITNESS,lab.weth)
    register(g.desk,witness,g.gov)
    s=source(g,lab.factory)
    witness.watch(s,lab.asset,0,True)
    assert s.addNewPriceFeed(lab.asset,*params(lab.pool),sender=g.gov)
    pending=s.pendingUpdates(lab.asset)
    advance_timelock_blocks(2)
    assert g.desk.getPrice(lab.asset,True)==3*10**18
    with boa.reverts('price source not executable'):s.confirmNewPriceFeed(lab.asset,sender=g.gov)
    assert s.pendingUpdates(lab.asset)==pending
    assert g.desk.getRegId(s)==0


def test_snapshot_and_coverage_are_storage_only_even_during_outage(active):
    l=active
    Raw({},address=l.pool.address);Raw({},address=l.anchor.address);Raw({},address=l.g.hq.address)
    before=l.s.feedConfig(l.asset)
    assert not l.s.addPriceSnapshot(l.asset,gas=150000)
    assert l.s._computation.children==[] and l.s._computation.get_log_entries()==()
    assert l.s.hasPriceFeed(l.asset,gas=75000)
    assert l.s._computation.children==[]
    assert l.s.feedConfig(l.asset)==before


def test_reverse_token_order_lifecycle_and_amount_conversions(lab):
    from .compiled import deploy
    a,w=lab.weth,lab.asset
    g=make_graph()
    weth_price_source(g,w,lab.anchor)
    s=source(g,lab.factory)
    lab.pool.set_history(tick=37)
    expected=deploy('v3','Reference').quote(37,10**18,a.address,w.address)
    assert admit(g,s,a,params(lab.pool))==expected
    assert not s.feedConfig(a).assetIsToken0 and s.feedConfig(a).quoteAsset==w.address
    g.desk.syncTokenScale(a,sender=g.gov)
    assert g.desk.getUsdValue(a,3*10**18,True)==3*expected
    assert g.desk.getAssetAmount(a,3*expected,True)==3*10**18
    s.disablePriceFeed(a,sender=g.gov);advance_timelock_blocks(2)
    assert s.confirmDisablePriceFeed(a,sender=g.gov)
    assert not s.hasPriceFeed(a) and s.getPricedAssets()==[]
    assert admit(g,s,a,params(lab.pool))==expected
    assert s.getPricedAssets()==[a.address]
    assert g.desk.getUsdValue(a,3*10**18,True)==3*expected


def test_current_desk_rotation_routes_the_quote_leg_through_the_new_desk(active):
    l=active;g=l.g;old=g.desk
    with temporary_desk(g):
        # the new desk has no sources yet: no WETH price, so the feed is unavailable
        assert l.s.getPriceAndHasFeed(l.asset)==(0,True)
        assert old.getPrice(l.asset)==0
        register(g.desk,g.chainlink,g.gov)
        register(g.desk,l.s,g.gov)
        g.desk.syncTokenScale(l.asset,sender=g.local)
        assert l.s.getPriceAndHasFeed(l.asset)==(10**18,True)
        assert g.desk.getPrice(l.asset,True)==10**18
        assert g.desk.getUsdValue(l.asset,10**18,True)==10**18
        # Chainlink authenticates the forwarding desk; this source now rejects
        # any non-canonical supplied desk itself, including with stale time zero.
        assert l.s.getPrice(l.asset,0,old.address)==0


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
    old=lab.g.desk
    with pytest.raises(AssertionError,match='injected failure'):
        with temporary_desk(lab.g) as replacement:
            assert lab.g.desk is replacement
            assert lab.g.hq.getAddr(7)==replacement.address
            raise AssertionError('injected failure')
    assert lab.g.desk is old and lab.g.hq.getAddr(7)==old.address
