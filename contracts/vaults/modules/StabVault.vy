# @version 0.4.1

uses: vaultData
uses: addys

import contracts.vaults.modules.VaultData as vaultData
import contracts.modules.Addys as addys

from interfaces import Vault
from ethereum.ercs import IERC4626
from ethereum.ercs import IERC20

interface ControlRoom:
    def getStabPoolRedemptionsConfig(_asset: address, _redeemer: address) -> StabPoolRedemptionsConfig: view
    def getStabPoolClaimsConfig(_asset: address, _claimer: address) -> StabPoolClaimsConfig: view

interface PriceDesk:
    def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256: view
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface GreenToken:
    def burn(_amount: uint256): nonpayable

struct StabPoolClaim:
    stabAsset: address
    claimAsset: address
    maxUsdValue: uint256

struct StabPoolRedemption:
    claimAsset: address
    maxGreenAmount: uint256

struct StabPoolClaimsConfig:
    canClaimInStabPoolGeneral: bool
    canClaimInStabPoolAsset: bool
    isUserAllowed: bool

struct StabPoolRedemptionsConfig:
    canRedeemInStabPoolGeneral: bool
    canRedeemInStabPoolAsset: bool
    isUserAllowed: bool

event AssetClaimedInStabilityPool:
    user: indexed(address)
    stabAsset: indexed(address)
    claimAsset: indexed(address)
    claimAmount: uint256
    claimUsdValue: uint256
    claimShares: uint256
    isDepleted: bool

# claimable balances
claimableBalances: public(HashMap[address, HashMap[address, uint256]]) # stab asset -> claimable asset -> balance
totalClaimableBalances: public(HashMap[address, uint256]) # claimable asset -> balance

# claimable assets (iterable)
claimableAssets: public(HashMap[address, HashMap[uint256, address]]) # stab asset -> index -> claimable asset
indexOfClaimableAsset: public(HashMap[address, HashMap[address, uint256]]) # stab asset -> claimable asset -> index
numClaimableAssets: public(HashMap[address, uint256]) # stab asset -> num claimable assets

MAX_STAB_CLAIMS: constant(uint256) = 15
MAX_STAB_REDEMPTIONS: constant(uint256) = 15
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
    _priceDesk: address,
) -> (uint256, uint256):
    assert not vaultData.isPaused # dev: contract paused

    # validation
    assert empty(address) not in [_user, _asset] # dev: invalid user or asset
    totalAssetBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    depositAmount: uint256 = min(_amount, totalAssetBalance)
    assert depositAmount != 0 # dev: invalid deposit amount

    # calc usd values
    totalStabValue: uint256 = staticcall PriceDesk(_priceDesk).getUsdValue(_asset, totalAssetBalance, True)
    assert totalStabValue != 0 # dev: no price for stab asset

    newUserValue: uint256 = totalStabValue
    prevStabValue: uint256 = 0
    if depositAmount != totalAssetBalance:
        newUserValue = depositAmount * totalStabValue // totalAssetBalance
        prevStabValue = (totalAssetBalance - depositAmount) * totalStabValue // totalAssetBalance # remove the deposited amount to calc shares accurately

    # calc shares
    claimableValue: uint256 = self._getValueOfClaimableAssets(_asset, _priceDesk)
    newShares: uint256 = self._valueToShares(newUserValue, vaultData.totalBalances[_asset], prevStabValue + claimableValue, False)

    # add balance on deposit
    vaultData._addBalanceOnDeposit(_user, _asset, newShares, True)

    return depositAmount, newShares


@internal
def _withdrawTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
    _priceDesk: address,
) -> (uint256, uint256, bool):
    assert not vaultData.isPaused # dev: contract paused
    assert empty(address) not in [_user, _asset, _recipient] # dev: invalid user, asset, or recipient

    # calc shares + amount to withdraw
    withdrawalShares: uint256 = 0
    withdrawalAmount: uint256 = 0
    withdrawalShares, withdrawalAmount = self._calcWithdrawalSharesAndAmount(_user, _asset, _amount, _priceDesk)

    # reduce balance on withdrawal
    isDepleted: bool = False
    withdrawalShares, isDepleted = vaultData._reduceBalanceOnWithdrawal(_user, _asset, withdrawalShares, True)

    assert extcall IERC20(_asset).transfer(_recipient, withdrawalAmount, default_return_value=True) # dev: token transfer failed
    return withdrawalAmount, withdrawalShares, isDepleted


@internal
def _transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
    _priceDesk: address,
) -> (uint256, uint256, bool):
    assert not vaultData.isPaused # dev: contract paused
    assert empty(address) not in [_fromUser, _toUser, _asset] # dev: invalid users or asset

    # calc shares + amount to transfer
    transferShares: uint256 = 0
    transferAmount: uint256 = 0
    transferShares, transferAmount = self._calcWithdrawalSharesAndAmount(_fromUser, _asset, _transferAmount, _priceDesk)

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
    # NOTE: converting usd value to amount, even though vault may not actually have this asset balance!!
    totalShares: uint256 = vaultData.totalBalances[_asset]
    if totalShares == 0:
        return 0
    return vaultData.userBalances[_user][_asset] * _totalAmount // totalShares


@view
@internal
def _getTotalAmountForVault(_asset: address) -> uint256:
    # NOTE: converting usd value to amount, even though vault may not actually have this asset balance!!

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
    totalStabAssetBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    assert totalStabAssetBalance != 0 # dev: no stab asset to withdraw

    # user shares
    withdrawalShares: uint256 = vaultData.userBalances[_user][_asset]
    assert withdrawalShares != 0 # dev: user has no shares

    # calc usd values
    totalStabValue: uint256 = staticcall PriceDesk(_priceDesk).getUsdValue(_asset, totalStabAssetBalance, True)
    assert totalStabValue != 0 # dev: no price for stab asset
    claimableValue: uint256 = self._getValueOfClaimableAssets(_asset, _priceDesk)
    totalValue: uint256 = totalStabValue + claimableValue

    # max withdraw usd value
    maxWithdrawUsdValue: uint256 = self._sharesToValue(withdrawalShares, totalShares, totalValue, False)
    maxWithdrawStabAmount: uint256 = maxWithdrawUsdValue * totalStabAssetBalance // totalStabValue
    assert maxWithdrawStabAmount != 0 # dev: max withdraw stab amount is 0

    # max amount available to withdraw
    if _amount >= maxWithdrawStabAmount and maxWithdrawStabAmount <= totalStabAssetBalance:
        return withdrawalShares, maxWithdrawStabAmount

    # finalize withdrawal amount / shares
    maxAvailStabAmount: uint256 = min(maxWithdrawStabAmount, totalStabAssetBalance)
    withdrawalAmount: uint256 = min(_amount, maxAvailStabAmount)
    assert withdrawalAmount != 0 # dev: no withdrawal amount

    withdrawalUsdValue: uint256 = withdrawalAmount * totalStabValue // totalStabAssetBalance
    withdrawalShares = min(withdrawalShares, self._valueToShares(withdrawalUsdValue, totalShares, totalValue, True))
    return withdrawalShares, withdrawalAmount


# usd value -> shares


@view
@external
def valueToShares(_asset: address, _usdValue: uint256, _shouldRoundUp: bool) -> uint256:
    totalValue: uint256 = self._getTotalValue(_asset)
    return self._valueToShares(_usdValue, vaultData.totalBalances[_asset], totalValue, _shouldRoundUp)


@view
@internal
def _valueToShares(
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
    return self._sharesToValue(_shares, vaultData.totalBalances[_asset], totalValue, _shouldRoundUp)


@view
@internal
def _sharesToValue(
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


##################
# Stability Pool #
##################


@external
def swapForLiquidatedCollateral(
    _stabAsset: address,
    _stabAssetAmount: uint256,
    _liqAsset: address,
    _liqAmountSent: uint256,
    _recipient: address,
    _greenToken: address,
) -> uint256:
    assert not vaultData.isPaused # dev: contract paused
    assert msg.sender == addys._getAuctionHouseAddr() # dev: only AuctionHouse allowed
    assert vaultData.indexOfAsset[_liqAsset] == 0 # dev: liq asset cannot be stab asset

    # add claimable balance
    self._addClaimableBalance(_stabAsset, _liqAsset, _liqAmountSent)

    # finalize amount
    amount: uint256 = min(_stabAssetAmount, staticcall IERC20(_stabAsset).balanceOf(self))
    assert amount != 0 # dev: nothing to transfer

    # burn green token
    if _recipient == empty(address):
        assert _stabAsset == _greenToken # dev: must be green token
        extcall GreenToken(_greenToken).burn(amount) # dev: burn failed

    else:
        assert extcall IERC20(_stabAsset).transfer(_recipient, amount, default_return_value=True) # dev: transfer failed

    return amount


# utilities


@view
@external
def getTotalValue(_asset: address) -> uint256:
    return self._getTotalValue(_asset)


@view
@external
def getTotalUserValue(_user: address, _asset: address) -> uint256:
    totalValue: uint256 = self._getTotalValue(_asset)
    return self._sharesToValue(vaultData.userBalances[_user][_asset], vaultData.totalBalances[_asset], totalValue, False)


@view
@internal
def _getTotalValue(_asset: address, _priceDesk: address = empty(address)) -> uint256:
    priceDesk: address = _priceDesk
    if priceDesk == empty(address):
        priceDesk = addys._getPriceDeskAddr()
    totalStabValue: uint256 = staticcall PriceDesk(priceDesk).getUsdValue(_asset, staticcall IERC20(_asset).balanceOf(self), True)
    claimableValue: uint256 = self._getValueOfClaimableAssets(_asset, priceDesk)
    return totalStabValue + claimableValue


@view
@internal
def _getValueOfClaimableAssets(_stabAsset: address, _priceDesk: address) -> uint256:
    totalValue: uint256 = 0
    numClaimableAssets: uint256 = self.numClaimableAssets[_stabAsset]
    if numClaimableAssets == 0:
        return 0

    for i: uint256 in range(1, numClaimableAssets, bound=max_value(uint256)):
        asset: address = self.claimableAssets[_stabAsset][i]
        if asset == empty(address):
            continue
        balance: uint256 = self.claimableBalances[_stabAsset][asset]
        if balance == 0:
            continue

        claimValue: uint256 = staticcall PriceDesk(_priceDesk).getUsdValue(asset, balance, True)
        assert claimValue != 0 # dev: claimable asset has no value
        totalValue += claimValue

    return totalValue


############################
# Claims (already in pool) #
############################


@external
def claimFromStabilityPool(
    _claimer: address,
    _stabAsset: address,
    _claimAsset: address,
    _maxUsdValue: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert not vaultData.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)
    return self._claimFromStabilityPool(_claimer, _stabAsset, _claimAsset, _maxUsdValue, a.priceDesk, a.controlRoom)


@external
def claimManyFromStabilityPool(
    _claimer: address,
    _claims: DynArray[StabPoolClaim, MAX_STAB_CLAIMS],
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert not vaultData.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    totalUsdValue: uint256 = 0
    for c: StabPoolClaim in _claims:
        totalUsdValue += self._claimFromStabilityPool(_claimer, c.stabAsset, c.claimAsset, c.maxUsdValue, a.priceDesk, a.controlRoom)
    return totalUsdValue


@internal
def _claimFromStabilityPool(
    _claimer: address,
    _stabAsset: address,
    _claimAsset: address,
    _maxUsdValue: uint256,
    _priceDesk: address,
    _controlRoom: address,
) -> uint256:
    if empty(address) in [_claimer, _stabAsset, _claimAsset] or _maxUsdValue == 0:
        return 0

    # check claims config
    config: StabPoolClaimsConfig = staticcall ControlRoom(_controlRoom).getStabPoolClaimsConfig(_stabAsset, _claimer)
    if not config.canClaimInStabPoolGeneral or not config.canClaimInStabPoolAsset or not config.isUserAllowed:
        return 0

    # max claimable asset
    maxClaimableAsset: uint256 = self.claimableBalances[_stabAsset][_claimAsset]
    if maxClaimableAsset == 0:
        return 0

    # calc shares + amount to withdraw
    claimShares: uint256 = 0
    claimAmount: uint256 = 0
    claimUsdValue: uint256 = 0
    claimShares, claimAmount, claimUsdValue = self._calcClaimSharesAndAmount(_claimer, _stabAsset, _claimAsset, _maxUsdValue, maxClaimableAsset, _priceDesk)
    if claimShares == 0:
        return 0

    # reduce balance on withdrawal
    isDepleted: bool = False
    claimShares, isDepleted = vaultData._reduceBalanceOnWithdrawal(_claimer, _stabAsset, claimShares, True)

    # reduce claimable balances
    self._reduceClaimableBalances(_stabAsset, _claimAsset, claimAmount, maxClaimableAsset)

    # move tokens to recipient
    assert extcall IERC20(_claimAsset).transfer(_claimer, claimAmount, default_return_value=True) # dev: token transfer failed

    log AssetClaimedInStabilityPool(user=_claimer, stabAsset=_stabAsset, claimAsset=_claimAsset, claimAmount=claimAmount, claimUsdValue=claimUsdValue, claimShares=claimShares, isDepleted=isDepleted)
    return claimUsdValue


@view
@internal
def _calcClaimSharesAndAmount(
    _claimer: address,
    _stabAsset: address,
    _claimAsset: address,
    _maxUsdValue: uint256,
    _maxClaimableAsset: uint256,
    _priceDesk: address,
) -> (uint256, uint256, uint256):

    # NOTE: failing gracefully here, in case of many claims at same time

    # total claimable asset
    totalClaimAsset: uint256 = min(_maxClaimableAsset, staticcall IERC20(_claimAsset).balanceOf(self))
    if totalClaimAsset == 0:
        return 0, 0, 0 # no claimable asset

    # user shares
    maxUserShares: uint256 = vaultData.userBalances[_claimer][_stabAsset]
    if maxUserShares == 0:
        return 0, 0, 0 # no user shares

    # totals
    totalShares: uint256 = vaultData.totalBalances[_stabAsset]
    totalValue: uint256 = self._getTotalValue(_stabAsset)

    # max claim values for user
    maxClaimUsdValue: uint256 = self._sharesToValue(maxUserShares, totalShares, totalValue, False)
    maxClaimAmount: uint256 = staticcall PriceDesk(_priceDesk).getAssetAmount(_claimAsset, maxClaimUsdValue, True)
    if maxClaimAmount == 0:
        return 0, 0, 0 # not getting price for claim asset

    # max amount available to withdraw
    if _maxUsdValue >= maxClaimUsdValue and maxClaimAmount <= totalClaimAsset:
        return maxUserShares, maxClaimAmount, maxClaimUsdValue

    # finalize withdrawal amount / shares
    claimAmount: uint256 = min(maxClaimAmount, totalClaimAsset)
    if _maxUsdValue != max_value(uint256):
        claimAmount = min(claimAmount, _maxUsdValue * maxClaimAmount // maxClaimUsdValue)

    # finalize values
    claimUsdValue: uint256 = claimAmount * maxClaimUsdValue // maxClaimAmount
    claimShares: uint256 = min(maxUserShares, self._valueToShares(claimUsdValue, totalShares, totalValue, True))
    return claimShares, claimAmount, claimUsdValue


###############
# Redemptions #
###############


@external
def redeemFromStabilityPool(
    _asset: address,
    _greenAmount: uint256,
    _redeemer: address,
    _wantsSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert not vaultData.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    assert self._canRedeemInThisVault(a.greenToken) # dev: redemptions not allowed

    greenAmount: uint256 = min(_greenAmount, staticcall IERC20(a.greenToken).balanceOf(self))
    assert greenAmount != 0 # dev: no green to redeem
    greenSpent: uint256 = self._redeemFromStabilityPool(_redeemer, _asset, max_value(uint256), greenAmount, a.greenToken, a.priceDesk, a.controlRoom)

    # handle leftover green
    if greenAmount > greenSpent:
        self._handleGreenForUser(_redeemer, greenAmount - greenSpent, _wantsSavingsGreen, a.greenToken, a.savingsGreen)

    return greenSpent


@external
def redeemManyFromStabilityPool(
    _redemptions: DynArray[StabPoolRedemption, MAX_STAB_REDEMPTIONS],
    _greenAmount: uint256,
    _redeemer: address,
    _wantsSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert not vaultData.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    assert self._canRedeemInThisVault(a.greenToken) # dev: redemptions not allowed

    totalGreenSpent: uint256 = 0
    totalGreenRemaining: uint256 = min(_greenAmount, staticcall IERC20(a.greenToken).balanceOf(self))
    assert totalGreenRemaining != 0 # dev: no green to redeem

    for r: StabPoolRedemption in _redemptions:
        if totalGreenRemaining == 0:
            break
        greenSpent: uint256 = self._redeemFromStabilityPool(_redeemer, r.claimAsset, r.maxGreenAmount, totalGreenRemaining, a.greenToken, a.priceDesk, a.controlRoom)
        totalGreenRemaining -= greenSpent
        totalGreenSpent += greenSpent

    # handle leftover green
    if totalGreenRemaining != 0:
        self._handleGreenForUser(_redeemer, totalGreenRemaining, _wantsSavingsGreen, a.greenToken, a.savingsGreen)

    return totalGreenSpent


@view
@internal
def _canRedeemInThisVault(_greenToken: address) -> bool:
    # if green is a stab asset, then it must be the ONLY asset in the vault
    if vaultData.indexOfAsset[_greenToken] != 0:
        return vaultData._getNumVaultAssets() == 1
    return True


@internal
def _redeemFromStabilityPool(
    _redeemer: address,
    _asset: address,
    _maxGreenForAsset: uint256,
    _totalGreenRemaining: uint256,
    _greenToken: address,
    _priceDesk: address,
    _controlRoom: address,
) -> uint256:

    # NOTE: failing gracefully here, in case of many redemptions at same time

    # invalid inputs
    if empty(address) in [_redeemer, _asset] or 0 in [_maxGreenForAsset, _totalGreenRemaining]:
        return 0

    # check redemption config
    config: StabPoolRedemptionsConfig = staticcall ControlRoom(_controlRoom).getStabPoolRedemptionsConfig(_asset, _redeemer)
    if not config.canRedeemInStabPoolGeneral or not config.canRedeemInStabPoolAsset or not config.isUserAllowed:
        return 0

    # cannot redeem green token
    if _asset == _greenToken:
        return 0

    # treating green as $1
    maxGreenAvailable: uint256 = min(_totalGreenRemaining, staticcall IERC20(_greenToken).balanceOf(self))
    maxRedeemValue: uint256 = min(_maxGreenForAsset, maxGreenAvailable)
    if maxRedeemValue == 0:
        return 0

    # max claimable amount
    maxClaimableAmount: uint256 = staticcall PriceDesk(_priceDesk).getAssetAmount(_asset, maxRedeemValue, True)
    if maxClaimableAmount == 0:
        return 0

    # total claimable asset
    actualClaimableAmount: uint256 = min(self.totalClaimableBalances[_asset], staticcall IERC20(_asset).balanceOf(self))
    if actualClaimableAmount == 0:
        return 0

    # finalize amounts
    remainingRedeemValue: uint256 = maxRedeemValue
    remainingClaimAmount: uint256 = maxClaimableAmount
    if maxClaimableAmount > actualClaimableAmount:
        remainingRedeemValue = min(actualClaimableAmount * maxRedeemValue // maxClaimableAmount, maxRedeemValue)
        remainingClaimAmount = actualClaimableAmount

    greenSpent: uint256 = 0
    numStabAssets: uint256 = vaultData.numAssets
    if numStabAssets == 0:
        return 0

    # iterate thru stab assets
    for i: uint256 in range(1, numStabAssets, bound=max_value(uint256)):
        if remainingClaimAmount == 0 or remainingRedeemValue == 0:
            break

        stabAsset: address = vaultData.vaultAssets[i]
        if stabAsset == empty(address):
            continue

        # claimable balance
        claimableBalance: uint256 = self.claimableBalances[stabAsset][_asset]
        if claimableBalance == 0:
            continue

        # reduce claimable balances
        claimAmount: uint256 = min(remainingClaimAmount, claimableBalance)
        self._reduceClaimableBalances(stabAsset, _asset, claimAmount, claimableBalance)
        assert extcall IERC20(_asset).transfer(_redeemer, claimAmount, default_return_value=True) # dev: transfer failed
        remainingClaimAmount -= claimAmount

        # add green to claimable
        redeemAmount: uint256 = min(claimAmount * maxRedeemValue // maxClaimableAmount, remainingRedeemValue)
        self._addClaimableBalance(stabAsset, _greenToken, redeemAmount)
        remainingRedeemValue -= redeemAmount
        greenSpent += redeemAmount

    return greenSpent


##################
# Green Handling #
##################


@internal
def _handleGreenForUser(
    _recipient: address,
    _greenAmount: uint256,
    _wantsSavingsGreen: bool,
    _greenToken: address,
    _savingsGreen: address,
):
    amount: uint256 = min(_greenAmount, staticcall IERC20(_greenToken).balanceOf(self))
    if amount == 0:
        return

    if _wantsSavingsGreen:
        extcall IERC4626(_savingsGreen).deposit(amount, _recipient)
    else:
        assert extcall IERC20(_greenToken).transfer(_recipient, amount, default_return_value=True) # dev: green transfer failed


##################
# Claimable Data #
##################


# add claimable


@internal
def _addClaimableBalance(
    _stabAsset: address,
    _claimAsset: address,
    _claimAmount: uint256,
):
    claimAmount: uint256 = min(_claimAmount, staticcall IERC20(_claimAsset).balanceOf(self))
    assert claimAmount != 0 # dev: nothing received

    # update balances
    self.claimableBalances[_stabAsset][_claimAsset] += claimAmount
    self.totalClaimableBalances[_claimAsset] += claimAmount

    # register claimable asset if not already registered
    if self.indexOfClaimableAsset[_stabAsset][_claimAsset] == 0:
        self._registerClaimableAsset(_stabAsset, _claimAsset)


# register claimable asset


@internal
def _registerClaimableAsset(_stabAsset: address, _assetReceived: address):
    cid: uint256 = self.numClaimableAssets[_stabAsset]
    if cid == 0:
        cid = 1 # not using 0 index
    self.claimableAssets[_stabAsset][cid] = _assetReceived
    self.indexOfClaimableAsset[_stabAsset][_assetReceived] = cid
    self.numClaimableAssets[_stabAsset] = cid + 1


# reduce claimable


@internal
def _reduceClaimableBalances(
    _stabAsset: address,
    _claimAsset: address,
    _claimAmount: uint256,
    _prevClaimableBalance: uint256,
):
    newClaimableBalance: uint256 = _prevClaimableBalance - _claimAmount
    self.claimableBalances[_stabAsset][_claimAsset] = newClaimableBalance
    self.totalClaimableBalances[_claimAsset] -= _claimAmount

    # remove claimable asset if depleted
    if newClaimableBalance == 0:
        self._removeClaimableAsset(_stabAsset, _claimAsset)


# deregister claimable asset


@internal
def _removeClaimableAsset(_stabAsset: address, _asset: address):
    numAssets: uint256 = self.numClaimableAssets[_stabAsset]
    if numAssets == 0:
        return

    targetIndex: uint256 = self.indexOfClaimableAsset[_stabAsset][_asset]
    if targetIndex == 0:
        return

    # update data
    lastIndex: uint256 = numAssets - 1
    self.numClaimableAssets[_stabAsset] = lastIndex
    self.indexOfClaimableAsset[_stabAsset][_asset] = 0

    # shift to replace the one being removed
    if targetIndex != lastIndex:
        lastAsset: address = self.claimableAssets[_stabAsset][lastIndex]
        self.claimableAssets[_stabAsset][targetIndex] = lastAsset
        self.indexOfClaimableAsset[_stabAsset][lastAsset] = targetIndex