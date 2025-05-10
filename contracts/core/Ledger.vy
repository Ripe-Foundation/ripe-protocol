# @version 0.4.1

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

# deposit / withdrawals


struct DepositLedgerData:
    isParticipatingInVault: bool
    numUserVaults: uint256


# points / rewards

struct RipeRewards:
    stakers: uint256
    borrowers: uint256
    voteDepositors: uint256
    genDepositors: uint256
    newRipeRewards: uint256
    lastUpdate: uint256
    lastRewardsBlock: uint256

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

# user vault participation
userVaults: public(HashMap[address, HashMap[uint256, uint256]]) # user -> index -> vault id
indexOfVault: public(HashMap[address, HashMap[uint256, uint256]]) # user -> vault id -> index
numUserVaults: public(HashMap[address, uint256]) # user -> num vaults

# ripe rewards
ripeRewards: public(RipeRewards)
ripeAvailForRewards: public(uint256)

# borrow data
userDebt: public(HashMap[address, UserDebt]) # user -> user debt
totalDebt: public(uint256) # total debt
borrowers: public(HashMap[uint256, address]) # index -> borrower
indexOfBorrower: public(HashMap[address, uint256]) # borrower -> index
numBorrowers: public(uint256) # num borrowers
borrowIntervals: public(HashMap[address, IntervalBorrow]) # user -> borrow interval
unrealizedYield: public(uint256) # unrealized yield

# points
globalDepositPoints: public(GlobalDepositPoints)
assetDepositPoints: public(HashMap[uint256, HashMap[address, AssetDepositPoints]]) # vault id -> asset -> points
userDepositPoints: public(HashMap[address, HashMap[uint256, HashMap[address, UserDepositPoints]]]) # user -> vault id -> asset -> points
userBorrowPoints:  public(HashMap[address, BorrowPoints]) # user -> BorrowPoints
globalBorrowPoints: public(BorrowPoints)

TELLER_ID: constant(uint256) = 1 # TODO: make sure this is correct
LOOTBOX_ID: constant(uint256) = 5 # TODO: make sure this is correct
CREDIT_ENGINE_ID: constant(uint256) = 8 # TODO: make sure this is correct

# config
ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry


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
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(TELLER_ID) # dev: only Teller allowed

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
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(TELLER_ID) # dev: only Teller allowed

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
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(CREDIT_ENGINE_ID) # dev: only CreditEngine allowed

    # reduce prev user debt
    totalDebt: uint256 = self.totalDebt
    prevUserDebt: uint256 = self.userDebt[_user].amount
    if prevUserDebt != 0:
        totalDebt -= prevUserDebt

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

    # remove borrower
    if _userDebt.amount == 0:
        self._removeBorrower(_user)

    # add borrower (if necessary)
    elif self.indexOfBorrower[_user] == 0:
        self._addNewBorrower(_user)


# realize yield


@external
def flushUnrealizedYield() -> uint256:
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(CREDIT_ENGINE_ID) # dev: only CreditEngine allowed
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


####################
# Rewards / Points #
####################


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
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(LOOTBOX_ID) # dev: only Lootbox allowed

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
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(LOOTBOX_ID) # dev: only Lootbox allowed

    self.globalBorrowPoints = _globalPoints
    if _user != empty(address):
        self.userBorrowPoints[_user] = _userPoints
    self._setRipeRewards(_ripeRewards)


# ripe rewards


@external
def setRipeRewards(_ripeRewards: RipeRewards):
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(LOOTBOX_ID) # dev: only Lootbox allowed
    self._setRipeRewards(_ripeRewards)


@internal
def _setRipeRewards(_ripeRewards: RipeRewards):
    self.ripeRewards = _ripeRewards
    if _ripeRewards.newRipeRewards != 0:
        self.ripeAvailForRewards -= min(self.ripeAvailForRewards, _ripeRewards.newRipeRewards)


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
