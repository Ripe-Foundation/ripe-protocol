#!/usr/bin/env python3
"""Read-only, pinned Uniswap V3 depth. Never submits a transaction.

Exact-input swap segment rounding and tick crossing follow the pinned Uniswap
references in tests/priceSources/uniswap_v3/reference. USD values mark the input
at the initial spot quote ratio and the live PriceDesk quote price at the pin.
They are market depth, not the capital cost of manipulating a TWAP.
"""
import argparse
from functools import lru_cache
from fractions import Fraction
import json
from math import isqrt
from pathlib import Path
import re
import sys

import requests
from eth_abi import decode, encode
from eth_utils import keccak, to_checksum_address

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

Q96 = 1 << 96
MIN_TICK, MAX_TICK = -887272, 887272
# TickMath constants derived from the MIT v4 source pinned in the TWAP math
# module. Copyright 2023 Universal Navigation Inc.; notice retained below.
TICK_FACTORS = (
    340265354078544963557816517032075149313,
    340248342086729790484326174814286782778,
    340214320654664324051920982716015181260,
    340146287995602323631171512101879684304,
    340010263488231146823593991679159461444,
    339738377640345403697157401104375502016,
    339195258003219555707034227454543997025,
    338111622100601834656805679988414885971,
    335954724994790223023589805789778977700,
    331682121138379247127172139078559817300,
    323299236684853023288211250268160618739,
    307163716377032989948697243942600083929,
    277268403626896220162999269216087595045,
    225923453940442621947126027127485391333,
    149997214084966997727330242082538205943,
    66119101136024775622716233608466517926,
    12847376061809297530290974190478138313,
    485053260817066172746253684029974020,
    691415978906521570653435304214168,
    1404880482679654955896180642,
)


def ceil_div(a, b):
    return (a + b - 1) // b


def sqrt_at_tick(tick):
    if not MIN_TICK <= tick <= MAX_TICK:
        raise ValueError('tick outside Uniswap domain')
    ratio = 1 << 128
    for bit, factor in enumerate(TICK_FACTORS):
        if abs(tick) & (1 << bit):
            ratio = ratio * factor >> 128
    if tick > 0:
        ratio = ((1 << 256) - 1) // ratio
    return ceil_div(ratio, 1 << 32)


class Rpc:
    def __init__(self, url):
        self.url = url
        self.session = requests.Session()

    def call(self, method, params):
        # Failure is explicit; never substitute another block/provider.
        try:
            response = self.session.post(self.url, json={'jsonrpc': '2.0', 'id': 1,
                'method': method, 'params': params}, timeout=(5, 20))
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError):
            raise ValueError('RPC transport or response failure') from None
        if 'error' in data:
            # Do not echo endpoint credentials or provider-supplied URLs.
            raise ValueError(f'RPC {method} failed (code {data["error"].get("code")})')
        if 'result' not in data:
            raise ValueError('RPC result missing')
        return data['result']


class Pinned:
    def __init__(self, rpc, block=None):
        self.rpc = rpc
        self.chain_id = int(rpc.call('eth_chainId', []), 16)
        self.block = int(rpc.call('eth_blockNumber', []), 16) if block is None else block
        self.header = self._header()
        self.timestamp = int(self.header['timestamp'], 16)

    def _header(self):
        header = self.rpc.call('eth_getBlockByNumber', [hex(self.block), False])
        if not isinstance(header, dict) or not all(k in header for k in ('number', 'hash', 'timestamp')):
            raise ValueError('pinned header incomplete')
        if int(header['number'], 16) != self.block or not re.fullmatch('0x[0-9a-fA-F]{64}', header['hash']):
            raise ValueError('pinned header invalid')
        return {key: header[key] for key in ('number', 'hash', 'timestamp')}

    def verify(self):
        if self._header() != self.header:
            raise ValueError('pinned header changed; discard snapshot')

    @lru_cache(maxsize=None)
    def read(self, address, signature, outputs, inputs=(), args=()):
        data = keccak(text=signature)[:4] + encode(inputs, args)
        raw = self.rpc.call('eth_call', [{'to': to_checksum_address(address), 'data': '0x' + data.hex()}, hex(self.block)])
        return decode(outputs, bytes.fromhex(raw[2:]))


class PoolTicks:
    def __init__(self, pin, pool, spacing):
        self.pin, self.pool, self.spacing = pin, pool, spacing

    def next(self, tick, down):
        # Match nextInitializedTickWithinOneWord, including empty word boundaries.
        compressed = tick // self.spacing + (0 if down else 1)
        word, bit = compressed >> 8, compressed % 256
        bitmap, = self.pin.read(self.pool, 'tickBitmap(int16)', ('uint256',), ('int16',), (word,))
        masked = bitmap & ((1 << (bit + 1)) - 1) if down else bitmap & (((1 << 256) - 1) ^ ((1 << bit) - 1))
        index = (masked.bit_length() - 1 if down else (masked & -masked).bit_length() - 1) if masked else (0 if down else 255)
        boundary = (compressed + index - bit) * self.spacing
        return max(MIN_TICK, min(MAX_TICK, boundary)), bool(masked)

    def net(self, tick):
        gross, net, *_, initialized = self.pin.read(self.pool, 'ticks(int24)',
            ('uint128', 'int128', 'uint256', 'uint256', 'int56', 'uint160', 'uint32', 'bool'), ('int24',), (tick,))
        if not initialized or not gross:
            raise ValueError('bitmap and initialized tick disagree')
        return net


def walk_depth(sqrt_price, tick, liquidity, target, fee, ticks):
    """Fee-inclusive exact raw input to a Q96 limit, rounded like V3 swap steps."""
    if not 0 <= fee < 1_000_000 or not 0 <= liquidity < 1 << 128:
        raise ValueError('invalid fee or liquidity')
    down = target < sqrt_price
    start = sqrt_price
    amount_in = amount_out = steps = 0
    crossed = []
    while sqrt_price != target:
        boundary, initialized = ticks.next(tick, down)
        at_boundary = sqrt_at_tick(boundary)
        stop = max(target, at_boundary) if down else min(target, at_boundary)
        if not (stop <= sqrt_price if down else stop >= sqrt_price):
            raise ValueError('inconsistent tick/price')
        low, high = sorted((sqrt_price, stop))
        if down:
            net = ceil_div(liquidity * Q96 * (high-low), high*low)
            out = liquidity * (high-low) // Q96
        else:
            net = ceil_div(liquidity * (high-low), Q96)
            out = liquidity * Q96 * (high-low) // (high*low)
        amount_in += net + ceil_div(net * fee, 1_000_000-fee)
        amount_out += out
        sqrt_price = stop
        if stop == at_boundary:
            if initialized:
                delta = ticks.net(boundary)
                liquidity += -delta if down else delta
                if not 0 <= liquidity < 1 << 128:
                    raise ValueError('crossing produced invalid liquidity')
                crossed.append({'tick': boundary, 'liquidityNet': delta, 'liquidityAfter': liquidity})
            tick = boundary-1 if down else boundary
        steps += 1
        if steps > 200_000:
            raise ValueError('tick walk bound exceeded; no depth estimate produced')
    return {'input_raw': amount_in, 'output_raw': amount_out, 'zero_for_one': down,
            'sqrt_start_x96': start, 'sqrt_target_x96': target, 'steps': steps, 'crossings': crossed}


def spot_target(sqrt_price, asset_is_token0, move_percent):
    ratio = Fraction(100 + move_percent, 100)
    if not asset_is_token0:
        ratio = 1 / ratio
    target2 = Fraction(sqrt_price * sqrt_price) * ratio
    target = isqrt(target2.numerator // target2.denominator)
    # Round away from the initial price so the requested percentage is reached.
    if ratio > 1 and target * target * target2.denominator < target2.numerator:
        target += 1
    if not sqrt_at_tick(MIN_TICK) < target < sqrt_at_tick(MAX_TICK):
        raise ValueError('requested spot move exceeds pool domain')
    return target


def resolve_desk(pin, source, explicit):
    if source:
        hq, = pin.read(source, 'getRipeHq()', ('address',))
    elif explicit:
        return explicit, 'explicit --price-desk'
    else:
        networks = {4663: 'robinhood-mainnet', 8453: 'base-mainnet'}
        if pin.chain_id not in networks:
            raise ValueError('supply --source or --price-desk on this chain')
        manifest = Path(__file__).resolve().parents[1] / 'migration_history' / networks[pin.chain_id] / 'v1/current-manifest.json'
        hq = json.loads(manifest.read_text())['contracts']['RipeHq']['address']
    desk, = pin.read(hq, 'getAddr(uint256)', ('address',), ('uint256',), (7,))
    if int(desk, 16) == 0 or (explicit and explicit.lower() != desk.lower()):
        raise ValueError('missing canonical desk or explicit desk disagrees with source')
    return desk, 'live RipeHq.getAddr(7), hq=' + hq


def snapshot(pin, pool, asset, source=None, price_desk=None, window=3600, age=1800, ratio=5000):
    if source:
        window, age, ratio = pin.read(source, 'feedDefaults()', ('uint32', 'uint32', 'uint256'))
    if not 1800 <= window <= 14400 or not 0 < age <= window or not 0 < ratio <= 10000:
        raise ValueError('invalid proposal defaults')
    token0, = pin.read(pool, 'token0()', ('address',))
    token1, = pin.read(pool, 'token1()', ('address',))
    if asset.lower() not in (token0.lower(), token1.lower()):
        raise ValueError('asset is not a pool token')
    asset0 = asset.lower() == token0.lower()
    quote = token1 if asset0 else token0
    d0, = pin.read(token0, 'decimals()', ('uint8',))
    d1, = pin.read(token1, 'decimals()', ('uint8',))
    if max(d0, d1) > 18:
        raise ValueError('token decimals exceed source domain')
    fee, = pin.read(pool, 'fee()', ('uint24',))
    spacing, = pin.read(pool, 'tickSpacing()', ('int24',))
    if spacing <= 0:
        raise ValueError('invalid tick spacing')
    liquidity, = pin.read(pool, 'liquidity()', ('uint128',))
    sqrt_price, tick, index, card, card_next, _, unlocked = pin.read(pool, 'slot0()', ('uint160', 'int24', 'uint16', 'uint16', 'uint16', 'uint8', 'bool'))
    latest, _, _, initialized = pin.read(pool, 'observations(uint256)', ('uint32', 'int56', 'uint160', 'bool'), ('uint256',), (index,))
    if not unlocked or not initialized or not 0 <= index < card <= card_next:
        raise ValueError('invalid/locked pool observation state')
    _, cumulative = pin.read(pool, 'observe(uint32[])', ('int56[]', 'uint160[]'), ('uint32[]',), ((window, 0),))
    delta = (cumulative[1] - cumulative[0]) % (1 << 160)
    harmonic = window * ((1 << 160) - 1) // (delta << 32) if delta else 0
    if harmonic >= 1 << 128:
        harmonic = 0
    floor = ceil_div(harmonic * ratio, 10000)
    desk, desk_resolution = resolve_desk(pin, source, price_desk)
    quote_price, = pin.read(desk, 'getPrice(address)', ('uint256',), ('address',), (quote,))
    if quote_price == 0:
        raise ValueError('live PriceDesk quote is unavailable at pin')
    qdec = d1 if asset0 else d0
    price1_per_raw0 = Fraction(sqrt_price*sqrt_price, Q96*Q96)
    quote_per_raw = (price1_per_raw0, Fraction(1)) if asset0 else (Fraction(1), 1/price1_per_raw0)
    ticks = PoolTicks(pin, pool, spacing)
    rows = []
    for percent in (-1, 1, -2, 2):
        row = walk_depth(sqrt_price, tick, liquidity, spot_target(sqrt_price, asset0, percent), fee, ticks)
        input0 = row['zero_for_one']
        usd18 = Fraction(row['input_raw']) * quote_per_raw[0 if input0 else 1] * quote_price / 10**qdec
        row.update(asset_spot_move_percent=percent, input_token=token0 if input0 else token1,
                   input_usd18=usd18.numerator//usd18.denominator)
        value = row['input_usd18']
        row['input_usd'] = f'{value//10**18}.{value%10**18:018d}'
        rows.append(row)
    pin.verify()
    obs_age = (pin.timestamp % (1 << 32) - latest) % (1 << 32)
    return {'label': f'market depth snapshot at block {pin.block}; not a TWAP manipulation cost',
        'block': pin.block, 'block_hash': pin.header['hash'], 'chain_id': pin.chain_id,
        'pool': pool, 'token0': token0, 'token1': token1, 'asset_side': 0 if asset0 else 1, 'quote': quote,
        'fee_pips': fee, 'fee_inclusive': True, 'current_liquidity': liquidity, 'harmonic_liquidity': harmonic,
        'window': window, 'max_observation_age': age, 'ratio_bps': ratio, 'proposal_min_liquidity': floor,
        'observation_cardinality': card, 'cardinality_clears_window_plus_one': card >= window+1,
        'latest_observation_age': obs_age, 'observation_age_passes': obs_age <= age,
        'price_desk': desk, 'desk_resolution': desk_resolution, 'quote_price_usd18': quote_price,
        'valuation': 'Input marked at initial spot quote ratio and pinned live PriceDesk quote USD; fee inclusive per swap step',
        'directions': rows, 'smaller_direction_2pct_usd18': min(r['input_usd18'] for r in rows if abs(r['asset_spot_move_percent']) == 2)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rpc'); parser.add_argument('pool'); parser.add_argument('asset')
    parser.add_argument('--source'); parser.add_argument('--price-desk', help='Override manifest lookup when no source is supplied')
    parser.add_argument('--block', type=int)
    parser.add_argument('--window', type=int, default=3600)
    parser.add_argument('--age', type=int, default=1800)
    parser.add_argument('--ratio', type=int, default=5000)
    args = parser.parse_args()
    try:
        result = snapshot(Pinned(Rpc(args.rpc), args.block), to_checksum_address(args.pool),
            to_checksum_address(args.asset), args.source, args.price_desk, args.window, args.age, args.ratio)
    except (ValueError, KeyError, OSError) as exc:
        print(f'No verified depth snapshot: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
