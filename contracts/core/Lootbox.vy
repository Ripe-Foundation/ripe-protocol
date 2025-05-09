# @version 0.4.1

from interfaces import Vault
from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed

interface Ledger:
    def setDepositPointsAndRipeRewards(_user: address, _vaultId: uint256, _asset: address, _userPoints: UserDepositPoints, _assetPoints: AssetDepositPoints, _globalPoints: GlobalDepositPoints, _ripeRewards: RipeRewards): nonpayable
    def setBorrowPointsAndRipeRewards(_user: address, _userPoints: BorrowPoints, _globalPoints: BorrowPoints, _ripeRewards: RipeRewards): nonpayable
    def getDepositPointsBundle(_user: address, _vaultId: uint256, _asset: address) -> DepositPointsBundle: view
    def getBorrowPointsBundle(_user: address) -> BorrowPointsBundle: view
    def userVaults(_user: address, _index: uint256) -> uint256: view
    def setRipeRewards(_ripeRewards: RipeRewards): nonpayable
    def getRipeRewardsBundle() -> RipeRewardsBundle: view
    def numUserVaults(_user: address) -> uint256: view

interface AddyRegistry:
    def isValidAddyAddr(_addr: address) -> bool: view
    def getAddy(_addyId: uint256) -> address: view
    def ripeToken() -> address: view

interface VaultBook:
    def getVault(_vaultId: uint256) -> address: view
    def isNftVault(_vaultId: uint256) -> bool: view

interface ControlRoom:
    def getDepositPointsAllocs(_vaultId: uint256, _asset: address) -> DepositPointsAllocs: view
    def getRipeRewardsConfig() -> RipeRewardsConfig: view

interface PriceDesk:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface RipeToken:
    def mint(_to: address, _amount: uint256): nonpayable

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

struct UserDepositLoot:
    ripeStakerLoot: uint256
    ripeVoteLoot: uint256
    ripeGenLoot: uint256

struct RipeRewardsAllocs:
    stakers: uint256
    borrowers: uint256
    voteDepositors: uint256
    genDepositors: uint256
    total: uint256

struct RipeRewardsConfig:
    ripeRewardsAllocs: RipeRewardsAllocs
    ripeRewardsStartBlock: uint256
    ripePerBlock: uint256

struct DepositPointsAllocs:
    stakers: uint256
    stakersTotal: uint256
    voteDepositor: uint256
    voteDepositorTotal: uint256

LEDGER_ID: constant(uint256) = 2 # TODO: make sure this is correct
VAULT_BOOK_ID: constant(uint256) = 3 # TODO: make sure this is correct
CONTROL_ROOM_ID: constant(uint256) = 6 # TODO: make sure this is correct
PRICE_DESK_ID: constant(uint256) = 7 # TODO: make sure this is correct

EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%

# config
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True


#############
# Top Level #
#############


@external
def claimLoot(_user: address, _shouldStake: bool) -> uint256:
    assert staticcall AddyRegistry(ADDY_REGISTRY).isValidAddyAddr(msg.sender) # dev: no perms

    addys: address[4] = self._getAddys()
    ledger: address = addys[0]
    vaultBook: address = addys[1]

    # total loot -- start with borrow loot
    totalRipeForUser: uint256 = self._claimBorrowLoot(_user, addys)

    # now look at deposit loot
    numUserVaults: uint256 = staticcall Ledger(ledger).numUserVaults(_user)
    for i: uint256 in range(1, numUserVaults, bound=max_value(uint256)):
        vaultId: uint256 = staticcall Ledger(ledger).userVaults(_user, i)
        vaultAddr: address = staticcall VaultBook(vaultBook).getVault(vaultId)
        if vaultAddr == empty(address):
            continue
        numUserAssets: uint256 = staticcall Vault(vaultAddr).numUserAssets(_user)
        for y: uint256 in range(1, numUserAssets, bound=max_value(uint256)):
            asset: address = staticcall Vault(vaultAddr).userAssets(_user, y)
            if asset == empty(address):
                continue
            totalRipeForUser += self._claimDepositLoot(_user, vaultId, vaultAddr, asset, addys)

    # mint ripe, then stake or transfer to user
    if totalRipeForUser != 0:
        self._handleRipeMint(_user, totalRipeForUser, _shouldStake)

    return totalRipeForUser


@external
def claimDepositLootOnExit(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
) -> uint256:
    assert staticcall AddyRegistry(ADDY_REGISTRY).isValidAddyAddr(msg.sender) # dev: no perms
    totalRipeForUser: uint256 = self._claimDepositLoot(_user, _vaultId, _vaultAddr, _asset, self._getAddys())
    if totalRipeForUser != 0:
        self._handleRipeMint(_user, totalRipeForUser, True)
    return totalRipeForUser


# view claimable


@view
@external
def getClaimableLoot(_user: address) -> uint256:
    addys: address[4] = self._getAddys()
    ledger: address = addys[0]
    vaultBook: address = addys[1]

    # total loot -- start with borrow loot
    totalRipeForUser: uint256 = self._getClaimableBorrowLoot(_user, addys)

    # now look at deposit loot
    numUserVaults: uint256 = staticcall Ledger(ledger).numUserVaults(_user)
    for i: uint256 in range(1, numUserVaults, bound=max_value(uint256)):
        vaultId: uint256 = staticcall Ledger(ledger).userVaults(_user, i)
        vaultAddr: address = staticcall VaultBook(vaultBook).getVault(vaultId)
        if vaultAddr == empty(address):
            continue
        numUserAssets: uint256 = staticcall Vault(vaultAddr).numUserAssets(_user)
        for y: uint256 in range(1, numUserAssets, bound=max_value(uint256)):
            asset: address = staticcall Vault(vaultAddr).userAssets(_user, y)
            if asset == empty(address):
                continue
            totalRipeForUser += self._getClaimableDepositLoot(_user, vaultId, vaultAddr, asset, addys)

    return totalRipeForUser


##################
# Deposit Points #
##################


# update points


@external
def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address):
    assert staticcall AddyRegistry(ADDY_REGISTRY).isValidAddyAddr(msg.sender) # dev: no perms
    addys: address[4] = self._getAddys()

    # get latest global rewards
    globalRewards: RipeRewards = self._getLatestGlobalRipeRewards(addys)

    # get latest deposit points
    up: UserDepositPoints = empty(UserDepositPoints)
    ap: AssetDepositPoints = empty(AssetDepositPoints)
    gp: GlobalDepositPoints = empty(GlobalDepositPoints)
    up, ap, gp = self._getLatestDepositPoints(_user, _vaultId, _vaultAddr, _asset, globalRewards.lastRewardsBlock, addys)

    # update points
    ledger: address = addys[0]
    extcall Ledger(ledger).setDepositPointsAndRipeRewards(_user, _vaultId, _asset, up, ap, gp, globalRewards)


# global deposit points


@view
@internal
def _getLatestGlobalDepositPoints(
    _globalPoints: GlobalDepositPoints,
    _lastRipeRewardsBlock: uint256,
    _stakersTotalAlloc: uint256,
    _voteDepositorTotalAlloc: uint256,
) -> GlobalDepositPoints:
    globalPoints: GlobalDepositPoints = _globalPoints

    # nothing to do here
    if globalPoints.lastUpdate == 0 or _lastRipeRewardsBlock <= globalPoints.lastUpdate:
        globalPoints.lastUpdate = block.number
        return globalPoints

    # update ripe rewards points
    elapsedBlocks: uint256 = _lastRipeRewardsBlock - globalPoints.lastUpdate
    globalPoints.ripeStakerPoints += _stakersTotalAlloc * elapsedBlocks
    globalPoints.ripeVotePoints += _voteDepositorTotalAlloc * elapsedBlocks
    globalPoints.ripeGenPoints += globalPoints.lastUsdValue * elapsedBlocks

    # Note: will update `lastUsdValue` later in flow (after knowing AssetDepositPoints changes in usd value)

    globalPoints.lastUpdate = block.number
    return globalPoints


# asset deposit points


@view
@internal
def _getLatestAssetDepositPoints(
    _assetPoints: AssetDepositPoints,
    _lastRipeRewardsBlock: uint256,
    _stakersAlloc: uint256,
    _voteDepositorAlloc: uint256,
) -> AssetDepositPoints:
    assetPoints: AssetDepositPoints = _assetPoints

    # balance points - how each user will split rewards for this vault/asset
    elapsedBlocks: uint256 = 0
    if assetPoints.lastUpdate != 0 and block.number > assetPoints.lastUpdate:
        elapsedBlocks = block.number - assetPoints.lastUpdate
        assetPoints.balancePoints += assetPoints.lastBalance * elapsedBlocks

    # nothing else to do here
    if assetPoints.lastUpdate == 0 or _lastRipeRewardsBlock <= assetPoints.lastUpdate:
        assetPoints.lastUpdate = block.number
        return assetPoints

    # update ripe rewards points
    elapsedBlocks = _lastRipeRewardsBlock - assetPoints.lastUpdate
    assetPoints.ripeStakerPoints += _stakersAlloc * elapsedBlocks
    assetPoints.ripeVotePoints += _voteDepositorAlloc * elapsedBlocks
    assetPoints.ripeGenPoints += assetPoints.lastUsdValue * elapsedBlocks

    # Note: will update `lastUsdValue` later in flow

    assetPoints.lastUpdate = block.number
    return assetPoints


# user deposit points


@view
@internal
def _getLatestUserDepositPoints(_userPoints: UserDepositPoints) -> UserDepositPoints:
    userPoints: UserDepositPoints = _userPoints

    # add user balance points
    if userPoints.lastUpdate != 0 and block.number > userPoints.lastUpdate:
        elapsedBlocks: uint256 = block.number - userPoints.lastUpdate
        userPoints.balancePoints += userPoints.lastBalance * elapsedBlocks

    # Note: will update `lastBalance` later in flow (if necessary)

    userPoints.lastUpdate = block.number
    return userPoints


# combined points


@view
@internal
def _getLatestDepositPoints(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _lastRipeRewardsBlock: uint256,
    _addys: address[4],
) -> (UserDepositPoints, AssetDepositPoints, GlobalDepositPoints):
    ledger: address = _addys[0]
    controlRoom: address = _addys[1]
    vaultBook: address = _addys[2]
    priceDesk: address = _addys[3]

    # get data
    p: DepositPointsBundle = staticcall Ledger(ledger).getDepositPointsBundle(_user, _vaultId, _asset)
    a: DepositPointsAllocs = staticcall ControlRoom(controlRoom).getDepositPointsAllocs(_vaultId, _asset) 

    # latest global points
    globalPoints: GlobalDepositPoints = self._getLatestGlobalDepositPoints(p.globalPoints, _lastRipeRewardsBlock, a.stakersTotal, a.voteDepositorTotal)

    # latest asset points
    assetPoints: AssetDepositPoints = self._getLatestAssetDepositPoints(p.assetPoints, _lastRipeRewardsBlock, a.stakers, a.voteDepositor)
    if assetPoints.precision == 0:
        assetPoints.precision = self._getAssetPrecision(_vaultId, _asset, vaultBook)

    # latest asset value (staked assets not eligible for gen deposit rewards)
    newAssetUsdValue: uint256 = 0
    if a.stakers == 0:
        newAssetUsdValue = self._refreshAssetUsdValue(_asset, _vaultAddr, priceDesk)

    # update `lastUsdValue` for global + asset
    if newAssetUsdValue != assetPoints.lastUsdValue:
        globalPoints.lastUsdValue -= assetPoints.lastUsdValue
        globalPoints.lastUsdValue += newAssetUsdValue
        assetPoints.lastUsdValue = newAssetUsdValue

    # nothing else to do here
    if _user == empty(address):
        return empty(UserDepositPoints), assetPoints, globalPoints

    # latest user points
    userPoints: UserDepositPoints = self._getLatestUserDepositPoints(p.userPoints)

    # get user loot share
    userLootShare: uint256 = staticcall Vault(_vaultAddr).getUserLootBoxShare(_user, _asset)
    if userLootShare != 0:
        userLootShare = userLootShare // assetPoints.precision

    # update `lastBalance`
    assetPoints.lastBalance -= userPoints.lastBalance
    assetPoints.lastBalance += userLootShare
    userPoints.lastBalance = userLootShare

    return userPoints, assetPoints, globalPoints


# claim deposit loot


@internal
def _claimDepositLoot(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _addys: address[4],
) -> uint256:
    userRipeRewards: UserDepositLoot = empty(UserDepositLoot)
    up: UserDepositPoints = empty(UserDepositPoints)
    ap: AssetDepositPoints = empty(AssetDepositPoints)
    gp: GlobalDepositPoints = empty(GlobalDepositPoints)
    globalRipeRewards: RipeRewards = empty(RipeRewards)
    userRipeRewards, up, ap, gp, globalRipeRewards = self._getClaimableDepositLootData(_user, _vaultId, _vaultAddr, _asset, _addys)

    totalRipeForUser: uint256 = userRipeRewards.ripeStakerLoot + userRipeRewards.ripeVoteLoot + userRipeRewards.ripeGenLoot
    if totalRipeForUser != 0:
        ledger: address = _addys[0]
        extcall Ledger(ledger).setDepositPointsAndRipeRewards(_user, _vaultId, _asset, up, ap, gp, globalRipeRewards)

    return totalRipeForUser


# claimable deposit loot


@view
@internal
def _getClaimableDepositLootData(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _addys: address[4],
) -> (UserDepositLoot, UserDepositPoints, AssetDepositPoints, GlobalDepositPoints, RipeRewards):

    # need to get this with each iteration because state may have changed (during claim)
    globalRewards: RipeRewards = self._getLatestGlobalRipeRewards(_addys)

    # get latest deposit points
    up: UserDepositPoints = empty(UserDepositPoints)
    ap: AssetDepositPoints = empty(AssetDepositPoints)
    gp: GlobalDepositPoints = empty(GlobalDepositPoints)
    up, ap, gp = self._getLatestDepositPoints(_user, _vaultId, _vaultAddr, _asset, globalRewards.lastRewardsBlock, _addys)

    # user has no points
    if up.balancePoints == 0:
        return empty(UserDepositLoot), up, ap, gp, globalRewards

    # calc user's share
    userShareOfAsset: uint256 = 0
    if ap.balancePoints != 0:
        userShareOfAsset = min(up.balancePoints * HUNDRED_PERCENT // ap.balancePoints, HUNDRED_PERCENT)

    # insufficient user share, may need to wait longer to claim
    if userShareOfAsset == 0:
        return empty(UserDepositLoot), up, ap, gp, globalRewards

    # calc user's share of loot, per category
    userLoot: UserDepositLoot = empty(UserDepositLoot)
    ap.ripeStakerPoints, gp.ripeStakerPoints, globalRewards.stakers, userLoot.ripeStakerLoot = self._calcSpecificLoot(userShareOfAsset, ap.ripeStakerPoints, gp.ripeStakerPoints, globalRewards.stakers)
    ap.ripeVotePoints, gp.ripeVotePoints, globalRewards.voteDepositors, userLoot.ripeVoteLoot = self._calcSpecificLoot(userShareOfAsset, ap.ripeVotePoints, gp.ripeVotePoints, globalRewards.voteDepositors)
    ap.ripeGenPoints, gp.ripeGenPoints, globalRewards.genDepositors, userLoot.ripeGenLoot = self._calcSpecificLoot(userShareOfAsset, ap.ripeGenPoints, gp.ripeGenPoints, globalRewards.genDepositors)

    # only zero out points if they actually received loot -- asset or user may not always have sufficient points (yet) to get loot
    didReceiveLoot: bool = (
        userLoot.ripeStakerLoot != 0 or
        userLoot.ripeVoteLoot != 0 or
        userLoot.ripeGenLoot != 0
    )
    if didReceiveLoot:
        ap.balancePoints -= up.balancePoints # do first
        up.balancePoints = 0

    return userLoot, up, ap, gp, globalRewards


@view
@internal
def _getClaimableDepositLoot(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _addys: address[4],
) -> uint256:
    userRipeRewards: UserDepositLoot = empty(UserDepositLoot)
    up: UserDepositPoints = empty(UserDepositPoints)
    ap: AssetDepositPoints = empty(AssetDepositPoints)
    gp: GlobalDepositPoints = empty(GlobalDepositPoints)
    globalRipeRewards: RipeRewards = empty(RipeRewards)
    userRipeRewards, up, ap, gp, globalRipeRewards = self._getClaimableDepositLootData(_user, _vaultId, _vaultAddr, _asset, _addys)
    return userRipeRewards.ripeStakerLoot + userRipeRewards.ripeVoteLoot + userRipeRewards.ripeGenLoot


@view
@external
def getClaimableDepositLootForAsset(_user: address, _vaultId: uint256, _asset: address) -> uint256:
    addys: address[4] = self._getAddys()
    vaultAddr: address = staticcall VaultBook(addys[2]).getVault(_vaultId)
    return self._getClaimableDepositLoot(_user, _vaultId, vaultAddr, _asset, addys)


# deposit points utils


@view
@internal
def _calcSpecificLoot(
    _userShareOfAsset: uint256,
    _assetPoints: uint256,
    _globalPoints: uint256,
    _rewardsAvailable: uint256,
) -> (uint256, uint256, uint256, uint256):

    # nothing to do here
    if _assetPoints == 0 or _globalPoints == 0 or _rewardsAvailable == 0:
        return _assetPoints, _globalPoints, _rewardsAvailable, 0

    # calc asset rewards
    assetRewards: uint256 = 0
    if _assetPoints * HUNDRED_PERCENT > _globalPoints:
        assetShareOfGlobal: uint256 = min(_assetPoints * HUNDRED_PERCENT // _globalPoints, HUNDRED_PERCENT)
        assetRewards = _rewardsAvailable * assetShareOfGlobal // HUNDRED_PERCENT
    else:
        assetRewards = _rewardsAvailable * _assetPoints // _globalPoints

    # calc user rewards (for asset)
    userRewards: uint256 = assetRewards * _userShareOfAsset // HUNDRED_PERCENT
    if userRewards == 0:
        return _assetPoints, _globalPoints, _rewardsAvailable, 0

    # calc how many points to reduce (from asset and global)
    pointsToReduce: uint256 = 0
    if _assetPoints * _userShareOfAsset > HUNDRED_PERCENT:
        pointsToReduce = _assetPoints * _userShareOfAsset // HUNDRED_PERCENT
    else:
        remainingRewards: uint256 = assetRewards - userRewards
        pointsRemaining: uint256 = _assetPoints
        if _assetPoints * remainingRewards > assetRewards:
            pointsRemaining = _assetPoints * remainingRewards // assetRewards
        pointsToReduce = _assetPoints - pointsRemaining

    if pointsToReduce == 0:
        return _assetPoints, _globalPoints, _rewardsAvailable, 0

    # updated data
    newAssetPoints: uint256 = _assetPoints - pointsToReduce
    newGlobalPoints: uint256 = _globalPoints - pointsToReduce
    newRewardsAvail: uint256 = _rewardsAvailable - userRewards
    return newAssetPoints, newGlobalPoints, newRewardsAvail, userRewards


@view
@internal
def _refreshAssetUsdValue(_asset: address, _vaultAddr: address, _priceDesk: address) -> uint256:
    assetAmount: uint256 = staticcall Vault(_vaultAddr).getTotalAmountForVault(_asset)
    if assetAmount == 0:
        return 0
    newUsdValue: uint256 = staticcall PriceDesk(_priceDesk).getUsdValue(_asset, assetAmount)
    if newUsdValue != 0:
        newUsdValue = newUsdValue // EIGHTEEN_DECIMALS # reduce risk of integer overflow
    return newUsdValue


@view
@internal
def _getAssetPrecision(_vaultId: uint256, _asset: address, _vaultBook: address) -> uint256:
    if staticcall VaultBook(_vaultBook).isNftVault(_vaultId):
        return 1
    decimals: uint256 = convert(staticcall IERC20Detailed(_asset).decimals(), uint256)
    if decimals >= 8: # wbtc has 8 decimals
        return 10 ** (decimals // 2)
    return 10 ** decimals


#################
# Borrower Loot #
#################


# update borrow points


@external
def updateBorrowPoints(_user: address):
    assert staticcall AddyRegistry(ADDY_REGISTRY).isValidAddyAddr(msg.sender) # dev: no perms
    addys: address[4] = self._getAddys()
    ledger: address = addys[0]
    globalRewards: RipeRewards = self._getLatestGlobalRipeRewards(addys)

    up: BorrowPoints = empty(BorrowPoints)
    gp: BorrowPoints = empty(BorrowPoints)
    up, gp = self._getLatestBorrowPoints(_user, globalRewards.lastRewardsBlock, ledger)
    extcall Ledger(ledger).setBorrowPointsAndRipeRewards(_user, up, gp, globalRewards)


# borrow points


@view 
@internal 
def _getLatestGlobalBorrowPoints(_globalPoints: BorrowPoints, _lastRipeRewardsBlock: uint256) -> BorrowPoints:
    globalPoints: BorrowPoints = _globalPoints

    if globalPoints.lastUpdate != 0 and _lastRipeRewardsBlock > globalPoints.lastUpdate:
        newBorrowPoints: uint256 = globalPoints.lastPrincipal * (_lastRipeRewardsBlock - globalPoints.lastUpdate)
        globalPoints.points += newBorrowPoints

    # Note: will update `lastPrincipal` later in flow

    globalPoints.lastUpdate = block.number
    return globalPoints


@view 
@internal 
def _getLatestUserBorrowPoints(_userPoints: BorrowPoints, _lastRipeRewardsBlock: uint256) -> BorrowPoints:
    userPoints: BorrowPoints = _userPoints

    # update borrow points
    if userPoints.lastUpdate != 0 and _lastRipeRewardsBlock > userPoints.lastUpdate:
        elapsedBlocks: uint256 = _lastRipeRewardsBlock - userPoints.lastUpdate
        userPoints.points += userPoints.lastPrincipal * elapsedBlocks

    # Note: will update `lastPrincipal` later in flow (if necessary)

    userPoints.lastUpdate = block.number
    return userPoints


@view 
@internal 
def _getLatestBorrowPoints(_user: address, _lastRipeRewardsBlock: uint256, _ledger: address) -> (BorrowPoints, BorrowPoints):
    p: BorrowPointsBundle = staticcall Ledger(_ledger).getBorrowPointsBundle(_user)
    globalPoints: BorrowPoints = self._getLatestGlobalBorrowPoints(p.globalPoints, _lastRipeRewardsBlock)

    # if no user, return global points
    if _user == empty(address):
        return empty(BorrowPoints), globalPoints
    
    # get user points
    userPoints: BorrowPoints = self._getLatestUserBorrowPoints(p.userPoints, _lastRipeRewardsBlock)

    # normalize user debt -- reduce risk of integer overflow
    userDebt: uint256 = p.userDebtPrincipal
    if userDebt != 0:
        userDebt = userDebt // EIGHTEEN_DECIMALS

    # update `lastPrincipal`
    globalPoints.lastPrincipal -= userPoints.lastPrincipal
    globalPoints.lastPrincipal += userDebt
    userPoints.lastPrincipal = userDebt

    return userPoints, globalPoints


# claim loot


@internal 
def _claimBorrowLoot(_user: address, _addys: address[4]) -> uint256:
    userRipeRewards: uint256 = 0
    up: BorrowPoints = empty(BorrowPoints)
    gp: BorrowPoints = empty(BorrowPoints)
    globalRipeRewards: RipeRewards = empty(RipeRewards)
    userRipeRewards, up, gp, globalRipeRewards = self._getClaimableBorrowLootData(_user, _addys)
    if userRipeRewards != 0:
        ledger: address = _addys[0]
        extcall Ledger(ledger).setBorrowPointsAndRipeRewards(_user, up, gp, globalRipeRewards)
    return userRipeRewards


# claimable loot


@view 
@internal 
def _getClaimableBorrowLootData(_user: address, _addys: address[4]) -> (uint256, BorrowPoints, BorrowPoints, RipeRewards):
    ledger: address = _addys[0]

    # get latest global rewards
    globalRewards: RipeRewards = self._getLatestGlobalRipeRewards(_addys)
    if globalRewards.borrowers == 0:
        return 0, empty(BorrowPoints), empty(BorrowPoints), empty(RipeRewards)

    # get latest borrow points
    up: BorrowPoints = empty(BorrowPoints)
    gp: BorrowPoints = empty(BorrowPoints)
    up, gp = self._getLatestBorrowPoints(_user, globalRewards.lastRewardsBlock, ledger)

    # user has no points
    if up.points == 0:
        return 0, empty(BorrowPoints), empty(BorrowPoints), empty(RipeRewards)

    # calc user's share
    userShare: uint256 = 0
    if gp.points != 0:
        userShare = min(up.points * HUNDRED_PERCENT // gp.points, HUNDRED_PERCENT)

    # insufficient user share, may need to wait longer to claim
    if userShare == 0:
        return 0, empty(BorrowPoints), empty(BorrowPoints), empty(RipeRewards)

    # calc borrower rewards
    userRipeRewards: uint256 = globalRewards.borrowers * userShare // HUNDRED_PERCENT

    # update structs
    if userRipeRewards != 0:
        globalRewards.borrowers -= userRipeRewards
        gp.points -= up.points # do first
        up.points = 0

    return userRipeRewards, up, gp, globalRewards


@view
@internal 
def _getClaimableBorrowLoot(_user: address, _addys: address[4]) -> uint256:
    userRipeRewards: uint256 = 0
    up: BorrowPoints = empty(BorrowPoints)
    gp: BorrowPoints = empty(BorrowPoints)
    globalRipeRewards: RipeRewards = empty(RipeRewards)
    userRipeRewards, up, gp, globalRipeRewards = self._getClaimableBorrowLootData(_user, _addys)
    return userRipeRewards


@view
@external 
def getClaimableBorrowLoot(_user: address) -> uint256:
    return self._getClaimableBorrowLoot(_user, self._getAddys())


################
# Ripe Rewards #
################


# update ripe rewards


@external
def updateRipeRewards():
    assert staticcall AddyRegistry(ADDY_REGISTRY).isValidAddyAddr(msg.sender) # dev: no perms
    addys: address[4] = self._getAddys()
    ripeRewards: RipeRewards = self._getLatestGlobalRipeRewards(addys)
    ledger: address = addys[0]
    extcall Ledger(ledger).setRipeRewards(ripeRewards)


# get latest global ripe rewards


@view
@external
def getLatestGlobalRipeRewards() -> RipeRewards:
    return self._getLatestGlobalRipeRewards(self._getAddys())


@view
@internal
def _getLatestGlobalRipeRewards(_addys: address[4]) -> RipeRewards:
    ledger: address = _addys[0]
    controlRoom: address = _addys[1]

    # get data
    b: RipeRewardsBundle = staticcall Ledger(ledger).getRipeRewardsBundle()
    globalRewards: RipeRewards = b.ripeRewards
    globalRewards.newRipeRewards = 0 # important to reset!

    # get rewards config
    config: RipeRewardsConfig = staticcall ControlRoom(controlRoom).getRipeRewardsConfig()

    # use most recent time between `lastUpdate` and `ripeRewardsStartBlock`
    lastUpdateAdjusted: uint256 = max(globalRewards.lastUpdate, config.ripeRewardsStartBlock)

    newRipeDistro: uint256 = 0
    if lastUpdateAdjusted != 0 and block.number > lastUpdateAdjusted:
        elapsedBlocks: uint256 = block.number - lastUpdateAdjusted
        newRipeDistro = min(elapsedBlocks * config.ripePerBlock, b.ripeAvailForRewards)

    # nothing to do here
    if newRipeDistro == 0:
        globalRewards.lastUpdate = block.number
        return globalRewards

    # allocate ripe rewards to global buckets
    if config.ripeRewardsAllocs.total != 0:
        globalRewards.stakers += newRipeDistro * config.ripeRewardsAllocs.stakers // config.ripeRewardsAllocs.total
        globalRewards.borrowers += newRipeDistro * config.ripeRewardsAllocs.borrowers // config.ripeRewardsAllocs.total
        globalRewards.voteDepositors += newRipeDistro * config.ripeRewardsAllocs.voteDepositors // config.ripeRewardsAllocs.total
        globalRewards.genDepositors += newRipeDistro * config.ripeRewardsAllocs.genDepositors // config.ripeRewardsAllocs.total

        # rewards were distro'd, save important data
        globalRewards.newRipeRewards = newRipeDistro
        globalRewards.lastRewardsBlock = block.number

    globalRewards.lastUpdate = block.number
    return globalRewards


#########
# Utils #
#########


@internal
def _handleRipeMint(_user: address, _amount: uint256, _shouldStake: bool):
    ripeToken: address = staticcall AddyRegistry(ADDY_REGISTRY).ripeToken()
    extcall RipeToken(ripeToken).mint(_user, _amount)

    # TODO: handle staking


@view
@internal
def _getAddys() -> address[4]:
    ar: address = ADDY_REGISTRY
    ledger: address = staticcall AddyRegistry(ar).getAddy(LEDGER_ID)
    controlRoom: address = staticcall AddyRegistry(ar).getAddy(CONTROL_ROOM_ID)
    vaultBook: address = staticcall AddyRegistry(ar).getAddy(VAULT_BOOK_ID)
    priceDesk: address = staticcall AddyRegistry(ar).getAddy(PRICE_DESK_ID)
    return [ledger, controlRoom, vaultBook, priceDesk]