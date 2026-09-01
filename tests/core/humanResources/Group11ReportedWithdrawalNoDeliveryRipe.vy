# @version 0.4.3

# Test-only runtime swapped onto the live RIPE address. Storage slots 0-11
# match Erc20Token. transfer changes no stored balances: only the calling
# vault sees virtual sender/recipient deltas, while HumanResources sees the
# real zero delivery.

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
balances: HashMap[address, uint256]
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)
nonces: public(HashMap[address, uint256])

reportedVault: public(address)
reportedRecipient: public(address)
reportedAmount: public(uint256)


@view
@external
def balanceOf(_user: address) -> uint256:
    balance: uint256 = self.balances[_user]
    if self.reportedAmount != 0 and msg.sender == self.reportedVault:
        if _user == self.reportedVault:
            return balance - self.reportedAmount
        if _user == self.reportedRecipient:
            return balance + self.reportedAmount
    return balance


@external
def transfer(_recipient: address, _amount: uint256) -> bool:
    assert self.balances[msg.sender] >= _amount
    self.reportedVault = msg.sender
    self.reportedRecipient = _recipient
    self.reportedAmount = _amount
    return True


@external
def burn(_amount: uint256) -> bool:
    # Backstop: the successful test path proves a zero actual burn skips this call.
    return False
