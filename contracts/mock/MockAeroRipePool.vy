# @version 0.4.3

poolToken0: address
poolToken1: address
reserve0: public(uint256)
reserve1: public(uint256)
poolTimestamp: public(uint256)
reserveResponseMode: public(uint256)


@deploy
def __init__(_token0: address, _token1: address):
    self.poolToken0 = _token0
    self.poolToken1 = _token1


@view
@external
def tokens() -> (address, address):
    return self.poolToken0, self.poolToken1


@external
def configureState(_reserve0: uint256, _reserve1: uint256, _timestamp: uint256):
    self.reserve0 = _reserve0
    self.reserve1 = _reserve1
    self.poolTimestamp = _timestamp


@external
def setReserveResponseMode(_responseMode: uint256):
    assert _responseMode <= 3
    self.reserveResponseMode = _responseMode


@view
@external
@raw_return
def getReserves() -> Bytes[97]:
    if self.reserveResponseMode == 3:
        raise "forced revert"

    data: Bytes[96] = concat(
        convert(self.reserve0, bytes32),
        convert(self.reserve1, bytes32),
        convert(self.poolTimestamp, bytes32),
    )
    if self.reserveResponseMode == 1:
        return slice(data, 0, 95)
    if self.reserveResponseMode == 2:
        return concat(data, b"x")
    return data
