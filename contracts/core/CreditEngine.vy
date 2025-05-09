# @version 0.4.1

from interfaces import Vault
from ethereum.ercs import IERC20

interface Ledger:
    def setUserDebt(_user: address, _userDebt: UserDebt, _newInterest: uint256, _interval: IntervalBorrow): nonpayable
    def getBorrowDataBundle(_user: address) -> BorrowDataBundle: view
    def userVaults(_user: address, _index: uint256) -> uint256: view
    def getRepayDataBundle(_user: address) -> RepayDataBundle: view
    def flushUnrealizedYield() -> uint256: nonpayable

interface ControlRoom:
    def getDebtTerms(_vaultId: uint256, _asset: address) -> DebtTerms: view
    def getBorrowConfig() -> BorrowConfig: view
    def isDaowryEnabled() -> bool: view
    def isRepayEnabled() -> bool: view

interface GreenToken:
    def burn(_from: address, _amount: uint256): nonpayable
    def mint(_to: address, _amount: uint256): nonpayable

interface VaultBook:
    def getVault(_vaultId: uint256) -> address: view
    def getStakedGreenVault() -> address: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view
    def governance() -> address: view

interface PriceDesk:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool) -> uint256: view

interface LootBox:
    def updateBorrowPoints(_user: address): nonpayable

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
    numAllowedBorrowers: uint256
    maxBorrowPerInterval: uint256
    numBlocksPerInterval: uint256
    perUserDebtLimit: uint256
    globalDebtLimit: uint256
    minDebtAmount: uint256

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

TELLER_ID: constant(uint256) = 1 # TODO: make sure this is correct
LEDGER_ID: constant(uint256) = 2 # TODO: make sure this is correct
VAULT_BOOK_ID: constant(uint256) = 3 # TODO: make sure this is correct
LOOTBOX_ID: constant(uint256) = 5 # TODO: make sure this is correct
CONTROL_ROOM_ID: constant(uint256) = 6 # TODO: make sure this is correct
PRICE_DESK_ID: constant(uint256) = 7 # TODO: make sure this is correct

# config
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))

ONE_YEAR: constant(uint256) = 60 * 60 * 24 * 365
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_DEBT_UPDATES: constant(uint256) = 25


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True


##########
# Borrow #
##########


@external
def borrowForUser(
    _user: address,
    _amount: uint256,
    _shouldStake: bool,
    _greenToken: address,
) -> uint256:
    addys: address[6] = self._getAddys()
    teller: address = addys[0]
    ledger: address = addys[1]
    lootBox: address = addys[3]
    controlRoom: address = addys[4]
    vaultBook: address = addys[2]
    assert msg.sender == teller # dev: only teller allowed

    # get borrow data
    d: BorrowDataBundle = staticcall Ledger(ledger).getBorrowDataBundle(_user)

    # get latest user debt
    userDebt: UserDebt = empty(UserDebt)
    newInterest: uint256 = 0
    userDebt, newInterest = self._getLatestUserDebtWithInterest(d.userDebt)

    # get borrow data (debt terms for user)
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, True, addys)

    # validation
    newBorrowAmount: uint256 = 0
    isFreshInterval: bool = False
    newBorrowAmount, isFreshInterval = self._validateOnBorrow(_amount, userDebt, bt.totalMaxDebt, d.userBorrowInterval, d.isUserBorrower, d.numBorrowers, d.totalDebt, controlRoom)
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
    extcall Ledger(ledger).setUserDebt(_user, userDebt, newInterest, userBorrowInterval)

    # update borrow points
    extcall LootBox(lootBox).updateBorrowPoints(_user)

    # mint green - piggy back on borrow to flush unrealized yield
    unrealizedYield: uint256 = extcall Ledger(ledger).flushUnrealizedYield()
    totalGreenMint: uint256 = newBorrowAmount + unrealizedYield
    extcall GreenToken(_greenToken).mint(self, totalGreenMint)

    # origination fee
    daowry: uint256 = self._getDaowryAmount(newBorrowAmount, bt.debtTerms.daowry, controlRoom)

    # green for stakers
    forGreenStakers: uint256 = daowry + unrealizedYield
    if forGreenStakers != 0:
        self._sendGreenToStakers(_greenToken, forGreenStakers, vaultBook)

    # borrower gets their green now -- do this AFTER sending green to stakers
    forBorrower: uint256 = newBorrowAmount - daowry
    self._handleGreenForUser(_user, forBorrower, _shouldStake, _greenToken)

    log NewBorrow(user=_user, newLoan=forBorrower, daowry=daowry, didStake=_shouldStake, outstandingUserDebt=userDebt.amount, userCollateralVal=bt.collateralVal, maxUserDebt=bt.totalMaxDebt, globalYieldRealized=unrealizedYield)
    return forBorrower


# borrow validation


@view
@internal
def _validateOnBorrow(
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
    config: BorrowConfig = staticcall ControlRoom(_controlRoom).getBorrowConfig()
    assert config.isBorrowEnabled # dev: borrow not enabled

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
    addys: address[6] = self._getAddys()
    ledger: address = addys[1]
    controlRoom: address = addys[4]

    # get latest user debt
    d: BorrowDataBundle = staticcall Ledger(ledger).getBorrowDataBundle(_user)
    userDebt: UserDebt = empty(UserDebt)
    na1: uint256 = 0
    userDebt, na1 = self._getLatestUserDebtWithInterest(d.userDebt)

    # cannot borrow in liquidation
    if userDebt.inLiquidation:
        return 0

    # get borrow config
    config: BorrowConfig = staticcall ControlRoom(controlRoom).getBorrowConfig()
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
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, False, addys)
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
    _repayAmount: uint256,
    _shouldStakeRefund: bool,
    _greenToken: address,
) -> uint256:
    addys: address[6] = self._getAddys()
    teller: address = addys[0]
    ledger: address = addys[1]
    lootBox: address = addys[3]
    controlRoom: address = addys[4]
    assert msg.sender == teller # dev: only teller allowed

    # get repay data
    d: RepayDataBundle = staticcall Ledger(ledger).getRepayDataBundle(_user)

    # get latest user debt
    userDebt: UserDebt = empty(UserDebt)
    newInterest: uint256 = 0
    userDebt, newInterest = self._getLatestUserDebtWithInterest(d.userDebt)
    totalAccruedInterest: uint256 = userDebt.amount - userDebt.principal

    # validation
    repayAmount: uint256 = 0
    refundAmount: uint256 = 0
    repayAmount, refundAmount = self._validateOnRepay(_repayAmount, userDebt, _greenToken, controlRoom)

    # get borrow data (debt terms for user)
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, True, addys)

    # update user debt
    userDebt.amount -= repayAmount
    if repayAmount > totalAccruedInterest:
        userDebt.principal -= min(userDebt.principal, totalAccruedInterest)
    userDebt.debtTerms = bt.debtTerms
    extcall Ledger(ledger).setUserDebt(_user, userDebt, newInterest, empty(IntervalBorrow))

    # update borrow points
    extcall LootBox(lootBox).updateBorrowPoints(_user)

    # burn green repayment
    extcall GreenToken(_greenToken).burn(self, repayAmount)

    # handle refund
    if refundAmount != 0:
        self._handleGreenForUser(_user, refundAmount, _shouldStakeRefund, _greenToken)

    log RepayDebt(user=_user, repayAmount=repayAmount, refundAmount=refundAmount, didStakeRefund=_shouldStakeRefund, outstandingUserDebt=userDebt.amount, userCollateralVal=bt.collateralVal, maxUserDebt=bt.totalMaxDebt)
    return repayAmount


# repay validation


@view
@internal
def _validateOnRepay(
    _repayAmount: uint256,
    _userDebt: UserDebt,
    _greenToken: address,
    _controlRoom: address,
) -> (uint256, uint256):
    assert _userDebt.amount != 0 # dev: no debt outstanding
    assert staticcall ControlRoom(_controlRoom).isRepayEnabled() # dev: repay paused

    # available amount
    availAmount: uint256 = min(_repayAmount, staticcall IERC20(_greenToken).balanceOf(self))
    assert availAmount != 0 # dev: cannot repay with 0 green

    # finalize amounts
    repayAmount: uint256 = min(availAmount, _userDebt.amount)
    refundAmount: uint256 = 0
    if repayAmount > availAmount:
        refundAmount = repayAmount - availAmount

    return repayAmount, refundAmount


################
# Borrow Terms #
################


@view
@external
def getUserBorrowTerms(_user: address, _shouldRaise: bool) -> UserBorrowTerms:
    addys: address[6] = self._getAddys()
    data: BorrowDataBundle = staticcall Ledger(addys[1]).getBorrowDataBundle(_user)
    return self._getUserBorrowTerms(_user, data.numUserVaults, _shouldRaise, addys)


@view
@internal
def _getUserBorrowTerms(
    _user: address,
    _numUserVaults: uint256,
    _shouldRaise: bool,
    _addys: address[6],
) -> UserBorrowTerms:
    ledger: address = _addys[1]
    vaultBook: address = _addys[2]
    controlRoom: address = _addys[4]
    priceDesk: address = _addys[5]

    # to facilitate weighted debt terms
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    redemptionThresholdSum: uint256 = 0
    liqThresholdSum: uint256 = 0
    liqFeeSum: uint256 = 0
    borrowRateSum: uint256 = 0
    daowrySum: uint256 = 0
    totalSum: uint256 = 0

    # iterate thru each user vault
    for i: uint256 in range(1, _numUserVaults, bound=max_value(uint256)):
        vaultId: uint256 = staticcall Ledger(ledger).userVaults(_user, i)
        vaultAddr: address = staticcall VaultBook(vaultBook).getVault(vaultId)
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
            debtTerms: DebtTerms = staticcall ControlRoom(controlRoom).getDebtTerms(vaultId, asset)

            # collateral value, max debt
            collateralVal: uint256 = staticcall PriceDesk(priceDesk).getUsdValue(asset, amount, _shouldRaise)
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


###############
# Update Debt #
###############


@external
def updateDebtForUser(_user: address) -> bool:
    addys: address[6] = self._getAddys()
    return self._updateDebtForUser(_user, addys)


@external
def updateDebtForManyUsers(_users: DynArray[address, MAX_DEBT_UPDATES]) -> bool:
    addys: address[6] = self._getAddys()
    for u: address in _users:
        self._updateDebtForUser(u, addys)
    return True


@internal
def _updateDebtForUser(_user: address, _addys: address[6]) -> bool:
    ledger: address = _addys[1]
    lootBox: address = _addys[3]

    # get data (repay data has the only stuff we need)
    d: RepayDataBundle = staticcall Ledger(ledger).getRepayDataBundle(_user)
    if d.userDebt.amount == 0:
        return False

    # accrue interest
    userDebt: UserDebt = empty(UserDebt)
    newInterest: uint256 = 0
    userDebt, newInterest = self._getLatestUserDebtWithInterest(d.userDebt)

    # debt terms for user
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, True, _addys)
    userDebt.debtTerms = bt.debtTerms
    extcall Ledger(ledger).setUserDebt(_user, userDebt, newInterest, empty(IntervalBorrow))

    # update borrow points
    extcall LootBox(lootBox).updateBorrowPoints(_user)
    return True


###############
# Debt Health #
###############


@view
@external
def hasGoodDebtHealth(_user: address) -> bool:
    return self._checkDebtHealth(_user, True, self._getAddys())


@view
@external
def canLiquidateUser(_user: address) -> bool:
    return self._checkDebtHealth(_user, False, self._getAddys())


@view
@internal
def _checkDebtHealth(_user: address, _shouldCheckLtv: bool, _addys: address[6]) -> bool:
    ledger: address = _addys[1]

    # get data (repay data has the only stuff we need)
    d: RepayDataBundle = staticcall Ledger(ledger).getRepayDataBundle(_user)
    if d.userDebt.amount == 0:
        return _shouldCheckLtv # nothing to check, use that var to return correct value

    userDebt: UserDebt = empty(UserDebt)
    na: uint256 = 0
    userDebt, na = self._getLatestUserDebtWithInterest(d.userDebt)
    bt: UserBorrowTerms = self._getUserBorrowTerms(_user, d.numUserVaults, False, _addys)

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
        receiver = staticcall AddyRegistry(ADDY_REGISTRY).governance()

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


# addys


@view
@internal
def _getAddys() -> address[6]:
    ar: address = ADDY_REGISTRY
    teller: address = staticcall AddyRegistry(ar).getAddy(TELLER_ID)
    ledger: address = staticcall AddyRegistry(ar).getAddy(LEDGER_ID)
    vaultBook: address = staticcall AddyRegistry(ar).getAddy(VAULT_BOOK_ID)
    lootBox: address = staticcall AddyRegistry(ar).getAddy(LOOTBOX_ID)
    controlRoom: address = staticcall AddyRegistry(ar).getAddy(CONTROL_ROOM_ID)
    priceDesk: address = staticcall AddyRegistry(ar).getAddy(PRICE_DESK_ID)
    return [teller, ledger, vaultBook, lootBox, controlRoom, priceDesk]