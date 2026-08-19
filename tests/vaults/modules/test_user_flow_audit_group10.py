# Group 10 proof tests — prune / activate / custody-deficit safety property.
#
# Dedicated file for the permissionless-maintenance audit (Group 10). Does not
# modify shared fixtures or existing assertions. Claimable rows are seeded with
# `swapForLiquidatedCollateral(..., sender=auction_house.address)`, which
# impersonates AuctionHouse and skips the Group 1 swap path. Pauses use both
# the suite shortcut (`sender=switchboard_alpha.address`, address impersonation,
# not Charlie's production path) and the production `SwitchboardCharlie.pause`
# (immediate, governor). Prune / activate callers are always ordinary EOAs.
#
# Mock price strategy: setPrice(token, P) quotes P USD (1e18) per whole token,
# so a claim of N atoms prices at N * P / 1e18. Balances are chosen so the pair
# USD lands on the hysteresis point under test.

from pathlib import Path

import boa
import pytest

from conf_utils import filter_logs
from constants import MAX_UINT256


EIGHTEEN = 10**18
ACTIVATION = 10**17          # $0.10
RETENTION = 5 * 10**16       # $0.05
MAX_ACTIVE = 20
MAX_MAINT = 15
ROOT = Path(__file__).resolve().parents[3]

CLAIM_ABSENT = 0
CLAIM_DORMANT = 1
CLAIM_ACTIVE = 2
DEACTIVATION_ZERO = 1
DEACTIVATION_DUST = 2


def _seed_stab(stability_pool, asset, whale, user, teller, mock_price_source,
               amount=100 * EIGHTEEN):
    mock_price_source.setPrice(asset, EIGHTEEN)
    asset.transfer(stability_pool, amount, sender=whale)
    stability_pool.depositTokensInVault(user, asset, amount, sender=teller.address)


def _record_claim(stability_pool, stab_asset, claim_asset, claim_whale,
                  claim_amount, recipient, auction_house, green_token,
                  savings_green, stab_amount=1):
    claim_asset.transfer(stability_pool, claim_amount, sender=claim_whale)
    return stability_pool.swapForLiquidatedCollateral(
        stab_asset, stab_amount, claim_asset, claim_amount, recipient,
        green_token, savings_green, sender=auction_house.address,
    )


def _deploy_claim_token(governance, holder, index, amount=10 * EIGHTEEN):
    token = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        f"G10 Claim {index}",
        f"G10C{index}",
        18,
        0,
        name=f"g10_claim_{index}",
    )
    token.mint(holder, amount, sender=governance.address)
    return token


@pytest.fixture
def g10_pool(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    """Stab cohort (alpha, bob funded) + one claim token (bravo) priced $1."""
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN)
    return {
        "stab": alpha_token,
        "claim": bravo_token,
        "claim_whale": bravo_token_whale,
        "auction_house": auction_house,
        "green": green_token,
        "sgreen": savings_green,
        "prices": mock_price_source,
    }


def _exit_cohort(pool, stab, user, teller):
    pool.withdrawTokensFromVault(user, stab, MAX_UINT256, user, sender=teller.address)
    assert pool.totalBalances(stab) == 0


def _empty_activate(pool, stab, claims, switchboard, caller):
    assert pool.totalBalances(stab) == 0
    pool.pause(True, sender=switchboard.address)
    for start in range(0, len(claims), MAX_MAINT):
        pool.activateClaimAssets(stab, claims[start:start + MAX_MAINT], sender=caller)


def _exact_floor(amount):
    return (ACTIVATION * EIGHTEEN + amount - 1) // amount


def _claim_state(pool, stab, claims):
    return {
        "pairs": {c.address: pool.claimableBalances(stab, c) for c in claims},
        "totals": {c.address: pool.totalClaimableBalances(c) for c in claims},
        "indexes": {c.address: pool.indexOfClaimableAsset(stab, c) for c in claims},
        "states": {c.address: pool.getClaimAssetState(stab, c) for c in claims},
        "custody": {c.address: c.balanceOf(pool) for c in claims},
        "num": pool.numClaimableAssets(stab),
        "num_active": pool.getNumActiveClaimAssets(stab),
    }


# ---------------------------------------------------------------------------
# Never-skip #1: prune identity
# ---------------------------------------------------------------------------


def test_g10_prune_dust_by_eoa_moves_no_value_and_uses_reason_2(
    g10_pool, stability_pool, alice, bob, teller, mock_price_source,
    switchboard_alpha, alpha_token_whale,
):
    """EOA prune of a low-positive pair: list row only, reason 2, balances
    and custody untouched, NAV shrinks, and a later receipt re-activates the
    dormant pile at the same pair balance."""
    pool = stability_pool
    stab = g10_pool["stab"]
    claim = g10_pool["claim"]

    pile = ACTIVATION - 1
    _record_claim(pool, stab, claim, g10_pool["claim_whale"], pile,
                  alice, g10_pool["auction_house"], g10_pool["green"],
                  g10_pool["sgreen"])
    assert pool.getClaimAssetState(stab, claim) == CLAIM_DORMANT
    _exit_cohort(pool, stab, bob, teller)
    stab.transfer(pool, 100 * EIGHTEEN, sender=alpha_token_whale)
    mock_price_source.setPrice(claim, _exact_floor(pile))
    _empty_activate(pool, stab, [claim], switchboard_alpha, alice)
    pool.pause(False, sender=switchboard_alpha.address)
    assert pool.getClaimAssetState(stab, claim) == CLAIM_ACTIVE
    nav_before = pool.getTotalValue(stab)

    # Drop the quote so the pair prices just under retention.
    mock_price_source.setPrice(claim, RETENTION * EIGHTEEN // pile - 1)

    before = _claim_state(pool, stab, [claim])
    assert pool.pruneClaimableAssets(stab, [claim], sender=alice) is None
    logs = filter_logs(pool, "ClaimAssetDeactivated")
    assert len(logs) == 1
    assert logs[0].stabAsset == stab.address
    assert logs[0].claimAsset == claim.address
    assert logs[0].balance == pile
    assert logs[0].activeCount == 0
    assert logs[0].reason == DEACTIVATION_DUST

    after = _claim_state(pool, stab, [claim])
    # list membership changed; value did not move
    assert after["pairs"] == before["pairs"] == {claim.address: pile}
    assert after["totals"] == before["totals"] == {claim.address: pile}
    assert after["custody"] == before["custody"] == {claim.address: pile}
    assert after["indexes"] == {claim.address: 0}
    assert after["states"] == {claim.address: CLAIM_DORMANT}
    assert after["num"] == 1 and after["num_active"] == 0
    assert pool.getTotalValue(stab) == stab.balanceOf(pool)

    # Pruning a second time and pruning unknown rows is a no-op.
    # (boa get_logs only yields logs since the previous call, so this also
    # proves none of the three calls emitted)
    pool.pruneClaimableAssets(stab, [claim], sender=alice)
    pool.pruneClaimableAssets(stab, [], sender=alice)
    pool.pruneClaimableAssets(alice, [claim], sender=alice)  # unknown stab
    assert len(filter_logs(pool, "ClaimAssetDeactivated")) == 0

    # Restore price; a fresh receipt re-activates the same dormant pair.
    mock_price_source.setPrice(claim, EIGHTEEN)
    _record_claim(pool, stab, claim, g10_pool["claim_whale"], 1, alice,
                  g10_pool["auction_house"], g10_pool["green"],
                  g10_pool["sgreen"])
    assert pool.getClaimAssetState(stab, claim) == CLAIM_ACTIVE
    assert pool.getTotalValue(stab) > stab.balanceOf(pool)
    assert nav_before > stab.balanceOf(pool)


def test_g10_prune_hysteresis_boundaries_and_source_zero_skip(
    g10_pool, stability_pool, governance, alice, bob, teller, mock_price_source,
    switchboard_alpha, alpha_token_whale,
):
    """exact $0.05 stays; mid-band stays; >= $0.10 stays; source-zero stays
    and the rest of the batch still runs (PriceDesk fail-soft)."""
    pool = stability_pool
    stab = g10_pool["stab"]
    ah = g10_pool["auction_house"]
    green, sgreen = g10_pool["green"], g10_pool["sgreen"]

    t_exact = _deploy_claim_token(governance, alice, 1)
    t_band = _deploy_claim_token(governance, alice, 2)
    t_hi = _deploy_claim_token(governance, alice, 3)
    t_dust = _deploy_claim_token(governance, alice, 4)
    t_zero = _deploy_claim_token(governance, alice, 5)

    # Below-floor receipts, last-exit, then empty-cohort activate.
    for tok in (t_exact, t_band, t_hi, t_dust, t_zero):
        mock_price_source.setPrice(tok, EIGHTEEN)
        _record_claim(pool, stab, tok, alice, ACTIVATION - 1, alice, ah, green, sgreen)
        assert pool.getClaimAssetState(stab, tok) == CLAIM_DORMANT
    _exit_cohort(pool, stab, bob, teller)
    stab.transfer(pool, EIGHTEEN, sender=alpha_token_whale)
    for tok in (t_exact, t_band, t_hi, t_dust, t_zero):
        mock_price_source.setPrice(tok, _exact_floor(ACTIVATION - 1))
    _empty_activate(pool, stab, [t_exact, t_band, t_hi, t_dust, t_zero], switchboard_alpha, alice)
    pool.pause(False, sender=switchboard_alpha.address)
    for tok in (t_exact, t_band, t_hi, t_dust, t_zero):
        assert pool.getClaimAssetState(stab, tok) == CLAIM_ACTIVE
    pile = ACTIVATION - 1
    for tok, usd, ceil in (
        (t_exact, RETENTION, True),
        (t_band, RETENTION + 10**16, True),
        (t_hi, ACTIVATION, True),
        (t_dust, RETENTION - 1, False),
    ):
        price = ((usd * EIGHTEEN + pile - 1) // pile) if ceil else (usd * EIGHTEEN // pile)
        mock_price_source.setPrice(tok, price)

    # t_zero loses its feed entirely (PriceDesk fail-soft zero)
    mock_price_source.setPrice(t_zero, 0)

    pool.pruneClaimableAssets(stab, [t_exact, t_band, t_hi, t_dust, t_zero],
                              sender=alice)

    logs = filter_logs(pool, "ClaimAssetDeactivated")
    assert len(logs) == 1
    assert logs[0].claimAsset == t_dust.address
    assert logs[0].reason == DEACTIVATION_DUST
    for tok in (t_exact, t_band, t_hi, t_zero):
        assert pool.getClaimAssetState(stab, tok) == CLAIM_ACTIVE
    assert pool.getClaimAssetState(stab, t_dust) == CLAIM_DORMANT
    assert pool.getNumActiveClaimAssets(stab) == 4


def test_g10_prune_batch_swap_and_pop_middle_then_shifted_tail(
    g10_pool, stability_pool, governance, alice, bob, teller, mock_price_source,
    switchboard_alpha, alpha_token_whale,
):
    """active [A, B, C] + prune [A, C]: after A is removed, C sits in A's
    old index; the second request must still remove C, leave B intact, and
    emit correct event fields. Duplicates in one call are no-ops."""
    pool = stability_pool
    stab = g10_pool["stab"]
    ah = g10_pool["auction_house"]
    green, sgreen = g10_pool["green"], g10_pool["sgreen"]

    a = _deploy_claim_token(governance, alice, 11)
    b = _deploy_claim_token(governance, alice, 12)
    c = _deploy_claim_token(governance, alice, 13)
    for tok in (a, b, c):
        mock_price_source.setPrice(tok, EIGHTEEN)
        _record_claim(pool, stab, tok, alice, ACTIVATION - 1, alice, ah, green, sgreen)
    _exit_cohort(pool, stab, bob, teller)
    stab.transfer(pool, EIGHTEEN, sender=alpha_token_whale)
    for tok in (a, b, c):
        mock_price_source.setPrice(tok, _exact_floor(ACTIVATION - 1))
    _empty_activate(pool, stab, [a, b, c], switchboard_alpha, alice)
    pool.pause(False, sender=switchboard_alpha.address)

    assert [pool.claimableAssets(stab, i) for i in (1, 2, 3)] == [
        a.address, b.address, c.address,
    ]

    # all three priced to dust, but the batch only asks for A and C (twice)
    for tok in (a, b, c):
        mock_price_source.setPrice(tok, RETENTION - 1)
    pool.pruneClaimableAssets(stab, [a, c, c], sender=alice)

    logs = filter_logs(pool, "ClaimAssetDeactivated")
    assert len(logs) == 2
    assert logs[0].claimAsset == a.address
    # lastIndex - 1 at removal time: list of 3, so 2 (active count BEFORE
    # the decrement, per the event's own convention)
    assert logs[0].activeCount == 2
    assert logs[1].claimAsset == c.address
    assert logs[1].activeCount == 1
    assert pool.getClaimAssetState(stab, a) == CLAIM_DORMANT
    assert pool.getClaimAssetState(stab, b) == CLAIM_ACTIVE
    assert pool.getClaimAssetState(stab, c) == CLAIM_DORMANT
    assert pool.claimableAssets(stab, 1) == b.address
    assert pool.indexOfClaimableAsset(stab, b) == 1
    assert pool.claimableAssets(stab, 2) == "0x0000000000000000000000000000000000000000"
    assert pool.numClaimableAssets(stab) == 2
    assert pool.getNumActiveClaimAssets(stab) == 1


def test_g10_pruned_dormant_pile_remains_claimable_by_funded_shareholder(
    g10_pool, stability_pool, teller, bob, vault_book, mock_price_source,
    setGeneralConfig, setAssetConfig,
):
    """After a legal dust prune the now-dormant pile still claims (thin
    Group 5 measurement only: dormant pair balance is untouched and the
    claim math reads claimableBalances, not the active list)."""
    pool = stability_pool
    stab = g10_pool["stab"]
    claim = g10_pool["claim"]
    setGeneralConfig()          # genConfig.canClaimInStabPool = True
    setAssetConfig(claim)       # assetConfig.canClaimInStabPool = True
    vault_id = vault_book.getRegId(pool)

    _record_claim(pool, stab, claim, g10_pool["claim_whale"], ACTIVATION - 1,
                  bob, g10_pool["auction_house"], g10_pool["green"],
                  g10_pool["sgreen"])
    assert pool.getClaimAssetState(stab, claim) == CLAIM_DORMANT

    # honest price back; bob (funded shareholder) claims the dormant pile
    mock_price_source.setPrice(claim, EIGHTEEN)
    from conf_utils import claim_from_stability_pool
    got = claim_from_stability_pool(
        teller, vault_id, stab, claim, user=bob, sender=bob,
    )
    assert got > 0
    assert pool.claimableBalances(stab, claim) == 0
    assert pool.totalClaimableBalances(claim) == 0


# ---------------------------------------------------------------------------
# Never-skip #1a: custody-deficit safety property (required)
# ---------------------------------------------------------------------------


def test_g10_dust_prune_of_undercustodied_row_must_keep_nav_actions_blocked(
    g10_pool, stability_pool, alice, bob, teller, alpha_token,
    alpha_token_whale, mock_price_source,
):
    """SAFETY PROPERTY (brief never-skip 1a). An active pair with
    custody < totalClaimableBalances freezes deposit/withdraw/getTotalValue
    ('claim custody deficit'). A live-book dust prune is a membership no-op,
    so the short row stays on the iterable and NAV actions stay blocked.
    Deficit state is modeled by impersonating the pool
    (token.transfer sender=stability_pool) — fixture/direct-state only; the
    prune itself is an ordinary EOA call."""
    pool = stability_pool
    stab = g10_pool["stab"]
    claim = g10_pool["claim"]

    # active claim row worth $1 at honest price
    _record_claim(pool, stab, claim, g10_pool["claim_whale"], EIGHTEEN,
                  bob, g10_pool["auction_house"], g10_pool["green"],
                  g10_pool["sgreen"])
    assert pool.getClaimAssetState(stab, claim) == CLAIM_ACTIVE

    # model custody loss: one wei leaves pool custody (impersonation)
    claim.transfer(alice, 1, sender=pool.address)
    assert claim.balanceOf(pool) == EIGHTEEN - 1
    assert pool.totalClaimableBalances(claim) == EIGHTEEN

    with boa.reverts("claim custody deficit"):
        pool.getTotalValue(stab)
    with boa.reverts("claim custody deficit"):
        pool.depositTokensInVault(alice, stab, EIGHTEEN, sender=teller.address)
    with boa.reverts("claim custody deficit"):
        pool.withdrawTokensFromVault(bob, stab, EIGHTEEN, bob,
                                     sender=teller.address)

    # ordinary EOA prunes the row at a valid dust quote (< $0.05, nonzero)
    mock_price_source.setPrice(claim, RETENTION - 1)
    pool.pruneClaimableAssets(stab, [claim], sender=alice)
    assert filter_logs(pool, "ClaimAssetDeactivated") == []
    assert pool.getClaimAssetState(stab, claim) == CLAIM_ACTIVE

    # custody and liability are unchanged — the deficit is NOT settled
    assert claim.balanceOf(pool) == EIGHTEEN - 1
    assert pool.totalClaimableBalances(claim) == EIGHTEEN

    with boa.reverts("claim custody deficit"):
        pool.getTotalValue(stab)
    with boa.reverts("claim custody deficit"):
        pool.depositTokensInVault(alice, stab, EIGHTEEN, sender=teller.address)
    with boa.reverts("claim custody deficit"):
        pool.withdrawTokensFromVault(bob, stab, EIGHTEEN, bob, sender=teller.address)


# ---------------------------------------------------------------------------
# Never-skip #1b: share/NAV compositions (both required)
# ---------------------------------------------------------------------------


def test_g10_low_quote_prune_does_not_let_new_depositor_capture_restored_claim_nav(
    stability_pool, alpha_token, alpha_token_whale, bravo_token,
    bravo_token_whale, governance, alice, bob, teller, auction_house,
    switchboard_alpha, mock_price_source, green_token, savings_green,
):
    """Never-skip 1b(i). A live-share dust prune is a no-op, so a later
    depositor mints against the still-listed pile and cannot capture it.
    """
    pool = stability_pool
    stab, claim = alpha_token, bravo_token
    carol = boa.env.generate_address("carol")

    _seed_stab(pool, stab, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(claim, EIGHTEEN)
    _record_claim(pool, stab, claim, bravo_token_whale, 100 * EIGHTEEN, bob,
                  auction_house, green_token, savings_green)
    nav_honest = pool.getTotalValue(stab)
    assert nav_honest == 200 * EIGHTEEN - 1  # 100 stab + 100 claim - payout

    # wrong-but-nonzero low quote; live-share prune must not hide the pile
    mock_price_source.setPrice(claim, RETENTION * EIGHTEEN // (100 * EIGHTEEN) - 1)
    pool.pruneClaimableAssets(stab, [claim], sender=alice)
    assert pool.getClaimAssetState(stab, claim) == CLAIM_ACTIVE
    mock_price_source.setPrice(claim, EIGHTEEN)

    alpha_token.transfer(pool, 10 * EIGHTEEN, sender=alpha_token_whale)
    pool.depositTokensInVault(carol, stab, 10 * EIGHTEEN, sender=teller.address)
    pool.pause(True, sender=switchboard_alpha.address)
    pool.activateClaimAssets(stab, [claim], sender=alice)
    pool.pause(False, sender=switchboard_alpha.address)
    assert pool.getTotalValue(stab) == nav_honest + 10 * EIGHTEEN

    # carol's claim on total value vs the $10 she put in
    carol_value = pool.getTotalUserValue(carol, stab)
    capture = carol_value - 10 * EIGHTEEN
    assert abs(capture) <= 1, f"live-share prune must not transfer value: {capture}"

    # control: identical custody/honest price, no prune timing — the same
    # deposit after reactivation is worth exactly $10 (up to share rounding)
    bob2 = boa.env.generate_address("bob2")
    alpha_token.transfer(pool, 10 * EIGHTEEN, sender=alpha_token_whale)
    pool.depositTokensInVault(bob2, stab, 10 * EIGHTEEN, sender=teller.address)
    bob2_value = pool.getTotalUserValue(bob2, stab)
    assert abs(bob2_value - 10 * EIGHTEEN) <= 10 * EIGHTEEN // 1000


def test_g10_high_quote_activate_inflates_dormant_pile_into_nav(
    stability_pool, alpha_token, alpha_token_whale, bravo_token,
    bravo_token_whale, alice, bob, teller, auction_house, switchboard_alpha,
    mock_price_source, green_token, savings_green,
):
    """Never-skip 1b(ii). Live-share activate is a no-op, so a high quote
    cannot seat a dormant pile onto NAV for the exiting holder.
    """
    pool = stability_pool
    stab, claim = alpha_token, bravo_token

    _seed_stab(pool, stab, alpha_token_whale, bob, teller, mock_price_source)

    # dormant pile: honest pair USD $0.05 (below the $0.10 receipt floor)
    mock_price_source.setPrice(claim, EIGHTEEN)
    _record_claim(pool, stab, claim, bravo_token_whale, RETENTION, bob,
                  auction_house, green_token, savings_green)
    assert pool.getClaimAssetState(stab, claim) == CLAIM_DORMANT
    assert pool.getTotalValue(stab) == 100 * EIGHTEEN - 1

    # wrong high quote: live-share activate must not seat the dormant pile
    mock_price_source.setPrice(claim, EIGHTEEN * 2000)  # $100 for 0.05 tokens
    pool.pause(True, sender=switchboard_alpha.address)
    pool.activateClaimAssets(stab, [claim], sender=alice)
    pool.pause(False, sender=switchboard_alpha.address)
    assert pool.getClaimAssetState(stab, claim) == CLAIM_DORMANT
    assert pool.getTotalValue(stab) == 100 * EIGHTEEN - 1

    withdrawn, _ = pool.withdrawTokensFromVault(
        bob, stab, EIGHTEEN, bob, sender=teller.address,
    )
    assert withdrawn == EIGHTEEN

    mock_price_source.setPrice(claim, EIGHTEEN)
    assert pool.getTotalValue(stab) == 99 * EIGHTEEN - 1


# ---------------------------------------------------------------------------
# Never-skip #2: activate identity
# ---------------------------------------------------------------------------


def test_g10_activate_requires_pause_and_moves_no_value(
    stability_pool, alpha_token, alpha_token_whale, bravo_token,
    bravo_token_whale, alice, bob, teller, auction_house, switchboard_alpha,
    switchboard_charlie, governance, mock_price_source, green_token,
    savings_green,
):
    """Unpaused activate reverts. Pause via BOTH the suite shortcut and the
    production Charlie pause (immediate, governor). Exact $0.10 activates;
    just-below and source-zero skip; duplicates emit one event; zero /
    unknown addresses skip; balances and custody never move."""
    pool = stability_pool
    stab = alpha_token
    _seed_stab(pool, stab, alpha_token_whale, bob, teller, mock_price_source)

    # two dormant piles: one priced at exactly $0.10 on activate, one just under
    low = _deploy_claim_token(governance, alice, 21)
    high = _deploy_claim_token(governance, alice, 22)
    for tok in (low, high):
        mock_price_source.setPrice(tok, EIGHTEEN)
        _record_claim(pool, stab, tok, alice, RETENTION, bob, auction_house,
                      green_token, savings_green)
        assert pool.getClaimAssetState(stab, tok) == CLAIM_DORMANT

    # unpaused activate reverts, no list change
    with boa.reverts("contract not paused"):
        pool.activateClaimAssets(stab, [low, high], sender=alice)

    _exit_cohort(pool, stab, bob, teller)
    alpha_token.transfer(pool, EIGHTEEN, sender=alpha_token_whale)

    # PRODUCTION PAUSE: Charlie.pause(stability_pool, True), governor, immediate
    assert switchboard_charlie.pause(pool.address, True, sender=governance.address)
    assert pool.isPaused()

    # independent quotes: low just under $0.10, high exactly $0.10
    mock_price_source.setPrice(low, (ACTIVATION - 1) * EIGHTEEN // RETENTION)
    mock_price_source.setPrice(high, ACTIVATION * EIGHTEEN // RETENTION)

    before = _claim_state(pool, stab, [low, high])
    pool.activateClaimAssets(
        stab, [high, low, high, boa.env.generate_address("nobody")],
        sender=alice,
    )
    logs = filter_logs(pool, "ClaimAssetActivated")
    assert len(logs) == 1  # duplicate `high` collapses to one event
    assert logs[0].claimAsset == high.address
    assert logs[0].balance == RETENTION
    assert logs[0].activeCount == 1

    after = _claim_state(pool, stab, [low, high])
    assert after["pairs"] == before["pairs"]
    assert after["totals"] == before["totals"]
    assert after["custody"] == before["custody"]
    assert pool.getClaimAssetState(stab, high) == CLAIM_ACTIVE
    assert pool.getClaimAssetState(stab, low) == CLAIM_DORMANT

    # suite-shortcut pause also gates (address impersonation, not Charlie)
    assert switchboard_charlie.pause(pool.address, False, sender=governance.address)
    with boa.reverts("contract not paused"):
        pool.activateClaimAssets(stab, [low], sender=alice)
    pool.pause(True, sender=switchboard_alpha.address)
    mock_price_source.setPrice(low, ACTIVATION * EIGHTEEN // RETENTION)
    pool.activateClaimAssets(stab, [low], sender=bob)  # caller need not hold shares
    assert pool.getClaimAssetState(stab, low) == CLAIM_ACTIVE
    pool.pause(False, sender=switchboard_alpha.address)


def test_g10_can_activate_helper_not_exported_and_source_semantics(
    stability_pool, alpha_token, alpha_token_whale, bravo_token,
    bravo_token_whale, alice, bob, teller, auction_house, mock_price_source,
    green_token, savings_green,
):
    """`canActivateClaimAsset` is NOT callable on the StabilityPool contract.
    The live-book predicate is an early return on the StabVault module source;
    removing that `totalBalances != 0` gate must fail this test.
    """
    pool = stability_pool
    with pytest.raises(Exception):
        pool.canActivateClaimAsset(alpha_token, bravo_token)

    source = (ROOT / "contracts/vaults/modules/StabVault.vy").read_text()
    start = source.index("def canActivateClaimAsset(")
    end = source.index("def _getClaimAssetActivationData(")
    body = source[start:end]
    assert "vaultData.totalBalances[_stabAsset] != 0" in body
    assert "return False, 0, 0" in body
    assert body.index("if vaultData.totalBalances[_stabAsset] != 0:") < body.index(
        "self._getStabAddys()"
    )
    assert "usdValue >= ACTIVATION_USD_THRESHOLD" in body
    assert "capacityRemaining != 0" in body
    assert "isPaused" in body  # comment only; execute still asserts pause
    return_block = body[body.index("return ("):]
    assert "vaultData.totalBalances[_stabAsset]" not in return_block

    # equivalent keeper preflight from exported getters
    stab = alpha_token
    _seed_stab(pool, stab, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN)
    _record_claim(pool, stab, bravo_token, bravo_token_whale, RETENTION, bob,
                  auction_house, green_token, savings_green)
    pair = pool.claimableBalances(stab, bravo_token)
    state = pool.getClaimAssetState(stab, bravo_token)
    active = pool.getNumActiveClaimAssets(stab)
    usd = mock_price_source.getPrice(bravo_token) * pair // EIGHTEEN
    assert (state == CLAIM_DORMANT and usd >= ACTIVATION
            and active < MAX_ACTIVE) is False  # usd is $0.05 here
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN)
    usd = mock_price_source.getPrice(bravo_token) * pair // EIGHTEEN
    # Live book: keeper preflight must also require an empty cohort.
    assert not (
        pool.totalBalances(stab) == 0
        and state == CLAIM_DORMANT
        and usd >= ACTIVATION
        and active < MAX_ACTIVE
    )


def test_g10_activate_capacity_last_slot_first_come_first_served(
    stability_pool, alpha_token, alpha_token_whale, governance, alice, bob,
    teller, auction_house, switchboard_alpha, mock_price_source, green_token,
    savings_green,
):
    """Never-skip #2 capacity ordering. 19 active rows, two eligible dormant
    candidates, one slot left. Caller order inside ONE batch decides which
    candidate takes it; the loser stays dormant even though it quoted high.
    Two separate txs: the second caller finds the slot gone. Once the slot
    is freed by a dust prune (an occupying row falls below $0.05), the loser
    can activate. `configuration / post-liquidation inventory-dependent`."""
    pool = stability_pool
    stab = alpha_token
    _seed_stab(pool, stab, alpha_token_whale, bob, teller, mock_price_source)

    # dormant candidates first (cap rejects new receipts once full)
    low = _deploy_claim_token(governance, alice, 31)
    high = _deploy_claim_token(governance, alice, 32)
    for tok in (low, high):
        mock_price_source.setPrice(tok, EIGHTEEN)
        _record_claim(pool, stab, tok, alice, RETENTION, bob, auction_house,
                      green_token, savings_green)
        assert pool.getClaimAssetState(stab, tok) == CLAIM_DORMANT

    # fill 19 dormant rows, then empty-cohort activate (live-share seating is gone)
    fillers = [_deploy_claim_token(governance, alice, 100 + i) for i in range(19)]
    for tok in fillers:
        mock_price_source.setPrice(tok, EIGHTEEN)
        _record_claim(pool, stab, tok, alice, ACTIVATION - 1, bob, auction_house,
                      green_token, savings_green)
    _exit_cohort(pool, stab, bob, teller)
    alpha_token.transfer(pool, EIGHTEEN, sender=alpha_token_whale)
    floor = _exact_floor(ACTIVATION - 1)
    for tok in fillers + [low, high]:
        mock_price_source.setPrice(tok, floor)
    _empty_activate(pool, stab, fillers[:15], switchboard_alpha, alice)
    pool.activateClaimAssets(stab, fillers[15:], sender=alice)
    pool.pause(False, sender=switchboard_alpha.address)
    assert pool.getNumActiveClaimAssets(stab) == 19

    # both candidates quote $0.20 (>= $0.10); order decides
    pool.pause(True, sender=switchboard_alpha.address)
    mock_price_source.setPrice(low, 2 * EIGHTEEN)
    mock_price_source.setPrice(high, 2 * EIGHTEEN)
    pool.activateClaimAssets(stab, [low, high], sender=alice)
    assert pool.getNumActiveClaimAssets(stab) == 20
    assert pool.getClaimAssetState(stab, low) == CLAIM_ACTIVE
    assert pool.getClaimAssetState(stab, high) == CLAIM_DORMANT  # lost the slot

    # the second caller in a separate tx finds the slot gone (silent skip)
    pool.activateClaimAssets(stab, [high], sender=bob)
    assert pool.getClaimAssetState(stab, high) == CLAIM_DORMANT

    # recovery: not "pause again" — prune frees the slot only after an
    # occupying row falls below retention, then activate takes it
    mock_price_source.setPrice(fillers[0], RETENTION * EIGHTEEN // (2 * EIGHTEEN) - 1)
    pool.pruneClaimableAssets(stab, [fillers[0]], sender=bob)  # works paused too
    assert pool.getNumActiveClaimAssets(stab) == 19
    pool.activateClaimAssets(stab, [high], sender=bob)
    assert pool.getClaimAssetState(stab, high) == CLAIM_ACTIVE
    pool.pause(False, sender=switchboard_alpha.address)
    assert pool.getNumActiveClaimAssets(stab) == 20


def test_g10_cross_cohort_custody_deficit_blocks_activate_on_other_stab(
    stability_pool, alpha_token, charlie_token, alpha_token_whale,
    charlie_token_whale, governance, alice, bob, teller, auction_house,
    switchboard_alpha, mock_price_source, green_token, savings_green,
):
    """Never-skip #2 cross-cohort custody: stab A (alpha) and stab B
    (charlie, 6 decimals — priced per-token so amounts carry 6dp) share one
    claim asset. A deficit anywhere in the shared claim's custody blocks
    activate on the OTHER cohort (custody compare is global
    totalClaimableBalances, not the requested pair). Prune/activate on A
    never touches B's pair or the global liability. Repaired-custody
    positive control included. Deficit is modeled by impersonating the pool
    (fixture/direct-state-only)."""
    pool = stability_pool
    stab_a, stab_b = alpha_token, charlie_token
    _seed_stab(pool, stab_a, alpha_token_whale, bob, teller, mock_price_source)
    _seed_stab(pool, stab_b, charlie_token_whale, bob, teller,
               mock_price_source, amount=100 * 10**6)

    claim = _deploy_claim_token(governance, alice, 41, 2 * EIGHTEEN)
    mock_price_source.setPrice(claim, EIGHTEEN)

    # active row on A; dormant row on B
    _record_claim(pool, stab_a, claim, alice, EIGHTEEN, bob, auction_house,
                  green_token, savings_green)
    _record_claim(pool, stab_b, claim, alice, RETENTION, bob, auction_house,
                  green_token, savings_green)
    assert pool.getClaimAssetState(stab_a, claim) == CLAIM_ACTIVE
    assert pool.getClaimAssetState(stab_b, claim) == CLAIM_DORMANT
    liability = EIGHTEEN + RETENTION
    assert pool.totalClaimableBalances(claim) == liability
    _exit_cohort(pool, stab_b, bob, teller)
    charlie_token.transfer(pool, 10**6, sender=charlie_token_whale)

    # custody deficit against the GLOBAL liability (1 wei)
    claim.transfer(alice, 1, sender=pool.address)

    pool.pause(True, sender=switchboard_alpha.address)
    mock_price_source.setPrice(claim, 2 * EIGHTEEN)  # B's pair quotes $0.10+
    with boa.reverts("claim custody deficit"):
        pool.activateClaimAssets(stab_b, [claim], sender=alice)

    # prune/activate on A do not touch B's pair or the global liability
    pool.pruneClaimableAssets(stab_a, [claim], sender=alice)  # active, $2 quote: stays
    assert pool.claimableBalances(stab_b, claim) == RETENTION
    assert pool.totalClaimableBalances(claim) == liability

    # repaired-custody positive control
    claim.transfer(pool, 1, sender=alice)
    pool.activateClaimAssets(stab_b, [claim], sender=alice)
    assert pool.getClaimAssetState(stab_b, claim) == CLAIM_ACTIVE
    assert pool.claimableBalances(stab_b, claim) == RETENTION
    assert pool.totalClaimableBalances(claim) == liability
    pool.pause(False, sender=switchboard_alpha.address)


def test_g10_can_accept_liquidation_asset_pause_and_capacity_boundaries(
    stability_pool, alpha_token, alpha_token_whale, governance, alice, bob,
    teller, auction_house, switchboard_alpha, mock_price_source, green_token,
    savings_green, vault_book, setGeneralConfig, setAssetConfig,
):
    """canAcceptLiquidationAsset is unconditionally False while paused; a
    new inactive claim asset is accepted while unpaused with liquidity and
    capacity, rejected at the 20-active cap, and accepted again after prune
    frees a slot (measured unpaused)."""
    pool = stability_pool
    stab = alpha_token
    _seed_stab(pool, stab, alpha_token_whale, bob, teller, mock_price_source)

    fresh = _deploy_claim_token(governance, alice, 51)
    mock_price_source.setPrice(fresh, EIGHTEEN)

    # healthy acceptance snapshot (unpaused)
    assert pool.canAcceptLiquidationAsset(stab, fresh)

    # paused: unconditionally False (a measurement taken now proves nothing
    # about capacity)
    pool.pause(True, sender=switchboard_alpha.address)
    assert not pool.canAcceptLiquidationAsset(stab, fresh)
    pool.pause(False, sender=switchboard_alpha.address)
    assert pool.canAcceptLiquidationAsset(stab, fresh)

    # fill to the cap, then a NEW inactive asset is refused; already-active
    # assets are still accepted (the cap only gates new rows)
    fillers = [_deploy_claim_token(governance, alice, 150 + i) for i in range(20)]
    for tok in fillers:
        mock_price_source.setPrice(tok, EIGHTEEN)
        _record_claim(pool, stab, tok, alice, EIGHTEEN, bob, auction_house,
                      green_token, savings_green)
    assert pool.getNumActiveClaimAssets(stab) == 20
    assert not pool.canAcceptLiquidationAsset(stab, fresh)
    assert pool.canAcceptLiquidationAsset(stab, fillers[0])

    # Free a slot by claiming an occupant to zero; live-share dust prune is a no-op.
    setGeneralConfig()
    setAssetConfig(fillers[0])
    from conf_utils import claim_from_stability_pool
    claim_from_stability_pool(
        teller, vault_book.getRegId(pool), stab, fillers[0], user=bob, sender=bob,
    )
    assert pool.getNumActiveClaimAssets(stab) == 19
    assert pool.canAcceptLiquidationAsset(stab, fresh)


def test_g10_prune_custody_deficit_adjacent_positive_control(
    g10_pool, stability_pool, alice, bob, teller, alpha_token,
    alpha_token_whale, mock_price_source,
):
    """Adjacent positive control for never-skip 1a: full custody, same dust
    quote. Live-share prune is a no-op; the claim row stays ACTIVE and in
    NAV. Share actions proceed because custody is intact, not because the
    row was delisted."""
    pool = stability_pool
    stab = g10_pool["stab"]
    claim = g10_pool["claim"]

    _record_claim(pool, stab, claim, g10_pool["claim_whale"], EIGHTEEN,
                  bob, g10_pool["auction_house"], g10_pool["green"],
                  g10_pool["sgreen"])
    mock_price_source.setPrice(claim, RETENTION - 1)
    pool.pruneClaimableAssets(stab, [claim], sender=alice)
    # Live-share full-custody prune is a no-op; NAV stays live.
    assert pool.getClaimAssetState(stab, claim) == CLAIM_ACTIVE

    claim_usd = (
        pool.claimableBalances(stab, claim)
        * mock_price_source.getPrice(claim)
        // EIGHTEEN
    )
    assert pool.getTotalValue(stab) == stab.balanceOf(pool) + claim_usd
    alpha_token.transfer(pool, EIGHTEEN, sender=alpha_token_whale)
    pool.depositTokensInVault(alice, stab, EIGHTEEN, sender=teller.address)
    withdrawn, _ = pool.withdrawTokensFromVault(
        bob, stab, EIGHTEEN, bob, sender=teller.address,
    )
    assert withdrawn == EIGHTEEN


def test_g10_prune_custody_deficit_activate_still_reverts_until_replenished(
    g10_pool, stability_pool, alice, bob, teller, switchboard_alpha,
    mock_price_source, alpha_token_whale,
):
    """Adjacent control after the failing case: activate reverts while the
    deficit remains; replenishing custody, then pause+activate restores the
    row (the sanctioned recovery path)."""
    pool = stability_pool
    stab = g10_pool["stab"]
    claim = g10_pool["claim"]

    _record_claim(pool, stab, claim, g10_pool["claim_whale"], ACTIVATION - 1,
                  bob, g10_pool["auction_house"], g10_pool["green"],
                  g10_pool["sgreen"])
    assert pool.getClaimAssetState(stab, claim) == CLAIM_DORMANT
    _exit_cohort(pool, stab, bob, teller)
    stab.transfer(pool, EIGHTEEN, sender=alpha_token_whale)
    mock_price_source.setPrice(claim, _exact_floor(ACTIVATION - 1))
    claim.transfer(alice, 1, sender=pool.address)
    pool.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("claim custody deficit"):
        pool.activateClaimAssets(stab, [claim], sender=alice)

    # replenish the missing wei, then the sanctioned path works
    claim.transfer(pool, 1, sender=alice)
    pool.activateClaimAssets(stab, [claim], sender=alice)
    pool.pause(False, sender=switchboard_alpha.address)
    assert pool.getClaimAssetState(stab, claim) == CLAIM_ACTIVE
    assert pool.getTotalValue(stab) > stab.balanceOf(pool)
