import boa

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


def test_convertToAssetsSafe_validation(
    undy_vault_prices,
    alpha_token_vault,
    mock_price_source,
    alpha_token,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
):
    """Test that validation checks convertToAssetsSafe implementation"""
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # alpha_token_vault has convertToAssetsSafe implementation
    assert undy_vault_prices.isValidNewFeed(alpha_token_vault, 0, 10, 0, 10)

    # If we try with an address that doesn't have convertToAssetsSafe,
    # it should fail (but our mock vaults all have it, so this test verifies the happy path)


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
    boa.env.time_travel(seconds=1)  # Advance time
    undy_vault_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    snapshot1 = undy_vault_prices.snapShots(bravo_token_vault, 1)

    # Snapshot 2: Transfer tokens to vault to change price per share
    bravo_token.transfer(bravo_token_vault, 100 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    boa.env.time_travel(seconds=1)  # Advance time
    undy_vault_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    snapshot2 = undy_vault_prices.snapShots(bravo_token_vault, 2)

    # Snapshot 3: Deposit more to change total supply
    bravo_token.approve(bravo_token_vault, 50 * EIGHTEEN_DECIMALS, sender=bravo_token_whale)
    bravo_token_vault.deposit(50 * EIGHTEEN_DECIMALS, bravo_token_whale, sender=bravo_token_whale)
    boa.env.time_travel(seconds=1)  # Advance time
    undy_vault_prices.addPriceSnapshot(bravo_token_vault, sender=teller.address)
    snapshot3 = undy_vault_prices.snapShots(bravo_token_vault, 0)  # Wraps to index 0

    # Calculate weighted average from actual snapshot data
    numerator = (snapshot1.totalSupply * snapshot1.pricePerShare +
                 snapshot2.totalSupply * snapshot2.pricePerShare +
                 snapshot3.totalSupply * snapshot3.pricePerShare)
    denominator = snapshot1.totalSupply + snapshot2.totalSupply + snapshot3.totalSupply
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

    assert weighted_price == config.lastSnapshot.pricePerShare
