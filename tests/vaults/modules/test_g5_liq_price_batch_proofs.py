"""Group 5 — liquidation matrix, price freeze, two valuations, batch skip.

Never-skips #4 (liquidation compose) and #5 (price / skip / freeze).
"""
import boa

from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from conf_utils import (
    clear_transient_storage,
    claim_from_stability_pool,
    redeem_from_stability_pool,
)


def _seed_stab(stability_pool, asset, whale, user, teller, mock_price_source, amount):
    mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)
    asset.transfer(stability_pool, amount, sender=whale)
    assert stability_pool.depositTokensInVault(user, asset, amount, sender=teller.address) == amount


def _record_claim(stability_pool, stab_asset, claim_asset, claim_whale, claim_amount,
                  recipient, auction_house, green_token, savings_green, stab_amount=1):
    claim_asset.transfer(stability_pool, claim_amount, sender=claim_whale)
    return stability_pool.swapForLiquidatedCollateral(
        stab_asset, stab_amount, claim_asset, claim_amount,
        recipient, green_token, savings_green, sender=auction_house.address,
    )


def _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig):
    setGeneralConfig()
    stab_id = vault_book.getRegId(stability_pool)
    setAssetConfig(alpha_token, _vaultIds=[stab_id])
    return stab_id


def test_g5_flagged_unhealthy_claim_reverts(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig, setGeneralDebtConfig,
    createDebtTerms, performDeposit, ledger, charlie_token, charlie_token_whale,
    simple_erc20_vault,
):
    """Claim of a still-unhealthy flagged user reverts at higher-risk housekeeping."""
    with boa.env.anchor():
        stab_id = _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        setAssetConfig(
            charlie_token,
            _debtTerms=createDebtTerms(50_00, 60_00, 70_00, 10_00, 0, 0),
            _shouldSwapInStabPools=False,
            _shouldAuctionInstantly=True,
        )
        setGeneralDebtConfig()
        _seed_stab(
            stability_pool, alpha_token, alpha_token_whale, bob, teller,
            mock_price_source, 100 * EIGHTEEN_DECIMALS,
        )
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool, alpha_token, bravo_token, bravo_token_whale,
            10 * EIGHTEEN_DECIMALS, bob, auction_house, green_token, savings_green,
        )
        clear_transient_storage()
        mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
        performDeposit(bob, 100 * 10**6, charlie_token, charlie_token_whale)
        clear_transient_storage()
        boa.env.time_travel(blocks=1)
        assert teller.borrow(10 * EIGHTEEN_DECIMALS, bob, False, False, sender=bob) == 10 * EIGHTEEN_DECIMALS
        clear_transient_storage()

        mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS // 100)
        teller.liquidateUser(bob, False, sender=sally)
        clear_transient_storage()
        assert ledger.userDebt(bob).inLiquidation
        assert ledger.userDebt(bob).amount > 0
        boa.env.time_travel(blocks=1)

        with boa.reverts("bad debt health"):
            claim_from_stability_pool(teller, stab_id, alpha_token, bravo_token, sender=bob)


def test_g5_flagged_now_healthy_claim_clears_flag(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig, setGeneralDebtConfig,
    createDebtTerms, performDeposit, ledger, charlie_token, charlie_token_whale,
):
    """Flagged, then price restored so collateral is healthy: claim commits and clears the flag."""
    with boa.env.anchor():
        stab_id = _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        setAssetConfig(
            charlie_token,
            _debtTerms=createDebtTerms(50_00, 60_00, 70_00, 10_00, 0, 0),
            _shouldSwapInStabPools=False,
            _shouldAuctionInstantly=True,
        )
        setGeneralDebtConfig()
        _seed_stab(
            stability_pool, alpha_token, alpha_token_whale, bob, teller,
            mock_price_source, 100 * EIGHTEEN_DECIMALS,
        )
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool, alpha_token, bravo_token, bravo_token_whale,
            10 * EIGHTEEN_DECIMALS, bob, auction_house, green_token, savings_green,
        )
        clear_transient_storage()
        mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
        performDeposit(bob, 100 * 10**6, charlie_token, charlie_token_whale)
        clear_transient_storage()
        boa.env.time_travel(blocks=1)
        assert teller.borrow(10 * EIGHTEEN_DECIMALS, bob, False, False, sender=bob) == 10 * EIGHTEEN_DECIMALS
        clear_transient_storage()

        mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS // 100)
        teller.liquidateUser(bob, False, sender=sally)
        clear_transient_storage()
        assert ledger.userDebt(bob).inLiquidation
        mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
        boa.env.time_travel(blocks=1)

        before = bravo_token.balanceOf(bob)
        claim_from_stability_pool(teller, stab_id, alpha_token, bravo_token, sender=bob)
        clear_transient_storage()
        assert bravo_token.balanceOf(bob) > before
        assert not ledger.userDebt(bob).inLiquidation


def test_g5_debt_zero_flagged_stab_withdraw_quotes_max_flag_sticks(
    stability_pool, alpha_token, alpha_token_whale, bob, teller,
    vault_book, setGeneralConfig, setAssetConfig, mock_price_source,
    ledger, credit_engine, createDebtTerms,
):
    """Debt-zero + inLiquidation: quote is max_value; withdraw commits;
    HK does not write a cleared flag."""
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        _seed_stab(
            stability_pool, alpha_token, alpha_token_whale, bob, teller,
            mock_price_source, 100 * EIGHTEEN_DECIMALS,
        )
        clear_transient_storage()
        debt_terms = createDebtTerms()
        ledger.setUserDebt(bob, (0, 0, debt_terms, 0, True), 0, (0, 0), sender=credit_engine.address)
        assert ledger.userDebt(bob).inLiquidation
        assert ledger.userDebt(bob).amount == 0

        stab_id = vault_book.getRegId(stability_pool)
        quoted = credit_engine.getMaxWithdrawableForAsset(bob, stab_id, alpha_token, stability_pool)
        assert quoted == MAX_UINT256

        withdrawn = teller.withdraw(alpha_token, EIGHTEEN_DECIMALS, bob, stability_pool, 0, sender=bob)
        clear_transient_storage()
        assert withdrawn == EIGHTEEN_DECIMALS
        assert ledger.userDebt(bob).inLiquidation


def test_g5_unhealthy_unflagged_ltv0_stab_withdraw_reverts_at_hk(
    stability_pool, savings_green, bravo_token, bravo_token_whale, bob, teller,
    auction_house, mock_price_source, green_token, whale, vault_book,
    mission_control, switchboard_alpha, switchboard_bravo, setGeneralConfig,
    setAssetConfig, createDebtTerms, setGeneralDebtConfig, performDeposit,
    charlie_token, charlie_token_whale, ledger,
):
    """Unhealthy-but-not-flagged: sGREEN ltv=0 quotes max_value; post-withdraw
    higher-risk HK still reverts on bad overall debt health."""
    with boa.env.anchor():
        setGeneralConfig()
        stab_id = vault_book.getRegId(stability_pool)
        mission_control.setPriorityStabVaults([(stab_id, savings_green)], sender=switchboard_alpha.address)
        setAssetConfig(savings_green, _vaultIds=[stab_id], _debtTerms=createDebtTerms(0, 0, 0, 0, 0, 0))
        setAssetConfig(
            charlie_token,
            _debtTerms=createDebtTerms(50_00, 60_00, 70_00, 10_00, 0, 0),
        )
        setGeneralDebtConfig()

        green_amt = 100 * EIGHTEEN_DECIMALS
        green_token.transfer(bob, green_amt, sender=whale)
        green_token.approve(savings_green.address, green_amt, sender=bob)
        sgreen = savings_green.deposit(green_amt, bob, sender=bob)
        savings_green.approve(teller.address, sgreen, sender=bob)
        teller.deposit(savings_green, sgreen, bob, stability_pool, sender=bob)
        clear_transient_storage()

        mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
        performDeposit(bob, 100 * 10**6, charlie_token, charlie_token_whale)
        clear_transient_storage()
        boa.env.time_travel(blocks=1)
        assert teller.borrow(10 * EIGHTEEN_DECIMALS, bob, False, False, sender=bob) == 10 * EIGHTEEN_DECIMALS
        clear_transient_storage()

        mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS // 100)
        assert not ledger.userDebt(bob).inLiquidation
        with boa.reverts("bad debt health"):
            teller.withdraw(savings_green, EIGHTEEN_DECIMALS, bob, stability_pool, 0, sender=bob)


def test_g5_unpriceable_active_freezes_nav_paths(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig, whale,
):
    """One unpriceable active claimable fail-closes depositor NAV paths.
    Liquidation-available fail-softs to 0. Prune cannot remove it while
    fail-soft USD is 0. Liveness, not theft, unless someone extracts during freeze.
    """
    with boa.env.anchor():
        stab_id = _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        _seed_stab(
            stability_pool, alpha_token, alpha_token_whale, bob, teller,
            mock_price_source, 100 * EIGHTEEN_DECIMALS,
        )
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool, alpha_token, bravo_token, bravo_token_whale,
            10 * EIGHTEEN_DECIMALS, bob, auction_house, green_token, savings_green,
        )
        clear_transient_storage()
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 1

        mock_price_source.disablePriceFeed(bravo_token)

        # strict NAV fail-closes (configured source, no price)
        with boa.reverts():
            stability_pool.getTotalValue(alpha_token)
        alpha_token.transfer(bob, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
        alpha_token.approve(teller.address, EIGHTEEN_DECIMALS, sender=bob)
        with boa.reverts():
            teller.deposit(alpha_token, EIGHTEEN_DECIMALS, bob, stability_pool, sender=bob)
        with boa.reverts():
            teller.withdraw(alpha_token, EIGHTEEN_DECIMALS, bob, stability_pool, 0, sender=bob)
        with boa.reverts():
            claim_from_stability_pool(teller, stab_id, alpha_token, bravo_token, sender=bob)

        # fail-soft liquidation mirror: same pile, amount 0 (two valuations disagree)
        asset, amount = stability_pool.getUserAssetAndAmountAtIndex(bob, 1)
        assert asset == alpha_token.address
        assert amount == 0

        # prune does not remove while fail-soft USD is 0
        stability_pool.pruneClaimableAssets(alpha_token, [bravo_token.address])
        assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == 2  # still active

        # redeem sizing: configured-failed + shouldRaise → full batch revert
        pay = EIGHTEEN_DECIMALS
        green_token.transfer(bob, pay, sender=whale)
        green_token.approve(teller.address, pay, sender=bob)
        with boa.reverts():
            redeem_from_stability_pool(teller, stab_id, bravo_token, pay, bob, sender=bob)


def test_g5_claim_soft_skip_then_auth_revert_rolls_nothing(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig, governance,
):
    """Row 1 soft-skips on a disabled claim asset; row 2 is enabled and
    unauthorized — hard auth revert. No state from the batch remains."""
    with boa.env.anchor():
        stab_id = _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        echo = boa.load(
            "contracts/mock/MockErc20.vy", governance, "EchoC", "ECHC", 18, 1_000_000,
            name="echo_g5_claim",
        )
        echo_whale = boa.env.generate_address("echo_g5_claim_whale")
        echo.mint(echo_whale, 1000 * EIGHTEEN_DECIMALS, sender=governance.address)
        setAssetConfig(bravo_token, _canClaimInStabPool=False)
        setAssetConfig(echo, _canClaimInStabPool=True)
        _seed_stab(
            stability_pool, alpha_token, alpha_token_whale, bob, teller,
            mock_price_source, 100 * EIGHTEEN_DECIMALS,
        )
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(echo, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool, alpha_token, bravo_token, bravo_token_whale,
            10 * EIGHTEEN_DECIMALS, bob, auction_house, green_token, savings_green,
        )
        _record_claim(
            stability_pool, alpha_token, echo, echo_whale,
            10 * EIGHTEEN_DECIMALS, bob, auction_house, green_token, savings_green,
        )
        clear_transient_storage()
        shares = stability_pool.userBalances(bob, alpha_token)
        pair_b = stability_pool.claimableBalances(alpha_token, bravo_token)
        pair_e = stability_pool.claimableBalances(alpha_token, echo)
        with boa.reverts("cannot claim for user"):
            teller.claimManyFromStabilityPool(
                stab_id,
                [
                    (alpha_token, bravo_token, MAX_UINT256),
                    (alpha_token, echo, MAX_UINT256),
                ],
                bob,
                False,
                sender=sally,
            )
        assert stability_pool.userBalances(bob, alpha_token) == shares
        assert stability_pool.claimableBalances(alpha_token, bravo_token) == pair_b
        assert stability_pool.claimableBalances(alpha_token, echo) == pair_e


def test_g5_all_skip_redeem_reverts(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, whale, setGeneralConfig, setAssetConfig,
):
    with boa.env.anchor():
        stab_id = _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token, _canRedeemInStabPool=False)
        _seed_stab(
            stability_pool, alpha_token, alpha_token_whale, bob, teller,
            mock_price_source, 100 * EIGHTEEN_DECIMALS,
        )
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool, alpha_token, bravo_token, bravo_token_whale,
            10 * EIGHTEEN_DECIMALS, bob, auction_house, green_token, savings_green,
        )
        clear_transient_storage()
        pay = EIGHTEEN_DECIMALS
        green_token.transfer(bob, pay, sender=whale)
        green_token.approve(teller.address, pay, sender=bob)
        with boa.reverts("no redemptions occurred"):
            redeem_from_stability_pool(teller, stab_id, bravo_token, pay, bob, sender=bob)


def test_g5_redeem_20_active_new_green_reverts_clean(
    stability_pool, alpha_token, alpha_token_whale, bob, teller, auction_house,
    mock_price_source, green_token, savings_green, vault_book, whale,
    setGeneralConfig, setAssetConfig, governance,
):
    """A cohort already at MAX_ACTIVE_CLAIM_ASSETS=20 cannot add replacement
    GREEN as a new pair. Redeem must revert with no custody / share change.
    Liveness at the ceiling, not theft."""
    with boa.env.anchor():
        stab_id = _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        _seed_stab(
            stability_pool, alpha_token, alpha_token_whale, bob, teller,
            mock_price_source, 200 * EIGHTEEN_DECIMALS,
        )
        tokens = []
        for i in range(20):
            t = boa.load(
                "contracts/mock/MockErc20.vy", governance, f"A{i}", f"A{i}", 18, 1_000_000,
                name=f"g5_act_{i}",
            )
            w = boa.env.generate_address(f"g5_act_whale_{i}")
            t.mint(w, 1000 * EIGHTEEN_DECIMALS, sender=governance.address)
            mock_price_source.setPrice(t, EIGHTEEN_DECIMALS)
            setAssetConfig(t)
            _record_claim(
                stability_pool, alpha_token, t, w, EIGHTEEN_DECIMALS,
                bob, auction_house, green_token, savings_green,
            )
            tokens.append(t)
        clear_transient_storage()
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 20

        # Partial redeem so the pair stays active (still 20). Replacement GREEN
        # is a new pair and must not become a 21st active entry.
        setAssetConfig(green_token)
        mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
        pay = 10**16  # $0.01, well above wrap dust, well below $1 pile
        green_token.transfer(bob, pay, sender=whale)
        green_token.approve(teller.address, pay, sender=bob)
        pair_before = stability_pool.claimableBalances(alpha_token, tokens[0])
        shares_before = stability_pool.userBalances(bob, alpha_token)
        bob_green = green_token.balanceOf(bob)
        with boa.reverts():
            redeem_from_stability_pool(teller, stab_id, tokens[0], pay, bob, sender=bob)
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 20
        assert stability_pool.claimableBalances(alpha_token, tokens[0]) == pair_before
        assert stability_pool.userBalances(bob, alpha_token) == shares_before
        assert green_token.balanceOf(bob) == bob_green
        assert green_token.balanceOf(teller.address) == 0
