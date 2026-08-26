import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT
from conf_utils import filter_logs, install_lootbox_user_checkpoint_trap, redeem_collateral


PRECISION_18 = 10 ** 9

_install_lootbox_user_checkpoint_trap = install_lootbox_user_checkpoint_trap


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


def test_deregistered_redeem_forces_external_delivery(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    ledger,
    vault_book,
    simple_erc20_vault,
    mission_control,
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
        enable_rewards=False,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    assert mission_control.deregisterAsset(
        alpha_token,
        sender=switchboard_alpha.address,
    )
    assert mission_control.indexOfAsset(alpha_token) == 0
    assert not ledger.isParticipatingInVault(alice, vault_id)

    payment = 10 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    before = (
        alpha_token.balanceOf(alice),
        simple_erc20_vault.userBalances(bob, alpha_token),
        simple_erc20_vault.userBalances(alice, alpha_token),
        ledger.isParticipatingInVault(alice, vault_id),
        ledger.userDepositPoints(alice, vault_id, alpha_token),
        green_token.balanceOf(alice),
    )

    assert _redeem(
        teller,
        bob,
        vault_id,
        alpha_token,
        payment,
        alice,
        True,
    ) > 0
    assert alpha_token.balanceOf(alice) > before[0]
    assert simple_erc20_vault.userBalances(bob, alpha_token) < before[1]
    assert simple_erc20_vault.userBalances(alice, alpha_token) == 0
    assert not ledger.isParticipatingInVault(alice, vault_id)
    recipient_points = ledger.userDepositPoints(alice, vault_id, alpha_token)
    assert recipient_points.lastBalance == 0
    assert recipient_points.balancePoints == 0


def test_deregistered_redeem_fails_closed_when_withdrawals_disabled(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    vault_book,
    simple_erc20_vault,
    mission_control,
    switchboard_alpha,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
):
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
        _liqFee=0,
        _borrowRate=0,
    )
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
        200 * EIGHTEEN_DECIMALS,
        100 * EIGHTEEN_DECIMALS,
        70 * EIGHTEEN_DECIMALS // 100,
        enable_rewards=False,
    )
    setAssetConfig(
        alpha_token,
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
        _debtTerms=debt_terms,
        _canWithdraw=False,
    )
    assert mission_control.deregisterAsset(alpha_token, sender=switchboard_alpha.address)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    payment = 10 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    before = (
        alpha_token.balanceOf(alice),
        simple_erc20_vault.userBalances(bob, alpha_token),
        simple_erc20_vault.userBalances(alice, alpha_token),
        green_token.balanceOf(alice),
    )

    with boa.reverts("no redemptions occurred"):
        _redeem(teller, bob, vault_id, alpha_token, payment, alice, True)

    assert (
        alpha_token.balanceOf(alice),
        simple_erc20_vault.userBalances(bob, alpha_token),
        simple_erc20_vault.userBalances(alice, alpha_token),
        green_token.balanceOf(alice),
    ) == before


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
    _install_lootbox_user_checkpoint_trap(lootbox, ripe_hq, bob)
    with boa.reverts("external call failed"):
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
    _install_lootbox_user_checkpoint_trap(lootbox, ripe_hq, alice)
    with boa.reverts("external call failed"):
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
    bob_vault = simple_erc20_vault.userBalances(bob, alpha_token)
    alice_wallet = alpha_token.balanceOf(alice)
    vault_tokens = alpha_token.balanceOf(simple_erc20_vault)
    bob_points = ledger.userDepositPoints(bob, vault_id, alpha_token)
    asset_points = ledger.assetDepositPoints(vault_id, alpha_token)
    global_points = ledger.globalDepositPoints()
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    _install_lootbox_user_checkpoint_trap(lootbox, ripe_hq, bob)
    debt_before = ledger.userDebt(bob).amount
    green_before = green_token.balanceOf(alice)
    green_allowance = green_token.allowance(alice, teller)
    with boa.reverts("external call failed"):
        _redeem(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, False)
    assert simple_erc20_vault.userBalances(bob, alpha_token) == bob_vault
    assert alpha_token.balanceOf(alice) == alice_wallet
    assert alpha_token.balanceOf(simple_erc20_vault) == vault_tokens
    assert ledger.userDepositPoints(bob, vault_id, alpha_token) == bob_points
    assert ledger.assetDepositPoints(vault_id, alpha_token) == asset_points
    assert ledger.globalDepositPoints() == global_points
    assert ledger.userDebt(bob).amount == debt_before
    assert green_token.balanceOf(alice) == green_before
    assert green_token.allowance(alice, teller) == green_allowance
    assert filter_logs(teller, "CollateralRedeemed") == []


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
