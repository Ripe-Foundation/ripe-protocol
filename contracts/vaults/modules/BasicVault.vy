# @version 0.4.1

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
    depositAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(self))
    assert depositAmount != 0 # dev: invalid deposit amount

    # add balance on deposit
    vaultData._addBalanceOnDeposit(_user, _asset, depositAmount, True)

    return depositAmount


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

    # reduce balance on withdrawal
    withdrawalAmount: uint256 = 0
    isDepleted: bool = False
    withdrawalAmount, isDepleted = vaultData._reduceBalanceOnWithdrawal(_user, _asset, _amount, True)

    # move tokens to recipient
    withdrawalAmount = min(withdrawalAmount, staticcall IERC20(_asset).balanceOf(self))
    assert withdrawalAmount != 0 # dev: no withdrawal amount
    assert extcall IERC20(_asset).transfer(_recipient, withdrawalAmount, default_return_value=True) # dev: token transfer failed

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
    return asset, vaultData.userBalances[_user][asset]


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
    return vaultData.userBalances[_user][_asset]


@view
@internal
def _getTotalAmountForVault(_asset: address) -> uint256:
    return vaultData.totalBalances[_asset]
