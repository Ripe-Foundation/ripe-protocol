# @version 0.4.3
# Local callback payer for organic history tests; never a pricing dependency.
from ethereum.ercs import IERC20
interface Pool:
    def mint(recipient: address, lower: int24, upper: int24, amount: uint128, data: Bytes[1]) -> (uint256,uint256): nonpayable
    def burn(lower: int24, upper: int24, amount: uint128) -> (uint256,uint256): nonpayable
    def token0() -> address: view
    def token1() -> address: view
interface SwapPool:
    def swap(recipient: address, zeroForOne: bool, amount: int256, limit: uint160, data: Bytes[1]) -> (int256,int256): nonpayable
pool: address
@external
def add(pool: address, amount: uint128):
    self.pool = pool
    extcall Pool(pool).mint(self, -887200, 887200, amount, b"")
@external
def remove(pool: address, amount: uint128):
    self.pool = pool
    extcall Pool(pool).burn(-887200, 887200, amount)
@external
def uniswapV3MintCallback(a: uint256, b: uint256, data: Bytes[1]):
    assert msg.sender == self.pool
    assert extcall IERC20(staticcall Pool(msg.sender).token0()).transfer(msg.sender, a)
    assert extcall IERC20(staticcall Pool(msg.sender).token1()).transfer(msg.sender, b)
@external
def move(pool: address, zeroForOne: bool, limit: uint160):
    self.pool = pool
    extcall SwapPool(pool).swap(self, zeroForOne, 10**30, limit, b"")
@external
def uniswapV3SwapCallback(a: int256, b: int256, data: Bytes[1]):
    assert msg.sender == self.pool
    if a > 0:
        assert extcall IERC20(staticcall Pool(msg.sender).token0()).transfer(msg.sender, convert(a,uint256))
    if b > 0:
        assert extcall IERC20(staticcall Pool(msg.sender).token1()).transfer(msg.sender, convert(b,uint256))
@external
def add_range(pool: address, lower: int24, upper: int24, amount: uint128):
    self.pool = pool
    extcall Pool(pool).mint(self, lower, upper, amount, b"")
