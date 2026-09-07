# SPDX-License-Identifier: MIT
# @version 0.4.3
# Derived tick-to-sqrt and floor mulDiv: Uniswap v4-core
# 46c6834698c48bc4a463a86d8420f4eb1d7f3b75 (MIT).
# getSqrtPriceAtTick maps to V3 getSqrtRatioAtTick.
# FullMath credits Remco Bloemen: https://xn--2-umb.com/21/muldiv
#
# Copyright 2023 Universal Navigation Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the “Software”), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons
# to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

MIN_TICK: constant(int256) = -887272
MAX_TICK: constant(int256) = 887272
MIN_SQRT_RATIO: constant(uint256) = 4295128739
MAX_SQRT_RATIO: constant(uint256) = 1461446703485210103287273052203988822378723970342


@pure
@internal
def mulDiv(a: uint256, b: uint256, denominator: uint256) -> (bool, uint256):
    # Reconstruct the 512-bit product, then divide exactly modulo 2**256.
    lo: uint256 = unsafe_mul(a, b)
    mm: uint256 = uint256_mulmod(a, b, max_value(uint256))
    hi: uint256 = unsafe_sub(unsafe_sub(mm, lo), convert(mm < lo, uint256))
    if denominator <= hi:
        return False, 0
    if hi == 0:
        return True, lo // denominator
    remainder: uint256 = uint256_mulmod(a, b, denominator)
    hi = unsafe_sub(hi, convert(remainder > lo, uint256))
    lo = unsafe_sub(lo, remainder)
    twos: uint256 = unsafe_sub(0, denominator) & denominator
    odd: uint256 = denominator // twos
    lo = lo // twos
    lo |= unsafe_mul(hi, unsafe_add(unsafe_div(unsafe_sub(0, twos), twos), 1))
    inverse: uint256 = unsafe_mul(3, odd) ^ 2
    for i: uint256 in range(6):
        inverse = unsafe_mul(inverse, unsafe_sub(2, unsafe_mul(odd, inverse)))
    return True, unsafe_mul(lo, inverse)


@pure
@internal
def sqrtAtTick(tick: int256) -> uint256:
    if tick < MIN_TICK or tick > MAX_TICK:
        return 0
    absolute: uint256 = convert(abs(tick), uint256)
    ratio: uint256 = 2**128
    if absolute & 1 != 0:
        ratio = 340265354078544963557816517032075149313
    if absolute & 2 != 0:
        ratio = (ratio * 340248342086729790484326174814286782778) >> 128
    if absolute & 4 != 0:
        ratio = (ratio * 340214320654664324051920982716015181260) >> 128
    if absolute & 8 != 0:
        ratio = (ratio * 340146287995602323631171512101879684304) >> 128
    if absolute & 16 != 0:
        ratio = (ratio * 340010263488231146823593991679159461444) >> 128
    if absolute & 32 != 0:
        ratio = (ratio * 339738377640345403697157401104375502016) >> 128
    if absolute & 64 != 0:
        ratio = (ratio * 339195258003219555707034227454543997025) >> 128
    if absolute & 128 != 0:
        ratio = (ratio * 338111622100601834656805679988414885971) >> 128
    if absolute & 256 != 0:
        ratio = (ratio * 335954724994790223023589805789778977700) >> 128
    if absolute & 512 != 0:
        ratio = (ratio * 331682121138379247127172139078559817300) >> 128
    if absolute & 1024 != 0:
        ratio = (ratio * 323299236684853023288211250268160618739) >> 128
    if absolute & 2048 != 0:
        ratio = (ratio * 307163716377032989948697243942600083929) >> 128
    if absolute & 4096 != 0:
        ratio = (ratio * 277268403626896220162999269216087595045) >> 128
    if absolute & 8192 != 0:
        ratio = (ratio * 225923453940442621947126027127485391333) >> 128
    if absolute & 16384 != 0:
        ratio = (ratio * 149997214084966997727330242082538205943) >> 128
    if absolute & 32768 != 0:
        ratio = (ratio * 66119101136024775622716233608466517926) >> 128
    if absolute & 65536 != 0:
        ratio = (ratio * 12847376061809297530290974190478138313) >> 128
    if absolute & 131072 != 0:
        ratio = (ratio * 485053260817066172746253684029974020) >> 128
    if absolute & 262144 != 0:
        ratio = (ratio * 691415978906521570653435304214168) >> 128
    if absolute & 524288 != 0:
        ratio = (ratio * 1404880482679654955896180642) >> 128
    if tick > 0:
        ratio = max_value(uint256) // ratio
    return (ratio >> 32) + convert(ratio & (2**32 - 1) != 0, uint256)


@pure
@internal
def quoteAtTick(tick: int256, amount: uint256, assetIsToken0: bool) -> uint256:
    sqrtRatio: uint256 = self.sqrtAtTick(tick)
    if sqrtRatio == 0:
        return 0
    ratio: uint256 = 0
    unit: uint256 = 2**192
    valid: bool = False
    if sqrtRatio <= convert(max_value(uint128), uint256):
        ratio = sqrtRatio * sqrtRatio
    else:
        valid, ratio = self.mulDiv(sqrtRatio, sqrtRatio, 2**64)
        if not valid:
            return 0
        unit = 2**128
    result: uint256 = 0
    if assetIsToken0:
        valid, result = self.mulDiv(ratio, amount, unit)
    else:
        valid, result = self.mulDiv(unit, amount, ratio)
    return result if valid else 0


@pure
@internal
def meanTick(past: int56, current: int56, window: uint32) -> (bool, int256):
    if window == 0:
        return False, 0
    # Subtract at the accumulator's width BEFORE widening, preserving wraps.
    delta: int256 = convert(unsafe_sub(current, past), int256)
    divisor: int256 = convert(window, int256)
    mean: int256 = delta // divisor
    if delta < 0 and delta % divisor != 0:
        mean -= 1
    return mean >= MIN_TICK and mean <= MAX_TICK, mean


@pure
@internal
def harmonicLiquidity(past: uint160, current: uint160, window: uint32) -> uint256:
    delta: uint256 = convert(unsafe_sub(current, past), uint256)
    if delta == 0 or window == 0:
        return 0
    harmonic: uint256 = convert(window, uint256) * convert(max_value(uint160), uint256) // (delta << 32)
    return harmonic if harmonic <= convert(max_value(uint128), uint256) else 0
