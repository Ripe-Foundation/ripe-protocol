import pytest
import boa

from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def valid_contributor_terms():
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


@pytest.fixture(scope="module")
def setupRipeGovVaultConfig(mission_control, setAssetConfig, setGeneralConfig, switchboard_alpha, ripe_token):
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


# Test canModifyHrContributor


def test_hr_can_modify_hr_contributor_switchboard_address(
    human_resources,
    switchboard_alpha,
    bob,
):   
    result = human_resources.canModifyHrContributor(switchboard_alpha.address)
    assert result

    result = human_resources.canModifyHrContributor(bob)
    assert not result


# Test hasRipeBalance


def test_hr_has_ripe_balance_no_balance(
    human_resources,
    setupRipeGovVaultConfig,
    deployedContributor,
    ripe_gov_vault,
    whale,
    ripe_token,
    teller,
):
    """Test hasRipeBalance returns False when contributor has no RIPE balance"""
    
    setupRipeGovVaultConfig()
    contributor_addr = deployedContributor()
    
    result = human_resources.hasRipeBalance(contributor_addr)
    assert not result

    # Give contributor some RIPE tokens in the vault
    deposit_amount = 1000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        contributor_addr, ripe_token, deposit_amount, sender=teller.address
    )
    
    result = human_resources.hasRipeBalance(contributor_addr)
    assert result


# Test transferContributorRipeTokens


def test_hr_transfer_contributor_ripe_tokens_success(
    human_resources,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    setupRipeGovVaultConfig,
    deployedContributor,
    alice
):
    """Test successful transfer of RIPE tokens from contributor"""
    
    setupRipeGovVaultConfig()
    contributor_addr = deployedContributor()
    
    # Give contributor some RIPE tokens in the vault
    deposit_amount = 1000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        contributor_addr, ripe_token, deposit_amount, sender=teller.address
    )
    
    # Get initial balance
    initial_alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    
    # Transfer tokens (called from contributor address)
    transferred_amount = human_resources.transferContributorRipeTokens(
        alice,  # to user
        200,    # lock duration
        sender=contributor_addr
    )
    
    # Check event was emitted
    events = filter_logs(human_resources, "RipeTokensTransferred")
    assert len(events) == 1
    event = events[0]
    assert event.fromUser == contributor_addr
    assert event.toUser == alice
    assert event.amount == transferred_amount
    
    # Check alice received the tokens
    final_alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    assert final_alice_balance > initial_alice_balance
    assert transferred_amount > 0


def test_hr_transfer_contributor_ripe_tokens_not_contributor(
    human_resources,
    alice,
    bob
):
    """Test transfer fails when caller is not a contributor"""
    
    with boa.reverts("not a contributor"):
        human_resources.transferContributorRipeTokens(
            bob,  # to user
            200,  # lock duration
            sender=alice  # Not a contributor
        )


def test_hr_transfer_contributor_ripe_tokens_paused(
    human_resources,
    switchboard_delta,
    deployedContributor,
    alice
):
    """Test transfer fails when contract is paused"""
    
    contributor_addr = deployedContributor()
    
    # Pause the contract
    human_resources.pause(True, sender=switchboard_delta.address)
    
    with boa.reverts("contract paused"):
        human_resources.transferContributorRipeTokens(
            alice,  # to user
            200,    # lock duration
            sender=contributor_addr
        )


# Test cashRipeCheck


def test_hr_cash_ripe_check_success(
    human_resources,
    ripe_gov_vault,
    ripe_token,
    setupRipeGovVaultConfig,
    deployedContributor
):
    """Test successful cashing of RIPE check"""
    
    setupRipeGovVaultConfig()
    contributor_addr = deployedContributor()
    
    cash_amount = 50000 * EIGHTEEN_DECIMALS  # 50K tokens
    lock_duration = 500  # blocks
    
    # Get initial vault balance for contributor
    initial_balance = ripe_gov_vault.getTotalAmountForUser(contributor_addr, ripe_token)
    
    # Cash RIPE check
    result = human_resources.cashRipeCheck(
        cash_amount,
        lock_duration,
        sender=contributor_addr
    )
    
    assert result
    
    # Check that contributor now has more RIPE in vault
    final_balance = ripe_gov_vault.getTotalAmountForUser(contributor_addr, ripe_token)
    assert final_balance > initial_balance


def test_hr_cash_ripe_check_not_contributor(
    human_resources,
    alice
):
    """Test cash RIPE check fails when caller is not a contributor"""
    
    with boa.reverts("not a contributor"):
        human_resources.cashRipeCheck(
            50000 * EIGHTEEN_DECIMALS,
            500,
            sender=alice
        )


def test_hr_cash_ripe_check_paused(
    human_resources,
    switchboard_delta,
    deployedContributor
):
    """Test cash RIPE check fails when contract is paused"""
    
    contributor_addr = deployedContributor()
    
    # Pause the contract
    human_resources.pause(True, sender=switchboard_delta.address)
    
    with boa.reverts("contract paused"):
        human_resources.cashRipeCheck(
            50000 * EIGHTEEN_DECIMALS,
            500,
            sender=contributor_addr
        )


# Test refundAfterCancelPaycheck


def test_hr_refund_after_cancel_paycheck_no_burn(
    human_resources,
    ledger,
    setupRipeGovVaultConfig,
    deployedContributor,
):
    """Test refund after cancel paycheck without burning position"""
    
    setupRipeGovVaultConfig()
    contributor_addr = deployedContributor()
    
    refund_amount = 25000 * EIGHTEEN_DECIMALS  # 25K tokens
    
    # Get initial ledger balance
    initial_ripe_avail = ledger.ripeAvailForHr()
    
    # Refund without burning
    human_resources.refundAfterCancelPaycheck(
        refund_amount,
        False,  # don't burn position
        sender=contributor_addr
    )
    
    # Check that ledger balance increased
    final_ripe_avail = ledger.ripeAvailForHr()
    assert final_ripe_avail == initial_ripe_avail + refund_amount


def test_hr_refund_after_cancel_paycheck_with_burn_no_position(
    human_resources,
    ledger,
    setupRipeGovVaultConfig,
    deployedContributor
):
    """Test refund with burn when contributor has no vault position"""
    
    setupRipeGovVaultConfig()
    contributor_addr = deployedContributor()
    
    refund_amount = 25000 * EIGHTEEN_DECIMALS
    
    # Get initial ledger balance
    initial_ripe_avail = ledger.ripeAvailForHr()
    
    # Refund with burn (but no position to burn)
    human_resources.refundAfterCancelPaycheck(
        refund_amount,
        True,  # burn position
        sender=contributor_addr
    )
    
    # Check that ledger balance still increased (refund still works)
    final_ripe_avail = ledger.ripeAvailForHr()
    assert final_ripe_avail == initial_ripe_avail + refund_amount


def test_hr_refund_after_cancel_paycheck_with_burn_with_position(
    human_resources,
    ripe_gov_vault,
    ripe_token,
    ledger,
    whale,
    teller,
    setupRipeGovVaultConfig,
    deployedContributor
):
    """Test refund with burn when contributor has vault position"""
    
    setupRipeGovVaultConfig()
    contributor_addr = deployedContributor()
    
    # Give contributor some RIPE tokens in the vault first
    deposit_amount = 1000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, deposit_amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        contributor_addr, ripe_token, deposit_amount, sender=teller.address
    )
    
    refund_amount = 25000 * EIGHTEEN_DECIMALS
    
    # Get initial states
    initial_ripe_avail = ledger.ripeAvailForHr()
    initial_hr_ripe_balance = ripe_token.balanceOf(human_resources)
    
    # Refund with burn
    human_resources.refundAfterCancelPaycheck(
        refund_amount,
        True,  # burn position
        sender=contributor_addr
    )
    
    # Check that ledger balance increased (refund)
    final_ripe_avail = ledger.ripeAvailForHr()
    assert final_ripe_avail == initial_ripe_avail + refund_amount
    
    # Check that contributor's vault position was withdrawn
    final_contributor_balance = ripe_gov_vault.getTotalAmountForUser(contributor_addr, ripe_token)
    assert final_contributor_balance == initial_hr_ripe_balance == 0


def test_hr_refund_after_cancel_paycheck_not_contributor(
    human_resources,
    alice
):
    """Test refund fails when caller is not a contributor"""
    
    with boa.reverts("not a contributor"):
        human_resources.refundAfterCancelPaycheck(
            25000 * EIGHTEEN_DECIMALS,
            False,
            sender=alice
        )


def test_hr_refund_after_cancel_paycheck_paused(
    human_resources,
    switchboard_delta,
    deployedContributor
):
    """Test refund fails when contract is paused"""
    
    contributor_addr = deployedContributor()
    
    # Pause the contract
    human_resources.pause(True, sender=switchboard_delta.address)
    
    with boa.reverts("contract paused"):
        human_resources.refundAfterCancelPaycheck(
            25000 * EIGHTEEN_DECIMALS,
            False,
            sender=contributor_addr
        )


# Test getTotalClaimed


def test_hr_get_total_claimed_no_contributors(
    human_resources
):
    """Test getTotalClaimed returns 0 when no contributors exist"""
    
    total_claimed = human_resources.getTotalClaimed()
    assert total_claimed == 0


def test_hr_get_total_claimed_with_contributors(
    human_resources,
    deployedContributor
):
    """Test getTotalClaimed with contributors (will be 0 since no claims made)"""
    
    # Deploy a contributor
    deployedContributor()
    
    # Should return 0 since no claims have been made yet
    # (contributors don't automatically have claimed amounts)
    total_claimed = human_resources.getTotalClaimed()
    assert total_claimed == 0


# Test getTotalCompensation


def test_hr_get_total_compensation_no_contributors(
    human_resources
):
    """Test getTotalCompensation returns 0 when no contributors exist"""
    
    total_compensation = human_resources.getTotalCompensation()
    assert total_compensation == 0


def test_hr_get_total_compensation_single_contributor(
    human_resources,
    deployedContributor,
    valid_contributor_terms
):
    """Test getTotalCompensation with single contributor"""
    
    # Deploy a contributor
    deployedContributor()
    
    total_compensation = human_resources.getTotalCompensation()
    assert total_compensation == valid_contributor_terms["compensation"]


def test_hr_get_total_compensation_multiple_contributors(
    human_resources,
    deployedContributor,
    valid_contributor_terms
):
    """Test getTotalCompensation with multiple contributors"""
    
    # Deploy first contributor
    deployedContributor()
    
    # Deploy second contributor with different compensation
    terms2 = valid_contributor_terms.copy()
    terms2["compensation"] = 300000 * EIGHTEEN_DECIMALS  # 300K tokens
    terms2["owner"] = "0x" + "33" * 20  # Different owner
    deployedContributor(terms2)
    
    # Deploy third contributor
    terms3 = valid_contributor_terms.copy()
    terms3["compensation"] = 200000 * EIGHTEEN_DECIMALS  # 200K tokens  
    terms3["owner"] = "0x" + "44" * 20  # Different owner
    deployedContributor(terms3)
    
    total_compensation = human_resources.getTotalCompensation()
    expected_total = (
        valid_contributor_terms["compensation"] +  # 500K
        terms2["compensation"] +                   # 300K  
        terms3["compensation"]                     # 200K
    )  # Total: 1M
    assert total_compensation == expected_total
