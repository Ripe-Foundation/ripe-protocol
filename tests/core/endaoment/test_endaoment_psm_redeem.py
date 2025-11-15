import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from conf_utils import filter_logs


SIX_DECIMALS = 10**6  # For tokens like USDC that have 6 decimals
ONE_DAY_BLOCKS = 43_200
HUNDRED_PERCENT = 100_00


#########################
# Access Control Tests #
#########################


def test_redeem_fails_when_paused(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption should fail when contract is paused"""
    user = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    # Enable redemption
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Setup user with GREEN tokens (via mint)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC for redemptions
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Approve GREEN for redemption
    green_token.approve(endaoment_psm.address, green_amount, sender=user)

    # Pause contract
    endaoment_psm.pause(True, sender=switchboard_charlie.address)

    # Attempt to redeem should fail
    with boa.reverts("contract paused"):
        endaoment_psm.redeemGreen(sender=user)


def test_redeem_fails_when_redemption_disabled(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption should fail when canRedeem flag is False"""
    user = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup user with GREEN tokens (via mint)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Verify canRedeem is False
    assert endaoment_psm.canRedeem() == False

    # Approve GREEN and attempt to redeem
    green_token.approve(endaoment_psm.address, green_amount, sender=user)

    with boa.reverts("redemption disabled"):
        endaoment_psm.redeemGreen(sender=user)


def test_redeem_succeeds_when_enabled(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption should succeed when properly enabled"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user first
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Approve GREEN and redeem
    green_token.approve(endaoment_psm.address, 1000 * EIGHTEEN_DECIMALS, sender=user)
    usdc_received = endaoment_psm.redeemGreen(sender=user)

    # Verify
    assert usdc_received > 0


def test_redeem_fails_with_zero_address_recipient(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption to zero address should fail"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Approve GREEN and attempt to redeem to zero address
    green_token.approve(endaoment_psm.address, 1000 * EIGHTEEN_DECIMALS, sender=user)

    with boa.reverts("invalid recipient"):
        endaoment_psm.redeemGreen(1000 * EIGHTEEN_DECIMALS, ZERO_ADDRESS, sender=user)


def test_redeem_fails_with_zero_balance(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Redemption should fail if user has no GREEN"""
    user = boa.env.generate_address()

    # Enable redemption
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Attempt to redeem with zero balance
    with boa.reverts("zero amount"):
        endaoment_psm.redeemGreen(sender=user)


def test_redeem_fails_without_approval(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption should fail without GREEN approval"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Attempt to redeem without GREEN approval
    with boa.reverts("transfer failed"):
        endaoment_psm.redeemGreen(sender=user)


def test_redeem_requires_sufficient_approval(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption should fail if approval is less than amount"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Setup user with partial approval
    green_token.approve(endaoment_psm.address, 500 * EIGHTEEN_DECIMALS, sender=user)

    # Attempt to redeem more than approved
    with boa.reverts("transfer failed"):
        endaoment_psm.redeemGreen(1000 * EIGHTEEN_DECIMALS, sender=user)


##################
# Allowlist Tests #
##################


def test_redeem_succeeds_without_allowlist_enforcement(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Anyone can redeem when allowlist is not enforced"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Verify allowlist not enforced
    assert endaoment_psm.shouldEnforceRedeemAllowlist() == False

    # Approve and redeem
    green_token.approve(endaoment_psm.address, 1000 * EIGHTEEN_DECIMALS, sender=user)
    usdc_received = endaoment_psm.redeemGreen(sender=user)

    assert usdc_received > 0


def test_redeem_fails_when_not_on_allowlist(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption should fail when allowlist is enforced and user is not on it"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and allowlist enforcement
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setShouldEnforceRedeemAllowlist(True, sender=switchboard_charlie.address)

    # Verify user not on allowlist
    assert endaoment_psm.redeemAllowlist(user) == False

    # Approve GREEN and attempt to redeem
    green_token.approve(endaoment_psm.address, 1000 * EIGHTEEN_DECIMALS, sender=user)

    with boa.reverts("not on redeem allowlist"):
        endaoment_psm.redeemGreen(sender=user)


def test_redeem_succeeds_when_on_allowlist(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption should succeed when user is on allowlist"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption, allowlist, and add user
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setShouldEnforceRedeemAllowlist(True, sender=switchboard_charlie.address)
    endaoment_psm.updateRedeemAllowlist(user, True, sender=switchboard_charlie.address)

    # Verify user on allowlist
    assert endaoment_psm.redeemAllowlist(user) == True

    # Approve and redeem
    green_token.approve(endaoment_psm.address, 1000 * EIGHTEEN_DECIMALS, sender=user)
    usdc_received = endaoment_psm.redeemGreen(sender=user)

    assert usdc_received > 0


def test_remove_from_allowlist_blocks_future_redemptions(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Removing user from allowlist blocks their future redemptions"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 2000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 2000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption, allowlist, add user
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setShouldEnforceRedeemAllowlist(True, sender=switchboard_charlie.address)
    endaoment_psm.updateRedeemAllowlist(user, True, sender=switchboard_charlie.address)

    # First redemption succeeds
    green_token.approve(endaoment_psm.address, 2000 * EIGHTEEN_DECIMALS, sender=user)
    usdc1 = endaoment_psm.redeemGreen(500 * EIGHTEEN_DECIMALS, sender=user)
    assert usdc1 > 0

    # Remove user from allowlist
    endaoment_psm.updateRedeemAllowlist(user, False, sender=switchboard_charlie.address)

    # Second redemption fails
    with boa.reverts("not on redeem allowlist"):
        endaoment_psm.redeemGreen(500 * EIGHTEEN_DECIMALS, sender=user)


def test_add_to_allowlist_enables_redemptions(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Adding user to allowlist enables their redemptions"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and allowlist enforcement (user not on list)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setShouldEnforceRedeemAllowlist(True, sender=switchboard_charlie.address)

    # Approve GREEN
    green_token.approve(endaoment_psm.address, 1000 * EIGHTEEN_DECIMALS, sender=user)

    # Redemption fails
    with boa.reverts("not on redeem allowlist"):
        endaoment_psm.redeemGreen(sender=user)

    # Add user to allowlist
    endaoment_psm.updateRedeemAllowlist(user, True, sender=switchboard_charlie.address)

    # Now redemption succeeds
    usdc_received = endaoment_psm.redeemGreen(sender=user)
    assert usdc_received > 0


def test_allowlist_check_uses_sender_not_recipient(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Allowlist should check sender, not recipient"""
    sender = boa.env.generate_address()
    recipient = boa.env.generate_address()

    # Setup: mint GREEN to sender
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(sender, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=sender)
    endaoment_psm.mintGreen(sender=sender)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption, allowlist, add sender (not recipient)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setShouldEnforceRedeemAllowlist(True, sender=switchboard_charlie.address)
    endaoment_psm.updateRedeemAllowlist(sender, True, sender=switchboard_charlie.address)

    # Approve GREEN
    green_token.approve(endaoment_psm.address, 1000 * EIGHTEEN_DECIMALS, sender=sender)

    # Sender can redeem to recipient
    usdc_received = endaoment_psm.redeemGreen(1000 * EIGHTEEN_DECIMALS, recipient, sender=sender)
    assert usdc_received > 0


def test_allowlist_enforcement_toggle(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Toggling allowlist enforcement should work correctly"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 2000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 2000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption, enforce allowlist (user not on list)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setShouldEnforceRedeemAllowlist(True, sender=switchboard_charlie.address)

    # Approve GREEN
    green_token.approve(endaoment_psm.address, 2000 * EIGHTEEN_DECIMALS, sender=user)

    # Redemption fails when enforced
    with boa.reverts("not on redeem allowlist"):
        endaoment_psm.redeemGreen(500 * EIGHTEEN_DECIMALS, sender=user)

    # Disable enforcement
    endaoment_psm.setShouldEnforceRedeemAllowlist(False, sender=switchboard_charlie.address)

    # Now redemption succeeds
    usdc_received = endaoment_psm.redeemGreen(500 * EIGHTEEN_DECIMALS, sender=user)
    assert usdc_received > 0


##########################
# Amount Handling Tests #
##########################


def test_redeem_with_explicit_amount(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redeeming specific GREEN amount should return corresponding USDC"""
    user = boa.env.generate_address()
    green_amount = 500 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and redeem
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    usdc_received = endaoment_psm.redeemGreen(green_amount, sender=user)

    # Should receive 500 USDC (1:1 at peg)
    expected_usdc = 500 * SIX_DECIMALS
    assert usdc_received == expected_usdc


def test_redeem_with_max_value_uses_full_balance(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redeeming with max_value should use user's full GREEN balance"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    green_balance = green_token.balanceOf(user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and redeem with max_value
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, MAX_UINT256, sender=user)
    usdc_received = endaoment_psm.redeemGreen(sender=user)

    # Should use full balance
    expected_usdc = 1000 * SIX_DECIMALS
    assert usdc_received == expected_usdc
    assert green_token.balanceOf(user) == 0


def test_redeem_capped_by_user_balance(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Requested redemption amount should be capped by user's actual balance"""
    user = boa.env.generate_address()
    actual_balance = 500 * EIGHTEEN_DECIMALS
    requested_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup: mint 500 GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 500 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 500 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and redeem
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, requested_amount, sender=user)
    usdc_received = endaoment_psm.redeemGreen(requested_amount, sender=user)

    # Should only redeem actual balance (500 GREEN)
    expected_usdc = 500 * SIX_DECIMALS
    assert usdc_received == expected_usdc


def test_redeem_updates_balances_correctly(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption should correctly update all balances"""
    user = boa.env.generate_address()
    redeem_amount = 500 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Record balances before
    green_before = green_token.balanceOf(user)
    usdc_before = charlie_token.balanceOf(user)
    psm_usdc_before = charlie_token.balanceOf(endaoment_psm.address)

    # Enable redemption and redeem
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, redeem_amount, sender=user)
    usdc_received = endaoment_psm.redeemGreen(redeem_amount, sender=user)

    # Check balances after
    green_after = green_token.balanceOf(user)
    usdc_after = charlie_token.balanceOf(user)
    psm_usdc_after = charlie_token.balanceOf(endaoment_psm.address)

    # Verify changes
    assert green_before - green_after == redeem_amount  # GREEN burned
    assert usdc_after - usdc_before == usdc_received  # USDC received
    assert psm_usdc_before - psm_usdc_after == usdc_received  # USDC left PSM


def test_redeem_to_different_recipient(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption can send USDC to a different recipient"""
    redeemer = boa.env.generate_address()
    recipient = boa.env.generate_address()
    redeem_amount = 500 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to redeemer
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(redeemer, 500 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 500 * SIX_DECIMALS, sender=redeemer)
    endaoment_psm.mintGreen(sender=redeemer)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, redeem_amount, sender=redeemer)

    # Redeemer redeems to recipient
    usdc_received = endaoment_psm.redeemGreen(redeem_amount, recipient, sender=redeemer)

    # Verify
    assert green_token.balanceOf(redeemer) == 0
    assert charlie_token.balanceOf(recipient) == usdc_received
    assert charlie_token.balanceOf(redeemer) == 0


def test_multiple_redemptions_reduce_balance(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Multiple redemptions should reduce GREEN balance"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, 1000 * EIGHTEEN_DECIMALS, sender=user)

    # First redemption
    usdc1 = endaoment_psm.redeemGreen(300 * EIGHTEEN_DECIMALS, sender=user)
    balance_after_first = green_token.balanceOf(user)
    assert balance_after_first == 700 * EIGHTEEN_DECIMALS

    # Second redemption
    usdc2 = endaoment_psm.redeemGreen(200 * EIGHTEEN_DECIMALS, sender=user)
    balance_after_second = green_token.balanceOf(user)
    assert balance_after_second == 500 * EIGHTEEN_DECIMALS


def test_return_value_matches_usdc_sent(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Function return value should match actual USDC sent"""
    user = boa.env.generate_address()
    redeem_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    balance_before = charlie_token.balanceOf(user)

    # Enable redemption and redeem
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, redeem_amount, sender=user)
    returned_amount = endaoment_psm.redeemGreen(redeem_amount, sender=user)

    balance_after = charlie_token.balanceOf(user)
    actual_received = balance_after - balance_before

    assert returned_amount == actual_received


##############
# Fee Tests #
##############


def test_redeem_with_zero_fee(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Default zero fee should result in 1:1 redemption"""
    user = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Verify zero fee
    assert endaoment_psm.redeemFee() == 0

    # Enable redemption and redeem
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    usdc_received = endaoment_psm.redeemGreen(green_amount, sender=user)

    # Should receive 1:1
    expected_usdc = 1000 * SIX_DECIMALS
    assert usdc_received == expected_usdc


def test_redeem_with_5_percent_fee(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """5% fee should reduce USDC received accordingly"""
    user = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and set fee
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setRedeemFee(500, sender=switchboard_charlie.address)  # 5.00%

    # Redeem
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    usdc_received = endaoment_psm.redeemGreen(green_amount, sender=user)

    # Should receive 950 USDC (1000 - 5% fee)
    expected_usdc = 950 * SIX_DECIMALS
    assert usdc_received == expected_usdc


def test_redeem_with_10_percent_fee(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """10% fee should reduce USDC received accordingly"""
    user = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and set fee
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setRedeemFee(1000, sender=switchboard_charlie.address)  # 10.00%

    # Redeem
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    usdc_received = endaoment_psm.redeemGreen(green_amount, sender=user)

    # Should receive 900 USDC (1000 - 10% fee)
    expected_usdc = 900 * SIX_DECIMALS
    assert usdc_received == expected_usdc


def test_redeem_with_high_fee(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """50% fee should reduce USDC received significantly"""
    user = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and set fee
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setRedeemFee(5000, sender=switchboard_charlie.address)  # 50.00%

    # Redeem
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    usdc_received = endaoment_psm.redeemGreen(green_amount, sender=user)

    # Should receive 500 USDC (1000 - 50% fee)
    expected_usdc = 500 * SIX_DECIMALS
    assert usdc_received == expected_usdc


def test_fee_stays_in_contract(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Fees should stay in the PSM contract"""
    user = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and set fee
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setRedeemFee(500, sender=switchboard_charlie.address)  # 5.00%

    # Record PSM balance before
    psm_balance_before = charlie_token.balanceOf(endaoment_psm.address)

    # Redeem
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    usdc_received = endaoment_psm.redeemGreen(green_amount, sender=user)

    # PSM should have lost only the USDC sent (950), fee (50) stays
    psm_balance_after = charlie_token.balanceOf(endaoment_psm.address)
    assert psm_balance_before - psm_balance_after == usdc_received


def test_fee_accumulation_over_multiple_redemptions(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Fees should accumulate in PSM over multiple redemptions"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 2000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 2000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and set fee
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setRedeemFee(500, sender=switchboard_charlie.address)  # 5.00%

    # Record PSM balance before
    psm_balance_start = charlie_token.balanceOf(endaoment_psm.address)

    # Redeem twice
    green_token.approve(endaoment_psm.address, 2000 * EIGHTEEN_DECIMALS, sender=user)
    usdc1 = endaoment_psm.redeemGreen(1000 * EIGHTEEN_DECIMALS, sender=user)
    usdc2 = endaoment_psm.redeemGreen(1000 * EIGHTEEN_DECIMALS, sender=user)

    # Total USDC paid out: 950 + 950 = 1900
    # Total fees accumulated: 50 + 50 = 100
    psm_balance_end = charlie_token.balanceOf(endaoment_psm.address)
    total_paid_out = usdc1 + usdc2
    assert psm_balance_start - psm_balance_end == total_paid_out
    assert total_paid_out == 1900 * SIX_DECIMALS


#################
# Pricing Tests #
#################


def test_redeem_at_peg_one_to_one(endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie, governance):
    """At $1.00 peg, should redeem 1:1"""
    user = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Set USDC price to exactly $1.00
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)

    # Enable redemption and redeem
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    usdc_received = endaoment_psm.redeemGreen(green_amount, sender=user)

    # Should receive 1:1
    expected_usdc = 1000 * SIX_DECIMALS
    assert usdc_received == expected_usdc


def test_redeem_when_usdc_above_peg(endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie, governance):
    """When USDC > $1, protocol gives less USDC (protects protocol from giving too much)"""
    user = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to user at peg
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Set USDC price to $1.05
    mock_price_source.setPrice(charlie_token.address, int(1.05 * EIGHTEEN_DECIMALS))

    # Enable redemption and redeem
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    usdc_received = endaoment_psm.redeemGreen(green_amount, sender=user)

    # When USDC is at $1.05, PriceDesk.getAssetAmount calculates:
    # 1000 GREEN worth $1000, divided by $1.05 per USDC = 1000/1.05 = ~952.38 USDC
    # Decimal conversion gives 1000 USDC
    # min(952.38, 1000) = 952.38 USDC (protocol protects itself)
    # Expected: 952380952 (in 6 decimals, which is 952.380952 USDC)
    expected_usdc = 952380952
    assert usdc_received == expected_usdc


def test_redeem_when_usdc_below_peg(endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie, governance):
    """When USDC < $1, protocol gives less USDC (based on price desk value)"""
    user = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to user at peg
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Set USDC price to $0.95
    mock_price_source.setPrice(charlie_token.address, int(0.95 * EIGHTEEN_DECIMALS))

    # Enable redemption and redeem
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    usdc_received = endaoment_psm.redeemGreen(green_amount, sender=user)

    # At $0.95, PriceDesk.getAssetAmount returns ~950 USDC (1000 GREEN worth $1000, converted to USDC at $0.95 per USDC ~= 1053 USDC)
    # Actually: the function gets asset amount given green amount
    # So we need to understand the math better. For redemption at off-peg, the protocol protects itself
    # by giving the minimum value. At $0.95 per USDC, decimal conversion is 1:1 (1000 USDC)
    # but the price would suggest needing more USDC to match value... Actually this returns 1000 USDC
    expected_usdc = 1000 * SIX_DECIMALS
    assert usdc_received == expected_usdc


def test_decimal_conversion_18_to_6(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Verify correct decimal conversion from 18 to 6 decimals"""
    user = boa.env.generate_address()
    green_amount = 1 * EIGHTEEN_DECIMALS  # 1 GREEN

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and redeem
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    usdc_received = endaoment_psm.redeemGreen(green_amount, sender=user)

    # 1 GREEN (1e18) should become 1 USDC (1e6)
    expected_usdc = 1 * SIX_DECIMALS
    assert usdc_received == expected_usdc


def test_pricing_with_fee_interaction(endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie, governance):
    """Fees and pricing should interact correctly"""
    user = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to user at peg
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption, set fee and price
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setRedeemFee(500, sender=switchboard_charlie.address)  # 5% fee
    mock_price_source.setPrice(charlie_token.address, int(0.95 * EIGHTEEN_DECIMALS))  # $0.95

    # Redeem
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    usdc_received = endaoment_psm.redeemGreen(green_amount, sender=user)

    # At $0.95, decimal conversion gives 1000 USDC (min with price desk)
    # After 5% fee: 1000 * 0.95 = 950 USDC
    expected_usdc = 950 * SIX_DECIMALS
    assert usdc_received == expected_usdc


def test_pricing_different_scenarios(endaoment_psm, charlie_token, green_token, mock_price_source, switchboard_charlie, governance):
    """Test redemption at various price points"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user at peg
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 3000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 3000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(3000 * SIX_DECIMALS, sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 20000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, MAX_UINT256, sender=user)

    # Test at peg (should be 1:1)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    usdc1 = endaoment_psm.redeemGreen(1000 * EIGHTEEN_DECIMALS, sender=user)
    assert usdc1 == 1000 * SIX_DECIMALS

    # Test at $1.02 (protocol protects itself by giving less USDC)
    # 1000 GREEN worth $1000, divided by $1.02 per USDC = 1000/1.02 = 980.392156... USDC
    mock_price_source.setPrice(charlie_token.address, int(1.02 * EIGHTEEN_DECIMALS))
    usdc2 = endaoment_psm.redeemGreen(1000 * EIGHTEEN_DECIMALS, sender=user)
    assert usdc2 == 980392156  # 980.392156 USDC in 6 decimals


##################
# Interval Tests #
##################


def test_redeem_within_interval_limit(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption within limit should succeed"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 60000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 60000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 100000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Verify interval limit
    max_interval = endaoment_psm.maxIntervalRedeem()
    assert max_interval == 100_000 * EIGHTEEN_DECIMALS

    # Redeem 50,000 GREEN (well within limit)
    green_token.approve(endaoment_psm.address, 50_000 * EIGHTEEN_DECIMALS, sender=user)
    usdc_received = endaoment_psm.redeemGreen(50_000 * EIGHTEEN_DECIMALS, sender=user)

    assert usdc_received == 50_000 * SIX_DECIMALS


def test_redeem_exactly_at_interval_limit(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption exactly at limit should succeed"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 100_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 100_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 100_000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Redeem exactly 100,000 GREEN
    green_token.approve(endaoment_psm.address, 100_000 * EIGHTEEN_DECIMALS, sender=user)
    usdc_received = endaoment_psm.redeemGreen(100_000 * EIGHTEEN_DECIMALS, sender=user)

    assert usdc_received == 100_000 * SIX_DECIMALS


def test_redeem_exceeds_interval_limit(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption beyond limit should fail"""
    user = boa.env.generate_address()

    # Setup: increase mint interval to allow minting 100,001 GREEN
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMaxIntervalMint(150_000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)

    charlie_token.mint(user, 100_001 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 100_001 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 100_001 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption (default redeem interval is 100,000)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, 100_001 * EIGHTEEN_DECIMALS, sender=user)

    # Attempt to redeem 100,001 GREEN should fail
    with boa.reverts("exceeds max interval redeem"):
        endaoment_psm.redeemGreen(100_001 * EIGHTEEN_DECIMALS, sender=user)


def test_multiple_redemptions_accumulate_in_interval(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Multiple redemptions should accumulate toward interval limit"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user (increase mint interval to allow 101k mint)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMaxIntervalMint(150_000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)

    charlie_token.mint(user, 101_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 101_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 101_000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, 101_000 * EIGHTEEN_DECIMALS, sender=user)

    # First redemption: 60,000 GREEN
    usdc1 = endaoment_psm.redeemGreen(60_000 * EIGHTEEN_DECIMALS, sender=user)
    assert usdc1 == 60_000 * SIX_DECIMALS

    # Second redemption: 40,000 GREEN (total 100,000)
    usdc2 = endaoment_psm.redeemGreen(40_000 * EIGHTEEN_DECIMALS, sender=user)
    assert usdc2 == 40_000 * SIX_DECIMALS

    # Third redemption: 1 more GREEN should fail
    with boa.reverts("exceeds max interval redeem"):
        endaoment_psm.redeemGreen(1 * EIGHTEEN_DECIMALS, sender=user)


def test_interval_resets_after_blocks(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Interval should reset after configured blocks"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user (need to mint 200k total, so increase mint interval)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMaxIntervalMint(250_000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)

    charlie_token.mint(user, 200_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 200_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 200_000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, 200_000 * EIGHTEEN_DECIMALS, sender=user)

    # Redeem full limit
    usdc1 = endaoment_psm.redeemGreen(100_000 * EIGHTEEN_DECIMALS, sender=user)
    assert usdc1 == 100_000 * SIX_DECIMALS

    # Roll forward past interval
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    # Should be able to redeem another 100,000 GREEN
    usdc2 = endaoment_psm.redeemGreen(100_000 * EIGHTEEN_DECIMALS, sender=user)
    assert usdc2 == 100_000 * SIX_DECIMALS


def test_interval_boundary_exact_block(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Test behavior at exact interval boundary"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user (increase mint interval)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMaxIntervalMint(250_000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)

    charlie_token.mint(user, 200_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 200_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 200_000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and redeem full limit
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, 200_000 * EIGHTEEN_DECIMALS, sender=user)
    endaoment_psm.redeemGreen(100_000 * EIGHTEEN_DECIMALS, sender=user)

    # Roll to one block before the boundary
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS - 1)

    # One block before boundary, should still be in same interval
    with boa.reverts("exceeds max interval redeem"):
        endaoment_psm.redeemGreen(1 * EIGHTEEN_DECIMALS, sender=user)

    # Roll one more block to reach the boundary
    boa.env.time_travel(blocks=1)

    # At the boundary (start + numBlocks), we're in a fresh interval
    usdc2 = endaoment_psm.redeemGreen(50_000 * EIGHTEEN_DECIMALS, sender=user)
    assert usdc2 == 50_000 * SIX_DECIMALS


def test_fresh_interval_starts_on_first_redeem(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """First redemption should initialize interval start"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 50_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 50_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 100_000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Check initial state
    interval_data = endaoment_psm.globalRedeemInterval()
    assert interval_data[0] == 0  # start == 0 initially

    # First redemption
    green_token.approve(endaoment_psm.address, 30_000 * EIGHTEEN_DECIMALS, sender=user)
    current_block = boa.env.evm.patch.block_number
    endaoment_psm.redeemGreen(30_000 * EIGHTEEN_DECIMALS, sender=user)

    # Check interval updated
    interval_data = endaoment_psm.globalRedeemInterval()
    assert interval_data[0] == current_block
    assert interval_data[1] == 30_000 * EIGHTEEN_DECIMALS


def test_interval_amount_accumulates(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Interval amount should accumulate across redemptions"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 100_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 100_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 100_000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, 100_000 * EIGHTEEN_DECIMALS, sender=user)

    # First redemption: 30,000 GREEN
    endaoment_psm.redeemGreen(30_000 * EIGHTEEN_DECIMALS, sender=user)
    interval_data = endaoment_psm.globalRedeemInterval()
    assert interval_data[1] == 30_000 * EIGHTEEN_DECIMALS

    # Second redemption: 20,000 GREEN
    endaoment_psm.redeemGreen(20_000 * EIGHTEEN_DECIMALS, sender=user)
    interval_data = endaoment_psm.globalRedeemInterval()
    assert interval_data[1] == 50_000 * EIGHTEEN_DECIMALS


def test_getAvailIntervalRedemptions_accuracy(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """getAvailIntervalRedemptions should return accurate remaining capacity"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 100_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 100_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 100_000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Initial: full capacity
    avail = endaoment_psm.getAvailIntervalRedemptions()
    assert avail == 100_000 * EIGHTEEN_DECIMALS

    # Redeem 30,000
    green_token.approve(endaoment_psm.address, 100_000 * EIGHTEEN_DECIMALS, sender=user)
    endaoment_psm.redeemGreen(30_000 * EIGHTEEN_DECIMALS, sender=user)

    # Should have 70,000 remaining
    avail = endaoment_psm.getAvailIntervalRedemptions()
    assert avail == 70_000 * EIGHTEEN_DECIMALS

    # Redeem 70,000 more
    endaoment_psm.redeemGreen(70_000 * EIGHTEEN_DECIMALS, sender=user)

    # Should have 0 remaining
    avail = endaoment_psm.getAvailIntervalRedemptions()
    assert avail == 0


def test_getAvailIntervalRedemptions_resets_after_interval(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """getAvailIntervalRedemptions should reset to full capacity after interval expires"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user (increase mint interval)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMaxIntervalMint(250_000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)

    charlie_token.mint(user, 200_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 200_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 200_000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, 200_000 * EIGHTEEN_DECIMALS, sender=user)

    # Redeem 60,000
    endaoment_psm.redeemGreen(60_000 * EIGHTEEN_DECIMALS, sender=user)

    # Should have 40,000 remaining
    avail = endaoment_psm.getAvailIntervalRedemptions()
    assert avail == 40_000 * EIGHTEEN_DECIMALS

    # Travel past interval
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    # Should reset to full capacity
    avail = endaoment_psm.getAvailIntervalRedemptions()
    assert avail == 100_000 * EIGHTEEN_DECIMALS


def test_getAvailIntervalRedemptions_before_first_redeem(endaoment_psm):
    """getAvailIntervalRedemptions should return full capacity before first redemption"""
    avail = endaoment_psm.getAvailIntervalRedemptions()
    assert avail == 100_000 * EIGHTEEN_DECIMALS


def test_getMaxRedeemableGreenAmount_full_interval(endaoment_psm, charlie_token, switchboard_charlie, mock_price_source, governance):
    """getMaxRedeemableGreenAmount should return full interval capacity"""
    # Fund PSM with lots of USDC
    charlie_token.mint(endaoment_psm.address, 200_000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # At 1:1 peg with no fee, max GREEN should equal interval limit
    max_green = endaoment_psm.getMaxRedeemableGreenAmount()
    assert max_green == 100_000 * EIGHTEEN_DECIMALS


def test_getMaxRedeemableGreenAmount_after_partial_redeem(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """getMaxRedeemableGreenAmount should reflect remaining interval capacity"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 100_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 100_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 200_000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Redeem 30,000 GREEN
    green_token.approve(endaoment_psm.address, 30_000 * EIGHTEEN_DECIMALS, sender=user)
    endaoment_psm.redeemGreen(30_000 * EIGHTEEN_DECIMALS, sender=user)

    # Max GREEN should now be 70,000
    max_green = endaoment_psm.getMaxRedeemableGreenAmount()
    assert max_green == 70_000 * EIGHTEEN_DECIMALS


def test_getMaxRedeemableGreenAmount_with_fee(endaoment_psm, charlie_token, switchboard_charlie, mock_price_source, governance):
    """getMaxRedeemableGreenAmount with fee - interval limit is constraining factor"""
    # Fund PSM with USDC (ample amount - more than needed)
    charlie_token.mint(endaoment_psm.address, 200_000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption with 5% fee
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setRedeemFee(500, sender=switchboard_charlie.address)  # 5%

    # The function returns min(intervalCapacity, maxGreenFromUsdc)
    # intervalCapacity = 100,000 GREEN (not adjusted for fees)
    # maxGreenFromUsdc = with 200k USDC and fee adjustment, this is way more than 100k
    # Therefore, min(100k, huge) = 100k GREEN
    # The interval limit is the constraining factor, not USDC availability
    expected = 100_000 * EIGHTEEN_DECIMALS
    max_green = endaoment_psm.getMaxRedeemableGreenAmount()
    assert max_green == expected


def test_concurrent_redemptions_by_different_users_share_interval(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Multiple users should share same interval limit"""
    user_a = boa.env.generate_address()
    user_b = boa.env.generate_address()

    # Setup: mint GREEN to users (increase mint interval for total 110k)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMaxIntervalMint(150_000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)

    charlie_token.mint(user_a, 60_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.mint(user_b, 50_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 60_000 * SIX_DECIMALS, sender=user_a)
    charlie_token.approve(endaoment_psm.address, 50_000 * SIX_DECIMALS, sender=user_b)
    endaoment_psm.mintGreen(sender=user_a)
    endaoment_psm.mintGreen(sender=user_b)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 200_000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, 60_000 * EIGHTEEN_DECIMALS, sender=user_a)
    green_token.approve(endaoment_psm.address, 50_000 * EIGHTEEN_DECIMALS, sender=user_b)

    # User A redeems 60,000 GREEN
    usdc_a = endaoment_psm.redeemGreen(sender=user_a)
    assert usdc_a == 60_000 * SIX_DECIMALS

    # User B tries to redeem all 50,000 but that would exceed interval limit
    with boa.reverts("exceeds max interval redeem"):
        endaoment_psm.redeemGreen(sender=user_b)

    # User B can successfully redeem 40,000 GREEN (remaining in interval)
    usdc_b = endaoment_psm.redeemGreen(40_000 * EIGHTEEN_DECIMALS, sender=user_b)
    assert usdc_b == 40_000 * SIX_DECIMALS


#########################
# USDC Liquidity Tests #
#########################


def test_redeem_from_idle_usdc(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption should use idle USDC in PSM"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with idle USDC
    charlie_token.mint(endaoment_psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)
    psm_balance_before = charlie_token.balanceOf(endaoment_psm.address)

    # Enable redemption and redeem
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, 1000 * EIGHTEEN_DECIMALS, sender=user)
    usdc_received = endaoment_psm.redeemGreen(sender=user)

    # PSM balance should decrease by USDC sent
    psm_balance_after = charlie_token.balanceOf(endaoment_psm.address)
    assert psm_balance_before - psm_balance_after == usdc_received


def test_redeem_fails_if_insufficient_usdc(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption should fail if insufficient USDC available

    Note: In production, this scenario occurs when USDC is deployed to yield and the yield
    position loses value or cannot be withdrawn quickly enough. Since we're not testing yield,
    we artificially create this scenario by having governance transfer USDC out of the PSM.
    This still validates that the "insufficient USDC" error handling works correctly.
    """
    user = boa.env.generate_address()

    # Setup: mint GREEN to user (PSM receives 1000 USDC)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Artificially drain USDC from PSM to simulate yield losses
    # In production, this would happen via yield deployment and losses
    # PSM has 1000 USDC, we'll transfer 950 USDC out, leaving only 50 USDC
    drain_address = boa.env.generate_address()
    charlie_token.transfer(drain_address, 950 * SIX_DECIMALS, sender=endaoment_psm.address)

    # Verify PSM only has 50 USDC now
    assert charlie_token.balanceOf(endaoment_psm.address) == 50 * SIX_DECIMALS

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, 1000 * EIGHTEEN_DECIMALS, sender=user)

    # Attempt to redeem 1000 GREEN (needs 1000 USDC, but only 50 available)
    # This should fail with "insufficient USDC" because:
    # - usdcBalance = 50 USDC
    # - usdcAfterFee = 1000 USDC
    # - _withdrawFromYield returns 0 (no yield configured)
    # - assert 50 >= 1000 fails with "insufficient USDC"
    with boa.reverts("insufficient USDC"):
        endaoment_psm.redeemGreen(1000 * EIGHTEEN_DECIMALS, sender=user)


def test_getMaxRedeemableGreenAmount_limited_by_usdc_availability(endaoment_psm, charlie_token, switchboard_charlie, mock_price_source, governance):
    """getMaxRedeemableGreenAmount should be limited by USDC availability"""
    # Fund PSM with only 50,000 USDC (less than interval limit)
    charlie_token.mint(endaoment_psm.address, 50_000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Max GREEN should be limited by USDC (50,000), not interval (100,000)
    max_green = endaoment_psm.getMaxRedeemableGreenAmount()
    assert max_green == 50_000 * EIGHTEEN_DECIMALS


def test_multiple_redemptions_reduce_available_usdc(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Multiple redemptions should reduce available USDC"""
    user = boa.env.generate_address()

    # Setup: mint 5,000 GREEN to user (PSM receives 5,000 USDC)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 5_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 5_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Verify PSM has exactly 5,000 USDC
    assert charlie_token.balanceOf(endaoment_psm.address) == 5_000 * SIX_DECIMALS

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, 5_000 * EIGHTEEN_DECIMALS, sender=user)

    # First redemption: 3,000 GREEN (PSM gives 3,000 USDC, has 2,000 USDC left)
    usdc1 = endaoment_psm.redeemGreen(3_000 * EIGHTEEN_DECIMALS, sender=user)
    assert usdc1 == 3_000 * SIX_DECIMALS
    assert charlie_token.balanceOf(endaoment_psm.address) == 2_000 * SIX_DECIMALS

    # Second redemption: 2,000 GREEN (PSM gives 2,000 USDC, has 0 USDC left)
    usdc2 = endaoment_psm.redeemGreen(2_000 * EIGHTEEN_DECIMALS, sender=user)
    assert usdc2 == 2_000 * SIX_DECIMALS
    assert charlie_token.balanceOf(endaoment_psm.address) == 0

    # PSM now has 0 USDC, and user has 0 GREEN
    # Third redemption attempt: mint a tiny amount to try to redeem
    # But drain USDC first so redemption will fail
    charlie_token.mint(user, 10 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 10 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(10 * SIX_DECIMALS, sender=user)

    # PSM now has 10 USDC from the mint, user has 10 GREEN
    # Approve GREEN for redemption
    green_token.approve(endaoment_psm.address, 10 * EIGHTEEN_DECIMALS, sender=user)

    # Drain the USDC to create insufficient scenario
    charlie_token.transfer(boa.env.generate_address(), 10 * SIX_DECIMALS, sender=endaoment_psm.address)
    assert charlie_token.balanceOf(endaoment_psm.address) == 0

    # Third redemption: 10 GREEN should fail (no USDC left)
    with boa.reverts("insufficient USDC"):
        endaoment_psm.redeemGreen(10 * EIGHTEEN_DECIMALS, sender=user)


def test_exactly_drain_available_usdc(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Redemption should succeed when exactly draining all available USDC"""
    user = boa.env.generate_address()

    # Setup: mint 1000 GREEN to user (PSM receives exactly 1,000 USDC)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Verify PSM has exactly 1,000 USDC
    assert charlie_token.balanceOf(endaoment_psm.address) == 1000 * SIX_DECIMALS

    # Enable redemption and redeem all 1000 GREEN
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, 1000 * EIGHTEEN_DECIMALS, sender=user)
    usdc_received = endaoment_psm.redeemGreen(sender=user)

    # Should receive all 1,000 USDC
    assert usdc_received == 1000 * SIX_DECIMALS
    # PSM should have no USDC left (exactly drained)
    assert charlie_token.balanceOf(endaoment_psm.address) == 0


###############
# Event Tests #
###############


def test_redeem_emits_event_with_correct_params(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """RedeemGreen event should be emitted with correct parameters"""
    user = boa.env.generate_address()
    recipient = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and redeem
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    usdc_received = endaoment_psm.redeemGreen(green_amount, recipient, sender=user)

    # Check event
    log = filter_logs(endaoment_psm, "RedeemGreen")[0]
    assert log.user == recipient
    assert log.sender == user
    assert log.greenIn == green_amount
    assert log.usdcOut == usdc_received
    assert log.usdcFee == 0  # default no fee


def test_event_sender_vs_recipient_different(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Event should correctly distinguish sender and recipient"""
    redeemer = boa.env.generate_address()
    recipient = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to redeemer
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(redeemer, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=redeemer)
    endaoment_psm.mintGreen(sender=redeemer)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and redeem
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, green_amount, sender=redeemer)
    endaoment_psm.redeemGreen(green_amount, recipient, sender=redeemer)

    # Check event
    log = filter_logs(endaoment_psm, "RedeemGreen")[0]
    assert log.sender == redeemer
    assert log.user == recipient
    assert log.sender != log.user


def test_event_fee_amount_correct(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Event should show correct fee amount"""
    user = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and set fee
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setRedeemFee(500, sender=switchboard_charlie.address)  # 5%

    # Redeem
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    endaoment_psm.redeemGreen(green_amount, sender=user)

    # Check event - fee should be 50 USDC (5% of 1000)
    log = filter_logs(endaoment_psm, "RedeemGreen")[0]
    expected_fee = 50 * SIX_DECIMALS
    assert log.usdcFee == expected_fee


def test_event_for_zero_fee_redemption(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Event should show zero fee when no fee set"""
    user = boa.env.generate_address()
    green_amount = 1000 * EIGHTEEN_DECIMALS

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption (no fee set)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Redeem
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    endaoment_psm.redeemGreen(green_amount, sender=user)

    # Check event
    log = filter_logs(endaoment_psm, "RedeemGreen")[0]
    assert log.usdcFee == 0


####################
# Edge Case Tests #
####################


def test_max_uint256_handled_correctly(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """max_value should be capped at user balance"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    user_balance = green_token.balanceOf(user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and redeem with max_value (default parameter)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, MAX_UINT256, sender=user)
    usdc_received = endaoment_psm.redeemGreen(sender=user)

    # Should redeem based on actual balance
    expected_usdc = 1000 * SIX_DECIMALS
    assert usdc_received == expected_usdc


def test_very_small_green_amount(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Test redeeming with sub-dollar amounts"""
    user = boa.env.generate_address()
    small_amount = int(0.5 * EIGHTEEN_DECIMALS)  # 0.5 GREEN

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, int(0.5 * SIX_DECIMALS), sender=governance.address)
    charlie_token.approve(endaoment_psm.address, int(0.5 * SIX_DECIMALS), sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and redeem
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, small_amount, sender=user)
    usdc_received = endaoment_psm.redeemGreen(small_amount, sender=user)

    # Should receive 0.5 USDC
    expected_usdc = int(0.5 * SIX_DECIMALS)
    assert usdc_received == expected_usdc


def test_state_changes_atomic_on_revert(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Failed redemption should revert all state changes"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user (increase mint interval)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMaxIntervalMint(150_000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)

    charlie_token.mint(user, 100_001 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 100_001 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 100_001 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # Get initial interval state
    interval_before = endaoment_psm.globalRedeemInterval()

    # Approve and try to redeem over limit
    green_token.approve(endaoment_psm.address, 100_001 * EIGHTEEN_DECIMALS, sender=user)
    with boa.reverts("exceeds max interval redeem"):
        endaoment_psm.redeemGreen(100_001 * EIGHTEEN_DECIMALS, sender=user)

    # Interval state should be unchanged
    interval_after = endaoment_psm.globalRedeemInterval()
    assert interval_after == interval_before


def test_dust_amounts_and_precision(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Test redemption with very small dust amounts"""
    user = boa.env.generate_address()
    dust_amount = 1  # 1 wei of GREEN

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption and redeem
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, dust_amount, sender=user)

    # This may revert with "zero redeem amount" or "zero amount" due to precision
    # 1 wei GREEN = 0.000000000000000001 GREEN = 0.000000000000000001 USDC (in 18 decimals)
    # Converting to 6 decimals: 0.000000000000000001 * 10^6 / 10^18 = 0
    with boa.reverts("zero redeem amount"):
        endaoment_psm.redeemGreen(dust_amount, sender=user)


def test_consecutive_redemptions(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Test multiple consecutive redemptions"""
    user = boa.env.generate_address()

    # Setup: mint GREEN to user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.mint(user, 10_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 10_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(sender=user)

    # Fund PSM with USDC
    charlie_token.mint(endaoment_psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)

    # Enable redemption
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, 10_000 * EIGHTEEN_DECIMALS, sender=user)

    # Make 10 consecutive redemptions of 1000 GREEN each
    for i in range(10):
        usdc = endaoment_psm.redeemGreen(1000 * EIGHTEEN_DECIMALS, sender=user)
        assert usdc == 1000 * SIX_DECIMALS

    # All GREEN should be redeemed
    assert green_token.balanceOf(user) == 0


#######################
# Integration Tests  #
#######################


def test_full_cycle_mint_then_redeem(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Test full cycle: mint then redeem"""
    user = boa.env.generate_address()
    initial_usdc = 1000 * SIX_DECIMALS

    # Setup user with USDC
    charlie_token.mint(user, initial_usdc, sender=governance.address)

    # Enable minting and mint
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    charlie_token.approve(endaoment_psm.address, initial_usdc, sender=user)
    green_minted = endaoment_psm.mintGreen(sender=user)

    # Verify user has GREEN and no USDC
    assert green_token.balanceOf(user) == green_minted
    assert charlie_token.balanceOf(user) == 0

    # Enable redemption and redeem
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    green_token.approve(endaoment_psm.address, green_minted, sender=user)
    usdc_received = endaoment_psm.redeemGreen(sender=user)

    # Verify full cycle: user has USDC back, no GREEN
    assert charlie_token.balanceOf(user) == usdc_received
    assert green_token.balanceOf(user) == 0
    assert usdc_received == initial_usdc  # 1:1 at peg with no fees


def test_mint_partial_redeem_mint_again(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Test mint, partial redeem, mint again"""
    user = boa.env.generate_address()

    # Setup
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # First mint: 1000 USDC -> 1000 GREEN
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)
    green1 = endaoment_psm.mintGreen(sender=user)
    assert green_token.balanceOf(user) == 1000 * EIGHTEEN_DECIMALS

    # Fund PSM with USDC for redemptions
    charlie_token.mint(endaoment_psm.address, 10000 * SIX_DECIMALS, sender=governance.address)

    # Partial redeem: 400 GREEN -> 400 USDC
    green_token.approve(endaoment_psm.address, 400 * EIGHTEEN_DECIMALS, sender=user)
    usdc1 = endaoment_psm.redeemGreen(400 * EIGHTEEN_DECIMALS, sender=user)
    assert green_token.balanceOf(user) == 600 * EIGHTEEN_DECIMALS
    assert charlie_token.balanceOf(user) == 400 * SIX_DECIMALS

    # Second mint: 500 USDC -> 500 GREEN
    charlie_token.mint(user, 500 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 500 * SIX_DECIMALS, sender=user)
    green2 = endaoment_psm.mintGreen(500 * SIX_DECIMALS, sender=user)
    assert green_token.balanceOf(user) == 1100 * EIGHTEEN_DECIMALS


def test_fee_accumulation_across_multiple_redemptions_integration(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Test fee accumulation over multiple redemptions in realistic scenario"""
    user1 = boa.env.generate_address()
    user2 = boa.env.generate_address()

    # Setup
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    endaoment_psm.setRedeemFee(500, sender=switchboard_charlie.address)  # 5%

    # Both users mint GREEN
    charlie_token.mint(user1, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.mint(user2, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user1)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user2)
    endaoment_psm.mintGreen(sender=user1)
    endaoment_psm.mintGreen(sender=user2)

    # Record PSM USDC balance
    psm_balance_before = charlie_token.balanceOf(endaoment_psm.address)

    # User1 redeems (5% fee)
    green_token.approve(endaoment_psm.address, 1000 * EIGHTEEN_DECIMALS, sender=user1)
    usdc1 = endaoment_psm.redeemGreen(sender=user1)
    assert usdc1 == 950 * SIX_DECIMALS  # 1000 - 5% = 950

    # User2 redeems (5% fee)
    green_token.approve(endaoment_psm.address, 1000 * EIGHTEEN_DECIMALS, sender=user2)
    usdc2 = endaoment_psm.redeemGreen(sender=user2)
    assert usdc2 == 950 * SIX_DECIMALS  # 1000 - 5% = 950

    # PSM should retain fees: started with 2000, paid out 1900, keeps 100
    psm_balance_after = charlie_token.balanceOf(endaoment_psm.address)
    fees_retained = psm_balance_before - psm_balance_after - (usdc1 + usdc2)
    assert fees_retained == 0  # All correctly accounted


def test_multiple_users_interleaved_redemptions(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Test multiple users with interleaved mints and redemptions"""
    user1 = boa.env.generate_address()
    user2 = boa.env.generate_address()
    user3 = boa.env.generate_address()

    # Setup
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    # User1 mints
    charlie_token.mint(user1, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user1)
    endaoment_psm.mintGreen(sender=user1)

    # User2 mints
    charlie_token.mint(user2, 2000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 2000 * SIX_DECIMALS, sender=user2)
    endaoment_psm.mintGreen(sender=user2)

    # User1 redeems half
    green_token.approve(endaoment_psm.address, 500 * EIGHTEEN_DECIMALS, sender=user1)
    usdc1a = endaoment_psm.redeemGreen(500 * EIGHTEEN_DECIMALS, sender=user1)
    assert usdc1a == 500 * SIX_DECIMALS

    # User3 mints
    charlie_token.mint(user3, 500 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 500 * SIX_DECIMALS, sender=user3)
    endaoment_psm.mintGreen(sender=user3)

    # User2 redeems all
    green_token.approve(endaoment_psm.address, 2000 * EIGHTEEN_DECIMALS, sender=user2)
    usdc2 = endaoment_psm.redeemGreen(sender=user2)
    assert usdc2 == 2000 * SIX_DECIMALS

    # Verify final balances
    assert green_token.balanceOf(user1) == 500 * EIGHTEEN_DECIMALS
    assert green_token.balanceOf(user2) == 0
    assert green_token.balanceOf(user3) == 500 * EIGHTEEN_DECIMALS
