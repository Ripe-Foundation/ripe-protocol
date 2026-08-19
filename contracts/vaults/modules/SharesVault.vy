# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

uses: vaultData
import contracts.vaults.modules.VaultData as vaultData

from interfaces import Vault
from ethereum.ercs import IERC20

DECIMAL_OFFSET: constant(uint256) = 10 ** 8
MAX_TRANSFER_DELTA: constant(uint256) = 2


@deploy
def __init__():
    pass


########
# Core #
########


@internal
def _depositTokensInVault(
    _user: address,
    _asset: address,
    _amount: uint256,
) -> (uint256, uint256):
    assert not vaultData.isPaused # dev: contract paused

    # validation
    assert empty(address) not in [_user, _asset] # dev: invalid user or asset
    totalAssetBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    depositAmount: uint256 = min(_amount, totalAssetBalance)
    assert depositAmount != 0 # dev: invalid deposit amount

    # calc shares
    prevTotalBalance: uint256 = totalAssetBalance - depositAmount # remove the deposited amount to calc shares accurately
    newShares: uint256 = self._amountToShares(depositAmount, vaultData.totalBalances[_asset], prevTotalBalance, False)
    assert newShares != 0 # dev: cannot receive 0 shares

    # add balance on deposit
    vaultData._addBalanceOnDeposit(_user, _asset, newShares, True)

    return depositAmount, newShares


@internal
def _withdrawTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
) -> (uint256, uint256, bool):
    assert not vaultData.isPaused # dev: contract paused
    assert empty(address) not in [_user, _asset, _recipient] # dev: invalid user, asset, or recipient
    assert _recipient != self # dev: invalid recipient

    requestedShares: uint256 = 0
    requestedAmount: uint256 = 0
    requestedShares, requestedAmount = self._calcWithdrawalSharesAndAmount(_user, _asset, _amount)

    totalSharesBefore: uint256 = vaultData.totalBalances[_asset]
    userSharesBefore: uint256 = vaultData.userBalances[_user][_asset]
    vaultBefore: uint256 = staticcall IERC20(_asset).balanceOf(self)
    recipientBefore: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)

    assert extcall IERC20(_asset).transfer(_recipient, requestedAmount, default_return_value=True) # dev: token transfer failed

    vaultAfter: uint256 = staticcall IERC20(_asset).balanceOf(self)
    recipientAfter: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)
    assert vaultAfter <= vaultBefore # dev: invalid vault outflow
    assert recipientAfter >= recipientBefore # dev: invalid recipient delivery

    actualOutflow: uint256 = vaultBefore - vaultAfter
    actualDelivery: uint256 = recipientAfter - recipientBefore
    assert self._isWithinTransferDelta(actualOutflow, requestedAmount) # dev: invalid vault outflow
    assert self._isWithinTransferDelta(actualDelivery, requestedAmount) # dev: invalid recipient delivery

    withdrawalShares: uint256 = requestedShares
    if actualOutflow != requestedAmount:
        withdrawalShares = self._amountToShares(
            actualOutflow,
            totalSharesBefore,
            vaultBefore,
            True,
        )
        if withdrawalShares > userSharesBefore:
            assert userSharesBefore == totalSharesBefore # dev: remaining holder loss
            withdrawalShares = userSharesBefore
    assert withdrawalShares != 0 # dev: cannot withdraw 0 shares

    isDepleted: bool = False
    withdrawalShares, isDepleted = vaultData._reduceBalanceOnWithdrawal(
        _user,
        _asset,
        withdrawalShares,
        True,
    )

    return actualOutflow, withdrawalShares, isDepleted


@pure
@internal
def _isWithinTransferDelta(
    _actual: uint256,
    _requested: uint256,
) -> bool:
    if _actual >= _requested:
        return _actual - _requested <= MAX_TRANSFER_DELTA
    return _requested - _actual <= MAX_TRANSFER_DELTA


@internal
def _transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
) -> (uint256, uint256, bool):
    assert not vaultData.isPaused # dev: contract paused
    assert empty(address) not in [_fromUser, _toUser, _asset] # dev: invalid users or asset

    # calc shares + amount to transfer
    transferShares: uint256 = 0
    transferAmount: uint256 = 0
    transferShares, transferAmount = self._calcWithdrawalSharesAndAmount(_fromUser, _asset, _transferAmount)

    # transfer shares
    isFromUserDepleted: bool = False
    transferShares, isFromUserDepleted = vaultData._reduceBalanceOnWithdrawal(_fromUser, _asset, transferShares, False)
    vaultData._addBalanceOnDeposit(_toUser, _asset, transferShares, False)

    return transferAmount, transferShares, isFromUserDepleted


####################
# Needs For Others #
####################


@view
@internal
def _getVaultDataOnDeposit(_user: address, _asset: address) -> Vault.VaultDataOnDeposit:
    # used in Teller.vy
    totalBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    return Vault.VaultDataOnDeposit(
        hasPosition=vaultData.indexOfUserAsset[_user][_asset] != 0,
        numAssets=vaultData._getNumUserAssets(_user),
        userBalance=self._getTotalAmountForUserWithTotalBal(_user, _asset, totalBalance),
        totalBalance=totalBalance,
    )


@view
@internal
def _getUserLootBoxShare(_user: address, _asset: address) -> uint256:
    # used in Lootbox.vy
    return vaultData.userBalances[_user][_asset] // DECIMAL_OFFSET


@view
@internal
def _getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
    # used in CreditEngine.vy
    asset: address = vaultData.userAssets[_user][_index]
    if asset == empty(address):
        return empty(address), 0
    userShares: uint256 = vaultData.userBalances[_user][asset]
    if userShares == 0:
        return empty(address), 0
    return asset, self._sharesToAmount(userShares, vaultData.totalBalances[asset], staticcall IERC20(asset).balanceOf(self), False)


@view
@internal
def _getUserAssetAtIndexAndHasBalance(_user: address, _index: uint256) -> (address, bool):
    # used in Lootbox.vy and AuctionHouse.vy
    asset: address = vaultData.userAssets[_user][_index]
    if asset == empty(address):
        return empty(address), False
    return asset, vaultData.userBalances[_user][asset] != 0


###############
# Other Utils #
###############


@view
@internal
def _getTotalAmountForUser(_user: address, _asset: address) -> uint256:
    return self._getTotalAmountForUserWithTotalBal(_user, _asset, staticcall IERC20(_asset).balanceOf(self))


@view
@internal
def _getTotalAmountForUserWithTotalBal(_user: address, _asset: address, _totalBalance: uint256) -> uint256:
    userShares: uint256 = vaultData.userBalances[_user][_asset]
    return self._sharesToAmount(userShares, vaultData.totalBalances[_asset], _totalBalance, False)


@view
@internal
def _getTotalAmountForVault(_asset: address) -> uint256:
    return staticcall IERC20(_asset).balanceOf(self)


##########
# Shares #
##########


@view
@internal
def _calcWithdrawalSharesAndAmount(
    _user: address,
    _asset: address,
    _amount: uint256,
) -> (uint256, uint256):
    totalBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    assert totalBalance != 0 # dev: no asset to withdraw

    totalShares: uint256 = vaultData.totalBalances[_asset]

    # user shares
    withdrawalShares: uint256 = vaultData.userBalances[_user][_asset]
    assert withdrawalShares != 0 # dev: user has no shares

    # calc amount + shares to withdraw
    withdrawalAmount: uint256 = min(totalBalance, self._sharesToAmount(withdrawalShares, totalShares, totalBalance, False))
    if _amount < withdrawalAmount:
        withdrawalShares = min(withdrawalShares, self._amountToShares(_amount, totalShares, totalBalance, True))
        withdrawalAmount = _amount

    assert withdrawalAmount != 0 # dev: no withdrawal amount
    return withdrawalShares, withdrawalAmount


# amount -> shares


@view
@external
def amountToShares(_asset: address, _amount: uint256, _shouldRoundUp: bool) -> uint256:
    totalShares: uint256 = vaultData.totalBalances[_asset]
    totalBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    return self._amountToShares(_amount, totalShares, totalBalance, _shouldRoundUp)


@view
@internal
def _amountToShares(
    _amount: uint256,
    _totalShares: uint256,
    _totalBalance: uint256,
    _shouldRoundUp: bool,
) -> uint256:
    totalBalance: uint256 = _totalBalance

    # dead shares / decimal offset -- preventing donation attacks
    totalBalance += 1
    totalShares: uint256 = _totalShares + DECIMAL_OFFSET

    shares: uint256 = self._mulDiv(_amount, totalShares, totalBalance)
    if _shouldRoundUp and (uint256_mulmod(_amount, totalShares, totalBalance) != 0):
        shares += 1

    return shares


# shares -> amount


@view
@external
def sharesToAmount(_asset: address, _shares: uint256, _shouldRoundUp: bool) -> uint256:
    totalShares: uint256 = vaultData.totalBalances[_asset]
    totalBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    return self._sharesToAmount(_shares, totalShares, totalBalance, _shouldRoundUp)


@view
@internal
def _sharesToAmount(
    _shares: uint256,
    _totalShares: uint256,
    _totalBalance: uint256,
    _shouldRoundUp: bool,
) -> uint256:
    totalBalance: uint256 = _totalBalance

    # dead shares / decimal offset -- preventing donation attacks
    totalBalance += 1
    totalShares: uint256 = _totalShares + DECIMAL_OFFSET

    amount: uint256 = self._mulDiv(_shares, totalBalance, totalShares)
    if _shouldRoundUp and (uint256_mulmod(_shares, totalBalance, totalShares) != 0):
        amount += 1

    return amount


# safe math


@view
@internal
def _mulDiv(_x: uint256, _y: uint256, _d: uint256) -> uint256:
    assert _d != 0 # dev: zero denominator

    lo: uint256 = unsafe_mul(_x, _y)
    mm: uint256 = uint256_mulmod(_x, _y, max_value(uint256))
    hi: uint256 = unsafe_sub(
        unsafe_sub(mm, lo),
        convert(mm < lo, uint256),
    )

    if hi == 0:
        return lo // _d

    assert _d > hi # dev: result overflows

    rem: uint256 = uint256_mulmod(_x, _y, _d)
    hi = unsafe_sub(hi, convert(rem > lo, uint256))
    lo = unsafe_sub(lo, rem)

    tz: uint256 = unsafe_sub(0, _d) & _d
    d2: uint256 = _d // tz
    lo = lo // tz
    lo |= unsafe_mul(
        hi,
        unsafe_add(
            unsafe_div(unsafe_sub(0, tz), tz),
            1,
        ),
    )

    inv: uint256 = unsafe_mul(3, d2) ^ 2
    for i: uint256 in range(6):
        inv = unsafe_mul(
            inv,
            unsafe_sub(2, unsafe_mul(d2, inv)),
        )

    return unsafe_mul(lo, inv)
