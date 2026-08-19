"""Group 5 proof: a dust sGREEN redeem wrap used to hard-revert a
documented soft-skip row and roll back committed siblings.

`StabVault._redeemFromStabilityPool` is annotated fail-soft and returns 0
for every other unsatisfiable condition. The sGREEN wrap used to call
`sGREEN.deposit` with no dust guard, so `convertToShares(redeemAmount) == 0`
reverted the whole batch. The wrap is now skipped in that case; sibling
rows still settle, and an all-dust batch reverts `no redemptions occurred`.
The refund-side `> 10 ** 9` cutoff at `_handleGreenForUser` is unchanged.
"""

import boa
import pytest
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from conf_utils import clear_transient_storage, claim_from_stability_pool


PILE = 40 * EIGHTEEN_DECIMALS


@pytest.fixture
def stab_cohort(
    stability_pool, green_token, savings_green, whale, bob, teller, vault_book,
    auction_house, mock_price_source, bravo_token, bravo_token_whale,
    charlie_token, charlie_token_whale, setGeneralConfig, setAssetConfig,
):
    """Launch-shaped cohort: sGREEN stability asset, WETH-like claim inventory.

    bravo is priced at exactly $1.00 with 18 decimals, the price/decimal shape
    that makes a one-wei claim residue worth one wei of GREEN.
    """
    setGeneralConfig()
    setAssetConfig(savings_green, [1], _minDepositBalance=10 ** 16,
                   _canClaimInStabPool=False, _canRedeemInStabPool=False)
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
    sg = savings_green.address

    green_token.transfer(bob, 200 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller.address, 200 * EIGHTEEN_DECIMALS, sender=bob)
    teller.convertToSavingsGreenAndDepositIntoStabPool(
        bob, 200 * EIGHTEEN_DECIMALS, sender=bob)
    clear_transient_storage()

    for tok, tok_whale, amt, stab_out in (
        (bravo_token, bravo_token_whale, PILE, 30 * EIGHTEEN_DECIMALS),
        (charlie_token, charlie_token_whale, 30 * 10 ** 6, 20 * EIGHTEEN_DECIMALS),
    ):
        tok.transfer(stability_pool.address, amt, sender=tok_whale)
        stability_pool.swapForLiquidatedCollateral(
            sg, stab_out, tok.address, amt, ZERO_ADDRESS, green_token.address, sg,
            sender=auction_house.address,
        )
        clear_transient_storage()
    return vault_book.getRegId(stability_pool.address)


def _fund(green_token, teller, whale, user, amount):
    green_token.transfer(user, amount, sender=whale)
    green_token.approve(teller.address, MAX_UINT256, sender=user)


def _accrue_sgreen_yield(green_token, savings_green, whale, amount):
    """Any Endaoment yield puts the sGREEN rate above parity."""
    green_token.transfer(savings_green.address, amount, sender=whale)


def test_committed_redeem_row_survives_a_dust_remainder_on_a_later_row(
    stab_cohort, stability_pool, green_token, savings_green, whale, sally, teller,
    bravo_token,
):
    """Row 1 commits; row 2 is charged 1 wei. Row 1 must survive."""
    vault_id = stab_cohort
    _accrue_sgreen_yield(green_token, savings_green, whale, 100 * EIGHTEEN_DECIMALS)
    assert savings_green.convertToAssets(EIGHTEEN_DECIMALS) > EIGHTEEN_DECIMALS
    assert savings_green.convertToShares(1) == 0  # the trigger condition

    _fund(green_token, teller, whale, sally, 500 * EIGHTEEN_DECIMALS)
    rows = [(bravo_token.address, 10 * EIGHTEEN_DECIMALS),
            (bravo_token.address, MAX_UINT256)]

    # Adjacent positive control: a 2-wei remainder settles fine.
    with boa.env.anchor():
        spent = teller.redeemManyFromStabilityPool(
            vault_id, rows, 10 * EIGHTEEN_DECIMALS + 2, sally, False, False, True,
            sender=sally)
        clear_transient_storage()
        assert spent == 10 * EIGHTEEN_DECIMALS + 2

    # Safety property: a row the contract cannot satisfy must soft-skip; it must
    # not destroy a sibling row that already committed. One wei less of budget.
    sally_green_before = green_token.balanceOf(sally)
    sally_sgreen_before = savings_green.balanceOf(sally)
    spent = teller.redeemManyFromStabilityPool(
        vault_id, rows, 10 * EIGHTEEN_DECIMALS + 1, sally, False, False, True,
        sender=sally)
    clear_transient_storage()
    assert spent == 10 * EIGHTEEN_DECIMALS
    assert stability_pool.claimableBalances(
        savings_green.address, bravo_token.address) == PILE - 10 * EIGHTEEN_DECIMALS
    assert sally_green_before - green_token.balanceOf(sally) == 10 * EIGHTEEN_DECIMALS
    assert savings_green.balanceOf(sally) == sally_sgreen_before
    assert green_token.balanceOf(stability_pool.address) == 0


def test_one_wei_claim_residue_does_not_brick_sibling_redemption_rows(
    stab_cohort, stability_pool, green_token, savings_green, whale, sally, alice,
    teller, bravo_token, charlie_token,
):
    """A third party leaves a one-wei residue; that row must soft-skip.

    Historically every later row naming that asset reverted
    `cannot receive 0 shares` and destroyed the batch. The dust wrap now
    continues; an unrelated sibling row in the same batch still settles.
    """
    vault_id = stab_cohort
    sg = savings_green.address
    _accrue_sgreen_yield(green_token, savings_green, whale, 100 * EIGHTEEN_DECIMALS)
    _fund(green_token, teller, whale, alice, 500 * EIGHTEEN_DECIMALS)
    _fund(green_token, teller, whale, sally, 500 * EIGHTEEN_DECIMALS)

    teller.redeemManyFromStabilityPool(
        vault_id, [(bravo_token.address, MAX_UINT256)], PILE - 1, alice,
        False, False, True, sender=alice)
    clear_transient_storage()
    assert stability_pool.claimableBalances(sg, bravo_token.address) == 1
    assert bravo_token.balanceOf(stability_pool.address) == 1

    # Control: an unrelated claim asset still redeems on its own.
    with boa.env.anchor():
        assert teller.redeemManyFromStabilityPool(
            vault_id, [(charlie_token.address, MAX_UINT256)],
            100 * EIGHTEEN_DECIMALS, sally, False, False, True, sender=sally) != 0
        clear_transient_storage()

    # Safety property: an unsatisfiable bravo row must soft-skip, leaving the
    # charlie row in the same batch to settle normally.
    leftover_assets = 70 * EIGHTEEN_DECIMALS
    expected_sgreen = savings_green.convertToShares(leftover_assets)
    sally_sgreen_before = savings_green.balanceOf(sally)
    spent = teller.redeemManyFromStabilityPool(
        vault_id,
        [(charlie_token.address, MAX_UINT256), (bravo_token.address, MAX_UINT256)],
        100 * EIGHTEEN_DECIMALS, sally, False, False, True, sender=sally)
    clear_transient_storage()
    assert spent == 30 * EIGHTEEN_DECIMALS
    assert stability_pool.claimableBalances(sg, bravo_token.address) == 1
    sgreen_delta = savings_green.balanceOf(sally) - sally_sgreen_before
    assert sgreen_delta == expected_sgreen
    assets_back = savings_green.convertToAssets(sgreen_delta)
    assert assets_back in (leftover_assets, leftover_assets - 1)
    assert green_token.balanceOf(stability_pool.address) == 0


def test_same_sequences_are_safe_while_sgreen_is_at_parity(
    stab_cohort, stability_pool, green_token, savings_green, whale, sally, alice,
    teller, bravo_token,
):
    """Adjacent positive control: at rate == 1.0 both sequences succeed.

    This isolates the defect to `convertToShares(redeemAmount) == 0`, not to
    the batch shape or the residue itself.
    """
    vault_id = stab_cohort
    sg = savings_green.address
    assert savings_green.convertToAssets(EIGHTEEN_DECIMALS) == EIGHTEEN_DECIMALS
    _fund(green_token, teller, whale, alice, 500 * EIGHTEEN_DECIMALS)
    _fund(green_token, teller, whale, sally, 500 * EIGHTEEN_DECIMALS)

    with boa.env.anchor():
        spent = teller.redeemManyFromStabilityPool(
            vault_id,
            [(bravo_token.address, 10 * EIGHTEEN_DECIMALS),
             (bravo_token.address, MAX_UINT256)],
            10 * EIGHTEEN_DECIMALS + 1, sally, False, False, True, sender=sally)
        clear_transient_storage()
        assert spent == 10 * EIGHTEEN_DECIMALS + 1

    teller.redeemManyFromStabilityPool(
        vault_id, [(bravo_token.address, MAX_UINT256)], PILE - 1, alice,
        False, False, True, sender=alice)
    clear_transient_storage()
    assert stability_pool.claimableBalances(sg, bravo_token.address) == 1
    assert teller.redeemManyFromStabilityPool(
        vault_id, [(bravo_token.address, MAX_UINT256)], 100 * EIGHTEEN_DECIMALS,
        sally, False, False, True, sender=sally) == 1
    clear_transient_storage()


def test_g5_dust_wrap_revert_rolls_back_committed_row(
    stab_cohort, stability_pool, green_token, savings_green, whale, sally, teller,
    bravo_token,
):
    """Dust row skips; sibling stays committed (same balances as the first test)."""
    vault_id = stab_cohort
    _accrue_sgreen_yield(green_token, savings_green, whale, 100 * EIGHTEEN_DECIMALS)
    _fund(green_token, teller, whale, sally, 500 * EIGHTEEN_DECIMALS)
    rows = [(bravo_token.address, 10 * EIGHTEEN_DECIMALS),
            (bravo_token.address, MAX_UINT256)]

    pair_before = stability_pool.claimableBalances(
        savings_green.address, bravo_token.address)
    sally_bravo_before = bravo_token.balanceOf(sally)
    sally_green_before = green_token.balanceOf(sally)
    sally_sgreen_before = savings_green.balanceOf(sally)

    spent = teller.redeemManyFromStabilityPool(
        vault_id, rows, 10 * EIGHTEEN_DECIMALS + 1, sally, False, False, True,
        sender=sally)
    clear_transient_storage()

    assert spent == 10 * EIGHTEEN_DECIMALS
    assert stability_pool.claimableBalances(
        savings_green.address, bravo_token.address) == pair_before - 10 * EIGHTEEN_DECIMALS
    assert bravo_token.balanceOf(sally) - sally_bravo_before == 10 * EIGHTEEN_DECIMALS
    assert sally_green_before - green_token.balanceOf(sally) == 10 * EIGHTEEN_DECIMALS
    assert savings_green.balanceOf(sally) == sally_sgreen_before
    assert green_token.balanceOf(stability_pool.address) == 0


def test_g5_one_wei_residue_is_cleared_by_shareholder_claim(
    stab_cohort, stability_pool, green_token, savings_green, whale, bob, alice,
    teller, bravo_token,
):
    """An ordinary shareholder claim clears the 1-wei residue."""
    vault_id = stab_cohort
    sg = savings_green.address
    _accrue_sgreen_yield(green_token, savings_green, whale, 100 * EIGHTEEN_DECIMALS)
    _fund(green_token, teller, whale, alice, 500 * EIGHTEEN_DECIMALS)
    teller.redeemManyFromStabilityPool(
        vault_id, [(bravo_token.address, MAX_UINT256)], PILE - 1, alice,
        False, False, True, sender=alice)
    clear_transient_storage()
    assert stability_pool.claimableBalances(sg, bravo_token.address) == 1

    bob_bravo_before = bravo_token.balanceOf(bob)
    claimed = claim_from_stability_pool(
        teller, vault_id, savings_green, bravo_token, sender=bob,
    )
    clear_transient_storage()
    assert claimed == 1
    assert bravo_token.balanceOf(bob) - bob_bravo_before == 1
    assert stability_pool.claimableBalances(sg, bravo_token.address) == 0


def test_g5_weth_priced_one_wei_residue_settles_at_ordinary_sgreen_rate(
    stab_cohort, stability_pool, green_token, savings_green, whale, alice, teller,
    bravo_token, mock_price_source,
):
    """1-wei residue of a ~$2k 18-dec asset + large GREEN budget does not wrap-revert
    at an ordinary post-yield sGREEN rate. `_getAssetAmount` is nonzero; redeemAmount
    is ~2000 GREEN wei; convertToShares(2000) != 0. Launch-WETH DoS is rate-dependent,
    not a blanket `_getAssetAmount == 0` skip.
    """
    vault_id = stab_cohort
    sg = savings_green.address
    _accrue_sgreen_yield(green_token, savings_green, whale, 100 * EIGHTEEN_DECIMALS)
    _fund(green_token, teller, whale, alice, 500 * EIGHTEEN_DECIMALS)
    teller.redeemManyFromStabilityPool(
        vault_id, [(bravo_token.address, MAX_UINT256)], PILE - 1, alice,
        False, False, True, sender=alice)
    clear_transient_storage()
    assert stability_pool.claimableBalances(sg, bravo_token.address) == 1

    mock_price_source.setPrice(bravo_token, 2000 * EIGHTEEN_DECIMALS)
    assert savings_green.convertToShares(2000) != 0

    spent = teller.redeemManyFromStabilityPool(
        vault_id, [(bravo_token.address, MAX_UINT256)],
        100 * EIGHTEEN_DECIMALS, alice, False, False, True, sender=alice)
    clear_transient_storage()
    assert spent != 0
    assert stability_pool.claimableBalances(sg, bravo_token.address) == 0


def test_g5_single_dust_only_redemption_reverts_no_redemptions_occurred(
    stab_cohort, stability_pool, green_token, savings_green, whale, sally, teller,
    bravo_token,
):
    vault_id = stab_cohort
    sg = savings_green.address
    _accrue_sgreen_yield(green_token, savings_green, whale, 100 * EIGHTEEN_DECIMALS)
    assert savings_green.convertToShares(1) == 0
    _fund(green_token, teller, whale, sally, 500 * EIGHTEEN_DECIMALS)

    pair_before = stability_pool.claimableBalances(sg, bravo_token.address)
    sally_green_before = green_token.balanceOf(sally)
    with boa.reverts("no redemptions occurred"):
        teller.redeemManyFromStabilityPool(
            vault_id, [(bravo_token.address, MAX_UINT256)], 1, sally,
            False, False, True, sender=sally)
    clear_transient_storage()
    assert green_token.balanceOf(sally) == sally_green_before
    assert stability_pool.claimableBalances(sg, bravo_token.address) == pair_before


def test_g5_same_claim_asset_second_stab_slice_still_settles_when_sgreen_wrap_is_dust(
    stab_cohort, stability_pool, green_token, savings_green, whale, sally, bob,
    teller, bravo_token, bravo_token_whale, alpha_token, alpha_token_whale,
    setAssetConfig, mock_price_source, auction_house,
):
    vault_id = stab_cohort
    sg = savings_green.address
    _accrue_sgreen_yield(green_token, savings_green, whale, 100 * EIGHTEEN_DECIMALS)
    assert savings_green.convertToShares(1) == 0
    _fund(green_token, teller, whale, sally, 500 * EIGHTEEN_DECIMALS)

    teller.redeemManyFromStabilityPool(
        vault_id, [(bravo_token.address, MAX_UINT256)], PILE - 1, sally,
        False, False, True, sender=sally)
    clear_transient_storage()
    assert stability_pool.claimableBalances(sg, bravo_token.address) == 1

    setAssetConfig(alpha_token, [1])
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    alpha_amt = 50 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, alpha_amt, sender=alpha_token_whale)
    alpha_token.approve(teller.address, alpha_amt, sender=bob)
    teller.deposit(alpha_token, alpha_amt, bob, stability_pool, sender=bob)
    clear_transient_storage()
    assert stability_pool.vaultAssets(1) == sg
    assert stability_pool.vaultAssets(2) == alpha_token.address

    alpha_bravo = 10 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool.address, alpha_bravo, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, 1, bravo_token.address, alpha_bravo, bob,
        green_token.address, sg, sender=auction_house.address)
    clear_transient_storage()
    assert stability_pool.claimableBalances(alpha_token.address, bravo_token.address) == alpha_bravo

    sally_bravo_before = bravo_token.balanceOf(sally)
    sally_green_before = green_token.balanceOf(sally)
    spent = teller.redeemManyFromStabilityPool(
        vault_id, [(bravo_token.address, MAX_UINT256)], alpha_bravo, sally,
        False, False, True, sender=sally)
    clear_transient_storage()
    assert spent == alpha_bravo
    assert stability_pool.claimableBalances(sg, bravo_token.address) == 1
    assert stability_pool.claimableBalances(alpha_token.address, bravo_token.address) == 0
    assert bravo_token.balanceOf(sally) - sally_bravo_before == alpha_bravo
    assert sally_green_before - green_token.balanceOf(sally) == alpha_bravo
