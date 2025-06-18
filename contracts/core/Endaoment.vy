# @version 0.4.1

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department

from ethereum.ercs import IERC20
from ethereum.ercs import IERC721

interface UnderscoreLego:
    def addLiquidity(_nftTokenId: uint256, _pool: address, _tokenA: address, _tokenB: address, _tickLower: int24, _tickUpper: int24, _amountA: uint256, _amountB: uint256, _minAmountA: uint256, _minAmountB: uint256, _minLpAmount: uint256, _recipient: address, _oracleRegistry: address = empty(address)) -> (uint256, uint256, uint256, uint256, uint256, uint256, uint256): nonpayable
    def removeLiquidity(_nftTokenId: uint256, _pool: address, _tokenA: address, _tokenB: address, _lpToken: address, _liqToRemove: uint256, _minAmountA: uint256, _minAmountB: uint256, _recipient: address, _oracleRegistry: address = empty(address)) -> (uint256, uint256, uint256, uint256, uint256, bool): nonpayable
    def swapTokens(_amountIn: uint256, _minAmountOut: uint256, _tokenPath: DynArray[address, 5], _poolPath: DynArray[address, 4], _recipient: address, _oracleRegistry: address = empty(address)) -> (uint256, uint256, uint256, uint256): nonpayable
    def depositTokens(_asset: address, _amount: uint256, _vault: address, _recipient: address, _oracleRegistry: address = empty(address)) -> (uint256, address, uint256, uint256, uint256): nonpayable
    def withdrawTokens(_asset: address, _amount: uint256, _vaultToken: address, _recipient: address, _oracleRegistry: address = empty(address)) -> (uint256, uint256, uint256, uint256): nonpayable
    def claimRewards(_user: address, _market: address, _rewardToken: address, _rewardAmount: uint256, _proof: bytes32): nonpayable
    def getAccessForLego(_user: address) -> (address, String[64], uint256): view
    def getLpToken(_pool: address) -> address: view

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

interface LegoRegistry:
    def getLegoAddr(_legoId: uint256) -> address: view

interface UnderscoreRegistry:
    def getAddy(_id: uint256) -> address: view

interface MissionControl:
    def underscoreRegistry() -> address: view

struct SwapInstruction:
    legoId: uint256
    amountIn: uint256
    minAmountOut: uint256
    tokenPath: DynArray[address, MAX_TOKEN_PATH]
    poolPath: DynArray[address, MAX_TOKEN_PATH - 1]

struct StabilizerConfig:
    pool: address
    lpToken: address
    greenBalance: uint256
    greenRatio: uint256
    greenIndex: uint256
    stabilizerAdjustWeight: uint256
    stabilizerMaxPoolDebt: uint256

event EndaomentDeposit:
    asset: indexed(address)
    vaultToken: indexed(address)
    assetAmountDeposited: uint256
    vaultTokenAmountReceived: uint256
    refundAssetAmount: uint256
    usdValue: uint256
    legoId: uint256
    legoAddr: address

event EndaomentWithdrawal:
    asset: indexed(address)
    vaultToken: indexed(address)
    hasVaultToken: bool
    assetAmountReceived: uint256
    vaultTokenAmountBurned: uint256
    refundVaultTokenAmount: uint256
    usdValue: uint256
    legoId: uint256
    legoAddr: address

event EndaomentSwap:
    tokenIn: indexed(address)
    tokenOut: indexed(address)
    swapAmount: uint256
    toAmount: uint256
    refundAssetAmount: uint256
    usdValue: uint256
    numTokens: uint256
    legoId: uint256
    legoAddr: address

event EndaomentLiquidityAdded:
    tokenA: indexed(address)
    tokenB: indexed(address)
    liqAmountA: uint256
    liqAmountB: uint256
    liquidityAdded: uint256
    pool: address
    usdValue: uint256
    refundAssetAmountA: uint256
    refundAssetAmountB: uint256
    nftTokenId: uint256
    legoId: uint256
    legoAddr: address

event EndaomentLiquidityRemoved:
    tokenA: indexed(address)
    tokenB: address
    removedAmountA: uint256
    removedAmountB: uint256
    usdValue: uint256
    isDepleted: bool
    liquidityRemoved: uint256
    lpToken: indexed(address)
    refundedLpAmount: uint256
    legoId: uint256
    legoAddr: address

event EndaomentEthConvertedToWeth:
    amount: uint256
    paidEth: uint256
    weth: indexed(address)

event EndaomentWethConvertedToEth:
    amount: uint256
    weth: indexed(address)

event EndaomentRewardsClaimed:
    market: indexed(address)
    rewardToken: indexed(address)
    rewardAmount: uint256
    proof: bytes32
    legoId: uint256
    legoAddr: address

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

ERC721_RECEIVE_DATA: constant(Bytes[1024]) = b"UnderscoreErc721"
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
FIFTY_PERCENT: constant(uint256) = 50_00 # 50.00%
EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
MAX_SWAP_INSTRUCTIONS: constant(uint256) = 5
MAX_LEGOS: constant(uint256) = 20
MAX_TOKEN_PATH: constant(uint256) = 5
LEGO_REGISTRY_ID: constant(uint256) = 2
CURVE_PRICES_ID: constant(uint256) = 2

WETH: public(immutable(address))


@deploy
def __init__(_ripeHq: address, _weth: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, True, False) # can mint green only
    WETH = _weth


@payable
@external
def __default__():
    pass


@view
@external
def onERC721Received(_operator: address, _owner: address, _tokenId: uint256, _data: Bytes[1024]) -> bytes4:
    # must implement method for safe NFT transfers
    return method_id("onERC721Received(address,address,uint256,bytes)", output_type=bytes4)


###########
# Deposit #
###########


@nonreentrant
@external
def depositTokens(
    _legoId: uint256,
    _asset: address,
    _vault: address,
    _amount: uint256 = max_value(uint256),
) -> (uint256, address, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    return self._depositTokens(_legoId, _asset, _vault, _amount)


@internal
def _depositTokens(
    _legoId: uint256,
    _asset: address,
    _vault: address,
    _amount: uint256,
) -> (uint256, address, uint256, uint256):
    legoAddr: address = self._getLegoAddr(_legoId)
    amount: uint256 = self._getAmount(_asset, _amount)
    assert extcall IERC20(_asset).approve(legoAddr, amount, default_return_value=True) # dev: approval failed

    # deposit into lego partner
    assetAmountDeposited: uint256 = 0
    vaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    refundAssetAmount: uint256 = 0
    usdValue: uint256 = 0
    assetAmountDeposited, vaultToken, vaultTokenAmountReceived, refundAssetAmount, usdValue = extcall UnderscoreLego(legoAddr).depositTokens(_asset, amount, _vault, self)
    assert extcall IERC20(_asset).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    log EndaomentDeposit(asset=_asset, vaultToken=vaultToken, assetAmountDeposited=assetAmountDeposited, vaultTokenAmountReceived=vaultTokenAmountReceived, refundAssetAmount=refundAssetAmount, usdValue=usdValue, legoId=_legoId, legoAddr=legoAddr)
    return assetAmountDeposited, vaultToken, vaultTokenAmountReceived, usdValue


############
# Withdraw #
############


@nonreentrant
@external
def withdrawTokens(
    _legoId: uint256,
    _asset: address,
    _vaultAddr: address,
    _withdrawAmount: uint256 = max_value(uint256),
    _hasVaultToken: bool = True,
) -> (uint256, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    return self._withdrawTokens(_legoId, _asset, _vaultAddr, _withdrawAmount, _hasVaultToken)


@internal
def _withdrawTokens(
    _legoId: uint256,
    _asset: address,
    _vaultAddr: address,
    _withdrawAmount: uint256,
    _hasVaultToken: bool,
) -> (uint256, uint256, uint256):
    legoAddr: address = self._getLegoAddr(_legoId)

    # finalize amount, this will look at vault token balance (not always 1:1 with underlying asset)
    withdrawAmount: uint256 = _withdrawAmount
    if _hasVaultToken and _vaultAddr != empty(address):
        withdrawAmount = self._getAmount(_vaultAddr, _withdrawAmount)
        # some vault tokens require max value approval (comp v3)
        assert extcall IERC20(_vaultAddr).approve(legoAddr, max_value(uint256), default_return_value=True) # dev: approval failed
    assert withdrawAmount != 0 # dev: nothing to withdraw

    # withdraw from lego partner
    assetAmountReceived: uint256 = 0
    vaultTokenAmountBurned: uint256 = 0
    refundVaultTokenAmount: uint256 = 0
    usdValue: uint256 = 0
    assetAmountReceived, vaultTokenAmountBurned, refundVaultTokenAmount, usdValue = extcall UnderscoreLego(legoAddr).withdrawTokens(_asset, withdrawAmount, _vaultAddr, self)

    # zero out approvals
    if _hasVaultToken and _vaultAddr != empty(address):
        assert extcall IERC20(_vaultAddr).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    log EndaomentWithdrawal(asset=_asset, vaultToken=_vaultAddr, hasVaultToken=_hasVaultToken, assetAmountReceived=assetAmountReceived, vaultTokenAmountBurned=vaultTokenAmountBurned, refundVaultTokenAmount=refundVaultTokenAmount, usdValue=usdValue, legoId=_legoId, legoAddr=legoAddr)
    return assetAmountReceived, vaultTokenAmountBurned, usdValue


#############
# Rebalance #
#############


@nonreentrant
@external
def rebalance(
    _fromLegoId: uint256,
    _fromAsset: address,
    _fromVaultAddr: address,
    _toLegoId: uint256,
    _toVaultAddr: address,
    _fromVaultAmount: uint256 = max_value(uint256),
    _hasFromVaultToken: bool = True,
) -> (uint256, address, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms

    # withdraw from the first lego
    assetAmountReceived: uint256 = 0
    na: uint256 = 0
    withdrawUsdValue: uint256 = 0
    assetAmountReceived, na, withdrawUsdValue = self._withdrawTokens(_fromLegoId, _fromAsset, _fromVaultAddr, _fromVaultAmount, _hasFromVaultToken)

    # deposit the received assets into the second lego
    assetAmountDeposited: uint256 = 0
    newVaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    depositUsdValue: uint256 = 0
    assetAmountDeposited, newVaultToken, vaultTokenAmountReceived, depositUsdValue = self._depositTokens(_toLegoId, _fromAsset, _toVaultAddr, assetAmountReceived)

    usdValue: uint256 = max(withdrawUsdValue, depositUsdValue)
    return assetAmountDeposited, newVaultToken, vaultTokenAmountReceived, usdValue


########
# Swap #
########


@nonreentrant
@external
def swapTokens(_swapInstructions: DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS]) -> (uint256, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms

    underscoreRegistry: address = staticcall MissionControl(addys._getMissionControlAddr()).underscoreRegistry()
    legoRegistry: address = staticcall UnderscoreRegistry(underscoreRegistry).getAddy(LEGO_REGISTRY_ID)
    numSwapInstructions: uint256 = len(_swapInstructions)
    assert numSwapInstructions != 0 # dev: no swaps

    # get high level swap info
    tokenIn: address = empty(address)
    initialAmountIn: uint256 = 0
    tokenIn, initialAmountIn = self._getHighLevelSwapInfo(numSwapInstructions, _swapInstructions)

    # perform swap instructions
    amountIn: uint256 = initialAmountIn
    lastTokenOut: address = empty(address)
    lastTokenOutAmount: uint256 = 0
    lastUsdValue: uint256 = 0
    for j: uint256 in range(numSwapInstructions, bound=MAX_SWAP_INSTRUCTIONS):
        i: SwapInstruction = _swapInstructions[j]

        # from lego to lego, must follow the same token path
        if lastTokenOut != empty(address):
            newTokenIn: address = i.tokenPath[0]
            assert lastTokenOut == newTokenIn # dev: invalid token path
            amountIn = min(lastTokenOutAmount, staticcall IERC20(newTokenIn).balanceOf(self))

        lastTokenOut, lastTokenOutAmount, lastUsdValue = self._performSwapInstruction(i.legoId, amountIn, i.minAmountOut, i.tokenPath, i.poolPath, legoRegistry)

    return initialAmountIn, lastTokenOutAmount, lastUsdValue


@internal
def _performSwapInstruction(
    _legoId: uint256,
    _amountIn: uint256,
    _minAmountOut: uint256,
    _tokenPath: DynArray[address, MAX_TOKEN_PATH],
    _poolPath: DynArray[address, MAX_TOKEN_PATH - 1],
    _legoRegistry: address,
) -> (address, uint256, uint256):
    legoAddr: address = staticcall LegoRegistry(_legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego

    # get token in and token out
    tokenIn: address = _tokenPath[0]
    tokenOut: address = _tokenPath[len(_tokenPath) - 1]

    # approve token in
    assert extcall IERC20(tokenIn).approve(legoAddr, _amountIn, default_return_value=True) # dev: approval failed

    # swap assets via lego partner
    tokenInAmount: uint256 = 0
    tokenOutAmount: uint256 = 0
    refundTokenInAmount: uint256 = 0
    usdValue: uint256 = 0
    tokenInAmount, tokenOutAmount, refundTokenInAmount, usdValue = extcall UnderscoreLego(legoAddr).swapTokens(_amountIn, _minAmountOut, _tokenPath, _poolPath, self)

    # reset approvals
    assert extcall IERC20(tokenIn).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    log EndaomentSwap(tokenIn=tokenIn, tokenOut=tokenOut, swapAmount=tokenInAmount, toAmount=tokenOutAmount, refundAssetAmount=refundTokenInAmount, usdValue=usdValue, numTokens=len(_tokenPath), legoId=_legoId, legoAddr=legoAddr)
    return tokenOut, tokenOutAmount, usdValue


@view
@internal
def _getHighLevelSwapInfo(_numSwapInstructions: uint256, _swapInstructions: DynArray[SwapInstruction, MAX_SWAP_INSTRUCTIONS]) -> (address, uint256):   
    firstRoutePath: DynArray[address, MAX_TOKEN_PATH] = _swapInstructions[0].tokenPath
    firstRouteNumTokens: uint256 = len(firstRoutePath)
    assert firstRouteNumTokens >= 2 # dev: invalid token path

    # finalize token in and token out
    tokenIn: address = firstRoutePath[0]
    tokenOut: address = empty(address)
    if _numSwapInstructions == 1:
        tokenOut = firstRoutePath[firstRouteNumTokens - 1]
    else:
        lastRoutePath: DynArray[address, MAX_TOKEN_PATH] = _swapInstructions[_numSwapInstructions - 1].tokenPath
        lastRouteNumTokens: uint256 = len(lastRoutePath)
        assert lastRouteNumTokens >= 2 # dev: invalid token path
        tokenOut = lastRoutePath[lastRouteNumTokens - 1]

    assert empty(address) not in [tokenIn, tokenOut] # dev: invalid token path

    # finalize amount in
    amountIn: uint256 = self._getAmount(tokenIn, _swapInstructions[0].amountIn)
    return tokenIn, amountIn


#################
# Add Liquidity #
#################


@nonreentrant
@external
def addLiquidity(
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
    _minLpAmount: uint256 = 0,
) -> (uint256, uint256, uint256, uint256, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    legoAddr: address = self._getLegoAddr(_legoId)
    return self._addLiquidity(_legoId, legoAddr, _nftAddr, _nftTokenId, _pool, _tokenA, _tokenB, _amountA, _amountB, _tickLower, _tickUpper, _minAmountA, _minAmountB, _minLpAmount)


@internal
def _addLiquidity(
    _legoId: uint256,
    _legoAddr: address,
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
    _minLpAmount: uint256 = 0,
) -> (uint256, uint256, uint256, uint256, uint256):

    # token a
    amountA: uint256 = 0
    if _amountA != 0:
        amountA = self._getAmount(_tokenA, _amountA)
        assert extcall IERC20(_tokenA).approve(_legoAddr, amountA, default_return_value=True) # dev: approval failed

    # token b
    amountB: uint256 = 0
    if _amountB != 0:
        amountB = self._getAmount(_tokenB, _amountB)
        assert extcall IERC20(_tokenB).approve(_legoAddr, amountB, default_return_value=True) # dev: approval failed

    # transfer nft to lego (if applicable)
    hasNftLiqPosition: bool = _nftAddr != empty(address) and _nftTokenId != 0
    if hasNftLiqPosition:
        extcall IERC721(_nftAddr).safeTransferFrom(self, _legoAddr, _nftTokenId, ERC721_RECEIVE_DATA)

    # add liquidity via lego partner
    liquidityAdded: uint256 = 0
    liqAmountA: uint256 = 0
    liqAmountB: uint256 = 0
    usdValue: uint256 = 0
    refundAssetAmountA: uint256 = 0
    refundAssetAmountB: uint256 = 0
    nftTokenId: uint256 = 0
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountA, refundAssetAmountB, nftTokenId = extcall UnderscoreLego(_legoAddr).addLiquidity(_nftTokenId, _pool, _tokenA, _tokenB, _tickLower, _tickUpper, amountA, amountB, _minAmountA, _minAmountB, _minLpAmount, self)

    # validate the nft came back
    if hasNftLiqPosition:
        assert staticcall IERC721(_nftAddr).ownerOf(_nftTokenId) == self # dev: nft not returned

    # token a
    if amountA != 0:
        assert extcall IERC20(_tokenA).approve(_legoAddr, 0, default_return_value=True) # dev: approval failed

    # token b
    if amountB != 0:
        assert extcall IERC20(_tokenB).approve(_legoAddr, 0, default_return_value=True) # dev: approval failed

    log EndaomentLiquidityAdded(tokenA=_tokenA, tokenB=_tokenB, liqAmountA=liqAmountA, liqAmountB=liqAmountB, liquidityAdded=liquidityAdded, pool=_pool, usdValue=usdValue, refundAssetAmountA=refundAssetAmountA, refundAssetAmountB=refundAssetAmountB, nftTokenId=nftTokenId, legoId=_legoId, legoAddr=_legoAddr)
    return liquidityAdded, liqAmountA, liqAmountB, usdValue, nftTokenId


####################
# Remove Liquidity #
####################


@nonreentrant
@external
def removeLiquidity(
    _legoId: uint256,
    _nftAddr: address,
    _nftTokenId: uint256,
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _liqToRemove: uint256 = max_value(uint256),
    _minAmountA: uint256 = 0,
    _minAmountB: uint256 = 0,
) -> (uint256, uint256, uint256, bool):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms

    legoAddr: address = self._getLegoAddr(_legoId)
    lpToken: address = empty(address)
    liqToRemove: uint256 = _liqToRemove

    # transfer nft to lego (if applicable)
    hasNftLiqPosition: bool = _nftAddr != empty(address) and _nftTokenId != 0
    if hasNftLiqPosition:
        extcall IERC721(_nftAddr).safeTransferFrom(self, legoAddr, _nftTokenId, ERC721_RECEIVE_DATA)

    # handle lp token
    else:
        lpToken = staticcall UnderscoreLego(legoAddr).getLpToken(_pool)
        liqToRemove = self._getAmount(lpToken, liqToRemove)
        assert extcall IERC20(lpToken).approve(legoAddr, liqToRemove, default_return_value=True) # dev: approval failed

    # remove liquidity via lego partner
    amountA: uint256 = 0
    amountB: uint256 = 0
    usdValue: uint256 = 0
    liquidityRemoved: uint256 = 0
    refundedLpAmount: uint256 = 0
    isDepleted: bool = False
    amountA, amountB, usdValue, liquidityRemoved, refundedLpAmount, isDepleted = extcall UnderscoreLego(legoAddr).removeLiquidity(_nftTokenId, _pool, _tokenA, _tokenB, lpToken, liqToRemove, _minAmountA, _minAmountB, self)

    # validate the nft came back, reset lp token approvals
    if hasNftLiqPosition:
        if not isDepleted:
            assert staticcall IERC721(_nftAddr).ownerOf(_nftTokenId) == self # dev: nft not returned
    else:
        assert extcall IERC20(lpToken).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    log EndaomentLiquidityRemoved(tokenA=_tokenA, tokenB=_tokenB, removedAmountA=amountA, removedAmountB=amountB, usdValue=usdValue, isDepleted=isDepleted, liquidityRemoved=liquidityRemoved, lpToken=lpToken, refundedLpAmount=refundedLpAmount, legoId=_legoId, legoAddr=legoAddr)
    return amountA, amountB, usdValue, isDepleted


################
# Wrapped ETH #
################


# eth -> weth


@nonreentrant
@payable
@external
def convertEthToWeth(
    _amount: uint256 = max_value(uint256),
    _depositLegoId: uint256 = 0,
    _depositVault: address = empty(address),
) -> (uint256, address, uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    weth: address = WETH

    # convert eth to weth
    amount: uint256 = min(_amount, self.balance)
    assert amount != 0 # dev: nothing to convert
    extcall WethContract(weth).deposit(value=amount)
    log EndaomentEthConvertedToWeth(amount=amount, paidEth=msg.value, weth=weth)

    # deposit weth into lego partner
    vaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    if _depositLegoId != 0:
        depositUsdValue: uint256 = 0
        amount, vaultToken, vaultTokenAmountReceived, depositUsdValue = self._depositTokens(_depositLegoId, weth, _depositVault, amount)

    return amount, vaultToken, vaultTokenAmountReceived


# weth -> eth


@nonreentrant
@external
def convertWethToEth(
    _amount: uint256 = max_value(uint256),
    _recipient: address = empty(address),
    _withdrawLegoId: uint256 = 0,
    _withdrawVaultAddr: address = empty(address),
    _hasWithdrawVaultToken: bool = True,
) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    weth: address = WETH

    # withdraw weth from lego partner (if applicable)
    amount: uint256 = _amount
    usdValue: uint256 = 0
    if _withdrawLegoId != 0:
        _na: uint256 = 0
        amount, _na, usdValue = self._withdrawTokens(_withdrawLegoId, weth, _withdrawVaultAddr, _amount, _hasWithdrawVaultToken)

    # convert weth to eth
    amount = min(amount, staticcall IERC20(weth).balanceOf(self))
    assert amount != 0 # dev: nothing to convert
    extcall WethContract(weth).withdraw(amount)
    log EndaomentWethConvertedToEth(amount=amount, weth=weth)

    # ignoring `_recipient` in this context
    return amount


#################
# Claim Rewards #
#################


@nonreentrant
@external
def claimRewards(
    _legoId: uint256,
    _market: address = empty(address),
    _rewardToken: address = empty(address),
    _rewardAmount: uint256 = max_value(uint256),
    _proof: bytes32 = empty(bytes32),
):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms

    # make sure lego has access to claim rewards
    legoAddr: address = self._getLegoAddr(_legoId)
    self._checkLegoAccessForAction(legoAddr)

    # pre reward balance
    preRewardBalance: uint256 = 0
    if _rewardToken != empty(address):
        preRewardBalance = staticcall IERC20(_rewardToken).balanceOf(self)

    # claim rewards
    extcall UnderscoreLego(legoAddr).claimRewards(self, _market, _rewardToken, _rewardAmount, _proof)

    # post reward balance
    postRewardBalance: uint256 = 0
    if _rewardToken != empty(address):
        postRewardBalance = staticcall IERC20(_rewardToken).balanceOf(self)
    rewardAmount: uint256 = postRewardBalance - preRewardBalance

    log EndaomentRewardsClaimed(market=_market, rewardToken=_rewardToken, rewardAmount=rewardAmount, proof=_proof, legoId=_legoId, legoAddr=legoAddr)


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
    legoAddr: address = self._getLegoAddr(_legoId)
    liquidityAdded: uint256 = 0
    liqAmountA: uint256 = 0
    liqAmountB: uint256 = 0
    usdValue: uint256 = 0
    nftTokenId: uint256 = 0
    liquidityAdded, liqAmountA, liqAmountB, usdValue, nftTokenId = self._addLiquidity(_legoId, legoAddr, empty(address), 0, _pool, _asset, a.greenToken, partnerAmount, greenAmount, 0, 0, 0, 0, _minLpAmount)

    # share lp balance with partner
    lpToken: address = staticcall UnderscoreLego(legoAddr).getLpToken(_pool)
    lpBalance: uint256 = staticcall IERC20(lpToken).balanceOf(self)
    assert lpBalance != 0 # dev: no liquidity added
    assert extcall IERC20(lpToken).transfer(_partner, lpBalance // 2, default_return_value=True) # dev: could not transfer

    # add pool debt
    extcall Ledger(a.ledger).updateGreenPoolDebt(_pool, greenAmount, True)

    log PartnerLiquidityAdded(partner=_partner, asset=_asset, partnerAmount=partnerAmount, greenAmount=greenAmount, lpBalance=lpBalance)
    return liquidityAdded, liqAmountA, liqAmountB


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
    legoRegistry: address = staticcall UnderscoreRegistry(underscoreRegistry).getAddy(LEGO_REGISTRY_ID)
    legoAddr: address = staticcall LegoRegistry(legoRegistry).getLegoAddr(_legoId)
    assert legoAddr != empty(address) # dev: invalid lego
    return legoAddr


# amount


@view
@internal
def _getAmount(_asset: address, _amount: uint256) -> uint256:
    amount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(self))
    assert amount != 0 # dev: no funds available
    return amount


# recover nft


@external
def recoverNft(_collection: address, _nftTokenId: uint256, _recipient: address) -> bool:
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    if staticcall IERC721(_collection).ownerOf(_nftTokenId) != self:
        return False

    extcall IERC721(_collection).safeTransferFrom(self, _recipient, _nftTokenId)
    log EndaomentNftRecovered(collection=_collection, nftTokenId=_nftTokenId, recipient=_recipient)
    return True


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
def _checkLegoAccessForAction(_legoAddr: address):
    targetAddr: address = empty(address)
    accessAbi: String[64] = empty(String[64])
    numInputs: uint256 = 0
    targetAddr, accessAbi, numInputs = staticcall UnderscoreLego(_legoAddr).getAccessForLego(self)

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
            revert_on_failure=False,
            max_outsize=32,
        )
    
    # assumes input (and order) is: user addr (owner), lego addr (operator)
    elif numInputs == 2:
        success, response = raw_call(
            targetAddr,
            concat(
                method_abi,
                convert(self, bytes32),
                convert(_legoAddr, bytes32),
            ),
            revert_on_failure=False,
            max_outsize=32,
        )

    # assumes input (and order) is: user addr (owner), lego addr (operator), allowed bool
    elif numInputs == 3:
        success, response = raw_call(
            targetAddr,
            concat(
                method_abi,
                convert(self, bytes32),
                convert(_legoAddr, bytes32),
                convert(True, bytes32),
            ),
            revert_on_failure=False,
            max_outsize=32,
        )

    assert success # dev: failed to set operator


####################
# Other Underscore #
####################


@nonreentrant
@external
def borrow(
    _legoId: uint256,
    _borrowAsset: address = empty(address),
    _amount: uint256 = max_value(uint256),
) -> (address, uint256, uint256):
    return empty(address), 0, 0


@nonreentrant
@external
def repayDebt(
    _legoId: uint256,
    _paymentAsset: address,
    _paymentAmount: uint256 = max_value(uint256),
) -> (address, uint256, uint256, uint256):
    return empty(address), 0, 0, 0


@nonreentrant
@external
def transferFunds(
    _recipient: address,
    _amount: uint256 = max_value(uint256),
    _asset: address = empty(address),
) -> (uint256, uint256):
    # NOTE: use `recoverFunds()` from DeptBasics module instead
    return 0, 0