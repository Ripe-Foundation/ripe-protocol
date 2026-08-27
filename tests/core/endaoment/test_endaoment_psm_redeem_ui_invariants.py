"""Pins the exact EndaomentPSM redeem behaviours the web UI depends on.

These are NOT new protocol requirements - they document existing behaviour that
the swap UI must mirror. If one of these fails, the UI's redeem quote or input
cap has silently become wrong.
"""

import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS

SIX_DECIMALS = 10**6
HUNDRED_PERCENT = 100_00


def test_maxRedeemable_user_arg_is_green_only(
    endaoment_psm, charlie_token, green_token, savings_green,
    switchboard_charlie, governance, mock_price_source, whale,
):
    """getMaxRedeemableGreenAmount(_user) mins against the user's GREEN balance.
    A user holding ONLY sGREEN gets 0 back, yet redeemGreen(..., True) succeeds.
    => UI must NOT pass the user address on the sGREEN route."""
    user = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    green_token.transfer(user, green_amount, sender=whale)
    green_token.approve(savings_green.address, green_amount, sender=user)
    shares = savings_green.deposit(green_amount, user, sender=user)

    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    charlie_token.mint(endaoment_psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)

    assert green_token.balanceOf(user) == 0
    assert savings_green.balanceOf(user) == shares

    # what a naive UI would query for the input cap
    naive_max = endaoment_psm.getMaxRedeemableGreenAmount(user, False)
    assert naive_max == 0, f"expected 0, got {naive_max}"

    # what the UI SHOULD query
    protocol_max_green = endaoment_psm.getMaxRedeemableGreenAmount(ZERO_ADDRESS, False)
    correct_max_shares = min(savings_green.convertToShares(protocol_max_green), shares)
    assert correct_max_shares == shares

    # and the redeem in fact works
    savings_green.approve(endaoment_psm.address, shares, sender=user)
    usdc_out = endaoment_psm.redeemGreen(shares, user, True, sender=user)
    assert usdc_out > 0


def test_over_max_silently_caps_no_revert(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source, whale,
):
    """Entering above the max does NOT revert - it silently caps.
    User signs for X, receives quote-for-max. UI must clamp input."""
    user = boa.env.generate_address()
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # PSM only holds 100 USDC -> max redeemable ~100 GREEN
    charlie_token.mint(endaoment_psm.address, 100 * SIX_DECIMALS, sender=governance.address)
    green_token.transfer(user, 5_000 * EIGHTEEN_DECIMALS, sender=whale)

    max_green = endaoment_psm.getMaxRedeemableGreenAmount(user, False)

    green_token.approve(endaoment_psm.address, 5_000 * EIGHTEEN_DECIMALS, sender=user)
    usdc_out = endaoment_psm.redeemGreen(5_000 * EIGHTEEN_DECIMALS, sender=user)

    # no revert; capped
    assert usdc_out == 100 * SIX_DECIMALS
    assert green_token.balanceOf(user) == 4_900 * EIGHTEEN_DECIMALS


def test_no_one_green_threshold_on_redeem(
    endaoment_psm, charlie_token, green_token, savings_green,
    switchboard_charlie, governance, mock_price_source, whale,
):
    """mint has `_wantsSavingsGreen and greenToMint > ONE_GREEN`.
    Redeem has NO such threshold - sub-1-GREEN sGREEN redeem works."""
    user = boa.env.generate_address()
    tiny = EIGHTEEN_DECIMALS // 2  # 0.5 GREEN

    green_token.transfer(user, tiny, sender=whale)
    green_token.approve(savings_green.address, tiny, sender=user)
    shares = savings_green.deposit(tiny, user, sender=user)

    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    charlie_token.mint(endaoment_psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)

    savings_green.approve(endaoment_psm.address, shares, sender=user)
    usdc_out = endaoment_psm.redeemGreen(shares, user, True, sender=user)
    assert usdc_out == SIX_DECIMALS // 2


def test_dust_rounds_to_zero_reverts(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source, whale,
):
    """Sub-1e12 wei GREEN rounds to 0 USDC -> reverts, not a silent 0-value burn."""
    user = boa.env.generate_address()
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    charlie_token.mint(endaoment_psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)

    dust = 10**11  # 0.0000001 GREEN -> 0 in 6dp
    green_token.transfer(user, 10**18, sender=whale)
    green_token.approve(endaoment_psm.address, 10**18, sender=user)

    with boa.reverts():
        endaoment_psm.redeemGreen(dust, sender=user)


def test_fee_100_percent_max_is_zero(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source, whale,
):
    """redeemFee == 100_00 -> getMaxRedeemableGreenAmount returns 0 and redeem reverts."""
    user = boa.env.generate_address()
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setRedeemFee(100_00, sender=switchboard_charlie.address)
    charlie_token.mint(endaoment_psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)

    green_token.transfer(user, 1000 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(endaoment_psm.address, 1000 * EIGHTEEN_DECIMALS, sender=user)

    assert endaoment_psm.getMaxRedeemableGreenAmount(user, False) == 0
    with boa.reverts():
        endaoment_psm.redeemGreen(1000 * EIGHTEEN_DECIMALS, sender=user)


def test_max_redeemable_round_trips_exactly_to_available_usdc(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source, whale,
):
    """getMaxRedeemableGreenAmount grosses up by 1/(1-fee). Redeeming exactly that
    amount must NOT revert on the `usdcBalance >= usdcAfterFee` liquidity assert -
    otherwise the UI's MAX button always fails."""
    user = boa.env.generate_address()
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setRedeemFee(500, sender=switchboard_charlie.address)  # 5%

    # 100 USDC of liquidity, interval limit (100k) is not binding
    charlie_token.mint(endaoment_psm.address, 100 * SIX_DECIMALS, sender=governance.address)
    green_token.transfer(user, 5_000 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(endaoment_psm.address, 5_000 * EIGHTEEN_DECIMALS, sender=user)

    max_green = endaoment_psm.getMaxRedeemableGreenAmount(user, False)
    # 100e18 * 10000 // 9500
    assert max_green == 100 * EIGHTEEN_DECIMALS * HUNDRED_PERCENT // (HUNDRED_PERCENT - 500)

    usdc_out = endaoment_psm.redeemGreen(max_green, sender=user)
    assert usdc_out == 100 * SIX_DECIMALS
    assert charlie_token.balanceOf(endaoment_psm.address) == 0
