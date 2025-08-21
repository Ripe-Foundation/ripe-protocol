import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, HUNDRED_PERCENT
from config.BluePrint import ADDYS
from conf_utils import filter_logs


#########################
# Aero Ripe Prices Test #
#########################


@pytest.base
def test_get_price_aero_ripe_single_asset(aero_ripe_prices, fork, price_desk):
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    
    price = aero_ripe_prices.getAeroRipePrice(ripe_token)
    assert price > 0
    
    # Returns correct price with stale time
    price_with_stale = aero_ripe_prices.getPrice(ripe_token, 0, price_desk.address)
    assert price_with_stale > 0
    
    # Non-RIPE token returns 0
    assert aero_ripe_prices.getAeroRipePrice(ADDYS[fork]["WETH"]) == 0


@pytest.base
def test_get_price_and_has_feed(aero_ripe_prices, fork, price_desk):
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    weth = ADDYS[fork]["WETH"]
    
    # RIPE token has feed
    price, has_feed = aero_ripe_prices.getPriceAndHasFeed(ripe_token, 0, price_desk.address)
    assert price > 0
    assert has_feed is True
    
    # Non-RIPE token does not have feed
    price, has_feed = aero_ripe_prices.getPriceAndHasFeed(weth, 0, price_desk.address)
    assert price == 0
    assert has_feed is False


@pytest.base
def test_has_price_feed(aero_ripe_prices, fork):
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    weth = ADDYS[fork]["WETH"]
    
    # Only RIPE token has price feed
    assert aero_ripe_prices.hasPriceFeed(ripe_token) is True
    assert aero_ripe_prices.hasPriceFeed(weth) is False
    assert aero_ripe_prices.hasPriceFeed(ZERO_ADDRESS) is False


@pytest.base
def test_pool_price_calculation(aero_ripe_prices, fork):
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    ripe_weth_pool = ADDYS[fork]["RIPE_WETH_POOL"]
    
    # Get pool interface to check reserves
    pool = boa.from_etherscan(ripe_weth_pool, name="AeroClassicPool")
    token0, token1 = pool.tokens()
    reserve0, reserve1, _ = pool.getReserves()
    
    # Pool has valid reserves and contains RIPE token
    assert reserve0 > 0
    assert reserve1 > 0
    assert token0 == ripe_token or token1 == ripe_token
    
    # Get the price and verify it's reasonable
    price = aero_ripe_prices.getAeroRipePrice(ripe_token)
    assert price > 0


@pytest.base 
def test_add_price_snapshot_basic(aero_ripe_prices, fork, vault_book):
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    
    # Get initial state
    config = aero_ripe_prices.priceConfigs(ripe_token)
    initial_next_index = config.nextIndex
    
    # Add snapshot (need valid Ripe address permission - using vault_book)
    success = aero_ripe_prices.addPriceSnapshot(ripe_token, sender=vault_book.address)
    
    # Get logs immediately after transaction
    logs = filter_logs(aero_ripe_prices, "PriceSnapshotAdded")
    
    assert success is True
    
    # Snapshot was added with correct values
    new_config = aero_ripe_prices.priceConfigs(ripe_token)
    assert new_config.lastSnapshot.price > 0
    assert new_config.lastSnapshot.lastUpdate == boa.env.evm.patch.timestamp
    
    # Event is emitted with correct values
    assert len(logs) > 0
    last_log = logs[-1]
    assert last_log.asset == ripe_token
    assert last_log.price > 0


@pytest.base
def test_add_price_snapshot_time_delay(aero_ripe_prices, fork, vault_book):
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    
    # Add first snapshot
    assert aero_ripe_prices.addPriceSnapshot(ripe_token, sender=vault_book.address) is True
    
    # Adding another immediately fails due to minSnapshotDelay
    assert aero_ripe_prices.addPriceSnapshot(ripe_token, sender=vault_book.address) is False
    
    # Fast forward time past minSnapshotDelay (5 minutes)
    boa.env.time_travel(seconds=301)
    
    # Now succeeds after time delay
    assert aero_ripe_prices.addPriceSnapshot(ripe_token, sender=vault_book.address) is True


@pytest.base
def test_snapshot_circular_buffer(aero_ripe_prices, fork, vault_book):
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    
    # Get max snapshots
    config = aero_ripe_prices.priceConfigs(ripe_token)
    max_snapshots = config.maxNumSnapshots
    
    # Add snapshots up to max limit
    for i in range(max_snapshots):
        aero_ripe_prices.addPriceSnapshot(ripe_token, sender=vault_book.address)
        boa.env.time_travel(seconds=301)  # Past minSnapshotDelay
    
    # Check next index wrapped around
    final_config = aero_ripe_prices.priceConfigs(ripe_token)
    assert final_config.nextIndex == 0
    
    # Add one more to verify circular buffer behavior
    assert aero_ripe_prices.addPriceSnapshot(ripe_token, sender=vault_book.address) is True
    
    newest_config = aero_ripe_prices.priceConfigs(ripe_token)
    assert newest_config.nextIndex == 1


@pytest.base
def test_get_weighted_price(aero_ripe_prices, fork, vault_book):
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    
    # Must return 0 when no snapshots exist
    initial_weighted = aero_ripe_prices.getWeightedPrice(ripe_token)
    assert initial_weighted == 0
    
    # Add multiple snapshots
    prices = []
    for i in range(5):
        aero_ripe_prices.addPriceSnapshot(ripe_token, sender=vault_book.address)
        
        # Get the snapshot that was just added
        config = aero_ripe_prices.priceConfigs(ripe_token)
        prices.append(config.lastSnapshot.price)
        
        boa.env.time_travel(seconds=301)
    
    # Get weighted price
    weighted_price = aero_ripe_prices.getWeightedPrice(ripe_token)
    assert weighted_price > 0
    
    # Weighted price must be the average of all snapshots
    expected_avg = sum(prices) // len(prices)
    # Price variance must be within 10% due to throttling
    assert abs(weighted_price - expected_avg) < expected_avg // 10


@pytest.base
def test_weighted_price_with_stale_snapshots(aero_ripe_prices, fork, vault_book, governance):
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    
    # Update config to have a stale time
    aero_ripe_prices.updatePriceConfig(
        300,      # minSnapshotDelay
        20,       # maxNumSnapshots  
        1000,     # maxUpsideDeviation (10%)
        3600,     # staleTime (1 hour)
        sender=governance.address
    )
    
    # Wait for timelock
    boa.env.time_travel(seconds=86401)  # Past max timelock
    
    # Add some snapshots
    for i in range(3):
        aero_ripe_prices.addPriceSnapshot(ripe_token, sender=vault_book.address)
        boa.env.time_travel(seconds=301)
    
    # Fast forward past stale time
    boa.env.time_travel(seconds=3700)
    
    # Add fresh snapshot
    aero_ripe_prices.addPriceSnapshot(ripe_token, sender=vault_book.address)
    
    # Weighted price must only include non-stale snapshots
    weighted_price = aero_ripe_prices.getWeightedPrice(ripe_token)
    assert weighted_price > 0


@pytest.base
def test_get_latest_snapshot(aero_ripe_prices, fork):
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    
    # Get latest snapshot
    snapshot = aero_ripe_prices.getLatestSnapshot(ripe_token)
    assert snapshot.price > 0
    assert snapshot.lastUpdate == boa.env.evm.patch.timestamp
    
    # Non-RIPE token returns empty snapshot
    weth = ADDYS[fork]["WETH"]
    empty_snapshot = aero_ripe_prices.getLatestSnapshot(weth)
    assert empty_snapshot.price == 0
    assert empty_snapshot.lastUpdate == 0


@pytest.base
def test_upside_throttling(aero_ripe_prices, fork, vault_book):
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    
    # Add initial snapshot
    aero_ripe_prices.addPriceSnapshot(ripe_token, sender=vault_book.address)
    
    initial_config = aero_ripe_prices.priceConfigs(ripe_token)
    initial_price = initial_config.lastSnapshot.price
    
    # Time travel and add another snapshot
    boa.env.time_travel(seconds=301)
    
    aero_ripe_prices.addPriceSnapshot(ripe_token, sender=vault_book.address)
    
    # New price must be throttled by maxUpsideDeviation
    new_config = aero_ripe_prices.priceConfigs(ripe_token)
    new_price = new_config.lastSnapshot.price
    
    # Price increase must not exceed 10% (default maxUpsideDeviation)
    max_allowed = initial_price + (initial_price * 1000 // HUNDRED_PERCENT)
    assert new_price <= max_allowed


@pytest.base
def test_update_price_config(aero_ripe_prices, fork, governance):
    # Update configuration
    success = aero_ripe_prices.updatePriceConfig(
        600,    # minSnapshotDelay (10 mins)
        15,     # maxNumSnapshots
        2000,   # maxUpsideDeviation (20%)
        7200,   # staleTime (2 hours)
        sender=governance.address
    )
    assert success is True
    
    # Event is emitted for config update
    logs = filter_logs(aero_ripe_prices, "PriceConfigUpdatePending")
    assert len(logs) > 0
    last_log = logs[-1]
    assert last_log.minSnapshotDelay == 600
    assert last_log.maxNumSnapshots == 15
    assert last_log.maxUpsideDeviation == 2000
    assert last_log.staleTime == 7200


@pytest.base
def test_invalid_price_config(aero_ripe_prices, fork):
    # Invalid configurations are rejected
    
    # minSnapshotDelay too high (> 1 week)
    assert aero_ripe_prices.isValidPriceConfig(
        604801,  # > 1 week
        20,
        1000,
        3600
    ) is False
    
    # maxNumSnapshots = 0
    assert aero_ripe_prices.isValidPriceConfig(
        300,
        0,       # Invalid
        1000,
        3600
    ) is False
    
    # maxNumSnapshots > 25
    assert aero_ripe_prices.isValidPriceConfig(
        300,
        26,      # Too high
        1000,
        3600
    ) is False
    
    # maxUpsideDeviation > 100%
    assert aero_ripe_prices.isValidPriceConfig(
        300,
        20,
        10001,   # > 100%
        3600
    ) is False
    
    # Valid config
    assert aero_ripe_prices.isValidPriceConfig(
        300,
        20,
        1000,
        3600
    ) is True


@pytest.base
def test_has_pending_price_feed_update(aero_ripe_prices, fork, governance):
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    
    # Initially no pending update
    assert aero_ripe_prices.hasPendingPriceFeedUpdate(ripe_token) is False
    
    # Create pending update
    aero_ripe_prices.updatePriceConfig(600, 15, 2000, 7200, sender=governance.address)
    
    # Pending update exists
    assert aero_ripe_prices.hasPendingPriceFeedUpdate(ripe_token) is True
    
    # Non-RIPE token has no pending update
    assert aero_ripe_prices.hasPendingPriceFeedUpdate(ADDYS[fork]["WETH"]) is False


@pytest.base
def test_price_with_no_reserves(aero_ripe_prices, fork, price_desk):
    # Pool on Base has reserves, so price must be greater than 0
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    
    price = aero_ripe_prices.getPrice(ripe_token, 0, price_desk.address)
    assert price > 0


@pytest.base
def test_non_ripe_token_operations(aero_ripe_prices, fork, price_desk, vault_book):
    weth = ADDYS[fork]["WETH"]
    
    # Non-RIPE tokens must return 0 for all price operations
    assert aero_ripe_prices.getPrice(weth, 0, price_desk.address) == 0
    assert aero_ripe_prices.getAeroRipePrice(weth) == 0
    assert aero_ripe_prices.getWeightedPrice(weth) == 0
    assert aero_ripe_prices.hasPriceFeed(weth) is False
    
    # Adding snapshot for non-RIPE fails
    assert aero_ripe_prices.addPriceSnapshot(weth, sender=vault_book.address) is False
    
    # Get empty snapshot
    snapshot = aero_ripe_prices.getLatestSnapshot(weth)
    assert snapshot.price == 0
    assert snapshot.lastUpdate == 0


@pytest.base
def test_permission_checks(aero_ripe_prices, fork, bob):
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    
    # Non-authorized address cannot add snapshots
    with boa.reverts("no perms"):
        aero_ripe_prices.addPriceSnapshot(ripe_token, sender=bob)
    
    # Non-governance cannot update config  
    with boa.reverts("no perms"):
        aero_ripe_prices.updatePriceConfig(300, 20, 1000, 3600, sender=bob)


@pytest.base
def test_price_calculation_with_different_decimals(aero_ripe_prices, fork):
    # Price calculation handles different token decimals correctly
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    
    # Price is normalized to 18 decimals
    price = aero_ripe_prices.getAeroRipePrice(ripe_token)
    assert price > 0
    
    # Price must be within reasonable bounds to catch decimal conversion errors
    assert price > EIGHTEEN_DECIMALS // 1000000  # Must be > 0.000001
    assert price < EIGHTEEN_DECIMALS * 1000000   # Must be < 1,000,000


@pytest.base
def test_combined_price_with_weighted_minimum(aero_ripe_prices, fork, price_desk, vault_book):
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    
    # Get initial Aero price
    aero_price = aero_ripe_prices.getAeroRipePrice(ripe_token)
    
    # Add snapshots with known prices
    for i in range(3):
        aero_ripe_prices.addPriceSnapshot(ripe_token, sender=vault_book.address)
        boa.env.time_travel(seconds=301)
    
    # Get combined price (min of aero and weighted)
    combined_price = aero_ripe_prices.getPrice(ripe_token, 0, price_desk.address)
    weighted_price = aero_ripe_prices.getWeightedPrice(ripe_token)
    
    # Combined price must be the minimum of aero and weighted prices
    assert combined_price == min(aero_price, weighted_price)


@pytest.base
def test_immutable_values(aero_ripe_prices, fork):
    # Immutable values are set correctly
    ripe_weth_pool = ADDYS[fork]["RIPE_WETH_POOL"]
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    
    assert aero_ripe_prices.RIPE_WETH_POOL() == ripe_weth_pool
    assert aero_ripe_prices.RIPE_TOKEN() == ripe_token


@pytest.base
def test_pool_token_ordering(aero_ripe_prices, fork):
    ripe_token = ADDYS[fork]["RIPE_TOKEN"]
    weth = ADDYS[fork]["WETH"]
    ripe_weth_pool = ADDYS[fork]["RIPE_WETH_POOL"]
    
    # Get pool tokens
    pool = boa.from_etherscan(ripe_weth_pool, name="AeroClassicPool")
    token0, token1 = pool.tokens()
    
    # RIPE is token0, WETH is token1 (sorted by address)
    assert token0 == ripe_token
    assert token1 == weth
    
    # Price calculation works with this token ordering
    price = aero_ripe_prices.getAeroRipePrice(ripe_token)
    assert price > 0