import pytest
import boa

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS
from conf_utils import filter_logs
from contracts.modules import Contributor


@pytest.fixture(scope="module")
def valid_contributor_terms():
    """Valid contributor terms for testing"""
    return {
        "owner": "0x" + "11" * 20,
        "manager": "0x" + "22" * 20,
        "compensation": 500000 * EIGHTEEN_DECIMALS,  # 500K tokens
        "startDelay": 7 * 24 * 3600,  # 7 days in seconds
        "vestingLength": 2 * 365 * 24 * 3600,  # 2 years in seconds
        "cliffLength": 90 * 24 * 3600,  # 90 days in seconds
        "unlockLength": 365 * 24 * 3600,  # 1 year in seconds
        "depositLockDuration": 100,  # 100 blocks
    }


@pytest.fixture(scope="module")
def setupHrConfig(mission_control, switchboard_delta, contributor_template):
    """Setup HR configuration in MissionControl"""
    def setupHrConfig(
        _contribTemplate=None,
        _maxCompensation=1000000 * EIGHTEEN_DECIMALS,  # 1M tokens
        _minCliffLength=30 * 24 * 3600,  # 30 days
        _maxStartDelay=90 * 24 * 3600,  # 90 days
        _minVestingLength=365 * 24 * 3600,  # 1 year
        _maxVestingLength=4 * 365 * 24 * 3600,  # 4 years
    ):
        # Use contributor_template address if not provided
        template_addr = _contribTemplate if _contribTemplate else contributor_template.address
        
        hr_config = (
            template_addr,
            _maxCompensation,
            _minCliffLength,
            _maxStartDelay,
            _minVestingLength,
            _maxVestingLength,
        )
        
        # Call setHrConfig from switchboard (authorized caller)
        mission_control.setHrConfig(hr_config, sender=switchboard_delta.address)
        return hr_config
    
    yield setupHrConfig


@pytest.fixture(scope="module")
def setupLedgerBalance(ledger, switchboard_delta):
    """Setup ledger with sufficient RIPE balance for HR"""
    def setupLedgerBalance(_amount=1000000 * EIGHTEEN_DECIMALS):  # 1M tokens default
        ledger.setRipeAvailForHr(_amount, sender=switchboard_delta.address)
        return _amount
    
    yield setupLedgerBalance


@pytest.fixture(scope="module")
def setupRipeGovVaultConfig(mission_control, setGeneralConfig, setAssetConfig, switchboard_alpha, ripe_token):
    """Setup RipeGov vault configuration for RIPE token"""
    def setupRipeGovVaultConfig(
        _assetWeight = 100_00,
        _minLockDuration = 100,
        _maxLockDuration = 1000,
        _maxLockBoost = 200_00,
        _exitFee = 10_00,
        _canExit = True,
    ):
        setGeneralConfig()

        # Set up lock terms
        lock_terms = (
            _minLockDuration,
            _maxLockDuration,
            _maxLockBoost,
            _canExit,
            _exitFee,
        )

        # Set RipeGov vault config with asset weight
        mission_control.setRipeGovVaultConfig(
            ripe_token, 
            _assetWeight,
            False,
            lock_terms, 
            sender=switchboard_alpha.address
        )
        
        # Configure ripe_token for vault_id 2 (ripe_gov_vault)
        setAssetConfig(ripe_token, _vaultIds=[2])

    yield setupRipeGovVaultConfig


@pytest.fixture(scope="module")
def deployedContributor(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
    governance
):
    """Deploy a contributor contract for testing"""
    def deployedContributor(_terms=None):
        terms = _terms if _terms else valid_contributor_terms
        
        # Setup HR configuration and ledger balance
        setupHrConfig()
        setupLedgerBalance(terms["compensation"])
        
        # Initiate contributor
        action_id = human_resources.initiateNewContributor(
            terms["owner"],
            terms["manager"],
            terms["compensation"],
            terms["startDelay"],
            terms["vestingLength"],
            terms["cliffLength"],
            terms["unlockLength"],
            terms["depositLockDuration"],
            sender=governance.address
        )
        
        # Wait for timelock and confirm
        boa.env.time_travel(blocks=human_resources.actionTimeLock())
        human_resources.confirmNewContributor(action_id, sender=governance.address)
        
        # Get contributor address from event
        events = filter_logs(human_resources, "NewContributorConfirmed")
        contributor_address = events[0].contributorAddr
        
        return contributor_address
    
    yield deployedContributor


@pytest.fixture  
def contributor_contract(deployedContributor):
    """Get a deployed contributor contract instance"""
    contributor_addr = deployedContributor()
    return Contributor.at(contributor_addr)


@pytest.fixture
def owner_address(valid_contributor_terms):
    """Get the owner address from terms"""
    return valid_contributor_terms["owner"]


@pytest.fixture  
def manager_address(valid_contributor_terms):
    """Get the manager address from terms"""
    return valid_contributor_terms["manager"]


# Test Initialization


def test_contributor_initialization_success(
    contributor_contract,
    valid_contributor_terms,
    owner_address,
    manager_address
):
    """Test successful contributor contract initialization"""
    
    # Check basic state variables
    assert contributor_contract.owner() == owner_address
    assert contributor_contract.manager() == manager_address
    assert contributor_contract.compensation() == valid_contributor_terms["compensation"]
    assert contributor_contract.depositLockDuration() == valid_contributor_terms["depositLockDuration"]
    
    # Check timing calculations
    current_time = boa.env.evm.patch.timestamp
    expected_start_time = current_time + valid_contributor_terms["startDelay"]
    expected_end_time = expected_start_time + valid_contributor_terms["vestingLength"]
    expected_cliff_time = expected_start_time + valid_contributor_terms["cliffLength"]
    expected_unlock_time = expected_start_time + valid_contributor_terms["unlockLength"]
    
    assert contributor_contract.startTime() == expected_start_time
    assert contributor_contract.endTime() == expected_end_time
    assert contributor_contract.cliffTime() == expected_cliff_time
    assert contributor_contract.unlockTime() == expected_unlock_time
    
    # Check initial states
    assert contributor_contract.totalClaimed() == 0
    assert contributor_contract.isFrozen() == False
    assert contributor_contract.hasPendingRipeTransfer() == False
    assert contributor_contract.hasPendingOwnerChange() == False


def test_contributor_initialization_invalid_terms(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    governance,
    valid_contributor_terms
):
    """Test that contributor initialization fails with invalid terms"""
    
    setupHrConfig()
    setupLedgerBalance(valid_contributor_terms["compensation"])
    
    # Test zero compensation - should fail at HR level
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(
            valid_contributor_terms["owner"],
            valid_contributor_terms["manager"],
            0,  # Zero compensation
            valid_contributor_terms["startDelay"],
            valid_contributor_terms["vestingLength"],
            valid_contributor_terms["cliffLength"],
            valid_contributor_terms["unlockLength"],
            valid_contributor_terms["depositLockDuration"],
            sender=governance.address
        )


# Test Cash Ripe Check


def test_contributor_cash_ripe_check_by_owner_before_vesting(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address
):
    """Test cashing ripe check by owner before vesting starts"""
    
    setupRipeGovVaultConfig()
    
    # Before vesting starts, claimable should be 0
    claimable = contributor_contract.getClaimable()
    assert claimable == 0
    
    # Cash check should return 0
    result = contributor_contract.cashRipeCheck(sender=owner_address)
    assert result == 0


def test_contributor_cash_ripe_check_after_cliff(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    valid_contributor_terms
):
    """Test cashing ripe check after cliff period"""
    
    setupRipeGovVaultConfig()
    
    # Fast forward past start and cliff time
    start_delay = valid_contributor_terms["startDelay"]
    cliff_length = valid_contributor_terms["cliffLength"]
    
    # Move past start + cliff + some additional time for vesting
    boa.env.time_travel(seconds=start_delay + cliff_length + (30 * 24 * 3600))  # +30 days
    
    # Should have some claimable amount
    claimable = contributor_contract.getClaimable()
    assert claimable > 0
    
    # Cash the check
    result = contributor_contract.cashRipeCheck(sender=owner_address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "RipeCheckCashed")
    assert len(events) == 1
    event = events[0]
    assert event.owner == owner_address
    assert event.cashedBy == owner_address
    assert event.amount == claimable
    
    assert result == claimable
    
    # Total claimed should be updated
    assert contributor_contract.totalClaimed() == claimable


def test_contributor_cash_ripe_check_by_manager(
    contributor_contract,
    setupRipeGovVaultConfig,
    manager_address,
    valid_contributor_terms
):
    """Test cashing ripe check by manager"""
    
    setupRipeGovVaultConfig()
    
    # Fast forward to have some vesting
    start_delay = valid_contributor_terms["startDelay"]
    cliff_length = valid_contributor_terms["cliffLength"]
    boa.env.time_travel(seconds=start_delay + cliff_length + (30 * 24 * 3600))
    
    claimable = contributor_contract.getClaimable()
    assert claimable > 0
    
    # Manager can cash check
    result = contributor_contract.cashRipeCheck(sender=manager_address)
    assert result == claimable


def test_contributor_cash_ripe_check_unauthorized(
    contributor_contract,
    setupRipeGovVaultConfig,
    alice
):
    """Test that unauthorized users cannot cash ripe check"""
    
    setupRipeGovVaultConfig()
    
    with boa.reverts("no perms"):
        contributor_contract.cashRipeCheck(sender=alice)


def test_contributor_cash_ripe_check_when_frozen(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_alpha,
    owner_address,
    valid_contributor_terms
):
    """Test that cash ripe check returns 0 when contract is frozen"""
    
    setupRipeGovVaultConfig()
    
    # Fast forward to have vesting
    start_delay = valid_contributor_terms["startDelay"]
    cliff_length = valid_contributor_terms["cliffLength"]
    boa.env.time_travel(seconds=start_delay + cliff_length + (30 * 24 * 3600))
    
    # Freeze the contract
    contributor_contract.setIsFrozen(True, sender=switchboard_alpha.address)
    
    # Should return 0 when frozen
    result = contributor_contract.cashRipeCheck(sender=owner_address)
    assert result == 0


# Test RIPE Transfer Workflow


def test_contributor_initiate_ripe_transfer_success(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    valid_contributor_terms
):
    """Test successful initiation of RIPE transfer"""
    
    setupRipeGovVaultConfig()
    
    # Give contributor some RIPE balance first
    deposit_amount = 1000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        contributor_contract.address, ripe_token, deposit_amount, sender=teller.address
    )
    
    # Fast forward past unlock time
    start_delay = valid_contributor_terms["startDelay"]
    unlock_length = valid_contributor_terms["unlockLength"]
    boa.env.time_travel(seconds=start_delay + unlock_length + 1)
    
    # Should not have pending transfer initially
    assert contributor_contract.hasPendingRipeTransfer() == False
    
    # Initiate transfer
    contributor_contract.initiateRipeTransfer(sender=owner_address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "RipeTransferInitiated")
    assert len(events) == 1
    event = events[0]
    assert event.owner == owner_address
    assert event.initiatedBy == owner_address
    
    # Should now have pending transfer
    assert contributor_contract.hasPendingRipeTransfer() == True


def test_contributor_initiate_ripe_transfer_before_unlock(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address
):
    """Test that RIPE transfer fails before unlock time"""
    
    setupRipeGovVaultConfig()
    
    with boa.reverts("time not past unlock"):
        contributor_contract.initiateRipeTransfer(sender=owner_address)


def test_contributor_initiate_ripe_transfer_unauthorized(
    contributor_contract,
    setupRipeGovVaultConfig,
    alice
):
    """Test that unauthorized users cannot initiate RIPE transfer"""
    
    setupRipeGovVaultConfig()
    
    with boa.reverts("no perms"):
        contributor_contract.initiateRipeTransfer(sender=alice)


def test_contributor_initiate_ripe_transfer_when_frozen(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_alpha,
    owner_address
):
    """Test that RIPE transfer initiation fails when frozen"""
    
    setupRipeGovVaultConfig()
    
    # Freeze the contract
    contributor_contract.setIsFrozen(True, sender=switchboard_alpha.address)
    
    with boa.reverts("contract frozen"):
        contributor_contract.initiateRipeTransfer(sender=owner_address)


def test_contributor_confirm_ripe_transfer_success(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    valid_contributor_terms
):
    """Test successful confirmation of RIPE transfer"""
    
    setupRipeGovVaultConfig()
    
    # Setup RIPE balance and initiate transfer
    deposit_amount = 1000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        contributor_contract.address, ripe_token, deposit_amount, sender=teller.address
    )
    
    # Fast forward past unlock time
    start_delay = valid_contributor_terms["startDelay"]
    unlock_length = valid_contributor_terms["unlockLength"]
    boa.env.time_travel(seconds=start_delay + unlock_length + 1)
    
    # Initiate transfer
    contributor_contract.initiateRipeTransfer(sender=owner_address)
    
    # Fast forward past key action delay
    key_action_delay = contributor_contract.keyActionDelay()
    boa.env.time_travel(blocks=key_action_delay)
    
    # Confirm transfer
    contributor_contract.confirmRipeTransfer(sender=owner_address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "RipeTransferConfirmed")
    assert len(events) == 1
    event = events[0]
    assert event.recipient == owner_address
    assert event.confirmedBy == owner_address
    
    # Should no longer have pending transfer
    assert contributor_contract.hasPendingRipeTransfer() == False


def test_contributor_confirm_ripe_transfer_too_early(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    valid_contributor_terms
):
    """Test that RIPE transfer confirmation fails before delay"""
    
    setupRipeGovVaultConfig()
    
    # Setup and initiate transfer
    deposit_amount = 1000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        contributor_contract.address, ripe_token, deposit_amount, sender=teller.address
    )
    
    start_delay = valid_contributor_terms["startDelay"]
    unlock_length = valid_contributor_terms["unlockLength"]
    boa.env.time_travel(seconds=start_delay + unlock_length + 1)
    
    contributor_contract.initiateRipeTransfer(sender=owner_address)
    
    # Try to confirm immediately
    with boa.reverts("time delay not reached"):
        contributor_contract.confirmRipeTransfer(sender=owner_address)


def test_contributor_cancel_ripe_transfer_by_owner(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    valid_contributor_terms
):
    """Test cancellation of RIPE transfer by owner"""
    
    setupRipeGovVaultConfig()
    
    # Setup and initiate transfer
    deposit_amount = 1000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        contributor_contract.address, ripe_token, deposit_amount, sender=teller.address
    )
    
    start_delay = valid_contributor_terms["startDelay"]
    unlock_length = valid_contributor_terms["unlockLength"]
    boa.env.time_travel(seconds=start_delay + unlock_length + 1)
    
    contributor_contract.initiateRipeTransfer(sender=owner_address)
    
    # Cancel transfer
    contributor_contract.cancelRipeTransfer(sender=owner_address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "RipeTransferCancelled")
    assert len(events) == 1
    
    # Should no longer have pending transfer
    assert contributor_contract.hasPendingRipeTransfer() == False


def test_contributor_cancel_ripe_transfer_no_pending(
    contributor_contract,
    owner_address
):
    """Test that cancelling RIPE transfer fails when no pending transfer"""
    
    with boa.reverts("no pending transfer"):
        contributor_contract.cancelRipeTransfer(sender=owner_address)


# Test Ownership Change Workflow


def test_contributor_change_ownership_success(
    contributor_contract,
    owner_address,
    alice
):
    """Test successful ownership change initiation"""
    
    # Should not have pending change initially
    assert contributor_contract.hasPendingOwnerChange() == False
    
    # Initiate ownership change
    contributor_contract.changeOwnership(alice, sender=owner_address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "OwnershipChangeInitiated")
    assert len(events) == 1
    event = events[0]
    assert event.prevOwner == owner_address
    assert event.newOwner == alice
    
    # Should now have pending change
    assert contributor_contract.hasPendingOwnerChange() == True


def test_contributor_change_ownership_unauthorized(
    contributor_contract,
    alice,
    bob
):
    """Test that only owner can initiate ownership change"""
    
    with boa.reverts("no perms"):
        contributor_contract.changeOwnership(bob, sender=alice)


def test_contributor_change_ownership_invalid_new_owner(
    contributor_contract,
    owner_address
):
    """Test that ownership change fails with invalid new owner"""
    
    # Cannot change to zero address
    with boa.reverts("invalid new owner"):
        contributor_contract.changeOwnership(ZERO_ADDRESS, sender=owner_address)
    
    # Cannot change to same owner
    with boa.reverts("invalid new owner"):
        contributor_contract.changeOwnership(owner_address, sender=owner_address)


def test_contributor_confirm_ownership_change_success(
    contributor_contract,
    owner_address,
    alice
):
    """Test successful ownership change confirmation"""
    
    # Initiate change
    contributor_contract.changeOwnership(alice, sender=owner_address)
    
    # Fast forward past delay
    key_action_delay = contributor_contract.keyActionDelay()
    boa.env.time_travel(blocks=key_action_delay)
    
    # New owner confirms
    contributor_contract.confirmOwnershipChange(sender=alice)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "OwnershipChangeConfirmed")
    assert len(events) == 1
    event = events[0]
    assert event.prevOwner == owner_address
    assert event.newOwner == alice
    
    # Owner should be changed
    assert contributor_contract.owner() == alice
    assert contributor_contract.hasPendingOwnerChange() == False


def test_contributor_confirm_ownership_change_wrong_user(
    contributor_contract,
    owner_address,
    alice,
    bob
):
    """Test that only new owner can confirm ownership change"""
    
    # Initiate change
    contributor_contract.changeOwnership(alice, sender=owner_address)
    
    # Fast forward past delay
    key_action_delay = contributor_contract.keyActionDelay()
    boa.env.time_travel(blocks=key_action_delay)
    
    # Wrong user tries to confirm
    with boa.reverts("only new owner can confirm"):
        contributor_contract.confirmOwnershipChange(sender=bob)


def test_contributor_cancel_ownership_change_success(
    contributor_contract,
    owner_address,
    alice
):
    """Test successful ownership change cancellation"""
    
    # Initiate change
    contributor_contract.changeOwnership(alice, sender=owner_address)
    
    # Cancel change
    contributor_contract.cancelOwnershipChange(sender=owner_address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "OwnershipChangeCancelled")
    assert len(events) == 1
    
    # Should no longer have pending change
    assert contributor_contract.hasPendingOwnerChange() == False


# Test Admin Functions


def test_contributor_set_manager_by_owner(
    contributor_contract,
    owner_address,
    alice
):
    """Test setting manager by owner"""
    
    # Set new manager
    contributor_contract.setManager(alice, sender=owner_address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "ManagerModified")
    assert len(events) == 1
    event = events[0]
    assert event.newManager == alice
    assert event.changedBy == owner_address
    
    # Manager should be updated
    assert contributor_contract.manager() == alice


def test_contributor_set_manager_unauthorized(
    contributor_contract,
    alice,
    bob
):
    """Test that unauthorized users cannot set manager"""
    
    with boa.reverts("no perms"):
        contributor_contract.setManager(bob, sender=alice)


def test_contributor_set_manager_zero_address(
    contributor_contract,
    owner_address
):
    """Test that manager cannot be set to zero address"""
    
    with boa.reverts("cannot be 0x0"):
        contributor_contract.setManager(ZERO_ADDRESS, sender=owner_address)


def test_contributor_set_key_action_delay_success(
    contributor_contract,
    owner_address
):
    """Test setting key action delay"""
    
    # Get current delay
    current_delay = contributor_contract.keyActionDelay()
    new_delay = current_delay + 10
    
    # Set new delay
    contributor_contract.setKeyActionDelay(new_delay, sender=owner_address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "KeyActionDelaySet")
    assert len(events) == 1
    event = events[0]
    assert event.numBlocks == new_delay
    
    # Delay should be updated
    assert contributor_contract.keyActionDelay() == new_delay


def test_contributor_set_key_action_delay_unauthorized(
    contributor_contract,
    alice
):
    """Test that only owner can set key action delay"""
    
    with boa.reverts("no perms"):
        contributor_contract.setKeyActionDelay(100, sender=alice)


# Test HR Admin Functions


def test_contributor_set_frozen_by_switchboard(
    contributor_contract,
    switchboard_alpha
):
    """Test freezing contract by switchboard"""
    
    # Initially not frozen
    assert contributor_contract.isFrozen() == False
    
    # Freeze contract
    result = contributor_contract.setIsFrozen(True, sender=switchboard_alpha.address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "FreezeModified")
    assert len(events) == 1
    event = events[0]
    assert event.isFrozen == True
    
    assert result == True
    assert contributor_contract.isFrozen() == True
    
    # Unfreeze contract
    contributor_contract.setIsFrozen(False, sender=switchboard_alpha.address)
    assert contributor_contract.isFrozen() == False


def test_contributor_set_frozen_unauthorized(
    contributor_contract,
    alice
):
    """Test that only authorized addresses can freeze contract"""
    
    with boa.reverts("no perms"):
        contributor_contract.setIsFrozen(True, sender=alice)


def test_contributor_cancel_paycheck_success(
    contributor_contract,
    switchboard_alpha,
    setupRipeGovVaultConfig,
    valid_contributor_terms
):
    """Test successful paycheck cancellation after cliff - should reach cliff"""
    
    setupRipeGovVaultConfig()
    
    # Fast forward to after start and cliff but before end
    start_delay = valid_contributor_terms["startDelay"]
    cliff_length = valid_contributor_terms["cliffLength"]
    boa.env.time_travel(seconds=start_delay + cliff_length + (10 * 24 * 3600))  # +10 days past cliff
    
    # Store initial state
    original_compensation = contributor_contract.compensation()
    original_total_claimed = contributor_contract.totalClaimed()
    owner_address = contributor_contract.owner()
    
    # Calculate expected values - since we're past cliff, it should cash the check first
    claimable_before_cancel = contributor_contract.getClaimable()
    expected_total_claimed_after_cancel = original_total_claimed + claimable_before_cancel
    expected_forfeited = original_compensation - expected_total_claimed_after_cancel
    
    # Cancel paycheck
    contributor_contract.cancelPaycheck(sender=switchboard_alpha.address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "RipePaycheckCancelled")
    assert len(events) == 1
    event = events[0]
    
    # Verify all event fields comprehensively
    assert event.owner == owner_address
    assert event.forfeitedAmount == expected_forfeited
    assert event.didReachCliff == True  # We're past cliff time
    
    # Verify contract state changes
    assert contributor_contract.compensation() == expected_total_claimed_after_cancel
    assert contributor_contract.endTime() == boa.env.evm.patch.timestamp
    assert contributor_contract.totalClaimed() == expected_total_claimed_after_cancel


def test_contributor_cancel_paycheck_before_cliff(
    contributor_contract,
    switchboard_alpha,
    setupRipeGovVaultConfig,
    valid_contributor_terms
):
    """Test paycheck cancellation before cliff - should not reach cliff"""
    
    setupRipeGovVaultConfig()
    
    # Fast forward to after start but before cliff
    start_delay = valid_contributor_terms["startDelay"]
    cliff_length = valid_contributor_terms["cliffLength"]
    boa.env.time_travel(seconds=start_delay + (cliff_length // 2))  # Halfway to cliff
    
    # Store initial state
    original_compensation = contributor_contract.compensation()
    original_total_claimed = contributor_contract.totalClaimed()
    owner_address = contributor_contract.owner()
    
    # Before cliff, no cashing should occur, so forfeit should be full compensation
    expected_forfeited = original_compensation
    
    # Cancel paycheck
    contributor_contract.cancelPaycheck(sender=switchboard_alpha.address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "RipePaycheckCancelled")
    assert len(events) == 1
    event = events[0]
    
    # Verify all event fields comprehensively
    assert event.owner == owner_address
    assert event.forfeitedAmount == expected_forfeited
    assert event.didReachCliff == False  # We're before cliff time
    
    # Verify contract state changes
    assert contributor_contract.compensation() == 0  # All forfeited
    assert contributor_contract.endTime() == boa.env.evm.patch.timestamp
    assert contributor_contract.totalClaimed() == original_total_claimed  # No change since no cash


def test_contributor_cancel_paycheck_after_end(
    contributor_contract,
    switchboard_alpha,
    setupRipeGovVaultConfig,
    valid_contributor_terms
):
    """Test that paycheck cancellation fails after vesting ends"""
    
    setupRipeGovVaultConfig()
    
    # Fast forward past end time
    start_delay = valid_contributor_terms["startDelay"]
    vesting_length = valid_contributor_terms["vestingLength"]
    boa.env.time_travel(seconds=start_delay + vesting_length + 1)
    
    with boa.reverts("cannot cancel"):
        contributor_contract.cancelPaycheck(sender=switchboard_alpha.address)


def test_contributor_cancel_paycheck_unauthorized(
    contributor_contract,
    alice
):
    """Test that only HR admin can cancel paycheck"""
    
    with boa.reverts("no perms"):
        contributor_contract.cancelPaycheck(sender=alice)


# Test View Functions


def test_contributor_get_claimable_before_start(
    contributor_contract
):
    """Test getClaimable before vesting starts"""
    
    claimable = contributor_contract.getClaimable()
    assert claimable == 0


def test_contributor_get_claimable_during_vesting(
    contributor_contract,
    valid_contributor_terms
):
    """Test getClaimable during vesting period"""
    
    # Fast forward to middle of vesting
    start_delay = valid_contributor_terms["startDelay"]
    cliff_length = valid_contributor_terms["cliffLength"]
    boa.env.time_travel(seconds=start_delay + cliff_length + (30 * 24 * 3600))
    
    claimable = contributor_contract.getClaimable()
    total_vested = contributor_contract.getTotalVested()
    total_claimed = contributor_contract.totalClaimed()
    
    assert claimable == total_vested - total_claimed
    assert claimable > 0


def test_contributor_get_total_vested_linear_progression(
    contributor_contract,
    valid_contributor_terms
):
    """Test that getTotalVested progresses linearly"""
    
    compensation = valid_contributor_terms["compensation"]
    start_delay = valid_contributor_terms["startDelay"]
    vesting_length = valid_contributor_terms["vestingLength"]
    
    # At start of vesting
    boa.env.time_travel(seconds=start_delay)
    vested_at_start = contributor_contract.getTotalVested()
    assert vested_at_start == 0
    
    # At 25% through vesting
    boa.env.time_travel(seconds=vesting_length // 4)
    vested_at_25_percent = contributor_contract.getTotalVested()
    expected_25_percent = compensation // 4
    # Allow for small rounding differences
    assert abs(vested_at_25_percent - expected_25_percent) < compensation // 100
    
    # At 50% through vesting
    boa.env.time_travel(seconds=vesting_length // 4)
    vested_at_50_percent = contributor_contract.getTotalVested()
    expected_50_percent = compensation // 2
    assert abs(vested_at_50_percent - expected_50_percent) < compensation // 100
    
    # At end of vesting
    boa.env.time_travel(seconds=vesting_length // 2)
    vested_at_end = contributor_contract.getTotalVested()
    assert vested_at_end == compensation


def test_contributor_get_unvested_comp(
    contributor_contract,
    valid_contributor_terms
):
    """Test getUnvestedComp calculation"""
    
    compensation = valid_contributor_terms["compensation"]
    start_delay = valid_contributor_terms["startDelay"]
    vesting_length = valid_contributor_terms["vestingLength"]
    
    # At start
    boa.env.time_travel(seconds=start_delay)
    unvested = contributor_contract.getUnvestedComp()
    assert unvested == compensation
    
    # At 50% through vesting
    boa.env.time_travel(seconds=vesting_length // 2)
    unvested = contributor_contract.getUnvestedComp()
    expected_unvested = compensation // 2
    assert abs(unvested - expected_unvested) < compensation // 100
    
    # At end
    boa.env.time_travel(seconds=vesting_length // 2)
    unvested = contributor_contract.getUnvestedComp()
    assert unvested == 0


def test_contributor_get_remaining_vesting_length(
    contributor_contract,
    valid_contributor_terms
):
    """Test getRemainingVestingLength calculation"""
    
    start_delay = valid_contributor_terms["startDelay"]
    vesting_length = valid_contributor_terms["vestingLength"]
    
    # Before start
    remaining = contributor_contract.getRemainingVestingLength()
    expected_remaining = start_delay + vesting_length
    assert remaining == expected_remaining
    
    # At 25% through vesting
    boa.env.time_travel(seconds=start_delay + (vesting_length // 4))
    remaining = contributor_contract.getRemainingVestingLength()
    expected_remaining = (vesting_length * 3) // 4
    assert remaining == expected_remaining
    
    # After end
    boa.env.time_travel(seconds=vesting_length)
    remaining = contributor_contract.getRemainingVestingLength()
    assert remaining == 0


def test_contributor_get_remaining_unlock_length(
    contributor_contract,
    valid_contributor_terms
):
    """Test getRemainingUnlockLength calculation"""
    
    start_delay = valid_contributor_terms["startDelay"]
    unlock_length = valid_contributor_terms["unlockLength"]
    
    # Before start
    remaining = contributor_contract.getRemainingUnlockLength()
    expected_remaining = start_delay + unlock_length
    assert remaining == expected_remaining
    
    # At 50% through unlock period
    boa.env.time_travel(seconds=start_delay + (unlock_length // 2))
    remaining = contributor_contract.getRemainingUnlockLength()
    expected_remaining = unlock_length // 2
    assert remaining == expected_remaining
    
    # After unlock
    boa.env.time_travel(seconds=unlock_length)
    remaining = contributor_contract.getRemainingUnlockLength()
    assert remaining == 0


# Test Complex Scenarios


def test_contributor_complex_vesting_and_claims_scenario(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    valid_contributor_terms
):
    """Test complex scenario with multiple claims throughout vesting"""
    
    setupRipeGovVaultConfig()
    
    compensation = valid_contributor_terms["compensation"]
    start_delay = valid_contributor_terms["startDelay"]
    cliff_length = valid_contributor_terms["cliffLength"]
    vesting_length = valid_contributor_terms["vestingLength"]
    
    # Fast forward past cliff
    boa.env.time_travel(seconds=start_delay + cliff_length)
    
    # First claim at cliff
    first_claim = contributor_contract.cashRipeCheck(sender=owner_address)
    assert first_claim > 0
    assert contributor_contract.totalClaimed() == first_claim
    
    # Fast forward to 50% through vesting
    boa.env.time_travel(seconds=(vesting_length - cliff_length) // 2)
    
    # Second claim
    claimable_before = contributor_contract.getClaimable()
    second_claim = contributor_contract.cashRipeCheck(sender=owner_address)
    assert second_claim == claimable_before
    assert contributor_contract.totalClaimed() == first_claim + second_claim
    
    # Fast forward to end of vesting
    boa.env.time_travel(seconds=(vesting_length - cliff_length) // 2)
    
    # Final claim
    final_claim = contributor_contract.cashRipeCheck(sender=owner_address)
    total_claimed = contributor_contract.totalClaimed()
    
    # Total claimed should equal total compensation
    assert total_claimed == compensation
    
    # No more claimable
    assert contributor_contract.getClaimable() == 0


def test_contributor_ownership_change_blocks_ripe_transfer(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    alice,
    valid_contributor_terms
):
    """Test that pending ownership change blocks RIPE transfer"""
    
    setupRipeGovVaultConfig()
    
    # Setup RIPE balance
    deposit_amount = 1000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        contributor_contract.address, ripe_token, deposit_amount, sender=teller.address
    )
    
    # Fast forward past unlock
    start_delay = valid_contributor_terms["startDelay"]
    unlock_length = valid_contributor_terms["unlockLength"]
    boa.env.time_travel(seconds=start_delay + unlock_length + 1)
    
    # Initiate ownership change
    contributor_contract.changeOwnership(alice, sender=owner_address)
    
    # Should not be able to initiate RIPE transfer
    with boa.reverts("cannot do with pending ownership change"):
        contributor_contract.initiateRipeTransfer(sender=owner_address)


# Test RIPE Transfer with _shouldCashCheck Parameter


def test_contributor_initiate_ripe_transfer_without_cashing(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    valid_contributor_terms
):
    """Test initiating RIPE transfer without cashing check first"""
    
    setupRipeGovVaultConfig()
    
    # Give contributor some RIPE balance
    deposit_amount = 1000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        contributor_contract.address, ripe_token, deposit_amount, sender=teller.address
    )
    
    # Fast forward past unlock time and generate some claimable
    start_delay = valid_contributor_terms["startDelay"]
    unlock_length = valid_contributor_terms["unlockLength"]
    boa.env.time_travel(seconds=start_delay + unlock_length + (30 * 24 * 3600))
    
    # Should have claimable amount but we won't cash it
    claimable_before = contributor_contract.getClaimable()
    total_claimed_before = contributor_contract.totalClaimed()
    assert claimable_before > 0
    
    # Initiate transfer without cashing check
    contributor_contract.initiateRipeTransfer(False, sender=owner_address)  # _shouldCashCheck=False
    
    # Check that no cashing occurred
    assert contributor_contract.getClaimable() == claimable_before
    assert contributor_contract.totalClaimed() == total_claimed_before
    
    # Should still have pending transfer
    assert contributor_contract.hasPendingRipeTransfer() == True


def test_contributor_confirm_ripe_transfer_without_cashing(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    valid_contributor_terms
):
    """Test confirming RIPE transfer without cashing check"""
    
    setupRipeGovVaultConfig()
    
    # Setup RIPE balance and initiate transfer
    deposit_amount = 1000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        contributor_contract.address, ripe_token, deposit_amount, sender=teller.address
    )
    
    # Fast forward past unlock time
    start_delay = valid_contributor_terms["startDelay"]
    unlock_length = valid_contributor_terms["unlockLength"]
    boa.env.time_travel(seconds=start_delay + unlock_length + (30 * 24 * 3600))
    
    # Initiate transfer without cashing
    contributor_contract.initiateRipeTransfer(False, sender=owner_address)
    
    # Fast forward past key action delay
    key_action_delay = contributor_contract.keyActionDelay()
    boa.env.time_travel(blocks=key_action_delay)
    
    # Store claimable amount before confirm
    claimable_before = contributor_contract.getClaimable()
    total_claimed_before = contributor_contract.totalClaimed()
    
    # Confirm transfer without cashing check
    contributor_contract.confirmRipeTransfer(False, sender=owner_address)  # _shouldCashCheck=False
    
    # Check that no cashing occurred during confirm
    assert contributor_contract.getClaimable() == claimable_before
    assert contributor_contract.totalClaimed() == total_claimed_before
    
    # Should no longer have pending transfer
    assert contributor_contract.hasPendingRipeTransfer() == False


# Test Manager Permissions for Admin Functions


def test_contributor_set_manager_by_hr_admin(
    contributor_contract,
    switchboard_alpha,
    alice
):
    """Test that HR admin can set manager"""
    
    original_manager = contributor_contract.manager()
    
    # HR admin can set manager
    contributor_contract.setManager(alice, sender=switchboard_alpha.address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "ManagerModified")
    assert len(events) == 1
    event = events[0]
    assert event.newManager == alice
    assert event.changedBy == switchboard_alpha.address
    
    # Manager should be updated
    assert contributor_contract.manager() == alice


def test_contributor_set_manager_with_pending_ownership_change(
    contributor_contract,
    owner_address,
    alice,
    bob
):
    """Test that setting manager fails with pending ownership change"""
    
    # Initiate ownership change
    contributor_contract.changeOwnership(alice, sender=owner_address)
    
    # Should not be able to set manager
    with boa.reverts("cannot do with pending ownership change"):
        contributor_contract.setManager(bob, sender=owner_address)


def test_contributor_cancel_ripe_transfer_by_hr_admin(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    switchboard_alpha,
    owner_address,
    valid_contributor_terms
):
    """Test that HR admin can cancel RIPE transfer"""
    
    setupRipeGovVaultConfig()
    
    # Setup and initiate transfer
    deposit_amount = 1000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        contributor_contract.address, ripe_token, deposit_amount, sender=teller.address
    )
    
    start_delay = valid_contributor_terms["startDelay"]
    unlock_length = valid_contributor_terms["unlockLength"]
    boa.env.time_travel(seconds=start_delay + unlock_length + 1)
    
    contributor_contract.initiateRipeTransfer(sender=owner_address)
    
    # HR admin can cancel transfer
    contributor_contract.cancelRipeTransfer(sender=switchboard_alpha.address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "RipeTransferCancelled")
    assert len(events) == 1
    event = events[0]
    assert event.cancelledBy == switchboard_alpha.address
    
    # Should no longer have pending transfer
    assert contributor_contract.hasPendingRipeTransfer() == False


def test_contributor_cancel_ownership_change_by_hr_admin(
    contributor_contract,
    switchboard_alpha,
    owner_address,
    alice
):
    """Test that HR admin can cancel ownership change"""
    
    # Initiate ownership change
    contributor_contract.changeOwnership(alice, sender=owner_address)
    
    # HR admin can cancel ownership change
    contributor_contract.cancelOwnershipChange(sender=switchboard_alpha.address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "OwnershipChangeCancelled")
    assert len(events) == 1
    event = events[0]
    assert event.cancelledBy == switchboard_alpha.address
    
    # Should no longer have pending change
    assert contributor_contract.hasPendingOwnerChange() == False


# Test Enhanced Event Field Verification


def test_contributor_ripe_transfer_cancelled_comprehensive_event(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    valid_contributor_terms
):
    """Test comprehensive event fields for RipeTransferCancelled"""
    
    setupRipeGovVaultConfig()
    
    # Setup and initiate transfer
    deposit_amount = 1000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        contributor_contract.address, ripe_token, deposit_amount, sender=teller.address
    )
    
    start_delay = valid_contributor_terms["startDelay"]
    unlock_length = valid_contributor_terms["unlockLength"]
    boa.env.time_travel(seconds=start_delay + unlock_length + 1)
    
    contributor_contract.initiateRipeTransfer(sender=owner_address)
    
    # Cancel transfer
    contributor_contract.cancelRipeTransfer(sender=owner_address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "RipeTransferCancelled")
    assert len(events) == 1
    event = events[0]
    
    # Verify key event fields (not timing which can be tricky)
    assert event.recipient == owner_address
    assert event.cancelledBy == owner_address
    # Verify timing fields exist and are reasonable
    assert event.initiatedBlock > 0
    assert event.confirmBlock > event.initiatedBlock


def test_contributor_ownership_change_cancelled_comprehensive_event(
    contributor_contract,
    owner_address,
    alice
):
    """Test comprehensive event fields for OwnershipChangeCancelled"""
    
    # Initiate ownership change
    contributor_contract.changeOwnership(alice, sender=owner_address)
    
    # Cancel change
    contributor_contract.cancelOwnershipChange(sender=owner_address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "OwnershipChangeCancelled")
    assert len(events) == 1
    event = events[0]
    
    # Verify key event fields (not timing which can be tricky)
    assert event.cancelledOwner == alice
    assert event.cancelledBy == owner_address
    # Verify timing fields exist and are reasonable
    assert event.initiatedBlock > 0
    assert event.confirmBlock > event.initiatedBlock


# Test Edge Cases and Error Conditions


def test_contributor_cash_ripe_check_by_hr_admin(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_alpha,
    valid_contributor_terms
):
    """Test that HR admin can cash ripe check"""
    
    setupRipeGovVaultConfig()
    
    # Fast forward to have some vesting
    start_delay = valid_contributor_terms["startDelay"]
    cliff_length = valid_contributor_terms["cliffLength"]
    boa.env.time_travel(seconds=start_delay + cliff_length + (30 * 24 * 3600))
    
    claimable = contributor_contract.getClaimable()
    assert claimable > 0
    
    # HR admin can cash check
    result = contributor_contract.cashRipeCheck(sender=switchboard_alpha.address)
    assert result == claimable
    
    # Check event was emitted immediately after transaction
    events = filter_logs(contributor_contract, "RipeCheckCashed")
    assert len(events) == 1
    event = events[0]
    assert event.owner == contributor_contract.owner()
    assert event.cashedBy == switchboard_alpha.address
    assert event.amount == claimable



def test_contributor_exact_timing_boundaries(
    contributor_contract,
    setupRipeGovVaultConfig,
    valid_contributor_terms
):
    """Test behavior at exact timing boundaries"""
    
    setupRipeGovVaultConfig()
    
    start_delay = valid_contributor_terms["startDelay"]
    cliff_length = valid_contributor_terms["cliffLength"]
    unlock_length = valid_contributor_terms["unlockLength"]
    
    # Test exactly at start time
    boa.env.time_travel(seconds=start_delay)
    assert contributor_contract.getTotalVested() == 0
    assert contributor_contract.getClaimable() == 0
    
    # Test exactly at cliff time  
    boa.env.time_travel(seconds=cliff_length)
    vested_at_cliff = contributor_contract.getTotalVested()
    assert vested_at_cliff > 0
    
    # Test exactly at unlock time
    remaining_unlock = unlock_length - cliff_length
    boa.env.time_travel(seconds=remaining_unlock)
    assert contributor_contract.getRemainingUnlockLength() == 0
    
    # Test one second before unlock (should still fail RIPE transfer)
    boa.env.time_travel(seconds=-1)
    with boa.reverts("time not past unlock"):
        contributor_contract.initiateRipeTransfer(sender=contributor_contract.owner())


def test_contributor_key_action_delay_boundary_values(
    contributor_contract,
    owner_address
):
    """Test setting key action delay to boundary values"""
    
    # Get current delay (should be set to MIN_KEY_ACTION_DELAY initially)
    current_delay = contributor_contract.keyActionDelay()
    
    # Test setting below minimum (current_delay should be MIN_KEY_ACTION_DELAY)
    with boa.reverts("invalid delay"):
        contributor_contract.setKeyActionDelay(current_delay - 1, sender=owner_address)
    
    # Test setting to a very high value (should exceed MAX_KEY_ACTION_DELAY)
    with boa.reverts("invalid delay"):
        contributor_contract.setKeyActionDelay(999999999, sender=owner_address)
    
    # Test setting to a valid value within bounds
    new_valid_delay = current_delay + 10
    contributor_contract.setKeyActionDelay(new_valid_delay, sender=owner_address)
    
    # Verify the delay was updated
    assert contributor_contract.keyActionDelay() == new_valid_delay
