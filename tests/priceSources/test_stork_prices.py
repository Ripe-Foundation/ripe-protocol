import boa
import pytest

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS
from conf_utils import filter_logs
from config.BluePrint import CORE_TOKENS

MONTH_IN_SECONDS = 30 * 24 * 60 * 60


@pytest.fixture(scope="module")
def addStorkFeed(stork_prices, governance):
    def addStorkFeed(_asset, _feed_id):
        if stork_prices.hasPriceFeed(_asset):
            return
        assert stork_prices.addNewPriceFeed(_asset, _feed_id, sender=governance.address)
        boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)
        assert stork_prices.confirmNewPriceFeed(_asset, sender=governance.address)
    yield addStorkFeed


###################
# Unique to Stork #
###################


def test_stork_local_update_prices(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    addStorkFeed,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    addStorkFeed(alpha_token, data_feed_id)
    assert stork_prices.getPrice(alpha_token) != 0

    # get payload
    publish_time = boa.env.evm.patch.timestamp + 1
    payload = mock_stork.createPriceFeedUpdateData(
        data_feed_id,
        998888888000000000,
        publish_time,
    )
    exp_fee = len(payload)

    # no balance
    assert not stork_prices.updateStorkPrice(payload, sender=governance.address)

    # add eth balance
    assert boa.env.get_balance(stork_prices.address) == 0
    boa.env.set_balance(stork_prices.address, EIGHTEEN_DECIMALS)
    assert boa.env.get_balance(stork_prices.address) > exp_fee
    pre_stork_prices_bal = boa.env.get_balance(stork_prices.address)

    # success
    assert stork_prices.updateStorkPrice(payload, sender=governance.address)

    log = filter_logs(stork_prices, 'StorkPriceUpdated')[0]
    assert log.payload == payload
    assert log.feeAmount == exp_fee
    assert log.caller == governance.address

    assert boa.env.get_balance(stork_prices.address) == pre_stork_prices_bal - exp_fee
    assert boa.env.get_balance(mock_stork.address) == exp_fee

    # check mock stork
    price_data = mock_stork.priceFeeds(data_feed_id)
    assert price_data.quantizedValue == 998888888000000000
    assert price_data.timestampNs == publish_time * 1_000_000_000

    assert int(1 * EIGHTEEN_DECIMALS) > stork_prices.getPrice(alpha_token) > int(0.97 * EIGHTEEN_DECIMALS)


def test_stork_update_many_prices(
    stork_prices,
    mock_stork,
    alpha_token,
    bravo_token,
    governance,
    addStorkFeed,
):
    # Add feeds for multiple assets
    data_feed_id_1 = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    data_feed_id_2 = bytes.fromhex("8416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290d")
    
    # Setup the second feed by creating a payload and updating it in MockStork
    payload_2 = mock_stork.createPriceFeedUpdateData(data_feed_id_2, 970000000000000000, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_stork.updateTemporalNumericValuesV1(payload_2, value=len(payload_2))
    
    addStorkFeed(alpha_token, data_feed_id_1)
    addStorkFeed(bravo_token, data_feed_id_2)

    # Create payloads for both feeds
    publish_time = boa.env.evm.patch.timestamp + 1
    payload1 = mock_stork.createPriceFeedUpdateData(data_feed_id_1, 998000000000000000, publish_time)
    payload2 = mock_stork.createPriceFeedUpdateData(data_feed_id_2, 970000000000000000, publish_time)
    
    # Add ETH balance
    total_fee = len(payload1) + len(payload2)
    boa.env.set_balance(stork_prices.address, total_fee + EIGHTEEN_DECIMALS)
    pre_balance = boa.env.get_balance(stork_prices.address)

    # Test successful batch update
    num_updated = stork_prices.updateManyStorkPrices([payload1, payload2], sender=governance.address)
    assert num_updated == 2

    # Check balances
    assert boa.env.get_balance(stork_prices.address) == pre_balance - total_fee

    # Test with insufficient balance (should stop after first update fails)
    boa.env.set_balance(stork_prices.address, len(payload1) - 1)  # Not enough for first payload
    num_updated = stork_prices.updateManyStorkPrices([payload1, payload2], sender=governance.address)
    assert num_updated == 0


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
    governance,
    addStorkFeed,
    quantized_value,
    expected_price,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    addStorkFeed(alpha_token, data_feed_id)

    # get payload
    publish_time = boa.env.evm.patch.timestamp + 1
    payload = mock_stork.createPriceFeedUpdateData(
        data_feed_id,
        quantized_value,
        publish_time,
    )

    # add eth balance
    if boa.env.get_balance(stork_prices.address) < EIGHTEEN_DECIMALS:
        boa.env.set_balance(stork_prices.address, 2 * EIGHTEEN_DECIMALS)

    # update price
    assert stork_prices.updateStorkPrice(payload, sender=governance.address)

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
    governance,
    addStorkFeed,
):
    boa.env.evm.patch.timestamp += MONTH_IN_SECONDS

    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    addStorkFeed(alpha_token, data_feed_id)
    assert stork_prices.getPrice(alpha_token) != 0

    # get payload with stale timestamp
    publish_time = boa.env.evm.patch.timestamp - 3601  # 1 hour and 1 second ago, > stale time (3600s)
    payload = mock_stork.createPriceFeedUpdateData(
        data_feed_id,
        998000000000000000,
        publish_time,
    )

    # add eth balance
    boa.env.set_balance(stork_prices.address, EIGHTEEN_DECIMALS)

    # success update price
    assert stork_prices.updateStorkPrice(payload, sender=governance.address)

    # price should be 0 due to staleness
    assert stork_prices.getPrice(alpha_token, 3600) == 0


def test_stork_is_valid_feed(
    stork_prices,
    alpha_token,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    invalid_feed_id = bytes.fromhex("f" * 64)

    # valid feed (exists in MockStork)
    assert stork_prices.isValidNewFeed(alpha_token, data_feed_id)

    # invalid feed id (doesn't exist in MockStork)
    assert not stork_prices.isValidNewFeed(alpha_token, invalid_feed_id)

    # invalid asset
    assert not stork_prices.isValidNewFeed(ZERO_ADDRESS, data_feed_id)


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

    # Test adding invalid feed (non-existent feed)
    invalid_feed_id = bytes.fromhex("f" * 64)
    with boa.reverts("invalid feed"):
        stork_prices.addNewPriceFeed(alpha_token, invalid_feed_id, sender=governance.address)

    # Test adding feed with zero address asset
    with boa.reverts("invalid feed"):
        stork_prices.addNewPriceFeed(ZERO_ADDRESS, data_feed_id, sender=governance.address)

    # Test successful feed addition
    assert stork_prices.addNewPriceFeed(alpha_token, data_feed_id, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "NewStorkFeedPending")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id

    # Verify pending state
    assert stork_prices.hasPendingPriceFeedUpdate(alpha_token)
    pending = stork_prices.pendingUpdates(alpha_token)
    assert pending.feedId == data_feed_id

    # Test confirming before time lock
    with boa.reverts("time lock not reached"):
        stork_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Travel past time lock
    boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)

    # Test confirming
    assert stork_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "NewStorkFeedAdded")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id

    # Verify feed is active
    assert stork_prices.hasPriceFeed(alpha_token)
    assert stork_prices.feedConfig(alpha_token) == data_feed_id
    assert stork_prices.getPrice(alpha_token) != 0
    assert not stork_prices.hasPendingPriceFeedUpdate(alpha_token)

    # Test canceling non-existent feed
    with boa.reverts("cannot cancel action"):
        stork_prices.cancelNewPendingPriceFeed(alpha_token, sender=governance.address)

    # Test adding feed for existing asset
    with boa.reverts("invalid feed"):
        stork_prices.addNewPriceFeed(alpha_token, data_feed_id, sender=governance.address)


def test_stork_add_price_feed_cancel(
    stork_prices,
    alpha_token,
    governance,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")

    # Add feed
    assert stork_prices.addNewPriceFeed(alpha_token, data_feed_id, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "NewStorkFeedPending")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id

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
    mock_stork.updateTemporalNumericValuesV1(payload, value=len(payload))
    
    assert stork_prices.addNewPriceFeed(alpha_token, invalid_feed_id, sender=governance.address)
    
    # Travel past time lock
    boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)

    # Now update the feed with zero timestampNs to make validation fail
    # In Stork, validation checks timestampNs != 0, so we set it to 0
    invalid_payload = mock_stork.createPriceFeedUpdateData(invalid_feed_id, 0, 0)  # timestamp 0
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_stork.updateTemporalNumericValuesV1(invalid_payload, value=len(invalid_payload))

    # Confirm should fail and auto-cancel due to invalid timestamp (0)
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
    mock_stork.updateTemporalNumericValuesV1(payload_2, value=len(payload_2))

    # Add initial feed
    addStorkFeed(alpha_token, data_feed_id_1)

    # Test unauthorized access
    with boa.reverts("no perms"):
        stork_prices.updatePriceFeed(alpha_token, data_feed_id_2, sender=bob)

    # Test updating with same feed
    with boa.reverts("invalid feed"):
        stork_prices.updatePriceFeed(alpha_token, data_feed_id_1, sender=governance.address)

    # Test updating non-existent asset
    with boa.reverts("invalid feed"):
        stork_prices.updatePriceFeed(ZERO_ADDRESS, data_feed_id_2, sender=governance.address)

    # Test updating with invalid feed
    invalid_feed_id = bytes.fromhex("f" * 64)
    with boa.reverts("invalid feed"):
        stork_prices.updatePriceFeed(alpha_token, invalid_feed_id, sender=governance.address)

    # Test successful update
    assert stork_prices.updatePriceFeed(alpha_token, data_feed_id_2, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "StorkFeedUpdatePending")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id_2
    assert log.oldFeedId == data_feed_id_1

    # Test confirming before time lock
    with boa.reverts("time lock not reached"):
        stork_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    # Travel past time lock
    boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)

    # Test confirming
    assert stork_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "StorkFeedUpdated")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id_2
    assert log.oldFeedId == data_feed_id_1

    # Verify feed is updated
    assert stork_prices.hasPriceFeed(alpha_token)
    assert stork_prices.feedConfig(alpha_token) == data_feed_id_2
    assert stork_prices.getPrice(alpha_token) != 0

    # Test canceling non-existent update
    with boa.reverts("cannot cancel action"):
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
    mock_stork.updateTemporalNumericValuesV1(payload_2, value=len(payload_2))

    # Add initial feed
    addStorkFeed(alpha_token, data_feed_id_1)

    # Start update
    assert stork_prices.updatePriceFeed(alpha_token, data_feed_id_2, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "StorkFeedUpdatePending")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id_2
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
    assert stork_prices.feedConfig(alpha_token) == data_feed_id_1
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
    mock_stork.updateTemporalNumericValuesV1(payload_2, value=len(payload_2))
    invalid_feed_id = bytes.fromhex("f" * 64)

    # Add initial feed
    addStorkFeed(alpha_token, data_feed_id_1)

    # Test isValidUpdateFeed function
    assert stork_prices.isValidUpdateFeed(alpha_token, data_feed_id_2)  # Valid update
    assert not stork_prices.isValidUpdateFeed(alpha_token, data_feed_id_1)  # Same feed
    assert not stork_prices.isValidUpdateFeed(bravo_token, data_feed_id_2)  # No existing feed
    assert not stork_prices.isValidUpdateFeed(alpha_token, invalid_feed_id)  # Invalid feed


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
    boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)

    # Test confirming
    assert stork_prices.confirmDisablePriceFeed(alpha_token, sender=governance.address)
    
    # Verify event
    log = filter_logs(stork_prices, "StorkFeedDisabled")[0]
    assert log.asset == alpha_token.address
    assert log.feedId == data_feed_id

    # Verify feed is disabled
    assert not stork_prices.hasPriceFeed(alpha_token)
    assert stork_prices.getPrice(alpha_token) == 0
    assert stork_prices.feedConfig(alpha_token) == bytes(32)

    # Test canceling non-existent disable
    with boa.reverts("cannot cancel action"):
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
    assert stork_prices.feedConfig(alpha_token) == data_feed_id

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
    governance,
    addStorkFeed,
):
    data_feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    addStorkFeed(alpha_token, data_feed_id)

    # Test price exactly at stale time boundary
    publish_time = boa.env.evm.patch.timestamp
    payload = mock_stork.createPriceFeedUpdateData(data_feed_id, 998000000000000000, publish_time)
    boa.env.set_balance(stork_prices.address, EIGHTEEN_DECIMALS)
    assert stork_prices.updateStorkPrice(payload, sender=governance.address)

    # Test price just at stale boundary (should still be valid)
    assert stork_prices.getPrice(alpha_token, 0) != 0
    boa.env.time_travel(seconds=1)
    assert stork_prices.getPrice(alpha_token, 1) != 0

    # Test price just over stale boundary
    boa.env.time_travel(seconds=1)
    assert stork_prices.getPrice(alpha_token, 1) == 0

    # Test with maximum uint256 stale time
    payload = mock_stork.createPriceFeedUpdateData(data_feed_id, 998000000000000000, boa.env.evm.patch.timestamp)
    assert stork_prices.updateStorkPrice(payload, sender=governance.address)
    assert stork_prices.getPrice(alpha_token, 2**256 - 1) != 0

    # Test with zero stale time (never stale)
    boa.env.time_travel(seconds=100000)
    assert stork_prices.getPrice(alpha_token, 0) != 0


def test_stork_time_lock_edge_cases(
    stork_prices,
    mock_stork,
    alpha_token,
    bravo_token,
    governance,
):
    data_feed_id_1 = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    data_feed_id_2 = bytes.fromhex("8416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290d")
    
    # Setup the second feed in MockStork
    payload_2 = mock_stork.createPriceFeedUpdateData(data_feed_id_2, 970000000000000000, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_stork.updateTemporalNumericValuesV1(payload_2, value=len(payload_2))

    # Test confirming just before time lock boundary
    assert stork_prices.addNewPriceFeed(alpha_token, data_feed_id_1, sender=governance.address)
    boa.env.time_travel(blocks=stork_prices.actionTimeLock() - 1)
    with boa.reverts("time lock not reached"):
        stork_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test confirming at time lock boundary
    boa.env.time_travel(blocks=1)
    assert stork_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Test multiple time lock actions in sequence
    assert stork_prices.updatePriceFeed(alpha_token, data_feed_id_2, sender=governance.address)
    boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)
    assert stork_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
    
    assert stork_prices.disablePriceFeed(alpha_token, sender=governance.address)
    boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)
    assert stork_prices.confirmDisablePriceFeed(alpha_token, sender=governance.address)

    # Test with different time lock values
    stork_prices.setActionTimeLock(302400, sender=governance.address)  # 7 days in blocks
    assert stork_prices.addNewPriceFeed(bravo_token, data_feed_id_1, sender=governance.address)
    boa.env.time_travel(blocks=302400)
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
    mock_stork.updateTemporalNumericValuesV1(payload_2, value=len(payload_2))

    # Test multiple governance actions in sequence
    assert stork_prices.addNewPriceFeed(alpha_token, data_feed_id_1, sender=governance.address)
    assert stork_prices.cancelNewPendingPriceFeed(alpha_token, sender=governance.address)
    assert stork_prices.addNewPriceFeed(alpha_token, data_feed_id_1, sender=governance.address)
    boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)
    assert stork_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)
    assert stork_prices.updatePriceFeed(alpha_token, data_feed_id_2, sender=governance.address)
    boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)
    assert stork_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    # Test governance actions during pause (using MissionControl address)
    stork_prices.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        stork_prices.addNewPriceFeed(alpha_token, data_feed_id_1, sender=governance.address)
    with boa.reverts("contract paused"):
        stork_prices.updatePriceFeed(alpha_token, data_feed_id_1, sender=governance.address)
    with boa.reverts("contract paused"):
        stork_prices.disablePriceFeed(alpha_token, sender=governance.address)

    # Test governance actions after unpause
    stork_prices.pause(False, sender=switchboard_alpha.address)
    # First disable the existing feed
    assert stork_prices.disablePriceFeed(alpha_token, sender=governance.address)
    boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)
    assert stork_prices.confirmDisablePriceFeed(alpha_token, sender=governance.address)
    # Now we can add a new feed
    assert stork_prices.addNewPriceFeed(alpha_token, data_feed_id_1, sender=governance.address)


def test_stork_feed_validation_edge_cases(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
):
    bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")

    # Test feed validation with zero timestampNs (invalid)
    zero_timestamp_feed_id = bytes.fromhex("9416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290e")
    
    # Create a feed with zero timestamp (invalid)
    zero_payload = mock_stork.createPriceFeedUpdateData(zero_timestamp_feed_id, 998000000000000000, 0)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_stork.updateTemporalNumericValuesV1(zero_payload, value=len(zero_payload))

    # Should fail validation due to zero timestampNs
    with boa.reverts("invalid feed"):
        stork_prices.addNewPriceFeed(alpha_token, zero_timestamp_feed_id, sender=governance.address)

    # Fix the timestamp and it should work
    fresh_payload = mock_stork.createPriceFeedUpdateData(zero_timestamp_feed_id, 998000000000000000, boa.env.evm.patch.timestamp)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)  # Add ETH for fee payment
    mock_stork.updateTemporalNumericValuesV1(fresh_payload, value=len(fresh_payload))
    assert stork_prices.addNewPriceFeed(alpha_token, zero_timestamp_feed_id, sender=governance.address)


@pytest.base
def test_set_stork_feed_cbtc(
    stork_prices,
    fork,
    addStorkFeed,
):
    cbtc = CORE_TOKENS[fork]["CBBTC"]
    data_feed_id = bytes.fromhex("7404e3d104ea7841c3d9e6fd20adfe99b4ad586bc08d8f3bd3afef894cf184de")
    addStorkFeed(cbtc, data_feed_id)

    assert stork_prices.feedConfig(cbtc) == data_feed_id
    assert 99_000 * EIGHTEEN_DECIMALS > stork_prices.getPrice(cbtc) > 97_000 * EIGHTEEN_DECIMALS