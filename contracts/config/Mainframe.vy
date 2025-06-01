# @version 0.4.1
# pragma optimize codesize

exports: gov.__interface__
exports: addys.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: addys
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.Addys as addys
import contracts.modules.TimeLock as timeLock

interface MissionControl:
    def setAssetConfig(_asset: address, _assetConfig: AssetConfig): nonpayable
    def assetConfig(_asset: address) -> AssetConfig: view
    def isSupportedAsset(_asset: address) -> bool: view
    def canDisable(_user: address) -> bool: view

interface Whitelist:
    def isUserAllowed(_user: address, _asset: address) -> bool: view

interface VaultBook:
    def isValidRegId(_regId: uint256) -> bool: view

flag ActionType:
    ASSET_ADD_NEW
    ASSET_DEPOSIT_PARAMS
    ASSET_LIQ_CONFIG
    ASSET_DEBT_TERMS
    ASSET_WHITELIST

struct NewAsset:
    asset: address
    config: AssetConfig

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

struct AssetConfigLite:
    asset: address
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
    specialStabPoolId: uint256
    customAuctionParams: AuctionParams
    whitelist: address

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

event PendingAssetDepositParamsChange:
    asset: indexed(address)
    numVaultIds: uint256
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
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

event CanDepositAssetSet:
    asset: indexed(address)
    canDeposit: bool
    caller: indexed(address)

event CanWithdrawAssetSet:
    asset: indexed(address)
    canWithdraw: bool
    caller: indexed(address)

event CanRedeemInStabPoolAssetSet:
    asset: indexed(address)
    canRedeemInStabPool: bool
    caller: indexed(address)

event CanBuyInAuctionAssetSet:
    asset: indexed(address)
    canBuyInAuction: bool
    caller: indexed(address)

event CanClaimInStabPoolAssetSet:
    asset: indexed(address)
    canClaimInStabPool: bool
    caller: indexed(address)

event CanRedeemCollateralAssetSet:
    asset: indexed(address)
    canRedeemCollateral: bool
    caller: indexed(address)

event NewAssetAdded:
    asset: indexed(address)
    numVaults: uint256
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
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

event AssetDepositParamsSet:
    asset: indexed(address)
    numVaultIds: uint256
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    perUserDepositLimit: uint256
    globalDepositLimit: uint256

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

# pending config changes
actionType: public(HashMap[uint256, ActionType]) # aid -> type
pendingNewAsset: public(HashMap[uint256, NewAsset]) # aid -> asset
pendingAssetConfig: public(HashMap[uint256, AssetConfigLite]) # aid -> config

MAX_VAULTS_PER_ASSET: constant(uint256) = 10
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100%


@deploy
def __init__(
    _ripeHq: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    addys.__init__(_ripeHq)
    timeLock.__init__(_minConfigTimeLock, _maxConfigTimeLock, 0, _maxConfigTimeLock)


# access control


@view
@internal
def _hasPermsToEnable(_caller: address, _shouldEnable: bool) -> bool:
    if gov._canGovern(_caller):
        return True
    if not _shouldEnable:
        return staticcall MissionControl(addys._getMissionControlAddr()).canDisable(_caller)
    return False


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
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    assert not staticcall MissionControl(addys._getMissionControlAddr()).isSupportedAsset(_asset) # dev: must be new asset

    debtTerms: DebtTerms = empty(DebtTerms)
    if _debtTerms.ltv != 0:
        debtTerms = _debtTerms
    customAuctionParams: AuctionParams = empty(AuctionParams)
    if _customAuctionParams.hasParams:
        customAuctionParams = _customAuctionParams

    config: AssetConfig = AssetConfig(
        vaultIds=_vaultIds,
        stakersPointsAlloc=_stakersPointsAlloc,
        voterPointsAlloc=_voterPointsAlloc,
        perUserDepositLimit=_perUserDepositLimit,
        globalDepositLimit=_globalDepositLimit,
        debtTerms=debtTerms,
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
    assert self._isValidAssetConfig(_asset, config) # dev: invalid asset

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ASSET_ADD_NEW
    self.pendingNewAsset[aid] = NewAsset(
        asset=_asset,
        config=config,
    )
    return aid


@view
@internal
def _isValidAssetConfig(_asset: address, _config: AssetConfig) -> bool:
    if _asset == empty(address):
        return False
    if _config.debtTerms.ltv != 0 and not self._isValidDebtTerms(_config.debtTerms):
        return False
    if not self._isValidAssetDepositParams(_asset, _config.vaultIds, _config.stakersPointsAlloc, _config.voterPointsAlloc, _config.perUserDepositLimit, _config.globalDepositLimit):
        return False
    if not self._isValidAssetLiqConfig(_asset, _config.shouldBurnAsPayment, _config.shouldTransferToEndaoment, _config.shouldSwapInStabPools, _config.shouldAuctionInstantly, _config.specialStabPoolId, _config.isNft, _config.whitelist, _config.debtTerms.ltv):
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
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    assert staticcall MissionControl(addys._getMissionControlAddr()).isSupportedAsset(_asset) # dev: invalid asset
    assert self._isValidAssetDepositParams(_asset, _vaultIds, _stakersPointsAlloc, _voterPointsAlloc, _perUserDepositLimit, _globalDepositLimit) # dev: invalid asset deposit params
    return self._setPendingAssetConfig(ActionType.ASSET_DEPOSIT_PARAMS, _asset, _vaultIds, _stakersPointsAlloc, _voterPointsAlloc, _perUserDepositLimit, _globalDepositLimit)


@view
@internal
def _isValidAssetDepositParams(
    _asset: address,
    _vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _stakersPointsAlloc: uint256,
    _voterPointsAlloc: uint256,
    _perUserDepositLimit: uint256,
    _globalDepositLimit: uint256,
) -> bool:
    vaultBook: address = addys._getVaultBookAddr()
    if 0 in [_perUserDepositLimit, _globalDepositLimit]:
        return False
    if max_value(uint256) in [_perUserDepositLimit, _globalDepositLimit, _stakersPointsAlloc, _voterPointsAlloc]:
        return False
    if _perUserDepositLimit > _globalDepositLimit:
        return False
    for vaultId: uint256 in _vaultIds:
        if not staticcall VaultBook(vaultBook).isValidRegId(vaultId):
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
    _customAuctionParams: AuctionParams = empty(AuctionParams),
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    customAuctionParams: AuctionParams = empty(AuctionParams)
    if _customAuctionParams.hasParams:
        assert self._areValidAuctionParams(_customAuctionParams) # dev: invalid auction params
        customAuctionParams = _customAuctionParams

    mc: address = addys._getMissionControlAddr()
    assert staticcall MissionControl(mc).isSupportedAsset(_asset) # dev: invalid asset
    assetConfig: AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)
    assert self._isValidAssetLiqConfig(_asset, _shouldBurnAsPayment, _shouldTransferToEndaoment, _shouldSwapInStabPools, _shouldAuctionInstantly, _specialStabPoolId, assetConfig.isNft, assetConfig.whitelist, assetConfig.debtTerms.ltv) # dev: invalid asset liq config
    return self._setPendingAssetConfig(ActionType.ASSET_LIQ_CONFIG, _asset, [], 0, 0, 0, 0, empty(DebtTerms), _shouldBurnAsPayment, _shouldTransferToEndaoment, _shouldSwapInStabPools, _shouldAuctionInstantly, _specialStabPoolId, customAuctionParams)


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
) -> bool:
    a: addys.Addys = addys._getAddys()

    if _shouldBurnAsPayment:

        # can only burn if green or savings green
        if _asset not in [a.greenToken, a.savingsGreen]:
            return False

    if _shouldTransferToEndaoment:

        # cannot transfer to endaoment if green or savings green
        if _asset in [a.greenToken, a.savingsGreen]:
            return False

    if _shouldSwapInStabPools:

        # cannot be nft
        if _isNft:
            return False

        # cannot have whitelist if no special stab pool
        if _whitelist != empty(address) and _specialStabPoolId == 0:
            return False

        # must have ltv
        if _debtTermsLtv == 0:
            return False

    # make sure special stab pool is valid
    if _specialStabPoolId != 0 and not staticcall VaultBook(a.vaultBook).isValidRegId(_specialStabPoolId):
        return False

    return True


@view
@internal
def _areValidAuctionParams(_params: AuctionParams) -> bool:
    if not _params.hasParams:
        return False
    if _params.startDiscount >= HUNDRED_PERCENT:
        return False
    if _params.maxDiscount >= HUNDRED_PERCENT:
        return False
    if _params.startDiscount >= _params.maxDiscount:
        return False
    if _params.delay >= _params.duration:
        return False
    if _params.duration == 0 or _params.duration == max_value(uint256):
        return False
    return True


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
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    assert staticcall MissionControl(addys._getMissionControlAddr()).isSupportedAsset(_asset) # dev: invalid asset

    debtTerms: DebtTerms = empty(DebtTerms)
    if _ltv != 0:
        debtTerms = DebtTerms(
            ltv=_ltv,
            redemptionThreshold=_redemptionThreshold,
            liqThreshold=_liqThreshold,
            liqFee=_liqFee,
            borrowRate=_borrowRate,
            daowry=_daowry,
        )
        assert self._isValidDebtTerms(debtTerms) # dev: invalid debt terms
    return self._setPendingAssetConfig(ActionType.ASSET_DEBT_TERMS, _asset, [], 0, 0, 0, 0, debtTerms)


@view
@internal
def _isValidDebtTerms(_debtTerms: DebtTerms) -> bool:
    if _debtTerms.liqThreshold > HUNDRED_PERCENT:
        return False
    if _debtTerms.redemptionThreshold > _debtTerms.liqThreshold:
        return False
    if _debtTerms.ltv > _debtTerms.redemptionThreshold:
        return False
    if _debtTerms.liqFee > HUNDRED_PERCENT or _debtTerms.borrowRate > HUNDRED_PERCENT or _debtTerms.daowry > HUNDRED_PERCENT:
        return False
    if 0 in [_debtTerms.liqFee, _debtTerms.borrowRate]:
        return False

    # make liq threshold and liq bonus work together
    liqSum: uint256 = _debtTerms.liqThreshold + (_debtTerms.liqThreshold * _debtTerms.liqFee // HUNDRED_PERCENT)
    return liqSum <= HUNDRED_PERCENT


#####################
# Asset - Whitelist #
#####################


@external
def setWhitelistForAsset(_asset: address, _whitelist: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    assert staticcall MissionControl(addys._getMissionControlAddr()).isSupportedAsset(_asset) # dev: invalid asset
    assert self._isValidWhitelist(_whitelist) # dev: invalid whitelist
    return self._setPendingAssetConfig(ActionType.ASSET_WHITELIST, _asset, [], 0, 0, 0, 0, empty(DebtTerms), False, False, False, False, 0, empty(AuctionParams), _whitelist)
    

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
    _vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET] = [],
    _stakersPointsAlloc: uint256 = 0,
    _voterPointsAlloc: uint256 = 0,
    _perUserDepositLimit: uint256 = 0,
    _globalDepositLimit: uint256 = 0,
    _debtTerms: DebtTerms = empty(DebtTerms),
    _shouldBurnAsPayment: bool = False,
    _shouldTransferToEndaoment: bool = False,
    _shouldSwapInStabPools: bool = False,
    _shouldAuctionInstantly: bool = False,
    _specialStabPoolId: uint256 = 0,
    _customAuctionParams: AuctionParams = empty(AuctionParams),
    _whitelist: address = empty(address),
) -> uint256:

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = _actionType
    self.pendingAssetConfig[aid] = AssetConfigLite(
        asset=_asset,
        vaultIds=_vaultIds,
        stakersPointsAlloc=_stakersPointsAlloc,
        voterPointsAlloc=_voterPointsAlloc,
        perUserDepositLimit=_perUserDepositLimit,
        globalDepositLimit=_globalDepositLimit,
        debtTerms=_debtTerms,
        shouldBurnAsPayment=_shouldBurnAsPayment,
        shouldTransferToEndaoment=_shouldTransferToEndaoment,
        shouldSwapInStabPools=_shouldSwapInStabPools,
        shouldAuctionInstantly=_shouldAuctionInstantly,
        specialStabPoolId=_specialStabPoolId,
        customAuctionParams=_customAuctionParams,
        whitelist=_whitelist,
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


############################
# Asset - Enable / Disable #
############################


@external
def setCanDepositAsset(_asset: address, _shouldEnable: bool) -> bool:
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    assert staticcall MissionControl(mc).isSupportedAsset(_asset) # dev: invalid asset
    assetConfig: AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)
    assert assetConfig.canDeposit != _shouldEnable # dev: already set
    assetConfig.canDeposit = _shouldEnable
    extcall MissionControl(mc).setAssetConfig(_asset, assetConfig)

    log CanDepositAssetSet(asset=_asset, canDeposit=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanWithdrawAsset(_asset: address, _shouldEnable: bool) -> bool:
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    assert staticcall MissionControl(mc).isSupportedAsset(_asset) # dev: invalid asset
    assetConfig: AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)
    assert assetConfig.canWithdraw != _shouldEnable # dev: already set
    assetConfig.canWithdraw = _shouldEnable
    extcall MissionControl(mc).setAssetConfig(_asset, assetConfig)

    log CanWithdrawAssetSet(asset=_asset, canWithdraw=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanRedeemInStabPoolAsset(_asset: address, _shouldEnable: bool) -> bool:
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    assert staticcall MissionControl(mc).isSupportedAsset(_asset) # dev: invalid asset
    assetConfig: AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)
    assert assetConfig.canRedeemInStabPool != _shouldEnable # dev: already set
    assetConfig.canRedeemInStabPool = _shouldEnable
    extcall MissionControl(mc).setAssetConfig(_asset, assetConfig)

    log CanRedeemInStabPoolAssetSet(asset=_asset, canRedeemInStabPool=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanBuyInAuctionAsset(_asset: address, _shouldEnable: bool) -> bool:
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    assert staticcall MissionControl(mc).isSupportedAsset(_asset) # dev: invalid asset
    assetConfig: AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)
    assert assetConfig.canBuyInAuction != _shouldEnable # dev: already set
    assetConfig.canBuyInAuction = _shouldEnable
    extcall MissionControl(mc).setAssetConfig(_asset, assetConfig)

    log CanBuyInAuctionAssetSet(asset=_asset, canBuyInAuction=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanClaimInStabPoolAsset(_asset: address, _shouldEnable: bool) -> bool:
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    assert staticcall MissionControl(mc).isSupportedAsset(_asset) # dev: invalid asset
    assetConfig: AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)
    assert assetConfig.canClaimInStabPool != _shouldEnable # dev: already set
    assetConfig.canClaimInStabPool = _shouldEnable
    extcall MissionControl(mc).setAssetConfig(_asset, assetConfig)

    log CanClaimInStabPoolAssetSet(asset=_asset, canClaimInStabPool=_shouldEnable, caller=msg.sender)
    return True


# redeem collateral


@external
def setCanRedeemCollateralAsset(_asset: address, _shouldEnable: bool) -> bool:
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    assert staticcall MissionControl(mc).isSupportedAsset(_asset) # dev: invalid asset
    assetConfig: AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)
    assert assetConfig.canRedeemCollateral != _shouldEnable # dev: already set
    assert self._isValidRedeemCollateralConfig(_asset, _shouldEnable, assetConfig.isNft, assetConfig.debtTerms.ltv, assetConfig.shouldTransferToEndaoment) # dev: invalid redeem collateral config
    assetConfig.canRedeemCollateral = _shouldEnable
    extcall MissionControl(mc).setAssetConfig(_asset, assetConfig)

    log CanRedeemCollateralAssetSet(asset=_asset, canRedeemCollateral=_shouldEnable, caller=msg.sender)
    return True


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
    mc: address = addys._getMissionControlAddr()

    if actionType == ActionType.ASSET_ADD_NEW:
        p: NewAsset = self.pendingNewAsset[_aid]
        assert self._isValidAssetConfig(p.asset, p.config) # dev: invalid asset config
        extcall MissionControl(mc).setAssetConfig(p.asset, p.config)
        log NewAssetAdded(
            asset=p.asset,
            numVaults=len(p.config.vaultIds),
            stakersPointsAlloc=p.config.stakersPointsAlloc,
            voterPointsAlloc=p.config.voterPointsAlloc,
            perUserDepositLimit=p.config.perUserDepositLimit,
            globalDepositLimit=p.config.globalDepositLimit,
            debtTermsLtv=p.config.debtTerms.ltv,
            debtTermsRedemptionThreshold=p.config.debtTerms.redemptionThreshold,
            debtTermsLiqThreshold=p.config.debtTerms.liqThreshold,
            debtTermsLiqFee=p.config.debtTerms.liqFee,
            debtTermsBorrowRate=p.config.debtTerms.borrowRate,
            debtTermsDaowry=p.config.debtTerms.daowry,
            shouldBurnAsPayment=p.config.shouldBurnAsPayment,
            shouldTransferToEndaoment=p.config.shouldTransferToEndaoment,
            shouldSwapInStabPools=p.config.shouldSwapInStabPools,
            shouldAuctionInstantly=p.config.shouldAuctionInstantly,
            canDeposit=p.config.canDeposit,
            canWithdraw=p.config.canWithdraw,
            canRedeemCollateral=p.config.canRedeemCollateral,
            canRedeemInStabPool=p.config.canRedeemInStabPool,
            canBuyInAuction=p.config.canBuyInAuction,
            canClaimInStabPool=p.config.canClaimInStabPool,
            specialStabPoolId=p.config.specialStabPoolId,
            auctionStartDiscount=p.config.customAuctionParams.startDiscount,
            auctionMaxDiscount=p.config.customAuctionParams.maxDiscount,
            auctionDelay=p.config.customAuctionParams.delay,
            auctionDuration=p.config.customAuctionParams.duration,
            whitelist=p.config.whitelist,
            isNft=p.config.isNft,
        )

    elif actionType == ActionType.ASSET_DEPOSIT_PARAMS:
        p: AssetConfigLite = self.pendingAssetConfig[_aid]
        config: AssetConfig = staticcall MissionControl(mc).assetConfig(p.asset)
        config.vaultIds = p.vaultIds
        config.stakersPointsAlloc = p.stakersPointsAlloc
        config.voterPointsAlloc = p.voterPointsAlloc
        config.perUserDepositLimit = p.perUserDepositLimit
        config.globalDepositLimit = p.globalDepositLimit
        assert self._isValidAssetConfig(p.asset, config) # dev: invalid asset config
        extcall MissionControl(mc).setAssetConfig(p.asset, config)
        log AssetDepositParamsSet(asset=p.asset, numVaultIds=len(p.vaultIds), stakersPointsAlloc=p.stakersPointsAlloc, voterPointsAlloc=p.voterPointsAlloc, perUserDepositLimit=p.perUserDepositLimit, globalDepositLimit=p.globalDepositLimit)

    elif actionType == ActionType.ASSET_LIQ_CONFIG:
        p: AssetConfigLite = self.pendingAssetConfig[_aid]
        config: AssetConfig = staticcall MissionControl(mc).assetConfig(p.asset)
        config.shouldBurnAsPayment = p.shouldBurnAsPayment
        config.shouldTransferToEndaoment = p.shouldTransferToEndaoment
        config.shouldSwapInStabPools = p.shouldSwapInStabPools
        config.shouldAuctionInstantly = p.shouldAuctionInstantly
        config.specialStabPoolId = p.specialStabPoolId
        config.customAuctionParams = p.customAuctionParams
        assert self._isValidAssetConfig(p.asset, config) # dev: invalid asset config
        extcall MissionControl(mc).setAssetConfig(p.asset, config)
        log AssetLiqConfigSet(asset=p.asset, shouldBurnAsPayment=p.shouldBurnAsPayment, shouldTransferToEndaoment=p.shouldTransferToEndaoment, shouldSwapInStabPools=p.shouldSwapInStabPools, shouldAuctionInstantly=p.shouldAuctionInstantly, specialStabPoolId=p.specialStabPoolId, auctionStartDiscount=p.customAuctionParams.startDiscount, auctionMaxDiscount=p.customAuctionParams.maxDiscount, auctionDelay=p.customAuctionParams.delay, auctionDuration=p.customAuctionParams.duration)

    elif actionType == ActionType.ASSET_DEBT_TERMS:
        p: AssetConfigLite = self.pendingAssetConfig[_aid]
        config: AssetConfig = staticcall MissionControl(mc).assetConfig(p.asset)
        config.debtTerms = p.debtTerms
        assert self._isValidAssetConfig(p.asset, config) # dev: invalid asset config
        extcall MissionControl(mc).setAssetConfig(p.asset, config)
        log AssetDebtTermsSet(asset=p.asset, ltv=p.debtTerms.ltv, redemptionThreshold=p.debtTerms.redemptionThreshold, liqThreshold=p.debtTerms.liqThreshold, liqFee=p.debtTerms.liqFee, borrowRate=p.debtTerms.borrowRate, daowry=p.debtTerms.daowry)

    elif actionType == ActionType.ASSET_WHITELIST:
        p: AssetConfigLite = self.pendingAssetConfig[_aid]
        config: AssetConfig = staticcall MissionControl(mc).assetConfig(p.asset)
        config.whitelist = p.whitelist
        assert self._isValidAssetConfig(p.asset, config) # dev: invalid asset config
        extcall MissionControl(mc).setAssetConfig(p.asset, config)
        log WhitelistAssetSet(asset=p.asset, whitelist=p.whitelist)

    self.actionType[_aid] = empty(ActionType)
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
