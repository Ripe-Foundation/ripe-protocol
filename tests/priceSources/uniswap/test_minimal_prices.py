from dataclasses import dataclass

import boa
import pytest

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT, ZERO_ADDRESS


@dataclass
class UniswapV2PricesFixture:
    source: object
    pair: object
    ripe: object
    quote: object
    quote_desk: object
    hq: object
    governor: str
    snapshot_caller: str
    switchboard_caller: str
    ripe_is_token0: bool


def set_pool_reserves(fixture, ripe_units, quote_units):
    ripe_reserve = ripe_units * 10 ** fixture.ripe.decimals()
    quote_reserve = quote_units * 10 ** fixture.quote.decimals()
    fixture.ripe.setBalance(fixture.pair.address, ripe_reserve)
    fixture.quote.setBalance(fixture.pair.address, quote_reserve)
    fixture.pair.sync()


@pytest.fixture
def uniswap_v2_prices_builder(governance):
    def build(
        *,
        ripe_is_token0=True,
        ripe_decimals=18,
        quote_decimals=18,
        ripe_units=100,
        quote_units=10,
        quote_usd=2_000 * EIGHTEEN_DECIMALS,
        pool_contains_ripe=True,
        finish_setup=True,
    ):
        ripe = boa.load("contracts/mock/MockUniswapV2Token.vy", ripe_decimals)
        quote = boa.load("contracts/mock/MockUniswapV2Token.vy", quote_decimals)
        other = boa.load("contracts/mock/MockUniswapV2Token.vy", 18)
        pair = boa.load("contracts/mock/MockUniswapV2Pair.vy")

        paired_ripe = ripe if pool_contains_ripe else other
        token0 = paired_ripe.address if ripe_is_token0 else quote.address
        token1 = quote.address if ripe_is_token0 else paired_ripe.address
        pair.configureIdentity(ZERO_ADDRESS, token0, token1)

        ripe_reserve = ripe_units * 10**ripe_decimals
        quote_reserve = quote_units * 10**quote_decimals
        reserve0 = ripe_reserve if ripe_is_token0 else quote_reserve
        reserve1 = quote_reserve if ripe_is_token0 else ripe_reserve
        token0_contract = paired_ripe if ripe_is_token0 else quote
        token1_contract = quote if ripe_is_token0 else paired_ripe
        token0_contract.setBalance(pair.address, reserve0)
        token1_contract.setBalance(pair.address, reserve1)
        pair.mint(governance.address)

        quote_desk = boa.load("contracts/mock/MockUniswapV2QuotePriceDesk.vy")
        quote_desk.setPrice(quote_usd)
        hq = boa.load(
            "contracts/mock/MockUniswapV2RipeHq.vy",
            governance.address,
            quote_desk.address,
        )
        snapshot_caller = boa.env.generate_address("uniswap snapshot caller")
        switchboard_caller = boa.env.generate_address("uniswap switchboard caller")
        hq.setValidRipeAddr(snapshot_caller, True)
        hq.setValidSwitchboardAddr(switchboard_caller, True)

        source = boa.load(
            "contracts/priceSources/UniswapV2Prices.vy",
            hq.address,
            ZERO_ADDRESS,
            pair.address,
            ripe.address,
            1,
            100,
        )
        if finish_setup:
            assert source.setActionTimeLockAfterSetup(sender=governance.address)

        return UniswapV2PricesFixture(
            source=source,
            pair=pair,
            ripe=ripe,
            quote=quote,
            quote_desk=quote_desk,
            hq=hq,
            governor=governance.address,
            snapshot_caller=snapshot_caller,
            switchboard_caller=switchboard_caller,
            ripe_is_token0=ripe_is_token0,
        )

    return build


####################
# Price correctness #
####################


@pytest.mark.parametrize("ripe_is_token0", [True, False])
def test_prices_ripe_from_either_uniswap_v2_token_position(
    uniswap_v2_prices_builder,
    ripe_is_token0,
):
    fixture = uniswap_v2_prices_builder(ripe_is_token0=ripe_is_token0)

    expected_price = 200 * EIGHTEEN_DECIMALS
    assert fixture.source.getUniswapV2RipePrice(fixture.ripe.address) == expected_price
    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    assert fixture.source.getPrice(fixture.ripe.address) == expected_price
    assert fixture.source.getPriceAndHasFeed(
        fixture.ripe.address,
        0,
        fixture.quote_desk.address,
    ) == (expected_price, True)


@pytest.mark.parametrize(
    "ripe_decimals,quote_decimals",
    [(18, 6), (6, 18), (8, 8), (0, 18), (18, 0)],
)
def test_normalizes_uniswap_v2_token_decimals(
    uniswap_v2_prices_builder,
    ripe_decimals,
    quote_decimals,
):
    fixture = uniswap_v2_prices_builder(
        ripe_decimals=ripe_decimals,
        quote_decimals=quote_decimals,
    )

    assert fixture.source.getUniswapV2RipePrice(
        fixture.ripe.address,
    ) == 200 * EIGHTEEN_DECIMALS


@pytest.mark.parametrize(
    "ripe_units,quote_units,expected_quote_per_ripe",
    [(100, 10, 10**17), (100, 5, 5 * 10**16), (25, 10, 4 * 10**17)],
)
def test_tracks_uniswap_v2_reserve_ratio(
    uniswap_v2_prices_builder,
    ripe_units,
    quote_units,
    expected_quote_per_ripe,
):
    fixture = uniswap_v2_prices_builder(
        ripe_units=ripe_units,
        quote_units=quote_units,
    )

    expected = expected_quote_per_ripe * 2_000
    assert fixture.source.getUniswapV2RipePrice(fixture.ripe.address) == expected


@pytest.mark.parametrize("quote_usd", [1, EIGHTEEN_DECIMALS, 2_000 * EIGHTEEN_DECIMALS])
def test_scales_linearly_with_quote_asset_price(uniswap_v2_prices_builder, quote_usd):
    fixture = uniswap_v2_prices_builder(quote_usd=quote_usd)
    assert fixture.source.getUniswapV2RipePrice(
        fixture.ripe.address,
    ) == quote_usd // 10


def test_zero_quote_price_returns_zero(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder(quote_usd=0)
    assert fixture.source.getUniswapV2RipePrice(fixture.ripe.address) == 0


@pytest.mark.parametrize("ripe_units,quote_units", [(0, 10), (100, 0), (0, 0)])
def test_zero_reserve_returns_zero(
    uniswap_v2_prices_builder,
    ripe_units,
    quote_units,
):
    fixture = uniswap_v2_prices_builder()
    set_pool_reserves(fixture, ripe_units, quote_units)
    assert fixture.source.getUniswapV2RipePrice(fixture.ripe.address) == 0


def test_constructor_rejects_pair_without_configured_ripe(uniswap_v2_prices_builder):
    with boa.reverts("ripe not in pool"):
        uniswap_v2_prices_builder(pool_contains_ripe=False)


def test_preserves_precision_when_inverse_reserve_ratio_is_sub_unit(
    uniswap_v2_prices_builder,
):
    fixture = uniswap_v2_prices_builder(ripe_is_token0=False)
    fixture.quote.setBalance(fixture.pair.address, 10**19)
    fixture.ripe.setBalance(fixture.pair.address, 1)
    fixture.pair.sync()
    assert fixture.source.getUniswapV2RipePrice(
        fixture.ripe.address,
    ) == 20_000 * 10**36


@pytest.mark.parametrize("ripe_decimals,quote_decimals", [(19, 18), (18, 19)])
def test_unsupported_token_decimals_return_zero(
    uniswap_v2_prices_builder,
    ripe_decimals,
    quote_decimals,
):
    fixture = uniswap_v2_prices_builder(
        ripe_decimals=ripe_decimals,
        quote_decimals=quote_decimals,
    )
    assert fixture.source.getUniswapV2RipePrice(fixture.ripe.address) == 0


@pytest.mark.parametrize("decimals", [19, 255, 256, 2**256 - 1])
def test_runtime_unsupported_token_decimals_return_zero(
    uniswap_v2_prices_builder,
    decimals,
):
    fixture = uniswap_v2_prices_builder()
    fixture.ripe.setDecimals(decimals)
    assert fixture.source.getUniswapV2RipePrice(fixture.ripe.address) == 0


def test_constructor_rejects_zero_pool_or_ripe(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    with boa.reverts("invalid pool or ripe"):
        boa.load(
            "contracts/priceSources/UniswapV2Prices.vy",
            fixture.hq.address,
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            fixture.ripe.address,
            1,
            100,
        )
    with boa.reverts("invalid pool or ripe"):
        boa.load(
            "contracts/priceSources/UniswapV2Prices.vy",
            fixture.hq.address,
            ZERO_ADDRESS,
            fixture.pair.address,
            ZERO_ADDRESS,
            1,
            100,
        )


def test_only_exposes_the_configured_ripe_asset(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()

    assert fixture.source.getPrice(
        fixture.quote.address,
        0,
        fixture.quote_desk.address,
    ) == 0
    assert fixture.source.getPriceAndHasFeed(
        fixture.quote.address,
        0,
        fixture.quote_desk.address,
    ) == (0, False)
    assert fixture.source.getUniswapV2RipePrice(fixture.quote.address) == 0
    assert fixture.source.hasPriceFeed(fixture.ripe.address) is True
    assert fixture.source.hasPriceFeed(fixture.quote.address) is False
    assert fixture.source.hasPriceFeed(ZERO_ADDRESS) is False


def test_constructor_sets_expected_immutables_and_defaults(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    config = fixture.source.priceConfigs(fixture.ripe.address)

    assert fixture.source.RIPE_WETH_POOL() == fixture.pair.address
    assert fixture.source.RIPE_TOKEN() == fixture.ripe.address
    assert config.minSnapshotDelay == 300
    assert config.maxNumSnapshots == 20
    assert config.maxUpsideDeviation == 1_000
    assert config.staleTime == 86_400
    assert config.nextIndex == 0
    assert fixture.source.getPricedAssets() == [fixture.ripe.address]
    assert len(boa.env.get_code(fixture.source.address)) == 13_925


def test_protocol_price_is_zero_until_first_snapshot(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    spot = 200 * EIGHTEEN_DECIMALS
    assert fixture.source.getUniswapV2RipePrice(fixture.ripe.address) == spot
    assert fixture.source.getPrice(fixture.ripe.address) == 0
    assert fixture.source.getPriceAndHasFeed(fixture.ripe.address) == (0, True)

    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    assert fixture.source.getPrice(fixture.ripe.address) == spot


def test_empty_price_desk_argument_uses_registered_price_desk(
    uniswap_v2_prices_builder,
):
    fixture = uniswap_v2_prices_builder()
    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    assert fixture.source.getPrice(fixture.ripe.address) == 200 * EIGHTEEN_DECIMALS


####################
# Snapshot behavior #
####################


def test_latest_snapshot_reads_current_uniswap_price(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    snapshot = fixture.source.getLatestSnapshot(fixture.ripe.address)
    assert snapshot.price == 200 * EIGHTEEN_DECIMALS
    assert snapshot.lastUpdate == boa.env.timestamp


def test_add_snapshot_stores_price_and_emits_event(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    log = filter_logs(fixture.source, "PriceSnapshotAdded")[-1]

    config = fixture.source.priceConfigs(fixture.ripe.address)
    assert config.lastSnapshot.price == 200 * EIGHTEEN_DECIMALS
    assert config.lastSnapshot.lastUpdate == boa.env.timestamp
    assert config.nextIndex == 1
    assert log.asset == fixture.ripe.address
    assert log.price == config.lastSnapshot.price
    assert log.lastUpdate == config.lastSnapshot.lastUpdate


def test_snapshot_delay_is_enforced_at_exact_boundary(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    assert not fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    boa.env.time_travel(seconds=299)
    assert not fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    boa.env.time_travel(seconds=1)
    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )


def test_snapshot_buffer_wraps_and_overwrites_oldest_entry(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    for _ in range(20):
        assert fixture.source.addPriceSnapshot(
            fixture.ripe.address,
            sender=fixture.snapshot_caller,
        )
        boa.env.time_travel(seconds=300)

    assert fixture.source.priceConfigs(fixture.ripe.address).nextIndex == 0
    first_timestamp = fixture.source.snapShots(fixture.ripe.address, 0).lastUpdate
    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    assert fixture.source.priceConfigs(fixture.ripe.address).nextIndex == 1
    assert fixture.source.snapShots(fixture.ripe.address, 0).lastUpdate > first_timestamp


def test_weighted_price_is_arithmetic_mean_of_live_snapshots(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    observed = []
    for quote_units in (10, 5, 4):
        set_pool_reserves(fixture, 100, quote_units)
        assert fixture.source.addPriceSnapshot(
            fixture.ripe.address,
            sender=fixture.snapshot_caller,
        )
        observed.append(fixture.source.priceConfigs(fixture.ripe.address).lastSnapshot.price)
        boa.env.time_travel(seconds=300)

    assert fixture.source.getWeightedPrice(fixture.ripe.address) == sum(observed) // len(observed)


def test_snapshot_upside_is_throttled_by_default_ten_percent(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    initial = fixture.source.priceConfigs(fixture.ripe.address).lastSnapshot.price

    boa.env.time_travel(seconds=300)
    set_pool_reserves(fixture, 100, 20)
    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    latest = fixture.source.priceConfigs(fixture.ripe.address).lastSnapshot.price
    assert latest == initial + initial * 1_000 // HUNDRED_PERCENT


def test_downside_is_immediate_and_combined_price_uses_lower_value(
    uniswap_v2_prices_builder,
):
    fixture = uniswap_v2_prices_builder()
    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    set_pool_reserves(fixture, 100, 5)

    spot = 100 * EIGHTEEN_DECIMALS
    assert fixture.source.getWeightedPrice(fixture.ripe.address) == 200 * EIGHTEEN_DECIMALS
    assert fixture.source.getPrice(
        fixture.ripe.address,
        0,
        fixture.quote_desk.address,
    ) == spot


def test_combined_price_uses_weighted_floor_when_spot_is_higher(
    uniswap_v2_prices_builder,
):
    fixture = uniswap_v2_prices_builder()
    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    set_pool_reserves(fixture, 100, 20)
    assert fixture.source.getWeightedPrice(
        fixture.ripe.address,
    ) == 200 * EIGHTEEN_DECIMALS
    assert fixture.source.getUniswapV2RipePrice(
        fixture.ripe.address,
    ) == 400 * EIGHTEEN_DECIMALS
    assert fixture.source.getPrice(
        fixture.ripe.address,
        0,
        fixture.quote_desk.address,
    ) == 200 * EIGHTEEN_DECIMALS


def test_all_stale_snapshots_fail_closed_to_zero(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    boa.env.time_travel(seconds=86_401)
    assert fixture.source.getWeightedPrice(fixture.ripe.address) == 0
    assert fixture.source.getPrice(fixture.ripe.address) == 0


@pytest.mark.xfail(
    strict=True,
    reason="pending owner decision: spot snapshots remain manipulable without TWAP or liquidity floor",
)
def test_repeated_manipulated_snapshots_cannot_persistently_suppress_price(
    uniswap_v2_prices_builder,
):
    fixture = uniswap_v2_prices_builder()
    honest = 200 * EIGHTEEN_DECIMALS
    for _ in range(5):
        set_pool_reserves(fixture, 100, 1)
        assert fixture.source.addPriceSnapshot(
            fixture.ripe.address,
            sender=fixture.snapshot_caller,
        )
        boa.env.time_travel(seconds=300)

    set_pool_reserves(fixture, 100, 10)
    assert fixture.source.getUniswapV2RipePrice(fixture.ripe.address) == honest
    assert fixture.source.getPrice(fixture.ripe.address) == honest


def test_non_ripe_snapshot_operations_are_noops(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    assert not fixture.source.addPriceSnapshot(
        fixture.quote.address,
        sender=fixture.snapshot_caller,
    )
    assert fixture.source.getWeightedPrice(fixture.quote.address) == 0
    assert fixture.source.getLatestSnapshot(fixture.quote.address) == (0, 0)


################################
# Governance and access control #
################################


@pytest.mark.parametrize(
    "config",
    [
        (0, 20, 1_000, 3_600),
        (604_801, 20, 1_000, 3_600),
        (300, 4, 1_000, 3_600),
        (300, 26, 1_000, 3_600),
        (300, 20, 0, 3_600),
        (300, 20, 10_001, 3_600),
        (300, 20, 1_000, 0),
        (300, 20, 1_000, 604_801),
    ],
)
def test_rejects_invalid_price_configurations(uniswap_v2_prices_builder, config):
    fixture = uniswap_v2_prices_builder()
    assert not fixture.source.isValidPriceConfig(*config)
    with boa.reverts("invalid config"):
        fixture.source.updatePriceConfig(*config, sender=fixture.governor)


def test_accepts_price_configuration_boundaries(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    assert fixture.source.isValidPriceConfig(1, 5, 1, 1)
    assert fixture.source.isValidPriceConfig(604_800, 25, 10_000, 604_800)


def test_governance_can_propose_and_confirm_configuration(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    new_config = (600, 15, 2_000, 7_200)
    assert fixture.source.updatePriceConfig(*new_config, sender=fixture.governor)
    pending = fixture.source.pendingPriceConfigs(fixture.ripe.address)
    assert pending.actionId != 0
    assert fixture.source.hasPendingPriceFeedUpdate(fixture.ripe.address)
    assert not fixture.source.canConfirmAction(pending.actionId)

    boa.env.time_travel(blocks=fixture.source.actionTimeLock())
    assert fixture.source.confirmPriceFeedUpdate(
        fixture.ripe.address,
        sender=fixture.governor,
    )
    log = filter_logs(fixture.source, "PriceConfigUpdated")[-1]
    config = fixture.source.priceConfigs(fixture.ripe.address)
    assert (
        config.minSnapshotDelay,
        config.maxNumSnapshots,
        config.maxUpsideDeviation,
        config.staleTime,
    ) == new_config
    assert not fixture.source.hasPendingPriceFeedUpdate(fixture.ripe.address)
    assert log.asset == fixture.ripe.address
    assert log.minSnapshotDelay == new_config[0]
    assert log.maxNumSnapshots == new_config[1]
    assert log.maxUpsideDeviation == new_config[2]
    assert log.staleTime == new_config[3]
    assert config.lastSnapshot.price == 200 * EIGHTEEN_DECIMALS
    assert config.nextIndex == 1


def test_configuration_cannot_be_confirmed_before_timelock(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    assert fixture.source.updatePriceConfig(600, 15, 2_000, 7_200, sender=fixture.governor)
    with boa.reverts("time lock not reached"):
        fixture.source.confirmPriceFeedUpdate(
            fixture.ripe.address,
            sender=fixture.governor,
        )
    assert fixture.source.hasPendingPriceFeedUpdate(fixture.ripe.address)


def test_config_confirmation_adds_fresh_snapshot(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    assert fixture.source.updatePriceConfig(600, 15, 2_000, 7_200, sender=fixture.governor)

    boa.env.time_travel(blocks=50)
    set_pool_reserves(fixture, 100, 5)
    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    latest_before_confirm = fixture.source.priceConfigs(fixture.ripe.address).lastSnapshot

    assert fixture.source.confirmPriceFeedUpdate(
        fixture.ripe.address,
        sender=fixture.governor,
    )
    config = fixture.source.priceConfigs(fixture.ripe.address)
    assert config.lastSnapshot == latest_before_confirm
    assert config.nextIndex == 2
    assert fixture.source.snapShots(fixture.ripe.address, 1) == latest_before_confirm


def test_config_confirmation_clamps_cursor_when_snapshot_window_shrinks(
    uniswap_v2_prices_builder,
):
    fixture = uniswap_v2_prices_builder()
    for _ in range(12):
        assert fixture.source.addPriceSnapshot(
            fixture.ripe.address,
            sender=fixture.snapshot_caller,
        )
        boa.env.time_travel(seconds=300)
    assert fixture.source.priceConfigs(fixture.ripe.address).nextIndex == 12

    assert fixture.source.updatePriceConfig(
        300,
        5,
        1_000,
        86_400,
        sender=fixture.governor,
    )
    boa.env.time_travel(blocks=fixture.source.actionTimeLock())
    assert fixture.source.confirmPriceFeedUpdate(
        fixture.ripe.address,
        sender=fixture.governor,
    )
    assert fixture.source.priceConfigs(fixture.ripe.address).nextIndex == 0

    boa.env.time_travel(seconds=300)
    old_slot = fixture.source.snapShots(fixture.ripe.address, 0)
    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    assert fixture.source.priceConfigs(fixture.ripe.address).nextIndex == 1
    assert fixture.source.snapShots(fixture.ripe.address, 0).lastUpdate > old_slot.lastUpdate


def test_governance_can_cancel_configuration(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    original = fixture.source.priceConfigs(fixture.ripe.address)
    assert fixture.source.updatePriceConfig(600, 15, 2_000, 7_200, sender=fixture.governor)
    assert fixture.source.cancelPriceFeedUpdate(
        fixture.ripe.address,
        sender=fixture.governor,
    )
    log = filter_logs(fixture.source, "PriceConfigUpdateCancelled")[-1]
    assert fixture.source.priceConfigs(fixture.ripe.address) == original
    assert not fixture.source.hasPendingPriceFeedUpdate(fixture.ripe.address)
    assert log.asset == fixture.ripe.address


def test_governance_cannot_cancel_configuration_while_paused(
    uniswap_v2_prices_builder,
):
    fixture = uniswap_v2_prices_builder()
    assert fixture.source.updatePriceConfig(
        600,
        15,
        2_000,
        7_200,
        sender=fixture.governor,
    )
    fixture.source.pause(True, sender=fixture.switchboard_caller)
    with boa.reverts("contract paused"):
        fixture.source.cancelPriceFeedUpdate(
            fixture.ripe.address,
            sender=fixture.governor,
        )
    assert fixture.source.hasPendingPriceFeedUpdate(fixture.ripe.address)
    fixture.source.pause(False, sender=fixture.switchboard_caller)
    assert fixture.source.cancelPriceFeedUpdate(
        fixture.ripe.address,
        sender=fixture.governor,
    )
    assert not fixture.source.hasPendingPriceFeedUpdate(fixture.ripe.address)


def test_new_config_proposal_replaces_pending_record_without_cancelling_old_action(
    uniswap_v2_prices_builder,
):
    fixture = uniswap_v2_prices_builder()
    assert fixture.source.updatePriceConfig(
        600,
        15,
        2_000,
        7_200,
        sender=fixture.governor,
    )
    old_aid = fixture.source.pendingPriceConfigs(fixture.ripe.address).actionId
    assert fixture.source.hasPendingAction(old_aid)

    assert fixture.source.updatePriceConfig(
        900,
        10,
        3_000,
        10_800,
        sender=fixture.governor,
    )
    new_aid = fixture.source.pendingPriceConfigs(fixture.ripe.address).actionId
    assert new_aid != old_aid
    assert fixture.source.hasPendingAction(old_aid)
    assert fixture.source.hasPendingAction(new_aid)


def test_expired_config_remains_reported_as_pending_until_cancelled(
    uniswap_v2_prices_builder,
):
    fixture = uniswap_v2_prices_builder()
    assert fixture.source.updatePriceConfig(
        600,
        15,
        2_000,
        7_200,
        sender=fixture.governor,
    )
    aid = fixture.source.pendingPriceConfigs(fixture.ripe.address).actionId
    expiration = fixture.source.pendingActions(aid).expiration
    boa.env.time_travel(blocks=expiration - boa.env.evm.patch.block_number)
    assert fixture.source.isExpired(aid)
    assert fixture.source.hasPendingAction(aid)
    assert fixture.source.hasPendingPriceFeedUpdate(fixture.ripe.address)
    assert fixture.source.cancelPriceFeedUpdate(
        fixture.ripe.address,
        sender=fixture.governor,
    )
    assert not fixture.source.hasPendingAction(aid)


def test_pre_setup_zero_timelock_requires_deployment_gate(
    uniswap_v2_prices_builder,
):
    fixture = uniswap_v2_prices_builder(finish_setup=False)
    assert fixture.source.actionTimeLock() == 0
    assert fixture.source.updatePriceConfig(
        600,
        15,
        2_000,
        7_200,
        sender=fixture.governor,
    )
    assert fixture.source.confirmPriceFeedUpdate(
        fixture.ripe.address,
        sender=fixture.governor,
    )
    assert fixture.source.setActionTimeLockAfterSetup(sender=fixture.governor)
    assert fixture.source.actionTimeLock() == fixture.source.minActionTimeLock()


def test_config_proposal_emits_complete_event(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    assert fixture.source.updatePriceConfig(600, 15, 2_000, 7_200, sender=fixture.governor)
    log = filter_logs(fixture.source, "PriceConfigUpdatePending")[-1]
    assert log.asset == fixture.ripe.address
    assert log.minSnapshotDelay == 600
    assert log.maxNumSnapshots == 15
    assert log.maxUpsideDeviation == 2_000
    assert log.staleTime == 7_200
    assert log.actionId == fixture.source.pendingPriceConfigs(fixture.ripe.address).actionId


def test_unauthorized_callers_cannot_snapshot_or_configure(
    uniswap_v2_prices_builder,
    bob,
):
    fixture = uniswap_v2_prices_builder()
    with boa.reverts("no perms"):
        fixture.source.addPriceSnapshot(fixture.ripe.address, sender=bob)
    with boa.reverts("no perms"):
        fixture.source.updatePriceConfig(300, 20, 1_000, 3_600, sender=bob)
    with boa.reverts("no perms"):
        fixture.source.confirmPriceFeedUpdate(fixture.ripe.address, sender=bob)
    with boa.reverts("no perms"):
        fixture.source.cancelPriceFeedUpdate(fixture.ripe.address, sender=bob)


def test_pause_zeroes_price_and_blocks_state_changes(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    assert fixture.source.addPriceSnapshot(
        fixture.ripe.address,
        sender=fixture.snapshot_caller,
    )
    fixture.source.pause(True, sender=fixture.switchboard_caller)
    assert fixture.source.getPrice(
        fixture.ripe.address,
        0,
        fixture.quote_desk.address,
    ) == 0
    assert fixture.source.getWeightedPrice(fixture.ripe.address) == 0
    assert fixture.source.hasPriceFeed(fixture.ripe.address)
    with boa.reverts("contract paused"):
        fixture.source.addPriceSnapshot(
            fixture.ripe.address,
            sender=fixture.snapshot_caller,
        )
    with boa.reverts("contract paused"):
        fixture.source.updatePriceConfig(300, 20, 1_000, 3_600, sender=fixture.governor)

    fixture.source.pause(False, sender=fixture.switchboard_caller)
    assert fixture.source.getPrice(
        fixture.ripe.address,
        0,
        fixture.quote_desk.address,
    ) == 200 * EIGHTEEN_DECIMALS


def test_unsupported_feed_lifecycle_stubs_report_no_action(
    uniswap_v2_prices_builder,
):
    fixture = uniswap_v2_prices_builder()
    assert not fixture.source.confirmNewPriceFeed(fixture.ripe.address)
    assert not fixture.source.cancelNewPendingPriceFeed(fixture.ripe.address)
    assert not fixture.source.disablePriceFeed(fixture.ripe.address)
    assert not fixture.source.confirmDisablePriceFeed(fixture.ripe.address)
    assert not fixture.source.cancelDisablePriceFeed(fixture.ripe.address)


def test_only_switchboard_can_pause(uniswap_v2_prices_builder, bob):
    fixture = uniswap_v2_prices_builder()
    with boa.reverts("no perms"):
        fixture.source.pause(True, sender=bob)


#####################
# Adversarial inputs #
#####################


def test_reverting_pair_read_fails_closed(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    fixture.pair.setShouldRevert(True)
    with boa.reverts():
        fixture.source.getUniswapV2RipePrice(fixture.ripe.address)


def test_truncated_reserve_response_fails_closed(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    fixture.pair.setReserveResponseMode(1)
    with boa.reverts():
        fixture.source.getUniswapV2RipePrice(fixture.ripe.address)


def test_reserve_response_with_trailing_bytes_uses_canonical_prefix(
    uniswap_v2_prices_builder,
):
    fixture = uniswap_v2_prices_builder()
    fixture.pair.setReserveResponseMode(2)
    assert fixture.source.getUniswapV2RipePrice(
        fixture.ripe.address,
    ) == 200 * EIGHTEEN_DECIMALS


@pytest.mark.parametrize("word_kind", [2, 3])
def test_malformed_token_identity_response_fails_closed(
    uniswap_v2_prices_builder,
    word_kind,
):
    fixture = uniswap_v2_prices_builder()
    fixture.pair.setWordResponseMode(word_kind, 1)
    with boa.reverts():
        fixture.source.getUniswapV2RipePrice(fixture.ripe.address)


def test_reverting_quote_price_source_fails_closed(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    fixture.quote_desk.setShouldRevert(True)
    with boa.reverts():
        fixture.source.getUniswapV2RipePrice(fixture.ripe.address)


def test_price_multiplication_overflow_returns_zero(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    fixture.ripe.setBalance(fixture.pair.address, 1)
    fixture.quote.setBalance(fixture.pair.address, 2**112 - 1)
    fixture.pair.sync()
    fixture.quote_desk.setPrice(2**256 - 1)
    assert fixture.source.getUniswapV2RipePrice(fixture.ripe.address) == 0


def test_truncated_quote_price_response_fails_closed(uniswap_v2_prices_builder):
    fixture = uniswap_v2_prices_builder()
    fixture.quote_desk.setResponseMode(1)
    with boa.reverts():
        fixture.source.getUniswapV2RipePrice(fixture.ripe.address)


@pytest.mark.parametrize("response_mode", [2, 3])
def test_quote_response_with_trailing_bytes_uses_canonical_prefix(
    uniswap_v2_prices_builder,
    response_mode,
):
    fixture = uniswap_v2_prices_builder()
    fixture.quote_desk.setResponseMode(response_mode)
    assert fixture.source.getUniswapV2RipePrice(
        fixture.ripe.address,
    ) == 200 * EIGHTEEN_DECIMALS


def test_recursive_quote_request_terminates_without_mutation(
    uniswap_v2_prices_builder,
):
    fixture = uniswap_v2_prices_builder()
    fixture.quote_desk.setRecursion(
        fixture.source.address,
        fixture.quote.address,
        0,
    )
    assert fixture.source.getUniswapV2RipePrice(fixture.ripe.address) == 0
    assert fixture.source.priceConfigs(fixture.ripe.address).nextIndex == 0
