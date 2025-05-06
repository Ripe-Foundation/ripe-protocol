# @version 0.4.1

from ethereum.ercs import IERC20

event VaultFundsRecovered:
    vaultId: uint256
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

event VaultIdSet:
    vaultId: uint256

event VaultActivated:
    vaultId: uint256
    isActivated: bool

# config
vaultId: public(uint256)
isActivated: public(bool)

# balances (may be shares or actual balance)
userBalances: public(HashMap[address, HashMap[address, uint256]]) # user -> asset -> balance
totalBalances: public(HashMap[address, uint256]) # asset -> balance

# user assets (iterable)
userAssets: public(HashMap[address, HashMap[uint256, address]]) # user -> index -> asset
indexOfUserAsset: public(HashMap[address, HashMap[address, uint256]]) # user -> asset -> index
numUserAssets: public(HashMap[address, uint256]) # user -> num assets

# vault assets (iterable)
vaultAssets: public(HashMap[uint256, address]) # index -> asset
indexOfAsset: public(HashMap[address, uint256]) # asset -> index
numAssets: public(uint256) # num assets


@deploy
def __init__():
    self.isActivated = True


###################
# Balance Updates #
###################


# deposit


@internal
def _addBalanceOnDeposit(
    _user: address,
    _asset: address,
    _depositBal: uint256,
    _shouldUpdateTotal: bool,
):
    # update balances
    self.userBalances[_user][_asset] += _depositBal
    if _shouldUpdateTotal:
        self.totalBalances[_asset] += _depositBal

    # register user asset (if necessary)
    if self.indexOfUserAsset[_user][_asset] == 0:
        self._registerUserAsset(_user, _asset)

    # register vault asset (if necessary)
    if self.indexOfAsset[_asset] == 0:
        self._registerVaultAsset(_asset)


# withdrawal


@internal
def _reduceBalanceOnWithdrawal(
    _user: address,
    _asset: address,
    _withdrawBal: uint256,
    _shouldUpdateTotal: bool,
) -> (uint256, bool):
    assert self.indexOfUserAsset[_user][_asset] != 0 # dev: user does not have this asset

    currentBal: uint256 = self.userBalances[_user][_asset]
    withdrawBal: uint256 = min(_withdrawBal, currentBal)
    assert withdrawBal != 0 # dev: nothing to withdraw

    # update balances
    currentBal -= withdrawBal
    self.userBalances[_user][_asset] = currentBal
    if _shouldUpdateTotal:
        self.totalBalances[_asset] -= withdrawBal

    return withdrawBal, currentBal == 0


################
# Registration #
################


# user


@internal
def _registerUserAsset(_user: address, _asset: address):
    aid: uint256 = self.numUserAssets[_user]
    if aid == 0:
        aid = 1 # not using 0 index
    self.userAssets[_user][aid] = _asset
    self.indexOfUserAsset[_user][_asset] = aid
    self.numUserAssets[_user] = aid + 1


@internal
def _deregisterUserAsset(_user: address, _asset: address):
    if self.userBalances[_user][_asset] != 0:
        return

    numUserAssets: uint256 = self.numUserAssets[_user]
    if numUserAssets == 0:
        return

    targetIndex: uint256 = self.indexOfUserAsset[_user][_asset]
    if targetIndex == 0:
        return

    # update data
    lastIndex: uint256 = numUserAssets - 1
    self.numUserAssets[_user] = lastIndex
    self.indexOfUserAsset[_user][_asset] = 0

    # get last item, replace the removed item
    if targetIndex != lastIndex:
        lastItem: address = self.userAssets[_user][lastIndex]
        self.userAssets[_user][targetIndex] = lastItem
        self.indexOfUserAsset[_user][lastItem] = targetIndex


# vault


@internal
def _registerVaultAsset(_asset: address):
    aid: uint256 = self.numAssets
    if aid == 0:
        aid = 1 # not using 0 index
    self.vaultAssets[aid] = _asset
    self.indexOfAsset[_asset] = aid
    self.numAssets = aid + 1


@internal
def _deregisterVaultAsset(_asset: address):
    if self.totalBalances[_asset] != 0:
        return

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
        lastItem: address = self.vaultAssets[lastIndex]
        self.vaultAssets[targetIndex] = lastItem
        self.indexOfAsset[lastItem] = targetIndex


########
# Ripe #
########


# has funds


@view
@external
def hasAnyFunds() -> bool:
    numAssets: uint256 = self.numAssets
    for i: uint256 in range(1, numAssets, bound=max_value(uint256)):
        asset: address = self.vaultAssets[i]
        if self.totalBalances[asset] != 0:
            return True
    return False


# vault id


@internal
def _setVaultId(_vaultId: uint256) -> bool:
    prevVaultId: uint256 = self.vaultId
    assert prevVaultId == 0 or prevVaultId == _vaultId # dev: invalid vault id
    self.vaultId = _vaultId
    log VaultIdSet(vaultId=_vaultId)
    return True


# recover funds


@internal
def _recoverFunds(_asset: address, _recipient: address) -> bool:
    balance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    if empty(address) in [_recipient, _asset] or balance == 0:
        return False

    # cannot recover funds from a registered asset with a balance
    if self.indexOfAsset[_asset] != 0 and self.totalBalances[_asset] != 0:
        return False

    # recover
    assert extcall IERC20(_asset).transfer(_recipient, balance, default_return_value=True) # dev: recovery failed
    log VaultFundsRecovered(vaultId=self.vaultId, asset=_asset, recipient=_recipient, balance=balance)
    return True


# activation


@internal
def _activate(_shouldActivate: bool):
    self.isActivated = _shouldActivate
    log VaultActivated(vaultId=self.vaultId, isActivated=_shouldActivate)