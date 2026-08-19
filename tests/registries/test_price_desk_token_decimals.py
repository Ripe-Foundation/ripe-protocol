import boa

from constants import EIGHTEEN_DECIMALS


ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"

DECIMALS_TOKEN = """
# @version 0.4.3

_decimals: public(uint8)
should_revert: public(bool)
oog: public(bool)
oog_then_valid: public(bool)
malformed_word: public(bool)

@deploy
def __init__(_decimals: uint8):
    self._decimals = _decimals

@external
def setDecimals(_decimals: uint8):
    self._decimals = _decimals

@external
def setShouldRevert(_v: bool):
    self.should_revert = _v

@external
def setOog(_v: bool):
    self.oog = _v

@external
def setOogThenValid(_v: bool):
    self.oog_then_valid = _v

@external
def setMalformedWord(_v: bool):
    self.malformed_word = _v

@view
@external
def decimals() -> uint256:
    if self.should_revert:
        raise "decimals revert"
    if self.oog or self.oog_then_valid:
        s: uint256 = 0
        for i: uint256 in range(10_000):
            s += i
        if self.oog_then_valid:
            return convert(self._decimals, uint256)
        return s
    if self.malformed_word:
        return max_value(uint256)
    return convert(self._decimals, uint256)
"""

# Runtime that RETURN 31 or 33 zero bytes for any call, including decimals().
RET_31_CODE = bytes.fromhex("601f6000f3")
RET_33_CODE = bytes.fromhex("60216000f3")


def _token(decimals):
    return boa.loads(DECIMALS_TOKEN, decimals)


def _price(mock_price_source, token, price=EIGHTEEN_DECIMALS):
    mock_price_source.setPrice(token, price)


def test_price_desk_token_decimals_happy_paths(price_desk, mock_price_source):
    for decimals, amount, price, expected_usd in (
        (0, 5, EIGHTEEN_DECIMALS, 5 * EIGHTEEN_DECIMALS),
        (6, 10**6, EIGHTEEN_DECIMALS, EIGHTEEN_DECIMALS),
        (18, EIGHTEEN_DECIMALS, EIGHTEEN_DECIMALS, EIGHTEEN_DECIMALS),
        # decimals=77, amount=1, price=10**77 proves scale construction and
        # this specific conversion only. It does not prove that every
        # 77-decimal amount/price pair avoids checked multiplication overflow.
        (77, 1, 10**77, 1),
    ):
        token = _token(decimals)
        _price(mock_price_source, token, price)
        assert price_desk.getUsdValue(token, amount, False) == expected_usd
        assert price_desk.getAssetAmount(token, expected_usd, False) == amount


def test_price_desk_checked_mul_overflow_at_77_decimals(price_desk, mock_price_source):
    token = _token(77)
    _price(mock_price_source, token, 10**18)
    with boa.reverts("safemul"):
        price_desk.getUsdValue(token, 10**77, False)
    with boa.reverts("safemul"):
        price_desk.getAssetAmount(token, 10**18, False)


def test_price_desk_rejects_decimals_above_77(price_desk, mock_price_source):
    token = _token(78)
    _price(mock_price_source, token)
    assert price_desk.getUsdValue(token, EIGHTEEN_DECIMALS, False) == 0
    assert price_desk.getAssetAmount(token, EIGHTEEN_DECIMALS, False) == 0
    with boa.reverts("invalid token decimals"):
        price_desk.getUsdValue(token, EIGHTEEN_DECIMALS, True)
    with boa.reverts("invalid token decimals"):
        price_desk.getAssetAmount(token, EIGHTEEN_DECIMALS, True)


def test_price_desk_decimals_revert_oog_and_returndata(
    price_desk,
    mock_price_source,
):
    token = _token(18)
    _price(mock_price_source, token)

    token.setShouldRevert(True)
    assert price_desk.getUsdValue(token, EIGHTEEN_DECIMALS, False) == 0
    with boa.reverts("invalid token decimals"):
        price_desk.getUsdValue(token, EIGHTEEN_DECIMALS, True)
    token.setShouldRevert(False)

    token.setOog(True)
    assert price_desk.getUsdValue(token, EIGHTEEN_DECIMALS, False) == 0
    with boa.reverts("invalid token decimals"):
        price_desk.getUsdValue(token, EIGHTEEN_DECIMALS, True)
    token.setOog(False)

    token.setOogThenValid(True)
    assert price_desk.getUsdValue(token, EIGHTEEN_DECIMALS, False) == 0
    with boa.reverts("invalid token decimals"):
        price_desk.getUsdValue(token, EIGHTEEN_DECIMALS, True)
    token.setOogThenValid(False)

    token.setMalformedWord(True)
    assert price_desk.getUsdValue(token, EIGHTEEN_DECIMALS, False) == 0
    with boa.reverts("invalid token decimals"):
        price_desk.getUsdValue(token, EIGHTEEN_DECIMALS, True)

    short = boa.env.generate_address()
    boa.env.set_code(short, RET_31_CODE)
    _price(mock_price_source, short)
    assert price_desk.getUsdValue(short, EIGHTEEN_DECIMALS, False) == 0
    with boa.reverts("invalid token decimals"):
        price_desk.getAssetAmount(short, EIGHTEEN_DECIMALS, True)

    long = boa.env.generate_address()
    boa.env.set_code(long, RET_33_CODE)
    _price(mock_price_source, long)
    assert price_desk.getUsdValue(long, EIGHTEEN_DECIMALS, False) == 0
    with boa.reverts("invalid token decimals"):
        price_desk.getUsdValue(long, EIGHTEEN_DECIMALS, True)


def test_price_desk_eth_skips_token_decimals_call(price_desk, mock_price_source):
    eth = price_desk.ETH()
    _price(mock_price_source, eth)
    assert price_desk.getUsdValue(eth, EIGHTEEN_DECIMALS, False) == EIGHTEEN_DECIMALS
    assert price_desk.getUsdValue(eth, EIGHTEEN_DECIMALS, True) == EIGHTEEN_DECIMALS
    assert price_desk.getAssetAmount(eth, EIGHTEEN_DECIMALS, False) == EIGHTEEN_DECIMALS
