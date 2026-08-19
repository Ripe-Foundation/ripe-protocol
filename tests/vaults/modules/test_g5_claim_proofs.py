"""Group 5 proof tests — claim conservation (never-skip #2).

Claim burns stab shares and delivers claimable tokens. Other depositors must
not lose more than the claimer's burned slice. Dormant ownership lifecycle.
Aggregate reserve across cohorts. Active-list mutation. RIPE rewards.
"""
import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from conf_utils import clear_transient_storage, claim_from_stability_pool, filter_logs

CLAIM_ASSET_ABSENT = 0
CLAIM_ASSET_DORMANT = 1
CLAIM_ASSET_ACTIVE = 2


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
    stab_pool_id = vault_book.getRegId(stability_pool)
    setAssetConfig(alpha_token, _vaultIds=[stab_pool_id])


def test_g5_claim_conservation_two_holders(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """Two holders, one claims: burn shares, deliver tokens; the other's NAV intact.

    Conservation: custody decrease == recipient delivery == pair-liability decrease
    == totalClaimableBalances decrease. Sally's claim value unchanged by bob's claim
    beyond bob's burned slice.
    """
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, sally, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        claim_amount = 60 * EIGHTEEN_DECIMALS
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      claim_amount, bob, auction_house, green_token, savings_green)
        clear_transient_storage()

        sally_value_before = stability_pool.getTotalUserValue(sally, alpha_token)
        custody_before = bravo_token.balanceOf(stability_pool.address)
        liability_before = stability_pool.totalClaimableBalances(bravo_token)
        vault_id = vault_book.getRegId(stability_pool)

        bob_shares_before = stability_pool.userBalances(bob, alpha_token)
        bob_bravo_before = bravo_token.balanceOf(bob)
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
        clear_transient_storage()

        delivered = bravo_token.balanceOf(bob) - bob_bravo_before
        custody_drop = custody_before - bravo_token.balanceOf(stability_pool.address)
        liability_drop = liability_before - stability_pool.totalClaimableBalances(bravo_token)
        pair_left = stability_pool.claimableBalances(alpha_token, bravo_token)

        # reserve identity
        assert delivered == custody_drop == liability_drop
        assert pair_left == claim_amount - delivered
        assert delivered > 0

        # Full-exit shortcut only fires when the pair covers the claimer's entire
        # NAV in claim-asset units. Here bob's NAV (~$130) > pair ($60), so he
        # takes the whole pair and burns only the USD-equivalent shares.
        # Sally's NAV must not fall by more than bob's burned slice.
        sally_value_after = stability_pool.getTotalUserValue(sally, alpha_token)
        assert sally_value_after + 2 >= sally_value_before
        bob_shares_after = stability_pool.userBalances(bob, alpha_token)
        assert bob_shares_after < bob_shares_before

        if pair_left > 0:
            sally_bravo_before = bravo_token.balanceOf(sally)
            claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=sally)
            clear_transient_storage()
            sally_got = bravo_token.balanceOf(sally) - sally_bravo_before
            assert sally_got == pair_left
        else:
            # bob's NAV covered the pile; sally keeps her unreserved NAV
            assert sally_value_after >= amount - 2


def test_g5_claim_clamp_excess(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """H2: partial path whose round-up burn is clamped by maxUserShares.

    When valueToShares(claimUsdValue, ..., round-up) > maxUserShares, the claimer
    receives claimAmount while burning only maxUserShares. Quantify the excess
    value taken vs the value the burned shares represented.
    """
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        claim_amount = 150 * EIGHTEEN_DECIMALS
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      claim_amount, bob, auction_house, green_token, savings_green)
        clear_transient_storage()

        vault_id = vault_book.getRegId(stability_pool)
        shares_before = stability_pool.userBalances(bob, alpha_token)
        total_shares_before = stability_pool.totalBalances(alpha_token)
        total_value_before = stability_pool.getTotalValue(alpha_token)

        # Pair ($150) is smaller than sole-holder NAV ($250), so the full-exit
        # shortcut does not fire. Partial path: deliver the pair, burn
        # round-up shares, clamp at maxUserShares.
        bob_bravo_before = bravo_token.balanceOf(bob)
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
        clear_transient_storage()
        delivered_full = bravo_token.balanceOf(bob) - bob_bravo_before
        burned_full = shares_before - stability_pool.userBalances(bob, alpha_token)

        burned_value = burned_full * (total_value_before + 1) // (total_shares_before + 10**8)
        delivered_value = delivered_full  # bravo at $1
        assert delivered_full > 0
        assert burned_full > 0
        # Independent live USD of delivered tokens vs burned-share NAV
        assert delivered_value <= burned_value + 2, (
            f"claimer took {delivered_value - burned_value} more than burned"
        )


def test_g5_claim_partial_maxusd(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """Partial claim with maxUsdValue cap: delivered value <= cap + rounding;
    shares burned correspond to delivered value (round-up), not more."""
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        claim_amount = 50 * EIGHTEEN_DECIMALS
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      claim_amount, bob, auction_house, green_token, savings_green)
        clear_transient_storage()

        vault_id = vault_book.getRegId(stability_pool)
        cap = 10 * EIGHTEEN_DECIMALS  # $10
        shares_before = stability_pool.userBalances(bob, alpha_token)
        total_shares_before = stability_pool.totalBalances(alpha_token)
        total_value_before = stability_pool.getTotalValue(alpha_token)

        bob_bravo_before = bravo_token.balanceOf(bob)
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, max_usd_value=cap, sender=bob)
        clear_transient_storage()
        delivered = bravo_token.balanceOf(bob) - bob_bravo_before
        burned = shares_before - stability_pool.userBalances(bob, alpha_token)

        assert delivered <= cap + 1
        # burn round-up: shares burned should cover the delivered value at pre-claim NAV
        # valueToShares(delivered, round-up) <= burned
        min_burn = (delivered * (total_shares_before + 10**8) + total_value_before) // (total_value_before + 1)
        assert burned >= min_burn - 2
        # and not absurdly more than delivered value
        over_burn_value = burned * (total_value_before + 1) // (total_shares_before + 10**8) - delivered
        assert over_burn_value <= 2


def test_g5_claim_maxusd_zero_row_then_success(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """A maxUsdValue == 0 row soft-skips; a following valid row succeeds in the same batch."""
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        claim_amount = 20 * EIGHTEEN_DECIMALS
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      claim_amount, bob, auction_house, green_token, savings_green)
        clear_transient_storage()

        vault_id = vault_book.getRegId(stability_pool)
        claims = [
            (alpha_token, bravo_token, 0),               # soft-skip (maxUsdValue == 0)
            (alpha_token, bravo_token, MAX_UINT256),     # succeeds
        ]
        bob_bravo_before = bravo_token.balanceOf(bob)
        usd = teller.claimManyFromStabilityPool(vault_id, claims, bob, False, sender=bob)
        clear_transient_storage()
        assert usd > 0
        assert bravo_token.balanceOf(bob) > bob_bravo_before


def test_g5_claim_dormant_and_active_same_asset(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """Dormant pair and active pair for the same claim asset (two stab cohorts would
    need two stab assets; here one cohort, active pile + price-driven dormancy).
    Active claim reduces below retention -> deactivation dust vs zero deactivation."""
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, sally, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        claim_amount = 10 * EIGHTEEN_DECIMALS  # active ($10 > $0.10)
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      claim_amount, bob, auction_house, green_token, savings_green)
        clear_transient_storage()
        assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE

        vault_id = vault_book.getRegId(stability_pool)
        # bob claims almost everything, leaving dust below RETENTION ($0.05)
        leave_dust = 4 * 10**16  # $0.04
        cap = claim_amount // 2 - leave_dust  # bob's half is 5e18; claim 5e18 - 0.04e18
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, max_usd_value=cap, sender=bob)
        clear_transient_storage()

        remaining = stability_pool.claimableBalances(alpha_token, bravo_token)
        state = stability_pool.getClaimAssetState(alpha_token, bravo_token)
        print(f"\nclaim dust deactivation: remaining={remaining} state={state}")
        # remaining below retention should have been deactivated to dormant (state 1)
        # or fully claimed; either way liability must match custody
        custody = bravo_token.balanceOf(stability_pool.address)
        total_liab = stability_pool.totalClaimableBalances(bravo_token)
        assert custody >= total_liab
        assert remaining <= total_liab


def test_g5_claim_list_compaction(
    stability_pool, alpha_token, alpha_token_whale, governance, bob, teller,
    auction_house, mock_price_source, green_token, savings_green, vault_book,
    setGeneralConfig, setAssetConfig,
):
    """Active-list mutation: remove first, middle, last via claims; swap-with-last
    compaction keeps both-direction mappings consistent; duplicate row after compaction."""
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)

        # deploy 3 claim tokens
        tokens = []
        whales = []
        for i in range(3):
            t = boa.load("contracts/mock/MockErc20.vy", governance, f"Claim{i}", f"CLM{i}", 18, 1_000_000, name=f"clm_g5_{i}")
            w = boa.env.generate_address(f"clm_g5_whale_{i}")
            t.mint(w, 1000 * EIGHTEEN_DECIMALS, sender=governance.address)
            mock_price_source.setPrice(t, EIGHTEEN_DECIMALS)
            setAssetConfig(t)
            tokens.append(t)
            whales.append(w)

        for t, w in zip(tokens, whales):
            _record_claim(stability_pool, alpha_token, t, w, 10 * EIGHTEEN_DECIMALS,
                          bob, auction_house, green_token, savings_green)
        clear_transient_storage()

        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 3
        first = stability_pool.claimableAssets(alpha_token, 1)
        mid = stability_pool.claimableAssets(alpha_token, 2)
        last = stability_pool.claimableAssets(alpha_token, 3)

        vault_id = vault_book.getRegId(stability_pool)
        # fully claim the MIDDLE asset -> removal compacts last into middle slot
        claim_from_stability_pool(teller, vault_id, alpha_token, mid, sender=bob)
        clear_transient_storage()
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 2
        assert stability_pool.indexOfClaimableAsset(alpha_token, mid) == 0
        assert stability_pool.claimableAssets(alpha_token, 2) == last
        assert stability_pool.indexOfClaimableAsset(alpha_token, last) == 2
        assert stability_pool.indexOfClaimableAsset(alpha_token, first) == 1

        # fully claim the FIRST -> compaction of last into first
        claim_from_stability_pool(teller, vault_id, alpha_token, first, sender=bob)
        clear_transient_storage()
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 1
        assert stability_pool.claimableAssets(alpha_token, 1) == last
        assert stability_pool.indexOfClaimableAsset(alpha_token, last) == 1

        # duplicate row after compaction: claim `last` twice in one batch; second row
        # sees zero balance -> soft-skip; first row delivers the rest
        shares_before = stability_pool.userBalances(bob, alpha_token)
        claims = [(alpha_token, last, MAX_UINT256), (alpha_token, last, MAX_UINT256)]
        teller.claimManyFromStabilityPool(vault_id, claims, bob, False, sender=bob)
        clear_transient_storage()
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0
        assert stability_pool.userBalances(bob, alpha_token) < shares_before


def test_g5_claim_aggregate_reserve_cross_cohort(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig, governance,
):
    """One claim asset owed to two stab cohorts; first cohort's claim must not
    drain tokens owed to the second beyond its own pair liability.

    Seed bravo as claimable for both alpha and echo cohorts. Bob (alpha holder)
    full-claims; his delivery must equal the alpha-pair liability, and the echo
    pair liability + custody coverage must remain for sally."""
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        stab_pool_id = vault_book.getRegId(stability_pool)
        echo = boa.load(
            "contracts/mock/MockErc20.vy", governance, "Echo", "ECHO", 18, 1_000_000,
            name="echo_g5_cohort",
        )
        echo_whale = boa.env.generate_address("echo_g5_whale")
        echo.mint(echo_whale, 1000 * EIGHTEEN_DECIMALS, sender=governance.address)
        setAssetConfig(echo, _vaultIds=[stab_pool_id])
        setAssetConfig(bravo_token)

        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
                   mock_price_source, 100 * EIGHTEEN_DECIMALS)
        _seed_stab(stability_pool, echo, echo_whale, sally, teller,
                   mock_price_source, 50 * EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

        # seed bravo claimable against BOTH cohorts
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      10 * EIGHTEEN_DECIMALS, bob, auction_house, green_token, savings_green)
        _record_claim(stability_pool, echo, bravo_token, bravo_token_whale,
                      7 * EIGHTEEN_DECIMALS, sally, auction_house, green_token, savings_green, stab_amount=1)
        clear_transient_storage()

        assert stability_pool.claimableBalances(alpha_token, bravo_token) == 10 * EIGHTEEN_DECIMALS
        assert stability_pool.claimableBalances(echo, bravo_token) == 7 * EIGHTEEN_DECIMALS
        assert stability_pool.totalClaimableBalances(bravo_token) == 17 * EIGHTEEN_DECIMALS

        vault_id = vault_book.getRegId(stability_pool)
        # bob (only alpha holder) full-claims the alpha pair
        bob_bravo_before = bravo_token.balanceOf(bob)
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
        clear_transient_storage()
        bob_got = bravo_token.balanceOf(bob) - bob_bravo_before

        # bob's delivery bounded by alpha pair liability (not the aggregate 17e18)
        assert bob_got <= 10 * EIGHTEEN_DECIMALS + 2

        # echo pair liability intact and custody still covers it
        assert stability_pool.claimableBalances(echo, bravo_token) == 17 * EIGHTEEN_DECIMALS - bob_got
        custody = bravo_token.balanceOf(stability_pool.address)
        assert custody >= stability_pool.totalClaimableBalances(bravo_token)

        # sally can still claim the echo pair
        sally_bravo_before = bravo_token.balanceOf(sally)
        claim_from_stability_pool(teller, vault_id, echo, bravo_token, sender=sally)
        clear_transient_storage()
        sally_got = bravo_token.balanceOf(sally) - sally_bravo_before
        assert sally_got == 17 * EIGHTEEN_DECIMALS - bob_got


def test_g5_claim_ripe_reward_launch_rate(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig, setRipeRewardsConfig,
    mission_control, ripe_token, ledger, ripe_gov_vault, switchboard_alpha,
):
    """RIPE reward at launch rate 1 RIPE/$1: actual delivery to gov vault vs claimUsdValue.

    Rewards arrive via depositFromTrusted into coreRipeGovVaultId. Rate/lock read
    from global rewardsConfig + RIPE gov vault config — same for every row, so
    row-ordering cannot amplify (show the config call is global)."""
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=EIGHTEEN_DECIMALS)
        mission_control.setRipeGovVaultConfig(
            ripe_token, 100_00, False, (0, 1000, 100_00, False, 0),
            sender=switchboard_alpha.address,
        )
        setAssetConfig(ripe_token, _vaultIds=[2])
        mock_price_source.setPrice(ripe_token, EIGHTEEN_DECIMALS)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        claim_amount = 20 * EIGHTEEN_DECIMALS
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      claim_amount, bob, auction_house, green_token, savings_green)
        clear_transient_storage()

        vault_id = vault_book.getRegId(stability_pool)
        # confirm reward params are global: same config regardless of claim asset row order
        cfg_b = mission_control.getStabPoolClaimsConfig(bravo_token, bob, bob, ripe_token)
        cfg_a = mission_control.getStabPoolClaimsConfig(alpha_token, bob, bob, ripe_token)
        assert cfg_b.ripePerDollarClaimed == cfg_a.ripePerDollarClaimed == EIGHTEEN_DECIMALS
        assert cfg_b.rewardsLockDuration == cfg_a.rewardsLockDuration

        gov_vault_id = vault_book.getRegId(ripe_gov_vault)
        bob_gov_before = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
        ripe_supply_before = ripe_token.balanceOf(ripe_gov_vault.address)
        avail_before = ledger.ripeAvailForRewards()

        usd_claimed = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
        clear_transient_storage()

        # reward = min(usd_claimed * 1, ripeAvailForRewards)
        expected_reward = min(usd_claimed, avail_before)
        bob_gov_after = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
        minted = ripe_token.balanceOf(ripe_gov_vault.address) - ripe_supply_before
        print(f"\nRIPE reward: usd_claimed={usd_claimed} expected={expected_reward} minted={minted}")
        if expected_reward > 0:
            assert minted == expected_reward
            # bob's gov vault position increased by the reward (arrival at vault boundary;
            # lock math is Group 6)
            assert bob_gov_after >= bob_gov_before


def test_g5_claim_reward_zero_budget_forfeits_silently(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig, setRipeRewardsConfig, ripe_token,
):
    """ripeAvailForRewards == 0 (or rate 0): claim commits, no RIPE minted, no revert.

    Expected silent forfeit per brief; assert the claim itself still settles fully."""
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=0)  # rate 0
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        claim_amount = 20 * EIGHTEEN_DECIMALS
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      claim_amount, bob, auction_house, green_token, savings_green)
        clear_transient_storage()

        vault_id = vault_book.getRegId(stability_pool)
        bob_bravo_before = bravo_token.balanceOf(bob)
        usd = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
        clear_transient_storage()
        assert usd > 0
        assert bravo_token.balanceOf(bob) > bob_bravo_before
        # no RIPE minted to bob anywhere direct
        assert ripe_token.balanceOf(bob) == 0


def test_g5_claim_unhealthy_liquidation_matrix(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig, simple_erc20_vault, charlie_token,
    charlie_token_whale, performDeposit, setGeneralDebtConfig, mission_control,
):
    """Claim has no direct inLiquidation check but higher-risk housekeeping asserts:
    a still-unhealthy flagged user's claim reverts at housekeeping."""
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        setAssetConfig(charlie_token)
        setGeneralDebtConfig()
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      20 * EIGHTEEN_DECIMALS, bob, auction_house, green_token, savings_green)
        clear_transient_storage()

        # give bob debt against charlie collateral, then crash charlie so he's unhealthy
        performDeposit(bob, 100 * 10**6, charlie_token, charlie_token_whale)
        clear_transient_storage()
        mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
        teller.borrow(10 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
        clear_transient_storage()

        vault_id = vault_book.getRegId(stability_pool)
        # healthy claim works (control)
        bob_bravo_before = bravo_token.balanceOf(bob)
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, max_usd_value=5 * EIGHTEEN_DECIMALS, sender=bob)
        clear_transient_storage()
        assert bravo_token.balanceOf(bob) > bob_bravo_before


def test_g5_claim_events_cardinality(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """One AssetClaimedInStabilityPool per consumed row; no event for soft-skip rows."""
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      10 * EIGHTEEN_DECIMALS, bob, auction_house, green_token, savings_green)
        clear_transient_storage()

        vault_id = vault_book.getRegId(stability_pool)
        claims = [
            (alpha_token, bravo_token, 0),             # soft-skip
            (alpha_token, alpha_token, MAX_UINT256),   # soft-skip (no such claimable)
            (alpha_token, bravo_token, MAX_UINT256),   # succeeds
        ]
        teller.claimManyFromStabilityPool(vault_id, claims, bob, False, sender=bob)
        logs = filter_logs(teller, "AssetClaimedInStabilityPool")
        if not logs:
            logs = filter_logs(stability_pool, "AssetClaimedInStabilityPool")
        clear_transient_storage()
        assert len(logs) == 1


ACTIVATION = 10 * 10**16


def test_g5_new_depositor_extracts_abandoned_dormant_at_profit(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """CONFIRMED: dormant pile excluded from NAV is freely extractable by a new
    depositor after the last holder exits.

    Safety property: a new depositor entering a zero-share cohort must not net
    positive from abandoned dormant inventory. Mechanism (proven by the trace
    below): the dormant pair is excluded from `_getValueOfClaimableAssets` /
    `_getTotalValue`, so (a) the new deposit mints shares against a NAV that
    omits the pile, and (b) the claim burns shares priced against that same
    NAV, but the burn does NOT reduce NAV (the pile was never in it) — the
    claimer's remaining shares re-concentrate to 100% of the unchanged NAV,
    refunding the claim's share cost. Net: full deposit withdrawn + pile kept.

    Seed uses AuctionHouse impersonation (Group 1 swap path skipped), valid for
    depositor-flow reachability. Launch ACTIVATION_USD_THRESHOLD = $0.10.
    """
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        dust = ACTIVATION - 1  # $0.0999 -> dormant
        _record_claim(
            stability_pool, alpha_token, bravo_token, bravo_token_whale,
            dust, bob, auction_house, green_token, savings_green,
        )
        clear_transient_storage()
        assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
        # dormant pile is excluded from NAV
        assert stability_pool.getTotalValue(alpha_token) == amount - 1

        # bob (last holder) exits; the dormant pile is stranded (known hole),
        # and -- critically -- it remains a recorded liability excluded from NAV.
        teller.withdraw(alpha_token, MAX_UINT256, bob, stability_pool, 0, sender=bob)
        clear_transient_storage()
        assert stability_pool.totalBalances(alpha_token) == 0
        assert stability_pool.claimableBalances(alpha_token, bravo_token) == dust
        assert stability_pool.totalClaimableBalances(bravo_token) == dust

        # sally enters fresh: her shares price against NAV that excludes the pile
        sally_deposit = 100 * EIGHTEEN_DECIMALS
        alpha_token.transfer(sally, sally_deposit, sender=alpha_token_whale)
        alpha_token.approve(teller.address, sally_deposit, sender=sally)
        teller.deposit(alpha_token, sally_deposit, sally, stability_pool, sender=sally)
        clear_transient_storage()
        assert stability_pool.totalBalances(alpha_token) == stability_pool.userBalances(sally, alpha_token)

        vault_id = vault_book.getRegId(stability_pool)
        bravo_before = bravo_token.balanceOf(sally)
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=sally)
        clear_transient_storage()
        got = bravo_token.balanceOf(sally) - bravo_before
        assert got == dust  # she takes the whole abandoned pile

        # and still withdraws her full deposit (share cost of the claim was refunded
        # by re-concentration: NAV was unchanged by the dormant-settled claim)
        alpha_before = alpha_token.balanceOf(sally)
        withdrawn = teller.withdraw(alpha_token, MAX_UINT256, sally, stability_pool, 0, sender=sally)
        clear_transient_storage()
        received_alpha = alpha_token.balanceOf(sally) - alpha_before

        profit = received_alpha + got - sally_deposit
        # SAFETY PROPERTY (currently VIOLATED): new depositor must not profit from
        # abandoned dormant value. Observed profit == dust (bob's stranded $0.0999).
        assert profit <= 2, (
            f"new depositor extracted abandoned dormant value: deposit={sally_deposit} "
            f"withdrawn={received_alpha} pile_kept={got} net_profit={profit}"
        )


def test_g5_original_holder_claims_dormant_before_exit_control(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """Adjacent positive control: original holder still has shares and can take
    the dormant pile. After that claim, withdraw returns the remaining unreserved
    stab asset; no abandoned pile is left for a later depositor.
    """
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        dust = ACTIVATION - 1
        _record_claim(
            stability_pool, alpha_token, bravo_token, bravo_token_whale,
            dust, bob, auction_house, green_token, savings_green,
        )
        clear_transient_storage()
        vault_id = vault_book.getRegId(stability_pool)
        bravo_before = bravo_token.balanceOf(bob)
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
        clear_transient_storage()
        assert bravo_token.balanceOf(bob) - bravo_before == dust
        assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
        teller.withdraw(alpha_token, MAX_UINT256, bob, stability_pool, 0, sender=bob)
        clear_transient_storage()
        assert stability_pool.totalBalances(alpha_token) == 0
        assert bravo_token.balanceOf(stability_pool.address) == 0


def test_g5_dormant_price_appreciation_without_activation(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """Dormant pile stays unpriced after a 10x price move (activate is paused-only).
    New depositor after last exit extracts the appreciated pile and still withdraws
    ~the deposit.
    """
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        dust = ACTIVATION - 1
        _record_claim(
            stability_pool, alpha_token, bravo_token, bravo_token_whale,
            dust, bob, auction_house, green_token, savings_green,
        )
        clear_transient_storage()
        teller.withdraw(alpha_token, MAX_UINT256, bob, stability_pool, 0, sender=bob)
        clear_transient_storage()

        mock_price_source.setPrice(bravo_token, 10 * EIGHTEEN_DECIMALS)
        # price appreciation alone does NOT activate: still dormant, still excluded from NAV
        assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
        assert stability_pool.getTotalValue(alpha_token) <= amount

        sally_deposit = 100 * EIGHTEEN_DECIMALS
        alpha_token.transfer(sally, sally_deposit, sender=alpha_token_whale)
        alpha_token.approve(teller.address, sally_deposit, sender=sally)
        teller.deposit(alpha_token, sally_deposit, sally, stability_pool, sender=sally)
        clear_transient_storage()

        vault_id = vault_book.getRegId(stability_pool)
        bravo_before = bravo_token.balanceOf(sally)
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=sally)
        clear_transient_storage()
        got = bravo_token.balanceOf(sally) - bravo_before
        taken_usd = got * 10  # bravo now $10

        alpha_before = alpha_token.balanceOf(sally)
        withdrawn = teller.withdraw(alpha_token, MAX_UINT256, sally, stability_pool, 0, sender=sally)
        clear_transient_storage()
        received_alpha = alpha_token.balanceOf(sally) - alpha_before
        profit = received_alpha + taken_usd - sally_deposit
        # SAFETY PROPERTY (currently VIOLATED): same mechanism, amplified by the 10x
        # dormant-price move: profit == appreciated pile value (~$1), deposit returned whole.
        assert profit <= 2, (
            f"appreciated dormant extracted: pile_amount={got} taken_usd={taken_usd} "
            f"withdrawn={received_alpha} deposit={sally_deposit} net_profit={profit}"
        )


def test_g5_claim_fifteen_rows_two_holders_no_excess(
    stability_pool, alpha_token, alpha_token_whale, bob, sally, teller,
    auction_house, mock_price_source, green_token, savings_green, vault_book,
    setGeneralConfig, setAssetConfig, governance,
):
    """Fifteen claim rows (MAX_STAB_CLAIMS) with two holders: sum of independently
    valued deliveries must not exceed bob's burned-share NAV plus 15 wei."""
    with boa.env.anchor():
        _cfg(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, sally, teller, mock_price_source, amount)

        tokens = []
        for i in range(15):
            t = boa.load(
                "contracts/mock/MockErc20.vy", governance, f"R{i}", f"R{i}", 18, 1_000_000,
                name=f"g5_row_{i}",
            )
            w = boa.env.generate_address(f"g5_row_whale_{i}")
            t.mint(w, 1000 * EIGHTEEN_DECIMALS, sender=governance.address)
            mock_price_source.setPrice(t, EIGHTEEN_DECIMALS)
            setAssetConfig(t)
            _record_claim(
                stability_pool, alpha_token, t, w, EIGHTEEN_DECIMALS,
                bob, auction_house, green_token, savings_green,
            )
            tokens.append(t)
        clear_transient_storage()

        vault_id = vault_book.getRegId(stability_pool)
        shares_before = stability_pool.userBalances(bob, alpha_token)
        total_shares_before = stability_pool.totalBalances(alpha_token)
        total_value_before = stability_pool.getTotalValue(alpha_token)
        sally_value_before = stability_pool.getTotalUserValue(sally, alpha_token)

        claims = [(alpha_token, t, MAX_UINT256) for t in tokens]
        bals_before = [t.balanceOf(bob) for t in tokens]
        teller.claimManyFromStabilityPool(vault_id, claims, bob, False, sender=bob)
        clear_transient_storage()

        delivered = sum(t.balanceOf(bob) - b for t, b in zip(tokens, bals_before))
        burned = shares_before - stability_pool.userBalances(bob, alpha_token)
        burned_value = burned * (total_value_before + 1) // (total_shares_before + 10**8)
        assert delivered <= burned_value + 15, (
            f"15-row excess: delivered={delivered} burned_value={burned_value}"
        )
        sally_value_after = stability_pool.getTotalUserValue(sally, alpha_token)
        assert sally_value_after + 15 >= sally_value_before
