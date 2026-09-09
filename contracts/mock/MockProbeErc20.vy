# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026

# @dev ERC-20 test double for transfer-probe behavior.
# @version 0.4.3

from ethereum.ercs import IERC20

implements: IERC20


event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    value: uint256


name: public(constant(String[32])) = "Probe Test Token"
symbol: public(constant(String[32])) = "PROBE"
decimals: public(constant(uint8)) = 18

balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

controller: public(address)
paused: public(bool)
returnFalse: public(bool)
revertTransfers: public(bool)
isBlocked: public(HashMap[address, bool])


@deploy
def __init__(_controller: address, _supply: uint256):
    assert _controller != empty(address)
    self.controller = _controller
    self.balanceOf[_controller] = _supply
    self.totalSupply = _supply
    log Transfer(sender=empty(address), receiver=_controller, value=_supply)


@internal
def _validateTransfer(_from: address, _to: address):
    assert not self.revertTransfers, "mock transfer reverted"
    assert not self.paused, "token paused"
    assert not self.isBlocked[_from], "sender blocked"
    assert not self.isBlocked[_to], "recipient blocked"
    assert not self.isBlocked[msg.sender], "operator blocked"


@external
def transfer(_to: address, _value: uint256) -> bool:
    self._validateTransfer(msg.sender, _to)
    if self.returnFalse:
        return False

    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    log Transfer(sender=msg.sender, receiver=_to, value=_value)
    return True


@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    self._validateTransfer(_from, _to)
    if self.returnFalse:
        return False

    self.allowance[_from][msg.sender] -= _value
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    log Transfer(sender=_from, receiver=_to, value=_value)
    return True


@external
def approve(_spender: address, _value: uint256) -> bool:
    assert not self.paused, "token paused"
    assert not self.isBlocked[msg.sender], "owner blocked"
    assert not self.isBlocked[_spender], "spender blocked"
    self.allowance[msg.sender][_spender] = _value
    log Approval(owner=msg.sender, spender=_spender, value=_value)
    return True


@external
def setPaused(_paused: bool):
    assert msg.sender == self.controller
    self.paused = _paused


@external
def setBlocked(_account: address, _blocked: bool):
    assert msg.sender == self.controller
    self.isBlocked[_account] = _blocked


@external
def setReturnFalse(_returnFalse: bool):
    assert msg.sender == self.controller
    self.returnFalse = _returnFalse


@external
def setRevertTransfers(_revertTransfers: bool):
    assert msg.sender == self.controller
    self.revertTransfers = _revertTransfers
