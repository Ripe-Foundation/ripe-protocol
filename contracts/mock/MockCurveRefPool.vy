# @version 0.4.3

poolBalances: uint256[2]


@external
def setBalances(_altBalance: uint256, _greenBalance: uint256):
    self.poolBalances[0] = _altBalance
    self.poolBalances[1] = _greenBalance


@view
@external
def balances(_index: uint256) -> uint256:
    assert _index < 2
    return self.poolBalances[_index]


@view
@external
def totalSupply() -> uint256:
    return self.poolBalances[0] + self.poolBalances[1]


@view
@external
def get_virtual_price() -> uint256:
    return 10 ** 18


@view
@external
def price_oracle(_index: uint256 = 0) -> uint256:
    return 10 ** 18


@view
@external
def lp_price() -> uint256:
    return 10 ** 18
