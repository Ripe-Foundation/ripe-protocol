from dataclasses import dataclass

import boa
import pytest

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


MAX_UINT112 = 2**112 - 1


@dataclass
class UniswapV2MonitorFixture:
    source: object
    pair: object
    ripe: object
    weth: object
    price_desk: object
    hq: object
    ripe_is_token0: bool


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
