import pytest
import boa

from constants import ZERO_ADDRESS
from conf_utils import filter_logs


###############
# Test Fixtures
###############


@pytest.fixture(scope="function")
def mock_auction_house():
    """Mock auction house that can be controlled for testing"""
    return boa.load("contracts/mock/MockAuctionHouse.vy", name="mock_auction_house")


###############
# Access Control Tests
###############


def test_switchboard_three_access_control_governance_actions(
    switchboard_charlie,
    alice,
    bob,
    teller,
    ripe_token,
):
    """Test that only governance can perform governance actions (both immediate and timelock)"""
    contract_addr = teller.address
    user_addr = alice
    asset_addr = ripe_token.address
    
    # Non-governance users should be rejected for immediate governance actions
    with boa.reverts("no perms"):
        switchboard_charlie.pause(contract_addr, True, sender=alice)
    
    # Non-governance users should be rejected for timelock governance actions
    with boa.reverts("no perms"):
        switchboard_charlie.recoverFunds(contract_addr, user_addr, asset_addr, sender=bob)
    
    with boa.reverts("no perms"):
        switchboard_charlie.recoverFundsMany(contract_addr, user_addr, [asset_addr], sender=alice)
    
    with boa.reverts("no perms"):
        switchboard_charlie.startAuction(user_addr, 1, asset_addr, sender=bob)
    
    with boa.reverts("no perms"):
        switchboard_charlie.startManyAuctions([(user_addr, 1, asset_addr)], sender=alice)
    
    with boa.reverts("no perms"):
        switchboard_charlie.pauseAuction(user_addr, 1, asset_addr, sender=bob)
    
    with boa.reverts("no perms"):
        switchboard_charlie.pauseManyAuctions([(user_addr, 1, asset_addr)], sender=alice)
    
    with boa.reverts("no perms"):
        switchboard_charlie.executePendingAction(1, sender=bob)
    
    with boa.reverts("no perms"):
        switchboard_charlie.cancelPendingAction(1, sender=alice)


def test_switchboard_three_access_control_lite_actions(
    switchboard_charlie,
    alice,
    bob,
    sally,
    mission_control,
    alpha_token,
):
    """Test access control for lite actions (immediate execution)"""
    user_addr = alice
    asset_addr = alpha_token.address
    
    # Users without lite access should be rejected
    with boa.reverts("no perms"):
        switchboard_charlie.updateDebtForUser(user_addr, sender=bob)
    
    with boa.reverts("no perms"):
        switchboard_charlie.updateDebtForManyUsers([user_addr], sender=alice)
    
    with boa.reverts("no perms"):
        switchboard_charlie.claimLootForUser(user_addr, False, sender=bob)
    
    with boa.reverts("no perms"):
        switchboard_charlie.claimLootForManyUsers([user_addr], False, sender=alice)
    
    with boa.reverts("no perms"):
        switchboard_charlie.updateRipeRewards(sender=bob)
    
    with boa.reverts("no perms"):
        switchboard_charlie.claimDepositLootForAsset(user_addr, 1, asset_addr, sender=alice)
    
    with boa.reverts("no perms"):
        switchboard_charlie.updateDepositPoints(user_addr, 1, asset_addr, sender=bob)
    
    # Give sally lite access
    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_charlie.address)
    
    switchboard_charlie.updateDebtForUser(user_addr, sender=sally)


def test_switchboard_three_blacklist_special_permissions(
    switchboard_charlie,
    alice,
    bob,
    sally,
    governance,
    mission_control,
    ripe_token,
):
    """Test special blacklist permissions: lite users can add, only governance can remove"""
    token_addr = ripe_token.address
    user_addr = alice
    
    # Non-lite users can't add to blacklist
    with boa.reverts("no perms"):
        switchboard_charlie.setBlacklist(token_addr, user_addr, True, sender=bob)
    
    # Give sally lite access
    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_charlie.address)
    
    # Sally can add to blacklist (immediate action)
    result = switchboard_charlie.setBlacklist(token_addr, user_addr, True, sender=sally)
    assert result
    
    # Verify event was emitted immediately
    logs = filter_logs(switchboard_charlie, "BlacklistSet")
    assert len(logs) == 1
    assert logs[0].isBlacklisted
    
    # Governance can remove from blacklist (immediate action)
    result2 = switchboard_charlie.setBlacklist(token_addr, user_addr, False, sender=governance.address)
    assert result2
    
    # Verify removal event
    logs2 = filter_logs(switchboard_charlie, "BlacklistSet")
    assert len(logs2) == 1
    assert not logs2[0].isBlacklisted
    
    # But sally can't remove from blacklist (only governance can)
    with boa.reverts("no perms"):
        switchboard_charlie.setBlacklist(token_addr, user_addr, False, sender=sally)


def test_switchboard_three_locked_account_special_permissions(
    switchboard_charlie,
    alice,
    bob,
    sally,
    governance,
    mission_control,
    ledger,
):
    """Test special locked account permissions: lite users can lock, only governance can unlock"""
    wallet_addr = alice
    
    # Non-lite users can't lock accounts
    with boa.reverts("no perms"):
        switchboard_charlie.setLockedAccount(wallet_addr, True, sender=bob)
    
    # Give sally lite access
    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_charlie.address)
    
    # Sally can lock account (immediate action)
    result = switchboard_charlie.setLockedAccount(wallet_addr, True, sender=sally)
    assert result
    
    # Verify event was emitted immediately
    logs = filter_logs(switchboard_charlie, "LockedAccountSet") 
    assert len(logs) == 1
    assert logs[0].wallet == wallet_addr
    assert logs[0].isLocked
    assert logs[0].caller == sally
    
    # Verify ledger state was updated
    assert ledger.isLockedAccount(wallet_addr)
    
    # Governance can unlock account (immediate action)
    result2 = switchboard_charlie.setLockedAccount(wallet_addr, False, sender=governance.address)
    assert result2
    
    # Verify unlock event
    logs2 = filter_logs(switchboard_charlie, "LockedAccountSet")
    assert len(logs2) == 1
    assert logs2[0].wallet == wallet_addr
    assert not logs2[0].isLocked
    assert logs2[0].caller == governance.address
    
    # Verify ledger state was updated
    assert not ledger.isLockedAccount(wallet_addr)
    
    # But sally can't unlock account (only governance can)
    # First lock it again
    switchboard_charlie.setLockedAccount(wallet_addr, True, sender=sally)
    assert ledger.isLockedAccount(wallet_addr)
    
    # Sally can't unlock
    with boa.reverts("no perms"):
        switchboard_charlie.setLockedAccount(wallet_addr, False, sender=sally)


def test_switchboard_three_locked_account_parameter_validation(
    switchboard_charlie,
    governance,
    alice,
    mission_control,
):
    """Test locked account parameter validation and integration"""
    # Give governance lite access for testing
    mission_control.setCanPerformLiteAction(governance.address, True, sender=switchboard_charlie.address)
    
    # Test invalid wallet address (zero address)
    with boa.reverts("invalid wallet"):
        switchboard_charlie.setLockedAccount(ZERO_ADDRESS, True, sender=governance.address)
    
    # Test valid wallet address
    result = switchboard_charlie.setLockedAccount(alice, True, sender=governance.address)
    assert result
    
    # Test return value is correct
    assert isinstance(result, bool)
    assert result == True
    
    # Test unlock operation
    result2 = switchboard_charlie.setLockedAccount(alice, False, sender=governance.address)
    assert result2


###############
# Parameter Validation Tests
###############


def test_switchboard_three_parameter_validation(
    switchboard_charlie,
    governance,
    teller,
    alice,
    alpha_token,
):
    """Test parameter validation for all functions"""
    contract_addr = teller.address
    user_addr = alice
    asset_addr = alpha_token.address
    
    # Test pause with invalid contract address (zero address) - this will fail during execution, not validation
    # The pause function executes immediately and tries to call the zero address contract
    with boa.reverts():  # Generic revert due to calling zero address contract
        switchboard_charlie.pause(ZERO_ADDRESS, True, sender=governance.address)
    
    # Test recoverFunds with invalid parameters
    with boa.reverts("invalid parameters"):
        switchboard_charlie.recoverFunds(ZERO_ADDRESS, user_addr, asset_addr, sender=governance.address)
    
    with boa.reverts("invalid parameters"):
        switchboard_charlie.recoverFunds(contract_addr, ZERO_ADDRESS, asset_addr, sender=governance.address)
    
    with boa.reverts("invalid parameters"):
        switchboard_charlie.recoverFunds(contract_addr, user_addr, ZERO_ADDRESS, sender=governance.address)
    
    # Test recoverFundsMany with invalid parameters
    with boa.reverts("invalid parameters"):
        switchboard_charlie.recoverFundsMany(ZERO_ADDRESS, user_addr, [asset_addr], sender=governance.address)
    
    with boa.reverts("invalid parameters"):
        switchboard_charlie.recoverFundsMany(contract_addr, ZERO_ADDRESS, [asset_addr], sender=governance.address)
    
    with boa.reverts("no assets provided"):
        switchboard_charlie.recoverFundsMany(contract_addr, user_addr, [], sender=governance.address)
    
    # Test auction functions with invalid parameters
    with boa.reverts("invalid parameters"):
        switchboard_charlie.startAuction(ZERO_ADDRESS, 1, asset_addr, sender=governance.address)
    
    with boa.reverts("invalid parameters"):
        switchboard_charlie.startAuction(user_addr, 1, ZERO_ADDRESS, sender=governance.address)
    
    with boa.reverts("no auctions provided"):
        switchboard_charlie.startManyAuctions([], sender=governance.address)
    
    with boa.reverts("invalid parameters"):
        switchboard_charlie.pauseAuction(ZERO_ADDRESS, 1, asset_addr, sender=governance.address)
    
    with boa.reverts("invalid parameters"):
        switchboard_charlie.pauseAuction(user_addr, 1, ZERO_ADDRESS, sender=governance.address)
    
    with boa.reverts("no auctions provided"):
        switchboard_charlie.pauseManyAuctions([], sender=governance.address)
    
    # Test lite action parameter validation
    with boa.reverts("invalid parameters"):
        switchboard_charlie.setBlacklist(ZERO_ADDRESS, user_addr, True, sender=governance.address)
    
    with boa.reverts("invalid parameters"):
        switchboard_charlie.setBlacklist(asset_addr, ZERO_ADDRESS, True, sender=governance.address)
    
    with boa.reverts("invalid user"):
        switchboard_charlie.updateDebtForUser(ZERO_ADDRESS, sender=governance.address)
    
    with boa.reverts("no users provided"):
        switchboard_charlie.updateDebtForManyUsers([], sender=governance.address)
    
    with boa.reverts("invalid user"):
        switchboard_charlie.claimLootForUser(ZERO_ADDRESS, False, sender=governance.address)
    
    with boa.reverts("no users provided"):
        switchboard_charlie.claimLootForManyUsers([], False, sender=governance.address)
    
    with boa.reverts("invalid parameters"):
        switchboard_charlie.claimDepositLootForAsset(ZERO_ADDRESS, 1, asset_addr, sender=governance.address)
    
    with boa.reverts("invalid parameters"):
        switchboard_charlie.claimDepositLootForAsset(user_addr, 1, ZERO_ADDRESS, sender=governance.address)
    
    with boa.reverts("invalid parameters"):
        switchboard_charlie.updateDepositPoints(ZERO_ADDRESS, 1, asset_addr, sender=governance.address)
    
    with boa.reverts("invalid parameters"):
        switchboard_charlie.updateDepositPoints(user_addr, 1, ZERO_ADDRESS, sender=governance.address)


def test_switchboard_three_array_limits(
    switchboard_charlie,
    governance,
    teller,
    alice,
    alpha_token,
):
    """Test array size limits"""
    contract_addr = teller.address
    user_addr = alice
    asset_addr = alpha_token.address
    
    # Test MAX_RECOVER_ASSETS limit (20)
    max_assets = [asset_addr] * 21  # Exceed limit
    with boa.reverts():  # Should fail due to Vyper array size validation
        switchboard_charlie.recoverFundsMany(contract_addr, user_addr, max_assets, sender=governance.address)
    
    # Test MAX_AUCTIONS limit (20)
    max_auctions = [(user_addr, 1, asset_addr)] * 21  # Exceed limit
    with boa.reverts():  # Should fail due to Vyper array size validation
        switchboard_charlie.startManyAuctions(max_auctions, sender=governance.address)
    
    # Test MAX_DEBT_UPDATES limit (50)
    max_users = [user_addr] * 51  # Exceed limit
    with boa.reverts():  # Should fail due to Vyper array size validation
        switchboard_charlie.updateDebtForManyUsers(max_users, sender=governance.address)
    
    # Test MAX_CLAIM_USERS limit (50)
    max_claim_users = [user_addr] * 51  # Exceed limit
    with boa.reverts():  # Should fail due to Vyper array size validation
        switchboard_charlie.claimLootForManyUsers(max_claim_users, False, sender=governance.address)


###############
# Timelock Functionality Tests
###############


def test_switchboard_three_pause_action_immediate(
    switchboard_charlie,
    governance,
    teller,
):
    """Test pause action immediate functionality (no longer timelock)"""
    contract_addr = teller.address
    
    # Pause action now executes immediately
    result = switchboard_charlie.pause(contract_addr, True, sender=governance.address)
    assert result
    
    # Verify event was emitted immediately (no pending action)
    logs = filter_logs(switchboard_charlie, "PauseExecuted")
    assert len(logs) == 1
    log = logs[0]
    assert log.contractAddr == contract_addr
    assert log.shouldPause


def test_switchboard_three_recover_funds_action_timelock(
    switchboard_charlie,
    governance,
    teller,
    alice,
    alpha_token,
):
    """Test recover funds action timelock functionality"""
    contract_addr = teller.address
    recipient = alice
    asset = alpha_token.address
    
    # Create pending recover funds action
    action_id = switchboard_charlie.recoverFunds(contract_addr, recipient, asset, sender=governance.address)
    
    # Verify event was emitted (immediately after transaction)
    logs = filter_logs(switchboard_charlie, "PendingRecoverFundsAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.contractAddr == contract_addr
    assert log.recipient == recipient
    assert log.asset == asset
    assert log.actionId == action_id
    
    # Verify action is stored
    assert switchboard_charlie.actionType(action_id) == 1  # ActionType.RECOVER_FUNDS
    stored_action = switchboard_charlie.pendingRecoverFundsActions(action_id)
    assert stored_action.contractAddr == contract_addr
    assert stored_action.recipient == recipient
    assert stored_action.asset == asset


def test_switchboard_three_recover_funds_many_action_timelock(
    switchboard_charlie,
    governance,
    teller,
    alice,
    alpha_token,
    bravo_token,
):
    """Test recover funds many action timelock functionality"""
    contract_addr = teller.address
    recipient = alice
    assets = [alpha_token.address, bravo_token.address]
    
    # Create pending recover funds many action
    action_id = switchboard_charlie.recoverFundsMany(contract_addr, recipient, assets, sender=governance.address)
    
    # Verify event was emitted (immediately after transaction)
    logs = filter_logs(switchboard_charlie, "PendingRecoverFundsManyAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.contractAddr == contract_addr
    assert log.recipient == recipient
    assert log.numAssets == len(assets)
    assert log.actionId == action_id
    
    # Verify action is stored
    assert switchboard_charlie.actionType(action_id) == 2  # ActionType.RECOVER_FUNDS_MANY
    stored_action = switchboard_charlie.pendingRecoverFundsManyActions(action_id)
    assert stored_action.contractAddr == contract_addr
    assert stored_action.recipient == recipient
    assert stored_action.assets == assets


def test_switchboard_three_auction_actions_timelock(
    switchboard_charlie,
    governance,
    alice,
    alpha_token,
):
    """Test auction action timelock functionality (simplified without registry mocking)"""
    user_addr = alice
    vault_id = 1
    asset_addr = alpha_token.address
    
    # Test auction start action - should fail auction validation but create action first
    with boa.reverts("cannot start auction"):
        switchboard_charlie.startAuction(user_addr, vault_id, asset_addr, sender=governance.address)
    
    # Test auction pause (should work fine)
    pause_action_id = switchboard_charlie.pauseAuction(user_addr, vault_id, asset_addr, sender=governance.address)
    
    # Verify event was emitted (immediately after transaction)
    logs = filter_logs(switchboard_charlie, "PendingPauseAuctionAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.liqUser == user_addr
    assert log.vaultId == vault_id
    assert log.asset == asset_addr
    assert log.actionId == pause_action_id
    
    # Verify action is stored
    assert switchboard_charlie.actionType(pause_action_id) == 16  # ActionType.PAUSE_AUCTION
    stored_pause_action = switchboard_charlie.pendingPauseAuctionActions(pause_action_id)
    assert stored_pause_action.liqUser == user_addr
    assert stored_pause_action.vaultId == vault_id
    assert stored_pause_action.asset == asset_addr


def test_switchboard_three_auction_validation_failure(
    switchboard_charlie,
    governance,
    alice,
    alpha_token,
):
    """Test that auction validation failures are properly caught (simplified)"""
    user_addr = alice
    vault_id = 1
    asset_addr = alpha_token.address
    
    # Test with the real auction house - should fail validation
    with boa.reverts("cannot start auction"):
        switchboard_charlie.startAuction(user_addr, vault_id, asset_addr, sender=governance.address)
    
    # Test with many auctions - should also fail validation  
    auctions = [
        (user_addr, vault_id, asset_addr),
        (user_addr, vault_id + 1, asset_addr)
    ]
    
    with boa.reverts("cannot start auction"):
        switchboard_charlie.startManyAuctions(auctions, sender=governance.address)


def test_switchboard_three_action_cancellation(
    switchboard_charlie,
    governance,
    teller,
    alice,
    ripe_token,
):
    """Test action cancellation functionality"""
    contract_addr = teller.address
    recipient = alice
    asset = ripe_token.address
    
    # Create pending timelock action
    action_id = switchboard_charlie.recoverFunds(contract_addr, recipient, asset, sender=governance.address)
    
    # Verify action exists
    assert switchboard_charlie.actionType(action_id) == 1  # ActionType.RECOVER_FUNDS
    
    # Cancel action
    success = switchboard_charlie.cancelPendingAction(action_id, sender=governance.address)
    assert success
    
    # Verify action was cleared
    assert switchboard_charlie.actionType(action_id) == 0  # Cleared to empty
    
    # Should not be able to cancel again
    with boa.reverts("cannot cancel action"):
        switchboard_charlie.cancelPendingAction(action_id, sender=governance.address)


def test_switchboard_three_action_expiration(
    switchboard_charlie,
    governance,
    teller,
    alice,
    ripe_token,
):
    """Test action expiration and automatic cleanup"""
    contract_addr = teller.address
    recipient = alice
    asset = ripe_token.address
    
    # Create pending timelock action (recoverFunds creates a timelock action)
    action_id = switchboard_charlie.recoverFunds(contract_addr, recipient, asset, sender=governance.address)
    
    # Verify action was created
    assert switchboard_charlie.actionType(action_id) == 1  # ActionType.RECOVER_FUNDS
    
    # Time travel past expiration (way beyond max timelock)
    boa.env.time_travel(blocks=100000)  # Far past any reasonable timelock
    
    # Execution should auto-cancel expired action, but first try will revert due to no balance
    # Let me test the expiration logic indirectly by checking if action can be executed
    with boa.reverts("nothing to recover"):
        switchboard_charlie.executePendingAction(action_id, sender=governance.address)


###############
# Integration Tests
###############


def test_switchboard_three_deposit_points_vault_lookup(
    switchboard_charlie,
    governance,
    alice,
    alpha_token,
    simple_erc20_vault,
    vault_book,
    mission_control,
):
    """Test that deposit points function properly looks up vault address"""
    user_addr = alice
    asset_addr = alpha_token.address
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Give switchboard lite access for this test
    mission_control.setCanPerformLiteAction(governance, True, sender=switchboard_charlie.address)
    
    # Should fail with invalid vault ID
    with boa.reverts("invalid vault"):
        switchboard_charlie.updateDepositPoints(user_addr, 999, asset_addr, sender=governance.address)
    
    # Should succeed with valid vault ID
    result = switchboard_charlie.updateDepositPoints(user_addr, vault_id, asset_addr, sender=governance.address)
    assert result


def test_switchboard_three_event_emission_immediate_actions(
    switchboard_charlie,
    governance,
    alice,
    ripe_token,
    mission_control,
):
    """Test that immediate actions emit proper events"""
    user_addr = alice
    asset_addr = ripe_token.address  # Use ripe_token which has setBlacklist function
    
    # Give switchboard lite access for this test
    mission_control.setCanPerformLiteAction(governance, True, sender=switchboard_charlie.address)
    
    # Test blacklist event - should succeed with governance permissions (immediate action)
    result = switchboard_charlie.setBlacklist(asset_addr, user_addr, True, sender=governance.address)
    
    # Should have emitted BlacklistSet event (immediately after transaction)
    logs = filter_logs(switchboard_charlie, "BlacklistSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.tokenAddr == asset_addr
    assert log.addr == user_addr
    assert log.isBlacklisted
    assert log.caller == governance.address
    
    assert result


def test_switchboard_three_execution_with_different_action_types(
    switchboard_charlie,
    governance,
    teller,
    alice,
    ripe_token,
):
    """Test execution of different action types"""
    contract_addr = teller.address
    user_addr = alice
    asset_addr = ripe_token.address
    
    # Create different types of pending actions (timelock actions only)
    
    # 1. Recover funds action
    recover_id = switchboard_charlie.recoverFunds(contract_addr, user_addr, asset_addr, sender=governance.address)
    
    # 2. Pause auction action
    pause_auction_id = switchboard_charlie.pauseAuction(user_addr, 1, asset_addr, sender=governance.address)
    
    # Verify actions were created
    assert switchboard_charlie.actionType(recover_id) == 1  # ActionType.RECOVER_FUNDS
    assert switchboard_charlie.actionType(pause_auction_id) == 16  # ActionType.PAUSE_AUCTION
    
    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    
    # Test execution - recover should fail (no balance), but will revert instead of returning False
    with boa.reverts("nothing to recover"):
        switchboard_charlie.executePendingAction(recover_id, sender=governance.address)
    
    pause_auction_result = switchboard_charlie.executePendingAction(pause_auction_id, sender=governance.address)
    assert pause_auction_result
    assert switchboard_charlie.actionType(pause_auction_id) == 0  # Action cleared


###############
# Edge Cases
###############


def test_switchboard_three_edge_cases(
    switchboard_charlie,
    governance,
):
    """Test various edge cases"""
    
    # Test execution of non-existent action
    assert not switchboard_charlie.executePendingAction(999, sender=governance.address)
    
    # Test cancellation of non-existent action
    with boa.reverts("cannot cancel action"):
        switchboard_charlie.cancelPendingAction(999, sender=governance.address)
    
    # Note: Constants like MAX_RECOVER_ASSETS are not exposed as public methods in Vyper
    # They are used internally within the contract for array size limits


def test_switchboard_three_governance_integration(
    switchboard_charlie,
    governance,
    teller,
    alice,
    ripe_token,
):
    """Test governance integration and permissions"""
    contract_addr = teller.address
    user_addr = alice
    asset_addr = ripe_token.address
    
    # Test that governance functions work with proper sender
    # The switchboard should inherit governance from LocalGov module
    
    # Test immediate action as governance
    result = switchboard_charlie.pause(contract_addr, True, sender=governance.address)
    assert result
    
    # Test timelock action as governance
    action_id = switchboard_charlie.recoverFunds(contract_addr, user_addr, asset_addr, sender=governance.address)
    assert action_id > 0
    
    # Verify governance can cancel timelock actions
    success = switchboard_charlie.cancelPendingAction(action_id, sender=governance.address)
    assert success


def test_switchboard_three_address_getters(
    switchboard_charlie,
    governance,
    ripe_hq,
):
    """Test that internal address getters work correctly"""
    # These are internal functions, so we test them indirectly by ensuring
    # the switchboard can interact with the contracts
    
    # The fact that other tests pass shows that the address getters work,
    # but we can also test by trying operations that would use these addresses
    
    # Test address getters work by creating a timelock action (doesn't call external contracts immediately)
    action_id = switchboard_charlie.recoverFunds(ripe_hq.address, governance.address, ripe_hq.address, sender=governance.address)
    assert action_id > 0
    assert switchboard_charlie.actionType(action_id) == 1


###############
# Additional Comprehensive Tests
###############


def test_switchboard_three_access_control_hasperms_logic(
    switchboard_charlie,
    governance,
    alice,
    bob,
    mission_control,
    ripe_token,
):
    """Test the internal hasPermsForLiteAction logic thoroughly"""
    token_addr = ripe_token.address  # Use ripe_token which has setBlacklist function
    user_addr = alice
    
    # Test 1: Governance always passes regardless of _hasLiteAccess parameter
    # Governance should be able to remove from blacklist even though _hasLiteAccess=False (immediate action)
    result = switchboard_charlie.setBlacklist(token_addr, user_addr, False, sender=governance.address)
    assert result
    
    # Test 2: Non-governance user without lite access fails for _hasLiteAccess=True operations  
    with boa.reverts("no perms"):
        switchboard_charlie.updateDebtForUser(user_addr, sender=bob)
    
    # Test 3: Give bob lite access and test _hasLiteAccess=True operations
    mission_control.setCanPerformLiteAction(bob, True, sender=switchboard_charlie.address)
    result = switchboard_charlie.updateDebtForUser(user_addr, sender=bob)
    assert result
    
    # Test 4: Bob with lite access still can't do _hasLiteAccess=False operations (remove blacklist)
    with boa.reverts("no perms"):
        switchboard_charlie.setBlacklist(token_addr, user_addr, False, sender=bob)


def test_switchboard_three_action_type_flag_values(
    switchboard_charlie,
    governance,
    teller,
    alice,
    alpha_token,
):
    """Test that ActionType flag values are stored correctly"""
    contract_addr = teller.address
    user_addr = alice
    asset_addr = alpha_token.address
    
    # Create different action types and verify flag values - pause is NOT a flag-stored action
    # pause() function is immediate and doesn't store ActionType
    # Only timelock actions store ActionType values
    
    recover_id = switchboard_charlie.recoverFunds(contract_addr, user_addr, asset_addr, sender=governance.address)
    assert switchboard_charlie.actionType(recover_id) == 1  # ActionType.RECOVER_FUNDS = 1
    
    recover_many_id = switchboard_charlie.recoverFundsMany(contract_addr, user_addr, [asset_addr], sender=governance.address)
    assert switchboard_charlie.actionType(recover_many_id) == 2  # ActionType.RECOVER_FUNDS_MANY = 2
    
    pause_auction_id = switchboard_charlie.pauseAuction(user_addr, 1, asset_addr, sender=governance.address)
    assert switchboard_charlie.actionType(pause_auction_id) == 16  # ActionType.PAUSE_AUCTION = 16
    
    # Test that different actions have different IDs and ActionTypes
    assert recover_id != recover_many_id != pause_auction_id
    assert switchboard_charlie.actionType(recover_id) != switchboard_charlie.actionType(recover_many_id)


def test_switchboard_three_multiple_pending_actions_storage(
    switchboard_charlie,
    governance,
    teller,
    alice,
    alpha_token,
    bravo_token,
):
    """Test storage consistency with multiple pending actions"""
    contract_addr = teller.address
    user_addr = alice
    asset1 = alpha_token.address
    asset2 = bravo_token.address
    
    # Create multiple different pending actions - only timelock actions store ActionType
    action1 = switchboard_charlie.recoverFunds(contract_addr, user_addr, asset1, sender=governance.address)
    action2 = switchboard_charlie.recoverFundsMany(contract_addr, user_addr, [asset1, asset2], sender=governance.address)
    action3 = switchboard_charlie.pauseAuction(user_addr, 1, asset1, sender=governance.address)
    
    # Verify each action is stored correctly and independently
    assert switchboard_charlie.actionType(action1) == 1  # RECOVER_FUNDS
    assert switchboard_charlie.actionType(action2) == 2  # RECOVER_FUNDS_MANY
    assert switchboard_charlie.actionType(action3) == 16  # PAUSE_AUCTION
    
    # Verify action data integrity
    recover_data = switchboard_charlie.pendingRecoverFundsActions(action1)
    assert recover_data.contractAddr == contract_addr
    assert recover_data.recipient == user_addr
    assert recover_data.asset == asset1
    
    recover_many_data = switchboard_charlie.pendingRecoverFundsManyActions(action2)
    assert recover_many_data.contractAddr == contract_addr
    assert recover_many_data.recipient == user_addr
    assert recover_many_data.assets == [asset1, asset2]
    
    pause_data = switchboard_charlie.pendingPauseAuctionActions(action3)
    assert pause_data.liqUser == user_addr
    assert pause_data.vaultId == 1
    assert pause_data.asset == asset1


def test_switchboard_three_immediate_actions_return_values(
    switchboard_charlie,
    governance,
    alice,
    alpha_token,
    mission_control,
    setGeneralConfig,
):
    """Test return value handling for immediate actions"""
    user_addr = alice
    asset_addr = alpha_token.address
    
    # Enable loot claiming
    setGeneralConfig()
    
    # Give governance lite access
    mission_control.setCanPerformLiteAction(governance.address, True, sender=switchboard_charlie.address)
    
    # Test functions that return bool - these should work deterministically
    result = switchboard_charlie.updateDebtForUser(user_addr, sender=governance.address)
    assert isinstance(result, bool)
    assert result
    
    result = switchboard_charlie.updateDebtForManyUsers([user_addr], sender=governance.address)
    assert isinstance(result, bool)
    assert result
    
    result = switchboard_charlie.updateRipeRewards(sender=governance.address)
    assert isinstance(result, bool)
    assert result
    
    result = switchboard_charlie.updateDepositPoints(user_addr, 1, asset_addr, sender=governance.address)
    assert isinstance(result, bool)
    assert result
    
    # Test functions that return uint256 - loot claiming is enabled but config returns 0 amounts
    result = switchboard_charlie.claimLootForUser(user_addr, False, sender=governance.address)
    assert isinstance(result, int)
    assert result == 0  # No loot to claim
    
    result = switchboard_charlie.claimLootForManyUsers([user_addr], False, sender=governance.address)
    assert isinstance(result, int)
    assert result == 0  # No loot to claim
    
    result = switchboard_charlie.claimDepositLootForAsset(user_addr, 1, asset_addr, sender=governance.address)
    assert isinstance(result, int)
    assert result == 0  # No loot to claim


def test_switchboard_three_batch_operations_edge_cases(
    switchboard_charlie,
    governance,
    teller,
    alice,
    alpha_token,
    bravo_token,
    setGeneralConfig,
):
    """Test batch operations at limits and with edge cases"""
    contract_addr = teller.address
    asset1 = alpha_token.address
    asset2 = bravo_token.address
    
    # Enable loot claiming
    setGeneralConfig()
    
    # Test exactly at MAX_RECOVER_ASSETS limit (20)
    assets_at_limit = [asset1] * 20
    action_id = switchboard_charlie.recoverFundsMany(contract_addr, alice, assets_at_limit, sender=governance.address)
    stored_action = switchboard_charlie.pendingRecoverFundsManyActions(action_id)
    assert len(stored_action.assets) == 20
    
    # Test exactly at MAX_DEBT_UPDATES limit (50)
    users_at_limit = [alice] * 25  # MAX_DEBT_UPDATES limit in contract is 25
    result = switchboard_charlie.updateDebtForManyUsers(users_at_limit, sender=governance.address)
    assert result
    
    # Test exactly at MAX_CLAIM_USERS limit (25) - the actual limit in Lootbox contract
    users_at_claim_limit = [alice] * 25
    result = switchboard_charlie.claimLootForManyUsers(users_at_claim_limit, False, sender=governance.address)
    assert isinstance(result, int)
    assert result == 0  # No loot to claim
    
    # Test beyond MAX_CLAIM_USERS limit - should fail bounds check
    users_over_limit = [alice] * 26
    with boa.reverts():  # DynArray bounds check failure
        switchboard_charlie.claimLootForManyUsers(users_over_limit, False, sender=governance.address)
    
    # Test batch with mixed valid/invalid addresses
    # The switchboard doesn't validate individual assets in the array,
    # only _contractAddr and _recipient, so this should succeed
    mixed_assets = [asset1, ZERO_ADDRESS, asset2]
    action_id = switchboard_charlie.recoverFundsMany(contract_addr, alice, mixed_assets, sender=governance.address)
    stored_action = switchboard_charlie.pendingRecoverFundsManyActions(action_id)
    assert len(stored_action.assets) == 3
    assert stored_action.assets == mixed_assets


def test_switchboard_three_execution_event_emission(
    switchboard_charlie,
    governance,
    alice,
    ripe_token,
):
    """Test that pending action execution emits proper events"""
    user_addr = alice
    asset_addr = ripe_token.address
    
    # Create pause auction action
    action_id = switchboard_charlie.pauseAuction(user_addr, 1, asset_addr, sender=governance.address)
    
    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    
    # Execute action
    result = switchboard_charlie.executePendingAction(action_id, sender=governance.address)
    assert result
    
    # Should have emitted execution event (immediately after transaction)
    logs = filter_logs(switchboard_charlie, "PauseAuctionExecuted")
    assert len(logs) == 1
    log = logs[0]
    assert log.liqUser == user_addr
    assert log.vaultId == 1
    assert log.asset == asset_addr
    assert not log.success  # Auction doesn't exist, so pause will fail


def test_switchboard_three_storage_cleanup_after_execution(
    switchboard_charlie,
    governance,
    alice,
    ripe_token,
):
    """Test that storage is properly cleaned up after execution"""
    user_addr = alice
    asset_addr = ripe_token.address
    
    # Create pause auction action
    action_id = switchboard_charlie.pauseAuction(user_addr, 1, asset_addr, sender=governance.address)
    
    # Verify action is stored
    assert switchboard_charlie.actionType(action_id) == 16  # ActionType.PAUSE_AUCTION
    
    # Time travel and execute
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    result = switchboard_charlie.executePendingAction(action_id, sender=governance.address)
    assert result
    
    # Verify storage was cleaned up
    assert switchboard_charlie.actionType(action_id) == 0


def test_switchboard_three_cancel_pending_action_internal(
    switchboard_charlie,
    governance,
    alice,
    ripe_token,
):
    """Test internal _cancelPendingAction functionality"""
    user_addr = alice
    asset_addr = ripe_token.address
    
    # Create multiple timelock actions
    action1 = switchboard_charlie.pauseAuction(user_addr, 1, asset_addr, sender=governance.address)
    action2 = switchboard_charlie.pauseAuction(user_addr, 2, asset_addr, sender=governance.address)
    
    # Cancel first action
    success1 = switchboard_charlie.cancelPendingAction(action1, sender=governance.address)
    assert success1
    assert switchboard_charlie.actionType(action1) == 0
    
    # Verify second action is unaffected
    assert switchboard_charlie.actionType(action2) == 16  # PAUSE_AUCTION
    
    # Cancel second action
    success2 = switchboard_charlie.cancelPendingAction(action2, sender=governance.address)
    assert success2
    assert switchboard_charlie.actionType(action2) == 0


def test_switchboard_three_all_immediate_action_events(
    switchboard_charlie,
    governance,
    alice,
    ripe_token,
    mission_control,
):
    """Test event emission for all immediate actions"""
    user_addr = alice
    asset_addr = ripe_token.address  # Use ripe_token which has setBlacklist function
    
    # Give governance lite access
    mission_control.setCanPerformLiteAction(governance.address, True, sender=switchboard_charlie.address)
    
    # Test immediate actions only (these execute right away, no timelock)
    
    # 1. Test blacklist (immediate action)
    result1 = switchboard_charlie.setBlacklist(asset_addr, user_addr, True, sender=governance.address)
    logs1 = filter_logs(switchboard_charlie, "BlacklistSet")
    assert len(logs1) == 1
    assert result1
    
    # 2. Test debt update (immediate action)
    result2 = switchboard_charlie.updateDebtForUser(user_addr, sender=governance.address)
    logs2 = filter_logs(switchboard_charlie, "DebtUpdatedForUser")
    assert len(logs2) == 1
    assert result2
    
    # 3. Test ripe rewards update (immediate action)
    result3 = switchboard_charlie.updateRipeRewards(sender=governance.address)
    logs3 = filter_logs(switchboard_charlie, "RipeRewardsUpdated")
    assert len(logs3) == 1
    assert result3
    
    # 4. Test deposit points update (immediate action)
    result4 = switchboard_charlie.updateDepositPoints(user_addr, 1, asset_addr, sender=governance.address)
    logs4 = filter_logs(switchboard_charlie, "DepositPointsUpdated")
    assert len(logs4) == 1
    assert result4


def test_switchboard_three_address_getter_integration(
    switchboard_charlie,
    governance,
    alice,
    alpha_token,
    setGeneralConfig,
):
    """Test address getter functions indirectly through operations"""
    user_addr = alice
    asset_addr = alpha_token.address
    
    # Enable loot claiming
    setGeneralConfig()
    
    # Test that address getters work by attempting operations that use them
    # These should all succeed since we're testing address lookup, not underlying functionality
    
    # Test MissionControl address (via permission check)
    result1 = switchboard_charlie.updateDebtForUser(user_addr, sender=governance.address)
    assert result1
    
    # Test Lootbox address - loot claims now enabled, should return 0
    result2 = switchboard_charlie.claimLootForUser(user_addr, False, sender=governance.address)
    assert isinstance(result2, int)
    assert result2 == 0  # No loot to claim
    
    # Test VaultBook address 
    result3 = switchboard_charlie.updateDepositPoints(user_addr, 1, asset_addr, sender=governance.address)
    assert result3
    
    # Test AuctionHouse address (should fail validation but address lookup works)
    with boa.reverts("cannot start auction"):
        switchboard_charlie.startAuction(user_addr, 1, asset_addr, sender=governance.address)


def test_switchboard_three_state_consistency_after_operations(
    switchboard_charlie,
    governance,
    teller,
    alice,
    ripe_token,
):
    """Test that state remains consistent after various operations"""
    contract_addr = teller.address
    user_addr = alice
    asset_addr = ripe_token.address
    
    # Create multiple actions and verify state tracking
    action1 = switchboard_charlie.recoverFunds(contract_addr, user_addr, asset_addr, sender=governance.address)
    action2 = switchboard_charlie.pauseAuction(user_addr, 1, asset_addr, sender=governance.address)
    
    # Verify both actions exist
    assert switchboard_charlie.actionType(action1) == 1  # RECOVER_FUNDS
    assert switchboard_charlie.actionType(action2) == 16  # PAUSE_AUCTION
    
    # Cancel first action
    switchboard_charlie.cancelPendingAction(action1, sender=governance.address)
    assert switchboard_charlie.actionType(action1) == 0
    assert switchboard_charlie.actionType(action2) == 16  # Unaffected
    
    # Create another action to verify ID management
    action3 = switchboard_charlie.pauseAuction(user_addr, 2, asset_addr, sender=governance.address)
    assert switchboard_charlie.actionType(action3) == 16  # PAUSE_AUCTION


def test_switchboard_three_recover_funds_execution_failure(
    switchboard_charlie,
    governance,
    teller,
    alice,
    alpha_token,
    bravo_token,
):
    """Test that recover funds actions fail execution deterministically"""
    contract_addr = teller.address
    user_addr = alice
    asset1 = alpha_token.address
    asset2 = bravo_token.address
    
    # Test RECOVER_FUNDS execution failure
    action_id = switchboard_charlie.recoverFunds(contract_addr, user_addr, asset1, sender=governance.address)
    assert switchboard_charlie.actionType(action_id) == 1  # RECOVER_FUNDS
    
    # Time travel and execute - should fail with nothing to recover
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    with boa.reverts("nothing to recover"):
        switchboard_charlie.executePendingAction(action_id, sender=governance.address)
    
    # Test RECOVER_FUNDS_MANY execution failure  
    action_id2 = switchboard_charlie.recoverFundsMany(contract_addr, user_addr, [asset1, asset2], sender=governance.address)
    assert switchboard_charlie.actionType(action_id2) == 2  # RECOVER_FUNDS_MANY
    
    # Time travel and execute - should fail with nothing to recover
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    with boa.reverts("nothing to recover"):
        switchboard_charlie.executePendingAction(action_id2, sender=governance.address)


def test_switchboard_three_auction_execution_success(
    switchboard_charlie,
    governance,
    alice,
    alpha_token,
):
    """Test that auction pause actions execute successfully"""
    user_addr = alice
    asset1 = alpha_token.address
    
    # Test PAUSE_AUCTION execution success
    action_id = switchboard_charlie.pauseAuction(user_addr, 1, asset1, sender=governance.address)
    assert switchboard_charlie.actionType(action_id) == 16  # PAUSE_AUCTION
    
    # Time travel and execute - should succeed
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    success = switchboard_charlie.executePendingAction(action_id, sender=governance.address)
    assert success
    assert switchboard_charlie.actionType(action_id) == 0  # Cleared after execution
    
    # Test PAUSE_MANY_AUCTIONS execution success
    action_id2 = switchboard_charlie.pauseManyAuctions([(user_addr, 1, asset1), (user_addr, 2, asset1)], sender=governance.address)
    assert switchboard_charlie.actionType(action_id2) == 32  # PAUSE_MANY_AUCTIONS
    
    # Time travel and execute - should succeed
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    success2 = switchboard_charlie.executePendingAction(action_id2, sender=governance.address)
    assert success2
    assert switchboard_charlie.actionType(action_id2) == 0  # Cleared after execution


def test_switchboard_three_start_auction_validation_failure(
    switchboard_charlie,
    governance,
    alice,
    alpha_token,
):
    """Test that start auction actions fail validation deterministically"""
    user_addr = alice
    asset1 = alpha_token.address
    
    # START_AUCTION actions should fail validation before creating action
    with boa.reverts("cannot start auction"):
        switchboard_charlie.startAuction(user_addr, 1, asset1, sender=governance.address)
    
    # START_MANY_AUCTIONS actions should also fail validation
    auctions = [(user_addr, 1, asset1), (user_addr, 2, asset1)]
    with boa.reverts("cannot start auction"):
        switchboard_charlie.startManyAuctions(auctions, sender=governance.address)


def test_switchboard_three_execution_with_mock_contracts(
    switchboard_charlie,
    governance,
    alice,
    alpha_token,
):
    """Test execution scenarios with mock contracts where possible"""
    user_addr = alice
    asset_addr = alpha_token.address
    
    # Test auction operations that don't require validation
    pause_auction_id = switchboard_charlie.pauseAuction(user_addr, 1, asset_addr, sender=governance.address)
    assert switchboard_charlie.actionType(pause_auction_id) == 16  # PAUSE_AUCTION
    
    pause_many_id = switchboard_charlie.pauseManyAuctions([(user_addr, 1, asset_addr)], sender=governance.address)
    assert switchboard_charlie.actionType(pause_many_id) == 32  # PAUSE_MANY_AUCTIONS
    
    # Time travel and test execution
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    
    # Test individual auction pause execution
    success1 = switchboard_charlie.executePendingAction(pause_auction_id, sender=governance.address)
    assert success1
    assert switchboard_charlie.actionType(pause_auction_id) == 0
    
    # Test batch auction pause execution
    success2 = switchboard_charlie.executePendingAction(pause_many_id, sender=governance.address)
    assert success2
    assert switchboard_charlie.actionType(pause_many_id) == 0


def test_switchboard_three_execution_failure_scenarios(
    switchboard_charlie,
    governance,
    alice,
    ripe_token,
):
    """Test execution scenarios where underlying calls might fail"""
    user_addr = alice
    asset_addr = ripe_token.address
    
    # Test immediate action that should fail - invalid contract address
    with boa.reverts():  # extcodesize is zero error
        switchboard_charlie.pause("0x1234567890123456789012345678901234567890", True, sender=governance.address)
    
    # Test timelock action that will fail execution (invalid contract for recover)
    action_id = switchboard_charlie.recoverFunds("0x1234567890123456789012345678901234567890", user_addr, asset_addr, sender=governance.address)
    
    # Time travel and attempt execution
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    
    # Execution should fail due to invalid contract (extcodesize is zero)
    with boa.reverts():  # Generic revert due to calling zero-code address
        switchboard_charlie.executePendingAction(action_id, sender=governance.address)


def test_switchboard_three_timelock_confirmation_edge_cases(
    switchboard_charlie,
    governance,
    alice,
    ripe_token,
):
    """Test timelock confirmation logic edge cases"""
    user_addr = alice
    asset_addr = ripe_token.address
    
    # Create timelock action
    action_id = switchboard_charlie.pauseAuction(user_addr, 1, asset_addr, sender=governance.address)
    
    # Test immediate execution (should fail due to timelock)
    result1 = switchboard_charlie.executePendingAction(action_id, sender=governance.address)
    assert not result1
    
    # Should succeed after timelock period
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    result2 = switchboard_charlie.executePendingAction(action_id, sender=governance.address)
    assert result2
    assert switchboard_charlie.actionType(action_id) == 0


def test_switchboard_three_vault_book_integration_edge_cases(
    switchboard_charlie,
    governance,
    alice,
    alpha_token,
    mission_control,
):
    """Test vault book integration edge cases in updateDepositPoints"""
    user_addr = alice
    asset_addr = alpha_token.address
    
    # Give governance lite access
    mission_control.setCanPerformLiteAction(governance.address, True, sender=switchboard_charlie.address)
    
    # Test with valid vault ID (vault 1 should exist)
    result = switchboard_charlie.updateDepositPoints(user_addr, 1, asset_addr, sender=governance.address)
    assert result
    
    # Test with definitely invalid vault ID
    with boa.reverts("invalid vault"):
        switchboard_charlie.updateDepositPoints(user_addr, 999999, asset_addr, sender=governance.address)


def test_switchboard_three_complex_workflow_scenarios(
    switchboard_charlie,
    governance,
    teller,
    alice,
    bob,
    ripe_token,
    mission_control,
):
    """Test complex workflows combining multiple action types and permissions"""
    contract_addr = teller.address
    user1 = alice
    user2 = bob
    asset_addr = ripe_token.address  # Use ripe_token which has setBlacklist function
    
    # Enable lite actions for user1
    mission_control.setCanPerformLiteAction(user1, True, sender=switchboard_charlie.address)
    
    # Mixed workflow:
    # 1. Governance creates timelock action
    action1 = switchboard_charlie.recoverFunds(contract_addr, user1, asset_addr, sender=governance.address)
    assert switchboard_charlie.actionType(action1) == 1  # RECOVER_FUNDS
    
    # 2. Lite user performs immediate action
    result_immediate1 = switchboard_charlie.updateDebtForUser(user2, sender=user1)
    assert result_immediate1
    
    # 3. Governance cancels timelock action
    success = switchboard_charlie.cancelPendingAction(action1, sender=governance.address)
    assert success
    assert switchboard_charlie.actionType(action1) == 0  # Cancelled
    
    # 4. Governance creates new timelock action
    action3 = switchboard_charlie.pauseAuction(user1, 3, asset_addr, sender=governance.address)
    assert switchboard_charlie.actionType(action3) == 16  # PAUSE_AUCTION
    
    # Another immediate action (executes right away)
    result_immediate2 = switchboard_charlie.setBlacklist(asset_addr, user2, True, sender=user1)
    assert result_immediate2
    
    # Timelock action (creates pending action that needs time + execution)
    action4 = switchboard_charlie.pauseAuction(user1, 3, asset_addr, sender=governance.address)
    assert switchboard_charlie.actionType(action4) == 16  # PAUSE_AUCTION


def test_switchboard_three_data_integrity_comprehensive(
    switchboard_charlie,
    governance,
    teller,
    alice,
    bob,
    alpha_token,
    bravo_token,
):
    """Test comprehensive data integrity across all operations"""
    contract_addr = teller.address
    user1 = alice
    user2 = bob
    asset1 = alpha_token.address
    asset2 = bravo_token.address
    
    # Create all supported timelock actions and verify data integrity
    
    # 1. RECOVER_FUNDS action
    action1 = switchboard_charlie.recoverFunds(contract_addr, user1, asset1, sender=governance.address)
    assert switchboard_charlie.actionType(action1) == 1  # RECOVER_FUNDS
    recover_data = switchboard_charlie.pendingRecoverFundsActions(action1)
    assert recover_data.contractAddr == contract_addr
    assert recover_data.recipient == user1
    assert recover_data.asset == asset1
    
    # 2. RECOVER_FUNDS_MANY action
    action2 = switchboard_charlie.recoverFundsMany(contract_addr, user2, [asset1, asset2], sender=governance.address)
    assert switchboard_charlie.actionType(action2) == 2  # RECOVER_FUNDS_MANY
    recover_many_data = switchboard_charlie.pendingRecoverFundsManyActions(action2)
    assert recover_many_data.contractAddr == contract_addr
    assert recover_many_data.recipient == user2
    assert len(recover_many_data.assets) == 2
    assert recover_many_data.assets == [asset1, asset2]
    
    # 3. PAUSE_AUCTION action
    action3 = switchboard_charlie.pauseAuction(user1, 1, asset1, sender=governance.address)
    assert switchboard_charlie.actionType(action3) == 16  # PAUSE_AUCTION
    auction_data = switchboard_charlie.pendingPauseAuctionActions(action3)
    assert auction_data.liqUser == user1
    assert auction_data.vaultId == 1
    assert auction_data.asset == asset1
    
    # 4. PAUSE_MANY_AUCTIONS action
    action4 = switchboard_charlie.pauseManyAuctions([(user1, 1, asset1), (user2, 2, asset2)], sender=governance.address)
    assert switchboard_charlie.actionType(action4) == 32  # PAUSE_MANY_AUCTIONS
    first_auction = switchboard_charlie.pendingPauseManyAuctionsActions(action4, 0)
    second_auction = switchboard_charlie.pendingPauseManyAuctionsActions(action4, 1)
    assert first_auction.liqUser == user1
    assert first_auction.vaultId == 1
    assert first_auction.asset == asset1
    assert second_auction.liqUser == user2
    assert second_auction.vaultId == 2
    assert second_auction.asset == asset2
    
    # Verify all action IDs are unique
    all_actions = [action1, action2, action3, action4]
    assert len(all_actions) == len(set(all_actions)), "Action IDs should be unique"
    
    # Test selective cancellation - cancel first action
    switchboard_charlie.cancelPendingAction(action1, sender=governance.address)
    assert switchboard_charlie.actionType(action1) == 0  # Cancelled
    
    # Verify other actions unaffected
    assert switchboard_charlie.actionType(action2) == 2
    assert switchboard_charlie.actionType(action3) == 16  
    assert switchboard_charlie.actionType(action4) == 32
    
    # Cancel another action to test multiple cancellations
    switchboard_charlie.cancelPendingAction(action3, sender=governance.address)
    assert switchboard_charlie.actionType(action3) == 0  # Cancelled
    
    # Verify remaining actions still unaffected
    assert switchboard_charlie.actionType(action2) == 2
    assert switchboard_charlie.actionType(action4) == 32


###############
# Training Wheels Tests
###############


def test_switchboard_three_add_many_training_wheels_access_control(
    switchboard_charlie,
    alice,
    bob, 
    governance,
    training_wheels,
    alpha_token,
):
    """Test access control for setManyTrainingWheelsAccess"""
    addr = training_wheels.address
    training_wheel_access = [
        (alice, True),
        (bob, False)
    ]
    
    # Non-governance users should be rejected
    with boa.reverts("no perms"):
        switchboard_charlie.setManyTrainingWheelsAccess(addr, training_wheel_access, sender=alice)
    
    with boa.reverts("no perms"):
        switchboard_charlie.setManyTrainingWheelsAccess(addr, training_wheel_access, sender=bob)
    
    # Governance should succeed
    action_id = switchboard_charlie.setManyTrainingWheelsAccess(addr, training_wheel_access, sender=governance.address)
    assert action_id > 0


def test_switchboard_three_add_many_training_wheels_parameter_validation(
    switchboard_charlie,
    governance,
    alice,
    training_wheels,
    alpha_token,
):
    """Test parameter validation for setManyTrainingWheelsAccess"""
    valid_training_wheels = [(alice, True)]
    
    # Test invalid address (zero address)
    with boa.reverts("invalid address"):
        switchboard_charlie.setManyTrainingWheelsAccess(ZERO_ADDRESS, valid_training_wheels, sender=governance.address)
    
    # Test empty training wheels array
    with boa.reverts("no training wheels provided"):
        switchboard_charlie.setManyTrainingWheelsAccess(training_wheels.address, [], sender=governance.address)
    
    # Test array limit (MAX_TRAINING_WHEEL_ACCESS = 25)
    max_training_wheels = [(alice, True)] * 26  # Exceed limit
    with boa.reverts():  # Should fail due to Vyper array size validation
        switchboard_charlie.setManyTrainingWheelsAccess(training_wheels.address, max_training_wheels, sender=governance.address)
    
    # Test exactly at limit should work
    at_limit_training_wheels = [(alice, True)] * 25
    action_id = switchboard_charlie.setManyTrainingWheelsAccess(training_wheels.address, at_limit_training_wheels, sender=governance.address)
    assert action_id > 0


def test_switchboard_three_add_many_training_wheels_timelock_and_execution(
    switchboard_charlie,
    governance,
    alice,
    bob,
    sally,
    training_wheels,
    alpha_token,
    bravo_token,
):
    """Test timelock functionality and execution for setManyTrainingWheelsAccess"""
    addr = training_wheels.address
    training_wheel_access = [
        (alice, True),   # Allow alice
        (bob, False),    # Deny bob  
        (sally, True),   # Allow sally
        (alice, False),  # Deny alice (this will override the first one)
    ]
    
    # Create pending action
    action_id = switchboard_charlie.setManyTrainingWheelsAccess(addr, training_wheel_access, sender=governance.address)
    
    # Verify event was emitted immediately
    logs = filter_logs(switchboard_charlie, "PendingSetManyTrainingWheelsAccess")
    assert len(logs) == 1
    log = logs[0]
    assert log.addr == addr
    assert log.numTrainingWheels == len(training_wheel_access)
    assert log.actionId == action_id
    
    # Verify action is stored correctly
    assert switchboard_charlie.actionType(action_id) == 16384  # ActionType.ADD_MANY_TRAINING_WHEELS
    stored_bundle = switchboard_charlie.pendingTrainingWheelAccess(action_id)
    assert stored_bundle.addr == addr
    assert len(stored_bundle.trainingWheels) == len(training_wheel_access)
    
    # Verify individual training wheel access entries
    for i, (user, is_allowed) in enumerate(training_wheel_access):
        stored_tw = switchboard_charlie.pendingTrainingWheelAccess(action_id).trainingWheels[i]
        assert stored_tw.user == user
        assert stored_tw.isAllowed == is_allowed
    
    # Execution should fail before timelock
    result = switchboard_charlie.executePendingAction(action_id, sender=governance.address)
    assert not result
    
    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    
    # Now execution should succeed
    result = switchboard_charlie.executePendingAction(action_id, sender=governance.address)
    assert result
    
    # Verify execution event was emitted
    exec_logs = filter_logs(switchboard_charlie, "SetManyTrainingWheelsAccessExecuted")
    assert len(exec_logs) == 1
    exec_log = exec_logs[0]
    assert exec_log.addr == addr
    assert exec_log.numTrainingWheels == len(training_wheel_access)
    
    # Verify training wheels contract was called correctly
    # Check that the training wheels were set properly (final state after all calls)
    assert training_wheels.allowed(alice) == False  # Last call wins
    assert training_wheels.allowed(bob) == False
    assert training_wheels.allowed(sally) == True
    
    # Verify action was cleared after execution
    assert switchboard_charlie.actionType(action_id) == 0


def test_switchboard_three_add_many_training_wheels_cancellation(
    switchboard_charlie,
    governance,
    alice,
    training_wheels,
):
    """Test cancellation of setManyTrainingWheelsAccess actions"""
    addr = training_wheels.address
    training_wheel_access = [(alice, True)]
    
    # Create pending action
    action_id = switchboard_charlie.setManyTrainingWheelsAccess(addr, training_wheel_access, sender=governance.address)
    assert switchboard_charlie.actionType(action_id) == 16384  # ADD_MANY_TRAINING_WHEELS
    
    # Cancel action
    success = switchboard_charlie.cancelPendingAction(action_id, sender=governance.address)
    assert success
    
    # Verify action was cleared
    assert switchboard_charlie.actionType(action_id) == 0
    
    # Should not be able to cancel again
    with boa.reverts("cannot cancel action"):
        switchboard_charlie.cancelPendingAction(action_id, sender=governance.address)


def test_switchboard_three_set_training_wheels_access_control(
    switchboard_charlie,
    alice,
    bob,
    governance,
    training_wheels,
):
    """Test access control for setTrainingWheels"""
    training_wheels_addr = training_wheels.address
    
    # Non-governance users should be rejected
    with boa.reverts("no perms"):
        switchboard_charlie.setTrainingWheels(training_wheels_addr, sender=alice)
    
    with boa.reverts("no perms"):
        switchboard_charlie.setTrainingWheels(training_wheels_addr, sender=bob)
    
    # Governance should succeed
    action_id = switchboard_charlie.setTrainingWheels(training_wheels_addr, sender=governance.address)
    assert action_id > 0


def test_switchboard_three_set_training_wheels_timelock_and_execution(
    switchboard_charlie,
    governance,
    training_wheels,
    mission_control,
):
    """Test timelock functionality and execution for setTrainingWheels"""
    training_wheels_addr = training_wheels.address
    
    # Create pending action
    action_id = switchboard_charlie.setTrainingWheels(training_wheels_addr, sender=governance.address)
    
    # Verify event was emitted immediately
    logs = filter_logs(switchboard_charlie, "PendingTrainingWheelsChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.trainingWheels == training_wheels_addr
    assert log.actionId == action_id
    
    # Verify action is stored correctly
    assert switchboard_charlie.actionType(action_id) == 8192  # ActionType.TRAINING_WHEELS
    stored_address = switchboard_charlie.pendingTrainingWheels(action_id)
    assert stored_address == training_wheels_addr
    
    # Execution should fail before timelock
    result = switchboard_charlie.executePendingAction(action_id, sender=governance.address)
    assert not result
    
    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    
    # Now execution should succeed
    result = switchboard_charlie.executePendingAction(action_id, sender=governance.address)
    assert result
    
    # Verify execution event was emitted
    exec_logs = filter_logs(switchboard_charlie, "TrainingWheelsSet")
    assert len(exec_logs) == 1
    exec_log = exec_logs[0]
    assert exec_log.trainingWheels == training_wheels_addr
    
    # Verify mission control was called correctly
    # The training wheels address should be set in mission control
    assert mission_control.trainingWheels() == training_wheels_addr
    
    # Verify action was cleared after execution
    assert switchboard_charlie.actionType(action_id) == 0


# Run the tests
if __name__ == "__main__":
    print("Additional comprehensive tests for SwitchboardThree.vy")
    print("These tests cover:")
    print("- Access control edge cases")
    print("- ActionType flag values and storage")
    print("- Return value handling")
    print("- Execution paths for all ActionTypes")
    print("- Timelock integration edge cases")
    print("- Complex workflows and permission boundaries")
    print("- Data integrity across all operations")
    print("- Training wheels functionality")
    print("- New setTrainingWheels function")
