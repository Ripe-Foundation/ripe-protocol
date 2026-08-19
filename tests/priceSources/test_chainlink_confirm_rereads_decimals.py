import boa

from config.BluePrint import ADDYS, PARAMS
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


def _desk_params(fork):
    return (
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
    )


def _load_chainlink(ripe_hq, fork):
    min_tl, max_tl = _desk_params(fork)
    src = boa.load(
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
        60 * 60 * 24,
        name="cl_decimals_reread",
    )
    return src


def _load_redstone(ripe_hq, fork):
    min_tl, max_tl = _desk_params(fork)
    src = boa.load(
        "contracts/priceSources/RedStone.vy",
        ripe_hq,
        ZERO_ADDRESS,
        ADDYS[fork]["ETH"],
        min_tl,
        max_tl,
        name="rs_decimals_reread",
    )
    return src


def test_chainlink_confirm_cancels_on_live_decimals_mismatch(
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    feed = boa.load("contracts/mock/MockChainlinkFeed.vy", EIGHTEEN_DECIMALS)
    assert feed.decimals() == 8
    src = _load_chainlink(ripe_hq, fork)
    assert src.setActionTimeLockAfterSetup(sender=governance.address)
    assert src.addNewPriceFeed(charlie_token, feed, sender=governance.address)
    pending = src.pendingUpdates(charlie_token)
    assert pending.config.decimals == 8

    feed.setDecimals(18)
    feed.setMockData(EIGHTEEN_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    boa.env.time_travel(blocks=src.actionTimeLock() + 1)
    feed.setMockData(EIGHTEEN_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert not src.confirmNewPriceFeed(charlie_token, sender=governance.address)
    assert not src.hasPriceFeed(charlie_token)
    assert not src.hasPendingPriceFeedUpdate(charlie_token)


def test_chainlink_update_confirm_cancels_on_decimals_mismatch(
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    feed = boa.load("contracts/mock/MockChainlinkFeed.vy", EIGHTEEN_DECIMALS)
    src = _load_chainlink(ripe_hq, fork)
    assert src.setActionTimeLockAfterSetup(sender=governance.address)
    assert src.addNewPriceFeed(charlie_token, feed, sender=governance.address)
    boa.env.time_travel(blocks=src.actionTimeLock() + 1)
    feed.setMockData(100_000_000, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert src.confirmNewPriceFeed(charlie_token, sender=governance.address)

    new_feed = boa.load("contracts/mock/MockChainlinkFeed.vy", EIGHTEEN_DECIMALS)
    assert src.updatePriceFeed(charlie_token, new_feed, sender=governance.address)
    new_feed.setDecimals(18)
    boa.env.time_travel(blocks=src.actionTimeLock() + 1)
    new_feed.setMockData(EIGHTEEN_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert not src.confirmPriceFeedUpdate(charlie_token, sender=governance.address)
    assert src.feedConfig(charlie_token).feed == feed.address
    assert src.feedConfig(charlie_token).decimals == 8


def test_chainlink_live_decimals_change_prices_zero(
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    feed = boa.load("contracts/mock/MockChainlinkFeed.vy", EIGHTEEN_DECIMALS)
    src = _load_chainlink(ripe_hq, fork)
    assert src.setActionTimeLockAfterSetup(sender=governance.address)
    assert src.addNewPriceFeed(charlie_token, feed, sender=governance.address)
    boa.env.time_travel(blocks=src.actionTimeLock() + 1)
    feed.setMockData(100_000_000, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert src.confirmNewPriceFeed(charlie_token, sender=governance.address)
    assert src.getPrice(charlie_token) != 0

    feed.setDecimals(18)
    assert src.getPrice(charlie_token) == 0
    assert src.getPriceAndHasFeed(charlie_token) == (0, True)
    assert src.hasPriceFeed(charlie_token) is True


def test_redstone_confirm_cancels_on_live_decimals_mismatch(
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    feed = boa.load("contracts/mock/MockChainlinkFeed.vy", EIGHTEEN_DECIMALS)
    src = _load_redstone(ripe_hq, fork)
    assert src.setActionTimeLockAfterSetup(sender=governance.address)
    assert src.addNewPriceFeed(charlie_token, feed, sender=governance.address)
    feed.setDecimals(18)
    boa.env.time_travel(blocks=src.actionTimeLock() + 1)
    feed.setMockData(EIGHTEEN_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert not src.confirmNewPriceFeed(charlie_token, sender=governance.address)
    assert not src.hasPriceFeed(charlie_token)


def test_redstone_update_confirm_and_live_decimals_change(
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    feed = boa.load("contracts/mock/MockChainlinkFeed.vy", EIGHTEEN_DECIMALS)
    src = _load_redstone(ripe_hq, fork)
    assert src.setActionTimeLockAfterSetup(sender=governance.address)
    assert src.addNewPriceFeed(charlie_token, feed, sender=governance.address)
    boa.env.time_travel(blocks=src.actionTimeLock() + 1)
    feed.setMockData(100_000_000, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert src.confirmNewPriceFeed(charlie_token, sender=governance.address)

    new_feed = boa.load("contracts/mock/MockChainlinkFeed.vy", EIGHTEEN_DECIMALS)
    assert src.updatePriceFeed(charlie_token, new_feed, sender=governance.address)
    new_feed.setDecimals(6)
    boa.env.time_travel(blocks=src.actionTimeLock() + 1)
    new_feed.setMockData(100_000_000, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert not src.confirmPriceFeedUpdate(charlie_token, sender=governance.address)
    assert src.feedConfig(charlie_token).decimals == 8
    assert src.feedConfig(charlie_token).feed == feed.address

    feed.setMockData(100_000_000, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert src.getPrice(charlie_token) != 0
    feed.setDecimals(18)
    assert src.getPrice(charlie_token) == 0
    assert src.getPriceAndHasFeed(charlie_token) == (0, True)
    assert src.hasPriceFeed(charlie_token) is True
