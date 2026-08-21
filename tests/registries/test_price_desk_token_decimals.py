import boa
import pytest

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"

DECIMALS_TOKEN = """
# @version 0.4.3

_decimals: public(uint8)
should_revert: public(bool)

@deploy
def __init__(_decimals: uint8):
    self._decimals = _decimals

@external
def setDecimals(_decimals: uint8):
    self._decimals = _decimals

@external
def setShouldRevert(_v: bool):
    self.should_revert = _v

@view
@external
def decimals() -> uint8:
    if self.should_revert:
        raise "decimals revert"
    return self._decimals
"""

MALFORMED_DECIMALS_TOKEN = """
# @version 0.4.3

@view
@external
def decimals() -> uint256:
    return max_value(uint256)
"""

REVERTING_PRICE_SOURCE = """
# @version 0.4.3

@view
@external
def getPriceAndHasFeed(
    _asset: address,
    _staleTime: uint256 = 0,
    _priceDesk: address = empty(address),
) -> (uint256, bool):
    raise "price source boom"
"""


def _token(decimals):
    return boa.loads(DECIMALS_TOKEN, decimals)


def _price(mock_price_source, token, price=EIGHTEEN_DECIMALS):
    mock_price_source.setPrice(token, price)


def _feed(mock_price_source, token):
    mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)


def test_anyone_can_sync_when_feed_exists(price_desk, bob, mock_price_source):
    token = _token(8)
    with boa.reverts("no price feed"):
        price_desk.syncTokenScale(token, sender=bob)
    _feed(mock_price_source, token)
    price_desk.syncTokenScale(token, sender=bob)
    logs = filter_logs(price_desk, "TokenScaleSet")
    assert logs[-1].asset == token.address
    assert logs[-1].decimals == 8
    assert logs[-1].scale == 10**8
    assert price_desk.tokenScale(token) == 10**8


def test_sync_is_first_set_only(price_desk, bob, mock_price_source):
    token = _token(8)
    _feed(mock_price_source, token)
    price_desk.syncTokenScale(token, sender=bob)
    token.setDecimals(18)
    with boa.reverts("already set"):
        price_desk.syncTokenScale(token, sender=bob)
    assert price_desk.tokenScale(token) == 10**8


def test_gov_and_switchboard_can_sync_without_feed_and_overwrite(
    price_desk,
    governance,
    switchboard_bravo,
    bob,
    mock_price_source,
):
    token = _token(8)
    price_desk.syncTokenScale(token, sender=governance.address)
    assert price_desk.tokenScale(token) == 10**8
    token.setDecimals(6)
    price_desk.syncTokenScale(token, sender=switchboard_bravo.address)
    logs = filter_logs(price_desk, "TokenScaleSet")
    assert logs[-1].decimals == 6
    assert logs[-1].scale == 10**6
    assert price_desk.tokenScale(token) == 10**6
    _feed(mock_price_source, token)
    with boa.reverts("already set"):
        price_desk.syncTokenScale(token, sender=bob)
    assert price_desk.tokenScale(token) == 10**6


def test_paused_price_desk_still_allows_sync(
    price_desk,
    switchboard_alpha,
    governance,
    bob,
    mock_price_source,
):
    token = _token(18)
    _feed(mock_price_source, token)
    price_desk.pause(True, sender=switchboard_alpha.address)
    price_desk.syncTokenScale(token, sender=bob)
    assert price_desk.tokenScale(token) == EIGHTEEN_DECIMALS
    token.setDecimals(8)
    price_desk.syncTokenScale(token, sender=governance.address)
    assert price_desk.tokenScale(token) == 10**8


def test_missing_scale_returns_zero_or_reverts(price_desk, mock_price_source):
    token = _token(18)
    _price(mock_price_source, token)
    assert price_desk.getUsdValue(token, EIGHTEEN_DECIMALS, False) == 0
    assert price_desk.getAssetAmount(token, EIGHTEEN_DECIMALS, False) == 0
    with boa.reverts("missing token scale"):
        price_desk.getUsdValue(token, EIGHTEEN_DECIMALS, True)
    with boa.reverts("missing token scale"):
        price_desk.getAssetAmount(token, EIGHTEEN_DECIMALS, True)


def test_missing_scale_is_resolved_before_reverting_price_source(
    ripe_hq,
    deploy3r,
    mission_control,
    switchboard_alpha,
    setGeneralConfig,
):
    token = _token(18)
    source = boa.loads(REVERTING_PRICE_SOURCE)
    desk = boa.load(
        "contracts/registries/PriceDesk.vy",
        ripe_hq,
        deploy3r,
        ETH,
        1,
        2,
        name="missing_scale_before_price",
    )
    assert desk.startAddNewAddressToRegistry(source, "reverting", sender=deploy3r)
    assert desk.confirmNewAddressToRegistry(source, sender=deploy3r) == 1
    mission_control.setPriorityPriceSourceIds([1], sender=switchboard_alpha.address)
    setGeneralConfig()
    with boa.reverts("missing token scale"):
        desk.getUsdValue(token, EIGHTEEN_DECIMALS, True)
    with boa.reverts("missing token scale"):
        desk.getAssetAmount(token, EIGHTEEN_DECIMALS, True)


def test_zero_decimals_stores_one(price_desk, bob, mock_price_source):
    token = _token(0)
    _feed(mock_price_source, token)
    price_desk.syncTokenScale(token, sender=bob)
    assert price_desk.tokenScale(token) == 1
    _price(mock_price_source, token)
    assert price_desk.getUsdValue(token, 5, False) == 5 * EIGHTEEN_DECIMALS
    assert price_desk.getAssetAmount(token, 5 * EIGHTEEN_DECIMALS, False) == 5


def test_decimals_77_succeeds_and_78_reverts(price_desk, governance, bob, mock_price_source):
    token_77 = _token(77)
    _feed(mock_price_source, token_77)
    price_desk.syncTokenScale(token_77, sender=bob)
    assert price_desk.tokenScale(token_77) == 10**77

    token_78 = _token(78)
    _feed(mock_price_source, token_78)
    with boa.reverts("invalid token decimals"):
        price_desk.syncTokenScale(token_78, sender=bob)
    assert price_desk.tokenScale(token_78) == 0
    with boa.reverts("invalid token decimals"):
        price_desk.syncTokenScale(token_78, sender=governance.address)
    assert price_desk.tokenScale(token_78) == 0


def test_reverting_or_malformed_decimals_does_not_write(price_desk, bob, mock_price_source):
    token = _token(18)
    token.setShouldRevert(True)
    _feed(mock_price_source, token)
    with boa.reverts("decimals revert"):
        price_desk.syncTokenScale(token, sender=bob)
    assert price_desk.tokenScale(token) == 0

    malformed = boa.loads(MALFORMED_DECIMALS_TOKEN)
    _feed(mock_price_source, malformed)
    with boa.reverts():
        price_desk.syncTokenScale(malformed, sender=bob)
    assert price_desk.tokenScale(malformed) == 0


def test_gov_cannot_write_when_decimals_reverts(price_desk, governance):
    token = _token(8)
    token.setShouldRevert(True)
    with boa.reverts("decimals revert"):
        price_desk.syncTokenScale(token, sender=governance.address)
    assert price_desk.tokenScale(token) == 0


def test_eth_uses_1e18_without_storage(price_desk, mock_price_source, governance, bob):
    eth = price_desk.ETH()
    assert price_desk.tokenScale(eth) == 0
    with boa.reverts("invalid asset"):
        price_desk.syncTokenScale(eth, sender=bob)
    with boa.reverts("invalid asset"):
        price_desk.syncTokenScale(eth, sender=governance.address)
    assert price_desk.tokenScale(eth) == 0
    _price(mock_price_source, eth)
    assert price_desk.getUsdValue(eth, EIGHTEEN_DECIMALS, False) == EIGHTEEN_DECIMALS
    assert price_desk.getUsdValue(eth, EIGHTEEN_DECIMALS, True) == EIGHTEEN_DECIMALS
    assert price_desk.getAssetAmount(eth, EIGHTEEN_DECIMALS, False) == EIGHTEEN_DECIMALS


def test_eight_decimal_amount_and_price_yield_one_usd(
    price_desk,
    bob,
    mock_price_source,
):
    token = _token(8)
    _feed(mock_price_source, token)
    price_desk.syncTokenScale(token, sender=bob)
    _price(mock_price_source, token, EIGHTEEN_DECIMALS)
    assert price_desk.getUsdValue(token, 10**8, False) == EIGHTEEN_DECIMALS
    assert price_desk.getAssetAmount(token, EIGHTEEN_DECIMALS, False) == 10**8


def test_decimal_drift_does_not_change_cached_scale(
    price_desk,
    governance,
    bob,
    mock_price_source,
):
    token = _token(8)
    _feed(mock_price_source, token)
    price_desk.syncTokenScale(token, sender=bob)
    assert price_desk.getUsdValue(token, 10**8, False) == EIGHTEEN_DECIMALS
    token.setDecimals(18)
    assert price_desk.tokenScale(token) == 10**8
    assert price_desk.getUsdValue(token, 10**8, False) == EIGHTEEN_DECIMALS
    with boa.reverts("already set"):
        price_desk.syncTokenScale(token, sender=bob)
    price_desk.syncTokenScale(token, sender=governance.address)
    assert price_desk.tokenScale(token) == EIGHTEEN_DECIMALS
    assert price_desk.getUsdValue(token, 10**8, False) == 10**8


def test_explicit_set_restores_empty_or_redeployed_desk(
    ripe_hq,
    deploy3r,
    mock_price_source,
    mission_control,
    switchboard_alpha,
    setGeneralConfig,
):
    token = _token(6)
    desk = boa.load(
        "contracts/registries/PriceDesk.vy",
        ripe_hq,
        deploy3r,
        ETH,
        1,
        2,
        name="redeployed_price_desk",
    )
    assert desk.tokenScale(token) == 0
    desk.syncTokenScale(token, sender=deploy3r)
    assert desk.tokenScale(token) == 10**6
    _price(mock_price_source, token)
    assert desk.startAddNewAddressToRegistry(mock_price_source, "mock", sender=deploy3r)
    assert desk.confirmNewAddressToRegistry(mock_price_source, sender=deploy3r) == 1
    mission_control.setPriorityPriceSourceIds([1], sender=switchboard_alpha.address)
    setGeneralConfig()
    assert desk.getUsdValue(token, 10**6, False) == EIGHTEEN_DECIMALS


def test_gov_overwrite_blocks_later_public_sync(price_desk, governance, bob, mock_price_source):
    token = _token(8)
    price_desk.syncTokenScale(token, sender=governance.address)
    first = filter_logs(price_desk, "TokenScaleSet")[-1]
    assert first.scale == 10**8
    token.setDecimals(18)
    price_desk.syncTokenScale(token, sender=governance.address)
    second = filter_logs(price_desk, "TokenScaleSet")[-1]
    assert second.decimals == 18
    assert second.scale == EIGHTEEN_DECIMALS
    _feed(mock_price_source, token)
    with boa.reverts("already set"):
        price_desk.syncTokenScale(token, sender=bob)
    assert price_desk.tokenScale(token) == EIGHTEEN_DECIMALS


def test_sync_rejects_empty_address(price_desk, governance, bob):
    with boa.reverts("invalid asset"):
        price_desk.syncTokenScale(ZERO_ADDRESS, sender=bob)
    with boa.reverts("invalid asset"):
        price_desk.syncTokenScale(ZERO_ADDRESS, sender=governance.address)


def test_checked_mul_overflow_at_77_decimals(price_desk, bob, mock_price_source):
    token = _token(77)
    _feed(mock_price_source, token)
    price_desk.syncTokenScale(token, sender=bob)
    _price(mock_price_source, token, 10**18)
    with boa.reverts("safemul"):
        price_desk.getUsdValue(token, 10**77, False)
    with boa.reverts("safemul"):
        price_desk.getAssetAmount(token, 10**18, False)


def test_zero_amount_and_zero_address_early_returns(price_desk, bob, mock_price_source):
    token = _token(18)
    _feed(mock_price_source, token)
    price_desk.syncTokenScale(token, sender=bob)
    _price(mock_price_source, token)
    assert price_desk.getUsdValue(token, 0, True) == 0
    assert price_desk.getAssetAmount(token, 0, True) == 0
    assert price_desk.getUsdValue(ZERO_ADDRESS, EIGHTEEN_DECIMALS, True) == 0
    assert price_desk.getAssetAmount(ZERO_ADDRESS, EIGHTEEN_DECIMALS, True) == 0
