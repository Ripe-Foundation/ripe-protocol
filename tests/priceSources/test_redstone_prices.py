import boa
import pytest

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, ONE_DAY_IN_SECS, ZERO_ADDRESS
from config.BluePrint import ADDYS, CORE_TOKENS


CHAINLINK_DECIMALS = 10**8
MAX_FEED_STALE_TIME = 7 * ONE_DAY_IN_SECS
MIN_LOCAL_STALE_TIME = 5 * 60

CUSTOM_PRICE_DESK = """
# @version 0.4.3

price: immutable(uint256)

@deploy
def __init__(_price: uint256):
    price = _price

@view
@external
def getPrice(_asset: address, _shouldRaise: bool = False) -> uint256:
    return price
"""


@pytest.fixture(autouse=True)
def valid_global_stale_time(setGeneralConfig):
    """Local defaults are zero; source tests exercise zero as global inheritance."""

    setGeneralConfig(_priceStaleTime=ONE_DAY_IN_SECS)


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


def _add_chainlink_eth_feed(
    chainlink,
    redstone,
    feed,
    governance,
    stale_time=600,
):
    _set_redstone_feed(feed, 2_500 * CHAINLINK_DECIMALS)
    assert chainlink.addNewPriceFeed(
        redstone.ETH(),
        feed,
        stale_time,
        False,
        False,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=chainlink.actionTimeLock() + 1)
    _set_redstone_feed(feed, 2_500 * CHAINLINK_DECIMALS)
    assert chainlink.confirmNewPriceFeed(
        redstone.ETH(), sender=governance.address
    )


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
    "global_bound,feed_bound,age,expected_valid",
    [
        (7_200, 0, 5_400, True),
        (3_600, 0, 5_400, False),
        (3_600, 7_200, 5_400, True),
        (7_200, 3_600, 5_400, False),
        (7_200, 3_600, 3_600, True),
        (3_600, 7_200, 7_201, False),
    ],
)
def test_redstone_global_default_and_exact_feed_override_matrix(
    redstone,
    alpha_token,
    bravo_token,
    mock_redstone_alpha,
    governance,
    mission_control,
    switchboard_alpha,
    global_bound,
    feed_bound,
    age,
    expected_valid,
):
    assert redstone.getPriceAndHasFeed(bravo_token) == (0, False)
    _set_redstone_global_bound(
        switchboard_alpha, governance, mission_control, global_bound
    )
    _add_redstone_feed(
        redstone,
        alpha_token,
        mock_redstone_alpha,
        governance,
        feed_bound,
    )
    _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS, age)

    expected_price = 500 * EIGHTEEN_DECIMALS if expected_valid else 0
    assert redstone.getPrice(alpha_token) == expected_price
    assert redstone.getPriceAndHasFeed(alpha_token) == (
        expected_price,
        True,
    )


def test_redstone_omitted_add_and_update_stale_time_inherit_global(
    redstone,
    alpha_token,
    mock_redstone_alpha,
    mock_redstone_eth,
    governance,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _set_redstone_feed(
            mock_redstone_alpha, 500 * CHAINLINK_DECIMALS
        )
        assert redstone.addNewPriceFeed(
            alpha_token,
            mock_redstone_alpha,
            sender=governance.address,
        )
        assert redstone.pendingUpdates(alpha_token).config.staleTime == 0

        boa.env.time_travel(blocks=redstone.actionTimeLock() + 1)
        _set_redstone_feed(
            mock_redstone_alpha, 500 * CHAINLINK_DECIMALS
        )
        assert redstone.confirmNewPriceFeed(
            alpha_token, sender=governance.address
        )
        assert redstone.feedConfig(alpha_token).staleTime == 0

        _set_redstone_feed(
            mock_redstone_eth, 1_000 * CHAINLINK_DECIMALS
        )
        assert redstone.updatePriceFeed(
            alpha_token,
            mock_redstone_eth,
            sender=governance.address,
        )
        assert redstone.pendingUpdates(alpha_token).config.staleTime == 0

        boa.env.time_travel(blocks=redstone.actionTimeLock() + 1)
        _set_redstone_feed(
            mock_redstone_eth, 1_000 * CHAINLINK_DECIMALS
        )
        assert redstone.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert redstone.feedConfig(alpha_token).feed == mock_redstone_eth.address
        assert redstone.feedConfig(alpha_token).staleTime == 0

        _set_redstone_feed(
            mock_redstone_eth, 1_000 * CHAINLINK_DECIMALS, age=100
        )
        assert redstone.getPrice(alpha_token) == 1_000 * EIGHTEEN_DECIMALS
        _set_redstone_feed(
            mock_redstone_eth, 1_000 * CHAINLINK_DECIMALS, age=101
        )
        assert redstone.getPrice(alpha_token) == 0


def test_redstone_nonzero_global_requires_canonical_pricedesk_forwarding(
    redstone,
    alpha_token,
    bravo_token,
    mock_redstone_alpha,
    governance,
    mission_control,
    switchboard_alpha,
    price_desk,
):
    _set_redstone_global_bound(
        switchboard_alpha, governance, mission_control, 7_200
    )
    _add_redstone_feed(
        redstone,
        alpha_token,
        mock_redstone_alpha,
        governance,
        0,
    )
    _set_redstone_feed(
        mock_redstone_alpha, 500 * CHAINLINK_DECIMALS, age=100
    )
    expected = 500 * EIGHTEEN_DECIMALS

    assert redstone.getPrice(alpha_token, 300) == 0
    assert redstone.getPrice(alpha_token, 300, price_desk.address) == 0
    assert redstone.getPrice(
        alpha_token, 300, ZERO_ADDRESS, sender=price_desk.address
    ) == 0
    assert redstone.getPriceAndHasFeed(alpha_token, 300) == (0, True)
    assert redstone.getPriceAndHasFeed(bravo_token, 300) == (0, False)

    assert redstone.getPrice(
        alpha_token,
        300,
        price_desk.address,
        sender=price_desk.address,
    ) == expected
    assert redstone.getPriceAndHasFeed(
        alpha_token,
        300,
        price_desk.address,
        sender=price_desk.address,
    ) == (expected, True)

    _set_redstone_feed(
        mock_redstone_alpha, 500 * CHAINLINK_DECIMALS, age=301
    )
    assert redstone.getPrice(
        alpha_token,
        300,
        price_desk.address,
        sender=price_desk.address,
    ) == 0


def test_redstone_exact_override_ignores_invalid_global_policy(
    redstone,
    price_desk,
    alpha_token,
    mock_redstone_alpha,
    governance,
    setGeneralConfig,
):
    _add_redstone_feed(
        redstone,
        alpha_token,
        mock_redstone_alpha,
        governance,
        300,
    )
    _set_redstone_feed(
        mock_redstone_alpha, 500 * CHAINLINK_DECIMALS, age=200
    )
    expected = 500 * EIGHTEEN_DECIMALS

    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        assert redstone.getPrice(alpha_token) == expected
        assert price_desk.getPrice(alpha_token) == expected

    for invalid_global in (0, MAX_FEED_STALE_TIME + 1):
        with boa.env.anchor():
            setGeneralConfig(_priceStaleTime=invalid_global)
            assert redstone.getPrice(alpha_token) == expected
            assert redstone.getPriceAndHasFeed(alpha_token) == (
                expected,
                True,
            )
            assert price_desk.getPrice(alpha_token) == expected


def test_redstone_candidate_validation_uses_exact_feed_override(
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
    assert redstone.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS


def test_redstone_eth_composition_preserved(
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
        MIN_LOCAL_STALE_TIME,
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
        MIN_LOCAL_STALE_TIME,
        needs_eth=True,
        refresh_feeds=(
            (mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS),
        ),
    )
    expected_price = 500 * 2_500 * EIGHTEEN_DECIMALS
    assert redstone.getPrice(alpha_token, 0, price_desk) == expected_price
    assert price_desk.getPrice(alpha_token) == expected_price


def test_redstone_stale_time_update_preserves_active_eth_route(
    redstone,
    chainlink,
    price_desk,
    alpha_token,
    mock_redstone_alpha,
    mock_redstone_eth,
    governance,
):
    eth = redstone.ETH()
    _set_redstone_feed(mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS)
    assert chainlink.addNewPriceFeed(
        eth,
        mock_redstone_eth,
        600,
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
        600,
        needs_eth=True,
        refresh_feeds=((mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS),),
    )
    before = redstone.feedConfig(alpha_token)
    expected = 500 * 2_500 * EIGHTEEN_DECIMALS
    assert redstone.getPrice(alpha_token, 0, price_desk) == expected
    assert price_desk.getPrice(alpha_token) == expected

    assert redstone.isValidStaleTimeUpdate(alpha_token, 300)
    assert redstone.updateStaleTime(
        alpha_token, 300, sender=governance.address
    )
    boa.env.time_travel(blocks=redstone.actionTimeLock() + 1)
    _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS)
    _set_redstone_feed(mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS)
    assert redstone.confirmPriceFeedUpdate(
        alpha_token, sender=governance.address
    )

    after = redstone.feedConfig(alpha_token)
    assert after.feed == before.feed
    assert after.decimals == before.decimals
    assert after.needsEthToUsd is before.needsEthToUsd
    assert after.staleTime == 300
    assert redstone.pendingUpdates(alpha_token).actionId == 0
    assert redstone.getPrice(alpha_token, 0, price_desk) == expected
    assert price_desk.getPrice(alpha_token) == expected


def test_redstone_eth_leg_uses_pricedesk_global_independently(
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
            MIN_LOCAL_STALE_TIME,
            needs_eth=True,
            refresh_feeds=((mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS),),
        )

        _set_redstone_feed(mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS, age=50)
        _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS)

        assert price_desk.getPrice(eth) == 2_500 * EIGHTEEN_DECIMALS
        assert price_desk.getPrice(eth, False) == 2_500 * EIGHTEEN_DECIMALS
        assert price_desk.getPrice(eth, False, 10) == 0
        expected = 500 * 2_500 * EIGHTEEN_DECIMALS
        assert redstone.getPrice(alpha_token, 0, price_desk) == expected
        assert redstone.getPrice(alpha_token, 10, price_desk) == 0


def test_redstone_stale_time_update_lifecycle_and_validator_parity(
    redstone,
    alpha_token,
    bravo_token,
    mock_redstone_alpha,
    governance,
    bob,
    switchboard_alpha,
):
    assert not redstone.hasPriceFeed(bravo_token)
    assert not redstone.isValidStaleTimeUpdate(bravo_token, 3_600)
    with boa.reverts("invalid feed"):
        redstone.updateStaleTime(
            bravo_token, 3_600, sender=governance.address
        )
    assert redstone.pendingUpdates(bravo_token).actionId == 0

    _add_redstone_feed(
        redstone,
        alpha_token,
        mock_redstone_alpha,
        governance,
        7_200,
    )
    current = redstone.feedConfig(alpha_token)

    with boa.reverts("no perms"):
        redstone.updateStaleTime(alpha_token, 3_600, sender=bob)

    redstone.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        redstone.updateStaleTime(
            alpha_token, 3_600, sender=governance.address
        )
    redstone.pause(False, sender=switchboard_alpha.address)

    assert not redstone.isValidUpdateFeed(
        alpha_token,
        current.feed,
        current.decimals,
        current.needsEthToUsd,
        3_600,
    )
    with boa.reverts("invalid feed"):
        redstone.updatePriceFeed(
            alpha_token,
            current.feed,
            3_600,
            current.needsEthToUsd,
            sender=governance.address,
        )

    for candidate, expected_valid in (
        (0, True),
        (3_600, True),
        (7_200, False),
        (MAX_FEED_STALE_TIME + 1, False),
    ):
        assert (
            redstone.isValidStaleTimeUpdate(alpha_token, candidate)
            is expected_valid
        )
        with boa.env.anchor():
            if expected_valid:
                assert redstone.updateStaleTime(
                    alpha_token, candidate, sender=governance.address
                )
            else:
                with boa.reverts("invalid feed"):
                    redstone.updateStaleTime(
                        alpha_token, candidate, sender=governance.address
                    )

    assert redstone.updateStaleTime(
        alpha_token, 3_600, sender=governance.address
    )
    pending = redstone.pendingUpdates(alpha_token)
    assert pending.actionId != 0
    assert pending.config.feed == current.feed
    assert pending.config.decimals == current.decimals
    assert pending.config.needsEthToUsd is current.needsEthToUsd
    assert pending.config.staleTime == 3_600

    with boa.reverts("time lock not reached"):
        redstone.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
    boa.env.time_travel(blocks=redstone.actionTimeLock() + 1)
    _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS)
    assert redstone.confirmPriceFeedUpdate(
        alpha_token, sender=governance.address
    )
    stored = redstone.feedConfig(alpha_token)
    assert stored.feed == current.feed
    assert stored.decimals == current.decimals
    assert stored.needsEthToUsd is current.needsEthToUsd
    assert stored.staleTime == 3_600
    assert redstone.pendingUpdates(alpha_token).actionId == 0

    assert redstone.updateStaleTime(
        alpha_token, 0, sender=governance.address
    )
    boa.env.time_travel(blocks=redstone.actionTimeLock() + 1)
    _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS)
    assert redstone.confirmPriceFeedUpdate(
        alpha_token, sender=governance.address
    )
    assert redstone.feedConfig(alpha_token).staleTime == 0

    assert redstone.updateStaleTime(
        alpha_token, 7_200, sender=governance.address
    )
    assert redstone.cancelPriceFeedUpdate(
        alpha_token, sender=governance.address
    )
    assert redstone.feedConfig(alpha_token).staleTime == 0
    assert redstone.pendingUpdates(alpha_token).actionId == 0
    with boa.reverts("no pending update feed"):
        redstone.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )

    _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS)
    assert redstone.updateStaleTime(
        alpha_token, 300, sender=governance.address
    )
    boa.env.time_travel(blocks=redstone.actionTimeLock() + 1)
    _set_redstone_feed(
        mock_redstone_alpha, 500 * CHAINLINK_DECIMALS, age=301
    )
    assert not redstone.confirmPriceFeedUpdate(
        alpha_token, sender=governance.address
    )
    retry_pending = redstone.pendingUpdates(alpha_token)
    assert retry_pending.actionId != 0
    assert retry_pending.config.staleTime == MIN_LOCAL_STALE_TIME
    assert redstone.feedConfig(alpha_token).staleTime == 0

    _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS)
    assert redstone.confirmPriceFeedUpdate(
        alpha_token, sender=governance.address
    )
    assert redstone.feedConfig(alpha_token).staleTime == MIN_LOCAL_STALE_TIME
    assert redstone.pendingUpdates(alpha_token).actionId == 0


@pytest.mark.parametrize("invalid_global", [0, MAX_FEED_STALE_TIME + 1])
@pytest.mark.parametrize(
    "candidate_stale_time,should_confirm",
    [(0, False), (MAX_FEED_STALE_TIME, True)],
)
def test_redstone_stale_time_confirmation_revalidates_live_global_policy(
    redstone,
    alpha_token,
    mock_redstone_alpha,
    governance,
    setGeneralConfig,
    invalid_global,
    candidate_stale_time,
    should_confirm,
):
    _add_redstone_feed(
        redstone,
        alpha_token,
        mock_redstone_alpha,
        governance,
        600,
    )
    before = redstone.feedConfig(alpha_token)
    expected = 500 * EIGHTEEN_DECIMALS
    assert redstone.getPrice(alpha_token) == expected
    assert redstone.isValidStaleTimeUpdate(
        alpha_token, candidate_stale_time
    )
    assert redstone.updateStaleTime(
        alpha_token, candidate_stale_time, sender=governance.address
    )

    boa.env.time_travel(blocks=redstone.actionTimeLock() + 1)
    _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS)
    setGeneralConfig(_priceStaleTime=invalid_global)
    assert (
        redstone.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        is should_confirm
    )

    after = redstone.feedConfig(alpha_token)
    assert after.feed == before.feed
    assert after.decimals == before.decimals
    assert after.needsEthToUsd is before.needsEthToUsd
    assert after.staleTime == (
        candidate_stale_time if should_confirm else before.staleTime
    )
    pending = redstone.pendingUpdates(alpha_token)
    if should_confirm:
        assert pending.actionId == 0
    else:
        assert pending.actionId != 0
        assert pending.config.feed == before.feed
        assert pending.config.staleTime == candidate_stale_time
    assert redstone.getPrice(alpha_token) == expected


def _start_redstone_pending_action(
    kind,
    source,
    asset,
    primary_feed,
    alternate_feed,
    governance,
):
    _set_redstone_feed(primary_feed, 500 * CHAINLINK_DECIMALS)
    if kind == "add":
        assert source.addNewPriceFeed(
            asset,
            primary_feed,
            MIN_LOCAL_STALE_TIME,
            sender=governance.address,
        )
        return

    _add_redstone_feed(
        source,
        asset,
        primary_feed,
        governance,
        MIN_LOCAL_STALE_TIME,
    )
    _set_redstone_feed(alternate_feed, 1_000 * CHAINLINK_DECIMALS)
    if kind == "update":
        assert source.updatePriceFeed(
            asset,
            alternate_feed,
            MIN_LOCAL_STALE_TIME,
            sender=governance.address,
        )
    elif kind == "stale":
        assert source.updateStaleTime(
            asset, 600, sender=governance.address
        )
    else:
        assert kind == "disable"
        assert source.disablePriceFeed(asset, sender=governance.address)


def _redstone_pending_state(source, asset):
    pending = source.pendingUpdates(asset)
    return (
        pending.actionId,
        pending.config.feed,
        pending.config.decimals,
        pending.config.needsEthToUsd,
        pending.config.staleTime,
    )


def _redstone_active_state(source, asset):
    active = source.feedConfig(asset)
    return (
        source.hasPriceFeed(asset),
        active.feed,
        active.decimals,
        active.needsEthToUsd,
        active.staleTime,
    )


def _redstone_action_state(source, asset):
    return (
        source.hasPendingPriceFeedUpdate(asset),
        _redstone_pending_state(source, asset),
        _redstone_active_state(source, asset),
    )


def _redstone_wrong_action_selectors(pending_kind):
    if pending_kind == "add":
        return (
            ("no pending update feed", "confirmPriceFeedUpdate"),
            ("no pending update feed", "cancelPriceFeedUpdate"),
            ("no pending disable feed", "confirmDisablePriceFeed"),
            ("no pending disable feed", "cancelDisablePriceFeed"),
        )
    if pending_kind in ("update", "stale"):
        return (
            ("no pending new feed", "confirmNewPriceFeed"),
            ("no pending new feed", "cancelNewPendingPriceFeed"),
            ("no pending disable feed", "confirmDisablePriceFeed"),
            ("no pending disable feed", "cancelDisablePriceFeed"),
        )
    assert pending_kind == "disable"
    return (
        ("no pending new feed", "confirmNewPriceFeed"),
        ("no pending new feed", "cancelNewPendingPriceFeed"),
        ("no pending update feed", "confirmPriceFeedUpdate"),
        ("no pending update feed", "cancelPriceFeedUpdate"),
    )


@pytest.mark.parametrize("pending_kind", ["add", "update", "stale", "disable"])
def test_redstone_pending_action_collisions_and_cleanup(
    redstone,
    alpha_token,
    mock_redstone_alpha,
    mock_redstone_eth,
    governance,
    pending_kind,
):
    _start_redstone_pending_action(
        pending_kind,
        redstone,
        alpha_token,
        mock_redstone_alpha,
        mock_redstone_eth,
        governance,
    )
    before = _redstone_action_state(redstone, alpha_token)

    initiators = (
        lambda: redstone.addNewPriceFeed(
            alpha_token,
            mock_redstone_alpha,
            MIN_LOCAL_STALE_TIME,
            sender=governance.address,
        ),
        lambda: redstone.updatePriceFeed(
            alpha_token,
            mock_redstone_eth,
            MIN_LOCAL_STALE_TIME,
            sender=governance.address,
        ),
        lambda: redstone.updateStaleTime(
            alpha_token, 300, sender=governance.address
        ),
        lambda: redstone.disablePriceFeed(
            alpha_token, sender=governance.address
        ),
    )
    for initiate in initiators:
        with boa.reverts("pending feed action"):
            initiate()
        assert _redstone_action_state(redstone, alpha_token) == before

    for reason, selector in _redstone_wrong_action_selectors(pending_kind):
        with boa.reverts(reason):
            getattr(redstone, selector)(
                alpha_token, sender=governance.address
            )
        assert _redstone_action_state(redstone, alpha_token) == before

    active_before = _redstone_active_state(redstone, alpha_token)
    if pending_kind == "add":
        assert redstone.cancelNewPendingPriceFeed(
            alpha_token, sender=governance.address
        )
    elif pending_kind in ("update", "stale"):
        assert redstone.cancelPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
    else:
        assert redstone.cancelDisablePriceFeed(
            alpha_token, sender=governance.address
        )
    assert not redstone.hasPendingPriceFeedUpdate(alpha_token)
    assert _redstone_active_state(redstone, alpha_token) == active_before


@pytest.mark.parametrize("pending_kind", ["add", "update", "stale", "disable"])
def test_redstone_expired_pending_action_requires_explicit_cleanup(
    redstone,
    alpha_token,
    mock_redstone_alpha,
    mock_redstone_eth,
    governance,
    pending_kind,
):
    with boa.env.anchor():
        _start_redstone_pending_action(
            pending_kind,
            redstone,
            alpha_token,
            mock_redstone_alpha,
            mock_redstone_eth,
            governance,
        )
        before = _redstone_pending_state(redstone, alpha_token)
        _advance_timelock_blocks(
            redstone.actionTimeLock() + redstone.expiration()
        )
        assert redstone.hasPendingPriceFeedUpdate(alpha_token)

        with boa.reverts("pending feed action"):
            redstone.updateStaleTime(
                alpha_token, 300, sender=governance.address
            )
        assert _redstone_pending_state(redstone, alpha_token) == before

        if pending_kind == "add":
            assert redstone.cancelNewPendingPriceFeed(
                alpha_token, sender=governance.address
            )
            assert redstone.addNewPriceFeed(
                alpha_token,
                mock_redstone_alpha,
                MIN_LOCAL_STALE_TIME,
                sender=governance.address,
            )
        elif pending_kind in ("update", "stale"):
            assert redstone.cancelPriceFeedUpdate(
                alpha_token, sender=governance.address
            )
            assert redstone.updateStaleTime(
                alpha_token, 600, sender=governance.address
            )
        else:
            assert redstone.cancelDisablePriceFeed(
                alpha_token, sender=governance.address
            )
            assert redstone.disablePriceFeed(
                alpha_token, sender=governance.address
            )

        after = _redstone_pending_state(redstone, alpha_token)
        assert after[0] != 0
        assert after[0] != before[0]


def test_redstone_invalid_effective_stale_policies_fail_closed(
    redstone,
    alpha_token,
    bravo_token,
    mock_redstone_alpha,
    mock_redstone_eth,
    governance,
    setGeneralConfig,
    price_desk,
    ripe_hq,
):
    _add_redstone_feed(
        redstone,
        alpha_token,
        mock_redstone_alpha,
        governance,
        0,
    )
    _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS)
    _set_redstone_feed(mock_redstone_eth, 1_000 * CHAINLINK_DECIMALS)
    assert redstone.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS
    assert not redstone.isValidNewFeed(
        bravo_token,
        mock_redstone_eth,
        8,
        False,
        MAX_FEED_STALE_TIME + 1,
    )
    assert not redstone.isValidStaleTimeUpdate(
        alpha_token, MAX_FEED_STALE_TIME + 1
    )

    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=0)
        assert redstone.getPrice(alpha_token) == 0
        assert redstone.getPriceAndHasFeed(alpha_token) == (0, True)

    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=MAX_FEED_STALE_TIME + 1)
        assert redstone.getPrice(alpha_token) == 0
        assert redstone.getPriceAndHasFeed(alpha_token) == (0, True)

    with boa.env.anchor():
        ripe_hq.eval("registry.addrInfo[5].addr = empty(address)")
        assert ripe_hq.getAddr(5) == ZERO_ADDRESS
        assert redstone.getPrice(alpha_token) == 0
        assert redstone.getPriceAndHasFeed(alpha_token) == (0, True)

    assert redstone.getPrice(
        alpha_token,
        MAX_FEED_STALE_TIME + 1,
        price_desk.address,
        sender=price_desk.address,
    ) == 0

    for invalid_local in (MIN_LOCAL_STALE_TIME - 1, MAX_FEED_STALE_TIME + 1):
        with boa.env.anchor():
            redstone.eval(
                f"self.feedConfig[{alpha_token.address}].staleTime = "
                f"{invalid_local}"
            )
            assert redstone.getPrice(alpha_token) == 0
            assert redstone.getPriceAndHasFeed(alpha_token) == (0, True)


def test_redstone_conversion_safety_and_custom_pricedesk_boundaries(
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
        3_600,
        False,
        False,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=chainlink.actionTimeLock() + 1)
    _set_redstone_feed(mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS)
    assert chainlink.confirmNewPriceFeed(
        redstone.ETH(), sender=governance.address
    )

    assert not redstone.isValidNewFeed(
        redstone.ETH(),
        mock_redstone_alpha,
        8,
        True,
        3_600,
    )
    _add_redstone_feed(
        redstone,
        redstone.ETH(),
        mock_redstone_eth,
        governance,
        3_600,
        refresh_feeds=((mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS),),
    )
    _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS)
    _set_redstone_feed(mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS)

    assert not redstone.isValidNewFeed(
        alpha_token,
        mock_redstone_eth,
        8,
        True,
        3_600,
    )
    assert redstone.isValidNewFeed(
        alpha_token,
        mock_redstone_alpha,
        8,
        True,
        3_600,
    )
    _add_redstone_feed(
        redstone,
        alpha_token,
        mock_redstone_alpha,
        governance,
        3_600,
        needs_eth=True,
        refresh_feeds=((mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS),),
    )
    _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS)
    _set_redstone_feed(mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS)

    canonical_expected = 500 * 2_500 * EIGHTEEN_DECIMALS
    assert redstone.getPrice(alpha_token) == canonical_expected
    assert redstone.getPrice(alpha_token, 0, ZERO_ADDRESS) == canonical_expected

    custom = boa.loads(
        CUSTOM_PRICE_DESK,
        1_234 * EIGHTEEN_DECIMALS,
        name="custom_redstone_price_desk",
    )
    assert redstone.getPrice(alpha_token, 0, custom.address) == (
        500 * 1_234 * EIGHTEEN_DECIMALS
    )
    assert redstone.getPriceAndHasFeed(
        alpha_token, 0, custom.address
    ) == (500 * 1_234 * EIGHTEEN_DECIMALS, True)

    assert redstone.getPrice(
        alpha_token,
        300,
        custom.address,
        sender=custom.address,
    ) == 0
    assert redstone.getPrice(
        alpha_token,
        300,
        custom.address,
        sender=price_desk.address,
    ) == 0
    assert redstone.getPrice(
        alpha_token,
        300,
        price_desk.address,
        sender=price_desk.address,
    ) == canonical_expected

    with boa.env.anchor():
        redstone.eval(
            f"self.feedConfig[{alpha_token.address}].feed = "
            f"{mock_redstone_eth.address}"
        )
        assert redstone.getPrice(alpha_token) == 0

    with boa.env.anchor():
        redstone.eval(
            f"self.feedConfig[{redstone.ETH()}].needsEthToUsd = True"
        )
        assert redstone.getPrice(redstone.ETH()) == 0
        assert redstone.getPrice(alpha_token) == 0


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


@pytest.mark.parametrize("explicit_zero", [False, True])
def test_redstone_feed_rotation_zero_preserves_active_stale_policy(
    redstone,
    alpha_token,
    mock_redstone_alpha,
    mock_redstone_eth,
    governance,
    explicit_zero,
):
    with boa.env.anchor():
        _add_redstone_feed(
            redstone,
            alpha_token,
            mock_redstone_alpha,
            governance,
            3_600,
        )
        _set_redstone_feed(
            mock_redstone_eth, 1_000 * CHAINLINK_DECIMALS
        )

        assert redstone.isValidUpdateFeed(
            alpha_token,
            mock_redstone_eth,
            8,
            False,
            0,
        )
        if explicit_zero:
            assert redstone.updatePriceFeed(
                alpha_token,
                mock_redstone_eth,
                0,
                sender=governance.address,
            )
        else:
            assert redstone.updatePriceFeed(
                alpha_token,
                mock_redstone_eth,
                sender=governance.address,
            )
        pending_log = filter_logs(
            redstone, "RedStoneFeedUpdatePending"
        )[0]
        pending = redstone.pendingUpdates(alpha_token)
        assert pending.config.staleTime == 3_600
        assert pending_log.staleTime == 3_600

        _advance_timelock_blocks(redstone.actionTimeLock() + 1)
        _set_redstone_feed(
            mock_redstone_eth, 1_000 * CHAINLINK_DECIMALS
        )
        assert redstone.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        updated_log = filter_logs(redstone, "RedStoneFeedUpdated")[0]
        stored = redstone.feedConfig(alpha_token)
        assert stored.feed == mock_redstone_eth.address
        assert stored.staleTime == 3_600
        assert updated_log.staleTime == 3_600


@pytest.mark.parametrize(
    "candidate,is_valid",
    [
        (MIN_LOCAL_STALE_TIME - 1, False),
        (MIN_LOCAL_STALE_TIME, True),
        (MAX_FEED_STALE_TIME, True),
        (MAX_FEED_STALE_TIME + 1, False),
    ],
)
def test_redstone_local_stale_bounds_cover_feed_lifecycles(
    redstone,
    alpha_token,
    mock_redstone_alpha,
    mock_redstone_eth,
    governance,
    candidate,
    is_valid,
):
    with boa.env.anchor():
        _set_redstone_feed(
            mock_redstone_alpha, 500 * CHAINLINK_DECIMALS
        )
        assert redstone.isValidNewFeed(
            alpha_token,
            mock_redstone_alpha,
            8,
            False,
            candidate,
        ) is is_valid
        if is_valid:
            assert redstone.addNewPriceFeed(
                alpha_token,
                mock_redstone_alpha,
                candidate,
                sender=governance.address,
            )
            assert (
                redstone.pendingUpdates(alpha_token).config.staleTime
                == candidate
            )
            _advance_timelock_blocks(redstone.actionTimeLock() + 1)
            _set_redstone_feed(
                mock_redstone_alpha, 500 * CHAINLINK_DECIMALS
            )
            assert redstone.confirmNewPriceFeed(
                alpha_token, sender=governance.address
            )
        else:
            with boa.reverts("invalid feed"):
                redstone.addNewPriceFeed(
                    alpha_token,
                    mock_redstone_alpha,
                    candidate,
                    sender=governance.address,
                )

    with boa.env.anchor():
        _add_redstone_feed(
            redstone,
            alpha_token,
            mock_redstone_alpha,
            governance,
            600,
        )
        _set_redstone_feed(
            mock_redstone_eth, 1_000 * CHAINLINK_DECIMALS
        )
        assert redstone.isValidUpdateFeed(
            alpha_token,
            mock_redstone_eth,
            8,
            False,
            candidate,
        ) is is_valid
        if is_valid:
            assert redstone.updatePriceFeed(
                alpha_token,
                mock_redstone_eth,
                candidate,
                sender=governance.address,
            )
            _advance_timelock_blocks(redstone.actionTimeLock() + 1)
            _set_redstone_feed(
                mock_redstone_eth, 1_000 * CHAINLINK_DECIMALS
            )
            assert redstone.confirmPriceFeedUpdate(
                alpha_token, sender=governance.address
            )
            assert redstone.feedConfig(alpha_token).staleTime == candidate
        else:
            with boa.reverts("invalid feed"):
                redstone.updatePriceFeed(
                    alpha_token,
                    mock_redstone_eth,
                    candidate,
                    sender=governance.address,
                )

    with boa.env.anchor():
        _add_redstone_feed(
            redstone,
            alpha_token,
            mock_redstone_alpha,
            governance,
            600,
        )
        assert redstone.isValidStaleTimeUpdate(
            alpha_token, candidate
        ) is is_valid
        if is_valid:
            assert redstone.updateStaleTime(
                alpha_token, candidate, sender=governance.address
            )
            _advance_timelock_blocks(redstone.actionTimeLock() + 1)
            _set_redstone_feed(
                mock_redstone_alpha, 500 * CHAINLINK_DECIMALS
            )
            assert redstone.confirmPriceFeedUpdate(
                alpha_token, sender=governance.address
            )
            assert redstone.feedConfig(alpha_token).staleTime == candidate
        else:
            with boa.reverts("invalid feed"):
                redstone.updateStaleTime(
                    alpha_token, candidate, sender=governance.address
                )


def test_redstone_paused_source_keeps_pricing_but_freezes_pending_actions(
    redstone,
    alpha_token,
    mock_redstone_alpha,
    governance,
    switchboard_alpha,
):
    with boa.env.anchor():
        _add_redstone_feed(
            redstone,
            alpha_token,
            mock_redstone_alpha,
            governance,
            600,
        )
        assert redstone.updateStaleTime(
            alpha_token,
            MIN_LOCAL_STALE_TIME,
            sender=governance.address,
        )
        _advance_timelock_blocks(redstone.actionTimeLock() + 1)
        _set_redstone_feed(
            mock_redstone_alpha, 500 * CHAINLINK_DECIMALS
        )

        redstone.pause(True, sender=switchboard_alpha.address)
        assert redstone.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS
        with boa.reverts("contract paused"):
            redstone.updateStaleTime(
                alpha_token, 1_200, sender=governance.address
            )
        with boa.reverts("contract paused"):
            redstone.confirmPriceFeedUpdate(
                alpha_token, sender=governance.address
            )
        with boa.reverts("contract paused"):
            redstone.cancelPriceFeedUpdate(
                alpha_token, sender=governance.address
            )

        redstone.pause(False, sender=switchboard_alpha.address)
        assert redstone.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert redstone.updateStaleTime(
            alpha_token, 600, sender=governance.address
        )
        redstone.pause(True, sender=switchboard_alpha.address)
        with boa.reverts("contract paused"):
            redstone.cancelPriceFeedUpdate(
                alpha_token, sender=governance.address
            )
        redstone.pause(False, sender=switchboard_alpha.address)
        assert redstone.cancelPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert redstone.pendingUpdates(alpha_token).actionId == 0


def test_redstone_failed_stale_confirmation_can_cancel_after_expiry(
    redstone,
    alpha_token,
    mock_redstone_alpha,
    governance,
):
    with boa.env.anchor():
        _add_redstone_feed(
            redstone,
            alpha_token,
            mock_redstone_alpha,
            governance,
            600,
        )
        assert redstone.updateStaleTime(
            alpha_token,
            MIN_LOCAL_STALE_TIME,
            sender=governance.address,
        )
        _advance_timelock_blocks(redstone.actionTimeLock() + 1)
        _set_redstone_feed(
            mock_redstone_alpha,
            500 * CHAINLINK_DECIMALS,
            age=MIN_LOCAL_STALE_TIME + 1,
        )
        assert not redstone.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        action_id = redstone.pendingUpdates(alpha_token).actionId
        assert action_id != 0

        _advance_timelock_blocks(redstone.expiration())
        assert redstone.pendingUpdates(alpha_token).actionId == action_id
        assert redstone.cancelPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert redstone.pendingUpdates(alpha_token).actionId == 0


def test_redstone_converting_stale_confirmation_retries_after_eth_anchor_recovers(
    redstone,
    chainlink,
    price_desk,
    alpha_token,
    mock_redstone_alpha,
    mock_redstone_eth,
    governance,
):
    with boa.env.anchor():
        _add_chainlink_eth_feed(
            chainlink,
            redstone,
            mock_redstone_eth,
            governance,
        )
        _add_redstone_feed(
            redstone,
            alpha_token,
            mock_redstone_alpha,
            governance,
            600,
            needs_eth=True,
            refresh_feeds=(
                (mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS),
            ),
        )
        assert redstone.updateStaleTime(
            alpha_token,
            MIN_LOCAL_STALE_TIME,
            sender=governance.address,
        )
        action_id = redstone.pendingUpdates(alpha_token).actionId
        assert action_id != 0
        pending_before = _redstone_pending_state(redstone, alpha_token)
        active_before = _redstone_active_state(redstone, alpha_token)

        _advance_timelock_blocks(redstone.actionTimeLock() + 1)
        _set_redstone_feed(mock_redstone_alpha, 500 * CHAINLINK_DECIMALS)
        _set_redstone_feed(
            mock_redstone_eth,
            2_500 * CHAINLINK_DECIMALS,
            age=601,
        )
        assert price_desk.getPrice(redstone.ETH()) == 0

        assert not redstone.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert _redstone_pending_state(
            redstone, alpha_token
        ) == pending_before
        assert _redstone_active_state(redstone, alpha_token) == active_before
        assert redstone.hasPendingAction(action_id)

        _set_redstone_feed(mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS)
        assert redstone.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert redstone.feedConfig(alpha_token).staleTime == MIN_LOCAL_STALE_TIME
        assert redstone.pendingUpdates(alpha_token).actionId == 0
        assert not redstone.hasPendingAction(action_id)


def test_redstone_failed_feed_replacement_confirmation_auto_cancels(
    redstone,
    alpha_token,
    mock_redstone_alpha,
    mock_redstone_eth,
    governance,
):
    with boa.env.anchor():
        _add_redstone_feed(
            redstone,
            alpha_token,
            mock_redstone_alpha,
            governance,
            600,
        )
        active = redstone.feedConfig(alpha_token)
        _set_redstone_feed(
            mock_redstone_eth, 1_000 * CHAINLINK_DECIMALS
        )
        assert redstone.updatePriceFeed(
            alpha_token,
            mock_redstone_eth,
            600,
            sender=governance.address,
        )
        action_id = redstone.pendingUpdates(alpha_token).actionId
        assert action_id != 0
        _advance_timelock_blocks(redstone.actionTimeLock() + 1)
        _set_redstone_feed(mock_redstone_eth, 0)

        assert not redstone.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert redstone.pendingUpdates(alpha_token).actionId == 0
        assert not redstone.hasPendingAction(action_id)
        assert redstone.feedConfig(alpha_token).feed == active.feed
        assert redstone.feedConfig(alpha_token).staleTime == active.staleTime


def test_redstone_converting_replacement_auto_cancels_when_eth_anchor_is_unhealthy(
    redstone,
    chainlink,
    price_desk,
    alpha_token,
    mock_redstone_alpha,
    mock_redstone_eth,
    governance,
):
    with boa.env.anchor():
        _add_chainlink_eth_feed(
            chainlink,
            redstone,
            mock_redstone_eth,
            governance,
        )
        _add_redstone_feed(
            redstone,
            alpha_token,
            mock_redstone_alpha,
            governance,
            600,
            needs_eth=True,
            refresh_feeds=(
                (mock_redstone_eth, 2_500 * CHAINLINK_DECIMALS),
            ),
        )
        empty_pending = _redstone_pending_state(redstone, alpha_token)
        active_before = _redstone_active_state(redstone, alpha_token)
        replacement = boa.load(
            "contracts/mock/MockChainlinkFeed.vy",
            500 * EIGHTEEN_DECIMALS,
        )
        _set_redstone_feed(replacement, 1_000 * CHAINLINK_DECIMALS)
        assert redstone.updatePriceFeed(
            alpha_token,
            replacement,
            600,
            True,
            sender=governance.address,
        )
        action_id = redstone.pendingUpdates(alpha_token).actionId
        assert action_id != 0

        _advance_timelock_blocks(redstone.actionTimeLock() + 1)
        _set_redstone_feed(replacement, 1_000 * CHAINLINK_DECIMALS)
        _set_redstone_feed(
            mock_redstone_eth,
            2_500 * CHAINLINK_DECIMALS,
            age=601,
        )
        assert price_desk.getPrice(redstone.ETH()) == 0

        assert not redstone.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert _redstone_pending_state(
            redstone, alpha_token
        ) == empty_pending
        assert not redstone.hasPendingAction(action_id)
        assert _redstone_active_state(redstone, alpha_token) == active_before
