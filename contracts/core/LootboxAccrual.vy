#     ╔══════════════════════════════════════════════════════════════╗
#     ║  ** Lootbox Accrual **                                       ║
#     ║  Point / reward accrual math and index snapshots that        ║
#     ║  outlive a Lootbox swap. Not a Ripe HQ department.           ║
#     ╚══════════════════════════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3
# pragma optimize codesize

initializes: addys

import contracts.modules.Addys as addys
import interfaces.ConfigStructs as cs

interface MissionControl:
    def getPriorityLiqAssetVaults() -> DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]: view
    def getPriorityStabVaults() -> DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]: view
    def getPriorityPriceSourceIds() -> DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]: view
    def getPointsIndexBundle(_asset: address) -> PointsIndexBundle: view
    def getDepositPointsConfig(_asset: address) -> DepositPointsConfig: view
    def ripeGovVaultConfig(_asset: address) -> cs.RipeGovVaultConfig: view
    def getEnabledClockBundle() -> EnabledClockBundle: view
    def assetConfig(_asset: address) -> cs.AssetConfig: view
    def rewardsConfig() -> cs.RipeRewardsConfig: view
    def getRewardsConfig() -> RewardsConfig: view
    def ripeBondConfig() -> cs.RipeBondConfig: view
    def genDebtConfig() -> cs.GenDebtConfig: view
    def assets(_index: uint256) -> address: view
    def isImportFinalized() -> bool: view
    def genConfig() -> cs.GenConfig: view
    def underscoreRegistry() -> address: view
    def shouldCheckLastTouch() -> bool: view
    def lootboxAccrual() -> address: view
    def hrConfig() -> cs.HrConfig: view
    def activationBlock() -> uint256: view
    def trainingWheels() -> address: view
    def numAssets() -> uint256: view
    def priorMC() -> address: view

interface Lootbox:
    def lootboxAccrual() -> address: view

interface Ledger:
    def getDepositPointsBundle(_user: address, _vaultId: uint256, _asset: address) -> DepositPointsBundle: view
    def getBorrowPointsBundle(_user: address) -> BorrowPointsBundle: view
    def getRipeRewardsBundle() -> RipeRewardsBundle: view

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

# enabled-block clock (MissionControl)
struct EnabledClockBundle:
    activationBlock: uint256
    arePointsEnabled: bool
    enabledBlocks: uint256
    enabledClockBlock: uint256

# enabled-block clock + global / asset point indexes (MissionControl)
struct PointsIndexBundle:
    activationBlock: uint256
    arePointsEnabled: bool
    enabledBlocks: uint256
    enabledClockBlock: uint256
    globalStakerIndex: uint256
    globalVoterIndex: uint256
    globalIndexEnabledBlocks: uint256
    stakersPointsAllocTotal: uint256
    voterPointsAllocTotal: uint256
    assetStakerIndex: uint256
    assetVoterIndex: uint256
    assetIndexEnabledBlocks: uint256
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256

# index snapshot for a points scope (global / asset)
struct IndexSnap:
    snapInit: bool
    stakerIndexSnap: uint256
    voterIndexSnap: uint256
    enabledSnap: uint256

# enabled-clock snapshot (user deposit / borrow global / borrow user)
struct EnabledSnap:
    snapInit: bool
    enabledSnap: uint256

# next snaps for one deposit write: the current peeks at preview time (returned by `previewDeposit`,
# persisted by `commitDepositSnaps` after the Ledger write)
struct DepositSnaps:
    globalStakerIndex: uint256
    globalVoterIndex: uint256
    assetStakerIndex: uint256
    assetVoterIndex: uint256
    enabledBlocks: uint256

event LootboxAccrualArmed:
    missionControl: indexed(address)
    activationBlock: uint256
    frozenAssets: uint256

# activation -- bound to exactly one MissionControl, armed on exactly one block
activationBlock: public(uint256)
armedMissionControl: public(address)

# frozen arm-time point rates (lazy bridge only)
frozenStakerTotal: public(uint256)
frozenVoterTotal: public(uint256)
frozenArePointsEnabled: public(bool)
frozenAssetStaker: public(HashMap[address, uint256]) # asset -> stakersPointsAlloc at arm
frozenAssetVoter: public(HashMap[address, uint256]) # asset -> voterPointsAlloc at arm

# snapshots
globalDepositSnap: public(IndexSnap)
assetDepositSnap: public(HashMap[uint256, HashMap[address, IndexSnap]]) # vault id -> asset -> snap
userDepositSnap: public(HashMap[address, HashMap[uint256, HashMap[address, EnabledSnap]]]) # user -> vault id -> asset -> snap
globalBorrowSnap: public(EnabledSnap)
userBorrowSnap: public(HashMap[address, EnabledSnap]) # user -> snap

EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
# arm walks the MissionControl asset registry once to freeze per-asset rates (and, for a
# replacement, to compare every asset config with the live prior); the Defaults interface caps a
# registry snapshot at 50 assets, this leaves headroom and a known gas ceiling
MAX_ASSETS_AT_ARM: constant(uint256) = 100
MAX_PRIORITY_PRICE_SOURCES: constant(uint256) = 10 # MissionControl.MAX_PRIORITY_PRICE_SOURCES
PRIORITY_VAULT_DATA: constant(uint256) = 20 # MissionControl.PRIORITY_VAULT_DATA


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)


#######
# Arm #
#######


@external
def arm(_mc: address):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert self.activationBlock == 0 # dev: already armed
    assert _mc != empty(address) # dev: invalid mission control

    # the MissionControl must be bound to this accrual (three-way binding: MC <-> Accrual <-> Lootbox)
    assert staticcall MissionControl(_mc).lootboxAccrual() == self # dev: accrual mismatch
    assert staticcall MissionControl(_mc).activationBlock() == 0 # dev: mission control already armed

    # a replacement MissionControl must have finished importing its predecessor (MissionControl
    # itself requires that finalize in the arm block) and must mirror the live prior's global
    # state exactly: a stale Defaults snapshot or un-replayed drift cannot go live
    prior: address = staticcall MissionControl(_mc).priorMC()
    if prior != empty(address):
        assert staticcall MissionControl(_mc).isImportFinalized() # dev: import not finalized
        self._assertGlobalsMirrorPrior(_mc, prior)

    # freeze arm-time point rates (used only by the lazy bridge)
    config: RewardsConfig = staticcall MissionControl(_mc).getRewardsConfig()
    self.frozenStakerTotal = config.stakersPointsAllocTotal
    self.frozenVoterTotal = config.voterPointsAllocTotal
    self.frozenArePointsEnabled = config.arePointsEnabled

    # bounded walk of the asset registry (numAssets is the next 1-based index)
    numAssets: uint256 = staticcall MissionControl(_mc).numAssets()
    assert numAssets <= MAX_ASSETS_AT_ARM + 1 # dev: too many assets
    frozenAssets: uint256 = 0
    if numAssets > 1:
        for i: uint256 in range(1, numAssets, bound=MAX_ASSETS_AT_ARM + 1):
            asset: address = staticcall MissionControl(_mc).assets(i)
            if asset == empty(address):
                continue
            if prior != empty(address):
                self._assertAssetMirrorsPrior(_mc, prior, asset)
            assetConfig: DepositPointsConfig = staticcall MissionControl(_mc).getDepositPointsConfig(asset)
            if assetConfig.stakersPointsAlloc != 0:
                self.frozenAssetStaker[asset] = assetConfig.stakersPointsAlloc
            if assetConfig.voterPointsAlloc != 0:
                self.frozenAssetVoter[asset] = assetConfig.voterPointsAlloc
            frozenAssets += 1

    self.armedMissionControl = _mc
    self.activationBlock = block.number
    log LootboxAccrualArmed(missionControl=_mc, activationBlock=block.number, frozenAssets=frozenAssets)


@view
@internal
def _assertGlobalsMirrorPrior(_mc: address, _prior: address):
    # every global config the protocol reads from MissionControl, value-equal to the live prior
    assert keccak256(abi_encode(staticcall MissionControl(_mc).genConfig())) == keccak256(abi_encode(staticcall MissionControl(_prior).genConfig())) # dev: gen config drift
    assert keccak256(abi_encode(staticcall MissionControl(_mc).genDebtConfig())) == keccak256(abi_encode(staticcall MissionControl(_prior).genDebtConfig())) # dev: gen debt config drift
    assert keccak256(abi_encode(staticcall MissionControl(_mc).hrConfig())) == keccak256(abi_encode(staticcall MissionControl(_prior).hrConfig())) # dev: hr config drift
    assert keccak256(abi_encode(staticcall MissionControl(_mc).ripeBondConfig())) == keccak256(abi_encode(staticcall MissionControl(_prior).ripeBondConfig())) # dev: ripe bond config drift
    assert keccak256(abi_encode(staticcall MissionControl(_mc).rewardsConfig())) == keccak256(abi_encode(staticcall MissionControl(_prior).rewardsConfig())) # dev: rewards config drift
    assert keccak256(abi_encode(staticcall MissionControl(_mc).getPriorityLiqAssetVaults())) == keccak256(abi_encode(staticcall MissionControl(_prior).getPriorityLiqAssetVaults())) # dev: priority liq vaults drift
    assert keccak256(abi_encode(staticcall MissionControl(_mc).getPriorityStabVaults())) == keccak256(abi_encode(staticcall MissionControl(_prior).getPriorityStabVaults())) # dev: priority stab vaults drift
    assert keccak256(abi_encode(staticcall MissionControl(_mc).getPriorityPriceSourceIds())) == keccak256(abi_encode(staticcall MissionControl(_prior).getPriorityPriceSourceIds())) # dev: priority price sources drift
    assert staticcall MissionControl(_mc).underscoreRegistry() == staticcall MissionControl(_prior).underscoreRegistry() # dev: underscore registry drift
    assert staticcall MissionControl(_mc).trainingWheels() == staticcall MissionControl(_prior).trainingWheels() # dev: training wheels drift
    assert staticcall MissionControl(_mc).shouldCheckLastTouch() == staticcall MissionControl(_prior).shouldCheckLastTouch() # dev: last touch drift


@view
@internal
def _assertAssetMirrorsPrior(_mc: address, _prior: address, _asset: address):
    assert keccak256(abi_encode(staticcall MissionControl(_mc).assetConfig(_asset))) == keccak256(abi_encode(staticcall MissionControl(_prior).assetConfig(_asset))) # dev: asset config drift
    assert keccak256(abi_encode(staticcall MissionControl(_mc).ripeGovVaultConfig(_asset))) == keccak256(abi_encode(staticcall MissionControl(_prior).ripeGovVaultConfig(_asset))) # dev: ripe gov vault config drift


@view
@internal
def _assertArmed(_mc: address, _mcActivationBlock: uint256):
    # armed, bound to this MissionControl, and both armed on the same block
    activationBlock: uint256 = self.activationBlock
    assert activationBlock != 0 and _mc == self.armedMissionControl and activationBlock == _mcActivationBlock # dev: not armed


@view
@external
def isArmedWith(_mc: address) -> bool:
    # armed, bound to `_mc`, and both armed on the same block
    activationBlock: uint256 = self.activationBlock
    if activationBlock == 0 or _mc != self.armedMissionControl:
        return False
    return staticcall MissionControl(_mc).activationBlock() == activationBlock


@view
@external
def assertActivated(_mc: address, _lootbox: address) -> bool:
    # Arming half of the activation verifier (SwitchboardEcho.assertRewardAccountingActivated
    # proves the RipeHq registry half and calls this): armed with exactly `_mc`, both armed on
    # the same nonzero block, and `_mc` / `_lootbox` both bound to this accrual.
    activationBlock: uint256 = self.activationBlock
    assert activationBlock != 0 and _mc == self.armedMissionControl # dev: not armed
    assert staticcall MissionControl(_mc).activationBlock() == activationBlock # dev: mission control not armed
    assert staticcall MissionControl(_mc).lootboxAccrual() == self # dev: accrual mismatch
    assert staticcall Lootbox(_lootbox).lootboxAccrual() == self # dev: lootbox not bound
    return True


############
# Previews #
############


# ripe rewards


@view
@external
def previewRipeRewards(_mc: address, _ledger: address) -> RipeRewards:
    self._assertArmed(_mc, staticcall MissionControl(_mc).activationBlock())
    b: RipeRewardsBundle = staticcall Ledger(_ledger).getRipeRewardsBundle()
    config: RewardsConfig = staticcall MissionControl(_mc).getRewardsConfig()
    return self._calcRipeRewards(b, config)


@view
@internal
def _calcRipeRewards(_b: RipeRewardsBundle, _config: RewardsConfig) -> RipeRewards:
    rewards: RipeRewards = _b.ripeRewards
    rewards.newRipeRewards = 0 # important to reset!

    # elapsed blocks
    elapsedBlocks: uint256 = 0
    if rewards.lastUpdate != 0 and block.number > rewards.lastUpdate:
        elapsedBlocks = block.number - rewards.lastUpdate

    # update last update
    rewards.lastUpdate = block.number

    # nothing to do here
    if elapsedBlocks == 0 or _config.ripePerBlock == 0 or _b.ripeAvailForRewards == 0:
        return rewards

    # new Ripe rewards
    newRipeDistro: uint256 = min(elapsedBlocks * _config.ripePerBlock, _b.ripeAvailForRewards)

    # allocate ripe rewards to global buckets -- only the four floored
    # allocation deltas leave `ripeAvailForRewards`; the floor remainder stays available
    total: uint256 = _config.borrowersAlloc + _config.stakersAlloc + _config.votersAlloc + _config.genDepositorsAlloc
    if total != 0:
        newBorrowers: uint256 = newRipeDistro * _config.borrowersAlloc // total
        newStakers: uint256 = newRipeDistro * _config.stakersAlloc // total
        newVoters: uint256 = newRipeDistro * _config.votersAlloc // total
        newGenDepositors: uint256 = newRipeDistro * _config.genDepositorsAlloc // total
        rewards.borrowers += newBorrowers
        rewards.stakers += newStakers
        rewards.voters += newVoters
        rewards.genDepositors += newGenDepositors
        rewards.newRipeRewards = newBorrowers + newStakers + newVoters + newGenDepositors

    return rewards


# deposit points


@view
@external
def previewDeposit(
    _mc: address,
    _ledger: address,
    _user: address,
    _vaultId: uint256,
    _asset: address,
) -> (UserDepositPoints, AssetDepositPoints, GlobalDepositPoints, DepositSnaps):
    ib: PointsIndexBundle = staticcall MissionControl(_mc).getPointsIndexBundle(_asset)
    self._assertArmed(_mc, ib.activationBlock)
    p: DepositPointsBundle = staticcall Ledger(_ledger).getDepositPointsBundle(_user, _vaultId, _asset)
    c: EnabledClockBundle = EnabledClockBundle(
        activationBlock=ib.activationBlock,
        arePointsEnabled=ib.arePointsEnabled,
        enabledBlocks=ib.enabledBlocks,
        enabledClockBlock=ib.enabledClockBlock,
    )

    # next snaps = the current peeks
    enabledNow: uint256 = self._peekEnabledAt(c, block.number)
    nextSnaps: DepositSnaps = DepositSnaps(
        globalStakerIndex=ib.globalStakerIndex + ib.stakersPointsAllocTotal * (enabledNow - ib.globalIndexEnabledBlocks),
        globalVoterIndex=ib.globalVoterIndex + ib.voterPointsAllocTotal * (enabledNow - ib.globalIndexEnabledBlocks),
        assetStakerIndex=ib.assetStakerIndex + ib.stakersPointsAlloc * (enabledNow - ib.assetIndexEnabledBlocks),
        assetVoterIndex=ib.assetVoterIndex + ib.voterPointsAlloc * (enabledNow - ib.assetIndexEnabledBlocks),
        enabledBlocks=enabledNow,
    )

    # global points
    gp: GlobalDepositPoints = p.globalPoints
    gs: IndexSnap = self.globalDepositSnap
    enabledDelta: uint256 = self._enabledDelta(gp.lastUpdate, gs.snapInit, gs.enabledSnap, c)
    gp.ripeStakerPoints += self._indexDelta(gp.lastUpdate, gs.snapInit, gs.stakerIndexSnap, ib.globalStakerIndex, ib.stakersPointsAllocTotal, ib.globalIndexEnabledBlocks, c, self.frozenStakerTotal)
    gp.ripeVotePoints += self._indexDelta(gp.lastUpdate, gs.snapInit, gs.voterIndexSnap, ib.globalVoterIndex, ib.voterPointsAllocTotal, ib.globalIndexEnabledBlocks, c, self.frozenVoterTotal)
    gp.ripeGenPoints += gp.lastUsdValue * enabledDelta
    gp.lastUpdate = block.number

    # asset points
    ap: AssetDepositPoints = p.assetPoints
    asnap: IndexSnap = self.assetDepositSnap[_vaultId][_asset]
    enabledDelta = self._enabledDelta(ap.lastUpdate, asnap.snapInit, asnap.enabledSnap, c)
    ap.ripeStakerPoints += self._indexDelta(ap.lastUpdate, asnap.snapInit, asnap.stakerIndexSnap, ib.assetStakerIndex, ib.stakersPointsAlloc, ib.assetIndexEnabledBlocks, c, self.frozenAssetStaker[_asset])
    ap.ripeVotePoints += self._indexDelta(ap.lastUpdate, asnap.snapInit, asnap.voterIndexSnap, ib.assetVoterIndex, ib.voterPointsAlloc, ib.assetIndexEnabledBlocks, c, self.frozenAssetVoter[_asset])
    ap.ripeGenPoints += ap.lastUsdValue * enabledDelta
    ap.balancePoints += ap.lastBalance * enabledDelta
    ap.lastUpdate = block.number

    # user points
    up: UserDepositPoints = empty(UserDepositPoints)
    if _user != empty(address):
        up = p.userPoints
        us: EnabledSnap = self.userDepositSnap[_user][_vaultId][_asset]
        enabledDelta = self._enabledDelta(up.lastUpdate, us.snapInit, us.enabledSnap, c)
        up.balancePoints += up.lastBalance * enabledDelta
        up.lastUpdate = block.number

    return up, ap, gp, nextSnaps


# borrow points


@view
@external
def previewBorrow(_mc: address, _ledger: address, _user: address) -> (BorrowPoints, BorrowPoints, uint256):
    c: EnabledClockBundle = staticcall MissionControl(_mc).getEnabledClockBundle()
    self._assertArmed(_mc, c.activationBlock)
    p: BorrowPointsBundle = staticcall Ledger(_ledger).getBorrowPointsBundle(_user)
    enabledNow: uint256 = self._peekEnabledAt(c, block.number) # next snap

    # global points
    globalPoints: BorrowPoints = p.globalPoints
    gs: EnabledSnap = self.globalBorrowSnap
    globalPoints.points += globalPoints.lastPrincipal * self._enabledDelta(globalPoints.lastUpdate, gs.snapInit, gs.enabledSnap, c)
    globalPoints.lastUpdate = block.number

    # if no user, return global points
    if _user == empty(address):
        return empty(BorrowPoints), globalPoints, enabledNow

    # user points
    userPoints: BorrowPoints = p.userPoints
    us: EnabledSnap = self.userBorrowSnap[_user]
    userPoints.points += userPoints.lastPrincipal * self._enabledDelta(userPoints.lastUpdate, us.snapInit, us.enabledSnap, c)
    userPoints.lastUpdate = block.number

    # normalize user debt -- reduce risk of integer overflow
    userDebt: uint256 = p.userDebtPrincipal
    if userDebt != 0:
        userDebt = userDebt // EIGHTEEN_DECIMALS

    # update `lastPrincipal`
    globalPoints.lastPrincipal -= userPoints.lastPrincipal
    globalPoints.lastPrincipal += userDebt
    userPoints.lastPrincipal = userDebt

    return userPoints, globalPoints, enabledNow


###############
# Lazy Bridge #
###############


@pure
@internal
def _peekEnabledAt(_c: EnabledClockBundle, _block: uint256) -> uint256:
    # caller guarantees `_block >= _c.enabledClockBlock` (current enable segment)
    if _c.arePointsEnabled:
        return _c.enabledBlocks + (_block - _c.enabledClockBlock)
    return _c.enabledBlocks


@view
@internal
def _enabledDelta(
    _lastUpdate: uint256,
    _snapInit: bool,
    _enabledSnap: uint256,
    _c: EnabledClockBundle,
) -> uint256:
    enabledNow: uint256 = self._peekEnabledAt(_c, block.number)

    # first save: no credit
    if _lastUpdate == 0:
        return 0

    # snapshotted record: enabled blocks since the snapshot
    if _snapInit:
        return enabledNow - _enabledSnap

    # legacy record (never snapshotted)
    activationBlock: uint256 = self.activationBlock
    if _lastUpdate <= activationBlock:
        # everything since activation, plus one leftover window at the arm-time flag
        delta: uint256 = enabledNow
        if _lastUpdate < activationBlock and self.frozenArePointsEnabled:
            delta += activationBlock - _lastUpdate
        return delta

    # persisted past activation by an old Lootbox: it wrote through `_lastUpdate`
    if _lastUpdate >= _c.enabledClockBlock:
        return enabledNow - self._peekEnabledAt(_c, _lastUpdate)

    # before the current enable segment: credit only the current segment
    return enabledNow - _c.enabledBlocks


@view
@internal
def _indexDelta(
    _lastUpdate: uint256,
    _snapInit: bool,
    _indexSnap: uint256,
    _storedIndex: uint256,
    _rate: uint256,
    _indexEnabledBlocks: uint256,
    _c: EnabledClockBundle,
    _frozenRate: uint256,
) -> uint256:
    enabledNow: uint256 = self._peekEnabledAt(_c, block.number)
    indexNow: uint256 = _storedIndex + _rate * (enabledNow - _indexEnabledBlocks)

    # first save: no credit
    if _lastUpdate == 0:
        return 0

    # snapshotted record: index growth since the snapshot
    if _snapInit:
        return indexNow - _indexSnap

    # legacy record (never snapshotted)
    activationBlock: uint256 = self.activationBlock
    if _lastUpdate <= activationBlock:
        # everything since activation, plus one leftover window at the arm-time rate
        delta: uint256 = indexNow
        if _lastUpdate < activationBlock and self.frozenArePointsEnabled:
            delta += _frozenRate * (activationBlock - _lastUpdate)
        return delta

    # persisted past activation by an old Lootbox: it wrote through `_lastUpdate`
    if _lastUpdate >= _c.enabledClockBlock:
        enabledAt: uint256 = self._peekEnabledAt(_c, _lastUpdate)
        if enabledAt >= _indexEnabledBlocks:
            return indexNow - (_storedIndex + _rate * (enabledAt - _indexEnabledBlocks))

    # before the current index segment: credit only the current segment (the current rate
    # segment within the current enable segment), never anything the old Lootbox already wrote
    return _rate * (enabledNow - max(_indexEnabledBlocks, _c.enabledBlocks))


###########
# Commits #
###########


# The current HQ Lootbox (id 16) commits exactly the next snaps that `previewDeposit` /
# `previewBorrow` returned for the write it just persisted. Views never reach here.


@external
def commitDepositSnaps(_user: address, _vaultId: uint256, _asset: address, _snaps: DepositSnaps):
    assert msg.sender == addys._getLootboxAddr() # dev: no perms
    assert self.activationBlock != 0 # dev: not armed
    self.globalDepositSnap = IndexSnap(
        snapInit=True,
        stakerIndexSnap=_snaps.globalStakerIndex,
        voterIndexSnap=_snaps.globalVoterIndex,
        enabledSnap=_snaps.enabledBlocks,
    )
    self.assetDepositSnap[_vaultId][_asset] = IndexSnap(
        snapInit=True,
        stakerIndexSnap=_snaps.assetStakerIndex,
        voterIndexSnap=_snaps.assetVoterIndex,
        enabledSnap=_snaps.enabledBlocks,
    )
    if _user != empty(address):
        self.userDepositSnap[_user][_vaultId][_asset] = EnabledSnap(snapInit=True, enabledSnap=_snaps.enabledBlocks)


@external
def commitBorrowSnaps(_user: address, _enabledSnap: uint256):
    assert msg.sender == addys._getLootboxAddr() # dev: no perms
    assert self.activationBlock != 0 # dev: not armed
    self.globalBorrowSnap = EnabledSnap(snapInit=True, enabledSnap=_enabledSnap)
    if _user != empty(address):
        self.userBorrowSnap[_user] = EnabledSnap(snapInit=True, enabledSnap=_enabledSnap)
