# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

uses: vaultData
import contracts.vaults.modules.VaultData as vaultData

from interfaces import Vault
from ethereum.ercs import IERC20


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
) -> uint256:
    assert not vaultData.isPaused # dev: contract paused

    # validation
    assert empty(address) not in [_user, _asset] # dev: invalid user or asset
    assert _amount != 0 # dev: invalid deposit amount

    # check actual vault backing
    custodyBefore: uint256 = staticcall IERC20(_asset).balanceOf(self)
    nominalBefore: uint256 = vaultData.totalBalances[_asset]
    assert custodyBefore >= nominalBefore + _amount # dev: insufficient vault backing

    # add balance on deposit
    vaultData._addBalanceOnDeposit(_user, _asset, _amount, True)

    return _amount


@internal
def _withdrawTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
) -> (uint256, bool):
    assert not vaultData.isPaused # dev: contract paused

    # validation
    assert empty(address) not in [_user, _asset, _recipient] # dev: invalid user, asset, or recipient
    assert _amount != 0 # dev: invalid withdrawal amount

    # check pre withdrawal values
    vaultBefore: uint256 = staticcall IERC20(_asset).balanceOf(self)
    assert vaultBefore >= vaultData.totalBalances[_asset] # dev: insufficient vault backing
    recipientBefore: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)

    # reduce balance on withdrawal
    withdrawalAmount: uint256 = 0
    isDepleted: bool = False
    withdrawalAmount, isDepleted = vaultData._reduceBalanceOnWithdrawal(_user, _asset, _amount, True)

    # move tokens to recipient
    withdrawalAmount = min(withdrawalAmount, vaultBefore)
    assert withdrawalAmount != 0 # dev: no withdrawal amount
    assert extcall IERC20(_asset).transfer(_recipient, withdrawalAmount, default_return_value=True) # dev: token transfer failed

    # check post withdrawal values
    vaultAfter: uint256 = staticcall IERC20(_asset).balanceOf(self)
    recipientAfter: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)
    assert vaultBefore - vaultAfter == withdrawalAmount # dev: invalid vault outflow
    assert recipientAfter - recipientBefore == withdrawalAmount # dev: invalid recipient delivery

    return withdrawalAmount, isDepleted


@internal
def _transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
) -> (uint256, bool):
    assert not vaultData.isPaused # dev: contract paused

    # validation
    assert empty(address) not in [_fromUser, _toUser, _asset] # dev: invalid users or asset
    assert _transferAmount != 0 # dev: invalid transfer amount
    assert _fromUser != _toUser # dev: invalid transfer users
    assert staticcall IERC20(_asset).balanceOf(self) >= vaultData.totalBalances[_asset] # dev: insufficient vault backing

    # transfer balances
    transferAmount: uint256 = 0
    isFromUserDepleted: bool = False
    transferAmount, isFromUserDepleted = vaultData._reduceBalanceOnWithdrawal(_fromUser, _asset, _transferAmount, False)
    vaultData._addBalanceOnDeposit(_toUser, _asset, transferAmount, False)

    return transferAmount, isFromUserDepleted


####################
# Needs For Others #
####################


@view
@internal
def _getVaultDataOnDeposit(_user: address, _asset: address) -> Vault.VaultDataOnDeposit:
    # used in Teller.vy
    return Vault.VaultDataOnDeposit(
        hasPosition=vaultData.indexOfUserAsset[_user][_asset] != 0,
        numAssets=vaultData._getNumUserAssets(_user),
        userBalance=vaultData.userBalances[_user][_asset],
        totalBalance=vaultData.totalBalances[_asset],
    )


@view
@internal
def _getUserLootBoxShare(_user: address, _asset: address) -> uint256:
    # used in Lootbox.vy
    return vaultData.userBalances[_user][_asset]


@view
@internal
def _getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
    # used in CreditEngine.vy
    asset: address = vaultData.userAssets[_user][_index]
    if asset == empty(address):
        return empty(address), 0

    nominalAmount: uint256 = vaultData.userBalances[_user][asset]

    # preserve the registered asset even when its nominal amount is zero so
    # CreditEngine continues to include its configured debt terms
    if staticcall IERC20(asset).balanceOf(self) < vaultData.totalBalances[asset]:
        return asset, 0

    return asset, nominalAmount


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
    nominalAmount: uint256 = vaultData.userBalances[_user][_asset]
    if nominalAmount == 0 or staticcall IERC20(_asset).balanceOf(self) < vaultData.totalBalances[_asset]:
        return 0
    return nominalAmount


@view
@internal
def _getTotalAmountForVault(_asset: address) -> uint256:
    totalBalance: uint256 = vaultData.totalBalances[_asset]
    if staticcall IERC20(_asset).balanceOf(self) < totalBalance:
        return 0
    return totalBalance
