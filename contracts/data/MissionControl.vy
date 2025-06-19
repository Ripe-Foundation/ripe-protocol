# @version 0.4.1
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

struct TellerWithdrawConfig:
    canWithdrawGeneral: bool
    canWithdrawAsset: bool
    isUserAllowed: bool
    canWithdrawForUser: bool

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
    autoStakeDurationRatio: uint256
    minLockDuration: uint256
    maxLockDuration: uint256

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
ripeGovVaultConfig: public(HashMap[address, cs.RipeGovVaultConfig]) # asset -> cs
stabClaimRewardsConfig: public(cs.StabClaimRewardsConfig)
priorityLiqAssetVaults: public(DynArray[cs.VaultLite, PRIORITY_VAULT_DATA])
priorityStabVaults: public(DynArray[cs.VaultLite, PRIORITY_VAULT_DATA])

# access
canPerformLiteAction: public(HashMap[address, bool]) # user -> canPerformLiteAction

# other
priorityPriceSourceIds: public(DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES])
underscoreRegistry: public(address)
shouldCheckLastTouch: public(bool)

MAX_VAULTS_PER_ASSET: constant(uint256) = 10
MAX_PRIORITY_PRICE_SOURCES: constant(uint256) = 10
PRIORITY_VAULT_DATA: constant(uint256) = 20


@deploy
def __init__(_ripeHq: address, _defaults: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting
    self.numAssets = 1 # not using 0 index

    # defaults
    if _defaults != empty(address):
        self.genConfig = staticcall Defaults(_defaults).genConfig()
        self.genDebtConfig = staticcall Defaults(_defaults).genDebtConfig()
        self.hrConfig = staticcall Defaults(_defaults).hrConfig()
        self.ripeBondConfig = staticcall Defaults(_defaults).ripeBondConfig()
        self.rewardsConfig = staticcall Defaults(_defaults).rewardsConfig()
        self.stabClaimRewardsConfig = staticcall Defaults(_defaults).stabClaimRewardsConfig()
        self.underscoreRegistry = staticcall Defaults(_defaults).underscoreRegistry()
        self.shouldCheckLastTouch = staticcall Defaults(_defaults).shouldCheckLastTouch()

        ripeGovVaultConfig: cs.RipeGovVaultConfig = staticcall Defaults(_defaults).ripeGovVaultConfig()
        if ripeGovVaultConfig.assetWeight != 0:
            self.ripeGovVaultConfig[addys._getRipeToken()] = ripeGovVaultConfig


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
    self._updatePointsAllocs(_asset, _config.stakersPointsAlloc, _config.voterPointsAlloc) # do first!
    self.assetConfig[_asset] = _config

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


################
# Vault Config #
################


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


# stab pool claims


@external
def setStabClaimRewardsConfig(_config: cs.StabClaimRewardsConfig):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.stabClaimRewardsConfig = _config


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


##################
# Access Control #
##################


@external
def setCanPerformLiteAction(_user: address, _canDo: bool):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.canPerformLiteAction[_user] = _canDo


#########
# Other #
#########


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


# general liquidation cs


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
        ltvPaybackBuffer=genDebtConfig.ltvPaybackBuffer,
        genAuctionParams=genDebtConfig.genAuctionParams,
        priorityLiqAssetVaults=priorityLiqAssetVaults,
        priorityStabVaults=priorityStabVaults,
    )


@view
@external
def getGenAuctionParams() -> cs.AuctionParams:
    return self.genDebtConfig.genAuctionParams


# asset liquidation cs


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
def getStabPoolClaimsConfig(_claimAsset: address, _claimer: address, _caller: address) -> StabPoolClaimsConfig:
    assetConfig: cs.AssetConfig = self.assetConfig[_claimAsset]

    canClaimFromStabPoolForUser: bool = True
    if _claimer != _caller:
        delegation: cs.ActionDelegation = self.userDelegation[_claimer][_caller]
        canClaimFromStabPoolForUser = delegation.canClaimFromStabPool

    rewardsConfig: cs.StabClaimRewardsConfig = self.stabClaimRewardsConfig
    return StabPoolClaimsConfig(
        canClaimInStabPoolGeneral=self.genConfig.canClaimInStabPool,
        canClaimInStabPoolAsset=assetConfig.canClaimInStabPool,
        canClaimFromStabPoolForUser=canClaimFromStabPoolForUser,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _claimer, _claimAsset),
        rewardsLockDuration=rewardsConfig.rewardsLockDuration,
        ripePerDollarClaimed=rewardsConfig.ripePerDollarClaimed,
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

    ripeTokenVaultConfig: cs.RipeGovVaultConfig = self.ripeGovVaultConfig[_ripeToken]
    rewardsConfig: cs.RipeRewardsConfig = self.rewardsConfig

    return ClaimLootConfig(
        canClaimLoot=self.genConfig.canClaimLoot,
        canClaimLootForUser=canClaimLootForUser,
        autoStakeRatio=rewardsConfig.autoStakeRatio,
        autoStakeDurationRatio=rewardsConfig.autoStakeDurationRatio,
        minLockDuration=ripeTokenVaultConfig.lockTerms.minLockDuration,
        maxLockDuration=ripeTokenVaultConfig.lockTerms.maxLockDuration,
    )


# rewards cs


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


# price cs


@view
@external
def getPriceConfig() -> PriceConfig:
    return PriceConfig(
        staleTime=self.genConfig.priceStaleTime,
        priorityPriceSourceIds=self.priorityPriceSourceIds,
    )


# ripe bond cs


@view
@external
def getPurchaseRipeBondConfig(_user: address) -> PurchaseRipeBondConfig:
    bondConfig: cs.RipeBondConfig = self.ripeBondConfig
    vaultConfig: cs.RipeGovVaultConfig = self.ripeGovVaultConfig[addys._getRipeToken()]

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
    )


# dynamic borrow rate cs


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