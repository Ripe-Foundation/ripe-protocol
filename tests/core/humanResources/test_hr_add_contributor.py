import pytest
import boa

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS
from conf_utils import filter_logs


@pytest.fixture
def valid_terms():
    """Valid contributor terms for testing"""
    return {
        "owner": "0x" + "11" * 20,
        "manager": "0x" + "22" * 20,
        "compensation": 500000 * EIGHTEEN_DECIMALS,  # 500K tokens
        "startDelay": 7 * 24 * 3600,  # 7 days
        "vestingLength": 2 * 365 * 24 * 3600,  # 2 years
        "cliffLength": 90 * 24 * 3600,  # 90 days
        "unlockLength": 365 * 24 * 3600,  # 1 year
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


# tests


def test_hr_initiate_new_contributor_success(
    human_resources, 
    setupHrConfig, 
    setupLedgerBalance,
    valid_terms,
    governance
):
    """Test successful initiation of a new contributor"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    # Call initiateNewContributor
    action_id = human_resources.initiateNewContributor(
        valid_terms["owner"],
        valid_terms["manager"], 
        valid_terms["compensation"],
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"],
        sender=governance.address
    )
    
    # Check event was emitted immediately after transaction
    events = filter_logs(human_resources, "NewContributorInitiated")
    assert len(events) == 1
    event = events[0]
    assert event.owner == valid_terms["owner"]
    assert event.manager == valid_terms["manager"]
    assert event.compensation == valid_terms["compensation"]
    assert event.actionId == action_id
    
    # Check that action ID was returned
    assert action_id > 0
    
    # Check pending contributor was stored
    pending = human_resources.pendingContributor(action_id)
    assert pending.owner == valid_terms["owner"]
    assert pending.manager == valid_terms["manager"]
    assert pending.compensation == valid_terms["compensation"]


def test_hr_initiate_new_contributor_invalid_perms(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance, 
    valid_terms,
    bob
):
    """Test initiation fails with invalid permissions"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    with boa.reverts("no perms"):
        human_resources.initiateNewContributor(
            valid_terms["owner"],
            valid_terms["manager"],
            valid_terms["compensation"],
            valid_terms["startDelay"],
            valid_terms["vestingLength"],
            valid_terms["cliffLength"],
            valid_terms["unlockLength"],
            valid_terms["depositLockDuration"],
            sender=bob  # Non-governance account
        )


def test_hr_initiate_new_contributor_paused(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms,
    governance,
    switchboard_delta,
):
    """Test initiation fails when contract is paused"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    # Pause the contract
    human_resources.pause(True, sender=switchboard_delta.address)
    
    with boa.reverts("contract paused"):
        human_resources.initiateNewContributor(
            valid_terms["owner"],
            valid_terms["manager"],
            valid_terms["compensation"],
            valid_terms["startDelay"],
            valid_terms["vestingLength"],
            valid_terms["cliffLength"],
            valid_terms["unlockLength"],
            valid_terms["depositLockDuration"],
            sender=governance.address
        )


def test_hr_initiate_new_contributor_invalid_terms(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms,
    governance
):
    """Test initiation fails with invalid contributor terms"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    # Test with zero compensation
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(
            valid_terms["owner"],
            valid_terms["manager"],
            0,  # Invalid: zero compensation
            valid_terms["startDelay"],
            valid_terms["vestingLength"],
            valid_terms["cliffLength"],
            valid_terms["unlockLength"],
            valid_terms["depositLockDuration"],
            sender=governance.address
        )
    
    # Test with cliff longer than unlock
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(
            valid_terms["owner"],
            valid_terms["manager"],
            valid_terms["compensation"],
            valid_terms["startDelay"],
            valid_terms["vestingLength"],
            valid_terms["vestingLength"] + 1,  # Invalid: cliff > unlock
            valid_terms["unlockLength"],
            valid_terms["depositLockDuration"],
            sender=governance.address
        )


def test_hr_confirm_new_contributor_success(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms,
    governance
):
    """Test successful confirmation of a new contributor"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    # First initiate a contributor
    action_id = human_resources.initiateNewContributor(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"],
        sender=governance.address
    )
    
    # Mine blocks to reach confirmation time
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    
    # Confirm the contributor
    result = human_resources.confirmNewContributor(action_id, sender=governance.address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(human_resources, "NewContributorConfirmed")
    assert len(events) == 1
    event = events[0]
    assert event.owner == valid_terms["owner"]
    assert event.actionId == action_id
    assert event.contributorAddr != ZERO_ADDRESS  # Should have deployed address
    
    # Check return value
    assert result
    
    # Check pending contributor was cleared
    pending = human_resources.pendingContributor(action_id)
    assert pending.owner == ZERO_ADDRESS  # Should be empty


def test_hr_confirm_new_contributor_invalid_perms(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms,
    governance,
    bob
):
    """Test confirmation fails with invalid permissions"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    # First initiate a contributor
    action_id = human_resources.initiateNewContributor(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"],
        sender=governance.address
    )
    
    # Mine blocks to reach confirmation time
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    
    with boa.reverts("no perms"):
        human_resources.confirmNewContributor(action_id, sender=bob)


def test_hr_confirm_new_contributor_no_pending(
    human_resources, 
    setupHrConfig,
    governance
):
    """Test confirmation fails when no pending contributor exists"""
    
    # Setup HR configuration
    setupHrConfig()
    
    with boa.reverts("no pending contributor"):
        human_resources.confirmNewContributor(999, sender=governance.address)


def test_hr_confirm_new_contributor_timelock_not_reached(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms,
    governance
):
    """Test confirmation fails when timelock not reached"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    # First initiate a contributor
    action_id = human_resources.initiateNewContributor(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"],
        sender=governance.address
    )
    
    # Try to confirm immediately without waiting
    with boa.reverts("time lock not reached"):
        human_resources.confirmNewContributor(action_id, sender=governance.address)


def test_hr_cancel_new_contributor_success(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms,
    governance
):
    """Test successful cancellation of a pending contributor"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    # First initiate a contributor
    action_id = human_resources.initiateNewContributor(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"],
        sender=governance.address
    )
    
    # Cancel the contributor
    result = human_resources.cancelNewContributor(action_id, sender=governance.address)
    
    # Check event was emitted immediately after transaction
    events = filter_logs(human_resources, "NewContributorCancelled")
    assert len(events) == 1
    event = events[0]
    assert event.owner == valid_terms["owner"]
    assert event.actionId == action_id
    
    # Check return value
    assert result
    
    # Check pending contributor was cleared
    pending = human_resources.pendingContributor(action_id)
    assert pending.owner == ZERO_ADDRESS  # Should be empty


def test_hr_cancel_new_contributor_invalid_perms(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms,
    governance,
    bob
):
    """Test cancellation fails with invalid permissions"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    # First initiate a contributor
    action_id = human_resources.initiateNewContributor(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"],
        sender=governance.address
    )
    
    with boa.reverts("no perms"):
        human_resources.cancelNewContributor(action_id, sender=bob)


def test_hr_cancel_new_contributor_no_pending(
    human_resources, 
    setupHrConfig,
    governance
):
    """Test cancellation fails when no pending contributor exists"""
    
    # Setup HR configuration
    setupHrConfig()
    
    with boa.reverts("no pending contributor"):
        human_resources.cancelNewContributor(999, sender=governance.address)


def test_hr_confirm_new_contributor_ledger_state_updated(
    human_resources,
    ledger,
    setupHrConfig,
    setupLedgerBalance,
    valid_terms,
    governance
):
    """Test that ledger state is properly updated when a contributor is confirmed"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    initial_balance = valid_terms["compensation"] * 2  # Set more than needed
    setupLedgerBalance(initial_balance)
    
    # Record initial ledger state
    initial_ripe_avail = ledger.ripeAvailForHr()
    initial_num_contributors = ledger.numContributors()
    
    # Initiate a contributor
    action_id = human_resources.initiateNewContributor(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"],
        sender=governance.address
    )
    
    # Wait for timelock and confirm
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    result = human_resources.confirmNewContributor(action_id, sender=governance.address)
    
    # Get event to find deployed contributor address
    events = filter_logs(human_resources, "NewContributorConfirmed")
    assert len(events) == 1
    contributor_address = events[0].contributorAddr
    
    # Verify ledger state updates
    assert result
    
    # Check ripeAvailForHr decreased by compensation amount
    final_ripe_avail = ledger.ripeAvailForHr()
    assert final_ripe_avail == initial_ripe_avail - valid_terms["compensation"]
    
    # Check numContributors increased properly (1-indexed system)
    final_num_contributors = ledger.numContributors()
    if initial_num_contributors == 0:
        # First contributor: goes from 0 to 2 (increment of 2)
        assert final_num_contributors == 2
        contributor_index = 1
    else:
        # Subsequent contributors: increment by 1
        assert final_num_contributors == initial_num_contributors + 1
        contributor_index = initial_num_contributors
    
    # Check contributor is in the contributors array at the correct index
    assert ledger.contributors(contributor_index) == contributor_address
    
    # Check isHrContributor returns True for the new contributor
    assert ledger.isHrContributor(contributor_address)


def test_hr_confirm_multiple_contributors_ledger_state(
    human_resources,
    ledger,
    setupHrConfig,
    setupLedgerBalance,
    valid_terms,
    governance
):
    """Test that ledger state is correctly maintained across multiple contributors"""
    
    # Setup HR configuration and ledger balance for multiple contributors
    setupHrConfig()
    total_balance = valid_terms["compensation"] * 3  # Enough for 3 contributors
    setupLedgerBalance(total_balance)
    
    # Record initial ledger state
    initial_ripe_avail = ledger.ripeAvailForHr()
    initial_num_contributors = ledger.numContributors()
    
    contributor_addresses = []
    
    # Confirm three contributors
    for i in range(3):
        # Create unique terms for each contributor
        owner = "0x" + str(i+1).zfill(2) * 20  # 0x11...11, 0x22...22, 0x33...33
        manager = "0x" + str(i+5).zfill(2) * 20  # 0x55...55, 0x66...66, 0x77...77
        
        # Initiate contributor
        action_id = human_resources.initiateNewContributor(
            owner,
            manager,
            valid_terms["compensation"],
            valid_terms["startDelay"],
            valid_terms["vestingLength"],
            valid_terms["cliffLength"],
            valid_terms["unlockLength"],
            valid_terms["depositLockDuration"],
            sender=governance.address
        )
        
        # Wait for timelock and confirm
        boa.env.time_travel(blocks=human_resources.actionTimeLock())
        result = human_resources.confirmNewContributor(action_id, sender=governance.address)
        
        # Get contributor address from event
        events = filter_logs(human_resources, "NewContributorConfirmed")
        assert len(events) == 1
        contributor_address = events[0].contributorAddr
        contributor_addresses.append(contributor_address)
        
        assert result
    
    # Verify final ledger state
    final_ripe_avail = ledger.ripeAvailForHr()
    final_num_contributors = ledger.numContributors()
    
    # Check ripeAvailForHr decreased by total compensation for all contributors
    expected_final_balance = initial_ripe_avail - (valid_terms["compensation"] * 3)
    assert final_ripe_avail == expected_final_balance
    
    # Check numContributors increased properly for 3 contributors
    if initial_num_contributors == 0:
        # Starting from 0: first contributor increments by 2, then each by 1
        # 0 -> 2 -> 3 -> 4 (total increment of 4)
        assert final_num_contributors == 4
        start_index = 1
    else:
        # Starting from non-zero: each contributor increments by 1
        assert final_num_contributors == initial_num_contributors + 3
        start_index = initial_num_contributors
    
    # Check all contributors are in the contributors array at correct indices
    for i, contributor_addr in enumerate(contributor_addresses):
        index = start_index + i
        assert ledger.contributors(index) == contributor_addr
        
        # Check each contributor is recognized as HR contributor
        assert ledger.isHrContributor(contributor_addr)


def test_hr_are_valid_contributor_terms_success(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms
):
    """Test valid contributor terms pass validation"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    result = human_resources.areValidContributorTerms(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"]
    )
    
    assert result


def test_hr_are_valid_contributor_terms_no_template(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms
):
    """Test validation fails when no contributor template is set"""
    
    # Setup HR config with empty template
    setupHrConfig(_contribTemplate=ZERO_ADDRESS)
    setupLedgerBalance(valid_terms["compensation"])
    
    result = human_resources.areValidContributorTerms(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"]
    )
    
    assert not result


def test_hr_are_valid_contributor_terms_zero_compensation(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms
):
    """Test validation fails with zero compensation"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    result = human_resources.areValidContributorTerms(
        valid_terms["owner"],
        valid_terms["manager"],
        0,  # Zero compensation
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"]
    )
    
    assert not result


def test_hr_are_valid_contributor_terms_insufficient_balance(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms
):
    """Test validation fails when insufficient RIPE balance available"""
    
    # Setup HR configuration
    setupHrConfig()
    # Set balance lower than compensation
    setupLedgerBalance(100000 * EIGHTEEN_DECIMALS)  # Less than compensation
    
    result = human_resources.areValidContributorTerms(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"]
    )
    
    assert not result


def test_hr_are_valid_contributor_terms_exceeds_max_compensation(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms
):
    """Test validation fails when compensation exceeds maximum"""
    
    # Set max compensation lower than requested
    setupHrConfig(_maxCompensation=100000 * EIGHTEEN_DECIMALS)  # Lower than requested
    setupLedgerBalance(valid_terms["compensation"])
    
    result = human_resources.areValidContributorTerms(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],  # Higher than max
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"]
    )
    
    assert not result


def test_hr_are_valid_contributor_terms_zero_cliff(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms
):
    """Test validation fails with zero cliff length"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    result = human_resources.areValidContributorTerms(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        0,  # Zero cliff
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"]
    )
    
    assert not result


def test_hr_are_valid_contributor_terms_cliff_below_minimum(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms
):
    """Test validation fails when cliff length below minimum"""
    
    # Set minimum cliff higher than requested
    setupHrConfig(_minCliffLength=365 * 24 * 3600)  # 1 year minimum
    setupLedgerBalance(valid_terms["compensation"])
    
    result = human_resources.areValidContributorTerms(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        90 * 24 * 3600,  # 90 days - below minimum
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"]
    )
    
    assert not result


def test_hr_are_valid_contributor_terms_zero_vesting(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms
):
    """Test validation fails with zero vesting length"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    result = human_resources.areValidContributorTerms(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        0,  # Zero vesting
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"]
    )
    
    assert not result


def test_hr_are_valid_contributor_terms_unlock_greater_than_vesting(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms
):
    """Test validation fails when unlock length greater than vesting"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    result = human_resources.areValidContributorTerms(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        365 * 24 * 3600,  # 1 year vesting
        valid_terms["cliffLength"],
        2 * 365 * 24 * 3600,  # 2 year unlock - greater than vesting
        valid_terms["depositLockDuration"]
    )
    
    assert not result


def test_hr_are_valid_contributor_terms_cliff_greater_than_unlock(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms
):
    """Test validation fails when cliff length greater than unlock"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    result = human_resources.areValidContributorTerms(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        2 * 365 * 24 * 3600,  # 2 year cliff
        365 * 24 * 3600,  # 1 year unlock - less than cliff
        valid_terms["depositLockDuration"]
    )
    
    assert not result


def test_hr_are_valid_contributor_terms_empty_owner(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms
):
    """Test validation fails with empty owner address"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    result = human_resources.areValidContributorTerms(
        ZERO_ADDRESS,  # Empty owner
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"]
    )
    
    assert not result


def test_hr_are_valid_contributor_terms_empty_manager(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms
):
    """Test validation fails with empty manager address"""
    
    # Setup HR configuration and ledger balance
    setupHrConfig()
    setupLedgerBalance(valid_terms["compensation"])
    
    result = human_resources.areValidContributorTerms(
        valid_terms["owner"],
        ZERO_ADDRESS,  # Empty manager
        valid_terms["compensation"],
        valid_terms["startDelay"],
        valid_terms["vestingLength"],
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"]
    )
    
    assert not result


def test_hr_are_valid_contributor_terms_start_delay_too_long(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms
):
    """Test validation fails when start delay exceeds maximum"""
    
    # Set max start delay lower than requested
    setupHrConfig(_maxStartDelay=1 * 24 * 3600)  # 1 day maximum
    setupLedgerBalance(valid_terms["compensation"])
    
    result = human_resources.areValidContributorTerms(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        7 * 24 * 3600,  # 7 days - exceeds maximum
        valid_terms["vestingLength"],
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"]
    )
    
    assert not result


def test_hr_are_valid_contributor_terms_vesting_below_minimum(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms
):
    """Test validation fails when vesting length below minimum"""
    
    # Set minimum vesting higher than requested
    setupHrConfig(_minVestingLength=3 * 365 * 24 * 3600)  # 3 years minimum
    setupLedgerBalance(valid_terms["compensation"])
    
    result = human_resources.areValidContributorTerms(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        2 * 365 * 24 * 3600,  # 2 years - below minimum
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"]
    )
    
    assert not result


def test_hr_are_valid_contributor_terms_vesting_above_maximum(
    human_resources, 
    setupHrConfig,
    setupLedgerBalance,
    valid_terms
):
    """Test validation fails when vesting length above maximum"""
    
    # Set maximum vesting lower than requested
    setupHrConfig(_maxVestingLength=1 * 365 * 24 * 3600)  # 1 year maximum
    setupLedgerBalance(valid_terms["compensation"])
    
    result = human_resources.areValidContributorTerms(
        valid_terms["owner"],
        valid_terms["manager"],
        valid_terms["compensation"],
        valid_terms["startDelay"],
        2 * 365 * 24 * 3600,  # 2 years - above maximum
        valid_terms["cliffLength"],
        valid_terms["unlockLength"],
        valid_terms["depositLockDuration"]
    )
    
    assert not result
