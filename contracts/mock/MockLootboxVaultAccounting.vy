# @version 0.4.3

usable: public(uint256)
shares: public(uint256)
loot: public(uint256)
mode: public(uint256)
converted: public(uint256)


@external
def configure(
    _usable: uint256,
    _shares: uint256,
    _loot: uint256,
    _mode: uint256,
    _converted: uint256,
):
    self.usable = _usable
    self.shares = _shares
    self.loot = _loot
    self.mode = _mode
    self.converted = _converted


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
    if self.mode == 5:
        raise "reverting totals"
    return self.shares


@view
@external
def sharesToAmount(_asset: address, _shares: uint256, _shouldRoundUp: bool) -> uint256:
    if self.mode == 1 or self.mode == 5:
        raise "reverting conversion"
    if self.mode == 4:
        return 0
    return self.converted
