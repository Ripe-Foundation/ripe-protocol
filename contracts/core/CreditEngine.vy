# @version 0.4.1

from interfaces import Vault
from ethereum.ercs import IERC20

interface Ledger:
    def setUserDebt(_user: address, _userDebt: UserDebt, _interval: IntervalBorrow): nonpayable
    def userVaults(_user: address, _index: uint256) -> uint256: view
    def numUserVaults(_user: address) -> uint256: view
    def userDebt(_user: address) -> UserDebt: view
interface PriceDesk:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool) -> uint256: view

interface ControlRoom:
    def getDebtTerms(_vaultId: uint256, _asset: address) -> DebtTerms: view
    def isDaowryEnabled() -> bool: view

interface VaultBook:
    def getVault(_vaultId: uint256) -> address: view
    def getStakedGreenVault() -> address: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view
    def governance() -> address: view

interface LootBoxPoints:
    def updateBorrowPoints(_user: address, _didDebtChange: bool): nonpayable

struct DebtTerms:
    ltv: uint256
    redemptionThreshold: uint256
    liqThreshold: uint256
    liqFee: uint256
    borrowRate: uint256
    daowry: uint256

struct BorrowData:
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

TELLER_ID: constant(uint256) = 1 # TODO: make sure this is correct
LEDGER_ID: constant(uint256) = 2 # TODO: make sure this is correct
VAULT_BOOK_ID: constant(uint256) = 3 # TODO: make sure this is correct
LOOTBOX_ID: constant(uint256) = 5 # TODO: make sure this is correct
CONTROL_ROOM_ID: constant(uint256) = 6 # TODO: make sure this is correct
PRICE_DESK_ID: constant(uint256) = 7 # TODO: make sure this is correct

# config
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
ONE_YEAR: constant(uint256) = 60 * 60 * 24 * 365


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True


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


###############
# Borrow Data #
###############


@view
@external
def getBorrowDataForUser(_user: address, _shouldRaise: bool) -> BorrowData:
    return self._getBorrowDataForUser(_user, _shouldRaise, self._getAddys())


@view
@internal
def _getBorrowDataForUser(_user: address, _shouldRaise: bool, _addys: address[6]) -> BorrowData:
    ledger: address = _addys[1]
    vaultBook: address = _addys[2]
    controlRoom: address = _addys[4]
    priceDesk: address = _addys[5]

    # to facilitate weighted debt terms
    bd: BorrowData = empty(BorrowData)
    redemptionThresholdSum: uint256 = 0
    liqThresholdSum: uint256 = 0
    liqFeeSum: uint256 = 0
    borrowRateSum: uint256 = 0
    daowrySum: uint256 = 0
    totalSum: uint256 = 0

    # iterate thru each user vault
    numUserVaults: uint256 = staticcall Ledger(ledger).numUserVaults(_user)
    for i: uint256 in range(1, numUserVaults, bound=max_value(uint256)):
        vaultId: uint256 = staticcall Ledger(ledger).userVaults(_user, i)
        vaultAddr: address = staticcall VaultBook(vaultBook).getVault(vaultId)

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
            bd.collateralVal += collateralVal
            bd.totalMaxDebt += maxDebt

    # finalize debt terms (weighted)
    if totalSum != 0:
        bd.debtTerms.redemptionThreshold = redemptionThresholdSum // totalSum
        bd.debtTerms.liqThreshold = liqThresholdSum // totalSum
        bd.debtTerms.liqFee = liqFeeSum // totalSum
        bd.debtTerms.borrowRate = borrowRateSum // totalSum
        bd.debtTerms.daowry = daowrySum // totalSum

    # finalize overall ltv
    if bd.collateralVal != 0:
        bd.debtTerms.ltv = bd.totalMaxDebt * HUNDRED_PERCENT // bd.collateralVal

    # ensure liq threshold and liq fee can work together
    liqSum: uint256 = bd.debtTerms.liqThreshold + (bd.debtTerms.liqThreshold * bd.debtTerms.liqFee // HUNDRED_PERCENT)
    if liqSum > HUNDRED_PERCENT:
        adjustedLiqFee: uint256 = (HUNDRED_PERCENT - bd.debtTerms.liqThreshold) * HUNDRED_PERCENT // bd.debtTerms.liqThreshold
        bd.debtTerms.liqFee = adjustedLiqFee

    return bd


################
# Current Debt #
################


@view
@internal
def _getLatestUserDebt(_user: address, _ledger: address) -> (UserDebt, uint256):
    userDebt: UserDebt = staticcall Ledger(_ledger).userDebt(_user)

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


##########
# Borrow #
##########


@external
def borrowForUser(_user: address, _amount: uint256, _shouldStake: bool) -> uint256:
    addys: address[6] = self._getAddys()
    teller: address = addys[0]
    ledger: address = addys[1]
    lootBox: address = addys[3]
    assert msg.sender == teller # dev: only teller allowed

    # get latest user debt
    userDebt: UserDebt = empty(UserDebt)
    newInterest: uint256 = 0
    userDebt, newInterest = self._getLatestUserDebt(_user, ledger)

    # get borrow data (debt terms for user)
    borrowData: BorrowData = self._getBorrowDataForUser(_user, True, addys)

    # TODO: validation
    # not in liquidation
    # _amount != 0
    # ControlRoom.isBorrowEnabled ()
    # Borrow Intervals
    # global debt limit
    # borrowData.maxDebt - userDebt.amount
    # userDebt.amount >= minDebtAmount
    newBorrowAmount: uint256 = _amount
    userBorrowInterval: IntervalBorrow = empty(IntervalBorrow) # TODO: implement

    # update user debt
    userDebt.amount += newBorrowAmount
    userDebt.principal += newBorrowAmount
    userDebt.debtTerms = borrowData.debtTerms
    extcall Ledger(ledger).setUserDebt(_user, userDebt, userBorrowInterval)

    # update borrow points
    extcall LootBoxPoints(lootBox).updateBorrowPoints(_user, True)

    # mint green
    daowry: uint256 = self._handleGreenMint(_user, newBorrowAmount, newInterest, borrowData.debtTerms.daowry, _shouldStake, addys)

    # log NewBorrow(_user, newBorrowAmount, daowry)
    return newBorrowAmount


@internal
def _handleGreenMint(
    _user: address,
    _newBorrowAmount: uint256,
    _newInterest: uint256,
    _daowryRatio: uint256,
    _shouldStake: bool,
    _addys: address[6],
) -> uint256:
    vaultBook: address = _addys[2]
    controlRoom: address = _addys[4]
    greenToken: address = _addys[5]

    # mint green
    greenToMint: uint256 = _newBorrowAmount + _newInterest
    # mint green (comes to this contract)
    # AddyRegistry.mint(greenToMint)
    # TODO: implement

    # calc daowry (origination fee)
    daowry: uint256 = 0
    if _daowryRatio != 0 and staticcall ControlRoom(controlRoom).isDaowryEnabled():
        daowry = _newBorrowAmount * _daowryRatio // HUNDRED_PERCENT

    # transfer to green stakers
    self._sendGreenToStakers(greenToken, daowry + _newInterest, vaultBook)

    # auto-stake into strat
    forUser: uint256 = min(_newBorrowAmount - daowry, staticcall IERC20(greenToken).balanceOf(self))
    if _shouldStake:
        pass
        # TODO: implement auto-staking

    else:
        assert extcall IERC20(greenToken).transfer(_user, forUser) # dev: could not transfer

    return daowry


@internal
def _sendGreenToStakers(
    _greenToken: address,
    _amount: uint256,
    _vaultBook: address,
) -> bool:
    if _greenToken == empty(address) or _amount == 0:
        return False

    # staked green vault
    receiver: address = staticcall VaultBook(_vaultBook).getStakedGreenVault()

    # edge case (vault not set) -- for now transfer tokens to governance
    if receiver == empty(address):
        receiver = staticcall AddyRegistry(ADDY_REGISTRY).governance()

    # transfer tokens to staked green vault
    assert extcall IERC20(_greenToken).transfer(receiver, _amount) # dev: could not transfer
    return True
