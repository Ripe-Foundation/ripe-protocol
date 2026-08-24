import boa
import pytest

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS
from conf_utils import filter_logs, advance_timelock_blocks
from config.BluePrint import CORE_TOKENS

MONTH_IN_SECONDS = 30 * 24 * 60 * 60
MAX_FEED_STALE_TIME = 7 * 24 * 60 * 60
MIN_LOCAL_STALE_TIME = 5 * 60
NOT_FOUND_REVERT = "Revert(b'\\xc5r;Q')"


@pytest.fixture(autouse=True)
def default_price_stale_time(setGeneralConfig):
    setGeneralConfig(_priceStaleTime=24 * 60 * 60)


@pytest.fixture(scope="module")
def addStorkFeed(stork_prices, governance):
    def addStorkFeed(_asset, _feed_id, _stale_time=0):
        if stork_prices.hasPriceFeed(_asset):
            return
        assert stork_prices.addNewPriceFeed(_asset, _feed_id, _stale_time, sender=governance.address)
        advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
        assert stork_prices.confirmNewPriceFeed(_asset, sender=governance.address)
    yield addStorkFeed


@pytest.fixture(scope="module")
def authorized_caller(switchboard_alpha, mission_control, governance, bob):
    """Grant canPerformLiteAction permission to bob for oracle updates"""
    action_id = switchboard_alpha.setCanPerformLiteAction(bob, True, sender=governance.address)
    advance_timelock_blocks(switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    assert mission_control.canPerformLiteAction(bob)
    return bob


###################
# Unique to Stork #
###################


def test_stork_local_update_prices(
    stork_prices,
    mock_stork,
    alpha_token,
    authorized_caller,
    addStorkFeed,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    addStorkFeed(alpha_token, data_feed_id)
    assert stork_prices.getPrice(alpha_token) != 0

    # get payload
    publish_time = boa.env.evm.patch.timestamp
    payload = mock_stork.createPriceFeedUpdateData(
        data_feed_id,
        998888888000000000,
        publish_time,
    )
    exp_fee = 1

    # insufficient payment
    with boa.reverts("payment required"):
        stork_prices.updateStorkPrice([payload], sender=authorized_caller, value=0)

    # success - caller provides payment
    assert boa.env.get_balance(mock_stork.address) == 0
    boa.env.set_balance(authorized_caller, EIGHTEEN_DECIMALS)
    pre_switchboard_bal = boa.env.get_balance(authorized_caller)

    assert stork_prices.updateStorkPrice([payload], sender=authorized_caller, value=EIGHTEEN_DECIMALS)

    log = filter_logs(stork_prices, 'StorkPriceUpdated')[0]
    assert list(log.payload) == [payload]
    assert log.feeAmount == exp_fee
    assert log.caller == authorized_caller

    # Check that fee was paid and excess was refunded
    assert boa.env.get_balance(mock_stork.address) == exp_fee
    assert boa.env.get_balance(authorized_caller) == pre_switchboard_bal - exp_fee

    # check mock stork
    price_data = mock_stork.priceFeeds(data_feed_id)
    assert price_data.quantizedValue == 998888888000000000
    assert price_data.timestampNs == publish_time * 1_000_000_000

    assert int(1 * EIGHTEEN_DECIMALS) > stork_prices.getPrice(alpha_token) > int(0.97 * EIGHTEEN_DECIMALS)


def test_stork_recover_eth(
    stork_prices,
    bob,
    governance,
):
    # no balance
    with boa.reverts("invalid recipient or balance"):
        stork_prices.recoverEthBalance(bob, sender=governance.address)

    # Add ETH balance to contract
    initial_balance = EIGHTEEN_DECIMALS  # 1 ETH
    boa.env.set_balance(stork_prices.address, initial_balance)
    assert boa.env.get_balance(stork_prices.address) == initial_balance

    # No perms check
    with boa.reverts("no perms"):
        stork_prices.recoverEthBalance(bob, sender=bob)

    # Invalid recipient check
    with boa.reverts("invalid recipient or balance"):
        stork_prices.recoverEthBalance(ZERO_ADDRESS, sender=governance.address)

    # Success case
    pre_bob_balance = boa.env.get_balance(bob)
    assert stork_prices.recoverEthBalance(bob, sender=governance.address)
    log = filter_logs(stork_prices, 'EthRecoveredFromStork')[0]

    # Check balances
    assert boa.env.get_balance(stork_prices.address) == 0
    assert boa.env.get_balance(bob) == pre_bob_balance + initial_balance

    # Check event
    assert log.recipient == bob
    assert log.amount == initial_balance


@pytest.mark.parametrize(
    'quantized_value, expected_price',
    [
        (1000000000000000000, 1000000000000000000),  # 1.0 ETH price
        (0, 0),  # Zero price
        (500000000000000000, 500000000000000000),  # 0.5 ETH price
        (2500000000000000000000, 2500000000000000000000),  # 2500 ETH price (like ETH/USD)
        (1, 1),  # Minimal price value
        (999999999999999999, 999999999999999999),  # Just under 1 ETH
        (18446744073709551615, 18446744073709551615),  # Max uint64 value
        (123456789012345678, 123456789012345678),  # Random value
    ]
)
def test_stork_get_price(
    stork_prices,
    mock_stork,
    alpha_token,
    authorized_caller,
    addStorkFeed,
    quantized_value,
    expected_price,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    addStorkFeed(alpha_token, data_feed_id)

    # get payload
    publish_time = boa.env.evm.patch.timestamp
    payload = mock_stork.createPriceFeedUpdateData(
        data_feed_id,
        quantized_value,
        publish_time,
    )

    # update price - caller provides payment
    boa.env.set_balance(authorized_caller, 10 * EIGHTEEN_DECIMALS)
    assert stork_prices.updateStorkPrice([payload], sender=authorized_caller, value=EIGHTEEN_DECIMALS)

    # test price
    assert stork_prices.getPrice(alpha_token) == expected_price


def test_stork_get_price_and_has_feed(
    stork_prices,
    alpha_token,
    bravo_token,
    addStorkFeed,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    
    # Test with no feed
    price, has_feed = stork_prices.getPriceAndHasFeed(bravo_token)
    assert price == 0
    assert not has_feed

    # Add feed
    addStorkFeed(alpha_token, data_feed_id)
    
    # Test with feed
    price, has_feed = stork_prices.getPriceAndHasFeed(alpha_token)
    assert price != 0
    assert has_feed


def test_stork_get_price_stale(
    stork_prices,
    mock_stork,
    alpha_token,
    authorized_caller,
    addStorkFeed,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    _set_sc20_stork_price(mock_stork, boa.env.timestamp)
    addStorkFeed(alpha_token, data_feed_id, 3600)
    assert stork_prices.getPrice(alpha_token) != 0

    # get payload with stale timestamp
    publish_time = boa.env.evm.patch.timestamp - 3601  # 1 hour and 1 second ago, > stale time (3600s)
    payload = mock_stork.createPriceFeedUpdateData(
        data_feed_id,
        998000000000000000,
        publish_time,
    )

    # Give authorized_caller ETH for payment
    boa.env.set_balance(authorized_caller, 10 * EIGHTEEN_DECIMALS)

    # success update price
    assert stork_prices.updateStorkPrice([payload], sender=authorized_caller, value=EIGHTEEN_DECIMALS)

    # price should be 0 due to staleness
    assert stork_prices.getPrice(alpha_token) == 0


def test_stork_price_stale_with_feed_config(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
):
    stale_time = 3600
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")

    _set_sc20_stork_price(mock_stork, boa.env.timestamp)
    assert stork_prices.addNewPriceFeed(
        alpha_token, data_feed_id, stale_time, sender=governance.address
    )
    advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
    _set_sc20_stork_price(mock_stork, boa.env.timestamp)
    assert stork_prices.confirmNewPriceFeed(
        alpha_token, sender=governance.address
    )

    config = stork_prices.feedConfig(alpha_token)
    assert config.feedId == data_feed_id
    assert config.staleTime == stale_time
    assert stork_prices.getPrice(alpha_token) != 0

    boa.env.time_travel(seconds=stale_time)
    assert stork_prices.getPrice(alpha_token) != 0
    boa.env.time_travel(seconds=1)
    assert stork_prices.getPrice(alpha_token) == 0


def test_stork_is_valid_feed(
    stork_prices,
    alpha_token,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    invalid_feed_id = bytes.fromhex("f" * 64)

    # valid feed (exists in MockStork)
    assert stork_prices.isValidNewFeed(alpha_token, data_feed_id, 0)

    # unknown feed id: production Stork reverts NotFound(); MockStork matches
    with boa.reverts(NOT_FOUND_REVERT):
        stork_prices.isValidNewFeed(alpha_token, invalid_feed_id, 0)

    # invalid asset
    assert not stork_prices.isValidNewFeed(ZERO_ADDRESS, data_feed_id, 0)


######################
# Add New Feed Tests #
######################


def test_stork_add_price_feed(
    stork_prices,
    alpha_token,
    governance,
    bob,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")

    # Test unauthorized access
    with boa.reverts("no perms"):
        stork_prices.addNewPriceFeed(alpha_token, data_feed_id, sender=bob)

    # Test adding unset feed (production Stork NotFound)
    invalid_feed_id = bytes.fromhex("f" * 64)
    with boa.reverts(NOT_FOUND_REVERT):
        stork_prices.addNewPriceFeed(alpha_token, invalid_feed_id, 0, sender=governance.address)
    assert not stork_prices.hasPendingPriceFeedUpdate(alpha_token)
    assert not stork_prices.hasPriceFeed(alpha_token)

    # Test adding feed with zero address asset
    with boa.reverts("invalid feed"):
        stork_prices.addNewPriceFeed(ZERO_ADDRESS, data_feed_id, 0, sender=governance.address)

    # Test successful feed addition
    assert stork_prices.addNewPriceFeed(alpha_token, data_feed_id, 0, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "NewStorkFeedPending")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id
    assert log.staleTime == 0

    # Verify pending state
    assert stork_prices.hasPendingPriceFeedUpdate(alpha_token)
    pending = stork_prices.pendingUpdates(alpha_token)
    assert pending.config.feedId == data_feed_id

    # Test confirming before time lock
    with boa.reverts("time lock not reached"):
        stork_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Travel past time lock
    advance_timelock_blocks(stork_prices.actionTimeLock() + 1)

    # Test confirming
    assert stork_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "NewStorkFeedAdded")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id
    assert log.staleTime == 0

    # Verify feed is active
    assert stork_prices.hasPriceFeed(alpha_token)
    assert stork_prices.feedConfig(alpha_token).feedId == data_feed_id
    assert stork_prices.getPrice(alpha_token) != 0
    assert not stork_prices.hasPendingPriceFeedUpdate(alpha_token)

    # Test canceling non-existent feed
    with boa.reverts("no pending new feed"):
        stork_prices.cancelNewPendingPriceFeed(alpha_token, sender=governance.address)

    # Test adding feed for existing asset
    with boa.reverts("invalid feed"):
        stork_prices.addNewPriceFeed(alpha_token, data_feed_id, 0, sender=governance.address)


def test_stork_add_price_feed_cancel(
    stork_prices,
    alpha_token,
    governance,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")

    # Add feed
    assert stork_prices.addNewPriceFeed(alpha_token, data_feed_id, 0, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "NewStorkFeedPending")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id
    assert log.staleTime == 0

    # Cancel feed
    assert stork_prices.cancelNewPendingPriceFeed(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "NewStorkFeedCancelled")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id

    # Verify feed is not active
    assert not stork_prices.hasPriceFeed(alpha_token)
    assert stork_prices.getPrice(alpha_token) == 0
    assert not stork_prices.hasPendingPriceFeedUpdate(alpha_token)

    # Test confirming after cancel
    with boa.reverts("no pending new feed"):
        stork_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)


def test_stork_add_price_feed_validation_during_confirm(
    stork_prices,
    alpha_token,
    mock_stork,
    governance,
):
    # Use a different feed ID that doesn't exist initially
    invalid_feed_id = bytes.fromhex("8416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290d")

    # Setup the feed first so validation passes during add
    payload = mock_stork.createPriceFeedUpdateData(invalid_feed_id, 998000000000000000, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_stork.updateTemporalNumericValuesV1([payload], value=1)
    
    assert stork_prices.addNewPriceFeed(alpha_token, invalid_feed_id, 0, sender=governance.address)
    
    # Travel past time lock
    advance_timelock_blocks(stork_prices.actionTimeLock() + 1)

    # Invalidate with a negative quantized value. Ordinary validation
    # failures returned normally still auto-cancel during confirmation.
    # Timestamp-zero / NotFound is not an ordinary validation failure:
    # it bubbles and leaves the pending action intact (covered separately).
    invalid_payload = mock_stork.createPriceFeedUpdateData(
        invalid_feed_id, -1, boa.env.evm.patch.timestamp
    )
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_stork.updateTemporalNumericValuesV1([invalid_payload], value=1)

    # Confirm should fail and auto-cancel due to the negative value
    assert not stork_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)
    
    # Verify feed was cancelled
    assert not stork_prices.hasPriceFeed(alpha_token)
    assert not stork_prices.hasPendingPriceFeedUpdate(alpha_token)


#####################
# Update Feed Tests #
#####################


def test_stork_update_price_feed(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    bob,
    addStorkFeed,
):
    data_feed_id_1 = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    data_feed_id_2 = bytes.fromhex("8416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290d")
    
    # Setup the second feed in MockStork
    payload_2 = mock_stork.createPriceFeedUpdateData(data_feed_id_2, 970000000000000000, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_stork.updateTemporalNumericValuesV1([payload_2], value=1)

    # Add initial feed
    addStorkFeed(alpha_token, data_feed_id_1)

    # Test unauthorized access
    with boa.reverts("no perms"):
        stork_prices.updatePriceFeed(alpha_token, data_feed_id_2, 0, sender=bob)

    # Test updating with same feed
    with boa.reverts("invalid feed"):
        stork_prices.updatePriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)

    # Test updating non-existent asset
    with boa.reverts("invalid feed"):
        stork_prices.updatePriceFeed(ZERO_ADDRESS, data_feed_id_2, 0, sender=governance.address)

    # Test updating with an unset feed (production Stork NotFound)
    invalid_feed_id = bytes.fromhex("f" * 64)
    with boa.reverts(NOT_FOUND_REVERT):
        stork_prices.updatePriceFeed(alpha_token, invalid_feed_id, 0, sender=governance.address)
    assert stork_prices.feedConfig(alpha_token).feedId == data_feed_id_1
    assert not stork_prices.hasPendingPriceFeedUpdate(alpha_token)

    # Test successful update
    assert stork_prices.updatePriceFeed(alpha_token, data_feed_id_2, 0, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "StorkFeedUpdatePending")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id_2
    assert log.staleTime == 0
    assert log.oldFeedId == data_feed_id_1

    # Test confirming before time lock
    with boa.reverts("time lock not reached"):
        stork_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    # Travel past time lock
    advance_timelock_blocks(stork_prices.actionTimeLock() + 1)

    # Test confirming
    assert stork_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "StorkFeedUpdated")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id_2
    assert log.staleTime == 0
    assert log.oldFeedId == data_feed_id_1

    # Verify feed is updated
    assert stork_prices.hasPriceFeed(alpha_token)
    assert stork_prices.feedConfig(alpha_token).feedId == data_feed_id_2
    assert stork_prices.getPrice(alpha_token) != 0

    # Test canceling non-existent update
    with boa.reverts("no pending update feed"):
        stork_prices.cancelPriceFeedUpdate(alpha_token, sender=governance.address)


def test_stork_update_price_feed_cancel(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    addStorkFeed,
):
    data_feed_id_1 = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    data_feed_id_2 = bytes.fromhex("8416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290d")
    
    # Setup the second feed in MockStork
    payload_2 = mock_stork.createPriceFeedUpdateData(data_feed_id_2, 970000000000000000, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_stork.updateTemporalNumericValuesV1([payload_2], value=1)

    # Add initial feed
    addStorkFeed(alpha_token, data_feed_id_1)

    # Start update
    assert stork_prices.updatePriceFeed(alpha_token, data_feed_id_2, 0, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "StorkFeedUpdatePending")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id_2
    assert log.staleTime == 0
    assert log.oldFeedId == data_feed_id_1

    # Cancel update
    assert stork_prices.cancelPriceFeedUpdate(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "StorkFeedUpdateCancelled")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id_2
    assert log.oldFeedId == data_feed_id_1

    # Verify feed is not updated
    assert stork_prices.hasPriceFeed(alpha_token)
    assert stork_prices.feedConfig(alpha_token).feedId == data_feed_id_1
    assert not stork_prices.hasPendingPriceFeedUpdate(alpha_token)

    # Test confirming after cancel
    with boa.reverts("no pending update feed"):
        stork_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)


def test_stork_update_feed_validation_functions(
    stork_prices,
    mock_stork,
    alpha_token,
    bravo_token,
    addStorkFeed,
):
    data_feed_id_1 = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    data_feed_id_2 = bytes.fromhex("8416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290d")
    
    # Setup the second feed in MockStork
    payload_2 = mock_stork.createPriceFeedUpdateData(data_feed_id_2, 970000000000000000, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_stork.updateTemporalNumericValuesV1([payload_2], value=1)
    invalid_feed_id = bytes.fromhex("f" * 64)

    # Add initial feed
    addStorkFeed(alpha_token, data_feed_id_1)

    # Test isValidUpdateFeed function
    assert stork_prices.isValidUpdateFeed(alpha_token, data_feed_id_2, 0)  # Valid update
    assert not stork_prices.isValidUpdateFeed(alpha_token, data_feed_id_1, 0)  # Same feed
    assert not stork_prices.isValidUpdateFeed(bravo_token, data_feed_id_2, 0)  # No existing feed
    with boa.reverts(NOT_FOUND_REVERT):
        stork_prices.isValidUpdateFeed(alpha_token, invalid_feed_id, 0)


######################
# Disable Feed Tests #
######################


def test_stork_disable_price_feed(
    stork_prices,
    alpha_token,
    governance,
    bob,
    addStorkFeed,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")

    # Add initial feed
    addStorkFeed(alpha_token, data_feed_id)

    # Test unauthorized access
    with boa.reverts("no perms"):
        stork_prices.disablePriceFeed(alpha_token, sender=bob)

    # Test disabling non-existent feed
    with boa.reverts("invalid asset"):
        stork_prices.disablePriceFeed(ZERO_ADDRESS, sender=governance.address)

    # Test successful disable
    assert stork_prices.disablePriceFeed(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "DisableStorkFeedPending")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id

    # Test confirming before time lock
    with boa.reverts("time lock not reached"):
        stork_prices.confirmDisablePriceFeed(alpha_token, sender=governance.address)

    # Travel past time lock
    advance_timelock_blocks(stork_prices.actionTimeLock() + 1)

    # Test confirming
    assert stork_prices.confirmDisablePriceFeed(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "StorkFeedDisabled")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id

    # Verify feed is disabled
    assert not stork_prices.hasPriceFeed(alpha_token)
    assert stork_prices.getPrice(alpha_token) == 0
    assert stork_prices.feedConfig(alpha_token).feedId == bytes(32)

    # Test canceling non-existent disable
    with boa.reverts("no pending disable feed"):
        stork_prices.cancelDisablePriceFeed(alpha_token, sender=governance.address)


def test_stork_disable_price_feed_cancel(
    stork_prices,
    alpha_token,
    governance,
    addStorkFeed,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")

    # Add initial feed
    addStorkFeed(alpha_token, data_feed_id)

    # Start disable
    assert stork_prices.disablePriceFeed(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "DisableStorkFeedPending")[0]
    assert log.asset == alpha_token.address

    # Cancel disable
    assert stork_prices.cancelDisablePriceFeed(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "DisableStorkFeedCancelled")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id

    # Verify feed is still active
    assert stork_prices.hasPriceFeed(alpha_token)
    assert stork_prices.getPrice(alpha_token) != 0
    assert stork_prices.feedConfig(alpha_token).feedId == data_feed_id

    # Test confirming after cancel
    with boa.reverts("no pending disable feed"):
        stork_prices.confirmDisablePriceFeed(alpha_token, sender=governance.address)


def test_stork_disable_feed_validation_functions(
    stork_prices,
    alpha_token,
    bravo_token,
    addStorkFeed,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")

    # Add initial feed
    addStorkFeed(alpha_token, data_feed_id)

    # Test isValidDisablePriceFeed function
    assert stork_prices.isValidDisablePriceFeed(alpha_token)  # Valid disable
    assert not stork_prices.isValidDisablePriceFeed(bravo_token)  # No existing feed


#############################
# Edge Cases and Validation #
#############################


def test_stork_price_stale_edge_cases(
    stork_prices,
    mock_stork,
    alpha_token,
    authorized_caller,
    addStorkFeed,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    addStorkFeed(alpha_token, data_feed_id, MIN_LOCAL_STALE_TIME)

    # Give authorized_caller enough ETH for all tests
    boa.env.set_balance(authorized_caller, 100 * EIGHTEEN_DECIMALS)

    # Test price exactly at stale time boundary
    publish_time = boa.env.evm.patch.timestamp
    payload = mock_stork.createPriceFeedUpdateData(data_feed_id, 998000000000000000, publish_time)
    assert stork_prices.updateStorkPrice([payload], sender=authorized_caller, value=EIGHTEEN_DECIMALS)

    # Test price just at stale boundary (should still be valid)
    assert stork_prices.getPrice(alpha_token) != 0
    boa.env.time_travel(seconds=MIN_LOCAL_STALE_TIME)
    assert stork_prices.getPrice(alpha_token) != 0

    # Test price just over stale boundary
    boa.env.time_travel(seconds=1)
    assert stork_prices.getPrice(alpha_token) == 0


def test_stork_time_lock_edge_cases(
    stork_prices,
    mock_stork,
    alpha_token,
    bravo_token,
    governance,
):
    data_feed_id_1 = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    data_feed_id_2 = bytes.fromhex("8416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290d")

    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)
    payload_1 = mock_stork.createPriceFeedUpdateData(data_feed_id_1, 998000000000000000, boa.env.evm.patch.timestamp)
    payload_2 = mock_stork.createPriceFeedUpdateData(data_feed_id_2, 970000000000000000, boa.env.evm.patch.timestamp)
    mock_stork.updateTemporalNumericValuesV1([payload_1, payload_2], value=2)

    # Test confirming just before time lock boundary
    assert stork_prices.addNewPriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)
    advance_timelock_blocks(stork_prices.actionTimeLock() - 1)
    with boa.reverts("time lock not reached"):
        stork_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test confirming at time lock boundary
    advance_timelock_blocks(1)
    assert stork_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test multiple time lock actions in sequence
    assert stork_prices.updatePriceFeed(alpha_token, data_feed_id_2, 0, sender=governance.address)
    advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
    assert stork_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    
    assert stork_prices.disablePriceFeed(alpha_token, sender=governance.address)
    advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
    assert stork_prices.confirmDisablePriceFeed(alpha_token, sender=governance.address)

    # Test with different time lock values
    stork_prices.setActionTimeLock(302400, sender=governance.address)  # 7 days in blocks
    assert stork_prices.addNewPriceFeed(bravo_token, data_feed_id_1, 0, sender=governance.address)
    advance_timelock_blocks(302400)
    assert stork_prices.confirmNewPriceFeed(bravo_token, sender=governance.address)


def test_stork_governance_edge_cases(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    switchboard_alpha,
):
    data_feed_id_1 = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    data_feed_id_2 = bytes.fromhex("8416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290d")
    
    # Setup the second feed in MockStork
    payload_2 = mock_stork.createPriceFeedUpdateData(data_feed_id_2, 970000000000000000, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_stork.updateTemporalNumericValuesV1([payload_2], value=1)

    # Test multiple governance actions in sequence
    assert stork_prices.addNewPriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)
    assert stork_prices.cancelNewPendingPriceFeed(alpha_token, sender=governance.address)
    assert stork_prices.addNewPriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)
    advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
    assert stork_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)
    assert stork_prices.updatePriceFeed(alpha_token, data_feed_id_2, 0, sender=governance.address)
    advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
    assert stork_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    # Test governance actions during pause (using switchboard address)
    stork_prices.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        stork_prices.addNewPriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)
    with boa.reverts("contract paused"):
        stork_prices.updatePriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)
    with boa.reverts("contract paused"):
        stork_prices.updateStaleTime(
            alpha_token, 3_600, sender=governance.address
        )
    with boa.reverts("contract paused"):
        stork_prices.disablePriceFeed(alpha_token, sender=governance.address)

    # Test governance actions after unpause
    stork_prices.pause(False, sender=switchboard_alpha.address)
    # First disable the existing feed
    assert stork_prices.disablePriceFeed(alpha_token, sender=governance.address)
    advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
    assert stork_prices.confirmDisablePriceFeed(alpha_token, sender=governance.address)
    # Now we can add a new feed
    assert stork_prices.addNewPriceFeed(alpha_token, data_feed_id_1, 0, sender=governance.address)


def test_stork_feed_validation_edge_cases(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
):
    bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")

    # Production Stork reverts with NotFound() when timestampNs is zero.
    # MockStork matches that; StorkPrices does not treat timestamp zero
    # as an ordinary invalid result.
    zero_timestamp_feed_id = bytes.fromhex("9416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290e")
    
    zero_payload = mock_stork.createPriceFeedUpdateData(zero_timestamp_feed_id, 998000000000000000, 0)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_stork.updateTemporalNumericValuesV1([zero_payload], value=1)

    with boa.reverts(NOT_FOUND_REVERT):
        stork_prices.addNewPriceFeed(alpha_token, zero_timestamp_feed_id, 0, sender=governance.address)

    # Fix the timestamp and it should work
    fresh_payload = mock_stork.createPriceFeedUpdateData(zero_timestamp_feed_id, 998000000000000000, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_stork.updateTemporalNumericValuesV1([fresh_payload], value=1)
    assert stork_prices.addNewPriceFeed(alpha_token, zero_timestamp_feed_id, 0, sender=governance.address)


@pytest.base
def test_set_stork_feed_cbtc(
    stork_prices,
    fork,
    addStorkFeed,
    setGeneralConfig,
    mission_control,
):
    cbtc = CORE_TOKENS[fork]["CBBTC"]
    # Official keccak256("BTCUSD") asset id. The value is on the pinned
    # Stork contract, but older than MissionControl's 1-day global window.
    data_feed_id = bytes.fromhex("7404e3d104ea7841c3d9e6fd20adfe99b4ad586bc08d8f3bd3afef894cf184de")
    previous_stale = mission_control.getPriceStaleTime()
    if not stork_prices.isValidNewFeed(cbtc, data_feed_id, 0):
        setGeneralConfig(_priceStaleTime=0)
    try:
        addStorkFeed(cbtc, data_feed_id)
        assert stork_prices.feedConfig(cbtc).feedId == data_feed_id
        price = stork_prices.getPrice(cbtc)
        assert price != 0
        assert 10_000 * EIGHTEEN_DECIMALS < price < 250_000 * EIGHTEEN_DECIMALS
    finally:
        setGeneralConfig(_priceStaleTime=previous_stale)


SC20_STORK_FEED_ID = bytes.fromhex(
    "7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c"
)
SC20_STORK_ALT_FEED_ID = bytes.fromhex(
    "8416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290d"
)
SC20_STORK_PRICE = 998_000_000_000_000_000


def _set_sc20_stork_price(
    mock_stork,
    publish_time,
    feed_id=SC20_STORK_FEED_ID,
):
    payload = mock_stork.createPriceFeedUpdateData(
        feed_id,
        SC20_STORK_PRICE,
        publish_time,
    )
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)
    mock_stork.updateTemporalNumericValuesV1([payload], value=1)


def _add_sc20_stork_feed(
    stork_prices,
    mock_stork,
    asset,
    governance,
    stale_time,
    feed_id=SC20_STORK_FEED_ID,
):
    _set_sc20_stork_price(mock_stork, boa.env.timestamp, feed_id)
    assert stork_prices.addNewPriceFeed(
        asset,
        feed_id,
        stale_time,
        sender=governance.address,
    )
    advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
    _set_sc20_stork_price(mock_stork, boa.env.timestamp, feed_id)
    assert stork_prices.confirmNewPriceFeed(asset, sender=governance.address)


def test_stork_omitted_add_and_update_stale_time_inherit_global(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _set_sc20_stork_price(mock_stork, boa.env.timestamp)
        assert stork_prices.addNewPriceFeed(
            alpha_token,
            SC20_STORK_FEED_ID,
            sender=governance.address,
        )
        assert stork_prices.pendingUpdates(alpha_token).config.staleTime == 0

        advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
        _set_sc20_stork_price(mock_stork, boa.env.timestamp)
        assert stork_prices.confirmNewPriceFeed(
            alpha_token, sender=governance.address
        )
        assert stork_prices.feedConfig(alpha_token).staleTime == 0

        _set_sc20_stork_price(
            mock_stork,
            boa.env.timestamp,
            SC20_STORK_ALT_FEED_ID,
        )
        assert stork_prices.updatePriceFeed(
            alpha_token,
            SC20_STORK_ALT_FEED_ID,
            sender=governance.address,
        )
        assert stork_prices.pendingUpdates(alpha_token).config.staleTime == 0

        advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
        _set_sc20_stork_price(
            mock_stork,
            boa.env.timestamp,
            SC20_STORK_ALT_FEED_ID,
        )
        assert stork_prices.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        stored = stork_prices.feedConfig(alpha_token)
        assert stored.feedId == SC20_STORK_ALT_FEED_ID
        assert stored.staleTime == 0

        boa.env.time_travel(seconds=100)
        assert stork_prices.getPrice(alpha_token) == SC20_STORK_PRICE
        boa.env.time_travel(seconds=1)
        assert stork_prices.getPrice(alpha_token) == 0


@pytest.mark.parametrize(
    "feed_bound,global_bound,age,expected_valid",
    [
        (0, 100, 100, True),
        (0, 100, 101, False),
        (600, 100, 450, True),
        (MIN_LOCAL_STALE_TIME, 100, 375, False),
        (MIN_LOCAL_STALE_TIME, 0, MIN_LOCAL_STALE_TIME, True),
        (MIN_LOCAL_STALE_TIME, 0, MIN_LOCAL_STALE_TIME + 1, False),
        (MIN_LOCAL_STALE_TIME, MAX_FEED_STALE_TIME + 1, MIN_LOCAL_STALE_TIME, True),
        (MAX_FEED_STALE_TIME, 0, MAX_FEED_STALE_TIME, True),
        (MAX_FEED_STALE_TIME, 100, MAX_FEED_STALE_TIME + 1, False),
        (0, 0, 0, False),
        (0, MAX_FEED_STALE_TIME + 1, 0, False),
    ],
)
def test_stork_exact_override_and_global_inheritance_matrix(
    stork_prices,
    mock_stork,
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
        assert stork_prices.getPriceAndHasFeed(bravo_token) == (0, False)
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_stork_feed(
            stork_prices,
            mock_stork,
            alpha_token,
            governance,
            feed_bound,
        )
        setGeneralConfig(_priceStaleTime=global_bound)
        _set_sc20_stork_price(mock_stork, boa.env.timestamp)
        boa.env.time_travel(seconds=age)

        expected_price = SC20_STORK_PRICE if expected_valid else 0
        assert stork_prices.getPrice(alpha_token) == expected_price
        assert stork_prices.getPriceAndHasFeed(alpha_token) == (
            expected_price,
            True,
        )
        assert price_desk.getPrice(alpha_token) == expected_price


def test_stork_forwarded_global_requires_canonical_price_desk(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    price_desk,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_stork_feed(
            stork_prices, mock_stork, alpha_token, governance, 0
        )
        _set_sc20_stork_price(mock_stork, boa.env.timestamp)

        assert price_desk.getPrice(alpha_token) == SC20_STORK_PRICE
        assert stork_prices.getPrice(alpha_token) == SC20_STORK_PRICE

        assert stork_prices.getPrice(
            alpha_token, 100, price_desk.address
        ) == 0
        assert stork_prices.getPriceAndHasFeed(
            alpha_token, 100, price_desk.address
        ) == (0, True)
        assert stork_prices.getPrice(
            alpha_token, 100, ZERO_ADDRESS, sender=price_desk.address
        ) == 0
        assert stork_prices.getPriceAndHasFeed(
            alpha_token, 100, ZERO_ADDRESS, sender=price_desk.address
        ) == (0, True)

        assert stork_prices.getPrice(
            alpha_token,
            100,
            price_desk.address,
            sender=price_desk.address,
        ) == SC20_STORK_PRICE
        assert stork_prices.getPriceAndHasFeed(
            alpha_token,
            100,
            price_desk.address,
            sender=price_desk.address,
        ) == (SC20_STORK_PRICE, True)


def test_stork_invalid_stale_bounds_fail_closed_at_admission_and_runtime(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    setGeneralConfig,
):
    with boa.env.anchor():
        _set_sc20_stork_price(mock_stork, boa.env.timestamp)
        assert not stork_prices.isValidNewFeed(
            alpha_token, SC20_STORK_FEED_ID, MAX_FEED_STALE_TIME + 1
        )
        with boa.reverts("invalid feed"):
            stork_prices.addNewPriceFeed(
                alpha_token,
                SC20_STORK_FEED_ID,
                MAX_FEED_STALE_TIME + 1,
                sender=governance.address,
            )

        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_stork_feed(
            stork_prices, mock_stork, alpha_token, governance, 0
        )
        for invalid_global in (0, MAX_FEED_STALE_TIME + 1):
            setGeneralConfig(_priceStaleTime=invalid_global)
            assert stork_prices.getPrice(alpha_token) == 0
            assert stork_prices.getPriceAndHasFeed(alpha_token) == (0, True)

        assert not stork_prices.isValidStaleTimeUpdate(
            alpha_token, MAX_FEED_STALE_TIME + 1
        )
        with boa.reverts("invalid feed"):
            stork_prices.updateStaleTime(
                alpha_token,
                MAX_FEED_STALE_TIME + 1,
                sender=governance.address,
            )

        setGeneralConfig(_priceStaleTime=100)
        _set_sc20_stork_price(mock_stork, boa.env.timestamp)
        for invalid_local in (
            MIN_LOCAL_STALE_TIME - 1,
            MAX_FEED_STALE_TIME + 1,
        ):
            with boa.env.anchor():
                stork_prices.eval(
                    f"self.feedConfig[{alpha_token.address}].staleTime = "
                    f"{invalid_local}"
                )
                assert stork_prices.getPrice(alpha_token) == 0
                assert stork_prices.getPriceAndHasFeed(alpha_token) == (0, True)


def test_stork_stale_time_update_lifecycle_noop_cancel_and_liveness(
    stork_prices,
    mock_stork,
    alpha_token,
    bravo_token,
    governance,
    bob,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        assert not stork_prices.hasPriceFeed(bravo_token)
        assert not stork_prices.isValidStaleTimeUpdate(bravo_token, 600)
        with boa.reverts("invalid feed"):
            stork_prices.updateStaleTime(
                bravo_token, 600, sender=governance.address
            )
        assert stork_prices.pendingUpdates(bravo_token).actionId == 0

        _add_sc20_stork_feed(
            stork_prices,
            mock_stork,
            alpha_token,
            governance,
            MIN_LOCAL_STALE_TIME,
        )
        _set_sc20_stork_price(mock_stork, boa.env.timestamp)

        with boa.reverts("no perms"):
            stork_prices.updateStaleTime(alpha_token, 600, sender=bob)

        assert stork_prices.updateStaleTime(
            alpha_token, 600, sender=governance.address
        )
        pending = stork_prices.pendingUpdates(alpha_token)
        assert pending.actionId != 0
        assert pending.config.feedId == SC20_STORK_FEED_ID
        assert pending.config.staleTime == 600
        assert stork_prices.feedConfig(alpha_token).staleTime == MIN_LOCAL_STALE_TIME
        assert stork_prices.getPrice(alpha_token) == SC20_STORK_PRICE

        with boa.reverts("time lock not reached"):
            stork_prices.confirmPriceFeedUpdate(
                alpha_token, sender=governance.address
            )
        advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
        _set_sc20_stork_price(mock_stork, boa.env.timestamp)
        assert stork_prices.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert stork_prices.feedConfig(alpha_token).staleTime == 600

        assert not stork_prices.isValidStaleTimeUpdate(alpha_token, 600)
        with boa.reverts("invalid feed"):
            stork_prices.updateStaleTime(
                alpha_token, 600, sender=governance.address
            )

        assert stork_prices.updateStaleTime(
            alpha_token, 0, sender=governance.address
        )
        assert stork_prices.cancelPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert stork_prices.feedConfig(alpha_token).staleTime == 600
        assert stork_prices.pendingUpdates(alpha_token).actionId == 0

    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_stork_feed(
            stork_prices, mock_stork, alpha_token, governance, 600
        )
        _set_sc20_stork_price(mock_stork, boa.env.timestamp)
        assert stork_prices.updateStaleTime(
            alpha_token, MIN_LOCAL_STALE_TIME, sender=governance.address
        )
        advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
        boa.env.time_travel(seconds=MIN_LOCAL_STALE_TIME + 1)

        assert stork_prices.getPrice(alpha_token) == SC20_STORK_PRICE
        assert not stork_prices.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert stork_prices.feedConfig(alpha_token).staleTime == 600
        retry_pending = stork_prices.pendingUpdates(alpha_token)
        assert retry_pending.actionId != 0
        assert retry_pending.config.staleTime == MIN_LOCAL_STALE_TIME

        _set_sc20_stork_price(mock_stork, boa.env.timestamp)
        assert stork_prices.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert stork_prices.feedConfig(alpha_token).staleTime == MIN_LOCAL_STALE_TIME
        assert stork_prices.pendingUpdates(alpha_token).actionId == 0


def test_stork_stale_time_update_to_zero_confirms_global_inheritance(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_stork_feed(
            stork_prices, mock_stork, alpha_token, governance, 600
        )

        assert stork_prices.updateStaleTime(
            alpha_token, 0, sender=governance.address
        )
        pending = stork_prices.pendingUpdates(alpha_token)
        assert pending.actionId != 0
        assert pending.config.feedId == SC20_STORK_FEED_ID
        assert pending.config.staleTime == 0
        assert stork_prices.feedConfig(alpha_token).staleTime == 600

        advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
        _set_sc20_stork_price(mock_stork, boa.env.timestamp)
        assert stork_prices.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        stored = stork_prices.feedConfig(alpha_token)
        assert stored.feedId == SC20_STORK_FEED_ID
        assert stored.staleTime == 0
        assert stork_prices.pendingUpdates(alpha_token).actionId == 0

        boa.env.time_travel(seconds=100)
        assert stork_prices.getPrice(alpha_token) == SC20_STORK_PRICE
        assert stork_prices.getPriceAndHasFeed(alpha_token) == (
            SC20_STORK_PRICE,
            True,
        )
        boa.env.time_travel(seconds=1)
        assert stork_prices.getPrice(alpha_token) == 0
        assert stork_prices.getPriceAndHasFeed(alpha_token) == (0, True)


def test_stork_failed_feed_replacement_confirmation_auto_cancels(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
):
    with boa.env.anchor():
        _add_sc20_stork_feed(
            stork_prices,
            mock_stork,
            alpha_token,
            governance,
            600,
        )
        active = stork_prices.feedConfig(alpha_token)
        _set_sc20_stork_price(
            mock_stork,
            boa.env.timestamp,
            SC20_STORK_ALT_FEED_ID,
        )
        assert stork_prices.updatePriceFeed(
            alpha_token,
            SC20_STORK_ALT_FEED_ID,
            600,
            sender=governance.address,
        )
        action_id = stork_prices.pendingUpdates(alpha_token).actionId
        assert action_id != 0
        advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
        boa.env.time_travel(seconds=1)
        invalid_payload = mock_stork.createPriceFeedUpdateData(
            SC20_STORK_ALT_FEED_ID,
            -1,
            boa.env.timestamp,
        )
        boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)
        mock_stork.updateTemporalNumericValuesV1([invalid_payload], value=1)

        assert not stork_prices.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert stork_prices.pendingUpdates(alpha_token).actionId == 0
        assert not stork_prices.hasPendingAction(action_id)
        stored = stork_prices.feedConfig(alpha_token)
        assert stored.feedId == active.feedId
        assert stored.staleTime == active.staleTime


@pytest.mark.parametrize(
    "invalid_global", [0, MAX_FEED_STALE_TIME + 1]
)
@pytest.mark.parametrize(
    "pending_stale_time,should_confirm", [(0, False), (600, True)]
)
def test_stork_stale_time_confirmation_revalidates_inherited_policy(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    setGeneralConfig,
    invalid_global,
    pending_stale_time,
    should_confirm,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_stork_feed(
            stork_prices, mock_stork, alpha_token, governance, 300
        )
        assert stork_prices.updateStaleTime(
            alpha_token,
            pending_stale_time,
            sender=governance.address,
        )
        pending = stork_prices.pendingUpdates(alpha_token)
        assert pending.actionId != 0
        assert pending.config.feedId == SC20_STORK_FEED_ID
        assert pending.config.staleTime == pending_stale_time

        setGeneralConfig(_priceStaleTime=invalid_global)
        advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
        _set_sc20_stork_price(mock_stork, boa.env.timestamp)

        assert stork_prices.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        ) is should_confirm
        stored = stork_prices.feedConfig(alpha_token)
        assert stored.feedId == SC20_STORK_FEED_ID
        assert stored.staleTime == (600 if should_confirm else 300)
        pending_after = stork_prices.pendingUpdates(alpha_token)
        if should_confirm:
            assert pending_after.actionId == 0
            assert pending_after.config.feedId == bytes(32)
            assert pending_after.config.staleTime == 0
        else:
            assert pending_after.actionId == pending.actionId
            assert pending_after.config.feedId == SC20_STORK_FEED_ID
            assert pending_after.config.staleTime == 0
        assert stork_prices.getPrice(alpha_token) == SC20_STORK_PRICE
        assert stork_prices.getPriceAndHasFeed(alpha_token) == (
            SC20_STORK_PRICE,
            True,
        )


def test_stork_inherited_policy_fails_closed_without_mission_control(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    ripe_hq,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_stork_feed(
            stork_prices, mock_stork, alpha_token, governance, 0
        )
        _set_sc20_stork_price(mock_stork, boa.env.timestamp)
        assert stork_prices.getPrice(alpha_token) == SC20_STORK_PRICE

        assert ripe_hq.getAddr(5) != ZERO_ADDRESS
        ripe_hq.eval("registry.addrInfo[5].addr = empty(address)")
        assert ripe_hq.getAddr(5) == ZERO_ADDRESS
        assert stork_prices.getPrice(alpha_token) == 0
        assert stork_prices.getPriceAndHasFeed(alpha_token) == (0, True)


@pytest.mark.parametrize(
    "candidate",
    [0, 299, MIN_LOCAL_STALE_TIME, MAX_FEED_STALE_TIME, MAX_FEED_STALE_TIME + 1],
)
def test_stork_stale_time_preflight_matches_initiation(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    setGeneralConfig,
    candidate,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_stork_feed(
            stork_prices, mock_stork, alpha_token, governance, 600
        )
        _set_sc20_stork_price(mock_stork, boa.env.timestamp)
        expected = candidate in (0, MIN_LOCAL_STALE_TIME, MAX_FEED_STALE_TIME)
        assert stork_prices.isValidStaleTimeUpdate(
            alpha_token, candidate
        ) is expected
        with boa.env.anchor():
            if expected:
                assert stork_prices.updateStaleTime(
                    alpha_token, candidate, sender=governance.address
                )
            else:
                with boa.reverts("invalid feed"):
                    stork_prices.updateStaleTime(
                        alpha_token, candidate, sender=governance.address
                    )


def test_stork_inherited_zero_preflight_rejects_zero_global(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _add_sc20_stork_feed(
            stork_prices,
            mock_stork,
            alpha_token,
            governance,
            MIN_LOCAL_STALE_TIME,
        )
        setGeneralConfig(_priceStaleTime=0)
        assert not stork_prices.isValidStaleTimeUpdate(alpha_token, 0)
        with boa.reverts("invalid feed"):
            stork_prices.updateStaleTime(
                alpha_token, 0, sender=governance.address
            )


def _start_stork_pending_action(
    kind,
    stork_prices,
    mock_stork,
    asset,
    governance,
):
    _set_sc20_stork_price(mock_stork, boa.env.timestamp)
    _set_sc20_stork_price(
        mock_stork, boa.env.timestamp, SC20_STORK_ALT_FEED_ID
    )
    if kind == "add":
        assert stork_prices.addNewPriceFeed(
            asset,
            SC20_STORK_FEED_ID,
            MIN_LOCAL_STALE_TIME,
            sender=governance.address,
        )
        return

    _add_sc20_stork_feed(
        stork_prices,
        mock_stork,
        asset,
        governance,
        MIN_LOCAL_STALE_TIME,
    )
    if kind == "update":
        assert stork_prices.updatePriceFeed(
            asset,
            SC20_STORK_ALT_FEED_ID,
            MIN_LOCAL_STALE_TIME,
            sender=governance.address,
        )
    elif kind == "stale":
        assert stork_prices.updateStaleTime(
            asset, 600, sender=governance.address
        )
    else:
        assert kind == "disable"
        assert stork_prices.disablePriceFeed(
            asset, sender=governance.address
        )


def _stork_action_state(source, asset):
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


def _stork_wrong_action_selectors(pending_kind):
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
def test_stork_pending_action_blocks_initiators_and_wrong_selectors(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    setGeneralConfig,
    pending_kind,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _start_stork_pending_action(
            pending_kind,
            stork_prices,
            mock_stork,
            alpha_token,
            governance,
        )
        before = _stork_action_state(stork_prices, alpha_token)

        attempts = (
            lambda: stork_prices.addNewPriceFeed(
                alpha_token,
                SC20_STORK_FEED_ID,
                MIN_LOCAL_STALE_TIME,
                sender=governance.address,
            ),
            lambda: stork_prices.updatePriceFeed(
                alpha_token,
                SC20_STORK_ALT_FEED_ID,
                MIN_LOCAL_STALE_TIME,
                sender=governance.address,
            ),
            lambda: stork_prices.updateStaleTime(
                alpha_token, 300, sender=governance.address
            ),
            lambda: stork_prices.disablePriceFeed(
                alpha_token, sender=governance.address
            ),
        )
        for attempt in attempts:
            with boa.reverts("pending feed action"):
                attempt()
            assert _stork_action_state(stork_prices, alpha_token) == before

        for reason, selector in _stork_wrong_action_selectors(pending_kind):
            with boa.reverts(reason):
                getattr(stork_prices, selector)(
                    alpha_token, sender=governance.address
                )
            assert _stork_action_state(stork_prices, alpha_token) == before


@pytest.mark.parametrize("pending_kind", ["add", "update", "stale", "disable"])
def test_stork_expired_pending_action_requires_cleanup(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    setGeneralConfig,
    pending_kind,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=100)
        _start_stork_pending_action(
            pending_kind,
            stork_prices,
            mock_stork,
            alpha_token,
            governance,
        )
        advance_timelock_blocks(
            stork_prices.actionTimeLock() + stork_prices.expiration()
        )
        assert stork_prices.hasPendingPriceFeedUpdate(alpha_token)
        with boa.reverts("pending feed action"):
            stork_prices.updateStaleTime(
                alpha_token, 300, sender=governance.address
            )

        if pending_kind == "add":
            assert stork_prices.cancelNewPendingPriceFeed(
                alpha_token, sender=governance.address
            )
            assert stork_prices.addNewPriceFeed(
                alpha_token,
                SC20_STORK_FEED_ID,
                MIN_LOCAL_STALE_TIME,
                sender=governance.address,
            )
        elif pending_kind in ("update", "stale"):
            assert stork_prices.cancelPriceFeedUpdate(
                alpha_token, sender=governance.address
            )
            assert stork_prices.updateStaleTime(
                alpha_token, 600, sender=governance.address
            )
        else:
            assert stork_prices.cancelDisablePriceFeed(
                alpha_token, sender=governance.address
            )
            assert stork_prices.disablePriceFeed(
                alpha_token, sender=governance.address
            )


def test_stork_timestamp_conversion_matches_admission_and_runtime(
    stork_prices,
    mock_stork,
    alpha_token,
    bravo_token,
    governance,
):
    _add_sc20_stork_feed(
        stork_prices,
        mock_stork,
        alpha_token,
        governance,
        MIN_LOCAL_STALE_TIME,
    )
    current_second_ns = boa.env.timestamp * 1_000_000_000
    cases = (
        (0, False),
        (999_999_999, False),
        (current_second_ns, True),
        (current_second_ns + 999_999_999, True),
        (current_second_ns + 1_000_000_000, False),
    )

    for raw_timestamp_ns, expected_valid in cases:
        mock_stork.setMockTemporalNumericValue(
            SC20_STORK_FEED_ID,
            SC20_STORK_PRICE,
            raw_timestamp_ns,
        )
        expected_price = SC20_STORK_PRICE if expected_valid else 0
        assert stork_prices.getPrice(alpha_token) == expected_price
        assert stork_prices.getPriceAndHasFeed(alpha_token) == (
            expected_price,
            True,
        )
        assert stork_prices.isValidNewFeed(
            bravo_token, SC20_STORK_FEED_ID, MIN_LOCAL_STALE_TIME
        ) is expected_valid


def test_stork_zero_and_subsecond_timestamp_rejected_at_admission(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
):
    for raw_timestamp_ns in (0, 1, 999_999_999):
        mock_stork.setMockTemporalNumericValue(
            SC20_STORK_ALT_FEED_ID,
            SC20_STORK_PRICE,
            raw_timestamp_ns,
        )
        assert not stork_prices.isValidNewFeed(
            alpha_token, SC20_STORK_ALT_FEED_ID, MIN_LOCAL_STALE_TIME
        )
        with boa.reverts("invalid feed"):
            stork_prices.addNewPriceFeed(
                alpha_token,
                SC20_STORK_ALT_FEED_ID,
                MIN_LOCAL_STALE_TIME,
                sender=governance.address,
            )


def test_stork_future_whole_second_is_fail_soft_and_recovers(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
):
    _add_sc20_stork_feed(
        stork_prices,
        mock_stork,
        alpha_token,
        governance,
        MIN_LOCAL_STALE_TIME,
    )
    future_time = boa.env.timestamp + 100
    _set_sc20_stork_price(mock_stork, future_time)

    assert stork_prices.getPrice(alpha_token) == 0
    assert stork_prices.getPriceAndHasFeed(alpha_token) == (0, True)

    boa.env.time_travel(seconds=100)
    assert stork_prices.getPrice(alpha_token) == SC20_STORK_PRICE


def test_stork_current_timestamp_is_valid(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
):
    _add_sc20_stork_feed(
        stork_prices,
        mock_stork,
        alpha_token,
        governance,
        MIN_LOCAL_STALE_TIME,
    )
    _set_sc20_stork_price(mock_stork, boa.env.timestamp)
    assert stork_prices.getPrice(alpha_token) == SC20_STORK_PRICE


@pytest.mark.parametrize("explicit_zero", [False, True])
def test_stork_feed_rotation_zero_preserves_active_stale_policy(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    explicit_zero,
):
    with boa.env.anchor():
        _add_sc20_stork_feed(
            stork_prices,
            mock_stork,
            alpha_token,
            governance,
            3_600,
        )
        _set_sc20_stork_price(
            mock_stork,
            boa.env.timestamp,
            SC20_STORK_ALT_FEED_ID,
        )

        assert stork_prices.isValidUpdateFeed(
            alpha_token, SC20_STORK_ALT_FEED_ID, 0
        )
        if explicit_zero:
            assert stork_prices.updatePriceFeed(
                alpha_token,
                SC20_STORK_ALT_FEED_ID,
                0,
                sender=governance.address,
            )
        else:
            assert stork_prices.updatePriceFeed(
                alpha_token,
                SC20_STORK_ALT_FEED_ID,
                sender=governance.address,
            )
        pending_log = filter_logs(
            stork_prices, "StorkFeedUpdatePending"
        )[0]
        pending = stork_prices.pendingUpdates(alpha_token)
        assert pending.config.staleTime == 3_600
        assert pending_log.staleTime == 3_600

        advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
        _set_sc20_stork_price(
            mock_stork,
            boa.env.timestamp,
            SC20_STORK_ALT_FEED_ID,
        )
        assert stork_prices.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        updated_log = filter_logs(stork_prices, "StorkFeedUpdated")[0]
        stored = stork_prices.feedConfig(alpha_token)
        assert stored.feedId == SC20_STORK_ALT_FEED_ID
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
def test_stork_local_stale_bounds_cover_feed_lifecycles(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    candidate,
    is_valid,
):
    with boa.env.anchor():
        _set_sc20_stork_price(mock_stork, boa.env.timestamp)
        assert stork_prices.isValidNewFeed(
            alpha_token, SC20_STORK_FEED_ID, candidate
        ) is is_valid
        if is_valid:
            assert stork_prices.addNewPriceFeed(
                alpha_token,
                SC20_STORK_FEED_ID,
                candidate,
                sender=governance.address,
            )
            assert (
                stork_prices.pendingUpdates(alpha_token).config.staleTime
                == candidate
            )
            advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
            _set_sc20_stork_price(mock_stork, boa.env.timestamp)
            assert stork_prices.confirmNewPriceFeed(
                alpha_token, sender=governance.address
            )
        else:
            with boa.reverts("invalid feed"):
                stork_prices.addNewPriceFeed(
                    alpha_token,
                    SC20_STORK_FEED_ID,
                    candidate,
                    sender=governance.address,
                )

    with boa.env.anchor():
        _add_sc20_stork_feed(
            stork_prices,
            mock_stork,
            alpha_token,
            governance,
            600,
        )
        _set_sc20_stork_price(
            mock_stork,
            boa.env.timestamp,
            SC20_STORK_ALT_FEED_ID,
        )
        assert stork_prices.isValidUpdateFeed(
            alpha_token, SC20_STORK_ALT_FEED_ID, candidate
        ) is is_valid
        if is_valid:
            assert stork_prices.updatePriceFeed(
                alpha_token,
                SC20_STORK_ALT_FEED_ID,
                candidate,
                sender=governance.address,
            )
            advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
            _set_sc20_stork_price(
                mock_stork,
                boa.env.timestamp,
                SC20_STORK_ALT_FEED_ID,
            )
            assert stork_prices.confirmPriceFeedUpdate(
                alpha_token, sender=governance.address
            )
            assert stork_prices.feedConfig(alpha_token).staleTime == candidate
        else:
            with boa.reverts("invalid feed"):
                stork_prices.updatePriceFeed(
                    alpha_token,
                    SC20_STORK_ALT_FEED_ID,
                    candidate,
                    sender=governance.address,
                )

    with boa.env.anchor():
        _add_sc20_stork_feed(
            stork_prices,
            mock_stork,
            alpha_token,
            governance,
            600,
        )
        assert stork_prices.isValidStaleTimeUpdate(
            alpha_token, candidate
        ) is is_valid
        if is_valid:
            assert stork_prices.updateStaleTime(
                alpha_token, candidate, sender=governance.address
            )
            advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
            _set_sc20_stork_price(mock_stork, boa.env.timestamp)
            assert stork_prices.confirmPriceFeedUpdate(
                alpha_token, sender=governance.address
            )
            assert stork_prices.feedConfig(alpha_token).staleTime == candidate
        else:
            with boa.reverts("invalid feed"):
                stork_prices.updateStaleTime(
                    alpha_token, candidate, sender=governance.address
                )


def test_stork_paused_source_keeps_pricing_but_freezes_pending_actions(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    switchboard_alpha,
):
    with boa.env.anchor():
        _add_sc20_stork_feed(
            stork_prices,
            mock_stork,
            alpha_token,
            governance,
            600,
        )
        assert stork_prices.updateStaleTime(
            alpha_token,
            MIN_LOCAL_STALE_TIME,
            sender=governance.address,
        )
        advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
        _set_sc20_stork_price(mock_stork, boa.env.timestamp)

        stork_prices.pause(True, sender=switchboard_alpha.address)
        assert stork_prices.getPrice(alpha_token) == SC20_STORK_PRICE
        with boa.reverts("contract paused"):
            stork_prices.updateStaleTime(
                alpha_token, 1_200, sender=governance.address
            )
        with boa.reverts("contract paused"):
            stork_prices.confirmPriceFeedUpdate(
                alpha_token, sender=governance.address
            )
        with boa.reverts("contract paused"):
            stork_prices.cancelPriceFeedUpdate(
                alpha_token, sender=governance.address
            )

        stork_prices.pause(False, sender=switchboard_alpha.address)
        assert stork_prices.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert stork_prices.updateStaleTime(
            alpha_token, 600, sender=governance.address
        )
        stork_prices.pause(True, sender=switchboard_alpha.address)
        with boa.reverts("contract paused"):
            stork_prices.cancelPriceFeedUpdate(
                alpha_token, sender=governance.address
            )
        stork_prices.pause(False, sender=switchboard_alpha.address)
        assert stork_prices.cancelPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert stork_prices.pendingUpdates(alpha_token).actionId == 0


def test_stork_failed_stale_confirmation_can_cancel_after_expiry(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
):
    with boa.env.anchor():
        _add_sc20_stork_feed(
            stork_prices,
            mock_stork,
            alpha_token,
            governance,
            600,
        )
        assert stork_prices.updateStaleTime(
            alpha_token,
            MIN_LOCAL_STALE_TIME,
            sender=governance.address,
        )
        advance_timelock_blocks(stork_prices.actionTimeLock() + 1)
        _set_sc20_stork_price(
            mock_stork,
            boa.env.timestamp - MIN_LOCAL_STALE_TIME - 1,
        )
        assert not stork_prices.confirmPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        action_id = stork_prices.pendingUpdates(alpha_token).actionId
        assert action_id != 0

        advance_timelock_blocks(stork_prices.expiration())
        assert stork_prices.pendingUpdates(alpha_token).actionId == action_id
        assert stork_prices.cancelPriceFeedUpdate(
            alpha_token, sender=governance.address
        )
        assert stork_prices.pendingUpdates(alpha_token).actionId == 0
