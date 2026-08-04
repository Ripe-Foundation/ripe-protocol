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
from ethereum.ercs import IERC20
import contracts.modules.Addys as addys
import contracts.vaults.modules.VaultData as vaultData
import contracts.vaults.modules.BasicVault as basicVault

event GuardedErc20VaultDeposit:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256

event GuardedErc20VaultWithdrawal:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    isDepleted: bool

event GuardedErc20VaultTransfer:
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

    custodyBefore: uint256 = staticcall IERC20(_asset).balanceOf(self)

    nominalBefore: uint256 = vaultData.totalBalances[_asset]
    assert _amount != 0 # dev: invalid deposit amount
    assert custodyBefore >= nominalBefore + _amount # dev: insufficient vault backing

    depositAmount: uint256 = basicVault._depositTokensInVault(_user, _asset, _amount)
    assert depositAmount == _amount # dev: invalid deposit amount

    custodyAfter: uint256 = staticcall IERC20(_asset).balanceOf(self)
    assert custodyAfter == custodyBefore # dev: vault backing changed
    assert vaultData.totalBalances[_asset] == nominalBefore + _amount # dev: invalid nominal accounting

    log GuardedErc20VaultDeposit(user=_user, asset=_asset, amount=depositAmount)
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

    vaultBefore: uint256 = staticcall IERC20(_asset).balanceOf(self)

    nominalBefore: uint256 = vaultData.totalBalances[_asset]
    assert vaultBefore >= nominalBefore # dev: insufficient vault backing

    endaomentFunds: address = addys._getEndaomentFundsAddr()
    if endaomentFunds != empty(address):
        assert _recipient != endaomentFunds # dev: prohibited recipient
    endaomentPsm: address = addys._getEndaomentPsmAddr()
    if endaomentPsm != empty(address):
        assert _recipient != endaomentPsm # dev: prohibited recipient

    recipientBefore: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)

    assert not vaultData.isPaused # dev: contract paused
    assert empty(address) not in [_user, _asset, _recipient] # dev: invalid user, asset, or recipient
    assert _amount != 0 # dev: invalid withdrawal amount

    withdrawalAmount: uint256 = 0
    isDepleted: bool = False
    withdrawalAmount, isDepleted = vaultData._reduceBalanceOnWithdrawal(_user, _asset, _amount, True)
    withdrawalAmount = min(withdrawalAmount, vaultBefore)
    assert withdrawalAmount != 0 # dev: no withdrawal amount
    assert extcall IERC20(_asset).transfer(
        _recipient,
        withdrawalAmount,
        default_return_value=True,
    ) # dev: token transfer failed

    vaultAfter: uint256 = staticcall IERC20(_asset).balanceOf(self)

    recipientAfter: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)

    assert vaultAfter <= vaultBefore and recipientAfter >= recipientBefore # dev: invalid token movement
    assert vaultBefore - vaultAfter == withdrawalAmount # dev: invalid vault outflow
    assert recipientAfter - recipientBefore == withdrawalAmount # dev: invalid recipient delivery
    assert vaultAfter >= vaultData.totalBalances[_asset] # dev: insufficient post-withdraw backing

    log GuardedErc20VaultWithdrawal(user=_user, asset=_asset, amount=withdrawalAmount, isDepleted=isDepleted)
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

    custodyBefore: uint256 = staticcall IERC20(_asset).balanceOf(self)

    nominalBefore: uint256 = vaultData.totalBalances[_asset]
    assert custodyBefore >= nominalBefore # dev: insufficient vault backing
    assert _transferAmount != 0 # dev: invalid transfer amount

    fromUserBefore: uint256 = vaultData.userBalances[_fromUser][_asset]
    toUserBefore: uint256 = vaultData.userBalances[_toUser][_asset]

    transferAmount: uint256 = 0
    isFromUserDepleted: bool = False
    transferAmount, isFromUserDepleted = basicVault._transferBalanceWithinVault(_asset, _fromUser, _toUser, _transferAmount)

    fromUserAfter: uint256 = vaultData.userBalances[_fromUser][_asset]
    toUserAfter: uint256 = vaultData.userBalances[_toUser][_asset]
    assert transferAmount != 0 and transferAmount <= _transferAmount # dev: invalid transfer amount
    assert transferAmount <= fromUserBefore and fromUserAfter <= fromUserBefore # dev: invalid seller accounting
    assert toUserAfter >= toUserBefore # dev: invalid buyer accounting
    assert fromUserBefore - fromUserAfter == transferAmount # dev: invalid seller accounting
    assert toUserAfter - toUserBefore == transferAmount # dev: invalid buyer accounting
    assert vaultData.totalBalances[_asset] == nominalBefore # dev: invalid nominal accounting

    custodyAfter: uint256 = staticcall IERC20(_asset).balanceOf(self)
    assert custodyAfter == custodyBefore # dev: vault backing changed
    assert custodyAfter >= nominalBefore # dev: insufficient post-transfer backing

    log GuardedErc20VaultTransfer(fromUser=_fromUser, toUser=_toUser, asset=_asset, transferAmount=transferAmount, isFromUserDepleted=isFromUserDepleted)
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
    # used in Lootbox.vy; reward policy remains external configuration
    return basicVault._getUserLootBoxShare(_user, _asset)


@view
@external
def getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
    # used in CreditEngine.vy
    asset: address = vaultData.userAssets[_user][_index]
    if asset == empty(address):
        return empty(address), 0

    nominalAmount: uint256 = vaultData.userBalances[_user][asset]
    if nominalAmount == 0:
        return empty(address), 0

    if staticcall IERC20(asset).balanceOf(self) < vaultData.totalBalances[asset]:
        return asset, 0
    return asset, nominalAmount


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
    nominalAmount: uint256 = vaultData.userBalances[_user][_asset]
    if nominalAmount == 0 or staticcall IERC20(_asset).balanceOf(self) < vaultData.totalBalances[_asset]:
        return 0
    return nominalAmount


@view
@external
def getTotalAmountForVault(_asset: address) -> uint256:
    return basicVault._getTotalAmountForVault(_asset)
