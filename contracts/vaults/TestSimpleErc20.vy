# @version 0.4.1

implements: Vault

exports: addys.__interface__
exports: vaultData.__interface__

initializes: addys
initializes: vaultData[addys := addys]
initializes: simpleErc20Vault[addys := addys, vaultData := vaultData]

from interfaces import Vault
import contracts.modules.Addys as addys
import contracts.modules.VaultData as vaultData
import contracts.modules.SimpleErc20Vault as simpleErc20Vault
from ethereum.ercs import IERC20

event TestSimpleErc20VaultDeposit:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256

event TestSimpleErc20VaultWithdrawal:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    isDepleted: bool

event TestSimpleErc20VaultTransfer:
    fromUser: indexed(address)
    toUser: indexed(address)
    asset: indexed(address)
    transferAmount: uint256
    isFromUserDepleted: bool


@deploy
def __init__(_hq: address):
    addys.__init__(_hq)
    vaultData.__init__()
    simpleErc20Vault.__init__()


########
# Core #
########


@external
def depositTokensInVault(
    _user: address,
    _asset: address,
    _amount: uint256,
) -> uint256:
    depositAmount: uint256 = simpleErc20Vault._depositTokensInVault(_user, _asset, _amount)
    log TestSimpleErc20VaultDeposit(user=_user, asset=_asset, amount=depositAmount)
    return depositAmount


@external
def withdrawTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
) -> (uint256, bool):
    withdrawalAmount: uint256 = 0
    isDepleted: bool = False
    withdrawalAmount, isDepleted = simpleErc20Vault._withdrawTokensFromVault(_user, _asset, _amount, _recipient)
    log TestSimpleErc20VaultWithdrawal(user=_user, asset=_asset, amount=withdrawalAmount, isDepleted=isDepleted)
    return withdrawalAmount, isDepleted


@external
def transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
) -> (uint256, bool):
    transferAmount: uint256 = 0
    isFromUserDepleted: bool = False
    transferAmount, isFromUserDepleted = simpleErc20Vault._transferBalanceWithinVault(_asset, _fromUser, _toUser, _transferAmount)
    log TestSimpleErc20VaultTransfer(fromUser=_fromUser, toUser=_toUser, asset=_asset, transferAmount=transferAmount, isFromUserDepleted=isFromUserDepleted)
    return transferAmount, isFromUserDepleted


####################
# Needs For Others #
####################


@view
@external
def getVaultDataOnDeposit(_user: address, _asset: address) -> Vault.VaultDataOnDeposit:
    # used in Teller.vy
    return simpleErc20Vault._getVaultDataOnDeposit(_user, _asset)


@view
@external
def getUserLootBoxShare(_user: address, _asset: address) -> uint256:
    # used in Lootbox.vy
    return simpleErc20Vault._getUserLootBoxShare(_user, _asset)


@view
@external
def getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
    # used in CreditEngine.vy
    return simpleErc20Vault._getUserAssetAndAmountAtIndex(_user, _index)


@view
@external
def getUserAssetAtIndexAndHasBalance(_user: address, _index: uint256) -> (address, bool):
    # used in Lootbox.vy and AuctionHouse.vy
    return simpleErc20Vault._getUserAssetAtIndexAndHasBalance(_user, _index)


###############
# Other Utils #
###############


@view
@external
def getTotalAmountForUser(_user: address, _asset: address) -> uint256:
    return simpleErc20Vault._getTotalAmountForUser(_user, _asset)


@view
@external
def getTotalAmountForVault(_asset: address) -> uint256:
    return simpleErc20Vault._getTotalAmountForVault(_asset)
