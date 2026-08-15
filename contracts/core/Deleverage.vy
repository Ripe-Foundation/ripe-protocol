#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3
#pragma optimize codesize

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
from ethereum.ercs import IERC20Detailed

interface MissionControl:
    def userDelegation(_user: address, _caller: address) -> cs.ActionDelegation: view
    def getAssetLiqConfig(_asset: address) -> AssetLiqConfig: view
    def getFirstVaultIdForAsset(_asset: address) -> uint256: view
    def getDebtTerms(_asset: address) -> cs.DebtTerms: view
    def getGenLiqConfig() -> GenLiqConfig: view
    def getLtvPaybackBuffer() -> uint256: view
    def underscoreRegistry() -> address: view
    def isStabVaultId(_vaultId: uint256) -> bool: view

interface CreditEngine:
    def repayFromDept(_user: address, _userDebt: UserDebt, _repayValue: uint256, _newInterest: uint256, _numUserVaults: uint256, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def getLatestUserDebtAndTerms(_user: address, _shouldRaise: bool, _a: addys.Addys = empty(addys.Addys)) -> (UserDebt, UserBorrowTerms, uint256): view
    def getUserBorrowTerms(_user: address, _shouldRaise: bool, _skipVaultId: uint256 = 0, _skipAsset: address = empty(address), _a: addys.Addys = empty(addys.Addys)) -> UserBorrowTerms: view

interface Ledger:
    def isParticipatingInVault(_user: address, _vaultId: uint256) -> bool: view
    def userVaults(_user: address, _index: uint256) -> uint256: view
    def numUserVaults(_user: address) -> uint256: view

interface Teller:
    def depositFromTrusted(_user: address, _vaultId: uint256, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def performHousekeeping(_isHigherRisk: bool, _user: address, _shouldUpdateDebt: bool, _a: addys.Addys = empty(addys.Addys)): nonpayable

interface PriceDesk:
    def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256: view
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface VaultRegistry:
    def isBasicEarnVault(_vaultAddr: address) -> bool: view
    def isEarnVault(_vaultAddr: address) -> bool: view

interface Registry:
    def getAddr(_vaultId: uint256) -> address: view
    def isValidAddr(_addr: address) -> bool: view

interface AuctionHouse:
    def withdrawTokensFromVault(_user: address, _asset: address, _amount: uint256, _recipient: address, _vaultAddr: address, _preflightSafeConversion: bool, _a: addys.Addys) -> (uint256, bool): nonpayable

interface UnderscoreVault:
    def convertToAssetsSafe(_shares: uint256) -> uint256: view

interface EndaomentPSM:
    def getUsdcYieldPositionVaultToken() -> address: view

interface GreenToken:
    def burn(_amount: uint256) -> bool: nonpayable

interface RipeHq:
    def governance() -> address: view

struct DeleverageUserRequest:
    user: address
    targetRepayAmount: uint256

struct DeleverageAsset:
    vaultId: uint256
    asset: address
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
    hasQuarantinedAsset: bool

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
    targetRepayAmountWithBuffer: uint256
    collateralValueRepaid: uint256
    debtToClear: uint256
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

event CollateralSwapped:
    user: indexed(address)
    caller: indexed(address)
    withdrawVaultId: uint256
    withdrawAsset: indexed(address)
    withdrawAmount: uint256
    depositVaultId: uint256
    depositAsset: address
    depositAmount: uint256
    usdValue: uint256

event DeleverageUserWithVolatileAssets:
    user: indexed(address)
    repaidAmount: uint256
    hasGoodDebtHealth: bool

event MinDeleverageBpsSet:
    bps: uint256

event DeleverageBufferSet:
    bps: uint256

event DeleverageCooldownSet:
    blocks: uint256

event UnderscoreSafeSpreadBpsSet:
    bps: uint256

event DeleverageFullPayoffParamSet:
    param: uint256
    amount: uint256

lastDeleverageBlock: public(HashMap[address, uint256]) # user -> block number, only for deleverageForWithdrawal

# deleverage params
minDeleverageBps: public(uint256)
deleverageBuffer: public(uint256)
deleverageCooldown: public(uint256)
underscoreSafeSpreadBps: public(uint256)

# buffer / dust params
deleverageFullPayoffBuffer: public(uint256)
deleverageOverageBps: public(uint256)
deleverageDustThreshold: public(uint256)
deleverageDustBps: public(uint256)

# cache
vaultAddrs: transient(HashMap[uint256, address]) # vaultId -> vaultAddr
assetLiqConfig: transient(HashMap[address, AssetLiqConfig]) # asset -> config
didHandleAsset: transient(HashMap[address, HashMap[uint256, HashMap[address, bool]]]) # user -> vaultId -> asset -> did handle
didHandleVaultId: transient(HashMap[address, HashMap[uint256, bool]]) # user -> vaultId -> did handle
underscoreVaultRegistry: transient(HashMap[address, address])

UNDERSCORE_LEGOBOOK_ID: constant(uint256) = 3
UNDERSCORE_VAULT_REGISTRY_ID: constant(uint256) = 10
UNDERSCORE_LEGO_CALLER_TYPE: constant(uint256) = 1
UNDERSCORE_EARN_VAULT_CALLER_TYPE: constant(uint256) = 2
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_COOLDOWN_BLOCKS: constant(uint256) = 7_200 # ~1 day at 12s/block
MAX_UNDERSCORE_SAFE_SPREAD_BPS: constant(uint256) = 500 # 5% hard ceiling
MAX_DELEVERAGE_FULL_PAYOFF_BUFFER: constant(uint256) = 10 ** 18
MAX_DELEVERAGE_DUST_THRESHOLD: constant(uint256) = 10 ** 16
MAX_DELEVERAGE_OVERAGE_BPS: constant(uint256) = 500 # 5% hard ceiling
MAX_DELEVERAGE_DUST_BPS: constant(uint256) = 500 # 5% hard ceiling
PRIORITY_LIQ_VAULT_DATA: constant(uint256) = 20
MAX_STAB_VAULT_DATA: constant(uint256) = 10
MAX_DELEVERAGE_USERS: constant(uint256) = 25
MAX_DELEVERAGE_ASSETS: constant(uint256) = 25


@deploy
def __init__(
    _ripeHq: address,
    _minDeleverageBps: uint256,
    _deleverageBuffer: uint256,
    _deleverageCooldown: uint256,
    _underscoreSafeSpreadBps: uint256,
    _deleverageFullPayoffBuffer: uint256,
    _deleverageOverageBps: uint256,
    _deleverageDustThreshold: uint256,
    _deleverageDustBps: uint256,
):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no special permissions needed

    assert _minDeleverageBps <= HUNDRED_PERCENT # dev: invalid bps
    assert _deleverageBuffer <= HUNDRED_PERCENT # dev: invalid bps
    assert _deleverageCooldown <= MAX_COOLDOWN_BLOCKS # dev: cooldown too large
    assert _underscoreSafeSpreadBps <= MAX_UNDERSCORE_SAFE_SPREAD_BPS # dev: exceeds hard ceiling
    assert _deleverageFullPayoffBuffer <= MAX_DELEVERAGE_FULL_PAYOFF_BUFFER # dev: exceeds hard ceiling
    assert _deleverageOverageBps <= MAX_DELEVERAGE_OVERAGE_BPS # dev: exceeds hard ceiling
    assert _deleverageDustThreshold <= MAX_DELEVERAGE_DUST_THRESHOLD # dev: exceeds hard ceiling
    assert _deleverageDustBps <= MAX_DELEVERAGE_DUST_BPS # dev: exceeds hard ceiling

    self.minDeleverageBps = _minDeleverageBps
    self.deleverageBuffer = _deleverageBuffer
    self.deleverageCooldown = _deleverageCooldown
    self.underscoreSafeSpreadBps = _underscoreSafeSpreadBps
    self.deleverageFullPayoffBuffer = _deleverageFullPayoffBuffer
    self.deleverageOverageBps = _deleverageOverageBps
    self.deleverageDustThreshold = _deleverageDustThreshold
    self.deleverageDustBps = _deleverageDustBps


###################
# Main Deleverage #
###################


# many users


@external
@nonreentrant
def deleverageManyUsers(_users: DynArray[DeleverageUserRequest, MAX_DELEVERAGE_USERS], _caller: address, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only teller allowed
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)
    config: GenLiqConfig = staticcall MissionControl(a.missionControl).getGenLiqConfig()
    isTrusted: bool = addys._isValidRipeAddr(_caller)
    if not isTrusted:
        isTrusted = self._getUnderscoreAddrType(_caller, a.missionControl, False) != 0

    endaoFunds: address = addys._getEndaomentFundsAddr()
    endaomentPsm: address = addys._getEndaomentPsmAddr()
    psmYieldPositionToken: address = staticcall EndaomentPSM(endaomentPsm).getUsdcYieldPositionVaultToken()

    totalRepaidAmount: uint256 = 0
    numUsers: uint256 = 0
    for u: DeleverageUserRequest in _users:
        repaidAmount: uint256 = self._deleverageUser(u.user, _caller, isTrusted, u.targetRepayAmount, config, endaoFunds, endaomentPsm, psmYieldPositionToken, a)
        if repaidAmount != 0:
            totalRepaidAmount += repaidAmount
            numUsers += 1

    assert numUsers != 0 # dev: nobody deleveraged
    return totalRepaidAmount


# specific assets in order


@external
@nonreentrant
def deleverageWithSpecificAssets(_user: address, _assets: DynArray[DeleverageAsset, MAX_DELEVERAGE_ASSETS], _caller: address, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only teller allowed
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)
    isTrusted: bool = _user == _caller or addys._isValidRipeAddr(_caller)
    if not isTrusted:
        isTrusted = self._getUnderscoreAddrType(_caller, a.missionControl, False) != 0

    endaoFunds: address = addys._getEndaomentFundsAddr()
    endaomentPsm: address = addys._getEndaomentPsmAddr()
    psmYieldPositionToken: address = staticcall EndaomentPSM(endaomentPsm).getUsdcYieldPositionVaultToken()

    # check perms -- must also be able to borrow
    if not isTrusted:
        delegation: cs.ActionDelegation = staticcall MissionControl(a.missionControl).userDelegation(_user, _caller)
        isTrusted = delegation.canBorrow

    # must be trusted to deleverage with specific asset order
    assert isTrusted # dev: not allowed

    # get latest user debt
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    newInterest: uint256 = 0
    userDebt, bt, newInterest = staticcall CreditEngine(a.creditEngine).getLatestUserDebtAndTerms(_user, True, a)
    if userDebt.amount == 0 or bt.hasQuarantinedAsset:
        return 0

    # This tracks remaining collateral budget, not just remaining debt, once the buffer fires.
    maxTargetRepayAmount: uint256 = userDebt.amount
    targetRepayAmount: uint256 = 0
    effectiveBuffer: uint256 = 0
    useFullPayoffExtras: bool = False

    # process each asset in the specified order
    for data: DeleverageAsset in _assets:
        if maxTargetRepayAmount == 0:
            break
        if data.targetRepayAmount == 0:
            continue

        # get vault address
        vaultAddr: address = empty(address)
        isVaultAddrCached: bool = False
        vaultAddr, isVaultAddrCached = self._getVaultAddr(data.vaultId, a.vaultBook)
        if vaultAddr == empty(address):
            continue

        # cache vault addr
        if not isVaultAddrCached:
            self.vaultAddrs[data.vaultId] = vaultAddr

        # handle this specific asset
        repayForAsset: uint256 = min(maxTargetRepayAmount, data.targetRepayAmount)
        if targetRepayAmount != userDebt.amount:
            targetRepayAmount = unsafe_add(targetRepayAmount, min(unsafe_sub(userDebt.amount, targetRepayAmount), data.targetRepayAmount))
            if targetRepayAmount == userDebt.amount:
                # Owner-keyed full-payoff classification necessarily depends on
                # the configured Underscore registry being healthy even when all
                # payoff extras are zero. Governance can set that registry to
                # zero to restore Ripe-only operation only while extras stay off.
                useFullPayoffExtras = self._getUnderscoreAddrType(_user, a.missionControl, False) != UNDERSCORE_EARN_VAULT_CALLER_TYPE
            if useFullPayoffExtras:
                # Full-payoff intent lets the buffer exceed this asset's target.
                # If this asset cannot fill it, the extra budget carries to later assets.
                effectiveBuffer = self._getFullPayoffBuffer(userDebt.amount)
                maxTargetRepayAmount = unsafe_add(maxTargetRepayAmount, effectiveBuffer)
                repayForAsset = unsafe_add(repayForAsset, effectiveBuffer)
        remainingToRepayForAsset: uint256 = self._handleSpecificAsset(_user, data.vaultId, vaultAddr, data.asset, repayForAsset, False, endaoFunds, endaomentPsm, psmYieldPositionToken, a)
        # _handleSpecificAsset returns its budget unchanged or reduced, so the
        # paired unsafe subtraction remains bounded by repayForAsset.
        paidAmountForAsset: uint256 = unsafe_sub(repayForAsset, remainingToRepayForAsset)
        maxTargetRepayAmount = unsafe_sub(maxTargetRepayAmount, paidAmountForAsset)

    # Budget starts as debt and may be lifted by buffer; consumed collateral is budget minus remainder.
    totalRepaidAmount: uint256 = unsafe_sub(unsafe_add(userDebt.amount, effectiveBuffer), maxTargetRepayAmount)
    assert totalRepaidAmount != 0 # dev: no assets processed

    # Settle against the refreshed debt struct and interest. Planning above
    # (targetRepayAmount, buffer, budget) stays keyed to the pre-interaction
    # snapshot; the refreshed amount is required to equal it, so the full-payoff
    # and dust semantics are preserved.
    userDebt, newInterest = self._refreshSettlementDebt(_user, userDebt.amount, a)

    # Repay debt. This repeats the full-payoff check from the buffer branch above;
    # it relies on targetRepayAmount only moving up toward userDebt.amount in the loop.
    debtToClear: uint256 = self._getDebtToClear(useFullPayoffExtras, totalRepaidAmount, userDebt.amount)
    hasGoodDebtHealth: bool = extcall CreditEngine(a.creditEngine).repayFromDept(_user, userDebt, debtToClear, newInterest, 0, a)

    log DeleverageUser(
        user=_user,
        caller=_caller,
        targetRepayAmount=targetRepayAmount,
        targetRepayAmountWithBuffer=unsafe_add(targetRepayAmount, effectiveBuffer),
        collateralValueRepaid=totalRepaidAmount,
        debtToClear=debtToClear,
        hasGoodDebtHealth=hasGoodDebtHealth,
    )
    return debtToClear


######################
# Special Deleverage #
######################


# volatile collateral assets


@external
@nonreentrant
def deleverageWithVolAssets(_user: address, _assets: DynArray[DeleverageAsset, MAX_DELEVERAGE_ASSETS]) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()
    if not addys._isValidRipeAddr(msg.sender):
        assert addys._isSwitchboardAddr(msg.sender) # dev: no perms

    # get latest user debt
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    newInterest: uint256 = 0
    userDebt, bt, newInterest = staticcall CreditEngine(a.creditEngine).getLatestUserDebtAndTerms(_user, True, a)
    if userDebt.amount == 0 or bt.hasQuarantinedAsset:
        return 0

    maxTargetRepayAmount: uint256 = userDebt.amount
    endaoFunds: address = addys._getEndaomentFundsAddr()
    endaomentPsm: address = addys._getEndaomentPsmAddr()
    psmYieldPositionToken: address = staticcall EndaomentPSM(endaomentPsm).getUsdcYieldPositionVaultToken()

    # process each volatile asset in the specified order
    for data: DeleverageAsset in _assets:
        if maxTargetRepayAmount == 0:
            break
        if data.targetRepayAmount == 0:
            continue

        # get vault address
        vaultAddr: address = empty(address)
        isVaultAddrCached: bool = False
        vaultAddr, isVaultAddrCached = self._getVaultAddr(data.vaultId, a.vaultBook)
        if vaultAddr == empty(address):
            continue

        # cache vault addr
        if not isVaultAddrCached:
            self.vaultAddrs[data.vaultId] = vaultAddr

        # handle this volatile asset (skip stability pool & shouldTransferToEndaoment assets)
        repayForAsset: uint256 = min(maxTargetRepayAmount, data.targetRepayAmount)
        remainingToRepayForAsset: uint256 = self._handleSpecificAsset(_user, data.vaultId, vaultAddr, data.asset, repayForAsset, True, endaoFunds, endaomentPsm, psmYieldPositionToken, a)
        paidAmountForAsset: uint256 = repayForAsset - remainingToRepayForAsset
        maxTargetRepayAmount -= paidAmountForAsset

    # calculate how much we actually repaid
    totalRepaidAmount: uint256 = userDebt.amount - maxTargetRepayAmount
    assert totalRepaidAmount != 0 # dev: no volatile assets processed

    # Refresh live debt after collateral interactions; revert if the
    # amount changed. Settlement uses the refreshed struct + interest.
    userDebt, newInterest = self._refreshSettlementDebt(_user, userDebt.amount, a)

    # repay debt
    hasGoodDebtHealth: bool = extcall CreditEngine(a.creditEngine).repayFromDept(_user, userDebt, min(totalRepaidAmount, userDebt.amount), newInterest, 0, a)

    log DeleverageUserWithVolatileAssets(
        user=_user,
        repaidAmount=totalRepaidAmount,
        hasGoodDebtHealth=hasGoodDebtHealth,
    )
    return totalRepaidAmount


# collateral swap


@external
@nonreentrant
def swapCollateral(
    _user: address,
    _withdrawVaultId: uint256,
    _withdrawAsset: address,
    _depositVaultId: uint256,
    _depositAsset: address,
    _withdrawAmount: uint256 = max_value(uint256),
) -> (uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert empty(address) not in [_user, _withdrawAsset, _depositAsset] # dev: invalid assets
    assert 0 not in [_withdrawVaultId, _depositVaultId] # dev: invalid vault ids

    a: addys.Addys = addys._getAddys()
    if not addys._isValidRipeAddr(msg.sender):
        assert msg.sender == staticcall RipeHq(a.hq).governance() # dev: governance only

    # get vault addresses
    withdrawVaultAddr: address = staticcall Registry(a.vaultBook).getAddr(_withdrawVaultId)
    assert withdrawVaultAddr != empty(address) # dev: invalid withdraw vault

    depositVaultAddr: address = staticcall Registry(a.vaultBook).getAddr(_depositVaultId)
    assert depositVaultAddr != empty(address) # dev: invalid deposit vault

    # get debt terms for both assets
    withdrawAssetTerms: cs.DebtTerms = staticcall MissionControl(a.missionControl).getDebtTerms(_withdrawAsset)
    depositAssetTerms: cs.DebtTerms = staticcall MissionControl(a.missionControl).getDebtTerms(_depositAsset)

    # validate LTV: deposit asset must have >= LTV as withdraw asset
    assert depositAssetTerms.ltv >= withdrawAssetTerms.ltv # dev: deposit asset LTV too low

    # withdraw collateral from user's vault, transfer to governance (msg.sender)
    withdrawnAmount: uint256 = 0
    isPositionDepleted: bool = False
    withdrawnAmount, isPositionDepleted = extcall AuctionHouse(a.auctionHouse).withdrawTokensFromVault(
        _user,
        _withdrawAsset,
        _withdrawAmount,
        msg.sender, # recipient is governance
        withdrawVaultAddr,
        False,
        a,
    )
    assert withdrawnAmount != 0 # dev: no collateral withdrawn

    # calculate USD value of withdrawn amount
    usdValue: uint256 = staticcall PriceDesk(a.priceDesk).getUsdValue(_withdrawAsset, withdrawnAmount, True)
    assert usdValue != 0 # dev: invalid USD value

    # calculate deposit amount based on USD value
    depositAmount: uint256 = staticcall PriceDesk(a.priceDesk).getAssetAmount(_depositAsset, usdValue, True)
    assert depositAmount != 0 # dev: invalid deposit amount

    # transfer new collateral from governance to this contract
    assert extcall IERC20(_depositAsset).transferFrom(msg.sender, self, depositAmount) # dev: transferFrom failed

    # approve Teller to spend tokens and deposit into user's vault
    assert extcall IERC20(_depositAsset).approve(a.teller, depositAmount) # dev: approve failed
    extcall Teller(a.teller).depositFromTrusted(_user, _depositVaultId, _depositAsset, depositAmount, 0, a)
    assert extcall IERC20(_depositAsset).approve(a.teller, 0) # dev: approve failed

    # perform house keeping
    extcall Teller(a.teller).performHousekeeping(False, _user, True, a)

    log CollateralSwapped(
        user=_user,
        caller=msg.sender,
        withdrawVaultId=_withdrawVaultId,
        withdrawAsset=_withdrawAsset,
        withdrawAmount=withdrawnAmount,
        depositVaultId=_depositVaultId,
        depositAsset=_depositAsset,
        depositAmount=depositAmount,
        usdValue=usdValue,
    )
    return withdrawnAmount, depositAmount


# underscore leverage vaults


@external
@nonreentrant
def deleverageForWithdrawal(_user: address, _vaultId: uint256, _asset: address, _amount: uint256) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys()

    isTrustedCaller: bool = addys._isValidRipeAddr(msg.sender)
    if not isTrustedCaller:
        assert self._getUnderscoreAddrType(msg.sender, a.missionControl, False) != 0 # dev: no perms
        isTrustedCaller = msg.sender == _user

    # get current user state
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    na: uint256 = 0
    userDebt, bt, na = staticcall CreditEngine(a.creditEngine).getLatestUserDebtAndTerms(_user, True, a)
    if userDebt.amount == 0 or bt.hasQuarantinedAsset:
        return False

    vaultId: uint256 = _vaultId
    if _vaultId == 0:
        vaultId = staticcall MissionControl(a.missionControl).getFirstVaultIdForAsset(_asset)

    # asset information
    vaultAddr: address = staticcall Registry(a.vaultBook).getAddr(vaultId)
    userBalance: uint256 = staticcall Vault(vaultAddr).getTotalAmountForUser(_user, _asset)
    userUsdValue: uint256 = staticcall PriceDesk(a.priceDesk).getUsdValue(_asset, userBalance, True)

    # calculate withdraw usd value
    withdrawUsdValue: uint256 = userUsdValue
    if _amount < userBalance:
        withdrawUsdValue = userUsdValue * _amount // userBalance

    # projected collateral after withdrawal (lazy-cached for near-redemption bypass checks)
    projectedCollateralVal: uint256 = bt.collateralVal - withdrawUsdValue if bt.collateralVal > withdrawUsdValue else 0
    didCheckNearRedemption: bool = False
    isNearRedemption: bool = False

    # cooldown: skip if recently deleveraged, unless near redemption after withdrawal
    # NOTE: uses strict `>` (not `>=`) so same-block calls are allowed -- this is intentional
    # to support multi-asset withdrawals that trigger multiple deleverages in a single tx.
    # tradeoff: same-block spam (e.g. bundled txs) also bypasses cooldown.
    cooldown: uint256 = self.deleverageCooldown
    lastBlock: uint256 = self.lastDeleverageBlock[_user]
    if cooldown != 0 and lastBlock != 0 and block.number > lastBlock and block.number < lastBlock + cooldown:
        if not didCheckNearRedemption:
            isNearRedemption = self._canDeleverageUserDebtPosition(userDebt.amount, projectedCollateralVal, bt.debtTerms.redemptionThreshold)
            didCheckNearRedemption = True
        if not isNearRedemption:
            return False

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
    debtTimesEffectiveLtv: uint256 = userDebt.amount * effectiveLtv // HUNDRED_PERCENT
    if bt.totalMaxDebt <= debtTimesEffectiveLtv:
        return False
    denominator: uint256 = bt.totalMaxDebt - debtTimesEffectiveLtv

    requiredRepayment: uint256 = numerator // denominator
    if requiredRepayment == 0:
        return False

    # apply configurable buffer to be more conservative
    bufferBps: uint256 = self.deleverageBuffer
    if bufferBps != 0:
        requiredRepayment = requiredRepayment * (HUNDRED_PERCENT + bufferBps) // HUNDRED_PERCENT

    # cap at max deleveragable amount
    requiredRepayment = min(maxDeleveragable, requiredRepayment)

    # final cap at total debt
    requiredRepayment = min(userDebt.amount, requiredRepayment)

    # skip if effective repayment is below minimum threshold (% of total debt)
    # unless position would be near redemption after withdrawal
    minBps: uint256 = self.minDeleverageBps
    if minBps != 0 and requiredRepayment * HUNDRED_PERCENT < userDebt.amount * minBps:
        if not didCheckNearRedemption:
            isNearRedemption = self._canDeleverageUserDebtPosition(userDebt.amount, projectedCollateralVal, bt.debtTerms.redemptionThreshold)
            didCheckNearRedemption = True
        if not isNearRedemption:
            return False

    # execute deleveraging
    config: GenLiqConfig = staticcall MissionControl(a.missionControl).getGenLiqConfig()
    endaomentPsm: address = addys._getEndaomentPsmAddr()
    psmYieldPositionToken: address = staticcall EndaomentPSM(endaomentPsm).getUsdcYieldPositionVaultToken()
    repaidAmount: uint256 = self._deleverageUser(_user, msg.sender, isTrustedCaller, requiredRepayment, config, addys._getEndaomentFundsAddr(), endaomentPsm, psmYieldPositionToken, a)
    if repaidAmount != 0:
        self.lastDeleverageBlock[_user] = block.number
    return repaidAmount != 0


#######################
# Internal Deleverage #
#######################


@internal
def _deleverageUser(
    _user: address,
    _caller: address,
    _isTrusted: bool,
    _targetRepayAmount: uint256,
    _config: GenLiqConfig,
    _endaoFunds: address,
    _endaomentPsm: address,
    _psmYieldPositionToken: address,
    _a: addys.Addys,
) -> uint256:
    isTrusted: bool = _isTrusted

    # check perms -- must also be able to borrow
    if not isTrusted and _user != _caller:
        delegation: cs.ActionDelegation = staticcall MissionControl(_a.missionControl).userDelegation(_user, _caller)
        isTrusted = delegation.canBorrow

    # get latest user debt
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    newInterest: uint256 = 0
    userDebt, bt, newInterest = staticcall CreditEngine(_a.creditEngine).getLatestUserDebtAndTerms(_user, True, _a)
    if userDebt.amount == 0 or bt.hasQuarantinedAsset:
        return 0

    # finalize target repay amount
    targetRepayAmount: uint256 = min(_targetRepayAmount, userDebt.amount)
    if targetRepayAmount == 0:
        targetRepayAmount = userDebt.amount # maximum possible

    # have cap when not trusted (treat similar to redemption)
    if not isTrusted:
        if not self._canDeleverageUserDebtPosition(userDebt.amount, bt.collateralVal, bt.debtTerms.redemptionThreshold):
            return 0
        # SwitchboardBravo rejects ltv > redemptionThreshold. This ordering is
        # required for the cap below to remain conservative.
        targetLtv: uint256 = bt.lowestLtv
        ltvPaybackBuffer: uint256 = staticcall MissionControl(_a.missionControl).getLtvPaybackBuffer()
        if ltvPaybackBuffer != 0:
            targetLtv = targetLtv * (HUNDRED_PERCENT - ltvPaybackBuffer) // HUNDRED_PERCENT
        maxRepayableAmount: uint256 = self._calcAmountToPay(userDebt.amount, bt.collateralVal, targetLtv)
        if maxRepayableAmount == 0:
            return 0
        targetRepayAmount = min(targetRepayAmount, maxRepayableAmount)

    # Earn vault position owners must not have more collateral removed than debt,
    # regardless of which trusted caller initiated the deleverage.
    useFullPayoffExtras: bool = isTrusted and targetRepayAmount == userDebt.amount
    if useFullPayoffExtras:
        # Owner-keyed full-payoff classification necessarily depends on the
        # configured Underscore registry being healthy even when all payoff
        # extras are zero. Governance can set that registry to zero to restore
        # Ripe-only operation only while extras stay off.
        useFullPayoffExtras = self._getUnderscoreAddrType(_user, _a.missionControl, False) != UNDERSCORE_EARN_VAULT_CALLER_TYPE

    # get extra collateral if buffer params set (either usd value or bps over debt amount)
    effectiveBuffer: uint256 = 0
    if useFullPayoffExtras:
        effectiveBuffer = self._getFullPayoffBuffer(userDebt.amount)

    # add extra buffer to account for rounding down collateral to ensure we hit target debt amount
    collateralTargetRepayAmount: uint256 = unsafe_add(targetRepayAmount, effectiveBuffer)

    # perform deleverage phases
    collateralValueRepaid: uint256 = self._performDeleveragePhases(_user, collateralTargetRepayAmount, _config.priorityStabVaults, _config.priorityLiqAssetVaults, _endaoFunds, _endaomentPsm, _psmYieldPositionToken, _a)
    if collateralValueRepaid == 0:
        return 0

    # Refresh live debt after collateral interactions; revert if the
    # amount changed. Planning quantities above stay keyed to the pre-interaction
    # snapshot; settlement uses the refreshed struct + interest.
    userDebt, newInterest = self._refreshSettlementDebt(_user, userDebt.amount, _a)

    # repay debt
    debtToClear: uint256 = self._getDebtToClear(useFullPayoffExtras, collateralValueRepaid, userDebt.amount)

    hasGoodDebtHealth: bool = extcall CreditEngine(_a.creditEngine).repayFromDept(_user, userDebt, debtToClear, newInterest, 0, _a)

    log DeleverageUser(
        user=_user,
        caller=_caller,
        targetRepayAmount=targetRepayAmount,
        targetRepayAmountWithBuffer=collateralTargetRepayAmount,
        collateralValueRepaid=collateralValueRepaid,
        debtToClear=debtToClear,
        hasGoodDebtHealth=hasGoodDebtHealth,
    )
    return debtToClear


@view
@internal
def _getFullPayoffBuffer(_debtAmount: uint256) -> uint256:
    # Returns the extra collateral budget for full-payoff intent.
    # The buffer is capped by both an absolute amount and a debt-relative bps cap
    # so small debts cannot over-consume disproportionate collateral.
    return min(self.deleverageFullPayoffBuffer, unsafe_mul(_debtAmount, self.deleverageOverageBps) // HUNDRED_PERCENT)


@view
@internal
def _refreshSettlementDebt(_user: address, _planningDebtAmount: uint256, _a: addys.Addys) -> (UserDebt, uint256):
    # Re-read live debt after all collateral interactions, immediately
    # before settlement. block.timestamp is constant within a transaction, so
    # ordinary interest accrual cannot change the amount between the planning
    # read and this read; a changed amount means a debt-mutating route (e.g. a
    # callback-token reentry into Teller.repay/borrow) ran during the interaction
    # phase. Settlement was planned against the original amount, so adapting here
    # could over-consume collateral or mis-handle full-payoff/dust; revert
    # instead and roll the whole transaction back atomically.
    refreshedDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    refreshedInterest: uint256 = 0
    refreshedDebt, bt, refreshedInterest = staticcall CreditEngine(_a.creditEngine).getLatestUserDebtAndTerms(_user, False, _a)
    assert refreshedDebt.amount == _planningDebtAmount # dev: debt changed
    return refreshedDebt, refreshedInterest


@view
@internal
def _getDebtToClear(_useFullPayoffExtras: bool, _collateralValueRepaid: uint256, _debtAmount: uint256) -> uint256:
    # Debt accounting is capped at the real debt even when buffer causes extra
    # collateral to be consumed.
    debtToClear: uint256 = min(_collateralValueRepaid, _debtAmount)

    # Only full-payoff flows may forgive tiny residual debt, and only after
    # nonzero collateral was actually consumed. This prevents free debt clearing
    # while still removing floor-rounding dust within the configured caps.
    if _useFullPayoffExtras and _collateralValueRepaid != 0 and debtToClear < _debtAmount:
        dustRemaining: uint256 = unsafe_sub(_debtAmount, debtToClear)
        # This is an explicit debt write-off: repayFromDept does not burn GREEN
        # for the forgiven remainder. Deployment keeps both dust params at zero
        # until governance approves the accounting policy.
        if dustRemaining <= self.deleverageDustThreshold and unsafe_mul(dustRemaining, HUNDRED_PERCENT) <= unsafe_mul(_debtAmount, self.deleverageDustBps):
            debtToClear = _debtAmount
    return debtToClear


# deleverage phases


@internal
def _performDeleveragePhases(
    _user: address,
    _targetRepayAmount: uint256,
    _priorityStabVaults: DynArray[VaultData, MAX_STAB_VAULT_DATA],
    _priorityLiqAssetVaults: DynArray[VaultData, PRIORITY_LIQ_VAULT_DATA],
    _endaoFunds: address,
    _endaomentPsm: address,
    _psmYieldPositionToken: address,
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

            # Phase 1 vaults are Stability Pool cohorts by construction, so apply
            # the fail-soft availability gate.
            remainingToRepay = self._iterateThruAssetsWithinVault(_user, stabPool.vaultId, stabPool.vaultAddr, remainingToRepay, True, _endaoFunds, _endaomentPsm, _psmYieldPositionToken, _a)
            if self.vaultAddrs[stabPool.vaultId] == empty(address):
                self.vaultAddrs[stabPool.vaultId] = stabPool.vaultAddr # cache

    # PHASE 2 -- Go thru priority liq assets (set in mission control)

    if len(_priorityLiqAssetVaults) != 0 and remainingToRepay != 0:
        for pData: VaultData in _priorityLiqAssetVaults:
            if remainingToRepay == 0:
                break

            # Stability Pool cohorts must never be processed as ordinary
            # priority liq assets here -- that route would invoke the strict NAV
            # valuation and re-open the broad-Deleverage revert if governance ever
            # lists a stab vault in this set. Executable exclusion; the cohort is
            # still reachable via phase 1 / phase 3 with fail-soft handling.
            if staticcall MissionControl(_a.missionControl).isStabVaultId(pData.vaultId):
                continue

            if not staticcall Vault(pData.vaultAddr).doesUserHaveBalance(_user, pData.asset):
                continue

            remainingToRepay = self._handleSpecificAsset(_user, pData.vaultId, pData.vaultAddr, pData.asset, remainingToRepay, False, _endaoFunds, _endaomentPsm, _psmYieldPositionToken, _a)
            if self.vaultAddrs[pData.vaultId] == empty(address):
                self.vaultAddrs[pData.vaultId] = pData.vaultAddr # cache

    # PHASE 3 -- Go thru user's vaults (top to bottom as saved in ledger / vaults)

    if remainingToRepay != 0:
        remainingToRepay = self._iterateThruAllUserVaults(_user, remainingToRepay, _endaoFunds, _endaomentPsm, _psmYieldPositionToken, _a)

    return _targetRepayAmount - remainingToRepay


# all user vaults


@internal
def _iterateThruAllUserVaults(
    _user: address,
    _remainingToRepay: uint256,
    _endaoFunds: address,
    _endaomentPsm: address,
    _psmYieldPositionToken: address,
    _a: addys.Addys,
) -> uint256:
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

        # The full user-vault sweep can re-encounter a Stability Pool
        # cohort (whether or not it was in the priority list). Classify it so the
        # same fail-soft availability gate applies here. The didHandleVaultId
        # transient guard inside _iterateThruAssetsWithinVault prevents a second
        # probe of a cohort already handled in phase 1.
        isStabVault: bool = staticcall MissionControl(_a.missionControl).isStabVaultId(vaultId)
        remainingToRepay = self._iterateThruAssetsWithinVault(_user, vaultId, vaultAddr, remainingToRepay, isStabVault, _endaoFunds, _endaomentPsm, _psmYieldPositionToken, _a)

    return remainingToRepay


# all assets within vault


@internal
def _iterateThruAssetsWithinVault(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _remainingToRepay: uint256,
    _isStabVault: bool,
    _endaoFunds: address,
    _endaomentPsm: address,
    _psmYieldPositionToken: address,
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

        asset: address = empty(address)
        availableAmount: uint256 = 0
        asset, availableAmount = self._getBroadTraversalAsset(_user, _vaultAddr, y, _isStabVault)
        if asset == empty(address) or availableAmount == 0:
            continue

        # handle specific liq asset
        remainingToRepay = self._handleSpecificAsset(_user, _vaultId, _vaultAddr, asset, remainingToRepay, False, _endaoFunds, _endaomentPsm, _psmYieldPositionToken, _a)

    return remainingToRepay


@view
@internal
def _getBroadTraversalAsset(_user: address, _vaultAddr: address, _index: uint256, _isStabVault: bool) -> (address, uint256):
    if _isStabVault:
        # Stability Pool cohorts expose their fail-soft liquidation amount.
        return staticcall Vault(_vaultAddr).getUserAssetAndAmountAtIndex(_user, _index)

    asset: address = empty(address)
    hasBalance: bool = False
    asset, hasBalance = staticcall Vault(_vaultAddr).getUserAssetAtIndexAndHasBalance(_user, _index)
    return asset, 1 if hasBalance else 0


# specific asset


@internal
def _handleSpecificAsset(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _remainingToRepay: uint256,
    _volatilesOnly: bool,
    _endaoFunds: address,
    _endaomentPsm: address,
    _psmYieldPositionToken: address,
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

    # transfer to endaoment funds or psm
    recipient: address = _endaoFunds
    if _psmYieldPositionToken != empty(address) and _asset == _psmYieldPositionToken:
        recipient = _endaomentPsm

    # handle volatile assets only - skip normal deleverage assets (shouldBurnAsPayment or shouldTransferToEndaoment)
    if _volatilesOnly:
        if config.shouldBurnAsPayment or config.shouldTransferToEndaoment:
            return _remainingToRepay
        return self._transferToEndaoment(_user, _vaultId, _vaultAddr, _asset, _remainingToRepay, recipient, _a)

    # burn stability pool assets (GREEN, sGREEN)
    if config.shouldBurnAsPayment and _asset in [_a.greenToken, _a.savingsGreen]:
        return self._burnStabPoolAsset(_user, _vaultId, _vaultAddr, _asset, _remainingToRepay, _a)

    # transfer to endaoment (other stablecoins)
    if config.shouldTransferToEndaoment:
        return self._transferToEndaoment(_user, _vaultId, _vaultAddr, _asset, _remainingToRepay, recipient, _a)

    return _remainingToRepay


# burn stability pool assets


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


# transfer to endaoment


@internal
def _transferToEndaoment(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _remainingToRepay: uint256,
    _recipient: address,
    _a: addys.Addys,
) -> uint256:
    collateralUsdValueSent: uint256 = 0
    collateralAmountSent: uint256 = 0
    isPositionDepleted: bool = False
    collateralUsdValueSent, collateralAmountSent, isPositionDepleted = self._transferCollateral(_user, _recipient, _vaultAddr, _asset, _remainingToRepay, _a)
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


# deleverage info


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

        isStabVault: bool = staticcall MissionControl(_a.missionControl).isStabVaultId(vaultId)

        # iterate through assets
        for y: uint256 in range(1, numUserAssets, bound=max_value(uint256)):
            asset: address = empty(address)
            amount: uint256 = 0
            asset, amount = self._getBroadTraversalAsset(_user, vaultAddr, y, isStabVault)
            if asset == empty(address) or amount == 0:
                continue

            if not isStabVault:
                amount = staticcall Vault(vaultAddr).getTotalAmountForUser(_user, asset)
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
            # Zero-LTV assets remain repayment liquidity even though they do not
            # contribute borrowing capacity in CreditEngine collateral value.
            ltvSum += usdValue * debtTerms.ltv

    # calculate effective weighted LTV
    effectiveWeightedLtv: uint256 = 0
    if maxDeleveragableUsd != 0:
        effectiveWeightedLtv = ltvSum // maxDeleveragableUsd

    return maxDeleveragableUsd, effectiveWeightedLtv


# max deleverage amount (when untrusted caller)


@view
@external
def getMaxDeleverageAmount(_user: address) -> uint256:
    a: addys.Addys = addys._getAddys()

    # get latest user debt and terms
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    na: uint256 = 0
    userDebt, bt, na = staticcall CreditEngine(a.creditEngine).getLatestUserDebtAndTerms(_user, False, a)
    if userDebt.amount == 0 or userDebt.inLiquidation or bt.hasQuarantinedAsset or bt.collateralVal == 0:
        return 0

    if not self._canDeleverageUserDebtPosition(userDebt.amount, bt.collateralVal, bt.debtTerms.redemptionThreshold):
        return 0

    ltvPaybackBuffer: uint256 = staticcall MissionControl(a.missionControl).getLtvPaybackBuffer()

    # target ltv
    targetLtv: uint256 = bt.lowestLtv
    if ltvPaybackBuffer != 0:
        targetLtv = targetLtv * (HUNDRED_PERCENT - ltvPaybackBuffer) // HUNDRED_PERCENT

    return self._calcAmountToPay(userDebt.amount, bt.collateralVal, targetLtv)


@view
@internal
def _calcAmountToPay(_debtAmount: uint256, _collateralValue: uint256, _targetLtv: uint256) -> uint256:
    # goal here is to only reduce the debt necessary to get LTV back to safe position
    # it will never be perfectly precise because depending on what assets are taken
    # to ensure maximum protocol solvency, we will target the user's lowest LTV
    collValueAdjusted: uint256 =_collateralValue * _targetLtv // HUNDRED_PERCENT

    # collateral value too low
    if _debtAmount <= collValueAdjusted:
        return _debtAmount

    debtToRepay: uint256 = (_debtAmount - collValueAdjusted) * HUNDRED_PERCENT // (HUNDRED_PERCENT - _targetLtv)
    return min(debtToRepay, _debtAmount)


@view
@internal
def _canDeleverageUserDebtPosition(_userDebtAmount: uint256, _collateralVal: uint256, _redemptionThreshold: uint256) -> bool:
    if _redemptionThreshold == 0:
        return False

    # check if collateral value is below (or equal) to redemption threshold
    redemptionThreshold: uint256 = _userDebtAmount * HUNDRED_PERCENT // _redemptionThreshold
    return _collateralVal <= redemptionThreshold


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
    isUnderscoreBasicEarnVault: bool = self._getUnderscoreAddrType(_asset, _a.missionControl, True) != 0
    underlyingAsset: address = empty(address)
    if isUnderscoreBasicEarnVault:
        underlyingAsset = staticcall IERC4626(_asset).asset()

    # calculate max asset amount
    maxAssetAmount: uint256 = self._getMaxAssetAmount(_asset, _targetUsdValue, isUnderscoreBasicEarnVault, underlyingAsset, _a.greenToken, _a.savingsGreen, _a.priceDesk)
    if maxAssetAmount == 0:
        return 0, 0, False

    # withdraw and transfer to recipient -- AuctionHouse has permissions to perform this
    amountSent: uint256 = 0
    isPositionDepleted: bool = False
    amountSent, isPositionDepleted = extcall AuctionHouse(_a.auctionHouse).withdrawTokensFromVault(_fromUser, _asset, maxAssetAmount, _toUser, _vaultAddr, isUnderscoreBasicEarnVault, _a)

    usdValue: uint256 = _targetUsdValue * amountSent // maxAssetAmount

    # For underscore basic earn vault assets, cap max conversion at
    # convertToAssetsSafe + configured spread so crediting remains bounded.
    if isUnderscoreBasicEarnVault and amountSent != 0 and underlyingAsset != empty(address):
        na: uint256 = 0
        cappedUnderlying: uint256 = 0
        na, cappedUnderlying = self._getMaxAndCappedUnderlyingForShares(_asset, amountSent)
        # AuctionHouse preflights BasicVault's known amount clamps; retain this
        # as a consistency invariant for divergent vault or asset behavior.
        assert cappedUnderlying != 0 # dev: zero safe underlying
        usdValue = staticcall PriceDesk(_a.priceDesk).getUsdValue(underlyingAsset, cappedUnderlying, True)

    return usdValue, amountSent, isPositionDepleted


# underscore caller info


@internal
def _getUnderscoreAddrType(_addr: address, _mc: address, _basicEarnVaultOnly: bool) -> uint256:
    # Normal mode classifies callers/owners: 0 = not Underscore, 1 = lego or
    # other trusted caller, 2 = earn vault. Basic-vault-only mode classifies an
    # asset and returns only 0 or 2; it deliberately skips the lego-book lookup.
    # Writes the underscore vault registry to transient cache, so do not use from @view paths.
    underscore: address = staticcall MissionControl(_mc).underscoreRegistry()
    if underscore == empty(address):
        # The zero-registry escape hatch cannot identify earn-vault owners, so
        # governance must keep full-payoff extras disabled while using it.
        return 0

    vaultRegistry: address = self._getUnderscoreVaultRegistry(underscore)
    if vaultRegistry != empty(address):
        if _basicEarnVaultOnly:
            return UNDERSCORE_EARN_VAULT_CALLER_TYPE if staticcall VaultRegistry(vaultRegistry).isBasicEarnVault(_addr) else 0
        if staticcall VaultRegistry(vaultRegistry).isEarnVault(_addr):
            return UNDERSCORE_EARN_VAULT_CALLER_TYPE
    elif _basicEarnVaultOnly:
        return 0

    # check if underscore lego
    undyLegoBook: address = staticcall Registry(underscore).getAddr(UNDERSCORE_LEGOBOOK_ID)
    if undyLegoBook == empty(address):
        return 0
    return UNDERSCORE_LEGO_CALLER_TYPE if staticcall Registry(undyLegoBook).isValidAddr(_addr) else 0


@internal
def _getUnderscoreVaultRegistry(_underscoreRegistry: address) -> address:
    vaultRegistry: address = self.underscoreVaultRegistry[_underscoreRegistry]
    if vaultRegistry == empty(address):
        vaultRegistry = staticcall Registry(_underscoreRegistry).getAddr(UNDERSCORE_VAULT_REGISTRY_ID)
        if vaultRegistry != empty(address):
            self.underscoreVaultRegistry[_underscoreRegistry] = vaultRegistry
    return vaultRegistry


@view
@internal
def _getMaxAndCappedUnderlyingForShares(_asset: address, _shares: uint256) -> (uint256, uint256):
    maxUnderlying: uint256 = staticcall IERC4626(_asset).convertToAssets(_shares)
    if maxUnderlying == 0:
        return 0, 0

    safeUnderlying: uint256 = staticcall UnderscoreVault(_asset).convertToAssetsSafe(_shares)
    if safeUnderlying == 0:
        return 0, 0

    maxAllowedUnderlying: uint256 = safeUnderlying * (HUNDRED_PERCENT + self.underscoreSafeSpreadBps) // HUNDRED_PERCENT
    return maxUnderlying, min(maxUnderlying, maxAllowedUnderlying)


# get asset amount


@view
@internal
def _getMaxAssetAmount(
    _asset: address,
    _targetUsdValue: uint256,
    _isUnderscoreBasicEarnVault: bool,
    _underlyingAsset: address,
    _greenToken: address,
    _savingsGreen: address,
    _priceDesk: address,
) -> uint256:
    amount: uint256 = 0
    if _asset == _greenToken:
        amount = _targetUsdValue
    elif _asset == _savingsGreen:
        amount = staticcall IERC4626(_savingsGreen).convertToShares(_targetUsdValue)
    elif _isUnderscoreBasicEarnVault:

        if _underlyingAsset == empty(address):
            return 0
        underlyingAmount: uint256 = staticcall PriceDesk(_priceDesk).getAssetAmount(_underlyingAsset, _targetUsdValue, True)
        adjustedUnderlyingAmount: uint256 = underlyingAmount

        # Compare max vs capped value for one whole-share unit.
        # Using a fixed share unit avoids noisy tiny-amount rounding.
        sampleShareUnit: uint256 = 10 ** convert(staticcall IERC20Detailed(_asset).decimals(), uint256)
        maxSampleUnderlying: uint256 = 0
        cappedSampleUnderlying: uint256 = 0
        maxSampleUnderlying, cappedSampleUnderlying = self._getMaxAndCappedUnderlyingForShares(_asset, sampleShareUnit)
        if cappedSampleUnderlying == 0:
            return 0
        if maxSampleUnderlying > cappedSampleUnderlying:
            # ceil(a / b) = (a + b - 1) // b
            adjustedUnderlyingAmount = (underlyingAmount * maxSampleUnderlying + cappedSampleUnderlying - 1) // cappedSampleUnderlying

        amount = staticcall IERC4626(_asset).convertToShares(adjustedUnderlyingAmount)
    else:
        amount = staticcall PriceDesk(_priceDesk).getAssetAmount(_asset, _targetUsdValue, True)
    return amount


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


# deleverage params

# Constructor args are validated above. The four legacy setters remain
# Switchboard-enforced to preserve runtime bytecode; the new full-payoff params
# also enforce their unsafe-math ceilings here as defense in depth.


@external
def setMinDeleverageBps(_bps: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: only switchboard allowed
    assert not deptBasics.isPaused # dev: contract paused
    self.minDeleverageBps = _bps
    log MinDeleverageBpsSet(bps=_bps)


@external
def setDeleverageBuffer(_bps: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: only switchboard allowed
    assert not deptBasics.isPaused # dev: contract paused
    self.deleverageBuffer = _bps
    log DeleverageBufferSet(bps=_bps)


@external
def setDeleverageCooldown(_blocks: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: only switchboard allowed
    assert not deptBasics.isPaused # dev: contract paused
    self.deleverageCooldown = _blocks
    log DeleverageCooldownSet(blocks=_blocks)


@external
def setUnderscoreSafeSpreadBps(_bps: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: only switchboard allowed
    assert not deptBasics.isPaused # dev: contract paused
    self.underscoreSafeSpreadBps = _bps
    log UnderscoreSafeSpreadBpsSet(bps=_bps)


@external
def setDeleverageFullPayoffParam(_param: uint256, _amount: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: only switchboard allowed
    assert not deptBasics.isPaused # dev: contract paused
    # _param values: 1=fullPayoffBuffer, 2=overageBps, 3=dustThreshold, 4=dustBps
    if _param == 1:
        assert _amount <= MAX_DELEVERAGE_FULL_PAYOFF_BUFFER # dev: exceeds hard ceiling
        self.deleverageFullPayoffBuffer = _amount
    elif _param == 2:
        assert _amount <= MAX_DELEVERAGE_OVERAGE_BPS # dev: exceeds hard ceiling
        self.deleverageOverageBps = _amount
    elif _param == 3:
        assert _amount <= MAX_DELEVERAGE_DUST_THRESHOLD # dev: exceeds hard ceiling
        self.deleverageDustThreshold = _amount
    else:
        assert _param == 4 # dev: invalid param
        assert _amount <= MAX_DELEVERAGE_DUST_BPS # dev: exceeds hard ceiling
        self.deleverageDustBps = _amount
    log DeleverageFullPayoffParamSet(param=_param, amount=_amount)
