#            ___          ___                       ___          ___          ___          ___          ___                 
#           /\__\        /\  \        _____        /\  \        /\  \        /\  \        /\__\        /\  \                
#          /:/ _/_       \:\  \      /::\  \      /::\  \      /::\  \      |::\  \      /:/ _/_       \:\  \       ___     
#         /:/ /\__\       \:\  \    /:/\:\  \    /:/\:\  \    /:/\:\  \     |:|:\  \    /:/ /\__\       \:\  \     /\__\    
#        /:/ /:/ _/_  _____\:\  \  /:/  \:\__\  /:/ /::\  \  /:/  \:\  \  __|:|\:\  \  /:/ /:/ _/_  _____\:\  \   /:/  /    
#       /:/_/:/ /\__\/::::::::\__\/:/__/ \:|__|/:/_/:/\:\__\/:/__/ \:\__\/::::|_\:\__\/:/_/:/ /\__\/::::::::\__\ /:/__/     
#       \:\/:/ /:/  /\:\~~\~~\/__/\:\  \ /:/  /\:\/:/  \/__/\:\  \ /:/  /\:\~~\  \/__/\:\/:/ /:/  /\:\~~\~~\/__//::\  \     
#        \::/_/:/  /  \:\  \       \:\  /:/  /  \::/__/      \:\  /:/  /  \:\  \       \::/_/:/  /  \:\  \     /:/\:\  \    
#         \:\/:/  /    \:\  \       \:\/:/  /    \:\  \       \:\/:/  /    \:\  \       \:\/:/  /    \:\  \    \/__\:\  \   
#          \::/  /      \:\__\       \::/  /      \:\__\       \::/  /      \:\__\       \::/  /      \:\__\        \:\__\  
#           \/__/        \/__/        \/__/        \/__/        \/__/        \/__/        \/__/        \/__/         \/__/  
#
#     ╔════════════════════════════════════════════════════╗
#     ║  ** Endaoment **                                   ║
#     ║  Handles protocol-owned liquidity, peg management  ║
#     ╚════════════════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics

from interfaces import Department
from interfaces import UndyLego

from ethereum.ercs import IERC20
from ethereum.ercs import IERC721

interface CurvePool:
    def remove_liquidity_imbalance(_amounts: DynArray[uint256, 2], _maxLpBurnAmount: uint256, _recipient: address = msg.sender) -> uint256: nonpayable
    def add_liquidity(_amounts: DynArray[uint256, 2], _minLpAmountOut: uint256, _recipient: address = msg.sender) -> uint256: nonpayable
    def get_virtual_price() -> uint256: view

interface Ledger:
    def updateGreenPoolDebt(_pool: address, _amount: uint256, _isIncrement: bool): nonpayable
    def greenPoolDebt(_pool: address) -> uint256: view

interface PriceDesk:
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view
    def getAddr(_regId: uint256) -> address: view

interface GreenToken:
    def mint(_to: address, _amount: uint256): nonpayable
    def burn(_amount: uint256) -> bool: nonpayable

interface WethContract:
    def withdraw(_amount: uint256): nonpayable
    def deposit(): payable

interface CurvePrices:
    def getGreenStabilizerConfig() -> StabilizerConfig: view

interface UnderscoreRegistry:
    def getAddr(_id: uint256) -> address: view

interface MissionControl:
    def underscoreRegistry() -> address: view

struct StabilizerConfig:
    pool: address
    lpToken: address
    greenBalance: uint256
    greenRatio: uint256
    greenIndex: uint256
    stabilizerAdjustWeight: uint256
    stabilizerMaxPoolDebt: uint256

event WalletAction:
    op: uint8 
    asset1: indexed(address)
    asset2: indexed(address)
    amount1: uint256
    amount2: uint256
    usdValue: uint256
    legoId: uint256

event WalletActionExt:
    op: uint8
    asset1: indexed(address)
    asset2: indexed(address)
    tokenId: uint256
    amount1: uint256
    amount2: uint256
    usdValue: uint256
    extra: uint256

event EndaomentNftRecovered:
    collection: indexed(address)
    nftTokenId: uint256
    recipient: indexed(address)

event StabilizerPoolLiqAdded:
    pool: indexed(address)
    greenAmountAdded: uint256
    lpReceived: uint256
    poolDebtAdded: uint256

event StabilizerPoolLiqRemoved:
    pool: indexed(address)
    lpBurned: uint256
    greenAmountRemoved: uint256
    debtRepaid: uint256

event PoolDebtRepaid:
    pool: indexed(address)
    amount: uint256

event PartnerLiquidityAdded:
    partner: indexed(address)
    asset: indexed(address)
    partnerAmount: uint256
    greenAmount: uint256
    lpBalance: uint256

event PartnerLiquidityMinted:
    partner: indexed(address)
    asset: indexed(address)
    partnerAmount: uint256
    greenMinted: uint256

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_SWAP_INSTRUCTIONS: constant(uint256) = 5
MAX_TOKEN_PATH: constant(uint256) = 5
MAX_ASSETS: constant(uint256) = 10
MAX_LEGOS: constant(uint256) = 10
ERC721_RECEIVE_DATA: constant(Bytes[1024]) = b"UE721"
API_VERSION: constant(String[28]) = "0.1.0"
FIFTY_PERCENT: constant(uint256) = 50_00 # 50.00%
EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
LEGO_BOOK_ID: constant(uint256) = 4
CURVE_PRICES_ID: constant(uint256) = 2

WETH: public(immutable(address))
ETH: public(immutable(address))


@deploy
def __init__(_ripeHq: address, _weth: address, _eth: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, True, False) # can mint green only

    assert empty(address) not in [_weth, _eth] # dev: invalid addys
    WETH = _weth
    ETH = _eth


@view
@external
def onERC721Received(_operator: address, _owner: address, _tokenId: uint256, _data: Bytes[1024]) -> bytes4:
    # must implement method for safe NFT transfers
    return method_id("onERC721Received(address,address,uint256,bytes)", output_type = bytes4)


@payable
@external
def __default__():
    pass


#########
# Yield #
#########


# deposit


@nonreentrant
@external
def depositForYield(
    _legoId: uint256,
    _asset: address,
    _vaultAddr: address = empty(address),
    _amount: uint256 = max_value(uint256),
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, address, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    return self._depositForYield(_legoId, _asset, _vaultAddr, _amount, _extraData, True)


@internal
def _depositForYield(
    _legoId: uint256,
    _asset: address,
    _vaultAddr: address,
    _amount: uint256,
    _extraData: bytes32,
    _shouldGenerateEvent: bool,
) -> (uint256, address, uint256, uint256):
    legoAddr: address = self._getLegoAddr(_legoId)
    amount: uint256 = self._getAmountAndApprove(_asset, _amount, legoAddr) # doing approval here

    # deposit for yield
    assetAmount: uint256 = 0
    vaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    txUsdValue: uint256 = 0
    assetAmount, vaultToken, vaultTokenAmountReceived, txUsdValue = extcall UndyLego(legoAddr).depositForYield(_asset, amount, _vaultAddr, _extraData, self)
    self._resetApproval(_asset, legoAddr)

    if _shouldGenerateEvent:
        log WalletAction(
            op = 10,
            asset1 = _asset,
            asset2 = vaultToken,
            amount1 = assetAmount,
            amount2 = vaultTokenAmountReceived,
            usdValue = txUsdValue,
            legoId = _legoId,
        )
    return assetAmount, vaultToken, vaultTokenAmountReceived, txUsdValue


# withdraw


@nonreentrant
@external
def withdrawFromYield(
    _legoId: uint256,
    _vaultToken: address,
    _amount: uint256 = max_value(uint256),
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, address, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    return self._withdrawFromYield(_legoId, _vaultToken, _amount, _extraData, True)


@internal
def _withdrawFromYield(
    _legoId: uint256,
    _vaultToken: address,
    _amount: uint256,
    _extraData: bytes32,
    _shouldGenerateEvent: bool,
) -> (uint256, address, uint256, uint256):
    legoAddr: address = self._getLegoAddr(_legoId)
    amount: uint256 = _amount
    if _vaultToken != empty(address):
        amount = self._getAmountAndApprove(_vaultToken, _amount, empty(address)) # not approving here

        # some vault tokens require max value approval (comp v3)
        assert extcall IERC20(_vaultToken).approve(legoAddr, max_value(uint256), default_return_value = True) # dev: appr

    # withdraw from yield
    vaultTokenAmountBurned: uint256 = 0
    underlyingAsset: address = empty(address)
    underlyingAmount: uint256 = 0
    txUsdValue: uint256 = 0
    vaultTokenAmountBurned, underlyingAsset, underlyingAmount, txUsdValue = extcall UndyLego(legoAddr).withdrawFromYield(_vaultToken, amount, _extraData, self)

    if _vaultToken != empty(address):
        self._resetApproval(_vaultToken, legoAddr)

    if _shouldGenerateEvent:
        log WalletAction(
            op = 11,
            asset1 = _vaultToken,
            asset2 = underlyingAsset,
            amount1 = vaultTokenAmountBurned,
            amount2 = underlyingAmount,
            usdValue = txUsdValue,
            legoId = _legoId,
        )
    return vaultTokenAmountBurned, underlyingAsset, underlyingAmount, txUsdValue


# rebalance position


@nonreentrant
@external
def rebalanceYieldPosition(
    _fromLegoId: uint256,
    _fromVaultToken: address,
    _toLegoId: uint256,
    _toVaultAddr: address = empty(address),
    _fromVaultAmount: uint256 = max_value(uint256),
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, address, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms

    # withdraw
    vaultTokenAmountBurned: uint256 = 0
    underlyingAsset: address = empty(address)
    underlyingAmount: uint256 = 0
    withdrawTxUsdValue: uint256 = 0
    vaultTokenAmountBurned, underlyingAsset, underlyingAmount, withdrawTxUsdValue = self._withdrawFromYield(_fromLegoId, _fromVaultToken, _fromVaultAmount, _extraData, False)

    # deposit
    toVaultToken: address = empty(address)
    toVaultTokenAmountReceived: uint256 = 0
    depositTxUsdValue: uint256 = 0
    underlyingAmount, toVaultToken, toVaultTokenAmountReceived, depositTxUsdValue = self._depositForYield(_toLegoId, underlyingAsset, _toVaultAddr, underlyingAmount, _extraData, False)

    maxUsdValue: uint256 = max(withdrawTxUsdValue, depositTxUsdValue)
    log WalletAction(
        op = 12,
        asset1 = _fromVaultToken,
        asset2 = toVaultToken,
        amount1 = vaultTokenAmountBurned,
        amount2 = toVaultTokenAmountReceived,
        usdValue = maxUsdValue,
        legoId = _fromLegoId,
    )
    return underlyingAmount, toVaultToken, toVaultTokenAmountReceived, maxUsdValue


###################
# Swap / Exchange #
###################


@nonreentrant
@external
def swapTokens(_instructions: DynArray[UndyLego.SwapInstruction, MAX_SWAP_INSTRUCTIONS]) -> (address, uint256, address, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms

    tokenIn: address = empty(address)
    tokenOut: address = empty(address)
    legoIds: DynArray[uint256, MAX_LEGOS] = []
    tokenIn, tokenOut, legoIds = self._validateAndGetSwapInfo(_instructions)

    origAmountIn: uint256 = self._getAmountAndApprove(tokenIn, _instructions[0].amountIn, empty(address)) # not approving here
    amountIn: uint256 = origAmountIn
    lastTokenOut: address = empty(address)
    lastTokenOutAmount: uint256 = 0
    maxTxUsdValue: uint256 = 0

    # perform swaps
    for i: UndyLego.SwapInstruction in _instructions:
        if lastTokenOut != empty(address):
            newTokenIn: address = i.tokenPath[0]
            assert lastTokenOut == newTokenIn # dev: path
            amountIn = min(lastTokenOutAmount, staticcall IERC20(newTokenIn).balanceOf(self))
        
        thisTxUsdValue: uint256 = 0
        lastTokenOut, lastTokenOutAmount, thisTxUsdValue = self._performSwapInstruction(amountIn, i)
        maxTxUsdValue = max(maxTxUsdValue, thisTxUsdValue)

    log WalletAction(
        op = 20,
        asset1 = tokenIn,
        asset2 = lastTokenOut,
        amount1 = origAmountIn,
        amount2 = lastTokenOutAmount,
        usdValue = maxTxUsdValue,
        legoId = legoIds[0], # using just the first lego used
    )
    return tokenIn, origAmountIn, lastTokenOut, lastTokenOutAmount, maxTxUsdValue


@internal
def _performSwapInstruction(
    _amountIn: uint256,
    _i: UndyLego.SwapInstruction,
) -> (address, uint256, uint256):
    legoAddr: address = self._getLegoAddr(_i.legoId)
    assert legoAddr != empty(address) # dev: lego

    # tokens
    tokenIn: address = _i.tokenPath[0]
    tokenOut: address = _i.tokenPath[len(_i.tokenPath) - 1]
    tokenInAmount: uint256 = 0
    tokenOutAmount: uint256 = 0
    txUsdValue: uint256 = 0

    assert extcall IERC20(tokenIn).approve(legoAddr, _amountIn, default_return_value = True) # dev: appr
    tokenInAmount, tokenOutAmount, txUsdValue = extcall UndyLego(legoAddr).swapTokens(_amountIn, _i.minAmountOut, _i.tokenPath, _i.poolPath, self)
    self._resetApproval(tokenIn, legoAddr)
    return tokenOut, tokenOutAmount, txUsdValue


@internal
def _validateAndGetSwapInfo(_instructions: DynArray[UndyLego.SwapInstruction, MAX_SWAP_INSTRUCTIONS]) -> (address, address, DynArray[uint256, MAX_LEGOS]):
    numSwapInstructions: uint256 = len(_instructions)
    assert numSwapInstructions != 0 # dev: swaps

    # lego ids, make sure token paths are valid
    legoIds: DynArray[uint256, MAX_LEGOS] = []
    for i: UndyLego.SwapInstruction in _instructions:
        assert len(i.tokenPath) >= 2 # dev: path
        if i.legoId not in legoIds:
            legoIds.append(i.legoId)

    # finalize tokens
    firstRoutePath: DynArray[address, MAX_TOKEN_PATH] = _instructions[0].tokenPath
    tokenIn: address = firstRoutePath[0]
    tokenOut: address = empty(address)

    if numSwapInstructions == 1:
        tokenOut = firstRoutePath[len(firstRoutePath) - 1]
    else:
        lastRoutePath: DynArray[address, MAX_TOKEN_PATH] = _instructions[numSwapInstructions - 1].tokenPath
        tokenOut = lastRoutePath[len(lastRoutePath) - 1]

    assert empty(address) not in [tokenIn, tokenOut] # dev: path
    return tokenIn, tokenOut, legoIds


# mint / redeem


@nonreentrant
@external
def mintOrRedeemAsset(
    _legoId: uint256,
    _tokenIn: address,
    _tokenOut: address,
    _amountIn: uint256 = max_value(uint256),
    _minAmountOut: uint256 = 0,
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, uint256, bool, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    legoAddr: address = self._getLegoAddr(_legoId)

    # mint or redeem asset
    tokenInAmount: uint256 = self._getAmountAndApprove(_tokenIn, _amountIn, legoAddr) # doing approval here
    tokenOutAmount: uint256 = 0
    isPending: bool = False
    txUsdValue: uint256 = 0
    tokenInAmount, tokenOutAmount, isPending, txUsdValue = extcall UndyLego(legoAddr).mintOrRedeemAsset(_tokenIn, _tokenOut, tokenInAmount, _minAmountOut, _extraData, self)
    self._resetApproval(_tokenIn, legoAddr)

    log WalletAction(
        op = 21,
        asset1 = _tokenIn,
        asset2 = _tokenOut,
        amount1 = tokenInAmount,
        amount2 = tokenOutAmount,
        usdValue = txUsdValue,
        legoId = _legoId,
    )
    return tokenInAmount, tokenOutAmount, isPending, txUsdValue


@nonreentrant
@external
def confirmMintOrRedeemAsset(
    _legoId: uint256,
    _tokenIn: address,
    _tokenOut: address,
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    legoAddr: address = self._getLegoAddr(_legoId)

    # confirm mint or redeem asset (if there is a delay on action)
    tokenOutAmount: uint256 = 0
    txUsdValue: uint256 = 0
    tokenOutAmount, txUsdValue = extcall UndyLego(legoAddr).confirmMintOrRedeemAsset(_tokenIn, _tokenOut, _extraData, self)

    log WalletAction(
        op = 22,
        asset1 = _tokenIn,
        asset2 = _tokenOut,
        amount1 = 0,
        amount2 = tokenOutAmount,
        usdValue = txUsdValue,
        legoId = _legoId,
    )
    return tokenOutAmount, txUsdValue


#################
# Claim Rewards #
#################


@nonreentrant
@external
def claimRewards(
    _legoId: uint256,
    _rewardToken: address = empty(address),
    _rewardAmount: uint256 = max_value(uint256),
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    legoAddr: address = self._getLegoAddr(_legoId)

    self._checkLegoAccessForAction(legoAddr, UndyLego.ActionType.REWARDS)

    # claim rewards
    rewardAmount: uint256 = 0
    txUsdValue: uint256 = 0
    rewardAmount, txUsdValue = extcall UndyLego(legoAddr).claimRewards(self, _rewardToken, _rewardAmount, _extraData)

    log WalletAction(
        op = 50,
        asset1 = _rewardToken,
        asset2 = legoAddr,
        amount1 = rewardAmount,
        amount2 = 0,
        usdValue = txUsdValue,
        legoId = _legoId,
    )
    return rewardAmount, txUsdValue


###############
# Wrapped ETH #
###############


# eth -> weth


@nonreentrant
@payable
@external
def convertEthToWeth(_amount: uint256 = max_value(uint256)) -> (uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms

    # convert eth to weth
    weth: address = WETH
    amount: uint256 = min(_amount, self.balance)
    assert amount != 0 # dev: no amt
    extcall WethContract(weth).deposit(value = amount)

    txUsdValue: uint256 = staticcall PriceDesk(addys._getPriceDeskAddr()).getUsdValue(weth, amount, False)
    log WalletAction(
        op = 2,
        asset1 = ETH,
        asset2 = weth,
        amount1 = msg.value,
        amount2 = amount,
        usdValue = txUsdValue,
        legoId = 0,
    )
    return amount, txUsdValue


# weth -> eth


@nonreentrant
@external
def convertWethToEth(_amount: uint256 = max_value(uint256)) -> (uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms

    # convert weth to eth
    weth: address = WETH
    amount: uint256 = self._getAmountAndApprove(weth, _amount, empty(address)) # nothing to approve
    extcall WethContract(weth).withdraw(amount)

    txUsdValue: uint256 = staticcall PriceDesk(addys._getPriceDeskAddr()).getUsdValue(weth, amount, False)
    log WalletAction(
        op = 3,
        asset1 = weth,
        asset2 = ETH,
        amount1 = amount,
        amount2 = amount,
        usdValue = txUsdValue,
        legoId = 0,
    )
    return amount, txUsdValue


######################
# Liquidity - Simple #
######################


# add liquidity (simple)


@nonreentrant
@external
def addLiquidity(
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
) -> (uint256, uint256, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    lpToken: address = empty(address)
    lpAmountReceived: uint256 = 0
    addedTokenA: uint256 = 0
    addedTokenB: uint256 = 0
    txUsdValue: uint256 = 0
    lpToken, lpAmountReceived, addedTokenA, addedTokenB, txUsdValue = self._addLiquidity(_legoId, _pool, _tokenA, _tokenB, _amountA, _amountB, _minAmountA, _minAmountB, _minLpAmount, _extraData)
    return lpAmountReceived, addedTokenA, addedTokenB, txUsdValue


@internal
def _addLiquidity(
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
) -> (address, uint256, uint256, uint256, uint256):
    legoAddr: address = self._getLegoAddr(_legoId)

    # token approvals
    amountA: uint256 = 0
    if _amountA != 0:
        amountA = self._getAmountAndApprove(_tokenA, _amountA, legoAddr)
    amountB: uint256 = 0
    if _amountB != 0:
        amountB = self._getAmountAndApprove(_tokenB, _amountB, legoAddr)

    # add liquidity via lego partner
    lpToken: address = empty(address)
    lpAmountReceived: uint256 = 0
    addedTokenA: uint256 = 0
    addedTokenB: uint256 = 0
    txUsdValue: uint256 = 0
    lpToken, lpAmountReceived, addedTokenA, addedTokenB, txUsdValue = extcall UndyLego(legoAddr).addLiquidity(_pool, _tokenA, _tokenB, amountA, amountB, _minAmountA, _minAmountB, _minLpAmount, _extraData, self)

    # remove approvals
    if amountA != 0:
        self._resetApproval(_tokenA, legoAddr)
    if amountB != 0:
        self._resetApproval(_tokenB, legoAddr)

    log WalletAction(
        op = 30,
        asset1 = _tokenA,
        asset2 = _tokenB,
        amount1 = addedTokenA,
        amount2 = addedTokenB,
        usdValue = txUsdValue,
        legoId = _legoId,
    )
    return lpToken, lpAmountReceived, addedTokenA, addedTokenB, txUsdValue


# remove liquidity (simple)


@nonreentrant
@external
def removeLiquidity(
    _legoId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _lpToken: address,
    _lpAmount: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, uint256, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    return self._removeLiquidity(_legoId, _pool, _tokenA, _tokenB, _lpToken, _lpAmount, _minAmountA, _minAmountB, _extraData)


@internal
def _removeLiquidity(
    _legoId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _lpToken: address,
    _lpAmount: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, uint256, uint256, uint256):
    legoAddr: address = self._getLegoAddr(_legoId)

    # remove liquidity via lego partner
    amountAReceived: uint256 = 0
    amountBReceived: uint256 = 0
    lpAmountBurned: uint256 = 0
    txUsdValue: uint256 = 0
    lpAmount: uint256 = self._getAmountAndApprove(_lpToken, _lpAmount, legoAddr)
    amountAReceived, amountBReceived, lpAmountBurned, txUsdValue = extcall UndyLego(legoAddr).removeLiquidity(_pool, _tokenA, _tokenB, _lpToken, lpAmount, _minAmountA, _minAmountB, _extraData, self)
    self._resetApproval(_lpToken, legoAddr)

    log WalletAction(
        op = 31,
        asset1 = _tokenA,
        asset2 = _tokenB,
        amount1 = amountAReceived,
        amount2 = amountBReceived,
        usdValue = txUsdValue,
        legoId = _legoId,
    )
    return amountAReceived, amountBReceived, lpAmountBurned, txUsdValue


############################
# Liquidity - Concentrated #
############################


@nonreentrant
@external
def addLiquidityConcentrated(
    _legoId: uint256,
    _nftAddr: address,
    _nftTokenId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256 = max_value(uint256),
    _amountB: uint256 = max_value(uint256),
    _tickLower: int24 = min_value(int24),
    _tickUpper: int24 = max_value(int24),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, uint256, uint256, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    legoAddr: address = self._getLegoAddr(_legoId)

    # token approvals
    amountA: uint256 = 0
    if _amountA != 0:
        amountA = self._getAmountAndApprove(_tokenA, _amountA, legoAddr)
    amountB: uint256 = 0
    if _amountB != 0:
        amountB = self._getAmountAndApprove(_tokenB, _amountB, legoAddr)

    # transfer nft to lego (if applicable)
    hasNftLiqPosition: bool = _nftAddr != empty(address) and _nftTokenId != 0
    if hasNftLiqPosition:
        extcall IERC721(_nftAddr).safeTransferFrom(self, legoAddr, _nftTokenId, ERC721_RECEIVE_DATA)

    # add liquidity via lego partner
    liqAdded: uint256 = 0
    addedTokenA: uint256 = 0
    addedTokenB: uint256 = 0
    nftTokenId: uint256 = 0
    txUsdValue: uint256 = 0
    liqAdded, addedTokenA, addedTokenB, nftTokenId, txUsdValue = extcall UndyLego(legoAddr).addLiquidityConcentrated(_nftTokenId, _pool, _tokenA, _tokenB, _tickLower, _tickUpper, amountA, amountB, _minAmountA, _minAmountB, _extraData, self)

    # make sure nft is back
    assert staticcall IERC721(_nftAddr).ownerOf(nftTokenId) == self # dev: nft not returned

    # remove approvals
    if amountA != 0:
        self._resetApproval(_tokenA, legoAddr)
    if amountB != 0:
        self._resetApproval(_tokenB, legoAddr)

    log WalletActionExt(
        op = 32,
        asset1 = _tokenA,
        asset2 = _tokenB,
        tokenId = nftTokenId,
        amount1 = addedTokenA,
        amount2 = addedTokenB,
        usdValue = txUsdValue,
        extra = liqAdded,
    )
    return liqAdded, addedTokenA, addedTokenB, nftTokenId, txUsdValue


@nonreentrant
@external
def removeLiquidityConcentrated(
    _legoId: uint256,
    _nftAddr: address,
    _nftTokenId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _liqToRemove: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
    _extraData: bytes32 = empty(bytes32),
) -> (uint256, uint256, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    legoAddr: address = self._getLegoAddr(_legoId)

    # must have nft liq position
    assert _nftAddr != empty(address) # dev: invalid nft addr
    assert _nftTokenId != 0 # dev: invalid nft token id
    extcall IERC721(_nftAddr).safeTransferFrom(self, legoAddr, _nftTokenId, ERC721_RECEIVE_DATA)

    # remove liquidity via lego partner
    amountAReceived: uint256 = 0
    amountBReceived: uint256 = 0
    liqRemoved: uint256 = 0
    isDepleted: bool = False
    txUsdValue: uint256 = 0
    amountAReceived, amountBReceived, liqRemoved, isDepleted, txUsdValue = extcall UndyLego(legoAddr).removeLiquidityConcentrated(_nftTokenId, _pool, _tokenA, _tokenB, _liqToRemove, _minAmountA, _minAmountB, _extraData, self)

    # validate the nft came back (if not depleted)
    if not isDepleted:
        assert staticcall IERC721(_nftAddr).ownerOf(_nftTokenId) == self # dev: nft not returned

    log WalletActionExt(
        op = 33,
        asset1 = _tokenA,
        asset2 = _tokenB,
        tokenId = _nftTokenId,
        amount1 = amountAReceived,
        amount2 = amountBReceived,
        usdValue = txUsdValue,
        extra = liqRemoved,
    )
    return amountAReceived, amountBReceived, liqRemoved, txUsdValue


####################
# Green Stabilizer #
####################


@external
def stabilizeGreenRefPool() -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    a: addys.Addys = addys._getAddys()

    curvePrices: address = staticcall PriceDesk(a.priceDesk).getAddr(CURVE_PRICES_ID)
    data: StabilizerConfig = staticcall CurvePrices(curvePrices).getGreenStabilizerConfig()
    if data.pool == empty(address) or data.greenBalance == 0:
        return False

    # current profits
    lpBalance: uint256 = staticcall IERC20(data.lpToken).balanceOf(self)
    leftoverGreen: uint256 = staticcall IERC20(a.greenToken).balanceOf(self)
    poolDebt: uint256 = staticcall Ledger(a.ledger).greenPoolDebt(data.pool)
    initialProfit: uint256 = self._calcProfitForStabilizer(data.pool, lpBalance, leftoverGreen, poolDebt)

    # add/remove Green to pool (50% ratio is fully balanced)
    didAdjust: bool = False
    if data.greenRatio < FIFTY_PERCENT:
        didAdjust = self._addStabilizerGreenLiquidity(poolDebt, leftoverGreen, data, a.greenToken, a.ledger)
    else:
        didAdjust = self._removeStabilizerGreenLiquidity(lpBalance, poolDebt, data, a.greenToken, a.ledger)

    # calc new profits
    lpBalance = staticcall IERC20(data.lpToken).balanceOf(self)
    leftoverGreen = staticcall IERC20(a.greenToken).balanceOf(self)
    poolDebt = staticcall Ledger(a.ledger).greenPoolDebt(data.pool)
    newProfit: uint256 = self._calcProfitForStabilizer(data.pool, lpBalance, leftoverGreen, poolDebt)
    assert newProfit >= initialProfit # dev: stabilizer was not profitable

    return didAdjust


# add green liq


@internal
def _addStabilizerGreenLiquidity(
    _poolDebt: uint256,
    _leftoverGreen: uint256,
    _data: StabilizerConfig,
    _greenToken: address,
    _ledger: address,
) -> bool:
    greenAmountToAdd: uint256 = self._getGreenAmountToAdd(_poolDebt, _leftoverGreen, _data)
    if greenAmountToAdd == 0:
        return False # debt max reached

    # mint green, save debt
    newDebt: uint256 = 0
    if greenAmountToAdd > _leftoverGreen:
        newDebt = greenAmountToAdd - _leftoverGreen
        self._addPoolDebt(_data.pool, newDebt, _greenToken, _ledger)

    # add liquidity
    assert extcall IERC20(_greenToken).approve(_data.pool, greenAmountToAdd, default_return_value=True) # dev: approval failed
    amounts: DynArray[uint256, 2] = [0, 0]
    amounts[_data.greenIndex] = greenAmountToAdd
    lpReceived: uint256 = extcall CurvePool(_data.pool).add_liquidity(amounts, 0, self)
    assert extcall IERC20(_greenToken).approve(_data.pool, 0, default_return_value=True) # dev: approval failed

    log StabilizerPoolLiqAdded(pool=_data.pool, greenAmountAdded=greenAmountToAdd, lpReceived=lpReceived, poolDebtAdded=newDebt)
    return lpReceived != 0


@view
@internal
def _getGreenAmountToAdd(
    _poolDebt: uint256,
    _leftoverGreen: uint256,
    _data: StabilizerConfig,
) -> uint256:
    # only add green when green ratio < 50% (pool has excess other asset)
    if _data.greenRatio >= FIFTY_PERCENT:
        return 0
    
    totalPoolBalance: uint256 = _data.greenBalance * HUNDRED_PERCENT // _data.greenRatio
    targetBalance: uint256 = totalPoolBalance // 2
    
    # safe subtraction: only proceed if targetBalance > greenBalance
    if targetBalance <= _data.greenBalance:
        return 0
    
    greenAdjustFull: uint256 = (targetBalance - _data.greenBalance) * 2
    greenAdjustWeighted: uint256 = greenAdjustFull * _data.stabilizerAdjustWeight // HUNDRED_PERCENT

    debtAvail: uint256 = 0 
    if _data.stabilizerMaxPoolDebt > _poolDebt:
        debtAvail = _data.stabilizerMaxPoolDebt - _poolDebt

    return min(greenAdjustWeighted, debtAvail + _leftoverGreen)


@view
@external
def getGreenAmountToAddInStabilizer() -> uint256:
    curvePrices: address = staticcall PriceDesk(addys._getPriceDeskAddr()).getAddr(CURVE_PRICES_ID)
    data: StabilizerConfig = staticcall CurvePrices(curvePrices).getGreenStabilizerConfig()
    if data.pool == empty(address) or data.greenBalance == 0:
        return 0
    poolDebt: uint256 = staticcall Ledger(addys._getLedgerAddr()).greenPoolDebt(data.pool)
    leftoverGreen: uint256 = staticcall IERC20(addys._getGreenToken()).balanceOf(self)
    return self._getGreenAmountToAdd(poolDebt, leftoverGreen, data)


# remove green liq


@internal
def _removeStabilizerGreenLiquidity(
    _lpBalance: uint256,
    _poolDebt: uint256,
    _data: StabilizerConfig,
    _greenToken: address,
    _ledger: address,
) -> bool:
    greenAmount: uint256 = self._getGreenAmountToRemove(_lpBalance, _poolDebt, _data)
    if greenAmount == 0:
        return False # nothing to remove 

    # remove liquidity
    assert extcall IERC20(_data.lpToken).approve(_data.pool, _lpBalance, default_return_value=True) # dev: approval failed
    amounts: DynArray[uint256, 2] = [0, 0]
    amounts[_data.greenIndex] = greenAmount
    lpBurned: uint256 = extcall CurvePool(_data.pool).remove_liquidity_imbalance(amounts, max_value(uint256), self)
    assert extcall IERC20(_data.lpToken).approve(_data.pool, 0, default_return_value=True) # dev: approval failed

    # update pool debt
    greenAmount = min(greenAmount, staticcall IERC20(_greenToken).balanceOf(self))
    debtToRepay: uint256 = min(greenAmount, _poolDebt)
    if debtToRepay != 0:
        self._repayPoolDebt(_data.pool, debtToRepay, _greenToken, _ledger)

    log StabilizerPoolLiqRemoved(pool=_data.pool, lpBurned=lpBurned, greenAmountRemoved=greenAmount, debtRepaid=debtToRepay)
    return lpBurned != 0 and greenAmount != 0


@view
@internal
def _getGreenAmountToRemove(
    _lpBalance: uint256,
    _poolDebt: uint256,
    _data: StabilizerConfig,
) -> uint256:
    # only remove green when green ratio > 50% (pool has excess green)
    if _data.greenRatio <= FIFTY_PERCENT:
        return 0
    
    totalPoolBalance: uint256 = _data.greenBalance * HUNDRED_PERCENT // _data.greenRatio
    targetBalance: uint256 = totalPoolBalance // 2
    
    # safe subtraction: only proceed if greenBalance > targetBalance
    if _data.greenBalance <= targetBalance:
        return 0
    
    greenAdjustFull: uint256 = (_data.greenBalance - targetBalance) * 2
    greenAdjustWeighted: uint256 = greenAdjustFull * _data.stabilizerAdjustWeight // HUNDRED_PERCENT
    maxGreenToRemove: uint256 = max(_poolDebt, _data.greenBalance * _lpBalance // staticcall IERC20(_data.lpToken).totalSupply())
    return min(greenAdjustWeighted, maxGreenToRemove)


@view
@external
def getGreenAmountToRemoveInStabilizer() -> uint256:
    curvePrices: address = staticcall PriceDesk(addys._getPriceDeskAddr()).getAddr(CURVE_PRICES_ID)
    data: StabilizerConfig = staticcall CurvePrices(curvePrices).getGreenStabilizerConfig()
    if data.pool == empty(address) or data.greenBalance == 0:
        return 0
    lpBalance: uint256 = staticcall IERC20(data.lpToken).balanceOf(self)
    poolDebt: uint256 = staticcall Ledger(addys._getLedgerAddr()).greenPoolDebt(data.pool)
    return self._getGreenAmountToRemove(lpBalance, poolDebt, data)


# utilities


@view
@internal
def _calcProfitForStabilizer(
    _pool: address,
    _lpBalance: uint256,
    _greenBalance: uint256,
    _poolDebt: uint256,
) -> uint256:
    netGreenBal: uint256 = 0
    netGreenDebt: uint256 = 0
    if _poolDebt > _greenBalance:
        netGreenDebt = _poolDebt - _greenBalance
        netGreenBal = 0
    else:
        netGreenBal = _greenBalance - _poolDebt

    virtualPrice: uint256 = staticcall CurvePool(_pool).get_virtual_price()

    lpDebt: uint256 = 0
    if netGreenDebt != 0:
        lpDebt = netGreenDebt * EIGHTEEN_DECIMALS // virtualPrice

    if _lpBalance <= lpDebt:
        return 0
    else:
        netGreenBalInLp: uint256 = netGreenBal * EIGHTEEN_DECIMALS // virtualPrice
        return (_lpBalance - lpDebt) + netGreenBalInLp


#####################
# Partner Liquidity #
#####################


@external
def mintPartnerLiquidity(_partner: address, _asset: address, _amount: uint256 = max_value(uint256)) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    a: addys.Addys = addys._getAddys()
    partnerAmount: uint256 = 0
    greenMinted: uint256 = 0
    partnerAmount, greenMinted = self._mintPartnerLiquidity(_partner, _asset, _amount, a.priceDesk, a.greenToken)
    log PartnerLiquidityMinted(partner=_partner, asset=_asset, partnerAmount=partnerAmount, greenMinted=greenMinted)
    return greenMinted


@external
def addPartnerLiquidity(
    _legoId: uint256,
    _pool: address,
    _partner: address,
    _asset: address,
    _amount: uint256 = max_value(uint256),
    _minLpAmount: uint256 = 0,
) -> (uint256, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    a: addys.Addys = addys._getAddys()

    # mint green
    partnerAmount: uint256 = 0
    greenAmount: uint256 = 0
    partnerAmount, greenAmount = self._mintPartnerLiquidity(_partner, _asset, _amount, a.priceDesk, a.greenToken)

    # add liquidity
    lpToken: address = empty(address)
    lpAmountReceived: uint256 = 0
    liqAmountA: uint256 = 0
    liqAmountB: uint256 = 0
    usdValue: uint256 = 0
    lpToken, lpAmountReceived, liqAmountA, liqAmountB, usdValue = self._addLiquidity(_legoId, _pool, _asset, a.greenToken, partnerAmount, greenAmount, 0, 0, _minLpAmount)

    # share lp balance with partner
    lpBalance: uint256 = staticcall IERC20(lpToken).balanceOf(self)
    assert lpBalance != 0 # dev: no liquidity added
    assert extcall IERC20(lpToken).transfer(_partner, lpBalance // 2, default_return_value=True) # dev: could not transfer

    # add pool debt
    extcall Ledger(a.ledger).updateGreenPoolDebt(_pool, greenAmount, True)

    log PartnerLiquidityAdded(partner=_partner, asset=_asset, partnerAmount=partnerAmount, greenAmount=greenAmount, lpBalance=lpBalance)
    return lpAmountReceived, liqAmountA, liqAmountB


# utils


@internal
def _mintPartnerLiquidity(
    _partner: address,
    _asset: address,
    _amount: uint256,
    _priceDesk: address,
    _greenToken: address,
) -> (uint256, uint256):
    partnerAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(_partner))
    assert partnerAmount != 0 # dev: no asset to add
    assert extcall IERC20(_asset).transferFrom(_partner, self, partnerAmount, default_return_value=True) # dev: transfer failed

    usdValue: uint256 = staticcall PriceDesk(_priceDesk).getUsdValue(_asset, partnerAmount, True)
    assert usdValue != 0 # dev: invalid asset

    # mint green
    extcall GreenToken(_greenToken).mint(self, usdValue)
    return partnerAmount, usdValue


#############
# Pool Debt #
#############


@external
def repayPoolDebt(_pool: address, _amount: uint256 = max_value(uint256)) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    a: addys.Addys = addys._getAddys()

    greenAvail: uint256 = min(_amount, staticcall IERC20(a.greenToken).balanceOf(self))
    repayAmount: uint256 = min(greenAvail, staticcall Ledger(a.ledger).greenPoolDebt(_pool))
    assert repayAmount != 0 # dev: no debt to repay

    self._repayPoolDebt(_pool, repayAmount, a.greenToken, a.ledger)
    log PoolDebtRepaid(pool=_pool, amount=repayAmount)
    return True


#############
# Utilities #
#############


# lego addr


@view
@internal
def _getLegoAddr(_legoId: uint256) -> address:
    underscoreRegistry: address = staticcall MissionControl(addys._getMissionControlAddr()).underscoreRegistry()
    assert underscoreRegistry != empty(address) # dev: invalid underscore registry
    legoBook: address = staticcall UnderscoreRegistry(underscoreRegistry).getAddr(LEGO_BOOK_ID)
    legoAddr: address = staticcall UnderscoreRegistry(legoBook).getAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego
    return legoAddr


# approve


@internal
def _getAmountAndApprove(_token: address, _amount: uint256, _legoAddr: address) -> uint256:
    amount: uint256 = min(_amount, staticcall IERC20(_token).balanceOf(self))
    assert amount != 0 # dev: no balance for _token
    if _legoAddr != empty(address):
        assert extcall IERC20(_token).approve(_legoAddr, amount, default_return_value = True) # dev: appr
    return amount


# reset approval


@internal
def _resetApproval(_token: address, _legoAddr: address):
    if _legoAddr != empty(address):
        assert extcall IERC20(_token).approve(_legoAddr, 0, default_return_value = True) # dev: appr


# recover nft


@external
def recoverNft(_collection: address, _nftTokenId: uint256, _recipient: address):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    extcall IERC721(_collection).safeTransferFrom(self, _recipient, _nftTokenId)
    log EndaomentNftRecovered(collection=_collection, nftTokenId=_nftTokenId, recipient=_recipient)


# pool debt


@internal
def _repayPoolDebt(
    _pool: address,
    _amount: uint256,
    _greenToken: address,
    _ledger: address,
):
    assert extcall GreenToken(_greenToken).burn(_amount) # dev: could not burn green
    extcall Ledger(_ledger).updateGreenPoolDebt(_pool, _amount, False)


@internal
def _addPoolDebt(
    _pool: address,
    _amount: uint256,
    _greenToken: address,
    _ledger: address,
):
    extcall GreenToken(_greenToken).mint(self, _amount)
    extcall Ledger(_ledger).updateGreenPoolDebt(_pool, _amount, True)


# allow lego to perform action


@internal
def _checkLegoAccessForAction(_legoAddr: address, _action: UndyLego.ActionType):
    if _legoAddr == empty(address):
        return

    targetAddr: address = empty(address)
    accessAbi: String[64] = empty(String[64])
    numInputs: uint256 = 0
    targetAddr, accessAbi, numInputs = staticcall UndyLego(_legoAddr).getAccessForLego(self, _action)

    # nothing to do here
    if targetAddr == empty(address):
        return

    method_abi: bytes4 = convert(slice(keccak256(accessAbi), 0, 4), bytes4)
    success: bool = False
    response: Bytes[32] = b""

    # assumes input is: lego addr (operator)
    if numInputs == 1:
        success, response = raw_call(
            targetAddr,
            concat(
                method_abi,
                convert(_legoAddr, bytes32),
            ),
            revert_on_failure = False,
            max_outsize = 32,
        )
    
    # assumes input (and order) is: user (self), lego addr (operator)
    elif numInputs == 2:
        success, response = raw_call(
            targetAddr,
            concat(
                method_abi,
                convert(self, bytes32),
                convert(_legoAddr, bytes32),
            ),
            revert_on_failure = False,
            max_outsize = 32,
        )

    # assumes input (and order) is: user (self), lego addr (operator), allowed bool
    elif numInputs == 3:
        success, response = raw_call(
            targetAddr,
            concat(
                method_abi,
                convert(self, bytes32),
                convert(_legoAddr, bytes32),
                convert(True, bytes32),
            ),
            revert_on_failure = False,
            max_outsize = 32,
        )

    assert success # dev: failed to set operator
