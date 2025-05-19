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

interface Whitelist:
    def isUserAllowed(_user: address, _asset: address) -> bool: view

interface VaultBook:
    def getAddr(_regId: uint256) -> address: view

struct DebtTerms:
    ltv: uint256
    redemptionThreshold: uint256
    liqThreshold: uint256
    liqFee: uint256
    borrowRate: uint256
    daowry: uint256

struct VaultData:
    vaultId: uint256
    vaultAddr: address
    asset: address

struct AuctionParams:
    hasParams: bool
    startDiscount: uint256
    minEntitled: uint256
    maxDiscount: uint256
    minBidIncrement: uint256
    maxBidIncrement: uint256
    delay: uint256
    duration: uint256
    extension: uint256

struct GenConfig:
    canDeposit: bool
    canWithdraw: bool
    canBorrow: bool
    canRepay: bool
    canRedeemCollateral: bool
    canRedeemInStabPool: bool
    canClaimInStabPool: bool
    canBuyInAuction: bool
    canLiquidate: bool
    canClaimLoot: bool
    perUserMaxAssetsPerVault: uint256
    perUserMaxVaults: uint256

struct GenDebtConfig:
    numAllowedBorrowers: uint256
    maxBorrowPerInterval: uint256
    numBlocksPerInterval: uint256
    perUserDebtLimit: uint256
    globalDebtLimit: uint256
    minDebtAmount: uint256
    isDaowryEnabled: bool
    ltvPaybackBuffer: uint256
    keeperFeeRatio: uint256
    minKeeperFee: uint256
    genAuctionParams: AuctionParams
    genStabPoolIds: DynArray[uint256, MAX_GEN_STAB_POOLS]

struct AssetConfig:
    stakersAlloc: uint256
    voteDepositorAlloc: uint256
    canDeposit: bool
    canWithdraw: bool
    canRedeemCollateral: bool
    canRedeemInStabPool: bool
    canClaimInStabPool: bool
    canBuyInAuction: bool
    shouldTransferToEndaoment: bool
    shouldSwapInStabPools: bool
    shouldAuctionInstantly: bool
    whitelist: address
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
    debtTerms: DebtTerms
    isStable: bool
    isNft: bool
    specialStabPoolId: uint256
    customAuctionParams: AuctionParams

struct UserConfig:
    canAnyoneDeposit: bool
    canAnyoneRepayDebt: bool

struct ActionDelegation:
    canWithdraw: bool
    canBorrow: bool
    canClaimFromStabPool: bool
    canClaimLoot: bool

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
    genStabPools: DynArray[VaultData, MAX_GEN_STAB_POOLS]

struct AssetLiqConfig:
    hasConfig: bool
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
    arePointsEnabled: bool
    stakers: uint256
    stakersTotal: uint256
    voteDepositor: uint256
    voteDepositorTotal: uint256

struct RipeRewardsAllocs:
    stakers: uint256
    voteDepositors: uint256
    genDepositors: uint256
    borrowers: uint256

struct RipeRewardsConfig:
    ripeRewardsAllocs: RipeRewardsAllocs
    ripePerBlock: uint256

# global config
genConfig: public(GenConfig)
genDebtConfig: public(GenDebtConfig)
assetConfig: public(HashMap[address, AssetConfig]) # asset -> config

# user config
userConfig: public(HashMap[address, UserConfig]) # user -> config
userDelegation: public(HashMap[address, HashMap[address, ActionDelegation]]) # user -> caller -> config

# ripe rewards
ripeAllocs: public(RipeRewardsAllocs)
ripePerBlock: public(uint256)
arePointsEnabled: public(bool)

# deposit points allocs
stakersAllocTotal: public(uint256)
voteDepositorAllocTotal: public(uint256)

MAX_GEN_STAB_POOLS: constant(uint256) = 10


# init
@deploy
def __init__(_ripeHq: address):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False) # no minting


#################
# Global Config #
#################


@external
def setGeneralConfig(
    _perUserMaxAssetsPerVault: uint256,
    _perUserMaxVaults: uint256,
    _canDeposit: bool,
    _canWithdraw: bool,
    _canBorrow: bool,
    _canRepay: bool,
    _canRedeemCollateral: bool,
    _canRedeemInStabPool: bool,
    _canClaimInStabPool: bool,
    _canBuyInAuction: bool,
    _canLiquidate: bool,
    _canClaimLoot: bool,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    # TODO: add time lock, validation, event

    self.genConfig = GenConfig(
        canDeposit=_canDeposit,
        canWithdraw=_canWithdraw,
        canBorrow=_canBorrow,
        canRepay=_canRepay,
        canRedeemCollateral=_canRedeemCollateral,
        canRedeemInStabPool=_canRedeemInStabPool,
        canClaimInStabPool=_canClaimInStabPool,
        canBuyInAuction=_canBuyInAuction,
        canLiquidate=_canLiquidate,
        canClaimLoot=_canClaimLoot,
        perUserMaxAssetsPerVault=_perUserMaxAssetsPerVault,
        perUserMaxVaults=_perUserMaxVaults,
    )
    return True


# general debt config


@external
def setGenDebtConfig(
    _numAllowedBorrowers: uint256,
    _maxBorrowPerInterval: uint256,
    _numBlocksPerInterval: uint256,
    _perUserDebtLimit: uint256,
    _globalDebtLimit: uint256,
    _minDebtAmount: uint256,
    _isDaowryEnabled: bool,
    _ltvPaybackBuffer: uint256,
    _keeperFeeRatio: uint256,
    _minKeeperFee: uint256,
    _genAuctionParams: AuctionParams,
    _genStabPoolIds: DynArray[uint256, MAX_GEN_STAB_POOLS],
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    # TODO: add time lock, validation, event

    self.genDebtConfig = GenDebtConfig(
        numAllowedBorrowers=_numAllowedBorrowers,
        maxBorrowPerInterval=_maxBorrowPerInterval,
        numBlocksPerInterval=_numBlocksPerInterval,
        perUserDebtLimit=_perUserDebtLimit,
        globalDebtLimit=_globalDebtLimit,
        minDebtAmount=_minDebtAmount,
        isDaowryEnabled=_isDaowryEnabled,
        ltvPaybackBuffer=_ltvPaybackBuffer,
        keeperFeeRatio=_keeperFeeRatio,
        minKeeperFee=_minKeeperFee,
        genAuctionParams=_genAuctionParams,
        genStabPoolIds=_genStabPoolIds,
    )
    return True


################
# Asset Config #
################


@external
def setAssetConfig(
    _asset: address,
    _stakersAlloc: uint256,
    _voteDepositorAlloc: uint256,
    _canDeposit: bool,
    _canWithdraw: bool,
    _canRedeemCollateral: bool,
    _canRedeemInStabPool: bool,
    _canClaimInStabPool: bool,
    _canBuyInAuction: bool,
    _shouldTransferToEndaoment: bool,
    _shouldSwapInStabPools: bool,
    _shouldAuctionInstantly: bool,
    _whitelist: address,
    _perUserDepositLimit: uint256,
    _globalDepositLimit: uint256,
    _debtTerms: DebtTerms,
    _isStable: bool,
    _isNft: bool,
    _specialStabPoolId: uint256,
    _customAuctionParams: AuctionParams,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    # TODO: add time lock, validation, event

    # update total allocs
    prevConfig: AssetConfig = self.assetConfig[_asset]
    self.stakersAllocTotal += _stakersAlloc - prevConfig.stakersAlloc
    self.voteDepositorAllocTotal += _voteDepositorAlloc - prevConfig.voteDepositorAlloc

    self.assetConfig[_asset] = AssetConfig(
        stakersAlloc=_stakersAlloc,
        voteDepositorAlloc=_voteDepositorAlloc,
        canDeposit=_canDeposit,
        canWithdraw=_canWithdraw,
        canRedeemCollateral=_canRedeemCollateral,
        canRedeemInStabPool=_canRedeemInStabPool,
        canClaimInStabPool=_canClaimInStabPool,
        canBuyInAuction=_canBuyInAuction,
        shouldTransferToEndaoment=_shouldTransferToEndaoment,
        shouldSwapInStabPools=_shouldSwapInStabPools,
        shouldAuctionInstantly=_shouldAuctionInstantly,
        whitelist=_whitelist,
        perUserDepositLimit=_perUserDepositLimit,
        globalDepositLimit=_globalDepositLimit,
        debtTerms=_debtTerms,
        isStable=_isStable,
        isNft=_isNft,
        specialStabPoolId=_specialStabPoolId,
        customAuctionParams=_customAuctionParams,
    )
    return True


###############
# User Config #
###############


@external
def setUserConfig(
    _canAnyoneDeposit: bool = True,
    _canAnyoneRepayDebt: bool = True,
) -> bool:

    # TODO: add time lock, validation, event

    self.userConfig[msg.sender] = UserConfig(
        canAnyoneDeposit=_canAnyoneDeposit,
        canAnyoneRepayDebt=_canAnyoneRepayDebt,
    )
    return True


@external
def setUserDelegation(
    _user: address,
    _canWithdraw: bool = True,
    _canBorrow: bool = True,
    _canClaimFromStabPool: bool = True,
    _canClaimLoot: bool = True,
) -> bool:

    # TODO: add time lock, validation, event

    self.userDelegation[msg.sender][_user] = ActionDelegation(
        canWithdraw=_canWithdraw,
        canBorrow=_canBorrow,
        canClaimFromStabPool=_canClaimFromStabPool,
        canClaimLoot=_canClaimLoot,
    )
    return True


####################
# Rewards / Points #
####################


@external
def setRipeRewardsConfig(
    _ripeRewardsAllocs: RipeRewardsAllocs,
    _ripePerBlock: uint256,
    _arePointsEnabled: bool,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    # TODO: add time lock, validation, event

    self.ripeAllocs = _ripeRewardsAllocs
    self.ripePerBlock = _ripePerBlock
    self.arePointsEnabled = _arePointsEnabled
    return True


###########
# Helpers #
###########


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
    genConfig: GenConfig = self.genConfig
    assetConfig: AssetConfig = self.assetConfig[_asset]

    return TellerDepositConfig(
        canDepositGeneral=genConfig.canDeposit,
        canDepositAsset=assetConfig.canDeposit,
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
    genConfig: GenConfig = self.genConfig
    assetConfig: AssetConfig = self.assetConfig[_asset]

    canWithdrawForUser: bool = True
    if _user != _caller:
        canWithdrawForUser = self.userDelegation[_user][_caller].canWithdraw

    return TellerWithdrawConfig(
        canWithdrawGeneral=genConfig.canWithdraw,
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
    genConfig: GenConfig = self.genConfig
    genDebtConfig: GenDebtConfig = self.genDebtConfig

    canBorrowForUser: bool = True
    if _user != _caller:
        canBorrowForUser = self.userDelegation[_user][_caller].canBorrow

    return BorrowConfig(
        canBorrow=genConfig.canBorrow,
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
    genConfig: GenConfig = self.genConfig
    assetConfig: AssetConfig = self.assetConfig[_asset]

    # TODO: when setting asset config -> canRedeemCollateral, make sure: has LTV, not stable, not NFT

    return RedeemCollateralConfig(
        canRedeemCollateralGeneral=genConfig.canRedeemCollateral,
        canRedeemCollateralAsset=assetConfig.canRedeemCollateral,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _redeemer, _asset),
        ltvPaybackBuffer=self.genDebtConfig.ltvPaybackBuffer,
    )


# auction purchases


@view
@external
def getAuctionBuyConfig(_asset: address, _buyer: address) -> AuctionBuyConfig:
    genConfig: GenConfig = self.genConfig
    assetConfig: AssetConfig = self.assetConfig[_asset]

    return AuctionBuyConfig(
        canBuyInAuctionGeneral=genConfig.canBuyInAuction,
        canBuyInAuctionAsset=assetConfig.canBuyInAuction,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _buyer, _asset),
    )


# general liquidation config


@view
@external
def getGenLiqConfig() -> GenLiqConfig:
    genDebtConfig: GenDebtConfig = self.genDebtConfig

    # TODO: put together all this data
    genStabPools: DynArray[VaultData, MAX_GEN_STAB_POOLS] = []

    return GenLiqConfig(
        canLiquidate=self.genConfig.canLiquidate,
        keeperFeeRatio=genDebtConfig.keeperFeeRatio,
        minKeeperFee=genDebtConfig.minKeeperFee,
        ltvPaybackBuffer=genDebtConfig.ltvPaybackBuffer,
        genAuctionParams=genDebtConfig.genAuctionParams,
        genStabPools=genStabPools,
    )


# asset liquidation config


@view
@external
def getAssetLiqConfig(_asset: address) -> AssetLiqConfig:
    assetConfig: AssetConfig = self.assetConfig[_asset]

    # TODO: when setting asset config...
    # shouldTransferToEndaoment -- needs to be stable-ish, etc. Or Stab pool asset (LP token, etc)
    # shouldSwapInStabPools -- check LTV, whitelist/specialStabPoolId, NFT status

    # TODO: handle special stab pool
    specialStabPool: VaultData = empty(VaultData)

    return AssetLiqConfig(
        hasConfig=True,
        shouldTransferToEndaoment=assetConfig.shouldTransferToEndaoment,
        shouldSwapInStabPools=assetConfig.shouldSwapInStabPools,
        shouldAuctionInstantly=assetConfig.shouldAuctionInstantly,
        customAuctionParams=assetConfig.customAuctionParams,
        specialStabPool=specialStabPool,
    )


# stability pool claims


@view
@external
def getStabPoolClaimsConfig(_asset: address, _claimer: address) -> StabPoolClaimsConfig:
    genConfig: GenConfig = self.genConfig
    assetConfig: AssetConfig = self.assetConfig[_asset]

    return StabPoolClaimsConfig(
        canClaimInStabPoolGeneral=genConfig.canClaimInStabPool,
        canClaimInStabPoolAsset=assetConfig.canClaimInStabPool,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _claimer, _asset),
    )


# stability pool redemptions


@view
@external
def getStabPoolRedemptionsConfig(_asset: address, _redeemer: address) -> StabPoolRedemptionsConfig:
    genConfig: GenConfig = self.genConfig
    assetConfig: AssetConfig = self.assetConfig[_asset]

    return StabPoolRedemptionsConfig(
        canRedeemInStabPoolGeneral=genConfig.canRedeemInStabPool,
        canRedeemInStabPoolAsset=assetConfig.canRedeemInStabPool,
        isUserAllowed=self._isUserAllowed(assetConfig.whitelist, _redeemer, _asset),
    )


# loot claims


@view
@external
def getClaimLootConfig(_user: address, _caller: address) -> ClaimLootConfig:
    genConfig: GenConfig = self.genConfig

    canClaimLootForUser: bool = True
    if _user != _caller:
        canClaimLootForUser = self.userDelegation[_user][_caller].canClaimLoot

    return ClaimLootConfig(
        canClaimLoot=genConfig.canClaimLoot,
        canClaimLootForUser=canClaimLootForUser,
    )


# ripe rewards


@view
@external
def getRipeRewardsConfig() -> RipeRewardsConfig:
    return RipeRewardsConfig(
        ripeRewardsAllocs=self.ripeAllocs,
        ripePerBlock=self.ripePerBlock,
    )


# deposit points


@view
@external
def getDepositPointsConfig(_user: address, _asset: address) -> DepositPointsConfig:
    assetConfig: AssetConfig = self.assetConfig[_asset]

    # eventually we could turn off points for specific users or assets

    return DepositPointsConfig(
        arePointsEnabled=self.arePointsEnabled,
        stakers=assetConfig.stakersAlloc,
        stakersTotal=self.stakersAllocTotal,
        voteDepositor=assetConfig.voteDepositorAlloc,
        voteDepositorTotal=self.voteDepositorAllocTotal,
    )


# borrow points


@view
@external
def areBorrowPointsEnabled(_user: address) -> bool:
    # eventually we could turn off points for specific users or assets
    return self.arePointsEnabled