# @version 0.4.1

interface SavingsGreen:
    def pricePerShare() -> uint256: view

sGreen: public(address)

@deploy
def __init__(
    _sGreen: address,
):
    self.sGreen = _sGreen


########
# Core #
########


@view
@internal
def _getPrice() -> uint256:
    return staticcall SavingsGreen(self.sGreen).pricePerShare()


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
    if _asset != self.sGreen:
        return 0
    
    return self._getPrice()


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    if _asset != self.sGreen:
      return 0, False
    
    return self._getPrice(), True

@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return _asset == self.sGreen


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
