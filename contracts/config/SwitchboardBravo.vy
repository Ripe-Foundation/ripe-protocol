#        ______   __     __   __   ______  ______   __  __   ______   ______   ______   ______   _____    
#       /\  ___\ /\ \  _ \ \ /\ \ /\__  _\/\  ___\ /\ \_\ \ /\  == \ /\  __ \ /\  __ \ /\  == \ /\  __-.  
#       \ \___  \\ \ \/ ".\ \\ \ \\/_/\ \/\ \ \____\ \  __ \\ \  __< \ \ \/\ \\ \  __ \\ \  __< \ \ \/\ \ 
#        \/\_____\\ \__/".~\_\\ \_\  \ \_\ \ \_____\\ \_\ \_\\ \_____\\ \_____\\ \_\ \_\\ \_\ \_\\ \____- 
#         \/_____/ \/_/   \/_/ \/_/   \/_/  \/_____/ \/_/\/_/ \/_____/ \/_____/ \/_/\/_/ \/_/ /_/ \/____/ 
#                                                   ┳┓        
#                                                   ┣┫┏┓┏┓┓┏┏┓
#                                                   ┻┛┛ ┗┻┗┛┗┛
#
#      Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#      Ripe Foundation (C) 2026 

# @version 0.4.3
# pragma optimize codesize

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock
import interfaces.ConfigStructs as cs

interface StabilityPool:
    def indexOfClaimableAsset(_stabAsset: address, _claimAsset: address) -> uint256: view
    def claimableBalances(_stabAsset: address, _claimAsset: address) -> uint256: view
    def getNumActiveClaimAssets(_stabAsset: address) -> uint256: view
    def totalClaimableBalances(_asset: address) -> uint256: view
    def indexOfAsset(_asset: address) -> uint256: view
    def vaultAssets(_index: uint256) -> address: view
    def getNumVaultAssets() -> uint256: view
    def isPaused() -> bool: view

interface MissionControl:
    def setAssetConfig(_asset: address, _assetConfig: cs.AssetConfig): nonpayable
    def assetConfig(_asset: address) -> cs.AssetConfig: view
    def rewardVaultId(_asset: address) -> uint256: view
    def canPerformLiteAction(_user: address) -> bool: view
    def isSupportedAsset(_asset: address) -> bool: view
    def isStabVaultId(_vaultId: uint256) -> bool: view
    def coreRipeGovVaultId() -> uint256: view
    def maxLtvDeviation() -> uint256: view
    def trainingWheels() -> address: view
    def getRipeHq() -> address: view

interface PriceDesk:
    def tokenScale(_asset: address) -> uint256: view
    def syncTokenScale(_asset: address): nonpayable
    def getAddr(_regId: uint256) -> address: view

interface VaultBook:
    def isValidRegId(_regId: uint256) -> bool: view
    def getAddr(_regId: uint256) -> address: view

interface Lootbox:
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address): nonpayable

interface SwitchboardAlpha:
    def areValidAuctionParams(_params: cs.AuctionParams) -> bool: view

interface Whitelist:
    def isUserAllowed(_user: address, _asset: address) -> bool: view

interface CurvePrices:
    def addGreenRefPoolSnapshot() -> bool: nonpayable

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

flag ActionType:
    ASSET_ADD_NEW
    ASSET_DEPOSIT_PARAMS
    ASSET_LIQ_CONFIG
    ASSET_DEBT_TERMS
    ASSET_WHITELIST

struct AssetUpdate:
    asset: address
    config: cs.AssetConfig

event NewAssetPending:
    asset: indexed(address)
    numVaults: uint256
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
    minDepositBalance: uint256
    debtTermsLtv: uint256
    debtTermsRedemptionThreshold: uint256
    debtTermsLiqThreshold: uint256
    debtTermsLiqFee: uint256
    debtTermsBorrowRate: uint256
    debtTermsDaowry: uint256
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
    auctionStartDiscount: uint256
    auctionMaxDiscount: uint256
    auctionDelay: uint256
    auctionDuration: uint256
    whitelist: address
    isNft: bool

event PendingAssetDepositParamsChange:
    asset: indexed(address)
    numVaultIds: uint256
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
    minDepositBalance: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingAssetLiqConfigChange:
    asset: indexed(address)
    shouldBurnAsPayment: bool
    shouldTransferToEndaoment: bool
    shouldSwapInStabPools: bool
    shouldAuctionInstantly: bool
    specialStabPoolId: uint256
    auctionStartDiscount: uint256
    auctionMaxDiscount: uint256
    auctionDelay: uint256
    auctionDuration: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingAssetDebtTermsChange:
    asset: indexed(address)
    ltv: uint256
    redemptionThreshold: uint256
    liqThreshold: uint256
    liqFee: uint256
    borrowRate: uint256
    daowry: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingAssetWhitelistChange:
    asset: indexed(address)
    whitelist: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event AssetAdded:
    asset: indexed(address)

event AssetDepositParamsSet:
    asset: indexed(address)
    numVaultIds: uint256
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
    minDepositBalance: uint256

event AssetLiqConfigSet:
    asset: indexed(address)
    shouldBurnAsPayment: bool
    shouldTransferToEndaoment: bool
    shouldSwapInStabPools: bool
    shouldAuctionInstantly: bool
    specialStabPoolId: uint256
    auctionStartDiscount: uint256
    auctionMaxDiscount: uint256
    auctionDelay: uint256
    auctionDuration: uint256

event AssetDebtTermsSet:
    asset: indexed(address)
    ltv: uint256
    redemptionThreshold: uint256
    liqThreshold: uint256
    liqFee: uint256
    borrowRate: uint256
    daowry: uint256

event WhitelistAssetSet:
    asset: indexed(address)
    whitelist: indexed(address)

event GreenRefPoolSnapshotAttempted:
    caller: indexed(address)
    priceSourceId: indexed(uint256)
    priceSourceAddr: indexed(address)
    didUpdate: bool

# pending config changes
actionType: public(HashMap[uint256, ActionType]) # aid -> type
pendingAssetConfig: public(HashMap[uint256, AssetUpdate]) # aid -> asset
pendingMissionControl: public(HashMap[uint256, address]) # aid -> target mission control

MAX_ACTIVE_CLAIM_ASSETS: constant(uint256) = 20
MAX_VAULTS_PER_ASSET: constant(uint256) = 10
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100%

GREEN_TOKEN_ID: constant(uint256) = 1
SAVINGS_GREEN_ID: constant(uint256) = 2
LEDGER_ID: constant(uint256) = 4
MISSION_CONTROL_ID: constant(uint256) = 5
SWITCHBOARD_ID: constant(uint256) = 6
PRICE_DESK_ID: constant(uint256) = 7
VAULT_BOOK_ID: constant(uint256) = 8
LOOTBOX_ID: constant(uint256) = 16
SWITCHBOARD_ALPHA_ID: constant(uint256) = 1


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    timeLock.__init__(_minConfigTimeLock, _maxConfigTimeLock, 0, _maxConfigTimeLock)


# addys lite


@view
@internal
def _getMissionControlAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(MISSION_CONTROL_ID)


@view
@internal
def _resolveMissionControl(_missionControl: address) -> address:
    mc: address = self._getMissionControlAddr()
    if _missionControl == empty(address):
        return mc
    assert _missionControl != mc # dev: use empty for current mission control
    return _missionControl


#############
# Add Asset #
#############


@external
def addAsset(
    _asset: address,
    _vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _stakersPointsAlloc: uint256,
    _voterPointsAlloc: uint256,
    _perUserDepositLimit: uint256,
    _globalDepositLimit: uint256,
    _minDepositBalance: uint256 = 0,
    _debtTerms: cs.DebtTerms = empty(cs.DebtTerms),
    _shouldBurnAsPayment: bool = False,
    _shouldTransferToEndaoment: bool = False,
    _shouldSwapInStabPools: bool = True,
    _shouldAuctionInstantly: bool = True,
    _canDeposit: bool = True,
    _canWithdraw: bool = True,
    _canRedeemCollateral: bool = True,
    _canRedeemInStabPool: bool = True,
    _canBuyInAuction: bool = True,
    _canClaimInStabPool: bool = True,
    _specialStabPoolId: uint256 = 0,
    _customAuctionParams: cs.AuctionParams = empty(cs.AuctionParams),
    _whitelist: address = empty(address),
    _isNft: bool = False,
    _missionControl: address = empty(address),
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    mc: address = self._resolveMissionControl(_missionControl)
    assert not staticcall MissionControl(mc).isSupportedAsset(_asset) # dev: must be new asset

    customAuctionParams: cs.AuctionParams = empty(cs.AuctionParams)
    if _customAuctionParams.hasParams:
        customAuctionParams = _customAuctionParams

    config: cs.AssetConfig = cs.AssetConfig(
        vaultIds=_vaultIds,
        stakersPointsAlloc=_stakersPointsAlloc,
        voterPointsAlloc=_voterPointsAlloc,
        perUserDepositLimit=_perUserDepositLimit,
        globalDepositLimit=_globalDepositLimit,
        minDepositBalance=_minDepositBalance,
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
        customAuctionParams=customAuctionParams,
        whitelist=_whitelist,
        isNft=_isNft,
    )
    assert self._isValidAssetConfig(_asset, config, mc) # dev: invalid asset

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ASSET_ADD_NEW
    self.pendingMissionControl[aid] = mc
    self.pendingAssetConfig[aid] = AssetUpdate(
        asset=_asset,
        config=config,
    )

    log NewAssetPending(
        asset=_asset,
        numVaults=len(config.vaultIds),
        stakersPointsAlloc=config.stakersPointsAlloc,
        voterPointsAlloc=config.voterPointsAlloc,
        perUserDepositLimit=config.perUserDepositLimit,
        globalDepositLimit=config.globalDepositLimit,
        minDepositBalance=config.minDepositBalance,
        debtTermsLtv=config.debtTerms.ltv,
        debtTermsRedemptionThreshold=config.debtTerms.redemptionThreshold,
        debtTermsLiqThreshold=config.debtTerms.liqThreshold,
        debtTermsLiqFee=config.debtTerms.liqFee,
        debtTermsBorrowRate=config.debtTerms.borrowRate,
        debtTermsDaowry=config.debtTerms.daowry,
        shouldBurnAsPayment=config.shouldBurnAsPayment,
        shouldTransferToEndaoment=config.shouldTransferToEndaoment,
        shouldSwapInStabPools=config.shouldSwapInStabPools,
        shouldAuctionInstantly=config.shouldAuctionInstantly,
        canDeposit=config.canDeposit,
        canWithdraw=config.canWithdraw,
        canRedeemCollateral=config.canRedeemCollateral,
        canRedeemInStabPool=config.canRedeemInStabPool,
        canBuyInAuction=config.canBuyInAuction,
        canClaimInStabPool=config.canClaimInStabPool,
        specialStabPoolId=config.specialStabPoolId,
        auctionStartDiscount=config.customAuctionParams.startDiscount,
        auctionMaxDiscount=config.customAuctionParams.maxDiscount,
        auctionDelay=config.customAuctionParams.delay,
        auctionDuration=config.customAuctionParams.duration,
        whitelist=config.whitelist,
        isNft=config.isNft,
    )
    return aid


@view
@internal
def _isValidAssetConfig(_asset: address, _config: cs.AssetConfig, _missionControl: address) -> bool:
    if _asset == empty(address):
        return False
    if not self._isValidDebtTerms(_config.debtTerms):
        return False
    if not self._isValidAssetDepositParams(_asset, _config.vaultIds, _config.stakersPointsAlloc, _config.voterPointsAlloc, _config.perUserDepositLimit, _config.globalDepositLimit, _config.minDepositBalance, _missionControl):
        return False
    if not self._isValidAssetLiqConfig(_asset, _config.shouldBurnAsPayment, _config.shouldTransferToEndaoment, _config.shouldSwapInStabPools, _config.shouldAuctionInstantly, _config.specialStabPoolId, _config.isNft, _config.whitelist, _config.debtTerms.ltv, _missionControl):
        return False
    if not self._isValidRedeemCollateralConfig(_asset, _config.canRedeemCollateral, _config.isNft, _config.debtTerms.ltv, _config.shouldTransferToEndaoment):
        return False
    if not self._isValidWhitelist(_config.whitelist):
        return False
    if _config.customAuctionParams.hasParams and not self._areValidAuctionParams(_config.customAuctionParams):
        return False
    return True


##########################
# Asset - Deposit Params #
##########################


@external
def setAssetDepositParams(
    _asset: address,
    _vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _stakersPointsAlloc: uint256,
    _voterPointsAlloc: uint256,
    _perUserDepositLimit: uint256,
    _globalDepositLimit: uint256,
    _minDepositBalance: uint256,
    _missionControl: address = empty(address),
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    mc: address = self._resolveMissionControl(_missionControl)
    assert staticcall MissionControl(mc).isSupportedAsset(_asset) # dev: invalid asset
    assert self._isValidAssetDepositParams(_asset, _vaultIds, _stakersPointsAlloc, _voterPointsAlloc, _perUserDepositLimit, _globalDepositLimit, _minDepositBalance, mc) # dev: invalid asset deposit params
    return self._setPendingAssetConfig(ActionType.ASSET_DEPOSIT_PARAMS, _asset, mc, _vaultIds, _stakersPointsAlloc, _voterPointsAlloc, _perUserDepositLimit, _globalDepositLimit, _minDepositBalance)


@view
@internal
def _isValidAssetDepositParams(
    _asset: address,
    _vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _stakersPointsAlloc: uint256,
    _voterPointsAlloc: uint256,
    _perUserDepositLimit: uint256,
    _globalDepositLimit: uint256,
    _minDepositBalance: uint256,
    _missionControl: address,
) -> bool:
    vaultBook: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(VAULT_BOOK_ID)
    if 0 in [_perUserDepositLimit, _globalDepositLimit]:
        return False
    if max_value(uint256) in [_perUserDepositLimit, _globalDepositLimit, _stakersPointsAlloc, _voterPointsAlloc]:
        return False
    if _stakersPointsAlloc + _voterPointsAlloc > HUNDRED_PERCENT:
        return False
    if _perUserDepositLimit > _globalDepositLimit:
        return False
    if _minDepositBalance > _perUserDepositLimit:
        return False
    for vaultId: uint256 in _vaultIds:
        if not staticcall VaultBook(vaultBook).isValidRegId(vaultId):
            return False
    
    if _stakersPointsAlloc != 0:
        earner: uint256 = staticcall MissionControl(_missionControl).rewardVaultId(_asset)
        if earner == 0:
            return False
        coreVaultId: uint256 = staticcall MissionControl(_missionControl).coreRipeGovVaultId()
        if earner != coreVaultId and not staticcall MissionControl(_missionControl).isStabVaultId(earner):
            return False

    return True


######################
# Asset - Liq Config #
######################


@external
def setAssetLiqConfig(
    _asset: address,
    _shouldBurnAsPayment: bool,
    _shouldTransferToEndaoment: bool,
    _shouldSwapInStabPools: bool,
    _shouldAuctionInstantly: bool,
    _specialStabPoolId: uint256 = 0,
    _customAuctionParams: cs.AuctionParams = empty(cs.AuctionParams),
    _missionControl: address = empty(address),
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    customAuctionParams: cs.AuctionParams = empty(cs.AuctionParams)
    if _customAuctionParams.hasParams:
        assert self._areValidAuctionParams(_customAuctionParams) # dev: invalid auction params
        customAuctionParams = _customAuctionParams

    mc: address = self._resolveMissionControl(_missionControl)
    assert staticcall MissionControl(mc).isSupportedAsset(_asset) # dev: invalid asset
    assetConfig: cs.AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)
    assert self._isValidAssetLiqConfig(_asset, _shouldBurnAsPayment, _shouldTransferToEndaoment, _shouldSwapInStabPools, _shouldAuctionInstantly, _specialStabPoolId, assetConfig.isNft, assetConfig.whitelist, assetConfig.debtTerms.ltv, mc) # dev: invalid asset liq config
    return self._setPendingAssetConfig(ActionType.ASSET_LIQ_CONFIG, _asset, mc, [], 0, 0, 0, 0, 0, empty(cs.DebtTerms), _shouldBurnAsPayment, _shouldTransferToEndaoment, _shouldSwapInStabPools, _shouldAuctionInstantly, _specialStabPoolId, customAuctionParams)


@view
@internal
def _isValidAssetLiqConfig(
    _asset: address,
    _shouldBurnAsPayment: bool,
    _shouldTransferToEndaoment: bool,
    _shouldSwapInStabPools: bool,
    _shouldAuctionInstantly: bool,
    _specialStabPoolId: uint256,
    _isNft: bool,
    _whitelist: address,
    _debtTermsLtv: uint256,
    _missionControl: address,
) -> bool:
    ripeHq: address = gov._getRipeHqFromGov()
    greenToken: address = staticcall RipeHq(ripeHq).getAddr(GREEN_TOKEN_ID)
    savingsGreen: address = staticcall RipeHq(ripeHq).getAddr(SAVINGS_GREEN_ID)
    vaultBook: address = staticcall RipeHq(ripeHq).getAddr(VAULT_BOOK_ID)

    if _shouldSwapInStabPools and not _shouldAuctionInstantly:
        return False

    if _shouldBurnAsPayment:

        # can only burn if green or savings green
        if _asset not in [greenToken, savingsGreen]:
            return False

    if _shouldTransferToEndaoment:

        # cannot transfer to endaoment if green or savings green
        if _asset in [greenToken, savingsGreen]:
            return False

    if _shouldSwapInStabPools:

        # cannot be nft
        if _isNft:
            return False

        # cannot have whitelist if no special stab pool
        if _whitelist != empty(address) and _specialStabPoolId == 0:
            if _whitelist != staticcall MissionControl(_missionControl).trainingWheels():
                return False

        # must have ltv
        if _debtTermsLtv == 0:
            return False

    # verify has correct interface
    if _specialStabPoolId != 0:
        if not staticcall VaultBook(vaultBook).isValidRegId(_specialStabPoolId):
            return False
        stabPool: address = staticcall VaultBook(vaultBook).getAddr(_specialStabPoolId)
        if stabPool == empty(address) or not stabPool.is_contract:
            return False
        numStabAssets: uint256 = staticcall StabilityPool(stabPool).getNumVaultAssets()
        hasStabAsset: bool = numStabAssets != 0
        stabAsset: address = savingsGreen
        if hasStabAsset:
            stabAsset = staticcall StabilityPool(stabPool).vaultAssets(1)
            if stabAsset == empty(address):
                return False

        # configuration validity is structural
        claimAssetIndex: uint256 = staticcall StabilityPool(stabPool).indexOfAsset(_asset)
        claimIndex: uint256 = staticcall StabilityPool(stabPool).indexOfClaimableAsset(stabAsset, _asset)
        activeClaimCount: uint256 = staticcall StabilityPool(stabPool).getNumActiveClaimAssets(stabAsset)
        if hasStabAsset and (
            claimAssetIndex != 0
            or (claimIndex == 0 and activeClaimCount >= MAX_ACTIVE_CLAIM_ASSETS)
        ):
            return False

        # verify has correct interface
        naPair: uint256 = staticcall StabilityPool(stabPool).claimableBalances(stabAsset, _asset)
        na: uint256 = staticcall StabilityPool(stabPool).totalClaimableBalances(savingsGreen)
        naPaused: bool = staticcall StabilityPool(stabPool).isPaused()
        if naPaused:
            return False

    return True


@view
@internal
def _areValidAuctionParams(_params: cs.AuctionParams) -> bool:
    switchboard: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(SWITCHBOARD_ID)
    switchboardAlpha: address = staticcall RipeHq(switchboard).getAddr(SWITCHBOARD_ALPHA_ID)
    return staticcall SwitchboardAlpha(switchboardAlpha).areValidAuctionParams(_params)


######################
# Asset - Debt Terms #
######################


@external
def setAssetDebtTerms(
    _asset: address,
    _ltv: uint256,
    _redemptionThreshold: uint256,
    _liqThreshold: uint256,
    _liqFee: uint256,
    _borrowRate: uint256,
    _daowry: uint256,
    _missionControl: address = empty(address),
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    mc: address = self._resolveMissionControl(_missionControl)
    assert staticcall MissionControl(mc).isSupportedAsset(_asset) # dev: invalid asset
    assetConfig: cs.AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)
    maxDeviation: uint256 = staticcall MissionControl(mc).maxLtvDeviation()

    debtTerms: cs.DebtTerms = cs.DebtTerms(
        ltv=_ltv,
        redemptionThreshold=_redemptionThreshold,
        liqThreshold=_liqThreshold,
        liqFee=_liqFee,
        borrowRate=_borrowRate,
        daowry=_daowry,
    )
    self._assertDebtTermsWithinMaxStep(debtTerms, assetConfig.debtTerms, maxDeviation)
    assert self._isValidDebtTerms(debtTerms) # dev: invalid debt terms
    return self._setPendingAssetConfig(ActionType.ASSET_DEBT_TERMS, _asset, mc, [], 0, 0, 0, 0, 0, debtTerms)


@view
@internal
def _isValidDebtTerms(_debtTerms: cs.DebtTerms) -> bool:
    if _debtTerms.liqThreshold > HUNDRED_PERCENT:
        return False
    if _debtTerms.redemptionThreshold > _debtTerms.liqThreshold:
        return False
    if _debtTerms.ltv > _debtTerms.redemptionThreshold:
        return False
    if _debtTerms.liqFee > HUNDRED_PERCENT or _debtTerms.borrowRate > HUNDRED_PERCENT or _debtTerms.daowry > HUNDRED_PERCENT:
        return False
    if _debtTerms.ltv != 0 and 0 in [_debtTerms.liqFee, _debtTerms.borrowRate]:
        return False
    
    # if ltv > 0, liq threshold and redemption threshold must be > 0
    if _debtTerms.ltv != 0 and (_debtTerms.liqThreshold == 0 or _debtTerms.redemptionThreshold == 0):
        return False

    # make liq threshold and liq bonus work together
    liqSum: uint256 = _debtTerms.liqThreshold + (_debtTerms.liqThreshold * _debtTerms.liqFee // HUNDRED_PERCENT)
    return liqSum <= HUNDRED_PERCENT


@view
@internal
def _isLtvWithinMaxDeviation(_newLtv: uint256, _prevLtv: uint256, _maxDeviation: uint256) -> bool:

    # cannot set ltv to 0 after already non-zero
    if _prevLtv != 0 and _newLtv == 0:
        return False

    if _prevLtv == 0 or _maxDeviation == 0:
        return True

    return HUNDRED_PERCENT > _newLtv and self._isWithinMaxStepDown(_newLtv, _prevLtv, _maxDeviation)


@internal
def _assertDebtTermsWithinMaxStep(_new: cs.DebtTerms, _prev: cs.DebtTerms, _maxDeviation: uint256):
    assert self._isLtvWithinMaxDeviation(_new.ltv, _prev.ltv, _maxDeviation) # dev: ltv is outside max deviation
    assert self._isWithinMaxStepDown(_new.redemptionThreshold, _prev.redemptionThreshold, _maxDeviation) # dev: redemption threshold is outside max deviation
    assert self._isWithinMaxStepDown(_new.liqThreshold, _prev.liqThreshold, _maxDeviation) # dev: liq threshold is outside max deviation
    assert _prev.borrowRate == 0 or _maxDeviation == 0 or _new.borrowRate <= _prev.borrowRate or _new.borrowRate - _prev.borrowRate <= _maxDeviation # dev: borrow rate is outside max deviation


@view
@internal
def _isWithinMaxStepDown(_new: uint256, _prev: uint256, _maxDeviation: uint256) -> bool:
    if _prev == 0 or _maxDeviation == 0:
        return True
    return _new >= _prev or _prev - _new <= _maxDeviation


#####################
# Asset - Whitelist #
#####################


@external
def setWhitelistForAsset(_asset: address, _whitelist: address, _missionControl: address = empty(address)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    mc: address = self._resolveMissionControl(_missionControl)
    assert staticcall MissionControl(mc).isSupportedAsset(_asset) # dev: invalid asset
    assert self._isValidWhitelist(_whitelist) # dev: invalid whitelist
    return self._setPendingAssetConfig(ActionType.ASSET_WHITELIST, _asset, mc, [], 0, 0, 0, 0, 0, empty(cs.DebtTerms), False, False, False, False, 0, empty(cs.AuctionParams), _whitelist)


@view
@internal
def _isValidWhitelist(_whitelist: address) -> bool:
    # make sure has interface
    if _whitelist != empty(address):
        assert not staticcall Whitelist(_whitelist).isUserAllowed(empty(address), empty(address)) # dev: invalid whitelist
    return True


##########################
# Asset - Pending Config #
##########################


@internal
def _setPendingAssetConfig(
    _actionType: ActionType,
    _asset: address,
    _missionControl: address = empty(address),
    _vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET] = [],
    _stakersPointsAlloc: uint256 = 0,
    _voterPointsAlloc: uint256 = 0,
    _perUserDepositLimit: uint256 = 0,
    _globalDepositLimit: uint256 = 0,
    _minDepositBalance: uint256 = 0,
    _debtTerms: cs.DebtTerms = empty(cs.DebtTerms),
    _shouldBurnAsPayment: bool = False,
    _shouldTransferToEndaoment: bool = False,
    _shouldSwapInStabPools: bool = False,
    _shouldAuctionInstantly: bool = False,
    _specialStabPoolId: uint256 = 0,
    _customAuctionParams: cs.AuctionParams = empty(cs.AuctionParams),
    _whitelist: address = empty(address),
) -> uint256:

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = _actionType
    self.pendingMissionControl[aid] = _missionControl
    config: cs.AssetConfig = cs.AssetConfig(
        vaultIds=_vaultIds,
        stakersPointsAlloc=_stakersPointsAlloc,
        voterPointsAlloc=_voterPointsAlloc,
        perUserDepositLimit=_perUserDepositLimit,
        globalDepositLimit=_globalDepositLimit,
        minDepositBalance=_minDepositBalance,
        debtTerms=_debtTerms,
        shouldBurnAsPayment=_shouldBurnAsPayment,
        shouldTransferToEndaoment=_shouldTransferToEndaoment,
        shouldSwapInStabPools=_shouldSwapInStabPools,
        shouldAuctionInstantly=_shouldAuctionInstantly,
        canDeposit=False,
        canWithdraw=False,
        canRedeemCollateral=False,
        canRedeemInStabPool=False,
        canBuyInAuction=False,
        canClaimInStabPool=False,
        specialStabPoolId=_specialStabPoolId,
        customAuctionParams=_customAuctionParams,
        whitelist=_whitelist,
        isNft=False,
    )
    self.pendingAssetConfig[aid] = AssetUpdate(
        asset=_asset,
        config=config,
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    if _actionType == ActionType.ASSET_DEPOSIT_PARAMS:
        log PendingAssetDepositParamsChange(
            asset=_asset,
            numVaultIds=len(_vaultIds),
            stakersPointsAlloc=_stakersPointsAlloc,
            voterPointsAlloc=_voterPointsAlloc,
            perUserDepositLimit=_perUserDepositLimit,
            globalDepositLimit=_globalDepositLimit,
            minDepositBalance=_minDepositBalance,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.ASSET_LIQ_CONFIG:
        log PendingAssetLiqConfigChange(
            asset=_asset,
            shouldBurnAsPayment=_shouldBurnAsPayment,
            shouldTransferToEndaoment=_shouldTransferToEndaoment,
            shouldSwapInStabPools=_shouldSwapInStabPools,
            shouldAuctionInstantly=_shouldAuctionInstantly,
            specialStabPoolId=_specialStabPoolId,
            auctionStartDiscount=_customAuctionParams.startDiscount,
            auctionMaxDiscount=_customAuctionParams.maxDiscount,
            auctionDelay=_customAuctionParams.delay,
            auctionDuration=_customAuctionParams.duration,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.ASSET_DEBT_TERMS:
        log PendingAssetDebtTermsChange(
            asset=_asset,
            ltv=_debtTerms.ltv,
            redemptionThreshold=_debtTerms.redemptionThreshold,
            liqThreshold=_debtTerms.liqThreshold,
            liqFee=_debtTerms.liqFee,
            borrowRate=_debtTerms.borrowRate,
            daowry=_debtTerms.daowry,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.ASSET_WHITELIST:
        log PendingAssetWhitelistChange(
            asset=_asset,
            whitelist=_whitelist,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    return aid


# validation on collateral redemption


@view
@internal
def _isValidRedeemCollateralConfig(
    _asset: address,
    _shouldEnable: bool,
    _isNft: bool,
    _debtTermsLtv: uint256,
    _shouldTransferToEndaoment: bool,
) -> bool:
    if not _shouldEnable:
        return True

    # cannot redeem collateral if nft
    if _isNft:
        return False

    # must have ltv
    if _debtTermsLtv == 0:
        return False

    # any stable-ish assets cannot be redeemed
    if _shouldTransferToEndaoment:
        return False

    return True


# asset config write


@view
@internal
def _vaultIdsEqual(
    _a: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _b: DynArray[uint256, MAX_VAULTS_PER_ASSET],
) -> bool:
    if len(_a) != len(_b):
        return False
    for i: uint256 in range(len(_a), bound=MAX_VAULTS_PER_ASSET):
        if _a[i] != _b[i]:
            return False
    return True


@view
@internal
def _assertAssetAllocStructure(
    _asset: address,
    _missionControl: address,
    _isAddNew: bool,
    _oldVaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _newVaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _oldStakers: uint256,
    _oldVoter: uint256,
    _newStakers: uint256,
    _newVoter: uint256,
):
    if _isAddNew:
        assert _newStakers == 0 and _newVoter == 0 # dev: new asset must start at zero allocs
    membershipChanged: bool = not self._vaultIdsEqual(_oldVaultIds, _newVaultIds)
    allocsChanged: bool = _oldStakers != _newStakers or _oldVoter != _newVoter
    assert not (membershipChanged and allocsChanged) # dev: cannot change membership and allocs together
    earner: uint256 = staticcall MissionControl(_missionControl).rewardVaultId(_asset)
    if membershipChanged:
        assert _oldStakers == 0 and _oldVoter == 0 and _newStakers == 0 and _newVoter == 0 # dev: membership change requires zero allocs
        assert earner == 0 or earner in _newVaultIds # dev: cannot drop reward vault
    if _newStakers != 0 or _newVoter != 0:
        assert earner != 0 # dev: active allocs require reward vault


@internal
def _checkpointSelectedRows(
    _asset: address,
    _vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _vaultAddrs: DynArray[address, MAX_VAULTS_PER_ASSET],
    _lootbox: address,
):
    for i: uint256 in range(len(_vaultIds), bound=MAX_VAULTS_PER_ASSET):
        extcall Lootbox(_lootbox).updateDepositPoints(empty(address), _vaultIds[i], _vaultAddrs[i], _asset)


@internal
def _writeAssetConfig(
    _asset: address,
    _config: cs.AssetConfig,
    _mc: address,
    _actionType: ActionType,
    _oldVaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _oldStakers: uint256,
    _oldVoter: uint256,
):
    if _actionType == ActionType.ASSET_ADD_NEW or _actionType == ActionType.ASSET_DEPOSIT_PARAMS:
        self._assertAssetAllocStructure(_asset, _mc, _actionType == ActionType.ASSET_ADD_NEW, _oldVaultIds, _config.vaultIds, _oldStakers, _oldVoter, _config.stakersPointsAlloc, _config.voterPointsAlloc)
    assert self._isValidAssetConfig(_asset, _config, _mc) # dev: invalid asset config

    needCkpt: bool = (
        _actionType == ActionType.ASSET_DEPOSIT_PARAMS
        and _mc == self._getMissionControlAddr()
        and (_oldStakers != _config.stakersPointsAlloc or _oldVoter != _config.voterPointsAlloc)
    )
    selectedIds: DynArray[uint256, MAX_VAULTS_PER_ASSET] = []
    selectedAddrs: DynArray[address, MAX_VAULTS_PER_ASSET] = []
    lootbox: address = empty(address)
    if needCkpt:
        ripeHq: address = gov._getRipeHqFromGov()
        vaultBook: address = staticcall RipeHq(ripeHq).getAddr(VAULT_BOOK_ID)
        lootbox = staticcall RipeHq(ripeHq).getAddr(LOOTBOX_ID)
        earner: uint256 = staticcall MissionControl(_mc).rewardVaultId(_asset)
        if earner != 0:
            vaultAddr: address = staticcall VaultBook(vaultBook).getAddr(earner)
            assert vaultAddr != empty(address) # dev: invalid vault
            selectedIds.append(earner)
            selectedAddrs.append(vaultAddr)
        self._checkpointSelectedRows(_asset, selectedIds, selectedAddrs, lootbox)

    extcall MissionControl(_mc).setAssetConfig(_asset, _config)

    if needCkpt and (_oldStakers == 0) != (_config.stakersPointsAlloc == 0):
        self._checkpointSelectedRows(_asset, selectedIds, selectedAddrs, lootbox)


#############
# Execution #
#############


@external
def executePendingAction(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    # check time lock
    if not timeLock._confirmAction(_aid):
        if timeLock._isExpired(_aid):
            self._cancelPendingAction(_aid)
        return False

    actionType: ActionType = self.actionType[_aid]
    mc: address = self.pendingMissionControl[_aid]
    if mc == empty(address):
        mc = self._getMissionControlAddr()
    p: AssetUpdate = self.pendingAssetConfig[_aid]

    if actionType == ActionType.ASSET_ADD_NEW:
        assert not staticcall MissionControl(mc).isSupportedAsset(p.asset) # dev: must be new asset
        # Empty old alloc/vault args are unused: structure and needCkpt gate on action type.
        self._writeAssetConfig(p.asset, p.config, mc, ActionType.ASSET_ADD_NEW, [], 0, 0)
        if not p.config.isNft:
            priceDesk: address = staticcall RipeHq(staticcall MissionControl(mc).getRipeHq()).getAddr(PRICE_DESK_ID)
            assert priceDesk != empty(address) # dev: missing price desk
            if staticcall PriceDesk(priceDesk).tokenScale(p.asset) == 0:
                extcall PriceDesk(priceDesk).syncTokenScale(p.asset)
        log AssetAdded(asset=p.asset)

    elif actionType == ActionType.ASSET_DEPOSIT_PARAMS:
        assert mc == self._getMissionControlAddr() # dev: not current mission control
        assert staticcall MissionControl(mc).isSupportedAsset(p.asset) # dev: invalid asset
        config: cs.AssetConfig = staticcall MissionControl(mc).assetConfig(p.asset)
        oldVaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET] = config.vaultIds
        oldStakers: uint256 = config.stakersPointsAlloc
        oldVoter: uint256 = config.voterPointsAlloc
        config.vaultIds = p.config.vaultIds
        config.stakersPointsAlloc = p.config.stakersPointsAlloc
        config.voterPointsAlloc = p.config.voterPointsAlloc
        config.perUserDepositLimit = p.config.perUserDepositLimit
        config.globalDepositLimit = p.config.globalDepositLimit
        config.minDepositBalance = p.config.minDepositBalance
        self._writeAssetConfig(p.asset, config, mc, ActionType.ASSET_DEPOSIT_PARAMS, oldVaultIds, oldStakers, oldVoter)
        log AssetDepositParamsSet(asset=p.asset, numVaultIds=len(p.config.vaultIds), stakersPointsAlloc=p.config.stakersPointsAlloc, voterPointsAlloc=p.config.voterPointsAlloc, perUserDepositLimit=p.config.perUserDepositLimit, globalDepositLimit=p.config.globalDepositLimit, minDepositBalance=p.config.minDepositBalance)

    elif actionType == ActionType.ASSET_LIQ_CONFIG:
        assert staticcall MissionControl(mc).isSupportedAsset(p.asset) # dev: invalid asset
        config: cs.AssetConfig = staticcall MissionControl(mc).assetConfig(p.asset)
        config.shouldBurnAsPayment = p.config.shouldBurnAsPayment
        config.shouldTransferToEndaoment = p.config.shouldTransferToEndaoment
        config.shouldSwapInStabPools = p.config.shouldSwapInStabPools
        config.shouldAuctionInstantly = p.config.shouldAuctionInstantly
        config.specialStabPoolId = p.config.specialStabPoolId
        config.customAuctionParams = p.config.customAuctionParams
        # Empty old alloc/vault args are unused: structure and needCkpt gate on action type.
        self._writeAssetConfig(p.asset, config, mc, ActionType.ASSET_LIQ_CONFIG, [], 0, 0)
        log AssetLiqConfigSet(asset=p.asset, shouldBurnAsPayment=p.config.shouldBurnAsPayment, shouldTransferToEndaoment=p.config.shouldTransferToEndaoment, shouldSwapInStabPools=p.config.shouldSwapInStabPools, shouldAuctionInstantly=p.config.shouldAuctionInstantly, specialStabPoolId=p.config.specialStabPoolId, auctionStartDiscount=p.config.customAuctionParams.startDiscount, auctionMaxDiscount=p.config.customAuctionParams.maxDiscount, auctionDelay=p.config.customAuctionParams.delay, auctionDuration=p.config.customAuctionParams.duration)

    elif actionType == ActionType.ASSET_DEBT_TERMS:
        assert staticcall MissionControl(mc).isSupportedAsset(p.asset) # dev: invalid asset
        config: cs.AssetConfig = staticcall MissionControl(mc).assetConfig(p.asset)
        previousTerms: cs.DebtTerms = config.debtTerms
        pendingTerms: cs.DebtTerms = p.config.debtTerms
        maxDeviation: uint256 = staticcall MissionControl(mc).maxLtvDeviation()
        self._assertDebtTermsWithinMaxStep(pendingTerms, previousTerms, maxDeviation)
        config.debtTerms = pendingTerms
        # Empty old alloc/vault args are unused: structure and needCkpt gate on action type.
        self._writeAssetConfig(p.asset, config, mc, ActionType.ASSET_DEBT_TERMS, [], 0, 0)
        log AssetDebtTermsSet(asset=p.asset, ltv=pendingTerms.ltv, redemptionThreshold=pendingTerms.redemptionThreshold, liqThreshold=pendingTerms.liqThreshold, liqFee=pendingTerms.liqFee, borrowRate=pendingTerms.borrowRate, daowry=pendingTerms.daowry)

    elif actionType == ActionType.ASSET_WHITELIST:
        assert staticcall MissionControl(mc).isSupportedAsset(p.asset) # dev: invalid asset
        config: cs.AssetConfig = staticcall MissionControl(mc).assetConfig(p.asset)
        config.whitelist = p.config.whitelist
        # Empty old alloc/vault args are unused: structure and needCkpt gate on action type.
        self._writeAssetConfig(p.asset, config, mc, ActionType.ASSET_WHITELIST, [], 0, 0)
        log WhitelistAssetSet(asset=p.asset, whitelist=p.config.whitelist)

    self.actionType[_aid] = empty(ActionType)
    self.pendingMissionControl[_aid] = empty(address)
    return True


# cancel action


@external
def cancelPendingAction(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    self._cancelPendingAction(_aid)
    return True


@internal
def _cancelPendingAction(_aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.actionType[_aid] = empty(ActionType)
    self.pendingMissionControl[_aid] = empty(address)


###########################
# GREEN Ref Pool Snapshot #
###########################


@external
def addGreenRefPoolSnapshot(_curvePricesId: uint256) -> bool:
    if not gov._canGovern(msg.sender):
        assert staticcall MissionControl(self._getMissionControlAddr()).canPerformLiteAction(msg.sender) # dev: no perms

    priceDesk: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(PRICE_DESK_ID)
    assert priceDesk != empty(address) # dev: missing price desk

    priceSourceAddr: address = staticcall PriceDesk(priceDesk).getAddr(_curvePricesId)
    assert priceSourceAddr != empty(address) # dev: invalid price source id

    didUpdate: bool = extcall CurvePrices(priceSourceAddr).addGreenRefPoolSnapshot()
    log GreenRefPoolSnapshotAttempted(
        caller=msg.sender,
        priceSourceId=_curvePricesId,
        priceSourceAddr=priceSourceAddr,
        didUpdate=didUpdate,
    )
    return didUpdate
