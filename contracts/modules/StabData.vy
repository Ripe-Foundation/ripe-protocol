# @version 0.4.1

uses: addys

import contracts.modules.Addys as addys
from ethereum.ercs import IERC20

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
    return self._handleStabAssetToSend(_stabAsset, _stabAmountToRemove, _recipient)


# transfer stab asset


@internal
def _handleStabAssetToSend(
    _stabAsset: address,
    _stabAmountToRemove: uint256,
    _recipient: address,
) -> uint256:
    assert _recipient != empty(address) # dev: no recipient

    # finalize amount
    amountToSend: uint256 = min(_stabAmountToRemove, staticcall IERC20(_stabAsset).balanceOf(self))
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
    _liqAsset: address,
    _liqAmountSent: uint256,
):
    liqAmountReceived: uint256 = min(_liqAmountSent, staticcall IERC20(_liqAsset).balanceOf(self))
    assert liqAmountReceived != 0 # dev: nothing received

    # update balances
    self.claimableBalances[_stabAsset][_liqAsset] += liqAmountReceived
    self.totalClaimableBalances[_liqAsset] += liqAmountReceived

    # register claimable asset if not already registered
    if self.indexOfClaimableAsset[_stabAsset][_liqAsset] == 0:
        self._registerClaimableAsset(_stabAsset, _liqAsset)


# register claimable asset



@internal
def _registerClaimableAsset(_stabAsset: address, _liqAsset: address):
    cid: uint256 = self.numClaimableAssets[_stabAsset]
    if cid == 0:
        cid = 1 # not using 0 index
    self.claimableAssets[_stabAsset][cid] = _liqAsset
    self.indexOfClaimableAsset[_stabAsset][_liqAsset] = cid
    self.numClaimableAssets[_stabAsset] = cid + 1




