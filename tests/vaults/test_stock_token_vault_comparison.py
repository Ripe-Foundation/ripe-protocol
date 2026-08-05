"""Behavioral evidence for the Track 5 scenario matrix.

Scenario traceability:
N-01/N-04 -> first/base-unit lifecycle
N-02/N-03 -> multi-user lifecycle and internal transfer
D-01/D-03 -> donation before first deposit, cleanup, and recovery
D-02 -> donation between deposits
M-01 -> short-received second deposit
L-01/B-01/R-01 -> partial issuer reductions, borrowing power, and Lootbox state
L-02/B-02/B-03 -> total-loss debt health and new borrowing
L-03 -> two-user withdrawal ordering
L-04 -> partial/total-loss deregistration and recovery constraints
Z-01/Z-02 -> donation/deposit after total loss
I-01/I-05 -> exact deposit and retry
I-02/I-06/I-07 -> pause across direct, external, and internal paths
I-03/I-04/I-08 -> role blocklists and external auction atomicity
A-01/A-02/A-03/A-04 -> pre-loss auction initiation and settlement
A-05 -> two-buyer ordering after partial loss
A-06/A-07 -> post-loss auction initiation and settlement
DV-01 -> Deleverage external-withdrawal path
E-01 -> vault and Teller event/state reconciliation
R-02 -> real Lootbox point-state updates after donation and loss
C-01 -> registry and required asset flags
"""

import boa
import pytest

from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from conf_utils import filter_logs


VAULT_CASES = (
    pytest.param("simple", 3, id="simple-erc20"),
    pytest.param("rebase", 4, id="rebase-erc20"),
)

@pytest.fixture(autouse=True)
def isolate_boa_storage_diagnostics():
    """Avoid Boa repr crashes from stale address/type trace metadata."""

    # These are diagnostic dictionaries, not EVM state. Keep the workaround
    # local because the proper shared fixture in tests/conftest.py is outside
    # this candidate's explicit authorization.
    assert isinstance(boa.env.sstore_trace, dict)
    assert isinstance(boa.env.sha3_trace, dict)
    boa.env.sstore_trace.clear()
    boa.env.sha3_trace.clear()
    yield
    boa.env.sstore_trace.clear()
    boa.env.sha3_trace.clear()


@pytest.fixture
def stock_token(deploy3r):
    return boa.load(
        "contracts/mock/MockStockTokenControls.vy",
        deploy3r,
        18,
        name="mock_stock_token_controls",
    )


def _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault):
    return simple_erc20_vault if vault_kind == "simple" else rebase_erc20_vault


def _configure_stock_asset(
    token,
    vault_id,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    *,
    should_auction=True,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=80_00,
        _liqFee=0,
        _borrowRate=0,
    )
    setAssetConfig(
        token,
        _vaultIds=[vault_id],
        _debtTerms=debt_terms,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=should_auction,
        _canRedeemCollateral=False,
    )


def _direct_deposit(token, vault, teller, user, amount, admin):
    token.mint(vault, amount, sender=admin)
    return vault.depositTokensInVault(user, token, amount, sender=teller.address)


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_liquidation_eligibility_after_total_issuer_burn(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    deploy3r,
    bob,
):
    """Total custody loss removes usable collateral from both vault models."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)

    deposit_amount = 200 * EIGHTEEN_DECIMALS
    debt_amount = 100 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, deposit_amount, sender=deploy3r)
    stock_token.approve(teller, deposit_amount, sender=bob)
    assert teller.deposit(stock_token, deposit_amount, bob, vault, sender=bob) == deposit_amount
    teller.borrow(debt_amount, bob, False, sender=bob)

    stock_token.adminBurn(vault, deposit_amount, sender=deploy3r)
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS // 2)

    assert stock_token.balanceOf(vault) == 0
    assert credit_engine.getUserDebtAmount(bob) == debt_amount
    assert credit_engine.canLiquidateUser(bob)
    assert credit_engine.getCollateralValue(bob) == 0


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_internal_auction_after_total_issuer_burn(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    green_token,
    whale,
    deploy3r,
    bob,
    alice,
    sally,
):
    """A liquidator must not pay GREEN for collateral with zero live custody."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)

    deposit_amount = 200 * EIGHTEEN_DECIMALS
    debt_amount = 100 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, deposit_amount, sender=deploy3r)
    stock_token.approve(teller, deposit_amount, sender=bob)
    deposited = teller.deposit(stock_token, deposit_amount, bob, vault, sender=bob)
    assert deposited == deposit_amount
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Open the auction while both vaults still hold the collateral. This isolates
    # settlement behavior from RebaseErc20's separate post-zero liquidation
    # eligibility behavior.
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS // 2)
    assert credit_engine.canLiquidateUser(bob)
    teller.liquidateUser(bob, False, sender=sally)
    assert ledger.hasFungibleAuction(bob, vault_id, stock_token)

    # Exercise issuer authority rather than impersonating the vault after the
    # auction exists.
    stock_token.adminBurn(vault, deposit_amount, sender=deploy3r)
    assert stock_token.balanceOf(vault) == 0

    payment = 20 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    alice_green_before = green_token.balanceOf(alice)
    debt_before = credit_engine.getUserDebtAmount(bob)

    with boa.reverts("no green spent"):
        teller.buyFungibleAuction(
            bob,
            vault_id,
            stock_token,
            payment,
            False,
            True,
            False,
            sender=alice,
        )

    assert green_token.balanceOf(alice) == alice_green_before
    assert credit_engine.getUserDebtAmount(bob) == debt_before
    assert vault.getTotalAmountForUser(alice, stock_token) == 0
    assert stock_token.balanceOf(alice) == 0
    assert stock_token.balanceOf(vault) == 0


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
@pytest.mark.parametrize("bob_withdraws_first", (True, False), ids=("bob-first", "alice-first"))
def test_partial_loss_withdrawal_order(
    vault_kind,
    vault_id,
    bob_withdraws_first,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    teller,
    deploy3r,
    bob,
    alice,
):
    """Simple freezes partial loss; Rebase continues pro-rata withdrawals."""

    del vault_id
    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    amount = 100 * EIGHTEEN_DECIMALS
    assert _direct_deposit(stock_token, vault, teller, bob, amount, deploy3r) == amount
    assert _direct_deposit(stock_token, vault, teller, alice, amount, deploy3r) == amount

    stock_token.adminBurn(vault, amount, sender=deploy3r)
    assert stock_token.balanceOf(vault) == amount

    first = bob if bob_withdraws_first else alice
    second = alice if bob_withdraws_first else bob
    if vault_kind == "simple":
        for user in (first, second):
            with boa.reverts("insufficient vault backing"):
                vault.withdrawTokensFromVault(
                    user,
                    stock_token,
                    MAX_UINT256,
                    user,
                    sender=teller.address,
                )
            assert vault.getTotalAmountForUser(user, stock_token) == 0
            assert vault.userBalances(user, stock_token) == amount
        assert stock_token.balanceOf(vault) == amount
        return

    first_amount, first_depleted = vault.withdrawTokensFromVault(
        first,
        stock_token,
        MAX_UINT256,
        first,
        sender=teller.address,
    )
    assert first_depleted

    second_amount, second_depleted = vault.withdrawTokensFromVault(
        second,
        stock_token,
        MAX_UINT256,
        second,
        sender=teller.address,
    )
    assert second_depleted
    assert abs(first_amount - second_amount) <= 1
    assert amount - 2 <= first_amount + second_amount <= amount
    assert stock_token.balanceOf(vault) <= 2


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_donation_between_deposits_and_common_views(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    teller,
    deploy3r,
    bob,
    alice,
):
    """Donation allocation and raw/common views remain intentionally distinct."""

    del vault_id
    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    amount = 100 * EIGHTEEN_DECIMALS
    assert _direct_deposit(stock_token, vault, teller, bob, amount, deploy3r) == amount

    bob_raw_before = vault.userBalances(bob, stock_token)
    bob_loot_before = vault.getUserLootBoxShare(bob, stock_token)
    stock_token.mint(vault, amount, sender=deploy3r)

    bob_claim_after_donation = vault.getTotalAmountForUser(bob, stock_token)
    assert vault.getUserLootBoxShare(bob, stock_token) == bob_loot_before
    assert vault.userBalances(bob, stock_token) == bob_raw_before
    assert _direct_deposit(stock_token, vault, teller, alice, amount, deploy3r) == amount

    actual = stock_token.balanceOf(vault)
    bob_claim = vault.getTotalAmountForUser(bob, stock_token)
    alice_claim = vault.getTotalAmountForUser(alice, stock_token)
    assert actual == 3 * amount

    if vault_kind == "simple":
        assert bob_claim_after_donation == amount
        assert bob_claim == amount
        assert alice_claim == amount
        assert vault.getTotalAmountForVault(stock_token) == 2 * amount
        assert vault.totalBalances(stock_token) == 2 * amount
    else:
        assert 2 * amount - 2 <= bob_claim_after_donation <= 2 * amount
        assert 2 * amount - 2 <= bob_claim <= 2 * amount
        assert amount - 2 <= alice_claim <= amount
        assert actual - 3 <= bob_claim + alice_claim <= actual
        assert vault.getTotalAmountForVault(stock_token) == actual
        assert vault.getUserLootBoxShare(bob, stock_token) == bob_raw_before // 10**8


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_donation_before_first_deposit_can_be_deregistered_and_recovered(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    teller,
    lootbox,
    switchboard_alpha,
    deploy3r,
    bob,
    sally,
):
    """Unallocated/dead-share donation residue is recoverable only after cleanup."""

    del vault_id
    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    donation = 100 * EIGHTEEN_DECIMALS
    deposit = 100 * EIGHTEEN_DECIMALS
    stock_token.mint(vault, donation, sender=deploy3r)
    assert _direct_deposit(stock_token, vault, teller, bob, deposit, deploy3r) == deposit

    expected_withdrawn = vault.getTotalAmountForUser(bob, stock_token)
    withdrawn, depleted = vault.withdrawTokensFromVault(
        bob,
        stock_token,
        MAX_UINT256,
        bob,
        sender=teller.address,
    )
    assert depleted
    assert withdrawn == expected_withdrawn
    if vault_kind == "simple":
        assert withdrawn == deposit
    else:
        # The pre-deposit donation and SharesVault's virtual assets/shares dilute
        # the first depositor by about 0.0000005 token at this scale.
        assert deposit - 10**12 <= withdrawn < deposit
    assert vault.totalBalances(stock_token) == 0
    assert stock_token.balanceOf(vault) == donation + deposit - withdrawn

    # False means Bob has no other registered assets remaining after this one.
    assert not vault.deregisterUserAsset(bob, stock_token, sender=lootbox.address)
    assert vault.deregisterVaultAsset(stock_token, sender=switchboard_alpha.address)

    residue = stock_token.balanceOf(vault)
    sally_before = stock_token.balanceOf(sally)
    vault.recoverFunds(sally, stock_token, sender=switchboard_alpha.address)
    assert stock_token.balanceOf(vault) == 0
    assert stock_token.balanceOf(sally) == sally_before + residue


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_issuer_pause_blocks_external_transfer_but_not_internal_balance_transfer(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    teller,
    auction_house,
    deploy3r,
    bob,
    alice,
):
    """Internal accounting can move while the issuer has stopped token movement."""

    del vault_id
    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    amount = 100 * EIGHTEEN_DECIMALS
    transfer_amount = 40 * EIGHTEEN_DECIMALS
    assert _direct_deposit(stock_token, vault, teller, bob, amount, deploy3r) == amount

    stock_token.setPaused(True, sender=deploy3r)
    moved, _ = vault.transferBalanceWithinVault(
        stock_token,
        bob,
        alice,
        transfer_amount,
        sender=auction_house.address,
    )
    assert moved == transfer_amount
    alice_claim = vault.getTotalAmountForUser(alice, stock_token)
    assert alice_claim == transfer_amount

    with boa.reverts("token paused"):
        vault.withdrawTokensFromVault(
            alice,
            stock_token,
            transfer_amount,
            alice,
            sender=teller.address,
        )
    assert vault.getTotalAmountForUser(alice, stock_token) == alice_claim

    stock_token.setPaused(False, sender=deploy3r)
    withdrawn, depleted = vault.withdrawTokensFromVault(
        alice,
        stock_token,
        transfer_amount,
        alice,
        sender=teller.address,
    )
    assert withdrawn == transfer_amount
    assert depleted


DEPOSIT_BLOCKLIST_CASES = (
    pytest.param("setSenderBlocked", "sender blocked", id="borrower-as-sender"),
    pytest.param("setRecipientBlocked", "recipient blocked", id="vault-as-recipient"),
    pytest.param("setOperatorBlocked", "operator blocked", id="teller-as-operator"),
)


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
@pytest.mark.parametrize(("setter_name", "revert_reason"), DEPOSIT_BLOCKLIST_CASES)
def test_deposit_blocklist_roles_and_retry(
    vault_kind,
    vault_id,
    setter_name,
    revert_reason,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    teller,
    deploy3r,
    bob,
):
    """Deposit identifies borrower, vault, and Teller ERC-20 roles separately."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    amount = 100 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, amount, sender=deploy3r)
    stock_token.approve(teller, amount, sender=bob)

    blocked = bob
    if setter_name == "setRecipientBlocked":
        blocked = vault.address
    elif setter_name == "setOperatorBlocked":
        blocked = teller.address
    setter = getattr(stock_token, setter_name)
    setter(blocked, True, sender=deploy3r)

    with boa.reverts(revert_reason):
        teller.deposit(stock_token, amount, bob, vault, sender=bob)
    assert stock_token.balanceOf(vault) == 0
    assert vault.getTotalAmountForUser(bob, stock_token) == 0

    setter(blocked, False, sender=deploy3r)
    assert teller.deposit(stock_token, amount, bob, vault, sender=bob) == amount


WITHDRAW_BLOCKLIST_CASES = (
    pytest.param("setSenderBlocked", "sender blocked", id="vault-as-sender"),
    pytest.param("setRecipientBlocked", "recipient blocked", id="user-as-recipient"),
    pytest.param("setOperatorBlocked", "operator blocked", id="vault-as-operator"),
)


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
@pytest.mark.parametrize(("setter_name", "revert_reason"), WITHDRAW_BLOCKLIST_CASES)
def test_withdraw_blocklist_roles_and_retry(
    vault_kind,
    vault_id,
    setter_name,
    revert_reason,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    teller,
    deploy3r,
    bob,
):
    """Withdrawal identifies the vault as sender/operator and user as recipient."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    amount = 100 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, amount, sender=deploy3r)
    stock_token.approve(teller, amount, sender=bob)
    teller.deposit(stock_token, amount, bob, vault, sender=bob)
    claim_before = vault.getTotalAmountForUser(bob, stock_token)

    blocked = vault.address
    if setter_name == "setRecipientBlocked":
        blocked = bob
    setter = getattr(stock_token, setter_name)
    setter(blocked, True, sender=deploy3r)

    with boa.reverts(revert_reason):
        teller.withdraw(stock_token, amount // 2, bob, vault, sender=bob)
    assert vault.getTotalAmountForUser(bob, stock_token) == claim_before

    setter(blocked, False, sender=deploy3r)
    assert teller.withdraw(stock_token, amount // 2, bob, vault, sender=bob) == amount // 2


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_short_received_after_existing_user_backing_reverts_atomically(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    teller,
    deploy3r,
    bob,
    alice,
):
    """Call-local custody delta rejects the primary multi-user masking path."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    requested = 100 * EIGHTEEN_DECIMALS

    stock_token.mint(bob, requested, sender=deploy3r)
    stock_token.approve(teller, requested, sender=bob)
    first_reported = teller.deposit(stock_token, requested, bob, vault, sender=bob)
    assert first_reported == requested

    raw_total_before = vault.totalBalances(stock_token)
    custody_before = stock_token.balanceOf(vault)
    bob_claim_before = vault.getTotalAmountForUser(bob, stock_token)
    stock_token.mint(alice, requested, sender=deploy3r)
    stock_token.approve(teller, requested, sender=alice)
    stock_token.setUpgradeBehavior(3, sender=deploy3r)

    with boa.reverts():
        teller.deposit(stock_token, requested, alice, vault, sender=alice)

    assert stock_token.balanceOf(alice) == requested
    assert stock_token.balanceOf(vault) == custody_before
    assert vault.totalBalances(stock_token) == raw_total_before
    assert vault.getTotalAmountForUser(bob, stock_token) == bob_claim_before
    assert vault.getTotalAmountForUser(alice, stock_token) == 0
    assert filter_logs(teller, "TellerDeposit") == []


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_donation_cannot_mask_short_current_receipt(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    teller,
    ledger,
    deploy3r,
    bob,
):
    """A pre-existing custody surplus cannot substitute for this call's receipt."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    requested = 100 * EIGHTEEN_DECIMALS
    donation = 25 * EIGHTEEN_DECIMALS
    stock_token.mint(vault, donation, sender=deploy3r)
    stock_token.mint(bob, requested, sender=deploy3r)
    stock_token.approve(teller, requested, sender=bob)
    stock_token.setUpgradeBehavior(3, sender=deploy3r)

    with boa.reverts():
        teller.deposit(stock_token, requested, bob, vault, sender=bob)

    assert stock_token.balanceOf(bob) == requested
    assert stock_token.balanceOf(vault) == donation
    assert vault.totalBalances(stock_token) == 0
    assert vault.getTotalAmountForUser(bob, stock_token) == 0
    assert ledger.getNumUserVaults(bob) == 0
    assert filter_logs(teller, "TellerDeposit") == []


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
@pytest.mark.parametrize("decimals", (6, 18), ids=("six-decimals", "eighteen-decimals"))
def test_first_deposit_and_withdrawal_at_token_decimals(
    vault_kind,
    vault_id,
    decimals,
    simple_erc20_vault,
    rebase_erc20_vault,
    teller,
    deploy3r,
    bob,
):
    """Both vaults accept exact base units independently of token decimals."""

    del vault_id
    token = boa.load(
        "contracts/mock/MockStockTokenControls.vy",
        deploy3r,
        decimals,
        name=f"mock_stock_token_{vault_kind}_{decimals}",
    )
    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    amount = 123 * 10**decimals + 7
    assert _direct_deposit(token, vault, teller, bob, amount, deploy3r) == amount
    withdrawn, depleted = vault.withdrawTokensFromVault(
        bob,
        token,
        MAX_UINT256,
        bob,
        sender=teller.address,
    )
    assert depleted
    assert amount - 1 <= withdrawn <= amount


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_external_auction_after_total_issuer_burn_reverts_atomically(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    green_token,
    whale,
    deploy3r,
    bob,
    alice,
    sally,
):
    """External settlement cannot charge GREEN when the token transfer cannot occur."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)

    deposit_amount = 200 * EIGHTEEN_DECIMALS
    debt_amount = 100 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, deposit_amount, sender=deploy3r)
    stock_token.approve(teller, deposit_amount, sender=bob)
    teller.deposit(stock_token, deposit_amount, bob, vault, sender=bob)
    teller.borrow(debt_amount, bob, False, sender=bob)
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS // 2)
    teller.liquidateUser(bob, False, sender=sally)
    assert ledger.hasFungibleAuction(bob, vault_id, stock_token)
    stock_token.adminBurn(vault, deposit_amount, sender=deploy3r)

    payment = 20 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    green_before = green_token.balanceOf(alice)
    debt_before = credit_engine.getUserDebtAmount(bob)
    with boa.reverts():
        teller.buyFungibleAuction(
            bob,
            vault_id,
            stock_token,
            payment,
            False,
            False,
            False,
            sender=alice,
        )

    assert green_token.balanceOf(alice) == green_before
    assert credit_engine.getUserDebtAmount(bob) == debt_before
    assert stock_token.balanceOf(alice) == 0
    assert ledger.hasFungibleAuction(bob, vault_id, stock_token)


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_normal_multi_user_lifecycle_and_internal_transfer(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    teller,
    auction_house,
    deploy3r,
    bob,
    alice,
):
    """Equivalent ordinary deposits, transfers, and withdrawals reconcile."""

    del vault_id
    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    bob_amount = 100 * EIGHTEEN_DECIMALS
    alice_amount = 60 * EIGHTEEN_DECIMALS
    moved_amount = 20 * EIGHTEEN_DECIMALS

    assert _direct_deposit(stock_token, vault, teller, bob, bob_amount, deploy3r) == bob_amount
    assert _direct_deposit(stock_token, vault, teller, alice, alice_amount, deploy3r) == alice_amount
    moved, depleted = vault.transferBalanceWithinVault(
        stock_token,
        bob,
        alice,
        moved_amount,
        sender=auction_house.address,
    )
    assert moved == moved_amount
    assert not depleted
    assert vault.getTotalAmountForUser(bob, stock_token) == bob_amount - moved_amount
    assert vault.getTotalAmountForUser(alice, stock_token) == alice_amount + moved_amount

    partial, depleted = vault.withdrawTokensFromVault(
        bob,
        stock_token,
        30 * EIGHTEEN_DECIMALS,
        bob,
        sender=teller.address,
    )
    assert partial == 30 * EIGHTEEN_DECIMALS
    assert not depleted

    alice_final, alice_depleted = vault.withdrawTokensFromVault(
        alice,
        stock_token,
        MAX_UINT256,
        alice,
        sender=teller.address,
    )
    bob_final, bob_depleted = vault.withdrawTokensFromVault(
        bob,
        stock_token,
        MAX_UINT256,
        bob,
        sender=teller.address,
    )
    assert alice_amount + moved_amount - 1 <= alice_final <= alice_amount + moved_amount
    assert bob_amount - moved_amount - partial - 1 <= bob_final <= bob_amount - moved_amount - partial
    assert alice_depleted and bob_depleted
    assert stock_token.balanceOf(vault) <= 2


ISSUER_REDUCTION_CASES = (
    pytest.param("adminBurn", id="administrative-burn"),
    pytest.param("forceRedeem", id="forced-redemption"),
    pytest.param("forceTransfer", id="forced-transfer"),
)


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
@pytest.mark.parametrize("issuer_action", ISSUER_REDUCTION_CASES)
def test_partial_issuer_reduction_updates_only_live_share_claims(
    vault_kind,
    vault_id,
    issuer_action,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    teller,
    deploy3r,
    bob,
    sally,
):
    """All modeled issuer reductions bypass VaultData in the same way."""

    del vault_id
    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    amount = 100 * EIGHTEEN_DECIMALS
    loss = 25 * EIGHTEEN_DECIMALS
    assert _direct_deposit(stock_token, vault, teller, bob, amount, deploy3r) == amount
    raw_before = vault.userBalances(bob, stock_token)
    loot_share_before = vault.getUserLootBoxShare(bob, stock_token)

    if issuer_action == "forceTransfer":
        stock_token.forceTransfer(vault, sally, loss, sender=deploy3r)
        assert stock_token.balanceOf(sally) == loss
    else:
        getattr(stock_token, issuer_action)(vault, loss, sender=deploy3r)

    assert stock_token.balanceOf(vault) == amount - loss
    assert vault.userBalances(bob, stock_token) == raw_before
    assert vault.getUserLootBoxShare(bob, stock_token) == loot_share_before
    if vault_kind == "simple":
        assert vault.getTotalAmountForUser(bob, stock_token) == 0
        assert vault.getTotalAmountForVault(stock_token) == amount
    else:
        assert amount - loss - 1 <= vault.getTotalAmountForUser(bob, stock_token) <= amount - loss
        assert vault.getTotalAmountForVault(stock_token) == amount - loss


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_donation_after_total_loss_revalues_only_share_claims(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    teller,
    deploy3r,
    bob,
):
    """A later unallocated balance restores old Rebase claims but not nominal solvency."""

    del vault_id
    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    amount = 100 * EIGHTEEN_DECIMALS
    donation = 25 * EIGHTEEN_DECIMALS
    assert _direct_deposit(stock_token, vault, teller, bob, amount, deploy3r) == amount
    stock_token.adminBurn(vault, amount, sender=deploy3r)
    assert stock_token.balanceOf(vault) == 0
    stock_token.mint(vault, donation, sender=deploy3r)

    if vault_kind == "simple":
        assert vault.getTotalAmountForUser(bob, stock_token) == 0
        assert vault.getTotalAmountForVault(stock_token) == amount
    else:
        assert donation - 1 <= vault.getTotalAmountForUser(bob, stock_token) <= donation
        assert vault.getTotalAmountForVault(stock_token) == donation


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_new_deposit_after_total_loss_with_old_accounting(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    teller,
    deploy3r,
    bob,
    alice,
):
    """Fresh deposits after zero expose stale-nominal capture versus share dilution."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    old_amount = 100 * EIGHTEEN_DECIMALS
    fresh_amount = 50 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, old_amount, sender=deploy3r)
    stock_token.approve(teller, old_amount, sender=bob)
    assert teller.deposit(stock_token, old_amount, bob, vault, sender=bob) == old_amount
    stock_token.adminBurn(vault, old_amount, sender=deploy3r)

    if vault_kind == "simple":
        stock_token.mint(alice, fresh_amount, sender=deploy3r)
        stock_token.approve(teller, fresh_amount, sender=alice)
        with boa.reverts("insufficient vault backing"):
            teller.deposit(stock_token, fresh_amount, alice, vault, sender=alice)
        assert stock_token.balanceOf(alice) == fresh_amount
        assert stock_token.balanceOf(vault) == 0
        assert vault.getTotalAmountForUser(bob, stock_token) == 0
        assert vault.getTotalAmountForUser(alice, stock_token) == 0
        assert vault.userBalances(bob, stock_token) == old_amount
    else:
        stock_token.mint(alice, fresh_amount, sender=deploy3r)
        stock_token.approve(teller, fresh_amount, sender=alice)
        assert teller.deposit(
            stock_token, fresh_amount, alice, vault, sender=alice
        ) == fresh_amount
        assert stock_token.balanceOf(vault) == fresh_amount
        # With live assets at zero but old shares outstanding, the fresh deposit
        # mints against a virtual one-unit denominator. Old shares are diluted to
        # a zero-rounded claim and the fresh depositor owns the live balance.
        assert vault.getTotalAmountForUser(bob, stock_token) == 0
        assert fresh_amount - 1 <= vault.getTotalAmountForUser(alice, stock_token) <= fresh_amount
        assert fresh_amount - 1 <= teller.withdraw(
            stock_token,
            MAX_UINT256,
            alice,
            vault,
            sender=alice,
        ) <= fresh_amount


TRANSFER_GUARD_CASES = (
    pytest.param("pause", 0, id="issuer-pause"),
    pytest.param("upgrade", 1, id="upgrade-revert"),
    pytest.param("upgrade", 2, id="upgrade-false-return"),
)


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
@pytest.mark.parametrize(("guard_kind", "upgrade_mode"), TRANSFER_GUARD_CASES)
def test_transfer_guards_block_deposit_atomically_and_retry(
    vault_kind,
    vault_id,
    guard_kind,
    upgrade_mode,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    teller,
    deploy3r,
    bob,
):
    """Pause and behavior-switch failures leave both deposits atomic and retryable."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    amount = 100 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, amount, sender=deploy3r)
    stock_token.approve(teller, amount, sender=bob)
    if guard_kind == "pause":
        stock_token.setPaused(True, sender=deploy3r)
    else:
        stock_token.setUpgradeBehavior(upgrade_mode, sender=deploy3r)

    with boa.reverts():
        teller.deposit(stock_token, amount, bob, vault, sender=bob)
    assert stock_token.balanceOf(bob) == amount
    assert stock_token.balanceOf(vault) == 0
    assert vault.getTotalAmountForUser(bob, stock_token) == 0

    if guard_kind == "pause":
        stock_token.setPaused(False, sender=deploy3r)
    else:
        stock_token.setUpgradeBehavior(0, sender=deploy3r)
    assert teller.deposit(stock_token, amount, bob, vault, sender=bob) == amount


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
@pytest.mark.parametrize(
    "should_transfer_balance",
    (True, False),
    ids=("internal-balance-transfer", "external-token-transfer"),
)
def test_auction_after_partial_issuer_loss_reconciles_payment_and_delivery(
    vault_kind,
    vault_id,
    should_transfer_balance,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    green_token,
    whale,
    deploy3r,
    bob,
    alice,
    sally,
):
    """Both modes settle while enough live collateral remains after a partial loss."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    debt_amount = 100 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, deposit_amount, sender=deploy3r)
    stock_token.approve(teller, deposit_amount, sender=bob)
    teller.deposit(stock_token, deposit_amount, bob, vault, sender=bob)
    teller.borrow(debt_amount, bob, False, sender=bob)
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS // 2)
    teller.liquidateUser(bob, False, sender=sally)
    assert ledger.hasFungibleAuction(bob, vault_id, stock_token)

    stock_token.adminBurn(vault, 100 * EIGHTEEN_DECIMALS, sender=deploy3r)
    payment = 20 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    green_before = green_token.balanceOf(alice)
    debt_before = credit_engine.getUserDebtAmount(bob)
    vault_live_before = stock_token.balanceOf(vault)

    if vault_kind == "simple":
        with boa.reverts("no green spent"):
            teller.buyFungibleAuction(
                bob,
                vault_id,
                stock_token,
                payment,
                False,
                should_transfer_balance,
                False,
                sender=alice,
            )
        assert green_token.balanceOf(alice) == green_before
        assert credit_engine.getUserDebtAmount(bob) == debt_before
        assert stock_token.balanceOf(vault) == vault_live_before
        assert stock_token.balanceOf(alice) == 0
        assert vault.getTotalAmountForUser(alice, stock_token) == 0
        assert ledger.hasFungibleAuction(bob, vault_id, stock_token)

        # Keeping the auction active is intentional: if issuer backing returns
        # before expiry, the same auction recovers without a Switchboard call.
        stock_token.mint(
            vault,
            100 * EIGHTEEN_DECIMALS,
            sender=deploy3r,
        )
        assert teller.buyFungibleAuction(
            bob,
            vault_id,
            stock_token,
            payment,
            False,
            should_transfer_balance,
            False,
            sender=alice,
        ) == payment
        assert green_token.balanceOf(alice) == green_before - payment
        assert credit_engine.getUserDebtAmount(bob) == debt_before - payment
        return

    green_spent = teller.buyFungibleAuction(
        bob, vault_id, stock_token, payment, False,
        should_transfer_balance, False, sender=alice,
    )
    assert green_spent == payment
    assert green_token.balanceOf(alice) == green_before - payment
    assert credit_engine.getUserDebtAmount(bob) == debt_before - payment

    collateral = 40 * EIGHTEEN_DECIMALS
    if should_transfer_balance:
        assert stock_token.balanceOf(alice) == 0
        assert collateral - 1 <= vault.getTotalAmountForUser(alice, stock_token) <= collateral
        assert stock_token.balanceOf(vault) == vault_live_before
    else:
        assert collateral - 1 <= stock_token.balanceOf(alice) <= collateral
        assert vault_live_before - collateral <= stock_token.balanceOf(vault) <= vault_live_before - collateral + 1


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_deleverage_external_withdrawal_after_partial_and_total_loss(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    deleverage,
    switchboard_alpha,
    deploy3r,
    bob,
):
    """The governance volatile-asset path is live-backed and atomic at zero."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    debt_amount = 100 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, deposit_amount, sender=deploy3r)
    stock_token.approve(teller, deposit_amount, sender=bob)
    teller.deposit(stock_token, deposit_amount, bob, vault, sender=bob)
    teller.borrow(debt_amount, bob, False, sender=bob)
    stock_token.adminBurn(vault, 100 * EIGHTEEN_DECIMALS, sender=deploy3r)

    target = 20 * EIGHTEEN_DECIMALS
    debt_before = credit_engine.getUserDebtAmount(bob)
    if vault_kind == "simple":
        with boa.reverts():
            deleverage.deleverageWithVolAssets(
                bob,
                [(vault_id, stock_token.address, target)],
                sender=switchboard_alpha.address,
            )
        assert credit_engine.getUserDebtAmount(bob) == debt_before
        assert stock_token.balanceOf(vault) == 100 * EIGHTEEN_DECIMALS
        return

    assert deleverage.deleverageWithVolAssets(
        bob,
        [(vault_id, stock_token.address, target)],
        sender=switchboard_alpha.address,
    ) == target
    assert credit_engine.getUserDebtAmount(bob) == debt_before - target
    assert stock_token.balanceOf(vault) == 80 * EIGHTEEN_DECIMALS

    stock_token.adminBurn(vault, stock_token.balanceOf(vault), sender=deploy3r)
    debt_before_zero_attempt = credit_engine.getUserDebtAmount(bob)
    with boa.reverts():
        deleverage.deleverageWithVolAssets(
            bob,
            [(vault_id, stock_token.address, target)],
            sender=switchboard_alpha.address,
        )
    assert credit_engine.getUserDebtAmount(bob) == debt_before_zero_attempt
    assert stock_token.balanceOf(vault) == 0


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_registry_and_required_asset_flags(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mission_control,
    vault_book,
    bob,
):
    """The harness pins test IDs and the required Robinhood risk flags."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    assert vault_book.getRegId(vault) == vault_id
    assert mission_control.getFirstVaultIdForAsset(stock_token) == vault_id
    redeem_config = mission_control.getRedeemCollateralConfig(stock_token, bob)
    liq_config = mission_control.getAssetLiqConfig(stock_token)
    assert not redeem_config.canRedeemCollateralAsset
    assert not liq_config.shouldSwapInStabPools


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_new_borrow_after_total_issuer_burn(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    deploy3r,
    bob,
):
    """Neither protected nominal nor share accounting permits missing custody debt."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
    amount = 100 * EIGHTEEN_DECIMALS
    borrow_amount = 40 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, amount, sender=deploy3r)
    stock_token.approve(teller, amount, sender=bob)
    teller.deposit(stock_token, amount, bob, vault, sender=bob)
    stock_token.adminBurn(vault, amount, sender=deploy3r)

    with boa.reverts():
        teller.borrow(borrow_amount, bob, False, sender=bob)
    assert credit_engine.getUserDebtAmount(bob) == 0


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_paused_external_auction_purchase_is_atomic_and_retryable(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    green_token,
    whale,
    deploy3r,
    bob,
    alice,
    sally,
):
    """An issuer pause cannot strand GREEN in a failed external settlement."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, deposit_amount, sender=deploy3r)
    stock_token.approve(teller, deposit_amount, sender=bob)
    teller.deposit(stock_token, deposit_amount, bob, vault, sender=bob)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS // 2)
    teller.liquidateUser(bob, False, sender=sally)
    assert ledger.hasFungibleAuction(bob, vault_id, stock_token)

    payment = 20 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    stock_token.setPaused(True, sender=deploy3r)
    green_before = green_token.balanceOf(alice)
    debt_before = credit_engine.getUserDebtAmount(bob)

    with boa.reverts("token paused"):
        teller.buyFungibleAuction(
            bob,
            vault_id,
            stock_token,
            payment,
            False,
            False,
            False,
            sender=alice,
        )
    assert green_token.balanceOf(alice) == green_before
    assert credit_engine.getUserDebtAmount(bob) == debt_before
    assert stock_token.balanceOf(alice) == 0

    stock_token.setPaused(False, sender=deploy3r)
    assert teller.buyFungibleAuction(
        bob,
        vault_id,
        stock_token,
        payment,
        False,
        False,
        False,
        sender=alice,
    ) == payment
    assert stock_token.balanceOf(alice) == 40 * EIGHTEEN_DECIMALS


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_one_base_unit_lifecycle(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    teller,
    deploy3r,
    bob,
):
    """The smallest positive unit survives the empty-vault conversion."""

    del vault_id
    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    assert _direct_deposit(stock_token, vault, teller, bob, 1, deploy3r) == 1
    withdrawn, depleted = vault.withdrawTokensFromVault(
        bob,
        stock_token,
        MAX_UINT256,
        bob,
        sender=teller.address,
    )
    assert withdrawn == 1
    assert depleted
    assert stock_token.balanceOf(vault) == 0


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_vault_events_reconcile_amounts_shares_and_state(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    teller,
    auction_house,
    deploy3r,
    bob,
    alice,
):
    """E-01: emitted token amounts and share fields equal resulting state deltas."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    transfer_amount = 20 * EIGHTEEN_DECIMALS
    withdrawal_amount = 30 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, deposit_amount, sender=deploy3r)
    stock_token.approve(teller, deposit_amount, sender=bob)

    raw_before = vault.userBalances(bob, stock_token)
    assert teller.deposit(stock_token, deposit_amount, bob, vault, sender=bob) == deposit_amount
    raw_after_deposit = vault.userBalances(bob, stock_token)
    teller_deposit = filter_logs(teller, "TellerDeposit")
    assert len(teller_deposit) == 1
    assert teller_deposit[0].amount == deposit_amount
    if vault_kind == "simple":
        deposit_event = filter_logs(teller, "SimpleErc20VaultDeposit")
        assert len(deposit_event) == 1
        assert deposit_event[0].amount == deposit_amount
        assert raw_after_deposit - raw_before == deposit_amount
    else:
        deposit_event = filter_logs(teller, "RebaseErc20VaultDeposit")
        assert len(deposit_event) == 1
        assert deposit_event[0].amount == deposit_amount
        assert deposit_event[0].shares == raw_after_deposit - raw_before

    bob_raw_before_transfer = vault.userBalances(bob, stock_token)
    alice_raw_before_transfer = vault.userBalances(alice, stock_token)
    moved, depleted = vault.transferBalanceWithinVault(
        stock_token,
        bob,
        alice,
        transfer_amount,
        sender=auction_house.address,
    )
    assert moved == transfer_amount
    assert not depleted
    if vault_kind == "simple":
        transfer_event = filter_logs(vault, "SimpleErc20VaultTransfer")
    else:
        transfer_event = filter_logs(vault, "RebaseErc20VaultTransfer")
    bob_raw_after_transfer = vault.userBalances(bob, stock_token)
    alice_raw_after_transfer = vault.userBalances(alice, stock_token)
    if vault_kind == "simple":
        assert len(transfer_event) == 1
        assert transfer_event[0].transferAmount == transfer_amount
        assert bob_raw_before_transfer - bob_raw_after_transfer == transfer_amount
        assert alice_raw_after_transfer - alice_raw_before_transfer == transfer_amount
    else:
        assert len(transfer_event) == 1
        transferred_shares = bob_raw_before_transfer - bob_raw_after_transfer
        assert transfer_event[0].transferAmount == transfer_amount
        assert transfer_event[0].transferShares == transferred_shares
        assert alice_raw_after_transfer - alice_raw_before_transfer == transferred_shares

    bob_raw_before_withdrawal = vault.userBalances(bob, stock_token)
    bob_token_before = stock_token.balanceOf(bob)
    withdrawn = teller.withdraw(
        stock_token,
        withdrawal_amount,
        bob,
        vault,
        sender=bob,
    )
    assert withdrawn == withdrawal_amount
    assert stock_token.balanceOf(bob) - bob_token_before == withdrawn
    teller_withdrawal = filter_logs(teller, "TellerWithdrawal")
    assert len(teller_withdrawal) == 1
    assert teller_withdrawal[0].amount == withdrawn
    bob_raw_after_withdrawal = vault.userBalances(bob, stock_token)
    if vault_kind == "simple":
        withdrawal_event = filter_logs(teller, "SimpleErc20VaultWithdrawal")
        assert len(withdrawal_event) == 1
        assert withdrawal_event[0].amount == withdrawn
        assert bob_raw_before_withdrawal - bob_raw_after_withdrawal == withdrawn
    else:
        withdrawal_event = filter_logs(teller, "RebaseErc20VaultWithdrawal")
        assert len(withdrawal_event) == 1
        withdrawn_shares = bob_raw_before_withdrawal - bob_raw_after_withdrawal
        assert withdrawal_event[0].amount == withdrawn
        assert withdrawal_event[0].shares == withdrawn_shares


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
@pytest.mark.parametrize(
    "should_transfer_balance",
    (True, False),
    ids=("internal-balance-transfer", "external-token-transfer"),
)
def test_auction_started_after_partial_issuer_loss_skips_deficient_simple(
    vault_kind,
    vault_id,
    should_transfer_balance,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    green_token,
    whale,
    deploy3r,
    bob,
    alice,
    sally,
):
    """A-06: deficient Simple is skipped while live Rebase collateral settles."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, deposit_amount, sender=deploy3r)
    stock_token.approve(teller, deposit_amount, sender=bob)
    teller.deposit(stock_token, deposit_amount, bob, vault, sender=bob)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # The issuer action precedes the price change and liquidation call.
    stock_token.adminBurn(vault, 100 * EIGHTEEN_DECIMALS, sender=deploy3r)
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS // 2)
    assert credit_engine.canLiquidateUser(bob)
    liquidation_result = teller.liquidateUser(bob, False, sender=sally)
    if vault_kind == "simple":
        assert liquidation_result == 0
        assert not ledger.hasFungibleAuction(bob, vault_id, stock_token)
        assert not ledger.userDebt(bob).inLiquidation
        return
    assert ledger.hasFungibleAuction(bob, vault_id, stock_token)

    payment = 20 * EIGHTEEN_DECIMALS
    collateral = 40 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    debt_before = credit_engine.getUserDebtAmount(bob)
    live_before = stock_token.balanceOf(vault)
    assert teller.buyFungibleAuction(
        bob, vault_id, stock_token, payment, False,
        should_transfer_balance, False, sender=alice,
    ) == payment
    assert credit_engine.getUserDebtAmount(bob) == debt_before - payment

    purchase_event = filter_logs(teller, "FungAuctionPurchased")
    assert len(purchase_event) == 1
    assert purchase_event[0].greenSpent == payment
    assert purchase_event[0].collateralAmountSent in (collateral, collateral - 1)
    assert purchase_event[0].collateralUsdValueSent == 20 * EIGHTEEN_DECIMALS
    if should_transfer_balance:
        assert stock_token.balanceOf(alice) == 0
        assert collateral - 1 <= vault.getTotalAmountForUser(alice, stock_token) <= collateral
        assert stock_token.balanceOf(vault) == live_before
    else:
        assert collateral - 1 <= stock_token.balanceOf(alice) <= collateral
        assert live_before - collateral <= stock_token.balanceOf(vault) <= live_before - collateral + 1


@pytest.mark.parametrize(
    ("vault_kind", "vault_id"),
    VAULT_CASES,
)
def test_auction_started_after_total_issuer_loss(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    green_token,
    whale,
    deploy3r,
    bob,
    alice,
    sally,
):
    """A-07: total-loss positions are liquidatable but create no empty auction."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, deposit_amount, sender=deploy3r)
    stock_token.approve(teller, deposit_amount, sender=bob)
    teller.deposit(stock_token, deposit_amount, bob, vault, sender=bob)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    stock_token.adminBurn(vault, deposit_amount, sender=deploy3r)
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS // 2)

    assert credit_engine.canLiquidateUser(bob)
    liquidation_result = teller.liquidateUser(bob, False, sender=sally)
    assert liquidation_result == 0
    assert not ledger.hasFungibleAuction(bob, vault_id, stock_token)
    assert not ledger.userDebt(bob).inLiquidation

    # Restoring issuer backing makes the same permissionless liquidation call
    # usable again; governance is not required to clear a permanent latch.
    stock_token.mint(vault, deposit_amount, sender=deploy3r)
    assert credit_engine.canLiquidateUser(bob)
    # Titanoboa 0.2.7 retains EIP-1153 values between simulated top-level
    # transactions; production EVMs clear them before this second call.
    boa.env.evm.vm.state.clear_transient_storage()
    teller.liquidateUser(bob, False, sender=sally)
    assert ledger.hasFungibleAuction(bob, vault_id, stock_token)
    assert ledger.userDebt(bob).inLiquidation


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_paused_internal_auction_purchase_charges_green_but_blocks_withdrawal(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    green_token,
    whale,
    deploy3r,
    bob,
    alice,
    sally,
):
    """I-07: a paused token does not stop a real internal auction settlement."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, deposit_amount, sender=deploy3r)
    stock_token.approve(teller, deposit_amount, sender=bob)
    teller.deposit(stock_token, deposit_amount, bob, vault, sender=bob)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS // 2)
    teller.liquidateUser(bob, False, sender=sally)

    payment = 20 * EIGHTEEN_DECIMALS
    collateral = 40 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    stock_token.setPaused(True, sender=deploy3r)
    green_before = green_token.balanceOf(alice)
    debt_before = credit_engine.getUserDebtAmount(bob)
    assert teller.buyFungibleAuction(
        bob,
        vault_id,
        stock_token,
        payment,
        False,
        True,
        False,
        sender=alice,
    ) == payment
    assert green_token.balanceOf(alice) == green_before - payment
    assert credit_engine.getUserDebtAmount(bob) == debt_before - payment
    assert collateral - 1 <= vault.getTotalAmountForUser(alice, stock_token) <= collateral
    assert stock_token.balanceOf(alice) == 0

    with boa.reverts("token paused"):
        teller.withdraw(stock_token, MAX_UINT256, alice, vault, sender=alice)
    stock_token.setPaused(False, sender=deploy3r)
    assert collateral - 1 <= teller.withdraw(
        stock_token,
        MAX_UINT256,
        alice,
        vault,
        sender=alice,
    ) <= collateral


EXTERNAL_AUCTION_BLOCKLIST_CASES = (
    pytest.param("setSenderBlocked", "sender blocked", id="vault-as-sender"),
    pytest.param("setRecipientBlocked", "recipient blocked", id="buyer-as-recipient"),
    pytest.param("setOperatorBlocked", "operator blocked", id="vault-as-operator"),
)


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
@pytest.mark.parametrize(("setter_name", "revert_reason"), EXTERNAL_AUCTION_BLOCKLIST_CASES)
def test_blocklisted_external_auction_purchase_is_atomic_and_retryable(
    vault_kind,
    vault_id,
    setter_name,
    revert_reason,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    green_token,
    whale,
    deploy3r,
    bob,
    alice,
    sally,
):
    """I-08: each external-auction ERC-20 role fails atomically and can retry."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, deposit_amount, sender=deploy3r)
    stock_token.approve(teller, deposit_amount, sender=bob)
    teller.deposit(stock_token, deposit_amount, bob, vault, sender=bob)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS // 2)
    teller.liquidateUser(bob, False, sender=sally)
    assert ledger.hasFungibleAuction(bob, vault_id, stock_token)

    payment = 20 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    blocked = alice if setter_name == "setRecipientBlocked" else vault.address
    setter = getattr(stock_token, setter_name)
    setter(blocked, True, sender=deploy3r)
    green_before = green_token.balanceOf(alice)
    debt_before = credit_engine.getUserDebtAmount(bob)
    live_before = stock_token.balanceOf(vault)

    with boa.reverts(revert_reason):
        teller.buyFungibleAuction(
            bob,
            vault_id,
            stock_token,
            payment,
            False,
            False,
            False,
            sender=alice,
        )
    assert green_token.balanceOf(alice) == green_before
    assert credit_engine.getUserDebtAmount(bob) == debt_before
    assert stock_token.balanceOf(vault) == live_before
    assert stock_token.balanceOf(alice) == 0
    assert ledger.hasFungibleAuction(bob, vault_id, stock_token)

    setter(blocked, False, sender=deploy3r)
    assert teller.buyFungibleAuction(
        bob,
        vault_id,
        stock_token,
        payment,
        False,
        False,
        False,
        sender=alice,
    ) == payment
    collateral = 40 * EIGHTEEN_DECIMALS
    if vault_kind == "simple":
        assert stock_token.balanceOf(alice) == collateral
    else:
        assert stock_token.balanceOf(alice) in (collateral, collateral - 1)


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
@pytest.mark.parametrize("loss_kind", ("partial", "total"))
def test_loss_state_blocks_deregistration_and_governance_recovery(
    vault_kind,
    vault_id,
    loss_kind,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    teller,
    lootbox,
    switchboard_alpha,
    deploy3r,
    bob,
    sally,
):
    """L-04: raw accounting blocks cleanup after partial and total issuer loss."""

    del vault_id
    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    amount = 100 * EIGHTEEN_DECIMALS
    assert _direct_deposit(stock_token, vault, teller, bob, amount, deploy3r) == amount
    loss = amount // 4 if loss_kind == "partial" else amount
    stock_token.adminBurn(vault, loss, sender=deploy3r)
    assert vault.userBalances(bob, stock_token) != 0
    assert vault.totalBalances(stock_token) != 0

    # True means Bob remains registered because this raw position still exists.
    assert vault.deregisterUserAsset(bob, stock_token, sender=lootbox.address)
    assert vault.isUserInVaultAsset(bob, stock_token)
    assert not vault.deregisterVaultAsset(stock_token, sender=switchboard_alpha.address)
    assert vault.isSupportedVaultAsset(stock_token)
    if loss_kind == "partial":
        with boa.reverts("invalid recovery"):
            vault.recoverFunds(sally, stock_token, sender=switchboard_alpha.address)
    else:
        with boa.reverts("nothing to recover"):
            vault.recoverFunds(sally, stock_token, sender=switchboard_alpha.address)


@pytest.mark.parametrize(("vault_kind", "vault_id"), VAULT_CASES)
def test_lootbox_points_update_after_donation_and_total_loss(
    vault_kind,
    vault_id,
    stock_token,
    simple_erc20_vault,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    setRipeRewardsConfig,
    mock_price_source,
    teller,
    ledger,
    lootbox,
    deploy3r,
    bob,
):
    """R-02: real Lootbox updates preserve user weight but refresh global value."""

    vault = _vault_for_case(vault_kind, simple_erc20_vault, rebase_erc20_vault)
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    setAssetConfig(
        stock_token,
        _vaultIds=[vault_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=20,
        _debtTerms=createDebtTerms(
            _ltv=50_00,
            _redemptionThreshold=60_00,
            _liqThreshold=80_00,
            _liqFee=0,
            _borrowRate=0,
        ),
        _shouldSwapInStabPools=False,
        _canRedeemCollateral=False,
    )
    setRipeRewardsConfig(True)
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
    amount = 100 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, amount, sender=deploy3r)
    stock_token.approve(teller, amount, sender=bob)
    teller.deposit(stock_token, amount, bob, vault, sender=bob)

    initial_user = ledger.userDepositPoints(bob, vault_id, stock_token)
    initial_asset = ledger.assetDepositPoints(vault_id, stock_token)
    expected_user_weight = vault.getUserLootBoxShare(bob, stock_token) // initial_asset.precision
    assert initial_user.lastBalance == expected_user_weight
    assert initial_asset.lastUsdValue == 100

    boa.env.time_travel(blocks=10)
    stock_token.mint(vault, amount, sender=deploy3r)
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        vault,
        stock_token,
        sender=teller.address,
    )
    donated_user = ledger.userDepositPoints(bob, vault_id, stock_token)
    donated_asset = ledger.assetDepositPoints(vault_id, stock_token)
    assert donated_user.balancePoints == expected_user_weight * 10
    assert donated_user.lastBalance == expected_user_weight
    assert donated_asset.lastBalance == expected_user_weight
    assert donated_asset.lastUsdValue == (100 if vault_kind == "simple" else 200)

    boa.env.time_travel(blocks=10)
    stock_token.adminBurn(vault, 2 * amount, sender=deploy3r)
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        vault,
        stock_token,
        sender=teller.address,
    )
    lost_user = ledger.userDepositPoints(bob, vault_id, stock_token)
    lost_asset = ledger.assetDepositPoints(vault_id, stock_token)
    assert lost_user.balancePoints == expected_user_weight * 20
    assert lost_user.lastBalance == expected_user_weight
    assert lost_asset.lastBalance == expected_user_weight
    assert lost_asset.lastUsdValue == (100 if vault_kind == "simple" else 0)


@pytest.mark.parametrize("first_buyer_name", ("alice", "sally"))
def test_simple_internal_auction_two_buyer_order_freezes_after_loss(
    first_buyer_name,
    stock_token,
    simple_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    green_token,
    whale,
    deploy3r,
    bob,
    alice,
    sally,
):
    """A-05: neither buyer can acquire a claim after Simple loses backing."""

    vault = simple_erc20_vault
    vault_id = 3
    _configure_stock_asset(
        stock_token,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    stock_token.mint(bob, deposit_amount, sender=deploy3r)
    stock_token.approve(teller, deposit_amount, sender=bob)
    teller.deposit(stock_token, deposit_amount, bob, vault, sender=bob)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS // 2)
    teller.liquidateUser(bob, False, sender=deploy3r)
    assert ledger.hasFungibleAuction(bob, vault_id, stock_token)
    stock_token.adminBurn(vault, 100 * EIGHTEEN_DECIMALS, sender=deploy3r)

    payment = 40 * EIGHTEEN_DECIMALS
    first = alice if first_buyer_name == "alice" else sally
    second = sally if first_buyer_name == "alice" else alice
    for buyer in (first, second):
        green_token.transfer(buyer, payment, sender=whale)
        green_token.approve(teller, payment, sender=buyer)
        with boa.reverts("no green spent"):
            teller.buyFungibleAuction(
                bob,
                vault_id,
                stock_token,
                payment,
                False,
                True,
                False,
                sender=buyer,
            )
        assert green_token.balanceOf(buyer) == payment
        assert vault.getTotalAmountForUser(buyer, stock_token) == 0
        assert stock_token.balanceOf(buyer) == 0

    assert credit_engine.getUserDebtAmount(bob) == 100 * EIGHTEEN_DECIMALS
    assert stock_token.balanceOf(vault) == 100 * EIGHTEEN_DECIMALS
    assert ledger.hasFungibleAuction(bob, vault_id, stock_token)
