# @version 0.4.1

implements: Vault

initializes: gov
initializes: vaultData
initializes: sharesMath

exports: gov.__interface__
exports: vaultData.__interface__

import contracts.modules.LocalGov as gov
import contracts.modules.VaultData as vaultData
import contracts.modules.SharesMath as sharesMath
from interfaces import Vault
from ethereum.ercs import IERC20

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

event RebaseErc20VaultDeposit:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    shares: uint256

event RebaseErc20VaultWithdrawal:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    isDepleted: bool
    shares: uint256

event RebaseErc20VaultTransfer:
    fromUser: indexed(address)
    toUser: indexed(address)
    asset: indexed(address)
    transferAmount: uint256
    isFromUserDepleted: bool
    transferShares: uint256

TELLER_ID: constant(uint256) = 1 # TODO: make sure this is correct
LEDGER_ID: constant(uint256) = 2 # TODO: make sure this is correct
VAULT_BOOK_ID: constant(uint256) = 3 # TODO: make sure this is correct

ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry

    # initialize modules
    gov.__init__(empty(address), _addyRegistry, 0, 0)
    vaultData.__init__()
    sharesMath.__init__()


########
# Core #
########


@external
def depositTokensInVault(
    _user: address,
    _asset: address,
    _amount: uint256,
) -> uint256:
    assert vaultData.isActivated # dev: not activated
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(TELLER_ID) # dev: only Teller allowed

    # validation
    assert empty(address) not in [_user, _asset] # dev: invalid user or asset
    totalAssetBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    depositAmount: uint256 = min(_amount, totalAssetBalance)
    assert depositAmount != 0 # dev: invalid deposit amount

    # calc shares
    prevTotalBalance: uint256 = totalAssetBalance - depositAmount # remove the deposited amount to calc shares accurately
    newShares: uint256 = sharesMath._amountToShares(_asset, depositAmount, vaultData.totalBalances[_asset], prevTotalBalance, False)

    # add balance on deposit
    vaultData._addBalanceOnDeposit(_user, _asset, newShares, True)

    log RebaseErc20VaultDeposit(user=_user, asset=_asset, amount=depositAmount, shares=newShares)
    return depositAmount


@external
def withdrawTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
) -> (uint256, bool):
    assert vaultData.isActivated # dev: not activated
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(TELLER_ID) # dev: only Teller allowed

    # validation
    assert empty(address) not in [_user, _asset, _recipient] # dev: invalid user, asset, or recipient
    assert _amount != 0 # dev: invalid amount

    # calc shares + amount to withdraw
    withdrawalShares: uint256 = 0
    withdrawalAmount: uint256 = 0
    withdrawalShares, withdrawalAmount = self._calcWithdrawalSharesAndAmount(_user, _asset, _amount)

    # reduce balance on withdrawal
    isDepleted: bool = False
    withdrawalShares, isDepleted = vaultData._reduceBalanceOnWithdrawal(_user, _asset, withdrawalShares, True)

    # move tokens to recipient
    withdrawalAmount = min(withdrawalAmount, staticcall IERC20(_asset).balanceOf(self))
    assert withdrawalAmount != 0 # dev: no withdrawal amount
    assert extcall IERC20(_asset).transfer(_recipient, withdrawalAmount, default_return_value=True) # dev: token transfer failed

    # deregister user asset if depleted
    if isDepleted:
        vaultData._deregisterUserAsset(_user, _asset)

    log RebaseErc20VaultWithdrawal(user=_user, asset=_asset, amount=withdrawalAmount, isDepleted=isDepleted, shares=withdrawalShares)
    return withdrawalAmount, isDepleted


@external
def transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
) -> (uint256, bool):
    assert vaultData.isActivated # dev: not activated
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(LEDGER_ID) # dev: only Ledger allowed

    # validation
    assert empty(address) not in [_fromUser, _toUser, _asset] # dev: invalid users or asset
    assert _transferAmount != 0 # dev: invalid amount

    # calc shares + amount to transfer
    transferShares: uint256 = 0
    transferAmount: uint256 = 0
    transferShares, transferAmount = self._calcWithdrawalSharesAndAmount(_fromUser, _asset, _transferAmount)

    # transfer shares
    isFromUserDepleted: bool = False
    transferShares, isFromUserDepleted = vaultData._reduceBalanceOnWithdrawal(_fromUser, _asset, transferShares, False)
    vaultData._addBalanceOnDeposit(_toUser, _asset, transferShares, False)

    log RebaseErc20VaultTransfer(fromUser=_fromUser, toUser=_toUser, asset=_asset, transferAmount=transferAmount, isFromUserDepleted=isFromUserDepleted, transferShares=transferShares)
    return transferAmount, isFromUserDepleted


@view
@internal
def _calcWithdrawalSharesAndAmount(
    _user: address,
    _asset: address,
    _amount: uint256,
) -> (uint256, uint256):
    totalShares: uint256 = vaultData.totalBalances[_asset]
    totalBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)

    # user shares
    withdrawalShares: uint256 = vaultData.userBalances[_user][_asset]
    assert withdrawalShares != 0 # dev: user has no shares

    # calc amount + shares to withdraw
    withdrawalAmount: uint256 = sharesMath._sharesToAmount(_asset, withdrawalShares, totalShares, totalBalance, False)
    if _amount < withdrawalAmount:
        withdrawalShares = min(withdrawalShares, sharesMath._amountToShares(_asset, _amount, totalShares, totalBalance, True))
        withdrawalAmount = _amount

    return withdrawalShares, withdrawalAmount


##########
# Shares #
##########


@view
@external
def amountToShares(_asset: address, _amount: uint256, _shouldRoundUp: bool) -> uint256:
    totalShares: uint256 = vaultData.totalBalances[_asset]
    totalBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    return sharesMath._amountToShares(_asset, _amount, totalShares, totalBalance, _shouldRoundUp)


@view
@external
def sharesToAmount(_asset: address, _shares: uint256, _shouldRoundUp: bool) -> uint256:
    totalShares: uint256 = vaultData.totalBalances[_asset]
    totalBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    return sharesMath._sharesToAmount(_asset, _shares, totalShares, totalBalance, _shouldRoundUp)


########
# Ripe #
########


@external
def deregisterUserAsset(_user: address, _asset: address):
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(LEDGER_ID) # dev: only Ledger allowed
    vaultData._deregisterUserAsset(_user, _asset)


@external
def deregisterVaultAsset(_asset: address):
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(LEDGER_ID) # dev: only Ledger allowed
    vaultData._deregisterVaultAsset(_asset)


@external
def recoverFunds(_asset: address, _recipient: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return vaultData._recoverFunds(_asset, _recipient)


@external
def setVaultId(_vaultId: uint256) -> bool:
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(VAULT_BOOK_ID) # dev: no perms
    return vaultData._setVaultId(_vaultId)


@external
def activate(_shouldActivate: bool):
    assert gov._canGovern(msg.sender) # dev: no perms
    vaultData._activate(_shouldActivate)
