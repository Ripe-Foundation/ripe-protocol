import boa

from constants import MAX_UINT256, ZERO_ADDRESS
from conf_utils import filter_logs


def test_deployment_success(switchboard_bravo):
    assert switchboard_bravo.actionId() == 1  # starts at 1


def test_governance_permissions(switchboard_bravo, bob):
    # Test functions that require governance permissions
    with boa.reverts("no perms"):
        switchboard_bravo.addAsset(
            ZERO_ADDRESS, [], 0, 0, 100, 1000, 0,
            sender=bob
        )
    
    with boa.reverts("no perms"):
        switchboard_bravo.setAssetDepositParams(
            ZERO_ADDRESS, [], 0, 0, 100, 1000, 0,
            sender=bob
        )


def test_enable_disable_permissions(switchboard_bravo, governance, bob, alpha_token):
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
        switchboard_bravo.setCanDepositAsset(alpha_token, True, sender=bob)
    
    # Governance can enable/disable
    assert switchboard_bravo.setCanDepositAsset(alpha_token, False, sender=governance.address)
    
    # Test users with canDisable permission can disable
    # First set bob as someone who can disable (this would be done through SwitchboardOne)
    # For now, test that bob cannot enable
    with boa.reverts("no perms"):
        switchboard_bravo.setCanDepositAsset(alpha_token, True, sender=bob)


def test_add_asset_validation(switchboard_bravo, governance, alpha_token):
    """Test asset addition validation"""
    # Test invalid asset (zero address)
    with boa.reverts("invalid asset"):
        switchboard_bravo.addAsset(
            ZERO_ADDRESS, [1], 50_00, 30_00, 1000, 10000, 0,
            sender=governance.address
        )


def test_add_asset_success(switchboard_bravo, governance, alpha_token):
    """Test successful asset addition"""
    action_id = switchboard_bravo.addAsset(
        alpha_token, 
        [1, 2],  # vault IDs
        50_00,   # stakers points alloc
        30_00,   # voter points alloc  
        1000,    # per user deposit limit
        10000,   # global deposit limit
        0,       # minDepositBalance
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
    assert action_id > 0
    
    # Check event was emitted
    logs = filter_logs(switchboard_bravo, "NewAssetPending")
    assert len(logs) == 1
    log = logs[0]
    assert log.asset == alpha_token.address
    assert log.numVaults == 2
    assert log.stakersPointsAlloc == 50_00
    assert log.voterPointsAlloc == 30_00
    assert log.perUserDepositLimit == 1000
    assert log.globalDepositLimit == 10000
    
    # Check pending config was stored
    pending = switchboard_bravo.pendingAssetConfig(action_id)
    assert pending.asset == alpha_token.address
    assert len(pending.config.vaultIds) == 2
    assert pending.config.vaultIds[0] == 1
    assert pending.config.vaultIds[1] == 2


def test_add_asset_with_debt_terms(switchboard_bravo, governance, alpha_token):
    """Test asset addition with debt terms"""
    debt_terms = (
        75_00,  # ltv
        80_00,  # redemption threshold
        85_00,  # liq threshold
        5_00,   # liq fee
        10_00,  # borrow rate
        2_00    # daowry
    )
    
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        debt_terms,  # debt terms
        False,  # shouldBurnAsPayment
        False,  # shouldTransferToEndaoment  
        True,   # shouldSwapInStabPools (True because we have LTV)
        True,   # shouldAuctionInstantly
        True,   # canDeposit
        True,   # canWithdraw
        True,   # canRedeemCollateral (True because we have LTV)
        True,   # canRedeemInStabPool
        True,   # canBuyInAuction
        True,   # canClaimInStabPool
        0,      # specialStabPoolId
        sender=governance.address
    )
    assert action_id > 0
    
    logs = filter_logs(switchboard_bravo, "NewAssetPending")
    assert len(logs) == 1
    log = logs[0]
    assert log.debtTermsLtv == 75_00
    assert log.debtTermsRedemptionThreshold == 80_00
    assert log.debtTermsLiqThreshold == 85_00


def test_add_asset_with_custom_flags(switchboard_bravo, governance, alpha_token):
    """Test asset addition with custom flags"""
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False,  # shouldBurnAsPayment (False - only green tokens can burn)
        False,  # shouldTransferToEndaoment  
        False,  # shouldSwapInStabPools (False because no LTV)
        False,  # shouldAuctionInstantly
        False,  # canDeposit
        False,  # canWithdraw
        False,  # canRedeemCollateral (False because no LTV)
        True,   # canRedeemInStabPool
        True,   # canBuyInAuction
        True,   # canClaimInStabPool
        0,      # specialStabPoolId (use 0, not 5)
        sender=governance.address
    )
    assert action_id > 0
    
    logs = filter_logs(switchboard_bravo, "NewAssetPending")
    assert len(logs) == 1
    log = logs[0]
    assert not log.shouldBurnAsPayment  # Updated expectation
    assert not log.shouldTransferToEndaoment
    assert not log.canDeposit
    assert not log.canWithdraw
    assert log.specialStabPoolId == 0  # Updated expectation


def test_execute_add_asset(switchboard_bravo, mission_control, governance, alpha_token):
    """Test executing asset addition"""
    # Add asset
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
    
    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    
    # Execute the action
    assert switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Check event was emitted  
    logs = filter_logs(switchboard_bravo, "AssetAdded")
    assert len(logs) == 1
    assert logs[0].asset == alpha_token.address
    
    # Verify the action was cleaned up
    assert switchboard_bravo.actionType(action_id) == 0
    assert not switchboard_bravo.hasPendingAction(action_id)


def test_asset_deposit_params_validation(switchboard_bravo, governance, alpha_token):
    """Test asset deposit params validation"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Test invalid deposit params - zero limits
    with boa.reverts("invalid asset deposit params"):
        switchboard_bravo.setAssetDepositParams(
            alpha_token, [1], 50_00, 30_00, 0, 10000, 0,  # zero per user limit
            sender=governance.address
        )
    
    with boa.reverts("invalid asset deposit params"):
        switchboard_bravo.setAssetDepositParams(
            alpha_token, [1], 50_00, 30_00, 1000, 0, 0,  # zero global limit
            sender=governance.address
        )
    
    # Test per user > global
    with boa.reverts("invalid asset deposit params"):
        switchboard_bravo.setAssetDepositParams(
            alpha_token, [1], 50_00, 30_00, 10000, 1000, 0,  # per user > global
            sender=governance.address
        )
    
    # Test allocations > 100%
    with boa.reverts("invalid asset deposit params"):
        switchboard_bravo.setAssetDepositParams(
            alpha_token, [1], 60_00, 50_00, 1000, 10000, 0,  # 110% total
            sender=governance.address
        )


def test_asset_deposit_params_success(switchboard_bravo, governance, alpha_token):
    """Test successful asset deposit params setting"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Set new deposit params
    action_id = switchboard_bravo.setAssetDepositParams(
        alpha_token, [2, 3], 40_00, 35_00, 2000, 20000, 0,
        sender=governance.address
    )
    assert action_id > 0
    
    # Check event
    logs = filter_logs(switchboard_bravo, "PendingAssetDepositParamsChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.asset == alpha_token.address
    assert log.numVaultIds == 2
    assert log.stakersPointsAlloc == 40_00
    assert log.voterPointsAlloc == 35_00


def test_execute_asset_deposit_params(switchboard_bravo, mission_control, governance, alpha_token):
    """Test executing asset deposit params change"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Set new deposit params
    action_id = switchboard_bravo.setAssetDepositParams(
        alpha_token, [2, 3], 40_00, 35_00, 2000, 20000, 0,
        sender=governance.address
    )
    
    # Execute
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    assert switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Check event
    logs = filter_logs(switchboard_bravo, "AssetDepositParamsSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.asset == alpha_token.address
    assert log.numVaultIds == 2
    assert log.stakersPointsAlloc == 40_00


def test_asset_debt_terms_validation(switchboard_bravo, governance, alpha_token):
    """Test asset debt terms validation"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Test invalid debt terms - liq threshold > 100%
    with boa.reverts("invalid debt terms"):
        switchboard_bravo.setAssetDebtTerms(
            alpha_token, 75_00, 80_00, 105_00, 5_00, 10_00, 2_00,  # liq threshold > 100%
            sender=governance.address
        )
    
    # Test redemption > liq threshold
    with boa.reverts("invalid debt terms"):
        switchboard_bravo.setAssetDebtTerms(
            alpha_token, 75_00, 90_00, 85_00, 5_00, 10_00, 2_00,  # redemption > liq
            sender=governance.address
        )
    
    # Test ltv > redemption
    with boa.reverts("invalid debt terms"):
        switchboard_bravo.setAssetDebtTerms(
            alpha_token, 85_00, 80_00, 90_00, 5_00, 10_00, 2_00,  # ltv > redemption
            sender=governance.address
        )


def test_asset_debt_terms_success(switchboard_bravo, governance, alpha_token):
    """Test successful asset debt terms setting"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Set debt terms
    action_id = switchboard_bravo.setAssetDebtTerms(
        alpha_token, 70_00, 75_00, 80_00, 8_00, 12_00, 3_00,
        sender=governance.address
    )
    assert action_id > 0
    
    # Check event
    logs = filter_logs(switchboard_bravo, "PendingAssetDebtTermsChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.asset == alpha_token.address
    assert log.ltv == 70_00
    assert log.redemptionThreshold == 75_00
    assert log.liqThreshold == 80_00


def test_execute_asset_debt_terms(switchboard_bravo, mission_control, governance, alpha_token):
    """Test executing asset debt terms change"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Set debt terms
    action_id = switchboard_bravo.setAssetDebtTerms(
        alpha_token, 70_00, 75_00, 80_00, 8_00, 12_00, 3_00,
        sender=governance.address
    )
    
    # Execute
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    assert switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Check event
    logs = filter_logs(switchboard_bravo, "AssetDebtTermsSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.asset == alpha_token.address
    assert log.ltv == 70_00
    assert log.redemptionThreshold == 75_00


def test_asset_enable_disable_flags(switchboard_bravo, mission_control, governance, alpha_token):
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
    assert switchboard_bravo.setCanDepositAsset(alpha_token, True, sender=governance.address)
    
    # Check event
    logs = filter_logs(switchboard_bravo, "CanDepositAssetSet")
    assert len(logs) == 1
    assert logs[0].asset == alpha_token.address
    assert logs[0].canDeposit
    
    # Test disabling deposits
    assert switchboard_bravo.setCanDepositAsset(alpha_token, False, sender=governance.address)
    
    # Test setting same value fails
    with boa.reverts("already set"):
        switchboard_bravo.setCanDepositAsset(alpha_token, False, sender=governance.address)


def test_all_asset_enable_disable_functions(switchboard_bravo, governance, alpha_token):
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
        switchboard_bravo.setCanWithdrawAsset,
        switchboard_bravo.setCanRedeemInStabPoolAsset,
        switchboard_bravo.setCanBuyInAuctionAsset, 
        switchboard_bravo.setCanClaimInStabPoolAsset,
    ]
    
    for func in functions:
        # Enable (assets start with False for these)
        assert func(alpha_token, True, sender=governance.address)
        
        # Disable
        assert func(alpha_token, False, sender=governance.address)


def test_asset_whitelist_setting(switchboard_bravo, governance, alpha_token, mock_rando_contract):
    """Test setting whitelist for asset"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Set whitelist (this will fail validation with mock contract)
    with boa.reverts("invalid whitelist"):
        switchboard_bravo.setWhitelistForAsset(alpha_token, mock_rando_contract, sender=governance.address)


def test_execute_invalid_action(switchboard_bravo, governance):
    """Test executing non-existent action"""
    assert not switchboard_bravo.executePendingAction(999, sender=governance.address)


def test_cancel_action(switchboard_bravo, governance, alpha_token):
    """Test canceling pending action"""
    # Create an action
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    
    # Cancel it
    assert switchboard_bravo.cancelPendingAction(action_id, sender=governance.address)
    
    # Verify it's no longer pending
    assert not switchboard_bravo.hasPendingAction(action_id)


def test_execute_before_timelock_when_timelock_nonzero(switchboard_bravo, governance, alpha_token):
    """Test executing action before timelock expires"""
    time_lock = switchboard_bravo.actionTimeLock()
    
    if time_lock == 0:
        # If timelock is 0, action executes immediately
        action_id = switchboard_bravo.addAsset(
            alpha_token, [1], 50_00, 30_00, 1000, 10000,
            (0, 0, 0, 0, 0, 0),  # empty debt terms
            False, False, False, True, True, True, False, True, True, True, 0,
            sender=governance.address
        )
        assert switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    else:
        # Test that action cannot be executed before timelock
        action_id = switchboard_bravo.addAsset(
            alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
            (0, 0, 0, 0, 0, 0),  # empty debt terms
            False, False, False, True, True, True, False, True, True, True, 0,
            sender=governance.address
        )
        # Try to execute before timelock
        assert not switchboard_bravo.executePendingAction(action_id, sender=governance.address)


def test_execute_expired_action(switchboard_bravo, governance, alpha_token):
    """Test executing expired action"""
    # Create an action
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    
    # Time travel past expiration
    time_lock = switchboard_bravo.actionTimeLock()
    expiration = switchboard_bravo.expiration()
    boa.env.time_travel(blocks=time_lock + expiration + 1)
    
    # Try to execute expired action
    assert not switchboard_bravo.executePendingAction(action_id, sender=governance.address)


def test_action_id_increment(switchboard_bravo, governance, alpha_token):
    """Test that action IDs increment properly"""
    initial_id = switchboard_bravo.actionId()
    
    # Create an action
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    
    # Action ID should increment
    assert action_id == initial_id
    assert switchboard_bravo.actionId() == initial_id + 1


def test_pending_action_cleanup(switchboard_bravo, governance, alpha_token):
    """Test that pending action data is cleaned up after execution"""
    # Create and execute an action
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    assert switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Verify pending data is cleaned up
    assert switchboard_bravo.actionType(action_id) == 0  # empty ActionType
    assert not switchboard_bravo.hasPendingAction(action_id)


def test_asset_liq_config_validation(switchboard_bravo, governance, alpha_token):
    """Test asset liquidation config validation"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Test valid liq config
    action_id = switchboard_bravo.setAssetLiqConfig(
        alpha_token, False, True, False, True, 0,  # use specialStabPoolId=0
        sender=governance.address
    )
    assert action_id > 0


def test_asset_liq_config_with_auction_params(switchboard_bravo, governance, alpha_token):
    """Test asset liquidation config with custom auction params"""
    # First add the asset with debt terms so we can swap in stab pools
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (75_00, 80_00, 85_00, 5_00, 10_00, 2_00),  # debt terms with LTV
        False, False, True, True, True, True, True, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Test with custom auction params
    auction_params = (True, 10_00, 50_00, 1000, 3000)  # hasParams, start, max, delay, duration
    action_id = switchboard_bravo.setAssetLiqConfig(
        alpha_token, False, True, True, True, 0, auction_params,
        sender=governance.address
    )
    assert action_id > 0
    
    # Check event
    logs = filter_logs(switchboard_bravo, "PendingAssetLiqConfigChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.asset == alpha_token.address
    assert log.auctionStartDiscount == 10_00
    assert log.auctionMaxDiscount == 50_00


def test_execute_asset_liq_config(switchboard_bravo, mission_control, governance, alpha_token):
    """Test executing asset liquidation config change"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Set liq config
    action_id = switchboard_bravo.setAssetLiqConfig(
        alpha_token, False, False, False, False, 0,  # use specialStabPoolId=0
        sender=governance.address
    )
    
    # Execute
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    assert switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Check event
    logs = filter_logs(switchboard_bravo, "AssetLiqConfigSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.asset == alpha_token.address
    assert not log.shouldBurnAsPayment
    assert not log.shouldTransferToEndaoment
    assert log.specialStabPoolId == 0  # Updated expectation


def test_execute_asset_whitelist(switchboard_bravo, mission_control, governance, alpha_token):
    """Test executing asset whitelist change"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Set whitelist to zero address (removing whitelist)
    action_id = switchboard_bravo.setWhitelistForAsset(alpha_token, ZERO_ADDRESS, sender=governance.address)
    
    # Execute
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    assert switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Check event
    logs = filter_logs(switchboard_bravo, "WhitelistAssetSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.asset == alpha_token.address
    assert log.whitelist == ZERO_ADDRESS


def test_asset_not_supported_validation(switchboard_bravo, governance, bravo_token):
    """Test that operations on unsupported assets fail"""
    # Try to set deposit params on non-existent asset
    with boa.reverts("invalid asset"):
        switchboard_bravo.setAssetDepositParams(
            bravo_token, [1], 50_00, 30_00, 1000, 10000, 0,
            sender=governance.address
        )
    
    # Try to set debt terms on non-existent asset
    with boa.reverts("invalid asset"):
        switchboard_bravo.setAssetDebtTerms(
            bravo_token, 70_00, 75_00, 80_00, 8_00, 12_00, 3_00,
            sender=governance.address
        )
    
    # Try to enable/disable non-existent asset
    with boa.reverts("invalid asset"):
        switchboard_bravo.setCanDepositAsset(bravo_token, True, sender=governance.address)


def test_debt_terms_boundary_conditions(switchboard_bravo, governance, alpha_token):
    """Test debt terms at boundary conditions"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Test valid boundary conditions
    # LTV = redemption = liq threshold (all equal)
    action_id = switchboard_bravo.setAssetDebtTerms(
        alpha_token, 80_00, 80_00, 80_00, 5_00, 10_00, 2_00,
        sender=governance.address
    )
    assert action_id > 0
    
    # Test with zero LTV (should be valid)
    action_id = switchboard_bravo.setAssetDebtTerms(
        alpha_token, 0, 0, 80_00, 0, 0, 0,
        sender=governance.address
    )
    assert action_id > 0
    
    # Test liq threshold at exactly 100% - but this fails the liq threshold + bonus validation
    # Let's test a valid case instead: 95% liq threshold with 5% fee = 99.75% total
    action_id = switchboard_bravo.setAssetDebtTerms(
        alpha_token, 80_00, 90_00, 95_00, 5_00, 10_00, 2_00,
        sender=governance.address
    )
    assert action_id > 0


def test_asset_deposit_params_boundary_conditions(switchboard_bravo, governance, alpha_token):
    """Test asset deposit params at boundary conditions"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Test with per user = global limit (should be valid)
    action_id = switchboard_bravo.setAssetDepositParams(
        alpha_token, [1], 50_00, 30_00, 5000, 5000, 0,
        sender=governance.address
    )
    assert action_id > 0
    
    # Test with total allocation = 100%
    action_id = switchboard_bravo.setAssetDepositParams(
        alpha_token, [1], 60_00, 40_00, 1000, 10000, 0,
        sender=governance.address
    )
    assert action_id > 0
    
    # Test with zero allocations (should be valid)
    action_id = switchboard_bravo.setAssetDepositParams(
        alpha_token, [1], 0, 0, 1000, 10000, 0,
        sender=governance.address
    )
    assert action_id > 0


def test_asset_deposit_params_max_vaults(switchboard_bravo, governance, alpha_token):
    """Test asset deposit params with maximum vault IDs"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Test with available vault IDs (only 1, 2, 3 exist in test environment)
    available_vaults = [1, 2, 3]  # Only use existing vaults
    action_id = switchboard_bravo.setAssetDepositParams(
        alpha_token, available_vaults, 50_00, 30_00, 1000, 10000, 0,
        sender=governance.address
    )
    assert action_id > 0
    
    # Check pending config
    pending = switchboard_bravo.pendingAssetConfig(action_id)
    assert len(pending.config.vaultIds) == 3


def test_sequential_actions_same_asset(switchboard_bravo, governance, alpha_token):
    """Test multiple sequential actions on the same asset"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Create multiple sequential actions for the same asset
    action_id1 = switchboard_bravo.setAssetDepositParams(
        alpha_token, [2], 40_00, 35_00, 2000, 20000, 0,
        sender=governance.address
    )
    action_id2 = switchboard_bravo.setAssetDebtTerms(
        alpha_token, 70_00, 75_00, 80_00, 8_00, 12_00, 3_00,
        sender=governance.address
    )
    action_id3 = switchboard_bravo.setAssetLiqConfig(
        alpha_token, False, True, False, True, 0,  # shouldSwapInStabPools=False
        sender=governance.address
    )
    
    assert action_id1 != action_id2 != action_id3
    assert action_id2 == action_id1 + 1
    assert action_id3 == action_id2 + 1


def test_multiple_assets_workflow(switchboard_bravo, governance, alpha_token, bravo_token):
    """Test workflow with multiple assets"""
    # Add first asset
    action_id1 = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    
    # Add second asset
    action_id2 = switchboard_bravo.addAsset(
        bravo_token, [2], 40_00, 35_00, 2000, 20000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    
    # Execute both
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    assert switchboard_bravo.executePendingAction(action_id1, sender=governance.address)
    assert switchboard_bravo.executePendingAction(action_id2, sender=governance.address)
    
    # Configure both assets differently (they start with canDeposit=True, canWithdraw=True)
    assert switchboard_bravo.setCanDepositAsset(alpha_token, False, sender=governance.address)
    assert switchboard_bravo.setCanDepositAsset(bravo_token, False, sender=governance.address)
    
    assert switchboard_bravo.setCanWithdrawAsset(alpha_token, False, sender=governance.address)
    assert switchboard_bravo.setCanWithdrawAsset(bravo_token, False, sender=governance.address)


def test_complex_asset_configuration(switchboard_bravo, governance, alpha_token):
    """Test complex asset configuration with all parameters"""
    # Add asset with full configuration
    debt_terms = (75_00, 80_00, 85_00, 5_00, 10_00, 2_00)
    auction_params = (True, 15_00, 45_00, 500, 2000)
    
    action_id = switchboard_bravo.addAsset(
        alpha_token,
        [1, 2, 3],  # use only existing vaults
        45_00,      # stakers alloc
        35_00,      # voters alloc  
        5000,       # per user limit
        50000,      # global limit
        0,          # minDepositBalance
        debt_terms,
        False,      # shouldBurnAsPayment (not green token)
        False,      # shouldTransferToEndaoment
        True,       # shouldSwapInStabPools (we have LTV)
        False,      # shouldAuctionInstantly
        True,       # canDeposit
        True,       # canWithdraw
        True,       # canRedeemCollateral (we have LTV)
        True,       # canRedeemInStabPool
        True,       # canBuyInAuction
        True,       # canClaimInStabPool
        0,          # specialStabPoolId (use 0, not 10)
        auction_params,
        ZERO_ADDRESS,  # whitelist
        False,      # isNft
        sender=governance.address
    )
    assert action_id > 0
    
    # Check all parameters were stored
    logs = filter_logs(switchboard_bravo, "NewAssetPending")
    assert len(logs) == 1
    log = logs[0]
    assert log.asset == alpha_token.address
    assert log.numVaults == 3
    assert log.stakersPointsAlloc == 45_00
    assert log.voterPointsAlloc == 35_00
    assert not log.shouldBurnAsPayment
    assert not log.shouldTransferToEndaoment
    assert log.canDeposit
    assert log.canWithdraw
    assert log.specialStabPoolId == 0  # Updated expectation
    assert log.auctionStartDiscount == 15_00
    assert not log.isNft


def test_execute_all_action_types(switchboard_bravo, mission_control, governance, alpha_token):
    """Test executing all different action types"""
    time_lock = switchboard_bravo.actionTimeLock()
    
    # Add asset first
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=time_lock)
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Test all action types
    actions = []
    
    # Deposit params - use only existing vaults
    actions.append(switchboard_bravo.setAssetDepositParams(
        alpha_token, [2, 3], 40_00, 35_00, 2000, 20000, 0,
        sender=governance.address
    ))
    
    # Debt terms
    actions.append(switchboard_bravo.setAssetDebtTerms(
        alpha_token, 70_00, 75_00, 80_00, 8_00, 12_00, 3_00,
        sender=governance.address
    ))
    
    # Liq config - use specialStabPoolId=0
    actions.append(switchboard_bravo.setAssetLiqConfig(
        alpha_token, False, False, False, True, 0,  # use 0, not 5
        sender=governance.address
    ))
    
    # Whitelist
    actions.append(switchboard_bravo.setWhitelistForAsset(
        alpha_token, ZERO_ADDRESS, sender=governance.address
    ))
    
    # Execute all actions
    boa.env.time_travel(blocks=time_lock)
    for action in actions:
        assert switchboard_bravo.executePendingAction(action, sender=governance.address)
    
    # Verify all actions were cleaned up
    for action in actions:
        assert switchboard_bravo.actionType(action) == 0
        assert not switchboard_bravo.hasPendingAction(action)


def test_cancel_action_edge_cases(switchboard_bravo, governance, alpha_token):
    """Test action cancellation edge cases"""
    # Test canceling non-existent action
    with boa.reverts("cannot cancel action"):
        switchboard_bravo.cancelPendingAction(999, sender=governance.address)
    
    # Test canceling already executed action
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Should fail to cancel already executed action
    with boa.reverts("cannot cancel action"):
        switchboard_bravo.cancelPendingAction(action_id, sender=governance.address)


def test_asset_flag_validation_redeem_collateral(switchboard_bravo, governance, alpha_token):
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
        switchboard_bravo.setCanRedeemCollateralAsset(alpha_token, True, sender=governance.address)


def test_debt_terms_liq_bonus_validation(switchboard_bravo, governance, alpha_token):
    """Test debt terms liquidation bonus validation"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Test invalid combination where liq threshold + bonus > 100%
    # liq threshold 90% + 15% fee = 103.5% total > 100%
    with boa.reverts("invalid debt terms"):
        switchboard_bravo.setAssetDebtTerms(
            alpha_token, 75_00, 80_00, 90_00, 15_00, 10_00, 2_00,
            sender=governance.address
        )


def test_non_zero_ltv_requires_fees(switchboard_bravo, governance, alpha_token):
    """Test that non-zero LTV requires non-zero fees"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Test that non-zero LTV with zero liq fee fails
    with boa.reverts("invalid debt terms"):
        switchboard_bravo.setAssetDebtTerms(
            alpha_token, 75_00, 80_00, 85_00, 0, 10_00, 2_00,  # zero liq fee
            sender=governance.address
        )
    
    # Test that non-zero LTV with zero borrow rate fails
    with boa.reverts("invalid debt terms"):
        switchboard_bravo.setAssetDebtTerms(
            alpha_token, 75_00, 80_00, 85_00, 5_00, 0, 2_00,  # zero borrow rate
            sender=governance.address
        )


def test_max_uint256_validation(switchboard_bravo, governance, alpha_token):
    """Test that MAX_UINT256 values are rejected"""
    # Test max uint256 in deposit params - should fail with "invalid asset" error
    with boa.reverts("invalid asset"):
        switchboard_bravo.addAsset(
            alpha_token, [1], MAX_UINT256, 30_00, 1000, 10000, 0,  # max stakersPointsAlloc
            (0, 0, 0, 0, 0, 0), False, False, False, True, True, True, False, True, True, True, 0,
            sender=governance.address
        )
    
    with boa.reverts("invalid asset"):
        switchboard_bravo.addAsset(
            alpha_token, [1], 50_00, MAX_UINT256, 1000, 10000, 0,  # max voterPointsAlloc
            (0, 0, 0, 0, 0, 0), False, False, False, True, True, True, False, True, True, True, 0,
            sender=governance.address
        )
    
    with boa.reverts("invalid asset"):
        switchboard_bravo.addAsset(
            alpha_token, [1], 50_00, 30_00, MAX_UINT256, 10000, 0,  # max perUserDepositLimit
            (0, 0, 0, 0, 0, 0), False, False, False, True, True, True, False, True, True, True, 0,
            sender=governance.address
        )
    
    with boa.reverts("invalid asset"):
        switchboard_bravo.addAsset(
            alpha_token, [1], 50_00, 30_00, 1000, MAX_UINT256, 0,  # max globalDepositLimit
            (0, 0, 0, 0, 0, 0), False, False, False, True, True, True, False, True, True, True, 0,
            sender=governance.address
        )


def test_ltv_deviation_validation_edge_cases(switchboard_bravo, switchboard_alpha, governance, alpha_token):
    """Test LTV deviation validation with various edge cases"""
    # First add the asset with initial LTV
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (60_00, 70_00, 80_00, 5_00, 10_00, 2_00),  # 60% LTV
        False, False, True, True, True, True, True, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Set max deviation via switchboard_alpha (10% deviation allowed)
    action_id = switchboard_alpha.setMaxLtvDeviation(10_00, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Test: Cannot set LTV to 0 when previously non-zero
    with boa.reverts("ltv is outside max deviation"):
        switchboard_bravo.setAssetDebtTerms(
            alpha_token, 0, 0, 80_00, 0, 0, 0,  # LTV to 0
            sender=governance.address
        )
    
    # Test: LTV change within allowed deviation (60% -> 65%)
    action_id = switchboard_bravo.setAssetDebtTerms(
        alpha_token, 65_00, 70_00, 80_00, 5_00, 10_00, 2_00,
        sender=governance.address
    )
    assert action_id > 0
    
    # Test: LTV change outside allowed deviation (60% -> 75% = 15% change > 10% max)
    with boa.reverts("ltv is outside max deviation"):
        switchboard_bravo.setAssetDebtTerms(
            alpha_token, 75_00, 80_00, 85_00, 5_00, 10_00, 2_00,
            sender=governance.address
        )
    
    # Test: LTV change to lower bound (60% -> 50%)
    action_id = switchboard_bravo.setAssetDebtTerms(
        alpha_token, 50_00, 60_00, 70_00, 5_00, 10_00, 2_00,
        sender=governance.address
    )
    assert action_id > 0
    
    # Test: LTV change outside lower bound (60% -> 45% = 15% change > 10% max)
    with boa.reverts("ltv is outside max deviation"):
        switchboard_bravo.setAssetDebtTerms(
            alpha_token, 45_00, 60_00, 70_00, 5_00, 10_00, 2_00,
            sender=governance.address
        )


def test_ltv_deviation_from_zero_ltv(switchboard_bravo, switchboard_alpha, governance, alpha_token):
    """Test LTV deviation validation when starting from zero LTV"""
    # Add asset with zero LTV
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # Zero LTV
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Set max deviation via switchboard_alpha
    action_id = switchboard_alpha.setMaxLtvDeviation(10_00, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    
    # Can set any LTV when starting from zero (no restriction)
    action_id = switchboard_bravo.setAssetDebtTerms(
        alpha_token, 75_00, 80_00, 85_00, 5_00, 10_00, 2_00,
        sender=governance.address
    )
    assert action_id > 0


def test_ltv_deviation_with_default_values(switchboard_bravo, governance, alpha_token, bravo_token, setGeneralDebtConfig):
    """Test LTV deviation validation with default max deviation (10%)"""
    setGeneralDebtConfig()

    # Add first asset with LTV
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (50_00, 60_00, 70_00, 5_00, 10_00, 2_00),  # 50% LTV
        False, False, True, True, True, True, True, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Test: LTV change within default max deviation (50% -> 55%, change = 5% < 10% default)
    action_id = switchboard_bravo.setAssetDebtTerms(
        alpha_token, 55_00, 65_00, 75_00, 5_00, 10_00, 2_00,
        sender=governance.address
    )
    assert action_id > 0
    
    # Test: LTV change outside default max deviation (50% -> 65%, change = 15% > 10% default)
    with boa.reverts("ltv is outside max deviation"):
        switchboard_bravo.setAssetDebtTerms(
            alpha_token, 65_00, 75_00, 85_00, 5_00, 10_00, 2_00,
            sender=governance.address
        )
    
    # Add another asset to test from zero LTV (should be unrestricted)
    action_id = switchboard_bravo.addAsset(
        bravo_token, [2], 40_00, 30_00, 2000, 20000, 0,
        (0, 0, 0, 0, 0, 0),  # Zero LTV
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Can set any LTV from zero (no restriction)
    action_id = switchboard_bravo.setAssetDebtTerms(
        bravo_token, 80_00, 85_00, 90_00, 5_00, 10_00, 2_00,
        sender=governance.address
    )
    assert action_id > 0


# def test_whitelist_special_stab_pool_validation(switchboard_bravo, governance, alpha_token, mock_rando_contract):
#     """Test whitelist and special stab pool interaction validation"""
#     # Test: Cannot have whitelist with zero special stab pool when swapping in stab pools
#     with boa.reverts("invalid asset"):
#         switchboard_bravo.addAsset(
#             alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
#             (60_00, 70_00, 80_00, 5_00, 10_00, 2_00),  # with LTV
#             False,  # shouldBurnAsPayment
#             False,  # shouldTransferToEndaoment
#             True,   # shouldSwapInStabPools
#             True,   # shouldAuctionInstantly
#             True,   # canDeposit
#             True,   # canWithdraw
#             True,   # canRedeemCollateral
#             True,   # canRedeemInStabPool
#             True,   # canBuyInAuction
#             True,   # canClaimInStabPool
#             0,      # specialStabPoolId (zero with whitelist = invalid)
#             (False, 0, 0, 0, 0),  # customAuctionParams
#             mock_rando_contract,  # whitelist (non-zero)
#             False,  # isNft
#             sender=governance.address
#         )


def test_auction_params_validation_delegation(switchboard_bravo, governance, alpha_token, switchboard_alpha):
    """Test that auction params validation is delegated to SwitchboardOne"""
    # Create invalid auction params (start >= max discount)
    invalid_auction_params = (True, 50_00, 40_00, 1000, 3000)  # start 50% >= max 40%
    
    # This should fail because SwitchboardOne validates auction params
    with boa.reverts("invalid auction params"):
        switchboard_bravo.setAssetLiqConfig(
            alpha_token, False, True, False, True, 0, invalid_auction_params,
            sender=governance.address
        )


def test_permission_can_disable_logic(switchboard_bravo, switchboard_alpha, governance, bob, alpha_token):
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
    assert switchboard_bravo.setCanDepositAsset(alpha_token, False, sender=bob)  # disable allowed
    
    with boa.reverts("no perms"):
        switchboard_bravo.setCanDepositAsset(alpha_token, True, sender=bob)  # enable not allowed


def test_asset_configuration_validation_comprehensive(switchboard_bravo, governance, alpha_token):
    """Test comprehensive asset configuration validation scenarios"""
    # Test: shouldSwapInStabPools=True requires non-zero LTV
    with boa.reverts("invalid asset"):
        switchboard_bravo.addAsset(
            alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
            (0, 0, 0, 0, 0, 0),  # zero LTV
            False,  # shouldBurnAsPayment
            False,  # shouldTransferToEndaoment
            True,   # shouldSwapInStabPools (requires LTV)
            True,   # shouldAuctionInstantly
            True,   # canDeposit
            True,   # canWithdraw
            False,  # canRedeemCollateral
            True,   # canRedeemInStabPool
            True,   # canBuyInAuction
            True,   # canClaimInStabPool
            0,      # specialStabPoolId
            sender=governance.address
        )
    
    # Test: canRedeemCollateral=True requires non-zero LTV
    with boa.reverts("invalid asset"):
        switchboard_bravo.addAsset(
            alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
            (0, 0, 0, 0, 0, 0),  # zero LTV
            False,  # shouldBurnAsPayment
            False,  # shouldTransferToEndaoment
            False,  # shouldSwapInStabPools
            True,   # shouldAuctionInstantly
            True,   # canDeposit
            True,   # canWithdraw
            True,   # canRedeemCollateral (requires LTV)
            True,   # canRedeemInStabPool
            True,   # canBuyInAuction
            True,   # canClaimInStabPool
            0,      # specialStabPoolId
            sender=governance.address
        )


def test_asset_enable_redeem_collateral_validation(switchboard_bravo, governance, alpha_token):
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
    assert switchboard_bravo.setCanRedeemCollateralAsset(alpha_token, True, sender=governance.address)


def test_action_execution_normal_workflow(switchboard_bravo, governance, alpha_token):
    """Test normal action execution workflow"""
    # Create a valid action
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (60_00, 70_00, 80_00, 5_00, 10_00, 2_00),
        False, False, True, True, True, True, True, True, True, True, 0,
        sender=governance.address
    )
    
    # Time travel past timelock  
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    
    # Normal execution should work
    assert switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Check that action was cleaned up
    assert switchboard_bravo.actionType(action_id) == 0
    assert not switchboard_bravo.hasPendingAction(action_id)


def test_complex_multi_asset_configuration_scenarios(switchboard_bravo, governance, alpha_token, bravo_token, green_token):
    """Test complex scenarios with multiple assets having different configurations"""
    # Add green token with burn capability
    action_id1 = switchboard_bravo.addAsset(
        green_token, [1], 30_00, 20_00, 500, 5000, 0,
        (0, 0, 0, 0, 0, 0),  # no debt terms
        True,   # shouldBurnAsPayment (valid for green)
        False,  # shouldTransferToEndaoment
        False,  # shouldSwapInStabPools
        True,   # shouldAuctionInstantly
        True,   # canDeposit
        True,   # canWithdraw
        False,  # canRedeemCollateral
        True,   # canRedeemInStabPool
        True,   # canBuyInAuction
        True,   # canClaimInStabPool
        0,      # specialStabPoolId
        sender=governance.address
    )
    
    # Add regular token with endaoment transfer
    action_id2 = switchboard_bravo.addAsset(
        alpha_token, [2], 40_00, 35_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # no debt terms
        False,  # shouldBurnAsPayment (invalid for regular token)
        True,   # shouldTransferToEndaoment (valid for regular token)
        False,  # shouldSwapInStabPools
        False,  # shouldAuctionInstantly
        True,   # canDeposit
        True,   # canWithdraw
        False,  # canRedeemCollateral
        True,   # canRedeemInStabPool
        True,   # canBuyInAuction
        True,   # canClaimInStabPool
        0,      # specialStabPoolId
        sender=governance.address
    )
    
    # Add token with full debt functionality
    action_id3 = switchboard_bravo.addAsset(
        bravo_token, [1, 3], 50_00, 30_00, 2000, 20000, 0,  # include vault 1 for staker allocation
        (70_00, 75_00, 85_00, 8_00, 12_00, 3_00),  # full debt terms
        False,  # shouldBurnAsPayment
        False,  # shouldTransferToEndaoment
        True,   # shouldSwapInStabPools (has LTV)
        True,   # shouldAuctionInstantly
        True,   # canDeposit
        True,   # canWithdraw
        True,   # canRedeemCollateral (has LTV)
        True,   # canRedeemInStabPool
        True,   # canBuyInAuction
        True,   # canClaimInStabPool
        0,      # specialStabPoolId
        sender=governance.address
    )
    
    assert action_id1 > 0
    assert action_id2 > 0  
    assert action_id3 > 0
    
    # All should be unique action IDs
    assert len({action_id1, action_id2, action_id3}) == 3


def test_debt_terms_validation_comprehensive_edge_cases(switchboard_bravo, governance, alpha_token):
    """Test comprehensive debt terms validation edge cases"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Test: liq threshold at 95% with 0% fee (valid - avoids LTV deviation issues)
    action_id = switchboard_bravo.setAssetDebtTerms(
        alpha_token, 0, 0, 95_00, 0, 10_00, 2_00,  # LTV=0 to avoid deviation
        sender=governance.address
    )
    assert action_id > 0
    
    # Test: High values but valid combination  
    action_id = switchboard_bravo.setAssetDebtTerms(
        alpha_token, 0, 0, 90_00, 10_00, 100_00, 100_00,  # high values but valid
        sender=governance.address
    )
    assert action_id > 0
    
    # Test: Zero values for optional fields when LTV is zero
    action_id = switchboard_bravo.setAssetDebtTerms(
        alpha_token, 0, 0, 50_00, 0, 0, 0,  # all zeros except liq threshold
        sender=governance.address
    )
    assert action_id > 0


def test_special_stab_pool_id_validation(switchboard_bravo, governance, alpha_token):
    """Test special stab pool ID validation"""
    # Test: invalid special stab pool ID (non-existent vault)
    with boa.reverts("invalid asset"):
        switchboard_bravo.addAsset(
            alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
            (60_00, 70_00, 80_00, 5_00, 10_00, 2_00),  # with LTV
            False, False, True, True, True, True, True, True, True, True, 999,  # invalid stab pool ID
            sender=governance.address
        )
    
    # Test: valid special stab pool ID (existing vault)
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (60_00, 70_00, 80_00, 5_00, 10_00, 2_00),  # with LTV
        False, False, True, True, True, True, True, True, True, True, 1,  # valid stab pool ID
        sender=governance.address
    )
    assert action_id > 0


def test_endaoment_transfer_restrictions(switchboard_bravo, governance, alpha_token):
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
        switchboard_bravo.setCanRedeemCollateralAsset(alpha_token, True, sender=governance.address)


def test_whitelist_interface_validation(switchboard_bravo, governance, alpha_token, mock_rando_contract):
    """Test whitelist interface validation"""
    # First add the asset
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Test invalid whitelist (contract doesn't have proper interface)
    with boa.reverts("invalid whitelist"):
        switchboard_bravo.setWhitelistForAsset(alpha_token, mock_rando_contract, sender=governance.address)
    
    # Test valid whitelist (zero address to remove whitelist)
    action_id = switchboard_bravo.setWhitelistForAsset(alpha_token, ZERO_ADDRESS, sender=governance.address)
    assert action_id > 0


def test_green_token_burn_validation(switchboard_bravo, governance, green_token, savings_green):
    """Test validation rules specific to green tokens for burning"""
    # Test: Green token can burn as payment
    action_id = switchboard_bravo.addAsset(
        green_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        True,   # shouldBurnAsPayment (valid for green token)
        False,  # shouldTransferToEndaoment
        False,  # shouldSwapInStabPools
        True,   # shouldAuctionInstantly
        True,   # canDeposit
        True,   # canWithdraw
        False,  # canRedeemCollateral
        True,   # canRedeemInStabPool
        True,   # canBuyInAuction
        True,   # canClaimInStabPool
        0,      # specialStabPoolId
        sender=governance.address
    )
    assert action_id > 0
    
    # Test: Savings green can also burn as payment
    action_id = switchboard_bravo.addAsset(
        savings_green, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        True,   # shouldBurnAsPayment (valid for savings green)
        False,  # shouldTransferToEndaoment
        False,  # shouldSwapInStabPools
        True,   # shouldAuctionInstantly
        True,   # canDeposit
        True,   # canWithdraw
        False,  # canRedeemCollateral
        True,   # canRedeemInStabPool
        True,   # canBuyInAuction
        True,   # canClaimInStabPool
        0,      # specialStabPoolId
        sender=governance.address
    )
    assert action_id > 0


def test_green_token_endaoment_restrictions(switchboard_bravo, governance, green_token, savings_green, alpha_token):
    """Test that green tokens cannot transfer to endaoment"""
    # Test: Green token cannot transfer to endaoment
    with boa.reverts("invalid asset"):
        switchboard_bravo.addAsset(
            green_token, [1], 50_00, 30_00, 1000, 10000, 0,
            (0, 0, 0, 0, 0, 0),  # empty debt terms
            False,  # shouldBurnAsPayment
            True,   # shouldTransferToEndaoment (invalid for green token)
            False,  # shouldSwapInStabPools
            True,   # shouldAuctionInstantly
            True,   # canDeposit
            True,   # canWithdraw
            False,  # canRedeemCollateral
            True,   # canRedeemInStabPool
            True,   # canBuyInAuction
            True,   # canClaimInStabPool
            0,      # specialStabPoolId
            sender=governance.address
        )
    
    # Test: Savings green cannot transfer to endaoment
    with boa.reverts("invalid asset"):
        switchboard_bravo.addAsset(
            savings_green, [1], 50_00, 30_00, 1000, 10000, 0,
            (0, 0, 0, 0, 0, 0),  # empty debt terms
            False,  # shouldBurnAsPayment
            True,   # shouldTransferToEndaoment (invalid for savings green)
            False,  # shouldSwapInStabPools
            True,   # shouldAuctionInstantly
            True,   # canDeposit
            True,   # canWithdraw
            False,  # canRedeemCollateral
            True,   # canRedeemInStabPool
            True,   # canBuyInAuction
            True,   # canClaimInStabPool
            0,      # specialStabPoolId
            sender=governance.address
        )
    
    # Test: Regular tokens can transfer to endaoment
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False,  # shouldBurnAsPayment
        True,   # shouldTransferToEndaoment (valid for regular token)
        False,  # shouldSwapInStabPools
        True,   # shouldAuctionInstantly
        True,   # canDeposit
        True,   # canWithdraw
        False,  # canRedeemCollateral
        True,   # canRedeemInStabPool
        True,   # canBuyInAuction
        True,   # canClaimInStabPool
        0,      # specialStabPoolId
        sender=governance.address
    )
    assert action_id > 0


def test_nft_asset_restrictions(switchboard_bravo, governance, mock_rando_contract):
    """Test NFT-specific restrictions"""
    # Since there's no dedicated NFT fixture, we'll use a regular contract to test NFT validation
    # Test: NFT cannot swap in stab pools
    with boa.reverts("invalid asset"):
        switchboard_bravo.addAsset(
            mock_rando_contract, [1], 50_00, 30_00, 1000, 10000, 0,
            (60_00, 70_00, 80_00, 5_00, 10_00, 2_00),  # with LTV
            False,  # shouldBurnAsPayment
            False,  # shouldTransferToEndaoment
            True,   # shouldSwapInStabPools (invalid for NFT)
            True,   # shouldAuctionInstantly
            True,   # canDeposit
            True,   # canWithdraw
            True,   # canRedeemCollateral
            True,   # canRedeemInStabPool
            True,   # canBuyInAuction
            True,   # canClaimInStabPool
            0,      # specialStabPoolId
            (False, 0, 0, 0, 0),  # customAuctionParams
            ZERO_ADDRESS,  # whitelist
            True,   # isNft
            sender=governance.address
        )
    
    # Test: NFT cannot redeem collateral
    with boa.reverts("invalid asset"):
        switchboard_bravo.addAsset(
            mock_rando_contract, [1], 50_00, 30_00, 1000, 10000, 0,
            (60_00, 70_00, 80_00, 5_00, 10_00, 2_00),  # with LTV
            False,  # shouldBurnAsPayment
            False,  # shouldTransferToEndaoment
            False,  # shouldSwapInStabPools
            True,   # shouldAuctionInstantly
            True,   # canDeposit
            True,   # canWithdraw
            True,   # canRedeemCollateral (invalid for NFT)
            True,   # canRedeemInStabPool
            True,   # canBuyInAuction
            True,   # canClaimInStabPool
            0,      # specialStabPoolId
            (False, 0, 0, 0, 0),  # customAuctionParams
            ZERO_ADDRESS,  # whitelist
            True,   # isNft
            sender=governance.address
        )
    
    # Test: Valid NFT configuration
    action_id = switchboard_bravo.addAsset(
        mock_rando_contract, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # no debt terms for NFT
        False,  # shouldBurnAsPayment
        False,  # shouldTransferToEndaoment
        False,  # shouldSwapInStabPools
        True,   # shouldAuctionInstantly
        True,   # canDeposit
        True,   # canWithdraw
        False,  # canRedeemCollateral
        True,   # canRedeemInStabPool
        True,   # canBuyInAuction
        True,   # canClaimInStabPool
        0,      # specialStabPoolId
        (False, 0, 0, 0, 0),  # customAuctionParams
        ZERO_ADDRESS,  # whitelist
        True,   # isNft
        sender=governance.address
    )
    assert action_id > 0


def test_min_deposit_balance_validation(switchboard_bravo, governance, alpha_token):
    """Test minDepositBalance validation"""
    # Test adding asset with minDepositBalance > perUserDepositLimit (should fail)
    with boa.reverts("invalid asset"):
        switchboard_bravo.addAsset(
            alpha_token, [1], 50_00, 30_00, 1000, 10000, 2000,  # minDepositBalance > perUserDepositLimit
            (0, 0, 0, 0, 0, 0),  # empty debt terms
            False, False, False, True, True, True, False, True, True, True, 0,
            sender=governance.address
        )
    
    # Add asset with valid minDepositBalance
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 10000, 100000, 5000,  # minDepositBalance < perUserDepositLimit
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    assert action_id > 0
    
    # Check event includes minDepositBalance
    logs = filter_logs(switchboard_bravo, "NewAssetPending")
    assert len(logs) == 1
    log = logs[0]
    assert log.minDepositBalance == 5000
    
    # Execute the action
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Test updating asset deposit params with invalid minDepositBalance
    with boa.reverts("invalid asset deposit params"):
        switchboard_bravo.setAssetDepositParams(
            alpha_token, [1], 50_00, 30_00, 5000, 50000, 6000,  # minDepositBalance > perUserDepositLimit
            sender=governance.address
        )
    
    # Test updating with valid minDepositBalance
    action_id = switchboard_bravo.setAssetDepositParams(
        alpha_token, [1], 50_00, 30_00, 20000, 200000, 15000,  # minDepositBalance < perUserDepositLimit
        sender=governance.address
    )
    assert action_id > 0
    
    # Check event includes minDepositBalance
    logs = filter_logs(switchboard_bravo, "PendingAssetDepositParamsChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.minDepositBalance == 15000


def test_min_deposit_balance_boundary_conditions(switchboard_bravo, governance, alpha_token):
    """Test minDepositBalance boundary conditions"""
    # Test minDepositBalance = 0 (should be valid)
    action_id = switchboard_bravo.addAsset(
        alpha_token, [1], 50_00, 30_00, 1000, 10000, 0,
        (0, 0, 0, 0, 0, 0),  # empty debt terms
        False, False, False, True, True, True, False, True, True, True, 0,
        sender=governance.address
    )
    assert action_id > 0
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Test minDepositBalance = perUserDepositLimit (should be valid)
    action_id = switchboard_bravo.setAssetDepositParams(
        alpha_token, [1], 50_00, 30_00, 5000, 50000, 5000,  # minDepositBalance == perUserDepositLimit
        sender=governance.address
    )
    assert action_id > 0
    
    # Test minDepositBalance slightly above perUserDepositLimit (should fail)
    with boa.reverts("invalid asset deposit params"):
        switchboard_bravo.setAssetDepositParams(
            alpha_token, [1], 50_00, 30_00, 5000, 50000, 5001,  # minDepositBalance > perUserDepositLimit
            sender=governance.address
        )


def test_cannot_set_zero_thresholds_with_positive_ltv(
    governance, switchboard_bravo, alpha_token, mission_control
):
    """Test that validation prevents setting zero thresholds when ltv > 0"""
    
    # First add alpha token as a supported asset
    action_id = switchboard_bravo.addAsset(
        alpha_token,
        [1],  # vaultIds
        50_00,  # stakersPointsAlloc (50%)
        30_00,  # voterPointsAlloc (30%) - total 80% < 100%
        10000 * 10**18,  # perUserDepositLimit
        1000000 * 10**18,  # globalDepositLimit
        0,      # minDepositBalance
        (50_00, 60_00, 70_00, 10_00, 5_00, 1_00),  # Normal debt terms
        False,  # shouldBurnAsPayment
        False,  # shouldTransferToEndaoment
        True,   # shouldSwapInStabPools
        False,  # shouldAuctionInstantly
        True,   # canDeposit
        True,   # canWithdraw
        True,   # canRedeemCollateral
        True,   # canRedeemInStabPool
        True,   # canBuyInAuction
        True,   # canClaimInStabPool
        0,      # specialStabPoolId
        (False, 0, 0, 0, 0),  # customAuctionParams
        ZERO_ADDRESS,  # whitelist
        False,  # isNft
        sender=governance.address
    )
    
    # Fast forward and execute the pending action
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    switchboard_bravo.executePendingAction(action_id, sender=governance.address)
    
    # Verify asset is set up
    assert mission_control.isSupportedAsset(alpha_token)
    
    # Try to set invalid debt terms: ltv > 0 but liqThreshold = 0
    with boa.reverts("invalid debt terms"):
        switchboard_bravo.setAssetDebtTerms(
            alpha_token,
            50_00,  # ltv = 50%
            0,      # redemptionThreshold = 0 (invalid!)
            0,      # liqThreshold = 0 (invalid!)
            10_00,  # liqFee = 10%
            5_00,   # borrowRate = 5%
            1_00,   # daowry = 1%
            sender=governance.address
        )
    
    # Try to set invalid debt terms: ltv > 0 but only redemptionThreshold = 0
    with boa.reverts("invalid debt terms"):
        switchboard_bravo.setAssetDebtTerms(
            alpha_token,
            50_00,  # ltv = 50%
            0,      # redemptionThreshold = 0 (invalid!)
            70_00,  # liqThreshold = 70%
            10_00,  # liqFee = 10%
            5_00,   # borrowRate = 5%
            1_00,   # daowry = 1%
            sender=governance.address
        )
    
    # Valid case: ltv > 0 with proper thresholds should work
    action_id = switchboard_bravo.setAssetDebtTerms(
        alpha_token,
        55_00,  # ltv = 55% (valid change from 50%)
        65_00,  # redemptionThreshold = 65% 
        75_00,  # liqThreshold = 75%
        10_00,  # liqFee = 10%
        5_00,   # borrowRate = 5%
        1_00,   # daowry = 1%
        sender=governance.address
    )
    assert action_id > 0  # Should succeed
