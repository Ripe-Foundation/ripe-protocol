import pytest
import boa

from constants import BLUE_CHIP_PROTOCOL_MORPHO, EIGHTEEN_DECIMALS, ZERO_ADDRESS
from conf_utils import filter_logs


#####################
# Local Integration #
#####################


def test_add_local_fake_morpho_asset(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    price_desk,
    teller,
):
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    assert blue_chip_prices.isValidNewFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10)

    # add new price feed - using positional args with custom values
    assert blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    log = filter_logs(blue_chip_prices, "NewPriceConfigAdded")[0]

    # verify config
    config = blue_chip_prices.priceConfigs(alpha_token_vault)
    assert config.protocol == BLUE_CHIP_PROTOCOL_MORPHO
    assert config.underlyingAsset == alpha_token.address
    assert config.underlyingDecimals == 18
    assert config.vaultTokenDecimals == 18
    assert config.minSnapshotDelay == 0
    assert config.maxNumSnapshots == 10
    assert config.maxUpsideDeviation == 0
    assert config.staleTime == 10
    assert config.nextIndex == 1 # snapshot taken during registration

    # verify event
    assert log.asset == alpha_token_vault.address
    assert log.protocol == BLUE_CHIP_PROTOCOL_MORPHO
    assert log.underlyingAsset == alpha_token.address
    assert log.maxNumSnapshots == 10
    assert log.maxUpsideDeviation == 0
    assert log.staleTime == 10

    alpha_token_price = price_desk.getPrice(alpha_token)
    assert alpha_token_price == 1 * EIGHTEEN_DECIMALS  # Should be exactly what we set

    # test price
    alpha_vault_price = blue_chip_prices.getPrice(alpha_token_vault)
    assert alpha_vault_price == alpha_token_price

    # deposit
    alpha_token.approve(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault.deposit(100 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)

    # still same price
    alpha_vault_price = blue_chip_prices.getPrice(alpha_token_vault)
    assert alpha_vault_price == alpha_token_price
    first_snapshot = blue_chip_prices.getLatestSnapshot(alpha_token_vault)

    # have whale transfer double the amount
    alpha_token.transfer(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # still same price, no new snapshot
    alpha_vault_price = blue_chip_prices.getPrice(alpha_token_vault)
    assert alpha_vault_price == alpha_token_price

    # but latest snapshot has new price per share
    latest_snapshot = blue_chip_prices.getLatestSnapshot(alpha_token_vault)
    assert latest_snapshot.pricePerShare == first_snapshot.pricePerShare * 2

    # advance time to allow new snapshot
    boa.env.time_travel(seconds=1)

    # add new snapshot
    blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)

    # new price
    assert blue_chip_prices.getPrice(alpha_token_vault) == alpha_token_price * 2


######################
# Add New Price Feed #
######################


def test_add_new_price_feed_success(
    blue_chip_prices,
    governance,
    bravo_token_vault,
    mock_price_source,
    bravo_token,
):
    """Test successful addition of new price feed"""
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    
    # Should be valid
    assert blue_chip_prices.isValidNewFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 20)
    
    # Add new price feed
    assert blue_chip_prices.addNewPriceFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 20, sender=governance.address)
    
    # Check event immediately after transaction
    pending_log = filter_logs(blue_chip_prices, "NewPriceConfigPending")[0]
    assert pending_log.asset == bravo_token_vault.address
    assert pending_log.protocol == BLUE_CHIP_PROTOCOL_MORPHO
    assert pending_log.underlyingAsset == bravo_token.address
    assert pending_log.maxNumSnapshots == 5
    assert pending_log.maxUpsideDeviation == 0
    assert pending_log.staleTime == 20
    
    # Check pending state
    assert blue_chip_prices.hasPendingPriceFeedUpdate(bravo_token_vault)


def test_add_new_price_feed_invalid_params(
    blue_chip_prices,
    governance,
    charlie_token_vault,
    mock_price_source,
    charlie_token,
):
    """Test adding new price feed with invalid parameters"""
    mock_price_source.setPrice(charlie_token, 3 * EIGHTEEN_DECIMALS)
    
    # Invalid: maxNumSnapshots = 0
    assert not blue_chip_prices.isValidNewFeed(charlie_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 0, 0, 10)
    with boa.reverts("invalid feed"):
        blue_chip_prices.addNewPriceFeed(charlie_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 0, 0, 10, sender=governance.address)
    
    # Invalid: maxNumSnapshots > 25
    assert not blue_chip_prices.isValidNewFeed(charlie_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 26, 0, 10)
    with boa.reverts("invalid feed"):
        blue_chip_prices.addNewPriceFeed(charlie_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 26, 0, 10, sender=governance.address)


def test_add_new_price_feed_no_governance(
    blue_chip_prices,
    alice,
    bravo_token_vault,
    mock_price_source,
    bravo_token,
):
    """Test adding new price feed without governance permissions"""
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    
    with boa.reverts("no perms"):
        blue_chip_prices.addNewPriceFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 20, sender=alice)


def test_add_new_price_feed_already_exists(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
):
    """Test adding price feed for asset that already has one"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Add first feed
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Try to add again - should be invalid
    assert not blue_chip_prices.isValidNewFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 20)
    with boa.reverts("invalid feed"):
        blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 20, sender=governance.address)


def test_confirm_new_price_feed_before_timelock(
    blue_chip_prices,
    governance,
    bravo_token_vault,
    mock_price_source,
    bravo_token,
):
    """Test confirming new price feed before timelock expires"""
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    
    # Add new price feed
    blue_chip_prices.addNewPriceFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 20, sender=governance.address)
    
    # Try to confirm immediately - should fail
    with boa.reverts("time lock not reached"):
        blue_chip_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)


def test_confirm_new_price_feed_success(
    blue_chip_prices,
    governance,
    bravo_token_vault,
    mock_price_source,
    bravo_token,
):
    """Test successful confirmation of new price feed"""
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    
    # Add new price feed
    blue_chip_prices.addNewPriceFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 20, sender=governance.address)
    
    # Time travel and confirm
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)
    
    # Check event immediately after transaction
    added_log = filter_logs(blue_chip_prices, "NewPriceConfigAdded")[0]
    assert added_log.asset == bravo_token_vault.address
    assert added_log.protocol == BLUE_CHIP_PROTOCOL_MORPHO
    assert added_log.underlyingAsset == bravo_token.address
    
    # Check no longer pending
    assert not blue_chip_prices.hasPendingPriceFeedUpdate(bravo_token_vault)
    
    # Check has feed now
    assert blue_chip_prices.hasPriceFeed(bravo_token_vault)
    
    # Check config
    config = blue_chip_prices.priceConfigs(bravo_token_vault)
    assert config.protocol == BLUE_CHIP_PROTOCOL_MORPHO
    assert config.underlyingAsset == bravo_token.address
    assert config.minSnapshotDelay == 0
    assert config.maxNumSnapshots == 5
    assert config.staleTime == 20
    assert config.nextIndex == 1  # snapshot taken during registration


def test_cancel_new_pending_price_feed(
    blue_chip_prices,
    governance,
    bravo_token_vault,
    mock_price_source,
    bravo_token,
):
    """Test canceling pending new price feed"""
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    
    # Add new price feed
    blue_chip_prices.addNewPriceFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 20, sender=governance.address)
    assert blue_chip_prices.hasPendingPriceFeedUpdate(bravo_token_vault)
    
    # Cancel
    assert blue_chip_prices.cancelNewPendingPriceFeed(bravo_token_vault, sender=governance.address)
    
    # Check event immediately after transaction
    cancelled_log = filter_logs(blue_chip_prices, "NewPriceConfigCancelled")[0]
    assert cancelled_log.asset == bravo_token_vault.address
    assert cancelled_log.protocol == BLUE_CHIP_PROTOCOL_MORPHO
    assert cancelled_log.underlyingAsset == bravo_token.address
    
    # Check no longer pending
    assert not blue_chip_prices.hasPendingPriceFeedUpdate(bravo_token_vault)
    
    # Check no feed added
    assert not blue_chip_prices.hasPriceFeed(bravo_token_vault)


#######################
# Update Price Config #
#######################


def test_update_price_config_success(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
):
    """Test successful price config update"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # First add a feed
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Now update it
    assert blue_chip_prices.isValidUpdateConfig(alpha_token_vault, 15, 30)
    assert blue_chip_prices.updatePriceConfig(alpha_token_vault, 0, 15, 0, 30, sender=governance.address)
    
    # Check event immediately after transaction
    pending_log = filter_logs(blue_chip_prices, "PriceConfigUpdatePending")[0]
    assert pending_log.asset == alpha_token_vault.address
    assert pending_log.maxNumSnapshots == 15
    assert pending_log.staleTime == 30
    
    # Check pending state
    assert blue_chip_prices.hasPendingPriceFeedUpdate(alpha_token_vault)


def test_update_price_config_no_existing_feed(
    blue_chip_prices,
    governance,
    bravo_token_vault,
):
    """Test updating price config for non-existent feed"""
    # Should be invalid - no existing feed
    assert not blue_chip_prices.isValidUpdateConfig(bravo_token_vault, 15, 30)
    
    with boa.reverts("invalid config"):
        blue_chip_prices.updatePriceConfig(bravo_token_vault, 0, 15, 0, 30, sender=governance.address)


def test_update_price_config_invalid_params(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
):
    """Test updating price config with invalid parameters"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # First add a feed
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Invalid: maxNumSnapshots = 0
    assert not blue_chip_prices.isValidUpdateConfig(alpha_token_vault, 0, 30)
    with boa.reverts("invalid config"):
        blue_chip_prices.updatePriceConfig(alpha_token_vault, 0, 0, 0, 30, sender=governance.address)
    
    # Invalid: maxNumSnapshots > 25
    assert not blue_chip_prices.isValidUpdateConfig(alpha_token_vault, 26, 30)
    with boa.reverts("invalid config"):
        blue_chip_prices.updatePriceConfig(alpha_token_vault, 0, 26, 0, 30, sender=governance.address)


def test_confirm_price_feed_update_success(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
):
    """Test successful confirmation of price feed update"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # First add a feed
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Update it
    blue_chip_prices.updatePriceConfig(alpha_token_vault, 0, 15, 0, 30, sender=governance.address)
    
    # Time travel and confirm
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmPriceFeedUpdate(alpha_token_vault, sender=governance.address)
    
    # Check event immediately after transaction
    updated_log = filter_logs(blue_chip_prices, "PriceConfigUpdated")[0]
    assert updated_log.asset == alpha_token_vault.address
    assert updated_log.maxNumSnapshots == 15
    assert updated_log.staleTime == 30
    
    # Check no longer pending
    assert not blue_chip_prices.hasPendingPriceFeedUpdate(alpha_token_vault)
    
    # Check updated config
    config = blue_chip_prices.priceConfigs(alpha_token_vault)
    assert config.maxNumSnapshots == 15
    assert config.staleTime == 30


def test_cancel_price_feed_update(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
):
    """Test canceling pending price feed update"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # First add a feed
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Update it
    blue_chip_prices.updatePriceConfig(alpha_token_vault, 0, 15, 0, 30, sender=governance.address)
    assert blue_chip_prices.hasPendingPriceFeedUpdate(alpha_token_vault)
    
    # Cancel
    assert blue_chip_prices.cancelPriceFeedUpdate(alpha_token_vault, sender=governance.address)
    
    # Check event immediately after transaction
    cancelled_log = filter_logs(blue_chip_prices, "PriceConfigUpdateCancelled")[0]
    assert cancelled_log.asset == alpha_token_vault.address
    assert cancelled_log.protocol == BLUE_CHIP_PROTOCOL_MORPHO
    assert cancelled_log.underlyingAsset == alpha_token.address
    
    # Check no longer pending
    assert not blue_chip_prices.hasPendingPriceFeedUpdate(alpha_token_vault)
    
    # Check config unchanged
    config = blue_chip_prices.priceConfigs(alpha_token_vault)
    assert config.maxNumSnapshots == 10  # original values
    assert config.staleTime == 10


######################
# Disable Price Feed #
######################


def test_disable_price_feed_success(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
):
    """Test successful price feed disable initiation"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # First add a feed
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Should be valid to disable
    assert blue_chip_prices.isValidDisablePriceFeed(alpha_token_vault)
    
    # Disable it
    assert blue_chip_prices.disablePriceFeed(alpha_token_vault, sender=governance.address)
    
    # Check pending state
    assert blue_chip_prices.hasPendingPriceFeedUpdate(alpha_token_vault)


def test_disable_price_feed_no_existing_feed(
    blue_chip_prices,
    governance,
    bravo_token_vault,
):
    """Test disabling price feed for non-existent feed"""
    # Should be invalid - no existing feed
    assert not blue_chip_prices.isValidDisablePriceFeed(bravo_token_vault)
    
    with boa.reverts("invalid asset"):
        blue_chip_prices.disablePriceFeed(bravo_token_vault, sender=governance.address)


def test_confirm_disable_price_feed_success(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
):
    """Test successful confirmation of price feed disable"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # First add a feed
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Disable it
    blue_chip_prices.disablePriceFeed(alpha_token_vault, sender=governance.address)
    
    # Time travel and confirm
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmDisablePriceFeed(alpha_token_vault, sender=governance.address)
    
    # Check no longer pending
    assert not blue_chip_prices.hasPendingPriceFeedUpdate(alpha_token_vault)
    
    # Check no longer has feed
    assert not blue_chip_prices.hasPriceFeed(alpha_token_vault)
    
    # Check config is empty
    config = blue_chip_prices.priceConfigs(alpha_token_vault)
    assert config.underlyingAsset == ZERO_ADDRESS
    assert config.maxNumSnapshots == 0
    assert config.staleTime == 0


def test_cancel_disable_price_feed(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
):
    """Test canceling pending price feed disable"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # First add a feed
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Disable it
    blue_chip_prices.disablePriceFeed(alpha_token_vault, sender=governance.address)
    assert blue_chip_prices.hasPendingPriceFeedUpdate(alpha_token_vault)
    
    # Cancel
    assert blue_chip_prices.cancelDisablePriceFeed(alpha_token_vault, sender=governance.address)
    
    # Check no longer pending
    assert not blue_chip_prices.hasPendingPriceFeedUpdate(alpha_token_vault)
    
    # Check still has feed
    assert blue_chip_prices.hasPriceFeed(alpha_token_vault)
    
    # Check config unchanged
    config = blue_chip_prices.priceConfigs(alpha_token_vault)
    assert config.underlyingAsset == alpha_token.address
    assert config.maxNumSnapshots == 10
    assert config.staleTime == 10


########################
# Validation Functions #
########################


def test_is_valid_new_feed_comprehensive(
    blue_chip_prices,
    governance,
    bravo_token_vault,
    charlie_token_vault,
    mock_price_source,
    bravo_token,
    charlie_token,
):
    """Test comprehensive validation for new feeds"""
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 3 * EIGHTEEN_DECIMALS)
    
    # Valid cases
    assert blue_chip_prices.isValidNewFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 1, 0, 0)  # min snapshots
    assert blue_chip_prices.isValidNewFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 25, 0, 0)  # max snapshots
    assert blue_chip_prices.isValidNewFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 1000)  # with stale time
    assert blue_chip_prices.isValidNewFeed(charlie_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 10)  # different token
    
    # Invalid cases
    assert not blue_chip_prices.isValidNewFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 0, 0, 10)  # 0 snapshots
    assert not blue_chip_prices.isValidNewFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 26, 0, 10)  # too many snapshots
    
    # Add a feed and check it's no longer valid to add again
    blue_chip_prices.addNewPriceFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)
    
    assert not blue_chip_prices.isValidNewFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 20)  # already exists


def test_is_valid_update_config_comprehensive(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    bravo_token_vault,
    mock_price_source,
    alpha_token,
    bravo_token,
):
    """Test comprehensive validation for config updates"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    
    # Add a feed first
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Valid updates for existing feed
    assert blue_chip_prices.isValidUpdateConfig(alpha_token_vault, 1, 0)  # min snapshots
    assert blue_chip_prices.isValidUpdateConfig(alpha_token_vault, 25, 0)  # max snapshots
    assert blue_chip_prices.isValidUpdateConfig(alpha_token_vault, 15, 1000)  # with stale time
    
    # Invalid updates for existing feed
    assert not blue_chip_prices.isValidUpdateConfig(alpha_token_vault, 0, 10)  # 0 snapshots
    assert not blue_chip_prices.isValidUpdateConfig(alpha_token_vault, 26, 10)  # too many snapshots
    
    # Invalid for non-existent feed
    assert not blue_chip_prices.isValidUpdateConfig(bravo_token_vault, 10, 10)  # no feed exists


def test_is_valid_disable_price_feed_comprehensive(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    bravo_token_vault,
    mock_price_source,
    alpha_token,
):
    """Test comprehensive validation for disabling feeds"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Invalid - no feed exists
    assert not blue_chip_prices.isValidDisablePriceFeed(bravo_token_vault)
    
    # Add a feed
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Valid - feed exists
    assert blue_chip_prices.isValidDisablePriceFeed(alpha_token_vault)
    
    # Disable it
    blue_chip_prices.disablePriceFeed(alpha_token_vault, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmDisablePriceFeed(alpha_token_vault, sender=governance.address)
    
    # Invalid again - no feed exists anymore
    assert not blue_chip_prices.isValidDisablePriceFeed(alpha_token_vault)


#######################
# Edge Cases & Errors #
#######################


def test_no_price_for_underlying_asset(
    blue_chip_prices,
    bravo_token_vault,
):
    """Test that feeds are invalid when underlying asset has no price"""
    # Don't set price for bravo_token
    assert not blue_chip_prices.isValidNewFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10)


def test_operations_when_paused(
    blue_chip_prices,
    governance,
    bravo_token_vault,
    mock_price_source,
    bravo_token,
    switchboard_alpha,
):
    """Test that operations fail when contract is paused"""
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    
    # Pause the contract
    blue_chip_prices.pause(True, sender=switchboard_alpha.address)
    
    # All operations should fail when paused
    with boa.reverts("contract paused"):
        blue_chip_prices.addNewPriceFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10, sender=governance.address)
    
    with boa.reverts("contract paused"):
        blue_chip_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)
    
    with boa.reverts("contract paused"):
        blue_chip_prices.cancelNewPendingPriceFeed(bravo_token_vault, sender=governance.address)


def test_multiple_pending_operations_same_asset(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
):
    """Test that new operations overwrite previous pending operations for the same asset"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Add a feed
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Start an update
    blue_chip_prices.updatePriceConfig(alpha_token_vault, 0, 15, 0, 30, sender=governance.address)
    
    # Check first operation is pending
    assert blue_chip_prices.hasPendingPriceFeedUpdate(alpha_token_vault)
    
    # Start another operation - this should overwrite the previous pending operation
    blue_chip_prices.updatePriceConfig(alpha_token_vault, 0, 20, 0, 40, sender=governance.address)
    
    # Still pending but now with new values
    assert blue_chip_prices.hasPendingPriceFeedUpdate(alpha_token_vault)
    
    # Confirm the operation and verify it uses the latest values (20, 40)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmPriceFeedUpdate(alpha_token_vault, sender=governance.address)
    
    # Verify the config has the latest values, not the first ones
    config = blue_chip_prices.priceConfigs(alpha_token_vault)
    assert config.maxNumSnapshots == 20  # Should be latest value, not 15
    assert config.staleTime == 40  # Should be latest value, not 30


##################
# Snapshot Tests #
##################


def test_basic_snapshot_creation(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
):
    """Test basic snapshot creation and retrieval"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Add price feed
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 3, 0, 100, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Initial snapshot should be created during registration
    config = blue_chip_prices.priceConfigs(alpha_token_vault)
    assert config.nextIndex == 1
    
    # Get initial snapshot
    initial_snapshot = blue_chip_prices.getLatestSnapshot(alpha_token_vault)
    assert initial_snapshot.totalSupply == 0  # No deposits yet
    assert initial_snapshot.pricePerShare == 1 * EIGHTEEN_DECIMALS  # 1:1 ratio initially
    
    # Make a deposit to change total supply
    alpha_token.approve(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault.deposit(100 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)
    
    # Advance time to allow new snapshot
    boa.env.time_travel(seconds=1)
    
    # Add new snapshot
    result = blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    assert result == True  # Should succeed now
    
    # Check new snapshot
    new_snapshot = blue_chip_prices.getLatestSnapshot(alpha_token_vault)
    assert new_snapshot.totalSupply == 100  # 100 tokens deposited
    assert new_snapshot.pricePerShare == 1 * EIGHTEEN_DECIMALS  # Still 1:1 ratio
    
    # Verify nextIndex incremented
    config = blue_chip_prices.priceConfigs(alpha_token_vault)
    assert config.nextIndex == 2


def test_weighted_price_calculation(
    blue_chip_prices,
    governance,
    bravo_token_vault,
    bravo_token_whale,
    mock_price_source,
    bravo_token,
    teller,
):
    """Test weighted price calculation with multiple snapshots"""
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    
    # Add price feed with small max snapshots for easier testing
    blue_chip_prices.addNewPriceFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 3, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)
    
    # Snapshot 1: 100 tokens at 1:1 ratio
    bravo_token.approve(bravo_token_vault, 100 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    bravo_token_vault.deposit(100 * EIGHTEEN_DECIMALS, bravo_token_whale, sender=bravo_token_whale)
    boa.env.time_travel(seconds=1)  # Advance time
    blue_chip_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    snapshot1 = blue_chip_prices.snapShots(bravo_token_vault, 1)
    
    # Snapshot 2: Transfer tokens to vault to change price per share (200 tokens, same shares)
    bravo_token.transfer(bravo_token_vault, 100 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    boa.env.time_travel(seconds=1)  # Advance time
    blue_chip_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    snapshot2 = blue_chip_prices.snapShots(bravo_token_vault, 2)
    
    # Snapshot 3: Deposit more to change total supply (300 tokens total, 150 shares)
    bravo_token.approve(bravo_token_vault, 50 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    bravo_token_vault.deposit(50 * EIGHTEEN_DECIMALS, bravo_token_whale, sender=bravo_token_whale)
    boa.env.time_travel(seconds=1)  # Advance time
    blue_chip_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    snapshot3 = blue_chip_prices.snapShots(bravo_token_vault, 0)  # Wraps to index 0
    
    # Calculate weighted average from actual snapshot data
    # Weighted = (snapshot1.totalSupply * snapshot1.pricePerShare + 
    #             snapshot2.totalSupply * snapshot2.pricePerShare + 
    #             snapshot3.totalSupply * snapshot3.pricePerShare) / 
    #            (snapshot1.totalSupply + snapshot2.totalSupply + snapshot3.totalSupply)
    numerator = (snapshot1.totalSupply * snapshot1.pricePerShare + 
                 snapshot2.totalSupply * snapshot2.pricePerShare + 
                 snapshot3.totalSupply * snapshot3.pricePerShare)
    denominator = snapshot1.totalSupply + snapshot2.totalSupply + snapshot3.totalSupply
    expected_weighted_price = numerator // denominator
    
    weighted_price = blue_chip_prices.getWeightedPrice(bravo_token_vault)
    assert weighted_price == expected_weighted_price


def test_snapshot_rotation(
    blue_chip_prices,
    governance,
    charlie_token_vault,
    charlie_token_whale,
    mock_price_source,
    charlie_token,
    teller,
):
    """Test that snapshots rotate when maxNumSnapshots is reached"""
    mock_price_source.setPrice(charlie_token, 3 * EIGHTEEN_DECIMALS)
    
    # Add price feed with maxNumSnapshots = 2
    blue_chip_prices.addNewPriceFeed(charlie_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 2, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(charlie_token_vault, sender=governance.address)
    
    # Initial state: nextIndex should be 1 (snapshot created during registration)
    config = blue_chip_prices.priceConfigs(charlie_token_vault)
    assert config.nextIndex == 1
    
    # Add first manual snapshot (index 1)
    charlie_token.approve(charlie_token_vault, 100 * (10 ** charlie_token.decimals()), sender=charlie_token_whale)
    charlie_token_vault.deposit(100 * (10 ** charlie_token.decimals()), charlie_token_whale, sender=charlie_token_whale)
    boa.env.time_travel(seconds=1)  # Advance time
    blue_chip_prices.addPriceSnapshot(charlie_token_vault, sender=teller.address)
    
    config = blue_chip_prices.priceConfigs(charlie_token_vault)
    assert config.nextIndex == 0  # Should wrap back to 0
    
    # Add second manual snapshot (index 0, overwriting the initial snapshot)
    charlie_token.transfer(charlie_token_vault, 50 * (10 ** charlie_token.decimals()), sender=charlie_token_whale)
    boa.env.time_travel(seconds=1)  # Advance time
    blue_chip_prices.addPriceSnapshot(charlie_token_vault, sender=teller.address)
    
    config = blue_chip_prices.priceConfigs(charlie_token_vault)
    assert config.nextIndex == 1  # Should be back to 1
    
    # Verify only 2 snapshots exist (others were overwritten)
    # We know exactly what should be in each index:
    # Index 0: 2nd manual snapshot (100 deposited + 50 transferred = 150 total supply, 1.5 price per share)
    # Index 1: 1st manual snapshot (100 deposited = 100 total supply, 1.0 price per share)
    snapshot_at_index_0 = blue_chip_prices.snapShots(charlie_token_vault, 0)
    snapshot_at_index_1 = blue_chip_prices.snapShots(charlie_token_vault, 1)
    
    # Assert exactly what should be in index 0 (2nd manual snapshot with transfer)
    assert snapshot_at_index_0.totalSupply == 100  # 100 tokens deposited initially
    assert snapshot_at_index_0.pricePerShare == 1500000  # 1.5 * 10^6 (charlie token has 6 decimals)
    
    # Assert exactly what should be in index 1 (1st manual snapshot)  
    assert snapshot_at_index_1.totalSupply == 100  # 100 tokens deposited
    assert snapshot_at_index_1.pricePerShare == 1000000  # 1.0 * 10^6 (charlie token has 6 decimals)
    
    # Calculate expected weighted price precisely
    # Weighted = (100 * 1500000 + 100 * 1000000) / (100 + 100) = 250000000 / 200 = 1250000
    expected_weighted_price = (100 * 1500000 + 100 * 1000000) // (100 + 100)
    
    weighted_price = blue_chip_prices.getWeightedPrice(charlie_token_vault)
    assert weighted_price == expected_weighted_price


def test_stale_snapshot_handling(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
):
    """Test that stale snapshots are ignored in weighted price calculation"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Add price feed with staleTime = 10 seconds
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Create first snapshot
    alpha_token.approve(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault.deposit(100 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)
    blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    
    # Time travel to make the snapshot stale (> 10 seconds)
    boa.env.time_travel(seconds=15)
    
    # Create second snapshot
    alpha_token.transfer(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    
    # The weighted price should only consider the non-stale snapshot
    weighted_price = blue_chip_prices.getWeightedPrice(alpha_token_vault)
    latest_snapshot = blue_chip_prices.getLatestSnapshot(alpha_token_vault)
    
    # Should equal the latest snapshot's price since older ones are stale
    assert weighted_price == latest_snapshot.pricePerShare


def test_no_valid_snapshots_fallback(
    blue_chip_prices,
    governance,
    bravo_token_vault,
    mock_price_source,
    bravo_token,
):
    """Test fallback to lastSnapshot when no valid snapshots exist"""
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    
    # Add price feed with very short stale time
    blue_chip_prices.addNewPriceFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 3, 0, 1, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)
    
    # Time travel to make all snapshots stale
    boa.env.time_travel(seconds=5)
    
    # Get weighted price - should fallback to lastSnapshot
    weighted_price = blue_chip_prices.getWeightedPrice(bravo_token_vault)
    config = blue_chip_prices.priceConfigs(bravo_token_vault)
    
    assert weighted_price == config.lastSnapshot.pricePerShare


def test_snapshot_prevents_duplicates_same_block(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
):
    """Test that multiple snapshot calls in same block don't create duplicates"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Add price feed
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Make a deposit
    alpha_token.approve(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault.deposit(100 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)
    
    # Get initial nextIndex
    config_before = blue_chip_prices.priceConfigs(alpha_token_vault)
    initial_next_index = config_before.nextIndex
    
    # Advance time first
    boa.env.time_travel(seconds=1)
    
    # Add first snapshot
    result1 = blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    
    # Try to add another snapshot in same block (same timestamp) - should fail
    result2 = blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    
    # First should succeed, second should fail/not add
    assert result1 == True
    assert result2 == False  # Should return False for duplicate in same timestamp
    
    # nextIndex should only increment once
    config_after = blue_chip_prices.priceConfigs(alpha_token_vault)
    assert config_after.nextIndex == (initial_next_index + 1) % config_after.maxNumSnapshots


def test_empty_vault_snapshot_handling(
    blue_chip_prices,
    governance,
    bravo_token_vault,
    mock_price_source,
    bravo_token,
    teller,
):
    """Test snapshot creation with empty vault (zero total supply)"""
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    
    # Add price feed
    blue_chip_prices.addNewPriceFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 3, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)
    
    # Add snapshot with empty vault
    blue_chip_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    
    # Get latest snapshot
    snapshot = blue_chip_prices.getLatestSnapshot(bravo_token_vault)
    assert snapshot.totalSupply == 0
    assert snapshot.pricePerShare == 1 * EIGHTEEN_DECIMALS  # Should still have valid pricePerShare
    
    # Weighted price should fallback to lastSnapshot.pricePerShare since no snapshots have totalSupply > 0
    weighted_price = blue_chip_prices.getWeightedPrice(bravo_token_vault)
    config = blue_chip_prices.priceConfigs(bravo_token_vault)
    assert weighted_price == config.lastSnapshot.pricePerShare


def test_price_per_share_changes(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
):
    """Test comprehensive price per share changes and snapshot tracking"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Add price feed
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 10, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Stage 1: Initial deposit (1:1 ratio)
    alpha_token.approve(alpha_token_vault, 2000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)  # Approve more tokens
    alpha_token_vault.deposit(1000 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)
    boa.env.time_travel(seconds=1)  # Advance time
    blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    
    snapshot1 = blue_chip_prices.getLatestSnapshot(alpha_token_vault)
    assert snapshot1.totalSupply == 1000
    assert snapshot1.pricePerShare == 1 * EIGHTEEN_DECIMALS
    
    # Stage 2: Transfer tokens to vault (increases price per share)
    alpha_token.transfer(alpha_token_vault, 500 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    boa.env.time_travel(seconds=1)  # Advance time
    blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    
    snapshot2 = blue_chip_prices.getLatestSnapshot(alpha_token_vault)
    assert snapshot2.totalSupply == 1000  # Same shares
    assert snapshot2.pricePerShare == 1.5 * EIGHTEEN_DECIMALS  # 1500 tokens / 1000 shares
    
    # Stage 3: Another deposit (dilutes price per share back down)
    alpha_token_vault.deposit(500 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)
    boa.env.time_travel(seconds=1)  # Advance time
    blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    
    snapshot3 = blue_chip_prices.getLatestSnapshot(alpha_token_vault)
    # Total assets: 1500 + 500 = 2000, total shares: 1000 + 333.33 ≈ 1333
    # Price per share should be around 1.5 (2000/1333)
    assert snapshot3.totalSupply == 1333  # Exact shares: 1000 + (500/(1500/1000)) = 1000 + 333.33 = 1333
    assert snapshot3.pricePerShare == 1.5 * EIGHTEEN_DECIMALS  # Should maintain the ratio
    
    # Verify weighted price considers all snapshots
    # We know exactly what snapshots should exist:
    # - Initial snapshot at index 0 (created during confirmNewPriceFeed): totalSupply=0, ignored in weighting
    # - Stage 1 snapshot at index 1: totalSupply=1000, pricePerShare=1e18  
    # - Stage 2 snapshot at index 2: totalSupply=1000, pricePerShare=1.5e18
    # - Stage 3 snapshot at index 3: totalSupply=1333, pricePerShare=1.5e18
    
    snapshot_0 = blue_chip_prices.snapShots(alpha_token_vault, 0)  # Initial (ignored due to totalSupply=0)
    snapshot_1 = blue_chip_prices.snapShots(alpha_token_vault, 1)  # Stage 1
    snapshot_2 = blue_chip_prices.snapShots(alpha_token_vault, 2)  # Stage 2  
    snapshot_3 = blue_chip_prices.snapShots(alpha_token_vault, 3)  # Stage 3
    
    # Assert exact values for each snapshot
    assert snapshot_0.totalSupply == 0  # Initial snapshot, ignored in weighting
    assert snapshot_1.totalSupply == 1000 and snapshot_1.pricePerShare == 1 * EIGHTEEN_DECIMALS
    assert snapshot_2.totalSupply == 1000 and snapshot_2.pricePerShare == 1.5 * EIGHTEEN_DECIMALS  
    assert snapshot_3.totalSupply == 1333 and snapshot_3.pricePerShare == 1.5 * EIGHTEEN_DECIMALS
    
    # Calculate expected weighted price precisely (excluding snapshot_0 due to totalSupply=0)
    # Weighted = (1000*1e18 + 1000*1.5e18 + 1333*1.5e18) / (1000+1000+1333)
    numerator = (1000 * 1 * EIGHTEEN_DECIMALS + 1000 * 15 * EIGHTEEN_DECIMALS // 10 + 1333 * 15 * EIGHTEEN_DECIMALS // 10)
    denominator = (1000 + 1000 + 1333)
    expected_weighted_price = numerator // denominator
    
    weighted_price = blue_chip_prices.getWeightedPrice(alpha_token_vault)
    assert weighted_price == expected_weighted_price


##############################
# Max Upside Deviation Tests #
##############################


def test_max_upside_deviation_validation(
    blue_chip_prices,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
):
    """Test validation of maxUpsideDeviation parameter"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Valid: 0% deviation (no limit)
    assert blue_chip_prices.isValidNewFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 10)
    
    # Valid: 50% deviation
    assert blue_chip_prices.isValidNewFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 5000, 10)  # 50%
    
    # Valid: 100% deviation
    assert blue_chip_prices.isValidNewFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 10000, 10)  # 100%
    
    # Invalid: >100% deviation
    assert not blue_chip_prices.isValidNewFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 10001, 10)  # 100.01%
    
    # Invalid: very high deviation
    assert not blue_chip_prices.isValidNewFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 50000, 10)  # 500%


def test_max_upside_deviation_throttling_basic(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
):
    """Test basic price throttling with maxUpsideDeviation"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Add feed with 10% max upside deviation
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 1000, 0, sender=governance.address)  # 10%
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Initial deposit to establish baseline
    alpha_token.approve(alpha_token_vault, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault.deposit(1000 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)
    blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    
    initial_snapshot = blue_chip_prices.getLatestSnapshot(alpha_token_vault)
    assert initial_snapshot.pricePerShare == 1 * EIGHTEEN_DECIMALS
    
    # Transfer a large amount to vault (would normally double the price per share)
    alpha_token.transfer(alpha_token_vault, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    
    # Price should be throttled to max 10% increase
    throttled_snapshot = blue_chip_prices.getLatestSnapshot(alpha_token_vault)
    expected_max_price = 1 * EIGHTEEN_DECIMALS + (1 * EIGHTEEN_DECIMALS * 1000 // 10000)  # 1.1 * EIGHTEEN_DECIMALS
    assert throttled_snapshot.pricePerShare == expected_max_price


def test_max_upside_deviation_no_limit(
    blue_chip_prices,
    governance,
    bravo_token_vault,
    bravo_token_whale,
    mock_price_source,
    bravo_token,
    teller,
):
    """Test that 0 maxUpsideDeviation means no throttling"""
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    
    # Add feed with 0% max upside deviation (no limit)
    blue_chip_prices.addNewPriceFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)
    
    # Initial deposit
    bravo_token.approve(bravo_token_vault, 100 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    bravo_token_vault.deposit(100 * EIGHTEEN_DECIMALS, bravo_token_whale, sender=bravo_token_whale)
    blue_chip_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    
    # Transfer large amount (triple the price per share)
    bravo_token.transfer(bravo_token_vault, 200 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    blue_chip_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    
    # Price should not be throttled
    final_snapshot = blue_chip_prices.getLatestSnapshot(bravo_token_vault)
    assert final_snapshot.pricePerShare == 3 * EIGHTEEN_DECIMALS  # Full 3x increase allowed


def test_max_upside_deviation_gradual_increases(
    blue_chip_prices,
    governance,
    charlie_token_vault,
    charlie_token_whale,
    mock_price_source,
    charlie_token,
    teller,
):
    """Test gradual price increases within and beyond deviation limits"""
    mock_price_source.setPrice(charlie_token, 3 * EIGHTEEN_DECIMALS)
    
    # Add feed with 5% max upside deviation
    blue_chip_prices.addNewPriceFeed(charlie_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 500, 0, sender=governance.address)  # 5%
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(charlie_token_vault, sender=governance.address)
    
    # Initial deposit
    charlie_token.approve(charlie_token_vault, 1000 * (10 ** charlie_token.decimals()), sender=charlie_token_whale)
    charlie_token_vault.deposit(1000 * (10 ** charlie_token.decimals()), charlie_token_whale, sender=charlie_token_whale)
    boa.env.time_travel(seconds=1)  # Advance time
    blue_chip_prices.addPriceSnapshot(charlie_token_vault, sender=teller.address)
    
    # Get the config to check lastSnapshot (this is what throttling uses as reference)
    config_after_first = blue_chip_prices.priceConfigs(charlie_token_vault)
    first_snapshot_price = config_after_first.lastSnapshot.pricePerShare
    
    # Small increase (within 5% limit)
    charlie_token.transfer(charlie_token_vault, 30 * (10 ** charlie_token.decimals()), sender=charlie_token_whale)  # 3% increase
    boa.env.time_travel(seconds=1)  # Advance time
    blue_chip_prices.addPriceSnapshot(charlie_token_vault, sender=teller.address)
    
    # Get config again to see the new lastSnapshot
    config_after_second = blue_chip_prices.priceConfigs(charlie_token_vault)
    second_snapshot_price = config_after_second.lastSnapshot.pricePerShare
    
    # Should allow the full 3% increase
    expected_price_1 = first_snapshot_price * 103 // 100
    assert second_snapshot_price == expected_price_1
    
    # Large increase (beyond 5% limit)
    charlie_token.transfer(charlie_token_vault, 200 * (10 ** charlie_token.decimals()), sender=charlie_token_whale)  # Would be ~15% more
    boa.env.time_travel(seconds=1)  # Advance time
    blue_chip_prices.addPriceSnapshot(charlie_token_vault, sender=teller.address)
    
    # Get config for the final snapshot
    config_after_third = blue_chip_prices.priceConfigs(charlie_token_vault)
    third_snapshot_price = config_after_third.lastSnapshot.pricePerShare
    
    # Should be throttled to 5% increase from the previous lastSnapshot price
    expected_max_price = second_snapshot_price + (second_snapshot_price * 500 // 10000)  # 5% increase
    assert third_snapshot_price == expected_max_price


def test_max_upside_deviation_with_existing_config(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
):
    """Test updating maxUpsideDeviation for existing config"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Add feed with no deviation limit initially
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Update to add 20% deviation limit
    blue_chip_prices.updatePriceConfig(alpha_token_vault, 0, 5, 2000, 0, sender=governance.address)  # 20%
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmPriceFeedUpdate(alpha_token_vault, sender=governance.address)
    
    # Verify config was updated
    config = blue_chip_prices.priceConfigs(alpha_token_vault)
    assert config.maxUpsideDeviation == 2000
    
    # Test that throttling now works
    alpha_token.approve(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault.deposit(100 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)
    blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    
    # Large transfer should be throttled
    alpha_token.transfer(alpha_token_vault, 200 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    
    final_snapshot = blue_chip_prices.getLatestSnapshot(alpha_token_vault)
    # Should be throttled to exactly 20% increase from the lastSnapshot price
    # Last snapshot was at 1e18, so 20% increase = 1e18 + (1e18 * 2000 / 10000) = 1.2e18
    expected_throttled_price = 1 * EIGHTEEN_DECIMALS + (1 * EIGHTEEN_DECIMALS * 2000 // 10000)
    assert final_snapshot.pricePerShare == expected_throttled_price


def test_max_upside_deviation_event_assertions(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
):
    """Test that events properly include maxUpsideDeviation"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Add feed with deviation limit
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 1500, 60, sender=governance.address)  # 15%
    
    # Check pending event
    pending_log = filter_logs(blue_chip_prices, "NewPriceConfigPending")[0]
    assert pending_log.maxUpsideDeviation == 1500
    
    # Confirm and check added event
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    added_log = filter_logs(blue_chip_prices, "NewPriceConfigAdded")[0]
    assert added_log.maxUpsideDeviation == 1500
    
    # Update config
    blue_chip_prices.updatePriceConfig(alpha_token_vault, 0, 8, 2500, 90, sender=governance.address)  # 25%
    
    update_pending_log = filter_logs(blue_chip_prices, "PriceConfigUpdatePending")[0]
    assert update_pending_log.maxUpsideDeviation == 2500
    
    # Confirm update
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmPriceFeedUpdate(alpha_token_vault, sender=governance.address)
    
    updated_log = filter_logs(blue_chip_prices, "PriceConfigUpdated")[0]
    assert updated_log.maxUpsideDeviation == 2500


def test_invalid_max_upside_deviation_in_update(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
):
    """Test that invalid maxUpsideDeviation values are rejected in updates"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Add valid feed first
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 1000, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Try to update with invalid deviation (>100%)
    with boa.reverts("invalid config"):
        blue_chip_prices.updatePriceConfig(alpha_token_vault, 0, 5, 15000, 0, sender=governance.address)  # 150%
    
    # Try to update with valid deviation
    blue_chip_prices.updatePriceConfig(alpha_token_vault, 0, 5, 5000, 0, sender=governance.address)  # 50% - should work


############################
# Min Snapshot Delay Tests #
############################


def test_min_snapshot_delay_validation(
    blue_chip_prices,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
):
    """Test validation of minSnapshotDelay parameter"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Valid: 0 seconds (no delay)
    assert blue_chip_prices.isValidNewFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 10)
    
    # Valid: 5 minutes
    assert blue_chip_prices.isValidNewFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 300, 5, 0, 10)
    
    # Valid: 1 day
    assert blue_chip_prices.isValidNewFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 86400, 5, 0, 10)
    
    # Valid: 1 week (max allowed)
    assert blue_chip_prices.isValidNewFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 604800, 5, 0, 10)
    
    # Invalid: >1 week
    assert not blue_chip_prices.isValidNewFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 604801, 5, 0, 10)


def test_min_snapshot_delay_prevents_spam(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
):
    """Test that minSnapshotDelay prevents rapid snapshot creation"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Add feed with 10 second min delay
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 10, 5, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Make a deposit to change state
    alpha_token.approve(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault.deposit(100 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)
    
    # Get initial nextIndex after registration snapshot
    config_before = blue_chip_prices.priceConfigs(alpha_token_vault)
    initial_next_index = config_before.nextIndex
    
    # Try to add snapshot immediately - should fail due to delay
    result1 = blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    assert result1 == False  # Should fail due to minSnapshotDelay
    
    # nextIndex should not have changed
    config_after_fail = blue_chip_prices.priceConfigs(alpha_token_vault)
    assert config_after_fail.nextIndex == initial_next_index
    
    # Wait 5 seconds - still too early
    boa.env.time_travel(seconds=5)
    result2 = blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    assert result2 == False  # Should still fail
    
    # Wait another 6 seconds (total 11 seconds) - should work now
    boa.env.time_travel(seconds=6)
    result3 = blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    assert result3 == True  # Should succeed now
    
    # nextIndex should have incremented
    config_after_success = blue_chip_prices.priceConfigs(alpha_token_vault)
    assert config_after_success.nextIndex == (initial_next_index + 1) % config_after_success.maxNumSnapshots


def test_min_snapshot_delay_zero_means_no_delay(
    blue_chip_prices,
    governance,
    bravo_token_vault,
    bravo_token_whale,
    mock_price_source,
    bravo_token,
    teller,
):
    """Test that 0 minSnapshotDelay means no delay restriction"""
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    
    # Add feed with no min delay
    blue_chip_prices.addNewPriceFeed(bravo_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)
    
    # Make a deposit
    bravo_token.approve(bravo_token_vault, 100 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    bravo_token_vault.deposit(100 * EIGHTEEN_DECIMALS, bravo_token_whale, sender=bravo_token_whale)
    
    # Advance time by 1 second to avoid duplicate timestamp check
    boa.env.time_travel(seconds=1)
    
    # Should be able to add snapshot immediately (no minSnapshotDelay)
    result = blue_chip_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    assert result == True  # Should succeed immediately


def test_min_snapshot_delay_updated_config(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
):
    """Test that updating minSnapshotDelay affects future snapshots"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Add feed with no delay initially
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 0, 5, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Make a deposit and add snapshot (should work with no delay)
    alpha_token.approve(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault.deposit(100 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)
    
    # Advance time to avoid duplicate timestamp
    boa.env.time_travel(seconds=1)
    result1 = blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    assert result1 == True
    
    # Update config to add 5 second delay
    blue_chip_prices.updatePriceConfig(alpha_token_vault, 5, 5, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmPriceFeedUpdate(alpha_token_vault, sender=governance.address)
    
    # Now snapshots should be delayed
    alpha_token.transfer(alpha_token_vault, 50 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Advance time by 1 second to avoid duplicate timestamp check
    boa.env.time_travel(seconds=1)
    
    # Try immediately - should fail due to minSnapshotDelay (only 1 second passed, need >5)
    result2 = blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    assert result2 == False
    
    # Wait 5 more seconds (total 6 seconds) - should work
    boa.env.time_travel(seconds=5)
    result3 = blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    assert result3 == True


def test_min_snapshot_delay_resets_after_successful_snapshot(
    blue_chip_prices,
    governance,
    charlie_token_vault,
    charlie_token_whale,
    mock_price_source,
    charlie_token,
    teller,
):
    """Test that delay resets after each successful snapshot"""
    mock_price_source.setPrice(charlie_token, 3 * EIGHTEEN_DECIMALS)
    
    # Add feed with 8 second delay
    blue_chip_prices.addNewPriceFeed(charlie_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 8, 5, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(charlie_token_vault, sender=governance.address)
    
    # Make a deposit
    charlie_token.approve(charlie_token_vault, 100 * (10 ** charlie_token.decimals()), sender=charlie_token_whale)
    charlie_token_vault.deposit(100 * (10 ** charlie_token.decimals()), charlie_token_whale, sender=charlie_token_whale)
    
    # Wait and add first snapshot
    boa.env.time_travel(seconds=9)
    result1 = blue_chip_prices.addPriceSnapshot(charlie_token_vault, sender=teller.address)
    assert result1 == True
    
    # Change state and try again immediately - should fail
    charlie_token.transfer(charlie_token_vault, 50 * (10 ** charlie_token.decimals()), sender=charlie_token_whale)
    result2 = blue_chip_prices.addPriceSnapshot(charlie_token_vault, sender=teller.address)
    assert result2 == False
    
    # Wait 8 seconds and try again - should work
    boa.env.time_travel(seconds=8)
    result3 = blue_chip_prices.addPriceSnapshot(charlie_token_vault, sender=teller.address)
    assert result3 == True


def test_min_snapshot_delay_edge_cases(
    blue_chip_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
):
    """Test edge cases for minSnapshotDelay"""
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    
    # Add feed with 2 second delay for clearer testing
    blue_chip_prices.addNewPriceFeed(alpha_token_vault, BLUE_CHIP_PROTOCOL_MORPHO, 2, 5, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    blue_chip_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)
    
    # Make a deposit
    alpha_token.approve(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault.deposit(100 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)
    
    # 1 second should fail (less than 2 second delay)
    boa.env.time_travel(seconds=1)
    result1 = blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    assert result1 == False  # Should fail - need >= 2 seconds
    
    # Exactly 2 seconds should succeed (condition is >= not >)
    boa.env.time_travel(seconds=1)  # Total 2 seconds
    result2 = blue_chip_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    assert result2 == True  # Should succeed - exactly matches the delay requirement