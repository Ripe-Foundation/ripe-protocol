# @version 0.4.1

from interfaces import Vault
from ethereum.ercs import IERC20

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

struct DepositConfig:
    canDeposit: bool
    isUserAllowed: bool
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
    maxDepositAssetsPerVault: uint256
    maxDepositVaults: uint256

struct DebtTerms:
    ltv: uint256
    redemptionThreshold: uint256
    liqThreshold: uint256
    liqFee: uint256
    borrowRate: uint256
    daowry: uint256

struct BorrowConfig:
    isBorrowEnabled: bool
    numAllowedBorrowers: uint256
    maxBorrowPerInterval: uint256
    numBlocksPerInterval: uint256
    perUserDebtLimit: uint256
    globalDebtLimit: uint256
    minDebtAmount: uint256

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
ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True


##########################
# Deposits / Withdrawals #
##########################


@view
@external
def getDepositConfig(_vaultId: uint256, _asset: address, _user: address) -> DepositConfig:
    # TODO: implement
    return empty(DepositConfig)


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
def getBorrowConfig() -> BorrowConfig:
    # TODO: implement
    return empty(BorrowConfig)


@view
@external
def isRepayEnabled() -> bool:
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