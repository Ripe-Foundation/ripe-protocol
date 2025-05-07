# @version 0.4.1

event PriceSourceIdSet:
    priceSourceId: uint256

priceSourceId: public(uint256)

# priced assets
assets: public(HashMap[uint256, address]) # index -> asset
indexOfAsset: public(HashMap[address, uint256]) # asset -> index
numAssets: public(uint256) # number of assets

MAX_ASSETS: constant(uint256) = 50


@deploy
def __init__():
    pass


############
# Set Data #
############


@internal
def _addPricedAsset(_asset: address):
    aid: uint256 = self.numAssets
    if aid == 0:
        aid = 1 # not using 0 index
    self.assets[aid] = _asset
    self.indexOfAsset[_asset] = aid
    self.numAssets = aid + 1


@internal
def _removePricedAsset(_asset: address):
    numAssets: uint256 = self.numAssets
    if numAssets == 0:
        return

    targetIndex: uint256 = self.indexOfAsset[_asset]
    if targetIndex == 0:
        return

    # update data
    lastIndex: uint256 = numAssets - 1
    self.numAssets = lastIndex
    self.indexOfAsset[_asset] = 0

    # get last item, replace the removed item
    if targetIndex != lastIndex:
        lastItem: address = self.assets[lastIndex]
        self.assets[targetIndex] = lastItem
        self.indexOfAsset[lastItem] = targetIndex


#############
# Utilities #
#############


@view
@external
def getPricedAssets() -> DynArray[address, MAX_ASSETS]:
    numAssets: uint256 = self.numAssets
    if numAssets == 0:
        return []
    assets: DynArray[address, MAX_ASSETS] = []
    for i: uint256 in range(1, numAssets, bound=MAX_ASSETS):
        assets.append(self.assets[i])
    return assets


########
# Ripe #
########


@internal
def _setPriceSourceId(_priceSourceId: uint256) -> bool:
    prevPriceSourceId: uint256 = self.priceSourceId
    assert prevPriceSourceId == 0 or prevPriceSourceId == _priceSourceId # dev: invalid price source id
    self.priceSourceId = _priceSourceId
    log PriceSourceIdSet(priceSourceId=_priceSourceId)
    return True