# @version 0.4.3
# Successful sharesToAmount that ABI-encodes dynamic bytes so the raw
# return length is not 32. Vyper 0.4.3 has no raw_return builtin.

usable: public(uint256)
shares: public(uint256)
loot: public(uint256)
payload: public(Bytes[64])


@external
def configure(_usable: uint256, _shares: uint256, _loot: uint256, _payload: Bytes[64]):
    self.usable = _usable
    self.shares = _shares
    self.loot = _loot
    self.payload = _payload


@view
@external
def getUserLootBoxShare(_user: address, _asset: address) -> uint256:
    return self.loot


@view
@external
def getTotalAmountForVault(_asset: address) -> uint256:
    return self.usable


@view
@external
def totalBalances(_asset: address) -> uint256:
    return self.shares


@view
@external
def sharesToAmount(_asset: address, _shares: uint256, _shouldRoundUp: bool) -> Bytes[64]:
    return self.payload
