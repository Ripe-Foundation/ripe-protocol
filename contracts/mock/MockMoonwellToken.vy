# @version 0.4.3

underlying: public(address)
exchangeRate: public(uint256)
totalSupply: public(uint256)
shareDecimals: public(uint8)
shouldRevert: public(bool)


@deploy
def __init__(
    _underlying: address,
    _exchangeRate: uint256,
    _totalSupply: uint256,
    _shareDecimals: uint8,
):
    self.underlying = _underlying
    self.exchangeRate = _exchangeRate
    self.totalSupply = _totalSupply
    self.shareDecimals = _shareDecimals


@external
def setExchangeRate(_exchangeRate: uint256):
    self.exchangeRate = _exchangeRate


@external
def setShouldRevert(_shouldRevert: bool):
    self.shouldRevert = _shouldRevert


@view
@external
def exchangeRateStored() -> uint256:
    if self.shouldRevert:
        raise
    return self.exchangeRate


@view
@external
def decimals() -> uint8:
    return self.shareDecimals
