# @version 0.4.3

governance: public(address)
green: public(address)
savingsGreen: public(address)
ripe: public(address)
priceDesk: public(address)
validRipeAddrs: public(HashMap[address, bool])
pools: public(HashMap[address, bool])
poolCoins: HashMap[address, address[2]]

GREEN_TOKEN_ID: constant(uint256) = 1
SAVINGS_GREEN_ID: constant(uint256) = 2
RIPE_TOKEN_ID: constant(uint256) = 3
SWITCHBOARD_ID: constant(uint256) = 6
PRICE_DESK_ID: constant(uint256) = 7


@deploy
def __init__(
    _governance: address,
    _green: address,
    _savingsGreen: address,
    _ripe: address,
):
    self.governance = _governance
    self.green = _green
    self.savingsGreen = _savingsGreen
    self.ripe = _ripe


@external
def setPool(_pool: address, _altAsset: address, _green: address):
    self.pools[_pool] = True
    self.poolCoins[_pool] = [_altAsset, _green]


@external
def setPoolRegistered(_pool: address, _isRegistered: bool):
    self.pools[_pool] = _isRegistered


@external
def setValidRipeAddr(_addr: address, _isValid: bool):
    self.validRipeAddrs[_addr] = _isValid


@external
def setPriceDesk(_priceDesk: address):
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
    if _regId == GREEN_TOKEN_ID:
        return self.green
    if _regId == SAVINGS_GREEN_ID:
        return self.savingsGreen
    if _regId == RIPE_TOKEN_ID:
        return self.ripe
    if _regId == SWITCHBOARD_ID:
        return self
    if _regId == PRICE_DESK_ID:
        return self.priceDesk
    return empty(address)


@view
@external
def isValidAddr(_addr: address) -> bool:
    return self.validRipeAddrs[_addr]


@view
@external
def isSwitchboardAddr(_addr: address) -> bool:
    return self.validRipeAddrs[_addr]


@view
@external
def get_address(_id: uint256) -> address:
    return self


@view
@external
def is_registered(_pool: address) -> bool:
    return self.pools[_pool]


@view
@external
def get_lp_token(_pool: address) -> address:
    if self.pools[_pool]:
        return _pool
    return empty(address)


@view
@external
def get_n_underlying_coins(_pool: address) -> uint256:
    if self.pools[_pool]:
        return 2
    return 0


@view
@external
def get_underlying_coins(_pool: address) -> address[8]:
    coins: address[2] = self.poolCoins[_pool]
    return [coins[0], coins[1], empty(address), empty(address), empty(address), empty(address), empty(address), empty(address)]


@view
@external
def get_registry_handlers_from_pool(_pool: address) -> address[10]:
    if not self.pools[_pool]:
        return empty(address[10])
    return [self, empty(address), empty(address), empty(address), empty(address), empty(address), empty(address), empty(address), empty(address), empty(address)]


@view
@external
def get_base_registry(_addr: address) -> address:
    if _addr == self:
        return self
    return empty(address)
