#        ______   __     __   __   ______  ______   __  __   ______   ______   ______   ______   _____    
#       /\  ___\ /\ \  _ \ \ /\ \ /\__  _\/\  ___\ /\ \_\ \ /\  == \ /\  __ \ /\  __ \ /\  == \ /\  __-.  
#       \ \___  \\ \ \/ ".\ \\ \ \\/_/\ \/\ \ \____\ \  __ \\ \  __< \ \ \/\ \\ \  __ \\ \  __< \ \ \/\ \ 
#        \/\_____\\ \__/".~\_\\ \_\  \ \_\ \ \_____\\ \_\ \_\\ \_____\\ \_____\\ \_\ \_\\ \_\ \_\\ \____- 
#         \/_____/ \/_/   \/_/ \/_/   \/_/  \/_____/ \/_/\/_/ \/_____/ \/_____/ \/_/\/_/ \/_/ /_/ \/____/ 
#                                                      ┓  ┓   
#                                                     ┏┫┏┓┃╋┏┓
#                                                     ┗┻┗ ┗┗┗┻
#
#      Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#      Ripe Foundation (C) 2025 

# @version 0.4.3
# pragma optimize codesize

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock
from interfaces import Vault
import interfaces.ConfigStructs as cs

interface MissionControl:
    def setUnderscoreRegistry(_underscoreRegistry: address): nonpayable
    def setRipeBondConfig(_config: cs.RipeBondConfig): nonpayable
    def setShouldCheckLastTouch(_shouldCheck: bool): nonpayable
    def canPerformLiteAction(_user: address) -> bool: view
    def setHrConfig(_config: cs.HrConfig): nonpayable
    def ripeBondConfig() -> cs.RipeBondConfig: view
    def underscoreRegistry() -> address: view
    def shouldCheckLastTouch() -> bool: view
    def hrConfig() -> cs.HrConfig: view

interface BondBooster:
    def setManyBondBoosters(_boosters: DynArray[BoosterConfig, MAX_BOOSTERS]): nonpayable
    def setMaxBoostAndMaxUnits(_maxBoostRatio: uint256, _maxUnits: uint256): nonpayable
    def removeManyBondBoosters(_users: DynArray[address, MAX_BOOSTERS]): nonpayable
    def getBoostRatio(_user: address, _units: uint256) -> uint256: view
    def setMinLockDuration(_minLockDuration: uint256): nonpayable
    def setBondBooster(_config: BoosterConfig): nonpayable
    def removeBondBooster(_user: address): nonpayable

interface HrContributor:
    def setIsFrozen(_shouldFreeze: bool) -> bool: nonpayable
    def setManager(_manager: address): nonpayable
    def cashRipeCheck() -> uint256: nonpayable
    def cancelOwnershipChange(): nonpayable
    def cancelRipeTransfer(): nonpayable
    def cancelPaycheck(): nonpayable

interface Teller:
    def deleverageWithSpecificAssets(_assets: DynArray[DeleverageAsset, MAX_DELEVERAGE_ASSETS], _user: address = msg.sender) -> uint256: nonpayable
    def deleverageUser(_user: address = msg.sender, _targetRepayAmount: uint256 = max_value(uint256)) -> uint256: nonpayable
    def deleverageManyUsers(_users: DynArray[DeleverageUserRequest, MAX_DELEVERAGE_USERS]) -> uint256: nonpayable

interface Lootbox:
    def resetUserBalancePoints(_user: address, _asset: address, _vaultId: uint256): nonpayable
    def resetAssetPoints(_asset: address, _vaultId: uint256): nonpayable
    def resetUserBorrowPoints(_user: address): nonpayable

interface BondRoom:
    def startBondEpochAtBlock(_block: uint256): nonpayable
    def setBondBooster(_bondBooster: address): nonpayable
    def bondBooster() -> address: view

interface Ledger:
    def isHrContributor(_contributor: address) -> bool: view
    def setRipeAvailForRewards(_amount: uint256): nonpayable
    def setRipeAvailForBonds(_amount: uint256): nonpayable
    def setRipeAvailForHr(_amount: uint256): nonpayable
    def setBadDebt(_amount: uint256): nonpayable

interface Deleverage:
    def deleverageWithVolAssets(_user: address, _assets: DynArray[DeleverageAsset, MAX_DELEVERAGE_ASSETS]) -> uint256: nonpayable

interface UnderscoreLedger:
    def isUserWallet(_addr: address) -> bool: view

interface UnderscoreRegistry:
    def getAddr(_addyId: uint256) -> address: view

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

flag ActionType:
    HR_CONFIG_TEMPLATE
    HR_CONFIG_MAX_COMP
    HR_CONFIG_MIN_CLIFF
    HR_CONFIG_MAX_START_DELAY
    HR_CONFIG_VESTING
    HR_MANAGER
    HR_CANCEL_PAYCHECK
    RIPE_BOND_CONFIG
    RIPE_BOND_EPOCH_LENGTH
    RIPE_BAD_DEBT
    RIPE_BOND_BOOSTER
    BOND_BOOSTER_ADD
    BOND_BOOSTER_BOUNDARIES
    LOOT_USER_BALANCE_RESET
    LOOT_ASSET_RESET
    LOOT_USER_BORROW_RESET
    RIPE_AVAIL_REWARDS
    RIPE_AVAIL_HR
    RIPE_AVAIL_BONDS
    OTHER_UNDERSCORE_REGISTRY
    OTHER_SHOULD_CHECK_LAST_TOUCH

struct DeleverageUserRequest:
    user: address
    targetRepayAmount: uint256

struct DeleverageAsset:
    vaultId: uint256
    asset: address
    targetRepayAmount: uint256

struct PendingManager:
    contributor: address
    pendingManager: address

struct PendingCancelPaycheck:
    contributor: address
    pendingShouldCancel: bool

struct BoosterConfig:
    user: address
    boostRatio: uint256
    maxUnitsAllowed: uint256
    expireBlock: uint256

struct UserBalanceReset:
    user: address
    asset: address
    vaultId: uint256

struct AssetReset:
    asset: address
    vaultId: uint256

struct BoosterBoundaries:
    maxBoostRatio: uint256
    maxUnits: uint256

event PendingHrContribTemplateChange:
    contribTemplate: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingHrMaxCompensationChange:
    maxCompensation: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingHrMinCliffLengthChange:
    minCliffLength: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingHrMaxStartDelayChange:
    maxStartDelay: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingHrVestingLengthBoundariesChange:
    minVestingLength: uint256
    maxVestingLength: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingManagerSet:
    contributor: indexed(address)
    manager: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingCancelPaycheckSet:
    contributor: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event RipeCheckCashedFromSwitchboard:
    contributor: indexed(address)
    cashedBy: indexed(address)
    amount: uint256

event RipeTransferCancelledFromSwitchboard:
    contributor: indexed(address)
    cancelledBy: indexed(address)

event OwnershipChangeCancelledFromSwitchboard:
    contributor: indexed(address)
    cancelledBy: indexed(address)

event ContributorFrozenFromSwitchboard:
    contributor: indexed(address)
    frozenBy: indexed(address)
    shouldFreeze: bool

event PendingRipeBondConfigSet:
    asset: indexed(address)
    amountPerEpoch: uint256
    minRipePerUnit: uint256
    maxRipePerUnit: uint256
    maxRipePerUnitLockBonus: uint256
    shouldAutoRestart: bool
    restartDelayBlocks: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingRipeBondEpochLengthSet:
    epochLength: uint256
    confirmationBlock: uint256
    actionId: uint256

event CanPurchaseRipeBondModified:
    canPurchaseRipeBond: bool
    modifier: indexed(address)

event PendingBadDebtSet:
    badDebt: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingBondBoosterSet:
    bondBooster: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingBoosterBoundariesSet:
    maxBoostRatio: uint256
    maxUnits: uint256
    confirmationBlock: uint256
    actionId: uint256

event BoosterMinLockDurationSet:
    minLockDuration: uint256

event PendingBoosterConfigsSet:
    numBoosters: uint256
    confirmationBlock: uint256
    actionId: uint256

event ManyBondBoostersRemoved:
    numUsers: uint256

event BondBoosterRemoved:
    user: indexed(address)

event PendingBoosterConfigSet:
    user: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event HrContribTemplateSet:
    contribTemplate: indexed(address)

event HrMaxCompensationSet:
    maxCompensation: uint256

event HrMinCliffLengthSet:
    minCliffLength: uint256

event HrMaxStartDelaySet:
    maxStartDelay: uint256

event HrVestingLengthBoundariesSet:
    minVestingLength: uint256
    maxVestingLength: uint256

event HrContributorManagerSet:
    contributor: indexed(address)
    manager: indexed(address)

event HrContributorCancelPaycheckSet:
    contributor: indexed(address)

event RipeBondConfigSet:
    asset: indexed(address)
    amountPerEpoch: uint256
    minRipePerUnit: uint256
    maxRipePerUnit: uint256
    maxRipePerUnitLockBonus: uint256
    shouldAutoRestart: bool

event RipeBondEpochLengthSet:
    epochLength: uint256

event RipeBondStartEpochAtBlockSet:
    startBlock: uint256

event BadDebtSet:
    badDebt: uint256

event RipeBondBoosterSet:
    bondBooster: indexed(address)

event ManyBondBoostersSet:
    numBoosters: uint256

event BoosterBoundariesSet:
    maxBoostRatio: uint256
    maxUnits: uint256

event PendingUserBalanceResetSet:
    numResets: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingAssetResetSet:
    numResets: uint256
    confirmationBlock: uint256
    actionId: uint256

event UserBalanceResetExecuted:
    numResets: uint256

event AssetResetExecuted:
    numResets: uint256

event PendingUserBorrowResetSet:
    numResets: uint256
    confirmationBlock: uint256
    actionId: uint256

event UserBorrowResetExecuted:
    numResets: uint256

event PendingRipeAvailableForRewardsChange:
    amount: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingRipeAvailableForHrChange:
    amount: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingRipeAvailableForBondsChange:
    amount: uint256
    confirmationBlock: uint256
    actionId: uint256

event RipeAvailableForRewardsSet:
    amount: uint256

event RipeAvailableForHrSet:
    amount: uint256

event RipeAvailableForBondsSet:
    amount: uint256

event PendingUnderscoreRegistryChange:
    underscoreRegistry: address
    confirmationBlock: uint256
    actionId: uint256

event PendingShouldCheckLastTouchChange:
    shouldCheck: bool
    confirmationBlock: uint256
    actionId: uint256

event UnderscoreRegistrySet:
    addr: indexed(address)

event ShouldCheckLastTouchSet:
    shouldCheck: bool

# pending config changes
actionType: public(HashMap[uint256, ActionType]) # aid -> type
pendingHrConfig: public(HashMap[uint256, cs.HrConfig]) # aid -> config
pendingManager: public(HashMap[uint256, PendingManager]) # aid -> pending manager
pendingCancelPaycheck: public(HashMap[uint256, address]) # aid -> contributor
pendingRipeBondConfig: public(HashMap[uint256, cs.RipeBondConfig]) # aid -> config
pendingRipeBondConfigValue: public(HashMap[uint256, uint256]) # aid -> block
pendingBondBooster: public(HashMap[uint256, address]) # aid -> bond booster
pendingBoosterConfigs: public(HashMap[uint256, DynArray[BoosterConfig, MAX_BOOSTERS]]) # aid -> configs
pendingBoosterBoundaries: public(HashMap[uint256, BoosterBoundaries]) # aid -> boundaries
pendingUserBalanceReset: public(HashMap[uint256, DynArray[UserBalanceReset, MAX_USERS]]) # aid -> users
pendingAssetReset: public(HashMap[uint256, DynArray[AssetReset, MAX_ASSETS]]) # aid -> assets
pendingUserBorrowReset: public(HashMap[uint256, DynArray[address, MAX_USERS]]) # aid -> users
pendingRipeAvailable: public(HashMap[uint256, uint256]) # aid -> amount
pendingUnderscoreRegistry: public(HashMap[uint256, address])
pendingShouldCheckLastTouch: public(HashMap[uint256, bool])
pendingMissionControl: public(HashMap[uint256, address]) # aid -> target mission control

TELLER_ID: constant(uint256) = 3
LEDGER_ID: constant(uint256) = 4
MISSION_CONTROL_ID: constant(uint256) = 5
UNDERSCORE_LEDGER_ID: constant(uint256) = 1
BOND_ROOM_ID: constant(uint256) = 12
LOOTBOX_ID: constant(uint256) = 16
DELEVERAGE_ID: constant(uint256) = 18
EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
MAX_BOOSTERS: constant(uint256) = 50
HUNDRED_PERCENT: constant(uint256) = 100_00
MAX_USERS: constant(uint256) = 40
MAX_ASSETS: constant(uint256) = 20
MAX_DELEVERAGE_USERS: constant(uint256) = 25
MAX_DELEVERAGE_ASSETS: constant(uint256) = 25

# timestamp units (not blocks!)
DAY_IN_SECONDS: constant(uint256) = 60 * 60 * 24
WEEK_IN_SECONDS: constant(uint256) = 7 * DAY_IN_SECONDS
MONTH_IN_SECONDS: constant(uint256) = 30 * DAY_IN_SECONDS
YEAR_IN_SECONDS: constant(uint256) = 365 * DAY_IN_SECONDS


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    timeLock.__init__(_minConfigTimeLock, _maxConfigTimeLock, 0, _maxConfigTimeLock)


# access control


@view
@internal
def _hasPermsToEnable(_caller: address, _isLite: bool) -> bool:
    if gov._canGovern(_caller):
        return True
    if _isLite:
        return staticcall MissionControl(self._getMissionControlAddr()).canPerformLiteAction(_caller)
    return False


# addys lite


@view
@internal
def _getMissionControlAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(MISSION_CONTROL_ID)


@view
@internal
def _resolveMissionControl(_missionControl: address) -> address:
    mc: address = self._getMissionControlAddr()
    if _missionControl == empty(address):
        return mc
    assert _missionControl != mc # dev: use empty for current mission control
    return _missionControl


@view
@internal
def _getLedgerAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(LEDGER_ID)


@view
@internal
def _getTellerAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(TELLER_ID)


@view
@internal
def _getBondRoomAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(BOND_ROOM_ID)


@view
@internal
def _getLootboxAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(LOOTBOX_ID)


##############
# Deleverage #
##############


@external
def deleverageUser(_user: address, _targetRepayAmount: uint256 = max_value(uint256)) -> uint256:
    assert self._hasPermsToEnable(msg.sender, True) # dev: no perms
    return extcall Teller(self._getTellerAddr()).deleverageUser(_user, _targetRepayAmount)


@external
def deleverageManyUsers(_users: DynArray[DeleverageUserRequest, MAX_DELEVERAGE_USERS]) -> uint256:
    assert self._hasPermsToEnable(msg.sender, True) # dev: no perms
    return extcall Teller(self._getTellerAddr()).deleverageManyUsers(_users)


@external
def deleverageWithSpecificAssets(_assets: DynArray[DeleverageAsset, MAX_DELEVERAGE_ASSETS], _user: address) -> uint256:
    assert self._hasPermsToEnable(msg.sender, True) # dev: no perms
    return extcall Teller(self._getTellerAddr()).deleverageWithSpecificAssets(_assets, _user)


@external
def deleverageWithVolAssets(_user: address, _assets: DynArray[DeleverageAsset, MAX_DELEVERAGE_ASSETS]) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    deleverage: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(DELEVERAGE_ID)
    return extcall Deleverage(deleverage).deleverageWithVolAssets(_user, _assets)


#############
# HR Config #
#############


# contrib template


@external
def setContributorTemplate(_contribTemplate: address, _missionControl: address = empty(address)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _contribTemplate.is_contract and _contribTemplate != empty(address) # dev: invalid contrib template
    aid: uint256 = self._setPendingHrConfig(ActionType.HR_CONFIG_TEMPLATE, _contribTemplate)
    self.pendingMissionControl[aid] = self._resolveMissionControl(_missionControl)
    return aid


# max compensation


@external
def setMaxCompensation(_maxComp: uint256, _missionControl: address = empty(address)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _maxComp != 0 and _maxComp <= 20_000_000 * EIGHTEEN_DECIMALS # dev: invalid max compensation
    aid: uint256 = self._setPendingHrConfig(ActionType.HR_CONFIG_MAX_COMP, empty(address), _maxComp)
    self.pendingMissionControl[aid] = self._resolveMissionControl(_missionControl)
    return aid


# min cliff length


@external
def setMinCliffLength(_minCliffLength: uint256, _missionControl: address = empty(address)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _minCliffLength > WEEK_IN_SECONDS # dev: invalid min cliff length
    aid: uint256 = self._setPendingHrConfig(ActionType.HR_CONFIG_MIN_CLIFF, empty(address), 0, _minCliffLength)
    self.pendingMissionControl[aid] = self._resolveMissionControl(_missionControl)
    return aid


# max start delay


@external
def setMaxStartDelay(_maxStartDelay: uint256, _missionControl: address = empty(address)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _maxStartDelay <= 3 * MONTH_IN_SECONDS # dev: invalid max start delay
    aid: uint256 = self._setPendingHrConfig(ActionType.HR_CONFIG_MAX_START_DELAY, empty(address), 0, 0, _maxStartDelay)
    self.pendingMissionControl[aid] = self._resolveMissionControl(_missionControl)
    return aid


# min vesting length


@external
def setVestingLengthBoundaries(_minVestingLength: uint256, _maxVestingLength: uint256, _missionControl: address = empty(address)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _minVestingLength < _maxVestingLength # dev: invalid vesting length boundaries
    assert _minVestingLength > MONTH_IN_SECONDS # dev: invalid min vesting length
    assert _maxVestingLength <= 5 * YEAR_IN_SECONDS # dev: invalid max vesting length
    aid: uint256 = self._setPendingHrConfig(ActionType.HR_CONFIG_VESTING, empty(address), 0, 0, 0, _minVestingLength, _maxVestingLength)
    self.pendingMissionControl[aid] = self._resolveMissionControl(_missionControl)
    return aid


# set pending hr config


@internal
def _setPendingHrConfig(
    _actionType: ActionType,
    _contribTemplate: address = empty(address),
    _maxCompensation: uint256 = 0,
    _minCliffLength: uint256 = 0,
    _maxStartDelay: uint256 = 0,
    _minVestingLength: uint256 = 0,
    _maxVestingLength: uint256 = 0,
) -> uint256:
    aid: uint256 = timeLock._initiateAction()

    self.actionType[aid] = _actionType
    self.pendingHrConfig[aid] = cs.HrConfig(
        contribTemplate=_contribTemplate,
        maxCompensation=_maxCompensation,
        minCliffLength=_minCliffLength,
        maxStartDelay=_maxStartDelay,
        minVestingLength=_minVestingLength,
        maxVestingLength=_maxVestingLength,
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    if _actionType == ActionType.HR_CONFIG_TEMPLATE:
        log PendingHrContribTemplateChange(
            contribTemplate=_contribTemplate,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.HR_CONFIG_MAX_COMP:
        log PendingHrMaxCompensationChange(
            maxCompensation=_maxCompensation,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.HR_CONFIG_MIN_CLIFF:
        log PendingHrMinCliffLengthChange(
            minCliffLength=_minCliffLength,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.HR_CONFIG_MAX_START_DELAY:
        log PendingHrMaxStartDelayChange(
            maxStartDelay=_maxStartDelay,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    elif _actionType == ActionType.HR_CONFIG_VESTING:
        log PendingHrVestingLengthBoundariesChange(
            minVestingLength=_minVestingLength,
            maxVestingLength=_maxVestingLength,
            confirmationBlock=confirmationBlock,
            actionId=aid,
        )
    return aid


#######################
# Contributor Options #
#######################


# cancel paycheck


@external
def cancelPaycheckForContributor(_contributor: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert staticcall Ledger(self._getLedgerAddr()).isHrContributor(_contributor) # dev: not a contributor
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.HR_CANCEL_PAYCHECK
    self.pendingCancelPaycheck[aid] = _contributor
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingCancelPaycheckSet(contributor=_contributor, confirmationBlock=confirmationBlock, actionId=aid)
    return aid


# set manager


@external
def setManagerForContributor(_contributor: address, _manager: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _manager != empty(address) # dev: invalid manager
    assert staticcall Ledger(self._getLedgerAddr()).isHrContributor(_contributor) # dev: not a contributor
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.HR_MANAGER
    self.pendingManager[aid] = PendingManager(contributor=_contributor, pendingManager=_manager)
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingManagerSet(contributor=_contributor, manager=_manager, confirmationBlock=confirmationBlock, actionId=aid)
    return aid


# lite actions


@external
def cashRipeCheckForContributor(_contributor: address) -> bool:
    assert self._hasPermsToEnable(msg.sender, True) # dev: no perms
    amount: uint256 = extcall HrContributor(_contributor).cashRipeCheck()
    log RipeCheckCashedFromSwitchboard(contributor=_contributor, cashedBy=msg.sender, amount=amount)
    return True


@external
def cancelRipeTransferForContributor(_contributor: address) -> bool:
    assert self._hasPermsToEnable(msg.sender, True) # dev: no perms
    extcall HrContributor(_contributor).cancelRipeTransfer()
    log RipeTransferCancelledFromSwitchboard(contributor=_contributor, cancelledBy=msg.sender)
    return True


@external
def cancelOwnershipChangeForContributor(_contributor: address) -> bool:
    assert self._hasPermsToEnable(msg.sender, True) # dev: no perms
    extcall HrContributor(_contributor).cancelOwnershipChange()
    log OwnershipChangeCancelledFromSwitchboard(contributor=_contributor, cancelledBy=msg.sender)
    return True


@external
def freezeContributor(_contributor: address, _shouldFreeze: bool) -> bool:
    assert self._hasPermsToEnable(msg.sender, _shouldFreeze) # dev: no perms
    assert extcall HrContributor(_contributor).setIsFrozen(_shouldFreeze) # dev: could not freeze
    log ContributorFrozenFromSwitchboard(contributor=_contributor, frozenBy=msg.sender, shouldFreeze=_shouldFreeze)
    return True


####################
# Ripe Bond Config #
####################


# main config


@external
def setRipeBondConfig(
    _asset: address,
    _amountPerEpoch: uint256,
    _minRipePerUnit: uint256,
    _maxRipePerUnit: uint256,
    _maxRipePerUnitLockBonus: uint256,
    _shouldAutoRestart: bool,
    _restartDelayBlocks: uint256,
    _missionControl: address = empty(address),
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RIPE_BOND_CONFIG

    assert _asset != empty(address) # dev: invalid asset
    assert 0 not in [_amountPerEpoch, _maxRipePerUnit] # dev: invalid config
    assert _minRipePerUnit < _maxRipePerUnit # dev: invalid min/max ripe per unit
    assert _maxRipePerUnitLockBonus <= (10 * HUNDRED_PERCENT) # dev: max is 1000%

    self.pendingRipeBondConfig[aid] = cs.RipeBondConfig(
        asset=_asset,
        amountPerEpoch=_amountPerEpoch,
        canBond=False,
        minRipePerUnit=_minRipePerUnit,
        maxRipePerUnit=_maxRipePerUnit,
        maxRipePerUnitLockBonus=_maxRipePerUnitLockBonus,
        epochLength=0,
        shouldAutoRestart=_shouldAutoRestart,
        restartDelayBlocks=_restartDelayBlocks,
    )
    self.pendingMissionControl[aid] = self._resolveMissionControl(_missionControl)
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingRipeBondConfigSet(
        asset=_asset,
        amountPerEpoch=_amountPerEpoch,
        minRipePerUnit=_minRipePerUnit,
        maxRipePerUnit=_maxRipePerUnit,
        maxRipePerUnitLockBonus=_maxRipePerUnitLockBonus,
        shouldAutoRestart=_shouldAutoRestart,
        restartDelayBlocks=_restartDelayBlocks,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


# epoch length


@external
def setRipeBondEpochLength(_epochLength: uint256, _missionControl: address = empty(address)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _epochLength != 0 # dev: invalid epoch length
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RIPE_BOND_EPOCH_LENGTH
    self.pendingRipeBondConfigValue[aid] = _epochLength
    self.pendingMissionControl[aid] = self._resolveMissionControl(_missionControl)
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingRipeBondEpochLengthSet(epochLength=_epochLength, confirmationBlock=confirmationBlock, actionId=aid)
    return aid


# start epoch at block


@external
def setStartEpochAtBlock(_block: uint256 = 0):
    assert gov._canGovern(msg.sender) # dev: no perms

    blockNum: uint256 = max(_block, block.number)
    bondRoom: address = self._getBondRoomAddr()
    extcall BondRoom(bondRoom).startBondEpochAtBlock(blockNum)
    log RipeBondStartEpochAtBlockSet(startBlock=blockNum)


# disable / enable bonding


@external
def setCanPurchaseRipeBond(_canBond: bool, _missionControl: address = empty(address)) -> bool:
    assert self._hasPermsToEnable(msg.sender, not _canBond) # dev: no perms
    mc: address = self._resolveMissionControl(_missionControl)
    config: cs.RipeBondConfig = staticcall MissionControl(mc).ripeBondConfig()
    assert config.canBond != _canBond # dev: no change
    config.canBond = _canBond
    extcall MissionControl(mc).setRipeBondConfig(config)
    log CanPurchaseRipeBondModified(canPurchaseRipeBond=_canBond, modifier=msg.sender)
    return True


# set bad debt


@external
def setBadDebt(_amount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RIPE_BAD_DEBT
    self.pendingRipeBondConfigValue[aid] = _amount
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingBadDebtSet(badDebt=_amount, confirmationBlock=confirmationBlock, actionId=aid)
    return aid


##################
# Ripe Available #
##################


@external
def setRipeAvailableForRewards(_amount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RIPE_AVAIL_REWARDS
    self.pendingRipeAvailable[aid] = _amount
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingRipeAvailableForRewardsChange(
        amount=_amount,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


@external
def setRipeAvailableForHr(_amount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RIPE_AVAIL_HR
    self.pendingRipeAvailable[aid] = _amount
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingRipeAvailableForHrChange(
        amount=_amount,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


@external
def setRipeAvailableForBonds(_amount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RIPE_AVAIL_BONDS
    self.pendingRipeAvailable[aid] = _amount
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingRipeAvailableForBondsChange(
        amount=_amount,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


#######################
# Underscore Registry #
#######################


@external
def setUnderscoreRegistry(_underscoreRegistry: address, _missionControl: address = empty(address)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert self._isValidUnderscoreAddr(_underscoreRegistry) # dev: invalid underscore registry

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.OTHER_UNDERSCORE_REGISTRY
    self.pendingUnderscoreRegistry[aid] = _underscoreRegistry
    self.pendingMissionControl[aid] = self._resolveMissionControl(_missionControl)
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingUnderscoreRegistryChange(
        underscoreRegistry=_underscoreRegistry,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


@view
@internal
def _isValidUnderscoreAddr(_addr: address) -> bool:
    if _addr == empty(address):
        return True # allowing setting to empty address

    undyLedger: address = staticcall UnderscoreRegistry(_addr).getAddr(UNDERSCORE_LEDGER_ID)
    if undyLedger == empty(address):
        return False

    # make sure has interface
    return not staticcall UnderscoreLedger(undyLedger).isUserWallet(empty(address))


###########################
# Should Check Last Touch #
###########################


@external
def setShouldCheckLastTouch(_shouldCheck: bool, _missionControl: address = empty(address)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.OTHER_SHOULD_CHECK_LAST_TOUCH
    self.pendingShouldCheckLastTouch[aid] = _shouldCheck
    self.pendingMissionControl[aid] = self._resolveMissionControl(_missionControl)
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingShouldCheckLastTouchChange(shouldCheck=_shouldCheck, confirmationBlock=confirmationBlock, actionId=aid)
    return aid


################
# Bond Booster #
################


# setting bond booster contract


@external
def setRipeBondBooster(_bondBooster: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert self._isValidRipeBondBoosterAddr(_bondBooster) # dev: invalid bond booster

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RIPE_BOND_BOOSTER
    self.pendingBondBooster[aid] = _bondBooster
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingBondBoosterSet(
        bondBooster=_bondBooster,
        confirmationBlock=confirmationBlock,
        actionId=aid,
    )
    return aid


@view
@internal
def _isValidRipeBondBoosterAddr(_addr: address) -> bool:
    # make sure has interface
    if _addr != empty(address):
        na: uint256 = staticcall BondBooster(_addr).getBoostRatio(empty(address), 10)
    return True


# add booster configs


@external
def setManyBondBoosters(_boosters: DynArray[BoosterConfig, MAX_BOOSTERS]) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert len(_boosters) != 0 # dev: no boosters
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.BOND_BOOSTER_ADD
    self.pendingBoosterConfigs[aid] = _boosters
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingBoosterConfigsSet(numBoosters=len(_boosters), confirmationBlock=confirmationBlock, actionId=aid)
    return aid


# add single booster config


@external
def setBondBooster(_config: BoosterConfig) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.BOND_BOOSTER_ADD
    self.pendingBoosterConfigs[aid] = [_config]
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingBoosterConfigSet(user=_config.user, confirmationBlock=confirmationBlock, actionId=aid)
    return aid


# remove boosted users


@external
def removeManyBondBoosters(_users: DynArray[address, MAX_BOOSTERS]) -> bool:
    assert self._hasPermsToEnable(msg.sender, True) # dev: no perms
    bondBooster: address = staticcall BondRoom(self._getBondRoomAddr()).bondBooster()
    extcall BondBooster(bondBooster).removeManyBondBoosters(_users)
    log ManyBondBoostersRemoved(numUsers=len(_users))
    return True


# remove single boosted user


@external
def removeBondBooster(_user: address) -> bool:
    assert self._hasPermsToEnable(msg.sender, True) # dev: no perms
    bondBooster: address = staticcall BondRoom(self._getBondRoomAddr()).bondBooster()
    extcall BondBooster(bondBooster).removeBondBooster(_user)
    log BondBoosterRemoved(user=_user)
    return True


# set booster boundaries


@external
def setBoosterBoundaries(_maxBoostRatio: uint256, _maxUnits: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.BOND_BOOSTER_BOUNDARIES
    self.pendingBoosterBoundaries[aid] = BoosterBoundaries(maxBoostRatio=_maxBoostRatio, maxUnits=_maxUnits)
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingBoosterBoundariesSet(maxBoostRatio=_maxBoostRatio, maxUnits=_maxUnits, confirmationBlock=confirmationBlock, actionId=aid)
    return aid


# set booster min lock duration


@external
def setBoosterMinLockDuration(_minLockDuration: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    bondBooster: address = staticcall BondRoom(self._getBondRoomAddr()).bondBooster()
    extcall BondBooster(bondBooster).setMinLockDuration(_minLockDuration)
    log BoosterMinLockDurationSet(minLockDuration=_minLockDuration)
    return True


################
# Loot Cleanup #
################


@external
def resetManyUserBalancePoints(_users: DynArray[UserBalanceReset, MAX_USERS]) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert len(_users) != 0 # dev: no users
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.LOOT_USER_BALANCE_RESET
    self.pendingUserBalanceReset[aid] = _users
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingUserBalanceResetSet(numResets=len(_users), confirmationBlock=confirmationBlock, actionId=aid)
    return aid


@external
def resetManyAssetPoints(_assets: DynArray[AssetReset, MAX_ASSETS]) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert len(_assets) != 0 # dev: no assets
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.LOOT_ASSET_RESET
    self.pendingAssetReset[aid] = _assets
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingAssetResetSet(numResets=len(_assets), confirmationBlock=confirmationBlock, actionId=aid)
    return aid


@external
def resetManyUserBorrowPoints(_users: DynArray[address, MAX_USERS]) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert len(_users) != 0 # dev: no users
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.LOOT_USER_BORROW_RESET
    self.pendingUserBorrowReset[aid] = _users
    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingUserBorrowResetSet(numResets=len(_users), confirmationBlock=confirmationBlock, actionId=aid)
    return aid


#############
# Execution #
#############


@external
def executePendingAction(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    # check time lock
    if not timeLock._confirmAction(_aid):
        if timeLock._isExpired(_aid):
            self._cancelPendingAction(_aid)
        return False

    actionType: ActionType = self.actionType[_aid]

    # use stored MC if set, otherwise fallback to current (for backwards compat)
    mc: address = self.pendingMissionControl[_aid]
    if mc == empty(address):
        mc = self._getMissionControlAddr()

    if actionType == ActionType.HR_CONFIG_TEMPLATE:
        config: cs.HrConfig = staticcall MissionControl(mc).hrConfig()
        config.contribTemplate = self.pendingHrConfig[_aid].contribTemplate
        extcall MissionControl(mc).setHrConfig(config)
        log HrContribTemplateSet(contribTemplate=config.contribTemplate)

    elif actionType == ActionType.HR_CONFIG_MAX_COMP:
        config: cs.HrConfig = staticcall MissionControl(mc).hrConfig()
        p: cs.HrConfig = self.pendingHrConfig[_aid]
        config.maxCompensation = p.maxCompensation
        extcall MissionControl(mc).setHrConfig(config)
        log HrMaxCompensationSet(maxCompensation=p.maxCompensation)

    elif actionType == ActionType.HR_CONFIG_MIN_CLIFF:
        config: cs.HrConfig = staticcall MissionControl(mc).hrConfig()
        p: cs.HrConfig = self.pendingHrConfig[_aid]
        config.minCliffLength = p.minCliffLength
        extcall MissionControl(mc).setHrConfig(config)
        log HrMinCliffLengthSet(minCliffLength=p.minCliffLength)

    elif actionType == ActionType.HR_CONFIG_MAX_START_DELAY:
        config: cs.HrConfig = staticcall MissionControl(mc).hrConfig()
        p: cs.HrConfig = self.pendingHrConfig[_aid]
        config.maxStartDelay = p.maxStartDelay
        extcall MissionControl(mc).setHrConfig(config)
        log HrMaxStartDelaySet(maxStartDelay=p.maxStartDelay)

    elif actionType == ActionType.HR_CONFIG_VESTING:
        config: cs.HrConfig = staticcall MissionControl(mc).hrConfig()
        p: cs.HrConfig = self.pendingHrConfig[_aid]
        config.minVestingLength = p.minVestingLength
        config.maxVestingLength = p.maxVestingLength
        extcall MissionControl(mc).setHrConfig(config)
        log HrVestingLengthBoundariesSet(minVestingLength=p.minVestingLength, maxVestingLength=p.maxVestingLength)

    elif actionType == ActionType.HR_MANAGER:
        p: PendingManager = self.pendingManager[_aid]
        extcall HrContributor(p.contributor).setManager(p.pendingManager)
        log HrContributorManagerSet(contributor=p.contributor, manager=p.pendingManager)

    elif actionType == ActionType.HR_CANCEL_PAYCHECK:
        p: address = self.pendingCancelPaycheck[_aid]
        extcall HrContributor(p).cancelPaycheck()
        log HrContributorCancelPaycheckSet(contributor=p)

    elif actionType == ActionType.RIPE_BOND_CONFIG:
        p: cs.RipeBondConfig = self.pendingRipeBondConfig[_aid]
        config: cs.RipeBondConfig = staticcall MissionControl(mc).ripeBondConfig()
        config.asset = p.asset
        config.amountPerEpoch = p.amountPerEpoch
        config.minRipePerUnit = p.minRipePerUnit
        config.maxRipePerUnit = p.maxRipePerUnit
        config.maxRipePerUnitLockBonus = p.maxRipePerUnitLockBonus
        config.shouldAutoRestart = p.shouldAutoRestart
        config.restartDelayBlocks = p.restartDelayBlocks
        extcall MissionControl(mc).setRipeBondConfig(config)
        log RipeBondConfigSet(asset=p.asset, amountPerEpoch=p.amountPerEpoch, minRipePerUnit=p.minRipePerUnit, maxRipePerUnit=p.maxRipePerUnit, maxRipePerUnitLockBonus=p.maxRipePerUnitLockBonus, shouldAutoRestart=p.shouldAutoRestart)

    elif actionType == ActionType.RIPE_BOND_EPOCH_LENGTH:
        config: cs.RipeBondConfig = staticcall MissionControl(mc).ripeBondConfig()
        config.epochLength = self.pendingRipeBondConfigValue[_aid]
        extcall MissionControl(mc).setRipeBondConfig(config)
        log RipeBondEpochLengthSet(epochLength=config.epochLength)

    elif actionType == ActionType.RIPE_BAD_DEBT:
        amount: uint256 = self.pendingRipeBondConfigValue[_aid]
        extcall Ledger(self._getLedgerAddr()).setBadDebt(amount)
        log BadDebtSet(badDebt=amount)

    elif actionType == ActionType.RIPE_BOND_BOOSTER:
        bondBooster: address = self.pendingBondBooster[_aid]
        extcall BondRoom(self._getBondRoomAddr()).setBondBooster(bondBooster)
        log RipeBondBoosterSet(bondBooster=bondBooster)

    elif actionType == ActionType.BOND_BOOSTER_ADD:
        boosters: DynArray[BoosterConfig, MAX_BOOSTERS] = self.pendingBoosterConfigs[_aid]
        bondBooster: address = staticcall BondRoom(self._getBondRoomAddr()).bondBooster()
        extcall BondBooster(bondBooster).setManyBondBoosters(boosters)
        log ManyBondBoostersSet(numBoosters=len(boosters))

    elif actionType == ActionType.BOND_BOOSTER_BOUNDARIES:
        boundaries: BoosterBoundaries = self.pendingBoosterBoundaries[_aid]
        bondBooster: address = staticcall BondRoom(self._getBondRoomAddr()).bondBooster()
        extcall BondBooster(bondBooster).setMaxBoostAndMaxUnits(boundaries.maxBoostRatio, boundaries.maxUnits)
        log BoosterBoundariesSet(maxBoostRatio=boundaries.maxBoostRatio, maxUnits=boundaries.maxUnits)

    elif actionType == ActionType.LOOT_USER_BALANCE_RESET:
        resets: DynArray[UserBalanceReset, MAX_USERS] = self.pendingUserBalanceReset[_aid]
        lootbox: address = self._getLootboxAddr()
        for reset: UserBalanceReset in resets:
            extcall Lootbox(lootbox).resetUserBalancePoints(reset.user, reset.asset, reset.vaultId)
        log UserBalanceResetExecuted(numResets=len(resets))

    elif actionType == ActionType.LOOT_ASSET_RESET:
        resets: DynArray[AssetReset, MAX_ASSETS] = self.pendingAssetReset[_aid]
        lootbox: address = self._getLootboxAddr()
        for reset: AssetReset in resets:
            extcall Lootbox(lootbox).resetAssetPoints(reset.asset, reset.vaultId)
        log AssetResetExecuted(numResets=len(resets))

    elif actionType == ActionType.LOOT_USER_BORROW_RESET:
        users: DynArray[address, MAX_USERS] = self.pendingUserBorrowReset[_aid]
        lootbox: address = self._getLootboxAddr()
        for user: address in users:
            extcall Lootbox(lootbox).resetUserBorrowPoints(user)
        log UserBorrowResetExecuted(numResets=len(users))

    elif actionType == ActionType.RIPE_AVAIL_REWARDS:
        amount: uint256 = self.pendingRipeAvailable[_aid]
        extcall Ledger(self._getLedgerAddr()).setRipeAvailForRewards(amount)
        log RipeAvailableForRewardsSet(amount=amount)

    elif actionType == ActionType.RIPE_AVAIL_HR:
        amount: uint256 = self.pendingRipeAvailable[_aid]
        extcall Ledger(self._getLedgerAddr()).setRipeAvailForHr(amount)
        log RipeAvailableForHrSet(amount=amount)

    elif actionType == ActionType.RIPE_AVAIL_BONDS:
        amount: uint256 = self.pendingRipeAvailable[_aid]
        extcall Ledger(self._getLedgerAddr()).setRipeAvailForBonds(amount)
        log RipeAvailableForBondsSet(amount=amount)

    elif actionType == ActionType.OTHER_UNDERSCORE_REGISTRY:
        underscoreRegistry: address = self.pendingUnderscoreRegistry[_aid]
        extcall MissionControl(mc).setUnderscoreRegistry(underscoreRegistry)
        log UnderscoreRegistrySet(addr=underscoreRegistry)

    elif actionType == ActionType.OTHER_SHOULD_CHECK_LAST_TOUCH:
        shouldCheck: bool = self.pendingShouldCheckLastTouch[_aid]
        extcall MissionControl(mc).setShouldCheckLastTouch(shouldCheck)
        log ShouldCheckLastTouchSet(shouldCheck=shouldCheck)

    self.actionType[_aid] = empty(ActionType)
    return True


# cancel action


@external
def cancelPendingAction(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    self._cancelPendingAction(_aid)
    return True


@internal
def _cancelPendingAction(_aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.actionType[_aid] = empty(ActionType)
