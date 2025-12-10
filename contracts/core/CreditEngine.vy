#           _             _           _          _             _        _                _            _             _               _          _             _      
#         /\ \           /\ \        /\ \       /\ \          /\ \     /\ \             /\ \         /\ \     _    /\ \            /\ \       /\ \     _    /\ \    
#        /  \ \         /  \ \      /  \ \     /  \ \____     \ \ \    \_\ \           /  \ \       /  \ \   /\_\ /  \ \           \ \ \     /  \ \   /\_\ /  \ \   
#       / /\ \ \       / /\ \ \    / /\ \ \   / /\ \_____\    /\ \_\   /\__ \         / /\ \ \     / /\ \ \_/ / // /\ \_\          /\ \_\   / /\ \ \_/ / // /\ \ \  
#      / / /\ \ \     / / /\ \_\  / / /\ \_\ / / /\/___  /   / /\/_/  / /_ \ \       / / /\ \_\   / / /\ \___/ // / /\/_/         / /\/_/  / / /\ \___/ // / /\ \_\ 
#     / / /  \ \_\   / / /_/ / / / /_/_ \/_// / /   / / /   / / /    / / /\ \ \     / /_/_ \/_/  / / /  \/____// / / ______      / / /    / / /  \/____// /_/_ \/_/ 
#    / / /    \/_/  / / /__\/ / / /____/\  / / /   / / /   / / /    / / /  \/_/    / /____/\    / / /    / / // / / /\_____\    / / /    / / /    / / // /____/\    
#   / / /          / / /_____/ / /\____\/ / / /   / / /   / / /    / / /          / /\____\/   / / /    / / // / /  \/____ /   / / /    / / /    / / // /\____\/    
#  / / /________  / / /\ \ \  / / /______ \ \ \__/ / /___/ / /__  / / /          / / /______  / / /    / / // / /_____/ / /___/ / /__  / / /    / / // / /______    
# / / /_________\/ / /  \ \ \/ / /_______\ \ \___\/ //\__\/_/___\/_/ /          / / /_______\/ / /    / / // / /______\/ //\__\/_/___\/ / /    / / // / /_______\   
# \/____________/\/_/    \_\/\/__________/  \/_____/ \/_________/\_\/           \/__________/\/_/     \/_/ \/___________/ \/_________/\/_/     \/_/ \/__________/   
#
#     ╔══════════════════════════════════════════════════════════════╗
#     ║  ** Credit Engine **                                         ║
#     ║  Handles all credit-related actions (borrow, repay, redeem)  ║
#     ╚══════════════════════════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3
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
    def getBorrowConfig(_user: address, _caller: address) -> BorrowConfig: view
    def getDynamicBorrowRateConfig() -> DynamicBorrowRateConfig: view
    def getRepayConfig(_user: address) -> RepayConfig: view
    def getDebtTerms(_asset: address) -> cs.DebtTerms: view
    def underscoreRegistry() -> address: view

interface Teller:
    def depositFromTrusted(_user: address, _vaultId: uint256, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def isUnderscoreWalletOwner(_user: address, _caller: address, _mc: address = empty(address)) -> bool: view

interface LootBox:
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address, _a: addys.Addys = empty(addys.Addys)): nonpayable
    def updateBorrowPoints(_user: address, _a: addys.Addys = empty(addys.Addys)): nonpayable

interface GreenToken:
    def mint(_to: address, _amount: uint256): nonpayable
    def burn(_amount: uint256) -> bool: nonpayable

interface PriceDesk:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool) -> uint256: view

interface CurvePrices:
    def getCurrentGreenPoolStatus() -> CurrentGreenPoolStatus: view

interface VaultRegistry:
    def isEarnVault(_vaultAddr: address) -> bool: view

interface AddressRegistry:
    def getAddr(_regId: uint256) -> address: view

interface RipeHq:
    def governance() -> address: view

flag RepayType:
    STANDARD
    LIQUIDATION
    AUCTION
    REDEMPTION
    DELEVERAGE

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
    lowestLtv: uint256
    highestLtv: uint256

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

event UnderscoreVaultDiscountSet:
    discount: uint256

event BuybackRatioSet:
    ratio: uint256

# borrow rate discount
undyVaulDiscount: public(uint256)

# buyback ratio for revenue split
buybackRatio: public(uint256)

ONE_YEAR: constant(uint256) = 60 * 60 * 24 * 365
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
DANGER_BLOCKS_DENOMINATOR: constant(uint256) = 100_0000 # 100.0000%
ONE_PERCENT: constant(uint256) = 1_00 # 1.00%
STABILITY_POOL_ID: constant(uint256) = 1
CURVE_PRICES_ID: constant(uint256) = 2
UNDERSCORE_VAULT_REGISTRY_ID: constant(uint256) = 10


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, True, False) # can mint green only

    # default discount for underscore vaults
    self.undyVaulDiscount = 50_00 # 50.00%

    # default buyback ratio (disabled)
    self.buybackRatio = 0


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

    # check if underscore vault (used for daowry, borrow rate discount)
    isUndyVault: bool = self._isUnderscoreVault(_user, a.missionControl)

    # get borrow data (debt terms for user)
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, True, 0, empty(address), isUndyVault, a)

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

    # check debt health (use bt.totalMaxDebt directly to avoid rounding discrepancy)
    assert userDebt.amount <= bt.totalMaxDebt # dev: bad debt health
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
    if config.isDaowryEnabled and not isUndyVault:
        daowry = newBorrowAmount * bt.debtTerms.daowry // HUNDRED_PERCENT

    # dao revenue
    forDao: uint256 = daowry + unrealizedYield
    if forDao != 0:

        # split revenue between governance (for buyback) and savings green
        forBuyback: uint256 = 0
        buybackRatio: uint256 = self.buybackRatio
        if buybackRatio != 0:
            forBuyback = forDao * buybackRatio // HUNDRED_PERCENT

        # transfer to governance for buyback
        if forBuyback != 0:
            govWallet: address = staticcall RipeHq(a.hq).governance()
            assert extcall IERC20(a.greenToken).transfer(govWallet, forBuyback, default_return_value=True) # dev: could not transfer to gov

        # transfer to savings green
        forSavingsGreen: uint256 = forDao - forBuyback
        if forSavingsGreen != 0:
            assert extcall IERC20(a.greenToken).transfer(a.savingsGreen, forSavingsGreen, default_return_value=True) # dev: could not transfer

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
    isUndyVault: bool = self._isUnderscoreVault(_user, a.missionControl)

    # avail debt based on collateral value / ltv
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, False, 0, empty(address), isUndyVault, a)
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


# generic repay (liquidation, deleverage, redemption)


@external
def repayFromDept(
    _user: address,
    _userDebt: UserDebt,
    _repayValue: uint256,
    _newInterest: uint256,
    _numUserVaults: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> bool:
    deleverage: address = addys._getDeleverageAddr()
    auctionHouse: address = addys._getAuctionHouseAddr()
    creditRedeem: address = addys._getCreditRedeemAddr()
    assert msg.sender in [deleverage, auctionHouse, creditRedeem] # dev: not allowed
    assert not deptBasics.isPaused # dev: contract paused

    repayType: RepayType = empty(RepayType)
    if msg.sender == deleverage:
        repayType = RepayType.DELEVERAGE
    elif msg.sender == auctionHouse:
        repayType = RepayType.LIQUIDATION
    elif msg.sender == creditRedeem:
        repayType = RepayType.REDEMPTION

    a: addys.Addys = addys._getAddys(_a)
    numUserVaults: uint256 = _numUserVaults
    if numUserVaults == 0:
        numUserVaults = staticcall Ledger(a.ledger).numUserVaults(_user)
    return self._repayDebt(_user, _userDebt, numUserVaults, _repayValue, 0, _newInterest, False, False, repayType, a)


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
    isUndyVault: bool = self._isUnderscoreVault(_user, _a.missionControl)

    # get latest debt terms
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, _numUserVaults, True, 0, empty(address), isUndyVault, _a)
    userDebt.debtTerms = bt.debtTerms

    # check debt health (use bt.totalMaxDebt directly to avoid rounding discrepancy)
    hasGoodDebtHealth: bool = userDebt.amount <= bt.totalMaxDebt
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
    if availAmount > _userDebtAmount:
        refundAmount = availAmount - _userDebtAmount

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


################
# Borrow Terms #
################


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
    isUndyVault: bool = self._isUnderscoreVault(_user, a.missionControl)
    return self._getUserBorrowTerms(_user, staticcall Ledger(a.ledger).numUserVaults(_user), _shouldRaise, _skipVaultId, _skipAsset, isUndyVault, a)


@view
@external
def getUserBorrowTermsWithNumVaults(
    _user: address,
    _numUserVaults: uint256,
    _shouldRaise: bool,
    _skipVaultId: uint256 = 0,
    _skipAsset: address = empty(address),
    _a: addys.Addys = empty(addys.Addys),
) -> UserBorrowTerms:
    a: addys.Addys = addys._getAddys(_a)
    isUndyVault: bool = self._isUnderscoreVault(_user, a.missionControl)
    return self._getUserBorrowTerms(_user, _numUserVaults, _shouldRaise, _skipVaultId, _skipAsset, isUndyVault, a)


@view
@external
def getBorrowRate(_user: address) -> uint256:
    a: addys.Addys = addys._getAddys()
    isUndyVault: bool = self._isUnderscoreVault(_user, a.missionControl)
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, staticcall Ledger(a.ledger).numUserVaults(_user), False, 0, empty(address), isUndyVault, a)
    return bt.debtTerms.borrowRate


@view
@internal
def _getUserBorrowTerms(
    _user: address,
    _numUserVaults: uint256,
    _shouldRaise: bool,
    _skipVaultId: uint256,
    _skipAsset: address,
    _isUndyVault: bool,
    _a: addys.Addys,
) -> UserBorrowTerms:

    # nothing to do here
    if _numUserVaults == 0:
        return empty(UserBorrowTerms)

    hasSkip: bool = (_skipVaultId != 0 and _skipAsset != empty(address))

    # sum vars
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    bt.lowestLtv = max_value(uint256)
    bt.highestLtv = 0
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

            # lowest ltv
            if debtTerms.ltv != 0 and debtTerms.ltv < bt.lowestLtv:
                bt.lowestLtv = debtTerms.ltv

            # highest ltv
            if debtTerms.ltv > bt.highestLtv:
                bt.highestLtv = debtTerms.ltv

            # totals
            if not (hasSkip and asset == _skipAsset and vaultId == _skipVaultId):
                bt.collateralVal += collateralVal
                bt.totalMaxDebt += maxDebt

    # edge case -- but safer to use
    if bt.lowestLtv == max_value(uint256):
        bt.lowestLtv = 0

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

    # apply discount for underscore vaults
    if _isUndyVault:
        undyVaulDiscount: uint256 = self.undyVaulDiscount
        if undyVaulDiscount != 0:
            bt.debtTerms.borrowRate = bt.debtTerms.borrowRate * (HUNDRED_PERCENT - undyVaulDiscount) // HUNDRED_PERCENT

    # dynamic borrow rate (for normal users)
    else:
        bt.debtTerms.borrowRate = self._getDynamicBorrowRate(bt.debtTerms.borrowRate, _a.missionControl, _a.priceDesk)

    return bt


# collateral value


@view
@external
def getUserCollateralValueAndDebtAmount(_user: address) -> (uint256, uint256):
    a: addys.Addys = addys._getAddys()
    d: RepayDataBundle = staticcall Ledger(a.ledger).getRepayDataBundle(_user)
    userDebt: UserDebt = empty(UserDebt)
    na: uint256 = 0
    userDebt, na = self._getLatestUserDebtWithInterest(d.userDebt)
    isUndyVault: bool = self._isUnderscoreVault(_user, a.missionControl)
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, False, 0, empty(address), isUndyVault, a)
    return bt.collateralVal, userDebt.amount


@view
@external
def getCollateralValue(_user: address) -> uint256:
    a: addys.Addys = addys._getAddys()
    isUndyVault: bool = self._isUnderscoreVault(_user, a.missionControl)
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, staticcall Ledger(a.ledger).numUserVaults(_user), True, 0, empty(address), isUndyVault, a)
    return bt.collateralVal


####################
# Latest User Debt #
####################


@view
@external
def getUserDebtAmount(_user: address) -> uint256:
    d: RepayDataBundle = staticcall Ledger(addys._getLedgerAddr()).getRepayDataBundle(_user)
    userDebt: UserDebt = empty(UserDebt)
    na: uint256 = 0
    userDebt, na = self._getLatestUserDebtWithInterest(d.userDebt)
    return userDebt.amount


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
    isUndyVault: bool = self._isUnderscoreVault(_user, _a.missionControl)
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, _shouldRaise, 0, empty(address), isUndyVault, _a)

    return userDebt, bt, newInterest


# accrue interest


@view
@external
def getLatestUserDebtWithInterest(_userDebt: UserDebt) -> (UserDebt, uint256):
    return self._getLatestUserDebtWithInterest(_userDebt)


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

    # check debt health (use bt.totalMaxDebt directly to avoid rounding discrepancy)
    if _debtType == 1:
        return userDebt.amount <= bt.totalMaxDebt
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


################
# Dynamic Rate #
################


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


##############
# Underscore #
##############


# set undy vault discount


@external
def setUnderscoreVaultDiscount(_discount: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: only switchboard allowed
    assert not deptBasics.isPaused # dev: contract paused
    assert _discount <= HUNDRED_PERCENT # dev: invalid discount
    self.undyVaulDiscount = _discount
    log UnderscoreVaultDiscountSet(discount=_discount)


# underscore vault


@view
@internal
def _isUnderscoreVault(_addr: address, _mc: address) -> bool:
    underscore: address = staticcall MissionControl(_mc).underscoreRegistry()
    if underscore == empty(address):
        return False
    vaultRegistry: address = staticcall AddressRegistry(underscore).getAddr(UNDERSCORE_VAULT_REGISTRY_ID)
    if vaultRegistry == empty(address):
        return False
    return staticcall VaultRegistry(vaultRegistry).isEarnVault(_addr)


#############
# Utilities #
#############


# update debt


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

    # debt health (use bt.totalMaxDebt directly to avoid rounding discrepancy)
    hasGoodDebtHealth: bool = userDebt.amount <= bt.totalMaxDebt
    if hasGoodDebtHealth:
        userDebt.inLiquidation = False

    userDebt.debtTerms = bt.debtTerms

    extcall Ledger(a.ledger).setUserDebt(_user, userDebt, newInterest, empty(IntervalBorrow))

    # update borrow points
    extcall LootBox(a.lootbox).updateBorrowPoints(_user, a)

    return hasGoodDebtHealth


# credit redeem wrappers


@external
def transferOrWithdrawViaRedemption(
    _shouldTransferBalance: bool,
    _asset: address,
    _user: address,
    _recipient: address,
    _amount: uint256,
    _vaultId: uint256,
    _vaultAddr: address,
    _a: addys.Addys,
) -> uint256:
    assert msg.sender == addys._getCreditRedeemAddr() # dev: only credit redeem allowed

    amountSent: uint256 = 0
    na: bool = False
    if _shouldTransferBalance:
        amountSent, na = extcall Vault(_vaultAddr).transferBalanceWithinVault(_asset, _user, _recipient, _amount, _a)
        extcall Ledger(_a.ledger).addVaultToUser(_recipient, _vaultId)
        extcall LootBox(_a.lootbox).updateDepositPoints(_recipient, _vaultId, _vaultAddr, _asset, _a)

    else:
        amountSent, na = extcall Vault(_vaultAddr).withdrawTokensFromVault(_user, _asset, _amount, _recipient, _a)
    return amountSent


# handle green


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

    # get the asset's debt terms
    assetDebtTerms: cs.DebtTerms = staticcall MissionControl(a.missionControl).getDebtTerms(_asset)
    if assetDebtTerms.ltv == 0:
        return max_value(uint256) # asset doesn't contribute to borrowing power

    # get current asset value for user
    userBalance: uint256 = staticcall Vault(vaultAddr).getTotalAmountForUser(_user, _asset)
    userUsdValue: uint256 = staticcall PriceDesk(a.priceDesk).getUsdValue(_asset, userBalance, False)
    if userUsdValue == 0:
        return 0 # cannot determine value

    # get borrow terms excluding the asset to withdraw
    isUndyVault: bool = self._isUnderscoreVault(_user, a.missionControl)
    btExcluding: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, True, _vaultId, _asset, isUndyVault, a)

    # calculate minimum asset value that must remain
    minAssetValueToRemain: uint256 = 0
    
    if btExcluding.collateralVal == 0:

        # entire debt must be supported by this asset
        minAssetValueToRemain = userDebt.amount * (HUNDRED_PERCENT + ONE_PERCENT) // assetDebtTerms.ltv

    # multi-asset case: use capacity-based calculation
    else:
        # Calculate how much debt the remaining assets can support
        remainingMaxDebt: uint256 = btExcluding.totalMaxDebt

        # Calculate total debt that needs to be supported (with 1% buffer)
        totalDebtNeeded: uint256 = userDebt.amount * (HUNDRED_PERCENT + ONE_PERCENT) // HUNDRED_PERCENT

        # If remaining assets can support all debt, can withdraw everything
        if remainingMaxDebt >= totalDebtNeeded:
            return max_value(uint256)

        # Calculate how much debt must be covered by this asset
        debtNeedingAssetSupport: uint256 = totalDebtNeeded - remainingMaxDebt

        # Calculate minimum collateral value needed from this asset
        # minCollateral = debtNeeded / assetLTV
        minAssetValueToRemain = debtNeedingAssetSupport * HUNDRED_PERCENT // assetDebtTerms.ltv

    # cannot withdraw if user has less than the minimum required
    if userUsdValue <= minAssetValueToRemain:
        return 0
    
    # convert to asset amount
    maxWithdrawableValue: uint256 = userUsdValue - minAssetValueToRemain
    return userBalance * maxWithdrawableValue // userUsdValue


# set buyback ratio


@external
def setBuybackRatio(_ratio: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: only switchboard allowed
    assert not deptBasics.isPaused # dev: contract paused
    assert _ratio <= HUNDRED_PERCENT # dev: invalid ratio
    self.buybackRatio = _ratio
    log BuybackRatioSet(ratio=_ratio)


########   #######  ########  ########   #######  ##      ## 
##     ## ##     ## ##     ## ##     ## ##     ## ##  ##  ## 
##     ## ##     ## ##     ## ##     ## ##     ## ##  ##  ## 
########  ##     ## ########  ########  ##     ## ##  ##  ## 
##     ## ##     ## ##   ##   ##   ##   ##     ## ##  ##  ## 
##     ## ##     ## ##    ##  ##    ##  ##     ## ##  ##  ## 
########   #######  ##     ## ##     ##  #######   ###  ###  