# @version 0.4.1

implements: Vault

exports: addys.__interface__
exports: vaultData.__interface__

initializes: addys
initializes: vaultData[addys := addys]
initializes: basicVault[addys := addys, vaultData := vaultData]

from interfaces import Vault
import contracts.modules.Addys as addys
import contracts.modules.VaultData as vaultData
import contracts.modules.BasicVault as basicVault
from ethereum.ercs import IERC20

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


@deploy
def __init__(_ripeHq: address, _initialVaultBook: address):
    addys.__init__(_ripeHq)
    vaultData.__init__(_initialVaultBook)
    basicVault.__init__()


########
# Core #
########


@external
def depositTokensInVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    depositAmount: uint256 = basicVault._depositTokensInVault(_user, _asset, _amount)
    log SimpleErc20VaultDeposit(user=_user, asset=_asset, amount=depositAmount)
    return depositAmount


@external
def withdrawTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
    _a: addys.Addys = empty(addys.Addys),
) -> (uint256, bool):
    withdrawalAmount: uint256 = 0
    isDepleted: bool = False
    withdrawalAmount, isDepleted = basicVault._withdrawTokensFromVault(_user, _asset, _amount, _recipient)
    log SimpleErc20VaultWithdrawal(user=_user, asset=_asset, amount=withdrawalAmount, isDepleted=isDepleted)
    return withdrawalAmount, isDepleted


@external
def transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> (uint256, bool):
    transferAmount: uint256 = 0
    isFromUserDepleted: bool = False
    transferAmount, isFromUserDepleted = basicVault._transferBalanceWithinVault(_asset, _fromUser, _toUser, _transferAmount)
    log SimpleErc20VaultTransfer(fromUser=_fromUser, toUser=_toUser, asset=_asset, transferAmount=transferAmount, isFromUserDepleted=isFromUserDepleted)
    return transferAmount, isFromUserDepleted


####################
# Needs For Others #
####################


@view
@external
def getVaultDataOnDeposit(_user: address, _asset: address) -> Vault.VaultDataOnDeposit:
    # used in Teller.vy
    return basicVault._getVaultDataOnDeposit(_user, _asset)


@view
@external
def getUserLootBoxShare(_user: address, _asset: address) -> uint256:
    # used in Lootbox.vy
    return basicVault._getUserLootBoxShare(_user, _asset)


@view
@external
def getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
    # used in CreditEngine.vy
    return basicVault._getUserAssetAndAmountAtIndex(_user, _index)


@view
@external
def getUserAssetAtIndexAndHasBalance(_user: address, _index: uint256) -> (address, bool):
    # used in Lootbox.vy and AuctionHouse.vy
    return basicVault._getUserAssetAtIndexAndHasBalance(_user, _index)


###############
# Other Utils #
###############


@view
@external
def getTotalAmountForUser(_user: address, _asset: address) -> uint256:
    return basicVault._getTotalAmountForUser(_user, _asset)


@view
@external
def getTotalAmountForVault(_asset: address) -> uint256:
    return basicVault._getTotalAmountForVault(_asset)
