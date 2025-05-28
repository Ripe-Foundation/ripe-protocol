# @version 0.4.1

implements: Department

exports: gov.__interface__
exports: addys.__interface__
exports: deptBasics.__interface__

initializes: gov
initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.LocalGov as gov
import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department

interface ControlRoomData:
    def getManyConfigs(_getGenConfig: bool, _getDebtConfig: bool, _getRewardsConfig: bool, _asset: address = empty(address), _user: address = empty(address)) -> MetaConfig: view
    def setPriorityLiqAssetVaults(_priorityLiqAssetVaults: DynArray[VaultLite, PRIORITY_LIQ_VAULT_DATA]): nonpayable
    def setPriorityStabVaults(_priorityStabVaults: DynArray[VaultLite, MAX_STAB_VAULT_DATA]): nonpayable
    def setPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]): nonpayable
    def setUserDelegation(_user: address, _delegate: address, _config: ActionDelegation): nonpayable
    def getPriorityLiqAssetVaults() -> DynArray[VaultLite, PRIORITY_LIQ_VAULT_DATA]: view
    def getPriorityPriceSourceIds() -> DynArray[uint256, MAX_PRIORITY_PARTNERS]: view
    def userDelegation(_user: address, _delegate: address) -> ActionDelegation: view
    def getPriorityStabVaults() -> DynArray[VaultLite, MAX_STAB_VAULT_DATA]: view
    def setAssetConfig(_asset: address, _assetConfig: AssetConfig): nonpayable
    def setRipeRewardsConfig(_rewardsConfig: RipeRewardsConfig): nonpayable
    def setUserConfig(_user: address, _userConfig: UserConfig): nonpayable
    def setGeneralDebtConfig(_genDebtConfig: GenDebtConfig): nonpayable
    def setGeneralConfig(_genConfig: GenConfig): nonpayable
    def assetConfig(_asset: address) -> AssetConfig: view
    def getControlRoomId() -> uint256: view
    def genDebtConfig() -> GenDebtConfig: view
    def genConfig() -> GenConfig: view
    def ripeHq() -> address: view

interface Whitelist:
    def isUserAllowed(_user: address, _asset: address) -> bool: view

interface Vault:
    def vaultAssets(_index: uint256) -> address: view

interface VaultBook:
    def getAddr(_vaultId: uint256) -> address: view

interface PriceDesk:
    def isValidRegId(_regId: uint256) -> bool: view

# core structs

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

struct AssetConfig:
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

struct UserConfig:
    canAnyoneDeposit: bool
    canAnyoneRepayDebt: bool

struct ActionDelegation:
    canWithdraw: bool
    canBorrow: bool
    canClaimFromStabPool: bool
    canClaimLoot: bool

struct RipeRewardsConfig:
    arePointsEnabled: bool
    ripePerBlock: uint256
    borrowersAlloc: uint256
    stakersAlloc: uint256
    votersAlloc: uint256
    genDepositorsAlloc: uint256

struct TotalPointsAllocs:
    stakersPointsAllocTotal: uint256
    voterPointsAllocTotal: uint256

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

# helper config bundles

struct TellerDepositConfig:
    canDepositGeneral: bool
    canDepositAsset: bool
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
    priorityLiqAssetVaults: DynArray[VaultData, PRIORITY_LIQ_VAULT_DATA]
    priorityStabVaults: DynArray[VaultData, MAX_STAB_VAULT_DATA]

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
    isUserAllowed: bool

struct StabPoolRedemptionsConfig:
    canRedeemInStabPoolGeneral: bool
    canRedeemInStabPoolAsset: bool
    isUserAllowed: bool

struct ClaimLootConfig:
    canClaimLoot: bool
    canClaimLootForUser: bool

struct DepositPointsConfig:
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    isNft: bool

struct RewardsConfig:
    arePointsEnabled: bool
    ripePerBlock: uint256
    borrowersAlloc: uint256
    stakersAlloc: uint256
    votersAlloc: uint256
    genDepositorsAlloc: uint256
    stakersPointsAllocTotal: uint256
    voterPointsAllocTotal: uint256

struct PriceConfig:
    staleTime: uint256
    priorityPriceSourceIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]

struct VaultData:
    vaultId: uint256
    vaultAddr: address
    asset: address

struct VaultLite:
    vaultId: uint256
    asset: address

struct MetaConfig:
    genConfig: GenConfig
    genDebtConfig: GenDebtConfig
    assetConfig: AssetConfig
    userConfig: UserConfig
    rewardsConfig: RipeRewardsConfig
    totalPointsAllocs: TotalPointsAllocs

event PriorityPriceSourceIdsModified:
    numIds: uint256

event StaleTimeSet:
    staleTime: uint256

# control room data
data: public(address)

MIN_STALE_TIME: public(immutable(uint256))
MAX_STALE_TIME: public(immutable(uint256))

MAX_PRIORITY_PARTNERS: constant(uint256) = 10
MAX_STAB_VAULT_DATA: constant(uint256) = 10
PRIORITY_LIQ_VAULT_DATA: constant(uint256) = 20


@deploy
def __init__(
    _ripeHq: address,
    _controlRoomData: address,
    _minStaleTime: uint256,
    _maxStaleTime: uint256,
):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting

    # control room data
    assert staticcall ControlRoomData(_controlRoomData).ripeHq() == _ripeHq # dev: invalid ripe hq
    assert staticcall ControlRoomData(_controlRoomData).getControlRoomId() == addys._getControlRoomId() # dev: invalid control room id
    self.data = _controlRoomData

    assert _minStaleTime < _maxStaleTime # dev: invalid stale time range
    MIN_STALE_TIME = _minStaleTime
    MAX_STALE_TIME = _maxStaleTime


#################
# Global Config #
#################


@external
def setGeneralConfig(
    _perUserMaxVaults: uint256,
    _perUserMaxAssetsPerVault: uint256,
    _priceStaleTime: uint256,
    _canDeposit: bool,
    _canWithdraw: bool,
    _canBorrow: bool,
    _canRepay: bool,
    _canClaimLoot: bool,
    _canLiquidate: bool,
    _canRedeemCollateral: bool,
    _canRedeemInStabPool: bool,
    _canBuyInAuction: bool,
    _canClaimInStabPool: bool,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock, validation, event

    genConfig: GenConfig = GenConfig(
        perUserMaxVaults=_perUserMaxVaults,
        perUserMaxAssetsPerVault=_perUserMaxAssetsPerVault,
        priceStaleTime=_priceStaleTime,
        canDeposit=_canDeposit,
        canWithdraw=_canWithdraw,
        canBorrow=_canBorrow,
        canRepay=_canRepay,
        canClaimLoot=_canClaimLoot,
        canLiquidate=_canLiquidate,
        canRedeemCollateral=_canRedeemCollateral,
        canRedeemInStabPool=_canRedeemInStabPool,
        canBuyInAuction=_canBuyInAuction,
        canClaimInStabPool=_canClaimInStabPool,
    )
    extcall ControlRoomData(self.data).setGeneralConfig(genConfig)
    return True


# general debt config


@external
def setGeneralDebtConfig(
    _perUserDebtLimit: uint256,
    _globalDebtLimit: uint256,
    _minDebtAmount: uint256,
    _numAllowedBorrowers: uint256,
    _maxBorrowPerInterval: uint256,
    _numBlocksPerInterval: uint256,
    _keeperFeeRatio: uint256,
    _minKeeperFee: uint256,
    _isDaowryEnabled: bool,
    _ltvPaybackBuffer: uint256,
    _genAuctionParams: AuctionParams,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock, validation, event

    genDebtConfig: GenDebtConfig = GenDebtConfig(
        perUserDebtLimit=_perUserDebtLimit,
        globalDebtLimit=_globalDebtLimit,
        minDebtAmount=_minDebtAmount,
        numAllowedBorrowers=_numAllowedBorrowers,
        maxBorrowPerInterval=_maxBorrowPerInterval,
        numBlocksPerInterval=_numBlocksPerInterval,
        keeperFeeRatio=_keeperFeeRatio,
        minKeeperFee=_minKeeperFee,
        isDaowryEnabled=_isDaowryEnabled,
        ltvPaybackBuffer=_ltvPaybackBuffer,
        genAuctionParams=_genAuctionParams,
    )
    extcall ControlRoomData(self.data).setGeneralDebtConfig(genDebtConfig)
    return True


################
# Asset Config #
################


@external
def setAssetConfig(
    _asset: address,
    _stakersPointsAlloc: uint256,
    _voterPointsAlloc: uint256,
    _perUserDepositLimit: uint256,
    _globalDepositLimit: uint256,
    _debtTerms: DebtTerms,
    _shouldBurnAsPayment: bool,
    _shouldTransferToEndaoment: bool,
    _shouldSwapInStabPools: bool,
    _shouldAuctionInstantly: bool,
    _canDeposit: bool,
    _canWithdraw: bool,
    _canRedeemCollateral: bool,
    _canRedeemInStabPool: bool,
    _canBuyInAuction: bool,
    _canClaimInStabPool: bool,
    _specialStabPoolId: uint256,
    _customAuctionParams: AuctionParams,
    _whitelist: address,
    _isNft: bool,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock, validation, event

    assetConfig: AssetConfig = AssetConfig(
        stakersPointsAlloc=_stakersPointsAlloc,
        voterPointsAlloc=_voterPointsAlloc,
        perUserDepositLimit=_perUserDepositLimit,
        globalDepositLimit=_globalDepositLimit,
        debtTerms=_debtTerms,
        shouldBurnAsPayment=_shouldBurnAsPayment,
        shouldTransferToEndaoment=_shouldTransferToEndaoment,
        shouldSwapInStabPools=_shouldSwapInStabPools,
        shouldAuctionInstantly=_shouldAuctionInstantly,
        canDeposit=_canDeposit,
        canWithdraw=_canWithdraw,
        canRedeemCollateral=_canRedeemCollateral,
        canRedeemInStabPool=_canRedeemInStabPool,
        canBuyInAuction=_canBuyInAuction,
        canClaimInStabPool=_canClaimInStabPool,
        specialStabPoolId=_specialStabPoolId,
        customAuctionParams=_customAuctionParams,
        whitelist=_whitelist,
        isNft=_isNft,
    )
    extcall ControlRoomData(self.data).setAssetConfig(_asset, assetConfig)
    return True


####################
# Rewards / Points #
####################


@external
def setRipeRewardsConfig(
    _arePointsEnabled: bool,
    _ripePerBlock: uint256,
    _borrowersAlloc: uint256,
    _stakersAlloc: uint256,
    _votersAlloc: uint256,
    _genDepositorsAlloc: uint256,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock, validation, event

    rewardsConfig: RipeRewardsConfig = RipeRewardsConfig(
        arePointsEnabled=_arePointsEnabled,
        ripePerBlock=_ripePerBlock,
        borrowersAlloc=_borrowersAlloc,
        stakersAlloc=_stakersAlloc,
        votersAlloc=_votersAlloc,
        genDepositorsAlloc=_genDepositorsAlloc,
    )
    extcall ControlRoomData(self.data).setRipeRewardsConfig(rewardsConfig)
    return True


###############
# User Config #
###############


@external
def setUserConfig(
    _canAnyoneDeposit: bool,
    _canAnyoneRepayDebt: bool,
) -> bool:
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock, validation, event

    userConfig: UserConfig = UserConfig(
        canAnyoneDeposit=_canAnyoneDeposit,
        canAnyoneRepayDebt=_canAnyoneRepayDebt,
    )
    extcall ControlRoomData(self.data).setUserConfig(msg.sender, userConfig)
    return True


@external
def setUserDelegation(
    _delegate: address,
    _canWithdraw: bool,
    _canBorrow: bool,
    _canClaimFromStabPool: bool,
    _canClaimLoot: bool,
) -> bool:
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock, validation, event

    # TODO: allow for owner of Underscore wallet to set this for their wallet.

    config: ActionDelegation = ActionDelegation(
        canWithdraw=_canWithdraw,
        canBorrow=_canBorrow,
        canClaimFromStabPool=_canClaimFromStabPool,
        canClaimLoot=_canClaimLoot,
    )
    extcall ControlRoomData(self.data).setUserDelegation(msg.sender, _delegate, config)
    return True


##########################
# Priority Price Sources #
##########################


@external
def setPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = self._sanitizePrioritySources(_priorityIds)
    assert self._areValidPriorityPriceSourceIds(priorityIds) # dev: invalid priority sources
    extcall ControlRoomData(self.data).setPriorityPriceSourceIds(priorityIds)

    log PriorityPriceSourceIdsModified(numIds=len(priorityIds))
    return True


# validation


@view
@external
def areValidPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
    priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = self._sanitizePrioritySources(_priorityIds)
    return self._areValidPriorityPriceSourceIds(priorityIds)


@view
@internal
def _areValidPriorityPriceSourceIds(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> bool:
    return len(_priorityIds) != 0


# utilities


@view
@internal
def _sanitizePrioritySources(_priorityIds: DynArray[uint256, MAX_PRIORITY_PARTNERS]) -> DynArray[uint256, MAX_PRIORITY_PARTNERS]:
    sanitizedIds: DynArray[uint256, MAX_PRIORITY_PARTNERS] = []
    priceDesk: address = addys._getPriceDeskAddr()
    for pid: uint256 in _priorityIds:
        if not staticcall PriceDesk(priceDesk).isValidRegId(pid):
            continue
        if pid in sanitizedIds:
            continue
        sanitizedIds.append(pid)
    return sanitizedIds


#######################
# Prices - Stale Time #
#######################


@external
def setStaleTime(_staleTime: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: not activated

    assert self._isValidStaleTime(_staleTime) # dev: invalid stale time

    # update data
    data: address = self.data
    genConfig: GenConfig = staticcall ControlRoomData(data).genConfig()
    genConfig.priceStaleTime = _staleTime
    extcall ControlRoomData(data).setGeneralConfig(genConfig)

    log StaleTimeSet(staleTime=_staleTime)
    return True


@view
@external
def getPriceStaleTime() -> uint256:
    # used by Chainlink.vy
    genConfig: GenConfig = staticcall ControlRoomData(self.data).genConfig()
    return genConfig.priceStaleTime


# validation


@view
@external
def isValidStaleTime(_staleTime: uint256) -> bool:
    return self._isValidStaleTime(_staleTime)


@view
@internal
def _isValidStaleTime(_staleTime: uint256) -> bool:
    return _staleTime >= MIN_STALE_TIME and _staleTime <= MAX_STALE_TIME


######################
# Special Vault Data #
######################


@external
def setPriorityLiqAssetVaults(_priorityLiqAssetVaults: DynArray[VaultLite, PRIORITY_LIQ_VAULT_DATA]) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock, validation, event

    extcall ControlRoomData(self.data).setPriorityLiqAssetVaults(_priorityLiqAssetVaults)
    return True


@external
def setPriorityStabVaults(_priorityStabVaults: DynArray[VaultLite, MAX_STAB_VAULT_DATA]) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock, validation, event

    extcall ControlRoomData(self.data).setPriorityStabVaults(_priorityStabVaults)
    return True


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
def getTellerDepositConfig(_asset: address, _user: address) -> TellerDepositConfig:
    c: MetaConfig = staticcall ControlRoomData(self.data).getManyConfigs(True, False, False, _asset, _user)
    return TellerDepositConfig(
        canDepositGeneral=c.genConfig.canDeposit,
        canDepositAsset=c.assetConfig.canDeposit,
        isUserAllowed=self._isUserAllowed(c.assetConfig.whitelist, _user, _asset),
        perUserDepositLimit=c.assetConfig.perUserDepositLimit,
        globalDepositLimit=c.assetConfig.globalDepositLimit,
        perUserMaxAssetsPerVault=c.genConfig.perUserMaxAssetsPerVault,
        perUserMaxVaults=c.genConfig.perUserMaxVaults,
        canAnyoneDeposit=c.userConfig.canAnyoneDeposit,
    )


# withdrawals


@view
@external
def getTellerWithdrawConfig(_asset: address, _user: address, _caller: address) -> TellerWithdrawConfig:
    data: address = self.data
    c: MetaConfig = staticcall ControlRoomData(data).getManyConfigs(True, False, False, _asset)

    canWithdrawForUser: bool = True
    if _user != _caller:
        delegation: ActionDelegation = staticcall ControlRoomData(data).userDelegation(_user, _caller)
        canWithdrawForUser = delegation.canWithdraw

    return TellerWithdrawConfig(
        canWithdrawGeneral=c.genConfig.canWithdraw,
        canWithdrawAsset=c.assetConfig.canWithdraw,
        isUserAllowed=self._isUserAllowed(c.assetConfig.whitelist, _user, _asset),
        canWithdrawForUser=canWithdrawForUser,
    )


# borrow


@view
@external
def getDebtTerms(_asset: address) -> DebtTerms:
    assetConfig: AssetConfig = staticcall ControlRoomData(self.data).assetConfig(_asset)
    return assetConfig.debtTerms


@view
@external
def getBorrowConfig(_user: address, _caller: address) -> BorrowConfig:
    data: address = self.data
    c: MetaConfig = staticcall ControlRoomData(data).getManyConfigs(True, True, False)

    canBorrowForUser: bool = True
    if _user != _caller:
        delegation: ActionDelegation = staticcall ControlRoomData(data).userDelegation(_user, _caller)
        canBorrowForUser = delegation.canBorrow

    return BorrowConfig(
        canBorrow=c.genConfig.canBorrow,
        canBorrowForUser=canBorrowForUser,
        numAllowedBorrowers=c.genDebtConfig.numAllowedBorrowers,
        maxBorrowPerInterval=c.genDebtConfig.maxBorrowPerInterval,
        numBlocksPerInterval=c.genDebtConfig.numBlocksPerInterval,
        perUserDebtLimit=c.genDebtConfig.perUserDebtLimit,
        globalDebtLimit=c.genDebtConfig.globalDebtLimit,
        minDebtAmount=c.genDebtConfig.minDebtAmount,
        isDaowryEnabled=c.genDebtConfig.isDaowryEnabled,
    )


# repay


@view
@external
def getRepayConfig(_user: address) -> RepayConfig:
    c: MetaConfig = staticcall ControlRoomData(self.data).getManyConfigs(True, False, False, empty(address), _user)
    return RepayConfig(
        canRepay=c.genConfig.canRepay,
        canAnyoneRepayDebt=c.userConfig.canAnyoneRepayDebt,
    )


# redeem collateral


@view
@external
def getRedeemCollateralConfig(_asset: address, _redeemer: address) -> RedeemCollateralConfig:
    c: MetaConfig = staticcall ControlRoomData(self.data).getManyConfigs(True, True, False, _asset)

    # TODO: when setting asset config -> canRedeemCollateral, make sure: has LTV, not stable, not NFT

    return RedeemCollateralConfig(
        canRedeemCollateralGeneral=c.genConfig.canRedeemCollateral,
        canRedeemCollateralAsset=c.assetConfig.canRedeemCollateral,
        isUserAllowed=self._isUserAllowed(c.assetConfig.whitelist, _redeemer, _asset),
        ltvPaybackBuffer=c.genDebtConfig.ltvPaybackBuffer,
    )


# auction purchases


@view
@external
def getAuctionBuyConfig(_asset: address, _buyer: address) -> AuctionBuyConfig:
    c: MetaConfig = staticcall ControlRoomData(self.data).getManyConfigs(True, False, False, _asset)
    return AuctionBuyConfig(
        canBuyInAuctionGeneral=c.genConfig.canBuyInAuction,
        canBuyInAuctionAsset=c.assetConfig.canBuyInAuction,
        isUserAllowed=self._isUserAllowed(c.assetConfig.whitelist, _buyer, _asset),
    )


# general liquidation config


@view
@external
def getGenLiqConfig() -> GenLiqConfig:
    data: address = self.data
    c: MetaConfig = staticcall ControlRoomData(data).getManyConfigs(True, True, False)
    vaultBook: address = addys._getVaultBookAddr()

    # priority liq asset vault data
    priorityLiqAssetVaults: DynArray[VaultData, PRIORITY_LIQ_VAULT_DATA] = []
    priorityLiqAssetData: DynArray[VaultLite, PRIORITY_LIQ_VAULT_DATA] = staticcall ControlRoomData(data).getPriorityLiqAssetVaults()
    for pData: VaultLite in priorityLiqAssetData:
        vaultAddr: address = staticcall VaultBook(vaultBook).getAddr(pData.vaultId)
        priorityLiqAssetVaults.append(VaultData(vaultId=pData.vaultId, vaultAddr=vaultAddr, asset=pData.asset))

    # stability pool vault data
    priorityStabVaults: DynArray[VaultData, MAX_STAB_VAULT_DATA] = []
    priorityStabData: DynArray[VaultLite, MAX_STAB_VAULT_DATA] = staticcall ControlRoomData(data).getPriorityStabVaults()
    for pData: VaultLite in priorityStabData:
        vaultAddr: address = staticcall VaultBook(vaultBook).getAddr(pData.vaultId)
        priorityStabVaults.append(VaultData(vaultId=pData.vaultId, vaultAddr=vaultAddr, asset=pData.asset))

    return GenLiqConfig(
        canLiquidate=c.genConfig.canLiquidate,
        keeperFeeRatio=c.genDebtConfig.keeperFeeRatio,
        minKeeperFee=c.genDebtConfig.minKeeperFee,
        ltvPaybackBuffer=c.genDebtConfig.ltvPaybackBuffer,
        genAuctionParams=c.genDebtConfig.genAuctionParams,
        priorityLiqAssetVaults=priorityLiqAssetVaults,
        priorityStabVaults=priorityStabVaults,
    )


@view
@external
def getGenAuctionParams() -> AuctionParams:
    genDebtConfig: GenDebtConfig = staticcall ControlRoomData(self.data).genDebtConfig()
    return genDebtConfig.genAuctionParams


# asset liquidation config


@view
@external
def getAssetLiqConfig(_asset: address) -> AssetLiqConfig:
    c: MetaConfig = staticcall ControlRoomData(self.data).getManyConfigs(False, False, False, _asset)

    # TODO: when setting asset config...
    # shouldTransferToEndaoment -- needs to be stable-ish, etc. Or Stab pool asset (LP token, etc)
    # shouldSwapInStabPools -- check LTV, whitelist/specialStabPoolId, NFT status

    # handle special stab pool
    specialStabPool: VaultData = empty(VaultData)
    if c.assetConfig.specialStabPoolId != 0:
        specialVaultAddr: address = staticcall VaultBook(addys._getVaultBookAddr()).getAddr(c.assetConfig.specialStabPoolId)
        if specialVaultAddr != empty(address):
            firstAsset: address = staticcall Vault(specialVaultAddr).vaultAssets(1) # get first asset
            if firstAsset != empty(address):
                specialStabPool = VaultData(
                    vaultId=c.assetConfig.specialStabPoolId,
                    vaultAddr=specialVaultAddr,
                    asset=firstAsset
                )

    return AssetLiqConfig(
        hasConfig=True,
        shouldBurnAsPayment=c.assetConfig.shouldBurnAsPayment,
        shouldTransferToEndaoment=c.assetConfig.shouldTransferToEndaoment,
        shouldSwapInStabPools=c.assetConfig.shouldSwapInStabPools,
        shouldAuctionInstantly=c.assetConfig.shouldAuctionInstantly,
        customAuctionParams=c.assetConfig.customAuctionParams,
        specialStabPool=specialStabPool,
    )


# stability pool claims


@view
@external
def getStabPoolClaimsConfig(_claimAsset: address, _claimer: address) -> StabPoolClaimsConfig:
    c: MetaConfig = staticcall ControlRoomData(self.data).getManyConfigs(True, False, False, _claimAsset)
    return StabPoolClaimsConfig(
        canClaimInStabPoolGeneral=c.genConfig.canClaimInStabPool,
        canClaimInStabPoolAsset=c.assetConfig.canClaimInStabPool,
        isUserAllowed=self._isUserAllowed(c.assetConfig.whitelist, _claimer, _claimAsset),
    )


# stability pool redemptions


@view
@external
def getStabPoolRedemptionsConfig(_asset: address, _redeemer: address) -> StabPoolRedemptionsConfig:
    c: MetaConfig = staticcall ControlRoomData(self.data).getManyConfigs(True, False, False, _asset)
    return StabPoolRedemptionsConfig(
        canRedeemInStabPoolGeneral=c.genConfig.canRedeemInStabPool,
        canRedeemInStabPoolAsset=c.assetConfig.canRedeemInStabPool,
        isUserAllowed=self._isUserAllowed(c.assetConfig.whitelist, _redeemer, _asset),
    )


# loot claims


@view
@external
def getClaimLootConfig(_user: address, _caller: address) -> ClaimLootConfig:
    data: address = self.data
    c: MetaConfig = staticcall ControlRoomData(data).getManyConfigs(True, False, False)

    canClaimLootForUser: bool = True
    if _user != _caller:
        delegation: ActionDelegation = staticcall ControlRoomData(data).userDelegation(_user, _caller)
        canClaimLootForUser = delegation.canClaimLoot

    return ClaimLootConfig(
        canClaimLoot=c.genConfig.canClaimLoot,
        canClaimLootForUser=canClaimLootForUser,
    )


# rewards config


@view
@external
def getRewardsConfig() -> RewardsConfig:
    c: MetaConfig = staticcall ControlRoomData(self.data).getManyConfigs(False, False, True)
    return RewardsConfig(
        arePointsEnabled=c.rewardsConfig.arePointsEnabled,
        ripePerBlock=c.rewardsConfig.ripePerBlock,
        borrowersAlloc=c.rewardsConfig.borrowersAlloc,
        stakersAlloc=c.rewardsConfig.stakersAlloc,
        votersAlloc=c.rewardsConfig.votersAlloc,
        genDepositorsAlloc=c.rewardsConfig.genDepositorsAlloc,
        stakersPointsAllocTotal=c.totalPointsAllocs.stakersPointsAllocTotal,
        voterPointsAllocTotal=c.totalPointsAllocs.voterPointsAllocTotal,
    )


# deposit points


@view
@external
def getDepositPointsConfig(_asset: address) -> DepositPointsConfig:
    c: MetaConfig = staticcall ControlRoomData(self.data).getManyConfigs(False, False, False, _asset)
    return DepositPointsConfig(
        stakersPointsAlloc=c.assetConfig.stakersPointsAlloc,
        voterPointsAlloc=c.assetConfig.voterPointsAlloc,
        isNft=c.assetConfig.isNft,
    )


# price config


@view
@external
def getPriceConfig() -> PriceConfig:
    data: address = self.data
    genConfig: GenConfig = staticcall ControlRoomData(data).genConfig()
    return PriceConfig(
        staleTime=genConfig.priceStaleTime,
        priorityPriceSourceIds=staticcall ControlRoomData(data).getPriorityPriceSourceIds(),
    )