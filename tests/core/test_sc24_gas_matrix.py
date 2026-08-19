import pytest
import boa

from constants import EIGHTEEN_DECIMALS
from conf_utils import buy_fungible_auction, filter_logs, redeem_collateral


# Manual benchmark plus documented ceilings (~20% above the hybrid pin).
# Default pytest.ini excludes marker "gas", so these ceilings are NOT an
# ordinary PR-CI gate. Run them explicitly:
#   pytest -m gas tests/core/test_sc24_gas_matrix.py -s
# Enforced Teller-path ceilings also live in test_ah_auctions.py and
# test_ah_liq_stab.py; those were not raised by this hybrid.
pytestmark = pytest.mark.gas

BASIC_DEPOSIT_CEILING = 182_000
BASIC_CHECKPOINT_CEILING = 66_000
BASIC_WITHDRAW_CEILING = 202_000
SHARES_CHECKPOINT_CEILING = 66_000
REDEMPTION_CEILING = 300_000
AUCTION_CEILING = 295_000
STAB_LIQ_CEILINGS = {1: 540_000, 2: 840_000, 5: 1_735_000}
DELEVERAGE_MANY_CEILING = 400_000


def _print_gas(label, gas_used, ceiling):
    print(f"GAS_MATRIX {label}={gas_used} ceiling={ceiling}")
    assert gas_used <= ceiling, f"{label} used {gas_used} > {ceiling}"


def test_gas_basic_vault_deposit_withdraw_checkpoint(
    setGeneralConfig,
    setRipeRewardsConfig,
    setAssetConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    alpha_token,
    alpha_token_whale,
    bob,
):
    setGeneralConfig()
    setRipeRewardsConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=0)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, amount, alpha_token, alpha_token_whale)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    alpha_token.transfer(bob, amount, sender=alpha_token_whale)
    alpha_token.approve(teller.address, amount, sender=bob)
    gas_before = boa.env.get_gas_used()
    teller.deposit(alpha_token, amount, bob, simple_erc20_vault, sender=bob)
    _print_gas("basic_vault_steady_deposit", boa.env.get_gas_used() - gas_before, BASIC_DEPOSIT_CEILING)
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 2 * amount

    gas_before = boa.env.get_gas_used()
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    _print_gas("basic_vault_steady_checkpoint", boa.env.get_gas_used() - gas_before, BASIC_CHECKPOINT_CEILING)
    user_points, asset_points, _ = lootbox.getLatestDepositPoints(bob, vault_id, alpha_token)
    assert asset_points.lastUsdValue > 0
    assert user_points.lastBalance > 0

    gas_before = boa.env.get_gas_used()
    withdrawn = teller.withdraw(alpha_token, amount, bob, simple_erc20_vault, sender=bob)
    _print_gas("basic_vault_steady_withdraw", boa.env.get_gas_used() - gas_before, BASIC_WITHDRAW_CEILING)
    assert withdrawn == amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == amount


def test_gas_shares_vault_checkpoint(
    setGeneralConfig,
    setRipeRewardsConfig,
    setAssetConfig,
    performDeposit,
    mock_price_source,
    rebase_erc20_vault,
    vault_book,
    lootbox,
    teller,
    alpha_token,
    alpha_token_whale,
    bob,
):
    setGeneralConfig()
    setRipeRewardsConfig()
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_book.getRegId(rebase_erc20_vault)],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(rebase_erc20_vault)
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, amount, alpha_token, alpha_token_whale, rebase_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)
    before = lootbox.getLatestDepositPoints(bob, vault_id, alpha_token)[1].lastUsdValue

    gas_before = boa.env.get_gas_used()
    lootbox.updateDepositPoints(bob, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)
    _print_gas("shares_vault_steady_checkpoint", boa.env.get_gas_used() - gas_before, SHARES_CHECKPOINT_CEILING)
    after = lootbox.getLatestDepositPoints(bob, vault_id, alpha_token)[1].lastUsdValue
    assert after > 0
    assert after == before


def test_gas_redemption(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    simple_erc20_vault,
    vault_book,
    ledger,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=0, _minKeeperFee=0)
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
        _shouldAuctionInstantly=False,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    redeem_collateral(
        teller,
        bob,
        vault_id,
        alpha_token,
        5 * EIGHTEEN_DECIMALS,
        False,
        False,
        False,
        sender=alice,
    )
    alice_before = alpha_token.balanceOf(alice)
    debt_before = ledger.userDebt(bob).amount
    gas_before = boa.env.get_gas_used()
    redeem_collateral(
        teller,
        bob,
        vault_id,
        alpha_token,
        5 * EIGHTEEN_DECIMALS,
        False,
        False,
        False,
        sender=alice,
    )
    _print_gas("redemption_steady", boa.env.get_gas_used() - gas_before, REDEMPTION_CEILING)
    assert alpha_token.balanceOf(alice) > alice_before
    assert ledger.userDebt(bob).amount < debt_before


def test_gas_auction_purchase(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=0, _minKeeperFee=0)
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
            _startDiscount=10_00,
            _maxDiscount=40_00,
            _delay=0,
            _duration=100,
        ),
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(alpha_token, 50 * EIGHTEEN_DECIMALS // 100)
    teller.liquidateUser(bob, False, sender=sally)
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    auction = filter_logs(teller, "FungibleAuctionUpdated")[0]
    buy_fungible_auction(
        teller,
        bob,
        auction.vaultId,
        alpha_token,
        5 * EIGHTEEN_DECIMALS,
        False,
        sender=alice,
    )
    boa.env.time_travel(blocks=1)
    alice_before = alpha_token.balanceOf(alice)
    gas_before = boa.env.get_gas_used()
    spent = buy_fungible_auction(
        teller,
        bob,
        auction.vaultId,
        alpha_token,
        5 * EIGHTEEN_DECIMALS,
        False,
        sender=alice,
    )
    _print_gas("auction_purchase_steady", boa.env.get_gas_used() - gas_before, AUCTION_CEILING)
    assert spent > 0
    assert alpha_token.balanceOf(alice) > alice_before


@pytest.mark.parametrize("user_count", [1, 2, 5])
def test_gas_stab_liquidation(
    user_count,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    alpha_token,
    alpha_token_whale,
    green_token,
    savings_green,
    whale,
    stability_pool,
    teller,
    credit_engine,
    mission_control,
    switchboard_alpha,
    vault_book,
    sally,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    stab_id = vault_book.getRegId(stability_pool)
    setAssetConfig(
        alpha_token,
        _debtTerms=createDebtTerms(
            _ltv=50_00,
            _liqThreshold=80_00,
            _liqFee=0,
            _borrowRate=0,
        ),
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )
    setAssetConfig(
        savings_green,
        _vaultIds=[stab_id],
        _debtTerms=createDebtTerms(0, 0, 0, 0, 0, 0),
        _shouldBurnAsPayment=True,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mission_control.setPriorityStabVaults(
        [(stab_id, savings_green)], sender=switchboard_alpha.address
    )
    pool_amount = 80 * EIGHTEEN_DECIMALS * user_count
    green_token.transfer(sally, pool_amount, sender=whale)
    green_token.approve(savings_green, pool_amount, sender=sally)
    pool_shares = savings_green.deposit(pool_amount, sally, sender=sally)
    savings_green.approve(teller, pool_shares, sender=sally)
    teller.deposit(savings_green, pool_shares, sally, stability_pool, sender=sally)
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    debt_amount = 50 * EIGHTEEN_DECIMALS
    users = [boa.env.generate_address(f"stab-liq-{i}") for i in range(user_count)]
    for user in users:
        performDeposit(user, deposit_amount, alpha_token, alpha_token_whale)
        teller.borrow(debt_amount, user, False, sender=user)
    mock_price_source.setPrice(alpha_token, 40 * EIGHTEEN_DECIMALS // 100)
    gas_before = boa.env.get_gas_used()
    teller.liquidateManyUsers(users, False, sender=sally)
    _print_gas(
        f"stab_liq_{user_count}_users",
        boa.env.get_gas_used() - gas_before,
        STAB_LIQ_CEILINGS[user_count],
    )
    for user in users:
        assert credit_engine.getUserDebtAmount(user) < debt_amount


def test_gas_deleverage_many_users(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    simple_erc20_vault,
    vault_book,
    lootbox,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_alpha,
    bob,
    credit_engine,
):
    # Trusted batch path that actually settles (endaoment transfer), so the
    # per-user Addys re-resolution on _checkpointSender is measured.
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    setRipeRewardsConfig(True, 10, 0, 0, 0, 10_000)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
        _debtTerms=createDebtTerms(
            _ltv=80_00,
            _redemptionThreshold=85_00,
            _liqThreshold=90_00,
            _liqFee=0,
            _borrowRate=0,
        ),
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=False,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mission_control.setPriorityLiqAssetVaults(
        [(vault_id, alpha_token)], sender=switchboard_alpha.address
    )
    performDeposit(bob, 1_000 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(200 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    debt_before = credit_engine.getUserDebtAmount(bob)
    gas_before = boa.env.get_gas_used()
    teller.deleverageManyUsers([(bob, 0)], sender=switchboard_alpha.address)
    _print_gas("deleverage_many_one_user", boa.env.get_gas_used() - gas_before, DELEVERAGE_MANY_CEILING)
    assert credit_engine.getUserDebtAmount(bob) < debt_before
