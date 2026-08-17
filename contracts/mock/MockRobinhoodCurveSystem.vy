# @version 0.4.3

# Local-only composition harness for Curve AddressProvider, MetaRegistry,
# StableSwapNG registry handler, and a two-coin pool. It is deliberately not a
# production Curve implementation.

coin0: public(address)
coin1: public(address)
registeredPool: public(address)
isPoolRegistered: public(bool)
oraclePrice: public(uint256)
shouldRevert: public(bool)
poolBalances: uint256[2]


@deploy
def __init__(_coin0: address, _coin1: address, _oraclePrice: uint256):
    self.coin0 = _coin0
    self.coin1 = _coin1
    self.registeredPool = self
    self.isPoolRegistered = True
    self.oraclePrice = _oraclePrice


@external
def setRegisteredPool(_pool: address):
    self.registeredPool = _pool


@external
def setRegistered(_registered: bool):
    self.isPoolRegistered = _registered


@external
def setCoins(_coin0: address, _coin1: address):
    self.coin0 = _coin0
    self.coin1 = _coin1


@external
def setOraclePrice(_price: uint256):
    self.oraclePrice = _price


@external
def setShouldRevert(_shouldRevert: bool):
    self.shouldRevert = _shouldRevert


@external
def setBalances(_coin0: uint256, _coin1: uint256):
    # Intentionally permissionless local-test control; this mock is not
    # production authorization evidence.
    self.poolBalances = [_coin0, _coin1]


# Curve AddressProvider


@view
@external
def get_address(_id: uint256) -> address:
    if _id == 7 or _id == 12:
        return self
    return empty(address)


# Curve MetaRegistry / StableSwapNG handler


@view
@external
def is_registered(_pool: address) -> bool:
    return self.isPoolRegistered and _pool == self.registeredPool


@view
@external
def get_lp_token(_pool: address) -> address:
    return _pool


@view
@external
def get_underlying_coins(_pool: address) -> address[8]:
    return [
        self.coin0,
        self.coin1,
        empty(address),
        empty(address),
        empty(address),
        empty(address),
        empty(address),
        empty(address),
    ]


@view
@external
def get_n_underlying_coins(_pool: address) -> uint256:
    return 2


@view
@external
def get_registry_handlers_from_pool(_pool: address) -> address[10]:
    return [
        self,
        empty(address),
        empty(address),
        empty(address),
        empty(address),
        empty(address),
        empty(address),
        empty(address),
        empty(address),
        empty(address),
    ]


@view
@external
def get_base_registry(_handler: address) -> address:
    return self


# StableSwapNG pool response


@view
@external
def price_oracle(_index: uint256) -> uint256:
    assert not self.shouldRevert, "pool revert"
    assert _index == 0, "bad index"
    return self.oraclePrice


@view
@external
def totalSupply() -> uint256:
    return 1


@view
@external
def get_virtual_price() -> uint256:
    return 10**18


@view
@external
def balances(_index: uint256) -> uint256:
    assert _index < 2, "bad index"
    return self.poolBalances[_index]
