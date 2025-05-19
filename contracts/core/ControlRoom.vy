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

struct GenConfig:
    canDeposit: bool
    canWithdraw: bool
    canBorrow: bool
    canRepay: bool
    canRedeemCollateral: bool
    canRedeemInStabPool: bool
    canClaimInStabPool: bool
    canBuyAuction: bool
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
    ltvPaybackBuffer: uint256
    keeperFeeRatio: uint256
    minKeeperFee: uint256
    genAuctionParams: AuctionParams
    genStabPoolIds: DynArray[uint256, MAX_GEN_STAB_POOLS]

struct AssetConfig:
    canDeposit: bool
    canWithdraw: bool
    canRedeemCollateral: bool
    canBuyInAuction: bool
    shouldSwapInStabPool: bool
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

struct WithdrawConfig:
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


##########






struct DebtTerms:
    ltv: uint256
    redemptionThreshold: uint256
    liqThreshold: uint256
    liqFee: uint256
    borrowRate: uint256
    daowry: uint256

struct RepayConfig:
    isRepayEnabled: bool
    canOthersRepayForUser: bool

struct RedeemCollateralConfig:
    canRedeemCollateral: bool
    ltvPaybackBuffer: uint256

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

struct VaultData:
    vaultId: uint256
    vaultAddr: address
    asset: address

struct GenLiqConfig:
    keeperFeeRatio: uint256
    minKeeperFee: uint256
    ltvPaybackBuffer: uint256
    genAuctionParams: AuctionParams
    genStabPools: DynArray[VaultData, MAX_GEN_STAB_POOLS]

struct AssetLiqConfig:
    hasConfig: bool
    hasLtv: bool
    hasWhitelist: bool
    isNft: bool
    isStable: bool
    specialStabPool: VaultData
    canAuctionInstantly: bool
    customAuctionParams: AuctionParams

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

# global config
genConfig: public(GenConfig)
genDebtConfig: public(GenDebtConfig)
assetConfig: public(HashMap[address, AssetConfig]) # asset -> config

# user config
userConfig: public(HashMap[address, UserConfig]) # user -> config
userDelegation: public(HashMap[address, HashMap[address, ActionDelegation]]) # user -> caller -> config

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
    _canBuyAuction: bool,
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
        canBuyAuction=_canBuyAuction,
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
    _canDeposit: bool,
    _canWithdraw: bool,
    _canRedeemCollateral: bool,
    _canBuyInAuction: bool,
    _shouldSwapInStabPool: bool,
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

    self.assetConfig[_asset] = AssetConfig(
        canDeposit=_canDeposit,
        canWithdraw=_canWithdraw,
        canRedeemCollateral=_canRedeemCollateral,
        canBuyInAuction=_canBuyInAuction,
        shouldSwapInStabPool=_shouldSwapInStabPool,
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


##########################
# Deposits / Withdrawals #
##########################


@view
@external
def getTellerDepositConfig(_asset: address, _user: address) -> TellerDepositConfig:
    genConfig: GenConfig = self.genConfig
    assetConfig: AssetConfig = self.assetConfig[_asset]

    isUserAllowed: bool = True 
    if assetConfig.whitelist != empty(address):
        isUserAllowed = staticcall Whitelist(assetConfig.whitelist).isUserAllowed(_user, _asset)

    return TellerDepositConfig(
        canDepositGeneral=genConfig.canDeposit,
        canDepositAsset=assetConfig.canDeposit,
        isUserAllowed=isUserAllowed,
        perUserDepositLimit=assetConfig.perUserDepositLimit,
        globalDepositLimit=assetConfig.globalDepositLimit,
        perUserMaxAssetsPerVault=genConfig.perUserMaxAssetsPerVault,
        perUserMaxVaults=genConfig.perUserMaxVaults,
        canAnyoneDeposit=self.userConfig[_user].canAnyoneDeposit,
    )


@view
@external
def getTellerWithdrawConfig(_asset: address, _user: address, _caller: address) -> WithdrawConfig:
    genConfig: GenConfig = self.genConfig
    assetConfig: AssetConfig = self.assetConfig[_asset]

    isUserAllowed: bool = True 
    if assetConfig.whitelist != empty(address):
        isUserAllowed = staticcall Whitelist(assetConfig.whitelist).isUserAllowed(_user, _asset)

    canWithdrawForUser: bool = True
    if _user != _caller:
        canWithdrawForUser = self.userDelegation[_user][_caller].canWithdraw

    return WithdrawConfig(
        canWithdrawGeneral=genConfig.canWithdraw,
        canWithdrawAsset=assetConfig.canWithdraw,
        isUserAllowed=isUserAllowed,
        canWithdrawForUser=canWithdrawForUser,
    )


########
# Debt #
########


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
    )


@view
@external
def getDebtTerms(_vaultId: uint256, _asset: address) -> DebtTerms:
    # TODO: implement
    return empty(DebtTerms)


@view
@external
def getRepayConfig(_user: address) -> RepayConfig:
    # TODO: implement
    return empty(RepayConfig)


@view
@external
def isDaowryEnabled() -> bool:
    # TODO: implement
    return False


@view
@external
def getRedeemCollateralConfig(_vaultId: uint256, _asset: address) -> RedeemCollateralConfig:
    # check general canRedeem 
    # check if has LTV
    # check whitelist
    # check if asset is stable
    # check if NFT
    return empty(RedeemCollateralConfig)



#################
# Auction House #
#################


@view
@external
def getGenLiqConfig() -> GenLiqConfig:
    # TODO: implement
    return empty(GenLiqConfig)


@view
@external
def getAssetLiqConfig(_vaultId: uint256, _asset: address) -> AssetLiqConfig:
    # TODO: implement
    return empty(AssetLiqConfig)


@view
@external
def canBuyAuction(_vaultId: uint256, _asset: address, _buyer: address) -> bool:

    # check global setting (if auctions enabled)
    # check whitelist (if it exists)

    # TODO: implement
    return True


####################
# Rewards / Points #
####################


@view
@external
def getRipeRewardsConfig() -> RipeRewardsConfig:
    # TODO: implement
    return empty(RipeRewardsConfig)


@view
@external
def getDepositPointsAllocs(_vaultId: uint256, _asset: address) -> DepositPointsAllocs:
    # TODO: implement
    return empty(DepositPointsAllocs)


@view
@external
def canCallerClaimLootForUser(_user: address, _caller: address) -> bool:
    # TODO: implement
    return False
