# @version 0.4.1

uses: addys

import contracts.modules.Addys as addys
from ethereum.ercs import IERC20

event PriceSourcePauseModified:
    isPaused: bool

event PriceSourceFundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

# config
isPaused: public(bool)

# priced assets
assets: public(HashMap[uint256, address]) # index -> asset
indexOfAsset: public(HashMap[address, uint256]) # asset -> index
numAssets: public(uint256) # number of assets

MAX_ASSETS: constant(uint256) = 50
MAX_RECOVER_ASSETS: constant(uint256) = 20


@deploy
def __init__(_shouldPause: bool):
    self.isPaused = _shouldPause


##############
# Asset Data #
##############


# add priced asset


@internal
def _addPricedAsset(_asset: address):
    aid: uint256 = self.numAssets
    if aid == 0:
        aid = 1 # not using 0 index
    self.assets[aid] = _asset
    self.indexOfAsset[_asset] = aid
    self.numAssets = aid + 1


# remove priced asset


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


# get priced assets


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


# activate


@external
def pause(_shouldPause: bool):
    assert msg.sender == addys._getControlRoomAddr() # dev: only ControlRoom allowed
    self.isPaused = _shouldPause
    log PriceSourcePauseModified(isPaused=_shouldPause)


# recover funds


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
    log PriceSourceFundsRecovered(asset=_asset, recipient=_recipient, balance=balance)