# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3
# pragma optimize codesize

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


struct GovData:
    govPoints: uint256
    lastShares: uint256
    lastPointsUpdate: uint256
    unlock: uint256
    lastTerms: cs.LockTerms


struct LegacySourceSnapshot:
    sourceShares: uint256
    sourceAmount: uint256
    govPoints: uint256
    unlock: uint256
    lastTerms: cs.LockTerms
    targetUserPointsBefore: uint256
    targetTotalPointsBefore: uint256


struct RipeGovMigrationData:
    amount: uint256
    govPoints: uint256
    unlock: uint256
    lastTerms: cs.LockTerms


struct RipeGovMigration:
    user: address
    asset: address
    sourceVaultId: uint256
    targetVaultId: uint256


struct VaultMigration:
    user: address
    asset: address
    sourceVaultId: uint256
    targetVaultId: uint256


interface AddressRegistry:
    def isValidRegId(_regId: uint256) -> bool: view
    def getAddr(_regId: uint256) -> address: view


interface MissionControl:
    def ripeGovVaultConfig(_asset: address) -> cs.RipeGovVaultConfig: view
    def isSupportedAssetInVault(_vaultId: uint256, _asset: address) -> bool: view
    def isStabVaultId(_vaultId: uint256) -> bool: view
    def coreRipeGovVaultId() -> uint256: view


interface RipeGovVault:
    def getLatestGovPoints(_lastShares: uint256, _lastPointsUpdate: uint256, _unlock: uint256, _terms: cs.LockTerms, _weight: uint256) -> uint256: view
    def totalUserGovPoints(_user: address) -> uint256: view
    def totalGovPoints() -> uint256: view
    def userGovData(_user: address, _asset: address) -> GovData: view
    def userBalances(_user: address, _asset: address) -> uint256: view


interface Ledger:
    def isParticipatingInVault(_user: address, _vaultId: uint256) -> bool: view


interface Teller:
    def executeRipeGovSource(_user: address, _asset: address, _sourceVault: address, _targetVault: address, _legacyMigration: RipeGovMigrationData, _shouldUseVaultWithdrawal: bool) -> RipeGovMigrationData: nonpayable
    def executeRipeGovImport(_user: address, _asset: address, _sourceVault: address, _targetVaultId: uint256, _targetVault: address, _migration: RipeGovMigrationData) -> uint256: nonpayable
    def executeVaultWithdrawal(_user: address, _asset: address, _sourceVault: address) -> (uint256, bool): nonpayable
    def executeVaultDeposit(_user: address, _asset: address, _amount: uint256, _targetVaultId: uint256, _targetVault: address) -> uint256: nonpayable


interface Lootbox:
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address, _a: addys.Addys = empty(addys.Addys)): nonpayable


event RipeGovPositionMigrationExecuted:
    user: indexed(address)
    asset: indexed(address)
    caller: indexed(address)
    sourceVaultId: uint256
    targetVaultId: uint256
    sourceVault: address
    targetVault: address
    amount: uint256
    targetShares: uint256
    govPoints: uint256
    unlock: uint256


event VaultPositionMigrationExecuted:
    user: indexed(address)
    asset: indexed(address)
    caller: indexed(address)
    sourceVaultId: uint256
    targetVaultId: uint256
    amount: uint256


event LegacyRipeGovMigrationAssetSet:
    asset: indexed(address)
    caller: indexed(address)


event LegacyRipeGovPositionMigrationExecuted:
    user: indexed(address)
    asset: indexed(address)
    caller: indexed(address)
    amount: uint256
    targetShares: uint256
    govPoints: uint256
    unlock: uint256


MAX_RIPE_GOV_MIGRATIONS: constant(uint256) = 25
MAX_VAULT_MIGRATIONS: constant(uint256) = 25
MAX_LEGACY_MIGRATIONS: constant(uint256) = 25

SWITCHBOARD_ECHO_ID: constant(uint256) = 5
LEGACY_RIPE_GOV_VAULT_ID: constant(uint256) = 2

LEGACY_RIPE_GOV_VAULT: public(immutable(address))
LEGACY_CHAIN_ID: public(immutable(uint256))

activeMigrationAsset: public(address)
legacyMigrationUserDedupe: transient(HashMap[address, bool])


@deploy
def __init__(
    _ripeHq: address,
    _shouldPause: bool,
    _legacyRipeGovVault: address,
    _legacyChainId: uint256,
):
    addys.__init__(_ripeHq)
    deptBasics.__init__(_shouldPause, False, False) # no minting
    assert (_legacyRipeGovVault == empty(address)) == (_legacyChainId == 0) # dev: incomplete legacy binding
    LEGACY_RIPE_GOV_VAULT = _legacyRipeGovVault
    LEGACY_CHAIN_ID = _legacyChainId


@view
@internal
def _assertSwitchboardEcho():
    switchboard: address = addys._getSwitchboardAddr()
    assert switchboard != empty(address) # dev: switchboard not registered
    assert msg.sender == staticcall AddressRegistry(switchboard).getAddr(SWITCHBOARD_ECHO_ID) # dev: only switchboard echo allowed


@view
@internal
def _assertLegacyBinding(_sourceVault: address):
    assert LEGACY_CHAIN_ID != 0 and chain.id == LEGACY_CHAIN_ID # dev: legacy migration disabled
    assert LEGACY_RIPE_GOV_VAULT != empty(address) and _sourceVault == LEGACY_RIPE_GOV_VAULT # dev: invalid legacy vault


@view
@internal
def _assertExclusiveFreeze(_a: addys.Addys):
    assert staticcall Department(_a.teller).isPaused() # dev: teller not paused
    assert staticcall Department(_a.auctionHouse).isPaused() # dev: auction house not paused
    assert staticcall Department(_a.creditEngine).isPaused() # dev: credit engine not paused
    assert staticcall Department(_a.humanResources).isPaused() # dev: human resources not paused
    assert staticcall Department(addys._getDeleverageAddr()).isPaused() # dev: deleverage not paused


@external
def migrateRipeGovPositions(
    _migrations: DynArray[RipeGovMigration, MAX_RIPE_GOV_MIGRATIONS],
    _caller: address,
) -> uint256:
    self._assertSwitchboardEcho()
    assert not deptBasics.isPaused # dev: contract paused
    assert _caller != empty(address) # dev: invalid caller
    assert len(_migrations) != 0 # dev: no migrations

    for migration: RipeGovMigration in _migrations:
        self._migrateRipeGovPosition(
            migration.user,
            migration.asset,
            migration.sourceVaultId,
            migration.targetVaultId,
            _caller,
        )

    return len(_migrations)


@external
def migrateVaultPositions(
    _migrations: DynArray[VaultMigration, MAX_VAULT_MIGRATIONS],
    _caller: address,
) -> uint256:
    self._assertSwitchboardEcho()
    assert not deptBasics.isPaused # dev: contract paused
    assert _caller != empty(address) # dev: invalid caller
    assert len(_migrations) != 0 # dev: no migrations

    a: addys.Addys = addys._getAddys()
    teller: Teller = Teller(a.teller)
    for migration: VaultMigration in _migrations:
        sourceVault: address = empty(address)
        targetVault: address = empty(address)
        sourceVault, targetVault = self._validateVaultMigration(
            migration.user,
            migration.asset,
            migration.sourceVaultId,
            migration.targetVaultId,
            a,
        )

        tellerBalanceBefore: uint256 = staticcall IERC20(migration.asset).balanceOf(a.teller)
        amount: uint256 = 0
        isDepleted: bool = False
        amount, isDepleted = extcall teller.executeVaultWithdrawal(
            migration.user,
            migration.asset,
            sourceVault,
        )
        assert isDepleted # dev: source position not depleted
        assert amount != 0 # dev: invalid migration amount
        tellerBalanceAfter: uint256 = staticcall IERC20(migration.asset).balanceOf(a.teller)
        assert tellerBalanceAfter >= tellerBalanceBefore # dev: invalid migration receipt
        assert tellerBalanceAfter - tellerBalanceBefore == amount # dev: inexact migration receipt
        assert not staticcall Vault(sourceVault).doesUserHaveBalance(migration.user, migration.asset) # dev: source balance remains

        deposited: uint256 = extcall teller.executeVaultDeposit(
            migration.user,
            migration.asset,
            amount,
            migration.targetVaultId,
            targetVault,
        )
        assert deposited == amount # dev: inexact migration deposit
        assert staticcall IERC20(migration.asset).balanceOf(a.teller) == tellerBalanceBefore # dev: teller balance remains
        extcall Lootbox(a.lootbox).updateDepositPoints(
            migration.user,
            migration.sourceVaultId,
            sourceVault,
            migration.asset,
            a,
        )

        log VaultPositionMigrationExecuted(
            user=migration.user,
            asset=migration.asset,
            caller=_caller,
            sourceVaultId=migration.sourceVaultId,
            targetVaultId=migration.targetVaultId,
            amount=amount,
        )

    return len(_migrations)


@external
def setLegacyRipeGovMigrationAsset(_asset: address, _caller: address) -> bool:
    self._assertSwitchboardEcho()
    assert not deptBasics.isPaused # dev: contract paused
    assert _caller != empty(address) # dev: invalid caller
    assert LEGACY_CHAIN_ID != 0 and LEGACY_RIPE_GOV_VAULT != empty(address) # dev: legacy migration disabled

    a: addys.Addys = addys._getAddys()
    sourceVault: address = staticcall AddressRegistry(a.vaultBook).getAddr(LEGACY_RIPE_GOV_VAULT_ID)
    self._assertLegacyBinding(sourceVault)
    assert _asset == empty(address) or staticcall MissionControl(a.missionControl).isSupportedAssetInVault(LEGACY_RIPE_GOV_VAULT_ID, _asset) # dev: unapproved migration asset

    if _asset != empty(address):
        assert self.activeMigrationAsset == empty(address) # dev: window already open

    self.activeMigrationAsset = _asset
    log LegacyRipeGovMigrationAssetSet(asset=_asset, caller=_caller)
    return True


@external
def migrateLegacyRipeGovPositions(
    _users: DynArray[address, MAX_LEGACY_MIGRATIONS],
    _asset: address,
    _caller: address,
) -> uint256:
    self._assertSwitchboardEcho()
    assert not deptBasics.isPaused # dev: contract paused
    assert _caller != empty(address) # dev: invalid caller
    assert len(_users) != 0 # dev: no migrations
    assert _asset != empty(address) and _asset == self.activeMigrationAsset # dev: asset window closed

    a: addys.Addys = addys._getAddys()
    targetVaultId: uint256 = staticcall MissionControl(a.missionControl).coreRipeGovVaultId()
    assert targetVaultId != 0 and targetVaultId != LEGACY_RIPE_GOV_VAULT_ID # dev: invalid target vault id
    sourceVault: address = staticcall AddressRegistry(a.vaultBook).getAddr(LEGACY_RIPE_GOV_VAULT_ID)
    targetVault: address = staticcall AddressRegistry(a.vaultBook).getAddr(targetVaultId)
    self._assertLegacyBinding(sourceVault)

    teller: Teller = Teller(a.teller)
    for user: address in _users:
        assert user != empty(address) # dev: invalid user
        assert not self.legacyMigrationUserDedupe[user] # dev: duplicate user
        self.legacyMigrationUserDedupe[user] = True

        self._validateLegacyRipeGovMigration(user, _asset, sourceVault, targetVaultId, targetVault, a)
        snap: LegacySourceSnapshot = self._getLegacyRipeGovSourceSnapshot(user, _asset, sourceVault, targetVault, a)
        expectedMigration: RipeGovMigrationData = RipeGovMigrationData(
            amount=snap.sourceAmount,
            govPoints=snap.govPoints,
            unlock=snap.unlock,
            lastTerms=snap.lastTerms,
        )

        actualMigration: RipeGovMigrationData = empty(RipeGovMigrationData)
        targetShares: uint256 = 0
        targetBalanceBefore: uint256 = staticcall IERC20(_asset).balanceOf(targetVault)
        tellerBalanceBefore: uint256 = staticcall IERC20(_asset).balanceOf(a.teller)
        actualMigration = extcall teller.executeRipeGovSource(
            user,
            _asset,
            sourceVault,
            targetVault,
            expectedMigration,
            True,
        )
        assert actualMigration.amount == expectedMigration.amount # dev: migration amount mismatch
        assert actualMigration.govPoints == expectedMigration.govPoints # dev: migration points mismatch
        assert actualMigration.unlock == expectedMigration.unlock # dev: migration unlock mismatch
        self._verifyRipeGovSourceExecution(
            user,
            _asset,
            sourceVault,
            targetVault,
            actualMigration.amount,
            targetBalanceBefore,
            tellerBalanceBefore,
        )
        targetShares = extcall teller.executeRipeGovImport(
            user,
            _asset,
            sourceVault,
            targetVaultId,
            targetVault,
            actualMigration,
        )
        assert targetShares != 0 # dev: invalid migration result
        extcall Lootbox(a.lootbox).updateDepositPoints(user, LEGACY_RIPE_GOV_VAULT_ID, sourceVault, _asset, a)
        extcall Lootbox(a.lootbox).updateDepositPoints(user, targetVaultId, targetVault, _asset, a)

        self._verifyLegacyRipeGovImport(
            user,
            _asset,
            sourceVault,
            targetVault,
            targetVaultId,
            actualMigration.amount,
            targetShares,
            snap,
            a,
        )

        log LegacyRipeGovPositionMigrationExecuted(
            user=user,
            asset=_asset,
            caller=_caller,
            amount=actualMigration.amount,
            targetShares=targetShares,
            govPoints=actualMigration.govPoints,
            unlock=actualMigration.unlock,
        )

    return len(_users)


@internal
def _migrateRipeGovPosition(
    _user: address,
    _asset: address,
    _sourceVaultId: uint256,
    _targetVaultId: uint256,
    _caller: address,
) -> uint256:
    a: addys.Addys = addys._getAddys()
    sourceVault: address = empty(address)
    targetVault: address = empty(address)
    sourceVault, targetVault = self._validateRipeGovMigration(
        _user,
        _asset,
        _sourceVaultId,
        _targetVaultId,
        a,
    )

    actualMigration: RipeGovMigrationData = empty(RipeGovMigrationData)
    targetShares: uint256 = 0
    targetBalanceBefore: uint256 = staticcall IERC20(_asset).balanceOf(targetVault)
    tellerBalanceBefore: uint256 = staticcall IERC20(_asset).balanceOf(a.teller)
    teller: Teller = Teller(a.teller)
    actualMigration = extcall teller.executeRipeGovSource(
        _user,
        _asset,
        sourceVault,
        targetVault,
        empty(RipeGovMigrationData),
        False,
    )
    assert actualMigration.amount != 0 # dev: invalid migration result
    self._verifyRipeGovSourceExecution(
        _user,
        _asset,
        sourceVault,
        targetVault,
        actualMigration.amount,
        targetBalanceBefore,
        tellerBalanceBefore,
    )
    targetShares = extcall teller.executeRipeGovImport(
        _user,
        _asset,
        sourceVault,
        _targetVaultId,
        targetVault,
        actualMigration,
    )
    assert targetShares != 0 # dev: invalid migration result
    extcall Lootbox(a.lootbox).updateDepositPoints(_user, _sourceVaultId, sourceVault, _asset, a)
    extcall Lootbox(a.lootbox).updateDepositPoints(_user, _targetVaultId, targetVault, _asset, a)

    log RipeGovPositionMigrationExecuted(
        user=_user,
        asset=_asset,
        caller=_caller,
        sourceVaultId=_sourceVaultId,
        targetVaultId=_targetVaultId,
        sourceVault=sourceVault,
        targetVault=targetVault,
        amount=actualMigration.amount,
        targetShares=targetShares,
        govPoints=actualMigration.govPoints,
        unlock=actualMigration.unlock,
    )
    return actualMigration.amount


@view
@internal
def _verifyRipeGovSourceExecution(
    _user: address,
    _asset: address,
    _sourceVault: address,
    _targetVault: address,
    _amount: uint256,
    _targetBalanceBefore: uint256,
    _tellerBalanceBefore: uint256,
):
    targetBalanceAfter: uint256 = staticcall IERC20(_asset).balanceOf(_targetVault)
    assert targetBalanceAfter >= _targetBalanceBefore # dev: invalid migration receipt
    assert targetBalanceAfter - _targetBalanceBefore == _amount # dev: inexact migration receipt
    assert staticcall IERC20(_asset).balanceOf(addys._getTellerAddr()) == _tellerBalanceBefore # dev: teller balance residue
    assert staticcall IERC20(_asset).allowance(addys._getTellerAddr(), _targetVault) == 0 # dev: teller allowance residue
    assert staticcall RipeGovVault(_sourceVault).userBalances(_user, _asset) == 0 # dev: source shares remain
    assert staticcall Vault(_sourceVault).getTotalAmountForUser(_user, _asset) == 0 # dev: source amount remains
    assert not staticcall Vault(_sourceVault).doesUserHaveBalance(_user, _asset) # dev: source balance remains


@view
@internal
def _validateRipeGovMigration(
    _user: address,
    _asset: address,
    _sourceVaultId: uint256,
    _targetVaultId: uint256,
    _a: addys.Addys,
) -> (address, address):
    assert empty(address) not in [_user, _asset] # dev: invalid user or asset
    assert _sourceVaultId != 0 and _targetVaultId != 0 # dev: invalid vault id
    assert _sourceVaultId != _targetVaultId # dev: same vault id

    vaultBook: AddressRegistry = AddressRegistry(_a.vaultBook)
    assert staticcall vaultBook.isValidRegId(_sourceVaultId) # dev: invalid source vault id
    assert staticcall vaultBook.isValidRegId(_targetVaultId) # dev: invalid target vault id
    assert staticcall MissionControl(_a.missionControl).isSupportedAssetInVault(_sourceVaultId, _asset) # dev: unsupported source asset
    assert staticcall MissionControl(_a.missionControl).isSupportedAssetInVault(_targetVaultId, _asset) # dev: unsupported target asset

    sourceVault: address = staticcall vaultBook.getAddr(_sourceVaultId)
    targetVault: address = staticcall vaultBook.getAddr(_targetVaultId)
    assert sourceVault != empty(address) and sourceVault.is_contract # dev: invalid source vault
    assert targetVault != empty(address) and targetVault.is_contract # dev: invalid target vault
    if LEGACY_RIPE_GOV_VAULT != empty(address):
        assert sourceVault != LEGACY_RIPE_GOV_VAULT # dev: use legacy migration route
    assert sourceVault != targetVault # dev: same vault
    assert staticcall Vault(sourceVault).isPaused() # dev: source vault not paused
    assert staticcall Vault(targetVault).isPaused() # dev: target vault not paused
    assert staticcall Ledger(_a.ledger).isParticipatingInVault(_user, _sourceVaultId) # dev: source vault missing from Ledger

    return sourceVault, targetVault


@view
@internal
def _validateLegacyRipeGovMigration(
    _user: address,
    _asset: address,
    _sourceVault: address,
    _targetVaultId: uint256,
    _targetVault: address,
    _a: addys.Addys,
):
    assert empty(address) not in [_user, _asset] # dev: invalid user or asset
    assert _targetVaultId != 0 and _targetVaultId != LEGACY_RIPE_GOV_VAULT_ID # dev: invalid target vault id
    assert _sourceVault != _targetVault # dev: same vault
    assert _sourceVault != empty(address) and _sourceVault.is_contract # dev: invalid source vault
    assert _targetVault != empty(address) and _targetVault.is_contract # dev: invalid target vault
    assert staticcall AddressRegistry(_a.vaultBook).getAddr(LEGACY_RIPE_GOV_VAULT_ID) == _sourceVault # dev: source vault not registered
    assert staticcall AddressRegistry(_a.vaultBook).getAddr(_targetVaultId) == _targetVault # dev: target vault not registered
    assert not staticcall Vault(_sourceVault).isPaused() # dev: source vault paused
    assert staticcall Vault(_targetVault).isPaused() # dev: target vault not in migration state

    self._assertExclusiveFreeze(_a)

    mc: MissionControl = MissionControl(_a.missionControl)
    assert staticcall mc.isSupportedAssetInVault(LEGACY_RIPE_GOV_VAULT_ID, _asset) # dev: unsupported source asset
    assert staticcall mc.isSupportedAssetInVault(_targetVaultId, _asset) # dev: unsupported target asset
    assert staticcall Vault(_sourceVault).isUserInVaultAsset(_user, _asset) # dev: source asset not registered
    assert staticcall Vault(_sourceVault).doesUserHaveBalance(_user, _asset) # dev: no source balance
    assert staticcall Ledger(_a.ledger).isParticipatingInVault(_user, LEGACY_RIPE_GOV_VAULT_ID) # dev: source vault missing from Ledger
    assert not staticcall Vault(_targetVault).doesUserHaveBalance(_user, _asset) # dev: target position exists


@view
@internal
def _getLegacyRipeGovSourceSnapshot(
    _user: address,
    _asset: address,
    _sourceVault: address,
    _targetVault: address,
    _a: addys.Addys,
) -> LegacySourceSnapshot:
    gd: GovData = staticcall RipeGovVault(_sourceVault).userGovData(_user, _asset)
    config: cs.RipeGovVaultConfig = staticcall MissionControl(_a.missionControl).ripeGovVaultConfig(_asset)
    sourceShares: uint256 = staticcall RipeGovVault(_sourceVault).userBalances(_user, _asset)
    sourceAmount: uint256 = staticcall Vault(_sourceVault).getTotalAmountForUser(_user, _asset)
    assert sourceShares != 0 and sourceAmount != 0 # dev: no source position

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
@internal
def _verifyLegacyRipeGovImport(
    _user: address,
    _asset: address,
    _sourceVault: address,
    _targetVault: address,
    _targetVaultId: uint256,
    _amount: uint256,
    _targetShares: uint256,
    _snapshot: LegacySourceSnapshot,
    _a: addys.Addys,
):
    assert staticcall RipeGovVault(_sourceVault).userBalances(_user, _asset) == 0 # dev: source shares remain
    assert staticcall Vault(_sourceVault).getTotalAmountForUser(_user, _asset) == 0 # dev: source amount remains
    assert not staticcall Vault(_sourceVault).doesUserHaveBalance(_user, _asset) # dev: source balance remains
    assert staticcall Vault(_sourceVault).isUserInVaultAsset(_user, _asset) # dev: source asset deregistered
    assert staticcall Ledger(_a.ledger).isParticipatingInVault(_user, LEGACY_RIPE_GOV_VAULT_ID) # dev: source ledger removed

    assert _amount != 0 and _targetShares != 0 # dev: invalid migration result
    assert staticcall RipeGovVault(_targetVault).userBalances(_user, _asset) == _targetShares # dev: target shares mismatch
    assert staticcall Vault(_targetVault).isUserInVaultAsset(_user, _asset) # dev: target asset not registered
    assert staticcall Vault(_targetVault).doesUserHaveBalance(_user, _asset) # dev: target position missing
    assert staticcall Ledger(_a.ledger).isParticipatingInVault(_user, _targetVaultId) # dev: target ledger missing

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
    assert staticcall RipeGovVault(_targetVault).totalUserGovPoints(_user) == _snapshot.targetUserPointsBefore + _snapshot.govPoints # dev: target user total mismatch
    assert staticcall RipeGovVault(_targetVault).totalGovPoints() == _snapshot.targetTotalPointsBefore + _snapshot.govPoints # dev: target global total mismatch


@view
@internal
def _validateVaultMigration(
    _user: address,
    _asset: address,
    _sourceVaultId: uint256,
    _targetVaultId: uint256,
    _a: addys.Addys,
) -> (address, address):
    assert empty(address) not in [_user, _asset] # dev: invalid user or asset
    assert _sourceVaultId != 0 and _targetVaultId != 0 # dev: invalid vault id
    assert _sourceVaultId != _targetVaultId # dev: same vault

    vaultBook: AddressRegistry = AddressRegistry(_a.vaultBook)
    assert staticcall vaultBook.isValidRegId(_sourceVaultId) # dev: invalid source vault id
    assert staticcall vaultBook.isValidRegId(_targetVaultId) # dev: invalid target vault id

    mc: MissionControl = MissionControl(_a.missionControl)
    assert staticcall mc.isSupportedAssetInVault(_sourceVaultId, _asset) # dev: unsupported source asset
    assert staticcall mc.isSupportedAssetInVault(_targetVaultId, _asset) # dev: unsupported target asset

    sourceVault: address = staticcall vaultBook.getAddr(_sourceVaultId)
    targetVault: address = staticcall vaultBook.getAddr(_targetVaultId)
    assert sourceVault != empty(address) and sourceVault.is_contract # dev: invalid source vault
    assert targetVault != empty(address) and targetVault.is_contract # dev: invalid target vault
    assert sourceVault != targetVault # dev: same vault
    assert not staticcall Vault(sourceVault).isPaused() # dev: source vault paused
    assert not staticcall Vault(targetVault).isPaused() # dev: target vault paused
    assert staticcall Ledger(_a.ledger).isParticipatingInVault(_user, _sourceVaultId) # dev: source vault missing from Ledger

    coreRipeGovVaultId: uint256 = staticcall mc.coreRipeGovVaultId()
    assert coreRipeGovVaultId != 0 # dev: invalid core ripe gov vault id
    assert _sourceVaultId != coreRipeGovVaultId # dev: source is core ripe gov
    assert _targetVaultId != coreRipeGovVaultId # dev: target is core ripe gov
    assert staticcall mc.isStabVaultId(_sourceVaultId) == staticcall mc.isStabVaultId(_targetVaultId) # dev: stab vault mismatch

    return sourceVault, targetVault
