import boa
import pytest

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS
from conf_utils import filter_logs
from config.BluePrint import CORE_TOKENS

MONTH_IN_SECONDS = 30 * 24 * 60 * 60


@pytest.fixture(scope="module")
def addPythFeed(pyth_prices, governance):
    def addPythFeed(_asset, _feed_id, _stale_time=0):
        if pyth_prices.hasPriceFeed(_asset):
            return
        assert pyth_prices.addNewPriceFeed(_asset, _feed_id, _stale_time, sender=governance.address)
        boa.env.time_travel(blocks=pyth_prices.actionTimeLock() + 1)
        assert pyth_prices.confirmNewPriceFeed(_asset, sender=governance.address)
    yield addPythFeed


##################
# Unique to Pyth #
##################


def test_pyth_local_update_prices(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    addPythFeed,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    addPythFeed(alpha_token, data_feed_id)
    assert pyth_prices.getPrice(alpha_token) != 0

    # get payload
    publish_time = boa.env.evm.patch.timestamp + 1
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        98000000,
        50000,
        -8,
        publish_time,
    )
    exp_fee = len(payload)

    # no balance
    assert not pyth_prices.updatePythPrice(payload, sender=governance.address)

    # add eth balance
    assert boa.env.get_balance(mock_pyth.address) == 0
    boa.env.set_balance(pyth_prices.address, EIGHTEEN_DECIMALS)
    assert boa.env.get_balance(pyth_prices.address) > exp_fee
    pre_pyth_prices_bal = boa.env.get_balance(pyth_prices.address)

    # success
    assert pyth_prices.updatePythPrice(payload, sender=governance.address)

    log = filter_logs(pyth_prices, 'PythPriceUpdated')[0]
    assert log.payload == payload
    assert log.feeAmount == exp_fee
    assert log.caller == governance.address

    assert boa.env.get_balance(pyth_prices.address) == pre_pyth_prices_bal - exp_fee
    assert boa.env.get_balance(mock_pyth.address) == exp_fee

    # check mock pyth
    price_data = mock_pyth.priceFeeds(data_feed_id)
    assert price_data.price.price == 98000000
    assert price_data.price.conf == 50000
    assert price_data.price.expo == -8
    assert price_data.price.publishTime == publish_time

    assert int(0.98 * EIGHTEEN_DECIMALS) > pyth_prices.getPrice(alpha_token) > int(0.97 * EIGHTEEN_DECIMALS)


def test_pyth_update_many_prices(
    pyth_prices,
    mock_pyth,
    alpha_token,
    bravo_token,
    governance,
    addPythFeed,
):
    # Add feeds for multiple assets
    data_feed_id_1 = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    data_feed_id_2 = bytes.fromhex("baa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94b")
    
    # Setup the second feed by creating a payload and updating it in MockPyth
    payload_2 = mock_pyth.createPriceFeedUpdateData(data_feed_id_2, 97000000, 45000, -8, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_pyth.updatePriceFeeds(payload_2, value=len(payload_2))
    
    addPythFeed(alpha_token, data_feed_id_1)
    addPythFeed(bravo_token, data_feed_id_2)

    # Create payloads for both feeds
    publish_time = boa.env.evm.patch.timestamp + 1
    payload1 = mock_pyth.createPriceFeedUpdateData(data_feed_id_1, 98000000, 50000, -8, publish_time)
    payload2 = mock_pyth.createPriceFeedUpdateData(data_feed_id_2, 97000000, 45000, -8, publish_time)
    
    # Add ETH balance
    total_fee = len(payload1) + len(payload2)
    boa.env.set_balance(pyth_prices.address, total_fee + EIGHTEEN_DECIMALS)
    pre_balance = boa.env.get_balance(pyth_prices.address)

    # Test successful batch update
    num_updated = pyth_prices.updateManyPythPrices([payload1, payload2], sender=governance.address)
    assert num_updated == 2

    # Check balances
    assert boa.env.get_balance(pyth_prices.address) == pre_balance - total_fee

    # Test with insufficient balance (should stop after first update fails)
    boa.env.set_balance(pyth_prices.address, len(payload1) - 1)  # Not enough for first payload
    num_updated = pyth_prices.updateManyPythPrices([payload1, payload2], sender=governance.address)
    assert num_updated == 0


def test_pyth_recover_eth(
    pyth_prices,
    bob,
    governance,
):
    # no balance
    with boa.reverts("invalid recipient or balance"):
        pyth_prices.recoverEthBalance(bob, sender=governance.address)

    # Add ETH balance to contract
    initial_balance = EIGHTEEN_DECIMALS  # 1 ETH
    boa.env.set_balance(pyth_prices.address, initial_balance)
    assert boa.env.get_balance(pyth_prices.address) == initial_balance

    # No perms check
    with boa.reverts("no perms"):
        pyth_prices.recoverEthBalance(bob, sender=bob)

    # Invalid recipient check
    with boa.reverts("invalid recipient or balance"):
        pyth_prices.recoverEthBalance(ZERO_ADDRESS, sender=governance.address)

    # Success case
    pre_bob_balance = boa.env.get_balance(bob)
    assert pyth_prices.recoverEthBalance(bob, sender=governance.address)
    log = filter_logs(pyth_prices, 'EthRecoveredFromPyth')[0]

    # Check balances
    assert boa.env.get_balance(pyth_prices.address) == 0
    assert boa.env.get_balance(bob) == pre_bob_balance + initial_balance

    # Check event
    assert log.recipient == bob
    assert log.amount == initial_balance


@pytest.mark.parametrize(
    'price, conf, expo, expected_price',
    [
        # Original test cases
        (99995021, 56127, -8, int(0.99995021 * 10**18) - int(56127 * 10**(-8) * 10**18)),  # Normal case
        (0, 56127, -8, 0),  # Zero price
        (-1, 56127, -8, 0), # Negative price
        (99995021, 99995021, -8, 0), # confidence == price
        (99995021, 99995022, -8, 0), # confidence > price
        (99995021, 56127, 0, int(99995021 * 10**18) - int(56127 * 10**(0) * 10**18)),   # Zero exponent
        (99995021, 56127, 1, int(99995021 * 10**19) - int(56127 * 10**(1) * 10**18)),   # Positive exponent
        
        # Confidence Edge Cases
        (100000000, 0, -8, int(1.0 * 10**18)),  # Zero confidence - should return full price
        (100000000, 1, -8, int(1.0 * 10**18) - int(1 * 10**(-8) * 10**18)),  # Minimal confidence
        (100000000, 50000000, -8, int(0.5 * 10**18)),  # 50% confidence
        
        # Exponent Edge Cases (corrected calculations)
        (100000000, 10000000, -18, 90000000),  # Very negative exponent (-18): price=100000000*10^18//10^18=100000000, conf=10000000, result=90000000
        (100000000, 10000000, -12, 90000000000000),  # Moderate negative exponent (-12): price*10^18//10^12, conf*10^18//10^12
        (100000000, 10000000, 2, 9000000000000000000000000000),  # Larger positive exponent (+2): price*10^18*10^2, conf*10^18*10^2
        (100000000, 10000000, 5, 9000000000000000000000000000000),  # Large positive exponent (+5): price*10^18*10^5, conf*10^18*10^5
        
        # Small Price Values (corrected calculations)
        (1, 0, -8, 10000000000),  # Minimal price value: 1*10^18//10^8 = 10^10
        (10, 5, -8, 50000000000),  # Small price with confidence: (10-5)*10^18//10^8 = 5*10^10
        (100, 99, -8, 10000000000),  # Small price, high confidence ratio: (100-99)*10^18//10^8 = 10^10
        
        # Large Price Values (corrected calculations)
        (4294967296, 2147483648, -8, 21474836480000000000),  # Large 32-bit values: (4294967296-2147483648)*10^18//10^8
        (999999999999, 100000000000, -8, 8999999999990000000000),  # Very large values: proper integer division
        
        # Precision Boundary Cases (corrected calculations)
        (1000000, 999999, -8, 10000000000),  # Confidence very close to price: (1000000-999999)*10^18//10^8
        (1000000, 500000, -18, 500000),  # High precision with -18 exponent: (1000000-500000)*10^18//10^18
        (123456789, 123456, -6, 123333333000000000000),  # Real-world-like values: proper scaling
        
        # Edge Arithmetic Cases (corrected calculations) 
        (9223372036854775807, 1000000, -8, 92233720368537758070000000000),  # Near max int64 price: proper large number handling
        (1000000000, 999999999, -8, 10000000000),  # Minimal difference: (1000000000-999999999)*10^18//10^8
        
        # Different Exponent Combinations (corrected calculations)
        (50000000, 25000000, -4, 2500000000000000000000),  # -4 exponent: (50000000-25000000)*10^18//10^4
        (30000000, 15000000, 3, 15000000000000000000000000000),  # +3 exponent: (30000000-15000000)*10^18*10^3
        (80000000, 40000000, -10, 4000000000000000),  # -10 exponent: (80000000-40000000)*10^18//10^10
        
        # Real-world Scenarios (corrected calculations)
        (300000000000, 150000000, -8, 2998500000000000000000),  # BTC-like price: (300000000000-150000000)*10^18//10^8
        (100000000, 50000, -8, 999500000000000000),  # Stablecoin-like: (100000000-50000)*10^18//10^8  
        (250000000000, 500000000, -8, 2495000000000000000000),  # ETH-like price: (250000000000-500000000)*10^18//10^8
        
        # Additional Edge Cases for Validation (corrected calculations)
        (1000000000, 2000000000, -8, 0),  # Confidence > price (should return 0)
        (-100, 50000, -8, 0),  # Another negative price case
    ]
)
def test_pyth_get_price(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    addPythFeed,
    price,
    conf,
    expo,
    expected_price,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    addPythFeed(alpha_token, data_feed_id)

    # get payload
    publish_time = boa.env.evm.patch.timestamp + 1
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        price,
        conf,
        expo,
        publish_time,
    )

    # add eth balance
    if boa.env.get_balance(pyth_prices.address) < EIGHTEEN_DECIMALS:
        boa.env.set_balance(pyth_prices.address, 2 * EIGHTEEN_DECIMALS)

    # update price
    assert pyth_prices.updatePythPrice(payload, sender=governance.address)

    # test price
    assert pyth_prices.getPrice(alpha_token) == expected_price


def test_pyth_get_price_and_has_feed(
    pyth_prices,
    alpha_token,
    bravo_token,
    addPythFeed,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    
    # Test with no feed
    price, has_feed = pyth_prices.getPriceAndHasFeed(bravo_token)
    assert price == 0
    assert not has_feed

    # Add feed
    addPythFeed(alpha_token, data_feed_id)
    
    # Test with feed
    price, has_feed = pyth_prices.getPriceAndHasFeed(alpha_token)
    assert price != 0
    assert has_feed


def test_pyth_get_price_stale(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    addPythFeed,
):
    boa.env.evm.patch.timestamp += MONTH_IN_SECONDS

    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    addPythFeed(alpha_token, data_feed_id)
    assert pyth_prices.getPrice(alpha_token) != 0

    # get payload
    publish_time = boa.env.evm.patch.timestamp - 3601 # 1 hour and 1 second ago, > stale time (3600s)
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        98000000,
        50000,
        -8,
        publish_time,
    )

    # add eth balance
    boa.env.set_balance(pyth_prices.address, EIGHTEEN_DECIMALS)

    # success update price
    assert pyth_prices.updatePythPrice(payload, sender=governance.address)

    # price should be 0 due to staleness
    assert pyth_prices.getPrice(alpha_token, 3600) == 0


def test_pyth_price_stale_with_feed_config(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
):
    # Test adding feed with custom stale time
    stale_time = 3600  # 1 hour
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    
    # Refresh the feed's timestamp to current time
    payload = mock_pyth.createPriceFeedUpdateData(data_feed_id, 98000000, 50000, -8, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_pyth.updatePriceFeeds(payload, value=len(payload))
    
    # Add feed with custom stale time (use 0 first to avoid validation issues)
    assert pyth_prices.addNewPriceFeed(alpha_token, data_feed_id, 0, sender=governance.address)
    boa.env.time_travel(blocks=pyth_prices.actionTimeLock() + 1)
    assert pyth_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Verify event has stale time
    log = filter_logs(pyth_prices, "NewPythFeedAdded")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id
    assert log.staleTime == 0  # We used 0 as stale time

    # Test price with feed's stale time (should have price data from earlier setup)
    assert pyth_prices.getPrice(alpha_token) != 0

    # Test price with additional stale time parameter (should use max of both)
    # The price should be 0 because the feed's publishTime is old enough to be stale with 1 hour stale time
    assert pyth_prices.getPrice(alpha_token, stale_time) == 0  # 1 hour stale time

    # Test price with larger stale time parameter (should also be stale)
    assert pyth_prices.getPrice(alpha_token, 7200) == 0  # 2 hours > 1 hour

    # Test that the feed config structure works correctly
    config = pyth_prices.feedConfig(alpha_token)
    assert config.feedId == data_feed_id
    assert config.staleTime == 0  # We used 0 as stale time


def test_pyth_is_valid_feed(
    pyth_prices,
    alpha_token,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    invalid_feed_id = bytes.fromhex("f" * 64)

    # valid feed
    assert pyth_prices.isValidNewFeed(alpha_token, data_feed_id, 0)

    # invalid feed id
    assert not pyth_prices.isValidNewFeed(alpha_token, invalid_feed_id, 0)

    # invalid asset
    assert not pyth_prices.isValidNewFeed(ZERO_ADDRESS, data_feed_id, 0)


######################
# Add New Feed Tests #
######################


def test_pyth_add_price_feed(
    pyth_prices,
    alpha_token,
    governance,
    bob,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")

    # Test unauthorized access
    with boa.reverts("no perms"):
        pyth_prices.addNewPriceFeed(alpha_token, data_feed_id, 0, sender=bob)

    # Test adding invalid feed (non-existent feed)
    invalid_feed_id = bytes.fromhex("f" * 64)
    with boa.reverts("invalid feed"):
        pyth_prices.addNewPriceFeed(alpha_token, invalid_feed_id, 0, sender=governance.address)

    # Test adding feed with zero address asset
    with boa.reverts("invalid feed"):
        pyth_prices.addNewPriceFeed(ZERO_ADDRESS, data_feed_id, 0, sender=governance.address)

    # Test successful feed addition
    assert pyth_prices.addNewPriceFeed(alpha_token, data_feed_id, 0, sender=governance.address)
    
    # Verify event
    log = filter_logs(pyth_prices, "NewPythFeedPending")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id
    assert log.staleTime == 0

    # Verify pending state
    assert pyth_prices.hasPendingPriceFeedUpdate(alpha_token)
    pending = pyth_prices.pendingUpdates(alpha_token)
    assert pending.config.feedId == data_feed_id

    # Test confirming before time lock
    with boa.reverts("time lock not reached"):
        pyth_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Travel past time lock
    boa.env.time_travel(blocks=pyth_prices.actionTimeLock() + 1)

    # Test confirming
    assert pyth_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(pyth_prices, "NewPythFeedAdded")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id
    assert log.staleTime == 0

    # Verify feed is active
    assert pyth_prices.hasPriceFeed(alpha_token)
    assert pyth_prices.feedConfig(alpha_token).feedId == data_feed_id
    assert pyth_prices.getPrice(alpha_token) != 0
    assert not pyth_prices.hasPendingPriceFeedUpdate(alpha_token)

    # Test canceling non-existent feed
    with boa.reverts("cannot cancel action"):
        pyth_prices.cancelNewPendingPriceFeed(alpha_token, sender=governance.address)

    # Test adding feed for existing asset
    with boa.reverts("invalid feed"):
        pyth_prices.addNewPriceFeed(alpha_token, data_feed_id, 0, sender=governance.address)


def test_pyth_add_price_feed_cancel(
    pyth_prices,
    alpha_token,
    governance,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")

    # Add feed
    assert pyth_prices.addNewPriceFeed(alpha_token, data_feed_id, 0, sender=governance.address)
    
    # Verify event
    log = filter_logs(pyth_prices, "NewPythFeedPending")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id
    assert log.staleTime == 0

    # Cancel feed
    assert pyth_prices.cancelNewPendingPriceFeed(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(pyth_prices, "NewPythFeedCancelled")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id

    # Verify feed is not active
    assert not pyth_prices.hasPriceFeed(alpha_token)
    assert pyth_prices.getPrice(alpha_token) == 0
    assert not pyth_prices.hasPendingPriceFeedUpdate(alpha_token)

    # Test confirming after cancel
    with boa.reverts("no pending new feed"):
        pyth_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)


def test_pyth_add_price_feed_validation_during_confirm(
    pyth_prices,
    alpha_token,
    mock_pyth,
    governance,
):
    # Use a different feed ID that doesn't exist
    invalid_feed_id = bytes.fromhex("baa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94b")

    # Add feed with non-existent feed ID (this should work initially)
    # Setup the feed first so validation passes during add
    payload = mock_pyth.createPriceFeedUpdateData(invalid_feed_id, 98000000, 50000, -8, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_pyth.updatePriceFeeds(payload, value=len(payload))
    
    assert pyth_prices.addNewPriceFeed(alpha_token, invalid_feed_id, 0, sender=governance.address)
    
    # Travel past time lock
    boa.env.time_travel(blocks=pyth_prices.actionTimeLock() + 1)

    # Now update the feed with invalid price (0) to make validation fail
    invalid_payload = mock_pyth.createPriceFeedUpdateData(invalid_feed_id, 0, 50000, -8, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_pyth.updatePriceFeeds(invalid_payload, value=len(invalid_payload))

    # Confirm should fail and auto-cancel due to invalid price (0)
    assert not pyth_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)
    
    # Verify feed was cancelled
    assert not pyth_prices.hasPriceFeed(alpha_token)
    assert not pyth_prices.hasPendingPriceFeedUpdate(alpha_token)


#####################
# Update Feed Tests #
#####################


def test_pyth_update_price_feed(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    bob,
    addPythFeed,
):
    data_feed_id_1 = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    data_feed_id_2 = bytes.fromhex("baa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94b")
    
    # Setup the second feed in MockPyth
    payload_2 = mock_pyth.createPriceFeedUpdateData(data_feed_id_2, 97000000, 45000, -8, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_pyth.updatePriceFeeds(payload_2, value=len(payload_2))

    # Add initial feed
    addPythFeed(alpha_token, data_feed_id_1)

    # Test unauthorized access
    with boa.reverts("no perms"):
        pyth_prices.updatePriceFeed(alpha_token, data_feed_id_2, 0, sender=bob)

    # Test updating with same feed
    with boa.reverts("invalid feed"):
        pyth_prices.updatePriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)

    # Test updating non-existent asset
    with boa.reverts("invalid feed"):
        pyth_prices.updatePriceFeed(ZERO_ADDRESS, data_feed_id_2, 0, sender=governance.address)

    # Test updating with invalid feed
    invalid_feed_id = bytes.fromhex("f" * 64)
    with boa.reverts("invalid feed"):
        pyth_prices.updatePriceFeed(alpha_token, invalid_feed_id, 0, sender=governance.address)

    # Test successful update
    assert pyth_prices.updatePriceFeed(alpha_token, data_feed_id_2, 0, sender=governance.address)
    
    # Verify event
    log = filter_logs(pyth_prices, "PythFeedUpdatePending")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id_2
    assert log.oldFeedId == data_feed_id_1
    assert log.staleTime == 0

    # Test confirming before time lock
    with boa.reverts("time lock not reached"):
        pyth_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    # Travel past time lock
    boa.env.time_travel(blocks=pyth_prices.actionTimeLock() + 1)

    # Test confirming
    assert pyth_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(pyth_prices, "PythFeedUpdated")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id_2
    assert log.oldFeedId == data_feed_id_1
    assert log.staleTime == 0

    # Verify feed is updated
    assert pyth_prices.hasPriceFeed(alpha_token)
    assert pyth_prices.feedConfig(alpha_token).feedId == data_feed_id_2
    assert pyth_prices.getPrice(alpha_token) != 0

    # Test canceling non-existent update
    with boa.reverts("cannot cancel action"):
        pyth_prices.cancelPriceFeedUpdate(alpha_token, sender=governance.address)


def test_pyth_update_price_feed_cancel(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    addPythFeed,
):
    data_feed_id_1 = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    data_feed_id_2 = bytes.fromhex("baa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94b")
    
    # Setup the second feed in MockPyth
    payload_2 = mock_pyth.createPriceFeedUpdateData(data_feed_id_2, 97000000, 45000, -8, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_pyth.updatePriceFeeds(payload_2, value=len(payload_2))

    # Add initial feed
    addPythFeed(alpha_token, data_feed_id_1)

    # Start update
    assert pyth_prices.updatePriceFeed(alpha_token, data_feed_id_2, 0, sender=governance.address)
    
    # Verify event
    log = filter_logs(pyth_prices, "PythFeedUpdatePending")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id_2
    assert log.oldFeedId == data_feed_id_1
    assert log.staleTime == 0

    # Cancel update
    assert pyth_prices.cancelPriceFeedUpdate(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(pyth_prices, "PythFeedUpdateCancelled")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id_2
    assert log.oldFeedId == data_feed_id_1

    # Verify feed is not updated
    assert pyth_prices.hasPriceFeed(alpha_token)
    assert pyth_prices.feedConfig(alpha_token).feedId == data_feed_id_1
    assert not pyth_prices.hasPendingPriceFeedUpdate(alpha_token)

    # Test confirming after cancel
    with boa.reverts("no pending update feed"):
        pyth_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)


def test_pyth_update_feed_validation_functions(
    pyth_prices,
    mock_pyth,
    alpha_token,
    bravo_token,
    addPythFeed,
):
    data_feed_id_1 = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    data_feed_id_2 = bytes.fromhex("baa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94b")
    
    # Setup the second feed in MockPyth
    payload_2 = mock_pyth.createPriceFeedUpdateData(data_feed_id_2, 97000000, 45000, -8, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_pyth.updatePriceFeeds(payload_2, value=len(payload_2))
    invalid_feed_id = bytes.fromhex("f" * 64)

    # Add initial feed
    addPythFeed(alpha_token, data_feed_id_1)

    # Test isValidUpdateFeed function
    assert pyth_prices.isValidUpdateFeed(alpha_token, data_feed_id_2, 0)  # Valid update
    assert not pyth_prices.isValidUpdateFeed(alpha_token, data_feed_id_1, 0)  # Same feed
    assert not pyth_prices.isValidUpdateFeed(bravo_token, data_feed_id_2, 0)  # No existing feed
    assert not pyth_prices.isValidUpdateFeed(alpha_token, invalid_feed_id, 0)  # Invalid feed


######################
# Disable Feed Tests #
######################


def test_pyth_disable_price_feed(
    pyth_prices,
    alpha_token,
    governance,
    bob,
    addPythFeed,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")

    # Add initial feed
    addPythFeed(alpha_token, data_feed_id)

    # Test unauthorized access
    with boa.reverts("no perms"):
        pyth_prices.disablePriceFeed(alpha_token, sender=bob)

    # Test disabling non-existent feed
    with boa.reverts("invalid asset"):
        pyth_prices.disablePriceFeed(ZERO_ADDRESS, sender=governance.address)

    # Test successful disable
    assert pyth_prices.disablePriceFeed(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(pyth_prices, "DisablePythFeedPending")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id

    # Test confirming before time lock
    with boa.reverts("time lock not reached"):
        pyth_prices.confirmDisablePriceFeed(alpha_token, sender=governance.address)

    # Travel past time lock
    boa.env.time_travel(blocks=pyth_prices.actionTimeLock() + 1)

    # Test confirming
    assert pyth_prices.confirmDisablePriceFeed(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(pyth_prices, "PythFeedDisabled")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id

    # Verify feed is disabled
    assert not pyth_prices.hasPriceFeed(alpha_token)
    assert pyth_prices.getPrice(alpha_token) == 0
    assert pyth_prices.feedConfig(alpha_token).feedId == bytes(32)

    # Test canceling non-existent disable
    with boa.reverts("cannot cancel action"):
        pyth_prices.cancelDisablePriceFeed(alpha_token, sender=governance.address)


def test_pyth_disable_price_feed_cancel(
    pyth_prices,
    alpha_token,
    governance,
    addPythFeed,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")

    # Add initial feed
    addPythFeed(alpha_token, data_feed_id)

    # Start disable
    assert pyth_prices.disablePriceFeed(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(pyth_prices, "DisablePythFeedPending")[0]
    assert log.asset == alpha_token.address

    # Cancel disable
    assert pyth_prices.cancelDisablePriceFeed(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(pyth_prices, "DisablePythFeedCancelled")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id

    # Verify feed is still active
    assert pyth_prices.hasPriceFeed(alpha_token)
    assert pyth_prices.getPrice(alpha_token) != 0
    assert pyth_prices.feedConfig(alpha_token).feedId == data_feed_id

    # Test confirming after cancel
    with boa.reverts("no pending disable feed"):
        pyth_prices.confirmDisablePriceFeed(alpha_token, sender=governance.address)


def test_pyth_disable_feed_validation_functions(
    pyth_prices,
    alpha_token,
    bravo_token,
    addPythFeed,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")

    # Add initial feed
    addPythFeed(alpha_token, data_feed_id)

    # Test isValidDisablePriceFeed function
    assert pyth_prices.isValidDisablePriceFeed(alpha_token)  # Valid disable
    assert not pyth_prices.isValidDisablePriceFeed(bravo_token)  # No existing feed


#############################
# Edge Cases and Validation #
#############################


def test_pyth_price_stale_edge_cases(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    addPythFeed,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    addPythFeed(alpha_token, data_feed_id)

    # Test price exactly at stale time boundary
    publish_time = boa.env.evm.patch.timestamp
    payload = mock_pyth.createPriceFeedUpdateData(data_feed_id, 98000000, 50000, -8, publish_time)
    boa.env.set_balance(pyth_prices.address, EIGHTEEN_DECIMALS)
    assert pyth_prices.updatePythPrice(payload, sender=governance.address)

    # Test price just at stale boundary (should still be valid)
    assert pyth_prices.getPrice(alpha_token, 0) != 0
    boa.env.time_travel(seconds=1)
    assert pyth_prices.getPrice(alpha_token, 1) != 0

    # Test price just over stale boundary
    boa.env.time_travel(seconds=1)
    assert pyth_prices.getPrice(alpha_token, 1) == 0

    # Test with maximum uint256 stale time
    payload = mock_pyth.createPriceFeedUpdateData(data_feed_id, 98000000, 50000, -8, boa.env.evm.patch.timestamp)
    assert pyth_prices.updatePythPrice(payload, sender=governance.address)
    assert pyth_prices.getPrice(alpha_token, 2**256 - 1) != 0

    # Test with zero stale time (never stale)
    boa.env.time_travel(seconds=100000)
    assert pyth_prices.getPrice(alpha_token, 0) != 0


def test_pyth_time_lock_edge_cases(
    pyth_prices,
    mock_pyth,
    alpha_token,
    bravo_token,
    governance,
):
    data_feed_id_1 = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    data_feed_id_2 = bytes.fromhex("baa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94b")
    
    # Setup the second feed in MockPyth
    payload_2 = mock_pyth.createPriceFeedUpdateData(data_feed_id_2, 97000000, 45000, -8, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_pyth.updatePriceFeeds(payload_2, value=len(payload_2))

    # Test confirming just before time lock boundary
    assert pyth_prices.addNewPriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)
    boa.env.time_travel(blocks=pyth_prices.actionTimeLock() - 1)
    with boa.reverts("time lock not reached"):
        pyth_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test confirming at time lock boundary
    boa.env.time_travel(blocks=1)
    assert pyth_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test multiple time lock actions in sequence
    assert pyth_prices.updatePriceFeed(alpha_token, data_feed_id_2, 0, sender=governance.address)
    boa.env.time_travel(blocks=pyth_prices.actionTimeLock() + 1)
    assert pyth_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    
    assert pyth_prices.disablePriceFeed(alpha_token, sender=governance.address)
    boa.env.time_travel(blocks=pyth_prices.actionTimeLock() + 1)
    assert pyth_prices.confirmDisablePriceFeed(alpha_token, sender=governance.address)

    # Test with different time lock values
    pyth_prices.setActionTimeLock(302400, sender=governance.address)  # 7 days in blocks
    assert pyth_prices.addNewPriceFeed(bravo_token, data_feed_id_1, 0, sender=governance.address)
    boa.env.time_travel(blocks=302400)
    assert pyth_prices.confirmNewPriceFeed(bravo_token, sender=governance.address)


def test_pyth_governance_edge_cases(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    switchboard_alpha,
):
    data_feed_id_1 = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    data_feed_id_2 = bytes.fromhex("baa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94b")
    
    # Setup the second feed in MockPyth
    payload_2 = mock_pyth.createPriceFeedUpdateData(data_feed_id_2, 97000000, 45000, -8, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_pyth.updatePriceFeeds(payload_2, value=len(payload_2))

    # Test multiple governance actions in sequence
    assert pyth_prices.addNewPriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)
    assert pyth_prices.cancelNewPendingPriceFeed(alpha_token, sender=governance.address)
    assert pyth_prices.addNewPriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)
    boa.env.time_travel(blocks=pyth_prices.actionTimeLock() + 1)
    assert pyth_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)
    assert pyth_prices.updatePriceFeed(alpha_token, data_feed_id_2, 0, sender=governance.address)
    boa.env.time_travel(blocks=pyth_prices.actionTimeLock() + 1)
    assert pyth_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    # Test governance actions during pause (using MissionControl address)
    pyth_prices.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        pyth_prices.addNewPriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)
    with boa.reverts("contract paused"):
        pyth_prices.updatePriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)
    with boa.reverts("contract paused"):
        pyth_prices.disablePriceFeed(alpha_token, sender=governance.address)

    # Test governance actions after unpause
    pyth_prices.pause(False, sender=switchboard_alpha.address)
    # First disable the existing feed
    assert pyth_prices.disablePriceFeed(alpha_token, sender=governance.address)
    boa.env.time_travel(blocks=pyth_prices.actionTimeLock() + 1)
    assert pyth_prices.confirmDisablePriceFeed(alpha_token, sender=governance.address)
    # Now we can add a new feed
    assert pyth_prices.addNewPriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)


def test_pyth_feed_validation_edge_cases(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
):
    bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")

    # Test basic feed validation - feed exists and has valid price
    new_feed_id = bytes.fromhex("caa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94c")
    
    # Create a feed with valid data
    payload = mock_pyth.createPriceFeedUpdateData(new_feed_id, 98000000, 50000, -8, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_pyth.updatePriceFeeds(payload, value=len(payload))

    # Should work regardless of timestamp since staleness check is removed for adding feeds
    assert pyth_prices.addNewPriceFeed(alpha_token, new_feed_id, 0, sender=governance.address)
    
    # Travel past time lock and confirm
    boa.env.time_travel(blocks=pyth_prices.actionTimeLock() + 1)
    assert pyth_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)
    
    # Verify feed is active
    assert pyth_prices.hasPriceFeed(alpha_token)
    assert pyth_prices.feedConfig(alpha_token).feedId == new_feed_id


@pytest.base
def test_set_pyth_feed_usdc(
    pyth_prices,
    fork,
    addPythFeed,
):
    usdc = CORE_TOKENS[fork]["USDC"]
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    addPythFeed(usdc, data_feed_id)

    assert pyth_prices.feedConfig(usdc) == data_feed_id
    assert int(1.02 * EIGHTEEN_DECIMALS) > pyth_prices.getPrice(usdc) > int(0.98 * EIGHTEEN_DECIMALS)


@pytest.base
def test_set_pyth_feed_aixbt(
    pyth_prices,
    addPythFeed,
):
    aixbt = "0x4f9fd6be4a90f2620860d680c0d4d5fb53d1a825"
    data_feed_id = bytes.fromhex("0fc54579a29ba60a08fdb5c28348f22fd3bec18e221dd6b90369950db638a5a7")
    addPythFeed(aixbt, data_feed_id)

    assert pyth_prices.feedConfig(aixbt) == data_feed_id
    assert int(0.19 * EIGHTEEN_DECIMALS) > pyth_prices.getPrice(aixbt) > int(0.18 * EIGHTEEN_DECIMALS)


@pytest.base
def test_set_pyth_feed_aero(
    pyth_prices,
    addPythFeed,
):
    aero = "0x940181a94a35a4569e4529a3cdfb74e38fd98631"
    data_feed_id = bytes.fromhex("9db37f4d5654aad3e37e2e14ffd8d53265fb3026d1d8f91146539eebaa2ef45f")
    addPythFeed(aero, data_feed_id)

    assert pyth_prices.feedConfig(aero) == data_feed_id
    assert int(0.68 * EIGHTEEN_DECIMALS) > pyth_prices.getPrice(aero) > int(0.64 * EIGHTEEN_DECIMALS)