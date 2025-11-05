#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3

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

interface MissionControl:
    def userDelegation(_user: address, _caller: address) -> cs.ActionDelegation: view
    def getAssetLiqConfig(_asset: address) -> AssetLiqConfig: view
    def getGenLiqConfig() -> GenLiqConfig: view
    def getDebtTerms(_asset: address) -> cs.DebtTerms: view
    def underscoreRegistry() -> address: view

interface CreditEngine:
    def repayFromDept(_user: address, _userDebt: UserDebt, _repayValue: uint256, _newInterest: uint256, _numUserVaults: uint256, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def getLatestUserDebtAndTerms(_user: address, _shouldRaise: bool, _a: addys.Addys = empty(addys.Addys)) -> (UserDebt, UserBorrowTerms, uint256): view
    def getUserBorrowTerms(_user: address, _shouldRaise: bool, _skipVaultId: uint256 = 0, _skipAsset: address = empty(address), _a: addys.Addys = empty(addys.Addys)) -> UserBorrowTerms: view

interface Ledger:
    def isParticipatingInVault(_user: address, _vaultId: uint256) -> bool: view
    def userVaults(_user: address, _index: uint256) -> uint256: view
    def numUserVaults(_user: address) -> uint256: view

interface PriceDesk:
    def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256: view
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface Registry:
    def getAddr(_vaultId: uint256) -> address: view
    def isValidAddr(_addr: address) -> bool: view

interface AuctionHouse:
    def withdrawTokensFromVault(_user: address, _asset: address, _amount: uint256, _recipient: address, _vaultAddr: address, _a: addys.Addys) -> (uint256, bool): nonpayable

interface VaultRegistry:
    def isEarnVault(_vaultAddr: address) -> bool: view

interface GreenToken:
    def burn(_amount: uint256) -> bool: nonpayable

struct DeleverageUserRequest:
    user: address
    targetRepayAmount: uint256

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

struct VaultData:
    vaultId: uint256
    vaultAddr: address
    asset: address

struct UserBorrowTerms:
    collateralVal: uint256
    totalMaxDebt: uint256
    debtTerms: cs.DebtTerms
    lowestLtv: uint256
    highestLtv: uint256

struct UserDebt:
    amount: uint256
    principal: uint256
    debtTerms: cs.DebtTerms
    lastTimestamp: uint256
    inLiquidation: bool

event DeleverageUser:
    user: indexed(address)
    caller: indexed(address)
    targetRepayAmount: uint256
    repaidAmount: uint256
    hasGoodDebtHealth: bool

event StabAssetBurntDuringDeleverage:
    user: indexed(address)
    vaultId: uint256
    stabAsset: indexed(address)
    amountBurned: uint256
    usdValue: uint256
    isDepleted: bool

event EndaomentTransferDuringDeleverage:
    user: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    amountSent: uint256
    usdValue: uint256
    isDepleted: bool

# cache
vaultAddrs: transient(HashMap[uint256, address]) # vaultId -> vaultAddr
assetLiqConfig: transient(HashMap[address, AssetLiqConfig]) # asset -> config
didHandleAsset: transient(HashMap[address, HashMap[uint256, HashMap[address, bool]]]) # user -> vaultId -> asset -> did handle
didHandleVaultId: transient(HashMap[address, HashMap[uint256, bool]]) # user -> vaultId -> did handle

UNDERSCORE_LEGOBOOK_ID: constant(uint256) = 3
UNDERSCORE_VAULT_REGISTRY_ID: constant(uint256) = 10
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
ONE_PERCENT: constant(uint256) = 1_00 # 1.00%
PRIORITY_LIQ_VAULT_DATA: constant(uint256) = 20
MAX_STAB_VAULT_DATA: constant(uint256) = 10
MAX_DELEVERAGE_USERS: constant(uint256) = 25


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no special permissions needed


################
# Entry Points #
################


# single user


@external
def deleverageUser(
    _user: address,
    _caller: address,
    _targetRepayAmount: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)
    config: GenLiqConfig = staticcall MissionControl(a.missionControl).getGenLiqConfig()
    repaidAmount: uint256 = self._deleverageUser(_user, _caller, _targetRepayAmount, config, a)
    assert repaidAmount != 0 # dev: cannot deleverage
    return repaidAmount


# many users


@external
def deleverageManyUsers(
    _users: DynArray[DeleverageUserRequest, MAX_DELEVERAGE_USERS],
    _caller: address,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)
    config: GenLiqConfig = staticcall MissionControl(a.missionControl).getGenLiqConfig()

    totalRepaidAmount: uint256 = 0
    numUsers: uint256 = 0
    for u: DeleverageUserRequest in _users:
        repaidAmount: uint256 = self._deleverageUser(u.user, _caller, u.targetRepayAmount, config, a)
        if repaidAmount != 0:
            totalRepaidAmount += repaidAmount
            numUsers += 1

    assert numUsers != 0 # dev: nobody deleveraged
    return totalRepaidAmount


#################
# Internal Core #
#################


@internal
def _deleverageUser(
    _user: address,
    _caller: address,
    _targetRepayAmount: uint256,
    _config: GenLiqConfig,
    _a: addys.Addys,
) -> uint256:

    # check perms -- must also be able to borrow
    if _user != _caller:
        delegation: cs.ActionDelegation = staticcall MissionControl(_a.missionControl).userDelegation(_user, _caller)
        if not delegation.canBorrow:
            return 0
    
    # get latest user debt
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    newInterest: uint256 = 0
    userDebt, bt, newInterest = staticcall CreditEngine(_a.creditEngine).getLatestUserDebtAndTerms(_user, True, _a)
    if userDebt.amount == 0:
        return 0

    # finalize target repay amount
    targetRepayAmount: uint256 = min(_targetRepayAmount, userDebt.amount)
    if targetRepayAmount == 0:
        targetRepayAmount = userDebt.amount # maximum possible

    # perform deleverage phases
    repaidAmount: uint256 = self._performDeleveragePhases(_user, targetRepayAmount, _config.priorityStabVaults, _config.priorityLiqAssetVaults, _a)
    if repaidAmount == 0:
        return 0

    # repay debt
    repaidAmount = min(repaidAmount, userDebt.amount)
    hasGoodDebtHealth: bool = extcall CreditEngine(_a.creditEngine).repayFromDept(_user, userDebt, repaidAmount, newInterest, 0, _a)

    log DeleverageUser(
        user=_user,
        caller=_caller,
        targetRepayAmount=targetRepayAmount,
        repaidAmount=repaidAmount,
        hasGoodDebtHealth=hasGoodDebtHealth,
    )
    return repaidAmount


@internal
def _performDeleveragePhases(
    _user: address,
    _targetRepayAmount: uint256,
    _priorityStabVaults: DynArray[VaultData, MAX_STAB_VAULT_DATA],
    _priorityLiqAssetVaults: DynArray[VaultData, PRIORITY_LIQ_VAULT_DATA],
    _a: addys.Addys,
) -> uint256:
    remainingToRepay: uint256 = _targetRepayAmount

    # PHASE 1 -- look at stability pool assets first

    if len(_priorityStabVaults) != 0:
        for stabPool: VaultData in _priorityStabVaults:
            if remainingToRepay == 0:
                break

            if not staticcall Ledger(_a.ledger).isParticipatingInVault(_user, stabPool.vaultId):
                continue

            remainingToRepay = self._iterateThruAssetsWithinVault(_user, stabPool.vaultId, stabPool.vaultAddr, remainingToRepay, _a)
            if self.vaultAddrs[stabPool.vaultId] == empty(address):
                self.vaultAddrs[stabPool.vaultId] = stabPool.vaultAddr # cache

    # PHASE 2 -- Go thru priority liq assets (set in mission control)

    if len(_priorityLiqAssetVaults) != 0 and remainingToRepay != 0:
        for pData: VaultData in _priorityLiqAssetVaults:
            if remainingToRepay == 0:
                break

            if not staticcall Vault(pData.vaultAddr).doesUserHaveBalance(_user, pData.asset):
                continue

            remainingToRepay = self._handleSpecificAsset(_user, pData.vaultId, pData.vaultAddr, pData.asset, remainingToRepay, _a)
            if self.vaultAddrs[pData.vaultId] == empty(address):
                self.vaultAddrs[pData.vaultId] = pData.vaultAddr # cache

    # PHASE 3 -- Go thru user's vaults (top to bottom as saved in ledger / vaults)

    if remainingToRepay != 0:
        remainingToRepay = self._iterateThruAllUserVaults(_user, remainingToRepay, _a)

    return _targetRepayAmount - remainingToRepay


###################
# Vaults / Assets #
###################


# all user vaults


@internal
def _iterateThruAllUserVaults(_user: address, _remainingToRepay: uint256, _a: addys.Addys) -> uint256:
    numUserVaults: uint256 = staticcall Ledger(_a.ledger).numUserVaults(_user)
    if numUserVaults == 0:
        return _remainingToRepay

    remainingToRepay: uint256 = _remainingToRepay
    for i: uint256 in range(1, numUserVaults, bound=max_value(uint256)):
        if remainingToRepay == 0:
            break

        vaultId: uint256 = staticcall Ledger(_a.ledger).userVaults(_user, i)

        # get vault address
        vaultAddr: address = empty(address)
        isVaultAddrCached: bool = False
        vaultAddr, isVaultAddrCached = self._getVaultAddr(vaultId, _a.vaultBook)
        if vaultAddr == empty(address):
            continue

        # cache vault addr
        if not isVaultAddrCached:
            self.vaultAddrs[vaultId] = vaultAddr

        remainingToRepay = self._iterateThruAssetsWithinVault(_user, vaultId, vaultAddr, remainingToRepay, _a)

    return remainingToRepay


# all assets within vault


@internal
def _iterateThruAssetsWithinVault(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _remainingToRepay: uint256,
    _a: addys.Addys,
) -> uint256:

    # check if we've already handled this vault
    if self.didHandleVaultId[_user][_vaultId]:
        return _remainingToRepay
    self.didHandleVaultId[_user][_vaultId] = True

    # no assets in vault, skip
    numUserAssets: uint256 = staticcall Vault(_vaultAddr).numUserAssets(_user)
    if numUserAssets == 0:
        return _remainingToRepay

    # totals
    remainingToRepay: uint256 = _remainingToRepay
    for y: uint256 in range(1, numUserAssets, bound=max_value(uint256)):
        if remainingToRepay == 0:
            break

        # check if user still has balance in this asset
        asset: address = empty(address)
        hasBalance: bool = False
        asset, hasBalance = staticcall Vault(_vaultAddr).getUserAssetAtIndexAndHasBalance(_user, y)
        if asset == empty(address) or not hasBalance:
            continue

        # handle specific liq asset
        remainingToRepay = self._handleSpecificAsset(_user, _vaultId, _vaultAddr, asset, remainingToRepay, _a)

    return remainingToRepay


# specific asset


@internal
def _handleSpecificAsset(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _remainingToRepay: uint256,
    _a: addys.Addys,
) -> uint256:

    # check if we've already handled this liq asset (cache for next time)
    if self.didHandleAsset[_user][_vaultId][_asset]:
        return _remainingToRepay
    self.didHandleAsset[_user][_vaultId][_asset] = True

    # asset liq config
    config: AssetLiqConfig = empty(AssetLiqConfig)
    isConfigCached: bool = False
    config, isConfigCached = self._getAssetLiqConfig(_asset, _a.missionControl)
    if not isConfigCached:
        self.assetLiqConfig[_asset] = config

    # burn as payment (GREEN, sGREEN)
    if config.shouldBurnAsPayment and _asset in [_a.greenToken, _a.savingsGreen]:
        return self._burnStabPoolAsset(_user, _vaultId, _vaultAddr, _asset, _remainingToRepay, _a)

    # endaoment wants this asset (other stablecoins)
    if config.shouldTransferToEndaoment:
        return self._transferToEndaoment(_user, _vaultId, _vaultAddr, _asset, _remainingToRepay, _a)

    return _remainingToRepay


#########################
# Stability Pool Assets #
#########################


@internal
def _burnStabPoolAsset(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _stabAsset: address,
    _remainingToRepay: uint256,
    _a: addys.Addys,
) -> uint256:
    usdValue: uint256 = 0
    amountReceived: uint256 = 0
    isPositionDepleted: bool = False
    usdValue, amountReceived, isPositionDepleted = self._transferCollateral(_user, self, _vaultAddr, _stabAsset, _remainingToRepay, _a)
    if usdValue == 0:
        return _remainingToRepay

    # burn stab asset
    if _stabAsset == _a.savingsGreen:
        greenAmount: uint256 = extcall IERC4626(_a.savingsGreen).redeem(amountReceived, self, self) # dev: savings green redeem failed
        assert extcall GreenToken(_a.greenToken).burn(greenAmount) # dev: failed to burn green
    else:
        assert extcall GreenToken(_a.greenToken).burn(amountReceived) # dev: failed to burn green

    log StabAssetBurntDuringDeleverage(
        user=_user,
        vaultId=_vaultId,
        stabAsset=_stabAsset,
        amountBurned=amountReceived,
        usdValue=usdValue,
        isDepleted=isPositionDepleted,
    )
    return _remainingToRepay - min(usdValue, _remainingToRepay)


######################
# Endaoment Transfer #
######################


@internal
def _transferToEndaoment(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _remainingToRepay: uint256,
    _a: addys.Addys,
) -> uint256:
    collateralUsdValueSent: uint256 = 0
    collateralAmountSent: uint256 = 0
    isPositionDepleted: bool = False
    collateralUsdValueSent, collateralAmountSent, isPositionDepleted = self._transferCollateral(_user, _a.endaoment, _vaultAddr, _asset, _remainingToRepay, _a)
    if collateralUsdValueSent == 0:
        return _remainingToRepay

    log EndaomentTransferDuringDeleverage(
        user=_user,
        vaultId=_vaultId,
        asset=_asset,
        amountSent=collateralAmountSent,
        usdValue=collateralUsdValueSent,
        isDepleted=isPositionDepleted
    )
    return _remainingToRepay - min(collateralUsdValueSent, _remainingToRepay)


#############
# Utilities #
#############


# transfer collateral


@internal
def _transferCollateral(
    _fromUser: address,
    _toUser: address,
    _vaultAddr: address,
    _asset: address,
    _targetUsdValue: uint256,
    _a: addys.Addys,
) -> (uint256, uint256, bool):
    maxAssetAmount: uint256 = self._getMaxAssetAmount(_asset, _targetUsdValue, _a.greenToken, _a.savingsGreen, _a.priceDesk)
    if maxAssetAmount == 0:
        return 0, 0, False

    # withdraw and transfer to recipient -- AuctionHouse has permissions to perform this
    amountSent: uint256 = 0
    isPositionDepleted: bool = False
    amountSent, isPositionDepleted = extcall AuctionHouse(_a.auctionHouse).withdrawTokensFromVault(_fromUser, _asset, maxAssetAmount, _toUser, _vaultAddr, _a)

    usdValue: uint256 = _targetUsdValue * amountSent // maxAssetAmount
    return usdValue, amountSent, isPositionDepleted


# get asset amount


@view
@internal
def _getMaxAssetAmount(
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


# get deleverage info


@view
@external
def getDeleverageInfo(_user: address) -> (uint256, uint256):
    return self._getDeleverageInfo(_user, addys._getAddys())


@view
@internal
def _getDeleverageInfo(_user: address, _a: addys.Addys) -> (uint256, uint256):
    maxDeleveragableUsd: uint256 = 0
    ltvSum: uint256 = 0 

    # number of user vaults
    numUserVaults: uint256 = staticcall Ledger(_a.ledger).numUserVaults(_user)
    if numUserVaults == 0:
        return 0, 0

    # iterate through user vaults
    for i: uint256 in range(1, numUserVaults, bound=max_value(uint256)):
        vaultId: uint256 = staticcall Ledger(_a.ledger).userVaults(_user, i)
        vaultAddr: address = staticcall Registry(_a.vaultBook).getAddr(vaultId)
        if vaultAddr == empty(address):
            continue

        # number of assets in vault
        numUserAssets: uint256 = staticcall Vault(vaultAddr).numUserAssets(_user)
        if numUserAssets == 0:
            continue

        # iterate through assets
        for y: uint256 in range(1, numUserAssets, bound=max_value(uint256)):
            asset: address = empty(address)
            hasBalance: bool = False
            asset, hasBalance = staticcall Vault(vaultAddr).getUserAssetAtIndexAndHasBalance(_user, y)
            if asset == empty(address) or not hasBalance:
                continue

            # get actual amount from vault
            amount: uint256 = staticcall Vault(vaultAddr).getTotalAmountForUser(_user, asset)
            if amount == 0:
                continue

            # check if asset is deleveragable
            assetLiqConfig: AssetLiqConfig = staticcall MissionControl(_a.missionControl).getAssetLiqConfig(asset)
            if not assetLiqConfig.shouldBurnAsPayment and not assetLiqConfig.shouldTransferToEndaoment:
                continue

            # usd value
            usdValue: uint256 = staticcall PriceDesk(_a.priceDesk).getUsdValue(asset, amount, True)
            if usdValue == 0:
                continue

            maxDeleveragableUsd += usdValue

            # get asset LTV for weighted calculation
            debtTerms: cs.DebtTerms = staticcall MissionControl(_a.missionControl).getDebtTerms(asset)
            ltvSum += usdValue * debtTerms.ltv

    # calculate effective weighted LTV
    effectiveWeightedLtv: uint256 = 0
    if maxDeleveragableUsd != 0:
        effectiveWeightedLtv = ltvSum // maxDeleveragableUsd

    return maxDeleveragableUsd, effectiveWeightedLtv


# deleverage if needed for withdrawal


@external
def deleverageForWithdrawal(_user: address, _vaultId: uint256, _asset: address, _amount: uint256) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()

    if not addys._isValidRipeAddr(msg.sender):
        assert self._isUnderscoreAddr(msg.sender, a.missionControl) # dev: no perms

    # get current user state
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    na: uint256 = 0
    userDebt, bt, na = staticcall CreditEngine(a.creditEngine).getLatestUserDebtAndTerms(_user, True, a)
    if userDebt.amount == 0:
        return False

    # asset information
    vaultAddr: address = staticcall Registry(a.vaultBook).getAddr(_vaultId)
    userBalance: uint256 = staticcall Vault(vaultAddr).getTotalAmountForUser(_user, _asset)
    userUsdValue: uint256 = staticcall PriceDesk(a.priceDesk).getUsdValue(_asset, userBalance, True)

    # calculate withdraw usd value
    withdrawUsdValue: uint256 = userUsdValue
    if _amount < userBalance:
        withdrawUsdValue = userUsdValue * _amount // userBalance

    # asset debt terms
    assetDebtTerms: cs.DebtTerms = staticcall MissionControl(a.missionControl).getDebtTerms(_asset)
    if assetDebtTerms.ltv == 0:
        return False # 0% LTV means asset doesn't affect borrowing capacity

    # calculate lost capacity from withdrawal
    lostCapacity: uint256 = withdrawUsdValue * assetDebtTerms.ltv // HUNDRED_PERCENT
    if lostCapacity == 0:
        return False # if no capacity lost, no need to deleverage

    # get deleverage info (maxDeleveragable amount and effective weighted LTV)
    maxDeleveragable: uint256 = 0
    effectiveLtv: uint256 = 0
    maxDeleveragable, effectiveLtv = self._getDeleverageInfo(_user, a)
    if maxDeleveragable == 0:
        return False # no deleveragable assets

    # calculate required repayment to maintain utilization ratio
    # Formula: requiredRepayment = (debt × lostCapacity) / (capacity - debt × effectiveLtv)
    numerator: uint256 = userDebt.amount * lostCapacity
    denominator: uint256 = bt.totalMaxDebt - (userDebt.amount * effectiveLtv // HUNDRED_PERCENT)
    if denominator == 0:
        return False # edge case: capacity exactly equals debt × effectiveLtv

    requiredRepayment: uint256 = numerator // denominator
    if requiredRepayment == 0:
        return False

    # apply 1% buffer to be more conservative
    requiredRepayment = requiredRepayment * (HUNDRED_PERCENT + ONE_PERCENT) // HUNDRED_PERCENT

    # cap at max deleveragable amount
    requiredRepayment = min(maxDeleveragable, requiredRepayment)

    # final cap at total debt
    requiredRepayment = min(userDebt.amount, requiredRepayment)

    # execute deleveraging
    config: GenLiqConfig = staticcall MissionControl(a.missionControl).getGenLiqConfig()
    repaidAmount: uint256 = self._deleverageUser(_user, _user, requiredRepayment, config, a)
    return repaidAmount != 0


# underscore address


@view
@internal
def _isUnderscoreAddr(_addr: address, _mc: address) -> bool:
    underscore: address = staticcall MissionControl(_mc).underscoreRegistry()
    if underscore == empty(address):
        return False

    # check if underscore vault
    vaultRegistry: address = staticcall Registry(underscore).getAddr(UNDERSCORE_VAULT_REGISTRY_ID)
    if vaultRegistry == empty(address):
        return False

    if staticcall VaultRegistry(vaultRegistry).isEarnVault(_addr):
        return True

    # check if underscore lego
    undyLegoBook: address = staticcall Registry(underscore).getAddr(UNDERSCORE_LEGOBOOK_ID)
    if undyLegoBook == empty(address):
        return False
    
    return staticcall Registry(undyLegoBook).isValidAddr(_addr)


# cache tools


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
    return staticcall Registry(_vaultBook).getAddr(_vaultId), False