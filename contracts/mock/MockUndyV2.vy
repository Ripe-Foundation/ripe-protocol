# @version 0.4.3

from ethereum.ercs import IERC20
from interfaces import UndyLego

interface Lego:
    def addLiquidity(_pool: address, _tokenA: address, _tokenB: address, _amountA: uint256, _amountB: uint256, _minAmountA: uint256, _minAmountB: uint256, _minLpAmount: uint256, _extraData: bytes32, _recipient: address) -> (address, uint256, uint256, uint256, uint256): nonpayable

interface UnderscoreRegistry:
    def getAddr(_regId: uint256) -> address: view

MAX_TOKEN_PATH: constant(uint256) = 5
LEGO_REGISTRY_ID: constant(uint256) = 3
UNDY_REGISTRY: public(immutable(address))

useThisLegoId: public(uint256)
_isUserWallet: public(bool)
_earnVaults: public(HashMap[address, bool])
_basicEarnVaults: public(HashMap[address, bool])
_allAddressesAreVaults: public(bool)


@deploy
def __init__(_undyLegacy: address):
    UNDY_REGISTRY = _undyLegacy
    self._allAddressesAreVaults = True  # default behavior for backwards compatibility


@view
@external
def getAddr(_regId: uint256) -> address:
    return self


@view
@external
def isValidAddr(_addr: address) -> bool:
    return True


@view
@external
def isUserWallet(_addr: address) -> bool:
    return self._isUserWallet


@external
def setIsUserWallet(_isUserWallet: bool):
    self._isUserWallet = _isUserWallet


@view
@internal
def _getLegoAddr(_legoId: uint256) -> address:
    legoRegistry: address = staticcall UnderscoreRegistry(UNDY_REGISTRY).getAddr(LEGO_REGISTRY_ID)
    return staticcall UnderscoreRegistry(legoRegistry).getAddr(_legoId)


@external
def setUseThisLegoId(_legoId: uint256):
    self.useThisLegoId = _legoId


@view
@external
def isEarnVault(_vaultAddr: address) -> bool:
    if self._allAddressesAreVaults:
        return True
    return self._earnVaults[_vaultAddr]


@view
@external
def isBasicEarnVault(_vaultAddr: address) -> bool:
    if self._allAddressesAreVaults:
        return True
    return self._basicEarnVaults[_vaultAddr]


@external
def setEarnVault(_vaultAddr: address, _isVault: bool):
    self._earnVaults[_vaultAddr] = _isVault
    # Backwards-compatible default for tests that only call setEarnVault.
    self._basicEarnVaults[_vaultAddr] = _isVault


@external
def setBasicEarnVault(_vaultAddr: address, _isVault: bool):
    self._basicEarnVaults[_vaultAddr] = _isVault


@external
def setAllAddressesAreVaults(_allAreVaults: bool):
    self._allAddressesAreVaults = _allAreVaults


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
    lpToken: address = empty(address)
    lpAmountReceived: uint256 = 0
    usdValue: uint256 = 0
    lpToken, lpAmountReceived, liqAmountA, liqAmountB, usdValue = extcall Lego(legoAddr).addLiquidity(
        _pool,
        _tokenA,
        _tokenB,
        liqAmountA,
        liqAmountB,
        _minAmountA,
        _minAmountB,
        _minLpAmount,
        _extraData,
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

    return lpToken, lpAmountReceived, liqAmountA, liqAmountB, usdValue


@external
def addDepositRewards(_asset: address, _amount: uint256):
    amount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(msg.sender))
    assert amount != 0 # dev: nothing to add
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, amount, default_return_value=True) # dev: transfer failed
