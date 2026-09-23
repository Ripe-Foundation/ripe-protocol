# @version 0.4.3
# Deliberately violates the operator quote-source rule for cycle regression tests.
interface Desk:
    def getPrice(asset: address, shouldRaise: bool = False) -> uint256: view
QUOTE: immutable(address)
UNDERLYING: immutable(address)
DESK: immutable(address)
@deploy
def __init__(quote: address, underlying: address, desk: address):
    QUOTE = quote
    UNDERLYING = underlying
    DESK = desk
@view
@external
def getPriceAndHasFeed(asset: address, staleTime: uint256 = 0, desk: address = empty(address)) -> (uint256, bool):
    if asset != QUOTE:
        return 0, False
    return staticcall Desk(DESK).getPrice(UNDERLYING), True
@view
@external
def hasPriceFeed(asset: address) -> bool:
    return asset == QUOTE
@external
def addPriceSnapshot(asset: address) -> bool:
    return False
