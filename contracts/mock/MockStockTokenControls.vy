# @dev Test-only ERC-20 mock for issuer-controlled Stock Token behavior.
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

event TokenPauseModified:
    isPaused: bool

event SenderBlocklistModified:
    account: indexed(address)
    isBlocked: bool

event RecipientBlocklistModified:
    account: indexed(address)
    isBlocked: bool

event OperatorBlocklistModified:
    account: indexed(address)
    isBlocked: bool

event UpgradeBehaviorModified:
    mode: uint256

name: public(constant(String[32])) = "Mock Stock Token"
symbol: public(constant(String[32])) = "MSTOCK"
decimals: public(immutable(uint8))

balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

admin: public(immutable(address))
isPaused: public(bool)
isSenderBlocked: public(HashMap[address, bool])
isRecipientBlocked: public(HashMap[address, bool])
isOperatorBlocked: public(HashMap[address, bool])

# Test-only implementation-upgrade stand-in:
# 0 = ordinary behavior; 1 = transfers revert; 2 = transfers return false;
# 3 = transfers burn one base unit from each nonzero amount.
upgradeBehavior: public(uint256)


@deploy
def __init__(_admin: address, _decimals: uint8):
    assert _admin != empty(address)
    admin = _admin
    decimals = _decimals


@internal
def _assertAdmin():
    assert msg.sender == admin, "only admin"


@internal
def _transfer(_operator: address, _from: address, _to: address, _value: uint256) -> bool:
    assert not self.isPaused, "token paused"
    assert not self.isSenderBlocked[_from], "sender blocked"
    assert not self.isRecipientBlocked[_to], "recipient blocked"
    assert not self.isOperatorBlocked[_operator], "operator blocked"
    assert self.upgradeBehavior != 1, "upgrade rejects transfers"

    if self.upgradeBehavior == 2:
        return False

    received: uint256 = _value
    if self.upgradeBehavior == 3 and _value != 0:
        received -= 1
        self.totalSupply -= 1

    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += received
    log Transfer(sender=_from, receiver=_to, value=received)
    if received != _value:
        log Transfer(sender=_from, receiver=empty(address), value=_value - received)
    return True


@external
def transfer(_to: address, _value: uint256) -> bool:
    return self._transfer(msg.sender, msg.sender, _to, _value)


@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    self.allowance[_from][msg.sender] -= _value
    return self._transfer(msg.sender, _from, _to, _value)


@external
def approve(_spender: address, _value: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _value
    log Approval(owner=msg.sender, spender=_spender, value=_value)
    return True


@external
def mint(_to: address, _value: uint256):
    self._assertAdmin()
    assert _to != empty(address)
    self.totalSupply += _value
    self.balanceOf[_to] += _value
    log Transfer(sender=empty(address), receiver=_to, value=_value)


@external
def adminBurn(_holder: address, _value: uint256):
    self._assertAdmin()
    self.balanceOf[_holder] -= _value
    self.totalSupply -= _value
    log Transfer(sender=_holder, receiver=empty(address), value=_value)


@external
def forceTransfer(_from: address, _to: address, _value: uint256):
    self._assertAdmin()
    assert _to != empty(address)
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    log Transfer(sender=_from, receiver=_to, value=_value)


@external
def forceRedeem(_holder: address, _value: uint256):
    self._assertAdmin()
    self.balanceOf[_holder] -= _value
    self.totalSupply -= _value
    log Transfer(sender=_holder, receiver=empty(address), value=_value)


@external
def setPaused(_shouldPause: bool):
    self._assertAdmin()
    assert _shouldPause != self.isPaused
    self.isPaused = _shouldPause
    log TokenPauseModified(isPaused=_shouldPause)


@external
def setSenderBlocked(_account: address, _isBlocked: bool):
    self._assertAdmin()
    self.isSenderBlocked[_account] = _isBlocked
    log SenderBlocklistModified(account=_account, isBlocked=_isBlocked)


@external
def setRecipientBlocked(_account: address, _isBlocked: bool):
    self._assertAdmin()
    self.isRecipientBlocked[_account] = _isBlocked
    log RecipientBlocklistModified(account=_account, isBlocked=_isBlocked)


@external
def setOperatorBlocked(_account: address, _isBlocked: bool):
    self._assertAdmin()
    self.isOperatorBlocked[_account] = _isBlocked
    log OperatorBlocklistModified(account=_account, isBlocked=_isBlocked)


@external
def setUpgradeBehavior(_mode: uint256):
    self._assertAdmin()
    assert _mode <= 3
    self.upgradeBehavior = _mode
    log UpgradeBehaviorModified(mode=_mode)
