import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, ONE_YEAR, ONE_DAY_IN_SECS
from conf_utils import filter_logs
from config.BluePrint import PARAMS, ADDYS


@pytest.fixture(scope="module")
def mock_chainlink_alpha(governance):
    return boa.load(
        "contracts/mock/MockChainlinkFeed.vy",
        500 * EIGHTEEN_DECIMALS,  # $500
        governance,
    )


@pytest.fixture(scope="module")
def mock_chainlink_bravo(governance):
    return boa.load(
        "contracts/mock/MockChainlinkFeed.vy",
        2_500 * EIGHTEEN_DECIMALS,  # ETH, 18 decimals, $2500
        governance,
    )


@pytest.fixture(scope="module")
def mock_chainlink_charlie(governance):
    return boa.load(
        "contracts/mock/MockChainlinkFeed.vy",
        EIGHTEEN_DECIMALS,  # USDC, 6 decimals, $1
        governance,
    )


@pytest.fixture(scope="module")
def mock_chainlink_delta(governance):
    return boa.load(
        "contracts/mock/MockChainlinkFeed.vy",
        50_000 * EIGHTEEN_DECIMALS,  # WBTC, 8 decimals, $50,000
        governance,
    )


@pytest.fixture(scope="module")
def mock_chainlink(ripe_hq, fork):
    CHAINLINK_ETH_USD = ZERO_ADDRESS if fork == "local" else ADDYS[fork]["CHAINLINK_ETH_USD"]
    CHAINLINK_BTC_USD = ZERO_ADDRESS if fork == "local" else ADDYS[fork]["CHAINLINK_BTC_USD"]
    c = boa.load(
        "contracts/priceSources/ChainlinkPrices.vy",
        ripe_hq,
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
        ADDYS[fork]["WETH"],
        ADDYS[fork]["ETH"],
        ADDYS[fork]["BTC"],
        CHAINLINK_ETH_USD,
        CHAINLINK_BTC_USD,
        name="chainlink",
    )
    assert c.setActionTimeLockAfterSetup(sender=ripe_hq.governance())
    return c


CHAINLINK_DECIMALS = 10 ** 8

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
    mock_chainlink_alpha.setMockData(0, sender=governance.address)  # Set price to 0
    assert mock_chainlink_alpha.latestRoundData().answer == 0
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Reset mock data
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, sender=governance.address)

    # Test successful feed addition
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "NewChainlinkFeedPending")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_alpha.address
    assert not log.needsEthToUsd
    assert not log.needsBtcToUsd

    # Test confirming before time lock
    with boa.reverts("time lock not reached"):
        mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Travel past time lock
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)

    # Test confirming
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "NewChainlinkFeedAdded")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_alpha.address
    assert not log.needsEthToUsd
    assert not log.needsBtcToUsd

    # Verify feed is active
    assert mock_chainlink.hasPriceFeed(alpha_token)
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS

    # Test canceling non-existent feed
    with boa.reverts("cannot cancel action"):
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
    # Add feed
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "NewChainlinkFeedPending")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_alpha.address
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
    mock_chainlink_delta,  # BTC feed
    governance,
):
    # Add ETH feed first
    assert mock_chainlink.addNewPriceFeed(mock_chainlink.ETH(), mock_chainlink_bravo, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmNewPriceFeed(mock_chainlink.ETH(), sender=governance.address)

    # Add feed with ETH conversion
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, True, False, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "NewChainlinkFeedPending")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_alpha.address
    assert log.needsEthToUsd
    assert not log.needsBtcToUsd

    # Confirm feed
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Verify price with ETH conversion
    # mock_chainlink_alpha price: 500 * CHAINLINK_DECIMALS
    # mock_chainlink_bravo price: 2500 * CHAINLINK_DECIMALS
    expected_price = 500 * 2500 * EIGHTEEN_DECIMALS
    assert mock_chainlink.getPrice(alpha_token) == expected_price

    # Add BTC feed
    assert mock_chainlink.addNewPriceFeed(mock_chainlink.BTC(), mock_chainlink_delta, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmNewPriceFeed(mock_chainlink.BTC(), sender=governance.address)

    # Update feed with BTC conversion using a different feed
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_delta, False, True, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "ChainlinkFeedUpdatePending")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_delta.address
    assert not log.needsEthToUsd
    assert log.needsBtcToUsd

    # Confirm update
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    # Verify price with BTC conversion
    # mock_chainlink_delta price: 50000 * CHAINLINK_DECIMALS
    # mock_chainlink_delta price: 50000 * CHAINLINK_DECIMALS
    expected_price = 50000 * 50000 * EIGHTEEN_DECIMALS
    assert mock_chainlink.getPrice(alpha_token) == expected_price

    # Test invalid conversion (both ETH and BTC)
    with boa.reverts("invalid feed"):
        mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_delta, True, True, sender=governance.address)


def test_chainlink_update_price_feed(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
    bob,
):
    # Add initial feed
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
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
    mock_chainlink_bravo.setMockData(0, sender=governance.address)  # Set price to 0
    with boa.reverts("invalid feed"):
        mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)

    # Reset mock data
    mock_chainlink_bravo.setMockData(1000 * CHAINLINK_DECIMALS, sender=governance.address)

    # Test successful update
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "ChainlinkFeedUpdatePending")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_bravo.address
    assert not log.needsEthToUsd
    assert not log.needsBtcToUsd

    # Test confirming before time lock
    with boa.reverts("time lock not reached"):
        mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    # Travel past time lock
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)

    # Test confirming
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "ChainlinkFeedUpdated")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_bravo.address
    assert not log.needsEthToUsd
    assert not log.needsBtcToUsd

    # Verify feed is updated
    assert mock_chainlink.hasPriceFeed(alpha_token)
    assert mock_chainlink.getPrice(alpha_token) == 1000 * EIGHTEEN_DECIMALS

    # Test canceling non-existent update
    with boa.reverts("cannot cancel action"):
        mock_chainlink.cancelPriceFeedUpdate(alpha_token, sender=governance.address)


def test_chainlink_update_price_feed_cancel(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
):
    # Add initial feed
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Start update
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)

    # Verify event
    log = filter_logs(mock_chainlink, "ChainlinkFeedUpdatePending")[0]
    assert log.asset == alpha_token.address
    assert log.feed == mock_chainlink_bravo.address
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
    # Add initial feed
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
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
    with boa.reverts("cannot cancel action"):
        mock_chainlink.cancelDisablePriceFeed(alpha_token, sender=governance.address)


def test_chainlink_disable_price_feed_cancel(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    governance,
):
    # Add initial feed
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
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


def test_chainlink_price_stale(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    governance,
):
    # Add feed
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Refresh the feed's updatedAt to current block.timestamp
    mock_chainlink_alpha.setMockData(500 * 10**8, sender=governance.address)

    # Test price with no stale time
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS

    # Test price with stale time (not stale yet)
    assert mock_chainlink.getPrice(alpha_token, 1) == 500 * EIGHTEEN_DECIMALS

    # Make price stale by advancing time
    boa.env.time_travel(seconds=2)  # Advance 2 seconds, making price stale for _staleTime=1
    assert mock_chainlink.getPrice(alpha_token, 1) == 0  # Price should be 0 when stale


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
    # Test with 8 decimals (default)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS

    # Test with 6 decimals
    mock_chainlink_bravo.setDecimals(6)
    mock_chainlink_bravo.setMockData(500 * 10**6, sender=governance.address)  # Set price to 500 with 6 decimals
    assert mock_chainlink.addNewPriceFeed(bravo_token, mock_chainlink_bravo, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmNewPriceFeed(bravo_token, sender=governance.address)
    assert mock_chainlink.getPrice(bravo_token) == 500 * EIGHTEEN_DECIMALS

    # Test with 18 decimals
    mock_chainlink_charlie.setDecimals(18)
    # Set price to 500 with 18 decimals
    mock_chainlink_charlie.setMockData(500 * EIGHTEEN_DECIMALS, sender=governance.address)
    assert mock_chainlink.addNewPriceFeed(charlie_token, mock_chainlink_charlie, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
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
    mock_chainlink_alpha.setMockData(0, sender=governance.address)
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Test price with negative price
    mock_chainlink_alpha.setMockData(-1, sender=governance.address)
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Test price with too many decimals
    mock_chainlink_bravo.setDecimals(20)  # Set decimals to 20 (invalid)
    mock_chainlink_bravo.setMockData(500 * 10**20, sender=governance.address)  # Set price with 20 decimals
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(bravo_token, mock_chainlink_bravo, sender=governance.address)


def test_chainlink_price_feed_edge_cases(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
):
    # Test with maximum valid decimals (18)
    mock_chainlink_alpha.setDecimals(18)
    mock_chainlink_alpha.setMockData(500 * EIGHTEEN_DECIMALS, sender=governance.address)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)
    assert mock_chainlink.getPrice(alpha_token) == 500 * EIGHTEEN_DECIMALS

    # Test with minimum valid decimals (1) using a different feed
    mock_chainlink_bravo.setDecimals(1)
    mock_chainlink_bravo.setMockData(5, sender=governance.address)  # 5 with 1 decimal = 0.5
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    assert mock_chainlink.getPrice(alpha_token) == 5 * 10**17  # 0.5 * 10**18

    # Test with very large price (use a new feed)
    mock_chainlink_alpha.setDecimals(8)
    mock_chainlink_alpha.setMockData(2**128 - 1, sender=governance.address)  # Very large price
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    assert mock_chainlink.getPrice(alpha_token) == (2**128 - 1) * 10**10  # Normalized to 18 decimals

    # Test with very small price (near 0 but not 0)
    mock_chainlink_bravo.setDecimals(8)
    mock_chainlink_bravo.setMockData(1, sender=governance.address)  # 1 with 8 decimals = 0.00000001
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    assert mock_chainlink.getPrice(alpha_token) == 10**10  # 0.00000001 * 10**18


def test_chainlink_stale_price_edge_cases(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    governance,
):
    # Add feed
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Refresh the feed's updatedAt to current block.timestamp
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, sender=governance.address)

    # Test price exactly at stale time boundary (should still be valid)
    assert mock_chainlink.getPrice(alpha_token, 1) == 500 * EIGHTEEN_DECIMALS
    boa.env.time_travel(seconds=2)  # Advance by _staleTime + 1
    assert mock_chainlink.getPrice(alpha_token, 1) == 0  # Price should be stale

    # Test price just before stale time boundary
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, sender=governance.address)
    assert mock_chainlink.getPrice(alpha_token, 2) == 500 * EIGHTEEN_DECIMALS
    boa.env.time_travel(seconds=1)
    assert mock_chainlink.getPrice(alpha_token, 2) == 500 * EIGHTEEN_DECIMALS  # Price should not be stale

    # Test multiple stale checks in sequence
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, sender=governance.address)
    assert mock_chainlink.getPrice(alpha_token, 1) == 500 * EIGHTEEN_DECIMALS
    boa.env.time_travel(seconds=2)
    assert mock_chainlink.getPrice(alpha_token, 1) == 0  # First stale check
    assert mock_chainlink.getPrice(alpha_token, 1) == 0  # Second stale check

    # Test with maximum uint256 stale time
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, sender=governance.address)
    assert mock_chainlink.getPrice(alpha_token, 2**256 - 1) == 500 * EIGHTEEN_DECIMALS
    boa.env.time_travel(seconds=1)
    assert mock_chainlink.getPrice(alpha_token, 2**256 - 1) == 500 * EIGHTEEN_DECIMALS  # Price should not be stale

    # Test with zero stale time
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, sender=governance.address)
    assert mock_chainlink.getPrice(alpha_token, 0) == 500 * EIGHTEEN_DECIMALS
    boa.env.time_travel(seconds=1)
    assert mock_chainlink.getPrice(alpha_token, 0) == 500 * EIGHTEEN_DECIMALS  # Price should not be stale


def test_chainlink_time_lock_edge_cases(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
):
    # Test confirming just before time lock boundary
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() - 1)
    with boa.reverts("time lock not reached"):
        mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test confirming at time lock boundary
    boa.env.time_travel(blocks=1)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test multiple time lock actions in sequence (use a different feed for update)
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    assert mock_chainlink.disablePriceFeed(alpha_token, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmDisablePriceFeed(alpha_token, sender=governance.address)

    # Test with maximum allowed time lock (use a reasonable value)
    mock_chainlink.setActionTimeLock(302400, sender=governance.address)  # 7 days in blocks
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=302400)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test with minimum allowed time lock
    mock_chainlink.setActionTimeLock(21600, sender=governance.address)  # 12 hours in blocks
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)
    boa.env.time_travel(blocks=21600)
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)


def test_chainlink_governance_edge_cases(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    mock_chainlink_bravo,
    governance,
    switchboard_alpha,
):
    # Test multiple governance actions in sequence
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    assert mock_chainlink.cancelNewPendingPriceFeed(alpha_token, sender=governance.address)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)
    assert mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_bravo, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    # Test governance actions during pause (using MissionControl address)
    mock_chainlink.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    with boa.reverts("contract paused"):
        mock_chainlink.updatePriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    with boa.reverts("contract paused"):
        mock_chainlink.disablePriceFeed(alpha_token, sender=governance.address)

    # Test governance actions after pause
    mock_chainlink.pause(False, sender=switchboard_alpha.address)
    # First disable the existing feed
    assert mock_chainlink.disablePriceFeed(alpha_token, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    assert mock_chainlink.confirmDisablePriceFeed(alpha_token, sender=governance.address)
    # Now we can add a new feed
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)


def test_chainlink_price_feed_round_validation(
    mock_chainlink,
    alpha_token,
    mock_chainlink_alpha,
    governance,
):
    """Test validation of price feed round IDs"""
    # Test with zero round ID
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 0, 1, 1, 1, sender=governance.address)
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Test with answeredInRound < roundId
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 2, 1, 1, 1, sender=governance.address)
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Test with valid round data
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, 1, 1, sender=governance.address)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
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
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, 1, current_time + 1000, sender=governance.address)
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # set stale time to 1 day
    aid = switchboard_alpha.setStaleTime(ONE_DAY_IN_SECS, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock() + 1)
    assert switchboard_alpha.executePendingAction(aid, sender=governance.address)
    assert mission_control.getPriceStaleTime() == ONE_DAY_IN_SECS

    # Test with old timestamp
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, 1, current_time -
                                     (ONE_DAY_IN_SECS * 2), sender=governance.address)
    with boa.reverts("invalid feed"):
        mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)

    # Test with valid timestamp
<<<<<<< HEAD
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, 1, current_time, sender=governance.address)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, 1,
                                     boa.env.evm.patch.timestamp, sender=governance.address)
=======
    # Need to set timestamp to current time since validation happens immediately
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, 1, boa.env.evm.patch.timestamp)
    assert mock_chainlink.addNewPriceFeed(alpha_token, mock_chainlink_alpha, sender=governance.address)
    boa.env.time_travel(blocks=mock_chainlink.actionTimeLock() + 1)
    # Update timestamp again for confirmation validation
    mock_chainlink_alpha.setMockData(500 * CHAINLINK_DECIMALS, 1, 1, 1, boa.env.evm.patch.timestamp)
>>>>>>> master
    assert mock_chainlink.confirmNewPriceFeed(alpha_token, sender=governance.address)
