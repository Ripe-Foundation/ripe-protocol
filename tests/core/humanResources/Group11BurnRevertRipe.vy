# @version 0.4.3

# Test-only runtime swapped onto the live RIPE address. Storage layout
# matches Erc20Token module slots 0-11 so transfer can move real balances
# while burn reverts.

struct PendingHq:
    newHq: address
    initiatedBlock: uint256
    confirmBlock: uint256

ripeHq: public(address)
blacklisted: public(HashMap[address, bool])
isPaused: public(bool)
pendingHq: public(PendingHq)
hqChangeTimeLock: public(uint256)
tempGov: address
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)
nonces: public(HashMap[address, uint256])


@external
def transfer(_recipient: address, _amount: uint256) -> bool:
    self.balanceOf[msg.sender] -= _amount
    self.balanceOf[_recipient] += _amount
    return True


@external
def burn(_amount: uint256) -> bool:
    # Runtime-dependent: `assert False` is a compile-time StaticAssertion.
    # HR only calls burn when burnAmount != 0, so this always reverts
    # after a successful vault transfer.
    assert _amount == 0  # dev: burn mutant revert
    return False
