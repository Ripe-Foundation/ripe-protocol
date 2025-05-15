# @version 0.4.1

implements: PriceSource
import interfaces.PriceSource as PriceSource

price: public(HashMap[address, uint256])
priceSourceId: public(uint256)


@deploy
def __init__():
    pass


@external
def setPrice(_asset: address, _price: uint256):
    self.price[_asset] = _price


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _oracleRegistry: address = empty(address)) -> uint256:
    return self.price[_asset]


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _oracleRegistry: address = empty(address)) -> (uint256, bool):
    price: uint256 = self.price[_asset]
    return price, price != 0


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self.price[_asset] != 0


@view
@external
def hasPendingPriceFeedUpdate(_asset: address) -> bool:
    return False


@view
@external
def priceFeedChangeDelay() -> uint256:
    return 0


@external
def setPriceFeedChangeDelay(_numBlocks: uint256) -> bool:
    return True


@external
def setPriceFeedChangeDelayToMin() -> bool:
    return True


# config


@external
def confirmNewPriceFeed(_asset: address) -> bool:
    return True


@external
def cancelNewPendingPriceFeed(_asset: address) -> bool:
    return True


@external
def confirmPriceFeedUpdate(_asset: address) -> bool:
    return True


@external
def cancelPriceFeedUpdate(_asset: address) -> bool:
    return True


@external
def disablePriceFeed(_asset: address) -> bool:
    return True


@external
def confirmDisablePriceFeed(_asset: address) -> bool:
    return True


@external
def cancelDisablePriceFeed(_asset: address) -> bool:
    return True


@external
def setPriceSourceId(_priceSourceId: uint256) -> bool:
    self.priceSourceId = _priceSourceId
    return True

@view
@external
def getPricedAssets() -> DynArray[address, 50]:
    return []
