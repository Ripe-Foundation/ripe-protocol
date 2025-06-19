# @version 0.4.1
# pragma optimize codesize

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department
from interfaces import Vault
import interfaces.ConfigStructs as cs

from ethereum.ercs import IERC4626
from ethereum.ercs import IERC20

interface Ledger:
    def setUserDebt(_user: address, _userDebt: UserDebt, _newInterest: uint256, _interval: IntervalBorrow): nonpayable
    def getBorrowDataBundle(_user: address) -> BorrowDataBundle: view
    def addVaultToUser(_user: address, _vaultId: uint256): nonpayable
    def userVaults(_user: address, _index: uint256) -> uint256: view
    def getRepayDataBundle(_user: address) -> RepayDataBundle: view
    def numUserVaults(_user: address) -> uint256: view
    def flushUnrealizedYield() -> uint256: nonpayable

interface MissionControl:
    def getRedeemCollateralConfig(_asset: address, _recipient: address) -> RedeemCollateralConfig: view
    def getBorrowConfig(_user: address, _caller: address) -> BorrowConfig: view
    def getDynamicBorrowRateConfig() -> DynamicBorrowRateConfig: view
    def getRepayConfig(_user: address) -> RepayConfig: view
    def getDebtTerms(_asset: address) -> cs.DebtTerms: view
    def getLtvPaybackBuffer() -> uint256: view

interface PriceDesk:
    def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256: view
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool) -> uint256: view

interface Teller:
    def depositFromTrusted(_user: address, _vaultId: uint256, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def isUnderscoreWalletOwner(_user: address, _caller: address, _mc: address = empty(address)) -> bool: view

interface LootBox:
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address, _a: addys.Addys = empty(addys.Addys)): nonpayable
    def updateBorrowPoints(_user: address, _a: addys.Addys = empty(addys.Addys)): nonpayable

interface GreenToken:
    def mint(_to: address, _amount: uint256): nonpayable
    def burn(_amount: uint256) -> bool: nonpayable

interface CurvePrices:
    def getCurrentGreenPoolStatus() -> CurrentGreenPoolStatus: view

interface AddressRegistry:
    def getAddr(_regId: uint256) -> address: view

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

struct UserBorrowTerms:
    collateralVal: uint256
    totalMaxDebt: uint256
    debtTerms: cs.DebtTerms

struct UserDebt:
    amount: uint256
    principal: uint256
    debtTerms: cs.DebtTerms
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
    canAnyoneDeposit: bool

struct CollateralRedemption:
    user: address
    vaultId: uint256
    asset: address
    maxGreenAmount: uint256

struct CurrentGreenPoolStatus:
    weightedRatio: uint256
    dangerTrigger: uint256
    numBlocksInDanger: uint256

struct DynamicBorrowRateConfig:
    minDynamicRateBoost: uint256
    maxDynamicRateBoost: uint256
    increasePerDangerBlock: uint256
    maxBorrowRate: uint256

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

event CollateralRedeemed:
    user: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    amount: uint256
    recipient: indexed(address)
    caller: address
    repayValue: uint256
    hasGoodDebtHealth: bool

ONE_YEAR: constant(uint256) = 60 * 60 * 24 * 365
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
DANGER_BLOCKS_DENOMINATOR: constant(uint256) = 100_0000 # 100.0000%
ONE_PERCENT: constant(uint256) = 1_00 # 1.00%
MAX_DEBT_UPDATES: constant(uint256) = 25
MAX_COLLATERAL_REDEMPTIONS: constant(uint256) = 20
STABILITY_POOL_ID: constant(uint256) = 1
CURVE_PRICES_ID: constant(uint256) = 2


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
    _shouldEnterStabPool: bool,
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
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, True, 0, empty(address), a)

    # get config
    config: BorrowConfig = staticcall MissionControl(a.missionControl).getBorrowConfig(_user, _caller)

    # check perms
    if _user != _caller and not config.canBorrowForUser:
        assert staticcall Teller(a.teller).isUnderscoreWalletOwner(_user, _caller, a.missionControl) # dev: not allowed to borrow for user

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
    daowry: uint256 = 0
    if config.isDaowryEnabled:
        daowry = newBorrowAmount * bt.debtTerms.daowry // HUNDRED_PERCENT

    # dao revenue
    forDao: uint256 = daowry + unrealizedYield
    if forDao != 0:
        assert extcall IERC20(a.greenToken).transfer(a.savingsGreen, forDao, default_return_value=True) # dev: could not transfer

    # borrower gets their green now -- do this AFTER sending green to stakers
    forBorrower: uint256 = newBorrowAmount - daowry
    self._handleGreenForUser(_user, forBorrower, _wantsSavingsGreen, _shouldEnterStabPool, a)

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

    # check num allowed borrowers
    if not _d.isUserBorrower:
        assert _config.numAllowedBorrowers > _d.numBorrowers # dev: max num borrowers reached

    # main var
    newBorrowAmount: uint256 = _greenAmount

    # avail debt based on collateral value / ltv
    availDebtPerLtv: uint256 = 0
    if _maxUserDebt > _userDebt.amount:
        availDebtPerLtv = _maxUserDebt - _userDebt.amount
    assert availDebtPerLtv != 0 # dev: no debt available
    newBorrowAmount = min(newBorrowAmount, availDebtPerLtv)

    # check borrow interval
    availInInterval: uint256 = 0
    isFreshInterval: bool = False
    availInInterval, isFreshInterval = self._getAvailDebtInInterval(_d.userBorrowInterval, _config.maxBorrowPerInterval, _config.numBlocksPerInterval)
    assert availInInterval != 0 # dev: interval borrow limit reached
    newBorrowAmount = min(newBorrowAmount, availInInterval)

    # check per user debt limit
    availPerUser: uint256 = 0
    if _config.perUserDebtLimit > _userDebt.amount:
        availPerUser = _config.perUserDebtLimit - _userDebt.amount
    assert availPerUser != 0 # dev: per user debt limit reached
    newBorrowAmount = min(newBorrowAmount, availPerUser)

    # check global debt limit
    availGlobal: uint256 = 0
    if _config.globalDebtLimit > _d.totalDebt:
        availGlobal = _config.globalDebtLimit - _d.totalDebt
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
    config: BorrowConfig = staticcall MissionControl(a.missionControl).getBorrowConfig(_user, _user)
    if not config.canBorrow:
        return 0

    # check num allowed borrowers
    if not d.isUserBorrower and config.numAllowedBorrowers <= d.numBorrowers:
        return 0

    # main var
    newBorrowAmount: uint256 = max_value(uint256)

    # avail debt based on collateral value / ltv
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, False, 0, empty(address), a)
    availDebtPerLtv: uint256 = 0
    if bt.totalMaxDebt > userDebt.amount:
        availDebtPerLtv = bt.totalMaxDebt - userDebt.amount
    newBorrowAmount = min(newBorrowAmount, availDebtPerLtv)

    # check borrow interval
    availInInterval: uint256 = 0
    na2: bool = False
    availInInterval, na2 = self._getAvailDebtInInterval(d.userBorrowInterval, config.maxBorrowPerInterval, config.numBlocksPerInterval)
    newBorrowAmount = min(newBorrowAmount, availInInterval)

    # check per user debt limit
    availPerUser: uint256 = 0
    if config.perUserDebtLimit > userDebt.amount:
        availPerUser = config.perUserDebtLimit - userDebt.amount
    newBorrowAmount = min(newBorrowAmount, availPerUser)

    # check global debt limit
    availGlobal: uint256 = 0
    if config.globalDebtLimit > d.totalDebt:
        availGlobal = config.globalDebtLimit - d.totalDebt
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
    _shouldRefundSavingsGreen: bool,
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
    repayAmount, refundAmount = self._validateOnRepay(_user, _caller, _greenAmount, userDebt.amount, a.missionControl, a.greenToken, a.teller)
    assert repayAmount != 0 # dev: cannot repay with 0 green

    return self._repayDebt(_user, userDebt, d.numUserVaults, repayAmount, refundAmount, newInterest, True, _shouldRefundSavingsGreen, RepayType.STANDARD, a)


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
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, _numUserVaults, True, 0, empty(address), _a)
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
        assert extcall GreenToken(_a.greenToken).burn(_repayValue) # dev: could not burn green

    # handle refund
    if _refundAmount != 0:
        self._handleGreenForUser(_user, _refundAmount, _wantsSavingsGreen, False, _a)

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
    _missionControl: address,
    _greenToken: address,
    _teller: address,
) -> (uint256, uint256):
    assert _userDebtAmount != 0 # dev: no debt outstanding

    # repay config
    repayConfig: RepayConfig = staticcall MissionControl(_missionControl).getRepayConfig(_user)
    assert repayConfig.canRepay # dev: repay paused

    # others repaying for user
    if _user != _caller and not repayConfig.canAnyoneRepayDebt:
        assert staticcall Teller(_teller).isUnderscoreWalletOwner(_user, _caller, _missionControl) # dev: not allowed to repay for user

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
    _recipient: address,
    _caller: address,
    _shouldTransferBalance: bool,
    _shouldRefundSavingsGreen: bool,
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
        greenSpent: uint256 = self._redeemCollateral(r.user, r.vaultId, r.asset, r.maxGreenAmount, totalGreenRemaining, _recipient, _caller, _shouldTransferBalance, a)
        totalGreenRemaining -= greenSpent
        totalGreenSpent += greenSpent

    assert totalGreenSpent != 0 # dev: no redemptions occurred

    # handle leftover green
    if totalGreenRemaining != 0:
        self._handleGreenForUser(_caller, totalGreenRemaining, _shouldRefundSavingsGreen, False, a)

    return totalGreenSpent


@external
def redeemCollateral(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _greenAmount: uint256,
    _recipient: address,
    _caller: address,
    _shouldTransferBalance: bool,
    _shouldRefundSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    greenAmount: uint256 = min(_greenAmount, staticcall IERC20(a.greenToken).balanceOf(self))
    assert greenAmount != 0 # dev: no green to redeem
    greenSpent: uint256 = self._redeemCollateral(_user, _vaultId, _asset, max_value(uint256), greenAmount, _recipient, _caller, _shouldTransferBalance, a)
    assert greenSpent != 0 # dev: no redemptions occurred

    # handle leftover green
    if greenAmount > greenSpent:
        self._handleGreenForUser(_caller, greenAmount - greenSpent, _shouldRefundSavingsGreen, False, a)

    return greenSpent


@internal
def _redeemCollateral(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _maxGreenForAsset: uint256,
    _totalGreenRemaining: uint256,
    _recipient: address,
    _caller: address,
    _shouldTransferBalance: bool,
    _a: addys.Addys,
) -> uint256:

    # NOTE: failing gracefully here, in case of many redemptions at same time

    # invalid inputs
    if empty(address) in [_recipient, _asset, _user] or 0 in [_maxGreenForAsset, _totalGreenRemaining, _vaultId]:
        return 0

    # vault address
    vaultAddr: address = staticcall AddressRegistry(_a.vaultBook).getAddr(_vaultId)
    if vaultAddr == empty(address):
        return 0

    # user must have balance
    if not staticcall Vault(vaultAddr).doesUserHaveBalance(_user, _asset):
        return 0

    # redemptions not allowed on asset
    config: RedeemCollateralConfig = staticcall MissionControl(_a.missionControl).getRedeemCollateralConfig(_asset, _recipient)
    if not config.canRedeemCollateralGeneral or not config.canRedeemCollateralAsset or not config.isUserAllowed:
        return 0

    # make sure caller can deposit to recipient
    if _recipient != _caller and not config.canAnyoneDeposit:
        assert staticcall Teller(_a.teller).isUnderscoreWalletOwner(_recipient, _caller, _a.missionControl) # dev: not allowed to deposit for user

    # get latest user debt
    d: RepayDataBundle = staticcall Ledger(_a.ledger).getRepayDataBundle(_user)
    userDebt: UserDebt = empty(UserDebt)
    newInterest: uint256 = 0
    userDebt, newInterest = self._getLatestUserDebtWithInterest(d.userDebt)

    # cannot redeem if no debt or in liquidation
    if userDebt.amount == 0 or userDebt.inLiquidation:
        return 0
    
    # get latest debt terms
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, True, 0, empty(address), _a)
    if bt.collateralVal == 0:
        return 0

    # user has not reached redemption threshold
    if not self._canRedeemUserCollateral(userDebt.amount, bt.collateralVal, bt.debtTerms.redemptionThreshold):
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

    # withdraw or transfer balance to redeemer
    amountSent: uint256 = 0
    na: bool = False
    if _shouldTransferBalance:
        amountSent, na = extcall Vault(vaultAddr).transferBalanceWithinVault(_asset, _user, _recipient, maxAssetAmount, _a)
        extcall Ledger(_a.ledger).addVaultToUser(_recipient, _vaultId)
        extcall LootBox(_a.lootbox).updateDepositPoints(_recipient, _vaultId, vaultAddr, _asset, _a)

    else:
        amountSent, na = extcall Vault(vaultAddr).withdrawTokensFromVault(_user, _asset, maxAssetAmount, _recipient, _a)

    # repay debt
    repayValue: uint256 = amountSent * maxRedeemValue // maxAssetAmount
    hasGoodDebtHealth: bool = self._repayDebt(_user, userDebt, d.numUserVaults, min(repayValue, userDebt.amount), 0, newInterest, True, False, RepayType.REDEMPTION, _a)

    log CollateralRedeemed(
        user=_user,
        vaultId=_vaultId,
        asset=_asset,
        amount=amountSent,
        recipient=_recipient,
        caller=_caller,
        repayValue=repayValue,
        hasGoodDebtHealth=hasGoodDebtHealth,
    )
    return min(repayValue, maxRedeemValue)


# utils


@view
@external
def getMaxRedeemValue(_user: address) -> uint256:
    a: addys.Addys = addys._getAddys()

    # get latest user debt and terms
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    na: uint256 = 0
    userDebt, bt, na = self._getLatestUserDebtAndTerms(_user, False, a)
    if userDebt.amount == 0 or userDebt.inLiquidation or bt.collateralVal == 0:
        return 0

    if not self._canRedeemUserCollateral(userDebt.amount, bt.collateralVal, bt.debtTerms.redemptionThreshold):
        return 0
    
    ltvPaybackBuffer: uint256 = staticcall MissionControl(a.missionControl).getLtvPaybackBuffer()
    targetLtv: uint256 = bt.debtTerms.ltv * (HUNDRED_PERCENT - ltvPaybackBuffer) // HUNDRED_PERCENT
    return self._calcAmountToPay(userDebt.amount, bt.collateralVal, targetLtv)


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
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, staticcall Ledger(a.ledger).numUserVaults(_user), True, 0, empty(address), a)
    return bt.collateralVal


@view
@external
def getUserBorrowTerms(
    _user: address,
    _shouldRaise: bool,
    _skipVaultId: uint256 = 0,
    _skipAsset: address = empty(address),
    _a: addys.Addys = empty(addys.Addys),
) -> UserBorrowTerms:
    a: addys.Addys = addys._getAddys(_a)
    return self._getUserBorrowTerms(_user, staticcall Ledger(a.ledger).numUserVaults(_user), _shouldRaise, _skipVaultId, _skipAsset, a)


@view
@internal
def _getUserBorrowTerms(
    _user: address,
    _numUserVaults: uint256,
    _shouldRaise: bool,
    _skipVaultId: uint256,
    _skipAsset: address,
    _a: addys.Addys,
) -> UserBorrowTerms:

    # nothing to do here
    if _numUserVaults == 0:
        return empty(UserBorrowTerms)

    hasSkip: bool = (_skipVaultId != 0 and _skipAsset != empty(address))

    # sum vars
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    ltvSum: uint256 = 0
    redemptionThresholdSum: uint256 = 0
    liqThresholdSum: uint256 = 0
    liqFeeSum: uint256 = 0
    borrowRateSum: uint256 = 0
    daowrySum: uint256 = 0
    totalSum: uint256 = 0

    # iterate thru each user vault
    for i: uint256 in range(1, _numUserVaults, bound=max_value(uint256)):
        vaultId: uint256 = staticcall Ledger(_a.ledger).userVaults(_user, i)
        vaultAddr: address = staticcall AddressRegistry(_a.vaultBook).getAddr(vaultId)
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
            debtTerms: cs.DebtTerms = staticcall MissionControl(_a.missionControl).getDebtTerms(asset)

            # skip if no ltv (staked green, staked ripe, etc)
            if debtTerms.ltv == 0:
                continue

            # collateral value, max debt
            collateralVal: uint256 = staticcall PriceDesk(_a.priceDesk).getUsdValue(asset, amount, _shouldRaise)
            maxDebt: uint256 = collateralVal * debtTerms.ltv // HUNDRED_PERCENT

            # need to return some debt terms, even if not getting any price
            debtTermsWeight: uint256 = maxDebt
            if debtTermsWeight == 0:
                debtTermsWeight = 1

            # debt terms sums -- weight is based on max debt (ltv)
            ltvSum += debtTermsWeight * debtTerms.ltv
            redemptionThresholdSum += debtTermsWeight * debtTerms.redemptionThreshold
            liqThresholdSum += debtTermsWeight * debtTerms.liqThreshold
            liqFeeSum += debtTermsWeight * debtTerms.liqFee
            borrowRateSum += debtTermsWeight * debtTerms.borrowRate
            daowrySum += debtTermsWeight * debtTerms.daowry
            totalSum += debtTermsWeight

            # totals
            if not (hasSkip and asset == _skipAsset and vaultId == _skipVaultId):
                bt.collateralVal += collateralVal
                bt.totalMaxDebt += maxDebt

    # finalize debt terms (weighted)
    if totalSum != 0:
        bt.debtTerms.ltv = ltvSum // totalSum
        bt.debtTerms.redemptionThreshold = redemptionThresholdSum // totalSum
        bt.debtTerms.liqThreshold = liqThresholdSum // totalSum
        bt.debtTerms.liqFee = liqFeeSum // totalSum
        bt.debtTerms.borrowRate = borrowRateSum // totalSum
        bt.debtTerms.daowry = daowrySum // totalSum

    # overwrite ltv if collateral value is available
    if bt.collateralVal != 0:
        bt.debtTerms.ltv = bt.totalMaxDebt * HUNDRED_PERCENT // bt.collateralVal

    # ensure liq threshold and liq fee can work together
    if bt.debtTerms.liqThreshold != 0:
        liqSum: uint256 = bt.debtTerms.liqThreshold + (bt.debtTerms.liqThreshold * bt.debtTerms.liqFee // HUNDRED_PERCENT)
        if liqSum > HUNDRED_PERCENT:
            adjustedLiqFee: uint256 = (HUNDRED_PERCENT - bt.debtTerms.liqThreshold) * HUNDRED_PERCENT // bt.debtTerms.liqThreshold
            bt.debtTerms.liqFee = adjustedLiqFee
    else:
        bt.debtTerms.liqFee = 0

    # dynamic borrow rate
    bt.debtTerms.borrowRate = self._getDynamicBorrowRate(bt.debtTerms.borrowRate, _a.missionControl, _a.priceDesk)
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
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, _shouldRaise, 0, empty(address), _a)

    return userDebt, bt, newInterest


# dynamic interest rate adjustments


@view
@external
def getDynamicBorrowRate(_baseRate: uint256) -> uint256:
    return self._getDynamicBorrowRate(_baseRate, addys._getMissionControlAddr(), addys._getPriceDeskAddr())


@view
@internal
def _getDynamicBorrowRate(_baseRate: uint256, _missionControl: address, _priceDesk: address) -> uint256:
    curvePrices: address = staticcall AddressRegistry(_priceDesk).getAddr(CURVE_PRICES_ID)
    if curvePrices == empty(address):
        return _baseRate

    status: CurrentGreenPoolStatus = staticcall CurvePrices(curvePrices).getCurrentGreenPoolStatus()
    if status.weightedRatio == 0 or status.weightedRatio < status.dangerTrigger:
        return _baseRate

    config: DynamicBorrowRateConfig = staticcall MissionControl(_missionControl).getDynamicBorrowRateConfig()

    # dynamic rate boost (depending on pool health)
    rateBoost: uint256 = 0
    if config.maxDynamicRateBoost != 0:
        dynamicRatio: uint256 = (status.weightedRatio - status.dangerTrigger) * HUNDRED_PERCENT // (HUNDRED_PERCENT - status.dangerTrigger)
        rateMultiplier: uint256 = self._calcDynamicRateBoost(dynamicRatio, config.minDynamicRateBoost, config.maxDynamicRateBoost)
        rateBoost = _baseRate * rateMultiplier // HUNDRED_PERCENT

    # danger boost (longer pool health imbalanced, higher rate keeps getting)
    dangerBoost: uint256 = 0
    if status.numBlocksInDanger != 0 and config.increasePerDangerBlock != 0:
        dangerBoost = (config.increasePerDangerBlock * status.numBlocksInDanger) * HUNDRED_PERCENT // DANGER_BLOCKS_DENOMINATOR

    return min(_baseRate + rateBoost + dangerBoost, config.maxBorrowRate)


@pure
@internal
def _calcDynamicRateBoost(_ratio: uint256, _minBoost: uint256, _maxBoost: uint256) -> uint256:
    if _ratio == 0 or _minBoost == _maxBoost:
        return _minBoost
    valRange: uint256 = _maxBoost - _minBoost
    adjustment: uint256 =  _ratio * valRange // HUNDRED_PERCENT
    return _minBoost + adjustment


###############
# Update Debt #
###############


@external
def updateDebtForUser(_user: address, _a: addys.Addys = empty(addys.Addys)) -> bool:
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    newInterest: uint256 = 0
    userDebt, bt, newInterest = self._getLatestUserDebtAndTerms(_user, True, a)
    if userDebt.amount == 0:
        return True

    # debt health
    hasGoodDebtHealth: bool = self._hasGoodDebtHealth(userDebt.amount, bt.collateralVal, bt.debtTerms.ltv)
    if hasGoodDebtHealth:
        userDebt.inLiquidation = False

    userDebt.debtTerms = bt.debtTerms
    extcall Ledger(a.ledger).setUserDebt(_user, userDebt, newInterest, empty(IntervalBorrow))

    # update borrow points
    extcall LootBox(a.lootbox).updateBorrowPoints(_user, a)

    return hasGoodDebtHealth


###############
# Debt Health #
###############


@view
@external
def hasGoodDebtHealth(_user: address, _a: addys.Addys = empty(addys.Addys)) -> bool:
    return self._checkDebtHealth(_user, 1, _a)


@view
@external
def canLiquidateUser(_user: address, _a: addys.Addys = empty(addys.Addys)) -> bool:
    return self._checkDebtHealth(_user, 2, _a)


@view
@external
def canRedeemUserCollateral(_user: address, _a: addys.Addys = empty(addys.Addys)) -> bool:
    return self._checkDebtHealth(_user, 3, _a)


@view
@internal
def _checkDebtHealth(_user: address, _debtType: uint256, _a: addys.Addys) -> bool:
    a: addys.Addys = addys._getAddys(_a)

    # get latest user debt and terms
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    na: uint256 = 0
    userDebt, bt, na = self._getLatestUserDebtAndTerms(_user, False, a)
    if userDebt.amount == 0:
        return _debtType == 1 # nothing to check

    # in liquidation, can't do anything
    if userDebt.inLiquidation:
        return False

    # check debt health
    if _debtType == 1:
        return self._hasGoodDebtHealth(userDebt.amount, bt.collateralVal, bt.debtTerms.ltv)
    elif _debtType == 2:
        return self._canLiquidateUser(userDebt.amount, bt.collateralVal, bt.debtTerms.liqThreshold)
    elif _debtType == 3:
        return self._canRedeemUserCollateral(userDebt.amount, bt.collateralVal, bt.debtTerms.redemptionThreshold)
    else:
        return False


@view
@internal
def _hasGoodDebtHealth(_userDebtAmount: uint256, _collateralVal: uint256, _ltv: uint256) -> bool:
    maxUserDebt: uint256 = _collateralVal * _ltv // HUNDRED_PERCENT
    return _userDebtAmount <= maxUserDebt


@view
@internal
def _canLiquidateUser(_userDebtAmount: uint256, _collateralVal: uint256, _liqThreshold: uint256) -> bool:
    if _liqThreshold == 0:
        return False
    
    # check if collateral value is below (or equal) to liquidation threshold
    collateralLiqThreshold: uint256 = _userDebtAmount * HUNDRED_PERCENT // _liqThreshold
    return _collateralVal <= collateralLiqThreshold


@view
@internal
def _canRedeemUserCollateral(_userDebtAmount: uint256, _collateralVal: uint256, _redemptionThreshold: uint256) -> bool:
    if _redemptionThreshold == 0:
        return False
    
    # check if collateral value is below (or equal) to redemption threshold
    redemptionThreshold: uint256 = _userDebtAmount * HUNDRED_PERCENT // _redemptionThreshold
    return _collateralVal <= redemptionThreshold


# thresholds


@view
@external
def getLiquidationThreshold(_user: address) -> uint256:
    return self._getThreshold(_user, 2)


@view
@external
def getRedemptionThreshold(_user: address) -> uint256:
    return self._getThreshold(_user, 3)


@view
@internal
def _getThreshold(_user: address, _debtType: uint256) -> uint256:
    a: addys.Addys = addys._getAddys()

    # get latest user debt and terms
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    na: uint256 = 0
    userDebt, bt, na = self._getLatestUserDebtAndTerms(_user, False, a)
    if userDebt.amount == 0:
        return 0

    if _debtType == 2:
        if bt.debtTerms.liqThreshold == 0:
            return 0
        return userDebt.amount * HUNDRED_PERCENT // bt.debtTerms.liqThreshold
    elif _debtType == 3:
        if bt.debtTerms.redemptionThreshold == 0:
            return 0
        return userDebt.amount * HUNDRED_PERCENT // bt.debtTerms.redemptionThreshold
    else:
        return 0


##################
# Green Handling #
##################


@internal
def _handleGreenForUser(
    _recipient: address,
    _greenAmount: uint256,
    _wantsSavingsGreen: bool,
    _shouldEnterStabPool: bool,
    _a: addys.Addys,
):
    amount: uint256 = min(_greenAmount, staticcall IERC20(_a.greenToken).balanceOf(self))
    if amount == 0:
        return

    if _wantsSavingsGreen and amount > 10 ** 9: # small dust will fail

        sgreenRecipient: address = _recipient
        if _shouldEnterStabPool:
            sgreenRecipient = self

        # put GREEN into sGREEN
        assert extcall IERC20(_a.greenToken).approve(_a.savingsGreen, amount, default_return_value=True) # dev: green approval failed
        sGreenAmount: uint256 = extcall IERC4626(_a.savingsGreen).deposit(amount, sgreenRecipient)
        assert extcall IERC20(_a.greenToken).approve(_a.savingsGreen, 0, default_return_value=True) # dev: green approval failed

        # put sGREEN into stability pool
        if _shouldEnterStabPool:
            assert extcall IERC20(_a.savingsGreen).approve(_a.teller, sGreenAmount, default_return_value=True) # dev: sgreen approval failed
            extcall Teller(_a.teller).depositFromTrusted(_recipient, STABILITY_POOL_ID, _a.savingsGreen, sGreenAmount, 0, _a)
            assert extcall IERC20(_a.savingsGreen).approve(_a.teller, 0, default_return_value=True) # dev: sgreen approval failed

    else:
        assert extcall IERC20(_a.greenToken).transfer(_recipient, amount, default_return_value=True) # dev: green transfer failed


#############
# Utilities #
#############


# max withdrawable


@view
@external
def getMaxWithdrawableForAsset(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _vaultAddr: address = empty(address),
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    a: addys.Addys = addys._getAddys(_a)

    vaultAddr: address = _vaultAddr
    if vaultAddr == empty(address):
        vaultAddr = staticcall AddressRegistry(a.vaultBook).getAddr(_vaultId)

    # get latest user debt
    d: RepayDataBundle = staticcall Ledger(a.ledger).getRepayDataBundle(_user)
    userDebt: UserDebt = empty(UserDebt)
    na: uint256 = 0
    userDebt, na = self._getLatestUserDebtWithInterest(d.userDebt)

    # no debt, can do max withdraw
    if userDebt.amount == 0:
        return max_value(uint256)

    # cannot withdraw if in liquidation
    if userDebt.inLiquidation:
        return 0

    # get current asset value for user
    userBalance: uint256 = staticcall Vault(vaultAddr).getTotalAmountForUser(_user, _asset)
    userUsdValue: uint256 = staticcall PriceDesk(a.priceDesk).getUsdValue(_asset, userBalance, False)
    if userUsdValue == 0:
        return 0 # cannot determine value

    # get the asset's debt terms
    assetDebtTerms: cs.DebtTerms = staticcall MissionControl(a.missionControl).getDebtTerms(_asset)
    if assetDebtTerms.ltv == 0:
        return max_value(uint256) # asset doesn't contribute to borrowing power

    # get borrow terms excluding the asset to withdraw
    btExcluding: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, True, _vaultId, _asset, a)

    # calculate minimum asset value that must remain
    minAssetValueToRemain: uint256 = 0
    
    if btExcluding.collateralVal == 0:

        # entire debt must be supported by this asset
        minAssetValueToRemain = userDebt.amount * (HUNDRED_PERCENT + ONE_PERCENT) // assetDebtTerms.ltv

    # multi-asset case: check if remaining collateral is sufficient
    else:
        minCollateralNeeded: uint256 = userDebt.amount * (HUNDRED_PERCENT + ONE_PERCENT) // btExcluding.debtTerms.ltv
        if btExcluding.collateralVal >= minCollateralNeeded:
            return max_value(uint256) # remaining collateral is sufficient
        
        # calculate additional value needed from this asset
        additionalCollateralNeeded: uint256 = minCollateralNeeded - btExcluding.collateralVal
        minAssetValueToRemain = additionalCollateralNeeded * HUNDRED_PERCENT // assetDebtTerms.ltv

    # cannot withdraw if user has less than the minimum required
    if userUsdValue <= minAssetValueToRemain:
        return 0
    
    # convert to asset amount
    maxWithdrawableValue: uint256 = userUsdValue - minAssetValueToRemain
    return userBalance * maxWithdrawableValue // userUsdValue


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

    # multiply all numerators first, then divide by combined denominators
    newInterest: uint256 = (userDebt.amount * userDebt.debtTerms.borrowRate * timeElapsed) // (HUNDRED_PERCENT * ONE_YEAR)
    userDebt.amount += newInterest

    userDebt.lastTimestamp = block.timestamp
    return userDebt, newInterest


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
