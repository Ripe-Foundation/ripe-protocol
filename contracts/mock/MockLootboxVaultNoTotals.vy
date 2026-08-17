# @version 0.4.3
# No totalBalances selector. Used for fail-closed fallback tests.

usable: public(uint256)
loot: public(uint256)


@external
def configure(_usable: uint256, _loot: uint256):
    self.usable = _usable
    self.loot = _loot


@view
@external
def getUserLootBoxShare(_user: address, _asset: address) -> uint256:
    return self.loot


@view
@external
def getTotalAmountForVault(_asset: address) -> uint256:
    return self.usable
