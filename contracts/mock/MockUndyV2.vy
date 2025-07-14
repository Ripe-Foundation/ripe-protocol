# @version 0.4.3

from ethereum.ercs import IERC20
from interfaces import UndyLego

interface LegacyLego:
    def addLiquidity(_nftTokenId: uint256, _pool: address, _tokenA: address, _tokenB: address, _tickLower: int24, _tickUpper: int24, _amountA: uint256, _amountB: uint256, _minAmountA: uint256, _minAmountB: uint256, _minLpAmount: uint256, _recipient: address, _oracleRegistry: address = empty(address)) -> (uint256, uint256, uint256, uint256, uint256, uint256, uint256): nonpayable

interface LegoRegistry:
    def getLegoAddr(_legoId: uint256) -> address: view

interface UnderscoreRegistry:
    def getAddy(_regId: uint256) -> address: view

MAX_TOKEN_PATH: constant(uint256) = 5
LEGACY_LEGO_REGISTRY_ID: constant(uint256) = 2
UNDY_LEGACY: public(immutable(address))

useThisLegoId: public(uint256)


@deploy
def __init__(_undyLegacy: address):
    UNDY_LEGACY = _undyLegacy


@view
@external
def getAddr(_regId: uint256) -> address:
    return self


@view
@external
def isUserWallet(_addr: address) -> bool:
    return True


@view
@internal
def _getLegoAddr(_legoId: uint256) -> address:
    legoRegistry: address = staticcall UnderscoreRegistry(UNDY_LEGACY).getAddy(LEGACY_LEGO_REGISTRY_ID)
    return staticcall LegoRegistry(legoRegistry).getLegoAddr(_legoId)


@external
def setUseThisLegoId(_legoId: uint256):
    self.useThisLegoId = _legoId


#############
# Liquidity #
#############


# add liquidity


@external
def addLiquidity(
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256,
    _amountB: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _minLpAmount: uint256,
    _extraData: bytes32,
    _recipient: address,
    _miniAddys: UndyLego.MiniAddys = empty(UndyLego.MiniAddys),
) -> (address, uint256, uint256, uint256, uint256):
    preLegoBalanceA: uint256 = staticcall IERC20(_tokenA).balanceOf(self)
    preLegoBalanceB: uint256 = staticcall IERC20(_tokenB).balanceOf(self)

    # token a
    liqAmountA: uint256 = min(_amountA, staticcall IERC20(_tokenA).balanceOf(msg.sender))
    assert liqAmountA != 0 # dev: nothing to transfer
    assert extcall IERC20(_tokenA).transferFrom(msg.sender, self, liqAmountA, default_return_value=True) # dev: transfer failed

    # token b
    liqAmountB: uint256 = min(_amountB, staticcall IERC20(_tokenB).balanceOf(msg.sender))
    assert liqAmountB != 0 # dev: nothing to transfer
    assert extcall IERC20(_tokenB).transferFrom(msg.sender, self, liqAmountB, default_return_value=True) # dev: transfer failed

    # get lecacy lego addr
    legoAddr: address = self._getLegoAddr(self.useThisLegoId)

    # approvals
    assert extcall IERC20(_tokenA).approve(legoAddr, liqAmountA, default_return_value=True) # dev: approval failed
    assert extcall IERC20(_tokenB).approve(legoAddr, liqAmountB, default_return_value=True) # dev: approval failed

    # legacy underscore lego
    liquidityAdded: uint256 = 0
    usdValue: uint256 = 0
    refundAssetAmountALeg: uint256 = 0
    refundAssetAmountBLeg: uint256 = 0
    nftTokenId: uint256 = 0
    liquidityAdded, liqAmountA, liqAmountB, usdValue, refundAssetAmountALeg, refundAssetAmountBLeg, nftTokenId = extcall LegacyLego(legoAddr).addLiquidity(
        0,
        _pool,
        _tokenA,
        _tokenB,
        0,
        0,
        liqAmountA,
        liqAmountB,
        _minAmountA,
        _minAmountB,
        _minLpAmount,
        _recipient,
    )

    # reset approvals
    assert extcall IERC20(_tokenA).approve(legoAddr, 0, default_return_value=True) # dev: approval failed
    assert extcall IERC20(_tokenB).approve(legoAddr, 0, default_return_value=True) # dev: approval failed

    # refund if full liquidity was not added
    currentLegoBalanceA: uint256 = staticcall IERC20(_tokenA).balanceOf(self)
    refundAssetAmountA: uint256 = 0
    if currentLegoBalanceA > preLegoBalanceA:
        refundAssetAmountA = currentLegoBalanceA - preLegoBalanceA
        assert extcall IERC20(_tokenA).transfer(msg.sender, refundAssetAmountA, default_return_value=True) # dev: transfer failed

    currentLegoBalanceB: uint256 = staticcall IERC20(_tokenB).balanceOf(self)
    refundAssetAmountB: uint256 = 0
    if currentLegoBalanceB > preLegoBalanceB:
        refundAssetAmountB = currentLegoBalanceB - preLegoBalanceB
        assert extcall IERC20(_tokenB).transfer(msg.sender, refundAssetAmountB, default_return_value=True) # dev: transfer failed

    return _pool, liquidityAdded, liqAmountA, liqAmountB, usdValue
