# @version 0.4.1

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department
from interfaces import Vault
from ethereum.ercs import IERC4626
from ethereum.ercs import IERC20

interface Ledger:
    def getFungibleAuctionDuringPurchase(_liqUser: address, _vaultId: uint256, _asset: address) -> FungibleAuction: view
    def removeFungibleAuction(_liqUser: address, _vaultId: uint256, _asset: address): nonpayable
    def createNewFungibleAuction(_auc: FungibleAuction) -> uint256: nonpayable
    def userVaults(_user: address, _index: uint256) -> uint256: view
    def numUserVaults(_user: address) -> uint256: view

interface CreditEngine:
    def repayDuringLiquidation(_liqUser: address, _userDebt: UserDebt, _repayAmount: uint256, _newInterest: uint256, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def getLatestUserDebtAndTerms(_user: address, _shouldRaise: bool, _a: addys.Addys = empty(addys.Addys)) -> (UserDebt, UserBorrowTerms, uint256): view
    def repayDuringAuctionPurchase(_liqUser: address, _repayAmount: uint256, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable

interface ControlRoom:
    def getAuctionBuyConfig(_asset: address, _buyer: address) -> AuctionBuyConfig: view
    def getAssetLiqConfig(_asset: address) -> AssetLiqConfig: view
    def getGenLiqConfig() -> GenLiqConfig: view

interface PriceDesk:
    def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256: view
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface GreenToken:
    def mint(_to: address, _amount: uint256): nonpayable
    def burn(_amount: uint256): nonpayable

interface StabilityPool:
    def swapForLiquidatedCollateral(_stabAsset: address, _stabAmountToRemove: uint256, _liqAsset: address, _liqAmountSent: uint256, _recipient: address, _greenToken: address) -> uint256: nonpayable

interface VaultBook:
    def getAddr(_vaultId: uint256) -> address: view

struct AuctionBuyConfig:
    canBuyInAuctionGeneral: bool
    canBuyInAuctionAsset: bool
    isUserAllowed: bool

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
    canLiquidate: bool
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

struct FungibleAuction:
    liqUser: address
    vaultId: uint256
    asset: address 
    startDiscount: uint256
    maxDiscount: uint256
    startBlock: uint256
    endBlock: uint256
    isActive: bool

struct FungAuctionPurchase:
    liqUser: address
    vaultId: uint256
    asset: address
    maxGreenAmount: uint256

event LiquidateUser:
    user: indexed(address)
    totalLiqFees: uint256
    targetRepayAmount: uint256
    repayAmount: uint256
    didRestoreDebtHealth: bool
    collateralValueOut: uint256
    numAuctionsStarted: uint256
    keeperFee: uint256

event CollateralSentToEndaoment:
    liqUser: indexed(address)
    vaultId: uint256
    liqAsset: indexed(address)
    amountSent: uint256
    usdValue: uint256
    isDepleted: bool

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
assetLiqConfig: transient(HashMap[address, AssetLiqConfig]) # asset -> config
numUserAssetsForAuction: transient(HashMap[address, uint256]) # user -> num assets
userAssetForAuction: transient(HashMap[address, HashMap[uint256, VaultData]]) # user -> index -> asset

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_GEN_STAB_POOLS: constant(uint256) = 10
MAX_LIQ_USERS: constant(uint256) = 50
MAX_AUCTION_PURCHASES: constant(uint256) = 20


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(True, False) # can mint green (keeper rewards)


###############
# Liquidation #
###############


@external
def liquidateUser(
    _liqUser: address,
    _keeper: address,
    _wantsSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only teller allowed
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    config: GenLiqConfig = staticcall ControlRoom(a.controlRoom).getGenLiqConfig()
    assert config.canLiquidate # dev: cannot liquidate

    keeperRewards: uint256 = self._liquidateUser(_liqUser, config, a)
    assert keeperRewards != 0 # dev: no keeper rewards

    # handle keeper rewards
    self._handleGreenForUser(_keeper, keeperRewards, True, _wantsSavingsGreen, a.greenToken, a.savingsGreen)

    return keeperRewards


@external
def liquidateManyUsers(
    _liqUsers: DynArray[address, MAX_LIQ_USERS],
    _keeper: address,
    _wantsSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only teller allowed
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    config: GenLiqConfig = staticcall ControlRoom(a.controlRoom).getGenLiqConfig()
    assert config.canLiquidate # dev: cannot liquidate

    totalKeeperRewards: uint256 = 0
    for liqUser: address in _liqUsers:
        totalKeeperRewards += self._liquidateUser(liqUser, config, a)
    assert totalKeeperRewards != 0 # dev: no keeper rewards

    # handle keeper rewards
    self._handleGreenForUser(_keeper, totalKeeperRewards, True, _wantsSavingsGreen, a.greenToken, a.savingsGreen)

    return totalKeeperRewards


@internal
def _liquidateUser(
    _liqUser: address,
    _config: GenLiqConfig,
    _a: addys.Addys,
) -> uint256:
    if _liqUser == empty(address):
        return 0

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
    targetRepayAmount: uint256 = self._calcAmountOfDebtToRepay(userDebt.amount, bt.collateralVal, targetLtv)

    # swap collateral to pay debt (liquidation fees basically mean selling at a discount)
    repayValueIn: uint256 = 0
    collateralValueOut: uint256 = 0
    repayValueIn, collateralValueOut = self._handleLiqUserCollateral(_liqUser, targetRepayAmount, liqFeeRatio, _config.genStabPools, _a)

    # repayValueIn may be zero, but need to update debt
    didRestoreDebtHealth: bool = extcall CreditEngine(_a.creditEngine).repayDuringLiquidation(_liqUser, userDebt, repayValueIn, newInterest, _a)

    # start auctions (if necessary)
    numAuctionsStarted: uint256 = 0
    if not didRestoreDebtHealth:
        numAuctionsStarted = self._initiateAuctions(_liqUser, _config.genAuctionParams, _a)

    log LiquidateUser(user=_liqUser, totalLiqFees=totalLiqFees, targetRepayAmount=targetRepayAmount, repayAmount=repayValueIn, didRestoreDebtHealth=didRestoreDebtHealth, collateralValueOut=collateralValueOut, numAuctionsStarted=numAuctionsStarted, keeperFee=keeperFee)
    return keeperFee


@view
@internal
def _calcAmountOfDebtToRepay(_debtAmount: uint256, _collateralValue: uint256, _targetLtv: uint256) -> uint256:
    # goal here is to only reduce the debt necessary to get LTV back to safe position
    # it will never be perfectly precise because depending on what assets are taken, the LTV might slightly change
    collValueAdjusted: uint256 =_collateralValue * _targetLtv // HUNDRED_PERCENT

    toPay: uint256 = (_debtAmount - collValueAdjusted) * HUNDRED_PERCENT // (HUNDRED_PERCENT - _targetLtv)
    return min(toPay, _debtAmount)


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

            liqAsset: address = empty(address)
            hasBalance: bool = False
            liqAsset, hasBalance = staticcall Vault(vaultAddr).getUserAssetAtIndexAndHasBalance(_liqUser, y)
            if liqAsset == empty(address) or not hasBalance:
                continue

            # get asset liq config
            config: AssetLiqConfig = empty(AssetLiqConfig)
            isConfigCached: bool = False
            config, isConfigCached = self._getAssetLiqConfig(liqAsset, _a.controlRoom)

            # cache asset liq config
            if not isConfigCached:
                self.assetLiqConfig[liqAsset] = config

            # no ltv, skip
            if not config.hasLtv:
                continue

            # cannot liquidiate via stability pools if NFT or whitelisted (with no special stab pool)
            if config.isNft or (config.hasWhitelist and config.specialStabPool.vaultAddr == empty(address)):
                self._saveUserAssetForAuction(_liqUser, vaultId, vaultAddr, liqAsset)
                continue

            # stable asset, transfer to endaoment
            stabValueIn: uint256 = 0
            collValueOut: uint256 = 0
            if config.isStable:
                stabValueIn, collValueOut = self._transferStablesToEndaoment(_liqUser, vaultId, vaultAddr, liqAsset, remainingToRepay, _a)
                remainingToRepay -= stabValueIn
                collateralValueOut += collValueOut
                continue

            # stability pools to use
            stabPoolsToUse: DynArray[VaultData, MAX_GEN_STAB_POOLS] = _genStabPools
            if config.specialStabPool.vaultAddr != empty(address):
                stabPoolsToUse = [config.specialStabPool]

            # iterate thru each stab pool
            shouldGoToNextLiqAsset: bool = False
            for sp: VaultData in stabPoolsToUse:
                if remainingToRepay == 0:
                    break

                # swap with stability pool
                stabValueIn, collValueOut, shouldGoToNextLiqAsset = self._swapCollateralWithStabPool(sp, _liqUser, vaultId, vaultAddr, liqAsset, remainingToRepay, _liqFeeRatio, _a)
                remainingToRepay -= stabValueIn
                collateralValueOut += collValueOut

                # if position depleted, nothing else to do with this asset
                if shouldGoToNextLiqAsset:
                    break

            # add to auction list if not depleted
            if not shouldGoToNextLiqAsset:
                self._saveUserAssetForAuction(_liqUser, vaultId, vaultAddr, liqAsset)

    return _targetRepayAmount - remainingToRepay, collateralValueOut


# transfer stables to endaoment


@internal
def _transferStablesToEndaoment(
    _liqUser: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _liqAsset: address,
    _remainingToRepay: uint256,
    _a: addys.Addys,
) -> (uint256, uint256):
    maxAssetAmount: uint256 = staticcall PriceDesk(_a.priceDesk).getAssetAmount(_liqAsset, _remainingToRepay, True)

    # withdraw from vault
    amountSent: uint256 = 0
    isDepleted: bool = False
    amountSent, isDepleted = extcall Vault(_vaultAddr).withdrawTokensFromVault(_liqUser, _liqAsset, maxAssetAmount, _a.endaoment, _a)
    usdValue: uint256 = amountSent * _remainingToRepay // maxAssetAmount

    log CollateralSentToEndaoment(liqUser=_liqUser, vaultId=_vaultId, liqAsset=_liqAsset, amountSent=amountSent, usdValue=usdValue, isDepleted=isDepleted)
    return min(usdValue, _remainingToRepay), amountSent


# swap with stability pool


@internal
def _swapCollateralWithStabPool(
    _stabPool: VaultData,
    _liqUser: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _liqAsset: address,
    _remainingToRepay: uint256,
    _liqFeeRatio: uint256,
    _a: addys.Addys,
) -> (uint256, uint256, bool):

    # cannot liquidiate asset that is also a stability pool asset in that vault
    if staticcall Vault(_stabPool.vaultAddr).isSupportedVaultAsset(_liqAsset):
        return 0, 0, False

    # no balance in stability pool, skip
    maxAmountInStabPool: uint256 = staticcall IERC20(_stabPool.asset).balanceOf(_stabPool.vaultAddr)
    if maxAmountInStabPool == 0:
        return 0, 0, False

    # max usd value in stability pool
    maxValueInStabPool: uint256 = maxAmountInStabPool # green treated as $1
    proceedsAddr: address = empty(address)
    if _stabPool.asset != _a.greenToken:
        maxValueInStabPool = staticcall PriceDesk(_a.priceDesk).getUsdValue(_stabPool.asset, maxAmountInStabPool, True)
        proceedsAddr = _a.endaoment

        # can't get price of stab asset, skip
        if maxValueInStabPool == 0:
            return 0, 0, False

    # handle collateral buy
    amountSentToBuyer: uint256 = 0
    collateralValueOut: uint256 = 0
    amountNeededFromBuyer: uint256 = 0
    shouldGoToNextLiqAsset: bool = False
    amountSentToBuyer, collateralValueOut, amountNeededFromBuyer, shouldGoToNextLiqAsset = self._handleCollateralDuringPurchase(_liqUser, _vaultAddr, _liqAsset, maxValueInStabPool, maxAmountInStabPool, _stabPool.vaultAddr, _remainingToRepay, _liqFeeRatio, _a.priceDesk)

    # nothing sent to buyer, skip
    if amountSentToBuyer == 0:
        return 0, 0, shouldGoToNextLiqAsset

    # remove assets from stability pool
    stabAmountSwapped: uint256 = extcall StabilityPool(_stabPool.vaultAddr).swapForLiquidatedCollateral(_stabPool.asset, amountNeededFromBuyer, _liqAsset, amountSentToBuyer, proceedsAddr, _a.greenToken)
    stabValueSwapped: uint256 = maxValueInStabPool * stabAmountSwapped // maxAmountInStabPool

    log CollateralSwappedWithStabPool(
        liqUser=_liqUser,
        liqVaultId=_vaultId,
        liqAsset=_liqAsset,
        collateralAmountOut=amountSentToBuyer,
        collateralValueOut=collateralValueOut,
        stabVaultId=_stabPool.vaultId,
        stabAsset=_stabPool.asset,
        stabAmountSwapped=stabAmountSwapped,
        stabValueSwapped=stabValueSwapped,
    )
    return min(stabValueSwapped, _remainingToRepay), collateralValueOut, shouldGoToNextLiqAsset


@internal
def _handleCollateralDuringPurchase(
    _liqUser: address,
    _liqVaultAddr: address,
    _liqAsset: address,
    _maxBuyerValue: uint256,
    _maxBuyerAmount: uint256,
    _recipient: address,
    _extraCeilingOnValue: uint256,
    _discount: uint256,
    _priceDesk: address,
) -> (uint256, uint256, uint256, bool):

    # max values from liq user
    maxLiqCollateralValue: uint256 = min(_extraCeilingOnValue, _maxBuyerValue * HUNDRED_PERCENT // (HUNDRED_PERCENT - _discount))
    maxLiqCollateralAmount: uint256 = staticcall PriceDesk(_priceDesk).getAssetAmount(_liqAsset, maxLiqCollateralValue, True)

    # cannot get price info, skip
    if maxLiqCollateralAmount == 0:
        return 0, 0, 0, True

    # transfer collateral to buyer
    amountSentToBuyer: uint256 = 0
    isPositionDepleted: bool = False
    amountSentToBuyer, isPositionDepleted = extcall Vault(_liqVaultAddr).withdrawTokensFromVault(_liqUser, _liqAsset, maxLiqCollateralAmount, _recipient)

    # finalize values for buyer
    collateralValueOut: uint256 = maxLiqCollateralValue * amountSentToBuyer // maxLiqCollateralAmount
    valueNeededFromBuyer: uint256 = collateralValueOut * (HUNDRED_PERCENT - _discount) // HUNDRED_PERCENT
    amountNeededFromBuyer: uint256 = _maxBuyerAmount * valueNeededFromBuyer // _maxBuyerValue

    return amountSentToBuyer, collateralValueOut, amountNeededFromBuyer, isPositionDepleted


######################
# Auction Management #
######################


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
        config, isConfigCached = self._getAssetLiqConfig(d.asset, _a.controlRoom)

        # cache asset liq config
        if not isConfigCached:
            self.assetLiqConfig[d.asset] = config

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


@external
def buyFungibleAuction(
    _liqUser: address,
    _vaultId: uint256,
    _asset: address,
    _greenAmount: uint256,
    _buyer: address,
    _wantsSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only teller allowed
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    greenAmount: uint256 = min(_greenAmount, staticcall IERC20(a.greenToken).balanceOf(self))
    assert greenAmount != 0 # dev: no green to redeem
    greenSpent: uint256 = self._buyFungibleAuction(_liqUser, _vaultId, _asset, max_value(uint256), greenAmount, _buyer, a)
    assert greenSpent != 0 # dev: no green spent

    # handle leftover green
    if greenAmount > greenSpent:
        self._handleGreenForUser(_buyer, greenAmount - greenSpent, False, _wantsSavingsGreen, a.greenToken, a.savingsGreen)

    return greenSpent


@external
def buyManyFungibleAuctions(
    _purchases: DynArray[FungAuctionPurchase, MAX_AUCTION_PURCHASES],
    _greenAmount: uint256,
    _buyer: address,
    _wantsSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only teller allowed
    assert deptBasics.isActivated # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    totalGreenSpent: uint256 = 0
    totalGreenRemaining: uint256 = min(_greenAmount, staticcall IERC20(a.greenToken).balanceOf(self))
    assert totalGreenRemaining != 0 # dev: no green to redeem

    for p: FungAuctionPurchase in _purchases:
        if totalGreenRemaining == 0:
            break
        greenSpent: uint256 = self._buyFungibleAuction(p.liqUser, p.vaultId, p.asset, p.maxGreenAmount, totalGreenRemaining, _buyer, a)
        totalGreenRemaining -= greenSpent
        totalGreenSpent += greenSpent

    assert totalGreenSpent != 0 # dev: no green spent

    # handle leftover green
    if totalGreenRemaining != 0:
        self._handleGreenForUser(_buyer, totalGreenRemaining, False, _wantsSavingsGreen, a.greenToken, a.savingsGreen)

    return totalGreenSpent


@internal
def _buyFungibleAuction(
    _liqUser: address,
    _vaultId: uint256,
    _asset: address,
    _maxGreenForAsset: uint256,
    _totalGreenRemaining: uint256,
    _buyer: address,
    _a: addys.Addys,
) -> uint256:

    # NOTE: faililng gracefully in case there are many purchases at same time

    # this also verifies that user is in liquidation
    auc: FungibleAuction = staticcall Ledger(_a.ledger).getFungibleAuctionDuringPurchase(_liqUser, _vaultId, _asset)
    if not auc.isActive:
        return 0

    # not within time boundaries, skip
    if block.number < auc.startBlock or block.number >= auc.endBlock:
        return 0

    # check auction config
    config: AuctionBuyConfig = staticcall ControlRoom(_a.controlRoom).getAuctionBuyConfig(_asset, _buyer)
    if not config.canBuyInAuctionGeneral or not config.canBuyInAuctionAsset or not config.isUserAllowed:
        return 0

    # finalize green amount
    availGreen: uint256 = min(_totalGreenRemaining, staticcall IERC20(_a.greenToken).balanceOf(self))
    greenAmount: uint256 = min(_maxGreenForAsset, availGreen)
    if greenAmount == 0:
        return 0

    # calculate discount
    auctionProgress: uint256 = (block.number - auc.startBlock) * HUNDRED_PERCENT // (auc.endBlock - auc.startBlock)
    discount: uint256 = self._calculateAuctionDiscount(auctionProgress, auc.startDiscount, auc.maxDiscount)

    # get vault addr
    vaultAddr: address = staticcall VaultBook(_a.vaultBook).getAddr(_vaultId)
    if vaultAddr == empty(address):
        return 0

    # handle collateral buy
    payUsdValue: uint256 = greenAmount # green treated as $1
    amountSentToBuyer: uint256 = 0
    collateralValueOut: uint256 = 0
    amountNeededFromBuyer: uint256 = 0
    isPositionDepleted: bool = False
    amountSentToBuyer, collateralValueOut, amountNeededFromBuyer, isPositionDepleted = self._handleCollateralDuringPurchase(_liqUser, vaultAddr, _asset, payUsdValue, greenAmount, _buyer, max_value(uint256), discount, _a.priceDesk)
    
    # nothing withdrawn from vault, skip
    if amountSentToBuyer == 0:
        return 0

    # disable auction (if depleted)
    if isPositionDepleted:
        extcall Ledger(_a.ledger).removeFungibleAuction(_liqUser, _vaultId, _asset)

    # repay debt for liq user
    greenSpent: uint256 = min(amountNeededFromBuyer, greenAmount)
    assert extcall IERC20(_a.greenToken).transfer(_a.creditEngine, greenSpent, default_return_value=True) # dev: could not transfer
    hasGoodDebtHealth: bool = extcall CreditEngine(_a.creditEngine).repayDuringAuctionPurchase(_liqUser, greenSpent, _a)

    # TODO: event

    return greenSpent


@pure
@internal
def _calculateAuctionDiscount(_progress: uint256, _startDiscount: uint256, _maxDiscount: uint256) -> uint256:
    if _progress == 0 or _startDiscount == _maxDiscount:
        return _startDiscount
    discountRange: uint256 = _maxDiscount - _startDiscount
    adjustment: uint256 =  _progress * discountRange // HUNDRED_PERCENT
    return _startDiscount + adjustment


##################
# Green Handling #
##################


@internal
def _handleGreenForUser(
    _recipient: address,
    _greenAmount: uint256,
    _needsMint: bool,
    _wantsSavingsGreen: bool,
    _greenToken: address,
    _savingsGreen: address,
):
    # mint green
    if _needsMint:
        if not _wantsSavingsGreen:
            extcall GreenToken(_greenToken).mint(_recipient, _greenAmount) # directly to recipient, exit
            return
        extcall GreenToken(_greenToken).mint(self, _greenAmount)

    # finalize amount
    amount: uint256 = min(_greenAmount, staticcall IERC20(_greenToken).balanceOf(self))
    if amount == 0:
        return

    if _wantsSavingsGreen:
        extcall IERC4626(_savingsGreen).deposit(amount, _recipient)
    else:
        assert extcall IERC20(_greenToken).transfer(_recipient, amount, default_return_value=True) # dev: green transfer failed


#########
# Cache #
#########


@view
@internal
def _getAssetLiqConfig(_asset: address, _controlRoom: address) -> (AssetLiqConfig, bool):
    config: AssetLiqConfig = self.assetLiqConfig[_asset]
    if config.hasConfig:
        return config, True
    return staticcall ControlRoom(_controlRoom).getAssetLiqConfig(_asset), False


@view
@internal
def _getVaultAddr(_vaultId: uint256, _vaultBook: address) -> (address, bool):
    vaultAddr: address = self.vaultAddrs[_vaultId]
    if vaultAddr != empty(address):
        return vaultAddr, True
    return staticcall VaultBook(_vaultBook).getAddr(_vaultId), False


@internal
def _saveUserAssetForAuction(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address):
    nextId: uint256 = self.numUserAssetsForAuction[_user]
    self.userAssetForAuction[_user][nextId] = VaultData(vaultId=_vaultId, vaultAddr=_vaultAddr, asset=_asset)
    self.numUserAssetsForAuction[_user] = nextId + 1
