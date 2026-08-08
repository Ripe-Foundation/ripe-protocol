#                     ___                                    ___          ___     
#            ___     /  /\                                  /  /\        /  /\    
#           /  /\   /  /:/_                                /  /:/_      /  /::\   
#          /  /:/  /  /:/ /\   ___     ___  ___     ___   /  /:/ /\    /  /:/\:\  
#         /  /:/  /  /:/ /:/_ /__/\   /  /\/__/\   /  /\ /  /:/ /:/_  /  /:/~/:/  
#        /  /::\ /__/:/ /:/ /\\  \:\ /  /:/\  \:\ /  /://__/:/ /:/ /\/__/:/ /:/___
#       /__/:/\:\\  \:\/:/ /:/ \  \:\  /:/  \  \:\  /:/ \  \:\/:/ /:/\  \:\/:::::/
#       \__\/  \:\\  \::/ /:/   \  \:\/:/    \  \:\/:/   \  \::/ /:/  \  \::/~~~~ 
#            \  \:\\  \:\/:/     \  \::/      \  \::/     \  \:\/:/    \  \:\     
#             \__\/ \  \::/       \__\/        \__\/       \  \::/      \  \:\    
#                    \__\/                                  \__\/        \__\/    
#
#     ╔═══════════════════════════════════════════════════════════════════════╗
#     ║  ** Teller **                                                         ║
#     ║  Handles deposits, withdrawals, and entry-point for all user actions  ║
#     ╚═══════════════════════════════════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department
from interfaces import Vault
import interfaces.ConfigStructs as cs

from ethereum.ercs import IERC20

interface MissionControl:
    def ripeGovVaultConfig(_asset: address) -> cs.RipeGovVaultConfig: view
    def getTellerDepositConfig(_vaultId: uint256, _asset: address, _user: address) -> TellerDepositConfig: view
    def isSupportedAssetInVault(_vaultId: uint256, _asset: address) -> bool: view
    def getFirstVaultIdForAsset(_asset: address) -> uint256: view
    def isStabVaultId(_vaultId: uint256) -> bool: view
    def coreRipeGovVaultId() -> uint256: view
    def underscoreRegistry() -> address: view

interface RipeGovVault:
    def getLatestGovPoints(_lastShares: uint256, _lastPointsUpdate: uint256, _unlock: uint256, _terms: cs.LockTerms, _weight: uint256) -> uint256: view
    def totalUserGovPoints(_user: address) -> uint256: view
    def totalGovPoints() -> uint256: view
    def userGovData(_user: address, _asset: address) -> GovData: view
    def userBalances(_user: address, _asset: address) -> uint256: view

interface AddressRegistry:
    def isValidRegId(_regId: uint256) -> bool: view
    def getRegId(_addr: address) -> uint256: view
    def getAddr(_regId: uint256) -> address: view
    def isValidAddr(_addr: address) -> bool: view

interface CreditEngine:
    def getMaxWithdrawableForAsset(_user: address, _vaultId: uint256, _asset: address, _vaultAddr: address = empty(address), _a: addys.Addys = empty(addys.Addys)) -> uint256: view

interface Ledger:
    def userDepositPoints(_user: address, _vaultId: uint256, _asset: address) -> UserDepositPoints: view
    def isParticipatingInVault(_user: address, _vaultId: uint256) -> bool: view
    def getDepositLedgerData(_user: address, _vaultId: uint256) -> DepositLedgerData: view

interface VaultRegistry:
    def isEarnVault(_vaultAddr: address) -> bool: view

interface UnderscoreLedger:
    def isUserWallet(_addr: address) -> bool: view

interface UnderscoreWallet:
    def walletConfig() -> address: view

interface UnderscoreWalletConfig:
    def owner() -> address: view

# mirrors `Ledger.UserDepositPoints`, read to prove a source asset carries no residual entitlement
struct UserDepositPoints:
    balancePoints: uint256
    lastBalance: uint256
    lastUpdate: uint256

# mirrors `RipeGov.GovData`. Declared here (and identically in Teller) because each contract is its
# own compilation unit and Phase 1 may not add a shared file to `interfaces/`.
struct GovData:
    govPoints: uint256
    lastShares: uint256
    lastPointsUpdate: uint256
    unlock: uint256
    lastTerms: cs.LockTerms

# the complete original legacy record, captured before the withdrawal destroys it, plus the target
# point totals as they stood before the import (so the import's effect is checked as an exact delta)
struct LegacySourceSnapshot:
    sourceShares: uint256
    sourceAmount: uint256
    govPoints: uint256
    unlock: uint256
    lastTerms: cs.LockTerms
    targetUserPointsBefore: uint256
    targetTotalPointsBefore: uint256

struct DepositLedgerData:
    isParticipatingInVault: bool
    numUserVaults: uint256

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
    minDepositBalance: uint256

struct TellerWithdrawConfig:
    canWithdrawGeneral: bool
    canWithdrawAsset: bool
    isUserAllowed: bool
    canWithdrawForUser: bool
    minDepositBalance: uint256

UNDERSCORE_LEDGER_ID: constant(uint256) = 1
UNDERSCORE_LEGOBOOK_ID: constant(uint256) = 3
UNDERSCORE_VAULT_REGISTRY_ID: constant(uint256) = 10


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting


######################
# Deposit Validation #
######################


@view
@external
def validateOnDeposit(
    _asset: address,
    _amount: uint256,
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _depositor: address,
    _didAlreadyValidateSender: bool,
    _areFundsHereAlready: bool,
    _d: DepositLedgerData,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    a: addys.Addys = addys._getAddys(_a)

    config: TellerDepositConfig = staticcall MissionControl(a.missionControl).getTellerDepositConfig(_vaultId, _asset, _user)
    assert config.canDepositGeneral # dev: protocol deposits disabled
    assert config.canDepositAsset # dev: asset deposits disabled
    assert config.doesVaultSupportAsset # dev: vault does not support asset
    assert config.isUserAllowed # dev: user not on whitelist

    # trusted depositor
    isRipeDepartment: bool = addys._isValidRipeAddr(_depositor)

    # make sure depositor is allowed to deposit for user
    if not _didAlreadyValidateSender and _user != _depositor and not config.canAnyoneDeposit:
        assert isRipeDepartment or self._isUnderscoreWalletOwner(_user, _depositor, staticcall MissionControl(a.missionControl).underscoreRegistry()) # dev: cannot deposit for user

    # avail amount
    holder: address = _depositor
    if _areFundsHereAlready:
        holder = a.teller
    amount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(holder))
    assert amount != 0 # dev: cannot deposit 0

    # if depositing from ripe dept, skip these limits
    if isRipeDepartment:
        return amount
    
    # vault data
    vd: Vault.VaultDataOnDeposit = staticcall Vault(_vaultAddr).getVaultDataOnDeposit(_user, _asset)

    # check max vaults, max assets per vault
    if not _d.isParticipatingInVault:
        assert _d.numUserVaults < config.perUserMaxVaults # dev: reached max vaults

    elif not vd.hasPosition:
        assert vd.numAssets < config.perUserMaxAssetsPerVault # dev: reached max assets per vault

    # per user deposit limit
    availPerUserDeposit: uint256 = self._getAvailPerUserDepositLimit(vd.userBalance, config.perUserDepositLimit)
    assert availPerUserDeposit != 0 # dev: cannot deposit, reached user limit
    amount = min(amount, availPerUserDeposit)

    # global deposit limit
    availGlobalDeposit: uint256 = self._getAvailGlobalDepositLimit(vd.totalBalance, config.globalDepositLimit)
    assert availGlobalDeposit != 0 # dev: cannot deposit, reached global limit
    amount = min(amount, availGlobalDeposit)

    # min balance
    assert amount + vd.userBalance >= config.minDepositBalance # dev: too small a balance

    return amount


# per user deposit limit


@view 
@internal 
def _getAvailPerUserDepositLimit(_userDepositBal: uint256, _perUserDepositLimit: uint256) -> uint256:
    if _perUserDepositLimit == max_value(uint256):
        return max_value(uint256)
    availDeposits: uint256 = 0
    if _perUserDepositLimit > _userDepositBal:
        availDeposits = _perUserDepositLimit - _userDepositBal
    return availDeposits


# global deposit limit


@view 
@internal 
def _getAvailGlobalDepositLimit(_totalDepositBal: uint256, _globalDepositLimit: uint256) -> uint256:
    availDeposits: uint256 = 0
    if _globalDepositLimit > _totalDepositBal:
        availDeposits = _globalDepositLimit - _totalDepositBal
    return availDeposits


#########################
# Withdrawal Validation #
#########################


@view
@external
def validateOnWithdrawal(
    _asset: address,
    _amount: uint256,
    _user: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _caller: address,
    _config: TellerWithdrawConfig,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    a: addys.Addys = addys._getAddys(_a)
    assert _amount != 0 # dev: cannot withdraw 0

    assert _config.canWithdrawGeneral # dev: protocol withdrawals disabled
    assert _config.canWithdrawAsset # dev: asset withdrawals disabled
    assert _config.isUserAllowed # dev: user not on whitelist

    # make sure caller is allowed to withdraw for user
    if _user != _caller and not _config.canWithdrawForUser:
        assert self._isUnderscoreWalletOwner(_user, _caller, staticcall MissionControl(a.missionControl).underscoreRegistry()) # dev: not allowed to withdraw for user

    # max withdrawable
    maxWithdrawable: uint256 = staticcall CreditEngine(a.creditEngine).getMaxWithdrawableForAsset(_user, _vaultId, _asset, _vaultAddr, a)
    assert maxWithdrawable != 0 # dev: cannot withdraw anything

    return min(_amount, maxWithdrawable)


##############################
# Vault Migration Validation #
##############################


# ripe gov position migration


@view
@external
def validateRipeGovMigration(
    _user: address,
    _asset: address,
    _sourceVaultId: uint256,
    _targetVaultId: uint256,
) -> (address, address):
    assert empty(address) not in [_user, _asset] # dev: invalid user or asset
    assert _sourceVaultId != 0 and _targetVaultId != 0 # dev: invalid vault id
    assert _sourceVaultId != _targetVaultId # dev: same vault

    # validation
    a: addys.Addys = addys._getAddys()
    vaultBook: AddressRegistry = AddressRegistry(a.vaultBook)
    assert staticcall vaultBook.isValidRegId(_sourceVaultId) # dev: invalid source vault id
    assert staticcall vaultBook.isValidRegId(_targetVaultId) # dev: invalid target vault id
    assert staticcall MissionControl(a.missionControl).isSupportedAssetInVault(_sourceVaultId, _asset) # dev: unsupported source asset
    assert staticcall MissionControl(a.missionControl).isSupportedAssetInVault(_targetVaultId, _asset) # dev: unsupported target asset

    # get vault addresses
    sourceVault: address = staticcall vaultBook.getAddr(_sourceVaultId)
    targetVault: address = staticcall vaultBook.getAddr(_targetVaultId)
    assert sourceVault != empty(address) and sourceVault.is_contract # dev: invalid source vault
    assert targetVault != empty(address) and targetVault.is_contract # dev: invalid target vault
    assert sourceVault != targetVault # dev: same vault
    assert staticcall Vault(sourceVault).isPaused() # dev: source vault not paused
    assert staticcall Vault(targetVault).isPaused() # dev: target vault not paused

    sourceLedgerData: DepositLedgerData = staticcall Ledger(a.ledger).getDepositLedgerData(_user, _sourceVaultId)
    assert sourceLedgerData.isParticipatingInVault # dev: source vault missing from Ledger

    return sourceVault, targetVault


# BASE LEGACY ripe gov position migration
#
# Separate from `validateRipeGovMigration` on purpose. That validator requires BOTH endpoints
# paused, which suits an exporter-capable source. The deployed Base legacy vault predates the
# exporter and cannot be changed, so its migration drives the ordinary `SharesVault` withdrawal --
# which means the legacy source must stay UNPAUSED. Only the target is paused, because that pause
# is the migration-only mode in which `importPositionForMigration` is the sole way in.


# EXCLUSIVE FREEZE. A Teller pause alone does NOT close the legacy vault. The DEPLOYED legacy vault
# keeps its pre-migration permissions, so it authorizes AuctionHouse and CreditEngine on
# `withdrawTokensFromVault` / `transferBalanceWithinVault`, HumanResources on the contributor
# transfer and burn routes, and any valid Ripe department on `updateUserGovPoints` / `adjustLock` /
# `releaseLock`. Deleverage is named explicitly rather than covered by the AuctionHouse pause: it is
# reachable from a switchboard, checks only its OWN pause flag, and then withdraws through
# AuctionHouse against a caller-supplied vault address.


@view
@internal
def _assertExclusiveFreeze(_a: addys.Addys):
    assert staticcall Department(_a.teller).isPaused() # dev: teller not paused
    assert staticcall Department(_a.auctionHouse).isPaused() # dev: auction house not paused
    assert staticcall Department(_a.creditEngine).isPaused() # dev: credit engine not paused
    assert staticcall Department(_a.humanResources).isPaused() # dev: human resources not paused
    assert staticcall Department(addys._getDeleverageAddr()).isPaused() # dev: deleverage not paused


@view
@external
def validateLegacyRipeGovMigration(
    _user: address,
    _asset: address,
    _sourceVaultId: uint256,
    _sourceVault: address,
    _targetVaultId: uint256,
    _targetVault: address,
    _a: addys.Addys = empty(addys.Addys),
) -> bool:
    a: addys.Addys = addys._getAddys(_a)

    assert empty(address) not in [_user, _asset] # dev: invalid user or asset
    assert _sourceVaultId != 0 and _targetVaultId != 0 # dev: invalid vault id
    assert _sourceVaultId != _targetVaultId # dev: same vault id
    assert _sourceVault != _targetVault # dev: same vault
    assert _sourceVault != empty(address) and _sourceVault.is_contract # dev: invalid source vault
    assert _targetVault != empty(address) and _targetVault.is_contract # dev: invalid target vault

    # exact registration -- id and address must agree in the live VaultBook
    vaultBook: AddressRegistry = AddressRegistry(a.vaultBook)
    assert staticcall vaultBook.getAddr(_sourceVaultId) == _sourceVault # dev: source vault not registered
    assert staticcall vaultBook.getAddr(_targetVaultId) == _targetVault # dev: target vault not registered

    # Base asymmetry (see note above) -- deliberately NOT the both-paused upstream rule
    assert not staticcall Vault(_sourceVault).isPaused() # dev: source vault paused
    assert staticcall Vault(_targetVault).isPaused() # dev: target vault not in migration state

    self._assertExclusiveFreeze(a)

    # both endpoints must support the asset being moved
    mc: MissionControl = MissionControl(a.missionControl)
    assert staticcall mc.isSupportedAssetInVault(_sourceVaultId, _asset) # dev: unsupported source asset
    assert staticcall mc.isSupportedAssetInVault(_targetVaultId, _asset) # dev: unsupported target asset

    # source position must exist and be enumerated in both the vault and the Ledger
    assert staticcall Vault(_sourceVault).isUserInVaultAsset(_user, _asset) # dev: source asset not registered
    assert staticcall Vault(_sourceVault).doesUserHaveBalance(_user, _asset) # dev: no source balance
    assert staticcall Ledger(a.ledger).isParticipatingInVault(_user, _sourceVaultId) # dev: source vault missing from Ledger

    # no target replay
    assert not staticcall Vault(_targetVault).doesUserHaveBalance(_user, _asset) # dev: target position exists

    return True


@view
@external
def getLegacyRipeGovSourceSnapshot(
    _user: address,
    _asset: address,
    _sourceVault: address,
    _targetVault: address,
    _a: addys.Addys = empty(addys.Addys),
) -> LegacySourceSnapshot:
    a: addys.Addys = addys._getAddys(_a)

    gd: GovData = staticcall RipeGovVault(_sourceVault).userGovData(_user, _asset)
    config: cs.RipeGovVaultConfig = staticcall MissionControl(a.missionControl).ripeGovVaultConfig(_asset)

    sourceShares: uint256 = staticcall RipeGovVault(_sourceVault).userBalances(_user, _asset)
    sourceAmount: uint256 = staticcall Vault(_sourceVault).getTotalAmountForUser(_user, _asset)
    assert sourceShares != 0 and sourceAmount != 0 # dev: no source position

    # pending points through THIS block, using the source vault's own math, the user's original
    # terms / unlock / last update / shares and the unchanged current asset weight. Off-chain
    # manifest values are evidence, never the execution input for this number.
    pending: uint256 = staticcall RipeGovVault(_sourceVault).getLatestGovPoints(
        gd.lastShares,
        gd.lastPointsUpdate,
        gd.unlock,
        gd.lastTerms,
        config.assetWeight,
    )

    return LegacySourceSnapshot(
        sourceShares=sourceShares,
        sourceAmount=sourceAmount,
        govPoints=gd.govPoints + pending,
        unlock=gd.unlock,
        lastTerms=gd.lastTerms,
        targetUserPointsBefore=staticcall RipeGovVault(_targetVault).totalUserGovPoints(_user),
        targetTotalPointsBefore=staticcall RipeGovVault(_targetVault).totalGovPoints(),
    )


@view
@external
def verifyLegacyRipeGovImport(
    _user: address,
    _asset: address,
    _sourceVault: address,
    _sourceVaultId: uint256,
    _targetVault: address,
    _targetVaultId: uint256,
    _amount: uint256,
    _targetShares: uint256,
    _snapshot: LegacySourceSnapshot,
    _a: addys.Addys = empty(addys.Addys),
) -> bool:
    a: addys.Addys = addys._getAddys(_a)

    # complete source depletion for this asset
    assert staticcall RipeGovVault(_sourceVault).userBalances(_user, _asset) == 0 # dev: source shares remain
    assert staticcall Vault(_sourceVault).getTotalAmountForUser(_user, _asset) == 0 # dev: source amount remains
    assert not staticcall Vault(_sourceVault).doesUserHaveBalance(_user, _asset) # dev: source balance remains

    # the source registration and its Ledger membership MUST still be here -- reward settlement has
    # not happened yet, and the user may still hold the other source asset. This is the deliberate
    # divergence from the upstream flow, which removes the source Ledger entry immediately.
    assert staticcall Vault(_sourceVault).isUserInVaultAsset(_user, _asset) # dev: source asset deregistered
    assert staticcall Ledger(a.ledger).isParticipatingInVault(_user, _sourceVaultId) # dev: source ledger removed

    # exact target position
    assert _amount != 0 # dev: invalid migration amount
    assert staticcall RipeGovVault(_targetVault).userBalances(_user, _asset) == _targetShares # dev: target shares mismatch
    assert staticcall Vault(_targetVault).isUserInVaultAsset(_user, _asset) # dev: target asset not registered
    assert staticcall Vault(_targetVault).doesUserHaveBalance(_user, _asset) # dev: target position missing
    assert staticcall Ledger(a.ledger).isParticipatingInVault(_user, _targetVaultId) # dev: target ledger missing

    # preserved governance record -- points stock plus pending, original unlock, original terms
    newGd: GovData = staticcall RipeGovVault(_targetVault).userGovData(_user, _asset)
    assert newGd.govPoints == _snapshot.govPoints # dev: target points mismatch
    assert newGd.lastShares == _targetShares # dev: target last shares mismatch
    assert newGd.lastPointsUpdate == block.number # dev: target last update mismatch
    assert newGd.unlock == _snapshot.unlock # dev: target unlock mismatch
    assert newGd.lastTerms.minLockDuration == _snapshot.lastTerms.minLockDuration # dev: target terms mismatch
    assert newGd.lastTerms.maxLockDuration == _snapshot.lastTerms.maxLockDuration # dev: target terms mismatch
    assert newGd.lastTerms.maxLockBoost == _snapshot.lastTerms.maxLockBoost # dev: target terms mismatch
    assert newGd.lastTerms.canExit == _snapshot.lastTerms.canExit # dev: target terms mismatch
    assert newGd.lastTerms.exitFee == _snapshot.lastTerms.exitFee # dev: target terms mismatch

    # exact deltas on both target point totals
    assert staticcall RipeGovVault(_targetVault).totalUserGovPoints(_user) == _snapshot.targetUserPointsBefore + _snapshot.govPoints # dev: target user total mismatch
    assert staticcall RipeGovVault(_targetVault).totalGovPoints() == _snapshot.targetTotalPointsBefore + _snapshot.govPoints # dev: target global total mismatch

    return True


@view
@external
def verifyLegacyRipeGovSettlement(
    _user: address,
    _sourceVault: address,
    _sourceVaultId: uint256,
    _settledAsset: address,
    _lpAsset: address,
    _didRemoveVault: bool,
    _a: addys.Addys = empty(addys.Addys),
) -> bool:
    a: addys.Addys = addys._getAddys(_a)

    # the freeze must have held for the whole settlement. This runs after Lootbox has mutated
    # state, but the call is atomic -- a failure here reverts the entire settlement.
    self._assertExclusiveFreeze(a)

    assert not staticcall Vault(_sourceVault).doesUserHaveBalance(_user, _settledAsset) # dev: settled asset has balance
    assert not staticcall Vault(_sourceVault).isUserInVaultAsset(_user, _settledAsset) # dev: settled asset not deregistered

    stillParticipating: bool = staticcall Ledger(a.ledger).isParticipatingInVault(_user, _sourceVaultId)
    assert stillParticipating != _didRemoveVault # dev: ledger state mismatch

    if _didRemoveVault:
        # nothing may remain REGISTERED in the source
        assert staticcall Vault(_sourceVault).numUserAssets(_user) <= 1 # dev: source registrations remain

        # ...and nothing may remain OWED on either live source asset. Registration count alone is
        # not proof of reward-freeness: an asset deregistered in an earlier round could still hold
        # residual Ledger deposit points, which no enumeration would surface again.
        # LIMIT: the deprecated pool is not read here; its emptiness (including zero residual
        # deposit points) is a hard Phase 2 census precondition.
        ripePoints: UserDepositPoints = staticcall Ledger(a.ledger).userDepositPoints(_user, _sourceVaultId, a.ripeToken)
        lpPoints: UserDepositPoints = staticcall Ledger(a.ledger).userDepositPoints(_user, _sourceVaultId, _lpAsset)
        assert ripePoints.balancePoints == 0 # dev: ripe entitlement remains
        assert lpPoints.balancePoints == 0 # dev: lp entitlement remains

    return True


# generic deposit vault position migration


@view
@external
def validateVaultMigration(
    _user: address,
    _asset: address,
    _sourceVaultId: uint256,
    _targetVaultId: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> (address, address):
    a: addys.Addys = addys._getAddys(_a)

    assert empty(address) not in [_user, _asset] # dev: invalid user or asset
    assert _sourceVaultId != 0 and _targetVaultId != 0 # dev: invalid vault id
    assert _sourceVaultId != _targetVaultId # dev: same vault

    # validation
    vaultBook: AddressRegistry = AddressRegistry(a.vaultBook)
    assert staticcall vaultBook.isValidRegId(_sourceVaultId) # dev: invalid source vault id
    assert staticcall vaultBook.isValidRegId(_targetVaultId) # dev: invalid target vault id

    mc: MissionControl = MissionControl(a.missionControl)
    assert staticcall mc.isSupportedAssetInVault(_sourceVaultId, _asset) # dev: unsupported source asset
    assert staticcall mc.isSupportedAssetInVault(_targetVaultId, _asset) # dev: unsupported target asset

    # get vault addresses
    sourceVault: address = staticcall vaultBook.getAddr(_sourceVaultId)
    targetVault: address = staticcall vaultBook.getAddr(_targetVaultId)
    assert sourceVault != empty(address) and sourceVault.is_contract # dev: invalid source vault
    assert targetVault != empty(address) and targetVault.is_contract # dev: invalid target vault
    assert sourceVault != targetVault # dev: same vault
    assert not staticcall Vault(sourceVault).isPaused() # dev: source vault paused
    assert not staticcall Vault(targetVault).isPaused() # dev: target vault paused

    sourceLedgerData: DepositLedgerData = staticcall Ledger(a.ledger).getDepositLedgerData(_user, _sourceVaultId)
    assert sourceLedgerData.isParticipatingInVault # dev: source vault missing from Ledger

    # the current core ripe gov vault is never an eligible endpoint.
    coreRipeGovVaultId: uint256 = staticcall mc.coreRipeGovVaultId()
    assert coreRipeGovVaultId != 0 # dev: invalid core ripe gov vault id
    assert _sourceVaultId != coreRipeGovVaultId # dev: source is core ripe gov
    assert _targetVaultId != coreRipeGovVaultId # dev: target is core ripe gov

    # both endpoints must share stability classification
    isSourceStabVault: bool = staticcall mc.isStabVaultId(_sourceVaultId)
    isTargetStabVault: bool = staticcall mc.isStabVaultId(_targetVaultId)
    assert isSourceStabVault == isTargetStabVault # dev: stab vault mismatch

    return sourceVault, targetVault


##############
# Vault Info #
##############


@view
@external
def getVaultAddrAndId(
    _asset: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _vaultBook: address,
    _missionControl: address,
) -> (address, uint256):
    vaultAddr: address = empty(address)
    vaultId: uint256 = 0

    # if no vault data specified, get first vault id for asset
    if _vaultAddr == empty(address) and _vaultId == 0:
        vaultId = staticcall MissionControl(_missionControl).getFirstVaultIdForAsset(_asset)
        assert vaultId != 0 # dev: invalid asset
        vaultAddr = staticcall AddressRegistry(_vaultBook).getAddr(vaultId)
        assert vaultAddr != empty(address) # dev: invalid vault id

    # vault id
    elif _vaultId != 0:
        vaultAddr = staticcall AddressRegistry(_vaultBook).getAddr(_vaultId)
        assert vaultAddr != empty(address) # dev: invalid vault id
        vaultId = _vaultId
        if _vaultAddr != empty(address):
            assert vaultAddr == _vaultAddr # dev: vault id and vault addr mismatch

    # vault addr
    elif _vaultAddr != empty(address):
        vaultId = staticcall AddressRegistry(_vaultBook).getRegId(_vaultAddr) # dev: invalid vault addr
        assert vaultId != 0 # dev: invalid vault addr
        vaultAddr = _vaultAddr

    return vaultAddr, vaultId


##############
# Underscore #
##############


@view
@external
def isUnderscoreWalletOrVault(_addr: address, _mc: address = empty(address)) -> bool:
    missionControl: address = _mc
    if _mc == empty(address):
        missionControl = addys._getMissionControlAddr()
    underscore: address = staticcall MissionControl(missionControl).underscoreRegistry()
    return self._isUnderscoreWallet(_addr, underscore) or self._isUnderscoreVault(_addr, underscore)


# underscore wallet


@view
@external
def isUnderscoreWallet(_user: address, _mc: address = empty(address)) -> bool:
    missionControl: address = _mc
    if _mc == empty(address):
        missionControl = addys._getMissionControlAddr()
    underscore: address = staticcall MissionControl(missionControl).underscoreRegistry()
    return self._isUnderscoreWallet(_user, underscore)


@view
@internal
def _isUnderscoreWallet(_user: address, _underscore: address) -> bool:
    if _underscore == empty(address):
        return False
    undyLedger: address = staticcall AddressRegistry(_underscore).getAddr(UNDERSCORE_LEDGER_ID)
    if undyLedger == empty(address):
        return False

    # check if user is underscore wallet
    return staticcall UnderscoreLedger(undyLedger).isUserWallet(_user)


# underscore vault check


@view
@external
def isUnderscoreVault(_user: address, _mc: address = empty(address)) -> bool:
    missionControl: address = _mc
    if _mc == empty(address):
        missionControl = addys._getMissionControlAddr()
    underscore: address = staticcall MissionControl(missionControl).underscoreRegistry()
    return self._isUnderscoreVault(_user, underscore)


@view
@internal
def _isUnderscoreVault(_user: address, _underscore: address) -> bool:
    if _underscore == empty(address):
        return False

    # check if underscore vault
    vaultRegistry: address = staticcall AddressRegistry(_underscore).getAddr(UNDERSCORE_VAULT_REGISTRY_ID)
    if vaultRegistry == empty(address):
        return False

    # check if vault is an earn vault
    return staticcall VaultRegistry(vaultRegistry).isEarnVault(_user)


# underscore wallet owner check


@view
@external
def isUnderscoreWalletOwner(_user: address, _caller: address, _mc: address = empty(address)) -> bool:
    missionControl: address = _mc
    if _mc == empty(address):
        missionControl = addys._getMissionControlAddr()
    underscore: address = staticcall MissionControl(missionControl).underscoreRegistry()
    return self._isUnderscoreWalletOwner(_user, _caller, underscore)


@view
@internal
def _isUnderscoreWalletOwner(_user: address, _caller: address, _underscore: address) -> bool:
    if _underscore == empty(address):
        return False

    if not self._isUnderscoreWallet(_user, _underscore):
        return False

    walletConfig: address = staticcall UnderscoreWallet(_user).walletConfig()
    if walletConfig == empty(address):
        return False

    # check if caller is owner
    return staticcall UnderscoreWalletConfig(walletConfig).owner() == _caller


# underscore address check


@view
@external
def isUnderscoreAddr(_addr: address, _mc: address = empty(address)) -> bool:
    missionControl: address = _mc
    if _mc == empty(address):
        missionControl = addys._getMissionControlAddr()
    underscore: address = staticcall MissionControl(_mc).underscoreRegistry()
    return self._isUnderscoreAddr(_addr, underscore)


@view
@internal
def _isUnderscoreAddr(_addr: address, _underscore: address) -> bool:
    if _underscore == empty(address):
        return False

    # check if addr is in underscore registry (Loot Distributor)
    if staticcall AddressRegistry(_underscore).isValidAddr(_addr):
        return True

    # check if addr is an underscore lego
    undyLegoBook: address = staticcall AddressRegistry(_underscore).getAddr(UNDERSCORE_LEGOBOOK_ID)
    if undyLegoBook == empty(address):
        return False
    return staticcall AddressRegistry(undyLegoBook).isValidAddr(_addr)


# owner or lego


@view
@external
def isUnderscoreOwnerOrLego(_user: address, _caller: address, _mc: address = empty(address)) -> bool:
    missionControl: address = _mc
    if _mc == empty(address):
        missionControl = addys._getMissionControlAddr()
    underscore: address = staticcall MissionControl(missionControl).underscoreRegistry()
    return self._isUnderscoreWalletOwner(_user, _caller, underscore) or self._isUnderscoreAddr(_caller, underscore)
