# @version 0.4.1

implements: Vault

initializes: vaultData
initializes: gov

exports: vaultData.__interface__
exports: gov.__interface__

import contracts.modules.VaultData as vaultData
import contracts.modules.LocalGov as gov
from interfaces import Vault
from ethereum.ercs import IERC20

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

event SimpleErc20VaultDeposit:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256

event SimpleErc20VaultWithdrawal:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    isDepleted: bool

event SimpleErc20VaultTransfer:
    fromUser: indexed(address)
    toUser: indexed(address)
    asset: indexed(address)
    transferAmount: uint256
    isFromUserDepleted: bool

TELLER_ID: constant(uint256) = 1 # TODO: make sure this is correct
LEDGER_ID: constant(uint256) = 2 # TODO: make sure this is correct
VAULT_BOOK_ID: constant(uint256) = 3 # TODO: make sure this is correct

ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry

    # initialize modules
    vaultData.__init__()
    gov.__init__(empty(address), _addyRegistry, 0, 0)


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
    depositAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(self))
    assert depositAmount != 0 # dev: invalid deposit amount

    # add balance on deposit
    vaultData._addBalanceOnDeposit(_user, _asset, depositAmount, True)

    log SimpleErc20VaultDeposit(user=_user, asset=_asset, amount=depositAmount)
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

    # reduce balance on withdrawal
    withdrawalAmount: uint256 = 0
    isDepleted: bool = False
    withdrawalAmount, isDepleted = vaultData._reduceBalanceOnWithdrawal(_user, _asset, _amount, True)

    # move tokens to recipient
    withdrawalAmount = min(withdrawalAmount, staticcall IERC20(_asset).balanceOf(self))
    assert withdrawalAmount != 0 # dev: no withdrawal amount
    assert extcall IERC20(_asset).transfer(_recipient, withdrawalAmount, default_return_value=True) # dev: token transfer failed

    log SimpleErc20VaultWithdrawal(user=_user, asset=_asset, amount=withdrawalAmount, isDepleted=isDepleted)
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

    # transfer balances
    transferAmount: uint256 = 0
    isFromUserDepleted: bool = False
    transferAmount, isFromUserDepleted = vaultData._reduceBalanceOnWithdrawal(_fromUser, _asset, _transferAmount, False)
    vaultData._addBalanceOnDeposit(_toUser, _asset, transferAmount, False)

    log SimpleErc20VaultTransfer(fromUser=_fromUser, toUser=_toUser, asset=_asset, transferAmount=transferAmount, isFromUserDepleted=isFromUserDepleted)
    return transferAmount, isFromUserDepleted


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