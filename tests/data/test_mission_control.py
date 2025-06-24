import pytest
import boa

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS


############
# Fixtures #
############

@pytest.fixture
def sample_gen_config():
    return (
        10,     # perUserMaxVaults
        5,      # perUserMaxAssetsPerVault
        3600,   # priceStaleTime (1 hour)
        True,   # canDeposit
        True,   # canWithdraw
        True,   # canBorrow
        True,   # canRepay
        True,   # canClaimLoot
        True,   # canLiquidate
        True,   # canRedeemCollateral
        True,   # canRedeemInStabPool
        True,   # canBuyInAuction
        True,   # canClaimInStabPool
    )

@pytest.fixture
def sample_gen_debt_config():
    return (
        10000 * EIGHTEEN_DECIMALS, # perUserDebtLimit
        1000000 * EIGHTEEN_DECIMALS, # globalDebtLimit
        100 * EIGHTEEN_DECIMALS,  # minDebtAmount
        1000,                    # numAllowedBorrowers
        1000 * EIGHTEEN_DECIMALS, # maxBorrowPerInterval
        100,                     # numBlocksPerInterval
        100,                     # minDynamicRateBoost (1%)
        1000,                    # maxDynamicRateBoost (10%)
        10,                      # increasePerDangerBlock (0.1%)
        2000,                    # maxBorrowRate (20%)
        5000,                    # maxLtvDeviation (50%)
        1000,                    # keeperFeeRatio (10%)
        10 * EIGHTEEN_DECIMALS,  # minKeeperFee
        1000 * EIGHTEEN_DECIMALS, # maxKeeperFee
        True,                    # isDaowryEnabled
        500,                     # ltvPaybackBuffer (5%)
        (True, 1000, 5000, 1000, 2000), # genAuctionParams
    )

@pytest.fixture
def sample_asset_config():
    return (
        [1, 2],                  # vaultIds
        100,                     # stakersPointsAlloc
        200,                     # voterPointsAlloc
        1000 * EIGHTEEN_DECIMALS, # perUserDepositLimit
        10000 * EIGHTEEN_DECIMALS, # globalDepositLimit
        0,                         # minDepositBalance
        (5000, 6000, 7000, 1000, 500, 0), # debtTerms
        False,                   # shouldBurnAsPayment
        False,                   # shouldTransferToEndaoment
        True,                    # shouldSwapInStabPools
        False,                   # shouldAuctionInstantly
        True,                    # canDeposit
        True,                    # canWithdraw
        True,                    # canRedeemCollateral
        True,                    # canRedeemInStabPool
        True,                    # canBuyInAuction
        True,                    # canClaimInStabPool
        0,                       # specialStabPoolId
        (True, 1000, 5000, 1000, 2000), # customAuctionParams
        ZERO_ADDRESS,           # whitelist
        False,                   # isNft
    )

@pytest.fixture
def sample_user_config():
    return (
        True,  # canAnyoneDeposit
        True,  # canAnyoneRepayDebt
        True,  # canAnyoneBondForUser
    )

@pytest.fixture
def sample_action_delegation():
    return (
        True,  # canWithdraw
        True,  # canBorrow
        True,  # canClaimFromStabPool
        True,  # canClaimLoot
    )

@pytest.fixture
def sample_ripe_rewards_config():
    return (
        True,                    # arePointsEnabled
        10 * EIGHTEEN_DECIMALS,  # ripePerBlock
        2500,                    # borrowersAlloc (25%)
        2500,                    # stakersAlloc (25%)
        2500,                    # votersAlloc (25%)
        2500,                    # genDepositorsAlloc (25%)
        1000,                    # autoStakeRatio (10%)
        5000,                    # autoStakeDurationRatio (50%)
        1 * EIGHTEEN_DECIMALS,   # stabPoolRipePerDollarClaimed
    )


####################
# Initial State    #
####################

def test_mission_control_initial_state(mission_control):
    """Test initial state of mission control contract."""
    # Should have 1 asset registered initially (index 1, since 0 is not used)
    assert mission_control.getNumAssets() == 0  # actual count
    assert mission_control.numAssets() == 1    # internal counter (1-based)
    
    # Should inherit DeptBasics properly
    assert not mission_control.isPaused()
    assert not mission_control.canMintGreen()
    assert not mission_control.canMintRipe()


#######################
# Global Config Tests #
#######################

def test_mission_control_set_general_config(mission_control, switchboard_alpha, sample_gen_config):
    """Test setting general configuration."""
    mission_control.setGeneralConfig(sample_gen_config, sender=switchboard_alpha.address)
    
    stored_config = mission_control.genConfig()
    assert stored_config.canDeposit == sample_gen_config[3]
    assert stored_config.canWithdraw == sample_gen_config[4]
    assert stored_config.canBorrow == sample_gen_config[5]
    assert stored_config.priceStaleTime == sample_gen_config[2]

def test_mission_control_set_general_config_unauthorized(mission_control, alice, sample_gen_config):
    """Test that only Switchboard can set general config."""
    with boa.reverts("no perms"):
        mission_control.setGeneralConfig(sample_gen_config, sender=alice)

def test_mission_control_set_general_debt_config(mission_control, switchboard_alpha, sample_gen_debt_config):
    """Test setting general debt configuration."""
    mission_control.setGeneralDebtConfig(sample_gen_debt_config, sender=switchboard_alpha.address)
    
    stored_config = mission_control.genDebtConfig()
    assert stored_config.numAllowedBorrowers == sample_gen_debt_config[3]
    assert stored_config.maxBorrowPerInterval == sample_gen_debt_config[4]
    assert stored_config.globalDebtLimit == sample_gen_debt_config[1]

def test_mission_control_set_general_debt_config_unauthorized(mission_control, alice, sample_gen_debt_config):
    """Test that only Switchboard can set general debt config."""
    with boa.reverts("no perms"):
        mission_control.setGeneralDebtConfig(sample_gen_debt_config, sender=alice)

def test_mission_control_keeper_config_validation(mission_control, switchboard_alpha, sample_gen_debt_config):
    """Test that keeper config with all three parameters is properly stored and retrieved."""
    # Set the debt config
    mission_control.setGeneralDebtConfig(sample_gen_debt_config, sender=switchboard_alpha.address)
    
    # Retrieve and validate all keeper fee parameters
    stored_config = mission_control.genDebtConfig()
    assert stored_config.keeperFeeRatio == sample_gen_debt_config[11]  # 1000 (10%)
    assert stored_config.minKeeperFee == sample_gen_debt_config[12]   # 10 * EIGHTEEN_DECIMALS
    assert stored_config.maxKeeperFee == sample_gen_debt_config[13]   # 1000 * EIGHTEEN_DECIMALS
    
    # Verify the values are what we expect
    assert stored_config.keeperFeeRatio == 1000
    assert stored_config.minKeeperFee == 10 * EIGHTEEN_DECIMALS  
    assert stored_config.maxKeeperFee == 1000 * EIGHTEEN_DECIMALS

def test_mission_control_set_hr_config(mission_control, switchboard_alpha, alice):
    """Test setting HR configuration."""
    hr_config = (
        alice,                   # contribTemplate
        1000 * EIGHTEEN_DECIMALS, # maxCompensation
        7200,                    # minCliffLength
        1000,                    # maxStartDelay
        14400,                   # minVestingLength
        518400,                  # maxVestingLength
    )
    
    mission_control.setHrConfig(hr_config, sender=switchboard_alpha.address)
    stored_config = mission_control.hrConfig()
    assert stored_config.contribTemplate == hr_config[0]
    assert stored_config.maxCompensation == hr_config[1]
    assert stored_config.minCliffLength == hr_config[2]

def test_mission_control_set_hr_config_unauthorized(mission_control, alice):
    """Test that only Switchboard can set HR config."""
    hr_config = (alice, 1000 * EIGHTEEN_DECIMALS, 7200, 1000, 14400, 518400)
    with boa.reverts("no perms"):
        mission_control.setHrConfig(hr_config, sender=alice)

def test_mission_control_set_ripe_bond_config(mission_control, switchboard_alpha, alpha_token):
    """Test setting RIPE bond configuration."""
    bond_config = (
        alpha_token.address,      # asset
        1000 * EIGHTEEN_DECIMALS, # amountPerEpoch
        True,                     # canBond
        100,                      # minRipePerUnit
        1000,                     # maxRipePerUnit
        500,                      # maxRipePerUnitLockBonus
        7200,                     # epochLength (blocks)
        True,                     # shouldAutoRestart
        100,                      # restartDelayBlocks
    )
    
    mission_control.setRipeBondConfig(bond_config, sender=switchboard_alpha.address)
    stored_config = mission_control.ripeBondConfig()
    assert stored_config.asset == bond_config[0]
    assert stored_config.amountPerEpoch == bond_config[1]
    assert stored_config.canBond == bond_config[2]

def test_mission_control_set_ripe_bond_config_unauthorized(mission_control, alice, alpha_token):
    """Test that only Switchboard can set RIPE bond config."""
    bond_config = (alpha_token.address, 1000 * EIGHTEEN_DECIMALS, True, 100, 1000, 500, 7200, True, 100)
    with boa.reverts("no perms"):
        mission_control.setRipeBondConfig(bond_config, sender=alice)


######################
# Asset Config Tests #
######################

def test_mission_control_set_asset_config(mission_control, switchboard_alpha, alpha_token, sample_asset_config):
    """Test setting asset configuration."""
    mission_control.setAssetConfig(alpha_token.address, sample_asset_config, sender=switchboard_alpha.address)
    
    stored_config = mission_control.assetConfig(alpha_token.address)
    assert stored_config.canDeposit == sample_asset_config[11]
    assert stored_config.canWithdraw == sample_asset_config[12]
    assert stored_config.perUserDepositLimit == sample_asset_config[3]
    
    # Check asset was registered
    assert mission_control.isSupportedAsset(alpha_token.address)
    assert mission_control.getNumAssets() == 1

def test_mission_control_set_asset_config_unauthorized(mission_control, alice, alpha_token, sample_asset_config):
    """Test that only Switchboard can set asset config."""
    with boa.reverts("no perms"):
        mission_control.setAssetConfig(alpha_token.address, sample_asset_config, sender=alice)

def test_mission_control_asset_registration(mission_control, switchboard_alpha, alpha_token, bravo_token, sample_asset_config):
    """Test asset registration functionality."""
    # Initially no assets
    assert mission_control.getNumAssets() == 0
    assert not mission_control.isSupportedAsset(alpha_token.address)
    
    # Add first asset
    mission_control.setAssetConfig(alpha_token.address, sample_asset_config, sender=switchboard_alpha.address)
    assert mission_control.getNumAssets() == 1
    assert mission_control.isSupportedAsset(alpha_token.address)
    assert mission_control.assets(1) == alpha_token.address
    assert mission_control.indexOfAsset(alpha_token.address) == 1
    
    # Add second asset
    mission_control.setAssetConfig(bravo_token.address, sample_asset_config, sender=switchboard_alpha.address)
    assert mission_control.getNumAssets() == 2
    assert mission_control.isSupportedAsset(bravo_token.address)
    assert mission_control.assets(2) == bravo_token.address
    assert mission_control.indexOfAsset(bravo_token.address) == 2

def test_mission_control_deregister_asset(mission_control, switchboard_alpha, alpha_token, bravo_token, charlie_token, sample_asset_config):
    """Test asset deregistration functionality."""
    # Add multiple assets
    mission_control.setAssetConfig(alpha_token.address, sample_asset_config, sender=switchboard_alpha.address)
    mission_control.setAssetConfig(bravo_token.address, sample_asset_config, sender=switchboard_alpha.address)
    mission_control.setAssetConfig(charlie_token.address, sample_asset_config, sender=switchboard_alpha.address)
    
    assert mission_control.getNumAssets() == 3
    
    # Deregister middle asset
    success = mission_control.deregisterAsset(bravo_token.address, sender=switchboard_alpha.address)
    assert success
    assert mission_control.getNumAssets() == 2
    assert not mission_control.isSupportedAsset(bravo_token.address)
    assert mission_control.indexOfAsset(bravo_token.address) == 0
    
    # Check that charlie moved to bravo's position
    assert mission_control.assets(2) == charlie_token.address
    assert mission_control.indexOfAsset(charlie_token.address) == 2

def test_mission_control_deregister_asset_nonexistent(mission_control, switchboard_alpha, alpha_token):
    """Test deregistering non-existent asset."""
    success = mission_control.deregisterAsset(alpha_token.address, sender=switchboard_alpha.address)
    assert not success

def test_mission_control_deregister_asset_unauthorized(mission_control, alice, alpha_token):
    """Test that only Switchboard can deregister assets."""
    with boa.reverts("no perms"):
        mission_control.deregisterAsset(alpha_token.address, sender=alice)


#####################
# User Config Tests #
#####################

def test_mission_control_set_user_config_switchboard(mission_control, switchboard_alpha, alice, sample_user_config):
    """Test setting user config via Switchboard."""
    mission_control.setUserConfig(alice, sample_user_config, sender=switchboard_alpha.address)
    
    stored_config = mission_control.userConfig(alice)
    assert stored_config.canAnyoneDeposit == sample_user_config[0]
    assert stored_config.canAnyoneRepayDebt == sample_user_config[1]
    assert stored_config.canAnyoneBondForUser == sample_user_config[2]

def test_mission_control_set_user_config_teller(mission_control, teller, alice, sample_user_config):
    """Test setting user config via Teller."""
    mission_control.setUserConfig(alice, sample_user_config, sender=teller.address)
    
    stored_config = mission_control.userConfig(alice)
    assert stored_config.canAnyoneDeposit == sample_user_config[0]
    assert stored_config.canAnyoneRepayDebt == sample_user_config[1]

def test_mission_control_set_user_config_unauthorized(mission_control, alice, sample_user_config):
    """Test that only Switchboard or Teller can set user config."""
    with boa.reverts("no perms"):
        mission_control.setUserConfig(alice, sample_user_config, sender=alice)

def test_mission_control_set_user_delegation(mission_control, switchboard_alpha, alice, bob, sample_action_delegation):
    """Test setting user delegation."""
    mission_control.setUserDelegation(alice, bob, sample_action_delegation, sender=switchboard_alpha.address)
    
    stored_delegation = mission_control.userDelegation(alice, bob)
    assert stored_delegation.canWithdraw == sample_action_delegation[0]
    assert stored_delegation.canBorrow == sample_action_delegation[1]
    assert stored_delegation.canClaimFromStabPool == sample_action_delegation[2]
    assert stored_delegation.canClaimLoot == sample_action_delegation[3]

def test_mission_control_set_user_delegation_teller(mission_control, teller, alice, bob, sample_action_delegation):
    """Test setting user delegation via Teller."""
    mission_control.setUserDelegation(alice, bob, sample_action_delegation, sender=teller.address)
    
    stored_delegation = mission_control.userDelegation(alice, bob)
    assert stored_delegation.canWithdraw == sample_action_delegation[0]

def test_mission_control_set_user_delegation_unauthorized(mission_control, alice, bob, sample_action_delegation):
    """Test that only Switchboard or Teller can set user delegation."""
    with boa.reverts("no perms"):
        mission_control.setUserDelegation(alice, bob, sample_action_delegation, sender=alice)


########################
# Rewards Config Tests #
########################

def test_mission_control_set_ripe_rewards_config(mission_control, switchboard_alpha, sample_ripe_rewards_config):
    """Test setting RIPE rewards configuration."""
    mission_control.setRipeRewardsConfig(sample_ripe_rewards_config, sender=switchboard_alpha.address)
    
    stored_config = mission_control.rewardsConfig()
    assert stored_config.arePointsEnabled == sample_ripe_rewards_config[0]
    assert stored_config.ripePerBlock == sample_ripe_rewards_config[1]
    assert stored_config.borrowersAlloc == sample_ripe_rewards_config[2]

def test_mission_control_set_ripe_rewards_config_unauthorized(mission_control, alice, sample_ripe_rewards_config):
    """Test that only Switchboard can set rewards config."""
    with boa.reverts("no perms"):
        mission_control.setRipeRewardsConfig(sample_ripe_rewards_config, sender=alice)

def test_mission_control_points_allocs_tracking(mission_control, switchboard_alpha, alpha_token, bravo_token, sample_asset_config):
    """Test that points allocations are tracked correctly."""
    # Initially no allocations
    total_allocs = mission_control.totalPointsAllocs()
    assert total_allocs.stakersPointsAllocTotal == 0
    assert total_allocs.voterPointsAllocTotal == 0
    
    # Add first asset with points
    asset_config_1 = list(sample_asset_config)
    asset_config_1[1] = 100  # stakersPointsAlloc
    asset_config_1[2] = 200  # voterPointsAlloc
    
    mission_control.setAssetConfig(alpha_token.address, tuple(asset_config_1), sender=switchboard_alpha.address)
    
    total_allocs = mission_control.totalPointsAllocs()
    assert total_allocs.stakersPointsAllocTotal == 100
    assert total_allocs.voterPointsAllocTotal == 200
    
    # Add second asset
    asset_config_2 = list(sample_asset_config)
    asset_config_2[1] = 150  # stakersPointsAlloc
    asset_config_2[2] = 250  # voterPointsAlloc
    
    mission_control.setAssetConfig(bravo_token.address, tuple(asset_config_2), sender=switchboard_alpha.address)
    
    total_allocs = mission_control.totalPointsAllocs()
    assert total_allocs.stakersPointsAllocTotal == 250  # 100 + 150
    assert total_allocs.voterPointsAllocTotal == 450   # 200 + 250
    
    # Update first asset allocation
    asset_config_1[1] = 50   # reduce stakersPointsAlloc
    asset_config_1[2] = 100  # reduce voterPointsAlloc
    
    mission_control.setAssetConfig(alpha_token.address, tuple(asset_config_1), sender=switchboard_alpha.address)
    
    total_allocs = mission_control.totalPointsAllocs()
    assert total_allocs.stakersPointsAllocTotal == 200  # 50 + 150
    assert total_allocs.voterPointsAllocTotal == 350    # 100 + 250


######################
# View Function Tests #
######################

def test_mission_control_get_teller_deposit_config(mission_control, switchboard_alpha, alpha_token, alice, sample_gen_config, sample_asset_config):
    """Test getting teller deposit configuration."""
    # Set up configs
    mission_control.setGeneralConfig(sample_gen_config, sender=switchboard_alpha.address)
    mission_control.setAssetConfig(alpha_token.address, sample_asset_config, sender=switchboard_alpha.address)
    
    # Test with vault that supports the asset
    config = mission_control.getTellerDepositConfig(1, alpha_token.address, alice)
    assert config.canDepositGeneral
    assert config.canDepositAsset
    assert config.doesVaultSupportAsset  # vault 1 is in sample_asset_config vaultIds
    assert config.isUserAllowed  # no whitelist set
    assert config.perUserDepositLimit == sample_asset_config[3]
    
    # Test with vault that doesn't support the asset
    config = mission_control.getTellerDepositConfig(999, alpha_token.address, alice)
    assert not config.doesVaultSupportAsset

def test_mission_control_get_teller_withdraw_config(mission_control, switchboard_alpha, alice, bob, alpha_token, sample_gen_config, sample_asset_config, sample_action_delegation):
    """Test getting teller withdraw configuration."""
    # Set up configs
    mission_control.setGeneralConfig(sample_gen_config, sender=switchboard_alpha.address)
    mission_control.setAssetConfig(alpha_token.address, sample_asset_config, sender=switchboard_alpha.address)
    
    # Test withdrawal for self
    config = mission_control.getTellerWithdrawConfig(alpha_token.address, alice, alice)
    assert config.canWithdrawGeneral
    assert config.canWithdrawAsset
    assert config.isUserAllowed
    assert config.canWithdrawForUser
    
    # Test withdrawal for another user without delegation
    config = mission_control.getTellerWithdrawConfig(alpha_token.address, alice, bob)
    assert not config.canWithdrawForUser  # no delegation set
    
    # Set delegation and test again
    mission_control.setUserDelegation(alice, bob, sample_action_delegation, sender=switchboard_alpha.address)
    config = mission_control.getTellerWithdrawConfig(alpha_token.address, alice, bob)
    assert config.canWithdrawForUser

def test_mission_control_get_borrow_config(mission_control, switchboard_alpha, alice, bob, sample_gen_config, sample_gen_debt_config, sample_action_delegation):
    """Test getting borrow configuration."""
    # Set up configs
    mission_control.setGeneralConfig(sample_gen_config, sender=switchboard_alpha.address)
    mission_control.setGeneralDebtConfig(sample_gen_debt_config, sender=switchboard_alpha.address)
    
    # Test borrowing for self
    config = mission_control.getBorrowConfig(alice, alice)
    assert config.canBorrow
    assert config.canBorrowForUser
    assert config.numAllowedBorrowers == sample_gen_debt_config[3]
    assert config.globalDebtLimit == sample_gen_debt_config[1]
    
    # Test borrowing for another user without delegation
    config = mission_control.getBorrowConfig(alice, bob)
    assert not config.canBorrowForUser
    
    # Set delegation and test again
    mission_control.setUserDelegation(alice, bob, sample_action_delegation, sender=switchboard_alpha.address)
    config = mission_control.getBorrowConfig(alice, bob)
    assert config.canBorrowForUser

def test_mission_control_get_debt_terms(mission_control, switchboard_alpha, alpha_token, sample_asset_config):
    """Test getting debt terms for an asset."""
    mission_control.setAssetConfig(alpha_token.address, sample_asset_config, sender=switchboard_alpha.address)
    
    debt_terms = mission_control.getDebtTerms(alpha_token.address)
    expected_terms = sample_asset_config[6]  # debtTerms
    assert debt_terms.ltv == expected_terms[0]
    assert debt_terms.redemptionThreshold == expected_terms[1]
    assert debt_terms.liqThreshold == expected_terms[2]
    assert debt_terms.liqFee == expected_terms[3]
    assert debt_terms.borrowRate == expected_terms[4]
    assert debt_terms.daowry == expected_terms[5]

def test_mission_control_get_repay_config(mission_control, alice):
    """Test getting repay configuration."""
    # Test with default user config
    config = mission_control.getRepayConfig(alice)
    assert not config.canRepay  # default gen config
    assert not config.canAnyoneRepayDebt  # default user config
    

def test_mission_control_get_repay_config_with_user_settings(mission_control, switchboard_alpha, alice, sample_gen_config, sample_user_config):
    """Test repay config with user settings."""
    mission_control.setGeneralConfig(sample_gen_config, sender=switchboard_alpha.address)
    mission_control.setUserConfig(alice, sample_user_config, sender=switchboard_alpha.address)
    
    config = mission_control.getRepayConfig(alice)
    assert config.canRepay
    assert config.canAnyoneRepayDebt


######################
# Vault Config Tests #
######################

def test_mission_control_set_ripe_gov_vault_config(mission_control, switchboard_alpha, ripe_token):
    """Test setting RIPE governance vault configuration."""
    lock_terms = (
        7200,   # minLockDuration (blocks)
        518400, # maxLockDuration (blocks) 
        2000,   # maxLockBoost (20%)
        True,   # canExit
        500,    # exitFee (5%)
    )
    
    mission_control.setRipeGovVaultConfig(
        ripe_token.address,
        1000,  # assetWeight
        True,  # shouldFreezeWhenBadDebt
        lock_terms,
        sender=switchboard_alpha.address
    )
    
    stored_config = mission_control.ripeGovVaultConfig(ripe_token.address)
    assert stored_config.assetWeight == 1000
    assert stored_config.shouldFreezeWhenBadDebt
    assert stored_config.lockTerms.minLockDuration == 7200
    assert stored_config.lockTerms.maxLockDuration == 518400

def test_mission_control_set_ripe_gov_vault_config_unauthorized(mission_control, alice, ripe_token):
    """Test that only Switchboard can set RIPE gov vault config."""
    lock_terms = (7200, 518400, 2000, True, 500)
    with boa.reverts("no perms"):
        mission_control.setRipeGovVaultConfig(ripe_token.address, 1000, True, lock_terms, sender=alice)

def test_mission_control_set_stab_claim_rewards_config(mission_control, setRipeRewardsConfig):
    """Test setting stability pool claim rewards configuration."""
    # Set up rewards config with stab pool rewards
    setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=100 * EIGHTEEN_DECIMALS)
    
    stored_config = mission_control.rewardsConfig()
    assert stored_config.stabPoolRipePerDollarClaimed == 100 * EIGHTEEN_DECIMALS

def test_mission_control_set_stab_claim_rewards_config_unauthorized(mission_control, alice):
    """Test that only Switchboard can set stab claim rewards config."""
    with boa.reverts("no perms"):
        mission_control.setRipeRewardsConfig((True, 10, 25_00, 25_00, 25_00, 25_00, 0, 0, 100 * EIGHTEEN_DECIMALS), sender=alice)

def test_mission_control_set_priority_liq_asset_vaults(mission_control, switchboard_alpha, alpha_token):
    """Test setting priority liquidation asset vaults."""
    priority_vaults = [
        (1, alpha_token.address),  # (vaultId, asset)
        (2, alpha_token.address),
    ]
    
    mission_control.setPriorityLiqAssetVaults(priority_vaults, sender=switchboard_alpha.address)
    
    stored_vaults = mission_control.getPriorityLiqAssetVaults()
    assert len(stored_vaults) == 2
    assert stored_vaults[0].vaultId == 1
    assert stored_vaults[0].asset == alpha_token.address

def test_mission_control_set_priority_liq_asset_vaults_unauthorized(mission_control, alice, alpha_token):
    """Test that only Switchboard can set priority liq asset vaults."""
    priority_vaults = [(1, alpha_token.address)]
    with boa.reverts("no perms"):
        mission_control.setPriorityLiqAssetVaults(priority_vaults, sender=alice)

def test_mission_control_set_priority_stab_vaults(mission_control, switchboard_alpha, alpha_token):
    """Test setting priority stability pool vaults."""
    priority_vaults = [
        (3, alpha_token.address),  # (vaultId, asset)
        (4, alpha_token.address),
    ]
    
    mission_control.setPriorityStabVaults(priority_vaults, sender=switchboard_alpha.address)
    
    stored_vaults = mission_control.getPriorityStabVaults()
    assert len(stored_vaults) == 2
    assert stored_vaults[0].vaultId == 3
    assert stored_vaults[0].asset == alpha_token.address

def test_mission_control_set_priority_stab_vaults_unauthorized(mission_control, alice, alpha_token):
    """Test that only Switchboard can set priority stab vaults."""
    priority_vaults = [(3, alpha_token.address)]
    with boa.reverts("no perms"):
        mission_control.setPriorityStabVaults(priority_vaults, sender=alice)


##########################
# Access Control Tests  #
##########################

def test_mission_control_set_can_perform_lite_action(mission_control, switchboard_alpha, alice):
    """Test setting lite action permissions."""
    # Initially false
    assert not mission_control.canPerformLiteAction(alice)
    
    # Set to true
    mission_control.setCanPerformLiteAction(alice, True, sender=switchboard_alpha.address)
    assert mission_control.canPerformLiteAction(alice)
    
    # Set back to false
    mission_control.setCanPerformLiteAction(alice, False, sender=switchboard_alpha.address)
    assert not mission_control.canPerformLiteAction(alice)

def test_mission_control_set_can_perform_lite_action_unauthorized(mission_control, alice):
    """Test that only Switchboard can set lite action permissions."""
    with boa.reverts("no perms"):
        mission_control.setCanPerformLiteAction(alice, True, sender=alice)


#################
# Other Tests   #
#################

def test_mission_control_set_underscore_registry(mission_control, switchboard_alpha, alpha_token):
    """Test setting underscore registry address."""
    mission_control.setUnderscoreRegistry(alpha_token.address, sender=switchboard_alpha.address)
    assert mission_control.underscoreRegistry() == alpha_token.address

def test_mission_control_set_underscore_registry_unauthorized(mission_control, alice, alpha_token):
    """Test that only Switchboard can set underscore registry."""
    with boa.reverts("no perms"):
        mission_control.setUnderscoreRegistry(alpha_token.address, sender=alice)

def test_mission_control_set_priority_price_source_ids(mission_control, switchboard_alpha):
    """Test setting priority price source IDs."""
    price_source_ids = [1, 2, 3, 4]
    mission_control.setPriorityPriceSourceIds(price_source_ids, sender=switchboard_alpha.address)
    
    stored_ids = mission_control.getPriorityPriceSourceIds()
    assert len(stored_ids) == 4
    assert stored_ids[0] == 1
    assert stored_ids[3] == 4

def test_mission_control_set_priority_price_source_ids_unauthorized(mission_control, alice):
    """Test that only Switchboard can set priority price source IDs."""
    with boa.reverts("no perms"):
        mission_control.setPriorityPriceSourceIds([1, 2, 3], sender=alice)


###########################
# Complex View Functions #
###########################

def test_mission_control_get_gen_liq_config(mission_control, switchboard_alpha, sample_gen_config, sample_gen_debt_config, alpha_token):
    """Test getting general liquidation configuration."""
    # Set up configs
    mission_control.setGeneralConfig(sample_gen_config, sender=switchboard_alpha.address)
    mission_control.setGeneralDebtConfig(sample_gen_debt_config, sender=switchboard_alpha.address)
    
    # Set priority vaults
    priority_liq_vaults = [(1, alpha_token.address)]
    priority_stab_vaults = [(2, alpha_token.address)]
    mission_control.setPriorityLiqAssetVaults(priority_liq_vaults, sender=switchboard_alpha.address)
    mission_control.setPriorityStabVaults(priority_stab_vaults, sender=switchboard_alpha.address)
    
    config = mission_control.getGenLiqConfig()
    assert config.canLiquidate
    assert config.keeperFeeRatio == sample_gen_debt_config[11]
    assert config.minKeeperFee == sample_gen_debt_config[12]
    assert config.maxKeeperFee == sample_gen_debt_config[13]
    assert len(config.priorityLiqAssetVaults) == 1
    assert len(config.priorityStabVaults) == 1

def test_mission_control_get_asset_liq_config(mission_control, switchboard_alpha, alpha_token, sample_asset_config):
    """Test getting asset liquidation configuration."""
    mission_control.setAssetConfig(alpha_token.address, sample_asset_config, sender=switchboard_alpha.address)
    
    config = mission_control.getAssetLiqConfig(alpha_token.address)
    assert config.hasConfig
    assert config.shouldBurnAsPayment == sample_asset_config[7]
    assert config.shouldTransferToEndaoment == sample_asset_config[8]
    assert config.shouldSwapInStabPools == sample_asset_config[9]
    assert config.shouldAuctionInstantly == sample_asset_config[10]

def test_mission_control_get_stab_pool_claims_config(mission_control, switchboard_alpha, alice, bob, alpha_token, ripe_token, sample_gen_config, sample_asset_config, sample_action_delegation, setRipeRewardsConfig):
    """Test getting stability pool claims configuration."""
    # Set up configs
    mission_control.setGeneralConfig(sample_gen_config, sender=switchboard_alpha.address)
    mission_control.setAssetConfig(alpha_token.address, sample_asset_config, sender=switchboard_alpha.address)
    
    # Set RipeRewardsConfig with stab pool rewards and autoStakeDurationRatio=0
    setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=100 * EIGHTEEN_DECIMALS, _autoStakeDurationRatio=0)
    
    # Set RIPE gov vault config for lock duration calculation
    lock_terms = (7200, 518400, 2000, True, 500)
    mission_control.setRipeGovVaultConfig(ripe_token.address, 1000, True, lock_terms, sender=switchboard_alpha.address)
    
    # Test claiming for self
    config = mission_control.getStabPoolClaimsConfig(alpha_token.address, alice, alice, ripe_token.address)
    assert config.canClaimInStabPoolGeneral
    assert config.canClaimInStabPoolAsset
    assert config.canClaimFromStabPoolForUser
    assert config.rewardsLockDuration == 7200  # minLockDuration when autoStakeDurationRatio is 0
    
    # Test claiming for another user without delegation
    config = mission_control.getStabPoolClaimsConfig(alpha_token.address, alice, bob, ripe_token.address)
    assert not config.canClaimFromStabPoolForUser
    
    # Set delegation and test again
    mission_control.setUserDelegation(alice, bob, sample_action_delegation, sender=switchboard_alpha.address)
    config = mission_control.getStabPoolClaimsConfig(alpha_token.address, alice, bob, ripe_token.address)
    assert config.canClaimFromStabPoolForUser

def test_mission_control_get_claim_loot_config(mission_control, switchboard_alpha, alice, bob, ripe_token, sample_gen_config, sample_ripe_rewards_config, sample_action_delegation):
    """Test getting claim loot configuration."""
    # Set up configs
    mission_control.setGeneralConfig(sample_gen_config, sender=switchboard_alpha.address)
    mission_control.setRipeRewardsConfig(sample_ripe_rewards_config, sender=switchboard_alpha.address)
    
    # Set RIPE gov vault config
    lock_terms = (7200, 518400, 2000, True, 500)
    mission_control.setRipeGovVaultConfig(ripe_token.address, 1000, True, lock_terms, sender=switchboard_alpha.address)
    
    # Test claiming for self
    config = mission_control.getClaimLootConfig(alice, alice, ripe_token.address)
    assert config.canClaimLoot
    assert config.canClaimLootForUser
    assert config.autoStakeRatio == sample_ripe_rewards_config[6]
    assert config.rewardsLockDuration == 255600  # calculated: 7200 + (511200 * 50%)
    
    # Test claiming for another user without delegation
    config = mission_control.getClaimLootConfig(alice, bob, ripe_token.address)
    assert not config.canClaimLootForUser
    
    # Set delegation and test again
    mission_control.setUserDelegation(alice, bob, sample_action_delegation, sender=switchboard_alpha.address)
    config = mission_control.getClaimLootConfig(alice, bob, ripe_token.address)
    assert config.canClaimLootForUser

def test_mission_control_get_rewards_config(mission_control, switchboard_alpha, alpha_token, sample_ripe_rewards_config, sample_asset_config):
    """Test getting rewards configuration."""
    # Set rewards config
    mission_control.setRipeRewardsConfig(sample_ripe_rewards_config, sender=switchboard_alpha.address)
    
    # Add asset with points allocation
    asset_config = list(sample_asset_config)
    asset_config[1] = 300  # stakersPointsAlloc
    asset_config[2] = 400  # voterPointsAlloc
    mission_control.setAssetConfig(alpha_token.address, tuple(asset_config), sender=switchboard_alpha.address)
    
    config = mission_control.getRewardsConfig()
    assert config.arePointsEnabled
    assert config.ripePerBlock == 10 * EIGHTEEN_DECIMALS
    assert config.borrowersAlloc == 2500
    assert config.stakersPointsAllocTotal == 300
    assert config.voterPointsAllocTotal == 400

def test_mission_control_get_deposit_points_config(mission_control, switchboard_alpha, alpha_token, sample_asset_config):
    """Test getting deposit points configuration."""
    mission_control.setAssetConfig(alpha_token.address, sample_asset_config, sender=switchboard_alpha.address)
    
    config = mission_control.getDepositPointsConfig(alpha_token.address)
    assert config.stakersPointsAlloc == sample_asset_config[1]
    assert config.voterPointsAlloc == sample_asset_config[2]
    assert config.isNft == sample_asset_config[20]

def test_mission_control_get_price_config(mission_control, switchboard_alpha, sample_gen_config):
    """Test getting price configuration."""
    mission_control.setGeneralConfig(sample_gen_config, sender=switchboard_alpha.address)
    
    price_source_ids = [1, 2, 3]
    mission_control.setPriorityPriceSourceIds(price_source_ids, sender=switchboard_alpha.address)
    
    config = mission_control.getPriceConfig()
    assert config.staleTime == sample_gen_config[2]
    assert len(config.priorityPriceSourceIds) == 3

def test_mission_control_get_purchase_ripe_bond_config(mission_control, switchboard_alpha, alice, ripe_token, alpha_token, sample_user_config):
    """Test getting purchase RIPE bond configuration."""
    # Set up bond config
    bond_config = (alpha_token.address, 1000 * EIGHTEEN_DECIMALS, True, 100, 1000, 500, 7200, True, 100)
    mission_control.setRipeBondConfig(bond_config, sender=switchboard_alpha.address)
    
    # Set RIPE gov vault config
    lock_terms = (7200, 518400, 2000, True, 500)
    mission_control.setRipeGovVaultConfig(ripe_token.address, 1000, True, lock_terms, sender=switchboard_alpha.address)
    
    # Set user config
    mission_control.setUserConfig(alice, sample_user_config, sender=switchboard_alpha.address)
    
    config = mission_control.getPurchaseRipeBondConfig(alice)
    assert config.asset == alpha_token.address
    assert config.amountPerEpoch == 1000 * EIGHTEEN_DECIMALS
    assert config.canBond
    assert config.minLockDuration == 7200
    assert config.maxLockDuration == 518400
    assert config.canAnyoneBondForUser

def test_mission_control_get_dynamic_borrow_rate_config(mission_control, switchboard_alpha, sample_gen_debt_config):
    """Test getting dynamic borrow rate configuration."""
    mission_control.setGeneralDebtConfig(sample_gen_debt_config, sender=switchboard_alpha.address)
    
    config = mission_control.getDynamicBorrowRateConfig()
    assert config.minDynamicRateBoost == sample_gen_debt_config[6]
    assert config.maxDynamicRateBoost == sample_gen_debt_config[7]
    assert config.increasePerDangerBlock == sample_gen_debt_config[8]
    assert config.maxBorrowRate == sample_gen_debt_config[9]


#######################
# Helper Function Tests #
#######################

def test_mission_control_vault_support_check(mission_control, switchboard_alpha, alpha_token, sample_asset_config):
    """Test vault support checking functionality."""
    # Initially asset not supported
    assert not mission_control.isSupportedAsset(alpha_token.address)
    assert not mission_control.isSupportedAssetInVault(1, alpha_token.address)
    
    # Add asset config with specific vault IDs
    mission_control.setAssetConfig(alpha_token.address, sample_asset_config, sender=switchboard_alpha.address)
    
    # Now asset should be supported
    assert mission_control.isSupportedAsset(alpha_token.address)
    assert mission_control.isSupportedAssetInVault(1, alpha_token.address)  # vault 1 in config
    assert mission_control.isSupportedAssetInVault(2, alpha_token.address)  # vault 2 in config
    assert not mission_control.isSupportedAssetInVault(999, alpha_token.address)  # vault 999 not in config

def test_mission_control_get_first_vault_id_for_asset(mission_control, switchboard_alpha, alpha_token, sample_asset_config):
    """Test getting first vault ID for an asset."""
    # Initially no vault ID
    assert mission_control.getFirstVaultIdForAsset(alpha_token.address) == 0
    
    # Add asset config
    mission_control.setAssetConfig(alpha_token.address, sample_asset_config, sender=switchboard_alpha.address)
    
    # Should return first vault ID from config
    assert mission_control.getFirstVaultIdForAsset(alpha_token.address) == 1  # first in [1, 2]

def test_mission_control_underscore_access_check(mission_control, switchboard_alpha, alice, bob, sample_user_config, sample_action_delegation):
    """Test underscore protocol access checking."""
    # Initially no access
    assert not mission_control.doesUndyLegoHaveAccess(alice, bob)
    
    # Set partial user config (missing some required settings)
    partial_config = (True, False, True)  # canAnyoneDeposit=True, canAnyoneRepayDebt=False
    mission_control.setUserConfig(alice, partial_config, sender=switchboard_alpha.address)
    assert not mission_control.doesUndyLegoHaveAccess(alice, bob)
    
    # Set full user config
    mission_control.setUserConfig(alice, sample_user_config, sender=switchboard_alpha.address)
    
    # Set partial delegation (missing some required settings)
    partial_delegation = (True, False, True, True)  # canBorrow=False
    mission_control.setUserDelegation(alice, bob, partial_delegation, sender=switchboard_alpha.address)
    assert not mission_control.doesUndyLegoHaveAccess(alice, bob)
    
    # Set full delegation
    mission_control.setUserDelegation(alice, bob, sample_action_delegation, sender=switchboard_alpha.address)
    assert mission_control.doesUndyLegoHaveAccess(alice, bob)


#########################
# DeptBasics Inherited  #
#########################

def test_mission_control_can_mint_tokens(mission_control):
    """Test inherited minting permissions."""
    assert not mission_control.canMintGreen()
    assert not mission_control.canMintRipe()

def test_mission_control_pause_functionality(mission_control, switchboard_alpha):
    """Test inherited pause functionality."""
    # Initially not paused
    assert not mission_control.isPaused()
    
    # Pause
    mission_control.pause(True, sender=switchboard_alpha.address)
    assert mission_control.isPaused()
    
    # Unpause
    mission_control.pause(False, sender=switchboard_alpha.address)
    assert not mission_control.isPaused()

def test_mission_control_recover_funds(mission_control, switchboard_alpha, alice, alpha_token, governance):
    """Test inherited fund recovery functionality."""
    # Setup: send some tokens to mission control
    initial_balance = 1000 * EIGHTEEN_DECIMALS
    alpha_token.mint(alice, initial_balance, sender=governance.address)
    alpha_token.transfer(mission_control.address, initial_balance, sender=alice)
    
    # Check initial state
    assert alpha_token.balanceOf(mission_control.address) == initial_balance
    initial_alice_balance = alpha_token.balanceOf(alice)
    
    # Recover funds
    mission_control.recoverFunds(alice, alpha_token.address, sender=switchboard_alpha.address)
    
    # Check funds were recovered
    assert alpha_token.balanceOf(mission_control.address) == 0
    assert alpha_token.balanceOf(alice) == initial_alice_balance + initial_balance

def test_mission_control_recover_funds_unauthorized(mission_control, alice, alpha_token):
    """Test that only Switchboard can recover funds."""
    with boa.reverts("no perms"):
        mission_control.recoverFunds(alice, alpha_token.address, sender=alice)


######################
# Edge Cases & Limits #
######################

def test_mission_control_max_priority_price_sources(mission_control, switchboard_alpha):
    """Test maximum priority price sources limit."""
    # Create max allowed price source IDs (10)
    max_ids = list(range(1, 11))  # [1, 2, 3, ..., 10]
    mission_control.setPriorityPriceSourceIds(max_ids, sender=switchboard_alpha.address)
    
    stored_ids = mission_control.getPriorityPriceSourceIds()
    assert len(stored_ids) == 10

def test_mission_control_max_priority_vaults(mission_control, switchboard_alpha, alpha_token):
    """Test maximum priority vaults limit."""
    # Create max allowed priority vaults (20)
    max_vaults = [(i, alpha_token.address) for i in range(1, 21)]
    mission_control.setPriorityLiqAssetVaults(max_vaults, sender=switchboard_alpha.address)
    
    stored_vaults = mission_control.getPriorityLiqAssetVaults()
    assert len(stored_vaults) == 20

def test_mission_control_empty_configurations(mission_control, alice):
    """Test behavior with empty/default configurations."""
    # Test getting configs for non-existent asset
    debt_terms = mission_control.getDebtTerms(alice)  # using alice as dummy asset
    assert debt_terms.ltv == 0
    assert debt_terms.redemptionThreshold == 0
    
    # Test getting config for non-existent user
    user_config = mission_control.userConfig(alice)
    assert not user_config.canAnyoneDeposit
    assert not user_config.canAnyoneRepayDebt
    
    # Test delegation for non-existent delegation
    delegation = mission_control.userDelegation(alice, alice)
    assert not delegation.canWithdraw
    assert not delegation.canBorrow

def test_mission_control_comprehensive_config_flow(mission_control, switchboard_alpha, alice, alpha_token, sample_gen_config, sample_asset_config, sample_user_config):
    """Test comprehensive configuration workflow."""
    # 1. Set general config
    mission_control.setGeneralConfig(sample_gen_config, sender=switchboard_alpha.address)
    
    # 2. Set asset config (should register asset)
    mission_control.setAssetConfig(alpha_token.address, sample_asset_config, sender=switchboard_alpha.address)
    assert mission_control.isSupportedAsset(alpha_token.address)
    
    # 3. Set user config
    mission_control.setUserConfig(alice, sample_user_config, sender=switchboard_alpha.address)
    
    # 4. Test integrated view functions
    deposit_config = mission_control.getTellerDepositConfig(1, alpha_token.address, alice)
    assert deposit_config.canDepositGeneral
    assert deposit_config.canDepositAsset
    assert deposit_config.doesVaultSupportAsset
    assert deposit_config.canAnyoneDeposit
    
    # 5. Deregister asset
    success = mission_control.deregisterAsset(alpha_token.address, sender=switchboard_alpha.address)
    assert success
    assert not mission_control.isSupportedAsset(alpha_token.address)
    
    # 6. Test that asset-specific configs now reflect deregistration
    deposit_config = mission_control.getTellerDepositConfig(1, alpha_token.address, alice)
    # Note: Asset config remains but asset is no longer in registry
    # The doesVaultSupportAsset still works because assetConfig is not cleared
    # But isSupportedAsset should return False
    assert deposit_config.doesVaultSupportAsset  # config still exists
    assert not mission_control.isSupportedAsset(alpha_token.address)  # but not in registry


####################
# Boundary Testing #
####################

def test_mission_control_multiple_asset_management(mission_control, switchboard_alpha, alpha_token, bravo_token, charlie_token, sample_asset_config):
    """Test managing multiple assets simultaneously."""
    assets = [alpha_token, bravo_token, charlie_token]
    
    # Add all assets
    for i, asset in enumerate(assets):
        mission_control.setAssetConfig(asset.address, sample_asset_config, sender=switchboard_alpha.address)
        assert mission_control.getNumAssets() == i + 1
        assert mission_control.assets(i + 1) == asset.address
    
    # Update middle asset with different config
    modified_config = list(sample_asset_config)
    modified_config[3] = 2000 * EIGHTEEN_DECIMALS  # different perUserDepositLimit
    mission_control.setAssetConfig(bravo_token.address, tuple(modified_config), sender=switchboard_alpha.address)
    
    # Check configs are independent
    alpha_config = mission_control.assetConfig(alpha_token.address)
    bravo_config = mission_control.assetConfig(bravo_token.address)
    assert alpha_config.perUserDepositLimit == sample_asset_config[3]
    assert bravo_config.perUserDepositLimit == 2000 * EIGHTEEN_DECIMALS
    
    # Remove middle asset and verify integrity
    mission_control.deregisterAsset(bravo_token.address, sender=switchboard_alpha.address)
    assert mission_control.getNumAssets() == 2
    assert not mission_control.isSupportedAsset(bravo_token.address)
    assert mission_control.isSupportedAsset(alpha_token.address)
    assert mission_control.isSupportedAsset(charlie_token.address)
