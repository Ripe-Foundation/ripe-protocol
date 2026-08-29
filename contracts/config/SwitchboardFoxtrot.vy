#        ______   __     __   __   ______  ______   __  __   ______   ______   ______   ______   _____
#       /\  ___\ /\ \  _ \ \ /\ \ /\__  _\/\  ___\ /\ \_\ \ /\  == \ /\  __ \ /\  __ \ /\  == \ /\  __-.
#       \ \___  \\ \ \/ ".\ \\ \ \\/_/\ \/\ \ \____\ \  __ \\ \  __< \ \ \/\ \\ \  __ \\ \  __< \ \ \/\ \
#        \/\_____\\ \__/".~\_\\ \_\  \ \_\ \ \_____\\ \_\ \_\\ \_____\\ \_____\\ \_\ \_\\ \_\ \_\\ \____-
#         \/_____/ \/_/   \/_/ \/_/   \/_/  \/_____/ \/_/\/_/ \/_____/ \/_____/ \/_/\/_/ \/_/ /_/ \/____/
#                                    ╔═╗┌─┐─┐ ┬┌┬┐┬─┐┌─┐┌┬┐
#                                    ╠╣ │ │┌┴┬┘ │ ├┬┘│ │ │
#                                    ╚  └─┘┴ └─ ┴ ┴└─└─┘ ┴
#
#      Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#      Ripe Foundation (C) 2026

# @version 0.4.3

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock
import interfaces.ConfigStructs as cs

interface RipeReserveEngine:
    def setRateOverride(_targetBasePayoutRate: uint256, _targetEpoch: uint256) -> uint256: nonpayable
    def isValidRateOverride(_targetBasePayoutRate: uint256, _targetEpoch: uint256) -> bool: view
    def start(_genesisBlock: uint256, _epochLength: uint256): nonpayable
    def isValidConfig(_config: ReserveEngineConfig) -> bool: view
    def isValidEpochLength(_epochLength: uint256) -> bool: view
    def setConfig(_newConfig: ReserveEngineConfig): nonpayable
    def setCanAcquireRipe(_canAcquireRipe: bool): nonpayable
    def isValidPaymentToken(_token: address) -> bool: view
    def overrideTargetBasePayoutRate() -> uint256: view
    def setPaymentToken(_token: address): nonpayable
    def engineConfig() -> ReserveEngineConfig: view
    def overrideTargetEpoch() -> uint256: view
    def cancelRateOverride(): nonpayable
    def genesisBlock() -> uint256: view
    def canAcquireRipe() -> bool: view
    def isRunning() -> bool: view
    def stop(): nonpayable

interface RipeReserveVesting:
    def setRemainingAllocationBudget(_amount: uint256): nonpayable

interface AuctionHouse:
    def startManyAuctions(_auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS]) -> uint256: nonpayable
    def pauseManyAuctions(_auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS]) -> uint256: nonpayable
    def pauseAuction(_liqUser: address, _liqVaultId: uint256, _liqAsset: address) -> bool: nonpayable
    def startAuction(_liqUser: address, _liqVaultId: uint256, _liqAsset: address) -> bool: nonpayable
    def canStartAuction(_liqUser: address, _liqVaultId: uint256, _liqAsset: address) -> bool: view

interface MissionControl:
    def setAccrualStartBlock(_asset: address, _vaultId: uint256, _startBlock: uint256): nonpayable
    def assetConfig(_asset: address) -> cs.AssetConfig: view
    def isSupportedAssetInVault(_vaultId: uint256, _asset: address) -> bool: view
    def isSupportedAsset(_asset: address) -> bool: view
    def canPerformLiteAction(_user: address) -> bool: view
    def rewardVaultId(_asset: address) -> uint256: view
    def accrualStartBlock(_asset: address, _vaultId: uint256) -> uint256: view

interface Ledger:
    def globalDepositPoints() -> GlobalDepositPoints: view
    def assetDepositPoints(_vaultId: uint256, _asset: address) -> AssetDepositPoints: view

interface PriceDesk:
    def getAddr(_regId: uint256) -> address: view

interface CurvePrices:
    def addGreenRefPoolSnapshot() -> bool: nonpayable

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

flag ActionType:
    RESERVE_ENGINE_CONFIG
    RESERVE_VESTING_ALLOCATION_BUDGET_SET
    START_AUCTION
    START_MANY_AUCTIONS
    PAUSE_AUCTION
    PAUSE_MANY_AUCTIONS
    SET_ACCRUAL_CLOCK_ARMED

struct GlobalDepositPoints:
    lastUsdValue: uint256
    ripeStakerPoints: uint256
    ripeVotePoints: uint256
    ripeGenPoints: uint256
    lastUpdate: uint256

struct AssetDepositPoints:
    balancePoints: uint256
    lastBalance: uint256
    lastUsdValue: uint256
    ripeStakerPoints: uint256
    ripeVotePoints: uint256
    ripeGenPoints: uint256
    lastUpdate: uint256
    precision: uint256

struct ReserveEngineConfig:
    paymentCapPerEpoch: uint256
    minPaymentAmount: uint256
    maxAllInPayoutRate: uint256
    seedBasePayoutRate: uint256
    uHighBps: uint256
    uLowBps: uint256
    minUpBps: uint256
    maxUpBps: uint256
    minDownBps: uint256
    maxDownBps: uint256
    decayBps: uint256
    maxDecayEpochs: uint256
    maxVestingBonus: uint256
    minVestingLength: uint256
    maxVestingLength: uint256
    epochLength: uint256

struct FungAuctionConfig:
    liqUser: address
    vaultId: uint256
    asset: address

struct AccrualClockUpdate:
    asset: address
    vaultId: uint256
    shouldArm: bool
    missionControl: address

event PendingReserveEngineConfigSet:
    actionId: uint256
    confirmationBlock: uint256
    paymentCapPerEpoch: uint256
    minPaymentAmount: uint256
    maxAllInPayoutRate: uint256
    seedBasePayoutRate: uint256
    uHighBps: uint256
    uLowBps: uint256
    minUpBps: uint256
    maxUpBps: uint256
    minDownBps: uint256
    maxDownBps: uint256
    decayBps: uint256
    maxDecayEpochs: uint256
    maxVestingBonus: uint256
    minVestingLength: uint256
    maxVestingLength: uint256
    epochLength: uint256

event ReserveEngineConfigExecuted:
    actionId: uint256

event PendingReserveVestingAllocationBudgetSet:
    actionId: uint256
    confirmationBlock: uint256
    amount: uint256

event ReserveVestingAllocationBudgetExecuted:
    actionId: uint256

event ReserveEngineRateOverrideSet:
    targetEpoch: indexed(uint256)
    targetBasePayoutRate: uint256

event ReserveEngineRateOverrideCancelled:
    targetEpoch: indexed(uint256)
    targetBasePayoutRate: uint256

event ReserveEngineStarted:
    genesisBlock: uint256
    epochLength: uint256

event ReserveEnginePaymentTokenSet:
    token: indexed(address)

event ReserveEngineCanAcquireRipeSet:
    canAcquireRipe: bool

event PendingStartAuctionAction:
    liqUser: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingStartManyAuctionsAction:
    numAuctions: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingPauseAuctionAction:
    liqUser: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingPauseManyAuctionsAction:
    numAuctions: uint256
    confirmationBlock: uint256
    actionId: uint256

event StartAuctionExecuted:
    liqUser: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    success: bool

event StartManyAuctionsExecuted:
    numAuctionsStarted: uint256

event PauseAuctionExecuted:
    liqUser: indexed(address)
    vaultId: uint256
    asset: indexed(address)
    success: bool

event PauseManyAuctionsExecuted:
    numAuctionsPaused: uint256

event PendingAccrualClockArmedAction:
    asset: indexed(address)
    vaultId: uint256
    shouldArm: bool
    confirmationBlock: uint256
    actionId: uint256

event AccrualClockArmedSet:
    asset: indexed(address)
    vaultId: uint256
    shouldArm: bool
    caller: indexed(address)

event GreenRefPoolSnapshotAttempted:
    caller: indexed(address)
    priceSourceId: indexed(uint256)
    priceSourceAddr: indexed(address)
    didUpdate: bool

# pending actions
actionType: public(HashMap[uint256, ActionType]) # aid -> type
pendingEngineConfig: public(HashMap[uint256, ReserveEngineConfig]) # aid -> config
pendingVestingAllocationBudget: public(HashMap[uint256, uint256]) # aid -> amount
pendingStartAuctionActions: public(HashMap[uint256, FungAuctionConfig])
pendingStartManyAuctionsActions: public(HashMap[uint256, DynArray[FungAuctionConfig, MAX_AUCTIONS]])
pendingPauseAuctionActions: public(HashMap[uint256, FungAuctionConfig])
pendingPauseManyAuctionsActions: public(HashMap[uint256, DynArray[FungAuctionConfig, MAX_AUCTIONS]])
pendingAccrualClock: public(HashMap[uint256, AccrualClockUpdate])

LEDGER_ID: constant(uint256) = 4
MISSION_CONTROL_ID: constant(uint256) = 5
PRICE_DESK_ID: constant(uint256) = 7
RIPE_RESERVE_ENGINE_ID: constant(uint256) = 26
RIPE_RESERVE_VESTING_ID: constant(uint256) = 27
AUCTION_HOUSE_ID: constant(uint256) = 9
MAX_AUCTIONS: constant(uint256) = 20
HUNDRED_PERCENT: constant(uint256) = 100_00


@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    timeLock.__init__(_minConfigTimeLock, _maxConfigTimeLock, 0, _maxConfigTimeLock)


# address getters


@view
@internal
def _getRipeReserveEngineAddr() -> address:
    engine: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(RIPE_RESERVE_ENGINE_ID)
    assert engine != empty(address) and engine.is_contract # dev: invalid engine
    return engine


@view
@internal
def _getRipeReserveVestingAddr() -> address:
    vesting: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(RIPE_RESERVE_VESTING_ID)
    assert vesting != empty(address) and vesting.is_contract # dev: invalid vesting
    return vesting


@view
@internal
def _getAuctionHouseAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(AUCTION_HOUSE_ID)


@view
@internal
def _getMissionControlAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(MISSION_CONTROL_ID)


@view
@internal
def _getLedgerAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(LEDGER_ID)


#########################
# Promotional Accrual   #
#########################


@view
@internal
def _isPristineAssetPoints(_asset: address, _vaultId: uint256) -> bool:
    points: AssetDepositPoints = staticcall Ledger(self._getLedgerAddr()).assetDepositPoints(_vaultId, _asset)
    return (
        points.lastUpdate == 0
        and points.lastBalance == 0
        and points.balancePoints == 0
        and points.ripeStakerPoints == 0
        and points.ripeVotePoints == 0
        and points.ripeGenPoints == 0
        and points.lastUsdValue == 0
    )


@view
@internal
def _validateAccrualClockTransition(_asset: address, _vaultId: uint256, _shouldArm: bool, _missionControl: address):
    assert _missionControl == self._getMissionControlAddr() # dev: not current mission control
    assert staticcall MissionControl(_missionControl).isSupportedAsset(_asset) # dev: invalid asset
    assert _vaultId != 0 and staticcall MissionControl(_missionControl).rewardVaultId(_asset) == _vaultId # dev: invalid reward vault
    assert staticcall MissionControl(_missionControl).isSupportedAssetInVault(_vaultId, _asset) # dev: unsupported reward vault

    config: cs.AssetConfig = staticcall MissionControl(_missionControl).assetConfig(_asset)
    assert not config.canDeposit # dev: deposits must be disabled
    assert config.debtTerms.ltv == 0 # dev: ltv must be zero
    assert config.stakersPointsAlloc == 0 and config.voterPointsAlloc == 0 # dev: allocations must be zero
    current: uint256 = staticcall MissionControl(_missionControl).accrualStartBlock(_asset, _vaultId)
    if _shouldArm:
        assert current == 0 # dev: invalid accrual clock transition
    else:
        assert current == max_value(uint256) # dev: invalid accrual clock transition
    assert self._isPristineAssetPoints(_asset, _vaultId) # dev: asset points not pristine


@external
def setAccrualClockArmed(_asset: address, _vaultId: uint256, _shouldArm: bool) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    mc: address = self._getMissionControlAddr()
    self._validateAccrualClockTransition(_asset, _vaultId, _shouldArm, mc)

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.SET_ACCRUAL_CLOCK_ARMED
    self.pendingAccrualClock[aid] = AccrualClockUpdate(asset=_asset, vaultId=_vaultId, shouldArm=_shouldArm, missionControl=mc)
    log PendingAccrualClockArmedAction(
        asset=_asset,
        vaultId=_vaultId,
        shouldArm=_shouldArm,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return aid


#########################
# Reserve Engine Config #
#########################


@external
def setReserveEngineConfig(_config: ReserveEngineConfig) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    engine: address = self._getRipeReserveEngineAddr()
    assert staticcall RipeReserveEngine(engine).isValidConfig(_config) # dev: invalid config

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RESERVE_ENGINE_CONFIG
    self.pendingEngineConfig[aid] = _config

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingReserveEngineConfigSet(
        actionId=aid,
        confirmationBlock=confirmationBlock,
        paymentCapPerEpoch=_config.paymentCapPerEpoch,
        minPaymentAmount=_config.minPaymentAmount,
        maxAllInPayoutRate=_config.maxAllInPayoutRate,
        seedBasePayoutRate=_config.seedBasePayoutRate,
        uHighBps=_config.uHighBps,
        uLowBps=_config.uLowBps,
        minUpBps=_config.minUpBps,
        maxUpBps=_config.maxUpBps,
        minDownBps=_config.minDownBps,
        maxDownBps=_config.maxDownBps,
        decayBps=_config.decayBps,
        maxDecayEpochs=_config.maxDecayEpochs,
        maxVestingBonus=_config.maxVestingBonus,
        minVestingLength=_config.minVestingLength,
        maxVestingLength=_config.maxVestingLength,
        epochLength=_config.epochLength,
    )
    return aid


# can acquire ripe


@external
def setCanAcquireRipe(_canAcquireRipe: bool):
    assert gov._canGovern(msg.sender) # dev: no perms

    engine: address = self._getRipeReserveEngineAddr()
    assert staticcall RipeReserveEngine(engine).canAcquireRipe() != _canAcquireRipe # dev: no change
    extcall RipeReserveEngine(engine).setCanAcquireRipe(_canAcquireRipe)
    log ReserveEngineCanAcquireRipeSet(canAcquireRipe=_canAcquireRipe)


#################
# Rate Override #
#################


@external
def setReserveEngineRateOverride(_targetBasePayoutRate: uint256, _targetEpoch: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    engine: address = self._getRipeReserveEngineAddr()
    assert staticcall RipeReserveEngine(engine).isValidRateOverride(_targetBasePayoutRate, _targetEpoch) # dev: invalid rate override
    resolvedEpoch: uint256 = extcall RipeReserveEngine(engine).setRateOverride(_targetBasePayoutRate, _targetEpoch)
    log ReserveEngineRateOverrideSet(
        targetEpoch=resolvedEpoch,
        targetBasePayoutRate=_targetBasePayoutRate,
    )
    return resolvedEpoch


@external
def cancelReserveEngineRateOverride():
    assert gov._canGovern(msg.sender) # dev: no perms

    engine: address = self._getRipeReserveEngineAddr()
    targetBasePayoutRate: uint256 = staticcall RipeReserveEngine(engine).overrideTargetBasePayoutRate()
    assert targetBasePayoutRate != 0 # dev: no rate override
    targetEpoch: uint256 = staticcall RipeReserveEngine(engine).overrideTargetEpoch()
    extcall RipeReserveEngine(engine).cancelRateOverride()
    log ReserveEngineRateOverrideCancelled(targetEpoch=targetEpoch, targetBasePayoutRate=targetBasePayoutRate)


#########
# Start #
#########


@external
def startReserveEngine(_genesisBlock: uint256, _epochLength: uint256):
    assert gov._canGovern(msg.sender) # dev: no perms

    engine: address = self._getRipeReserveEngineAddr()
    assert not staticcall RipeReserveEngine(engine).isRunning() # dev: already running
    assert staticcall RipeReserveEngine(engine).isValidEpochLength(_epochLength) # dev: invalid epoch length
    assert staticcall RipeReserveEngine(engine).isValidConfig(staticcall RipeReserveEngine(engine).engineConfig()) # dev: not configured
    extcall RipeReserveEngine(engine).start(_genesisBlock, _epochLength)
    resolvedGenesisBlock: uint256 = staticcall RipeReserveEngine(engine).genesisBlock()
    log ReserveEngineStarted(genesisBlock=resolvedGenesisBlock, epochLength=_epochLength)


@external
def stopReserveEngine():
    assert gov._canGovern(msg.sender) # dev: no perms

    engine: address = self._getRipeReserveEngineAddr()
    assert staticcall RipeReserveEngine(engine).isRunning() # dev: not running
    extcall RipeReserveEngine(engine).stop()


#################
# Payment Token #
#################


@external
def setReserveEnginePaymentToken(_token: address):
    assert gov._canGovern(msg.sender) # dev: no perms

    engine: address = self._getRipeReserveEngineAddr()
    assert staticcall RipeReserveEngine(engine).isValidPaymentToken(_token) # dev: invalid payment token
    extcall RipeReserveEngine(engine).setPaymentToken(_token)
    log ReserveEnginePaymentTokenSet(token=_token)


#####################
# Allocation Budget #
#####################


@external
def setReserveVestingRemainingAllocationBudget(_amount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    self._getRipeReserveVestingAddr()

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.RESERVE_VESTING_ALLOCATION_BUDGET_SET
    self.pendingVestingAllocationBudget[aid] = _amount

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingReserveVestingAllocationBudgetSet(
        actionId=aid,
        confirmationBlock=confirmationBlock,
        amount=_amount,
    )
    return aid


###################
# Auction Actions #
###################


@external
def startAuction(_liqUser: address, _vaultId: uint256, _asset: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert empty(address) not in [_liqUser, _asset] # dev: invalid parameters

    auctionHouseAddr: address = self._getAuctionHouseAddr()
    assert staticcall AuctionHouse(auctionHouseAddr).canStartAuction(_liqUser, _vaultId, _asset) # dev: cannot start auction

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.START_AUCTION
    self.pendingStartAuctionActions[aid] = FungAuctionConfig(
        liqUser=_liqUser,
        vaultId=_vaultId,
        asset=_asset,
    )

    log PendingStartAuctionAction(
        liqUser=_liqUser,
        vaultId=_vaultId,
        asset=_asset,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return aid


@external
def startManyAuctions(_auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS]) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert len(_auctions) != 0 # dev: no auctions provided

    auctionHouseAddr: address = self._getAuctionHouseAddr()
    for auction: FungAuctionConfig in _auctions:
        assert staticcall AuctionHouse(auctionHouseAddr).canStartAuction(auction.liqUser, auction.vaultId, auction.asset) # dev: cannot start auction

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.START_MANY_AUCTIONS
    self.pendingStartManyAuctionsActions[aid] = _auctions

    log PendingStartManyAuctionsAction(
        numAuctions=len(_auctions),
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return aid


@external
def pauseAuction(_liqUser: address, _vaultId: uint256, _asset: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert empty(address) not in [_liqUser, _asset] # dev: invalid parameters

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PAUSE_AUCTION
    self.pendingPauseAuctionActions[aid] = FungAuctionConfig(
        liqUser=_liqUser,
        vaultId=_vaultId,
        asset=_asset,
    )

    log PendingPauseAuctionAction(
        liqUser=_liqUser,
        vaultId=_vaultId,
        asset=_asset,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return aid


@external
def pauseManyAuctions(_auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS]) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert len(_auctions) != 0 # dev: no auctions provided

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PAUSE_MANY_AUCTIONS
    self.pendingPauseManyAuctionsActions[aid] = _auctions

    log PendingPauseManyAuctionsAction(
        numAuctions=len(_auctions),
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
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
    assert actionType != empty(ActionType) # dev: invalid action

    if actionType == ActionType.RESERVE_ENGINE_CONFIG:
        engine: address = self._getRipeReserveEngineAddr()
        config: ReserveEngineConfig = self.pendingEngineConfig[_aid]
        assert staticcall RipeReserveEngine(engine).isValidConfig(config) # dev: invalid config
        extcall RipeReserveEngine(engine).setConfig(config)
        self.pendingEngineConfig[_aid] = empty(ReserveEngineConfig)
        log ReserveEngineConfigExecuted(actionId=_aid)

    elif actionType == ActionType.RESERVE_VESTING_ALLOCATION_BUDGET_SET:
        vesting: address = self._getRipeReserveVestingAddr()
        amount: uint256 = self.pendingVestingAllocationBudget[_aid]
        extcall RipeReserveVesting(vesting).setRemainingAllocationBudget(amount)
        self.pendingVestingAllocationBudget[_aid] = 0
        log ReserveVestingAllocationBudgetExecuted(actionId=_aid)

    elif actionType == ActionType.START_AUCTION:
        p: FungAuctionConfig = self.pendingStartAuctionActions[_aid]
        success: bool = extcall AuctionHouse(self._getAuctionHouseAddr()).startAuction(p.liqUser, p.vaultId, p.asset)
        log StartAuctionExecuted(liqUser=p.liqUser, vaultId=p.vaultId, asset=p.asset, success=success)

    elif actionType == ActionType.START_MANY_AUCTIONS:
        auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS] = self.pendingStartManyAuctionsActions[_aid]
        numStarted: uint256 = extcall AuctionHouse(self._getAuctionHouseAddr()).startManyAuctions(auctions)
        log StartManyAuctionsExecuted(numAuctionsStarted=numStarted)

    elif actionType == ActionType.PAUSE_AUCTION:
        p: FungAuctionConfig = self.pendingPauseAuctionActions[_aid]
        success: bool = extcall AuctionHouse(self._getAuctionHouseAddr()).pauseAuction(p.liqUser, p.vaultId, p.asset)
        log PauseAuctionExecuted(liqUser=p.liqUser, vaultId=p.vaultId, asset=p.asset, success=success)

    elif actionType == ActionType.PAUSE_MANY_AUCTIONS:
        auctions: DynArray[FungAuctionConfig, MAX_AUCTIONS] = self.pendingPauseManyAuctionsActions[_aid]
        numPaused: uint256 = extcall AuctionHouse(self._getAuctionHouseAddr()).pauseManyAuctions(auctions)
        log PauseManyAuctionsExecuted(numAuctionsPaused=numPaused)

    elif actionType == ActionType.SET_ACCRUAL_CLOCK_ARMED:
        p: AccrualClockUpdate = self.pendingAccrualClock[_aid]
        self._validateAccrualClockTransition(p.asset, p.vaultId, p.shouldArm, p.missionControl)
        extcall MissionControl(p.missionControl).setAccrualStartBlock(p.asset, p.vaultId, max_value(uint256) if p.shouldArm else 0)
        self.pendingAccrualClock[_aid] = empty(AccrualClockUpdate)
        log AccrualClockArmedSet(asset=p.asset, vaultId=p.vaultId, shouldArm=p.shouldArm, caller=msg.sender)

    else:
        raise "invalid action"

    self.actionType[_aid] = empty(ActionType)
    return True


#################
# Cancel Action #
#################


@external
def cancelPendingAction(_aid: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    self._cancelPendingAction(_aid)
    return True


@internal
def _cancelPendingAction(_aid: uint256):
    actionType: ActionType = self.actionType[_aid]
    assert actionType != empty(ActionType) # dev: invalid action
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action

    if actionType == ActionType.RESERVE_ENGINE_CONFIG:
        self.pendingEngineConfig[_aid] = empty(ReserveEngineConfig)
    elif actionType == ActionType.RESERVE_VESTING_ALLOCATION_BUDGET_SET:
        self.pendingVestingAllocationBudget[_aid] = 0
    elif (
        actionType == ActionType.START_AUCTION
        or actionType == ActionType.START_MANY_AUCTIONS
        or actionType == ActionType.PAUSE_AUCTION
        or actionType == ActionType.PAUSE_MANY_AUCTIONS
    ):
        pass
    elif actionType == ActionType.SET_ACCRUAL_CLOCK_ARMED:
        self.pendingAccrualClock[_aid] = empty(AccrualClockUpdate)
    else:
        raise "invalid action"

    self.actionType[_aid] = empty(ActionType)


###########################
# GREEN Ref Pool Snapshot #
###########################


@external
def addGreenRefPoolSnapshot(_curvePricesId: uint256) -> bool:
    if not gov._canGovern(msg.sender):
        assert staticcall MissionControl(self._getMissionControlAddr()).canPerformLiteAction(msg.sender) # dev: no perms

    priceDesk: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(PRICE_DESK_ID)
    assert priceDesk != empty(address) # dev: missing price desk

    priceSourceAddr: address = staticcall PriceDesk(priceDesk).getAddr(_curvePricesId)
    assert priceSourceAddr != empty(address) # dev: invalid price source id

    didUpdate: bool = extcall CurvePrices(priceSourceAddr).addGreenRefPoolSnapshot()
    log GreenRefPoolSnapshotAttempted(
        caller=msg.sender,
        priceSourceId=_curvePricesId,
        priceSourceAddr=priceSourceAddr,
        didUpdate=didUpdate,
    )
    return didUpdate
