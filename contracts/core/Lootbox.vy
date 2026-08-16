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
    def ripeAvailForRewards() -> uint256: view

interface MissionControl:
    def getClaimLootConfig(_user: address, _caller: address, _ripeToken: address) -> ClaimLootConfig: view
    def getDepositPointsConfig(_asset: address) -> DepositPointsConfig: view
    def isRipeGovVaultId(_vaultId: uint256) -> bool: view
    def getRewardsConfig() -> RewardsConfig: view
    def coreRipeGovVaultId() -> uint256: view
    def underscoreRegistry() -> address: view

interface Teller:
    def depositFromTrusted(_user: address, _vaultId: uint256, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def isUnderscoreWalletOwner(_user: address, _caller: address, _mc: address = empty(address)) -> bool: view

interface PriceDesk:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface UnderscoreLootDistributor:
    def addDepositRewards(_asset: address, _amount: uint256): nonpayable

interface RipeToken:
    def mint(_to: address, _amount: uint256): nonpayable

interface AddressRegistry:
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

event UnderscoreRewardsDistributed:
    underscoreAddr: indexed(address)
    depositAmount: uint256
    yieldAmount: uint256
    blockNumber: uint256

event HasUnderscoreRewardsUpdated:
    hasRewards: bool

event UnderscoreSendIntervalUpdated:
    numBlocks: uint256

event UndyDepositRewardsAmountUpdated:
    amount: uint256

event UndyYieldBonusAmountUpdated:
    amount: uint256

# underscore rewards
hasUnderscoreRewards: public(bool)
underscoreSendInterval: public(uint256)
lastUnderscoreSend: public(uint256)
undyDepositRewardsAmount: public(uint256)
undyYieldBonusAmount: public(uint256)

UNDERSCORE_LOOT_DISTRIBUTOR_ID: constant(uint256) = 6
EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_ASSETS_TO_CLEAN: constant(uint256) = 20
MAX_VAULTS_TO_CLEAN: constant(uint256) = 10
MAX_CLAIM_USERS: constant(uint256) = 25
MIN_UNDERSCORE_SEND_INTERVAL: immutable(uint256)


@deploy
def __init__(
    _ripeHq: address,
    _minUnderscoreSendInterval: uint256,
    _underscoreSendInterval: uint256,
    _undyDepositRewardsAmount: uint256,
    _undyYieldBonusAmount: uint256,
):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, True) # can mint ripe only

    # underscore rewards
    assert _minUnderscoreSendInterval != 0 and _minUnderscoreSendInterval != max_value(uint256) # dev: invalid floor
    MIN_UNDERSCORE_SEND_INTERVAL = _minUnderscoreSendInterval

    if _underscoreSendInterval != 0:
        assert _underscoreSendInterval >= MIN_UNDERSCORE_SEND_INTERVAL # dev: invalid interval
        self.underscoreSendInterval = _underscoreSendInterval
        self.undyDepositRewardsAmount = _undyDepositRewardsAmount
        self.undyYieldBonusAmount = _undyYieldBonusAmount
        self.hasUnderscoreRewards = True


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

    coreRipeGovVaultId: uint256 = self._getCoreRipeGovVaultId(_a.missionControl)
    for i: uint256 in range(1, numUserVaults, bound=max_value(uint256)):
        vaultId: uint256 = staticcall Ledger(_a.ledger).userVaults(_user, i)
        vaultAddr: address = staticcall AddressRegistry(_a.vaultBook).getAddr(vaultId)
        if vaultAddr == empty(address):
            continue

        assetsToRemove: DynArray[address, MAX_ASSETS_TO_CLEAN] = []
        numUserAssets: uint256 = staticcall Vault(vaultAddr).numUserAssets(_user)
        if numUserAssets == 0:
            continue
        for y: uint256 in range(1, numUserAssets, bound=max_value(uint256)):
            asset: address = empty(address)
            hasBalance: bool = False
            asset, hasBalance = staticcall Vault(vaultAddr).getUserAssetAtIndexAndHasBalance(_user, y)
            if asset == empty(address):
                continue

            # claim loot first -- whether this asset can be cleaned up depends on the result
            totalRipeForUser += self._claimDepositLoot(_user, vaultId, vaultAddr, asset, _a)

            # Save to clean up later, but ONLY once the entitlement is gone. A deferred claim
            # leaves `balancePoints` intact, and deregistering here would put those points beyond
            # ordinary enumeration -- `claimDepositLootForAsset` is department-gated, so the user
            # could not recover them on their own. Deregistration does not depend on points
            # (`deregisterUserAsset` only checks the balance), so waiting costs nothing.
            if not hasBalance and len(assetsToRemove) < MAX_ASSETS_TO_CLEAN:
                b: DepositPointsBundle = staticcall Ledger(_a.ledger).getDepositPointsBundle(_user, vaultId, asset)
                if b.userPoints.balancePoints == 0:
                    assetsToRemove.append(asset)

        # clean up user assets (storage optimization)
        stillInVault: bool = self._cleanUpUserAssets(_user, vaultAddr, assetsToRemove)
        if not stillInVault and len(vaultsToRemove) < MAX_VAULTS_TO_CLEAN:
            vaultsToRemove.append(vaultId)

    # clean up user vaults (storage optimization)
    self._cleanUpUserVaults(_user, vaultsToRemove, _a.ledger)

    # mint ripe, then stake or transfer to user
    if totalRipeForUser != 0:
        self._handleRipeMint(_user, totalRipeForUser, _shouldStake, config, coreRipeGovVaultId, _a)

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
        vaultAddr: address = staticcall AddressRegistry(a.vaultBook).getAddr(vaultId)
        if vaultAddr == empty(address):
            continue
        numUserAssets: uint256 = staticcall Vault(vaultAddr).numUserAssets(_user)
        if numUserAssets == 0:
            continue
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
    vaultAddr: address = staticcall AddressRegistry(a.vaultBook).getAddr(_vaultId)
    coreRipeGovVaultId: uint256 = self._getCoreRipeGovVaultId(a.missionControl)
    totalRipeForUser: uint256 = self._claimDepositLoot(_user, _vaultId, vaultAddr, _asset, a)
    if totalRipeForUser != 0:
        config: ClaimLootConfig = staticcall MissionControl(a.missionControl).getClaimLootConfig(_user, _user, a.ripeToken)
        self._handleRipeMint(_user, totalRipeForUser, False, config, coreRipeGovVaultId, a)
    return totalRipeForUser


@internal
def _claimDepositLoot(
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
    userRipeRewards, up, ap, gp, globalRipeRewards = self._getDepositLootData(_user, _vaultId, _vaultAddr, _asset, _a)

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

    # user has no points, or the asset total is inconsistent -- nothing can be computed
    if up.balancePoints == 0 or ap.balancePoints == 0:
        return empty(UserDepositLoot), up, ap, gp, globalRewards

    hasBalance: bool = staticcall Vault(_vaultAddr).doesUserHaveBalance(_user, _asset)
    rewardsBudget: uint256 = staticcall Ledger(_a.ledger).ripeAvailForRewards()
    rewardsBudget -= min(globalRewards.newRipeRewards, rewardsBudget)
    rewardsCanFlow: bool = config.ripePerBlock != 0 and rewardsBudget != 0

    # a category is terminal when
    # 1- its empty bucket cannot refill, or
    # 2- the user has exited and its funded bucket rounded below one wei
    # Funded dust for a live position remains deferred.

    stakerCanReceiveRewards: bool = rewardsCanFlow and config.stakersAlloc != 0
    resolveStakerTerminal: bool = (
        (globalRewards.stakers == 0 and not stakerCanReceiveRewards) or
        (globalRewards.stakers != 0 and not hasBalance)
    )

    voterCanReceiveRewards: bool = rewardsCanFlow and config.votersAlloc != 0
    resolveVoterTerminal: bool = (
        (globalRewards.voters == 0 and not voterCanReceiveRewards) or
        (globalRewards.voters != 0 and not hasBalance)
    )

    genCanReceiveRewards: bool = rewardsCanFlow and config.genDepositorsAlloc != 0
    resolveGenTerminal: bool = (
        (globalRewards.genDepositors == 0 and not genCanReceiveRewards) or
        (globalRewards.genDepositors != 0 and not hasBalance)
    )

    # nothing is committed until we know the whole claim can be settled: `up.balancePoints` is a single ticket
    # backing all three reward pools, so a partial settlement would zero the ticket while leaving one pool's entitlement unpaid.
    apStaker: uint256 = 0
    gpStaker: uint256 = 0
    rewStaker: uint256 = 0
    lootStaker: uint256 = 0
    apStaker, gpStaker, rewStaker, lootStaker = self._calcSpecificLoot(up.balancePoints, ap.balancePoints, ap.ripeStakerPoints, gp.ripeStakerPoints, globalRewards.stakers, resolveStakerTerminal, True)

    apVote: uint256 = 0
    gpVote: uint256 = 0
    rewVote: uint256 = 0
    lootVote: uint256 = 0
    apVote, gpVote, rewVote, lootVote = self._calcSpecificLoot(up.balancePoints, ap.balancePoints, ap.ripeVotePoints, gp.ripeVotePoints, globalRewards.voters, resolveVoterTerminal, True)

    apGen: uint256 = 0
    gpGen: uint256 = 0
    rewGen: uint256 = 0
    lootGen: uint256 = 0
    apGen, gpGen, rewGen, lootGen = self._calcSpecificLoot(up.balancePoints, ap.balancePoints, ap.ripeGenPoints, gp.ripeGenPoints, globalRewards.genDepositors, resolveGenTerminal, True)

    # Any attributable zero-paying category blocks the shared ticket until it becomes terminal.
    isBlocked: bool = (
        self._isCategoryBlocked(ap.ripeStakerPoints, gp.ripeStakerPoints, lootStaker, resolveStakerTerminal) or
        self._isCategoryBlocked(ap.ripeVotePoints, gp.ripeVotePoints, lootVote, resolveVoterTerminal) or
        self._isCategoryBlocked(ap.ripeGenPoints, gp.ripeGenPoints, lootGen, resolveGenTerminal)
    )

    hasCategoryEntitlement: bool = (
        (ap.ripeStakerPoints != 0 and gp.ripeStakerPoints != 0) or
        (ap.ripeVotePoints != 0 and gp.ripeVotePoints != 0) or
        (ap.ripeGenPoints != 0 and gp.ripeGenPoints != 0)
    )

    # a live position with no category entitlement keeps its ticket. Otherwise every category must
    # either pay or resolve terminally before the shared ticket can be consumed.
    if isBlocked or (hasBalance and not hasCategoryEntitlement):
        return empty(UserDepositLoot), up, ap, gp, globalRewards

    # every attributable category paid -- commit all three atomically and consume the ticket
    ap.ripeStakerPoints = apStaker
    ap.ripeVotePoints = apVote
    ap.ripeGenPoints = apGen
    gp.ripeStakerPoints = gpStaker
    gp.ripeVotePoints = gpVote
    gp.ripeGenPoints = gpGen
    globalRewards.stakers = rewStaker
    globalRewards.voters = rewVote
    globalRewards.genDepositors = rewGen

    ap.balancePoints -= up.balancePoints # do first
    up.balancePoints = 0

    return UserDepositLoot(
        ripeStakerLoot=lootStaker,
        ripeVoteLoot=lootVote,
        ripeGenLoot=lootGen,
    ), up, ap, gp, globalRewards


@view
@internal
def _isCategoryBlocked(
    _assetPoints: uint256,
    _globalPoints: uint256,
    _paid: uint256,
    _resolveTerminalDust: bool,
) -> bool:
    return _paid == 0 and _assetPoints != 0 and _globalPoints != 0 and not _resolveTerminalDust


# helper / views


@view
@external
def getClaimableDepositLootForAsset(_user: address, _vaultId: uint256, _asset: address) -> uint256:
    a: addys.Addys = addys._getAddys()
    vaultAddr: address = staticcall AddressRegistry(a.vaultBook).getAddr(_vaultId)
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
    userRipeRewards, up, ap, gp, globalRipeRewards = self._getDepositLootData(_user, _vaultId, _vaultAddr, _asset, _a)
    return userRipeRewards.ripeStakerLoot + userRipeRewards.ripeVoteLoot + userRipeRewards.ripeGenLoot
    

# claim utils


# NOTE: this external keeps its original basis-point signature so its ABI and expectations are
# unchanged. It forwards `(_userShareOfAsset, HUNDRED_PERCENT)` as the ratio, which reproduces the
# previous math exactly. The claim path passes the raw point counts instead, for full precision.


@view
@external
def calcSpecificLoot(
    _userShareOfAsset: uint256,
    _assetPoints: uint256,
    _globalPoints: uint256,
    _rewardsAvailable: uint256,
) -> (uint256, uint256, uint256, uint256):
    return self._calcSpecificLoot(_userShareOfAsset, HUNDRED_PERCENT, _assetPoints, _globalPoints, _rewardsAvailable, False, False)


@view
@internal
def _calcSpecificLoot(
    _userPoints: uint256,
    _totalPoints: uint256,
    _assetPoints: uint256,
    _globalPoints: uint256,
    _rewardsAvailable: uint256,
    _resolveTerminalDust: bool,
    _ensurePointProgress: bool,
  ) -> (uint256, uint256, uint256, uint256):

    # early returns for edge cases
    if _assetPoints == 0 or _globalPoints == 0 or _userPoints == 0 or _totalPoints == 0:
        return _assetPoints, _globalPoints, _rewardsAvailable, 0
    if _rewardsAvailable == 0 and not _resolveTerminalDust:
        return _assetPoints, _globalPoints, 0, 0

    # cap asset points to global points to prevent inconsistencies
    assetPoints: uint256 = min(_assetPoints, _globalPoints)

    userRewards: uint256 = 0
    if _rewardsAvailable != 0:
        # calc asset rewards, then the user's ratio directly with no intermediate quantisation
        assetRewards: uint256 = _rewardsAvailable * assetPoints // _globalPoints
        userRewards = assetRewards * _userPoints // _totalPoints

    if userRewards == 0 and not _resolveTerminalDust:
        return assetPoints, _globalPoints, _rewardsAvailable, 0

    # calc points to reduce -- same ratio, same precision as the payout above
    userAssetPoints: uint256 = assetPoints * _userPoints // _totalPoints
    pointsToReduce: uint256 = userAssetPoints
    if pointsToReduce == 0 and _ensurePointProgress:
        pointsToReduce = 1
    pointsToReduce = min(pointsToReduce, assetPoints)
    pointsToReduce = min(pointsToReduce, _globalPoints)

    # update values
    newAssetPoints: uint256 = assetPoints - pointsToReduce
    newGlobalPoints: uint256 = _globalPoints - pointsToReduce
    if userRewards == 0 and _rewardsAvailable != 0:
        userRewards = 1
    newRewardsAvail: uint256 = _rewardsAvailable - userRewards

    return newAssetPoints, newGlobalPoints, newRewardsAvail, userRewards


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


# reset balance points


@external
def resetUserBalancePoints(_user: address, _asset: address, _vaultId: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()

    # get latest global rewards
    config: RewardsConfig = staticcall MissionControl(a.missionControl).getRewardsConfig()
    globalRewards: RipeRewards = self._getLatestGlobalRipeRewards(config, a)
    vaultAddr: address = staticcall AddressRegistry(a.vaultBook).getAddr(_vaultId)
    if empty(address) in [vaultAddr, _asset, _user]:
        return

    # get latest deposit points
    up: UserDepositPoints = empty(UserDepositPoints)
    ap: AssetDepositPoints = empty(AssetDepositPoints)
    gp: GlobalDepositPoints = empty(GlobalDepositPoints)
    up, ap, gp = self._getLatestDepositPoints(_user, _vaultId, vaultAddr, _asset, config, a)

    # reset user balance points
    ap.balancePoints -= min(up.balancePoints, ap.balancePoints)
    up.balancePoints = 0

    # update points
    extcall Ledger(a.ledger).setDepositPointsAndRipeRewards(_user, _vaultId, _asset, up, ap, gp, globalRewards)


# reset asset points


@external
def resetAssetPoints(_asset: address, _vaultId: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()

    # get latest global rewards
    config: RewardsConfig = staticcall MissionControl(a.missionControl).getRewardsConfig()
    globalRewards: RipeRewards = self._getLatestGlobalRipeRewards(config, a)
    vaultAddr: address = staticcall AddressRegistry(a.vaultBook).getAddr(_vaultId)
    if empty(address) in [vaultAddr, _asset]:
        return

    # get latest deposit points
    up: UserDepositPoints = empty(UserDepositPoints)
    ap: AssetDepositPoints = empty(AssetDepositPoints)
    gp: GlobalDepositPoints = empty(GlobalDepositPoints)
    up, ap, gp = self._getLatestDepositPoints(empty(address), _vaultId, vaultAddr, _asset, config, a)

    # reset asset points
    gp.ripeStakerPoints -= min(ap.ripeStakerPoints, gp.ripeStakerPoints)
    ap.ripeStakerPoints = 0
    gp.ripeVotePoints -= min(ap.ripeVotePoints, gp.ripeVotePoints)
    ap.ripeVotePoints = 0
    gp.ripeGenPoints -= min(ap.ripeGenPoints, gp.ripeGenPoints)
    ap.ripeGenPoints = 0

    # update points
    extcall Ledger(a.ledger).setDepositPointsAndRipeRewards(empty(address), _vaultId, _asset, up, ap, gp, globalRewards)


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
    vaultAddr: address = staticcall AddressRegistry(a.vaultBook).getAddr(_vaultId)
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
    assert staticcall MissionControl(_a.missionControl).coreRipeGovVaultId() != 0 # dev: invalid vault id
    p: DepositPointsBundle = staticcall Ledger(_a.ledger).getDepositPointsBundle(_user, _vaultId, _asset)

    # latest global points
    globalPoints: GlobalDepositPoints = self._getLatestGlobalDepositPoints(p.globalPoints, _c.arePointsEnabled, _c.stakersPointsAllocTotal, _c.voterPointsAllocTotal)

    # latest asset points
    assetConfig: DepositPointsConfig = staticcall MissionControl(_a.missionControl).getDepositPointsConfig(_asset) 
    assetPoints: AssetDepositPoints = self._getLatestAssetDepositPoints(p.assetPoints, _c.arePointsEnabled, assetConfig.stakersPointsAlloc, assetConfig.voterPointsAlloc)
    if assetPoints.precision == 0:
        assetPoints.precision = self._getAssetPrecision(assetConfig.isNft, _asset)

    # Ripe Gov vaults return an already-normalized share. MissionControl retains every historical
    # core id because old positions and rewards can remain claimable after the core pointer moves.
    isRipeGovVault: bool = staticcall MissionControl(_a.missionControl).isRipeGovVaultId(_vaultId)

    # Update holder lastBalance before lastUsdValue so gen-reward funding only
    # includes value represented by normalized holder points.
    userPoints: UserDepositPoints = empty(UserDepositPoints)
    rawLootShare: uint256 = 0
    if _user != empty(address):
        userPoints = self._getLatestUserDepositPoints(p.userPoints, _c.arePointsEnabled)
        rawLootShare = staticcall Vault(_vaultAddr).getUserLootBoxShare(_user, _asset)
        userLootShare: uint256 = rawLootShare
        if userLootShare != 0 and not isRipeGovVault:
            userLootShare = userLootShare // assetPoints.precision
        assetPoints.lastBalance -= userPoints.lastBalance
        assetPoints.lastBalance += userLootShare
        userPoints.lastBalance = userLootShare

    # Staked assets are not eligible for gen deposit rewards. RipeGov keeps
    # vault totals because its share is already normalized. Other vaults fund
    # from attributable underlying: convert aggregate normalized loot share
    # through the current user's share-to-asset rate so rebasing vaults keep
    # yield while sub-precision residuals still cannot fill the bucket.
    newAssetUsdValue: uint256 = 0
    if assetConfig.stakersPointsAlloc == 0:
        assetAmount: uint256 = 0
        if isRipeGovVault:
            assetAmount = staticcall Vault(_vaultAddr).getTotalAmountForVault(_asset)
        elif assetPoints.lastBalance != 0:
            if rawLootShare != 0:
                userAmount: uint256 = staticcall Vault(_vaultAddr).getTotalAmountForUser(_user, _asset)
                eligibleShare: uint256 = assetPoints.lastBalance * assetPoints.precision
                assetAmount = eligibleShare * userAmount // rawLootShare
            else:
                assetAmount = staticcall Vault(_vaultAddr).getTotalAmountForVault(_asset)
        newAssetUsdValue = self._refreshAssetUsdValue(_asset, assetAmount, _a.priceDesk)

    if newAssetUsdValue != assetPoints.lastUsdValue:
        globalPoints.lastUsdValue -= assetPoints.lastUsdValue
        globalPoints.lastUsdValue += newAssetUsdValue
        assetPoints.lastUsdValue = newAssetUsdValue

    return userPoints, assetPoints, globalPoints


# utils


@view
@internal
def _refreshAssetUsdValue(_asset: address, _amount: uint256, _priceDesk: address) -> uint256:
    if _amount == 0:
        return 0
    newUsdValue: uint256 = staticcall PriceDesk(_priceDesk).getUsdValue(_asset, _amount)
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


# reset borrow points


@external
def resetUserBorrowPoints(_user: address):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    if _user == empty(address):
        return

    config: RewardsConfig = staticcall MissionControl(a.missionControl).getRewardsConfig()
    globalRewards: RipeRewards = self._getLatestGlobalRipeRewards(config, a)
    up: BorrowPoints = empty(BorrowPoints)
    gp: BorrowPoints = empty(BorrowPoints)
    up, gp = self._getLatestBorrowPoints(_user, config.arePointsEnabled, a.ledger)

    # reset user borrow points
    gp.points -= min(up.points, gp.points)
    up.points = 0

    # update points
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
        coreRipeGovVaultId: uint256 = self._getCoreRipeGovVaultId(a.missionControl)
        self._handleRipeMint(_user, totalRipeForUser, False, config, coreRipeGovVaultId, a)
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

    # calc borrower rewards
    cappedPoints: uint256 = min(up.points, gp.points)
    userRipeRewards: uint256 = 0
    if gp.points != 0 and cappedPoints != 0 and globalRewards.borrowers != 0:
        if cappedPoints == gp.points:
            userRipeRewards = globalRewards.borrowers
        else:
            userRipeRewards = self._mulDivFloor(globalRewards.borrowers, cappedPoints, gp.points)

    # update structs
    if userRipeRewards != 0:
        globalRewards.borrowers -= userRipeRewards
        gp.points -= cappedPoints # do first
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
    _coreRipeGovVaultId: uint256,
    _a: addys.Addys,
):
    assert _coreRipeGovVaultId != 0 # dev: invalid vault id

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
        extcall Teller(_a.teller).depositFromTrusted(_user, _coreRipeGovVaultId, _a.ripeToken, amountToStake, _config.rewardsLockDuration, _a)
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


# ripe gov vault id


@view
@internal
def _getCoreRipeGovVaultId(_missionControl: address) -> uint256:
    vaultId: uint256 = staticcall MissionControl(_missionControl).coreRipeGovVaultId()
    assert vaultId != 0 # dev: invalid vault id
    return vaultId


# math


@pure
@internal
def _mulDivFloor(_x: uint256, _y: uint256, _d: uint256) -> uint256:
    assert _d != 0 # dev: zero denominator

    lo: uint256 = unsafe_mul(_x, _y)
    mm: uint256 = uint256_mulmod(_x, _y, max_value(uint256))
    hi: uint256 = unsafe_sub(
        unsafe_sub(mm, lo),
        convert(mm < lo, uint256),
    )

    # Fast path: the product fits in 256 bits.
    if hi == 0:
        return lo // _d

    # The full-precision result must fit in uint256.
    assert _d > hi # dev: result overflows

    # Make the 512-bit product exactly divisible by the denominator.
    rem: uint256 = uint256_mulmod(_x, _y, _d)
    hi = unsafe_sub(hi, convert(rem > lo, uint256))
    lo = unsafe_sub(lo, rem)

    # Factor powers of two out of the denominator and shift the
    # high product bits into the low product word.
    tz: uint256 = unsafe_sub(0, _d) & _d
    d2: uint256 = _d // tz
    lo = lo // tz
    lo |= unsafe_mul(
        hi,
        unsafe_add(
            unsafe_div(unsafe_sub(0, tz), tz),
            1,
        ),
    )

    # Compute the modular inverse of the now-odd denominator.
    inv: uint256 = unsafe_mul(3, d2) ^ 2
    for i: uint256 in range(6):
        inv = unsafe_mul(
            inv,
            unsafe_sub(2, unsafe_mul(d2, inv)),
        )

    return unsafe_mul(lo, inv)


###############################
# Underscore Loot Distributor #
###############################


@external
def distributeUnderscoreRewards() -> (uint256, uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()

    assert self.hasUnderscoreRewards # dev: no underscore rewards

    # check interval constraint
    underscoreSendInterval: uint256 = self.underscoreSendInterval
    assert underscoreSendInterval != 0 # dev: invalid interval
    assert block.number > self.lastUnderscoreSend + underscoreSendInterval # dev: too early

    # get available RIPE rewards
    ripeAvailForRewards: uint256 = staticcall Ledger(a.ledger).ripeAvailForRewards()

    # piggy backing on this to actually update ripe rewards available
    config: RewardsConfig = staticcall MissionControl(a.missionControl).getRewardsConfig()
    ripeRewards: RipeRewards = self._getLatestGlobalRipeRewards(config, a)
    ripeAvailForRewards -= min(ripeRewards.newRipeRewards, ripeAvailForRewards)
    assert ripeAvailForRewards != 0 # dev: no rewards to distribute

    # calculate total
    undyDepositRewardsAmount: uint256 = self.undyDepositRewardsAmount
    undyYieldBonusAmount: uint256 = self.undyYieldBonusAmount
    totalRewardsAmount: uint256 = undyDepositRewardsAmount + undyYieldBonusAmount
    assert totalRewardsAmount != 0 # dev: no rewards to distribute

    newUndyRewards: uint256 = min(totalRewardsAmount, ripeAvailForRewards)

    # calculate proportional amounts for deposit and yield
    depositRewards: uint256 = undyDepositRewardsAmount
    yieldBonusAmount: uint256 = undyYieldBonusAmount
    if newUndyRewards != totalRewardsAmount:
        depositRewards = newUndyRewards * undyDepositRewardsAmount // totalRewardsAmount
        yieldBonusAmount = newUndyRewards - depositRewards

    # mint RIPE tokens
    extcall RipeToken(a.ripeToken).mint(self, newUndyRewards)

    # get underscore distributor address
    underscoreDistributor: address = self._getUnderscoreLootDistributor(a.missionControl)
    assert underscoreDistributor != empty(address) # dev: no underscore distributor

    # add deposit rewards
    if depositRewards != 0:
        assert extcall IERC20(a.ripeToken).approve(underscoreDistributor, depositRewards, default_return_value=True) # dev: ripe approval failed
        extcall UnderscoreLootDistributor(underscoreDistributor).addDepositRewards(a.ripeToken, depositRewards)
        assert extcall IERC20(a.ripeToken).approve(underscoreDistributor, 0, default_return_value=True) # dev: ripe approval failed

    # transfer yield bonus to underscore distributor
    if yieldBonusAmount != 0:
        assert extcall IERC20(a.ripeToken).transfer(underscoreDistributor, yieldBonusAmount, default_return_value=True) # dev: ripe transfer failed

    # update last rewards distribution block
    self.lastUnderscoreSend = block.number

    # update Ledger accounting - use RipeRewards.newRipeRewards to decrement ripeAvailForRewards
    ripeRewards.newRipeRewards += newUndyRewards
    extcall Ledger(a.ledger).setRipeRewards(ripeRewards)

    log UnderscoreRewardsDistributed(
        underscoreAddr=underscoreDistributor,
        depositAmount=depositRewards,
        yieldAmount=yieldBonusAmount,
        blockNumber=block.number
    )
    return depositRewards, yieldBonusAmount


# get underscore loot distributor


@view
@internal
def _getUnderscoreLootDistributor(_mc: address) -> address:
    underscore: address = staticcall MissionControl(_mc).underscoreRegistry()
    if underscore == empty(address):
        return empty(address)
    return staticcall AddressRegistry(underscore).getAddr(UNDERSCORE_LOOT_DISTRIBUTOR_ID)


# config setters


@view
@external
def minUnderscoreSendInterval() -> uint256:
    return MIN_UNDERSCORE_SEND_INTERVAL


@external
def setHasUnderscoreRewards(_hasRewards: bool):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    assert _hasRewards != self.hasUnderscoreRewards # dev: no change
    self.hasUnderscoreRewards = _hasRewards
    log HasUnderscoreRewardsUpdated(hasRewards=_hasRewards)


@external
def setUnderscoreSendInterval(_numBlocks: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    assert _numBlocks != max_value(uint256) # dev: invalid interval
    assert _numBlocks >= MIN_UNDERSCORE_SEND_INTERVAL # dev: invalid interval
    assert _numBlocks != self.underscoreSendInterval # dev: no change
    self.underscoreSendInterval = _numBlocks
    log UnderscoreSendIntervalUpdated(numBlocks=_numBlocks)


@external
def setUndyDepositRewardsAmount(_amount: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    assert _amount != max_value(uint256) # dev: invalid amount
    assert _amount != self.undyDepositRewardsAmount # dev: no change
    self.undyDepositRewardsAmount = _amount
    log UndyDepositRewardsAmountUpdated(amount=_amount)


@external
def setUndyYieldBonusAmount(_amount: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    assert _amount != max_value(uint256) # dev: invalid amount
    assert _amount != self.undyYieldBonusAmount # dev: no change
    self.undyYieldBonusAmount = _amount
    log UndyYieldBonusAmountUpdated(amount=_amount)
