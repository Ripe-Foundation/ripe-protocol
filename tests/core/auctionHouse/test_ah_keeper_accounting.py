import boa
import pytest

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT, MAX_UINT256
from conf_utils import filter_logs


DUST = 10**6


@pytest.fixture(scope="session")
def keeper_accounting_glp(governance):
    return boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "Keeper Accounting LP",
        "KALP",
        18,
        1_000_000_000,
        name="keeper_accounting_glp",
    )


@pytest.fixture(scope="session")
def keeper_accounting_glp_whale(env, keeper_accounting_glp, governance):
    holder = env.generate_address("keeper_accounting_glp_whale")
    keeper_accounting_glp.mint(
        holder,
        100_000_000 * EIGHTEEN_DECIMALS,
        sender=governance.address,
    )
    return holder


def _clear_transient():
    boa.env.evm.vm.state.clear_transient_storage()


def _configure_collateral(
    setAssetConfig,
    createDebtTerms,
    asset,
    vault_id,
    *,
    liq_fee=10_00,
    should_swap=True,
    should_auction=False,
):
    setAssetConfig(
        asset,
        _vaultIds=[vault_id],
        _debtTerms=createDebtTerms(
            _ltv=30_00,
            _redemptionThreshold=40_00,
            _liqThreshold=50_00,
            _liqFee=liq_fee,
            _borrowRate=0,
        ),
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=should_swap,
        _shouldAuctionInstantly=should_auction,
    )


def _configure_glp_stability(
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    mission_control,
    switchboard_alpha,
    stability_pool,
    vault_book,
    keeper_accounting_glp,
):
    stab_id = vault_book.getRegId(stability_pool)
    setAssetConfig(
        keeper_accounting_glp,
        _vaultIds=[stab_id],
        _debtTerms=createDebtTerms(0, 0, 0, 0, 0, 0),
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=True,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=False,
    )
    mock_price_source.setPrice(keeper_accounting_glp, EIGHTEEN_DECIMALS)
    mission_control.setPriorityStabVaults(
        [(stab_id, keeper_accounting_glp)],
        sender=switchboard_alpha.address,
    )


def _fund_glp_pool(
    amount,
    provider,
    keeper_accounting_glp,
    keeper_accounting_glp_whale,
    teller,
    stability_pool,
):
    keeper_accounting_glp.transfer(
        provider,
        amount,
        sender=keeper_accounting_glp_whale,
    )
    keeper_accounting_glp.approve(teller, amount, sender=provider)
    teller.deposit(
        keeper_accounting_glp,
        amount,
        provider,
        stability_pool,
        0,
        sender=provider,
    )


def _open_position(
    user,
    collateral_amount,
    debt_amount,
    alpha_token,
    alpha_token_whale,
    teller,
    simple_erc20_vault,
):
    alpha_token.transfer(user, collateral_amount, sender=alpha_token_whale)
    alpha_token.approve(teller, collateral_amount, sender=user)
    teller.deposit(
        alpha_token,
        collateral_amount,
        user,
        simple_erc20_vault,
        0,
        sender=user,
    )
    teller.borrow(debt_amount, user, False, sender=user)


def test_keeper_green_is_backed_when_glp_stability_covers_liquidation(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    alpha_token,
    alpha_token_whale,
    keeper_accounting_glp,
    keeper_accounting_glp_whale,
    green_token,
    mock_price_source,
    simple_erc20_vault,
    stability_pool,
    endaoment_funds,
    teller,
    credit_engine,
    ledger,
    mission_control,
    switchboard_alpha,
    vault_book,
    bob,
    sally,
):
    setGeneralConfig()
    setGeneralDebtConfig(
        _keeperFeeRatio=5_00,
        _minKeeperFee=0,
        _maxKeeperFee=MAX_UINT256,
        _ltvPaybackBuffer=1_00,
    )
    simple_id = vault_book.getRegId(simple_erc20_vault)
    _configure_collateral(
        setAssetConfig,
        createDebtTerms,
        alpha_token,
        simple_id,
    )
    _configure_glp_stability(
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        mission_control,
        switchboard_alpha,
        stability_pool,
        vault_book,
        keeper_accounting_glp,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _fund_glp_pool(
        3_000 * EIGHTEEN_DECIMALS,
        sally,
        keeper_accounting_glp,
        keeper_accounting_glp_whale,
        teller,
        stability_pool,
    )
    _open_position(
        bob,
        4_000 * EIGHTEEN_DECIMALS,
        1_000 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        teller,
        simple_erc20_vault,
    )
    mock_price_source.setPrice(alpha_token, 45 * EIGHTEEN_DECIMALS // 100)
    assert credit_engine.canLiquidateUser(bob)

    supply_before = green_token.totalSupply()
    debt_before = ledger.totalDebt()
    user_debt_before = ledger.userDebt(bob).amount
    reserve_before = keeper_accounting_glp.balanceOf(endaoment_funds)
    keeper_before = green_token.balanceOf(sally)
    backing_before = debt_before + reserve_before - supply_before

    _clear_transient()
    teller.liquidateUser(bob, False, sender=sally)
    log = filter_logs(teller, "LiquidateUser")[0]

    supply_after = green_token.totalSupply()
    debt_after = ledger.totalDebt()
    reserve_after = keeper_accounting_glp.balanceOf(endaoment_funds)
    backing_after = debt_after + reserve_after - supply_after

    assert log.totalLiqFees == 150 * EIGHTEEN_DECIMALS
    assert log.keeperFee == 50 * EIGHTEEN_DECIMALS
    base_fee = log.totalLiqFees - log.keeperFee
    paid_base = min(
        log.collateralValueOut - log.repayAmount,
        base_fee,
    )
    unpaid_base = base_fee - paid_base
    assert log.liqFeesUnpaid == unpaid_base + log.keeperFee
    assert ledger.userDebt(bob).amount == (
        user_debt_before + log.liqFeesUnpaid - log.repayAmount
    )
    assert debt_after == debt_before + log.liqFeesUnpaid - log.repayAmount
    assert supply_after - supply_before == log.keeperFee
    assert green_token.balanceOf(sally) - keeper_before == log.keeperFee
    assert abs((reserve_after - reserve_before) - log.repayAmount) <= DUST
    assert abs((backing_after - backing_before) - unpaid_base) <= DUST


def test_keeper_green_is_backed_when_sgreen_stability_burns_payment(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    alpha_token,
    alpha_token_whale,
    green_token,
    savings_green,
    whale,
    mock_price_source,
    simple_erc20_vault,
    stability_pool,
    teller,
    credit_engine,
    ledger,
    mission_control,
    switchboard_alpha,
    vault_book,
    alice,
    sally,
):
    setGeneralConfig()
    setGeneralDebtConfig(
        _keeperFeeRatio=5_00,
        _minKeeperFee=0,
        _maxKeeperFee=MAX_UINT256,
        _ltvPaybackBuffer=1_00,
    )
    simple_id = vault_book.getRegId(simple_erc20_vault)
    stab_id = vault_book.getRegId(stability_pool)
    _configure_collateral(
        setAssetConfig,
        createDebtTerms,
        alpha_token,
        simple_id,
    )
    setAssetConfig(
        savings_green,
        _vaultIds=[stab_id],
        _debtTerms=createDebtTerms(0, 0, 0, 0, 0, 0),
        _shouldBurnAsPayment=True,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mission_control.setPriorityStabVaults(
        [(stab_id, savings_green)],
        sender=switchboard_alpha.address,
    )

    pool_amount = 3_000 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, pool_amount, sender=whale)
    green_token.approve(savings_green, pool_amount, sender=sally)
    pool_shares = savings_green.deposit(pool_amount, sally, sender=sally)
    savings_green.approve(teller, pool_shares, sender=sally)
    teller.deposit(
        savings_green,
        pool_shares,
        sally,
        stability_pool,
        0,
        sender=sally,
    )
    _open_position(
        alice,
        4_000 * EIGHTEEN_DECIMALS,
        1_000 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        teller,
        simple_erc20_vault,
    )
    mock_price_source.setPrice(alpha_token, 45 * EIGHTEEN_DECIMALS // 100)
    assert credit_engine.canLiquidateUser(alice)

    supply_before = green_token.totalSupply()
    debt_before = ledger.totalDebt()
    user_debt_before = ledger.userDebt(alice).amount
    keeper_green_before = green_token.balanceOf(sally)
    keeper_sgreen_before = savings_green.balanceOf(sally)

    _clear_transient()
    keeper_rewards = teller.liquidateUser(alice, True, sender=sally)
    log = filter_logs(teller, "LiquidateUser")[0]

    supply_after = green_token.totalSupply()
    debt_after = ledger.totalDebt()
    keeper_sgreen_received = (
        savings_green.balanceOf(sally) - keeper_sgreen_before
    )
    burned = supply_before + log.keeperFee - supply_after

    assert log.keeperFee == 50 * EIGHTEEN_DECIMALS
    base_fee = log.totalLiqFees - log.keeperFee
    paid_base = min(
        log.collateralValueOut - log.repayAmount,
        base_fee,
    )
    unpaid_base = base_fee - paid_base
    assert log.liqFeesUnpaid == unpaid_base + log.keeperFee
    assert keeper_rewards == log.keeperFee
    assert green_token.balanceOf(sally) == keeper_green_before
    assert keeper_sgreen_received > 0
    assert abs(
        savings_green.convertToAssets(keeper_sgreen_received) - log.keeperFee
    ) <= DUST
    assert abs(burned - log.repayAmount) <= DUST
    assert ledger.userDebt(alice).amount == (
        user_debt_before + log.liqFeesUnpaid - log.repayAmount
    )
    assert debt_after == debt_before + log.liqFeesUnpaid - log.repayAmount
    assert abs(
        (debt_after - supply_after)
        - (debt_before - supply_before)
        - unpaid_base
    ) <= DUST


def test_mixed_stability_and_auction_books_keeper_and_unpaid_base_fee(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    alpha_token,
    alpha_token_whale,
    keeper_accounting_glp,
    keeper_accounting_glp_whale,
    green_token,
    mock_price_source,
    simple_erc20_vault,
    stability_pool,
    teller,
    credit_engine,
    ledger,
    mission_control,
    switchboard_alpha,
    vault_book,
    bob,
    sally,
):
    setGeneralConfig()
    setGeneralDebtConfig(
        _keeperFeeRatio=5_00,
        _minKeeperFee=0,
        _maxKeeperFee=MAX_UINT256,
        _ltvPaybackBuffer=1_00,
    )
    simple_id = vault_book.getRegId(simple_erc20_vault)
    _configure_collateral(
        setAssetConfig,
        createDebtTerms,
        alpha_token,
        simple_id,
        should_auction=True,
    )
    _configure_glp_stability(
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        mission_control,
        switchboard_alpha,
        stability_pool,
        vault_book,
        keeper_accounting_glp,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _fund_glp_pool(
        100 * EIGHTEEN_DECIMALS,
        sally,
        keeper_accounting_glp,
        keeper_accounting_glp_whale,
        teller,
        stability_pool,
    )
    _open_position(
        bob,
        4_000 * EIGHTEEN_DECIMALS,
        1_000 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        teller,
        simple_erc20_vault,
    )
    mock_price_source.setPrice(alpha_token, 45 * EIGHTEEN_DECIMALS // 100)
    assert credit_engine.canLiquidateUser(bob)

    supply_before = green_token.totalSupply()
    debt_before = ledger.userDebt(bob).amount
    _clear_transient()
    teller.liquidateUser(bob, False, sender=sally)
    log = filter_logs(teller, "LiquidateUser")[0]

    paid_base = min(
        log.collateralValueOut - log.repayAmount,
        log.totalLiqFees - log.keeperFee,
    )
    assert log.repayAmount > 0
    assert log.numAuctionsStarted == 1
    assert ledger.hasFungibleAuctions(bob)
    assert log.liqFeesUnpaid == log.totalLiqFees - paid_base
    assert log.liqFeesUnpaid >= log.keeperFee
    assert ledger.userDebt(bob).amount == debt_before + log.liqFeesUnpaid - log.repayAmount
    assert green_token.totalSupply() - supply_before == log.keeperFee


def test_expired_pure_auction_retry_does_not_repeat_first_pass_fees(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    alpha_token,
    alpha_token_whale,
    green_token,
    mock_price_source,
    simple_erc20_vault,
    teller,
    credit_engine,
    ledger,
    auction_house,
    vault_book,
    bob,
    sally,
):
    setGeneralConfig()
    setGeneralDebtConfig(
        _keeperFeeRatio=5_00,
        _minKeeperFee=0,
        _maxKeeperFee=MAX_UINT256,
        _ltvPaybackBuffer=1_00,
    )
    simple_id = vault_book.getRegId(simple_erc20_vault)
    _configure_collateral(
        setAssetConfig,
        createDebtTerms,
        alpha_token,
        simple_id,
        should_swap=False,
        should_auction=True,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _open_position(
        bob,
        4_000 * EIGHTEEN_DECIMALS,
        1_000 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        teller,
        simple_erc20_vault,
    )
    mock_price_source.setPrice(alpha_token, 45 * EIGHTEEN_DECIMALS // 100)
    assert credit_engine.canLiquidateUser(bob)

    supply_before = green_token.totalSupply()
    debt_before = ledger.userDebt(bob).amount
    _clear_transient()
    teller.liquidateUser(bob, False, sender=sally)
    log = filter_logs(teller, "LiquidateUser")[0]

    assert log.repayAmount == 0
    assert log.collateralValueOut == 0
    assert log.numAuctionsStarted == 1
    assert log.totalLiqFees > 0
    assert log.liqFeesUnpaid == log.totalLiqFees
    assert log.keeperFee > 0
    debt_after_first_pass = ledger.userDebt(bob).amount
    supply_after_first_pass = green_token.totalSupply()
    assert debt_after_first_pass == debt_before + log.totalLiqFees
    assert supply_after_first_pass == supply_before + log.keeperFee

    auction = filter_logs(teller, "FungibleAuctionUpdated")[0]
    boa.env.time_travel(blocks=auction.endBlock - boa.env.evm.patch.block_number)
    assert auction_house.removeExpiredFungibleAuction(
        bob,
        auction.vaultId,
        alpha_token,
        sender=sally,
    )
    assert not ledger.hasFungibleAuctions(bob)

    _clear_transient()
    teller.liquidateUser(bob, False, sender=sally)
    retry_log = filter_logs(teller, "LiquidateUser")[0]
    assert retry_log.repayAmount == 0
    assert retry_log.numAuctionsStarted == 1
    assert retry_log.totalLiqFees == 0
    assert retry_log.liqFeesUnpaid == 0
    assert retry_log.keeperFee == 0
    assert ledger.userDebt(bob).amount == debt_after_first_pass
    assert green_token.totalSupply() == supply_after_first_pass


def test_deeply_underwater_min_keeper_fee_produces_zero_spread_and_zero_mint(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    alpha_token,
    alpha_token_whale,
    keeper_accounting_glp,
    keeper_accounting_glp_whale,
    green_token,
    mock_price_source,
    simple_erc20_vault,
    stability_pool,
    teller,
    credit_engine,
    mission_control,
    switchboard_alpha,
    vault_book,
    bob,
    sally,
):
    setGeneralConfig()
    setGeneralDebtConfig(
        _keeperFeeRatio=10_00,
        _minKeeperFee=5 * EIGHTEEN_DECIMALS,
        _maxKeeperFee=50 * EIGHTEEN_DECIMALS,
        _ltvPaybackBuffer=0,
    )
    simple_id = vault_book.getRegId(simple_erc20_vault)
    _configure_collateral(
        setAssetConfig,
        createDebtTerms,
        alpha_token,
        simple_id,
    )
    _configure_glp_stability(
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        mission_control,
        switchboard_alpha,
        stability_pool,
        vault_book,
        keeper_accounting_glp,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _fund_glp_pool(
        200 * EIGHTEEN_DECIMALS,
        sally,
        keeper_accounting_glp,
        keeper_accounting_glp_whale,
        teller,
        stability_pool,
    )
    _open_position(
        bob,
        200 * EIGHTEEN_DECIMALS,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        teller,
        simple_erc20_vault,
    )
    recorded_debt, _, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    underwater_price = (
        recorded_debt.amount * EIGHTEEN_DECIMALS // collateral_amount
    )
    mock_price_source.setPrice(alpha_token, underwater_price)
    assert credit_engine.canLiquidateUser(bob)

    supply_before = green_token.totalSupply()
    keeper_before = green_token.balanceOf(sally)
    _clear_transient()
    teller.liquidateUser(bob, False, sender=sally)
    log = filter_logs(teller, "LiquidateUser")[0]

    assert log.totalLiqFees == 0
    assert log.liqFeesUnpaid == 0
    assert log.keeperFee == 0
    assert log.collateralValueOut == log.repayAmount
    assert green_token.totalSupply() == supply_before
    assert green_token.balanceOf(sally) == keeper_before


def test_reduced_base_fee_controls_stability_spread_ratio(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    alpha_token,
    alpha_token_whale,
    keeper_accounting_glp,
    keeper_accounting_glp_whale,
    mock_price_source,
    simple_erc20_vault,
    stability_pool,
    teller,
    credit_engine,
    mission_control,
    switchboard_alpha,
    vault_book,
    bob,
    sally,
):
    setGeneralConfig()
    setGeneralDebtConfig(
        _keeperFeeRatio=0,
        _minKeeperFee=0,
        _maxKeeperFee=MAX_UINT256,
        _ltvPaybackBuffer=0,
    )
    simple_id = vault_book.getRegId(simple_erc20_vault)
    _configure_collateral(
        setAssetConfig,
        createDebtTerms,
        alpha_token,
        simple_id,
    )
    _configure_glp_stability(
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        mission_control,
        switchboard_alpha,
        stability_pool,
        vault_book,
        keeper_accounting_glp,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _fund_glp_pool(
        200 * EIGHTEEN_DECIMALS,
        sally,
        keeper_accounting_glp,
        keeper_accounting_glp_whale,
        teller,
        stability_pool,
    )
    _open_position(
        bob,
        200 * EIGHTEEN_DECIMALS,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        teller,
        simple_erc20_vault,
    )
    recorded_debt, _, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    reduced_base_fee = 5 * EIGHTEEN_DECIMALS
    collateral_amount = 200 * EIGHTEEN_DECIMALS
    reduced_fee_price = (
        (recorded_debt.amount + reduced_base_fee)
        * EIGHTEEN_DECIMALS
        // collateral_amount
    )
    mock_price_source.setPrice(alpha_token, reduced_fee_price)
    assert credit_engine.canLiquidateUser(bob)

    _clear_transient()
    teller.liquidateUser(bob, False, sender=sally)
    log = filter_logs(teller, "LiquidateUser")[0]

    assert log.totalLiqFees == reduced_base_fee
    assert log.keeperFee == 0
    reduced_ratio = (
        reduced_base_fee * HUNDRED_PERCENT // recorded_debt.amount
    )
    expected_repay = (
        log.collateralValueOut
        * (HUNDRED_PERCENT - reduced_ratio)
        // HUNDRED_PERCENT
    )
    assert abs(log.repayAmount - expected_repay) <= DUST
    configured_ratio_repay = (
        log.collateralValueOut
        * (HUNDRED_PERCENT - 10_00)
        // HUNDRED_PERCENT
    )
    assert abs(log.repayAmount - configured_ratio_repay) > EIGHTEEN_DECIMALS
