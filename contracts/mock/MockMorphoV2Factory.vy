# @version 0.4.3

# Raw-return modes used to prove exact ABI handling by BlueChipYieldPrices.
# 0 = canonical bool, 1 = revert, 2 = empty, 3 = short, 4 = long,
# 5 = non-canonical true word.

isSupported: public(HashMap[address, bool])
responseMode: public(uint256)


@external
def setVault(_vault: address, _isSupported: bool):
    self.isSupported[_vault] = _isSupported


@external
def setResponseMode(_mode: uint256):
    assert _mode <= 5
    self.responseMode = _mode


@view
@external
@raw_return
def isVaultV2(_vault: address) -> Bytes[33]:
    mode: uint256 = self.responseMode
    if mode == 1:
        raise
    if mode == 2:
        return b""
    if mode == 3:
        return b"\x01"
    if mode == 4:
        return concat(convert(1, bytes32), b"\x00")
    if mode == 5:
        return slice(convert(2, bytes32), 0, 32)
    return slice(convert(self.isSupported[_vault], bytes32), 0, 32)
