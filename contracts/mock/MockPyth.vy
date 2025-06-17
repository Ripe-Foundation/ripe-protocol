# @version 0.4.1

struct Price:
    price: int64
    conf: uint64
    expo: int32
    publishTime: uint64

struct PriceFeed:
    id: bytes32
    price: Price
    emaPrice: Price

priceFeeds: public(HashMap[bytes32, PriceFeed])
feedExists: HashMap[bytes32, bool]


@deploy
def __init__():
    # initialize "usdc" feed
    usdcId: bytes32 = 0xeaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a
    self.feedExists[usdcId] = True
    usdcFeed: PriceFeed = empty(PriceFeed)
    usdcFeed.id = usdcId
    usdcFeed.price = Price(
        price=99995021,
        conf=56127,
        expo=-8,
        publishTime=convert(block.timestamp, uint64)
    )
    self.priceFeeds[usdcId] = usdcFeed


@view
@external
def getPriceNoOlderThan(_priceFeedId: bytes32, _age: uint256) -> Price:
    priceFeed: PriceFeed = self.priceFeeds[_priceFeedId]
    if priceFeed.id == empty(bytes32):
        return empty(Price)
    if block.timestamp > convert(priceFeed.price.publishTime, uint256) + _age:
        raise "Price too old"
    return priceFeed.price


@view
@external
def getPriceUnsafe(_priceFeedId: bytes32) -> Price:
    priceFeed: PriceFeed = self.priceFeeds[_priceFeedId]
    if priceFeed.id == empty(bytes32):
        return empty(Price)
    return priceFeed.price


@view
@external
def priceFeedExists(_priceFeedId: bytes32) -> bool:
    return self.feedExists[_priceFeedId]


@view
@external
def getUpdateFee(_payLoad: Bytes[2048]) -> uint256:
    return len(_payLoad)


@payable
@external
def updatePriceFeeds(_payLoad: Bytes[2048]):
    updateFee: uint256 = len(_payLoad)
    assert msg.value >= updateFee, "not enough eth"

    price_feed: PriceFeed = abi_decode(_payLoad, PriceFeed)
    lastPublishTime: uint64 = self.priceFeeds[price_feed.id].price.publishTime
    if lastPublishTime < price_feed.price.publishTime:
        self.priceFeeds[price_feed.id] = price_feed
        self.feedExists[price_feed.id] = True


@pure
@external
def createPriceFeedUpdateData(
    _id: bytes32,
    _price: int64,
    _conf: uint64,
    _expo: int32,
    _publishTime: uint64
) -> Bytes[2048]:
    priceFeed: PriceFeed = PriceFeed(
        id=_id,
        price=Price(
            price=_price,
            conf=_conf,
            expo=_expo,
            publishTime=_publishTime
        ),
        emaPrice=Price(
            price=_price,
            conf=_conf,
            expo=_expo,
            publishTime=_publishTime
        )
    )
    return abi_encode(priceFeed)



