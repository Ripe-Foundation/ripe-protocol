import hashlib

import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from conf_utils import filter_logs


#####################
# Local Integration #
#####################


def test_setup_underscore_registry(
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test that we can set the underscore registry in mission control"""
    # Set the underscore registry
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)

    # Verify it was set
    assert mission_control.underscoreRegistry() == mock_undy_v2.address


def test_add_local_undy_vault_asset(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    price_desk,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test end-to-end integration: add vault, create snapshots, verify pricing"""
    # Setup underscore registry
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)

    # Set price for underlying asset
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    assert undy_vault_prices.isValidNewFeed(alpha_token_vault, 0, 10, 0, 10)

    # Add new price feed - using positional args with custom values
    assert undy_vault_prices.addNewPriceFeed(alpha_token_vault, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    log = filter_logs(undy_vault_prices, "NewPriceConfigAdded")[0]

    # Verify config
    config = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert config.underlyingAsset == alpha_token.address
    assert config.underlyingDecimals == 18
    assert config.vaultTokenDecimals == 18
    assert config.minSnapshotDelay == 0
    assert config.maxNumSnapshots == 10
    assert config.maxUpsideDeviation == 0
    assert config.staleTime == 10
    assert config.nextIndex == 1  # snapshot taken during registration

    # Verify event
    assert log.asset == alpha_token_vault.address
    assert log.underlyingAsset == alpha_token.address
    assert log.maxNumSnapshots == 10
    assert log.maxUpsideDeviation == 0
    assert log.staleTime == 10

    alpha_token_price = price_desk.getPrice(alpha_token)
    assert alpha_token_price == 1 * EIGHTEEN_DECIMALS

    # Test price
    alpha_vault_price = undy_vault_prices.getPrice(alpha_token_vault)
    assert alpha_vault_price == alpha_token_price

    # Deposit
    alpha_token.approve(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault.deposit(100 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)

    # Still same price
    alpha_vault_price = undy_vault_prices.getPrice(alpha_token_vault)
    assert alpha_vault_price == alpha_token_price
    first_snapshot = undy_vault_prices.getLatestSnapshot(alpha_token_vault)

    # Have whale transfer double the amount
    alpha_token.transfer(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # Still same price, no new snapshot
    alpha_vault_price = undy_vault_prices.getPrice(alpha_token_vault)
    assert alpha_vault_price == alpha_token_price

    # But latest snapshot has new price per share
    latest_snapshot = undy_vault_prices.getLatestSnapshot(alpha_token_vault)
    assert latest_snapshot.pricePerShare == first_snapshot.pricePerShare * 2

    # Advance time to allow new snapshot
    boa.env.time_travel(seconds=1)

    # Add new snapshot
    undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)

    # New price
    assert undy_vault_prices.getPrice(alpha_token_vault) == alpha_token_price * 2


######################
# Add New Price Feed #
######################


def test_add_new_price_feed_success(
    undy_vault_prices,
    governance,
    bravo_token_vault,
    mock_price_source,
    bravo_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test successful addition of new price feed"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)

    # Should be valid
    assert undy_vault_prices.isValidNewFeed(bravo_token_vault, 0, 5, 0, 20)

    # Add new price feed
    assert undy_vault_prices.addNewPriceFeed(bravo_token_vault, 0, 5, 0, 20, sender=governance.address)

    # Check event immediately after transaction
    pending_log = filter_logs(undy_vault_prices, "NewPriceConfigPending")[0]
    assert pending_log.asset == bravo_token_vault.address
    assert pending_log.underlyingAsset == bravo_token.address
    assert pending_log.maxNumSnapshots == 5
    assert pending_log.maxUpsideDeviation == 0
    assert pending_log.staleTime == 20

    # Check pending state
    assert undy_vault_prices.hasPendingPriceFeedUpdate(bravo_token_vault)


def test_add_new_price_feed_invalid_params(
    undy_vault_prices,
    governance,
    charlie_token_vault,
    mock_price_source,
    charlie_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test adding new price feed with invalid parameters"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(charlie_token, 3 * EIGHTEEN_DECIMALS)

    # Invalid: maxNumSnapshots = 0
    assert not undy_vault_prices.isValidNewFeed(charlie_token_vault, 0, 0, 0, 10)
    with boa.reverts("invalid feed"):
        undy_vault_prices.addNewPriceFeed(charlie_token_vault, 0, 0, 0, 10, sender=governance.address)

    # Invalid: maxNumSnapshots > 25
    assert not undy_vault_prices.isValidNewFeed(charlie_token_vault, 0, 26, 0, 10)
    with boa.reverts("invalid feed"):
        undy_vault_prices.addNewPriceFeed(charlie_token_vault, 0, 26, 0, 10, sender=governance.address)


def test_add_new_price_feed_no_governance(
    undy_vault_prices,
    alice,
    bravo_token_vault,
    mock_price_source,
    bravo_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test adding new price feed without governance permissions"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)

    with boa.reverts("no perms"):
        undy_vault_prices.addNewPriceFeed(bravo_token_vault, 0, 5, 0, 20, sender=alice)


def test_add_new_price_feed_already_exists(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test adding price feed for asset that already has one"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Add first feed
    undy_vault_prices.addNewPriceFeed(alpha_token_vault, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    # Try to add again - should be invalid
    assert not undy_vault_prices.isValidNewFeed(alpha_token_vault, 0, 5, 0, 20)
    with boa.reverts("invalid feed"):
        undy_vault_prices.addNewPriceFeed(alpha_token_vault, 0, 5, 0, 20, sender=governance.address)


def test_confirm_new_price_feed_before_timelock(
    undy_vault_prices,
    governance,
    bravo_token_vault,
    mock_price_source,
    bravo_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test confirming new price feed before timelock expires"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)

    # Add new price feed
    undy_vault_prices.addNewPriceFeed(bravo_token_vault, 0, 5, 0, 20, sender=governance.address)

    # Try to confirm immediately - should fail
    with boa.reverts("time lock not reached"):
        undy_vault_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)


def test_confirm_new_price_feed_success(
    undy_vault_prices,
    governance,
    bravo_token_vault,
    mock_price_source,
    bravo_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test successful confirmation of new price feed"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)

    # Add new price feed
    undy_vault_prices.addNewPriceFeed(bravo_token_vault, 0, 5, 0, 20, sender=governance.address)

    # Time travel and confirm
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)

    # Check event immediately after transaction
    added_log = filter_logs(undy_vault_prices, "NewPriceConfigAdded")[0]
    assert added_log.asset == bravo_token_vault.address
    assert added_log.underlyingAsset == bravo_token.address

    # Check no longer pending
    assert not undy_vault_prices.hasPendingPriceFeedUpdate(bravo_token_vault)

    # Check has feed now
    assert undy_vault_prices.hasPriceFeed(bravo_token_vault)

    # Check config
    config = undy_vault_prices.priceConfigs(bravo_token_vault)
    assert config.underlyingAsset == bravo_token.address
    assert config.minSnapshotDelay == 0
    assert config.maxNumSnapshots == 5
    assert config.staleTime == 20
    assert config.nextIndex == 1  # snapshot taken during registration


#######################
# Update Price Config #
#######################


def test_update_price_config_success(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test successful price config update"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # First add a feed
    undy_vault_prices.addNewPriceFeed(alpha_token_vault, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    # Now update it
    assert undy_vault_prices.isValidUpdateConfig(alpha_token_vault, 15, 30)
    assert undy_vault_prices.updatePriceConfig(alpha_token_vault, 0, 15, 0, 30, sender=governance.address)

    # Check event immediately after transaction
    pending_log = filter_logs(undy_vault_prices, "PriceConfigUpdatePending")[0]
    assert pending_log.asset == alpha_token_vault.address
    assert pending_log.maxNumSnapshots == 15
    assert pending_log.staleTime == 30

    # Check pending state
    assert undy_vault_prices.hasPendingPriceFeedUpdate(alpha_token_vault)


def test_update_price_config_no_existing_feed(
    undy_vault_prices,
    governance,
    bravo_token_vault,
):
    """Test updating price config for non-existent feed"""
    # Should be invalid - no existing feed
    assert not undy_vault_prices.isValidUpdateConfig(bravo_token_vault, 15, 30)

    with boa.reverts("invalid config"):
        undy_vault_prices.updatePriceConfig(bravo_token_vault, 0, 15, 0, 30, sender=governance.address)


def test_confirm_price_feed_update_success(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test successful confirmation of price feed update"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # First add a feed
    undy_vault_prices.addNewPriceFeed(alpha_token_vault, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    # Update it
    undy_vault_prices.updatePriceConfig(alpha_token_vault, 0, 15, 0, 30, sender=governance.address)

    # Time travel and confirm
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmPriceFeedUpdate(alpha_token_vault, sender=governance.address)

    # Check event immediately after transaction
    updated_log = filter_logs(undy_vault_prices, "PriceConfigUpdated")[0]
    assert updated_log.asset == alpha_token_vault.address
    assert updated_log.maxNumSnapshots == 15
    assert updated_log.staleTime == 30

    # Check no longer pending
    assert not undy_vault_prices.hasPendingPriceFeedUpdate(alpha_token_vault)

    # Check updated config
    config = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert config.maxNumSnapshots == 15
    assert config.staleTime == 30


def test_cancel_price_feed_update(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test canceling pending price feed update"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # First add a feed
    undy_vault_prices.addNewPriceFeed(alpha_token_vault, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    # Update it
    undy_vault_prices.updatePriceConfig(alpha_token_vault, 0, 15, 0, 30, sender=governance.address)
    assert undy_vault_prices.hasPendingPriceFeedUpdate(alpha_token_vault)

    # Cancel
    assert undy_vault_prices.cancelPriceFeedUpdate(alpha_token_vault, sender=governance.address)

    # Check event immediately after transaction
    cancelled_log = filter_logs(undy_vault_prices, "PriceConfigUpdateCancelled")[0]
    assert cancelled_log.asset == alpha_token_vault.address
    assert cancelled_log.underlyingAsset == alpha_token.address

    # Check no longer pending
    assert not undy_vault_prices.hasPendingPriceFeedUpdate(alpha_token_vault)

    # Check config unchanged
    config = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert config.maxNumSnapshots == 10  # original values
    assert config.staleTime == 10


######################
# Disable Price Feed #
######################


def test_disable_price_feed_success(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test successful price feed disable initiation"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # First add a feed
    undy_vault_prices.addNewPriceFeed(alpha_token_vault, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    # Should be valid to disable
    assert undy_vault_prices.isValidDisablePriceFeed(alpha_token_vault)

    # Disable it
    assert undy_vault_prices.disablePriceFeed(alpha_token_vault, sender=governance.address)

    # Check pending state
    assert undy_vault_prices.hasPendingPriceFeedUpdate(alpha_token_vault)


def test_confirm_disable_price_feed_success(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test successful confirmation of price feed disable"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # First add a feed
    undy_vault_prices.addNewPriceFeed(alpha_token_vault, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    # Disable it
    undy_vault_prices.disablePriceFeed(alpha_token_vault, sender=governance.address)

    # Time travel and confirm
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmDisablePriceFeed(alpha_token_vault, sender=governance.address)

    # Check no longer pending
    assert not undy_vault_prices.hasPendingPriceFeedUpdate(alpha_token_vault)

    # Check no longer has feed
    assert not undy_vault_prices.hasPriceFeed(alpha_token_vault)

    # Check config is empty
    config = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert config.underlyingAsset == ZERO_ADDRESS
    assert config.maxNumSnapshots == 0
    assert config.staleTime == 0


def test_cancel_disable_price_feed(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test canceling pending price feed disable"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # First add a feed
    undy_vault_prices.addNewPriceFeed(alpha_token_vault, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    # Disable it
    undy_vault_prices.disablePriceFeed(alpha_token_vault, sender=governance.address)
    assert undy_vault_prices.hasPendingPriceFeedUpdate(alpha_token_vault)

    # Cancel
    assert undy_vault_prices.cancelDisablePriceFeed(alpha_token_vault, sender=governance.address)

    # Check no longer pending
    assert not undy_vault_prices.hasPendingPriceFeedUpdate(alpha_token_vault)

    # Check still has feed
    assert undy_vault_prices.hasPriceFeed(alpha_token_vault)

    # Check config unchanged
    config = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert config.underlyingAsset == alpha_token.address
    assert config.maxNumSnapshots == 10
    assert config.staleTime == 10


########################
# Validation Functions #
########################


def test_is_valid_new_feed_comprehensive(
    undy_vault_prices,
    governance,
    bravo_token_vault,
    charlie_token_vault,
    mock_price_source,
    bravo_token,
    charlie_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test comprehensive validation for new feeds"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 3 * EIGHTEEN_DECIMALS)

    # Valid cases
    assert undy_vault_prices.isValidNewFeed(bravo_token_vault, 0, 1, 0, 0)  # min snapshots
    assert undy_vault_prices.isValidNewFeed(bravo_token_vault, 0, 25, 0, 0)  # max snapshots
    assert undy_vault_prices.isValidNewFeed(bravo_token_vault, 0, 10, 0, 1000)  # with stale time
    assert undy_vault_prices.isValidNewFeed(charlie_token_vault, 0, 5, 0, 10)  # different token

    # Invalid cases
    assert not undy_vault_prices.isValidNewFeed(bravo_token_vault, 0, 0, 0, 10)  # 0 snapshots
    assert not undy_vault_prices.isValidNewFeed(bravo_token_vault, 0, 26, 0, 10)  # too many snapshots

    # Add a feed and check it's no longer valid to add again
    undy_vault_prices.addNewPriceFeed(bravo_token_vault, 0, 10, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)

    assert not undy_vault_prices.isValidNewFeed(bravo_token_vault, 0, 5, 0, 20)  # already exists


def test_vault_registry_validation(
    undy_vault_prices,
    bravo_token_vault,
    mock_price_source,
    bravo_token,
):
    """Test that validation checks vault registry"""
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)

    # Without setting underscore registry, validation should fail
    # (mission_control.underscoreRegistry() will return zero address)
    # This will cause the validation to fail when trying to check isEarnVault
    assert not undy_vault_prices.isValidNewFeed(bravo_token_vault, 0, 10, 0, 10)


def test_convertToAssets_validation(
    undy_vault_prices,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test that validation checks convertToAssets implementation"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # alpha_token_vault has convertToAssets implementation
    assert undy_vault_prices.isValidNewFeed(alpha_token_vault, 0, 10, 0, 10)

    # If we try with an address that doesn't have convertToAssets,
    # it should fail (but our mock vaults all have it, so this test verifies the happy path)


def test_snapshots_use_convertToAssets_not_convertToAssetsSafe(
    undy_vault_prices,
    governance,
    alpha_token_vault_with_safe_gap,
    alpha_token,
    alpha_token_whale,
    mock_price_source,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Regression: snapshots should use convertToAssets, not convertToAssetsSafe."""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Seed vault with shares at 1:1
    alpha_token.approve(alpha_token_vault_with_safe_gap, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault_with_safe_gap.deposit(100 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)

    # Register feed and create initial snapshot
    assert undy_vault_prices.isValidNewFeed(alpha_token_vault_with_safe_gap, 0, 5, 0, 100)
    undy_vault_prices.addNewPriceFeed(alpha_token_vault_with_safe_gap, 0, 5, 0, 100, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(alpha_token_vault_with_safe_gap, sender=governance.address)

    # Simulate yield accrual (pps doubles)
    alpha_token.transfer(alpha_token_vault_with_safe_gap, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    boa.env.time_travel(seconds=1)
    undy_vault_prices.addPriceSnapshot(alpha_token_vault_with_safe_gap, sender=teller.address)

    latest_snapshot = undy_vault_prices.getLatestSnapshot(alpha_token_vault_with_safe_gap)
    one_share = 10 ** alpha_token_vault_with_safe_gap.decimals()
    raw_pps = alpha_token_vault_with_safe_gap.convertToAssets(one_share)
    safe_pps = alpha_token_vault_with_safe_gap.convertToAssetsSafe(one_share)

    assert latest_snapshot.pricePerShare == raw_pps
    assert latest_snapshot.pricePerShare > safe_pps


def test_no_price_for_underlying_asset(
    undy_vault_prices,
    bravo_token_vault,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test that feeds are invalid when underlying asset has no price"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    # Don't set price for bravo_token
    assert not undy_vault_prices.isValidNewFeed(bravo_token_vault, 0, 10, 0, 10)


##################
# Snapshot Tests #
##################


def test_basic_snapshot_creation(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test basic snapshot creation and retrieval"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Add price feed
    undy_vault_prices.addNewPriceFeed(alpha_token_vault, 0, 3, 0, 100, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    # Initial snapshot should be created during registration
    config = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert config.nextIndex == 1

    # Get initial snapshot
    initial_snapshot = undy_vault_prices.getLatestSnapshot(alpha_token_vault)
    assert initial_snapshot.totalSupply == 0  # No deposits yet
    assert initial_snapshot.pricePerShare == 1 * EIGHTEEN_DECIMALS  # 1:1 ratio initially

    # Make a deposit to change total supply
    alpha_token.approve(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault.deposit(100 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)

    # Advance time to allow new snapshot
    boa.env.time_travel(seconds=1)

    # Add new snapshot
    result = undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    assert result  # Should succeed now

    # Check new snapshot
    new_snapshot = undy_vault_prices.getLatestSnapshot(alpha_token_vault)
    assert new_snapshot.totalSupply == 100  # 100 tokens deposited
    assert new_snapshot.pricePerShare == 1 * EIGHTEEN_DECIMALS  # Still 1:1 ratio

    # Verify nextIndex incremented
    config = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert config.nextIndex == 2


def test_weighted_price_calculation(
    undy_vault_prices,
    governance,
    bravo_token_vault,
    bravo_token_whale,
    mock_price_source,
    bravo_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test weighted price calculation with multiple snapshots"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)

    # Add price feed with small max snapshots for easier testing
    undy_vault_prices.addNewPriceFeed(bravo_token_vault, 0, 3, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)

    # Snapshot 1: 100 tokens at 1:1 ratio
    bravo_token.approve(bravo_token_vault, 100 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    bravo_token_vault.deposit(100 * EIGHTEEN_DECIMALS, bravo_token_whale, sender=bravo_token_whale)
    boa.env.time_travel(seconds=1)
    undy_vault_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    snapshot1 = undy_vault_prices.snapShots(bravo_token_vault, 1)

    # Snapshot 2: Transfer tokens to vault to change price per share
    bravo_token.transfer(bravo_token_vault, 100 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    boa.env.time_travel(seconds=7)
    undy_vault_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    snapshot2 = undy_vault_prices.snapShots(bravo_token_vault, 2)

    # Snapshot 3: Deposit more to change total supply
    bravo_token.approve(bravo_token_vault, 50 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    bravo_token_vault.deposit(50 * EIGHTEEN_DECIMALS, bravo_token_whale, sender=bravo_token_whale)
    boa.env.time_travel(seconds=11)
    undy_vault_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    snapshot3 = undy_vault_prices.snapShots(bravo_token_vault, 0)  # Wraps to index 0
    boa.env.time_travel(seconds=13)

    # Wrapped chronology is snapshot1 for 7s, snapshot2 for 11s, then
    # snapshot3 for 13s through the current timestamp.
    numerator = (
        snapshot1.pricePerShare * 7
        + snapshot2.pricePerShare * 11
        + snapshot3.pricePerShare * 13
    )
    denominator = 7 + 11 + 13
    expected_weighted_price = numerator // denominator

    weighted_price = undy_vault_prices.getWeightedPrice(bravo_token_vault)
    assert weighted_price == expected_weighted_price


def test_snapshot_rotation(
    undy_vault_prices,
    governance,
    charlie_token_vault,
    charlie_token_whale,
    mock_price_source,
    charlie_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test that snapshots rotate when maxNumSnapshots is reached"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(charlie_token, 3 * EIGHTEEN_DECIMALS)

    # Add price feed with maxNumSnapshots = 2
    undy_vault_prices.addNewPriceFeed(charlie_token_vault, 0, 2, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(charlie_token_vault, sender=governance.address)

    # Initial state: nextIndex should be 1
    config = undy_vault_prices.priceConfigs(charlie_token_vault)
    assert config.nextIndex == 1

    # Add first manual snapshot (index 1)
    charlie_token.approve(charlie_token_vault, 100 * (10 ** charlie_token.decimals()), sender=charlie_token_whale)
    charlie_token_vault.deposit(100 * (10 ** charlie_token.decimals()), charlie_token_whale, sender=charlie_token_whale)
    boa.env.time_travel(seconds=1)  # Advance time
    undy_vault_prices.addPriceSnapshot(charlie_token_vault, sender=teller.address)

    config = undy_vault_prices.priceConfigs(charlie_token_vault)
    assert config.nextIndex == 0  # Should wrap back to 0

    # Add second manual snapshot (index 0, overwriting the initial snapshot)
    charlie_token.transfer(charlie_token_vault, 50 * (10 ** charlie_token.decimals()), sender=charlie_token_whale)
    boa.env.time_travel(seconds=1)  # Advance time
    undy_vault_prices.addPriceSnapshot(charlie_token_vault, sender=teller.address)

    config = undy_vault_prices.priceConfigs(charlie_token_vault)
    assert config.nextIndex == 1  # Should be back to 1


def test_stale_snapshot_handling(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test that stale snapshots are ignored in weighted price calculation"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Add price feed with staleTime = 10 seconds
    undy_vault_prices.addNewPriceFeed(alpha_token_vault, 0, 5, 0, 10, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    # Create first snapshot
    alpha_token.approve(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault.deposit(100 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)
    undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)

    # Time travel to make the snapshot stale (> 10 seconds)
    boa.env.time_travel(seconds=15)

    # Create second snapshot
    alpha_token.transfer(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)

    # The weighted price should only consider the non-stale snapshot
    weighted_price = undy_vault_prices.getWeightedPrice(alpha_token_vault)
    latest_snapshot = undy_vault_prices.getLatestSnapshot(alpha_token_vault)

    # Should equal the latest snapshot's price since older ones are stale
    assert weighted_price == latest_snapshot.pricePerShare


def test_price_per_share_changes(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test comprehensive price per share changes and snapshot tracking"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Add price feed
    undy_vault_prices.addNewPriceFeed(alpha_token_vault, 0, 10, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    # Stage 1: Initial deposit (1:1 ratio)
    alpha_token.approve(alpha_token_vault, 2000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault.deposit(1000 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)
    boa.env.time_travel(seconds=1)
    undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)

    snapshot1 = undy_vault_prices.getLatestSnapshot(alpha_token_vault)
    assert snapshot1.totalSupply == 1000
    assert snapshot1.pricePerShare == 1 * EIGHTEEN_DECIMALS

    # Stage 2: Transfer tokens to vault (increases price per share)
    alpha_token.transfer(alpha_token_vault, 500 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    boa.env.time_travel(seconds=1)
    undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)

    snapshot2 = undy_vault_prices.getLatestSnapshot(alpha_token_vault)
    assert snapshot2.totalSupply == 1000  # Same shares
    assert snapshot2.pricePerShare == 1.5 * EIGHTEEN_DECIMALS


##############################
# Max Upside Deviation Tests #
##############################


def test_max_upside_deviation_validation(
    undy_vault_prices,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test validation of maxUpsideDeviation parameter"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Valid: 0% deviation (no limit)
    assert undy_vault_prices.isValidNewFeed(alpha_token_vault, 0, 5, 0, 10)

    # Valid: 50% deviation
    assert undy_vault_prices.isValidNewFeed(alpha_token_vault, 0, 5, 5000, 10)

    # Valid: 100% deviation
    assert undy_vault_prices.isValidNewFeed(alpha_token_vault, 0, 5, 10000, 10)

    # Invalid: >100% deviation
    assert not undy_vault_prices.isValidNewFeed(alpha_token_vault, 0, 5, 10001, 10)


def test_max_upside_deviation_throttling_basic(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test basic price throttling with maxUpsideDeviation"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Add feed with 10% max upside deviation
    undy_vault_prices.addNewPriceFeed(alpha_token_vault, 0, 5, 1000, 0, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    # Initial deposit to establish baseline
    alpha_token.approve(alpha_token_vault, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault.deposit(1000 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)
    undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)

    initial_snapshot = undy_vault_prices.getLatestSnapshot(alpha_token_vault)
    assert initial_snapshot.pricePerShare == 1 * EIGHTEEN_DECIMALS

    # Transfer a large amount to vault
    alpha_token.transfer(alpha_token_vault, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)

    # Price should be throttled to max 10% increase
    throttled_snapshot = undy_vault_prices.getLatestSnapshot(alpha_token_vault)
    expected_max_price = 1 * EIGHTEEN_DECIMALS + (1 * EIGHTEEN_DECIMALS * 1000 // 10000)
    assert throttled_snapshot.pricePerShare == expected_max_price


def test_max_upside_deviation_no_limit(
    undy_vault_prices,
    governance,
    bravo_token_vault,
    bravo_token_whale,
    mock_price_source,
    bravo_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test that 0 maxUpsideDeviation means no throttling"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)

    # Add feed with 0% max upside deviation (no limit)
    undy_vault_prices.addNewPriceFeed(bravo_token_vault, 0, 5, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)

    # Initial deposit
    bravo_token.approve(bravo_token_vault, 100 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    bravo_token_vault.deposit(100 * EIGHTEEN_DECIMALS, bravo_token_whale, sender=bravo_token_whale)
    undy_vault_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)

    # Transfer large amount (triple the price per share)
    bravo_token.transfer(bravo_token_vault, 200 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    undy_vault_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)

    # Price should not be throttled
    final_snapshot = undy_vault_prices.getLatestSnapshot(bravo_token_vault)
    assert final_snapshot.pricePerShare == 3 * EIGHTEEN_DECIMALS


############################
# Min Snapshot Delay Tests #
############################


def test_min_snapshot_delay_prevents_spam(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test that minSnapshotDelay prevents rapid snapshot creation"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Add feed with 10 second min delay
    undy_vault_prices.addNewPriceFeed(alpha_token_vault, 10, 5, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(alpha_token_vault, sender=governance.address)

    # Make a deposit to change state
    alpha_token.approve(alpha_token_vault, 100 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    alpha_token_vault.deposit(100 * EIGHTEEN_DECIMALS, alpha_token_whale, sender=alpha_token_whale)

    # Get initial nextIndex after registration snapshot
    config_before = undy_vault_prices.priceConfigs(alpha_token_vault)
    initial_next_index = config_before.nextIndex

    # Try to add snapshot immediately - should fail due to delay
    result1 = undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    assert not result1

    # nextIndex should not have changed
    config_after_fail = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert config_after_fail.nextIndex == initial_next_index

    # Wait 11 seconds - should work now
    boa.env.time_travel(seconds=11)
    result3 = undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    assert result3


def test_min_snapshot_delay_zero_means_no_delay(
    undy_vault_prices,
    governance,
    bravo_token_vault,
    bravo_token_whale,
    mock_price_source,
    bravo_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test that 0 minSnapshotDelay means no delay restriction"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)

    # Add feed with no min delay
    undy_vault_prices.addNewPriceFeed(bravo_token_vault, 0, 5, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)

    # Make a deposit
    bravo_token.approve(bravo_token_vault, 100 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    bravo_token_vault.deposit(100 * EIGHTEEN_DECIMALS, bravo_token_whale, sender=bravo_token_whale)

    # Advance time by 1 second to avoid duplicate timestamp check
    boa.env.time_travel(seconds=1)

    # Should be able to add snapshot immediately
    result = undy_vault_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    assert result


#######################
# Edge Cases & Errors #
#######################


def test_operations_when_paused(
    undy_vault_prices,
    governance,
    bravo_token_vault,
    mock_price_source,
    bravo_token,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
):
    """Test that operations fail when contract is paused"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)

    # Pause the contract
    undy_vault_prices.pause(True, sender=switchboard_alpha.address)

    # All operations should fail when paused
    with boa.reverts("contract paused"):
        undy_vault_prices.addNewPriceFeed(bravo_token_vault, 0, 10, 0, 10, sender=governance.address)

    with boa.reverts("contract paused"):
        undy_vault_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)

    with boa.reverts("contract paused"):
        undy_vault_prices.cancelNewPendingPriceFeed(bravo_token_vault, sender=governance.address)


def test_no_valid_snapshots_fallback(
    undy_vault_prices,
    governance,
    bravo_token_vault,
    mock_price_source,
    bravo_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test fallback to lastSnapshot when no valid snapshots exist"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)

    # Add price feed with very short stale time
    undy_vault_prices.addNewPriceFeed(bravo_token_vault, 0, 3, 0, 1, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    undy_vault_prices.confirmNewPriceFeed(bravo_token_vault, sender=governance.address)

    # Time travel to make all snapshots stale
    boa.env.time_travel(seconds=5)

    # Get weighted price - should fallback to lastSnapshot
    weighted_price = undy_vault_prices.getWeightedPrice(bravo_token_vault)
    config = undy_vault_prices.priceConfigs(bravo_token_vault)

    assert config.lastSnapshot.pricePerShare != 0
    assert weighted_price == 0


########################################
# Price-integrity remediation regressions
########################################


def _register_undy_integrity_feed(
    prices,
    governance,
    vault,
    min_delay=0,
    max_snapshots=5,
    max_upside=0,
    stale_time=0,
):
    assert prices.addNewPriceFeed(
        vault,
        min_delay,
        max_snapshots,
        max_upside,
        stale_time,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=prices.actionTimeLock() + 1)
    assert prices.confirmNewPriceFeed(vault, sender=governance.address)


def _undy_config_state(config):
    snapshot = config.lastSnapshot
    return (
        config.underlyingAsset,
        config.underlyingDecimals,
        config.vaultTokenDecimals,
        config.minSnapshotDelay,
        config.maxNumSnapshots,
        config.maxUpsideDeviation,
        config.staleTime,
        snapshot.totalSupply,
        snapshot.pricePerShare,
        snapshot.lastUpdate,
        config.nextIndex,
    )


def _deposit_undy(vault, token, whale, amount):
    token.approve(vault, amount, sender=whale)
    vault.deposit(amount, whale, sender=whale)


def test_undy_update_confirmation_preserves_live_cursor_and_throttle_baseline(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_upside=1_000,
    )
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        1_000 * EIGHTEEN_DECIMALS,
    )
    boa.env.time_travel(seconds=1)
    assert undy_vault_prices.addPriceSnapshot(
        alpha_token_vault,
        sender=teller.address,
    )
    baseline = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert baseline.lastSnapshot.pricePerShare == EIGHTEEN_DECIMALS
    assert baseline.nextIndex == 2
    assert undy_vault_prices.updatePriceConfig(
        alpha_token_vault,
        0,
        5,
        1_000,
        77,
        sender=governance.address,
    )
    pending = undy_vault_prices.pendingPriceConfigs(alpha_token_vault).config
    assert pending.lastSnapshot.pricePerShare == EIGHTEEN_DECIMALS
    assert pending.nextIndex == 2

    alpha_token.burn(500 * EIGHTEEN_DECIMALS, sender=alpha_token_vault.address)
    boa.env.time_travel(seconds=1)
    assert undy_vault_prices.addPriceSnapshot(
        alpha_token_vault,
        sender=teller.address,
    )
    assert (
        undy_vault_prices.priceConfigs(alpha_token_vault).lastSnapshot.pricePerShare
        == EIGHTEEN_DECIMALS // 2
    )
    alpha_token.transfer(
        alpha_token_vault,
        300 * EIGHTEEN_DECIMALS,
        sender=alpha_token_whale,
    )
    boa.env.time_travel(seconds=1)
    assert undy_vault_prices.addPriceSnapshot(
        alpha_token_vault,
        sender=teller.address,
    )
    before = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert before.lastSnapshot.pricePerShare == 55 * 10**16
    assert before.nextIndex == 4

    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmPriceFeedUpdate(
        alpha_token_vault,
        sender=governance.address,
    )
    after = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert after.lastSnapshot.pricePerShare == before.lastSnapshot.pricePerShare
    assert after.nextIndex == before.nextIndex
    assert after.staleTime == 77
    assert after.underlyingAsset == before.underlyingAsset
    assert after.underlyingDecimals == before.underlyingDecimals
    assert after.vaultTokenDecimals == before.vaultTokenDecimals
    assert undy_vault_prices.snapShots(alpha_token_vault, 4).lastUpdate == 0
    assert not undy_vault_prices.hasPendingPriceFeedUpdate(alpha_token_vault)


def test_undy_unchanged_capacity_confirmation_revalidates_live_pps(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_snapshots=5,
    )
    before = _undy_config_state(undy_vault_prices.priceConfigs(alpha_token_vault))
    assert undy_vault_prices.updatePriceConfig(
        alpha_token_vault, 0, 5, 0, 99, sender=governance.address
    )
    alpha_token.eval(f"self.balanceOf[{alpha_token_vault.address}] = 0")
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)

    # Unchanged-capacity updates retain the pre-remediation confirm-time
    # revalidation and cancellation behavior. Resize seed failures instead
    # revert atomically, as covered separately.
    assert not undy_vault_prices.confirmPriceFeedUpdate(
        alpha_token_vault,
        sender=governance.address,
    )
    assert _undy_config_state(
        undy_vault_prices.priceConfigs(alpha_token_vault)
    ) == before
    assert not undy_vault_prices.hasPendingPriceFeedUpdate(alpha_token_vault)


def test_undy_cancel_update_leaves_advanced_live_cursor_unchanged(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
    )
    assert undy_vault_prices.updatePriceConfig(
        alpha_token_vault, 0, 7, 500, 99, sender=governance.address
    )
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    boa.env.time_travel(seconds=1)
    assert undy_vault_prices.addPriceSnapshot(
        alpha_token_vault,
        sender=teller.address,
    )
    before = _undy_config_state(undy_vault_prices.priceConfigs(alpha_token_vault))
    assert undy_vault_prices.cancelPriceFeedUpdate(
        alpha_token_vault,
        sender=governance.address,
    )
    assert _undy_config_state(
        undy_vault_prices.priceConfigs(alpha_token_vault)
    ) == before
    assert not undy_vault_prices.hasPendingPriceFeedUpdate(alpha_token_vault)


def test_undy_update_confirmation_cursor_edge_cases(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Zero and one intervening snapshots retain normal cursor progression."""
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
    )
    initial = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert initial.nextIndex == 1
    assert undy_vault_prices.updatePriceConfig(
        alpha_token_vault, 0, 7, 500, 99, sender=governance.address
    )
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmPriceFeedUpdate(
        alpha_token_vault,
        sender=governance.address,
    )
    no_intervening = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert no_intervening.nextIndex == 1
    assert no_intervening.lastSnapshot.pricePerShare == initial.lastSnapshot.pricePerShare
    assert no_intervening.maxNumSnapshots == 7
    assert no_intervening.maxUpsideDeviation == 500
    assert no_intervening.staleTime == 99

    assert undy_vault_prices.updatePriceConfig(
        alpha_token_vault, 0, 7, 500, 100, sender=governance.address
    )
    pending = undy_vault_prices.pendingPriceConfigs(alpha_token_vault).config
    assert pending.nextIndex == 1
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    boa.env.time_travel(seconds=1)
    assert undy_vault_prices.addPriceSnapshot(
        alpha_token_vault,
        sender=teller.address,
    )
    before = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert before.nextIndex == 2
    assert before.lastSnapshot.totalSupply == 100
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmPriceFeedUpdate(
        alpha_token_vault,
        sender=governance.address,
    )
    after = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert after.nextIndex == before.nextIndex
    assert after.lastSnapshot.totalSupply == before.lastSnapshot.totalSupply
    assert undy_vault_prices.snapShots(alpha_token_vault, before.nextIndex).lastUpdate == 0
    assert not undy_vault_prices.hasPendingPriceFeedUpdate(alpha_token_vault)


def test_undy_update_confirmation_timelock_revert_is_atomic(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
    )
    before = _undy_config_state(undy_vault_prices.priceConfigs(alpha_token_vault))
    assert undy_vault_prices.updatePriceConfig(
        alpha_token_vault, 0, 7, 500, 99, sender=governance.address
    )
    with boa.reverts("time lock not reached"):
        undy_vault_prices.confirmPriceFeedUpdate(
            alpha_token_vault,
            sender=governance.address,
        )
    assert _undy_config_state(
        undy_vault_prices.priceConfigs(alpha_token_vault)
    ) == before
    assert undy_vault_prices.hasPendingPriceFeedUpdate(alpha_token_vault)


def test_undy_update_confirmation_normalizes_widest_valid_ring_shrink(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_snapshots=25,
    )
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    for _ in range(3):
        boa.env.time_travel(seconds=1)
        assert undy_vault_prices.addPriceSnapshot(
            alpha_token_vault,
            sender=teller.address,
        )
    assert undy_vault_prices.priceConfigs(alpha_token_vault).nextIndex == 4
    assert undy_vault_prices.updatePriceConfig(
        alpha_token_vault, 0, 1, 0, 0, sender=governance.address
    )
    boa.env.time_travel(seconds=1)
    assert undy_vault_prices.addPriceSnapshot(
        alpha_token_vault,
        sender=teller.address,
    )
    old_live_next_index = undy_vault_prices.priceConfigs(alpha_token_vault).nextIndex
    assert old_live_next_index == 5
    previous_zero = undy_vault_prices.snapShots(alpha_token_vault, 0)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmPriceFeedUpdate(
        alpha_token_vault,
        sender=governance.address,
    )
    after = undy_vault_prices.priceConfigs(alpha_token_vault)
    at_zero = undy_vault_prices.snapShots(alpha_token_vault, 0)
    assert after.maxNumSnapshots == 1
    assert after.nextIndex == old_live_next_index % after.maxNumSnapshots
    assert at_zero.lastUpdate > previous_zero.lastUpdate
    assert at_zero.lastUpdate == after.lastSnapshot.lastUpdate


def test_undy_successful_zero_live_pps_fails_closed(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
    )
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) > 0
    assert undy_vault_prices.getPrice(alpha_token_vault) == EIGHTEEN_DECIMALS
    alpha_token.eval(f"self.balanceOf[{alpha_token_vault.address}] = 0")
    assert alpha_token_vault.convertToAssets(EIGHTEEN_DECIMALS) == 0
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) > 0
    assert undy_vault_prices.getPrice(alpha_token_vault) == 0


def test_undy_positive_live_pps_keeps_existing_min_policy(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
    )
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == EIGHTEEN_DECIMALS
    alpha_token.burn(50 * EIGHTEEN_DECIMALS, sender=alpha_token_vault.address)
    assert undy_vault_prices.getPrice(alpha_token_vault) == 5 * 10**17
    alpha_token.transfer(
        alpha_token_vault,
        150 * EIGHTEEN_DECIMALS,
        sender=alpha_token_whale,
    )
    assert undy_vault_prices.getPrice(alpha_token_vault) == EIGHTEEN_DECIMALS


def test_undy_typed_live_pps_revert_is_not_suppressed(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
    )
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) > 0
    supply = alpha_token_vault.totalSupply()
    alpha_token_vault.setShouldRevertConvertToAssets(True)
    assert alpha_token_vault.totalSupply() == supply
    with boa.reverts():
        alpha_token_vault.convertToAssets(EIGHTEEN_DECIMALS)
    with boa.reverts():
        undy_vault_prices.getPrice(alpha_token_vault)


##########################################
# SC-05 / SC-17 / SC-23 fail-first cases #
##########################################


def test_undy_sc05_resize_clears_all_25_snapshot_slots(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_snapshots=25,
    )
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    for _ in range(24):
        boa.env.time_travel(seconds=1)
        assert undy_vault_prices.addPriceSnapshot(
            alpha_token_vault,
            sender=teller.address,
        )

    assert all(
        undy_vault_prices.snapShots(alpha_token_vault, index).lastUpdate != 0
        for index in range(25)
    )
    assert undy_vault_prices.updatePriceConfig(
        alpha_token_vault,
        0,
        1,
        0,
        0,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmPriceFeedUpdate(
        alpha_token_vault,
        sender=governance.address,
    )

    config = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert config.nextIndex == 0
    assert config.lastSnapshot.pricePerShare == EIGHTEEN_DECIMALS
    assert undy_vault_prices.snapShots(alpha_token_vault, 0).lastUpdate == (
        config.lastSnapshot.lastUpdate
    )
    assert all(
        undy_vault_prices.snapShots(alpha_token_vault, index).lastUpdate == 0
        for index in range(1, 25)
    )
    # In the confirmation block the seed has zero elapsed duration, so this
    # immediate result uses the fresh lastSnapshot fallback, not the TWAP ring.
    assert undy_vault_prices.getPrice(alpha_token_vault) == EIGHTEEN_DECIMALS


def test_undy_sc17_duration_weighting_uses_irregular_wrapped_intervals_not_supply(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_snapshots=3,
    )
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )

    boa.env.time_travel(seconds=1)
    assert undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    boa.env.time_travel(seconds=7)
    alpha_token.transfer(
        alpha_token_vault,
        100 * EIGHTEEN_DECIMALS,
        sender=alpha_token_whale,
    )
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        1_000 * EIGHTEEN_DECIMALS,
    )
    assert undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    boa.env.time_travel(seconds=11)
    alpha_token.burn(600 * EIGHTEEN_DECIMALS, sender=alpha_token_vault.address)
    assert undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    boa.env.time_travel(seconds=13)

    # Chronological wrapped observations are 1x for 7s, 2x for 11s, and 1x
    # for 13s. Their supplies are 100, 600, and 600, deliberately unequal.
    expected = (
        EIGHTEEN_DECIMALS * 7
        + 2 * EIGHTEEN_DECIMALS * 11
        + EIGHTEEN_DECIMALS * 13
    ) // (7 + 11 + 13)
    assert expected != 4 * EIGHTEEN_DECIMALS // 3
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == expected


def test_undy_sc23_last_snapshot_fallback_expires_after_inclusive_boundary(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_snapshots=3,
        stale_time=5,
    )
    # The empty vault makes the ring observation ineligible by supply, forcing
    # the lastSnapshot fallback while its nonzero PPS remains fresh.
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == EIGHTEEN_DECIMALS
    boa.env.time_travel(seconds=5)
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == EIGHTEEN_DECIMALS
    boa.env.time_travel(seconds=1)
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == 0


def _undy_ring_state(prices, vault):
    return tuple(
        (
            snapshot.totalSupply,
            snapshot.pricePerShare,
            snapshot.lastUpdate,
        )
        for snapshot in (prices.snapShots(vault, index) for index in range(25))
    )


def test_undy_sc05_shrink_write_regrow_same_block_seed_never_resurrects_history(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_snapshots=4,
    )
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    for _ in range(4):
        boa.env.time_travel(seconds=1)
        alpha_token.transfer(
            alpha_token_vault,
            10 * EIGHTEEN_DECIMALS,
            sender=alpha_token_whale,
        )
        assert undy_vault_prices.addPriceSnapshot(
            alpha_token_vault,
            sender=teller.address,
        )
    discarded_updates = {
        undy_vault_prices.snapShots(alpha_token_vault, index).lastUpdate
        for index in range(4)
    }
    assert len(discarded_updates) == 4

    assert undy_vault_prices.updatePriceConfig(
        alpha_token_vault, 0, 1, 0, 0, sender=governance.address
    )
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    alpha_token.transfer(
        alpha_token_vault,
        10 * EIGHTEEN_DECIMALS,
        sender=alpha_token_whale,
    )
    assert undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    ordinary_same_block = undy_vault_prices.priceConfigs(
        alpha_token_vault
    ).lastSnapshot
    assert undy_vault_prices.confirmPriceFeedUpdate(
        alpha_token_vault,
        sender=governance.address,
    )
    assert len(filter_logs(undy_vault_prices, "PricePerShareSnapshotAdded")) == 1
    seeded = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert seeded.nextIndex == 0
    assert seeded.lastSnapshot.lastUpdate == ordinary_same_block.lastUpdate
    assert all(
        undy_vault_prices.snapShots(alpha_token_vault, index).lastUpdate == 0
        for index in range(1, 25)
    )

    boa.env.time_travel(seconds=1)
    alpha_token.transfer(
        alpha_token_vault,
        10 * EIGHTEEN_DECIMALS,
        sender=alpha_token_whale,
    )
    assert undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    assert undy_vault_prices.priceConfigs(alpha_token_vault).nextIndex == 0

    assert undy_vault_prices.updatePriceConfig(
        alpha_token_vault, 0, 4, 0, 0, sender=governance.address
    )
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmPriceFeedUpdate(
        alpha_token_vault,
        sender=governance.address,
    )
    regrown = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert regrown.nextIndex == 1
    assert all(
        undy_vault_prices.snapShots(alpha_token_vault, index).lastUpdate == 0
        for index in range(1, 25)
    )
    assert discarded_updates.isdisjoint(
        {
            undy_vault_prices.snapShots(alpha_token_vault, index).lastUpdate
            for index in range(25)
            if undy_vault_prices.snapShots(alpha_token_vault, index).lastUpdate != 0
        }
    )
    # The confirmation-block price uses the fresh fallback because the seed's
    # elapsed duration is zero; it is not a TWAP-ring assertion.
    assert undy_vault_prices.getPrice(alpha_token_vault) == regrown.lastSnapshot.pricePerShare

    seed = regrown.lastSnapshot
    boa.env.time_travel(seconds=7)
    alpha_token.transfer(
        alpha_token_vault,
        10 * EIGHTEEN_DECIMALS,
        sender=alpha_token_whale,
    )
    assert undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    latest = undy_vault_prices.priceConfigs(alpha_token_vault).lastSnapshot
    boa.env.time_travel(seconds=11)
    expected = (seed.pricePerShare * 7 + latest.pricePerShare * 11) // 18
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == expected
    assert undy_vault_prices.getPrice(alpha_token_vault) == expected


def test_undy_sc05_resize_zero_seed_reverts_all_state_including_timelock(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_snapshots=3,
    )
    assert undy_vault_prices.updatePriceConfig(
        alpha_token_vault, 0, 5, 0, 0, sender=governance.address
    )
    config_before = _undy_config_state(
        undy_vault_prices.priceConfigs(alpha_token_vault)
    )
    ring_before = _undy_ring_state(undy_vault_prices, alpha_token_vault)
    pending_before = undy_vault_prices.pendingPriceConfigs(alpha_token_vault)
    confirmation_before = undy_vault_prices.getActionConfirmationBlock(
        pending_before.actionId
    )
    alpha_token.eval(f"self.balanceOf[{alpha_token_vault.address}] = 0")
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    with boa.reverts("invalid snapshot"):
        undy_vault_prices.confirmPriceFeedUpdate(
            alpha_token_vault,
            sender=governance.address,
        )
    assert _undy_config_state(
        undy_vault_prices.priceConfigs(alpha_token_vault)
    ) == config_before
    assert _undy_ring_state(undy_vault_prices, alpha_token_vault) == ring_before
    pending_after = undy_vault_prices.pendingPriceConfigs(alpha_token_vault)
    assert pending_after.actionId == pending_before.actionId
    assert undy_vault_prices.getActionConfirmationBlock(pending_after.actionId) == (
        confirmation_before
    )
    assert undy_vault_prices.hasPendingPriceFeedUpdate(alpha_token_vault)


def test_undy_sc05_new_feed_zero_seed_is_not_registered_and_pending_is_preserved(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    assert undy_vault_prices.addNewPriceFeed(
        alpha_token_vault, 0, 3, 0, 0, sender=governance.address
    )
    pending = undy_vault_prices.pendingPriceConfigs(alpha_token_vault)
    alpha_token.eval(f"self.balanceOf[{alpha_token_vault.address}] = 0")
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    with boa.reverts("invalid snapshot"):
        undy_vault_prices.confirmNewPriceFeed(
            alpha_token_vault,
            sender=governance.address,
        )
    assert not undy_vault_prices.hasPriceFeed(alpha_token_vault)
    assert undy_vault_prices.pendingPriceConfigs(alpha_token_vault).actionId == (
        pending.actionId
    )
    assert undy_vault_prices.hasPendingPriceFeedUpdate(alpha_token_vault)
    assert _undy_ring_state(undy_vault_prices, alpha_token_vault) == ((0, 0, 0),) * 25


def test_undy_sc05_disable_and_reregister_cannot_reuse_prior_observations(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_snapshots=3,
    )
    for _ in range(2):
        boa.env.time_travel(seconds=1)
        assert undy_vault_prices.addPriceSnapshot(
            alpha_token_vault,
            sender=teller.address,
        )
    prior_updates = {
        undy_vault_prices.snapShots(alpha_token_vault, index).lastUpdate
        for index in range(3)
    }
    assert undy_vault_prices.disablePriceFeed(
        alpha_token_vault,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmDisablePriceFeed(
        alpha_token_vault,
        sender=governance.address,
    )
    assert any(value != (0, 0, 0) for value in _undy_ring_state(undy_vault_prices, alpha_token_vault))
    assert undy_vault_prices.addNewPriceFeed(
        alpha_token_vault, 0, 3, 0, 0, sender=governance.address
    )
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmNewPriceFeed(
        alpha_token_vault,
        sender=governance.address,
    )
    config = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert config.nextIndex == 1
    assert all(
        undy_vault_prices.snapShots(alpha_token_vault, index).lastUpdate == 0
        for index in range(1, 25)
    )
    assert config.lastSnapshot.lastUpdate not in prior_updates


def test_undy_sc17_zero_pps_snapshot_does_not_mutate_and_next_positive_is_throttled(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_snapshots=3,
        max_upside=1_000,
    )
    before = _undy_config_state(undy_vault_prices.priceConfigs(alpha_token_vault))
    ring_before = _undy_ring_state(undy_vault_prices, alpha_token_vault)
    alpha_token.eval(f"self.balanceOf[{alpha_token_vault.address}] = 0")
    boa.env.time_travel(seconds=1)
    assert not undy_vault_prices.addPriceSnapshot(
        alpha_token_vault,
        sender=teller.address,
    )
    assert filter_logs(undy_vault_prices, "PricePerShareSnapshotAdded") == []
    assert _undy_config_state(
        undy_vault_prices.priceConfigs(alpha_token_vault)
    ) == before
    assert _undy_ring_state(undy_vault_prices, alpha_token_vault) == ring_before
    alpha_token.eval(
        f"self.balanceOf[{alpha_token_vault.address}] = {200 * EIGHTEEN_DECIMALS}"
    )
    boa.env.time_travel(seconds=1)
    assert undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    assert undy_vault_prices.priceConfigs(alpha_token_vault).lastSnapshot.pricePerShare == (
        11 * EIGHTEEN_DECIMALS // 10
    )


def test_undy_sc17_resize_seed_clamps_then_twap_ratchets_toward_live_pps(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_snapshots=3,
        max_upside=1_000,
    )
    assert undy_vault_prices.updatePriceConfig(
        alpha_token_vault, 0, 4, 1_000, 0, sender=governance.address
    )
    alpha_token.eval(
        f"self.balanceOf[{alpha_token_vault.address}] = {200 * EIGHTEEN_DECIMALS}"
    )
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmPriceFeedUpdate(
        alpha_token_vault,
        sender=governance.address,
    )
    seed = undy_vault_prices.priceConfigs(alpha_token_vault).lastSnapshot
    assert seed.pricePerShare == 11 * EIGHTEEN_DECIMALS // 10
    assert undy_vault_prices.getPrice(alpha_token_vault) == seed.pricePerShare
    boa.env.time_travel(seconds=7)
    assert undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    second = undy_vault_prices.priceConfigs(alpha_token_vault).lastSnapshot
    assert second.pricePerShare == 121 * EIGHTEEN_DECIMALS // 100
    boa.env.time_travel(seconds=11)
    expected_second = (seed.pricePerShare * 7 + second.pricePerShare * 11) // 18
    assert undy_vault_prices.getPrice(alpha_token_vault) == expected_second
    assert undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    third = undy_vault_prices.priceConfigs(alpha_token_vault).lastSnapshot
    assert third.pricePerShare == 1331 * EIGHTEEN_DECIMALS // 1000
    boa.env.time_travel(seconds=13)
    expected_third = (
        seed.pricePerShare * 7
        + second.pricePerShare * 11
        + third.pricePerShare * 13
    ) // 31
    assert undy_vault_prices.getPrice(alpha_token_vault) == expected_third


def test_undy_sc17_timing_manipulation_and_supply_inflation_controls(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    assert undy_vault_prices.addNewPriceFeed(
        alpha_token_vault, 10, 5, 0, 100, sender=governance.address
    )
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmNewPriceFeed(
        alpha_token_vault,
        sender=governance.address,
    )

    with boa.env.anchor():
        boa.env.time_travel(seconds=10)
        alpha_token.eval(
            f"self.balanceOf[{alpha_token_vault.address}] = {200 * EIGHTEEN_DECIMALS}"
        )
        assert undy_vault_prices.addPriceSnapshot(
            alpha_token_vault,
            sender=teller.address,
        )
        alpha_token.eval(
            f"self.balanceOf[{alpha_token_vault.address}] = {100 * EIGHTEEN_DECIMALS}"
        )
        boa.env.time_travel(seconds=30)
        assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == (
            EIGHTEEN_DECIMALS * 10 + 2 * EIGHTEEN_DECIMALS * 30
        ) // 40
        assert undy_vault_prices.getPrice(alpha_token_vault) == EIGHTEEN_DECIMALS

    with boa.env.anchor():
        boa.env.time_travel(seconds=10)
        alpha_token.eval(
            f"self.balanceOf[{alpha_token_vault.address}] = {50 * EIGHTEEN_DECIMALS}"
        )
        assert undy_vault_prices.addPriceSnapshot(
            alpha_token_vault,
            sender=teller.address,
        )
        alpha_token.eval(
            f"self.balanceOf[{alpha_token_vault.address}] = {100 * EIGHTEEN_DECIMALS}"
        )
        boa.env.time_travel(seconds=30)
        manipulated = (
            EIGHTEEN_DECIMALS * 10 + (EIGHTEEN_DECIMALS // 2) * 30
        ) // 40
        # A depressed price is conservative for the oracle but can still be
        # economically value-extracting through liquidations until an honest
        # refresh dilutes it or the configured freshness window expires.
        assert undy_vault_prices.getPrice(alpha_token_vault) == manipulated
        assert undy_vault_prices.addPriceSnapshot(
            alpha_token_vault,
            sender=teller.address,
        )
        boa.env.time_travel(seconds=20)
        refreshed = (
            EIGHTEEN_DECIMALS * 10
            + (EIGHTEEN_DECIMALS // 2) * 30
            + EIGHTEEN_DECIMALS * 20
        ) // 60
        assert undy_vault_prices.getPrice(alpha_token_vault) == refreshed
        boa.env.time_travel(seconds=101)
        assert undy_vault_prices.getPrice(alpha_token_vault) == 0

    results = []
    for inflate_supply in (False, True):
        with boa.env.anchor():
            boa.env.time_travel(seconds=10)
            alpha_token.eval(
                f"self.balanceOf[{alpha_token_vault.address}] = {200 * EIGHTEEN_DECIMALS}"
            )
            if inflate_supply:
                _deposit_undy(
                    alpha_token_vault,
                    alpha_token,
                    alpha_token_whale,
                    1_000 * EIGHTEEN_DECIMALS,
                )
            assert undy_vault_prices.addPriceSnapshot(
                alpha_token_vault,
                sender=teller.address,
            )
            boa.env.time_travel(seconds=11)
            supply = alpha_token_vault.totalSupply()
            alpha_token.eval(
                f"self.balanceOf[{alpha_token_vault.address}] = {supply}"
            )
            assert undy_vault_prices.addPriceSnapshot(
                alpha_token_vault,
                sender=teller.address,
            )
            boa.env.time_travel(seconds=13)
            results.append(undy_vault_prices.getWeightedPrice(alpha_token_vault))
    expected = (
        EIGHTEEN_DECIMALS * 10
        + 2 * EIGHTEEN_DECIMALS * 11
        + EIGHTEEN_DECIMALS * 13
    ) // 34
    assert results == [expected, expected]


def test_undy_ordinary_user_teller_deposit_can_time_downward_snapshot(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    mock_price_source,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
    simple_erc20_vault,
    teller,
):
    """Exercise the production Teller -> PriceDesk -> Undy snapshot path."""
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    setGeneralConfig()
    setAssetConfig(alpha_token_vault)

    amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, amount, sender=alpha_token_whale)
    alpha_token.approve(alpha_token_vault, amount, sender=bob)
    assert alpha_token_vault.deposit(amount, bob, sender=bob) == amount
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        min_delay=10,
        max_snapshots=5,
        stale_time=100,
    )
    seed = undy_vault_prices.priceConfigs(alpha_token_vault).lastSnapshot

    boa.env.time_travel(seconds=10)
    alpha_token.eval(
        f"self.balanceOf[{alpha_token_vault.address}] = {50 * EIGHTEEN_DECIMALS}"
    )
    share_amount = EIGHTEEN_DECIMALS
    alpha_token_vault.approve(teller, share_amount, sender=bob)
    assert teller.deposit(
        alpha_token_vault,
        share_amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    ) == share_amount

    manipulated = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert manipulated.nextIndex == 2
    assert manipulated.lastSnapshot.lastUpdate == boa.env.evm.patch.timestamp
    assert manipulated.lastSnapshot.pricePerShare == EIGHTEEN_DECIMALS // 2

    alpha_token.eval(
        f"self.balanceOf[{alpha_token_vault.address}] = {100 * EIGHTEEN_DECIMALS}"
    )
    boa.env.time_travel(seconds=30)
    expected = (
        seed.pricePerShare * 10
        + (EIGHTEEN_DECIMALS // 2) * 30
    ) // 40
    assert undy_vault_prices.getPrice(alpha_token_vault) == expected


def test_undy_delay_freshness_boundary_and_zero_stale_policy(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token,
    bravo_token_vault,
    bravo_token,
    charlie_token_vault,
    charlie_token,
    mock_price_source,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
    teller,
):
    """The overlap predicate avoids a stale-and-snapshot-ineligible interval."""
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    assert undy_vault_prices.isValidNewFeed(alpha_token_vault, 10, 3, 0, 10)
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        min_delay=10,
        max_snapshots=3,
        stale_time=10,
    )
    boa.env.time_travel(seconds=10)
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == EIGHTEEN_DECIMALS
    assert undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == EIGHTEEN_DECIMALS

    mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        bravo_token_vault,
        min_delay=10,
        max_snapshots=3,
        stale_time=8,
    )
    boa.env.time_travel(seconds=8)
    assert undy_vault_prices.getWeightedPrice(bravo_token_vault) == EIGHTEEN_DECIMALS
    boa.env.time_travel(seconds=1)
    assert undy_vault_prices.getWeightedPrice(bravo_token_vault) == 0
    assert not undy_vault_prices.addPriceSnapshot(
        bravo_token_vault,
        sender=teller.address,
    )
    boa.env.time_travel(seconds=1)
    assert undy_vault_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    assert undy_vault_prices.getWeightedPrice(bravo_token_vault) == EIGHTEEN_DECIMALS

    mock_price_source.setPrice(charlie_token, 3 * EIGHTEEN_DECIMALS)
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        charlie_token_vault,
        min_delay=10,
        max_snapshots=3,
        stale_time=0,
    )
    charlie_pps = undy_vault_prices.priceConfigs(
        charlie_token_vault
    ).lastSnapshot.pricePerShare
    boa.env.time_travel(seconds=10**7)
    assert charlie_pps != 0
    assert undy_vault_prices.getWeightedPrice(charlie_token_vault) == charlie_pps


def test_undy_zero_supply_bootstrap_hands_off_to_eligible_ring_observation(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token,
    alpha_token_whale,
    mock_price_source,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
    teller,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_snapshots=3,
    )
    initial = undy_vault_prices.priceConfigs(alpha_token_vault)
    assert initial.lastSnapshot.totalSupply == 0
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == EIGHTEEN_DECIMALS

    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    alpha_token.eval(
        f"self.balanceOf[{alpha_token_vault.address}] = {80 * EIGHTEEN_DECIMALS}"
    )
    boa.env.time_travel(seconds=1)
    assert undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    first_eligible = undy_vault_prices.priceConfigs(alpha_token_vault).lastSnapshot
    # Snapshot supply is normalized by the vault-token decimal scale.
    assert first_eligible.totalSupply == 100
    assert first_eligible.pricePerShare == 8 * EIGHTEEN_DECIMALS // 10
    assert (
        undy_vault_prices.getWeightedPrice(alpha_token_vault)
        == first_eligible.pricePerShare
    )
    boa.env.time_travel(seconds=7)
    alpha_token.eval(
        f"self.balanceOf[{alpha_token_vault.address}] = {60 * EIGHTEEN_DECIMALS}"
    )
    assert undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    second_eligible = undy_vault_prices.priceConfigs(alpha_token_vault).lastSnapshot
    assert second_eligible.totalSupply == 100
    assert second_eligible.pricePerShare == 6 * EIGHTEEN_DECIMALS // 10

    boa.env.time_travel(seconds=11)
    # Bootstrap 1e18 is supply-ineligible. The nonzero-supply ring computes
    # (0.8e18 * 7 + 0.6e18 * 11) / 18, not the 0.6e18 fallback.
    expected = (
        first_eligible.pricePerShare * 7
        + second_eligible.pricePerShare * 11
    ) // 18
    assert expected != second_eligible.pricePerShare
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == expected


def test_undy_sub_one_share_supply_uses_fresh_fallback_and_one_share_enters_ring(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token,
    mock_price_source,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    scale = EIGHTEEN_DECIMALS
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    with boa.env.anchor():
        alpha_token_vault.eval(f"self.totalSupply = {scale - 1}")
        alpha_token.eval(
            f"self.balanceOf[{alpha_token_vault.address}] = {2 * scale}"
        )
        _register_undy_integrity_feed(
            undy_vault_prices,
            governance,
            alpha_token_vault,
            max_snapshots=3,
            stale_time=5,
        )
        latest = undy_vault_prices.priceConfigs(alpha_token_vault).lastSnapshot
        expected_fallback = 2 * scale * scale // (scale - 1)
        assert latest.totalSupply == 0
        assert latest.pricePerShare == expected_fallback
        assert undy_vault_prices.snapShots(
            alpha_token_vault, 0
        ).totalSupply == 0
        # The normalized-zero observation is ring-ineligible, so its nonzero
        # PPS is available only through the fresh lastSnapshot fallback.
        assert (
            undy_vault_prices.getWeightedPrice(alpha_token_vault)
            == expected_fallback
        )
        assert undy_vault_prices.getPrice(alpha_token_vault) == expected_fallback
        boa.env.time_travel(seconds=5)
        assert (
            undy_vault_prices.getWeightedPrice(alpha_token_vault)
            == expected_fallback
        )
        boa.env.time_travel(seconds=1)
        assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == 0
        assert undy_vault_prices.getPrice(alpha_token_vault) == 0

    with boa.env.anchor():
        alpha_token_vault.eval(f"self.totalSupply = {scale}")
        alpha_token.eval(f"self.balanceOf[{alpha_token_vault.address}] = {scale}")
        _register_undy_integrity_feed(
            undy_vault_prices,
            governance,
            alpha_token_vault,
            max_snapshots=3,
            stale_time=100,
        )
        eligible = undy_vault_prices.priceConfigs(alpha_token_vault).lastSnapshot
        assert eligible.totalSupply == 1
        assert eligible.pricePerShare == scale

        boa.env.time_travel(seconds=3)
        assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == scale
        alpha_token_vault.eval(f"self.totalSupply = {scale - 1}")
        alpha_token.eval(
            f"self.balanceOf[{alpha_token_vault.address}] = {2 * scale}"
        )
        assert undy_vault_prices.addPriceSnapshot(
            alpha_token_vault,
            sender=teller.address,
        )
        ineligible = undy_vault_prices.priceConfigs(alpha_token_vault).lastSnapshot
        assert ineligible.totalSupply == 0
        assert ineligible.pricePerShare != eligible.pricePerShare

        boa.env.time_travel(seconds=4)
        # The one-share seed remains the only eligible ring observation. Its
        # value differs from the fresh normalized-zero lastSnapshot fallback.
        assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == (
            eligible.pricePerShare
        )
        assert undy_vault_prices.getWeightedPrice(alpha_token_vault) != (
            ineligible.pricePerShare
        )


def test_undy_sc17_capacity_one_and_malformed_chronology_fail_soft(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_snapshots=1,
    )
    boa.env.time_travel(seconds=17)
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == EIGHTEEN_DECIMALS
    assert undy_vault_prices.updatePriceConfig(
        alpha_token_vault, 0, 3, 0, 0, sender=governance.address
    )
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmPriceFeedUpdate(
        alpha_token_vault,
        sender=governance.address,
    )
    boa.env.time_travel(seconds=1)
    assert undy_vault_prices.addPriceSnapshot(alpha_token_vault, sender=teller.address)
    undy_vault_prices.eval(
        f"self.snapShots[{alpha_token_vault.address}][0].lastUpdate = "
        f"self.snapShots[{alpha_token_vault.address}][1].lastUpdate"
    )
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == 0


def test_undy_sc17_corrupt_capacity_cursor_and_future_timestamp_fail_soft(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_snapshots=3,
        stale_time=100,
    )
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) != 0
    assert undy_vault_prices.getPrice(alpha_token_vault) != 0

    # Validated public operations cannot create any of these states. Each
    # isolated mutation pins the defense-in-depth fail-soft guards.
    with boa.env.anchor():
        undy_vault_prices.eval(
            f"self.priceConfigs[{alpha_token_vault.address}].maxNumSnapshots = 26"
        )
        assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == 0
        assert undy_vault_prices.getPrice(alpha_token_vault) == 0

    with boa.env.anchor():
        undy_vault_prices.eval(
            f"self.priceConfigs[{alpha_token_vault.address}].maxNumSnapshots = 0"
        )
        assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == 0
        assert undy_vault_prices.getPrice(alpha_token_vault) == 0

    with boa.env.anchor():
        undy_vault_prices.eval(
            f"self.priceConfigs[{alpha_token_vault.address}].nextIndex = "
            f"self.priceConfigs[{alpha_token_vault.address}].maxNumSnapshots"
        )
        assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == 0
        assert undy_vault_prices.getPrice(alpha_token_vault) == 0

    with boa.env.anchor():
        future_timestamp = boa.env.evm.patch.timestamp + 1
        undy_vault_prices.eval(
            f"self.snapShots[{alpha_token_vault.address}][0].lastUpdate = "
            f"{future_timestamp}"
        )
        assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == 0
        assert undy_vault_prices.getPrice(alpha_token_vault) == 0


def test_undy_sc17_duration_multiplication_overflow_fails_soft(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    alpha_token_whale,
    mock_price_source,
    alpha_token,
    teller,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _deposit_undy(
        alpha_token_vault,
        alpha_token,
        alpha_token_whale,
        100 * EIGHTEEN_DECIMALS,
    )
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_snapshots=3,
    )
    # Inject a malformed-but-representable stored PPS so this isolates the
    # oracle's duration multiplication rather than overflowing the vault's
    # own convertToAssets implementation first.
    undy_vault_prices.eval(
        f"self.snapShots[{alpha_token_vault.address}][0].pricePerShare = {2**256 - 1}"
    )
    boa.env.time_travel(seconds=2)
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == 0


def test_undy_sc23_zero_stale_time_and_deadline_overflow(
    undy_vault_prices,
    governance,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    _register_undy_integrity_feed(
        undy_vault_prices,
        governance,
        alpha_token_vault,
        max_snapshots=3,
        stale_time=0,
    )
    boa.env.time_travel(seconds=10**7)
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == EIGHTEEN_DECIMALS
    assert undy_vault_prices.updatePriceConfig(
        alpha_token_vault,
        0,
        3,
        0,
        2**256 - 1,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmPriceFeedUpdate(
        alpha_token_vault,
        sender=governance.address,
    )
    assert undy_vault_prices.getWeightedPrice(alpha_token_vault) == 0


def test_undy_final_deployed_runtime_measurement(undy_vault_prices):
    # Deliberately NOT artifact-marked. This asserts the EIP-170 ceiling, which
    # is deployability, not artifact identity: it cannot go stale from a source
    # change and only fails when the contract genuinely will not deploy. The
    # size and hash are printed for review, never asserted.
    runtime = bytes(boa.env.get_code(undy_vault_prices.address))
    print(
        "UNDY_RUNTIME",
        f"size={len(runtime)}",
        f"sha256={hashlib.sha256(runtime).hexdigest()}",
        f"headroom={24_576 - len(runtime)}",
    )
    assert len(runtime) < 24_576
