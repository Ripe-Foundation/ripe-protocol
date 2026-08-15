"""
SC-09 -- skip unavailable Stability Pool cohorts in optional broad Deleverage.

Broad/default Deleverage must fail-soft when a Stability Pool cohort is
unavailable (an unpriceable / source-failed claim asset makes the strict NAV
valuation revert). It skips that cohort and continues through healthy ordinary
collateral, without mutating any Stability Pool claim/reward/share/custody state.

Strict paths (direct claims/withdrawals) stay fail-closed.
"""

import pytest
import boa
from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def claim_token(governance):
    # a plain 18-decimal token used only as a liquidated claim asset in a
    # Stability Pool cohort (never a vault/collateral asset)
    return boa.load(
        "contracts/mock/MockErc20.vy", governance, "Claim Token", "CLAIM", 18, 1_000_000_000,
        name="sc09_claim_token",
    )


@pytest.fixture(scope="module")
def claim_token_whale(env, claim_token, governance):
    whale = env.generate_address("sc09_claim_whale")
    claim_token.mint(whale, 100_000_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    return whale


@pytest.fixture(scope="module")
def green_lp_token(governance):
    return boa.load(
        "contracts/mock/MockErc20.vy", governance, "Green LP Token", "GLP", 18, 1_000_000_000,
        name="sc09_green_lp_token",
    )


@pytest.fixture(scope="module")
def green_lp_token_whale(env, green_lp_token, governance):
    whale = env.generate_address("sc09_green_lp_whale")
    green_lp_token.mint(whale, 100_000_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    return whale


@pytest.fixture(scope="module")
def processing_failure_token(governance):
    return boa.load(
        "contracts/mock/MockReentrantRepayToken.vy",
        governance,
        name="sc09_processing_failure_token",
    )


@pytest.fixture(scope="module")
def processing_failure_token_whale(env, processing_failure_token, governance):
    whale = env.generate_address("sc09_processing_failure_token_whale")
    processing_failure_token.mint(
        whale,
        100_000_000 * EIGHTEEN_DECIMALS,
        sender=governance.address,
    )
    return whale


def _debt(credit_engine, user):
    return credit_engine.getLatestUserDebtAndTerms(user, False)[0].amount


def _seed_custody_deficit(
    stability_pool, auction_house, stab_asset, claim_token, claim_token_whale,
    mock_price_source, green_token, savings_green, governance,
    claim_amount=100 * EIGHTEEN_DECIMALS,
):
    """
    Register a claim asset (priced) then BURN half the pool's real custody of it,
    leaving totalClaimableBalances above balanceOf -- an aggregate claim-custody
    deficit. The strict NAV path reverts "claim custody deficit"; the fail-soft
    availability view reports the cohort unavailable (zero).
    """
    mock_price_source.setPrice(claim_token, 1 * EIGHTEEN_DECIMALS)
    claim_token.transfer(stability_pool, claim_amount, sender=claim_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        stab_asset, 1, claim_token, claim_amount, governance,
        green_token, savings_green, sender=auction_house.address,
    )
    claim_token.burn(claim_amount // 2, sender=stability_pool.address)
    assert claim_token.balanceOf(stability_pool) < stability_pool.totalClaimableBalances(claim_token)


def _stab_snapshot(stability_pool, stab_asset, claim_token, user, ledger, vault_id):
    """Stored cohort, custody, claim, and reward state for no-mutation checks."""
    return {
        "user_shares": stability_pool.userBalances(user, stab_asset),
        "total_shares": stability_pool.totalBalances(stab_asset),
        "pair_claim": stability_pool.claimableBalances(stab_asset, claim_token),
        "aggregate_liability": stability_pool.totalClaimableBalances(claim_token),
        "num_claim_assets": stability_pool.numClaimableAssets(stab_asset),
        "num_active_claims": stability_pool.getNumActiveClaimAssets(stab_asset),
        "claim_index": stability_pool.indexOfClaimableAsset(stab_asset, claim_token),
        "stab_custody": stab_asset.balanceOf(stability_pool.address),
        "claim_custody": claim_token.balanceOf(stability_pool.address),
        "user_loot_share": stability_pool.getUserLootBoxShare(user, stab_asset),
        "user_deposit_points": ledger.userDepositPoints(user, vault_id, stab_asset),
        "asset_deposit_points": ledger.assetDepositPoints(vault_id, stab_asset),
        "global_deposit_points": ledger.globalDepositPoints(),
    }


def _seed_broken_claim(
    stability_pool,
    auction_house,
    stab_asset,
    claim_token,
    claim_token_whale,
    mock_price_source,
    green_token,
    savings_green,
    governance,
    claim_amount=100 * EIGHTEEN_DECIMALS,
):
    """
    Register `claim_token` as an active claimable asset in `stab_asset`'s cohort,
    then make its price source fail. After this, strict NAV valuation of the
    cohort reverts while the fail-soft view reports it unavailable.
    """
    mock_price_source.setPrice(claim_token, 1 * EIGHTEEN_DECIMALS)
    # pool must physically custody the claim tokens before they are registered
    claim_token.transfer(stability_pool, claim_amount, sender=claim_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        stab_asset,          # stab asset cohort
        1,                   # tiny stab-asset amount moved out (1 wei)
        claim_token,         # liquidated claim asset
        claim_amount,        # reported received
        governance,          # recipient of the 1 wei stab asset
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    # now break the claim asset's price source
    mock_price_source.setShouldRevert(claim_token, True)


@pytest.fixture
def sc09_setup(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    alpha_token,
    alpha_token_whale,
    savings_green,
    green_token,
    stability_pool,
    mock_price_source,
    performDeposit,
    teller,
    setup_priority_configs,
    bob,
):
    """
    bob: alpha_token healthy ordinary collateral (endaoment-transfer) + an sGREEN
    Stability Pool position + GREEN debt. Priority stab vaults front-load the
    sGREEN cohort so broad Deleverage meets it first.
    """
    def sc09_setup(
        alpha_deposit=1_000 * EIGHTEEN_DECIMALS,
        borrow_amount=300 * EIGHTEEN_DECIMALS,
        priority_stab=True,
        priority_liq_stab=False,
        extra_stab_assets=None,
    ):
        setGeneralConfig()
        setGeneralDebtConfig(_ltvPaybackBuffer=0)

        # healthy ordinary collateral, deleveragable via endaoment transfer
        alpha_terms = createDebtTerms(
            _ltv=50_00,
            _redemptionThreshold=60_00,
            _liqThreshold=70_00,
            _liqFee=0,
            _borrowRate=0,
        )
        setAssetConfig(
            alpha_token,
            _debtTerms=alpha_terms,
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=True,
        )
        mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

        # sGREEN stability asset
        stab_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
        setAssetConfig(
            savings_green,
            _vaultIds=[1],
            _debtTerms=stab_terms,
            _shouldBurnAsPayment=True,
        )

        # deposit healthy collateral and borrow sGREEN
        performDeposit(bob, alpha_deposit, alpha_token, alpha_token_whale)
        teller.borrow(borrow_amount, bob, True, sender=bob)  # get sGREEN

        sgreen_balance = savings_green.balanceOf(bob)
        assert sgreen_balance > 0
        performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

        stab_assets = [(stability_pool, savings_green)]
        if extra_stab_assets:
            stab_assets = extra_stab_assets

        if priority_stab:
            setup_priority_configs(priority_stab_assets=stab_assets, priority_liq_assets=[])
        elif priority_liq_stab:
            setup_priority_configs(priority_stab_assets=[], priority_liq_assets=stab_assets)
        else:
            setup_priority_configs(priority_stab_assets=[], priority_liq_assets=[])

        return {"sgreen_balance": sgreen_balance}

    return sc09_setup


def _deleverage(teller, user, switchboard_alpha):
    return teller.deleverageManyUsers([(user, 0)], sender=switchboard_alpha.address)


# ---------------------------------------------------------------------------
# Phase 1 -- unavailable cohort is skipped, healthy collateral is processed
# ---------------------------------------------------------------------------


def test_sc09_phase1_skips_unavailable_cohort_processes_healthy(
    sc09_setup,
    teller,
    credit_engine,
    ledger,
    vault_book,
    stability_pool,
    savings_green,
    alpha_token,
    claim_token,
    claim_token_whale,
    mock_price_source,
    green_token,
    endaoment_funds,
    auction_house,
    governance,
    bob,
    switchboard_alpha,
):
    borrow_amount = 300 * EIGHTEEN_DECIMALS
    sc09_setup(borrow_amount=borrow_amount)
    _seed_broken_claim(
        stability_pool, auction_house, savings_green, claim_token, claim_token_whale,
        mock_price_source, green_token, savings_green, governance,
    )

    pre_debt = _debt(credit_engine, bob)
    assert pre_debt == borrow_amount
    stab_vault_id = vault_book.getRegId(stability_pool)
    before = _stab_snapshot(
        stability_pool, savings_green, claim_token, bob, ledger, stab_vault_id,
    )
    pre_endao_alpha = alpha_token.balanceOf(endaoment_funds)

    # broad deleverage: cohort is unavailable -> skip it, full-payoff via alpha
    repaid = _deleverage(teller, bob, switchboard_alpha)

    # EXACT settlement: full debt cleared via healthy alpha (price 1, buffer 0)
    assert repaid == borrow_amount
    assert _debt(credit_engine, bob) == 0
    assert alpha_token.balanceOf(endaoment_funds) - pre_endao_alpha == borrow_amount

    # DeleverageUser event fields (teller is the tx entry point that owns the logs)
    logs = filter_logs(teller, "DeleverageUser")
    assert len(logs) == 1
    log = logs[0]
    assert log.user == bob
    assert log.caller == switchboard_alpha.address
    assert log.targetRepayAmount == borrow_amount
    assert log.targetRepayAmountWithBuffer == borrow_amount
    assert log.collateralValueRepaid == borrow_amount
    assert log.debtToClear == borrow_amount
    assert log.hasGoodDebtHealth is True

    # NO Stability Pool claim/reward/share/custody/enumeration state changed
    assert _stab_snapshot(
        stability_pool, savings_green, claim_token, bob, ledger, stab_vault_id,
    ) == before
    # nothing was burned or claimed from the pool
    assert len(filter_logs(teller, "StabAssetBurntDuringDeleverage")) == 0
    assert len(filter_logs(teller, "EndaomentTransferDuringDeleverage")) == 1  # alpha only


def test_sc09_recovered_price_lets_cohort_participate(
    sc09_setup,
    teller,
    credit_engine,
    stability_pool,
    savings_green,
    claim_token,
    claim_token_whale,
    mock_price_source,
    green_token,
    auction_house,
    governance,
    bob,
    switchboard_alpha,
):
    sc09_setup()
    _seed_broken_claim(
        stability_pool, auction_house, savings_green, claim_token, claim_token_whale,
        mock_price_source, green_token, savings_green, governance,
    )

    # recover the claim-asset price source
    mock_price_source.setShouldRevert(claim_token, False)

    pre_sgreen_shares = stability_pool.userBalances(bob, savings_green)
    assert pre_sgreen_shares > 0

    # cohort is available again -> broad deleverage burns the sGREEN cohort
    repaid = _deleverage(teller, bob, switchboard_alpha)
    assert repaid > 0
    burns = filter_logs(teller, "StabAssetBurntDuringDeleverage")
    assert len(burns) > 0
    assert stability_pool.userBalances(bob, savings_green) < pre_sgreen_shares


# ---------------------------------------------------------------------------
# Custody/accounting deficit: broad Deleverage skips (matches liquidation),
# but strict/direct paths stay fail-closed. (SC-09 availability-class boundary.)
# ---------------------------------------------------------------------------


def test_sc09_custody_deficit_skips_broad_but_strict_reverts(
    sc09_setup,
    teller,
    credit_engine,
    ledger,
    vault_book,
    stability_pool,
    savings_green,
    alpha_token,
    claim_token,
    claim_token_whale,
    mock_price_source,
    green_token,
    endaoment_funds,
    auction_house,
    governance,
    bob,
    switchboard_alpha,
):
    """
    A claim-CUSTODY deficit (not a price outage) makes the strict NAV path revert
    "claim custody deficit" while the fail-soft availability view reports zero --
    exactly as the deployed liquidation path treats it. Per the agreed semantics,
    broad Deleverage skips the cohort (identical to AuctionHouse liquidation) and
    proceeds through healthy collateral WITHOUT mutating any pool state, while
    every strict/direct Stability Pool path remains fail-closed.
    """
    borrow_amount = 300 * EIGHTEEN_DECIMALS
    sc09_setup(borrow_amount=borrow_amount)
    _seed_custody_deficit(
        stability_pool, auction_house, savings_green, claim_token, claim_token_whale,
        mock_price_source, green_token, savings_green, governance,
    )

    # strict NAV is fail-closed on the custody deficit ...
    with boa.reverts("claim custody deficit"):
        stability_pool.getTotalValue(savings_green)
    # ... while the fail-soft availability view reports the cohort unavailable
    found = False
    for i in range(1, stability_pool.getNumUserAssets(bob) + 1):
        asset, amount = stability_pool.getUserAssetAndAmountAtIndex(bob, i)
        if asset == savings_green.address:
            assert amount == 0
            found = True
    assert found

    stab_vault_id = vault_book.getRegId(stability_pool)
    before = _stab_snapshot(
        stability_pool, savings_green, claim_token, bob, ledger, stab_vault_id,
    )
    pre_endao_alpha = alpha_token.balanceOf(endaoment_funds)

    # broad Deleverage skips the custody-deficient cohort, settles via alpha
    repaid = _deleverage(teller, bob, switchboard_alpha)
    assert repaid == borrow_amount
    assert _debt(credit_engine, bob) == 0
    assert alpha_token.balanceOf(endaoment_funds) - pre_endao_alpha == borrow_amount

    # the deficient cohort's state is completely untouched
    assert _stab_snapshot(
        stability_pool, savings_green, claim_token, bob, ledger, stab_vault_id,
    ) == before

    # strict/direct processing stays fail-closed on the same deficit
    with boa.reverts("claim custody deficit"):
        teller.withdraw(savings_green, 10 * EIGHTEEN_DECIMALS, bob, stability_pool, sender=bob)


@pytest.mark.parametrize("unavailable", ["price", "pause", "custody"])
def test_sc09_withdrawal_preflight_skips_unavailable_stab_cohort(
    unavailable,
    sc09_setup,
    deleverage,
    teller,
    credit_engine,
    ledger,
    vault_book,
    simple_erc20_vault,
    stability_pool,
    savings_green,
    alpha_token,
    claim_token,
    claim_token_whale,
    mock_price_source,
    green_token,
    endaoment_funds,
    auction_house,
    governance,
    bob,
    switchboard_alpha,
):
    """Views and withdrawal assist use the same fail-soft cohort probe."""
    borrow_amount = 300 * EIGHTEEN_DECIMALS
    withdraw_amount = 100 * EIGHTEEN_DECIMALS
    sc09_setup(borrow_amount=borrow_amount)
    mock_price_source.setPrice(savings_green, 1 * EIGHTEEN_DECIMALS)

    if unavailable == "price":
        _seed_broken_claim(
            stability_pool, auction_house, savings_green, claim_token,
            claim_token_whale, mock_price_source, green_token, savings_green,
            governance,
        )
    elif unavailable == "custody":
        _seed_custody_deficit(
            stability_pool, auction_house, savings_green, claim_token,
            claim_token_whale, mock_price_source, green_token, savings_green,
            governance,
        )
    else:
        stability_pool.pause(True, sender=switchboard_alpha.address)

    stab_vault_id = vault_book.getRegId(stability_pool)
    simple_vault_id = vault_book.getRegId(simple_erc20_vault)
    before_stab = _stab_snapshot(
        stability_pool, savings_green, claim_token, bob, ledger, stab_vault_id,
    )
    before_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    before_endao = alpha_token.balanceOf(endaoment_funds)

    # Unavailable sGREEN contributes neither repayment liquidity nor weighted
    # LTV. Healthy ordinary collateral remains visible and strictly valued.
    assert deleverage.getDeleverageInfo(bob) == (before_alpha, 50_00)

    # The same unavailable condition is never softened for a direct withdrawal.
    with boa.reverts():
        teller.withdraw(
            savings_green,
            10 * EIGHTEEN_DECIMALS,
            bob,
            stability_pool,
            sender=bob,
        )
    assert _stab_snapshot(
        stability_pool, savings_green, claim_token, bob, ledger, stab_vault_id,
    ) == before_stab

    # Withdrawal assistance skips the cohort and uses healthy alpha. With a
    # 50% LTV, debt=300, capacity=500, and a $100 projected withdrawal, the
    # required repayment is floor(300 * 50 / (500 - 300 * 50%)).
    expected_repayment = (
        borrow_amount * (withdraw_amount * 50_00 // 100_00)
        // (before_alpha * 50_00 // 100_00 - borrow_amount * 50_00 // 100_00)
    )
    assert deleverage.deleverageForWithdrawal(
        bob,
        simple_vault_id,
        alpha_token,
        withdraw_amount,
        sender=teller.address,
    ) is True
    assert _debt(credit_engine, bob) == borrow_amount - expected_repayment
    assert before_alpha - simple_erc20_vault.getTotalAmountForUser(
        bob, alpha_token,
    ) == expected_repayment
    assert alpha_token.balanceOf(endaoment_funds) - before_endao == expected_repayment
    assert _stab_snapshot(
        stability_pool, savings_green, claim_token, bob, ledger, stab_vault_id,
    ) == before_stab

    # Restore only the failed availability condition. The fail-soft probe and
    # public sizing view immediately include the cohort again.
    if unavailable == "price":
        mock_price_source.setShouldRevert(claim_token, False)
    elif unavailable == "custody":
        deficit = (
            stability_pool.totalClaimableBalances(claim_token)
            - claim_token.balanceOf(stability_pool)
        )
        claim_token.mint(stability_pool, deficit, sender=governance.address)
    else:
        stability_pool.pause(False, sender=switchboard_alpha.address)

    remaining_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    available_stab = stability_pool.getUserAssetAndAmountAtIndex(bob, 1)[1]
    assert available_stab > 0
    expected_max = remaining_alpha + available_stab
    expected_ltv = remaining_alpha * 50_00 // expected_max
    assert deleverage.getDeleverageInfo(bob) == (expected_max, expected_ltv)


def test_sc09_withdrawal_preflight_unavailable_only_makes_no_progress(
    sc09_setup,
    setAssetConfig,
    createDebtTerms,
    deleverage,
    teller,
    credit_engine,
    ledger,
    vault_book,
    simple_erc20_vault,
    stability_pool,
    savings_green,
    alpha_token,
    claim_token,
    claim_token_whale,
    mock_price_source,
    green_token,
    endaoment_funds,
    auction_house,
    governance,
    bob,
):
    """An unavailable-only repayment set returns false without mutation."""
    sc09_setup()
    mock_price_source.setPrice(savings_green, 1 * EIGHTEEN_DECIMALS)
    alpha_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=0,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token,
        _debtTerms=alpha_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
    )
    _seed_broken_claim(
        stability_pool, auction_house, savings_green, claim_token,
        claim_token_whale, mock_price_source, green_token, savings_green,
        governance,
    )

    stab_vault_id = vault_book.getRegId(stability_pool)
    simple_vault_id = vault_book.getRegId(simple_erc20_vault)
    before_stab = _stab_snapshot(
        stability_pool, savings_green, claim_token, bob, ledger, stab_vault_id,
    )
    before_debt = _debt(credit_engine, bob)
    before_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    before_endao = alpha_token.balanceOf(endaoment_funds)

    assert deleverage.getDeleverageInfo(bob) == (0, 0)
    assert deleverage.deleverageForWithdrawal(
        bob,
        simple_vault_id,
        alpha_token,
        100 * EIGHTEEN_DECIMALS,
        sender=teller.address,
    ) is False
    assert _debt(credit_engine, bob) == before_debt
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == before_alpha
    assert alpha_token.balanceOf(endaoment_funds) == before_endao
    assert _stab_snapshot(
        stability_pool, savings_green, claim_token, bob, ledger, stab_vault_id,
    ) == before_stab


# ---------------------------------------------------------------------------
# Processing-time failures: a healthy probe is not converted into a skip
# ---------------------------------------------------------------------------


def test_sc09_processing_failure_after_healthy_probe_reverts_atomically(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    alpha_token,
    alpha_token_whale,
    processing_failure_token,
    processing_failure_token_whale,
    stability_pool,
    mock_price_source,
    performDeposit,
    teller,
    credit_engine,
    setup_priority_configs,
    ledger,
    vault_book,
    claim_token,
    green_token,
    endaoment_funds,
    bob,
    switchboard_alpha,
):
    """
    The cohort passes the fail-soft availability probe. Its outbound transfer
    then reenters a guarded Deleverage route and reverts after pool shares have
    started changing. Broad Deleverage must propagate that failure and roll back
    every pool, reward, custody, debt, token, and event mutation.
    """
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)

    # Alpha supplies borrow capacity but is not itself deleveragable.
    alpha_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=0,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token,
        _debtTerms=alpha_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
    )
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    stab_vault_id = vault_book.getRegId(stability_pool)
    stab_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(
        processing_failure_token,
        _vaultIds=[stab_vault_id],
        _debtTerms=stab_terms,
        _shouldTransferToEndaoment=True,
    )
    mock_price_source.setPrice(processing_failure_token, 1 * EIGHTEEN_DECIMALS)

    borrow_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, 1_000 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(borrow_amount, bob, False, sender=bob)
    performDeposit(
        bob,
        300 * EIGHTEEN_DECIMALS,
        processing_failure_token,
        processing_failure_token_whale,
        stability_pool,
    )
    setup_priority_configs(
        priority_stab_assets=[(stability_pool, processing_failure_token)],
        priority_liq_assets=[],
    )

    # Prove this is not a probe-time skip: the cohort is available and nonzero.
    found_available = False
    for i in range(1, stability_pool.getNumUserAssets(bob) + 1):
        asset, amount = stability_pool.getUserAssetAndAmountAtIndex(bob, i)
        if asset == processing_failure_token.address:
            assert amount > 0
            found_available = True
    assert found_available

    before = _stab_snapshot(
        stability_pool,
        processing_failure_token,
        claim_token,
        bob,
        ledger,
        stab_vault_id,
    )
    pre_debt = _debt(credit_engine, bob)
    pre_green_supply = green_token.totalSupply()
    pre_endao = processing_failure_token.balanceOf(endaoment_funds)

    # The Stability Pool reduces shares before transferring. The callback makes
    # that transfer fail, so the outer broad operation must revert atomically.
    processing_failure_token.configureReenterDeleverage(
        teller.address,
        bob,
        sender=processing_failure_token.hq(),
    )
    with boa.reverts():
        _deleverage(teller, bob, switchboard_alpha)

    assert _stab_snapshot(
        stability_pool,
        processing_failure_token,
        claim_token,
        bob,
        ledger,
        stab_vault_id,
    ) == before
    assert _debt(credit_engine, bob) == pre_debt
    assert green_token.totalSupply() == pre_green_supply
    assert processing_failure_token.balanceOf(endaoment_funds) == pre_endao
    assert len(filter_logs(teller, "DeleverageUser")) == 0
    assert len(filter_logs(teller, "EndaomentTransferDuringDeleverage")) == 0

    # Disarming the transfer callback makes the identical processing path work,
    # isolating the post-probe transfer failure as the reason for the revert.
    processing_failure_token.disableAttack(sender=processing_failure_token.hq())
    repaid = _deleverage(teller, bob, switchboard_alpha)
    assert repaid == borrow_amount
    assert _debt(credit_engine, bob) == 0
    assert processing_failure_token.balanceOf(endaoment_funds) - pre_endao == borrow_amount


# ---------------------------------------------------------------------------
# Phase 2 -- executable exclusion prevents the strict revert re-opening
# ---------------------------------------------------------------------------


def test_sc09_phase2_excludes_stab_vault(
    sc09_setup,
    teller,
    credit_engine,
    stability_pool,
    savings_green,
    alpha_token,
    claim_token,
    claim_token_whale,
    mock_price_source,
    green_token,
    endaoment_funds,
    auction_house,
    governance,
    bob,
    switchboard_alpha,
):
    # deliberately (mis)configure the stab vault into the priority LIQ set
    sc09_setup(priority_stab=False, priority_liq_stab=True)
    _seed_broken_claim(
        stability_pool, auction_house, savings_green, claim_token, claim_token_whale,
        mock_price_source, green_token, savings_green, governance,
    )

    pre_debt = _debt(credit_engine, bob)
    pre_claim = stability_pool.claimableBalances(savings_green, claim_token)
    pre_endao_alpha = alpha_token.balanceOf(endaoment_funds)

    # Phase 2 must exclude the stab vault (else strict NAV reverts); phase 3
    # then meets it and fail-softly skips. Healthy alpha still processed.
    repaid = _deleverage(teller, bob, switchboard_alpha)
    assert repaid > 0
    assert alpha_token.balanceOf(endaoment_funds) > pre_endao_alpha
    assert _debt(credit_engine, bob) < pre_debt
    assert stability_pool.claimableBalances(savings_green, claim_token) == pre_claim


# ---------------------------------------------------------------------------
# Multiple cohorts: one unavailable, one healthy
# ---------------------------------------------------------------------------


def test_sc09_multi_cohort_one_unavailable_one_healthy(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    alpha_token,
    alpha_token_whale,
    savings_green,
    green_token,
    stability_pool,
    mock_price_source,
    performDeposit,
    teller,
    credit_engine,
    setup_priority_configs,
    green_lp_token,
    green_lp_token_whale,
    claim_token,
    claim_token_whale,
    endaoment_funds,
    auction_house,
    governance,
    bob,
    switchboard_alpha,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    stab_terms = createDebtTerms(0, 0, 0, 0, 0, 0)

    # sGREEN cohort (will be broken) + green_lp cohort (healthy, endaoment route)
    setAssetConfig(savings_green, _vaultIds=[1], _debtTerms=stab_terms, _shouldBurnAsPayment=True)
    setAssetConfig(green_lp_token, _vaultIds=[1], _debtTerms=stab_terms, _shouldTransferToEndaoment=True)
    mock_price_source.setPrice(green_lp_token, 1 * EIGHTEEN_DECIMALS)

    # bob: sGREEN position + green_lp position + debt
    # fund bob with green_lp and deposit into stab pool
    green_lp_token.transfer(bob, 200 * EIGHTEEN_DECIMALS, sender=green_lp_token_whale)
    green_lp_token.approve(teller, 200 * EIGHTEEN_DECIMALS, sender=bob)
    teller.deposit(green_lp_token, 200 * EIGHTEEN_DECIMALS, bob, stability_pool, 0, sender=bob)

    # alpha for borrow capacity (not deleveragable so cohorts are the only source)
    alpha_terms = createDebtTerms(_ltv=50_00, _redemptionThreshold=60_00, _liqThreshold=70_00, _liqFee=0, _borrowRate=0)
    setAssetConfig(alpha_token, _debtTerms=alpha_terms, _shouldBurnAsPayment=False, _shouldTransferToEndaoment=False)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    performDeposit(bob, 1_000 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)

    teller.borrow(200 * EIGHTEEN_DECIMALS, bob, True, sender=bob)
    sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

    setup_priority_configs(
        priority_stab_assets=[(stability_pool, savings_green), (stability_pool, green_lp_token)],
        priority_liq_assets=[],
    )

    # break only the sGREEN cohort
    _seed_broken_claim(
        stability_pool, auction_house, savings_green, claim_token, claim_token_whale,
        mock_price_source, green_token, savings_green, governance,
    )

    pre_debt = _debt(credit_engine, bob)
    pre_glp = stability_pool.userBalances(bob, green_lp_token)
    pre_sgreen = stability_pool.userBalances(bob, savings_green)
    pre_endao_glp = green_lp_token.balanceOf(endaoment_funds)

    repaid = _deleverage(teller, bob, switchboard_alpha)
    assert repaid > 0

    # healthy green_lp cohort was processed (moved to endaoment), debt reduced
    assert green_lp_token.balanceOf(endaoment_funds) > pre_endao_glp
    assert stability_pool.userBalances(bob, green_lp_token) < pre_glp
    assert _debt(credit_engine, bob) < pre_debt
    # broken sGREEN cohort untouched
    assert stability_pool.userBalances(bob, savings_green) == pre_sgreen


# ---------------------------------------------------------------------------
# Stability-pool-only collateral, no healthy fallback
# ---------------------------------------------------------------------------


def test_sc09_stab_only_no_fallback_no_progress(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    alpha_token,
    alpha_token_whale,
    savings_green,
    green_token,
    stability_pool,
    mock_price_source,
    performDeposit,
    teller,
    credit_engine,
    setup_priority_configs,
    claim_token,
    claim_token_whale,
    auction_house,
    governance,
    bob,
    switchboard_alpha,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)

    # alpha only provides borrow capacity, NOT deleveragable (no burn/endaoment)
    alpha_terms = createDebtTerms(_ltv=50_00, _redemptionThreshold=60_00, _liqThreshold=70_00, _liqFee=0, _borrowRate=0)
    setAssetConfig(alpha_token, _debtTerms=alpha_terms, _shouldBurnAsPayment=False, _shouldTransferToEndaoment=False)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    stab_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(savings_green, _vaultIds=[1], _debtTerms=stab_terms, _shouldBurnAsPayment=True)

    performDeposit(bob, 1_000 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(200 * EIGHTEEN_DECIMALS, bob, True, sender=bob)
    sgreen_balance = savings_green.balanceOf(bob)
    performDeposit(bob, sgreen_balance, savings_green, bob, stability_pool)

    setup_priority_configs(priority_stab_assets=[(stability_pool, savings_green)], priority_liq_assets=[])
    _seed_broken_claim(
        stability_pool, auction_house, savings_green, claim_token, claim_token_whale,
        mock_price_source, green_token, savings_green, governance,
    )

    pre_debt = _debt(credit_engine, bob)
    # only (unavailable) stab collateral is deleveragable -> nothing processed
    with boa.reverts("nobody deleveraged"):
        _deleverage(teller, bob, switchboard_alpha)
    assert _debt(credit_engine, bob) == pre_debt


# ---------------------------------------------------------------------------
# Errors OUTSIDE the stab cohort must NOT be suppressed
# ---------------------------------------------------------------------------


def test_sc09_ordinary_asset_price_failure_still_reverts(
    sc09_setup,
    teller,
    credit_engine,
    alpha_token,
    mock_price_source,
    bob,
    switchboard_alpha,
):
    # no broken claim; instead break the HEALTHY ordinary collateral's price
    sc09_setup(priority_stab=False)
    mock_price_source.setShouldRevert(alpha_token, True)

    # the ordinary (non-stab) price failure must propagate, not be skipped
    with boa.reverts():
        _deleverage(teller, bob, switchboard_alpha)


# ---------------------------------------------------------------------------
# Strict direct Stability Pool paths stay fail-closed
# ---------------------------------------------------------------------------


def test_sc09_direct_withdraw_still_reverts_strictly(
    sc09_setup,
    teller,
    stability_pool,
    savings_green,
    claim_token,
    claim_token_whale,
    mock_price_source,
    green_token,
    auction_house,
    governance,
    bob,
):
    sc09_setup(priority_stab=False)
    _seed_broken_claim(
        stability_pool, auction_house, savings_green, claim_token, claim_token_whale,
        mock_price_source, green_token, savings_green, governance,
    )

    # direct user withdrawal from the stab pool must fail closed on the
    # unpriceable claim asset (strict NAV valuation)
    with boa.reverts():
        teller.withdraw(savings_green, 10 * EIGHTEEN_DECIMALS, bob, stability_pool, sender=bob)


def test_sc09_strict_nav_reverts_but_failsoft_reports_zero(
    sc09_setup,
    stability_pool,
    savings_green,
    claim_token,
    claim_token_whale,
    mock_price_source,
    green_token,
    auction_house,
    governance,
    bob,
):
    """
    Root-cause pinpoint: the strict cohort valuation reverts while the fail-soft
    availability view (used by the SC-09 skip) reports the cohort unavailable.
    """
    sc09_setup(priority_stab=False)
    _seed_broken_claim(
        stability_pool, auction_house, savings_green, claim_token, claim_token_whale,
        mock_price_source, green_token, savings_green, governance,
    )

    # strict path reverts
    with boa.reverts():
        stability_pool.getTotalAmountForUser(bob, savings_green)

    # fail-soft availability view reports 0 for the sGREEN asset index
    found_zero = False
    num_assets = stability_pool.getNumUserAssets(bob)
    for i in range(1, num_assets + 1):
        asset, amount = stability_pool.getUserAssetAndAmountAtIndex(bob, i)
        if asset == savings_green.address:
            assert amount == 0
            found_zero = True
    assert found_zero
