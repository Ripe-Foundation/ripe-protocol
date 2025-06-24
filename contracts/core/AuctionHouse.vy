#               o                                   o        o                                 o         o                                                   
#              <|>                                 <|>     _<|>_                              <|>       <|>                                                  
#              / \                                 < >                                        < >       < >                                                  
#            o/   \o        o       o       __o__   |        o      o__ __o    \o__ __o        |         |     o__ __o     o       o       __o__   o__  __o  
#           <|__ __|>      <|>     <|>     />  \    o__/_   <|>    /v     v\    |     |>       o__/_ _\__o    /v     v\   <|>     <|>     />  \   /v      |> 
#           /       \      < >     < >   o/         |       / \   />       <\  / \   / \       |         |   />       <\  < >     < >     \o     />      //  
#         o/         \o     |       |   <|          |       \o/   \         /  \o/   \o/      <o>       <o>  \         /   |       |       v\    \o    o/    
#        /v           v\    o       o    \\         o        |     o       o    |     |        |         |    o       o    o       o        <\    v\  /v __o 
#       />             <\   <\__ __/>     _\o__</   <\__    / \    <\__ __/>   / \   / \      / \       / \   <\__ __/>    <\__ __/>   _\o__</     <\/> __/> 
#
#     ╔══════════════════════════════════════════╗
#     ║  ** Auction House **                     ║
#     ║  Handles all liquidation-related logic   ║
#     ╚══════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.1
# pragma optimize codesize

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department
from interfaces import Vault
import interfaces.ConfigStructs as cs

from ethereum.ercs import IERC4626
from ethereum.ercs import IERC20

interface Ledger:
    def setFungibleAuction(_liqUser: address, _vaultId: uint256, _asset: address, _auc: FungibleAuction) -> bool: nonpayable
    def getFungibleAuctionDuringPurchase(_liqUser: address, _vaultId: uint256, _asset: address) -> FungibleAuction: view
    def removeFungibleAuction(_liqUser: address, _vaultId: uint256, _asset: address): nonpayable
    def hasFungibleAuction(_liqUser: address, _vaultId: uint256, _asset: address) -> bool: view
    def isParticipatingInVault(_user: address, _vaultId: uint256) -> bool: view
    def createNewFungibleAuction(_auc: FungibleAuction) -> uint256: nonpayable
    def addVaultToUser(_user: address, _vaultId: uint256): nonpayable
    def userVaults(_user: address, _index: uint256) -> uint256: view
    def isUserInLiquidation(_user: address) -> bool: view
    def numUserVaults(_user: address) -> uint256: view

interface MissionControl:
    def getAuctionBuyConfig(_asset: address, _recipient: address) -> AuctionBuyConfig: view
    def getAssetLiqConfig(_asset: address) -> AssetLiqConfig: view
    def getGenAuctionParams() -> cs.AuctionParams: view
    def getGenLiqConfig() -> GenLiqConfig: view

interface StabilityPool:
    def swapForLiquidatedCollateral(_stabAsset: address, _stabAmountToRemove: uint256, _liqAsset: address, _liqAmountSent: uint256, _recipient: address, _greenToken: address, _savingsGreenToken: address) -> uint256: nonpayable
    def swapWithClaimableGreen(_stabAsset: address, _greenAmount: uint256, _liqAsset: address, _liqAmountSent: uint256, _greenToken: address) -> uint256: nonpayable
    def claimableBalances(_stabAsset: address, _greenToken: address) -> uint256: view

interface CreditEngine:
    def repayDuringLiquidation(_liqUser: address, _userDebt: UserDebt, _repayAmount: uint256, _newInterest: uint256, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def getLatestUserDebtAndTerms(_user: address, _shouldRaise: bool, _a: addys.Addys = empty(addys.Addys)) -> (UserDebt, UserBorrowTerms, uint256): view
    def repayDuringAuctionPurchase(_liqUser: address, _repayAmount: uint256, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable

interface PriceDesk:
    def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256: view
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface GreenToken:
    def mint(_to: address, _amount: uint256): nonpayable
    def burn(_amount: uint256) -> bool: nonpayable

interface LootBox:
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address, _a: addys.Addys = empty(addys.Addys)): nonpayable

interface Teller:
    def isUnderscoreWalletOwner(_user: address, _caller: address, _mc: address = empty(address)) -> bool: view

interface VaultBook:
    def getAddr(_vaultId: uint256) -> address: view

struct AuctionBuyConfig:
    canBuyInAuctionGeneral: bool
    canBuyInAuctionAsset: bool
    isUserAllowed: bool
    canAnyoneDeposit: bool

struct UserBorrowTerms:
    collateralVal: uint256
    totalMaxDebt: uint256
    debtTerms: cs.DebtTerms

struct UserDebt:
    amount: uint256
    principal: uint256
    debtTerms: cs.DebtTerms
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
    maxKeeperFee: uint256
    ltvPaybackBuffer: uint256
    genAuctionParams: cs.AuctionParams
    priorityLiqAssetVaults: DynArray[VaultData, PRIORITY_LIQ_VAULT_DATA]
    priorityStabVaults: DynArray[VaultData, MAX_STAB_VAULT_DATA]

struct AssetLiqConfig:
    hasConfig: bool
    shouldBurnAsPayment: bool
    shouldTransferToEndaoment: bool
    shouldSwapInStabPools: bool
    shouldAuctionInstantly: bool
    customAuctionParams: cs.AuctionParams
    specialStabPool: VaultData

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

struct FungAuctionConfig:
    liqUser: address
    vaultId: uint256
    asset: address

event LiquidateUser:
    user: indexed(address)
    totalLiqFees: uint256
    targetRepayAmount: uint256
    repayAmount: uint256
    didRestoreDebtHealth: bool
    collateralValueOut: uint256
    liqFeesUnpaid: uint256
    numAuctionsStarted: uint256
    keeperFee: uint256

event CollateralSentToEndaoment:
    liqUser: indexed(address)
    vaultId: uint256
    liqAsset: indexed(address)
    amountSent: uint256
    usdValue: uint256
    isDepleted: bool

event StabAssetBurntAsRepayment:
    liqUser: indexed(address)
    vaultId: uint256
    liqStabAsset: indexed(address)
    amountBurned: uint256
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
    assetSwapped: address
    amountSwapped: uint256
    valueSwapped: uint256

event FungibleAuctionUpdated:
    liqUser: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    startDiscount: uint256
    maxDiscount: uint256
    startBlock: uint256
    endBlock: uint256
    isNewAuction: bool

event FungibleAuctionPaused:
    liqUser: indexed(address)
    vaultId: uint256
    asset: indexed(address)

event FungAuctionPurchased:
    liqUser: indexed(address)
    liqVaultId: uint256
    liqAsset: indexed(address)
    greenSpent: uint256
    recipient: indexed(address)
    caller: address
    collateralAmountSent: uint256
    collateralUsdValueSent: uint256
    isPositionDepleted: bool
    hasGoodDebtHealth: bool

# cache
vaultAddrs: transient(HashMap[uint256, address]) # vaultId -> vaultAddr
assetLiqConfig: transient(HashMap[address, AssetLiqConfig]) # asset -> config
didHandleLiqAsset: transient(HashMap[address, HashMap[uint256, HashMap[address, bool]]]) # user -> vaultId -> asset -> did handle
didHandleVaultId: transient(HashMap[address, HashMap[uint256, bool]]) # user -> vaultId -> did handle
numUserAssetsForAuction: transient(HashMap[address, uint256]) # user -> num assets
userAssetForAuction: transient(HashMap[address, HashMap[uint256, VaultData]]) # user -> index -> asset

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
ONE_PERCENT: constant(uint256) = 1_00 # 1%
MAX_STAB_VAULT_DATA: constant(uint256) = 10
PRIORITY_LIQ_VAULT_DATA: constant(uint256) = 20
MAX_LIQ_USERS: constant(uint256) = 50
MAX_AUCTIONS: constant(uint256) = 20


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, True, False) # can mint green (keeper rewards)


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
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    config: GenLiqConfig = staticcall MissionControl(a.missionControl).getGenLiqConfig()
    assert config.canLiquidate # dev: cannot liquidate

    # liquidate user
    keeperRewards: uint256 = self._liquidateUser(_liqUser, config, a)

    # handle keeper rewards
    if keeperRewards != 0:
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
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    config: GenLiqConfig = staticcall MissionControl(a.missionControl).getGenLiqConfig()
    assert config.canLiquidate # dev: cannot liquidate

    totalKeeperRewards: uint256 = 0
    for liqUser: address in _liqUsers:
        totalKeeperRewards += self._liquidateUser(liqUser, config, a)

    # handle keeper rewards
    if totalKeeperRewards != 0:
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

    # user has debt but no liquidation threshold - cannot liquidate
    if bt.debtTerms.liqThreshold == 0:
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
    if keeperFee != 0 and _config.maxKeeperFee != 0:
        keeperFee = min(keeperFee, _config.maxKeeperFee)

    if keeperFee != 0:
        totalLiqFees += keeperFee
        liqFeeRatio = totalLiqFees * HUNDRED_PERCENT // userDebt.amount

    # how much to achieve safe LTV - use single robust formula for all liquidation types
    targetLtv: uint256 = bt.debtTerms.ltv * (HUNDRED_PERCENT - _config.ltvPaybackBuffer) // HUNDRED_PERCENT
    targetRepayAmount: uint256 = self._calcTargetRepayAmount(userDebt.amount, bt.collateralVal, targetLtv, liqFeeRatio)

    # perform liquidation phases
    repayValueIn: uint256 = 0
    collateralValueOut: uint256 = 0
    repayValueIn, collateralValueOut = self._performLiquidationPhases(_liqUser, targetRepayAmount, liqFeeRatio, _config, _a)

    # check if liq fees were already covered (stability pool swaps)
    liqFeesUnpaid: uint256 = totalLiqFees
    if collateralValueOut > repayValueIn:
        paidLiqFees: uint256 = collateralValueOut - repayValueIn
        liqFeesUnpaid -= min(paidLiqFees, liqFeesUnpaid)

    # repayValueIn may be zero, but need to update debt
    userDebt.amount += liqFeesUnpaid
    repayValueIn = min(repayValueIn, userDebt.amount)
    didRestoreDebtHealth: bool = extcall CreditEngine(_a.creditEngine).repayDuringLiquidation(_liqUser, userDebt, repayValueIn, newInterest, _a)

    # start auctions (if necessary)
    numAuctionsStarted: uint256 = 0
    if not didRestoreDebtHealth:
        numAuctionsStarted = self._startAuctionsDuringLiq(_liqUser, _config.genAuctionParams, _a.missionControl, _a.ledger)

    log LiquidateUser(
        user=_liqUser,
        totalLiqFees=totalLiqFees,
        targetRepayAmount=targetRepayAmount,
        repayAmount=repayValueIn,
        didRestoreDebtHealth=didRestoreDebtHealth,
        collateralValueOut=collateralValueOut,
        liqFeesUnpaid=liqFeesUnpaid,
        numAuctionsStarted=numAuctionsStarted,
        keeperFee=keeperFee,
    )
    return keeperFee


########################
# Liquidation - Phases #
########################


@internal
def _performLiquidationPhases(
    _liqUser: address,
    _targetRepayAmount: uint256,
    _liqFeeRatio: uint256,
    _config: GenLiqConfig,
    _a: addys.Addys,
) -> (uint256, uint256):
    remainingToRepay: uint256 = _targetRepayAmount
    collateralValueOut: uint256 = 0

    # PHASE 1 -- If liq user is in stability pool, use those assets first to pay off debt

    for stabPool: VaultData in _config.priorityStabVaults:
        if remainingToRepay == 0:
            break

        if not staticcall Ledger(_a.ledger).isParticipatingInVault(_liqUser, stabPool.vaultId):
            continue

        remainingToRepay, collateralValueOut = self._iterateThruAssetsWithinVault(_liqUser, stabPool.vaultId, stabPool.vaultAddr, remainingToRepay, collateralValueOut, _liqFeeRatio, [], _a)
        if self.vaultAddrs[stabPool.vaultId] == empty(address):
            self.vaultAddrs[stabPool.vaultId] = stabPool.vaultAddr # cache

    # PHASE 2 -- Go thru priority liq assets (set in mission control)

    if remainingToRepay != 0:
        for pData: VaultData in _config.priorityLiqAssetVaults:
            if remainingToRepay == 0:
                break

            if not staticcall Vault(pData.vaultAddr).doesUserHaveBalance(_liqUser, pData.asset):
                continue

            remainingToRepay, collateralValueOut = self._handleSpecificLiqAsset(_liqUser, pData.vaultId, pData.vaultAddr, pData.asset, remainingToRepay, collateralValueOut, _liqFeeRatio, _config.priorityStabVaults, _a)
            if self.vaultAddrs[pData.vaultId] == empty(address):
                self.vaultAddrs[pData.vaultId] = pData.vaultAddr # cache

    # PHASE 3 -- Go thru user's vaults (top to bottom as saved in ledger / vaults)

    if remainingToRepay != 0:
        remainingToRepay, collateralValueOut = self._iterateThruAllUserVaults(_liqUser, remainingToRepay, collateralValueOut, _liqFeeRatio, _config.priorityStabVaults, _a)

    return _targetRepayAmount - remainingToRepay, collateralValueOut


#################################
# Liquidation - All User Vaults #
#################################


@internal
def _iterateThruAllUserVaults(
    _liqUser: address,
    _remainingToRepay: uint256,
    _collateralValueOut: uint256,
    _liqFeeRatio: uint256,
    _genStabPools: DynArray[VaultData, MAX_STAB_VAULT_DATA],
    _a: addys.Addys,
) -> (uint256, uint256):
    remainingToRepay: uint256 = _remainingToRepay
    collateralValueOut: uint256 = _collateralValueOut

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
        if vaultAddr == empty(address):
            continue

        # cache vault addr
        if not isVaultAddrCached:
            self.vaultAddrs[vaultId] = vaultAddr

        remainingToRepay, collateralValueOut = self._iterateThruAssetsWithinVault(_liqUser, vaultId, vaultAddr, remainingToRepay, collateralValueOut, _liqFeeRatio, _genStabPools, _a)

    return remainingToRepay, collateralValueOut


#####################################
# Liquidation - Assets Within Vault #
#####################################


@internal
def _iterateThruAssetsWithinVault(
    _liqUser: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _remainingToRepay: uint256,
    _collateralValueOut: uint256,
    _liqFeeRatio: uint256,
    _genStabPools: DynArray[VaultData, MAX_STAB_VAULT_DATA],
    _a: addys.Addys,
) -> (uint256, uint256):

    # check if we've already handled this vault
    if self.didHandleVaultId[_liqUser][_vaultId]:
        return _remainingToRepay, _collateralValueOut
    self.didHandleVaultId[_liqUser][_vaultId] = True

    # no assets in vault, skip
    numUserAssets: uint256 = staticcall Vault(_vaultAddr).numUserAssets(_liqUser)
    if numUserAssets == 0:
        return _remainingToRepay, _collateralValueOut

    # totals
    remainingToRepay: uint256 = _remainingToRepay
    collateralValueOut: uint256 = _collateralValueOut
    for y: uint256 in range(1, numUserAssets, bound=max_value(uint256)):
        if remainingToRepay == 0:
            break

        # check if user still has balance in this asset
        liqAsset: address = empty(address)
        hasBalance: bool = False
        liqAsset, hasBalance = staticcall Vault(_vaultAddr).getUserAssetAtIndexAndHasBalance(_liqUser, y)
        if liqAsset == empty(address) or not hasBalance:
            continue

        # handle specific liq asset
        remainingToRepay, collateralValueOut = self._handleSpecificLiqAsset(_liqUser, _vaultId, _vaultAddr, liqAsset, remainingToRepay, collateralValueOut, _liqFeeRatio, _genStabPools, _a)

    return remainingToRepay, collateralValueOut


################################
# Liquidation - Specific Asset #
################################


@internal
def _handleSpecificLiqAsset(
    _liqUser: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _liqAsset: address,
    _remainingToRepay: uint256,
    _collateralValueOut: uint256,
    _liqFeeRatio: uint256,
    _genStabPools: DynArray[VaultData, MAX_STAB_VAULT_DATA],
    _a: addys.Addys,
) -> (uint256, uint256):

    # check if we've already handled this liq asset (cache for next time)
    if self.didHandleLiqAsset[_liqUser][_vaultId][_liqAsset]:
        return _remainingToRepay, _collateralValueOut
    self.didHandleLiqAsset[_liqUser][_vaultId][_liqAsset] = True

    # asset liq config
    config: AssetLiqConfig = empty(AssetLiqConfig)
    isConfigCached: bool = False
    config, isConfigCached = self._getAssetLiqConfig(_liqAsset, _a.missionControl)
    if not isConfigCached:
        self.assetLiqConfig[_liqAsset] = config

    # totals
    remainingToRepay: uint256 = _remainingToRepay
    collateralValueOut: uint256 = _collateralValueOut

    # burn as payment (GREEN, sGREEN)
    if config.shouldBurnAsPayment and _liqAsset in [_a.greenToken, _a.savingsGreen]:
        remainingToRepay, collateralValueOut = self._burnLiqUserStabAsset(_liqUser, _vaultId, _vaultAddr, _liqAsset, remainingToRepay, collateralValueOut, _a)
        return remainingToRepay, collateralValueOut

    # endaoment wants this asset (other stablecoins)
    if config.shouldTransferToEndaoment:
        remainingToRepay, collateralValueOut = self._transferToEndaoment(_liqUser, _vaultId, _vaultAddr, _liqAsset, remainingToRepay, collateralValueOut, _a)
        return remainingToRepay, collateralValueOut

    # stability pool swaps (eth, btc, etc)
    isPositionDepleted: bool = False
    if config.shouldSwapInStabPools:
        remainingToRepay, collateralValueOut, isPositionDepleted = self._swapWithStabPools(_liqUser, _vaultId, _vaultAddr, _liqAsset, _liqFeeRatio, remainingToRepay, collateralValueOut, config.specialStabPool, _genStabPools, _a)

    # add to auction list if not depleted
    if config.shouldAuctionInstantly and not isPositionDepleted:
        self._saveLiqAssetForAuction(_liqUser, _vaultId, _vaultAddr, _liqAsset)

    return remainingToRepay, collateralValueOut


####################################
# Liquidation - Endaoment Transfer #
####################################


@internal
def _transferToEndaoment(
    _liqUser: address,
    _liqVaultId: uint256,
    _liqVaultAddr: address,
    _liqAsset: address,
    _remainingToRepay: uint256,
    _collateralValueOut: uint256,
    _a: addys.Addys,
) -> (uint256, uint256):
    remainingToRepay: uint256 = _remainingToRepay
    collateralValueOut: uint256 = _collateralValueOut

    collateralUsdValueSent: uint256 = 0
    collateralAmountSent: uint256 = 0
    isPositionDepleted: bool = False
    na: bool = False
    collateralUsdValueSent, collateralAmountSent, isPositionDepleted, na = self._transferCollateral(_liqUser, _a.endaoment, _liqVaultId, _liqVaultAddr, _liqAsset, False, remainingToRepay, _a)
    if collateralUsdValueSent == 0:
        return remainingToRepay, collateralValueOut

    # update totals
    remainingToRepay -= min(collateralUsdValueSent, remainingToRepay)
    collateralValueOut += collateralUsdValueSent

    log CollateralSentToEndaoment(
        liqUser=_liqUser,
        vaultId=_liqVaultId,
        liqAsset=_liqAsset,
        amountSent=collateralAmountSent,
        usdValue=collateralUsdValueSent,
        isDepleted=isPositionDepleted,
    )
    return remainingToRepay, collateralValueOut


#################################
# Liquidation - Burn Stab Asset #
#################################


@internal
def _burnLiqUserStabAsset(
    _liqUser: address,
    _liqVaultId: uint256,
    _liqVaultAddr: address,
    _liqStabAsset: address,
    _remainingToRepay: uint256,
    _collateralValueOut: uint256,
    _a: addys.Addys,
) -> (uint256, uint256):
    remainingToRepay: uint256 = _remainingToRepay
    collateralValueOut: uint256 = _collateralValueOut

    usdValue: uint256 = 0
    amountReceived: uint256 = 0
    isPositionDepleted: bool = False
    na: bool = False
    usdValue, amountReceived, isPositionDepleted, na = self._transferCollateral(_liqUser, self, _liqVaultId, _liqVaultAddr, _liqStabAsset, False, remainingToRepay, _a)
    if usdValue == 0:
        return remainingToRepay, collateralValueOut

    # burn stab asset
    if _liqStabAsset == _a.savingsGreen:
        greenAmount: uint256 = extcall IERC4626(_a.savingsGreen).redeem(amountReceived, self, self) # dev: savings green redeem failed
        assert extcall GreenToken(_a.greenToken).burn(greenAmount) # dev: failed to burn green
    else:
        assert extcall GreenToken(_a.greenToken).burn(amountReceived) # dev: failed to burn green

    # update totals
    remainingToRepay -= min(usdValue, remainingToRepay)
    collateralValueOut += usdValue

    log StabAssetBurntAsRepayment(
        liqUser=_liqUser,
        vaultId=_liqVaultId,
        liqStabAsset=_liqStabAsset,
        amountBurned=amountReceived,
        usdValue=usdValue,
        isDepleted=isPositionDepleted,
    )
    return remainingToRepay, collateralValueOut


######################################
# Liquidation - Stability Pool Swaps #
######################################


# iterate thru stab pools


@internal
def _swapWithStabPools(
    _liqUser: address,
    _liqVaultId: uint256,
    _liqVaultAddr: address,
    _liqAsset: address,
    _liqFeeRatio: uint256,
    _remainingToRepay: uint256,
    _collateralValueOut: uint256,
    _specialStabPool: VaultData,
    _genStabPools: DynArray[VaultData, MAX_STAB_VAULT_DATA],
    _a: addys.Addys,
) -> (uint256, uint256, bool):

    # stability pools to use
    stabPoolsToUse: DynArray[VaultData, MAX_STAB_VAULT_DATA] = _genStabPools
    if _specialStabPool.vaultAddr != empty(address):
        stabPoolsToUse = [_specialStabPool]

    # nothing to do here
    if len(stabPoolsToUse) == 0:
        return _remainingToRepay, _collateralValueOut, False

    # totals
    remainingToRepay: uint256 = _remainingToRepay
    collateralValueOut: uint256 = _collateralValueOut

    # iterate thru each stab pool
    isPositionDepleted: bool = False
    for stabPool: VaultData in stabPoolsToUse:
        if remainingToRepay == 0:
            break

        # swap with stability pool
        shouldGoToNextAsset: bool = False
        remainingToRepay, collateralValueOut, isPositionDepleted, shouldGoToNextAsset = self._swapWithSpecificStabPool(stabPool, _liqUser, _liqVaultId, _liqVaultAddr, _liqAsset, _liqFeeRatio, remainingToRepay, collateralValueOut, _a)

        # nothing else to do here
        if isPositionDepleted or shouldGoToNextAsset:
            break

    return remainingToRepay, collateralValueOut, isPositionDepleted


# individual stability pool swap


@internal
def _swapWithSpecificStabPool(
    _stabPool: VaultData,
    _liqUser: address,
    _liqVaultId: uint256,
    _liqVaultAddr: address,
    _liqAsset: address,
    _liqFeeRatio: uint256,
    _remainingToRepay: uint256,
    _collateralValueOut: uint256,
    _a: addys.Addys,
) -> (uint256, uint256, bool, bool):
    remainingToRepay: uint256 = _remainingToRepay
    collateralValueOut: uint256 = _collateralValueOut

    # cannot liquidate asset that is also a stability pool asset in that vault
    if staticcall Vault(_stabPool.vaultAddr).isSupportedVaultAsset(_liqAsset):
        return remainingToRepay, collateralValueOut, False, False

    # check for green redemptions for this stab asset
    isPositionDepleted: bool = False
    shouldGoToNextAsset: bool = False
    remainingToRepay, collateralValueOut, isPositionDepleted, shouldGoToNextAsset = self._swapWithGreenRedemptions(_stabPool, _liqUser, _liqVaultId, _liqVaultAddr, _liqAsset, _liqFeeRatio, remainingToRepay, collateralValueOut, _a)
    if remainingToRepay == 0 or isPositionDepleted or shouldGoToNextAsset:
        return remainingToRepay, collateralValueOut, isPositionDepleted, shouldGoToNextAsset

    # no balance in stability pool, skip
    maxAmountInStabPool: uint256 = staticcall IERC20(_stabPool.asset).balanceOf(_stabPool.vaultAddr)
    if maxAmountInStabPool == 0:
        return remainingToRepay, collateralValueOut, False, False

    # max usd value in stability pool
    maxUsdValueInStabPool: uint256 = self._getUsdValue(_stabPool.asset, maxAmountInStabPool, _a.greenToken, _a.savingsGreen, _a.priceDesk)  
    if maxUsdValueInStabPool == 0:
        return remainingToRepay, collateralValueOut, False, False # can't get price of stab asset, skip      

    # where to move stab asset
    stabProceedsAddr: address = _a.endaoment # non-green assets, move to Endaoment
    if _stabPool.asset in [_a.greenToken, _a.savingsGreen]:
        stabProceedsAddr = empty(address)

    # swap with stability pool
    return self._swapAssetsWithStabPool(True, _liqUser, _liqVaultId, _liqVaultAddr, _liqAsset, _liqFeeRatio, maxAmountInStabPool, maxUsdValueInStabPool, remainingToRepay, collateralValueOut, _stabPool, stabProceedsAddr, _a)


@view
@internal
def _getUsdValue(
    _asset: address,
    _amount: uint256,
    _greenToken: address,
    _savingsGreen: address,
    _priceDesk: address,
) -> uint256:
    usdValue: uint256 = 0
    if _asset == _greenToken:
        usdValue = _amount
    elif _asset == _savingsGreen:
        usdValue = staticcall IERC4626(_savingsGreen).convertToAssets(_amount)
    else:
        usdValue = staticcall PriceDesk(_priceDesk).getUsdValue(_asset, _amount, True)
    return usdValue


@internal
def _swapWithGreenRedemptions(
    _stabPool: VaultData,
    _liqUser: address,
    _liqVaultId: uint256,
    _liqVaultAddr: address,
    _liqAsset: address,
    _liqFeeRatio: uint256,
    _remainingToRepay: uint256,
    _collateralValueOut: uint256,
    _a: addys.Addys,
) -> (uint256, uint256, bool, bool):
    maxClaimableGreen: uint256 = staticcall StabilityPool(_stabPool.vaultAddr).claimableBalances(_stabPool.asset, _a.greenToken)
    if maxClaimableGreen == 0:
        return _remainingToRepay, _collateralValueOut, False, False
    return self._swapAssetsWithStabPool(False, _liqUser, _liqVaultId, _liqVaultAddr, _liqAsset, _liqFeeRatio, maxClaimableGreen, maxClaimableGreen, _remainingToRepay, _collateralValueOut, _stabPool, empty(address), _a)


@internal
def _swapAssetsWithStabPool(
    _isNormalStabSwap: bool,
    _liqUser: address,
    _liqVaultId: uint256,
    _liqVaultAddr: address,
    _liqAsset: address,
    _liqFeeRatio: uint256,
    _maxAmountInStabPool: uint256,
    _maxUsdValueInStabPool: uint256,
    _remainingToRepay: uint256,
    _collateralValueOut: uint256,
    _stabPool: VaultData,
    _stabProceedsAddr: address,
    _a: addys.Addys,
) -> (uint256, uint256, bool, bool):
    remainingToRepay: uint256 = _remainingToRepay
    collateralValueOut: uint256 = _collateralValueOut

    # max collateral usd value (to take from liq user)
    maxCollateralUsdValue: uint256 = min(_maxUsdValueInStabPool, remainingToRepay) * HUNDRED_PERCENT // (HUNDRED_PERCENT - _liqFeeRatio)

    # transfer collateral to stability pool
    collateralUsdValueSent: uint256 = 0
    collateralAmountSent: uint256 = 0
    isPositionDepleted: bool = False
    shouldGoToNextAsset: bool = False
    collateralUsdValueSent, collateralAmountSent, isPositionDepleted, shouldGoToNextAsset = self._transferCollateral(_liqUser, _stabPool.vaultAddr, _liqVaultId, _liqVaultAddr, _liqAsset, False, maxCollateralUsdValue, _a)
    if collateralUsdValueSent == 0 or collateralAmountSent == 0:
        return remainingToRepay, collateralValueOut, isPositionDepleted, shouldGoToNextAsset

    # calc target stab pool values
    targetStabPoolUsdValue: uint256 = collateralUsdValueSent * (HUNDRED_PERCENT - _liqFeeRatio) // HUNDRED_PERCENT
    targetStabPoolAmount: uint256 = targetStabPoolUsdValue * _maxAmountInStabPool // _maxUsdValueInStabPool

    # take asset out of stability pool
    stabPoolAmount: uint256 = 0
    assetSwapped: address = empty(address)
    if _isNormalStabSwap:
        stabPoolAmount = extcall StabilityPool(_stabPool.vaultAddr).swapForLiquidatedCollateral(_stabPool.asset, targetStabPoolAmount, _liqAsset, collateralAmountSent, _stabProceedsAddr, _a.greenToken, _a.savingsGreen)
        assetSwapped = _stabPool.asset
    else:
        stabPoolAmount = extcall StabilityPool(_stabPool.vaultAddr).swapWithClaimableGreen(_stabPool.asset, targetStabPoolAmount, _liqAsset, collateralAmountSent, _a.greenToken)
        assetSwapped = _a.greenToken

    # verify it's a fair swap
    assert self._isPaymentCloseEnough(targetStabPoolAmount, stabPoolAmount) # dev: invalid stability pool swap

    # update overall values
    stabValueSwapped: uint256 = _maxUsdValueInStabPool * stabPoolAmount // _maxAmountInStabPool
    remainingToRepay -= min(stabValueSwapped, remainingToRepay)
    collateralValueOut += collateralUsdValueSent

    log CollateralSwappedWithStabPool(
        liqUser=_liqUser,
        liqVaultId=_liqVaultId,
        liqAsset=_liqAsset,
        collateralAmountOut=collateralAmountSent,
        collateralValueOut=collateralUsdValueSent,
        stabVaultId=_stabPool.vaultId,
        stabAsset=_stabPool.asset,
        assetSwapped=assetSwapped,
        amountSwapped=stabPoolAmount,
        valueSwapped=stabValueSwapped,
    )
    return remainingToRepay, collateralValueOut, isPositionDepleted, shouldGoToNextAsset


######################
# Auction Initiation #
######################


# start during liquidation


@internal
def _startAuctionsDuringLiq(
    _liqUser: address,
    _genAuctionParams: cs.AuctionParams,
    _missionControl: address,
    _ledger: address,
) -> uint256:
    numAssets: uint256 = self.numUserAssetsForAuction[_liqUser]
    if numAssets == 0:
        return 0

    numAuctionsStarted: uint256 = 0
    for i: uint256 in range(numAssets, bound=max_value(uint256)):
        d: VaultData = self.userAssetForAuction[_liqUser][i]
        didCreateAuction: bool = self._createOrUpdateFungAuction(_liqUser, d.vaultId, d.asset, False, _genAuctionParams, _missionControl, _ledger)
        if didCreateAuction:
            numAuctionsStarted += 1

    return numAuctionsStarted


# start / restart (via mission control)


@external
def startAuction(
    _liqUser: address,
    _liqVaultId: uint256,
    _liqAsset: address,
    _a: addys.Addys = empty(addys.Addys),
) -> bool:
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)
    genParams: cs.AuctionParams = staticcall MissionControl(a.missionControl).getGenAuctionParams()
    return self._startAuction(_liqUser, _liqVaultId, _liqAsset, genParams, a)


@external
def startManyAuctions(
    _auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS],
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    genParams: cs.AuctionParams = staticcall MissionControl(a.missionControl).getGenAuctionParams()
    numAuctionsStarted: uint256 = 0
    for auc: FungAuctionConfig in _auctions:
        didStart: bool = self._startAuction(auc.liqUser, auc.vaultId, auc.asset, genParams, a)
        if didStart:
            numAuctionsStarted += 1

    return numAuctionsStarted


@internal
def _startAuction(
    _liqUser: address,
    _liqVaultId: uint256,
    _liqAsset: address,
    _genParams: cs.AuctionParams,
    _a: addys.Addys,
) -> bool:
    if not self._canStartAuction(_liqUser, _liqVaultId, _liqAsset, _a.vaultBook, _a.ledger):
        return False
    hasAuction: bool = staticcall Ledger(_a.ledger).hasFungibleAuction(_liqUser, _liqVaultId, _liqAsset)
    return self._createOrUpdateFungAuction(_liqUser, _liqVaultId, _liqAsset, hasAuction, _genParams, _a.missionControl, _a.ledger)


# validation


@view
@external
def canStartAuction(
    _liqUser: address,
    _liqVaultId: uint256,
    _liqAsset: address,
) -> bool:
    a: addys.Addys = addys._getAddys()
    return self._canStartAuction(_liqUser, _liqVaultId, _liqAsset, a.vaultBook, a.ledger)


@view
@internal
def _canStartAuction(
    _liqUser: address,
    _liqVaultId: uint256,
    _liqAsset: address,
    _vaultBook: address,
    _ledger: address,
) -> bool:
    vaultAddr: address = staticcall VaultBook(_vaultBook).getAddr(_liqVaultId)
    if vaultAddr == empty(address):
        return False
    if not staticcall Vault(vaultAddr).doesUserHaveBalance(_liqUser, _liqAsset):
        return False
    return staticcall Ledger(_ledger).isUserInLiquidation(_liqUser)


# create auction


@internal
def _createOrUpdateFungAuction(
    _liqUser: address,
    _vaultId: uint256,
    _asset: address,
    _alreadyExists: bool,
    _genAuctionParams: cs.AuctionParams,
    _missionControl: address,
    _ledger: address,
) -> bool:

    # get asset liq config
    config: AssetLiqConfig = empty(AssetLiqConfig)
    isConfigCached: bool = False
    config, isConfigCached = self._getAssetLiqConfig(_asset, _missionControl)
    if not isConfigCached:
        self.assetLiqConfig[_asset] = config # cache

    # finalize auction params
    params: cs.AuctionParams = _genAuctionParams
    if config.customAuctionParams.hasParams:
        params = config.customAuctionParams

    startBlock: uint256 = block.number + params.delay
    endBlock: uint256 = startBlock + params.duration
    auctionData: FungibleAuction = FungibleAuction(
        liqUser=_liqUser,
        vaultId=_vaultId,
        asset=_asset,
        startDiscount=params.startDiscount,
        maxDiscount=params.maxDiscount,
        startBlock=startBlock,
        endBlock=endBlock,
        isActive=True,
    )

    # update existing auction data
    if _alreadyExists:
        assert extcall Ledger(_ledger).setFungibleAuction(_liqUser, _vaultId, _asset, auctionData) # dev: failed to set auction

    # create new auction
    else:
        aid: uint256 = extcall Ledger(_ledger).createNewFungibleAuction(auctionData)
        if aid == 0:
            return False # fail gracefully, though this should never happen

    log FungibleAuctionUpdated(
        liqUser=_liqUser,
        vaultId=_vaultId,
        asset=_asset,
        startDiscount=params.startDiscount,
        maxDiscount=params.maxDiscount,
        startBlock=startBlock,
        endBlock=endBlock,
        isNewAuction=not _alreadyExists,
    )
    return True


# pause


@external
def pauseAuction(
    _liqUser: address,
    _liqVaultId: uint256,
    _liqAsset: address,
    _a: addys.Addys = empty(addys.Addys),
) -> bool:
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)
    return self._pauseAuction(_liqUser, _liqVaultId, _liqAsset, a.ledger)


@external
def pauseManyAuctions(
    _auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS],
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    numAuctionsPaused: uint256 = 0
    for auc: FungAuctionConfig in _auctions:
        didPause: bool = self._pauseAuction(auc.liqUser, auc.vaultId, auc.asset, a.ledger)
        if didPause:
            numAuctionsPaused += 1

    return numAuctionsPaused


@internal
def _pauseAuction(
    _liqUser: address,
    _liqVaultId: uint256,
    _liqAsset: address,
    _ledger: address,
) -> bool:
    auc: FungibleAuction = staticcall Ledger(_ledger).getFungibleAuctionDuringPurchase(_liqUser, _liqVaultId, _liqAsset)
    if not auc.isActive:
        return False

    auc.isActive = False
    assert extcall Ledger(_ledger).setFungibleAuction(_liqUser, _liqVaultId, _liqAsset, auc) # dev: failed to set auction
    log FungibleAuctionPaused(
        liqUser=_liqUser,
        vaultId=_liqVaultId,
        asset=_liqAsset,
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
    _recipient: address,
    _caller: address,
    _shouldTransferBalance: bool,
    _shouldRefundSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only teller allowed
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    greenAmount: uint256 = min(_greenAmount, staticcall IERC20(a.greenToken).balanceOf(self))
    assert greenAmount != 0 # dev: no green to spend
    greenSpent: uint256 = self._buyFungibleAuction(_liqUser, _vaultId, _asset, max_value(uint256), greenAmount, _recipient, _caller, _shouldTransferBalance, a)
    assert greenSpent != 0 # dev: no green spent

    # handle leftover green
    if greenAmount > greenSpent:
        self._handleGreenForUser(_caller, greenAmount - greenSpent, False, _shouldRefundSavingsGreen, a.greenToken, a.savingsGreen)

    return greenSpent


@external
def buyManyFungibleAuctions(
    _purchases: DynArray[FungAuctionPurchase, MAX_AUCTIONS],
    _greenAmount: uint256,
    _recipient: address,
    _caller: address,
    _shouldTransferBalance: bool,
    _shouldRefundSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only teller allowed
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    totalGreenSpent: uint256 = 0
    totalGreenRemaining: uint256 = min(_greenAmount, staticcall IERC20(a.greenToken).balanceOf(self))
    assert totalGreenRemaining != 0 # dev: no green to spend

    for p: FungAuctionPurchase in _purchases:
        if totalGreenRemaining == 0:
            break
        greenSpent: uint256 = self._buyFungibleAuction(p.liqUser, p.vaultId, p.asset, p.maxGreenAmount, totalGreenRemaining, _recipient, _caller, _shouldTransferBalance, a)
        totalGreenRemaining -= greenSpent
        totalGreenSpent += greenSpent

    assert totalGreenSpent != 0 # dev: no green spent

    # handle leftover green
    if totalGreenRemaining != 0:
        self._handleGreenForUser(_caller, totalGreenRemaining, False, _shouldRefundSavingsGreen, a.greenToken, a.savingsGreen)

    return totalGreenSpent


@internal
def _buyFungibleAuction(
    _liqUser: address,
    _liqVaultId: uint256,
    _liqAsset: address,
    _maxGreenForAsset: uint256,
    _totalGreenRemaining: uint256,
    _recipient: address,
    _caller: address,
    _shouldTransferBalance: bool,
    _a: addys.Addys,
) -> uint256:

    # NOTE: faililng gracefully in case there are many purchases at same time

    # recipient cannot be user
    if _liqUser == _recipient:
        return 0

    # this also verifies that user is in liquidation
    auc: FungibleAuction = staticcall Ledger(_a.ledger).getFungibleAuctionDuringPurchase(_liqUser, _liqVaultId, _liqAsset)
    if not auc.isActive:
        return 0

    # not within time boundaries, skip
    if block.number < auc.startBlock or block.number >= auc.endBlock:
        return 0

    # check auction config
    config: AuctionBuyConfig = staticcall MissionControl(_a.missionControl).getAuctionBuyConfig(_liqAsset, _recipient)
    if not config.canBuyInAuctionGeneral or not config.canBuyInAuctionAsset or not config.isUserAllowed:
        return 0

    # make sure caller can deposit to recipient
    if _recipient != _caller and not config.canAnyoneDeposit:
        assert staticcall Teller(_a.teller).isUnderscoreWalletOwner(_recipient, _caller, _a.missionControl) # dev: not allowed to deposit for user

    # finalize green amount
    availGreen: uint256 = min(_totalGreenRemaining, staticcall IERC20(_a.greenToken).balanceOf(self))
    greenAmount: uint256 = min(_maxGreenForAsset, availGreen)
    if greenAmount == 0:
        return 0

    # calculate discount
    auctionProgress: uint256 = (block.number - auc.startBlock) * HUNDRED_PERCENT // (auc.endBlock - auc.startBlock)
    discount: uint256 = self._calculateAuctionDiscount(auctionProgress, auc.startDiscount, auc.maxDiscount)

    # get vault addr
    liqVaultAddr: address = staticcall VaultBook(_a.vaultBook).getAddr(_liqVaultId)
    if liqVaultAddr == empty(address):
        return 0

    # max collateral usd value (to take from liq user)
    maxCollateralUsdValue: uint256 = greenAmount * HUNDRED_PERCENT // (HUNDRED_PERCENT - discount)

    # transfer collateral to buyer
    collateralUsdValueSent: uint256 = 0
    collateralAmountSent: uint256 = 0
    isPositionDepleted: bool = False
    shouldGoToNextAsset: bool = False
    collateralUsdValueSent, collateralAmountSent, isPositionDepleted, shouldGoToNextAsset = self._transferCollateral(_liqUser, _recipient, _liqVaultId, liqVaultAddr, _liqAsset, _shouldTransferBalance, maxCollateralUsdValue, _a)
    if collateralUsdValueSent == 0 or collateralAmountSent == 0:
        return 0

    # pay green amount, pay back debt
    greenRequired: uint256 = collateralUsdValueSent * (HUNDRED_PERCENT - discount) // HUNDRED_PERCENT
    greenSpent: uint256 = min(greenRequired, greenAmount)
    assert extcall IERC20(_a.greenToken).transfer(_a.creditEngine, greenSpent, default_return_value=True) # dev: could not transfer
    assert self._isPaymentCloseEnough(greenRequired, greenSpent) # dev: amounts do not match up
    hasGoodDebtHealth: bool = extcall CreditEngine(_a.creditEngine).repayDuringAuctionPurchase(_liqUser, greenSpent, _a)

    # disable auction (if depleted)
    if isPositionDepleted and staticcall Ledger(_a.ledger).hasFungibleAuction(_liqUser, _liqVaultId, _liqAsset):
        extcall Ledger(_a.ledger).removeFungibleAuction(_liqUser, _liqVaultId, _liqAsset)

    log FungAuctionPurchased(
        liqUser=_liqUser,
        liqVaultId=_liqVaultId,
        liqAsset=_liqAsset,
        greenSpent=greenSpent,
        recipient=_recipient,
        caller=_caller,
        collateralAmountSent=collateralAmountSent,
        collateralUsdValueSent=collateralUsdValueSent,
        isPositionDepleted=isPositionDepleted,
        hasGoodDebtHealth=hasGoodDebtHealth,
    )
    return greenSpent


@pure
@internal
def _calculateAuctionDiscount(_progress: uint256, _startDiscount: uint256, _maxDiscount: uint256) -> uint256:
    if _progress == 0 or _startDiscount == _maxDiscount:
        return _startDiscount
    discountRange: uint256 = _maxDiscount - _startDiscount
    adjustment: uint256 =  _progress * discountRange // HUNDRED_PERCENT
    return _startDiscount + adjustment


#############
# Utilities #
#############


# transfer collateral


@internal
def _transferCollateral(
    _fromUser: address,
    _toUser: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _shouldTransferBalance: bool,
    _targetUsdValue: uint256,
    _a: addys.Addys,
) -> (uint256, uint256, bool, bool):
    maxAssetAmount: uint256 = self._getAssetAmount(_asset, _targetUsdValue, _a.greenToken, _a.savingsGreen, _a.priceDesk)
    if maxAssetAmount == 0:
        return 0, 0, False, True # skip if cannot get price for this asset

    amountSent: uint256 = 0
    isPositionDepleted: bool = False

    # transfer balance within vault
    if _shouldTransferBalance:
        amountSent, isPositionDepleted = extcall Vault(_vaultAddr).transferBalanceWithinVault(_asset, _fromUser, _toUser, maxAssetAmount, _a)
        extcall Ledger(_a.ledger).addVaultToUser(_toUser, _vaultId)
        extcall LootBox(_a.lootbox).updateDepositPoints(_toUser, _vaultId, _vaultAddr, _asset, _a)

    # withdraw and transfer to recipient
    else:
        amountSent, isPositionDepleted = extcall Vault(_vaultAddr).withdrawTokensFromVault(_fromUser, _asset, maxAssetAmount, _toUser, _a)

    usdValue: uint256 = amountSent * _targetUsdValue // maxAssetAmount
    return usdValue, amountSent, isPositionDepleted, isPositionDepleted


@view
@internal
def _getAssetAmount(
    _asset: address,
    _targetUsdValue: uint256,
    _greenToken: address,
    _savingsGreen: address,
    _priceDesk: address,
) -> uint256:
    amount: uint256 = 0
    if _asset == _greenToken:
        amount = _targetUsdValue
    elif _asset == _savingsGreen:
        amount = staticcall IERC4626(_savingsGreen).convertToShares(_targetUsdValue)
    else:
        amount = staticcall PriceDesk(_priceDesk).getAssetAmount(_asset, _targetUsdValue, True)
    return amount


# green handling


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

    if _wantsSavingsGreen and amount > 10 ** 9: # small dust will fail
        assert extcall IERC20(_greenToken).approve(_savingsGreen, amount, default_return_value=True) # dev: green approval failed
        extcall IERC4626(_savingsGreen).deposit(amount, _recipient)
        assert extcall IERC20(_greenToken).approve(_savingsGreen, 0, default_return_value=True) # dev: green approval failed

    else:
        assert extcall IERC20(_greenToken).transfer(_recipient, amount, default_return_value=True) # dev: green transfer failed


# is payment close enough


@pure
@internal
def _isPaymentCloseEnough(_requestedAmount: uint256, _actualAmount: uint256) -> bool:
    # An extra safety check to make sure what was paid was actually close-ish to what was requested
    buffer: uint256 = _requestedAmount * ONE_PERCENT // HUNDRED_PERCENT
    upperBound: uint256 = _requestedAmount + buffer
    lowerBound: uint256 = _requestedAmount - buffer
    return upperBound >= _actualAmount and _actualAmount >= lowerBound


# calc amount of debt to repay


@view
@external
def calcAmountOfDebtToRepayDuringLiq(_user: address) -> uint256:
    a: addys.Addys = addys._getAddys()
    config: GenLiqConfig = staticcall MissionControl(a.missionControl).getGenLiqConfig()

    # user debt
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    na: uint256 = 0
    userDebt, bt, na = staticcall CreditEngine(a.creditEngine).getLatestUserDebtAndTerms(_user, True, a)
    
    # No debt to repay
    if userDebt.amount == 0:
        return 0

    # liquidation fees
    totalLiqFees: uint256 = userDebt.amount * bt.debtTerms.liqFee // HUNDRED_PERCENT
    liqFeeRatio: uint256 = bt.debtTerms.liqFee

    # keeper fee (for liquidator)
    keeperFee: uint256 = max(config.minKeeperFee, userDebt.amount * config.keeperFeeRatio // HUNDRED_PERCENT)
    if keeperFee != 0 and config.maxKeeperFee != 0:
        keeperFee = min(keeperFee, config.maxKeeperFee)
    if keeperFee != 0:
        totalLiqFees += keeperFee
        liqFeeRatio = totalLiqFees * HUNDRED_PERCENT // userDebt.amount

    # calc amount of debt to repay using unified formula
    targetLtv: uint256 = bt.debtTerms.ltv * (HUNDRED_PERCENT - config.ltvPaybackBuffer) // HUNDRED_PERCENT
    return self._calcTargetRepayAmount(userDebt.amount, bt.collateralVal, targetLtv, liqFeeRatio)


@pure
@internal
def _calcTargetRepayAmount(
    _debtAmount: uint256,
    _collateralValue: uint256,
    _targetLtv: uint256,
    _liqFeeRatio: uint256,
) -> uint256:
    """
    Calculate the optimal debt repay amount to restore user to target LTV.

    UNIFIED FORMULA FOR ALL LIQUIDATION TYPES
    This function uses a single mathematical formula that works for both:
    1. Stability pool swaps (where liquidation fees come from collateral-repay difference)
    2. Claimable GREEN liquidations (where fees are added to debt)

    MATHEMATICAL DERIVATION:
    Goal: (newDebt) / (newCollateral) = targetLTV

    For stability pool swaps:
    - newDebt = originalDebt - repayAmount  
    - newCollateral = originalCollateral - collateralTaken
    - repayAmount = collateralTaken * (1 - liqFeeRatio)

    Solving: R = (D - T*C) * (1-F) / (1 - F - T)
    Where:
    - R = repayAmount (what we solve for)
    - D = _debtAmount  
    - C = _collateralValue
    - T = _targetLtv
    - F = _liqFeeRatio

    CONSERVATIVE NATURE:
    This formula is conservative for claimable GREEN liquidations, meaning it may 
    repay slightly more debt than strictly necessary. This is INTENTIONAL because:
    - It guarantees debt health restoration in all cases
    - Over-repayment is safe (just makes user "too healthy")
    - Under-repayment is dangerous (triggers unnecessary auctions)

    TRADE-OFFS:
    ✅ Simple: One formula for all liquidation types
    ✅ Safe: Guarantees debt health restoration  
    ✅ Robust: Works for future liquidation mechanisms
    ❌ Slightly over-conservative for claimable GREEN edge cases

    PARAMETERS:
    @param _debtAmount: User's current debt amount
    @param _collateralValue: User's current collateral value in USD
    @param _targetLtv: Target LTV to achieve (e.g., 49% for 50% max with 1% buffer)
    @param _liqFeeRatio: Total liquidation fee ratio (liquidation fee + keeper fee)

    @return: Amount of debt to repay to reach target LTV
    """

    if _targetLtv == 0:
        return _debtAmount # repay everything to achieve 0% LTV

    # calculate denominator: (1 - F - T)
    if HUNDRED_PERCENT <= _liqFeeRatio + _targetLtv:
        return _debtAmount # edge case: F + T >= 100%, need full repayment

    denominator: uint256 = HUNDRED_PERCENT - _liqFeeRatio - _targetLtv
    if denominator == 0:
        return _debtAmount

    # calculate numerator: (D - T*C) * (1-F)
    oneMinusF: uint256 = HUNDRED_PERCENT - _liqFeeRatio
    debtValue: uint256 = _debtAmount * HUNDRED_PERCENT  
    targetDebtValue: uint256 = _targetLtv * _collateralValue

    # check if already at target LTV
    if debtValue <= targetDebtValue:
        return 0

    # calculate numerator: (D*100% - T*C) * (1-F)
    numerator: uint256 = (debtValue - targetDebtValue) * oneMinusF

    # calculate repay amount: R = numerator / (denominator * HUNDRED_PERCENT)
    return numerator // (denominator * HUNDRED_PERCENT)


#########
# Cache #
#########


@view
@internal
def _getAssetLiqConfig(_asset: address, _missionControl: address) -> (AssetLiqConfig, bool):
    config: AssetLiqConfig = self.assetLiqConfig[_asset]
    if config.hasConfig:
        return config, True
    return staticcall MissionControl(_missionControl).getAssetLiqConfig(_asset), False


@view
@internal
def _getVaultAddr(_vaultId: uint256, _vaultBook: address) -> (address, bool):
    vaultAddr: address = self.vaultAddrs[_vaultId]
    if vaultAddr != empty(address):
        return vaultAddr, True
    return staticcall VaultBook(_vaultBook).getAddr(_vaultId), False


@internal
def _saveLiqAssetForAuction(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address):
    nextId: uint256 = self.numUserAssetsForAuction[_user]
    self.userAssetForAuction[_user][nextId] = VaultData(vaultId=_vaultId, vaultAddr=_vaultAddr, asset=_asset)
    self.numUserAssetsForAuction[_user] = nextId + 1


##       ####  #######  ##     ## #### ########     ###    ######## ####  #######  ##    ## 
##        ##  ##     ## ##     ##  ##  ##     ##   ## ##      ##     ##  ##     ## ###   ## 
##        ##  ##     ## ##     ##  ##  ##     ##  ##   ##     ##     ##  ##     ## ####  ## 
##        ##  ##     ## ##     ##  ##  ##     ## ##     ##    ##     ##  ##     ## ## ## ## 
##        ##  ##  ## ## ##     ##  ##  ##     ## #########    ##     ##  ##     ## ##  #### 
##        ##  ##    ##  ##     ##  ##  ##     ## ##     ##    ##     ##  ##     ## ##   ### 
######## ####  ##### ##  #######  #### ########  ##     ##    ##    ####  #######  ##    ##