# @version 0.4.1

uses: addys

import contracts.modules.Addys as addys
from ethereum.ercs import IERC20

interface PriceDesk:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

# claimable balances
claimableBalances: public(HashMap[address, HashMap[address, uint256]]) # stab asset -> claimable asset -> balance
totalClaimableBalances: public(HashMap[address, uint256]) # claimable asset -> balance

# claimable assets (iterable)
claimableAssets: public(HashMap[address, HashMap[uint256, address]]) # stab asset -> index -> claimable asset
indexOfClaimableAsset: public(HashMap[address, HashMap[address, uint256]]) # stab asset -> claimable asset -> index
numClaimableAssets: public(HashMap[address, uint256]) # stab asset -> num claimable assets


@deploy
def __init__():
    pass


@view
@internal
def _getValueOfClaimableAssets(_stabAsset: address, _priceDesk: address) -> uint256:
    totalValue: uint256 = 0
    numClaimableAssets: uint256 = self.numClaimableAssets[_stabAsset]
    for i: uint256 in range(1, numClaimableAssets, bound=max_value(uint256)):
        asset: address = self.claimableAssets[_stabAsset][i]
        if asset == empty(address):
            continue
        balance: uint256 = self.claimableBalances[_stabAsset][asset]
        if balance == 0:
            continue
        totalValue += staticcall PriceDesk(_priceDesk).getUsdValue(asset, balance, True)
    return totalValue


########
# Core #
########


@external
def swapForLiquidatedCollateral(
    _stabAsset: address,
    _stabAmountToRemove: uint256,
    _liqAsset: address,
    _liqAmountSent: uint256,
    _recipient: address,
) -> uint256:
    assert msg.sender == addys._getAuctionHouseAddr() # dev: only AuctionHouse allowed

    self._handleReceivedAsset(_stabAsset, _liqAsset, _liqAmountSent)
    return self._transferStabAssetOut(_stabAsset, _stabAmountToRemove, _recipient)


# transfer stab asset


@internal
def _transferStabAssetOut(
    _stabAsset: address,
    _stabAmount: uint256,
    _recipient: address,
) -> uint256:
    assert _recipient != empty(address) # dev: no recipient

    # finalize amount
    amountToSend: uint256 = min(_stabAmount, staticcall IERC20(_stabAsset).balanceOf(self))
    assert amountToSend != 0 # dev: nothing to transfer

    # transfer stab asset
    assert extcall IERC20(_stabAsset).transfer(_recipient, amountToSend, default_return_value=True) # dev: transfer failed
    return amountToSend


########
# Data #
########


# receive claimable asset


@internal
def _handleReceivedAsset(
    _stabAsset: address,
    _assetReceived: address,
    _amountReceived: uint256,
):
    amountReceived: uint256 = min(_amountReceived, staticcall IERC20(_assetReceived).balanceOf(self))
    assert amountReceived != 0 # dev: nothing received

    # update balances
    self.claimableBalances[_stabAsset][_assetReceived] += amountReceived
    self.totalClaimableBalances[_assetReceived] += amountReceived

    # register claimable asset if not already registered
    if self.indexOfClaimableAsset[_stabAsset][_assetReceived] == 0:
        self._registerClaimableAsset(_stabAsset, _assetReceived)


# register claimable asset



@internal
def _registerClaimableAsset(_stabAsset: address, _assetReceived: address):
    cid: uint256 = self.numClaimableAssets[_stabAsset]
    if cid == 0:
        cid = 1 # not using 0 index
    self.claimableAssets[_stabAsset][cid] = _assetReceived
    self.indexOfClaimableAsset[_stabAsset][_assetReceived] = cid
    self.numClaimableAssets[_stabAsset] = cid + 1




