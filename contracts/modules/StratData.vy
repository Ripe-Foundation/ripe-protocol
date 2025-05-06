# @version 0.4.1

struct BalanceData:
    asset: address
    bal: uint256 # could be shares or actual balance

# balance data
balanceData: public(HashMap[address, HashMap[uint256, BalanceData]]) # user -> index -> BalanceData
indexOfAsset: public(HashMap[address, HashMap[address, uint256]]) # user -> asset -> index
numAssets: public(HashMap[address, uint256]) # user -> num assets

totalBalances: public(HashMap[address, uint256]) # asset -> total balances


@deploy
def __init__():
    pass


################
# Balance Data #
################


# deposit


@internal
def _addBalanceOnDeposit(
    _user: address,
    _asset: address,
    _depositBal: uint256,
    _shouldUpdateTotal: bool,
):
    aid: uint256 = self.indexOfAsset[_user][_asset]
    balData: BalanceData = self.balanceData[_user][aid]

    # new asset for this user
    if aid == 0:
        aid = self._registerAsset(_user, _asset)
        balData.asset = _asset

    # update data
    balData.bal += _depositBal
    self.balanceData[_user][aid] = balData

    if _shouldUpdateTotal:
        self.totalBalances[_asset] += _depositBal


# withdrawal


@internal
def _reduceBalanceOnWithdrawal(
    _user: address,
    _asset: address,
    _withdrawBal: uint256,
    _shouldUpdateTotal: bool,
) -> (uint256, bool):
    aid: uint256 = self.indexOfAsset[_user][_asset]
    assert aid != 0 # dev: user does not have this asset

    balData: BalanceData = self.balanceData[_user][aid]
    withdrawBal: uint256 = min(_withdrawBal, balData.bal)
    assert withdrawBal != 0 # dev: nothing to withdraw

    # update data
    balData.bal -= withdrawBal
    self.balanceData[_user][aid] = balData

    if _shouldUpdateTotal:
        self.totalBalances[_asset] -= withdrawBal

    return withdrawBal, balData.bal == 0


################
# Registration #
################


@internal
def _registerAsset(_user: address, _asset: address) -> uint256:
    aid: uint256 = self.numAssets[_user]
    if aid == 0:
        aid = 1 # not using 0 index
    self.indexOfAsset[_user][_asset] = aid
    self.numAssets[_user] = aid + 1
    return aid


@internal
def _deregisterAsset(_user: address, _asset: address):
    numAssets: uint256 = self.numAssets[_user]
    if numAssets == 0:
        return

    targetIndex: uint256 = self.indexOfAsset[_user][_asset]
    if targetIndex == 0:
        return

    # update data
    lastIndex: uint256 = numAssets - 1
    self.numAssets[_user] = lastIndex
    self.indexOfAsset[_user][_asset] = 0

    # get last item, replace the removed item
    if targetIndex != lastIndex:
        lastItem: BalanceData = self.balanceData[_user][lastIndex]
        self.balanceData[_user][targetIndex] = lastItem
        self.indexOfAsset[_user][lastItem.asset] = targetIndex


#############
# Utilities #
#############


@view
@internal
def _getUserBalance(_user: address, _asset: address) -> uint256:
    aid: uint256 = self.indexOfAsset[_user][_asset]
    return self.balanceData[_user][aid].bal
