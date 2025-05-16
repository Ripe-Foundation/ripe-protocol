# @version 0.4.1

implements: PriceSource

exports: gov.__interface__
exports: addys.__interface__
exports: priceData.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: addys
initializes: priceData[addys := addys]
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.Addys as addys
import contracts.modules.PriceSourceData as priceData
import contracts.modules.TimeLock as timeLock

import interfaces.PriceSource as PriceSource

interface PriceDesk:
    def minRegistryTimeLock() -> uint256: view
    def maxRegistryTimeLock() -> uint256: view

price: public(HashMap[address, uint256])


@deploy
def __init__(_ripeHq: address, _initialPriceDesk: address):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    addys.__init__(_ripeHq)
    priceData.__init__(_initialPriceDesk)

    # time lock module
    priceDesk: address = addys._getPriceDeskAddr()
    if priceDesk == empty(address):
        priceDesk = _initialPriceDesk
    timeLock.__init__(staticcall PriceDesk(priceDesk).minRegistryTimeLock(), staticcall PriceDesk(priceDesk).maxRegistryTimeLock(), 0)


########
# Core #
########


@external
def setPrice(_asset: address, _price: uint256):
    assert gov._canGovern(msg.sender) # dev: no perms
    self.price[_asset] = _price


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
    return self.price[_asset]


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    price: uint256 = self.price[_asset]
    return price, price != 0


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self.price[_asset] != 0


#########
# Other #
#########


@view
@external
def hasPendingPriceFeedUpdate(_asset: address) -> bool:
    return False


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
