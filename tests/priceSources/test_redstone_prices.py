import boa
import pytest

from constants import EIGHTEEN_DECIMALS


CHAINLINK_DECIMALS = 10**8


@pytest.fixture(scope="module")
def mock_redstone_alpha():
    return boa.load(
        "contracts/mock/MockChainlinkFeed.vy",
        500 * EIGHTEEN_DECIMALS,
    )


@pytest.fixture(scope="module")
def mock_redstone_eth():
    return boa.load(
        "contracts/mock/MockChainlinkFeed.vy",
        2_500 * EIGHTEEN_DECIMALS,
    )


def _set_redstone_feed(feed, price, age=0):
    feed.setMockData(
        price,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - age,
    )


def _add_redstone_feed(
    redstone,
    asset,
    feed,
    governance,
    stale_time,
    needs_eth=False,
    refresh_feeds=(),
):
    _set_redstone_feed(feed, 500 * CHAINLINK_DECIMALS)
    assert redstone.addNewPriceFeed(
        asset,
        feed,
        stale_time,
        needs_eth,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=redstone.actionTimeLock() + 1)
    for other_feed, price in refresh_feeds:
        _set_redstone_feed(other_feed, price)
    _set_redstone_feed(feed, 500 * CHAINLINK_DECIMALS)
    assert redstone.confirmNewPriceFeed(asset, sender=governance.address)


def _set_redstone_global_bound(
    switchboard_alpha,
    governance,
    mission_control,
    stale_time=7_200,
):
    action_id = switchboard_alpha.setStaleTime(
        stale_time, sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock() + 1)
    assert switchboard_alpha.executePendingAction(
        action_id, sender=governance.address
    )
    assert mission_control.getPriceStaleTime() == stale_time


@pytest.mark.parametrize(
    "caller_bound,feed_bound,age,expected_valid",
    [
        (0, 0, 100_000, True),
        (20, 0, 21, False),
        (0, 20, 21, False),
        (10, 20, 11, False),
        (20, 10, 11, False),
        (10, 10, 5, True),
        (10, 20, 10, True),
        (10, 20, 11, False),
    ],
)
def test_sc20_redstone_stale_resolver_matrix(
    redstone,
    alpha_token,
    bravo_token,
    mock_redstone_alpha,
    governance,
    caller_bound,
    feed_bound,
    age,
    expected_valid,
):
    assert redstone.getPriceAndHasFeed(bravo_token) == (0, False)
    _add_redstone_feed(
        redstone,
        alpha_token,
        mock_redstone_alpha,
        governance,
        feed_bound,
    )
    _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS, age)

    expected_price = 500 * EIGHTEEN_DECIMALS if expected_valid else 0
    assert redstone.getPrice(alpha_token, caller_bound) == expected_price
    assert redstone.getPriceAndHasFeed(alpha_token, caller_bound) == (
        expected_price,
        True,
    )


def test_sc20_redstone_validation_uses_stricter_candidate_bound(
    redstone,
    alpha_token,
    mock_redstone_alpha,
    mission_control,
    switchboard_alpha,
    governance,
):
    _set_redstone_global_bound(
        switchboard_alpha, governance, mission_control
    )
    _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS, 5_400)
    assert not redstone.isValidNewFeed(
        alpha_token,
        mock_redstone_alpha,
        8,
        False,
        3_600,
    )


def test_sc21_redstone_future_timestamp_characterization(
    redstone,
    alpha_token,
    bravo_token,
    mock_redstone_alpha,
    governance,
):
    assert redstone.getPriceAndHasFeed(bravo_token) == (0, False)
    _add_redstone_feed(
        redstone,
        alpha_token,
        mock_redstone_alpha,
        governance,
        0,
    )
    future_time = boa.env.timestamp + 100
    mock_redstone_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        future_time,
    )
    assert redstone.getPrice(alpha_token, 0) == 0
    assert redstone.getPrice(alpha_token, 1_000) == 0
    assert redstone.getPriceAndHasFeed(alpha_token, 0) == (0, True)
    assert redstone.getPriceAndHasFeed(alpha_token, 1_000) == (0, True)

    _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS)
    assert redstone.getPrice(alpha_token, 1) == 500 * EIGHTEEN_DECIMALS


def test_sc20_redstone_eth_composition_preserved(
    redstone,
    chainlink,
    price_desk,
    alpha_token,
    mock_redstone_alpha,
    mock_redstone_eth,
    governance,
):
    _set_redstone_feed(mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS)
    assert chainlink.addNewPriceFeed(
        redstone.ETH(),
        mock_redstone_eth,
        10,
        False,
        False,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=chainlink.actionTimeLock() + 1)
    _set_redstone_feed(mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS)
    assert chainlink.confirmNewPriceFeed(
        redstone.ETH(), sender=governance.address
    )

    _add_redstone_feed(
        redstone,
        alpha_token,
        mock_redstone_alpha,
        governance,
        10,
        needs_eth=True,
        refresh_feeds=(
            (mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS),
        ),
    )
    expected_price = 500 * 2_500 * EIGHTEEN_DECIMALS
    assert redstone.getPrice(alpha_token, 10, price_desk) == expected_price
