#       .----------------.  .----------------.  .----------------.  .----------------.  .----------------.  .----------------.  .----------------. 
#      | .--------------. || .--------------. || .--------------. || .--------------. || .--------------. || .--------------. || .--------------. |
#      | |   _____      | || |     ____     | || |     ____     | || |  _________   | || |   ______     | || |     ____     | || |  ____  ____  | |
#      | |  |_   _|     | || |   .'    `.   | || |   .'    `.   | || | |  _   _  |  | || |  |_   _ \    | || |   .'    `.   | || | |_  _||_  _| | |
#      | |    | |       | || |  /  .--.  \  | || |  /  .--.  \  | || | |_/ | | \_|  | || |    | |_) |   | || |  /  .--.  \  | || |   \ \  / /   | |
#      | |    | |   _   | || |  | |    | |  | || |  | |    | |  | || |     | |      | || |    |  __'.   | || |  | |    | |  | || |    > `' <    | |
#      | |   _| |__/ |  | || |  \  `--'  /  | || |  \  `--'  /  | || |    _| |_     | || |   _| |__) |  | || |  \  `--'  /  | || |  _/ /'`\ \_  | |
#      | |  |________|  | || |   `.____.'   | || |   `.____.'   | || |   |_____|    | || |  |_______/   | || |   `.____.'   | || | |____||____| | |
#      | |              | || |              | || |              | || |              | || |              | || |              | || |              | |
#      | '--------------' || '--------------' || '--------------' || '--------------' || '--------------' || '--------------' || '--------------' |
#       '----------------'  '----------------'  '----------------'  '----------------'  '----------------'  '----------------'  '----------------' 
#
#     ╔════════════════════════════════════════════════╗
#     ║  ** Lootbox **                                 ║
#     ║  Where all the Ripe token rewards logic lives  ║
#     ╚════════════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

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

from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed

interface Ledger:
    def setDepositPointsAndRipeRewards(_user: address, _vaultId: uint256, _asset: address, _userPoints: UserDepositPoints, _assetPoints: AssetDepositPoints, _globalPoints: GlobalDepositPoints, _ripeRewards: RipeRewards): nonpayable
    def setBorrowPointsAndRipeRewards(_user: address, _userPoints: BorrowPoints, _globalPoints: BorrowPoints, _ripeRewards: RipeRewards): nonpayable
    def getDepositPointsBundle(_user: address, _vaultId: uint256, _asset: address) -> DepositPointsBundle: view
    def removeVaultFromUser(_user: address, _vaultId: uint256): nonpayable
    def getBorrowPointsBundle(_user: address) -> BorrowPointsBundle: view
    def userVaults(_user: address, _index: uint256) -> uint256: view
    def setRipeRewards(_ripeRewards: RipeRewards): nonpayable
    def getRipeRewardsBundle() -> RipeRewardsBundle: view
    def numUserVaults(_user: address) -> uint256: view

interface MissionControl:
    def getClaimLootConfig(_user: address, _caller: address, _ripeToken: address) -> ClaimLootConfig: view
    def getDepositPointsConfig(_asset: address) -> DepositPointsConfig: view
    def getRewardsConfig() -> RewardsConfig: view

interface Teller:
    def depositFromTrusted(_user: address, _vaultId: uint256, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def isUnderscoreWalletOwner(_user: address, _caller: address, _mc: address = empty(address)) -> bool: view

interface PriceDesk:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface RipeToken:
    def mint(_to: address, _amount: uint256): nonpayable

interface VaultBook:
    def getAddr(_vaultId: uint256) -> address: view

struct RipeRewards:
    borrowers: uint256
    stakers: uint256
    voters: uint256
    genDepositors: uint256
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

struct UserDepositLoot:
    ripeStakerLoot: uint256
    ripeVoteLoot: uint256
    ripeGenLoot: uint256

struct RewardsConfig:
    arePointsEnabled: bool
    ripePerBlock: uint256
    borrowersAlloc: uint256
    stakersAlloc: uint256
    votersAlloc: uint256
    genDepositorsAlloc: uint256
    stakersPointsAllocTotal: uint256
    voterPointsAllocTotal: uint256

struct DepositPointsConfig:
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    isNft: bool

struct ClaimLootConfig:
    canClaimLoot: bool
    canClaimLootForUser: bool
    autoStakeRatio: uint256
    rewardsLockDuration: uint256

event DepositLootClaimed:
    user: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    ripeStakerLoot: uint256
    ripeVoteLoot: uint256
    ripeGenLoot: uint256

event BorrowLootClaimed:
    user: indexed(address)
    ripeAmount: uint256

EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_ASSETS_TO_CLEAN: constant(uint256) = 20
MAX_VAULTS_TO_CLEAN: constant(uint256) = 10
MAX_CLAIM_USERS: constant(uint256) = 25
RIPE_GOV_VAULT_ID: constant(uint256) = 2


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, True) # can mint ripe only


##############
# Claim Loot #
##############


@external
def claimLootForUser(
    _user: address,
    _caller: address,
    _shouldStake: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)
    isSwitchboard: bool = addys._isSwitchboardAddr(msg.sender)
    return self._claimLoot(_user, _caller, _shouldStake, not isSwitchboard, a)


@external
def claimLootForManyUsers(
    _users: DynArray[address, MAX_CLAIM_USERS],
    _caller: address,
    _shouldStake: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)
    isSwitchboard: bool = addys._isSwitchboardAddr(msg.sender)

    totalRipeForUsers: uint256 = 0
    for u: address in _users:
        totalRipeForUsers += self._claimLoot(u, _caller, _shouldStake, not isSwitchboard, a)
    return totalRipeForUsers


# core -- gets borrow loot AND deposit loot


@internal
def _claimLoot(
    _user: address,
    _caller: address,
    _shouldStake: bool,
    _shouldCheckCaller: bool,
    _a: addys.Addys,
) -> uint256:

    # nothing to do here
    if _user == empty(address):
        return 0

    # check if caller can claim for user
    config: ClaimLootConfig = staticcall MissionControl(_a.missionControl).getClaimLootConfig(_user, _caller, _a.ripeToken)
    assert config.canClaimLoot # dev: loot claims disabled

    # can others claim for user
    if _shouldCheckCaller:
        if _user != _caller and not config.canClaimLootForUser:
            assert staticcall Teller(_a.teller).isUnderscoreWalletOwner(_user, _caller, _a.missionControl) # dev: cannot claim for user

    # total loot -- start with borrow loot
    totalRipeForUser: uint256 = self._claimBorrowLoot(_user, _a)

    # now look at deposit loot
    vaultsToRemove: DynArray[uint256, MAX_VAULTS_TO_CLEAN] = []
    numUserVaults: uint256 = staticcall Ledger(_a.ledger).numUserVaults(_user)

    # if no vaults, return 0
    if numUserVaults == 0:
        return totalRipeForUser

    for i: uint256 in range(1, numUserVaults, bound=max_value(uint256)):
        vaultId: uint256 = staticcall Ledger(_a.ledger).userVaults(_user, i)
        vaultAddr: address = staticcall VaultBook(_a.vaultBook).getAddr(vaultId)
        if vaultAddr == empty(address):
            continue

        assetsToRemove: DynArray[address, MAX_ASSETS_TO_CLEAN] = []
        numUserAssets: uint256 = staticcall Vault(vaultAddr).numUserAssets(_user)
        for y: uint256 in range(1, numUserAssets, bound=max_value(uint256)):
            asset: address = empty(address)
            hasBalance: bool = False
            asset, hasBalance = staticcall Vault(vaultAddr).getUserAssetAtIndexAndHasBalance(_user, y)
            if asset == empty(address):
                continue

            # save to clean up later
            if not hasBalance and len(assetsToRemove) < MAX_ASSETS_TO_CLEAN:
                assetsToRemove.append(asset)

            # claim loot
            totalRipeForUser += self._claimDepositLoot(_user, vaultId, vaultAddr, asset, not hasBalance, _a)

        # clean up user assets (storage optimization)
        stillInVault: bool = self._cleanUpUserAssets(_user, vaultAddr, assetsToRemove)
        if not stillInVault and len(vaultsToRemove) < MAX_VAULTS_TO_CLEAN:
            vaultsToRemove.append(vaultId)

    # clean up user vaults (storage optimization)
    self._cleanUpUserVaults(_user, vaultsToRemove, _a.ledger)

    # mint ripe, then stake or transfer to user
    if totalRipeForUser != 0:
        self._handleRipeMint(_user, totalRipeForUser, _shouldStake, config, _a)

    return totalRipeForUser


# view / helper


@view
@external
def getClaimableLoot(_user: address) -> uint256:
    a: addys.Addys = addys._getAddys()

    # total loot -- start with borrow loot
    totalRipeForUser: uint256 = self._getClaimableBorrowLoot(_user, a)

    # now look at deposit loot
    numUserVaults: uint256 = staticcall Ledger(a.ledger).numUserVaults(_user)
    if numUserVaults == 0:
        return totalRipeForUser

    for i: uint256 in range(1, numUserVaults, bound=max_value(uint256)):
        vaultId: uint256 = staticcall Ledger(a.ledger).userVaults(_user, i)
        vaultAddr: address = staticcall VaultBook(a.vaultBook).getAddr(vaultId)
        if vaultAddr == empty(address):
            continue
        numUserAssets: uint256 = staticcall Vault(vaultAddr).numUserAssets(_user)
        for y: uint256 in range(1, numUserAssets, bound=max_value(uint256)):
            asset: address = staticcall Vault(vaultAddr).userAssets(_user, y)
            if asset == empty(address):
                continue
            totalRipeForUser += self._getClaimableDepositLootForAsset(_user, vaultId, vaultAddr, asset, a)

    return totalRipeForUser


##############################
# Claim Loot - Deposit Asset #
##############################


# claims


@external
def claimDepositLootForAsset(_user: address, _vaultId: uint256, _asset: address) -> uint256:
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    vaultAddr: address = staticcall VaultBook(a.vaultBook).getAddr(_vaultId)
    totalRipeForUser: uint256 = self._claimDepositLoot(_user, _vaultId, vaultAddr, _asset, False, a)
    if totalRipeForUser != 0:
        config: ClaimLootConfig = staticcall MissionControl(a.missionControl).getClaimLootConfig(_user, _user, a.ripeToken)
        self._handleRipeMint(_user, totalRipeForUser, False, config, a)
    return totalRipeForUser


@internal
def _claimDepositLoot(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _shouldFlush: bool,
    _a: addys.Addys,
) -> uint256:
    userRipeRewards: UserDepositLoot = empty(UserDepositLoot)
    up: UserDepositPoints = empty(UserDepositPoints)
    ap: AssetDepositPoints = empty(AssetDepositPoints)
    gp: GlobalDepositPoints = empty(GlobalDepositPoints)
    globalRipeRewards: RipeRewards = empty(RipeRewards)
    userRipeRewards, up, ap, gp, globalRipeRewards = self._getDepositLootData(_user, _vaultId, _vaultAddr, _asset, _shouldFlush, _a)

    totalRipeForUser: uint256 = userRipeRewards.ripeStakerLoot + userRipeRewards.ripeVoteLoot + userRipeRewards.ripeGenLoot
    extcall Ledger(_a.ledger).setDepositPointsAndRipeRewards(_user, _vaultId, _asset, up, ap, gp, globalRipeRewards)
    if totalRipeForUser != 0:
        log DepositLootClaimed(user=_user, vaultId=_vaultId, asset=_asset, ripeStakerLoot=userRipeRewards.ripeStakerLoot, ripeVoteLoot=userRipeRewards.ripeVoteLoot, ripeGenLoot=userRipeRewards.ripeGenLoot)
    return totalRipeForUser


# core logic (claimable loot for asset)


@view
@internal
def _getDepositLootData(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _shouldFlush: bool,
    _a: addys.Addys,
) -> (UserDepositLoot, UserDepositPoints, AssetDepositPoints, GlobalDepositPoints, RipeRewards):

    # need to get this with each iteration because state may have changed (during claim)
    config: RewardsConfig = staticcall MissionControl(_a.missionControl).getRewardsConfig()
    globalRewards: RipeRewards = self._getLatestGlobalRipeRewards(config, _a)

    # get latest deposit points
    up: UserDepositPoints = empty(UserDepositPoints)
    ap: AssetDepositPoints = empty(AssetDepositPoints)
    gp: GlobalDepositPoints = empty(GlobalDepositPoints)
    up, ap, gp = self._getLatestDepositPoints(_user, _vaultId, _vaultAddr, _asset, config, _a)

    # user has no points
    if up.balancePoints == 0:
        return empty(UserDepositLoot), up, ap, gp, globalRewards

    # calc user's share
    userShareOfAsset: uint256 = 0
    if ap.balancePoints != 0:
        userShareOfAsset = min(up.balancePoints * HUNDRED_PERCENT // ap.balancePoints, HUNDRED_PERCENT)

    # insufficient user share, may need to wait longer to claim
    if userShareOfAsset == 0:
        if _shouldFlush:
            up, ap = self._flushDepositPoints(up, ap)
        return empty(UserDepositLoot), up, ap, gp, globalRewards

    # calc user's share of loot, per category
    userLoot: UserDepositLoot = empty(UserDepositLoot)
    ap.ripeStakerPoints, gp.ripeStakerPoints, globalRewards.stakers, userLoot.ripeStakerLoot = self._calcSpecificLoot(userShareOfAsset, ap.ripeStakerPoints, gp.ripeStakerPoints, globalRewards.stakers)
    ap.ripeVotePoints, gp.ripeVotePoints, globalRewards.voters, userLoot.ripeVoteLoot = self._calcSpecificLoot(userShareOfAsset, ap.ripeVotePoints, gp.ripeVotePoints, globalRewards.voters)
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


# helper / views


@view
@external
def getClaimableDepositLootForAsset(_user: address, _vaultId: uint256, _asset: address) -> uint256:
    a: addys.Addys = addys._getAddys()
    vaultAddr: address = staticcall VaultBook(a.vaultBook).getAddr(_vaultId)
    return self._getClaimableDepositLootForAsset(_user, _vaultId, vaultAddr, _asset, a)


@view
@internal
def _getClaimableDepositLootForAsset(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _a: addys.Addys,
) -> uint256:
    userRipeRewards: UserDepositLoot = empty(UserDepositLoot)
    up: UserDepositPoints = empty(UserDepositPoints)
    ap: AssetDepositPoints = empty(AssetDepositPoints)
    gp: GlobalDepositPoints = empty(GlobalDepositPoints)
    globalRipeRewards: RipeRewards = empty(RipeRewards)
    userRipeRewards, up, ap, gp, globalRipeRewards = self._getDepositLootData(_user, _vaultId, _vaultAddr, _asset, False, _a)
    return userRipeRewards.ripeStakerLoot + userRipeRewards.ripeVoteLoot + userRipeRewards.ripeGenLoot


# claim utils


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
def _flushDepositPoints(_userPoints: UserDepositPoints, _assetPoints: AssetDepositPoints) -> (UserDepositPoints, AssetDepositPoints):
    up: UserDepositPoints = _userPoints
    ap: AssetDepositPoints = _assetPoints
    ap.balancePoints -= up.balancePoints
    up.balancePoints = 0
    return up, ap


##################
# Deposit Points #
##################


# update points


@external
def updateDepositPoints(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _a: addys.Addys = empty(addys.Addys),
):
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    # get latest global rewards
    config: RewardsConfig = staticcall MissionControl(a.missionControl).getRewardsConfig()
    globalRewards: RipeRewards = self._getLatestGlobalRipeRewards(config, a)

    # get latest deposit points
    up: UserDepositPoints = empty(UserDepositPoints)
    ap: AssetDepositPoints = empty(AssetDepositPoints)
    gp: GlobalDepositPoints = empty(GlobalDepositPoints)
    up, ap, gp = self._getLatestDepositPoints(_user, _vaultId, _vaultAddr, _asset, config, a)

    # update points
    extcall Ledger(a.ledger).setDepositPointsAndRipeRewards(_user, _vaultId, _asset, up, ap, gp, globalRewards)


# global deposit points


@view
@internal
def _getLatestGlobalDepositPoints(
    _globalPoints: GlobalDepositPoints,
    _arePointsEnabled: bool,
    _stakersTotalAlloc: uint256,
    _voteDepositorTotalAlloc: uint256,
) -> GlobalDepositPoints:
    globalPoints: GlobalDepositPoints = _globalPoints

    # elapsed blocks
    elapsedBlocks: uint256 = 0
    if globalPoints.lastUpdate != 0 and block.number > globalPoints.lastUpdate:
        elapsedBlocks = block.number - globalPoints.lastUpdate

    # update last update
    globalPoints.lastUpdate = block.number

    # nothing to do here
    if not _arePointsEnabled or elapsedBlocks == 0:
        return globalPoints

    # update ripe rewards points
    globalPoints.ripeStakerPoints += _stakersTotalAlloc * elapsedBlocks
    globalPoints.ripeVotePoints += _voteDepositorTotalAlloc * elapsedBlocks
    globalPoints.ripeGenPoints += globalPoints.lastUsdValue * elapsedBlocks

    # Note: will update `lastUsdValue` later in flow (after knowing AssetDepositPoints changes in usd value)

    return globalPoints


# asset deposit points


@view
@internal
def _getLatestAssetDepositPoints(
    _assetPoints: AssetDepositPoints,
    _arePointsEnabled: bool,
    _stakersAlloc: uint256,
    _voteDepositorAlloc: uint256,
) -> AssetDepositPoints:
    assetPoints: AssetDepositPoints = _assetPoints

    # elapsed blocks
    elapsedBlocks: uint256 = 0
    if assetPoints.lastUpdate != 0 and block.number > assetPoints.lastUpdate:
        elapsedBlocks = block.number - assetPoints.lastUpdate

    # update last update
    assetPoints.lastUpdate = block.number

    # nothing to do here
    if not _arePointsEnabled or elapsedBlocks == 0:
        return assetPoints

    # update ripe rewards points
    assetPoints.ripeStakerPoints += _stakersAlloc * elapsedBlocks
    assetPoints.ripeVotePoints += _voteDepositorAlloc * elapsedBlocks
    assetPoints.ripeGenPoints += assetPoints.lastUsdValue * elapsedBlocks

    # balance points - how each user will split rewards for this vault/asset
    assetPoints.balancePoints += assetPoints.lastBalance * elapsedBlocks

    # Note: will update `lastUsdValue` later in flow

    return assetPoints


# user deposit points


@view
@internal
def _getLatestUserDepositPoints(
    _userPoints: UserDepositPoints,
    _arePointsEnabled: bool,
) -> UserDepositPoints:
    userPoints: UserDepositPoints = _userPoints

    # elapsed blocks
    elapsedBlocks: uint256 = 0
    if userPoints.lastUpdate != 0 and block.number > userPoints.lastUpdate:
        elapsedBlocks = block.number - userPoints.lastUpdate

    # update last update
    userPoints.lastUpdate = block.number

    # nothing to do here
    if not _arePointsEnabled or elapsedBlocks == 0:
        return userPoints

    # add user balance points
    userPoints.balancePoints += userPoints.lastBalance * elapsedBlocks

    # Note: will update `lastBalance` later in flow (if necessary)

    return userPoints


# combined points


@view
@external
def getLatestDepositPoints(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _a: addys.Addys = empty(addys.Addys),
) -> (UserDepositPoints, AssetDepositPoints, GlobalDepositPoints):
    a: addys.Addys = addys._getAddys(_a)
    c: RewardsConfig = staticcall MissionControl(a.missionControl).getRewardsConfig()
    vaultAddr: address = staticcall VaultBook(a.vaultBook).getAddr(_vaultId)
    return self._getLatestDepositPoints(_user, _vaultId, vaultAddr, _asset, c, a)


@view
@internal
def _getLatestDepositPoints(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _c: RewardsConfig,
    _a: addys.Addys,
) -> (UserDepositPoints, AssetDepositPoints, GlobalDepositPoints):
    p: DepositPointsBundle = staticcall Ledger(_a.ledger).getDepositPointsBundle(_user, _vaultId, _asset)

    # latest global points
    globalPoints: GlobalDepositPoints = self._getLatestGlobalDepositPoints(p.globalPoints, _c.arePointsEnabled, _c.stakersPointsAllocTotal, _c.voterPointsAllocTotal)

    # latest asset points
    assetConfig: DepositPointsConfig = staticcall MissionControl(_a.missionControl).getDepositPointsConfig(_asset) 
    assetPoints: AssetDepositPoints = self._getLatestAssetDepositPoints(p.assetPoints, _c.arePointsEnabled, assetConfig.stakersPointsAlloc, assetConfig.voterPointsAlloc)
    if assetPoints.precision == 0:
        assetPoints.precision = self._getAssetPrecision(assetConfig.isNft, _asset)

    # latest asset value (staked assets not eligible for gen deposit rewards)
    newAssetUsdValue: uint256 = 0
    if assetConfig.stakersPointsAlloc == 0:
        newAssetUsdValue = self._refreshAssetUsdValue(_asset, _vaultAddr, _a.priceDesk)

    # update `lastUsdValue` for global + asset
    if newAssetUsdValue != assetPoints.lastUsdValue:
        globalPoints.lastUsdValue -= assetPoints.lastUsdValue
        globalPoints.lastUsdValue += newAssetUsdValue
        assetPoints.lastUsdValue = newAssetUsdValue

    # nothing else to do here
    if _user == empty(address):
        return empty(UserDepositPoints), assetPoints, globalPoints

    # latest user points
    userPoints: UserDepositPoints = self._getLatestUserDepositPoints(p.userPoints, _c.arePointsEnabled)

    # get user loot share
    userLootShare: uint256 = staticcall Vault(_vaultAddr).getUserLootBoxShare(_user, _asset)
    if userLootShare != 0:
        userLootShare = userLootShare // assetPoints.precision

    # update `lastBalance`
    assetPoints.lastBalance -= userPoints.lastBalance
    assetPoints.lastBalance += userLootShare
    userPoints.lastBalance = userLootShare

    return userPoints, assetPoints, globalPoints


# utils


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
def _getAssetPrecision(_isNft: bool, _asset: address) -> uint256:
    if _isNft:
        return 1
    decimals: uint256 = convert(staticcall IERC20Detailed(_asset).decimals(), uint256)
    if decimals >= 8: # wbtc has 8 decimals
        return 10 ** (decimals // 2)
    return 10 ** decimals


##########################
# Borrower Loot - Points #
##########################


# update borrow points


@external
def updateBorrowPoints(_user: address, _a: addys.Addys = empty(addys.Addys)):
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    config: RewardsConfig = staticcall MissionControl(a.missionControl).getRewardsConfig()
    globalRewards: RipeRewards = self._getLatestGlobalRipeRewards(config, a)
    up: BorrowPoints = empty(BorrowPoints)
    gp: BorrowPoints = empty(BorrowPoints)
    up, gp = self._getLatestBorrowPoints(_user, config.arePointsEnabled, a.ledger)
    extcall Ledger(a.ledger).setBorrowPointsAndRipeRewards(_user, up, gp, globalRewards)


# borrow points


@view 
@internal 
def _getLatestGlobalBorrowPoints(_globalPoints: BorrowPoints, _arePointsEnabled: bool) -> BorrowPoints:
    globalPoints: BorrowPoints = _globalPoints

    # elapsed blocks
    elapsedBlocks: uint256 = 0
    if globalPoints.lastUpdate != 0 and block.number > globalPoints.lastUpdate:
        elapsedBlocks = block.number - globalPoints.lastUpdate

    # update last update
    globalPoints.lastUpdate = block.number

    # nothing to do here
    if not _arePointsEnabled or elapsedBlocks == 0:
        return globalPoints

    # update borrow points
    globalPoints.points += globalPoints.lastPrincipal * elapsedBlocks

    # Note: will update `lastPrincipal` later in flow

    return globalPoints


@view 
@internal 
def _getLatestUserBorrowPoints(_userPoints: BorrowPoints, _arePointsEnabled: bool) -> BorrowPoints:
    userPoints: BorrowPoints = _userPoints

    # elapsed blocks
    elapsedBlocks: uint256 = 0
    if userPoints.lastUpdate != 0 and block.number > userPoints.lastUpdate:
        elapsedBlocks = block.number - userPoints.lastUpdate

    # update last update
    userPoints.lastUpdate = block.number

    # nothing to do here
    if not _arePointsEnabled or elapsedBlocks == 0:
        return userPoints

    # update borrow points
    userPoints.points += userPoints.lastPrincipal * elapsedBlocks

    # Note: will update `lastPrincipal` later in flow (if necessary)

    return userPoints


@view 
@internal 
def _getLatestBorrowPoints(
    _user: address,
    _arePointsEnabled: bool,
    _ledger: address,
) -> (BorrowPoints, BorrowPoints):
    p: BorrowPointsBundle = staticcall Ledger(_ledger).getBorrowPointsBundle(_user)
    
    # global points
    globalPoints: BorrowPoints = self._getLatestGlobalBorrowPoints(p.globalPoints, _arePointsEnabled)

    # if no user, return global points
    if _user == empty(address):
        return empty(BorrowPoints), globalPoints
    
    # user points
    userPoints: BorrowPoints = self._getLatestUserBorrowPoints(p.userPoints, _arePointsEnabled)

    # normalize user debt -- reduce risk of integer overflow
    userDebt: uint256 = p.userDebtPrincipal
    if userDebt != 0:
        userDebt = userDebt // EIGHTEEN_DECIMALS

    # update `lastPrincipal`
    globalPoints.lastPrincipal -= userPoints.lastPrincipal
    globalPoints.lastPrincipal += userDebt
    userPoints.lastPrincipal = userDebt

    return userPoints, globalPoints


##########################
# Borrower Loot - Claims #
##########################


@external
def claimBorrowLoot(_user: address) -> uint256:
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    totalRipeForUser: uint256 = self._claimBorrowLoot(_user, a)
    if totalRipeForUser != 0:
        config: ClaimLootConfig = staticcall MissionControl(a.missionControl).getClaimLootConfig(_user, _user, a.ripeToken)
        self._handleRipeMint(_user, totalRipeForUser, False, config, a)
    return totalRipeForUser


@internal 
def _claimBorrowLoot(_user: address, _a: addys.Addys) -> uint256:
    userRipeRewards: uint256 = 0
    up: BorrowPoints = empty(BorrowPoints)
    gp: BorrowPoints = empty(BorrowPoints)
    globalRipeRewards: RipeRewards = empty(RipeRewards)
    userRipeRewards, up, gp, globalRipeRewards = self._getClaimableBorrowLootData(_user, _a)
    extcall Ledger(_a.ledger).setBorrowPointsAndRipeRewards(_user, up, gp, globalRipeRewards)
    if userRipeRewards != 0:
        log BorrowLootClaimed(user=_user, ripeAmount=userRipeRewards)
    return userRipeRewards


# claimable loot


@view 
@internal 
def _getClaimableBorrowLootData(_user: address, _a: addys.Addys) -> (uint256, BorrowPoints, BorrowPoints, RipeRewards):
    config: RewardsConfig = staticcall MissionControl(_a.missionControl).getRewardsConfig()
    globalRewards: RipeRewards = self._getLatestGlobalRipeRewards(config, _a)

    # latest borrow points
    up: BorrowPoints = empty(BorrowPoints)
    gp: BorrowPoints = empty(BorrowPoints)
    up, gp = self._getLatestBorrowPoints(_user, config.arePointsEnabled, _a.ledger)

    # calc user's share
    userShare: uint256 = 0
    if gp.points != 0:
        userShare = min(up.points * HUNDRED_PERCENT // gp.points, HUNDRED_PERCENT)

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
def _getClaimableBorrowLoot(_user: address, _a: addys.Addys) -> uint256:
    userRipeRewards: uint256 = 0
    up: BorrowPoints = empty(BorrowPoints)
    gp: BorrowPoints = empty(BorrowPoints)
    globalRipeRewards: RipeRewards = empty(RipeRewards)
    userRipeRewards, up, gp, globalRipeRewards = self._getClaimableBorrowLootData(_user, _a)
    return userRipeRewards


@view
@external 
def getClaimableBorrowLoot(_user: address) -> uint256:
    return self._getClaimableBorrowLoot(_user, addys._getAddys())


################
# Ripe Rewards #
################


# update ripe rewards


@external
def updateRipeRewards(_a: addys.Addys = empty(addys.Addys)) -> RipeRewards:
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)
    config: RewardsConfig = staticcall MissionControl(a.missionControl).getRewardsConfig()
    ripeRewards: RipeRewards = self._getLatestGlobalRipeRewards(config, a)
    extcall Ledger(a.ledger).setRipeRewards(ripeRewards)
    return ripeRewards


# get latest global ripe rewards


@view
@external
def getLatestGlobalRipeRewards() -> RipeRewards:
    a: addys.Addys = addys._getAddys()
    config: RewardsConfig = staticcall MissionControl(a.missionControl).getRewardsConfig()
    return self._getLatestGlobalRipeRewards(config, a)


@view
@internal
def _getLatestGlobalRipeRewards(_config: RewardsConfig, _a: addys.Addys) -> RipeRewards:
    b: RipeRewardsBundle = staticcall Ledger(_a.ledger).getRipeRewardsBundle()
    rewards: RipeRewards = b.ripeRewards
    rewards.newRipeRewards = 0 # important to reset!

    # elapsed blocks
    elapsedBlocks: uint256 = 0
    if rewards.lastUpdate != 0 and block.number > rewards.lastUpdate:
        elapsedBlocks = block.number - rewards.lastUpdate

    # update last update
    rewards.lastUpdate = block.number

    # nothing to do here
    if elapsedBlocks == 0 or _config.ripePerBlock == 0 or b.ripeAvailForRewards == 0:
        return rewards

    # new Ripe rewards
    newRipeDistro: uint256 = min(elapsedBlocks * _config.ripePerBlock, b.ripeAvailForRewards)

    # allocate ripe rewards to global buckets
    total: uint256 = _config.borrowersAlloc + _config.stakersAlloc + _config.votersAlloc + _config.genDepositorsAlloc
    if total != 0:
        rewards.borrowers += newRipeDistro * _config.borrowersAlloc // total
        rewards.stakers += newRipeDistro * _config.stakersAlloc // total
        rewards.voters += newRipeDistro * _config.votersAlloc // total
        rewards.genDepositors += newRipeDistro * _config.genDepositorsAlloc // total

        # rewards were distro'd, save important data
        rewards.newRipeRewards = newRipeDistro

    return rewards


#########
# Utils #
#########


# handle ripe mint


@internal
def _handleRipeMint(
    _user: address,
    _amount: uint256,
    _shouldStake: bool,
    _config: ClaimLootConfig,
    _a: addys.Addys,
):
    # if no auto stake, just mint to user
    if not _shouldStake and _config.autoStakeRatio == 0:
        extcall RipeToken(_a.ripeToken).mint(_user, _amount)
        return

    # mint ripe tokens here
    extcall RipeToken(_a.ripeToken).mint(self, _amount)

    # finalize amounts
    amountToStake: uint256 = _amount
    amountToSend: uint256 = 0
    if not _shouldStake:
        amountToStake = min(_amount * _config.autoStakeRatio // HUNDRED_PERCENT, _amount)
        amountToSend = _amount - amountToStake

    # stake ripe tokens
    if amountToStake != 0:
        assert extcall IERC20(_a.ripeToken).approve(_a.teller, amountToStake, default_return_value=True) # dev: ripe approval failed
        extcall Teller(_a.teller).depositFromTrusted(_user, RIPE_GOV_VAULT_ID, _a.ripeToken, amountToStake, _config.rewardsLockDuration, _a)
        assert extcall IERC20(_a.ripeToken).approve(_a.teller, 0, default_return_value=True) # dev: ripe approval failed

    # transfer ripe to user
    if amountToSend != 0:
        amount: uint256 = min(amountToSend, staticcall IERC20(_a.ripeToken).balanceOf(self))
        assert extcall IERC20(_a.ripeToken).transfer(_user, amount, default_return_value=True) # dev: ripe transfer failed


# storage clean up


@internal
def _cleanUpUserAssets(
    _user: address,
    _vaultAddr: address,
    _assetsToClean: DynArray[address, MAX_ASSETS_TO_CLEAN],
) -> bool:
    if len(_assetsToClean) == 0:
        return True
    stillInVault: bool = True
    for a: address in _assetsToClean:
        stillInVault = extcall Vault(_vaultAddr).deregisterUserAsset(_user, a)
    return stillInVault


@internal
def _cleanUpUserVaults(
    _user: address,
    _vaultsToClean: DynArray[uint256, MAX_VAULTS_TO_CLEAN],
    _ledger: address,
):
    if len(_vaultsToClean) == 0:
        return
    for vid: uint256 in _vaultsToClean:
        extcall Ledger(_ledger).removeVaultFromUser(_user, vid)