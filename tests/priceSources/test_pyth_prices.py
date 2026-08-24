import boa
import pytest

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS
from conf_utils import filter_logs, advance_timelock_blocks
from config.BluePrint import CORE_TOKENS

MONTH_IN_SECONDS = 30 * 24 * 60 * 60
MAX_FEED_STALE_TIME = 7 * 24 * 60 * 60


@pytest.fixture(autouse=True)
def default_price_stale_time(setGeneralConfig):
    setGeneralConfig(_priceStaleTime=24 * 60 * 60)


@pytest.fixture(scope="module")
def addPythFeed(pyth_prices, governance):
    def addPythFeed(_asset, _feed_id, _stale_time=0):
        if pyth_prices.hasPriceFeed(_asset):
            return
        assert pyth_prices.addNewPriceFeed(_asset, _feed_id, _stale_time, sender=governance.address)
        advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
        assert pyth_prices.confirmNewPriceFeed(_asset, sender=governance.address)
        # MockPyth ignores updates whose publish time is not strictly newer.
        boa.env.time_travel(seconds=1)
    yield addPythFeed


@pytest.fixture(scope="module")
def authorized_caller(switchboard_alpha, mission_control, governance, bob):
    """Grant canPerformLiteAction permission to bob for oracle updates"""
    action_id = switchboard_alpha.setCanPerformLiteAction(bob, True, sender=governance.address)
    advance_timelock_blocks(switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    assert mission_control.canPerformLiteAction(bob)
    return bob


##################
# Unique to Pyth #
##################


def test_pyth_local_update_prices(
    pyth_prices,
    mock_pyth,
    alpha_token,
    authorized_caller,
    addPythFeed,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    addPythFeed(alpha_token, data_feed_id)
    assert pyth_prices.getPrice(alpha_token) != 0

    # get payload
    publish_time = boa.env.evm.patch.timestamp
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        98000000,
        50000,
        -8,
        publish_time,
    )
    exp_fee = 1

    # insufficient payment
    with boa.reverts("payment required"):
        pyth_prices.updatePythPrice([payload], sender=authorized_caller, value=0)

    # success - caller provides payment
    assert boa.env.get_balance(mock_pyth.address) == 0
    boa.env.set_balance(authorized_caller, EIGHTEEN_DECIMALS)
    pre_caller_bal = boa.env.get_balance(authorized_caller)

    assert pyth_prices.updatePythPrice([payload], sender=authorized_caller, value=EIGHTEEN_DECIMALS)

    log = filter_logs(pyth_prices, 'PythPriceUpdated')[0]
    assert list(log.payload) == [payload]
    assert log.feeAmount == exp_fee
    assert log.caller == authorized_caller

    # Check that fee was paid and excess was refunded
    assert boa.env.get_balance(mock_pyth.address) == exp_fee
    assert boa.env.get_balance(authorized_caller) == pre_caller_bal - exp_fee

    # check mock pyth
    price_data = mock_pyth.priceFeeds(data_feed_id)
    assert price_data.price.price == 98000000
    assert price_data.price.conf == 50000
    assert price_data.price.expo == -8
    assert price_data.price.publishTime == publish_time

    assert int(0.98 * EIGHTEEN_DECIMALS) >= pyth_prices.getPrice(alpha_token) > int(0.97 * EIGHTEEN_DECIMALS)


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
    authorized_caller,
    switchboard_alpha,
    addPythFeed,
):
    """Test that confidence ratio validation works correctly with different thresholds"""
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    addPythFeed(alpha_token, data_feed_id)

    # Give switchboard enough ETH for all tests
    boa.env.set_balance(authorized_caller, 100 * EIGHTEEN_DECIMALS)

    # Test 1: With default 3% threshold, 2% confidence should pass (returns price - confidence)
    boa.env.time_travel(seconds=1)
    publish_time = boa.env.evm.patch.timestamp
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        100000000,  # price = $1.00
        2000000,    # confidence = $0.02 (2%)
        -8,
        publish_time,
    )
    assert pyth_prices.updatePythPrice([payload], sender=authorized_caller, value=EIGHTEEN_DECIMALS)
    assert pyth_prices.getPrice(alpha_token) == int(0.98 * 10**18)  # Returns price - confidence

    # Test 2: With default 3% threshold, 5% confidence should be rejected
    boa.env.time_travel(seconds=1)
    publish_time = boa.env.evm.patch.timestamp
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        100000000,  # price = $1.00
        5000000,    # confidence = $0.05 (5%)
        -8,
        publish_time,
    )
    assert pyth_prices.updatePythPrice([payload], sender=authorized_caller, value=EIGHTEEN_DECIMALS)
    assert pyth_prices.getPrice(alpha_token) == 0  # Rejected due to high confidence

    # Test 3: Change threshold to 10%, now 5% should pass (returns price - confidence)
    assert pyth_prices.setMaxConfidenceRatio(1000, sender=switchboard_alpha.address)  # 10%
    boa.env.time_travel(seconds=1)
    publish_time = boa.env.evm.patch.timestamp
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        100000000,  # price = $1.00
        5000000,    # confidence = $0.05 (5%)
        -8,
        publish_time,
    )
    assert pyth_prices.updatePythPrice([payload], sender=authorized_caller, value=EIGHTEEN_DECIMALS)
    assert pyth_prices.getPrice(alpha_token) == int(0.95 * 10**18)  # Now accepted, returns price - confidence

    # Test 4: With 10% threshold, 15% confidence should still be rejected
    boa.env.time_travel(seconds=1)
    publish_time = boa.env.evm.patch.timestamp
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        100000000,  # price = $1.00
        15000000,   # confidence = $0.15 (15%)
        -8,
        publish_time,
    )
    assert pyth_prices.updatePythPrice([payload], sender=authorized_caller, value=EIGHTEEN_DECIMALS)
    assert pyth_prices.getPrice(alpha_token) == 0  # Rejected

    # Test 5: Setting to 0 disables validation entirely (accepts any confidence)
    assert pyth_prices.setMaxConfidenceRatio(0, sender=switchboard_alpha.address)  # Disable validation
    boa.env.time_travel(seconds=1)
    publish_time = boa.env.evm.patch.timestamp
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        100000000,  # price = $1.00
        90000000,   # confidence = $0.90 (90%!)
        -8,
        publish_time,
    )
    assert pyth_prices.updatePythPrice([payload], sender=authorized_caller, value=EIGHTEEN_DECIMALS)
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
    authorized_caller,
    addPythFeed,
    price,
    conf,
    expo,
    expected_price,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    addPythFeed(alpha_token, data_feed_id)

    # get payload
    publish_time = boa.env.evm.patch.timestamp
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        price,
        conf,
        expo,
        publish_time,
    )

    # Give switchboard ETH for payment
    boa.env.set_balance(authorized_caller, EIGHTEEN_DECIMALS)

    # update price - caller provides payment
    boa.env.set_balance(authorized_caller, 10 * EIGHTEEN_DECIMALS)
    assert pyth_prices.updatePythPrice([payload], sender=authorized_caller, value=EIGHTEEN_DECIMALS)

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
    authorized_caller,
    addPythFeed,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    addPythFeed(alpha_token, data_feed_id, 3600)
    assert pyth_prices.getPrice(alpha_token) != 0

    boa.env.time_travel(seconds=MONTH_IN_SECONDS)

    # get payload
    publish_time = boa.env.evm.patch.timestamp - 3601 # 1 hour and 1 second ago, > stale time (3600s)
    payload = mock_pyth.createPriceFeedUpdateData(
        data_feed_id,
        98000000,
        50000,
        -8,
        publish_time,
    )

    # Give authorized_caller ETH for payment
    boa.env.set_balance(authorized_caller, 10 * EIGHTEEN_DECIMALS)

    # success update price - caller provides payment
    assert pyth_prices.updatePythPrice([payload], sender=authorized_caller, value=EIGHTEEN_DECIMALS)

    # price should be 0 due to staleness
    assert pyth_prices.getPrice(alpha_token) == 0


def test_pyth_price_stale_with_feed_config(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
):
    # Test adding feed with custom stale time
    stale_time = 3600  # 1 hour
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    
    # Add and confirm an exact per-feed override.
    assert pyth_prices.addNewPriceFeed(alpha_token, data_feed_id, stale_time, sender=governance.address)
    advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
    boa.env.time_travel(seconds=1)
    _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)
    assert pyth_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Verify event has stale time
    log = filter_logs(pyth_prices, "NewPythFeedAdded")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id
    assert log.staleTime == stale_time

    # Test price with feed's stale time (should have price data from earlier setup)
    assert pyth_prices.getPrice(alpha_token) != 0

    # Equality at the configured age is valid; one second beyond is stale.
    boa.env.time_travel(seconds=stale_time)
    assert pyth_prices.getPrice(alpha_token) != 0
    boa.env.time_travel(seconds=1)
    assert pyth_prices.getPrice(alpha_token) == 0

    # Test that the feed config structure works correctly
    config = pyth_prices.feedConfig(alpha_token)
    assert config.feedId == data_feed_id
    assert config.staleTime == stale_time


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
    advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)

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
    with boa.reverts("no pending new feed"):
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
    mock_pyth.updatePriceFeeds([payload], value=1)
    
    assert pyth_prices.addNewPriceFeed(alpha_token, invalid_feed_id, 0, sender=governance.address)
    
    # Travel past time lock
    advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)

    # Now update the feed with invalid price (0) to make validation fail
    boa.env.time_travel(seconds=1)
    invalid_payload = mock_pyth.createPriceFeedUpdateData(invalid_feed_id, 0, 50000, -8, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_pyth.updatePriceFeeds([invalid_payload], value=1)

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
    mock_pyth.updatePriceFeeds([payload_2], value=1)

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
    advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)

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
    with boa.reverts("no pending update feed"):
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
    mock_pyth.updatePriceFeeds([payload_2], value=1)

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
    mock_pyth.updatePriceFeeds([payload_2], value=1)
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
    advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)

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
    with boa.reverts("no pending disable feed"):
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
    authorized_caller,
    addPythFeed,
):
    data_feed_id = bytes.fromhex("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a")
    addPythFeed(alpha_token, data_feed_id, 1)

    # Give switchboard enough ETH for all tests
    boa.env.set_balance(authorized_caller, 100 * EIGHTEEN_DECIMALS)

    # Test price exactly at stale time boundary
    publish_time = boa.env.evm.patch.timestamp
    payload = mock_pyth.createPriceFeedUpdateData(data_feed_id, 98000000, 50000, -8, publish_time)
    assert pyth_prices.updatePythPrice([payload], sender=authorized_caller, value=EIGHTEEN_DECIMALS)

    # Test price just at stale boundary (should still be valid)
    assert pyth_prices.getPrice(alpha_token) != 0
    boa.env.time_travel(seconds=1)
    assert pyth_prices.getPrice(alpha_token) != 0

    # Test price just over stale boundary
    boa.env.time_travel(seconds=1)
    assert pyth_prices.getPrice(alpha_token) == 0


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
    mock_pyth.updatePriceFeeds([payload_2], value=1)

    # Test confirming just before time lock boundary
    assert pyth_prices.addNewPriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)
    advance_timelock_blocks(pyth_prices.actionTimeLock() - 1)
    with boa.reverts("time lock not reached"):
        pyth_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test confirming at time lock boundary
    advance_timelock_blocks(1)
    assert pyth_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test multiple time lock actions in sequence
    assert pyth_prices.updatePriceFeed(alpha_token, data_feed_id_2, 0, sender=governance.address)
    advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
    assert pyth_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    
    assert pyth_prices.disablePriceFeed(alpha_token, sender=governance.address)
    advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
    assert pyth_prices.confirmDisablePriceFeed(alpha_token, sender=governance.address)

    # Test with different time lock values
    pyth_prices.setActionTimeLock(302400, sender=governance.address)  # 7 days in blocks
    assert pyth_prices.addNewPriceFeed(bravo_token, data_feed_id_1, 0, sender=governance.address)
    advance_timelock_blocks(302400)
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
    mock_pyth.updatePriceFeeds([payload_2], value=1)

    # Test multiple governance actions in sequence
    assert pyth_prices.addNewPriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)
    assert pyth_prices.cancelNewPendingPriceFeed(alpha_token, sender=governance.address)
    assert pyth_prices.addNewPriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)
    advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
    assert pyth_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)
    assert pyth_prices.updatePriceFeed(alpha_token, data_feed_id_2, 0, sender=governance.address)
    advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
    assert pyth_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    # Test governance actions during pause (using switchboard address)
    pyth_prices.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        pyth_prices.addNewPriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)
    with boa.reverts("contract paused"):
        pyth_prices.updatePriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)
    with boa.reverts("contract paused"):
        pyth_prices.updateStaleTime(
            alpha_token, 3_600, sender=governance.address
        )
    with boa.reverts("contract paused"):
        pyth_prices.disablePriceFeed(alpha_token, sender=governance.address)

    # Test governance actions after unpause
    pyth_prices.pause(False, sender=switchboard_alpha.address)
    # First disable the existing feed
    assert pyth_prices.disablePriceFeed(alpha_token, sender=governance.address)
    advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
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
    mock_pyth.updatePriceFeeds([payload], value=1)

    # Fresh data is valid under the inherited global stale-time policy.
    assert pyth_prices.addNewPriceFeed(alpha_token, new_feed_id, 0, sender=governance.address)
    
    # Travel past time lock and confirm
    advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
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

    assert pyth_prices.feedConfig(usdc).feedId == data_feed_id
    assert int(1.02 * EIGHTEEN_DECIMALS) > pyth_prices.getPrice(usdc) > int(0.98 * EIGHTEEN_DECIMALS)


@pytest.base
def test_set_pyth_feed_aixbt(
    pyth_prices,
    addPythFeed,
):
    aixbt = "0x4f9fd6be4a90f2620860d680c0d4d5fb53d1a825"
    data_feed_id = bytes.fromhex("0fc54579a29ba60a08fdb5c28348f22fd3bec18e221dd6b90369950db638a5a7")
    addPythFeed(aixbt, data_feed_id)

    assert pyth_prices.feedConfig(aixbt).feedId == data_feed_id
    assert int(0.15 * EIGHTEEN_DECIMALS) > pyth_prices.getPrice(aixbt) > int(0.08 * EIGHTEEN_DECIMALS)


@pytest.base
def test_set_pyth_feed_aero(
    pyth_prices,
    addPythFeed,
):
    aero = "0x940181a94a35a4569e4529a3cdfb74e38fd98631"
    data_feed_id = bytes.fromhex("9db37f4d5654aad3e37e2e14ffd8d53265fb3026d1d8f91146539eebaa2ef45f")
    addPythFeed(aero, data_feed_id)

    assert pyth_prices.feedConfig(aero).feedId == data_feed_id
    assert int(1.60 * EIGHTEEN_DECIMALS) > pyth_prices.getPrice(aero) > int(1.20 * EIGHTEEN_DECIMALS)


SC20_PYTH_FEED_ID = bytes.fromhex(
    "eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a"
)
SC20_PYTH_ALT_FEED_ID = bytes.fromhex(
    "baa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94b"
)
SC20_PYTH_PRICE = (98_000_000 - 50_000) * 10**10


def _set_sc20_pyth_price(
    mock_pyth,
    publish_time,
    feed_id=SC20_PYTH_FEED_ID,
):
    payload = mock_pyth.createPriceFeedUpdateData(
        feed_id,
        98_000_000,
        50_000,
        -8,
        publish_time,
    )
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)
    mock_pyth.updatePriceFeeds([payload], value=1)


def _add_sc20_pyth_feed(
    pyth_prices,
    mock_pyth,
    asset,
    governance,
    stale_time,
    feed_id=SC20_PYTH_FEED_ID,
):
    _set_sc20_pyth_price(mock_pyth, boa.env.timestamp, feed_id)
    assert pyth_prices.addNewPriceFeed(
        asset,
        feed_id,
        stale_time,
        sender=governance.address,
    )
    advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
    boa.env.time_travel(seconds=1)
    _set_sc20_pyth_price(mock_pyth, boa.env.timestamp, feed_id)
    assert pyth_prices.confirmNewPriceFeed(asset, sender=governance.address)


def test_pyth_omitted_add_and_update_stale_time_inherit_global(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)
        assert pyth_prices.addNewPriceFeed(
            alpha_token,
            SC20_PYTH_FEED_ID,
            sender=governance.address,
        )
        assert pyth_prices.pendingUpdates(alpha_token).config.staleTime == 0

        advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
        boa.env.time_travel(seconds=1)
        _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)
        assert pyth_prices.confirmNewPriceFeed(
            alpha_token, sender=governance.address
        )
        assert pyth_prices.feedConfig(alpha_token).staleTime == 0

        _set_sc20_pyth_price(
            mock_pyth,
            boa.env.timestamp,
            SC20_PYTH_ALT_FEED_ID,
        )
        assert pyth_prices.updatePriceFeed(
            alpha_token,
            SC20_PYTH_ALT_FEED_ID,
            sender=governance.address,
        )
        assert pyth_prices.pendingUpdates(alpha_token).config.staleTime == 0

        advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
        boa.env.time_travel(seconds=1)
        _set_sc20_pyth_price(
            mock_pyth,
            boa.env.timestamp,
            SC20_PYTH_ALT_FEED_ID,
        )
        assert pyth_prices.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        stored = pyth_prices.feedConfig(alpha_token)
        assert stored.feedId == SC20_PYTH_ALT_FEED_ID
        assert stored.staleTime == 0

        boa.env.time_travel(seconds=100)
        assert pyth_prices.getPrice(alpha_token) == SC20_PYTH_PRICE
        boa.env.time_travel(seconds=1)
        assert pyth_prices.getPrice(alpha_token) == 0


@pytest.mark.parametrize(
    "feed_bound,global_bound,age,expected_valid",
    [
        (0, 100, 100, True),
        (0, 100, 101, False),
        (200, 100, 150, True),
        (50, 100, 75, False),
        (50, 0, 50, True),
        (50, 0, 51, False),
        (50, MAX_FEED_STALE_TIME + 1, 50, True),
        (MAX_FEED_STALE_TIME, 0, MAX_FEED_STALE_TIME, True),
        (MAX_FEED_STALE_TIME, 100, MAX_FEED_STALE_TIME + 1, False),
        (0, 0, 0, False),
        (0, MAX_FEED_STALE_TIME + 1, 0, False),
    ],
)
def test_pyth_exact_override_and_global_inheritance_matrix(
    pyth_prices,
    mock_pyth,
    alpha_token,
    bravo_token,
    governance,
    price_desk,
    setGeneralConfig,
    feed_bound,
    global_bound,
    age,
    expected_valid,
):
    with boa.env.anchor():
        assert pyth_prices.getPriceAndHasFeed(bravo_token) == (0, False)
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_pyth_feed(
            pyth_prices,
            mock_pyth,
            alpha_token,
            governance,
            feed_bound,
        )
        setGeneralConfig(_priceStaleTime=global_bound)
        _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)
        boa.env.time_travel(seconds=age)

        expected_price = SC20_PYTH_PRICE if expected_valid else 0
        assert pyth_prices.getPrice(alpha_token) == expected_price
        assert pyth_prices.getPriceAndHasFeed(alpha_token) == (
            expected_price,
            True,
        )
        assert price_desk.getPrice(alpha_token) == expected_price


def test_pyth_forwarded_global_requires_canonical_price_desk(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    price_desk,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_pyth_feed(
            pyth_prices, mock_pyth, alpha_token, governance, 0
        )
        _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)

        assert price_desk.getPrice(alpha_token) == SC20_PYTH_PRICE
        assert pyth_prices.getPrice(alpha_token) == SC20_PYTH_PRICE

        assert pyth_prices.getPrice(
            alpha_token, 100, price_desk.address
        ) == 0
        assert pyth_prices.getPriceAndHasFeed(
            alpha_token, 100, price_desk.address
        ) == (0, True)
        assert pyth_prices.getPrice(
            alpha_token, 100, ZERO_ADDRESS, sender=price_desk.address
        ) == 0
        assert pyth_prices.getPriceAndHasFeed(
            alpha_token, 100, ZERO_ADDRESS, sender=price_desk.address
        ) == (0, True)

        assert pyth_prices.getPrice(
            alpha_token,
            100,
            price_desk.address,
            sender=price_desk.address,
        ) == SC20_PYTH_PRICE
        assert pyth_prices.getPriceAndHasFeed(
            alpha_token,
            100,
            price_desk.address,
            sender=price_desk.address,
        ) == (SC20_PYTH_PRICE, True)


def test_pyth_invalid_stale_bounds_fail_closed_at_admission_and_runtime(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    setGeneralConfig,
):
    with boa.env.anchor():
        _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)
        assert not pyth_prices.isValidNewFeed(
            alpha_token, SC20_PYTH_FEED_ID, MAX_FEED_STALE_TIME + 1
        )
        with boa.reverts("invalid feed"):
            pyth_prices.addNewPriceFeed(
                alpha_token,
                SC20_PYTH_FEED_ID,
                MAX_FEED_STALE_TIME + 1,
                sender=governance.address,
            )

        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_pyth_feed(
            pyth_prices, mock_pyth, alpha_token, governance, 0
        )
        for invalid_global in (0, MAX_FEED_STALE_TIME + 1):
            setGeneralConfig(_priceStaleTime=invalid_global)
            assert pyth_prices.getPrice(alpha_token) == 0
            assert pyth_prices.getPriceAndHasFeed(alpha_token) == (0, True)

        assert not pyth_prices.isValidStaleTimeUpdate(
            alpha_token, MAX_FEED_STALE_TIME + 1
        )
        with boa.reverts("invalid feed"):
            pyth_prices.updateStaleTime(
                alpha_token,
                MAX_FEED_STALE_TIME + 1,
                sender=governance.address,
            )

        setGeneralConfig(_priceStaleTime=100)
        _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)
        pyth_prices.eval(
            f"self.feedConfig[{alpha_token.address}].staleTime = "
            f"{MAX_FEED_STALE_TIME + 1}"
        )
        assert pyth_prices.getPrice(alpha_token) == 0
        assert pyth_prices.getPriceAndHasFeed(alpha_token) == (0, True)


def test_pyth_stale_time_update_lifecycle_noop_cancel_and_liveness(
    pyth_prices,
    mock_pyth,
    alpha_token,
    bravo_token,
    governance,
    bob,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        assert not pyth_prices.hasPriceFeed(bravo_token)
        assert not pyth_prices.isValidStaleTimeUpdate(bravo_token, 200)
        with boa.reverts("invalid feed"):
            pyth_prices.updateStaleTime(
                bravo_token, 200, sender=governance.address
            )
        assert pyth_prices.pendingUpdates(bravo_token).actionId == 0

        _add_sc20_pyth_feed(
            pyth_prices, mock_pyth, alpha_token, governance, 100
        )
        _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)

        with boa.reverts("no perms"):
            pyth_prices.updateStaleTime(alpha_token, 200, sender=bob)

        assert pyth_prices.updateStaleTime(
            alpha_token, 200, sender=governance.address
        )
        pending = pyth_prices.pendingUpdates(alpha_token)
        assert pending.actionId != 0
        assert pending.config.feedId == SC20_PYTH_FEED_ID
        assert pending.config.staleTime == 200
        assert pyth_prices.feedConfig(alpha_token).staleTime == 100
        assert pyth_prices.getPrice(alpha_token) == SC20_PYTH_PRICE

        with boa.reverts("time lock not reached"):
            pyth_prices.confirmPriceFeedUpdate(
                alpha_token, sender=governance.address
            )
        advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
        _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)
        assert pyth_prices.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert pyth_prices.feedConfig(alpha_token).staleTime == 200

        assert not pyth_prices.isValidStaleTimeUpdate(alpha_token, 200)
        with boa.reverts("invalid feed"):
            pyth_prices.updateStaleTime(
                alpha_token, 200, sender=governance.address
            )

        assert pyth_prices.updateStaleTime(
            alpha_token, 0, sender=governance.address
        )
        assert pyth_prices.cancelPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert pyth_prices.feedConfig(alpha_token).staleTime == 200
        assert pyth_prices.pendingUpdates(alpha_token).actionId == 0

    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_pyth_feed(
            pyth_prices, mock_pyth, alpha_token, governance, 100
        )
        _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)
        assert pyth_prices.updateStaleTime(
            alpha_token, 10, sender=governance.address
        )
        advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
        boa.env.time_travel(seconds=11)

        assert pyth_prices.getPrice(alpha_token) == SC20_PYTH_PRICE
        assert not pyth_prices.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert pyth_prices.feedConfig(alpha_token).staleTime == 100
        assert pyth_prices.pendingUpdates(alpha_token).actionId == 0


def test_pyth_stale_time_update_to_zero_confirms_global_inheritance(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_pyth_feed(
            pyth_prices, mock_pyth, alpha_token, governance, 200
        )

        assert pyth_prices.updateStaleTime(
            alpha_token, 0, sender=governance.address
        )
        pending = pyth_prices.pendingUpdates(alpha_token)
        assert pending.actionId != 0
        assert pending.config.feedId == SC20_PYTH_FEED_ID
        assert pending.config.staleTime == 0
        assert pyth_prices.feedConfig(alpha_token).staleTime == 200

        advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
        boa.env.time_travel(seconds=1)
        _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)
        assert pyth_prices.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        stored = pyth_prices.feedConfig(alpha_token)
        assert stored.feedId == SC20_PYTH_FEED_ID
        assert stored.staleTime == 0
        assert pyth_prices.pendingUpdates(alpha_token).actionId == 0

        boa.env.time_travel(seconds=100)
        assert pyth_prices.getPrice(alpha_token) == SC20_PYTH_PRICE
        assert pyth_prices.getPriceAndHasFeed(alpha_token) == (
            SC20_PYTH_PRICE,
            True,
        )
        boa.env.time_travel(seconds=1)
        assert pyth_prices.getPrice(alpha_token) == 0
        assert pyth_prices.getPriceAndHasFeed(alpha_token) == (0, True)


@pytest.mark.parametrize(
    "invalid_global", [0, MAX_FEED_STALE_TIME + 1]
)
@pytest.mark.parametrize(
    "pending_stale_time,should_confirm", [(0, False), (200, True)]
)
def test_pyth_stale_time_confirmation_revalidates_inherited_policy(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    setGeneralConfig,
    invalid_global,
    pending_stale_time,
    should_confirm,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_pyth_feed(
            pyth_prices, mock_pyth, alpha_token, governance, 300
        )
        assert pyth_prices.updateStaleTime(
            alpha_token,
            pending_stale_time,
            sender=governance.address,
        )
        pending = pyth_prices.pendingUpdates(alpha_token)
        assert pending.actionId != 0
        assert pending.config.feedId == SC20_PYTH_FEED_ID
        assert pending.config.staleTime == pending_stale_time

        setGeneralConfig(_priceStaleTime=invalid_global)
        advance_timelock_blocks(pyth_prices.actionTimeLock() + 1)
        boa.env.time_travel(seconds=1)
        _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)

        assert pyth_prices.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        ) is should_confirm
        stored = pyth_prices.feedConfig(alpha_token)
        assert stored.feedId == SC20_PYTH_FEED_ID
        assert stored.staleTime == (200 if should_confirm else 300)
        cleared = pyth_prices.pendingUpdates(alpha_token)
        assert cleared.actionId == 0
        assert cleared.config.feedId == bytes(32)
        assert cleared.config.staleTime == 0
        assert pyth_prices.getPrice(alpha_token) == SC20_PYTH_PRICE
        assert pyth_prices.getPriceAndHasFeed(alpha_token) == (
            SC20_PYTH_PRICE,
            True,
        )


def test_pyth_inherited_policy_fails_closed_without_mission_control(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    ripe_hq,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_pyth_feed(
            pyth_prices, mock_pyth, alpha_token, governance, 0
        )
        _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)
        assert pyth_prices.getPrice(alpha_token) == SC20_PYTH_PRICE

        assert ripe_hq.getAddr(5) != ZERO_ADDRESS
        ripe_hq.eval("registry.addrInfo[5].addr = empty(address)")
        assert ripe_hq.getAddr(5) == ZERO_ADDRESS
        assert pyth_prices.getPrice(alpha_token) == 0
        assert pyth_prices.getPriceAndHasFeed(alpha_token) == (0, True)


@pytest.mark.parametrize(
    "candidate",
    [0, 1, 100, MAX_FEED_STALE_TIME, MAX_FEED_STALE_TIME + 1],
)
def test_pyth_stale_time_preflight_matches_initiation(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    setGeneralConfig,
    candidate,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_pyth_feed(
            pyth_prices, mock_pyth, alpha_token, governance, 100
        )
        _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)
        expected = candidate not in (100, MAX_FEED_STALE_TIME + 1)
        assert pyth_prices.isValidStaleTimeUpdate(
            alpha_token, candidate
        ) is expected
        with boa.env.anchor():
            if expected:
                assert pyth_prices.updateStaleTime(
                    alpha_token, candidate, sender=governance.address
                )
            else:
                with boa.reverts("invalid feed"):
                    pyth_prices.updateStaleTime(
                        alpha_token, candidate, sender=governance.address
                    )


def test_pyth_inherited_zero_preflight_rejects_zero_global(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_pyth_feed(
            pyth_prices, mock_pyth, alpha_token, governance, 100
        )
        setGeneralConfig(_priceStaleTime=0)
        assert not pyth_prices.isValidStaleTimeUpdate(alpha_token, 0)
        with boa.reverts("invalid feed"):
            pyth_prices.updateStaleTime(
                alpha_token, 0, sender=governance.address
            )


def _start_pyth_pending_action(
    kind,
    pyth_prices,
    mock_pyth,
    asset,
    governance,
):
    _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)
    _set_sc20_pyth_price(
        mock_pyth, boa.env.timestamp, SC20_PYTH_ALT_FEED_ID
    )
    if kind == "add":
        assert pyth_prices.addNewPriceFeed(
            asset, SC20_PYTH_FEED_ID, 100, sender=governance.address
        )
        return

    _add_sc20_pyth_feed(
        pyth_prices, mock_pyth, asset, governance, 100
    )
    if kind == "update":
        assert pyth_prices.updatePriceFeed(
            asset,
            SC20_PYTH_ALT_FEED_ID,
            100,
            sender=governance.address,
        )
    elif kind == "stale":
        assert pyth_prices.updateStaleTime(
            asset, 200, sender=governance.address
        )
    else:
        assert kind == "disable"
        assert pyth_prices.disablePriceFeed(
            asset, sender=governance.address
        )


def _pyth_action_state(source, asset):
    pending = source.pendingUpdates(asset)
    active = source.feedConfig(asset)
    return (
        source.hasPendingPriceFeedUpdate(asset),
        pending.actionId,
        pending.config.feedId,
        pending.config.staleTime,
        source.hasPriceFeed(asset),
        active.feedId,
        active.staleTime,
    )


def _pyth_wrong_action_selectors(pending_kind):
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
def test_pyth_pending_action_blocks_initiators_and_wrong_selectors(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    setGeneralConfig,
    pending_kind,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _start_pyth_pending_action(
            pending_kind,
            pyth_prices,
            mock_pyth,
            alpha_token,
            governance,
        )
        before = _pyth_action_state(pyth_prices, alpha_token)

        attempts = (
            lambda: pyth_prices.addNewPriceFeed(
                alpha_token,
                SC20_PYTH_FEED_ID,
                100,
                sender=governance.address,
            ),
            lambda: pyth_prices.updatePriceFeed(
                alpha_token,
                SC20_PYTH_ALT_FEED_ID,
                100,
                sender=governance.address,
            ),
            lambda: pyth_prices.updateStaleTime(
                alpha_token, 300, sender=governance.address
            ),
            lambda: pyth_prices.disablePriceFeed(
                alpha_token, sender=governance.address
            ),
        )
        for attempt in attempts:
            with boa.reverts("pending feed action"):
                attempt()
            assert _pyth_action_state(pyth_prices, alpha_token) == before

        for reason, selector in _pyth_wrong_action_selectors(pending_kind):
            with boa.reverts(reason):
                getattr(pyth_prices, selector)(
                    alpha_token, sender=governance.address
                )
            assert _pyth_action_state(pyth_prices, alpha_token) == before


@pytest.mark.parametrize("pending_kind", ["add", "update", "stale", "disable"])
def test_pyth_expired_pending_action_requires_cleanup(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    setGeneralConfig,
    pending_kind,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _start_pyth_pending_action(
            pending_kind,
            pyth_prices,
            mock_pyth,
            alpha_token,
            governance,
        )
        advance_timelock_blocks(
            pyth_prices.actionTimeLock() + pyth_prices.expiration()
        )
        assert pyth_prices.hasPendingPriceFeedUpdate(alpha_token)
        with boa.reverts("pending feed action"):
            pyth_prices.updateStaleTime(
                alpha_token, 300, sender=governance.address
            )

        if pending_kind == "add":
            assert pyth_prices.cancelNewPendingPriceFeed(
                alpha_token, sender=governance.address
            )
            assert pyth_prices.addNewPriceFeed(
                alpha_token,
                SC20_PYTH_FEED_ID,
                100,
                sender=governance.address,
            )
        elif pending_kind in ("update", "stale"):
            assert pyth_prices.cancelPriceFeedUpdate(
                alpha_token, sender=governance.address
            )
            assert pyth_prices.updateStaleTime(
                alpha_token, 300, sender=governance.address
            )
        else:
            assert pyth_prices.cancelDisablePriceFeed(
                alpha_token, sender=governance.address
            )
            assert pyth_prices.disablePriceFeed(
                alpha_token, sender=governance.address
            )


def test_pyth_raw_accessor_ignores_staleness_but_not_future_data(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=10)
        _add_sc20_pyth_feed(
            pyth_prices, mock_pyth, alpha_token, governance, 0
        )
        publish_time = boa.env.timestamp
        _set_sc20_pyth_price(mock_pyth, publish_time)
        boa.env.time_travel(seconds=11)

        assert pyth_prices.getPrice(alpha_token) == 0
        assert pyth_prices.getPriceAndHasFeed(alpha_token) == (0, True)
        assert pyth_prices.getLastPriceAndLastUpdate(alpha_token) == (
            SC20_PYTH_PRICE,
            publish_time,
        )

        _set_sc20_pyth_price(mock_pyth, boa.env.timestamp + 1)
        assert pyth_prices.getLastPriceAndLastUpdate(alpha_token) == (0, 0)


def test_pyth_future_timestamp_is_fail_soft_and_recovers(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
):
    _add_sc20_pyth_feed(
        pyth_prices, mock_pyth, alpha_token, governance, 100
    )
    future_time = boa.env.timestamp + 100
    _set_sc20_pyth_price(mock_pyth, future_time)

    assert pyth_prices.getPrice(alpha_token) == 0
    assert pyth_prices.getPriceAndHasFeed(alpha_token) == (0, True)
    assert pyth_prices.getLastPriceAndLastUpdate(alpha_token) == (0, 0)

    boa.env.time_travel(seconds=100)
    assert pyth_prices.getPrice(alpha_token) == SC20_PYTH_PRICE


def test_pyth_current_timestamp_is_valid(
    pyth_prices,
    mock_pyth,
    alpha_token,
    governance,
):
    _add_sc20_pyth_feed(
        pyth_prices, mock_pyth, alpha_token, governance, 1
    )
    _set_sc20_pyth_price(mock_pyth, boa.env.timestamp)
    assert pyth_prices.getPrice(alpha_token) == SC20_PYTH_PRICE
