# @version 0.4.3

# Test-only PriceSource with independently configurable raw return shapes.
# Modes: 0 canonical, 1 revert, 2 empty, 3 short, 4 oversized by one byte,
# 5 noncanonical Boolean word, 6 oversized to 96 bytes (price/feed channels).

price: public(uint256)
hasFeed: public(bool)
priceResponseMode: public(uint256)
hasFeedResponseMode: public(uint256)
snapshotResponseMode: public(uint256)
snapshotCount: public(uint256)


@external
def configure(
    _price: uint256,
    _hasFeed: bool,
    _priceResponseMode: uint256 = 0,
    _hasFeedResponseMode: uint256 = 0,
    _snapshotResponseMode: uint256 = 0,
):
    assert _priceResponseMode <= 6
    assert _hasFeedResponseMode <= 6
    assert _snapshotResponseMode <= 5
    self.price = _price
    self.hasFeed = _hasFeed
    self.priceResponseMode = _priceResponseMode
    self.hasFeedResponseMode = _hasFeedResponseMode
    self.snapshotResponseMode = _snapshotResponseMode


@view
@external
@raw_return
def getPriceAndHasFeed(
    _asset: address,
    _staleTime: uint256 = 0,
    _priceDesk: address = empty(address),
) -> Bytes[96]:
    mode: uint256 = self.priceResponseMode
    if mode == 1:
        raise
    if mode == 2:
        return b""

    hasFeedWord: uint256 = 2 if mode == 5 else convert(self.hasFeed, uint256)
    response: Bytes[64] = concat(
        convert(self.price, bytes32),
        convert(hasFeedWord, bytes32),
    )
    if mode == 3:
        return slice(response, 0, 63)
    if mode == 4:
        return concat(response, b"x")
    if mode == 6:
        return concat(response, empty(bytes32))
    return response


@view
@external
@raw_return
def hasPriceFeed(_asset: address) -> Bytes[96]:
    mode: uint256 = self.hasFeedResponseMode
    if mode == 1:
        raise
    if mode == 2:
        return b""

    hasFeedWord: uint256 = 2 if mode == 5 else convert(self.hasFeed, uint256)
    response: bytes32 = convert(hasFeedWord, bytes32)
    if mode == 3:
        return slice(response, 0, 31)
    if mode == 4:
        return concat(response, b"x")
    if mode == 6:
        return concat(response, empty(bytes32), empty(bytes32))
    return slice(response, 0, 32)


@external
@raw_return
def addPriceSnapshot(_asset: address) -> Bytes[33]:
    self.snapshotCount += 1

    mode: uint256 = self.snapshotResponseMode
    if mode == 1:
        raise
    if mode == 2:
        return b""

    resultWord: uint256 = 2 if mode == 5 else 1
    response: bytes32 = convert(resultWord, bytes32)
    if mode == 3:
        return slice(response, 0, 31)
    if mode == 4:
        return concat(response, b"x")
    return slice(response, 0, 32)
