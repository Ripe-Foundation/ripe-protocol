#        ______   __     __   __   ______  ______   __  __   ______   ______   ______   ______   _____
#       /\  ___\ /\ \  _ \ \ /\ \ /\__  _\/\  ___\ /\ \_\ \ /\  == \ /\  __ \ /\  __ \ /\  == \ /\  __-.
#       \ \___  \\ \ \/ ".\ \\ \ \\/_/\ \/\ \ \____\ \  __ \\ \  __< \ \ \/\ \\ \  __ \\ \  __< \ \ \/\ \
#        \/\_____\\ \__/".~\_\\ \_\  \ \_\ \ \_____\\ \_\ \_\\ \_____\\ \_____\\ \_\ \_\\ \_\ \_\\ \____-
#         \/_____/ \/_/   \/_/ \/_/   \/_/  \/_____/ \/_/\/_/ \/_____/ \/_____/ \/_/\/_/ \/_/ /_/ \/____/
#                                                    ┏━┓     ┓
#                                                    ┣━ ┏┓┣┓┏┓
#                                                    ┗━┛┗┗┛┗┗┛
#
#      Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#      Ripe Foundation (C) 2025

# @version 0.4.3

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock
from interfaces import UndyLego as ul

interface Endaoment:
    def addLiquidity(_legoId: uint256, _pool: address, _tokenA: address, _tokenB: address, _amountA: uint256 = max_value(uint256), _amountB: uint256 = max_value(uint256), _minAmountA: uint256 = 0, _minAmountB: uint256 = 0, _minLpAmount: uint256 = 0, _extraData: bytes32 = empty(bytes32)) -> (uint256, uint256, uint256, uint256): nonpayable
    def removeLiquidity(_legoId: uint256, _pool: address, _tokenA: address, _tokenB: address, _lpToken: address, _lpAmount: uint256 = max_value(uint256), _minAmountA: uint256 = 0, _minAmountB: uint256 = 0, _extraData: bytes32 = empty(bytes32)) -> (uint256, uint256, uint256, uint256): nonpayable
    def depositForYield(_legoId: uint256, _asset: address, _vaultAddr: address = empty(address), _amount: uint256 = max_value(uint256), _extraData: bytes32 = empty(bytes32)) -> (uint256, address, uint256, uint256): nonpayable
    def claimIncentives(_user: address, _legoId: uint256, _rewardToken: address = empty(address), _rewardAmount: uint256 = max_value(uint256), _proofs: DynArray[bytes32, MAX_PROOFS] = []) -> (uint256, uint256): nonpayable
    def withdrawFromYield(_legoId: uint256, _vaultToken: address, _amount: uint256 = max_value(uint256), _extraData: bytes32 = empty(bytes32)) -> (uint256, address, uint256, uint256): nonpayable
    def addPartnerLiquidity(_legoId: uint256, _pool: address, _partner: address, _asset: address, _amount: uint256, _minLpAmount: uint256) -> (uint256, uint256, uint256): nonpayable
    def swapTokens(_instructions: DynArray[ul.SwapInstruction, MAX_SWAP_INSTRUCTIONS]) -> (address, uint256, address, uint256, uint256): nonpayable
    def mintPartnerLiquidity(_partner: address, _asset: address, _amount: uint256 = max_value(uint256)) -> uint256: nonpayable
    def transferFundsToGov(_asset: address, _amount: uint256 = max_value(uint256)) -> (uint256, uint256): nonpayable
    def transferFundsToEndaomentPSM(_amount: uint256 = max_value(uint256)) -> (uint256, uint256): nonpayable
    def convertWethToEth(_amount: uint256 = max_value(uint256)) -> (uint256, uint256): nonpayable
    def convertEthToWeth(_amount: uint256 = max_value(uint256)) -> (uint256, uint256): nonpayable
    def transferFundsToVault(_assets: DynArray[address, MAX_ASSETS]): nonpayable
    def repayPoolDebt(_pool: address, _amount: uint256) -> bool: nonpayable
    def stabilizeGreenRefPool() -> bool: nonpayable

interface EndaomentPSM:
    def withdrawFromYield(_amount: uint256 = max_value(uint256), _shouldTransferToEndaoFunds: bool = False, _shouldFullSweep: bool = False) -> (uint256, uint256): nonpayable
    def setUsdcYieldPosition(_legoId: uint256, _vaultToken: address): nonpayable
    def transferUsdcToEndaomentFunds(_amount: uint256) -> uint256: nonpayable
    def updateRedeemAllowlist(_user: address, _isAllowed: bool): nonpayable
    def updateMintAllowlist(_user: address, _isAllowed: bool): nonpayable
    def setShouldEnforceRedeemAllowlist(_shouldEnforce: bool): nonpayable
    def setShouldEnforceMintAllowlist(_shouldEnforce: bool): nonpayable
    def setMaxIntervalRedeem(_maxGreenAmount: uint256): nonpayable
    def setShouldAutoDeposit(_shouldAutoDeposit: bool): nonpayable
    def setMaxIntervalMint(_maxGreenAmount: uint256): nonpayable
    def setNumBlocksPerInterval(_blocks: uint256): nonpayable
    def setCanRedeem(_canRedeem: bool): nonpayable
    def setRedeemFee(_fee: uint256): nonpayable
    def depositToYield() -> uint256: nonpayable
    def setCanMint(_canMint: bool): nonpayable
    def setMintFee(_fee: uint256): nonpayable

interface MissionControl:
    def canPerformLiteAction(_user: address) -> bool: view

interface RipeHq:
    def getAddr(_regId: uint256) -> address: view

flag ActionType:
    ENDAO_SWAP
    ENDAO_ADD_LIQUIDITY
    ENDAO_REMOVE_LIQUIDITY
    ENDAO_PARTNER_MINT
    ENDAO_PARTNER_POOL
    ENDAO_REPAY
    ENDAO_TRANSFER
    PSM_SET_CAN_MINT
    PSM_SET_MINT_FEE
    PSM_SET_MAX_INTERVAL_MINT
    PSM_SET_SHOULD_ENFORCE_MINT_ALLOWLIST
    PSM_UPDATE_MINT_ALLOWLIST
    PSM_SET_CAN_REDEEM
    PSM_SET_REDEEM_FEE
    PSM_SET_MAX_INTERVAL_REDEEM
    PSM_SET_SHOULD_ENFORCE_REDEEM_ALLOWLIST
    PSM_UPDATE_REDEEM_ALLOWLIST
    PSM_SET_USDC_YIELD_POSITION
    PSM_SET_NUM_BLOCKS_PER_INTERVAL
    PSM_SET_SHOULD_AUTO_DEPOSIT

struct EndaoLiquidityAction:
    legoId: uint256
    pool: address
    tokenA: address
    tokenB: address
    amountA: uint256
    amountB: uint256
    minAmountA: uint256
    minAmountB: uint256
    minLpAmount: uint256
    extraData: bytes32
    lpToken: address
    lpAmount: uint256

struct EndaoPartnerMintAction:
    partner: address
    asset: address
    amount: uint256

struct EndaoPartnerPoolAction:
    legoId: uint256
    pool: address
    partner: address
    asset: address
    amount: uint256
    minLpAmount: uint256

struct EndaoRepayAction:
    pool: address
    amount: uint256

struct EndaoTransfer:
    asset: address
    amount: uint256

struct PsmSetCanMintAction:
    canMint: bool

struct PsmSetMintFeeAction:
    fee: uint256

struct PsmSetMaxIntervalMintAction:
    maxGreenAmount: uint256

struct PsmSetShouldEnforceMintAllowlistAction:
    shouldEnforce: bool

struct PsmUpdateMintAllowlistAction:
    user: address
    isAllowed: bool

struct PsmSetCanRedeemAction:
    canRedeem: bool

struct PsmSetRedeemFeeAction:
    fee: uint256

struct PsmSetMaxIntervalRedeemAction:
    maxGreenAmount: uint256

struct PsmSetShouldEnforceRedeemAllowlistAction:
    shouldEnforce: bool

struct PsmUpdateRedeemAllowlistAction:
    user: address
    isAllowed: bool

struct PsmSetUsdcYieldPositionAction:
    legoId: uint256
    vaultToken: address

struct PsmSetNumBlocksPerIntervalAction:
    blocks: uint256

struct PsmSetShouldAutoDepositAction:
    shouldAutoDeposit: bool

event EndaomentDepositPerformed:
    legoId: uint256
    asset: indexed(address)
    vault: indexed(address)
    amount: uint256
    caller: indexed(address)

event EndaomentWithdrawalPerformed:
    legoId: uint256
    asset: indexed(address)
    vaultAddr: indexed(address)
    withdrawAmount: uint256
    caller: indexed(address)

event EndaomentEthToWethPerformed:
    amount: uint256
    caller: indexed(address)

event EndaomentWethToEthPerformed:
    amount: uint256
    caller: indexed(address)

event EndaomentClaimPerformed:
    legoId: uint256
    rewardToken: indexed(address)
    rewardAmount: uint256
    usdValue: uint256
    caller: indexed(address)

event EndaomentStabilizerPerformed:
    success: bool
    caller: indexed(address)

event EndaomentPsmTransferPerformed:
    amount: uint256
    usdValue: uint256
    caller: indexed(address)

event EndaomentVaultTransferPerformed:
    numAssets: uint256
    caller: indexed(address)

event EndaomentPsmDepositPerformed:
    amountDeposited: uint256
    caller: indexed(address)

event EndaomentPsmWithdrawPerformed:
    amountWithdrawn: uint256
    amountTransferred: uint256
    caller: indexed(address)

event EndaomentPsmTransferToFundsPerformed:
    amount: uint256
    caller: indexed(address)

event PendingEndaoTransferAction:
    asset: indexed(address)
    amount: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingEndaoSwapAction:
    numSwapInstructions: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingEndaoAddLiquidityAction:
    legoId: uint256
    pool: indexed(address)
    tokenA: indexed(address)
    tokenB: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingEndaoRemoveLiquidityAction:
    legoId: uint256
    pool: indexed(address)
    tokenA: indexed(address)
    tokenB: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingEndaoPartnerMintAction:
    partner: indexed(address)
    asset: indexed(address)
    amount: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingEndaoPartnerPoolAction:
    legoId: uint256
    pool: indexed(address)
    partner: indexed(address)
    asset: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingEndaoRepayAction:
    pool: indexed(address)
    amount: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingPsmSetCanMintAction:
    canMint: bool
    confirmationBlock: uint256
    actionId: uint256

event PendingPsmSetMintFeeAction:
    fee: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingPsmSetMaxIntervalMintAction:
    maxGreenAmount: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingPsmSetShouldEnforceMintAllowlistAction:
    shouldEnforce: bool
    confirmationBlock: uint256
    actionId: uint256

event PendingPsmUpdateMintAllowlistAction:
    user: indexed(address)
    isAllowed: bool
    confirmationBlock: uint256
    actionId: uint256

event PendingPsmSetCanRedeemAction:
    canRedeem: bool
    confirmationBlock: uint256
    actionId: uint256

event PendingPsmSetRedeemFeeAction:
    fee: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingPsmSetMaxIntervalRedeemAction:
    maxGreenAmount: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingPsmSetShouldEnforceRedeemAllowlistAction:
    shouldEnforce: bool
    confirmationBlock: uint256
    actionId: uint256

event PendingPsmUpdateRedeemAllowlistAction:
    user: indexed(address)
    isAllowed: bool
    confirmationBlock: uint256
    actionId: uint256

event PendingPsmSetUsdcYieldPositionAction:
    legoId: uint256
    vaultToken: indexed(address)
    confirmationBlock: uint256
    actionId: uint256

event PendingPsmSetNumBlocksPerIntervalAction:
    blocks: uint256
    confirmationBlock: uint256
    actionId: uint256

event PendingPsmSetShouldAutoDepositAction:
    shouldAutoDeposit: bool
    confirmationBlock: uint256
    actionId: uint256

event EndaoTransferExecuted:
    asset: indexed(address)
    amount: uint256

event EndaoSwapExecuted:
    numSwapInstructions: uint256

event EndaoAddLiquidityExecuted:
    legoId: uint256
    pool: indexed(address)
    tokenA: indexed(address)
    tokenB: indexed(address)

event EndaoRemoveLiquidityExecuted:
    legoId: uint256
    pool: indexed(address)
    tokenA: indexed(address)
    tokenB: indexed(address)

event EndaoPartnerMintExecuted:
    partner: indexed(address)
    asset: indexed(address)
    greenMinted: uint256

event EndaoPartnerPoolExecuted:
    legoId: uint256
    pool: indexed(address)
    partner: indexed(address)
    asset: indexed(address)

event EndaoRepayExecuted:
    pool: indexed(address)
    success: bool

event PsmSetCanMintExecuted:
    canMint: bool

event PsmSetMintFeeExecuted:
    fee: uint256

event PsmSetMaxIntervalMintExecuted:
    maxGreenAmount: uint256

event PsmSetShouldEnforceMintAllowlistExecuted:
    shouldEnforce: bool

event PsmUpdateMintAllowlistExecuted:
    user: indexed(address)
    isAllowed: bool

event PsmSetCanRedeemExecuted:
    canRedeem: bool

event PsmSetRedeemFeeExecuted:
    fee: uint256

event PsmSetMaxIntervalRedeemExecuted:
    maxGreenAmount: uint256

event PsmSetShouldEnforceRedeemAllowlistExecuted:
    shouldEnforce: bool

event PsmUpdateRedeemAllowlistExecuted:
    user: indexed(address)
    isAllowed: bool

event PsmSetUsdcYieldPositionExecuted:
    legoId: uint256
    vaultToken: indexed(address)

event PsmSetNumBlocksPerIntervalExecuted:
    blocks: uint256

event PsmSetShouldAutoDepositExecuted:
    shouldAutoDeposit: bool

# pending actions storage
actionType: public(HashMap[uint256, ActionType])
pendingEndaoSwapActions: public(HashMap[uint256, DynArray[ul.SwapInstruction, MAX_SWAP_INSTRUCTIONS]])
pendingEndaoAddLiquidityActions: public(HashMap[uint256, EndaoLiquidityAction])
pendingEndaoRemoveLiquidityActions: public(HashMap[uint256, EndaoLiquidityAction])
pendingEndaoPartnerMintActions: public(HashMap[uint256, EndaoPartnerMintAction])
pendingEndaoPartnerPoolActions: public(HashMap[uint256, EndaoPartnerPoolAction])
pendingEndaoRepayActions: public(HashMap[uint256, EndaoRepayAction])
pendingEndaoTransfer: public(HashMap[uint256, EndaoTransfer])
pendingPsmSetCanMintActions: public(HashMap[uint256, PsmSetCanMintAction])
pendingPsmSetMintFeeActions: public(HashMap[uint256, PsmSetMintFeeAction])
pendingPsmSetMaxIntervalMintActions: public(HashMap[uint256, PsmSetMaxIntervalMintAction])
pendingPsmSetShouldEnforceMintAllowlistActions: public(HashMap[uint256, PsmSetShouldEnforceMintAllowlistAction])
pendingPsmUpdateMintAllowlistActions: public(HashMap[uint256, PsmUpdateMintAllowlistAction])
pendingPsmSetCanRedeemActions: public(HashMap[uint256, PsmSetCanRedeemAction])
pendingPsmSetRedeemFeeActions: public(HashMap[uint256, PsmSetRedeemFeeAction])
pendingPsmSetMaxIntervalRedeemActions: public(HashMap[uint256, PsmSetMaxIntervalRedeemAction])
pendingPsmSetShouldEnforceRedeemAllowlistActions: public(HashMap[uint256, PsmSetShouldEnforceRedeemAllowlistAction])
pendingPsmUpdateRedeemAllowlistActions: public(HashMap[uint256, PsmUpdateRedeemAllowlistAction])
pendingPsmSetUsdcYieldPositionActions: public(HashMap[uint256, PsmSetUsdcYieldPositionAction])
pendingPsmSetNumBlocksPerIntervalActions: public(HashMap[uint256, PsmSetNumBlocksPerIntervalAction])
pendingPsmSetShouldAutoDepositActions: public(HashMap[uint256, PsmSetShouldAutoDepositAction])

MAX_SWAP_INSTRUCTIONS: constant(uint256) = 5
MAX_PROOFS: constant(uint256) = 25
MAX_ASSETS: constant(uint256) = 10

MISSION_CONTROL_ID: constant(uint256) = 5
ENDAOMENT_ID: constant(uint256) = 14
ENDAOMENT_PSM_ID: constant(uint256) = 22


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
def _hasPermsForLiteAction(_caller: address, _hasLiteAccess: bool) -> bool:
    if gov._canGovern(_caller):
        return True
    if _hasLiteAccess:
        mc: MissionControl = MissionControl(self._getMissionControlAddr())
        return staticcall mc.canPerformLiteAction(_caller)
    return False


# address getters


@view
@internal
def _getMissionControlAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(MISSION_CONTROL_ID)


@view
@internal
def _getEndaomentAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(ENDAOMENT_ID)


@view
@internal
def _getEndaomentPsmAddr() -> address:
    return staticcall RipeHq(gov._getRipeHqFromGov()).getAddr(ENDAOMENT_PSM_ID)


######################
# Endaoment Functions
######################


@external
def depositForYieldInEndaoment(_legoId: uint256, _asset: address, _vaultAddr: address = empty(address), _amount: uint256 = max_value(uint256), _extraData: bytes32 = empty(bytes32)) -> (uint256, address, uint256, uint256):
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms

    result: (uint256, address, uint256, uint256) = extcall Endaoment(self._getEndaomentAddr()).depositForYield(_legoId, _asset, _vaultAddr, _amount, _extraData)
    log EndaomentDepositPerformed(legoId=_legoId, asset=_asset, vault=result[1], amount=result[2], caller=msg.sender)
    return result


@external
def withdrawFromYieldInEndaoment(_legoId: uint256, _vaultToken: address, _amount: uint256 = max_value(uint256), _extraData: bytes32 = empty(bytes32)) -> (uint256, address, uint256, uint256):
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms

    result: (uint256, address, uint256, uint256) = extcall Endaoment(self._getEndaomentAddr()).withdrawFromYield(_legoId, _vaultToken, _amount, _extraData)
    log EndaomentWithdrawalPerformed(legoId=_legoId, asset=result[1], vaultAddr=_vaultToken, withdrawAmount=result[2], caller=msg.sender)
    return result


@external
def convertEthToWethInEndaoment(_amount: uint256 = max_value(uint256)) -> (uint256, uint256):
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms

    result: (uint256, uint256) = extcall Endaoment(self._getEndaomentAddr()).convertEthToWeth(_amount)
    log EndaomentEthToWethPerformed(amount=result[0], caller=msg.sender)
    return result


@external
def convertWethToEthInEndaoment(_amount: uint256 = max_value(uint256)) -> (uint256, uint256):
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms

    result: (uint256, uint256) = extcall Endaoment(self._getEndaomentAddr()).convertWethToEth(_amount)
    log EndaomentWethToEthPerformed(amount=result[0], caller=msg.sender)
    return result


@external
def claimIncentivesInEndaoment(_user: address, _legoId: uint256, _rewardToken: address = empty(address), _rewardAmount: uint256 = max_value(uint256), _proofs: DynArray[bytes32, MAX_PROOFS] = []) -> (uint256, uint256):
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms

    result: (uint256, uint256) = extcall Endaoment(self._getEndaomentAddr()).claimIncentives(_user, _legoId, _rewardToken, _rewardAmount, _proofs)
    log EndaomentClaimPerformed(legoId=_legoId, rewardToken=_rewardToken, rewardAmount=result[0], usdValue=result[1], caller=msg.sender)
    return result


@external
def stabilizeGreenRefPoolInEndaoment() -> bool:
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms

    success: bool = extcall Endaoment(self._getEndaomentAddr()).stabilizeGreenRefPool()
    log EndaomentStabilizerPerformed(success=success, caller=msg.sender)
    return success


@external
def transferFundsToEndaomentPsmInEndaoment(_amount: uint256 = max_value(uint256)) -> (uint256, uint256):
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms

    result: (uint256, uint256) = extcall Endaoment(self._getEndaomentAddr()).transferFundsToEndaomentPSM(_amount)
    log EndaomentPsmTransferPerformed(amount=result[0], usdValue=result[1], caller=msg.sender)
    return result


@external
def transferFundsToVaultInEndaoment(_assets: DynArray[address, MAX_ASSETS]):
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms
    assert len(_assets) != 0 # dev: no assets provided

    extcall Endaoment(self._getEndaomentAddr()).transferFundsToVault(_assets)
    log EndaomentVaultTransferPerformed(numAssets=len(_assets), caller=msg.sender)


########################
# EndaomentPSM Functions
########################


@external
def depositToYieldInPsm() -> uint256:
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms

    amountDeposited: uint256 = extcall EndaomentPSM(self._getEndaomentPsmAddr()).depositToYield()
    log EndaomentPsmDepositPerformed(amountDeposited=amountDeposited, caller=msg.sender)
    return amountDeposited


@external
def withdrawFromYieldInPsm(_amount: uint256 = max_value(uint256), _shouldTransferToEndaoFunds: bool = False, _shouldFullSweep: bool = False) -> (uint256, uint256):
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms

    result: (uint256, uint256) = extcall EndaomentPSM(self._getEndaomentPsmAddr()).withdrawFromYield(_amount, _shouldTransferToEndaoFunds, _shouldFullSweep)
    log EndaomentPsmWithdrawPerformed(amountWithdrawn=result[0], amountTransferred=result[1], caller=msg.sender)
    return result


@external
def transferUsdcToEndaomentFundsInPsm(_amount: uint256) -> uint256:
    assert self._hasPermsForLiteAction(msg.sender, True) # dev: no perms

    amountTransferred: uint256 = extcall EndaomentPSM(self._getEndaomentPsmAddr()).transferUsdcToEndaomentFunds(_amount)
    log EndaomentPsmTransferToFundsPerformed(amount=amountTransferred, caller=msg.sender)
    return amountTransferred


# timelock actions - Endaoment


@external
def performEndaomentTransfer(_asset: address, _amount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _asset != empty(address) # dev: invalid asset
    assert _amount != 0 # dev: invalid amount

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ENDAO_TRANSFER
    self.pendingEndaoTransfer[aid] = EndaoTransfer(
        asset=_asset,
        amount=_amount
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingEndaoTransferAction(
        asset=_asset,
        amount=_amount,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def performEndaomentSwap(_instructions: DynArray[ul.SwapInstruction, MAX_SWAP_INSTRUCTIONS]) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert len(_instructions) != 0 # dev: no swap instructions provided

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ENDAO_SWAP
    self.pendingEndaoSwapActions[aid] = _instructions

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingEndaoSwapAction(
        numSwapInstructions=len(_instructions),
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def addLiquidityInEndaoment(
    _legoId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256 = max_value(uint256),
    _amountB: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _minLpAmount: uint256 = 0,
    _extraData: bytes32 = empty(bytes32),
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _legoId != 0 # dev: invalid lego id

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ENDAO_ADD_LIQUIDITY
    self.pendingEndaoAddLiquidityActions[aid] = EndaoLiquidityAction(
        legoId=_legoId,
        pool=_pool,
        tokenA=_tokenA,
        tokenB=_tokenB,
        amountA=_amountA,
        amountB=_amountB,
        minAmountA=_minAmountA,
        minAmountB=_minAmountB,
        minLpAmount=_minLpAmount,
        extraData=_extraData,
        lpToken=empty(address),
        lpAmount=0,
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingEndaoAddLiquidityAction(
        legoId=_legoId,
        pool=_pool,
        tokenA=_tokenA,
        tokenB=_tokenB,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def removeLiquidityInEndaoment(
    _legoId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _lpToken: address,
    _lpAmount: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _extraData: bytes32 = empty(bytes32),
) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _legoId != 0 # dev: invalid lego id

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ENDAO_REMOVE_LIQUIDITY
    self.pendingEndaoRemoveLiquidityActions[aid] = EndaoLiquidityAction(
        legoId=_legoId,
        pool=_pool,
        tokenA=_tokenA,
        tokenB=_tokenB,
        amountA=0,
        amountB=0,
        minAmountA=_minAmountA,
        minAmountB=_minAmountB,
        minLpAmount=0,
        extraData=_extraData,
        lpToken=_lpToken,
        lpAmount=_lpAmount,
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingEndaoRemoveLiquidityAction(
        legoId=_legoId,
        pool=_pool,
        tokenA=_tokenA,
        tokenB=_tokenB,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def mintPartnerLiquidityInEndaoment(_partner: address, _asset: address, _amount: uint256 = max_value(uint256)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _partner != empty(address) # dev: invalid partner
    assert _asset != empty(address) # dev: invalid asset

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ENDAO_PARTNER_MINT
    self.pendingEndaoPartnerMintActions[aid] = EndaoPartnerMintAction(
        partner=_partner,
        asset=_asset,
        amount=_amount
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingEndaoPartnerMintAction(
        partner=_partner,
        asset=_asset,
        amount=_amount,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def addPartnerLiquidityInEndaoment(_legoId: uint256, _pool: address, _partner: address, _asset: address, _amount: uint256, _minLpAmount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _legoId != 0 # dev: invalid lego id
    assert _partner != empty(address) # dev: invalid partner

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ENDAO_PARTNER_POOL
    self.pendingEndaoPartnerPoolActions[aid] = EndaoPartnerPoolAction(
        legoId=_legoId,
        pool=_pool,
        partner=_partner,
        asset=_asset,
        amount=_amount,
        minLpAmount=_minLpAmount
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingEndaoPartnerPoolAction(
        legoId=_legoId,
        pool=_pool,
        partner=_partner,
        asset=_asset,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def repayPoolDebtInEndaoment(_pool: address, _amount: uint256 = max_value(uint256)) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _pool != empty(address) # dev: invalid pool

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.ENDAO_REPAY
    self.pendingEndaoRepayActions[aid] = EndaoRepayAction(
        pool=_pool,
        amount=_amount
    )

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingEndaoRepayAction(
        pool=_pool,
        amount=_amount,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


# timelock actions - EndaomentPSM


@external
def setPsmCanMint(_canMint: bool) -> uint256:
    # if False, allow lite access; otherwise require governance
    if not _canMint:
        assert self._hasPermsForLiteAction(msg.sender, True) or gov._canGovern(msg.sender) # dev: no perms
    else:
        assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PSM_SET_CAN_MINT
    self.pendingPsmSetCanMintActions[aid] = PsmSetCanMintAction(canMint=_canMint)

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPsmSetCanMintAction(
        canMint=_canMint,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def setPsmMintFee(_fee: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PSM_SET_MINT_FEE
    self.pendingPsmSetMintFeeActions[aid] = PsmSetMintFeeAction(fee=_fee)

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPsmSetMintFeeAction(
        fee=_fee,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def setPsmMaxIntervalMint(_maxGreenAmount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PSM_SET_MAX_INTERVAL_MINT
    self.pendingPsmSetMaxIntervalMintActions[aid] = PsmSetMaxIntervalMintAction(maxGreenAmount=_maxGreenAmount)

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPsmSetMaxIntervalMintAction(
        maxGreenAmount=_maxGreenAmount,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def setPsmShouldEnforceMintAllowlist(_shouldEnforce: bool) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PSM_SET_SHOULD_ENFORCE_MINT_ALLOWLIST
    self.pendingPsmSetShouldEnforceMintAllowlistActions[aid] = PsmSetShouldEnforceMintAllowlistAction(shouldEnforce=_shouldEnforce)

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPsmSetShouldEnforceMintAllowlistAction(
        shouldEnforce=_shouldEnforce,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def updatePsmMintAllowlist(_user: address, _isAllowed: bool) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _user != empty(address) # dev: invalid user

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PSM_UPDATE_MINT_ALLOWLIST
    self.pendingPsmUpdateMintAllowlistActions[aid] = PsmUpdateMintAllowlistAction(user=_user, isAllowed=_isAllowed)

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPsmUpdateMintAllowlistAction(
        user=_user,
        isAllowed=_isAllowed,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def setPsmCanRedeem(_canRedeem: bool) -> uint256:
    # if False, allow lite access; otherwise require governance
    if not _canRedeem:
        assert self._hasPermsForLiteAction(msg.sender, True) or gov._canGovern(msg.sender) # dev: no perms
    else:
        assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PSM_SET_CAN_REDEEM
    self.pendingPsmSetCanRedeemActions[aid] = PsmSetCanRedeemAction(canRedeem=_canRedeem)

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPsmSetCanRedeemAction(
        canRedeem=_canRedeem,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def setPsmRedeemFee(_fee: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PSM_SET_REDEEM_FEE
    self.pendingPsmSetRedeemFeeActions[aid] = PsmSetRedeemFeeAction(fee=_fee)

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPsmSetRedeemFeeAction(
        fee=_fee,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def setPsmMaxIntervalRedeem(_maxGreenAmount: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PSM_SET_MAX_INTERVAL_REDEEM
    self.pendingPsmSetMaxIntervalRedeemActions[aid] = PsmSetMaxIntervalRedeemAction(maxGreenAmount=_maxGreenAmount)

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPsmSetMaxIntervalRedeemAction(
        maxGreenAmount=_maxGreenAmount,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def setPsmShouldEnforceRedeemAllowlist(_shouldEnforce: bool) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PSM_SET_SHOULD_ENFORCE_REDEEM_ALLOWLIST
    self.pendingPsmSetShouldEnforceRedeemAllowlistActions[aid] = PsmSetShouldEnforceRedeemAllowlistAction(shouldEnforce=_shouldEnforce)

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPsmSetShouldEnforceRedeemAllowlistAction(
        shouldEnforce=_shouldEnforce,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def updatePsmRedeemAllowlist(_user: address, _isAllowed: bool) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _user != empty(address) # dev: invalid user

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PSM_UPDATE_REDEEM_ALLOWLIST
    self.pendingPsmUpdateRedeemAllowlistActions[aid] = PsmUpdateRedeemAllowlistAction(user=_user, isAllowed=_isAllowed)

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPsmUpdateRedeemAllowlistAction(
        user=_user,
        isAllowed=_isAllowed,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def setPsmUsdcYieldPosition(_legoId: uint256, _vaultToken: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert _legoId != 0 # dev: invalid lego id

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PSM_SET_USDC_YIELD_POSITION
    self.pendingPsmSetUsdcYieldPositionActions[aid] = PsmSetUsdcYieldPositionAction(legoId=_legoId, vaultToken=_vaultToken)

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPsmSetUsdcYieldPositionAction(
        legoId=_legoId,
        vaultToken=_vaultToken,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def setPsmNumBlocksPerInterval(_blocks: uint256) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PSM_SET_NUM_BLOCKS_PER_INTERVAL
    self.pendingPsmSetNumBlocksPerIntervalActions[aid] = PsmSetNumBlocksPerIntervalAction(blocks=_blocks)

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPsmSetNumBlocksPerIntervalAction(
        blocks=_blocks,
        confirmationBlock=confirmationBlock,
        actionId=aid
    )
    return aid


@external
def setPsmShouldAutoDeposit(_shouldAutoDeposit: bool) -> uint256:
    # if False, allow lite access; otherwise require governance
    if not _shouldAutoDeposit:
        assert self._hasPermsForLiteAction(msg.sender, True) or gov._canGovern(msg.sender) # dev: no perms
    else:
        assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.actionType[aid] = ActionType.PSM_SET_SHOULD_AUTO_DEPOSIT
    self.pendingPsmSetShouldAutoDepositActions[aid] = PsmSetShouldAutoDepositAction(shouldAutoDeposit=_shouldAutoDeposit)

    confirmationBlock: uint256 = timeLock._getActionConfirmationBlock(aid)
    log PendingPsmSetShouldAutoDepositAction(
        shouldAutoDeposit=_shouldAutoDeposit,
        confirmationBlock=confirmationBlock,
        actionId=aid
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

    if actionType == ActionType.ENDAO_TRANSFER:
        p: EndaoTransfer = self.pendingEndaoTransfer[_aid]
        extcall Endaoment(self._getEndaomentAddr()).transferFundsToGov(p.asset, p.amount)
        log EndaoTransferExecuted(asset=p.asset, amount=p.amount)

    elif actionType == ActionType.ENDAO_SWAP:
        swapInstructions: DynArray[ul.SwapInstruction, MAX_SWAP_INSTRUCTIONS] = self.pendingEndaoSwapActions[_aid]
        extcall Endaoment(self._getEndaomentAddr()).swapTokens(swapInstructions)
        log EndaoSwapExecuted(numSwapInstructions=len(swapInstructions))

    elif actionType == ActionType.ENDAO_ADD_LIQUIDITY:
        p: EndaoLiquidityAction = self.pendingEndaoAddLiquidityActions[_aid]
        extcall Endaoment(self._getEndaomentAddr()).addLiquidity(p.legoId, p.pool, p.tokenA, p.tokenB, p.amountA, p.amountB, p.minAmountA, p.minAmountB, p.minLpAmount, p.extraData)
        log EndaoAddLiquidityExecuted(legoId=p.legoId, pool=p.pool, tokenA=p.tokenA, tokenB=p.tokenB)

    elif actionType == ActionType.ENDAO_REMOVE_LIQUIDITY:
        p: EndaoLiquidityAction = self.pendingEndaoRemoveLiquidityActions[_aid]
        extcall Endaoment(self._getEndaomentAddr()).removeLiquidity(p.legoId, p.pool, p.tokenA, p.tokenB, p.lpToken, p.lpAmount, p.minAmountA, p.minAmountB, p.extraData)
        log EndaoRemoveLiquidityExecuted(legoId=p.legoId, pool=p.pool, tokenA=p.tokenA, tokenB=p.tokenB)

    elif actionType == ActionType.ENDAO_PARTNER_MINT:
        p: EndaoPartnerMintAction = self.pendingEndaoPartnerMintActions[_aid]
        greenMinted: uint256 = extcall Endaoment(self._getEndaomentAddr()).mintPartnerLiquidity(p.partner, p.asset, p.amount)
        log EndaoPartnerMintExecuted(partner=p.partner, asset=p.asset, greenMinted=greenMinted)

    elif actionType == ActionType.ENDAO_PARTNER_POOL:
        p: EndaoPartnerPoolAction = self.pendingEndaoPartnerPoolActions[_aid]
        extcall Endaoment(self._getEndaomentAddr()).addPartnerLiquidity(p.legoId, p.pool, p.partner, p.asset, p.amount, p.minLpAmount)
        log EndaoPartnerPoolExecuted(legoId=p.legoId, pool=p.pool, partner=p.partner, asset=p.asset)

    elif actionType == ActionType.ENDAO_REPAY:
        p: EndaoRepayAction = self.pendingEndaoRepayActions[_aid]
        success: bool = extcall Endaoment(self._getEndaomentAddr()).repayPoolDebt(p.pool, p.amount)
        log EndaoRepayExecuted(pool=p.pool, success=success)

    elif actionType == ActionType.PSM_SET_CAN_MINT:
        p: PsmSetCanMintAction = self.pendingPsmSetCanMintActions[_aid]
        extcall EndaomentPSM(self._getEndaomentPsmAddr()).setCanMint(p.canMint)
        log PsmSetCanMintExecuted(canMint=p.canMint)

    elif actionType == ActionType.PSM_SET_MINT_FEE:
        p: PsmSetMintFeeAction = self.pendingPsmSetMintFeeActions[_aid]
        extcall EndaomentPSM(self._getEndaomentPsmAddr()).setMintFee(p.fee)
        log PsmSetMintFeeExecuted(fee=p.fee)

    elif actionType == ActionType.PSM_SET_MAX_INTERVAL_MINT:
        p: PsmSetMaxIntervalMintAction = self.pendingPsmSetMaxIntervalMintActions[_aid]
        extcall EndaomentPSM(self._getEndaomentPsmAddr()).setMaxIntervalMint(p.maxGreenAmount)
        log PsmSetMaxIntervalMintExecuted(maxGreenAmount=p.maxGreenAmount)

    elif actionType == ActionType.PSM_SET_SHOULD_ENFORCE_MINT_ALLOWLIST:
        p: PsmSetShouldEnforceMintAllowlistAction = self.pendingPsmSetShouldEnforceMintAllowlistActions[_aid]
        extcall EndaomentPSM(self._getEndaomentPsmAddr()).setShouldEnforceMintAllowlist(p.shouldEnforce)
        log PsmSetShouldEnforceMintAllowlistExecuted(shouldEnforce=p.shouldEnforce)

    elif actionType == ActionType.PSM_UPDATE_MINT_ALLOWLIST:
        p: PsmUpdateMintAllowlistAction = self.pendingPsmUpdateMintAllowlistActions[_aid]
        extcall EndaomentPSM(self._getEndaomentPsmAddr()).updateMintAllowlist(p.user, p.isAllowed)
        log PsmUpdateMintAllowlistExecuted(user=p.user, isAllowed=p.isAllowed)

    elif actionType == ActionType.PSM_SET_CAN_REDEEM:
        p: PsmSetCanRedeemAction = self.pendingPsmSetCanRedeemActions[_aid]
        extcall EndaomentPSM(self._getEndaomentPsmAddr()).setCanRedeem(p.canRedeem)
        log PsmSetCanRedeemExecuted(canRedeem=p.canRedeem)

    elif actionType == ActionType.PSM_SET_REDEEM_FEE:
        p: PsmSetRedeemFeeAction = self.pendingPsmSetRedeemFeeActions[_aid]
        extcall EndaomentPSM(self._getEndaomentPsmAddr()).setRedeemFee(p.fee)
        log PsmSetRedeemFeeExecuted(fee=p.fee)

    elif actionType == ActionType.PSM_SET_MAX_INTERVAL_REDEEM:
        p: PsmSetMaxIntervalRedeemAction = self.pendingPsmSetMaxIntervalRedeemActions[_aid]
        extcall EndaomentPSM(self._getEndaomentPsmAddr()).setMaxIntervalRedeem(p.maxGreenAmount)
        log PsmSetMaxIntervalRedeemExecuted(maxGreenAmount=p.maxGreenAmount)

    elif actionType == ActionType.PSM_SET_SHOULD_ENFORCE_REDEEM_ALLOWLIST:
        p: PsmSetShouldEnforceRedeemAllowlistAction = self.pendingPsmSetShouldEnforceRedeemAllowlistActions[_aid]
        extcall EndaomentPSM(self._getEndaomentPsmAddr()).setShouldEnforceRedeemAllowlist(p.shouldEnforce)
        log PsmSetShouldEnforceRedeemAllowlistExecuted(shouldEnforce=p.shouldEnforce)

    elif actionType == ActionType.PSM_UPDATE_REDEEM_ALLOWLIST:
        p: PsmUpdateRedeemAllowlistAction = self.pendingPsmUpdateRedeemAllowlistActions[_aid]
        extcall EndaomentPSM(self._getEndaomentPsmAddr()).updateRedeemAllowlist(p.user, p.isAllowed)
        log PsmUpdateRedeemAllowlistExecuted(user=p.user, isAllowed=p.isAllowed)

    elif actionType == ActionType.PSM_SET_USDC_YIELD_POSITION:
        p: PsmSetUsdcYieldPositionAction = self.pendingPsmSetUsdcYieldPositionActions[_aid]
        extcall EndaomentPSM(self._getEndaomentPsmAddr()).setUsdcYieldPosition(p.legoId, p.vaultToken)
        log PsmSetUsdcYieldPositionExecuted(legoId=p.legoId, vaultToken=p.vaultToken)

    elif actionType == ActionType.PSM_SET_NUM_BLOCKS_PER_INTERVAL:
        p: PsmSetNumBlocksPerIntervalAction = self.pendingPsmSetNumBlocksPerIntervalActions[_aid]
        extcall EndaomentPSM(self._getEndaomentPsmAddr()).setNumBlocksPerInterval(p.blocks)
        log PsmSetNumBlocksPerIntervalExecuted(blocks=p.blocks)

    elif actionType == ActionType.PSM_SET_SHOULD_AUTO_DEPOSIT:
        p: PsmSetShouldAutoDepositAction = self.pendingPsmSetShouldAutoDepositActions[_aid]
        extcall EndaomentPSM(self._getEndaomentPsmAddr()).setShouldAutoDeposit(p.shouldAutoDeposit)
        log PsmSetShouldAutoDepositExecuted(shouldAutoDeposit=p.shouldAutoDeposit)

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
    assert timeLock._cancelAction(_aid) # dev: cannot cancel action
    self.actionType[_aid] = empty(ActionType)
