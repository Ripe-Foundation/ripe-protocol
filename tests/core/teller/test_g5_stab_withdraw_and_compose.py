"""Group 5: real-Teller Stability Pool withdraw, plus the liquidation and
last-touch composes that the mock-vault action-block tests do not cover.

Everything here runs through `Teller` against the real `StabilityPool` with
sGREEN as the stability asset (the launch shape), so the quote, the vault
arithmetic, and `_performHousekeeping` all participate.
"""

import boa
import pytest
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from conf_utils import clear_transient_storage, claim_from_stability_pool


def _convert(teller, green_token, whale, user, amount):
    green_token.transfer(user, amount, sender=whale)
    green_token.approve(teller.address, MAX_UINT256, sender=user)
    out = teller.convertToSavingsGreenAndDepositIntoStabPool(user, amount, sender=user)
    clear_transient_storage()
    return out


def _seed_claimable(stability_pool, sg, green_token, auction_house, tok, tok_whale,
                    amount, stab_out):
    """AuctionHouse-impersonating seed. Skips the Group 1 conservation path."""
    tok.transfer(stability_pool.address, amount, sender=tok_whale)
    stability_pool.swapForLiquidatedCollateral(
        sg, stab_out, tok.address, amount, ZERO_ADDRESS, green_token.address, sg,
        sender=auction_house.address)


@pytest.fixture
def launch_stab(setGeneralConfig, setAssetConfig, savings_green, bravo_token,
                mock_price_source, createDebtTerms):
    setGeneralConfig()
    setAssetConfig(savings_green, [1], _minDepositBalance=10 ** 16,
                   _debtTerms=createDebtTerms(_ltv=0, _redemptionThreshold=0,
                                              _liqThreshold=0, _liqFee=0, _borrowRate=0),
                   _shouldSwapInStabPools=False, _shouldAuctionInstantly=False,
                   _canClaimInStabPool=False, _canRedeemInStabPool=False)
    setAssetConfig(bravo_token)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)


def test_teller_stab_withdraw_conserves_value_across_both_settlement_branches(
    launch_stab, stability_pool, green_token, savings_green, whale, bob, alice,
    teller, auction_house, bravo_token, bravo_token_whale,
):
    """Branch (a) pays the whole position in sGREEN; branch (b) retains shares.

    Value is checked with an independent live conversion
    (`savings_green.convertToAssets`), not with the vault's own share maths.
    """
    sg = savings_green.address
    _convert(teller, green_token, whale, bob, 100 * EIGHTEEN_DECIMALS)
    _convert(teller, green_token, whale, alice, 100 * EIGHTEEN_DECIMALS)

    # exchange rate moves between deposit and withdraw
    green_token.transfer(savings_green.address, 100 * EIGHTEEN_DECIMALS, sender=whale)
    assert savings_green.convertToAssets(EIGHTEEN_DECIMALS) == 3 * EIGHTEEN_DECIMALS // 2

    _seed_claimable(stability_pool, sg, green_token, auction_house, bravo_token,
                    bravo_token_whale, 40 * EIGHTEEN_DECIMALS, 10 * EIGHTEEN_DECIMALS)

    unreserved = savings_green.balanceOf(stability_pool.address)
    bob_nav = stability_pool.getTotalUserValue(bob, sg)
    bob_stab_units = stability_pool.getTotalAmountForUser(bob, sg)
    assert bob_stab_units <= unreserved                     # branch (a) precondition

    with boa.env.anchor():
        got = teller.withdraw(savings_green, MAX_UINT256, bob, stability_pool, sender=bob)
        clear_transient_storage()
        # every share burns even though claimable remains for alice
        assert stability_pool.userBalances(bob, sg) == 0
        assert stability_pool.claimableBalances(sg, bravo_token.address) == 40 * EIGHTEEN_DECIMALS
        # independently valued payout matches the position it replaced, to rounding
        assert abs(savings_green.convertToAssets(got) - bob_nav) <= 2
        # alice's remaining claim is untouched
        assert abs(stability_pool.getTotalUserValue(alice, sg) - bob_nav) <= 2

    # branch (b): drain the unreserved side so it cannot cover bob's whole NAV
    _seed_claimable(stability_pool, sg, green_token, auction_house, bravo_token,
                    bravo_token_whale, 100 * EIGHTEEN_DECIMALS,
                    savings_green.balanceOf(stability_pool.address) - 10 * EIGHTEEN_DECIMALS)
    unreserved = savings_green.balanceOf(stability_pool.address)
    bob_nav = stability_pool.getTotalUserValue(bob, sg)
    assert stability_pool.getTotalAmountForUser(bob, sg) > unreserved

    got = teller.withdraw(savings_green, MAX_UINT256, bob, stability_pool, sender=bob)
    clear_transient_storage()
    assert got == unreserved                                 # only unreserved sGREEN leaves
    assert savings_green.balanceOf(stability_pool.address) == 0
    assert stability_pool.userBalances(bob, sg) != 0          # shares retained vs claimable
    remaining = stability_pool.getTotalUserValue(bob, sg)
    assert abs(remaining + savings_green.convertToAssets(got) - bob_nav) <= 2


def test_teller_stab_withdraw_is_blocked_by_the_liquidation_flag_even_once_healthy(
    launch_stab, stability_pool, green_token, savings_green, whale, bob, sally,
    teller, auction_house, bravo_token, bravo_token_whale, alpha_token,
    alpha_token_whale, mock_price_source, setAssetConfig, setGeneralDebtConfig,
    createDebtTerms, performDeposit, ledger, credit_engine, vault_book,
    mission_control, switchboard_alpha,
):
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    setAssetConfig(alpha_token, [3],
                   _debtTerms=createDebtTerms(_ltv=50_00, _liqThreshold=80_00,
                                              _liqFee=0, _borrowRate=0),
                   _shouldSwapInStabPools=False, _shouldAuctionInstantly=True)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mission_control.setShouldCheckLastTouch(True, sender=switchboard_alpha.address)
    sg = savings_green.address
    vault_id = vault_book.getRegId(stability_pool.address)

    _convert(teller, green_token, whale, bob, 100 * EIGHTEEN_DECIMALS)
    _seed_claimable(stability_pool, sg, green_token, auction_house, bravo_token,
                    bravo_token_whale, 40 * EIGHTEEN_DECIMALS, 30 * EIGHTEEN_DECIMALS)
    boa.env.time_travel(blocks=1)
    performDeposit(bob, 400 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    clear_transient_storage()
    boa.env.time_travel(blocks=1)
    teller.borrow(50 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    clear_transient_storage()

    # sGREEN ltv is 0, so the quote is unlimited while bob is merely indebted
    assert credit_engine.getMaxWithdrawableForAsset(
        bob, vault_id, sg, stability_pool.address) == MAX_UINT256

    boa.env.time_travel(blocks=1)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS // 10)
    teller.liquidateUser(bob, False, sender=sally)
    clear_transient_storage()
    assert ledger.userDebt(bob).inLiquidation

    # flagged + still in debt: blocked at the quote, not at housekeeping
    assert credit_engine.getMaxWithdrawableForAsset(
        bob, vault_id, sg, stability_pool.address) == 0
    boa.env.time_travel(blocks=1)
    with boa.reverts("cannot withdraw anything"):
        teller.withdraw(savings_green, EIGHTEEN_DECIMALS, bob, stability_pool, sender=bob)
    clear_transient_storage()

    # claim of a still-unhealthy flagged user dies at higher-risk housekeeping
    boa.env.time_travel(blocks=1)
    with boa.reverts("bad debt health"):
        claim_from_stability_pool(teller, vault_id, savings_green, bravo_token,
                                  EIGHTEEN_DECIMALS, sender=bob)
    clear_transient_storage()

    # a third-party redemption to the flagged user still commits (lower risk)
    green_token.transfer(sally, 50 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller.address, MAX_UINT256, sender=sally)
    teller.setUserConfig(bob, True, False, False, sender=bob)
    clear_transient_storage()
    boa.env.time_travel(blocks=1)
    assert teller.redeemManyFromStabilityPool(
        vault_id, [(bravo_token.address, MAX_UINT256)], 2 * EIGHTEEN_DECIMALS,
        bob, False, False, True, sender=sally) != 0
    clear_transient_storage()

    # collateral recovers: still flagged, so the quote still blocks the withdraw
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    assert ledger.userDebt(bob).inLiquidation
    assert credit_engine.getMaxWithdrawableForAsset(
        bob, vault_id, sg, stability_pool.address) == 0
    boa.env.time_travel(blocks=1)
    with boa.reverts("cannot withdraw anything"):
        teller.withdraw(savings_green, EIGHTEEN_DECIMALS, bob, stability_pool, sender=bob)
    clear_transient_storage()

    # ... but a claim now commits and its housekeeping clears the flag
    boa.env.time_travel(blocks=1)
    claim_from_stability_pool(teller, vault_id, savings_green, bravo_token,
                              EIGHTEEN_DECIMALS, sender=bob)
    clear_transient_storage()
    assert not ledger.userDebt(bob).inLiquidation
    boa.env.time_travel(blocks=1)
    assert teller.withdraw(savings_green, EIGHTEEN_DECIMALS, bob,
                           stability_pool, sender=bob) == EIGHTEEN_DECIMALS
    clear_transient_storage()


def test_stab_claim_and_redeem_last_touch_directions(
    launch_stab, stability_pool, green_token, savings_green, whale, bob, sally,
    teller, auction_house, bravo_token, bravo_token_whale, alpha_token,
    alpha_token_whale, mock_price_source, setAssetConfig, setGeneralDebtConfig,
    createDebtTerms, performDeposit, ledger, vault_book, mission_control,
    switchboard_alpha,
):
    """Higher-risk stab actions stamp `lastTouch`; the recipient of a
    third-party redemption does not."""
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    setAssetConfig(alpha_token, [3],
                   _debtTerms=createDebtTerms(_ltv=50_00, _liqThreshold=80_00,
                                              _liqFee=0, _borrowRate=0),
                   _shouldSwapInStabPools=False, _shouldAuctionInstantly=False)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mission_control.setShouldCheckLastTouch(True, sender=switchboard_alpha.address)
    sg = savings_green.address
    vault_id = vault_book.getRegId(stability_pool.address)

    _convert(teller, green_token, whale, bob, 100 * EIGHTEEN_DECIMALS)
    _seed_claimable(stability_pool, sg, green_token, auction_house, bravo_token,
                    bravo_token_whale, 60 * EIGHTEEN_DECIMALS, 30 * EIGHTEEN_DECIMALS)
    boa.env.time_travel(blocks=1)
    performDeposit(bob, 400 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    clear_transient_storage()
    boa.env.time_travel(blocks=1)
    teller.borrow(50 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    clear_transient_storage()
    green_token.transfer(sally, 100 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller.address, MAX_UINT256, sender=sally)

    boa.env.time_travel(blocks=1)
    with boa.env.anchor():
        claim_from_stability_pool(teller, vault_id, savings_green, bravo_token,
                                  5 * EIGHTEEN_DECIMALS, sender=bob)
        clear_transient_storage()
        assert ledger.lastTouch(bob) == boa.env.evm.patch.block_number
        with boa.reverts("one action per block"):
            teller.borrow(EIGHTEEN_DECIMALS, bob, False, sender=bob)
        clear_transient_storage()

    with boa.env.anchor():
        teller.setUserConfig(bob, True, False, False, sender=bob)
        clear_transient_storage()
        boa.env.time_travel(blocks=1)
        touch_before = ledger.lastTouch(bob)
        teller.redeemManyFromStabilityPool(
            vault_id, [(bravo_token.address, MAX_UINT256)], 5 * EIGHTEEN_DECIMALS,
            bob, False, False, True, sender=sally)
        clear_transient_storage()
        # recipient != caller, so no recipient stamp and the recipient may still act
        assert ledger.lastTouch(bob) == touch_before
        assert teller.borrow(EIGHTEEN_DECIMALS, bob, False, sender=bob) != 0
        clear_transient_storage()

    # check OFF: the same higher-risk claim no longer blocks a same-block borrow
    mission_control.setShouldCheckLastTouch(False, sender=switchboard_alpha.address)
    boa.env.time_travel(blocks=1)
    claim_from_stability_pool(teller, vault_id, savings_green, bravo_token,
                              5 * EIGHTEEN_DECIMALS, sender=bob)
    clear_transient_storage()
    assert teller.borrow(EIGHTEEN_DECIMALS, bob, False, sender=bob) != 0
    clear_transient_storage()
