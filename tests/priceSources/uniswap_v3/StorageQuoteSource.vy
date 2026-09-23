# @version 0.4.3
# Cold SLOAD cost fixture. Metadata warming is deliberately adversarial.
QUOTE: immutable(address)
loadCount: public(uint256)
warmMetadata: public(bool)
values: HashMap[uint256, uint256]
@deploy
def __init__(quote: address, count: uint256, warm: bool):
    QUOTE = quote if quote != empty(address) else self
    assert count <= 110
    self.loadCount = count
    self.warmMetadata = warm
    for i: uint256 in range(110):
        self.values[i] = i + 1
@external
def configure(count: uint256, warm: bool = False):
    assert count <= 110
    self.loadCount = count
    self.warmMetadata = warm
@view
@internal
def _touch() -> uint256:
    value: uint256 = 0
    for i: uint256 in range(self.loadCount, bound=110):
        value += self.values[i]
    return value
@view
@external
def decimals() -> uint256:
    if self.warmMetadata:
        assert self._touch() != 0
    return 18
@view
@external
def getPriceAndHasFeed(asset: address, staleTime: uint256 = 0, desk: address = empty(address)) -> (uint256, bool):
    if asset != QUOTE:
        return 0, False
    value: uint256 = self._touch()
    return (10 ** 18 if value != 0 or self.loadCount == 0 else 0), True
@view
@external
def hasPriceFeed(asset: address) -> bool:
    return asset == QUOTE
@external
def addPriceSnapshot(asset: address) -> bool:
    return False
