"""Confirm and price use decimals cached at proposal.

A live decimals() change during the pending timelock does not cancel.
Confirmation admits the cached decimals and can mis-scale immediately.
"""

import boa

from config.BluePrint import ADDYS, PARAMS
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


ONE_DAY_IN_SECS = 60 * 60 * 24


def _desk_params(fork):
    return (
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
    )


def _load_chainlink(ripe_hq, fork):
    min_tl, max_tl = _desk_params(fork)
    return boa.load(
        "contracts/priceSources/ChainlinkPrices.vy",
        ripe_hq,
        ZERO_ADDRESS,
        min_tl,
        max_tl,
        ADDYS[fork]["WETH"],
        ADDYS[fork]["ETH"],
        ADDYS[fork]["BTC"],
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        ONE_DAY_IN_SECS,
        name="cl_cached_decimals",
    )


def _load_redstone(ripe_hq, fork):
    min_tl, max_tl = _desk_params(fork)
    return boa.load(
        "contracts/priceSources/RedStone.vy",
        ripe_hq,
        ZERO_ADDRESS,
        ADDYS[fork]["ETH"],
        min_tl,
        max_tl,
        name="rs_cached_decimals",
    )


def _fresh_round(feed, answer=100_000_000, round_id=1, answered_in_round=1, updated_at=None):
    ts = boa.env.timestamp if updated_at is None else updated_at
    feed.setMockData(answer, round_id, answered_in_round, ts, ts)


def test_chainlink_new_confirm_and_read_use_cached_decimals_after_live_change(
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    feed = boa.load("contracts/mock/MockChainlinkFeed.vy", EIGHTEEN_DECIMALS)
    assert feed.decimals() == 8
    src = _load_chainlink(ripe_hq, fork)
    assert src.setActionTimeLockAfterSetup(sender=governance.address)
    _fresh_round(feed)
    assert src.addNewPriceFeed(
        charlie_token, feed, ONE_DAY_IN_SECS, sender=governance.address
    )
    pending = src.pendingUpdates(charlie_token)
    assert pending.config.decimals == 8

    # Timelock-window drift: confirm admits cached 8, it does not cancel.
    feed.setDecimals(18)
    boa.env.time_travel(blocks=src.actionTimeLock() + 1)
    _fresh_round(feed, 100_000_000)
    assert src.confirmNewPriceFeed(charlie_token, sender=governance.address)
    assert src.hasPriceFeed(charlie_token)
    assert src.feedConfig(charlie_token).decimals == 8
    assert src.getPrice(charlie_token) == EIGHTEEN_DECIMALS
    assert src.getPriceAndHasFeed(charlie_token) == (EIGHTEEN_DECIMALS, True)


def test_chainlink_update_confirm_and_active_read_keep_cached_decimals(
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    feed = boa.load("contracts/mock/MockChainlinkFeed.vy", EIGHTEEN_DECIMALS)
    src = _load_chainlink(ripe_hq, fork)
    assert src.setActionTimeLockAfterSetup(sender=governance.address)
    _fresh_round(feed)
    assert src.addNewPriceFeed(
        charlie_token, feed, ONE_DAY_IN_SECS, sender=governance.address
    )
    boa.env.time_travel(blocks=src.actionTimeLock() + 1)
    _fresh_round(feed)
    assert src.confirmNewPriceFeed(charlie_token, sender=governance.address)

    new_feed = boa.load("contracts/mock/MockChainlinkFeed.vy", EIGHTEEN_DECIMALS)
    _fresh_round(new_feed)
    assert src.updatePriceFeed(
        charlie_token, new_feed, ONE_DAY_IN_SECS, sender=governance.address
    )
    assert src.pendingUpdates(charlie_token).config.decimals == 8
    # Timelock-window drift: confirm admits cached 8, it does not cancel.
    new_feed.setDecimals(6)
    boa.env.time_travel(blocks=src.actionTimeLock() + 1)
    _fresh_round(new_feed, 100_000_000)
    assert src.confirmPriceFeedUpdate(charlie_token, sender=governance.address)
    assert src.feedConfig(charlie_token).feed == new_feed.address
    assert src.feedConfig(charlie_token).decimals == 8
    assert src.getPrice(charlie_token) == EIGHTEEN_DECIMALS

    new_feed.setDecimals(18)
    _fresh_round(new_feed, 100_000_000)
    assert src.getPrice(charlie_token) == EIGHTEEN_DECIMALS
    assert src.getPriceAndHasFeed(charlie_token) == (EIGHTEEN_DECIMALS, True)
    assert src.hasPriceFeed(charlie_token) is True


def test_redstone_new_confirm_and_read_use_cached_decimals_after_live_change(
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    feed = boa.load("contracts/mock/MockChainlinkFeed.vy", EIGHTEEN_DECIMALS)
    src = _load_redstone(ripe_hq, fork)
    assert src.setActionTimeLockAfterSetup(sender=governance.address)
    _fresh_round(feed)
    assert src.addNewPriceFeed(
        charlie_token, feed, ONE_DAY_IN_SECS, sender=governance.address
    )
    assert src.pendingUpdates(charlie_token).config.decimals == 8

    # Timelock-window drift: confirm admits cached 8, it does not cancel.
    feed.setDecimals(18)
    boa.env.time_travel(blocks=src.actionTimeLock() + 1)
    _fresh_round(feed, 100_000_000)
    assert src.confirmNewPriceFeed(charlie_token, sender=governance.address)
    assert src.feedConfig(charlie_token).decimals == 8
    assert src.getPrice(charlie_token) == EIGHTEEN_DECIMALS
    assert src.getPriceAndHasFeed(charlie_token) == (EIGHTEEN_DECIMALS, True)


def test_redstone_update_confirm_and_active_read_keep_cached_decimals(
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    feed = boa.load("contracts/mock/MockChainlinkFeed.vy", EIGHTEEN_DECIMALS)
    src = _load_redstone(ripe_hq, fork)
    assert src.setActionTimeLockAfterSetup(sender=governance.address)
    _fresh_round(feed)
    assert src.addNewPriceFeed(
        charlie_token, feed, ONE_DAY_IN_SECS, sender=governance.address
    )
    boa.env.time_travel(blocks=src.actionTimeLock() + 1)
    _fresh_round(feed)
    assert src.confirmNewPriceFeed(charlie_token, sender=governance.address)

    new_feed = boa.load("contracts/mock/MockChainlinkFeed.vy", EIGHTEEN_DECIMALS)
    _fresh_round(new_feed)
    assert src.updatePriceFeed(
        charlie_token, new_feed, ONE_DAY_IN_SECS, sender=governance.address
    )
    # Timelock-window drift: confirm admits cached 8, it does not cancel.
    new_feed.setDecimals(6)
    boa.env.time_travel(blocks=src.actionTimeLock() + 1)
    _fresh_round(new_feed, 100_000_000)
    assert src.confirmPriceFeedUpdate(charlie_token, sender=governance.address)
    assert src.feedConfig(charlie_token).decimals == 8
    assert src.feedConfig(charlie_token).feed == new_feed.address
    assert src.getPrice(charlie_token) == EIGHTEEN_DECIMALS

    new_feed.setDecimals(18)
    _fresh_round(new_feed, 100_000_000)
    assert src.getPrice(charlie_token) == EIGHTEEN_DECIMALS
    assert src.getPriceAndHasFeed(charlie_token) == (EIGHTEEN_DECIMALS, True)
    assert src.hasPriceFeed(charlie_token) is True


def _confirm_eight_decimal_feed(src, token, feed, governance):
    assert src.setActionTimeLockAfterSetup(sender=governance.address)
    _fresh_round(feed)
    assert src.addNewPriceFeed(
        token, feed, ONE_DAY_IN_SECS, sender=governance.address
    )
    boa.env.time_travel(blocks=src.actionTimeLock() + 1)
    # Timelock-window drift: confirm admits cached 8, it does not cancel.
    feed.setDecimals(18)
    _fresh_round(feed, 100_000_000)
    assert src.confirmNewPriceFeed(token, sender=governance.address)
    assert src.feedConfig(token).decimals == 8
    assert src.getPrice(token) == EIGHTEEN_DECIMALS
    return src


def test_cached_decimals_still_reject_invalid_round_stale_future_zero_negative(
    ripe_hq,
    governance,
    fork,
    charlie_token,
    delta_token,
):
    cl_feed = boa.load("contracts/mock/MockChainlinkFeed.vy", EIGHTEEN_DECIMALS)
    chainlink = _confirm_eight_decimal_feed(
        _load_chainlink(ripe_hq, fork), charlie_token, cl_feed, governance
    )

    rs_feed = boa.load("contracts/mock/MockChainlinkFeed.vy", EIGHTEEN_DECIMALS)
    redstone = _confirm_eight_decimal_feed(
        _load_redstone(ripe_hq, fork), delta_token, rs_feed, governance
    )

    for src, token, feed in (
        (chainlink, charlie_token, cl_feed),
        (redstone, delta_token, rs_feed),
    ):
        feed.setDecimals(6)

        _fresh_round(feed, 100_000_000, round_id=0, answered_in_round=0)
        assert src.getPrice(token) == 0

        _fresh_round(feed, 100_000_000, round_id=2, answered_in_round=1)
        assert src.getPrice(token) == 0

        _fresh_round(feed, 100_000_000)
        boa.env.time_travel(seconds=ONE_DAY_IN_SECS + 1)
        assert src.getPrice(token) == 0

        future = boa.env.timestamp + 100
        feed.setMockData(100_000_000, 1, 1, future, future)
        assert src.getPrice(token) == 0

        _fresh_round(feed, 0)
        assert src.getPrice(token) == 0

        _fresh_round(feed, -1)
        assert src.getPrice(token) == 0

        _fresh_round(feed, 100_000_000)
        assert src.getPrice(token) == EIGHTEEN_DECIMALS
        assert src.hasPriceFeed(token) is True
