# @version 0.4.1

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department

# deposit / withdrawals

struct DepositLedgerData:
    isParticipatingInVault: bool
    numUserVaults: uint256

# points / rewards

struct RipeRewards:
    stakers: uint256
    voteDepositors: uint256
    genDepositors: uint256
    borrowers: uint256
    newRipeRewards: uint256
    lastUpdate: uint256

struct GlobalDepositPoints:
    lastUsdValue: uint256
    ripeStakerPoints: uint256
    ripeVotePoints: uint256
    ripeGenPoints: uint256
    lastUpdate: uint256

struct AssetDepositPoints:
    balancePoints: uint256
    lastBalance: uint256
    lastUsdValue: uint256
    ripeStakerPoints: uint256
    ripeVotePoints: uint256
    ripeGenPoints: uint256
    lastUpdate: uint256
    precision: uint256

struct UserDepositPoints:
    balancePoints: uint256
    lastBalance: uint256
    lastUpdate: uint256

struct BorrowPoints:
    lastPrincipal: uint256
    points: uint256
    lastUpdate: uint256

struct BorrowPointsBundle:
    userPoints: BorrowPoints
    globalPoints: BorrowPoints
    userDebtPrincipal: uint256

struct DepositPointsBundle:
    userPoints: UserDepositPoints
    assetPoints: AssetDepositPoints
    globalPoints: GlobalDepositPoints

struct RipeRewardsBundle:
    ripeRewards: RipeRewards
    ripeAvailForRewards: uint256

# debt

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

struct DebtTerms:
    ltv: uint256
    redemptionThreshold: uint256
    liqThreshold: uint256
    liqFee: uint256
    borrowRate: uint256
    daowry: uint256

struct UserDebt:
    amount: uint256
    principal: uint256
    debtTerms: DebtTerms
    lastTimestamp: uint256
    inLiquidation: bool

struct IntervalBorrow:
    start: uint256
    amount: uint256

# auctions

struct FungibleAuction:
    liqUser: address
    vaultId: uint256
    asset: address 
    startDiscount: uint256
    maxDiscount: uint256
    startBlock: uint256
    endBlock: uint256
    isActive: bool

# user vault participation
userVaults: public(HashMap[address, HashMap[uint256, uint256]]) # user -> index -> vault id
indexOfVault: public(HashMap[address, HashMap[uint256, uint256]]) # user -> vault id -> index
numUserVaults: public(HashMap[address, uint256]) # user -> num vaults

# borrow data
userDebt: public(HashMap[address, UserDebt]) # user -> user debt
totalDebt: public(uint256) # total debt
borrowers: public(HashMap[uint256, address]) # index -> borrower
indexOfBorrower: public(HashMap[address, uint256]) # borrower -> index
numBorrowers: public(uint256) # num borrowers
borrowIntervals: public(HashMap[address, IntervalBorrow]) # user -> borrow interval
unrealizedYield: public(uint256) # unrealized yield

# ripe rewards
ripeRewards: public(RipeRewards)
ripeAvailForRewards: public(uint256)

# points
globalDepositPoints: public(GlobalDepositPoints)
assetDepositPoints: public(HashMap[uint256, HashMap[address, AssetDepositPoints]]) # vault id -> asset -> points
userDepositPoints: public(HashMap[address, HashMap[uint256, HashMap[address, UserDepositPoints]]]) # user -> vault id -> asset -> points
userBorrowPoints:  public(HashMap[address, BorrowPoints]) # user -> BorrowPoints
globalBorrowPoints: public(BorrowPoints)

# auctions
fungibleAuctions: public(HashMap[address, HashMap[uint256, FungibleAuction]]) # liq user -> auction index -> FungibleAuction
fungibleAuctionIndex: public(HashMap[address, HashMap[uint256, HashMap[address, uint256]]]) # liq user -> vault id -> asset -> auction index
numFungibleAuctions: public(HashMap[address, uint256]) # liq user -> num fungible auctions

fungLiqUsers: public(HashMap[uint256, address]) # index -> liq user
indexOfFungLiqUser: public(HashMap[address, uint256]) # liq user -> index
numFungLiqUsers: public(uint256) # num liq users


@deploy
def __init__(_ripeHq: address, _ripeAvailForRewards: uint256):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting

    if _ripeAvailForRewards != 0:
        self.ripeAvailForRewards = _ripeAvailForRewards


###############
# User Vaults #
###############


@view
@external
def isParticipatingInVault(_user: address, _vaultId: uint256) -> bool:
    return self.indexOfVault[_user][_vaultId] != 0


@view
@internal
def _getNumUserVaults(_user: address) -> uint256:
    numVaults: uint256 = self.numUserVaults[_user]
    if numVaults == 0:
        return 0
    return numVaults - 1


@external
def addVaultToUser(_user: address, _vaultId: uint256):
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert not deptBasics.isPaused # dev: not activated

    # already participating - fail gracefully
    if self.indexOfVault[_user][_vaultId] != 0:
        return

    # register vault
    vid: uint256 = self.numUserVaults[_user]
    if vid == 0:
        vid = 1 # not using 0 index

    self.userVaults[_user][vid] = _vaultId
    self.indexOfVault[_user][_vaultId] = vid
    self.numUserVaults[_user] = vid + 1


@external
def removeVaultFromUser(_user: address, _vaultId: uint256):
    assert msg.sender == addys._getLootboxAddr() # dev: only Lootbox allowed
    assert not deptBasics.isPaused # dev: not activated

    numUserVaults: uint256 = self.numUserVaults[_user]
    if numUserVaults == 0:
        return

    targetIndex: uint256 = self.indexOfVault[_user][_vaultId]
    if targetIndex == 0:
        return

    # update data
    lastIndex: uint256 = numUserVaults - 1
    self.numUserVaults[_user] = lastIndex
    self.indexOfVault[_user][_vaultId] = 0

    # have last vault replace the target vault
    if targetIndex != lastIndex:
        lastVaultId: uint256 = self.userVaults[_user][lastIndex]
        self.userVaults[_user][targetIndex] = lastVaultId
        self.indexOfVault[_user][lastVaultId] = targetIndex


# utils


@view
@external
def getDepositLedgerData(_user: address, _vaultId: uint256) -> DepositLedgerData:
    return DepositLedgerData(
        isParticipatingInVault=self.indexOfVault[_user][_vaultId] != 0,
        numUserVaults=self._getNumUserVaults(_user),
    )


########
# Debt #
########


@external
def setUserDebt(_user: address, _userDebt: UserDebt, _newYield: uint256, _interval: IntervalBorrow):
    assert msg.sender == addys._getCreditEngineAddr() # dev: only CreditEngine allowed
    assert not deptBasics.isPaused # dev: not activated

    # reduce prev user debt
    totalDebt: uint256 = self.totalDebt
    prevUserDebt: UserDebt = self.userDebt[_user]
    if prevUserDebt.amount != 0:
        totalDebt -= prevUserDebt.amount

    # save new user debt
    self.userDebt[_user] = _userDebt
    if _userDebt.amount != 0:
        totalDebt += _userDebt.amount
    self.totalDebt = totalDebt

    # update intervals -- during repay, we pass in empty interval
    if _interval.start != 0:
        self.borrowIntervals[_user] = _interval

    # update unrealized yield
    if _newYield != 0:
        self.unrealizedYield += _newYield

    # update fung auctions (if they exist)
    if prevUserDebt.inLiquidation and not _userDebt.inLiquidation:
        self._removeAllFungibleAuctions(_user)

    # remove borrower
    if _userDebt.amount == 0:
        self._removeBorrower(_user)

    # add borrower (if necessary)
    elif self.indexOfBorrower[_user] == 0:
        self._addNewBorrower(_user)


# realize yield


@external
def flushUnrealizedYield() -> uint256:
    assert msg.sender == addys._getCreditEngineAddr() # dev: only CreditEngine allowed
    assert not deptBasics.isPaused # dev: not activated

    unrealizedYield: uint256 = self.unrealizedYield
    self.unrealizedYield = 0
    return unrealizedYield


# registration


@internal
def _addNewBorrower(_user: address):
    bid: uint256 = self.numBorrowers
    if bid == 0:
        bid = 1 # not using 0 index
    self.borrowers[bid] = _user
    self.indexOfBorrower[_user] = bid
    self.numBorrowers = bid + 1


@internal
def _removeBorrower(_user: address):
    numBorrowers: uint256 = self.numBorrowers
    if numBorrowers == 0:
        return

    targetIndex: uint256 = self.indexOfBorrower[_user]
    if targetIndex == 0:
        return

    # update data
    lastIndex: uint256 = numBorrowers - 1
    self.numBorrowers = lastIndex
    self.indexOfBorrower[_user] = 0

    # shift users to replace the removed one
    if targetIndex != lastIndex:
        lastUser: address = self.borrowers[lastIndex]
        self.borrowers[targetIndex] = lastUser
        self.indexOfBorrower[lastUser] = targetIndex


# utils


@view
@external
def hasDebt(_user: address) -> bool:
    return self.userDebt[_user].amount != 0


@view
@external
def getBorrowDataBundle(_user: address) -> BorrowDataBundle:
    return BorrowDataBundle(
        userDebt=self.userDebt[_user],
        userBorrowInterval=self.borrowIntervals[_user],
        isUserBorrower=self.indexOfBorrower[_user] != 0,
        numUserVaults=self.numUserVaults[_user],
        totalDebt=self.totalDebt,
        numBorrowers=self.numBorrowers,
    )


@view
@external
def getRepayDataBundle(_user: address) -> RepayDataBundle:
    return RepayDataBundle(
        userDebt=self.userDebt[_user],
        numUserVaults=self.numUserVaults[_user],
    )


@view
@external
def isBorrower(_user: address) -> bool:
    return self.indexOfBorrower[_user] != 0


@view
@external
def isUserInLiquidation(_user: address) -> bool:
    return self.userDebt[_user].inLiquidation


####################
# Rewards / Points #
####################


# ripe rewards


@external
def setRipeRewards(_ripeRewards: RipeRewards):
    assert msg.sender == addys._getLootboxAddr() # dev: only Lootbox allowed
    assert not deptBasics.isPaused # dev: not activated
    self._setRipeRewards(_ripeRewards)


@internal
def _setRipeRewards(_ripeRewards: RipeRewards):
    self.ripeRewards = _ripeRewards
    if _ripeRewards.newRipeRewards != 0:
        self.ripeAvailForRewards -= min(self.ripeAvailForRewards, _ripeRewards.newRipeRewards)


@external
def setRipeAvailForRewards(_amount: uint256):
    assert msg.sender == addys._getLootboxAddr() # dev: only Lootbox allowed
    assert not deptBasics.isPaused # dev: not activated
    self.ripeAvailForRewards = _amount


# deposit points


@external
def setDepositPointsAndRipeRewards(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _userPoints: UserDepositPoints,
    _assetPoints: AssetDepositPoints,
    _globalPoints: GlobalDepositPoints,
    _ripeRewards: RipeRewards,
):
    assert msg.sender == addys._getLootboxAddr() # dev: only Lootbox allowed
    assert not deptBasics.isPaused # dev: not activated

    if _user != empty(address):
        self.userDepositPoints[_user][_vaultId][_asset] = _userPoints
    self.assetDepositPoints[_vaultId][_asset] = _assetPoints
    self.globalDepositPoints = _globalPoints
    self._setRipeRewards(_ripeRewards)


# borrow points


@external
def setBorrowPointsAndRipeRewards(
    _user: address,
    _userPoints: BorrowPoints,
    _globalPoints: BorrowPoints,
    _ripeRewards: RipeRewards,
):
    assert msg.sender == addys._getLootboxAddr() # dev: only Lootbox allowed
    assert not deptBasics.isPaused # dev: not activated

    self.globalBorrowPoints = _globalPoints
    if _user != empty(address):
        self.userBorrowPoints[_user] = _userPoints
    self._setRipeRewards(_ripeRewards)


# utils


@view
@external
def getRipeRewardsBundle() -> RipeRewardsBundle:
    return RipeRewardsBundle(
        ripeRewards=self.ripeRewards,
        ripeAvailForRewards=self.ripeAvailForRewards,
    )


@view
@external
def getBorrowPointsBundle(_user: address) -> BorrowPointsBundle:
    return BorrowPointsBundle(
        userPoints=self.userBorrowPoints[_user],
        globalPoints=self.globalBorrowPoints,
        userDebtPrincipal=self.userDebt[_user].principal,
    )


@view
@external
def getDepositPointsBundle(_user: address, _vaultId: uint256, _asset: address) -> DepositPointsBundle:
    userPoints: UserDepositPoints = empty(UserDepositPoints)
    if _user != empty(address):
        userPoints = self.userDepositPoints[_user][_vaultId][_asset]
    return DepositPointsBundle(
        userPoints=userPoints,
        assetPoints=self.assetDepositPoints[_vaultId][_asset],
        globalPoints=self.globalDepositPoints,
    )


############
# Auctions #
############


@view
@external
def hasFungibleAuctions(_liqUser: address) -> bool:
    return self.numFungibleAuctions[_liqUser] != 0


# create new auction


@external
def createNewFungibleAuction(_auc: FungibleAuction) -> uint256:
    assert msg.sender == addys._getAuctionHouseAddr() # dev: only AuctionHouse allowed
    assert not deptBasics.isPaused # dev: not activated

    # fail gracefully if auction already exists
    if self.fungibleAuctionIndex[_auc.liqUser][_auc.vaultId][_auc.asset] != 0:
        return 0

    # create new auction
    aid: uint256 = self.numFungibleAuctions[_auc.liqUser]
    if aid == 0:
        aid = 1
    self.fungibleAuctions[_auc.liqUser][aid] = _auc
    self.fungibleAuctionIndex[_auc.liqUser][_auc.vaultId][_auc.asset] = aid
    self.numFungibleAuctions[_auc.liqUser] = aid + 1

    # register fungible liq user (if applicable)
    if self.indexOfFungLiqUser[_auc.liqUser] == 0:
        self._registerFungibleLiqUser(_auc.liqUser)

    return aid


# register fungible liq user


@internal
def _registerFungibleLiqUser(_liqUser: address):
    uid: uint256 = self.numFungLiqUsers
    if uid == 0:
        uid = 1
    self.fungLiqUsers[uid] = _liqUser
    self.indexOfFungLiqUser[_liqUser] = uid
    self.numFungLiqUsers = uid + 1


# removal fungible auction


@external
def removeFungibleAuction(_liqUser: address, _vaultId: uint256, _asset: address):
    assert msg.sender == addys._getAuctionHouseAddr() # dev: only AuctionHouse allowed
    assert not deptBasics.isPaused # dev: not activated

    numAuctions: uint256 = self.numFungibleAuctions[_liqUser]
    if numAuctions == 0:
        return

    targetIndex: uint256 = self.fungibleAuctionIndex[_liqUser][_vaultId][_asset]
    if targetIndex == 0:
        return

    # update data
    lastIndex: uint256 = numAuctions - 1
    self.numFungibleAuctions[_liqUser] = lastIndex
    self.fungibleAuctionIndex[_liqUser][_vaultId][_asset] = 0

    # have last auction replace the target auction
    if targetIndex != lastIndex:
        lastItem: FungibleAuction = self.fungibleAuctions[_liqUser][lastIndex]
        self.fungibleAuctions[_liqUser][targetIndex] = lastItem
        self.fungibleAuctionIndex[_liqUser][lastItem.vaultId][lastItem.asset] = targetIndex

    # no more fungible auctions
    if lastIndex <= 1:
        self.numFungibleAuctions[_liqUser] = 0
        self._removeFungLiqUser(_liqUser)


# remove liq user


@internal
def _removeFungLiqUser(_liqUser: address):
    numUsers: uint256 = self.numFungLiqUsers
    if numUsers == 0:
        return

    targetIndex: uint256 = self.indexOfFungLiqUser[_liqUser]
    if targetIndex == 0:
        return

    # update data
    lastIndex: uint256 = numUsers - 1
    self.numFungLiqUsers = lastIndex
    self.indexOfFungLiqUser[_liqUser] = 0

    # have last liq user replace the target liq user
    if targetIndex != lastIndex:
        lastUser: address = self.fungLiqUsers[lastIndex]
        self.fungLiqUsers[targetIndex] = lastUser
        self.indexOfFungLiqUser[lastUser] = targetIndex


# remove all fungible auctions


@external
def removeAllFungibleAuctions(_liqUser: address):
    assert msg.sender in [addys._getAuctionHouseAddr(), addys._getCreditEngineAddr()] # dev: only AuctionHouse or CreditEngine allowed
    assert not deptBasics.isPaused # dev: not activated
    self._removeAllFungibleAuctions(_liqUser)


@internal
def _removeAllFungibleAuctions(_liqUser: address):
    self._removeFungLiqUser(_liqUser)

    numAuctions: uint256 = self.numFungibleAuctions[_liqUser]
    if numAuctions == 0:
        return

    # zero out the auction indexes
    for i: uint256 in range(1, numAuctions, bound=max_value(uint256)):
        auc: FungibleAuction = self.fungibleAuctions[_liqUser][i]
        self.fungibleAuctionIndex[_liqUser][auc.vaultId][auc.asset] = 0

    # zero out total num
    self.numFungibleAuctions[_liqUser] = 0


# utils


@view
@external
def getFungibleAuction(_liqUser: address, _vaultId: uint256, _asset: address) -> FungibleAuction:
    aid: uint256 = self.fungibleAuctionIndex[_liqUser][_vaultId][_asset]
    return self.fungibleAuctions[_liqUser][aid]


@view
@external
def getFungibleAuctionDuringPurchase(_liqUser: address, _vaultId: uint256, _asset: address) -> FungibleAuction:
    if not self.userDebt[_liqUser].inLiquidation:
        return empty(FungibleAuction)
    aid: uint256 = self.fungibleAuctionIndex[_liqUser][_vaultId][_asset]
    return self.fungibleAuctions[_liqUser][aid]


@view
@external
def hasFungibleAuction(_liqUser: address, _vaultId: uint256, _asset: address) -> bool:
    return self.fungibleAuctionIndex[_liqUser][_vaultId][_asset] != 0
