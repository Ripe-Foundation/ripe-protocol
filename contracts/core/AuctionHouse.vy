# @version 0.4.1

initializes: addys
exports: addys.__interface__
import contracts.modules.Addys as addys

from interfaces import Vault
from ethereum.ercs import IERC20

interface CreditEngine:
    def updateDebtDuringLiquidation(_liqUser: address, _userDebt: UserDebt, _amount: uint256, _newInterest: uint256, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def getLatestUserDebtAndTerms(_user: address, _shouldRaise: bool, _a: addys.Addys = empty(addys.Addys)) -> (UserDebt, UserBorrowTerms, uint256): view

interface PriceDesk:
    def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256: view
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface ControlRoom:
    def getAssetLiqConfig(_vaultId: uint256, _asset: address) -> AssetLiqConfig: view
    def getGenLiqConfig() -> GenLiqConfig: view

interface Ledger:
    def userVaults(_user: address, _index: uint256) -> uint256: view
    def numUserVaults(_user: address) -> uint256: view

interface StabilityPool:
    def swapForLiquidatedCollateral(_stabAsset: address, _stabAmountToRemove: uint256, _liqAsset: address, _liqAmountSent: uint256, _recipient: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface VaultBook:
    def getVault(_vaultId: uint256) -> address: view

struct DebtTerms:
    ltv: uint256
    redemptionThreshold: uint256
    liqThreshold: uint256
    liqFee: uint256
    borrowRate: uint256
    daowry: uint256

struct UserBorrowTerms:
    collateralVal: uint256
    totalMaxDebt: uint256
    debtTerms: DebtTerms

struct UserDebt:
    amount: uint256
    principal: uint256
    debtTerms: DebtTerms
    lastTimestamp: uint256
    inLiquidation: bool

struct VaultData:
    vaultId: uint256
    vaultAddr: address
    asset: address

struct GenLiqConfig:
    keeperFeeRatio: uint256
    minKeeperFee: uint256
    ltvPaybackBuffer: uint256
    genAuctionConfig: AuctionConfig
    genStabPools: DynArray[VaultData, MAX_GEN_STAB_POOLS]

struct AssetLiqConfig:
    hasConfig: bool
    hasLtv: bool
    hasWhitelist: bool
    isNft: bool
    specialStabPool: VaultData
    auctionConfig: AuctionConfig

struct AuctionConfig:
    hasConfig: bool
    startDiscount: uint256
    minEntitled: uint256
    maxDiscount: uint256
    minBidIncrement: uint256
    maxBidIncrement: uint256
    delay: uint256
    duration: uint256
    extension: uint256

event LiquidateUser:
    user: address
    totalLiqFees: uint256
    targetRepayAmount: uint256
    repayAmount: uint256
    didRestoreDebtHealth: bool
    collateralValueOut: uint256
    auctionValueStarted: uint256
    keeperFee: uint256

event CollateralSwappedWithStabPool:
    liqUser: address
    liqVaultId: uint256
    liqAsset: address
    collateralAmountOut: uint256
    collateralValueOut: uint256
    stabVaultId: uint256
    stabAsset: address
    stabAmountSwapped: uint256
    stabValueSwapped: uint256

# cache
vaultAddrs: transient(HashMap[uint256, address]) # vaultId -> vaultAddr
assetLiqConfig: transient(HashMap[uint256, HashMap[address, AssetLiqConfig]]) # vaultId -> asset -> config
numUserAssetsForAuction: transient(HashMap[address, uint256]) # user -> num assets
userAssetForAuction: transient(HashMap[address, HashMap[uint256, VaultData]]) # user -> index -> asset

# config
isActivated: public(bool)

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_GEN_STAB_POOLS: constant(uint256) = 10


@deploy
def __init__(_hq: address):
    addys.__init__(_hq)
    self.isActivated = True


###############
# Liquidation #
###############


@internal
def _liquidateUser(
    _liqUser: address,
    _config: GenLiqConfig,
    _a: addys.Addys,
) -> uint256:

    # get latest user debt and terms
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    newInterest: uint256 = 0
    userDebt, bt, newInterest = staticcall CreditEngine(_a.creditEngine).getLatestUserDebtAndTerms(_liqUser, True, _a)

    # no debt
    if userDebt.amount == 0:
        return 0

    # already in liquidation
    if userDebt.inLiquidation:
        return 0

    # not reached liquidation threshold
    collateralLiqThreshold: uint256 = userDebt.amount * HUNDRED_PERCENT // bt.debtTerms.liqThreshold
    if bt.collateralVal > collateralLiqThreshold:
        return 0

    # TO THINK ABOUT...
    # TODO: claim things
    # TODO: pay with stables
    # TODO: pay with stability pool

    # set liquidation mode
    userDebt.inLiquidation = True

    # liquidation fees
    totalLiqFees: uint256 = userDebt.amount * bt.debtTerms.liqFee // HUNDRED_PERCENT
    liqFeeRatio: uint256 = bt.debtTerms.liqFee

    # keeper fee (for liquidator)
    keeperFee: uint256 = max(_config.minKeeperFee, userDebt.amount * _config.keeperFeeRatio // HUNDRED_PERCENT)
    if keeperFee != 0:
        totalLiqFees += keeperFee
        liqFeeRatio = totalLiqFees * HUNDRED_PERCENT // userDebt.amount

    # update user debt
    userDebt.amount += totalLiqFees

    # how much to achieve safe LTV -- won't be exact because depends on which collateral is liquidated (LTV changes)
    targetLtv: uint256 = bt.debtTerms.ltv * (HUNDRED_PERCENT - _config.ltvPaybackBuffer) // HUNDRED_PERCENT
    targetRepayAmount: uint256 = self._calcAmountToPay(userDebt.amount, bt.collateralVal, targetLtv)

    # swap collateral to pay debt (liquidation fees basically mean selling at a discount)
    repayValueIn: uint256 = 0
    collateralValueOut: uint256 = 0
    repayValueIn, collateralValueOut = self._handleLiqUserCollateral(_liqUser, targetRepayAmount, liqFeeRatio, _config.genStabPools, _a)

    # repayValueIn may be zero, but need to update debt
    didRestoreDebtHealth: bool = extcall CreditEngine(_a.creditEngine).updateDebtDuringLiquidation(_liqUser, userDebt, repayValueIn, newInterest, _a)

    # start auctions (if necessary)
    auctionValueStarted: uint256 = 0
    if not didRestoreDebtHealth:
        auctionValueStarted = self._initiateAuctions(_liqUser, _config.genAuctionConfig, _a)

    log LiquidateUser(user=_liqUser, totalLiqFees=totalLiqFees, targetRepayAmount=targetRepayAmount, repayAmount=repayValueIn, didRestoreDebtHealth=didRestoreDebtHealth, collateralValueOut=collateralValueOut, auctionValueStarted=auctionValueStarted, keeperFee=keeperFee)
    return keeperFee


# handle user's collateral


@internal
def _handleLiqUserCollateral(
    _liqUser: address,
    _targetRepayAmount: uint256,
    _liqFeeRatio: uint256,
    _genStabPools: DynArray[VaultData, MAX_GEN_STAB_POOLS],
    _a: addys.Addys,
) -> (uint256, uint256):
    remainingToRepay: uint256 = _targetRepayAmount
    collateralValueOut: uint256 = 0

    # iterate thru each user vault
    numUserVaults: uint256 = staticcall Ledger(_a.ledger).numUserVaults(_liqUser)
    for i: uint256 in range(1, numUserVaults, bound=max_value(uint256)):
        if remainingToRepay == 0:
            break

        vaultId: uint256 = staticcall Ledger(_a.ledger).userVaults(_liqUser, i)

        # get vault address
        vaultAddr: address = empty(address)
        isVaultAddrCached: bool = False
        vaultAddr, isVaultAddrCached = self._getVaultAddr(vaultId, _a.vaultBook)

        # no vault, skip
        if vaultAddr == empty(address):
            continue

        # cache vault addr
        if not isVaultAddrCached:
            self.vaultAddrs[vaultId] = vaultAddr

        # iterate thru each user asset
        numUserAssets: uint256 = staticcall Vault(vaultAddr).numUserAssets(_liqUser)
        for y: uint256 in range(1, numUserAssets, bound=max_value(uint256)):
            if remainingToRepay == 0:
                break

            asset: address = empty(address)
            amount: uint256 = 0
            asset, amount = staticcall Vault(vaultAddr).getUserAssetAndAmountAtIndex(_liqUser, y)
            if asset == empty(address) or amount == 0:
                continue

            # get asset liq config
            config: AssetLiqConfig = empty(AssetLiqConfig)
            isConfigCached: bool = False
            config, isConfigCached = self._getAssetLiqConfig(vaultId, asset, _a.controlRoom)

            # cache asset liq config
            if not isConfigCached:
                self.assetLiqConfig[vaultId][asset] = config

            # no ltv, skip
            if not config.hasLtv:
                continue

            # cannot liquidiate via stability pools if NFT or whitelisted (with no special stab pool)
            if config.isNft or (config.hasWhitelist and config.specialStabPool.vaultAddr == empty(address)):
                self._saveUserAssetForAuction(_liqUser, vaultId, vaultAddr, asset)
                continue

            # stability pools to use
            stabPoolsToUse: DynArray[VaultData, MAX_GEN_STAB_POOLS] = _genStabPools
            if config.specialStabPool.vaultAddr != empty(address):
                stabPoolsToUse = [config.specialStabPool]

            # iterate thru each stab pool
            isPositionDepleted: bool = False
            for sp: VaultData in stabPoolsToUse:
                if remainingToRepay == 0:
                    break

                # no balance in stability pool, skip
                maxAmountInStabPool: uint256 = staticcall IERC20(sp.asset).balanceOf(sp.vaultAddr)
                if maxAmountInStabPool == 0:
                    continue

                # swap with stability pool
                stabValueIn: uint256 = 0
                collValueOut: uint256 = 0
                stabValueIn, collValueOut, isPositionDepleted = self._swapCollateralWithStabPool(sp, maxAmountInStabPool, _liqUser, vaultId, vaultAddr, asset, remainingToRepay, _liqFeeRatio, _a)
                remainingToRepay -= stabValueIn
                collateralValueOut += collValueOut

                # if position depleted, nothing else to do with this asset
                if isPositionDepleted:
                    break

            # add to auction list if not depleted
            if not isPositionDepleted:
                self._saveUserAssetForAuction(_liqUser, vaultId, vaultAddr, asset)


    # TODO:
    # clean up vault asset storage (per user)
    # clean up ledger vault participation

    return _targetRepayAmount - remainingToRepay, collateralValueOut


# swap with stability pool


@internal
def _swapCollateralWithStabPool(
    _stabPool: VaultData,
    _maxAmountInStabPool: uint256,
    _liqUser: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _remainingToRepay: uint256,
    _liqFeeRatio: uint256,
    _a: addys.Addys,
) -> (uint256, uint256, bool):
    isGreenToken: bool = _stabPool.asset == _a.greenToken

    # max usd value in stability pool
    maxValueInStabPool: uint256 = _maxAmountInStabPool # green treated as $1
    recipient: address = empty(address)
    if not isGreenToken:
        maxValueInStabPool = staticcall PriceDesk(_a.priceDesk).getUsdValue(_stabPool.asset, _maxAmountInStabPool, True)
        recipient = _a.governance

    # max values from liq user
    maxLiqUserSwapValue: uint256 = min(_remainingToRepay, maxValueInStabPool * HUNDRED_PERCENT // (HUNDRED_PERCENT - _liqFeeRatio))
    maxLiqUserSwapAmount: uint256 = staticcall PriceDesk(_a.priceDesk).getAssetAmount(_asset, maxLiqUserSwapValue, True)

    # transfer collateral to stability pool
    amountSentToStabPool: uint256 = 0
    isPositionDepleted: bool = False
    isUserStillInVault: bool = False
    amountSentToStabPool, isPositionDepleted, isUserStillInVault = extcall Vault(_vaultAddr).withdrawTokensFromVault(_liqUser, _asset, maxLiqUserSwapAmount, _stabPool.vaultAddr)

    # finalize values for stability pool !!
    collateralValueOut: uint256 = maxLiqUserSwapValue * amountSentToStabPool // maxLiqUserSwapAmount
    stabValueToRemove: uint256 = collateralValueOut * (HUNDRED_PERCENT - _liqFeeRatio) // HUNDRED_PERCENT
    stabAmountToRemove: uint256 = _maxAmountInStabPool * stabValueToRemove // maxValueInStabPool

    # remove assets from stability pool
    stabAmountSwapped: uint256 = extcall StabilityPool(_stabPool.vaultAddr).swapForLiquidatedCollateral(_stabPool.asset, stabAmountToRemove, _asset, amountSentToStabPool, recipient, _a)
    stabValueSwapped: uint256 = maxValueInStabPool * stabAmountSwapped // _maxAmountInStabPool

    # TODO: add to clean up list if depleted

    log CollateralSwappedWithStabPool(
        liqUser=_liqUser,
        liqVaultId=_vaultId,
        liqAsset=_asset,
        collateralAmountOut=amountSentToStabPool,
        collateralValueOut=collateralValueOut,
        stabVaultId=_stabPool.vaultId,
        stabAsset=_stabPool.asset,
        stabAmountSwapped=stabAmountSwapped,
        stabValueSwapped=stabValueSwapped,
    )
    return min(stabValueSwapped, _remainingToRepay), collateralValueOut, isPositionDepleted


# initiate auctions


@internal
def _initiateAuctions(_liqUser: address, _genAuctionConfig: AuctionConfig, _a: addys.Addys) -> uint256:
    totalAuctionValue: uint256 = 0

    numAssets: uint256 = self.numUserAssetsForAuction[_liqUser]
    for i: uint256 in range(numAssets, bound=max_value(uint256)):

        data: VaultData = self.userAssetForAuction[_liqUser][i]
        config: AssetLiqConfig = self.assetLiqConfig[data.vaultId][data.asset]

        # TODO: implement, start auction for each asset

    return totalAuctionValue


#########
# Cache #
#########


@view
@internal
def _getAssetLiqConfig(_vaultId: uint256, _asset: address, _controlRoom: address) -> (AssetLiqConfig, bool):
    config: AssetLiqConfig = self.assetLiqConfig[_vaultId][_asset]
    if config.hasConfig:
        return config, True
    return staticcall ControlRoom(_controlRoom).getAssetLiqConfig(_vaultId, _asset), False


@view
@internal
def _getVaultAddr(_vaultId: uint256, _vaultBook: address) -> (address, bool):
    vaultAddr: address = self.vaultAddrs[_vaultId]
    if vaultAddr != empty(address):
        return vaultAddr, True
    return staticcall VaultBook(_vaultBook).getVault(_vaultId), False


@internal
def _saveUserAssetForAuction(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address):
    nextId: uint256 = self.numUserAssetsForAuction[_user]
    self.userAssetForAuction[_user][nextId] = VaultData(vaultId=_vaultId, vaultAddr=_vaultAddr, asset=_asset)
    self.numUserAssetsForAuction[_user] = nextId + 1


#############
# Utilities #
#############


@view
@external
def calcAmountToPay(_debtAmount: uint256, _collateralValue: uint256, _targetLtv: uint256) -> uint256:
    return self._calcAmountToPay(_debtAmount, _collateralValue, _targetLtv)


@view
@internal
def _calcAmountToPay(_debtAmount: uint256, _collateralValue: uint256, _targetLtv: uint256) -> uint256:
    # goal here is to only reduce the debt necessary to get LTV back to safe position
    # it will never be perfectly precise because depending on what assets are taken, the LTV might slightly change
    collValueAdjusted: uint256 =_collateralValue * _targetLtv // HUNDRED_PERCENT

    toPay: uint256 = (_debtAmount - collValueAdjusted) * HUNDRED_PERCENT // (HUNDRED_PERCENT - _targetLtv)
    return min(toPay, _debtAmount)