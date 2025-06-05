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
from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed

struct LockTerms:
    minLockDuration: uint256
    maxLockDuration: uint256
    maxLockBoost: uint256
    canExit: bool
    exitFee: uint256

struct GovData:
    govPoints: uint256
    lastShares: uint256
    lastPointsUpdate: uint256
    unlock: uint256
    lastTerms: LockTerms

event RipeGovVaultDeposit:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    shares: uint256

event RipeGovVaultWithdrawal:
    user: indexed(address)
    asset: indexed(address)
    amount: uint256
    isDepleted: bool
    shares: uint256

event RipeGovVaultTransfer:
    fromUser: indexed(address)
    toUser: indexed(address)
    asset: indexed(address)
    transferAmount: uint256
    isFromUserDepleted: bool
    transferShares: uint256

# user gov data
userGovData: public(HashMap[address, HashMap[address, GovData]]) # user -> asset -> GovData
userGovPoints: public(HashMap[address, uint256]) # user -> gov points
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

    # deposit tokens (using shares module)
    depositAmount: uint256 = 0
    newShares: uint256 = 0
    depositAmount, newShares = sharesVault._depositTokensInVault(_user, _asset, _amount)

    # handle gov data/points
    lockTerms: LockTerms = empty(LockTerms) # TODO: get lock terms
    self._handleGovDataOnDeposit(_user, _asset, newShares, lockTerms, 0)
    # TODO: call "Governance" to update any votes

    log RipeGovVaultDeposit(user=_user, asset=_asset, amount=depositAmount, shares=newShares)
    return depositAmount


@internal
def _handleGovDataOnDeposit(
    _user: address,
    _asset: address,
    _newShares: uint256,
    _lockTerms: LockTerms,
    _additionalPoints: uint256,
):
    userData: GovData = empty(GovData)
    newPoints: uint256 = 0
    userData, newPoints = self._getLatestGovPoints(_user, _asset, _lockTerms)

    userData.unlock = self._getWeightedLockOnTokenDeposit(_newShares, _lockTerms, userData.lastShares, userData.unlock)
    userData.lastShares += _newShares
    self.userGovData[_user][_asset] = userData

    newPoints += _additionalPoints
    self.userGovPoints[_user] += newPoints
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

    # withdraw tokens (using shares module)
    withdrawalAmount: uint256 = 0
    withdrawalShares: uint256 = 0
    isDepleted: bool = False
    withdrawalAmount, withdrawalShares, isDepleted = sharesVault._withdrawTokensFromVault(_user, _asset, _amount, _recipient)

    # handle gov data/points
    lockTerms: LockTerms = empty(LockTerms) # TODO: get lock terms
    self._handleGovDataOnWithdrawal(_user, _asset, withdrawalShares, lockTerms, True)
    # TODO: call "Governance" to update any votes

    log RipeGovVaultWithdrawal(user=_user, asset=_asset, amount=withdrawalAmount, isDepleted=isDepleted, shares=withdrawalShares)
    return withdrawalAmount, isDepleted


@internal
def _handleGovDataOnWithdrawal(
    _user: address,
    _asset: address,
    _withdrawalShares: uint256,
    _lockTerms: LockTerms,
    _shouldCheckUnlock: bool,
) -> uint256:
    userData: GovData = empty(GovData)
    newPoints: uint256 = 0
    userData, newPoints = self._getLatestGovPoints(_user, _asset, _lockTerms)
    prevSavedPoints: uint256 = userData.govPoints - newPoints

    if _shouldCheckUnlock:
        assert block.number >= userData.unlock # dev: not reached unlock

    transferPoints: uint256 = userData.govPoints
    userData.govPoints = self._updatePointsOnWithdrawal(userData.govPoints, _withdrawalShares, userData.lastShares)
    userData.lastShares -= _withdrawalShares
    self.userGovData[_user][_asset] = userData

    # update gov points
    preUserGovPoints: uint256 = self.userGovPoints[_user]
    newUserGovPoints: uint256 = preUserGovPoints - prevSavedPoints + userData.govPoints
    self.userGovPoints[_user] = newUserGovPoints

    totalGovPoints: uint256 = self.totalGovPoints
    totalGovPoints = totalGovPoints - preUserGovPoints + newUserGovPoints
    self.totalGovPoints = totalGovPoints

    return transferPoints


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

    # transfer tokens (using shares module)
    transferAmount: uint256 = 0
    transferShares: uint256 = 0
    isFromUserDepleted: bool = False
    transferAmount, transferShares, isFromUserDepleted = sharesVault._transferBalanceWithinVault(_asset, _fromUser, _toUser, _transferAmount)

    # handle gov data/points
    self._handleGovDataOnTransfer(_fromUser, _toUser, _asset, transferShares, False)

    log RipeGovVaultTransfer(fromUser=_fromUser, toUser=_toUser, asset=_asset, transferAmount=transferAmount, isFromUserDepleted=isFromUserDepleted, transferShares=transferShares)
    return transferAmount, isFromUserDepleted


@internal
def _handleGovDataOnTransfer(
    _fromUser: address,
    _toUser: address,
    _asset: address,
    _transferShares: uint256,
    _shouldTransferPoints: bool,
):
    lockTerms: LockTerms = empty(LockTerms) # TODO: get lock terms

    # from user
    transferPoints: uint256 = self._handleGovDataOnWithdrawal(_fromUser, _asset, _transferShares, lockTerms, False)
    if not _shouldTransferPoints:
        transferPoints = 0

    # to user
    self._handleGovDataOnDeposit(_toUser, _asset, _transferShares, lockTerms, transferPoints)

    # Do this for both users
    # TODO: call "Governance" to update any votes


# utilities


@view
@internal
def _updatePointsOnWithdrawal(_points: uint256, _withdrawShares: uint256, _totalShares: uint256) -> uint256:
    penalty: uint256 = _points
    if _withdrawShares != _totalShares:
        penalty = min(_points, _points * _withdrawShares // _totalShares)
    return _points - penalty


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


################
# Locked Utils #
################


# latest gov bal data


@view
@internal
def _getLatestGovPoints(_user: address, _asset: address, _terms: LockTerms) -> (GovData, uint256):
    userData: GovData = self.userGovData[_user][_asset]
    userData.unlock = self._refreshUnlock(userData.unlock, _terms, userData.lastTerms)
    userData.lastTerms = _terms

    # base points (shares + time deposited)
    shares: uint256 = userData.lastShares // PRECISION
    newPoints: uint256 = 0
    if userData.lastPointsUpdate != 0 and block.number > userData.lastPointsUpdate:
        elapsedBlocks: uint256 = block.number - userData.lastPointsUpdate
        newPoints = shares * elapsedBlocks

    # asset weight
    if newPoints != 0:
        weight: uint256 = HUNDRED_PERCENT # TODO: get weight
        newPoints = newPoints * weight // HUNDRED_PERCENT

    # lock boost bonus
    if newPoints != 0 and userData.unlock > block.number:
        remainingLockDuration: uint256 = min(userData.unlock - block.number, _terms.maxLockDuration) # it is possible that param change caused higher than max, add this check
        if remainingLockDuration > _terms.minLockDuration:
            lockBoost: uint256 = _terms.maxLockBoost * (remainingLockDuration - _terms.minLockDuration) // (_terms.maxLockDuration - _terms.minLockDuration)
            newPoints += newPoints * lockBoost // HUNDRED_PERCENT

    # add total 
    userData.govPoints += newPoints
    userData.lastPointsUpdate = block.number
    return userData, newPoints


# weighted lock on token deposit


@view
@internal
def _getWeightedLockOnTokenDeposit(
    _newShares: uint256,
    _lockTerms: LockTerms,
    _prevShares: uint256,
    _prevUnlock: uint256,
) -> uint256:
    # nothing to do here (no previous balance)
    if _prevShares < PRECISION:
        return block.number + _lockTerms.minLockDuration
    prevNormalized: uint256 = _prevShares // PRECISION 

    # previous lock duration
    prevDuration: uint256 = 1
    if _prevUnlock > block.number:
        prevDuration = min(_prevUnlock - block.number, _lockTerms.maxLockDuration)

    # not allowing zero on `newNormalized` or `newLockDuration` -- or else new deposit won't get any weight
    newNormalized: uint256 = 1
    if _newShares > PRECISION:
        newNormalized = _newShares // PRECISION
    newLockDuration: uint256 = max(_lockTerms.minLockDuration, 1)

    # take weighted average, blending the unlock durations
    newWeightedDuration: uint256 = ((prevNormalized * prevDuration) + (newNormalized * newLockDuration)) // (prevNormalized + newNormalized)
    return newWeightedDuration + block.number


# same terms


@view
@external
def areKeyTermsSame(_newTerms: LockTerms, _prevTerms: LockTerms) -> bool:
    return self._areKeyTermsSame(_newTerms, _prevTerms)


@view
@internal
def _areKeyTermsSame(_newTerms: LockTerms, _prevTerms: LockTerms) -> bool:
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
@internal
def _refreshUnlock(_prevUnlock: uint256, _newTerms: LockTerms, _prevTerms: LockTerms) -> uint256:
    unlock: uint256 = _prevUnlock
    if not self._areKeyTermsSame(_newTerms, _prevTerms):
        unlock = 0
    # will auto-adjust down if max duration improved
    return min(unlock, block.number + _newTerms.maxLockDuration)


@pure
@internal
def _calcBottomsUp(_ratio: uint256, _minVal: uint256, _maxVal: uint256) -> uint256:
    if _ratio == 0 or _minVal == _maxVal:
        return _minVal
    valRange: uint256 = _maxVal - _minVal
    adjustment: uint256 =  _ratio * valRange // HUNDRED_PERCENT
    return _minVal + adjustment