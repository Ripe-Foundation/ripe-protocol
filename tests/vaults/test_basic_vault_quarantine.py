import json
from pathlib import Path

import boa
import pytest

from conf_utils import buy_fungible_auction, redeem_collateral
from constants import EIGHTEEN_DECIMALS, MAX_UINT256


EIP_170_LIMIT = 24_576
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def stock_token(deploy3r):
    return boa.load(
        "contracts/mock/MockStockTokenControls.vy",
        deploy3r,
        18,
        name="quarantine_stock_token",
    )


def _configure_asset(
    token,
    vault_id,
    setAssetConfig,
    createDebtTerms,
    *,
    stakers_alloc=10,
    voter_alloc=20,
):
    setAssetConfig(
        token,
        _vaultIds=[vault_id],
        _stakersPointsAlloc=stakers_alloc,
        _voterPointsAlloc=voter_alloc,
        _debtTerms=createDebtTerms(
            _ltv=50_00,
            _redemptionThreshold=60_00,
            _liqThreshold=80_00,
            _liqFee=0,
            _borrowRate=0,
        ),
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
        _canRedeemCollateral=True,
    )


def _deposit(token, vault, teller, user, amount, admin):
    token.mint(user, amount, sender=admin)
    token.approve(teller, amount, sender=user)
    return teller.deposit(token, amount, user, vault, sender=user)


def _setup_stock_position(
    stock_token,
    simple_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    deploy3r,
    user,
    *,
    deposit_amount=200 * EIGHTEEN_DECIMALS,
    borrow_amount=50 * EIGHTEEN_DECIMALS,
    stakers_alloc=10,
    voter_alloc=20,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    _configure_asset(
        stock_token,
        3,
        setAssetConfig,
        createDebtTerms,
        stakers_alloc=stakers_alloc,
        voter_alloc=voter_alloc,
    )
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
    assert _deposit(
        stock_token,
        simple_erc20_vault,
        teller,
        user,
        deposit_amount,
        deploy3r,
    ) == deposit_amount
    if borrow_amount != 0:
        assert teller.borrow(borrow_amount, user, False, sender=user) == borrow_amount
    return deposit_amount


def _create_custody_shortfall(stock_token, simple_erc20_vault, deploy3r, amount=1):
    stock_token.adminBurn(simple_erc20_vault, amount, sender=deploy3r)


def test_quarantine_detection_borrow_block_and_automatic_recovery(
    stock_token,
    simple_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    deploy3r,
    bob,
):
    deposit_amount = _setup_stock_position(
        stock_token,
        simple_erc20_vault,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        teller,
        deploy3r,
        bob,
    )

    _create_custody_shortfall(stock_token, simple_erc20_vault, deploy3r)
    debt, terms, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    assert debt.amount == 50 * EIGHTEEN_DECIMALS
    assert simple_erc20_vault.getUserLootBoxShare(bob, stock_token) == 0
    stock_index = simple_erc20_vault.indexOfUserAsset(bob, stock_token)
    assert simple_erc20_vault.getUserAssetAtIndexAndHasBalance(bob, stock_index) == (
        stock_token.address,
        True,
    )
    assert simple_erc20_vault.doesUserHaveBalance(bob, stock_token)
    assert terms.hasQuarantinedAsset
    assert terms.collateralVal == 0
    assert simple_erc20_vault.getTotalAmountForVault(stock_token) == 0
    assert not credit_engine.hasGoodDebtHealth(bob)
    assert not credit_engine.canLiquidateUser(bob)
    assert not credit_engine.canRedeemUserCollateral(bob)
    assert credit_engine.getMaxBorrowAmount(bob) == 0
    with boa.reverts("quarantined asset"):
        teller.borrow(1, bob, False, sender=bob)

    stock_token.mint(simple_erc20_vault, 1, sender=deploy3r)
    recovered = credit_engine.getUserBorrowTerms(bob, False)
    assert not recovered.hasQuarantinedAsset
    assert recovered.collateralVal == deposit_amount
    assert simple_erc20_vault.getTotalAmountForVault(stock_token) == deposit_amount
    assert credit_engine.hasGoodDebtHealth(bob)
    assert credit_engine.getMaxBorrowAmount(bob) > 0


def test_indebted_quarantine_blocks_positive_ltv_withdrawal_but_allows_repay_and_other_deposit(
    stock_token,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    green_token,
    deploy3r,
    bob,
    alice,
):
    _setup_stock_position(
        stock_token,
        simple_erc20_vault,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        teller,
        deploy3r,
        bob,
    )
    _configure_asset(alpha_token, 3, setAssetConfig, createDebtTerms)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _create_custody_shortfall(stock_token, simple_erc20_vault, deploy3r)

    other_deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, other_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, other_deposit, sender=bob)
    assert teller.deposit(
        alpha_token,
        other_deposit,
        bob,
        simple_erc20_vault,
        sender=bob,
    ) == other_deposit
    terms = credit_engine.getUserBorrowTerms(bob, False)
    assert terms.hasQuarantinedAsset
    # Type-1 health remains a truthful capacity check even though the account
    # is quarantined from new borrowing and forced actions.
    assert credit_engine.hasGoodDebtHealth(bob)
    assert not credit_engine.canLiquidateUser(bob)
    assert not credit_engine.canRedeemUserCollateral(bob)
    with boa.reverts("quarantined asset"):
        teller.borrow(1, bob, False, sender=bob)

    # The indebted user cannot withdraw either the quarantined asset itself or
    # unrelated positive-LTV collateral. BasicVault independently fails closed
    # if its Teller-only withdrawal entrypoint is invoked directly.
    assert credit_engine.getMaxWithdrawableForAsset(
        bob,
        3,
        stock_token,
        simple_erc20_vault,
    ) == 0
    with boa.reverts("cannot withdraw anything"):
        teller.withdraw(
            stock_token,
            1,
            bob,
            simple_erc20_vault,
            sender=bob,
        )
    with boa.reverts("insufficient vault backing"):
        simple_erc20_vault.withdrawTokensFromVault(
            bob,
            stock_token,
            1,
            bob,
            sender=teller.address,
        )
    assert credit_engine.getMaxWithdrawableForAsset(
        bob,
        3,
        alpha_token,
        simple_erc20_vault,
    ) == 0
    with boa.reverts("cannot withdraw anything"):
        teller.withdraw(
            alpha_token,
            1,
            bob,
            simple_erc20_vault,
            sender=bob,
        )

    # Quarantine is scoped to affected accounts, not every holder or every
    # asset in the vault. A debt-free holder can still exit healthy collateral.
    alice_amount = 20 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alice, alice_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, alice_amount, sender=alice)
    assert teller.deposit(
        alpha_token,
        alice_amount,
        alice,
        simple_erc20_vault,
        sender=alice,
    ) == alice_amount
    assert credit_engine.getMaxWithdrawableForAsset(
        alice,
        3,
        alpha_token,
        simple_erc20_vault,
    ) == MAX_UINT256
    assert teller.withdraw(
        alpha_token,
        alice_amount,
        alice,
        simple_erc20_vault,
        sender=alice,
    ) == alice_amount

    repay_amount = 10 * EIGHTEEN_DECIMALS
    debt_before = credit_engine.getUserDebtAmount(bob)
    green_token.approve(teller, repay_amount, sender=bob)
    assert teller.repay(repay_amount, bob, False, False, sender=bob)
    assert credit_engine.getUserDebtAmount(bob) == debt_before - repay_amount


def test_existing_auction_is_frozen_by_shortfall_and_recovers_with_custody(
    stock_token,
    simple_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    green_token,
    whale,
    deploy3r,
    bob,
    alice,
    sally,
):
    deposit_amount = _setup_stock_position(
        stock_token,
        simple_erc20_vault,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        teller,
        deploy3r,
        bob,
        borrow_amount=100 * EIGHTEEN_DECIMALS,
    )
    setAssetConfig(
        stock_token,
        _vaultIds=[3],
        _debtTerms=createDebtTerms(
            _ltv=50_00,
            _redemptionThreshold=60_00,
            _liqThreshold=80_00,
            _liqFee=0,
            _borrowRate=0,
        ),
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
        _canRedeemCollateral=True,
    )
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS // 2)
    assert credit_engine.canLiquidateUser(bob)
    teller.liquidateUser(bob, False, sender=sally)
    assert ledger.hasFungibleAuction(bob, 3, stock_token)

    _create_custody_shortfall(stock_token, simple_erc20_vault, deploy3r)
    assert credit_engine.getUserBorrowTerms(bob, False).hasQuarantinedAsset
    payment = 20 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    green_before = green_token.balanceOf(alice)
    debt_before = credit_engine.getUserDebtAmount(bob)
    # AuctionHouse observes zero usable custody and skips this entry before a
    # vault transfer is attempted; the batch then fails atomically. The direct
    # vault withdrawal guard is covered separately above.
    with boa.reverts("no green spent"):
        buy_fungible_auction(
            teller,
            bob,
            3,
            stock_token,
            payment,
            False,
            False,
            False,
            sender=alice,
        )
    assert green_token.balanceOf(alice) == green_before
    assert credit_engine.getUserDebtAmount(bob) == debt_before
    assert ledger.hasFungibleAuction(bob, 3, stock_token)

    stock_token.mint(simple_erc20_vault, 1, sender=deploy3r)
    assert stock_token.balanceOf(simple_erc20_vault) == deposit_amount
    assert not credit_engine.getUserBorrowTerms(bob, False).hasQuarantinedAsset
    boa.env.evm.vm.state.clear_transient_storage()
    spent = buy_fungible_auction(
        teller,
        bob,
        3,
        stock_token,
        payment,
        False,
        False,
        False,
        sender=alice,
    )
    assert spent > 0
    assert green_token.balanceOf(alice) == green_before - spent
    assert credit_engine.getUserDebtAmount(bob) == debt_before - spent


def test_governance_swap_collateral_remains_available_for_healthy_assets(
    stock_token,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    deleverage,
    deploy3r,
    governance,
    bob,
):
    _setup_stock_position(
        stock_token,
        simple_erc20_vault,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        teller,
        deploy3r,
        bob,
    )
    for token in (alpha_token, bravo_token):
        _configure_asset(token, 3, setAssetConfig, createDebtTerms)
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)

    healthy_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, healthy_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, healthy_amount, sender=bob)
    assert teller.deposit(
        alpha_token,
        healthy_amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    ) == healthy_amount

    swap_amount = 20 * EIGHTEEN_DECIMALS
    bravo_token.transfer(governance, swap_amount, sender=bravo_token_whale)
    bravo_token.approve(deleverage, swap_amount, sender=governance.address)
    _create_custody_shortfall(stock_token, simple_erc20_vault, deploy3r)
    assert credit_engine.getUserBorrowTerms(bob, False).hasQuarantinedAsset

    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        3,
        alpha_token,
        3,
        bravo_token,
        swap_amount,
        sender=governance.address,
    )
    assert withdrawn == deposited == swap_amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == (
        healthy_amount - swap_amount
    )
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == swap_amount
    assert credit_engine.getUserBorrowTerms(bob, False).hasQuarantinedAsset


def test_quarantine_suppresses_new_liquidation_redemption_and_forced_deleverage(
    stock_token,
    simple_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    credit_redeem,
    deleverage,
    ledger,
    green_token,
    whale,
    switchboard_alpha,
    deploy3r,
    bob,
    alice,
    sally,
):
    _setup_stock_position(
        stock_token,
        simple_erc20_vault,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        teller,
        deploy3r,
        bob,
        borrow_amount=100 * EIGHTEEN_DECIMALS,
    )
    _create_custody_shortfall(stock_token, simple_erc20_vault, deploy3r)
    debt_before = credit_engine.getUserDebtAmount(bob)

    assert teller.liquidateUser(bob, False, sender=sally) == 0
    assert not ledger.hasFungibleAuction(bob, 3, stock_token)
    assert not ledger.userDebt(bob).inLiquidation

    assert credit_redeem.getMaxRedeemValue(bob) == 0
    payment = 10 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    with boa.reverts("no redemptions occurred"):
        redeem_collateral(
            teller,
            bob,
            3,
            stock_token,
            payment,
            False,
            False,
            False,
            sender=alice,
        )

    assert deleverage.getMaxDeleverageAmount(bob) == 0
    with boa.reverts("nobody deleveraged"):
        teller.deleverageManyUsers(
            [(bob, payment)],
            sender=switchboard_alpha.address,
        )
    assert deleverage.deleverageWithVolAssets(
        bob,
        [(3, stock_token.address, payment)],
        sender=switchboard_alpha.address,
    ) == 0
    assert not deleverage.deleverageForWithdrawal(
        bob,
        3,
        stock_token,
        1,
        sender=switchboard_alpha.address,
    )
    assert credit_engine.getUserDebtAmount(bob) == debt_before


def test_share_rounding_dust_does_not_trigger_quarantine(
    stock_token,
    rebase_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    deploy3r,
    bob,
    alice,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    _configure_asset(stock_token, 4, setAssetConfig, createDebtTerms)
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
    assert _deposit(
        stock_token,
        rebase_erc20_vault,
        teller,
        bob,
        EIGHTEEN_DECIMALS,
        deploy3r,
    ) == EIGHTEEN_DECIMALS
    assert _deposit(stock_token, rebase_erc20_vault, teller, alice, 1, deploy3r) == 1

    total_custody = stock_token.balanceOf(rebase_erc20_vault)
    stock_token.adminBurn(rebase_erc20_vault, total_custody - 1, sender=deploy3r)
    assert rebase_erc20_vault.getTotalAmountForUser(alice, stock_token) == 0
    assert rebase_erc20_vault.getUserLootBoxShare(alice, stock_token) != 0
    assert rebase_erc20_vault.getTotalAmountForVault(stock_token) == 1
    assert not credit_engine.getUserBorrowTerms(alice, False).hasQuarantinedAsset


def test_zero_ltv_shortfall_suppresses_user_rewards_without_debt_quarantine(
    stock_token,
    simple_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    setRipeRewardsConfig,
    mock_price_source,
    teller,
    credit_engine,
    lootbox,
    ledger,
    switchboard_alpha,
    deploy3r,
    bob,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    setAssetConfig(
        stock_token,
        _vaultIds=[3],
        _stakersPointsAlloc=10,
        _voterPointsAlloc=20,
        _debtTerms=createDebtTerms(0, 0, 0, 0, 0, 0),
        _shouldSwapInStabPools=False,
    )
    setRipeRewardsConfig(True)
    ledger.setRipeAvailForRewards(
        1_000 * EIGHTEEN_DECIMALS,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    assert _deposit(
        stock_token,
        simple_erc20_vault,
        teller,
        bob,
        deposit_amount,
        deploy3r,
    ) == deposit_amount

    boa.env.time_travel(blocks=10)
    lootbox.updateDepositPoints(
        bob,
        3,
        simple_erc20_vault,
        stock_token,
        sender=teller.address,
    )
    healthy_user = ledger.userDepositPoints(bob, 3, stock_token)
    healthy_asset = ledger.assetDepositPoints(3, stock_token)
    claimable_before = lootbox.getClaimableDepositLootForAsset(bob, 3, stock_token)
    assert healthy_user.balancePoints > 0
    assert healthy_user.lastBalance == deposit_amount // healthy_asset.precision
    assert healthy_asset.lastBalance == healthy_user.lastBalance
    assert claimable_before > 0

    _create_custody_shortfall(stock_token, simple_erc20_vault, deploy3r)
    assert not credit_engine.getUserBorrowTerms(bob, False).hasQuarantinedAsset
    assert simple_erc20_vault.getUserLootBoxShare(bob, stock_token) == 0
    stock_index = simple_erc20_vault.indexOfUserAsset(bob, stock_token)
    assert simple_erc20_vault.getUserAssetAtIndexAndHasBalance(bob, stock_index) == (
        stock_token.address,
        True,
    )
    assert simple_erc20_vault.userBalances(bob, stock_token) == deposit_amount
    assert simple_erc20_vault.totalBalances(stock_token) == deposit_amount

    # Enumeration remains nominal, so Lootbox visits the asset and writes the
    # custody-suppressed share into the user's current reward balance.
    lootbox.updateDepositPoints(
        bob,
        3,
        simple_erc20_vault,
        stock_token,
        sender=teller.address,
    )
    suppressed_user = ledger.userDepositPoints(bob, 3, stock_token)
    suppressed_asset = ledger.assetDepositPoints(3, stock_token)
    assert suppressed_user.lastBalance == 0
    assert suppressed_user.balancePoints == healthy_user.balancePoints
    assert suppressed_asset.lastBalance == (
        healthy_asset.lastBalance - healthy_user.lastBalance
    )
    assert suppressed_asset.lastBalance == 0
    assert lootbox.getClaimableDepositLootForAsset(bob, 3, stock_token) == claimable_before

    # Historical balance points remain, but no new user balance points accrue
    # after the suppressed zero balance has been checkpointed.
    boa.env.time_travel(blocks=10)
    lootbox.updateDepositPoints(
        bob,
        3,
        simple_erc20_vault,
        stock_token,
        sender=teller.address,
    )
    still_suppressed_user = ledger.userDepositPoints(bob, 3, stock_token)
    still_suppressed_asset = ledger.assetDepositPoints(3, stock_token)
    assert still_suppressed_user.lastBalance == 0
    assert still_suppressed_user.balancePoints == suppressed_user.balancePoints
    assert still_suppressed_asset.lastBalance == 0
    assert still_suppressed_asset.ripeStakerPoints > suppressed_asset.ripeStakerPoints
    assert still_suppressed_asset.ripeVotePoints > suppressed_asset.ripeVotePoints
    assert lootbox.getClaimableDepositLootForAsset(bob, 3, stock_token) >= claimable_before

    # Exact custody restoration is sufficient: no storage reset or governance
    # cleanup is needed, and no balance points are caught up for the deficient interval.
    stock_token.mint(simple_erc20_vault, 1, sender=deploy3r)
    assert simple_erc20_vault.getUserLootBoxShare(bob, stock_token) == deposit_amount
    before_recovery_user = ledger.userDepositPoints(bob, 3, stock_token)
    before_recovery_asset = ledger.assetDepositPoints(3, stock_token)
    expected_stored_share = deposit_amount // before_recovery_asset.precision
    lootbox.updateDepositPoints(
        bob,
        3,
        simple_erc20_vault,
        stock_token,
        sender=teller.address,
    )
    recovered_user = ledger.userDepositPoints(bob, 3, stock_token)
    recovered_asset = ledger.assetDepositPoints(3, stock_token)
    assert recovered_user.lastBalance == expected_stored_share
    assert recovered_user.balancePoints == before_recovery_user.balancePoints
    assert recovered_asset.lastBalance == (
        before_recovery_asset.lastBalance + expected_stored_share
    )

    boa.env.time_travel(blocks=10)
    lootbox.updateDepositPoints(
        bob,
        3,
        simple_erc20_vault,
        stock_token,
        sender=teller.address,
    )
    resumed_user = ledger.userDepositPoints(bob, 3, stock_token)
    assert resumed_user.balancePoints == recovered_user.balancePoints + expected_stored_share * 10
    assert resumed_user.lastBalance == expected_stored_share


def test_shortfall_checkpoints_each_normalized_user_share_and_leaves_healthy_asset_untouched(
    stock_token,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    setRipeRewardsConfig,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    deploy3r,
    bob,
    alice,
):
    bob_stock = 100 * EIGHTEEN_DECIMALS
    alice_stock = 50 * EIGHTEEN_DECIMALS
    alice_alpha = 40 * EIGHTEEN_DECIMALS
    _setup_stock_position(
        stock_token,
        simple_erc20_vault,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        teller,
        deploy3r,
        bob,
        deposit_amount=bob_stock,
        borrow_amount=0,
    )
    assert _deposit(
        stock_token,
        simple_erc20_vault,
        teller,
        alice,
        alice_stock,
        deploy3r,
    ) == alice_stock
    _configure_asset(alpha_token, 3, setAssetConfig, createDebtTerms)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    alpha_token.transfer(alice, alice_alpha, sender=alpha_token_whale)
    alpha_token.approve(teller, alice_alpha, sender=alice)
    assert teller.deposit(
        alpha_token,
        alice_alpha,
        alice,
        simple_erc20_vault,
        sender=alice,
    ) == alice_alpha
    setRipeRewardsConfig(True)

    for user, asset in (
        (bob, stock_token),
        (alice, stock_token),
        (alice, alpha_token),
    ):
        lootbox.updateDepositPoints(
            user,
            3,
            simple_erc20_vault,
            asset,
            sender=teller.address,
        )

    bob_before = ledger.userDepositPoints(bob, 3, stock_token)
    alice_before = ledger.userDepositPoints(alice, 3, stock_token)
    stock_before = ledger.assetDepositPoints(3, stock_token)
    alpha_user_before = ledger.userDepositPoints(alice, 3, alpha_token)
    alpha_before = ledger.assetDepositPoints(3, alpha_token)
    assert stock_before.precision == 10**9
    assert bob_before.lastBalance == bob_stock // stock_before.precision
    assert alice_before.lastBalance == alice_stock // stock_before.precision
    assert stock_before.lastBalance == bob_before.lastBalance + alice_before.lastBalance

    _create_custody_shortfall(stock_token, simple_erc20_vault, deploy3r)
    for user, nominal in ((bob, bob_stock), (alice, alice_stock)):
        assert simple_erc20_vault.getUserLootBoxShare(user, stock_token) == 0
        assert simple_erc20_vault.userBalances(user, stock_token) == nominal
        index = simple_erc20_vault.indexOfUserAsset(user, stock_token)
        assert simple_erc20_vault.getUserAssetAtIndexAndHasBalance(user, index) == (
            stock_token.address,
            True,
        )

    assert simple_erc20_vault.getUserLootBoxShare(alice, alpha_token) == alice_alpha
    lootbox.updateDepositPoints(
        bob,
        3,
        simple_erc20_vault,
        stock_token,
        sender=teller.address,
    )
    bob_after = ledger.userDepositPoints(bob, 3, stock_token)
    alice_unchanged = ledger.userDepositPoints(alice, 3, stock_token)
    stock_after_bob = ledger.assetDepositPoints(3, stock_token)
    assert bob_after.lastBalance == 0
    assert alice_unchanged.lastBalance == alice_before.lastBalance
    assert stock_after_bob.lastBalance == stock_before.lastBalance - bob_before.lastBalance
    assert ledger.userDepositPoints(alice, 3, alpha_token) == alpha_user_before
    assert ledger.assetDepositPoints(3, alpha_token) == alpha_before

    lootbox.updateDepositPoints(
        alice,
        3,
        simple_erc20_vault,
        stock_token,
        sender=teller.address,
    )
    alice_after = ledger.userDepositPoints(alice, 3, stock_token)
    stock_after_alice = ledger.assetDepositPoints(3, stock_token)
    assert alice_after.lastBalance == 0
    assert stock_after_alice.lastBalance == (
        stock_after_bob.lastBalance - alice_before.lastBalance
    )
    assert stock_after_alice.lastBalance == 0
    assert ledger.userDepositPoints(alice, 3, alpha_token) == alpha_user_before
    assert ledger.assetDepositPoints(3, alpha_token) == alpha_before


@pytest.mark.parametrize(
    ("stakers_alloc", "voter_alloc"),
    ((0, 20), (10, 20)),
    ids=("general-and-voter", "staker-and-voter"),
)
def test_reward_updates_keep_configured_allocations_during_quarantine(
    stakers_alloc,
    voter_alloc,
    stock_token,
    simple_erc20_vault,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    setRipeRewardsConfig,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    mission_control,
    deploy3r,
    bob,
):
    _setup_stock_position(
        stock_token,
        simple_erc20_vault,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        teller,
        deploy3r,
        bob,
        borrow_amount=0,
        stakers_alloc=stakers_alloc,
        voter_alloc=voter_alloc,
    )
    setRipeRewardsConfig(True)

    boa.env.time_travel(blocks=10)
    lootbox.updateDepositPoints(
        bob,
        3,
        simple_erc20_vault,
        stock_token,
        sender=teller.address,
    )
    before = ledger.assetDepositPoints(3, stock_token)
    user_before = ledger.userDepositPoints(bob, 3, stock_token)
    global_before = ledger.globalDepositPoints()
    assert user_before.lastBalance > 0
    assert before.ripeVotePoints > 0
    if stakers_alloc == 0:
        assert before.ripeGenPoints > 0
    else:
        assert before.ripeStakerPoints > 0
    configured_before = mission_control.getDepositPointsConfig(stock_token)

    _create_custody_shortfall(stock_token, simple_erc20_vault, deploy3r)
    assert simple_erc20_vault.getUserLootBoxShare(bob, stock_token) == 0
    stock_index = simple_erc20_vault.indexOfUserAsset(bob, stock_token)
    assert simple_erc20_vault.getUserAssetAtIndexAndHasBalance(bob, stock_index) == (
        stock_token.address,
        True,
    )
    boa.env.time_travel(blocks=10)
    lootbox.updateDepositPoints(
        bob,
        3,
        simple_erc20_vault,
        stock_token,
        sender=teller.address,
    )
    quarantined = ledger.assetDepositPoints(3, stock_token)
    suppressed_user = ledger.userDepositPoints(bob, 3, stock_token)
    global_quarantined = ledger.globalDepositPoints()
    assert suppressed_user.lastBalance == 0
    assert suppressed_user.balancePoints >= user_before.balancePoints
    assert quarantined.lastBalance == 0
    if stakers_alloc == 0:
        assert quarantined.ripeStakerPoints == before.ripeStakerPoints
        assert global_quarantined.ripeStakerPoints >= global_before.ripeStakerPoints
        # Legacy general rewards book the stale pre-incident USD value through
        # this first asset-specific update, then refresh it to zero.
        assert quarantined.ripeGenPoints > before.ripeGenPoints
        assert global_quarantined.ripeGenPoints > global_before.ripeGenPoints
    else:
        assert quarantined.ripeStakerPoints > before.ripeStakerPoints
        assert global_quarantined.ripeStakerPoints > global_before.ripeStakerPoints
        assert quarantined.ripeGenPoints == before.ripeGenPoints
        assert global_quarantined.ripeGenPoints == global_before.ripeGenPoints
    assert quarantined.ripeVotePoints > before.ripeVotePoints
    assert quarantined.lastUsdValue == 0
    assert global_quarantined.ripeVotePoints > global_before.ripeVotePoints
    assert mission_control.getDepositPointsConfig(stock_token) == configured_before

    stock_token.mint(simple_erc20_vault, 1, sender=deploy3r)
    boa.env.time_travel(blocks=10)
    lootbox.updateDepositPoints(
        bob,
        3,
        simple_erc20_vault,
        stock_token,
        sender=teller.address,
    )
    boa.env.time_travel(blocks=10)
    lootbox.updateDepositPoints(
        bob,
        3,
        simple_erc20_vault,
        stock_token,
        sender=teller.address,
    )
    recovered = ledger.assetDepositPoints(3, stock_token)
    recovered_user = ledger.userDepositPoints(bob, 3, stock_token)
    assert recovered_user.lastBalance == (
        simple_erc20_vault.userBalances(bob, stock_token) // recovered.precision
    )
    assert recovered.ripeVotePoints > quarantined.ripeVotePoints
    if stakers_alloc == 0:
        assert recovered.ripeGenPoints > quarantined.ripeGenPoints
    else:
        assert recovered.ripeStakerPoints > quarantined.ripeStakerPoints


def test_unrelated_reward_update_preserves_shortfall_asset_fixed_allocation_state(
    stock_token,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    setRipeRewardsConfig,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    mission_control,
    deploy3r,
    bob,
    alice,
):
    _setup_stock_position(
        stock_token,
        simple_erc20_vault,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        teller,
        deploy3r,
        bob,
        borrow_amount=0,
        stakers_alloc=10,
        voter_alloc=20,
    )
    _configure_asset(
        alpha_token,
        3,
        setAssetConfig,
        createDebtTerms,
        stakers_alloc=0,
        voter_alloc=5,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    alpha_amount = 50 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alice, alpha_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, alpha_amount, sender=alice)
    assert teller.deposit(
        alpha_token,
        alpha_amount,
        alice,
        simple_erc20_vault,
        sender=alice,
    ) == alpha_amount
    setRipeRewardsConfig(True)

    boa.env.time_travel(blocks=10)
    lootbox.updateDepositPoints(
        bob,
        3,
        simple_erc20_vault,
        stock_token,
        sender=teller.address,
    )
    lootbox.updateDepositPoints(
        alice,
        3,
        simple_erc20_vault,
        alpha_token,
        sender=teller.address,
    )
    stock_before = ledger.assetDepositPoints(3, stock_token)
    configured_before = mission_control.getDepositPointsConfig(stock_token)

    _create_custody_shortfall(stock_token, simple_erc20_vault, deploy3r)
    boa.env.time_travel(blocks=10)
    lootbox.updateDepositPoints(
        alice,
        3,
        simple_erc20_vault,
        alpha_token,
        sender=teller.address,
    )
    # Updating an unrelated healthy asset does not mutate this asset's record.
    # Its next own calculation keeps using the configured fixed allocations,
    # even though the affected user's current balance share is suppressed.
    assert ledger.assetDepositPoints(3, stock_token) == stock_before

    boa.env.time_travel(blocks=10)
    lootbox.updateDepositPoints(
        bob,
        3,
        simple_erc20_vault,
        stock_token,
        sender=teller.address,
    )
    stock_after = ledger.assetDepositPoints(3, stock_token)
    assert stock_after.ripeStakerPoints > stock_before.ripeStakerPoints
    assert stock_after.ripeVotePoints > stock_before.ripeVotePoints
    assert stock_after.ripeGenPoints == stock_before.ripeGenPoints
    assert stock_after.lastUsdValue == 0
    assert mission_control.getDepositPointsConfig(stock_token) == configured_before


def test_mixed_deleverage_batch_skips_quarantine_and_one_element_batch_replaces_singular_api(
    stock_token,
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    deleverage,
    switchboard_delta,
    switchboard_alpha,
    deploy3r,
    bob,
    alice,
):
    _setup_stock_position(
        stock_token,
        simple_erc20_vault,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        teller,
        deploy3r,
        bob,
    )
    _configure_asset(alpha_token, 3, setAssetConfig, createDebtTerms)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    alpha_deposit = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alice, alpha_deposit, sender=alpha_token_whale)
    alpha_token.approve(teller, alpha_deposit, sender=alice)
    assert teller.deposit(
        alpha_token,
        alpha_deposit,
        alice,
        simple_erc20_vault,
        sender=alice,
    ) == alpha_deposit
    assert teller.borrow(
        50 * EIGHTEEN_DECIMALS,
        alice,
        False,
        sender=alice,
    ) == 50 * EIGHTEEN_DECIMALS
    _create_custody_shortfall(stock_token, simple_erc20_vault, deploy3r)

    assert not hasattr(teller, "deleverageUser")
    assert not hasattr(deleverage, "deleverageUser")
    assert not hasattr(switchboard_delta, "deleverageUser")

    one_target = 5 * EIGHTEEN_DECIMALS
    alice_before = credit_engine.getUserDebtAmount(alice)
    assert teller.deleverageManyUsers(
        [(alice, one_target)],
        sender=switchboard_alpha.address,
    ) == one_target
    assert credit_engine.getUserDebtAmount(alice) == alice_before - one_target

    # Boa 0.2.7 retains EIP-1153 values across simulated top-level calls;
    # production EVMs clear them between these two transactions.
    boa.env.evm.vm.state.clear_transient_storage()
    mixed_target = 10 * EIGHTEEN_DECIMALS
    bob_before = credit_engine.getUserDebtAmount(bob)
    alice_before = credit_engine.getUserDebtAmount(alice)
    assert teller.deleverageManyUsers(
        [(bob, mixed_target), (alice, mixed_target)],
        sender=switchboard_alpha.address,
    ) == mixed_target
    assert credit_engine.getUserDebtAmount(bob) == bob_before
    assert credit_engine.getUserDebtAmount(alice) == alice_before - mixed_target


def test_removed_singular_deleverage_api_and_appended_borrow_terms_abi():
    for name in ("Deleverage", "Teller", "SwitchboardDelta"):
        abi = json.loads((ROOT / "scripts" / "abis" / f"{name}.json").read_text())
        assert not any(
            item.get("type") == "function" and item.get("name") == "deleverageUser"
            for item in abi
        )

    credit_engine_abi = json.loads(
        (ROOT / "scripts" / "abis" / "CreditEngine.json").read_text()
    )
    get_terms = next(
        item
        for item in credit_engine_abi
        if item.get("type") == "function" and item.get("name") == "getUserBorrowTerms"
    )
    components = get_terms["outputs"][0]["components"]
    assert components[-1] == {
        "name": "hasQuarantinedAsset",
        "type": "bool",
    }


def test_changed_contract_deployed_runtime_sizes_include_immutables(
    simple_erc20_vault,
    credit_engine,
    auction_house,
    credit_redeem,
    deleverage,
    lootbox,
    teller,
    switchboard_delta,
):
    changed_contracts = {
        "SimpleErc20": simple_erc20_vault,
        "CreditEngine": credit_engine,
        "AuctionHouse": auction_house,
        "CreditRedeem": credit_redeem,
        "Deleverage": deleverage,
        "Lootbox": lootbox,
        "Teller": teller,
        "SwitchboardDelta": switchboard_delta,
    }
    sizes = {
        name: len(boa.env.get_code(contract.address))
        for name, contract in changed_contracts.items()
    }
    for name, size in sizes.items():
        print(f"RUNTIME_SIZE {name} {size} headroom={EIP_170_LIMIT - size}")
    assert all(size < EIP_170_LIMIT for size in sizes.values())
