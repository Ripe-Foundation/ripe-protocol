from decimal import Decimal

import boa
import pytest

from config.robinhood_blueprint import Disposition, get_component

from .conftest import (
    FACTORY,
    ONE,
    WETH,
    WINDOW,
    ZERO,
    diagnostic_price,
    diagnostic_state,
    sync_pair,
)


def test_constructor_rejects_protocol_accounting_without_official_sequencer(
    ripe_hq_deploy,
    candidate_builder,
):
    f = candidate_builder(activate=False)
    with boa.reverts("accounting unavailable"):
        boa.load(
            "contracts/priceSources/RobinhoodUniswapV2RipePrices.vy",
            ripe_hq_deploy,
            ZERO,
            FACTORY,
            f.ripe.address,
            WETH,
            f.pair.address,
            1,
            100,
            ZERO,
            2,
        )


def test_constructor_rejects_unverified_sequencer_in_every_mode(
    ripe_hq_deploy,
    candidate_builder,
    alice,
):
    f = candidate_builder(activate=False)
    for mode, expected in ((1, "unverified sequencer"), (2, "accounting unavailable")):
        with boa.reverts(expected):
            boa.load(
                "contracts/priceSources/RobinhoodUniswapV2RipePrices.vy",
                ripe_hq_deploy,
                ZERO,
                FACTORY,
                f.ripe.address,
                WETH,
                f.pair.address,
                1,
                100,
                alice,
                mode,
            )


def test_constructor_rejects_wrong_factory_pair_and_token_membership(
    ripe_hq_deploy,
    candidate_builder,
    alice,
):
    f = candidate_builder(activate=False)
    f.factory.setPair(f.ripe.address, WETH, alice)
    with boa.reverts():
        boa.load(
            "contracts/priceSources/RobinhoodUniswapV2RipePrices.vy",
            ripe_hq_deploy,
            ZERO,
            FACTORY,
            f.ripe.address,
            WETH,
            f.pair.address,
            1,
            100,
            ZERO,
            1,
        )


@pytest.mark.parametrize(
    "runtime",
    [
        bytes.fromhex("601f6000f3"),
        bytes.fromhex("60216000f3"),
        bytes.fromhex("60006000fd"),
    ],
)
def test_constructor_rejects_malformed_or_reverting_token_decimals(
    ripe_hq_deploy,
    candidate_builder,
    runtime,
):
    f = candidate_builder(activate=False)
    boa.env.set_code(WETH, runtime)
    with boa.reverts():
        boa.load(
            "contracts/priceSources/RobinhoodUniswapV2RipePrices.vy",
            ripe_hq_deploy,
            ZERO,
            FACTORY,
            f.ripe.address,
            WETH,
            f.pair.address,
            1,
            100,
            ZERO,
            1,
        )


@pytest.mark.parametrize(
    "config",
    [
        (WINDOW - 1, WINDOW, WINDOW, 1, 1, 100, WINDOW, 3600),
        (WINDOW, WINDOW - 1, WINDOW, 1, 1, 100, WINDOW, 3600),
        (WINDOW, 2 * WINDOW + 1, WINDOW, 1, 1, 100, WINDOW, 3600),
        (WINDOW, WINDOW, WINDOW - 1, 1, 1, 100, WINDOW, 3600),
        (WINDOW, WINDOW, WINDOW, 0, 1, 100, WINDOW, 3600),
        (WINDOW, WINDOW, WINDOW, 1, 0, 100, WINDOW, 3600),
        (WINDOW, WINDOW, WINDOW, 1, 1, 0, WINDOW, 3600),
        (WINDOW, WINDOW, WINDOW, 1, 1, 2001, WINDOW, 3600),
        (WINDOW, WINDOW, WINDOW, 1, 1, 100, WINDOW - 1, 3600),
        (WINDOW, WINDOW, WINDOW, 1, 1, 100, WINDOW, 0),
        (WINDOW, WINDOW, WINDOW, 1, 1, 100, WINDOW, 48 * 3600 + 1),
    ],
)
def test_configuration_ceilings(candidate_builder, config):
    f = candidate_builder(activate=False)
    assert f.source.isValidOracleConfig(*config) is False


def test_timelock_setup_is_live_and_enforced(candidate_builder):
    f = candidate_builder(activate=False, finish_setup=False)
    assert f.source.actionTimeLock() == 0
    args = (WINDOW, WINDOW, WINDOW, 1, 1, 100, WINDOW, 3600)
    with boa.reverts("setup incomplete"):
        f.source.updateOracleConfig(*args, sender=f.governor)

    assert f.source.setActionTimeLockAfterSetup(sender=f.governor)
    assert f.source.actionTimeLock() == f.source.minActionTimeLock() == 1
    with boa.reverts("already set"):
        f.source.setActionTimeLockAfterSetup(sender=f.governor)


@pytest.mark.parametrize("selected", [10, 20])
def test_timelock_setup_accepts_exact_constructor_boundaries(candidate_builder, selected):
    f = candidate_builder(
        activate=False,
        finish_setup=False,
        min_time_lock=10,
        max_time_lock=20,
    )
    assert f.source.setActionTimeLockAfterSetup(selected, sender=f.governor)
    assert f.source.actionTimeLock() == selected


@pytest.mark.parametrize("selected", [9, 21])
def test_timelock_setup_rejects_values_outside_constructor_boundaries(candidate_builder, selected):
    f = candidate_builder(
        activate=False,
        finish_setup=False,
        min_time_lock=10,
        max_time_lock=20,
    )
    with boa.reverts("invalid time lock"):
        f.source.setActionTimeLockAfterSetup(selected, sender=f.governor)


def test_unauthorized_configuration_and_activation(candidate_builder, alice):
    f = candidate_builder(activate=False)
    with boa.reverts():
        f.source.updateOracleConfig(WINDOW, WINDOW, WINDOW, 1, 1, 100, WINDOW, 3600, sender=alice)
    assert f.source.update()
    boa.env.time_travel(seconds=WINDOW)
    assert f.source.update()
    with boa.reverts():
        f.source.initiateActivation(sender=alice)


def test_activation_is_separate_from_config_confirmation(candidate_builder):
    f = candidate_builder(activate=False)
    assert f.source.oracleConfig().activated is False
    assert f.source.getPrice(f.ripe.address, 3600, f.quote_desk.address) == 0
    assert diagnostic_state(f)[0] == 1
    assert f.source.update()
    boa.env.time_travel(seconds=WINDOW)
    assert f.source.update()
    assert f.source.oracleConfig().activated is False
    assert f.source.initiateActivation(sender=f.governor)
    with boa.reverts():
        f.source.confirmNewPriceFeed(f.ripe.address, sender=f.governor)
    boa.env.time_travel(blocks=1)
    assert f.source.confirmNewPriceFeed(f.ripe.address, sender=f.governor)
    assert diagnostic_state(f)[0] == 0


def test_disable_lifecycle_and_non_ripe_selectors(candidate_builder):
    f = candidate_builder()
    assert f.source.disablePriceFeed(f.quote.address, sender=f.governor) is False
    assert f.source.confirmDisablePriceFeed(f.quote.address, sender=f.governor) is False
    assert f.source.cancelDisablePriceFeed(f.quote.address, sender=f.governor) is False
    assert f.source.confirmPriceFeedUpdate(f.quote.address, sender=f.governor) is False
    assert f.source.cancelPriceFeedUpdate(f.quote.address, sender=f.governor) is False
    assert f.source.confirmNewPriceFeed(f.quote.address, sender=f.governor) is False
    assert f.source.cancelNewPendingPriceFeed(f.quote.address, sender=f.governor) is False

    assert f.source.disablePriceFeed(f.ripe.address, sender=f.governor)
    boa.env.time_travel(blocks=1)
    assert f.source.confirmDisablePriceFeed(f.ripe.address, sender=f.governor)
    assert f.source.getPrice(f.ripe.address, 3600, f.quote_desk.address) == 0
    assert f.source.hasPriceFeed(f.ripe.address) is False
    assert diagnostic_state(f)[0] == 1
    assert f.source.getPricedAssets() == [f.ripe.address]


def test_disable_cancellation(candidate_builder):
    f = candidate_builder()
    assert f.source.disablePriceFeed(f.ripe.address, sender=f.governor)
    assert f.source.hasPendingPriceFeedUpdate(f.ripe.address)
    assert f.source.cancelDisablePriceFeed(f.ripe.address, sender=f.governor)
    assert f.source.oracleConfig().activated


def test_config_timelock_cancellation_and_supersession(candidate_builder):
    f = candidate_builder()
    args = (WINDOW, 2 * WINDOW, 2 * WINDOW, 2, 2, 1_000, WINDOW, 3600)
    assert f.source.updateOracleConfig(*args, sender=f.governor)
    with boa.reverts():
        f.source.updateOracleConfig(*args, sender=f.governor)
    assert f.source.cancelPriceFeedUpdate(f.ripe.address, sender=f.governor)

    assert f.source.updateOracleConfig(*args, sender=f.governor)
    with boa.reverts():
        f.source.confirmPriceFeedUpdate(f.ripe.address, sender=f.governor)
    boa.env.time_travel(blocks=1)
    assert f.source.confirmPriceFeedUpdate(f.ripe.address, sender=f.governor)
    assert f.source.oracleConfig().minRipeReserve == 2


def test_config_confirmation_preserves_disable_that_happened_while_pending(candidate_builder):
    f = candidate_builder()
    args = (WINDOW, 2 * WINDOW, 2 * WINDOW, 2, 3, 1_000, WINDOW, 3600)
    assert f.source.updateOracleConfig(*args, sender=f.governor)
    assert f.source.disablePriceFeed(f.ripe.address, sender=f.governor)
    boa.env.time_travel(blocks=f.source.actionTimeLock())
    assert f.source.confirmDisablePriceFeed(f.ripe.address, sender=f.governor)
    assert f.source.oracleConfig().activated is False

    assert f.source.confirmPriceFeedUpdate(f.ripe.address, sender=f.governor)
    events = f.source.get_logs()
    assert f.source.oracleConfig().activated is False
    assert f.source.oracleConfig().minRipeReserve == 2
    assert [type(event).__name__ for event in events] == [
        "OracleConfigUpdatePrevious",
        "OracleConfigUpdateConfirmed",
    ]
    previous, confirmed = events
    assert previous.activated is False and confirmed.activated is False
    assert previous.minRipeReserve == 1 and confirmed.minRipeReserve == 2
    assert previous.minQuoteReserve == 1 and confirmed.minQuoteReserve == 3


def test_config_confirmation_preserves_activation_that_happened_while_pending(candidate_builder):
    f = candidate_builder(activate=False)
    assert f.source.update()
    boa.env.time_travel(seconds=WINDOW)
    assert f.source.update()
    args = (WINDOW, 2 * WINDOW, 2 * WINDOW, 2, 3, 1_000, WINDOW, 3600)
    assert f.source.updateOracleConfig(*args, sender=f.governor)
    assert f.source.initiateActivation(sender=f.governor)
    boa.env.time_travel(blocks=f.source.actionTimeLock())
    assert f.source.confirmNewPriceFeed(f.ripe.address, sender=f.governor)
    assert f.source.oracleConfig().activated is True

    assert f.source.confirmPriceFeedUpdate(f.ripe.address, sender=f.governor)
    events = f.source.get_logs()
    assert f.source.oracleConfig().activated is True
    assert [type(event).__name__ for event in events] == [
        "OracleConfigUpdatePrevious",
        "OracleConfigUpdateConfirmed",
    ]
    previous, confirmed = events
    assert previous.activated is True and confirmed.activated is True
    assert previous.maxSpotToTwapDeviationBps == 2_000
    assert confirmed.maxSpotToTwapDeviationBps == 1_000


def test_lifecycle_events_expose_action_and_boundary_fields(candidate_builder):
    f = candidate_builder(activate=False)
    assert f.source.update()
    checkpoint = f.source.get_logs()[0]
    assert type(checkpoint).__name__ == "CumulativePriceCheckpointUpdated"
    assert checkpoint.localTimestamp != 0
    assert checkpoint.pairTimestamp == boa.env.evm.patch.timestamp % 2**32

    boa.env.time_travel(seconds=WINDOW)
    assert f.source.update()
    names = [type(event).__name__ for event in f.source.get_logs()]
    assert names == ["CumulativePriceAverageUpdated", "CumulativePriceCheckpointUpdated"]

    assert f.source.initiateActivation(sender=f.governor)
    pending = f.source.get_logs()[0]
    assert type(pending).__name__ == "OracleActivationPending"
    assert pending.confirmationBlock == boa.env.evm.patch.block_number + f.source.actionTimeLock()
    boa.env.time_travel(blocks=f.source.actionTimeLock())
    assert f.source.confirmNewPriceFeed(f.ripe.address, sender=f.governor)
    activated = f.source.get_logs()[0]
    assert type(activated).__name__ == "OracleActivated"
    assert activated.activationTimestamp == boa.env.evm.patch.timestamp


def test_recovery_uses_standard_switchboard_authorization(
    candidate_builder,
    alpha_token,
    governance,
    switchboard_alpha,
    alice,
):
    f = candidate_builder()
    amount = 123
    alpha_token.transfer(f.source.address, amount, sender=governance.address)
    with boa.reverts():
        f.source.recoverFunds(alice, alpha_token.address, sender=alice)
    before = alpha_token.balanceOf(alice)
    f.source.recoverFunds(alice, alpha_token.address, sender=switchboard_alpha.address)
    assert alpha_token.balanceOf(alice) == before + amount


def test_reserve_floors_and_lp_supply(candidate_builder):
    f = candidate_builder(min_ripe_reserve=100 * ONE, min_quote_reserve=10 * ONE)
    f.pair.configureState(
        100 * ONE - 1,
        10 * ONE,
        f.pair.pairTimestamp(),
        f.pair.mockPrice0Cumulative(),
        f.pair.mockPrice1Cumulative(),
        f.pair.mockTotalSupply(),
    )
    assert diagnostic_state(f)[0] == 4
    f.pair.configureState(
        100 * ONE,
        10 * ONE,
        f.pair.pairTimestamp(),
        f.pair.mockPrice0Cumulative(),
        f.pair.mockPrice1Cumulative(),
        0,
    )
    assert diagnostic_state(f)[0] == 4


@pytest.mark.parametrize(
    "ripe_reserve,quote_reserve,expected_live",
    [
        (100 * ONE - 1, 10 * ONE, False),
        (100 * ONE, 10 * ONE - 1, False),
        (100 * ONE, 10 * ONE, True),
        (100 * ONE + 1, 10 * ONE + 1, True),
    ],
)
def test_independent_reserve_floor_boundaries(
    candidate_builder,
    ripe_reserve,
    quote_reserve,
    expected_live,
):
    f = candidate_builder(min_ripe_reserve=100 * ONE, min_quote_reserve=10 * ONE)
    sync_pair(f, ripe_reserve, quote_reserve)
    price = diagnostic_price(f)
    assert (price != 0) is expected_live


def test_spot_deviation_boundary(candidate_builder):
    f = candidate_builder(max_deviation_bps=100)
    # exactly 1% above the TWAP is accepted
    f.pair.configureState(
        f.reserve0,
        f.reserve1 * 101 // 100,
        f.pair.pairTimestamp(),
        f.pair.mockPrice0Cumulative(),
        f.pair.mockPrice1Cumulative(),
        f.pair.mockTotalSupply(),
    )
    assert diagnostic_state(f)[0] == 0
    # one additional raw quote unit crosses the integer-bps boundary
    f.pair.configureState(
        f.reserve0,
        f.reserve1 * 101 // 100 + f.reserve1 // 10_000,
        f.pair.pairTimestamp(),
        f.pair.mockPrice0Cumulative(),
        f.pair.mockPrice1Cumulative(),
        f.pair.mockTotalSupply(),
    )
    assert diagnostic_state(f)[0] == 8


def test_economic_execution_depth_reproduces_section_9():
    fee = Decimal("0.997")
    target = Decimal("0.99")
    multiplier = target * fee / (fee - target)
    max_input = Decimal("50000") / multiplier
    required_reserve = multiplier * Decimal("25000")
    assert Decimal("354") < max_input < Decimal("355")
    assert Decimal("3520000") < required_reserve < Decimal("3530000")
    execution_ratio = fee * Decimal("50000") / (Decimal("50000") + fee * max_input)
    assert abs(execution_ratio - target) < Decimal("1e-70")


def test_attack_cost_research_invariant_is_not_activation_authority():
    exposure = Decimal("100000")
    required_attack_cost = 5 * exposure
    # No manipulation-duration, inventory, unwind, or arbitrage model is frozen,
    # so current evidence establishes no positive C_attack value.
    established_attack_cost = Decimal("0")
    assert established_attack_cost <= required_attack_cost


@pytest.mark.parametrize(
    "deviation_bps,expected_low,expected_high",
    [
        (200, Decimal("2.5"), Decimal("3.5")),
        (2_000, Decimal("28"), Decimal("35")),
    ],
)
def test_spot_guard_dos_cost_is_explicitly_not_twap_attack_cost(
    deviation_bps,
    expected_low,
    expected_high,
):
    quote_side = Decimal("50000")
    fee = Decimal("0.997")
    target_price_ratio = Decimal(10_000 - deviation_bps - 1) / Decimal(10_000)
    # Solve r = x^2 / ((x + fee*dx) * (x + dx)), then immediately
    # reverse with the quote output. Normalize x=500k RIPE, y=$50k.
    ripe_side = Decimal("500000")
    discriminant = (Decimal(1) + fee) ** 2 - 4 * fee * (
        Decimal(1) - Decimal(1) / target_price_ratio
    )
    input_fraction = (-(Decimal(1) + fee) + discriminant.sqrt()) / (2 * fee)
    ripe_input = ripe_side * input_fraction
    quote_output = quote_side * fee * ripe_input / (ripe_side + fee * ripe_input)
    post_ripe = ripe_side + ripe_input
    post_quote = quote_side - quote_output
    ripe_bought_back = post_ripe * fee * quote_output / (post_quote + fee * quote_output)
    round_trip_cost_usd = (ripe_input - ripe_bought_back) * quote_side / ripe_side
    # This is a one-transaction availability threshold, not C_attack for a
    # sustained TWAP manipulation. It is orders of magnitude below 5E.
    assert expected_low < round_trip_cost_usd < expected_high


def test_gas_profile(candidate_builder):
    f = candidate_builder(activate=False)

    assert f.source.update()
    checkpoint_gas = f.source._computation.get_gas_used()

    boa.env.time_travel(seconds=WINDOW)
    assert f.source.update()
    average_gas = f.source._computation.get_gas_used()

    assert f.source.initiateActivation(sender=f.governor)
    boa.env.time_travel(blocks=1)
    assert f.source.confirmNewPriceFeed(f.ripe.address, sender=f.governor)

    assert diagnostic_price(f) != 0
    diagnostic_read_gas = f.source._computation.get_gas_used()

    assert f.source.getPrice(f.ripe.address, 3600, f.quote_desk.address) == 0
    inert_read_gas = f.source._computation.get_gas_used()

    assert f.quote_desk.consume(f.source.address, f.ripe.address, 3600) == 0
    inert_consumer_gas = f.quote_desk._computation.get_gas_used()

    print(
        "GAS_PROFILE "
        f"checkpoint={checkpoint_gas} average={average_gas} "
        f"diagnostic_read={diagnostic_read_gas} inert_read={inert_read_gas} "
        f"inert_consumer={inert_consumer_gas}"
    )
    assert max(
        checkpoint_gas,
        average_gas,
        diagnostic_read_gas,
        inert_read_gas,
        inert_consumer_gas,
    ) < 1_000_000


def _register_price_source(price_desk, source, governor, description, expected_id):
    assert price_desk.startAddNewAddressToRegistry(
        source.address,
        description,
        sender=governor,
    )
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock())
    assert price_desk.confirmNewAddressToRegistry(source.address, sender=governor) == expected_id


def _restore_safe_monitor(f, stale_time, registry):
    if diagnostic_state(f, stale_time, registry)[0] == 0:
        return
    assert f.source.update()
    if f.source.average().updatedAt == 0:
        boa.env.time_travel(seconds=WINDOW)
        assert f.source.update()
    assert diagnostic_state(f, stale_time, registry)[0] == 0


@pytest.mark.parametrize(
    "monitor_state,expected_status",
    [
        ("safe", 0),
        ("unsafe", 8),
        ("stale", 6),
        ("paused", 1),
        ("uninitialized", 1),
        ("dependency-failing", 2),
    ],
)
def test_real_price_desk_accidental_monitor_registration_is_price_inert(
    candidate_builder,
    price_desk,
    mock_price_source,
    mission_control,
    setGeneralConfig,
    switchboard_alpha,
    teller,
    monitor_state,
    expected_status,
):
    f = candidate_builder(
        activate=monitor_state != "uninitialized",
        max_staleness=WINDOW,
        max_quote_stale=48 * 3600,
    )
    setGeneralConfig(_priceStaleTime=24 * 3600)
    global_stale = mission_control.getPriceConfig().staleTime
    assert global_stale == 24 * 3600
    mock_price_source.setPrice(WETH, 2_000 * ONE)

    _register_price_source(
        price_desk,
        f.source,
        f.governor,
        "Robinhood Uniswap V2 RIPE TWAP",
        11,
    )

    if monitor_state != "uninitialized":
        _restore_safe_monitor(f, global_stale, price_desk.address)
    if monitor_state == "unsafe":
        sync_pair(f, f.reserve0, f.reserve1 * 2)
    elif monitor_state == "stale":
        boa.env.time_travel(seconds=WINDOW + 1)
    elif monitor_state == "paused":
        f.source.pause(True, sender=switchboard_alpha.address)
    elif monitor_state == "dependency-failing":
        f.pair.setShouldRevert(True)

    assert diagnostic_state(f, global_stale, price_desk.address)[0] == expected_status
    assert f.source.getPrice(f.ripe.address, global_stale, price_desk.address) == 0
    assert f.source.getPriceAndHasFeed(
        f.ripe.address,
        global_stale,
        price_desk.address,
    ) == (0, False)
    assert f.source.hasPriceFeed(f.ripe.address) is False

    # No authoritative source knows this synthetic RIPE asset. If the monitor
    # set PriceDesk's internal hasFeedConfig bit, the should-raise call would
    # revert. Both paths returning zero proves accidental registration is inert.
    assert price_desk.hasPriceFeed(f.ripe.address) is False
    assert price_desk.getPrice(f.ripe.address, False) == 0
    composed_gas = price_desk._computation.get_gas_used()
    assert composed_gas < 1_500_000
    if monitor_state == "safe":
        print(f"INERT_PRICE_DESK_GAS composed={composed_gas}")
    assert price_desk.getPrice(f.ripe.address, True) == 0

    # PriceDesk snapshot routing intentionally ignores the monitor. Watchers
    # must invoke update() and diagnostics directly.
    checkpoint = f.source.checkpoint()
    assert price_desk.addPriceSnapshot(f.ripe.address, sender=teller.address) is False
    assert f.source.checkpoint() == checkpoint


def test_real_price_desk_monitor_does_not_interfere_with_authoritative_sources(
    candidate_builder,
    price_desk,
    mock_price_source,
    ripe_hq_deploy,
):
    f = candidate_builder(max_quote_stale=48 * 3600)
    _register_price_source(
        price_desk,
        f.source,
        f.governor,
        "Robinhood Uniswap V2 RIPE TWAP",
        11,
    )

    # An earlier source wins without any behavior change.
    earlier_price = 123 * ONE
    mock_price_source.setPrice(f.ripe.address, earlier_price)
    f.pair.setShouldRevert(True)
    assert price_desk.getPrice(f.ripe.address, False) == earlier_price
    assert price_desk.getPrice(f.ripe.address, True) == earlier_price

    # With the earlier source removed, PriceDesk passes through the inert,
    # dependency-failing monitor and reaches a later authoritative source.
    assert mock_price_source.disablePriceFeed(f.ripe.address)
    later_source = boa.load(
        "contracts/mock/MockPriceSource.vy",
        ripe_hq_deploy,
        1,
        100,
    )
    later_price = 456 * ONE
    later_source.setPrice(f.ripe.address, later_price)
    _register_price_source(
        price_desk,
        later_source,
        f.governor,
        "Later authoritative source",
        12,
    )
    assert price_desk.getPrice(f.ripe.address, False) == later_price
    assert price_desk.getPrice(f.ripe.address, True) == later_price


def test_launch_configuration_has_no_lp_admission_or_psm_authority():
    assert get_component("CM-015").deployment is Disposition.REQUIRED
    assert get_component("CM-016").deployment is Disposition.REQUIRED
    assert get_component("CM-018").deployment is Disposition.REQUIRED
    assert {
        get_component(component_id).deployment
        for component_id in ("CM-017", "CM-019", "CM-020")
    } == {Disposition.OMITTED}
    assert all(
        component.name != "RobinhoodUniswapV2RipePrices"
        for component in (
            get_component(component_id)
            for component_id in ("CM-015", "CM-016", "CM-017", "CM-018", "CM-019", "CM-020")
        )
    )
