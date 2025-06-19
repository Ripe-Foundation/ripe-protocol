# @version 0.4.1

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

interface Lootbox:
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address, _a: addys.Addys = empty(addys.Addys)): nonpayable

interface BoardRoom:
    def govPowerDidChangeForUser(_user: address, _userGovPoints: uint256, _totalGovPoints: uint256): nonpayable

interface MissionControl:
    def ripeGovVaultConfig(_asset: address) -> cs.RipeGovVaultConfig: view

interface VaultBook:
    def getRegId(_vaultAddr: address) -> uint256: view

interface Ledger:
    def badDebt() -> uint256: view

struct GovData:
    govPoints: uint256
    lastShares: uint256
    lastPointsUpdate: uint256
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

# user gov data
userGovData: public(HashMap[address, HashMap[address, GovData]]) # user -> asset -> GovData
totalUserGovPoints: public(HashMap[address, uint256]) # user -> gov points
totalGovPoints: public(uint256) # total gov points

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


@external
def depositTokensInVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert msg.sender == addys._getTellerAddr() # dev: only Teller allowed
    return self._depositTokensInRipeGovVault(_user, _asset, _amount, 0, _a)


@external
def depositTokensWithLockDuration(
    _user: address,
    _asset: address,
    _amount: uint256,
    _lockDuration: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    return self._depositTokensInRipeGovVault(_user, _asset, _amount, _lockDuration, _a)


@internal
def _depositTokensInRipeGovVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _lockDuration: uint256,
    _a: addys.Addys,
) -> uint256:
    a: addys.Addys = addys._getAddys(_a)

    # deposit tokens (using shares module)
    depositAmount: uint256 = 0
    newShares: uint256 = 0
    depositAmount, newShares = sharesVault._depositTokensInVault(_user, _asset, _amount)

    # handle gov data/points
    config: cs.RipeGovVaultConfig = staticcall MissionControl(a.missionControl).ripeGovVaultConfig(_asset)
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
    newPoints: uint256 = self._getLatestGovPoints(userData.lastShares, userData.lastPointsUpdate, userData.unlock, _config.lockTerms, _config.assetWeight)
    newPoints += _additionalPoints

    # refresh unlock / terms
    userData.unlock = self._refreshUnlock(userData.unlock, _config.lockTerms, userData.lastTerms)
    userData.lastTerms = _config.lockTerms
    userData.unlock = self._getWeightedLockOnTokenDeposit(_newShares, _newLockDuration, _config.lockTerms, userData.lastShares, userData.unlock)

    # save user data
    userData.lastShares = vaultData.userBalances[_user][_asset]
    userData.govPoints += newPoints
    userData.lastPointsUpdate = block.number
    self.userGovData[_user][_asset] = userData

    # save total gov points
    self.totalUserGovPoints[_user] += newPoints
    self.totalGovPoints += newPoints


# withdraw


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
    config: cs.RipeGovVaultConfig = staticcall MissionControl(_a.missionControl).ripeGovVaultConfig(_asset)
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
    newPoints: uint256 = self._getLatestGovPoints(userData.lastShares, userData.lastPointsUpdate, userData.unlock, _config.lockTerms, _config.assetWeight)
    prevSavedPoints: uint256 = userData.govPoints

    # refresh unlock / terms
    userData.unlock = self._refreshUnlock(userData.unlock, _config.lockTerms, userData.lastTerms)
    userData.lastTerms = _config.lockTerms
    if _shouldCheckRestrictions:
        assert block.number >= userData.unlock # dev: not reached unlock
        if _config.shouldFreezeWhenBadDebt:
            assert staticcall Ledger(_ledger).badDebt() == 0 # dev: cannot withdraw when bad debt

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

    # transfer tokens (using shares module)
    transferAmount: uint256 = 0
    transferShares: uint256 = 0
    isFromUserDepleted: bool = False
    transferAmount, transferShares, isFromUserDepleted = sharesVault._transferBalanceWithinVault(_asset, _fromUser, _toUser, _transferAmount)

    # handle gov data/points
    config: cs.RipeGovVaultConfig = staticcall MissionControl(a.missionControl).ripeGovVaultConfig(_asset)
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
    # from user
    transferPoints: uint256 = self._handleGovDataOnWithdrawal(_fromUser, _asset, _transferShares, False, _config, _ledger)
    if not _shouldTransferPoints:
        transferPoints = 0

    # to user
    self._handleGovDataOnDeposit(_toUser, _asset, _transferShares, _lockDuration, transferPoints, _config)

    # update other gov points / boardroom
    self._updateUserGovPoints(_fromUser, _asset, _missionControl, _boardroom)
    self._updateUserGovPoints(_toUser, _asset, _missionControl, _boardroom)


# transfer contributor tokens


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
    config: cs.RipeGovVaultConfig = staticcall MissionControl(a.missionControl).ripeGovVaultConfig(a.ripeToken)

    # transfer tokens (using shares module)
    ripeAmount: uint256 = 0
    transferShares: uint256 = 0
    na: bool = False
    ripeAmount, transferShares, na = sharesVault._transferBalanceWithinVault(a.ripeToken, _contributor, _toUser, max_value(uint256))

    # handle gov data/points
    self._handleGovDataOnTransfer(_contributor, _toUser, a.ripeToken, transferShares, _lockDuration, True, config, a.missionControl, a.boardroom, a.ledger)

    log RipeTokensTransferred(fromUser=_contributor, toUser=_toUser, amount=ripeAmount)
    return ripeAmount


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
    a: addys.Addys = addys._getAddys(_a)
    self._updateUserGovPoints(_user, empty(address), a.missionControl, a.boardroom)


@internal
def _updateUserGovPoints(
    _user: address,
    _skipAsset: address,
    _missionControl: address,
    _boardroom: address,
):
    numUserAssets: uint256 = vaultData.numUserAssets[_user]
    if numUserAssets != 0:
        for i: uint256 in range(1, numUserAssets, bound=max_value(uint256)):
            asset: address = vaultData.userAssets[_user][i]
            if asset == _skipAsset or asset == empty(address):
                continue
            self._updateGovPointsForUserAsset(_user, asset, _missionControl)

    # update boardroom
    if _boardroom != empty(address):
        extcall BoardRoom(_boardroom).govPowerDidChangeForUser(_user, self.totalUserGovPoints[_user], self.totalGovPoints)


@internal
def _updateGovPointsForUserAsset(
    _user: address,
    _asset: address,
    _missionControl: address,
):
    config: cs.RipeGovVaultConfig = staticcall MissionControl(_missionControl).ripeGovVaultConfig(_asset)

    userData: GovData = self.userGovData[_user][_asset]
    newPoints: uint256 = self._getLatestGovPoints(userData.lastShares, userData.lastPointsUpdate, userData.unlock, config.lockTerms, config.assetWeight)

    # refresh unlock / terms
    userData.unlock = self._refreshUnlock(userData.unlock, config.lockTerms, userData.lastTerms)
    userData.lastTerms = config.lockTerms

    # save user data
    userData.govPoints += newPoints
    userData.lastPointsUpdate = block.number
    self.userGovData[_user][_asset] = userData

    # save total gov points
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
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    a: addys.Addys = addys._getAddys(_a)

    # do a full update first
    self._updateUserGovPoints(_user, empty(address), a.missionControl, a.boardroom)

    # validation
    userData: GovData = self.userGovData[_user][_asset]
    assert userData.lastTerms.maxLockDuration != 0 # dev: no lock terms
    assert userData.lastShares != 0 # dev: no position

    # update lootbox points
    vaultId: uint256 = staticcall VaultBook(a.vaultBook).getRegId(self) # dev: invalid vault addr
    extcall Lootbox(a.lootbox).updateDepositPoints(_user, vaultId, self, _asset, a)

    # update lock duration
    lockDuration: uint256 = max(_newLockDuration, userData.lastTerms.minLockDuration)
    lockDuration = min(lockDuration, userData.lastTerms.maxLockDuration)
    newUnlockBlock: uint256 = block.number + lockDuration
    assert newUnlockBlock > userData.unlock # dev: new lock cannot be earlier
    userData.unlock = newUnlockBlock
    self.userGovData[_user][_asset] = userData

    log LockModified(user=_user, asset=_asset, newLockDuration=lockDuration)


@external
def releaseLock(
    _user: address,
    _asset: address,
    _a: addys.Addys = empty(addys.Addys),
):
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    a: addys.Addys = addys._getAddys(_a)

    # they are probably wanting to exit early because of bad debt, crisis of confidence
    # if they won't be able to withdraw anyway, don't let them exit early (it will cost them for no reason!)
    config: cs.RipeGovVaultConfig = staticcall MissionControl(a.missionControl).ripeGovVaultConfig(_asset)
    if staticcall Ledger(a.ledger).badDebt() != 0:
        assert not config.shouldFreezeWhenBadDebt # dev: saving user money

    # do a full update first
    self._updateUserGovPoints(_user, empty(address), a.missionControl, a.boardroom)

    # validation
    userData: GovData = self.userGovData[_user][_asset]
    assert userData.unlock > block.number # dev: no release needed
    assert userData.lastTerms.canExit # dev: cannot exit
    assert userData.lastShares != 0 # dev: no position

    # update lootbox points
    vaultId: uint256 = staticcall VaultBook(a.vaultBook).getRegId(self) # dev: invalid vault addr
    extcall Lootbox(a.lootbox).updateDepositPoints(_user, vaultId, self, _asset, a)

    # handle payment
    exitFee: uint256 = userData.lastTerms.exitFee
    assert exitFee != 0 # dev: no exit fee

    # remove shares (cost to exit early)
    userShares: uint256 = vaultData.userBalances[_user][_asset]
    sharesToRemove: uint256 = min(userShares, userShares * exitFee // HUNDRED_PERCENT)
    vaultData._reduceBalanceOnWithdrawal(_user, _asset, sharesToRemove, True)
    userData.lastShares -= sharesToRemove

    # update lock duration
    userData.unlock = 0
    self.userGovData[_user][_asset] = userData

    log LockReleased(user=_user, asset=_asset, exitFee=exitFee)


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
    if _lastShares == 0:
        return 0

    # base points (shares + time deposited)
    newPoints: uint256 = 0
    if _lastPointsUpdate != 0 and block.number > _lastPointsUpdate:
        shares: uint256 = _lastShares // PRECISION
        newPoints = shares * (block.number - _lastPointsUpdate)

    if newPoints == 0:
        return 0

    # asset weight
    if _weight != 0:
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
    if _prevUnlock > block.number and _lockTerms.maxLockDuration != 0:
        prevDuration = min(_prevUnlock - block.number, _lockTerms.maxLockDuration)

    # not allowing zero on `newNormalized` or `newLockDuration` -- or else new deposit won't get any weight
    newNormalized: uint256 = 1
    if _newShares > PRECISION:
        newNormalized = _newShares // PRECISION
    newLockDuration: uint256 = max(_newLockDuration, 1)

    # take weighted average, blending the unlock durations
    newWeightedDuration: uint256 = ((prevNormalized * prevDuration) + (newNormalized * newLockDuration)) // (prevNormalized + newNormalized)
    return block.number + newWeightedDuration


# same terms


@view
@external
def areKeyTermsSame(_newTerms: cs.LockTerms, _prevTerms: cs.LockTerms) -> bool:
    return self._areKeyTermsSame(_newTerms, _prevTerms)


@view
@internal
def _areKeyTermsSame(_newTerms: cs.LockTerms, _prevTerms: cs.LockTerms) -> bool:
    # can no longer exit!!
    if _prevTerms.canExit and not _newTerms.canExit:
        return False

    # boost got worse
    if _newTerms.maxLockBoost < _prevTerms.maxLockBoost:
        return False
   
    # min lock duration improved
    if _newTerms.minLockDuration < _prevTerms.minLockDuration:
        return False
    
    # exit fees got worse
    if _newTerms.exitFee > _prevTerms.exitFee:
        return False

    return True


# refresh unlock


@view
@external
def refreshUnlock(_prevUnlock: uint256, _newTerms: cs.LockTerms, _prevTerms: cs.LockTerms) -> uint256:
    return self._refreshUnlock(_prevUnlock, _newTerms, _prevTerms)


@view
@internal
def _refreshUnlock(_prevUnlock: uint256, _newTerms: cs.LockTerms, _prevTerms: cs.LockTerms) -> uint256:
    unlock: uint256 = _prevUnlock
    if not self._areKeyTermsSame(_newTerms, _prevTerms):
        unlock = 0
    # will auto-adjust down if max duration improved
    return min(unlock, block.number + _newTerms.maxLockDuration)
