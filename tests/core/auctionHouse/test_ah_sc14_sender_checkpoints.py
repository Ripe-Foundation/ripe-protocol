import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT
from conf_utils import buy_fungible_auction, filter_logs, install_lootbox_user_checkpoint_trap


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
    _install_lootbox_user_checkpoint_trap(lootbox, ripe_hq, alice)
    with boa.reverts("external call failed"):
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
        _buy(teller, bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS, alice, False)
    assert simple_erc20_vault.userBalances(bob, alpha_token) == bob_vault
    assert alpha_token.balanceOf(alice) == alice_wallet
    assert alpha_token.balanceOf(simple_erc20_vault) == vault_tokens
    assert ledger.userDepositPoints(bob, vault_id, alpha_token) == bob_points
    assert ledger.assetDepositPoints(vault_id, alpha_token) == asset_points
    assert ledger.globalDepositPoints() == global_points
    assert ledger.userDebt(bob).amount == debt_before
    assert green_token.balanceOf(alice) == green_before
    assert green_token.allowance(alice, teller) == green_allowance
    assert filter_logs(teller, "FungAuctionPurchased") == []


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
        200 * EIGHTEEN_DECIMALS,
        100 * EIGHTEEN_DECIMALS,
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
    assert recipient.lastBalance == _normalized(simple_erc20_vault.userBalances(alice, alpha_token))
    assert recipient.lastBalance > recipient_before.lastBalance


def test_sc14_self_transfer_rejected_before_checkpoint(
    setGeneralConfig,
    setAssetConfig,
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
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, amount, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    before = ledger.userDepositPoints(bob, vault_id, alpha_token)
    # Self-transfer is rejected by the vault before any checkpoint.
    with boa.reverts("not allowed"):
        simple_erc20_vault.transferBalanceWithinVault(
            alpha_token,
            bob,
            bob,
            amount // 2,
            sender=teller.address,
        )
    assert ledger.userDepositPoints(bob, vault_id, alpha_token) == before
    assert simple_erc20_vault.userBalances(bob, alpha_token) == amount


def test_deregistered_auction_forces_external_delivery_even_if_withdrawals_disabled(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    createAuctionParams,
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
    sally,
):
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
        200 * EIGHTEEN_DECIMALS,
        100 * EIGHTEEN_DECIMALS,
    )
    assert mission_control.deregisterAsset(alpha_token, sender=switchboard_alpha.address)
    # Model a legacy retired config. New retirements cannot enter this posture,
    # but canWithdraw still must not disable the liquidation path.
    mission_control.eval(
        f"self.assetConfig[{alpha_token.address}].canWithdraw = False"
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    assert not ledger.isParticipatingInVault(alice, vault_id)

    payment = 10 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    wallet_before = alpha_token.balanceOf(alice)
    sender_before = simple_erc20_vault.userBalances(bob, alpha_token)

    assert _buy(teller, bob, vault_id, alpha_token, payment, alice, True) > 0
    assert alpha_token.balanceOf(alice) > wallet_before
    assert simple_erc20_vault.userBalances(bob, alpha_token) < sender_before
    assert simple_erc20_vault.userBalances(alice, alpha_token) == 0
    assert not ledger.isParticipatingInVault(alice, vault_id)
    recipient = ledger.userDepositPoints(alice, vault_id, alpha_token)
    assert recipient.lastBalance == 0
    assert recipient.balancePoints == 0


def test_deregistered_auction_fails_closed_when_auction_is_disabled(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    createAuctionParams,
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
    sally,
):
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
        200 * EIGHTEEN_DECIMALS,
        100 * EIGHTEEN_DECIMALS,
    )
    assert mission_control.deregisterAsset(alpha_token, sender=switchboard_alpha.address)
    # Model a legacy retired config with its dedicated auction lever disabled.
    mission_control.eval(
        f"self.assetConfig[{alpha_token.address}].canBuyInAuction = False"
    )

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

    with boa.reverts("no green spent"):
        _buy(teller, bob, vault_id, alpha_token, payment, alice, True)

    assert (
        alpha_token.balanceOf(alice),
        simple_erc20_vault.userBalances(bob, alpha_token),
        simple_erc20_vault.userBalances(alice, alpha_token),
        green_token.balanceOf(alice),
    ) == before
