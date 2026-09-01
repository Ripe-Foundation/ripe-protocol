# @version 0.4.3
# Successful totalBalances that is not a canonical 32-byte uint256.

usable: public(uint256)
loot: public(uint256)
payload: public(Bytes[64])


@external
def configure(_usable: uint256, _loot: uint256, _payload: Bytes[64]):
    self.usable = _usable
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
def totalBalances(_asset: address) -> Bytes[64]:
    return self.payload
