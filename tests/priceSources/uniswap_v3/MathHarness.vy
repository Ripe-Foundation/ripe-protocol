# SPDX-License-Identifier: MIT
# @version 0.4.3
import contracts.priceSources.modules.UniswapV3TwapMath as math
@pure
@external
def sqrt(tick: int256) -> uint256:
    return math._getSqrtRatioAtTick(tick)
@pure
@external
def quote(tick: int256, amount: uint256, token0: bool) -> uint256:
    return math._getQuoteAtTick(tick, amount, token0)
@pure
@external
def mulDiv(a: uint256, b: uint256, d: uint256) -> (bool, uint256):
    return math._mulDiv(a, b, d)
@pure
@external
def mean(past: int56, current: int56, window: uint32) -> (bool, int256):
    return math._getMeanTick(past, current, window)
@pure
@external
def harmonic(past: uint160, current: uint160, window: uint32) -> uint256:
    return math._getHarmonicLiquidity(past, current, window)
