from pathlib import Path

import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT
from conf_utils import filter_logs, redeem_collateral


PRECISION_18 = 10 ** 9


def _install_lootbox_recipient_checkpoint_trap(lootbox, ripe_hq, blocked_user):
    source = Path("contracts/core/Lootbox.vy").read_text()
    needle = """@external
def updateDepositPoints(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _a: addys.Addys = empty(addys.Addys),
):
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
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


def _make_redeemable(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    alpha_token,
    alpha_token_whale,
    green_token,
    bob,
    deposit_amount,
    debt_amount,
    price_after,
    enable_rewards=True,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=0, _minKeeperFee=0)
    if enable_rewards:
        _enable_gen_rewards(setRipeRewardsConfig)
    else:
        setRipeRewardsConfig(False, 0, 0, 0, 0, 0)
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
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    teller.borrow(debt_amount, bob, False, sender=bob)
    mock_price_source.setPrice(alpha_token, price_after)


def _redeem(teller, bob, vault_id, asset, amount, alice, transfer):
    return redeem_collateral(
        teller,
        bob,
        vault_id,
        asset,
        amount,
        False,
        transfer,
        False,
        sender=alice,
    )


def test_sc14_redeem_partial_internal_transfer_checkpoints_sender(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
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
):
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _make_redeemable(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
        70 * EIGHTEEN_DECIMALS // 100,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    before = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert before.lastBalance == _normalized(deposit_amount)

    elapsed = 18
    boa.env.time_travel(blocks=elapsed)
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    spent = _redeem(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, True)
    assert spent > 0

    remaining = simple_erc20_vault.userBalances(bob, alpha_token)
    received = simple_erc20_vault.userBalances(alice, alpha_token)
    sender = ledger.userDepositPoints(bob, vault_id, alpha_token)
    recipient = ledger.userDepositPoints(alice, vault_id, alpha_token)
    asset = ledger.assetDepositPoints(vault_id, alpha_token)
    assert remaining < deposit_amount
    assert received > 0
    assert sender.lastBalance == _normalized(remaining)
    assert sender.balancePoints == before.lastBalance * elapsed
    assert recipient.lastBalance == _normalized(received)
    assert asset.lastBalance == sender.lastBalance + recipient.lastBalance

    future = 11
    boa.env.time_travel(blocks=future)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == (
        before.lastBalance * elapsed + sender.lastBalance * future
    )
    assert ledger.userDepositPoints(alice, vault_id, alpha_token).balancePoints == (
        recipient.lastBalance * future
    )


def test_sc14_redeem_full_internal_transfer_zeroes_sender(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
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
):
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _make_redeemable(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
        50 * EIGHTEEN_DECIMALS // 100,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    green_token.transfer(alice, 200 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 200 * EIGHTEEN_DECIMALS, sender=alice)
    assert _redeem(teller, bob, vault_id, alpha_token, 100 * EIGHTEEN_DECIMALS, alice, True) > 0
    assert simple_erc20_vault.userBalances(bob, alpha_token) == 0

    sender = ledger.userDepositPoints(bob, vault_id, alpha_token)
    recipient = ledger.userDepositPoints(alice, vault_id, alpha_token)
    assert sender.lastBalance == 0
    assert recipient.lastBalance == _normalized(simple_erc20_vault.userBalances(alice, alpha_token))

    boa.env.time_travel(blocks=14)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).lastBalance == 0
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == sender.balancePoints
    assert ledger.userDepositPoints(alice, vault_id, alpha_token).balancePoints == recipient.lastBalance * 14


def test_sc14_redeem_withdrawal_does_not_credit_external_recipient(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
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
):
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _make_redeemable(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
        70 * EIGHTEEN_DECIMALS // 100,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    asset_before = ledger.assetDepositPoints(vault_id, alpha_token).lastBalance
    alice_wallet_before = alpha_token.balanceOf(alice)
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    assert _redeem(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, False) > 0

    remaining = simple_erc20_vault.userBalances(bob, alpha_token)
    sender = ledger.userDepositPoints(bob, vault_id, alpha_token)
    recipient = ledger.userDepositPoints(alice, vault_id, alpha_token)
    assert sender.lastBalance == _normalized(remaining)
    assert recipient.lastBalance == 0
    assert recipient.balancePoints == 0
    assert simple_erc20_vault.userBalances(alice, alpha_token) == 0
    assert alpha_token.balanceOf(alice) > alice_wallet_before
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastBalance == sender.lastBalance
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastBalance < asset_before


def test_sc14_redeem_same_block_repeated_operations(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
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
):
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _make_redeemable(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
        50 * EIGHTEEN_DECIMALS // 100,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    boa.env.time_travel(blocks=7)
    green_token.transfer(alice, 120 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 120 * EIGHTEEN_DECIMALS, sender=alice)

    assert _redeem(teller, bob, vault_id, alpha_token, 20 * EIGHTEEN_DECIMALS, alice, True) > 0
    after_first = ledger.userDepositPoints(bob, vault_id, alpha_token)
    points_after_first = after_first.balancePoints
    assert after_first.lastBalance == _normalized(simple_erc20_vault.userBalances(bob, alpha_token))

    assert _redeem(teller, bob, vault_id, alpha_token, 20 * EIGHTEEN_DECIMALS, alice, True) > 0
    after_second = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert after_second.lastBalance == _normalized(simple_erc20_vault.userBalances(bob, alpha_token))
    assert after_second.lastBalance < after_first.lastBalance
    assert after_second.balancePoints == points_after_first

    assert _redeem(teller, bob, vault_id, alpha_token, 80 * EIGHTEEN_DECIMALS, alice, True) > 0
    assert simple_erc20_vault.userBalances(bob, alpha_token) == 0
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).lastBalance == 0


def test_sc14_redeem_checkpoint_revert_rolls_back_state(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
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
):
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _make_redeemable(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
        70 * EIGHTEEN_DECIMALS // 100,
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
        _redeem(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, True)
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
    assert filter_logs(teller, "CollateralRedeemed") == []


def test_sc14_redeem_recipient_checkpoint_revert_rolls_back_registration(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
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
):
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _make_redeemable(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
        70 * EIGHTEEN_DECIMALS // 100,
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
        _redeem(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, True)
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
    assert filter_logs(teller, "CollateralRedeemed") == []


def test_sc14_redeem_withdrawal_checkpoint_revert_rolls_back_tokens(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
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
):
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _make_redeemable(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
        70 * EIGHTEEN_DECIMALS // 100,
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
        _redeem(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, False)
    assert simple_erc20_vault.userBalances(bob, alpha_token) == bob_vault
    assert alpha_token.balanceOf(alice) == alice_wallet
    assert alpha_token.balanceOf(simple_erc20_vault) == vault_tokens
    assert ledger.userDepositPoints(bob, vault_id, alpha_token) == bob_points
    assert ledger.assetDepositPoints(vault_id, alpha_token) == asset_points
    assert ledger.globalDepositPoints() == global_points


def test_sc14_redeem_zero_allocation_still_tracks_balances(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
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
):
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _make_redeemable(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        setRipeRewardsConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        deposit_amount,
        100 * EIGHTEEN_DECIMALS,
        70 * EIGHTEEN_DECIMALS // 100,
        enable_rewards=False,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    ripe_before = ledger.ripeRewards()
    debt_before = ledger.userDebt(bob).amount
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    spent = _redeem(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, True)
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
