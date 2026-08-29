from dataclasses import dataclass

import boa
import pytest

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


MAX_UINT112 = 2**112 - 1
MAX_UINT32 = 2**32 - 1


ASSET_PRICE_DESK_SOURCE = """# @version 0.4.3
prices: HashMap[address, uint256]

@external
def setPrice(_asset: address, _price: uint256):
    self.prices[_asset] = _price

@view
@external
def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256:
    return self.prices[_asset]
"""


@dataclass
class UniswapV2MonitorFixture:
    source: object
    pair: object
    ripe: object
    weth: object
    price_desk: object
    hq: object
    ripe_is_token0: bool


@dataclass
class GenericPoolFixture:
    pair: object
    asset: object
    partner: object
    asset_is_token0: bool


@pytest.fixture(scope="module")
def uniswap_v2_factories():
    return {
        "token": boa.load_partial("contracts/mock/MockUniswapV2Token.vy"),
        "pair": boa.load_partial("contracts/mock/MockUniswapV2Pair.vy"),
        "price_desk": boa.load_partial(
            "contracts/mock/MockUniswapV2QuotePriceDesk.vy"
        ),
        "hq": boa.load_partial("contracts/mock/MockUniswapV2RipeHq.vy"),
        "source": boa.load_partial(
            "contracts/priceSources/UniswapV2Prices.vy"
        ),
    }


def _set_raw_reserves(fixture, ripe_reserve, weth_reserve):
    fixture.ripe.setBalance(fixture.pair.address, ripe_reserve)
    fixture.weth.setBalance(fixture.pair.address, weth_reserve)
    fixture.pair.sync()


def _deploy_generic_pool(
    factories,
    *,
    asset_decimals=18,
    partner_decimals=18,
    asset_reserve=100 * EIGHTEEN_DECIMALS,
    partner_reserve=10 * EIGHTEEN_DECIMALS,
    asset_is_token0=True,
    timestamp=1_700_000_000,
):
    asset = factories["token"].deploy(asset_decimals)
    partner = factories["token"].deploy(partner_decimals)
    pair = factories["pair"].deploy()
    token0 = asset.address if asset_is_token0 else partner.address
    token1 = partner.address if asset_is_token0 else asset.address
    pair.configureIdentity(ZERO_ADDRESS, token0, token1)
    reserve0 = asset_reserve if asset_is_token0 else partner_reserve
    reserve1 = partner_reserve if asset_is_token0 else asset_reserve
    pair.configureState(reserve0, reserve1, timestamp, 0, 0, 1)
    return GenericPoolFixture(pair, asset, partner, asset_is_token0)


def _set_generic_pool_state(
    pool_fixture,
    asset_reserve,
    partner_reserve,
    timestamp=1_700_000_000,
):
    reserve0 = (
        asset_reserve if pool_fixture.asset_is_token0 else partner_reserve
    )
    reserve1 = (
        partner_reserve if pool_fixture.asset_is_token0 else asset_reserve
    )
    pool_fixture.pair.configureState(reserve0, reserve1, timestamp, 0, 0, 1)


def _deploy_source_with_price_desk(factories, governance, price_desk):
    default_pool = _deploy_generic_pool(factories)
    hq = factories["hq"].deploy(governance.address, price_desk.address)
    source = factories["source"].deploy(
        hq.address,
        default_pool.pair.address,
        default_pool.asset.address,
        default_pool.partner.address,
    )
    return source


@pytest.fixture
def uniswap_v2_monitor_builder(uniswap_v2_factories, governance):
    def build(
        *,
        ripe_is_token0=True,
        ripe_decimals=18,
        weth_decimals=18,
        ripe_units=100,
        weth_units=10,
        weth_usd=2_000 * EIGHTEEN_DECIMALS,
    ):
        ripe = uniswap_v2_factories["token"].deploy(ripe_decimals)
        weth = uniswap_v2_factories["token"].deploy(weth_decimals)
        pair = uniswap_v2_factories["pair"].deploy()
        token0 = ripe.address if ripe_is_token0 else weth.address
        token1 = weth.address if ripe_is_token0 else ripe.address
        pair.configureIdentity(ZERO_ADDRESS, token0, token1)

        ripe_reserve = ripe_units * 10**ripe_decimals
        weth_reserve = weth_units * 10**weth_decimals
        ripe.setBalance(pair.address, ripe_reserve)
        weth.setBalance(pair.address, weth_reserve)
        pair.mint(governance.address)

        price_desk = uniswap_v2_factories["price_desk"].deploy()
        price_desk.setPrice(weth_usd)
        hq = uniswap_v2_factories["hq"].deploy(
            governance.address,
            price_desk.address,
        )
        source = uniswap_v2_factories["source"].deploy(
            hq.address,
            pair.address,
            ripe.address,
            weth.address,
        )
        return UniswapV2MonitorFixture(
            source=source,
            pair=pair,
            ripe=ripe,
            weth=weth,
            price_desk=price_desk,
            hq=hq,
            ripe_is_token0=ripe_is_token0,
        )

    return build


@pytest.mark.parametrize("ripe_is_token0", [True, False])
def test_monitor_reports_only_the_ripe_weth_pool_state_and_spot_prices(
    uniswap_v2_monitor_builder,
    ripe_is_token0,
):
    fixture = uniswap_v2_monitor_builder(ripe_is_token0=ripe_is_token0)

    assert fixture.source.isMonitoringOnly() is True
    assert fixture.source.RIPE_HQ() == fixture.hq.address
    assert fixture.source.RIPE_WETH_POOL() == fixture.pair.address
    assert fixture.source.RIPE_TOKEN() == fixture.ripe.address
    assert fixture.source.WETH_TOKEN() == fixture.weth.address
    assert fixture.source.RIPE_IS_TOKEN0() is ripe_is_token0

    ripe_reserve = 100 * EIGHTEEN_DECIMALS
    weth_reserve = 10 * EIGHTEEN_DECIMALS
    assert fixture.source.getRipePoolState() == (
        ripe_reserve,
        weth_reserve,
        fixture.pair.pairTimestamp(),
    )
    assert fixture.source.getRipeWethMonitoringPrice() == EIGHTEEN_DECIMALS // 10
    assert fixture.source.getRipeUsdMonitoringPrice() == 200 * EIGHTEEN_DECIMALS


@pytest.mark.parametrize("asset_is_token0", [True, False])
@pytest.mark.parametrize(
    "asset_decimals,partner_decimals,asset_reserve,partner_reserve,partner_usd,expected",
    [
        (
            18,
            18,
            100 * EIGHTEEN_DECIMALS,
            10 * EIGHTEEN_DECIMALS,
            2_000 * EIGHTEEN_DECIMALS,
            200 * EIGHTEEN_DECIMALS,
        ),
        (
            6,
            18,
            100 * 10**6,
            10 * EIGHTEEN_DECIMALS,
            2_000 * EIGHTEEN_DECIMALS,
            200 * EIGHTEEN_DECIMALS,
        ),
        (
            18,
            6,
            50 * EIGHTEEN_DECIMALS,
            1_000 * 10**6,
            EIGHTEEN_DECIMALS,
            20 * EIGHTEEN_DECIMALS,
        ),
        (
            0,
            18,
            5,
            2 * EIGHTEEN_DECIMALS,
            3 * EIGHTEEN_DECIMALS,
            6 * EIGHTEEN_DECIMALS // 5,
        ),
        (
            18,
            0,
            2 * EIGHTEEN_DECIMALS,
            5,
            3 * EIGHTEEN_DECIMALS,
            15 * EIGHTEEN_DECIMALS // 2,
        ),
    ],
)
def test_generic_monitoring_price_normalizes_decimals_and_token_order(
    uniswap_v2_factories,
    uniswap_v2_monitor_builder,
    asset_is_token0,
    asset_decimals,
    partner_decimals,
    asset_reserve,
    partner_reserve,
    partner_usd,
    expected,
):
    monitor = uniswap_v2_monitor_builder(weth_usd=partner_usd)
    pool = _deploy_generic_pool(
        uniswap_v2_factories,
        asset_decimals=asset_decimals,
        partner_decimals=partner_decimals,
        asset_reserve=asset_reserve,
        partner_reserve=partner_reserve,
        asset_is_token0=asset_is_token0,
    )

    assert (
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )
        == expected
    )


def test_one_source_monitors_multiple_assets_and_prices_each_partner(
    uniswap_v2_factories,
    governance,
):
    price_desk = boa.loads(
        ASSET_PRICE_DESK_SOURCE,
        name="uniswap_asset_routed_price_desk",
    )
    source = _deploy_source_with_price_desk(
        uniswap_v2_factories,
        governance,
        price_desk,
    )
    first = _deploy_generic_pool(
        uniswap_v2_factories,
        asset_decimals=6,
        partner_decimals=18,
        asset_reserve=100 * 10**6,
        partner_reserve=10 * EIGHTEEN_DECIMALS,
    )
    second = _deploy_generic_pool(
        uniswap_v2_factories,
        asset_decimals=18,
        partner_decimals=6,
        asset_reserve=50 * EIGHTEEN_DECIMALS,
        partner_reserve=1_000 * 10**6,
        asset_is_token0=False,
    )

    price_desk.setPrice(first.asset.address, 99_999 * EIGHTEEN_DECIMALS)
    price_desk.setPrice(first.partner.address, 2_000 * EIGHTEEN_DECIMALS)
    price_desk.setPrice(second.asset.address, 88_888 * EIGHTEEN_DECIMALS)
    price_desk.setPrice(second.partner.address, EIGHTEEN_DECIMALS)

    assert (
        source.getPoolMonitoringPrice(
            first.asset.address,
            first.pair.address,
            first.partner.address,
        )
        == 200 * EIGHTEEN_DECIMALS
    )
    assert (
        source.getPoolMonitoringPrice(
            second.asset.address,
            second.pair.address,
            second.partner.address,
        )
        == 20 * EIGHTEEN_DECIMALS
    )
    assert source.getPriceAndHasFeed(first.asset.address) == (0, False)
    assert source.getPriceAndHasFeed(second.asset.address) == (0, False)
    assert source.getPricedAssets() == []


def test_generic_monitoring_price_rejects_invalid_config_without_asserting(
    uniswap_v2_factories,
    uniswap_v2_monitor_builder,
):
    monitor = uniswap_v2_monitor_builder()
    pool = _deploy_generic_pool(uniswap_v2_factories)
    other = uniswap_v2_factories["token"].deploy(18)
    values = [pool.asset.address, pool.pair.address, pool.partner.address]

    for index in range(3):
        invalid = values.copy()
        invalid[index] = ZERO_ADDRESS
        assert monitor.source.getPoolMonitoringPrice(*invalid) == 0

    assert (
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.asset.address,
        )
        == 0
    )
    assert (
        monitor.source.getPoolMonitoringPrice(
            other.address,
            pool.pair.address,
            pool.partner.address,
        )
        == 0
    )
    assert (
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            other.address,
        )
        == 0
    )


@pytest.mark.parametrize(
    "asset_reserve,partner_reserve,timestamp",
    [
        (0, EIGHTEEN_DECIMALS, 1_700_000_000),
        (EIGHTEEN_DECIMALS, 0, 1_700_000_000),
        (MAX_UINT112 + 1, EIGHTEEN_DECIMALS, 1_700_000_000),
        (EIGHTEEN_DECIMALS, MAX_UINT112 + 1, 1_700_000_000),
        (EIGHTEEN_DECIMALS, EIGHTEEN_DECIMALS, MAX_UINT32 + 1),
    ],
)
def test_generic_monitoring_price_rejects_invalid_pool_state(
    uniswap_v2_factories,
    uniswap_v2_monitor_builder,
    asset_reserve,
    partner_reserve,
    timestamp,
):
    monitor = uniswap_v2_monitor_builder(weth_usd=EIGHTEEN_DECIMALS)
    pool = _deploy_generic_pool(
        uniswap_v2_factories,
        asset_reserve=asset_reserve,
        partner_reserve=partner_reserve,
        timestamp=timestamp,
    )

    assert (
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )
        == 0
    )


def test_generic_monitoring_price_accepts_reserve_and_timestamp_boundaries(
    uniswap_v2_factories,
    uniswap_v2_monitor_builder,
):
    monitor = uniswap_v2_monitor_builder(weth_usd=2 * EIGHTEEN_DECIMALS)
    pool = _deploy_generic_pool(
        uniswap_v2_factories,
        asset_reserve=MAX_UINT112,
        partner_reserve=MAX_UINT112,
        timestamp=MAX_UINT32,
        asset_is_token0=False,
    )

    assert (
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )
        == 2 * EIGHTEEN_DECIMALS
    )


def test_generic_monitoring_price_uses_typed_pair_call_behavior(
    uniswap_v2_factories,
    uniswap_v2_monitor_builder,
):
    monitor = uniswap_v2_monitor_builder(weth_usd=EIGHTEEN_DECIMALS)
    pool = _deploy_generic_pool(uniswap_v2_factories)

    pool.pair.setWordResponseMode(2, 1)
    with boa.reverts():
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )

    pool.pair.setWordResponseMode(2, 2)
    assert (
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )
        == EIGHTEEN_DECIMALS // 10
    )

    pool.pair.setWordResponseMode(2, 0)
    pool.pair.setWordResponseMode(3, 3)
    with boa.reverts():
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )

    pool.pair.setWordResponseMode(3, 0)
    pool.pair.setReserveResponseMode(1)
    with boa.reverts():
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )

    pool.pair.setReserveResponseMode(2)
    assert (
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )
        == EIGHTEEN_DECIMALS // 10
    )

    pool.pair.setReserveResponseMode(0)
    pool.pair.setShouldRevert(True)
    with boa.reverts():
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )


def test_generic_monitoring_price_rejects_unsupported_decimals(
    uniswap_v2_factories,
    uniswap_v2_monitor_builder,
):
    monitor = uniswap_v2_monitor_builder()
    pool = _deploy_generic_pool(uniswap_v2_factories)

    pool.asset.setDecimals(19)
    assert (
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )
        == 0
    )

    pool.asset.setDecimals(18)
    pool.partner.setDecimals(19)
    assert (
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )
        == 0
    )


def test_generic_monitoring_price_reverts_when_token_has_no_decimals(
    uniswap_v2_factories,
    uniswap_v2_monitor_builder,
):
    monitor = uniswap_v2_monitor_builder()
    asset = boa.env.generate_address("uniswap-token-without-decimals")
    partner = uniswap_v2_factories["token"].deploy(18)
    pair = uniswap_v2_factories["pair"].deploy()
    pair.configureIdentity(ZERO_ADDRESS, asset, partner.address)
    pair.configureState(
        100 * EIGHTEEN_DECIMALS,
        10 * EIGHTEEN_DECIMALS,
        1_700_000_000,
        0,
        0,
        1,
    )

    with boa.reverts():
        monitor.source.getPoolMonitoringPrice(
            asset,
            pair.address,
            partner.address,
        )


def test_generic_monitoring_price_returns_zero_when_ratio_truncates_to_zero(
    uniswap_v2_factories,
    uniswap_v2_monitor_builder,
):
    monitor = uniswap_v2_monitor_builder(weth_usd=EIGHTEEN_DECIMALS)
    pool = _deploy_generic_pool(
        uniswap_v2_factories,
        asset_reserve=MAX_UINT112,
        partner_reserve=1,
    )

    assert (
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )
        == 0
    )


def test_generic_monitoring_price_uses_typed_price_desk_call_behavior(
    uniswap_v2_factories,
    uniswap_v2_monitor_builder,
):
    monitor = uniswap_v2_monitor_builder(weth_usd=2_000 * EIGHTEEN_DECIMALS)
    pool = _deploy_generic_pool(uniswap_v2_factories)

    monitor.price_desk.setPrice(0)
    assert (
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )
        == 0
    )

    monitor.price_desk.setPrice(2_000 * EIGHTEEN_DECIMALS)
    monitor.price_desk.setResponseMode(1)
    with boa.reverts():
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )

    for response_mode in (2, 3):
        monitor.price_desk.setResponseMode(response_mode)
        assert (
            monitor.source.getPoolMonitoringPrice(
                pool.asset.address,
                pool.pair.address,
                pool.partner.address,
            )
            == 200 * EIGHTEEN_DECIMALS
        )

    monitor.price_desk.setResponseMode(0)
    monitor.price_desk.setShouldRevert(True)
    with boa.reverts():
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )


def test_generic_monitoring_price_returns_zero_without_price_desk(
    uniswap_v2_factories,
    governance,
):
    default_pool = _deploy_generic_pool(uniswap_v2_factories)
    hq = uniswap_v2_factories["hq"].deploy(
        governance.address,
        ZERO_ADDRESS,
    )
    source = uniswap_v2_factories["source"].deploy(
        hq.address,
        default_pool.pair.address,
        default_pool.asset.address,
        default_pool.partner.address,
    )
    pool = _deploy_generic_pool(uniswap_v2_factories)

    assert (
        source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )
        == 0
    )


def test_generic_monitoring_price_overflow_fails_closed(
    uniswap_v2_factories,
    uniswap_v2_monitor_builder,
):
    monitor = uniswap_v2_monitor_builder(weth_usd=MAX_UINT256)
    pool = _deploy_generic_pool(
        uniswap_v2_factories,
        asset_reserve=1,
        partner_reserve=MAX_UINT112,
    )

    assert (
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )
        == 0
    )


def test_generic_monitoring_price_tracks_current_reserves_without_state(
    uniswap_v2_factories,
    uniswap_v2_monitor_builder,
):
    monitor = uniswap_v2_monitor_builder(
        weth_usd=2_000 * EIGHTEEN_DECIMALS
    )
    pool = _deploy_generic_pool(uniswap_v2_factories)

    assert (
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )
        == 200 * EIGHTEEN_DECIMALS
    )

    _set_generic_pool_state(
        pool,
        100 * EIGHTEEN_DECIMALS,
        EIGHTEEN_DECIMALS,
    )
    assert (
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )
        == 20 * EIGHTEEN_DECIMALS
    )

    _set_generic_pool_state(
        pool,
        100 * EIGHTEEN_DECIMALS,
        10 * EIGHTEEN_DECIMALS,
    )
    assert (
        monitor.source.getPoolMonitoringPrice(
            pool.asset.address,
            pool.pair.address,
            pool.partner.address,
        )
        == 200 * EIGHTEEN_DECIMALS
    )
    assert monitor.source.getPricedAssets() == []


def test_every_protocol_price_source_entrypoint_is_permanently_inert(
    uniswap_v2_monitor_builder,
    bob,
):
    fixture = uniswap_v2_monitor_builder()
    source = fixture.source
    ripe = fixture.ripe.address

    assert source.getPrice(ripe) == 0
    assert source.getPrice(ripe, 123) == 0
    assert source.getPrice(ripe, 123, fixture.price_desk.address) == 0
    assert source.getPriceAndHasFeed(ripe) == (0, False)
    assert source.getPriceAndHasFeed(ripe, 123) == (0, False)
    assert source.getPriceAndHasFeed(
        ripe, 123, fixture.price_desk.address
    ) == (0, False)
    assert source.hasPriceFeed(ripe) is False
    assert source.hasPendingPriceFeedUpdate(ripe) is False
    assert source.getPricedAssets() == []

    for method in (
        source.addPriceSnapshot,
        source.confirmNewPriceFeed,
        source.cancelNewPendingPriceFeed,
        source.confirmPriceFeedUpdate,
        source.cancelPriceFeedUpdate,
        source.disablePriceFeed,
        source.confirmDisablePriceFeed,
        source.cancelDisablePriceFeed,
    ):
        assert method(ripe, sender=bob) is False

    assert source.actionTimeLock() == 0
    assert source.hasPendingAction(1) is False
    assert source.getActionConfirmationBlock(1) == 0
    assert source.setActionTimeLock(1, sender=bob) is False
    assert source.setActionTimeLockAfterSetup(sender=bob) is False
    assert source.setActionTimeLockAfterSetup(1, sender=bob) is False
    assert source.isPaused() is False

    with boa.reverts("monitoring only"):
        source.pause(True, sender=bob)
    with boa.reverts("monitoring only"):
        source.recoverFunds(bob, ripe, sender=bob)
    with boa.reverts("monitoring only"):
        source.recoverFundsMany(bob, [ripe], sender=bob)


@pytest.mark.parametrize("zero_field", ["hq", "pair", "ripe", "weth"])
def test_constructor_rejects_zero_monitoring_identity(
    uniswap_v2_factories,
    governance,
    zero_field,
):
    ripe = uniswap_v2_factories["token"].deploy(18)
    weth = uniswap_v2_factories["token"].deploy(18)
    pair = uniswap_v2_factories["pair"].deploy()
    pair.configureIdentity(ZERO_ADDRESS, ripe.address, weth.address)
    price_desk = uniswap_v2_factories["price_desk"].deploy()
    hq = uniswap_v2_factories["hq"].deploy(
        governance.address, price_desk.address
    )
    values = {
        "hq": hq.address,
        "pair": pair.address,
        "ripe": ripe.address,
        "weth": weth.address,
    }
    values[zero_field] = ZERO_ADDRESS

    with boa.reverts("invalid monitoring config"):
        uniswap_v2_factories["source"].deploy(
            values["hq"], values["pair"], values["ripe"], values["weth"]
        )


def test_constructor_rejects_non_ripe_weth_pair(
    uniswap_v2_factories,
    governance,
):
    ripe = uniswap_v2_factories["token"].deploy(18)
    weth = uniswap_v2_factories["token"].deploy(18)
    other = uniswap_v2_factories["token"].deploy(18)
    pair = uniswap_v2_factories["pair"].deploy()
    pair.configureIdentity(ZERO_ADDRESS, ripe.address, other.address)
    price_desk = uniswap_v2_factories["price_desk"].deploy()
    hq = uniswap_v2_factories["hq"].deploy(
        governance.address, price_desk.address
    )

    with boa.reverts("not ripe weth pool"):
        uniswap_v2_factories["source"].deploy(
            hq.address, pair.address, ripe.address, weth.address
        )


@pytest.mark.parametrize(
    "ripe_decimals,weth_decimals,reason",
    [(6, 18, "invalid ripe decimals"), (18, 6, "invalid weth decimals")],
)
def test_constructor_rejects_noncanonical_token_decimals(
    uniswap_v2_factories,
    governance,
    ripe_decimals,
    weth_decimals,
    reason,
):
    ripe = uniswap_v2_factories["token"].deploy(ripe_decimals)
    weth = uniswap_v2_factories["token"].deploy(weth_decimals)
    pair = uniswap_v2_factories["pair"].deploy()
    pair.configureIdentity(ZERO_ADDRESS, ripe.address, weth.address)
    price_desk = uniswap_v2_factories["price_desk"].deploy()
    hq = uniswap_v2_factories["hq"].deploy(
        governance.address, price_desk.address
    )

    with boa.reverts(reason):
        uniswap_v2_factories["source"].deploy(
            hq.address, pair.address, ripe.address, weth.address
        )


def test_zero_reserve_returns_zero_without_manufacturing_a_feed(
    uniswap_v2_monitor_builder,
):
    fixture = uniswap_v2_monitor_builder()
    _set_raw_reserves(fixture, 0, 10 * EIGHTEEN_DECIMALS)

    ripe_reserve, weth_reserve, last_update = fixture.source.getRipePoolState()
    assert ripe_reserve == 0
    assert weth_reserve == 10 * EIGHTEEN_DECIMALS
    assert last_update == fixture.pair.pairTimestamp()
    assert fixture.source.getRipeWethMonitoringPrice() == 0
    assert fixture.source.getRipeUsdMonitoringPrice() == 0
    assert fixture.source.getPriceAndHasFeed(fixture.ripe.address) == (0, False)


def test_short_pool_response_reverts(uniswap_v2_monitor_builder):
    fixture = uniswap_v2_monitor_builder()
    fixture.pair.setReserveResponseMode(1)
    with boa.reverts():
        fixture.source.getRipePoolState()
    with boa.reverts():
        fixture.source.getRipeWethMonitoringPrice()
    with boa.reverts():
        fixture.source.getRipeUsdMonitoringPrice()


def test_overlong_pool_response_uses_abi_prefix(uniswap_v2_monitor_builder):
    fixture = uniswap_v2_monitor_builder()
    fixture.pair.setReserveResponseMode(2)
    ripe_reserve = 100 * EIGHTEEN_DECIMALS
    weth_reserve = 10 * EIGHTEEN_DECIMALS
    assert fixture.source.getRipePoolState() == (
        ripe_reserve,
        weth_reserve,
        fixture.pair.pairTimestamp(),
    )
    assert fixture.source.getRipeWethMonitoringPrice() == EIGHTEEN_DECIMALS // 10
    assert fixture.source.getRipeUsdMonitoringPrice() == 200 * EIGHTEEN_DECIMALS


def test_reverting_pool_read_reverts(uniswap_v2_monitor_builder):
    fixture = uniswap_v2_monitor_builder()
    fixture.pair.setShouldRevert(True)
    with boa.reverts():
        fixture.source.getRipePoolState()
    with boa.reverts():
        fixture.source.getRipeWethMonitoringPrice()
    with boa.reverts():
        fixture.source.getRipeUsdMonitoringPrice()


def test_short_price_desk_response_reverts_usd_view(uniswap_v2_monitor_builder):
    fixture = uniswap_v2_monitor_builder()
    fixture.price_desk.setResponseMode(1)
    assert fixture.source.getRipeWethMonitoringPrice() == EIGHTEEN_DECIMALS // 10
    with boa.reverts():
        fixture.source.getRipeUsdMonitoringPrice()


@pytest.mark.parametrize("response_mode", [2, 3])
def test_overlong_price_desk_response_uses_abi_prefix(
    uniswap_v2_monitor_builder,
    response_mode,
):
    fixture = uniswap_v2_monitor_builder()
    fixture.price_desk.setResponseMode(response_mode)
    assert fixture.source.getRipeWethMonitoringPrice() == EIGHTEEN_DECIMALS // 10
    assert fixture.source.getRipeUsdMonitoringPrice() == 200 * EIGHTEEN_DECIMALS


def test_reverting_weth_usd_price_reverts_usd_view(uniswap_v2_monitor_builder):
    fixture = uniswap_v2_monitor_builder()
    fixture.price_desk.setShouldRevert(True)
    assert fixture.source.getRipeWethMonitoringPrice() == EIGHTEEN_DECIMALS // 10
    with boa.reverts():
        fixture.source.getRipeUsdMonitoringPrice()


def test_missing_price_desk_only_zeroes_usd_monitoring(
    uniswap_v2_factories,
    governance,
):
    ripe = uniswap_v2_factories["token"].deploy(18)
    weth = uniswap_v2_factories["token"].deploy(18)
    pair = uniswap_v2_factories["pair"].deploy()
    pair.configureIdentity(ZERO_ADDRESS, ripe.address, weth.address)
    ripe.setBalance(pair.address, 100 * EIGHTEEN_DECIMALS)
    weth.setBalance(pair.address, 10 * EIGHTEEN_DECIMALS)
    pair.mint(governance.address)
    hq = uniswap_v2_factories["hq"].deploy(governance.address, ZERO_ADDRESS)
    source = uniswap_v2_factories["source"].deploy(
        hq.address, pair.address, ripe.address, weth.address
    )

    assert source.getRipeWethMonitoringPrice() == EIGHTEEN_DECIMALS // 10
    assert source.getRipeUsdMonitoringPrice() == 0


def test_price_multiplication_overflow_fails_closed(
    uniswap_v2_monitor_builder,
):
    fixture = uniswap_v2_monitor_builder()
    _set_raw_reserves(fixture, 1, MAX_UINT112)
    fixture.price_desk.setPrice(MAX_UINT256)

    assert fixture.source.getRipeWethMonitoringPrice() == MAX_UINT112 * EIGHTEEN_DECIMALS
    assert fixture.source.getRipeUsdMonitoringPrice() == 0


def test_spot_manipulation_is_immediate_and_has_no_persistent_snapshot_state(
    uniswap_v2_monitor_builder,
):
    fixture = uniswap_v2_monitor_builder()
    assert fixture.source.getRipeUsdMonitoringPrice() == 200 * EIGHTEEN_DECIMALS

    _set_raw_reserves(
        fixture,
        100 * EIGHTEEN_DECIMALS,
        1 * EIGHTEEN_DECIMALS,
    )
    assert fixture.source.getRipeUsdMonitoringPrice() == 20 * EIGHTEEN_DECIMALS

    _set_raw_reserves(
        fixture,
        100 * EIGHTEEN_DECIMALS,
        10 * EIGHTEEN_DECIMALS,
    )
    assert fixture.source.getRipeUsdMonitoringPrice() == 200 * EIGHTEEN_DECIMALS
    assert fixture.source.getPricedAssets() == []
