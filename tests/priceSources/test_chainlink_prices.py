import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, ONE_YEAR, ONE_DAY_IN_SECS
from conf_utils import filter_logs
from config.BluePrint import PARAMS, ADDYS, CORE_TOKENS


@pytest.fixture(scope="module")
def mock_chainlink_alpha():
    return boa.load(
        "contracts/mock/MockChainlinkFeed.vy",
        500 * EIGHTEEN_DECIMALS,  # $500
    )


@pytest.fixture(scope="module")
def mock_chainlink_bravo():
    return boa.load(
        "contracts/mock/MockChainlinkFeed.vy",
        2_500 * EIGHTEEN_DECIMALS,  # ETH, 18 decimals, $2500
    )


@pytest.fixture(scope="module")
def mock_chainlink_charlie():
    return boa.load(
        "contracts/mock/MockChainlinkFeed.vy",
        EIGHTEEN_DECIMALS,  # USDC, 6 decimals, $1
    )


@pytest.fixture(scope="module")
def mock_chainlink_delta():
    return boa.load(
        "contracts/mock/MockChainlinkFeed.vy",
        50_000 * EIGHTEEN_DECIMALS,  # WBTC, 8 decimals, $50,000
    )


@pytest.fixture(scope="module")
def mock_chainlink(ripe_hq, fork):
    CHAINLINK_ETH_USD = ZERO_ADDRESS if fork == "local" else ADDYS[fork]["CHAINLINK_ETH_USD"]
    CHAINLINK_BTC_USD = ZERO_ADDRESS if fork == "local" else ADDYS[fork]["CHAINLINK_BTC_USD"]
    ONE_DAY_IN_SECS = 60 * 60 * 24
    c = boa.load(
        "contracts/priceSources/ChainlinkPrices.vy",
        ripe_hq,
        ZERO_ADDRESS,
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
        ADDYS[fork]["WETH"],
        ADDYS[fork]["ETH"],
        ADDYS[fork]["BTC"],
        CHAINLINK_ETH_USD,
        CHAINLINK_BTC_USD,
        ONE_DAY_IN_SECS,
        name="chainlink",
    )
    assert c.setActionTimeLockAfterSetup(sender=ripe_hq.governance())
    return c


CHAINLINK_DECIMALS = 10 ** 8
MAX_FEED_STALE_TIME = 7 * ONE_DAY_IN_SECS
MIN_LOCAL_STALE_TIME = 5 * 60


@pytest.fixture(autouse=True)
def valid_global_stale_time(setGeneralConfig):
    """Local defaults are zero; source tests exercise zero as global inheritance."""

    setGeneralConfig(_priceStaleTime=ONE_DAY_IN_SECS)

# tests


def test_chainlink_add_price_feed(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    governance,
    bob,
):
    # Test unauthorized access
    with boa.reverts("no perms"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=bob)

    # Test adding invalid feed (zero address)
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, ZERO_ADDRESS, sender=governance.address)

    # Test adding feed with invalid price
    mock_chainlink_alpha.setMockData(0)  # Set price to 0
    assert mock_chainlink_alpha.latestRoundData().answer == 0
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Reset mock data with current timestamp
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)

    # Test successful feed addition
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "NewChainlinkFeedPending")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_alpha.address
    assert log.staleTime == 0
    assert not log.needsEthToUsd
    assert not log.needsBtcToUsd

    # Test confirming before time lock
    with boa.reverts("time lock not reached"):
        mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Travel past time lock
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)

    # Refresh timestamp after time travel
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)

    # Test confirming
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "NewChainlinkFeedAdded")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_alpha.address
    assert log.staleTime == 0
    assert not log.needsEthToUsd
    assert not log.needsBtcToUsd

    # Verify feed is active
    assert mock_chainlink.hasPriceFeed(alpha_token)
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS

    # Test canceling non-existent feed
    with boa.reverts("no pending new feed"):
        mock_chainlink.cancelNewPendingPriceFeed(alpha_token, sender=governance.address)

    # Test adding feed for existing asset
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)


def test_chainlink_add_price_feed_cancel(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    governance,
):
    # Set up mock with current timestamp
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)

    # Add feed
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "NewChainlinkFeedPending")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_alpha.address
    assert log.staleTime == 0
    assert not log.needsEthToUsd
    assert not log.needsBtcToUsd

    # Cancel feed
    assert mock_chainlink.cancelNewPendingPriceFeed(alpha_token, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "NewChainlinkFeedCancelled")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_alpha.address

    # Verify feed is not active
    assert not mock_chainlink.hasPriceFeed(alpha_token)
    assert mock_chainlink.getPrice(alpha_token) == 0

    # Test confirming after cancel
    with boa.reverts("no pending new feed"):
        mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)


def test_chainlink_add_price_feed_eth_btc_conversion(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,  # ETH feed
    mock_chainlink_charlie,  # BTC-denominated primary feed
    mock_chainlink_delta,  # BTC feed
    governance,
):
    # Set up mocks with current timestamp
    mock_chainlink_bravo.setMockData(2500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)

    # Add ETH feed first
    assert mock_chainlink.addNewPriceFeed(mock_chainlink.ETH(), mock_chainlink_bravo, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_bravo.setMockData(2500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(mock_chainlink.ETH(), sender=governance.address)

    # Set up alpha mock with current timestamp
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)

    # Add feed with ETH conversion (explicit staleTime=0)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, 0, True, False, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "NewChainlinkFeedPending")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_alpha.address
    assert log.staleTime == 0
    assert log.needsEthToUsd
    assert not log.needsBtcToUsd

    # Confirm feed
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    mock_chainlink_bravo.setMockData(2500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Verify price with ETH conversion
    # mock_chainlink_alpha price: 500 * CHAINLINK_DECIMALS
    # mock_chainlink_bravo price: 2500 * CHAINLINK_DECIMALS
    expected_price = 500 * 2500 * EIGHTEEN_DECIMALS
    assert mock_chainlink.getPrice(alpha_token) == expected_price

    # Add BTC feed
    mock_chainlink_delta.setMockData(50000 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.addNewPriceFeed(mock_chainlink.BTC(), mock_chainlink_delta, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_delta.setMockData(50000 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(mock_chainlink.BTC(), sender=governance.address)

    # Update to a distinct BTC-denominated feed. Reusing the BTC/USD anchor as
    # the primary feed is rejected by the conversion-route guard.
    mock_chainlink_charlie.setMockData(
        500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp
    )
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_charlie, 0, False, True, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "ChainlinkFeedUpdatePending")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_charlie.address
    assert log.staleTime == 0
    assert not log.needsEthToUsd
    assert log.needsBtcToUsd

    # Confirm update
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_charlie.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    mock_chainlink_delta.setMockData(50000 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    # Verify price with BTC conversion
    # mock_chainlink_charlie price: 500 * CHAINLINK_DECIMALS
    # mock_chainlink_delta price: 50000 * CHAINLINK_DECIMALS
    expected_price = 500 * 50000 * EIGHTEEN_DECIMALS
    assert mock_chainlink.getPrice(alpha_token) == expected_price

    # Test invalid conversion (both ETH and BTC)
    with boa.reverts("invalid feed"):
        mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_alpha, 0, True, True, sender=governance.address)


def test_chainlink_update_price_feed(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
    bob,
):
    # Add initial feed with current timestamp
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test unauthorized access
    with boa.reverts("no perms"):
        mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=bob)

    # Test updating with same feed
    with boa.reverts("invalid feed"):
        mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Test updating with zero address
    with boa.reverts("invalid feed"):
        mock_chainlink.updatePriceFeed(alpha_token, ZERO_ADDRESS, sender=governance.address)

    # Test updating with invalid price
    mock_chainlink_bravo.setMockData(0)  # Set price to 0
    with boa.reverts("invalid feed"):
        mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)

    # Reset mock data with current timestamp
    mock_chainlink_bravo.setMockData(1000 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)

    # Test successful update
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "ChainlinkFeedUpdatePending")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_bravo.address
    assert log.staleTime == 0
    assert not log.needsEthToUsd
    assert not log.needsBtcToUsd

    # Test confirming before time lock
    with boa.reverts("time lock not reached"):
        mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    # Travel past time lock
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)

    # Refresh timestamp after time travel
    mock_chainlink_bravo.setMockData(1000 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)

    # Test confirming
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "ChainlinkFeedUpdated")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_bravo.address
    assert log.staleTime == 0
    assert not log.needsEthToUsd
    assert not log.needsBtcToUsd

    # Verify feed is updated
    assert mock_chainlink.hasPriceFeed(alpha_token)
    assert mock_chainlink.getPrice(alpha_token) == 1000 * EIGHTEEN_DECIMALS

    # Test canceling non-existent update
    with boa.reverts("no pending update feed"):
        mock_chainlink.cancelPriceFeedUpdate(alpha_token, sender=governance.address)


def test_chainlink_update_price_feed_cancel(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
):
    # Add initial feed with current timestamp
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Start update with current timestamp
    mock_chainlink_bravo.setMockData(1000 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "ChainlinkFeedUpdatePending")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_bravo.address
    assert log.staleTime == 0
    assert not log.needsEthToUsd
    assert not log.needsBtcToUsd

    # Cancel update
    assert mock_chainlink.cancelPriceFeedUpdate(alpha_token, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "ChainlinkFeedUpdateCancelled")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_bravo.address

    # Verify feed is not updated
    assert mock_chainlink.hasPriceFeed(alpha_token)
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS

    # Test confirming after cancel
    with boa.reverts("no pending update feed"):
        mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)


def test_chainlink_disable_price_feed(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    governance,
    bob,
):
    # Add initial feed with current timestamp
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test unauthorized access
    with boa.reverts("no perms"):
        mock_chainlink.disablePriceFeed(alpha_token, sender=bob)

    # Test disabling non-existent feed
    with boa.reverts("invalid asset"):
        mock_chainlink.disablePriceFeed(ZERO_ADDRESS, sender=governance.address)

    # Test successful disable
    assert mock_chainlink.disablePriceFeed(alpha_token, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "DisableChainlinkFeedPending")[0]
    assert log.asset == alpha_token.address

    # Test confirming before time lock
    with boa.reverts("time lock not reached"):
        mock_chainlink.confirmDisablePriceFeed(alpha_token, sender=governance.address)

    # Travel past time lock
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)

    # Test confirming
    assert mock_chainlink.confirmDisablePriceFeed(alpha_token, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "ChainlinkFeedDisabled")[0]
    assert log.asset == alpha_token.address

    # Verify feed is disabled
    assert not mock_chainlink.hasPriceFeed(alpha_token)
    assert mock_chainlink.getPrice(alpha_token) == 0

    # Test canceling non-existent disable
    with boa.reverts("no pending disable feed"):
        mock_chainlink.cancelDisablePriceFeed(alpha_token, sender=governance.address)


def test_chainlink_disable_price_feed_cancel(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    governance,
):
    # Add initial feed with current timestamp
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Start disable
    assert mock_chainlink.disablePriceFeed(alpha_token, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "DisableChainlinkFeedPending")[0]
    assert log.asset == alpha_token.address

    # Cancel disable
    assert mock_chainlink.cancelDisablePriceFeed(alpha_token, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "DisableChainlinkFeedCancelled")[0]
    assert log.asset == alpha_token.address

    # Verify feed is still active
    assert mock_chainlink.hasPriceFeed(alpha_token)
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS

    # Test confirming after cancel
    with boa.reverts("no pending disable feed"):
        mock_chainlink.confirmDisablePriceFeed(alpha_token, sender=governance.address)


def test_chainlink_disable_default_feeds(
    mock_chainlink,
    governance,
):
    # Test disabling ETH feed
    with boa.reverts("invalid asset"):
        mock_chainlink.disablePriceFeed(mock_chainlink.ETH(), sender=governance.address)

    # Test disabling WETH feed
    with boa.reverts("invalid asset"):
        mock_chainlink.disablePriceFeed(mock_chainlink.WETH(), sender=governance.address)

    # Test disabling BTC feed
    with boa.reverts("invalid asset"):
        mock_chainlink.disablePriceFeed(mock_chainlink.BTC(), sender=governance.address)


def test_chainlink_zero_stale_inherits_global(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    governance,
):
    # A stored zero inherits MissionControl's one-day policy.
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, 0, False, False, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - ONE_DAY_IN_SECS,
    )
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS

    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - ONE_DAY_IN_SECS - 1,
    )
    assert mock_chainlink.getPrice(alpha_token) == 0


def test_chainlink_price_stale_with_feed_config(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,  # Use a different feed for update
    governance,
):
    # Test adding feed with custom stale time
    stale_time = 3600  # 1 hour
    
    # Refresh the feed's timestamp to current time
    mock_chainlink_alpha.setMockData(500 * 10**8)
    
    # Add feed with custom stale time
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, stale_time, False, False, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    # Refresh again after time travel
    mock_chainlink_alpha.setMockData(500 * 10**8)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Verify event has stale time
    log = filter_logs(mock_chainlink, "NewChainlinkFeedAdded")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_alpha.address
    assert log.staleTime == stale_time
    assert not log.needsEthToUsd
    assert not log.needsBtcToUsd

    # Test price with feed's stale time
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS

    # Nonzero second-argument values are reserved for canonical PriceDesk.
    assert mock_chainlink.getPrice(alpha_token, 7200) == 0

    # Make price stale by advancing time (less than feed's stale time)
    boa.env.time_travel(seconds=1800)  # Advance 30 minutes
    mock_chainlink_alpha.setMockData(500 * 10**8)
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS  # Should still be valid

    # Make price stale by advancing time (more than feed's stale time)
    boa.env.time_travel(seconds=3600)  # Advance another hour (total 2 hours)
    # Set the feed's updatedAt to an old timestamp to make it stale
    old_timestamp = boa.env.timestamp - 7200  # 2 hours ago
    mock_chainlink_alpha.setMockData(500 * 10**8, 1, 1, boa.env.timestamp, old_timestamp)
    assert mock_chainlink.getPrice(alpha_token) == 0  # Price should be 0 when stale

    # Test updating feed with different stale time
    mock_chainlink_bravo.setMockData(500 * 10**8)  # Use bravo feed with same price
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, 7200, False, False, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_bravo.setMockData(500 * 10**8)
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    # Verify update event has new stale time
    log = filter_logs(mock_chainlink, "ChainlinkFeedUpdated")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_bravo.address
    assert log.staleTime == 7200
    assert not log.needsEthToUsd
    assert not log.needsBtcToUsd

    # Test price with new stale time
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS

    # Make price stale with new stale time
    boa.env.time_travel(seconds=3600)  # Advance 1 hour
    mock_chainlink_bravo.setMockData(500 * 10**8)
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS  # Should still be valid

    boa.env.time_travel(seconds=3601)  # Advance another hour + 1 second (total 2 hours + 1 second)
    # Set the feed's updatedAt to an old timestamp to make it stale
    old_timestamp = boa.env.timestamp - 7201  # 2 hours + 1 second ago
    mock_chainlink_bravo.setMockData(500 * 10**8, 1, 1, boa.env.timestamp, old_timestamp)
    assert mock_chainlink.getPrice(alpha_token) == 0  # Price should be 0 when stale


def test_chainlink_price_decimals(
    mock_chainlink,
    alpha_token,  # 8 decimals
    bravo_token,  # 6 decimals
    charlie_token,  # 18 decimals
    mock_chainlink_alpha,  # 8 decimals
    mock_chainlink_bravo,  # 6 decimals
    mock_chainlink_charlie,  # 18 decimals
    governance,
):
    # Test with 8 decimals (default) - with current timestamp
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS

    # Test with 6 decimals
    mock_chainlink_bravo.setDecimals(6)
    mock_chainlink_bravo.setMockData(500 * 10**6, 1, 1, boa.env.timestamp, boa.env.timestamp)  # Set price to 500 with 6 decimals
    assert mock_chainlink.addNewPriceFeed(bravo_token, mock_chainlink_bravo, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_bravo.setMockData(500 * 10**6, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(bravo_token, sender=governance.address)
    assert mock_chainlink.getPrice(bravo_token) == 500 * EIGHTEEN_DECIMALS

    # Test with 18 decimals
    mock_chainlink_charlie.setDecimals(18)
    mock_chainlink_charlie.setMockData(500 * EIGHTEEN_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)  # Set price to 500 with 18 decimals
    assert mock_chainlink.addNewPriceFeed(charlie_token, mock_chainlink_charlie, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_charlie.setMockData(500 * EIGHTEEN_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(charlie_token, sender=governance.address)
    assert mock_chainlink.getPrice(charlie_token) == 500 * EIGHTEEN_DECIMALS


def test_chainlink_price_validation(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    bravo_token,
    governance,
):
    # Test price with no feed
    assert mock_chainlink.getPrice(alpha_token) == 0
    assert not mock_chainlink.hasPriceFeed(alpha_token)

    # Test price with zero price
    mock_chainlink_alpha.setMockData(0)
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Test price with negative price
    mock_chainlink_alpha.setMockData(-1)
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Test price with too many decimals
    mock_chainlink_bravo.setDecimals(20)  # Set decimals to 20 (invalid)
    mock_chainlink_bravo.setMockData(500 * 10**20)  # Set price with 20 decimals
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(bravo_token, mock_chainlink_bravo, sender=governance.address)


def test_chainlink_price_feed_edge_cases(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
):
    # Test with maximum valid decimals (18) - with current timestamp
    mock_chainlink_alpha.setDecimals(18)
    mock_chainlink_alpha.setMockData(500 * EIGHTEEN_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(500 * EIGHTEEN_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS

    # Test with minimum valid decimals (1) using a different feed - with current timestamp
    mock_chainlink_bravo.setDecimals(1)
    mock_chainlink_bravo.setMockData(5, 1, 1, boa.env.timestamp, boa.env.timestamp)  # 5 with 1 decimal = 0.5
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_bravo.setMockData(5, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    assert mock_chainlink.getPrice(alpha_token) == 5 * 10**17  # 0.5 * 10**18

    # Test with very large price (use a new feed) - with current timestamp
    mock_chainlink_alpha.setDecimals(8)
    mock_chainlink_alpha.setMockData(2**128 - 1, 1, 1, boa.env.timestamp, boa.env.timestamp)  # Very large price
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(2**128 - 1, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    assert mock_chainlink.getPrice(alpha_token) == (2**128 - 1) * 10**10  # Normalized to 18 decimals

    # Test with very small price (near 0 but not 0) - with current timestamp
    mock_chainlink_bravo.setDecimals(8)
    mock_chainlink_bravo.setMockData(1, 1, 1, boa.env.timestamp, boa.env.timestamp)  # 1 with 8 decimals = 0.00000001
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_bravo.setMockData(1, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    assert mock_chainlink.getPrice(alpha_token) == 10**10  # 0.00000001 * 10**18


def test_chainlink_stale_price_edge_cases(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    governance,
):
    # A nonzero local policy is exact and includes its boundary second.
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, 300, False, False, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - 300,
    )
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS

    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - 301,
    )
    assert mock_chainlink.getPrice(alpha_token) == 0


def test_chainlink_time_lock_edge_cases(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
):
    # Test confirming just before time lock boundary - with current timestamp
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() - 1)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    with boa.reverts("time lock not reached"):
        mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test confirming at time lock boundary
    boa.env.time_travel(blocks=1)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test multiple time lock actions in sequence (use a different feed for update) - with current timestamp
    mock_chainlink_bravo.setMockData(1000 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_bravo.setMockData(1000 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    assert mock_chainlink.disablePriceFeed(alpha_token, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmDisablePriceFeed(alpha_token, sender=governance.address)

    # Test with maximum allowed time lock (use a reasonable value) - with current timestamp
    mock_chainlink.setActionTimeLock(302400, sender=governance.address)  # 7 days in blocks
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=302400)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test with minimum allowed time lock - with current timestamp
    mock_chainlink.setActionTimeLock(21600, sender=governance.address)  # 12 hours in blocks
    mock_chainlink_bravo.setMockData(1000 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)
    boa.env.time_travel(blocks=21600)
    mock_chainlink_bravo.setMockData(1000 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)


def test_chainlink_governance_edge_cases(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
    switchboard_alpha,
):
    # Test multiple governance actions in sequence - with current timestamps
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    assert mock_chainlink.cancelNewPendingPriceFeed(alpha_token, sender=governance.address)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)
    mock_chainlink_bravo.setMockData(1000 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_bravo.setMockData(1000 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    expected_price = 1000 * EIGHTEEN_DECIMALS
    assert mock_chainlink.getPrice(alpha_token) == expected_price
    assert mock_chainlink.updateStaleTime(
        alpha_token, 3_600, sender=governance.address
    )

    # Test governance actions during pause (using MissionControl address)
    mock_chainlink.pause(True, sender=switchboard_alpha.address)
    assert mock_chainlink.getPrice(alpha_token) == expected_price
    with boa.reverts("contract paused"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    with boa.reverts("contract paused"):
        mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    with boa.reverts("contract paused"):
        mock_chainlink.updateStaleTime(
            alpha_token, 3_600, sender=governance.address
        )
    with boa.reverts("contract paused"):
        mock_chainlink.disablePriceFeed(alpha_token, sender=governance.address)
    with boa.reverts("contract paused"):
        mock_chainlink.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
    with boa.reverts("contract paused"):
        mock_chainlink.cancelPriceFeedUpdate(
            alpha_token, sender=governance.address
        )

    # Test governance actions after pause
    mock_chainlink.pause(False, sender=switchboard_alpha.address)
    assert mock_chainlink.cancelPriceFeedUpdate(
        alpha_token, sender=governance.address
    )
    # First disable the existing feed
    assert mock_chainlink.disablePriceFeed(alpha_token, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmDisablePriceFeed(alpha_token, sender=governance.address)
    # Now we can add a new feed - with current timestamp
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)


def test_chainlink_price_feed_round_validation(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    governance,
):
    """Test validation of price feed round IDs"""
    # Test with zero round ID (use current timestamp but invalid roundId)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 0, 1, boa.env.timestamp, boa.env.timestamp)
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Test with answeredInRound < roundId (use current timestamp but invalid round data)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 2, 1, boa.env.timestamp, boa.env.timestamp)
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Test with valid round data - with current timestamp
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, boa.env.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)


def test_chainlink_price_feed_timestamp_validation(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    governance,
    switchboard_alpha,
    mission_control,
):
    """Test validation of price feed timestamps"""
    boa.env.evm.patch.timestamp += ONE_YEAR
    current_time = boa.env.evm.patch.timestamp

    # Test with future timestamp
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, 1, current_time + 1000)
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # set stale time to 1 day
    aid = switchboard_alpha.setStaleTime(ONE_DAY_IN_SECS, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock() + 1)
    assert switchboard_alpha.executePendingAction(aid, sender=governance.address)
    assert mission_control.getPriceStaleTime() == ONE_DAY_IN_SECS

    # Test with old timestamp
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, 1, current_time - (ONE_DAY_IN_SECS * 2))
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Test with valid timestamp
    # Need to set timestamp to current time since validation happens immediately
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, 1, boa.env.evm.patch.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    # Update timestamp again for confirmation validation
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, 1, boa.env.evm.patch.timestamp)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)


def _add_sc20_chainlink_feed(
    source,
    asset,
    feed,
    governance,
    stale_time,
    needs_eth=False,
    needs_btc=False,
    refresh_feeds=(),
):
    feed.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    assert source.addNewPriceFeed(
        asset,
        feed,
        stale_time,
        needs_eth,
        needs_btc,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=source.actionTimeLock() + 1)
    for other_feed, price in refresh_feeds:
        other_feed.setMockData(
            price,
            1,
            1,
            boa.env.timestamp,
            boa.env.timestamp,
        )
    feed.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    assert source.confirmNewPriceFeed(asset, sender=governance.address)


def _set_sc20_chainlink_global_bound(
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


@pytest.mark.parametrize("explicit_zero", [False, True])
def test_chainlink_zero_stale_time_on_feed_rotation_preserves_active_policy(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
    explicit_zero,
):
    _add_sc20_chainlink_feed(
        mock_chainlink,
        alpha_token,
        mock_chainlink_alpha,
        governance,
        600,
    )
    mock_chainlink_bravo.setDecimals(8)
    mock_chainlink_bravo.setMockData(
        2_500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )

    assert mock_chainlink.isValidUpdateFeed(
        alpha_token,
        mock_chainlink_bravo,
        8,
        False,
        False,
        0,
    )
    if explicit_zero:
        assert mock_chainlink.updatePriceFeed(
            alpha_token,
            mock_chainlink_bravo,
            0,
            sender=governance.address,
        )
    else:
        assert mock_chainlink.updatePriceFeed(
            alpha_token,
            mock_chainlink_bravo,
            sender=governance.address,
        )

    log = filter_logs(mock_chainlink, "ChainlinkFeedUpdatePending")[0]
    assert log.feed == mock_chainlink_bravo.address
    assert log.staleTime == 600
    pending = mock_chainlink.pendingUpdates(alpha_token)
    assert pending.config.feed == mock_chainlink_bravo.address
    assert pending.config.staleTime == 600

    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_bravo.setMockData(
        2_500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    assert mock_chainlink.confirmPriceFeedUpdate(
        alpha_token, sender=governance.address
    )
    stored = mock_chainlink.feedConfig(alpha_token)
    assert stored.feed == mock_chainlink_bravo.address
    assert stored.staleTime == 600


@pytest.mark.parametrize(
    "candidate,expected_valid",
    [
        (299, False),
        (300, True),
        (MAX_FEED_STALE_TIME, True),
        (MAX_FEED_STALE_TIME + 1, False),
    ],
)
def test_chainlink_local_stale_time_boundaries_on_add_and_feed_update(
    mock_chainlink,
    alpha_token,
    bravo_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
    candidate,
    expected_valid,
):
    mock_chainlink_alpha.setDecimals(8)
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    assert mock_chainlink.isValidNewFeed(
        alpha_token,
        mock_chainlink_alpha,
        8,
        False,
        False,
        candidate,
    ) is expected_valid
    if expected_valid:
        assert mock_chainlink.addNewPriceFeed(
            alpha_token,
            mock_chainlink_alpha,
            candidate,
            sender=governance.address,
        )
        boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
        mock_chainlink_alpha.setMockData(
            500 * CHAINLINK_DECIMALS,
            1,
            1,
            boa.env.timestamp,
            boa.env.timestamp,
        )
        assert mock_chainlink.confirmNewPriceFeed(
            alpha_token, sender=governance.address
        )
        assert mock_chainlink.feedConfig(alpha_token).staleTime == candidate
    else:
        with boa.reverts("invalid feed"):
            mock_chainlink.addNewPriceFeed(
                alpha_token,
                mock_chainlink_alpha,
                candidate,
                sender=governance.address,
            )

    with boa.env.anchor():
        _add_sc20_chainlink_feed(
            mock_chainlink,
            bravo_token,
            mock_chainlink_alpha,
            governance,
            600,
        )
        mock_chainlink_bravo.setDecimals(8)
        mock_chainlink_bravo.setMockData(
            2_500 * CHAINLINK_DECIMALS,
            1,
            1,
            boa.env.timestamp,
            boa.env.timestamp,
        )
        assert mock_chainlink.isValidUpdateFeed(
            bravo_token,
            mock_chainlink_bravo,
            8,
            False,
            False,
            candidate,
        ) is expected_valid
        if expected_valid:
            assert mock_chainlink.updatePriceFeed(
                bravo_token,
                mock_chainlink_bravo,
                candidate,
                sender=governance.address,
            )
            boa.env.time_travel(
                blocks=mock_chainlink.actionTimeLock() + 1
            )
            mock_chainlink_bravo.setMockData(
                2_500 * CHAINLINK_DECIMALS,
                1,
                1,
                boa.env.timestamp,
                boa.env.timestamp,
            )
            assert mock_chainlink.confirmPriceFeedUpdate(
                bravo_token, sender=governance.address
            )
            assert mock_chainlink.feedConfig(bravo_token).staleTime == candidate
        else:
            with boa.reverts("invalid feed"):
                mock_chainlink.updatePriceFeed(
                    bravo_token,
                    mock_chainlink_bravo,
                    candidate,
                    sender=governance.address,
                )


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
def test_chainlink_global_default_and_exact_feed_override_matrix(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    governance,
    mission_control,
    switchboard_alpha,
    global_bound,
    feed_bound,
    age,
    expected_valid,
):
    _set_sc20_chainlink_global_bound(
        switchboard_alpha, governance, mission_control, global_bound
    )
    _add_sc20_chainlink_feed(
        mock_chainlink,
        alpha_token,
        mock_chainlink_alpha,
        governance,
        feed_bound,
    )
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - age,
    )

    expected_price = 500 * EIGHTEEN_DECIMALS if expected_valid else 0
    assert mock_chainlink.getPrice(alpha_token) == expected_price
    assert mock_chainlink.getPriceAndHasFeed(alpha_token) == (
        expected_price,
        True,
    )


def test_chainlink_nonzero_global_requires_canonical_pricedesk_forwarding(
    mock_chainlink,
    alpha_token,
    bravo_token,
    mock_chainlink_alpha,
    governance,
    mission_control,
    switchboard_alpha,
    price_desk,
):
    _set_sc20_chainlink_global_bound(
        switchboard_alpha, governance, mission_control, 7_200
    )
    _add_sc20_chainlink_feed(
        mock_chainlink,
        alpha_token,
        mock_chainlink_alpha,
        governance,
        0,
    )
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - 100,
    )
    expected = 500 * EIGHTEEN_DECIMALS

    assert mock_chainlink.getPrice(alpha_token, 300) == 0
    assert mock_chainlink.getPrice(alpha_token, 300, price_desk.address) == 0
    assert mock_chainlink.getPrice(
        alpha_token, 300, ZERO_ADDRESS, sender=price_desk.address
    ) == 0
    assert mock_chainlink.getPriceAndHasFeed(alpha_token, 300) == (0, True)
    assert mock_chainlink.getPriceAndHasFeed(bravo_token, 300) == (0, False)

    assert mock_chainlink.getPrice(
        alpha_token,
        300,
        price_desk.address,
        sender=price_desk.address,
    ) == expected
    assert mock_chainlink.getPriceAndHasFeed(
        alpha_token,
        300,
        price_desk.address,
        sender=price_desk.address,
    ) == (expected, True)

    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - 301,
    )
    assert mock_chainlink.getPrice(
        alpha_token,
        300,
        price_desk.address,
        sender=price_desk.address,
    ) == 0


def test_chainlink_pricedesk_forwards_live_global_policy(
    chainlink,
    price_desk,
    alpha_token,
    mock_chainlink_alpha,
    governance,
    mission_control,
    switchboard_alpha,
):
    _set_sc20_chainlink_global_bound(
        switchboard_alpha, governance, mission_control, 3_600
    )
    _add_sc20_chainlink_feed(
        chainlink,
        alpha_token,
        mock_chainlink_alpha,
        governance,
        0,
    )
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - 3_600,
    )
    expected = 500 * EIGHTEEN_DECIMALS
    assert price_desk.getPrice(alpha_token) == expected
    assert chainlink.getPrice(alpha_token) == expected

    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - 3_601,
    )
    assert price_desk.getPrice(alpha_token) == 0
    assert chainlink.getPrice(alpha_token) == 0


def test_chainlink_exact_override_ignores_invalid_global_policy(
    chainlink,
    price_desk,
    alpha_token,
    mock_chainlink_alpha,
    governance,
    setGeneralConfig,
):
    _add_sc20_chainlink_feed(
        chainlink,
        alpha_token,
        mock_chainlink_alpha,
        governance,
        300,
    )
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - 200,
    )
    expected = 500 * EIGHTEEN_DECIMALS

    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        assert chainlink.getPrice(alpha_token) == expected
        assert price_desk.getPrice(alpha_token) == expected

    for invalid_global in (0, MAX_FEED_STALE_TIME + 1):
        with boa.env.anchor():
            setGeneralConfig(_priceStaleTime=invalid_global)
            assert chainlink.getPrice(alpha_token) == expected
            assert chainlink.getPriceAndHasFeed(alpha_token) == (
                expected,
                True,
            )
            assert price_desk.getPrice(alpha_token) == expected


@pytest.mark.parametrize("conversion_kind", ["eth", "btc"])
@pytest.mark.parametrize("stale_leg", ["conversion", "primary", "none"])
def test_chainlink_feed_overrides_are_independent_per_conversion_leg(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    mock_chainlink_delta,
    governance,
    conversion_kind,
    stale_leg,
):
    conversion_asset = (
        mock_chainlink.ETH() if conversion_kind == "eth" else mock_chainlink.BTC()
    )
    conversion_feed = (
        mock_chainlink_bravo if conversion_kind == "eth" else mock_chainlink_delta
    )
    conversion_price = (
        2_500 * CHAINLINK_DECIMALS
        if conversion_kind == "eth"
        else 50_000 * CHAINLINK_DECIMALS
    )
    conversion_bound = 300 if stale_leg == "conversion" else 600
    primary_bound = 300 if stale_leg == "primary" else 600
    _add_sc20_chainlink_feed(
        mock_chainlink,
        conversion_asset,
        conversion_feed,
        governance,
        conversion_bound,
    )
    conversion_feed.setMockData(
        conversion_price, 1, 1, boa.env.timestamp, boa.env.timestamp
    )
    _add_sc20_chainlink_feed(
        mock_chainlink,
        alpha_token,
        mock_chainlink_alpha,
        governance,
        primary_bound,
        needs_eth=conversion_kind == "eth",
        needs_btc=conversion_kind == "btc",
        refresh_feeds=((conversion_feed, conversion_price),),
    )

    primary_age = 301 if stale_leg == "primary" else 5
    conversion_age = 301 if stale_leg == "conversion" else 5
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - primary_age,
    )
    conversion_feed.setMockData(
        conversion_price,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - conversion_age,
    )

    expected = 0
    if stale_leg == "none":
        normalized_conversion_price = (
            2_500 * EIGHTEEN_DECIMALS
            if conversion_kind == "eth"
            else 50_000 * EIGHTEEN_DECIMALS
        )
        expected = 500 * normalized_conversion_price
    assert mock_chainlink.getPrice(alpha_token) == expected


@pytest.mark.parametrize("conversion_kind", ["eth", "btc"])
@pytest.mark.parametrize("aged_leg", ["conversion", "primary"])
def test_chainlink_forwarded_global_applies_to_each_zero_config_leg(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    mock_chainlink_delta,
    governance,
    mission_control,
    switchboard_alpha,
    price_desk,
    conversion_kind,
    aged_leg,
):
    conversion_asset = (
        mock_chainlink.ETH() if conversion_kind == "eth" else mock_chainlink.BTC()
    )
    conversion_feed = (
        mock_chainlink_bravo if conversion_kind == "eth" else mock_chainlink_delta
    )
    conversion_price = (
        2_500 * CHAINLINK_DECIMALS
        if conversion_kind == "eth"
        else 50_000 * CHAINLINK_DECIMALS
    )
    _set_sc20_chainlink_global_bound(
        switchboard_alpha, governance, mission_control, 600
    )
    _add_sc20_chainlink_feed(
        mock_chainlink, conversion_asset, conversion_feed, governance, 0
    )
    conversion_feed.setMockData(
        conversion_price, 1, 1, boa.env.timestamp, boa.env.timestamp
    )
    _add_sc20_chainlink_feed(
        mock_chainlink,
        alpha_token,
        mock_chainlink_alpha,
        governance,
        0,
        needs_eth=conversion_kind == "eth",
        needs_btc=conversion_kind == "btc",
        refresh_feeds=((conversion_feed, conversion_price),),
    )
    primary_age = 301 if aged_leg == "primary" else 5
    conversion_age = 301 if aged_leg == "conversion" else 5
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - primary_age,
    )
    conversion_feed.setMockData(
        conversion_price,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - conversion_age,
    )
    normalized_conversion_price = (
        2_500 * EIGHTEEN_DECIMALS
        if conversion_kind == "eth"
        else 50_000 * EIGHTEEN_DECIMALS
    )
    assert mock_chainlink.getPrice(alpha_token) == (
        500 * normalized_conversion_price
    )
    assert mock_chainlink.getPrice(
        alpha_token,
        300,
        price_desk.address,
        sender=price_desk.address,
    ) == 0


@pytest.mark.parametrize("conversion_kind", ["eth", "btc"])
@pytest.mark.parametrize("bounded_leg", ["conversion", "primary"])
@pytest.mark.parametrize(
    "global_bound,local_bound,local_age,inherited_age,expected_valid",
    [
        (600, 300, 301, 5, False),
        (600, 300, 5, 301, True),
        (300, 600, 301, 5, True),
    ],
)
def test_chainlink_zero_leg_inherits_global_and_preserves_other_leg_override(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    mock_chainlink_delta,
    governance,
    mission_control,
    switchboard_alpha,
    price_desk,
    conversion_kind,
    bounded_leg,
    global_bound,
    local_bound,
    local_age,
    inherited_age,
    expected_valid,
):
    conversion_asset = (
        mock_chainlink.ETH() if conversion_kind == "eth" else mock_chainlink.BTC()
    )
    conversion_feed = (
        mock_chainlink_bravo if conversion_kind == "eth" else mock_chainlink_delta
    )
    conversion_price = (
        2_500 * CHAINLINK_DECIMALS
        if conversion_kind == "eth"
        else 50_000 * CHAINLINK_DECIMALS
    )
    _set_sc20_chainlink_global_bound(
        switchboard_alpha, governance, mission_control, global_bound
    )
    conversion_bound = local_bound if bounded_leg == "conversion" else 0
    primary_bound = local_bound if bounded_leg == "primary" else 0
    _add_sc20_chainlink_feed(
        mock_chainlink,
        conversion_asset,
        conversion_feed,
        governance,
        conversion_bound,
    )
    conversion_feed.setMockData(
        conversion_price, 1, 1, boa.env.timestamp, boa.env.timestamp
    )
    _add_sc20_chainlink_feed(
        mock_chainlink,
        alpha_token,
        mock_chainlink_alpha,
        governance,
        primary_bound,
        needs_eth=conversion_kind == "eth",
        needs_btc=conversion_kind == "btc",
        refresh_feeds=((conversion_feed, conversion_price),),
    )
    primary_age = local_age if bounded_leg == "primary" else inherited_age
    conversion_age = local_age if bounded_leg == "conversion" else inherited_age
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - primary_age,
    )
    conversion_feed.setMockData(
        conversion_price,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - conversion_age,
    )
    normalized_conversion_price = (
        2_500 * EIGHTEEN_DECIMALS
        if conversion_kind == "eth"
        else 50_000 * EIGHTEEN_DECIMALS
    )
    expected = 500 * normalized_conversion_price if expected_valid else 0
    assert mock_chainlink.getPrice(alpha_token, 0) == expected
    assert mock_chainlink.getPrice(
        alpha_token,
        global_bound,
        price_desk.address,
        sender=price_desk.address,
    ) == expected


@pytest.mark.parametrize("conversion_kind", ["eth", "btc"])
def test_chainlink_stale_time_update_preserves_active_conversion_route(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    mock_chainlink_delta,
    governance,
    conversion_kind,
):
    conversion_asset = (
        mock_chainlink.ETH() if conversion_kind == "eth" else mock_chainlink.BTC()
    )
    conversion_feed = (
        mock_chainlink_bravo if conversion_kind == "eth" else mock_chainlink_delta
    )
    conversion_price = (
        2_500 * CHAINLINK_DECIMALS
        if conversion_kind == "eth"
        else 50_000 * CHAINLINK_DECIMALS
    )
    _add_sc20_chainlink_feed(
        mock_chainlink,
        conversion_asset,
        conversion_feed,
        governance,
        600,
    )
    conversion_feed.setMockData(
        conversion_price, 1, 1, boa.env.timestamp, boa.env.timestamp
    )
    _add_sc20_chainlink_feed(
        mock_chainlink,
        alpha_token,
        mock_chainlink_alpha,
        governance,
        600,
        needs_eth=conversion_kind == "eth",
        needs_btc=conversion_kind == "btc",
        refresh_feeds=((conversion_feed, conversion_price),),
    )
    before = mock_chainlink.feedConfig(alpha_token)
    normalized_conversion_price = (
        2_500 * EIGHTEEN_DECIMALS
        if conversion_kind == "eth"
        else 50_000 * EIGHTEEN_DECIMALS
    )
    expected = 500 * normalized_conversion_price
    assert mock_chainlink.getPrice(alpha_token) == expected

    assert mock_chainlink.isValidStaleTimeUpdate(alpha_token, 300)
    assert mock_chainlink.updateStaleTime(
        alpha_token, 300, sender=governance.address
    )
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    conversion_feed.setMockData(
        conversion_price, 1, 1, boa.env.timestamp, boa.env.timestamp
    )
    assert mock_chainlink.confirmPriceFeedUpdate(
        alpha_token, sender=governance.address
    )

    after = mock_chainlink.feedConfig(alpha_token)
    assert after.feed == before.feed
    assert after.decimals == before.decimals
    assert after.needsEthToUsd is before.needsEthToUsd
    assert after.needsBtcToUsd is before.needsBtcToUsd
    assert after.staleTime == 300
    assert mock_chainlink.pendingUpdates(alpha_token).actionId == 0
    assert mock_chainlink.getPrice(alpha_token) == expected


def test_chainlink_candidate_validation_uses_exact_feed_override(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mission_control,
    switchboard_alpha,
    governance,
):
    with boa.env.anchor():
        _set_sc20_chainlink_global_bound(
            switchboard_alpha, governance, mission_control
        )
        mock_chainlink_alpha.setMockData(
            500 * CHAINLINK_DECIMALS,
            1,
            1,
            boa.env.timestamp,
            boa.env.timestamp - 5_400,
        )
        assert mock_chainlink.isValidNewFeed(
            alpha_token,
            mock_chainlink_alpha,
            8,
            False,
            False,
            7_200,
        )
        assert not mock_chainlink.isValidNewFeed(
            alpha_token,
            mock_chainlink_alpha,
            8,
            False,
            False,
            3_600,
        )


@pytest.mark.parametrize("conversion_kind", ["eth", "btc"])
def test_chainlink_candidate_validation_checks_conversion_leg_override(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    mock_chainlink_delta,
    governance,
    mission_control,
    switchboard_alpha,
    conversion_kind,
):
    with boa.env.anchor():
        _set_sc20_chainlink_global_bound(
            switchboard_alpha, governance, mission_control
        )
        conversion_asset = (
            mock_chainlink.ETH()
            if conversion_kind == "eth"
            else mock_chainlink.BTC()
        )
        conversion_feed = (
            mock_chainlink_bravo
            if conversion_kind == "eth"
            else mock_chainlink_delta
        )
        conversion_price = (
            2_500 * CHAINLINK_DECIMALS
            if conversion_kind == "eth"
            else 50_000 * CHAINLINK_DECIMALS
        )
        _add_sc20_chainlink_feed(
            mock_chainlink, conversion_asset, conversion_feed, governance, 3_600
        )
        mock_chainlink_alpha.setMockData(
            500 * CHAINLINK_DECIMALS,
            1,
            1,
            boa.env.timestamp,
            boa.env.timestamp,
        )
        assert mock_chainlink.isValidNewFeed(
            alpha_token,
            mock_chainlink_alpha,
            8,
            conversion_kind == "eth",
            conversion_kind == "btc",
            7_200,
        )

        conversion_feed.setMockData(
            conversion_price,
            1,
            1,
            boa.env.timestamp,
            boa.env.timestamp - 5_400,
        )
        assert not mock_chainlink.isValidNewFeed(
            alpha_token,
            mock_chainlink_alpha,
            8,
            conversion_kind == "eth",
            conversion_kind == "btc",
            7_200,
        )


def test_sc21_chainlink_future_timestamp_characterization(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    bravo_token,
    governance,
):
    assert mock_chainlink.getPriceAndHasFeed(bravo_token) == (0, False)
    _add_sc20_chainlink_feed(
        mock_chainlink,
        alpha_token,
        mock_chainlink_alpha,
        governance,
        0,
    )
    future_time = boa.env.timestamp + 100
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS, 1, 1, boa.env.timestamp, future_time
    )
    assert mock_chainlink.getPrice(alpha_token, 0) == 0
    assert mock_chainlink.getPrice(alpha_token, 1_000) == 0
    assert mock_chainlink.getPriceAndHasFeed(alpha_token, 0) == (0, True)
    assert mock_chainlink.getPriceAndHasFeed(alpha_token, 1_000) == (0, True)

    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS


def test_chainlink_stale_time_update_lifecycle_and_validator_parity(
    mock_chainlink,
    alpha_token,
    bravo_token,
    mock_chainlink_alpha,
    governance,
    bob,
):
    assert not mock_chainlink.hasPriceFeed(bravo_token)
    assert not mock_chainlink.isValidStaleTimeUpdate(bravo_token, 3_600)
    with boa.reverts("invalid feed"):
        mock_chainlink.updateStaleTime(
            bravo_token, 3_600, sender=governance.address
        )
    assert mock_chainlink.pendingUpdates(bravo_token).actionId == 0

    _add_sc20_chainlink_feed(
        mock_chainlink,
        alpha_token,
        mock_chainlink_alpha,
        governance,
        7_200,
    )
    current = mock_chainlink.feedConfig(alpha_token)

    with boa.reverts("no perms"):
        mock_chainlink.updateStaleTime(
            alpha_token, 3_600, sender=bob
        )

    assert not mock_chainlink.isValidUpdateFeed(
        alpha_token,
        current.feed,
        current.decimals,
        current.needsEthToUsd,
        current.needsBtcToUsd,
        3_600,
    )
    with boa.reverts("invalid feed"):
        mock_chainlink.updatePriceFeed(
            alpha_token,
            current.feed,
            3_600,
            current.needsEthToUsd,
            current.needsBtcToUsd,
            sender=governance.address,
        )

    for candidate, expected_valid in (
        (0, True),
        (299, False),
        (300, True),
        (3_600, True),
        (7_200, False),
        (MAX_FEED_STALE_TIME, True),
        (MAX_FEED_STALE_TIME + 1, False),
    ):
        assert (
            mock_chainlink.isValidStaleTimeUpdate(alpha_token, candidate)
            is expected_valid
        )
        with boa.env.anchor():
            if expected_valid:
                assert mock_chainlink.updateStaleTime(
                    alpha_token, candidate, sender=governance.address
                )
            else:
                with boa.reverts("invalid feed"):
                    mock_chainlink.updateStaleTime(
                        alpha_token, candidate, sender=governance.address
                    )

    assert mock_chainlink.updateStaleTime(
        alpha_token, 3_600, sender=governance.address
    )
    log = filter_logs(mock_chainlink, "ChainlinkFeedUpdatePending")[0]
    assert log.feed == current.feed
    assert log.oldFeed == current.feed
    assert log.staleTime == 3_600
    pending = mock_chainlink.pendingUpdates(alpha_token)
    assert pending.actionId != 0
    assert pending.config.feed == current.feed
    assert pending.config.decimals == current.decimals
    assert pending.config.needsEthToUsd is current.needsEthToUsd
    assert pending.config.needsBtcToUsd is current.needsBtcToUsd
    assert pending.config.staleTime == 3_600
    with boa.reverts("time lock not reached"):
        mock_chainlink.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    assert mock_chainlink.confirmPriceFeedUpdate(
        alpha_token, sender=governance.address
    )
    stored = mock_chainlink.feedConfig(alpha_token)
    assert stored.feed == current.feed
    assert stored.decimals == current.decimals
    assert stored.needsEthToUsd is current.needsEthToUsd
    assert stored.needsBtcToUsd is current.needsBtcToUsd
    assert stored.staleTime == 3_600
    assert mock_chainlink.pendingUpdates(alpha_token).actionId == 0

    assert mock_chainlink.updateStaleTime(
        alpha_token, 0, sender=governance.address
    )
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    assert mock_chainlink.confirmPriceFeedUpdate(
        alpha_token, sender=governance.address
    )
    assert mock_chainlink.feedConfig(alpha_token).staleTime == 0

    assert mock_chainlink.updateStaleTime(
        alpha_token, 7_200, sender=governance.address
    )
    assert mock_chainlink.cancelPriceFeedUpdate(
        alpha_token, sender=governance.address
    )
    assert mock_chainlink.feedConfig(alpha_token).staleTime == 0
    assert mock_chainlink.pendingUpdates(alpha_token).actionId == 0
    with boa.reverts("no pending update feed"):
        mock_chainlink.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )

    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    assert mock_chainlink.updateStaleTime(
        alpha_token, 300, sender=governance.address
    )
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp - 301,
    )
    assert not mock_chainlink.confirmPriceFeedUpdate(
        alpha_token, sender=governance.address
    )
    pending = mock_chainlink.pendingUpdates(alpha_token)
    assert pending.actionId != 0
    assert pending.config.staleTime == 300
    assert mock_chainlink.feedConfig(alpha_token).staleTime == 0

    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    assert mock_chainlink.confirmPriceFeedUpdate(
        alpha_token, sender=governance.address
    )
    assert mock_chainlink.pendingUpdates(alpha_token).actionId == 0
    assert mock_chainlink.feedConfig(alpha_token).staleTime == 300


def test_chainlink_failed_feed_replacement_confirmation_auto_cancels(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
):
    with boa.env.anchor():
        _add_sc20_chainlink_feed(
            mock_chainlink,
            alpha_token,
            mock_chainlink_alpha,
            governance,
            600,
        )
        active = mock_chainlink.feedConfig(alpha_token)
        mock_chainlink_bravo.setMockData(
            1_000 * CHAINLINK_DECIMALS,
            1,
            1,
            boa.env.timestamp,
            boa.env.timestamp,
        )
        assert mock_chainlink.updatePriceFeed(
            alpha_token,
            mock_chainlink_bravo,
            600,
            False,
            False,
            sender=governance.address,
        )
        action_id = mock_chainlink.pendingUpdates(alpha_token).actionId
        assert action_id != 0
        boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
        mock_chainlink_bravo.setMockData(
            0,
            1,
            1,
            boa.env.timestamp,
            boa.env.timestamp,
        )

        assert not mock_chainlink.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert mock_chainlink.pendingUpdates(alpha_token).actionId == 0
        assert not mock_chainlink.hasPendingAction(action_id)
        stored = mock_chainlink.feedConfig(alpha_token)
        assert stored.feed == active.feed
        assert stored.staleTime == active.staleTime


@pytest.mark.parametrize("invalid_global", [0, MAX_FEED_STALE_TIME + 1])
@pytest.mark.parametrize(
    "candidate_stale_time,should_confirm",
    [(0, False), (MAX_FEED_STALE_TIME, True)],
)
def test_chainlink_stale_time_confirmation_revalidates_live_global_policy(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    governance,
    setGeneralConfig,
    invalid_global,
    candidate_stale_time,
    should_confirm,
):
    _add_sc20_chainlink_feed(
        mock_chainlink,
        alpha_token,
        mock_chainlink_alpha,
        governance,
        600,
    )
    before = mock_chainlink.feedConfig(alpha_token)
    expected = 500 * EIGHTEEN_DECIMALS
    assert mock_chainlink.getPrice(alpha_token) == expected
    assert mock_chainlink.isValidStaleTimeUpdate(
        alpha_token, candidate_stale_time
    )
    assert mock_chainlink.updateStaleTime(
        alpha_token, candidate_stale_time, sender=governance.address
    )

    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    setGeneralConfig(_priceStaleTime=invalid_global)
    assert (
        mock_chainlink.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        is should_confirm
    )

    after = mock_chainlink.feedConfig(alpha_token)
    assert after.feed == before.feed
    assert after.decimals == before.decimals
    assert after.needsEthToUsd is before.needsEthToUsd
    assert after.needsBtcToUsd is before.needsBtcToUsd
    assert after.staleTime == (
        candidate_stale_time if should_confirm else before.staleTime
    )
    afterPending = mock_chainlink.pendingUpdates(alpha_token)
    if should_confirm:
        assert afterPending.actionId == 0
    else:
        assert afterPending.actionId != 0
        assert afterPending.config.staleTime == candidate_stale_time
        assert mock_chainlink.cancelPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert mock_chainlink.pendingUpdates(alpha_token).actionId == 0
    assert mock_chainlink.getPrice(alpha_token) == expected


def _start_chainlink_pending_action(
    kind,
    source,
    asset,
    primary_feed,
    alternate_feed,
    governance,
):
    primary_feed.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    if kind == "add":
        assert source.addNewPriceFeed(
            asset, primary_feed, 300, sender=governance.address
        )
        return

    _add_sc20_chainlink_feed(
        source,
        asset,
        primary_feed,
        governance,
        300,
    )
    alternate_feed.setMockData(
        1_000 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    if kind == "update":
        assert source.updatePriceFeed(
            asset, alternate_feed, 300, sender=governance.address
        )
    elif kind == "stale":
        assert source.updateStaleTime(
            asset, 600, sender=governance.address
        )
    else:
        assert kind == "disable"
        assert source.disablePriceFeed(asset, sender=governance.address)


def _chainlink_pending_state(source, asset):
    pending = source.pendingUpdates(asset)
    return (
        pending.actionId,
        pending.config.feed,
        pending.config.decimals,
        pending.config.needsEthToUsd,
        pending.config.needsBtcToUsd,
        pending.config.staleTime,
    )


def _chainlink_active_state(source, asset):
    active = source.feedConfig(asset)
    return (
        source.hasPriceFeed(asset),
        active.feed,
        active.decimals,
        active.needsEthToUsd,
        active.needsBtcToUsd,
        active.staleTime,
    )


def _chainlink_action_state(source, asset):
    return (
        source.hasPendingPriceFeedUpdate(asset),
        _chainlink_pending_state(source, asset),
        _chainlink_active_state(source, asset),
    )


def _chainlink_wrong_action_selectors(pending_kind):
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
def test_chainlink_pending_action_collisions_and_cleanup(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
    pending_kind,
):
    _start_chainlink_pending_action(
        pending_kind,
        mock_chainlink,
        alpha_token,
        mock_chainlink_alpha,
        mock_chainlink_bravo,
        governance,
    )
    before = _chainlink_action_state(mock_chainlink, alpha_token)

    initiators = (
        lambda: mock_chainlink.addNewPriceFeed(
            alpha_token,
            mock_chainlink_alpha,
            300,
            sender=governance.address,
        ),
        lambda: mock_chainlink.updatePriceFeed(
            alpha_token,
            mock_chainlink_bravo,
            300,
            sender=governance.address,
        ),
        lambda: mock_chainlink.updateStaleTime(
            alpha_token, 300, sender=governance.address
        ),
        lambda: mock_chainlink.disablePriceFeed(
            alpha_token, sender=governance.address
        ),
    )
    for initiate in initiators:
        with boa.reverts("pending feed action"):
            initiate()
        assert _chainlink_action_state(mock_chainlink, alpha_token) == before

    for reason, selector in _chainlink_wrong_action_selectors(pending_kind):
        with boa.reverts(reason):
            getattr(mock_chainlink, selector)(
                alpha_token, sender=governance.address
            )
        assert _chainlink_action_state(mock_chainlink, alpha_token) == before

    active_before = _chainlink_active_state(mock_chainlink, alpha_token)
    if pending_kind == "add":
        assert mock_chainlink.cancelNewPendingPriceFeed(
            alpha_token, sender=governance.address
        )
    elif pending_kind in ("update", "stale"):
        assert mock_chainlink.cancelPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
    else:
        assert mock_chainlink.cancelDisablePriceFeed(
            alpha_token, sender=governance.address
        )
    assert not mock_chainlink.hasPendingPriceFeedUpdate(alpha_token)
    assert _chainlink_active_state(mock_chainlink, alpha_token) == active_before


@pytest.mark.parametrize("pending_kind", ["add", "update", "stale", "disable"])
def test_chainlink_expired_pending_action_requires_explicit_cleanup(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
    pending_kind,
):
    with boa.env.anchor():
        _start_chainlink_pending_action(
            pending_kind,
            mock_chainlink,
            alpha_token,
            mock_chainlink_alpha,
            mock_chainlink_bravo,
            governance,
        )
        before = _chainlink_pending_state(mock_chainlink, alpha_token)
        _advance_timelock_blocks(
            mock_chainlink.actionTimeLock() + mock_chainlink.expiration()
        )
        assert mock_chainlink.hasPendingPriceFeedUpdate(alpha_token)

        with boa.reverts("pending feed action"):
            mock_chainlink.updateStaleTime(
                alpha_token, 300, sender=governance.address
            )
        assert _chainlink_pending_state(mock_chainlink, alpha_token) == before

        if pending_kind == "add":
            assert mock_chainlink.cancelNewPendingPriceFeed(
                alpha_token, sender=governance.address
            )
            assert mock_chainlink.addNewPriceFeed(
                alpha_token,
                mock_chainlink_alpha,
                300,
                sender=governance.address,
            )
        elif pending_kind in ("update", "stale"):
            assert mock_chainlink.cancelPriceFeedUpdate(
                alpha_token, sender=governance.address
            )
            assert mock_chainlink.updateStaleTime(
                alpha_token, 600, sender=governance.address
            )
        else:
            assert mock_chainlink.cancelDisablePriceFeed(
                alpha_token, sender=governance.address
            )
            assert mock_chainlink.disablePriceFeed(
                alpha_token, sender=governance.address
            )

        after = _chainlink_pending_state(mock_chainlink, alpha_token)
        assert after[0] != 0
        assert after[0] != before[0]


def test_chainlink_invalid_effective_stale_policies_fail_closed(
    mock_chainlink,
    alpha_token,
    bravo_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
    setGeneralConfig,
    price_desk,
    ripe_hq,
):
    _add_sc20_chainlink_feed(
        mock_chainlink,
        alpha_token,
        mock_chainlink_alpha,
        governance,
        0,
    )
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS
    assert not mock_chainlink.isValidNewFeed(
        bravo_token,
        mock_chainlink_bravo,
        8,
        False,
        False,
        MAX_FEED_STALE_TIME + 1,
    )
    assert not mock_chainlink.isValidStaleTimeUpdate(
        alpha_token, MAX_FEED_STALE_TIME + 1
    )

    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=0)
        assert mock_chainlink.getPrice(alpha_token) == 0
        assert mock_chainlink.getPriceAndHasFeed(alpha_token) == (0, True)

    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=MAX_FEED_STALE_TIME + 1)
        assert mock_chainlink.getPrice(alpha_token) == 0
        assert mock_chainlink.getPriceAndHasFeed(alpha_token) == (0, True)

    with boa.env.anchor():
        ripe_hq.eval("registry.addrInfo[5].addr = empty(address)")
        assert ripe_hq.getAddr(5) == ZERO_ADDRESS
        assert mock_chainlink.getPrice(alpha_token) == 0
        assert mock_chainlink.getPriceAndHasFeed(alpha_token) == (0, True)

    assert mock_chainlink.getPrice(
        alpha_token,
        MAX_FEED_STALE_TIME + 1,
        price_desk.address,
        sender=price_desk.address,
    ) == 0

    for invalid_local in (MIN_LOCAL_STALE_TIME - 1, MAX_FEED_STALE_TIME + 1):
        with boa.env.anchor():
            mock_chainlink.eval(
                f"self.feedConfig[{alpha_token.address}].staleTime = "
                f"{invalid_local}"
            )
            assert mock_chainlink.getPrice(alpha_token) == 0
            assert mock_chainlink.getPriceAndHasFeed(alpha_token) == (0, True)


def test_chainlink_conversion_validation_preserves_legitimate_routes(
    mock_chainlink,
    alpha_token,
    bravo_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    mock_chainlink_charlie,
    mock_chainlink_delta,
    governance,
):
    mock_chainlink_bravo.setMockData(
        2_500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    _add_sc20_chainlink_feed(
        mock_chainlink,
        mock_chainlink.ETH(),
        mock_chainlink_bravo,
        governance,
        3_600,
    )
    mock_chainlink_delta.setMockData(
        50_000 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    _add_sc20_chainlink_feed(
        mock_chainlink,
        mock_chainlink.BTC(),
        mock_chainlink_delta,
        governance,
        3_600,
        refresh_feeds=((mock_chainlink_bravo, 2_500 * CHAINLINK_DECIMALS),),
    )
    mock_chainlink_alpha.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    mock_chainlink_charlie.setMockData(
        500 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )

    assert not mock_chainlink.isValidUpdateFeed(
        mock_chainlink.ETH(),
        mock_chainlink_alpha,
        8,
        True,
        False,
        3_600,
    )
    assert not mock_chainlink.isValidUpdateFeed(
        mock_chainlink.BTC(),
        mock_chainlink_alpha,
        8,
        False,
        True,
        3_600,
    )
    assert not mock_chainlink.isValidNewFeed(
        alpha_token,
        mock_chainlink_alpha,
        8,
        True,
        True,
        3_600,
    )
    assert not mock_chainlink.isValidNewFeed(
        alpha_token,
        mock_chainlink_bravo,
        8,
        True,
        False,
        3_600,
    )
    assert not mock_chainlink.isValidNewFeed(
        alpha_token,
        mock_chainlink_delta,
        8,
        False,
        True,
        3_600,
    )
    assert mock_chainlink.isValidNewFeed(
        alpha_token,
        mock_chainlink_alpha,
        8,
        True,
        False,
        3_600,
    )
    assert mock_chainlink.isValidNewFeed(
        alpha_token,
        mock_chainlink_alpha,
        8,
        False,
        True,
        3_600,
    )

    with boa.env.anchor():
        _add_sc20_chainlink_feed(
            mock_chainlink,
            alpha_token,
            mock_chainlink_alpha,
            governance,
            3_600,
            needs_eth=True,
            refresh_feeds=(
                (mock_chainlink_bravo, 2_500 * CHAINLINK_DECIMALS),
            ),
        )
        assert mock_chainlink.getPrice(alpha_token) == (
            500 * 2_500 * EIGHTEEN_DECIMALS
        )

    with boa.env.anchor():
        _add_sc20_chainlink_feed(
            mock_chainlink,
            alpha_token,
            mock_chainlink_alpha,
            governance,
            3_600,
            needs_btc=True,
            refresh_feeds=(
                (mock_chainlink_delta, 50_000 * CHAINLINK_DECIMALS),
            ),
        )
        assert mock_chainlink.getPrice(alpha_token) == (
            500 * 50_000 * EIGHTEEN_DECIMALS
        )

    # BTC/ETH * direct ETH/USD is a legitimate BTC/USD route, but it cannot
    # then serve as the supposedly direct BTC/USD anchor for another route.
    with boa.env.anchor():
        assert mock_chainlink.updatePriceFeed(
            mock_chainlink.BTC(),
            mock_chainlink_charlie,
            3_600,
            True,
            False,
            sender=governance.address,
        )
        boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
        mock_chainlink_charlie.setMockData(
            500 * CHAINLINK_DECIMALS,
            1,
            1,
            boa.env.timestamp,
            boa.env.timestamp,
        )
        mock_chainlink_bravo.setMockData(
            2_500 * CHAINLINK_DECIMALS,
            1,
            1,
            boa.env.timestamp,
            boa.env.timestamp,
        )
        assert mock_chainlink.confirmPriceFeedUpdate(
            mock_chainlink.BTC(), sender=governance.address
        )
        assert mock_chainlink.getPrice(mock_chainlink.BTC()) == (
            500 * 2_500 * EIGHTEEN_DECIMALS
        )
        assert not mock_chainlink.isValidNewFeed(
            alpha_token,
            mock_chainlink_alpha,
            8,
            False,
            True,
            3_600,
        )

    # ETH/BTC * direct BTC/USD is the symmetric legitimate route.
    with boa.env.anchor():
        assert mock_chainlink.updatePriceFeed(
            mock_chainlink.ETH(),
            mock_chainlink_charlie,
            3_600,
            False,
            True,
            sender=governance.address,
        )
        boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
        mock_chainlink_charlie.setMockData(
            500 * CHAINLINK_DECIMALS,
            1,
            1,
            boa.env.timestamp,
            boa.env.timestamp,
        )
        mock_chainlink_delta.setMockData(
            50_000 * CHAINLINK_DECIMALS,
            1,
            1,
            boa.env.timestamp,
            boa.env.timestamp,
        )
        assert mock_chainlink.confirmPriceFeedUpdate(
            mock_chainlink.ETH(), sender=governance.address
        )
        assert mock_chainlink.getPrice(mock_chainlink.ETH()) == (
            500 * 50_000 * EIGHTEEN_DECIMALS
        )
        assert not mock_chainlink.isValidNewFeed(
            alpha_token,
            mock_chainlink_alpha,
            8,
            True,
            False,
            3_600,
        )


def test_chainlink_legacy_unsafe_conversion_states_fail_closed(
    mock_chainlink,
    alpha_token,
    bravo_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    mock_chainlink_charlie,
    mock_chainlink_delta,
    governance,
):
    _add_sc20_chainlink_feed(
        mock_chainlink,
        mock_chainlink.ETH(),
        mock_chainlink_bravo,
        governance,
        3_600,
    )
    _add_sc20_chainlink_feed(
        mock_chainlink,
        mock_chainlink.BTC(),
        mock_chainlink_delta,
        governance,
        3_600,
        refresh_feeds=((mock_chainlink_bravo, 2_500 * CHAINLINK_DECIMALS),),
    )
    _add_sc20_chainlink_feed(
        mock_chainlink,
        alpha_token,
        mock_chainlink_alpha,
        governance,
        3_600,
        needs_eth=True,
        refresh_feeds=((mock_chainlink_bravo, 2_500 * CHAINLINK_DECIMALS),),
    )
    mock_chainlink_delta.setMockData(
        50_000 * CHAINLINK_DECIMALS,
        1,
        1,
        boa.env.timestamp,
        boa.env.timestamp,
    )
    _add_sc20_chainlink_feed(
        mock_chainlink,
        bravo_token,
        mock_chainlink_charlie,
        governance,
        3_600,
        needs_btc=True,
        refresh_feeds=((mock_chainlink_delta, 50_000 * CHAINLINK_DECIMALS),),
    )
    for feed, price in (
        (mock_chainlink_alpha, 500 * CHAINLINK_DECIMALS),
        (mock_chainlink_charlie, 500 * CHAINLINK_DECIMALS),
        (mock_chainlink_bravo, 2_500 * CHAINLINK_DECIMALS),
        (mock_chainlink_delta, 50_000 * CHAINLINK_DECIMALS),
    ):
        feed.setMockData(
            price, 1, 1, boa.env.timestamp, boa.env.timestamp
        )
    assert mock_chainlink.getPrice(alpha_token) != 0
    assert mock_chainlink.getPrice(bravo_token) != 0

    with boa.env.anchor():
        mock_chainlink.eval(
            f"self.feedConfig[{alpha_token.address}].needsBtcToUsd = True"
        )
        mock_chainlink.eval(
            f"self.feedConfig[{bravo_token.address}].needsEthToUsd = True"
        )
        assert mock_chainlink.getPrice(alpha_token) == 0
        assert mock_chainlink.getPrice(bravo_token) == 0

    with boa.env.anchor():
        mock_chainlink.eval(
            f"self.feedConfig[{alpha_token.address}].feed = "
            f"{mock_chainlink_bravo.address}"
        )
        mock_chainlink.eval(
            f"self.feedConfig[{bravo_token.address}].feed = "
            f"{mock_chainlink_delta.address}"
        )
        assert mock_chainlink.getPrice(alpha_token) == 0
        assert mock_chainlink.getPrice(bravo_token) == 0

    with boa.env.anchor():
        mock_chainlink.eval(
            f"self.feedConfig[{mock_chainlink.ETH()}].needsEthToUsd = True"
        )
        mock_chainlink.eval(
            f"self.feedConfig[{mock_chainlink.BTC()}].needsBtcToUsd = True"
        )
        assert mock_chainlink.getPrice(mock_chainlink.ETH()) == 0
        assert mock_chainlink.getPrice(mock_chainlink.BTC()) == 0

    with boa.env.anchor():
        mock_chainlink.eval(
            f"self.feedConfig[{mock_chainlink.ETH()}].needsBtcToUsd = True"
        )
        assert mock_chainlink.getPrice(mock_chainlink.ETH()) != 0
        assert mock_chainlink.getPrice(alpha_token) == 0

    with boa.env.anchor():
        mock_chainlink.eval(
            f"self.feedConfig[{mock_chainlink.BTC()}].needsEthToUsd = True"
        )
        assert mock_chainlink.getPrice(mock_chainlink.BTC()) != 0
        assert mock_chainlink.getPrice(bravo_token) == 0

    with boa.env.anchor():
        mock_chainlink.eval(
            f"self.feedConfig[{mock_chainlink.ETH()}].needsBtcToUsd = True"
        )
        mock_chainlink.eval(
            f"self.feedConfig[{mock_chainlink.BTC()}].needsEthToUsd = True"
        )
        assert mock_chainlink.getPrice(mock_chainlink.ETH()) == 0
        assert mock_chainlink.getPrice(mock_chainlink.BTC()) == 0
        assert mock_chainlink.getPrice(alpha_token) == 0
        assert mock_chainlink.getPrice(bravo_token) == 0


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


def _assert_feed_config(config, feed, decimals, stale_time, needs_eth=False, needs_btc=False):
    assert config.feed == feed
    assert config.decimals == decimals
    assert config.needsEthToUsd is needs_eth
    assert config.needsBtcToUsd is needs_btc
    assert config.staleTime == stale_time


@pytest.base
def test_base_constructor_eth_btc_metadata_matches_real_feeds(chainlink, fork):
    eth = ADDYS[fork]["ETH"]
    weth = ADDYS[fork]["WETH"]
    btc = ADDYS[fork]["BTC"]
    eth_feed_addr = ADDYS[fork]["CHAINLINK_ETH_USD"]
    btc_feed_addr = ADDYS[fork]["CHAINLINK_BTC_USD"]

    eth_feed = _load_aggregator(eth_feed_addr, "chainlink_eth_usd")
    btc_feed = _load_aggregator(btc_feed_addr, "chainlink_btc_usd")
    eth_price, eth_decimals = _normalized_aggregator_price(eth_feed)
    btc_price, btc_decimals = _normalized_aggregator_price(btc_feed)

    eth_cfg = chainlink.feedConfig(eth)
    weth_cfg = chainlink.feedConfig(weth)
    btc_cfg = chainlink.feedConfig(btc)

    _assert_feed_config(eth_cfg, eth_feed_addr, eth_decimals, 0)
    _assert_feed_config(weth_cfg, eth_feed_addr, eth_decimals, 0)
    _assert_feed_config(btc_cfg, btc_feed_addr, btc_decimals, 0)

    assert chainlink.getPrice(eth) == eth_price
    assert chainlink.getPrice(weth) == eth_price
    assert chainlink.getPrice(btc) == btc_price


@pytest.base
def test_base_eth_weth_btc_direct_and_pricedesk_reads(chainlink, price_desk, fork):
    eth = ADDYS[fork]["ETH"]
    weth = ADDYS[fork]["WETH"]
    btc = ADDYS[fork]["BTC"]

    eth_price = chainlink.getPrice(eth)
    weth_price = chainlink.getPrice(weth)
    btc_price = chainlink.getPrice(btc)

    assert eth_price != 0
    assert weth_price == eth_price
    assert btc_price != 0
    assert chainlink.getPriceAndHasFeed(eth) == (eth_price, True)
    assert chainlink.getPriceAndHasFeed(weth) == (weth_price, True)
    assert chainlink.getPriceAndHasFeed(btc) == (btc_price, True)

    assert price_desk.getPrice(eth) == eth_price
    assert price_desk.getPrice(weth) == weth_price
    assert price_desk.getPrice(btc) == btc_price


@pytest.base
def test_base_usdc_usd_propose_confirm_cached_decimals_and_pricedesk(
    chainlink,
    price_desk,
    governance,
    fork,
    charlie_token,
):
    usdc = CORE_TOKENS[fork]["USDC"]
    feed_addr = ADDYS[fork]["CHAINLINK_USDC_USD"]
    feed = _load_aggregator(feed_addr, "chainlink_usdc_usd")
    expected_price, expected_decimals = _normalized_aggregator_price(feed)

    # Session chainlink starts without USDC. Curve/green-ref usdc_token
    # fixtures in the same pytest process may already have admitted it.
    if not chainlink.hasPriceFeed(usdc):
        assert chainlink.addNewPriceFeed(
            usdc, feed_addr, 0, False, False, sender=governance.address
        )
        pending_usdc = chainlink.pendingUpdates(usdc).config
        _assert_feed_config(pending_usdc, feed_addr, expected_decimals, 0)
        _advance_timelock_blocks(chainlink.actionTimeLock() + 1)
        assert chainlink.confirmNewPriceFeed(usdc, sender=governance.address)

    stored = chainlink.feedConfig(usdc)
    _assert_feed_config(stored, feed_addr, expected_decimals, 0)
    usdc_price = chainlink.getPrice(usdc)
    assert usdc_price == expected_price
    assert usdc_price != 0
    assert chainlink.getPriceAndHasFeed(usdc) == (expected_price, True)
    assert price_desk.getPrice(usdc) == expected_price

    # This-file governance path for the USDC/USD aggregator.
    assert not chainlink.hasPriceFeed(charlie_token)
    assert chainlink.addNewPriceFeed(
        charlie_token, feed_addr, 0, False, False, sender=governance.address
    )
    pending = chainlink.pendingUpdates(charlie_token).config
    _assert_feed_config(pending, feed_addr, expected_decimals, 0)
    _advance_timelock_blocks(chainlink.actionTimeLock() + 1)
    assert chainlink.confirmNewPriceFeed(charlie_token, sender=governance.address)
    stored_probe = chainlink.feedConfig(charlie_token)
    _assert_feed_config(
        stored_probe,
        pending.feed,
        pending.decimals,
        pending.staleTime,
        pending.needsEthToUsd,
        pending.needsBtcToUsd,
    )
    assert chainlink.getPrice(charlie_token) == expected_price
    assert price_desk.getPrice(charlie_token) == expected_price
