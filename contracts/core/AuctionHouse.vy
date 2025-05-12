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
    def canBuyAuction(_vaultId: uint256, _asset: address, _buyer: address) -> bool: view
    def getGenLiqConfig() -> GenLiqConfig: view

interface Ledger:
    def getFungibleAuction(_liqUser: address, _vaultId: uint256, _asset: address) -> FungibleAuction: view
    def createNewFungibleAuction(_auc: FungibleAuction) -> uint256: nonpayable
    def userVaults(_user: address, _index: uint256) -> uint256: view
    def numUserVaults(_user: address) -> uint256: view

interface StabilityPool:
    def swapForLiquidatedCollateral(_stabAsset: address, _stabAmountToRemove: uint256, _liqAsset: address, _liqAmountSent: uint256, _recipient: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable

interface VaultBook:
    def getVaultAddr(_vaultId: uint256) -> address: view

interface GreenToken:
    def burn(_amount: uint256): nonpayable

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
    genAuctionParams: AuctionParams
    genStabPools: DynArray[VaultData, MAX_GEN_STAB_POOLS]

struct AssetLiqConfig:
    hasConfig: bool
    hasLtv: bool
    hasWhitelist: bool
    isNft: bool
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

struct FungibleAuction:
    liqUser: address
    vaultId: uint256
    asset: address 
    startDiscount: uint256
    maxDiscount: uint256
    startBlock: uint256
    endBlock: uint256
    isActive: bool

event LiquidateUser:
    user: indexed(address)
    totalLiqFees: uint256
    targetRepayAmount: uint256
    repayAmount: uint256
    didRestoreDebtHealth: bool
    collateralValueOut: uint256
    numAuctionsStarted: uint256
    keeperFee: uint256

event CollateralSwappedWithStabPool:
    liqUser: indexed(address)
    liqVaultId: uint256
    liqAsset: indexed(address)
    collateralAmountOut: uint256
    collateralValueOut: uint256
    stabVaultId: uint256
    stabAsset: indexed(address)
    stabAmountSwapped: uint256
    stabValueSwapped: uint256

event NewFungibleAuctionCreated:
    liqUser: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    startDiscount: uint256
    maxDiscount: uint256
    startBlock: uint256
    endBlock: uint256
    auctionId: uint256

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
    numAuctionsStarted: uint256 = 0
    if not didRestoreDebtHealth:
        numAuctionsStarted = self._initiateAuctions(_liqUser, _config.genAuctionParams, _a)

    log LiquidateUser(user=_liqUser, totalLiqFees=totalLiqFees, targetRepayAmount=targetRepayAmount, repayAmount=repayValueIn, didRestoreDebtHealth=didRestoreDebtHealth, collateralValueOut=collateralValueOut, numAuctionsStarted=numAuctionsStarted, keeperFee=keeperFee)
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
    proceedsAddr: address = empty(address)
    if not isGreenToken:
        maxValueInStabPool = staticcall PriceDesk(_a.priceDesk).getUsdValue(_stabPool.asset, _maxAmountInStabPool, True)
        proceedsAddr = _a.governance

    # handle collateral buy
    amountSentToBuyer: uint256 = 0
    collateralValueOut: uint256 = 0
    amountNeededFromBuyer: uint256 = 0
    isPositionDepleted: bool = False
    amountSentToBuyer, collateralValueOut, amountNeededFromBuyer, isPositionDepleted = self._handleCollateralDuringPurchase(_liqUser, _vaultAddr, _asset, maxValueInStabPool, _maxAmountInStabPool, _stabPool.vaultAddr, _remainingToRepay, _liqFeeRatio, _a.priceDesk)

    # remove assets from stability pool
    stabAmountSwapped: uint256 = extcall StabilityPool(_stabPool.vaultAddr).swapForLiquidatedCollateral(_stabPool.asset, amountNeededFromBuyer, _asset, amountSentToBuyer, proceedsAddr, _a)
    stabValueSwapped: uint256 = maxValueInStabPool * stabAmountSwapped // _maxAmountInStabPool

    # TODO: add to clean up list if depleted

    log CollateralSwappedWithStabPool(
        liqUser=_liqUser,
        liqVaultId=_vaultId,
        liqAsset=_asset,
        collateralAmountOut=amountSentToBuyer,
        collateralValueOut=collateralValueOut,
        stabVaultId=_stabPool.vaultId,
        stabAsset=_stabPool.asset,
        stabAmountSwapped=stabAmountSwapped,
        stabValueSwapped=stabValueSwapped,
    )
    return min(stabValueSwapped, _remainingToRepay), collateralValueOut, isPositionDepleted


@internal
def _handleCollateralDuringPurchase(
    _liqUser: address,
    _liqVaultAddr: address,
    _liqAsset: address,
    _maxBuyerValue: uint256,
    _maxBuyerAmount: uint256,
    _proceedsAddr: address,
    _extraCeilingOnValue: uint256,
    _discount: uint256,
    _priceDesk: address,
) -> (uint256, uint256, uint256, bool):

    # max values from liq user
    maxLiqCollateralValue: uint256 = min(_extraCeilingOnValue, _maxBuyerValue * HUNDRED_PERCENT // (HUNDRED_PERCENT - _discount))
    maxLiqCollateralAmount: uint256 = staticcall PriceDesk(_priceDesk).getAssetAmount(_liqAsset, maxLiqCollateralValue, True)

    # transfer collateral to buyer
    amountSentToBuyer: uint256 = 0
    isPositionDepleted: bool = False
    isUserStillInVault: bool = False
    amountSentToBuyer, isPositionDepleted, isUserStillInVault = extcall Vault(_liqVaultAddr).withdrawTokensFromVault(_liqUser, _liqAsset, maxLiqCollateralAmount, _proceedsAddr)

    # finalize values for buyer
    collateralValueOut: uint256 = maxLiqCollateralValue * amountSentToBuyer // maxLiqCollateralAmount
    valueNeededFromBuyer: uint256 = collateralValueOut * (HUNDRED_PERCENT - _discount) // HUNDRED_PERCENT
    amountNeededFromBuyer: uint256 = _maxBuyerAmount * valueNeededFromBuyer // _maxBuyerValue

    return amountSentToBuyer, collateralValueOut, amountNeededFromBuyer, isPositionDepleted


##################
# Start Auctions #
##################


# start during liquidation


@internal
def _initiateAuctions(_liqUser: address, _genAuctionParams: AuctionParams, _a: addys.Addys) -> uint256:
    numAuctionsStarted: uint256 = 0
    numAssets: uint256 = self.numUserAssetsForAuction[_liqUser]
    if numAssets == 0:
        return 0

    for i: uint256 in range(numAssets, bound=max_value(uint256)):
        d: VaultData = self.userAssetForAuction[_liqUser][i]

        # get asset liq config
        config: AssetLiqConfig = empty(AssetLiqConfig)
        isConfigCached: bool = False
        config, isConfigCached = self._getAssetLiqConfig(d.vaultId, d.asset, _a.controlRoom)

        # cache asset liq config
        if not isConfigCached:
            self.assetLiqConfig[d.vaultId][d.asset] = config

        # some assets can't be auctioned instantly, not handling NFTs right now
        if not config.canAuctionInstantly or config.isNft:
            continue

        # finalize auction params
        params: AuctionParams = _genAuctionParams
        if config.customAuctionParams.hasParams:
            params = config.customAuctionParams

        # create auction
        didCreateAuction: bool = self._createNewFungibleAuction(_liqUser, d.vaultId, d.asset, params, _a.ledger)
        if didCreateAuction:
            numAuctionsStarted += 1

    return numAuctionsStarted


# create auction


@internal
def _createNewFungibleAuction(
    _liqUser: address,
    _vaultId: uint256,
    _asset: address,
    _params: AuctionParams,
    _ledger: address,
) -> bool:
    startBlock: uint256 = block.number + _params.delay
    endBlock: uint256 = startBlock + _params.duration
    newAuction: FungibleAuction = FungibleAuction(
        liqUser=_liqUser,
        vaultId=_vaultId,
        asset=_asset,
        startDiscount=_params.startDiscount,
        maxDiscount=_params.maxDiscount,
        startBlock=startBlock,
        endBlock=endBlock,
        isActive=True,
    )
    aid: uint256 = extcall Ledger(_ledger).createNewFungibleAuction(newAuction)
    if aid == 0:
        return False

    log NewFungibleAuctionCreated(
        liqUser=_liqUser,
        vaultId=_vaultId,
        asset=_asset,
        startDiscount=_params.startDiscount,
        maxDiscount=_params.maxDiscount,
        startBlock=startBlock,
        endBlock=endBlock,
        auctionId=aid,
    )
    return True


################
# Buy Auctions #
################


@internal
def _buyFungibleAuction(
    _liqUser: address,
    _vaultId: uint256,
    _asset: address,
    _buyer: address,
    _payAmount: uint256,
    _a: addys.Addys,
) -> uint256:
    auc: FungibleAuction = staticcall Ledger(_a.ledger).getFungibleAuction(_liqUser, _vaultId, _asset)
    payAmount: uint256 = self._validateOnBuyFungibleAuction(auc, _buyer, _payAmount, _a.greenToken, _a.controlRoom)
    payUsdValue: uint256 = payAmount # green treated as $1

    # calculate discount
    auctionProgress: uint256 = (block.number - auc.startBlock) * HUNDRED_PERCENT // (auc.endBlock - auc.startBlock)
    discount: uint256 = self._calculateDiscount(auctionProgress, auc.startDiscount, auc.maxDiscount)
    vaultAddr: address = staticcall VaultBook(_a.vaultBook).getVaultAddr(_vaultId)

    # handle collateral buy
    amountSentToBuyer: uint256 = 0
    collateralValueOut: uint256 = 0
    amountNeededFromBuyer: uint256 = 0
    isPositionDepleted: bool = False
    amountSentToBuyer, collateralValueOut, amountNeededFromBuyer, isPositionDepleted = self._handleCollateralDuringPurchase(_liqUser, vaultAddr, _asset, payUsdValue, payAmount, _buyer, max_value(uint256), discount, _a.priceDesk)

    # burn amount
    greenToBurn: uint256 = min(amountNeededFromBuyer, staticcall IERC20(_a.greenToken).balanceOf(self))
    extcall GreenToken(_a.greenToken).burn(greenToBurn)

    # update debt
    # TODO: update debt

    return 0



@view
@internal
def _validateOnBuyFungibleAuction(
    _auc: FungibleAuction,
    _buyer: address,
    _payAmount: uint256,
    _greenToken: address,
    _controlRoom: address,
) -> uint256:
    assert _auc.isActive # dev: auction is not active
    assert block.number >= _auc.startBlock and block.number < _auc.endBlock # dev: not within auction window
    assert staticcall ControlRoom(_controlRoom).canBuyAuction(_auc.vaultId, _auc.asset, _buyer) # dev: cannot buy auction

    payAmount: uint256 = min(_payAmount, staticcall IERC20(_greenToken).balanceOf(self))
    assert payAmount != 0 # dev: cannot pay 0
    return payAmount


@pure
@internal
def _calculateDiscount(_progress: uint256, _startDiscount: uint256, _maxDiscount: uint256) -> uint256:
    if _progress == 0 or _startDiscount == _maxDiscount:
        return _startDiscount
    discountRange: uint256 = _maxDiscount - _startDiscount
    adjustment: uint256 =  _progress * discountRange // HUNDRED_PERCENT
    return _startDiscount + adjustment


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
    return staticcall VaultBook(_vaultBook).getVaultAddr(_vaultId), False


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