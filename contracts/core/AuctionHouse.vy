# @version 0.4.1

initializes: addys
exports: addys.__interface__
import contracts.modules.Addys as addys

interface CreditEngine:
    def repayDebtDuringLiquidation(_liqUser: address, _userDebt: UserDebt, _amount: uint256, _newInterest: uint256, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def getLatestUserDebtAndTerms(_user: address, _shouldRaise: bool, _a: addys.Addys = empty(addys.Addys)) -> (UserDebt, UserBorrowTerms, uint256): view

struct DebtTerms:
    ltv: uint256
    redemptionThreshold: uint256
    liqThreshold: uint256
    liqFee: uint256
    borrowRate: uint256
    daowry: uint256

struct UserBorrowTerms:
    collateralVal: uint256
    totalMaxDebt: uint256
    debtTerms: DebtTerms

struct UserDebt:
    amount: uint256
    principal: uint256
    debtTerms: DebtTerms
    lastTimestamp: uint256
    inLiquidation: bool

struct LiqConfig:
    keeperFeeRatio: uint256
    minKeeperFee: uint256
    ltvPaybackBuffer: uint256
    defaultAuctionConfig: AuctionConfig
    priorityAssets: DynArray[address, MAX_PRIORITY_ASSETS]

struct AuctionConfig:
    startDiscount: uint256
    minEntitled: uint256
    maxDiscount: uint256
    minBidIncrement: uint256
    maxBidIncrement: uint256
    delay: uint256
    duration: uint256
    extension: uint256

event LiquidateUser:
    user: address
    totalLiqFees: uint256
    targetRepayAmount: uint256
    repayAmount: uint256
    didRestoreDebtHealth: bool
    collateralValueOut: uint256
    auctionValueStarted: uint256
    keeperFee: uint256

# config
isActivated: public(bool)

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_PRIORITY_ASSETS: constant(uint256) = 20


@deploy
def __init__(_hq: address):
    addys.__init__(_hq)
    self.isActivated = True


@internal
def _liquidateUser(
    _liqUser: address,
    _config: LiqConfig,
    _a: addys.Addys,
) -> uint256:

    # get latest user debt and terms
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    newInterest: uint256 = 0
    userDebt, bt, newInterest = staticcall CreditEngine(_a.creditEngine).getLatestUserDebtAndTerms(_liqUser, True, _a)

    # no debt
    if userDebt.amount == 0:
        return 0

    # already in liquidation
    if userDebt.inLiquidation:
        return 0

    # not reached liquidation threshold
    collateralLiqThreshold: uint256 = userDebt.amount * HUNDRED_PERCENT // bt.debtTerms.liqThreshold
    if bt.collateralVal > collateralLiqThreshold:
        return 0

    # set liquidation mode
    userDebt.inLiquidation = True

    # liquidation fees
    totalLiqFees: uint256 = userDebt.amount * bt.debtTerms.liqFee // HUNDRED_PERCENT
    liqFeeRatio: uint256 = bt.debtTerms.liqFee

    # keeper fee (for liquidator)
    keeperFee: uint256 = max(_config.minKeeperFee, userDebt.amount * _config.keeperFeeRatio // HUNDRED_PERCENT)
    if keeperFee != 0:
        totalLiqFees += keeperFee
        liqFeeRatio = totalLiqFees * HUNDRED_PERCENT // userDebt.amount

    # update user debt
    userDebt.amount += totalLiqFees

    # how much to achieve safe LTV -- won't be exact because depends on which collateral is liquidated (LTV changes)
    targetLtv: uint256 = bt.debtTerms.ltv * (HUNDRED_PERCENT - _config.ltvPaybackBuffer) // HUNDRED_PERCENT
    targetRepayAmount: uint256 = self._calcAmountToPay(userDebt.amount, bt.collateralVal, targetLtv)

    # swap collateral to pay debt (liquidation fees basically mean selling at a discount)
    repayValueIn: uint256 = 0
    collateralValueOut: uint256 = 0
    repayValueIn, collateralValueOut = self._swapCollateralToPayDebt(_liqUser, targetRepayAmount, liqFeeRatio, _config.priorityAssets)

    # repay debt
    didRestoreDebtHealth: bool = extcall CreditEngine(_a.creditEngine).repayDebtDuringLiquidation(_liqUser, userDebt, repayValueIn, newInterest, _a)

    # start auctions (if necessary)
    auctionValueStarted: uint256 = 0
    if not didRestoreDebtHealth:
        auctionValueStarted = self._initiateAuctions(_liqUser, _config.defaultAuctionConfig, _a)

    log LiquidateUser(user=_liqUser, totalLiqFees=totalLiqFees, targetRepayAmount=targetRepayAmount, repayAmount=repayValueIn, didRestoreDebtHealth=didRestoreDebtHealth, collateralValueOut=collateralValueOut, auctionValueStarted=auctionValueStarted, keeperFee=keeperFee)
    return keeperFee


@internal
def _swapCollateralToPayDebt(
    _liqUser: address,
    _targetRepayAmount: uint256,
    _liqFeeRatio: uint256,
    _priorityAssets: DynArray[address, MAX_PRIORITY_ASSETS],
) -> (uint256, uint256):
    # TODO: implement
    return 0, 0


@internal
def _initiateAuctions(_liqUser: address, _config: AuctionConfig, _a: addys.Addys) -> uint256:
    # TODO: implement
    return 0


#############
# Utilities #
#############


@view
@external
def calcAmountToPay(_debtAmount: uint256, _collateralValue: uint256, _targetLtv: uint256) -> uint256:
    return self._calcAmountToPay(_debtAmount, _collateralValue, _targetLtv)


@view
@internal
def _calcAmountToPay(_debtAmount: uint256, _collateralValue: uint256, _targetLtv: uint256) -> uint256:
    # goal here is to only reduce the debt necessary to get LTV back to safe position
    # it will never be perfectly precise because depending on what assets are taken, the LTV might slightly change
    collValueAdjusted: uint256 =_collateralValue * _targetLtv // HUNDRED_PERCENT

    toPay: uint256 = (_debtAmount - collValueAdjusted) * HUNDRED_PERCENT // (HUNDRED_PERCENT - _targetLtv)
    return min(toPay, _debtAmount)