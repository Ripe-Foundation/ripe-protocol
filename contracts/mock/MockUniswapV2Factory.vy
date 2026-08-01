# @version 0.4.3

pairs: HashMap[address, HashMap[address, address]]
shouldRevert: public(bool)
responseMode: public(uint256)


@external
def setPair(_tokenA: address, _tokenB: address, _pair: address):
    self.pairs[_tokenA][_tokenB] = _pair
    self.pairs[_tokenB][_tokenA] = _pair


@external
def setShouldRevert(_shouldRevert: bool):
    self.shouldRevert = _shouldRevert


@external
def setResponseMode(_responseMode: uint256):
    self.responseMode = _responseMode


@view
@external
@raw_return
def getPair(_tokenA: address, _tokenB: address) -> Bytes[33]:
    assert not self.shouldRevert
    value: bytes32 = convert(self.pairs[_tokenA][_tokenB], bytes32)
    if self.responseMode == 1:
        return slice(value, 0, 31)
    if self.responseMode == 2:
        return concat(value, b"x")
    return slice(value, 0, 32)
