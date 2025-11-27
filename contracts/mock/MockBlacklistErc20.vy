# @dev ERC20 with blacklist functionality (like USDC/USDT)
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

event Blacklisted:
    account: indexed(address)

event UnBlacklisted:
    account: indexed(address)

name: public(constant(String[32])) = "Blacklist Token"
symbol: public(constant(String[32])) = "BLST"
decimals: public(constant(uint8)) = 18

balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

# Blacklist mapping
isBlacklisted: public(HashMap[address, bool])

hq: public(address)


@deploy
def __init__(_hq: address):
    self.hq = _hq

    # Mint initial supply
    init_supply: uint256 = 1_000_000 * 10**18
    self.balanceOf[_hq] = init_supply
    self.totalSupply = init_supply
    log Transfer(sender=empty(address), receiver=_hq, value=init_supply)


@external
def blacklist(_account: address):
    """Add account to blacklist"""
    assert msg.sender == self.hq
    assert _account != empty(address)
    self.isBlacklisted[_account] = True
    log Blacklisted(account=_account)


@external
def unblacklist(_account: address):
    """Remove account from blacklist"""
    assert msg.sender == self.hq
    self.isBlacklisted[_account] = False
    log UnBlacklisted(account=_account)


@external
def transfer(_to: address, _value: uint256) -> bool:
    """Transfer with blacklist check"""
    assert not self.isBlacklisted[msg.sender], "sender blacklisted"
    assert not self.isBlacklisted[_to], "recipient blacklisted"

    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    log Transfer(sender=msg.sender, receiver=_to, value=_value)
    return True


@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    """TransferFrom with blacklist check"""
    assert not self.isBlacklisted[_from], "from blacklisted"
    assert not self.isBlacklisted[_to], "to blacklisted"
    assert not self.isBlacklisted[msg.sender], "caller blacklisted"

    self.allowance[_from][msg.sender] -= _value
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    log Transfer(sender=_from, receiver=_to, value=_value)
    return True


@external
def approve(_spender: address, _value: uint256) -> bool:
    """Standard approve"""
    assert not self.isBlacklisted[msg.sender], "sender blacklisted"
    assert not self.isBlacklisted[_spender], "spender blacklisted"

    self.allowance[msg.sender][_spender] = _value
    log Approval(owner=msg.sender, spender=_spender, value=_value)
    return True


@external
def mint(_to: address, _value: uint256):
    """Mint tokens"""
    assert msg.sender == self.hq
    assert _to != empty(address)
    assert not self.isBlacklisted[_to], "recipient blacklisted"

    self.totalSupply += _value
    self.balanceOf[_to] += _value
    log Transfer(sender=empty(address), receiver=_to, value=_value)
