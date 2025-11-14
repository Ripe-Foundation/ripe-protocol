# @dev Malicious ERC20 that attempts reentrancy during transfer
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

name: public(constant(String[32])) = "Reentrant Token"
symbol: public(constant(String[32])) = "REENT"
decimals: public(constant(uint8)) = 18

balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

# Attack configuration
attackTarget: public(address)
attackEnabled: public(bool)
attackExecuted: public(bool)

hq: public(address)


@deploy
def __init__(_hq: address):
    self.hq = _hq
    # Mint initial supply to hq
    init_supply: uint256 = 1_000_000 * 10**18
    self.balanceOf[_hq] = init_supply
    self.totalSupply = init_supply
    log Transfer(sender=empty(address), receiver=_hq, value=init_supply)


@external
def setAttackTarget(_target: address):
    """Configure the contract to attack during transfer"""
    assert msg.sender == self.hq
    self.attackTarget = _target
    self.attackEnabled = True
    self.attackExecuted = False


@external
def disableAttack():
    """Disable attack mode"""
    assert msg.sender == self.hq
    self.attackEnabled = False


@external
def transfer(_to: address, _value: uint256) -> bool:
    """Transfer with reentrancy attack"""
    # Execute attack before state changes (if enabled and not yet executed)
    if self.attackEnabled and not self.attackExecuted and self.attackTarget != empty(address):
        self.attackExecuted = True
        # Try to reenter the target contract
        # Attempt to call hasBalance() which is a simple read function
        # This tests if the contract is protected against reentrancy
        success: bool = False
        response: Bytes[32] = b""
        success, response = raw_call(
            self.attackTarget,
            method_id("hasBalance(address)", output_type=Bytes[4]),
            max_outsize=32,
            revert_on_failure=False,
            is_delegate_call=False,
            is_static_call=False
        )
        # We don't care about the result, just attempting the reentrant call

    # Normal transfer logic
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    log Transfer(sender=msg.sender, receiver=_to, value=_value)
    return True


@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    """TransferFrom with potential reentrancy"""
    # Check allowance
    self.allowance[_from][msg.sender] -= _value

    # Execute attack if enabled
    if self.attackEnabled and not self.attackExecuted and self.attackTarget != empty(address):
        self.attackExecuted = True
        # Try to reenter by calling hasBalance()
        success: bool = False
        response: Bytes[32] = b""
        success, response = raw_call(
            self.attackTarget,
            method_id("hasBalance(address)", output_type=Bytes[4]),
            max_outsize=32,
            revert_on_failure=False,
            is_delegate_call=False,
            is_static_call=False
        )
        # We don't care about the result, just attempting the reentrant call

    # Normal transfer logic
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    log Transfer(sender=_from, receiver=_to, value=_value)
    return True


@external
def approve(_spender: address, _value: uint256) -> bool:
    """Standard approve"""
    self.allowance[msg.sender][_spender] = _value
    log Approval(owner=msg.sender, spender=_spender, value=_value)
    return True


@external
def mint(_to: address, _value: uint256):
    """Mint tokens"""
    assert msg.sender == self.hq
    assert _to != empty(address)
    self.totalSupply += _value
    self.balanceOf[_to] += _value
    log Transfer(sender=empty(address), receiver=_to, value=_value)
