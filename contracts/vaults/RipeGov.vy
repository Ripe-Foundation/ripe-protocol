#                                                 ______          _____                                                               
#        ___________        ____________    _____|\     \    _____\    \                _____              ____    _______    ______  
#        \          \      /            \  /     / |     |  /    / |    |          _____\    \_        ____\_  \__ \      |  |      | 
#         \    /\    \    |\___/\  \\___/||      |/     /| /    /  /___/|         /     /|     |      /     /     \ |     /  /     /| 
#          |   \_\    |    \|____\  \___|/|      |\____/ ||    |__ |___|/        /     / /____/|     /     /\      ||\    \  \    |/  
#          |      ___/           |  |     |\     \    | / |       \             |     | |_____|/    |     |  |     |\ \    \ |    |   
#          |      \  ____   __  /   / __  | \     \___|/  |     __/ __          |     | |_________  |     |  |     | \|     \|    |   
#         /     /\ \/    \ /  \/   /_/  | |  \     \      |\    \  /  \         |\     \|\        \ |     | /     /|  |\         /|   
#        /_____/ |\______||____________/|  \  \_____\     | \____\/    |        | \_____\|    |\__/||\     \_____/ |  | \_______/ |   
#        |     | | |     ||           | /   \ |     |     | |    |____/|        | |     /____/| | ||| \_____\   | /    \ |     | /    
#        |_____|/ \|_____||___________|/     \|_____|      \|____|   | |         \|_____|     |\|_|/ \ |    |___|/      \|_____|/     
#                                                                |___|/                 |____/        \|____|                         
#     ╔═════════════════════════════════════════════╗
#     ║  ** Ripe Governance Vault **                ║
#     ║  Deposit vault for RIPE tokens and RIPE LP  ║
#     ╚═════════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3
# pragma optimize codesize

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
import interfaces.ConfigStructs as cs

from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed

interface VaultBook:
    def getRegId(_vaultAddr: address) -> uint256: view
    def isValidAddr(_addr: address) -> bool: view

interface Lootbox:
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address, _a: addys.Addys = empty(addys.Addys)): nonpayable

interface BoardRoom:
    def govPowerDidChangeForUser(_user: address, _userGovPoints: uint256, _totalGovPoints: uint256): nonpayable

interface MissionControl:
    def ripeGovVaultConfig(_asset: address) -> cs.RipeGovVaultConfig: view

interface Ledger:
    def badDebt() -> uint256: view

struct GovData:
    govPoints: uint256
    lastShares: uint256
    lastPointsUpdate: uint256
    unlock: uint256
    lastTerms: cs.LockTerms

struct RipeGovMigrationData:
    amount: uint256
    govPoints: uint256
    unlock: uint256
    lastTerms: cs.LockTerms

event RipeGovVaultDeposit:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    shares: uint256
    lockDuration: uint256

event RipeGovVaultWithdrawal:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    isDepleted: bool
    shares: uint256

event RipeGovVaultBurnContributorTokens:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    shares: uint256

event RipeGovVaultTransfer:
    fromUser: indexed(address)
    toUser: indexed(address)
    asset: indexed(address)
    transferAmount: uint256
    isFromUserDepleted: bool
    transferShares: uint256

event RipeTokensTransferred:
    fromUser: indexed(address)
    toUser: indexed(address)
    amount: uint256

event LockModified:
    user: indexed(address)
    asset: indexed(address)
    newLockDuration: uint256

event LockReleased:
    user: indexed(address)
    asset: indexed(address)
    exitFee: uint256

event GovPointAccrualDisabledGlobally:
    disabledBlock: uint256
    caller: indexed(address)

event GovPointAccrualDisabledForUser:
    user: indexed(address)
    disabledBlock: uint256
    caller: indexed(address)

event RipeGovPositionExported:
    user: indexed(address)
    asset: indexed(address)
    targetVault: indexed(address)
    amount: uint256
    sourceShares: uint256
    govPoints: uint256
    unlock: uint256

event RipeGovPositionImported:
    user: indexed(address)
    asset: indexed(address)
    sourceVault: indexed(address)
    amount: uint256
    targetShares: uint256
    govPoints: uint256
    unlock: uint256

# user gov data
userGovData: public(HashMap[address, HashMap[address, GovData]]) # user -> asset -> GovData
totalUserGovPoints: public(HashMap[address, uint256]) # user -> gov points
totalGovPoints: public(uint256) # total gov points

# admin controls
govPointAccrualDisabledBlock: public(uint256) # zero means enabled; nonzero is the irreversible global-disable block
userGovPointAccrualDisabledBlock: public(HashMap[address, uint256]) # zero means enabled; nonzero is the irreversible user-disable block
positionMigratedOut: public(HashMap[address, HashMap[address, bool]]) # permanently prevents a migrated position from re-entering this vault

PRECISION: constant(uint256) = 10 ** 18 # total should be 10**24 (each asset in this strat is 18 decimals, plus 8 decimal offset for shares)
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    vaultData.__init__(False)
    sharesVault.__init__()


########
# Core #
########


# deposit


@nonreentrant
@external
def depositTokensInVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    return self._depositTokensInRipeGovVault(_user, _asset, _amount, 0, _a)


@nonreentrant
@external
def depositTokensWithLockDuration(
    _user: address,
    _asset: address,
    _amount: uint256,
    _lockDuration: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    return self._depositTokensInRipeGovVault(_user, _asset, _amount, _lockDuration, _a)


@internal
def _depositTokensInRipeGovVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _lockDuration: uint256,
    _a: addys.Addys,
) -> uint256:
    assert not self.positionMigratedOut[_user][_asset] # dev: position migrated
    a: addys.Addys = addys._getAddys(_a)

    config: cs.RipeGovVaultConfig = self._getRipeGovVaultConfig(_asset, a.missionControl)
    assert config.lockTerms.maxLockDuration != 0 # dev: no lock terms

    # deposit tokens (using shares module)
    depositAmount: uint256 = 0
    newShares: uint256 = 0
    depositAmount, newShares = sharesVault._depositTokensInVault(_user, _asset, _amount)

    # handle gov data/points
    lockDuration: uint256 = max(config.lockTerms.minLockDuration, _lockDuration)
    lockDuration = min(lockDuration, config.lockTerms.maxLockDuration)
    self._handleGovDataOnDeposit(_user, _asset, newShares, lockDuration, 0, config)
    self._updateUserGovPoints(_user, _asset, a.missionControl, a.boardroom)

    log RipeGovVaultDeposit(user=_user, asset=_asset, amount=depositAmount, shares=newShares, lockDuration=lockDuration)
    return depositAmount


@internal
def _handleGovDataOnDeposit(
    _user: address,
    _asset: address,
    _newShares: uint256,
    _newLockDuration: uint256,
    _additionalPoints: uint256,
    _config: cs.RipeGovVaultConfig,
):
    userData: GovData = self.userGovData[_user][_asset]
    shouldUpdatePoints: bool = not self._isGovPointAccrualDisabled(_user)
    newPoints: uint256 = 0
    if shouldUpdatePoints:
        newPoints = self._getLatestGovPoints(userData.lastShares, userData.lastPointsUpdate, userData.unlock, _config.lockTerms, _config.assetWeight)
        newPoints += _additionalPoints

    # refresh unlock / terms
    userData.unlock = self._refreshUnlock(userData.unlock, _config.lockTerms, userData.lastTerms)
    userData.lastTerms = _config.lockTerms
    userData.unlock = self._getWeightedLockOnTokenDeposit(_newShares, _newLockDuration, _config.lockTerms, userData.lastShares, userData.unlock)

    # save user data
    userData.lastShares = vaultData.userBalances[_user][_asset]
    userData.lastPointsUpdate = block.number
    if shouldUpdatePoints:
        userData.govPoints += newPoints
    self.userGovData[_user][_asset] = userData

    # save total gov points
    if shouldUpdatePoints:
        self.totalUserGovPoints[_user] += newPoints
        self.totalGovPoints += newPoints


# withdraw


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
    a: addys.Addys = addys._getAddys(_a)
    return self._withdrawTokensFromVault(_user, _asset, _amount, _recipient, True, a)


@nonreentrant
@external
def withdrawContributorTokensToBurn(_user: address, _a: addys.Addys = empty(addys.Addys)) -> uint256:
    hr: address = addys._getHumanResourcesAddr()
    assert msg.sender == hr # dev: not allowed
    a: addys.Addys = addys._getAddys(_a)
    if vaultData.userBalances[_user][a.ripeToken] == 0:
        return 0
    withdrawalAmount: uint256 = 0
    isDepleted: bool = False
    withdrawalAmount, isDepleted = self._withdrawTokensFromVault(_user, a.ripeToken, max_value(uint256), hr, False, a)
    return withdrawalAmount


@internal
def _withdrawTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
    _shouldCheckRestrictions: bool,
    _a: addys.Addys,
) -> (uint256, bool):
    # withdraw tokens (using shares module)
    withdrawalAmount: uint256 = 0
    withdrawalShares: uint256 = 0
    isDepleted: bool = False
    withdrawalAmount, withdrawalShares, isDepleted = sharesVault._withdrawTokensFromVault(_user, _asset, _amount, _recipient)

    # handle gov data/points
    config: cs.RipeGovVaultConfig = self._getRipeGovVaultConfig(_asset, _a.missionControl)
    self._handleGovDataOnWithdrawal(_user, _asset, withdrawalShares, _shouldCheckRestrictions, config, _a.ledger)
    self._updateUserGovPoints(_user, _asset, _a.missionControl, _a.boardroom)

    log RipeGovVaultWithdrawal(user=_user, asset=_asset, amount=withdrawalAmount, isDepleted=isDepleted, shares=withdrawalShares)
    return withdrawalAmount, isDepleted


@internal
def _handleGovDataOnWithdrawal(
    _user: address,
    _asset: address,
    _withdrawalShares: uint256,
    _shouldCheckRestrictions: bool,
    _config: cs.RipeGovVaultConfig,
    _ledger: address,
) -> uint256:
    userData: GovData = self.userGovData[_user][_asset]
    shouldUpdatePoints: bool = not self._isGovPointAccrualDisabled(_user)
    newPoints: uint256 = 0
    if shouldUpdatePoints:
        # Courtesy may zero unlock on this touch. Accrue through this block with
        # the pre-release unlock and the live terms/weight first.
        newPoints = self._getLatestGovPoints(userData.lastShares, userData.lastPointsUpdate, userData.unlock, _config.lockTerms, _config.assetWeight)

    # refresh unlock / terms
    userData.unlock = self._refreshUnlock(userData.unlock, _config.lockTerms, userData.lastTerms)
    userData.lastTerms = _config.lockTerms
    if _shouldCheckRestrictions:
        assert block.number >= userData.unlock # dev: not reached unlock
        if _config.shouldFreezeWhenBadDebt:
            assert staticcall Ledger(_ledger).badDebt() == 0 # dev: cannot withdraw when bad debt

    # Disabled users forfeit no stored points on a partial exit. A complete
    # per-asset exit clears only the frozen points already recorded for that
    # asset; unsafe pending accrual is intentionally never calculated.
    if not shouldUpdatePoints:
        userData.lastShares = vaultData.userBalances[_user][_asset]
        userData.lastPointsUpdate = block.number
        if userData.lastShares == 0:
            savedPoints: uint256 = userData.govPoints
            assert self.totalUserGovPoints[_user] >= savedPoints # dev: inconsistent user gov points
            assert self.totalGovPoints >= savedPoints # dev: inconsistent global gov points
            userData.govPoints = 0
            self.totalUserGovPoints[_user] -= savedPoints
            self.totalGovPoints -= savedPoints
        self.userGovData[_user][_asset] = userData
        return 0

    prevSavedPoints: uint256 = userData.govPoints

    # handle points penalty for withdrawal
    newUserPoints: uint256 = userData.govPoints + newPoints
    pointsToReduce: uint256 = newUserPoints
    if _withdrawalShares != userData.lastShares:
        pointsToReduce = min(newUserPoints, newUserPoints * _withdrawalShares // userData.lastShares)
    newUserPoints -= pointsToReduce

    # save user data
    userData.lastShares = vaultData.userBalances[_user][_asset]
    userData.govPoints = newUserPoints
    userData.lastPointsUpdate = block.number
    self.userGovData[_user][_asset] = userData

    # update total gov points
    preTotalUserGovPoints: uint256 = self.totalUserGovPoints[_user]
    newUserGovPoints: uint256 = preTotalUserGovPoints - prevSavedPoints + newUserPoints
    self.totalUserGovPoints[_user] = newUserGovPoints

    totalGovPoints: uint256 = self.totalGovPoints
    totalGovPoints = totalGovPoints - preTotalUserGovPoints + newUserGovPoints
    self.totalGovPoints = totalGovPoints

    return pointsToReduce


# transfer


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
    a: addys.Addys = addys._getAddys(_a)

    # Intentionally not gated on lock terms: AuctionHouse/CreditEngine forced
    # transfers must stay live for liquidation and redemption. The recipient
    # leg uses minLockDuration; a valid row may have minLockDuration == 0.

    # transfer tokens (using shares module)
    transferAmount: uint256 = 0
    transferShares: uint256 = 0
    isFromUserDepleted: bool = False
    transferAmount, transferShares, isFromUserDepleted = sharesVault._transferBalanceWithinVault(_asset, _fromUser, _toUser, _transferAmount)

    # handle gov data/points
    config: cs.RipeGovVaultConfig = self._getRipeGovVaultConfig(_asset, a.missionControl)
    self._handleGovDataOnTransfer(_fromUser, _toUser, _asset, transferShares, config.lockTerms.minLockDuration, False, config, a.missionControl, a.boardroom, a.ledger)

    log RipeGovVaultTransfer(fromUser=_fromUser, toUser=_toUser, asset=_asset, transferAmount=transferAmount, isFromUserDepleted=isFromUserDepleted, transferShares=transferShares)
    return transferAmount, isFromUserDepleted


@internal
def _handleGovDataOnTransfer(
    _fromUser: address,
    _toUser: address,
    _asset: address,
    _transferShares: uint256,
    _lockDuration: uint256,
    _shouldTransferPoints: bool,
    _config: cs.RipeGovVaultConfig,
    _missionControl: address,
    _boardroom: address,
    _ledger: address,
):
    assert not self.positionMigratedOut[_toUser][_asset] # dev: recipient position migrated

    # from user
    transferPoints: uint256 = self._handleGovDataOnWithdrawal(_fromUser, _asset, _transferShares, False, _config, _ledger)
    if not _shouldTransferPoints:
        transferPoints = 0

    # to user
    self._handleGovDataOnDeposit(_toUser, _asset, _transferShares, _lockDuration, transferPoints, _config)

    # The disabled sender already skips its own Boardroom callback below, but
    # the healthy recipient would still call it and could strand the sender's
    # emergency exit. Suppress both callbacks for this transaction; canonical
    # totals update atomically and the public update path can retry the recipient.
    boardroom: address = _boardroom
    if self._isGovPointAccrualDisabled(_fromUser):
        boardroom = empty(address)

    self._updateUserGovPoints(_fromUser, _asset, _missionControl, boardroom)
    self._updateUserGovPoints(_toUser, _asset, _missionControl, boardroom)


# transfer contributor tokens


@nonreentrant
@external
def transferContributorRipeTokens(
    _contributor: address,
    _toUser: address,
    _lockDuration: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getHumanResourcesAddr() # dev: not allowed
    a: addys.Addys = addys._getAddys(_a)

    # config
    config: cs.RipeGovVaultConfig = self._getRipeGovVaultConfig(a.ripeToken, a.missionControl)
    assert config.lockTerms.maxLockDuration != 0 # dev: no lock terms

    # transfer tokens (using shares module)
    ripeAmount: uint256 = 0
    transferShares: uint256 = 0
    na: bool = False
    ripeAmount, transferShares, na = sharesVault._transferBalanceWithinVault(a.ripeToken, _contributor, _toUser, max_value(uint256))

    # Confirmed Contributor duration is forwarded exactly. Do not clamp to the
    # live min/max; a later maximum reduction must not rewrite the agreement.
    self._handleGovDataOnTransfer(_contributor, _toUser, a.ripeToken, transferShares, _lockDuration, True, config, a.missionControl, a.boardroom, a.ledger)

    log RipeTokensTransferred(fromUser=_contributor, toUser=_toUser, amount=ripeAmount)
    return ripeAmount


# disable governance-point accrual


@external
def disableGovPointAccrualGlobally():
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert self.govPointAccrualDisabledBlock == 0 # dev: already disabled

    self.govPointAccrualDisabledBlock = block.number
    log GovPointAccrualDisabledGlobally(disabledBlock=block.number, caller=msg.sender)


@external
def disableGovPointAccrualForUser(_user: address):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _user != empty(address) # dev: invalid user
    assert self.govPointAccrualDisabledBlock == 0 # dev: globally disabled
    assert self.userGovPointAccrualDisabledBlock[_user] == 0 # dev: already disabled

    self.userGovPointAccrualDisabledBlock[_user] = block.number
    log GovPointAccrualDisabledForUser(user=_user, disabledBlock=block.number, caller=msg.sender)


@view
@internal
def _isGovPointAccrualDisabled(_user: address) -> bool:
    return self.govPointAccrualDisabledBlock != 0 or self.userGovPointAccrualDisabledBlock[_user] != 0


######################
# Position Migration #
######################


@nonreentrant
@external
def exportPositionForMigration(_user: address, _asset: address, _targetVault: address, _a: addys.Addys = empty(addys.Addys)) -> RipeGovMigrationData:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert vaultData.isPaused # dev: vault not paused
    assert not self.positionMigratedOut[_user][_asset] # dev: position already migrated

    a: addys.Addys = addys._getAddys(_a)
    assert empty(address) not in [_user, _asset, _targetVault] # dev: invalid migration address
    assert _targetVault != self and _targetVault.is_contract # dev: invalid target vault
    assert staticcall VaultBook(a.vaultBook).isValidAddr(_targetVault) # dev: invalid target vault

    # check position
    sourceShares: uint256 = vaultData.userBalances[_user][_asset]
    assert sourceShares != 0 # dev: no position

    # Accrue through this block without refreshing terms from current config.
    # Migration must preserve the terms and unlock the position was actually
    # carrying before a temporary wind-down configuration was installed.
    self._updateGovPointsForUserAsset(_user, _asset, a.missionControl, False)

    userData: GovData = self.userGovData[_user][_asset]
    assert userData.lastShares == sourceShares # dev: inconsistent position shares
    assert self.totalUserGovPoints[_user] >= userData.govPoints # dev: inconsistent user gov points
    assert self.totalGovPoints >= userData.govPoints # dev: inconsistent global gov points

    # calculate withdrawal shares and amount
    withdrawalShares: uint256 = 0
    amount: uint256 = 0
    withdrawalShares, amount = sharesVault._calcWithdrawalSharesAndAmount(_user, _asset, max_value(uint256))
    assert withdrawalShares == sourceShares # dev: partial migration

    # reduce balance
    removedShares: uint256 = 0
    isDepleted: bool = False
    removedShares, isDepleted = vaultData._reduceBalanceOnWithdrawal(_user, _asset, withdrawalShares, True)
    assert removedShares == sourceShares and isDepleted # dev: incomplete migration

    # update total gov points
    self.totalUserGovPoints[_user] -= userData.govPoints
    self.totalGovPoints -= userData.govPoints
    self.userGovData[_user][_asset] = empty(GovData)
    self.positionMigratedOut[_user][_asset] = True

    # transfer tokens to target vault
    assert extcall IERC20(_asset).transfer(_targetVault, amount, default_return_value=True) # dev: token transfer failed

    log RipeGovPositionExported(
        user=_user,
        asset=_asset,
        targetVault=_targetVault,
        amount=amount,
        sourceShares=sourceShares,
        govPoints=userData.govPoints,
        unlock=userData.unlock,
    )

    return RipeGovMigrationData(
        amount=amount,
        govPoints=userData.govPoints,
        unlock=userData.unlock,
        lastTerms=userData.lastTerms,
    )


@nonreentrant
@external
def importPositionForMigration(_user: address, _asset: address, _sourceVault: address, _migration: RipeGovMigrationData) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert vaultData.isPaused # dev: vault not paused

    # address validation
    assert empty(address) not in [_user, _asset, _sourceVault] # dev: invalid migration address
    assert _sourceVault != self and _sourceVault.is_contract # dev: invalid source vault
    assert staticcall VaultBook(addys._getVaultBookAddr()).isValidAddr(_sourceVault) # dev: invalid source vault

    # user validation
    assert not self.positionMigratedOut[_user][_asset] # dev: position already migrated out
    assert _migration.amount != 0 # dev: invalid migration amount
    assert vaultData.userBalances[_user][_asset] == 0 # dev: target balance exists

    # gov data validation
    userData: GovData = self.userGovData[_user][_asset]
    assert userData.govPoints == 0 and userData.lastShares == 0 # dev: target gov data exists
    assert userData.lastPointsUpdate == 0 and userData.unlock == 0 # dev: target gov data exists
    assert userData.lastTerms.minLockDuration == 0 and userData.lastTerms.maxLockDuration == 0 # dev: target terms exist
    assert userData.lastTerms.maxLockBoost == 0 and not userData.lastTerms.canExit and userData.lastTerms.exitFee == 0 # dev: target terms exist

    # check asset balance
    totalAssetBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    assert totalAssetBalance >= _migration.amount # dev: migration funds not received
    previousAssetBalance: uint256 = totalAssetBalance - _migration.amount

    # calculate target shares
    targetShares: uint256 = sharesVault._amountToShares(
        _migration.amount,
        vaultData.totalBalances[_asset],
        previousAssetBalance,
        False,
    )
    assert targetShares != 0 # dev: invalid target shares

    # add balance and update gov data
    vaultData._addBalanceOnDeposit(_user, _asset, targetShares, True)
    self.userGovData[_user][_asset] = GovData(
        govPoints=_migration.govPoints,
        lastShares=targetShares,
        lastPointsUpdate=block.number,
        unlock=_migration.unlock,
        lastTerms=_migration.lastTerms,
    )
    self.totalUserGovPoints[_user] += _migration.govPoints
    self.totalGovPoints += _migration.govPoints

    log RipeGovPositionImported(
        user=_user,
        asset=_asset,
        sourceVault=_sourceVault,
        amount=_migration.amount,
        targetShares=targetShares,
        govPoints=_migration.govPoints,
        unlock=_migration.unlock,
    )
    return targetShares


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
    userData: GovData = self.userGovData[_user][_asset]
    if userData.lastShares == 0:
        return 0

    points: uint256 = userData.lastShares // PRECISION
    if userData.lastTerms.maxLockDuration != 0:
        points += self._getLockBonusPoints(points, userData.unlock, userData.lastTerms)

    return points


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


#####################
# Update Gov Points #
#####################


@external
def updateUserGovPoints(_user: address, _a: addys.Addys = empty(addys.Addys)):
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms

    # A gov-point refresh rewrites `unlock` and `lastTerms` from the CURRENT asset config
    # (`_updateGovPointsForUserAsset`), unconditionally -- the accrual-disable flag gates only the
    # POINTS, not that rewrite. While this vault is in its migration pause -- the window in which
    # wind-down terms are live and imported positions carry preserved original terms -- that
    # rewrite would destroy exactly what the migration preserves, so the route is closed.
    assert not vaultData.isPaused # dev: contract paused

    a: addys.Addys = addys._getAddys(_a)
    self._updateUserGovPoints(_user, empty(address), a.missionControl, a.boardroom)


@internal
def _updateUserGovPoints(
    _user: address,
    _skipAsset: address,
    _missionControl: address,
    _boardroom: address,
):
    shouldUpdatePoints: bool = not self._isGovPointAccrualDisabled(_user)

    numUserAssets: uint256 = vaultData.numUserAssets[_user]
    if numUserAssets != 0:
        for i: uint256 in range(1, numUserAssets, bound=max_value(uint256)):
            asset: address = vaultData.userAssets[_user][i]
            if asset == _skipAsset or asset == empty(address):
                continue
            self._updateGovPointsForUserAsset(_user, asset, _missionControl, True)

    if not shouldUpdatePoints:
        return

    # update boardroom
    if _boardroom != empty(address):
        extcall BoardRoom(_boardroom).govPowerDidChangeForUser(_user, self.totalUserGovPoints[_user], self.totalGovPoints)


@internal
def _updateGovPointsForUserAsset(
    _user: address,
    _asset: address,
    _missionControl: address,
    _shouldRefreshTerms: bool,
):
    config: cs.RipeGovVaultConfig = self._getRipeGovVaultConfig(_asset, _missionControl)

    userData: GovData = self.userGovData[_user][_asset]
    shouldUpdatePoints: bool = not self._isGovPointAccrualDisabled(_user)
    newPoints: uint256 = 0
    if shouldUpdatePoints:
        pointTerms: cs.LockTerms = config.lockTerms
        if not _shouldRefreshTerms:
            pointTerms = userData.lastTerms
        newPoints = self._getLatestGovPoints(userData.lastShares, userData.lastPointsUpdate, userData.unlock, pointTerms, config.assetWeight)

    # Export migration accrues the position but deliberately retains its stored
    # pre-wind-down unlock and terms for the target import.
    if _shouldRefreshTerms:
        userData.unlock = self._refreshUnlock(userData.unlock, config.lockTerms, userData.lastTerms)
        userData.lastTerms = config.lockTerms

    # save user data
    userData.lastPointsUpdate = block.number
    if shouldUpdatePoints:
        userData.govPoints += newPoints
    self.userGovData[_user][_asset] = userData

    # save total gov points
    if shouldUpdatePoints:
        self.totalUserGovPoints[_user] += newPoints
        self.totalGovPoints += newPoints


####################
# Lock Adjustments #
####################


@external
def adjustLock(
    _user: address,
    _asset: address,
    _newLockDuration: uint256,
    _a: addys.Addys = empty(addys.Addys),
):
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert not vaultData.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    # do a full update first
    self._updateUserGovPoints(_user, empty(address), a.missionControl, a.boardroom)

    # validation
    userData: GovData = self.userGovData[_user][_asset]
    assert userData.lastTerms.maxLockDuration != 0 # dev: no lock terms
    assert userData.lastShares != 0 # dev: no position

    # update lock duration
    lockDuration: uint256 = max(_newLockDuration, userData.lastTerms.minLockDuration)
    lockDuration = min(lockDuration, userData.lastTerms.maxLockDuration)
    newUnlockBlock: uint256 = block.number + lockDuration
    assert newUnlockBlock > userData.unlock # dev: new lock cannot be earlier
    userData.unlock = newUnlockBlock
    self.userGovData[_user][_asset] = userData

    # checkpoint lootbox after the new unlock is committed
    self._updateDepositPoints(_user, _asset, a)

    log LockModified(user=_user, asset=_asset, newLockDuration=lockDuration)


@external
def releaseLock(
    _user: address,
    _asset: address,
    _a: addys.Addys = empty(addys.Addys),
):
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    assert not vaultData.isPaused # dev: contract paused
    a: addys.Addys = addys._getAddys(_a)

    # they are probably wanting to exit early because of bad debt, crisis of confidence
    # if they won't be able to withdraw anyway, don't let them exit early (it will cost them for no reason!)
    config: cs.RipeGovVaultConfig = self._getRipeGovVaultConfig(_asset, a.missionControl)
    if staticcall Ledger(a.ledger).badDebt() != 0:
        assert not config.shouldFreezeWhenBadDebt # dev: saving user money

    # do a full update first
    self._updateUserGovPoints(_user, empty(address), a.missionControl, a.boardroom)

    # validation
    userData: GovData = self.userGovData[_user][_asset]
    assert userData.unlock > block.number # dev: no release needed
    assert userData.lastTerms.canExit # dev: cannot exit
    assert userData.lastShares != 0 # dev: no position

    # handle payment
    exitFee: uint256 = userData.lastTerms.exitFee
    assert exitFee != 0 # dev: no exit fee

    # remove shares (cost to exit early)
    userShares: uint256 = vaultData.userBalances[_user][_asset]
    totalShares: uint256 = vaultData.totalBalances[_asset]
    # This guard requires a remaining holder address; permissionless addresses
    # cannot prove distinct beneficial ownership, so same-owner fee recapture
    # through another address remains possible by accepted policy.
    assert totalShares > userShares # dev: no remaining holders

    sharesToRemove: uint256 = userShares
    if exitFee != HUNDRED_PERCENT:
        totalBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
        claimBefore: uint256 = sharesVault._sharesToAmount(userShares, totalShares, totalBalance, False)
        assert claimBefore != 0 # dev: no fee-bearing claim

        # Floor the fee-adjusted live claim, then keep the largest indivisible
        # share balance whose exact post-state floored claim does not exceed the
        # target: claim(postShares) <= target < claim(postShares + 1).
        targetClaim: uint256 = claimBefore * (HUNDRED_PERCENT - exitFee) // HUNDRED_PERCENT
        claimCeiling: uint256 = targetClaim + 1
        # ceil((target + 1) * (remaining actual shares + virtual shares)
        #      / (assets - target)) - 1
        # is exactly floor((numerator - 1) / denominator), including the strict
        # boundary needed by the floored post-state claim inequality.
        maxPostShares: uint256 = sharesVault._amountToShares(
            claimCeiling,
            totalShares - userShares,
            totalBalance - claimCeiling,
            True,
        ) - 1
        sharesToRemove = userShares - maxPostShares

    vaultData._reduceBalanceOnWithdrawal(_user, _asset, sharesToRemove, True)
    userData.lastShares = vaultData.userBalances[_user][_asset]

    # release the lock before the external checkpoint so the vault reports the
    # final post-burn, unboosted Lootbox balance
    userData.unlock = 0
    self.userGovData[_user][_asset] = userData

    # accrue elapsed deposit points with the previous checkpoint, then store the
    # live post-burn balance for future accrual
    self._updateDepositPoints(_user, _asset, a)

    log LockReleased(user=_user, asset=_asset, exitFee=exitFee)


@internal
def _updateDepositPoints(_user: address, _asset: address, _a: addys.Addys):
    vaultId: uint256 = staticcall VaultBook(_a.vaultBook).getRegId(self) # dev: invalid vault addr
    extcall Lootbox(_a.lootbox).updateDepositPoints(_user, vaultId, self, _asset, _a)


@view
@internal
def _getRipeGovVaultConfig(_asset: address, _missionControl: address) -> cs.RipeGovVaultConfig:
    return staticcall MissionControl(_missionControl).ripeGovVaultConfig(_asset)


################
# Points Utils #
################


# latest gov points


@view
@external
def getLatestGovPoints(
    _lastShares: uint256,
    _lastPointsUpdate: uint256,
    _unlock: uint256,
    _terms: cs.LockTerms,
    _weight: uint256,
) -> uint256:
    return self._getLatestGovPoints(_lastShares, _lastPointsUpdate, _unlock, _terms, _weight)


@view
@internal
def _getLatestGovPoints(
    _lastShares: uint256,
    _lastPointsUpdate: uint256,
    _unlock: uint256,
    _terms: cs.LockTerms,
    _weight: uint256,
) -> uint256:
    if (_lastShares == 0 or _lastPointsUpdate == 0 or block.number <= _lastPointsUpdate):
        return 0

    # base points (shares + time deposited)
    newPoints: uint256 = (_lastShares // PRECISION) * (block.number - _lastPointsUpdate)
    if newPoints == 0:
        return 0

    # asset weight -- a configured zero means zero points (GOV-WEIGHT-01).
    # The multiplier is applied unconditionally: guarding on `_weight != 0` made a
    # zero weight fall through to the unweighted base, i.e. behave as 100%.
    newPoints = newPoints * _weight // HUNDRED_PERCENT

    # lock boost bonus (only if terms are set)
    if _terms.maxLockDuration != 0:
        newPoints += self._getLockBonusPoints(newPoints, _unlock, _terms)

    return newPoints


# lock bonus points


@view
@external
def getLockBonusPoints(
    _points: uint256,
    _unlock: uint256,
    _terms: cs.LockTerms,
) -> uint256:
    return self._getLockBonusPoints(_points, _unlock, _terms)


@view
@internal
def _getLockBonusPoints(
    _points: uint256,
    _unlock: uint256,
    _terms: cs.LockTerms,
) -> uint256:
    if _points == 0 or _unlock <= block.number:
        return 0

    remainingLockDuration: uint256 = min(_unlock - block.number, _terms.maxLockDuration) # it is possible that param change caused higher than max, add this check
    if remainingLockDuration <= _terms.minLockDuration:
        return 0
    
    lockBonusRatio: uint256 = _terms.maxLockBoost * (remainingLockDuration - _terms.minLockDuration) // (_terms.maxLockDuration - _terms.minLockDuration)
    return _points * lockBonusRatio // HUNDRED_PERCENT


# weighted lock on token deposit


@view
@external
def getWeightedLockOnTokenDeposit(
    _newShares: uint256,
    _newLockDuration: uint256,
    _lockTerms: cs.LockTerms,
    _prevShares: uint256,
    _prevUnlock: uint256,
) -> uint256:
    return self._getWeightedLockOnTokenDeposit(_newShares, _newLockDuration, _lockTerms, _prevShares, _prevUnlock)


@view
@internal
def _getWeightedLockOnTokenDeposit(
    _newShares: uint256,
    _newLockDuration: uint256,
    _lockTerms: cs.LockTerms,
    _prevShares: uint256,
    _prevUnlock: uint256,
) -> uint256:
    # nothing to do here (no previous balance)
    if _prevShares < PRECISION:
        return block.number + _newLockDuration
    prevNormalized: uint256 = _prevShares // PRECISION 

    # previous lock duration
    prevDuration: uint256 = 1
    if _prevUnlock > block.number:
        prevDuration = _prevUnlock - block.number

    # not allowing zero on `newNormalized` or `newLockDuration` -- or else new deposit won't get any weight
    newNormalized: uint256 = 1
    if _newShares > PRECISION:
        newNormalized = _newShares // PRECISION
    newLockDuration: uint256 = max(_newLockDuration, 1)

    # take weighted average, blending the unlock durations
    newWeightedDuration: uint256 = ((prevNormalized * prevDuration) + (newNormalized * newLockDuration)) // (prevNormalized + newNormalized)
    return block.number + newWeightedDuration


# legacy directional terms classifier; not the courtesy predicate


@view
@external
def areKeyTermsSame(_newTerms: cs.LockTerms, _prevTerms: cs.LockTerms) -> bool:
    return self._areKeyTermsSame(_newTerms, _prevTerms)


@view
@internal
def _areKeyTermsSame(_newTerms: cs.LockTerms, _prevTerms: cs.LockTerms) -> bool:
    return (
        (not _prevTerms.canExit or _newTerms.canExit)
        and _newTerms.maxLockBoost >= _prevTerms.maxLockBoost
        and _newTerms.minLockDuration >= _prevTerms.minLockDuration
        and _newTerms.exitFee <= _prevTerms.exitFee
    )


# refresh unlock


@view
@external
def refreshUnlock(_prevUnlock: uint256, _newTerms: cs.LockTerms, _prevTerms: cs.LockTerms) -> uint256:
    return self._refreshUnlock(_prevUnlock, _newTerms, _prevTerms)


@view
@internal
def _refreshUnlock(_prevUnlock: uint256, _newTerms: cs.LockTerms, _prevTerms: cs.LockTerms) -> uint256:
    # Courtesy zero when any live term is worse: canExit lost, fee up while
    # exit was already on, boost down, minLockDuration up, or maxLockDuration
    # up. Any adverse change wins even if another term improves.
    # False/0 -> True/fee enables an optional paid exit; that is not a courtesy.
    # Lazy: only a later touch while the worse config is still live persists
    # unlock=0. Restoring the old terms first removes the opportunity.
    # Once recorded, restoring the previous config does not restore the lock.
    # A later lock-forming action may establish a new lock.
    # This does not override Teller pause or shouldFreezeWhenBadDebt.
    if (
        (_prevTerms.canExit and not _newTerms.canExit)
        or (_prevTerms.canExit and _newTerms.exitFee > _prevTerms.exitFee)
        or _newTerms.maxLockBoost < _prevTerms.maxLockBoost
        or _newTerms.minLockDuration > _prevTerms.minLockDuration
        or _newTerms.maxLockDuration > _prevTerms.maxLockDuration
    ):
        return 0
    return _prevUnlock
