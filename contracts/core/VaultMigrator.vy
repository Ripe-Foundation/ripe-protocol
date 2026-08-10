# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

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

interface Teller:
    def importPositionForMigration(_user: address, _asset: address, _sourceVault: address, _targetVaultId: uint256, _targetVault: address, _migration: RipeGovMigrationData, _ledger: address) -> uint256: nonpayable
    def depositOnVaultMigration(_user: address, _asset: address, _amount: uint256, _targetVaultId: uint256, _targetVault: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def exportPositionForLegacyRipeGovMigration(_user: address, _asset: address, _sourceVault: address, _targetVault: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def exportPositionForMigration(_user: address, _asset: address, _sourceVault: address, _targetVault: address, _a: addys.Addys = empty(addys.Addys)) -> RipeGovMigrationData: nonpayable
    def performHousekeeping(_isHigherRisk: bool, _user: address, _shouldUpdateDebt: bool, _a: addys.Addys = empty(addys.Addys)): nonpayable
    def withdrawOnVaultMigration(_user: address, _asset: address, _sourceVault: address, _a: addys.Addys = empty(addys.Addys)) -> (uint256, bool): nonpayable

interface RipeGovVault:
    def getLatestGovPoints(_lastShares: uint256, _lastPointsUpdate: uint256, _unlock: uint256, _terms: cs.LockTerms, _weight: uint256) -> uint256: view
    def userGovData(_user: address, _asset: address) -> GovData: view
    def userBalances(_user: address, _asset: address) -> uint256: view
    def totalUserGovPoints(_user: address) -> uint256: view
    def totalGovPoints() -> uint256: view

interface MissionControl:
    def isSupportedAssetInVault(_vaultId: uint256, _asset: address) -> bool: view
    def ripeGovVaultConfig(_asset: address) -> cs.RipeGovVaultConfig: view
    def isStabVaultId(_vaultId: uint256) -> bool: view
    def coreRipeGovVaultId() -> uint256: view

interface AddressRegistry:
    def isValidRegId(_regId: uint256) -> bool: view
    def getAddr(_regId: uint256) -> address: view

interface Lootbox:
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address, _a: addys.Addys = empty(addys.Addys)): nonpayable

interface Ledger:
    def isParticipatingInVault(_user: address, _vaultId: uint256) -> bool: view

struct GovData:
    govPoints: uint256
    lastShares: uint256
    lastPointsUpdate: uint256
    unlock: uint256
    lastTerms: cs.LockTerms

struct PrevSourceSnapshot:
    sourceShares: uint256
    sourceAmount: uint256
    govPoints: uint256
    unlock: uint256
    lastTerms: cs.LockTerms

struct LegacyMigrationPosition:
    asset: address
    sourceSnapshot: PrevSourceSnapshot

struct RipeGovMigrationData:
    amount: uint256
    govPoints: uint256
    unlock: uint256
    lastTerms: cs.LockTerms

event RipeGovPositionMigrationExecuted:
    user: indexed(address)
    asset: indexed(address)
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
    sourceVaultId: uint256
    targetVaultId: uint256
    amount: uint256

event LegacyRipeGovPositionMigrationExecuted:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    targetShares: uint256
    govPoints: uint256
    unlock: uint256

MAX_MIGRATION_USERS: constant(uint256) = 25
MAX_USER_ASSETS: constant(uint256) = 20
MAX_GOV_USER_ASSETS: constant(uint256) = 5
BASE_CHAIN_ID: constant(uint256) = 8453
LEGACY_RIPE_GOV_VAULT_ID: constant(uint256) = 2
LEGACY_RIPE_GOV_VAULT: immutable(address)


@deploy
def __init__(_ripeHq: address, _shouldPause: bool, _legacyRipeGovVault: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(_shouldPause, False, False) # no minting
    LEGACY_RIPE_GOV_VAULT = _legacyRipeGovVault


##########################
# Basic Vault Migrations #
##########################


@external
def migrateVaultPositions(_users: DynArray[address, MAX_MIGRATION_USERS], _sourceVaultId: uint256, _targetVaultId: uint256) -> uint256:
    assert addys._isSwitchboardAddr(msg.sender) # dev: only switchboard allowed
    assert not deptBasics.isPaused # dev: contract paused
    assert len(_users) != 0 # dev: no migrations

    a: addys.Addys = addys._getAddys()

    # validate migration route
    sourceVault: address = empty(address)
    targetVault: address = empty(address)
    sourceVault, targetVault = self._validateMigrationRoute(_sourceVaultId, _targetVaultId, a.vaultBook, a.missionControl)

    # both must NOT be paused
    assert not staticcall Vault(sourceVault).isPaused() # dev: source vault paused
    assert not staticcall Vault(targetVault).isPaused() # dev: target vault paused

    # source and target must not be the core ripe gov vault
    coreRipeGovVaultId: uint256 = staticcall MissionControl(a.missionControl).coreRipeGovVaultId()
    assert _sourceVaultId != coreRipeGovVaultId # dev: source is core ripe gov
    assert _targetVaultId != coreRipeGovVaultId # dev: target is core ripe gov

    numPositions: uint256 = 0
    for user: address in _users:
        if user == empty(address):
            continue

        numPositionsBefore: uint256 = numPositions
        numUserAssets: uint256 = staticcall Vault(sourceVault).numUserAssets(user)
        for i: uint256 in range(1, numUserAssets, bound=MAX_USER_ASSETS):

            # get user asset and amount
            asset: address = empty(address)
            hasBalance: bool = False
            asset, hasBalance = staticcall Vault(sourceVault).getUserAssetAtIndexAndHasBalance(user, i)
            if not hasBalance or asset == empty(address):
                continue

            # validate target asset
            if not staticcall MissionControl(a.missionControl).isSupportedAssetInVault(_targetVaultId, asset):
                continue

            # check pre-migration balances
            tellerBalanceBefore: uint256 = staticcall IERC20(asset).balanceOf(a.teller)
            sourceVaultBalanceBefore: uint256 = staticcall IERC20(asset).balanceOf(sourceVault)
            targetVaultBalanceBefore: uint256 = staticcall IERC20(asset).balanceOf(targetVault)

            # execute withdrawal
            amount: uint256 = 0
            isDepleted: bool = False
            amount, isDepleted = extcall Teller(a.teller).withdrawOnVaultMigration(user, asset, sourceVault, a)
            assert isDepleted # dev: source position not depleted
            assert amount != 0 # dev: invalid migration amount

            # check post-withdrawal teller balance
            tellerBalanceMid: uint256 = staticcall IERC20(asset).balanceOf(a.teller)
            assert tellerBalanceMid > tellerBalanceBefore # dev: invalid migration receipt
            assert tellerBalanceMid - tellerBalanceBefore == amount # dev: inexact migration receipt
            assert not staticcall Vault(sourceVault).doesUserHaveBalance(user, asset) # dev: source balance remains

            # execute deposit
            deposited: uint256 = extcall Teller(a.teller).depositOnVaultMigration(user, asset, amount, _targetVaultId, targetVault, a)
            assert deposited == amount # dev: inexact migration deposit

            # check post-deposit balances
            assert staticcall IERC20(asset).balanceOf(a.teller) == tellerBalanceBefore # dev: teller balance remains
            assert staticcall IERC20(asset).balanceOf(sourceVault) == sourceVaultBalanceBefore - amount # dev: source vault balance remains
            assert staticcall IERC20(asset).balanceOf(targetVault) == targetVaultBalanceBefore + amount # dev: target vault balance remains

            # update lootbox deposit points
            extcall Lootbox(a.lootbox).updateDepositPoints(user, _sourceVaultId, sourceVault, asset, a)
            numPositions += 1

            log VaultPositionMigrationExecuted(
                user=user,
                asset=asset,
                sourceVaultId=_sourceVaultId,
                targetVaultId=_targetVaultId,
                amount=amount,
            )

        # perform house keeping
        if numPositions > numPositionsBefore:
            extcall Teller(a.teller).performHousekeeping(True, user, True, a)

    return numPositions


#######################
# Ripe Gov Migrations #
#######################


@external
def migrateRipeGovPositions(_users: DynArray[address, MAX_MIGRATION_USERS], _sourceVaultId: uint256) -> uint256:
    assert addys._isSwitchboardAddr(msg.sender) # dev: only switchboard allowed
    assert not deptBasics.isPaused # dev: contract paused
    assert len(_users) != 0 # dev: no migrations

    a: addys.Addys = addys._getAddys()
    targetVaultId: uint256 = staticcall MissionControl(a.missionControl).coreRipeGovVaultId()

    # validate migration route
    sourceVault: address = empty(address)
    targetVault: address = empty(address)
    sourceVault, targetVault = self._validateMigrationRoute(_sourceVaultId, targetVaultId, a.vaultBook, a.missionControl)

    # both must be paused
    assert staticcall Vault(sourceVault).isPaused() # dev: source vault not paused
    assert staticcall Vault(targetVault).isPaused() # dev: target vault not paused

    numPositions: uint256 = 0

    for user: address in _users:
        if user == empty(address):
            continue

        numPositionsBefore: uint256 = numPositions
        numUserAssets: uint256 = staticcall Vault(sourceVault).numUserAssets(user)
        for i: uint256 in range(1, numUserAssets, bound=MAX_GOV_USER_ASSETS):

            # get user asset and amount
            asset: address = empty(address)
            hasBalance: bool = False
            asset, hasBalance = staticcall Vault(sourceVault).getUserAssetAtIndexAndHasBalance(user, i)
            if not hasBalance or asset == empty(address):
                continue

            # validate target asset
            if not staticcall MissionControl(a.missionControl).isSupportedAssetInVault(targetVaultId, asset):
                continue

            # check pre-migration balances
            tellerBalanceBefore: uint256 = staticcall IERC20(asset).balanceOf(a.teller)
            sourceVaultBalanceBefore: uint256 = staticcall IERC20(asset).balanceOf(sourceVault)
            targetVaultBalanceBefore: uint256 = staticcall IERC20(asset).balanceOf(targetVault)

            # check pre-migration gov data
            targetUserPointsBefore: uint256 = staticcall RipeGovVault(targetVault).totalUserGovPoints(user)
            targetTotalPointsBefore: uint256 = staticcall RipeGovVault(targetVault).totalGovPoints()

            # export position from source vault
            migData: RipeGovMigrationData = extcall Teller(a.teller).exportPositionForMigration(user, asset, sourceVault, targetVault, a)
            assert migData.amount != 0 # dev: invalid migration result
            self._verifyRipeGovExport(user, asset, sourceVault, targetVault, migData.amount, tellerBalanceBefore, sourceVaultBalanceBefore, targetVaultBalanceBefore, a.teller)

            # import position to target vault
            targetShares: uint256 = extcall Teller(a.teller).importPositionForMigration(user, asset, sourceVault, targetVaultId, targetVault, migData, a.ledger)
            assert targetShares != 0 # dev: invalid migration result

            # update lootbox deposit points
            extcall Lootbox(a.lootbox).updateDepositPoints(user, _sourceVaultId, sourceVault, asset, a)
            extcall Lootbox(a.lootbox).updateDepositPoints(user, targetVaultId, targetVault, asset, a)

            # verify migration
            self._verifyRipeGovImport(user, asset, targetVault, targetVaultId, targetShares, migData, targetUserPointsBefore, targetTotalPointsBefore, a.ledger)
            numPositions += 1

            log RipeGovPositionMigrationExecuted(
                user=user,
                asset=asset,
                sourceVaultId=_sourceVaultId,
                targetVaultId=targetVaultId,
                sourceVault=sourceVault,
                targetVault=targetVault,
                amount=migData.amount,
                targetShares=targetShares,
                govPoints=migData.govPoints,
                unlock=migData.unlock,
            )

        # perform house keeping
        if numPositions > numPositionsBefore:
            extcall Teller(a.teller).performHousekeeping(True, user, True, a)

    return numPositions


# legacy ripe gov migration (Base chain only)


@external
def migrateLegacyRipeGovPositions(_users: DynArray[address, MAX_MIGRATION_USERS]) -> uint256:
    assert addys._isSwitchboardAddr(msg.sender) # dev: only switchboard allowed
    assert not deptBasics.isPaused # dev: contract paused
    assert len(_users) != 0 # dev: no migrations
    assert chain.id == BASE_CHAIN_ID and LEGACY_RIPE_GOV_VAULT != empty(address) # dev: legacy migration disabled

    a: addys.Addys = addys._getAddys()
    targetVaultId: uint256 = staticcall MissionControl(a.missionControl).coreRipeGovVaultId()

    # validate migration route
    sourceVault: address = empty(address)
    targetVault: address = empty(address)
    sourceVault, targetVault = self._validateMigrationRoute(LEGACY_RIPE_GOV_VAULT_ID, targetVaultId, a.vaultBook, a.missionControl)
    assert sourceVault == LEGACY_RIPE_GOV_VAULT # dev: invalid legacy vault

    # source must NOT be paused, target must be paused
    assert not staticcall Vault(sourceVault).isPaused() # dev: source vault paused
    assert staticcall Vault(targetVault).isPaused() # dev: target vault not paused

    numPositions: uint256 = 0
    for user: address in _users:
        if user == empty(address):
            continue

        numPositionsBefore: uint256 = numPositions

        # snapshot all supported positions before the first legacy withdrawal
        positions: DynArray[LegacyMigrationPosition, MAX_GOV_USER_ASSETS] = []
        numUserAssets: uint256 = staticcall Vault(sourceVault).numUserAssets(user)
        for i: uint256 in range(1, numUserAssets, bound=MAX_GOV_USER_ASSETS):

            # get user asset
            asset: address = empty(address)
            hasBalance: bool = False
            asset, hasBalance = staticcall Vault(sourceVault).getUserAssetAtIndexAndHasBalance(user, i)
            if not hasBalance or asset == empty(address):
                continue

            # validate target asset
            if not staticcall MissionControl(a.missionControl).isSupportedAssetInVault(targetVaultId, asset):
                continue

            positions.append(LegacyMigrationPosition(
                asset=asset,
                sourceSnapshot=self._getPreMigrationData(user, asset, sourceVault, a.missionControl),
            ))

        # migrate from the saved pre-withdrawal snapshots
        for p: LegacyMigrationPosition in positions:
            asset: address = p.asset
            prevSnapShot: PrevSourceSnapshot = p.sourceSnapshot

            # check pre-migration balances
            tellerBalanceBefore: uint256 = staticcall IERC20(asset).balanceOf(a.teller)
            sourceVaultBalanceBefore: uint256 = staticcall IERC20(asset).balanceOf(sourceVault)
            targetVaultBalanceBefore: uint256 = staticcall IERC20(asset).balanceOf(targetVault)

            # check pre-migration gov data
            targetUserPointsBefore: uint256 = staticcall RipeGovVault(targetVault).totalUserGovPoints(user)
            targetTotalPointsBefore: uint256 = staticcall RipeGovVault(targetVault).totalGovPoints()

            migData: RipeGovMigrationData = RipeGovMigrationData(
                amount=prevSnapShot.sourceAmount,
                govPoints=prevSnapShot.govPoints,
                unlock=prevSnapShot.unlock,
                lastTerms=prevSnapShot.lastTerms,
            )

            # export position from source vault
            amount: uint256 = extcall Teller(a.teller).exportPositionForLegacyRipeGovMigration(user, asset, sourceVault, targetVault, a)
            assert amount == migData.amount # dev: migration amount mismatch
            self._verifyRipeGovExport(user, asset, sourceVault, targetVault, amount, tellerBalanceBefore, sourceVaultBalanceBefore, targetVaultBalanceBefore, a.teller)

            # import position to target vault
            targetShares: uint256 = extcall Teller(a.teller).importPositionForMigration(user, asset, sourceVault, targetVaultId, targetVault, migData, a.ledger)
            assert targetShares != 0 # dev: invalid migration result

            # update lootbox deposit points
            extcall Lootbox(a.lootbox).updateDepositPoints(user, LEGACY_RIPE_GOV_VAULT_ID, sourceVault, asset, a)
            extcall Lootbox(a.lootbox).updateDepositPoints(user, targetVaultId, targetVault, asset, a)

            # verify migration
            self._verifyRipeGovImport(user, asset, targetVault, targetVaultId, targetShares, migData, targetUserPointsBefore, targetTotalPointsBefore, a.ledger)
            numPositions += 1

            log LegacyRipeGovPositionMigrationExecuted(
                user=user,
                asset=asset,
                amount=migData.amount,
                targetShares=targetShares,
                govPoints=migData.govPoints,
                unlock=migData.unlock,
            )

        # perform house keeping
        if numPositions > numPositionsBefore:
            extcall Teller(a.teller).performHousekeeping(True, user, True, a)

    return numPositions


####################
# Validation Utils #
####################


# migration route validation


@view
@internal
def _validateMigrationRoute(
    _sourceVaultId: uint256,
    _targetVaultId: uint256,
    _vaultBook: address,
    _missionControl: address,
) -> (address, address):
    assert _sourceVaultId != 0 and _targetVaultId != 0 # dev: invalid vault id
    assert _sourceVaultId != _targetVaultId # dev: same vault

    # validate source vault
    assert staticcall AddressRegistry(_vaultBook).isValidRegId(_sourceVaultId) # dev: invalid source vault id
    sourceVault: address = staticcall AddressRegistry(_vaultBook).getAddr(_sourceVaultId)
    assert sourceVault != empty(address) and sourceVault.is_contract # dev: invalid source vault

    # validate target vault
    assert staticcall AddressRegistry(_vaultBook).isValidRegId(_targetVaultId) # dev: invalid target vault id
    targetVault: address = staticcall AddressRegistry(_vaultBook).getAddr(_targetVaultId)
    assert targetVault != empty(address) and targetVault.is_contract # dev: invalid target vault

    assert sourceVault != targetVault # dev: same vault
    assert staticcall MissionControl(_missionControl).isStabVaultId(_sourceVaultId) == staticcall MissionControl(_missionControl).isStabVaultId(_targetVaultId) # dev: stab vault mismatch
    return sourceVault, targetVault


# get pre-migration data


@view
@internal
def _getPreMigrationData(
    _user: address,
    _asset: address,
    _sourceVault: address,
    _mc: address
) -> PrevSourceSnapshot:

    # user data
    gd: GovData = staticcall RipeGovVault(_sourceVault).userGovData(_user, _asset)
    sourceShares: uint256 = staticcall RipeGovVault(_sourceVault).userBalances(_user, _asset)
    sourceAmount: uint256 = staticcall Vault(_sourceVault).getTotalAmountForUser(_user, _asset)
    assert sourceShares != 0 and sourceAmount != 0 # dev: no source position

    config: cs.RipeGovVaultConfig = staticcall MissionControl(_mc).ripeGovVaultConfig(_asset)
    pending: uint256 = staticcall RipeGovVault(_sourceVault).getLatestGovPoints(
        gd.lastShares,
        gd.lastPointsUpdate,
        gd.unlock,
        gd.lastTerms,
        config.assetWeight,
    )

    return PrevSourceSnapshot(
        sourceShares=sourceShares,
        sourceAmount=sourceAmount,
        govPoints=gd.govPoints + pending,
        unlock=gd.unlock,
        lastTerms=gd.lastTerms,
    )


# after export from source vault


@view
@internal
def _verifyRipeGovExport(
    _user: address,
    _asset: address,
    _sourceVault: address,
    _targetVault: address,
    _amount: uint256,
    _tellerBalanceBefore: uint256,
    _sourceVaultBalanceBefore: uint256,
    _targetVaultBalanceBefore: uint256,
    _teller: address,
):
    # verify target position
    targetVaultBalanceAfter: uint256 = staticcall IERC20(_asset).balanceOf(_targetVault)
    assert targetVaultBalanceAfter > _targetVaultBalanceBefore # dev: invalid migration receipt
    assert targetVaultBalanceAfter - _targetVaultBalanceBefore == _amount # dev: inexact migration receipt

    # verify teller
    assert staticcall IERC20(_asset).balanceOf(_teller) == _tellerBalanceBefore # dev: teller balance residue
    assert staticcall IERC20(_asset).allowance(_teller, _targetVault) == 0 # dev: teller allowance residue

    # verify source vault
    assert staticcall IERC20(_asset).balanceOf(_sourceVault) == _sourceVaultBalanceBefore - _amount # dev: source vault balance remains

    # verify source position
    assert staticcall RipeGovVault(_sourceVault).userBalances(_user, _asset) == 0 # dev: source shares remain
    assert staticcall Vault(_sourceVault).getTotalAmountForUser(_user, _asset) == 0 # dev: source amount remains
    assert not staticcall Vault(_sourceVault).doesUserHaveBalance(_user, _asset) # dev: source balance remains



# after import to target vault


@view
@internal
def _verifyRipeGovImport(
    _user: address,
    _asset: address,
    _targetVault: address,
    _targetVaultId: uint256,
    _targetShares: uint256,
    _migration: RipeGovMigrationData,
    _targetUserPointsBefore: uint256,
    _targetTotalPointsBefore: uint256,
    _ledger: address,
):
    assert _migration.amount != 0 and _targetShares != 0 # dev: invalid migration result

    # verify target position
    assert staticcall RipeGovVault(_targetVault).userBalances(_user, _asset) == _targetShares # dev: target shares mismatch
    assert staticcall Vault(_targetVault).isUserInVaultAsset(_user, _asset) # dev: target asset not registered
    assert staticcall Vault(_targetVault).doesUserHaveBalance(_user, _asset) # dev: target position missing
    assert staticcall Ledger(_ledger).isParticipatingInVault(_user, _targetVaultId) # dev: target ledger missing

    # verify target gov data
    newGd: GovData = staticcall RipeGovVault(_targetVault).userGovData(_user, _asset)
    assert newGd.govPoints == _migration.govPoints # dev: target points mismatch
    assert newGd.lastShares == _targetShares # dev: target last shares mismatch
    assert newGd.lastPointsUpdate == block.number # dev: target last update mismatch
    assert newGd.unlock == _migration.unlock # dev: target unlock mismatch

    # last terms
    assert newGd.lastTerms.minLockDuration == _migration.lastTerms.minLockDuration # dev: target terms mismatch
    assert newGd.lastTerms.maxLockDuration == _migration.lastTerms.maxLockDuration # dev: target terms mismatch
    assert newGd.lastTerms.maxLockBoost == _migration.lastTerms.maxLockBoost # dev: target terms mismatch
    assert newGd.lastTerms.canExit == _migration.lastTerms.canExit # dev: target terms mismatch
    assert newGd.lastTerms.exitFee == _migration.lastTerms.exitFee # dev: target terms mismatch

    # gov points
    assert staticcall RipeGovVault(_targetVault).totalUserGovPoints(_user) == _targetUserPointsBefore + _migration.govPoints # dev: target user total mismatch
    assert staticcall RipeGovVault(_targetVault).totalGovPoints() == _targetTotalPointsBefore + _migration.govPoints # dev: target global total mismatch
