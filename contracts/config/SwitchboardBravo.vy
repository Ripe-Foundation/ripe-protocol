#        ______   __     __   __   ______  ______   __  __   ______   ______   ______   ______   _____    
#       /\  ___\ /\ \  _ \ \ /\ \ /\__  _\/\  ___\ /\ \_\ \ /\  == \ /\  __ \ /\  __ \ /\  == \ /\  __-.  
#       \ \___  \\ \ \/ ".\ \\ \ \\/_/\ \/\ \ \____\ \  __ \\ \  __< \ \ \/\ \\ \  __ \\ \  __< \ \ \/\ \ 
#        \/\_____\\ \__/".~\_\\ \_\  \ \_\ \ \_____\\ \_\ \_\\ \_____\\ \_____\\ \_\ \_\\ \_\ \_\\ \____- 
#         \/_____/ \/_/   \/_/ \/_/   \/_/  \/_____/ \/_/\/_/ \/_____/ \/_____/ \/_/\/_/ \/_/ /_/ \/____/ 
#                                                   ┳┓        
#                                                   ┣┫┏┓┏┓┓┏┏┓
#                                                   ┻┛┛ ┗┻┗┛┗┛
#
#      Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#      Ripe Foundation (C) 2026 

# @version 0.4.3
# pragma optimize codesize

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock
import interfaces.ConfigStructs as cs

interface MissionControl:
    def setAssetConfig(_asset: address, _assetConfig: cs.AssetConfig): nonpayable
    def setAccrualStartBlock(_asset: address, _vaultId: uint256, _startBlock: uint256): nonpayable
    def assetConfig(_asset: address) -> cs.AssetConfig: view
    def rewardVaultId(_asset: address) -> uint256: view
    def accrualStartBlock(_asset: address, _vaultId: uint256) -> uint256: view
    def isSupportedAsset(_asset: address) -> bool: view
    def isSupportedAssetInVault(_vaultId: uint256, _asset: address) -> bool: view
    def isStabVaultId(_vaultId: uint256) -> bool: view
    def isRipeGovVaultId(_vaultId: uint256) -> bool: view

interface VaultBook:
    def isValidRegId(_regId: uint256) -> bool: view
    def getAddr(_regId: uint256) -> address: view

interface Lootbox:
    def updateDepositPoints(_user: address, _vaultId: uint256, _vaultAddr: address, _asset: address): nonpayable
    def resetUserBalancePoints(_user: address, _asset: address, _vaultId: uint256): nonpayable
    def resetAssetPoints(_asset: address, _vaultId: uint256): nonpayable

interface Ledger:
    def globalDepositPoints() -> GlobalDepositPoints: view
    def assetDepositPoints(_vaultId: uint256, _asset: address) -> AssetDepositPoints: view

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

flag ActionType:
    ASSET_DEPOSIT_PARAMS
    PREPARE_PROMOTIONAL_COLLECTION

struct AssetUpdate:
    asset: address
    config: cs.AssetConfig

struct PromotionalCollection:
    asset: address
    vaultId: uint256

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

event PendingAssetDepositParamsChange:
    asset: indexed(address)
    numVaultIds: uint256
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
    minDepositBalance: uint256
    confirmationBlock: uint256
    actionId: uint256

event AssetDepositParamsSet:
    asset: indexed(address)
    numVaultIds: uint256
    stakersPointsAlloc: uint256
    voterPointsAlloc: uint256
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
    minDepositBalance: uint256

event PendingPromotionalCollection:
    asset: indexed(address)
    vaultId: uint256
    numTesters: uint256
    confirmationBlock: uint256
    actionId: uint256

event PromotionalCollectionPrepared:
    asset: indexed(address)
    vaultId: uint256
    numTesters: uint256
    caller: indexed(address)

# pending config changes
actionType: public(HashMap[uint256, ActionType]) # aid -> type
pendingAssetConfig: public(HashMap[uint256, AssetUpdate]) # aid -> asset
pendingPromotionalCollection: public(HashMap[uint256, PromotionalCollection]) # aid -> collection
pendingPromotionalTesters: public(HashMap[uint256, DynArray[address, MAX_REHEARSAL_TESTERS]]) # aid -> testers
pendingMissionControl: public(HashMap[uint256, address]) # aid -> target mission control

MAX_VAULTS_PER_ASSET: constant(uint256) = 10
MAX_REHEARSAL_TESTERS: constant(uint256) = 40
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100%

LEDGER_ID: constant(uint256) = 4
MISSION_CONTROL_ID: constant(uint256) = 5
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


##########################
# Asset - Deposit Params #
##########################


@external
def setAssetDepositParams(
    _asset: address,
    _vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _stakersPointsAlloc: uint256,
    _voterPointsAlloc: uint256,
    _perUserDepositLimit: uint256,
    _globalDepositLimit: uint256,
    _minDepositBalance: uint256,
    _missionControl: address = empty(address),
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    mc: address = self._resolveMissionControl(_missionControl)
    assert staticcall MissionControl(mc).isSupportedAsset(_asset) # dev: invalid asset
    assert self._isValidAssetDepositParams(_asset, _vaultIds, _stakersPointsAlloc, _voterPointsAlloc, _perUserDepositLimit, _globalDepositLimit, _minDepositBalance, mc) # dev: invalid asset deposit params
    return self._setPendingAssetDepositParams(_asset, mc, _vaultIds, _stakersPointsAlloc, _voterPointsAlloc, _perUserDepositLimit, _globalDepositLimit, _minDepositBalance)


@view
@internal
def _isValidAssetDepositParams(
    _asset: address,
    _vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _stakersPointsAlloc: uint256,
    _voterPointsAlloc: uint256,
    _perUserDepositLimit: uint256,
    _globalDepositLimit: uint256,
    _minDepositBalance: uint256,
    _missionControl: address,
) -> bool:
    vaultBook: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(VAULT_BOOK_ID)
    if 0 in [_perUserDepositLimit, _globalDepositLimit]:
        return False
    if max_value(uint256) in [_perUserDepositLimit, _globalDepositLimit, _stakersPointsAlloc, _voterPointsAlloc]:
        return False
    if _stakersPointsAlloc + _voterPointsAlloc > HUNDRED_PERCENT:
        return False
    if _perUserDepositLimit > _globalDepositLimit:
        return False
    if _minDepositBalance > _perUserDepositLimit:
        return False
    for vaultId: uint256 in _vaultIds:
        if not staticcall VaultBook(vaultBook).isValidRegId(vaultId):
            return False
    
    if _stakersPointsAlloc != 0:
        earner: uint256 = staticcall MissionControl(_missionControl).rewardVaultId(_asset)
        if earner == 0:
            return False
        if not staticcall MissionControl(_missionControl).isRipeGovVaultId(earner) and not staticcall MissionControl(_missionControl).isStabVaultId(earner):
            return False

    return True


##########################
# Asset - Pending Config #
##########################


@internal
def _setPendingAssetDepositParams(
    _asset: address,
    _missionControl: address,
    _vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _stakersPointsAlloc: uint256,
    _voterPointsAlloc: uint256,
    _perUserDepositLimit: uint256,
    _globalDepositLimit: uint256,
    _minDepositBalance: uint256,
) -> uint256:
    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ASSET_DEPOSIT_PARAMS
    self.pendingMissionControl[aid] = _missionControl
    config: cs.AssetConfig = empty(cs.AssetConfig)
    config.vaultIds = _vaultIds
    config.stakersPointsAlloc = _stakersPointsAlloc
    config.voterPointsAlloc = _voterPointsAlloc
    config.perUserDepositLimit = _perUserDepositLimit
    config.globalDepositLimit = _globalDepositLimit
    config.minDepositBalance = _minDepositBalance
    self.pendingAssetConfig[aid] = AssetUpdate(asset=_asset, config=config)
    log PendingAssetDepositParamsChange(
        asset=_asset,
        numVaultIds=len(_vaultIds),
        stakersPointsAlloc=_stakersPointsAlloc,
        voterPointsAlloc=_voterPointsAlloc,
        perUserDepositLimit=_perUserDepositLimit,
        globalDepositLimit=_globalDepositLimit,
        minDepositBalance=_minDepositBalance,
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return aid


############################
# Promotional Collection  #
############################


@view
@internal
def _validatePromotionalCollection(
    _asset: address,
    _vaultId: uint256,
    _missionControl: address,
) -> cs.AssetConfig:
    assert _missionControl == self._getMissionControlAddr() # dev: not current mission control
    assert staticcall MissionControl(_missionControl).isSupportedAsset(_asset) # dev: invalid asset
    assert _vaultId != 0 and staticcall MissionControl(_missionControl).rewardVaultId(_asset) == _vaultId # dev: invalid reward vault
    assert staticcall MissionControl(_missionControl).isSupportedAssetInVault(_vaultId, _asset) # dev: unsupported reward vault
    assert staticcall MissionControl(_missionControl).accrualStartBlock(_asset, _vaultId) == 0 # dev: accrual clock already armed

    config: cs.AssetConfig = staticcall MissionControl(_missionControl).assetConfig(_asset)
    assert config.debtTerms.ltv == 0 # dev: ltv must be zero
    assert config.stakersPointsAlloc == 0 # dev: staker allocation must be zero
    return config


@external
def preparePromotionalCollection(
    _asset: address,
    _vaultId: uint256,
    _testers: DynArray[address, MAX_REHEARSAL_TESTERS],
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    for i: uint256 in range(len(_testers), bound=MAX_REHEARSAL_TESTERS):
        tester: address = _testers[i]
        assert tester != empty(address) # dev: invalid tester
        for j: uint256 in range(i, bound=MAX_REHEARSAL_TESTERS):
            assert tester != _testers[j] # dev: duplicate tester

    mc: address = self._getMissionControlAddr()
    config: cs.AssetConfig = self._validatePromotionalCollection(_asset, _vaultId, mc)
    if config.canDeposit:
        config.canDeposit = False
        extcall MissionControl(mc).setAssetConfig(_asset, config)

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PREPARE_PROMOTIONAL_COLLECTION
    self.pendingMissionControl[aid] = mc
    self.pendingPromotionalCollection[aid] = PromotionalCollection(
        asset=_asset,
        vaultId=_vaultId,
    )
    self.pendingPromotionalTesters[aid] = _testers
    log PendingPromotionalCollection(
        asset=_asset,
        vaultId=_vaultId,
        numTesters=len(_testers),
        confirmationBlock=timeLock._getActionConfirmationBlock(aid),
        actionId=aid,
    )
    return aid


# asset config write


@view
@internal
def _vaultIdsEqual(
    _a: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _b: DynArray[uint256, MAX_VAULTS_PER_ASSET],
) -> bool:
    if len(_a) != len(_b):
        return False
    for i: uint256 in range(len(_a), bound=MAX_VAULTS_PER_ASSET):
        if _a[i] != _b[i]:
            return False
    return True


@view
@internal
def _assertAssetAllocStructure(_asset: address, _prevConfig: cs.AssetConfig, _newConfig: cs.AssetConfig, _missionControl: address):
    membershipChanged: bool = not self._vaultIdsEqual(_prevConfig.vaultIds, _newConfig.vaultIds)
    allocsChanged: bool = _prevConfig.stakersPointsAlloc != _newConfig.stakersPointsAlloc or _prevConfig.voterPointsAlloc != _newConfig.voterPointsAlloc
    assert not (membershipChanged and allocsChanged) # dev: cannot change membership and allocs together
    earner: uint256 = staticcall MissionControl(_missionControl).rewardVaultId(_asset)
    if membershipChanged:
        assert earner == 0 or earner in _newConfig.vaultIds # dev: cannot drop reward vault
        if _prevConfig.stakersPointsAlloc != 0 or _prevConfig.voterPointsAlloc != 0:
            # An active promotional allocation remains attached to the same earner;
            # non-earner vault membership can evolve independently.
            assert earner != 0 # dev: active allocs require reward vault
            startBlock: uint256 = staticcall MissionControl(_missionControl).accrualStartBlock(_asset, earner)
            assert startBlock != 0 and startBlock != max_value(uint256) # dev: membership change requires zero allocs or active promotion
    if _newConfig.stakersPointsAlloc != 0 or _newConfig.voterPointsAlloc != 0:
        assert earner != 0 # dev: active allocs require reward vault


@internal
def _enforceAccrualConfigChange(_asset: address, _prevConfig: cs.AssetConfig, _newConfig: cs.AssetConfig, _missionControl: address):
    vaultId: uint256 = staticcall MissionControl(_missionControl).rewardVaultId(_asset)
    if vaultId == 0:
        return

    startBlock: uint256 = staticcall MissionControl(_missionControl).accrualStartBlock(_asset, vaultId)
    if startBlock == 0:
        return

    assert vaultId in _newConfig.vaultIds # dev: promotional reward vault changed
    assert _newConfig.stakersPointsAlloc == 0 # dev: promotional staker alloc must remain zero

    if startBlock == max_value(uint256):
        assert _newConfig.debtTerms.ltv == 0 # dev: armed promotional ltv must remain zero
        assert _prevConfig.voterPointsAlloc == 0 # dev: invalid armed voter alloc
        if _newConfig.voterPointsAlloc == 0:
            return

        assert _missionControl == self._getMissionControlAddr() # dev: not current mission control
        assert _newConfig.voterPointsAlloc <= HUNDRED_PERCENT # dev: invalid voter alloc
        ledger: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(LEDGER_ID)
        assetPoints: AssetDepositPoints = staticcall Ledger(ledger).assetDepositPoints(vaultId, _asset)
        globalPoints: GlobalDepositPoints = staticcall Ledger(ledger).globalDepositPoints()
        assert assetPoints.lastUpdate == block.number # dev: asset points not checkpointed
        assert globalPoints.lastUpdate == block.number # dev: global points not checkpointed
        assert assetPoints.lastBalance != 0 # dev: promotional row has no balance
        extcall MissionControl(_missionControl).setAccrualStartBlock(_asset, vaultId, block.number)
        return

    assert _newConfig.voterPointsAlloc == _prevConfig.voterPointsAlloc # dev: promotional voter alloc is permanent


@internal
def _checkpointSelectedRows(
    _asset: address,
    _vaultIds: DynArray[uint256, MAX_VAULTS_PER_ASSET],
    _vaultAddrs: DynArray[address, MAX_VAULTS_PER_ASSET],
    _lootbox: address,
):
    for i: uint256 in range(len(_vaultIds), bound=MAX_VAULTS_PER_ASSET):
        extcall Lootbox(_lootbox).updateDepositPoints(empty(address), _vaultIds[i], _vaultAddrs[i], _asset)


@view
@internal
def _arePromotionalPointsCleared(_asset: address, _vaultId: uint256) -> bool:
    points: AssetDepositPoints = staticcall Ledger(
        staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(LEDGER_ID)
    ).assetDepositPoints(_vaultId, _asset)
    return (
        points.balancePoints == 0
        and points.ripeStakerPoints == 0
        and points.ripeVotePoints == 0
        and points.ripeGenPoints == 0
    )


@internal
def _writeAssetConfig(
    _asset: address,
    _config: cs.AssetConfig,
    _mc: address,
    _oldStakers: uint256,
    _oldVoter: uint256,
):
    prevConfig: cs.AssetConfig = staticcall MissionControl(_mc).assetConfig(_asset)
    self._assertAssetAllocStructure(_asset, prevConfig, _config, _mc)
    assert self._isValidAssetDepositParams(_asset, _config.vaultIds, _config.stakersPointsAlloc, _config.voterPointsAlloc, _config.perUserDepositLimit, _config.globalDepositLimit, _config.minDepositBalance, _mc) # dev: invalid asset deposit params

    needCkpt: bool = (
        _mc == self._getMissionControlAddr()
        and (_oldStakers != _config.stakersPointsAlloc or _oldVoter != _config.voterPointsAlloc)
    )
    selectedIds: DynArray[uint256, MAX_VAULTS_PER_ASSET] = []
    selectedAddrs: DynArray[address, MAX_VAULTS_PER_ASSET] = []
    lootbox: address = empty(address)
    earner: uint256 = 0
    startBefore: uint256 = 0
    if needCkpt:
        ripeHq: address = gov._getRipeHqFromGov()
        vaultBook: address = staticcall RipeHq(ripeHq).getAddr(VAULT_BOOK_ID)
        lootbox = staticcall RipeHq(ripeHq).getAddr(LOOTBOX_ID)
        earner = staticcall MissionControl(_mc).rewardVaultId(_asset)
        if earner != 0:
            vaultAddr: address = staticcall VaultBook(vaultBook).getAddr(earner)
            assert vaultAddr != empty(address) # dev: invalid vault
            selectedIds.append(earner)
            selectedAddrs.append(vaultAddr)
            startBefore = staticcall MissionControl(_mc).accrualStartBlock(_asset, earner)
        self._checkpointSelectedRows(_asset, selectedIds, selectedAddrs, lootbox)

    self._enforceAccrualConfigChange(_asset, prevConfig, _config, _mc)
    extcall MissionControl(_mc).setAssetConfig(_asset, _config)

    if needCkpt:
        startAfter: uint256 = 0
        if earner != 0:
            startAfter = staticcall MissionControl(_mc).accrualStartBlock(_asset, earner)
        # Same classification as MissionControl.getDepositPointsConfig.shouldFundGenPoints.
        oldFundGen: bool = earner != 0 and _oldStakers == 0 and _oldVoter == 0 and startBefore == 0
        newFundGen: bool = (
            earner != 0
            and _config.stakersPointsAlloc == 0
            and _config.voterPointsAlloc == 0
            and startAfter == 0
        )
        if oldFundGen != newFundGen:
            self._checkpointSelectedRows(_asset, selectedIds, selectedAddrs, lootbox)


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
    mc: address = self.pendingMissionControl[_aid]
    if mc == empty(address):
        mc = self._getMissionControlAddr()
    assert mc == self._getMissionControlAddr() # dev: not current mission control
    if actionType == ActionType.ASSET_DEPOSIT_PARAMS:
        p: AssetUpdate = self.pendingAssetConfig[_aid]
        assert staticcall MissionControl(mc).isSupportedAsset(p.asset) # dev: invalid asset
        config: cs.AssetConfig = staticcall MissionControl(mc).assetConfig(p.asset)
        oldStakers: uint256 = config.stakersPointsAlloc
        oldVoter: uint256 = config.voterPointsAlloc
        config.vaultIds = p.config.vaultIds
        config.stakersPointsAlloc = p.config.stakersPointsAlloc
        config.voterPointsAlloc = p.config.voterPointsAlloc
        config.perUserDepositLimit = p.config.perUserDepositLimit
        config.globalDepositLimit = p.config.globalDepositLimit
        config.minDepositBalance = p.config.minDepositBalance
        self._writeAssetConfig(p.asset, config, mc, oldStakers, oldVoter)
        log AssetDepositParamsSet(asset=p.asset, numVaultIds=len(p.config.vaultIds), stakersPointsAlloc=p.config.stakersPointsAlloc, voterPointsAlloc=p.config.voterPointsAlloc, perUserDepositLimit=p.config.perUserDepositLimit, globalDepositLimit=p.config.globalDepositLimit, minDepositBalance=p.config.minDepositBalance)

    elif actionType == ActionType.PREPARE_PROMOTIONAL_COLLECTION:
        collection: PromotionalCollection = self.pendingPromotionalCollection[_aid]
        testers: DynArray[address, MAX_REHEARSAL_TESTERS] = self.pendingPromotionalTesters[_aid]
        config: cs.AssetConfig = self._validatePromotionalCollection(collection.asset, collection.vaultId, mc)
        assert not config.canDeposit # dev: deposits must be disabled

        oldVoter: uint256 = config.voterPointsAlloc
        if oldVoter != 0:
            config.voterPointsAlloc = 0
            self._writeAssetConfig(collection.asset, config, mc, 0, oldVoter)

        lootbox: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(LOOTBOX_ID)
        for tester: address in testers:
            extcall Lootbox(lootbox).resetUserBalancePoints(tester, collection.asset, collection.vaultId)
        extcall Lootbox(lootbox).resetAssetPoints(collection.asset, collection.vaultId)
        assert self._arePromotionalPointsCleared(collection.asset, collection.vaultId) # dev: promotional points not clear

        extcall MissionControl(mc).setAccrualStartBlock(collection.asset, collection.vaultId, max_value(uint256))

        vaultBook: address = staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(VAULT_BOOK_ID)
        assert staticcall VaultBook(vaultBook).isValidRegId(collection.vaultId) # dev: invalid vault id
        vaultAddr: address = staticcall VaultBook(vaultBook).getAddr(collection.vaultId)
        assert vaultAddr != empty(address) # dev: invalid vault
        selectedIds: DynArray[uint256, MAX_VAULTS_PER_ASSET] = [collection.vaultId]
        selectedAddrs: DynArray[address, MAX_VAULTS_PER_ASSET] = [vaultAddr]
        self._checkpointSelectedRows(collection.asset, selectedIds, selectedAddrs, lootbox)

        assetPoints: AssetDepositPoints = staticcall Ledger(
            staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(LEDGER_ID)
        ).assetDepositPoints(collection.vaultId, collection.asset)
        assert assetPoints.lastUsdValue == 0 # dev: promotional gen funding weight not clear
        assert self._arePromotionalPointsCleared(collection.asset, collection.vaultId) # dev: promotional points not clear

        log PromotionalCollectionPrepared(asset=collection.asset, vaultId=collection.vaultId, numTesters=len(testers), caller=msg.sender)

        self.pendingPromotionalCollection[_aid] = empty(PromotionalCollection)
        self.pendingPromotionalTesters[_aid] = []

    else:
        raise "invalid action"

    self.actionType[_aid] = empty(ActionType)
    self.pendingMissionControl[_aid] = empty(address)
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
    actionType: ActionType = self.actionType[_aid]
    if actionType == ActionType.PREPARE_PROMOTIONAL_COLLECTION:
        self.pendingPromotionalCollection[_aid] = empty(PromotionalCollection)
        self.pendingPromotionalTesters[_aid] = []
    self.actionType[_aid] = empty(ActionType)
    self.pendingMissionControl[_aid] = empty(address)
