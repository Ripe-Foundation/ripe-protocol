# @version 0.4.3

governance: public(address)
priceDesk: public(address)
validRipeAddrs: public(HashMap[address, bool])
validSwitchboardAddrs: public(HashMap[address, bool])

PRICE_DESK_ID: constant(uint256) = 7
SWITCHBOARD_ID: constant(uint256) = 6


@deploy
def __init__(_governance: address, _priceDesk: address):
    self.governance = _governance
    self.priceDesk = _priceDesk


@view
@external
def minGovChangeTimeLock() -> uint256:
    return 1


@view
@external
def maxGovChangeTimeLock() -> uint256:
    return 100


@view
@external
def getAddr(_regId: uint256) -> address:
    if _regId == PRICE_DESK_ID:
        return self.priceDesk
    if _regId == SWITCHBOARD_ID:
        return self
    return empty(address)


@view
@external
def isValidAddr(_addr: address) -> bool:
    return self.validRipeAddrs[_addr]


@view
@external
def isSwitchboardAddr(_addr: address) -> bool:
    return self.validSwitchboardAddrs[_addr]


@external
def setValidRipeAddr(_addr: address, _isValid: bool):
    self.validRipeAddrs[_addr] = _isValid


@external
def setValidSwitchboardAddr(_addr: address, _isValid: bool):
    self.validSwitchboardAddrs[_addr] = _isValid
