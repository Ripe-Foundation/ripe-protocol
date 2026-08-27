# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026

# @version 0.4.3
# pragma optimize codesize

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock

struct VaultAssetReward:
    vaultId: uint256
    vaultAddr: address
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    fundGenPoints: bool
    retired: bool

struct AssetDepositPoints:
    balancePoints: uint256
    lastBalance: uint256
    lastUsdValue: uint256
    ripeStakerPoints: uint256
    ripeVotePoints: uint256
    ripeGenPoints: uint256
    lastUpdate: uint256
    precision: uint256

struct PendingRewardPairAction:
    asset: address
    targetPair: VaultAssetReward
    expectedPair: VaultAssetReward

interface MissionControl:
    def setRewardGov(_rewardGov: address): nonpayable
    def setRewardPair(_asset: address, _pair: VaultAssetReward): nonpayable
    def retireRewardPair(_asset: address, _vaultId: uint256): nonpayable
    def getRewardPair(_asset: address, _vaultId: uint256) -> VaultAssetReward: view
    def rewardPairAt(_asset: address, _index: uint256) -> VaultAssetReward: view
    def getPinnedVaultAddr(_vaultId: uint256) -> address: view
    def numRewardPairs(_asset: address) -> uint256: view
    def isSupportedAsset(_asset: address) -> bool: view
    def canPerformLiteAction(_user: address) -> bool: view

interface Lootbox:
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address): nonpayable

interface Ledger:
    def assetDepositPoints(_vaultId: uint256, _asset: address) -> AssetDepositPoints: view

interface VaultBook:
    def getAddr(_regId: uint256) -> address: view

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

flag ActionType:
    ADD_REWARD_PAIR
    UPDATE_REWARD_PAIR
    RETIRE_REWARD_PAIR

event RewardGovInitialized:
    missionControl: indexed(address)
    rewardGov: indexed(address)
    caller: indexed(address)

event PendingRewardPairChange:
    asset: indexed(address)
    vaultId: indexed(uint256)
    vaultAddr: indexed(address)
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    fundGenPoints: bool
    retired: bool
    caller: address
    confirmationBlock: uint256
    actionId: uint256

event RewardPairChanged:
    asset: indexed(address)
    vaultId: indexed(uint256)
    vaultAddr: indexed(address)
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    fundGenPoints: bool
    retired: bool
    caller: address

event RewardPairCheckpointed:
    asset: indexed(address)
    vaultId: indexed(uint256)
    vaultAddr: indexed(address)
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    fundGenPoints: bool
    retired: bool
    caller: address

actionType: public(HashMap[uint256, ActionType])
pendingRewardPair: HashMap[uint256, PendingRewardPairAction]
pendingMissionControl: public(HashMap[uint256, address])

MAX_REWARD_PAIRS_PER_ASSET: constant(uint256) = 20

LEDGER_ID: constant(uint256) = 4
MISSION_CONTROL_ID: constant(uint256) = 5
# Switchboard registry ID: Alpha=1 through Foxtrot=6 on Robinhood.
SWITCHBOARD_GOLF_ID: constant(uint256) = 7
VAULT_BOOK_ID: constant(uint256) = 8
LOOTBOX_ID: constant(uint256) = 16


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    timeLock.__init__(_minConfigTimeLock, _maxConfigTimeLock, 0, _maxConfigTimeLock)


# addresses


@view
@internal
def _hqAddr(_id: uint256) -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(_id)


@view
@internal
def _getMissionControlAddr() -> address:
    return self._hqAddr(MISSION_CONTROL_ID)


@view
@internal
def _hasCheckpointPerms(_caller: address) -> bool:
    if gov._canGovern(_caller):
        return True
    mc: address = self._getMissionControlAddr()
    return mc != empty(address) and staticcall MissionControl(mc).canPerformLiteAction(_caller)


# setup


@external
def initializeRewardGov() -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    mc: address = self._getMissionControlAddr()
    assert mc != empty(address) # dev: invalid mission control
    extcall MissionControl(mc).setRewardGov(self)
    log RewardGovInitialized(missionControl=mc, rewardGov=self, caller=msg.sender)
    return True


# pair helpers


@pure
@internal
def _samePair(_a: VaultAssetReward, _b: VaultAssetReward) -> bool:
    return (
        _a.vaultId == _b.vaultId
        and _a.vaultAddr == _b.vaultAddr
        and _a.stakersPointsAlloc == _b.stakersPointsAlloc
        and _a.voterPointsAlloc == _b.voterPointsAlloc
        and _a.fundGenPoints == _b.fundGenPoints
        and _a.retired == _b.retired
    )


@pure
@internal
def _isRaisingPolicy(_old: VaultAssetReward, _new: VaultAssetReward) -> bool:
    return (
        _new.stakersPointsAlloc > _old.stakersPointsAlloc
        or _new.voterPointsAlloc > _old.voterPointsAlloc
        or (_new.fundGenPoints and not _old.fundGenPoints)
    )


@pure
@internal
def _needsPostCheckpoint(_old: VaultAssetReward, _new: VaultAssetReward) -> bool:
    return (
        _old.fundGenPoints != _new.fundGenPoints
        or (_old.stakersPointsAlloc == 0) != (_new.stakersPointsAlloc == 0)
        or (_old.voterPointsAlloc == 0) != (_new.voterPointsAlloc == 0)
    )


@internal
def _checkpoint(_asset: address, _pair: VaultAssetReward):
    extcall Lootbox(self._hqAddr(LOOTBOX_ID)).updateDepositPoints(empty(address), _pair.vaultId, _pair.vaultAddr, _asset)


@internal
def _logCheckpoint(_asset: address, _pair: VaultAssetReward, _caller: address):
    log RewardPairCheckpointed(
        asset=_asset,
        vaultId=_pair.vaultId,
        vaultAddr=_pair.vaultAddr,
        stakersPointsAlloc=_pair.stakersPointsAlloc,
        voterPointsAlloc=_pair.voterPointsAlloc,
        fundGenPoints=_pair.fundGenPoints,
        retired=_pair.retired,
        caller=_caller,
    )


@internal
def _queueRewardPairChange(
    _actionType: ActionType,
    _asset: address,
    _targetPair: VaultAssetReward,
    _expectedPair: VaultAssetReward,
) -> uint256:
    mc: address = self._getMissionControlAddr()
    assert mc != empty(address) # dev: invalid mission control
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = _actionType
    self.pendingRewardPair[aid] = PendingRewardPairAction(
        asset=_asset,
        targetPair=_targetPair,
        expectedPair=_expectedPair,
    )
    self.pendingMissionControl[aid] = mc
    log PendingRewardPairChange(
        asset=_asset,
        vaultId=_targetPair.vaultId,
        vaultAddr=_targetPair.vaultAddr,
        stakersPointsAlloc=_targetPair.stakersPointsAlloc,
        voterPointsAlloc=_targetPair.voterPointsAlloc,
        fundGenPoints=_targetPair.fundGenPoints,
        retired=_targetPair.retired,
        caller=msg.sender,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return aid


# pair actions


@external
def addRewardPair(_asset: address, _vaultId: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _vaultId != 0 # dev: invalid vault id
    mc: address = self._getMissionControlAddr()
    assert staticcall MissionControl(mc).isSupportedAsset(_asset) # dev: invalid asset
    expectedPair: VaultAssetReward = staticcall MissionControl(mc).getRewardPair(_asset, _vaultId)
    assert expectedPair.vaultId == 0 # dev: reward pair exists

    vaultAddr: address = staticcall VaultBook(self._hqAddr(VAULT_BOOK_ID)).getAddr(_vaultId)
    assert vaultAddr != empty(address) and vaultAddr.is_contract # dev: invalid vault
    targetPair: VaultAssetReward = VaultAssetReward(
        vaultId=_vaultId,
        vaultAddr=vaultAddr,
        stakersPointsAlloc=0,
        voterPointsAlloc=0,
        fundGenPoints=False,
        retired=False,
    )
    return self._queueRewardPairChange(ActionType.ADD_REWARD_PAIR, _asset, targetPair, expectedPair)


@external
def updateRewardPair(
    _asset: address,
    _vaultId: uint256,
    _stakersPointsAlloc: uint256,
    _voterPointsAlloc: uint256,
    _fundGenPoints: bool,
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    mc: address = self._getMissionControlAddr()
    currentPair: VaultAssetReward = staticcall MissionControl(mc).getRewardPair(_asset, _vaultId)
    assert currentPair.vaultId == _vaultId and not currentPair.retired # dev: invalid reward pair
    targetPair: VaultAssetReward = currentPair
    targetPair.stakersPointsAlloc = _stakersPointsAlloc
    targetPair.voterPointsAlloc = _voterPointsAlloc
    targetPair.fundGenPoints = _fundGenPoints
    assert not self._samePair(currentPair, targetPair) # dev: no change
    return self._queueRewardPairChange(ActionType.UPDATE_REWARD_PAIR, _asset, targetPair, currentPair)


@external
def retireRewardPair(_asset: address, _vaultId: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    mc: address = self._getMissionControlAddr()
    currentPair: VaultAssetReward = staticcall MissionControl(mc).getRewardPair(_asset, _vaultId)
    assert currentPair.vaultId == _vaultId and not currentPair.retired # dev: invalid reward pair
    targetPair: VaultAssetReward = currentPair
    targetPair.stakersPointsAlloc = 0
    targetPair.voterPointsAlloc = 0
    targetPair.fundGenPoints = False
    targetPair.retired = True
    return self._queueRewardPairChange(ActionType.RETIRE_REWARD_PAIR, _asset, targetPair, currentPair)


# execution


@internal
def _executeRewardPairUpdate(_mc: address, _pending: PendingRewardPairAction):
    oldPair: VaultAssetReward = _pending.expectedPair
    targetPair: VaultAssetReward = _pending.targetPair
    row: AssetDepositPoints = staticcall Ledger(self._hqAddr(LEDGER_ID)).assetDepositPoints(oldPair.vaultId, _pending.asset)
    needsZeroInit: bool = row.lastUpdate == 0 and self._isRaisingPolicy(oldPair, targetPair)

    self._checkpoint(_pending.asset, oldPair)

    previousPair: VaultAssetReward = oldPair
    if needsZeroInit:
        zeroPair: VaultAssetReward = oldPair
        zeroPair.stakersPointsAlloc = 0
        zeroPair.voterPointsAlloc = 0
        zeroPair.fundGenPoints = False
        extcall MissionControl(_mc).setRewardPair(_pending.asset, zeroPair)
        self._checkpoint(_pending.asset, zeroPair)
        previousPair = zeroPair

    extcall MissionControl(_mc).setRewardPair(_pending.asset, targetPair)
    if self._needsPostCheckpoint(previousPair, targetPair):
        self._checkpoint(_pending.asset, targetPair)


@external
def executePendingAction(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    if not timeLock._confirmAction(_aid):
        if timeLock._isExpired(_aid):
            self._cancelPendingAction(_aid)
        return False

    action: ActionType = self.actionType[_aid]
    pending: PendingRewardPairAction = self.pendingRewardPair[_aid]
    mc: address = self.pendingMissionControl[_aid]
    assert mc == self._getMissionControlAddr() # dev: not current mission control
    currentPair: VaultAssetReward = staticcall MissionControl(mc).getRewardPair(pending.asset, pending.targetPair.vaultId)
    assert self._samePair(currentPair, pending.expectedPair) # dev: stale reward pair

    if action == ActionType.ADD_REWARD_PAIR:
        extcall MissionControl(mc).setRewardPair(pending.asset, pending.targetPair)
    elif action == ActionType.UPDATE_REWARD_PAIR:
        self._executeRewardPairUpdate(mc, pending)
    elif action == ActionType.RETIRE_REWARD_PAIR:
        self._checkpoint(pending.asset, pending.expectedPair)
        extcall MissionControl(mc).retireRewardPair(pending.asset, pending.targetPair.vaultId)
        self._checkpoint(pending.asset, pending.targetPair)
    else:
        raise "invalid action"

    log RewardPairChanged(
        asset=pending.asset,
        vaultId=pending.targetPair.vaultId,
        vaultAddr=pending.targetPair.vaultAddr,
        stakersPointsAlloc=pending.targetPair.stakersPointsAlloc,
        voterPointsAlloc=pending.targetPair.voterPointsAlloc,
        fundGenPoints=pending.targetPair.fundGenPoints,
        retired=pending.targetPair.retired,
        caller=msg.sender,
    )
    self._clearPendingAction(_aid)
    return True


@external
def cancelPendingAction(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    self._cancelPendingAction(_aid)
    return True


@internal
def _cancelPendingAction(_aid: uint256):
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self._clearPendingAction(_aid)


@internal
def _clearPendingAction(_aid: uint256):
    self.actionType[_aid] = empty(ActionType)
    self.pendingRewardPair[_aid] = empty(PendingRewardPairAction)
    self.pendingMissionControl[_aid] = empty(address)


# checkpoints


@external
def checkpointAsset(
    _asset: address,
    _start: uint256 = 0,
    _limit: uint256 = MAX_REWARD_PAIRS_PER_ASSET,
) -> uint256:
    assert self._hasCheckpointPerms(msg.sender) # dev: no perms
    assert _limit != 0 and _limit <= MAX_REWARD_PAIRS_PER_ASSET # dev: invalid limit
    assert _start <= max_value(uint256) - _limit # dev: invalid range

    mc: address = self._getMissionControlAddr()
    numPairs: uint256 = staticcall MissionControl(mc).numRewardPairs(_asset)
    if _start >= numPairs:
        return 0
    end: uint256 = min(numPairs, _start + _limit)
    numCheckpointed: uint256 = 0
    for i: uint256 in range(_start, end, bound=MAX_REWARD_PAIRS_PER_ASSET):
        pair: VaultAssetReward = staticcall MissionControl(mc).rewardPairAt(_asset, i)
        if pair.retired:
            continue
        self._checkpoint(_asset, pair)
        self._logCheckpoint(_asset, pair, msg.sender)
        numCheckpointed += 1
    return numCheckpointed


@external
def checkpointRowAt(_asset: address, _vaultId: uint256, _vaultAddr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _vaultId != 0 and _vaultAddr != empty(address) and _vaultAddr.is_contract # dev: invalid vault
    mc: address = self._getMissionControlAddr()
    pinnedAddr: address = staticcall MissionControl(mc).getPinnedVaultAddr(_vaultId)
    if pinnedAddr != empty(address):
        assert _vaultAddr == pinnedAddr # dev: vault addr mismatch
    else:
        # This PR does not reopen the empty-book governor-trust recovery path.
        bookAddr: address = staticcall VaultBook(self._hqAddr(VAULT_BOOK_ID)).getAddr(_vaultId)
        assert bookAddr != empty(address) and _vaultAddr == bookAddr # dev: vault addr mismatch

    pair: VaultAssetReward = staticcall MissionControl(mc).getRewardPair(_asset, _vaultId)
    extcall Lootbox(self._hqAddr(LOOTBOX_ID)).updateDepositPoints(empty(address), _vaultId, _vaultAddr, _asset)
    log RewardPairCheckpointed(
        asset=_asset,
        vaultId=_vaultId,
        vaultAddr=_vaultAddr,
        stakersPointsAlloc=pair.stakersPointsAlloc,
        voterPointsAlloc=pair.voterPointsAlloc,
        fundGenPoints=pair.fundGenPoints,
        retired=pair.retired,
        caller=msg.sender,
    )
    return True
