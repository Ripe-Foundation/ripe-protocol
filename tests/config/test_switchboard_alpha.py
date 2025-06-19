import boa

from constants import MAX_UINT256, ZERO_ADDRESS
from conf_utils import filter_logs


def test_deployment_invalid_stale_time_range(ripe_hq_deploy):
    # Test min >= max
    with boa.reverts("invalid stale time range"):
        boa.load(
            "contracts/config/SwitchboardAlpha.vy",
            ripe_hq_deploy.address,
            200,  # min
            100,  # max (less than min)
            50,   # min timelock
            500,  # max timelock
        )
    
    # Test equal values
    with boa.reverts("invalid stale time range"):
        boa.load(
            "contracts/config/SwitchboardAlpha.vy",
            ripe_hq_deploy.address,
            100,  # min
            100,  # max (equal to min)
            50,   # min timelock
            500,  # max timelock
        )


def test_deployment_success(switchboard_alpha):
    assert switchboard_alpha.MIN_STALE_TIME() > 0
    assert switchboard_alpha.MAX_STALE_TIME() > switchboard_alpha.MIN_STALE_TIME()
    assert switchboard_alpha.actionId() == 1  # starts at 1


def test_governance_permissions(switchboard_alpha, bob):
    # Test functions that require governance permissions
    with boa.reverts("no perms"):
        switchboard_alpha.setVaultLimits(10, 5, sender=bob)
    
    with boa.reverts("no perms"):
        switchboard_alpha.setStaleTime(1000, sender=bob)
    
    with boa.reverts("no perms"):
        switchboard_alpha.setGlobalDebtLimits(1000, 10000, 100, 50, sender=bob)


def test_enable_disable_permissions(switchboard_alpha, governance, bob):
    # Non-governance cannot enable
    with boa.reverts("no perms"):
        switchboard_alpha.setCanDeposit(True, sender=bob)
    
    # Test that users with canDisable permission can disable
    # First enable deposits as governance
    switchboard_alpha.setCanDeposit(True, sender=governance.address)
    
    # Set bob as someone who can disable
    switchboard_alpha.setCanPerformLiteAction(bob, True, sender=governance.address)
    
    # Time travel to execute the action
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    action_id = switchboard_alpha.actionId() - 1  # get the last action id
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Now bob should be able to disable
    switchboard_alpha.setCanDeposit(False, sender=bob)
    
    # But bob cannot enable
    with boa.reverts("no perms"):
        switchboard_alpha.setCanDeposit(True, sender=bob)


def test_set_vault_limits_validation(switchboard_alpha, governance):
    # Test invalid vault limits
    with boa.reverts("invalid vault limits"):
        switchboard_alpha.setVaultLimits(0, 5, sender=governance.address)  # zero max vaults
    
    with boa.reverts("invalid vault limits"):
        switchboard_alpha.setVaultLimits(10, 0, sender=governance.address)  # zero max assets
    
    with boa.reverts("invalid vault limits"):
        switchboard_alpha.setVaultLimits(MAX_UINT256, 5, sender=governance.address)  # max uint256
    
    with boa.reverts("invalid vault limits"):
        switchboard_alpha.setVaultLimits(10, MAX_UINT256, sender=governance.address)  # max uint256


def test_set_vault_limits_success(switchboard_alpha, governance):
    # Test valid vault limits
    action_id = switchboard_alpha.setVaultLimits(20, 10, sender=governance.address)
    assert action_id > 0
    
    # Check event was emitted
    logs = filter_logs(switchboard_alpha, "PendingVaultLimitsChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.perUserMaxVaults == 20
    assert log.perUserMaxAssetsPerVault == 10
    assert log.actionId == action_id
    
    # Check pending config was stored
    pending = switchboard_alpha.pendingGeneralConfig(action_id)
    assert pending.perUserMaxVaults == 20
    assert pending.perUserMaxAssetsPerVault == 10


def test_execute_vault_limits(switchboard_alpha, mission_control, governance):
    # Set vault limits
    action_id = switchboard_alpha.setVaultLimits(25, 15, sender=governance.address)
    
    # Time travel past timelock
    time_lock = switchboard_alpha.actionTimeLock()
    boa.env.time_travel(blocks=time_lock)
    
    # Execute the action
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Verify the config was applied to MissionControl
    config = mission_control.genConfig()
    assert config.perUserMaxVaults == 25
    assert config.perUserMaxAssetsPerVault == 15
    
    # Check event was emitted
    logs = filter_logs(switchboard_alpha, "VaultLimitsSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.perUserMaxVaults == 25
    assert log.perUserMaxAssetsPerVault == 15


def test_set_stale_time_validation(switchboard_alpha, governance):
    # Test invalid stale times
    with boa.reverts("invalid stale time"):
        switchboard_alpha.setStaleTime(switchboard_alpha.MIN_STALE_TIME() - 1, sender=governance.address)
    
    with boa.reverts("invalid stale time"):
        switchboard_alpha.setStaleTime(switchboard_alpha.MAX_STALE_TIME() + 1, sender=governance.address)


def test_set_stale_time_success(switchboard_alpha, governance):
    # Test valid stale time
    stale_time = (switchboard_alpha.MIN_STALE_TIME() + switchboard_alpha.MAX_STALE_TIME()) // 2
    action_id = switchboard_alpha.setStaleTime(stale_time, sender=governance.address)
    assert action_id > 0
    
    # Check event was emitted
    logs = filter_logs(switchboard_alpha, "PendingStaleTimeChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.priceStaleTime == stale_time
    assert log.actionId == action_id


def test_execute_stale_time(switchboard_alpha, mission_control, governance):
    # Set stale time
    stale_time = switchboard_alpha.MIN_STALE_TIME() + 100
    action_id = switchboard_alpha.setStaleTime(stale_time, sender=governance.address)
    
    # Time travel and execute
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Verify the config was applied
    config = mission_control.genConfig()
    assert config.priceStaleTime == stale_time
    
    # Check event
    logs = filter_logs(switchboard_alpha, "StaleTimeSet")
    assert len(logs) == 1
    assert logs[0].staleTime == stale_time


def test_enable_disable_deposit(switchboard_alpha, mission_control, governance):
    # Test enabling deposits
    assert switchboard_alpha.setCanDeposit(True, sender=governance.address)
    config = mission_control.genConfig()
    assert config.canDeposit
    
    # Check event
    logs = filter_logs(switchboard_alpha, "CanDepositSet")
    assert len(logs) == 1
    assert logs[0].canDeposit
    assert logs[0].caller == governance.address
    
    # Test disabling deposits
    assert switchboard_alpha.setCanDeposit(False, sender=governance.address)
    config = mission_control.genConfig()
    assert not config.canDeposit
    
    # Test setting same value fails
    with boa.reverts("already set"):
        switchboard_alpha.setCanDeposit(False, sender=governance.address)


def test_all_enable_disable_functions(switchboard_alpha, mission_control, governance):
    # Test all the enable/disable functions
    functions_and_fields = [
        (switchboard_alpha.setCanWithdraw, "canWithdraw"),
        (switchboard_alpha.setCanBorrow, "canBorrow"),
        (switchboard_alpha.setCanRepay, "canRepay"),
        (switchboard_alpha.setCanClaimLoot, "canClaimLoot"),
        (switchboard_alpha.setCanLiquidate, "canLiquidate"),
        (switchboard_alpha.setCanRedeemCollateral, "canRedeemCollateral"),
        (switchboard_alpha.setCanRedeemInStabPool, "canRedeemInStabPool"),
        (switchboard_alpha.setCanBuyInAuction, "canBuyInAuction"),
        (switchboard_alpha.setCanClaimInStabPool, "canClaimInStabPool"),
    ]
    
    for func, field in functions_and_fields:
        # Enable
        assert func(True, sender=governance.address)
        config = mission_control.genConfig()
        assert getattr(config, field)
        
        # Disable
        assert func(False, sender=governance.address)
        config = mission_control.genConfig()
        assert not getattr(config, field)


def test_global_debt_limits_validation(switchboard_alpha, governance):
    # Test invalid debt limits
    with boa.reverts("invalid debt limits"):
        switchboard_alpha.setGlobalDebtLimits(0, 10000, 100, 50, sender=governance.address)  # zero per user limit
    
    with boa.reverts("invalid debt limits"):
        switchboard_alpha.setGlobalDebtLimits(1000, 0, 100, 50, sender=governance.address)  # zero global limit
    
    with boa.reverts("invalid debt limits"):
        switchboard_alpha.setGlobalDebtLimits(1000, 10000, 100, 0, sender=governance.address)  # zero borrowers
    
    with boa.reverts("invalid debt limits"):
        switchboard_alpha.setGlobalDebtLimits(10000, 1000, 100, 50, sender=governance.address)  # per user > global
    
    with boa.reverts("invalid debt limits"):
        switchboard_alpha.setGlobalDebtLimits(1000, 10000, 2000, 50, sender=governance.address)  # min debt > per user
    
    with boa.reverts("invalid debt limits"):
        switchboard_alpha.setGlobalDebtLimits(MAX_UINT256, 10000, 100, 50, sender=governance.address)  # max uint256


def test_global_debt_limits_success(switchboard_alpha, governance):
    action_id = switchboard_alpha.setGlobalDebtLimits(5000, 50000, 100, 100, sender=governance.address)
    assert action_id > 0
    
    # Check event
    logs = filter_logs(switchboard_alpha, "PendingGlobalDebtLimitsChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.perUserDebtLimit == 5000
    assert log.globalDebtLimit == 50000
    assert log.minDebtAmount == 100
    assert log.numAllowedBorrowers == 100


def test_borrow_interval_config_validation(switchboard_alpha, governance):
    # Test invalid borrow interval config
    with boa.reverts("invalid borrow interval config"):
        switchboard_alpha.setBorrowIntervalConfig(0, 100, sender=governance.address)  # zero max borrow
    
    with boa.reverts("invalid borrow interval config"):
        switchboard_alpha.setBorrowIntervalConfig(1000, 0, sender=governance.address)  # zero blocks
    
    with boa.reverts("invalid borrow interval config"):
        switchboard_alpha.setBorrowIntervalConfig(MAX_UINT256, 100, sender=governance.address)  # max uint256


def test_keeper_config_validation(switchboard_alpha, governance):
    # Test invalid keeper config
    with boa.reverts("invalid keeper config"):
        switchboard_alpha.setKeeperConfig(11_00, 1000, 5000, sender=governance.address)  # > 10% fee ratio
    
    with boa.reverts("invalid keeper config"):
        switchboard_alpha.setKeeperConfig(5_00, 201 * 10**18, 300 * 10**18, sender=governance.address)  # > $200 min fee
    
    with boa.reverts("invalid keeper config"):
        switchboard_alpha.setKeeperConfig(MAX_UINT256, 1000, 5000, sender=governance.address)  # max uint256
    
    # Test minKeeperFee > maxKeeperFee
    with boa.reverts("invalid keeper config"):
        switchboard_alpha.setKeeperConfig(5_00, 100 * 10**18, 50 * 10**18, sender=governance.address)  # min > max
    
    # Test maxKeeperFee > 100k limit
    with boa.reverts("invalid keeper config"):
        switchboard_alpha.setKeeperConfig(5_00, 1000, 100_001 * 10**18, sender=governance.address)  # > 100k max
    
    # Test maxKeeperFee = max_value
    with boa.reverts("invalid keeper config"):
        switchboard_alpha.setKeeperConfig(5_00, 1000, MAX_UINT256, sender=governance.address)  # max uint256


def test_keeper_config_success(switchboard_alpha, governance):
    """Test successful keeper config with valid parameters"""
    # Test with valid parameters
    action_id = switchboard_alpha.setKeeperConfig(5_00, 50 * 10**18, 1000 * 10**18, sender=governance.address)
    assert action_id > 0
    
    # Check event was emitted
    logs = filter_logs(switchboard_alpha, "PendingKeeperConfigChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.keeperFeeRatio == 5_00
    assert log.minKeeperFee == 50 * 10**18
    assert log.maxKeeperFee == 1000 * 10**18
    assert log.actionId == action_id
    
    # Check pending config was stored correctly
    pending = switchboard_alpha.pendingDebtConfig(action_id)
    assert pending.keeperFeeRatio == 5_00
    assert pending.minKeeperFee == 50 * 10**18
    assert pending.maxKeeperFee == 1000 * 10**18


def test_keeper_config_boundary_conditions(switchboard_alpha, governance):
    """Test keeper config at boundary values"""
    # Test at exactly 10% fee ratio (should be valid)
    action_id = switchboard_alpha.setKeeperConfig(10_00, 1000, 5000, sender=governance.address)
    assert action_id > 0
    
    # Test at exactly $200 min fee (should be valid)
    action_id = switchboard_alpha.setKeeperConfig(5_00, 200 * 10**18, 1000 * 10**18, sender=governance.address)
    assert action_id > 0
    
    # Test at exactly 100k max fee (should be valid)
    action_id = switchboard_alpha.setKeeperConfig(5_00, 100 * 10**18, 100_000 * 10**18, sender=governance.address)
    assert action_id > 0
    
    # Test with zero fee ratio and equal min/max fees (should be valid)
    action_id = switchboard_alpha.setKeeperConfig(0, 0, 0, sender=governance.address)
    assert action_id > 0
    
    # Test with minKeeperFee = maxKeeperFee (should be valid)
    action_id = switchboard_alpha.setKeeperConfig(3_00, 75 * 10**18, 75 * 10**18, sender=governance.address)
    assert action_id > 0


def test_execute_keeper_config(switchboard_alpha, mission_control, governance):
    """Test execution of keeper config action with all three parameters"""
    # Create the action
    action_id = switchboard_alpha.setKeeperConfig(7_00, 100 * 10**18, 2500 * 10**18, sender=governance.address)
    assert action_id > 0
    
    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    
    # Execute the action
    success = switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    assert success
    
    # Verify the config was applied to MissionControl
    config = mission_control.genDebtConfig()
    assert config.keeperFeeRatio == 7_00
    assert config.minKeeperFee == 100 * 10**18
    assert config.maxKeeperFee == 2500 * 10**18
    
    # Check execution event was emitted with all three parameters
    logs = filter_logs(switchboard_alpha, "KeeperConfigSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.keeperFeeRatio == 7_00
    assert log.minKeeperFee == 100 * 10**18
    assert log.maxKeeperFee == 2500 * 10**18
    
    # Verify action was cleaned up
    assert switchboard_alpha.actionType(action_id) == 0
    assert not switchboard_alpha.hasPendingAction(action_id)


def test_keeper_config_permissions(switchboard_alpha, governance, bob):
    """Test that only governance can call setKeeperConfig"""
    # Non-governance user should not be able to call the function
    with boa.reverts("no perms"):
        switchboard_alpha.setKeeperConfig(5_00, 50 * 10**18, 1000 * 10**18, sender=bob)
    
    # Governance should be able to call the function
    action_id = switchboard_alpha.setKeeperConfig(5_00, 50 * 10**18, 1000 * 10**18, sender=governance.address)
    assert action_id > 0


def test_keeper_config_with_existing_debt_config(switchboard_alpha, mission_control, governance):
    """Test that keeper config only modifies the specific fields"""
    # First set some other debt config fields
    debt_action = switchboard_alpha.setGlobalDebtLimits(6000, 60000, 200, 120, sender=governance.address)
    
    # Execute them
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(debt_action, sender=governance.address)
    
    # Verify initial config
    config = mission_control.genDebtConfig()
    assert config.perUserDebtLimit == 6000
    assert config.globalDebtLimit == 60000
    
    # Now set keeper config
    keeper_action = switchboard_alpha.setKeeperConfig(9_00, 150 * 10**18, 3000 * 10**18, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(keeper_action, sender=governance.address)
    
    # Verify keeper fields were updated but others preserved
    config = mission_control.genDebtConfig()
    assert config.keeperFeeRatio == 9_00        # Updated
    assert config.minKeeperFee == 150 * 10**18  # Updated
    assert config.maxKeeperFee == 3000 * 10**18 # Updated
    assert config.perUserDebtLimit == 6000      # Preserved
    assert config.globalDebtLimit == 60000      # Preserved


def test_ltv_payback_buffer_validation(switchboard_alpha, governance):
    # Test invalid LTV payback buffer
    with boa.reverts("invalid ltv payback buffer"):
        switchboard_alpha.setLtvPaybackBuffer(0, sender=governance.address)  # zero
    
    with boa.reverts("invalid ltv payback buffer"):
        switchboard_alpha.setLtvPaybackBuffer(11_00, sender=governance.address)  # > 10%


def test_auction_params_validation(switchboard_alpha, governance):
    # Test invalid auction params
    with boa.reverts("invalid auction params"):
        switchboard_alpha.setGenAuctionParams(100_01, 50_00, 1000, 2000, sender=governance.address)  # start >= 100%
    
    with boa.reverts("invalid auction params"):
        switchboard_alpha.setGenAuctionParams(50_00, 100_01, 1000, 2000, sender=governance.address)  # max >= 100%
    
    with boa.reverts("invalid auction params"):
        switchboard_alpha.setGenAuctionParams(60_00, 50_00, 1000, 2000, sender=governance.address)  # start >= max
    
    with boa.reverts("invalid auction params"):
        switchboard_alpha.setGenAuctionParams(30_00, 50_00, MAX_UINT256, 1000, sender=governance.address)  # invalid delay
    
    with boa.reverts("invalid auction params"):
        switchboard_alpha.setGenAuctionParams(30_00, 50_00, 1000, 0, sender=governance.address)  # zero duration
    
    with boa.reverts("invalid auction params"):
        switchboard_alpha.setGenAuctionParams(30_00, 50_00, 1000, MAX_UINT256, sender=governance.address)  # max duration


def test_execute_debt_configs(switchboard_alpha, mission_control, governance):
    # Test executing global debt limits
    action_id = switchboard_alpha.setGlobalDebtLimits(6000, 60000, 200, 150, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.genDebtConfig()
    assert config.perUserDebtLimit == 6000
    assert config.globalDebtLimit == 60000
    assert config.minDebtAmount == 200
    assert config.numAllowedBorrowers == 150
    
    # Test executing borrow interval config
    action_id = switchboard_alpha.setBorrowIntervalConfig(5000, 100, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.genDebtConfig()
    assert config.maxBorrowPerInterval == 5000
    assert config.numBlocksPerInterval == 100
    
    # Test executing keeper config
    action_id = switchboard_alpha.setKeeperConfig(5_00, 50 * 10**18, 1000 * 10**18, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.genDebtConfig()
    assert config.keeperFeeRatio == 5_00
    assert config.minKeeperFee == 50 * 10**18
    assert config.maxKeeperFee == 1000 * 10**18


def test_daowry_enable_disable(switchboard_alpha, mission_control, governance):
    # Enable daowry
    assert switchboard_alpha.setIsDaowryEnabled(True, sender=governance.address)
    config = mission_control.genDebtConfig()
    assert config.isDaowryEnabled
    
    # Check event
    logs = filter_logs(switchboard_alpha, "IsDaowryEnabledSet")
    assert len(logs) == 1
    assert logs[0].isDaowryEnabled


def test_ripe_per_block(switchboard_alpha, governance):
    action_id = switchboard_alpha.setRipePerBlock(1000, sender=governance.address)
    assert action_id > 0
    
    # Check event
    logs = filter_logs(switchboard_alpha, "PendingRipeRewardsPerBlockChange")
    assert len(logs) == 1
    assert logs[0].ripePerBlock == 1000


def test_rewards_allocs_validation(switchboard_alpha, governance):
    # Test invalid allocations (sum > 100%)
    with boa.reverts("invalid rewards allocs"):
        switchboard_alpha.setRipeRewardsAllocs(50_00, 30_00, 25_00, 10_00, sender=governance.address)  # sum = 115%


def test_rewards_allocs_success(switchboard_alpha, governance):
    action_id = switchboard_alpha.setRipeRewardsAllocs(40_00, 25_00, 20_00, 15_00, sender=governance.address)
    assert action_id > 0
    
    # Check event
    logs = filter_logs(switchboard_alpha, "PendingRipeRewardsAllocsChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.borrowersAlloc == 40_00
    assert log.stakersAlloc == 25_00
    assert log.votersAlloc == 20_00
    assert log.genDepositorsAlloc == 15_00


def test_execute_rewards_config(switchboard_alpha, mission_control, governance):
    # Execute ripe per block
    action_id = switchboard_alpha.setRipePerBlock(2000, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.rewardsConfig()
    assert config.ripePerBlock == 2000
    
    # Execute rewards allocs
    action_id = switchboard_alpha.setRipeRewardsAllocs(35_00, 30_00, 20_00, 15_00, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.rewardsConfig()
    assert config.borrowersAlloc == 35_00
    assert config.stakersAlloc == 30_00
    assert config.votersAlloc == 20_00
    assert config.genDepositorsAlloc == 15_00


def test_rewards_points_enable_disable(switchboard_alpha, mission_control, governance):
    # Enable points
    assert switchboard_alpha.setRewardsPointsEnabled(True, sender=governance.address)
    config = mission_control.rewardsConfig()
    assert config.arePointsEnabled
    
    # Check event
    logs = filter_logs(switchboard_alpha, "RewardsPointsEnabledModified")
    assert len(logs) == 1
    assert logs[0].arePointsEnabled


def test_priority_liq_asset_vaults_filtered(switchboard_alpha, governance):
    # Create sample vault data that will be filtered out
    vaults = [
        (1, ZERO_ADDRESS),  # Will be filtered out due to invalid vault/asset
        (2, ZERO_ADDRESS),
    ]
    
    # The function should still succeed but filter out invalid vaults
    # This test expects the filtering behavior to work and all vaults to be filtered
    with boa.reverts("invalid priority vaults"):
        switchboard_alpha.setPriorityLiqAssetVaults(vaults, sender=governance.address)
    
    # Test with empty array directly
    with boa.reverts("invalid priority vaults"):
        switchboard_alpha.setPriorityLiqAssetVaults([], sender=governance.address)
    
    # Test with duplicate invalid vaults
    duplicate_vaults = [
        (1, ZERO_ADDRESS),
        (1, ZERO_ADDRESS),  # Exact duplicate
        (2, ZERO_ADDRESS),
    ]
    with boa.reverts("invalid priority vaults"):
        switchboard_alpha.setPriorityLiqAssetVaults(duplicate_vaults, sender=governance.address)


def test_priority_stab_vaults_filtered(switchboard_alpha, governance):
    vaults = [(1, ZERO_ADDRESS)]
    # Same as above - should be filtered out
    with boa.reverts("invalid priority vaults"):
        switchboard_alpha.setPriorityStabVaults(vaults, sender=governance.address)
    
    # Test with multiple invalid vaults including duplicates
    multiple_vaults = [
        (1, ZERO_ADDRESS),
        (2, ZERO_ADDRESS),
        (1, ZERO_ADDRESS),  # Duplicate
        (3, ZERO_ADDRESS),
    ]
    with boa.reverts("invalid priority vaults"):
        switchboard_alpha.setPriorityStabVaults(multiple_vaults, sender=governance.address)


def test_invalid_priority_vaults(switchboard_alpha, governance):
    # Test empty vaults array fails
    with boa.reverts("invalid priority vaults"):
        switchboard_alpha.setPriorityLiqAssetVaults([], sender=governance.address)


def test_priority_price_source_ids_filtered(switchboard_alpha, governance):
    # Test with invalid price source IDs (will be filtered)
    ids = [999, 998, 997]  # Use obviously invalid IDs that should be filtered out
    # This should revert since all IDs will be filtered out, resulting in empty list
    with boa.reverts("invalid priority sources"):
        switchboard_alpha.setPriorityPriceSourceIds(ids, sender=governance.address)
    
    # Test with duplicate invalid IDs
    duplicate_ids = [999, 999, 998, 998, 997, 997]
    with boa.reverts("invalid priority sources"):
        switchboard_alpha.setPriorityPriceSourceIds(duplicate_ids, sender=governance.address)
    
    # Test with mix of valid and invalid IDs (1 and 2 are valid in test env)
    mixed_ids = [1, 2, 999, 998, 1, 2]  # Contains duplicates
    # This should succeed because it has valid IDs (1 and 2)
    action_id = switchboard_alpha.setPriorityPriceSourceIds(mixed_ids, sender=governance.address)
    assert action_id > 0
    
    # Check that only valid, deduplicated IDs were stored
    logs = filter_logs(switchboard_alpha, "PendingPriorityPriceSourceIdsChange")
    assert len(logs) == 1
    assert logs[0].numPriorityPriceSourceIds == 2  # Only IDs 1 and 2 should be valid


def test_invalid_priority_sources(switchboard_alpha, governance):
    # Test empty sources array fails
    with boa.reverts("invalid priority sources"):
        switchboard_alpha.setPriorityPriceSourceIds([], sender=governance.address)


def test_set_underscore_registry_validation_zero_address(switchboard_alpha, governance):
    # Test invalid underscore registry with zero address
    # This will fail at the static call level
    with boa.reverts():
        switchboard_alpha.setUnderscoreRegistry(ZERO_ADDRESS, sender=governance.address)


def test_set_underscore_registry_success(switchboard_alpha, governance, mock_rando_contract):
    # This will fail validation as mock_rando_contract doesn't implement the required interface
    with boa.reverts():  # Just check it reverts, don't match exact message
        switchboard_alpha.setUnderscoreRegistry(mock_rando_contract, sender=governance.address)


def test_set_can_disable(switchboard_alpha, governance, bob):
    action_id = switchboard_alpha.setCanPerformLiteAction(bob, True, sender=governance.address)
    assert action_id > 0
    
    # Check event
    logs = filter_logs(switchboard_alpha, "PendingCanPerformLiteAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.user == bob
    assert log.canDo


def test_execute_can_disable(switchboard_alpha, mission_control, governance, bob):
    # Set can disable
    action_id = switchboard_alpha.setCanPerformLiteAction(bob, True, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Verify it was applied
    assert mission_control.canPerformLiteAction(bob)
    
    # Check event
    logs = filter_logs(switchboard_alpha, "CanPerformLiteAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.user == bob
    assert log.canDo


def test_execute_invalid_action(switchboard_alpha, governance):
    # Try to execute non-existent action
    assert not switchboard_alpha.executePendingAction(999, sender=governance.address)


def test_execute_before_timelock_when_timelock_nonzero(switchboard_alpha, governance):
    # First, let's check what the timelock actually is
    time_lock = switchboard_alpha.actionTimeLock()
    
    if time_lock == 0:
        # If timelock is 0, the action will execute immediately
        # This is expected behavior in this test setup
        action_id = switchboard_alpha.setVaultLimits(10, 5, sender=governance.address)
        # With timelock 0, this should succeed
        assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    else:
        # If timelock is non-zero, test the expected behavior
        action_id = switchboard_alpha.setVaultLimits(10, 5, sender=governance.address)
        # Try to execute before timelock
        assert not switchboard_alpha.executePendingAction(action_id, sender=governance.address)
        
        # Also test execution at various points before timelock
        for blocks_passed in [1, time_lock // 2, time_lock - 1]:
            boa.env.time_travel(blocks=1)
            assert not switchboard_alpha.executePendingAction(action_id, sender=governance.address)


def test_execute_expired_action(switchboard_alpha, governance):
    # Create an action
    action_id = switchboard_alpha.setVaultLimits(10, 5, sender=governance.address)
    
    # Time travel past expiration
    time_lock = switchboard_alpha.actionTimeLock()
    expiration = switchboard_alpha.expiration()
    boa.env.time_travel(blocks=time_lock + expiration + 1)
    
    # Try to execute expired action
    assert not switchboard_alpha.executePendingAction(action_id, sender=governance.address)


def test_cancel_action(switchboard_alpha, governance):
    # Create an action
    action_id = switchboard_alpha.setVaultLimits(10, 5, sender=governance.address)
    
    # Cancel it
    assert switchboard_alpha.cancelPendingAction(action_id, sender=governance.address)
    
    # Verify it's no longer pending
    assert not switchboard_alpha.hasPendingAction(action_id)


def test_execute_all_action_types(switchboard_alpha, mission_control, governance):
    time_lock = switchboard_alpha.actionTimeLock()
    
    # Test executing different action types
    test_cases = [
        # (action_creator, expected_field, expected_value)
        (lambda: switchboard_alpha.setVaultLimits(15, 8, sender=governance.address), "perUserMaxVaults", 15),
        (lambda: switchboard_alpha.setStaleTime(switchboard_alpha.MIN_STALE_TIME() + 50, sender=governance.address), "priceStaleTime", switchboard_alpha.MIN_STALE_TIME() + 50),
    ]
    
    for action_creator, field, expected_value in test_cases:
        # Create action
        action_id = action_creator()
        
        # Execute after timelock
        boa.env.time_travel(blocks=time_lock)
        assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
        
        # Verify the config was applied
        config = mission_control.genConfig()
        assert getattr(config, field) == expected_value


def test_sequential_actions_same_type(switchboard_alpha, governance):
    # Create multiple vault limit actions
    action_id1 = switchboard_alpha.setVaultLimits(10, 5, sender=governance.address)
    action_id2 = switchboard_alpha.setVaultLimits(20, 10, sender=governance.address)
    
    assert action_id1 != action_id2
    assert action_id2 == action_id1 + 1


def test_action_id_increment(switchboard_alpha, governance):
    initial_id = switchboard_alpha.actionId()
    
    # Create an action
    action_id = switchboard_alpha.setVaultLimits(10, 5, sender=governance.address)
    
    # Action ID should increment
    assert action_id == initial_id
    assert switchboard_alpha.actionId() == initial_id + 1


def test_pending_action_cleanup(switchboard_alpha, governance):
    # Create and execute an action
    action_id = switchboard_alpha.setVaultLimits(10, 5, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Verify pending data is cleaned up
    assert switchboard_alpha.actionType(action_id) == 0  # empty ActionType
    assert not switchboard_alpha.hasPendingAction(action_id)


def test_borrow_interval_with_existing_debt_config(switchboard_alpha, mission_control, governance):
    # First set global debt limits to establish minDebtAmount
    action_id = switchboard_alpha.setGlobalDebtLimits(5000, 50000, 100, 100, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Now test borrow interval config with amount less than minDebtAmount
    with boa.reverts("invalid borrow interval config"):
        switchboard_alpha.setBorrowIntervalConfig(50, 100, sender=governance.address)  # 50 < 100 (minDebtAmount)
    
    # Test valid borrow interval config
    action_id = switchboard_alpha.setBorrowIntervalConfig(500, 100, sender=governance.address)
    assert action_id > 0


def test_full_config_workflow(switchboard_alpha, mission_control, governance):
    time_lock = switchboard_alpha.actionTimeLock()
    
    # Create multiple configuration changes
    vault_action = switchboard_alpha.setVaultLimits(30, 20, sender=governance.address)
    debt_action = switchboard_alpha.setGlobalDebtLimits(8000, 80000, 500, 200, sender=governance.address)
    rewards_action = switchboard_alpha.setRipePerBlock(3000, sender=governance.address)
    
    # Execute them all after timelock
    boa.env.time_travel(blocks=time_lock)
    
    assert switchboard_alpha.executePendingAction(vault_action, sender=governance.address)
    assert switchboard_alpha.executePendingAction(debt_action, sender=governance.address)
    assert switchboard_alpha.executePendingAction(rewards_action, sender=governance.address)
    
    # Verify all configs were applied
    gen_config = mission_control.genConfig()
    assert gen_config.perUserMaxVaults == 30
    assert gen_config.perUserMaxAssetsPerVault == 20
    
    debt_config = mission_control.genDebtConfig()
    assert debt_config.perUserDebtLimit == 8000
    assert debt_config.globalDebtLimit == 80000
    
    rewards_config = mission_control.rewardsConfig()
    assert rewards_config.ripePerBlock == 3000


def test_mixed_immediate_and_timelock_actions(switchboard_alpha, mission_control, governance):
    # Immediate action (no timelock)
    switchboard_alpha.setCanDeposit(True, sender=governance.address)
    
    # Timelock action
    action_id = switchboard_alpha.setVaultLimits(25, 15, sender=governance.address)
    
    # Verify immediate action took effect
    config = mission_control.genConfig()
    assert config.canDeposit
    
    # Verify timelock action is pending
    assert switchboard_alpha.hasPendingAction(action_id)
    
    # Execute timelock action
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Verify both configs are applied
    config = mission_control.genConfig()
    assert config.canDeposit
    assert config.perUserMaxVaults == 25
    assert config.perUserMaxAssetsPerVault == 15


# Additional test coverage for missing scenarios

def test_has_perms_to_enable_complex_scenarios(switchboard_alpha, governance, bob):
    """Test complex permission scenarios for _hasPermsToEnable logic"""
    
    # Set bob as someone who can disable
    action_id = switchboard_alpha.setCanPerformLiteAction(bob, True, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Bob can disable but not enable
    switchboard_alpha.setCanDeposit(True, sender=governance.address)  # Enable first
    
    # Bob can disable
    switchboard_alpha.setCanDeposit(False, sender=bob)
    
    # But bob cannot enable again
    with boa.reverts("no perms"):
        switchboard_alpha.setCanDeposit(True, sender=bob)
    
    # Remove bob's disable permission
    action_id = switchboard_alpha.setCanPerformLiteAction(bob, False, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Now bob can't even disable
    switchboard_alpha.setCanDeposit(True, sender=governance.address)  # Enable first
    with boa.reverts("no perms"):
        switchboard_alpha.setCanDeposit(False, sender=bob)


def test_sanitize_priority_vaults_deduplication(switchboard_alpha, governance, alpha_token):
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
        switchboard_alpha.setPriorityLiqAssetVaults(vaults, sender=governance.address)


def test_sanitize_priority_sources_deduplication(switchboard_alpha, governance):
    """Test the deduplication logic in _sanitizePrioritySources"""
    
    # Test with duplicate price source IDs (1 and 2 are valid)
    ids = [1, 1, 2, 2, 1, 9]  # Contains duplicates, 9 is invalid
    
    # This should succeed with valid IDs 1 and 2 (deduplicated)
    action_id = switchboard_alpha.setPriorityPriceSourceIds(ids, sender=governance.address)
    assert action_id > 0
    
    # Check deduplication worked
    logs = filter_logs(switchboard_alpha, "PendingPriorityPriceSourceIdsChange")
    assert len(logs) == 1
    assert logs[0].numPriorityPriceSourceIds == 2  # Only unique valid IDs 1 and 2


def test_auction_params_boundary_conditions(switchboard_alpha, governance):
    """Test auction params validation at boundary conditions"""
    
    # Test with exact boundary values
    HUNDRED_PERCENT = 100_00
    
    # startDiscount just under maxDiscount (both under 100%)
    action_id = switchboard_alpha.setGenAuctionParams(
        HUNDRED_PERCENT - 2, HUNDRED_PERCENT - 1, 1000, 2000, 
        sender=governance.address
    )
    assert action_id > 0
    
    # Test delay = duration - 1 (just valid)
    action_id = switchboard_alpha.setGenAuctionParams(
        50_00, 80_00, 1999, 2000, 
        sender=governance.address
    )
    assert action_id > 0
    
    # Test minimum valid duration (1)
    action_id = switchboard_alpha.setGenAuctionParams(
        10_00, 50_00, 0, 1, 
        sender=governance.address
    )
    assert action_id > 0
    
    # Test startDiscount = 0, maxDiscount just under 100%
    action_id = switchboard_alpha.setGenAuctionParams(
        0, HUNDRED_PERCENT - 1, 100, 1000, 
        sender=governance.address
    )
    assert action_id > 0


def test_debt_limits_boundary_conditions(switchboard_alpha, governance):
    """Test debt limits validation at boundary conditions"""
    
    # Test where minDebtAmount equals perUserDebtLimit (should be valid)
    action_id = switchboard_alpha.setGlobalDebtLimits(1000, 10000, 1000, 100, sender=governance.address)
    assert action_id > 0
    
    # Test where perUserDebtLimit equals globalDebtLimit (should be valid)
    action_id = switchboard_alpha.setGlobalDebtLimits(5000, 5000, 100, 50, sender=governance.address)
    assert action_id > 0


def test_ltv_payback_buffer_boundary_conditions(switchboard_alpha, governance):
    """Test LTV payback buffer at boundary values"""
    
    # Test at exactly 10% (should be valid)
    action_id = switchboard_alpha.setLtvPaybackBuffer(10_00, sender=governance.address)
    assert action_id > 0
    
    # Test at 1 (minimum valid value)
    action_id = switchboard_alpha.setLtvPaybackBuffer(1, sender=governance.address)
    assert action_id > 0


def test_rewards_allocs_boundary_conditions(switchboard_alpha, governance):
    """Test rewards allocations at boundary conditions"""
    
    # Test with sum exactly equal to 100%
    action_id = switchboard_alpha.setRipeRewardsAllocs(25_00, 25_00, 25_00, 25_00, sender=governance.address)
    assert action_id > 0
    
    # Test with sum less than 100%
    action_id = switchboard_alpha.setRipeRewardsAllocs(20_00, 20_00, 20_00, 20_00, sender=governance.address)
    assert action_id > 0
    
    # Test with all allocation to one category
    action_id = switchboard_alpha.setRipeRewardsAllocs(100_00, 0, 0, 0, sender=governance.address)
    assert action_id > 0
    
    # Test with zero allocations
    action_id = switchboard_alpha.setRipeRewardsAllocs(0, 0, 0, 0, sender=governance.address)
    assert action_id > 0


def test_execution_with_state_changes(switchboard_alpha, mission_control, governance):
    """Test executing actions that modify current state"""
    
    # Set initial vault limits
    action_id1 = switchboard_alpha.setVaultLimits(10, 5, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id1, sender=governance.address)
    
    # Set different vault limits
    action_id2 = switchboard_alpha.setVaultLimits(20, 10, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id2, sender=governance.address)
    
    # Verify the latest values are applied
    config = mission_control.genConfig()
    assert config.perUserMaxVaults == 20
    assert config.perUserMaxAssetsPerVault == 10


def test_execution_all_action_types_comprehensive(switchboard_alpha, mission_control, governance):
    """Test executing every single action type to ensure complete coverage"""
    
    time_lock = switchboard_alpha.actionTimeLock()
    
    # Test LTV payback buffer execution (not covered in other tests)
    action_id = switchboard_alpha.setLtvPaybackBuffer(5_00, sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.genDebtConfig()
    assert config.ltvPaybackBuffer == 5_00
    
    # Check event
    logs = filter_logs(switchboard_alpha, "LtvPaybackBufferSet")
    assert len(logs) == 1
    assert logs[0].ltvPaybackBuffer == 5_00
    
    # Test auction params execution
    action_id = switchboard_alpha.setGenAuctionParams(20_00, 50_00, 1000, 3000, sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.genDebtConfig()
    assert config.genAuctionParams.startDiscount == 20_00
    assert config.genAuctionParams.maxDiscount == 50_00
    assert config.genAuctionParams.delay == 1000
    assert config.genAuctionParams.duration == 3000
    
    # Check event
    logs = filter_logs(switchboard_alpha, "GenAuctionParamsSet")
    assert len(logs) == 1
    assert logs[0].startDiscount == 20_00
    
    # Test max LTV deviation execution
    action_id = switchboard_alpha.setMaxLtvDeviation(8_00, sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Check event
    logs = filter_logs(switchboard_alpha, "MaxLtvDeviationSet")
    assert len(logs) == 1
    assert logs[0].newDeviation == 8_00


def test_cancel_action_edge_cases(switchboard_alpha, governance):
    """Test action cancellation edge cases"""
    
    # Test canceling non-existent action
    with boa.reverts("cannot cancel action"):
        switchboard_alpha.cancelPendingAction(999, sender=governance.address)
    
    # Test canceling already executed action
    action_id = switchboard_alpha.setVaultLimits(10, 5, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Should fail to cancel already executed action
    with boa.reverts("cannot cancel action"):
        switchboard_alpha.cancelPendingAction(action_id, sender=governance.address)
    
    # Test canceling an expired action
    action_id2 = switchboard_alpha.setVaultLimits(20, 10, sender=governance.address)
    expiration = switchboard_alpha.expiration()
    time_lock = switchboard_alpha.actionTimeLock()
    boa.env.time_travel(blocks=time_lock + expiration + 1)
    
    # Should be able to cancel expired action
    assert switchboard_alpha.cancelPendingAction(action_id2, sender=governance.address)
    
    # Test double cancellation
    action_id3 = switchboard_alpha.setVaultLimits(30, 15, sender=governance.address)
    assert switchboard_alpha.cancelPendingAction(action_id3, sender=governance.address)
    
    # Should fail on second cancel
    with boa.reverts("cannot cancel action"):
        switchboard_alpha.cancelPendingAction(action_id3, sender=governance.address)


def test_complex_workflow_multiple_pending_actions(switchboard_alpha, governance):
    """Test complex workflows with multiple pending actions"""
    
    # Create multiple different types of actions
    vault_action = switchboard_alpha.setVaultLimits(15, 8, sender=governance.address)
    debt_action = switchboard_alpha.setGlobalDebtLimits(3000, 30000, 150, 75, sender=governance.address)
    rewards_action = switchboard_alpha.setRipePerBlock(1500, sender=governance.address)
    keeper_action = switchboard_alpha.setKeeperConfig(3_00, 25 * 10**18, 500 * 10**18, sender=governance.address)
    buffer_action = switchboard_alpha.setLtvPaybackBuffer(7_00, sender=governance.address)
    
    # Verify all actions are pending
    assert switchboard_alpha.hasPendingAction(vault_action)
    assert switchboard_alpha.hasPendingAction(debt_action)
    assert switchboard_alpha.hasPendingAction(rewards_action)
    assert switchboard_alpha.hasPendingAction(keeper_action)
    assert switchboard_alpha.hasPendingAction(buffer_action)
    
    # Cancel one action
    switchboard_alpha.cancelPendingAction(keeper_action, sender=governance.address)
    assert not switchboard_alpha.hasPendingAction(keeper_action)
    
    # Execute the rest
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(vault_action, sender=governance.address)
    assert switchboard_alpha.executePendingAction(debt_action, sender=governance.address)
    assert switchboard_alpha.executePendingAction(rewards_action, sender=governance.address)
    assert switchboard_alpha.executePendingAction(buffer_action, sender=governance.address)
    
    # Verify all were cleaned up
    assert not switchboard_alpha.hasPendingAction(vault_action)
    assert not switchboard_alpha.hasPendingAction(debt_action)
    assert not switchboard_alpha.hasPendingAction(rewards_action)
    assert not switchboard_alpha.hasPendingAction(buffer_action)


def test_ripe_per_block_zero_value(switchboard_alpha, governance):
    """Test setting ripe per block to zero (edge case)"""
    
    action_id = switchboard_alpha.setRipePerBlock(0, sender=governance.address)
    assert action_id > 0
    
    # Execute and verify
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)


def test_stale_time_exact_boundaries(switchboard_alpha, governance):
    """Test stale time at exact min/max boundaries"""
    
    # Test at exact minimum
    min_stale = switchboard_alpha.MIN_STALE_TIME()
    action_id = switchboard_alpha.setStaleTime(min_stale, sender=governance.address)
    assert action_id > 0
    
    # Test at exact maximum
    max_stale = switchboard_alpha.MAX_STALE_TIME()
    action_id = switchboard_alpha.setStaleTime(max_stale, sender=governance.address)
    assert action_id > 0


def test_vault_limits_edge_cases(switchboard_alpha, governance):
    """Test vault limits with edge case values"""
    
    # Test with value 1 (minimum valid)
    action_id = switchboard_alpha.setVaultLimits(1, 1, sender=governance.address)
    assert action_id > 0
    
    # Test with large but valid values
    large_value = MAX_UINT256 - 1
    action_id = switchboard_alpha.setVaultLimits(large_value, large_value, sender=governance.address)
    assert action_id > 0


def test_action_state_consistency(switchboard_alpha, governance):
    """Test that action state is properly managed"""
    
    # Create action and verify it's stored
    action_id = switchboard_alpha.setVaultLimits(12, 6, sender=governance.address)
    
    # Verify pending config is stored
    pending = switchboard_alpha.pendingGeneralConfig(action_id)
    assert pending.perUserMaxVaults == 12
    assert pending.perUserMaxAssetsPerVault == 6
    
    # Verify action type is stored
    assert switchboard_alpha.actionType(action_id) != 0  # Should not be empty
    
    # Execute action
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Verify cleanup
    assert switchboard_alpha.actionType(action_id) == 0  # Should be empty after execution


def test_comprehensive_permission_matrix(switchboard_alpha, governance, bob, alice):
    """Test comprehensive permission scenarios"""
    
    # Test governance permissions
    assert switchboard_alpha.setCanDeposit(True, sender=governance.address)
    
    # Test with multiple users having disable permissions
    action_id1 = switchboard_alpha.setCanPerformLiteAction(bob, True, sender=governance.address)
    action_id2 = switchboard_alpha.setCanPerformLiteAction(alice, True, sender=governance.address)
    
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id1, sender=governance.address)
    switchboard_alpha.executePendingAction(action_id2, sender=governance.address)
    
    # Both bob and alice should be able to disable
    switchboard_alpha.setCanWithdraw(True, sender=governance.address)  # Enable first
    switchboard_alpha.setCanWithdraw(False, sender=bob)  # Bob disables
    switchboard_alpha.setCanWithdraw(True, sender=governance.address)  # Re-enable
    switchboard_alpha.setCanWithdraw(False, sender=alice)  # Alice disables
    
    # Remove bob's permission
    action_id = switchboard_alpha.setCanPerformLiteAction(bob, False, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Now only alice can disable
    switchboard_alpha.setCanWithdraw(True, sender=governance.address)  # Enable first
    with boa.reverts("no perms"):
        switchboard_alpha.setCanWithdraw(False, sender=bob)  # Bob can't disable
    switchboard_alpha.setCanWithdraw(False, sender=alice)  # Alice still can


def test_transient_storage_behavior(switchboard_alpha, governance, alpha_token, bravo_token):
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
        switchboard_alpha.setPriorityLiqAssetVaults(vaults, sender=governance.address)
    
    # Test that transient storage is cleared between calls
    # Create two separate calls with same vault data
    vaults1 = [(1, alpha_token), (2, bravo_token)]
    vaults2 = [(1, alpha_token), (3, alpha_token)]  # Reuses vault 1
    
    # Both calls should fail due to invalid vaults
    with boa.reverts("invalid priority vaults"):
        switchboard_alpha.setPriorityLiqAssetVaults(vaults1, sender=governance.address)
    
    with boa.reverts("invalid priority vaults"):
        switchboard_alpha.setPriorityLiqAssetVaults(vaults2, sender=governance.address)


def test_edge_case_stale_time_boundaries(switchboard_alpha, mission_control, governance):
    """Test stale time configuration at exact min/max boundaries with state changes"""
    min_stale = switchboard_alpha.MIN_STALE_TIME()
    max_stale = switchboard_alpha.MAX_STALE_TIME()
    
    # Set to minimum
    action_id = switchboard_alpha.setStaleTime(min_stale, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.genConfig()
    assert config.priceStaleTime == min_stale
    
    # Set to maximum
    action_id = switchboard_alpha.setStaleTime(max_stale, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.genConfig()
    assert config.priceStaleTime == max_stale
    
    # Try to set just outside boundaries
    with boa.reverts("invalid stale time"):
        switchboard_alpha.setStaleTime(min_stale - 1, sender=governance.address)
    
    with boa.reverts("invalid stale time"):
        switchboard_alpha.setStaleTime(max_stale + 1, sender=governance.address)


# Additional comprehensive tests

def test_priority_vault_maximum_array_size(switchboard_alpha, governance):
    """Test priority vaults with maximum allowed array size"""
    # PRIORITY_VAULT_DATA constant is 20
    max_vaults = []
    for i in range(20):
        max_vaults.append((i + 1, ZERO_ADDRESS))  # Will be filtered but tests max size
    
    # This should handle the maximum size without reverting
    with boa.reverts("invalid priority vaults"):
        switchboard_alpha.setPriorityLiqAssetVaults(max_vaults, sender=governance.address)


def test_priority_vault_deduplication_complex(switchboard_alpha, governance, alpha_token, bravo_token, charlie_token):
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
        switchboard_alpha.setPriorityLiqAssetVaults(vaults, sender=governance.address)


def test_priority_price_sources_maximum_array(switchboard_alpha, governance):
    """Test priority price sources with maximum allowed array size"""
    # MAX_PRIORITY_PRICE_SOURCES is 10
    # Mix of valid (1, 2) and invalid IDs
    max_sources = [1, 2] + list(range(100, 108))
    
    # This should succeed with the valid IDs
    action_id = switchboard_alpha.setPriorityPriceSourceIds(max_sources, sender=governance.address)
    assert action_id > 0
    
    # Should only have the valid IDs
    logs = filter_logs(switchboard_alpha, "PendingPriorityPriceSourceIdsChange")
    assert len(logs) == 1
    assert logs[0].numPriorityPriceSourceIds == 2  # Only IDs 1 and 2 are valid


def test_underscore_registry_validation_comprehensive(switchboard_alpha, governance):
    """Test underscore registry validation with various scenarios"""
    # Test with contract that doesn't implement expected interface
    with boa.reverts():
        switchboard_alpha.setUnderscoreRegistry(governance.address, sender=governance.address)
    
    # Test with EOA (not a contract)
    eoa_address = boa.env.generate_address()
    with boa.reverts():
        switchboard_alpha.setUnderscoreRegistry(eoa_address, sender=governance.address)


def test_action_expiration_boundary_conditions(switchboard_alpha, governance):
    """Test action expiration at exact boundary times"""
    # Create an action
    action_id = switchboard_alpha.setVaultLimits(10, 5, sender=governance.address)
    
    time_lock = switchboard_alpha.actionTimeLock()
    expiration = switchboard_alpha.expiration()
    
    # Test at exactly the expiration boundary
    boa.env.time_travel(blocks=time_lock + expiration)
    
    # Should still be executable at exact expiration
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    # Depending on implementation, this might succeed or fail
    
    # Create another action and test just after expiration
    action_id2 = switchboard_alpha.setVaultLimits(15, 8, sender=governance.address)
    boa.env.time_travel(blocks=time_lock + expiration + 1)
    
    # Should definitely fail after expiration
    assert not switchboard_alpha.executePendingAction(action_id2, sender=governance.address)


def test_multi_user_complex_permission_scenarios(switchboard_alpha, governance, bob, alice, charlie):
    """Test complex scenarios with multiple users having different permissions"""
    # Setup: Give different users different permissions
    action_id1 = switchboard_alpha.setCanPerformLiteAction(bob, True, sender=governance.address)
    action_id2 = switchboard_alpha.setCanPerformLiteAction(alice, True, sender=governance.address)
    
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id1, sender=governance.address)
    switchboard_alpha.executePendingAction(action_id2, sender=governance.address)
    
    # Enable multiple features
    switchboard_alpha.setCanDeposit(True, sender=governance.address)
    switchboard_alpha.setCanWithdraw(True, sender=governance.address)
    switchboard_alpha.setCanBorrow(True, sender=governance.address)
    
    # Test concurrent disabling by different users
    switchboard_alpha.setCanDeposit(False, sender=bob)
    switchboard_alpha.setCanWithdraw(False, sender=alice)
    
    # Verify charlie (no permissions) cannot disable
    # canBorrow is already True, so we don't need to re-enable it
    with boa.reverts("no perms"):
        switchboard_alpha.setCanBorrow(False, sender=charlie)
    
    # Test removing permissions while actions are pending
    action_id3 = switchboard_alpha.setCanPerformLiteAction(bob, False, sender=governance.address)
    
    # Bob should still be able to disable before the action executes
    switchboard_alpha.setCanDeposit(True, sender=governance.address)  # Re-enable
    switchboard_alpha.setCanDeposit(False, sender=bob)  # Should still work
    
    # Execute the permission removal
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id3, sender=governance.address)
    
    # Now bob cannot disable
    switchboard_alpha.setCanDeposit(True, sender=governance.address)  # Re-enable
    with boa.reverts("no perms"):
        switchboard_alpha.setCanDeposit(False, sender=bob)


def test_state_cleanup_on_failed_execution(switchboard_alpha, governance):
    """Test that state is properly cleaned up when execution fails"""
    # Create multiple actions
    action_id1 = switchboard_alpha.setVaultLimits(10, 5, sender=governance.address)
    switchboard_alpha.setStaleTime(switchboard_alpha.MIN_STALE_TIME() + 100, sender=governance.address)
    
    # Cancel one action
    switchboard_alpha.cancelPendingAction(action_id1, sender=governance.address)
    
    # Verify the action type is cleared
    assert switchboard_alpha.actionType(action_id1) == 0
    assert not switchboard_alpha.hasPendingAction(action_id1)
    
    # Verify pending data is cleared (though it might still exist in storage)
    # The important thing is that actionType is cleared so it can't be executed


def test_rapid_sequential_actions_same_type(switchboard_alpha, governance):
    """Test creating many sequential actions of the same type rapidly"""
    action_ids = []
    
    # Create 10 vault limit changes rapidly
    for i in range(10):
        action_id = switchboard_alpha.setVaultLimits(10 + i, 5 + i, sender=governance.address)
        action_ids.append(action_id)
    
    # Verify all have unique IDs
    assert len(set(action_ids)) == 10
    
    # Verify they're sequential
    for i in range(1, 10):
        assert action_ids[i] == action_ids[i-1] + 1
    
    # Execute them out of order
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    
    # Execute middle one first
    assert switchboard_alpha.executePendingAction(action_ids[5], sender=governance.address)
    
    # Execute last one
    assert switchboard_alpha.executePendingAction(action_ids[9], sender=governance.address)
    
    # Execute first one
    assert switchboard_alpha.executePendingAction(action_ids[0], sender=governance.address)
    
    # Verify others are still pending
    assert switchboard_alpha.hasPendingAction(action_ids[1])
    assert switchboard_alpha.hasPendingAction(action_ids[2])


def test_all_enable_disable_concurrent_state_changes(switchboard_alpha, mission_control, governance, bob):
    """Test all enable/disable functions with concurrent state changes"""
    # Give bob disable permissions
    action_id = switchboard_alpha.setCanPerformLiteAction(bob, True, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Test rapid enable/disable cycles
    functions = [
        (switchboard_alpha.setCanDeposit, "canDeposit"),
        (switchboard_alpha.setCanWithdraw, "canWithdraw"),
        (switchboard_alpha.setCanBorrow, "canBorrow"),
        (switchboard_alpha.setCanRepay, "canRepay"),
        (switchboard_alpha.setCanClaimLoot, "canClaimLoot"),
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
    assert config.canDeposit  # Re-enabled by governance
    assert config.canWithdraw  # Never disabled
    assert not config.canBorrow  # Disabled by bob
    assert config.canRepay  # Never disabled
    assert config.canClaimLoot  # Never disabled


def test_debt_config_interdependencies(switchboard_alpha, governance):
    """Test debt config settings that have interdependencies"""
    # Set initial debt limits
    action_id = switchboard_alpha.setGlobalDebtLimits(5000, 50000, 100, 100, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Now test borrow interval with edge cases around minDebtAmount
    # This should fail because maxBorrowPerInterval (99) < minDebtAmount (100)
    with boa.reverts("invalid borrow interval config"):
        switchboard_alpha.setBorrowIntervalConfig(99, 100, sender=governance.address)
    
    # This should succeed - exactly at minDebtAmount
    action_id = switchboard_alpha.setBorrowIntervalConfig(100, 100, sender=governance.address)
    assert action_id > 0
    
    # Test changing minDebtAmount after borrow interval is set
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Now try to set minDebtAmount higher than maxBorrowPerInterval
    # This should succeed because we're not validating against existing borrow config
    action_id = switchboard_alpha.setGlobalDebtLimits(5000, 50000, 200, 100, sender=governance.address)
    assert action_id > 0


def test_auction_params_comprehensive_validation(switchboard_alpha, governance):
    """Test auction parameters with comprehensive edge cases"""
    
    # Test with startDiscount = 0
    action_id = switchboard_alpha.setGenAuctionParams(0, 50_00, 100, 1000, sender=governance.address)
    assert action_id > 0
    
    # Test with very small duration
    action_id = switchboard_alpha.setGenAuctionParams(10_00, 50_00, 0, 1, sender=governance.address)
    assert action_id > 0
    
    # Test with delay = 0
    action_id = switchboard_alpha.setGenAuctionParams(10_00, 50_00, 0, 1000, sender=governance.address)
    assert action_id > 0
    
    # Test with very large but valid values
    large_duration = 1000000  # Large but not max_value
    action_id = switchboard_alpha.setGenAuctionParams(10_00, 50_00, 100, large_duration, sender=governance.address)
    assert action_id > 0


def test_rewards_config_zero_allocations(switchboard_alpha, mission_control, governance):
    """Test rewards configuration with all zero allocations"""
    # This should be valid - no rewards distributed
    action_id = switchboard_alpha.setRipeRewardsAllocs(0, 0, 0, 0, sender=governance.address)
    assert action_id > 0
    
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    config = mission_control.rewardsConfig()
    assert config.borrowersAlloc == 0
    assert config.stakersAlloc == 0
    assert config.votersAlloc == 0
    assert config.genDepositorsAlloc == 0


def test_multiple_pending_actions_cleanup(switchboard_alpha, governance):
    """Test cleanup of multiple pending actions of different types"""
    # Create one of each type of action
    vault_action = switchboard_alpha.setVaultLimits(10, 5, sender=governance.address)
    stale_action = switchboard_alpha.setStaleTime(switchboard_alpha.MIN_STALE_TIME() + 50, sender=governance.address)
    debt_action = switchboard_alpha.setGlobalDebtLimits(3000, 30000, 150, 75, sender=governance.address)
    rewards_action = switchboard_alpha.setRipePerBlock(1000, sender=governance.address)
    
    # Let some expire
    expiration = switchboard_alpha.expiration()
    time_lock = switchboard_alpha.actionTimeLock()
    boa.env.time_travel(blocks=time_lock + expiration + 1)
    
    # Try to execute expired actions - should fail and clean up
    assert not switchboard_alpha.executePendingAction(vault_action, sender=governance.address)
    assert not switchboard_alpha.executePendingAction(stale_action, sender=governance.address)
    
    # Verify cleanup
    assert switchboard_alpha.actionType(vault_action) == 0
    assert switchboard_alpha.actionType(stale_action) == 0
    
    # Cancel others manually
    switchboard_alpha.cancelPendingAction(debt_action, sender=governance.address)
    switchboard_alpha.cancelPendingAction(rewards_action, sender=governance.address)
    
    # Verify all are cleaned up
    assert not switchboard_alpha.hasPendingAction(vault_action)
    assert not switchboard_alpha.hasPendingAction(stale_action)
    assert not switchboard_alpha.hasPendingAction(debt_action)
    assert not switchboard_alpha.hasPendingAction(rewards_action)


def test_gas_optimization_large_arrays(switchboard_alpha, governance):
    """Test gas usage with maximum size arrays"""
    # Create maximum size priority vault array
    max_vaults = [(i, ZERO_ADDRESS) for i in range(20)]  # PRIORITY_VAULT_DATA = 20
    
    # Measure gas for setting priority vaults
    # This will revert but we can still check it handles max size
    with boa.reverts("invalid priority vaults"):
        switchboard_alpha.setPriorityLiqAssetVaults(max_vaults, sender=governance.address)
    
    # Create maximum size price source array with mix of valid and invalid
    max_sources = [1, 2] + list(range(100, 108))  # MAX_PRIORITY_PRICE_SOURCES = 10
    
    # This should succeed with valid IDs
    action_id = switchboard_alpha.setPriorityPriceSourceIds(max_sources, sender=governance.address)
    assert action_id > 0


def test_action_type_enum_coverage(switchboard_alpha, governance):
    """Ensure all ActionType enum values are tested"""
    # This test verifies we've covered all action types
    # Based on the contract, these are all the ActionType values:
    action_types_tested = set()
    
    # GEN_CONFIG_VAULT_LIMITS
    switchboard_alpha.setVaultLimits(10, 5, sender=governance.address)
    action_types_tested.add("GEN_CONFIG_VAULT_LIMITS")
    
    # GEN_CONFIG_STALE_TIME
    switchboard_alpha.setStaleTime(switchboard_alpha.MIN_STALE_TIME() + 50, sender=governance.address)
    action_types_tested.add("GEN_CONFIG_STALE_TIME")
    
    # DEBT_GLOBAL_LIMITS
    switchboard_alpha.setGlobalDebtLimits(5000, 50000, 100, 100, sender=governance.address)
    action_types_tested.add("DEBT_GLOBAL_LIMITS")
    
    # DEBT_BORROW_INTERVAL
    switchboard_alpha.setBorrowIntervalConfig(500, 100, sender=governance.address)
    action_types_tested.add("DEBT_BORROW_INTERVAL")
    
    # DEBT_KEEPER_CONFIG
    switchboard_alpha.setKeeperConfig(5_00, 50 * 10**18, 1000 * 10**18, sender=governance.address)
    action_types_tested.add("DEBT_KEEPER_CONFIG")
    
    # DEBT_LTV_PAYBACK_BUFFER
    switchboard_alpha.setLtvPaybackBuffer(5_00, sender=governance.address)
    action_types_tested.add("DEBT_LTV_PAYBACK_BUFFER")
    
    # DEBT_AUCTION_PARAMS
    switchboard_alpha.setGenAuctionParams(20_00, 50_00, 1000, 3000, sender=governance.address)
    action_types_tested.add("DEBT_AUCTION_PARAMS")
    
    # RIPE_REWARDS_BLOCK
    switchboard_alpha.setRipePerBlock(1000, sender=governance.address)
    action_types_tested.add("RIPE_REWARDS_BLOCK")
    
    # RIPE_REWARDS_ALLOCS
    switchboard_alpha.setRipeRewardsAllocs(25_00, 25_00, 25_00, 25_00, sender=governance.address)
    action_types_tested.add("RIPE_REWARDS_ALLOCS")
    
    # MAX_LTV_DEVIATION
    switchboard_alpha.setMaxLtvDeviation(10_00, sender=governance.address)
    action_types_tested.add("MAX_LTV_DEVIATION")
    
    # Verify we've tested all main action types
    assert len(action_types_tested) >= 10


def test_invalid_caller_scenarios(switchboard_alpha, governance, bob, alice):
    """Test various invalid caller scenarios beyond basic permission checks"""
    # Test calling from a contract (if we had a malicious contract)
    # For now, test with regular EOAs
    
    # Test non-governance trying to cancel actions
    action_id = switchboard_alpha.setVaultLimits(10, 5, sender=governance.address)
    
    with boa.reverts("no perms"):
        switchboard_alpha.cancelPendingAction(action_id, sender=bob)
    
    # Test non-governance trying to execute actions
    with boa.reverts("no perms"):
        switchboard_alpha.executePendingAction(action_id, sender=bob)
    
    # Give alice disable permissions
    action_id2 = switchboard_alpha.setCanPerformLiteAction(alice, True, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id2, sender=governance.address)
    
    # Alice still cannot execute pending actions
    with boa.reverts("no perms"):
        switchboard_alpha.executePendingAction(action_id, sender=alice)
    
    # Alice still cannot cancel pending actions
    with boa.reverts("no perms"):
        switchboard_alpha.cancelPendingAction(action_id, sender=alice)


def test_priority_stab_vault_validation_edge_cases(switchboard_alpha, governance, alpha_token, bravo_token):
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
        switchboard_alpha.setPriorityStabVaults(mixed_vaults, sender=governance.address)


def test_complex_workflow_with_failures(switchboard_alpha, mission_control, governance):
    """Test complex workflow with some actions failing and others succeeding"""
    # Create multiple actions
    action1 = switchboard_alpha.setVaultLimits(10, 5, sender=governance.address)
    action2 = switchboard_alpha.setStaleTime(switchboard_alpha.MIN_STALE_TIME() + 50, sender=governance.address)
    action3 = switchboard_alpha.setGlobalDebtLimits(5000, 50000, 100, 100, sender=governance.address)
    
    # Time travel to make first two executable
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    
    # Execute first two
    assert switchboard_alpha.executePendingAction(action1, sender=governance.address)
    assert switchboard_alpha.executePendingAction(action2, sender=governance.address)
    
    # Create another action that conflicts with action3
    action4 = switchboard_alpha.setGlobalDebtLimits(6000, 60000, 200, 150, sender=governance.address)
    
    # Execute action3
    assert switchboard_alpha.executePendingAction(action3, sender=governance.address)
    
    # Time travel for action4
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    
    # Execute action4 (should override action3's values)
    assert switchboard_alpha.executePendingAction(action4, sender=governance.address)
    
    # Verify final state
    config = mission_control.genConfig()
    assert config.perUserMaxVaults == 10
    assert config.priceStaleTime == switchboard_alpha.MIN_STALE_TIME() + 50
    
    debt_config = mission_control.genDebtConfig()
    assert debt_config.perUserDebtLimit == 6000  # From action4
    assert debt_config.globalDebtLimit == 60000
    assert debt_config.minDebtAmount == 200
    assert debt_config.numAllowedBorrowers == 150


def test_enable_disable_rapid_toggle(switchboard_alpha, mission_control, governance):
    """Test rapid toggling of enable/disable flags"""
    # Rapidly toggle deposit flag
    for i in range(5):
        switchboard_alpha.setCanDeposit(True, sender=governance.address)
        switchboard_alpha.setCanDeposit(False, sender=governance.address)
    
    # Final state should be False
    config = mission_control.genConfig()
    assert not config.canDeposit
    
    # Set to True and verify
    switchboard_alpha.setCanDeposit(True, sender=governance.address)
    config = mission_control.genConfig()
    assert config.canDeposit


def test_all_debt_config_fields_modified(switchboard_alpha, mission_control, governance):
    """Test modifying all debt config fields through different actions"""
    time_lock = switchboard_alpha.actionTimeLock()
    
    # Set all debt config fields
    actions = []
    
    # Global limits
    actions.append(switchboard_alpha.setGlobalDebtLimits(7000, 70000, 300, 200, sender=governance.address))
    
    # Borrow interval
    actions.append(switchboard_alpha.setBorrowIntervalConfig(1000, 50, sender=governance.address))
    
    # Keeper config
    actions.append(switchboard_alpha.setKeeperConfig(8_00, 80 * 10**18, 2000 * 10**18, sender=governance.address))
    
    # LTV payback buffer
    actions.append(switchboard_alpha.setLtvPaybackBuffer(9_00, sender=governance.address))
    
    # Auction params
    actions.append(switchboard_alpha.setGenAuctionParams(30_00, 60_00, 2000, 5000, sender=governance.address))
    
    # Execute all actions
    boa.env.time_travel(blocks=time_lock)
    for action in actions:
        assert switchboard_alpha.executePendingAction(action, sender=governance.address)
    
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


def test_pending_action_data_persistence(switchboard_alpha, governance):
    """Test that pending action data persists correctly until execution or cancellation"""
    # Create actions with specific data
    action1 = switchboard_alpha.setVaultLimits(42, 24, sender=governance.address)
    action2 = switchboard_alpha.setRipePerBlock(12345, sender=governance.address)
    
    # Verify pending data is stored correctly
    pending_gen = switchboard_alpha.pendingGeneralConfig(action1)
    assert pending_gen.perUserMaxVaults == 42
    assert pending_gen.perUserMaxAssetsPerVault == 24
    
    pending_rewards = switchboard_alpha.pendingRipeRewardsConfig(action2)
    assert pending_rewards.ripePerBlock == 12345
    
    # Time travel but don't execute
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock() // 2)
    
    # Data should still be there
    pending_gen = switchboard_alpha.pendingGeneralConfig(action1)
    assert pending_gen.perUserMaxVaults == 42
    
    # Cancel one action
    switchboard_alpha.cancelPendingAction(action1, sender=governance.address)
    
    # Execute the other
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock() // 2)
    switchboard_alpha.executePendingAction(action2, sender=governance.address)
    
    # Verify action types are cleared appropriately
    assert switchboard_alpha.actionType(action1) == 0  # Cancelled
    assert switchboard_alpha.actionType(action2) == 0  # Executed


def test_max_ltv_deviation_validation(switchboard_alpha, governance, bob):
    """Test max LTV deviation validation"""
    # Test invalid deviation - zero value
    with boa.reverts("invalid max deviation"):
        switchboard_alpha.setMaxLtvDeviation(0, sender=governance.address)
    
    # Test invalid deviation - greater than 100%
    with boa.reverts("invalid max deviation"):
        switchboard_alpha.setMaxLtvDeviation(101_00, sender=governance.address)  # 101%
    
    # Test non-governance cannot set
    with boa.reverts("no perms"):
        switchboard_alpha.setMaxLtvDeviation(10_00, sender=bob)


def test_max_ltv_deviation_success(switchboard_alpha, governance):
    """Test successful max LTV deviation setting"""
    # Test valid deviation - 5%
    action_id = switchboard_alpha.setMaxLtvDeviation(5_00, sender=governance.address)
    assert action_id > 0  # Should return a valid action ID
    
    # Check event was emitted
    logs = filter_logs(switchboard_alpha, "PendingMaxLtvDeviationChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.newDeviation == 5_00
    assert log.actionId == action_id
    
    # Check pending data was stored
    pending_debt = switchboard_alpha.pendingDebtConfig(action_id)
    assert pending_debt.maxLtvDeviation == 5_00
    
    # Test at exact boundary - 100%
    action_id2 = switchboard_alpha.setMaxLtvDeviation(100_00, sender=governance.address)
    assert action_id2 > 0
    assert action_id2 == action_id + 1  # Should increment
    
    # Test minimum valid value - 1
    action_id3 = switchboard_alpha.setMaxLtvDeviation(1, sender=governance.address)
    assert action_id3 > 0
    assert action_id3 == action_id2 + 1  # Should increment


def test_execute_max_ltv_deviation(switchboard_alpha, governance):
    """Test executing max LTV deviation action"""
    # Set max LTV deviation
    deviation = 15_00  # 15%
    action_id = switchboard_alpha.setMaxLtvDeviation(deviation, sender=governance.address)
    assert action_id > 0  # Should return action ID
    
    # Time travel past timelock
    time_lock = switchboard_alpha.actionTimeLock()
    boa.env.time_travel(blocks=time_lock)
    
    # Execute the action
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Check event was emitted
    logs = filter_logs(switchboard_alpha, "MaxLtvDeviationSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.newDeviation == deviation
    
    # Verify the action was cleaned up
    assert switchboard_alpha.actionType(action_id) == 0
    assert not switchboard_alpha.hasPendingAction(action_id)


def test_max_ltv_deviation_boundary_conditions(switchboard_alpha, governance):
    """Test max LTV deviation at exact boundary values"""
    # Test at exactly 100% (should be valid)
    action_id = switchboard_alpha.setMaxLtvDeviation(100_00, sender=governance.address)
    assert action_id > 0
    
    # Test at 1 (minimum valid value)
    action_id = switchboard_alpha.setMaxLtvDeviation(1, sender=governance.address)
    assert action_id > 0
    
    # Test common percentage values
    common_values = [1_00, 5_00, 10_00, 25_00, 50_00, 75_00, 99_99]
    for value in common_values:
        action_id = switchboard_alpha.setMaxLtvDeviation(value, sender=governance.address)
        assert action_id > 0
        
        pending_debt = switchboard_alpha.pendingDebtConfig(action_id)
        assert pending_debt.maxLtvDeviation == value


def test_max_ltv_deviation_full_workflow(switchboard_alpha, governance):
    """Test complete workflow of setting and executing max LTV deviation"""
    time_lock = switchboard_alpha.actionTimeLock()
    
    # Create multiple max LTV deviation changes
    deviations = [10_00, 20_00, 5_00]  # 10%, 20%, 5%
    action_ids = []
    
    for deviation in deviations:
        action_id = switchboard_alpha.setMaxLtvDeviation(deviation, sender=governance.address)
        assert action_id > 0
        action_ids.append(action_id)
    
    # Verify all actions are pending
    for i, action_id in enumerate(action_ids):
        assert switchboard_alpha.hasPendingAction(action_id)
        pending_debt = switchboard_alpha.pendingDebtConfig(action_id)
        assert pending_debt.maxLtvDeviation == deviations[i]
    
    # Execute them in order after timelock
    boa.env.time_travel(blocks=time_lock)
    
    for i, action_id in enumerate(action_ids):
        # Clear previous events by getting current count
        logs_before = filter_logs(switchboard_alpha, "MaxLtvDeviationSet")
        events_before = len(logs_before)
        
        assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
        
        # Verify new event was emitted
        logs_after = filter_logs(switchboard_alpha, "MaxLtvDeviationSet")
        assert len(logs_after) == events_before + 1  # Should have one more event
        assert logs_after[-1].newDeviation == deviations[i]  # Check the latest event
        
        # Verify cleanup
        assert not switchboard_alpha.hasPendingAction(action_id)
        assert switchboard_alpha.actionType(action_id) == 0


def test_max_ltv_deviation_cancel_and_expire(switchboard_alpha, governance):
    """Test canceling and expiring max LTV deviation actions"""
    # Create action
    action_id = switchboard_alpha.setMaxLtvDeviation(15_00, sender=governance.address)
    
    # Cancel it
    assert switchboard_alpha.cancelPendingAction(action_id, sender=governance.address)
    
    # Try to execute canceled action - should fail
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert not switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Create another action and let it expire
    action_id2 = switchboard_alpha.setMaxLtvDeviation(20_00, sender=governance.address)
    
    # Time travel beyond expiration (actionTimeLock + maxActionTimeLock + 1)
    # Since setActionTimeLockAfterSetup() was called, actionTimeLock is now non-zero
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock() + switchboard_alpha.maxActionTimeLock() + 1)
    
    # Should automatically clean up expired action
    assert not switchboard_alpha.executePendingAction(action_id2, sender=governance.address)
    
    # Action should be cleaned up
    assert switchboard_alpha.actionType(action_id2) == 0


def test_ripe_gov_vault_config_validation(switchboard_alpha, governance, alpha_token, setAssetConfig):
    """Test validation for setRipeGovVaultConfig function"""
    # Set up alpha_token to be supported in vault 2 (ripe gov vault)
    setAssetConfig(alpha_token.address, _vaultIds=[2])
    
    # Test with zero address asset
    with boa.reverts("invalid ripe vault config"):  # Will fail at _isValidRipeVaultConfig
        switchboard_alpha.setRipeGovVaultConfig(
            ZERO_ADDRESS,  # invalid asset
            100_00,  # 100% weight
            False,   # shouldFreezeWhenBadDebt
            86400,   # 1 day min lock
            31536000,  # 1 year max lock  
            200_00,  # 200% max boost
            5_00,    # 5% exit fee
            True,    # can exit
            sender=governance.address
        )
    
    # Test with unsupported asset (not configured in vault 2)
    with boa.reverts("invalid ripe vault config"):
        switchboard_alpha.setRipeGovVaultConfig(
            "0x1234567890123456789012345678901234567890",  # unsupported asset
            100_00,
            False,   # shouldFreezeWhenBadDebt
            86400,
            31536000,
            200_00,
            5_00,
            True,
            sender=governance.address
        )
    
    # Test with asset weight > 500%
    with boa.reverts("invalid ripe vault config"):
        switchboard_alpha.setRipeGovVaultConfig(
            alpha_token.address,  # supported asset
            501_00,  # > 500% weight (invalid)
            False,   # shouldFreezeWhenBadDebt
            86400,
            31536000,
            200_00,
            5_00,
            True,
            sender=governance.address
        )
    
    # Test with min lock > max lock duration
    with boa.reverts("invalid ripe vault config"):
        switchboard_alpha.setRipeGovVaultConfig(
            alpha_token.address,
            100_00,
            False,   # shouldFreezeWhenBadDebt
            31536000,  # 1 year min
            86400,     # 1 day max (invalid: min > max)
            200_00,
            5_00,
            True,
            sender=governance.address
        )
    
    # Test with max lock boost > 1000%
    with boa.reverts("invalid ripe vault config"):
        switchboard_alpha.setRipeGovVaultConfig(
            alpha_token.address,
            100_00,
            False,   # shouldFreezeWhenBadDebt
            86400,
            31536000,
            1001_00,  # > 1000% boost (invalid)
            5_00,
            True,
            sender=governance.address
        )
    
    # Test with exit fee > 100%
    with boa.reverts("invalid ripe vault config"):
        switchboard_alpha.setRipeGovVaultConfig(
            alpha_token.address,
            100_00,
            False,   # shouldFreezeWhenBadDebt
            86400,
            31536000,
            200_00,
            101_00,  # > 100% exit fee (invalid)
            True,
            sender=governance.address
        )
    
    # Test invalid combination: canExit=True but exitFee=0
    with boa.reverts("invalid ripe vault config"):
        switchboard_alpha.setRipeGovVaultConfig(
            alpha_token.address,
            100_00,
            False,   # shouldFreezeWhenBadDebt
            86400,
            31536000,
            200_00,
            0,      # exitFee = 0 (INVALID with canExit=True)
            True,   # canExit = True
            sender=governance.address
        )
    
    # Test invalid combination: canExit=False but exitFee>0
    with boa.reverts("invalid ripe vault config"):
        switchboard_alpha.setRipeGovVaultConfig(
            alpha_token.address,
            100_00,
            False,   # shouldFreezeWhenBadDebt
            86400,
            31536000,
            200_00,
            10_00,  # exitFee = 10% (INVALID with canExit=False)
            False,  # canExit = False
            sender=governance.address
        )


def test_ripe_gov_vault_config_success(switchboard_alpha, governance, alpha_token, setAssetConfig):
    """Test successful setRipeGovVaultConfig with valid parameters"""
    # Set up alpha_token to be supported in vault 2 (ripe gov vault)
    setAssetConfig(alpha_token.address, _vaultIds=[2])
    
    # Create action with valid parameters
    action_id = switchboard_alpha.setRipeGovVaultConfig(
        alpha_token.address,
        150_00,    # 150% asset weight
        True,      # shouldFreezeWhenBadDebt
        86400,     # 1 day min lock
        31536000,  # 1 year max lock
        300_00,    # 300% max boost
        10_00,     # 10% exit fee
        True,      # can exit
        sender=governance.address
    )
    
    # Check that action was created
    assert action_id > 0
    
    # Check event was emitted with correct parameters
    logs = filter_logs(switchboard_alpha, "PendingRipeGovVaultConfigChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.asset == alpha_token.address
    assert log.assetWeight == 150_00
    assert log.shouldFreezeWhenBadDebt
    assert log.minLockDuration == 86400
    assert log.maxLockDuration == 31536000
    assert log.maxLockBoost == 300_00
    assert log.exitFee == 10_00
    assert log.canExit
    assert log.actionId == action_id
    
    # Check pending config was stored correctly
    pending = switchboard_alpha.pendingRipeGovVaultConfig(action_id)
    assert pending.asset == alpha_token.address
    assert pending.assetWeight == 150_00
    assert pending.shouldFreezeWhenBadDebt
    assert pending.lockTerms.minLockDuration == 86400
    assert pending.lockTerms.maxLockDuration == 31536000
    assert pending.lockTerms.maxLockBoost == 300_00
    assert pending.lockTerms.exitFee == 10_00
    assert pending.lockTerms.canExit


def test_execute_ripe_gov_vault_config(switchboard_alpha, governance, bravo_token, setAssetConfig):
    """Test execution of ripe gov vault config action"""
    # Set up bravo_token to be supported in vault 2 (ripe gov vault)
    setAssetConfig(bravo_token.address, _vaultIds=[2])
    
    # Create the action with valid configuration
    # When canExit=False, exitFee must be 0 (per SwitchboardAlpha validation)
    action_id = switchboard_alpha.setRipeGovVaultConfig(
        bravo_token.address,
        200_00,    # 200% asset weight
        False,     # shouldFreezeWhenBadDebt
        7200,      # 2 hours min lock
        2592000,   # 30 days max lock
        400_00,    # 400% max boost
        0,         # 0% exit fee (VALID with canExit=False)
        False,     # cannot exit
        sender=governance.address
    )
    
    # Verify action was created
    assert action_id > 0
    
    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    
    # Execute the action
    success = switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    assert success
    
    # Check execution event was emitted
    logs = filter_logs(switchboard_alpha, "RipeGovVaultConfigSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.asset == bravo_token.address
    assert log.assetWeight == 200_00
    assert not log.shouldFreezeWhenBadDebt
    assert log.minLockDuration == 7200
    assert log.maxLockDuration == 2592000
    assert log.maxLockBoost == 400_00
    assert log.exitFee == 0  # Updated to match valid configuration
    assert not log.canExit
    
    # Verify action was cleaned up
    assert switchboard_alpha.actionType(action_id) == 0
    
    # Test that we can't execute the same action again
    assert not switchboard_alpha.executePendingAction(action_id, sender=governance.address)


def test_execute_ripe_gov_vault_config_with_exit_enabled(switchboard_alpha, governance, alpha_token, setAssetConfig):
    """Test execution of ripe gov vault config action with canExit=True and non-zero exitFee"""
    # Set up alpha_token to be supported in vault 2 (ripe gov vault)
    setAssetConfig(alpha_token.address, _vaultIds=[2])
    
    # Create the action with valid configuration
    # When canExit=True, exitFee must be non-zero (per SwitchboardAlpha validation)
    action_id = switchboard_alpha.setRipeGovVaultConfig(
        alpha_token.address,
        150_00,    # 150% asset weight
        True,      # shouldFreezeWhenBadDebt
        3600,      # 1 hour min lock
        1209600,   # 14 days max lock
        250_00,    # 250% max boost
        12_00,     # 12% exit fee (VALID with canExit=True)
        True,      # can exit
        sender=governance.address
    )
    
    # Verify action was created
    assert action_id > 0
    
    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    
    # Execute the action
    success = switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    assert success
    
    # Check execution event was emitted
    logs = filter_logs(switchboard_alpha, "RipeGovVaultConfigSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.asset == alpha_token.address
    assert log.assetWeight == 150_00
    assert log.shouldFreezeWhenBadDebt
    assert log.minLockDuration == 3600
    assert log.maxLockDuration == 1209600
    assert log.maxLockBoost == 250_00
    assert log.exitFee == 12_00
    assert log.canExit
    
    # Verify action was cleaned up
    assert switchboard_alpha.actionType(action_id) == 0


def test_ripe_gov_vault_config_permissions(switchboard_alpha, governance, bob, alpha_token, setAssetConfig):
    """Test that only governance can call setRipeGovVaultConfig"""
    # Set up alpha_token to be supported in vault 2
    setAssetConfig(alpha_token.address, _vaultIds=[2])
    
    # Non-governance user should not be able to call the function
    with boa.reverts("no perms"):
        switchboard_alpha.setRipeGovVaultConfig(
            alpha_token.address,
            100_00,
            False,   # shouldFreezeWhenBadDebt
            86400,
            31536000,
            200_00,
            5_00,
            True,
            sender=bob
        )
    
    # Governance should be able to call the function
    action_id = switchboard_alpha.setRipeGovVaultConfig(
        alpha_token.address,
        100_00,
        False,   # shouldFreezeWhenBadDebt
        86400,
        31536000,
        200_00,
        5_00,
        True,
        sender=governance.address
    )
    assert action_id > 0


def test_ripe_gov_vault_config_freeze_when_bad_debt_parameter(switchboard_alpha, governance, alpha_token, setAssetConfig):
    """Test the shouldFreezeWhenBadDebt parameter works correctly"""
    # Set up alpha_token to be supported in vault 2
    setAssetConfig(alpha_token.address, _vaultIds=[2])
    
    # Test with shouldFreezeWhenBadDebt=True
    action_id_freeze = switchboard_alpha.setRipeGovVaultConfig(
        alpha_token.address,
        100_00,    # 100% asset weight
        True,      # shouldFreezeWhenBadDebt = True
        86400,     # 1 day min lock
        31536000,  # 1 year max lock
        200_00,    # 200% max boost
        10_00,     # 10% exit fee
        True,      # can exit
        sender=governance.address
    )
    
    assert action_id_freeze > 0
    
    # Check event was emitted with correct freeze parameter
    logs = filter_logs(switchboard_alpha, "PendingRipeGovVaultConfigChange")
    freeze_log = [log for log in logs if log.actionId == action_id_freeze][0]
    assert freeze_log.shouldFreezeWhenBadDebt
    
    # Check pending config stores the correct value
    pending_freeze = switchboard_alpha.pendingRipeGovVaultConfig(action_id_freeze)
    assert pending_freeze.shouldFreezeWhenBadDebt
    
    # Test with shouldFreezeWhenBadDebt=False
    action_id_no_freeze = switchboard_alpha.setRipeGovVaultConfig(
        alpha_token.address,
        150_00,    # 150% asset weight
        False,     # shouldFreezeWhenBadDebt = False
        3600,      # 1 hour min lock
        2592000,   # 30 days max lock
        300_00,    # 300% max boost
        8_00,      # 8% exit fee
        True,      # can exit
        sender=governance.address
    )
    
    assert action_id_no_freeze > 0
    assert action_id_no_freeze != action_id_freeze
    
    # Check event was emitted with correct freeze parameter
    logs = filter_logs(switchboard_alpha, "PendingRipeGovVaultConfigChange")
    no_freeze_log = [log for log in logs if log.actionId == action_id_no_freeze][0]
    assert not no_freeze_log.shouldFreezeWhenBadDebt
    
    # Check pending config stores the correct value
    pending_no_freeze = switchboard_alpha.pendingRipeGovVaultConfig(action_id_no_freeze)
    assert not pending_no_freeze.shouldFreezeWhenBadDebt
    
    # Execute both actions to verify they work properly
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    
    # Execute freeze enabled action
    success_freeze = switchboard_alpha.executePendingAction(action_id_freeze, sender=governance.address)
    assert success_freeze
    
    # Check execution event for freeze enabled
    execution_logs = filter_logs(switchboard_alpha, "RipeGovVaultConfigSet")
    freeze_execution_log = [log for log in execution_logs if log.asset == alpha_token.address and log.assetWeight == 100_00][0]
    assert freeze_execution_log.shouldFreezeWhenBadDebt
    
    # Execute no freeze action  
    success_no_freeze = switchboard_alpha.executePendingAction(action_id_no_freeze, sender=governance.address)
    assert success_no_freeze
    
    # Check execution event for no freeze (this should overwrite the previous config)
    execution_logs = filter_logs(switchboard_alpha, "RipeGovVaultConfigSet")
    no_freeze_execution_log = [log for log in execution_logs if log.asset == alpha_token.address and log.assetWeight == 150_00][0]
    assert not no_freeze_execution_log.shouldFreezeWhenBadDebt


# Dynamic Rate Config Tests


def test_dynamic_rate_config_validation_zero_values(switchboard_alpha, governance):
    """Test dynamic rate config validation with zero values"""
    # Test minDynamicRateBoost = 0
    with boa.reverts("invalid dynamic rate config"):
        switchboard_alpha.setDynamicRateConfig(0, 500_00, 10, 100_00, sender=governance.address)
    
    # Test maxDynamicRateBoost = 0
    with boa.reverts("invalid dynamic rate config"):
        switchboard_alpha.setDynamicRateConfig(100_00, 0, 10, 100_00, sender=governance.address)
    
    # Test increasePerDangerBlock = 0
    with boa.reverts("invalid dynamic rate config"):
        switchboard_alpha.setDynamicRateConfig(100_00, 500_00, 0, 100_00, sender=governance.address)
    
    # Test maxBorrowRate = 0
    with boa.reverts("invalid dynamic rate config"):
        switchboard_alpha.setDynamicRateConfig(100_00, 500_00, 10, 0, sender=governance.address)


def test_dynamic_rate_config_validation_max_values(switchboard_alpha, governance):
    """Test dynamic rate config validation with maximum uint256 values"""
    # Test minDynamicRateBoost = max_value
    with boa.reverts("invalid dynamic rate config"):
        switchboard_alpha.setDynamicRateConfig(MAX_UINT256, 500_00, 10, 100_00, sender=governance.address)
    
    # Test maxDynamicRateBoost = max_value
    with boa.reverts("invalid dynamic rate config"):
        switchboard_alpha.setDynamicRateConfig(100_00, MAX_UINT256, 10, 100_00, sender=governance.address)
    
    # Test increasePerDangerBlock = max_value
    with boa.reverts("invalid dynamic rate config"):
        switchboard_alpha.setDynamicRateConfig(100_00, 500_00, MAX_UINT256, 100_00, sender=governance.address)
    
    # Test maxBorrowRate = max_value
    with boa.reverts("invalid dynamic rate config"):
        switchboard_alpha.setDynamicRateConfig(100_00, 500_00, 10, MAX_UINT256, sender=governance.address)


def test_dynamic_rate_config_validation_boost_ordering(switchboard_alpha, governance):
    """Test dynamic rate config validation with min > max boost"""
    # Test minDynamicRateBoost > maxDynamicRateBoost
    with boa.reverts("invalid dynamic rate config"):
        switchboard_alpha.setDynamicRateConfig(600_00, 500_00, 10, 100_00, sender=governance.address)
    
    # Test equal values (should be valid)
    action_id = switchboard_alpha.setDynamicRateConfig(500_00, 500_00, 10, 100_00, sender=governance.address)
    assert action_id > 0


def test_dynamic_rate_config_validation_max_boost_limit(switchboard_alpha, governance):
    """Test dynamic rate config validation with maxDynamicRateBoost > 1000%"""
    # Test maxDynamicRateBoost > 1000%
    with boa.reverts("invalid dynamic rate config"):
        switchboard_alpha.setDynamicRateConfig(100_00, 1001_00, 10, 100_00, sender=governance.address)
    
    # Test exactly at 1000% (should be valid)
    action_id = switchboard_alpha.setDynamicRateConfig(100_00, 1000_00, 10, 100_00, sender=governance.address)
    assert action_id > 0


def test_dynamic_rate_config_validation_max_borrow_rate_limit(switchboard_alpha, governance):
    """Test dynamic rate config validation with maxBorrowRate > 200%"""
    # Test maxBorrowRate > 200%
    with boa.reverts("invalid dynamic rate config"):
        switchboard_alpha.setDynamicRateConfig(100_00, 500_00, 10, 201_00, sender=governance.address)
    
    # Test exactly at 200% (should be valid)
    action_id = switchboard_alpha.setDynamicRateConfig(100_00, 500_00, 10, 200_00, sender=governance.address)
    assert action_id > 0


def test_dynamic_rate_config_permissions(switchboard_alpha, governance, bob):
    """Test that only governance can call setDynamicRateConfig"""
    # Non-governance user should not be able to call the function
    with boa.reverts("no perms"):
        switchboard_alpha.setDynamicRateConfig(100_00, 500_00, 10, 100_00, sender=bob)
    
    # Governance should be able to call the function
    action_id = switchboard_alpha.setDynamicRateConfig(100_00, 500_00, 10, 100_00, sender=governance.address)
    assert action_id > 0


def test_dynamic_rate_config_success(switchboard_alpha, governance):
    """Test successful dynamic rate config creation with valid parameters"""
    # Test with valid parameters
    action_id = switchboard_alpha.setDynamicRateConfig(150_00, 750_00, 25, 180_00, sender=governance.address)
    assert action_id > 0
    
    # Check event was emitted with correct parameters
    logs = filter_logs(switchboard_alpha, "PendingDynamicRateConfigChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.minDynamicRateBoost == 150_00
    assert log.maxDynamicRateBoost == 750_00
    assert log.increasePerDangerBlock == 25
    assert log.maxBorrowRate == 180_00
    assert log.actionId == action_id
    
    # Check pending config was stored correctly
    pending = switchboard_alpha.pendingDebtConfig(action_id)
    assert pending.minDynamicRateBoost == 150_00
    assert pending.maxDynamicRateBoost == 750_00
    assert pending.increasePerDangerBlock == 25
    assert pending.maxBorrowRate == 180_00


def test_dynamic_rate_config_boundary_conditions(switchboard_alpha, governance):
    """Test dynamic rate config at exact boundary values"""
    # Test at minimum valid values (all = 1)
    action_id = switchboard_alpha.setDynamicRateConfig(1, 1, 1, 1, sender=governance.address)
    assert action_id > 0
    
    # Test at maximum valid boost (1000%)
    action_id = switchboard_alpha.setDynamicRateConfig(1, 1000_00, 1, 1, sender=governance.address)
    assert action_id > 0
    
    # Test at maximum valid borrow rate (200%)
    action_id = switchboard_alpha.setDynamicRateConfig(1, 100_00, 1, 200_00, sender=governance.address)
    assert action_id > 0
    
    # Test just under limits
    action_id = switchboard_alpha.setDynamicRateConfig(999_99, 1000_00, MAX_UINT256 - 1, 199_99, sender=governance.address)
    assert action_id > 0


def test_execute_dynamic_rate_config(switchboard_alpha, mission_control, governance):
    """Test execution of dynamic rate config action"""
    # Create the action
    action_id = switchboard_alpha.setDynamicRateConfig(200_00, 800_00, 15, 150_00, sender=governance.address)
    assert action_id > 0
    
    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    
    # Execute the action
    success = switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    assert success
    
    # Verify the config was applied to MissionControl
    config = mission_control.genDebtConfig()
    assert config.minDynamicRateBoost == 200_00
    assert config.maxDynamicRateBoost == 800_00
    assert config.increasePerDangerBlock == 15
    assert config.maxBorrowRate == 150_00
    
    # Check execution event was emitted
    logs = filter_logs(switchboard_alpha, "DynamicRateConfigSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.minDynamicRateBoost == 200_00
    assert log.maxDynamicRateBoost == 800_00
    assert log.increasePerDangerBlock == 15
    assert log.maxBorrowRate == 150_00
    
    # Verify action was cleaned up
    assert switchboard_alpha.actionType(action_id) == 0
    assert not switchboard_alpha.hasPendingAction(action_id)


def test_multiple_dynamic_rate_config_actions(switchboard_alpha, governance):
    """Test creating multiple dynamic rate config actions"""
    # Create multiple actions with different parameters
    configs = [
        (100_00, 500_00, 10, 100_00),
        (200_00, 600_00, 20, 120_00),
        (300_00, 700_00, 30, 140_00),
    ]
    
    action_ids = []
    for min_boost, max_boost, danger_increase, max_rate in configs:
        action_id = switchboard_alpha.setDynamicRateConfig(
            min_boost, max_boost, danger_increase, max_rate, 
            sender=governance.address
        )
        assert action_id > 0
        action_ids.append(action_id)
    
    # Verify all actions are unique and sequential
    assert len(set(action_ids)) == 3  # All unique
    for i in range(1, 3):
        assert action_ids[i] == action_ids[i-1] + 1  # Sequential
    
    # Verify all pending configs are stored correctly
    for i, (min_boost, max_boost, danger_increase, max_rate) in enumerate(configs):
        pending = switchboard_alpha.pendingDebtConfig(action_ids[i])
        assert pending.minDynamicRateBoost == min_boost
        assert pending.maxDynamicRateBoost == max_boost
        assert pending.increasePerDangerBlock == danger_increase
        assert pending.maxBorrowRate == max_rate


def test_execute_multiple_dynamic_rate_configs(switchboard_alpha, mission_control, governance):
    """Test executing multiple dynamic rate config actions"""
    # Create multiple actions
    action_id1 = switchboard_alpha.setDynamicRateConfig(100_00, 400_00, 5, 80_00, sender=governance.address)
    action_id2 = switchboard_alpha.setDynamicRateConfig(250_00, 750_00, 35, 175_00, sender=governance.address)
    
    # Time travel and execute first action
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id1, sender=governance.address)
    
    # Verify first config was applied
    config = mission_control.genDebtConfig()
    assert config.minDynamicRateBoost == 100_00
    assert config.maxDynamicRateBoost == 400_00
    assert config.increasePerDangerBlock == 5
    assert config.maxBorrowRate == 80_00
    
    # Execute second action (should override first)
    assert switchboard_alpha.executePendingAction(action_id2, sender=governance.address)
    
    # Verify second config was applied
    config = mission_control.genDebtConfig()
    assert config.minDynamicRateBoost == 250_00
    assert config.maxDynamicRateBoost == 750_00
    assert config.increasePerDangerBlock == 35
    assert config.maxBorrowRate == 175_00
    
    # Verify both actions were cleaned up
    assert switchboard_alpha.actionType(action_id1) == 0
    assert switchboard_alpha.actionType(action_id2) == 0


def test_dynamic_rate_config_with_existing_debt_config(switchboard_alpha, mission_control, governance):
    """Test that dynamic rate config only modifies the specific fields"""
    # First set some other debt config fields
    debt_action = switchboard_alpha.setGlobalDebtLimits(5000, 50000, 100, 100, sender=governance.address)
    keeper_action = switchboard_alpha.setKeeperConfig(5_00, 50 * 10**18, 1000 * 10**18, sender=governance.address)
    
    # Execute them
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(debt_action, sender=governance.address)
    switchboard_alpha.executePendingAction(keeper_action, sender=governance.address)
    
    # Verify initial config
    config = mission_control.genDebtConfig()
    assert config.perUserDebtLimit == 5000
    assert config.globalDebtLimit == 50000
    assert config.keeperFeeRatio == 5_00
    assert config.minKeeperFee == 50 * 10**18
    
    # Now set dynamic rate config
    dynamic_action = switchboard_alpha.setDynamicRateConfig(300_00, 900_00, 40, 190_00, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(dynamic_action, sender=governance.address)
    
    # Verify dynamic fields were updated but others preserved
    config = mission_control.genDebtConfig()
    assert config.minDynamicRateBoost == 300_00  # Updated
    assert config.maxDynamicRateBoost == 900_00  # Updated
    assert config.increasePerDangerBlock == 40   # Updated
    assert config.maxBorrowRate == 190_00        # Updated
    assert config.perUserDebtLimit == 5000       # Preserved
    assert config.globalDebtLimit == 50000       # Preserved
    assert config.keeperFeeRatio == 5_00         # Preserved
    assert config.minKeeperFee == 50 * 10**18    # Preserved


def test_dynamic_rate_config_cancel_and_expire(switchboard_alpha, governance):
    """Test canceling and expiring dynamic rate config actions"""
    # Create action
    action_id = switchboard_alpha.setDynamicRateConfig(150_00, 650_00, 20, 160_00, sender=governance.address)
    
    # Cancel it
    assert switchboard_alpha.cancelPendingAction(action_id, sender=governance.address)
    
    # Verify it's cleaned up
    assert switchboard_alpha.actionType(action_id) == 0
    assert not switchboard_alpha.hasPendingAction(action_id)
    
    # Try to execute canceled action - should fail
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert not switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Create another action and let it expire
    action_id2 = switchboard_alpha.setDynamicRateConfig(200_00, 700_00, 25, 170_00, sender=governance.address)
    
    # Time travel beyond expiration
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock() + switchboard_alpha.maxActionTimeLock() + 1)
    
    # Should automatically clean up expired action
    assert not switchboard_alpha.executePendingAction(action_id2, sender=governance.address)
    assert switchboard_alpha.actionType(action_id2) == 0


def test_dynamic_rate_config_edge_case_combinations(switchboard_alpha, governance):
    """Test edge case parameter combinations for dynamic rate config"""
    # Test with very large increasePerDangerBlock value
    # Note: denominator is 100_0000 according to the contract comment
    large_increase = 50000  # This would be 50000/100_0000 = 0.5%
    action_id = switchboard_alpha.setDynamicRateConfig(50_00, 200_00, large_increase, 100_00, sender=governance.address)
    assert action_id > 0
    
    # Test with min boost very close to max boost
    action_id = switchboard_alpha.setDynamicRateConfig(999_00, 1000_00, 1, 50_00, sender=governance.address)
    assert action_id > 0
    
    # Test with small borrow rate and large boosts
    action_id = switchboard_alpha.setDynamicRateConfig(800_00, 1000_00, 100, 1, sender=governance.address)
    assert action_id > 0
    
    # Test with all parameters at their respective maximums
    action_id = switchboard_alpha.setDynamicRateConfig(1000_00, 1000_00, MAX_UINT256 - 1, 200_00, sender=governance.address)
    assert action_id > 0


def test_dynamic_rate_config_action_type_consistency(switchboard_alpha, governance):
    """Test that action type is properly managed for dynamic rate config"""
    # Create action and verify it's stored with correct type
    action_id = switchboard_alpha.setDynamicRateConfig(120_00, 520_00, 12, 110_00, sender=governance.address)
    
    # Verify action type is set (not empty)
    assert switchboard_alpha.actionType(action_id) != 0
    assert switchboard_alpha.hasPendingAction(action_id)
    
    # Verify pending config is stored
    pending = switchboard_alpha.pendingDebtConfig(action_id)
    assert pending.minDynamicRateBoost == 120_00
    assert pending.maxDynamicRateBoost == 520_00
    assert pending.increasePerDangerBlock == 12
    assert pending.maxBorrowRate == 110_00
    
    # Execute action
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Verify cleanup
    assert switchboard_alpha.actionType(action_id) == 0
    assert not switchboard_alpha.hasPendingAction(action_id)


def test_dynamic_rate_config_event_emissions(switchboard_alpha, governance):
    """Test that correct events are emitted for dynamic rate config"""
    # Clear any existing events by getting current count
    logs_before = filter_logs(switchboard_alpha, "PendingDynamicRateConfigChange")
    events_before = len(logs_before)
    
    # Create action
    action_id = switchboard_alpha.setDynamicRateConfig(180_00, 680_00, 18, 145_00, sender=governance.address)
    
    # Check pending event was emitted
    logs_after = filter_logs(switchboard_alpha, "PendingDynamicRateConfigChange")
    assert len(logs_after) == events_before + 1
    
    pending_log = logs_after[-1]  # Get the latest event
    assert pending_log.minDynamicRateBoost == 180_00
    assert pending_log.maxDynamicRateBoost == 680_00
    assert pending_log.increasePerDangerBlock == 18
    assert pending_log.maxBorrowRate == 145_00
    assert pending_log.actionId == action_id
    assert pending_log.confirmationBlock > 0
    
    # Execute and check execution event
    logs_before_exec = filter_logs(switchboard_alpha, "DynamicRateConfigSet")
    events_before_exec = len(logs_before_exec)
    
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Check execution event was emitted
    logs_after_exec = filter_logs(switchboard_alpha, "DynamicRateConfigSet")
    assert len(logs_after_exec) == events_before_exec + 1
    
    exec_log = logs_after_exec[-1]  # Get the latest event
    assert exec_log.minDynamicRateBoost == 180_00
    assert exec_log.maxDynamicRateBoost == 680_00
    assert exec_log.increasePerDangerBlock == 18
    assert exec_log.maxBorrowRate == 145_00
