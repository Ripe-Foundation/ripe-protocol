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
    control_room,
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
    teller.pause(True, sender=control_room.address)
    assert teller.isPaused()

    # Attempt borrow should fail
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    with boa.reverts("contract paused"):
        teller.borrow(borrow_amount, bob, False, sender=bob)

    # unpause the credit engine
    teller.pause(False, sender=control_room.address)
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
    endaoment,
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
    assert green_token.balanceOf(endaoment) == 0

    # borrow
    borrow_amount = 50 * EIGHTEEN_DECIMALS
    amount = teller.borrow(borrow_amount, bob, False, sender=bob)
    assert amount == borrow_amount

    # verify unrealized yield was minted and sent to endaoment
    assert ledger.unrealizedYield() == 0
    assert green_token.balanceOf(endaoment) == unrealized_yield

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
    endaoment,
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
    assert green_token.balanceOf(endaoment) == 0
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
    assert green_token.balanceOf(endaoment) == expected_daowry
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