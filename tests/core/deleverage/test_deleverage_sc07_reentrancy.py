"""
SC-07 -- stale debt overwrite during reentrant Deleverage execution.

A callback-capable admitted collateral token reenters a debt-mutating Teller
route (repay / borrow) while Deleverage is moving collateral. The inner mutation
changes the borrower's debt; the outer Deleverage settlement must NOT settle
against the stale pre-interaction UserDebt snapshot.

Invariant: immediately before settlement Deleverage re-reads the live debt and
    - reverts with "debt changed" if the amount moved during the interaction phase,
    - otherwise settles using the REFRESHED full struct + interest (never the stale
      snapshot), so a same-amount nested mutation cannot double-count interest.

A shared @nonreentrant guard on the external debt-writing routes additionally
blocks cross-entry reentrancy between guarded Deleverage routes (defense in depth).
"""

import pytest
import boa
from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs

HUNDRED_PERCENT = 100_00
ONE_YEAR = 60 * 60 * 24 * 365


@pytest.fixture(scope="module")
def reenter_token(governance):
    return boa.load(
        "contracts/mock/MockReentrantRepayToken.vy",
        governance,
        name="reenter_token",
    )


@pytest.fixture(scope="module")
def reenter_token_whale(env, reenter_token, governance):
    whale = env.generate_address("reenter_token_whale")
    reenter_token.mint(whale, 100_000_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    return whale


@pytest.fixture
def sc07_setup(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    setUserConfig,
    reenter_token,
    reenter_token_whale,
    bravo_token,
    bravo_token_whale,
    mock_price_source,
    performDeposit,
    teller,
    green_token,
    whale,
    bob,
    simple_erc20_vault,
    rebase_erc20_vault,
    vault_book,
):
    """
    Borrower `bob` holds two endaoment-transfer collateral positions and borrows
    GREEN. `reenter_token` (callback-capable) is armed to reenter Teller for bob
    during its collateral transfer.

    `bravo_vault="rebase"` places the second position in a DIFFERENT vault so the
    exploit genuinely spans two vaults (distinct didHandleVaultId keys); the
    default keeps both in the simple vault as two distinct assets.
    """
    def sc07_setup(
        reenter_deposit=400 * EIGHTEEN_DECIMALS,
        bravo_deposit=400 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        repay_amount=200 * EIGHTEEN_DECIMALS,
        reenter_endaoment=True,
        bravo_vault="simple",
        borrow_rate=0,
        get_green=True,
    ):
        setGeneralConfig()
        setGeneralDebtConfig(_ltvPaybackBuffer=0)

        debt_terms = createDebtTerms(
            _ltv=50_00,
            _redemptionThreshold=60_00,
            _liqThreshold=70_00,
            _liqFee=0,
            _borrowRate=borrow_rate,
        )
        simple_id = vault_book.getRegId(simple_erc20_vault)
        rebase_id = vault_book.getRegId(rebase_erc20_vault)
        bravo_vault_obj = rebase_erc20_vault if bravo_vault == "rebase" else simple_erc20_vault
        bravo_vault_id = rebase_id if bravo_vault == "rebase" else simple_id

        setAssetConfig(
            reenter_token,
            _vaultIds=[simple_id],
            _debtTerms=debt_terms,
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=reenter_endaoment,
        )
        setAssetConfig(
            bravo_token,
            _vaultIds=[simple_id, rebase_id],
            _debtTerms=debt_terms,
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=True,
        )
        mock_price_source.setPrice(reenter_token, 1 * EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)

        setUserConfig(bob, _canAnyoneRepayDebt=True)

        performDeposit(bob, reenter_deposit, reenter_token, reenter_token_whale, simple_erc20_vault)
        performDeposit(bob, bravo_deposit, bravo_token, bravo_token_whale, bravo_vault_obj)

        teller.borrow(borrow_amount, bob, not get_green, sender=bob)

        # fund the callback token with GREEN + approve Teller to pull it
        fund = borrow_amount * 3
        green_token.transfer(reenter_token, fund, sender=whale)
        green_token.approve(teller.address, fund, sender=reenter_token.address)

        # default arming: repay `repay_amount` during the callback
        reenter_token.configureAttack(teller.address, bob, repay_amount, sender=reenter_token.hq())

        return {
            "simple_id": simple_id,
            "rebase_id": rebase_id,
            "bravo_vault_id": bravo_vault_id,
            "borrow_amount": borrow_amount,
            "repay_amount": repay_amount,
        }

    return sc07_setup


# --- helpers ----------------------------------------------------------------


def _stored_debt(ledger, user):
    """Authoritative stored UserDebt (not the interest-accrued view)."""
    return ledger.userDebt(user)


def _assert_debt_struct_unchanged(ledger, user, before):
    after = ledger.userDebt(user)
    assert after.amount == before.amount, "amount changed"
    assert after.principal == before.principal, "principal changed"
    assert after.lastTimestamp == before.lastTimestamp, "lastTimestamp changed"
    assert after.inLiquidation == before.inLiquidation, "liquidation state changed"
    assert after.debtTerms.ltv == before.debtTerms.ltv, "ltv changed"
    assert (
        after.debtTerms.redemptionThreshold == before.debtTerms.redemptionThreshold
    ), "redemptionThreshold changed"
    assert after.debtTerms.liqThreshold == before.debtTerms.liqThreshold, "liqThreshold changed"
    assert after.debtTerms.liqFee == before.debtTerms.liqFee, "liqFee changed"
    assert after.debtTerms.borrowRate == before.debtTerms.borrowRate, "borrowRate changed"
    assert after.debtTerms.daowry == before.debtTerms.daowry, "daowry changed"


def _vault_position_snapshot(vault, user, asset):
    """Both sides of a collateral position, including raw shares and custody."""
    return {
        "user_balance": vault.userBalances(user, asset),
        "total_balance": vault.totalBalances(asset),
        "user_amount": vault.getTotalAmountForUser(user, asset),
        "custody": asset.balanceOf(vault.address),
    }


# ---------------------------------------------------------------------------
# deleverageWithSpecificAssets settlement site
# ---------------------------------------------------------------------------


def test_sc07_specific_assets_reverts_on_reentrant_repay(
    sc07_setup, teller, ledger, credit_engine, green_token, reenter_token,
    simple_erc20_vault, endaoment_funds, bob, switchboard_alpha,
):
    """Partial reentrant repay -> revert "debt changed" + total atomic rollback."""
    ctx = sc07_setup(borrow_rate=10_00)
    simple_id = ctx["simple_id"]

    # Make the rollback proof non-vacuous for interest accounting.
    boa.env.time_travel(seconds=ONE_YEAR)

    before = _stored_debt(ledger, bob)
    assert credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount > before.amount
    pre_green_supply = green_token.totalSupply()
    pre_endao = reenter_token.balanceOf(endaoment_funds)
    pre_token_green = green_token.balanceOf(reenter_token)
    pre_yield = ledger.unrealizedYield()
    pre_position = _vault_position_snapshot(simple_erc20_vault, bob, reenter_token)

    assets = [(simple_id, reenter_token.address, 100 * EIGHTEEN_DECIMALS)]
    with boa.reverts("debt changed"):
        teller.deleverageWithSpecificAssets(assets, bob, sender=switchboard_alpha.address)

    # full struct rolled back
    _assert_debt_struct_unchanged(ledger, bob, before)
    # no GREEN burned (inner repay rolled back), no interest booked
    assert green_token.totalSupply() == pre_green_supply
    assert green_token.balanceOf(reenter_token) == pre_token_green
    assert ledger.unrealizedYield() == pre_yield
    # no collateral withdrawal or transfer survived on either side
    assert _vault_position_snapshot(simple_erc20_vault, bob, reenter_token) == pre_position
    assert reenter_token.balanceOf(endaoment_funds) == pre_endao
    # no events survived
    assert len(filter_logs(teller, "DeleverageUser")) == 0
    assert len(filter_logs(teller, "RepayDebt")) == 0


# ---------------------------------------------------------------------------
# broad _deleverageUser settlement site (deleverageManyUsers)
# ---------------------------------------------------------------------------


def test_sc07_broad_deleverage_reverts_on_reentrant_repay(
    sc07_setup, teller, ledger, green_token, reenter_token, bravo_token,
    simple_erc20_vault, rebase_erc20_vault, endaoment_funds, bob,
    switchboard_alpha,
):
    """
    Broad Deleverage across TWO positions in different vaults: the callback fires
    while processing the first (insufficient) position; both planned positions are
    in the interaction phase before settlement, which must refresh + revert with
    full rollback of both.
    """
    ctx = sc07_setup(
        reenter_deposit=200 * EIGHTEEN_DECIMALS,
        bravo_deposit=600 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        repay_amount=150 * EIGHTEEN_DECIMALS,
        bravo_vault="rebase",
    )

    before = _stored_debt(ledger, bob)
    pre_green_supply = green_token.totalSupply()
    pre_endao_reenter = reenter_token.balanceOf(endaoment_funds)
    pre_endao_bravo = bravo_token.balanceOf(endaoment_funds)
    pre_yield = ledger.unrealizedYield()
    pre_reenter_position = _vault_position_snapshot(simple_erc20_vault, bob, reenter_token)
    pre_bravo_position = _vault_position_snapshot(rebase_erc20_vault, bob, bravo_token)

    with boa.reverts("debt changed"):
        teller.deleverageManyUsers([(bob, 0)], sender=switchboard_alpha.address)

    _assert_debt_struct_unchanged(ledger, bob, before)
    assert green_token.totalSupply() == pre_green_supply
    assert ledger.unrealizedYield() == pre_yield
    # NEITHER position's collateral moved
    assert _vault_position_snapshot(simple_erc20_vault, bob, reenter_token) == pre_reenter_position
    assert _vault_position_snapshot(rebase_erc20_vault, bob, bravo_token) == pre_bravo_position
    assert reenter_token.balanceOf(endaoment_funds) == pre_endao_reenter
    assert bravo_token.balanceOf(endaoment_funds) == pre_endao_bravo
    assert len(filter_logs(teller, "DeleverageUser")) == 0
    assert len(filter_logs(teller, "RepayDebt")) == 0


# ---------------------------------------------------------------------------
# deleverageWithVolAssets settlement site
# ---------------------------------------------------------------------------


def test_sc07_vol_assets_reverts_on_reentrant_repay(
    sc07_setup, deleverage, teller, ledger, green_token, reenter_token,
    simple_erc20_vault, endaoment_funds, bob, switchboard_alpha,
):
    """Volatile-asset settlement site: refresh + revert + full rollback."""
    ctx = sc07_setup(reenter_endaoment=False)
    simple_id = ctx["simple_id"]

    before = _stored_debt(ledger, bob)
    pre_green_supply = green_token.totalSupply()
    pre_endao = reenter_token.balanceOf(endaoment_funds)
    pre_yield = ledger.unrealizedYield()
    pre_position = _vault_position_snapshot(simple_erc20_vault, bob, reenter_token)

    assets = [(simple_id, reenter_token.address, 100 * EIGHTEEN_DECIMALS)]
    with boa.reverts("debt changed"):
        deleverage.deleverageWithVolAssets(bob, assets, sender=switchboard_alpha.address)

    _assert_debt_struct_unchanged(ledger, bob, before)
    assert green_token.totalSupply() == pre_green_supply
    assert ledger.unrealizedYield() == pre_yield
    assert _vault_position_snapshot(simple_erc20_vault, bob, reenter_token) == pre_position
    assert reenter_token.balanceOf(endaoment_funds) == pre_endao
    assert len(filter_logs(deleverage, "DeleverageUserWithVolatileAssets")) == 0
    assert len(filter_logs(deleverage, "RepayDebt")) == 0


# ---------------------------------------------------------------------------
# reentrant debt-INCREASING route (borrow)
# ---------------------------------------------------------------------------


def test_sc07_reentrant_borrow_change_reverts(
    sc07_setup, setUserDelegation, teller, ledger, green_token, reenter_token,
    simple_erc20_vault, endaoment_funds, bob, switchboard_alpha,
):
    """Nested Teller.borrow (increase) also trips the guard; full rollback."""
    ctx = sc07_setup()
    simple_id = ctx["simple_id"]

    setUserDelegation(bob, reenter_token.address, _canBorrow=True)
    reenter_token.configureBorrow(teller.address, bob, 50 * EIGHTEEN_DECIMALS, sender=reenter_token.hq())

    before = _stored_debt(ledger, bob)
    pre_green_supply = green_token.totalSupply()
    pre_endao = reenter_token.balanceOf(endaoment_funds)
    pre_position = _vault_position_snapshot(simple_erc20_vault, bob, reenter_token)

    assets = [(simple_id, reenter_token.address, 100 * EIGHTEEN_DECIMALS)]
    with boa.reverts("debt changed"):
        teller.deleverageWithSpecificAssets(assets, bob, sender=switchboard_alpha.address)

    _assert_debt_struct_unchanged(ledger, bob, before)
    assert green_token.totalSupply() == pre_green_supply
    assert _vault_position_snapshot(simple_erc20_vault, bob, reenter_token) == pre_position
    assert reenter_token.balanceOf(endaoment_funds) == pre_endao
    assert len(filter_logs(teller, "DeleverageUser")) == 0


# ---------------------------------------------------------------------------
# full repayment during the callback
# ---------------------------------------------------------------------------


def test_sc07_full_repay_during_callback_reverts(
    sc07_setup, teller, ledger, green_token, reenter_token, simple_erc20_vault,
    endaoment_funds, bob, switchboard_alpha,
):
    """Callback fully repays the debt (amount -> 0); guard must catch it."""
    ctx = sc07_setup(repay_amount=300 * EIGHTEEN_DECIMALS)  # == borrow_amount
    simple_id = ctx["simple_id"]

    before = _stored_debt(ledger, bob)
    assert before.amount == 300 * EIGHTEEN_DECIMALS
    pre_green_supply = green_token.totalSupply()
    pre_endao = reenter_token.balanceOf(endaoment_funds)
    pre_position = _vault_position_snapshot(simple_erc20_vault, bob, reenter_token)

    assets = [(simple_id, reenter_token.address, 100 * EIGHTEEN_DECIMALS)]
    with boa.reverts("debt changed"):
        teller.deleverageWithSpecificAssets(assets, bob, sender=switchboard_alpha.address)

    _assert_debt_struct_unchanged(ledger, bob, before)
    assert green_token.totalSupply() == pre_green_supply
    assert _vault_position_snapshot(simple_erc20_vault, bob, reenter_token) == pre_position
    assert reenter_token.balanceOf(endaoment_funds) == pre_endao
    assert len(filter_logs(teller, "DeleverageUser")) == 0
    assert len(filter_logs(teller, "RepayDebt")) == 0


# ---------------------------------------------------------------------------
# same-amount nested mutation: guard does NOT falsely revert, and settlement
# uses the REFRESHED struct/interest (no double-counted yield)
# ---------------------------------------------------------------------------


def test_sc07_same_amount_mutation_uses_refreshed_struct_and_interest(
    sc07_setup, setUserDelegation, teller, ledger, credit_engine, reenter_token,
    bob, switchboard_alpha,
):
    """
    The callback repays X then borrows X back (X > accrued interest): the debt
    AMOUNT is restored, so the guard must NOT revert. The nested repay/borrow
    "principalizes" the accrued interest -- after it, the LIVE debt is all
    principal (principal == amount). If the outer settlement then clears a small
    amount (<= the accrued interest) using the REFRESHED struct, it reduces
    principal, leaving principal ABOVE the original borrow principal. The stale
    snapshot (principal == original, non-principal == accrued interest) would
    instead treat the small clear as pure interest and leave principal unchanged.
    Exact post-settlement principal/debt prove the refreshed struct was used;
    zero remaining unrealized yield proves stale pre-callback interest was not
    handed to the outer settlement and booked a second time.
    """
    borrow_rate = 10_00  # 10% / yr
    borrow_amount = 300 * EIGHTEEN_DECIMALS
    ctx = sc07_setup(borrow_rate=borrow_rate, borrow_amount=borrow_amount, repay_amount=0)
    simple_id = ctx["simple_id"]

    setUserDelegation(bob, reenter_token.address, _canBorrow=True)

    # accrue interest for one year
    boa.env.time_travel(seconds=ONE_YEAR)
    stored = ledger.userDebt(bob)
    assert stored.principal == borrow_amount
    accrued = credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount - stored.amount
    assert accrued > 0

    # repay-then-borrow X, with X well above the accrued interest
    x = 100 * EIGHTEEN_DECIMALS
    assert x > accrued
    reenter_token.configureRepayThenBorrow(teller.address, bob, x, sender=reenter_token.hq())

    # outer settlement clears only a small amount, strictly below accrued interest
    small_target = accrued // 2
    assert small_target > 0
    assets = [(simple_id, reenter_token.address, small_target)]

    # amount is restored -> guard passes, deleverage settles
    repaid = teller.deleverageWithSpecificAssets(assets, bob, sender=switchboard_alpha.address)
    assert repaid == small_target

    after = ledger.userDebt(bob)
    # refreshed struct => interest was principalized, then partially cleared:
    # principal ends ABOVE the original borrow principal. Stale struct would leave
    # it at exactly `borrow_amount`.
    expected_remaining = stored.amount + accrued - small_target
    assert after.principal == expected_remaining
    assert after.amount == expected_remaining
    # The nested borrow realizes and flushes the accrued yield. Passing the stale
    # outer newInterest would incorrectly add that same yield back to the Ledger.
    assert ledger.unrealizedYield() == 0


# ---------------------------------------------------------------------------
# cross-entry reentrancy between guarded Deleverage routes (defense in depth)
# ---------------------------------------------------------------------------


def test_sc07_cross_entry_deleverage_reentrancy_blocked(
    sc07_setup, teller, ledger, green_token, reenter_token, endaoment_funds,
    simple_erc20_vault, bob, switchboard_alpha,
):
    """
    While deleverageWithSpecificAssets runs, a callback that reenters the guarded
    deleverageManyUsers route must be rejected by the shared @nonreentrant lock
    (Vyper emits a bare revert), reverting the whole tx before any debt mutation.
    A baseline run with the callback disarmed settles normally, isolating the lock
    as the cause of the reverting run.
    """
    ctx = sc07_setup()
    simple_id = ctx["simple_id"]
    assets = [(simple_id, reenter_token.address, 100 * EIGHTEEN_DECIMALS)]

    # armed: reenter deleverageManyUsers during the collateral transfer
    reenter_token.configureReenterDeleverage(teller.address, bob, sender=reenter_token.hq())
    before = _stored_debt(ledger, bob)
    pre_green_supply = green_token.totalSupply()
    pre_endao = reenter_token.balanceOf(endaoment_funds)
    pre_position = _vault_position_snapshot(simple_erc20_vault, bob, reenter_token)

    with boa.reverts():  # shared nonreentrant lock -> bare revert
        teller.deleverageWithSpecificAssets(assets, bob, sender=switchboard_alpha.address)

    # rejected before any state change (lock fires before the debt-refresh guard)
    _assert_debt_struct_unchanged(ledger, bob, before)
    assert green_token.totalSupply() == pre_green_supply
    assert _vault_position_snapshot(simple_erc20_vault, bob, reenter_token) == pre_position
    assert reenter_token.balanceOf(endaoment_funds) == pre_endao
    assert len(filter_logs(teller, "DeleverageUser")) == 0

    # baseline: same setup, callback disarmed -> the outer route settles normally,
    # proving the revert above is caused by the reentry, not the scenario itself.
    reenter_token.disableAttack(sender=reenter_token.hq())
    repaid = teller.deleverageWithSpecificAssets(assets, bob, sender=switchboard_alpha.address)
    assert repaid > 0
    assert _stored_debt(ledger, bob).amount < before.amount
