# @version 0.4.3

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
from ethereum.ercs import IERC4626

interface PriceDesk:
    def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256: view

SUPER_OETH: public(immutable(address))
WRAPPED_SUPER_OETH: public(immutable(address))
MCBETH: public(immutable(address))
VVV: public(immutable(address))

vvvPrice: public(uint256)


@deploy
def __init__(
    _ripeHq: address,
    _mcbeth: address,
    _superOETH: address,
    _wrappedSuperOETH: address,
    _vvv: address,
    _minPriceChangeTimeLock: uint256,
    _maxPriceChangeTimeLock: uint256,
):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    addys.__init__(_ripeHq)
    priceData.__init__(False)
    timeLock.__init__(_minPriceChangeTimeLock, _maxPriceChangeTimeLock, 0, _maxPriceChangeTimeLock)

    # set asset
    assert empty(address) not in [_superOETH, _wrappedSuperOETH] # dev: invalid asset addrs
    SUPER_OETH = _superOETH
    WRAPPED_SUPER_OETH = _wrappedSuperOETH
    priceData._addPricedAsset(_wrappedSuperOETH)

    MCBETH = _mcbeth
    if _mcbeth != empty(address):
        priceData._addPricedAsset(_mcbeth)

    VVV = _vvv
    if _vvv != empty(address):
        priceData._addPricedAsset(_vvv)

    self.vvvPrice = 240 * 10 ** 16 # $2.40


########
# Core #
########


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
    if MCBETH != empty(address) and _asset == MCBETH:
        return 1
    if VVV != empty(address) and _asset == VVV:
        return self.vvvPrice
    if _asset != WRAPPED_SUPER_OETH:
        return 0
    return self._getPrice(_asset, _priceDesk)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    if MCBETH != empty(address) and _asset == MCBETH:
        return 1, True
    if VVV != empty(address) and _asset == VVV:
        return self.vvvPrice, True    
    if _asset != WRAPPED_SUPER_OETH:
        return 0, False
    return self._getPrice(_asset, _priceDesk), True


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    if MCBETH != empty(address) and _asset == MCBETH:
        return True
    if VVV != empty(address) and _asset == VVV:
        return True   
    return _asset == WRAPPED_SUPER_OETH


@view
@internal
def _getPrice(_asset: address, _priceDesk: address) -> uint256:
    priceDesk: address = _priceDesk
    if _priceDesk == empty(address):
        priceDesk = addys._getPriceDeskAddr()

    superOethPrice: uint256 = staticcall PriceDesk(priceDesk).getPrice(SUPER_OETH, True)
    if superOethPrice == 0:
        return 0

    pricePerShare: uint256 = staticcall IERC4626(_asset).convertToAssets(10 ** 18)
    return superOethPrice * pricePerShare // (10 ** 18)


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
def addPriceSnapshot(_asset: address) -> bool:
    return False


@external
def disablePriceFeed(_asset: address) -> bool:
    return False


# reset VVV price (for stability pool)


@external
def resetVvvPrice():
    assert gov._canGovern(msg.sender) # dev: no perms
    self.vvvPrice = 1