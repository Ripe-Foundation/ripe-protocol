import pytest
import boa
from boa.contracts.base_evm_contract import BoaError

from constants import EIGHTEEN_DECIMALS
from conf_utils import assert_reverted_call, filter_logs
from tests.vaults.ripe_gov_exit_fee_model import (
    DECIMAL_OFFSET,
    HUNDRED_PERCENT,
    assert_exact_exit_claim,
)


def _add_remaining_holder(vault, token, funder, holder, amount, teller):
    token.transfer(vault, amount, sender=funder)
    vault.depositTokensInVault(holder, token, amount, sender=teller.address)


@pytest.fixture(scope="module")
def setupRipeGovVaultConfig(mission_control, setAssetConfig, switchboard_alpha, ripe_token):
    def setupRipeGovVaultConfig(
        _assetWeight = 100_00,
        _minLockDuration = 100,
        _maxLockDuration = 1000,
        _maxLockBoost = 200_00,
        _exitFee = 10_00,
        _canExit = True,
        _shouldFreezeWhenBadDebt = False,
    ):
        # Set up lock terms
        lock_terms = (
            _minLockDuration,
            _maxLockDuration,
            _maxLockBoost,
            _canExit,
            _exitFee,
        )

        # Set RipeGov vault config with asset weight of 100%
        mission_control.setRipeGovVaultConfig(
            ripe_token, 
            _assetWeight,
            _shouldFreezeWhenBadDebt,
            lock_terms, 
            sender=switchboard_alpha.address
        )
        
        # Configure ripe_token for vault_id 2 (ripe_gov_vault)
        setAssetConfig(ripe_token, _vaultIds=[2])

    yield setupRipeGovVaultConfig




def test_ripe_gov_clean_core_zero_share_deposit_rolls_back_and_boundaries_hold(
    setupRipeGovVaultConfig,
    setGeneralConfig,
    setAssetConfig,
    cleanCoreRipeGovFixture,
    ripe_token,
    whale,
    bob,
    teller,
    ledger,
    mission_control,
    boardroom,
    lootbox,
):
    """AUD-024 direct RipeGov path, including clean-core delayed binding."""
    setGeneralConfig()
    setupRipeGovVaultConfig()
    # SwitchboardBravo deliberately rejects unlimited caps. Establish finite
    # test caps before the fixture performs its preservation-sensitive update.
    finite_limit = 10 ** 40
    setAssetConfig(
        ripe_token,
        _vaultIds=[2],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
        _perUserDepositLimit=finite_limit,
        _globalDepositLimit=finite_limit,
    )
    core = cleanCoreRipeGovFixture()
    clean_vault = core["vault"]
    vault_id = core["vault_id"]

    assert mission_control.coreRipeGovVaultId() == vault_id
    assert core["new_vault_ids"] == core["existing_vault_ids"] + [vault_id]
    assert core["support_confirmation"] < core["pointer_confirmation"]

    donation = DECIMAL_OFFSET
    attempted_deposit = 1
    ripe_token.transfer(clean_vault, donation, sender=whale)
    ripe_token.transfer(bob, 3, sender=whale)
    ripe_token.approve(teller, 3, sender=bob)

    assert clean_vault.amountToShares(ripe_token, attempted_deposit, False) == 0
    assert attempted_deposit * DECIMAL_OFFSET // (donation + 1) == 0

    balance_before = ripe_token.balanceOf(bob)
    allowance_before = ripe_token.allowance(bob, teller)
    custody_before = ripe_token.balanceOf(clean_vault)
    user_shares_before = clean_vault.userBalances(bob, ripe_token)
    total_shares_before = clean_vault.totalBalances(ripe_token)
    gov_data_before = clean_vault.userGovData(bob, ripe_token)
    user_gov_points_before = clean_vault.totalUserGovPoints(bob)
    total_gov_points_before = clean_vault.totalGovPoints()
    ledger_data_before = ledger.getDepositLedgerData(bob, vault_id)
    user_points_before = ledger.userDepositPoints(bob, vault_id, ripe_token)
    asset_points_before = ledger.assetDepositPoints(vault_id, ripe_token)
    global_points_before = ledger.globalDepositPoints()
    rewards_before = ledger.ripeRewards()
    # The temporary Boardroom's only persisted field is DeptBasics.isPaused;
    # getRipeHq binds its immutable deployment identity as well.
    boardroom_state_before = (boardroom.isPaused(), boardroom.getRipeHq())
    lootbox_state_before = (
        lootbox.hasUnderscoreRewards(),
        lootbox.underscoreSendInterval(),
        lootbox.lastUnderscoreSend(),
        lootbox.undyDepositRewardsAmount(),
        lootbox.undyYieldBonusAmount(),
    )

    with pytest.raises(BoaError) as exc_info:
        teller.deposit(
            ripe_token,
            attempted_deposit,
            bob,
            clean_vault,
            vault_id,
            sender=bob,
        )
    assert_reverted_call(exc_info.value, "cannot receive 0 shares", teller)

    assert ripe_token.balanceOf(bob) == balance_before
    assert ripe_token.allowance(bob, teller) == allowance_before
    assert ripe_token.balanceOf(clean_vault) == custody_before
    assert clean_vault.userBalances(bob, ripe_token) == user_shares_before
    assert clean_vault.totalBalances(ripe_token) == total_shares_before
    assert clean_vault.userGovData(bob, ripe_token) == gov_data_before
    assert clean_vault.totalUserGovPoints(bob) == user_gov_points_before
    assert clean_vault.totalGovPoints() == total_gov_points_before
    assert ledger.getDepositLedgerData(bob, vault_id) == ledger_data_before
    assert ledger.userDepositPoints(bob, vault_id, ripe_token) == user_points_before
    assert ledger.assetDepositPoints(vault_id, ripe_token) == asset_points_before
    assert ledger.globalDepositPoints() == global_points_before
    assert ledger.ripeRewards() == rewards_before
    assert (boardroom.isPaused(), boardroom.getRipeHq()) == boardroom_state_before
    assert (
        lootbox.hasUnderscoreRewards(),
        lootbox.underscoreSendInterval(),
        lootbox.lastUnderscoreSend(),
        lootbox.undyDepositRewardsAmount(),
        lootbox.undyYieldBonusAmount(),
    ) == lootbox_state_before

    one_share_amount = 2
    assert one_share_amount * DECIMAL_OFFSET // (donation + 1) == 1
    assert teller.deposit(
        ripe_token,
        one_share_amount,
        bob,
        clean_vault,
        vault_id,
        sender=bob,
    ) == one_share_amount
    one_share_logs = teller.get_logs()
    assert clean_vault.userBalances(bob, ripe_token) == 1
    assert clean_vault.totalBalances(ripe_token) == 1
    vault_log = next(
        log for log in one_share_logs if type(log).__name__ == "RipeGovVaultDeposit"
    )
    assert vault_log.user == bob
    assert vault_log.asset == ripe_token.address
    assert vault_log.amount == one_share_amount
    assert vault_log.shares == 1

    ordinary_amount = EIGHTEEN_DECIMALS
    ripe_token.transfer(bob, ordinary_amount, sender=whale)
    ripe_token.approve(teller, ordinary_amount, sender=bob)
    shares_before_ordinary = clean_vault.userBalances(bob, ripe_token)
    assert teller.deposit(
        ripe_token,
        ordinary_amount,
        bob,
        clean_vault,
        vault_id,
        sender=bob,
    ) == ordinary_amount
    assert clean_vault.userBalances(bob, ripe_token) > shares_before_ordinary


def test_ripe_gov_vault_initial_deposit_no_lock(
    ripe_gov_vault, ripe_token, whale, bob, teller, _test, setupRipeGovVaultConfig
):
    """Test initial deposit without lock duration"""
    setupRipeGovVaultConfig()
      
    # Transfer tokens to vault first
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    
    # Deposit tokens
    deposited = ripe_gov_vault.depositTokensInVault(
        bob, ripe_token, deposit_amount, sender=teller.address
    )
    assert deposited == deposit_amount
    
    # Check user balance
    user_amount = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    _test(deposit_amount, user_amount)
    
    # Check governance data is initialized
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    assert userData.govPoints == 0  # No points yet, no time passed

    current_block = boa.env.evm.patch.block_number
    assert userData.unlock == current_block + 100  # Should be exactly minLockDuration (100) blocks from now


def test_ripe_gov_vault_deposit_with_lock_duration(
    ripe_gov_vault, ripe_token, whale, bob, switchboard_alpha, setupRipeGovVaultConfig,
    teller,
):
    """Test deposit with specific lock duration"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    lock_duration = 500  # blocks
    
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    
    # Deposit with lock duration
    deposited = ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, lock_duration, sender=teller.address
    )
    assert deposited == deposit_amount
    
    # Check governance data
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    expected_unlock = boa.env.evm.patch.block_number + lock_duration
    assert userData.unlock == expected_unlock  # unlock should match lock duration


def test_ripe_gov_vault_multiple_deposits_weighted_lock(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test multiple deposits create weighted average lock duration"""
    setupRipeGovVaultConfig()

    first_deposit = 100 * EIGHTEEN_DECIMALS
    second_deposit = 200 * EIGHTEEN_DECIMALS
    
    # First deposit with minimum lock
    ripe_token.transfer(ripe_gov_vault, first_deposit, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, first_deposit, sender=teller.address)
    
    first_unlock = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    
    # Second deposit with longer lock
    ripe_token.transfer(ripe_gov_vault, second_deposit, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, second_deposit, 800, sender=teller.address
    )
    
    second_unlock = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    
    # Second unlock should be between first unlock and full 800 block lock
    assert second_unlock > first_unlock
    assert second_unlock < boa.env.evm.patch.block_number + 800


def test_ripe_gov_vault_deposit_validation(
    ripe_gov_vault, ripe_token, bob, alice, setupRipeGovVaultConfig
):
    """Test deposit validation"""
    setupRipeGovVaultConfig()

    # Test unauthorized caller for depositTokensInVault
    with boa.reverts("only Teller allowed"):
        ripe_gov_vault.depositTokensInVault(bob, ripe_token, 100, sender=alice)
    
    # Test unauthorized caller for depositWithLockDuration
    with boa.reverts("only Teller allowed"):
        ripe_gov_vault.depositTokensWithLockDuration(bob, ripe_token, 100, 500, sender=alice)


def test_ripe_gov_vault_basic_withdrawal(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    _test,
    setupRipeGovVaultConfig,
):
    """Test basic withdrawal after lock period"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Fast forward past unlock time
    unlock_block = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    current_block = boa.env.evm.patch.block_number
    blocks_to_advance = unlock_block - current_block + 1
    boa.env.time_travel(blocks=blocks_to_advance)
    
    # Withdraw tokens
    withdraw_amount = 50 * EIGHTEEN_DECIMALS
    vault_before = ripe_token.balanceOf(ripe_gov_vault)
    recipient_before = ripe_token.balanceOf(alice)
    user_shares_before = ripe_gov_vault.userBalances(bob, ripe_token)
    total_shares_before = ripe_gov_vault.totalBalances(ripe_token)
    withdrawal_shares = ripe_gov_vault.amountToShares(
        ripe_token, withdraw_amount, True
    )
    gov_data_before = ripe_gov_vault.userGovData(bob, ripe_token)
    total_user_points_before = ripe_gov_vault.totalUserGovPoints(bob)
    total_points_before = ripe_gov_vault.totalGovPoints()
    accrued_points = ripe_gov_vault.getLatestGovPoints(
        gov_data_before.lastShares,
        gov_data_before.lastPointsUpdate,
        gov_data_before.unlock,
        gov_data_before.lastTerms,
        100_00,
    )
    points_before_reduction = gov_data_before.govPoints + accrued_points
    expected_asset_points = points_before_reduction - (
        points_before_reduction * withdrawal_shares // gov_data_before.lastShares
    )
    expected_user_points = (
        total_user_points_before - gov_data_before.govPoints + expected_asset_points
    )
    expected_total_points = (
        total_points_before - total_user_points_before + expected_user_points
    )
    
    withdrawn, is_depleted = ripe_gov_vault.withdrawTokensFromVault(
        bob, ripe_token, withdraw_amount, alice, sender=teller.address
    )
    
    # Check withdrawal
    assert withdrawn == withdraw_amount
    assert not is_depleted
    assert vault_before - ripe_token.balanceOf(ripe_gov_vault) == withdrawn
    assert ripe_token.balanceOf(alice) - recipient_before == withdrawn
    assert (
        ripe_gov_vault.userBalances(bob, ripe_token)
        == user_shares_before - withdrawal_shares
    )
    assert (
        ripe_gov_vault.totalBalances(ripe_token)
        == total_shares_before - withdrawal_shares
    )
    gov_data_after = ripe_gov_vault.userGovData(bob, ripe_token)
    assert gov_data_after.lastShares == user_shares_before - withdrawal_shares
    assert gov_data_after.govPoints == expected_asset_points
    assert ripe_gov_vault.totalUserGovPoints(bob) == expected_user_points
    assert ripe_gov_vault.totalGovPoints() == expected_total_points
    
    # Check remaining balance
    remaining = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    _test(deposit_amount - withdraw_amount, remaining)


def test_ripe_gov_vault_inexact_withdrawal_reverts_atomically(
    ripe_gov_vault,
    vault_book,
    governance,
    bob,
    teller,
    mission_control,
    switchboard_alpha,
    setAssetConfig,
):
    fee_token = boa.load(
        "contracts/mock/MockFeeOnTransferErc20.vy",
        governance.address,
        0,
        name="ripe_gov_short_delivery_token",
    )
    vault_id = vault_book.getRegId(ripe_gov_vault)
    assert vault_id != 0
    lock_terms = (100, 1_000, 200_00, True, 10_00)
    mission_control.setRipeGovVaultConfig(
        fee_token,
        100_00,
        False,
        lock_terms,
        sender=switchboard_alpha.address,
    )
    setAssetConfig(
        fee_token,
        _vaultIds=[vault_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    withdrawal_amount = 40 * EIGHTEEN_DECIMALS
    fee_token.transfer(ripe_gov_vault, deposit_amount, sender=governance.address)
    ripe_gov_vault.depositTokensInVault(
        bob, fee_token, deposit_amount, sender=teller.address
    )
    unlock_block = ripe_gov_vault.userGovData(bob, fee_token).unlock
    boa.env.time_travel(
        blocks=unlock_block - boa.env.evm.patch.block_number + 1
    )
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    assert ripe_gov_vault.totalUserGovPoints(bob) > 0
    fee_token.setTransferFee(5_00, sender=governance.address)

    state_before = (
        ripe_gov_vault.userBalances(bob, fee_token),
        ripe_gov_vault.totalBalances(fee_token),
        ripe_gov_vault.getTotalAmountForUser(bob, fee_token),
        ripe_gov_vault.getTotalAmountForVault(fee_token),
        ripe_gov_vault.numUserAssets(bob),
        ripe_gov_vault.numAssets(),
        fee_token.balanceOf(ripe_gov_vault),
        fee_token.balanceOf(bob),
        fee_token.balanceOf(governance),
        ripe_gov_vault.userGovData(bob, fee_token),
        ripe_gov_vault.totalUserGovPoints(bob),
        ripe_gov_vault.totalGovPoints(),
    )

    with boa.reverts("invalid recipient delivery"):
        ripe_gov_vault.withdrawTokensFromVault(
            bob,
            fee_token,
            withdrawal_amount,
            bob,
            sender=teller.address,
        )

    assert (
        ripe_gov_vault.userBalances(bob, fee_token),
        ripe_gov_vault.totalBalances(fee_token),
        ripe_gov_vault.getTotalAmountForUser(bob, fee_token),
        ripe_gov_vault.getTotalAmountForVault(fee_token),
        ripe_gov_vault.numUserAssets(bob),
        ripe_gov_vault.numAssets(),
        fee_token.balanceOf(ripe_gov_vault),
        fee_token.balanceOf(bob),
        fee_token.balanceOf(governance),
        ripe_gov_vault.userGovData(bob, fee_token),
        ripe_gov_vault.totalUserGovPoints(bob),
        ripe_gov_vault.totalGovPoints(),
    ) == state_before


def test_ripe_gov_vault_withdrawal_before_unlock_fails(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that withdrawal fails before unlock time"""
    setupRipeGovVaultConfig(_minLockDuration=100, _maxLockDuration=1000)
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit with lock
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 100, sender=teller.address
    )
    
    # Should revert with "not reached unlock" - trying to withdraw before unlock time
    with boa.reverts("not reached unlock"):
        ripe_gov_vault.withdrawTokensFromVault(bob, ripe_token, deposit_amount, bob, sender=teller.address)


def test_ripe_gov_vault_full_withdrawal_depletes_user(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, setupRipeGovVaultConfig
):
    """Test full withdrawal marks user as depleted"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit and advance time
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    unlock_block = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    current_block = boa.env.evm.patch.block_number
    blocks_to_advance = unlock_block - current_block + 1
    boa.env.time_travel(blocks=blocks_to_advance)
    
    # Withdraw all tokens
    withdrawn, is_depleted = ripe_gov_vault.withdrawTokensFromVault(
        bob, ripe_token, deposit_amount, alice, sender=teller.address
    )
    
    assert withdrawn == deposit_amount
    assert is_depleted
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0


def test_ripe_gov_vault_withdrawal_permission_checks(
    ripe_gov_vault, ripe_token, whale, bob, alice, setupRipeGovVaultConfig
):
    """Test withdrawal permission checks"""
    setupRipeGovVaultConfig()

    # Should revert with "not allowed" - only authorized addresses can call withdrawTokensFromVault
    with boa.reverts("not allowed"):
        ripe_gov_vault.withdrawTokensFromVault(bob, ripe_token, 100, alice, sender=alice)


def test_ripe_gov_vault_basic_transfer_between_users(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, auction_house, setupRipeGovVaultConfig
):
    """Test transferring balance between users"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    transfer_amount = 30 * EIGHTEEN_DECIMALS
    
    # Bob deposits tokens (using teller, not auction house)
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    initial_bob_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    initial_alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    
    # Transfer from Bob to Alice (using auction house)
    transferred, is_depleted = ripe_gov_vault.transferBalanceWithinVault(
        ripe_token, bob, alice, transfer_amount, sender=auction_house.address
    )
    
    assert transferred == transfer_amount
    assert not is_depleted
    
    # Check balances after transfer
    final_bob_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    final_alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    
    assert final_bob_balance == initial_bob_balance - transfer_amount
    assert final_alice_balance == initial_alice_balance + transfer_amount


def test_ripe_gov_vault_transfer_full_balance_depletes_sender(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, auction_house, setupRipeGovVaultConfig
):
    """Test transferring full balance marks sender as depleted"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Bob deposits tokens (using teller)
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Transfer all of Bob's balance to Alice (using auction house)
    transferred, is_depleted = ripe_gov_vault.transferBalanceWithinVault(
        ripe_token, bob, alice, deposit_amount, sender=auction_house.address
    )
    
    assert transferred == deposit_amount
    assert is_depleted
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) == deposit_amount


def test_ripe_gov_vault_transfer_permission_checks(
    ripe_gov_vault, ripe_token, bob, alice, setupRipeGovVaultConfig
):
    """Test transfer permission checks"""
    setupRipeGovVaultConfig()

    # Should revert with "not allowed" - only auction house or credit engine can call transfer
    with boa.reverts("not allowed"):
        ripe_gov_vault.transferBalanceWithinVault(ripe_token, bob, alice, 100, sender=alice)


def test_ripe_gov_vault_adjust_lock_permission_check(
    ripe_gov_vault, ripe_token, bob, alice, setupRipeGovVaultConfig
):
    """Test adjust lock permission checks"""
    setupRipeGovVaultConfig()

    # Should revert with "no perms" - only RipeHq addresses can call adjustLock
    with boa.reverts("only Teller allowed"):
        ripe_gov_vault.adjustLock(bob, ripe_token, 500, sender=alice)


def test_ripe_gov_vault_adjust_lock_no_position_fails(
    ripe_gov_vault, ripe_token, bob, switchboard_alpha, setupRipeGovVaultConfig,
    teller,
):
    """Test adjusting lock with no position fails"""
    setupRipeGovVaultConfig()

    # Should revert with "no lock terms" - no lock terms configured yet (first assertion)
    with boa.reverts("no lock terms"):
        ripe_gov_vault.adjustLock(bob, ripe_token, 500, sender=teller.address)


def test_ripe_gov_vault_adjust_lock_with_terms_but_no_position_fails(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test adjusting lock fails when user has lock terms but no position"""
    setupRipeGovVaultConfig(_minLockDuration=100, _maxLockDuration=1000)
    
    # Deposit for bob to create lock terms, then withdraw everything
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Get unlock time and advance past it
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    unlock_block = userData.unlock
    boa.env.time_travel(blocks=unlock_block - boa.env.evm.patch.block_number + 1)
    
    # Withdraw everything
    ripe_gov_vault.withdrawTokensFromVault(bob, ripe_token, deposit_amount, bob, sender=teller.address)
    
    # Should revert with "no position" - user has lock terms configured but no shares
    with boa.reverts("no position"):
        ripe_gov_vault.adjustLock(bob, ripe_token, 500, sender=teller.address)


def test_ripe_gov_vault_adjust_lock_extend_duration(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test adjusting lock to extend the duration"""
    setupRipeGovVaultConfig(_minLockDuration=100, _maxLockDuration=1000)
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens with minimum lock duration
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Get initial unlock time (should be current block + 100 minimum)
    userData_before = ripe_gov_vault.userGovData(bob, ripe_token)
    initial_unlock = userData_before.unlock
    current_block = boa.env.evm.patch.block_number
    assert initial_unlock == current_block + 100  # Should be minimum lock duration
    
    # Adjust lock to extend duration to 800 blocks
    ripe_gov_vault.adjustLock(bob, ripe_token, 800, sender=teller.address)
    
    # Verify unlock time was updated
    userData_after = ripe_gov_vault.userGovData(bob, ripe_token)
    new_unlock = userData_after.unlock
    expected_unlock = boa.env.evm.patch.block_number + 800  # Should be current block + 800
    
    assert new_unlock == expected_unlock
    assert new_unlock > initial_unlock  # Should be later than initial unlock
    assert userData_after.lastShares == userData_before.lastShares  # Shares unchanged


def test_ripe_gov_vault_adjust_lock_cannot_reduce_duration(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig  
):
    """Test that adjusting lock cannot reduce the duration (earlier unlock time)"""
    setupRipeGovVaultConfig(_minLockDuration=100, _maxLockDuration=1000)
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens with long lock duration
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 800, sender=teller.address  # 800 block lock
    )
    
    # Verify initial unlock time
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    initial_unlock = userData.unlock
    current_block = boa.env.evm.patch.block_number
    assert initial_unlock == current_block + 800
    
    # Try to adjust lock to shorter duration - should revert
    # Even though we're asking for 500 blocks, the new unlock would be current_block + 500
    # which is less than the existing unlock time
    with boa.reverts("new lock cannot be earlier"):
        ripe_gov_vault.adjustLock(bob, ripe_token, 500, sender=teller.address)


def test_ripe_gov_vault_release_lock_no_position_fails(
    ripe_gov_vault, ripe_token, bob, switchboard_alpha, setupRipeGovVaultConfig,
    teller,
):
    """Test releasing lock with no position fails"""
    setupRipeGovVaultConfig()

    # Should revert with "no release needed" - no unlock time set (first assertion)
    with boa.reverts("no release needed"):
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)


def test_ripe_gov_vault_release_lock_permission_check(
    ripe_gov_vault, ripe_token, bob, alice, setupRipeGovVaultConfig
):
    """Test release lock permission checks"""
    setupRipeGovVaultConfig()

    # Should revert with "no perms" - only RipeHq addresses can call releaseLock
    with boa.reverts("only Teller allowed"):
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=alice)


def test_ripe_gov_vault_update_gov_points_permission_check(
    ripe_gov_vault, bob, alice, setupRipeGovVaultConfig
):
    """Test update governance points permission checks"""
    setupRipeGovVaultConfig()

    # Should revert with "no perms" - only RipeHq addresses can call updateUserGovPoints
    with boa.reverts("no perms"):
        ripe_gov_vault.updateUserGovPoints(bob, sender=alice)


def test_ripe_gov_vault_gov_points_accumulate_over_time(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that governance points accumulate over time"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Initial points should be 0
    initial_points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints
    initial_total_points = ripe_gov_vault.totalUserGovPoints(bob)
    assert initial_points == 0
    assert initial_total_points == 0
    
    # Advance time and update points
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    # Points should have accumulated
    updated_points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints
    updated_total_points = ripe_gov_vault.totalUserGovPoints(bob)
    assert updated_points > initial_points
    assert updated_total_points > initial_total_points
    assert updated_total_points == updated_points


def test_ripe_gov_vault_lock_bonus_points(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that locked positions get bonus points compared to unlocked positions"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Bob deposits with minimum lock (no bonus)
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Alice deposits with long lock duration (should get bonus)
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        alice, ripe_token, deposit_amount, 900, sender=teller.address  # Near max lock
    )
    
    # Advance time equally for both
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    ripe_gov_vault.updateUserGovPoints(alice, sender=switchboard_alpha.address)
    
    bob_points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints  # Min lock
    alice_points = ripe_gov_vault.userGovData(alice, ripe_token).govPoints  # Long lock
    
    # Alice should have more points due to lock bonus
    assert alice_points > bob_points
    assert bob_points > 0  # Both should have base points
    assert alice_points > 0


def test_ripe_gov_vault_gov_points_reduction_on_withdrawal(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that governance points are reduced proportionally on withdrawal"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit and accumulate points WHILE LOCKED
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Advance time to accumulate significant points while still locked
    boa.env.time_travel(blocks=50)  # Accumulate points for 50 blocks
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    initial_points = ripe_gov_vault.totalUserGovPoints(bob)
    assert initial_points > 0
    
    # Now advance past unlock time so we can withdraw
    unlock_block = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    current_block = boa.env.evm.patch.block_number
    blocks_to_advance = unlock_block - current_block + 1
    boa.env.time_travel(blocks=blocks_to_advance)

    # Update points to include all time advancement, then capture points before withdrawal
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    points_before = ripe_gov_vault.totalUserGovPoints(bob)
    assert points_before > initial_points  # Should have accumulated more points

    # Withdraw half the position
    ripe_gov_vault.withdrawTokensFromVault(
        bob, ripe_token, deposit_amount // 2, alice, sender=teller.address
    )
    
    # Points should be reduced due to proportional reduction on withdrawal
    points_after = ripe_gov_vault.totalUserGovPoints(bob)
    assert points_after < points_before


def test_ripe_gov_vault_total_gov_points_tracking(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that total governance points are tracked correctly across users"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Bob deposits
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Alice deposits
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(alice, ripe_token, deposit_amount, sender=teller.address)
    
    # Advance time and update points for both
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    ripe_gov_vault.updateUserGovPoints(alice, sender=switchboard_alpha.address)
    
    bob_points = ripe_gov_vault.totalUserGovPoints(bob)
    alice_points = ripe_gov_vault.totalUserGovPoints(alice)
    total_points = ripe_gov_vault.totalGovPoints()
    
    # Total should equal sum of individual user points
    assert total_points == bob_points + alice_points
    assert bob_points > 0
    assert alice_points > 0


def test_ripe_gov_vault_lootbox_share_calculation(
    ripe_gov_vault, ripe_token, whale, bob, teller, setupRipeGovVaultConfig
):
    """Test lootbox share calculation for rewards"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Get lootbox share
    lootbox_share = ripe_gov_vault.getUserLootBoxShare(bob, ripe_token)
    assert lootbox_share > 0


def test_ripe_gov_vault_lootbox_share_no_position(
    ripe_gov_vault, ripe_token, bob, setupRipeGovVaultConfig
):
    """Test lootbox share with no position"""
    setupRipeGovVaultConfig()

    # Get lootbox share with no deposit
    lootbox_share = ripe_gov_vault.getUserLootBoxShare(bob, ripe_token)
    assert lootbox_share == 0


def test_ripe_gov_vault_user_asset_enumeration(
    ripe_gov_vault, ripe_token, whale, bob, teller, setupRipeGovVaultConfig
):
    """Test user asset enumeration functions"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Initially no assets
    asset, has_balance = ripe_gov_vault.getUserAssetAtIndexAndHasBalance(bob, 1)
    assert not has_balance
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Now should have balance
    asset, has_balance = ripe_gov_vault.getUserAssetAtIndexAndHasBalance(bob, 1)
    assert has_balance
    assert asset == ripe_token.address

    # Test asset and amount at index
    asset, amount = ripe_gov_vault.getUserAssetAndAmountAtIndex(bob, 1)
    assert asset == ripe_token.address
    assert amount > 0


def test_ripe_gov_vault_total_amount_functions(
    ripe_gov_vault, ripe_token, whale, bob, teller, setupRipeGovVaultConfig
):
    """Test total amount utility functions"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Initially zero
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForVault(ripe_token) == 0
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Check amounts
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == deposit_amount
    assert ripe_gov_vault.getTotalAmountForVault(ripe_token) == deposit_amount


def test_ripe_gov_vault_configuration_updates_after_deposit(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that configuration updates are handled properly for existing positions"""
    setupRipeGovVaultConfig()
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit with initial config
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Verify initial unlock time is set
    userData_before = ripe_gov_vault.userGovData(bob, ripe_token)
    assert userData_before.unlock > boa.env.evm.patch.block_number  # Should have future unlock
    
    # Update configuration with WORSE terms (this should reset unlock to 0)
    setupRipeGovVaultConfig(
        _assetWeight=150_00,  # increased (doesn't affect unlock reset)
        _minLockDuration=200,  # increased (doesn't affect unlock reset)
        _maxLockDuration=2000,  # increased (doesn't affect unlock reset)
        _maxLockBoost=300_00,  # increased (doesn't affect unlock reset)
        _exitFee=20_00,  # INCREASED from 10_00 - makes terms worse
        _canExit=False,  # DISABLED from True - makes terms worse
        _shouldFreezeWhenBadDebt=False,  # Added new parameter
    )
    
    # Update user points (should refresh terms and reset unlock)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    # User data should reflect that unlock was reset due to worse terms
    userData_after = ripe_gov_vault.userGovData(bob, ripe_token)
    
    # When terms get worse (exit disabled AND exit fees increased), unlock MUST be reset to 0
    assert userData_after.unlock == 0  # Should be exactly 0 when terms get worse
    assert userData_after.lastShares > 0  # Should still have shares


def test_ripe_gov_vault_lock_terms_enforcement(
    ripe_gov_vault, ripe_token, whale, bob, switchboard_alpha, setupRipeGovVaultConfig,
    teller,
):
    """Test that lock terms are enforced (min/max durations)"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Test with below minimum lock duration (should be increased to minimum)
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 50, sender=teller.address  # Below min (100)
    )
    
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    expected_min_unlock = boa.env.evm.patch.block_number + 100  # Should be enforced to minimum
    assert userData.unlock == expected_min_unlock
    
    # Test with above maximum lock duration (should be capped to maximum)
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 1500, sender=teller.address  # Above max (1000)
    )
    
    # The unlock should be a weighted average between previous min lock (100) and max lock (1000)
    # With equal deposits, this should be (100 + 1000) / 2 = 550 blocks from current time
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    current_block = boa.env.evm.patch.block_number
    expected_unlock = current_block + 550  # Weighted average of 100 and 1000
    assert userData.unlock == expected_unlock


def test_ripe_gov_vault_release_lock_when_cannot_exit(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that release lock fails when canExit is false"""
    # Setup config with exit disabled
    setupRipeGovVaultConfig(_canExit=False)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Should revert with "cannot exit" - exit is disabled in config
    with boa.reverts("cannot exit"):
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)


def test_ripe_gov_vault_release_lock_when_no_unlock_needed(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that release lock fails when no release is needed"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Fast forward past unlock time
    unlock_block = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    current_block = boa.env.evm.patch.block_number
    blocks_to_advance = unlock_block - current_block + 1
    boa.env.time_travel(blocks=blocks_to_advance)
    
    # Should revert with "no release needed" - already past unlock time
    with boa.reverts("no release needed"):
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)


def test_ripe_gov_vault_release_lock_successful_with_exit_fee(
    ripe_gov_vault, ripe_token, whale, bob, alice, switchboard_alpha, setupRipeGovVaultConfig,
    teller,
):
    """Test that release lock works successfully and charges exit fee"""
    # Setup with exit enabled and 10% exit fee
    setupRipeGovVaultConfig(_minLockDuration=100, _maxLockDuration=1000, _canExit=True, _exitFee=10_00)
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens with lock duration
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 500, sender=teller.address  # 500 block lock
    )
    _add_remaining_holder(ripe_gov_vault, ripe_token, whale, alice, deposit_amount, teller)
    
    # Verify initial state - should be locked
    userData_before = ripe_gov_vault.userGovData(bob, ripe_token)
    vault_balance_before = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    shares_before = userData_before.lastShares
    total_shares_before = ripe_gov_vault.totalBalances(ripe_token)
    custody_before = ripe_token.balanceOf(ripe_gov_vault)
    unlock_before = userData_before.unlock
    current_block = boa.env.evm.patch.block_number
    
    assert unlock_before == current_block + 500  # Should be locked for 500 blocks
    assert vault_balance_before > 0  # Should have vault balance
    assert shares_before > 0  # Should have shares
    
    # Release lock early (should charge 10% exit fee)
    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)
    
    # Verify state after release
    userData_after = ripe_gov_vault.userGovData(bob, ripe_token)
    vault_balance_after = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    shares_after = userData_after.lastShares
    total_shares_after = ripe_gov_vault.totalBalances(ripe_token)
    unlock_after = userData_after.unlock
    
    # 1. Unlock should be reset to 0 (no longer locked)
    assert unlock_after == 0
    
    # 2. The exact post-state claim must charge the economic 10% fee
    assert_exact_exit_claim(
        shares_before,
        total_shares_before,
        custody_before,
        10_00,
        shares_after,
        total_shares_after,
    )
    
    # 3. Vault balance should be reduced (exact amount may vary due to exchange rates)
    assert vault_balance_after < vault_balance_before
    
    # 4. Verify exit fee was charged from shares
    shares_fee_charged = shares_before - shares_after
    assert shares_fee_charged > shares_before * 10_00 // HUNDRED_PERCENT


def test_ripe_gov_vault_release_lock_state_changes(
    ripe_gov_vault, ripe_token, whale, bob, alice, switchboard_alpha, setupRipeGovVaultConfig,
    teller,
):
    """Test that release lock properly updates all state variables"""
    # Setup with exit enabled and 5% exit fee
    setupRipeGovVaultConfig(_minLockDuration=200, _maxLockDuration=800, _canExit=True, _exitFee=5_00)
    
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    
    # Deposit tokens with lock duration
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 600, sender=teller.address  # 600 block lock
    )
    _add_remaining_holder(ripe_gov_vault, ripe_token, whale, alice, deposit_amount, teller)
    
    # Advance some time to accumulate governance points while locked
    boa.env.time_travel(blocks=50)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    # Capture state before release
    userData_before = ripe_gov_vault.userGovData(bob, ripe_token)
    vault_balance_before = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    shares_before = userData_before.lastShares
    total_shares_before = ripe_gov_vault.totalBalances(ripe_token)
    custody_before = ripe_token.balanceOf(ripe_gov_vault)
    
    assert userData_before.unlock > boa.env.evm.patch.block_number  # Still locked
    assert vault_balance_before > 0  # Has vault balance
    assert shares_before > 0  # Has shares
    
    # Release lock
    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)
    
    # Verify all state changes
    userData_after = ripe_gov_vault.userGovData(bob, ripe_token)
    vault_balance_after = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    shares_after = userData_after.lastShares
    total_shares_after = ripe_gov_vault.totalBalances(ripe_token)
    
    # 1. Unlock should be reset to 0
    assert userData_after.unlock == 0
    
    # 2. The exact post-state claim must charge the economic 5% fee
    assert_exact_exit_claim(
        shares_before,
        total_shares_before,
        custody_before,
        5_00,
        shares_after,
        total_shares_after,
    )
    
    # 3. Vault balance should be reduced (but exact amount may vary)
    assert vault_balance_after < vault_balance_before
    
    # 4. Verify the shares fee amount is correct
    shares_fee_charged = shares_before - shares_after
    assert shares_fee_charged > shares_before * 5_00 // HUNDRED_PERCENT
    
    # 5. User retains a nonzero post-fee position
    assert shares_after != 0


def test_ripe_gov_vault_complex_points_scenario(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, auction_house, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test complex scenario with multiple operations affecting governance points"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Bob deposits with lock
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 800, sender=teller.address
    )
    
    # Alice deposits with minimum lock
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(alice, ripe_token, deposit_amount, sender=teller.address)
    
    # Advance time to accumulate points
    boa.env.time_travel(blocks=200)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    ripe_gov_vault.updateUserGovPoints(alice, sender=switchboard_alpha.address)
    
    bob_points_before = ripe_gov_vault.totalUserGovPoints(bob)
    alice_points_before = ripe_gov_vault.totalUserGovPoints(alice)
    total_points_before = ripe_gov_vault.totalGovPoints()
    
    # Bob should have more points due to longer lock
    assert bob_points_before > alice_points_before
    assert total_points_before == bob_points_before + alice_points_before
    
    # Transfer some of Bob's balance to Alice
    transfer_amount = 30 * EIGHTEEN_DECIMALS
    ripe_gov_vault.transferBalanceWithinVault(
        ripe_token, bob, alice, transfer_amount, sender=auction_house.address
    )
    
    # Check points after transfer
    bob_points_after = ripe_gov_vault.totalUserGovPoints(bob)
    alice_points_after = ripe_gov_vault.totalUserGovPoints(alice)
    total_points_after = ripe_gov_vault.totalGovPoints()
    
    # Bob should have fewer points, and total should be preserved
    assert bob_points_after < bob_points_before
    # Note: Transfer logic may not immediately give Alice more points in the same block
    # The important thing is that the system maintains consistency
    assert total_points_after == bob_points_after + alice_points_after


# Additional tests using different vault configurations

def test_ripe_gov_vault_high_asset_weight_more_points(
    ripe_gov_vault, ripe_token, whale, bob, charlie, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that higher asset weight results in more governance points"""
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Test with normal weight first using bob
    setupRipeGovVaultConfig(_assetWeight=100_00)  # 100% weight
    
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    normal_weight_points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints  # Use asset-specific points
    
    # Setup with high asset weight using charlie (different user)
    setupRipeGovVaultConfig(_assetWeight=300_00)  # 300% weight
    
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(charlie, ripe_token, deposit_amount, sender=teller.address)
    
    # Advance time and update points
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(charlie, sender=switchboard_alpha.address)
    
    high_weight_points = ripe_gov_vault.userGovData(charlie, ripe_token).govPoints  # Use asset-specific points
    
    # Higher asset weight (300%) should result in more points than normal weight (100%)
    assert high_weight_points > normal_weight_points
    assert normal_weight_points > 0  # Both should have some points
    assert high_weight_points > 0


def test_ripe_gov_vault_zero_asset_weight_no_points(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that zero asset weight doesn't break functionality"""
    # Setup with zero asset weight
    setupRipeGovVaultConfig(_assetWeight=0)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Advance time and update points
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    # GOV-WEIGHT-01: zero weight means zero points. This previously asserted only
    # `>= 0`, which is vacuous for a uint256 -- it passed while the multiplier was
    # being skipped and the balance was accruing full unweighted points.
    points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints
    total_points = ripe_gov_vault.totalUserGovPoints(bob)

    assert points == 0
    assert total_points == 0
    assert total_points == points  # Should be consistent

    # the deposit itself must still be intact -- zero points, not a failed deposit
    assert ripe_gov_vault.userGovData(bob, ripe_token).lastShares > 0


def test_ripe_gov_vault_max_lock_boost_comparison(
    ripe_gov_vault, ripe_token, whale, bob, charlie, switchboard_alpha, setupRipeGovVaultConfig,
    teller,
):
    """Test that higher max lock boost results in more bonus points"""
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Test with normal boost first using bob
    setupRipeGovVaultConfig(_maxLockBoost=200_00)  # 200% boost (default)

    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 1000, sender=teller.address  # Max lock
    )
    
    # Advance time and update points
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    normal_boost_points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints
    
    # Setup with high lock boost using charlie
    setupRipeGovVaultConfig(_maxLockBoost=500_00)  # 500% boost

    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        charlie, ripe_token, deposit_amount, 1000, sender=teller.address  # Max lock
    )
    
    # Advance time and update points
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(charlie, sender=switchboard_alpha.address)
    
    high_boost_points = ripe_gov_vault.userGovData(charlie, ripe_token).govPoints
    
    # Higher max lock boost (500%) should result in more points than normal boost (200%)
    assert high_boost_points > normal_boost_points
    assert normal_boost_points > 0  # Both should have some points
    assert high_boost_points > 0


def test_ripe_gov_vault_short_lock_range_enforcement(
    ripe_gov_vault, ripe_token, whale, bob, switchboard_alpha, setupRipeGovVaultConfig,
    teller,
):
    """Test vault with very short lock duration range"""
    # Setup with narrow lock range
    setupRipeGovVaultConfig(_minLockDuration=90, _maxLockDuration=110)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Test that lock durations are properly clamped to range
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 200, sender=teller.address  # Should be clamped to 110
    )
    
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    expected_unlock = boa.env.evm.patch.block_number + 110  # Should be clamped to max
    assert userData.unlock == expected_unlock


# util funciton tests


def test_ripe_gov_vault_get_latest_gov_points_zero_shares(ripe_gov_vault):
    """Test that getLatestGovPoints returns 0 when lastShares is 0"""
    
    # Test with zero shares
    points = ripe_gov_vault.getLatestGovPoints(
        0,  # lastShares = 0
        100,  # lastPointsUpdate
        200,  # unlock
        (50, 1000, 200_00, True, 10_00),  # terms
        100_00  # weight
    )
    assert points == 0


def test_ripe_gov_vault_get_latest_gov_points_no_time_elapsed(ripe_gov_vault):
    """Test that getLatestGovPoints returns 0 when no time has elapsed"""
    
    current_block = boa.env.evm.patch.block_number
    
    # Test with same block as last update
    points = ripe_gov_vault.getLatestGovPoints(
        1000 * 10**18,  # lastShares
        current_block,  # lastPointsUpdate = current block
        current_block + 100,  # unlock
        (50, 1000, 200_00, True, 10_00),  # terms
        100_00  # weight
    )
    assert points == 0


def test_ripe_gov_vault_get_latest_gov_points_with_asset_weight(ripe_gov_vault):
    """Test getLatestGovPoints with different asset weights"""
    
    # Advance time to ensure we have a reasonable current block
    boa.env.time_travel(blocks=2000)
    current_block = boa.env.evm.patch.block_number
    
    shares = 1000 * 10**18  # 1000 normalized shares
    time_elapsed = 100
    past_block = current_block - time_elapsed  # lastPointsUpdate in the past
    
    # Test with 100% weight (normal)
    points_100 = ripe_gov_vault.getLatestGovPoints(
        shares,
        past_block,  # lastPointsUpdate
        current_block + 500,  # still locked
        (0, 0, 0, False, 0),  # no lock terms
        100_00  # 100% weight
    )
    
    # Test with 200% weight (2x multiplier)
    points_200 = ripe_gov_vault.getLatestGovPoints(
        shares,
        past_block,
        current_block + 500,
        (0, 0, 0, False, 0),  # no lock terms
        200_00  # 200% weight
    )
    
    # Test with 50% weight (0.5x multiplier)
    points_50 = ripe_gov_vault.getLatestGovPoints(
        shares,
        past_block,
        current_block + 500,
        (0, 0, 0, False, 0),  # no lock terms
        50_00  # 50% weight
    )
    
    # Test with 0% weight (no points)
    points_0 = ripe_gov_vault.getLatestGovPoints(
        shares,
        past_block,
        current_block + 500,
        (0, 0, 0, False, 0),  # no lock terms
        0  # 0% weight
    )

    # Expected: 1000 shares * 100 blocks = 100,000 base points
    expected_base = 1000 * time_elapsed
    assert points_100 == expected_base
    assert points_200 == expected_base * 2
    assert points_50 == expected_base // 2
    # GOV-WEIGHT-01: 0% weight zeroes the points. This previously asserted
    # `points_0 == expected_base` with the note that a zero weight "doesn't zero out
    # points, it just doesn't apply weight multiplier" -- that was the DV-07 defect,
    # not intended behavior, and a zero weight now earns nothing.
    assert points_0 == 0


def test_ripe_gov_vault_get_latest_gov_points_with_lock_bonus(ripe_gov_vault):
    """Test getLatestGovPoints includes lock bonus when terms are set"""
    
    # Advance time to ensure we have a reasonable current block
    boa.env.time_travel(blocks=2000)
    current_block = boa.env.evm.patch.block_number
    
    shares = 1000 * 10**18
    time_elapsed = 100
    past_block = current_block - time_elapsed
    
    # Test without lock terms (no bonus)
    points_no_bonus = ripe_gov_vault.getLatestGovPoints(
        shares,
        past_block,
        current_block + 500,
        (0, 0, 0, False, 0),  # no lock terms
        100_00
    )
    
    # Test with lock terms (should have bonus)
    points_with_bonus = ripe_gov_vault.getLatestGovPoints(
        shares,
        past_block,
        current_block + 500,  # 500 blocks remaining
        (100, 1000, 200_00, True, 10_00),  # lock terms with 200% max boost
        100_00
    )
    
    # Should have more points with lock bonus
    assert points_with_bonus > points_no_bonus


def test_ripe_gov_vault_get_lock_bonus_points_zero_cases(ripe_gov_vault):
    """Test getLockBonusPoints returns 0 in various edge cases"""
    
    # Advance time to ensure we have a reasonable current block
    boa.env.time_travel(blocks=2000)
    current_block = boa.env.evm.patch.block_number
    
    terms = (100, 1000, 200_00, True, 10_00)  # min=100, max=1000, boost=200%
    
    # Test with zero points
    bonus = ripe_gov_vault.getLockBonusPoints(0, current_block + 500, terms)
    assert bonus == 0
    
    # Test with already unlocked (unlock <= current block)
    bonus = ripe_gov_vault.getLockBonusPoints(1000, current_block, terms)
    assert bonus == 0
    
    # Test with unlock in the past (use absolute past block number)
    past_unlock = 100  # Use absolute block number that's definitely in the past
    bonus = ripe_gov_vault.getLockBonusPoints(1000, past_unlock, terms)
    assert bonus == 0


def test_ripe_gov_vault_get_lock_bonus_points_below_min_lock(ripe_gov_vault):
    """Test getLockBonusPoints returns 0 when remaining lock is below minimum"""
    
    current_block = boa.env.evm.patch.block_number
    terms = (100, 1000, 200_00, True, 10_00)  # min=100, max=1000, boost=200%
    
    # Test with remaining lock duration below minimum (50 < 100)
    bonus = ripe_gov_vault.getLockBonusPoints(1000, current_block + 50, terms)
    assert bonus == 0


def test_ripe_gov_vault_get_lock_bonus_points_calculation(ripe_gov_vault):
    """Test getLockBonusPoints calculation logic"""
    
    current_block = boa.env.evm.patch.block_number
    terms = (100, 1000, 200_00, True, 10_00)  # min=100, max=1000, boost=200%
    base_points = 10000
    
    # Test at minimum lock (should give 0 bonus)
    bonus_min = ripe_gov_vault.getLockBonusPoints(base_points, current_block + 100, terms)
    assert bonus_min == 0
    
    # Test at maximum lock (should give full 200% bonus)
    bonus_max = ripe_gov_vault.getLockBonusPoints(base_points, current_block + 1000, terms)
    expected_max_bonus = base_points * 200_00 // 100_00  # 200% of base points
    assert bonus_max == expected_max_bonus
    
    # Test at halfway point (should give 100% bonus)
    halfway_lock = 100 + (1000 - 100) // 2  # 550 blocks
    bonus_half = ripe_gov_vault.getLockBonusPoints(base_points, current_block + halfway_lock, terms)
    expected_half_bonus = base_points * 100_00 // 100_00  # 100% of base points
    assert bonus_half == expected_half_bonus


def test_ripe_gov_vault_get_lock_bonus_points_higher_than_max(ripe_gov_vault):
    """Test getLockBonusPoints caps at maxLockDuration when unlock is higher"""
    
    current_block = boa.env.evm.patch.block_number
    terms = (100, 1000, 200_00, True, 10_00)  # min=100, max=1000, boost=200%
    base_points = 10000
    
    # Test with unlock way beyond max (should still use max for calculation)
    bonus_beyond = ripe_gov_vault.getLockBonusPoints(base_points, current_block + 2000, terms)
    bonus_at_max = ripe_gov_vault.getLockBonusPoints(base_points, current_block + 1000, terms)
    
    # Should be the same since it caps at maxLockDuration
    assert bonus_beyond == bonus_at_max


def test_ripe_gov_vault_get_weighted_lock_no_previous_balance(ripe_gov_vault):
    """Test getWeightedLockOnTokenDeposit with no previous balance"""
    
    current_block = boa.env.evm.patch.block_number
    precision = 10**18
    terms = (100, 1000, 200_00, True, 10_00)
    
    # Test with prevShares below PRECISION
    unlock = ripe_gov_vault.getWeightedLockOnTokenDeposit(
        1000 * precision,  # newShares
        500,  # newLockDuration
        terms,
        precision - 1,  # prevShares < PRECISION
        current_block + 200  # prevUnlock (irrelevant)
    )
    
    # Should just return current block + new lock duration
    assert unlock == current_block + 500


def test_ripe_gov_vault_get_weighted_lock_equal_shares(ripe_gov_vault):
    """Test getWeightedLockOnTokenDeposit with equal share amounts"""
    
    current_block = boa.env.evm.patch.block_number
    precision = 10**18
    terms = (100, 1000, 200_00, True, 10_00)
    
    # Test with equal shares but different lock durations
    unlock = ripe_gov_vault.getWeightedLockOnTokenDeposit(
        1000 * precision,  # newShares
        600,  # newLockDuration
        terms,
        1000 * precision,  # prevShares (same amount)
        current_block + 400  # prevUnlock (400 blocks remaining)
    )
    
    # Should be weighted average: (1000*400 + 1000*600) / (1000+1000) = 500
    expected_unlock = current_block + 500
    assert unlock == expected_unlock


def test_ripe_gov_vault_get_weighted_lock_different_ratios(ripe_gov_vault):
    """Test getWeightedLockOnTokenDeposit with different share ratios"""
    
    current_block = boa.env.evm.patch.block_number
    precision = 10**18
    terms = (100, 1000, 200_00, True, 10_00)
    
    # Test with 3:1 ratio (new deposit 3x larger)
    unlock = ripe_gov_vault.getWeightedLockOnTokenDeposit(
        3000 * precision,  # newShares (3x larger)
        800,  # newLockDuration
        terms,
        1000 * precision,  # prevShares
        current_block + 200  # prevUnlock (200 blocks remaining)
    )
    
    # Weighted average: (1000*200 + 3000*800) / (1000+3000) = (200k + 2.4M) / 4000 = 650
    expected_unlock = current_block + 650
    assert unlock == expected_unlock


def test_ripe_gov_vault_get_weighted_lock_already_unlocked(ripe_gov_vault):
    """Test getWeightedLockOnTokenDeposit when previous position is already unlocked"""
    
    # Advance time to ensure we have a reasonable current block
    boa.env.time_travel(blocks=2000)
    current_block = boa.env.evm.patch.block_number
    
    precision = 10**18
    terms = (100, 1000, 200_00, True, 10_00)
    
    # Test with previous unlock in the past (already unlocked)
    past_unlock = 100  # Use absolute block number that's definitely in the past
    unlock = ripe_gov_vault.getWeightedLockOnTokenDeposit(
        1000 * precision,  # newShares
        500,  # newLockDuration
        terms,
        2000 * precision,  # prevShares
        past_unlock  # prevUnlock (already passed)
    )
    
    # Previous duration should be treated as 1 (minimum)
    # Weighted average: (2000*1 + 1000*500) / (2000+1000) = 502000/3000 ≈ 167
    expected_unlock = current_block + 167
    assert unlock == expected_unlock


def test_ripe_gov_vault_are_key_terms_same_identical(ripe_gov_vault):
    """Test areKeyTermsSame returns True for identical terms"""
    
    terms1 = (100, 1000, 200_00, True, 10_00)
    terms2 = (100, 1000, 200_00, True, 10_00)
    
    assert ripe_gov_vault.areKeyTermsSame(terms1, terms2)


def test_ripe_gov_vault_are_key_terms_same_can_exit_worse(ripe_gov_vault):
    """Test areKeyTermsSame returns False when canExit goes from True to False"""
    
    old_terms = (100, 1000, 200_00, True, 10_00)   # canExit = True
    new_terms = (100, 1000, 200_00, False, 10_00)  # canExit = False
    
    assert not ripe_gov_vault.areKeyTermsSame(new_terms, old_terms)


def test_ripe_gov_vault_are_key_terms_same_can_exit_better(ripe_gov_vault):
    """Test areKeyTermsSame returns True when canExit goes from False to True"""
    
    old_terms = (100, 1000, 200_00, False, 10_00)  # canExit = False
    new_terms = (100, 1000, 200_00, True, 10_00)   # canExit = True
    
    assert ripe_gov_vault.areKeyTermsSame(new_terms, old_terms)


def test_ripe_gov_vault_are_key_terms_same_boost_worse(ripe_gov_vault):
    """Test areKeyTermsSame returns False when maxLockBoost decreases"""
    
    old_terms = (100, 1000, 200_00, True, 10_00)  # boost = 200%
    new_terms = (100, 1000, 150_00, True, 10_00)  # boost = 150%
    
    assert not ripe_gov_vault.areKeyTermsSame(new_terms, old_terms)


def test_ripe_gov_vault_are_key_terms_same_boost_better(ripe_gov_vault):
    """Test areKeyTermsSame returns True when maxLockBoost increases"""
    
    old_terms = (100, 1000, 150_00, True, 10_00)  # boost = 150%
    new_terms = (100, 1000, 200_00, True, 10_00)  # boost = 200%
    
    assert ripe_gov_vault.areKeyTermsSame(new_terms, old_terms)


def test_ripe_gov_vault_are_key_terms_same_min_lock_increase_allowed(ripe_gov_vault):
    """Test areKeyTermsSame returns True when minLockDuration increases (stricter terms)"""
    
    old_terms = (100, 1000, 200_00, True, 10_00)  # minLock = 100
    new_terms = (150, 1000, 200_00, True, 10_00)  # minLock = 150 (stricter)
    
    assert ripe_gov_vault.areKeyTermsSame(new_terms, old_terms)


def test_ripe_gov_vault_are_key_terms_same_min_lock_decrease_worse(ripe_gov_vault):
    """Test areKeyTermsSame returns False when minLockDuration decreases (terms get worse)"""
    
    old_terms = (150, 1000, 200_00, True, 10_00)  # minLock = 150
    new_terms = (100, 1000, 200_00, True, 10_00)  # minLock = 100 (looser, worse terms)
    
    assert not ripe_gov_vault.areKeyTermsSame(new_terms, old_terms)


def test_ripe_gov_vault_are_key_terms_same_exit_fee_worse(ripe_gov_vault):
    """Test areKeyTermsSame returns False when exitFee increases"""
    
    old_terms = (100, 1000, 200_00, True, 10_00)  # exitFee = 10%
    new_terms = (100, 1000, 200_00, True, 20_00)  # exitFee = 20%
    
    assert not ripe_gov_vault.areKeyTermsSame(new_terms, old_terms)


def test_ripe_gov_vault_are_key_terms_same_exit_fee_better(ripe_gov_vault):
    """Test areKeyTermsSame returns True when exitFee decreases"""
    
    old_terms = (100, 1000, 200_00, True, 20_00)  # exitFee = 20%
    new_terms = (100, 1000, 200_00, True, 10_00)  # exitFee = 10%
    
    assert ripe_gov_vault.areKeyTermsSame(new_terms, old_terms)


def test_ripe_gov_vault_are_key_terms_same_max_lock_duration_change(ripe_gov_vault):
    """Test areKeyTermsSame allows maxLockDuration changes (not a key term)"""
    
    old_terms = (100, 1000, 200_00, True, 10_00)  # maxLock = 1000
    new_terms = (100, 500, 200_00, True, 10_00)   # maxLock = 500
    
    # maxLockDuration changes are allowed (handled in refreshUnlock)
    assert ripe_gov_vault.areKeyTermsSame(new_terms, old_terms)


def test_ripe_gov_vault_refresh_unlock_terms_same(ripe_gov_vault):
    """Test refreshUnlock keeps unlock when terms are the same"""
    
    current_block = boa.env.evm.patch.block_number
    prev_unlock = current_block + 500
    terms = (100, 1000, 200_00, True, 10_00)
    
    new_unlock = ripe_gov_vault.refreshUnlock(prev_unlock, terms, terms)
    assert new_unlock == prev_unlock


def test_ripe_gov_vault_refresh_unlock_terms_worse(ripe_gov_vault):
    """Test refreshUnlock resets to 0 when terms get worse"""
    
    current_block = boa.env.evm.patch.block_number
    prev_unlock = current_block + 500
    old_terms = (100, 1000, 200_00, True, 10_00)  # canExit = True
    new_terms = (100, 1000, 200_00, False, 10_00) # canExit = False (worse)
    
    new_unlock = ripe_gov_vault.refreshUnlock(prev_unlock, new_terms, old_terms)
    assert new_unlock == 0


def test_ripe_gov_vault_refresh_unlock_max_duration_decreased(ripe_gov_vault):
    """Test refreshUnlock caps at new maxLockDuration when it's reduced"""
    
    current_block = boa.env.evm.patch.block_number
    prev_unlock = current_block + 1000  # locked for 1000 blocks
    old_terms = (100, 1200, 200_00, True, 10_00)  # maxLock = 1200
    new_terms = (100, 800, 200_00, True, 10_00)   # maxLock = 800 (reduced)
    
    new_unlock = ripe_gov_vault.refreshUnlock(prev_unlock, new_terms, old_terms)
    
    # Should be capped at current_block + 800 (new max)
    expected_unlock = current_block + 800
    assert new_unlock == expected_unlock


def test_ripe_gov_vault_refresh_unlock_max_duration_increased(ripe_gov_vault):
    """Test refreshUnlock keeps original unlock when maxLockDuration increases"""
    
    current_block = boa.env.evm.patch.block_number
    prev_unlock = current_block + 800   # locked for 800 blocks
    old_terms = (100, 1000, 200_00, True, 10_00)  # maxLock = 1000
    new_terms = (100, 1200, 200_00, True, 10_00)  # maxLock = 1200 (increased)
    
    new_unlock = ripe_gov_vault.refreshUnlock(prev_unlock, new_terms, old_terms)
    
    # Should keep original unlock since it's within new max
    assert new_unlock == prev_unlock


def test_ripe_gov_vault_refresh_unlock_terms_worse_and_max_changed(ripe_gov_vault):
    """Test refreshUnlock handles both terms getting worse and maxLockDuration change"""
    
    current_block = boa.env.evm.patch.block_number
    prev_unlock = current_block + 1000
    old_terms = (100, 1200, 200_00, True, 10_00)   # canExit=True, maxLock=1200
    new_terms = (100, 800, 200_00, False, 10_00)   # canExit=False, maxLock=800
    
    new_unlock = ripe_gov_vault.refreshUnlock(prev_unlock, new_terms, old_terms)
    
    # Terms got worse (canExit False), so should reset to 0
    # Even though maxLock changed, the reset to 0 takes precedence
    assert new_unlock == 0


###########################################
# Critical Production Gap Tests           #
###########################################


def test_ripe_gov_vault_multi_asset_governance_points_tracking(
    ripe_gov_vault, ripe_token, alpha_token, whale, alpha_token_whale, bob, teller, switchboard_alpha, mission_control, setupRipeGovVaultConfig, setAssetConfig
):
    """Test that users with multiple assets get correct governance points across all assets"""
    
    # Setup ripe_token configuration (default)
    setupRipeGovVaultConfig(_assetWeight=100_00, _minLockDuration=100, _maxLockDuration=1000)
    
    # Setup alpha_token as a second asset with different weight
    # First configure alpha_token for vault_id 2 (ripe_gov_vault)
    setAssetConfig(alpha_token, _vaultIds=[2])
    
    # Configure alpha_token with different asset weight in RipeGov vault
    lock_terms_alpha = (50, 500, 150_00, True, 5_00)  # Different terms than ripe_token
    mission_control.setRipeGovVaultConfig(
        alpha_token,
        200_00,  # 200% asset weight vs 100% for ripe_token
        False,
        lock_terms_alpha,
        sender=switchboard_alpha.address
    )
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Bob deposits ripe_token
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Bob deposits alpha_token  
    alpha_token.transfer(ripe_gov_vault, deposit_amount, sender=alpha_token_whale)
    ripe_gov_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    
    # Advance time to accumulate points
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    # Check individual asset governance points
    ripe_userData = ripe_gov_vault.userGovData(bob, ripe_token)
    alpha_userData = ripe_gov_vault.userGovData(bob, alpha_token)
    
    # Both should have governance points
    assert ripe_userData.govPoints > 0
    assert alpha_userData.govPoints > 0
    
    # Alpha should have more points due to higher asset weight (200% vs 100%)
    # Expected calculation: base_points * asset_weight / 100_00
    # Alpha has 2x weight, so should have roughly 2x points for same deposit/time
    assert alpha_userData.govPoints > ripe_userData.govPoints
    
    # Check total user governance points includes both assets
    total_user_points = ripe_gov_vault.totalUserGovPoints(bob)
    expected_total = ripe_userData.govPoints + alpha_userData.govPoints
    assert total_user_points == expected_total
    
    # Check global governance points includes this user's total
    total_global_points = ripe_gov_vault.totalGovPoints()
    assert total_global_points >= total_user_points


def test_ripe_gov_vault_multi_asset_governance_points_update_all(
    ripe_gov_vault, ripe_token, alpha_token, whale, alpha_token_whale, bob, alice, teller, switchboard_alpha, mission_control, setupRipeGovVaultConfig, setAssetConfig
):
    """Test that updateUserGovPoints() correctly iterates through all user assets"""
    
    # Setup both assets
    setupRipeGovVaultConfig(_assetWeight=100_00)
    setAssetConfig(alpha_token, _vaultIds=[2])
    
    # Configure alpha_token with different settings
    lock_terms_alpha = (200, 800, 300_00, True, 15_00)
    mission_control.setRipeGovVaultConfig(
        alpha_token,
        150_00,  # 150% asset weight
        False,
        lock_terms_alpha,
        sender=switchboard_alpha.address
    )
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Bob deposits to both assets
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    alpha_token.transfer(ripe_gov_vault, deposit_amount, sender=alpha_token_whale)
    ripe_gov_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    
    # Alice deposits only to ripe_token
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(alice, ripe_token, deposit_amount, sender=teller.address)
    
    # Advance time
    boa.env.time_travel(blocks=200)
    
    # Capture points before update
    bob_points_before = ripe_gov_vault.totalUserGovPoints(bob)
    alice_points_before = ripe_gov_vault.totalUserGovPoints(alice)
    global_points_before = ripe_gov_vault.totalGovPoints()
    
    # Update governance points for both users
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    ripe_gov_vault.updateUserGovPoints(alice, sender=switchboard_alpha.address)
    
    # Verify points increased for both users
    bob_points_after = ripe_gov_vault.totalUserGovPoints(bob)
    alice_points_after = ripe_gov_vault.totalUserGovPoints(alice)
    global_points_after = ripe_gov_vault.totalGovPoints()
    
    assert bob_points_after > bob_points_before
    assert alice_points_after > alice_points_before
    assert global_points_after > global_points_before
    
    # Bob should have accumulated points from BOTH assets
    # Alice should have accumulated points from only ONE asset
    bob_points_gained = bob_points_after - bob_points_before
    alice_points_gained = alice_points_after - alice_points_before
    
    # Bob's gain should be significantly higher due to having two assets
    # (especially with alpha_token's 150% weight vs 100%)
    assert bob_points_gained > alice_points_gained
    
    # Verify the multi-asset loop worked by checking individual asset points
    bob_ripe_points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints
    bob_alpha_points = ripe_gov_vault.userGovData(bob, alpha_token).govPoints
    alice_ripe_points = ripe_gov_vault.userGovData(alice, ripe_token).govPoints
    alice_alpha_points = ripe_gov_vault.userGovData(alice, alpha_token).govPoints
    
    assert bob_ripe_points > 0
    assert bob_alpha_points > 0
    assert alice_ripe_points > 0
    assert alice_alpha_points == 0  # Alice has no alpha_token deposits
    
    # Bob's total should equal sum of his individual asset points
    assert bob_points_after == bob_ripe_points + bob_alpha_points


def test_ripe_gov_vault_zero_exit_fee_blocks_release_lock_defensive(
    ripe_gov_vault, ripe_token, whale, bob, teller, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test vault's defensive validation against impossible configurations (defense-in-depth)
    
    NOTE: SwitchboardOne.vy prevents canExit=True + exitFee=0 configurations from being set.
    This test serves as defensive programming - the vault validates its own preconditions
    even though the configuration system should prevent this scenario.
    """
    
    # Setup with canExit=True but exitFee=0 
    # (This configuration should be impossible via SwitchboardOne, but we test vault's defense)
    setupRipeGovVaultConfig(
        _minLockDuration=100, 
        _maxLockDuration=1000, 
        _canExit=True,  # Exit is allowed
        _exitFee=0,      # No exit fee (invalid combination, but testing vault's defense)
        _shouldFreezeWhenBadDebt=False,  # Added new parameter
    )
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens with lock duration
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 500, sender=teller.address
    )
    
    # Verify user is locked
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    current_block = boa.env.evm.patch.block_number
    assert userData.unlock == current_block + 500  # Still locked
    assert userData.lastTerms.canExit       # Exit is allowed
    assert userData.lastTerms.exitFee == 0          # But exit fee is zero
    
    # Try to release lock - vault should defensively reject this
    with boa.reverts("no exit fee"):
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)
    
    # This demonstrates the vault's defensive programming:
    # Even if somehow an invalid configuration exists, the vault protects itself


######################################
# Contributor-Related Function Tests #
######################################


def test_ripe_gov_vault_withdraw_contributor_tokens_to_burn_permission_check(
    ripe_gov_vault, bob, alice, setupRipeGovVaultConfig
):
    """Test withdrawContributorTokensToBurn permission validation"""
    setupRipeGovVaultConfig()

    # Should revert with "not allowed" - only HR can call this function
    with boa.reverts("not allowed"):
        ripe_gov_vault.withdrawContributorTokensToBurn(bob, sender=alice)


def test_ripe_gov_vault_withdraw_contributor_tokens_to_burn_no_balance(
    ripe_gov_vault, bob, human_resources, setupRipeGovVaultConfig
):
    """Test withdrawContributorTokensToBurn returns 0 when user has no balance"""
    setupRipeGovVaultConfig()

    # Call from HR with user who has no balance
    withdrawn = ripe_gov_vault.withdrawContributorTokensToBurn(
        bob, sender=human_resources.address
    )
    
    assert withdrawn == 0


def test_ripe_gov_vault_withdraw_contributor_tokens_to_burn_with_balance(
    ripe_gov_vault, ripe_token, whale, bob, teller, human_resources, setupRipeGovVaultConfig
):
    """Test withdrawContributorTokensToBurn withdraws all tokens and bypasses unlock check"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens for bob with lock
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Verify bob has balance and is locked
    user_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    assert user_balance == deposit_amount
    assert userData.unlock > boa.env.evm.patch.block_number  # Still locked
    
    # Get exact strict-path pre-state.
    hr_initial_balance = ripe_token.balanceOf(human_resources.address)
    vault_initial_balance = ripe_token.balanceOf(ripe_gov_vault.address)
    user_shares_before = ripe_gov_vault.userBalances(bob, ripe_token)
    
    # Withdraw all tokens (should bypass unlock check)
    withdrawn = ripe_gov_vault.withdrawContributorTokensToBurn(
        bob, sender=human_resources.address
    )
    event = filter_logs(ripe_gov_vault, "RipeGovVaultWithdrawal")[-1]
    
    # Verify withdrawal worked
    assert withdrawn == deposit_amount
    assert vault_initial_balance - ripe_token.balanceOf(ripe_gov_vault.address) == withdrawn
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0  # User depleted
    assert ripe_gov_vault.userBalances(bob, ripe_token) == 0
    assert user_shares_before > 0
    assert ripe_token.balanceOf(human_resources.address) == hr_initial_balance + deposit_amount
    assert event.amount == withdrawn
    assert event.shares == user_shares_before


def test_ripe_gov_vault_withdraw_contributor_tokens_to_burn_governance_points_update(
    ripe_gov_vault, ripe_token, whale, bob, teller, human_resources, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test withdrawContributorTokensToBurn updates governance points correctly"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit and accumulate governance points
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Advance time to accumulate points
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    initial_points = ripe_gov_vault.totalUserGovPoints(bob)
    initial_total_points = ripe_gov_vault.totalGovPoints()
    assert initial_points > 0
    
    # Withdraw all tokens
    ripe_gov_vault.withdrawContributorTokensToBurn(bob, sender=human_resources.address)
    
    # Governance points should be reduced/reset
    final_points = ripe_gov_vault.totalUserGovPoints(bob)
    final_total_points = ripe_gov_vault.totalGovPoints()
    
    assert final_points < initial_points  # Points should be reduced
    assert final_total_points < initial_total_points  # Total should be reduced


def test_ripe_gov_vault_transfer_contributor_ripe_tokens_permission_check(
    ripe_gov_vault, bob, alice, charlie, setupRipeGovVaultConfig
):
    """Test transferContributorRipeTokens permission validation"""
    setupRipeGovVaultConfig()

    # Should revert with "not allowed" - only HR can call this function  
    with boa.reverts("not allowed"):
        ripe_gov_vault.transferContributorRipeTokens(bob, alice, 500, sender=charlie)


def test_ripe_gov_vault_transfer_contributor_ripe_tokens_no_balance(
    ripe_gov_vault, ripe_token, bob, alice, human_resources, setupRipeGovVaultConfig
):
    """Test transferContributorRipeTokens when contributor has no balance"""
    setupRipeGovVaultConfig()

    # First verify bob has no balance
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) == 0
    
    # Transfer when bob has no balance should fail with the SharesVault assertion
    # This is expected behavior - you can't transfer what doesn't exist
    with boa.reverts():  # Will revert with "no asset to withdraw" from SharesVault
        ripe_gov_vault.transferContributorRipeTokens(
            bob, alice, 500, sender=human_resources.address
        )


def test_ripe_gov_vault_transfer_contributor_ripe_tokens_with_balance(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, human_resources, setupRipeGovVaultConfig
):
    """Test transferContributorRipeTokens transfers all tokens correctly"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    lock_duration = 500
    
    # Give bob RIPE tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    initial_bob_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    initial_alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    
    # Transfer all tokens from bob to alice
    transferred = ripe_gov_vault.transferContributorRipeTokens(
        bob, alice, lock_duration, sender=human_resources.address
    )
    
    # Verify transfer
    assert transferred == initial_bob_balance
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0  # Bob depleted
    assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) == initial_alice_balance + transferred


def test_ripe_gov_vault_transfer_contributor_ripe_tokens_applies_lock_duration(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, human_resources, setupRipeGovVaultConfig
):
    """Test transferContributorRipeTokens applies correct lock duration to recipient"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    lock_duration = 800
    
    # Give bob RIPE tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Transfer with specific lock duration
    ripe_gov_vault.transferContributorRipeTokens(
        bob, alice, lock_duration, sender=human_resources.address
    )
    
    # Check alice's lock duration
    alice_userData = ripe_gov_vault.userGovData(alice, ripe_token)
    current_block = boa.env.evm.patch.block_number
    expected_unlock = current_block + lock_duration
    
    assert alice_userData.unlock == expected_unlock


def test_ripe_gov_vault_transfer_contributor_ripe_tokens_transfers_governance_points(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, human_resources, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test transferContributorRipeTokens transfers governance points from contributor to recipient"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    lock_duration = 600
    
    # Give bob RIPE tokens and accumulate governance points
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Advance time to accumulate points
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    initial_bob_points = ripe_gov_vault.totalUserGovPoints(bob)
    initial_alice_points = ripe_gov_vault.totalUserGovPoints(alice)
    initial_total_points = ripe_gov_vault.totalGovPoints()
    
    assert initial_bob_points > 0
    assert initial_alice_points == 0
    assert initial_total_points == initial_bob_points
    
    # Transfer tokens (this should transfer governance points with _shouldTransferPoints=True)
    ripe_gov_vault.transferContributorRipeTokens(
        bob, alice, lock_duration, sender=human_resources.address
    )
    
    # Check governance points after transfer - should be exact amounts
    final_bob_points = ripe_gov_vault.totalUserGovPoints(bob)
    final_alice_points = ripe_gov_vault.totalUserGovPoints(alice)
    final_total_points = ripe_gov_vault.totalGovPoints()
    
    # Bob should have ALL his points transferred to Alice since he transferred all his tokens
    assert final_bob_points == 0  # Bob should have exactly 0 points (transferred all tokens)
    assert final_alice_points == initial_bob_points  # Alice should have exactly Bob's original points
    
    # Total points should be exactly preserved
    assert final_total_points == initial_total_points
    assert final_total_points == final_bob_points + final_alice_points


def test_ripe_gov_vault_transfer_contributor_ripe_tokens_multiple_transfers(
    ripe_gov_vault, ripe_token, whale, bob, alice, charlie, teller, human_resources, setupRipeGovVaultConfig
):
    """Test multiple transferContributorRipeTokens calls work correctly"""
    setupRipeGovVaultConfig()

    deposit_amount = 150 * EIGHTEEN_DECIMALS
    
    # Setup bob with tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # First transfer: bob -> alice
    transferred1 = ripe_gov_vault.transferContributorRipeTokens(
        bob, alice, 400, sender=human_resources.address
    )
    
    assert transferred1 == deposit_amount
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) == transferred1
    
    # Second transfer: alice -> charlie (alice now has the tokens)
    transferred2 = ripe_gov_vault.transferContributorRipeTokens(
        alice, charlie, 600, sender=human_resources.address
    )
    
    assert transferred2 == transferred1  # Same amount as what alice had
    assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(charlie, ripe_token) == transferred2


def test_ripe_gov_vault_transfer_contributor_ripe_tokens_lock_duration_enforcement(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, human_resources, setupRipeGovVaultConfig
):
    """Test transferContributorRipeTokens uses weighted lock calculation"""
    # Setup with specific lock duration limits
    setupRipeGovVaultConfig(_minLockDuration=200, _maxLockDuration=800)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Setup transfer scenario - bob gets tokens first
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Check bob's initial lock (should be minimum 200)
    bob_userData_initial = ripe_gov_vault.userGovData(bob, ripe_token)
    current_block_before = boa.env.evm.patch.block_number
    assert bob_userData_initial.unlock == current_block_before + 200  # Bob has min lock
    
    # Transfer with lock duration - uses weighted lock calculation, not min/max enforcement
    ripe_gov_vault.transferContributorRipeTokens(
        bob, alice, 50, sender=human_resources.address  # Uses weighted lock calculation
    )
    
    # Alice gets a weighted lock based on bob's remaining lock and the requested duration
    alice_userData = ripe_gov_vault.userGovData(alice, ripe_token)
    current_block_after = boa.env.evm.patch.block_number
    
    # The weighted lock calculation blends bob's remaining lock duration with the requested duration
    # Since bob had all the shares and 200 blocks remaining, and we requested 50,
    # the weighted average should be: (shares*200 + shares*50) / (shares+shares) = 125
    # But since bob transfers ALL his shares to alice, it's just the weighted calculation
    # between bob's remaining duration and the new duration
    current_block_after + 50  # In this case, it uses the new duration
    
    # Alice should have a lock duration that makes sense based on the weighted calculation
    assert alice_userData.unlock > current_block_after  # Should be locked
    assert alice_userData.unlock >= current_block_after + 50  # Should be at least the requested duration


def test_ripe_gov_vault_contributor_functions_integration_workflow(
    ripe_gov_vault, ripe_token, whale, bob, alice, charlie, teller, human_resources, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test integration workflow using both contributor functions together"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Step 1: Bob (contributor) gets RIPE tokens and accumulates governance points
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Advance time to accumulate governance points
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    
    initial_bob_points = ripe_gov_vault.totalUserGovPoints(bob)
    initial_total_points = ripe_gov_vault.totalGovPoints()
    assert initial_bob_points > 0
    assert initial_total_points > 0
    assert initial_total_points == initial_bob_points  # Only bob has points initially
    
    # Step 2: Transfer RIPE tokens from contributor (bob) to owner (alice)
    transferred = ripe_gov_vault.transferContributorRipeTokens(
        bob, alice, 500, sender=human_resources.address
    )
    
    # Verify transfer completed and governance points moved exactly
    assert transferred == deposit_amount
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) == transferred
    
    # Alice should have exactly Bob's original points, Bob should have exactly 0
    alice_points_after_transfer = ripe_gov_vault.totalUserGovPoints(alice)
    bob_points_after_transfer = ripe_gov_vault.totalUserGovPoints(bob)
    total_points_after_transfer = ripe_gov_vault.totalGovPoints()
    
    assert bob_points_after_transfer == 0  # Bob transferred all tokens and points
    assert alice_points_after_transfer == initial_bob_points  # Alice got exactly Bob's points
    assert total_points_after_transfer == initial_total_points  # Total preserved exactly
    
    # Step 3: Later, Alice deposits more tokens directly (separate from HR system)
    additional_deposit = 50 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, additional_deposit, sender=whale)
    ripe_gov_vault.depositTokensInVault(alice, ripe_token, additional_deposit, sender=teller.address)
    
    # Alice should now have even more tokens
    alice_total_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    assert alice_total_balance == transferred + additional_deposit
    
    # Step 4: Simulate a contributor refund scenario - withdraw charlie's position for burning
    # First give charlie some tokens to simulate he's a contributor
    charlie_deposit = 75 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, charlie_deposit, sender=whale)
    ripe_gov_vault.depositTokensInVault(charlie, ripe_token, charlie_deposit, sender=teller.address)
    
    # Advance time for charlie to accumulate points
    boa.env.time_travel(blocks=50)
    ripe_gov_vault.updateUserGovPoints(charlie, sender=switchboard_alpha.address)
    
    charlie_points_before = ripe_gov_vault.totalUserGovPoints(charlie)
    total_points_before_burn = ripe_gov_vault.totalGovPoints()
    assert charlie_points_before > 0
    
    # Withdraw charlie's tokens for burning (bypass unlock check)
    hr_balance_before = ripe_token.balanceOf(human_resources.address)
    withdrawn = ripe_gov_vault.withdrawContributorTokensToBurn(
        charlie, sender=human_resources.address
    )
    
    # Verify withdrawal for burning
    assert withdrawn == charlie_deposit
    assert ripe_gov_vault.getTotalAmountForUser(charlie, ripe_token) == 0
    assert ripe_token.balanceOf(human_resources.address) == hr_balance_before + withdrawn
    
    # Charlie's governance points should be exactly 0 after burning all tokens
    charlie_points_after = ripe_gov_vault.totalUserGovPoints(charlie)
    total_points_after_burn = ripe_gov_vault.totalGovPoints()
    
    assert charlie_points_after == 0  # Charlie should have exactly 0 points after burn
    assert total_points_after_burn == total_points_before_burn - charlie_points_before  # Exact reduction
    
    # Final verification: Alice still has her tokens and points, bob and charlie are depleted
    assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) > 0
    assert ripe_gov_vault.totalUserGovPoints(alice) > 0
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(charlie, ripe_token) == 0
    assert ripe_gov_vault.totalUserGovPoints(bob) == 0
    assert ripe_gov_vault.totalUserGovPoints(charlie) == 0


######################################
# Bad Debt Withdrawal Freeze Tests   #
######################################


def test_ripe_gov_vault_withdrawal_frozen_when_bad_debt_exists(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, mission_control, ledger, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that withdrawals are frozen when shouldFreezeWhenBadDebt=True and bad debt exists"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Fast forward past unlock time
    unlock_block = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    current_block = boa.env.evm.patch.block_number
    blocks_to_advance = unlock_block - current_block + 1
    boa.env.time_travel(blocks=blocks_to_advance)
    
    # First verify withdrawal works normally without bad debt
    withdraw_amount = 25 * EIGHTEEN_DECIMALS
    initial_balance = ripe_token.balanceOf(alice)
    
    withdrawn, is_depleted = ripe_gov_vault.withdrawTokensFromVault(
        bob, ripe_token, withdraw_amount, alice, sender=teller.address
    )
    assert withdrawn == withdraw_amount
    assert ripe_token.balanceOf(alice) == initial_balance + withdraw_amount
    
    # Now enable bad debt freeze and set bad debt
    lock_terms = (100, 1000, 200_00, True, 10_00)
    mission_control.setRipeGovVaultConfig(
        ripe_token, 
        100_00,  # assetWeight
        True,    # shouldFreezeWhenBadDebt = True
        lock_terms,
        sender=switchboard_alpha.address
    )
    
    # Set bad debt in ledger
    bad_debt_amount = 50 * EIGHTEEN_DECIMALS
    ledger.setBadDebt(bad_debt_amount, sender=switchboard_alpha.address)
    
    # Verify bad debt was set
    assert ledger.badDebt() == bad_debt_amount
    
    # Now withdrawal should fail due to bad debt
    with boa.reverts("cannot withdraw when bad debt"):
        ripe_gov_vault.withdrawTokensFromVault(
            bob, ripe_token, withdraw_amount, alice, sender=teller.address
        )


def test_ripe_gov_vault_withdrawal_works_when_bad_debt_freeze_disabled(
    ripe_gov_vault, ripe_token, whale, bob, alice, teller, mission_control, ledger, switchboard_alpha, setupRipeGovVaultConfig
):
    """Test that withdrawals work when shouldFreezeWhenBadDebt=False even with bad debt"""
    setupRipeGovVaultConfig()

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, deposit_amount, sender=teller.address)
    
    # Fast forward past unlock time
    unlock_block = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    current_block = boa.env.evm.patch.block_number
    blocks_to_advance = unlock_block - current_block + 1
    boa.env.time_travel(blocks=blocks_to_advance)
    
    # Set bad debt freeze to disabled and set bad debt
    lock_terms = (100, 1000, 200_00, True, 10_00)
    mission_control.setRipeGovVaultConfig(
        ripe_token, 
        100_00,  # assetWeight
        False,   # shouldFreezeWhenBadDebt = False
        lock_terms,
        sender=switchboard_alpha.address
    )
    
    # Set bad debt in ledger
    bad_debt_amount = 50 * EIGHTEEN_DECIMALS
    ledger.setBadDebt(bad_debt_amount, sender=switchboard_alpha.address)
    
    # Verify bad debt exists
    assert ledger.badDebt() == bad_debt_amount
    
    # Withdrawal should still work because freeze is disabled
    withdraw_amount = 25 * EIGHTEEN_DECIMALS
    initial_balance = ripe_token.balanceOf(alice)
    
    withdrawn, is_depleted = ripe_gov_vault.withdrawTokensFromVault(
        bob, ripe_token, withdraw_amount, alice, sender=teller.address
    )
    
    assert withdrawn == withdraw_amount
    assert ripe_token.balanceOf(alice) == initial_balance + withdraw_amount


def test_ripe_gov_vault_release_lock_blocked_when_bad_debt_and_freeze_enabled(
    ripe_gov_vault, ripe_token, whale, bob, ledger, switchboard_alpha, setupRipeGovVaultConfig,
    teller,
):
    """Test that releaseLock() is blocked when bad debt exists and shouldFreezeWhenBadDebt=True to save users money"""
    # Setup with exit enabled and exit fee, and freeze enabled
    setupRipeGovVaultConfig(
        _minLockDuration=100, 
        _maxLockDuration=1000, 
        _canExit=True, 
        _exitFee=10_00,  # 10% exit fee
        _shouldFreezeWhenBadDebt=True,  # Enable freeze when bad debt
    )
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens with lock duration
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 500, sender=teller.address
    )
    
    # Verify user is locked and can normally release lock without bad debt
    userData_before = ripe_gov_vault.userGovData(bob, ripe_token)
    current_block = boa.env.evm.patch.block_number
    assert userData_before.unlock == current_block + 500  # Still locked
    assert userData_before.lastTerms.canExit       # Exit is allowed
    assert userData_before.lastTerms.exitFee == 10_00     # Has exit fee
    
    # Verify release lock works normally without bad debt
    # First test that it would work (we'll revert this)
    # We need to capture initial state
    initial_shares = userData_before.lastShares
    
    # Create bad debt
    bad_debt_amount = 50 * EIGHTEEN_DECIMALS
    ledger.setBadDebt(bad_debt_amount, sender=switchboard_alpha.address)
    
    # Verify bad debt exists
    assert ledger.badDebt() == bad_debt_amount
    
    # Now releaseLock should fail to save user money since withdrawals would be frozen anyway
    with boa.reverts("saving user money"):
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)
    
    # User's position should remain unchanged (not charged exit fee)
    userData_after = ripe_gov_vault.userGovData(bob, ripe_token)
    assert userData_after.lastShares == initial_shares  # No shares were removed
    assert userData_after.unlock == userData_before.unlock  # Still locked


def test_ripe_gov_vault_release_lock_works_when_bad_debt_but_freeze_disabled(
    ripe_gov_vault, ripe_token, whale, bob, alice, ledger, switchboard_alpha, setupRipeGovVaultConfig,
    teller,
):
    """Test that releaseLock() works when bad debt exists but shouldFreezeWhenBadDebt=False"""
    # Setup with exit enabled and exit fee, but freeze disabled
    setupRipeGovVaultConfig(
        _minLockDuration=100, 
        _maxLockDuration=1000, 
        _canExit=True, 
        _exitFee=8_00,  # 8% exit fee
        _shouldFreezeWhenBadDebt=False,  # Disable freeze when bad debt
    )
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens with lock duration
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 400, sender=teller.address
    )
    _add_remaining_holder(ripe_gov_vault, ripe_token, whale, alice, deposit_amount, teller)
    
    # Verify user is locked
    userData_before = ripe_gov_vault.userGovData(bob, ripe_token)
    current_block = boa.env.evm.patch.block_number
    assert userData_before.unlock == current_block + 400  # Still locked
    assert userData_before.lastTerms.canExit       # Exit is allowed
    assert userData_before.lastTerms.exitFee == 8_00      # Has exit fee
    initial_shares = userData_before.lastShares
    total_shares_before = ripe_gov_vault.totalBalances(ripe_token)
    custody_before = ripe_token.balanceOf(ripe_gov_vault)
    
    # Create bad debt
    bad_debt_amount = 30 * EIGHTEEN_DECIMALS
    ledger.setBadDebt(bad_debt_amount, sender=switchboard_alpha.address)
    
    # Verify bad debt exists
    assert ledger.badDebt() == bad_debt_amount
    
    # Release lock should work because freeze is disabled (even with bad debt)
    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)
    
    # Verify lock was released and exit fee was charged
    userData_after = ripe_gov_vault.userGovData(bob, ripe_token)
    assert userData_after.unlock == 0  # Lock released
    total_shares_after = ripe_gov_vault.totalBalances(ripe_token)
    
    # Verify the exact economic 8% claim reduction
    assert_exact_exit_claim(
        initial_shares,
        total_shares_before,
        custody_before,
        8_00,
        userData_after.lastShares,
        total_shares_after,
    )
    
    # Verify the shares fee was charged correctly
    shares_fee_charged = initial_shares - userData_after.lastShares
    assert shares_fee_charged > initial_shares * 8_00 // HUNDRED_PERCENT


def test_ripe_gov_vault_release_lock_works_when_no_bad_debt_regardless_of_freeze_setting(
    ripe_gov_vault, ripe_token, whale, bob, alice, ledger, switchboard_alpha, setupRipeGovVaultConfig,
    teller,
):
    """Test that releaseLock() works normally when there's no bad debt, regardless of shouldFreezeWhenBadDebt setting"""
    # Test with freeze enabled first
    setupRipeGovVaultConfig(
        _minLockDuration=100, 
        _maxLockDuration=1000, 
        _canExit=True, 
        _exitFee=12_00,  # 12% exit fee
        _shouldFreezeWhenBadDebt=True,  # Enable freeze when bad debt
    )
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Deposit tokens with lock duration
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, deposit_amount, 600, sender=teller.address
    )
    _add_remaining_holder(ripe_gov_vault, ripe_token, whale, alice, deposit_amount, teller)
    
    # Verify user is locked
    userData_before = ripe_gov_vault.userGovData(bob, ripe_token)
    current_block = boa.env.evm.patch.block_number
    assert userData_before.unlock == current_block + 600  # Still locked
    initial_shares = userData_before.lastShares
    total_shares_before = ripe_gov_vault.totalBalances(ripe_token)
    custody_before = ripe_token.balanceOf(ripe_gov_vault)
    
    # Verify no bad debt exists
    assert ledger.badDebt() == 0
    
    # Release lock should work normally since there's no bad debt
    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)
    
    # Verify lock was released and exit fee was charged
    userData_after = ripe_gov_vault.userGovData(bob, ripe_token)
    assert userData_after.unlock == 0  # Lock released
    total_shares_after = ripe_gov_vault.totalBalances(ripe_token)
    
    # Verify the exact economic 12% claim reduction
    assert_exact_exit_claim(
        initial_shares,
        total_shares_before,
        custody_before,
        12_00,
        userData_after.lastShares,
        total_shares_after,
    )


def test_depositIntoGovVault_basic_no_lock(
    teller, ripe_gov_vault, ripe_token, whale, setupRipeGovVaultConfig, setGeneralConfig
):
    """Test basic depositIntoGovVault without lock duration (lockDuration = 0)"""
    setupRipeGovVaultConfig()
    setGeneralConfig()  # Enable general deposits
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Approve teller to spend tokens
    ripe_token.approve(teller, deposit_amount, sender=whale)
    
    # Get initial balances
    initial_whale_balance = ripe_token.balanceOf(whale)
    initial_vault_balance = ripe_token.balanceOf(ripe_gov_vault)
    
    # Deposit without lock (lockDuration = 0)
    shares = teller.depositIntoGovVault(
        ripe_token,
        deposit_amount,
        0,  # No lock duration
        whale,
        sender=whale
    )
    
    # Verify deposit was successful
    assert shares == deposit_amount  # 1:1 for first deposit
    
    # Verify token transfer occurred
    assert ripe_token.balanceOf(whale) == initial_whale_balance - deposit_amount
    assert ripe_token.balanceOf(ripe_gov_vault) == initial_vault_balance + deposit_amount
    
    # Verify user's position in vault
    user_amount = ripe_gov_vault.getTotalAmountForUser(whale, ripe_token)
    assert user_amount == deposit_amount
    
    # Check governance data - should have minimum lock
    userData = ripe_gov_vault.userGovData(whale, ripe_token)
    current_block = boa.env.evm.patch.block_number
    assert userData.unlock == current_block + 100  # minLockDuration from config


def test_depositIntoGovVault_with_lock_duration(
    teller, ripe_gov_vault, ripe_token, whale, setupRipeGovVaultConfig, setGeneralConfig
):
    """Test depositIntoGovVault with specific lock duration"""
    setupRipeGovVaultConfig()
    setGeneralConfig()  # Enable general deposits
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    lock_duration = 500  # blocks
    
    # Approve teller to spend tokens
    ripe_token.approve(teller, deposit_amount, sender=whale)
    
    # Deposit with lock duration
    shares = teller.depositIntoGovVault(
        ripe_token,
        deposit_amount,
        lock_duration,
        whale,
        sender=whale
    )
    
    # Verify deposit was successful
    assert shares == deposit_amount
    
    # Check governance data - should have specified lock duration
    userData = ripe_gov_vault.userGovData(whale, ripe_token)
    expected_unlock = boa.env.evm.patch.block_number + lock_duration
    assert userData.unlock == expected_unlock


def test_depositIntoGovVault_underscore_can_deposit_for_others_with_lock(
    teller,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    mock_undy_v2,
    mission_control,
    switchboard_alpha,
    setupRipeGovVaultConfig,
    setGeneralConfig,
    setUserConfig,
    setUserDelegation,
):
    """Test that a user-authorized Underscore address can deposit with a lock."""
    setupRipeGovVaultConfig()
    setGeneralConfig()  # Enable general deposits
    
    # Set mock_undy_v2 as the underscore registry
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    setUserConfig(
        bob,
        _canAnyoneDeposit=True,
        _canAnyoneRepayDebt=True,
    )
    setUserDelegation(
        bob,
        mock_undy_v2.address,
        _canWithdraw=True,
        _canBorrow=True,
        _canClaimFromStabPool=True,
        _canClaimLoot=True,
    )
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    lock_duration = 500  # blocks - a specific lock duration between min and max
    
    # Transfer tokens to mock_undy_v2 (underscore address)
    ripe_token.transfer(mock_undy_v2.address, deposit_amount, sender=whale)
    
    # mock_undy_v2 approves teller
    ripe_token.approve(teller, deposit_amount, sender=mock_undy_v2.address)
    
    # mock_undy_v2 deposits for bob with specific lock duration
    shares = teller.depositIntoGovVault(
        ripe_token,
        deposit_amount,
        lock_duration,  # Specific lock duration
        bob,  # Depositing for bob
        sender=mock_undy_v2.address  # Underscore address is the sender
    )
    
    # Verify deposit was successful
    assert shares == deposit_amount
    
    # Verify bob received the deposit
    user_amount = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    assert user_amount == deposit_amount
    
    # Verify the specific lock duration was applied to bob
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    expected_unlock = boa.env.evm.patch.block_number + lock_duration
    assert userData.unlock == expected_unlock  # Should be exactly the lock_duration specified


def test_depositIntoGovVault_regular_user_cannot_deposit_for_others(
    teller, ripe_token, whale, bob, alice, setupRipeGovVaultConfig, setGeneralConfig
):
    """Test that regular users cannot deposit for other users"""
    setupRipeGovVaultConfig()
    setGeneralConfig()  # Enable general deposits
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Transfer tokens to alice (regular user)
    ripe_token.transfer(alice, deposit_amount, sender=whale)
    
    # Alice approves teller
    ripe_token.approve(teller, deposit_amount, sender=alice)
    
    # Alice tries to deposit for bob (should fail)
    with boa.reverts("no perms"):
        teller.depositIntoGovVault(
            ripe_token,
            deposit_amount,
            0,
            bob,  # Trying to deposit for bob
            sender=alice  # Regular user
        )


def test_depositIntoGovVault_for_self_allowed(
    teller, ripe_gov_vault, ripe_token, whale, alice, setupRipeGovVaultConfig, setGeneralConfig
):
    """Test that anyone can deposit for themselves with lock duration"""
    setupRipeGovVaultConfig()
    setGeneralConfig()  # Enable general deposits
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    lock_duration = 300  # blocks
    
    # Transfer tokens to alice
    ripe_token.transfer(alice, deposit_amount, sender=whale)
    
    # Approve teller from alice
    ripe_token.approve(teller, deposit_amount, sender=alice)
    
    # Deposit for self with lock duration (should succeed)
    shares = teller.depositIntoGovVault(
        ripe_token,
        deposit_amount,
        lock_duration,
        alice,  # Depositing for self
        sender=alice
    )
    
    # Verify deposit was successful
    assert shares == deposit_amount
    
    # Verify alice received the deposit
    user_amount = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    assert user_amount == deposit_amount


def test_depositIntoGovVault_when_paused(
    teller, ripe_token, whale, switchboard_alpha, setupRipeGovVaultConfig, setGeneralConfig
):
    """Test that depositIntoGovVault fails when contract is paused"""
    setupRipeGovVaultConfig()
    setGeneralConfig()  # Enable general deposits
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Approve teller to spend tokens
    ripe_token.approve(teller, deposit_amount, sender=whale)
    
    # Pause the teller contract
    teller.pause(True, sender=switchboard_alpha.address)
    
    # Try to deposit (should fail)
    with boa.reverts("contract paused"):
        teller.depositIntoGovVault(
            ripe_token,
            deposit_amount,
            0,
            whale,
            sender=whale
        )
    
    # Unpause for cleanup
    teller.pause(False, sender=switchboard_alpha.address)


def test_depositIntoGovVault_multiple_deposits(
    teller, ripe_gov_vault, ripe_token, whale, setupRipeGovVaultConfig, setGeneralConfig
):
    """Test multiple deposits through depositIntoGovVault with different lock durations"""
    setupRipeGovVaultConfig()
    setGeneralConfig()  # Enable general deposits
    
    first_deposit = 100 * EIGHTEEN_DECIMALS
    second_deposit = 200 * EIGHTEEN_DECIMALS
    
    # Approve teller for total amount
    total_amount = first_deposit + second_deposit
    ripe_token.approve(teller, total_amount, sender=whale)
    
    # First deposit with short lock
    lock_duration_1 = 200  # blocks
    teller.depositIntoGovVault(
        ripe_token,
        first_deposit,
        lock_duration_1,
        whale,
        sender=whale
    )
    
    # Get unlock time after first deposit
    userData_1 = ripe_gov_vault.userGovData(whale, ripe_token)
    unlock_1 = userData_1.unlock
    
    # Second deposit with longer lock
    lock_duration_2 = 600  # blocks
    teller.depositIntoGovVault(
        ripe_token,
        second_deposit,
        lock_duration_2,
        whale,
        sender=whale
    )
    
    # Verify total position
    total_amount_in_vault = ripe_gov_vault.getTotalAmountForUser(whale, ripe_token)
    assert total_amount_in_vault == first_deposit + second_deposit
    
    # Check that unlock time is weighted average
    userData_2 = ripe_gov_vault.userGovData(whale, ripe_token)
    unlock_2 = userData_2.unlock
    
    # The new unlock should be a weighted average, biased toward the larger deposit
    # Since second deposit is 2x larger with longer lock, it should pull the unlock time up
    assert unlock_2 > unlock_1
    assert unlock_2 < boa.env.evm.patch.block_number + lock_duration_2  # But not as far as the full second lock


def test_depositIntoGovVault_lock_duration_capped(
    teller, ripe_gov_vault, ripe_token, whale, setupRipeGovVaultConfig, setGeneralConfig
):
    """Test depositIntoGovVault with lock duration exceeding maximum gets capped"""
    setupRipeGovVaultConfig()
    setGeneralConfig()  # Enable general deposits
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    excessive_lock_duration = 1500  # exceeds maxLockDuration of 1000
    
    # Approve teller to spend tokens
    ripe_token.approve(teller, deposit_amount, sender=whale)
    
    # Deposit with excessive lock duration (should succeed but be capped)
    shares = teller.depositIntoGovVault(
        ripe_token,
        deposit_amount,
        excessive_lock_duration,
        whale,
        sender=whale
    )
    
    # Verify deposit was successful
    assert shares == deposit_amount
    
    # Verify lock duration was capped at maxLockDuration (1000)
    userData = ripe_gov_vault.userGovData(whale, ripe_token)
    expected_unlock = boa.env.evm.patch.block_number + 1000  # maxLockDuration
    assert userData.unlock == expected_unlock


def test_teller_governance_routes_follow_core_vault_pointer(
    teller,
    ripe_gov_vault,
    alternate_ripe_gov_vault,
    registerVault,
    mission_control,
    switchboard_alpha,
    ripe_token,
    whale,
    bob,
    setupRipeGovVaultConfig,
    setGeneralConfig,
    setAssetConfig,
):
    core_id = registerVault(alternate_ripe_gov_vault, "Core RipeGov")
    setupRipeGovVaultConfig()
    setGeneralConfig()
    setAssetConfig(ripe_token, _vaultIds=[core_id])
    mission_control.setCoreRipeGovVaultId(core_id, sender=switchboard_alpha.address)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    ripe_token.approve(teller, deposit_amount, sender=whale)
    assert teller.depositIntoGovVault(
        ripe_token,
        deposit_amount,
        500,
        whale,
        sender=whale,
    ) == deposit_amount
    assert alternate_ripe_gov_vault.getTotalAmountForUser(whale, ripe_token) == deposit_amount
    assert ripe_gov_vault.getTotalAmountForUser(whale, ripe_token) == 0

    _add_remaining_holder(
        alternate_ripe_gov_vault,
        ripe_token,
        whale,
        bob,
        deposit_amount,
        teller,
    )

    teller.adjustLock(ripe_token, 800, whale, sender=whale)
    adjusted = alternate_ripe_gov_vault.userGovData(whale, ripe_token)
    assert adjusted.unlock == boa.env.evm.patch.block_number + 800

    teller.releaseLock(ripe_token, whale, sender=whale)
    released = alternate_ripe_gov_vault.userGovData(whale, ripe_token)
    assert released.unlock == 0


def test_teller_governance_routes_fail_closed_when_core_pointer_is_unset(
    teller,
    mission_control,
    ripe_token,
    whale,
    setupRipeGovVaultConfig,
    setGeneralConfig,
):
    setupRipeGovVaultConfig()
    setGeneralConfig()
    mission_control.eval("self.coreRipeGovVaultId = 0")

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    ripe_token.approve(teller, deposit_amount, sender=whale)
    with boa.reverts("invalid vault id"):
        teller.depositIntoGovVault(ripe_token, deposit_amount, 0, whale, sender=whale)
    with boa.reverts("invalid vault id"):
        teller.adjustLock(ripe_token, 500, whale, sender=whale)
    with boa.reverts("invalid vault id"):
        teller.releaseLock(ripe_token, whale, sender=whale)


def test_core_pointer_rotation_preserves_legacy_position_points_and_explicit_exit(
    teller,
    ripe_gov_vault,
    alternate_ripe_gov_vault,
    registerVault,
    mission_control,
    switchboard_alpha,
    ripe_token,
    whale,
    setupRipeGovVaultConfig,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    lootbox,
    ledger,
):
    core_id = registerVault(alternate_ripe_gov_vault, "Replacement Core RipeGov")
    setupRipeGovVaultConfig()
    setGeneralConfig()
    setAssetConfig(ripe_token, _vaultIds=[2, core_id])
    setRipeRewardsConfig(True)
    mock_price_source.setPrice(ripe_token, EIGHTEEN_DECIMALS)

    legacy_amount = 100 * EIGHTEEN_DECIMALS
    ripe_token.approve(teller, legacy_amount, sender=whale)
    assert teller.depositIntoGovVault(
        ripe_token,
        legacy_amount,
        100,
        whale,
        sender=whale,
    ) == legacy_amount

    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(
        whale,
        2,
        ripe_gov_vault,
        ripe_token,
        sender=teller.address,
    )

    legacy_gov_before = ripe_gov_vault.userGovData(whale, ripe_token)
    legacy_points_before = ledger.userDepositPoints(whale, 2, ripe_token)
    legacy_asset_points_before = ledger.assetDepositPoints(2, ripe_token)
    global_points_before = ledger.globalDepositPoints()
    asset_config_before = mission_control.assetConfig(ripe_token)
    assert legacy_points_before.balancePoints > 0

    gov_snapshot = (
        legacy_gov_before.govPoints,
        legacy_gov_before.lastShares,
        legacy_gov_before.lastPointsUpdate,
        legacy_gov_before.unlock,
    )
    user_points_snapshot = (
        legacy_points_before.balancePoints,
        legacy_points_before.lastBalance,
        legacy_points_before.lastUpdate,
    )
    asset_points_snapshot = (
        legacy_asset_points_before.balancePoints,
        legacy_asset_points_before.lastBalance,
        legacy_asset_points_before.lastUsdValue,
        legacy_asset_points_before.ripeStakerPoints,
        legacy_asset_points_before.ripeVotePoints,
        legacy_asset_points_before.ripeGenPoints,
        legacy_asset_points_before.lastUpdate,
        legacy_asset_points_before.precision,
    )
    global_points_snapshot = (
        global_points_before.lastUsdValue,
        global_points_before.ripeStakerPoints,
        global_points_before.ripeVotePoints,
        global_points_before.ripeGenPoints,
        global_points_before.lastUpdate,
    )

    mission_control.setCoreRipeGovVaultId(core_id, sender=switchboard_alpha.address)

    legacy_gov_after = ripe_gov_vault.userGovData(whale, ripe_token)
    legacy_points_after = ledger.userDepositPoints(whale, 2, ripe_token)
    legacy_asset_points_after = ledger.assetDepositPoints(2, ripe_token)
    global_points_after = ledger.globalDepositPoints()
    asset_config_after = mission_control.assetConfig(ripe_token)

    assert ripe_gov_vault.getTotalAmountForUser(whale, ripe_token) == legacy_amount
    assert (
        legacy_gov_after.govPoints,
        legacy_gov_after.lastShares,
        legacy_gov_after.lastPointsUpdate,
        legacy_gov_after.unlock,
    ) == gov_snapshot
    assert (
        legacy_points_after.balancePoints,
        legacy_points_after.lastBalance,
        legacy_points_after.lastUpdate,
    ) == user_points_snapshot
    assert (
        legacy_asset_points_after.balancePoints,
        legacy_asset_points_after.lastBalance,
        legacy_asset_points_after.lastUsdValue,
        legacy_asset_points_after.ripeStakerPoints,
        legacy_asset_points_after.ripeVotePoints,
        legacy_asset_points_after.ripeGenPoints,
        legacy_asset_points_after.lastUpdate,
        legacy_asset_points_after.precision,
    ) == asset_points_snapshot
    assert (
        global_points_after.lastUsdValue,
        global_points_after.ripeStakerPoints,
        global_points_after.ripeVotePoints,
        global_points_after.ripeGenPoints,
        global_points_after.lastUpdate,
    ) == global_points_snapshot
    assert asset_config_after.stakersPointsAlloc == asset_config_before.stakersPointsAlloc
    assert asset_config_after.voterPointsAlloc == asset_config_before.voterPointsAlloc

    replacement_amount = 60 * EIGHTEEN_DECIMALS
    ripe_token.approve(teller, replacement_amount, sender=whale)
    assert teller.depositIntoGovVault(
        ripe_token,
        replacement_amount,
        100,
        whale,
        sender=whale,
    ) == replacement_amount
    assert ripe_gov_vault.getTotalAmountForUser(whale, ripe_token) == legacy_amount
    assert (
        alternate_ripe_gov_vault.getTotalAmountForUser(whale, ripe_token)
        == replacement_amount
    )

    legacy_unlock = ripe_gov_vault.userGovData(whale, ripe_token).unlock
    if boa.env.evm.patch.block_number <= legacy_unlock:
        boa.env.time_travel(
            blocks=legacy_unlock - boa.env.evm.patch.block_number + 1
        )
    assert teller.withdraw(
        ripe_token,
        legacy_amount,
        whale,
        ripe_gov_vault,
        2,
        sender=whale,
    ) == legacy_amount
    assert ripe_gov_vault.getTotalAmountForUser(whale, ripe_token) == 0
    assert (
        alternate_ripe_gov_vault.getTotalAmountForUser(whale, ripe_token)
        == replacement_amount
    )


############################################################################
# WP1 / GOV-WEIGHT-01 (Section 5.2): zero governance weight characterization
#
# GOV-WEIGHT-01 has no autonomous default. These tests pin the exact bound
# behavior at every boundary the decision must cover and keep the preferred
# "zero means zero" rule as a Section 6.1(B) strict-xfail checkpoint.
############################################################################

# (minLockDuration, maxLockDuration, maxLockBoost, canExit, exitFee)
NO_BOOST_TERMS = (0, 0, 0, False, 0)


def _weighted_points(vault, weight, *, shares=1_000 * EIGHTEEN_DECIMALS, blocks=10):
    """Pure points calculation for `shares` held over `blocks`, at `weight`."""
    current = boa.env.evm.patch.block_number
    if current <= blocks:
        boa.env.time_travel(blocks=blocks + 1 - current)
        current = boa.env.evm.patch.block_number
    return vault.getLatestGovPoints(
        shares,
        current - blocks,
        0,
        NO_BOOST_TERMS,
        weight,
    )


def test_zero_asset_weight_yields_zero_points(ripe_gov_vault):
    """GOV-WEIGHT-01, resolved: a configured zero weight earns zero points.

    Replaces the DV-07 characterization, which asserted the defect -- the
    multiplier was guarded by `if _weight != 0`, so a zero weight skipped the
    multiplication and produced the unweighted base, i.e. behaved as 100.00%.
    The multiplier is now applied unconditionally.
    """
    unweighted = 1_000 * 10  # shares normalized by PRECISION, times blocks held

    assert _weighted_points(ripe_gov_vault, HUNDRED_PERCENT) == unweighted
    assert _weighted_points(ripe_gov_vault, 0) == 0

    # the specific confusion being closed: zero must not equal full weight
    assert _weighted_points(ripe_gov_vault, 0) != _weighted_points(
        ripe_gov_vault, HUNDRED_PERCENT
    )


def test_nonzero_asset_weight_boundaries_are_exact(ripe_gov_vault):
    """GOV-WEIGHT-01 boundary matrix for every weight the decision must cover.

    Section 5.2 requires the selected rule to be asserted at zero, one unit, one
    less than full scale, full scale, and greater than full scale. Zero lives in
    test_zero_asset_weight_yields_zero_points; the rest are here. These values are
    unchanged by the GOV-WEIGHT-01 fix, which only ever altered the zero case --
    that they still hold is the evidence the fix was surgical.
    """
    base = 1_000 * 10

    assert _weighted_points(ripe_gov_vault, 1) == base * 1 // HUNDRED_PERCENT
    assert _weighted_points(ripe_gov_vault, 50_00) == base // 2
    assert _weighted_points(ripe_gov_vault, HUNDRED_PERCENT - 1) == (
        base * (HUNDRED_PERCENT - 1) // HUNDRED_PERCENT
    )
    assert _weighted_points(ripe_gov_vault, HUNDRED_PERCENT) == base
    assert _weighted_points(ripe_gov_vault, HUNDRED_PERCENT + 1) == (
        base * (HUNDRED_PERCENT + 1) // HUNDRED_PERCENT
    )
    assert _weighted_points(ripe_gov_vault, 2 * HUNDRED_PERCENT) == base * 2

    # 500_00 is the ceiling SwitchboardAlpha._isValidRipeVaultConfig permits
    assert _weighted_points(ripe_gov_vault, 500_00) == base * 5


def test_zero_weight_deposit_accrues_no_points(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    switchboard_alpha,
    setupRipeGovVaultConfig,
):
    """GOV-WEIGHT-01 at the deposit boundary, resolved.

    Exercised through real deposits rather than the pure view, so the decision is
    bound to observable vault state and not just to the helper. Previously the DV-07
    characterization, which asserted zero weight accrued at the full-weight rate.
    """
    amount = 100 * EIGHTEEN_DECIMALS

    setupRipeGovVaultConfig(_assetWeight=HUNDRED_PERCENT, _maxLockBoost=0)
    ripe_token.transfer(ripe_gov_vault, amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(bob, ripe_token, amount, sender=teller.address)
    boa.env.time_travel(blocks=25)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    full_weight_points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints
    assert full_weight_points > 0

    setupRipeGovVaultConfig(_assetWeight=0, _maxLockBoost=0)
    ripe_token.transfer(ripe_gov_vault, amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(alice, ripe_token, amount, sender=teller.address)
    boa.env.time_travel(blocks=25)
    ripe_gov_vault.updateUserGovPoints(alice, sender=switchboard_alpha.address)
    zero_weight_points = ripe_gov_vault.userGovData(alice, ripe_token).govPoints

    # A configured zero weight earns nothing, and the deposit itself still works.
    assert zero_weight_points == 0
    assert zero_weight_points != full_weight_points
    assert ripe_gov_vault.userGovData(alice, ripe_token).lastShares > 0
    assert ripe_gov_vault.totalUserGovPoints(alice) == 0


def test_zero_asset_weight_means_zero_points(ripe_gov_vault):
    """GOV-WEIGHT-01: the Section 5.2 preferred rule, now implemented.

    Was xfail(strict=True) while the gate was unresolved. The marker is removed
    rather than the test, so the same assertion that pinned the defect now pins
    the fix -- with strict=True still set it would XPASS and fail the suite.
    """
    assert _weighted_points(ripe_gov_vault, 0) == 0


def test_zero_weight_earns_no_lock_bonus(ripe_gov_vault):
    """A zero weight must not earn a lock bonus on top of zero base points.

    The bonus is applied after the weight multiplier, so this pins the ordering:
    if the multiplier were ever moved after the bonus, a zero weight would still
    accrue boost points and this would catch it.
    """
    current = boa.env.evm.patch.block_number
    if current <= 10:
        boa.env.time_travel(blocks=11 - current)
        current = boa.env.evm.patch.block_number

    boosted_terms = (0, 100, 200_00, True, 0)  # min, max, maxLockBoost, canExit, exitFee
    unlock = current + 50

    weighted = ripe_gov_vault.getLatestGovPoints(
        1_000 * EIGHTEEN_DECIMALS, current - 10, unlock, boosted_terms, HUNDRED_PERCENT
    )
    assert weighted > 1_000 * 10  # base plus a real bonus, so the terms do boost

    assert ripe_gov_vault.getLatestGovPoints(
        1_000 * EIGHTEEN_DECIMALS, current - 10, unlock, boosted_terms, 0
    ) == 0
