from pathlib import Path

import boa
import pytest

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT
from conf_utils import buy_fungible_auction, filter_logs


PRECISION_18 = 10 ** 9


def _install_lootbox_recipient_checkpoint_trap(lootbox, ripe_hq, blocked_user):
    source = Path("contracts/core/Lootbox.vy").read_text()
    needle = """@internal
def _updateDepositPoints(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _a: addys.Addys,
):
"""
    assert source.count(needle) == 1
    source = source.replace(
        needle,
        needle + f"    assert _user != {blocked_user} # dev: recipient checkpoint blocked\n",
        1,
    )
    mutant = boa.loads(
        source,
        ripe_hq.address,
        43_200,
        43_200,
        100 * EIGHTEEN_DECIMALS,
        100 * EIGHTEEN_DECIMALS,
        name="lootbox_recipient_trap",
    )
    boa.env.set_code(lootbox.address, bytes(boa.env.get_code(mutant.address)))


def _normalized(amount):
    return amount // PRECISION_18


def _enable_gen_rewards(setRipeRewardsConfig, ripe_per_block=10):
    setRipeRewardsConfig(
        True,
        ripe_per_block,
        0,
        0,
        0,
        HUNDRED_PERCENT,
    )


def _points_bundle(ledger, user, vault_id, asset):
    return (
        ledger.userDepositPoints(user, vault_id, asset),
        ledger.assetDepositPoints(vault_id, asset),
        ledger.globalDepositPoints(),
    )


def _open_auction(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    alpha_token,
    alpha_token_whale,
    green_token,
    bob,
    sally,
    deposit_amount,
    debt_amount,
    price_after=50 * EIGHTEEN_DECIMALS // 100,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=0, _minKeeperFee=0)
    _enable_gen_rewards(setRipeRewardsConfig)
    setAssetConfig(
        alpha_token,
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
        _debtTerms=createDebtTerms(
            _ltv=50_00,
            _redemptionThreshold=70_00,
            _liqThreshold=80_00,
            _liqFee=0,
            _borrowRate=0,
        ),
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
        _customAuctionParams=createAuctionParams(
            _startDiscount=0,
            _maxDiscount=0,
            _delay=0,
            _duration=100,
        ),
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    teller.borrow(debt_amount, bob, False, sender=bob)
    mock_price_source.setPrice(alpha_token, price_after)
    teller.liquidateUser(bob, False, sender=sally)
    return filter_logs(teller, "FungibleAuctionUpdated")[0]


def _buy(
    teller,
    bob,
    vault_id,
    asset,
    green_amount,
    alice,
    transfer,
):
    return buy_fungible_auction(
        teller,
        bob,
        vault_id,
        asset,
        green_amount,
        False,
        transfer,
        False,
        sender=alice,
    )


def test_sc14_ah_partial_internal_transfer_checkpoints_sender(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    auction = _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    before = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert before.lastBalance == _normalized(deposit_amount)

    elapsed = 20
    boa.env.time_travel(blocks=elapsed)
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    spent = _buy(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, True)
    assert spent > 0

    remaining = simple_erc20_vault.userBalances(bob, alpha_token)
    received = simple_erc20_vault.userBalances(alice, alpha_token)
    assert remaining < deposit_amount
    assert received > 0

    sender = ledger.userDepositPoints(bob, vault_id, alpha_token)
    recipient = ledger.userDepositPoints(alice, vault_id, alpha_token)
    asset = ledger.assetDepositPoints(vault_id, alpha_token)
    assert sender.lastBalance == _normalized(remaining)
    assert sender.lastBalance != before.lastBalance
    assert sender.balancePoints == before.lastBalance * elapsed
    assert recipient.lastBalance == _normalized(received)
    assert asset.lastBalance == sender.lastBalance + recipient.lastBalance

    future = 12
    boa.env.time_travel(blocks=future)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == (
        before.lastBalance * elapsed + sender.lastBalance * future
    )
    assert ledger.userDepositPoints(alice, vault_id, alpha_token).balancePoints == (
        recipient.lastBalance * future
    )


def test_sc14_ah_full_internal_transfer_zeroes_sender(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    points_before = ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints

    green_token.transfer(alice, 200 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 200 * EIGHTEEN_DECIMALS, sender=alice)
    assert _buy(teller, bob, vault_id, alpha_token, 100 * EIGHTEEN_DECIMALS, alice, True) > 0
    assert simple_erc20_vault.userBalances(bob, alpha_token) == 0

    sender = ledger.userDepositPoints(bob, vault_id, alpha_token)
    recipient = ledger.userDepositPoints(alice, vault_id, alpha_token)
    assert sender.lastBalance == 0
    assert recipient.lastBalance == _normalized(simple_erc20_vault.userBalances(alice, alpha_token))

    boa.env.time_travel(blocks=15)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == sender.balancePoints
    assert ledger.userDepositPoints(alice, vault_id, alpha_token).balancePoints == recipient.lastBalance * 15
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints >= points_before


def test_sc14_ah_withdrawal_does_not_credit_external_recipient(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    asset_before = ledger.assetDepositPoints(vault_id, alpha_token).lastBalance
    alice_wallet_before = alpha_token.balanceOf(alice)

    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    assert _buy(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, False) > 0

    remaining = simple_erc20_vault.userBalances(bob, alpha_token)
    sender = ledger.userDepositPoints(bob, vault_id, alpha_token)
    recipient = ledger.userDepositPoints(alice, vault_id, alpha_token)
    asset = ledger.assetDepositPoints(vault_id, alpha_token)
    assert sender.lastBalance == _normalized(remaining)
    assert recipient.lastBalance == 0
    assert recipient.balancePoints == 0
    assert simple_erc20_vault.userBalances(alice, alpha_token) == 0
    assert alpha_token.balanceOf(alice) > alice_wallet_before
    assert asset.lastBalance == sender.lastBalance
    assert asset.lastBalance < asset_before

    boa.env.time_travel(blocks=9)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    assert ledger.userDepositPoints(alice, vault_id, alpha_token).balancePoints == 0
    assert ledger.userDepositPoints(alice, vault_id, alpha_token).lastBalance == 0


def test_sc14_ah_same_block_repeated_transfers(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    boa.env.time_travel(blocks=8)
    green_token.transfer(alice, 200 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 200 * EIGHTEEN_DECIMALS, sender=alice)

    assert _buy(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, True) > 0
    after_first = ledger.userDepositPoints(bob, vault_id, alpha_token)
    remaining_after_first = simple_erc20_vault.userBalances(bob, alpha_token)
    assert after_first.lastBalance == _normalized(remaining_after_first)
    points_after_first = after_first.balancePoints

    assert _buy(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, True) > 0
    after_second = ledger.userDepositPoints(bob, vault_id, alpha_token)
    remaining_after_second = simple_erc20_vault.userBalances(bob, alpha_token)
    assert after_second.lastBalance == _normalized(remaining_after_second)
    assert after_second.lastBalance < after_first.lastBalance
    assert after_second.balancePoints == points_after_first

    assert _buy(teller, bob, vault_id, alpha_token, 100 * EIGHTEEN_DECIMALS, alice, True) > 0
    assert simple_erc20_vault.userBalances(bob, alpha_token) == 0
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).lastBalance == 0


def test_sc14_ah_checkpoint_revert_rolls_back_transfer_state(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    vault_book,
    simple_erc20_vault,
    switchboard_alpha,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    state = {
        "bob_vault": simple_erc20_vault.userBalances(bob, alpha_token),
        "alice_vault": simple_erc20_vault.userBalances(alice, alpha_token),
        "bob_wallet": alpha_token.balanceOf(bob),
        "alice_wallet": alpha_token.balanceOf(alice),
        "vault_tokens": alpha_token.balanceOf(simple_erc20_vault),
        "alice_participating": ledger.isParticipatingInVault(alice, vault_id),
        "bob_points": ledger.userDepositPoints(bob, vault_id, alpha_token),
        "alice_points": ledger.userDepositPoints(alice, vault_id, alpha_token),
        "asset_points": ledger.assetDepositPoints(vault_id, alpha_token),
        "global_points": ledger.globalDepositPoints(),
        "debt": ledger.userDebt(bob).amount,
    }
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    lootbox.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        _buy(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, True)
    assert simple_erc20_vault.userBalances(bob, alpha_token) == state["bob_vault"]
    assert simple_erc20_vault.userBalances(alice, alpha_token) == state["alice_vault"]
    assert alpha_token.balanceOf(bob) == state["bob_wallet"]
    assert alpha_token.balanceOf(alice) == state["alice_wallet"]
    assert alpha_token.balanceOf(simple_erc20_vault) == state["vault_tokens"]
    assert ledger.isParticipatingInVault(alice, vault_id) == state["alice_participating"]
    assert ledger.userDepositPoints(bob, vault_id, alpha_token) == state["bob_points"]
    assert ledger.userDepositPoints(alice, vault_id, alpha_token) == state["alice_points"]
    assert ledger.assetDepositPoints(vault_id, alpha_token) == state["asset_points"]
    assert ledger.globalDepositPoints() == state["global_points"]
    assert ledger.userDebt(bob).amount == state["debt"]
    assert filter_logs(teller, "FungAuctionPurchased") == []


def test_sc14_ah_recipient_checkpoint_revert_rolls_back_registration(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    vault_book,
    simple_erc20_vault,
    ripe_hq,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    state = {
        "bob_vault": simple_erc20_vault.userBalances(bob, alpha_token),
        "alice_vault": simple_erc20_vault.userBalances(alice, alpha_token),
        "alice_wallet": alpha_token.balanceOf(alice),
        "vault_tokens": alpha_token.balanceOf(simple_erc20_vault),
        "alice_participating": ledger.isParticipatingInVault(alice, vault_id),
        "bob_points": ledger.userDepositPoints(bob, vault_id, alpha_token),
        "alice_points": ledger.userDepositPoints(alice, vault_id, alpha_token),
        "asset_points": ledger.assetDepositPoints(vault_id, alpha_token),
        "global_points": ledger.globalDepositPoints(),
        "debt": ledger.userDebt(bob).amount,
    }
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    _install_lootbox_recipient_checkpoint_trap(lootbox, ripe_hq, alice)
    with boa.reverts():
        _buy(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, True)
    assert simple_erc20_vault.userBalances(bob, alpha_token) == state["bob_vault"]
    assert simple_erc20_vault.userBalances(alice, alpha_token) == state["alice_vault"]
    assert alpha_token.balanceOf(alice) == state["alice_wallet"]
    assert alpha_token.balanceOf(simple_erc20_vault) == state["vault_tokens"]
    assert ledger.isParticipatingInVault(alice, vault_id) == state["alice_participating"]
    assert not ledger.isParticipatingInVault(alice, vault_id)
    assert ledger.userDepositPoints(bob, vault_id, alpha_token) == state["bob_points"]
    assert ledger.userDepositPoints(alice, vault_id, alpha_token) == state["alice_points"]
    assert ledger.assetDepositPoints(vault_id, alpha_token) == state["asset_points"]
    assert ledger.globalDepositPoints() == state["global_points"]
    assert ledger.userDebt(bob).amount == state["debt"]
    assert filter_logs(teller, "FungAuctionPurchased") == []


def test_sc14_ah_withdrawal_checkpoint_revert_rolls_back_tokens(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    vault_book,
    simple_erc20_vault,
    switchboard_alpha,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    bob_vault = simple_erc20_vault.userBalances(bob, alpha_token)
    alice_wallet = alpha_token.balanceOf(alice)
    vault_tokens = alpha_token.balanceOf(simple_erc20_vault)
    bob_points = ledger.userDepositPoints(bob, vault_id, alpha_token)
    asset_points = ledger.assetDepositPoints(vault_id, alpha_token)
    global_points = ledger.globalDepositPoints()
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    lootbox.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        _buy(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, False)
    assert simple_erc20_vault.userBalances(bob, alpha_token) == bob_vault
    assert alpha_token.balanceOf(alice) == alice_wallet
    assert alpha_token.balanceOf(simple_erc20_vault) == vault_tokens
    assert ledger.userDepositPoints(bob, vault_id, alpha_token) == bob_points
    assert ledger.assetDepositPoints(vault_id, alpha_token) == asset_points
    assert ledger.globalDepositPoints() == global_points


def test_sc14_ah_zero_allocation_still_tracks_balances(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    setRipeRewardsConfig(False, 0, 0, 0, 0, 0)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
    )
    setRipeRewardsConfig(False, 0, 0, 0, 0, 0)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    ripe_before = ledger.ripeRewards()
    debt_before = ledger.userDebt(bob).amount
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    spent = _buy(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, True)
    assert spent > 0
    remaining = simple_erc20_vault.userBalances(bob, alpha_token)
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).lastBalance == _normalized(remaining)
    assert ledger.userDepositPoints(alice, vault_id, alpha_token).lastBalance == _normalized(
        simple_erc20_vault.userBalances(alice, alpha_token)
    )
    ripe_after = ledger.ripeRewards()
    assert ripe_after.genDepositors == ripe_before.genDepositors == 0
    assert ripe_after.newRipeRewards == ripe_before.newRipeRewards
    assert ledger.userDebt(bob).amount == debt_before - spent


def test_sc14_transfer_helper_self_recipient_checkpoints_once(
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=0)
    _enable_gen_rewards(setRipeRewardsConfig)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, amount, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    boa.env.time_travel(blocks=7)
    lootbox.updateDepositPointsForTransfer(
        bob, bob, vault_id, simple_erc20_vault, alpha_token, lootbox.getAddys(), sender=teller.address,
    )
    first = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert first.balancePoints == _normalized(amount) * 7
    assert first.lastBalance == _normalized(amount)

    lootbox.updateDepositPointsForTransfer(
        bob, bob, vault_id, simple_erc20_vault, alpha_token, lootbox.getAddys(), sender=teller.address,
    )
    assert ledger.userDepositPoints(bob, vault_id, alpha_token) == first


def test_sc14_ah_pre_mutation_self_recipient_return_skips_checkpoint(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    vault_book,
    simple_erc20_vault,
    switchboard_alpha,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    auction = _open_auction(
        setGeneralConfig, setAssetConfig, setGeneralDebtConfig, setRipeRewardsConfig,
        createDebtTerms, createAuctionParams, performDeposit, mock_price_source, teller,
        alpha_token, alpha_token_whale, green_token, bob, sally,
        200 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    before = _points_bundle(ledger, bob, vault_id, alpha_token)
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    lootbox.pause(True, sender=switchboard_alpha.address)

    with boa.reverts("no green spent"):
        buy_fungible_auction(
            teller, bob, auction.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS,
            False, True, False, recipient=bob, sender=alice,
        )
    assert _points_bundle(ledger, bob, vault_id, alpha_token) == before


def test_sc14_ah_existing_recipient_accrues_only_its_prior_balance(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    vault_book,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    _open_auction(
        setGeneralConfig, setAssetConfig, setGeneralDebtConfig, setRipeRewardsConfig,
        createDebtTerms, createAuctionParams, performDeposit, mock_price_source, teller,
        alpha_token, alpha_token_whale, green_token, bob, sally,
        200 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS,
    )
    prior = 30 * EIGHTEEN_DECIMALS
    performDeposit(alice, prior, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    recipient_before = ledger.userDepositPoints(alice, vault_id, alpha_token)

    elapsed = 6
    boa.env.time_travel(blocks=elapsed)
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    assert _buy(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, True) > 0

    recipient = ledger.userDepositPoints(alice, vault_id, alpha_token)
    assert recipient.balancePoints == recipient_before.lastBalance * elapsed
    assert recipient.lastBalance == _normalized(
        simple_erc20_vault.userBalances(alice, alpha_token)
    )
    assert recipient.lastBalance > recipient_before.lastBalance


@pytest.mark.parametrize("transfer", [True, False], ids=["transfer", "withdrawal"])
def test_sc14_ah_vault_failure_rolls_back_before_checkpoint(
    transfer,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    vault_book,
    simple_erc20_vault,
    switchboard_alpha,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    _open_auction(
        setGeneralConfig, setAssetConfig, setGeneralDebtConfig, setRipeRewardsConfig,
        createDebtTerms, createAuctionParams, performDeposit, mock_price_source, teller,
        alpha_token, alpha_token_whale, green_token, bob, sally,
        200 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    before = _points_bundle(ledger, bob, vault_id, alpha_token)
    bob_balance = simple_erc20_vault.userBalances(bob, alpha_token)
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    simple_erc20_vault.pause(True, sender=switchboard_alpha.address)

    with boa.reverts("contract paused"):
        _buy(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, transfer)
    assert simple_erc20_vault.userBalances(bob, alpha_token) == bob_balance
    assert _points_bundle(ledger, bob, vault_id, alpha_token) == before
