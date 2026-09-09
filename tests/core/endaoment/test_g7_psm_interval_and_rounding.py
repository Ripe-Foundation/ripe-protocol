"""Group 7 (PSM) — never-skip #4: interval passage, live reconfiguration, rounding.

Interval time is ``block.number``.  All block counts here are relative to the
*local* ``endaoment_psm`` fixture (``numBlocksPerInterval == 43_200``); the RH
scaffolding in ``config/robinhood_launch.py`` uses ``7_200``.
"""

import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from conf_utils import filter_logs
from tests.core.endaoment.g7_psm_helpers import after_psm_tx


SIX_DECIMALS = 10**6
ONE_USDC = 10**6
ONE_GREEN = 10**18
HUNDRED_PERCENT = 100_00
FIXTURE_BLOCKS = 43_200


def _enable(psm, sb):
    if not psm.canMint():
        psm.setCanMint(True, sender=sb.address)
    if not psm.canRedeem():
        psm.setCanRedeem(True, sender=sb.address)


def _fund_usdc(charlie_token, governance, who, amount, psm):
    charlie_token.mint(who, amount, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=who)


def _give_green(green_token, credit_engine, who, amount):
    green_token.mint(who, amount, sender=credit_engine.address)


# ---------------------------------------------------------------- passage


def test_g7_interval_window_boundaries_are_half_open(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source
):
    """`start + numBlocksPerInterval > block.number` -> exact expiry is a FRESH window."""
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)

    user = boa.env.generate_address()
    _fund_usdc(charlie_token, governance, user, 400_000 * SIX_DECIMALS, psm)

    assert psm.globalMintInterval().start == 0
    first = psm.mintGreen(60_000 * SIX_DECIMALS, user, False, sender=user)
    after_psm_tx()
    start = psm.globalMintInterval().start
    assert start == boa.env.evm.patch.block_number
    assert psm.getAvailIntervalMint() == psm.maxIntervalMint() - first

    # one block before expiry: still the same window
    boa.env.time_travel(blocks=FIXTURE_BLOCKS - 1)
    assert boa.env.evm.patch.block_number == start + FIXTURE_BLOCKS - 1
    assert psm.getAvailIntervalMint() == psm.maxIntervalMint() - first

    # exactly at start + numBlocks: the window has expired, capacity is full again
    boa.env.time_travel(blocks=1)
    assert boa.env.evm.patch.block_number == start + FIXTURE_BLOCKS
    assert psm.getAvailIntervalMint() == psm.maxIntervalMint()

    # and the next mint opens a brand new window rather than accumulating
    second = psm.mintGreen(60_000 * SIX_DECIMALS, user, False, sender=user)
    data = psm.globalMintInterval()
    assert data.start == start + FIXTURE_BLOCKS
    assert data.amount == second               # reset, not first + second


def test_g7_mint_and_redeem_intervals_are_independent(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance,
    mock_price_source, credit_engine
):
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)
    charlie_token.mint(psm.address, 100_000 * SIX_DECIMALS, sender=governance.address)

    user = boa.env.generate_address()
    _fund_usdc(charlie_token, governance, user, 50_000 * SIX_DECIMALS, psm)
    _give_green(green_token, credit_engine, user, 30_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    psm.mintGreen(50_000 * SIX_DECIMALS, user, False, sender=user)
    after_psm_tx()
    assert psm.getAvailIntervalMint() == psm.maxIntervalMint() - 50_000 * EIGHTEEN_DECIMALS
    assert psm.getAvailIntervalRedemptions() == psm.maxIntervalRedeem()   # untouched
    assert psm.globalRedeemInterval().start == 0

    psm.redeemGreen(30_000 * EIGHTEEN_DECIMALS, user, False, sender=user)
    assert psm.getAvailIntervalRedemptions() == psm.maxIntervalRedeem() - 30_000 * EIGHTEEN_DECIMALS
    assert psm.getAvailIntervalMint() == psm.maxIntervalMint() - 50_000 * EIGHTEEN_DECIMALS


# ---------------------------------------------- live reconfiguration


def test_g7_lowering_max_below_consumed_yields_zero_without_resetting_start(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source
):
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)

    user = boa.env.generate_address()
    _fund_usdc(charlie_token, governance, user, 200_000 * SIX_DECIMALS, psm)
    psm.mintGreen(60_000 * SIX_DECIMALS, user, False, sender=user)
    after_psm_tx()
    data_before = psm.globalMintInterval()

    psm.setMaxIntervalMint(10_000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)
    # `maxIntervalMint -= min(data.amount, maxIntervalMint)` saturates at zero
    assert psm.getAvailIntervalMint() == 0
    assert psm.globalMintInterval() == data_before      # start/amount untouched
    with boa.reverts("zero amount"):
        psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user)

    # raising it gives back exactly newMax - consumed
    psm.setMaxIntervalMint(90_000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)
    assert psm.getAvailIntervalMint() == 90_000 * EIGHTEEN_DECIMALS - data_before.amount
    assert psm.globalMintInterval() == data_before

    psm.setMaxIntervalMint(100_000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)


def test_g7_shortening_duration_expires_the_live_window_immediately(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source
):
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)

    user = boa.env.generate_address()
    _fund_usdc(charlie_token, governance, user, 400_000 * SIX_DECIMALS, psm)
    psm.mintGreen(100_000 * SIX_DECIMALS, user, False, sender=user)
    assert psm.getAvailIntervalMint() == 0

    boa.env.time_travel(blocks=100)
    # shorten below the elapsed distance -> window is already over
    psm.setNumBlocksPerInterval(10, sender=switchboard_charlie.address)
    assert psm.getAvailIntervalMint() == psm.maxIntervalMint()
    assert psm.globalMintInterval().amount == 100_000 * EIGHTEEN_DECIMALS  # storage kept

    # lengthening again re-activates the *same* stored window
    psm.setNumBlocksPerInterval(FIXTURE_BLOCKS, sender=switchboard_charlie.address)
    assert psm.getAvailIntervalMint() == 0

    psm.setNumBlocksPerInterval(1, sender=switchboard_charlie.address)
    assert psm.getAvailIntervalMint() == psm.maxIntervalMint()
    psm.setNumBlocksPerInterval(FIXTURE_BLOCKS, sender=switchboard_charlie.address)


def test_g7_max_accepted_interval_duration_keeps_window_check_callable(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source
):
    """Previously `max_value - 1` overflowed `start + duration` and bricked the window.

    This test now proves ordinary mint/view stay callable at that duration.
    """
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)

    user = boa.env.generate_address()
    _fund_usdc(charlie_token, governance, user, 200_000 * SIX_DECIMALS, psm)
    boa.env.time_travel(blocks=5)          # start must exceed 1 for the add to wrap
    psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user)
    after_psm_tx()
    start = psm.globalMintInterval().start
    assert start > 1

    psm.setNumBlocksPerInterval(MAX_UINT256 - 1, sender=switchboard_charlie.address)
    assert start + (MAX_UINT256 - 1) > MAX_UINT256
    assert psm.getAvailIntervalMint() == psm.maxIntervalMint() - 1_000 * EIGHTEEN_DECIMALS
    assert psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user) > 0
    after_psm_tx()

    psm.setNumBlocksPerInterval(FIXTURE_BLOCKS, sender=switchboard_charlie.address)
    assert psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user) > 0
    after_psm_tx()


def test_g7_unsafe_mint_cap_is_rejected_but_redeem_cap_remains_unbounded(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance,
    mock_price_source, credit_engine
):
    """Previously `maxIntervalMint == max_value - 1` overflowed PriceDesk.getAssetAmount.

    The setter now rejects that value. This test proves a legal cap still mints,
    and `maxIntervalRedeem == max_value - 1` remains harmless on redeem.
    """
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)
    charlie_token.mint(psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)

    user = boa.env.generate_address()
    _fund_usdc(charlie_token, governance, user, 10_000 * SIX_DECIMALS, psm)
    _give_green(green_token, credit_engine, user, 10_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    with boa.reverts("invalid max"):
        psm.setMaxIntervalMint(MAX_UINT256 - 1, sender=switchboard_charlie.address)
    psm.setMaxIntervalMint(50_000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)
    assert psm.getMaxUsdcAmountForMint(user, False) > 0
    assert psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user) > 0
    after_psm_tx()

    psm.setMaxIntervalRedeem(MAX_UINT256 - 1, sender=switchboard_charlie.address)
    assert psm.getMaxRedeemableGreenAmount(user, False) > 0
    assert psm.redeemGreen(1_000 * EIGHTEEN_DECIMALS, user, False, sender=user) > 0
    after_psm_tx()

    psm.setMaxIntervalMint(100_000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)
    psm.setMaxIntervalRedeem(100_000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)


# ---------------------------------------------- quote-bounds property grid


@pytest.mark.parametrize("price_num", [90, 95, 100, 101, 110])
@pytest.mark.parametrize("fee", [0, 1, 37, 5_00])
def test_g7_mint_never_exceeds_its_own_pre_call_quotes(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance,
    mock_price_source, price_num, fee
):
    """Unit-correct bounds: USDC debit <= getMaxUsdcAmountForMint, GREEN <= getAvailIntervalMint."""
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, price_num * EIGHTEEN_DECIMALS // 100)
    _enable(psm, switchboard_charlie)
    if psm.mintFee() != fee:
        psm.setMintFee(fee, sender=switchboard_charlie.address)

    user = boa.env.generate_address()
    _fund_usdc(charlie_token, governance, user, 500_000 * SIX_DECIMALS, psm)

    for request in (1, 13, 999_999, 7_777 * SIX_DECIMALS + 3, MAX_UINT256):
        quote_usdc = psm.getMaxUsdcAmountForMint(user, False)
        quote_green = psm.getAvailIntervalMint()
        pre_usdc = charlie_token.balanceOf(user)
        pre_amount = psm.globalMintInterval().amount
        if quote_usdc == 0:
            with boa.reverts("zero amount"):
                psm.mintGreen(request, user, False, sender=user)
            after_psm_tx()
            continue
        minted = psm.mintGreen(request, user, False, sender=user)
        after_psm_tx()
        spent = pre_usdc - charlie_token.balanceOf(user)
        assert spent <= quote_usdc, (price_num, fee, request, spent, quote_usdc)
        assert minted <= quote_green, (price_num, fee, request, minted, quote_green)
        increment = psm.globalMintInterval().amount - (pre_amount if psm.globalMintInterval().start != 0 else 0)
        assert minted <= quote_green
        assert increment in (minted, psm.globalMintInterval().amount)

    if psm.mintFee() != 0:
        psm.setMintFee(0, sender=switchboard_charlie.address)


@pytest.mark.parametrize("price_num", [90, 95, 100, 101, 110])
@pytest.mark.parametrize("fee", [0, 1, 37, 5_00])
def test_g7_raw_green_redeem_never_exceeds_its_own_pre_call_quote(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance,
    mock_price_source, credit_engine, price_num, fee
):
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, price_num * EIGHTEEN_DECIMALS // 100)
    _enable(psm, switchboard_charlie)
    if psm.redeemFee() != fee:
        psm.setRedeemFee(fee, sender=switchboard_charlie.address)
    charlie_token.mint(psm.address, 250_000 * SIX_DECIMALS, sender=governance.address)

    user = boa.env.generate_address()
    _give_green(green_token, credit_engine, user, 500_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    price = price_num * EIGHTEEN_DECIMALS // 100
    for request in (1, 10**12, 10**12 - 1, 3_333 * EIGHTEEN_DECIMALS + 7, MAX_UINT256):
        quote = psm.getMaxRedeemableGreenAmount(user, False)
        available = psm.getAvailableUsdc()
        pre_green = green_token.balanceOf(user)
        pre_supply = green_token.totalSupply()

        # predict the outcome from the contract arithmetic rather than catching
        # the revert: titanoboa 0.2.7 cannot render this BoaError's stack trace.
        exp_green = min(request, quote, pre_green)
        to_give = min(exp_green * ONE_USDC // price, exp_green * ONE_USDC // ONE_GREEN)
        after_fee = to_give - to_give * fee // HUNDRED_PERCENT

        if exp_green == 0:
            with boa.reverts("zero amount"):
                psm.redeemGreen(request, user, False, sender=user)
            after_psm_tx()
        elif to_give == 0:
            with boa.reverts("zero redeem amount"):
                psm.redeemGreen(request, user, False, sender=user)
            after_psm_tx()
        elif after_fee == 0:
            with boa.reverts("zero amount"):
                psm.redeemGreen(request, user, False, sender=user)
            after_psm_tx()
        else:
            out = psm.redeemGreen(request, user, False, sender=user)
            after_psm_tx()
            burned = pre_green - green_token.balanceOf(user)
            assert burned == exp_green
            assert burned == pre_supply - green_token.totalSupply()
            assert burned <= quote, (price_num, fee, request, burned, quote)
            assert out == after_fee
            assert out <= available, (price_num, fee, request, out, available)
            continue

        # every early stop is a full rollback
        assert green_token.balanceOf(user) == pre_green
        assert green_token.totalSupply() == pre_supply

    if psm.redeemFee() != 0:
        psm.setRedeemFee(0, sender=switchboard_charlie.address)


# ---------------------------------------------------------------- dust


def test_g7_dust_at_one_micro_usdc_and_the_green_conversion_unit(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance,
    mock_price_source, credit_engine
):
    """One micro-USDC mints 1e12 GREEN; one GREEN-decimal-unit below that redeems to zero."""
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)
    charlie_token.mint(psm.address, 1_000 * SIX_DECIMALS, sender=governance.address)

    user = boa.env.generate_address()
    _fund_usdc(charlie_token, governance, user, 10 * SIX_DECIMALS, psm)

    minted = psm.mintGreen(1, user, False, sender=user)
    after_psm_tx()
    assert minted == 10**12                        # one micro-USDC -> 1e12 GREEN

    _give_green(green_token, credit_engine, user, 10 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    # 1e12 GREEN is exactly one micro-USDC
    assert psm.redeemGreen(10**12, user, False, sender=user) == 1
    after_psm_tx()
    # one wei less rounds the payout to zero and stops *before* any GREEN moves
    pre = green_token.balanceOf(user)
    with boa.reverts("zero redeem amount"):
        psm.redeemGreen(10**12 - 1, user, False, sender=user)
    assert green_token.balanceOf(user) == pre


def test_g7_first_nonzero_fee_boundaries(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance,
    mock_price_source, credit_engine
):
    """`amount * bps // 10_000` — the first non-zero fee lands at ceil(10_000 / bps)."""
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)
    charlie_token.mint(psm.address, 100_000 * SIX_DECIMALS, sender=governance.address)

    for bps in (1, 10, 1_00):
        boundary = -(-HUNDRED_PERCENT // bps)      # ceil
        psm.setMintFee(bps, sender=switchboard_charlie.address)
        user = boa.env.generate_address()
        _fund_usdc(charlie_token, governance, user, 10 * SIX_DECIMALS, psm)

        psm.mintGreen(boundary - 1, user, False, sender=user)
        after_psm_tx()
        assert filter_logs(psm, "MintGreen")[0].usdcFee == 0
        psm.mintGreen(boundary, user, False, sender=user)
        after_psm_tx()
        assert filter_logs(psm, "MintGreen")[0].usdcFee == 1

        psm.setRedeemFee(bps, sender=switchboard_charlie.address)
        _give_green(green_token, credit_engine, user, 10 * EIGHTEEN_DECIMALS)
        green_token.approve(psm.address, MAX_UINT256, sender=user)
        psm.redeemGreen((boundary - 1) * 10**12, user, False, sender=user)
        after_psm_tx()
        assert filter_logs(psm, "RedeemGreen")[0].usdcFee == 0
        psm.redeemGreen(boundary * 10**12, user, False, sender=user)
        assert filter_logs(psm, "RedeemGreen")[0].usdcFee == 1
        after_psm_tx()
        psm.setRedeemFee(0, sender=switchboard_charlie.address)

    psm.setMintFee(0, sender=switchboard_charlie.address)
