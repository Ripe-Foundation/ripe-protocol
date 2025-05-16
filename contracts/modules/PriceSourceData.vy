# @version 0.4.1

uses: addys

import contracts.modules.Addys as addys
from ethereum.ercs import IERC20

event PriceSourceIdSet:
    priceSourceId: uint256

event PriceSourceActivated:
    priceSourceId: uint256
    isActivated: bool

event PriceSourceFundsRecovered:
    priceSourceId: uint256
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

# config
priceSourceId: public(uint256)
isActivated: public(bool)

# priced assets
assets: public(HashMap[uint256, address]) # index -> asset
indexOfAsset: public(HashMap[address, uint256]) # asset -> index
numAssets: public(uint256) # number of assets

MAX_ASSETS: constant(uint256) = 50
MAX_RECOVER_ASSETS: constant(uint256) = 20


@deploy
def __init__():
    self.isActivated = True


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


@external
def setRegistryId(_regId: uint256) -> bool:
    assert msg.sender == addys._getPriceDeskAddr() # dev: only vault book allowed

    prevSourceId: uint256 = self.priceSourceId
    assert prevSourceId == 0 or prevSourceId == _regId # dev: invalid vault id
    self.priceSourceId = _regId
    log PriceSourceIdSet(priceSourceId=_regId)
    return True


@external
def activate(_shouldActivate: bool):
    assert msg.sender == addys._getControlRoomAddr() # dev: only ControlRoom allowed
    self.isActivated = _shouldActivate
    log PriceSourceActivated(priceSourceId=self.priceSourceId, isActivated=_shouldActivate)


@external
def recoverFunds(_recipient: address, _asset: address):
    assert msg.sender == addys._getControlRoomAddr() # dev: only ControlRoom allowed
    self._recoverFunds(_recipient, _asset)


@external
def recoverFundsMany(_recipient: address, _assets: DynArray[address, MAX_RECOVER_ASSETS]):
    assert msg.sender == addys._getControlRoomAddr() # dev: only ControlRoom allowed
    for a: address in _assets:
        self._recoverFunds(_recipient, a)


@internal
def _recoverFunds(_recipient: address, _asset: address):
    assert empty(address) not in [_recipient, _asset] # dev: invalid recipient or asset
    balance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    assert balance != 0 # dev: nothing to recover

    assert extcall IERC20(_asset).transfer(_recipient, balance, default_return_value=True) # dev: recovery failed
    log PriceSourceFundsRecovered(priceSourceId=self.priceSourceId, asset=_asset, recipient=_recipient, balance=balance)