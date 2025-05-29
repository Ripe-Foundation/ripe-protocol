# @version 0.4.1

implements: Vault

exports: addys.__interface__
exports: vaultData.__interface__
exports: sharesVault.__interface__

initializes: addys
initializes: vaultData[addys := addys]
initializes: sharesVault[vaultData := vaultData]

from interfaces import Vault
import contracts.modules.Addys as addys
import contracts.vaults.modules.VaultData as vaultData
import contracts.vaults.modules.SharesVault as sharesVault
from ethereum.ercs import IERC20

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


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    vaultData.__init__(False)
    sharesVault.__init__()


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
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed

    depositAmount: uint256 = 0
    newShares: uint256 = 0
    depositAmount, newShares = sharesVault._depositTokensInVault(_user, _asset, _amount)
    log RebaseErc20VaultDeposit(user=_user, asset=_asset, amount=depositAmount, shares=newShares)
    return depositAmount


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
    withdrawalShares: uint256 = 0
    isDepleted: bool = False
    withdrawalAmount, withdrawalShares, isDepleted = sharesVault._withdrawTokensFromVault(_user, _asset, _amount, _recipient)
    log RebaseErc20VaultWithdrawal(user=_user, asset=_asset, amount=withdrawalAmount, isDepleted=isDepleted, shares=withdrawalShares)
    return withdrawalAmount, isDepleted


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
    transferShares: uint256 = 0
    isFromUserDepleted: bool = False
    transferAmount, transferShares, isFromUserDepleted = sharesVault._transferBalanceWithinVault(_asset, _fromUser, _toUser, _transferAmount)
    log RebaseErc20VaultTransfer(fromUser=_fromUser, toUser=_toUser, asset=_asset, transferAmount=transferAmount, isFromUserDepleted=isFromUserDepleted, transferShares=transferShares)
    return transferAmount, isFromUserDepleted


####################
# Needs For Others #
####################


@view
@external
def getVaultDataOnDeposit(_user: address, _asset: address) -> Vault.VaultDataOnDeposit:
    # used in Teller.vy
    return sharesVault._getVaultDataOnDeposit(_user, _asset)


@view
@external
def getUserLootBoxShare(_user: address, _asset: address) -> uint256:
    # used in Lootbox.vy
    return sharesVault._getUserLootBoxShare(_user, _asset)


@view
@external
def getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
    # used in CreditEngine.vy
    return sharesVault._getUserAssetAndAmountAtIndex(_user, _index)


@view
@external
def getUserAssetAtIndexAndHasBalance(_user: address, _index: uint256) -> (address, bool):
    # used in Lootbox.vy and AuctionHouse.vy
    return sharesVault._getUserAssetAtIndexAndHasBalance(_user, _index)


###############
# Other Utils #
###############


@view
@external
def getTotalAmountForUser(_user: address, _asset: address) -> uint256:
    return sharesVault._getTotalAmountForUser(_user, _asset)


@view
@external
def getTotalAmountForVault(_asset: address) -> uint256:
    return sharesVault._getTotalAmountForVault(_asset)
