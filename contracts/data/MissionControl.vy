#
#       __  __  _   ____   ____  _  ____  __  _     ____  ____  __  _  _____ _____  ____  _    
#      |  \/  || | (_ (_` (_ (_`| |/ () \|  \| |   / (__`/ () \|  \| ||_   _|| () )/ () \| |__ 
#      |_|\/|_||_|.__)__).__)__)|_|\____/|_|\__|   \____)\____/|_|\__|  |_|  |_|\_\\____/|____|
#
#     ╔═══════════════════════════════════════════════════╗
#     ║  ** Mission Control **                            ║
#     ║  Stores all configuration data for Ripe protocol  ║
#     ╚═══════════════════════════════════════════════════╝
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
import interfaces.ConfigStructs as cs
from interfaces import Department
from interfaces import Defaults

interface Whitelist:
    def isUserAllowed(_user: address, _asset: address) -> bool: view

interface Vault:
    def vaultAssets(_index: uint256) -> address: view

interface VaultBook:
    def getAddr(_regId: uint256) -> address: view

interface Lootbox:
    def checkpointRipeRewardsBeforeConfigChange(): nonpayable

interface LootboxAccrual:
    def armedMissionControl() -> address: view
    def activationBlock() -> uint256: view

interface PriorMissionControl:
    def userDelegation(_user: address, _delegate: address) -> cs.ActionDelegation: view
    def ripeGovVaultConfig(_asset: address) -> cs.RipeGovVaultConfig: view
    def assetConfig(_asset: address) -> cs.AssetConfig: view
    def userConfig(_user: address) -> cs.UserConfig: view
    def canPerformLiteAction(_signer: address) -> bool: view
    def isRipeGovVaultId(_vaultId: uint256) -> bool: view
    def isStabVaultId(_vaultId: uint256) -> bool: view
    def liteSigners(_index: uint256) -> address: view
    def indexOfAsset(_asset: address) -> uint256: view
    def coreRipeGovVaultId() -> uint256: view
    def preferredStabVaultId() -> uint256: view
    def assets(_index: uint256) -> address: view
    def numLiteSigners() -> uint256: view
    def numAssets() -> uint256: view

flag ImportCategory:
    USER_CONFIGS
    USER_DELEGATIONS
    STAB_VAULT_IDS
    RIPE_GOV_VAULT_IDS
    VAULT_POINTERS
    LITE_SIGNERS
    ASSETS
    RIPE_GOV_VAULT_CONFIGS

# owner-bound import manifest: expected unique key counts for the categories that cannot be
# enumerated on the prior MissionControl (the enumerable ones are reconciled by readback)
struct ImportManifest:
    userConfigs: uint256
    userDelegations: uint256
    stabVaultIds: uint256
    ripeGovVaultIds: uint256
    ripeGovVaultConfigs: uint256

struct AssetIndex:
    stakerIndex: uint256
    voterIndex: uint256
    enabledBlocks: uint256
    gen: uint256

struct EnabledClockBundle:
    activationBlock: uint256
    arePointsEnabled: bool
    enabledBlocks: uint256
    enabledClockBlock: uint256

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

event MissionControlArmed:
    activationBlock: uint256
    clockGen: uint256

event MissionControlImportBatch:
    category: ImportCategory
    numKeys: uint256

event MissionControlImportFinalized:
    priorMissionControl: indexed(address)
    userConfigs: uint256
    userDelegations: uint256
    stabVaultIds: uint256
    ripeGovVaultIds: uint256
    ripeGovVaultConfigs: uint256
    priorAssets: uint256
    priorLiteSigners: uint256

struct TotalPointsAllocs:
    stakersPointsAllocTotal: uint256
    voterPointsAllocTotal: uint256

struct TellerDepositConfig:
    canDepositGeneral: bool
    canDepositAsset: bool
    doesVaultSupportAsset: bool
    isUserAllowed: bool
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
    perUserMaxAssetsPerVault: uint256
    perUserMaxVaults: uint256
    canAnyoneDeposit: bool
    minDepositBalance: uint256

struct TellerWithdrawConfig:
    canWithdrawGeneral: bool
    canWithdrawAsset: bool
    isUserAllowed: bool
    canWithdrawForUser: bool
    minDepositBalance: uint256

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

struct RedeemCollateralConfig:
    canRedeemCollateralGeneral: bool
    canRedeemCollateralAsset: bool
    isUserAllowed: bool
    ltvPaybackBuffer: uint256
    canAnyoneDeposit: bool

struct AuctionBuyConfig:
    canBuyInAuctionGeneral: bool
    canBuyInAuctionAsset: bool
    isUserAllowed: bool
    canAnyoneDeposit: bool

struct GenLiqConfig:
    canLiquidate: bool
    keeperFeeRatio: uint256
    minKeeperFee: uint256
    maxKeeperFee: uint256
    ltvPaybackBuffer: uint256
    genAuctionParams: cs.AuctionParams
    priorityLiqAssetVaults: DynArray[VaultData, PRIORITY_VAULT_DATA]
    priorityStabVaults: DynArray[VaultData, PRIORITY_VAULT_DATA]

struct VaultData:
    vaultId: uint256
    vaultAddr: address
    asset: address

struct AssetLiqConfig:
    hasConfig: bool
    shouldBurnAsPayment: bool
    shouldTransferToEndaoment: bool
    shouldSwapInStabPools: bool
    shouldAuctionInstantly: bool
    customAuctionParams: cs.AuctionParams
    specialStabPool: VaultData

struct StabPoolClaimsConfig:
    canClaimInStabPoolGeneral: bool
    canClaimInStabPoolAsset: bool
    canClaimFromStabPoolForUser: bool
    isUserAllowed: bool
    rewardsLockDuration: uint256
    ripePerDollarClaimed: uint256

struct StabPoolRedemptionsConfig:
    canRedeemInStabPoolGeneral: bool
    canRedeemInStabPoolAsset: bool
    isUserAllowed: bool
    canAnyoneDeposit: bool

struct ClaimLootConfig:
    canClaimLoot: bool
    canClaimLootForUser: bool
    autoStakeRatio: uint256
    rewardsLockDuration: uint256

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

struct PriceConfig:
    staleTime: uint256
    priorityPriceSourceIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]

struct PurchaseRipeBondConfig:
    asset: address
    amountPerEpoch: uint256
    canBond: bool
    minRipePerUnit: uint256
    maxRipePerUnit: uint256
    maxRipePerUnitLockBonus: uint256
    epochLength: uint256
    shouldAutoRestart: bool
    restartDelayBlocks: uint256
    minLockDuration: uint256
    maxLockDuration: uint256
    canAnyoneBondForUser: bool
    isUserAllowed: bool

struct DynamicBorrowRateConfig:
    minDynamicRateBoost: uint256
    maxDynamicRateBoost: uint256
    increasePerDangerBlock: uint256
    maxBorrowRate: uint256

# global cs
genConfig: public(cs.GenConfig)
genDebtConfig: public(cs.GenDebtConfig)
hrConfig: public(cs.HrConfig)
ripeBondConfig: public(cs.RipeBondConfig)

# asset cs
assetConfig: public(HashMap[address, cs.AssetConfig]) # asset -> cs
assets: public(HashMap[uint256, address]) # index -> asset
indexOfAsset: public(HashMap[address, uint256]) # asset -> index
numAssets: public(uint256) # num assets

# user cs
userConfig: public(HashMap[address, cs.UserConfig]) # user -> cs
userDelegation: public(HashMap[address, HashMap[address, cs.ActionDelegation]]) # user -> delegate -> cs

# ripe rewards
rewardsConfig: public(cs.RipeRewardsConfig)
totalPointsAllocs: public(TotalPointsAllocs)

# vault cs
coreRipeGovVaultId: public(uint256)
preferredStabVaultId: public(uint256)
isStabVaultId: public(HashMap[uint256, bool])
ripeGovVaultConfig: public(HashMap[address, cs.RipeGovVaultConfig]) # asset -> cs
priorityLiqAssetVaults: public(DynArray[cs.VaultLite, PRIORITY_VAULT_DATA])
priorityStabVaults: public(DynArray[cs.VaultLite, PRIORITY_VAULT_DATA])

# lite signers (iterable)
liteSigners: public(HashMap[uint256, address]) # index -> signer
indexOfLiteSigner: public(HashMap[address, uint256]) # signer -> index
numLiteSigners: public(uint256)

# other
priorityPriceSourceIds: public(DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES])
underscoreRegistry: public(address)
trainingWheels: public(address)
shouldCheckLastTouch: public(bool)
isRipeGovVaultId: public(HashMap[uint256, bool])

# lootbox point indexes (armed accounting)
activationBlock: public(uint256)
clockGen: public(uint256)
enabledBlocks: public(uint256)
enabledClockBlock: public(uint256)
globalStakerIndex: public(uint256)
globalVoterIndex: public(uint256)
globalIndexEnabledBlocks: public(uint256)
assetIndexes: public(HashMap[address, AssetIndex]) # asset -> index row

# import from prior mission control
importedCategories: ImportCategory
isImportFinalized: public(bool)
importedUserConfigs: public(uint256)
importedUserDelegations: public(uint256)
importedStabVaultIds: public(uint256)
importedRipeGovVaultIds: public(uint256)
importedRipeGovVaultConfigs: public(uint256)
didImportUserConfig: HashMap[address, bool]
didImportUserDelegation: HashMap[address, HashMap[address, bool]]
didImportStabVaultId: HashMap[uint256, bool]
didImportRipeGovVaultId: HashMap[uint256, bool]
didImportRipeGovVaultConfig: HashMap[address, bool]
didImportAsset: HashMap[address, bool]

LOOTBOX_ACCRUAL: public(immutable(address))
PRIOR_MISSION_CONTROL: public(immutable(address))

MAX_IMPORT_BATCH: constant(uint256) = 50
# an asset copy rewrites ~25 storage slots (cs.AssetConfig) per key: keep one batch well inside an L2 tx budget
MAX_ASSET_IMPORT_BATCH: constant(uint256) = 10
MAX_IMPORT_WALK: constant(uint256) = 100 # prior asset / lite signer readback at finalize
MAX_VAULTS_PER_ASSET: constant(uint256) = 10
MAX_PRIORITY_PRICE_SOURCES: constant(uint256) = 10
PRIORITY_VAULT_DATA: constant(uint256) = 20
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%


@deploy
def __init__(_ripeHq: address, _defaults: address, _lootboxAccrual: address, _priorMissionControl: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting

    assert _lootboxAccrual != empty(address) # dev: invalid lootbox accrual
    LOOTBOX_ACCRUAL = _lootboxAccrual
    PRIOR_MISSION_CONTROL = _priorMissionControl # bound once; empty skips the import step
    self.enabledClockBlock = block.number

    self.numAssets = 1 # not using 0 index
    self.numLiteSigners = 1 # not using 0 index, 0 means "not in list"
    self.preferredStabVaultId = 1
    self.isStabVaultId[1] = True
    self.coreRipeGovVaultId = 2
    self.isRipeGovVaultId[2] = True

    # defaults
    if _defaults != empty(address):
        self.genConfig = staticcall Defaults(_defaults).genConfig()
        self.genDebtConfig = staticcall Defaults(_defaults).genDebtConfig()
        self.hrConfig = staticcall Defaults(_defaults).hrConfig()
        self.ripeBondConfig = staticcall Defaults(_defaults).ripeBondConfig()
        self.rewardsConfig = staticcall Defaults(_defaults).rewardsConfig()
        self.underscoreRegistry = staticcall Defaults(_defaults).underscoreRegistry()
        self.trainingWheels = staticcall Defaults(_defaults).trainingWheels()
        self.shouldCheckLastTouch = staticcall Defaults(_defaults).shouldCheckLastTouch()

        ripeGovVaultConfigs: DynArray[cs.RipeGovVaultConfigEntry, 5] = staticcall Defaults(_defaults).ripeGovVaultConfigs()
        for entry: cs.RipeGovVaultConfigEntry in ripeGovVaultConfigs:
            self.ripeGovVaultConfig[entry.asset] = entry.config

        # asset configs
        assetConfigs: DynArray[cs.AssetConfigEntry, 50] = staticcall Defaults(_defaults).assetConfigs()
        for entry: cs.AssetConfigEntry in assetConfigs:
            self._setAssetConfig(entry.asset, entry.config)

        # priority lists
        self.priorityLiqAssetVaults = staticcall Defaults(_defaults).priorityLiqAssetVaults()
        self.priorityStabVaults = staticcall Defaults(_defaults).priorityStabVaults()
        for vault: cs.VaultLite in self.priorityStabVaults:
            if vault.vaultId != 0:
                self.isStabVaultId[vault.vaultId] = True
        self.priorityPriceSourceIds = staticcall Defaults(_defaults).priorityPriceSourceIds()

        # lite signers
        liteSigners: DynArray[address, 10] = staticcall Defaults(_defaults).liteSigners()
        for signer: address in liteSigners:
            self._addLiteSigner(signer)


#################
# Global Config #
#################


@external
def setGeneralConfig(_config: cs.GenConfig):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.genConfig = _config


@external
def setGeneralDebtConfig(_config: cs.GenDebtConfig):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.genDebtConfig = _config


@external
def setHrConfig(_config: cs.HrConfig):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.hrConfig = _config


@external
def setRipeBondConfig(_config: cs.RipeBondConfig):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.ripeBondConfig = _config


################
# Asset Config #
################


@external
def setAssetConfig(_asset: address, _config: cs.AssetConfig):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self._setAssetConfig(_asset, _config)


@internal
def _setAssetConfig(_asset: address, _config: cs.AssetConfig):
    # armed: settle the point indexes at the old rates before the new allocs become visible
    if self.activationBlock != 0:
        prevStakersPointsAlloc: uint256 = self.assetConfig[_asset].stakersPointsAlloc
        prevVoterPointsAlloc: uint256 = self.assetConfig[_asset].voterPointsAlloc
        if prevStakersPointsAlloc != _config.stakersPointsAlloc or prevVoterPointsAlloc != _config.voterPointsAlloc:
            self._settleGlobalIndexes()
            self._settleAssetIndexes(_asset, prevStakersPointsAlloc, prevVoterPointsAlloc)

    self._updatePointsAllocs(_asset, _config.stakersPointsAlloc, _config.voterPointsAlloc) # do first!
    self.assetConfig[_asset] = _config

    # monotonic because retired stability pools can still hold user balances.
    if _config.specialStabPoolId != 0:
        self.isStabVaultId[_config.specialStabPoolId] = True

    # register asset (if necessary)
    if self.indexOfAsset[_asset] == 0:
        self._registerAsset(_asset)


# asset registration


@internal
def _registerAsset(_asset: address):
    aid: uint256 = self.numAssets
    self.assets[aid] = _asset
    self.indexOfAsset[_asset] = aid
    self.numAssets = aid + 1


@external
def deregisterAsset(_asset: address) -> bool:
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms

    numAssets: uint256 = self.numAssets
    if numAssets == 0:
        return False

    targetIndex: uint256 = self.indexOfAsset[_asset]
    if targetIndex == 0:
        return False

    assert self.assetConfig[_asset].stakersPointsAlloc == 0 and self.assetConfig[_asset].voterPointsAlloc == 0 # dev: active points alloc

    # update data
    lastIndex: uint256 = numAssets - 1
    self.numAssets = lastIndex
    self.indexOfAsset[_asset] = 0

    # get last item, replace the removed item
    if targetIndex != lastIndex:
        lastItem: address = self.assets[lastIndex]
        self.assets[targetIndex] = lastItem
        self.indexOfAsset[lastItem] = targetIndex

    return True


###############
# User Config #
###############


@external
def setUserConfig(_user: address, _config: cs.UserConfig):
    assert addys._isSwitchboardAddr(msg.sender) or msg.sender == addys._getTellerAddr() # dev: no perms
    self.userConfig[_user] = _config


@external
def setUserDelegation(_user: address, _delegate: address, _config: cs.ActionDelegation):
    assert addys._isSwitchboardAddr(msg.sender) or msg.sender == addys._getTellerAddr() # dev: no perms
    self.userDelegation[_user][_delegate] = _config


##################
# Rewards Config #
##################


@external
def setRipeRewardsConfig(_config: cs.RipeRewardsConfig):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms

    # armed: 1) checkpoint rewards at the old rate / allocs, 2) advance the enabled clock, 3) write
    if self.activationBlock != 0:
        prev: cs.RipeRewardsConfig = self.rewardsConfig
        if (
            prev.ripePerBlock != _config.ripePerBlock or
            prev.borrowersAlloc != _config.borrowersAlloc or
            prev.stakersAlloc != _config.stakersAlloc or
            prev.votersAlloc != _config.votersAlloc or
            prev.genDepositorsAlloc != _config.genDepositorsAlloc
        ):
            extcall Lootbox(addys._getLootboxAddr()).checkpointRipeRewardsBeforeConfigChange()
        if prev.arePointsEnabled != _config.arePointsEnabled:
            self._advanceEnabledClock(prev.arePointsEnabled)

    self.rewardsConfig = _config


# points allocs


@internal
def _updatePointsAllocs(_asset: address, _newStakersPointsAlloc: uint256, _newVoterPointsAlloc: uint256):
    totalPointsAllocs: TotalPointsAllocs = self.totalPointsAllocs

    # remove old allocs
    prevConfig: cs.AssetConfig = self.assetConfig[_asset]
    totalPointsAllocs.stakersPointsAllocTotal -= prevConfig.stakersPointsAlloc
    totalPointsAllocs.voterPointsAllocTotal -= prevConfig.voterPointsAlloc

    # add new allocs
    totalPointsAllocs.stakersPointsAllocTotal += _newStakersPointsAlloc
    totalPointsAllocs.voterPointsAllocTotal += _newVoterPointsAlloc
    self.totalPointsAllocs = totalPointsAllocs


#################
# Point Indexes #
#################


# enabled-block clock


@view
@internal
def _peekEnabledBlocks() -> uint256:
    if self.rewardsConfig.arePointsEnabled:
        return self.enabledBlocks + (block.number - self.enabledClockBlock)
    return self.enabledBlocks


@internal
def _advanceEnabledClock(_wasEnabled: bool):
    if _wasEnabled:
        self.enabledBlocks += block.number - self.enabledClockBlock
    self.enabledClockBlock = block.number


# settle indexes (before a rate change)


@internal
def _settleGlobalIndexes():
    enabled: uint256 = self._peekEnabledBlocks()
    indexEnabled: uint256 = self.globalIndexEnabledBlocks
    if enabled != indexEnabled:
        totalPointsAllocs: TotalPointsAllocs = self.totalPointsAllocs
        self.globalStakerIndex += totalPointsAllocs.stakersPointsAllocTotal * (enabled - indexEnabled)
        self.globalVoterIndex += totalPointsAllocs.voterPointsAllocTotal * (enabled - indexEnabled)
        self.globalIndexEnabledBlocks = enabled


@internal
def _settleAssetIndexes(_asset: address, _prevStakersAlloc: uint256, _prevVoterAlloc: uint256):
    enabled: uint256 = self._peekEnabledBlocks()
    row: AssetIndex = self.assetIndexes[_asset]
    if row.gen != self.clockGen:
        # rows from before this activation are inert: restart from zero at activation
        row = AssetIndex(stakerIndex=0, voterIndex=0, enabledBlocks=0, gen=self.clockGen)
    row.stakerIndex += _prevStakersAlloc * (enabled - row.enabledBlocks)
    row.voterIndex += _prevVoterAlloc * (enabled - row.enabledBlocks)
    row.enabledBlocks = enabled
    self.assetIndexes[_asset] = row


# arm


@external
def arm():
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert self.activationBlock == 0 # dev: already armed
    if PRIOR_MISSION_CONTROL != empty(address):
        # the import must have been finalized (sealed and reconciled against the prior), and the
        # prior must still be the live MissionControl this one replaces
        assert self.isImportFinalized # dev: import not finalized
        assert PRIOR_MISSION_CONTROL == addys._getMissionControlAddr() # dev: prior not live

    # the accrual must have been armed against this MissionControl in this same block
    assert staticcall LootboxAccrual(LOOTBOX_ACCRUAL).armedMissionControl() == self # dev: accrual not bound
    assert staticcall LootboxAccrual(LOOTBOX_ACCRUAL).activationBlock() == block.number # dev: accrual not armed

    clockGen: uint256 = self.clockGen + 1
    self.clockGen = clockGen
    self.globalStakerIndex = 0
    self.globalVoterIndex = 0
    self.globalIndexEnabledBlocks = 0
    self.enabledBlocks = 0
    self.enabledClockBlock = block.number
    self.activationBlock = block.number
    log MissionControlArmed(activationBlock=block.number, clockGen=clockGen)


# peeks


@view
@external
def peekEnabledBlocks() -> uint256:
    return self._peekEnabledBlocks()


@view
@external
def peekGlobalIndexes() -> (uint256, uint256):
    enabled: uint256 = self._peekEnabledBlocks() - self.globalIndexEnabledBlocks
    totalPointsAllocs: TotalPointsAllocs = self.totalPointsAllocs
    return (
        self.globalStakerIndex + totalPointsAllocs.stakersPointsAllocTotal * enabled,
        self.globalVoterIndex + totalPointsAllocs.voterPointsAllocTotal * enabled,
    )


@view
@external
def peekAssetIndexes(_asset: address) -> (uint256, uint256):
    row: AssetIndex = self._getLiveAssetIndex(_asset)
    enabled: uint256 = self._peekEnabledBlocks() - row.enabledBlocks
    assetConfig: cs.AssetConfig = self.assetConfig[_asset]
    return (
        row.stakerIndex + assetConfig.stakersPointsAlloc * enabled,
        row.voterIndex + assetConfig.voterPointsAlloc * enabled,
    )


@view
@internal
def _getLiveAssetIndex(_asset: address) -> AssetIndex:
    row: AssetIndex = self.assetIndexes[_asset]
    if row.gen != self.clockGen:
        return empty(AssetIndex)
    return row


@view
@external
def getEnabledClockBundle() -> EnabledClockBundle:
    return EnabledClockBundle(
        activationBlock=self.activationBlock,
        arePointsEnabled=self.rewardsConfig.arePointsEnabled,
        enabledBlocks=self.enabledBlocks,
        enabledClockBlock=self.enabledClockBlock,
    )


@view
@external
def getPointsIndexBundle(_asset: address) -> PointsIndexBundle:
    totalPointsAllocs: TotalPointsAllocs = self.totalPointsAllocs
    assetConfig: cs.AssetConfig = self.assetConfig[_asset]
    row: AssetIndex = self._getLiveAssetIndex(_asset)
    return PointsIndexBundle(
        activationBlock=self.activationBlock,
        arePointsEnabled=self.rewardsConfig.arePointsEnabled,
        enabledBlocks=self.enabledBlocks,
        enabledClockBlock=self.enabledClockBlock,
        globalStakerIndex=self.globalStakerIndex,
        globalVoterIndex=self.globalVoterIndex,
        globalIndexEnabledBlocks=self.globalIndexEnabledBlocks,
        stakersPointsAllocTotal=totalPointsAllocs.stakersPointsAllocTotal,
        voterPointsAllocTotal=totalPointsAllocs.voterPointsAllocTotal,
        assetStakerIndex=row.stakerIndex,
        assetVoterIndex=row.voterIndex,
        assetIndexEnabledBlocks=row.enabledBlocks,
        stakersPointsAlloc=assetConfig.stakersPointsAlloc,
        voterPointsAlloc=assetConfig.voterPointsAlloc,
    )


##########
# Import #
##########


@view
@external
def priorMC() -> address:
    return PRIOR_MISSION_CONTROL


@view
@external
def lootboxAccrual() -> address:
    return LOOTBOX_ACCRUAL


# Replacement flow (Switchboard-gated, reads the immutable prior only):
#   importFromPrior(category, keys...) in batches of <= 50, any number of times, until finalize
#   finalizeImport(manifest): one-time seal -- category flags complete + manifest counts +
#     symmetric readback reconciliation (prior assets / lite signers / pointers == candidate's,
#     both membership AND counts). After it, no further import can touch this contract.
#   arm(): requires the sealed finalize when a prior is bound, and the prior must still be the
#     live MissionControl at RipeHq id 5


@external
def importFromPrior(
    _category: ImportCategory,
    _addressKeys: DynArray[address, MAX_IMPORT_BATCH],
    _vaultIds: DynArray[uint256, MAX_IMPORT_BATCH],
    _delegates: DynArray[address, MAX_IMPORT_BATCH],
):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert PRIOR_MISSION_CONTROL != empty(address) # dev: no prior mission control
    assert not self.isImportFinalized # dev: import finalized
    assert self.activationBlock == 0 # dev: already armed
    prior: PriorMissionControl = PriorMissionControl(PRIOR_MISSION_CONTROL)

    numKeys: uint256 = 0
    if _category == ImportCategory.USER_CONFIGS:
        numKeys = len(_addressKeys)
        for user: address in _addressKeys:
            self.userConfig[user] = staticcall prior.userConfig(user)
            if not self.didImportUserConfig[user]:
                self.didImportUserConfig[user] = True
                self.importedUserConfigs += 1

    elif _category == ImportCategory.USER_DELEGATIONS:
        numKeys = len(_addressKeys)
        assert len(_delegates) == numKeys # dev: delegation pairs
        for i: uint256 in range(MAX_IMPORT_BATCH):
            if i >= numKeys:
                break
            user: address = _addressKeys[i]
            delegate: address = _delegates[i]
            self.userDelegation[user][delegate] = staticcall prior.userDelegation(user, delegate)
            if not self.didImportUserDelegation[user][delegate]:
                self.didImportUserDelegation[user][delegate] = True
                self.importedUserDelegations += 1

    elif _category == ImportCategory.STAB_VAULT_IDS:
        numKeys = len(_vaultIds)
        for vaultId: uint256 in _vaultIds:
            # monotonic: retired pools stay stab ids; only ids the prior confirms count
            if staticcall prior.isStabVaultId(vaultId):
                self.isStabVaultId[vaultId] = True
                if not self.didImportStabVaultId[vaultId]:
                    self.didImportStabVaultId[vaultId] = True
                    self.importedStabVaultIds += 1

    elif _category == ImportCategory.RIPE_GOV_VAULT_IDS:
        numKeys = len(_vaultIds)
        for vaultId: uint256 in _vaultIds:
            if staticcall prior.isRipeGovVaultId(vaultId):
                self.isRipeGovVaultId[vaultId] = True
                if not self.didImportRipeGovVaultId[vaultId]:
                    self.didImportRipeGovVaultId[vaultId] = True
                    self.importedRipeGovVaultIds += 1

    elif _category == ImportCategory.VAULT_POINTERS:
        coreRipeGovVaultId: uint256 = staticcall prior.coreRipeGovVaultId()
        if coreRipeGovVaultId != 0:
            self.coreRipeGovVaultId = coreRipeGovVaultId
            self.isRipeGovVaultId[coreRipeGovVaultId] = True
        preferredStabVaultId: uint256 = staticcall prior.preferredStabVaultId()
        if preferredStabVaultId != 0:
            self.preferredStabVaultId = preferredStabVaultId
            self.isStabVaultId[preferredStabVaultId] = True

    elif _category == ImportCategory.LITE_SIGNERS:
        numKeys = len(_addressKeys)
        for signer: address in _addressKeys:
            # mirrors the prior both ways so a revocation on the prior can be replayed
            if staticcall prior.canPerformLiteAction(signer):
                self._addLiteSigner(signer)
            else:
                self._removeLiteSigner(signer)

    elif _category == ImportCategory.ASSETS:
        numKeys = len(_addressKeys)
        assert numKeys <= MAX_ASSET_IMPORT_BATCH # dev: asset batch too large
        for asset: address in _addressKeys:
            assert staticcall prior.indexOfAsset(asset) != 0 # dev: asset not on prior
            # the prior (live) config always wins; registers the asset when Defaults missed it
            self._setAssetConfig(asset, staticcall prior.assetConfig(asset))
            self.didImportAsset[asset] = True

    elif _category == ImportCategory.RIPE_GOV_VAULT_CONFIGS:
        numKeys = len(_addressKeys)
        for asset: address in _addressKeys:
            self.ripeGovVaultConfig[asset] = staticcall prior.ripeGovVaultConfig(asset)
            if not self.didImportRipeGovVaultConfig[asset]:
                self.didImportRipeGovVaultConfig[asset] = True
                self.importedRipeGovVaultConfigs += 1

    else:
        raise "invalid category"

    self.importedCategories |= _category
    log MissionControlImportBatch(category=_category, numKeys=numKeys)


@external
def finalizeImport(_manifest: ImportManifest):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert PRIOR_MISSION_CONTROL != empty(address) # dev: no prior mission control
    assert not self.isImportFinalized # dev: import finalized
    prior: PriorMissionControl = PriorMissionControl(PRIOR_MISSION_CONTROL)

    # every category touched or explicitly marked empty
    allCategories: ImportCategory = (
        ImportCategory.USER_CONFIGS | ImportCategory.USER_DELEGATIONS |
        ImportCategory.STAB_VAULT_IDS | ImportCategory.RIPE_GOV_VAULT_IDS |
        ImportCategory.VAULT_POINTERS | ImportCategory.LITE_SIGNERS |
        ImportCategory.ASSETS | ImportCategory.RIPE_GOV_VAULT_CONFIGS
    )
    assert self.importedCategories == allCategories # dev: import incomplete

    # owner-bound manifest for the categories that cannot be enumerated on the prior
    assert self.importedUserConfigs == _manifest.userConfigs # dev: user configs manifest
    assert self.importedUserDelegations == _manifest.userDelegations # dev: user delegations manifest
    assert self.importedStabVaultIds == _manifest.stabVaultIds # dev: stab vault ids manifest
    assert self.importedRipeGovVaultIds == _manifest.ripeGovVaultIds # dev: ripe gov vault ids manifest
    assert self.importedRipeGovVaultConfigs == _manifest.ripeGovVaultConfigs # dev: ripe gov vault configs manifest

    # readback reconciliation of everything the prior can enumerate (both directions)
    assert self.coreRipeGovVaultId == staticcall prior.coreRipeGovVaultId() # dev: core vault id drift
    assert self.preferredStabVaultId == staticcall prior.preferredStabVaultId() # dev: preferred stab id drift

    priorNumAssets: uint256 = staticcall prior.numAssets()
    assert priorNumAssets <= MAX_IMPORT_WALK + 1 # dev: too many prior assets
    priorAssets: uint256 = 0
    if priorNumAssets > 1:
        for i: uint256 in range(1, priorNumAssets, bound=MAX_IMPORT_WALK + 1):
            asset: address = staticcall prior.assets(i)
            if asset == empty(address):
                continue
            assert self.didImportAsset[asset] # dev: asset not imported
            priorAssets += 1

    # nothing registered here that the prior does not have (stale Defaults extras), and the
    # registries are the same size: membership both ways + equal counts = set equality
    numAssets: uint256 = self.numAssets
    assert numAssets <= MAX_IMPORT_WALK + 1 # dev: too many assets
    candidateAssets: uint256 = 0
    if numAssets > 1:
        for i: uint256 in range(1, numAssets, bound=MAX_IMPORT_WALK + 1):
            asset: address = self.assets[i]
            if asset != empty(address):
                assert staticcall prior.indexOfAsset(asset) != 0 # dev: asset not on prior
                candidateAssets += 1
    assert candidateAssets == priorAssets # dev: asset count drift

    priorNumLiteSigners: uint256 = staticcall prior.numLiteSigners()
    assert priorNumLiteSigners <= MAX_IMPORT_WALK + 1 # dev: too many prior lite signers
    priorLiteSigners: uint256 = 0
    if priorNumLiteSigners > 1:
        for i: uint256 in range(1, priorNumLiteSigners, bound=MAX_IMPORT_WALK + 1):
            signer: address = staticcall prior.liteSigners(i)
            if signer == empty(address):
                continue
            assert self.indexOfLiteSigner[signer] != 0 # dev: lite signer not imported
            priorLiteSigners += 1

    numLiteSigners: uint256 = self.numLiteSigners
    assert numLiteSigners <= MAX_IMPORT_WALK + 1 # dev: too many lite signers
    candidateLiteSigners: uint256 = 0
    if numLiteSigners > 1:
        for i: uint256 in range(1, numLiteSigners, bound=MAX_IMPORT_WALK + 1):
            signer: address = self.liteSigners[i]
            if signer != empty(address):
                assert staticcall prior.canPerformLiteAction(signer) # dev: lite signer not on prior
                candidateLiteSigners += 1
    assert candidateLiteSigners == priorLiteSigners # dev: lite signer count drift

    self.isImportFinalized = True
    log MissionControlImportFinalized(
        priorMissionControl=PRIOR_MISSION_CONTROL,
        userConfigs=_manifest.userConfigs,
        userDelegations=_manifest.userDelegations,
        stabVaultIds=_manifest.stabVaultIds,
        ripeGovVaultIds=_manifest.ripeGovVaultIds,
        ripeGovVaultConfigs=_manifest.ripeGovVaultConfigs,
        priorAssets=priorAssets,
        priorLiteSigners=priorLiteSigners,
    )


################
# Vault Config #
################


# core ripe gov vault id


@external
def setCoreRipeGovVaultId(_vaultId: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _vaultId != 0 # dev: invalid vault id
    self.isRipeGovVaultId[self.coreRipeGovVaultId] = True
    self.isRipeGovVaultId[_vaultId] = True
    self.coreRipeGovVaultId = _vaultId


# preferred stability pool vault id


@external
def setPreferredStabVaultId(_vaultId: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _vaultId != 0 # dev: invalid vault id
    self.preferredStabVaultId = _vaultId
    self.isStabVaultId[_vaultId] = True


# ripe gov vault


@external
def setRipeGovVaultConfig(
    _asset: address,
    _assetWeight: uint256,
    _shouldFreezeWhenBadDebt: bool,
    _lockTerms: cs.LockTerms,
):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.ripeGovVaultConfig[_asset] = cs.RipeGovVaultConfig(
        lockTerms=_lockTerms,
        assetWeight=_assetWeight,
        shouldFreezeWhenBadDebt=_shouldFreezeWhenBadDebt,
    )


# priority liq asset vaults


@external
def setPriorityLiqAssetVaults(_priorityLiqAssetVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.priorityLiqAssetVaults = _priorityLiqAssetVaults


# stability pool vaults


@external
def setPriorityStabVaults(_priorityStabVaults: DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.priorityStabVaults = _priorityStabVaults
    for vault: cs.VaultLite in _priorityStabVaults:
        if vault.vaultId != 0:
            self.isStabVaultId[vault.vaultId] = True


################
# Lite Signers #
################


@external
def setCanPerformLiteAction(_signer: address, _canDo: bool):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    if _canDo:
        self._addLiteSigner(_signer)
    else:
        self._removeLiteSigner(_signer)


@view
@external
def canPerformLiteAction(_signer: address) -> bool:
    return self.indexOfLiteSigner[_signer] != 0


# add lite signer


@internal
def _addLiteSigner(_signer: address):
    if self.indexOfLiteSigner[_signer] != 0:
        return
    idx: uint256 = self.numLiteSigners
    self.liteSigners[idx] = _signer
    self.indexOfLiteSigner[_signer] = idx
    self.numLiteSigners = idx + 1


# remove lite signer


@internal
def _removeLiteSigner(_signer: address):
    targetIndex: uint256 = self.indexOfLiteSigner[_signer]
    if targetIndex == 0:
        return

    lastIndex: uint256 = self.numLiteSigners - 1
    self.numLiteSigners = lastIndex
    self.indexOfLiteSigner[_signer] = 0

    # swap with last item if not already last
    if targetIndex != lastIndex:
        lastItem: address = self.liteSigners[lastIndex]
        self.liteSigners[targetIndex] = lastItem
        self.indexOfLiteSigner[lastItem] = targetIndex

    self.liteSigners[lastIndex] = empty(address)


#########
# Other #
#########


# training wheels


@external
def setTrainingWheels(_trainingWheels: address):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.trainingWheels = _trainingWheels


# underscore registry


@external
def setUnderscoreRegistry(_underscoreRegistry: address):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.underscoreRegistry = _underscoreRegistry


# price sources


@external
def setPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.priorityPriceSourceIds = _priorityIds


# should check last touch


@external
def setShouldCheckLastTouch(_shouldCheck: bool):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.shouldCheckLastTouch = _shouldCheck


###################
# Helpers / Views #
###################


# asset utils


@view
@external
def isSupportedAsset(_asset: address) -> bool:
    return self.indexOfAsset[_asset] != 0


@view
@external
def isSupportedAssetInVault(_vaultId: uint256, _asset: address) -> bool:
    return _vaultId in self.assetConfig[_asset].vaultIds


@view
@external
def getNumAssets() -> uint256:
    return self._getNumAssets()


@view
@internal
def _getNumAssets() -> uint256:
    numAssets: uint256 = self.numAssets
    if numAssets == 0:
        return 0
    return numAssets - 1


@view
@external
def getFirstVaultIdForAsset(_asset: address) -> uint256:
    vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET] = self.assetConfig[_asset].vaultIds
    if len(vaultIds) == 0:
        return 0
    return vaultIds[0]


# is user allowed


@view
@internal
def _isUserAllowed(_whitelist: address, _user: address, _asset: address) -> bool:
    isUserAllowed: bool = True 
    if _whitelist != empty(address):
        isUserAllowed = staticcall Whitelist(_whitelist).isUserAllowed(_user, _asset)
    return isUserAllowed


# auto stake lock duration


@view
@internal
def _getLockDuration(_minLockDuration: uint256, _maxLockDuration: uint256, _autoStakeDurationRatio: uint256) -> uint256:
    if _maxLockDuration <= _minLockDuration or _autoStakeDurationRatio == 0:
        return _minLockDuration
    durationRange: uint256 = _maxLockDuration - _minLockDuration
    return durationRange * _autoStakeDurationRatio // HUNDRED_PERCENT


# deposits


@view
@external
def getTellerDepositConfig(_vaultId: uint256, _asset: address, _user: address) -> TellerDepositConfig:
    assetConfig: cs.AssetConfig = self.assetConfig[_asset]
    genConfig: cs.GenConfig = self.genConfig
    return TellerDepositConfig(
        canDepositGeneral=genConfig.canDeposit,
        canDepositAsset=assetConfig.canDeposit,
        doesVaultSupportAsset=_vaultId in assetConfig.vaultIds,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _user, _asset),
        perUserDepositLimit=assetConfig.perUserDepositLimit,
        globalDepositLimit=assetConfig.globalDepositLimit,
        perUserMaxAssetsPerVault=genConfig.perUserMaxAssetsPerVault,
        perUserMaxVaults=genConfig.perUserMaxVaults,
        canAnyoneDeposit=self.userConfig[_user].canAnyoneDeposit,
        minDepositBalance=assetConfig.minDepositBalance,
    )


# withdrawals


@view
@external
def getTellerWithdrawConfig(_asset: address, _user: address, _caller: address) -> TellerWithdrawConfig:
    assetConfig: cs.AssetConfig = self.assetConfig[_asset]

    canWithdrawForUser: bool = True
    if _user != _caller:
        delegation: cs.ActionDelegation = self.userDelegation[_user][_caller]
        canWithdrawForUser = delegation.canWithdraw

    return TellerWithdrawConfig(
        canWithdrawGeneral=self.genConfig.canWithdraw,
        canWithdrawAsset=assetConfig.canWithdraw,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _user, _asset),
        canWithdrawForUser=canWithdrawForUser,
        minDepositBalance=assetConfig.minDepositBalance,
    )


# borrow


@view
@external
def getDebtTerms(_asset: address) -> cs.DebtTerms:
    return self.assetConfig[_asset].debtTerms


@view
@external
def getBorrowConfig(_user: address, _caller: address) -> BorrowConfig:
    genDebtConfig: cs.GenDebtConfig = self.genDebtConfig

    canBorrowForUser: bool = True
    if _user != _caller:
        delegation: cs.ActionDelegation = self.userDelegation[_user][_caller]
        canBorrowForUser = delegation.canBorrow

    return BorrowConfig(
        canBorrow=self.genConfig.canBorrow,
        canBorrowForUser=canBorrowForUser,
        numAllowedBorrowers=genDebtConfig.numAllowedBorrowers,
        maxBorrowPerInterval=genDebtConfig.maxBorrowPerInterval,
        numBlocksPerInterval=genDebtConfig.numBlocksPerInterval,
        perUserDebtLimit=genDebtConfig.perUserDebtLimit,
        globalDebtLimit=genDebtConfig.globalDebtLimit,
        minDebtAmount=genDebtConfig.minDebtAmount,
        isDaowryEnabled=genDebtConfig.isDaowryEnabled,
    )


@view
@external
def maxLtvDeviation() -> uint256:
    return self.genDebtConfig.maxLtvDeviation


# repay


@view
@external
def getRepayConfig(_user: address) -> RepayConfig:
    return RepayConfig(
        canRepay=self.genConfig.canRepay,
        canAnyoneRepayDebt=self.userConfig[_user].canAnyoneRepayDebt,
    )


# redeem collateral


@view
@external
def getRedeemCollateralConfig(_asset: address, _recipient: address) -> RedeemCollateralConfig:
    assetConfig: cs.AssetConfig = self.assetConfig[_asset]
    return RedeemCollateralConfig(
        canRedeemCollateralGeneral=self.genConfig.canRedeemCollateral,
        canRedeemCollateralAsset=assetConfig.canRedeemCollateral,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _recipient, _asset),
        ltvPaybackBuffer=self.genDebtConfig.ltvPaybackBuffer,
        canAnyoneDeposit=self.userConfig[_recipient].canAnyoneDeposit,
    )


@view
@external
def getLtvPaybackBuffer() -> uint256:
    return self.genDebtConfig.ltvPaybackBuffer


# auction purchases


@view
@external
def getAuctionBuyConfig(_asset: address, _recipient: address) -> AuctionBuyConfig:
    assetConfig: cs.AssetConfig = self.assetConfig[_asset]
    return AuctionBuyConfig(
        canBuyInAuctionGeneral=self.genConfig.canBuyInAuction,
        canBuyInAuctionAsset=assetConfig.canBuyInAuction,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _recipient, _asset),
        canAnyoneDeposit=self.userConfig[_recipient].canAnyoneDeposit,
    )


# general liquidation config


@view
@external
def getGenLiqConfig() -> GenLiqConfig:
    genDebtConfig: cs.GenDebtConfig = self.genDebtConfig
    vaultBook: address = addys._getVaultBookAddr()

    # priority liq asset vault data
    priorityLiqAssetVaults: DynArray[VaultData, PRIORITY_VAULT_DATA] = []
    for pData: cs.VaultLite in self.priorityLiqAssetVaults:
        vaultAddr: address = staticcall VaultBook(vaultBook).getAddr(pData.vaultId)
        priorityLiqAssetVaults.append(VaultData(vaultId=pData.vaultId, vaultAddr=vaultAddr, asset=pData.asset))

    # stability pool vault data
    priorityStabVaults: DynArray[VaultData, PRIORITY_VAULT_DATA] = []
    for pData: cs.VaultLite in self.priorityStabVaults:
        vaultAddr: address = staticcall VaultBook(vaultBook).getAddr(pData.vaultId)
        priorityStabVaults.append(VaultData(vaultId=pData.vaultId, vaultAddr=vaultAddr, asset=pData.asset))

    return GenLiqConfig(
        canLiquidate=self.genConfig.canLiquidate,
        keeperFeeRatio=genDebtConfig.keeperFeeRatio,
        minKeeperFee=genDebtConfig.minKeeperFee,
        maxKeeperFee=genDebtConfig.maxKeeperFee,
        ltvPaybackBuffer=genDebtConfig.ltvPaybackBuffer,
        genAuctionParams=genDebtConfig.genAuctionParams,
        priorityLiqAssetVaults=priorityLiqAssetVaults,
        priorityStabVaults=priorityStabVaults,
    )


@view
@external
def getGenAuctionParams() -> cs.AuctionParams:
    return self.genDebtConfig.genAuctionParams


# asset liquidation config


@view
@external
def getAssetLiqConfig(_asset: address) -> AssetLiqConfig:
    assetConfig: cs.AssetConfig = self.assetConfig[_asset]
    vaultBook: address = addys._getVaultBookAddr()

    # handle special stab pool
    specialStabPool: VaultData = empty(VaultData)
    if assetConfig.specialStabPoolId != 0:
        specialVaultAddr: address = staticcall VaultBook(vaultBook).getAddr(assetConfig.specialStabPoolId)
        if specialVaultAddr != empty(address):
            firstAsset: address = staticcall Vault(specialVaultAddr).vaultAssets(1) # get first asset
            if firstAsset != empty(address):
                specialStabPool = VaultData(
                    vaultId=assetConfig.specialStabPoolId,
                    vaultAddr=specialVaultAddr,
                    asset=firstAsset
                )

    return AssetLiqConfig(
        hasConfig=True,
        shouldBurnAsPayment=assetConfig.shouldBurnAsPayment,
        shouldTransferToEndaoment=assetConfig.shouldTransferToEndaoment,
        shouldSwapInStabPools=assetConfig.shouldSwapInStabPools,
        shouldAuctionInstantly=assetConfig.shouldAuctionInstantly,
        customAuctionParams=assetConfig.customAuctionParams,
        specialStabPool=specialStabPool,
    )


# stability pool claims


@view
@external
def getStabPoolClaimsConfig(_claimAsset: address, _claimer: address, _caller: address, _ripeToken: address) -> StabPoolClaimsConfig:
    assetConfig: cs.AssetConfig = self.assetConfig[_claimAsset]

    canClaimFromStabPoolForUser: bool = True
    if _claimer != _caller:
        delegation: cs.ActionDelegation = self.userDelegation[_claimer][_caller]
        canClaimFromStabPoolForUser = delegation.canClaimFromStabPool

    vaultConfig: cs.RipeGovVaultConfig = self.ripeGovVaultConfig[_ripeToken]
    rewardsConfig: cs.RipeRewardsConfig = self.rewardsConfig
    lockDuration: uint256 = self._getLockDuration(vaultConfig.lockTerms.minLockDuration, vaultConfig.lockTerms.maxLockDuration, rewardsConfig.autoStakeDurationRatio)

    return StabPoolClaimsConfig(
        canClaimInStabPoolGeneral=self.genConfig.canClaimInStabPool,
        canClaimInStabPoolAsset=assetConfig.canClaimInStabPool,
        canClaimFromStabPoolForUser=canClaimFromStabPoolForUser,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _claimer, _claimAsset),
        rewardsLockDuration=lockDuration,
        ripePerDollarClaimed=rewardsConfig.stabPoolRipePerDollarClaimed,
    )


# stability pool redemptions


@view
@external
def getStabPoolRedemptionsConfig(_asset: address, _recipient: address) -> StabPoolRedemptionsConfig:
    assetConfig: cs.AssetConfig = self.assetConfig[_asset]
    return StabPoolRedemptionsConfig(
        canRedeemInStabPoolGeneral=self.genConfig.canRedeemInStabPool,
        canRedeemInStabPoolAsset=assetConfig.canRedeemInStabPool,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _recipient, _asset),
        canAnyoneDeposit=self.userConfig[_recipient].canAnyoneDeposit,
    )


# loot claims


@view
@external
def getClaimLootConfig(_user: address, _caller: address, _ripeToken: address) -> ClaimLootConfig:
    canClaimLootForUser: bool = True
    if _user != _caller:
        delegation: cs.ActionDelegation = self.userDelegation[_user][_caller]
        canClaimLootForUser = delegation.canClaimLoot

    vaultConfig: cs.RipeGovVaultConfig = self.ripeGovVaultConfig[_ripeToken]
    rewardsConfig: cs.RipeRewardsConfig = self.rewardsConfig
    lockDuration: uint256 = self._getLockDuration(vaultConfig.lockTerms.minLockDuration, vaultConfig.lockTerms.maxLockDuration, rewardsConfig.autoStakeDurationRatio)

    return ClaimLootConfig(
        canClaimLoot=self.genConfig.canClaimLoot,
        canClaimLootForUser=canClaimLootForUser,
        autoStakeRatio=rewardsConfig.autoStakeRatio,
        rewardsLockDuration=lockDuration,
    )


# rewards config


@view
@external
def getRewardsConfig() -> RewardsConfig:
    rewardsConfig: cs.RipeRewardsConfig = self.rewardsConfig
    totalPointsAllocs: TotalPointsAllocs = self.totalPointsAllocs
    return RewardsConfig(
        arePointsEnabled=rewardsConfig.arePointsEnabled,
        ripePerBlock=rewardsConfig.ripePerBlock,
        borrowersAlloc=rewardsConfig.borrowersAlloc,
        stakersAlloc=rewardsConfig.stakersAlloc,
        votersAlloc=rewardsConfig.votersAlloc,
        genDepositorsAlloc=rewardsConfig.genDepositorsAlloc,
        stakersPointsAllocTotal=totalPointsAllocs.stakersPointsAllocTotal,
        voterPointsAllocTotal=totalPointsAllocs.voterPointsAllocTotal,
    )


# deposit points


@view
@external
def getDepositPointsConfig(_asset: address) -> DepositPointsConfig:
    assetConfig: cs.AssetConfig = self.assetConfig[_asset]
    return DepositPointsConfig(
        stakersPointsAlloc=assetConfig.stakersPointsAlloc,
        voterPointsAlloc=assetConfig.voterPointsAlloc,
        isNft=assetConfig.isNft,
    )


# price config


@view
@external
def getPriceConfig() -> PriceConfig:
    return PriceConfig(
        staleTime=self.genConfig.priceStaleTime,
        priorityPriceSourceIds=self.priorityPriceSourceIds,
    )


# ripe bond config


@view
@external
def getPurchaseRipeBondConfig(_user: address) -> PurchaseRipeBondConfig:
    bondConfig: cs.RipeBondConfig = self.ripeBondConfig
    vaultConfig: cs.RipeGovVaultConfig = self.ripeGovVaultConfig[addys._getRipeToken()]
    assetConfig: cs.AssetConfig = self.assetConfig[bondConfig.asset]
    return PurchaseRipeBondConfig(
        asset=bondConfig.asset,
        amountPerEpoch=bondConfig.amountPerEpoch,
        canBond=bondConfig.canBond,
        minRipePerUnit=bondConfig.minRipePerUnit,
        maxRipePerUnit=bondConfig.maxRipePerUnit,
        maxRipePerUnitLockBonus=bondConfig.maxRipePerUnitLockBonus,
        epochLength=bondConfig.epochLength,
        shouldAutoRestart=bondConfig.shouldAutoRestart,
        restartDelayBlocks=bondConfig.restartDelayBlocks,
        minLockDuration=vaultConfig.lockTerms.minLockDuration,
        maxLockDuration=vaultConfig.lockTerms.maxLockDuration,
        canAnyoneBondForUser=self.userConfig[_user].canAnyoneBondForUser,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _user, bondConfig.asset),
    )


# dynamic borrow rate config


@view
@external
def getDynamicBorrowRateConfig() -> DynamicBorrowRateConfig:
    genDebtConfig: cs.GenDebtConfig = self.genDebtConfig
    return DynamicBorrowRateConfig(
        minDynamicRateBoost=genDebtConfig.minDynamicRateBoost,
        maxDynamicRateBoost=genDebtConfig.maxDynamicRateBoost,
        increasePerDangerBlock=genDebtConfig.increasePerDangerBlock,
        maxBorrowRate=genDebtConfig.maxBorrowRate,
    )


# stale price time


@view
@external
def getPriceStaleTime() -> uint256:
    # used by some price sources
    return self.genConfig.priceStaleTime


# priority data


@view 
@external 
def getPriorityPriceSourceIds() -> DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]:
    return self.priorityPriceSourceIds


@view 
@external 
def getPriorityLiqAssetVaults() -> DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]:
    return self.priorityLiqAssetVaults


@view 
@external 
def getPriorityStabVaults() -> DynArray[cs.VaultLite, PRIORITY_VAULT_DATA]:
    return self.priorityStabVaults


# underscore helper


@view
@external
def doesUndyLegoHaveAccess(_wallet: address, _legoAddr: address) -> bool:
    config: cs.UserConfig = self.userConfig[_wallet]
    if not config.canAnyoneDeposit or not config.canAnyoneRepayDebt:
        return False

    delegation: cs.ActionDelegation = self.userDelegation[_wallet][_legoAddr]
    if not delegation.canWithdraw or not delegation.canBorrow or not delegation.canClaimLoot:
        return False
    
    return True
