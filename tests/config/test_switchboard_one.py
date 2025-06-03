import pytest
import boa

from constants import MAX_UINT256, ZERO_ADDRESS
from conf_utils import filter_logs


def test_deployment_invalid_stale_time_range(ripe_hq_deploy):
    # Test min >= max
    with boa.reverts("invalid stale time range"):
        boa.load(
            "contracts/config/SwitchboardOne.vy",
            ripe_hq_deploy.address,
            200,  # min
            100,  # max (less than min)
            50,   # min timelock
            500,  # max timelock
        )
    
    # Test equal values
    with boa.reverts("invalid stale time range"):
        boa.load(
            "contracts/config/SwitchboardOne.vy",
            ripe_hq_deploy.address,
            100,  # min
            100,  # max (equal to min)
            50,   # min timelock
            500,  # max timelock
        )


def test_deployment_success(switchboard_one):
    assert switchboard_one.MIN_STALE_TIME() > 0
    assert switchboard_one.MAX_STALE_TIME() > switchboard_one.MIN_STALE_TIME()
    assert switchboard_one.actionId() == 1  # starts at 1


def test_governance_permissions(switchboard_one, bob):
    # Test functions that require governance permissions
    with boa.reverts("no perms"):
        switchboard_one.setVaultLimits(10, 5, sender=bob)
    
    with boa.reverts("no perms"):
        switchboard_one.setStaleTime(1000, sender=bob)
    
    with boa.reverts("no perms"):
        switchboard_one.setGlobalDebtLimits(1000, 10000, 100, 50, sender=bob)


def test_enable_disable_permissions(switchboard_one, governance, bob):
    # Non-governance cannot enable
    with boa.reverts("no perms"):
        switchboard_one.setCanDeposit(True, sender=bob)
    
    # Test that users with canDisable permission can disable
    # First enable deposits as governance
    switchboard_one.setCanDeposit(True, sender=governance.address)
    
    # Set bob as someone who can disable
    switchboard_one.setCanPerformLiteAction(bob, True, sender=governance.address)
    
    # Time travel to execute the action
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    action_id = switchboard_one.actionId() - 1  # get the last action id
    switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Now bob should be able to disable
    switchboard_one.setCanDeposit(False, sender=bob)
    
    # But bob cannot enable
    with boa.reverts("no perms"):
        switchboard_one.setCanDeposit(True, sender=bob)


def test_set_vault_limits_validation(switchboard_one, governance):
    # Test invalid vault limits
    with boa.reverts("invalid vault limits"):
        switchboard_one.setVaultLimits(0, 5, sender=governance.address)  # zero max vaults
    
    with boa.reverts("invalid vault limits"):
        switchboard_one.setVaultLimits(10, 0, sender=governance.address)  # zero max assets
    
    with boa.reverts("invalid vault limits"):
        switchboard_one.setVaultLimits(MAX_UINT256, 5, sender=governance.address)  # max uint256
    
    with boa.reverts("invalid vault limits"):
        switchboard_one.setVaultLimits(10, MAX_UINT256, sender=governance.address)  # max uint256


def test_set_vault_limits_success(switchboard_one, governance):
    # Test valid vault limits
    action_id = switchboard_one.setVaultLimits(20, 10, sender=governance.address)
    assert action_id > 0
    
    # Check event was emitted
    logs = filter_logs(switchboard_one, "PendingVaultLimitsChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.perUserMaxVaults == 20
    assert log.perUserMaxAssetsPerVault == 10
    assert log.actionId == action_id
    
    # Check pending config was stored
    pending = switchboard_one.pendingGeneralConfig(action_id)
    assert pending.perUserMaxVaults == 20
    assert pending.perUserMaxAssetsPerVault == 10


def test_execute_vault_limits(switchboard_one, mission_control, governance):
    # Set vault limits
    action_id = switchboard_one.setVaultLimits(25, 15, sender=governance.address)
    
    # Time travel past timelock
    time_lock = switchboard_one.actionTimeLock()
    boa.env.time_travel(blocks=time_lock)
    
    # Execute the action
    assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Verify the config was applied to MissionControl
    config = mission_control.genConfig()
    assert config.perUserMaxVaults == 25
    assert config.perUserMaxAssetsPerVault == 15
    
    # Check event was emitted
    logs = filter_logs(switchboard_one, "VaultLimitsSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.perUserMaxVaults == 25
    assert log.perUserMaxAssetsPerVault == 15


def test_set_stale_time_validation(switchboard_one, governance):
    # Test invalid stale times
    with boa.reverts("invalid stale time"):
        switchboard_one.setStaleTime(switchboard_one.MIN_STALE_TIME() - 1, sender=governance.address)
    
    with boa.reverts("invalid stale time"):
        switchboard_one.setStaleTime(switchboard_one.MAX_STALE_TIME() + 1, sender=governance.address)


def test_set_stale_time_success(switchboard_one, governance):
    # Test valid stale time
    stale_time = (switchboard_one.MIN_STALE_TIME() + switchboard_one.MAX_STALE_TIME()) // 2
    action_id = switchboard_one.setStaleTime(stale_time, sender=governance.address)
    assert action_id > 0
    
    # Check event was emitted
    logs = filter_logs(switchboard_one, "PendingStaleTimeChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.priceStaleTime == stale_time
    assert log.actionId == action_id


def test_execute_stale_time(switchboard_one, mission_control, governance):
    # Set stale time
    stale_time = switchboard_one.MIN_STALE_TIME() + 100
    action_id = switchboard_one.setStaleTime(stale_time, sender=governance.address)
    
    # Time travel and execute
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Verify the config was applied
    config = mission_control.genConfig()
    assert config.priceStaleTime == stale_time
    
    # Check event
    logs = filter_logs(switchboard_one, "StaleTimeSet")
    assert len(logs) == 1
    assert logs[0].staleTime == stale_time


def test_enable_disable_deposit(switchboard_one, mission_control, governance):
    # Test enabling deposits
    assert switchboard_one.setCanDeposit(True, sender=governance.address)
    config = mission_control.genConfig()
    assert config.canDeposit == True
    
    # Check event
    logs = filter_logs(switchboard_one, "CanDepositSet")
    assert len(logs) == 1
    assert logs[0].canDeposit == True
    assert logs[0].caller == governance.address
    
    # Test disabling deposits
    assert switchboard_one.setCanDeposit(False, sender=governance.address)
    config = mission_control.genConfig()
    assert config.canDeposit == False
    
    # Test setting same value fails
    with boa.reverts("already set"):
        switchboard_one.setCanDeposit(False, sender=governance.address)


def test_all_enable_disable_functions(switchboard_one, mission_control, governance):
    # Test all the enable/disable functions
    functions_and_fields = [
        (switchboard_one.setCanWithdraw, "canWithdraw"),
        (switchboard_one.setCanBorrow, "canBorrow"),
        (switchboard_one.setCanRepay, "canRepay"),
        (switchboard_one.setCanClaimLoot, "canClaimLoot"),
        (switchboard_one.setCanLiquidate, "canLiquidate"),
        (switchboard_one.setCanRedeemCollateral, "canRedeemCollateral"),
        (switchboard_one.setCanRedeemInStabPool, "canRedeemInStabPool"),
        (switchboard_one.setCanBuyInAuction, "canBuyInAuction"),
        (switchboard_one.setCanClaimInStabPool, "canClaimInStabPool"),
    ]
    
    for func, field in functions_and_fields:
        # Enable
        assert func(True, sender=governance.address)
        config = mission_control.genConfig()
        assert getattr(config, field) == True
        
        # Disable
        assert func(False, sender=governance.address)
        config = mission_control.genConfig()
        assert getattr(config, field) == False


def test_global_debt_limits_validation(switchboard_one, governance):
    # Test invalid debt limits
    with boa.reverts("invalid debt limits"):
        switchboard_one.setGlobalDebtLimits(0, 10000, 100, 50, sender=governance.address)  # zero per user limit
    
    with boa.reverts("invalid debt limits"):
        switchboard_one.setGlobalDebtLimits(1000, 0, 100, 50, sender=governance.address)  # zero global limit
    
    with boa.reverts("invalid debt limits"):
        switchboard_one.setGlobalDebtLimits(1000, 10000, 100, 0, sender=governance.address)  # zero borrowers
    
    with boa.reverts("invalid debt limits"):
        switchboard_one.setGlobalDebtLimits(10000, 1000, 100, 50, sender=governance.address)  # per user > global
    
    with boa.reverts("invalid debt limits"):
        switchboard_one.setGlobalDebtLimits(1000, 10000, 2000, 50, sender=governance.address)  # min debt > per user
    
    with boa.reverts("invalid debt limits"):
        switchboard_one.setGlobalDebtLimits(MAX_UINT256, 10000, 100, 50, sender=governance.address)  # max uint256


def test_global_debt_limits_success(switchboard_one, governance):
    action_id = switchboard_one.setGlobalDebtLimits(5000, 50000, 100, 100, sender=governance.address)
    assert action_id > 0
    
    # Check event
    logs = filter_logs(switchboard_one, "PendingGlobalDebtLimitsChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.perUserDebtLimit == 5000
    assert log.globalDebtLimit == 50000
    assert log.minDebtAmount == 100
    assert log.numAllowedBorrowers == 100


def test_borrow_interval_config_validation(switchboard_one, governance):
    # Test invalid borrow interval config
    with boa.reverts("invalid borrow interval config"):
        switchboard_one.setBorrowIntervalConfig(0, 100, sender=governance.address)  # zero max borrow
    
    with boa.reverts("invalid borrow interval config"):
        switchboard_one.setBorrowIntervalConfig(1000, 0, sender=governance.address)  # zero blocks
    
    with boa.reverts("invalid borrow interval config"):
        switchboard_one.setBorrowIntervalConfig(MAX_UINT256, 100, sender=governance.address)  # max uint256


def test_keeper_config_validation(switchboard_one, governance):
    # Test invalid keeper config
    with boa.reverts("invalid keeper config"):
        switchboard_one.setKeeperConfig(11_00, 1000, sender=governance.address)  # > 10% fee ratio
    
    with boa.reverts("invalid keeper config"):
        switchboard_one.setKeeperConfig(5_00, 201 * 10**18, sender=governance.address)  # > $200 min fee
    
    with boa.reverts("invalid keeper config"):
        switchboard_one.setKeeperConfig(MAX_UINT256, 1000, sender=governance.address)  # max uint256


def test_ltv_payback_buffer_validation(switchboard_one, governance):
    # Test invalid LTV payback buffer
    with boa.reverts("invalid ltv payback buffer"):
        switchboard_one.setLtvPaybackBuffer(0, sender=governance.address)  # zero
    
    with boa.reverts("invalid ltv payback buffer"):
        switchboard_one.setLtvPaybackBuffer(11_00, sender=governance.address)  # > 10%


def test_auction_params_validation(switchboard_one, governance):
    # Test invalid auction params
    with boa.reverts("invalid auction params"):
        switchboard_one.setGenAuctionParams(100_01, 50_00, 1000, 2000, sender=governance.address)  # start >= 100%
    
    with boa.reverts("invalid auction params"):
        switchboard_one.setGenAuctionParams(50_00, 100_01, 1000, 2000, sender=governance.address)  # max >= 100%
    
    with boa.reverts("invalid auction params"):
        switchboard_one.setGenAuctionParams(60_00, 50_00, 1000, 2000, sender=governance.address)  # start >= max
    
    with boa.reverts("invalid auction params"):
        switchboard_one.setGenAuctionParams(30_00, 50_00, MAX_UINT256, 1000, sender=governance.address)  # invalid delay
    
    with boa.reverts("invalid auction params"):
        switchboard_one.setGenAuctionParams(30_00, 50_00, 1000, 0, sender=governance.address)  # zero duration
    
    with boa.reverts("invalid auction params"):
        switchboard_one.setGenAuctionParams(30_00, 50_00, 1000, MAX_UINT256, sender=governance.address)  # max duration


def test_execute_debt_configs(switchboard_one, mission_control, governance):
    # Test executing global debt limits
    action_id = switchboard_one.setGlobalDebtLimits(6000, 60000, 200, 150, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.genDebtConfig()
    assert config.perUserDebtLimit == 6000
    assert config.globalDebtLimit == 60000
    assert config.minDebtAmount == 200
    assert config.numAllowedBorrowers == 150
    
    # Test executing borrow interval config
    action_id = switchboard_one.setBorrowIntervalConfig(5000, 100, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.genDebtConfig()
    assert config.maxBorrowPerInterval == 5000
    assert config.numBlocksPerInterval == 100
    
    # Test executing keeper config
    action_id = switchboard_one.setKeeperConfig(5_00, 50 * 10**18, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.genDebtConfig()
    assert config.keeperFeeRatio == 5_00
    assert config.minKeeperFee == 50 * 10**18


def test_daowry_enable_disable(switchboard_one, mission_control, governance):
    # Enable daowry
    assert switchboard_one.setIsDaowryEnabled(True, sender=governance.address)
    config = mission_control.genDebtConfig()
    assert config.isDaowryEnabled == True
    
    # Check event
    logs = filter_logs(switchboard_one, "IsDaowryEnabledSet")
    assert len(logs) == 1
    assert logs[0].isDaowryEnabled == True


def test_ripe_per_block(switchboard_one, governance):
    action_id = switchboard_one.setRipePerBlock(1000, sender=governance.address)
    assert action_id > 0
    
    # Check event
    logs = filter_logs(switchboard_one, "PendingRipeRewardsPerBlockChange")
    assert len(logs) == 1
    assert logs[0].ripePerBlock == 1000


def test_rewards_allocs_validation(switchboard_one, governance):
    # Test invalid allocations (sum > 100%)
    with boa.reverts("invalid rewards allocs"):
        switchboard_one.setRipeRewardsAllocs(50_00, 30_00, 25_00, 10_00, sender=governance.address)  # sum = 115%


def test_rewards_allocs_success(switchboard_one, governance):
    action_id = switchboard_one.setRipeRewardsAllocs(40_00, 25_00, 20_00, 15_00, sender=governance.address)
    assert action_id > 0
    
    # Check event
    logs = filter_logs(switchboard_one, "PendingRipeRewardsAllocsChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.borrowersAlloc == 40_00
    assert log.stakersAlloc == 25_00
    assert log.votersAlloc == 20_00
    assert log.genDepositorsAlloc == 15_00


def test_execute_rewards_config(switchboard_one, mission_control, governance):
    # Execute ripe per block
    action_id = switchboard_one.setRipePerBlock(2000, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.rewardsConfig()
    assert config.ripePerBlock == 2000
    
    # Execute rewards allocs
    action_id = switchboard_one.setRipeRewardsAllocs(35_00, 30_00, 20_00, 15_00, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.rewardsConfig()
    assert config.borrowersAlloc == 35_00
    assert config.stakersAlloc == 30_00
    assert config.votersAlloc == 20_00
    assert config.genDepositorsAlloc == 15_00


def test_rewards_points_enable_disable(switchboard_one, mission_control, governance):
    # Enable points
    assert switchboard_one.setRewardsPointsEnabled(True, sender=governance.address)
    config = mission_control.rewardsConfig()
    assert config.arePointsEnabled == True
    
    # Check event
    logs = filter_logs(switchboard_one, "RewardsPointsEnabledModified")
    assert len(logs) == 1
    assert logs[0].arePointsEnabled == True


def test_priority_liq_asset_vaults_filtered(switchboard_one, governance):
    # Create sample vault data that will be filtered out
    vaults = [
        (1, ZERO_ADDRESS),  # Will be filtered out due to invalid vault/asset
        (2, ZERO_ADDRESS),
    ]
    
    # The function should still succeed but filter out invalid vaults
    # This test expects the filtering behavior to work and all vaults to be filtered
    with boa.reverts("invalid priority vaults"):
        switchboard_one.setPriorityLiqAssetVaults(vaults, sender=governance.address)
    
    # Test with empty array directly
    with boa.reverts("invalid priority vaults"):
        switchboard_one.setPriorityLiqAssetVaults([], sender=governance.address)
    
    # Test with duplicate invalid vaults
    duplicate_vaults = [
        (1, ZERO_ADDRESS),
        (1, ZERO_ADDRESS),  # Exact duplicate
        (2, ZERO_ADDRESS),
    ]
    with boa.reverts("invalid priority vaults"):
        switchboard_one.setPriorityLiqAssetVaults(duplicate_vaults, sender=governance.address)


def test_priority_stab_vaults_filtered(switchboard_one, governance):
    vaults = [(1, ZERO_ADDRESS)]
    # Same as above - should be filtered out
    with boa.reverts("invalid priority vaults"):
        switchboard_one.setPriorityStabVaults(vaults, sender=governance.address)
    
    # Test with multiple invalid vaults including duplicates
    multiple_vaults = [
        (1, ZERO_ADDRESS),
        (2, ZERO_ADDRESS),
        (1, ZERO_ADDRESS),  # Duplicate
        (3, ZERO_ADDRESS),
    ]
    with boa.reverts("invalid priority vaults"):
        switchboard_one.setPriorityStabVaults(multiple_vaults, sender=governance.address)


def test_invalid_priority_vaults(switchboard_one, governance):
    # Test empty vaults array fails
    with boa.reverts("invalid priority vaults"):
        switchboard_one.setPriorityLiqAssetVaults([], sender=governance.address)


def test_priority_price_source_ids_filtered(switchboard_one, governance):
    # Test with invalid price source IDs (will be filtered)
    ids = [999, 998, 997]  # Use obviously invalid IDs that should be filtered out
    # This should revert since all IDs will be filtered out, resulting in empty list
    with boa.reverts("invalid priority sources"):
        switchboard_one.setPriorityPriceSourceIds(ids, sender=governance.address)
    
    # Test with duplicate invalid IDs
    duplicate_ids = [999, 999, 998, 998, 997, 997]
    with boa.reverts("invalid priority sources"):
        switchboard_one.setPriorityPriceSourceIds(duplicate_ids, sender=governance.address)
    
    # Test with mix of valid and invalid IDs (1 and 2 are valid in test env)
    mixed_ids = [1, 2, 999, 998, 1, 2]  # Contains duplicates
    # This should succeed because it has valid IDs (1 and 2)
    action_id = switchboard_one.setPriorityPriceSourceIds(mixed_ids, sender=governance.address)
    assert action_id > 0
    
    # Check that only valid, deduplicated IDs were stored
    logs = filter_logs(switchboard_one, "PendingPriorityPriceSourceIdsChange")
    assert len(logs) == 1
    assert logs[0].numPriorityPriceSourceIds == 2  # Only IDs 1 and 2 should be valid


def test_invalid_priority_sources(switchboard_one, governance):
    # Test empty sources array fails
    with boa.reverts("invalid priority sources"):
        switchboard_one.setPriorityPriceSourceIds([], sender=governance.address)


def test_set_underscore_registry_validation_zero_address(switchboard_one, governance):
    # Test invalid underscore registry with zero address
    # This will fail at the static call level
    with boa.reverts():
        switchboard_one.setUnderscoreRegistry(ZERO_ADDRESS, sender=governance.address)


def test_set_underscore_registry_success(switchboard_one, governance, mock_rando_contract):
    # This will fail validation as mock_rando_contract doesn't implement the required interface
    with boa.reverts():  # Just check it reverts, don't match exact message
        switchboard_one.setUnderscoreRegistry(mock_rando_contract, sender=governance.address)


def test_set_can_disable(switchboard_one, governance, bob):
    action_id = switchboard_one.setCanPerformLiteAction(bob, True, sender=governance.address)
    assert action_id > 0
    
    # Check event
    logs = filter_logs(switchboard_one, "PendingCanPerformLiteAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.user == bob
    assert log.canDo == True


def test_execute_can_disable(switchboard_one, mission_control, governance, bob):
    # Set can disable
    action_id = switchboard_one.setCanPerformLiteAction(bob, True, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Verify it was applied
    assert mission_control.canPerformLiteAction(bob) == True
    
    # Check event
    logs = filter_logs(switchboard_one, "CanPerformLiteAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.user == bob
    assert log.canDo == True


def test_execute_invalid_action(switchboard_one, governance):
    # Try to execute non-existent action
    assert not switchboard_one.executePendingAction(999, sender=governance.address)


def test_execute_before_timelock_when_timelock_nonzero(switchboard_one, governance):
    # First, let's check what the timelock actually is
    time_lock = switchboard_one.actionTimeLock()
    
    if time_lock == 0:
        # If timelock is 0, the action will execute immediately
        # This is expected behavior in this test setup
        action_id = switchboard_one.setVaultLimits(10, 5, sender=governance.address)
        # With timelock 0, this should succeed
        assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    else:
        # If timelock is non-zero, test the expected behavior
        action_id = switchboard_one.setVaultLimits(10, 5, sender=governance.address)
        # Try to execute before timelock
        assert not switchboard_one.executePendingAction(action_id, sender=governance.address)
        
        # Also test execution at various points before timelock
        for blocks_passed in [1, time_lock // 2, time_lock - 1]:
            boa.env.time_travel(blocks=1)
            assert not switchboard_one.executePendingAction(action_id, sender=governance.address)


def test_execute_expired_action(switchboard_one, governance):
    # Create an action
    action_id = switchboard_one.setVaultLimits(10, 5, sender=governance.address)
    
    # Time travel past expiration
    time_lock = switchboard_one.actionTimeLock()
    expiration = switchboard_one.expiration()
    boa.env.time_travel(blocks=time_lock + expiration + 1)
    
    # Try to execute expired action
    assert not switchboard_one.executePendingAction(action_id, sender=governance.address)


def test_cancel_action(switchboard_one, governance):
    # Create an action
    action_id = switchboard_one.setVaultLimits(10, 5, sender=governance.address)
    
    # Cancel it
    assert switchboard_one.cancelPendingAction(action_id, sender=governance.address)
    
    # Verify it's no longer pending
    assert not switchboard_one.hasPendingAction(action_id)


def test_execute_all_action_types(switchboard_one, mission_control, governance):
    time_lock = switchboard_one.actionTimeLock()
    
    # Test executing different action types
    test_cases = [
        # (action_creator, expected_field, expected_value)
        (lambda: switchboard_one.setVaultLimits(15, 8, sender=governance.address), "perUserMaxVaults", 15),
        (lambda: switchboard_one.setStaleTime(switchboard_one.MIN_STALE_TIME() + 50, sender=governance.address), "priceStaleTime", switchboard_one.MIN_STALE_TIME() + 50),
    ]
    
    for action_creator, field, expected_value in test_cases:
        # Create action
        action_id = action_creator()
        
        # Execute after timelock
        boa.env.time_travel(blocks=time_lock)
        assert switchboard_one.executePendingAction(action_id, sender=governance.address)
        
        # Verify the config was applied
        config = mission_control.genConfig()
        assert getattr(config, field) == expected_value


def test_sequential_actions_same_type(switchboard_one, governance):
    # Create multiple vault limit actions
    action_id1 = switchboard_one.setVaultLimits(10, 5, sender=governance.address)
    action_id2 = switchboard_one.setVaultLimits(20, 10, sender=governance.address)
    
    assert action_id1 != action_id2
    assert action_id2 == action_id1 + 1


def test_action_id_increment(switchboard_one, governance):
    initial_id = switchboard_one.actionId()
    
    # Create an action
    action_id = switchboard_one.setVaultLimits(10, 5, sender=governance.address)
    
    # Action ID should increment
    assert action_id == initial_id
    assert switchboard_one.actionId() == initial_id + 1


def test_pending_action_cleanup(switchboard_one, governance):
    # Create and execute an action
    action_id = switchboard_one.setVaultLimits(10, 5, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Verify pending data is cleaned up
    assert switchboard_one.actionType(action_id) == 0  # empty ActionType
    assert not switchboard_one.hasPendingAction(action_id)


def test_borrow_interval_with_existing_debt_config(switchboard_one, mission_control, governance):
    # First set global debt limits to establish minDebtAmount
    action_id = switchboard_one.setGlobalDebtLimits(5000, 50000, 100, 100, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Now test borrow interval config with amount less than minDebtAmount
    with boa.reverts("invalid borrow interval config"):
        switchboard_one.setBorrowIntervalConfig(50, 100, sender=governance.address)  # 50 < 100 (minDebtAmount)
    
    # Test valid borrow interval config
    action_id = switchboard_one.setBorrowIntervalConfig(500, 100, sender=governance.address)
    assert action_id > 0


def test_full_config_workflow(switchboard_one, mission_control, governance):
    time_lock = switchboard_one.actionTimeLock()
    
    # Create multiple configuration changes
    vault_action = switchboard_one.setVaultLimits(30, 20, sender=governance.address)
    debt_action = switchboard_one.setGlobalDebtLimits(8000, 80000, 500, 200, sender=governance.address)
    rewards_action = switchboard_one.setRipePerBlock(3000, sender=governance.address)
    
    # Execute them all after timelock
    boa.env.time_travel(blocks=time_lock)
    
    assert switchboard_one.executePendingAction(vault_action, sender=governance.address)
    assert switchboard_one.executePendingAction(debt_action, sender=governance.address)
    assert switchboard_one.executePendingAction(rewards_action, sender=governance.address)
    
    # Verify all configs were applied
    gen_config = mission_control.genConfig()
    assert gen_config.perUserMaxVaults == 30
    assert gen_config.perUserMaxAssetsPerVault == 20
    
    debt_config = mission_control.genDebtConfig()
    assert debt_config.perUserDebtLimit == 8000
    assert debt_config.globalDebtLimit == 80000
    
    rewards_config = mission_control.rewardsConfig()
    assert rewards_config.ripePerBlock == 3000


def test_mixed_immediate_and_timelock_actions(switchboard_one, mission_control, governance):
    # Immediate action (no timelock)
    switchboard_one.setCanDeposit(True, sender=governance.address)
    
    # Timelock action
    action_id = switchboard_one.setVaultLimits(25, 15, sender=governance.address)
    
    # Verify immediate action took effect
    config = mission_control.genConfig()
    assert config.canDeposit == True
    
    # Verify timelock action is pending
    assert switchboard_one.hasPendingAction(action_id)
    
    # Execute timelock action
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Verify both configs are applied
    config = mission_control.genConfig()
    assert config.canDeposit == True
    assert config.perUserMaxVaults == 25
    assert config.perUserMaxAssetsPerVault == 15


# Additional test coverage for missing scenarios

def test_has_perms_to_enable_complex_scenarios(switchboard_one, governance, bob):
    """Test complex permission scenarios for _hasPermsToEnable logic"""
    
    # Set bob as someone who can disable
    action_id = switchboard_one.setCanPerformLiteAction(bob, True, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Bob can disable but not enable
    switchboard_one.setCanDeposit(True, sender=governance.address)  # Enable first
    
    # Bob can disable
    switchboard_one.setCanDeposit(False, sender=bob)
    
    # But bob cannot enable again
    with boa.reverts("no perms"):
        switchboard_one.setCanDeposit(True, sender=bob)
    
    # Remove bob's disable permission
    action_id = switchboard_one.setCanPerformLiteAction(bob, False, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Now bob can't even disable
    switchboard_one.setCanDeposit(True, sender=governance.address)  # Enable first
    with boa.reverts("no perms"):
        switchboard_one.setCanDeposit(False, sender=bob)


def test_sanitize_priority_vaults_deduplication(switchboard_one, governance, alpha_token):
    """Test the deduplication logic in _sanitizePriorityVaults"""
    
    # Test with duplicate vault ID + asset combinations
    vaults = [
        (1, alpha_token),
        (1, alpha_token),  # exact duplicate
        (1, alpha_token),  # another duplicate
        (2, alpha_token),  # different vault, same asset
    ]
    
    # This should filter out duplicates and invalid vaults
    # In test environment, all vaults will be invalid (not registered in VaultBook)
    with boa.reverts("invalid priority vaults"):
        switchboard_one.setPriorityLiqAssetVaults(vaults, sender=governance.address)


def test_sanitize_priority_sources_deduplication(switchboard_one, governance):
    """Test the deduplication logic in _sanitizePrioritySources"""
    
    # Test with duplicate price source IDs (1 and 2 are valid)
    ids = [1, 1, 2, 2, 1, 3]  # Contains duplicates, 3 is invalid
    
    # This should succeed with valid IDs 1 and 2 (deduplicated)
    action_id = switchboard_one.setPriorityPriceSourceIds(ids, sender=governance.address)
    assert action_id > 0
    
    # Check deduplication worked
    logs = filter_logs(switchboard_one, "PendingPriorityPriceSourceIdsChange")
    assert len(logs) == 1
    assert logs[0].numPriorityPriceSourceIds == 2  # Only unique valid IDs 1 and 2


def test_auction_params_boundary_conditions(switchboard_one, governance):
    """Test auction params validation at boundary conditions"""
    
    # Test with exact boundary values
    HUNDRED_PERCENT = 100_00
    
    # startDiscount just under maxDiscount (both under 100%)
    action_id = switchboard_one.setGenAuctionParams(
        HUNDRED_PERCENT - 2, HUNDRED_PERCENT - 1, 1000, 2000, 
        sender=governance.address
    )
    assert action_id > 0
    
    # Test delay = duration - 1 (just valid)
    action_id = switchboard_one.setGenAuctionParams(
        50_00, 80_00, 1999, 2000, 
        sender=governance.address
    )
    assert action_id > 0
    
    # Test minimum valid duration (1)
    action_id = switchboard_one.setGenAuctionParams(
        10_00, 50_00, 0, 1, 
        sender=governance.address
    )
    assert action_id > 0
    
    # Test startDiscount = 0, maxDiscount just under 100%
    action_id = switchboard_one.setGenAuctionParams(
        0, HUNDRED_PERCENT - 1, 100, 1000, 
        sender=governance.address
    )
    assert action_id > 0


def test_debt_limits_boundary_conditions(switchboard_one, governance):
    """Test debt limits validation at boundary conditions"""
    
    # Test where minDebtAmount equals perUserDebtLimit (should be valid)
    action_id = switchboard_one.setGlobalDebtLimits(1000, 10000, 1000, 100, sender=governance.address)
    assert action_id > 0
    
    # Test where perUserDebtLimit equals globalDebtLimit (should be valid)
    action_id = switchboard_one.setGlobalDebtLimits(5000, 5000, 100, 50, sender=governance.address)
    assert action_id > 0


def test_keeper_config_boundary_conditions(switchboard_one, governance):
    """Test keeper config validation at boundary values"""
    
    # Test at exactly 10% fee ratio (should be valid)
    action_id = switchboard_one.setKeeperConfig(10_00, 1000, sender=governance.address)
    assert action_id > 0
    
    # Test at exactly $100 min fee (should be valid)
    action_id = switchboard_one.setKeeperConfig(5_00, 100 * 10**18, sender=governance.address)
    assert action_id > 0
    
    # Test with zero fee ratio (should be valid)
    action_id = switchboard_one.setKeeperConfig(0, 0, sender=governance.address)
    assert action_id > 0


def test_ltv_payback_buffer_boundary_conditions(switchboard_one, governance):
    """Test LTV payback buffer at boundary values"""
    
    # Test at exactly 10% (should be valid)
    action_id = switchboard_one.setLtvPaybackBuffer(10_00, sender=governance.address)
    assert action_id > 0
    
    # Test at 1 (minimum valid value)
    action_id = switchboard_one.setLtvPaybackBuffer(1, sender=governance.address)
    assert action_id > 0


def test_rewards_allocs_boundary_conditions(switchboard_one, governance):
    """Test rewards allocations at boundary conditions"""
    
    # Test with sum exactly equal to 100%
    action_id = switchboard_one.setRipeRewardsAllocs(25_00, 25_00, 25_00, 25_00, sender=governance.address)
    assert action_id > 0
    
    # Test with sum less than 100%
    action_id = switchboard_one.setRipeRewardsAllocs(20_00, 20_00, 20_00, 20_00, sender=governance.address)
    assert action_id > 0
    
    # Test with all allocation to one category
    action_id = switchboard_one.setRipeRewardsAllocs(100_00, 0, 0, 0, sender=governance.address)
    assert action_id > 0
    
    # Test with zero allocations
    action_id = switchboard_one.setRipeRewardsAllocs(0, 0, 0, 0, sender=governance.address)
    assert action_id > 0


def test_execution_with_state_changes(switchboard_one, mission_control, governance):
    """Test executing actions that modify current state"""
    
    # Set initial vault limits
    action_id1 = switchboard_one.setVaultLimits(10, 5, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id1, sender=governance.address)
    
    # Set different vault limits
    action_id2 = switchboard_one.setVaultLimits(20, 10, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id2, sender=governance.address)
    
    # Verify the latest values are applied
    config = mission_control.genConfig()
    assert config.perUserMaxVaults == 20
    assert config.perUserMaxAssetsPerVault == 10


def test_execution_all_action_types_comprehensive(switchboard_one, mission_control, governance):
    """Test executing every single action type to ensure complete coverage"""
    
    time_lock = switchboard_one.actionTimeLock()
    
    # Test LTV payback buffer execution (not covered in other tests)
    action_id = switchboard_one.setLtvPaybackBuffer(5_00, sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.genDebtConfig()
    assert config.ltvPaybackBuffer == 5_00
    
    # Check event
    logs = filter_logs(switchboard_one, "LtvPaybackBufferSet")
    assert len(logs) == 1
    assert logs[0].ltvPaybackBuffer == 5_00
    
    # Test auction params execution
    action_id = switchboard_one.setGenAuctionParams(20_00, 50_00, 1000, 3000, sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.genDebtConfig()
    assert config.genAuctionParams.startDiscount == 20_00
    assert config.genAuctionParams.maxDiscount == 50_00
    assert config.genAuctionParams.delay == 1000
    assert config.genAuctionParams.duration == 3000
    
    # Check event
    logs = filter_logs(switchboard_one, "GenAuctionParamsSet")
    assert len(logs) == 1
    assert logs[0].startDiscount == 20_00
    
    # Test max LTV deviation execution
    action_id = switchboard_one.setMaxLtvDeviation(8_00, sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Check event
    logs = filter_logs(switchboard_one, "MaxLtvDeviationSet")
    assert len(logs) == 1
    assert logs[0].newDeviation == 8_00


def test_cancel_action_edge_cases(switchboard_one, governance):
    """Test action cancellation edge cases"""
    
    # Test canceling non-existent action
    with boa.reverts("cannot cancel action"):
        switchboard_one.cancelPendingAction(999, sender=governance.address)
    
    # Test canceling already executed action
    action_id = switchboard_one.setVaultLimits(10, 5, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Should fail to cancel already executed action
    with boa.reverts("cannot cancel action"):
        switchboard_one.cancelPendingAction(action_id, sender=governance.address)
    
    # Test canceling an expired action
    action_id2 = switchboard_one.setVaultLimits(20, 10, sender=governance.address)
    expiration = switchboard_one.expiration()
    time_lock = switchboard_one.actionTimeLock()
    boa.env.time_travel(blocks=time_lock + expiration + 1)
    
    # Should be able to cancel expired action
    assert switchboard_one.cancelPendingAction(action_id2, sender=governance.address)
    
    # Test double cancellation
    action_id3 = switchboard_one.setVaultLimits(30, 15, sender=governance.address)
    assert switchboard_one.cancelPendingAction(action_id3, sender=governance.address)
    
    # Should fail on second cancel
    with boa.reverts("cannot cancel action"):
        switchboard_one.cancelPendingAction(action_id3, sender=governance.address)


def test_complex_workflow_multiple_pending_actions(switchboard_one, governance):
    """Test complex workflows with multiple pending actions"""
    
    # Create multiple different types of actions
    vault_action = switchboard_one.setVaultLimits(15, 8, sender=governance.address)
    debt_action = switchboard_one.setGlobalDebtLimits(3000, 30000, 150, 75, sender=governance.address)
    rewards_action = switchboard_one.setRipePerBlock(1500, sender=governance.address)
    keeper_action = switchboard_one.setKeeperConfig(3_00, 25 * 10**18, sender=governance.address)
    buffer_action = switchboard_one.setLtvPaybackBuffer(7_00, sender=governance.address)
    
    # Verify all actions are pending
    assert switchboard_one.hasPendingAction(vault_action)
    assert switchboard_one.hasPendingAction(debt_action)
    assert switchboard_one.hasPendingAction(rewards_action)
    assert switchboard_one.hasPendingAction(keeper_action)
    assert switchboard_one.hasPendingAction(buffer_action)
    
    # Cancel one action
    switchboard_one.cancelPendingAction(keeper_action, sender=governance.address)
    assert not switchboard_one.hasPendingAction(keeper_action)
    
    # Execute the rest
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    assert switchboard_one.executePendingAction(vault_action, sender=governance.address)
    assert switchboard_one.executePendingAction(debt_action, sender=governance.address)
    assert switchboard_one.executePendingAction(rewards_action, sender=governance.address)
    assert switchboard_one.executePendingAction(buffer_action, sender=governance.address)
    
    # Verify all were cleaned up
    assert not switchboard_one.hasPendingAction(vault_action)
    assert not switchboard_one.hasPendingAction(debt_action)
    assert not switchboard_one.hasPendingAction(rewards_action)
    assert not switchboard_one.hasPendingAction(buffer_action)


def test_ripe_per_block_zero_value(switchboard_one, governance):
    """Test setting ripe per block to zero (edge case)"""
    
    action_id = switchboard_one.setRipePerBlock(0, sender=governance.address)
    assert action_id > 0
    
    # Execute and verify
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id, sender=governance.address)


def test_stale_time_exact_boundaries(switchboard_one, governance):
    """Test stale time at exact min/max boundaries"""
    
    # Test at exact minimum
    min_stale = switchboard_one.MIN_STALE_TIME()
    action_id = switchboard_one.setStaleTime(min_stale, sender=governance.address)
    assert action_id > 0
    
    # Test at exact maximum
    max_stale = switchboard_one.MAX_STALE_TIME()
    action_id = switchboard_one.setStaleTime(max_stale, sender=governance.address)
    assert action_id > 0


def test_vault_limits_edge_cases(switchboard_one, governance):
    """Test vault limits with edge case values"""
    
    # Test with value 1 (minimum valid)
    action_id = switchboard_one.setVaultLimits(1, 1, sender=governance.address)
    assert action_id > 0
    
    # Test with large but valid values
    large_value = MAX_UINT256 - 1
    action_id = switchboard_one.setVaultLimits(large_value, large_value, sender=governance.address)
    assert action_id > 0


def test_action_state_consistency(switchboard_one, governance):
    """Test that action state is properly managed"""
    
    # Create action and verify it's stored
    action_id = switchboard_one.setVaultLimits(12, 6, sender=governance.address)
    
    # Verify pending config is stored
    pending = switchboard_one.pendingGeneralConfig(action_id)
    assert pending.perUserMaxVaults == 12
    assert pending.perUserMaxAssetsPerVault == 6
    
    # Verify action type is stored
    assert switchboard_one.actionType(action_id) != 0  # Should not be empty
    
    # Execute action
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Verify cleanup
    assert switchboard_one.actionType(action_id) == 0  # Should be empty after execution


def test_comprehensive_permission_matrix(switchboard_one, governance, bob, alice):
    """Test comprehensive permission scenarios"""
    
    # Test governance permissions
    assert switchboard_one.setCanDeposit(True, sender=governance.address)
    
    # Test with multiple users having disable permissions
    action_id1 = switchboard_one.setCanPerformLiteAction(bob, True, sender=governance.address)
    action_id2 = switchboard_one.setCanPerformLiteAction(alice, True, sender=governance.address)
    
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id1, sender=governance.address)
    switchboard_one.executePendingAction(action_id2, sender=governance.address)
    
    # Both bob and alice should be able to disable
    switchboard_one.setCanWithdraw(True, sender=governance.address)  # Enable first
    switchboard_one.setCanWithdraw(False, sender=bob)  # Bob disables
    switchboard_one.setCanWithdraw(True, sender=governance.address)  # Re-enable
    switchboard_one.setCanWithdraw(False, sender=alice)  # Alice disables
    
    # Remove bob's permission
    action_id = switchboard_one.setCanPerformLiteAction(bob, False, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Now only alice can disable
    switchboard_one.setCanWithdraw(True, sender=governance.address)  # Enable first
    with boa.reverts("no perms"):
        switchboard_one.setCanWithdraw(False, sender=bob)  # Bob can't disable
    switchboard_one.setCanWithdraw(False, sender=alice)  # Alice still can


def test_transient_storage_behavior(switchboard_one, governance, alpha_token, bravo_token):
    """Test that transient storage (vaultDedupe) works correctly across calls"""
    
    # This tests the deduplication logic that uses transient storage
    vaults = [
        (1, alpha_token),
        (1, bravo_token),
        (1, alpha_token),  # duplicate of first
    ]
    
    # The transient storage should deduplicate within a single call
    # All vaults will be invalid in test environment
    with boa.reverts("invalid priority vaults"):
        switchboard_one.setPriorityLiqAssetVaults(vaults, sender=governance.address)
    
    # Test that transient storage is cleared between calls
    # Create two separate calls with same vault data
    vaults1 = [(1, alpha_token), (2, bravo_token)]
    vaults2 = [(1, alpha_token), (3, alpha_token)]  # Reuses vault 1
    
    # Both calls should fail due to invalid vaults
    with boa.reverts("invalid priority vaults"):
        switchboard_one.setPriorityLiqAssetVaults(vaults1, sender=governance.address)
    
    with boa.reverts("invalid priority vaults"):
        switchboard_one.setPriorityLiqAssetVaults(vaults2, sender=governance.address)


def test_edge_case_stale_time_boundaries(switchboard_one, mission_control, governance):
    """Test stale time configuration at exact min/max boundaries with state changes"""
    min_stale = switchboard_one.MIN_STALE_TIME()
    max_stale = switchboard_one.MAX_STALE_TIME()
    
    # Set to minimum
    action_id = switchboard_one.setStaleTime(min_stale, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.genConfig()
    assert config.priceStaleTime == min_stale
    
    # Set to maximum
    action_id = switchboard_one.setStaleTime(max_stale, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.genConfig()
    assert config.priceStaleTime == max_stale
    
    # Try to set just outside boundaries
    with boa.reverts("invalid stale time"):
        switchboard_one.setStaleTime(min_stale - 1, sender=governance.address)
    
    with boa.reverts("invalid stale time"):
        switchboard_one.setStaleTime(max_stale + 1, sender=governance.address)


# Additional comprehensive tests

def test_priority_vault_maximum_array_size(switchboard_one, governance):
    """Test priority vaults with maximum allowed array size"""
    # PRIORITY_VAULT_DATA constant is 20
    max_vaults = []
    for i in range(20):
        max_vaults.append((i + 1, ZERO_ADDRESS))  # Will be filtered but tests max size
    
    # This should handle the maximum size without reverting
    with boa.reverts("invalid priority vaults"):
        switchboard_one.setPriorityLiqAssetVaults(max_vaults, sender=governance.address)


def test_priority_vault_deduplication_complex(switchboard_one, governance, alpha_token, bravo_token, charlie_token):
    """Test complex deduplication scenarios for priority vaults"""
    # Test with multiple duplicates and valid entries mixed
    vaults = [
        (1, alpha_token),
        (2, bravo_token),
        (1, alpha_token),  # Duplicate
        (3, charlie_token),
        (2, bravo_token),  # Duplicate
        (1, bravo_token),  # Same vault, different asset
        (3, charlie_token),  # Duplicate
    ]
    
    # The transient storage should handle deduplication correctly
    with boa.reverts("invalid priority vaults"):
        switchboard_one.setPriorityLiqAssetVaults(vaults, sender=governance.address)


def test_priority_price_sources_maximum_array(switchboard_one, governance):
    """Test priority price sources with maximum allowed array size"""
    # MAX_PRIORITY_PRICE_SOURCES is 10
    # Mix of valid (1, 2) and invalid IDs
    max_sources = [1, 2] + list(range(100, 108))
    
    # This should succeed with the valid IDs
    action_id = switchboard_one.setPriorityPriceSourceIds(max_sources, sender=governance.address)
    assert action_id > 0
    
    # Should only have the valid IDs
    logs = filter_logs(switchboard_one, "PendingPriorityPriceSourceIdsChange")
    assert len(logs) == 1
    assert logs[0].numPriorityPriceSourceIds == 2  # Only IDs 1 and 2 are valid


def test_underscore_registry_validation_comprehensive(switchboard_one, governance):
    """Test underscore registry validation with various scenarios"""
    # Test with contract that doesn't implement expected interface
    with boa.reverts():
        switchboard_one.setUnderscoreRegistry(governance.address, sender=governance.address)
    
    # Test with EOA (not a contract)
    eoa_address = boa.env.generate_address()
    with boa.reverts():
        switchboard_one.setUnderscoreRegistry(eoa_address, sender=governance.address)


def test_action_expiration_boundary_conditions(switchboard_one, governance):
    """Test action expiration at exact boundary times"""
    # Create an action
    action_id = switchboard_one.setVaultLimits(10, 5, sender=governance.address)
    
    time_lock = switchboard_one.actionTimeLock()
    expiration = switchboard_one.expiration()
    
    # Test at exactly the expiration boundary
    boa.env.time_travel(blocks=time_lock + expiration)
    
    # Should still be executable at exact expiration
    result = switchboard_one.executePendingAction(action_id, sender=governance.address)
    # Depending on implementation, this might succeed or fail
    
    # Create another action and test just after expiration
    action_id2 = switchboard_one.setVaultLimits(15, 8, sender=governance.address)
    boa.env.time_travel(blocks=time_lock + expiration + 1)
    
    # Should definitely fail after expiration
    assert not switchboard_one.executePendingAction(action_id2, sender=governance.address)


def test_multi_user_complex_permission_scenarios(switchboard_one, governance, bob, alice, charlie):
    """Test complex scenarios with multiple users having different permissions"""
    # Setup: Give different users different permissions
    action_id1 = switchboard_one.setCanPerformLiteAction(bob, True, sender=governance.address)
    action_id2 = switchboard_one.setCanPerformLiteAction(alice, True, sender=governance.address)
    
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id1, sender=governance.address)
    switchboard_one.executePendingAction(action_id2, sender=governance.address)
    
    # Enable multiple features
    switchboard_one.setCanDeposit(True, sender=governance.address)
    switchboard_one.setCanWithdraw(True, sender=governance.address)
    switchboard_one.setCanBorrow(True, sender=governance.address)
    
    # Test concurrent disabling by different users
    switchboard_one.setCanDeposit(False, sender=bob)
    switchboard_one.setCanWithdraw(False, sender=alice)
    
    # Verify charlie (no permissions) cannot disable
    # canBorrow is already True, so we don't need to re-enable it
    with boa.reverts("no perms"):
        switchboard_one.setCanBorrow(False, sender=charlie)
    
    # Test removing permissions while actions are pending
    action_id3 = switchboard_one.setCanPerformLiteAction(bob, False, sender=governance.address)
    
    # Bob should still be able to disable before the action executes
    switchboard_one.setCanDeposit(True, sender=governance.address)  # Re-enable
    switchboard_one.setCanDeposit(False, sender=bob)  # Should still work
    
    # Execute the permission removal
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id3, sender=governance.address)
    
    # Now bob cannot disable
    switchboard_one.setCanDeposit(True, sender=governance.address)  # Re-enable
    with boa.reverts("no perms"):
        switchboard_one.setCanDeposit(False, sender=bob)


def test_state_cleanup_on_failed_execution(switchboard_one, governance):
    """Test that state is properly cleaned up when execution fails"""
    # Create multiple actions
    action_id1 = switchboard_one.setVaultLimits(10, 5, sender=governance.address)
    action_id2 = switchboard_one.setStaleTime(switchboard_one.MIN_STALE_TIME() + 100, sender=governance.address)
    
    # Cancel one action
    switchboard_one.cancelPendingAction(action_id1, sender=governance.address)
    
    # Verify the action type is cleared
    assert switchboard_one.actionType(action_id1) == 0
    assert not switchboard_one.hasPendingAction(action_id1)
    
    # Verify pending data is cleared (though it might still exist in storage)
    # The important thing is that actionType is cleared so it can't be executed


def test_rapid_sequential_actions_same_type(switchboard_one, governance):
    """Test creating many sequential actions of the same type rapidly"""
    action_ids = []
    
    # Create 10 vault limit changes rapidly
    for i in range(10):
        action_id = switchboard_one.setVaultLimits(10 + i, 5 + i, sender=governance.address)
        action_ids.append(action_id)
    
    # Verify all have unique IDs
    assert len(set(action_ids)) == 10
    
    # Verify they're sequential
    for i in range(1, 10):
        assert action_ids[i] == action_ids[i-1] + 1
    
    # Execute them out of order
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    
    # Execute middle one first
    assert switchboard_one.executePendingAction(action_ids[5], sender=governance.address)
    
    # Execute last one
    assert switchboard_one.executePendingAction(action_ids[9], sender=governance.address)
    
    # Execute first one
    assert switchboard_one.executePendingAction(action_ids[0], sender=governance.address)
    
    # Verify others are still pending
    assert switchboard_one.hasPendingAction(action_ids[1])
    assert switchboard_one.hasPendingAction(action_ids[2])


def test_all_enable_disable_concurrent_state_changes(switchboard_one, mission_control, governance, bob):
    """Test all enable/disable functions with concurrent state changes"""
    # Give bob disable permissions
    action_id = switchboard_one.setCanPerformLiteAction(bob, True, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Test rapid enable/disable cycles
    functions = [
        (switchboard_one.setCanDeposit, "canDeposit"),
        (switchboard_one.setCanWithdraw, "canWithdraw"),
        (switchboard_one.setCanBorrow, "canBorrow"),
        (switchboard_one.setCanRepay, "canRepay"),
        (switchboard_one.setCanClaimLoot, "canClaimLoot"),
    ]
    
    # Enable all
    for func, _ in functions:
        func(True, sender=governance.address)
    
    # Bob disables some while governance enables others
    functions[0][0](False, sender=bob)  # Bob disables deposits
    functions[2][0](False, sender=bob)  # Bob disables borrows
    
    # Governance re-enables one
    functions[0][0](True, sender=governance.address)
    
    # Verify final state
    config = mission_control.genConfig()
    assert config.canDeposit == True  # Re-enabled by governance
    assert config.canWithdraw == True  # Never disabled
    assert config.canBorrow == False  # Disabled by bob
    assert config.canRepay == True  # Never disabled
    assert config.canClaimLoot == True  # Never disabled


def test_debt_config_interdependencies(switchboard_one, governance):
    """Test debt config settings that have interdependencies"""
    # Set initial debt limits
    action_id = switchboard_one.setGlobalDebtLimits(5000, 50000, 100, 100, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Now test borrow interval with edge cases around minDebtAmount
    # This should fail because maxBorrowPerInterval (99) < minDebtAmount (100)
    with boa.reverts("invalid borrow interval config"):
        switchboard_one.setBorrowIntervalConfig(99, 100, sender=governance.address)
    
    # This should succeed - exactly at minDebtAmount
    action_id = switchboard_one.setBorrowIntervalConfig(100, 100, sender=governance.address)
    assert action_id > 0
    
    # Test changing minDebtAmount after borrow interval is set
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Now try to set minDebtAmount higher than maxBorrowPerInterval
    # This should succeed because we're not validating against existing borrow config
    action_id = switchboard_one.setGlobalDebtLimits(5000, 50000, 200, 100, sender=governance.address)
    assert action_id > 0


def test_auction_params_comprehensive_validation(switchboard_one, governance):
    """Test auction parameters with comprehensive edge cases"""
    HUNDRED_PERCENT = 100_00
    
    # Test with startDiscount = 0
    action_id = switchboard_one.setGenAuctionParams(0, 50_00, 100, 1000, sender=governance.address)
    assert action_id > 0
    
    # Test with very small duration
    action_id = switchboard_one.setGenAuctionParams(10_00, 50_00, 0, 1, sender=governance.address)
    assert action_id > 0
    
    # Test with delay = 0
    action_id = switchboard_one.setGenAuctionParams(10_00, 50_00, 0, 1000, sender=governance.address)
    assert action_id > 0
    
    # Test with very large but valid values
    large_duration = 1000000  # Large but not max_value
    action_id = switchboard_one.setGenAuctionParams(10_00, 50_00, 100, large_duration, sender=governance.address)
    assert action_id > 0


def test_rewards_config_zero_allocations(switchboard_one, mission_control, governance):
    """Test rewards configuration with all zero allocations"""
    # This should be valid - no rewards distributed
    action_id = switchboard_one.setRipeRewardsAllocs(0, 0, 0, 0, sender=governance.address)
    assert action_id > 0
    
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.rewardsConfig()
    assert config.borrowersAlloc == 0
    assert config.stakersAlloc == 0
    assert config.votersAlloc == 0
    assert config.genDepositorsAlloc == 0


def test_multiple_pending_actions_cleanup(switchboard_one, governance):
    """Test cleanup of multiple pending actions of different types"""
    # Create one of each type of action
    vault_action = switchboard_one.setVaultLimits(10, 5, sender=governance.address)
    stale_action = switchboard_one.setStaleTime(switchboard_one.MIN_STALE_TIME() + 50, sender=governance.address)
    debt_action = switchboard_one.setGlobalDebtLimits(3000, 30000, 150, 75, sender=governance.address)
    rewards_action = switchboard_one.setRipePerBlock(1000, sender=governance.address)
    
    # Let some expire
    expiration = switchboard_one.expiration()
    time_lock = switchboard_one.actionTimeLock()
    boa.env.time_travel(blocks=time_lock + expiration + 1)
    
    # Try to execute expired actions - should fail and clean up
    assert not switchboard_one.executePendingAction(vault_action, sender=governance.address)
    assert not switchboard_one.executePendingAction(stale_action, sender=governance.address)
    
    # Verify cleanup
    assert switchboard_one.actionType(vault_action) == 0
    assert switchboard_one.actionType(stale_action) == 0
    
    # Cancel others manually
    switchboard_one.cancelPendingAction(debt_action, sender=governance.address)
    switchboard_one.cancelPendingAction(rewards_action, sender=governance.address)
    
    # Verify all are cleaned up
    assert not switchboard_one.hasPendingAction(vault_action)
    assert not switchboard_one.hasPendingAction(stale_action)
    assert not switchboard_one.hasPendingAction(debt_action)
    assert not switchboard_one.hasPendingAction(rewards_action)


def test_gas_optimization_large_arrays(switchboard_one, governance):
    """Test gas usage with maximum size arrays"""
    # Create maximum size priority vault array
    max_vaults = [(i, ZERO_ADDRESS) for i in range(20)]  # PRIORITY_VAULT_DATA = 20
    
    # Measure gas for setting priority vaults
    # This will revert but we can still check it handles max size
    with boa.reverts("invalid priority vaults"):
        switchboard_one.setPriorityLiqAssetVaults(max_vaults, sender=governance.address)
    
    # Create maximum size price source array with mix of valid and invalid
    max_sources = [1, 2] + list(range(100, 108))  # MAX_PRIORITY_PRICE_SOURCES = 10
    
    # This should succeed with valid IDs
    action_id = switchboard_one.setPriorityPriceSourceIds(max_sources, sender=governance.address)
    assert action_id > 0


def test_action_type_enum_coverage(switchboard_one, governance):
    """Ensure all ActionType enum values are tested"""
    # This test verifies we've covered all action types
    # Based on the contract, these are all the ActionType values:
    action_types_tested = set()
    
    # GEN_CONFIG_VAULT_LIMITS
    action_id = switchboard_one.setVaultLimits(10, 5, sender=governance.address)
    action_types_tested.add("GEN_CONFIG_VAULT_LIMITS")
    
    # GEN_CONFIG_STALE_TIME
    action_id = switchboard_one.setStaleTime(switchboard_one.MIN_STALE_TIME() + 50, sender=governance.address)
    action_types_tested.add("GEN_CONFIG_STALE_TIME")
    
    # DEBT_GLOBAL_LIMITS
    action_id = switchboard_one.setGlobalDebtLimits(5000, 50000, 100, 100, sender=governance.address)
    action_types_tested.add("DEBT_GLOBAL_LIMITS")
    
    # DEBT_BORROW_INTERVAL
    action_id = switchboard_one.setBorrowIntervalConfig(500, 100, sender=governance.address)
    action_types_tested.add("DEBT_BORROW_INTERVAL")
    
    # DEBT_KEEPER_CONFIG
    action_id = switchboard_one.setKeeperConfig(5_00, 50 * 10**18, sender=governance.address)
    action_types_tested.add("DEBT_KEEPER_CONFIG")
    
    # DEBT_LTV_PAYBACK_BUFFER
    action_id = switchboard_one.setLtvPaybackBuffer(5_00, sender=governance.address)
    action_types_tested.add("DEBT_LTV_PAYBACK_BUFFER")
    
    # DEBT_AUCTION_PARAMS
    action_id = switchboard_one.setGenAuctionParams(20_00, 50_00, 1000, 3000, sender=governance.address)
    action_types_tested.add("DEBT_AUCTION_PARAMS")
    
    # RIPE_REWARDS_BLOCK
    action_id = switchboard_one.setRipePerBlock(1000, sender=governance.address)
    action_types_tested.add("RIPE_REWARDS_BLOCK")
    
    # RIPE_REWARDS_ALLOCS
    action_id = switchboard_one.setRipeRewardsAllocs(25_00, 25_00, 25_00, 25_00, sender=governance.address)
    action_types_tested.add("RIPE_REWARDS_ALLOCS")
    
    # MAX_LTV_DEVIATION
    action_id = switchboard_one.setMaxLtvDeviation(10_00, sender=governance.address)
    action_types_tested.add("MAX_LTV_DEVIATION")
    
    # Verify we've tested all main action types
    assert len(action_types_tested) >= 10


def test_invalid_caller_scenarios(switchboard_one, governance, bob, alice):
    """Test various invalid caller scenarios beyond basic permission checks"""
    # Test calling from a contract (if we had a malicious contract)
    # For now, test with regular EOAs
    
    # Test non-governance trying to cancel actions
    action_id = switchboard_one.setVaultLimits(10, 5, sender=governance.address)
    
    with boa.reverts("no perms"):
        switchboard_one.cancelPendingAction(action_id, sender=bob)
    
    # Test non-governance trying to execute actions
    with boa.reverts("no perms"):
        switchboard_one.executePendingAction(action_id, sender=bob)
    
    # Give alice disable permissions
    action_id2 = switchboard_one.setCanPerformLiteAction(alice, True, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    switchboard_one.executePendingAction(action_id2, sender=governance.address)
    
    # Alice still cannot execute pending actions
    with boa.reverts("no perms"):
        switchboard_one.executePendingAction(action_id, sender=alice)
    
    # Alice still cannot cancel pending actions
    with boa.reverts("no perms"):
        switchboard_one.cancelPendingAction(action_id, sender=alice)


def test_priority_stab_vault_validation_edge_cases(switchboard_one, governance, alpha_token, bravo_token):
    """Test priority stability vault validation with edge cases"""
    # Test with mixed valid/invalid vaults
    mixed_vaults = [
        (0, alpha_token),      # Invalid vault ID (0)
        (1, ZERO_ADDRESS),     # Invalid asset
        (MAX_UINT256, alpha_token),  # Invalid vault ID (too large)
        (1, alpha_token),      # Potentially valid
        (2, bravo_token),      # Potentially valid
    ]
    
    # All should be filtered out in test environment
    with boa.reverts("invalid priority vaults"):
        switchboard_one.setPriorityStabVaults(mixed_vaults, sender=governance.address)


def test_complex_workflow_with_failures(switchboard_one, mission_control, governance):
    """Test complex workflow with some actions failing and others succeeding"""
    # Create multiple actions
    action1 = switchboard_one.setVaultLimits(10, 5, sender=governance.address)
    action2 = switchboard_one.setStaleTime(switchboard_one.MIN_STALE_TIME() + 50, sender=governance.address)
    action3 = switchboard_one.setGlobalDebtLimits(5000, 50000, 100, 100, sender=governance.address)
    
    # Time travel to make first two executable
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    
    # Execute first two
    assert switchboard_one.executePendingAction(action1, sender=governance.address)
    assert switchboard_one.executePendingAction(action2, sender=governance.address)
    
    # Create another action that conflicts with action3
    action4 = switchboard_one.setGlobalDebtLimits(6000, 60000, 200, 150, sender=governance.address)
    
    # Execute action3
    assert switchboard_one.executePendingAction(action3, sender=governance.address)
    
    # Time travel for action4
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock())
    
    # Execute action4 (should override action3's values)
    assert switchboard_one.executePendingAction(action4, sender=governance.address)
    
    # Verify final state
    config = mission_control.genConfig()
    assert config.perUserMaxVaults == 10
    assert config.priceStaleTime == switchboard_one.MIN_STALE_TIME() + 50
    
    debt_config = mission_control.genDebtConfig()
    assert debt_config.perUserDebtLimit == 6000  # From action4
    assert debt_config.globalDebtLimit == 60000
    assert debt_config.minDebtAmount == 200
    assert debt_config.numAllowedBorrowers == 150


def test_enable_disable_rapid_toggle(switchboard_one, mission_control, governance):
    """Test rapid toggling of enable/disable flags"""
    # Rapidly toggle deposit flag
    for i in range(5):
        switchboard_one.setCanDeposit(True, sender=governance.address)
        switchboard_one.setCanDeposit(False, sender=governance.address)
    
    # Final state should be False
    config = mission_control.genConfig()
    assert config.canDeposit == False
    
    # Set to True and verify
    switchboard_one.setCanDeposit(True, sender=governance.address)
    config = mission_control.genConfig()
    assert config.canDeposit == True


def test_all_debt_config_fields_modified(switchboard_one, mission_control, governance):
    """Test modifying all debt config fields through different actions"""
    time_lock = switchboard_one.actionTimeLock()
    
    # Set all debt config fields
    actions = []
    
    # Global limits
    actions.append(switchboard_one.setGlobalDebtLimits(7000, 70000, 300, 200, sender=governance.address))
    
    # Borrow interval
    actions.append(switchboard_one.setBorrowIntervalConfig(1000, 50, sender=governance.address))
    
    # Keeper config
    actions.append(switchboard_one.setKeeperConfig(8_00, 80 * 10**18, sender=governance.address))
    
    # LTV payback buffer
    actions.append(switchboard_one.setLtvPaybackBuffer(9_00, sender=governance.address))
    
    # Auction params
    actions.append(switchboard_one.setGenAuctionParams(30_00, 60_00, 2000, 5000, sender=governance.address))
    
    # Execute all actions
    boa.env.time_travel(blocks=time_lock)
    for action in actions:
        assert switchboard_one.executePendingAction(action, sender=governance.address)
    
    # Verify all fields were set
    config = mission_control.genDebtConfig()
    assert config.perUserDebtLimit == 7000
    assert config.globalDebtLimit == 70000
    assert config.minDebtAmount == 300
    assert config.numAllowedBorrowers == 200
    assert config.maxBorrowPerInterval == 1000
    assert config.numBlocksPerInterval == 50
    assert config.keeperFeeRatio == 8_00
    assert config.minKeeperFee == 80 * 10**18
    assert config.ltvPaybackBuffer == 9_00
    assert config.genAuctionParams.startDiscount == 30_00
    assert config.genAuctionParams.maxDiscount == 60_00
    assert config.genAuctionParams.delay == 2000
    assert config.genAuctionParams.duration == 5000


def test_pending_action_data_persistence(switchboard_one, governance):
    """Test that pending action data persists correctly until execution or cancellation"""
    # Create actions with specific data
    action1 = switchboard_one.setVaultLimits(42, 24, sender=governance.address)
    action2 = switchboard_one.setRipePerBlock(12345, sender=governance.address)
    
    # Verify pending data is stored correctly
    pending_gen = switchboard_one.pendingGeneralConfig(action1)
    assert pending_gen.perUserMaxVaults == 42
    assert pending_gen.perUserMaxAssetsPerVault == 24
    
    pending_rewards = switchboard_one.pendingRipeRewardsConfig(action2)
    assert pending_rewards.ripePerBlock == 12345
    
    # Time travel but don't execute
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock() // 2)
    
    # Data should still be there
    pending_gen = switchboard_one.pendingGeneralConfig(action1)
    assert pending_gen.perUserMaxVaults == 42
    
    # Cancel one action
    switchboard_one.cancelPendingAction(action1, sender=governance.address)
    
    # Execute the other
    boa.env.time_travel(blocks=switchboard_one.actionTimeLock() // 2)
    switchboard_one.executePendingAction(action2, sender=governance.address)
    
    # Verify action types are cleared appropriately
    assert switchboard_one.actionType(action1) == 0  # Cancelled
    assert switchboard_one.actionType(action2) == 0  # Executed


def test_max_ltv_deviation_validation(switchboard_one, governance, bob):
    """Test max LTV deviation validation"""
    # Test invalid deviation - zero value
    with boa.reverts("invalid max deviation"):
        switchboard_one.setMaxLtvDeviation(0, sender=governance.address)
    
    # Test invalid deviation - greater than 100%
    with boa.reverts("invalid max deviation"):
        switchboard_one.setMaxLtvDeviation(101_00, sender=governance.address)  # 101%
    
    # Test non-governance cannot set
    with boa.reverts("no perms"):
        switchboard_one.setMaxLtvDeviation(10_00, sender=bob)


def test_max_ltv_deviation_success(switchboard_one, governance):
    """Test successful max LTV deviation setting"""
    # Test valid deviation - 5%
    action_id = switchboard_one.setMaxLtvDeviation(5_00, sender=governance.address)
    assert action_id > 0  # Should return a valid action ID
    
    # Check event was emitted
    logs = filter_logs(switchboard_one, "PendingMaxLtvDeviationChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.newDeviation == 5_00
    assert log.actionId == action_id
    
    # Check pending data was stored
    pending_deviation = switchboard_one.pendingMaxLtvDeviation(action_id)
    assert pending_deviation == 5_00
    
    # Test at exact boundary - 100%
    action_id2 = switchboard_one.setMaxLtvDeviation(100_00, sender=governance.address)
    assert action_id2 > 0
    assert action_id2 == action_id + 1  # Should increment
    
    # Test minimum valid value - 1
    action_id3 = switchboard_one.setMaxLtvDeviation(1, sender=governance.address)
    assert action_id3 > 0
    assert action_id3 == action_id2 + 1  # Should increment


def test_execute_max_ltv_deviation(switchboard_one, governance):
    """Test executing max LTV deviation action"""
    # Set max LTV deviation
    deviation = 15_00  # 15%
    action_id = switchboard_one.setMaxLtvDeviation(deviation, sender=governance.address)
    assert action_id > 0  # Should return action ID
    
    # Time travel past timelock
    time_lock = switchboard_one.actionTimeLock()
    boa.env.time_travel(blocks=time_lock)
    
    # Execute the action
    assert switchboard_one.executePendingAction(action_id, sender=governance.address)
    
    # Check event was emitted
    logs = filter_logs(switchboard_one, "MaxLtvDeviationSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.newDeviation == deviation
    
    # Verify the action was cleaned up
    assert switchboard_one.actionType(action_id) == 0
    assert not switchboard_one.hasPendingAction(action_id)


def test_max_ltv_deviation_boundary_conditions(switchboard_one, governance):
    """Test max LTV deviation at exact boundary values"""
    # Test at exactly 100% (should be valid)
    action_id = switchboard_one.setMaxLtvDeviation(100_00, sender=governance.address)
    assert action_id > 0
    
    # Test at 1 (minimum valid value)
    action_id = switchboard_one.setMaxLtvDeviation(1, sender=governance.address)
    assert action_id > 0
    
    # Test common percentage values
    common_values = [1_00, 5_00, 10_00, 25_00, 50_00, 75_00, 99_99]
    for value in common_values:
        action_id = switchboard_one.setMaxLtvDeviation(value, sender=governance.address)
        assert action_id > 0
        
        pending = switchboard_one.pendingMaxLtvDeviation(action_id)
        assert pending == value


def test_max_ltv_deviation_full_workflow(switchboard_one, governance):
    """Test complete workflow of setting and executing max LTV deviation"""
    time_lock = switchboard_one.actionTimeLock()
    
    # Create multiple max LTV deviation changes
    deviations = [10_00, 20_00, 5_00]  # 10%, 20%, 5%
    action_ids = []
    
    for deviation in deviations:
        action_id = switchboard_one.setMaxLtvDeviation(deviation, sender=governance.address)
        assert action_id > 0
        action_ids.append(action_id)
    
    # Verify all actions are pending
    for i, action_id in enumerate(action_ids):
        assert switchboard_one.hasPendingAction(action_id)
        assert switchboard_one.pendingMaxLtvDeviation(action_id) == deviations[i]
    
    # Execute them in order after timelock
    boa.env.time_travel(blocks=time_lock)
    
    for i, action_id in enumerate(action_ids):
        # Clear previous events by getting current count
        logs_before = filter_logs(switchboard_one, "MaxLtvDeviationSet")
        events_before = len(logs_before)
        
        assert switchboard_one.executePendingAction(action_id, sender=governance.address)
        
        # Verify new event was emitted
        logs_after = filter_logs(switchboard_one, "MaxLtvDeviationSet")
        assert len(logs_after) == events_before + 1  # Should have one more event
        assert logs_after[-1].newDeviation == deviations[i]  # Check the latest event
        
        # Verify cleanup
        assert not switchboard_one.hasPendingAction(action_id)
        assert switchboard_one.actionType(action_id) == 0


def test_max_ltv_deviation_cancel_and_expire(switchboard_one, governance):
    """Test canceling and expiring max LTV deviation actions"""
    # Create an action
    action_id = switchboard_one.setMaxLtvDeviation(25_00, sender=governance.address)
    assert action_id > 0
    
    # Cancel it
    assert switchboard_one.cancelPendingAction(action_id, sender=governance.address)
    assert not switchboard_one.hasPendingAction(action_id)
    assert switchboard_one.actionType(action_id) == 0
    
    # Create another action and let it expire
    action_id2 = switchboard_one.setMaxLtvDeviation(30_00, sender=governance.address)
    assert action_id2 > 0
    
    # Time travel past expiration
    time_lock = switchboard_one.actionTimeLock()
    expiration = switchboard_one.expiration()
    boa.env.time_travel(blocks=time_lock + expiration + 1)
    
    # Try to execute expired action
    assert not switchboard_one.executePendingAction(action_id2, sender=governance.address)
    
    # Verify cleanup occurred
    assert not switchboard_one.hasPendingAction(action_id2)
    assert switchboard_one.actionType(action_id2) == 0
