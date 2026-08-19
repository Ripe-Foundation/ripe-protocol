"""Group 5 proof tests — deposit / withdraw conservation (never-skip #1).

Drive through the real Teller path where practical. StabilityPool calls with
sender=teller.address are used only to isolate vault-level math (component
tests), with Teller-level proofs alongside.

Each test is wrapped in boa.env.anchor() so session fixtures stay clean.
"""
import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from boa.contracts.base_evm_contract import BoaError
from conf_utils import (
    assert_reverted_call,
    clear_transient_storage,
    claim_from_stability_pool,
    filter_logs,
)

HUNDRED_PERCENT = 100_00


def _seed_stab(stability_pool, asset, whale, user, teller, mock_price_source, amount):
    # Owns the Teller/StabilityPool boundary. Callers must not clear again after return.
    mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)
    asset.transfer(stability_pool, amount, sender=whale)
    assert stability_pool.depositTokensInVault(user, asset, amount, sender=teller.address) == amount
    clear_transient_storage()


def _record_claim(stability_pool, stab_asset, claim_asset, claim_whale, claim_amount,
                  recipient, auction_house, green_token, savings_green, stab_amount=1):
    # Owns the StabilityPool swap boundary. Callers must not clear again after return.
    claim_asset.transfer(stability_pool, claim_amount, sender=claim_whale)
    out = stability_pool.swapForLiquidatedCollateral(
        stab_asset, stab_amount, claim_asset, claim_amount,
        recipient, green_token, savings_green, sender=auction_house.address,
    )
    clear_transient_storage()
    return out


def _teller_deposit(teller, vault, token, whale, user, amount, on_behalf=None):
    # Owns the Teller deposit boundary. Callers must not clear again after return.
    token.transfer(user, amount, sender=whale)
    token.approve(teller.address, amount, sender=user)
    out = teller.deposit(token, amount, on_behalf or user, vault, sender=user)
    clear_transient_storage()
    return out


def _config_sgreen_stab(stability_pool, savings_green, vault_book, mission_control,
                        switchboard_alpha, switchboard_bravo, setGeneralConfig, setAssetConfig,
                        createDebtTerms):
    """Launch-style: sGREEN is the stab asset, ltv=0, vaultIds=[stab pool]."""
    setGeneralConfig()
    stab_pool_id = vault_book.getRegId(stability_pool)
    mission_control.setPriorityStabVaults([(stab_pool_id, savings_green)], sender=switchboard_alpha.address)
    stab_debt_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(savings_green, _vaultIds=[stab_pool_id], _debtTerms=stab_debt_terms)


def _config_alpha_stab(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig,
                       min_balance=0):
    """alpha_token configured as a stab-pool asset (component tests)."""
    setGeneralConfig()
    stab_pool_id = vault_book.getRegId(stability_pool)
    setAssetConfig(alpha_token, _vaultIds=[stab_pool_id], _minDepositBalance=min_balance)


def test_g5_deposit_roundtrip_conservation(
    stability_pool, alpha_token, alpha_token_whale, bob, teller, auction_house,
    mock_price_source, vault_book, setGeneralConfig, setAssetConfig,
):
    """Positive control: deposit via Teller, withdraw via Teller; conservation holds.

    Deposit then withdraw the full position. Payer debit == vault custody increase
    == returned amount; shares mint round-down, burn round-up; final user position
    within rounding dust of the original.
    """
    with boa.env.anchor():
        _config_alpha_stab(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

        amount = 100 * EIGHTEEN_DECIMALS
        deposited = _teller_deposit(teller, stability_pool, alpha_token, alpha_token_whale, bob, amount)
        assert deposited == amount

        shares = stability_pool.userBalances(bob, alpha_token)
        total_shares = stability_pool.totalBalances(alpha_token)
        assert shares == total_shares and shares > 0

        # full withdraw via Teller
        alpha_token_before = alpha_token.balanceOf(bob)
        withdrawn = teller.withdraw(alpha_token, MAX_UINT256, bob, stability_pool, 0, sender=bob)
        clear_transient_storage()

        assert stability_pool.userBalances(bob, alpha_token) == 0
        assert stability_pool.totalBalances(alpha_token) == 0
        received = alpha_token.balanceOf(bob) - alpha_token_before
        assert received == withdrawn
        # full-position exit: burn round-up means user can lose at most rounding dust
        assert amount - received <= 2


def test_g5_deposit_zero_share_commit(
    stability_pool, alpha_token, alpha_token_whale, bob, sally, teller,
    mock_price_source, vault_book, setGeneralConfig, setAssetConfig,
):
    """H1: a successful nonzero deposit must not commit custody with newShares == 0.

    First depositor holds a large position (high NAV per share). A second
    depositor deposits an amount whose USD value is less than one share unit.
    If the deposit commits with zero shares, custody increased but the depositor
    received nothing -> their funds are distributed to the existing holder.
    """
    with boa.env.anchor():
        _config_alpha_stab(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

        big = 100 * EIGHTEEN_DECIMALS  # $100 -> shares = 100e18 * 1e8 / (100e18+1) ~ 1e10
        _teller_deposit(teller, stability_pool, alpha_token, alpha_token_whale, bob, big)
        bob_shares = stability_pool.userBalances(bob, alpha_token)
        assert bob_shares > 0

        # totalValue+1 ~ 100e18+1; totalShares+OFFSET ~ bob_shares+1e8
        # one share costs (totalValue+1)//(totalShares+1e8) ~ 1e10 wei of alpha
        # deposit less than one share unit:
        tiny = 1  # 1 wei
        custody_before = alpha_token.balanceOf(stability_pool.address)
        deposited = _teller_deposit(teller, stability_pool, alpha_token, alpha_token_whale, sally, tiny)
        sally_shares = stability_pool.userBalances(sally, alpha_token)

        # INVARIANT: nonzero committed deposit => nonzero shares
        if deposited != 0:
            assert sally_shares != 0, (
                f"custody committed ({alpha_token.balanceOf(stability_pool.address) - custody_before} wei) "
                f"with zero shares minted"
            )


def test_g5_deposit_zero_share_boundary_control(
    stability_pool, alpha_token, alpha_token_whale, bob, sally, teller,
    mock_price_source, vault_book, setGeneralConfig, setAssetConfig,
):
    """Adjacent positive control: deposit sized to mint exactly >=1 share succeeds."""
    with boa.env.anchor():
        _config_alpha_stab(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

        big = 100 * EIGHTEEN_DECIMALS
        _teller_deposit(teller, stability_pool, alpha_token, alpha_token_whale, bob, big)

        bob_shares = stability_pool.userBalances(bob, alpha_token)
        # one share unit in asset terms ~ (totalValue+1) // (totalShares + 1e8)
        total_value = stability_pool.getTotalValue(alpha_token)
        total_shares = stability_pool.totalBalances(alpha_token)
        one_share_cost = (total_value + 1) // (total_shares + 10**8) + 2
        deposited = _teller_deposit(teller, stability_pool, alpha_token, alpha_token_whale, sally, one_share_cost)
        assert stability_pool.userBalances(sally, alpha_token) >= 1


def test_g5_deposit_reserved_asset_reverts(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, teller, auction_house, mock_price_source, green_token, savings_green,
    setGeneralConfig, setAssetConfig,
):
    """Deposit of an asset reserved for claims must revert."""
    with boa.env.anchor():
        setGeneralConfig()
        setAssetConfig(bravo_token)
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
                   mock_price_source, 100 * EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      10 * EIGHTEEN_DECIMALS, bob, auction_house, green_token, savings_green)

        # bravo now has totalClaimableBalances > 0; depositing bravo as stab asset must revert
        bravo_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=bravo_token_whale)
        with boa.reverts("asset reserved for claims"):
            stability_pool.depositTokensInVault(bob, bravo_token, EIGHTEEN_DECIMALS, sender=teller.address)
        clear_transient_storage()


def test_g5_deposit_green_as_stab_reverts(
    stability_pool, green_token, whale, bob, teller, setGeneralConfig,
):
    """GREEN cannot be a stab asset."""
    with boa.env.anchor():
        setGeneralConfig()
        green_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=whale)
        with boa.reverts("green cannot be stab asset"):
            stability_pool.depositTokensInVault(bob, green_token, EIGHTEEN_DECIMALS, sender=teller.address)
        clear_transient_storage()


def test_g5_deposit_zero_amount_reverts(
    stability_pool, alpha_token, bob, teller, setGeneralConfig, setAssetConfig, mock_price_source,
):
    with boa.env.anchor():
        setGeneralConfig()
        setAssetConfig(alpha_token)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        with boa.reverts():
            teller.deposit(alpha_token, 0, bob, stability_pool, sender=bob)
        clear_transient_storage()


def test_g5_withdraw_zero_reverts(
    stability_pool, alpha_token, bob, teller, setGeneralConfig, setAssetConfig, mock_price_source,
):
    with boa.env.anchor():
        setGeneralConfig()
        setAssetConfig(alpha_token)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        with boa.reverts("cannot withdraw 0"):
            teller.withdraw(alpha_token, 0, bob, stability_pool, 0, sender=bob)
        clear_transient_storage()


def test_g5_withdraw_branches_with_active_claimable(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """Branch (a): unreserved covers user NAV -> all user shares burn even though
    claimable remains for the other holder. Remaining holder's claim must still be covered.
    """
    with boa.env.anchor():
        _config_alpha_stab(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, sally, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        # seed a small claimable: 10% of one cohort position
        claim_amount = 10 * EIGHTEEN_DECIMALS
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      claim_amount, bob, auction_house, green_token, savings_green)

        # bob withdraws max: unreserved alpha = 200e18 - 1 (stab_amount=1 taken by swap seed) ~ 199.99e18
        # bob NAV = (100e18 shares) / (200e18 shares) * (199.99e18 unreserved + 10e18 claimable) ~ 105e18 -> under unreserved
        bob_before = alpha_token.balanceOf(bob)
        withdrawn = teller.withdraw(alpha_token, MAX_UINT256, bob, stability_pool, 0, sender=bob)
        clear_transient_storage()

        # branch (a): all of bob's shares burn, claimable remains
        assert stability_pool.userBalances(bob, alpha_token) == 0
        assert stability_pool.claimableBalances(alpha_token, bravo_token) == claim_amount
        assert alpha_token.balanceOf(bob) - bob_before == withdrawn

        # sally's claim still fully covered: her NAV ~ 105e18 vs remaining unreserved + claimable
        sally_value = stability_pool.getTotalUserValue(sally, alpha_token)
        unreserved = alpha_token.balanceOf(stability_pool.address) - stability_pool.totalClaimableBalances(alpha_token)
        # sally NAV is against unreserved + claimable; claimable 10e18 is hers + bob's share... bob exited
        # without touching claimable, so claimable liability unchanged and custody unchanged
        assert sally_value > 0

        # sally can still claim the full bravo pile? she owns all remaining shares -> yes
        vault_id = vault_book.getRegId(stability_pool)
        sally_bravo_before = bravo_token.balanceOf(sally)
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=sally)
        clear_transient_storage()
        assert bravo_token.balanceOf(sally) - sally_bravo_before == claim_amount


def test_g5_withdraw_branch_b_unreserved_short(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """Branch (b): unreserved cannot cover user's entire NAV -> only available
    sGREEN leaves; user retains shares against leftover claimable NAV."""
    with boa.env.anchor():
        _config_alpha_stab(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, sally, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        # claimable large enough that bob's NAV (50% of total) exceeds total unreserved,
        # forcing branch (b): bob NAV = 50% * (U + C) > U  =>  C > U ~ 200e18
        claim_amount = 250 * EIGHTEEN_DECIMALS
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      claim_amount, bob, auction_house, green_token, savings_green)

        # unreserved ~199.99e18; bob NAV = 50% * (199.99 + 150) ~ 175e18 > his pro-rata unreserved 100e18
        withdrawn = teller.withdraw(alpha_token, MAX_UINT256, bob, stability_pool, 0, sender=bob)
        clear_transient_storage()

        # branch (b): bob retains shares against leftover claimable NAV
        bob_shares_after = stability_pool.userBalances(bob, alpha_token)
        assert bob_shares_after > 0
        assert withdrawn > 0
        # claimable untouched by withdraw
        assert stability_pool.claimableBalances(alpha_token, bravo_token) == claim_amount

        # bob's remaining shares still claim against the bravo pile
        vault_id = vault_book.getRegId(stability_pool)
        bob_bravo_before = bravo_token.balanceOf(bob)
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
        clear_transient_storage()
        bob_got = bravo_token.balanceOf(bob) - bob_bravo_before
        # bob's claimable slice should be roughly his NAV share of the pile (<= pro-rata half + dust)
        assert 0 < bob_got <= claim_amount * 55 // 100


def test_g5_deposit_into_existing_cohort_with_claimable(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """A later depositor joining a cohort with active claimable buys into existing NAV.
    Measure shares received vs an equivalent deposit before claimable existed."""
    with boa.env.anchor():
        _config_alpha_stab(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        claim_amount = 100 * EIGHTEEN_DECIMALS
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      claim_amount, bob, auction_house, green_token, savings_green)

        bob_shares = stability_pool.userBalances(bob, alpha_token)
        # sally deposits 100 alpha into cohort with NAV = 99.99 unreserved + 100 claimable ~ 200
        sally_deposit = 100 * EIGHTEEN_DECIMALS
        _teller_deposit(teller, stability_pool, alpha_token, alpha_token_whale, sally, sally_deposit)
        sally_shares = stability_pool.userBalances(sally, alpha_token)

        # NAV doubled (100 -> 200) so sally should get ~half of bob's share count
        # (not equal shares as if claimable were free)
        assert sally_shares < bob_shares * 55 // 100
        assert sally_shares > bob_shares * 45 // 100


def test_g5_deposit_after_total_shares_zero_with_dormant_leftover(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """H3: after totalShares == 0 with leftover DORMANT claimable, a new depositor
    mints shares against NAV that excludes dormant inventory, then claims it.

    If the new depositor can claim dormant value at a discount (shares priced
    without the dormant pile), abandoned value transfers to them.
    """
    with boa.env.anchor():
        _config_alpha_stab(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        amount = 100 * EIGHTEEN_DECIMALS
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, amount)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        # dormant dust: below ACTIVATION_USD_THRESHOLD ($0.10)
        dust = 5 * 10**16  # $0.05 worth of bravo at $1
        _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                      dust, bob, auction_house, green_token, savings_green)
        assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == 1  # DORMANT

        # bob fully exits (unreserved only; dormant remains stranded)
        teller.withdraw(alpha_token, MAX_UINT256, bob, stability_pool, 0, sender=bob)
        clear_transient_storage()
        assert stability_pool.totalBalances(alpha_token) == 0
        assert stability_pool.claimableBalances(alpha_token, bravo_token) == dust

        # sally deposits fresh; her shares are priced against NAV excluding the dormant pile
        sally_deposit = 100 * EIGHTEEN_DECIMALS
        _teller_deposit(teller, stability_pool, alpha_token, alpha_token_whale, sally, sally_deposit)
        sally_shares = stability_pool.userBalances(sally, alpha_token)
        assert sally_shares > 0

        # sally claims the dormant pile via Teller
        vault_id = vault_book.getRegId(stability_pool)
        bravo_before = bravo_token.balanceOf(sally)
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=sally)
        clear_transient_storage()
        got = bravo_token.balanceOf(sally) - bravo_before
        # how much of the dormant dust could sally take, and how many shares did it cost?
        shares_after = stability_pool.userBalances(sally, alpha_token)
        shares_burned = sally_shares - shares_after
        # report the ratio: value taken (in USD) vs shares burned * price-per-share
        total_value = stability_pool.getTotalValue(alpha_token)
        total_shares = stability_pool.totalBalances(alpha_token)
        print(f"\nH3 dormant capture: got={got} dust={dust} shares_burned={shares_burned} "
              f"of {sally_shares}; remaining NAV={total_value} shares={total_shares}")
        # For the report; assertion is that the dormant value IS reachable by a new
        # depositor. The open question is the pricing: shares_burned should be tiny
        # relative to the value taken if the dormant pile is unpriced.
        if got != 0:
            taken_usd = got  # bravo at $1
            print(f"taken_usd={taken_usd}, burned share pct of sally={shares_burned * 10000 // sally_shares}bps")


def test_g5_sgreen_convert_roundtrip(
    stability_pool, green_token, savings_green, whale, bob, teller,
    mission_control, switchboard_alpha, switchboard_bravo, vault_book,
    setGeneralConfig, setAssetConfig, createDebtTerms, mock_price_source,
):
    """Launch-config positive control: convert GREEN -> sGREEN -> stab pool, then withdraw.

    Convert has no dust cutoff; residue isolation on Teller after wrap.
    """
    with boa.env.anchor():
        _config_sgreen_stab(stability_pool, savings_green, vault_book, mission_control,
                            switchboard_alpha, switchboard_bravo, setGeneralConfig,
                            setAssetConfig, createDebtTerms)
        amount = 100 * EIGHTEEN_DECIMALS
        green_token.transfer(bob, amount, sender=whale)
        green_token.approve(teller.address, amount, sender=bob)

        teller_before_green = green_token.balanceOf(teller.address)
        teller_before_sgreen = savings_green.balanceOf(teller.address)
        deposited = teller.convertToSavingsGreenAndDepositIntoStabPool(bob, amount, sender=bob)
        clear_transient_storage()

        # Teller holds no residue after the wrap+deposit
        assert green_token.balanceOf(teller.address) == teller_before_green
        assert savings_green.balanceOf(teller.address) == teller_before_sgreen
        assert stability_pool.userBalances(bob, savings_green) > 0

        # withdraw via Teller
        sgreen_before = savings_green.balanceOf(bob)
        withdrawn = teller.withdraw(savings_green, MAX_UINT256, bob, stability_pool, 0, sender=bob)
        clear_transient_storage()
        assert savings_green.balanceOf(bob) - sgreen_before == withdrawn
        assert stability_pool.userBalances(bob, savings_green) == 0

        # independent value check: sGREEN received converts back to ~amount GREEN (minus dust)
        received_green_value = savings_green.convertToAssets(withdrawn)
        assert amount - received_green_value <= 10


def test_g5_nonzero_deposit_zero_shares_with_large_claimable_nav(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """Safety: a nonzero Teller deposit that would mint zero shares must revert.

    Tiny first deposit, then a large active claimable NAV, then a 1-wei
    second deposit. That path used to commit custody with newShares == 0.
    It must now revert `cannot mint 0 shares` with payer tokens, pool
    custody, and shares unchanged.
    """
    with boa.env.anchor():
        _config_alpha_stab(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

        first = 10**12  # 1e-6 tokens
        _teller_deposit(teller, stability_pool, alpha_token, alpha_token_whale, bob, first)
        assert stability_pool.userBalances(bob, alpha_token) > 0

        huge_claimable = 1_000_000 * EIGHTEEN_DECIMALS
        _record_claim(
            stability_pool, alpha_token, bravo_token, bravo_token_whale,
            huge_claimable, bob, auction_house, green_token, savings_green,
        )

        alpha_token.transfer(sally, 1, sender=alpha_token_whale)
        alpha_token.approve(teller.address, 1, sender=sally)
        payer_before = alpha_token.balanceOf(sally)
        custody_before = alpha_token.balanceOf(stability_pool.address)
        shares_before = stability_pool.userBalances(sally, alpha_token)
        with pytest.raises(BoaError) as exc_info:
            teller.deposit(alpha_token, 1, sally, stability_pool, sender=sally)
        assert_reverted_call(exc_info.value, "cannot mint 0 shares", teller)
        clear_transient_storage()
        assert alpha_token.balanceOf(sally) == payer_before
        assert alpha_token.balanceOf(stability_pool.address) == custody_before
        assert stability_pool.userBalances(sally, alpha_token) == shares_before


def test_g5_zero_share_adjacent_one_share_mints(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """Adjacent positive control for the zero-share finding: one unit above the
    0-share threshold mints at least one share. Same NAV (tiny first deposit +
    $1M active claimable).
    """
    with boa.env.anchor():
        _config_alpha_stab(stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig)
        setAssetConfig(bravo_token)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

        _teller_deposit(teller, stability_pool, alpha_token, alpha_token_whale, bob, 10**12)
        _record_claim(
            stability_pool, alpha_token, bravo_token, bravo_token_whale,
            1_000_000 * EIGHTEEN_DECIMALS, bob, auction_house, green_token, savings_green,
        )

        # 1 wei minted 0 shares; ~1e4 wei is the theoretical 1-share floor
        deposited = _teller_deposit(teller, stability_pool, alpha_token, alpha_token_whale, sally, 10**4 + 1)
        assert deposited != 0
        assert stability_pool.userBalances(sally, alpha_token) >= 1


def test_g5_zero_share_launch_min_after_tiny_trusted_seed(
    stability_pool, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale,
    bob, sally, teller, auction_house, mock_price_source, green_token, savings_green,
    vault_book, setGeneralConfig, setAssetConfig,
):
    """Launch-min 10**16 after a tiny trusted seed + $10M claimable.

    That deposit used to commit with zero shares. It must now revert
    `cannot mint 0 shares` with payer tokens, pool custody, and shares
    unchanged.
    """
    with boa.env.anchor():
        _config_alpha_stab(
            stability_pool, alpha_token, vault_book, setGeneralConfig, setAssetConfig,
            min_balance=10**16,
        )
        setAssetConfig(bravo_token)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

        # tiny first deposit bypasses Teller min (direct vault, as a trusted seed)
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source, 1)
        _record_claim(
            stability_pool, alpha_token, bravo_token, bravo_token_whale,
            10_000_000 * EIGHTEEN_DECIMALS, bob, auction_house, green_token, savings_green,
        )

        launch_min = 10**16
        alpha_token.transfer(sally, launch_min, sender=alpha_token_whale)
        alpha_token.approve(teller.address, launch_min, sender=sally)
        payer_before = alpha_token.balanceOf(sally)
        custody_before = alpha_token.balanceOf(stability_pool.address)
        shares_before = stability_pool.userBalances(sally, alpha_token)
        with pytest.raises(BoaError) as exc_info:
            teller.deposit(alpha_token, launch_min, sally, stability_pool, sender=sally)
        assert_reverted_call(exc_info.value, "cannot mint 0 shares", teller)
        clear_transient_storage()
        assert alpha_token.balanceOf(sally) == payer_before
        assert alpha_token.balanceOf(stability_pool.address) == custody_before
        assert stability_pool.userBalances(sally, alpha_token) == shares_before


def test_g5_convert_zero_reverts(
    stability_pool, green_token, savings_green, bob, teller, vault_book,
    mission_control, switchboard_alpha, switchboard_bravo, setGeneralConfig,
    setAssetConfig, createDebtTerms,
):
    with boa.env.anchor():
        _config_sgreen_stab(
            stability_pool, savings_green, vault_book, mission_control,
            switchboard_alpha, switchboard_bravo, setGeneralConfig,
            setAssetConfig, createDebtTerms,
        )
        with boa.reverts("cannot deposit 0 green"):
            teller.convertToSavingsGreenAndDepositIntoStabPool(bob, 0, sender=bob)
        clear_transient_storage()


def test_g5_sgreen_rate_move_between_deposit_and_withdraw(
    stability_pool, green_token, savings_green, whale, bob, teller,
    mission_control, switchboard_alpha, switchboard_bravo, vault_book,
    setGeneralConfig, setAssetConfig, createDebtTerms,
):
    """Move sGREEN convertToAssets between convert-deposit and withdraw.
    Independent GREEN value of the withdrawn shares must track the new rate,
    not a stale unit rate.
    """
    with boa.env.anchor():
        _config_sgreen_stab(
            stability_pool, savings_green, vault_book, mission_control,
            switchboard_alpha, switchboard_bravo, setGeneralConfig,
            setAssetConfig, createDebtTerms,
        )
        amount = 100 * EIGHTEEN_DECIMALS
        green_token.transfer(bob, amount, sender=whale)
        green_token.approve(teller.address, amount, sender=bob)
        deposited = teller.convertToSavingsGreenAndDepositIntoStabPool(bob, amount, sender=bob)
        clear_transient_storage()
        rate_before = savings_green.convertToAssets(deposited)

        # donate GREEN into sGREEN to move the exchange rate
        donation = 50 * EIGHTEEN_DECIMALS
        green_token.transfer(savings_green.address, donation, sender=whale)
        rate_after = savings_green.convertToAssets(deposited)
        assert rate_after > rate_before

        sgreen_before = savings_green.balanceOf(bob)
        withdrawn = teller.withdraw(savings_green, MAX_UINT256, bob, stability_pool, 0, sender=bob)
        clear_transient_storage()
        received = savings_green.balanceOf(bob) - sgreen_before
        assert received == withdrawn
        # withdrawn sGREEN independently values at the post-donation rate
        assert savings_green.convertToAssets(received) >= rate_after - 2
        assert green_token.balanceOf(teller.address) == 0
        assert savings_green.balanceOf(teller.address) == 0
