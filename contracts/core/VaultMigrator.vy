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
    def importPositionForMigration(_user: address, _asset: address, _sourceVault: address, _targetVaultId: uint256, _targetVault: address, _migration: RipeGovMigrationData, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def depositOnVaultMigration(_user: address, _asset: address, _amount: uint256, _targetVaultId: uint256, _targetVault: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def exportPositionForLegacyRipeGovMigration(_user: address, _asset: address, _sourceVault: address, _targetVault: address, _a: addys.Addys = empty(addys.Addys)) -> uint256: nonpayable
    def exportPositionForMigration(_user: address, _asset: address, _sourceVault: address, _targetVault: address, _a: addys.Addys = empty(addys.Addys)) -> RipeGovMigrationData: nonpayable
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

MAX_RIPE_GOV_MIGRATIONS: constant(uint256) = 25
MAX_VAULT_MIGRATIONS: constant(uint256) = 25
BASE_CHAIN_ID: constant(uint256) = 8453
LEGACY_RIPE_GOV_VAULT_ID: constant(uint256) = 2
LEGACY_RIPE_GOV_VAULT: immutable(address)

legacyMigrationUserDedupe: transient(HashMap[address, bool])


@deploy
def __init__(_ripeHq: address, _shouldPause: bool, _legacyRipeGovVault: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(_shouldPause, False, False) # no minting
    LEGACY_RIPE_GOV_VAULT = _legacyRipeGovVault


##########################
# Basic Vault Migrations #
##########################


@external
def migrateVaultPositions(_migrations: DynArray[VaultMigration, MAX_VAULT_MIGRATIONS]) -> uint256:
    assert addys._isSwitchboardAddr(msg.sender) # dev: only switchboard allowed
    assert not deptBasics.isPaused # dev: contract paused
    assert len(_migrations) != 0 # dev: no migrations

    a: addys.Addys = addys._getAddys()
    coreRipeGovVaultId: uint256 = staticcall MissionControl(a.missionControl).coreRipeGovVaultId()

    for m: VaultMigration in _migrations:

        # validate migration
        sourceVault: address = empty(address)
        targetVault: address = empty(address)
        sourceVault, targetVault = self._validateVaultMigration(m.user, m.asset, m.sourceVaultId, m.targetVaultId, a)

        # both must NOT be paused
        assert not staticcall Vault(sourceVault).isPaused() # dev: source vault paused
        assert not staticcall Vault(targetVault).isPaused() # dev: target vault paused

        # source and target must not be the core ripe gov vault
        assert m.sourceVaultId != coreRipeGovVaultId # dev: source is core ripe gov
        assert m.targetVaultId != coreRipeGovVaultId # dev: target is core ripe gov
        
        # check pre-migration teller balance
        tellerBalanceBefore: uint256 = staticcall IERC20(m.asset).balanceOf(a.teller)

        # execute withdrawal
        amount: uint256 = 0
        isDepleted: bool = False
        amount, isDepleted = extcall Teller(a.teller).withdrawOnVaultMigration(m.user, m.asset, sourceVault, a)
        assert isDepleted # dev: source position not depleted
        assert amount != 0 # dev: invalid migration amount

        # check post-withdrawal teller balance
        tellerBalanceAfter: uint256 = staticcall IERC20(m.asset).balanceOf(a.teller)
        assert tellerBalanceAfter > tellerBalanceBefore # dev: invalid migration receipt
        assert tellerBalanceAfter - tellerBalanceBefore == amount # dev: inexact migration receipt
        assert not staticcall Vault(sourceVault).doesUserHaveBalance(m.user, m.asset) # dev: source balance remains

        # execute deposit
        deposited: uint256 = extcall Teller(a.teller).depositOnVaultMigration(m.user, m.asset, amount, m.targetVaultId, targetVault, a)
        assert deposited == amount # dev: inexact migration deposit
        assert staticcall IERC20(m.asset).balanceOf(a.teller) == tellerBalanceBefore # dev: teller balance remains

        # update lootbox deposit points
        extcall Lootbox(a.lootbox).updateDepositPoints(m.user, m.sourceVaultId, sourceVault, m.asset, a)

        log VaultPositionMigrationExecuted(
            user=m.user,
            asset=m.asset,
            sourceVaultId=m.sourceVaultId,
            targetVaultId=m.targetVaultId,
            amount=amount,
        )

    return len(_migrations)


# validation


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
    assert staticcall Ledger(_a.ledger).isParticipatingInVault(_user, _sourceVaultId) # dev: source vault missing from Ledger

    vaultBook: AddressRegistry = AddressRegistry(_a.vaultBook)
    assert staticcall vaultBook.isValidRegId(_sourceVaultId) # dev: invalid source vault id
    assert staticcall vaultBook.isValidRegId(_targetVaultId) # dev: invalid target vault id

    mc: MissionControl = MissionControl(_a.missionControl)
    assert staticcall mc.isSupportedAssetInVault(_sourceVaultId, _asset) # dev: unsupported source asset
    assert staticcall mc.isSupportedAssetInVault(_targetVaultId, _asset) # dev: unsupported target asset

    # validate source vault
    sourceVault: address = staticcall vaultBook.getAddr(_sourceVaultId)
    assert sourceVault != empty(address) and sourceVault.is_contract # dev: invalid source vault

    # validate target vault
    targetVault: address = staticcall vaultBook.getAddr(_targetVaultId)
    assert targetVault != empty(address) and targetVault.is_contract # dev: invalid target vault
    assert sourceVault != targetVault # dev: same vault

    # validate core ripe gov vault id
    assert staticcall mc.isStabVaultId(_sourceVaultId) == staticcall mc.isStabVaultId(_targetVaultId) # dev: stab vault mismatch

    return sourceVault, targetVault


#######################
# Ripe Gov Migrations #
#######################


@external
def migrateRipeGovPositions(_migrations: DynArray[RipeGovMigration, MAX_RIPE_GOV_MIGRATIONS]) -> uint256:
    assert addys._isSwitchboardAddr(msg.sender) # dev: only switchboard allowed
    assert not deptBasics.isPaused # dev: contract paused
    assert len(_migrations) != 0 # dev: no migrations

    a: addys.Addys = addys._getAddys()
    coreRipeGovVaultId: uint256 = staticcall MissionControl(a.missionControl).coreRipeGovVaultId()

    for m: RipeGovMigration in _migrations:

        # validate migration
        sourceVault: address = empty(address)
        targetVault: address = empty(address)
        sourceVault, targetVault = self._validateVaultMigration(m.user, m.asset, m.sourceVaultId, m.targetVaultId, a)

        # both must be paused
        assert staticcall Vault(sourceVault).isPaused() # dev: source vault not paused
        assert staticcall Vault(targetVault).isPaused() # dev: target vault not paused
        assert m.targetVaultId == coreRipeGovVaultId # dev: target is not core ripe gov

        # check pre-migration balances
        targetBalanceBefore: uint256 = staticcall IERC20(m.asset).balanceOf(targetVault)
        tellerBalanceBefore: uint256 = staticcall IERC20(m.asset).balanceOf(a.teller)

        # get source snapshot
        prevSnapShot: PrevSourceSnapshot = self._getPreMigrationData(m.user, m.asset, sourceVault, targetVault, a.missionControl)

        # export position from source vault
        migData: RipeGovMigrationData = extcall Teller(a.teller).exportPositionForMigration(m.user, m.asset, sourceVault, targetVault, a)
        assert migData.amount != 0 # dev: invalid migration result
        self._verifyRipeGovExport(m.user, m.asset, sourceVault, targetVault, migData.amount, targetBalanceBefore, tellerBalanceBefore, a.teller)

        # import position to target vault
        targetShares: uint256 = extcall Teller(a.teller).importPositionForMigration(m.user, m.asset, sourceVault, m.targetVaultId, targetVault, migData, a)
        assert targetShares != 0 # dev: invalid migration result

        # update lootbox deposit points
        extcall Lootbox(a.lootbox).updateDepositPoints(m.user, m.sourceVaultId, sourceVault, m.asset, a)
        extcall Lootbox(a.lootbox).updateDepositPoints(m.user, m.targetVaultId, targetVault, m.asset, a)

        # verify migration
        self._verifyRipeGovImport(m.user, m.asset, targetVault, m.targetVaultId, migData.amount, targetShares, prevSnapShot, a.ledger)

        log RipeGovPositionMigrationExecuted(
            user=m.user,
            asset=m.asset,
            sourceVaultId=m.sourceVaultId,
            targetVaultId=m.targetVaultId,
            sourceVault=sourceVault,
            targetVault=targetVault,
            amount=migData.amount,
            targetShares=targetShares,
            govPoints=migData.govPoints,
            unlock=migData.unlock,
        )

    return len(_migrations)


# legacy ripe gov migration (Base chain only)


@external
def migrateLegacyRipeGovPositions(_users: DynArray[address, MAX_RIPE_GOV_MIGRATIONS], _asset: address) -> uint256:
    assert addys._isSwitchboardAddr(msg.sender) # dev: only switchboard allowed
    assert not deptBasics.isPaused # dev: contract paused
    assert len(_users) != 0 # dev: no migrations
    assert _asset != empty(address) # dev: invalid asset
    assert chain.id == BASE_CHAIN_ID and LEGACY_RIPE_GOV_VAULT != empty(address) # dev: legacy migration disabled

    a: addys.Addys = addys._getAddys()
    targetVaultId: uint256 = staticcall MissionControl(a.missionControl).coreRipeGovVaultId()

    # these need to be paused
    assert staticcall Department(a.teller).isPaused() # dev: teller not paused
    assert staticcall Department(a.auctionHouse).isPaused() # dev: auction house not paused
    assert staticcall Department(a.creditEngine).isPaused() # dev: credit engine not paused
    assert staticcall Department(a.humanResources).isPaused() # dev: human resources not paused
    assert staticcall Department(addys._getDeleverageAddr()).isPaused() # dev: deleverage not paused

    for user: address in _users:
        assert user != empty(address) # dev: invalid user
        assert not self.legacyMigrationUserDedupe[user] # dev: duplicate user
        self.legacyMigrationUserDedupe[user] = True

        # validate migration
        sourceVault: address = empty(address)
        targetVault: address = empty(address)
        sourceVault, targetVault = self._validateVaultMigration(user, _asset, LEGACY_RIPE_GOV_VAULT_ID, targetVaultId, a)
        assert sourceVault == LEGACY_RIPE_GOV_VAULT # dev: invalid legacy vault

        # source must NOT be paused, target must be paused
        assert not staticcall Vault(sourceVault).isPaused() # dev: source vault paused
        assert staticcall Vault(targetVault).isPaused() # dev: target vault not paused

        # check pre-migration balances
        targetBalanceBefore: uint256 = staticcall IERC20(_asset).balanceOf(targetVault)
        tellerBalanceBefore: uint256 = staticcall IERC20(_asset).balanceOf(a.teller)

        # get source snapshot
        prevSnapShot: PrevSourceSnapshot = self._getPreMigrationData(user, _asset, sourceVault, targetVault, a.missionControl)
        migData: RipeGovMigrationData = RipeGovMigrationData(
            amount=prevSnapShot.sourceAmount,
            govPoints=prevSnapShot.govPoints,
            unlock=prevSnapShot.unlock,
            lastTerms=prevSnapShot.lastTerms,
        )

        # export position from source vault
        amount: uint256 = extcall Teller(a.teller).exportPositionForLegacyRipeGovMigration(user, _asset, sourceVault, targetVault, a)
        assert amount == migData.amount # dev: migration amount mismatch
        self._verifyRipeGovExport(user, _asset, sourceVault, targetVault, amount, targetBalanceBefore, tellerBalanceBefore, a.teller)

        # import position to target vault
        targetShares: uint256 = extcall Teller(a.teller).importPositionForMigration(user, _asset, sourceVault, targetVaultId, targetVault, migData)
        assert targetShares != 0 # dev: invalid migration result

        # update lootbox deposit points
        extcall Lootbox(a.lootbox).updateDepositPoints(user, LEGACY_RIPE_GOV_VAULT_ID, sourceVault, _asset, a)
        extcall Lootbox(a.lootbox).updateDepositPoints(user, targetVaultId, targetVault, _asset, a)

        # verify migration
        self._verifyRipeGovImport(user, _asset, targetVault, targetVaultId, migData.amount, targetShares, prevSnapShot, a.ledger)

        log LegacyRipeGovPositionMigrationExecuted(
            user=user,
            asset=_asset,
            amount=migData.amount,
            targetShares=targetShares,
            govPoints=migData.govPoints,
            unlock=migData.unlock,
        )
    return len(_users)


####################
# Validation Utils #
####################


# post migration verification


@view
@internal
def _verifyRipeGovExport(
    _user: address,
    _asset: address,
    _sourceVault: address,
    _targetVault: address,
    _amount: uint256,
    _targetBalanceBefore: uint256,
    _tellerBalanceBefore: uint256,
    _teller: address,
):
    # verify target position
    targetBalanceAfter: uint256 = staticcall IERC20(_asset).balanceOf(_targetVault)
    assert targetBalanceAfter > _targetBalanceBefore # dev: invalid migration receipt
    assert targetBalanceAfter - _targetBalanceBefore == _amount # dev: inexact migration receipt

    # verify teller
    assert staticcall IERC20(_asset).balanceOf(_teller) == _tellerBalanceBefore # dev: teller balance residue
    assert staticcall IERC20(_asset).allowance(_teller, _targetVault) == 0 # dev: teller allowance residue

    # verify source position
    assert staticcall RipeGovVault(_sourceVault).userBalances(_user, _asset) == 0 # dev: source shares remain
    assert staticcall Vault(_sourceVault).getTotalAmountForUser(_user, _asset) == 0 # dev: source amount remains
    assert not staticcall Vault(_sourceVault).doesUserHaveBalance(_user, _asset) # dev: source balance remains


# get pre-migration data


@view
@internal
def _getPreMigrationData(
    _user: address,
    _asset: address,
    _sourceVault: address,
    _targetVault: address,
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
        targetUserPointsBefore=staticcall RipeGovVault(_targetVault).totalUserGovPoints(_user),
        targetTotalPointsBefore=staticcall RipeGovVault(_targetVault).totalGovPoints(),
    )


# verify migration


@view
@internal
def _verifyRipeGovImport(
    _user: address,
    _asset: address,
    _targetVault: address,
    _targetVaultId: uint256,
    _amount: uint256,
    _targetShares: uint256,
    _prevSnapShot: PrevSourceSnapshot,
    _ledger: address,
):
    assert _amount != 0 and _targetShares != 0 # dev: invalid migration result

    # verify target position
    assert staticcall RipeGovVault(_targetVault).userBalances(_user, _asset) == _targetShares # dev: target shares mismatch
    assert staticcall Vault(_targetVault).isUserInVaultAsset(_user, _asset) # dev: target asset not registered
    assert staticcall Vault(_targetVault).doesUserHaveBalance(_user, _asset) # dev: target position missing
    assert staticcall Ledger(_ledger).isParticipatingInVault(_user, _targetVaultId) # dev: target ledger missing

    # verify target gov data
    newGd: GovData = staticcall RipeGovVault(_targetVault).userGovData(_user, _asset)
    assert newGd.govPoints == _prevSnapShot.govPoints # dev: target points mismatch
    assert newGd.lastShares == _targetShares # dev: target last shares mismatch
    assert newGd.lastPointsUpdate == block.number # dev: target last update mismatch
    assert newGd.unlock == _prevSnapShot.unlock # dev: target unlock mismatch

    # last terms
    assert newGd.lastTerms.minLockDuration == _prevSnapShot.lastTerms.minLockDuration # dev: target terms mismatch
    assert newGd.lastTerms.maxLockDuration == _prevSnapShot.lastTerms.maxLockDuration # dev: target terms mismatch
    assert newGd.lastTerms.maxLockBoost == _prevSnapShot.lastTerms.maxLockBoost # dev: target terms mismatch
    assert newGd.lastTerms.canExit == _prevSnapShot.lastTerms.canExit # dev: target terms mismatch
    assert newGd.lastTerms.exitFee == _prevSnapShot.lastTerms.exitFee # dev: target terms mismatch

    # gov points
    assert staticcall RipeGovVault(_targetVault).totalUserGovPoints(_user) == _prevSnapShot.targetUserPointsBefore + _prevSnapShot.govPoints # dev: target user total mismatch
    assert staticcall RipeGovVault(_targetVault).totalGovPoints() == _prevSnapShot.targetTotalPointsBefore + _prevSnapShot.govPoints # dev: target global total mismatch
