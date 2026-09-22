#        _          _       _             _                  _           _                _               _            _            _        
#       /\ \    _ / /\     / /\          /\_\               _\ \        /\ \             / /\            /\ \         /\ \         /\_\      
#       \ \ \  /_/ / /    / /  \        / / /         _    /\__ \       \_\ \           / /  \          /  \ \       /  \ \       / / /  _   
#        \ \ \ \___\/    / / /\ \       \ \ \__      /\_\ / /_ \_\      /\__ \         / / /\ \        / /\ \ \     / /\ \ \     / / /  /\_\ 
#        / / /  \ \ \   / / /\ \ \       \ \___\    / / // / /\/_/     / /_ \ \       / / /\ \ \      / / /\ \ \   / / /\ \ \   / / /__/ / / 
#        \ \ \   \_\ \ / / /  \ \ \       \__  /   / / // / /         / / /\ \ \     / / /\ \_\ \    / / /  \ \_\ / / /  \ \_\ / /\_____/ /  
#         \ \ \  / / // / /___/ /\ \      / / /   / / // / /         / / /  \/_/    / / /\ \ \___\  / / /   / / // / /   / / // /\_______/   
#          \ \ \/ / // / /_____/ /\ \    / / /   / / // / / ____    / / /          / / /  \ \ \__/ / / /   / / // / /   / / // / /\ \ \      
#           \ \ \/ // /_________/\ \ \  / / /___/ / // /_/_/ ___/\ / / /          / / /____\_\ \  / / /___/ / // / /___/ / // / /  \ \ \     
#            \ \  // / /_       __\ \_\/ / /____\/ //_______/\__\//_/ /          / / /__________\/ / /____\/ // / /____\/ // / /    \ \ \    
#             \_\/ \_\___\     /____/_/\/_________/ \_______\/    \_\/           \/_____________/\/_________/ \/_________/ \/_/      \_\_\   

#     ╔═══════════════════════════════════╗
#     ║  ** Vault Book **                 ║
#     ║  Registry for all deposit vaults  ║
#     ╚═══════════════════════════════════╝

# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026

# @version 0.4.3

implements: Department
implements: VaultBookCompatibility

exports: gov.__interface__
exports: registry.__interface__
exports: addys.__interface__
exports: deptBasics.__interface__

initializes: gov
initializes: registry[gov := gov]
initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.LocalGov as gov
import contracts.registries.modules.AddressRegistry as registry
import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics

from interfaces import Vault
from interfaces import Department
from interfaces import VaultBookCompatibility
from ethereum.ercs import IERC20
from ethereum.ercs import IERC4626

interface StabilityPool:
    def canAcceptLiquidationAsset(_stabAsset: address, _claimAsset: address) -> bool: view
    def claimableBalances(_stabAsset: address, _claimAsset: address) -> uint256: view
    def totalClaimableBalances(_claimAsset: address) -> uint256: view
    def vaultAssets(_index: uint256) -> address: view
    def isPaused() -> bool: view

interface Ledger:
    def didGetRewardsFromStabClaims(_amount: uint256): nonpayable
    def ripeAvailForRewards() -> uint256: view

interface MissionControl:
    def isRipeGovVaultId(_vaultId: uint256) -> bool: view
    def isStabVaultId(_vaultId: uint256) -> bool: view

interface LegacyStabilityPool:
    def indexOfAsset(_asset: address) -> uint256: view
    def getRipeHq() -> address: view

interface RipeToken:
    def mint(_to: address, _amount: uint256): nonpayable

interface RipeGovVault:
    def totalGovPoints() -> uint256: view

interface PriceDesk:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

# Per optional read; qualified against pinned Base routes and claim inventories.
LEGACY_READ_GAS: constant(uint256) = 8_000_000

# Reserve for cold CALL access, bounded 68-byte input / 33-byte output memory,
# and generated setup between GAS and STATICCALL. EIP-150 needs ceil(gas/63)
# in addition to the stipend. Check even successful zero-returning targets:
# a nested price source can fail soft inside an otherwise successful call.
LEGACY_READ_MIN_GAS: constant(uint256) = LEGACY_READ_GAS + (LEGACY_READ_GAS + 62) // 63 + 50_000

LEGACY_POOL: public(immutable(address))
LEGACY_POOL_REG_ID: constant(uint256) = 1


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minRegistryTimeLock: uint256,
    _maxRegistryTimeLock: uint256,
    _legacyPool: address,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    registry.__init__(_minRegistryTimeLock, _maxRegistryTimeLock, 0, "VaultBook.vy")
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, True) # can mint ripe only

    LEGACY_POOL = _legacyPool
    if _legacyPool != empty(address):
        assert chain.id == 8453 # dev: legacy pool only on Base
        assert _legacyPool.is_contract # dev: invalid legacy pool
        assert staticcall LegacyStabilityPool(_legacyPool).getRipeHq() == _ripeHq # dev: invalid legacy hq
        assert self._hasLegacyStabilityPoolInterface(_legacyPool, empty(address), empty(address)) # dev: invalid legacy interface

        # compatibility probe
        naAsset: address = staticcall StabilityPool(_legacyPool).vaultAssets(1)
        naBalance: bool = False
        naAsset, naBalance = staticcall Vault(_legacyPool).getUserAssetAtIndexAndHasBalance(empty(address), 0)


@view
@external
def isVaultBookAddr(_addr: address) -> bool:
    return registry._isValidAddr(_addr)


############
# Registry #
############


# new address


@external
def startAddNewAddressToRegistry(_addr: address, _description: String[64]) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._startAddNewAddressToRegistry(_addr, _description)


@external
def confirmNewAddressToRegistry(_addr: address) -> uint256:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._confirmNewAddressToRegistry(_addr)


@external
def cancelNewAddressToRegistry(_addr: address) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._cancelNewAddressToRegistry(_addr)


# address update


@external
def startAddressUpdateToRegistry(_regId: uint256, _newAddr: address) -> bool:
    assert not self._doesVaultIdHaveAnyFunds(_regId) # dev: vault has funds

    assert self._canPerformAction(msg.sender) # dev: no perms
    self._assertValidVaultReplacement(_regId, _newAddr)
    return registry._startAddressUpdateToRegistry(_regId, _newAddr)


@external
def confirmAddressUpdateToRegistry(_regId: uint256) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    assert not self._doesVaultIdHaveAnyFunds(_regId) # dev: vault has funds
    didUpdate: bool = registry._confirmAddressUpdateToRegistry(_regId)
    if didUpdate:
        self._assertValidVaultReplacement(_regId, registry._getAddr(_regId))
    return didUpdate


@external
def cancelAddressUpdateToRegistry(_regId: uint256) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._cancelAddressUpdateToRegistry(_regId)


# address disable


@external
def startAddressDisableInRegistry(_regId: uint256) -> bool:
    assert not self._doesVaultIdHaveAnyFunds(_regId) # dev: vault has funds

    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._startAddressDisableInRegistry(_regId)


@external
def confirmAddressDisableInRegistry(_regId: uint256) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    assert not self._doesVaultIdHaveAnyFunds(_regId) # dev: vault has funds
    return registry._confirmAddressDisableInRegistry(_regId)


@external
def cancelAddressDisableInRegistry(_regId: uint256) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._cancelAddressDisableInRegistry(_regId)


# check if vault has funds


@view
@internal
def _assertValidVaultReplacement(_vaultId: uint256, _vaultAddr: address):
    missionControl: address = addys._getMissionControlAddr()
    if missionControl == empty(address):
        return

    if staticcall MissionControl(missionControl).isRipeGovVaultId(_vaultId):
        # historical IDs remain routable forever, so replacements must retain
        # the RipeGov points interface used by future maintenance checks.
        points: uint256 = staticcall RipeGovVault(_vaultAddr).totalGovPoints()

    if staticcall MissionControl(missionControl).isStabVaultId(_vaultId):
        # Stability IDs retain reward-mint authority, so replacements must keep
        # the StabilityPool surface used by claims, liquidations, and config.
        naFunds: bool = staticcall Vault(_vaultAddr).doesVaultHaveAnyFunds()
        naStabAsset: address = staticcall StabilityPool(_vaultAddr).vaultAssets(1)
        naPair: uint256 = staticcall StabilityPool(_vaultAddr).claimableBalances(empty(address), empty(address))
        naCanAccept: bool = staticcall StabilityPool(_vaultAddr).canAcceptLiquidationAsset(empty(address), empty(address))
        naTotal: uint256 = staticcall StabilityPool(_vaultAddr).totalClaimableBalances(empty(address))
        naPaused: bool = staticcall StabilityPool(_vaultAddr).isPaused()


@view
@internal
def _doesVaultIdHaveAnyFunds(_vaultId: uint256) -> bool:
    vaultAddr: address = registry._getAddr(_vaultId)
    if vaultAddr == empty(address):
        return False
    if staticcall Vault(vaultAddr).doesVaultHaveAnyFunds():
        return True

    missionControl: address = addys._getMissionControlAddr()
    if missionControl != empty(address) and staticcall MissionControl(missionControl).isRipeGovVaultId(_vaultId):
        # zero-share governance points cannot be migrated; clear them before
        # retiring or repointing a historical RipeGov vault.
        return staticcall RipeGovVault(vaultAddr).totalGovPoints() != 0
    return False


######################
# Stab Claim Rewards #
######################


# pass thru from stability pool


@external
def mintRipeForStabPoolClaims(_amount: uint256, _ripeToken: address, _ledger: address) -> bool:
    vaultId: uint256 = registry._getRegId(msg.sender)
    assert vaultId != 0 # dev: no perms

    missionControl: address = addys._getMissionControlAddr()
    assert staticcall MissionControl(missionControl).isStabVaultId(vaultId) # dev: not stab vault

    ripeToken: address = addys._getRipeToken()
    ledger: address = addys._getLedgerAddr()
    assert _ripeToken == ripeToken # dev: invalid ripe token
    assert _ledger == ledger # dev: invalid ledger
    assert _amount <= staticcall Ledger(ledger).ripeAvailForRewards() # dev: insufficient rewards

    extcall RipeToken(ripeToken).mint(msg.sender, _amount)
    extcall Ledger(ledger).didGetRewardsFromStabClaims(_amount)
    return True


#############
# Utilities #
#############


@view
@internal
def _canPerformAction(_caller: address) -> bool:
    return gov._canGovern(_caller) and not deptBasics.isPaused


#######################
# Vault Compatibility #
#######################


@view
@internal
def _isRegisteredLegacyPool() -> bool:
    # true only when the pool's registry id is 1 and enabled ID 1 still points back at it.
    return registry._getRegId(LEGACY_POOL) == LEGACY_POOL_REG_ID and registry._getAddr(LEGACY_POOL_REG_ID) == LEGACY_POOL and registry._isValidRegId(LEGACY_POOL_REG_ID)


@view
@external
def canAcceptLiquidationAsset(_vaultAddr: address, _stabAsset: address, _claimAsset: address) -> bool:
    # a zero binding and every other vault forward here; the bound pool never calls the modern selector it lacks.
    if LEGACY_POOL == empty(address) or _vaultAddr != LEGACY_POOL:
        return staticcall StabilityPool(_vaultAddr).canAcceptLiquidationAsset(_stabAsset, _claimAsset)

    # the bound pool must still be the enabled registry ID 1 row, and it must not be paused.
    if not self._isRegisteredLegacyPool() or staticcall StabilityPool(_vaultAddr).isPaused():
        return False

    # the stabilization asset must be listed, and incoming collateral must be a real address.
    if staticcall LegacyStabilityPool(_vaultAddr).indexOfAsset(_stabAsset) == 0 or _claimAsset == empty(address):
        return False

    # incoming collateral cannot already be one of the pool's deposit assets.
    if staticcall LegacyStabilityPool(_vaultAddr).indexOfAsset(_claimAsset) != 0:
        return False

    # any claim reserved on the stabilization asset can make the sized payment unspendable.
    if staticcall StabilityPool(_vaultAddr).totalClaimableBalances(_stabAsset) != 0:
        return False

    # a GREEN claim on this cohort is payable only when pool GREEN covers every cohort's GREEN liability.
    greenToken: address = addys._getGreenToken()
    greenClaim: uint256 = staticcall StabilityPool(_vaultAddr).claimableBalances(_stabAsset, greenToken)
    if greenClaim != 0:
        if staticcall IERC20(greenToken).balanceOf(_vaultAddr) < staticcall StabilityPool(_vaultAddr).totalClaimableBalances(greenToken):
            return False

    # no stabilization tokens left: only the already-backed GREEN claim can pay.
    amount: uint256 = staticcall IERC20(_stabAsset).balanceOf(_vaultAddr)
    if amount == 0:
        return greenClaim != 0

    # positive GREEN custody is spendable one-for-one, so it needs no quote.
    if _stabAsset == greenToken:
        return True

    # sGREEN shares must convert into a positive amount of GREEN.
    savingsGreen: address = addys._getSavingsGreen()
    if _stabAsset == savingsGreen:
        return staticcall IERC4626(savingsGreen).convertToAssets(amount) != 0

    # other assets need a positive non-raising USD quote; a zero price rejects the pair.
    return staticcall PriceDesk(addys._getPriceDeskAddr()).getUsdValue(_stabAsset, amount) != 0


@view
@external
def getDeleverageTraversalAsset(_user: address, _vaultAddr: address, _index: uint256, _isStabVault: bool) -> (address, uint256):
    asset: address = empty(address)
    hasBalance: bool = False

    # only the bound pool takes this path; a zero binding and every other vault stay on the modern getters.
    if LEGACY_POOL != empty(address) and _vaultAddr == LEGACY_POOL:

        # an invalid ID 1 row skips the index instead of reading a pool that is no longer registered.
        if not self._isRegisteredLegacyPool():
            return empty(address), 0

        # keep an empty slot or a zero balance exactly as the pool reports it.
        asset, hasBalance = staticcall Vault(_vaultAddr).getUserAssetAtIndexAndHasBalance(_user, _index)
        if asset == empty(address) or not hasBalance:
            return asset, 0

        # a paused pool cannot be deleveraged, so keep the asset and report no amount.
        if staticcall StabilityPool(_vaultAddr).isPaused():
            return asset, 0

        # custody that is fully reserved for claims cannot fund a withdrawal, so skip before pricing.
        custody: uint256 = staticcall IERC20(asset).balanceOf(_vaultAddr)
        if custody <= staticcall StabilityPool(_vaultAddr).totalClaimableBalances(asset):
            return asset, 0

        # return full NAV when a withdrawal would succeed, else zero; this amount is never the marker 1.
        return asset, self._getExecutableLegacyNav(_user, _vaultAddr, asset, custody)

    # modern stability vaults already return the real token amount at this index.
    if _isStabVault:
        return staticcall Vault(_vaultAddr).getUserAssetAndAmountAtIndex(_user, _index)

    # ordinary vaults report presence as 1; the caller loads the real amount afterward.
    asset, hasBalance = staticcall Vault(_vaultAddr).getUserAssetAtIndexAndHasBalance(_user, _index)
    return asset, 1 if hasBalance else 0


@view
@internal
def _optionalUint(_target: address, _data: Bytes[68]) -> uint256:

    # stop if the remaining gas cannot cover the stipend and its EIP-150 reserve.
    assert msg.gas >= LEGACY_READ_MIN_GAS, "insufficient legacy read gas"
    success: bool = False
    response: Bytes[33] = b""

    # a revert or a short reply becomes zero so traversal can skip this read.
    success, response = raw_call(_target, _data, gas=LEGACY_READ_GAS, max_outsize=33, is_static_call=True, revert_on_failure=False)
    if not success or len(response) != 32:
        return 0

    return abi_decode(response, uint256)


@view
@internal
def _getExecutableLegacyNav(_user: address, _vaultAddr: address, _asset: address, _custody: uint256) -> uint256:

    # a missing, reverting, or zero NAV skips this index; direct withdrawals and claims stay strict.
    nav: uint256 = self._optionalUint(_vaultAddr, abi_encode(_user, _asset, method_id=method_id("getTotalAmountForUser(address,address)")))
    if nav == 0:
        return 0

    # user value includes virtual shares and rounding that getTotalAmountForUser omits.
    userValue: uint256 = self._optionalUint(_vaultAddr, abi_encode(_user, _asset, method_id=method_id("getTotalUserValue(address,address)")))

    # a zero user value, or one that would overflow against custody, cannot be priced.
    if userValue == 0 or userValue > max_value(uint256) // _custody:
        return 0

    # value raw custody as GREEN one-for-one, sGREEN in assets, and every other asset in USD.
    custodyValue: uint256 = _custody
    if _asset == addys._getSavingsGreen():
        custodyValue = self._optionalUint(_asset, abi_encode(_custody, method_id=method_id("convertToAssets(uint256)")))
    elif _asset != addys._getGreenToken():
        custodyValue = self._optionalUint(addys._getPriceDeskAddr(), abi_encode(_asset, _custody, method_id=method_id("getUsdValue(address,uint256)")))

    # a zero or failed quote means nothing can be withdrawn.
    if custodyValue == 0:
        return 0

    # scale user value by custody over custody value, mirroring _calcWithdrawalSharesAndAmount.
    executable: uint256 = userValue * _custody // custodyValue

    # a zero payout or a reverse quote that rounds to zero is skipped; userValue * custody already bounds this.
    if executable == 0 or executable * custodyValue // _custody == 0:
        return 0

    # the ratio only decides eligibility; sizing must keep the full uncapped NAV.
    return nav


@view
@external
def hasStabilityPoolInterface(_vaultAddr: address, _stabAsset: address, _probeClaimAsset: address) -> bool:
    # only the bound pool is checked through legacy selectors; every other vault uses the modern probe.
    if LEGACY_POOL != empty(address) and _vaultAddr == LEGACY_POOL:

        # an invalid ID 1 row is not treated as a stability pool.
        if not self._isRegisteredLegacyPool():
            return False

        return self._hasLegacyStabilityPoolInterface(_vaultAddr, _stabAsset, _probeClaimAsset)

    # decoding False still proves the modern selector exists, including on an empty pool.
    naCanAccept: bool = staticcall StabilityPool(_vaultAddr).canAcceptLiquidationAsset(_stabAsset, _probeClaimAsset)
    return True


@view
@internal
def _hasLegacyStabilityPoolInterface(_vaultAddr: address, _stabAsset: address, _probeClaimAsset: address) -> bool:
    # index, claim balance, total reservations, and pause must decode; their values do not matter.
    naIndex: uint256 = staticcall LegacyStabilityPool(_vaultAddr).indexOfAsset(_stabAsset)
    naPair: uint256 = staticcall StabilityPool(_vaultAddr).claimableBalances(_stabAsset, _probeClaimAsset)
    naTotal: uint256 = staticcall StabilityPool(_vaultAddr).totalClaimableBalances(_stabAsset)
    naPaused: bool = staticcall StabilityPool(_vaultAddr).isPaused()
    return True

