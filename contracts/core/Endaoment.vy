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
#     Ripe Foundation (C) 2026

# @version 0.4.3
# pragma optimize codesize

implements: Department

exports: addys.__interface__
exports: (
    deptBasics.canMintGreen,
    deptBasics.canMintRipe,
)

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
    def calc_token_amount(_amounts: DynArray[uint256, 2], _is_deposit: bool) -> uint256: view
    def get_virtual_price() -> uint256: view

interface EndaomentFunds:
    def transfer(_asset: address = empty(address), _amount: uint256 = max_value(uint256)) -> uint256: nonpayable
    def hasBalance(_asset: address = empty(address)) -> bool: view

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

interface RipeHq:
    def governance() -> address: view

interface EndaomentPSM:
    def USDC() -> address: view

struct StabilizerConfig:
    pool: address
    lpToken: address
    greenBalance: uint256
    greenRatio: uint256
    greenIndex: uint256
    stabilizerAdjustWeight: uint256
    stabilizerMaxPoolDebt: uint256
    altBalance: uint256

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
    lpBalance: uint256  # verified LP received by this action, not total custody

event PartnerLiquidityMinted:
    partner: indexed(address)
    asset: indexed(address)
    partnerAmount: uint256
    usdValue: uint256
    greenMinted: uint256

HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
MAX_SWAP_INSTRUCTIONS: constant(uint256) = 5
MAX_TOKEN_PATH: constant(uint256) = 5
MAX_ASSETS: constant(uint256) = 10
MAX_LEGOS: constant(uint256) = 10
API_VERSION: constant(String[28]) = "0.1.0"
FIFTY_PERCENT: constant(uint256) = 50_00 # 50.00%
EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
LEGO_BOOK_ID: constant(uint256) = 3
CURVE_PRICES_ID: constant(uint256) = 2
MAX_PROOFS: constant(uint256) = 25

WETH: public(immutable(address))
ETH: public(immutable(address))


@deploy
def __init__(_ripeHq: address, _weth: address, _eth: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, True, False) # can mint green only

    assert empty(address) not in [_weth, _eth] # dev: invalid addys
    WETH = _weth
    ETH = _eth


#######################
# Department Controls #
#######################


@nonreentrant
@external
def pause(_shouldPause: bool):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _shouldPause != deptBasics.isPaused # dev: no change
    deptBasics.isPaused = _shouldPause
    log deptBasics.DepartmentPauseModified(isPaused=_shouldPause)


@nonreentrant
@external
def recoverFunds(_recipient: address, _asset: address):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    deptBasics._recoverFunds(_recipient, _asset)


@nonreentrant
@external
def recoverFundsMany(_recipient: address, _assets: DynArray[address, 20]):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    for asset: address in _assets:
        deptBasics._recoverFunds(_recipient, asset)


@view
@external
def isPaused() -> bool:
    return deptBasics.isPaused


@payable
@external
def __default__():
    pass


##################
# Transfer Funds #
##################


@nonreentrant
@external
def transferFundsToGov(_asset: address, _amount: uint256 = max_value(uint256)) -> (uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms

    # finalize amount
    endaoFunds: address = addys._getEndaomentFundsAddr()
    amount: uint256 = self._prepareEndaomentFunds(_asset, _amount, endaoFunds)
    assert amount != 0 # dev: no amt

    # perform transfer
    govRecipient: address = staticcall RipeHq(addys._getRipeHq()).governance()
    assert govRecipient != empty(address) # dev: invalid gov recipient
    assert extcall IERC20(_asset).transfer(govRecipient, amount, default_return_value = True) # dev: xfer

    txUsdValue: uint256 = staticcall PriceDesk(addys._getPriceDeskAddr()).getUsdValue(_asset, amount, False)
    log WalletAction(
        op = 1,
        asset1 = _asset,
        asset2 = govRecipient,
        amount1 = amount,
        amount2 = 0,
        usdValue = txUsdValue,
        legoId = 0,
    )
    return amount, txUsdValue


@nonreentrant
@external
def transferFundsToVault(_assets: DynArray[address, MAX_ASSETS]):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms

    priceDesk: address = addys._getPriceDeskAddr()
    endaoFunds: address = addys._getEndaomentFundsAddr()
    assert endaoFunds != empty(address) # dev: no endaoment funds

    for a: address in _assets:
        asset: address = a
        amount: uint256 = 0

        if a == empty(address):
            amount = self.balance
        else:
            amount = staticcall IERC20(a).balanceOf(self)

        # skip if no balance
        if amount == 0:
            continue

        # transfer to vault
        if a == empty(address):
            send(endaoFunds, amount)
            asset = WETH
        else:
            assert extcall IERC20(a).transfer(endaoFunds, amount, default_return_value = True) # dev: xfer

        txUsdValue: uint256 = staticcall PriceDesk(priceDesk).getUsdValue(asset, amount, False)
        log WalletAction(
            op = 1,
            asset1 = asset,
            asset2 = endaoFunds,
            amount1 = amount,
            amount2 = 0,
            usdValue = txUsdValue,
            legoId = 0,
        )


@nonreentrant
@external
def transferFundsToEndaomentPSM(_amount: uint256 = max_value(uint256)) -> (uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused

    # allow switchboard or governance to call this function
    isSwitchboard: bool = addys._isSwitchboardAddr(msg.sender)
    isGovernance: bool = msg.sender == staticcall RipeHq(addys._getRipeHq()).governance()
    assert isSwitchboard or isGovernance # dev: no perms

    # get EndaomentPSM and USDC address
    endaoPSM: address = addys._getEndaomentPsmAddr()
    assert endaoPSM != empty(address) # dev: no endaoment psm
    usdc: address = staticcall EndaomentPSM(endaoPSM).USDC()
    assert usdc != empty(address) # dev: no usdc

    # finalize amount
    endaoFunds: address = addys._getEndaomentFundsAddr()
    amount: uint256 = self._prepareEndaomentFunds(usdc, _amount, endaoFunds)
    assert amount != 0 # dev: no amt

    # perform transfer
    assert extcall IERC20(usdc).transfer(endaoPSM, amount, default_return_value = True) # dev: xfer

    txUsdValue: uint256 = staticcall PriceDesk(addys._getPriceDeskAddr()).getUsdValue(usdc, amount, False)
    log WalletAction(
        op = 1,
        asset1 = usdc,
        asset2 = endaoPSM,
        amount1 = amount,
        amount2 = 0,
        usdValue = txUsdValue,
        legoId = 0,
    )
    return amount, txUsdValue


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
    endaoFunds: address = addys._getEndaomentFundsAddr()
    amount: uint256 = self._getAmountAndApprove(_asset, _amount, legoAddr, endaoFunds) # doing approval here

    # deposit for yield
    assetAmount: uint256 = 0
    vaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    txUsdValue: uint256 = 0
    assetAmount, vaultToken, vaultTokenAmountReceived, txUsdValue = extcall UndyLego(legoAddr).depositForYield(_asset, amount, _vaultAddr, _extraData, endaoFunds)
    self._resetApproval(_asset, legoAddr, endaoFunds)

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
    endaoFunds: address = addys._getEndaomentFundsAddr()

    amount: uint256 = _amount
    if _vaultToken != empty(address):
        amount = self._getAmountAndApprove(_vaultToken, _amount, empty(address), endaoFunds) # not approving here

        # some vault tokens require max value approval (comp v3)
        assert extcall IERC20(_vaultToken).approve(legoAddr, max_value(uint256), default_return_value = True) # dev: appr

    # withdraw from yield
    vaultTokenAmountBurned: uint256 = 0
    underlyingAsset: address = empty(address)
    underlyingAmount: uint256 = 0
    txUsdValue: uint256 = 0
    vaultTokenAmountBurned, underlyingAsset, underlyingAmount, txUsdValue = extcall UndyLego(legoAddr).withdrawFromYield(_vaultToken, amount, _extraData, endaoFunds)

    if _vaultToken != empty(address):
        self._resetApproval(_vaultToken, legoAddr, endaoFunds)

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


###################
# Swap / Exchange #
###################


@nonreentrant
@external
def swapTokens(_instructions: DynArray[UndyLego.SwapInstruction, MAX_SWAP_INSTRUCTIONS]) -> (address, uint256, address, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    endaoFunds: address = addys._getEndaomentFundsAddr()

    tokenIn: address = empty(address)
    tokenOut: address = empty(address)
    legoIds: DynArray[uint256, MAX_LEGOS] = []
    tokenIn, tokenOut, legoIds = self._validateAndGetSwapInfo(_instructions)

    origAmountIn: uint256 = self._getAmountAndApprove(tokenIn, _instructions[0].amountIn, empty(address), endaoFunds) # not approving here
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

    assert lastTokenOutAmount != 0 # dev: no output amount
    self._transferToEndaomentFunds(lastTokenOut, endaoFunds)

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
    self._resetApproval(tokenIn, legoAddr, empty(address))
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


####################
# Claim Incentives #
####################


@nonreentrant
@external
def claimIncentives(
    _user: address,
    _legoId: uint256,
    _rewardToken: address = empty(address),
    _rewardAmount: uint256 = max_value(uint256),
    _proofs: DynArray[bytes32, MAX_PROOFS] = [],
) -> (uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms

    legoAddr: address = self._getLegoAddr(_legoId)
    self._checkLegoAccessForAction(legoAddr, UndyLego.ActionType.REWARDS)

    # claim rewards
    rewardAmount: uint256 = 0
    txUsdValue: uint256 = 0
    rewardAmount, txUsdValue = extcall UndyLego(legoAddr).claimIncentives(_user, _rewardToken, _rewardAmount, _proofs)

    # transfer to endaoment funds
    self._transferToEndaomentFunds(_rewardToken, addys._getEndaomentFundsAddr())

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
@external
def convertEthToWeth(_amount: uint256 = max_value(uint256)) -> (uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms

    endaoFunds: address = addys._getEndaomentFundsAddr()
    self._prepareEndaomentFunds(empty(address), _amount, endaoFunds)

    # convert eth to weth
    weth: address = WETH
    amount: uint256 = min(_amount, self.balance)
    assert amount != 0 # dev: no amt
    extcall WethContract(weth).deposit(value = amount)
    self._transferToEndaomentFunds(weth, endaoFunds)

    txUsdValue: uint256 = staticcall PriceDesk(addys._getPriceDeskAddr()).getUsdValue(weth, amount, False)
    log WalletAction(
        op = 2,
        asset1 = ETH,
        asset2 = weth,
        amount1 = amount,
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
    endaoFunds: address = addys._getEndaomentFundsAddr()

    # convert weth to eth
    weth: address = WETH
    amount: uint256 = self._getAmountAndApprove(weth, _amount, empty(address), endaoFunds) # nothing to approve
    extcall WethContract(weth).withdraw(amount)
    send(endaoFunds, self.balance)

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
    lpToken, lpAmountReceived, addedTokenA, addedTokenB, txUsdValue = self._addLiquidity(_legoId, _pool, _tokenA, _tokenB, _amountA, _amountB, _minAmountA, _minAmountB, _minLpAmount, _extraData, addys._getEndaomentFundsAddr())
    return lpAmountReceived, addedTokenA, addedTokenB, txUsdValue


@internal
def _addLiquidity(
    _legoId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256,
    _amountB: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _minLpAmount: uint256,
    _extraData: bytes32,
    _lpRecipient: address,
) -> (address, uint256, uint256, uint256, uint256):
    legoAddr: address = self._getLegoAddr(_legoId)
    endaoFunds: address = addys._getEndaomentFundsAddr()

    # token approvals
    amountA: uint256 = 0
    if _amountA != 0:
        amountA = self._getAmountAndApprove(_tokenA, _amountA, legoAddr, endaoFunds)
    amountB: uint256 = 0
    if _amountB != 0:
        amountB = self._getAmountAndApprove(_tokenB, _amountB, legoAddr, endaoFunds)

    # add liquidity via lego partner
    lpToken: address = empty(address)
    lpAmountReceived: uint256 = 0
    addedTokenA: uint256 = 0
    addedTokenB: uint256 = 0
    txUsdValue: uint256 = 0
    lpToken, lpAmountReceived, addedTokenA, addedTokenB, txUsdValue = extcall UndyLego(legoAddr).addLiquidity(_pool, _tokenA, _tokenB, amountA, amountB, _minAmountA, _minAmountB, _minLpAmount, _extraData, _lpRecipient)

    # remove approvals
    if amountA != 0:
        self._resetApproval(_tokenA, legoAddr, endaoFunds)
    if amountB != 0:
        self._resetApproval(_tokenB, legoAddr, endaoFunds)

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
    _lpAmount: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _extraData: bytes32,
) -> (uint256, uint256, uint256, uint256):
    legoAddr: address = self._getLegoAddr(_legoId)
    endaoFunds: address = addys._getEndaomentFundsAddr()

    # remove liquidity via lego partner
    amountAReceived: uint256 = 0
    amountBReceived: uint256 = 0
    lpAmountBurned: uint256 = 0
    txUsdValue: uint256 = 0
    lpAmount: uint256 = self._getAmountAndApprove(_lpToken, _lpAmount, legoAddr, endaoFunds)
    amountAReceived, amountBReceived, lpAmountBurned, txUsdValue = extcall UndyLego(legoAddr).removeLiquidity(_pool, _tokenA, _tokenB, _lpToken, lpAmount, _minAmountA, _minAmountB, _extraData, endaoFunds)
    self._resetApproval(_lpToken, legoAddr, endaoFunds)

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


####################
# Green Stabilizer #
####################


@nonreentrant
@external
def stabilizeGreenRefPool() -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    a: addys.Addys = addys._getAddys()
    endaoFunds: address = addys._getEndaomentFundsAddr()

    data: StabilizerConfig = self._getGreenStabilizerConfig(a.priceDesk)
    if data.pool == empty(address) or (data.greenBalance == 0 and data.altBalance == 0):
        return False
    if data.greenBalance == data.altBalance:
        return False

    # pull LP and Green from vault
    self._prepareEndaomentFunds(data.lpToken, max_value(uint256), endaoFunds)
    self._prepareEndaomentFunds(a.greenToken, max_value(uint256), endaoFunds)

    # current position
    lpBalance: uint256 = staticcall IERC20(data.lpToken).balanceOf(self)
    leftoverGreen: uint256 = staticcall IERC20(a.greenToken).balanceOf(self)
    poolDebt: uint256 = staticcall Ledger(a.ledger).greenPoolDebt(data.pool)
    initialIsDeficit: bool = False
    initialPosition: uint256 = 0
    initialIsDeficit, initialPosition = self._calcNetPositionForStabilizer(data.pool, lpBalance, leftoverGreen, poolDebt)

    # add/remove Green until the normalized pool balances converge
    didAdjust: bool = False
    if data.altBalance > data.greenBalance:
        didAdjust = self._addStabilizerGreenLiquidity(poolDebt, leftoverGreen, data, a.greenToken, a.ledger)
    elif data.greenBalance > data.altBalance:
        didAdjust = self._removeStabilizerGreenLiquidity(lpBalance, poolDebt, data, a.greenToken, a.ledger)

    # calc new position
    lpBalance = staticcall IERC20(data.lpToken).balanceOf(self)
    leftoverGreen = staticcall IERC20(a.greenToken).balanceOf(self)
    poolDebt = staticcall Ledger(a.ledger).greenPoolDebt(data.pool)
    newIsDeficit: bool = False
    newPosition: uint256 = 0
    newIsDeficit, newPosition = self._calcNetPositionForStabilizer(data.pool, lpBalance, leftoverGreen, poolDebt)

    isPositionNotWorse: bool = False
    if initialIsDeficit:
        isPositionNotWorse = not newIsDeficit or newPosition <= initialPosition
    elif not newIsDeficit:
        isPositionNotWorse = newPosition >= initialPosition
    assert isPositionNotWorse # dev: stabilizer was not profitable

    # transfer LP and Green back to vault
    self._transferToEndaomentFunds(data.lpToken, endaoFunds)
    self._transferToEndaomentFunds(a.greenToken, endaoFunds)

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
    # only add Green when the normalized alternate-asset balance is larger
    if _data.altBalance <= _data.greenBalance:
        return 0
    if _data.greenIndex >= 2:
        return 0
    
    greenAdjustFull: uint256 = _data.altBalance - _data.greenBalance
    greenAdjustWeighted: uint256 = greenAdjustFull * _data.stabilizerAdjustWeight // HUNDRED_PERCENT

    debtAvail: uint256 = 0 
    if _data.stabilizerMaxPoolDebt > _poolDebt:
        debtAvail = _data.stabilizerMaxPoolDebt - _poolDebt

    return min(greenAdjustWeighted, debtAvail + _leftoverGreen)


@view
@external
def getGreenAmountToAddInStabilizer() -> uint256:
    data: StabilizerConfig = self._getGreenStabilizerConfig(addys._getPriceDeskAddr())
    if data.pool == empty(address) or (data.greenBalance == 0 and data.altBalance == 0):
        return 0
    poolDebt: uint256 = staticcall Ledger(addys._getLedgerAddr()).greenPoolDebt(data.pool)
    leftoverGreen: uint256 = staticcall IERC20(addys._getGreenToken()).balanceOf(addys._getEndaomentFundsAddr())
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
    lpQuote: uint256 = self._quoteGreenRemoval(_data.pool, _data.greenIndex, greenAmount)
    if lpQuote >= _lpBalance:
        assert extcall IERC20(_data.lpToken).approve(_data.pool, 0, default_return_value=True) # dev: approval failed
        return False
    amounts: DynArray[uint256, 2] = [0, 0]
    amounts[_data.greenIndex] = greenAmount
    lpBurned: uint256 = extcall CurvePool(_data.pool).remove_liquidity_imbalance(amounts, lpQuote + 1, self)
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
    # only remove Green when its normalized balance is larger
    if _data.greenBalance <= _data.altBalance:
        return 0
    if _lpBalance == 0 or _data.greenIndex >= 2 or not _data.pool.is_contract:
        return 0
    
    greenAdjustFull: uint256 = _data.greenBalance - _data.altBalance
    greenAdjustWeighted: uint256 = greenAdjustFull * _data.stabilizerAdjustWeight // HUNDRED_PERCENT
    lpTotalSupply: uint256 = staticcall IERC20(_data.lpToken).totalSupply()
    if lpTotalSupply == 0:
        return 0

    maxGreenToRemove: uint256 = max(_poolDebt, _data.greenBalance * _lpBalance // lpTotalSupply)
    requestedGreen: uint256 = min(greenAdjustWeighted, maxGreenToRemove)
    if requestedGreen == 0:
        return 0

    lpQuote: uint256 = self._quoteGreenRemoval(_data.pool, _data.greenIndex, requestedGreen)
    if lpQuote < _lpBalance:
        return requestedGreen

    # StableSwap-NG burns calc_token_amount(amounts, False) + 1 LP token for
    # remove_liquidity_imbalance. Find the largest executable Green amount.
    low: uint256 = 0
    high: uint256 = requestedGreen
    for _i: uint256 in range(256):
        if low >= high:
            break
        midpoint: uint256 = high - (high - low) // 2
        if self._quoteGreenRemoval(_data.pool, _data.greenIndex, midpoint) < _lpBalance:
            low = midpoint
        else:
            high = midpoint - 1

    return low


@view
@internal
def _quoteGreenRemoval(_pool: address, _greenIndex: uint256, _greenAmount: uint256) -> uint256:
    amounts: DynArray[uint256, 2] = [0, 0]
    amounts[_greenIndex] = _greenAmount
    return staticcall CurvePool(_pool).calc_token_amount(amounts, False)


@view
@external
def getGreenAmountToRemoveInStabilizer() -> uint256:
    data: StabilizerConfig = self._getGreenStabilizerConfig(addys._getPriceDeskAddr())
    if data.pool == empty(address) or data.greenBalance == 0:
        return 0
    lpBalance: uint256 = staticcall IERC20(data.lpToken).balanceOf(addys._getEndaomentFundsAddr())
    poolDebt: uint256 = staticcall Ledger(addys._getLedgerAddr()).greenPoolDebt(data.pool)
    return self._getGreenAmountToRemove(lpBalance, poolDebt, data)


# utilities


@view
@internal
def _getGreenStabilizerConfig(_priceDesk: address) -> StabilizerConfig:
    curvePrices: address = staticcall PriceDesk(_priceDesk).getAddr(CURVE_PRICES_ID)
    if curvePrices == empty(address):
        return empty(StabilizerConfig)
    return staticcall CurvePrices(curvePrices).getGreenStabilizerConfig()


@view
@external
def calcProfitForStabilizer() -> uint256:
    a: addys.Addys = addys._getAddys()
    endaoFunds: address = addys._getEndaomentFundsAddr()
    data: StabilizerConfig = self._getGreenStabilizerConfig(a.priceDesk)
    if data.pool == empty(address):
        return 0
    lpBalance: uint256 = staticcall IERC20(data.lpToken).balanceOf(endaoFunds)
    leftoverGreen: uint256 = staticcall IERC20(a.greenToken).balanceOf(endaoFunds)
    poolDebt: uint256 = staticcall Ledger(a.ledger).greenPoolDebt(data.pool)
    return self._calcProfitForStabilizer(data.pool, lpBalance, leftoverGreen, poolDebt)


@view
@internal
def _calcNetPositionForStabilizer(
    _pool: address,
    _lpBalance: uint256,
    _greenBalance: uint256,
    _poolDebt: uint256,
) -> (bool, uint256):
    virtualPrice: uint256 = staticcall CurvePool(_pool).get_virtual_price()

    if _poolDebt > _greenBalance:
        lpDebt: uint256 = (_poolDebt - _greenBalance) * EIGHTEEN_DECIMALS // virtualPrice
        if lpDebt > _lpBalance:
            return True, lpDebt - _lpBalance
        return False, _lpBalance - lpDebt

    netGreenBalInLp: uint256 = (_greenBalance - _poolDebt) * EIGHTEEN_DECIMALS // virtualPrice
    return False, _lpBalance + netGreenBalInLp


@view
@internal
def _calcProfitForStabilizer(
    _pool: address,
    _lpBalance: uint256,
    _greenBalance: uint256,
    _poolDebt: uint256,
) -> uint256:
    isDeficit: bool = False
    position: uint256 = 0
    isDeficit, position = self._calcNetPositionForStabilizer(_pool, _lpBalance, _greenBalance, _poolDebt)

    if isDeficit or _lpBalance == 0:
        return 0

    return position


#####################
# Partner Liquidity #
#####################


@nonreentrant
@external
def mintPartnerLiquidity(_partner: address, _asset: address, _amount: uint256 = max_value(uint256)) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    a: addys.Addys = addys._getAddys()
    partnerAmount: uint256 = 0
    usdValue: uint256 = 0
    greenMinted: uint256 = 0
    partnerAmount, usdValue, greenMinted = self._mintPartnerLiquidity(_partner, _asset, _amount, a.priceDesk, a.greenToken, addys._getEndaomentFundsAddr())
    log PartnerLiquidityMinted(partner=_partner, asset=_asset, partnerAmount=partnerAmount, usdValue=usdValue, greenMinted=greenMinted)
    return greenMinted


@nonreentrant
@external
def addPartnerLiquidity(
    _legoId: uint256,
    _pool: address,
    _partner: address,
    _asset: address,
    _amount: uint256,
    _minLpAmount: uint256,
    _expectedLpToken: address,
) -> (uint256, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _expectedLpToken != empty(address) # dev: invalid lp token
    a: addys.Addys = addys._getAddys()
    endaoFunds: address = addys._getEndaomentFundsAddr()

    # mint green
    partnerAmount: uint256 = 0
    greenAmount: uint256 = 0
    greenMinted: uint256 = 0
    partnerAmount, greenAmount, greenMinted = self._mintPartnerLiquidity(_partner, _asset, _amount, a.priceDesk, a.greenToken, endaoFunds)
    partnerCustodyBefore: uint256 = self._getCombinedBalance(_asset, endaoFunds)
    greenCustodyBefore: uint256 = self._getCombinedBalance(a.greenToken, endaoFunds)

    # add liquidity (LP goes here so only the current action's delta is split)
    lpBefore: uint256 = staticcall IERC20(_expectedLpToken).balanceOf(self)
    lpToken: address = empty(address)
    lpAmountReceived: uint256 = 0
    liqAmountA: uint256 = 0
    liqAmountB: uint256 = 0
    usdValue: uint256 = 0
    lpToken, lpAmountReceived, liqAmountA, liqAmountB, usdValue = self._addLiquidity(_legoId, _pool, _asset, a.greenToken, partnerAmount, greenAmount, 0, 0, _minLpAmount, empty(bytes32), self)
    assert lpToken == _expectedLpToken # dev: unexpected lp token
    assert lpAmountReceived != 0 # dev: no liquidity added
    lpAfter: uint256 = staticcall IERC20(_expectedLpToken).balanceOf(self)
    assert lpAfter - lpBefore == lpAmountReceived # dev: lp amount mismatch

    # Qualified Legos report net venue contributions. Match those reports to the protocol's custody decrease
    # so downstream fees or inventory top-ups cannot be attributed to this partner action. Partial fills remain valid.
    partnerCustodyAfter: uint256 = self._getCombinedBalance(_asset, endaoFunds)
    greenCustodyAfter: uint256 = self._getCombinedBalance(a.greenToken, endaoFunds)
    assert partnerCustodyBefore - liqAmountA == partnerCustodyAfter # dev: partner asset accounting
    assert greenCustodyBefore - liqAmountB == greenCustodyAfter # dev: green accounting
    assert liqAmountA <= partnerAmount # dev: partner asset accounting
    assert liqAmountB <= greenAmount # dev: green accounting

    # Attribute pre-existing GREEN reserve first, then burn any provisional
    # mint that a partial fill did not actually contribute to the venue.
    greenReserve: uint256 = greenAmount - greenMinted
    finalGreenMinted: uint256 = 0
    if liqAmountB > greenReserve:
        finalGreenMinted = liqAmountB - greenReserve
    excessGreenMinted: uint256 = greenMinted - finalGreenMinted
    if excessGreenMinted != 0:
        greenBeforeBurn: uint256 = staticcall IERC20(a.greenToken).balanceOf(self)
        self._prepareEndaomentFunds(a.greenToken, excessGreenMinted, endaoFunds)
        greenAfterPull: uint256 = staticcall IERC20(a.greenToken).balanceOf(self)
        assert greenAfterPull > greenBeforeBurn # dev: green refund accounting
        assert greenAfterPull - greenBeforeBurn == excessGreenMinted # dev: green refund accounting
        assert extcall GreenToken(a.greenToken).burn(excessGreenMinted) # dev: could not burn green
    partnerAmount = liqAmountA
    greenAmount = liqAmountB
    greenMinted = finalGreenMinted

    # transfer partner's half
    partnerShare: uint256 = 0
    if _partner != self:
        partnerShare = lpAmountReceived // 2
    if partnerShare != 0:
        assert extcall IERC20(lpToken).transfer(_partner, partnerShare, default_return_value=True) # dev: could not transfer

    # transfer vault's half back to vault
    vaultShare: uint256 = lpAmountReceived - partnerShare
    if vaultShare != 0:
        assert extcall IERC20(lpToken).transfer(endaoFunds, vaultShare, default_return_value=True) # dev: could not transfer

    # add pool debt
    if greenMinted != 0:
        extcall Ledger(a.ledger).updateGreenPoolDebt(_pool, greenMinted, True)

    log PartnerLiquidityAdded(partner=_partner, asset=_asset, partnerAmount=partnerAmount, greenAmount=greenAmount, lpBalance=lpAmountReceived)
    return lpAmountReceived, liqAmountA, liqAmountB


# utils


@view
@internal
def _getCombinedBalance(_asset: address, _endaoFunds: address) -> uint256:
    return staticcall IERC20(_asset).balanceOf(self) + staticcall IERC20(_asset).balanceOf(_endaoFunds)


@internal
def _mintPartnerLiquidity(
    _partner: address,
    _asset: address,
    _amount: uint256,
    _priceDesk: address,
    _greenToken: address,
    _endaoFunds: address,
) -> (uint256, uint256, uint256):
    assert _asset != _greenToken # dev: invalid partner asset
    partnerAmount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(_partner))
    assert partnerAmount != 0 # dev: no asset to add

    if _partner != self:
        balanceBefore: uint256 = staticcall IERC20(_asset).balanceOf(_endaoFunds)
        assert extcall IERC20(_asset).transferFrom(_partner, _endaoFunds, partnerAmount, default_return_value=True) # dev: transfer failed
        balanceAfter: uint256 = staticcall IERC20(_asset).balanceOf(_endaoFunds)
        assert balanceAfter > balanceBefore # dev: no asset received
        partnerAmount = balanceAfter - balanceBefore

    usdValue: uint256 = staticcall PriceDesk(_priceDesk).getUsdValue(_asset, partnerAmount, True)
    assert usdValue != 0 # dev: invalid asset

    greenAvail: uint256 = staticcall IERC20(_greenToken).balanceOf(_endaoFunds)
    newMinted: uint256 = 0
    if usdValue > greenAvail:
        newMinted = usdValue - greenAvail
        extcall GreenToken(_greenToken).mint(_endaoFunds, newMinted)

    return partnerAmount, usdValue, newMinted


#############
# Pool Debt #
#############


@nonreentrant
@external
def repayPoolDebt(_pool: address, _amount: uint256 = max_value(uint256)) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    a: addys.Addys = addys._getAddys()
    endaoFunds: address = addys._getEndaomentFundsAddr()

    # pull Green from vault if needed
    self._prepareEndaomentFunds(a.greenToken, _amount, endaoFunds)

    greenAvail: uint256 = min(_amount, staticcall IERC20(a.greenToken).balanceOf(self))
    repayAmount: uint256 = min(greenAvail, staticcall Ledger(a.ledger).greenPoolDebt(_pool))
    assert repayAmount != 0 # dev: no debt to repay

    self._repayPoolDebt(_pool, repayAmount, a.greenToken, a.ledger)

    # transfer leftover Green back to vault
    leftoverGreen: uint256 = staticcall IERC20(a.greenToken).balanceOf(self)
    if leftoverGreen != 0:
        assert extcall IERC20(a.greenToken).transfer(endaoFunds, leftoverGreen, default_return_value = True)

    log PoolDebtRepaid(pool=_pool, amount=repayAmount)
    return True


#############
# Utilities #
#############


# pull funds from endaoment funds


@internal
def _prepareEndaomentFunds(_asset: address, _amount: uint256, _endaoFunds: address) -> uint256:
    if not staticcall EndaomentFunds(_endaoFunds).hasBalance(_asset):
        return 0
    return extcall EndaomentFunds(_endaoFunds).transfer(_asset, _amount)


# transfer funds to endaoment funds


@internal
def _transferToEndaomentFunds(_asset: address, _endaoFunds: address):
    if _endaoFunds != empty(address) and _asset != empty(address):
        currentBalance: uint256 = staticcall IERC20(_asset).balanceOf(self)
        if currentBalance != 0:
            assert extcall IERC20(_asset).transfer(_endaoFunds, currentBalance, default_return_value = True) # dev: transfer failed


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
def _getAmountAndApprove(_token: address, _amount: uint256, _legoAddr: address, _endaoFunds: address) -> uint256:
    self._prepareEndaomentFunds(_token, _amount, _endaoFunds)
    currentBalance: uint256 = staticcall IERC20(_token).balanceOf(self)
    amount: uint256 = min(_amount, currentBalance)
    assert amount != 0 # dev: no balance for _token

    if _legoAddr != empty(address):
        assert extcall IERC20(_token).approve(_legoAddr, amount, default_return_value = True) # dev: appr

    return amount


# reset approval


@internal
def _resetApproval(_token: address, _legoAddr: address, _endaoFunds: address):
    if _legoAddr != empty(address):
        assert extcall IERC20(_token).approve(_legoAddr, 0, default_return_value = True) # dev: appr
    
    self._transferToEndaomentFunds(_token, _endaoFunds)


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
