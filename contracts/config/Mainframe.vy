# @version 0.4.1
# pragma optimize codesize

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

interface MissionControl:
    def setAssetConfig(_asset: address, _assetConfig: AssetConfig): nonpayable
    def assetConfig(_asset: address) -> AssetConfig: view
    def canDisable(_user: address) -> bool: view

interface VaultBook:
    def isValidRegId(_regId: uint256) -> bool: view

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

event CanDepositAssetSet:
    asset: indexed(address)
    canDeposit: bool
    caller: indexed(address)

event CanWithdrawAssetSet:
    asset: indexed(address)
    canWithdraw: bool
    caller: indexed(address)

event CanRedeemCollateralAssetSet:
    asset: indexed(address)
    canRedeemCollateral: bool
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

MAX_VAULTS_PER_ASSET: constant(uint256) = 10
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100%


@deploy
def __init__(_ripeHq: address):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting


# access control


@view
@internal
def _hasPermsToEnable(_caller: address, _shouldEnable: bool) -> bool:
    if gov._canGovern(_caller):
        return True
    if not _shouldEnable:
        return staticcall MissionControl(addys._getMissionControlAddr()).canDisable(_caller)
    return False


################
# Asset Config #
################


@external
def setAssetConfig(
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
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock, validation

    assert _asset != empty(address) # dev: invalid asset
    assert self._isValidAssetLiqConfig(_asset, _shouldBurnAsPayment, _shouldTransferToEndaoment, _shouldSwapInStabPools, _shouldAuctionInstantly, _specialStabPoolId, _customAuctionParams, _isNft, _whitelist, _debtTerms.ltv) # dev: invalid asset liq config
    assert self._isValidRedeemCollateralConfig(_asset, _canRedeemCollateral, _isNft, _debtTerms.ltv, _shouldTransferToEndaoment) # dev: invalid redeem collateral config

    mc: address = addys._getMissionControlAddr()
    assetConfig: AssetConfig = AssetConfig(
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
    extcall MissionControl(mc).setAssetConfig(_asset, assetConfig)
    return True


# liquidation config


@external
def setAssetLiqConfig(
    _asset: address,
    _shouldBurnAsPayment: bool,
    _shouldTransferToEndaoment: bool,
    _shouldSwapInStabPools: bool,
    _shouldAuctionInstantly: bool,
    _specialStabPoolId: uint256 = 0,
    _customAuctionParams: AuctionParams = empty(AuctionParams),
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused

    # TODO: add time lock

    mc: address = addys._getMissionControlAddr()
    assetConfig: AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)
    assert self._isValidAssetLiqConfig(_asset, _shouldBurnAsPayment, _shouldTransferToEndaoment, _shouldSwapInStabPools, _shouldAuctionInstantly, _specialStabPoolId, _customAuctionParams, assetConfig.isNft, assetConfig.whitelist, assetConfig.debtTerms.ltv) # dev: invalid asset liq config
    assetConfig.shouldBurnAsPayment = _shouldBurnAsPayment
    assetConfig.shouldTransferToEndaoment = _shouldTransferToEndaoment
    assetConfig.shouldSwapInStabPools = _shouldSwapInStabPools
    assetConfig.shouldAuctionInstantly = _shouldAuctionInstantly
    assetConfig.specialStabPoolId = _specialStabPoolId
    assetConfig.customAuctionParams = _customAuctionParams
    extcall MissionControl(mc).setAssetConfig(_asset, assetConfig)

    log AssetLiqConfigSet(
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
    )
    return True


@view
@internal
def _isValidAssetLiqConfig(
    _asset: address,
    _shouldBurnAsPayment: bool,
    _shouldTransferToEndaoment: bool,
    _shouldSwapInStabPools: bool,
    _shouldAuctionInstantly: bool,
    _specialStabPoolId: uint256,
    _customAuctionParams: AuctionParams,
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

    # validate custom auction params
    if _customAuctionParams.hasParams and not self._areValidAuctionParams(_customAuctionParams):
        return False

    # make sure special stab pool is valid
    if _specialStabPoolId != 0 and not staticcall VaultBook(a.vaultBook).isValidRegId(_specialStabPoolId):
        return False

    return True


# TODO:
# deposit params (vault ids, points, limits)
# debt terms
# random: whitelist, isNft, etc.


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


# enable / disable


@external
def setCanDepositAsset(_asset: address, _shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    assetConfig: AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)
    assert assetConfig.canDeposit != _shouldEnable # dev: already set
    assetConfig.canDeposit = _shouldEnable
    extcall MissionControl(mc).setAssetConfig(_asset, assetConfig)

    log CanDepositAssetSet(asset=_asset, canDeposit=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanWithdrawAsset(_asset: address, _shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    assetConfig: AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)
    assert assetConfig.canWithdraw != _shouldEnable # dev: already set
    assetConfig.canWithdraw = _shouldEnable
    extcall MissionControl(mc).setAssetConfig(_asset, assetConfig)

    log CanWithdrawAssetSet(asset=_asset, canWithdraw=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanRedeemInStabPoolAsset(_asset: address, _shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    assetConfig: AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)
    assert assetConfig.canRedeemInStabPool != _shouldEnable # dev: already set
    assetConfig.canRedeemInStabPool = _shouldEnable
    extcall MissionControl(mc).setAssetConfig(_asset, assetConfig)

    log CanRedeemInStabPoolAssetSet(asset=_asset, canRedeemInStabPool=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanBuyInAuctionAsset(_asset: address, _shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    assetConfig: AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)
    assert assetConfig.canBuyInAuction != _shouldEnable # dev: already set
    assetConfig.canBuyInAuction = _shouldEnable
    extcall MissionControl(mc).setAssetConfig(_asset, assetConfig)

    log CanBuyInAuctionAssetSet(asset=_asset, canBuyInAuction=_shouldEnable, caller=msg.sender)
    return True


@external
def setCanClaimInStabPoolAsset(_asset: address, _shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
    assetConfig: AssetConfig = staticcall MissionControl(mc).assetConfig(_asset)
    assert assetConfig.canClaimInStabPool != _shouldEnable # dev: already set
    assetConfig.canClaimInStabPool = _shouldEnable
    extcall MissionControl(mc).setAssetConfig(_asset, assetConfig)

    log CanClaimInStabPoolAssetSet(asset=_asset, canClaimInStabPool=_shouldEnable, caller=msg.sender)
    return True


# redeem collateral


@external
def setCanRedeemCollateralAsset(_asset: address, _shouldEnable: bool) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert self._hasPermsToEnable(msg.sender, _shouldEnable) # dev: no perms

    mc: address = addys._getMissionControlAddr()
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