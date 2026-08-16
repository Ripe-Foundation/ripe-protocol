# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

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

MAX_TRANSFER_DELTA: constant(uint256) = 2

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


@nonreentrant
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
    withdrawalShares: uint256 = 0
    isDepleted: bool = False
    withdrawalAmount, withdrawalShares, isDepleted = self._withdrawTokensFromVault(_user, _asset, _amount, _recipient)
    log RebaseErc20VaultWithdrawal(user=_user, asset=_asset, amount=withdrawalAmount, isDepleted=isDepleted, shares=withdrawalShares)
    return withdrawalAmount, isDepleted


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
    requestedShares, requestedAmount = sharesVault._calcWithdrawalSharesAndAmount(_user, _asset, _amount)

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
        withdrawalShares = min(
            userSharesBefore,
            sharesVault._amountToShares(
                actualOutflow,
                totalSharesBefore,
                vaultBefore,
                True,
            ),
        )
    assert withdrawalShares != 0 # dev: cannot withdraw 0 shares
    assert self._preservesRemainingClaim(
        withdrawalShares,
        totalSharesBefore,
        vaultBefore,
        actualOutflow,
    ) # dev: remaining holder loss

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
def _isWithinTransferDelta(_actual: uint256, _requested: uint256) -> bool:
    if _actual >= _requested:
        return _actual - _requested <= MAX_TRANSFER_DELTA
    return _requested - _actual <= MAX_TRANSFER_DELTA


@view
@internal
def _preservesRemainingClaim(
    _withdrawalShares: uint256,
    _totalShares: uint256,
    _vaultBalance: uint256,
    _vaultOutflow: uint256,
) -> bool:
    assert _withdrawalShares <= _totalShares # dev: invalid withdrawal shares
    assert _vaultOutflow <= _vaultBalance # dev: invalid vault outflow
    remainingShares: uint256 = _totalShares - _withdrawalShares
    if remainingShares == 0:
        return True
    remainingClaimBefore: uint256 = sharesVault._sharesToAmount(
        remainingShares,
        _totalShares,
        _vaultBalance,
        False,
    )
    remainingClaimAfter: uint256 = sharesVault._sharesToAmount(
        remainingShares,
        remainingShares,
        _vaultBalance - _vaultOutflow,
        False,
    )
    return remainingClaimAfter >= remainingClaimBefore


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
