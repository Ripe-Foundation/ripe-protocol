import boa
import pytest

from constants import EIGHTEEN_DECIMALS
from config.BluePrint import ADDYS, CORE_TOKENS


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
    with boa.env.anchor():
        _set_redstone_global_bound(
            switchboard_alpha, governance, mission_control
        )
        _set_redstone_feed(
            mock_redstone_alpha, 500 * CHAINLINK_DECIMALS, 5_400
        )
        assert redstone.isValidNewFeed(
            alpha_token,
            mock_redstone_alpha,
            8,
            False,
            7_200,
        )
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


def test_redstone_eth_leg_uses_resolved_stale_on_pricedesk(
    redstone,
    chainlink,
    price_desk,
    alpha_token,
    mock_redstone_alpha,
    mock_redstone_eth,
    governance,
    switchboard_alpha,
    mission_control,
):
    with boa.env.anchor():
        _set_redstone_global_bound(
            switchboard_alpha,
            governance,
            mission_control,
            stale_time=7_200,
        )
        eth = redstone.ETH()
        _set_redstone_feed(mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS)
        assert chainlink.addNewPriceFeed(
            eth,
            mock_redstone_eth,
            0,
            False,
            False,
            sender=governance.address,
        )
        boa.env.time_travel(blocks=chainlink.actionTimeLock() + 1)
        _set_redstone_feed(mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS)
        assert chainlink.confirmNewPriceFeed(eth, sender=governance.address)

        _add_redstone_feed(
            redstone,
            alpha_token,
            mock_redstone_alpha,
            governance,
            10,
            needs_eth=True,
            refresh_feeds=((mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS),),
        )

        _set_redstone_feed(mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS, age=50)
        _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS)

        assert price_desk.getPrice(eth) == 2_500 * EIGHTEEN_DECIMALS
        assert price_desk.getPrice(eth, False) == 2_500 * EIGHTEEN_DECIMALS
        assert price_desk.getPrice(eth, False, 10) == 0
        with boa.reverts("has price config, no price"):
            redstone.getPrice(alpha_token, 0, price_desk)
        with boa.reverts("has price config, no price"):
            redstone.getPrice(alpha_token, 10, price_desk)


def _advance_timelock_blocks(blocks):
    """Advance governance NUMBER without aging historical fork oracles."""

    boa.env.evm.patch.block_number += blocks


def _load_aggregator(addr, name):
    return boa.from_etherscan(addr, name=name)


def _normalized_aggregator_price(feed):
    rnd = feed.latestRoundData()
    answer = int(getattr(rnd, "answer", rnd[1]))
    decimals = int(feed.decimals())
    assert answer > 0
    assert decimals <= 18
    price = answer
    if decimals < 18:
        price *= 10 ** (18 - decimals)
    return price, decimals


def _assert_redstone_config(config, feed, decimals, stale_time, needs_eth=False):
    assert config.feed == feed
    assert config.decimals == decimals
    assert config.needsEthToUsd is needs_eth
    assert config.staleTime == stale_time


@pytest.base
def test_base_redstone_generic_aggregator_sol_propose_confirm_and_pricedesk(
    redstone,
    chainlink,
    price_desk,
    governance,
    fork,
):
    # Real Base AggregatorV3 mechanics via the repository-configured SOL feed.
    # This is not a RedStone-provider feed.
    asset = CORE_TOKENS[fork]["USOL"]
    feed_addr = ADDYS[fork]["CHAINLINK_SOL_USD"]
    feed = _load_aggregator(feed_addr, "chainlink_sol_usd")
    expected_price, expected_decimals = _normalized_aggregator_price(feed)

    assert not redstone.hasPriceFeed(asset)
    assert not chainlink.hasPriceFeed(asset)
    assert price_desk.getPrice(asset) == 0
    assert redstone.addNewPriceFeed(asset, feed_addr, 0, False, sender=governance.address)
    pending = redstone.pendingUpdates(asset).config
    _assert_redstone_config(pending, feed_addr, expected_decimals, 0, False)
    _advance_timelock_blocks(redstone.actionTimeLock() + 1)
    assert redstone.confirmNewPriceFeed(asset, sender=governance.address)

    stored = redstone.feedConfig(asset)
    _assert_redstone_config(
        stored,
        pending.feed,
        pending.decimals,
        pending.staleTime,
        pending.needsEthToUsd,
    )
    assert stored.decimals == expected_decimals
    assert redstone.getPrice(asset) == expected_price
    assert redstone.getPriceAndHasFeed(asset) == (expected_price, True)
    assert redstone.getPrice(asset, 0, price_desk.address) == expected_price
    assert price_desk.getPrice(asset) == expected_price


@pytest.base
def test_base_redstone_needs_eth_to_usd_three_arg_pricedesk_path(
    redstone,
    chainlink,
    price_desk,
    governance,
    fork,
):
    # Prove generic AggregatorV3 * ETH/USD conversion. The DOGE feed is a
    # repository-configured Chainlink aggregator, not a RedStone provider.
    asset = CORE_TOKENS[fork]["CBDOGE"]
    feed_addr = ADDYS[fork]["CHAINLINK_DOGE_USD"]
    feed = _load_aggregator(feed_addr, "chainlink_doge_usd")
    doge_usd, expected_decimals = _normalized_aggregator_price(feed)
    eth = ADDYS[fork]["ETH"]
    eth_usd = chainlink.getPrice(eth)
    assert eth_usd != 0
    expected = doge_usd * eth_usd // EIGHTEEN_DECIMALS
    assert expected != 0

    # No other source registers this asset; the asserts below prove it.
    assert not redstone.hasPriceFeed(asset)
    assert not chainlink.hasPriceFeed(asset)
    assert price_desk.getPrice(asset) == 0
    assert redstone.addNewPriceFeed(asset, feed_addr, 0, True, sender=governance.address)
    pending = redstone.pendingUpdates(asset).config
    _assert_redstone_config(pending, feed_addr, expected_decimals, 0, True)
    _advance_timelock_blocks(redstone.actionTimeLock() + 1)
    assert redstone.confirmNewPriceFeed(asset, sender=governance.address)

    stored = redstone.feedConfig(asset)
    _assert_redstone_config(
        stored,
        pending.feed,
        pending.decimals,
        pending.staleTime,
        pending.needsEthToUsd,
    )
    assert stored.needsEthToUsd is True
    assert redstone.getPrice(asset, 0, price_desk.address) == expected
    assert price_desk.getPrice(asset) == expected
