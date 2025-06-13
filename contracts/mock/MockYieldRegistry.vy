# @version 0.4.1

assets: public(DynArray[address, MAX_VAL])

MAX_VAL: constant(uint256) = 50


@deploy
def __init__(_assets: DynArray[address, MAX_VAL]):
    self.assets = _assets


# compound v2 (moonwell)


@view
@external
def getAllMarkets() -> DynArray[address, MAX_VAL]:
    return self.assets


# fluid


@view
@external
def getAllFTokens() -> DynArray[address, MAX_VAL]:
    return self.assets


# compound v3


@view
@external
def factory(_asset: address) -> address:
    return _asset


# euler 


@view
@external
def isValidDeployment(_vault: address) -> bool:
    return True


@view
@external
def isProxy(_vault: address) -> bool:
    return True


# morpho


@view
@external
def isMetaMorpho(_vault: address) -> bool:
    return True


# sky


@view
@external
def usdc() -> address:
    return empty(address)


@view
@external
def usds() -> address:
    return empty(address)


@view
@external
def susds() -> address:
    return empty(address)
