"""Bit-exact compiled references and independent arbitrary-precision checks."""
import json
import random
from pathlib import Path

import boa
import pytest

from .compiled import deploy
from .reference.artifacts import verify_offline

U256 = 2**256 - 1
ROOT = Path(__file__).resolve().parents[3]


def test_compiled_tick_and_quote_differential(math):
    for version in ('v3', 'v4'):
        verify_offline(version)
    v3, v4 = deploy('v3', 'Reference'), deploy('v4', 'Reference')
    rng = random.Random(0x713A9)
    ticks = sorted(set([-887272, -887271, -1, 0, 1, 887271, 887272, 443636, 443637]
                       + [s * (2**i) for i in range(20) for s in (-1, 1)]
                       + [rng.randint(-887272, 887272) for _ in range(256)]))
    quotes = 0
    for tick in ticks:
        assert math.sqrt(tick) == v3.sqrt(tick) == v4.sqrt(tick)
        for decimals in (0, 6, 9, 18):
            for order in (True, False):
                a, b = ('0x' + '01'.zfill(40), '0x' + '02'.zfill(40))
                if not order:
                    a, b = b, a
                expected = v3.quote(tick, 10**decimals, a, b)
                assert math.quote(tick, 10**decimals, order) == v4.quote(tick, 10**decimals, a, b) == expected
                quotes += 1
    for bad in (-2**255, -887273, 887273, 2**255 - 1):
        assert math.sqrt(bad) == math.quote(bad, 10**18, True) == 0
    for bad in (-887273, 887273):
        for ref in (v3, v4):
            with boa.reverts():
                ref.sqrt(bad)
    print(f'COMPILED_DIFFERENTIAL ticks={len(ticks)} quotes={quotes} references=V3-0.7.6,V4-0.8.26,Vyper-0.4.3')


def test_frozen_math_vectors(math):
    data = json.loads((ROOT / 'docs/priceSources/uniswap-v3-twap-reference-vectors.json').read_text())
    for asset in data['assets']:
        for row in asset['vectors']:
            assert math.mean(*map(int, row['tick_cumulatives']), row['window_seconds']) == (True, row['mean_tick'])
            assert math.harmonic(*map(int, row['seconds_per_liquidity_cumulative_x128']), row['window_seconds']) == int(row['harmonic_liquidity'])
            assert math.sqrt(row['mean_tick']) == int(row['sqrt_ratio_x96'])
            q = math.quote(row['mean_tick'], 10**asset['asset_decimals'], asset['asset_is_token0'])
            assert q == int(row['weth_per_whole_asset_raw'])
            assert math.mulDiv(q, int(data['anchor']['price18']), 10**18) == (True, int(row['usd_price18']))


@pytest.mark.parametrize('delta,window,expected', [(0,1800,0),(1800,1800,1),(1801,1800,1),(-1800,1800,-1),(-1801,1800,-2),(-1,1800,-1)])
def test_signed_floor_and_accumulator_wrap(math, delta, window, expected):
    for past in (0, 2**55-1, -2**55):
        current = (past + delta + 2**55) % 2**56 - 2**55
        assert math.mean(past, current, window) == (True, expected)
    d = 1800 * 2**128 // 10**20
    expected_harmonic = 1800 * (2**160-1) // (d * 2**32)
    assert math.harmonic(2**160 - 10, d - 10, 1800) == expected_harmonic
    assert math.harmonic(0, 0, 1800) == math.harmonic(0, 1, 1800) == 0
    assert math.mean(0, 1, 0) == (False, 0)


def test_muldiv_boundaries_against_compiled_and_integer(math):
    v3, v4 = deploy('v3', 'Reference'), deploy('v4', 'Reference')
    for a,b,d in [(0,U256,1),(7,11,3),(U256,U256,U256),(U256,U256,U256-1),(2**200,2**100,2**50),(U256,2,0),(U256,U256,1),(1,1,0)]:
        q = a*b//d if d else U256+1
        valid = q <= U256
        assert math.mulDiv(a,b,d) == (valid, q if valid else 0)
        for ref in (v3,v4):
            if valid:
                assert ref.mulDiv(a,b,d) == q
            else:
                with boa.reverts():
                    ref.mulDiv(a,b,d)


@pytest.mark.fuzz
def test_fuzz_floor_and_narrow_wrap(math):
    rng=random.Random(0x56F1000)
    count=2048
    strata={(sign,remainder):0 for sign in (-1,1) for remainder in (False,True)}
    schedule=list(strata)*512
    rng.shuffle(schedule)
    for sign,remainder in schedule:
        w=rng.randint(1800,14400)
        delta=rng.randint(0,887270)*w + (rng.randint(1,w-1) if remainder else 0)
        delta*=sign
        strata[sign,bool(delta%w)]+=1
        past=rng.choice([-2**55,2**55-1,rng.randrange(-2**55,2**55)])
        current=(past+delta+2**55)%2**56-2**55
        assert math.mean(past,current,w)==(True,delta//w)
    assert all(n==512 for n in strata.values())
    print(f'FUZZ signed_floor={count} sign_exact_remainder={strata} seed=0x56f1000')


@pytest.mark.fuzz
def test_fuzz_muldiv(math):
    rng=random.Random(0x5121000)
    counts={'overflow_valid':0,'overflow_invalid':0,'zero_divisor':0,'ordinary':0}
    for i in range(2048):
        a,b=(2**255 | rng.getrandbits(255)),(2**255 | rng.getrandbits(255))
        assert a*b>U256
        if i%4==0:
            d=rng.randrange((a*b>>256)+1,2**256)
        elif i%4==1:
            d=rng.randrange(1,max(2,a*b>>256))
        elif i%4==2:
            d=0
        else:
            a,b,d=rng.getrandbits(100),rng.getrandbits(100),rng.randrange(1,2**128)
        q=a*b//d if d else U256+1
        valid=q<=U256
        assert math.mulDiv(a,b,d)==(valid,q if valid else 0)
        key='zero_divisor' if d==0 else 'ordinary' if a*b<=U256 else 'overflow_valid' if valid else 'overflow_invalid'
        counts[key]+=1
    assert all(v==512 for v in counts.values())
    print(f'FUZZ muldiv=2048 strata={counts} seed=0x5121000')


def test_exact_rational_rounding_bounds_in_both_directions(math):
    """On this range, independently prove a one-Q96-unit sqrt bound.

    Squaring propagates that error by (2*s+1)/2**192. The quote floor
    contributes strictly less than one raw unit; inversion divides the
    propagated ratio error by the product of the two positive ratios.
    This is an exact rational bound, not a tolerance for the compiled tests,
    and does not claim that the sqrt bound holds at the extreme ticks.
    """
    from fractions import Fraction
    for tick in (-4096,-100,-1,0,1,100,4096):
        ideal=Fraction(10001,10000)**tick
        sqrt=math.sqrt(tick)
        actual=Fraction(sqrt*sqrt,2**192)
        assert Fraction((sqrt-1)**2,2**192)<ideal<=actual
        bound=Fraction(2*sqrt+1,2**192)
        assert abs(actual-ideal)<bound
        for amount in (1,10**6,10**9,10**18):
            for order in (True,False):
                quote=math.quote(tick,amount,order)
                theoretical=amount*ideal if order else amount/ideal
                error=amount*bound if order else amount*bound/(ideal*actual)
                assert abs(quote-theoretical)<1+error
