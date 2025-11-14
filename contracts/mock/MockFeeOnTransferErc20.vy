# @dev ERC20 with transfer fee (like some real tokens)
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

name: public(constant(String[32])) = "Fee Token"
symbol: public(constant(String[32])) = "FEE"
decimals: public(constant(uint8)) = 18

balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

# Fee configuration (in basis points, e.g., 100 = 1%)
transferFeeBps: public(uint256)
feeRecipient: public(address)

hq: public(address)


@deploy
def __init__(_hq: address, _feeBps: uint256):
    assert _feeBps <= 10000  # Max 100%
    self.hq = _hq
    self.transferFeeBps = _feeBps
    self.feeRecipient = _hq

    # Mint initial supply
    init_supply: uint256 = 1_000_000 * 10**18
    self.balanceOf[_hq] = init_supply
    self.totalSupply = init_supply
    log Transfer(sender=empty(address), receiver=_hq, value=init_supply)


@external
def setTransferFee(_feeBps: uint256):
    """Update transfer fee"""
    assert msg.sender == self.hq
    assert _feeBps <= 10000
    self.transferFeeBps = _feeBps


@external
def setFeeRecipient(_recipient: address):
    """Update fee recipient"""
    assert msg.sender == self.hq
    assert _recipient != empty(address)
    self.feeRecipient = _recipient


@internal
def _transferWithFee(_from: address, _to: address, _value: uint256) -> bool:
    """Internal transfer that deducts fee"""
    # Calculate fee
    fee: uint256 = (_value * self.transferFeeBps) // 10000
    amountAfterFee: uint256 = _value - fee

    # Deduct from sender
    self.balanceOf[_from] -= _value

    # Add to recipient (minus fee)
    self.balanceOf[_to] += amountAfterFee

    # Add fee to fee recipient (could be burned instead)
    if fee > 0 and self.feeRecipient != empty(address):
        self.balanceOf[self.feeRecipient] += fee

    # Event logs the gross amount (before fee)
    log Transfer(sender=_from, receiver=_to, value=_value)

    return True


@external
def transfer(_to: address, _value: uint256) -> bool:
    """Transfer with fee deduction"""
    return self._transferWithFee(msg.sender, _to, _value)


@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    """TransferFrom with fee deduction"""
    # Check and decrease allowance
    self.allowance[_from][msg.sender] -= _value

    return self._transferWithFee(_from, _to, _value)


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
