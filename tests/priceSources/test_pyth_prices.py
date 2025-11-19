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

    assert int(0.98 * EIGHTEEN_DECIMALS) >= pyth_prices.getPrice(alpha_token) > int(0.97 * EIGHTEEN_DECIMALS)


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


def test_pyth_set_max_confidence_ratio(
    pyth_prices,
    governance,
    switchboard_alpha,
    bob,
):
    # Check initial value
    assert pyth_prices.maxConfidenceRatio() == 300  # 3% default

    # Test unauthorized access (non-switchboard)
    with boa.reverts("no perms"):
        pyth_prices.setMaxConfidenceRatio(500, sender=bob)

    # Test governance cannot call it (only switchboard can)
    with boa.reverts("no perms"):
        pyth_prices.setMaxConfidenceRatio(500, sender=governance.address)

    # Test setting to valid value (using switchboard)
    assert pyth_prices.setMaxConfidenceRatio(100, sender=switchboard_alpha.address)  # 1%
    assert pyth_prices.maxConfidenceRatio() == 100

    # Test duplicate setting (should revert)
    with boa.reverts("ratio already set"):
        pyth_prices.setMaxConfidenceRatio(100, sender=switchboard_alpha.address)

    # Test setting to another valid value
    assert pyth_prices.setMaxConfidenceRatio(1000, sender=switchboard_alpha.address)  # 10%
    assert pyth_prices.maxConfidenceRatio() == 1000

    # Test setting to maximum valid value (just under 100%)
    assert pyth_prices.setMaxConfidenceRatio(9999, sender=switchboard_alpha.address)
    assert pyth_prices.maxConfidenceRatio() == 9999

    # Test setting to zero (valid - disables validation)
    assert pyth_prices.setMaxConfidenceRatio(0, sender=switchboard_alpha.address)
    assert pyth_prices.maxConfidenceRatio() == 0

    # Test setting to 100% or above (invalid)
    with boa.reverts("ratio must be < 100%"):
        pyth_prices.setMaxConfidenceRatio(10000, sender=switchboard_alpha.address)

    with boa.reverts("ratio must be < 100%"):
        pyth_prices.setMaxConfidenceRatio(10001, sender=switchboard_alpha.address)

    # Reset to default
    assert pyth_prices.setMaxConfidenceRatio(300, sender=switchboard_alpha.address)


def test_pyth_max_confidence_ratio_event(
    pyth_prices,
    switchboard_alpha,
):
    """Test that MaxConfidenceRatioUpdated event is emitted"""
    # Change ratio and check event
    assert pyth_prices.setMaxConfidenceRatio(500, sender=switchboard_alpha.address)
    log = filter_logs(pyth_prices, 'MaxConfidenceRatioUpdated')[0]
    assert log.newRatio == 500

    # Change again
    assert pyth_prices.setMaxConfidenceRatio(100, sender=switchboard_alpha.address)
    log = filter_logs(pyth_prices, 'MaxConfidenceRatioUpdated')[0]
    assert log.newRatio == 100

    # Reset
    assert pyth_prices.setMaxConfidenceRatio(300, sender=switchboard_alpha.address)
    log = filter_logs(pyth_prices, 'MaxConfidenceRatioUpdated')[0]
    assert log.newRatio == 300


def test_pyth_confidence_ratio_validation(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    switchboard_alpha,
    addPythFeed,
):
    """Test that confidence ratio validation works correctly with different thresholds"""
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    addPythFeed(alpha_token, data_feed_id)

    # Set up ETH balance for price updates
    boa.env.set_balance(pyth_prices.address, 10 * EIGHTEEN_DECIMALS)

    # Test 1: With default 3% threshold, 2% confidence should pass (returns price - confidence)
    publish_time = boa.env.evm.patch.timestamp + 1
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        100000000,  # price = $1.00
        2000000,    # confidence = $0.02 (2%)
        -8,
        publish_time,
    )
    assert pyth_prices.updatePythPrice(payload, sender=governance.address)
    assert pyth_prices.getPrice(alpha_token) == int(0.98 * 10**18)  # Returns price - confidence

    # Test 2: With default 3% threshold, 5% confidence should be rejected
    publish_time = boa.env.evm.patch.timestamp + 2
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        100000000,  # price = $1.00
        5000000,    # confidence = $0.05 (5%)
        -8,
        publish_time,
    )
    assert pyth_prices.updatePythPrice(payload, sender=governance.address)
    assert pyth_prices.getPrice(alpha_token) == 0  # Rejected due to high confidence

    # Test 3: Change threshold to 10%, now 5% should pass (returns price - confidence)
    assert pyth_prices.setMaxConfidenceRatio(1000, sender=switchboard_alpha.address)  # 10%
    publish_time = boa.env.evm.patch.timestamp + 3
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        100000000,  # price = $1.00
        5000000,    # confidence = $0.05 (5%)
        -8,
        publish_time,
    )
    assert pyth_prices.updatePythPrice(payload, sender=governance.address)
    assert pyth_prices.getPrice(alpha_token) == int(0.95 * 10**18)  # Now accepted, returns price - confidence

    # Test 4: With 10% threshold, 15% confidence should still be rejected
    publish_time = boa.env.evm.patch.timestamp + 4
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        100000000,  # price = $1.00
        15000000,   # confidence = $0.15 (15%)
        -8,
        publish_time,
    )
    assert pyth_prices.updatePythPrice(payload, sender=governance.address)
    assert pyth_prices.getPrice(alpha_token) == 0  # Rejected

    # Test 5: Setting to 0 disables validation entirely (accepts any confidence)
    assert pyth_prices.setMaxConfidenceRatio(0, sender=switchboard_alpha.address)  # Disable validation
    publish_time = boa.env.evm.patch.timestamp + 5
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        100000000,  # price = $1.00
        90000000,   # confidence = $0.90 (90%!)
        -8,
        publish_time,
    )
    assert pyth_prices.updatePythPrice(payload, sender=governance.address)
    assert pyth_prices.getPrice(alpha_token) == int(0.1 * 10**18)  # Accepted! Returns price - confidence = 0.1

    # Reset to default
    assert pyth_prices.setMaxConfidenceRatio(300, sender=switchboard_alpha.address)


@pytest.mark.parametrize(
    'price, conf, expo, expected_price',
    [
        # Original test cases - RETURNS PRICE - CONFIDENCE (conservative approach)
        (99995021, 56127, -8, int(0.99995021 * 10**18) - int(56127 * 10**(-8) * 10**18)),  # Normal case, conf ratio ~0.056% < 3%
        (0, 56127, -8, 0),  # Zero price
        (-1, 56127, -8, 0), # Negative price
        (99995021, 99995021, -8, 0), # confidence == price
        (99995021, 99995022, -8, 0), # confidence > price
        (99995021, 56127, 0, int(99995021 * 10**18) - int(56127 * 10**18)),   # Zero exponent, conf ratio ~0.056% < 3%
        (99995021, 56127, 1, int(99995021 * 10**19) - int(56127 * 10**19)),   # Positive exponent, conf ratio ~0.056% < 3%

        # Confidence Edge Cases
        (100000000, 0, -8, int(1.0 * 10**18)),  # Zero confidence - returns full price (no subtraction)
        (100000000, 1, -8, int(1.0 * 10**18) - int(1 * 10**(-8) * 10**18)),  # Minimal confidence ~0.000001% < 3%
        (100000000, 50000000, -8, 0),  # 50% confidence > 3% - REJECTED

        # Exponent Edge Cases - 10% confidence > 3% - ALL REJECTED
        (100000000, 10000000, -18, 0),  # 10% confidence > 3%
        (100000000, 10000000, -12, 0),  # 10% confidence > 3%
        (100000000, 10000000, 2, 0),  # 10% confidence > 3%
        (100000000, 10000000, 5, 0),  # 10% confidence > 3%

        # Small Price Values
        (1, 0, -8, 10000000000),  # Zero confidence, returns: 1*10^18//10^8 = 10^10
        (10, 5, -8, 0),  # 50% confidence > 3% - REJECTED
        (100, 99, -8, 0),  # 99% confidence > 3% - REJECTED

        # Large Price Values
        (4294967296, 2147483648, -8, 0),  # 50% confidence > 3% - REJECTED
        (999999999999, 100000000000, -8, 0),  # 10% confidence > 3% - REJECTED

        # Precision Boundary Cases
        (1000000, 999999, -8, 0),  # 99.9999% confidence > 3% - REJECTED
        (1000000, 500000, -18, 0),  # 50% confidence > 3% - REJECTED
        (123456789, 123456, -6, int(123456789 * 10**12) - int(123456 * 10**12)),  # ~0.1% confidence < 3% - returns price - confidence

        # Edge Arithmetic Cases
        (9223372036854775807, 1000000, -8, int(92233720368547758070000000000) - int(1000000 * 10**10)),  # ~0.00001% confidence < 3%
        (1000000000, 999999999, -8, 0),  # 99.9999999% confidence > 3% - REJECTED

        # Different Exponent Combinations - 50% confidence > 3% - ALL REJECTED
        (50000000, 25000000, -4, 0),  # 50% confidence > 3%
        (30000000, 15000000, 3, 0),  # 50% confidence > 3%
        (80000000, 40000000, -10, 0),  # 50% confidence > 3%

        # Real-world Scenarios (price - confidence)
        (300000000000, 150000000, -8, int(3000 * 10**18) - int(1.5 * 10**18)),  # ~0.05% confidence < 3%
        (100000000, 50000, -8, int(1.0 * 10**18) - int(0.0005 * 10**18)),  # ~0.05% confidence < 3%
        (250000000000, 500000000, -8, int(2500 * 10**18) - int(5 * 10**18)),  # ~0.2% confidence < 3%

        # Additional Edge Cases for Validation
        (1000000000, 2000000000, -8, 0),  # Confidence > price (should return 0)
        (-100, 50000, -8, 0),  # Another negative price case

        # New test cases for 3% threshold boundary (price - confidence)
        (100000000, 3000000, -8, int(1.0 * 10**18) - int(0.03 * 10**18)),  # Exactly 3% confidence - PASSES (not >)
        (100000000, 3100000, -8, 0),  # 3.1% confidence - REJECTED (> 3%)
        (100000000, 2999999, -8, int(1.0 * 10**18) - int(0.02999999 * 10**18)),  # Just under 3% confidence - PASSES
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