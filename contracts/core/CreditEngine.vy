# @version 0.4.1

initializes: addys
exports: addys.__interface__
import contracts.modules.Addys as addys

from interfaces import Vault
from ethereum.ercs import IERC20

interface Ledger:
    def setUserDebt(_user: address, _userDebt: UserDebt, _newInterest: uint256, _interval: IntervalBorrow): nonpayable
    def getBorrowDataBundle(_user: address) -> BorrowDataBundle: view
    def userVaults(_user: address, _index: uint256) -> uint256: view
    def getRepayDataBundle(_user: address) -> RepayDataBundle: view
    def numUserVaults(_user: address) -> uint256: view
    def flushUnrealizedYield() -> uint256: nonpayable

interface ControlRoom:
    def getBorrowConfig(_user: address, _caller: address) -> BorrowConfig: view
    def getDebtTerms(_vaultId: uint256, _asset: address) -> DebtTerms: view
    def getRepayConfig(_user: address) -> RepayConfig: view
    def isDaowryEnabled() -> bool: view

interface PriceDesk:
    def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256: view
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool) -> uint256: view

interface GreenToken:
    def burn(_from: address, _amount: uint256): nonpayable
    def mint(_to: address, _amount: uint256): nonpayable

interface VaultBook:
    def getVault(_vaultId: uint256) -> address: view
    def getStakedGreenVault() -> address: view

interface LootBox:
    def updateBorrowPoints(_user: address, _a: addys.Addys = empty(addys.Addys)): nonpayable

interface RipeHq:
    def governance() -> address: view

struct BorrowDataBundle:
    userDebt: UserDebt
    userBorrowInterval: IntervalBorrow
    isUserBorrower: bool
    numUserVaults: uint256
    totalDebt: uint256
    numBorrowers: uint256

struct RepayDataBundle:
    userDebt: UserDebt
    numUserVaults: uint256

struct BorrowConfig:
    isBorrowEnabled: bool
    canBorrowForUser: bool
    numAllowedBorrowers: uint256
    maxBorrowPerInterval: uint256
    numBlocksPerInterval: uint256
    perUserDebtLimit: uint256
    globalDebtLimit: uint256
    minDebtAmount: uint256

struct RepayConfig:
    isRepayEnabled: bool
    canOthersRepayForUser: bool

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

event NewBorrow:
    user: indexed(address)
    newLoan: uint256
    daowry: uint256
    didStake: bool
    outstandingUserDebt: uint256
    userCollateralVal: uint256
    maxUserDebt: uint256
    globalYieldRealized: uint256

event RepayDebt:
    user: indexed(address)
    repayAmount: uint256
    refundAmount: uint256
    didStakeRefund: bool
    outstandingUserDebt: uint256
    userCollateralVal: uint256
    maxUserDebt: uint256

# config
isActivated: public(bool)

ONE_YEAR: constant(uint256) = 60 * 60 * 24 * 365
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
ONE_PERCENT: constant(uint256) = 1_00 # 1.00%
MAX_DEBT_UPDATES: constant(uint256) = 25


@deploy
def __init__(_hq: address):
    addys.__init__(_hq)
    self.isActivated = True


##########
# Borrow #
##########


@external
def borrowForUser(
    _user: address,
    _amount: uint256,
    _shouldStake: bool,
    _caller: address,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only teller allowed

    # get borrow data
    a: addys.Addys = addys._getAddys(_a)
    d: BorrowDataBundle = staticcall Ledger(a.ledger).getBorrowDataBundle(_user)

    # get latest user debt
    userDebt: UserDebt = empty(UserDebt)
    newInterest: uint256 = 0
    userDebt, newInterest = self._getLatestUserDebtWithInterest(d.userDebt)

    # get borrow data (debt terms for user)
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, True, a)

    # validation
    newBorrowAmount: uint256 = 0
    isFreshInterval: bool = False
    newBorrowAmount, isFreshInterval = self._validateOnBorrow(_user, _caller, _amount, userDebt, bt.totalMaxDebt, d.userBorrowInterval, d.isUserBorrower, d.numBorrowers, d.totalDebt, a.controlRoom)
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
    extcall Ledger(a.ledger).setUserDebt(_user, userDebt, newInterest, userBorrowInterval)

    # update borrow points
    extcall LootBox(a.lootbox).updateBorrowPoints(_user, a)

    # mint green - piggy back on borrow to flush unrealized yield
    unrealizedYield: uint256 = extcall Ledger(a.ledger).flushUnrealizedYield()
    totalGreenMint: uint256 = newBorrowAmount + unrealizedYield
    extcall GreenToken(a.greenToken).mint(self, totalGreenMint)

    # origination fee
    daowry: uint256 = self._getDaowryAmount(newBorrowAmount, bt.debtTerms.daowry, a.controlRoom)

    # green for stakers
    forGreenStakers: uint256 = daowry + unrealizedYield
    if forGreenStakers != 0:
        self._sendGreenToStakers(a.greenToken, forGreenStakers, a.vaultBook)

    # borrower gets their green now -- do this AFTER sending green to stakers
    forBorrower: uint256 = newBorrowAmount - daowry
    self._handleGreenForUser(_user, forBorrower, _shouldStake, a.greenToken)

    log NewBorrow(user=_user, newLoan=forBorrower, daowry=daowry, didStake=_shouldStake, outstandingUserDebt=userDebt.amount, userCollateralVal=bt.collateralVal, maxUserDebt=bt.totalMaxDebt, globalYieldRealized=unrealizedYield)
    return forBorrower


# borrow validation


@view
@internal
def _validateOnBorrow(
    _user: address,
    _caller: address,
    _amount: uint256,
    _userDebt: UserDebt,
    _maxUserDebt: uint256,
    _userBorrowInterval: IntervalBorrow,
    _isUserBorrower: bool,
    _numBorrowers: uint256,
    _totalDebt: uint256,
    _controlRoom: address,
) -> (uint256, bool):
    assert not _userDebt.inLiquidation # dev: cannot borrow in liquidation
    assert _amount != 0 # dev: cannot borrow 0 amount

    # get borrow config
    config: BorrowConfig = staticcall ControlRoom(_controlRoom).getBorrowConfig(_user, _caller)
    assert config.isBorrowEnabled # dev: borrow not enabled
    assert config.canBorrowForUser # dev: cannot borrow for user

    # check num allowed borrowers
    if not _isUserBorrower:
        numAvailBorrowers: uint256 = self._getAvailNumBorrowers(_numBorrowers, config.numAllowedBorrowers)
        assert numAvailBorrowers != 0 # dev: max num borrowers reached

    # main var
    newBorrowAmount: uint256 = _amount

    # avail debt based on collateral value / ltv
    availDebtPerLtv: uint256 = self._getAvailBasedOnLtv(_userDebt.amount, _maxUserDebt)
    assert availDebtPerLtv != 0 # dev: no debt available
    newBorrowAmount = min(newBorrowAmount, availDebtPerLtv)

    # check borrow interval
    availInInterval: uint256 = 0
    isFreshInterval: bool = False
    availInInterval, isFreshInterval = self._getAvailDebtInInterval(_userBorrowInterval, config.maxBorrowPerInterval, config.numBlocksPerInterval)
    assert availInInterval != 0 # dev: interval borrow limit reached
    newBorrowAmount = min(newBorrowAmount, availInInterval)

    # check per user debt limit
    availPerUser: uint256 = self._getAvailPerUserDebt(_userDebt.amount, config.perUserDebtLimit)
    assert availPerUser != 0 # dev: per user debt limit reached
    newBorrowAmount = min(newBorrowAmount, availPerUser)

    # check global debt limit
    availGlobal: uint256 = self._getAvailGlobalDebt(_totalDebt, config.globalDebtLimit)
    assert availGlobal != 0 # dev: global debt limit reached
    newBorrowAmount = min(newBorrowAmount, availGlobal)

    # must reach minimum debt threshold
    assert _userDebt.amount + newBorrowAmount >= config.minDebtAmount # dev: debt too small

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
    if not config.isBorrowEnabled:
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
    _amount: uint256,
    _shouldStakeRefund: bool,
    _caller: address,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only teller allowed

    # get repay data
    a: addys.Addys = addys._getAddys(_a)
    d: RepayDataBundle = staticcall Ledger(a.ledger).getRepayDataBundle(_user)

    # get latest user debt
    userDebt: UserDebt = empty(UserDebt)
    newInterest: uint256 = 0
    userDebt, newInterest = self._getLatestUserDebtWithInterest(d.userDebt)
    nonPrincipalDebt: uint256 = userDebt.amount - userDebt.principal

    # validation
    repayAmount: uint256 = 0
    refundAmount: uint256 = 0
    repayAmount, refundAmount = self._validateOnRepay(_user, _caller, _amount, userDebt, a)

    # get borrow data (debt terms for user)
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, True, a)

    # update user debt
    userDebt.amount -= repayAmount
    if repayAmount > nonPrincipalDebt:
        principalToReduce: uint256 = repayAmount - nonPrincipalDebt
        userDebt.principal -= min(principalToReduce, userDebt.principal)
    userDebt.debtTerms = bt.debtTerms
    extcall Ledger(a.ledger).setUserDebt(_user, userDebt, newInterest, empty(IntervalBorrow))

    # update borrow points
    extcall LootBox(a.lootbox).updateBorrowPoints(_user, a)

    # burn green repayment
    extcall GreenToken(a.greenToken).burn(self, repayAmount)

    # handle refund
    if refundAmount != 0:
        self._handleGreenForUser(_user, refundAmount, _shouldStakeRefund, a.greenToken)

    log RepayDebt(user=_user, repayAmount=repayAmount, refundAmount=refundAmount, didStakeRefund=_shouldStakeRefund, outstandingUserDebt=userDebt.amount, userCollateralVal=bt.collateralVal, maxUserDebt=bt.totalMaxDebt)
    return repayAmount


# repay validation


@view
@internal
def _validateOnRepay(
    _user: address,
    _caller: address,
    _amount: uint256,
    _userDebt: UserDebt,
    _a: addys.Addys,
) -> (uint256, uint256):
    assert _userDebt.amount != 0 # dev: no debt outstanding

    # get repay config
    repayConfig: RepayConfig = staticcall ControlRoom(_a.controlRoom).getRepayConfig(_user)
    assert repayConfig.isRepayEnabled # dev: repay paused
    if _user != _caller:
        assert repayConfig.canOthersRepayForUser # dev: cannot repay for user

    # available amount
    availAmount: uint256 = min(_amount, staticcall IERC20(_a.greenToken).balanceOf(self))
    assert availAmount != 0 # dev: cannot repay with 0 green

    # finalize amounts
    repayAmount: uint256 = min(availAmount, _userDebt.amount)
    refundAmount: uint256 = 0
    if repayAmount > availAmount:
        refundAmount = repayAmount - availAmount

    return repayAmount, refundAmount


# repay during liquidation


@external
def repayDebtDuringLiquidation(
    _liqUser: address,
    _userDebt: UserDebt,
    _amount: uint256,
    _newInterest: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> bool:
    assert msg.sender == addys._getAuctionHouseAddr() # dev: only auction house allowed
    a: addys.Addys = addys._getAddys(_a)

    userDebt: UserDebt = _userDebt
    nonPrincipalDebt: uint256 = userDebt.amount - userDebt.principal

    # reduce debt with repay amount
    userDebt.amount -= _amount
    if _amount > nonPrincipalDebt:
        principalToReduce: uint256 = _amount - nonPrincipalDebt
        userDebt.principal -= min(principalToReduce, userDebt.principal)

    # refresh collateral value and debt terms -- LIKELY CHANGED during liquidation (swaps with stability pool)
    numUserVaults: uint256 = staticcall Ledger(a.ledger).numUserVaults(_liqUser)
    bt: UserBorrowTerms = self._getUserBorrowTerms(_liqUser, numUserVaults, True, a)
    userDebt.debtTerms = bt.debtTerms

    # check debt health
    hasGoodDebtHealth: bool = self._hasGoodDebtHealth(userDebt.amount, bt.collateralVal, bt.debtTerms.ltv)
    if hasGoodDebtHealth:
        userDebt.inLiquidation = False

    # save user debt
    extcall Ledger(a.ledger).setUserDebt(_liqUser, userDebt, _newInterest, empty(IntervalBorrow))

    return hasGoodDebtHealth


################
# Borrow Terms #
################


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
        vaultAddr: address = staticcall VaultBook(_a.vaultBook).getVault(vaultId)
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
            debtTerms: DebtTerms = staticcall ControlRoom(_a.controlRoom).getDebtTerms(vaultId, asset)

            # collateral value, max debt
            collateralVal: uint256 = staticcall PriceDesk(_a.priceDesk).getUsdValue(asset, amount, _shouldRaise)
            maxDebt: uint256 = collateralVal * debtTerms.ltv // HUNDRED_PERCENT

            # debt terms sums -- weight is based on max debt (ltv)
            if maxDebt != 0:
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
def updateDebtForUser(_user: address) -> bool:
    return self._updateDebtForUser(_user, addys._getAddys())


@external
def updateDebtForManyUsers(_users: DynArray[address, MAX_DEBT_UPDATES]) -> bool:
    a: addys.Addys = addys._getAddys()
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
        return False

    userDebt.debtTerms = bt.debtTerms
    extcall Ledger(_a.ledger).setUserDebt(_user, userDebt, newInterest, empty(IntervalBorrow))

    # update borrow points
    extcall LootBox(_a.lootbox).updateBorrowPoints(_user, _a)
    return True


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


# green to stakers


@internal
def _sendGreenToStakers(
    _greenToken: address,
    _amount: uint256,
    _vaultBook: address,
) -> bool:
    receiver: address = staticcall VaultBook(_vaultBook).getStakedGreenVault()

    # edge case (vault not set) -- for now transfer tokens to governance
    if receiver == empty(address):
        receiver = staticcall RipeHq(addys._getRipeHq()).governance()

    # transfer tokens to staked green vault
    amount: uint256 = min(_amount, staticcall IERC20(_greenToken).balanceOf(self))
    assert extcall IERC20(_greenToken).transfer(receiver, amount) # dev: could not transfer
    return True


# green for user


@internal
def _handleGreenForUser(
    _user: address,
    _amount: uint256,
    _shouldStake: bool,
    _greenToken: address,
):
    amount: uint256 = min(_amount, staticcall IERC20(_greenToken).balanceOf(self))
    assert extcall IERC20(_greenToken).transfer(_user, amount) # dev: could not transfer

    # TODO: handle staking


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
def _getDaowryAmount(_borrowAmount: uint256, _daowryFee: uint256, _controlRoom: address) -> uint256:
    daowry: uint256 = 0
    if _daowryFee != 0 and staticcall ControlRoom(_controlRoom).isDaowryEnabled():
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