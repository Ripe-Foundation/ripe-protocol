"""Group 5 proof: a nonzero stab-pool deposit used to commit custody with
zero shares.

`StabVault._depositTokensInVault` computes newShares via `_valueToShares`
and used to hand a zero result to `_addBalanceOnDeposit`. Teller only
checked the token amount, so the deposit committed and the tokens were
unrecoverable or donated to incumbents.

`assert newShares != 0` now reverts `cannot mint 0 shares` before
custody is booked. The window is still
`depositValue <= preDepositNav // 10**8` after a zero-share cohort with
priced claimable NAV; the adjacent +1 wei mint still succeeds.
"""

import boa
import pytest
from boa.contracts.base_evm_contract import BoaError
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from conf_utils import assert_reverted_call, clear_transient_storage


DORMANT_PRICE = 10 ** 16           # $0.01 -> 9 tokens = $0.09, below the $0.10 floor
DORMANT_TOKENS = 9 * EIGHTEEN_DECIMALS


@pytest.fixture
def zero_share_cohort_with_priced_claimable(
    stability_pool, green_token, savings_green, whale, bob, sally, teller,
    auction_house, mock_price_source, bravo_token, bravo_token_whale,
    setGeneralConfig, setAssetConfig, switchboard_alpha,
):
    """sGREEN cohort with totalShares == 0 and $9 of ACTIVE claimable.

    Built only from in-scope moves: a below-floor liquidation receipt leaves a
    dormant pair; because dormant inventory is excluded from NAV the sole holder's
    Teller withdrawal takes branch (a) and burns every share; the pair then
    appreciates and re-enters the active set through the paused permissionless
    `activateClaimAssets` maintenance route.
    """
    setGeneralConfig()
    setAssetConfig(savings_green, [1], _minDepositBalance=0,
                   _canClaimInStabPool=False, _canRedeemInStabPool=False)
    setAssetConfig(bravo_token)
    sg = savings_green.address

    green_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller.address, MAX_UINT256, sender=bob)
    teller.convertToSavingsGreenAndDepositIntoStabPool(
        bob, 100 * EIGHTEEN_DECIMALS, sender=bob)
    clear_transient_storage()

    mock_price_source.setPrice(bravo_token, DORMANT_PRICE)
    bravo_token.transfer(stability_pool.address, DORMANT_TOKENS, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        sg, 1, bravo_token.address, DORMANT_TOKENS, ZERO_ADDRESS,
        green_token.address, sg, sender=auction_house.address)
    clear_transient_storage()
    assert stability_pool.getNumActiveClaimAssets(sg) == 0

    teller.withdraw(savings_green, MAX_UINT256, bob, stability_pool, sender=bob)
    clear_transient_storage()
    assert stability_pool.totalBalances(sg) == 0

    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    stability_pool.pause(True, sender=switchboard_alpha.address)
    clear_transient_storage()
    stability_pool.activateClaimAssets(sg, [bravo_token.address], sender=sally)
    clear_transient_storage()
    stability_pool.pause(False, sender=switchboard_alpha.address)
    clear_transient_storage()

    assert stability_pool.getNumActiveClaimAssets(sg) == 1
    assert stability_pool.getTotalValue(sg) == DORMANT_TOKENS
    assert savings_green.balanceOf(stability_pool.address) == 0
    return sg


def _convert(teller, green_token, savings_green, whale, user, amount):
    green_token.transfer(user, amount, sender=whale)
    green_token.approve(teller.address, MAX_UINT256, sender=user)
    out = teller.convertToSavingsGreenAndDepositIntoStabPool(user, amount, sender=user)
    clear_transient_storage()
    return out


def test_nonzero_deposit_must_not_commit_custody_with_zero_shares(
    zero_share_cohort_with_priced_claimable, stability_pool, green_token,
    savings_green, whale, sally, teller,
):
    sg = zero_share_cohort_with_priced_claimable
    nav = stability_pool.getTotalValue(sg)
    ceiling = nav // 10 ** 8          # 9e10 sGREEN wei at a $9 cohort NAV

    # Adjacent positive control: one wei above the ceiling mints a share.
    with boa.env.anchor():
        committed = _convert(teller, green_token, savings_green, whale, sally, ceiling + 1)
        assert committed == ceiling + 1
        assert stability_pool.userBalances(sally, sg) == 1
        assert stability_pool.getTotalUserValue(sally, sg) != 0

    green_token.transfer(sally, ceiling, sender=whale)
    green_token.approve(teller.address, MAX_UINT256, sender=sally)
    payer_green = green_token.balanceOf(sally)
    payer_sgreen = savings_green.balanceOf(sally)
    pool_custody = savings_green.balanceOf(stability_pool.address)
    shares_before = stability_pool.userBalances(sally, sg)
    with pytest.raises(BoaError) as exc_info:
        teller.convertToSavingsGreenAndDepositIntoStabPool(sally, ceiling, sender=sally)
    assert_reverted_call(exc_info.value, "cannot mint 0 shares", teller)
    clear_transient_storage()
    assert green_token.balanceOf(sally) == payer_green
    assert savings_green.balanceOf(sally) == payer_sgreen
    assert savings_green.balanceOf(stability_pool.address) == pool_custody
    assert stability_pool.userBalances(sally, sg) == shares_before


def test_zero_share_depositor_cannot_recover_the_committed_tokens(
    zero_share_cohort_with_priced_claimable, stability_pool, green_token,
    savings_green, whale, sally, teller, vault_book, bravo_token,
):
    """Losing convert reverts; sally has no shares and no committed pool custody."""
    sg = zero_share_cohort_with_priced_claimable
    ceiling = stability_pool.getTotalValue(sg) // 10 ** 8
    pool_custody = savings_green.balanceOf(stability_pool.address)
    with pytest.raises(BoaError) as exc_info:
        _convert(teller, green_token, savings_green, whale, sally, ceiling)
    assert_reverted_call(exc_info.value, "cannot mint 0 shares", teller)
    clear_transient_storage()
    assert stability_pool.userBalances(sally, sg) == 0
    assert savings_green.balanceOf(stability_pool.address) == pool_custody


def test_launch_min_deposit_balance_blocks_this_instance(
    zero_share_cohort_with_priced_claimable, stability_pool, green_token,
    savings_green, whale, sally, teller, setAssetConfig,
):
    """Control: the launch `minDepositBalance` of 1e16 keeps this cohort safe.

    It is a size floor, not a share-mint guard -- the window reopens for any
    cohort whose zero-share NAV exceeds `minDepositBalance * 10**8` ($1.06M at
    launch parameters).
    """
    setAssetConfig(savings_green, [1], _minDepositBalance=10 ** 16,
                   _canClaimInStabPool=False, _canRedeemInStabPool=False)
    ceiling = stability_pool.getTotalValue(zero_share_cohort_with_priced_claimable) // 10 ** 8
    assert ceiling < 10 ** 16
    with boa.reverts("too small a balance"):
        _convert(teller, green_token, savings_green, whale, sally, ceiling)
    clear_transient_storage()


def test_borrow_enter_stab_must_not_commit_zero_shares(
    zero_share_cohort_with_priced_claimable, stability_pool, green_token,
    savings_green, sally, teller, alpha_token, alpha_token_whale,
    setAssetConfig, setGeneralDebtConfig, performDeposit, ledger,
    credit_engine, mission_control, mock_price_source,
):
    sg = zero_share_cohort_with_priced_claimable
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()
    performDeposit(sally, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    clear_transient_storage()
    assert mission_control.preferredStabVaultId() == 1

    debt_before = ledger.userDebt(sally)
    interval_before = ledger.borrowIntervals(sally)
    green_supply = green_token.totalSupply()
    ce_green = green_token.balanceOf(credit_engine)
    ce_sgreen = savings_green.balanceOf(credit_engine)
    teller_green = green_token.balanceOf(teller)
    teller_sgreen = savings_green.balanceOf(teller)
    pool_custody = savings_green.balanceOf(stability_pool)
    pool_shares = stability_pool.totalBalances(sg)
    sally_green = green_token.balanceOf(sally)
    sally_sgreen = savings_green.balanceOf(sally)
    sally_shares = stability_pool.userBalances(sally, sg)

    with pytest.raises(BoaError) as exc_info:
        teller.borrow(10**9 + 1, sally, True, True, sender=sally)
    assert_reverted_call(exc_info.value, "cannot mint 0 shares", teller)
    clear_transient_storage()

    assert ledger.userDebt(sally) == debt_before
    assert ledger.borrowIntervals(sally) == interval_before
    assert green_token.totalSupply() == green_supply
    assert green_token.balanceOf(credit_engine) == ce_green
    assert savings_green.balanceOf(credit_engine) == ce_sgreen
    assert green_token.balanceOf(teller) == teller_green
    assert savings_green.balanceOf(teller) == teller_sgreen
    assert savings_green.balanceOf(stability_pool) == pool_custody
    assert stability_pool.totalBalances(sg) == pool_shares
    assert green_token.balanceOf(sally) == sally_green
    assert savings_green.balanceOf(sally) == sally_sgreen
    assert stability_pool.userBalances(sally, sg) == sally_shares
