"""Group 10 proof tests: permissionless claim-list maintenance only.

These tests deliberately seed claim receipts through ``swapForLiquidatedCollateral``
with ``sender=auction_house.address``.  That impersonates AuctionHouse to exercise
the StabilityPool receipt/list boundary; it is not a Group 1 liquidation proof.
"""

import boa
import pytest

from conf_utils import claim_from_stability_pool, filter_logs
from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


ACTIVATION = 10**17
RETENTION = 5 * 10**16
LOW_PRUNE_PRICE = 4 * 10**15  # 10 tokens -> $0.04
ACTIVE = 2
DORMANT = 1
ABSENT = 0


def _seed_stability_asset(
    stability_pool,
    asset,
    whale,
    user,
    teller,
    mock_price_source,
    amount=100 * EIGHTEEN_DECIMALS,
):
    mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)
    asset.transfer(stability_pool, amount, sender=whale)
    assert stability_pool.depositTokensInVault(
        user,
        asset,
        amount,
        sender=teller.address,
    ) == amount


def _record_claim(
    stability_pool,
    stab_asset,
    claim_asset,
    claim_whale,
    amount,
    recipient,
    auction_house,
    green_token,
    savings_green,
):
    claim_asset.transfer(stability_pool, amount, sender=claim_whale)
    return stability_pool.swapForLiquidatedCollateral(
        stab_asset,
        1,
        claim_asset,
        amount,
        recipient,
        green_token,
        savings_green,
        sender=auction_house.address,
    )


def _deposit_and_delta_shares(
    stability_pool,
    asset,
    whale,
    user,
    teller,
    amount,
):
    shares_before = stability_pool.userBalances(user, asset)
    asset.transfer(stability_pool, amount, sender=whale)
    assert stability_pool.depositTokensInVault(
        user,
        asset,
        amount,
        sender=teller.address,
    ) == amount
    return stability_pool.userBalances(user, asset) - shares_before


def _deploy_claim_token(governance, holder, suffix, amount):
    token = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        f"Group 10 Claim {suffix}",
        f"G10{suffix}",
        18,
        0,
        name=f"group10_claim_{suffix}",
    )
    token.mint(holder, amount, sender=governance.address)
    return token


def _exit_cohort(stability_pool, stab, user, teller):
    stability_pool.withdrawTokensFromVault(
        user, stab, MAX_UINT256, user, sender=teller.address,
    )
    assert stability_pool.totalBalances(stab) == 0


def _empty_activate(stability_pool, stab, claims, switchboard, caller):
    stability_pool.pause(True, sender=switchboard.address)
    for start in range(0, len(claims), 15):
        stability_pool.activateClaimAssets(stab, claims[start:start + 15], sender=caller)


def _claim_list_snapshot(pool, stab_asset, claim_assets):
    return {
        "stab_custody": stab_asset.balanceOf(pool.address),
        "num": pool.numClaimableAssets(stab_asset),
        "active": pool.getNumActiveClaimAssets(stab_asset),
        "slots": tuple(pool.claimableAssets(stab_asset, i) for i in range(1, 5)),
        "pairs": tuple(
            (
                pool.claimableBalances(stab_asset, asset),
                pool.indexOfClaimableAsset(stab_asset, asset),
                pool.getClaimAssetState(stab_asset, asset),
                pool.totalClaimableBalances(asset),
                asset.balanceOf(pool.address),
            )
            for asset in claim_assets
        ),
    }


def _make_active_deficit(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    claim_amount = 10 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        claim_amount,
        bob,
        auction_house,
        green_token,
        savings_green,
    )
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == ACTIVE

    # Address impersonation models custody loss.  It is not an ordinary EOA
    # route: an EOA can later prune, but cannot normally create this shortfall.
    assert bravo_token.transfer(alice, 1, sender=stability_pool.address)
    assert bravo_token.balanceOf(stability_pool.address) == claim_amount - 1
    assert stability_pool.totalClaimableBalances(bravo_token) == claim_amount
    mock_price_source.setPrice(bravo_token, LOW_PRUNE_PRICE)
    return claim_amount


def test_g10_prune_custody_deficit_characterization_and_recovery(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    """Characterize #1a: live-share dust prune is a no-op, so a short row
    stays on the iterable and NAV stays fail-closed until custody is repaired.
    """
    claim_amount = _make_active_deficit(
        stability_pool,
        alpha_token,
        bravo_token,
        alpha_token_whale,
        bravo_token_whale,
        bob,
        alice,
        teller,
        auction_house,
        mock_price_source,
        green_token,
        savings_green,
    )

    with boa.reverts("claim custody deficit"):
        stability_pool.getTotalValue(alpha_token)
    with boa.env.anchor():
        alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
        with boa.reverts("claim custody deficit"):
            stability_pool.depositTokensInVault(
                alice,
                alpha_token,
                EIGHTEEN_DECIMALS,
                sender=teller.address,
            )
    with boa.reverts("claim custody deficit"):
        stability_pool.withdrawTokensFromVault(
            bob,
            alpha_token,
            EIGHTEEN_DECIMALS,
            bob,
            sender=teller.address,
        )

    before = _claim_list_snapshot(stability_pool, alpha_token, [bravo_token])
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=alice)
    logs = filter_logs(stability_pool, "ClaimAssetDeactivated")
    after = _claim_list_snapshot(stability_pool, alpha_token, [bravo_token])

    assert before["pairs"][0][0] == after["pairs"][0][0] == claim_amount
    assert before["pairs"][0][3:] == after["pairs"][0][3:] == (
        claim_amount,
        claim_amount - 1,
    )
    assert after["stab_custody"] == before["stab_custody"]
    assert after["num"] == 2
    assert after["active"] == 1
    assert after["slots"][0] == bravo_token.address
    assert after["pairs"][0][1:3] == (
        stability_pool.indexOfClaimableAsset(alpha_token, bravo_token),
        ACTIVE,
    )
    assert logs == []

    # Live-share dust prune is a no-op, so the short row stays on NAV.
    with boa.reverts("claim custody deficit"):
        stability_pool.getTotalValue(alpha_token)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    with boa.reverts("claim custody deficit"):
        stability_pool.depositTokensInVault(
            alice,
            alpha_token,
            EIGHTEEN_DECIMALS,
            sender=teller.address,
        )

    # Live-share activate is a no-op (the short row stayed registered).
    # Replenishing custody is the repair; getTotalValue must recover without
    # a membership change.
    stability_pool.pause(True, sender=switchboard_alpha.address)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=alice)
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == ACTIVE
    bravo_token.transfer(stability_pool, 1, sender=bravo_token_whale)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert stability_pool.getTotalValue(alpha_token) > alpha_token.balanceOf(
        stability_pool.address
    )


def test_g10_prune_custody_deficit_does_not_reenable_nav_safety_property(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    _make_active_deficit(
        stability_pool,
        alpha_token,
        bravo_token,
        alpha_token_whale,
        bravo_token_whale,
        bob,
        alice,
        teller,
        auction_house,
        mock_price_source,
        green_token,
        savings_green,
    )
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=alice)
    with boa.reverts("claim custody deficit"):
        stability_pool.getTotalValue(alpha_token)


def test_g10_prune_full_custody_dust_control_keeps_nav_live(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    claim_amount = 10 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        claim_amount,
        bob,
        auction_house,
        green_token,
        savings_green,
    )
    mock_price_source.setPrice(bravo_token, LOW_PRUNE_PRICE)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=alice)
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == ACTIVE
    assert bravo_token.balanceOf(stability_pool.address) == claim_amount
    assert stability_pool.totalClaimableBalances(bravo_token) == claim_amount
    claim_usd = (
        claim_amount * mock_price_source.getPrice(bravo_token) // EIGHTEEN_DECIMALS
    )
    assert stability_pool.getTotalValue(alpha_token) == (
        alpha_token.balanceOf(stability_pool.address) + claim_usd
    )


@pytest.mark.parametrize("paused", (False, True), ids=("unpaused", "paused"))
def test_g10_prune_identity_swap_pop_and_balance_layers(
    paused,
    stability_pool,
    alpha_token,
    alpha_token_whale,
    governance,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    claims = [
        _deploy_claim_token(governance, alice, 100 + i, ACTIVATION)
        for i in range(3)
    ]
    for token in claims:
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool,
            alpha_token,
            token,
            alice,
            ACTIVATION - 1,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    floor = (ACTIVATION * EIGHTEEN_DECIMALS + ACTIVATION - 2) // (ACTIVATION - 1)
    for token in claims:
        mock_price_source.setPrice(token, floor)
    _empty_activate(stability_pool, alpha_token, claims, switchboard_alpha, alice)
    stability_pool.pause(False, sender=switchboard_alpha.address)

    first, middle, last = claims
    assert _claim_list_snapshot(stability_pool, alpha_token, claims)["slots"][:3] == (
        first.address,
        middle.address,
        last.address,
    )
    probe = _deploy_claim_token(governance, alice, 199, 0)
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, probe)

    # Empty, unknown, and duplicate-already-dormant entries are harmless.
    baseline = _claim_list_snapshot(stability_pool, alpha_token, claims)
    stability_pool.pruneClaimableAssets(alpha_token, [], sender=alice)
    stability_pool.pruneClaimableAssets(alpha_token, [ZERO_ADDRESS], sender=alice)
    assert _claim_list_snapshot(stability_pool, alpha_token, claims) == baseline

    mock_price_source.setPrice(first, LOW_PRUNE_PRICE)
    mock_price_source.setPrice(middle, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(last, LOW_PRUNE_PRICE)
    balances_before = tuple(token.balanceOf(stability_pool.address) for token in claims)
    liabilities_before = tuple(stability_pool.totalClaimableBalances(token) for token in claims)
    if paused:
        stability_pool.pause(True, sender=switchboard_alpha.address)

    # After the first removal `last` occupies slot 1.  The later address-based
    # lookup must still remove it, leaving only the original middle row.
    stability_pool.pruneClaimableAssets(
        alpha_token,
        [first, last, first, ZERO_ADDRESS],
        sender=alice,
    )
    logs = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 1
    assert stability_pool.numClaimableAssets(alpha_token) == 2
    assert stability_pool.claimableAssets(alpha_token, 1) == middle.address
    assert stability_pool.claimableAssets(alpha_token, 2) == ZERO_ADDRESS
    assert stability_pool.getClaimAssetState(alpha_token, first) == DORMANT
    assert stability_pool.getClaimAssetState(alpha_token, middle) == ACTIVE
    assert stability_pool.getClaimAssetState(alpha_token, last) == DORMANT
    assert tuple(token.balanceOf(stability_pool.address) for token in claims) == balances_before
    assert tuple(stability_pool.totalClaimableBalances(token) for token in claims) == liabilities_before
    assert [(log.claimAsset, log.reason, log.activeCount) for log in logs] == [
        (first.address, 2, 2),
        (last.address, 2, 1),
    ]
    stability_pool.pruneClaimableAssets(alpha_token, [first, first], sender=alice)
    assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []
    if paused:
        stability_pool.pause(False, sender=switchboard_alpha.address)
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, probe)


def test_g10_dormant_pruned_claim_still_delivers_for_funded_holder(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
):
    setGeneralConfig()
    setAssetConfig(bravo_token)
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        ACTIVATION - 1,
        bob,
        auction_house,
        green_token,
        savings_green,
    )
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == DORMANT
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    before = bravo_token.balanceOf(bob)
    claim_from_stability_pool(
        teller,
        vault_book.getRegId(stability_pool),
        alpha_token,
        bravo_token,
        sender=bob,
    )
    assert bravo_token.balanceOf(bob) - before == ACTIVATION - 1
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
    assert stability_pool.totalClaimableBalances(bravo_token) == 0


def test_g10_full_ordinary_claim_cannot_leave_a_zero_balance_active_row(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
):
    """An ordinary full claim removes the active row before maintenance runs."""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool,
        alpha_token,
        bravo_token,
        bravo_token_whale,
        ACTIVATION,
        bob,
        auction_house,
        green_token,
        savings_green,
    )
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == ACTIVE
    assert stability_pool.numClaimableAssets(alpha_token) == 2

    recipient_before = bravo_token.balanceOf(bob)
    claim_from_stability_pool(
        teller,
        vault_book.getRegId(stability_pool),
        alpha_token,
        bravo_token,
        sender=bob,
    )
    assert bravo_token.balanceOf(bob) - recipient_before == ACTIVATION
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
    assert stability_pool.totalClaimableBalances(bravo_token) == 0
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == ABSENT
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 0
    assert stability_pool.numClaimableAssets(alpha_token) == 1
    assert stability_pool.claimableAssets(alpha_token, 1) == ZERO_ADDRESS

    # Thus prune has no ordinary zero-balance active row to act on.
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=alice)
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == ABSENT


def _build_capacity_case(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    governance,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    suffix,
):
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    candidates = [
        _deploy_claim_token(governance, alice, suffix + 1, ACTIVATION - 1),
        _deploy_claim_token(governance, alice, suffix + 2, ACTIVATION - 1),
    ]
    for candidate in candidates:
        mock_price_source.setPrice(candidate, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool,
            alpha_token,
            candidate,
            alice,
            ACTIVATION - 1,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
        assert stability_pool.getClaimAssetState(alpha_token, candidate) == DORMANT

    active_tokens = [
        _deploy_claim_token(governance, alice, suffix + 10 + i, ACTIVATION)
        for i in range(19)
    ]
    for token in active_tokens:
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool,
            alpha_token,
            token,
            alice,
            ACTIVATION - 1,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0
    return candidates, active_tokens


@pytest.mark.parametrize("first_index", (0, 1), ids=("first-low", "first-high"))
def test_g10_activate_capacity_order_charlie_pause_and_recovery(
    first_index,
    stability_pool,
    alpha_token,
    alpha_token_whale,
    governance,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_charlie,
    switchboard_alpha,
):
    """The first eligible address consumes the twentieth active-list slot."""
    candidates, actives = _build_capacity_case(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        governance,
        bob,
        alice,
        teller,
        auction_house,
        mock_price_source,
        green_token,
        savings_green,
        200 + first_index * 100,
    )
    winner = candidates[first_index]
    loser = candidates[1 - first_index]
    probe = _deploy_claim_token(governance, alice, 299 + first_index, 0)
    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    floor = (ACTIVATION * EIGHTEEN_DECIMALS + ACTIVATION - 2) // (ACTIVATION - 1)
    for token in actives + candidates:
        mock_price_source.setPrice(token, floor)
    _empty_activate(stability_pool, alpha_token, actives, switchboard_alpha, alice)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, winner)
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, loser)

    unpaused_snapshot = _claim_list_snapshot(stability_pool, alpha_token, candidates)
    with boa.reverts("contract not paused"):
        stability_pool.activateClaimAssets(alpha_token, [winner], sender=alice)
    assert _claim_list_snapshot(stability_pool, alpha_token, candidates) == unpaused_snapshot

    # This is the production pause route: Charlie, invoked by the governor,
    # immediately calls the vault.  No lite signer is enabled in this fixture.
    assert switchboard_charlie.pause(
        stability_pool.address,
        True,
        sender=governance.address,
    )
    pause_logs = filter_logs(switchboard_charlie, "PauseExecuted")
    assert len(pause_logs) == 1
    assert pause_logs[0].contractAddr == stability_pool.address
    assert pause_logs[0].shouldPause
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, winner)

    for candidate in candidates:
        # Each pile is honestly below $0.10 but is eligible under the value
        # observed by maintenance in this paused call.
        mock_price_source.setPrice(candidate, 2 * EIGHTEEN_DECIMALS)
    stability_pool.activateClaimAssets(alpha_token, [winner, loser], sender=alice)
    logs = filter_logs(stability_pool, "ClaimAssetActivated")
    after_activate = _claim_list_snapshot(stability_pool, alpha_token, candidates)
    assert after_activate["stab_custody"] == unpaused_snapshot["stab_custody"]
    assert tuple(pair[0] for pair in after_activate["pairs"]) == tuple(
        pair[0] for pair in unpaused_snapshot["pairs"]
    )
    assert tuple(pair[3:] for pair in after_activate["pairs"]) == tuple(
        pair[3:] for pair in unpaused_snapshot["pairs"]
    )
    assert stability_pool.getClaimAssetState(alpha_token, winner) == ACTIVE
    assert stability_pool.getClaimAssetState(alpha_token, loser) == DORMANT
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 20
    assert [(log.claimAsset, log.balance, log.activeCount) for log in logs] == [
        (winner.address, ACTIVATION - 1, 20)
    ]

    # A retained row cannot be evicted by scoped maintenance merely to make
    # room: at its high quote, permissionless prune is a no-op.
    stability_pool.pruneClaimableAssets(alpha_token, [winner], sender=bob)
    prune_logs = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert stability_pool.getClaimAssetState(alpha_token, winner) == ACTIVE
    assert prune_logs == []

    # A later keeper has no priority and finds a silent capacity skip.
    stability_pool.activateClaimAssets(alpha_token, [loser], sender=bob)
    noop_logs = filter_logs(stability_pool, "ClaimAssetActivated")
    assert stability_pool.getClaimAssetState(alpha_token, loser) == DORMANT
    assert noop_logs == []
    assert switchboard_charlie.pause(
        stability_pool.address,
        False,
        sender=governance.address,
    )
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, loser)

    # Scoped maintenance can free a slot only when the occupying row becomes
    # dust; it cannot arbitrarily evict a retained row.
    mock_price_source.setPrice(winner, LOW_PRUNE_PRICE)
    stability_pool.pruneClaimableAssets(alpha_token, [winner], sender=alice)
    assert stability_pool.getClaimAssetState(alpha_token, winner) == DORMANT
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 19
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, loser)

    assert switchboard_charlie.pause(
        stability_pool.address,
        True,
        sender=governance.address,
    )
    mock_price_source.setPrice(loser, 2 * EIGHTEEN_DECIMALS)
    stability_pool.activateClaimAssets(alpha_token, [loser], sender=bob)
    assert stability_pool.getClaimAssetState(alpha_token, loser) == ACTIVE
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 20
    assert switchboard_charlie.pause(
        stability_pool.address,
        False,
        sender=governance.address,
    )
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, probe)


def test_g10_activate_global_custody_check_is_cross_cohort_and_atomic(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_charlie,
):
    """A deficit in cohort B blocks a paused activation in cohort A."""
    _seed_stability_asset(
        stability_pool,
        alpha_token,
        alpha_token_whale,
        bob,
        teller,
        mock_price_source,
    )
    _seed_stability_asset(
        stability_pool,
        bravo_token,
        bravo_token_whale,
        alice,
        teller,
        mock_price_source,
    )
    common = _deploy_claim_token(governance, alice, 400, 2 * ACTIVATION)
    mock_price_source.setPrice(common, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool,
        alpha_token,
        common,
        alice,
        ACTIVATION - 1,
        bob,
        auction_house,
        green_token,
        savings_green,
    )
    _record_claim(
        stability_pool,
        bravo_token,
        common,
        alice,
        ACTIVATION,
        bob,
        auction_house,
        green_token,
        savings_green,
    )
    assert stability_pool.getClaimAssetState(alpha_token, common) == DORMANT
    assert stability_pool.getClaimAssetState(bravo_token, common) == ACTIVE
    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    total_before = stability_pool.totalClaimableBalances(common)
    bravo_pair_before = stability_pool.claimableBalances(bravo_token, common)
    assert common.transfer(alice, 1, sender=stability_pool.address)
    assert common.balanceOf(stability_pool.address) == total_before - 1

    assert switchboard_charlie.pause(
        stability_pool.address,
        True,
        sender=governance.address,
    )
    with boa.reverts("claim custody deficit"):
        stability_pool.activateClaimAssets(alpha_token, [common], sender=alice)
    assert stability_pool.getClaimAssetState(alpha_token, common) == DORMANT
    assert stability_pool.claimableBalances(bravo_token, common) == bravo_pair_before
    assert stability_pool.totalClaimableBalances(common) == total_before

    # Prune sees the dormant A row and cannot mutate B's pair or the global
    # liability.  Replenishment is the required positive control.
    stability_pool.pruneClaimableAssets(alpha_token, [common], sender=alice)
    assert stability_pool.claimableBalances(bravo_token, common) == bravo_pair_before
    assert stability_pool.totalClaimableBalances(common) == total_before
    common.transfer(stability_pool, 1, sender=alice)
    mock_price_source.setPrice(common, 2 * EIGHTEEN_DECIMALS)
    stability_pool.activateClaimAssets(alpha_token, [common], sender=alice)
    assert stability_pool.getClaimAssetState(alpha_token, common) == ACTIVE
    assert stability_pool.claimableBalances(bravo_token, common) == bravo_pair_before
    assert stability_pool.totalClaimableBalances(common) == total_before

    # Once the global shortfall is repaired, an ordinary EOA can prune A's
    # active dust row, but that still cannot mutate B's pair or the aggregate.
    assert switchboard_charlie.pause(
        stability_pool.address,
        False,
        sender=governance.address,
    )
    mock_price_source.setPrice(common, LOW_PRUNE_PRICE)
    stability_pool.pruneClaimableAssets(alpha_token, [common], sender=alice)
    assert stability_pool.getClaimAssetState(alpha_token, common) == DORMANT
    assert stability_pool.claimableBalances(bravo_token, common) == bravo_pair_before
    assert stability_pool.totalClaimableBalances(common) == total_before


def _run_low_quote_prune_composition(
    should_prune,
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
    withdraw_attacker=False,
):
    with boa.env.anchor():
        _seed_stability_asset(
            stability_pool,
            alpha_token,
            alpha_token_whale,
            bob,
            teller,
            mock_price_source,
        )
        claim_amount = 10 * EIGHTEEN_DECIMALS
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool,
            alpha_token,
            bravo_token,
            bravo_token_whale,
            claim_amount,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
        assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == ACTIVE
        if should_prune:
            mock_price_source.setPrice(bravo_token, LOW_PRUNE_PRICE)
            stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=alice)
            assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == ACTIVE
            mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        else:
            assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == ACTIVE

        attacker_shares = _deposit_and_delta_shares(
            stability_pool,
            alpha_token,
            alpha_token_whale,
            alice,
            teller,
            100 * EIGHTEEN_DECIMALS,
        )
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == ACTIVE
        result = {
            "attacker_shares": attacker_shares,
            "attacker_value": stability_pool.getTotalUserValue(alice, alpha_token),
            "prior_holder_value": stability_pool.getTotalUserValue(bob, alpha_token),
            "claim_custody": bravo_token.balanceOf(stability_pool.address),
            "claim_liability": stability_pool.totalClaimableBalances(bravo_token),
        }
        if withdraw_attacker:
            recipient_before = alpha_token.balanceOf(alice)
            withdrawn, depleted = stability_pool.withdrawTokensFromVault(
                alice,
                alpha_token,
                MAX_UINT256,
                alice,
                sender=teller.address,
            )
            result["attacker_withdrawal"] = withdrawn
            result["attacker_delivery"] = alpha_token.balanceOf(alice) - recipient_before
            result["attacker_depleted"] = depleted
            result["remaining_stab_custody"] = alpha_token.balanceOf(stability_pool.address)
            result["claim_custody_after_withdrawal"] = bravo_token.balanceOf(
                stability_pool.address
            )
            result["claim_liability_after_withdrawal"] = stability_pool.totalClaimableBalances(
                bravo_token
            )
        return result


def test_g10_low_quote_prune_composition_characterization(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    control = _run_low_quote_prune_composition(
        False,
        stability_pool,
        alpha_token,
        bravo_token,
        alpha_token_whale,
        bravo_token_whale,
        bob,
        alice,
        teller,
        auction_house,
        mock_price_source,
        green_token,
        savings_green,
        switchboard_alpha,
    )
    pruned = _run_low_quote_prune_composition(
        True,
        stability_pool,
        alpha_token,
        bravo_token,
        alpha_token_whale,
        bravo_token_whale,
        bob,
        alice,
        teller,
        auction_house,
        mock_price_source,
        green_token,
        savings_green,
        switchboard_alpha,
    )
    assert pruned["claim_custody"] == control["claim_custody"] == 10 * EIGHTEEN_DECIMALS
    assert pruned["claim_liability"] == control["claim_liability"] == 10 * EIGHTEEN_DECIMALS
    assert abs(pruned["attacker_shares"] - control["attacker_shares"]) <= 1
    assert abs(pruned["attacker_value"] - control["attacker_value"]) <= 1
    assert abs(control["prior_holder_value"] - pruned["prior_holder_value"]) <= 1


def test_g10_low_quote_prune_withdrawal_delta_is_realizable(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    """A thin normal Teller withdrawal realizes the list-timing value delta."""
    control = _run_low_quote_prune_composition(
        False,
        stability_pool,
        alpha_token,
        bravo_token,
        alpha_token_whale,
        bravo_token_whale,
        bob,
        alice,
        teller,
        auction_house,
        mock_price_source,
        green_token,
        savings_green,
        switchboard_alpha,
        withdraw_attacker=True,
    )
    pruned = _run_low_quote_prune_composition(
        True,
        stability_pool,
        alpha_token,
        bravo_token,
        alpha_token_whale,
        bravo_token_whale,
        bob,
        alice,
        teller,
        auction_house,
        mock_price_source,
        green_token,
        savings_green,
        switchboard_alpha,
        withdraw_attacker=True,
    )
    assert control["attacker_depleted"] and pruned["attacker_depleted"]
    assert control["attacker_delivery"] == control["attacker_withdrawal"]
    assert pruned["attacker_delivery"] == pruned["attacker_withdrawal"]
    assert abs(pruned["attacker_withdrawal"] - control["attacker_withdrawal"]) <= 1
    assert abs(control["remaining_stab_custody"] - pruned["remaining_stab_custody"]) <= 1
    assert (
        control["claim_custody_after_withdrawal"]
        == pruned["claim_custody_after_withdrawal"]
        == 10 * EIGHTEEN_DECIMALS
    )
    assert (
        control["claim_liability_after_withdrawal"]
        == pruned["claim_liability_after_withdrawal"]
        == 10 * EIGHTEEN_DECIMALS
    )


def test_g10_low_quote_prune_does_not_transfer_prior_claim_value_to_new_depositor(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    control = _run_low_quote_prune_composition(
        False,
        stability_pool,
        alpha_token,
        bravo_token,
        alpha_token_whale,
        bravo_token_whale,
        bob,
        alice,
        teller,
        auction_house,
        mock_price_source,
        green_token,
        savings_green,
        switchboard_alpha,
    )
    pruned = _run_low_quote_prune_composition(
        True,
        stability_pool,
        alpha_token,
        bravo_token,
        alpha_token_whale,
        bravo_token_whale,
        bob,
        alice,
        teller,
        auction_house,
        mock_price_source,
        green_token,
        savings_green,
        switchboard_alpha,
    )
    assert pruned["attacker_value"] <= control["attacker_value"]


def _run_high_quote_activate_withdrawal(
    should_activate,
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    with boa.env.anchor():
        _seed_stability_asset(
            stability_pool,
            alpha_token,
            alpha_token_whale,
            bob,
            teller,
            mock_price_source,
        )
        claim_amount = 10 * EIGHTEEN_DECIMALS
        mock_price_source.setPrice(bravo_token, LOW_PRUNE_PRICE)
        _record_claim(
            stability_pool,
            alpha_token,
            bravo_token,
            bravo_token_whale,
            claim_amount,
            bob,
            auction_house,
            green_token,
            savings_green,
        )
        assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == DORMANT
        _deposit_and_delta_shares(
            stability_pool,
            alpha_token,
            alpha_token_whale,
            alice,
            teller,
            100 * EIGHTEEN_DECIMALS,
        )
        if should_activate:
            stability_pool.pause(True, sender=switchboard_alpha.address)
            mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
            stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=alice)
            stability_pool.pause(False, sender=switchboard_alpha.address)
            assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == DORMANT
        mock_price_source.setPrice(bravo_token, LOW_PRUNE_PRICE)
        recipient_before = alpha_token.balanceOf(alice)
        withdrawn, depleted = stability_pool.withdrawTokensFromVault(
            alice,
            alpha_token,
            MAX_UINT256,
            alice,
            sender=teller.address,
        )
        assert depleted
        assert alpha_token.balanceOf(alice) - recipient_before == withdrawn
        return withdrawn


def test_g10_high_quote_activate_then_honest_withdrawal_characterization(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    control_withdrawn = _run_high_quote_activate_withdrawal(
        False,
        stability_pool,
        alpha_token,
        bravo_token,
        alpha_token_whale,
        bravo_token_whale,
        bob,
        alice,
        teller,
        auction_house,
        mock_price_source,
        green_token,
        savings_green,
        switchboard_alpha,
    )
    activated_withdrawn = _run_high_quote_activate_withdrawal(
        True,
        stability_pool,
        alpha_token,
        bravo_token,
        alpha_token_whale,
        bravo_token_whale,
        bob,
        alice,
        teller,
        auction_house,
        mock_price_source,
        green_token,
        savings_green,
        switchboard_alpha,
    )
    assert control_withdrawn == 100 * EIGHTEEN_DECIMALS
    assert abs(activated_withdrawn - control_withdrawn) <= 1
