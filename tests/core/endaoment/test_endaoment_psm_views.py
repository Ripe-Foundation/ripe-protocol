import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256


SIX_DECIMALS = 10**6  # For tokens like USDC that have 6 decimals
ONE_DAY_BLOCKS = 43_200


################################
# View Function Accuracy Tests #
################################


def test_get_max_usdc_amount_for_mint_respects_interval_limit(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """getMaxUsdcAmountForMint should return amount limited by interval"""
    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Max interval mint is 100,000 GREEN by default (from fixture)
    # At 1:1 price, this means 100,000 USDC
    # Don't pass a user to get the theoretical max (not limited by user balance)
    max_usdc = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, False)
    assert max_usdc == 100_000 * SIX_DECIMALS


def test_get_max_usdc_amount_for_mint_after_partial_mint(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """getMaxUsdcAmountForMint should decrease after minting"""
    user = boa.env.generate_address()
    initial_mint = 10_000 * SIX_DECIMALS

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Check max before mint (not user-specific)
    max_before = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, False)
    assert max_before == 100_000 * SIX_DECIMALS

    # Mint some GREEN
    charlie_token.mint(user, initial_mint, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, initial_mint, sender=user)
    endaoment_psm.mintGreen(initial_mint, user, False, sender=user)

    # Check max after mint (not user-specific)
    max_after = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, False)
    assert max_after == (100_000 - 10_000) * SIX_DECIMALS


def test_get_max_usdc_amount_for_mint_considers_user_balance(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """getMaxUsdcAmountForMint should be limited by user's USDC balance when user is provided"""
    user = boa.env.generate_address()

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # User with no USDC should get 0 when user address is provided
    max_usdc = endaoment_psm.getMaxUsdcAmountForMint(user, False)
    assert max_usdc == 0

    # Give user some USDC (less than interval limit)
    charlie_token.mint(user, 1_000 * SIX_DECIMALS, sender=governance.address)

    # Now user should get amount limited by their balance
    max_usdc = endaoment_psm.getMaxUsdcAmountForMint(user, False)
    assert max_usdc == 1_000 * SIX_DECIMALS


def test_get_avail_interval_mint(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """getAvailIntervalMint should return available GREEN for minting"""
    user = boa.env.generate_address()
    mint_amount = 10_000 * SIX_DECIMALS

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Initially should be full amount (100k GREEN)
    avail_before = endaoment_psm.getAvailIntervalMint()
    assert avail_before == 100_000 * EIGHTEEN_DECIMALS

    # Mint some GREEN
    charlie_token.mint(user, mint_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, mint_amount, sender=user)
    endaoment_psm.mintGreen(mint_amount, user, False, sender=user)

    # Available should decrease
    avail_after = endaoment_psm.getAvailIntervalMint()
    assert avail_after == (100_000 - 10_000) * EIGHTEEN_DECIMALS


def test_get_max_redeemable_green_amount_limited_by_usdc(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source, whale):
    """getMaxRedeemableGreenAmount should be limited by available USDC"""
    # Enable redemption
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Fund PSM with 10k USDC
    charlie_token.mint(endaoment_psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)

    # Max redeemable should be limited by USDC (10k GREEN)
    # Don't pass user to get theoretical max
    max_redeemable = endaoment_psm.getMaxRedeemableGreenAmount(ZERO_ADDRESS, False)
    assert max_redeemable == 10_000 * EIGHTEEN_DECIMALS


def test_get_max_redeemable_green_amount_limited_by_interval(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source, whale):
    """getMaxRedeemableGreenAmount should be limited by interval when USDC is plentiful"""
    # Enable redemption
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Fund PSM with 200k USDC (more than interval limit)
    charlie_token.mint(endaoment_psm.address, 200_000 * SIX_DECIMALS, sender=governance.address)

    # Max redeemable should be limited by interval (100k GREEN default)
    # Don't pass user to get theoretical max
    max_redeemable = endaoment_psm.getMaxRedeemableGreenAmount(ZERO_ADDRESS, False)
    assert max_redeemable == 100_000 * EIGHTEEN_DECIMALS


def test_get_max_redeemable_green_amount_considers_user_balance(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source, whale):
    """getMaxRedeemableGreenAmount should be limited by user's GREEN balance when user is provided"""
    user = boa.env.generate_address()

    # Enable redemption
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    charlie_token.mint(endaoment_psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)

    # User with no GREEN should get 0 when user address is provided
    max_redeemable = endaoment_psm.getMaxRedeemableGreenAmount(user, False)
    assert max_redeemable == 0

    # Give user some GREEN (less than available)
    green_token.transfer(user, 1_000 * EIGHTEEN_DECIMALS, sender=whale)

    # Now user should get amount limited by their GREEN balance
    max_redeemable = endaoment_psm.getMaxRedeemableGreenAmount(user, False)
    assert max_redeemable == 1_000 * EIGHTEEN_DECIMALS


def test_get_avail_interval_redemptions(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source, whale):
    """getAvailIntervalRedemptions should return available GREEN for redemption"""
    user = boa.env.generate_address()
    redeem_amount = 5_000 * EIGHTEEN_DECIMALS

    # Enable redemption
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 100_000 * SIX_DECIMALS, sender=governance.address)

    # Initially should be full amount (100k GREEN)
    avail_before = endaoment_psm.getAvailIntervalRedemptions()
    assert avail_before == 100_000 * EIGHTEEN_DECIMALS

    # Give user GREEN and redeem
    green_token.transfer(user, redeem_amount, sender=whale)
    green_token.approve(endaoment_psm.address, redeem_amount, sender=user)
    endaoment_psm.redeemGreen(redeem_amount, user, False, sender=user)

    # Available should decrease
    avail_after = endaoment_psm.getAvailIntervalRedemptions()
    assert avail_after == (100_000 - 5_000) * EIGHTEEN_DECIMALS


def test_get_available_usdc_includes_balance(endaoment_psm, charlie_token, governance):
    """getAvailableUsdc should include PSM's USDC balance"""
    # Fund PSM with USDC
    usdc_amount = 50_000 * SIX_DECIMALS
    charlie_token.mint(endaoment_psm.address, usdc_amount, sender=governance.address)

    # Available USDC should equal balance (no yield position)
    available = endaoment_psm.getAvailableUsdc()
    assert available == usdc_amount


def test_get_underlying_yield_amount_zero_when_no_position(endaoment_psm):
    """getUnderlyingYieldAmount should return 0 when no yield position is set"""
    underlying = endaoment_psm.getUnderlyingYieldAmount()
    assert underlying == 0


################################################
# Underscore Vault Tests for getMaxRedeemableGreenAmount #
################################################


def test_get_max_redeemable_green_amount_vault_bypasses_interval_limits(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """getMaxRedeemableGreenAmount with _isUnderscoreVault=True should bypass interval limits"""
    # Enable redemption
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Fund PSM with 200k USDC (more than 100k interval limit)
    charlie_token.mint(endaoment_psm.address, 200_000 * SIX_DECIMALS, sender=governance.address)

    # Non-Underscore vault should be limited by interval (100k GREEN)
    max_redeemable_regular = endaoment_psm.getMaxRedeemableGreenAmount(ZERO_ADDRESS, False)
    assert max_redeemable_regular == 100_000 * EIGHTEEN_DECIMALS

    # Underscore vault should bypass interval limit and get full USDC-based amount (200k GREEN)
    max_redeemable_vault = endaoment_psm.getMaxRedeemableGreenAmount(ZERO_ADDRESS, True)
    assert max_redeemable_vault == 200_000 * EIGHTEEN_DECIMALS


def test_get_max_redeemable_green_amount_vault_bypasses_fees(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """getMaxRedeemableGreenAmount with _isUnderscoreVault=True should bypass fee adjustments"""
    # Enable redemption with 5% fee
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setRedeemFee(500, sender=switchboard_charlie.address)  # 5%

    # Fund PSM with 50k USDC (less than interval limit, so USDC becomes constraining)
    charlie_token.mint(endaoment_psm.address, 50_000 * SIX_DECIMALS, sender=governance.address)

    # Non-vault: with 5% fee and 50k USDC available
    # maxGreenFromUsdc = 50k * 100 / (100 - 5) = 50k * 100/95 ≈ 52,631 GREEN
    # min(100k interval, 52,631) = 52,631 GREEN
    max_redeemable_regular = endaoment_psm.getMaxRedeemableGreenAmount(ZERO_ADDRESS, False)
    expected_with_fee = 50_000 * EIGHTEEN_DECIMALS * 100_00 // (100_00 - 500)
    assert max_redeemable_regular == expected_with_fee

    # Vault: no fee adjustment, returns 50k GREEN (1:1 with USDC)
    max_redeemable_vault = endaoment_psm.getMaxRedeemableGreenAmount(ZERO_ADDRESS, True)
    assert max_redeemable_vault == 50_000 * EIGHTEEN_DECIMALS


def test_get_max_redeemable_green_amount_vault_respects_usdc_availability(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """getMaxRedeemableGreenAmount with _isUnderscoreVault=True should still respect USDC availability"""
    # Enable redemption
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Fund PSM with only 10k USDC (less than interval limit)
    charlie_token.mint(endaoment_psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)

    # Even as vault, should be limited by USDC availability (10k GREEN)
    max_redeemable_vault = endaoment_psm.getMaxRedeemableGreenAmount(ZERO_ADDRESS, True)
    assert max_redeemable_vault == 10_000 * EIGHTEEN_DECIMALS


def test_get_max_redeemable_green_amount_vault_with_user_balance(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source, whale):
    """getMaxRedeemableGreenAmount with _isUnderscoreVault=True and user address should respect user balance"""
    user = boa.env.generate_address()

    # Enable redemption
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Fund PSM with 100k USDC
    charlie_token.mint(endaoment_psm.address, 100_000 * SIX_DECIMALS, sender=governance.address)

    # Give user only 5k GREEN
    green_token.transfer(user, 5_000 * EIGHTEEN_DECIMALS, sender=whale)

    # Even as vault, should be limited by user's GREEN balance (5k GREEN)
    max_redeemable_vault = endaoment_psm.getMaxRedeemableGreenAmount(user, True)
    assert max_redeemable_vault == 5_000 * EIGHTEEN_DECIMALS


################################################
# Underscore Vault Tests for getMaxUsdcAmountForMint #
################################################


def test_get_max_usdc_amount_for_mint_vault_bypasses_interval_limits(endaoment_psm, charlie_token, switchboard_charlie, mock_price_source):
    """getMaxUsdcAmountForMint with _isUnderscoreVault=True should bypass interval limits"""
    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Non-Underscore vault should be limited by interval (100k GREEN = 100k USDC)
    max_usdc_regular = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, False)
    assert max_usdc_regular == 100_000 * SIX_DECIMALS

    # Underscore vault should bypass interval limit and return MAX_UINT256 (unlimited)
    max_usdc_vault = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, True)
    assert max_usdc_vault == MAX_UINT256


def test_get_max_usdc_amount_for_mint_vault_bypasses_fees(endaoment_psm, charlie_token, switchboard_charlie, mock_price_source):
    """getMaxUsdcAmountForMint with _isUnderscoreVault=True should bypass fee adjustments"""
    # Enable minting with 5% fee
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMintFee(500, sender=switchboard_charlie.address)  # 5%

    # Non-vault: with 5% fee, to mint 100k GREEN need ~105,263 USDC
    max_usdc_regular = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, False)
    expected_with_fee = 100_000 * SIX_DECIMALS * 100_00 // (100_00 - 500)
    assert max_usdc_regular == expected_with_fee

    # Vault: should return unlimited (MAX_UINT256), no fee adjustment
    max_usdc_vault = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, True)
    assert max_usdc_vault == MAX_UINT256


def test_get_max_usdc_amount_for_mint_vault_respects_user_balance(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """getMaxUsdcAmountForMint with _isUnderscoreVault=True and user address should respect user balance"""
    user = boa.env.generate_address()

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Give user only 50k USDC
    charlie_token.mint(user, 50_000 * SIX_DECIMALS, sender=governance.address)

    # Even as vault, should be limited by user's USDC balance (50k USDC)
    max_usdc_vault = endaoment_psm.getMaxUsdcAmountForMint(user, True)
    assert max_usdc_vault == 50_000 * SIX_DECIMALS


def test_get_max_usdc_amount_for_mint_vault_unlimited_when_no_user(endaoment_psm, charlie_token, switchboard_charlie, mock_price_source):
    """getMaxUsdcAmountForMint with _isUnderscoreVault=True and no user should return unlimited"""
    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Vault without user address should return MAX_UINT256 (truly unlimited)
    max_usdc_vault = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, True)
    assert max_usdc_vault == MAX_UINT256
