import pytest
import boa

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, HUNDRED_PERCENT
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


@pytest.fixture
def owner_address(valid_contributor_terms):
    """Get the owner address from terms"""
    return valid_contributor_terms["owner"]


@pytest.fixture  
def manager_address(valid_contributor_terms):
    """Get the manager address from terms"""
    return valid_contributor_terms["manager"]


###############
# Test Fixtures
###############


@pytest.fixture(scope="module")
def deployedContributor(
    human_resources,
    mission_control,
    switchboard_delta,
    contributor_template,
    ledger,
    governance,
    alice,
    bob
):
    """Deploy a contributor contract for testing"""
    def _deployedContributor(_owner=alice, _manager=bob, _compensation=1000 * EIGHTEEN_DECIMALS):
        owner = _owner
        manager = _manager
        compensation = _compensation
        
        # Set up HR config first
        hr_config = (
            contributor_template.address,  # contribTemplate
            5000 * EIGHTEEN_DECIMALS,      # maxCompensation
            100,                          # minCliffLength
            200,                          # maxStartDelay
            1000,                         # minVestingLength
            5000,                         # maxVestingLength
        )
        mission_control.setHrConfig(hr_config, sender=switchboard_delta.address)
        
        # Set available RIPE for HR
        ledger.setRipeAvailForHr(10000 * EIGHTEEN_DECIMALS, sender=switchboard_delta.address)
        
        # Initiate new contributor
        aid = human_resources.initiateNewContributor(
            owner,             # _owner
            manager,           # _manager  
            compensation,      # _compensation
            50,               # _startDelay
            2000,             # _vestingLength
            500,              # _cliffLength
            1500,             # _unlockLength
            1000,             # _depositLockDuration
            sender=governance.address
        )
        
        # Advance time to pass timelock
        boa.env.time_travel(blocks=human_resources.actionTimeLock())
        
        # Confirm contributor
        success = human_resources.confirmNewContributor(aid, sender=governance.address)
        assert success
        
        # Get the contributor address from logs
        logs = filter_logs(human_resources, "NewContributorConfirmed")
        contributor_addr = logs[-1].contributorAddr
        
        return contributor_addr
        
    return _deployedContributor


#########################
# Access Control Tests
#########################


def test_switchboard_delta_governance_permissions(switchboard_delta, alice):
    """Test that only governance can call governance functions"""
    # Non-governance cannot call governance functions
    with boa.reverts("no perms"):
        switchboard_delta.setContributorTemplate(alice, sender=alice)
    
    with boa.reverts("no perms"):
        switchboard_delta.setMaxCompensation(1000 * EIGHTEEN_DECIMALS, sender=alice)
    
    with boa.reverts("no perms"):
        switchboard_delta.setMinCliffLength(604800, sender=alice)  # 1 week
    
    with boa.reverts("no perms"):
        switchboard_delta.setMaxStartDelay(2592000, sender=alice)  # 1 month
    
    with boa.reverts("no perms"):
        switchboard_delta.setVestingLengthBoundaries(2592000, 31536000, sender=alice)  # 1 month to 1 year


def test_switchboard_delta_lite_action_permissions(switchboard_delta, mission_control, governance, alice, deployedContributor):
    """Test lite action permissions: governance always allowed, others need permission"""
    contributor_addr = deployedContributor()
    
    # Initially alice cannot perform lite actions
    with boa.reverts("no perms"):
        switchboard_delta.cashRipeCheckForContributor(contributor_addr, sender=alice)
    
    # Grant alice lite action permission
    mission_control.setCanPerformLiteAction(alice, True, sender=switchboard_delta.address)
    
    # Alice can now freeze (True)
    result = switchboard_delta.freezeContributor(contributor_addr, True, sender=alice)
    assert result
    
    # Alice cannot unfreeze (False) - only governance can
    with boa.reverts("no perms"):
        switchboard_delta.freezeContributor(contributor_addr, False, sender=alice)
    
    # Governance can both freeze and unfreeze
    result1 = switchboard_delta.freezeContributor(contributor_addr, True, sender=governance.address)
    assert result1
    result2 = switchboard_delta.freezeContributor(contributor_addr, False, sender=governance.address)
    assert result2


################################
# HR Config Functions Tests
################################


def test_switchboard_delta_set_contributor_template(switchboard_delta, contributor_template, governance):
    """Test setContributorTemplate creates timelock action"""
    aid = switchboard_delta.setContributorTemplate(contributor_template.address, sender=governance.address)
    
    # Check event was emitted (immediately after transaction)
    logs = filter_logs(switchboard_delta, "PendingHrContribTemplateChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.contribTemplate == contributor_template.address
    assert log.actionId == aid
    
    assert aid > 0
    
    # Check action was stored
    action_type = switchboard_delta.actionType(aid)
    assert action_type == 1  # HR_CONFIG_TEMPLATE
    
    # Check pending config was stored
    pending_config = switchboard_delta.pendingHrConfig(aid)
    assert pending_config[0] == contributor_template.address  # contribTemplate


def test_switchboard_delta_set_contributor_template_validation(switchboard_delta, governance):
    """Test setContributorTemplate validation"""
    # Empty address should fail
    with boa.reverts("invalid contrib template"):
        switchboard_delta.setContributorTemplate(ZERO_ADDRESS, sender=governance.address)


def test_switchboard_delta_set_max_compensation(switchboard_delta, governance):
    """Test setMaxCompensation creates timelock action"""
    max_comp = 10000 * EIGHTEEN_DECIMALS
    aid = switchboard_delta.setMaxCompensation(max_comp, sender=governance.address)
    
    # Check event was emitted (immediately after transaction)
    logs = filter_logs(switchboard_delta, "PendingHrMaxCompensationChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.maxCompensation == max_comp
    assert log.actionId == aid
    
    assert aid > 0
    
    # Check action was stored
    action_type = switchboard_delta.actionType(aid)
    assert action_type == 2  # HR_CONFIG_MAX_COMP
    
    # Check pending config was stored
    pending_config = switchboard_delta.pendingHrConfig(aid)
    assert pending_config[1] == max_comp  # maxCompensation


def test_switchboard_delta_set_max_compensation_validation(switchboard_delta, governance):
    """Test setMaxCompensation validation"""
    # Zero should fail
    with boa.reverts("invalid max compensation"):
        switchboard_delta.setMaxCompensation(0, sender=governance.address)
    
    # Too large should fail
    with boa.reverts("invalid max compensation"):
        switchboard_delta.setMaxCompensation(21_000_000 * EIGHTEEN_DECIMALS, sender=governance.address)


def test_switchboard_delta_set_min_cliff_length(switchboard_delta, governance):
    """Test setMinCliffLength creates timelock action"""
    min_cliff = 1209600  # 2 weeks in seconds
    aid = switchboard_delta.setMinCliffLength(min_cliff, sender=governance.address)
    
    # Check event was emitted (immediately after transaction)
    logs = filter_logs(switchboard_delta, "PendingHrMinCliffLengthChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.minCliffLength == min_cliff
    assert log.actionId == aid
    
    assert aid > 0
    
    # Check action was stored
    action_type = switchboard_delta.actionType(aid)
    assert action_type == 4  # HR_CONFIG_MIN_CLIFF
    
    # Check pending config was stored
    pending_config = switchboard_delta.pendingHrConfig(aid)
    assert pending_config[2] == min_cliff  # minCliffLength


def test_switchboard_delta_set_min_cliff_length_validation(switchboard_delta, governance):
    """Test setMinCliffLength validation"""
    # Too small should fail (must be > 1 week)
    with boa.reverts("invalid min cliff length"):
        switchboard_delta.setMinCliffLength(604800, sender=governance.address)  # exactly 1 week


def test_switchboard_delta_set_max_start_delay(switchboard_delta, governance):
    """Test setMaxStartDelay creates timelock action"""
    max_delay = 2592000  # 1 month in seconds
    aid = switchboard_delta.setMaxStartDelay(max_delay, sender=governance.address)
    
    # Check event was emitted (immediately after transaction)
    logs = filter_logs(switchboard_delta, "PendingHrMaxStartDelayChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.maxStartDelay == max_delay
    assert log.actionId == aid
    
    assert aid > 0
    
    # Check action was stored
    action_type = switchboard_delta.actionType(aid)
    assert action_type == 8  # HR_CONFIG_MAX_START_DELAY
    
    # Check pending config was stored
    pending_config = switchboard_delta.pendingHrConfig(aid)
    assert pending_config[3] == max_delay  # maxStartDelay


def test_switchboard_delta_set_max_start_delay_validation(switchboard_delta, governance):
    """Test setMaxStartDelay validation"""
    # Too large should fail (must be <= 3 months)
    with boa.reverts("invalid max start delay"):
        switchboard_delta.setMaxStartDelay(7776001, sender=governance.address)  # 3 months + 1 second


def test_switchboard_delta_set_vesting_length_boundaries(switchboard_delta, governance):
    """Test setVestingLengthBoundaries creates timelock action"""
    min_vesting = 5184000   # 2 months in seconds
    max_vesting = 63072000  # 2 years in seconds
    aid = switchboard_delta.setVestingLengthBoundaries(min_vesting, max_vesting, sender=governance.address)
    
    # Check event was emitted (immediately after transaction)
    logs = filter_logs(switchboard_delta, "PendingHrVestingLengthBoundariesChange")
    assert len(logs) == 1
    log = logs[0]
    assert log.minVestingLength == min_vesting
    assert log.maxVestingLength == max_vesting
    assert log.actionId == aid
    
    assert aid > 0
    
    # Check action was stored
    action_type = switchboard_delta.actionType(aid)
    assert action_type == 16  # HR_CONFIG_VESTING
    
    # Check pending config was stored
    pending_config = switchboard_delta.pendingHrConfig(aid)
    assert pending_config[4] == min_vesting  # minVestingLength
    assert pending_config[5] == max_vesting  # maxVestingLength


def test_switchboard_delta_set_vesting_length_boundaries_validation(switchboard_delta, governance):
    """Test setVestingLengthBoundaries validation"""
    # Min >= Max should fail
    with boa.reverts("invalid vesting length boundaries"):
        switchboard_delta.setVestingLengthBoundaries(31536000, 31536000, sender=governance.address)  # equal
    
    with boa.reverts("invalid vesting length boundaries"):
        switchboard_delta.setVestingLengthBoundaries(31536000, 15768000, sender=governance.address)  # min > max
    
    # Min too small should fail (must be > 1 month)
    with boa.reverts("invalid min vesting length"):
        switchboard_delta.setVestingLengthBoundaries(2592000, 31536000, sender=governance.address)  # exactly 1 month
    
    # Max too large should fail (must be <= 5 years)
    with boa.reverts("invalid max vesting length"):
        switchboard_delta.setVestingLengthBoundaries(5184000, 157680001, sender=governance.address)  # 5 years + 1 second


########################################
# Contributor Management Function Tests
########################################


def test_switchboard_delta_set_manager_for_contributor(switchboard_delta, governance, alice, bob, deployedContributor):
    """Test setManagerForContributor creates timelock action"""
    contributor_addr = deployedContributor()
    
    aid = switchboard_delta.setManagerForContributor(contributor_addr, bob, sender=governance.address)
    
    # Check event was emitted (immediately after transaction)
    logs = filter_logs(switchboard_delta, "PendingManagerSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.contributor == contributor_addr
    assert log.manager == bob
    assert log.actionId == aid
    
    assert aid > 0
    
    # Check action was stored
    action_type = switchboard_delta.actionType(aid)
    assert action_type == 32  # HR_MANAGER
    
    # Check pending manager was stored
    pending_manager = switchboard_delta.pendingManager(aid)
    assert pending_manager[0] == contributor_addr  # contributor
    assert pending_manager[1] == bob               # pendingManager


def test_switchboard_delta_set_manager_validation(switchboard_delta, governance, alice, deployedContributor):
    """Test setManagerForContributor validation"""
    contributor_addr = deployedContributor()
    
    # Empty manager should fail
    with boa.reverts("invalid manager"):
        switchboard_delta.setManagerForContributor(contributor_addr, ZERO_ADDRESS, sender=governance.address)
    
    # Non-contributor should fail
    with boa.reverts("not a contributor"):
        switchboard_delta.setManagerForContributor(alice, alice, sender=governance.address)


def test_switchboard_delta_cancel_paycheck_for_contributor(switchboard_delta, governance, deployedContributor):
    """Test cancelPaycheckForContributor creates timelock action"""
    contributor_addr = deployedContributor()
    
    aid = switchboard_delta.cancelPaycheckForContributor(contributor_addr, sender=governance.address)
    
    # Check event was emitted (immediately after transaction)
    logs = filter_logs(switchboard_delta, "PendingCancelPaycheckSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.contributor == contributor_addr
    assert log.actionId == aid
    
    assert aid > 0
    
    # Check action was stored
    action_type = switchboard_delta.actionType(aid)
    assert action_type == 64  # HR_CANCEL_PAYCHECK
    
    # Check pending cancellation was stored
    pending_cancel = switchboard_delta.pendingCancelPaycheck(aid)
    assert pending_cancel == contributor_addr


def test_switchboard_delta_cancel_paycheck_validation(switchboard_delta, governance, alice):
    """Test cancelPaycheckForContributor validation"""
    # Non-contributor should fail
    with boa.reverts("not a contributor"):
        switchboard_delta.cancelPaycheckForContributor(alice, sender=governance.address)


############################
# Lite Action Function Tests
############################


def test_switchboard_delta_cash_ripe_check_for_contributor(switchboard_delta, mission_control, governance, deployedContributor):
    """Test cashRipeCheckForContributor calls contributor and logs event"""
    contributor_addr = deployedContributor()
    
    # Grant governance lite action permission
    mission_control.setCanPerformLiteAction(governance.address, True, sender=switchboard_delta.address)
    
    # Cash ripe check - should return 0 but not fail (contributor has no claimable amount initially)
    result = switchboard_delta.cashRipeCheckForContributor(contributor_addr, sender=governance.address)
    assert result
    
    # Check event emission
    logs = filter_logs(switchboard_delta, "RipeCheckCashedFromSwitchboard")
    assert len(logs) == 1
    log = logs[0]
    assert log.contributor == contributor_addr
    assert log.cashedBy == governance.address
    assert log.amount == 0  # Should be 0 since contributor hasn't vested anything yet


def test_switchboard_delta_cancel_ripe_transfer_for_contributor(
    switchboard_delta, mission_control, governance, deployedContributor, 
    setupRipeGovVaultConfig, ripe_gov_vault, ripe_token, whale, teller, 
    valid_contributor_terms, alice
):
    """Test cancelRipeTransferForContributor successfully cancels ripe transfer"""
    # Setup vault config and deploy contributor properly
    setupRipeGovVaultConfig()
    contributor_addr = deployedContributor()
    contributor = Contributor.at(contributor_addr)
    
    # Grant governance lite action permission
    mission_control.setCanPerformLiteAction(governance.address, True, sender=switchboard_delta.address)
    
    # Set up a pending ripe transfer first
    # Give contributor some RIPE balance
    deposit_amount = 1000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(contributor.address, ripe_token, deposit_amount, sender=teller.address)
    
    # Fast forward past unlock time (using terms from fixture)
    start_delay = valid_contributor_terms["startDelay"]
    unlock_length = valid_contributor_terms["unlockLength"]
    boa.env.time_travel(seconds=start_delay + unlock_length + 1)
    
    # Initiate ripe transfer from contributor (alice is the actual owner)
    contributor.initiateRipeTransfer(sender=alice)
    
    # Verify pending transfer exists
    assert contributor.hasPendingRipeTransfer()
    
    # Cancel ripe transfer via switchboard - should succeed because SwitchboardDelta is registered
    result = switchboard_delta.cancelRipeTransferForContributor(contributor.address, sender=governance.address)
    assert result
    
    # Check event emission
    logs = filter_logs(switchboard_delta, "RipeTransferCancelledFromSwitchboard")
    assert len(logs) == 1
    log = logs[0]
    assert log.contributor == contributor.address
    assert log.cancelledBy == governance.address
    
    # Verify transfer was cancelled
    assert not contributor.hasPendingRipeTransfer()


def test_switchboard_delta_cancel_ownership_change_for_contributor(
    switchboard_delta, mission_control, governance, deployedContributor, 
    alice, bob
):
    """Test cancelOwnershipChangeForContributor successfully cancels ownership change"""
    # Use proper deployed contributor
    contributor_addr = deployedContributor()
    contributor = Contributor.at(contributor_addr)
    
    # Grant governance lite action permission
    mission_control.setCanPerformLiteAction(governance.address, True, sender=switchboard_delta.address)
    
    # Set up a pending ownership change first (alice is the actual owner)
    contributor.changeOwnership(bob, sender=alice)
    
    # Verify pending ownership change exists
    assert contributor.hasPendingOwnerChange()
    
    # Cancel ownership change via switchboard - should succeed because SwitchboardDelta is registered
    result = switchboard_delta.cancelOwnershipChangeForContributor(contributor.address, sender=governance.address)
    assert result
    
    # Check event emission
    logs = filter_logs(switchboard_delta, "OwnershipChangeCancelledFromSwitchboard")
    assert len(logs) == 1
    log = logs[0]
    assert log.contributor == contributor.address
    assert log.cancelledBy == governance.address
    
    # Verify ownership change was cancelled
    assert not contributor.hasPendingOwnerChange()


def test_switchboard_delta_freeze_contributor(switchboard_delta, mission_control, governance, deployedContributor):
    """Test freezeContributor calls contributor and logs event"""
    contributor_addr = deployedContributor()
    
    # Grant governance lite action permission
    mission_control.setCanPerformLiteAction(governance.address, True, sender=switchboard_delta.address)
    
    # Freeze contributor
    result = switchboard_delta.freezeContributor(contributor_addr, True, sender=governance.address)
    assert result
    
    # Check event emission
    logs = filter_logs(switchboard_delta, "ContributorFrozenFromSwitchboard")
    assert len(logs) == 1
    log = logs[0]
    assert log.contributor == contributor_addr
    assert log.frozenBy == governance.address
    assert log.shouldFreeze
    
    # Unfreeze contributor
    result = switchboard_delta.freezeContributor(contributor_addr, False, sender=governance.address)
    assert result


##########################
# Execution Function Tests
##########################


def test_switchboard_delta_execute_pending_hr_config_template(
    switchboard_delta, mission_control, contributor_template, governance
):
    """Test executing pending contributor template change"""
    # Create pending action
    aid = switchboard_delta.setContributorTemplate(contributor_template.address, sender=governance.address)
    
    # Advance time to pass timelock
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    
    # Execute action
    success = switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert success
    
    # Check config was updated
    hr_config = mission_control.hrConfig()
    assert hr_config[0] == contributor_template.address  # contribTemplate
    
    # Check execution event was emitted
    logs = filter_logs(switchboard_delta, "HrContribTemplateSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.contribTemplate == contributor_template.address
    
    # Check action was cleared
    action_type = switchboard_delta.actionType(aid)
    assert action_type == 0  # Should be cleared


def test_switchboard_delta_execute_pending_max_compensation(
    switchboard_delta, mission_control, governance
):
    """Test executing pending max compensation change"""
    max_comp = 15000 * EIGHTEEN_DECIMALS
    
    # Create pending action
    aid = switchboard_delta.setMaxCompensation(max_comp, sender=governance.address)
    
    # Advance time to pass timelock
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    
    # Execute action
    success = switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert success
    
    # Check config was updated
    hr_config = mission_control.hrConfig()
    assert hr_config[1] == max_comp  # maxCompensation
    
    # Check execution event was emitted
    logs = filter_logs(switchboard_delta, "HrMaxCompensationSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.maxCompensation == max_comp


def test_switchboard_delta_execute_pending_manager_change(
    switchboard_delta, governance, alice, bob, deployedContributor
):
    """Test executing pending manager change succeeds when switchboard is properly registered"""
    contributor_addr = deployedContributor()
    
    # Create pending action
    aid = switchboard_delta.setManagerForContributor(contributor_addr, bob, sender=governance.address)
    
    # Advance time to pass timelock
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    
    # Execute action - should succeed because SwitchboardDelta is registered as a switchboard
    success = switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert success


def test_switchboard_delta_execute_pending_cancel_paycheck(
    switchboard_delta, governance, human_resources, setupHrConfig, setupLedgerBalance, alice, bob
):
    """Test executing pending paycheck cancellation succeeds when switchboard is properly registered"""
    # Set up HR config and ledger balance
    setupHrConfig()
    setupLedgerBalance(1000 * EIGHTEEN_DECIMALS)
    
    # Create contributor with long but valid vesting period to allow cancellation
    aid = human_resources.initiateNewContributor(
        alice,                      # _owner
        bob,                       # _manager  
        1000 * EIGHTEEN_DECIMALS,  # _compensation
        50,                        # _startDelay
        4 * 365 * 24 * 3600,       # _vestingLength (4 years - max allowed)
        30 * 24 * 3600,            # _cliffLength (30 days - minimum allowed)
        365 * 24 * 3600,           # _unlockLength (1 year)
        1000,                      # _depositLockDuration
        sender=governance.address
    )
    
    # Advance time to pass HR timelock and confirm contributor
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    human_resources.confirmNewContributor(aid, sender=governance.address)
    
    # Get contributor address from logs
    logs = filter_logs(human_resources, "NewContributorConfirmed")
    contributor_addr = logs[-1].contributorAddr
    
    # Create pending action
    aid = switchboard_delta.cancelPaycheckForContributor(contributor_addr, sender=governance.address)
    
    # Advance time to pass timelock but not past vesting end
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    
    # Execute action - should succeed because SwitchboardDelta is registered as a switchboard
    success = switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert success
    
    # Check execution event was emitted
    logs = filter_logs(switchboard_delta, "HrContributorCancelPaycheckSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.contributor == contributor_addr


def test_switchboard_delta_execute_before_timelock_fails(
    switchboard_delta, contributor_template, governance
):
    """Test executing action before timelock passes fails"""
    # Create pending action
    aid = switchboard_delta.setContributorTemplate(contributor_template.address, sender=governance.address)
    
    # Try to execute immediately (should fail)
    success = switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert not success


def test_switchboard_delta_cancel_pending_action(
    switchboard_delta, contributor_template, governance
):
    """Test cancelling pending action"""
    # Create pending action
    aid = switchboard_delta.setContributorTemplate(contributor_template.address, sender=governance.address)
    
    # Cancel action
    success = switchboard_delta.cancelPendingAction(aid, sender=governance.address)
    assert success
    
    # Check action was cleared
    action_type = switchboard_delta.actionType(aid)
    assert action_type == 0  # Should be cleared


##########################
# Integration Workflow Tests
##########################


def test_switchboard_delta_complete_hr_config_workflow(
    switchboard_delta, mission_control, contributor_template, governance
):
    """Test complete workflow for HR configuration"""
    # 1. Set up multiple pending configuration changes
    aid1 = switchboard_delta.setContributorTemplate(contributor_template.address, sender=governance.address)
    aid2 = switchboard_delta.setMaxCompensation(8000 * EIGHTEEN_DECIMALS, sender=governance.address)
    aid3 = switchboard_delta.setMinCliffLength(1209600, sender=governance.address)  # 2 weeks
    aid4 = switchboard_delta.setVestingLengthBoundaries(5184000, 94608000, sender=governance.address)  # 2 months to 3 years
    
    # 2. Advance time to pass timelock
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    
    # 3. Execute all actions
    success1 = switchboard_delta.executePendingAction(aid1, sender=governance.address)
    assert success1
    success2 = switchboard_delta.executePendingAction(aid2, sender=governance.address)
    assert success2
    success3 = switchboard_delta.executePendingAction(aid3, sender=governance.address)
    assert success3
    success4 = switchboard_delta.executePendingAction(aid4, sender=governance.address)
    assert success4
    
    # 4. Verify final config
    hr_config = mission_control.hrConfig()
    assert hr_config[0] == contributor_template.address  # contribTemplate
    assert hr_config[1] == 8000 * EIGHTEEN_DECIMALS     # maxCompensation
    assert hr_config[2] == 1209600                       # minCliffLength
    assert hr_config[4] == 5184000                       # minVestingLength
    assert hr_config[5] == 94608000                      # maxVestingLength


def test_switchboard_delta_complete_contributor_management_workflow(
    switchboard_delta, mission_control, governance, human_resources, setupHrConfig, setupLedgerBalance,
    alice, bob
):
    """Test complete workflow for contributor management - SwitchboardDelta has proper permissions"""
    # Set up HR config and ledger balance
    setupHrConfig()
    setupLedgerBalance(1000 * EIGHTEEN_DECIMALS)
    
    # Create contributor with long but valid vesting period to allow paycheck cancellation
    aid = human_resources.initiateNewContributor(
        alice,                      # _owner
        bob,                       # _manager  
        1000 * EIGHTEEN_DECIMALS,  # _compensation
        50,                        # _startDelay
        4 * 365 * 24 * 3600,       # _vestingLength (4 years - max allowed)
        30 * 24 * 3600,            # _cliffLength (30 days - minimum allowed)
        365 * 24 * 3600,           # _unlockLength (1 year)
        1000,                      # _depositLockDuration
        sender=governance.address
    )
    
    # Advance time to pass HR timelock and confirm contributor
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    human_resources.confirmNewContributor(aid, sender=governance.address)
    
    # Get contributor address from logs
    logs = filter_logs(human_resources, "NewContributorConfirmed")
    contributor_addr = logs[-1].contributorAddr
    contributor = Contributor.at(contributor_addr)
    
    # 1. Set up pending contributor management actions (these should work)
    manager_aid = switchboard_delta.setManagerForContributor(contributor.address, bob, sender=governance.address)
    cancel_aid = switchboard_delta.cancelPaycheckForContributor(contributor.address, sender=governance.address)
    
    # 2. Perform immediate lite actions
    mission_control.setCanPerformLiteAction(governance.address, True, sender=switchboard_delta.address)
    
    # Freeze should work (returns bool)
    result1 = switchboard_delta.freezeContributor(contributor.address, True, sender=governance.address)
    assert result1
    
    # Cash ripe check should work (returns uint256)
    result2 = switchboard_delta.cashRipeCheckForContributor(contributor.address, sender=governance.address)
    assert result2
    
    # Set up pending ownership change to test cancellation (alice is the actual owner)
    contributor.changeOwnership(bob, sender=alice)
    assert contributor.hasPendingOwnerChange()
    
    # Cancel ownership change should work
    result3 = switchboard_delta.cancelOwnershipChangeForContributor(contributor.address, sender=governance.address)
    assert result3
    assert not contributor.hasPendingOwnerChange()
    
    # 3. Advance time and attempt to execute timelock actions (these should succeed)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    
    # These should succeed because SwitchboardDelta is registered as a switchboard
    success1 = switchboard_delta.executePendingAction(manager_aid, sender=governance.address)
    assert success1
    
    success2 = switchboard_delta.executePendingAction(cancel_aid, sender=governance.address)
    assert success2


###################
# Edge Case Tests
###################


def test_switchboard_delta_expired_action_auto_cancel(
    switchboard_delta, contributor_template, governance
):
    """Test that expired actions are auto-cancelled"""
    # Create pending action
    aid = switchboard_delta.setContributorTemplate(contributor_template.address, sender=governance.address)
    
    # Check initial state
    action_type_initial = switchboard_delta.actionType(aid)
    assert action_type_initial > 0  # Should be set
    
    # Advance time way beyond max timelock to ensure expiration
    # TimeLock in this implementation may be timestamp-based, so try both
    max_timelock = switchboard_delta.maxActionTimeLock()
    boa.env.time_travel(blocks=max_timelock * 2)  # Go well beyond expiration
    boa.env.time_travel(seconds=max_timelock * 2)  # Also try seconds in case it's timestamp-based
    
    # Try to execute (should auto-cancel and return False)
    success = switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert not success
    
    # Check action was cleared
    action_type = switchboard_delta.actionType(aid)
    assert action_type == 0  # Should be cleared


def test_switchboard_delta_mixed_permissions_scenario(
    switchboard_delta, mission_control, governance, deployedContributor, 
    alice, bob
):
    """Test mixed governance and lite action permissions"""
    # Use proper deployed contributor
    contributor_addr = deployedContributor()
    contributor = Contributor.at(contributor_addr)
    
    # Grant alice lite permission
    mission_control.setCanPerformLiteAction(alice, True, sender=switchboard_delta.address)
    
    # Alice can freeze but not unfreeze
    result = switchboard_delta.freezeContributor(contributor.address, True, sender=alice)
    assert result
    
    with boa.reverts("no perms"):
        switchboard_delta.freezeContributor(contributor.address, False, sender=alice)
    
    # Alice can do lite action that works
    result1 = switchboard_delta.cashRipeCheckForContributor(contributor.address, sender=alice)
    assert result1
    
    # Set up pending ownership change to test cancellation (alice is the actual owner)
    contributor.changeOwnership(bob, sender=alice)
    
    # Alice can cancel ownership change
    result2 = switchboard_delta.cancelOwnershipChangeForContributor(contributor.address, sender=alice)
    assert result2
    
    # Alice cannot do governance actions
    with boa.reverts("no perms"):
        switchboard_delta.setManagerForContributor(contributor.address, bob, sender=alice)
    
    # Governance can do everything (freeze/unfreeze)
    result3 = switchboard_delta.freezeContributor(contributor.address, False, sender=governance.address)
    assert result3
    
    # Governance can create timelock actions
    aid = switchboard_delta.setManagerForContributor(contributor.address, bob, sender=governance.address)
    assert aid > 0


def test_switchboard_delta_set_bad_debt(switchboard_delta, ledger, governance, alice):
    """Test setBadDebt creates timelock action and executes properly"""
    bad_debt_amount = 50000 * EIGHTEEN_DECIMALS  # 50K tokens
    
    # Non-governance cannot set bad debt
    with boa.reverts("no perms"):
        switchboard_delta.setBadDebt(bad_debt_amount, sender=alice)
    
    # Governance can create pending bad debt action
    success = switchboard_delta.setBadDebt(bad_debt_amount, sender=governance.address)
    assert success
    
    # Check pending event was emitted
    logs = filter_logs(switchboard_delta, "PendingBadDebtSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.badDebt == bad_debt_amount
    
    # Get the action ID from the event
    aid = log.actionId
    assert aid > 0
    
    # Check action was stored
    action_type = switchboard_delta.actionType(aid)
    assert action_type == 512  # ActionType.RIPE_BAD_DEBT (bit 9 set)
    
    # Check pending value was stored
    pending_value = switchboard_delta.pendingRipeBondConfigValue(aid)
    assert pending_value == bad_debt_amount
    
    # Verify initial ledger bad debt is 0
    initial_bad_debt = ledger.badDebt()
    assert initial_bad_debt == 0
    
    # Try to execute before timelock (should fail)
    success_early = switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert not success_early
    
    # Advance time past timelock
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    
    # Execute the action
    success_execute = switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert success_execute
    
    # Check execution event was emitted
    execution_logs = filter_logs(switchboard_delta, "BadDebtSet")
    assert len(execution_logs) == 1
    execution_log = execution_logs[0]
    assert execution_log.badDebt == bad_debt_amount
    
    # Verify ledger bad debt was actually set
    final_bad_debt = ledger.badDebt()
    assert final_bad_debt == bad_debt_amount
    
    # Check action was cleared after execution
    final_action_type = switchboard_delta.actionType(aid)
    assert final_action_type == 0  # Should be cleared


def test_switchboard_delta_set_ripe_bond_booster(switchboard_delta, bond_room, ripe_hq_deploy, governance, alice):
    """Test setRipeBondBooster creates timelock action and validates permissions"""
    # Deploy a new bond booster for testing
    new_bond_booster = boa.load(
        "contracts/config/BondBooster.vy",
        ripe_hq_deploy,
        1000 * HUNDRED_PERCENT,  # _maxBoostRatio (1000x or 100,000%)
        100,                     # _maxUnits
        0,                       # _minLockDuration (0 for default, no minimum)
        name="new_bond_booster"
    )
    
    # Non-governance cannot set bond booster
    with boa.reverts("no perms"):
        switchboard_delta.setRipeBondBooster(new_bond_booster.address, sender=alice)
    
    # Note: ZERO_ADDRESS is actually allowed by the validation logic
    # The validation only fails for non-empty addresses that don't have the interface
    
    # Governance can create pending bond booster action
    aid = switchboard_delta.setRipeBondBooster(new_bond_booster.address, sender=governance.address)
    assert aid > 0
    
    # Check pending event was emitted
    logs = filter_logs(switchboard_delta, "PendingBondBoosterSet")
    assert len(logs) == 1
    log = logs[0]
    assert log.bondBooster == new_bond_booster.address
    assert log.actionId == aid
    
    # Check action was stored
    action_type = switchboard_delta.actionType(aid)
    assert action_type == 1024  # ActionType.RIPE_BOND_BOOSTER (bit 10 set)
    
    # Check pending bond booster was stored
    pending_bond_booster = switchboard_delta.pendingBondBooster(aid)
    assert pending_bond_booster == new_bond_booster.address
    
    # Verify initial bond room has different bond booster
    initial_bond_booster = bond_room.bondBooster()
    assert initial_bond_booster != new_bond_booster.address
    
    # Try to execute before timelock (should fail)
    success_early = switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert not success_early
    
    # Advance time past timelock
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    
    # Execute the action
    success_execute = switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert success_execute
    
    # Check execution event was emitted
    execution_logs = filter_logs(switchboard_delta, "RipeBondBoosterSet")
    assert len(execution_logs) == 1
    execution_log = execution_logs[0]
    assert execution_log.bondBooster == new_bond_booster.address
    
    # Verify bond room bond booster was actually set
    final_bond_booster = bond_room.bondBooster()
    assert final_bond_booster == new_bond_booster.address
    
    # Check action was cleared after execution
    final_action_type = switchboard_delta.actionType(aid)
    assert final_action_type == 0  # Should be cleared


def test_switchboard_delta_set_ripe_bond_booster_validation(switchboard_delta, governance, alice):
    """Test setRipeBondBooster validation for invalid bond booster addresses"""
    # Non-contract address should fail validation (will revert when trying to call getBoostRatio)
    with boa.reverts():  # This will catch any revert, not a specific message
        switchboard_delta.setRipeBondBooster(alice, sender=governance.address)
    
    # Empty address is actually allowed by the validation logic
    # The validation only checks if the address has the interface when it's not empty
    aid = switchboard_delta.setRipeBondBooster(ZERO_ADDRESS, sender=governance.address)
    assert aid > 0


def test_switchboard_delta_set_start_epoch_at_block(switchboard_delta, bond_room, governance, alice):
    """Test setStartEpochAtBlock is instant and requires governance permissions"""
    # Non-governance cannot set start epoch
    with boa.reverts("no perms"):
        switchboard_delta.setStartEpochAtBlock(sender=alice)
    
    # Governance can set start epoch at block immediately (no timelock)
    current_block = boa.env.evm.patch.block_number
    future_block = current_block + 100
    
    # Set epoch to start at future block
    switchboard_delta.setStartEpochAtBlock(future_block, sender=governance.address)
    
    # Check event was emitted
    logs = filter_logs(switchboard_delta, "RipeBondStartEpochAtBlockSet")
    assert len(logs) == 1
    assert logs[0].startBlock == future_block
    
    # If no block specified, should use current block
    switchboard_delta.setStartEpochAtBlock(sender=governance.address)
    
    # Check event for current block
    logs = filter_logs(switchboard_delta, "RipeBondStartEpochAtBlockSet")
    assert len(logs) == 1
    assert logs[0].startBlock >= current_block
    
    # Test that when block is 0, it uses current block
    switchboard_delta.setStartEpochAtBlock(0, sender=governance.address)
    
    logs = filter_logs(switchboard_delta, "RipeBondStartEpochAtBlockSet")
    assert len(logs) == 1
    # When 0 is specified, it should use the current block
    assert logs[0].startBlock >= current_block
    
    # Time travel forward and verify block is used correctly
    boa.env.time_travel(blocks=50)
    new_current_block = boa.env.evm.patch.block_number
    
    switchboard_delta.setStartEpochAtBlock(sender=governance.address)
    logs = filter_logs(switchboard_delta, "RipeBondStartEpochAtBlockSet")
    assert len(logs) == 1
    assert logs[0].startBlock == new_current_block


def test_switchboard_delta_set_booster_min_lock_duration(switchboard_delta, bond_room, bond_booster, governance, alice):
    """Test setBoosterMinLockDuration updates BondBooster minLockDuration"""
    # Check initial value
    initial_min_lock = bond_booster.minLockDuration()
    assert initial_min_lock == 0  # Default from fixture
    
    # Non-governance cannot set min lock duration
    with boa.reverts("no perms"):
        switchboard_delta.setBoosterMinLockDuration(100, sender=alice)
    
    # Governance can set min lock duration
    new_min_lock = 1000  # 1000 blocks
    result = switchboard_delta.setBoosterMinLockDuration(new_min_lock, sender=governance.address)
    assert result == True
    
    # Verify the value was updated in BondBooster
    assert bond_booster.minLockDuration() == new_min_lock
    
    # Check event emission
    logs = filter_logs(switchboard_delta, "BoosterMinLockDurationSet")
    assert len(logs) == 1
    assert logs[0].minLockDuration == new_min_lock
    
    # Test updating to a different value
    newer_min_lock = 5000  # 5000 blocks
    switchboard_delta.setBoosterMinLockDuration(newer_min_lock, sender=governance.address)
    assert bond_booster.minLockDuration() == newer_min_lock
    
    # Test setting to 0 (no minimum)
    switchboard_delta.setBoosterMinLockDuration(0, sender=governance.address)
    assert bond_booster.minLockDuration() == 0
