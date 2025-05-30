import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from conf_utils import filter_logs


def test_basic_borrow(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    teller,
    green_token,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_amount, bravo_token, bravo_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)
    bravo_price = 2 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(bravo_token, bravo_price)

    # collateral value
    collateral_value = credit_engine.getCollateralValue(bob)
    assert collateral_value == 300 * EIGHTEEN_DECIMALS

    # borrow
    borrow_amount = 100 * EIGHTEEN_DECIMALS
    amount = teller.borrow(borrow_amount, bob, False, sender=bob)

    log = filter_logs(teller, "NewBorrow")[0]
    assert log.user == bob
    assert log.newLoan == borrow_amount
    assert log.daowry == 0
    assert log.didReceiveSavingsGreen == False
    assert log.outstandingUserDebt == borrow_amount == amount
    assert log.userCollateralVal == collateral_value
    assert log.maxUserDebt == 150 * EIGHTEEN_DECIMALS # default is 50% ltv
    assert log.globalYieldRealized == 0

    # check balance
    assert green_token.balanceOf(bob) == borrow_amount


def test_borrow_protocol_disabled(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
):
    # basic setup with protocol borrows disabled
    setGeneralConfig(_canBorrow=False)
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Attempt borrow should fail
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    with boa.reverts("borrow not enabled"):
        teller.borrow(borrow_amount, bob, False, sender=bob)


def test_borrow_user_not_allowed(
    alpha_token,
    alpha_token_whale,
    setUserDelegation,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
):
    # basic setup with user not allowed to borrow
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Attempt borrow should fail
    borrow_amount = 100 * EIGHTEEN_DECIMALS
    with boa.reverts("cannot borrow for user"):
        teller.borrow(borrow_amount, bob, False, sender=sally)

    # allow sally to withdraw for bob
    setUserDelegation(bob, sally, _canBorrow=True)

    # borrow should succeed
    teller.borrow(borrow_amount, bob, False, sender=sally)


def test_borrow_max_borrowers_reached(
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
):
    # basic setup with max borrowers = 1
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig(_numAllowedBorrowers=1)

    # deposits for both users
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(sally, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # First borrow should succeed
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Second borrow should fail
    with boa.reverts("max num borrowers reached"):
        teller.borrow(borrow_amount, sally, False, sender=sally)


def test_borrow_ltv_limit(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
):
    # basic setup with 50% LTV
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(bravo_token)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_amount, bravo_token, bravo_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)
    bravo_price = 2 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(bravo_token, bravo_price)

    # collateral value is 300 (100 * 1 + 100 * 2)
    # max borrow at 50% LTV is 150
    desired_borrow_amount = 200 * EIGHTEEN_DECIMALS
    amount = teller.borrow(desired_borrow_amount, bob, False, sender=bob)

    # borrow up to LTV limit should succeed
    assert amount == 150 * EIGHTEEN_DECIMALS

    # ltv reached
    with boa.reverts("no debt available"):
        teller.borrow(1 * EIGHTEEN_DECIMALS, bob, False, sender=bob)


def test_borrow_interval_limit(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
):
    # basic setup with interval limits
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig(_maxBorrowPerInterval=50 * EIGHTEEN_DECIMALS, _numBlocksPerInterval=10)

    # deposits
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # First borrow should succeed
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Second borrow in same interval should fail
    with boa.reverts("interval borrow limit reached"):
        teller.borrow(borrow_amount, bob, False, sender=bob)


def test_borrow_per_user_limit(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
):
    # basic setup with per user limit
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig(_perUserDebtLimit=50 * EIGHTEEN_DECIMALS)

    # deposits
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # First borrow should succeed
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Second borrow should fail
    with boa.reverts("per user debt limit reached"):
        teller.borrow(borrow_amount, bob, False, sender=bob)


def test_borrow_global_limit(
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
):
    # basic setup with global limit
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig(_globalDebtLimit=100 * EIGHTEEN_DECIMALS)

    # deposits for both users
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(sally, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # First borrow should succeed
    borrow_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # Second borrow should fail
    with boa.reverts("global debt limit reached"):
        teller.borrow(borrow_amount, sally, False, sender=sally)


def test_borrow_min_debt_amount(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
):
    # basic setup with minimum debt amount
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig(_minDebtAmount=100 * EIGHTEEN_DECIMALS)

    # deposits
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Attempt borrow below minimum should fail
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    with boa.reverts("debt too small"):
        teller.borrow(borrow_amount, bob, False, sender=bob)

    # borrow at minimum amount should succeed
    borrow_amount = 100 * EIGHTEEN_DECIMALS
    amount = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert amount == borrow_amount


def test_borrow_zero_amount(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # Attempt borrow of zero amount should fail
    with boa.reverts("cannot borrow 0 amount"):
        teller.borrow(0, bob, False, sender=bob)


def test_borrow_user_in_liquidation(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    teller,
    ledger,
    createDebtTerms,
    credit_engine,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # set user debt in liquidation
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, True)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)
    assert ledger.isUserInLiquidation(bob)

    # Attempt borrow should fail
    with boa.reverts("cannot borrow in liquidation"):
        teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)


def test_borrow_zero_address_user(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # user cannot be 0x0
    with boa.reverts("cannot borrow for 0x0"):
        teller.borrow(100 * EIGHTEEN_DECIMALS, ZERO_ADDRESS, False, sender=bob)


def test_borrow_credit_engine_paused(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    mission_control_gov,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # pause the credit engine
    teller.pause(True, sender=mission_control_gov.address)
    assert teller.isPaused()

    # Attempt borrow should fail
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    with boa.reverts("contract paused"):
        teller.borrow(borrow_amount, bob, False, sender=bob)

    # unpause the credit engine
    teller.pause(False, sender=mission_control_gov.address)
    assert not teller.isPaused()

    # borrow should now succeed
    amount = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert amount == borrow_amount


def test_borrow_updates_ledger_state(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    ledger,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # verify initial state
    assert ledger.getNumBorrowers() == 0
    assert ledger.numBorrowers() == 0
    assert not ledger.isBorrower(bob)
    assert ledger.totalDebt() == 0

    # borrow
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    amount = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert amount == borrow_amount

    # verify ledger state after borrow
    assert ledger.getNumBorrowers() == 1
    assert ledger.numBorrowers() == 2
    assert ledger.isBorrower(bob)
    assert ledger.totalDebt() == borrow_amount
    assert ledger.indexOfBorrower(bob) == 1
    assert ledger.borrowers(1) == bob

    # verify user debt
    user_debt = ledger.userDebt(bob)
    assert user_debt.amount == borrow_amount
    assert user_debt.principal == borrow_amount
    assert not user_debt.inLiquidation

    # verify borrow interval
    interval = ledger.borrowIntervals(bob)
    assert interval.start == boa.env.evm.patch.block_number
    assert interval.amount == borrow_amount


def test_borrow_updates_ledger_state_multiple_borrowers(
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    ledger,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposits for both users
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(sally, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # verify initial state
    assert ledger.getNumBorrowers() == 0
    assert ledger.numBorrowers() == 0
    assert not ledger.isBorrower(bob)
    assert not ledger.isBorrower(sally)
    assert ledger.totalDebt() == 0

    # first borrow
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    amount = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert amount == borrow_amount

    # verify ledger state after first borrow
    assert ledger.getNumBorrowers() == 1
    assert ledger.numBorrowers() == 2
    assert ledger.isBorrower(bob)
    assert not ledger.isBorrower(sally)
    assert ledger.totalDebt() == borrow_amount
    assert ledger.indexOfBorrower(bob) == 1
    assert ledger.borrowers(1) == bob

    # second borrow
    amount = teller.borrow(borrow_amount, sally, False, sender=sally)
    assert amount == borrow_amount

    # verify ledger state after second borrow
    assert ledger.getNumBorrowers() == 2
    assert ledger.numBorrowers() == 3
    assert ledger.isBorrower(bob)
    assert ledger.isBorrower(sally)
    assert ledger.totalDebt() == borrow_amount * 2
    assert ledger.indexOfBorrower(bob) == 1
    assert ledger.indexOfBorrower(sally) == 2
    assert ledger.borrowers(1) == bob
    assert ledger.borrowers(2) == sally

    # verify user debts
    bob_debt = ledger.userDebt(bob)
    sally_debt = ledger.userDebt(sally)
    assert bob_debt.amount == borrow_amount
    assert sally_debt.amount == borrow_amount
    assert not bob_debt.inLiquidation
    assert not sally_debt.inLiquidation


def test_borrow_updates_ledger_state_interval(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    ledger,
):
    # basic setup with interval limits
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig(_maxBorrowPerInterval=100 * EIGHTEEN_DECIMALS, _numBlocksPerInterval=10)

    # deposits
    deposit_amount = 400 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # first borrow
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    amount = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert amount == borrow_amount

    # verify initial interval state
    interval = ledger.borrowIntervals(bob)
    assert interval.start == boa.env.evm.patch.block_number
    assert interval.amount == borrow_amount
    orig_start = interval.start

    # second borrow in same interval
    amount = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert amount == borrow_amount

    # verify updated interval state
    interval = ledger.borrowIntervals(bob)
    assert interval.start == orig_start
    assert interval.amount == borrow_amount * 2

    # move blocks forward to new interval
    boa.env.time_travel(blocks=11)

    # borrow in new interval
    amount = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert amount == borrow_amount

    # verify new interval state
    interval = ledger.borrowIntervals(bob)
    assert interval.start == boa.env.evm.patch.block_number
    assert interval.amount == borrow_amount


def test_borrow_mints_unrealized_yield(
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    ledger,
    savings_green,
    green_token,
    createDebtTerms,
    credit_engine,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # set up unrealized yield in ledger
    debt_terms = createDebtTerms()
    user_debt = (0, 0, debt_terms, 0, False)
    unrealized_yield = 10 * EIGHTEEN_DECIMALS
    ledger.setUserDebt(sally, user_debt, unrealized_yield, (0, 0), sender=credit_engine.address)
    assert ledger.unrealizedYield() == unrealized_yield

    # verify initial balances
    assert green_token.balanceOf(savings_green) == 0

    # borrow
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    amount = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert amount == borrow_amount

    # verify unrealized yield was minted and sent to savings_green
    assert ledger.unrealizedYield() == 0
    assert green_token.balanceOf(savings_green) == unrealized_yield

    # verify borrow amount was also minted
    assert green_token.balanceOf(bob) == borrow_amount


def test_borrow_daowry(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    savings_green,
    green_token,
    createDebtTerms,
):
    # basic setup with daowry enabled
    setGeneralConfig()
    debt_terms = createDebtTerms(_daowry=1_00)  # 1% daowry
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_isDaowryEnabled=True)

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # verify initial balances
    assert green_token.balanceOf(savings_green) == 0
    assert green_token.balanceOf(bob) == 0

    # borrow
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # calculate expected daowry (1% of borrow amount)
    expected_daowry = borrow_amount * 1_00 // 100_00
    expected_borrower_amount = borrow_amount - expected_daowry

    # verify borrow log
    log = filter_logs(teller, "NewBorrow")[0]
    assert log.user == bob
    assert log.newLoan == expected_borrower_amount
    assert log.daowry == expected_daowry
    assert log.didReceiveSavingsGreen == False
    assert log.outstandingUserDebt == borrow_amount
    assert log.globalYieldRealized == 0

    # verify balances
    assert green_token.balanceOf(savings_green) == expected_daowry
    assert green_token.balanceOf(bob) == expected_borrower_amount


def test_borrow_savings_green(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    savings_green,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # verify initial balances
    assert green_token.balanceOf(bob) == 0
    assert savings_green.balanceOf(bob) == 0

    # borrow with savings_green
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    amount = teller.borrow(borrow_amount, bob, True, sender=bob)  # _wantsSavingsGreen=True

    # verify borrow log
    log = filter_logs(teller, "NewBorrow")[0]
    assert log.user == bob
    assert log.newLoan == borrow_amount
    assert log.didReceiveSavingsGreen == True
    assert log.outstandingUserDebt == borrow_amount

    # verify balances
    assert green_token.balanceOf(bob) == 0  # no regular green tokens
    assert savings_green.balanceOf(bob) != 0  # received savings_green instead


################
# Borrow Terms #
################


def test_get_user_borrow_terms_single_asset(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    createDebtTerms,
):
    # basic setup
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,  # 50%
        _redemptionThreshold=60_00,  # 60%
        _liqThreshold=70_00,  # 70%
        _liqFee=10_00,  # 10%
        _borrowRate=5_00,  # 5%
        _daowry=1_00,  # 1%
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # get borrow terms
    terms = credit_engine.getUserBorrowTerms(bob, True)

    # verify terms match the single asset's terms
    assert terms.debtTerms.ltv == 50_00
    assert terms.debtTerms.redemptionThreshold == 60_00
    assert terms.debtTerms.liqThreshold == 70_00
    assert terms.debtTerms.liqFee == 10_00
    assert terms.debtTerms.borrowRate == 5_00
    assert terms.debtTerms.daowry == 1_00

    # verify collateral value and max debt
    assert terms.collateralVal == 100 * EIGHTEEN_DECIMALS  # 100 tokens at $1 each
    assert terms.totalMaxDebt == 50 * EIGHTEEN_DECIMALS  # 50% of collateral value


def test_get_user_borrow_terms_multiple_assets(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    createDebtTerms,
):
    # basic setup
    setGeneralConfig()
    
    # Asset 1: 50% LTV, 100 tokens at $1 each = $100 collateral, $50 max debt
    alpha_debt_terms = createDebtTerms(
        _ltv=50_00,  # 50%
        _redemptionThreshold=60_00,  # 60%
        _liqThreshold=70_00,  # 70%
        _liqFee=10_00,  # 10%
        _borrowRate=5_00,  # 5%
        _daowry=1_00,  # 1%
    )
    
    # Asset 2: 75% LTV, 100 tokens at $2 each = $200 collateral, $150 max debt
    bravo_debt_terms = createDebtTerms(
        _ltv=75_00,  # 75%
        _redemptionThreshold=80_00,  # 80%
        _liqThreshold=85_00,  # 85%
        _liqFee=15_00,  # 15%
        _borrowRate=7_00,  # 7%
        _daowry=2_00,  # 2%
    )
    
    setAssetConfig(alpha_token, _debtTerms=alpha_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_debt_terms)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_amount, bravo_token, bravo_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    bravo_price = 2 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)
    mock_price_source.setPrice(bravo_token, bravo_price)

    # get borrow terms
    terms = credit_engine.getUserBorrowTerms(bob, True)

    # Total collateral value = $100 + $200 = $300
    # Total max debt = $50 + $150 = $200
    # Weighted terms:
    # - LTV: (50 * 50 + 150 * 75) / 200 = 68.75%
    # - Redemption: (50 * 60 + 150 * 80) / 200 = 75%
    # - Liq Threshold: (50 * 70 + 150 * 85) / 200 = 81.25%
    # - Liq Fee: (50 * 10 + 150 * 15) / 200 = 13.75%
    # - Borrow Rate: (50 * 5 + 150 * 7) / 200 = 6.5%
    # - Daowry: (50 * 1 + 150 * 2) / 200 = 1.75%

    assert terms.collateralVal == 300 * EIGHTEEN_DECIMALS  # $300 total collateral
    assert terms.totalMaxDebt == 200 * EIGHTEEN_DECIMALS  # $200 total max debt
    assert terms.debtTerms.ltv == 66_66  # 66.66% (200 * 100_00 / 300)
    assert terms.debtTerms.redemptionThreshold == 75_00  # 75%
    assert terms.debtTerms.liqThreshold == 81_25  # 81.25%
    assert terms.debtTerms.liqFee == 13_75  # 13.75%
    assert terms.debtTerms.borrowRate == 6_50  # 6.5%
    assert terms.debtTerms.daowry == 1_75  # 1.75%


def test_get_user_borrow_terms_liq_threshold_fee_adjustment(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    createDebtTerms,
):
    # Set up asset with high liqThreshold and liqFee so their sum exceeds 100%
    setGeneralConfig()
    # liqThreshold = 90%, liqFee = 20%
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=90_00,  # 90%
        _liqFee=20_00,        # 20%
        _borrowRate=5_00,
        _daowry=1_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock price
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # get borrow terms
    terms = credit_engine.getUserBorrowTerms(bob, True)

    # The contract should adjust liqFee so that liqThreshold + (liqThreshold * liqFee // 100_00) <= 100_00
    # adjustedLiqFee = (100_00 - liqThreshold) * 100_00 // liqThreshold
    expected_adjusted_liq_fee = (100_00 - 90_00) * 100_00 // 90_00  # = 11_11
    assert terms.debtTerms.liqThreshold == 90_00
    assert terms.debtTerms.liqFee == expected_adjusted_liq_fee
    # The sum should not exceed 100_00
    liq_sum = terms.debtTerms.liqThreshold + (terms.debtTerms.liqThreshold * terms.debtTerms.liqFee // 100_00)
    assert liq_sum <= 100_00


def test_get_user_borrow_terms_no_vaults(
    bob,
    credit_engine,
):
    # User has no vaults/collateral
    terms = credit_engine.getUserBorrowTerms(bob, True)
    assert terms.collateralVal == 0
    assert terms.totalMaxDebt == 0
    assert terms.debtTerms.ltv == 0
    assert terms.debtTerms.redemptionThreshold == 0
    assert terms.debtTerms.liqThreshold == 0
    assert terms.debtTerms.liqFee == 0
    assert terms.debtTerms.borrowRate == 0
    assert terms.debtTerms.daowry == 0


def test_get_user_borrow_terms_asset_with_zero_ltv(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    createDebtTerms,
):
    setGeneralConfig()
    # ltv=0, should be ignored
    debt_terms = createDebtTerms(_ltv=0, _redemptionThreshold=60_00, _liqThreshold=70_00, _liqFee=10_00, _borrowRate=5_00, _daowry=1_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    terms = credit_engine.getUserBorrowTerms(bob, True)
    assert terms.collateralVal == 0
    assert terms.totalMaxDebt == 0
    assert terms.debtTerms.ltv == 0


def test_get_user_borrow_terms_multiple_assets_some_zero_ltv(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    createDebtTerms,
):
    setGeneralConfig()
    # alpha: ltv=0, bravo: ltv=50%
    alpha_debt_terms = createDebtTerms(_ltv=0, _redemptionThreshold=60_00, _liqThreshold=70_00, _liqFee=10_00, _borrowRate=5_00, _daowry=1_00)
    bravo_debt_terms = createDebtTerms(_ltv=50_00, _redemptionThreshold=80_00, _liqThreshold=85_00, _liqFee=15_00, _borrowRate=7_00, _daowry=2_00)
    setAssetConfig(alpha_token, _debtTerms=alpha_debt_terms)
    setAssetConfig(bravo_token, _debtTerms=bravo_debt_terms)
    setGeneralDebtConfig()
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_amount, bravo_token, bravo_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    terms = credit_engine.getUserBorrowTerms(bob, True)
    # Only bravo_token should be counted
    assert terms.collateralVal == 200 * EIGHTEEN_DECIMALS
    assert terms.totalMaxDebt == 100 * EIGHTEEN_DECIMALS
    assert terms.debtTerms.ltv == 50_00
    assert terms.debtTerms.redemptionThreshold == 80_00
    assert terms.debtTerms.liqThreshold == 85_00
    assert terms.debtTerms.liqFee == 15_00
    assert terms.debtTerms.borrowRate == 700
    assert terms.debtTerms.daowry == 2_00


def test_get_user_borrow_terms_asset_with_zero_amount(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    credit_engine,
    createDebtTerms,
):
    setGeneralConfig()
    debt_terms = createDebtTerms(_ltv=50_00, _redemptionThreshold=60_00, _liqThreshold=70_00, _liqFee=10_00, _borrowRate=5_00, _daowry=1_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()
    # Manually ensure user has a vault but zero amount (simulate)
    # This requires direct manipulation or a fixture that allows it; here we just check that zero amount is ignored
    # (Assume the vault returns zero for getUserAssetAndAmountAtIndex)
    # So, no deposit is made
    terms = credit_engine.getUserBorrowTerms(bob, True)
    assert terms.collateralVal == 0
    assert terms.totalMaxDebt == 0
    assert terms.debtTerms.ltv == 0


def test_get_user_borrow_terms_asset_with_no_price(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    credit_engine,
    createDebtTerms,
):
    setGeneralConfig()
    debt_terms = createDebtTerms(_ltv=50_00, _redemptionThreshold=60_00, _liqThreshold=70_00, _liqFee=10_00, _borrowRate=5_00, _daowry=1_00)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # Set price to zero
    mock_price_source.setPrice(alpha_token, 0)
    terms = credit_engine.getUserBorrowTerms(bob, True)

    # Collateral value and max debt are 0 when price is unavailable
    assert terms.collateralVal == 0
    assert terms.totalMaxDebt == 0
    
    # Debt terms are still populated (weighted average with debtTermsWeight = 1)
    assert terms.debtTerms.ltv == 50_00
    assert terms.debtTerms.redemptionThreshold == 60_00
    assert terms.debtTerms.liqThreshold == 70_00
    assert terms.debtTerms.liqFee == 10_00
    assert terms.debtTerms.borrowRate == 5_00
    assert terms.debtTerms.daowry == 1_00


#########
# Other #
#########


def test_borrow_interest_calculation(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    createDebtTerms,
):
    # basic setup with high interest rate
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=100_00,  # 100% annual interest
        _daowry=1_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # borrow
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # time_travel forward by 1 year (31536000 seconds)
    boa.env.time_travel(seconds=31536000)

    # get latest user debt and terms
    user_debt, terms, new_interest = credit_engine.getLatestUserDebtAndTerms(bob, True)

    # userDebt should be original borrow amount
    assert user_debt.amount == borrow_amount + new_interest

    # newInterest should be approximately borrow_amount (100% annual interest)
    assert new_interest == borrow_amount


def test_update_debt_for_user(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    createDebtTerms,
    mission_control_gov,
):
    # basic setup with high interest rate
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=100_00,  # 100% annual interest
        _daowry=1_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # borrow
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # time_travel forward by 1 year (31536000 seconds)
    boa.env.time_travel(seconds=31536000)

    # update debt for user
    with boa.reverts("no perms"):
        credit_engine.updateDebtForUser(bob, sender=bob)

    credit_engine.updateDebtForUser(bob, sender=mission_control_gov.address)

    # get user debt directly from ledger
    user_debt = ledger.userDebt(bob)
    assert user_debt.amount == borrow_amount + borrow_amount  # borrow_amount + new_interest (100% annual interest)

    # verify totalDebt is updated
    assert ledger.totalDebt() == borrow_amount + borrow_amount

    # verify unrealizedYield is updated
    assert ledger.unrealizedYield() == borrow_amount


def test_has_good_debt_health(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    createDebtTerms,
):
    # basic setup
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=5_00,
        _daowry=1_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # borrow
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # hasGoodDebtHealth should be True
    assert credit_engine.hasGoodDebtHealth(bob)

    # lower price to trigger bad health
    mock_price_source.setPrice(alpha_token, alpha_price // 2)
    assert not credit_engine.hasGoodDebtHealth(bob)


def test_can_liquidate_user(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    createDebtTerms,
):
    # basic setup
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=70_00,
        _liqFee=10_00,
        _borrowRate=5_00,
        _daowry=1_00,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)

    # borrow
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    teller.borrow(borrow_amount, bob, False, sender=bob)

    # canLiquidateUser should be False
    assert not credit_engine.canLiquidateUser(bob)

    # lower price to trigger liquidation
    mock_price_source.setPrice(alpha_token, alpha_price // 2)
    assert credit_engine.canLiquidateUser(bob)
