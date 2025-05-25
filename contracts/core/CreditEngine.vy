# @version 0.4.1

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department
from interfaces import Vault
from ethereum.ercs import IERC4626
from ethereum.ercs import IERC20

interface Ledger:
    def setUserDebt(_user: address, _userDebt: UserDebt, _newInterest: uint256, _interval: IntervalBorrow): nonpayable
    def getBorrowDataBundle(_user: address) -> BorrowDataBundle: view
    def userVaults(_user: address, _index: uint256) -> uint256: view
    def getRepayDataBundle(_user: address) -> RepayDataBundle: view
    def numUserVaults(_user: address) -> uint256: view
    def flushUnrealizedYield() -> uint256: nonpayable

interface ControlRoom:
    def getRedeemCollateralConfig(_asset: address, _redeemer: address) -> RedeemCollateralConfig: view
    def getBorrowConfig(_user: address, _caller: address) -> BorrowConfig: view
    def getRepayConfig(_user: address) -> RepayConfig: view
    def getDebtTerms(_asset: address) -> DebtTerms: view

interface PriceDesk:
    def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256: view
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool) -> uint256: view

interface GreenToken:
    def mint(_to: address, _amount: uint256): nonpayable
    def burn(_amount: uint256): nonpayable

interface LootBox:
    def updateBorrowPoints(_user: address, _a: addys.Addys = empty(addys.Addys)): nonpayable

interface VaultBook:
    def getAddr(_vaultId: uint256) -> address: view

flag RepayType:
    STANDARD
    LIQUIDATION
    AUCTION
    REDEMPTION

struct BorrowDataBundle:
    userDebt: UserDebt
    userBorrowInterval: IntervalBorrow
    isUserBorrower: bool
    numUserVaults: uint256
    totalDebt: uint256
    numBorrowers: uint256

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

struct IntervalBorrow:
    start: uint256
    amount: uint256

struct RepayDataBundle:
    userDebt: UserDebt
    numUserVaults: uint256

struct BorrowConfig:
    canBorrow: bool
    canBorrowForUser: bool
    numAllowedBorrowers: uint256
    maxBorrowPerInterval: uint256
    numBlocksPerInterval: uint256
    perUserDebtLimit: uint256
    globalDebtLimit: uint256
    minDebtAmount: uint256
    isDaowryEnabled: bool

struct RepayConfig:
    canRepay: bool
    canAnyoneRepayDebt: bool

struct RedeemCollateralConfig:
    canRedeemCollateralGeneral: bool
    canRedeemCollateralAsset: bool
    isUserAllowed: bool
    ltvPaybackBuffer: uint256

struct CollateralRedemption:
    user: address
    vaultId: uint256
    asset: address
    maxGreenAmount: uint256

event NewBorrow:
    user: indexed(address)
    newLoan: uint256
    daowry: uint256
    didReceiveSavingsGreen: bool
    outstandingUserDebt: uint256
    userCollateralVal: uint256
    maxUserDebt: uint256
    globalYieldRealized: uint256

event RepayDebt:
    user: indexed(address)
    repayValue: uint256
    repayType: RepayType
    refundAmount: uint256
    refundWasSavingsGreen: bool
    outstandingUserDebt: uint256
    userCollateralVal: uint256
    maxUserDebt: uint256
    hasGoodDebtHealth: bool

ONE_YEAR: constant(uint256) = 60 * 60 * 24 * 365
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
ONE_PERCENT: constant(uint256) = 1_00 # 1.00%
MAX_DEBT_UPDATES: constant(uint256) = 25
MAX_COLLATERAL_REDEMPTIONS: constant(uint256) = 20


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, True, False) # can mint green only


##########
# Borrow #
##########


@external
def borrowForUser(
    _user: address,
    _greenAmount: uint256,
    _wantsSavingsGreen: bool,
    _caller: address,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only teller allowed
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    assert _user != empty(address) # dev: cannot borrow for 0x0

    # get borrow data
    d: BorrowDataBundle = staticcall Ledger(a.ledger).getBorrowDataBundle(_user)

    # get latest user debt
    userDebt: UserDebt = empty(UserDebt)
    newInterest: uint256 = 0
    userDebt, newInterest = self._getLatestUserDebtWithInterest(d.userDebt)

    # get borrow data (debt terms for user)
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, True, a)

    # get config
    config: BorrowConfig = staticcall ControlRoom(a.controlRoom).getBorrowConfig(_user, _caller)

    # validation
    newBorrowAmount: uint256 = 0
    isFreshInterval: bool = False
    newBorrowAmount, isFreshInterval = self._validateOnBorrow(_greenAmount, userDebt, bt.totalMaxDebt, d, config)
    assert newBorrowAmount != 0 # dev: cannot borrow

    # update borrow interval
    userBorrowInterval: IntervalBorrow = d.userBorrowInterval
    if isFreshInterval:
        userBorrowInterval.start = block.number
        userBorrowInterval.amount = newBorrowAmount
    else:
        userBorrowInterval.amount += newBorrowAmount

    # update user debt
    userDebt.amount += newBorrowAmount
    userDebt.principal += newBorrowAmount
    userDebt.debtTerms = bt.debtTerms

    # check debt health
    hasGoodDebtHealth: bool = self._hasGoodDebtHealth(userDebt.amount, bt.collateralVal, bt.debtTerms.ltv)
    assert hasGoodDebtHealth # dev: bad debt health
    userDebt.inLiquidation = False

    # save debt
    extcall Ledger(a.ledger).setUserDebt(_user, userDebt, newInterest, userBorrowInterval)

    # update borrow points
    extcall LootBox(a.lootbox).updateBorrowPoints(_user, a)

    # mint green - piggy back on borrow to flush unrealized yield
    unrealizedYield: uint256 = extcall Ledger(a.ledger).flushUnrealizedYield()
    totalGreenMint: uint256 = newBorrowAmount + unrealizedYield
    extcall GreenToken(a.greenToken).mint(self, totalGreenMint)

    # origination fee
    daowry: uint256 = self._getDaowryAmount(newBorrowAmount, bt.debtTerms.daowry, config.isDaowryEnabled)

    # dao revenue
    forDao: uint256 = daowry + unrealizedYield
    if forDao != 0:
        assert extcall IERC20(a.greenToken).transfer(a.savingsGreen, forDao, default_return_value=True) # dev: could not transfer

    # borrower gets their green now -- do this AFTER sending green to stakers
    forBorrower: uint256 = newBorrowAmount - daowry
    self._handleGreenForUser(_user, forBorrower, _wantsSavingsGreen, a.greenToken, a.savingsGreen)

    log NewBorrow(user=_user, newLoan=forBorrower, daowry=daowry, didReceiveSavingsGreen=_wantsSavingsGreen, outstandingUserDebt=userDebt.amount, userCollateralVal=bt.collateralVal, maxUserDebt=bt.totalMaxDebt, globalYieldRealized=unrealizedYield)
    return forBorrower


# borrow validation


@view
@internal
def _validateOnBorrow(
    _greenAmount: uint256,
    _userDebt: UserDebt,
    _maxUserDebt: uint256,
    _d: BorrowDataBundle,
    _config: BorrowConfig,
) -> (uint256, bool):
    assert not _userDebt.inLiquidation # dev: cannot borrow in liquidation
    assert _greenAmount != 0 # dev: cannot borrow 0 amount

    # get borrow config
    assert _config.canBorrow # dev: borrow not enabled
    assert _config.canBorrowForUser # dev: cannot borrow for user

    # check num allowed borrowers
    if not _d.isUserBorrower:
        numAvailBorrowers: uint256 = self._getAvailNumBorrowers(_d.numBorrowers, _config.numAllowedBorrowers)
        assert numAvailBorrowers != 0 # dev: max num borrowers reached

    # main var
    newBorrowAmount: uint256 = _greenAmount

    # avail debt based on collateral value / ltv
    availDebtPerLtv: uint256 = self._getAvailBasedOnLtv(_userDebt.amount, _maxUserDebt)
    assert availDebtPerLtv != 0 # dev: no debt available
    newBorrowAmount = min(newBorrowAmount, availDebtPerLtv)

    # check borrow interval
    availInInterval: uint256 = 0
    isFreshInterval: bool = False
    availInInterval, isFreshInterval = self._getAvailDebtInInterval(_d.userBorrowInterval, _config.maxBorrowPerInterval, _config.numBlocksPerInterval)
    assert availInInterval != 0 # dev: interval borrow limit reached
    newBorrowAmount = min(newBorrowAmount, availInInterval)

    # check per user debt limit
    availPerUser: uint256 = self._getAvailPerUserDebt(_userDebt.amount, _config.perUserDebtLimit)
    assert availPerUser != 0 # dev: per user debt limit reached
    newBorrowAmount = min(newBorrowAmount, availPerUser)

    # check global debt limit
    availGlobal: uint256 = self._getAvailGlobalDebt(_d.totalDebt, _config.globalDebtLimit)
    assert availGlobal != 0 # dev: global debt limit reached
    newBorrowAmount = min(newBorrowAmount, availGlobal)

    # must reach minimum debt threshold
    assert _userDebt.amount + newBorrowAmount >= _config.minDebtAmount # dev: debt too small

    return newBorrowAmount, isFreshInterval


# max available borrow (mostly for front-ends, no exceptions raised)


@view
@external
def getMaxBorrowAmount(_user: address) -> uint256:
    a: addys.Addys = addys._getAddys()

    # get latest user debt
    d: BorrowDataBundle = staticcall Ledger(a.ledger).getBorrowDataBundle(_user)
    userDebt: UserDebt = empty(UserDebt)
    na1: uint256 = 0
    userDebt, na1 = self._getLatestUserDebtWithInterest(d.userDebt)

    # cannot borrow in liquidation
    if userDebt.inLiquidation:
        return 0

    # get borrow config
    config: BorrowConfig = staticcall ControlRoom(a.controlRoom).getBorrowConfig(_user, _user)
    if not config.canBorrow:
        return 0

    # check num allowed borrowers
    if not d.isUserBorrower:
        numAvailBorrowers: uint256 = self._getAvailNumBorrowers(d.numBorrowers, config.numAllowedBorrowers)
        if numAvailBorrowers == 0:
            return 0

    # main var
    newBorrowAmount: uint256 = max_value(uint256)

    # avail debt based on collateral value / ltv
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, False, a)
    availDebtPerLtv: uint256 = self._getAvailBasedOnLtv(userDebt.amount, bt.totalMaxDebt)
    if availDebtPerLtv == 0:
        return 0
    newBorrowAmount = min(newBorrowAmount, availDebtPerLtv)

    # check borrow interval
    availInInterval: uint256 = 0
    na2: bool = False
    availInInterval, na2 = self._getAvailDebtInInterval(d.userBorrowInterval, config.maxBorrowPerInterval, config.numBlocksPerInterval)
    if availInInterval == 0:
        return 0
    newBorrowAmount = min(newBorrowAmount, availInInterval)

    # check per user debt limit
    availPerUser: uint256 = self._getAvailPerUserDebt(userDebt.amount, config.perUserDebtLimit)
    if availPerUser == 0:
        return 0
    newBorrowAmount = min(newBorrowAmount, availPerUser)

    # check global debt limit
    availGlobal: uint256 = self._getAvailGlobalDebt(d.totalDebt, config.globalDebtLimit)
    if availGlobal == 0:
        return 0
    newBorrowAmount = min(newBorrowAmount, availGlobal)

    # must reach minimum debt threshold
    if userDebt.amount + newBorrowAmount < config.minDebtAmount:
        return 0

    return newBorrowAmount


#########
# Repay #
#########


@external
def repayForUser(
    _user: address,
    _greenAmount: uint256,
    _wantsSavingsGreen: bool,
    _caller: address,
    _a: addys.Addys = empty(addys.Addys),
) -> bool:
    assert msg.sender == addys._getTellerAddr() # dev: only teller allowed
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    # get latest user debt
    d: RepayDataBundle = staticcall Ledger(a.ledger).getRepayDataBundle(_user)
    userDebt: UserDebt = empty(UserDebt)
    newInterest: uint256 = 0
    userDebt, newInterest = self._getLatestUserDebtWithInterest(d.userDebt)

    # validation
    repayAmount: uint256 = 0
    refundAmount: uint256 = 0
    repayAmount, refundAmount = self._validateOnRepay(_user, _caller, _greenAmount, userDebt.amount, a.controlRoom, a.greenToken)
    assert repayAmount != 0 # dev: cannot repay with 0 green

    return self._repayDebt(_user, userDebt, d.numUserVaults, repayAmount, refundAmount, newInterest, True, _wantsSavingsGreen, RepayType.STANDARD, a)


# repay during liquidation


@external
def repayDuringLiquidation(
    _liqUser: address,
    _userDebt: UserDebt,
    _repayValue: uint256,
    _newInterest: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> bool:
    assert msg.sender == addys._getAuctionHouseAddr() # dev: only auction house allowed
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)
    numVaults: uint256 = staticcall Ledger(a.ledger).numUserVaults(_liqUser)
    return self._repayDebt(_liqUser, _userDebt, numVaults, _repayValue, 0, _newInterest, False, False, RepayType.LIQUIDATION, a)


# repay during auction purchase


@external
def repayDuringAuctionPurchase(_liqUser: address, _repayValue: uint256, _a: addys.Addys = empty(addys.Addys)) -> bool:
    assert msg.sender == addys._getAuctionHouseAddr() # dev: only auction house allowed
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    # get latest user debt
    d: RepayDataBundle = staticcall Ledger(a.ledger).getRepayDataBundle(_liqUser)
    userDebt: UserDebt = empty(UserDebt)
    newInterest: uint256 = 0
    userDebt, newInterest = self._getLatestUserDebtWithInterest(d.userDebt)

    # finalize amounts
    repayAmount: uint256 = 0
    refundAmount: uint256 = 0
    repayAmount, refundAmount = self._getRepayAmountAndRefundAmount(userDebt.amount, _repayValue, a.greenToken)
    assert repayAmount != 0 # dev: cannot repay with 0 green

    return self._repayDebt(_liqUser, userDebt, d.numUserVaults, repayAmount, refundAmount, newInterest, True, True, RepayType.AUCTION, a)


# shared repay functionality


@internal
def _repayDebt(
    _user: address,
    _userDebt: UserDebt,
    _numUserVaults: uint256,
    _repayValue: uint256,
    _refundAmount: uint256,
    _newInterest: uint256,
    _shouldBurnGreen: bool,
    _wantsSavingsGreen: bool,
    _repayType: RepayType,
    _a: addys.Addys,
) -> bool:
    userDebt: UserDebt = self._reduceDebtAmount(_userDebt, _repayValue)

    # get latest debt terms
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, _numUserVaults, True, _a)
    userDebt.debtTerms = bt.debtTerms

    # check debt health
    hasGoodDebtHealth: bool = self._hasGoodDebtHealth(userDebt.amount, bt.collateralVal, bt.debtTerms.ltv)
    if hasGoodDebtHealth:
        userDebt.inLiquidation = False
    
    # update user debt, borrow points
    extcall Ledger(_a.ledger).setUserDebt(_user, userDebt, _newInterest, empty(IntervalBorrow))
    extcall LootBox(_a.lootbox).updateBorrowPoints(_user, _a)

    # burn green repayment
    if _shouldBurnGreen:
        extcall GreenToken(_a.greenToken).burn(_repayValue)

    # handle refund
    if _refundAmount != 0:
        self._handleGreenForUser(_user, _refundAmount, _wantsSavingsGreen, _a.greenToken, _a.savingsGreen)

    log RepayDebt(user=_user, repayValue=_repayValue, repayType=_repayType, refundAmount=_refundAmount, refundWasSavingsGreen=_wantsSavingsGreen, outstandingUserDebt=userDebt.amount, userCollateralVal=bt.collateralVal, maxUserDebt=bt.totalMaxDebt, hasGoodDebtHealth=hasGoodDebtHealth)
    return hasGoodDebtHealth


# repay validation


@view
@internal
def _validateOnRepay(
    _user: address,
    _caller: address,
    _greenAmount: uint256,
    _userDebtAmount: uint256,
    _controlRoom: address,
    _greenToken: address,
) -> (uint256, uint256):
    assert _userDebtAmount != 0 # dev: no debt outstanding

    # repay config
    repayConfig: RepayConfig = staticcall ControlRoom(_controlRoom).getRepayConfig(_user)
    assert repayConfig.canRepay # dev: repay paused
    if _user != _caller:
        assert repayConfig.canAnyoneRepayDebt # dev: cannot repay for user

    return self._getRepayAmountAndRefundAmount(_userDebtAmount, _greenAmount, _greenToken)


# repay amount and refund amount


@view
@internal
def _getRepayAmountAndRefundAmount(_userDebtAmount: uint256, _greenAmount: uint256, _greenToken: address) -> (uint256, uint256):
    availAmount: uint256 = min(_greenAmount, staticcall IERC20(_greenToken).balanceOf(self))

    repayAmount: uint256 = min(availAmount, _userDebtAmount)
    refundAmount: uint256 = 0
    if repayAmount > availAmount:
        refundAmount = repayAmount - availAmount

    return repayAmount, refundAmount


# reduce debt amount


@view
@internal
def _reduceDebtAmount(_userDebt: UserDebt, _repayAmount: uint256) -> UserDebt:
    userDebt: UserDebt = _userDebt
    nonPrincipalDebt: uint256 = userDebt.amount - userDebt.principal

    userDebt.amount -= _repayAmount
    if _repayAmount > nonPrincipalDebt:
        principalToReduce: uint256 = _repayAmount - nonPrincipalDebt
        userDebt.principal -= min(principalToReduce, userDebt.principal)

    return userDebt


#####################
# Redeem Collateral #
#####################


@external
def redeemCollateralFromMany(
    _redemptions: DynArray[CollateralRedemption, MAX_COLLATERAL_REDEMPTIONS],
    _greenAmount: uint256,
    _redeemer: address,
    _wantsSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    totalGreenSpent: uint256 = 0
    totalGreenRemaining: uint256 = min(_greenAmount, staticcall IERC20(a.greenToken).balanceOf(self))
    assert totalGreenRemaining != 0 # dev: no green to redeem

    for r: CollateralRedemption in _redemptions:
        if totalGreenRemaining == 0:
            break
        greenSpent: uint256 = self._redeemCollateral(r.user, r.vaultId, r.asset, r.maxGreenAmount, totalGreenRemaining, _redeemer, a)
        totalGreenRemaining -= greenSpent
        totalGreenSpent += greenSpent

    # handle leftover green
    if totalGreenRemaining != 0:
        self._handleGreenForUser(_redeemer, totalGreenRemaining, _wantsSavingsGreen, a.greenToken, a.savingsGreen)

    return totalGreenSpent


@external
def redeemCollateral(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _greenAmount: uint256,
    _redeemer: address,
    _wantsSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    greenAmount: uint256 = min(_greenAmount, staticcall IERC20(a.greenToken).balanceOf(self))
    assert greenAmount != 0 # dev: no green to redeem
    greenSpent: uint256 = self._redeemCollateral(_user, _vaultId, _asset, max_value(uint256), greenAmount, _redeemer, a)

    # handle leftover green
    if greenAmount > greenSpent:
        self._handleGreenForUser(_redeemer, greenAmount - greenSpent, _wantsSavingsGreen, a.greenToken, a.savingsGreen)

    return greenSpent


@internal
def _redeemCollateral(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _maxGreenForAsset: uint256,
    _totalGreenRemaining: uint256,
    _redeemer: address,
    _a: addys.Addys,
) -> uint256:

    # NOTE: failing gracefully here, in case of many redemptions at same time

    # invalid inputs
    if empty(address) in [_redeemer, _asset, _user] or 0 in [_maxGreenForAsset, _totalGreenRemaining, _vaultId]:
        return 0

    # redemptions not allowed on asset
    config: RedeemCollateralConfig = staticcall ControlRoom(_a.controlRoom).getRedeemCollateralConfig(_asset, _redeemer)
    if not config.canRedeemCollateralGeneral or not config.canRedeemCollateralAsset or not config.isUserAllowed:
        return 0

    # get latest user debt
    d: RepayDataBundle = staticcall Ledger(_a.ledger).getRepayDataBundle(_user)
    userDebt: UserDebt = empty(UserDebt)
    newInterest: uint256 = 0
    userDebt, newInterest = self._getLatestUserDebtWithInterest(d.userDebt)

    # cannot redeem if no debt or in liquidation
    if userDebt.amount == 0 or userDebt.inLiquidation:
        return 0
    
    # get latest debt terms
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, True, _a)
    if bt.collateralVal == 0:
        return 0

    # user has not reached redemption threshold
    currentRatio: uint256 = userDebt.amount * HUNDRED_PERCENT // bt.collateralVal
    if currentRatio < bt.debtTerms.redemptionThreshold:
        return 0

    # estimated debt to pay back to achieve safe LTV
    # won't be exact because depends on which collateral is redeemed (LTV changes)
    targetLtv: uint256 = bt.debtTerms.ltv * (HUNDRED_PERCENT - config.ltvPaybackBuffer) // HUNDRED_PERCENT
    maxCollateralValue: uint256 = self._calcAmountToPay(userDebt.amount, bt.collateralVal, targetLtv)

    # treating green as $1
    maxGreenAvailable: uint256 = min(_totalGreenRemaining, staticcall IERC20(_a.greenToken).balanceOf(self))
    maxGreenForAsset: uint256 = min(_maxGreenForAsset, maxGreenAvailable)
    maxRedeemValue: uint256 = min(maxCollateralValue, maxGreenForAsset)
    if maxRedeemValue == 0:
        return 0

    # max asset amount to take from user
    maxAssetAmount: uint256 = staticcall PriceDesk(_a.priceDesk).getAssetAmount(_asset, maxRedeemValue, True)
    if maxAssetAmount == 0:
        return 0

    # vault address
    vaultAddr: address = staticcall VaultBook(_a.vaultBook).getAddr(_vaultId)
    if vaultAddr == empty(address):
        return 0

    # user must have this asset in vault
    if not staticcall Vault(vaultAddr).isUserInVaultAsset(_user, _asset):
        return 0

    # withdraw from vault, transfer to redeemer
    amountSent: uint256 = 0
    na: bool = False
    amountSent, na = extcall Vault(vaultAddr).withdrawTokensFromVault(_user, _asset, maxAssetAmount, _redeemer, _a)

    # repay debt
    repayAmount: uint256 = min(maxRedeemValue, amountSent * maxRedeemValue // maxAssetAmount)
    repayAmount = min(repayAmount, userDebt.amount)
    hasGoodDebtHealth: bool = self._repayDebt(_user, userDebt, d.numUserVaults, repayAmount, 0, newInterest, True, False, RepayType.REDEMPTION, _a)

    # TODO: add event

    return repayAmount


@view
@internal
def _calcAmountToPay(_debtAmount: uint256, _collateralValue: uint256, _targetLtv: uint256) -> uint256:
    # goal here is to only reduce the debt necessary to get LTV back to safe position
    # it will never be perfectly precise because depending on what assets are taken, the LTV might slightly change
    collValueAdjusted: uint256 =_collateralValue * _targetLtv // HUNDRED_PERCENT

    toPay: uint256 = (_debtAmount - collValueAdjusted) * HUNDRED_PERCENT // (HUNDRED_PERCENT - _targetLtv)
    return min(toPay, _debtAmount)


################
# Borrow Terms #
################


@view
@external
def getCollateralValue(_user: address) -> uint256:
    a: addys.Addys = addys._getAddys()
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, staticcall Ledger(a.ledger).numUserVaults(_user), True, a)
    return bt.collateralVal


@view
@external
def getUserBorrowTerms(
    _user: address,
    _shouldRaise: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> UserBorrowTerms:
    a: addys.Addys = addys._getAddys(_a)
    return self._getUserBorrowTerms(_user, staticcall Ledger(a.ledger).numUserVaults(_user), _shouldRaise, a)


@view
@internal
def _getUserBorrowTerms(
    _user: address,
    _numUserVaults: uint256,
    _shouldRaise: bool,
    _a: addys.Addys,
) -> UserBorrowTerms:

    # nothing to do here
    if _numUserVaults == 0:
        return empty(UserBorrowTerms)

    # sum vars
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    redemptionThresholdSum: uint256 = 0
    liqThresholdSum: uint256 = 0
    liqFeeSum: uint256 = 0
    borrowRateSum: uint256 = 0
    daowrySum: uint256 = 0
    totalSum: uint256 = 0

    # iterate thru each user vault
    for i: uint256 in range(1, _numUserVaults, bound=max_value(uint256)):
        vaultId: uint256 = staticcall Ledger(_a.ledger).userVaults(_user, i)
        vaultAddr: address = staticcall VaultBook(_a.vaultBook).getAddr(vaultId)
        if vaultAddr == empty(address):
            continue

        # iterate thru each user asset
        numUserAssets: uint256 = staticcall Vault(vaultAddr).numUserAssets(_user)
        for y: uint256 in range(1, numUserAssets, bound=max_value(uint256)):

            # get user asset and amount
            asset: address = empty(address)
            amount: uint256 = 0
            asset, amount = staticcall Vault(vaultAddr).getUserAssetAndAmountAtIndex(_user, y)
            if asset == empty(address) or amount == 0:
                continue

            # debt terms
            debtTerms: DebtTerms = staticcall ControlRoom(_a.controlRoom).getDebtTerms(asset)

            # skip if no ltv (staked green, staked ripe, etc)
            if debtTerms.ltv == 0:
                continue

            # collateral value, max debt
            collateralVal: uint256 = staticcall PriceDesk(_a.priceDesk).getUsdValue(asset, amount, _shouldRaise)
            maxDebt: uint256 = collateralVal * debtTerms.ltv // HUNDRED_PERCENT

            # debt terms sums -- weight is based on max debt (ltv)
            redemptionThresholdSum += maxDebt * debtTerms.redemptionThreshold
            liqThresholdSum += maxDebt * debtTerms.liqThreshold
            liqFeeSum += maxDebt * debtTerms.liqFee
            borrowRateSum += maxDebt * debtTerms.borrowRate
            daowrySum += maxDebt * debtTerms.daowry
            totalSum += maxDebt

            # totals
            bt.collateralVal += collateralVal
            bt.totalMaxDebt += maxDebt

    # finalize debt terms (weighted)
    if totalSum != 0:
        bt.debtTerms.redemptionThreshold = redemptionThresholdSum // totalSum
        bt.debtTerms.liqThreshold = liqThresholdSum // totalSum
        bt.debtTerms.liqFee = liqFeeSum // totalSum
        bt.debtTerms.borrowRate = borrowRateSum // totalSum
        bt.debtTerms.daowry = daowrySum // totalSum

    # finalize overall ltv
    if bt.collateralVal != 0:
        bt.debtTerms.ltv = bt.totalMaxDebt * HUNDRED_PERCENT // bt.collateralVal

    # ensure liq threshold and liq fee can work together
    liqSum: uint256 = bt.debtTerms.liqThreshold + (bt.debtTerms.liqThreshold * bt.debtTerms.liqFee // HUNDRED_PERCENT)
    if liqSum > HUNDRED_PERCENT:
        adjustedLiqFee: uint256 = (HUNDRED_PERCENT - bt.debtTerms.liqThreshold) * HUNDRED_PERCENT // bt.debtTerms.liqThreshold
        bt.debtTerms.liqFee = adjustedLiqFee

    return bt


# latest user debt and terms


@view
@external
def getLatestUserDebtAndTerms(
    _user: address,
    _shouldRaise: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> (UserDebt, UserBorrowTerms, uint256):
    return self._getLatestUserDebtAndTerms(_user, _shouldRaise, addys._getAddys(_a))


@view
@internal
def _getLatestUserDebtAndTerms(
    _user: address,
    _shouldRaise: bool,
    _a: addys.Addys,
) -> (UserDebt, UserBorrowTerms, uint256):

    # get data (repay data has the only stuff we need)
    d: RepayDataBundle = staticcall Ledger(_a.ledger).getRepayDataBundle(_user)

    # accrue interest
    userDebt: UserDebt = empty(UserDebt)
    newInterest: uint256 = 0
    userDebt, newInterest = self._getLatestUserDebtWithInterest(d.userDebt)

    # debt terms for user
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, _shouldRaise, _a)

    return userDebt, bt, newInterest


###############
# Update Debt #
###############


@external
def updateDebtForUser(_user: address, _a: addys.Addys = empty(addys.Addys)) -> bool:
    assert addys._isValidRipeHqAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    return self._updateDebtForUser(_user, addys._getAddys(_a))


@external
def updateDebtForManyUsers(_users: DynArray[address, MAX_DEBT_UPDATES], _a: addys.Addys = empty(addys.Addys)) -> bool:
    assert addys._isValidRipeHqAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)
    for u: address in _users:
        self._updateDebtForUser(u, a)
    return True


@internal
def _updateDebtForUser(_user: address, _a: addys.Addys) -> bool:
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    newInterest: uint256 = 0
    userDebt, bt, newInterest = self._getLatestUserDebtAndTerms(_user, True, _a)
    if userDebt.amount == 0:
        return True

    # debt health
    hasGoodDebtHealth: bool = self._hasGoodDebtHealth(userDebt.amount, bt.collateralVal, bt.debtTerms.ltv)
    if hasGoodDebtHealth:
        userDebt.inLiquidation = False

    userDebt.debtTerms = bt.debtTerms
    extcall Ledger(_a.ledger).setUserDebt(_user, userDebt, newInterest, empty(IntervalBorrow))

    # update borrow points
    extcall LootBox(_a.lootbox).updateBorrowPoints(_user, _a)

    return hasGoodDebtHealth


###############
# Debt Health #
###############


@view
@external
def hasGoodDebtHealth(_user: address, _a: addys.Addys = empty(addys.Addys)) -> bool:
    return self._checkDebtHealth(_user, True, _a)


@view
@external
def canLiquidateUser(_user: address, _a: addys.Addys = empty(addys.Addys)) -> bool:
    return self._checkDebtHealth(_user, False, _a)


@view
@internal
def _checkDebtHealth(_user: address, _shouldCheckLtv: bool, _a: addys.Addys) -> bool:
    a: addys.Addys = addys._getAddys(_a)

    # get latest user debt and terms
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    na: uint256 = 0
    userDebt, bt, na = self._getLatestUserDebtAndTerms(_user, False, a)

    if userDebt.amount == 0:
        return _shouldCheckLtv # nothing to check, use that var to return correct value

    # check debt health
    if _shouldCheckLtv:
        return self._hasGoodDebtHealth(userDebt.amount, bt.collateralVal, bt.debtTerms.ltv)
    else:
        return self._canLiquidateUser(userDebt.amount, bt.collateralVal, bt.debtTerms.liqThreshold)


@view
@internal
def _hasGoodDebtHealth(_userDebtAmount: uint256, _collateralVal: uint256, _ltv: uint256) -> bool:
    maxUserDebt: uint256 = _collateralVal * _ltv // HUNDRED_PERCENT
    return _userDebtAmount <= maxUserDebt


@view
@internal
def _canLiquidateUser(_userDebtAmount: uint256, _collateralVal: uint256, _liqThreshold: uint256) -> bool:
    # check if collateral value is below (or equal) to liquidation threshold
    collateralLiqThreshold: uint256 = _userDebtAmount * HUNDRED_PERCENT // _liqThreshold
    return _collateralVal <= collateralLiqThreshold


##################
# Green Handling #
##################


@internal
def _handleGreenForUser(
    _recipient: address,
    _greenAmount: uint256,
    _wantsSavingsGreen: bool,
    _greenToken: address,
    _savingsGreen: address,
):
    amount: uint256 = min(_greenAmount, staticcall IERC20(_greenToken).balanceOf(self))
    if amount == 0:
        return

    if _wantsSavingsGreen:
        assert extcall IERC20(_greenToken).approve(_savingsGreen, amount, default_return_value=True) # dev: green approval failed
        extcall IERC4626(_savingsGreen).deposit(amount, _recipient)
        assert extcall IERC20(_greenToken).approve(_savingsGreen, 0, default_return_value=True) # dev: green approval failed

    else:
        assert extcall IERC20(_greenToken).transfer(_recipient, amount, default_return_value=True) # dev: green transfer failed


#############
# Utilities #
#############


# max withdrawable


@view
@external
def getMaxWithdrawableForAsset(_user: address, _asset: address, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    a: addys.Addys = addys._getAddys(_a)

    # get latest user debt and terms
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    na: uint256 = 0
    userDebt, bt, na = self._getLatestUserDebtAndTerms(_user, False, a)

    if userDebt.amount == 0:
        return max_value(uint256)

    # calculate max transferable usd value
    usdValueMustRemain: uint256 = max_value(uint256)
    if bt.debtTerms.ltv != 0:
        usdValueMustRemain = userDebt.amount * (HUNDRED_PERCENT + ONE_PERCENT) // bt.debtTerms.ltv # extra 1% buffer
    maxTransferUsdValue: uint256 = bt.collateralVal - min(usdValueMustRemain, bt.collateralVal)

    # cannot withdraw anything
    if maxTransferUsdValue == 0:
        return 0

    # based stricly on total ltvs, not taking into consideration how much user actually has deposited
    return staticcall PriceDesk(a.priceDesk).getAssetAmount(_asset, maxTransferUsdValue, False)


# accrue interest


@view
@internal
def _getLatestUserDebtWithInterest(_userDebt: UserDebt) -> (UserDebt, uint256):
    userDebt: UserDebt = _userDebt

    # nothing to do here
    if userDebt.amount == 0 or userDebt.debtTerms.borrowRate == 0 or block.timestamp <= userDebt.lastTimestamp:
        userDebt.lastTimestamp = block.timestamp
        return userDebt, 0

    # accrue latest interest
    timeElapsed: uint256 = block.timestamp - userDebt.lastTimestamp
    newInterest: uint256 = userDebt.amount * userDebt.debtTerms.borrowRate * timeElapsed // HUNDRED_PERCENT // ONE_YEAR
    userDebt.amount += newInterest

    userDebt.lastTimestamp = block.timestamp
    return userDebt, newInterest


# daowry (origination fee)


@view
@internal
def _getDaowryAmount(
    _borrowAmount: uint256,
    _daowryFee: uint256,
    _isDaowryEnabled: bool,
) -> uint256:
    daowry: uint256 = 0
    if _daowryFee != 0 and _isDaowryEnabled:
        daowry = _borrowAmount * _daowryFee // HUNDRED_PERCENT
    return daowry


# ltv


@view
@internal
def _getAvailBasedOnLtv(_currentUserDebt: uint256, _maxUserDebt: uint256) -> uint256:
    availDebt: uint256 = 0
    if _maxUserDebt > _currentUserDebt:
        availDebt = _maxUserDebt - _currentUserDebt
    return availDebt


# num borrowers


@view
@internal
def _getAvailNumBorrowers(_numBorrowers: uint256, _numAllowedBorrowers: uint256) -> uint256:
    numAllowed: uint256 = 0
    if _numAllowedBorrowers > _numBorrowers:
        numAllowed = _numAllowedBorrowers - _numBorrowers
    return numAllowed


# borrow interval


@view 
@internal 
def _getAvailDebtInInterval(
    _userInterval: IntervalBorrow,
    _maxBorrowPerInterval: uint256,
    _numBlocksPerInterval: uint256,
) -> (uint256, bool):
    availToBorrow: uint256 = _maxBorrowPerInterval
    isFreshInterval: bool = True
    if _userInterval.start != 0 and _userInterval.start + _numBlocksPerInterval > block.number:
        availToBorrow = _maxBorrowPerInterval - min(_userInterval.amount, _maxBorrowPerInterval)
        isFreshInterval = False
    return availToBorrow, isFreshInterval


# per user debt limit


@view 
@internal 
def _getAvailPerUserDebt(_currentUserDebt: uint256, _perUserDebtLimit: uint256) -> uint256:
    if _perUserDebtLimit == max_value(uint256):
        return max_value(uint256)
    availableDebt: uint256 = 0
    if _perUserDebtLimit > _currentUserDebt:
        availableDebt = _perUserDebtLimit - _currentUserDebt
    return availableDebt


# global debt limit


@view 
@internal 
def _getAvailGlobalDebt(_totalDebt: uint256, _globalDebtLimit: uint256) -> uint256:
    availableDebt: uint256 = 0
    if _globalDebtLimit > _totalDebt:
        availableDebt = _globalDebtLimit - _totalDebt
    return availableDebt