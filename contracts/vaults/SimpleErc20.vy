# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

implements: Vault

exports: addys.__interface__
exports: vaultData.__interface__

initializes: addys
initializes: vaultData[addys := addys]
initializes: basicVault[vaultData := vaultData]

from interfaces import Vault
import contracts.modules.Addys as addys
import contracts.vaults.modules.VaultData as vaultData
import contracts.vaults.modules.BasicVault as basicVault
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
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    vaultData.__init__(False)
    basicVault.__init__()


########
# Core #
########


@nonreentrant
@external
def depositTokensInVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed

    depositAmount: uint256 = basicVault._depositTokensInVault(_user, _asset, _amount)
    log SimpleErc20VaultDeposit(user=_user, asset=_asset, amount=depositAmount)
    return depositAmount


@nonreentrant
@external
def withdrawTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
    _a: addys.Addys = empty(addys.Addys),
) -> (uint256, bool):
    assert msg.sender in [addys._getTellerAddr(), addys._getAuctionHouseAddr(), addys._getCreditEngineAddr()] # dev: not allowed

    withdrawalAmount: uint256 = 0
    isDepleted: bool = False
    withdrawalAmount, isDepleted = basicVault._withdrawTokensFromVault(_user, _asset, _amount, _recipient)
    log SimpleErc20VaultWithdrawal(user=_user, asset=_asset, amount=withdrawalAmount, isDepleted=isDepleted)
    return withdrawalAmount, isDepleted


@nonreentrant
@external
def transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> (uint256, bool):
    assert msg.sender in [addys._getAuctionHouseAddr(), addys._getCreditEngineAddr()] # dev: not allowed

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
