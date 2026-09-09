# @version 0.4.3

# Each selector has an independent raw-return mode. Modes match
# MockMorphoV2Factory, with mode 5 returning a selector-specific incompatible
# word (out-of-range address/decimals, otherwise max uint256).

underlying: public(address)
shareDecimals: public(uint256)
supply: public(uint256)
pricePerShare: public(uint256)
conversionOverride: public(uint256)
hasConversionOverride: public(bool)

assetMode: public(uint256)
decimalsMode: public(uint256)
supplyMode: public(uint256)
convertMode: public(uint256)


@deploy
def __init__(_underlying: address, _decimals: uint256, _supply: uint256, _pricePerShare: uint256):
    self.underlying = _underlying
    self.shareDecimals = _decimals
    self.supply = _supply
    self.pricePerShare = _pricePerShare


@external
def setModes(_assetMode: uint256, _decimalsMode: uint256, _supplyMode: uint256, _convertMode: uint256):
    assert _assetMode <= 5 and _decimalsMode <= 5 and _supplyMode <= 5 and _convertMode <= 5
    self.assetMode = _assetMode
    self.decimalsMode = _decimalsMode
    self.supplyMode = _supplyMode
    self.convertMode = _convertMode


@external
def setPricePerShare(_pricePerShare: uint256):
    self.pricePerShare = _pricePerShare


@external
def setSupply(_supply: uint256):
    self.supply = _supply


@external
def setConversionOverride(_value: uint256, _enabled: bool):
    self.conversionOverride = _value
    self.hasConversionOverride = _enabled


@view
@internal
def _rawWord(_value: uint256, _mode: uint256, _incompatible: uint256) -> Bytes[33]:
    if _mode == 1:
        raise
    if _mode == 2:
        return b""
    if _mode == 3:
        return b"\x01"
    if _mode == 4:
        return concat(convert(_value, bytes32), b"\x00")
    if _mode == 5:
        return slice(convert(_incompatible, bytes32), 0, 32)
    return slice(convert(_value, bytes32), 0, 32)


@view
@external
@raw_return
def asset() -> Bytes[33]:
    return self._rawWord(convert(self.underlying, uint256), self.assetMode, max_value(uint256))


@view
@external
@raw_return
def decimals() -> Bytes[33]:
    return self._rawWord(self.shareDecimals, self.decimalsMode, 78)


@view
@external
@raw_return
def totalSupply() -> Bytes[33]:
    return self._rawWord(self.supply, self.supplyMode, max_value(uint256))


@view
@external
@raw_return
def convertToAssets(_shares: uint256) -> Bytes[33]:
    if self.convertMode == 5:
        return self._rawWord(0, self.convertMode, max_value(uint256))
    if self.hasConversionOverride:
        return self._rawWord(self.conversionOverride, self.convertMode, max_value(uint256))
    value: uint256 = _shares * self.pricePerShare // (10 ** self.shareDecimals)
    return self._rawWord(value, self.convertMode, max_value(uint256))
