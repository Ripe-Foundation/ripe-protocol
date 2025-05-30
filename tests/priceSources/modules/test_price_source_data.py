import pytest
import boa

from constants import ZERO_ADDRESS
from config.BluePrint import PARAMS
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def price_source_mock(ripe_hq_deploy, fork):
    return boa.load(
        "contracts/mock/MockPriceSource.vy",
        ripe_hq_deploy,
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
    )


# tests


def test_price_source_data_add_asset(
    price_source_mock,
    alpha_token,
):
    # Add asset
    price_source_mock.setPrice(alpha_token, 100)
    
    # Verify asset data
    assert price_source_mock.numAssets() == 2
    assert price_source_mock.assets(1) == alpha_token.address
    assert price_source_mock.indexOfAsset(alpha_token) == 1
    
    # Verify getPricedAssets
    assets = price_source_mock.getPricedAssets()
    assert len(assets) == 1
    assert assets[0] == alpha_token.address


def test_price_source_data_add_multiple_assets(
    price_source_mock,
    alpha_token,
    bravo_token,
    charlie_token,
):
    # Add multiple assets
    price_source_mock.setPrice(alpha_token, 100)
    price_source_mock.setPrice(bravo_token, 200)
    price_source_mock.setPrice(charlie_token, 300)
    
    # Verify asset data
    assert price_source_mock.numAssets() == 4
    assert price_source_mock.assets(1) == alpha_token.address
    assert price_source_mock.assets(2) == bravo_token.address
    assert price_source_mock.assets(3) == charlie_token.address
    assert price_source_mock.indexOfAsset(alpha_token) == 1
    assert price_source_mock.indexOfAsset(bravo_token) == 2
    assert price_source_mock.indexOfAsset(charlie_token) == 3
    
    # Verify getPricedAssets
    assets = price_source_mock.getPricedAssets()
    assert len(assets) == 3
    assert assets[0] == alpha_token.address
    assert assets[1] == bravo_token.address
    assert assets[2] == charlie_token.address


def test_price_source_data_remove_asset(
    price_source_mock,
    alpha_token,
    bravo_token,
    charlie_token,
):
    # Add assets
    price_source_mock.setPrice(alpha_token, 100)
    price_source_mock.setPrice(bravo_token, 200)
    price_source_mock.setPrice(charlie_token, 300)
    
    # Remove middle asset
    price_source_mock.disablePriceFeed(bravo_token)
    
    # Verify asset data
    assert price_source_mock.numAssets() == 3
    assert price_source_mock.assets(1) == alpha_token.address
    assert price_source_mock.assets(2) == charlie_token.address
    assert price_source_mock.indexOfAsset(alpha_token) == 1
    assert price_source_mock.indexOfAsset(bravo_token) == 0  # removed
    assert price_source_mock.indexOfAsset(charlie_token) == 2
    
    # Verify getPricedAssets
    assets = price_source_mock.getPricedAssets()
    assert len(assets) == 2
    assert assets[0] == alpha_token.address
    assert assets[1] == charlie_token.address


def test_price_source_data_remove_last_asset(
    price_source_mock,
    alpha_token,
    bravo_token,
):
    # Add assets
    price_source_mock.setPrice(alpha_token, 100)
    price_source_mock.setPrice(bravo_token, 200)
    
    # Remove last asset
    price_source_mock.disablePriceFeed(bravo_token)
    
    # Verify asset data
    assert price_source_mock.numAssets() == 2
    assert price_source_mock.assets(1) == alpha_token.address
    assert price_source_mock.indexOfAsset(alpha_token) == 1
    assert price_source_mock.indexOfAsset(bravo_token) == 0  # removed
    
    # Verify getPricedAssets
    assets = price_source_mock.getPricedAssets()
    assert len(assets) == 1
    assert assets[0] == alpha_token.address


def test_price_source_data_remove_first_asset(
    price_source_mock,
    alpha_token,
    bravo_token,
    charlie_token,
):
    # Add assets
    price_source_mock.setPrice(alpha_token, 100)
    price_source_mock.setPrice(bravo_token, 200)
    price_source_mock.setPrice(charlie_token, 300)
    
    # Remove first asset
    price_source_mock.disablePriceFeed(alpha_token)
    
    # Verify asset data
    assert price_source_mock.numAssets() == 3
    assert price_source_mock.assets(1) == charlie_token.address  # last asset moved to first position
    assert price_source_mock.assets(2) == bravo_token.address
    assert price_source_mock.indexOfAsset(alpha_token) == 0  # removed
    assert price_source_mock.indexOfAsset(bravo_token) == 2
    assert price_source_mock.indexOfAsset(charlie_token) == 1
    
    # Verify getPricedAssets
    assets = price_source_mock.getPricedAssets()
    assert len(assets) == 2
    assert assets[0] == charlie_token.address
    assert assets[1] == bravo_token.address


def test_price_source_data_remove_all_assets(
    price_source_mock,
    alpha_token,
    bravo_token,
    charlie_token,
):
    # Add assets
    price_source_mock.setPrice(alpha_token, 100)
    price_source_mock.setPrice(bravo_token, 200)
    price_source_mock.setPrice(charlie_token, 300)
    
    # Remove all assets
    price_source_mock.disablePriceFeed(alpha_token)
    price_source_mock.disablePriceFeed(bravo_token)
    price_source_mock.disablePriceFeed(charlie_token)
    
    # Verify asset data
    assert price_source_mock.numAssets() == 1
    assert price_source_mock.indexOfAsset(alpha_token) == 0
    assert price_source_mock.indexOfAsset(bravo_token) == 0
    assert price_source_mock.indexOfAsset(charlie_token) == 0
    
    # Verify getPricedAssets
    assets = price_source_mock.getPricedAssets()
    assert len(assets) == 0


def test_price_source_data_remove_nonexistent_asset(
    price_source_mock,
    alpha_token,
):
    # Try to remove non-existent asset
    price_source_mock.disablePriceFeed(alpha_token)
    
    # Verify no changes
    assert price_source_mock.numAssets() == 0
    assert price_source_mock.indexOfAsset(alpha_token) == 0
    
    # Verify getPricedAssets
    assets = price_source_mock.getPricedAssets()
    assert len(assets) == 0


def test_price_source_data_add_duplicate_asset(
    price_source_mock,
    alpha_token,
):
    # Add asset
    price_source_mock.setPrice(alpha_token, 100)
    
    # Add same asset again
    price_source_mock.setPrice(alpha_token, 200)
    
    # Verify asset data unchanged
    assert price_source_mock.numAssets() == 2
    assert price_source_mock.assets(1) == alpha_token.address
    assert price_source_mock.indexOfAsset(alpha_token) == 1
    
    # Verify getPricedAssets
    assets = price_source_mock.getPricedAssets()
    assert len(assets) == 1
    assert assets[0] == alpha_token.address


def test_price_source_data_pause(
    price_source_mock,
    mission_control_gov,
    bob,
):
    # Test initial state
    assert not price_source_mock.isPaused()
    
    # Test unauthorized pause
    with boa.reverts("no perms"):
        price_source_mock.pause(True, sender=bob)
    
    # Test pause
    price_source_mock.pause(True, sender=mission_control_gov.address)
    
    # Verify pause event
    pause_log = filter_logs(price_source_mock, "PriceSourcePauseModified")[0]
    assert pause_log.isPaused == True

    assert price_source_mock.isPaused()

    # Test unpause
    price_source_mock.pause(False, sender=mission_control_gov.address)
    
    # Verify unpause event
    unpause_log = filter_logs(price_source_mock, "PriceSourcePauseModified")[0]
    assert unpause_log.isPaused == False

    assert not price_source_mock.isPaused()

    # Test no change
    with boa.reverts("no change"):
        price_source_mock.pause(False, sender=mission_control_gov.address)


def test_price_source_data_recover_funds(
    price_source_mock,
    mission_control_gov,
    bob,
    alpha_token,
    alpha_token_whale,
):
    # Test unauthorized recovery
    with boa.reverts("no perms"):
        price_source_mock.recoverFunds(bob, alpha_token, sender=bob)
    
    # Test recovery with zero balance
    with boa.reverts("nothing to recover"):
        price_source_mock.recoverFunds(bob, alpha_token, sender=mission_control_gov.address)
    
    # Test recovery with invalid recipient
    with boa.reverts("invalid recipient or asset"):
        price_source_mock.recoverFunds(ZERO_ADDRESS, alpha_token, sender=mission_control_gov.address)
    
    # Test recovery with invalid asset
    with boa.reverts("invalid recipient or asset"):
        price_source_mock.recoverFunds(bob, ZERO_ADDRESS, sender=mission_control_gov.address)
    
    # Transfer tokens to price source
    amount = 1000
    alpha_token.transfer(price_source_mock, amount, sender=alpha_token_whale)
    
    # Test successful recovery
    price_source_mock.recoverFunds(bob, alpha_token, sender=mission_control_gov.address)
    
    # Verify recovery event
    recovery_log = filter_logs(price_source_mock, "PriceSourceFundsRecovered")[0]
    assert recovery_log.asset == alpha_token.address
    assert recovery_log.recipient == bob
    assert recovery_log.balance == amount
    
    # Verify token balance
    assert alpha_token.balanceOf(price_source_mock) == 0
    assert alpha_token.balanceOf(bob) == amount


def test_price_source_data_recover_funds_many(
    price_source_mock,
    mission_control_gov,
    bob,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
):
    # Test unauthorized recovery
    with boa.reverts("no perms"):
        price_source_mock.recoverFundsMany(bob, [alpha_token, bravo_token], sender=bob)
    
    # Test recovery with empty array
    price_source_mock.recoverFundsMany(bob, [], sender=mission_control_gov.address)
    # No events should be emitted for empty array
    
    # Test recovery with zero balances
    with boa.reverts("nothing to recover"):
        price_source_mock.recoverFundsMany(bob, [alpha_token, bravo_token], sender=mission_control_gov.address)
    
    # Test recovery with invalid recipient
    with boa.reverts("invalid recipient or asset"):
        price_source_mock.recoverFundsMany(ZERO_ADDRESS, [alpha_token, bravo_token], sender=mission_control_gov.address)

    # Transfer tokens to price source
    amount1 = 1000
    amount2 = 2000
    alpha_token.transfer(price_source_mock, amount1, sender=alpha_token_whale)
    bravo_token.transfer(price_source_mock, amount2, sender=bravo_token_whale)

    # Test recovery with invalid asset
    with boa.reverts("invalid recipient or asset"):
        price_source_mock.recoverFundsMany(bob, [alpha_token, ZERO_ADDRESS], sender=mission_control_gov.address)
    
    # Test recovery with too many assets
    too_many_assets = [alpha_token] * 21  # MAX_RECOVER_ASSETS is 20
    with boa.reverts():
        price_source_mock.recoverFundsMany(bob, too_many_assets, sender=mission_control_gov.address)
    
    # Test successful recovery of multiple assets
    price_source_mock.recoverFundsMany(bob, [alpha_token, bravo_token], sender=mission_control_gov.address)
    
    # Verify recovery events
    recovery_logs = filter_logs(price_source_mock, "PriceSourceFundsRecovered")
    assert len(recovery_logs) == 2
    
    # Verify first token recovery
    assert recovery_logs[0].asset == alpha_token.address
    assert recovery_logs[0].recipient == bob
    assert recovery_logs[0].balance == amount1
    
    # Verify second token recovery
    assert recovery_logs[1].asset == bravo_token.address
    assert recovery_logs[1].recipient == bob
    assert recovery_logs[1].balance == amount2
    
    # Verify token balances
    assert alpha_token.balanceOf(price_source_mock) == 0
    assert bravo_token.balanceOf(price_source_mock) == 0
    assert alpha_token.balanceOf(bob) == amount1
    assert bravo_token.balanceOf(bob) == amount2


def test_price_source_data_max_assets(
    price_source_mock,
):
    # Create array of unique token addresses
    tokens = []
    for i in range(50):  # MAX_ASSETS is 50
        # Create a new token address by adding i to the base token address
        token = boa.env.generate_address(i)
        tokens.append(token)
        price_source_mock.setPrice(token, 100)
    
    # Verify we can get all assets
    assets = price_source_mock.getPricedAssets()
    assert len(assets) == 50
    
    # Verify array ordering and indexing
    for i in range(50):
        assert price_source_mock.assets(i + 1) == assets[i]
        assert price_source_mock.indexOfAsset(assets[i]) == i + 1
        assert assets[i] in tokens  # Verify each asset is one of our tokens


def test_price_source_data_array_ordering(
    price_source_mock,
    alpha_token,
    bravo_token,
    charlie_token,
):
    # Add assets in specific order
    price_source_mock.setPrice(alpha_token, 100)
    price_source_mock.setPrice(bravo_token, 200)
    price_source_mock.setPrice(charlie_token, 300)
    
    # Get assets array
    assets = price_source_mock.getPricedAssets()
    
    # Verify array ordering matches addition order
    assert len(assets) == 3
    assert assets[0] == alpha_token.address
    assert assets[1] == bravo_token.address
    assert assets[2] == charlie_token.address
    
    # Remove middle asset
    price_source_mock.disablePriceFeed(bravo_token)
    
    # Get updated assets array
    assets = price_source_mock.getPricedAssets()
    
    # Verify array ordering after removal
    assert len(assets) == 2
    assert assets[0] == alpha_token.address
    assert assets[1] == charlie_token.address
    
    # Add new asset
    price_source_mock.setPrice(bravo_token, 400)
    
    # Get final assets array
    assets = price_source_mock.getPricedAssets()
    
    # Verify final array ordering
    assert len(assets) == 3
    assert assets[0] == alpha_token.address
    assert assets[1] == charlie_token.address
    assert assets[2] == bravo_token.address
