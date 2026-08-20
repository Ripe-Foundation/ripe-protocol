# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

uses: vaultData
uses: addys

import contracts.vaults.modules.VaultData as vaultData
import contracts.modules.Addys as addys

from interfaces import Vault
from ethereum.ercs import IERC4626
from ethereum.ercs import IERC20

interface MissionControl:
    def getStabPoolClaimsConfig(_claimAsset: address, _claimer: address, _caller: address, _ripeToken: address) -> StabPoolClaimsConfig: view
    def getTellerDepositConfig(_vaultId: uint256, _asset: address, _user: address) -> TellerDepositConfig: view
    def getStabPoolRedemptionsConfig(_asset: address, _recipient: address) -> StabPoolRedemptionsConfig: view
    def getFirstVaultIdForAsset(_asset: address) -> uint256: view
    def coreRipeGovVaultId() -> uint256: view

interface Teller:
    def depositFromTrusted(_user: address, _vaultId: uint256, _asset: address, _amount: uint256, _lockDuration: uint256, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def isUnderscoreWalletOwner(_user: address, _caller: address, _mc: address = empty(address)) -> bool: view

interface PriceDesk:
    def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256: view
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface VaultBook:
    def mintRipeForStabPoolClaims(_amount: uint256, _ripeToken: address, _ledger: address) -> bool: nonpayable
    def getRegId(_vaultAddr: address) -> uint256: view

interface GreenToken:
    def burn(_amount: uint256) -> bool: nonpayable

interface Ledger:
    def ripeAvailForRewards() -> uint256: view

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
    canClaimFromStabPoolForUser: bool
    isUserAllowed: bool
    rewardsLockDuration: uint256
    ripePerDollarClaimed: uint256

struct StabPoolRedemptionsConfig:
    canRedeemInStabPoolGeneral: bool
    canRedeemInStabPoolAsset: bool
    isUserAllowed: bool
    canAnyoneDeposit: bool

struct TellerDepositConfig:
    canDepositGeneral: bool
    canDepositAsset: bool
    doesVaultSupportAsset: bool
    isUserAllowed: bool
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
    perUserMaxAssetsPerVault: uint256
    perUserMaxVaults: uint256
    canAnyoneDeposit: bool

event AssetClaimedInStabilityPool:
    user: indexed(address)
    stabAsset: indexed(address)
    claimAsset: indexed(address)
    claimAmount: uint256
    claimUsdValue: uint256
    claimShares: uint256
    isDepleted: bool

event ClaimAssetActivated:
    stabAsset: indexed(address)
    claimAsset: indexed(address)
    balance: uint256
    activeCount: uint256

event ClaimAssetDeactivated:
    stabAsset: indexed(address)
    claimAsset: indexed(address)
    balance: uint256
    activeCount: uint256
    reason: uint256

event ClaimAssetLeftDormant:
    stabAsset: indexed(address)
    claimAsset: indexed(address)
    balance: uint256
    activeCount: uint256
    reason: uint256

# claimable balances
claimableBalances: public(HashMap[address, HashMap[address, uint256]]) # stab asset -> claimable asset -> balance
totalClaimableBalances: public(HashMap[address, uint256]) # claimable asset -> balance

# claimable assets (iterable)
claimableAssets: public(HashMap[address, HashMap[uint256, address]]) # stab asset -> index -> claimable asset
indexOfClaimableAsset: public(HashMap[address, HashMap[address, uint256]]) # stab asset -> claimable asset -> index
numClaimableAssets: public(HashMap[address, uint256]) # stab asset -> num claimable assets

MAX_STAB_CLAIMS: constant(uint256) = 15
MAX_STAB_REDEMPTIONS: constant(uint256) = 15
MAX_ACTIVE_CLAIM_ASSETS: constant(uint256) = 20
MAX_CLAIM_ASSET_MAINTENANCE: constant(uint256) = 15
DECIMAL_OFFSET: constant(uint256) = 10 ** 8
EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
ACTIVATION_USD_THRESHOLD: constant(uint256) = 10 * 10 ** 16  # $0.10 in 18-decimal USD
RETENTION_USD_THRESHOLD: constant(uint256) = 5 * 10 ** 16  # $0.05 in 18-decimal USD
# Live residual delisting is bounded to R <= P // 10**10. This caps omitted
# membership to one ten-billionth of the prior per-cohort pair. A correctly
# priced $100M pair implies at most approximately $0.01 of omitted residual.
# For a 6-decimal asset, one base unit can qualify only when P >= 10**10 raw
# units, i.e. 10,000 whole tokens.
LIVE_RESIDUAL_DIVISOR: constant(uint256) = 10 ** 10

CLAIM_ASSET_ABSENT: constant(uint256) = 0
CLAIM_ASSET_DORMANT: constant(uint256) = 1
CLAIM_ASSET_ACTIVE: constant(uint256) = 2

DEACTIVATION_ZERO: constant(uint256) = 1
DEACTIVATION_DUST: constant(uint256) = 2

DORMANT_BELOW_FLOOR: constant(uint256) = 1

GREEN_TOKEN: immutable(address)
SAVINGS_GREEN: immutable(address)


@deploy
def __init__():
    GREEN_TOKEN = addys._getGreenToken()
    SAVINGS_GREEN = addys._getSavingsGreen()


@view
@internal
def _getStabAddys() -> (address, address, address):
    return GREEN_TOKEN, SAVINGS_GREEN, addys._getPriceDeskAddr()


@view
@internal
def _getUnreservedBalance(_asset: address) -> uint256:
    custody: uint256 = staticcall IERC20(_asset).balanceOf(self)
    reserved: uint256 = self.totalClaimableBalances[_asset]
    assert custody >= reserved # dev: claim custody deficit
    return custody - reserved


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
    assert not vaultData.isPaused # dev: contract paused

    # validation
    assert empty(address) not in [_user, _asset] # dev: invalid user or asset
    assert _asset != _a.greenToken # dev: green cannot be stab asset
    assert self.totalClaimableBalances[_asset] == 0 # dev: asset reserved for claims
    totalAssetBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    depositAmount: uint256 = min(_amount, totalAssetBalance)
    assert depositAmount != 0 # dev: invalid deposit amount

    # calc usd values
    totalStabValue: uint256 = self._getUsdValue(_asset, totalAssetBalance, _a.greenToken, _a.savingsGreen, _a.priceDesk, True)
    assert totalStabValue != 0 # dev: no price for stab asset

    newUserValue: uint256 = totalStabValue
    prevStabValue: uint256 = 0
    if depositAmount != totalAssetBalance:
        newUserValue = depositAmount * totalStabValue // totalAssetBalance
        prevStabValue = (totalAssetBalance - depositAmount) * totalStabValue // totalAssetBalance # remove the deposited amount to calc shares accurately

    # calc shares
    claimableValue: uint256 = self._getValueOfClaimableAssets(_asset, _a.greenToken, _a.savingsGreen, _a.priceDesk)
    newShares: uint256 = self._valueToShares(newUserValue, vaultData.totalBalances[_asset], prevStabValue + claimableValue, False)
    assert newShares != 0 # dev: cannot mint 0 shares

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
    assert not vaultData.isPaused # dev: contract paused
    assert empty(address) not in [_user, _asset, _recipient] # dev: invalid user, asset, or recipient

    # calc shares + amount to withdraw
    withdrawalShares: uint256 = 0
    withdrawalAmount: uint256 = 0
    withdrawalShares, withdrawalAmount = self._calcWithdrawalSharesAndAmount(_user, _asset, _amount, _a)

    # reduce balance on withdrawal
    isDepleted: bool = False
    withdrawalShares, isDepleted = vaultData._reduceBalanceOnWithdrawal(_user, _asset, withdrawalShares, True)

    self._transferAssetExact(_asset, withdrawalAmount, _recipient)
    return withdrawalAmount, withdrawalShares, isDepleted


@internal
def _transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
    _a: addys.Addys,
) -> (uint256, uint256, bool):
    assert not vaultData.isPaused # dev: contract paused
    assert empty(address) not in [_fromUser, _toUser, _asset] # dev: invalid users or asset

    # calc shares + amount to transfer
    transferShares: uint256 = 0
    transferAmount: uint256 = 0
    transferShares, transferAmount = self._calcWithdrawalSharesAndAmount(_fromUser, _asset, _transferAmount, _a)

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
    return vaultData.userBalances[_user][_asset] // DECIMAL_OFFSET


@view
@internal
def _getCohortLiquidationAmount(_stabAsset: address) -> uint256:
    if vaultData.isPaused:
        return 0

    # Liquidation readiness consumes PriceDesk's non-raising zero-price
    # boundary. Strict accounting paths retain their existing fail-closed NAV
    # calls; this path returns zero so AuctionHouse skips the cohort and uses
    # its mandatory ordinary-auction fallback. Keep this mirror aligned with
    # both _getTotalAmountForVault and
    # _getValueOfClaimableAssets when their custody or valuation inputs change.
    custody: uint256 = staticcall IERC20(_stabAsset).balanceOf(self)
    reserved: uint256 = self.totalClaimableBalances[_stabAsset]
    if custody <= reserved:
        return 0

    stabAssetBalance: uint256 = custody - reserved
    priceDesk: address = addys._getPriceDeskAddr()
    totalStabValue: uint256 = self._getUsdValue(_stabAsset, stabAssetBalance, GREEN_TOKEN, SAVINGS_GREEN, priceDesk, False)
    if totalStabValue == 0:
        return 0

    claimableValue: uint256 = 0
    numClaimableAssets: uint256 = self.numClaimableAssets[_stabAsset]
    if numClaimableAssets != 0:
        for i: uint256 in range(1, numClaimableAssets, bound=max_value(uint256)):
            claimAsset: address = self.claimableAssets[_stabAsset][i]
            claimBalance: uint256 = self.claimableBalances[_stabAsset][claimAsset]
            if claimBalance == 0:
                continue

            # A claim is usable only when aggregate custody covers every cohort's
            # liability and PriceDesk can establish a non-zero value without
            # raising. Any zero result makes this cohort unavailable for now.
            if staticcall IERC20(claimAsset).balanceOf(self) < self.totalClaimableBalances[claimAsset]:
                return 0

            claimValue: uint256 = self._getUsdValue(claimAsset, claimBalance, GREEN_TOKEN, SAVINGS_GREEN, priceDesk, False)
            if claimValue == 0:
                return 0

            claimableValue += claimValue

    if claimableValue == 0:
        return stabAssetBalance

    return self._getAssetAmount(_stabAsset, totalStabValue + claimableValue, GREEN_TOKEN, SAVINGS_GREEN, priceDesk, False)


@view
@internal
def _getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
    # CreditEngine excludes Stability Pool vault IDs before collateral valuation.
    # AuctionHouse uses this iterator in liquidation phase 2; an unhealthy cohort
    # deliberately reports zero so liquidation can continue through the ordinary
    # auction path while its nominal position and asset enumeration remain intact.
    asset: address = vaultData.userAssets[_user][_index]
    if asset == empty(address):
        return empty(address), 0
    totalAmount: uint256 = self._getCohortLiquidationAmount(asset)
    if totalAmount == 0:
        return asset, 0
    return asset, self._getTotalAmountForUserWithTotalBal(_user, asset, totalAmount)


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
    # Liquidation-safe mirror: _getCohortLiquidationAmount. Keep its custody and
    # valuation inputs aligned while preserving this strict accounting path.

    # addys
    greenToken: address = empty(address)
    savingsGreen: address = empty(address)
    priceDesk: address = empty(address)
    greenToken, savingsGreen, priceDesk = self._getStabAddys()

    # get total value of asset
    stabAssetBalance: uint256 = self._getUnreservedBalance(_asset)
    totalStabValue: uint256 = self._getUsdValue(_asset, stabAssetBalance, greenToken, savingsGreen, priceDesk, True)
    claimableValue: uint256 = self._getValueOfClaimableAssets(_asset, greenToken, savingsGreen, priceDesk)

    # return amount if there is claimable value
    if claimableValue != 0:
        return self._getAssetAmount(_asset, totalStabValue + claimableValue, greenToken, savingsGreen, priceDesk, True)

    return stabAssetBalance


@view
@internal
def _getAssetAmount(
    _asset: address,
    _targetUsdValue: uint256,
    _greenToken: address,
    _savingsGreen: address,
    _priceDesk: address,
    _shouldRaise: bool,
) -> uint256:
    if _asset == _greenToken:
        return _targetUsdValue
    if _asset == _savingsGreen:
        return staticcall IERC4626(_savingsGreen).convertToShares(_targetUsdValue)
    return staticcall PriceDesk(_priceDesk).getAssetAmount(_asset, _targetUsdValue, _shouldRaise)


@view
@internal
def _getUsdValue(
    _asset: address,
    _amount: uint256,
    _greenToken: address,
    _savingsGreen: address,
    _priceDesk: address,
    _shouldRaise: bool,
) -> uint256:
    if _asset == _greenToken:
        return _amount
    if _asset == _savingsGreen:
        return staticcall IERC4626(_savingsGreen).convertToAssets(_amount)
    return staticcall PriceDesk(_priceDesk).getUsdValue(_asset, _amount, _shouldRaise)


##########
# Shares #
##########


@view
@internal
def _calcWithdrawalSharesAndAmount(
    _user: address,
    _asset: address,
    _amount: uint256,
    _a: addys.Addys,
) -> (uint256, uint256):
    totalShares: uint256 = vaultData.totalBalances[_asset]
    totalStabAssetBalance: uint256 = self._getUnreservedBalance(_asset)
    assert totalStabAssetBalance != 0 # dev: no stab asset to withdraw

    # user shares
    withdrawalShares: uint256 = vaultData.userBalances[_user][_asset]
    assert withdrawalShares != 0 # dev: user has no shares

    # calc usd values
    totalStabValue: uint256 = self._getUsdValue(_asset, totalStabAssetBalance, _a.greenToken, _a.savingsGreen, _a.priceDesk, True)
    assert totalStabValue != 0 # dev: no price for stab asset
    claimableValue: uint256 = self._getValueOfClaimableAssets(_asset, _a.greenToken, _a.savingsGreen, _a.priceDesk)
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
    greenToken: address = addys._getGreenToken()
    savingsGreen: address = addys._getSavingsGreen()
    priceDesk: address = addys._getPriceDeskAddr()
    totalValue: uint256 = self._getTotalValue(_asset, greenToken, savingsGreen, priceDesk)
    return self._valueToShares(_usdValue, vaultData.totalBalances[_asset], totalValue, _shouldRoundUp)


@view
@internal
def _valueToShares(
    _usdValue: uint256,
    _totalShares: uint256,
    _totalUsdValue: uint256,
    _shouldRoundUp: bool,
) -> uint256:
    return self._mulDiv(_usdValue, _totalShares + DECIMAL_OFFSET, _totalUsdValue + 1, _shouldRoundUp)


# shares -> usd value


@view
@external
def sharesToValue(_asset: address, _shares: uint256, _shouldRoundUp: bool) -> uint256:
    greenToken: address = addys._getGreenToken()
    savingsGreen: address = addys._getSavingsGreen()
    priceDesk: address = addys._getPriceDeskAddr()
    totalValue: uint256 = self._getTotalValue(_asset, greenToken, savingsGreen, priceDesk)
    return self._sharesToValue(_shares, vaultData.totalBalances[_asset], totalValue, _shouldRoundUp)


@view
@internal
def _sharesToValue(
    _shares: uint256,
    _totalShares: uint256,
    _totalUsdValue: uint256,
    _shouldRoundUp: bool,
) -> uint256:
    return self._mulDiv(_shares, _totalUsdValue + 1, _totalShares + DECIMAL_OFFSET, _shouldRoundUp)


@view
@internal
def _mulDiv(
    _amount: uint256,
    _multiplier: uint256,
    _denominator: uint256,
    _shouldRoundUp: bool,
) -> uint256:
    numerator: uint256 = _amount * _multiplier
    result: uint256 = numerator // _denominator
    if _shouldRoundUp and numerator % _denominator != 0:
        result += 1
    return result


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
    _savingsGreenToken: address,
) -> uint256:
    self._validateLiquidationSwap(_stabAsset, _liqAsset, msg.sender)

    # add claimable balance
    self._addSwapClaimable(_stabAsset, _liqAsset, _liqAmountSent)

    # finalize amount
    amount: uint256 = min(_stabAssetAmount, self._getUnreservedBalance(_stabAsset))
    assert amount != 0 # dev: nothing to transfer

    # burn green token
    if _recipient == empty(address):
        assert _stabAsset in [_greenToken, _savingsGreenToken] # dev: must be green or savings green
        if _stabAsset == _savingsGreenToken:
            greenAmount: uint256 = extcall IERC4626(_savingsGreenToken).redeem(amount, self, self) # dev: savings green redeem failed
            assert extcall GreenToken(_greenToken).burn(greenAmount) # dev: failed to burn green
        else:
            assert extcall GreenToken(_greenToken).burn(amount) # dev: failed to burn green

    else:
        assert extcall IERC20(_stabAsset).transfer(_recipient, amount, default_return_value=True) # dev: transfer failed

    return amount


@external
def swapWithClaimableGreen(
    _stabAsset: address,
    _greenAmount: uint256,
    _liqAsset: address,
    _liqAmountSent: uint256,
    _greenToken: address,
) -> uint256:
    self._validateLiquidationSwap(_stabAsset, _liqAsset, msg.sender)

    # add claimable balance
    self._addSwapClaimable(_stabAsset, _liqAsset, _liqAmountSent)

    # finalize amount
    maxClaimableGreen: uint256 = self.claimableBalances[_stabAsset][_greenToken]
    greenAvailable: uint256 = min(maxClaimableGreen, staticcall IERC20(_greenToken).balanceOf(self))
    amount: uint256 = min(_greenAmount, greenAvailable)
    assert amount != 0 # dev: no green

    # reduce green from claimable, and burn
    # NOTE: GREEN is 1:1 with USD, so remainingUsdValue = remaining balance
    self._reduceClaimableBalances(_stabAsset, _greenToken, amount, maxClaimableGreen, maxClaimableGreen - amount)
    assert extcall GreenToken(_greenToken).burn(amount) # dev: burn failed

    return amount


@view
@internal
def _validateLiquidationSwap(_stabAsset: address, _liqAsset: address, _sender: address):
    assert not vaultData.isPaused # dev: contract paused
    assert _sender == addys._getAuctionHouseAddr() # dev: only AuctionHouse allowed

    assert vaultData.indexOfAsset[_stabAsset] != 0 # dev: stab asset not supported
    assert vaultData.indexOfAsset[_liqAsset] == 0 # dev: liq asset cannot be vault asset
    assert _liqAsset != empty(address) # dev: invalid liq asset
    assert _stabAsset != GREEN_TOKEN # dev: green cannot be stab asset


@internal
def _addSwapClaimable(
    _stabAsset: address,
    _claimAsset: address,
    _reportedAmount: uint256,
):
    priceDesk: address = addys._getPriceDeskAddr()
    self._addClaimableBalance(_stabAsset, _claimAsset, _reportedAmount, priceDesk)


# utilities


@view
@external
def getTotalValue(_asset: address) -> uint256:
    return self._getCurrentTotalValue(_asset)


@view
@external
def getTotalUserValue(_user: address, _asset: address) -> uint256:
    totalValue: uint256 = self._getCurrentTotalValue(_asset)
    return self._sharesToValue(vaultData.userBalances[_user][_asset], vaultData.totalBalances[_asset], totalValue, False)


@view
@internal
def _getCurrentTotalValue(_asset: address) -> uint256:
    return self._getTotalValue(_asset, GREEN_TOKEN, SAVINGS_GREEN, addys._getPriceDeskAddr())


@view
@internal
def _getTotalValue(
    _asset: address,
    _greenToken: address,
    _savingsGreen: address,
    _priceDesk: address,
) -> uint256:
    totalStabValue: uint256 = 0
    stabAssetBalance: uint256 = self._getUnreservedBalance(_asset)
    if stabAssetBalance != 0:
        totalStabValue = self._getUsdValue(_asset, stabAssetBalance, _greenToken, _savingsGreen, _priceDesk, True)
    claimableValue: uint256 = self._getValueOfClaimableAssets(_asset, _greenToken, _savingsGreen, _priceDesk)
    return totalStabValue + claimableValue


@view
@internal
def _getValueOfClaimableAssets(
    _stabAsset: address,
    _greenToken: address,
    _savingsGreen: address,
    _priceDesk: address,
) -> uint256:
    # Liquidation-safe mirror: _getCohortLiquidationAmount. Keep its aggregate
    # custody and per-claim valuation inputs aligned with this strict path.
    totalValue: uint256 = 0
    numClaimableAssets: uint256 = self.numClaimableAssets[_stabAsset]
    if numClaimableAssets == 0:
        return 0

    for i: uint256 in range(1, numClaimableAssets, bound=max_value(uint256)):
        asset: address = self.claimableAssets[_stabAsset][i]
        balance: uint256 = self.claimableBalances[_stabAsset][asset]
        if balance == 0:
            continue

        # A claim is part of this cohort's NAV until its liability is settled.
        # Moving shares while its price is unavailable would transfer that
        # future value between cohorts, so valuation must fail closed.  The
        # aggregate custody check also covers this asset's liabilities to every
        # stability-asset cohort, not only the pair currently being valued.
        # PriceDesk floors a nonzero amount at a nonzero price to one USD-value
        # unit; an unavailable price still fails closed.
        assert staticcall IERC20(asset).balanceOf(self) >= self.totalClaimableBalances[asset] # dev: claim custody deficit
        claimValue: uint256 = self._getUsdValue(asset, balance, _greenToken, _savingsGreen, _priceDesk, True)
        assert claimValue != 0 # dev: no price for claim asset
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
    _caller: address,
    _shouldAutoDeposit: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    claims: DynArray[StabPoolClaim, MAX_STAB_CLAIMS] = []
    claims.append(StabPoolClaim(
        stabAsset=_stabAsset,
        claimAsset=_claimAsset,
        maxUsdValue=_maxUsdValue,
    ))
    return self._claimManyFromStabilityPool(_claimer, claims, _caller, _shouldAutoDeposit, _a)


@external
def claimManyFromStabilityPool(
    _claimer: address,
    _claims: DynArray[StabPoolClaim, MAX_STAB_CLAIMS],
    _caller: address,
    _shouldAutoDeposit: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    return self._claimManyFromStabilityPool(_claimer, _claims, _caller, _shouldAutoDeposit, _a)


@internal
def _claimManyFromStabilityPool(
    _claimer: address,
    _claims: DynArray[StabPoolClaim, MAX_STAB_CLAIMS],
    _caller: address,
    _shouldAutoDeposit: bool,
    _a: addys.Addys,
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert not vaultData.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)
    config: StabPoolClaimsConfig = empty(StabPoolClaimsConfig)

    totalUsdValue: uint256 = 0
    for c: StabPoolClaim in _claims:
        config = staticcall MissionControl(a.missionControl).getStabPoolClaimsConfig(c.claimAsset, _claimer, _caller, a.ripeToken)
        totalUsdValue += self._claimFromStabilityPool(_claimer, c.stabAsset, c.claimAsset, c.maxUsdValue, _caller, _shouldAutoDeposit, config, a)
    assert totalUsdValue != 0 # dev: nothing claimed
    self._handleClaimRewards(_claimer, totalUsdValue, config.rewardsLockDuration, config.ripePerDollarClaimed, a)
    return totalUsdValue


@internal
def _claimFromStabilityPool(
    _claimer: address,
    _stabAsset: address,
    _claimAsset: address,
    _maxUsdValue: uint256,
    _caller: address,
    _shouldAutoDeposit: bool,
    _config: StabPoolClaimsConfig,
    _a: addys.Addys,
) -> uint256:
    if empty(address) in [_claimer, _stabAsset, _claimAsset] or _maxUsdValue == 0:
        return 0

    # check claims config
    if not _config.canClaimInStabPoolGeneral or not _config.canClaimInStabPoolAsset or not _config.isUserAllowed:
        return 0

    # can others claim for user
    if _claimer != _caller and not _config.canClaimFromStabPoolForUser:
        assert staticcall Teller(_a.teller).isUnderscoreWalletOwner(_claimer, _caller, _a.missionControl) # dev: cannot claim for user

    # max claimable asset
    maxClaimableAsset: uint256 = self.claimableBalances[_stabAsset][_claimAsset]
    if maxClaimableAsset == 0:
        return 0

    # calc shares + amount to withdraw
    claimShares: uint256 = 0
    claimAmount: uint256 = 0
    claimUsdValue: uint256 = 0
    claimShares, claimAmount, claimUsdValue = self._calcClaimSharesAndAmount(_claimer, _stabAsset, _claimAsset, _maxUsdValue, maxClaimableAsset, _a)
    if claimShares == 0:
        return 0

    # reduce balance on withdrawal
    isDepleted: bool = False
    claimShares, isDepleted = vaultData._reduceBalanceOnWithdrawal(_claimer, _stabAsset, claimShares, True)

    # reduce claimable balances - compute remaining USD value using price ratio from claim calculation
    remainingUsdValue: uint256 = 0
    if claimAmount < maxClaimableAsset:
        numerator: uint256 = (maxClaimableAsset - claimAmount) * claimUsdValue
        if numerator < claimAmount:
            remainingUsdValue = 1 # very small dust, trigger removal
        else:
            remainingUsdValue = numerator // claimAmount
    self._reduceClaimableBalances(_stabAsset, _claimAsset, claimAmount, maxClaimableAsset, remainingUsdValue)

    # move tokens to recipient
    self._handleAssetForUser(_claimAsset, claimAmount, _claimer, _shouldAutoDeposit, _a)

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
    _a: addys.Addys,
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
    totalValue: uint256 = self._getTotalValue(_stabAsset, _a.greenToken, _a.savingsGreen, _a.priceDesk)

    # max claim values for user
    maxClaimUsdValue: uint256 = self._sharesToValue(maxUserShares, totalShares, totalValue, False)
    maxClaimAmount: uint256 = self._getAssetAmount(_claimAsset, maxClaimUsdValue, _a.greenToken, _a.savingsGreen, _a.priceDesk, True)
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


@internal
def _handleClaimRewards(
    _claimer: address,
    _claimUsdValue: uint256,
    _lockDuration: uint256,
    _ripePerDollarClaimed: uint256,
    _a: addys.Addys,
):
    if _ripePerDollarClaimed == 0:
        return

    ripeClaimRewards: uint256 = _claimUsdValue * _ripePerDollarClaimed // EIGHTEEN_DECIMALS
    ripeAvailable: uint256 = min(ripeClaimRewards, staticcall Ledger(_a.ledger).ripeAvailForRewards())
    if ripeAvailable == 0:
        return

    coreRipeGovVaultId: uint256 = staticcall MissionControl(_a.missionControl).coreRipeGovVaultId()
    assert coreRipeGovVaultId != 0 # dev: invalid vault id

    # mint ripe
    assert extcall VaultBook(_a.vaultBook).mintRipeForStabPoolClaims(ripeAvailable, _a.ripeToken, _a.ledger) # dev: mint failed

    # deposit into gov vault
    assert extcall IERC20(_a.ripeToken).approve(_a.teller, ripeAvailable, default_return_value=True) # dev: ripe approval failed
    extcall Teller(_a.teller).depositFromTrusted(_claimer, coreRipeGovVaultId, _a.ripeToken, ripeAvailable, _lockDuration, _a)
    assert extcall IERC20(_a.ripeToken).approve(_a.teller, 0, default_return_value=True) # dev: ripe approval failed


###############
# Redemptions #
###############


@external
def redeemFromStabilityPool(
    _asset: address,
    _greenAmount: uint256,
    _recipient: address,
    _caller: address,
    _shouldAutoDeposit: bool,
    _shouldRefundSavingsGreen: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert not vaultData.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    assert self._canRedeemInThisVault(a.greenToken) # dev: redemptions not allowed

    greenAmount: uint256 = min(_greenAmount, staticcall IERC20(a.greenToken).balanceOf(self))
    assert greenAmount != 0 # dev: no green to redeem
    greenSpent: uint256 = self._redeemFromStabilityPool(_recipient, _caller, _asset, max_value(uint256), greenAmount, _shouldAutoDeposit, a)
    assert greenSpent != 0 # dev: no redemptions occurred

    # handle leftover green
    if greenAmount > greenSpent:
        self._handleGreenForUser(_caller, greenAmount - greenSpent, _shouldRefundSavingsGreen, a.greenToken, a.savingsGreen)

    return greenSpent


@external
def redeemManyFromStabilityPool(
    _redemptions: DynArray[StabPoolRedemption, MAX_STAB_REDEMPTIONS],
    _greenAmount: uint256,
    _recipient: address,
    _caller: address,
    _shouldAutoDeposit: bool,
    _shouldRefundSavingsGreen: bool,
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
        greenSpent: uint256 = self._redeemFromStabilityPool(_recipient, _caller, r.claimAsset, r.maxGreenAmount, totalGreenRemaining, _shouldAutoDeposit, a)
        totalGreenRemaining -= greenSpent
        totalGreenSpent += greenSpent

    assert totalGreenSpent != 0 # dev: no redemptions occurred

    # handle leftover green
    if totalGreenRemaining != 0:
        self._handleGreenForUser(_caller, totalGreenRemaining, _shouldRefundSavingsGreen, a.greenToken, a.savingsGreen)

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
    _recipient: address,
    _caller: address,
    _asset: address,
    _maxGreenForAsset: uint256,
    _totalGreenRemaining: uint256,
    _shouldAutoDeposit: bool,
    _a: addys.Addys,
) -> uint256:

    # NOTE: failing gracefully here, in case of many redemptions at same time

    # invalid inputs
    if empty(address) in [_recipient, _asset] or 0 in [_maxGreenForAsset, _totalGreenRemaining]:
        return 0

    # cannot redeem green token - don't be silly
    if _asset == _a.greenToken:
        return 0

    # check redemption config
    config: StabPoolRedemptionsConfig = staticcall MissionControl(_a.missionControl).getStabPoolRedemptionsConfig(_asset, _recipient)
    if not config.canRedeemInStabPoolGeneral or not config.canRedeemInStabPoolAsset or not config.isUserAllowed:
        return 0

    # make sure caller can deposit to recipient
    if _recipient != _caller and not config.canAnyoneDeposit:
        assert staticcall Teller(_a.teller).isUnderscoreWalletOwner(_recipient, _caller, _a.missionControl) # dev: not allowed to deposit for user

    # treating green as $1
    maxGreenAvailable: uint256 = min(_totalGreenRemaining, staticcall IERC20(_a.greenToken).balanceOf(self))
    maxRedeemValue: uint256 = min(_maxGreenForAsset, maxGreenAvailable)
    if maxRedeemValue == 0:
        return 0

    # max claimable amount
    maxClaimableAmount: uint256 = self._getAssetAmount(_asset, maxRedeemValue, _a.greenToken, _a.savingsGreen, _a.priceDesk, True)
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

        claimAmount: uint256 = min(remainingClaimAmount, claimableBalance)

        redeemNumerator: uint256 = claimAmount * maxRedeemValue
        redeemAmount: uint256 = redeemNumerator // maxClaimableAmount
        if redeemNumerator % maxClaimableAmount != 0:
            redeemAmount += 1
        redeemAmount = min(redeemAmount, remainingRedeemValue)

        if stabAsset == _a.savingsGreen:
            if staticcall IERC4626(_a.savingsGreen).previewDeposit(redeemAmount) == 0:
                continue

        # compute remaining USD value using price ratio: maxRedeemValue / maxClaimableAmount
        remainingUsdValue: uint256 = 0
        if claimAmount < claimableBalance:
            numerator: uint256 = (claimableBalance - claimAmount) * maxRedeemValue
            if numerator < maxClaimableAmount:
                remainingUsdValue = 1 # very small dust, trigger removal
            else:
                remainingUsdValue = numerator // maxClaimableAmount
        self._reduceClaimableBalances(stabAsset, _asset, claimAmount, claimableBalance, remainingUsdValue)

        # move tokens to recipient
        self._handleAssetForUser(_asset, claimAmount, _recipient, _shouldAutoDeposit, _a)
        remainingClaimAmount -= claimAmount

        # if stab asset is sGREEN, just convert directly, no need to make green claimable in this case
        if stabAsset == _a.savingsGreen:
            assert extcall IERC20(_a.greenToken).approve(_a.savingsGreen, redeemAmount, default_return_value=True) # dev: green approval failed
            extcall IERC4626(_a.savingsGreen).deposit(redeemAmount, self)
            assert extcall IERC20(_a.greenToken).approve(_a.savingsGreen, 0, default_return_value=True) # dev: green approval failed

        # add green to claimable (i.e. GREEN LP)
        else:
            self._addClaimableBalance(stabAsset, _a.greenToken, redeemAmount, _a.priceDesk)

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

    if _wantsSavingsGreen and amount > 10 ** 9: # small dust will fail
        assert extcall IERC20(_greenToken).approve(_savingsGreen, amount, default_return_value=True) # dev: green approval failed
        extcall IERC4626(_savingsGreen).deposit(amount, _recipient)
        assert extcall IERC20(_greenToken).approve(_savingsGreen, 0, default_return_value=True) # dev: green approval failed

    else:
        assert extcall IERC20(_greenToken).transfer(_recipient, amount, default_return_value=True) # dev: green transfer failed


##################
# Asset Handling #
##################


@internal
def _handleAssetForUser(
    _asset: address,
    _amount: uint256,
    _recipient: address,
    _shouldAutoDeposit: bool,
    _a: addys.Addys,
):
    vaultId: uint256 = staticcall MissionControl(_a.missionControl).getFirstVaultIdForAsset(_asset)

    # auto-deposit
    if _shouldAutoDeposit and self._canPerformAutoDeposit(vaultId, _asset, _recipient, _a.missionControl, _a.vaultBook):
        assert extcall IERC20(_asset).approve(_a.teller, _amount, default_return_value=True) # dev: token approval failed
        extcall Teller(_a.teller).depositFromTrusted(_recipient, vaultId, _asset, _amount, 0, _a)
        assert extcall IERC20(_asset).approve(_a.teller, 0, default_return_value=True) # dev: token approval failed
    else:
        self._transferAssetExact(_asset, _amount, _recipient)


@internal
def _transferAssetExact(_asset: address, _amount: uint256, _recipient: address):
    recipientBefore: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)
    assert extcall IERC20(_asset).transfer(_recipient, _amount, default_return_value=True) # dev: transfer failed
    assert staticcall IERC20(_asset).balanceOf(_recipient) - recipientBefore == _amount # dev: invalid recipient delivery


@view
@internal
def _canPerformAutoDeposit(
    _vaultId: uint256,
    _asset: address,
    _recipient: address,
    _missionControl: address,
    _vaultBook: address,
) -> bool:
    # invalid vault or stability pool (can't deposit right back into it)
    if _vaultId == 0:
        return False
    selfVaultId: uint256 = staticcall VaultBook(_vaultBook).getRegId(self)
    if _vaultId == selfVaultId:
        return False
    config: TellerDepositConfig = staticcall MissionControl(_missionControl).getTellerDepositConfig(_vaultId, _asset, _recipient)
    return config.canDepositGeneral and config.canDepositAsset


##################
# Claimable Data #
##################


# count and state


@view
@external
def getNumActiveClaimAssets(_stabAsset: address) -> uint256:
    return self._getNumActiveClaimAssets(_stabAsset)


@view
@internal
def _getNumActiveClaimAssets(_stabAsset: address) -> uint256:
    numAssets: uint256 = self.numClaimableAssets[_stabAsset]
    return numAssets - convert(numAssets != 0, uint256)


@view
@external
def getClaimAssetState(_stabAsset: address, _claimAsset: address) -> uint256:
    if self.indexOfClaimableAsset[_stabAsset][_claimAsset] != 0:
        return CLAIM_ASSET_ACTIVE
    return CLAIM_ASSET_ABSENT if self.claimableBalances[_stabAsset][_claimAsset] == 0 else CLAIM_ASSET_DORMANT


@view
@external
def canAcceptLiquidationAsset(_stabAsset: address, _claimAsset: address) -> bool:
    if vaultData.indexOfAsset[_stabAsset] == 0 or vaultData.indexOfAsset[_claimAsset] != 0:
        return False

    activeCount: uint256 = self._getNumActiveClaimAssets(_stabAsset)
    if self.indexOfClaimableAsset[_stabAsset][_claimAsset] == 0 and activeCount >= MAX_ACTIVE_CLAIM_ASSETS:
        return False
    if vaultData.isPaused:
        return False

    if vaultData.totalBalances[_stabAsset] == 0 and activeCount == 0:
        # A configured empty cohort may receive its first liquidation, but any
        # legacy cross-cohort reservation makes AuctionHouse's raw-custody
        # sizing unsafe because it cannot distinguish the reserved amount.
        return self.totalClaimableBalances[_stabAsset] == 0

    return self._getCohortLiquidationAmount(_stabAsset) != 0


@view
@external
def canActivateClaimAsset(_stabAsset: address, _claimAsset: address) -> (bool, uint256, uint256):
    # pause not modeled; execute still asserts isPaused
    if vaultData.totalBalances[_stabAsset] != 0:
        return False, 0, 0
    greenToken: address = empty(address)
    savingsGreen: address = empty(address)
    priceDesk: address = empty(address)
    greenToken, savingsGreen, priceDesk = self._getStabAddys()
    usdValue: uint256 = 0
    capacityRemaining: uint256 = 0
    usdValue, capacityRemaining = self._getClaimAssetActivationData(_stabAsset, _claimAsset, greenToken, savingsGreen, priceDesk)
    return (
        usdValue >= ACTIVATION_USD_THRESHOLD
        and capacityRemaining != 0
    ), usdValue, capacityRemaining


@view
@internal
def _getClaimAssetActivationData(
    _stabAsset: address,
    _claimAsset: address,
    _greenToken: address,
    _savingsGreen: address,
    _priceDesk: address,
) -> (uint256, uint256):
    activeCount: uint256 = self._getNumActiveClaimAssets(_stabAsset)
    capacityRemaining: uint256 = 0
    if activeCount < MAX_ACTIVE_CLAIM_ASSETS:
        capacityRemaining = MAX_ACTIVE_CLAIM_ASSETS - activeCount

    pairBalance: uint256 = self.claimableBalances[_stabAsset][_claimAsset]
    if pairBalance == 0 or self.indexOfClaimableAsset[_stabAsset][_claimAsset] != 0:
        return 0, capacityRemaining

    custody: uint256 = staticcall IERC20(_claimAsset).balanceOf(self)
    priorLiability: uint256 = self.totalClaimableBalances[_claimAsset]
    assert custody >= priorLiability # dev: claim custody deficit
    return self._getUsdValue(_claimAsset, pairBalance, _greenToken, _savingsGreen, _priceDesk, False), capacityRemaining


# maintenance


@internal
def _maintainClaimableAssets(_stabAsset: address, _claimAssets: DynArray[address, MAX_CLAIM_ASSET_MAINTENANCE], _shouldActivate: bool):
    greenToken: address = empty(address)
    savingsGreen: address = empty(address)
    priceDesk: address = empty(address)
    greenToken, savingsGreen, priceDesk = self._getStabAddys()

    for claimAsset: address in _claimAssets:
        if _shouldActivate:
            # live book: fail-soft quote must not seat a pair onto NAV
            if vaultData.totalBalances[_stabAsset] != 0:
                continue

            pairBalance: uint256 = self.claimableBalances[_stabAsset][claimAsset]
            if pairBalance == 0 or self.indexOfClaimableAsset[_stabAsset][claimAsset] != 0:
                continue

            custody: uint256 = staticcall IERC20(claimAsset).balanceOf(self)
            priorLiability: uint256 = self.totalClaimableBalances[claimAsset]
            assert custody >= priorLiability # dev: claim custody deficit

            usdValue: uint256 = self._getUsdValue(claimAsset, pairBalance, greenToken, savingsGreen, priceDesk, False)
            if usdValue < ACTIVATION_USD_THRESHOLD:
                continue

            if self._getNumActiveClaimAssets(_stabAsset) >= MAX_ACTIVE_CLAIM_ASSETS:
                continue

            self._registerClaimableAsset(_stabAsset, claimAsset)
            continue

        if self.indexOfClaimableAsset[_stabAsset][claimAsset] == 0:
            continue

        balance: uint256 = self.claimableBalances[_stabAsset][claimAsset]
        if balance == 0:
            self._removeClaimableAsset(_stabAsset, claimAsset, DEACTIVATION_ZERO)
            continue

        # live book: fail-soft dust quote must not hide a nonzero pile
        if vaultData.totalBalances[_stabAsset] != 0:
            continue

        custody: uint256 = staticcall IERC20(claimAsset).balanceOf(self)
        if custody < self.totalClaimableBalances[claimAsset]:
            continue

        usdValue: uint256 = self._getUsdValue(claimAsset, balance, greenToken, savingsGreen, priceDesk, False)
        if usdValue != 0 and usdValue < RETENTION_USD_THRESHOLD:
            self._removeClaimableAsset(_stabAsset, claimAsset, DEACTIVATION_DUST)


@external
def pruneClaimableAssets(_stabAsset: address, _claimAssets: DynArray[address, MAX_CLAIM_ASSET_MAINTENANCE]):
    self._maintainClaimableAssets(_stabAsset, _claimAssets, False)


@external
def activateClaimAssets(_stabAsset: address, _claimAssets: DynArray[address, MAX_CLAIM_ASSET_MAINTENANCE]):
    assert vaultData.isPaused # dev: contract not paused
    self._maintainClaimableAssets(_stabAsset, _claimAssets, True)


# add claimable


@internal
def _addClaimableBalance(
    _stabAsset: address,
    _claimAsset: address,
    _reportedAmount: uint256,
    _priceDesk: address,
):
    assert _stabAsset != empty(address) # dev: invalid stab asset
    assert _claimAsset != empty(address) # dev: invalid claim asset
    assert _reportedAmount != 0 # dev: nothing received
    assert vaultData.indexOfAsset[_claimAsset] == 0 # dev: claim asset is stability asset

    # validate custody
    custody: uint256 = staticcall IERC20(_claimAsset).balanceOf(self)
    priorLiability: uint256 = self.totalClaimableBalances[_claimAsset]
    assert custody >= priorLiability # dev: claim custody deficit
    assert _reportedAmount <= custody - priorLiability # dev: short claim receipt

    newPairBalance: uint256 = self.claimableBalances[_stabAsset][_claimAsset] + _reportedAmount
    isActive: bool = self.indexOfClaimableAsset[_stabAsset][_claimAsset] != 0
    usdValue: uint256 = 0
    activeCount: uint256 = 0
    if not isActive:
        activeCount = self._getNumActiveClaimAssets(_stabAsset)
        assert activeCount < MAX_ACTIVE_CLAIM_ASSETS # dev: max active claim assets
        usdValue = self._getUsdValue(_claimAsset, newPairBalance, GREEN_TOKEN, SAVINGS_GREEN, _priceDesk, False)
        assert usdValue != 0 # dev: no price for claim asset

    # update balances
    self.claimableBalances[_stabAsset][_claimAsset] = newPairBalance
    self.totalClaimableBalances[_claimAsset] = priorLiability + _reportedAmount

    # already active
    if isActive:
        return

    if usdValue < ACTIVATION_USD_THRESHOLD:
        log ClaimAssetLeftDormant(stabAsset=_stabAsset, claimAsset=_claimAsset, balance=newPairBalance, activeCount=activeCount, reason=DORMANT_BELOW_FLOOR)
        return

    self._registerClaimableAsset(_stabAsset, _claimAsset)


# register claimable asset


@internal
def _registerClaimableAsset(_stabAsset: address, _assetReceived: address):
    assert self.claimableBalances[_stabAsset][_assetReceived] != 0 # dev: no claimable balance
    assert self.indexOfClaimableAsset[_stabAsset][_assetReceived] == 0 # dev: claim asset already active

    cid: uint256 = self.numClaimableAssets[_stabAsset]
    if cid == 0:
        cid = 1 # not using 0 index
    assert cid <= MAX_ACTIVE_CLAIM_ASSETS # dev: max active claim assets
    self.claimableAssets[_stabAsset][cid] = _assetReceived
    self.indexOfClaimableAsset[_stabAsset][_assetReceived] = cid
    self.numClaimableAssets[_stabAsset] = cid + 1
    log ClaimAssetActivated(stabAsset=_stabAsset, claimAsset=_assetReceived, balance=self.claimableBalances[_stabAsset][_assetReceived], activeCount=cid)


# reduce claimable


@internal
def _reduceClaimableBalances(
    _stabAsset: address,
    _claimAsset: address,
    _claimAmount: uint256,
    _prevClaimableBalance: uint256,
    _remainingUsdValue: uint256,
):
    newClaimableBalance: uint256 = _prevClaimableBalance - _claimAmount
    self.claimableBalances[_stabAsset][_claimAsset] = newClaimableBalance
    self.totalClaimableBalances[_claimAsset] -= _claimAmount

    if newClaimableBalance == 0:
        self._removeClaimableAsset(_stabAsset, _claimAsset, DEACTIVATION_ZERO)
        return

    # Dust-delist only when remaining USD is a priced value below RETENTION
    # $0.05. Zero/unavailable USD is never dust. An empty cohort may
    # dust-deactivate any such residual; a live cohort may only when the
    # leftover is microscopic: R <= P // LIVE_RESIDUAL_DIVISOR.
    if (
        _remainingUsdValue != 0
        and _remainingUsdValue < RETENTION_USD_THRESHOLD
    ):
        if (
            vaultData.totalBalances[_stabAsset] == 0
            or newClaimableBalance
               <= _prevClaimableBalance // LIVE_RESIDUAL_DIVISOR
        ):
            self._removeClaimableAsset(
                _stabAsset,
                _claimAsset,
                DEACTIVATION_DUST,
            )


# deregister claimable asset


@internal
def _removeClaimableAsset(_stabAsset: address, _asset: address, _reason: uint256):
    numAssets: uint256 = self.numClaimableAssets[_stabAsset]
    targetIndex: uint256 = self.indexOfClaimableAsset[_stabAsset][_asset]
    if targetIndex == 0:
        return

    # update data
    lastIndex: uint256 = numAssets - 1
    # shift to replace the one being removed
    if targetIndex != lastIndex:
        lastAsset: address = self.claimableAssets[_stabAsset][lastIndex]
        self.claimableAssets[_stabAsset][targetIndex] = lastAsset
        self.indexOfClaimableAsset[_stabAsset][lastAsset] = targetIndex

    self.claimableAssets[_stabAsset][lastIndex] = empty(address)
    self.indexOfClaimableAsset[_stabAsset][_asset] = 0
    self.numClaimableAssets[_stabAsset] = lastIndex
    log ClaimAssetDeactivated(stabAsset=_stabAsset, claimAsset=_asset, balance=self.claimableBalances[_stabAsset][_asset], activeCount=lastIndex - 1, reason=_reason)
