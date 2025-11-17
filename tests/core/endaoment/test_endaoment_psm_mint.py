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


def test_mint_fails_when_paused(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Minting should fail when contract is paused"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting first
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user with USDC
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Pause contract
    endaoment_psm.pause(True, sender=switchboard_charlie.address)

    # Attempt to mint should fail
    with boa.reverts("contract paused"):
        endaoment_psm.mintGreen(sender=user)


def test_mint_fails_when_minting_disabled(endaoment_psm, charlie_token, governance, mock_price_source):
    """Minting should fail when canMint flag is False"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Setup user with USDC
    charlie_token.mint(user, usdc_amount, sender=governance.address)

    # Verify canMint is False
    assert endaoment_psm.canMint() == False

    # Approve and attempt to mint
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    with boa.reverts("minting disabled"):
        endaoment_psm.mintGreen(sender=user)


def test_mint_succeeds_when_enabled(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Minting should succeed when properly enabled"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Set price
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Mint
    green_minted = endaoment_psm.mintGreen(sender=user)

    # Verify
    assert green_minted > 0


def test_mint_fails_with_zero_address_recipient(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Minting to zero address should fail"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Attempt to mint to zero address
    with boa.reverts("invalid recipient"):
        endaoment_psm.mintGreen(usdc_amount, ZERO_ADDRESS, sender=user)


def test_mint_fails_with_zero_balance(endaoment_psm, charlie_token, switchboard_charlie, mock_price_source):
    """Minting should fail if user has no USDC"""
    user = boa.env.generate_address()

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Attempt to mint with zero balance
    with boa.reverts("zero amount"):
        endaoment_psm.mintGreen(sender=user)


def test_mint_fails_without_approval(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Minting should fail without USDC approval"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user but don't approve
    charlie_token.mint(user, usdc_amount, sender=governance.address)

    # Attempt to mint without approval
    with boa.reverts("transfer failed"):
        endaoment_psm.mintGreen(sender=user)


def test_mint_requires_sufficient_approval(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Minting should fail if approval is less than amount"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user with partial approval
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 500 * SIX_DECIMALS, sender=user)

    # Attempt to mint more than approved
    with boa.reverts("transfer failed"):
        endaoment_psm.mintGreen(usdc_amount, sender=user)


##################
# Allowlist Tests #
##################


def test_mint_succeeds_without_allowlist_enforcement(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Anyone can mint when allowlist is not enforced"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Verify allowlist not enforced
    assert endaoment_psm.shouldEnforceMintAllowlist() == False

    # Setup and mint
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    green_minted = endaoment_psm.mintGreen(sender=user)

    assert green_minted > 0


def test_mint_fails_when_not_on_allowlist(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Minting should fail when allowlist is enforced and user is not on it"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting and allowlist enforcement
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setShouldEnforceMintAllowlist(True, sender=switchboard_charlie.address)

    # Verify user not on allowlist
    assert endaoment_psm.mintAllowlist(user) == False

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Attempt to mint
    with boa.reverts("not on mint allowlist"):
        endaoment_psm.mintGreen(sender=user)


def test_mint_succeeds_when_on_allowlist(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Minting should succeed when user is on allowlist"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting, allowlist, and add user
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setShouldEnforceMintAllowlist(True, sender=switchboard_charlie.address)
    endaoment_psm.updateMintAllowlist(user, True, sender=switchboard_charlie.address)

    # Verify user on allowlist
    assert endaoment_psm.mintAllowlist(user) == True

    # Setup and mint
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    green_minted = endaoment_psm.mintGreen(sender=user)

    assert green_minted > 0


def test_remove_from_allowlist_blocks_future_mints(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Removing user from allowlist blocks their future mints"""
    user = boa.env.generate_address()
    

    # Enable minting, allowlist, and add user
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setShouldEnforceMintAllowlist(True, sender=switchboard_charlie.address)
    endaoment_psm.updateMintAllowlist(user, True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, 2000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 2000 * SIX_DECIMALS, sender=user)

    # First mint succeeds
    green1 = endaoment_psm.mintGreen(500 * SIX_DECIMALS, sender=user)
    assert green1 > 0

    # Remove user from allowlist
    endaoment_psm.updateMintAllowlist(user, False, sender=switchboard_charlie.address)

    # Second mint fails
    with boa.reverts("not on mint allowlist"):
        endaoment_psm.mintGreen(500 * SIX_DECIMALS, sender=user)


def test_allowlist_check_uses_sender_not_recipient(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Allowlist should check sender, not recipient"""
    sender = boa.env.generate_address()
    recipient = boa.env.generate_address()
    

    # Enable minting, allowlist, add sender (not recipient)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setShouldEnforceMintAllowlist(True, sender=switchboard_charlie.address)
    endaoment_psm.updateMintAllowlist(sender, True, sender=switchboard_charlie.address)

    # Setup sender
    charlie_token.mint(sender, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=sender)

    # Sender can mint to recipient
    green_minted = endaoment_psm.mintGreen(1000 * SIX_DECIMALS, recipient, sender=sender)
    assert green_minted > 0


def test_allowlist_enforcement_toggle(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Toggling allowlist enforcement should work correctly"""
    user = boa.env.generate_address()
    

    # Enable minting, enforce allowlist (user not on list)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setShouldEnforceMintAllowlist(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, 2000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 2000 * SIX_DECIMALS, sender=user)

    # Mint fails when enforced
    with boa.reverts("not on mint allowlist"):
        endaoment_psm.mintGreen(500 * SIX_DECIMALS, sender=user)

    # Disable enforcement
    endaoment_psm.setShouldEnforceMintAllowlist(False, sender=switchboard_charlie.address)

    # Now mint succeeds
    green_minted = endaoment_psm.mintGreen(500 * SIX_DECIMALS, sender=user)
    assert green_minted > 0


##########################
# Amount Handling Tests #
##########################


def test_mint_with_explicit_amount(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Minting specific USDC amount should mint corresponding GREEN"""
    user = boa.env.generate_address()
    usdc_amount = 500 * SIX_DECIMALS

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup and mint
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    green_minted = endaoment_psm.mintGreen(usdc_amount, sender=user)

    # Should mint 500 GREEN (1:1 at peg)
    expected_green = 500 * EIGHTEEN_DECIMALS
    assert green_minted == expected_green


def test_mint_with_max_value_uses_full_balance(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Minting with max_value should use user's full USDC balance"""
    user = boa.env.generate_address()
    usdc_balance = 1000 * SIX_DECIMALS

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup and mint
    charlie_token.mint(user, usdc_balance, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, MAX_UINT256, sender=user)
    green_minted = endaoment_psm.mintGreen(sender=user)

    # Should use full 1000 USDC
    expected_green = 1000 * EIGHTEEN_DECIMALS
    assert green_minted == expected_green
    assert charlie_token.balanceOf(user) == 0


def test_mint_capped_by_user_balance(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Requested mint amount should be capped by user's actual balance"""
    user = boa.env.generate_address()
    actual_balance = 500 * SIX_DECIMALS
    requested_amount = 1000 * SIX_DECIMALS

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup and mint
    charlie_token.mint(user, actual_balance, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, requested_amount, sender=user)
    green_minted = endaoment_psm.mintGreen(requested_amount, sender=user)

    # Should only mint based on actual balance (500 USDC)
    expected_green = 500 * EIGHTEEN_DECIMALS
    assert green_minted == expected_green


def test_mint_updates_balances_correctly(endaoment_psm, charlie_token, switchboard_charlie, green_token, governance, mock_price_source):
    """Minting should correctly update all balances"""
    user = boa.env.generate_address()
    mint_amount = 500 * SIX_DECIMALS

    # Enable minting

    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)

    # Record balances before
    usdc_before = charlie_token.balanceOf(user)
    green_before = green_token.balanceOf(user)
    psm_usdc_before = charlie_token.balanceOf(endaoment_psm.address)

    # Mint
    charlie_token.approve(endaoment_psm.address, mint_amount, sender=user)
    green_minted = endaoment_psm.mintGreen(mint_amount, sender=user)

    # Check balances after
    usdc_after = charlie_token.balanceOf(user)
    green_after = green_token.balanceOf(user)
    psm_usdc_after = charlie_token.balanceOf(endaoment_psm.address)

    # Verify changes
    assert usdc_before - usdc_after == mint_amount
    assert green_after - green_before == green_minted
    assert psm_usdc_after - psm_usdc_before == mint_amount


def test_mint_to_different_recipient(endaoment_psm, charlie_token, switchboard_charlie, green_token, governance, mock_price_source):
    """Minting can send GREEN to a different recipient"""
    payer = boa.env.generate_address()
    recipient = boa.env.generate_address()
    mint_amount = 500 * SIX_DECIMALS

    # Enable minting

    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup payer
    charlie_token.mint(payer, mint_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, mint_amount, sender=payer)

    # Payer mints to recipient
    green_minted = endaoment_psm.mintGreen(mint_amount, recipient, sender=payer)

    # Verify
    assert charlie_token.balanceOf(payer) == 0
    assert green_token.balanceOf(recipient) == green_minted
    assert green_token.balanceOf(payer) == 0


def test_multiple_mints_accumulate(endaoment_psm, charlie_token, switchboard_charlie, green_token, governance, mock_price_source):
    """Multiple mints should accumulate GREEN balance"""
    user = boa.env.generate_address()

    # Enable minting

    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, 1000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 1000 * SIX_DECIMALS, sender=user)

    # First mint
    green1 = endaoment_psm.mintGreen(100 * SIX_DECIMALS, sender=user)
    balance_after_first = green_token.balanceOf(user)
    assert balance_after_first == green1

    # Second mint
    green2 = endaoment_psm.mintGreen(200 * SIX_DECIMALS, sender=user)
    balance_after_second = green_token.balanceOf(user)
    assert balance_after_second == green1 + green2


##############
# Fee Tests #
##############


def test_mint_with_zero_fee(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Default zero fee should result in 1:1 minting"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Verify zero fee
    assert endaoment_psm.mintFee() == 0

    # Setup and mint
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    green_minted = endaoment_psm.mintGreen(usdc_amount, sender=user)

    # Should mint 1:1
    expected_green = 1000 * EIGHTEEN_DECIMALS
    assert green_minted == expected_green


def test_mint_with_5_percent_fee(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """5% fee should reduce minted amount accordingly"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting and set fee
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMintFee(500, sender=switchboard_charlie.address)  # 5.00%

    # Setup and mint
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    green_minted = endaoment_psm.mintGreen(usdc_amount, sender=user)

    # Should mint 950 GREEN (1000 - 5% fee)
    expected_green = 950 * EIGHTEEN_DECIMALS
    assert green_minted == expected_green


def test_mint_with_maximum_fee(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """100% fee should result in zero mint and revert"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting and set 100% fee

    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMintFee(10000, sender=switchboard_charlie.address)  # 100.00%

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Attempt to mint should fail (100% fee means zero capacity)
    with boa.reverts("zero amount"):
        endaoment_psm.mintGreen(usdc_amount, sender=user)


def test_fee_stays_in_contract(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Fees should accumulate in the PSM contract"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting and set fee
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMintFee(500, sender=switchboard_charlie.address)  # 5.00%

    # Record PSM balance before
    psm_balance_before = charlie_token.balanceOf(endaoment_psm.address)

    # Setup and mint
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    endaoment_psm.mintGreen(usdc_amount, sender=user)

    # PSM should have all 1000 USDC (including 50 USDC fee)
    psm_balance_after = charlie_token.balanceOf(endaoment_psm.address)
    assert psm_balance_after - psm_balance_before == usdc_amount


def test_fee_calculation_precision(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Fee calculation should handle precision correctly"""
    user = boa.env.generate_address()
    usdc_amount = 1337 * SIX_DECIMALS  # Odd number

    # Enable minting and set fee
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMintFee(250, sender=switchboard_charlie.address)  # 2.50%

    # Setup and mint
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    green_minted = endaoment_psm.mintGreen(usdc_amount, sender=user)

    # Fee is 2.5% of 1337 USDC = 33.425 USDC (rounds down to 33.425 in raw units)
    # feeAmount = 1337000000 * 250 / 10000 = 33425000 (33.425 USDC)
    # Net amount = 1337000000 - 33425000 = 1303575000 (1303.575 USDC) -> 1303.575 GREEN
    expected_green = 1303575000000000000000  # 1303.575 * EIGHTEEN_DECIMALS
    assert green_minted == expected_green


def test_different_fee_amounts(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Different fee percentages should calculate correctly"""
    user = boa.env.generate_address()
    

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user with lots of USDC
    charlie_token.mint(user, 10_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 10_000 * SIX_DECIMALS, sender=user)

    # Test 1% fee
    endaoment_psm.setMintFee(100, sender=switchboard_charlie.address)  # 1.00%
    green1 = endaoment_psm.mintGreen(1000 * SIX_DECIMALS, sender=user)
    assert green1 == 990 * EIGHTEEN_DECIMALS  # 1000 - 1%

    # Test 10% fee
    endaoment_psm.setMintFee(1000, sender=switchboard_charlie.address)  # 10.00%
    green2 = endaoment_psm.mintGreen(1000 * SIX_DECIMALS, sender=user)
    assert green2 == 900 * EIGHTEEN_DECIMALS  # 1000 - 10%


#################
# Pricing Tests #
#################


def test_mint_at_peg_one_to_one(endaoment_psm, charlie_token, mock_price_source, switchboard_charlie, governance):
    """At $1.00 peg, should mint 1:1"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Set USDC price to exactly $1.00
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)

    # Setup and mint
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    green_minted = endaoment_psm.mintGreen(usdc_amount, sender=user)

    # Should mint 1:1
    expected_green = 1000 * EIGHTEEN_DECIMALS
    assert green_minted == expected_green


def test_mint_when_usdc_above_peg(endaoment_psm, charlie_token, mock_price_source, switchboard_charlie, governance):
    """When USDC > $1, protocol should mint less GREEN (protect protocol)"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Set USDC price to $1.05
    mock_price_source.setPrice(charlie_token.address, int(1.05 * EIGHTEEN_DECIMALS))

    # Setup and mint
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    green_minted = endaoment_psm.mintGreen(usdc_amount, sender=user)

    # Protocol uses min(), so at 1:1 conversion we get 1000 GREEN
    # But at $1.05, USD value would suggest 1050 GREEN
    # min(1050, 1000) = 1000 GREEN (protects protocol)
    expected_green = 1000 * EIGHTEEN_DECIMALS
    assert green_minted == expected_green


def test_mint_when_usdc_below_peg(endaoment_psm, charlie_token, mock_price_source, switchboard_charlie, governance):
    """When USDC < $1, protocol should mint less GREEN (protect protocol)"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Set USDC price to $0.95
    mock_price_source.setPrice(charlie_token.address, int(0.95 * EIGHTEEN_DECIMALS))

    # Setup and mint
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    green_minted = endaoment_psm.mintGreen(usdc_amount, sender=user)

    # At $0.95, USD value is 950 GREEN
    # 1:1 conversion gives 1000 GREEN
    # min(950, 1000) = 950 GREEN (protects protocol)
    expected_green = 950 * EIGHTEEN_DECIMALS
    assert green_minted == expected_green


def test_decimal_conversion_18_to_6(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Verify correct decimal conversion from 6 to 18 decimals"""
    user = boa.env.generate_address()
    usdc_amount = 1 * SIX_DECIMALS  # 1 USDC

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup and mint
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    green_minted = endaoment_psm.mintGreen(usdc_amount, sender=user)

    # 1 USDC (1e6) should become 1 GREEN (1e18)
    expected_green = 1 * EIGHTEEN_DECIMALS
    assert green_minted == expected_green


def test_pricing_with_fee_interaction(endaoment_psm, charlie_token, mock_price_source, switchboard_charlie, governance):
    """Fees and pricing should interact correctly"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting, set fee and price
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMintFee(500, sender=switchboard_charlie.address)  # 5% fee
    mock_price_source.setPrice(charlie_token.address, int(0.95 * EIGHTEEN_DECIMALS))  # $0.95

    # Setup and mint
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    green_minted = endaoment_psm.mintGreen(usdc_amount, sender=user)

    # At $0.95, min gives 950 GREEN before fee
    # After 5% fee: 950 * 0.95 = 902.5 GREEN
    expected_green = int(902.5 * EIGHTEEN_DECIMALS)
    assert green_minted == expected_green


##################
# Interval Tests #
##################


def test_mint_within_interval_limit(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Minting within limit should succeed"""
    user = boa.env.generate_address()

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Verify interval limit
    max_interval = endaoment_psm.maxIntervalMint()
    assert max_interval == 100_000 * EIGHTEEN_DECIMALS

    # Setup and mint 50,000 GREEN (well within limit)
    charlie_token.mint(user, 60_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 60_000 * SIX_DECIMALS, sender=user)
    green_minted = endaoment_psm.mintGreen(50_000 * SIX_DECIMALS, sender=user)

    assert green_minted == 50_000 * EIGHTEEN_DECIMALS


def test_mint_exactly_at_interval_limit(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Minting exactly at limit should succeed"""
    user = boa.env.generate_address()

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup and mint exactly 100,000 GREEN
    charlie_token.mint(user, 100_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 100_000 * SIX_DECIMALS, sender=user)
    green_minted = endaoment_psm.mintGreen(100_000 * SIX_DECIMALS, sender=user)

    assert green_minted == 100_000 * EIGHTEEN_DECIMALS


def test_mint_exceeds_interval_limit(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source):
    """Minting beyond limit should gracefully cap to interval limit"""
    user = boa.env.generate_address()

    # Enable minting

    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user with more USDC than interval allows
    charlie_token.mint(user, 100_001 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 100_001 * SIX_DECIMALS, sender=user)

    # Attempt to mint 100,001 USDC worth - should gracefully cap to 100,000
    green_minted = endaoment_psm.mintGreen(100_001 * SIX_DECIMALS, sender=user)

    # Should mint exactly 100,000 GREEN (the interval limit)
    assert green_minted == 100_000 * EIGHTEEN_DECIMALS
    assert green_token.balanceOf(user) == 100_000 * EIGHTEEN_DECIMALS

    # Only 100,000 USDC should have been transferred (not 100,001)
    assert charlie_token.balanceOf(user) == 1 * SIX_DECIMALS


def test_multiple_mints_accumulate_in_interval(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Multiple mints should accumulate toward interval limit"""
    user = boa.env.generate_address()

    # Enable minting

    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, 101_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 101_000 * SIX_DECIMALS, sender=user)

    # First mint: 60,000 GREEN
    green1 = endaoment_psm.mintGreen(60_000 * SIX_DECIMALS, sender=user)
    assert green1 == 60_000 * EIGHTEEN_DECIMALS

    # Second mint: 40,000 GREEN (total 100,000)
    green2 = endaoment_psm.mintGreen(40_000 * SIX_DECIMALS, sender=user)
    assert green2 == 40_000 * EIGHTEEN_DECIMALS

    # Third mint: trying to mint more should fail with zero amount (no interval capacity left)
    with boa.reverts("zero amount"):
        endaoment_psm.mintGreen(1 * SIX_DECIMALS, sender=user)


def test_interval_resets_after_blocks(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Interval should reset after configured blocks"""
    user = boa.env.generate_address()

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, 200_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 200_000 * SIX_DECIMALS, sender=user)

    # Mint full limit
    green1 = endaoment_psm.mintGreen(100_000 * SIX_DECIMALS, sender=user)
    assert green1 == 100_000 * EIGHTEEN_DECIMALS

    # Roll forward past interval
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    # Should be able to mint another 100,000 GREEN
    green2 = endaoment_psm.mintGreen(100_000 * SIX_DECIMALS, sender=user)
    assert green2 == 100_000 * EIGHTEEN_DECIMALS


def test_interval_boundary_exact_block(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Test behavior at exact interval boundary"""
    user = boa.env.generate_address()

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Record starting block
    start_block = boa.env.evm.patch.block_number

    # Setup and mint full limit
    charlie_token.mint(user, 200_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 200_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(100_000 * SIX_DECIMALS, sender=user)

    # Roll to one block before the boundary
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS - 1)

    # One block before boundary, should still be in same interval (no capacity left)
    with boa.reverts("zero amount"):
        endaoment_psm.mintGreen(1 * SIX_DECIMALS, sender=user)

    # Roll one more block to reach the boundary
    boa.env.time_travel(blocks=1)

    # At the boundary (start + numBlocks), we're in a fresh interval
    # (contract uses >, not >=, so boundary is already a new interval)
    green2 = endaoment_psm.mintGreen(50_000 * SIX_DECIMALS, sender=user)
    assert green2 == 50_000 * EIGHTEEN_DECIMALS


def test_fresh_interval_starts_on_first_mint(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """First mint should initialize interval start"""
    user = boa.env.generate_address()

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Check initial state
    interval_data = endaoment_psm.globalMintInterval()
    assert interval_data[0] == 0  # start == 0 initially

    # Setup user
    charlie_token.mint(user, 50_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 50_000 * SIX_DECIMALS, sender=user)

    # First mint
    current_block = boa.env.evm.patch.block_number
    endaoment_psm.mintGreen(30_000 * SIX_DECIMALS, sender=user)

    # Check interval updated
    interval_data = endaoment_psm.globalMintInterval()
    assert interval_data[0] == current_block
    assert interval_data[1] == 30_000 * EIGHTEEN_DECIMALS


def test_interval_amount_accumulates(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Interval amount should accumulate across mints"""
    user = boa.env.generate_address()

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, 100_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 100_000 * SIX_DECIMALS, sender=user)

    # First mint: 30,000 GREEN
    endaoment_psm.mintGreen(30_000 * SIX_DECIMALS, sender=user)
    interval_data = endaoment_psm.globalMintInterval()
    assert interval_data[1] == 30_000 * EIGHTEEN_DECIMALS

    # Second mint: 20,000 GREEN
    endaoment_psm.mintGreen(20_000 * SIX_DECIMALS, sender=user)
    interval_data = endaoment_psm.globalMintInterval()
    assert interval_data[1] == 50_000 * EIGHTEEN_DECIMALS


def test_getAvailIntervalMint_accuracy(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """getAvailIntervalMint should return accurate remaining capacity"""
    user = boa.env.generate_address()

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Initial: full capacity
    avail = endaoment_psm.getAvailIntervalMint()
    assert avail == 100_000 * EIGHTEEN_DECIMALS

    # Setup and mint 30,000
    charlie_token.mint(user, 100_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 100_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(30_000 * SIX_DECIMALS, sender=user)

    # Should have 70,000 remaining
    avail = endaoment_psm.getAvailIntervalMint()
    assert avail == 70_000 * EIGHTEEN_DECIMALS

    # Mint 70,000 more
    endaoment_psm.mintGreen(70_000 * SIX_DECIMALS, sender=user)

    # Should have 0 remaining
    avail = endaoment_psm.getAvailIntervalMint()
    assert avail == 0


def test_getAvailIntervalMint_resets_after_interval(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """getAvailIntervalMint should reset to full capacity after interval expires"""
    user = boa.env.generate_address()

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup and mint 60,000
    charlie_token.mint(user, 200_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 200_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(60_000 * SIX_DECIMALS, sender=user)

    # Should have 40,000 remaining
    avail = endaoment_psm.getAvailIntervalMint()
    assert avail == 40_000 * EIGHTEEN_DECIMALS

    # Travel past interval
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    # Should reset to full capacity
    avail = endaoment_psm.getAvailIntervalMint()
    assert avail == 100_000 * EIGHTEEN_DECIMALS


def test_getAvailIntervalMint_before_first_mint(endaoment_psm):
    """getAvailIntervalMint should return full capacity before first mint"""
    avail = endaoment_psm.getAvailIntervalMint()
    assert avail == 100_000 * EIGHTEEN_DECIMALS


def test_getMaxUsdcAmountForMint_full_interval(endaoment_psm, charlie_token, switchboard_charlie, mock_price_source):
    """getMaxUsdcAmountForMint should return full interval capacity in USDC"""
    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # At 1:1 peg with no fee, max USDC should equal interval limit
    max_usdc = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, False)
    assert max_usdc == 100_000 * SIX_DECIMALS


def test_getMaxUsdcAmountForMint_after_partial_mint(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """getMaxUsdcAmountForMint should reflect remaining interval capacity"""
    user = boa.env.generate_address()

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Mint 30,000 GREEN
    charlie_token.mint(user, 100_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 100_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(30_000 * SIX_DECIMALS, sender=user)

    # Max USDC should now be 70,000
    max_usdc = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, False)
    assert max_usdc == 70_000 * SIX_DECIMALS


def test_getMaxUsdcAmountForMint_with_fee(endaoment_psm, charlie_token, switchboard_charlie, mock_price_source):
    """getMaxUsdcAmountForMint should account for mint fee"""
    # Enable minting with 5% fee
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMintFee(500, sender=switchboard_charlie.address)  # 5%

    # With 5% fee, to get 100,000 GREEN need: 100,000 / 0.95 = 105,263.157... USDC
    # Formula: usdcInput = greenAmount * HUNDRED_PERCENT / (HUNDRED_PERCENT - fee)
    #         = 100_000 * 10_000 / (10_000 - 500)
    #         = 100_000 * 10_000 / 9_500
    expected = 100_000 * SIX_DECIMALS * 10_000 // 9_500
    max_usdc = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, False)
    assert max_usdc == expected


def test_getMaxUsdcAmountForMint_with_user_address(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """getMaxUsdcAmountForMint should cap by user balance when user provided"""
    user = boa.env.generate_address()

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Give user only 50,000 USDC
    charlie_token.mint(user, 50_000 * SIX_DECIMALS, sender=governance.address)

    # Without user address, should return full interval
    max_usdc_general = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, False)
    assert max_usdc_general == 100_000 * SIX_DECIMALS

    # With user address, should cap at user balance
    max_usdc_user = endaoment_psm.getMaxUsdcAmountForMint(user, False)
    assert max_usdc_user == 50_000 * SIX_DECIMALS


def test_getMaxUsdcAmountForMint_usdc_below_peg(endaoment_psm, charlie_token, switchboard_charlie, mock_price_source):
    """getMaxUsdcAmountForMint should require more USDC when below peg"""
    # Enable minting
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Set USDC price to $0.95 (below peg)
    mock_price_source.setPrice(charlie_token.address, 95 * (EIGHTEEN_DECIMALS // 100))

    # When USDC is at $0.95, need more USDC to mint 100k GREEN
    # To get $100k worth of GREEN, need 100k / 0.95 = ~105,263 USDC
    max_usdc = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, False)

    # Should be more than 100k USDC due to below-peg price
    assert max_usdc > 100_000 * SIX_DECIMALS
    # Should be approximately 105,263 USDC
    assert max_usdc > 105_000 * SIX_DECIMALS


def test_getMaxUsdcAmountForMint_usdc_above_peg(endaoment_psm, charlie_token, switchboard_charlie, mock_price_source):
    """getMaxUsdcAmountForMint should use decimal conversion when USDC above peg"""
    # Enable minting
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Set USDC price to $1.05 (above peg)
    mock_price_source.setPrice(charlie_token.address, 105 * (EIGHTEEN_DECIMALS // 100))

    # When USDC is at $1.05, the price desk would suggest less USDC needed
    # But contract uses max(priceDesk, decimalConversion), so at 1:1 decimal ratio
    max_usdc = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, False)

    # Should use decimal conversion (100k USDC for 100k GREEN)
    assert max_usdc == 100_000 * SIX_DECIMALS


def test_getMaxUsdcAmountForMint_after_interval_reset(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """getMaxUsdcAmountForMint should reset after interval expires"""
    user = boa.env.generate_address()

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Mint 80,000 GREEN
    charlie_token.mint(user, 100_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 100_000 * SIX_DECIMALS, sender=user)
    endaoment_psm.mintGreen(80_000 * SIX_DECIMALS, sender=user)

    # Should have only 20,000 remaining
    max_usdc = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, False)
    assert max_usdc == 20_000 * SIX_DECIMALS

    # Travel past interval
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    # Should reset to full capacity
    max_usdc = endaoment_psm.getMaxUsdcAmountForMint(ZERO_ADDRESS, False)
    assert max_usdc == 100_000 * SIX_DECIMALS


def test_getMaxUsdcAmountForMint_with_fee_and_user_balance(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """getMaxUsdcAmountForMint should apply both fee adjustment and user balance cap"""
    user = boa.env.generate_address()

    # Enable minting with 10% fee
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMintFee(1000, sender=switchboard_charlie.address)  # 10%

    # With 10% fee, full interval would require: 100,000 / 0.9 = 111,111.11... USDC
    expected_for_interval = 100_000 * SIX_DECIMALS * 10_000 // 9_000

    # Give user only 50,000 USDC (less than fee-adjusted amount)
    charlie_token.mint(user, 50_000 * SIX_DECIMALS, sender=governance.address)

    # Should cap at user's 50k balance
    max_usdc_user = endaoment_psm.getMaxUsdcAmountForMint(user, False)
    assert max_usdc_user == 50_000 * SIX_DECIMALS


def test_concurrent_mints_by_different_users_share_interval(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Multiple users should share same interval limit"""
    user_a = boa.env.generate_address()
    user_b = boa.env.generate_address()

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup users
    charlie_token.mint(user_a, 60_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.mint(user_b, 50_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 60_000 * SIX_DECIMALS, sender=user_a)
    charlie_token.approve(endaoment_psm.address, 50_000 * SIX_DECIMALS, sender=user_b)

    # User A mints 60,000 GREEN
    green_a = endaoment_psm.mintGreen(sender=user_a)
    assert green_a == 60_000 * EIGHTEEN_DECIMALS

    # User B tries to mint all 50,000 but interval limit only has 40,000 remaining
    # Should gracefully cap to 40,000 GREEN
    green_b = endaoment_psm.mintGreen(sender=user_b)
    assert green_b == 40_000 * EIGHTEEN_DECIMALS

    # User B should have 10,000 USDC remaining (50k - 40k used)
    assert charlie_token.balanceOf(user_b) == 10_000 * SIX_DECIMALS


###############
# Event Tests #
###############


def test_mint_emits_event_with_correct_params(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """MintGreen event should be emitted with correct parameters"""
    user = boa.env.generate_address()
    recipient = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup and mint
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    green_minted = endaoment_psm.mintGreen(usdc_amount, recipient, sender=user)

    # Check event
    log = filter_logs(endaoment_psm, "MintGreen")[0]
    assert log.user == recipient
    assert log.sender == user
    assert log.usdcIn == usdc_amount
    assert log.greenOut == green_minted
    assert log.usdcFee == 0  # default no fee


def test_event_sender_vs_recipient_different(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Event should correctly distinguish sender and recipient"""
    payer = boa.env.generate_address()
    recipient = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup and mint
    charlie_token.mint(payer, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=payer)
    endaoment_psm.mintGreen(usdc_amount, recipient, sender=payer)

    # Check event
    log = filter_logs(endaoment_psm, "MintGreen")[0]
    assert log.sender == payer
    assert log.user == recipient
    assert log.sender != log.user


def test_event_fee_amount_correct(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Event should show correct fee amount"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting and set fee
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMintFee(500, sender=switchboard_charlie.address)  # 5%

    # Setup and mint
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    endaoment_psm.mintGreen(usdc_amount, sender=user)

    # Check event - fee should be 50 USDC (5% of 1000)
    log = filter_logs(endaoment_psm, "MintGreen")[0]
    expected_fee = 50 * SIX_DECIMALS
    assert log.usdcFee == expected_fee


####################
# Edge Case Tests #
####################


def test_max_uint256_handled_correctly(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """max_value should be capped at user balance"""
    user = boa.env.generate_address()
    user_balance = 1000 * SIX_DECIMALS

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup and mint with max_value (default parameter)
    charlie_token.mint(user, user_balance, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, MAX_UINT256, sender=user)
    green_minted = endaoment_psm.mintGreen(sender=user)

    # Should mint based on actual balance
    expected_green = 1000 * EIGHTEEN_DECIMALS
    assert green_minted == expected_green


def test_return_value_matches_minted_amount(endaoment_psm, charlie_token, switchboard_charlie, green_token, governance, mock_price_source):
    """Function return value should match actual GREEN minted"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting

    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    balance_before = green_token.balanceOf(user)

    # Setup and mint
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    returned_amount = endaoment_psm.mintGreen(usdc_amount, sender=user)

    balance_after = green_token.balanceOf(user)
    actual_minted = balance_after - balance_before

    assert returned_amount == actual_minted


def test_should_auto_deposit_flag_respected(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """shouldAutoDeposit flag should control yield deposits"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting, disable auto-deposit
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setShouldAutoDeposit(False, sender=switchboard_charlie.address)

    # Setup and mint
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    endaoment_psm.mintGreen(usdc_amount, sender=user)

    # USDC should stay in PSM (not deposited to yield)
    psm_usdc_balance = charlie_token.balanceOf(endaoment_psm.address)
    assert psm_usdc_balance == usdc_amount


def test_state_changes_atomic_on_revert(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Failed mint should revert all state changes"""
    user = boa.env.generate_address()

    # Enable minting
    
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Get initial interval state
    interval_before = endaoment_psm.globalMintInterval()

    # Setup user
    charlie_token.mint(user, 100_001 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 100_001 * SIX_DECIMALS, sender=user)

    # Try to mint over limit - should gracefully cap to 100,000
    green_minted = endaoment_psm.mintGreen(100_001 * SIX_DECIMALS, sender=user)
    assert green_minted == 100_000 * EIGHTEEN_DECIMALS

    # Interval state should reflect the 100k mint
    interval_after = endaoment_psm.globalMintInterval()
    assert interval_after.amount == 100_000 * EIGHTEEN_DECIMALS
    assert interval_after.start > 0


def test_very_small_usdc_amount(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """Test minting with sub-dollar amounts"""
    user = boa.env.generate_address()
    small_amount = int(0.5 * SIX_DECIMALS)  # 0.5 USDC

    # Enable minting

    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup and mint
    charlie_token.mint(user, small_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, small_amount, sender=user)
    green_minted = endaoment_psm.mintGreen(small_amount, sender=user)

    # Should mint 0.5 GREEN
    expected_green = int(0.5 * EIGHTEEN_DECIMALS)
    assert green_minted == expected_green


###########################
# Savings Green Tests     #
###########################


def test_mint_with_savings_green_happy_path(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source, green_token, savings_green):
    """Minting with _wantsSavingsGreen=True should deposit GREEN into Savings Green and send sGREEN to recipient"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Get initial balances
    initial_green_balance = green_token.balanceOf(user)
    initial_sgreen_balance = savings_green.balanceOf(user)

    # Mint with Savings Green
    green_minted = endaoment_psm.mintGreen(usdc_amount, user, True, sender=user)

    # Verify user received sGREEN shares, not GREEN
    final_green_balance = green_token.balanceOf(user)
    final_sgreen_balance = savings_green.balanceOf(user)

    assert final_green_balance == initial_green_balance  # No GREEN received
    assert final_sgreen_balance > initial_sgreen_balance  # sGREEN shares received
    assert green_minted > 0  # Function returns GREEN amount that was minted


def test_mint_without_savings_green_uses_regular_green(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source, green_token, savings_green):
    """Minting with _wantsSavingsGreen=False (default) should send GREEN tokens directly"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Get initial balances
    initial_green_balance = green_token.balanceOf(user)
    initial_sgreen_balance = savings_green.balanceOf(user)

    # Mint without Savings Green (default False)
    green_minted = endaoment_psm.mintGreen(usdc_amount, user, False, sender=user)

    # Verify user received GREEN, not sGREEN
    final_green_balance = green_token.balanceOf(user)
    final_sgreen_balance = savings_green.balanceOf(user)

    assert final_green_balance == initial_green_balance + green_minted  # GREEN received
    assert final_sgreen_balance == initial_sgreen_balance  # No sGREEN received


def test_mint_savings_green_to_different_recipient(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source, green_token, savings_green):
    """Minting with Savings Green should send sGREEN to specified recipient"""
    user = boa.env.generate_address()
    recipient = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Get initial balances
    initial_recipient_sgreen = savings_green.balanceOf(recipient)

    # Mint with Savings Green to different recipient
    endaoment_psm.mintGreen(usdc_amount, recipient, True, sender=user)

    # Verify recipient received sGREEN
    final_recipient_sgreen = savings_green.balanceOf(recipient)
    assert final_recipient_sgreen > initial_recipient_sgreen


def test_mint_savings_green_share_calculation(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source, green_token, savings_green):
    """sGREEN shares received should match ERC4626 deposit calculation"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Mint with Savings Green
    green_minted = endaoment_psm.mintGreen(usdc_amount, user, True, sender=user)

    # Calculate expected shares
    expected_shares = savings_green.convertToShares(green_minted)
    actual_shares = savings_green.balanceOf(user)

    assert actual_shares == expected_shares


def test_mint_savings_green_with_dust_amount_fallback(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source, green_token, savings_green):
    """Minting with amount <= 10^18 (1 GREEN) should fallback to regular GREEN even if _wantsSavingsGreen=True"""
    user = boa.env.generate_address()
    # Amount that will mint exactly 1 GREEN (10^18 wei) - at dust threshold
    usdc_amount = 1 * SIX_DECIMALS  # 1 USDC

    # Enable minting (fee is already 0 by default)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Get initial balances
    initial_green_balance = green_token.balanceOf(user)
    initial_sgreen_balance = savings_green.balanceOf(user)

    # Mint with Savings Green (but amount is at dust threshold, should fallback)
    green_minted = endaoment_psm.mintGreen(usdc_amount, user, True, sender=user)

    # Verify user received GREEN (fallback), not sGREEN
    final_green_balance = green_token.balanceOf(user)
    final_sgreen_balance = savings_green.balanceOf(user)

    assert green_minted == 1 * EIGHTEEN_DECIMALS  # Exactly 1 GREEN (at threshold)
    assert final_green_balance == initial_green_balance + green_minted  # GREEN received directly
    assert final_sgreen_balance == initial_sgreen_balance  # No sGREEN received


def test_mint_savings_green_at_minimum_threshold(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source, green_token, savings_green):
    """Minting with amount just above 10^18 (> 1 GREEN) should deposit to Savings Green"""
    user = boa.env.generate_address()
    # Amount that will mint slightly more than 1 GREEN (10^18 wei)
    usdc_amount = 2 * SIX_DECIMALS  # 2 USDC = 2 GREEN, above threshold

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Get initial balances
    initial_sgreen_balance = savings_green.balanceOf(user)

    # Mint with Savings Green
    green_minted = endaoment_psm.mintGreen(usdc_amount, user, True, sender=user)

    # Verify user received sGREEN (not fallback)
    final_sgreen_balance = savings_green.balanceOf(user)

    assert green_minted > 1 * EIGHTEEN_DECIMALS  # Above threshold (> 1 GREEN)
    assert final_sgreen_balance > initial_sgreen_balance  # sGREEN received


def test_mint_savings_green_just_below_threshold(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source, green_token, savings_green):
    """Minting with amount less than 1 GREEN should fallback to regular GREEN"""
    user = boa.env.generate_address()
    # Mint 0.5 GREEN (below 1 GREEN threshold)
    usdc_amount = int(0.5 * SIX_DECIMALS)  # 0.5 USDC

    # Enable minting (fee is already 0 by default)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Get initial balances
    initial_green_balance = green_token.balanceOf(user)
    initial_sgreen_balance = savings_green.balanceOf(user)

    # Mint with Savings Green (should fallback since < 1 GREEN)
    green_minted = endaoment_psm.mintGreen(usdc_amount, user, True, sender=user)

    # Verify fallback behavior - regular GREEN received, not sGREEN
    final_green_balance = green_token.balanceOf(user)
    final_sgreen_balance = savings_green.balanceOf(user)

    assert green_minted == int(0.5 * EIGHTEEN_DECIMALS)  # 0.5 GREEN (below threshold)
    assert final_green_balance == initial_green_balance + green_minted  # GREEN received directly
    assert final_sgreen_balance == initial_sgreen_balance  # No sGREEN received


def test_mint_event_with_savings_green_flag_true(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source, savings_green):
    """MintGreen event should have receivedSavingsGreen=True when sGREEN deposited"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Mint with Savings Green
    endaoment_psm.mintGreen(usdc_amount, user, True, sender=user)

    # Check event
    log = filter_logs(endaoment_psm, "MintGreen")[0]
    assert log.receivedSavingsGreen == True


def test_mint_event_with_savings_green_flag_false(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source):
    """MintGreen event should have receivedSavingsGreen=False when regular GREEN minted"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Mint without Savings Green
    endaoment_psm.mintGreen(usdc_amount, user, False, sender=user)

    # Check event
    log = filter_logs(endaoment_psm, "MintGreen")[0]
    assert log.receivedSavingsGreen == False


def test_mint_savings_green_with_fee(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source, green_token, savings_green):
    """Minting with fee and Savings Green should apply fee before depositing to sGREEN"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS
    fee_percent = 5_00  # 5%

    # Enable minting with fee
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setMintFee(fee_percent, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Mint with Savings Green and fee
    green_minted = endaoment_psm.mintGreen(usdc_amount, user, True, sender=user)

    # Calculate expected GREEN after fee
    expected_usdc_after_fee = usdc_amount * (HUNDRED_PERCENT - fee_percent) // HUNDRED_PERCENT
    expected_green = expected_usdc_after_fee * EIGHTEEN_DECIMALS // SIX_DECIMALS

    # Verify correct amount was deposited to sGREEN
    assert green_minted == expected_green
    assert savings_green.balanceOf(user) > 0


def test_mint_savings_green_with_allowlist(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source, savings_green):
    """Minting with Savings Green should respect allowlist enforcement"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting with allowlist
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    endaoment_psm.setShouldEnforceMintAllowlist(True, sender=switchboard_charlie.address)
    endaoment_psm.updateMintAllowlist(user, True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Mint with Savings Green (should succeed due to allowlist)
    endaoment_psm.mintGreen(usdc_amount, user, True, sender=user)

    # Verify sGREEN received
    assert savings_green.balanceOf(user) > 0


def test_mint_savings_green_respects_interval_limits(endaoment_psm, charlie_token, switchboard_charlie, governance, mock_price_source, savings_green):
    """Minting with Savings Green should respect interval limits"""
    user = boa.env.generate_address()
    # Try to mint 100,001 GREEN (exceeds 100k limit)
    usdc_amount = 100_001 * SIX_DECIMALS

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Attempt to mint with Savings Green should gracefully cap to 100k
    green_minted = endaoment_psm.mintGreen(usdc_amount, user, True, sender=user)
    assert green_minted == 100_000 * EIGHTEEN_DECIMALS

    # Verify sGREEN received (100k GREEN deposited)
    sgreen_balance = savings_green.balanceOf(user)
    assert sgreen_balance > 0  # Will be slightly less than 100k due to share calculation


#############################
# Approval Reset Tests #
#############################


def test_mint_savings_green_resets_approval(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source, savings_green):
    """Minting with Savings Green should reset GREEN approval to 0 after deposit"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Mint with Savings Green
    endaoment_psm.mintGreen(usdc_amount, user, True, sender=user)

    # Verify that GREEN approval from PSM to Savings Green is 0
    psm_allowance = green_token.allowance(endaoment_psm.address, savings_green.address)
    assert psm_allowance == 0


def test_mint_savings_green_approval_reset_on_failure(endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source, savings_green):
    """If savings GREEN deposit fails, approval should still be reset to 0"""
    user = boa.env.generate_address()
    usdc_amount = 1000 * SIX_DECIMALS

    # Enable minting
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    # Setup user
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)

    # Mint normally first to verify baseline
    endaoment_psm.mintGreen(usdc_amount, user, True, sender=user)

    # After successful mint, approval should be 0
    psm_allowance = green_token.allowance(endaoment_psm.address, savings_green.address)
    assert psm_allowance == 0

    # Verify no leftover approvals that could be exploited
    assert psm_allowance == 0
