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
import contracts.priceSources.modules.PriceSourceData as priceData
import contracts.modules.TimeLock as timeLock

import interfaces.PriceSource as PriceSource

struct CurrentGreenPoolStatus:
    weightedRatio: uint256
    dangerTrigger: uint256
    numBlocksInDanger: uint256

mockData: public(CurrentGreenPoolStatus)


@deploy
def __init__(
    _ripeHq: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    addys.__init__(_ripeHq)
    priceData.__init__(False)
    timeLock.__init__(_minPriceChangeTimeLock, _maxPriceChangeTimeLock, 0, _maxPriceChangeTimeLock)


# MOCK CONFIG


@external
def setMockGreenPoolData(
    _weightedRatio: uint256,
    _dangerTrigger: uint256,
    _numBlocksInDanger: uint256,
):
    self.mockData = CurrentGreenPoolStatus(
        weightedRatio=_weightedRatio,
        dangerTrigger=_dangerTrigger,
        numBlocksInDanger=_numBlocksInDanger,
    )


@view
@external
def getCurrentGreenPoolStatus() -> CurrentGreenPoolStatus:
    mockData: CurrentGreenPoolStatus = self.mockData
    return CurrentGreenPoolStatus(
        weightedRatio=mockData.weightedRatio,
        dangerTrigger=mockData.dangerTrigger,
        numBlocksInDanger=mockData.numBlocksInDanger,
    )


@external
def addGreenRefPoolSnapshot() -> bool:
    return True


@external 
def addPriceSnapshot(_asset: address) -> bool:
    return False
    

########
# Core #
########


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
    return 0


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    return 0, False


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return False


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
def confirmDisablePriceFeed(_asset: address) -> bool:
    return True


@external
def cancelDisablePriceFeed(_asset: address) -> bool:
    return True


@external
def disablePriceFeed(_asset: address) -> bool:
    return True