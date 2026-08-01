import boa
import pytest

from .conftest import (
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


def test_constant_price_bootstrap_and_price(candidate_builder):
    f = candidate_builder()
    twap, period, updated_at = f.source.getTwapQuotePerRipe()
    expected = expected_quote_per_ripe(100 * ONE, 10 * ONE, 18, 18)
    assert twap == expected
    assert period == WINDOW
    assert updated_at != 0
    assert diagnostic_price(f) == expected * 2_000
    assert f.source.getPrice(f.ripe.address, 3600, f.quote_desk.address) == 0
    assert f.source.getPriceAndHasFeed(f.ripe.address, 3600, f.quote_desk.address) == (0, False)
    assert f.source.getPriceAndHasFeed(f.quote.address, 3600, f.quote_desk.address) == (0, False)
    assert f.source.hasPriceFeed(f.ripe.address) is False
    assert f.source.hasPriceFeed(f.quote.address) is False


@pytest.mark.parametrize("ripe_is_token0", [True, False])
def test_token_orientation(candidate_builder, ripe_is_token0):
    f = candidate_builder(ripe_is_token0=ripe_is_token0)
    assert f.source.RIPE_IS_TOKEN0() is ripe_is_token0
    expected = expected_quote_per_ripe(100 * ONE, 10 * ONE, 18, 18)
    assert f.source.getTwapQuotePerRipe()[0] == expected
    assert diagnostic_price(f) == expected * 2_000


@pytest.mark.parametrize(
    "ripe_decimals,quote_decimals",
    [(6, 18), (8, 18), (18, 6), (18, 8), (6, 8), (8, 6), (18, 18)],
)
def test_decimal_normalization(candidate_builder, ripe_decimals, quote_decimals):
    f = candidate_builder(ripe_decimals=ripe_decimals, quote_decimals=quote_decimals)
    expected = expected_quote_per_ripe(
        100 * 10**ripe_decimals,
        10 * 10**quote_decimals,
        ripe_decimals,
        quote_decimals,
    )
    twap = f.source.getTwapQuotePerRipe()[0]
    assert twap == expected
    assert diagnostic_price(f) == expected * 2_000


def test_increasing_and_decreasing_prices(candidate_builder):
    f = candidate_builder()
    old0, old1 = f.reserve0, f.reserve1
    checkpoint_timestamp = f.source.checkpoint().pairTimestamp

    boa.env.time_travel(seconds=WINDOW // 2)
    sync_pair(f, old0, old1 * 2)
    transition_timestamp = f.pair.pairTimestamp()
    boa.env.time_travel(seconds=WINDOW // 2)
    assert f.source.update()
    current_timestamp = f.source.checkpoint().pairTimestamp
    old_elapsed = (transition_timestamp - checkpoint_timestamp) % UINT32_MODULUS
    new_elapsed = (current_timestamp - transition_timestamp) % UINT32_MODULUS
    old_uq = f.reserve1 * Q112 // f.reserve0
    new_uq = 2 * f.reserve1 * Q112 // f.reserve0
    average_uq = (old_uq * old_elapsed + new_uq * new_elapsed) // (old_elapsed + new_elapsed)
    assert f.source.getTwapQuotePerRipe()[0] == normalize_uq(average_uq)

    sync_pair(f, old0, old1)
    boa.env.time_travel(seconds=WINDOW)
    assert f.source.update()
    assert f.source.getTwapQuotePerRipe()[0] == expected_quote_per_ripe(
        100 * ONE, 10 * ONE, 18, 18
    )


def test_multiple_observations_and_too_early_preserves_average(candidate_builder):
    f = candidate_builder()
    first_average = f.source.average()
    first_checkpoint = f.source.checkpoint()
    already_elapsed = boa.env.evm.patch.timestamp - first_checkpoint.localTimestamp
    boa.env.time_travel(seconds=WINDOW - already_elapsed - 1)
    assert f.source.update() is False
    assert f.source.average() == first_average
    assert f.source.checkpoint() == first_checkpoint
    boa.env.time_travel(seconds=1)
    assert f.source.update()
    assert f.source.average().averagingPeriodSeconds == WINDOW
    assert f.source.checkpoint().localTimestamp > first_checkpoint.localTimestamp


def test_exact_minimum_window_and_below_minimum(candidate_builder):
    f = candidate_builder(activate=False)
    assert f.source.update()
    checkpoint = f.source.checkpoint()
    boa.env.time_travel(seconds=WINDOW - 1)
    assert f.source.update() is False
    assert f.source.checkpoint() == checkpoint
    boa.env.time_travel(seconds=1)
    assert f.source.update()
    assert f.source.average().averagingPeriodSeconds == WINDOW


def test_stale_boundary(candidate_builder):
    f = candidate_builder(max_staleness=WINDOW)
    updated_at = f.source.average().updatedAt
    target = updated_at + WINDOW
    boa.env.time_travel(seconds=target - boa.env.evm.patch.timestamp)
    expected = expected_quote_per_ripe(100 * ONE, 10 * ONE, 18, 18) * 2_000
    assert diagnostic_price(f) == expected
    boa.env.time_travel(seconds=1)
    assert diagnostic_state(f)[0] == 6
    assert diagnostic_price(f) == 0
    assert f.source.getPriceAndHasFeed(f.ripe.address, 3600, f.quote_desk.address) == (0, False)


def test_rounding_is_downward(candidate_builder):
    f = candidate_builder(ripe_units=3, quote_units=1, quote_usd=ONE)
    twap = f.source.getTwapQuotePerRipe()[0]
    assert twap == (Q112 // 3) * ONE // Q112
    assert twap <= ONE // 3
    assert ONE // 3 - twap <= 1


def test_counterfactual_cumulative_math(candidate_builder):
    f = candidate_builder(activate=False)
    p0_before = f.pair.mockPrice0Cumulative()
    p1_before = f.pair.mockPrice1Cumulative()
    pair_timestamp = f.pair.pairTimestamp()
    boa.env.time_travel(seconds=137)
    p0, p1, current = f.source.getCurrentCumulativePrices()
    elapsed = (current - pair_timestamp) % UINT32_MODULUS
    assert p0 == (p0_before + (f.reserve1 * Q112 // f.reserve0) * elapsed) % UINT256_MODULUS
    assert p1 == (p1_before + (f.reserve0 * Q112 // f.reserve1) * elapsed) % UINT256_MODULUS


def test_pair_donation_is_invisible_until_sync_and_skim_preserves_reserves(candidate_builder, alice):
    f = candidate_builder(activate=False)
    quote_balance = f.quote.balanceOf(f.pair.address)
    donation = ONE
    f.quote.setBalance(f.pair.address, quote_balance + donation)
    reserves_before = (f.pair.reserve0(), f.pair.reserve1(), f.pair.pairTimestamp())
    cumulatives_before = (
        f.pair.mockPrice0Cumulative(),
        f.pair.mockPrice1Cumulative(),
    )

    assert (f.pair.reserve0(), f.pair.reserve1(), f.pair.pairTimestamp()) == reserves_before
    f.pair.skim(alice)
    assert f.quote.balanceOf(alice) == donation
    assert (f.pair.reserve0(), f.pair.reserve1(), f.pair.pairTimestamp()) == reserves_before
    assert (
        f.pair.mockPrice0Cumulative(),
        f.pair.mockPrice1Cumulative(),
    ) == cumulatives_before

    f.quote.setBalance(f.pair.address, quote_balance + donation)
    boa.env.time_travel(seconds=71)
    f.pair.sync()
    elapsed = (f.pair.pairTimestamp() - reserves_before[2]) % UINT32_MODULUS
    assert f.pair.reserve1() == quote_balance + donation
    assert f.pair.mockPrice0Cumulative() == (
        cumulatives_before[0] + (f.reserve1 * Q112 // f.reserve0) * elapsed
    ) % UINT256_MODULUS


def test_pair_mint_and_burn_self_accumulate_before_reserve_writes(candidate_builder, alice):
    f = candidate_builder(activate=False)
    supply_before = f.pair.mockTotalSupply()
    cumulative_before = f.pair.mockPrice0Cumulative()
    timestamp_before = f.pair.pairTimestamp()
    f.ripe.setBalance(f.pair.address, f.reserve0 + 2 * ONE)
    f.quote.setBalance(f.pair.address, f.reserve1 + ONE)
    boa.env.time_travel(seconds=83)
    minted = f.pair.mint(alice)
    elapsed = (f.pair.pairTimestamp() - timestamp_before) % UINT32_MODULUS
    assert minted == ONE
    assert f.pair.mockTotalSupply() == supply_before + minted
    assert f.pair.mockPrice0Cumulative() == (
        cumulative_before + (f.reserve1 * Q112 // f.reserve0) * elapsed
    ) % UINT256_MODULUS

    supply = f.pair.mockTotalSupply()
    liquidity = supply // 4
    boa.env.time_travel(seconds=97)
    amount0, amount1 = f.pair.burn(alice, liquidity)
    assert amount0 != 0 and amount1 != 0
    assert f.pair.mockTotalSupply() == supply - liquidity
    assert f.ripe.balanceOf(alice) == amount0
    assert f.quote.balanceOf(alice) == amount1


def test_pair_swap_and_flash_swap_follow_fee_adjusted_constant_product(candidate_builder, alice):
    f = candidate_builder(activate=False)
    amount0_in = ONE
    amount1_out = amount0_in * 997 * f.reserve1 // (f.reserve0 * 1_000 + amount0_in * 997)
    f.ripe.setBalance(f.pair.address, f.reserve0 + amount0_in)
    boa.env.time_travel(seconds=101)
    f.pair.swap(0, amount1_out, alice, b"")
    assert f.pair.reserve0() == f.reserve0 + amount0_in
    assert f.pair.reserve1() == f.reserve1 - amount1_out
    assert f.quote.balanceOf(alice) == amount1_out

    borrower = boa.load("contracts/mock/MockUniswapV2FlashBorrower.vy")
    reserve0 = f.pair.reserve0()
    reserve1 = f.pair.reserve1()
    flash_out = 10**15
    flash_repay = (flash_out * 1_000 + 996) // 997
    f.quote.setBalance(borrower.address, flash_repay - flash_out)
    borrower.configure(
        f.pair.address,
        f.ripe.address,
        f.quote.address,
        0,
        flash_repay,
    )
    boa.env.time_travel(seconds=103)
    f.pair.swap(0, flash_out, borrower.address, b"flash")
    assert f.pair.reserve0() == reserve0
    assert f.pair.reserve1() == reserve1 - flash_out + flash_repay


def test_sparse_pair_operations_feed_source_from_pair_cumulatives(candidate_builder):
    f = candidate_builder(activate=False)
    assert f.source.update()
    first = f.source.checkpoint()
    boa.env.time_travel(seconds=307)
    sync_pair(f, f.reserve0, f.reserve1 * 2)
    transition = f.pair.pairTimestamp()
    boa.env.time_travel(seconds=WINDOW - 307)
    assert f.source.update()
    elapsed_old = (transition - first.pairTimestamp) % UINT32_MODULUS
    elapsed_new = WINDOW - elapsed_old
    expected_uq = (
        (f.reserve1 * Q112 // f.reserve0) * elapsed_old
        + (2 * f.reserve1 * Q112 // f.reserve0) * elapsed_new
    ) // WINDOW
    assert f.source.average().price0Average == expected_uq


def test_add_price_snapshot_is_never_update_hook(candidate_builder):
    f = candidate_builder(activate=False)
    before = f.source.checkpoint()
    assert f.source.addPriceSnapshot(f.ripe.address) is False
    assert f.source.addPriceSnapshot(f.quote.address) is False
    assert f.source.checkpoint() == before
