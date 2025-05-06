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

event SimpleErc20StratDeposit:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256

event SimpleErc20StratWithdrawal:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    isDepleted: bool

event SimpleErc20StratTransfer:
    fromUser: indexed(address)
    toUser: indexed(address)
    asset: indexed(address)
    transferAmount: uint256
    isFromUserDepleted: bool

event SimpleErc20StratActivated:
    isActivated: bool

# registry ids
TELLER_ID: constant(uint256) = 1 # TODO: make sure this is correct
LEDGER_ID: constant(uint256) = 2 # TODO: make sure this is correct

# config
ADDY_REGISTRY: public(immutable(address))
isActivated: public(bool)


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
    depositAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(self))
    assert depositAmount != 0 # dev: invalid deposit amount

    # add balance on deposit
    stratData._addBalanceOnDeposit(_user, _asset, depositAmount, True)

    log SimpleErc20StratDeposit(user=_user, asset=_asset, amount=depositAmount)
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

    # reduce balance on withdrawal
    withdrawalAmount: uint256 = 0
    isDepleted: bool = False
    withdrawalAmount, isDepleted = stratData._reduceBalanceOnWithdrawal(_user, _asset, _amount, True)

    # move tokens to recipient
    withdrawalAmount = min(withdrawalAmount, staticcall IERC20(_asset).balanceOf(self))
    assert withdrawalAmount != 0 # dev: no withdrawal amount
    assert extcall IERC20(_asset).transfer(_recipient, withdrawalAmount, default_return_value=True) # dev: token transfer failed

    log SimpleErc20StratWithdrawal(user=_user, asset=_asset, amount=withdrawalAmount, isDepleted=isDepleted)
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

    # transfer balances
    transferAmount: uint256 = 0
    isFromUserDepleted: bool = False
    transferAmount, isFromUserDepleted = stratData._reduceBalanceOnWithdrawal(_fromUser, _asset, _transferAmount, False)
    stratData._addBalanceOnDeposit(_toUser, _asset, transferAmount, False)

    log SimpleErc20StratTransfer(fromUser=_fromUser, toUser=_toUser, asset=_asset, transferAmount=transferAmount, isFromUserDepleted=isFromUserDepleted)
    return transferAmount, isFromUserDepleted


########
# Ripe #
########


@external
def activate(_shouldActivate: bool):
    assert gov._canGovern(msg.sender) # dev: no perms
    self.isActivated = _shouldActivate
    log SimpleErc20StratActivated(isActivated=_shouldActivate)