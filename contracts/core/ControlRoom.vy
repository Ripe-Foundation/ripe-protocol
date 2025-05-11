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

# config
isActivated: public(bool)


@deploy
def __init__(_hq: address):
    addys.__init__(_hq)
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
