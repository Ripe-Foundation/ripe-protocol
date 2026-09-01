import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


def test_basic_vault_deposit_validation(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    switchboard_alpha,
    bob,
    teller,
):
    """Test deposit validation logic in BasicVault"""
    # Test deposit with zero address
    with boa.reverts("invalid user or asset"):
        simple_erc20_vault.depositTokensInVault(ZERO_ADDRESS, alpha_token, 100, sender=teller.address)
    with boa.reverts("invalid user or asset"):
        simple_erc20_vault.depositTokensInVault(bob, ZERO_ADDRESS, 100, sender=teller.address)

    # Test deposit with zero amount
    with boa.reverts("invalid deposit amount"):
        simple_erc20_vault.depositTokensInVault(bob, alpha_token, 0, sender=teller.address)

    # Test deposit when paused
    simple_erc20_vault.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        simple_erc20_vault.depositTokensInVault(bob, alpha_token, 100, sender=teller.address)
    simple_erc20_vault.pause(False, sender=switchboard_alpha.address)

    # Test deposit with amount larger than balance
    large_amount = 1000000 * EIGHTEEN_DECIMALS
    small_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(simple_erc20_vault, small_amount, sender=alpha_token_whale)
    with boa.reverts("insufficient vault backing"):
        simple_erc20_vault.depositTokensInVault(
            bob,
            alpha_token,
            large_amount,
            sender=teller.address,
        )
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0


def test_basic_vault_withdrawal_validation(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    switchboard_alpha,
    bob,
    teller,
):
    """Test withdrawal validation logic in BasicVault"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(simple_erc20_vault, deposit_amount, sender=alpha_token_whale)
    simple_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Test withdrawal with zero address
    with boa.reverts("invalid user, asset, or recipient"):
        simple_erc20_vault.withdrawTokensFromVault(ZERO_ADDRESS, alpha_token, 50, bob, sender=teller.address)
    with boa.reverts("invalid user, asset, or recipient"):
        simple_erc20_vault.withdrawTokensFromVault(bob, ZERO_ADDRESS, 50, bob, sender=teller.address)
    with boa.reverts("invalid user, asset, or recipient"):
        simple_erc20_vault.withdrawTokensFromVault(bob, alpha_token, 50, ZERO_ADDRESS, sender=teller.address)

    # Test withdrawal with zero amount
    with boa.reverts("invalid withdrawal amount"):
        simple_erc20_vault.withdrawTokensFromVault(bob, alpha_token, 0, bob, sender=teller.address)

    # Test withdrawal when paused
    simple_erc20_vault.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        simple_erc20_vault.withdrawTokensFromVault(bob, alpha_token, 50, bob, sender=teller.address)
    simple_erc20_vault.pause(False, sender=switchboard_alpha.address)

    # Test withdrawal with amount larger than balance
    large_withdraw = 200 * EIGHTEEN_DECIMALS
    withdrawn, is_depleted = simple_erc20_vault.withdrawTokensFromVault(
        bob, alpha_token, large_withdraw, bob, sender=teller.address
    )
    assert withdrawn == deposit_amount  # Should only withdraw what's available
    assert is_depleted


def test_basic_vault_transfer_validation(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    switchboard_alpha,
    teller,
    auction_house,
):
    """Test transfer validation logic in BasicVault"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(simple_erc20_vault, deposit_amount, sender=alpha_token_whale)
    simple_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Test transfer with zero address
    with boa.reverts("invalid users or asset"):
        simple_erc20_vault.transferBalanceWithinVault(ZERO_ADDRESS, bob, sally, 50, sender=auction_house.address)
    with boa.reverts("invalid users or asset"):
        simple_erc20_vault.transferBalanceWithinVault(alpha_token, ZERO_ADDRESS, sally, 50, sender=auction_house.address)
    with boa.reverts("invalid users or asset"):
        simple_erc20_vault.transferBalanceWithinVault(alpha_token, bob, ZERO_ADDRESS, 50, sender=auction_house.address)

    # Test transfer with zero amount
    with boa.reverts("invalid transfer amount"):
        simple_erc20_vault.transferBalanceWithinVault(alpha_token, bob, sally, 0, sender=auction_house.address)

    # Test transfer when paused
    simple_erc20_vault.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        simple_erc20_vault.transferBalanceWithinVault(alpha_token, bob, sally, 50, sender=auction_house.address)
    simple_erc20_vault.pause(False, sender=switchboard_alpha.address)

    # Test transfer with amount larger than balance
    large_transfer = 200 * EIGHTEEN_DECIMALS
    transferred, is_depleted = simple_erc20_vault.transferBalanceWithinVault(
        alpha_token, bob, sally, large_transfer, sender=auction_house.address
    )
    assert transferred == deposit_amount  # Should only transfer what's available
    assert is_depleted


def test_basic_vault_utility_functions(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
):
    """Test utility functions in BasicVault"""
    # Setup initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(simple_erc20_vault, deposit_amount, sender=alpha_token_whale)
    simple_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Test getTotalAmountForUser
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == deposit_amount

    # Test getTotalAmountForVault
    assert simple_erc20_vault.getTotalAmountForVault(alpha_token) == deposit_amount

    # Test getVaultDataOnDeposit
    vault_data = simple_erc20_vault.getVaultDataOnDeposit(bob, alpha_token)
    assert vault_data.hasPosition
    assert vault_data.numAssets == 1
    assert vault_data.userBalance == deposit_amount
    assert vault_data.totalBalance == deposit_amount

    # Test getUserLootBoxShare
    assert simple_erc20_vault.getUserLootBoxShare(bob, alpha_token) == deposit_amount

    # Test getUserAssetAndAmountAtIndex
    asset, amount = simple_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1)
    assert asset == alpha_token.address
    assert amount == deposit_amount

    # Test getUserAssetAtIndexAndHasBalance
    asset, has_balance = simple_erc20_vault.getUserAssetAtIndexAndHasBalance(bob, 1)
    assert asset == alpha_token.address
    assert has_balance


def test_basic_vault_lootbox_share_tracks_custody_without_mutating_nominal_state(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
):
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    surplus = 5 * EIGHTEEN_DECIMALS

    # A zero nominal balance returns before attempting an external token call.
    assert simple_erc20_vault.getUserLootBoxShare(bob, ZERO_ADDRESS) == 0

    alpha_token.transfer(simple_erc20_vault, deposit_amount, sender=alpha_token_whale)
    simple_erc20_vault.depositTokensInVault(
        bob,
        alpha_token,
        deposit_amount,
        sender=teller.address,
    )

    def assert_nominal_position(expected_share):
        custody_before = alpha_token.balanceOf(simple_erc20_vault)
        assert simple_erc20_vault.getUserLootBoxShare(bob, alpha_token) == expected_share
        assert alpha_token.balanceOf(simple_erc20_vault) == custody_before
        assert simple_erc20_vault.userBalances(bob, alpha_token) == deposit_amount
        assert simple_erc20_vault.totalBalances(alpha_token) == deposit_amount
        assert simple_erc20_vault.userAssets(bob, 1) == alpha_token.address
        assert simple_erc20_vault.indexOfUserAsset(bob, alpha_token) == 1
        assert simple_erc20_vault.numUserAssets(bob) == 2
        assert simple_erc20_vault.getUserAssetAtIndexAndHasBalance(bob, 1) == (
            alpha_token.address,
            True,
        )

    # Exact backing and surplus custody both expose the nominal reward share.
    assert_nominal_position(deposit_amount)
    alpha_token.transfer(simple_erc20_vault, surplus, sender=alpha_token_whale)
    assert_nominal_position(deposit_amount)

    # Strictly deficient custody suppresses the share at every severity.
    alpha_token.transfer(
        alpha_token_whale,
        surplus + 1,
        sender=simple_erc20_vault.address,
    )
    assert alpha_token.balanceOf(simple_erc20_vault) == deposit_amount - 1
    assert_nominal_position(0)

    partial_shortfall = 25 * EIGHTEEN_DECIMALS
    alpha_token.transfer(
        alpha_token_whale,
        partial_shortfall - 1,
        sender=simple_erc20_vault.address,
    )
    assert alpha_token.balanceOf(simple_erc20_vault) == deposit_amount - partial_shortfall
    assert_nominal_position(0)

    alpha_token.transfer(
        alpha_token_whale,
        deposit_amount - partial_shortfall,
        sender=simple_erc20_vault.address,
    )
    assert alpha_token.balanceOf(simple_erc20_vault) == 0
    assert_nominal_position(0)

    # Restoring exactly the missing custody automatically restores the share.
    alpha_token.transfer(simple_erc20_vault, deposit_amount, sender=alpha_token_whale)
    assert_nominal_position(deposit_amount)
