# @version 0.4.1

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

struct GenConfig:
    perUserMaxVaults: uint256
    perUserMaxAssetsPerVault: uint256
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

struct MetaConfig:
    genConfig: GenConfig
    genDebtConfig: GenDebtConfig
    assetConfig: AssetConfig
    userConfig: UserConfig
    rewardsConfig: RipeRewardsConfig
    totalPointsAllocs: TotalPointsAllocs

# global config
genConfig: public(GenConfig)
genDebtConfig: public(GenDebtConfig)
assetConfig: public(HashMap[address, AssetConfig]) # asset -> config

# user config
userConfig: public(HashMap[address, UserConfig]) # user -> config
userDelegation: public(HashMap[address, HashMap[address, ActionDelegation]]) # user -> caller -> config

# ripe rewards
rewardsConfig: public(RipeRewardsConfig)
totalPointsAllocs: public(TotalPointsAllocs)

RIPE_HQ: immutable(address)
CONTROL_ROOM_ID: constant(uint256) = 9


@deploy
def __init__(_ripeHq: address):
    assert _ripeHq != empty(address) # dev: invalid ripe hq
    RIPE_HQ = _ripeHq


# only control room has access


@view
@internal
def _getControlRoomAddr() -> address:
    return staticcall RipeHq(RIPE_HQ).getAddr(CONTROL_ROOM_ID)


#################
# Global Config #
#################


@external
def setGeneralConfig(_genConfig: GenConfig):
    assert msg.sender == self._getControlRoomAddr() # dev: no perms
    self.genConfig = _genConfig


@external
def setGeneralDebtConfig(_genDebtConfig: GenDebtConfig):
    assert msg.sender == self._getControlRoomAddr() # dev: no perms
    self.genDebtConfig = _genDebtConfig


################
# Asset Config #
################


@external
def setAssetConfig(_asset: address, _assetConfig: AssetConfig):
    assert msg.sender == self._getControlRoomAddr() # dev: no perms
    self._updatePointsAllocs(_asset, _assetConfig.stakersPointsAlloc, _assetConfig.voterPointsAlloc)
    self.assetConfig[_asset] = _assetConfig


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


####################
# Rewards / Points #
####################


@external
def setRipeRewardsConfig(_rewardsConfig: RipeRewardsConfig):
    assert msg.sender == self._getControlRoomAddr() # dev: no perms
    self.rewardsConfig = _rewardsConfig


###############
# User Config #
###############


@external
def setUserConfig(_user: address,_userConfig: UserConfig):
    assert msg.sender == self._getControlRoomAddr() # dev: no perms
    self.userConfig[_user] = _userConfig


@external
def setUserDelegation(_user: address, _delegate: address, _config: ActionDelegation):
    assert msg.sender == self._getControlRoomAddr() # dev: no perms
    self.userDelegation[_user][_delegate] = _config


#############
# Batch Get #
#############


@view
@external
def getManyConfigs(
    _getGenConfig: bool,
    _getDebtConfig: bool,
    _getRewardsConfig: bool,
    _asset: address = empty(address),
    _user: address = empty(address),
) -> MetaConfig:

    genConfig: GenConfig = empty(GenConfig)
    if _getGenConfig:
        genConfig = self.genConfig

    genDebtConfig: GenDebtConfig = empty(GenDebtConfig)
    if _getDebtConfig:
        genDebtConfig = self.genDebtConfig

    rewardsConfig: RipeRewardsConfig = empty(RipeRewardsConfig)
    totalPointsAllocs: TotalPointsAllocs = empty(TotalPointsAllocs)
    if _getRewardsConfig:
        rewardsConfig = self.rewardsConfig
        totalPointsAllocs = self.totalPointsAllocs

    assetConfig: AssetConfig = empty(AssetConfig)
    if _asset != empty(address):
        assetConfig = self.assetConfig[_asset]

    userConfig: UserConfig = empty(UserConfig)
    if _user != empty(address):
        userConfig = self.userConfig[_user]

    return MetaConfig(
        genConfig=genConfig,
        genDebtConfig=genDebtConfig,
        assetConfig=assetConfig,
        userConfig=userConfig,
        rewardsConfig=rewardsConfig,
        totalPointsAllocs=totalPointsAllocs,
    )


#########
# Other #
#########


@view
@external
def ripeHq() -> address:
    return RIPE_HQ


@view
@external
def getControlRoomId() -> uint256:
    return CONTROL_ROOM_ID