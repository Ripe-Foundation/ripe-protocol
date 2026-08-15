# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

implements: Vault

exports: addys.__interface__
exports: vaultData.__interface__
exports: sharesVault.__interface__

initializes: addys
initializes: vaultData[addys := addys]
initializes: sharesVault[vaultData := vaultData]

from interfaces import Vault
import contracts.modules.Addys as addys
import contracts.vaults.modules.VaultData as vaultData
import contracts.vaults.modules.SharesVault as sharesVault
from ethereum.ercs import IERC20

struct CompatibilityPlan:
    transferAmount: uint256
    vaultOutflow: uint256
    recipientDelivery: uint256
    isCompatible: bool

AAVE_RAY: constant(uint256) = 10 ** 27
COMET_INDEX_SCALE: constant(uint256) = 10 ** 15
MAX_ADDRESS: constant(uint256) = 2 ** 160 - 1
AAVE_BASE_POOL: constant(address) = 0xA238Dd80C259a72e81d7e4664a9801593F98d1c5
AAVE_CBBTC: constant(address) = 0xBdb9300b7CDE636d9cD4AFF00f6F009fFBBc8EE6
AAVE_USDC: constant(address) = 0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB
AAVE_WETH: constant(address) = 0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7
COMET_AERO: constant(address) = 0x784efeB622244d2348d4F2522f8860B96fbEcE89
COMET_USDC: constant(address) = 0xb125E6687d4313864e53df431d5425969c15Eb2F
COMET_WETH: constant(address) = 0x46e6b214b524310239732D51387075E0e70970bf
CBBTC: constant(address) = 0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf
USDC: constant(address) = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
WETH: constant(address) = 0x4200000000000000000000000000000000000006
AERO: constant(address) = 0x940181a94A35A4569E4529A3CDfB74e38FD98631
AAVE_PROXY_CBBTC_CODEHASH: constant(bytes32) = 0x4f2154b879ed2f2db9154d9664b5abfaae3128751c1645c4c17f646316bb8b62
AAVE_PROXY_CODEHASH: constant(bytes32) = 0x59d2fd2a4bad76f979bc2c1da50504e072f4b3bb64f5429302a384ad9c0706f2
COMET_PROXY_CODEHASH: constant(bytes32) = 0x64952234eab8f3aed74355c49119f627965640b1efeb6b28430b5a31b0d3b192

event RebaseErc20VaultDeposit:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    shares: uint256

event RebaseErc20VaultWithdrawal:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    isDepleted: bool
    shares: uint256

event RebaseErc20VaultTransfer:
    fromUser: indexed(address)
    toUser: indexed(address)
    asset: indexed(address)
    transferAmount: uint256
    isFromUserDepleted: bool
    transferShares: uint256


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    vaultData.__init__(False)
    sharesVault.__init__()


########
# Core #
########


@nonreentrant
@external
def depositTokensInVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed

    depositAmount: uint256 = 0
    newShares: uint256 = 0
    depositAmount, newShares = sharesVault._depositTokensInVault(_user, _asset, _amount)
    log RebaseErc20VaultDeposit(user=_user, asset=_asset, amount=depositAmount, shares=newShares)
    return depositAmount


@nonreentrant
@external
def withdrawTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
    _a: addys.Addys = empty(addys.Addys),
) -> (uint256, bool):
    assert msg.sender in [addys._getTellerAddr(), addys._getAuctionHouseAddr(), addys._getCreditEngineAddr()] # dev: not allowed

    withdrawalAmount: uint256 = 0
    withdrawalShares: uint256 = 0
    isDepleted: bool = False
    withdrawalAmount, withdrawalShares, isDepleted = self._withdrawCompatibleTokensFromVault(_user, _asset, _amount, _recipient)
    log RebaseErc20VaultWithdrawal(user=_user, asset=_asset, amount=withdrawalAmount, isDepleted=isDepleted, shares=withdrawalShares)
    return withdrawalAmount, isDepleted


@internal
def _withdrawCompatibleTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
) -> (uint256, uint256, bool):
    assert not vaultData.isPaused # dev: contract paused
    assert empty(address) not in [_user, _asset, _recipient] # dev: invalid user, asset, or recipient

    # Governance admission into this RebaseErc20 vault is the first eligibility
    # gate. Unknown admitted tokens retain the shared strict path.
    assert vaultData.indexOfAsset[_asset] != 0 # dev: unsupported asset
    assert vaultData.indexOfUserAsset[_user][_asset] != 0 # dev: user has no asset

    withdrawalShares: uint256 = 0
    theoreticalAmount: uint256 = 0
    withdrawalShares, theoreticalAmount = sharesVault._calcWithdrawalSharesAndAmount(_user, _asset, _amount)
    isFullWithdrawal: bool = withdrawalShares == vaultData.userBalances[_user][_asset]

    # Comet accrues inside transfer(). Bring its stored index current before
    # prediction, while no Ripe shares have been changed.
    if self._hasSupportedCometIdentity(_asset):
        if not self._tryAccrueComet(_asset):
            return sharesVault._withdrawTokensFromVault(_user, _asset, _amount, _recipient)
        withdrawalShares, theoreticalAmount = sharesVault._calcWithdrawalSharesAndAmount(_user, _asset, _amount)
        isFullWithdrawal = withdrawalShares == vaultData.userBalances[_user][_asset]

    vaultBefore: uint256 = staticcall IERC20(_asset).balanceOf(self)
    recipientBefore: uint256 = staticcall IERC20(_asset).balanceOf(_recipient)
    plan: CompatibilityPlan = self._getCompatibilityPlan(
        _asset,
        _recipient,
        theoreticalAmount,
        isFullWithdrawal,
        2,
        vaultBefore,
        recipientBefore,
    )
    if not plan.isCompatible:
        return sharesVault._withdrawTokensFromVault(_user, _asset, _amount, _recipient)

    if not isFullWithdrawal:
        withdrawalShares = min(
            vaultData.userBalances[_user][_asset],
            sharesVault._amountToShares(
                plan.vaultOutflow,
                vaultData.totalBalances[_asset],
                vaultBefore,
                True,
            ),
        )
        assert withdrawalShares != 0 # dev: cannot withdraw 0 shares
        # If charging the actual outflow rounds to every user share, upgrade
        # the operation to full-exit semantics rather than burn the position
        # for less than its maximum attainable claim.
        if withdrawalShares == vaultData.userBalances[_user][_asset]:
            isFullWithdrawal = True
            withdrawalShares, theoreticalAmount = sharesVault._calcWithdrawalSharesAndAmount(
                _user,
                _asset,
                max_value(uint256),
            )
            plan = self._getCompatibilityPlan(
                _asset,
                _recipient,
                theoreticalAmount,
                True,
                2,
                vaultBefore,
                recipientBefore,
            )
            if not plan.isCompatible:
                return sharesVault._withdrawTokensFromVault(_user, _asset, _amount, _recipient)

    if not self._preservesRemainingClaim(
        withdrawalShares,
        vaultData.totalBalances[_asset],
        vaultBefore,
        plan.vaultOutflow,
    ):
        # A full exit first selects maximum recipient delivery. If that choice
        # would consume value belonging to other shares, retry lower candidates
        # before failing closed.
        assert isFullWithdrawal # dev: remaining holder loss
        plan = self._getCompatibilityPlan(
            _asset,
            _recipient,
            theoreticalAmount,
            True,
            1,
            vaultBefore,
            recipientBefore,
        )
        if not plan.isCompatible:
            return sharesVault._withdrawTokensFromVault(_user, _asset, _amount, _recipient)
        if not self._preservesRemainingClaim(
            withdrawalShares,
            vaultData.totalBalances[_asset],
            vaultBefore,
            plan.vaultOutflow,
        ):
            plan = self._getCompatibilityPlan(
                _asset,
                _recipient,
                theoreticalAmount,
                True,
                0,
                vaultBefore,
                recipientBefore,
            )
            if not plan.isCompatible:
                return sharesVault._withdrawTokensFromVault(_user, _asset, _amount, _recipient)
        assert self._preservesRemainingClaim(
            withdrawalShares,
            vaultData.totalBalances[_asset],
            vaultBefore,
            plan.vaultOutflow,
        ) # dev: remaining holder loss

    isDepleted: bool = False
    withdrawalShares, isDepleted = vaultData._reduceBalanceOnWithdrawal(
        _user,
        _asset,
        withdrawalShares,
        True,
    )

    assert extcall IERC20(_asset).transfer(_recipient, plan.transferAmount, default_return_value=True) # dev: token transfer failed

    assert vaultBefore - staticcall IERC20(_asset).balanceOf(self) == plan.vaultOutflow # dev: invalid compatible vault outflow
    assert staticcall IERC20(_asset).balanceOf(_recipient) - recipientBefore == plan.recipientDelivery # dev: invalid compatible recipient delivery

    return plan.vaultOutflow, withdrawalShares, isDepleted


@view
@internal
def _preservesRemainingClaim(
    _withdrawalShares: uint256,
    _totalShares: uint256,
    _vaultBalance: uint256,
    _vaultOutflow: uint256,
) -> bool:
    assert _withdrawalShares <= _totalShares # dev: invalid withdrawal shares
    assert _vaultOutflow <= _vaultBalance # dev: invalid vault outflow
    remainingShares: uint256 = _totalShares - _withdrawalShares
    if remainingShares == 0:
        return True
    remainingClaimBefore: uint256 = sharesVault._sharesToAmount(
        remainingShares,
        _totalShares,
        _vaultBalance,
        False,
    )
    remainingClaimAfter: uint256 = sharesVault._sharesToAmount(
        remainingShares,
        remainingShares,
        _vaultBalance - _vaultOutflow,
        False,
    )
    return remainingClaimAfter >= remainingClaimBefore


@view
@internal
def _getCompatibilityPlan(
    _asset: address,
    _recipient: address,
    _theoreticalAmount: uint256,
    _isFullWithdrawal: bool,
    _fullDeliveryMode: uint8,
    _vaultBalance: uint256,
    _recipientBalance: uint256,
) -> CompatibilityPlan:
    if self._hasSupportedAaveIdentity(_asset):
        return self._getAavePlan(
            _asset,
            _recipient,
            _theoreticalAmount,
            _isFullWithdrawal,
            _fullDeliveryMode,
            _vaultBalance,
            _recipientBalance,
        )
    if self._hasSupportedCometIdentity(_asset):
        return self._getCometPlan(
            _asset,
            _recipient,
            _theoreticalAmount,
            _isFullWithdrawal,
            _fullDeliveryMode,
            _vaultBalance,
            _recipientBalance,
        )
    return empty(CompatibilityPlan)


@view
@internal
def _hasSupportedAaveIdentity(_asset: address) -> bool:
    if _asset == AAVE_CBBTC:
        return _asset.codehash == AAVE_PROXY_CBBTC_CODEHASH
    if _asset in [AAVE_USDC, AAVE_WETH]:
        return _asset.codehash == AAVE_PROXY_CODEHASH
    return False


@view
@internal
def _hasSupportedCometIdentity(_asset: address) -> bool:
    expectedUnderlying: address = self._expectedCometUnderlying(_asset)
    if expectedUnderlying == empty(address) or _asset.codehash != COMET_PROXY_CODEHASH:
        return False
    didRead: bool = False
    underlying: address = empty(address)
    didRead, underlying = self._safeReadAddress(_asset, method_id("baseToken()"))
    return didRead and underlying == expectedUnderlying


@pure
@internal
def _expectedAaveUnderlying(_asset: address) -> address:
    if _asset == AAVE_CBBTC:
        return CBBTC
    if _asset == AAVE_USDC:
        return USDC
    if _asset == AAVE_WETH:
        return WETH
    return empty(address)


@pure
@internal
def _expectedCometUnderlying(_asset: address) -> address:
    if _asset == COMET_AERO:
        return AERO
    if _asset == COMET_USDC:
        return USDC
    if _asset == COMET_WETH:
        return WETH
    return empty(address)


@internal
def _tryAccrueComet(_asset: address) -> bool:
    success: bool = False
    response: Bytes[1] = b""
    success, response = raw_call(
        _asset,
        abi_encode(self, method_id=method_id("accrueAccount(address)")),
        max_outsize=1,
        revert_on_failure=False,
    )
    return success and len(response) == 0


@view
@internal
def _safeReadUint(_target: address, _calldata: Bytes[36]) -> (bool, uint256):
    success: bool = False
    response: Bytes[33] = b""
    success, response = raw_call(
        _target,
        _calldata,
        max_outsize=33,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 32:
        return False, 0
    return True, abi_decode(response, uint256)


@view
@internal
def _safeReadAddress(_target: address, _calldata: Bytes[36]) -> (bool, address):
    didRead: bool = False
    value: uint256 = 0
    didRead, value = self._safeReadUint(_target, _calldata)
    if not didRead or value > MAX_ADDRESS:
        return False, empty(address)
    return True, convert(value, address)


@view
@internal
def _getAavePlan(
    _asset: address,
    _recipient: address,
    _theoreticalAmount: uint256,
    _isFullWithdrawal: bool,
    _fullDeliveryMode: uint8,
    _vaultBalance: uint256,
    _recipientBalance: uint256,
) -> CompatibilityPlan:
    didRead: bool = False
    pool: address = empty(address)
    underlying: address = empty(address)
    didRead, pool = self._safeReadAddress(_asset, method_id("POOL()"))
    if not didRead or pool != AAVE_BASE_POOL:
        return empty(CompatibilityPlan)
    didRead, underlying = self._safeReadAddress(_asset, method_id("UNDERLYING_ASSET_ADDRESS()"))
    if not didRead or underlying != self._expectedAaveUnderlying(_asset):
        return empty(CompatibilityPlan)

    index: uint256 = 0
    vaultScaled: uint256 = 0
    recipientScaled: uint256 = 0
    didRead, index = self._safeReadUint(
        pool,
        abi_encode(underlying, method_id=method_id("getReserveNormalizedIncome(address)")),
    )
    if not didRead or index == 0:
        return empty(CompatibilityPlan)
    didRead, vaultScaled = self._safeReadUint(
        _asset,
        abi_encode(self, method_id=method_id("scaledBalanceOf(address)")),
    )
    if not didRead:
        return empty(CompatibilityPlan)
    didRead, recipientScaled = self._safeReadUint(
        _asset,
        abi_encode(_recipient, method_id=method_id("scaledBalanceOf(address)")),
    )
    if (
        not didRead
        or self._aavePresent(vaultScaled, index) != _vaultBalance
        or self._aavePresent(recipientScaled, index) != _recipientBalance
        or _theoreticalAmount == max_value(uint256)
    ):
        return empty(CompatibilityPlan)
    baseScaled: uint256 = self._aaveScaled(_theoreticalAmount, index)
    if baseScaled == 0 or baseScaled > vaultScaled:
        return empty(CompatibilityPlan)

    plan: CompatibilityPlan = self._predictAave(
        _theoreticalAmount,
        index,
        vaultScaled,
        recipientScaled,
        _vaultBalance,
        _recipientBalance,
    )
    if _isFullWithdrawal and _fullDeliveryMode == 0:
        if _theoreticalAmount <= 1:
            return empty(CompatibilityPlan)
        plan = self._predictAave(
            _theoreticalAmount - 1,
            index,
            vaultScaled,
            recipientScaled,
            _vaultBalance,
            _recipientBalance,
        )
    elif _isFullWithdrawal and _fullDeliveryMode == 2:
        candidateAmount: uint256 = min(_vaultBalance, _theoreticalAmount + 1)
        candidateScaled: uint256 = self._aaveScaled(candidateAmount, index)
        if candidateAmount > _theoreticalAmount and candidateScaled <= vaultScaled:
            candidate: CompatibilityPlan = self._predictAave(
                candidateAmount,
                index,
                vaultScaled,
                recipientScaled,
                _vaultBalance,
                _recipientBalance,
            )
            if (
                candidate.vaultOutflow + 1 >= _theoreticalAmount
                and candidate.vaultOutflow <= _theoreticalAmount + 1
                and candidate.recipientDelivery + 1 >= _theoreticalAmount
                and candidate.recipientDelivery <= _theoreticalAmount + 1
                and candidate.recipientDelivery > plan.recipientDelivery
            ):
                plan = candidate
    elif not _isFullWithdrawal and plan.recipientDelivery < _theoreticalAmount:
        candidateScaled: uint256 = self._aaveScaled(_theoreticalAmount + 1, index)
        if candidateScaled > vaultScaled:
            return empty(CompatibilityPlan)
        plan = self._predictAave(
            _theoreticalAmount + 1,
            index,
            vaultScaled,
            recipientScaled,
            _vaultBalance,
            _recipientBalance,
        )
    if (
        plan.vaultOutflow > _theoreticalAmount + 1
        or plan.recipientDelivery > _theoreticalAmount + 1
    ):
        return empty(CompatibilityPlan)
    if _isFullWithdrawal:
        if (
            plan.vaultOutflow + 1 < _theoreticalAmount
            or plan.recipientDelivery + 1 < _theoreticalAmount
        ):
            return empty(CompatibilityPlan)
    elif (
        plan.vaultOutflow < _theoreticalAmount
        or plan.recipientDelivery < _theoreticalAmount
    ):
        return empty(CompatibilityPlan)
    plan.isCompatible = True
    return plan


@view
@internal
def _predictAave(
    _transferAmount: uint256,
    _index: uint256,
    _vaultScaled: uint256,
    _recipientScaled: uint256,
    _vaultBalance: uint256,
    _recipientBalance: uint256,
    ) -> CompatibilityPlan:
    scaledAmount: uint256 = self._aaveScaled(_transferAmount, _index)
    assert scaledAmount != 0 and scaledAmount <= _vaultScaled # dev: invalid Aave scaled amount
    vaultAfter: uint256 = self._aavePresent(_vaultScaled - scaledAmount, _index)
    recipientAfter: uint256 = self._aavePresent(_recipientScaled + scaledAmount, _index)
    return CompatibilityPlan(
        transferAmount=_transferAmount,
        vaultOutflow=_vaultBalance - vaultAfter,
        recipientDelivery=recipientAfter - _recipientBalance,
        isCompatible=False,
    )


@pure
@internal
def _aaveScaled(_amount: uint256, _index: uint256) -> uint256:
    # Aave v3.5+ rounds transfers up in scaled units.
    return (_amount * AAVE_RAY + _index - 1) // _index


@pure
@internal
def _aavePresent(_scaled: uint256, _index: uint256) -> uint256:
    # Aave v3.5+ rounds observable aToken balances down.
    return (_scaled * _index) // AAVE_RAY


@view
@internal
def _getCometPlan(
    _asset: address,
    _recipient: address,
    _theoreticalAmount: uint256,
    _isFullWithdrawal: bool,
    _fullDeliveryMode: uint8,
    _vaultBalance: uint256,
    _recipientBalance: uint256,
) -> CompatibilityPlan:
    success: bool = False
    response: Bytes[257] = b""
    success, response = raw_call(
        _asset,
        method_id("totalsBasic()"),
        max_outsize=257,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 256:
        return empty(CompatibilityPlan)

    index: uint64 = 0
    borrowIndex: uint64 = 0
    trackingSupplyIndex: uint64 = 0
    trackingBorrowIndex: uint64 = 0
    totalSupplyBase: uint104 = 0
    totalBorrowBase: uint104 = 0
    lastAccrualTime: uint40 = 0
    pauseFlags: uint8 = 0
    index, borrowIndex, trackingSupplyIndex, trackingBorrowIndex, totalSupplyBase, totalBorrowBase, lastAccrualTime, pauseFlags = abi_decode(response, (uint64, uint64, uint64, uint64, uint104, uint104, uint40, uint8))
    if index == 0:
        return empty(CompatibilityPlan)

    vaultPrincipal: int104 = 0
    recipientPrincipal: int104 = 0
    vaultTrackingIndex: uint64 = 0
    vaultTrackingAccrued: uint64 = 0
    vaultAssetsIn: uint16 = 0
    vaultReserved: uint8 = 0
    recipientTrackingIndex: uint64 = 0
    recipientTrackingAccrued: uint64 = 0
    recipientAssetsIn: uint16 = 0
    recipientReserved: uint8 = 0
    success, response = raw_call(
        _asset,
        abi_encode(self, method_id=method_id("userBasic(address)")),
        max_outsize=257,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 160:
        return empty(CompatibilityPlan)
    vaultPrincipal, vaultTrackingIndex, vaultTrackingAccrued, vaultAssetsIn, vaultReserved = abi_decode(response, (int104, uint64, uint64, uint16, uint8))

    success, response = raw_call(
        _asset,
        abi_encode(_recipient, method_id=method_id("userBasic(address)")),
        max_outsize=257,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 160:
        return empty(CompatibilityPlan)
    recipientPrincipal, recipientTrackingIndex, recipientTrackingAccrued, recipientAssetsIn, recipientReserved = abi_decode(response, (int104, uint64, uint64, uint16, uint8))
    if vaultPrincipal < 0 or recipientPrincipal < 0:
        return empty(CompatibilityPlan)
    if (
        self._cometPresent(convert(vaultPrincipal, uint256), index) != _vaultBalance
        or self._cometPresent(convert(recipientPrincipal, uint256), index) != _recipientBalance
        or _theoreticalAmount > max_value(uint256) - 2
    ):
        return empty(CompatibilityPlan)

    plan: CompatibilityPlan = self._predictComet(
        _theoreticalAmount,
        index,
        convert(vaultPrincipal, uint256),
        convert(recipientPrincipal, uint256),
        _vaultBalance,
        _recipientBalance,
    )
    if _isFullWithdrawal and _fullDeliveryMode == 0:
        if _theoreticalAmount <= 1:
            return empty(CompatibilityPlan)
        plan = self._predictComet(
            _theoreticalAmount - 1,
            index,
            convert(vaultPrincipal, uint256),
            convert(recipientPrincipal, uint256),
            _vaultBalance,
            _recipientBalance,
        )
    elif _isFullWithdrawal and _fullDeliveryMode == 2:
        maxPlan: CompatibilityPlan = self._predictComet(
            min(_vaultBalance, _theoreticalAmount + 1),
            index,
            convert(vaultPrincipal, uint256),
            convert(recipientPrincipal, uint256),
            _vaultBalance,
            _recipientBalance,
        )
        if (
            maxPlan.vaultOutflow + 1 >= _theoreticalAmount
            and maxPlan.vaultOutflow <= _theoreticalAmount + 2
            and maxPlan.recipientDelivery + 2 >= _theoreticalAmount
            and maxPlan.recipientDelivery <= _theoreticalAmount + 1
            and maxPlan.recipientDelivery > plan.recipientDelivery
        ):
            plan = maxPlan
    elif not _isFullWithdrawal and plan.recipientDelivery < _theoreticalAmount:
        if _theoreticalAmount + 1 > _vaultBalance:
            return empty(CompatibilityPlan)
        plan = self._predictComet(
            _theoreticalAmount + 1,
            index,
            convert(vaultPrincipal, uint256),
            convert(recipientPrincipal, uint256),
            _vaultBalance,
            _recipientBalance,
        )

    # Comet floors source and recipient principal independently. Partials may
    # therefore remove two more custody units than requested while still
    # delivering the full request; a full exit may leave those two units with
    # the exiting user's representation, never with remaining holders.
    if (
        plan.vaultOutflow > _theoreticalAmount + 2
        or plan.recipientDelivery > _theoreticalAmount + 1
    ):
        return empty(CompatibilityPlan)
    if _isFullWithdrawal:
        if (
            plan.vaultOutflow + 1 < _theoreticalAmount
            or plan.recipientDelivery + 2 < _theoreticalAmount
        ):
            return empty(CompatibilityPlan)
    elif (
        plan.vaultOutflow < _theoreticalAmount
        or plan.recipientDelivery < _theoreticalAmount
    ):
        return empty(CompatibilityPlan)
    plan.isCompatible = True
    return plan


@pure
@internal
def _predictComet(
    _transferAmount: uint256,
    _index: uint64,
    _vaultPrincipal: uint256,
    _recipientPrincipal: uint256,
    _vaultBalance: uint256,
    _recipientBalance: uint256,
) -> CompatibilityPlan:
    assert _transferAmount <= _vaultBalance # dev: invalid Comet transfer amount
    vaultPrincipalAfter: uint256 = ((_vaultBalance - _transferAmount) * COMET_INDEX_SCALE) // convert(_index, uint256)
    recipientPrincipalAfter: uint256 = ((_recipientBalance + _transferAmount) * COMET_INDEX_SCALE) // convert(_index, uint256)
    vaultAfter: uint256 = self._cometPresent(vaultPrincipalAfter, _index)
    recipientAfter: uint256 = self._cometPresent(recipientPrincipalAfter, _index)
    return CompatibilityPlan(
        transferAmount=_transferAmount,
        vaultOutflow=_vaultBalance - vaultAfter,
        recipientDelivery=recipientAfter - _recipientBalance,
        isCompatible=False,
    )


@pure
@internal
def _cometPresent(_principal: uint256, _index: uint64) -> uint256:
    return _principal * convert(_index, uint256) // COMET_INDEX_SCALE


@nonreentrant
@external
def transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> (uint256, bool):
    assert msg.sender in [addys._getAuctionHouseAddr(), addys._getCreditEngineAddr()] # dev: not allowed

    transferAmount: uint256 = 0
    transferShares: uint256 = 0
    isFromUserDepleted: bool = False
    transferAmount, transferShares, isFromUserDepleted = sharesVault._transferBalanceWithinVault(_asset, _fromUser, _toUser, _transferAmount)
    log RebaseErc20VaultTransfer(fromUser=_fromUser, toUser=_toUser, asset=_asset, transferAmount=transferAmount, isFromUserDepleted=isFromUserDepleted, transferShares=transferShares)
    return transferAmount, isFromUserDepleted


####################
# Needs For Others #
####################


@view
@external
def getVaultDataOnDeposit(_user: address, _asset: address) -> Vault.VaultDataOnDeposit:
    # used in Teller.vy
    return sharesVault._getVaultDataOnDeposit(_user, _asset)


@view
@external
def getUserLootBoxShare(_user: address, _asset: address) -> uint256:
    # used in Lootbox.vy
    return sharesVault._getUserLootBoxShare(_user, _asset)


@view
@external
def getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
    # used in CreditEngine.vy
    return sharesVault._getUserAssetAndAmountAtIndex(_user, _index)


@view
@external
def getUserAssetAtIndexAndHasBalance(_user: address, _index: uint256) -> (address, bool):
    # used in Lootbox.vy and AuctionHouse.vy
    return sharesVault._getUserAssetAtIndexAndHasBalance(_user, _index)


###############
# Other Utils #
###############


@view
@external
def getTotalAmountForUser(_user: address, _asset: address) -> uint256:
    return sharesVault._getTotalAmountForUser(_user, _asset)


@view
@external
def getTotalAmountForVault(_asset: address) -> uint256:
    return sharesVault._getTotalAmountForVault(_asset)
