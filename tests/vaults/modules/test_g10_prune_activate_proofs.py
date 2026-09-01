"""Group 10 proofs: pruneClaimableAssets / activateClaimAssets list membership.

Seed claimable with swapForLiquidatedCollateral(sender=auction_house.address):
AuctionHouse impersonation, not the Group 1 swap path.
"""

import json
from pathlib import Path

import boa
import pytest
from eth_utils import keccak

from conf_utils import (
    claim_from_stability_pool,
    filter_logs,
    redeem_from_stability_pool,
    sync_deployed_token,
)

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


ACTIVATION_THRESHOLD = 10 * 10**16
RETENTION_THRESHOLD = 5 * 10**16
LIVE_RESIDUAL_DIVISOR = 10**10
CLAIM_ASSET_ABSENT = 0
CLAIM_ASSET_DORMANT = 1
CLAIM_ASSET_ACTIVE = 2
DEACTIVATION_ZERO = 1
DEACTIVATION_DUST = 2
MAX_ACTIVE_CLAIM_ASSETS = 20
MAX_CLAIM_ASSET_MAINTENANCE = 15
ROOT = Path(__file__).resolve().parents[3]


def _exact_activation_price(pair_amount):
    return (ACTIVATION_THRESHOLD * EIGHTEEN_DECIMALS + pair_amount - 1) // pair_amount


def _seed_stab(stability_pool, asset, whale, user, teller, mock_price_source, amount=100 * EIGHTEEN_DECIMALS):
    mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)
    asset.transfer(stability_pool, amount, sender=whale)
    assert stability_pool.depositTokensInVault(user, asset, amount, sender=teller.address) == amount


def _record_claim(
    stability_pool,
    stab_asset,
    claim_asset,
    claim_whale,
    claim_amount,
    recipient,
    auction_house,
    green_token,
    savings_green,
    stab_amount=1,
):
    claim_asset.transfer(stability_pool, claim_amount, sender=claim_whale)
    return stability_pool.swapForLiquidatedCollateral(
        stab_asset,
        stab_amount,
        claim_asset,
        claim_amount,
        recipient,
        green_token,
        savings_green,
        sender=auction_house.address,
    )


def _deploy_claim_token(governance, holder, index, amount=EIGHTEEN_DECIMALS):
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
    sync_deployed_token(token)
    return token


def _list_snapshot(pool, stab, claims):
    slots = [pool.claimableAssets(stab, i) for i in range(1, MAX_ACTIVE_CLAIM_ASSETS + 1)]
    rows = []
    for claim in claims:
        rows.append(
            (
                claim.address,
                pool.claimableBalances(stab, claim),
                pool.totalClaimableBalances(claim),
                claim.balanceOf(pool.address),
                pool.indexOfClaimableAsset(stab, claim),
                pool.getClaimAssetState(stab, claim),
            )
        )
    return {
        "stab_custody": stab.balanceOf(pool.address),
        "num": pool.numClaimableAssets(stab),
        "active": pool.getNumActiveClaimAssets(stab),
        "slots": slots,
        "rows": rows,
    }


def _assert_balances_unchanged(before, after):
    assert after["stab_custody"] == before["stab_custody"]
    assert [row[1] for row in after["rows"]] == [row[1] for row in before["rows"]]
    assert [row[2] for row in after["rows"]] == [row[2] for row in before["rows"]]
    assert [row[3] for row in after["rows"]] == [row[3] for row in before["rows"]]


def _claimable_balance_slot(claim_asset, stab_asset):
    inner = keccak(
        (9).to_bytes(32, "big") + int(stab_asset.address, 16).to_bytes(32, "big")
    )
    return int.from_bytes(
        keccak(inner + int(claim_asset.address, 16).to_bytes(32, "big")),
        "big",
    )


def _dust_logs(contract, claim_asset):
    return [
        log
        for log in filter_logs(contract, "ClaimAssetDeactivated")
        if log.claimAsset == claim_asset.address
    ]


def _exit_cohort(stability_pool, stab, user, teller):
    stability_pool.withdrawTokensFromVault(
        user, stab, MAX_UINT256, user, sender=teller.address,
    )
    assert stability_pool.totalBalances(stab) == 0


def _activate_empty_cohort(stability_pool, stab, claims, switchboard, caller):
    """Seat dormant pairs while totalBalances == 0. Leaves the vault paused."""
    assert stability_pool.totalBalances(stab) == 0
    stability_pool.pause(True, sender=switchboard.address)
    for start in range(0, len(claims), MAX_CLAIM_ASSET_MAINTENANCE):
        stability_pool.activateClaimAssets(
            stab, claims[start:start + MAX_CLAIM_ASSET_MAINTENANCE], sender=caller,
        )


def _seed_dormant_then_empty_activate(
    stability_pool,
    stab,
    stab_whale,
    user,
    teller,
    mock_price_source,
    claim_rows,
    auction_house,
    green_token,
    savings_green,
    switchboard,
    activator,
    donate_stab=EIGHTEEN_DECIMALS,
):
    """G5 empty-cohort sequence: below-floor receipts, last exit, appreciate, activate.

    claim_rows: iterable of (token, whale, dormant_amount).
    """
    _seed_stab(stability_pool, stab, stab_whale, user, teller, mock_price_source)
    tokens = []
    for token, whale, amount in claim_rows:
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool, stab, token, whale, amount,
            user, auction_house, green_token, savings_green,
        )
        assert stability_pool.getClaimAssetState(stab, token) == CLAIM_ASSET_DORMANT
        tokens.append(token)
    _exit_cohort(stability_pool, stab, user, teller)
    if donate_stab:
        stab.transfer(stability_pool, donate_stab, sender=stab_whale)
    for token, _, amount in claim_rows:
        mock_price_source.setPrice(token, _exact_activation_price(amount))
    _activate_empty_cohort(stability_pool, stab, tokens, switchboard, activator)
    for token in tokens:
        assert stability_pool.getClaimAssetState(stab, token) == CLAIM_ASSET_ACTIVE
    return tokens


def test_g10_can_activate_is_not_exported_on_stability_pool(stability_pool):
    abi_names = {
        entry["name"]
        for entry in json.loads((ROOT / "scripts/abis/StabilityPool.json").read_text())
        if "name" in entry
    }
    assert "canActivateClaimAsset" not in abi_names
    assert "pruneClaimableAssets" in abi_names
    assert "activateClaimAssets" in abi_names
    assert "getClaimAssetState" in abi_names
    assert "canAcceptLiquidationAsset" in abi_names
    assert "claimManyFromStabilityPool" in abi_names
    assert "redeemManyFromStabilityPool" in abi_names
    assert "claimFromStabilityPool" not in abi_names
    assert "redeemFromStabilityPool" not in abi_names
    with pytest.raises(AttributeError):
        stability_pool.canActivateClaimAsset(ZERO_ADDRESS, ZERO_ADDRESS)


def test_g10_prune_identity_unpaused_and_paused(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
    governance,
):
    bravo_amt = ACTIVATION_THRESHOLD - 1
    charlie_amt = 50_000  # 6dp; $0.05 at $1, dormant
    _seed_dormant_then_empty_activate(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source,
        (
            (bravo_token, bravo_token_whale, bravo_amt),
            (charlie_token, charlie_token_whale, charlie_amt),
        ),
        auction_house, green_token, savings_green, switchboard_alpha, sally,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 3 * EIGHTEEN_DECIMALS)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    unknown = _deploy_claim_token(governance, alice, 900, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(unknown, EIGHTEEN_DECIMALS)

    before = _list_snapshot(stability_pool, alpha_token, [bravo_token, charlie_token, unknown])
    nav_before = stability_pool.getTotalValue(alpha_token)
    assert not stability_pool.isPaused()
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, unknown)

    # Empty / unknown / already-dormant / caller without shares: non-mutating.
    stability_pool.pruneClaimableAssets(alpha_token, [], sender=sally)
    stability_pool.pruneClaimableAssets(alpha_token, [unknown], sender=sally)
    stability_pool.pruneClaimableAssets(ZERO_ADDRESS, [bravo_token], sender=sally)
    noop_logs = filter_logs(stability_pool, "ClaimAssetDeactivated")
    _assert_balances_unchanged(before, _list_snapshot(stability_pool, alpha_token, [bravo_token, charlie_token, unknown]))
    assert noop_logs == []
    assert stability_pool.getTotalValue(alpha_token) == nav_before

    # High-positive quote retains. Independently priced.
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 3 * EIGHTEEN_DECIMALS)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token, charlie_token], sender=sally)
    assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.getClaimAssetState(alpha_token, charlie_token) == CLAIM_ASSET_ACTIVE

    # Exact $0.05 stays; band below $0.10 stays; below $0.05 dust-prunes (reason 2).
    retention_px = (RETENTION_THRESHOLD * EIGHTEEN_DECIMALS + bravo_amt - 1) // bravo_amt
    band_px = ((RETENTION_THRESHOLD + 10**16) * EIGHTEEN_DECIMALS + bravo_amt - 1) // bravo_amt
    dust_px = (RETENTION_THRESHOLD - 1) * EIGHTEEN_DECIMALS // bravo_amt
    mock_price_source.setPrice(bravo_token, retention_px)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=sally)
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    mock_price_source.setPrice(bravo_token, band_px)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=sally)
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    mock_price_source.setPrice(bravo_token, dust_px)
    pair_before = stability_pool.claimableBalances(alpha_token, bravo_token)
    total_before = stability_pool.totalClaimableBalances(bravo_token)
    custody_before = bravo_token.balanceOf(stability_pool.address)
    stab_before = alpha_token.balanceOf(stability_pool.address)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=sally)
    logs = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert len(logs) == 1
    assert logs[0].claimAsset == bravo_token.address
    assert logs[0].reason == DEACTIVATION_DUST
    assert logs[0].balance == pair_before
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 0
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == pair_before
    assert stability_pool.totalClaimableBalances(bravo_token) == total_before
    assert bravo_token.balanceOf(stability_pool.address) == custody_before
    assert alpha_token.balanceOf(stability_pool.address) == stab_before

    # Already-dormant skip; duplicates in one call emit once.
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token, bravo_token], sender=sally)
    assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []

    # Prune still works while paused (Switchboard spoof).
    stability_pool.pause(True, sender=switchboard_alpha.address)
    mock_price_source.setPrice(charlie_token, 4 * 10**15)
    stability_pool.pruneClaimableAssets(alpha_token, [charlie_token], sender=sally)
    paused_logs = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert len(paused_logs) == 1
    assert paused_logs[0].reason == DEACTIVATION_DUST
    assert stability_pool.getClaimAssetState(alpha_token, charlie_token) == CLAIM_ASSET_DORMANT
    stability_pool.pause(False, sender=switchboard_alpha.address)


def test_g10_prune_source_zero_retains_and_continues_batch(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    _seed_dormant_then_empty_activate(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source,
        (
            (bravo_token, bravo_token_whale, ACTIVATION_THRESHOLD - 1),
            (charlie_token, charlie_token_whale, 50_000),
        ),
        auction_house, green_token, savings_green, switchboard_alpha, sally,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 3 * EIGHTEEN_DECIMALS)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    bravo_index = stability_pool.indexOfClaimableAsset(alpha_token, bravo_token)
    mock_price_source.setPrice(bravo_token, 0)
    mock_price_source.setShouldRevert(bravo_token, True)
    mock_price_source.setPrice(charlie_token, 4 * 10**17)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token, charlie_token], sender=sally)
    logs = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert len(logs) == 1
    assert logs[0].claimAsset == charlie_token.address
    assert logs[0].reason == DEACTIVATION_DUST
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == bravo_index
    mock_price_source.setShouldRevert(bravo_token, False)


def test_g10_prune_swap_and_pop_middle_last_only_and_moved_tail(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    governance,
    bob,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    tokens = [_deploy_claim_token(governance, bob, 10 + i, ACTIVATION_THRESHOLD) for i in range(3)]
    _seed_dormant_then_empty_activate(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source,
        tuple((token, bob, ACTIVATION_THRESHOLD - 1) for token in tokens),
        auction_house, green_token, savings_green, switchboard_alpha, sally,
    )
    for token in tokens:
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    a, b, c = tokens
    assert [stability_pool.claimableAssets(alpha_token, i) for i in (1, 2, 3)] == [a.address, b.address, c.address]
    assert stability_pool.numClaimableAssets(alpha_token) == 4
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 3

    # After A is removed, C has moved into A's index. Later request must still remove C.
    for token in (a, c):
        mock_price_source.setPrice(token, 4 * 10**17)
    mock_price_source.setPrice(b, EIGHTEEN_DECIMALS)
    stability_pool.pruneClaimableAssets(alpha_token, [a, c], sender=sally)
    logs = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert [log.claimAsset for log in logs] == [a.address, c.address]
    assert [log.reason for log in logs] == [DEACTIVATION_DUST, DEACTIVATION_DUST]
    assert stability_pool.getClaimAssetState(alpha_token, a) == CLAIM_ASSET_DORMANT
    assert stability_pool.getClaimAssetState(alpha_token, c) == CLAIM_ASSET_DORMANT
    assert stability_pool.getClaimAssetState(alpha_token, b) == CLAIM_ASSET_ACTIVE
    assert stability_pool.claimableAssets(alpha_token, 1) == b.address
    assert stability_pool.claimableAssets(alpha_token, 2) == ZERO_ADDRESS
    assert stability_pool.indexOfClaimableAsset(alpha_token, b) == 1
    assert stability_pool.numClaimableAssets(alpha_token) == 2
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 1

    # Last / only-row: empty list is num==1, active count 0, slot zeroed.
    mock_price_source.setPrice(b, 4 * 10**17)
    stability_pool.pruneClaimableAssets(alpha_token, [b], sender=sally)
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0
    assert stability_pool.numClaimableAssets(alpha_token) == 1
    assert stability_pool.claimableAssets(alpha_token, 1) == ZERO_ADDRESS
    assert stability_pool.getTotalValue(alpha_token) == alpha_token.balanceOf(stability_pool.address)


def test_g10_prune_zero_balance_active_is_legacy_direct_storage(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        ACTIVATION_THRESHOLD, bob, auction_house, green_token, savings_green,
    )
    # Ordinary reduce already auto-removes at zero. Force the leftover row.
    boa.env.set_storage(
        stability_pool.address,
        _claimable_balance_slot(bravo_token, alpha_token),
        0,
    )
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) != 0
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=sally)
    logs = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert len(logs) == 1
    assert logs[0].reason == DEACTIVATION_ZERO
    assert logs[0].balance == 0
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ABSENT
    assert stability_pool.numClaimableAssets(alpha_token) == 1


def test_g10_prune_two_stabs_share_one_claim_asset(
    stability_pool,
    alpha_token,
    charlie_token,
    bravo_token,
    alpha_token_whale,
    charlie_token_whale,
    bravo_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    _seed_stab(
        stability_pool, charlie_token, charlie_token_whale, bob, teller, mock_price_source,
        100 * 10**6,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool, charlie_token, bravo_token, bravo_token_whale,
        ACTIVATION_THRESHOLD, bob, auction_house, green_token, savings_green,
    )
    _seed_dormant_then_empty_activate(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source,
        ((bravo_token, bravo_token_whale, ACTIVATION_THRESHOLD - 1),),
        auction_house, green_token, savings_green, switchboard_alpha, sally,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    b_pair = stability_pool.claimableBalances(charlie_token, bravo_token)
    global_liability = stability_pool.totalClaimableBalances(bravo_token)
    mock_price_source.setPrice(bravo_token, 4 * 10**17)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=sally)
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    assert stability_pool.getClaimAssetState(charlie_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.claimableBalances(charlie_token, bravo_token) == b_pair
    assert stability_pool.totalClaimableBalances(bravo_token) == global_liability


def test_g10_dormant_receipt_thin_claim_still_delivers(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
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
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    amount = ACTIVATION_THRESHOLD - 1
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        amount, bob, auction_house, green_token, savings_green,
    )
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(stability_pool)
    before = bravo_token.balanceOf(bob)
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
    assert bravo_token.balanceOf(bob) - before == amount
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0


def test_g10_1a_dust_prune_must_not_reenable_nav_with_custody_deficit(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    """Safety property: live-share dust prune must not unfreeze NAV while
    custody is short. The short row stays ACTIVE, so getTotalValue still
    reverts. Fixture uses address impersonation (`transfer` from the pool).
    """
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    amount = 10 * EIGHTEEN_DECIMALS
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        amount, bob, auction_house, green_token, savings_green,
    )
    bravo_token.transfer(alice, 1, sender=stability_pool.address)
    assert bravo_token.balanceOf(stability_pool.address) < stability_pool.totalClaimableBalances(bravo_token)
    with boa.reverts("claim custody deficit"):
        stability_pool.getTotalValue(alpha_token)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    with boa.reverts("claim custody deficit"):
        stability_pool.depositTokensInVault(alice, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address)
    with boa.reverts("claim custody deficit"):
        stability_pool.withdrawTokensFromVault(bob, alpha_token, EIGHTEEN_DECIMALS, bob, sender=teller.address)

    mock_price_source.setPrice(bravo_token, 4 * 10**15)
    pair = stability_pool.claimableBalances(alpha_token, bravo_token)
    liability = stability_pool.totalClaimableBalances(bravo_token)
    custody = bravo_token.balanceOf(stability_pool.address)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=sally)
    # Live book: dust prune is a no-op, so the short row stays on NAV.
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == pair
    assert stability_pool.totalClaimableBalances(bravo_token) == liability
    assert bravo_token.balanceOf(stability_pool.address) == custody
    assert custody < liability

    with boa.reverts("claim custody deficit"):
        stability_pool.getTotalValue(alpha_token)


def test_g10_1a_full_custody_dust_prune_allows_nav(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        10 * EIGHTEEN_DECIMALS, bob, auction_house, green_token, savings_green,
    )
    mock_price_source.setPrice(bravo_token, 4 * 10**15)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=sally)
    # Live-share full-custody dust prune is a no-op; the pair stays on NAV.
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.getTotalValue(alpha_token) == (
        alpha_token.balanceOf(stability_pool.address)
        + stability_pool.claimableBalances(alpha_token, bravo_token) * 4 * 10**15 // EIGHTEEN_DECIMALS
    )
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    assert stability_pool.depositTokensInVault(
        alice, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address,
    ) == EIGHTEEN_DECIMALS
    withdrawn, _ = stability_pool.withdrawTokensFromVault(
        alice, alpha_token, EIGHTEEN_DECIMALS, alice, sender=teller.address,
    )
    assert withdrawn > 0


def test_g10_1a_activate_reverts_while_deficit_then_replenish_restores(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    amount = ACTIVATION_THRESHOLD - 1
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        amount, bob, auction_house, green_token, savings_green,
    )
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    mock_price_source.setPrice(bravo_token, _exact_activation_price(amount))
    bravo_token.transfer(alice, 1, sender=stability_pool.address)
    stability_pool.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("claim custody deficit"):
        stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=sally)
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    bravo_token.transfer(stability_pool, 1, sender=alice)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=sally)
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert stability_pool.getTotalValue(alpha_token) > alpha_token.balanceOf(stability_pool.address)


def test_g10_1b_low_quote_prune_then_deposit_cannot_capture_omitted_value(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    """Invariant: prune timing must not hand pre-existing claim value to a later depositor."""
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    pile = 50 * EIGHTEEN_DECIMALS
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        pile, bob, auction_house, green_token, savings_green,
    )

    def _alice_withdraw_after_restore(*, prune_first):
        if prune_first:
            mock_price_source.setPrice(bravo_token, 9 * 10**14)
            stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=sally)
            assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        alpha_token.transfer(stability_pool, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
        stability_pool.depositTokensInVault(
            alice, alpha_token, 100 * EIGHTEEN_DECIMALS, sender=teller.address,
        )
        if prune_first:
            stability_pool.pause(True, sender=switchboard_alpha.address)
            stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=sally)
            stability_pool.pause(False, sender=switchboard_alpha.address)
        alice_stab_before = alpha_token.balanceOf(alice)
        withdrawn, _ = stability_pool.withdrawTokensFromVault(
            alice, alpha_token, MAX_UINT256, alice, sender=teller.address,
        )
        return withdrawn, alpha_token.balanceOf(alice) - alice_stab_before

    with boa.env.anchor():
        attack_withdrawn, _ = _alice_withdraw_after_restore(prune_first=True)
    with boa.env.anchor():
        control_withdrawn, _ = _alice_withdraw_after_restore(prune_first=False)

    # Live-share prune is a no-op, so prune-first and control mints match.
    assert attack_withdrawn <= control_withdrawn + 1, (
        f"low-quote prune timing transferred value: attack={attack_withdrawn} "
        f"control={control_withdrawn}"
    )


def test_g10_1b_high_quote_activate_then_withdraw_vs_control(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    dust = 4 * 10**16
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        dust, bob, auction_house, green_token, savings_green,
    )
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT

    def _bob_partial_withdraw(*, activate_with_high_quote):
        if activate_with_high_quote:
            mock_price_source.setPrice(bravo_token, 3 * EIGHTEEN_DECIMALS)
            stability_pool.pause(True, sender=switchboard_alpha.address)
            stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=sally)
            assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
            stability_pool.pause(False, sender=switchboard_alpha.address)
        alpha_token.transfer(stability_pool, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
        stability_pool.depositTokensInVault(
            alice, alpha_token, 100 * EIGHTEEN_DECIMALS, sender=teller.address,
        )
        bob_before = alpha_token.balanceOf(bob)
        withdrawn, _ = stability_pool.withdrawTokensFromVault(
            bob, alpha_token, 50 * EIGHTEEN_DECIMALS, bob, sender=teller.address,
        )
        return withdrawn, alpha_token.balanceOf(bob) - bob_before, stability_pool.userBalances(bob, alpha_token)

    with boa.env.anchor():
        attack = _bob_partial_withdraw(activate_with_high_quote=True)
    with boa.env.anchor():
        control = _bob_partial_withdraw(activate_with_high_quote=False)

    assert attack[0] == control[0] == 50 * EIGHTEEN_DECIMALS
    # High quote must not let Bob burn fewer shares for the same stab out.
    assert attack[2] <= control[2] + 1, (
        f"high-quote activate left Bob more residual shares: attack={attack} control={control}"
    )


def test_g10_activate_identity_charlie_pause_and_thresholds(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
    switchboard_charlie,
    governance,
    mission_control,
):
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        ACTIVATION_THRESHOLD - 1, bob, auction_house, green_token, savings_green,
    )
    # 50_000 six-decimal units at $1 is $0.05 — dormant. High quote can push it over $0.10.
    _record_claim(
        stability_pool, alpha_token, charlie_token, charlie_token_whale,
        50_000, bob, auction_house, green_token, savings_green,
    )
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    assert stability_pool.getClaimAssetState(alpha_token, charlie_token) == CLAIM_ASSET_DORMANT

    before = _list_snapshot(stability_pool, alpha_token, [bravo_token, charlie_token])
    with boa.reverts("contract not paused"):
        stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=sally)
    _assert_balances_unchanged(before, _list_snapshot(stability_pool, alpha_token, [bravo_token, charlie_token]))

    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # Production pause: Charlie governor, immediate. Lite enabled separately.
    assert switchboard_charlie.pause(stability_pool.address, True, sender=governance.address)
    assert stability_pool.isPaused()
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, bravo_token)

    # Empty / unknown / zero / already-active / pair-zero skip.
    stability_pool.activateClaimAssets(alpha_token, [], sender=sally)
    stability_pool.activateClaimAssets(alpha_token, [ZERO_ADDRESS], sender=sally)
    # Pair is $0.10 minus 1 wei at a $1 quote — just below the floor.
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=sally)
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    mock_price_source.setPrice(bravo_token, 0)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=sally)
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT

    # Exact $0.10 activates; duplicates emit once.
    exact_floor_price = (
        ACTIVATION_THRESHOLD * EIGHTEEN_DECIMALS + ACTIVATION_THRESHOLD - 2
    ) // (ACTIVATION_THRESHOLD - 1)
    mock_price_source.setPrice(bravo_token, exact_floor_price)
    pair = stability_pool.claimableBalances(alpha_token, bravo_token)
    custody = bravo_token.balanceOf(stability_pool.address)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token, bravo_token], sender=sally)
    logs = filter_logs(stability_pool, "ClaimAssetActivated")
    assert len(logs) == 1
    assert logs[0].claimAsset == bravo_token.address
    assert logs[0].balance == pair
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == pair
    assert bravo_token.balanceOf(stability_pool.address) == custody
    stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=sally)
    assert filter_logs(stability_pool, "ClaimAssetActivated") == []

    # High quote of a truly sub-threshold pile does activate if the helper sees ≥ $0.10.
    mock_price_source.setPrice(charlie_token, 2 * EIGHTEEN_DECIMALS)
    stability_pool.activateClaimAssets(alpha_token, [charlie_token], sender=sally)
    assert stability_pool.getClaimAssetState(alpha_token, charlie_token) == CLAIM_ASSET_ACTIVE

    switchboard_charlie.pause(stability_pool.address, False, sender=governance.address)
    assert not stability_pool.isPaused()
    nav = stability_pool.getTotalValue(alpha_token)
    assert nav > alpha_token.balanceOf(stability_pool.address)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    assert stability_pool.depositTokensInVault(
        alice, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address,
    ) == EIGHTEEN_DECIMALS
    withdrawn, _ = stability_pool.withdrawTokensFromVault(
        alice, alpha_token, EIGHTEEN_DECIMALS, alice, sender=teller.address,
    )
    assert withdrawn > 0

    # Lite pause is governance-enableable, not launch (DefaultsRobinhood.liteSigners is []).
    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_alpha.address)
    assert switchboard_charlie.pause(stability_pool.address, True, sender=sally)
    assert stability_pool.isPaused()
    switchboard_charlie.pause(stability_pool.address, False, sender=governance.address)


def test_g10_activate_can_accept_measured_only_while_unpaused(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    governance,
    bob,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        ACTIVATION_THRESHOLD - 1, bob, auction_house, green_token, savings_green,
    )
    candidate = _deploy_claim_token(governance, bob, 80, ACTIVATION_THRESHOLD)
    mock_price_source.setPrice(candidate, EIGHTEEN_DECIMALS)
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, candidate)
    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    stability_pool.pause(True, sender=switchboard_alpha.address)
    exact_floor_price = (
        ACTIVATION_THRESHOLD * EIGHTEEN_DECIMALS + ACTIVATION_THRESHOLD - 2
    ) // (ACTIVATION_THRESHOLD - 1)
    mock_price_source.setPrice(bravo_token, exact_floor_price)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=sally)
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, candidate)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, candidate)
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE


def test_g10_activate_capacity_order_and_persistence(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    governance,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    _seed_stab(
        stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source,
        100 * EIGHTEEN_DECIMALS + MAX_ACTIVE_CLAIM_ASSETS,
    )
    # Seed every candidate below the floor so last-exit can empty the cohort.
    low = _deploy_claim_token(governance, alice, 200, ACTIVATION_THRESHOLD - 1)
    high = _deploy_claim_token(governance, alice, 201, ACTIVATION_THRESHOLD - 1)
    extra = _deploy_claim_token(governance, alice, 202, ACTIVATION_THRESHOLD)
    mock_price_source.setPrice(low, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(high, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(extra, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool, alpha_token, low, alice, ACTIVATION_THRESHOLD - 1,
        bob, auction_house, green_token, savings_green,
    )
    _record_claim(
        stability_pool, alpha_token, high, alice, ACTIVATION_THRESHOLD - 1,
        bob, auction_house, green_token, savings_green,
    )
    actives = []
    for index in range(19):
        token = _deploy_claim_token(governance, alice, 210 + index, ACTIVATION_THRESHOLD)
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool, alpha_token, token, alice, ACTIVATION_THRESHOLD - 1,
            bob, auction_house, green_token, savings_green,
        )
        actives.append(token)
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0
    assert stability_pool.getClaimAssetState(alpha_token, low) == CLAIM_ASSET_DORMANT
    assert stability_pool.getClaimAssetState(alpha_token, high) == CLAIM_ASSET_DORMANT
    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(
        stability_pool, EIGHTEEN_DECIMALS + MAX_ACTIVE_CLAIM_ASSETS, sender=alpha_token_whale,
    )
    floor = _exact_activation_price(ACTIVATION_THRESHOLD - 1)
    for token in actives + [low, high]:
        mock_price_source.setPrice(token, floor)
    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.activateClaimAssets(alpha_token, actives[:15], sender=sally)
    stability_pool.activateClaimAssets(alpha_token, actives[15:], sender=sally)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 19
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, extra)

    with boa.env.anchor():
        stability_pool.pause(True, sender=switchboard_alpha.address)
        stability_pool.activateClaimAssets(alpha_token, [low, high], sender=sally)
        assert stability_pool.getClaimAssetState(alpha_token, low) == CLAIM_ASSET_ACTIVE
        assert stability_pool.getClaimAssetState(alpha_token, high) == CLAIM_ASSET_DORMANT
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 20
        stability_pool.pause(False, sender=switchboard_alpha.address)
        assert not stability_pool.canAcceptLiquidationAsset(alpha_token, extra)

    with boa.env.anchor():
        stability_pool.pause(True, sender=switchboard_alpha.address)
        stability_pool.activateClaimAssets(alpha_token, [high, low], sender=alice)
        assert stability_pool.getClaimAssetState(alpha_token, high) == CLAIM_ASSET_ACTIVE
        assert stability_pool.getClaimAssetState(alpha_token, low) == CLAIM_ASSET_DORMANT
        stability_pool.pause(False, sender=switchboard_alpha.address)

    # Two txs: second caller finds the slot gone.
    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.activateClaimAssets(alpha_token, [low], sender=sally)
    stability_pool.activateClaimAssets(alpha_token, [high], sender=alice)
    assert stability_pool.getClaimAssetState(alpha_token, low) == CLAIM_ASSET_ACTIVE
    assert stability_pool.getClaimAssetState(alpha_token, high) == CLAIM_ASSET_DORMANT
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 20

    # All twenty stay ≥ RETENTION: scoped maintenance has no arbitrary eviction.
    for token in actives + [low]:
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    stability_pool.pruneClaimableAssets(alpha_token, actives[:15], sender=sally)
    assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 20
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, extra)

    # Free a slot by dust-pruning the occupying row, then activate the loser.
    mock_price_source.setPrice(low, 4 * 10**17)
    stability_pool.pruneClaimableAssets(alpha_token, [low], sender=sally)
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 19
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, extra)
    mock_price_source.setPrice(high, floor)
    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.activateClaimAssets(alpha_token, [high], sender=alice)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert stability_pool.getClaimAssetState(alpha_token, high) == CLAIM_ASSET_ACTIVE
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, extra)


def test_g10_activate_cross_cohort_custody_and_green_claim(
    stability_pool,
    alpha_token,
    charlie_token,
    bravo_token,
    alpha_token_whale,
    charlie_token_whale,
    bravo_token_whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
    whale,
):
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    _seed_stab(
        stability_pool, charlie_token, charlie_token_whale, bob, teller, mock_price_source,
        100 * 10**6,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        ACTIVATION_THRESHOLD - 1, bob, auction_house, green_token, savings_green,
    )
    _record_claim(
        stability_pool, charlie_token, bravo_token, bravo_token_whale,
        ACTIVATION_THRESHOLD, bob, auction_house, green_token, savings_green,
    )
    _record_claim(
        stability_pool, alpha_token, green_token, whale, ACTIVATION_THRESHOLD - 1,
        bob, auction_house, green_token, savings_green,
    )
    assert stability_pool.getClaimAssetState(alpha_token, green_token) == CLAIM_ASSET_DORMANT
    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    b_pair = stability_pool.claimableBalances(charlie_token, bravo_token)
    global_liability = stability_pool.totalClaimableBalances(bravo_token)
    bravo_token.transfer(alice, 1, sender=stability_pool.address)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    stability_pool.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("claim custody deficit"):
        stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=sally)
    assert stability_pool.claimableBalances(charlie_token, bravo_token) == b_pair
    assert stability_pool.totalClaimableBalances(bravo_token) == global_liability
    bravo_token.transfer(stability_pool, 1, sender=alice)
    mock_price_source.setPrice(bravo_token, _exact_activation_price(ACTIVATION_THRESHOLD - 1))
    stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=sally)
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.claimableBalances(charlie_token, bravo_token) == b_pair
    assert stability_pool.totalClaimableBalances(bravo_token) == global_liability

    # GREEN is the 1:1 branch (amount == USD). Just below $0.10 stays dormant.
    stability_pool.activateClaimAssets(alpha_token, [green_token], sender=sally)
    assert stability_pool.getClaimAssetState(alpha_token, green_token) == CLAIM_ASSET_DORMANT
    stability_pool.pause(False, sender=switchboard_alpha.address)
    green_token.transfer(stability_pool, 1, sender=whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, 1, green_token, 1, bob, green_token, savings_green,
        sender=auction_house.address,
    )
    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.activateClaimAssets(alpha_token, [green_token], sender=sally)
    assert stability_pool.getClaimAssetState(alpha_token, green_token) == CLAIM_ASSET_ACTIVE
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert stability_pool.getTotalValue(alpha_token) > 0


def test_g10_1a_empty_full_custody_dust_prune_delists(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    amount = ACTIVATION_THRESHOLD - 1
    _seed_dormant_then_empty_activate(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source,
        ((bravo_token, bravo_token_whale, amount),),
        auction_house, green_token, savings_green, switchboard_alpha, sally,
        donate_stab=0,
    )
    mock_price_source.setPrice(bravo_token, 4 * 10**17)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=sally)
    logs = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert len(logs) == 1
    assert logs[0].reason == DEACTIVATION_DUST
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    assert stability_pool.getTotalValue(alpha_token) == alpha_token.balanceOf(stability_pool.address)
    assert stability_pool.getTotalValue(alpha_token) == 0


def test_g10_1a_empty_custody_deficit_dust_prune_keeps_active(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    amount = ACTIVATION_THRESHOLD - 1
    _seed_dormant_then_empty_activate(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source,
        ((bravo_token, bravo_token_whale, amount),),
        auction_house, green_token, savings_green, switchboard_alpha, sally,
    )
    stability_pool.pause(False, sender=switchboard_alpha.address)
    bravo_token.transfer(alice, 1, sender=stability_pool.address)
    mock_price_source.setPrice(bravo_token, 4 * 10**17)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=sally)
    assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    with boa.reverts("claim custody deficit"):
        stability_pool.getTotalValue(alpha_token)
    with boa.reverts("claim custody deficit"):
        stability_pool.depositTokensInVault(
            alice, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address,
        )


def test_g10_1a_empty_batch_short_row_skips_safe_row_continues(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    governance,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    a = _deploy_claim_token(governance, alice, 501, ACTIVATION_THRESHOLD)
    b = _deploy_claim_token(governance, alice, 502, ACTIVATION_THRESHOLD)
    _seed_dormant_then_empty_activate(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source,
        (
            (a, alice, ACTIVATION_THRESHOLD - 1),
            (b, alice, ACTIVATION_THRESHOLD - 1),
        ),
        auction_house, green_token, savings_green, switchboard_alpha, sally,
    )
    stability_pool.pause(False, sender=switchboard_alpha.address)
    a.transfer(alice, 1, sender=stability_pool.address)
    mock_price_source.setPrice(a, 4 * 10**17)
    mock_price_source.setPrice(b, 4 * 10**17)
    stability_pool.pruneClaimableAssets(alpha_token, [a, b], sender=sally)
    logs = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert len(logs) == 1
    assert logs[0].claimAsset == b.address
    assert logs[0].reason == DEACTIVATION_DUST
    assert stability_pool.getClaimAssetState(alpha_token, a) == CLAIM_ASSET_ACTIVE
    assert stability_pool.getClaimAssetState(alpha_token, b) == CLAIM_ASSET_DORMANT


def test_g10_1a_empty_cross_cohort_global_deficit_blocks_prune(
    stability_pool,
    alpha_token,
    charlie_token,
    bravo_token,
    alpha_token_whale,
    charlie_token_whale,
    bravo_token_whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    _seed_stab(
        stability_pool, charlie_token, charlie_token_whale, bob, teller, mock_price_source,
        100 * 10**6,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(
        stability_pool, charlie_token, bravo_token, bravo_token_whale,
        ACTIVATION_THRESHOLD, bob, auction_house, green_token, savings_green,
    )
    _seed_dormant_then_empty_activate(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source,
        ((bravo_token, bravo_token_whale, ACTIVATION_THRESHOLD - 1),),
        auction_house, green_token, savings_green, switchboard_alpha, sally,
    )
    stability_pool.pause(False, sender=switchboard_alpha.address)
    # One wei short against the shared global liability.
    bravo_token.transfer(alice, 1, sender=stability_pool.address)
    mock_price_source.setPrice(bravo_token, 4 * 10**17)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=sally)
    assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.getClaimAssetState(charlie_token, bravo_token) == CLAIM_ASSET_ACTIVE


def test_g10_live_cap_blocks_21st_and_empty_dust_prune_frees_slot(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    governance,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    switchboard_alpha,
):
    extra = _deploy_claim_token(governance, alice, 600, ACTIVATION_THRESHOLD)
    mock_price_source.setPrice(extra, EIGHTEEN_DECIMALS)

    def _live_arm():
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
        occupants = []
        for index in range(MAX_ACTIVE_CLAIM_ASSETS):
            token = _deploy_claim_token(governance, alice, 610 + index, ACTIVATION_THRESHOLD)
            mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
            _record_claim(
                stability_pool, alpha_token, token, alice, ACTIVATION_THRESHOLD,
                bob, auction_house, green_token, savings_green,
            )
            occupants.append(token)
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 20
        assert not stability_pool.canAcceptLiquidationAsset(alpha_token, extra)
        with boa.reverts("max active claim assets"):
            _record_claim(
                stability_pool, alpha_token, extra, alice, ACTIVATION_THRESHOLD,
                bob, auction_house, green_token, savings_green,
            )
        mock_price_source.setPrice(occupants[0], 4 * 10**17)
        stability_pool.pruneClaimableAssets(alpha_token, [occupants[0]], sender=sally)
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 20
        assert not stability_pool.canAcceptLiquidationAsset(alpha_token, extra)

    def _empty_arm():
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
        occupants = []
        for index in range(MAX_ACTIVE_CLAIM_ASSETS):
            token = _deploy_claim_token(governance, alice, 640 + index, ACTIVATION_THRESHOLD)
            mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
            _record_claim(
                stability_pool, alpha_token, token, alice, ACTIVATION_THRESHOLD - 1,
                bob, auction_house, green_token, savings_green,
            )
            occupants.append(token)
        _exit_cohort(stability_pool, alpha_token, bob, teller)
        alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
        floor = _exact_activation_price(ACTIVATION_THRESHOLD - 1)
        for token in occupants:
            mock_price_source.setPrice(token, floor)
        stability_pool.pause(True, sender=switchboard_alpha.address)
        stability_pool.activateClaimAssets(alpha_token, occupants[:15], sender=sally)
        stability_pool.activateClaimAssets(alpha_token, occupants[15:], sender=sally)
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 20
        mock_price_source.setPrice(occupants[0], 4 * 10**17)
        stability_pool.pruneClaimableAssets(alpha_token, [occupants[0]], sender=sally)
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 19
        stability_pool.pause(False, sender=switchboard_alpha.address)
        assert _record_claim(
            stability_pool, alpha_token, extra, alice, ACTIVATION_THRESHOLD,
            bob, auction_house, green_token, savings_green,
        ) == 1
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 20

    with boa.env.anchor():
        _live_arm()
    with boa.env.anchor():
        _empty_arm()


def test_g10_partial_claim_wrong_low_quote_keeps_row_active(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
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
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    pile = 10 * EIGHTEEN_DECIMALS
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        pile, bob, auction_house, green_token, savings_green,
    )
    mock_price_source.setPrice(bravo_token, 4 * 10**15)
    vault_id = vault_book.getRegId(stability_pool)
    sliver_usd = 10**16
    claim_from_stability_pool(
        teller, vault_id, alpha_token, bravo_token, sliver_usd, sender=bob,
    )
    residual = stability_pool.claimableBalances(alpha_token, bravo_token)
    assert residual != 0
    assert residual < pile
    assert stability_pool.totalBalances(alpha_token) != 0
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE


def test_g10_partial_redeem_wrong_low_quote_keeps_row_active(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    whale,
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
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    pile = 10 * EIGHTEEN_DECIMALS
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        pile, bob, auction_house, green_token, savings_green,
    )
    mock_price_source.setPrice(bravo_token, 4 * 10**15)
    vault_id = vault_book.getRegId(stability_pool)
    payment = 10**16
    green_token.transfer(bob, payment, sender=whale)
    green_token.approve(teller, payment, sender=bob)
    redeem_from_stability_pool(teller, vault_id, bravo_token, payment, sender=bob)
    residual = stability_pool.claimableBalances(alpha_token, bravo_token)
    assert residual != 0
    assert residual < pile
    assert stability_pool.totalBalances(alpha_token) != 0
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE


def test_g10_partial_claim_then_deposit_does_not_capture(
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
    switchboard_alpha,
):
    """Row-B economic isolation: the low quote is live during the claim.

    Attack claims at a wrong-low quote so implied remaining USD is dust
    (old `_claimFromStabilityPool` would unlist). Control claims the same
    token sliver at a non-unlisting quote (remaining USD above $0.05).
    A pre-claim stab donation on the control arm (no shares minted) equalizes
    valueToShares. After the claim, the attack arm receives the same
    25-stab top-up so pool stab custody matches. Alice then deposits,
    both arms run pause+activate at the restored honest price (old code
    would reseat the omitted row into NAV; the patch is a live-share
    no-op), and withdrawals match within one wei. No prune, no storage
    poke.
    """
    setGeneralConfig()
    setAssetConfig(bravo_token)

    claim_tokens = 10**16
    pile = 11 * EIGHTEEN_DECIMALS + claim_tokens
    attack_price = 4 * 10**15
    control_price = 5 * 10**15
    seed = 100 * EIGHTEEN_DECIMALS
    control_donate = 25 * EIGHTEEN_DECIMALS
    target_tokens = 9999999999950000

    def _claimed_log():
        logs = filter_logs(teller, "AssetClaimedInStabilityPool")
        if not logs:
            logs = filter_logs(stability_pool, "AssetClaimedInStabilityPool")
        assert len(logs) == 1
        return logs[0]

    def _setup(price, donate=0):
        _seed_stab(
            stability_pool, alpha_token, alpha_token_whale, bob, teller,
            mock_price_source, amount=seed,
        )
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(
            stability_pool, alpha_token, bravo_token, bravo_token_whale,
            pile, bob, auction_house, green_token, savings_green,
        )
        if donate:
            alpha_token.transfer(stability_pool, donate, sender=alpha_token_whale)
        mock_price_source.setPrice(bravo_token, price)

    def _claim_bounds(price):
        user_shares = stability_pool.userBalances(bob, alpha_token)
        total_shares = stability_pool.totalBalances(alpha_token)
        total_value = stability_pool.getTotalValue(alpha_token)
        max_usd = user_shares * (total_value + 1) // (total_shares + 10**8)
        max_amount = max_usd * EIGHTEEN_DECIMALS // price
        return max_usd, max_amount

    def _remaining_usd(tokens, max_usd, max_amount):
        claim_usd = tokens * max_usd // max_amount
        return (pile - tokens) * claim_usd // tokens

    def _usd_map_near(max_usd, max_amount, around_tokens, width=2000):
        k0 = around_tokens * max_usd // max_amount
        mapping = {}
        for k in range(max(1, k0 - width), k0 + width + 1):
            mapping[k * max_amount // max_usd] = k
        return mapping

    def _predicted_shares(tokens, max_usd, max_amount, total_shares, total_value):
        claim_usd = tokens * max_usd // max_amount
        numerator = claim_usd * (total_shares + 10**8)
        denominator = total_value + 1
        shares = numerator // denominator
        if numerator % denominator:
            shares += 1
        return shares

    def _probe(price, donate=0):
        with boa.env.anchor():
            _setup(price, donate)
            max_usd, max_amount = _claim_bounds(price)
            total_shares = stability_pool.totalBalances(alpha_token)
            total_value = stability_pool.getTotalValue(alpha_token)
            return max_usd, max_amount, total_shares, total_value

    attack_probe = _probe(attack_price)
    control_probe = _probe(control_price, control_donate)
    attack_map = _usd_map_near(attack_probe[0], attack_probe[1], target_tokens)
    control_map = _usd_map_near(control_probe[0], control_probe[1], target_tokens)
    common = set(attack_map) & set(control_map)
    assert common
    chosen_tokens = None
    for tokens in [target_tokens] + sorted(common, key=lambda value: abs(value - target_tokens)):
        if tokens not in common:
            continue
        if _remaining_usd(tokens, attack_probe[0], attack_probe[1]) >= RETENTION_THRESHOLD:
            continue
        if _remaining_usd(tokens, control_probe[0], control_probe[1]) < RETENTION_THRESHOLD:
            continue
        if _predicted_shares(tokens, *attack_probe) != _predicted_shares(tokens, *control_probe):
            continue
        chosen_tokens = tokens
        break
    assert chosen_tokens is not None
    attack_usd = attack_map[chosen_tokens]
    control_usd = control_map[chosen_tokens]

    def _arm(price, max_usd, expected_tokens, pre_claim_donate=0, post_claim_donate=0):
        _setup(price, pre_claim_donate)
        vault_id = vault_book.getRegId(stability_pool)
        claim_from_stability_pool(
            teller, vault_id, alpha_token, bravo_token, max_usd, sender=bob,
        )
        claimed = _claimed_log()
        residual = stability_pool.claimableBalances(alpha_token, bravo_token)
        claim_custody = bravo_token.balanceOf(stability_pool.address)
        assert claimed.claimAmount == expected_tokens
        assert residual == pile - expected_tokens
        assert claim_custody == residual
        assert residual != 0
        assert stability_pool.totalBalances(alpha_token) != 0
        assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        if post_claim_donate:
            alpha_token.transfer(
                stability_pool, post_claim_donate, sender=alpha_token_whale,
            )
        stab_custody = alpha_token.balanceOf(stability_pool.address)
        total_shares = stability_pool.totalBalances(alpha_token)
        bob_shares = stability_pool.userBalances(bob, alpha_token)
        restored_price = mock_price_source.getPrice(bravo_token)
        alpha_token.transfer(stability_pool, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
        stability_pool.depositTokensInVault(
            alice, alpha_token, 100 * EIGHTEEN_DECIMALS, sender=teller.address,
        )
        stability_pool.pause(True, sender=switchboard_alpha.address)
        stability_pool.activateClaimAssets(
            alpha_token, [bravo_token], sender=alice,
        )
        stability_pool.pause(False, sender=switchboard_alpha.address)
        assert stability_pool.getClaimAssetState(
            alpha_token, bravo_token,
        ) == CLAIM_ASSET_ACTIVE
        withdrawn, _ = stability_pool.withdrawTokensFromVault(
            alice, alpha_token, MAX_UINT256, alice, sender=teller.address,
        )
        return (
            withdrawn,
            claimed.claimAmount,
            claimed.claimShares,
            residual,
            claim_custody,
            stab_custody,
            total_shares,
            bob_shares,
            restored_price,
        )

    with boa.env.anchor():
        (
            attack_withdrawn,
            attack_claim_amount,
            attack_claim_shares,
            attack_residual,
            attack_claim_custody,
            attack_stab_custody,
            attack_total_shares,
            attack_bob_shares,
            attack_restored_price,
        ) = _arm(
            attack_price, attack_usd, chosen_tokens,
            post_claim_donate=control_donate,
        )
    with boa.env.anchor():
        (
            control_withdrawn,
            control_claim_amount,
            control_claim_shares,
            control_residual,
            control_claim_custody,
            control_stab_custody,
            control_total_shares,
            control_bob_shares,
            control_restored_price,
        ) = _arm(
            control_price, control_usd, chosen_tokens,
            pre_claim_donate=control_donate,
        )
    assert attack_claim_amount == control_claim_amount
    assert attack_claim_shares == control_claim_shares
    assert attack_residual == control_residual
    assert attack_claim_custody == control_claim_custody
    assert attack_stab_custody == control_stab_custody
    assert attack_total_shares == control_total_shares
    assert attack_bob_shares == control_bob_shares
    assert attack_restored_price == control_restored_price
    assert abs(attack_withdrawn - control_withdrawn) <= 1


def _seed_green_claim(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    green_token,
    savings_green,
    whale,
    auction_house,
    pair_amount,
):
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    green_token.transfer(stability_pool, pair_amount, sender=whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, 1, green_token, pair_amount, bob, green_token, savings_green,
        sender=auction_house.address,
    )
    assert stability_pool.getClaimAssetState(alpha_token, green_token) == CLAIM_ASSET_ACTIVE
    return pair_amount


def _swap_green_to_leftover(
    stability_pool,
    alpha_token,
    bravo_token,
    bravo_token_whale,
    green_token,
    auction_house,
    leftover,
    mock_price_source,
):
    prev = stability_pool.claimableBalances(alpha_token, green_token)
    consume = prev - leftover
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    bravo_token.transfer(stability_pool, 1, sender=bravo_token_whale)
    burned = stability_pool.swapWithClaimableGreen(
        alpha_token, consume, bravo_token, 1, green_token,
        sender=auction_house.address,
    )
    logs = _dust_logs(stability_pool, green_token)
    assert burned == consume
    return prev, logs


def test_g10_swap_with_claimable_green_meaningful_residual_stays_listed(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    whale,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    """A leftover just under $0.05 is meaningful, not microscopic, while shares remain."""
    pair_amount = _seed_green_claim(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source, green_token, savings_green, whale, auction_house,
        ACTIVATION_THRESHOLD,
    )
    leftover = RETENTION_THRESHOLD - 1
    assert leftover > pair_amount // LIVE_RESIDUAL_DIVISOR
    _, logs = _swap_green_to_leftover(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        green_token, auction_house, leftover, mock_price_source,
    )
    assert logs == []
    assert stability_pool.claimableBalances(alpha_token, green_token) == leftover
    assert stability_pool.getClaimAssetState(alpha_token, green_token) == CLAIM_ASSET_ACTIVE


def test_g10_swap_with_claimable_green_zero_residual_uses_reason_zero(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    whale,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_green_claim(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source, green_token, savings_green, whale, auction_house,
        ACTIVATION_THRESHOLD,
    )
    _, logs = _swap_green_to_leftover(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        green_token, auction_house, 0, mock_price_source,
    )
    assert len(logs) == 1
    assert logs[0].reason == DEACTIVATION_ZERO
    assert logs[0].balance == 0
    assert stability_pool.claimableBalances(alpha_token, green_token) == 0
    assert stability_pool.getClaimAssetState(alpha_token, green_token) == CLAIM_ASSET_ABSENT


@pytest.mark.parametrize("extra, expect_dust", [(0, True), (1, False)])
def test_g10_swap_with_claimable_green_live_inclusive_boundary(
    extra,
    expect_dust,
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    whale,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    pair_amount = _seed_green_claim(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source, green_token, savings_green, whale, auction_house,
        ACTIVATION_THRESHOLD,
    )
    leftover = pair_amount // LIVE_RESIDUAL_DIVISOR + extra
    prev, logs = _swap_green_to_leftover(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        green_token, auction_house, leftover, mock_price_source,
    )
    assert leftover < RETENTION_THRESHOLD
    assert stability_pool.claimableBalances(alpha_token, green_token) == leftover
    if expect_dust:
        assert len(logs) == 1
        assert logs[0].reason == DEACTIVATION_DUST
        assert logs[0].balance == leftover
        assert stability_pool.getClaimAssetState(alpha_token, green_token) == CLAIM_ASSET_DORMANT
        assert stability_pool.indexOfClaimableAsset(alpha_token, green_token) == 0
        assert leftover <= prev // LIVE_RESIDUAL_DIVISOR
    else:
        assert logs == []
        assert leftover == prev // LIVE_RESIDUAL_DIVISOR + 1
        assert stability_pool.getClaimAssetState(alpha_token, green_token) == CLAIM_ASSET_ACTIVE


def test_g10_swap_with_claimable_green_empty_cohort_dust_unlists(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    whale,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    green_token.transfer(stability_pool, RETENTION_THRESHOLD, sender=whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, 1, green_token, RETENTION_THRESHOLD, bob, green_token, savings_green,
        sender=auction_house.address,
    )
    assert stability_pool.getClaimAssetState(alpha_token, green_token) == CLAIM_ASSET_DORMANT
    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    top_up = ACTIVATION_THRESHOLD - RETENTION_THRESHOLD
    green_token.transfer(stability_pool, top_up, sender=whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, 1, green_token, top_up, bob, green_token, savings_green,
        sender=auction_house.address,
    )
    pair_amount = stability_pool.claimableBalances(alpha_token, green_token)
    assert pair_amount == ACTIVATION_THRESHOLD
    assert stability_pool.getClaimAssetState(alpha_token, green_token) == CLAIM_ASSET_ACTIVE
    leftover = RETENTION_THRESHOLD - 1
    assert leftover > pair_amount // LIVE_RESIDUAL_DIVISOR
    _, logs = _swap_green_to_leftover(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        green_token, auction_house, leftover, mock_price_source,
    )
    assert len(logs) == 1
    assert logs[0].reason == DEACTIVATION_DUST
    assert logs[0].balance == leftover
    assert stability_pool.claimableBalances(alpha_token, green_token) == leftover
    assert stability_pool.totalClaimableBalances(green_token) == leftover
    assert green_token.balanceOf(stability_pool) == leftover
    assert stability_pool.getClaimAssetState(alpha_token, green_token) == CLAIM_ASSET_DORMANT


def test_g10_live_eighteen_decimal_inclusive_boundary_via_one_dollar_redeem(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    whale,
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
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    pile = EIGHTEEN_DECIMALS
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        pile, bob, auction_house, green_token, savings_green,
    )
    bound = pile // LIVE_RESIDUAL_DIVISOR
    vault_id = vault_book.getRegId(stability_pool)

    def _redeem_to(leftover):
        consume = pile - leftover
        green_token.transfer(bob, consume, sender=whale)
        green_token.approve(teller, consume, sender=bob)
        redeem_from_stability_pool(
            teller, vault_id, bravo_token, consume, bob, sender=bob,
        )
        return _dust_logs(teller, bravo_token)

    with boa.env.anchor():
        logs = _redeem_to(bound)
        assert len(logs) == 1
        assert logs[0].reason == DEACTIVATION_DUST
        assert logs[0].balance == bound
        assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 0
        assert stability_pool.claimableBalances(alpha_token, bravo_token) == bound
        assert stability_pool.totalClaimableBalances(bravo_token) == bound
        assert bravo_token.balanceOf(stability_pool) == bound
        assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT

        received_before = bravo_token.balanceOf(bob)
        claim_from_stability_pool(
            teller, vault_id, alpha_token, bravo_token, MAX_UINT256, sender=bob,
        )
        assert bravo_token.balanceOf(bob) - received_before == bound
        assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
        assert stability_pool.totalClaimableBalances(bravo_token) == 0
        assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ABSENT

    logs = _redeem_to(bound + 1)
    assert logs == []
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == bound + 1
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE


def test_g10_live_p_less_than_d_no_nonzero_residual_qualifies(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
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
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 3 * 10**34)
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    pile = 10
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        pile, bob, auction_house, green_token, savings_green,
    )
    assert pile < LIVE_RESIDUAL_DIVISOR
    vault_id = vault_book.getRegId(stability_pool)
    claim_from_stability_pool(
        teller, vault_id, alpha_token, bravo_token, 27 * 10**16, sender=bob,
    )
    logs = _dust_logs(teller, bravo_token)
    leftover = stability_pool.claimableBalances(alpha_token, bravo_token)
    assert logs == []
    assert leftover != 0
    assert leftover > pile // LIVE_RESIDUAL_DIVISOR
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE


def test_g10_usd_below_retention_without_microscopic_ratio_stays_listed(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    whale,
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
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    pile = 30 * 10**16
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        pile, bob, auction_house, green_token, savings_green,
    )
    leftover = 4 * 10**16
    consume = pile - leftover
    vault_id = vault_book.getRegId(stability_pool)
    green_token.transfer(bob, consume, sender=whale)
    green_token.approve(teller, consume, sender=bob)
    redeem_from_stability_pool(
        teller, vault_id, bravo_token, consume, bob, sender=bob,
    )
    logs = _dust_logs(teller, bravo_token)
    assert leftover > pile // LIVE_RESIDUAL_DIVISOR
    assert leftover < RETENTION_THRESHOLD
    assert logs == []
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE


def test_g10_microscopic_ratio_at_retention_usd_stays_listed(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    whale,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    credit_engine,
):
    pile = 5 * 10**26
    leftover = pile // LIVE_RESIDUAL_DIVISOR
    assert leftover == RETENTION_THRESHOLD
    green_token.mint(whale, pile, sender=credit_engine.address)
    _seed_green_claim(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source, green_token, savings_green, whale, auction_house,
        pile,
    )
    _, logs = _swap_green_to_leftover(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        green_token, auction_house, leftover, mock_price_source,
    )
    assert logs == []
    assert leftover <= pile // LIVE_RESIDUAL_DIVISOR
    assert stability_pool.getClaimAssetState(alpha_token, green_token) == CLAIM_ASSET_ACTIVE


def test_g10_six_decimal_live_inclusive_boundary(
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    whale,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
    vault_book,
    governance,
    setGeneralConfig,
    setAssetConfig,
):
    setGeneralConfig()
    six = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "G10 Six",
        "G10S6",
        6,
        0,
        name="g10_six_claim",
    )
    six.mint(alice, 100_000 * 10**6, sender=governance.address)
    setAssetConfig(six)
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(six, EIGHTEEN_DECIMALS)
    pile = LIVE_RESIDUAL_DIVISOR  # 10,000 whole 6dp tokens
    _record_claim(
        stability_pool, alpha_token, six, alice,
        pile, bob, auction_house, green_token, savings_green,
    )
    bound = pile // LIVE_RESIDUAL_DIVISOR
    vault_id = vault_book.getRegId(stability_pool)

    def _redeem_to(leftover):
        consume_tokens = pile - leftover
        payment = consume_tokens * EIGHTEEN_DECIMALS // (10 ** six.decimals())
        green_token.transfer(bob, payment, sender=whale)
        green_token.approve(teller, payment, sender=bob)
        redeem_from_stability_pool(
            teller, vault_id, six, payment, bob, sender=bob,
        )
        return _dust_logs(teller, six)

    with boa.env.anchor():
        logs = _redeem_to(bound)
        assert len(logs) == 1
        assert logs[0].reason == DEACTIVATION_DUST
        assert logs[0].balance == bound
        assert stability_pool.getClaimAssetState(alpha_token, six) == CLAIM_ASSET_DORMANT

    logs = _redeem_to(bound + 1)
    assert logs == []
    assert stability_pool.getClaimAssetState(alpha_token, six) == CLAIM_ASSET_ACTIVE


def test_g10_wrong_low_quote_near_total_only_unlists_bounded_residual(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    whale,
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
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    pile = EIGHTEEN_DECIMALS
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        pile, bob, auction_house, green_token, savings_green,
    )
    mock_price_source.setPrice(bravo_token, 10**15)
    leftover = pile // LIVE_RESIDUAL_DIVISOR
    consume_tokens = pile - leftover
    payment = consume_tokens * 10**15 // EIGHTEEN_DECIMALS
    vault_id = vault_book.getRegId(stability_pool)
    green_token.transfer(bob, payment, sender=whale)
    green_token.approve(teller, payment, sender=bob)
    redeem_from_stability_pool(
        teller, vault_id, bravo_token, payment, bob, sender=bob,
    )
    logs = _dust_logs(teller, bravo_token)
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == leftover
    assert len(logs) == 1
    assert logs[0].reason == DEACTIVATION_DUST
    assert logs[0].balance == leftover
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT


def test_g10_wrong_low_quote_meaningful_residual_stays_listed(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    whale,
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
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    pile = 11 * EIGHTEEN_DECIMALS
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        pile, bob, auction_house, green_token, savings_green,
    )
    mock_price_source.setPrice(bravo_token, 10**15)
    payment = 10**15
    vault_id = vault_book.getRegId(stability_pool)
    green_token.transfer(bob, payment, sender=whale)
    green_token.approve(teller, payment, sender=bob)
    redeem_from_stability_pool(
        teller, vault_id, bravo_token, payment, bob, sender=bob,
    )
    logs = _dust_logs(teller, bravo_token)
    leftover = stability_pool.claimableBalances(alpha_token, bravo_token)
    assert leftover > pile // LIVE_RESIDUAL_DIVISOR
    assert leftover != 0
    assert logs == []
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE


def test_g10_dust_unlists_frees_slot_preserves_ledger_and_reactivates(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    whale,
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
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    pile = EIGHTEEN_DECIMALS
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        pile, bob, auction_house, green_token, savings_green,
    )
    leftover = pile // LIVE_RESIDUAL_DIVISOR
    consume = pile - leftover
    vault_id = vault_book.getRegId(stability_pool)
    green_token.transfer(bob, consume, sender=whale)
    green_token.approve(teller, consume, sender=bob)
    redeem_from_stability_pool(
        teller, vault_id, bravo_token, consume, bob, sender=bob,
    )
    logs = _dust_logs(teller, bravo_token)
    assert len(logs) == 1
    assert logs[0].reason == DEACTIVATION_DUST
    assert logs[0].balance == leftover
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 0
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == leftover
    assert stability_pool.totalClaimableBalances(bravo_token) == leftover
    assert bravo_token.balanceOf(stability_pool) == leftover
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT

    added = ACTIVATION_THRESHOLD
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        added, bob, auction_house, green_token, savings_green,
    )
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == leftover + added
    assert stability_pool.totalClaimableBalances(bravo_token) == leftover + added


def test_g10_live_prune_is_noop_on_surviving_nonzero_residual(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    whale,
    teller,
    auction_house,
    mock_price_source,
    green_token,
    savings_green,
):
    pair_amount = _seed_green_claim(
        stability_pool, alpha_token, alpha_token_whale, bob, teller,
        mock_price_source, green_token, savings_green, whale, auction_house,
        ACTIVATION_THRESHOLD,
    )
    leftover = pair_amount // LIVE_RESIDUAL_DIVISOR + 1
    _swap_green_to_leftover(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        green_token, auction_house, leftover, mock_price_source,
    )
    assert stability_pool.getClaimAssetState(alpha_token, green_token) == CLAIM_ASSET_ACTIVE
    stability_pool.pruneClaimableAssets(alpha_token, [green_token], sender=sally)
    logs = _dust_logs(stability_pool, green_token)
    assert logs == []
    assert stability_pool.claimableBalances(alpha_token, green_token) == leftover
    assert stability_pool.getClaimAssetState(alpha_token, green_token) == CLAIM_ASSET_ACTIVE


def test_g10_empty_cohort_partial_redemption_dust_unlists(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    whale,
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
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller, mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    dormant = 9 * 10**16
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        dormant, bob, auction_house, green_token, savings_green,
    )
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    top_up = 21 * 10**16
    _record_claim(
        stability_pool, alpha_token, bravo_token, bravo_token_whale,
        top_up, bob, auction_house, green_token, savings_green,
    )
    pile = dormant + top_up
    assert pile == 30 * 10**16
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    leftover = 4 * 10**16
    consume = pile - leftover
    vault_id = vault_book.getRegId(stability_pool)
    green_token.transfer(bob, consume, sender=whale)
    green_token.approve(teller, consume, sender=bob)
    redeem_from_stability_pool(
        teller, vault_id, bravo_token, consume, bob, sender=bob,
    )
    logs = _dust_logs(teller, bravo_token)
    assert leftover > pile // LIVE_RESIDUAL_DIVISOR
    assert len(logs) == 1
    assert logs[0].reason == DEACTIVATION_DUST
    assert logs[0].balance == leftover
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == leftover
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
