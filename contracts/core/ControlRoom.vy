# @version 0.4.1

initializes: addys
exports: addys.__interface__
import contracts.modules.Addys as addys

struct DepositConfig:
    canDeposit: bool
    isUserAllowed: bool
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
    maxDepositAssetsPerVault: uint256
    maxDepositVaults: uint256
    canOthersDepositForUser: bool

struct WithdrawConfig:
    canWithdraw: bool
    isUserAllowed: bool
    canWithdrawForUser: bool

struct DebtTerms:
    ltv: uint256
    redemptionThreshold: uint256
    liqThreshold: uint256
    liqFee: uint256
    borrowRate: uint256
    daowry: uint256

struct BorrowConfig:
    isBorrowEnabled: bool
    canBorrowForUser: bool
    numAllowedBorrowers: uint256
    maxBorrowPerInterval: uint256
    numBlocksPerInterval: uint256
    perUserDebtLimit: uint256
    globalDebtLimit: uint256
    minDebtAmount: uint256

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

# config
isActivated: public(bool)

MAX_GEN_STAB_POOLS: constant(uint256) = 10


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    self.isActivated = True


##########################
# Deposits / Withdrawals #
##########################


@view
@external
def getDepositConfig(_vaultId: uint256, _asset: address, _user: address) -> DepositConfig:
    # TODO: implement
    return empty(DepositConfig)


@view
@external
def getWithdrawConfig(_vaultId: uint256, _asset: address, _user: address, _caller: address) -> WithdrawConfig:
    # TODO: implement
    return empty(WithdrawConfig)


########
# Debt #
########


@view
@external
def getDebtTerms(_vaultId: uint256, _asset: address) -> DebtTerms:
    # TODO: implement
    return empty(DebtTerms)


@view
@external
def getBorrowConfig(_user: address, _caller: address) -> BorrowConfig:
    # TODO: implement
    return empty(BorrowConfig)


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
def canOthersClaimLootForUser(_user: address) -> bool:
    # TODO: implement
    return False
