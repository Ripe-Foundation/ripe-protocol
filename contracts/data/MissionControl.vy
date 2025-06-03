# @version 0.4.1
# pragma optimize codesize

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department

interface Whitelist:
    def isUserAllowed(_user: address, _asset: address) -> bool: view

interface Vault:
    def vaultAssets(_index: uint256) -> address: view

interface UnderscoreAgentFactory:
    def isUserWallet(_addr: address) -> bool: view

interface UnderscoreRegistry:
    def getAddy(_addyId: uint256) -> address: view

interface VaultBook:
    def getAddr(_regId: uint256) -> address: view

interface UnderscoreWallet:
    def walletConfig() -> address: view

interface UnderscoreWalletConfig:
    def owner() -> address: view

struct GenConfig:
    perUserMaxVaults: uint256
    perUserMaxAssetsPerVault: uint256
    priceStaleTime: uint256
    canDeposit: bool
    canWithdraw: bool
    canBorrow: bool
    canRepay: bool
    canClaimLoot: bool
    canLiquidate: bool
    canRedeemCollateral: bool
    canRedeemInStabPool: bool
    canBuyInAuction: bool
    canClaimInStabPool: bool

struct GenDebtConfig:
    perUserDebtLimit: uint256
    globalDebtLimit: uint256
    minDebtAmount: uint256
    numAllowedBorrowers: uint256
    maxBorrowPerInterval: uint256
    numBlocksPerInterval: uint256
    keeperFeeRatio: uint256
    minKeeperFee: uint256
    isDaowryEnabled: bool
    ltvPaybackBuffer: uint256
    genAuctionParams: AuctionParams

struct RipeRewardsConfig:
    arePointsEnabled: bool
    ripePerBlock: uint256
    borrowersAlloc: uint256
    stakersAlloc: uint256
    votersAlloc: uint256
    genDepositorsAlloc: uint256

struct AssetConfig:
    vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET]
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
    debtTerms: DebtTerms
    shouldBurnAsPayment: bool
    shouldTransferToEndaoment: bool
    shouldSwapInStabPools: bool
    shouldAuctionInstantly: bool
    canDeposit: bool
    canWithdraw: bool
    canRedeemCollateral: bool
    canRedeemInStabPool: bool
    canBuyInAuction: bool
    canClaimInStabPool: bool
    specialStabPoolId: uint256
    customAuctionParams: AuctionParams
    whitelist: address
    isNft: bool

struct TotalPointsAllocs:
    stakersPointsAllocTotal: uint256
    voterPointsAllocTotal: uint256

struct UserConfig:
    canAnyoneDeposit: bool
    canAnyoneRepayDebt: bool

struct ActionDelegation:
    canWithdraw: bool
    canBorrow: bool
    canClaimFromStabPool: bool
    canClaimLoot: bool

struct DebtTerms:
    ltv: uint256
    redemptionThreshold: uint256
    liqThreshold: uint256
    liqFee: uint256
    borrowRate: uint256
    daowry: uint256

struct AuctionParams:
    hasParams: bool
    startDiscount: uint256
    maxDiscount: uint256
    delay: uint256
    duration: uint256

struct VaultLite:
    vaultId: uint256
    asset: address

struct VaultData:
    vaultId: uint256
    vaultAddr: address
    asset: address

# helpers

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

struct AuctionBuyConfig:
    canBuyInAuctionGeneral: bool
    canBuyInAuctionAsset: bool
    isUserAllowed: bool

struct GenLiqConfig:
    canLiquidate: bool
    keeperFeeRatio: uint256
    minKeeperFee: uint256
    ltvPaybackBuffer: uint256
    genAuctionParams: AuctionParams
    priorityLiqAssetVaults: DynArray[VaultData, PRIORITY_VAULT_DATA]
    priorityStabVaults: DynArray[VaultData, PRIORITY_VAULT_DATA]

struct AssetLiqConfig:
    hasConfig: bool
    shouldBurnAsPayment: bool
    shouldTransferToEndaoment: bool
    shouldSwapInStabPools: bool
    shouldAuctionInstantly: bool
    customAuctionParams: AuctionParams
    specialStabPool: VaultData

struct StabPoolClaimsConfig:
    canClaimInStabPoolGeneral: bool
    canClaimInStabPoolAsset: bool
    canClaimFromStabPoolForUser: bool
    isUserAllowed: bool

struct StabPoolRedemptionsConfig:
    canRedeemInStabPoolGeneral: bool
    canRedeemInStabPoolAsset: bool
    isUserAllowed: bool

struct ClaimLootConfig:
    canClaimLoot: bool
    canClaimLootForUser: bool

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

# events

event UserConfigSet:
    user: indexed(address)
    canAnyoneDeposit: bool
    canAnyoneRepayDebt: bool

event UserDelegationSet:
    user: indexed(address)
    delegate: indexed(address)
    setter: indexed(address)
    canWithdraw: bool
    canBorrow: bool
    canClaimFromStabPool: bool
    canClaimLoot: bool

# global config
genConfig: public(GenConfig)
genDebtConfig: public(GenDebtConfig)

# asset config
assetConfig: public(HashMap[address, AssetConfig]) # asset -> config
assets: public(HashMap[uint256, address]) # index -> asset
indexOfAsset: public(HashMap[address, uint256]) # asset -> index
numAssets: public(uint256) # num assets

# user config
userConfig: public(HashMap[address, UserConfig]) # user -> config
userDelegation: public(HashMap[address, HashMap[address, ActionDelegation]]) # user -> caller -> config

# ripe rewards
rewardsConfig: public(RipeRewardsConfig)
totalPointsAllocs: public(TotalPointsAllocs)

# priority data
priorityPriceSourceIds: public(DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES])
priorityLiqAssetVaults: public(DynArray[VaultLite, PRIORITY_VAULT_DATA])
priorityStabVaults: public(DynArray[VaultLite, PRIORITY_VAULT_DATA])

# other
underscoreRegistry: public(address)
canDisable: public(HashMap[address, bool]) # user -> canDisable
maxLtvDeviation: public(uint256)

MAX_VAULTS_PER_ASSET: constant(uint256) = 10
MAX_PRIORITY_PRICE_SOURCES: constant(uint256) = 10
PRIORITY_VAULT_DATA: constant(uint256) = 20
UNDERSCORE_AGENT_FACTORY_ID: constant(uint256) = 1


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting

    self.numAssets = 1 # not using 0 index
    self.maxLtvDeviation = 10_00 # 10% default


#################
# Global Config #
#################


# general


@external
def setGeneralConfig(_config: GenConfig):
    assert addys._canModifyMissionControl(msg.sender) # dev: no perms
    self.genConfig = _config


# debt


@external
def setGeneralDebtConfig(_config: GenDebtConfig):
    assert addys._canModifyMissionControl(msg.sender) # dev: no perms
    self.genDebtConfig = _config


# rewards


@external
def setRipeRewardsConfig(_config: RipeRewardsConfig):
    assert addys._canModifyMissionControl(msg.sender) # dev: no perms
    self.rewardsConfig = _config


################
# Asset Config #
################


@external
def setAssetConfig(_asset: address, _config: AssetConfig):
    assert addys._canModifyMissionControl(msg.sender) # dev: no perms
    self._updatePointsAllocs(_asset, _config.stakersPointsAlloc, _config.voterPointsAlloc) # do first!
    self.assetConfig[_asset] = _config

    # register asset (if necessary)
    if self.indexOfAsset[_asset] == 0:
        self._registerAsset(_asset)


# points allocs


@internal
def _updatePointsAllocs(_asset: address, _newStakersPointsAlloc: uint256, _newVoterPointsAlloc: uint256):
    totalPointsAllocs: TotalPointsAllocs = self.totalPointsAllocs

    # remove old allocs
    prevConfig: AssetConfig = self.assetConfig[_asset]
    totalPointsAllocs.stakersPointsAllocTotal -= prevConfig.stakersPointsAlloc
    totalPointsAllocs.voterPointsAllocTotal -= prevConfig.voterPointsAlloc

    # add new allocs
    totalPointsAllocs.stakersPointsAllocTotal += _newStakersPointsAlloc
    totalPointsAllocs.voterPointsAllocTotal += _newVoterPointsAlloc
    self.totalPointsAllocs = totalPointsAllocs


# asset registration


@internal
def _registerAsset(_asset: address):
    aid: uint256 = self.numAssets
    self.assets[aid] = _asset
    self.indexOfAsset[_asset] = aid
    self.numAssets = aid + 1


@external
def deregisterAsset(_asset: address) -> bool:
    assert addys._canModifyMissionControl(msg.sender) # dev: no perms

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


# utils


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


#################
# Priority Data #
#################


# price sources


@external
def setPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]):
    assert addys._canModifyMissionControl(msg.sender) # dev: no perms
    self.priorityPriceSourceIds = _priorityIds


@view 
@external 
def getPriorityPriceSourceIds() -> DynArray[uint256, MAX_PRIORITY_PRICE_SOURCES]:
    return self.priorityPriceSourceIds


# priority liq asset vaults


@external
def setPriorityLiqAssetVaults(_priorityLiqAssetVaults: DynArray[VaultLite, PRIORITY_VAULT_DATA]):
    assert addys._canModifyMissionControl(msg.sender) # dev: no perms
    self.priorityLiqAssetVaults = _priorityLiqAssetVaults


@view 
@external 
def getPriorityLiqAssetVaults() -> DynArray[VaultLite, PRIORITY_VAULT_DATA]:
    return self.priorityLiqAssetVaults


# stability pool vaults


@external
def setPriorityStabVaults(_priorityStabVaults: DynArray[VaultLite, PRIORITY_VAULT_DATA]):
    assert addys._canModifyMissionControl(msg.sender) # dev: no perms
    self.priorityStabVaults = _priorityStabVaults


@view 
@external 
def getPriorityStabVaults() -> DynArray[VaultLite, PRIORITY_VAULT_DATA]:
    return self.priorityStabVaults


#########
# Other #
#########


# underscore registry


@external
def setUnderscoreRegistry(_underscoreRegistry: address):
    assert addys._canModifyMissionControl(msg.sender) # dev: no perms
    self.underscoreRegistry = _underscoreRegistry


# can disable


@external
def setCanDisable(_user: address, _canDisable: bool):
    assert addys._canModifyMissionControl(msg.sender) # dev: no perms
    self.canDisable[_user] = _canDisable


# max ltv deviation


@external
def setMaxLtvDeviation(_maxLtvDeviation: uint256):
    assert addys._canModifyMissionControl(msg.sender) # dev: no perms
    self.maxLtvDeviation = _maxLtvDeviation


# stale price time


@view
@external
def getPriceStaleTime() -> uint256:
    # used by Chainlink.vy
    return self.genConfig.priceStaleTime


###############
# User Config #
###############


@external
def setUserConfig(
    _canAnyoneDeposit: bool = True,
    _canAnyoneRepayDebt: bool = True,
) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    userConfig: UserConfig = UserConfig(
        canAnyoneDeposit=_canAnyoneDeposit,
        canAnyoneRepayDebt=_canAnyoneRepayDebt,
    )
    self.userConfig[msg.sender] = userConfig
    log UserConfigSet(user=msg.sender, canAnyoneDeposit=_canAnyoneDeposit, canAnyoneRepayDebt=_canAnyoneRepayDebt)
    return True


# delegation


@external
def setUserDelegation(
    _delegate: address,
    _canWithdraw: bool,
    _canBorrow: bool,
    _canClaimFromStabPool: bool,
    _canClaimLoot: bool,
    _user: address = msg.sender,
) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert _delegate != empty(address) # dev: invalid delegate

    # validate underscore wallet
    if _user != msg.sender:
        assert self._isUnderscoreWalletOwner(_user, msg.sender) # dev: not owner of underscore wallet

    config: ActionDelegation = ActionDelegation(
        canWithdraw=_canWithdraw,
        canBorrow=_canBorrow,
        canClaimFromStabPool=_canClaimFromStabPool,
        canClaimLoot=_canClaimLoot,
    )
    self.userDelegation[_user][_delegate] = config
    log UserDelegationSet(user=_user, delegate=_delegate, setter=msg.sender, canWithdraw=_canWithdraw, canBorrow=_canBorrow, canClaimFromStabPool=_canClaimFromStabPool, canClaimLoot=_canClaimLoot)
    return True


# underscore ownership check


@view
@internal
def _isUnderscoreWalletOwner(_user: address, _caller: address) -> bool:
    underscore: address = self.underscoreRegistry
    if underscore == empty(address):
        return False

    agentFactory: address = staticcall UnderscoreRegistry(underscore).getAddy(UNDERSCORE_AGENT_FACTORY_ID)
    if agentFactory == empty(address):
        return False

    # must be underscore wallet
    if not staticcall UnderscoreAgentFactory(agentFactory).isUserWallet(_user):
        return False

    walletConfig: address = staticcall UnderscoreWallet(_user).walletConfig()
    if walletConfig == empty(address):
        return False

    # caller must be owner!
    return staticcall UnderscoreWalletConfig(walletConfig).owner() == _caller


###################
# Helpers / Views #
###################


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
    assetConfig: AssetConfig = self.assetConfig[_asset]
    genConfig: GenConfig = self.genConfig
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
    assetConfig: AssetConfig = self.assetConfig[_asset]

    canWithdrawForUser: bool = True
    if _user != _caller:
        delegation: ActionDelegation = self.userDelegation[_user][_caller]
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
def getDebtTerms(_asset: address) -> DebtTerms:
    return self.assetConfig[_asset].debtTerms


@view
@external
def getBorrowConfig(_user: address, _caller: address) -> BorrowConfig:
    genDebtConfig: GenDebtConfig = self.genDebtConfig

    canBorrowForUser: bool = True
    if _user != _caller:
        delegation: ActionDelegation = self.userDelegation[_user][_caller]
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
def getRedeemCollateralConfig(_asset: address, _redeemer: address) -> RedeemCollateralConfig:
    assetConfig: AssetConfig = self.assetConfig[_asset]
    return RedeemCollateralConfig(
        canRedeemCollateralGeneral=self.genConfig.canRedeemCollateral,
        canRedeemCollateralAsset=assetConfig.canRedeemCollateral,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _redeemer, _asset),
        ltvPaybackBuffer=self.genDebtConfig.ltvPaybackBuffer,
    )


@view
@external
def getLtvPaybackBuffer() -> uint256:
    return self.genDebtConfig.ltvPaybackBuffer


# auction purchases


@view
@external
def getAuctionBuyConfig(_asset: address, _buyer: address) -> AuctionBuyConfig:
    assetConfig: AssetConfig = self.assetConfig[_asset]
    return AuctionBuyConfig(
        canBuyInAuctionGeneral=self.genConfig.canBuyInAuction,
        canBuyInAuctionAsset=assetConfig.canBuyInAuction,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _buyer, _asset),
    )


# general liquidation config


@view
@external
def getGenLiqConfig() -> GenLiqConfig:
    genDebtConfig: GenDebtConfig = self.genDebtConfig
    vaultBook: address = addys._getVaultBookAddr()

    # priority liq asset vault data
    priorityLiqAssetVaults: DynArray[VaultData, PRIORITY_VAULT_DATA] = []
    for pData: VaultLite in self.priorityLiqAssetVaults:
        vaultAddr: address = staticcall VaultBook(vaultBook).getAddr(pData.vaultId)
        priorityLiqAssetVaults.append(VaultData(vaultId=pData.vaultId, vaultAddr=vaultAddr, asset=pData.asset))

    # stability pool vault data
    priorityStabVaults: DynArray[VaultData, PRIORITY_VAULT_DATA] = []
    for pData: VaultLite in self.priorityStabVaults:
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
def getGenAuctionParams() -> AuctionParams:
    return self.genDebtConfig.genAuctionParams


# asset liquidation config


@view
@external
def getAssetLiqConfig(_asset: address) -> AssetLiqConfig:
    assetConfig: AssetConfig = self.assetConfig[_asset]
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
    assetConfig: AssetConfig = self.assetConfig[_claimAsset]

    canClaimFromStabPoolForUser: bool = True
    if _claimer != _caller:
        delegation: ActionDelegation = self.userDelegation[_claimer][_caller]
        canClaimFromStabPoolForUser = delegation.canClaimFromStabPool

    return StabPoolClaimsConfig(
        canClaimInStabPoolGeneral=self.genConfig.canClaimInStabPool,
        canClaimInStabPoolAsset=assetConfig.canClaimInStabPool,
        canClaimFromStabPoolForUser=canClaimFromStabPoolForUser,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _claimer, _claimAsset),
    )


# stability pool redemptions


@view
@external
def getStabPoolRedemptionsConfig(_asset: address, _redeemer: address) -> StabPoolRedemptionsConfig:
    assetConfig: AssetConfig = self.assetConfig[_asset]
    return StabPoolRedemptionsConfig(
        canRedeemInStabPoolGeneral=self.genConfig.canRedeemInStabPool,
        canRedeemInStabPoolAsset=assetConfig.canRedeemInStabPool,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _redeemer, _asset),
    )


# loot claims


@view
@external
def getClaimLootConfig(_user: address, _caller: address) -> ClaimLootConfig:
    canClaimLootForUser: bool = True
    if _user != _caller:
        delegation: ActionDelegation = self.userDelegation[_user][_caller]
        canClaimLootForUser = delegation.canClaimLoot
    return ClaimLootConfig(
        canClaimLoot=self.genConfig.canClaimLoot,
        canClaimLootForUser=canClaimLootForUser,
    )


# rewards config


@view
@external
def getRewardsConfig() -> RewardsConfig:
    rewardsConfig: RipeRewardsConfig = self.rewardsConfig
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
    assetConfig: AssetConfig = self.assetConfig[_asset]
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
