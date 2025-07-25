# @dev Implementation of ERC-20 token standard.
# @author Takayuki Jimba (@yudetamago)
# https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20.md

# @version 0.4.3

from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed

implements: IERC20
implements: IERC20Detailed

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    value: uint256

event MinterUpdated:
    minter: indexed(address)
    canMint: bool

name: public(String[32])
symbol: public(String[32])
decimals: public(uint8)

# NOTE: By declaring `balanceOf` as public, vyper automatically generates a 'balanceOf()' getter
#       method to allow access to account balances.
#       The _KeyType will become a required parameter for the getter and it will return _ValueType.
#       See: https://vyper.readthedocs.io/en/v0.1.0-beta.8/types.html?highlight=getter#mappings
balanceOf: public(HashMap[address, uint256])
# By declaring `allowance` as public, vyper automatically generates the `allowance()` getter
allowance: public(HashMap[address, HashMap[address, uint256]])
# By declaring `totalSupply` as public, we automatically create the `totalSupply()` getter
totalSupply: public(uint256)

# governance
hq: public(address)
isMinter: public(HashMap[address, bool])


@deploy
def __init__(_hq: address, _name: String[32], _symbol: String[32], _decimals: uint8, _supply: uint256):
    assert _hq != empty(address) # dev: cannot be 0x0
    self.hq = _hq
    self.isMinter[_hq] = True

    self.name = _name
    self.symbol = _symbol
    self.decimals = _decimals

    init_supply: uint256 = _supply * 10 ** convert(_decimals, uint256)
    if init_supply != 0:
        self.balanceOf[_hq] = init_supply
        self.totalSupply = init_supply
        log Transfer(sender=empty(address), receiver=_hq, value=init_supply)


@external
def transfer(_to : address, _value : uint256) -> bool:
    """
    @dev Transfer token for a specified address
    @param _to The address to transfer to.
    @param _value The amount to be transferred.
    """
    # NOTE: vyper does not allow underflows
    #       so the following subtraction would revert on insufficient balance
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    log Transfer(sender=msg.sender, receiver=_to, value=_value)
    return True


@external
def transferFrom(_from : address, _to : address, _value : uint256) -> bool:
    """
     @dev Transfer tokens from one address to another.
     @param _from address The address which you want to send tokens from
     @param _to address The address which you want to transfer to
     @param _value uint256 the amount of tokens to be transferred
    """
    # NOTE: vyper does not allow underflows
    #       so the following subtraction would revert on insufficient balance
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    # NOTE: vyper does not allow underflows
    #      so the following subtraction would revert on insufficient allowance
    self.allowance[_from][msg.sender] -= _value
    log Transfer(sender=_from, receiver=_to, value=_value)
    return True


@external
def approve(_spender : address, _value : uint256) -> bool:
    """
    @dev Approve the passed address to spend the specified amount of tokens on behalf of msg.sender.
         Beware that changing an allowance with this method brings the risk that someone may use both the old
         and the new allowance by unfortunate transaction ordering. One possible solution to mitigate this
         race condition is to first reduce the spender's allowance to 0 and set the desired value afterwards:
         https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
    @param _spender The address which will spend the funds.
    @param _value The amount of tokens to be spent.
    """
    self.allowance[msg.sender][_spender] = _value
    log Approval(owner=msg.sender, spender=_spender, value=_value)
    return True


@external
def mint(_to: address, _value: uint256):
    """
    @dev Mint an amount of the token and assigns it to an account.
         This encapsulates the modification of balances such that the
         proper events are emitted.
    @param _to The account that will receive the created tokens.
    @param _value The amount that will be created.
    """
    assert self.isMinter[msg.sender]
    assert _to != empty(address)
    self.totalSupply += _value
    self.balanceOf[_to] += _value
    log Transfer(sender=empty(address), receiver=_to, value=_value)


@internal
def _burn(_to: address, _value: uint256):
    """
    @dev Internal function that burns an amount of the token of a given
         account.
    @param _to The account whose tokens will be burned.
    @param _value The amount that will be burned.
    """
    assert _to != empty(address)
    self.totalSupply -= _value
    self.balanceOf[_to] -= _value
    log Transfer(sender=_to, receiver=empty(address), value=_value)


@external
def burn(_value: uint256) -> bool:
    """
    @dev Burn an amount of the token of msg.sender.
    @param _value The amount that will be burned.
    """
    self._burn(msg.sender, _value)
    return True


@external
def burnFrom(_to: address, _value: uint256):
    """
    @dev Burn an amount of the token from a given account.
    @param _to The account whose tokens will be burned.
    @param _value The amount that will be burned.
    """
    self.allowance[_to][msg.sender] -= _value
    self._burn(_to, _value)


@external
def setMinter(_minter: address, _canMint: bool) -> bool:
    assert msg.sender == self.hq
    assert _minter != empty(address) and _minter != self.hq
    self.isMinter[_minter] = _canMint
    log MinterUpdated(minter=_minter, canMint=_canMint)
    return True
