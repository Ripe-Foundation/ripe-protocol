#    .-.                  .
#   (_) )-.              /                           /  .-.
#      /   \   .-.  .-../   .-..  .-. .-.     .-.---/---`-'.-._..  .-.
#     /     )./.-'_(   /  ./.-'_)/   )   )    /  ) /   /  (   )  )/   )
#  .-/  `--' (__.'  `-'-..(__.''/   /   (    /`-' / _.(__. `-'  '/   (
# (_/     `-._)                          `-'/                         `-
#
#     ╔══════════════════════════════════════════════════════════════╗
#     ║  ** Credit Redeem **                                         ║
#     ║  Handles collateral redemption for debt positions            ║
#     ╚══════════════════════════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3
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

from ethereum.ercs import IERC20
from ethereum.ercs import IERC4626

interface CreditEngine:
    def getUserBorrowTermsWithNumVaults(_user: address, _numUserVaults: uint256, _shouldRaise: bool, _skipVaultId: uint256 = 0, _skipAsset: address = empty(address), _a: addys.Addys = empty(addys.Addys)) -> UserBorrowTerms: view
    def transferOrWithdrawViaRedemption(_shouldTransferBalance: bool, _asset: address, _user: address, _recipient: address, _amount: uint256, _vaultId: uint256, _vaultAddr: address, _a: addys.Addys) -> uint256: nonpayable
    def repayFromDept(_user: address, _userDebt: UserDebt, _repayValue: uint256, _newInterest: uint256, _numUserVaults: uint256, _a: addys.Addys = empty(addys.Addys)) -> bool: nonpayable
    def getLatestUserDebtAndTerms(_user: address, _shouldRaise: bool, _a: addys.Addys = empty(addys.Addys)) -> (UserDebt, UserBorrowTerms, uint256): view
    def getLatestUserDebtWithInterest(_userDebt: UserDebt) -> (UserDebt, uint256): view

interface Teller:
    def depositFromTrusted(_user: address, _vaultId: uint256, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def isUnderscoreWalletOwner(_user: address, _caller: address, _mc: address) -> bool: view

interface MissionControl:
    def getRedeemCollateralConfig(_asset: address, _recipient: address) -> RedeemCollateralConfig: view
    def getLtvPaybackBuffer() -> uint256: view

interface PriceDesk:
    def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool) -> uint256: view

interface Ledger:
    def getRepayDataBundle(_user: address) -> RepayDataBundle: view

interface GreenToken:
    def burn(_amount: uint256) -> bool: nonpayable

interface AddressRegistry:
    def getAddr(_regId: uint256) -> address: view

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

struct RepayDataBundle:
    userDebt: UserDebt
    numUserVaults: uint256

struct RedeemCollateralConfig:
    canRedeemCollateralGeneral: bool
    canRedeemCollateralAsset: bool
    isUserAllowed: bool
    ltvPaybackBuffer: uint256
    canAnyoneDeposit: bool

struct CollateralRedemption:
    user: address
    vaultId: uint256
    asset: address
    maxGreenAmount: uint256

event CollateralRedeemed:
    user: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    amount: uint256
    recipient: indexed(address)
    caller: address
    repayValue: uint256
    hasGoodDebtHealth: bool

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_COLLATERAL_REDEMPTIONS: constant(uint256) = 20
STABILITY_POOL_ID: constant(uint256) = 1


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no green minting/burning needed here


#####################
# Redeem Collateral #
#####################


@external
def redeemCollateralFromMany(
    _redemptions: DynArray[CollateralRedemption, MAX_COLLATERAL_REDEMPTIONS],
    _greenAmount: uint256,
    _recipient: address,
    _caller: address,
    _shouldTransferBalance: bool,
    _shouldRefundSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert not deptBasics.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    totalGreenSpent: uint256 = 0
    totalGreenRemaining: uint256 = min(_greenAmount, staticcall IERC20(a.greenToken).balanceOf(self))
    assert totalGreenRemaining != 0 # dev: no green to redeem

    for r: CollateralRedemption in _redemptions:
        if totalGreenRemaining == 0:
            break
        greenSpent: uint256 = self._redeemCollateral(r.user, r.vaultId, r.asset, r.maxGreenAmount, totalGreenRemaining, _recipient, _caller, _shouldTransferBalance, a)
        totalGreenRemaining -= greenSpent
        totalGreenSpent += greenSpent

    assert totalGreenSpent != 0 # dev: no redemptions occurred

    # handle leftover green
    if totalGreenRemaining != 0:
        self._handleGreenForUser(_caller, totalGreenRemaining, _shouldRefundSavingsGreen, False, a)

    return totalGreenSpent


@internal
def _redeemCollateral(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _maxGreenForAsset: uint256,
    _totalGreenRemaining: uint256,
    _recipient: address,
    _caller: address,
    _shouldTransferBalance: bool,
    _a: addys.Addys,
) -> uint256:

    # NOTE: failing gracefully here, in case of many redemptions at same time

    # invalid inputs
    if empty(address) in [_recipient, _asset, _user] or 0 in [_maxGreenForAsset, _totalGreenRemaining, _vaultId]:
        return 0

    # recipient cannot be user
    if _recipient == _user:
        return 0

    # vault address
    vaultAddr: address = staticcall AddressRegistry(_a.vaultBook).getAddr(_vaultId)
    if vaultAddr == empty(address):
        return 0

    # user must have balance
    if not staticcall Vault(vaultAddr).doesUserHaveBalance(_user, _asset):
        return 0

    # redemptions not allowed on asset
    config: RedeemCollateralConfig = staticcall MissionControl(_a.missionControl).getRedeemCollateralConfig(_asset, _recipient)
    if not config.canRedeemCollateralGeneral or not config.canRedeemCollateralAsset or not config.isUserAllowed:
        return 0

    # make sure caller can deposit to recipient
    if _recipient != _caller and not config.canAnyoneDeposit:
        assert staticcall Teller(_a.teller).isUnderscoreWalletOwner(_recipient, _caller, _a.missionControl) # dev: not allowed to deposit for user

    # get latest user debt
    d: RepayDataBundle = staticcall Ledger(_a.ledger).getRepayDataBundle(_user)
    userDebt: UserDebt = empty(UserDebt)
    newInterest: uint256 = 0
    userDebt, newInterest = staticcall CreditEngine(_a.creditEngine).getLatestUserDebtWithInterest(d.userDebt)

    # cannot redeem if no debt or in liquidation
    if userDebt.amount == 0 or userDebt.inLiquidation:
        return 0

    # get latest debt terms
    bt: UserBorrowTerms = staticcall CreditEngine(_a.creditEngine).getUserBorrowTermsWithNumVaults(_user, d.numUserVaults, True, 0, empty(address), _a)
    if bt.collateralVal == 0:
        return 0

    # user has not reached redemption threshold
    if not self._canRedeemUserCollateral(userDebt.amount, bt.collateralVal, bt.debtTerms.redemptionThreshold):
        return 0

    # estimated debt to pay back to achieve safe LTV
    # won't be exact because depends on which collateral is redeemed (LTV changes)
    targetLtv: uint256 = bt.debtTerms.ltv * (HUNDRED_PERCENT - config.ltvPaybackBuffer) // HUNDRED_PERCENT
    maxCollateralValue: uint256 = self._calcAmountToPay(userDebt.amount, bt.collateralVal, targetLtv)

    # treating green as $1
    maxGreenAvailable: uint256 = min(_totalGreenRemaining, staticcall IERC20(_a.greenToken).balanceOf(self))
    maxGreenForAsset: uint256 = min(_maxGreenForAsset, maxGreenAvailable)
    maxRedeemValue: uint256 = min(maxCollateralValue, maxGreenForAsset)
    if maxRedeemValue == 0:
        return 0

    # max asset amount to take from user
    maxAssetAmount: uint256 = staticcall PriceDesk(_a.priceDesk).getAssetAmount(_asset, maxRedeemValue, True)
    if maxAssetAmount == 0:
        return 0

    # withdraw or transfer balance to redeemer
    amountSent: uint256 = extcall CreditEngine(_a.creditEngine).transferOrWithdrawViaRedemption(_shouldTransferBalance, _asset, _user, _recipient, maxAssetAmount, _vaultId, vaultAddr, _a)

    # repay debt
    repayValue: uint256 = min(amountSent * maxRedeemValue // maxAssetAmount, userDebt.amount)
    assert extcall GreenToken(_a.greenToken).burn(repayValue) # dev: could not burn green
    hasGoodDebtHealth: bool = extcall CreditEngine(_a.creditEngine).repayFromDept(_user, userDebt, repayValue, newInterest, d.numUserVaults, _a)

    log CollateralRedeemed(
        user=_user,
        vaultId=_vaultId,
        asset=_asset,
        amount=amountSent,
        recipient=_recipient,
        caller=_caller,
        repayValue=repayValue,
        hasGoodDebtHealth=hasGoodDebtHealth,
    )
    return min(repayValue, maxRedeemValue)


# green handling


@internal
def _handleGreenForUser(
    _recipient: address,
    _greenAmount: uint256,
    _wantsSavingsGreen: bool,
    _shouldEnterStabPool: bool,
    _a: addys.Addys,
):
    amount: uint256 = min(_greenAmount, staticcall IERC20(_a.greenToken).balanceOf(self))
    if amount == 0:
        return

    if _wantsSavingsGreen and amount > 10 ** 9: # small dust will fail

        sgreenRecipient: address = _recipient
        if _shouldEnterStabPool:
            sgreenRecipient = self

        # put GREEN into sGREEN
        assert extcall IERC20(_a.greenToken).approve(_a.savingsGreen, amount, default_return_value=True) # dev: green approval failed
        sGreenAmount: uint256 = extcall IERC4626(_a.savingsGreen).deposit(amount, sgreenRecipient)
        assert extcall IERC20(_a.greenToken).approve(_a.savingsGreen, 0, default_return_value=True) # dev: green approval failed

        # put sGREEN into stability pool
        if _shouldEnterStabPool:
            assert extcall IERC20(_a.savingsGreen).approve(_a.teller, sGreenAmount, default_return_value=True) # dev: sgreen approval failed
            extcall Teller(_a.teller).depositFromTrusted(_recipient, STABILITY_POOL_ID, _a.savingsGreen, sGreenAmount, 0, _a)
            assert extcall IERC20(_a.savingsGreen).approve(_a.teller, 0, default_return_value=True) # dev: sgreen approval failed

    else:
        assert extcall IERC20(_a.greenToken).transfer(_recipient, amount, default_return_value=True) # dev: green transfer failed


# utils


@view
@external
def getMaxRedeemValue(_user: address) -> uint256:
    a: addys.Addys = addys._getAddys()

    # get latest user debt and terms
    userDebt: UserDebt = empty(UserDebt)
    bt: UserBorrowTerms = empty(UserBorrowTerms)
    na: uint256 = 0
    userDebt, bt, na = staticcall CreditEngine(a.creditEngine).getLatestUserDebtAndTerms(_user, False, a)
    if userDebt.amount == 0 or userDebt.inLiquidation or bt.collateralVal == 0:
        return 0

    if not self._canRedeemUserCollateral(userDebt.amount, bt.collateralVal, bt.debtTerms.redemptionThreshold):
        return 0
    
    ltvPaybackBuffer: uint256 = staticcall MissionControl(a.missionControl).getLtvPaybackBuffer()
    targetLtv: uint256 = bt.debtTerms.ltv * (HUNDRED_PERCENT - ltvPaybackBuffer) // HUNDRED_PERCENT
    return self._calcAmountToPay(userDebt.amount, bt.collateralVal, targetLtv)


@view
@internal
def _calcAmountToPay(_debtAmount: uint256, _collateralValue: uint256, _targetLtv: uint256) -> uint256:
    # goal here is to only reduce the debt necessary to get LTV back to safe position
    # it will never be perfectly precise because depending on what assets are taken, the LTV might slightly change
    collValueAdjusted: uint256 =_collateralValue * _targetLtv // HUNDRED_PERCENT

    toPay: uint256 = (_debtAmount - collValueAdjusted) * HUNDRED_PERCENT // (HUNDRED_PERCENT - _targetLtv)
    return min(toPay, _debtAmount)


@view
@internal
def _canRedeemUserCollateral(_userDebtAmount: uint256, _collateralVal: uint256, _redemptionThreshold: uint256) -> bool:
    if _redemptionThreshold == 0:
        return False
    
    # check if collateral value is below (or equal) to redemption threshold
    redemptionThreshold: uint256 = _userDebtAmount * HUNDRED_PERCENT // _redemptionThreshold
    return _collateralVal <= redemptionThreshold
