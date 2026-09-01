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


def test_hr_refund_burn_reverts_atomically_when_contributor_debt_becomes_unhealthy(
    human_resources,
    ripe_gov_vault,
    ripe_token,
    ledger,
    bob,
    teller,
    credit_engine,
    mission_control,
    switchboard_alpha,
    switchboard_charlie,
    setupRipeGovVaultConfig,
    setGeneralDebtConfig,
    mock_price_source,
    deployedContributor,
):
    setupRipeGovVaultConfig()
    setGeneralDebtConfig()
    mission_control.setShouldCheckLastTouch(False, sender=switchboard_alpha.address)
    mock_price_source.setPrice(ripe_token, EIGHTEEN_DECIMALS)
    contributor_addr = deployedContributor()

    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    human_resources.cashRipeCheck(
        deposit_amount,
        500,
        sender=contributor_addr,
    )

    mission_control.setUserDelegation(
        contributor_addr,
        bob,
        (False, True, False, False),
        sender=switchboard_charlie.address,
    )
    max_debt = credit_engine.getUserBorrowTerms(
        contributor_addr,
        False,
    ).totalMaxDebt
    assert max_debt > 0
    teller.borrow(max_debt, contributor_addr, False, sender=bob)

    debt_before = ledger.userDebt(contributor_addr).amount
    terms_before = credit_engine.getUserBorrowTerms(contributor_addr, False)
    assert debt_before == max_debt
    assert debt_before <= terms_before.totalMaxDebt

    refund_amount = 25_000 * EIGHTEEN_DECIMALS
    position_before = ripe_gov_vault.getTotalAmountForUser(
        contributor_addr,
        ripe_token,
    )
    total_shares_before = ripe_gov_vault.totalBalances(ripe_token)
    custody_before = ripe_token.balanceOf(ripe_gov_vault)
    supply_before = ripe_token.totalSupply()
    budget_before = ledger.ripeAvailForHr()
    with boa.reverts("bad debt health"):
        human_resources.refundAfterCancelPaycheck(
            refund_amount,
            True,
            sender=contributor_addr,
        )

    assert ripe_gov_vault.getTotalAmountForUser(contributor_addr, ripe_token) == position_before
    assert ripe_gov_vault.totalBalances(ripe_token) == total_shares_before
    assert ripe_token.balanceOf(ripe_gov_vault) == custody_before
    assert ripe_token.balanceOf(human_resources) == 0
    assert ripe_token.totalSupply() == supply_before
    assert ledger.ripeAvailForHr() == budget_before
    assert ledger.userDebt(contributor_addr).amount == debt_before


@pytest.mark.parametrize(
    ("debt_delta", "should_revert"),
    (
        pytest.param(0, False, id="exact-post-burn-capacity"),
        pytest.param(1, True, id="one-wei-over-post-burn-capacity"),
    ),
)
def test_hr_refund_burn_enforces_other_collateral_health_boundary(
    debt_delta,
    should_revert,
    human_resources,
    ripe_gov_vault,
    simple_erc20_vault,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    ledger,
    bob,
    teller,
    credit_engine,
    mission_control,
    switchboard_alpha,
    switchboard_charlie,
    setupRipeGovVaultConfig,
    setAssetConfig,
    createDebtTerms,
    setGeneralDebtConfig,
    mock_price_source,
    deployedContributor,
):
    setupRipeGovVaultConfig()
    alpha_ltv = 50_00
    setAssetConfig(
        alpha_token,
        _debtTerms=createDebtTerms(_ltv=alpha_ltv, _borrowRate=0),
    )
    setGeneralDebtConfig()
    mission_control.setShouldCheckLastTouch(False, sender=switchboard_alpha.address)
    mock_price_source.setPrice(ripe_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    contributor_addr = deployedContributor()

    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    human_resources.cashRipeCheck(
        deposit_amount,
        500,
        sender=contributor_addr,
    )

    alpha_token.transfer(human_resources, deposit_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, deposit_amount, sender=human_resources.address)
    teller.depositFromTrusted(
        contributor_addr,
        3,
        alpha_token,
        deposit_amount,
        0,
        sender=human_resources.address,
    )
    assert simple_erc20_vault.getTotalAmountForUser(contributor_addr, alpha_token) == deposit_amount

    mission_control.setUserDelegation(
        contributor_addr,
        bob,
        (False, True, False, False),
        sender=switchboard_charlie.address,
    )
    post_burn_max_debt = deposit_amount * alpha_ltv // 100_00
    borrow_amount = post_burn_max_debt + debt_delta
    pre_burn_terms = credit_engine.getUserBorrowTerms(contributor_addr, False)
    assert borrow_amount <= pre_burn_terms.totalMaxDebt
    teller.borrow(borrow_amount, contributor_addr, False, sender=bob)

    refund_amount = 25_000 * EIGHTEEN_DECIMALS
    budget_before = ledger.ripeAvailForHr()
    supply_before = ripe_token.totalSupply()
    ripe_position_before = ripe_gov_vault.getTotalAmountForUser(
        contributor_addr,
        ripe_token,
    )
    ripe_shares_before = ripe_gov_vault.totalBalances(ripe_token)
    alpha_position_before = simple_erc20_vault.getTotalAmountForUser(
        contributor_addr,
        alpha_token,
    )
    debt_before = ledger.userDebt(contributor_addr).amount
    assert debt_before == borrow_amount

    if should_revert:
        with boa.reverts("bad debt health"):
            human_resources.refundAfterCancelPaycheck(
                refund_amount,
                True,
                sender=contributor_addr,
            )

        assert ripe_gov_vault.getTotalAmountForUser(contributor_addr, ripe_token) == ripe_position_before
        assert ripe_gov_vault.totalBalances(ripe_token) == ripe_shares_before
        assert simple_erc20_vault.getTotalAmountForUser(contributor_addr, alpha_token) == alpha_position_before
        assert ripe_token.totalSupply() == supply_before
        assert ledger.ripeAvailForHr() == budget_before
        assert ledger.userDebt(contributor_addr).amount == debt_before
        return

    human_resources.refundAfterCancelPaycheck(refund_amount, True, sender=contributor_addr)

    assert ripe_gov_vault.getTotalAmountForUser(contributor_addr, ripe_token) == 0
    assert simple_erc20_vault.getTotalAmountForUser(contributor_addr, alpha_token) == alpha_position_before
    assert ripe_token.totalSupply() == supply_before - deposit_amount
    assert ledger.ripeAvailForHr() == budget_before + refund_amount
    debt = ledger.userDebt(contributor_addr).amount
    terms = credit_engine.getUserBorrowTerms(contributor_addr, False)
    assert debt == borrow_amount == terms.totalMaxDebt == post_burn_max_debt


def test_hr_refund_burn_honors_same_block_higher_risk_guard(
    human_resources,
    ripe_gov_vault,
    ripe_token,
    ledger,
    bob,
    teller,
    mission_control,
    switchboard_alpha,
    switchboard_charlie,
    setupRipeGovVaultConfig,
    setGeneralDebtConfig,
    mock_price_source,
    deployedContributor,
):
    setupRipeGovVaultConfig()
    setGeneralDebtConfig()
    mission_control.setShouldCheckLastTouch(True, sender=switchboard_alpha.address)
    mock_price_source.setPrice(ripe_token, EIGHTEEN_DECIMALS)
    contributor_addr = deployedContributor()

    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    human_resources.cashRipeCheck(deposit_amount, 500, sender=contributor_addr)
    mission_control.setUserDelegation(
        contributor_addr,
        bob,
        (False, True, False, False),
        sender=switchboard_charlie.address,
    )
    teller.borrow(1, contributor_addr, False, sender=bob)
    assert ledger.lastTouch(contributor_addr) == boa.env.evm.patch.block_number

    refund_amount = 25_000 * EIGHTEEN_DECIMALS
    position_before = ripe_gov_vault.getTotalAmountForUser(contributor_addr, ripe_token)
    supply_before = ripe_token.totalSupply()
    budget_before = ledger.ripeAvailForHr()
    debt_before = ledger.userDebt(contributor_addr).amount

    with boa.reverts("one action per block"):
        human_resources.refundAfterCancelPaycheck(
            refund_amount,
            True,
            sender=contributor_addr,
        )

    assert ripe_gov_vault.getTotalAmountForUser(contributor_addr, ripe_token) == position_before
    assert ripe_token.totalSupply() == supply_before
    assert ledger.ripeAvailForHr() == budget_before
    assert ledger.userDebt(contributor_addr).amount == debt_before


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


def test_hr_ripe_routes_follow_core_governance_vault_pointer(
    human_resources,
    ripe_gov_vault,
    alternate_ripe_gov_vault,
    registerVault,
    mission_control,
    switchboard_alpha,
    ripe_token,
    ledger,
    whale,
    teller,
    setupRipeGovVaultConfig,
    deployedContributor,
    setAssetConfig,
    alice,
):
    setupRipeGovVaultConfig()
    core_id = registerVault(alternate_ripe_gov_vault, "Core RipeGov")
    setAssetConfig(ripe_token, _vaultIds=[core_id])
    mission_control.setCoreRipeGovVaultId(core_id, sender=switchboard_alpha.address)
    contributor_addr = deployedContributor()

    assert not human_resources.hasRipeBalance(contributor_addr)
    assert human_resources.cashRipeCheck(
        50_000 * EIGHTEEN_DECIMALS,
        500,
        sender=contributor_addr,
    )
    assert human_resources.hasRipeBalance(contributor_addr)
    assert ripe_gov_vault.getTotalAmountForUser(contributor_addr, ripe_token) == 0

    transferred = human_resources.transferContributorRipeTokens(
        alice,
        200,
        sender=contributor_addr,
    )
    assert transferred > 0
    assert alternate_ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) == transferred

    deposit_amount = 1_000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(alternate_ripe_gov_vault, deposit_amount, sender=whale)
    alternate_ripe_gov_vault.depositTokensInVault(
        contributor_addr,
        ripe_token,
        deposit_amount,
        sender=teller.address,
    )
    ripe_available_before = ledger.ripeAvailForHr()
    human_resources.refundAfterCancelPaycheck(
        25_000 * EIGHTEEN_DECIMALS,
        True,
        sender=contributor_addr,
    )
    assert ledger.ripeAvailForHr() == ripe_available_before + 25_000 * EIGHTEEN_DECIMALS
    assert alternate_ripe_gov_vault.getTotalAmountForUser(contributor_addr, ripe_token) == 0


def test_hr_ripe_routes_fail_closed_when_core_pointer_is_unset(
    human_resources,
    mission_control,
    setupRipeGovVaultConfig,
    deployedContributor,
    alice,
):
    setupRipeGovVaultConfig()
    contributor_addr = deployedContributor()
    mission_control.eval("self.coreRipeGovVaultId = 0")

    with boa.reverts("invalid vault id"):
        human_resources.hasRipeBalance(contributor_addr)
    with boa.reverts("invalid vault id"):
        human_resources.transferContributorRipeTokens(alice, 200, sender=contributor_addr)
    with boa.reverts("invalid vault id"):
        human_resources.cashRipeCheck(50_000 * EIGHTEEN_DECIMALS, 500, sender=contributor_addr)
    with boa.reverts("invalid vault id"):
        human_resources.refundAfterCancelPaycheck(
            25_000 * EIGHTEEN_DECIMALS,
            True,
            sender=contributor_addr,
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
