# @version 0.4.1

initializes: stratData
initializes: gov

exports: stratData.__interface__
exports: gov.__interface__

import contracts.modules.StratData as stratData
import contracts.modules.LocalGov as gov
from ethereum.ercs import IERC20

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

event RebaseErc20StratDeposit:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    shares: uint256

event RebaseErc20StratWithdrawal:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    isDepleted: bool
    shares: uint256

event RebaseErc20StratTransfer:
    fromUser: indexed(address)
    toUser: indexed(address)
    asset: indexed(address)
    transferAmount: uint256
    isFromUserDepleted: bool
    transferShares: uint256

event RebaseErc20StratActivated:
    isActivated: bool

# registry ids
TELLER_ID: constant(uint256) = 1 # TODO: make sure this is correct
LEDGER_ID: constant(uint256) = 2 # TODO: make sure this is correct

# config
ADDY_REGISTRY: public(immutable(address))
isActivated: public(bool)

DECIMAL_OFFSET: constant(uint256) = (10 ** 8)


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True

    # initialize modules
    stratData.__init__()
    gov.__init__(empty(address), _addyRegistry, 0, 0)


########
# Core #
########


@external
def depositTokensInStrat(
    _user: address,
    _asset: address,
    _amount: uint256,
) -> uint256:
    assert self.isActivated # dev: not activated
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(TELLER_ID) # dev: only Teller allowed

    # validation
    assert empty(address) not in [_user, _asset] # dev: invalid user or asset
    totalAssetBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    depositAmount: uint256 = min(_amount, totalAssetBalance)
    assert depositAmount != 0 # dev: invalid deposit amount

    # calc shares
    prevTotalBalance: uint256 = totalAssetBalance - depositAmount # remove the deposited amount to calc shares accurately
    newShares: uint256 = self._amountToShares(_asset, depositAmount, stratData.totalBalances[_asset], prevTotalBalance, False)

    # add balance on deposit
    stratData._addBalanceOnDeposit(_user, _asset, newShares, True)

    log RebaseErc20StratDeposit(user=_user, asset=_asset, amount=depositAmount, shares=newShares)
    return depositAmount


@external
def withdrawTokensFromStrat(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
) -> (uint256, bool):
    assert self.isActivated # dev: not activated
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
    withdrawalShares, isDepleted = stratData._reduceBalanceOnWithdrawal(_user, _asset, withdrawalShares, True)

    # move tokens to recipient
    withdrawalAmount = min(withdrawalAmount, staticcall IERC20(_asset).balanceOf(self))
    assert withdrawalAmount != 0 # dev: no withdrawal amount
    assert extcall IERC20(_asset).transfer(_recipient, withdrawalAmount, default_return_value=True) # dev: token transfer failed

    log RebaseErc20StratWithdrawal(user=_user, asset=_asset, amount=withdrawalAmount, isDepleted=isDepleted, shares=withdrawalShares)
    return withdrawalAmount, isDepleted


@external
def transferTokenBalance(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
) -> (uint256, bool):
    assert self.isActivated # dev: not activated
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
    transferShares, isFromUserDepleted = stratData._reduceBalanceOnWithdrawal(_fromUser, _asset, transferShares, False)
    stratData._addBalanceOnDeposit(_toUser, _asset, transferShares, False)

    log RebaseErc20StratTransfer(fromUser=_fromUser, toUser=_toUser, asset=_asset, transferAmount=transferAmount, isFromUserDepleted=isFromUserDepleted, transferShares=transferShares)
    return transferAmount, isFromUserDepleted


@view
@internal
def _calcWithdrawalSharesAndAmount(
    _user: address,
    _asset: address,
    _amount: uint256,
) -> (uint256, uint256):
    totalShares: uint256 = stratData.totalBalances[_asset]
    totalBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)

    # user shares
    withdrawalShares: uint256 = stratData._getUserBalance(_user, _asset)
    assert withdrawalShares != 0 # dev: user has no shares

    # calc amount + shares to withdraw
    withdrawalAmount: uint256 = self._sharesToAmount(_asset, withdrawalShares, totalShares, totalBalance, False)
    if _amount < withdrawalAmount:
        withdrawalShares = min(withdrawalShares, self._amountToShares(_asset, _amount, totalShares, totalBalance, True))
        withdrawalAmount = _amount

    return withdrawalShares, withdrawalAmount


##########
# Shares #
##########


@view
@internal
def _amountToShares(
    _asset: address,
    _amount: uint256,
    _totalShares: uint256,
    _totalBalance: uint256,
    _shouldRoundUp: bool,
) -> uint256:
    totalBalance: uint256 = _totalBalance

    # dead shares / decimal offset -- preventing donation attacks
    totalBalance += 1
    totalShares: uint256 = _totalShares + DECIMAL_OFFSET

    # calc shares
    numerator: uint256 = _amount * totalShares
    shares: uint256 = numerator // totalBalance

    # rounding
    if _shouldRoundUp and (numerator % totalBalance != 0):
        shares += 1

    return shares


@view
@external
def amountToShares(_asset: address, _amount: uint256, _shouldRoundUp: bool) -> uint256:
    totalShares: uint256 = stratData.totalBalances[_asset]
    totalBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    return self._amountToShares(_asset, _amount, totalShares, totalBalance, _shouldRoundUp)


@view
@internal
def _sharesToAmount(
    _asset: address,
    _shares: uint256,
    _totalShares: uint256,
    _totalBalance: uint256,
    _shouldRoundUp: bool,
) -> uint256:
    totalBalance: uint256 = _totalBalance

    # dead shares / decimal offset -- preventing donation attacks
    totalBalance += 1
    totalShares: uint256 = _totalShares + DECIMAL_OFFSET

    # calc amount
    numerator: uint256 = _shares * totalBalance
    amount: uint256 = numerator // totalShares

    # rounding
    if _shouldRoundUp and (numerator % totalShares != 0):
        amount += 1

    return amount


@view
@external
def sharesToAmount(_asset: address, _shares: uint256, _shouldRoundUp: bool) -> uint256:
    totalShares: uint256 = stratData.totalBalances[_asset]
    totalBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    return self._sharesToAmount(_asset, _shares, totalShares, totalBalance, _shouldRoundUp)


########
# Ripe #
########


@external
def activate(_shouldActivate: bool):
    assert gov._canGovern(msg.sender) # dev: no perms
    self.isActivated = _shouldActivate
    log RebaseErc20StratActivated(isActivated=_shouldActivate)