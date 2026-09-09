# @version 0.4.3

price: public(uint256)
shouldRevert: public(bool)
responseMode: public(uint256)
recursiveTarget: public(address)
recursiveAsset: public(address)
recursiveStaleTime: public(uint256)


interface PriceSource:
    def getPrice(_asset: address, _staleTime: uint256, _oracleRegistry: address) -> uint256: view


@external
def setPrice(_price: uint256):
    self.price = _price


@external
def setShouldRevert(_shouldRevert: bool):
    self.shouldRevert = _shouldRevert


@external
def setResponseMode(_responseMode: uint256):
    self.responseMode = _responseMode


@external
def setRecursion(_target: address, _asset: address, _staleTime: uint256):
    self.recursiveTarget = _target
    self.recursiveAsset = _asset
    self.recursiveStaleTime = _staleTime


@external
def consume(_source: address, _asset: address, _staleTime: uint256) -> uint256:
    return staticcall PriceSource(_source).getPrice(_asset, _staleTime, self)


@view
@external
@raw_return
def getPrice(_asset: address, _shouldRaise: bool = False) -> Bytes[96]:
    assert not self.shouldRevert
    value: uint256 = self.price
    if self.recursiveTarget != empty(address):
        value = staticcall PriceSource(self.recursiveTarget).getPrice(
            self.recursiveAsset,
            self.recursiveStaleTime,
            self,
        )
    encoded: bytes32 = convert(value, bytes32)
    if self.responseMode == 1:
        return slice(encoded, 0, 31)
    if self.responseMode == 2:
        return concat(encoded, b"x")
    if self.responseMode == 3:
        return concat(encoded, empty(bytes32), empty(bytes32))
    return slice(encoded, 0, 32)
