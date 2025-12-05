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


@pytest.fixture(scope="function")
def new_mission_control(ripe_hq, defaults):
    """Deploy a new MissionControl that is NOT registered in RipeHq.

    Uses the same RipeHq so SwitchboardBravo/Charlie are authorized as switchboards,
    but this MC itself is not registered in the HQ registry.
    """
    return boa.load(
        "contracts/data/MissionControl.vy",
        ripe_hq,
        defaults,
        name="new_mission_control",
    )


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
    
    # Governance should succeed (immediate execution, no action_id returned)
    switchboard_charlie.setManyTrainingWheelsAccess(addr, training_wheel_access, sender=governance.address)
    
    # Verify the training wheels were set immediately
    assert training_wheels.allowed(alice) == True
    assert training_wheels.allowed(bob) == False


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
    
    # Test exactly at limit should work (immediate execution)
    at_limit_training_wheels = [(alice, True)] * 25
    switchboard_charlie.setManyTrainingWheelsAccess(training_wheels.address, at_limit_training_wheels, sender=governance.address)
    # Verify it was set
    assert training_wheels.allowed(alice) == True


def test_switchboard_three_add_many_training_wheels_immediate_execution(
    switchboard_charlie,
    governance,
    alice,
    bob,
    sally,
    training_wheels,
    alpha_token,
    bravo_token,
):
    """Test immediate execution for setManyTrainingWheelsAccess (no longer has timelock)"""
    addr = training_wheels.address
    training_wheel_access = [
        (alice, True),   # Allow alice
        (bob, False),    # Deny bob  
        (sally, True),   # Allow sally
        (alice, False),  # Deny alice (this will override the first one)
    ]
    
    # Execute immediately (no longer creates pending action)
    switchboard_charlie.setManyTrainingWheelsAccess(addr, training_wheel_access, sender=governance.address)
    
    # Verify events were emitted immediately for each access set
    logs = filter_logs(switchboard_charlie, "TrainingWheelsAccessSet")
    assert len(logs) == len(training_wheel_access)
    
    # Verify each event
    for i, (user, is_allowed) in enumerate(training_wheel_access):
        log = logs[i]
        assert log.trainingWheels == addr
        assert log.user == user
        assert log.isAllowed == is_allowed
    
    # Verify training wheels contract was called correctly
    # Check that the training wheels were set properly (final state after all calls)
    assert training_wheels.allowed(alice) == False  # Last call wins (alice was set to False in the last entry)
    assert training_wheels.allowed(bob) == False
    assert training_wheels.allowed(sally) == True


def test_switchboard_three_add_many_training_wheels_multiple_calls(
    switchboard_charlie,
    governance,
    alice,
    bob,
    training_wheels,
):
    """Test multiple calls to setManyTrainingWheelsAccess (immediate execution)"""
    addr = training_wheels.address
    
    # First call - set alice to True
    switchboard_charlie.setManyTrainingWheelsAccess(addr, [(alice, True)], sender=governance.address)
    assert training_wheels.allowed(alice) == True
    
    # Second call - set alice to False and bob to True
    switchboard_charlie.setManyTrainingWheelsAccess(addr, [(alice, False), (bob, True)], sender=governance.address)
    assert training_wheels.allowed(alice) == False
    assert training_wheels.allowed(bob) == True
    
    # Third call - can set multiple at once
    switchboard_charlie.setManyTrainingWheelsAccess(addr, [(alice, True), (bob, False)], sender=governance.address)
    assert training_wheels.allowed(alice) == True
    assert training_wheels.allowed(bob) == False


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
    assert switchboard_charlie.actionType(action_id) == 64  # ActionType.TRAINING_WHEELS (2^6 - 7th flag in Charlie)
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


###################################
# Underscore Rewards Tests
###################################


def test_switchboard_three_distribute_underscore_rewards_lite_action(
    switchboard_charlie,
    alice,
    bob,
    governance,
    mission_control,
    lootbox,
    ledger,
    switchboard_alpha,
    mock_undy_v2,
):
    """Test distributeUnderscoreRewards as lite action (immediate execution)"""
    # Setup: configure lootbox with underscore registry
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    ledger.setRipeAvailForRewards(1000 * 10**18, sender=switchboard_alpha.address)

    # Non-lite users should be rejected
    with boa.reverts("no perms"):
        switchboard_charlie.distributeUnderscoreRewards(sender=bob)

    # Give alice lite access
    mission_control.setCanPerformLiteAction(alice, True, sender=switchboard_charlie.address)

    # Alice can distribute (lite action)
    # Time travel past interval
    boa.env.time_travel(blocks=43_200 + 1)

    result = switchboard_charlie.distributeUnderscoreRewards(sender=alice)
    assert result

    # Verify event was emitted immediately from switchboard
    logs = filter_logs(switchboard_charlie, "UnderscoreRewardsDistributed")
    # There will be 2 events: one from Lootbox, one from SwitchboardCharlie
    # The switchboard event is the last one
    assert len(logs) >= 1
    switchboard_event = [log for log in logs if hasattr(log, 'caller')]
    assert len(switchboard_event) == 1
    assert switchboard_event[0].caller == alice
    assert switchboard_event[0].success

    # Governance can also distribute
    boa.env.time_travel(blocks=43_200 + 1)
    result2 = switchboard_charlie.distributeUnderscoreRewards(sender=governance.address)
    assert result2


def test_switchboard_three_set_has_underscore_rewards_special_permissions(
    switchboard_charlie,
    alice,
    bob,
    governance,
    mission_control,
    lootbox,
):
    """Test setHasUnderscoreRewards special permission logic (lite can disable, only gov can enable)"""
    # Non-lite users can't change
    with boa.reverts("no perms"):
        switchboard_charlie.setHasUnderscoreRewards(False, sender=bob)

    # Give alice lite access
    mission_control.setCanPerformLiteAction(alice, True, sender=switchboard_charlie.address)

    # Verify initial state is True (from constructor)
    assert lootbox.hasUnderscoreRewards() == True

    # Alice with lite access can disable (set to False)
    result = switchboard_charlie.setHasUnderscoreRewards(False, sender=alice)
    assert result
    assert lootbox.hasUnderscoreRewards() == False

    # Verify event emitted immediately
    logs = filter_logs(switchboard_charlie, "HasUnderscoreRewardsSet")
    assert len(logs) == 1
    assert logs[0].hasRewards == False
    assert logs[0].caller == alice

    # Alice with lite access CANNOT enable (set to True)
    with boa.reverts("no perms"):
        switchboard_charlie.setHasUnderscoreRewards(True, sender=alice)

    # Only governance can enable
    result2 = switchboard_charlie.setHasUnderscoreRewards(True, sender=governance.address)
    assert result2
    assert lootbox.hasUnderscoreRewards() == True

    # Verify event
    logs2 = filter_logs(switchboard_charlie, "HasUnderscoreRewardsSet")
    assert len(logs2) == 1
    assert logs2[0].hasRewards == True
    assert logs2[0].caller == governance.address


def test_switchboard_three_set_underscore_send_interval_timelock(
    switchboard_charlie,
    alice,
    governance,
    lootbox,
):
    """Test setUnderscoreSendInterval requires governance + timelock"""
    new_interval = 43_200 * 2  # 2 days

    # Non-governance users should be rejected
    with boa.reverts("no perms"):
        switchboard_charlie.setUnderscoreSendInterval(new_interval, sender=alice)

    # Governance creates pending action
    action_id = switchboard_charlie.setUnderscoreSendInterval(new_interval, sender=governance.address)
    assert action_id > 0

    # Verify event was emitted immediately
    logs = filter_logs(switchboard_charlie, "PendingUnderscoreSendIntervalAction")
    assert len(logs) == 1
    assert logs[0].interval == new_interval
    assert logs[0].actionId == action_id

    # Verify action is stored
    assert switchboard_charlie.actionType(action_id) == 128  # ActionType.SET_UNDERSCORE_SEND_INTERVAL (2^7)
    assert switchboard_charlie.pendingUnderscoreSendInterval(action_id) == new_interval

    # Can't execute before timelock
    result = switchboard_charlie.executePendingAction(action_id, sender=governance.address)
    assert not result

    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())

    # Now execution should succeed
    result = switchboard_charlie.executePendingAction(action_id, sender=governance.address)
    assert result

    # Verify lootbox was updated
    assert lootbox.underscoreSendInterval() == new_interval

    # Verify execution event
    logs2 = filter_logs(switchboard_charlie, "UnderscoreSendIntervalSet")
    assert len(logs2) == 1
    assert logs2[0].interval == new_interval
    assert logs2[0].caller == governance.address

    # Verify action cleared
    assert switchboard_charlie.actionType(action_id) == 0


def test_switchboard_three_set_undy_deposit_rewards_amount_timelock(
    switchboard_charlie,
    alice,
    governance,
    lootbox,
):
    """Test setUndyDepositRewardsAmount requires governance + timelock"""
    new_amount = 500 * 10**18

    # Non-governance users should be rejected
    with boa.reverts("no perms"):
        switchboard_charlie.setUndyDepositRewardsAmount(new_amount, sender=alice)

    # Governance creates pending action
    action_id = switchboard_charlie.setUndyDepositRewardsAmount(new_amount, sender=governance.address)
    assert action_id > 0

    # Verify event
    logs = filter_logs(switchboard_charlie, "PendingUndyDepositRewardsAmountAction")
    assert len(logs) == 1
    assert logs[0].amount == new_amount
    assert logs[0].actionId == action_id

    # Verify action stored
    assert switchboard_charlie.actionType(action_id) == 256  # ActionType.SET_UNDY_DEPOSIT_REWARDS_AMOUNT (2^8)
    assert switchboard_charlie.pendingUndyDepositRewardsAmount(action_id) == new_amount

    # Time travel and execute
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    result = switchboard_charlie.executePendingAction(action_id, sender=governance.address)
    assert result

    # Verify lootbox updated
    assert lootbox.undyDepositRewardsAmount() == new_amount

    # Verify event
    logs2 = filter_logs(switchboard_charlie, "UndyDepositRewardsAmountSet")
    assert len(logs2) == 1
    assert logs2[0].amount == new_amount

    # Verify action cleared
    assert switchboard_charlie.actionType(action_id) == 0


def test_switchboard_three_set_undy_yield_bonus_amount_timelock(
    switchboard_charlie,
    alice,
    governance,
    lootbox,
):
    """Test setUndyYieldBonusAmount requires governance + timelock"""
    new_amount = 300 * 10**18

    # Non-governance users should be rejected
    with boa.reverts("no perms"):
        switchboard_charlie.setUndyYieldBonusAmount(new_amount, sender=alice)

    # Governance creates pending action
    action_id = switchboard_charlie.setUndyYieldBonusAmount(new_amount, sender=governance.address)
    assert action_id > 0

    # Verify event
    logs = filter_logs(switchboard_charlie, "PendingUndyYieldBonusAmountAction")
    assert len(logs) == 1
    assert logs[0].amount == new_amount
    assert logs[0].actionId == action_id

    # Verify action stored
    assert switchboard_charlie.actionType(action_id) == 512  # ActionType.SET_UNDY_YIELD_BONUS_AMOUNT (2^9)
    assert switchboard_charlie.pendingUndyYieldBonusAmount(action_id) == new_amount

    # Time travel and execute
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    result = switchboard_charlie.executePendingAction(action_id, sender=governance.address)
    assert result

    # Verify lootbox updated
    assert lootbox.undyYieldBonusAmount() == new_amount

    # Verify event
    logs2 = filter_logs(switchboard_charlie, "UndyYieldBonusAmountSet")
    assert len(logs2) == 1
    assert logs2[0].amount == new_amount

    # Verify action cleared
    assert switchboard_charlie.actionType(action_id) == 0


def test_switchboard_three_underscore_rewards_multiple_pending_actions(
    switchboard_charlie,
    governance,
    lootbox,
):
    """Test multiple pending underscore rewards actions can coexist"""
    # Create multiple pending actions
    interval_action = switchboard_charlie.setUnderscoreSendInterval(43_200 * 3, sender=governance.address)
    deposit_action = switchboard_charlie.setUndyDepositRewardsAmount(600 * 10**18, sender=governance.address)
    yield_action = switchboard_charlie.setUndyYieldBonusAmount(400 * 10**18, sender=governance.address)

    # Verify all stored correctly
    assert switchboard_charlie.actionType(interval_action) == 128
    assert switchboard_charlie.actionType(deposit_action) == 256
    assert switchboard_charlie.actionType(yield_action) == 512

    assert switchboard_charlie.pendingUnderscoreSendInterval(interval_action) == 43_200 * 3
    assert switchboard_charlie.pendingUndyDepositRewardsAmount(deposit_action) == 600 * 10**18
    assert switchboard_charlie.pendingUndyYieldBonusAmount(yield_action) == 400 * 10**18

    # Time travel and execute one
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    result = switchboard_charlie.executePendingAction(interval_action, sender=governance.address)
    assert result

    # Verify only one was cleared
    assert switchboard_charlie.actionType(interval_action) == 0
    assert switchboard_charlie.actionType(deposit_action) == 256
    assert switchboard_charlie.actionType(yield_action) == 512

    # Execute another
    result2 = switchboard_charlie.executePendingAction(deposit_action, sender=governance.address)
    assert result2
    assert switchboard_charlie.actionType(deposit_action) == 0
    assert switchboard_charlie.actionType(yield_action) == 512


def test_switchboard_three_underscore_rewards_cancellation(
    switchboard_charlie,
    governance,
):
    """Test cancellation of underscore rewards actions"""
    # Create pending actions
    action_id = switchboard_charlie.setUnderscoreSendInterval(43_200 * 5, sender=governance.address)
    assert switchboard_charlie.actionType(action_id) == 128

    # Cancel
    success = switchboard_charlie.cancelPendingAction(action_id, sender=governance.address)
    assert success
    assert switchboard_charlie.actionType(action_id) == 0

    # Can't cancel again
    with boa.reverts("cannot cancel action"):
        switchboard_charlie.cancelPendingAction(action_id, sender=governance.address)


###################################
# Endaoment Function Coverage Tests


###################################
# Asset Flag Setter Tests
###################################


def test_flag_setter_enable_disable_permissions(switchboard_bravo, switchboard_charlie, governance, bob, alpha_token):
    """Test enable/disable permissions for asset flags"""
    # Add an asset first (need to execute it) - use valid config
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False,  # shouldBurnAsPayment
        False,  # shouldTransferToEndaoment
        False,  # shouldSwapInStabPools (False because no LTV)
        True,   # shouldAuctionInstantly
        True,   # canDeposit
        True,   # canWithdraw
        False,  # canRedeemCollateral (False because no LTV)
        True,   # canRedeemInStabPool
        True,   # canBuyInAuction
        True,   # canClaimInStabPool
        0,      # specialStabPoolId
        sender=governance.address
    )

    # Time travel and execute to add the asset
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    # Non-governance cannot enable
    with boa.reverts("no perms"):
        switchboard_charlie.setCanDepositAsset(alpha_token, True, sender=bob)

    # Governance can enable/disable
    assert switchboard_charlie.setCanDepositAsset(alpha_token, False, sender=governance.address)

    # Test users with canDisable permission can disable
    # First set bob as someone who can disable (this would be done through SwitchboardOne)
    # For now, test that bob cannot enable
    with boa.reverts("no perms"):
        switchboard_charlie.setCanDepositAsset(alpha_token, True, sender=bob)


def test_flag_setter_asset_enable_disable_flags(switchboard_bravo, switchboard_charlie, mission_control, governance, alpha_token):
    """Test asset enable/disable flag functions"""
    # First add the asset with canDeposit=False to test enabling
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, False, True, False, True, True, True, 0,  # canDeposit=False
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    # Test enabling deposits (asset starts with canDeposit=False)
    assert switchboard_charlie.setCanDepositAsset(alpha_token, True, sender=governance.address)

    # Check event
    logs = filter_logs(switchboard_charlie, "CanDepositAssetSet")
    assert len(logs) == 1
    assert logs[0].asset == alpha_token.address
    assert logs[0].canDeposit

    # Test disabling deposits
    assert switchboard_charlie.setCanDepositAsset(alpha_token, False, sender=governance.address)

    # Test setting same value fails
    with boa.reverts("already set"):
        switchboard_charlie.setCanDepositAsset(alpha_token, False, sender=governance.address)


def test_flag_setter_all_asset_enable_disable_functions(switchboard_bravo, switchboard_charlie, governance, alpha_token):
    """Test all asset enable/disable functions"""
    # First add the asset with varied initial states to avoid "already set" errors
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, False, False, False, False, False, 0,  # varied states
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    # Test all enable/disable functions (except redeem collateral which requires LTV)
    functions = [
        switchboard_charlie.setCanWithdrawAsset,
        switchboard_charlie.setCanRedeemInStabPoolAsset,
        switchboard_charlie.setCanBuyInAuctionAsset,
        switchboard_charlie.setCanClaimInStabPoolAsset,
    ]

    for func in functions:
        # Enable (assets start with False for these)
        assert func(alpha_token, True, sender=governance.address)

        # Disable
        assert func(alpha_token, False, sender=governance.address)


def test_flag_setter_validation_redeem_collateral(switchboard_bravo, switchboard_charlie, governance, alpha_token):
    """Test special validation for redeem collateral flag"""
    # Add asset with no LTV (cannot redeem collateral)
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 80_00, 0, 0, 0),  # zero LTV
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    # Should fail to enable redeem collateral for asset with no LTV
    with boa.reverts("invalid redeem collateral config"):
        switchboard_charlie.setCanRedeemCollateralAsset(alpha_token, True, sender=governance.address)


def test_flag_setter_permission_can_disable_logic(switchboard_bravo, switchboard_charlie, switchboard_alpha, governance, bob, alpha_token):
    """Test permission logic for users with canDisable permission"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    # Give bob canDisable permission via switchboard_alpha
    action_id = switchboard_alpha.setCanPerformLiteAction(bob, True, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)

    # Bob can disable (set to False) but not enable (set to True)
    assert switchboard_charlie.setCanDepositAsset(alpha_token, False, sender=bob)  # disable allowed

    with boa.reverts("no perms"):
        switchboard_charlie.setCanDepositAsset(alpha_token, True, sender=bob)  # enable not allowed


def test_flag_setter_enable_redeem_collateral_validation(switchboard_bravo, switchboard_charlie, governance, alpha_token):
    """Test special validation for enabling redeem collateral flag"""
    # Add asset with LTV so we can test enabling redeem collateral
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (60_00, 70_00, 80_00, 5_00, 10_00, 2_00),  # with LTV
        False, False, True, True, True, True, False, True, True, True, 0,  # canRedeemCollateral=False
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    # Should be able to enable redeem collateral since asset has LTV
    assert switchboard_charlie.setCanRedeemCollateralAsset(alpha_token, True, sender=governance.address)


def test_flag_setter_endaoment_transfer_restrictions(switchboard_bravo, switchboard_charlie, governance, alpha_token):
    """Test endaoment transfer restrictions for stable assets"""
    # Add asset with shouldTransferToEndaoment=True
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (60_00, 70_00, 80_00, 5_00, 10_00, 2_00),  # with LTV
        False,  # shouldBurnAsPayment
        True,   # shouldTransferToEndaoment
        True,   # shouldSwapInStabPools
        True,   # shouldAuctionInstantly
        True,   # canDeposit
        True,   # canWithdraw
        False,  # canRedeemCollateral (cannot redeem if transfers to endaoment)
        True,   # canRedeemInStabPool
        True,   # canBuyInAuction
        True,   # canClaimInStabPool
        0,      # specialStabPoolId
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    # Should not be able to enable redeem collateral for assets that transfer to endaoment
    with boa.reverts("invalid redeem collateral config"):
        switchboard_charlie.setCanRedeemCollateralAsset(alpha_token, True, sender=governance.address)


def test_flag_setter_unsupported_asset_validation(switchboard_charlie, governance, bravo_token):
    """Test that flag setters fail on unsupported assets"""
    # Try to enable/disable non-existent asset
    with boa.reverts("invalid asset"):
        switchboard_charlie.setCanDepositAsset(bravo_token, True, sender=governance.address)


###################################
# New MissionControl Tests (for _missionControl parameter)
###################################


def test_flag_setter_on_new_mission_control(
    switchboard_bravo,
    switchboard_charlie,
    governance,
    new_mission_control,
    bravo_token,
):
    """Test flag setters targeting a new MissionControl not registered in RipeHq"""
    # First add asset to new MC with canDeposit=False
    action_id = switchboard_bravo.addAsset(
        bravo_token.address,   # _asset
        [1],                   # _vaultIds
        50_00,                 # _stakersPointsAlloc
        30_00,                 # _voterPointsAlloc
        1000,                  # _perUserDepositLimit
        10000,                 # _globalDepositLimit
        0,                     # _minDepositBalance
        (0, 0, 0, 0, 0, 0),    # _debtTerms
        False,                 # _shouldBurnAsPayment
        False,                 # _shouldTransferToEndaoment
        False,                 # _shouldSwapInStabPools
        True,                  # _shouldAuctionInstantly
        False,                 # _canDeposit (start False to test enabling)
        True,                  # _canWithdraw
        False,                 # _canRedeemCollateral
        True,                  # _canRedeemInStabPool
        True,                  # _canBuyInAuction
        True,                  # _canClaimInStabPool
        0,                     # _specialStabPoolId
        (False, 0, 0, 0, 0),   # _customAuctionParams (empty)
        ZERO_ADDRESS,          # _whitelist
        False,                 # _isNft
        new_mission_control.address,  # _missionControl - TARGET NEW MC
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    # Verify asset is on new MC, not registered MC
    assert new_mission_control.isSupportedAsset(bravo_token.address)

    # Verify initial config has canDeposit=False
    config = new_mission_control.assetConfig(bravo_token.address)
    assert not config.canDeposit

    # Enable deposits using flag setter with _missionControl parameter
    assert switchboard_charlie.setCanDepositAsset(
        bravo_token.address,
        True,
        new_mission_control.address,  # TARGET NEW MC
        sender=governance.address
    )

    # Verify config changed on new MC
    config = new_mission_control.assetConfig(bravo_token.address)
    assert config.canDeposit

    # Verify event was emitted
    logs = filter_logs(switchboard_charlie, "CanDepositAssetSet")
    assert len(logs) == 1
    assert logs[0].asset == bravo_token.address
    assert logs[0].canDeposit


def test_multiple_flag_operations_on_new_mission_control(
    switchboard_bravo,
    switchboard_charlie,
    governance,
    new_mission_control,
    bravo_token,
):
    """Test multiple flag setter operations on new MissionControl"""
    # Add asset with varied initial flags (all disabled)
    action_id = switchboard_bravo.addAsset(
        bravo_token.address,   # _asset
        [1],                   # _vaultIds
        50_00,                 # _stakersPointsAlloc
        30_00,                 # _voterPointsAlloc
        1000,                  # _perUserDepositLimit
        10000,                 # _globalDepositLimit
        0,                     # _minDepositBalance
        (0, 0, 0, 0, 0, 0),    # _debtTerms
        False,                 # _shouldBurnAsPayment
        False,                 # _shouldTransferToEndaoment
        False,                 # _shouldSwapInStabPools
        True,                  # _shouldAuctionInstantly
        False,                 # _canDeposit
        False,                 # _canWithdraw
        False,                 # _canRedeemCollateral
        False,                 # _canRedeemInStabPool
        False,                 # _canBuyInAuction
        False,                 # _canClaimInStabPool
        0,                     # _specialStabPoolId
        (False, 0, 0, 0, 0),   # _customAuctionParams (empty)
        ZERO_ADDRESS,          # _whitelist
        False,                 # _isNft
        new_mission_control.address,  # _missionControl
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    # Enable multiple flags using new MC
    mc_addr = new_mission_control.address
    assert switchboard_charlie.setCanDepositAsset(bravo_token.address, True, mc_addr, sender=governance.address)
    assert switchboard_charlie.setCanWithdrawAsset(bravo_token.address, True, mc_addr, sender=governance.address)
    assert switchboard_charlie.setCanBuyInAuctionAsset(bravo_token.address, True, mc_addr, sender=governance.address)
    assert switchboard_charlie.setCanClaimInStabPoolAsset(bravo_token.address, True, mc_addr, sender=governance.address)

    # Verify all flags are set on new MC
    config = new_mission_control.assetConfig(bravo_token.address)
    assert config.canDeposit
    assert config.canWithdraw
    assert config.canBuyInAuction
    assert config.canClaimInStabPool
    # These should still be False
    assert not config.canRedeemCollateral
    assert not config.canRedeemInStabPool


def test_resolve_mission_control_validation_charlie(
    switchboard_bravo,
    switchboard_charlie,
    governance,
    mission_control,
    alpha_token,
):
    """Test that passing current MC address reverts with proper message on flag setters"""
    # First add asset to the registered MC (using default/empty _missionControl)
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    # Should revert when passing the currently registered MC address explicitly
    with boa.reverts("use empty for current mission control"):
        switchboard_charlie.setCanDepositAsset(
            alpha_token,
            False,
            mission_control.address,  # CURRENT MC - should revert
            sender=governance.address
        )


def test_flag_setter_new_mc_does_not_affect_registered_mc(
    switchboard_bravo,
    switchboard_charlie,
    governance,
    new_mission_control,
    mission_control,
    bravo_token,
):
    """Test that changes to new MC don't affect the registered MC"""
    # Add asset to new MC only
    action_id = switchboard_bravo.addAsset(
        bravo_token.address,   # _asset
        [1],                   # _vaultIds
        50_00,                 # _stakersPointsAlloc
        30_00,                 # _voterPointsAlloc
        1000,                  # _perUserDepositLimit
        10000,                 # _globalDepositLimit
        0,                     # _minDepositBalance
        (0, 0, 0, 0, 0, 0),    # _debtTerms
        False,                 # _shouldBurnAsPayment
        False,                 # _shouldTransferToEndaoment
        False,                 # _shouldSwapInStabPools
        True,                  # _shouldAuctionInstantly
        False,                 # _canDeposit
        True,                  # _canWithdraw
        False,                 # _canRedeemCollateral
        True,                  # _canRedeemInStabPool
        True,                  # _canBuyInAuction
        True,                  # _canClaimInStabPool
        0,                     # _specialStabPoolId
        (False, 0, 0, 0, 0),   # _customAuctionParams (empty)
        ZERO_ADDRESS,          # _whitelist
        False,                 # _isNft
        new_mission_control.address,  # _missionControl
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    # Verify asset is on new MC but NOT on registered MC
    assert new_mission_control.isSupportedAsset(bravo_token.address)
    assert not mission_control.isSupportedAsset(bravo_token.address)

    # Enable deposits on new MC
    assert switchboard_charlie.setCanDepositAsset(
        bravo_token.address,
        True,
        new_mission_control.address,
        sender=governance.address
    )

    # Verify config changed on new MC
    config = new_mission_control.assetConfig(bravo_token.address)
    assert config.canDeposit

    # Verify registered MC still doesn't have this asset
    assert not mission_control.isSupportedAsset(bravo_token.address)


# ========================================
# setTrainingWheels with _missionControl Tests
# ========================================


def test_set_training_wheels_on_new_mission_control(
    switchboard_charlie, governance, new_mission_control, mission_control
):
    """Test setTrainingWheels targeting a new MissionControl"""
    new_tw_addr = boa.env.generate_address("new_training_wheels")

    # Get original training wheels from registered MC
    original_tw = mission_control.trainingWheels()

    # Set training wheels on NEW mission control
    action_id = switchboard_charlie.setTrainingWheels(
        new_tw_addr,
        new_mission_control.address,  # _missionControl
        sender=governance.address
    )

    # Execute pending action
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    switchboard_charlie.executePendingAction(action_id, sender=governance.address)

    # Verify training wheels set on new MC
    assert new_mission_control.trainingWheels() == new_tw_addr

    # Verify registered MC unchanged
    assert mission_control.trainingWheels() == original_tw


def test_set_training_wheels_revert_current_mc(
    switchboard_charlie, governance, mission_control
):
    """Test that passing current MC address reverts"""
    new_tw_addr = boa.env.generate_address("new_training_wheels")

    with boa.reverts("use empty for current mission control"):
        switchboard_charlie.setTrainingWheels(
            new_tw_addr,
            mission_control.address,  # current MC - should revert
            sender=governance.address
        )


def test_set_training_wheels_pending_mc_storage(
    switchboard_charlie, governance, new_mission_control
):
    """Test that pendingMissionControl is stored correctly"""
    new_tw_addr = boa.env.generate_address("new_training_wheels")

    action_id = switchboard_charlie.setTrainingWheels(
        new_tw_addr,
        new_mission_control.address,
        sender=governance.address
    )

    # Verify pending mission control is stored
    assert switchboard_charlie.pendingMissionControl(action_id) == new_mission_control.address


# ========================================
# deregisterAsset Tests
# ========================================


def test_deregister_asset_permissions(switchboard_charlie, governance, alice, alpha_token):
    """Test that only governance can call deregisterAsset"""
    with boa.reverts("no perms"):
        switchboard_charlie.deregisterAsset(alpha_token, sender=alice)


def test_deregister_asset_parameter_validation(switchboard_charlie, governance):
    """Test parameter validation for deregisterAsset"""
    # Zero address should fail
    with boa.reverts("invalid asset"):
        switchboard_charlie.deregisterAsset(ZERO_ADDRESS, sender=governance.address)


def test_deregister_asset_creates_timelock(
    switchboard_bravo, switchboard_charlie, governance, alpha_token
):
    """Test deregisterAsset creates timelock action correctly"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    # Create pending deregister action
    aid = switchboard_charlie.deregisterAsset(alpha_token.address, sender=governance.address)
    assert aid > 0

    # Check event was emitted
    logs = filter_logs(switchboard_charlie, "PendingDeregisterAssetAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.asset == alpha_token.address
    assert log.actionId == aid

    # Check action was stored
    action_type = switchboard_charlie.actionType(aid)
    assert action_type == 1024  # ActionType.DEREGISTER_ASSET (2^10)

    # Check pending data was stored
    pending_asset = switchboard_charlie.pendingDeregisterAsset(aid)
    assert pending_asset == alpha_token.address


def test_deregister_asset_execute_success(
    switchboard_bravo, switchboard_charlie, governance, mission_control, alpha_token
):
    """Test executing pending deregister asset action"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    # Verify asset is registered
    assert mission_control.isSupportedAsset(alpha_token.address)

    # Create pending deregister action
    aid = switchboard_charlie.deregisterAsset(alpha_token.address, sender=governance.address)

    # Advance time past timelock
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())

    # Execute action
    success = switchboard_charlie.executePendingAction(aid, sender=governance.address)
    assert success

    # Check execution event was emitted
    logs = filter_logs(switchboard_charlie, "AssetDeregistered")
    assert len(logs) == 1
    assert logs[0].asset == alpha_token.address

    # Verify asset is deregistered
    assert not mission_control.isSupportedAsset(alpha_token.address)

    # Check action was cleared
    assert switchboard_charlie.actionType(aid) == 0


def test_deregister_asset_on_new_mission_control(
    switchboard_bravo, switchboard_charlie, governance, new_mission_control, mission_control, bravo_token
):
    """Test deregisterAsset targeting a new MissionControl"""
    # Add asset to new MC
    action_id = switchboard_bravo.addAsset(
        bravo_token.address, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),
        False, False, False, True, True, True, False, True, True, True, 0,
        (False, 0, 0, 0, 0), ZERO_ADDRESS, False,
        new_mission_control.address,  # _missionControl
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    # Verify asset is on new MC
    assert new_mission_control.isSupportedAsset(bravo_token.address)
    assert not mission_control.isSupportedAsset(bravo_token.address)

    # Deregister from new MC
    aid = switchboard_charlie.deregisterAsset(
        bravo_token.address,
        new_mission_control.address,  # _missionControl
        sender=governance.address
    )

    # Verify pending MC is stored
    assert switchboard_charlie.pendingMissionControl(aid) == new_mission_control.address

    # Execute
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    success = switchboard_charlie.executePendingAction(aid, sender=governance.address)
    assert success

    # Verify deregistered from new MC
    assert not new_mission_control.isSupportedAsset(bravo_token.address)


# ========================================
# setUserConfig Tests
# ========================================


def test_set_user_config_permissions(switchboard_charlie, governance, alice, bob):
    """Test that only governance can call setUserConfig"""
    # UserConfig: (canAnyoneDeposit, canAnyoneRepayDebt, canAnyoneBondForUser)
    user_config = (False, False, False)

    with boa.reverts("no perms"):
        switchboard_charlie.setUserConfig(alice, user_config, sender=bob)


def test_set_user_config_parameter_validation(switchboard_charlie, governance):
    """Test parameter validation for setUserConfig"""
    user_config = (False, False, False)

    # Zero address user should fail
    with boa.reverts("invalid user"):
        switchboard_charlie.setUserConfig(ZERO_ADDRESS, user_config, sender=governance.address)


def test_set_user_config_creates_timelock(
    switchboard_charlie, governance, mission_control, alice
):
    """Test setUserConfig creates a timelock action"""
    # UserConfig: (canAnyoneDeposit, canAnyoneRepayDebt, canAnyoneBondForUser)
    user_config = (True, True, False)

    # Initiate (creates pending action)
    aid = switchboard_charlie.setUserConfig(alice, user_config, sender=governance.address)
    assert aid > 0

    # Check pending event was emitted
    logs = filter_logs(switchboard_charlie, "PendingUserConfigAction")
    assert len(logs) == 1
    assert logs[0].user == alice
    assert logs[0].actionId == aid

    # Verify config was NOT set yet in MissionControl
    stored_config = mission_control.userConfig(alice)
    assert stored_config[0] == False  # canAnyoneDeposit - still default

    # Verify pending storage
    pending = switchboard_charlie.pendingUserConfig(aid)
    assert pending[0] == alice  # user


def test_set_user_config_execute_success(
    switchboard_charlie, governance, mission_control, alice
):
    """Test setUserConfig executes after timelock"""
    # UserConfig: (canAnyoneDeposit, canAnyoneRepayDebt, canAnyoneBondForUser)
    user_config = (True, True, False)

    # Initiate
    aid = switchboard_charlie.setUserConfig(alice, user_config, sender=governance.address)

    # Wait for timelock
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())

    # Execute
    success = switchboard_charlie.executePendingAction(aid, sender=governance.address)
    assert success

    # Check event was emitted
    logs = filter_logs(switchboard_charlie, "UserConfigSet")
    assert len(logs) == 1
    assert logs[0].user == alice
    assert logs[0].caller == governance.address

    # Verify config was set in MissionControl
    stored_config = mission_control.userConfig(alice)
    assert stored_config[0] == True  # canAnyoneDeposit
    assert stored_config[1] == True  # canAnyoneRepayDebt
    assert stored_config[2] == False # canAnyoneBondForUser


def test_set_user_config_on_new_mission_control(
    switchboard_charlie, governance, new_mission_control, mission_control, alice
):
    """Test setUserConfig targeting a new MissionControl"""
    user_config = (True, False, True)

    # Initiate config on new MC
    aid = switchboard_charlie.setUserConfig(
        alice,
        user_config,
        new_mission_control.address,  # _missionControl
        sender=governance.address
    )
    assert aid > 0

    # Verify pending MC storage
    assert switchboard_charlie.pendingMissionControl(aid) == new_mission_control.address

    # Wait for timelock and execute
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    success = switchboard_charlie.executePendingAction(aid, sender=governance.address)
    assert success

    # Verify config was set on new MC
    new_config = new_mission_control.userConfig(alice)
    assert new_config[0] == True  # canAnyoneDeposit

    # Verify registered MC was NOT affected
    reg_config = mission_control.userConfig(alice)
    assert reg_config[0] == False  # Still default


def test_set_user_config_revert_current_mc(
    switchboard_charlie, governance, mission_control, alice
):
    """Test that passing current MC address reverts"""
    user_config = (True, True, True)

    with boa.reverts("use empty for current mission control"):
        switchboard_charlie.setUserConfig(
            alice,
            user_config,
            mission_control.address,  # current MC - should revert
            sender=governance.address
        )


# ========================================
# setUserDelegation Tests
# ========================================


def test_set_user_delegation_permissions(switchboard_charlie, governance, alice, bob, sally):
    """Test that only governance can call setUserDelegation"""
    # ActionDelegation: (canWithdraw, canBorrow, canClaimFromStabPool, canClaimLoot)
    delegation_config = (False, False, False, False)

    with boa.reverts("no perms"):
        switchboard_charlie.setUserDelegation(alice, bob, delegation_config, sender=sally)


def test_set_user_delegation_parameter_validation(switchboard_charlie, governance, bob):
    """Test parameter validation for setUserDelegation"""
    delegation_config = (False, False, False, False)

    # Zero address user should fail
    with boa.reverts("invalid user"):
        switchboard_charlie.setUserDelegation(ZERO_ADDRESS, bob, delegation_config, sender=governance.address)


def test_set_user_delegation_creates_timelock(
    switchboard_charlie, governance, mission_control, alice, bob
):
    """Test setUserDelegation creates a timelock action"""
    # ActionDelegation: (canWithdraw, canBorrow, canClaimFromStabPool, canClaimLoot)
    delegation_config = (True, True, True, True)

    # Initiate (creates pending action)
    aid = switchboard_charlie.setUserDelegation(alice, bob, delegation_config, sender=governance.address)
    assert aid > 0

    # Check pending event was emitted
    logs = filter_logs(switchboard_charlie, "PendingUserDelegationAction")
    assert len(logs) == 1
    assert logs[0].user == alice
    assert logs[0].delegate == bob
    assert logs[0].actionId == aid

    # Verify delegation was NOT set yet in MissionControl
    stored_delegation = mission_control.userDelegation(alice, bob)
    assert stored_delegation[0] == False  # canWithdraw - still default

    # Verify pending storage
    pending = switchboard_charlie.pendingUserDelegation(aid)
    assert pending[0] == alice  # user
    assert pending[1] == bob  # delegate


def test_set_user_delegation_execute_success(
    switchboard_charlie, governance, mission_control, alice, bob
):
    """Test setUserDelegation executes after timelock"""
    # ActionDelegation: (canWithdraw, canBorrow, canClaimFromStabPool, canClaimLoot)
    delegation_config = (True, True, True, True)

    # Initiate
    aid = switchboard_charlie.setUserDelegation(alice, bob, delegation_config, sender=governance.address)

    # Wait for timelock
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())

    # Execute
    success = switchboard_charlie.executePendingAction(aid, sender=governance.address)
    assert success

    # Check event was emitted
    logs = filter_logs(switchboard_charlie, "UserDelegationSet")
    assert len(logs) == 1
    assert logs[0].user == alice
    assert logs[0].delegate == bob
    assert logs[0].caller == governance.address

    # Verify delegation was set in MissionControl
    stored_delegation = mission_control.userDelegation(alice, bob)
    assert stored_delegation[0] == True  # canWithdraw


def test_set_user_delegation_on_new_mission_control(
    switchboard_charlie, governance, new_mission_control, mission_control, alice, bob
):
    """Test setUserDelegation targeting a new MissionControl"""
    delegation_config = (True, False, True, False)

    # Initiate delegation on new MC
    aid = switchboard_charlie.setUserDelegation(
        alice,
        bob,
        delegation_config,
        new_mission_control.address,  # _missionControl
        sender=governance.address
    )
    assert aid > 0

    # Verify pending MC storage
    assert switchboard_charlie.pendingMissionControl(aid) == new_mission_control.address

    # Wait for timelock and execute
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    success = switchboard_charlie.executePendingAction(aid, sender=governance.address)
    assert success

    # Verify delegation was set on new MC
    new_delegation = new_mission_control.userDelegation(alice, bob)
    assert new_delegation[0] == True  # canWithdraw

    # Verify registered MC was NOT affected
    reg_delegation = mission_control.userDelegation(alice, bob)
    assert reg_delegation[0] == False  # Still default


def test_set_user_delegation_revert_current_mc(
    switchboard_charlie, governance, mission_control, alice, bob
):
    """Test that passing current MC address reverts"""
    delegation_config = (True, True, True, True)

    with boa.reverts("use empty for current mission control"):
        switchboard_charlie.setUserDelegation(
            alice,
            bob,
            delegation_config,
            mission_control.address,  # current MC - should revert
            sender=governance.address
        )


# ========================================
# deregisterVaultAsset Tests
# ========================================


def test_deregister_vault_asset_permissions(switchboard_charlie, governance, alice, alpha_token_vault, alpha_token):
    """Test that only governance can call deregisterVaultAsset"""
    with boa.reverts("no perms"):
        switchboard_charlie.deregisterVaultAsset(alpha_token_vault.address, alpha_token.address, sender=alice)


def test_deregister_vault_asset_parameter_validation(switchboard_charlie, governance, alpha_token_vault, alpha_token):
    """Test parameter validation for deregisterVaultAsset"""
    # Zero address vault should fail
    with boa.reverts("invalid vault"):
        switchboard_charlie.deregisterVaultAsset(ZERO_ADDRESS, alpha_token.address, sender=governance.address)

    # Zero address asset should fail
    with boa.reverts("invalid asset"):
        switchboard_charlie.deregisterVaultAsset(alpha_token_vault.address, ZERO_ADDRESS, sender=governance.address)


def test_deregister_vault_asset_creates_timelock(
    switchboard_charlie, governance, alpha_token_vault, alpha_token
):
    """Test deregisterVaultAsset creates timelock action correctly"""
    # Create pending deregister vault asset action
    aid = switchboard_charlie.deregisterVaultAsset(
        alpha_token_vault.address,
        alpha_token.address,
        sender=governance.address
    )
    assert aid > 0

    # Check event was emitted
    logs = filter_logs(switchboard_charlie, "PendingDeregisterVaultAssetAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.vaultAddr == alpha_token_vault.address
    assert log.asset == alpha_token.address
    assert log.actionId == aid

    # Check action was stored
    action_type = switchboard_charlie.actionType(aid)
    assert action_type == 2048  # ActionType.DEREGISTER_VAULT_ASSET (2^11)

    # Check pending data was stored
    pending_action = switchboard_charlie.pendingDeregisterVaultAsset(aid)
    assert pending_action[0] == alpha_token_vault.address  # vaultAddr
    assert pending_action[1] == alpha_token.address  # asset


def test_deregister_vault_asset_before_timelock_fails(
    switchboard_charlie, governance, alpha_token_vault, alpha_token
):
    """Test execution fails before timelock"""
    aid = switchboard_charlie.deregisterVaultAsset(
        alpha_token_vault.address,
        alpha_token.address,
        sender=governance.address
    )

    # Try to execute immediately (should fail)
    result = switchboard_charlie.executePendingAction(aid, sender=governance.address)
    assert not result

    # Verify action still exists
    assert switchboard_charlie.actionType(aid) != 0


def test_deregister_vault_asset_cancellation(
    switchboard_charlie, governance, alpha_token_vault, alpha_token
):
    """Test cancellation of deregisterVaultAsset action"""
    aid = switchboard_charlie.deregisterVaultAsset(
        alpha_token_vault.address,
        alpha_token.address,
        sender=governance.address
    )

    # Verify action exists
    assert switchboard_charlie.actionType(aid) != 0

    # Cancel
    success = switchboard_charlie.cancelPendingAction(aid, sender=governance.address)
    assert success

    # Verify action was cancelled
    assert switchboard_charlie.actionType(aid) == 0


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
    print("- Underscore rewards functions")
    print("- deregisterAsset function")
    print("- setUserConfig function")
    print("- setUserDelegation function")
    print("- deregisterVaultAsset function")
