# SPDX-License-Identifier: MIT
# @version 0.4.3

# Uniswap V3 TWAP math for UniswapV3TwapPrices. Pure integer functions only:
# callers gate every input and treat a False / zero result as "unavailable".
#
# Provenance:
#   - `_getSqrtRatioAtTick` and `_mulDiv` are derived from Uniswap v4-core,
#     commit 46c6834698c48bc4a463a86d8420f4eb1d7f3b75 (MIT): TickMath's
#     getSqrtPriceAtTick (the V3 getSqrtRatioAtTick equivalent) and FullMath's
#     mulDiv, which credits Remco Bloemen: https://xn--2-umb.com/21/muldiv
#   - `_getQuoteAtTick`, `_getMeanTick` and `_getHarmonicLiquidity` are written
#     from docs/priceSources/uniswap-v3-twap-spec.md and checked bit-for-bit
#     against the pinned V3 / V4 reference builds under
#     tests/priceSources/uniswap_v3/reference.
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

# uniswap v3 tick domain, and the sqrt ratios at its ends (Q64.96)
MIN_TICK: constant(int256) = -887272
MAX_TICK: constant(int256) = 887272
MIN_SQRT_RATIO: constant(uint256) = 4295128739
MAX_SQRT_RATIO: constant(uint256) = 1461446703485210103287273052203988822378723970342

Q32: constant(uint256) = 2 ** 32
Q64: constant(uint256) = 2 ** 64
Q128: constant(uint256) = 2 ** 128
Q192: constant(uint256) = 2 ** 192
MAX_UINT128: constant(uint256) = 2 ** 128 - 1
MAX_UINT160: constant(uint256) = 2 ** 160 - 1


#############
# Full Math #
#############


@pure
@internal
def _mulDiv(_a: uint256, _b: uint256, _denominator: uint256) -> (bool, uint256):
    # floor(a * b / denominator) with a 512-bit intermediate. Returns False when
    # the denominator is zero or the quotient does not fit in 256 bits, so an
    # unrepresentable result is reported rather than truncated

    # 512-bit product [prod1 prod0] = a * b, recovered via mulmod by 2**256 - 1
    prod0: uint256 = unsafe_mul(_a, _b)
    mm: uint256 = uint256_mulmod(_a, _b, max_value(uint256))
    prod1: uint256 = unsafe_sub(unsafe_sub(mm, prod0), convert(mm < prod0, uint256))

    # quotient fits only if denominator > prod1 (also rejects a zero denominator)
    if _denominator <= prod1:
        return False, 0

    # short circuit: the product already fits in 256 bits
    if prod1 == 0:
        return True, prod0 // _denominator

    # make the division exact by subtracting the remainder from [prod1 prod0]
    remainder: uint256 = uint256_mulmod(_a, _b, _denominator)
    prod1 = unsafe_sub(prod1, convert(remainder > prod0, uint256))
    prod0 = unsafe_sub(prod0, remainder)

    # factor powers of two out of the denominator and shift the product to match
    twos: uint256 = unsafe_sub(0, _denominator) & _denominator
    oddDenominator: uint256 = _denominator // twos
    prod0 = prod0 // twos
    prod0 |= unsafe_mul(prod1, unsafe_add(unsafe_div(unsafe_sub(0, twos), twos), 1))

    # modular inverse of the odd denominator: the seed is correct mod 2**4 and
    # each newton step doubles the precision, so six steps reach 2**256
    inverse: uint256 = unsafe_mul(3, oddDenominator) ^ 2
    for i: uint256 in range(6):
        inverse = unsafe_mul(inverse, unsafe_sub(2, unsafe_mul(oddDenominator, inverse)))
    return True, unsafe_mul(prod0, inverse)


#############
# Tick Math #
#############


@pure
@internal
def _getSqrtRatioAtTick(_tick: int256) -> uint256:
    # sqrt(1.0001 ** tick) as a Q64.96 fixed point, exactly as upstream
    # computes it: a Q128.128 product of the selected per-bit constants,
    # inverted for positive ticks, then rounded up into Q64.96. Zero for a
    # tick outside the domain
    if _tick < MIN_TICK or _tick > MAX_TICK:
        return 0

    # the initial ratio can equal 2**128; every multiplier below it, so each
    # product fits uint256 before the canonical >> 128
    absTick: uint256 = convert(abs(_tick), uint256)
    ratio: uint256 = Q128
    if absTick & 1 != 0:
        ratio = 340265354078544963557816517032075149313
    if absTick & 2 != 0:
        ratio = (ratio * 340248342086729790484326174814286782778) >> 128
    if absTick & 4 != 0:
        ratio = (ratio * 340214320654664324051920982716015181260) >> 128
    if absTick & 8 != 0:
        ratio = (ratio * 340146287995602323631171512101879684304) >> 128
    if absTick & 16 != 0:
        ratio = (ratio * 340010263488231146823593991679159461444) >> 128
    if absTick & 32 != 0:
        ratio = (ratio * 339738377640345403697157401104375502016) >> 128
    if absTick & 64 != 0:
        ratio = (ratio * 339195258003219555707034227454543997025) >> 128
    if absTick & 128 != 0:
        ratio = (ratio * 338111622100601834656805679988414885971) >> 128
    if absTick & 256 != 0:
        ratio = (ratio * 335954724994790223023589805789778977700) >> 128
    if absTick & 512 != 0:
        ratio = (ratio * 331682121138379247127172139078559817300) >> 128
    if absTick & 1024 != 0:
        ratio = (ratio * 323299236684853023288211250268160618739) >> 128
    if absTick & 2048 != 0:
        ratio = (ratio * 307163716377032989948697243942600083929) >> 128
    if absTick & 4096 != 0:
        ratio = (ratio * 277268403626896220162999269216087595045) >> 128
    if absTick & 8192 != 0:
        ratio = (ratio * 225923453940442621947126027127485391333) >> 128
    if absTick & 16384 != 0:
        ratio = (ratio * 149997214084966997727330242082538205943) >> 128
    if absTick & 32768 != 0:
        ratio = (ratio * 66119101136024775622716233608466517926) >> 128
    if absTick & 65536 != 0:
        ratio = (ratio * 12847376061809297530290974190478138313) >> 128
    if absTick & 131072 != 0:
        ratio = (ratio * 485053260817066172746253684029974020) >> 128
    if absTick & 262144 != 0:
        ratio = (ratio * 691415978906521570653435304214168) >> 128
    if absTick & 524288 != 0:
        ratio = (ratio * 1404880482679654955896180642) >> 128

    # the table is built for negative ticks; invert for positive ones
    if _tick > 0:
        ratio = max_value(uint256) // ratio

    # Q128.128 -> Q64.96, rounding up so the result round-trips upstream's tick math
    return (ratio >> 32) + convert(ratio & (Q32 - 1) != 0, uint256)


@pure
@internal
def _getQuoteAtTick(_tick: int256, _baseAmount: uint256, _baseIsToken0: bool) -> uint256:
    # quote token received for `_baseAmount` of the base token at `_tick`,
    # mirroring OracleLibrary.getQuoteAtTick. Zero for an out-of-domain tick
    # or an unrepresentable intermediate / result
    sqrtRatioX96: uint256 = self._getSqrtRatioAtTick(_tick)
    if sqrtRatioX96 == 0:
        return 0

    # square the sqrt ratio directly while it fits uint128 (Q64.192);
    # otherwise reduce it to Q128 with full precision
    isValid: bool = False
    ratio: uint256 = 0
    unit: uint256 = Q192
    if sqrtRatioX96 <= MAX_UINT128:
        ratio = sqrtRatioX96 * sqrtRatioX96
    else:
        isValid, ratio = self._mulDiv(sqrtRatioX96, sqrtRatioX96, Q64)
        if not isValid:
            return 0
        unit = Q128

    # ratio is token1 per token0, so the base's position picks the direction
    quote: uint256 = 0
    if _baseIsToken0:
        isValid, quote = self._mulDiv(ratio, _baseAmount, unit)
    else:
        isValid, quote = self._mulDiv(unit, _baseAmount, ratio)
    return quote if isValid else 0


###############
# Oracle Math #
###############


@pure
@internal
def _getMeanTick(_tickCumulativePast: int56, _tickCumulativeNow: int56, _window: uint32) -> (bool, int256):
    # time-weighted mean tick over the window as the mathematical floor of
    # (delta / window), like OracleLibrary.consult. Valid only inside the tick
    # domain; a zero delta is a valid mean tick of zero
    if _window == 0:
        return False, 0

    # subtract at the accumulator's int56 width BEFORE widening so a
    # legitimate wrap of the cumulative survives
    delta: int256 = convert(unsafe_sub(_tickCumulativeNow, _tickCumulativePast), int256)
    divisor: int256 = convert(_window, int256)

    # vyper's // truncates toward zero; round a negative inexact quotient down
    meanTick: int256 = delta // divisor
    if delta < 0 and delta % divisor != 0:
        meanTick -= 1
    return meanTick >= MIN_TICK and meanTick <= MAX_TICK, meanTick


@pure
@internal
def _getHarmonicLiquidity(_liquidityCumulativePast: uint160, _liquidityCumulativeNow: uint160, _window: uint32) -> uint256:
    # harmonic mean liquidity over the window, matching OracleLibrary.consult:
    #   floor(window * (2**160 - 1) / (secondsPerLiquidityDelta << 32))
    # Zero for a zero window / delta, or a result above uint128 (rejected
    # instead of reproducing upstream's narrowing cast)

    # subtract at the accumulator's uint160 width so a legitimate wrap survives
    delta: uint256 = convert(unsafe_sub(_liquidityCumulativeNow, _liquidityCumulativePast), uint256)
    if delta == 0 or _window == 0:
        return 0

    # numerator and shifted denominator both fit uint192 for permitted inputs
    harmonicLiquidity: uint256 = convert(_window, uint256) * MAX_UINT160 // (delta << 32)
    return harmonicLiquidity if harmonicLiquidity <= MAX_UINT128 else 0
