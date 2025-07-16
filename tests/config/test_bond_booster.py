import pytest
import boa

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, HUNDRED_PERCENT
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def valid_booster_config():
    """Valid booster configuration for testing"""
    return {
        "user": "0x" + "11" * 20,
        "boostRatio": HUNDRED_PERCENT,  # 100% boost
        "maxUnitsAllowed": 50,
        "expireBlock": 1000000,  # Far in the future
    }


#########################
# Access Control Tests
#########################


def test_bond_booster_add_new_units_used_permissions(bond_booster, alice, bond_room):
    """Test only BondRoom can call addNewUnitsUsed"""
    # Non-BondRoom address cannot call
    with boa.reverts("no perms"):
        bond_booster.addNewUnitsUsed(alice, 10, sender=alice)
    
    # BondRoom can call (though it will do nothing if no config exists)
    bond_booster.addNewUnitsUsed(alice, 10, sender=bond_room.address)


def test_bond_booster_set_bond_booster_permissions(bond_booster, alice, switchboard_delta):
    """Test only Switchboard can call setBondBooster"""
    config = (alice, HUNDRED_PERCENT, 50, 1000000)
    
    # Non-Switchboard address cannot call
    with boa.reverts("no perms"):
        bond_booster.setBondBooster(config, sender=alice)
    
    # Switchboard can call
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)


def test_bond_booster_set_many_bond_boosters_permissions(bond_booster, alice, switchboard_delta):
    """Test only Switchboard can call setManyBondBoosters"""
    configs = [
        (alice, HUNDRED_PERCENT, 50, 1000000),
    ]
    
    # Non-Switchboard address cannot call
    with boa.reverts("no perms"):
        bond_booster.setManyBondBoosters(configs, sender=alice)
    
    # Switchboard can call
    bond_booster.setManyBondBoosters(configs, sender=switchboard_delta.address)


def test_bond_booster_remove_bond_booster_permissions(bond_booster, alice, switchboard_delta):
    """Test only Switchboard can call removeBondBooster"""
    # Non-Switchboard address cannot call
    with boa.reverts("no perms"):
        bond_booster.removeBondBooster(alice, sender=alice)
    
    # Switchboard can call
    bond_booster.removeBondBooster(alice, sender=switchboard_delta.address)


#########################
# Get Boosted Ripe Tests
#########################


def test_bond_booster_get_boost_ratio_no_config(bond_booster, alice):
    """Test getBoostRatio returns 0 when no config exists"""
    boost_ratio = bond_booster.getBoostRatio(alice, 10)
    assert boost_ratio == 0


def test_bond_booster_get_boost_ratio_expired(bond_booster, alice, switchboard_delta):
    """Test getBoostRatio returns 0 when config is expired"""
    # Set config that expires at block 100
    config = (alice, HUNDRED_PERCENT, 50, 100)
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Move to block 101
    boa.env.evm.patch.timestamp += 1000
    boa.env.evm.patch.block_number = 101
    
    boost_ratio = bond_booster.getBoostRatio(alice, 10)
    assert boost_ratio == 0


def test_bond_booster_get_boost_ratio_units_exhausted(bond_booster, alice, switchboard_delta, bond_room):
    """Test getBoostRatio returns 0 when all units are used"""
    # Set config with 50 max units
    config = (alice, HUNDRED_PERCENT, 50, 1000000)
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Use all 50 units
    bond_booster.addNewUnitsUsed(alice, 50, sender=bond_room.address)
    
    boost_ratio = bond_booster.getBoostRatio(alice, 10)
    assert boost_ratio == 0


def test_bond_booster_get_boost_ratio_partial_units(bond_booster, alice, switchboard_delta, bond_room):
    """Test getBoostRatio with partially used units"""
    # Set config with 50 max units, 100% boost ratio
    config = (alice, HUNDRED_PERCENT, 50, 1000000)
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Use 30 units
    bond_booster.addNewUnitsUsed(alice, 30, sender=bond_room.address)
    
    # Request 30 units (only 20 available, but boost ratio should still be returned)
    boost_ratio = bond_booster.getBoostRatio(alice, 30)
    assert boost_ratio == HUNDRED_PERCENT  # Returns percentage, not affected by units requested


def test_bond_booster_get_boost_ratio_full_available(bond_booster, alice, switchboard_delta):
    """Test getBoostRatio when all requested units are available"""
    # Set config with 50 max units, 100% boost ratio
    config = (alice, HUNDRED_PERCENT, 50, 1000000)
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Request 30 units (all available)
    boost_ratio = bond_booster.getBoostRatio(alice, 30)
    assert boost_ratio == HUNDRED_PERCENT  # Returns percentage regardless of units requested


#########################
# Update Units Used Tests
#########################


def test_bond_booster_add_new_units_used(bond_booster, alice, switchboard_delta, bond_room):
    """Test addNewUnitsUsed updates units correctly"""
    # Set config
    config = (alice, HUNDRED_PERCENT, 50, 1000000)
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Initial units used should be 0
    assert bond_booster.unitsUsed(alice) == 0
    
    # Add 10 units
    bond_booster.addNewUnitsUsed(alice, 10, sender=bond_room.address)
    assert bond_booster.unitsUsed(alice) == 10
    
    # Add 15 more units
    bond_booster.addNewUnitsUsed(alice, 15, sender=bond_room.address)
    assert bond_booster.unitsUsed(alice) == 25


def test_bond_booster_add_new_units_no_config(bond_booster, bob, bond_room):
    """Test addNewUnitsUsed works even without config"""
    # No config for bob
    assert bond_booster.unitsUsed(bob) == 0
    
    # Add units (should work even without config)
    bond_booster.addNewUnitsUsed(bob, 10, sender=bond_room.address)
    assert bond_booster.unitsUsed(bob) == 10


#########################
# Set Booster Config Tests
#########################


def test_bond_booster_set_bond_booster(bond_booster, alice, switchboard_delta):
    """Test setBondBooster sets config correctly"""
    config = (alice, 2 * HUNDRED_PERCENT, 75, 2000000)  # 200% boost
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Check event immediately after transaction
    logs = filter_logs(bond_booster, "BondBoostModified")
    assert len(logs) == 1
    log = logs[0]
    assert log.user == alice
    assert log.boostRatio == 2 * HUNDRED_PERCENT
    assert log.maxUnitsAllowed == 75
    assert log.expireBlock == 2000000
    
    # Verify config was set
    stored_config = bond_booster.config(alice)
    assert stored_config[0] == alice
    assert stored_config[1] == 2 * HUNDRED_PERCENT
    assert stored_config[2] == 75
    assert stored_config[3] == 2000000


def test_bond_booster_set_bond_booster_invalid_fails(bond_booster, switchboard_delta):
    """Test setBondBooster fails with invalid config"""
    # Empty user address
    with boa.reverts("invalid booster"):
        config = (ZERO_ADDRESS, HUNDRED_PERCENT, 50, 1000000)
        bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Zero boostRatio
    with boa.reverts("invalid booster"):
        config = ("0x" + "11" * 20, 0, 50, 1000000)
        bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Expired block
    with boa.reverts("invalid booster"):
        config = ("0x" + "11" * 20, HUNDRED_PERCENT, 50, 0)
        bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Zero maxUnitsAllowed
    with boa.reverts("invalid booster"):
        config = ("0x" + "11" * 20, HUNDRED_PERCENT, 0, 1000000)
        bond_booster.setBondBooster(config, sender=switchboard_delta.address)


def test_bond_booster_set_bond_booster_exceeds_max_boost_ratio(bond_booster, alice, switchboard_delta):
    """Test setBondBooster fails when boostRatio exceeds maxBoostRatio"""
    # maxBoostRatio is 1000 * HUNDRED_PERCENT (100,000%) from fixture
    config = (alice, 1001 * HUNDRED_PERCENT, 50, 1000000)
    with boa.reverts("invalid booster"):
        bond_booster.setBondBooster(config, sender=switchboard_delta.address)


def test_bond_booster_set_bond_booster_exceeds_max_units(bond_booster, alice, switchboard_delta):
    """Test setBondBooster fails when maxUnitsAllowed exceeds MAX_UNITS"""
    # MAX_UNITS is 100 from fixture
    config = (alice, HUNDRED_PERCENT, 101, 1000000)
    with boa.reverts("invalid booster"):
        bond_booster.setBondBooster(config, sender=switchboard_delta.address)


#########################
# Set Many Boosters Tests
#########################


def test_bond_booster_set_many_bond_boosters(bond_booster, alice, bob, charlie, switchboard_delta):
    """Test setManyBondBoosters sets multiple configs"""
    configs = [
        (alice, HUNDRED_PERCENT, 50, 1000000),      # 100%
        (bob, 2 * HUNDRED_PERCENT, 25, 2000000),    # 200%
        (charlie, 3 * HUNDRED_PERCENT, 75, 3000000), # 300%
    ]
    
    bond_booster.setManyBondBoosters(configs, sender=switchboard_delta.address)
    
    # Check BondBoostModified events - one for each config
    logs = filter_logs(bond_booster, "BondBoostModified")
    assert len(logs) == 3
    
    # Verify events for each user
    assert logs[0].user == alice
    assert logs[0].boostRatio == HUNDRED_PERCENT
    assert logs[0].maxUnitsAllowed == 50
    assert logs[0].expireBlock == 1000000
    
    assert logs[1].user == bob
    assert logs[1].boostRatio == 2 * HUNDRED_PERCENT
    assert logs[1].maxUnitsAllowed == 25
    assert logs[1].expireBlock == 2000000
    
    assert logs[2].user == charlie
    assert logs[2].boostRatio == 3 * HUNDRED_PERCENT
    assert logs[2].maxUnitsAllowed == 75
    assert logs[2].expireBlock == 3000000
    
    # Verify all configs were set
    alice_config = bond_booster.config(alice)
    assert alice_config[1] == HUNDRED_PERCENT
    assert alice_config[2] == 50
    
    bob_config = bond_booster.config(bob)
    assert bob_config[1] == 2 * HUNDRED_PERCENT
    assert bob_config[2] == 25
    
    charlie_config = bond_booster.config(charlie)
    assert charlie_config[1] == 3 * HUNDRED_PERCENT
    assert charlie_config[2] == 75


def test_bond_booster_set_many_bond_boosters_empty_fails(bond_booster, switchboard_delta):
    """Test setManyBondBoosters fails with empty list"""
    with boa.reverts("no boosters"):
        bond_booster.setManyBondBoosters([], sender=switchboard_delta.address)


def test_bond_booster_set_many_bond_boosters_invalid_fails(bond_booster, alice, switchboard_delta):
    """Test setManyBondBoosters fails with invalid config"""
    configs = [
        (alice, HUNDRED_PERCENT, 50, 1000000),
        (ZERO_ADDRESS, 2 * HUNDRED_PERCENT, 25, 2000000),  # Invalid
    ]
    
    with boa.reverts("invalid booster"):
        bond_booster.setManyBondBoosters(configs, sender=switchboard_delta.address)


def test_bond_booster_set_many_bond_boosters_max_limit(bond_booster, switchboard_delta):
    """Test setManyBondBoosters works up to MAX_BOOSTERS limit"""
    # Create MAX_BOOSTERS (50) configs
    configs = []
    for i in range(50):
        user = "0x" + f"{i+1:040x}"  # Unique address for each
        configs.append((user, HUNDRED_PERCENT, 50, 1000000))
    
    # Should work with exactly MAX_BOOSTERS
    bond_booster.setManyBondBoosters(configs, sender=switchboard_delta.address)
    
    # Check BondBoostModified events - one for each config
    logs = filter_logs(bond_booster, "BondBoostModified")
    assert len(logs) == 50
    
    # Verify first and last events to ensure all were processed
    assert logs[0].user == "0x" + f"{1:040x}"
    assert logs[0].boostRatio == HUNDRED_PERCENT
    assert logs[0].maxUnitsAllowed == 50
    assert logs[0].expireBlock == 1000000
    
    assert logs[49].user == "0x" + f"{50:040x}"
    assert logs[49].boostRatio == HUNDRED_PERCENT
    assert logs[49].maxUnitsAllowed == 50
    assert logs[49].expireBlock == 1000000


#########################
# Remove Booster Tests
#########################


def test_bond_booster_remove_bond_booster(bond_booster, alice, switchboard_delta, bond_room):
    """Test removeBondBooster removes config and resets units"""
    # Set config and use some units
    config = (alice, HUNDRED_PERCENT, 50, 1000000)
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    bond_booster.addNewUnitsUsed(alice, 25, sender=bond_room.address)
    
    # Verify config and units are set
    assert bond_booster.config(alice)[0] == alice
    assert bond_booster.unitsUsed(alice) == 25
    
    # Remove booster
    bond_booster.removeBondBooster(alice, sender=switchboard_delta.address)
    
    # Check event immediately after transaction
    logs = filter_logs(bond_booster, "BondBoostRemoved")
    assert len(logs) == 1
    assert logs[0].user == alice
    
    # Verify config is cleared
    cleared_config = bond_booster.config(alice)
    assert cleared_config[0] == ZERO_ADDRESS
    assert cleared_config[1] == 0
    assert cleared_config[2] == 0
    assert cleared_config[3] == 0
    
    # Verify units are reset
    assert bond_booster.unitsUsed(alice) == 0


def test_bond_booster_remove_non_existent(bond_booster, bob, switchboard_delta):
    """Test removeBondBooster works on non-existent config"""
    # Bob has no config
    bond_booster.removeBondBooster(bob, sender=switchboard_delta.address)
    
    # Should still emit event
    logs = filter_logs(bond_booster, "BondBoostRemoved")
    assert len(logs) == 1
    assert logs[0].user == bob


#########################
# Validation Tests
#########################


def test_bond_booster_is_valid_booster(bond_booster, alice):
    """Test isValidBooster external function"""
    # Valid config
    valid_config = (alice, HUNDRED_PERCENT, 50, 1000000)
    assert bond_booster.isValidBooster(valid_config)
    
    # Invalid: empty user
    invalid_config1 = (ZERO_ADDRESS, HUNDRED_PERCENT, 50, 1000000)
    assert not bond_booster.isValidBooster(invalid_config1)
    
    # Invalid: zero boostRatio
    invalid_config2 = (alice, 0, 50, 1000000)
    assert not bond_booster.isValidBooster(invalid_config2)
    
    # Invalid: boostRatio > maxBoostRatio
    invalid_config3 = (alice, 1001 * HUNDRED_PERCENT, 50, 1000000)
    assert not bond_booster.isValidBooster(invalid_config3)
    
    # Invalid: expired block
    invalid_config4 = (alice, HUNDRED_PERCENT, 50, 0)
    assert not bond_booster.isValidBooster(invalid_config4)
    
    # Invalid: zero maxUnitsAllowed
    invalid_config5 = (alice, HUNDRED_PERCENT, 0, 1000000)
    assert not bond_booster.isValidBooster(invalid_config5)
    
    # Invalid: maxUnitsAllowed > MAX_UNITS
    invalid_config6 = (alice, HUNDRED_PERCENT, 101, 1000000)
    assert not bond_booster.isValidBooster(invalid_config6)


#########################
# Integration Tests
#########################


def test_bond_booster_update_existing_config(bond_booster, alice, switchboard_delta, bond_room):
    """Test updating existing booster config preserves units used"""
    # Set initial config
    config1 = (alice, HUNDRED_PERCENT, 50, 1000000)
    bond_booster.setBondBooster(config1, sender=switchboard_delta.address)
    
    # Use some units
    bond_booster.addNewUnitsUsed(alice, 20, sender=bond_room.address)
    assert bond_booster.unitsUsed(alice) == 20
    
    # Update config (change boostRatio and maxUnitsAllowed)
    config2 = (alice, int(1.5 * HUNDRED_PERCENT), 75, 2000000)  # 150%
    bond_booster.setBondBooster(config2, sender=switchboard_delta.address)
    
    # Units used should be preserved
    assert bond_booster.unitsUsed(alice) == 20
    
    # New config should be active
    stored_config = bond_booster.config(alice)
    assert stored_config[1] == int(1.5 * HUNDRED_PERCENT)
    assert stored_config[2] == 75


def test_bond_booster_workflow_complete(bond_booster, alice, bob, switchboard_delta, bond_room):
    """Test complete workflow of setting, using, and removing boosters"""
    # 1. Set boosters for multiple users
    configs = [
        (alice, HUNDRED_PERCENT, 50, 1000000),      # 100%
        (bob, 2 * HUNDRED_PERCENT, 30, 1000000),    # 200%
    ]
    bond_booster.setManyBondBoosters(configs, sender=switchboard_delta.address)
    
    # 2. Use some units for alice
    bond_booster.addNewUnitsUsed(alice, 20, sender=bond_room.address)
    
    # 3. Check boost ratios
    alice_boost_ratio = bond_booster.getBoostRatio(alice, 40)  # Still has units available
    assert alice_boost_ratio == HUNDRED_PERCENT
    
    bob_boost_ratio = bond_booster.getBoostRatio(bob, 20)  # Has units available
    assert bob_boost_ratio == 2 * HUNDRED_PERCENT
    
    # 4. Use more units for alice (exhaust)
    bond_booster.addNewUnitsUsed(alice, 30, sender=bond_room.address)
    alice_boost_ratio2 = bond_booster.getBoostRatio(alice, 10)
    assert alice_boost_ratio2 == 0  # All units used
    
    # 5. Remove alice's booster
    bond_booster.removeBondBooster(alice, sender=switchboard_delta.address)
    
    # 6. Verify alice has no boost, bob still does
    assert bond_booster.getBoostRatio(alice, 10) == 0
    assert bond_booster.getBoostRatio(bob, 10) == 2 * HUNDRED_PERCENT


def test_bond_booster_edge_cases(bond_booster, alice, switchboard_delta, bond_room):
    """Test edge cases and boundary conditions"""
    # Set config at max values
    config = (alice, 1000 * HUNDRED_PERCENT, 100, 1000000)  # Max boost ratio and units
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Use exactly max units
    bond_booster.addNewUnitsUsed(alice, 100, sender=bond_room.address)
    
    # Should get 0 boost ratio
    assert bond_booster.getBoostRatio(alice, 1) == 0
    
    # Reset for next test
    bond_booster.removeBondBooster(alice, sender=switchboard_delta.address)
    
    # Set config that expires next block
    current_block = boa.env.evm.patch.block_number
    config2 = (alice, HUNDRED_PERCENT, 50, current_block + 1)
    bond_booster.setBondBooster(config2, sender=switchboard_delta.address)
    
    # Should work now
    assert bond_booster.getBoostRatio(alice, 10) == HUNDRED_PERCENT
    
    # Move forward one block
    boa.env.evm.patch.block_number = current_block + 1
    
    # Should be expired
    assert bond_booster.getBoostRatio(alice, 10) == 0