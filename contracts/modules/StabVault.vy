# @version 0.4.1

uses: vaultData
uses: addys

import contracts.modules.VaultData as vaultData
import contracts.modules.Addys as addys

from interfaces import Vault
from ethereum.ercs import IERC20

interface PriceDesk:
    def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256: view
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

# claimable balances
claimableBalances: public(HashMap[address, HashMap[address, uint256]]) # stab asset -> claimable asset -> balance
totalClaimableBalances: public(HashMap[address, uint256]) # claimable asset -> balance

# claimable assets (iterable)
claimableAssets: public(HashMap[address, HashMap[uint256, address]]) # stab asset -> index -> claimable asset
indexOfClaimableAsset: public(HashMap[address, HashMap[address, uint256]]) # stab asset -> claimable asset -> index
numClaimableAssets: public(HashMap[address, uint256]) # stab asset -> num claimable assets

DECIMAL_OFFSET: constant(uint256) = 10 ** 8


@deploy
def __init__():
    pass


########
# Core #
########


@internal
def _depositTokensInVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _a: addys.Addys,
) -> (uint256, uint256):
    assert vaultData.isActivated # dev: not activated
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed

    # validation
    assert empty(address) not in [_user, _asset] # dev: invalid user or asset
    totalAssetBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    depositAmount: uint256 = min(_amount, totalAssetBalance)
    assert depositAmount != 0 # dev: invalid deposit amount

    # calc usd values
    totalStabValue: uint256 = staticcall PriceDesk(_a.priceDesk).getUsdValue(_asset, totalAssetBalance, True)
    claimableValue: uint256 = self._getValueOfClaimableAssets(_asset, _a.priceDesk)

    newUserValue: uint256 = totalStabValue
    prevStabValue: uint256 = 0
    if depositAmount != totalAssetBalance:
        newUserValue = depositAmount * totalStabValue // totalAssetBalance
        prevStabValue = (totalAssetBalance - depositAmount) * totalStabValue // totalAssetBalance # remove the deposited amount to calc shares accurately

    # calc shares
    newShares: uint256 = self._valueToShares(_asset, newUserValue, vaultData.totalBalances[_asset], prevStabValue + claimableValue, False)

    # add balance on deposit
    vaultData._addBalanceOnDeposit(_user, _asset, newShares, True)

    return depositAmount, newShares


@internal
def _withdrawTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
    _a: addys.Addys,
) -> (uint256, uint256, bool):
    assert vaultData.isActivated # dev: not activated
    assert msg.sender in [addys._getTellerAddr(), addys._getAuctionHouseAddr()] # dev: only Teller or AuctionHouse allowed
    a: addys.Addys = addys._getAddys(_a)

    # validation
    assert empty(address) not in [_user, _asset, _recipient] # dev: invalid user, asset, or recipient
    assert _amount != 0 # dev: invalid withdrawal amount

    # calc shares + amount to withdraw
    withdrawalShares: uint256 = 0
    withdrawalAmount: uint256 = 0
    withdrawalShares, withdrawalAmount = self._calcWithdrawalSharesAndAmount(_user, _asset, _amount, a.priceDesk)

    # reduce balance on withdrawal
    isDepleted: bool = False
    withdrawalShares, isDepleted = vaultData._reduceBalanceOnWithdrawal(_user, _asset, withdrawalShares, True)

    # move tokens to recipient
    assert withdrawalAmount != 0 # dev: no withdrawal amount
    assert extcall IERC20(_asset).transfer(_recipient, withdrawalAmount, default_return_value=True) # dev: token transfer failed

    return withdrawalAmount, withdrawalShares, isDepleted


@internal
def _transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
    _a: addys.Addys,
) -> (uint256, uint256, bool):
    assert vaultData.isActivated # dev: not activated
    assert msg.sender == addys._getAuctionHouseAddr() # dev: only AuctionHouse allowed
    a: addys.Addys = addys._getAddys(_a)

    # validation
    assert empty(address) not in [_fromUser, _toUser, _asset] # dev: invalid users or asset
    assert _transferAmount != 0 # dev: invalid transfer amount

    # calc shares + amount to transfer
    transferShares: uint256 = 0
    transferAmount: uint256 = 0
    transferShares, transferAmount = self._calcWithdrawalSharesAndAmount(_fromUser, _asset, _transferAmount, a.priceDesk)

    # transfer shares
    isFromUserDepleted: bool = False
    transferShares, isFromUserDepleted = vaultData._reduceBalanceOnWithdrawal(_fromUser, _asset, transferShares, False)
    vaultData._addBalanceOnDeposit(_toUser, _asset, transferShares, False)

    return transferAmount, transferShares, isFromUserDepleted


####################
# Needs For Others #
####################


@view
@internal
def _getVaultDataOnDeposit(_user: address, _asset: address) -> Vault.VaultDataOnDeposit:
    # used in Teller.vy
    totalAmount: uint256 = self._getTotalAmountForVault(_asset)
    return Vault.VaultDataOnDeposit(
        hasPosition=vaultData.indexOfUserAsset[_user][_asset] != 0,
        numAssets=vaultData._getNumUserAssets(_user),
        userBalance=self._getTotalAmountForUserWithTotalBal(_user, _asset, totalAmount),
        totalBalance=totalAmount,
    )


@view
@internal
def _getUserLootBoxShare(_user: address, _asset: address) -> uint256:
    # used in Lootbox.vy
    return vaultData.userBalances[_user][_asset]


@view
@internal
def _getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
    # used in CreditEngine.vy
    # NOTE: cannot borrow against stability pool positions, returning empty/0 to ensure this
    return empty(address), 0


@view
@internal
def _getUserAssetAtIndexAndHasBalance(_user: address, _index: uint256) -> (address, bool):
    # used in Lootbox.vy and AuctionHouse.vy
    asset: address = vaultData.userAssets[_user][_index]
    if asset == empty(address):
        return empty(address), False
    return asset, vaultData.userBalances[_user][asset] != 0


###############
# Other Utils #
###############


@view
@internal
def _getTotalAmountForUser(_user: address, _asset: address) -> uint256:
    totalAmount: uint256 = self._getTotalAmountForVault(_asset)
    return self._getTotalAmountForUserWithTotalBal(_user, _asset, totalAmount)


@view
@internal
def _getTotalAmountForUserWithTotalBal(_user: address, _asset: address, _totalAmount: uint256) -> uint256:
    # NOTE: converting usd value to amount, even though contract may not actually have this asset balance!!
    totalShares: uint256 = vaultData.totalBalances[_asset]
    if totalShares == 0:
        return 0
    return vaultData.userBalances[_user][_asset] * _totalAmount // totalShares


@view
@internal
def _getTotalAmountForVault(_asset: address) -> uint256:
    # NOTE: converting usd value to amount, even though contract may not actually have this asset balance!!

    # get total value of asset
    priceDesk: address = addys._getPriceDeskAddr()
    stabAssetBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    totalStabValue: uint256 = staticcall PriceDesk(priceDesk).getUsdValue(_asset, stabAssetBalance, True)
    claimableValue: uint256 = self._getValueOfClaimableAssets(_asset, priceDesk)

    # return amount if there is claimable value
    if claimableValue != 0:
        return staticcall PriceDesk(priceDesk).getAssetAmount(_asset, totalStabValue + claimableValue, True)
    return stabAssetBalance


##########
# Shares #
##########


@view
@internal
def _calcWithdrawalSharesAndAmount(
    _user: address,
    _asset: address,
    _amount: uint256,
    _priceDesk: address,
) -> (uint256, uint256):
    totalShares: uint256 = vaultData.totalBalances[_asset]

    # user shares
    withdrawalShares: uint256 = vaultData.userBalances[_user][_asset]
    assert withdrawalShares != 0 # dev: user has no shares

    # calc usd values
    totalStabAssetBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    totalStabValue: uint256 = staticcall PriceDesk(_priceDesk).getUsdValue(_asset, totalStabAssetBalance, True)
    claimableValue: uint256 = self._getValueOfClaimableAssets(_asset, _priceDesk)
    totalValue: uint256 = totalStabValue + claimableValue

    # max withdraw usd value
    maxWithdrawUsdValue: uint256 = self._sharesToValue(_asset, withdrawalShares, totalShares, totalValue, False)
    maxWithdrawStabAmount: uint256 = maxWithdrawUsdValue * totalStabAssetBalance // totalStabValue

    # max amount available to withdraw
    if _amount >= maxWithdrawStabAmount and maxWithdrawStabAmount <= totalStabAssetBalance:
        return withdrawalShares, maxWithdrawStabAmount

    # finalize withdrawal amount / shares
    maxAvailStabAmount: uint256 = min(maxWithdrawStabAmount, totalStabAssetBalance)
    withdrawalAmount: uint256 = min(_amount, maxAvailStabAmount)
    withdrawalShares = min(withdrawalShares, self._valueToShares(_asset, withdrawalAmount, totalShares, totalValue, True))

    return withdrawalShares, withdrawalAmount


# usd value -> shares


@view
@external
def valueToShares(_asset: address, _usdValue: uint256, _shouldRoundUp: bool) -> uint256:
    totalValue: uint256 = self._getTotalValue(_asset)
    return self._valueToShares(_asset, _usdValue, vaultData.totalBalances[_asset], totalValue, _shouldRoundUp)


@view
@internal
def _valueToShares(
    _asset: address,
    _usdValue: uint256,
    _totalShares: uint256,
    _totalUsdValue: uint256,
    _shouldRoundUp: bool,
) -> uint256:
    totalUsdValue: uint256 = _totalUsdValue

    # dead shares / decimal offset -- preventing donation attacks
    totalUsdValue += 1
    totalShares: uint256 = _totalShares + DECIMAL_OFFSET

    # calc shares
    numerator: uint256 = _usdValue * totalShares
    shares: uint256 = numerator // totalUsdValue

    # rounding
    if _shouldRoundUp and (numerator % totalUsdValue != 0):
        shares += 1

    return shares


# shares -> usd value


@view
@external
def sharesToValue(_asset: address, _shares: uint256, _shouldRoundUp: bool) -> uint256:
    totalValue: uint256 = self._getTotalValue(_asset)
    return self._sharesToValue(_asset, _shares, vaultData.totalBalances[_asset], totalValue, _shouldRoundUp)


@view
@internal
def _sharesToValue(
    _asset: address,
    _shares: uint256,
    _totalShares: uint256,
    _totalUsdValue: uint256,
    _shouldRoundUp: bool,
) -> uint256:
    totalUsdValue: uint256 = _totalUsdValue

    # dead shares / decimal offset -- preventing donation attacks
    totalUsdValue += 1
    totalShares: uint256 = _totalShares + DECIMAL_OFFSET

    # calc usd value
    numerator: uint256 = _shares * totalUsdValue
    usdValue: uint256 = numerator // totalShares

    # rounding
    if _shouldRoundUp and (numerator % totalShares != 0):
        usdValue += 1

    return usdValue


# helper


@view
@internal
def _getTotalValue(_asset: address, _priceDesk: address = empty(address)) -> uint256:
    priceDesk: address = _priceDesk
    if priceDesk == empty(address):
        priceDesk = addys._getPriceDeskAddr()
    totalStabValue: uint256 = staticcall PriceDesk(priceDesk).getUsdValue(_asset, staticcall IERC20(_asset).balanceOf(self), True)
    claimableValue: uint256 = self._getValueOfClaimableAssets(_asset, priceDesk)
    return totalStabValue + claimableValue


##################
# Stability Pool #
##################


# swap for liquidated collateral


@external
def swapForLiquidatedCollateral(
    _stabAsset: address,
    _stabAmountToRemove: uint256,
    _liqAsset: address,
    _liqAmountSent: uint256,
    _recipient: address,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getAuctionHouseAddr() # dev: only AuctionHouse allowed
    a: addys.Addys = addys._getAddys(_a)

    self._handleReceivedAsset(_stabAsset, _liqAsset, _liqAmountSent)
    return self._transferStabAssetOut(_stabAsset, _stabAmountToRemove, _recipient)


# claimable value


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
