import boa
import pytest

from .conftest import (
    FACTORY,
    ONE,
    Q112,
    UINT32_MODULUS,
    UINT256_MODULUS,
    WINDOW,
    diagnostic_price,
    diagnostic_state,
    expected_quote_per_ripe,
    normalize_uq,
    sync_pair,
)


def test_same_timestamp_and_same_block_updates(candidate_builder):
    f = candidate_builder(activate=False)
    assert f.source.update()
    checkpoint = f.source.checkpoint()
    assert f.source.update() is False
    assert f.source.update() is False
    assert f.source.checkpoint() == checkpoint


def test_permissionless_callers_cannot_bypass_timestamp_boundaries(candidate_builder, alice, bob):
    f = candidate_builder(activate=False)
    assert f.source.update(sender=alice)
    checkpoint = f.source.checkpoint()
    boa.env.time_travel(seconds=WINDOW - 1)
    assert f.source.update(sender=bob) is False
    assert f.source.checkpoint() == checkpoint
    boa.env.time_travel(seconds=1)
    assert f.source.update(sender=alice)
    assert f.source.average().averagingPeriodSeconds == WINDOW


def test_one_block_spot_manipulation_fails_closed_without_changing_twap(candidate_builder):
    f = candidate_builder()
    trusted = diagnostic_price(f)
    average = f.source.average()
    sync_pair(f, f.reserve0, f.reserve1 * 2)
    assert diagnostic_state(f)[0] == 8
    assert diagnostic_price(f) == 0
    assert f.source.update() is False
    assert f.source.average() == average
    sync_pair(f, f.reserve0, f.reserve1)
    assert diagnostic_price(f) == trusted


def test_manipulation_immediately_before_boundary_does_not_rewrite_history(candidate_builder):
    f = candidate_builder()
    boa.env.time_travel(seconds=WINDOW)
    sync_pair(f, f.reserve0, f.reserve1 * 2)
    assert f.source.update()
    expected = expected_quote_per_ripe(100 * ONE, 10 * ONE, 18, 18)
    assert f.source.getTwapQuotePerRipe()[0] == expected
    assert diagnostic_state(f)[0] == 8
    sync_pair(f, f.reserve0, f.reserve1)
    assert diagnostic_price(f) == expected * 2_000


def test_manipulation_immediately_after_boundary_does_not_rewrite_history(candidate_builder):
    f = candidate_builder()
    boa.env.time_travel(seconds=WINDOW + 1)
    sync_pair(f, f.reserve0, f.reserve1 * 2)
    assert f.source.update()
    expected = expected_quote_per_ripe(100 * ONE, 10 * ONE, 18, 18)
    assert f.source.getTwapQuotePerRipe()[0] == expected
    assert diagnostic_state(f)[0] == 8


def test_full_window_manipulation_is_not_misrepresented_as_single_block_protection(candidate_builder):
    f = candidate_builder()
    elapsed = boa.env.evm.patch.timestamp - f.source.checkpoint().localTimestamp
    boa.env.time_travel(seconds=WINDOW - elapsed)
    assert f.source.update()
    sync_pair(f, f.reserve0, f.reserve1 * 2)
    boa.env.time_travel(seconds=WINDOW)
    assert f.source.update()
    expected = normalize_uq(2 * f.reserve1 * Q112 // f.reserve0)
    assert f.source.getTwapQuotePerRipe()[0] == expected
    assert diagnostic_price(f) == expected * 2_000


@pytest.mark.parametrize("reserve0,reserve1", [(0, 10**18), (10**18, 0)])
def test_zero_reserves_fail_closed(candidate_builder, reserve0, reserve1):
    f = candidate_builder()
    f.pair.configureState(
        reserve0,
        reserve1,
        f.pair.pairTimestamp(),
        f.pair.mockPrice0Cumulative(),
        f.pair.mockPrice1Cumulative(),
        f.pair.mockTotalSupply(),
    )
    assert diagnostic_state(f)[0] == 4
    assert f.source.update() is False


@pytest.mark.parametrize("mode", [1, 2])
def test_short_and_oversized_reserve_response_fail_closed(candidate_builder, mode):
    f = candidate_builder()
    f.pair.setReserveResponseMode(mode)
    assert diagnostic_state(f)[0] == 2
    assert f.source.update() is False


def test_reverting_pair_calls_fail_closed(candidate_builder):
    f = candidate_builder()
    f.pair.setShouldRevert(True)
    assert diagnostic_state(f)[0] == 2
    assert f.source.update() is False


@pytest.mark.parametrize("kind", [1, 2, 3, 4, 5, 6])
@pytest.mark.parametrize("mode", [1, 2, 3])
def test_malformed_or_reverting_pair_word_reads_fail_closed(
    candidate_builder,
    kind,
    mode,
):
    f = candidate_builder()
    f.pair.setWordResponseMode(kind, mode)
    assert diagnostic_price(f) == 0
    assert f.source.update() is False


def test_pair_token_mismatch_and_wrong_factory_fail_closed(candidate_builder, alice):
    f = candidate_builder()
    f.pair.configureIdentity(FACTORY, f.ripe.address, alice)
    assert diagnostic_state(f)[0] == 3
    assert f.source.update() is False


def test_wrong_factory_pair_fails_closed(candidate_builder, alice):
    f = candidate_builder()
    f.factory.setPair(f.ripe.address, f.quote.address, alice)
    assert diagnostic_state(f)[0] == 3
    assert f.source.update() is False


@pytest.mark.parametrize("mode", [1, 2])
def test_short_and_oversized_factory_response_fail_closed(candidate_builder, mode):
    f = candidate_builder()
    f.factory.setResponseMode(mode)
    assert diagnostic_state(f)[0] == 3
    assert f.source.update() is False


def test_reverting_factory_response_fails_closed(candidate_builder):
    f = candidate_builder()
    f.factory.setShouldRevert(True)
    assert diagnostic_state(f)[0] == 3
    assert f.source.update() is False


@pytest.mark.parametrize("quote_case", ["absent", "zero", "revert", "short", "oversized"])
def test_quote_authority_failures_do_not_revert(candidate_builder, quote_case):
    f = candidate_builder()
    registry = f.quote_desk.address
    if quote_case == "absent":
        registry = "0x0000000000000000000000000000000000000000"
    elif quote_case == "zero":
        f.quote_desk.setPrice(0)
    elif quote_case == "revert":
        f.quote_desk.setShouldRevert(True)
    elif quote_case == "short":
        f.quote_desk.setResponseMode(1)
    else:
        f.quote_desk.setResponseMode(2)
    assert diagnostic_state(f, registry=registry)[0] == 9
    assert f.source.getPrice(f.ripe.address, 3600, registry) == 0
    assert f.source.getPriceAndHasFeed(f.ripe.address, 3600, registry) == (0, False)


def test_quote_stale_policy_rejects_zero_or_looser_mission_control_value(candidate_builder):
    f = candidate_builder(max_quote_stale=3600)
    assert diagnostic_price(f, 3600) != 0
    assert diagnostic_price(f, 3601) == 0
    assert diagnostic_price(f, 0) == 0
    assert f.source.getSafetyStateAtStaleTime(3600, f.quote_desk.address)[0] == 0
    assert f.source.getSafetyStateAtStaleTime(3601, f.quote_desk.address)[0] == 10
    assert f.source.getSafetyStateAtStaleTime(0, f.quote_desk.address)[0] == 10


def test_adversarial_recursive_registry_fails_closed(candidate_builder):
    f = candidate_builder()
    f.quote_desk.setRecursion(f.source.address, f.ripe.address, 3600)
    assert diagnostic_state(f)[0] == 9


def test_timestamp_wrap_boundary(candidate_builder):
    now = boa.env.evm.patch.timestamp
    target = UINT32_MODULUS - 900
    if now < target:
        boa.env.time_travel(seconds=target - now)
    f = candidate_builder(activate=False)
    assert f.source.update()
    checkpoint = f.source.checkpoint()
    assert checkpoint.pairTimestamp == boa.env.evm.patch.timestamp % UINT32_MODULUS
    boa.env.time_travel(seconds=WINDOW)
    assert f.source.update()
    assert f.source.average().averagingPeriodSeconds == WINDOW
    assert f.source.checkpoint().pairTimestamp == (
        checkpoint.pairTimestamp + WINDOW
    ) % UINT32_MODULUS


def test_accumulator_wrap_boundary(candidate_builder):
    f = candidate_builder(activate=False)
    near_wrap = UINT256_MODULUS - (f.reserve1 * Q112 // f.reserve0) * (WINDOW // 2)
    f.pair.configureState(
        f.reserve0,
        f.reserve1,
        boa.env.evm.patch.timestamp % UINT32_MODULUS,
        near_wrap,
        near_wrap,
        f.pair.mockTotalSupply(),
    )
    assert f.source.update()
    boa.env.time_travel(seconds=WINDOW)
    assert f.source.update()
    assert f.source.average().price0Average == f.reserve1 * Q112 // f.reserve0


def test_paused_source_fails_closed(candidate_builder, switchboard_alpha):
    f = candidate_builder()
    f.source.pause(True, sender=switchboard_alpha.address)
    assert diagnostic_state(f)[0] == 1
    assert f.source.update() is False


def test_stale_observation_recovers_only_after_new_full_window(candidate_builder):
    f = candidate_builder(max_period=WINDOW, max_staleness=WINDOW)
    boa.env.time_travel(seconds=WINDOW + 1)
    assert diagnostic_state(f)[0] == 6
    assert f.source.update()
    names = [type(event).__name__ for event in f.source.get_logs()]
    assert f.source.average().updatedAt == 0
    assert f.source.oracleConfig().activated is True
    assert f.source.activationTimestamp() != 0
    assert names == [
        "CumulativePriceCheckpointUpdated",
        "CumulativePriceCheckpointResynchronized",
    ]
    boa.env.time_travel(seconds=WINDOW)
    assert f.source.update()
    assert f.source.average().updatedAt != 0
    assert f.source.oracleConfig().activated is True
    assert diagnostic_state(f)[0] == 0


@pytest.mark.parametrize(
    "elapsed,expected_average,expected_resync",
    [
        (2 * WINDOW - 1, True, False),
        (2 * WINDOW, True, False),
        (2 * WINDOW + 1, False, True),
    ],
)
def test_maximum_averaging_period_boundaries(
    candidate_builder,
    elapsed,
    expected_average,
    expected_resync,
):
    f = candidate_builder(activate=False, max_period=2 * WINDOW)
    assert f.source.update()
    boa.env.time_travel(seconds=elapsed)
    assert f.source.update()
    names = [type(event).__name__ for event in f.source.get_logs()]
    assert (f.source.average().updatedAt != 0) is expected_average
    assert ("CumulativePriceCheckpointResynchronized" in names) is expected_resync


def test_reserve_floor_resynchronizes_without_governance_deactivation(candidate_builder):
    floor = 100 * ONE
    f = candidate_builder(min_ripe_reserve=floor)
    sync_pair(f, floor - 1, f.reserve1)
    assert f.source.update()
    resync = [
        event
        for event in f.source.get_logs()
        if type(event).__name__ == "CumulativePriceCheckpointResynchronized"
    ]
    assert f.source.oracleConfig().activated is True
    assert f.source.average().updatedAt == 0
    assert len(resync) == 1 and resync[0].reasonCode == 2

    sync_pair(f, floor, f.reserve1)
    boa.env.time_travel(seconds=WINDOW)
    assert f.source.update()
    assert f.source.oracleConfig().activated is True
    assert diagnostic_state(f)[0] == 0


def test_spot_negative_control_detects_reserve_pricing_substitution(candidate_builder):
    f = candidate_builder()
    original_twap = f.source.getTwapQuotePerRipe()[0]
    sync_pair(f, f.reserve0, f.reserve1 * 2)
    assert f.source.getTwapQuotePerRipe()[0] == original_twap
    assert diagnostic_state(f)[0] == 8


def test_orientation_negative_control(candidate_builder):
    f = candidate_builder(ripe_is_token0=False, ripe_units=100, quote_units=10)
    assert f.source.getTwapQuotePerRipe()[0] == expected_quote_per_ripe(
        100 * ONE, 10 * ONE, 18, 18
    )
    assert f.source.getTwapQuotePerRipe()[0] != 10 * ONE
    expected = expected_quote_per_ripe(100 * ONE, 10 * ONE, 18, 18) * 2_000
    assert diagnostic_price(f) == expected


def test_minimum_window_negative_control(candidate_builder):
    f = candidate_builder(activate=False)
    assert f.source.update()
    boa.env.time_travel(seconds=WINDOW - 1)
    assert f.source.update() is False
    assert f.source.average().updatedAt == 0


def test_stale_negative_control(candidate_builder):
    f = candidate_builder(max_staleness=WINDOW)
    boa.env.time_travel(seconds=WINDOW + 1)
    assert diagnostic_state(f)[0] == 6
