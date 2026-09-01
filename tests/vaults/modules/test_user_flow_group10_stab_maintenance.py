"""Group 10 proof tests -- permissionless StabVault claim-list maintenance.

Scope: `pruneClaimableAssets` / `activateClaimAssets` list membership only.
Share math beyond the single composition that prune/activate causes belongs to
Group 5; liquidation/auction product behaviour belongs to Group 1.

Claim rows are seeded with `swapForLiquidatedCollateral(sender=auction_house)`,
which impersonates AuctionHouse and therefore skips the Group 1 swap path.
"""

import boa
import pytest

from conf_utils import filter_logs, sync_deployed_token
from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


ACTIVATION_THRESHOLD = 10 * 10**16   # $0.10
RETENTION_THRESHOLD = 5 * 10**16     # $0.05
CLAIM_ASSET_ABSENT = 0
CLAIM_ASSET_DORMANT = 1
CLAIM_ASSET_ACTIVE = 2
DEACTIVATION_ZERO = 1
DEACTIVATION_DUST = 2
MAX_ACTIVE_CLAIM_ASSETS = 20


def _seed_stab(stability_pool, asset, whale, user, teller, mock_price_source,
               amount=100 * EIGHTEEN_DECIMALS):
    mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)
    asset.transfer(stability_pool, amount, sender=whale)
    assert stability_pool.depositTokensInVault(
        user, asset, amount, sender=teller.address,
    ) == amount


def _record_claim(stability_pool, stab_asset, claim_asset, claim_whale,
                  claim_amount, recipient, auction_house, green_token,
                  savings_green, stab_amount=1):
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


def _exit_cohort(stability_pool, stab, user, teller):
    stability_pool.withdrawTokensFromVault(
        user, stab, MAX_UINT256, user, sender=teller.address,
    )
    assert stability_pool.totalBalances(stab) == 0


def _exact_floor(amount):
    return (ACTIVATION_THRESHOLD * EIGHTEEN_DECIMALS + amount - 1) // amount


def _exact_floor_usd(amount, usd):
    return (usd * EIGHTEEN_DECIMALS + amount - 1) // amount


def _claim_ledger(stability_pool, stab_asset, claim_asset):
    """Every value prune/activate is forbidden to move."""
    return (
        stability_pool.claimableBalances(stab_asset, claim_asset),
        stability_pool.totalClaimableBalances(claim_asset),
        claim_asset.balanceOf(stability_pool),
        stab_asset.balanceOf(stability_pool),
        stability_pool.totalBalances(stab_asset),
    )


########################################################################
# Never-skip #1a -- custody-deficit safety property
#
# Candidate invariant: while aggregate claim custody is below aggregate
# claim liability, a permissionless dust prune must not hide the short row
# or re-enable NAV-dependent share minting, burning, or withdrawal.
########################################################################


def test_prune_does_not_reenable_share_actions_while_claim_custody_is_still_short(
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
    """SAFETY PROPERTY. Live-share dust prune is a no-op, so an undercustodied
    active row stays on the iterable and deposit/withdraw stay fail-closed.
    """
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    claim_amount = 10 * EIGHTEEN_DECIMALS
    _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                  claim_amount, bob, auction_house, green_token, savings_green)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE

    # Custody loss. Address impersonation of the pool: models a rebase /
    # confiscation / legacy-migration class of event, NOT an ordinary EOA flow.
    bravo_token.transfer(alice, 1, sender=stability_pool.address)
    assert bravo_token.balanceOf(stability_pool) < (
        stability_pool.totalClaimableBalances(bravo_token))

    # Before prune: every NAV-dependent share action is fail-closed.
    with boa.reverts("claim custody deficit"):
        stability_pool.getTotalValue(alpha_token)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS,
                         sender=alpha_token_whale)
    with boa.reverts("claim custody deficit"):
        stability_pool.depositTokensInVault(
            sally, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address)
    with boa.reverts("claim custody deficit"):
        stability_pool.withdrawTokensFromVault(
            bob, alpha_token, EIGHTEEN_DECIMALS, bob, sender=teller.address)

    ledger_before = _claim_ledger(stability_pool, alpha_token, bravo_token)
    bob_shares_before = stability_pool.userBalances(bob, alpha_token)

    # Ordinary EOA prunes at a valid nonzero quote below $0.05.
    # 10e18 bravo * $0.001 = $0.01 < RETENTION.
    mock_price_source.setPrice(bravo_token, 10**15)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token],
                                        sender=alice)

    # Live book: dust prune is a no-op. Deficit stays on the iterable.
    assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []
    assert _claim_ledger(stability_pool, alpha_token, bravo_token) == (
        ledger_before)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert bravo_token.balanceOf(stability_pool) < (
        stability_pool.totalClaimableBalances(bravo_token))
    assert stability_pool.userBalances(bob, alpha_token) == bob_shares_before

    # THE PROPERTY: the deficit is not repaired or settled, so NAV-dependent
    # share actions must stay blocked.
    with boa.reverts("claim custody deficit"):
        stability_pool.withdrawTokensFromVault(
            bob, alpha_token, EIGHTEEN_DECIMALS, bob, sender=teller.address)
    with boa.reverts("claim custody deficit"):
        stability_pool.depositTokensInVault(
            sally, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address)


def test_custody_deficit_blocks_share_actions_without_the_prune(
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
    """Causal control: same deficit and dust quote, no prune. Share actions
    stay blocked because the short row is still on the iterable.
    """
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    claim_amount = 10 * EIGHTEEN_DECIMALS
    _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                  claim_amount, bob, auction_house, green_token, savings_green)
    bravo_token.transfer(alice, 1, sender=stability_pool.address)
    mock_price_source.setPrice(bravo_token, 10**15)

    # No prune. Row stays on the iterable, strict NAV still walks it.
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS,
                         sender=alpha_token_whale)
    with boa.reverts("claim custody deficit"):
        stability_pool.withdrawTokensFromVault(
            bob, alpha_token, EIGHTEEN_DECIMALS, bob, sender=teller.address)
    with boa.reverts("claim custody deficit"):
        stability_pool.depositTokensInVault(
            sally, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address)


def test_full_custody_share_actions_remain_available_after_live_prune_noop(
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
    """Adjacent positive control -- full custody, same dust quote.

    Live-share prune is a no-op; the row stays ACTIVE. Share actions proceed
    because custody matches liability, not because the row was delisted.
    """
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    claim_amount = 10 * EIGHTEEN_DECIMALS
    _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                  claim_amount, bob, auction_house, green_token, savings_green)

    # No custody loss at all.
    assert bravo_token.balanceOf(stability_pool) == (
        stability_pool.totalClaimableBalances(bravo_token))
    claim_usd = (
        claim_amount * mock_price_source.getPrice(bravo_token) // EIGHTEEN_DECIMALS
    )
    assert stability_pool.getTotalValue(alpha_token) == (
        alpha_token.balanceOf(stability_pool) + claim_usd
    )

    mock_price_source.setPrice(bravo_token, 10**15)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token],
                                        sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    dust_usd = claim_amount * 10**15 // EIGHTEEN_DECIMALS
    assert stability_pool.getTotalValue(alpha_token) == (
        alpha_token.balanceOf(stability_pool) + dust_usd
    )

    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS,
                         sender=alpha_token_whale)
    assert stability_pool.depositTokensInVault(
        sally, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address,
    ) == EIGHTEEN_DECIMALS


def test_activate_still_reverts_until_custody_is_replenished(
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
    """Empty-cohort activate still asserts aggregate custody.

    A short dormant row cannot be seated until the missing wei is returned.
    """
    claim_amount = ACTIVATION_THRESHOLD - 1
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                  claim_amount, bob, auction_house, green_token, savings_green)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    stability_pool.withdrawTokensFromVault(
        bob, alpha_token, MAX_UINT256, bob, sender=teller.address)
    assert stability_pool.totalBalances(alpha_token) == 0
    bravo_token.transfer(alice, 1, sender=stability_pool.address)
    floor = (ACTIVATION_THRESHOLD * EIGHTEEN_DECIMALS + claim_amount - 1) // claim_amount
    mock_price_source.setPrice(bravo_token, floor)
    stability_pool.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("claim custody deficit"):
        stability_pool.activateClaimAssets(alpha_token, [bravo_token],
                                           sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_DORMANT

    bravo_token.transfer(stability_pool, 1, sender=alice)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token],
                                       sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    stability_pool.pause(False, sender=switchboard_alpha.address)
    claim_usd = (
        claim_amount * mock_price_source.getPrice(bravo_token) // EIGHTEEN_DECIMALS
    )
    assert stability_pool.getTotalValue(alpha_token) == (
        alpha_token.balanceOf(stability_pool) + claim_usd
    )


########################################################################
# Never-skip #1b -- share/NAV compositions caused by prune / activate
########################################################################


def test_low_quote_live_prune_does_not_move_value_between_existing_and_new_shareholders(
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
    """#1b(i): live-share dust prune must not transfer value between
    existing and future shareholders.

    Control arm: honest price throughout, no prune. Attack arm: identical
    custody and identical final honest price, but a keeper attempts prune
    while a low-but-nonzero quote is live. The row stays ACTIVE, so a new
    depositor mints against the still-listed pile.
    """
    PILE = 100 * EIGHTEEN_DECIMALS
    DEPOSIT = 100 * EIGHTEEN_DECIMALS
    LOW_QUOTE = 4 * 10**14  # pile -> $0.04, below RETENTION

    def _setup():
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
                   mock_price_source, DEPOSIT)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(stability_pool, alpha_token, bravo_token,
                      bravo_token_whale, PILE, bob, auction_house, green_token,
                      savings_green)
        assert stability_pool.getClaimAssetState(
            alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE

    def _sally_deposits():
        alpha_token.transfer(stability_pool, DEPOSIT, sender=alpha_token_whale)
        stability_pool.depositTokensInVault(
            sally, alpha_token, DEPOSIT, sender=teller.address)

    # ---- control: same custody, same honest price, no maintenance ----
    with boa.env.anchor():
        _setup()
        _sally_deposits()
        control = (
            stability_pool.getTotalUserValue(bob, alpha_token),
            stability_pool.getTotalUserValue(sally, alpha_token),
            stability_pool.getTotalValue(alpha_token),
        )

    # ---- attempted prune at the low quote (live-share no-op), then restore ----
    _setup()
    mock_price_source.setPrice(bravo_token, LOW_QUOTE)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token],
                                        sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _sally_deposits()
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE

    attack = (
        stability_pool.getTotalUserValue(bob, alpha_token),
        stability_pool.getTotalUserValue(sally, alpha_token),
        stability_pool.getTotalValue(alpha_token),
    )
    print(
        "GROUP10_1B_LOW_QUOTE_PRUNE",
        f"control_bob={control[0]}", f"control_sally={control[1]}",
        f"attack_bob={attack[0]}", f"attack_sally={attack[1]}",
        f"control_nav={control[2]}", f"attack_nav={attack[2]}",
        f"bob_delta={attack[0] - control[0]}",
    )

    # Same custody, same final honest price -> same total NAV.
    assert attack[2] == control[2]
    # THE PROPERTY: maintenance timing must not move value between holders.
    assert attack[0] == control[0]
    assert attack[1] == control[1]


def test_high_quote_activate_does_not_let_an_exiting_holder_take_phantom_value(
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
    """#1b(ii): live-share activate must not seat a sub-threshold pile, so
    the first exit cannot withdraw against an inflated NAV.
    """
    DEPOSIT = 100 * EIGHTEEN_DECIMALS
    DUST_PILE = 100  # 100 wei -- $1e-16 at the honest price
    HIGH_QUOTE = 10**36  # pile -> $100

    def _setup():
        _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
                   mock_price_source, DEPOSIT)
        alpha_token.transfer(stability_pool, DEPOSIT, sender=alpha_token_whale)
        stability_pool.depositTokensInVault(
            sally, alpha_token, DEPOSIT, sender=teller.address)
        mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
        _record_claim(stability_pool, alpha_token, bravo_token,
                      bravo_token_whale, DUST_PILE, bob, auction_house,
                      green_token, savings_green)
        # Genuinely below the activation floor at the honest price.
        assert stability_pool.getClaimAssetState(
            alpha_token, bravo_token) == CLAIM_ASSET_DORMANT

    # ---- control: pile stays dormant, bob exits, honest price ----
    with boa.env.anchor():
        _setup()
        control_bob_out, _ = stability_pool.withdrawTokensFromVault(
            bob, alpha_token, 2**255, bob, sender=teller.address)
        control_sally_left = stability_pool.getTotalUserValue(
            sally, alpha_token)

    # ---- attempted high-quote activate (live-share no-op) -> bob exits ----
    _setup()
    mock_price_source.setPrice(bravo_token, HIGH_QUOTE)
    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token],
                                       sender=alice)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_DORMANT

    attack_bob_out, _ = stability_pool.withdrawTokensFromVault(
        bob, alpha_token, 2**255, bob, sender=teller.address)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    attack_sally_left = stability_pool.getTotalUserValue(sally, alpha_token)

    print(
        "GROUP10_1B_HIGH_QUOTE_ACTIVATE",
        f"control_bob_out={control_bob_out}",
        f"attack_bob_out={attack_bob_out}",
        f"control_sally_left={control_sally_left}",
        f"attack_sally_left={attack_sally_left}",
    )

    # THE PROPERTY: activating a dormant row must not let the exiting holder
    # take stab-asset custody that belongs to the remaining holder.
    assert attack_bob_out == control_bob_out
    assert attack_sally_left == control_sally_left


########################################################################
# Never-skip #1 -- prune identity
########################################################################


def _claimable_balance_slot(claim_asset, stab_asset):
    from eth_utils import keccak
    inner = keccak((9).to_bytes(32, "big")
                   + int(stab_asset.address, 16).to_bytes(32, "big"))
    return int.from_bytes(
        keccak(inner + int(claim_asset.address, 16).to_bytes(32, "big")),
        "big",
    )


def _active_list(stability_pool, stab_asset, depth=8):
    num = stability_pool.numClaimableAssets(stab_asset)
    return (
        num,
        stability_pool.getNumActiveClaimAssets(stab_asset),
        [stability_pool.claimableAssets(stab_asset, i) for i in range(depth)],
    )


@pytest.fixture
def four_active_claims(
    stability_pool, alpha_token, alpha_token_whale, bob, teller,
    mock_price_source, auction_house, green_token, savings_green, governance,
    alice, switchboard_alpha,
):
    """Empty alpha cohort with four active claim rows [A, B, C, D]."""
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    tokens = []
    for i in range(4):
        tok = boa.load(
            "contracts/mock/MockErc20.vy", governance,
            f"G10 Claim {i}", f"G10C{i}", 18, 0, name=f"g10_claim_{i}",
        )
        tok.mint(alice, 1000 * EIGHTEEN_DECIMALS, sender=governance.address)
        sync_deployed_token(tok)
        mock_price_source.setPrice(tok, EIGHTEEN_DECIMALS)
        _record_claim(stability_pool, alpha_token, tok, alice,
                      ACTIVATION_THRESHOLD - 1, bob, auction_house, green_token,
                      savings_green)
        assert stability_pool.getClaimAssetState(
            alpha_token, tok) == CLAIM_ASSET_DORMANT
        tokens.append(tok)
    stability_pool.withdrawTokensFromVault(
        bob, alpha_token, MAX_UINT256, bob, sender=teller.address)
    assert stability_pool.totalBalances(alpha_token) == 0
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    floor = (
        ACTIVATION_THRESHOLD * EIGHTEEN_DECIMALS + ACTIVATION_THRESHOLD - 2
    ) // (ACTIVATION_THRESHOLD - 1)
    for tok in tokens:
        mock_price_source.setPrice(tok, floor)
    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.activateClaimAssets(alpha_token, tokens, sender=alice)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    for tok in tokens:
        assert stability_pool.getClaimAssetState(
            alpha_token, tok) == CLAIM_ASSET_ACTIVE
    return tokens


def test_prune_non_mutating_cases_change_nothing(
    stability_pool, alpha_token, bravo_token, charlie_token, alpha_token_whale,
    bravo_token_whale, bob, alice, sally, teller, auction_house,
    mock_price_source, green_token, savings_green,
):
    """Empty array, unknown claim asset, unknown stab asset, already-dormant.

    The caller (sally) holds no shares in the pool -- prune has no share
    requirement.
    """
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                  10 * EIGHTEEN_DECIMALS, bob, auction_house, green_token,
                  savings_green)
    mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)

    assert stability_pool.userBalances(sally, alpha_token) == 0
    before = (
        _active_list(stability_pool, alpha_token),
        _claim_ledger(stability_pool, alpha_token, bravo_token),
        stability_pool.getTotalValue(alpha_token),
    )

    stability_pool.pruneClaimableAssets(alpha_token, [], sender=sally)
    stability_pool.pruneClaimableAssets(alpha_token, [charlie_token],
                                        sender=sally)
    stability_pool.pruneClaimableAssets(alpha_token, [ZERO_ADDRESS],
                                        sender=sally)
    stability_pool.pruneClaimableAssets(bravo_token, [bravo_token],
                                        sender=sally)
    stability_pool.pruneClaimableAssets(charlie_token, [bravo_token],
                                        sender=sally)
    assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []
    assert (
        _active_list(stability_pool, alpha_token),
        _claim_ledger(stability_pool, alpha_token, bravo_token),
        stability_pool.getTotalValue(alpha_token),
    ) == before


def test_prune_swap_and_pop_middle_last_and_only_row(
    stability_pool, alpha_token, four_active_claims, alice,
    mock_price_source,
):
    """Middle, tail and final-row removals; slots, indices and event fields."""
    a, b, c, d = four_active_claims
    stab = alpha_token.address
    assert _active_list(stability_pool, alpha_token)[0] == 5
    assert _active_list(stability_pool, alpha_token)[2][1:5] == [
        a.address, b.address, c.address, d.address]

    # --- middle: remove B (index 2); D (index 4, the tail) takes its place
    mock_price_source.setPrice(b, 10**15)  # 1e18 * 1e15 / 1e18 = $0.001
    stability_pool.pruneClaimableAssets(alpha_token, [b], sender=alice)
    log = filter_logs(stability_pool, "ClaimAssetDeactivated")[0]
    assert log.stabAsset == stab and log.claimAsset == b.address
    assert log.reason == DEACTIVATION_DUST
    assert log.balance == ACTIVATION_THRESHOLD - 1
    assert log.activeCount == 3
    num, active, slots = _active_list(stability_pool, alpha_token)
    assert (num, active) == (4, 3)
    assert slots[1:5] == [a.address, d.address, c.address, ZERO_ADDRESS]
    assert stability_pool.indexOfClaimableAsset(alpha_token, d) == 2
    assert stability_pool.indexOfClaimableAsset(alpha_token, b) == 0

    # --- tail: remove C (index 3 == lastIndex); no shift
    mock_price_source.setPrice(c, 10**15)
    stability_pool.pruneClaimableAssets(alpha_token, [c], sender=alice)
    log = filter_logs(stability_pool, "ClaimAssetDeactivated")[0]
    assert log.activeCount == 2
    num, active, slots = _active_list(stability_pool, alpha_token)
    assert (num, active) == (3, 2)
    assert slots[1:5] == [a.address, d.address, ZERO_ADDRESS, ZERO_ADDRESS]

    # --- drain to the empty state: num settles at 1, not 0
    for tok in (a, d):
        mock_price_source.setPrice(tok, 10**15)
        stability_pool.pruneClaimableAssets(alpha_token, [tok], sender=alice)
    num, active, slots = _active_list(stability_pool, alpha_token)
    assert (num, active) == (1, 0)
    assert slots[1:5] == [ZERO_ADDRESS] * 4
    assert stability_pool.getTotalValue(alpha_token) != 0


def test_prune_batch_a_then_c_after_c_moved_into_a_index(
    stability_pool, alpha_token, four_active_claims, alice, mock_price_source,
):
    """One batch [A, C] over active [A, B, C]: after A goes, C occupies A's
    index, and the later request must still resolve to C.
    """
    a, b, c, d = four_active_claims
    # reduce to exactly [A, B, C]
    mock_price_source.setPrice(d, 10**15)
    stability_pool.pruneClaimableAssets(alpha_token, [d], sender=alice)
    assert _active_list(stability_pool, alpha_token)[2][1:4] == [
        a.address, b.address, c.address]

    for tok in (a, c):
        mock_price_source.setPrice(tok, 10**15)
    stability_pool.pruneClaimableAssets(alpha_token, [a, c], sender=alice)

    logs = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert [log.claimAsset for log in logs] == [a.address, c.address]
    assert [log.activeCount for log in logs] == [2, 1]
    assert all(log.reason == DEACTIVATION_DUST for log in logs)
    num, active, slots = _active_list(stability_pool, alpha_token)
    assert (num, active) == (2, 1)
    assert slots[1:4] == [b.address, ZERO_ADDRESS, ZERO_ADDRESS]
    assert stability_pool.indexOfClaimableAsset(alpha_token, b) == 1
    assert stability_pool.getClaimAssetState(alpha_token, b) == (
        CLAIM_ASSET_ACTIVE)
    for tok in (a, c):
        assert stability_pool.getClaimAssetState(alpha_token, tok) == (
            CLAIM_ASSET_DORMANT)


def test_prune_duplicates_remove_once(
    stability_pool, alpha_token, four_active_claims, alice, mock_price_source,
):
    a, b, c, d = four_active_claims
    mock_price_source.setPrice(a, 10**15)
    stability_pool.pruneClaimableAssets(alpha_token, [a, a, a], sender=alice)
    logs = filter_logs(stability_pool, "ClaimAssetDeactivated")
    assert len(logs) == 1
    num, active, _ = _active_list(stability_pool, alpha_token)
    assert (num, active) == (4, 3)


def test_prune_removes_zero_balance_active_row_with_reason_one(
    stability_pool, alpha_token, four_active_claims, alice,
):
    """Reason 1 is only reachable from a corrupted / legacy / direct-state row:
    ordinary `_reduceClaimableBalances` already removes at zero.
    """
    a, b, c, d = four_active_claims
    boa.env.set_storage(
        stability_pool.address, _claimable_balance_slot(a, alpha_token), 0)
    assert stability_pool.claimableBalances(alpha_token, a) == 0
    assert stability_pool.indexOfClaimableAsset(alpha_token, a) != 0

    stability_pool.pruneClaimableAssets(alpha_token, [a], sender=alice)
    log = filter_logs(stability_pool, "ClaimAssetDeactivated")[0]
    assert log.reason == DEACTIVATION_ZERO
    assert log.balance == 0
    assert stability_pool.getClaimAssetState(alpha_token, a) == (
        CLAIM_ASSET_ABSENT)


def test_prune_on_one_cohort_leaves_the_other_cohort_untouched(
    stability_pool, alpha_token, bravo_token, alpha_token_whale,
    bravo_token_whale, bob, alice, governance, teller, auction_house,
    mock_price_source, green_token, savings_green, switchboard_alpha,
):
    """Two stab assets share one claim asset; prune on A must not change B's
    pair balance or the global liability.
    """
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    _seed_stab(stability_pool, bravo_token, bravo_token_whale, bob, teller,
               mock_price_source)
    charlie_token = boa.load(
        "contracts/mock/MockErc20.vy", governance, "G10 Shared", "G10S", 18, 0,
        name="g10_shared_claim",
    )
    charlie_token_whale = alice
    charlie_token.mint(alice, 1000 * EIGHTEEN_DECIMALS,
                       sender=governance.address)
    sync_deployed_token(charlie_token)
    mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
    _record_claim(stability_pool, alpha_token, charlie_token,
                  charlie_token_whale, ACTIVATION_THRESHOLD - 1, bob,
                  auction_house, green_token, savings_green)
    _record_claim(stability_pool, bravo_token, charlie_token,
                  charlie_token_whale, 10 * EIGHTEEN_DECIMALS, bob,
                  auction_house, green_token, savings_green)
    assert stability_pool.totalClaimableBalances(charlie_token) == (
        10 * EIGHTEEN_DECIMALS + ACTIVATION_THRESHOLD - 1)

    b_pair = stability_pool.claimableBalances(bravo_token, charlie_token)
    b_index = stability_pool.indexOfClaimableAsset(bravo_token, charlie_token)
    global_liability = stability_pool.totalClaimableBalances(charlie_token)
    custody = charlie_token.balanceOf(stability_pool)

    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    mock_price_source.setPrice(charlie_token, _exact_floor(ACTIVATION_THRESHOLD - 1))
    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.activateClaimAssets(alpha_token, [charlie_token], sender=alice)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert stability_pool.getClaimAssetState(
        alpha_token, charlie_token) == CLAIM_ASSET_ACTIVE
    mock_price_source.setPrice(charlie_token, 10**15)  # each pile -> $0.01
    stability_pool.pruneClaimableAssets(alpha_token, [charlie_token],
                                        sender=alice)

    assert stability_pool.getClaimAssetState(
        alpha_token, charlie_token) == CLAIM_ASSET_DORMANT
    assert stability_pool.getClaimAssetState(
        bravo_token, charlie_token) == CLAIM_ASSET_ACTIVE
    assert stability_pool.claimableBalances(bravo_token, charlie_token) == (
        b_pair)
    assert stability_pool.indexOfClaimableAsset(
        bravo_token, charlie_token) == b_index
    assert stability_pool.totalClaimableBalances(charlie_token) == (
        global_liability)
    assert charlie_token.balanceOf(stability_pool) == custody


########################################################################
# Never-skip #2 -- activate identity
########################################################################


def test_activate_reverts_while_unpaused_and_changes_nothing(
    stability_pool, alpha_token, bravo_token, alpha_token_whale,
    bravo_token_whale, bob, alice, teller, auction_house, mock_price_source,
    green_token, savings_green,
):
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                  10 * EIGHTEEN_DECIMALS, bob, auction_house, green_token,
                  savings_green)
    mock_price_source.setPrice(bravo_token, 10**15)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token],
                                        sender=alice)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    before = (_active_list(stability_pool, alpha_token),
              _claim_ledger(stability_pool, alpha_token, bravo_token))
    assert not stability_pool.isPaused()
    with boa.reverts("contract not paused"):
        stability_pool.activateClaimAssets(alpha_token, [bravo_token],
                                           sender=alice)
    assert (_active_list(stability_pool, alpha_token),
            _claim_ledger(stability_pool, alpha_token, bravo_token)) == before


def test_activate_under_charlie_governor_and_lite_pause(
    stability_pool, alpha_token, bravo_token, alpha_token_whale,
    bravo_token_whale, bob, alice, teller, auction_house, mock_price_source,
    green_token, savings_green, switchboard_charlie, switchboard_alpha,
    mission_control, governance,
):
    """Production vault-pause proof.

    Charlie `pause(stability_pool, True)` is immediate. Governor may pause and
    unpause; a lite signer may only pause. Lite signers are `[]` in
    `DefaultsRobinhood.vy`, so the lite arm is governance-enableable, not the
    launch policy.
    """
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    dormant_amount = ACTIVATION_THRESHOLD - 1
    _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                  dormant_amount, bob, auction_house, green_token,
                  savings_green)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    _exit_cohort(stability_pool, alpha_token, bob, teller)
    exact_price = _exact_floor(dormant_amount)
    mock_price_source.setPrice(bravo_token, exact_price)
    ledger_before = _claim_ledger(stability_pool, alpha_token, bravo_token)

    # --- governor arm: real empty-cohort seating
    assert switchboard_charlie.pause(stability_pool.address, True,
                                    sender=governance.address)
    assert stability_pool.isPaused()
    stability_pool.activateClaimAssets(alpha_token, [bravo_token],
                                       sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert _claim_ledger(stability_pool, alpha_token, bravo_token) == (
        ledger_before)
    assert switchboard_charlie.pause(stability_pool.address, False,
                                    sender=governance.address)

    # back to dormant for the lite arm
    mock_price_source.setPrice(bravo_token, 10**15)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token],
                                        sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    mock_price_source.setPrice(bravo_token, exact_price)

    # --- lite arm (governance-enableable: liteSigners() is [] at launch)
    assert not mission_control.canPerformLiteAction(alice)
    with boa.reverts("no perms"):
        switchboard_charlie.pause(stability_pool.address, True, sender=alice)
    action_id = switchboard_alpha.setCanPerformLiteAction(
        alice, True, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    assert mission_control.canPerformLiteAction(alice)

    assert switchboard_charlie.pause(stability_pool.address, True, sender=alice)
    assert stability_pool.isPaused()
    stability_pool.activateClaimAssets(alpha_token, [bravo_token],
                                       sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE
    assert _claim_ledger(stability_pool, alpha_token, bravo_token) == (
        ledger_before)

    # lite may pause but not unpause
    with boa.reverts("no perms"):
        switchboard_charlie.pause(stability_pool.address, False, sender=alice)
    assert switchboard_charlie.pause(stability_pool.address, False,
                                    sender=governance.address)
    assert not stability_pool.isPaused()


def test_activate_skip_matrix_and_boundaries(
    stability_pool, alpha_token, bravo_token, alpha_token_whale,
    bravo_token_whale, bob, alice, governance, teller, auction_house,
    mock_price_source, green_token, savings_green, switchboard_alpha,
):
    """Empty / duplicates / zero / unknown / already-active / zero-balance /
    exact `$0.10` / just below / source-zero / high quote of a sub-threshold
    pile.
    """
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    # dormant sub-floor receipt: 0.05 bravo -> $0.05
    dormant_amount = 5 * 10**16
    _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                  dormant_amount, bob, auction_house, green_token,
                  savings_green)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_DORMANT

    # a genuinely tiny pile that only a wrong-high quote can lift
    tiny = boa.load("contracts/mock/MockErc20.vy", governance, "G10 Tiny",
                    "G10T", 18, 0, name="g10_tiny")
    tiny.mint(alice, EIGHTEEN_DECIMALS, sender=governance.address)
    sync_deployed_token(tiny)
    mock_price_source.setPrice(tiny, EIGHTEEN_DECIMALS)
    _record_claim(stability_pool, alpha_token, tiny, alice, 100, bob,
                  auction_house, green_token, savings_green)
    assert stability_pool.getClaimAssetState(
        alpha_token, tiny) == CLAIM_ASSET_DORMANT

    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    ledger_before = (_claim_ledger(stability_pool, alpha_token, bravo_token),
                     _claim_ledger(stability_pool, alpha_token, tiny))
    stability_pool.pause(True, sender=switchboard_alpha.address)

    # empty / zero address / unknown asset / zero pair balance -> no-ops
    stability_pool.activateClaimAssets(alpha_token, [], sender=alice)
    stability_pool.activateClaimAssets(
        alpha_token, [ZERO_ADDRESS, alpha_token, green_token], sender=alice)
    assert filter_logs(stability_pool, "ClaimAssetActivated") == []
    assert _active_list(stability_pool, alpha_token)[:2] == (0, 0)

    # just below $0.10 -> skip; source zero -> skip
    stability_pool.activateClaimAssets(alpha_token, [bravo_token],
                                       sender=alice)
    assert filter_logs(stability_pool, "ClaimAssetActivated") == []
    mock_price_source.setPrice(bravo_token, 0)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token],
                                       sender=alice)
    assert filter_logs(stability_pool, "ClaimAssetActivated") == []
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_DORMANT

    # one wei of USD below $0.10 -> still skipped
    exact_price = ACTIVATION_THRESHOLD * EIGHTEEN_DECIMALS // dormant_amount
    assert dormant_amount * exact_price // EIGHTEEN_DECIMALS == (
        ACTIVATION_THRESHOLD)
    mock_price_source.setPrice(bravo_token, exact_price - 1)
    assert dormant_amount * (exact_price - 1) // EIGHTEEN_DECIMALS == (
        ACTIVATION_THRESHOLD - 1)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token],
                                       sender=alice)
    assert filter_logs(stability_pool, "ClaimAssetActivated") == []
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_DORMANT

    # exact $0.10 -> activates; duplicates emit exactly one event
    mock_price_source.setPrice(bravo_token, exact_price)
    stability_pool.activateClaimAssets(
        alpha_token, [bravo_token, bravo_token], sender=alice)
    logs = filter_logs(stability_pool, "ClaimAssetActivated")
    assert len(logs) == 1
    assert logs[0].claimAsset == bravo_token.address
    assert logs[0].activeCount == 1
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE

    # already active -> silent skip
    stability_pool.activateClaimAssets(alpha_token, [bravo_token],
                                       sender=alice)
    assert filter_logs(stability_pool, "ClaimAssetActivated") == []

    # a truly sub-threshold pile does activate when the helper sees >= $0.10
    mock_price_source.setPrice(tiny, 10**36)  # 100 wei -> $100
    stability_pool.activateClaimAssets(alpha_token, [tiny], sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token, tiny) == CLAIM_ASSET_ACTIVE

    # nothing moved
    assert (_claim_ledger(stability_pool, alpha_token, bravo_token),
            _claim_ledger(stability_pool, alpha_token, tiny)) == ledger_before


def test_can_activate_claim_asset_is_not_exported_on_stability_pool(
    stability_pool,
):
    """`canActivateClaimAsset` lives on the StabVault module and is absent from
    `StabilityPool.vy` exports and `scripts/abis/StabilityPool.json`.
    """
    assert not hasattr(stability_pool, "canActivateClaimAsset")
    abi_names = {entry.get("name") for entry in stability_pool.abi}
    assert "canActivateClaimAsset" not in abi_names
    for exported in ("pruneClaimableAssets", "activateClaimAssets",
                     "getClaimAssetState", "canAcceptLiquidationAsset",
                     "pause"):
        assert exported in abi_names


def test_dormant_pile_is_still_claimable_by_a_funded_shareholder(
    stability_pool, alpha_token, alpha_token_whale, bravo_token,
    bravo_token_whale, bob, alice, teller, auction_house, mock_price_source,
    green_token, savings_green, setGeneralConfig, setAssetConfig, vault_book,
):
    """Below-floor receipt stays dormant (omitted from NAV) but remains
    claimable by a funded shareholder with claim config on.
    """
    from conf_utils import claim_from_stability_pool

    setGeneralConfig()
    setAssetConfig(bravo_token)
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    vault_id = vault_book.getRegId(stability_pool)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    pile = ACTIVATION_THRESHOLD - 1
    _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                  pile, bob, auction_house, green_token, savings_green)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_DORMANT
    # Below-floor pile is omitted from NAV, but the pool still owes it.
    assert stability_pool.getTotalValue(alpha_token) == alpha_token.balanceOf(
        stability_pool
    )
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == pile

    before = bravo_token.balanceOf(bob)
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token,
                              sender=bob)
    assert bravo_token.balanceOf(bob) - before == pile
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
    assert stability_pool.totalClaimableBalances(bravo_token) == 0


def test_green_as_claim_asset_uses_the_one_to_one_branch(
    stability_pool, alpha_token, alpha_token_whale, bob, alice, teller,
    auction_house, mock_price_source, green_token, savings_green,
    credit_engine, switchboard_alpha,
):
    """GREEN (not sGREEN) prices 1:1 inside `_getUsdValue`, so the thresholds
    are raw token amounts.
    """
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    green_token.mint(alice, EIGHTEEN_DECIMALS, sender=credit_engine.address)

    # a sub-floor GREEN receipt stays dormant: 0.05 GREEN == $0.05
    _record_claim(stability_pool, alpha_token, green_token, alice,
                  RETENTION_THRESHOLD, bob, auction_house, green_token,
                  savings_green)
    assert stability_pool.getClaimAssetState(
        alpha_token, green_token) == CLAIM_ASSET_DORMANT

    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    # top it up to exactly $0.10 while empty; receipt seating is unchanged
    _record_claim(stability_pool, alpha_token, green_token, alice,
                  ACTIVATION_THRESHOLD - RETENTION_THRESHOLD, bob,
                  auction_house, green_token, savings_green)
    assert stability_pool.getClaimAssetState(
        alpha_token, green_token) == CLAIM_ASSET_ACTIVE

    # exactly at RETENTION it survives a prune; one wei below it does not
    stability_pool.pruneClaimableAssets(alpha_token, [green_token],
                                        sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token, green_token) == CLAIM_ASSET_ACTIVE

    boa.env.set_storage(
        stability_pool.address,
        _claimable_balance_slot(green_token, alpha_token),
        RETENTION_THRESHOLD - 1,
    )
    stability_pool.pruneClaimableAssets(alpha_token, [green_token],
                                        sender=alice)
    log = filter_logs(stability_pool, "ClaimAssetDeactivated")[0]
    assert log.reason == DEACTIVATION_DUST
    assert stability_pool.getClaimAssetState(
        alpha_token, green_token) == CLAIM_ASSET_DORMANT


def test_cross_cohort_custody_deficit_blocks_activate_on_the_other_cohort(
    stability_pool, alpha_token, bravo_token, alpha_token_whale,
    bravo_token_whale, bob, alice, governance, teller, auction_house,
    mock_price_source, green_token, savings_green, switchboard_alpha,
):
    """The activate custody assert reads the GLOBAL liability, so a deficit
    created by cohort B blocks activation in cohort A.
    """
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    _seed_stab(stability_pool, bravo_token, bravo_token_whale, bob, teller,
               mock_price_source)
    shared = boa.load("contracts/mock/MockErc20.vy", governance, "G10 Cross",
                      "G10X", 18, 0, name="g10_cross")
    shared.mint(alice, 1000 * EIGHTEEN_DECIMALS, sender=governance.address)
    sync_deployed_token(shared)
    mock_price_source.setPrice(shared, EIGHTEEN_DECIMALS)

    # cohort A: dormant sub-floor row. cohort B: large active row.
    _record_claim(stability_pool, alpha_token, shared, alice,
                  5 * 10**16, bob, auction_house, green_token, savings_green)
    _record_claim(stability_pool, bravo_token, shared, alice,
                  50 * EIGHTEEN_DECIMALS, bob, auction_house, green_token,
                  savings_green)
    assert stability_pool.getClaimAssetState(
        alpha_token, shared) == CLAIM_ASSET_DORMANT
    assert stability_pool.getClaimAssetState(
        bravo_token, shared) == CLAIM_ASSET_ACTIVE

    b_pair = stability_pool.claimableBalances(bravo_token, shared)
    global_liability = stability_pool.totalClaimableBalances(shared)
    _exit_cohort(stability_pool, alpha_token, bob, teller)

    # B's custody disappears (impersonated pool transfer models the loss).
    shared.transfer(alice, EIGHTEEN_DECIMALS, sender=stability_pool.address)
    mock_price_source.setPrice(shared, 4 * EIGHTEEN_DECIMALS)  # A's pile -> $0.20

    stability_pool.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("claim custody deficit"):
        stability_pool.activateClaimAssets(alpha_token, [shared], sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token, shared) == CLAIM_ASSET_DORMANT

    # prune on A is still a silent no-op and touches nothing globally
    stability_pool.pruneClaimableAssets(alpha_token, [shared], sender=alice)
    assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []
    assert stability_pool.claimableBalances(bravo_token, shared) == b_pair
    assert stability_pool.totalClaimableBalances(shared) == global_liability

    # repaired-custody positive control
    shared.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alice)
    stability_pool.activateClaimAssets(alpha_token, [shared], sender=alice)
    assert stability_pool.getClaimAssetState(
        alpha_token, shared) == CLAIM_ASSET_ACTIVE
    assert stability_pool.claimableBalances(bravo_token, shared) == b_pair
    assert stability_pool.totalClaimableBalances(shared) == global_liability


def _mk_claim_token(governance, holder, tag):
    tok = boa.load("contracts/mock/MockErc20.vy", governance, f"G10 {tag}",
                   f"G10{tag}", 18, 0, name=f"g10_cap_{tag}")
    tok.mint(holder, 1000 * EIGHTEEN_DECIMALS, sender=governance.address)
    sync_deployed_token(tok)
    return tok


def test_activate_capacity_ordering_decides_who_takes_the_last_slot(
    stability_pool, alpha_token, alpha_token_whale, bob, alice, sally,
    governance, teller, auction_house, mock_price_source, green_token,
    savings_green, switchboard_alpha,
):
    """19 active, two eligible dormant candidates, one free slot.

    Array order inside one call, and caller order across two calls, decide
    which candidate is admitted. The loser stays dormant with no revert.
    Also measures `canAcceptLiquidationAsset` only while unpaused.
    """
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source, 200 * EIGHTEEN_DECIMALS)

    # Seed the two dormant candidates BEFORE filling the active list: at
    # capacity a new or dormant receipt reverts.
    low = _mk_claim_token(governance, alice, "LOW")
    high = _mk_claim_token(governance, alice, "HIGH")
    for tok, amt in ((low, 5 * 10**16), (high, 9 * 10**16)):
        mock_price_source.setPrice(tok, EIGHTEEN_DECIMALS)
        _record_claim(stability_pool, alpha_token, tok, alice, amt, bob,
                      auction_house, green_token, savings_green)
        assert stability_pool.getClaimAssetState(
            alpha_token, tok) == CLAIM_ASSET_DORMANT

    occupiers = []
    for i in range(19):
        tok = _mk_claim_token(governance, alice, f"A{i}")
        mock_price_source.setPrice(tok, EIGHTEEN_DECIMALS)
        _record_claim(stability_pool, alpha_token, tok, alice,
                      ACTIVATION_THRESHOLD - 1, bob, auction_house, green_token,
                      savings_green)
        occupiers.append(tok)
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0

    # Acceptance snapshot while UNPAUSED with a free slot.
    probe = _mk_claim_token(governance, alice, "PROBE")
    mock_price_source.setPrice(probe, EIGHTEEN_DECIMALS)
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, probe)

    # both candidates are eligible: $0.10 and $9.00
    mock_price_source.setPrice(low, 2 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(high, 100 * EIGHTEEN_DECIMALS)

    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    floor = _exact_floor(ACTIVATION_THRESHOLD - 1)
    for tok in occupiers:
        mock_price_source.setPrice(tok, floor)
    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.activateClaimAssets(alpha_token, occupiers[:15], sender=alice)
    stability_pool.activateClaimAssets(alpha_token, occupiers[15:], sender=alice)
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 19
    # A measurement taken during pause is unconditionally False.
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, probe)

    with boa.env.anchor():
        stability_pool.activateClaimAssets(alpha_token, [low, high],
                                           sender=alice)
        logs = filter_logs(stability_pool, "ClaimAssetActivated")
        assert [log.claimAsset for log in logs] == [low.address]
        assert stability_pool.getClaimAssetState(
            alpha_token, low) == CLAIM_ASSET_ACTIVE
        assert stability_pool.getClaimAssetState(
            alpha_token, high) == CLAIM_ASSET_DORMANT
        assert stability_pool.getNumActiveClaimAssets(alpha_token) == 20

    with boa.env.anchor():
        stability_pool.activateClaimAssets(alpha_token, [high, low],
                                           sender=alice)
        logs = filter_logs(stability_pool, "ClaimAssetActivated")
        assert [log.claimAsset for log in logs] == [high.address]
        assert stability_pool.getClaimAssetState(
            alpha_token, high) == CLAIM_ASSET_ACTIVE
        assert stability_pool.getClaimAssetState(
            alpha_token, low) == CLAIM_ASSET_DORMANT

    with boa.env.anchor():
        # separate transactions: the second caller finds the slot gone
        stability_pool.activateClaimAssets(alpha_token, [high], sender=alice)
        stability_pool.activateClaimAssets(alpha_token, [low], sender=sally)
        assert filter_logs(stability_pool, "ClaimAssetActivated") == []
        assert stability_pool.getClaimAssetState(
            alpha_token, low) == CLAIM_ASSET_DORMANT

    # take the last slot for real, then measure acceptance while UNPAUSED
    stability_pool.activateClaimAssets(alpha_token, [high], sender=alice)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 20
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, probe)

    # No arbitrary eviction: every active row is >= RETENTION, so a full
    # scoped prune of all twenty removes nothing.
    active_now = occupiers + [high]
    for batch in (active_now[:15], active_now[15:]):
        stability_pool.pruneClaimableAssets(alpha_token, batch, sender=sally)
        assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 20

    # Freeing a slot: one occupier falls below $0.05 and is pruned unpaused.
    mock_price_source.setPrice(occupiers[0], 10**15)
    stability_pool.pruneClaimableAssets(alpha_token, [occupiers[0]],
                                        sender=sally)
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 19
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, probe)

    # Admit the loser while the book is still empty; a live book cannot seat.
    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.activateClaimAssets(alpha_token, [low], sender=sally)
    assert stability_pool.getClaimAssetState(
        alpha_token, low) == CLAIM_ASSET_ACTIVE
    stability_pool.pause(False, sender=switchboard_alpha.address)

    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address,
    )
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, probe)

    # thin post-maintenance measurement: NAV usable, new deposit works
    assert stability_pool.getTotalValue(alpha_token) != 0
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS,
                         sender=alpha_token_whale)
    assert stability_pool.depositTokensInVault(
        sally, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address,
    ) == EIGHTEEN_DECIMALS


def test_prune_retention_band_and_paused_call_are_independent_of_pause(
    stability_pool, alpha_token, alpha_token_whale, bravo_token,
    bravo_token_whale, bob, alice, teller, auction_house, mock_price_source,
    green_token, savings_green, switchboard_alpha,
):
    """Prune has no pause check. Independently priced bands:
    `>= $0.10` stays, `$0.05 <= x < $0.10` stays, `< $0.05` goes -- and the
    outcome is identical paused and unpaused.
    """
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    pile = ACTIVATION_THRESHOLD - 1
    _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                  pile, bob, auction_house, green_token, savings_green)
    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    mock_price_source.setPrice(bravo_token, _exact_floor(pile))
    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=alice)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    index = stability_pool.indexOfClaimableAsset(alpha_token, bravo_token)
    assert index != 0

    # >= $0.10 (a high positive quote) -- retained
    mock_price_source.setPrice(bravo_token, 5 * EIGHTEEN_DECIMALS)  # $5.00
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token],
                                        sender=alice)
    assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []

    # $0.05 <= x < $0.10 -- retained, both paused and unpaused
    for price in (_exact_floor_usd(pile, RETENTION_THRESHOLD),
                  _exact_floor_usd(pile, ACTIVATION_THRESHOLD - 1)):
        mock_price_source.setPrice(bravo_token, price)
        stability_pool.pruneClaimableAssets(alpha_token, [bravo_token],
                                           sender=alice)
        assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []
    stability_pool.pause(True, sender=switchboard_alpha.address)
    mock_price_source.setPrice(bravo_token, _exact_floor_usd(pile, RETENTION_THRESHOLD))
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token],
                                        sender=alice)
    assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == (
        index)

    # one wei of USD below RETENTION, still paused -- removed
    mock_price_source.setPrice(
        bravo_token, (RETENTION_THRESHOLD - 1) * EIGHTEEN_DECIMALS // pile)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token],
                                        sender=alice)
    log = filter_logs(stability_pool, "ClaimAssetDeactivated")[0]
    assert log.reason == DEACTIVATION_DUST
    assert stability_pool.isPaused()
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_DORMANT


def test_dormant_pile_is_stranded_after_a_full_cohort_exit(
    stability_pool, alpha_token, alpha_token_whale, bravo_token,
    bravo_token_whale, bob, alice, teller, auction_house, mock_price_source,
    green_token, savings_green, setGeneralConfig, setAssetConfig, vault_book,
):
    """Dormant claims are not universally recoverable.

    Once every shareholder has exited the cohort, the dormant pile has no
    claimant; a later depositor becomes the only claimant. Pricing that
    residue is Group 5's question -- recorded here as the list consequence.
    """
    from conf_utils import claim_from_stability_pool

    setGeneralConfig()
    setAssetConfig(bravo_token)
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    vault_id = vault_book.getRegId(stability_pool)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    pile = ACTIVATION_THRESHOLD - 1
    _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                  pile, bob, auction_house, green_token, savings_green)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_DORMANT

    stability_pool.withdrawTokensFromVault(
        bob, alpha_token, 2**255, bob, sender=teller.address)
    assert stability_pool.totalBalances(alpha_token) == 0
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == pile

    with boa.reverts("nothing claimed"):
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token,
                                  sender=bob)
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == pile


def test_prune_does_not_reenable_liquidation_acceptance_while_custody_is_short(
    stability_pool, alpha_token, bravo_token, alpha_token_whale,
    bravo_token_whale, bob, alice, governance, teller, auction_house,
    mock_price_source, green_token, savings_green,
):
    """Live-share dust prune must not hide a short active row from liquidation
    readiness. `canAcceptLiquidationAsset` stays false while the deficit
    remains on the iterable.
    """
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                  10 * EIGHTEEN_DECIMALS, bob, auction_house, green_token,
                  savings_green)
    probe = _mk_claim_token(governance, alice, "ACCEPT")
    mock_price_source.setPrice(probe, EIGHTEEN_DECIMALS)
    assert stability_pool.canAcceptLiquidationAsset(alpha_token, probe)

    bravo_token.transfer(alice, 1, sender=stability_pool.address)
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, probe)
    assert stability_pool.getUserAssetAndAmountAtIndex(bob, 1) == (
        alpha_token.address, 0)

    mock_price_source.setPrice(bravo_token, 10**15)
    # control: without the prune the cohort stays unavailable
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, probe)

    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token],
                                        sender=alice)
    assert bravo_token.balanceOf(stability_pool) < (
        stability_pool.totalClaimableBalances(bravo_token))

    # THE PROPERTY: an unrepaired custody deficit must keep the cohort out of
    # liquidation routing.
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, probe)
    assert stability_pool.getUserAssetAndAmountAtIndex(bob, 1) == (
        alpha_token.address, 0)


def test_empty_state_num_one_re_registers_at_index_one(
    stability_pool, alpha_token, bravo_token, alpha_token_whale,
    bravo_token_whale, bob, alice, teller, auction_house, mock_price_source,
    green_token, savings_green, switchboard_alpha,
):
    """`numClaimableAssets == 1` is the code's empty state (not `0`).

    `_registerClaimableAsset` must re-use index 1 from there and leave the
    counter at 2, with no hole and a correct NAV walk.
    """
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                  ACTIVATION_THRESHOLD - 1, bob, auction_house, green_token,
                  savings_green)
    nav_with_pile = stability_pool.getTotalValue(alpha_token)

    _exit_cohort(stability_pool, alpha_token, bob, teller)
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    mock_price_source.setPrice(bravo_token, _exact_floor(ACTIVATION_THRESHOLD - 1))
    stability_pool.pause(True, sender=switchboard_alpha.address)
    stability_pool.activateClaimAssets(alpha_token, [bravo_token], sender=alice)
    stability_pool.pause(False, sender=switchboard_alpha.address)
    mock_price_source.setPrice(bravo_token, 10**15)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token],
                                        sender=alice)
    assert stability_pool.numClaimableAssets(alpha_token) == 1
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0
    assert stability_pool.claimableAssets(alpha_token, 1) == ZERO_ADDRESS
    nav_empty = stability_pool.getTotalValue(alpha_token)
    assert nav_empty < nav_with_pile

    # a fresh receipt registers back at index 1
    alpha_token.transfer(stability_pool, EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob, alpha_token, EIGHTEEN_DECIMALS, sender=teller.address,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    _record_claim(stability_pool, alpha_token, bravo_token, bravo_token_whale,
                  EIGHTEEN_DECIMALS, bob, auction_house, green_token,
                  savings_green)
    assert stability_pool.numClaimableAssets(alpha_token) == 2
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 1
    assert stability_pool.claimableAssets(alpha_token, 1) == bravo_token.address
    assert stability_pool.claimableAssets(alpha_token, 2) == ZERO_ADDRESS
    assert stability_pool.getTotalValue(alpha_token) > nav_empty


def test_permanently_unpriced_active_row_has_no_maintenance_exit(
    stability_pool, alpha_token, bravo_token, alpha_token_whale,
    bravo_token_whale, bob, alice, governance, teller, auction_house,
    mock_price_source, green_token, savings_green, setGeneralConfig,
    setAssetConfig, vault_book, switchboard_alpha,
):
    """An active claim row whose source returns `0` is deliberately retained by
    prune, and strict NAV fails closed -- so the whole cohort's claim route is
    frozen too, including claims of a DIFFERENT, healthy claim asset.

    There is no permissionless or user-callable path that drains or delists the
    row; only price recovery does. Recorded as the list-membership consequence
    (Group 5 owns the claim economics).
    """
    from conf_utils import claim_from_stability_pool

    setGeneralConfig()
    setAssetConfig(bravo_token)
    _seed_stab(stability_pool, alpha_token, alpha_token_whale, bob, teller,
               mock_price_source)
    vault_id = vault_book.getRegId(stability_pool)
    healthy = _mk_claim_token(governance, alice, "HEALTHY")
    setAssetConfig(healthy)
    for tok, whale in ((bravo_token, bravo_token_whale), (healthy, alice)):
        mock_price_source.setPrice(tok, EIGHTEEN_DECIMALS)
        _record_claim(stability_pool, alpha_token, tok, whale,
                      10 * EIGHTEEN_DECIMALS, bob, auction_house, green_token,
                      savings_green)
        assert stability_pool.getClaimAssetState(
            alpha_token, tok) == CLAIM_ASSET_ACTIVE

    mock_price_source.setPrice(bravo_token, 0)

    # prune deliberately retains it, paused or unpaused
    for paused in (False, True):
        if paused:
            stability_pool.pause(True, sender=switchboard_alpha.address)
        stability_pool.pruneClaimableAssets(
            alpha_token, [bravo_token, healthy], sender=alice)
        assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []
    stability_pool.pause(False, sender=switchboard_alpha.address)
    assert stability_pool.getClaimAssetState(
        alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE

    # every strict-NAV route is closed, including the healthy claim asset
    with boa.reverts():
        stability_pool.getTotalValue(alpha_token)
    with boa.reverts():
        claim_from_stability_pool(teller, vault_id, alpha_token, healthy,
                                  sender=bob)
    with boa.reverts():
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token,
                                  sender=bob)
    assert not stability_pool.canAcceptLiquidationAsset(alpha_token, healthy)

    # only price recovery restores the cohort
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    assert stability_pool.getTotalValue(alpha_token) != 0
    before = healthy.balanceOf(bob)
    claim_from_stability_pool(teller, vault_id, alpha_token, healthy,
                              sender=bob)
    assert healthy.balanceOf(bob) > before
