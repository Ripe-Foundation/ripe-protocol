import pytest
import boa

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def valid_booster_config():
    """Valid booster configuration for testing"""
    return {
        "user": "0x" + "11" * 20,
        "ripePerUnit": 100 * EIGHTEEN_DECIMALS,  # 100 RIPE per unit
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
    config = (alice, 100 * EIGHTEEN_DECIMALS, 50, 1000000)
    
    # Non-Switchboard address cannot call
    with boa.reverts("no perms"):
        bond_booster.setBondBooster(config, sender=alice)
    
    # Switchboard can call
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)


def test_bond_booster_set_many_bond_boosters_permissions(bond_booster, alice, switchboard_delta):
    """Test only Switchboard can call setManyBondBoosters"""
    configs = [
        (alice, 100 * EIGHTEEN_DECIMALS, 50, 1000000),
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


def test_bond_booster_get_boosted_ripe_no_config(bond_booster, alice):
    """Test getBoostedRipe returns 0 when no config exists"""
    boosted = bond_booster.getBoostedRipe(alice, 10)
    assert boosted == 0


def test_bond_booster_get_boosted_ripe_expired(bond_booster, alice, switchboard_delta):
    """Test getBoostedRipe returns 0 when config is expired"""
    # Set config that expires at block 100
    config = (alice, 100 * EIGHTEEN_DECIMALS, 50, 100)
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Move to block 101
    boa.env.evm.patch.timestamp += 1000
    boa.env.evm.patch.block_number = 101
    
    boosted = bond_booster.getBoostedRipe(alice, 10)
    assert boosted == 0


def test_bond_booster_get_boosted_ripe_units_exhausted(bond_booster, alice, switchboard_delta, bond_room):
    """Test getBoostedRipe returns 0 when all units are used"""
    # Set config with 50 max units
    config = (alice, 100 * EIGHTEEN_DECIMALS, 50, 1000000)
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Use all 50 units
    bond_booster.addNewUnitsUsed(alice, 50, sender=bond_room.address)
    
    boosted = bond_booster.getBoostedRipe(alice, 10)
    assert boosted == 0


def test_bond_booster_get_boosted_ripe_partial_units(bond_booster, alice, switchboard_delta, bond_room):
    """Test getBoostedRipe with partially used units"""
    # Set config with 50 max units, 100 RIPE per unit
    config = (alice, 100 * EIGHTEEN_DECIMALS, 50, 1000000)
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Use 30 units
    bond_booster.addNewUnitsUsed(alice, 30, sender=bond_room.address)
    
    # Request 30 units (only 20 available)
    boosted = bond_booster.getBoostedRipe(alice, 30)
    assert boosted == 100 * EIGHTEEN_DECIMALS * 20  # 20 units * 100 RIPE


def test_bond_booster_get_boosted_ripe_full_available(bond_booster, alice, switchboard_delta):
    """Test getBoostedRipe when all requested units are available"""
    # Set config with 50 max units, 100 RIPE per unit
    config = (alice, 100 * EIGHTEEN_DECIMALS, 50, 1000000)
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Request 30 units (all available)
    boosted = bond_booster.getBoostedRipe(alice, 30)
    assert boosted == 100 * EIGHTEEN_DECIMALS * 30  # 30 units * 100 RIPE


#########################
# Update Units Used Tests
#########################


def test_bond_booster_add_new_units_used(bond_booster, alice, switchboard_delta, bond_room):
    """Test addNewUnitsUsed updates units correctly"""
    # Set config
    config = (alice, 100 * EIGHTEEN_DECIMALS, 50, 1000000)
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
    config = (alice, 200 * EIGHTEEN_DECIMALS, 75, 2000000)
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Check event immediately after transaction
    logs = filter_logs(bond_booster, "BondBoostModified")
    assert len(logs) == 1
    log = logs[0]
    assert log.user == alice
    assert log.ripePerUnit == 200 * EIGHTEEN_DECIMALS
    assert log.maxUnitsAllowed == 75
    assert log.expireBlock == 2000000
    
    # Verify config was set
    stored_config = bond_booster.config(alice)
    assert stored_config[0] == alice
    assert stored_config[1] == 200 * EIGHTEEN_DECIMALS
    assert stored_config[2] == 75
    assert stored_config[3] == 2000000


def test_bond_booster_set_bond_booster_invalid_fails(bond_booster, switchboard_delta):
    """Test setBondBooster fails with invalid config"""
    # Empty user address
    with boa.reverts("invalid booster"):
        config = (ZERO_ADDRESS, 100 * EIGHTEEN_DECIMALS, 50, 1000000)
        bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Zero ripePerUnit
    with boa.reverts("invalid booster"):
        config = ("0x" + "11" * 20, 0, 50, 1000000)
        bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Expired block
    with boa.reverts("invalid booster"):
        config = ("0x" + "11" * 20, 100 * EIGHTEEN_DECIMALS, 50, 0)
        bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Zero maxUnitsAllowed
    with boa.reverts("invalid booster"):
        config = ("0x" + "11" * 20, 100 * EIGHTEEN_DECIMALS, 0, 1000000)
        bond_booster.setBondBooster(config, sender=switchboard_delta.address)


def test_bond_booster_set_bond_booster_exceeds_max_boost(bond_booster, alice, switchboard_delta):
    """Test setBondBooster fails when ripePerUnit exceeds MAX_BOOST"""
    # MAX_BOOST is 1000 * 10^18 from fixture
    config = (alice, 1001 * EIGHTEEN_DECIMALS, 50, 1000000)
    with boa.reverts("invalid booster"):
        bond_booster.setBondBooster(config, sender=switchboard_delta.address)


def test_bond_booster_set_bond_booster_exceeds_max_units(bond_booster, alice, switchboard_delta):
    """Test setBondBooster fails when maxUnitsAllowed exceeds MAX_UNITS"""
    # MAX_UNITS is 100 from fixture
    config = (alice, 100 * EIGHTEEN_DECIMALS, 101, 1000000)
    with boa.reverts("invalid booster"):
        bond_booster.setBondBooster(config, sender=switchboard_delta.address)


#########################
# Set Many Boosters Tests
#########################


def test_bond_booster_set_many_bond_boosters(bond_booster, alice, bob, charlie, switchboard_delta):
    """Test setManyBondBoosters sets multiple configs"""
    configs = [
        (alice, 100 * EIGHTEEN_DECIMALS, 50, 1000000),
        (bob, 200 * EIGHTEEN_DECIMALS, 25, 2000000),
        (charlie, 300 * EIGHTEEN_DECIMALS, 75, 3000000),
    ]
    
    bond_booster.setManyBondBoosters(configs, sender=switchboard_delta.address)
    
    # Check BondBoostModified events - one for each config
    logs = filter_logs(bond_booster, "BondBoostModified")
    assert len(logs) == 3
    
    # Verify events for each user
    assert logs[0].user == alice
    assert logs[0].ripePerUnit == 100 * EIGHTEEN_DECIMALS
    assert logs[0].maxUnitsAllowed == 50
    assert logs[0].expireBlock == 1000000
    
    assert logs[1].user == bob
    assert logs[1].ripePerUnit == 200 * EIGHTEEN_DECIMALS
    assert logs[1].maxUnitsAllowed == 25
    assert logs[1].expireBlock == 2000000
    
    assert logs[2].user == charlie
    assert logs[2].ripePerUnit == 300 * EIGHTEEN_DECIMALS
    assert logs[2].maxUnitsAllowed == 75
    assert logs[2].expireBlock == 3000000
    
    # Verify all configs were set
    alice_config = bond_booster.config(alice)
    assert alice_config[1] == 100 * EIGHTEEN_DECIMALS
    assert alice_config[2] == 50
    
    bob_config = bond_booster.config(bob)
    assert bob_config[1] == 200 * EIGHTEEN_DECIMALS
    assert bob_config[2] == 25
    
    charlie_config = bond_booster.config(charlie)
    assert charlie_config[1] == 300 * EIGHTEEN_DECIMALS
    assert charlie_config[2] == 75


def test_bond_booster_set_many_bond_boosters_empty_fails(bond_booster, switchboard_delta):
    """Test setManyBondBoosters fails with empty list"""
    with boa.reverts("no boosters"):
        bond_booster.setManyBondBoosters([], sender=switchboard_delta.address)


def test_bond_booster_set_many_bond_boosters_invalid_fails(bond_booster, alice, switchboard_delta):
    """Test setManyBondBoosters fails with invalid config"""
    configs = [
        (alice, 100 * EIGHTEEN_DECIMALS, 50, 1000000),
        (ZERO_ADDRESS, 200 * EIGHTEEN_DECIMALS, 25, 2000000),  # Invalid
    ]
    
    with boa.reverts("invalid booster"):
        bond_booster.setManyBondBoosters(configs, sender=switchboard_delta.address)


def test_bond_booster_set_many_bond_boosters_max_limit(bond_booster, switchboard_delta):
    """Test setManyBondBoosters works up to MAX_BOOSTERS limit"""
    # Create MAX_BOOSTERS (50) configs
    configs = []
    for i in range(50):
        user = "0x" + f"{i+1:040x}"  # Unique address for each
        configs.append((user, 100 * EIGHTEEN_DECIMALS, 50, 1000000))
    
    # Should work with exactly MAX_BOOSTERS
    bond_booster.setManyBondBoosters(configs, sender=switchboard_delta.address)
    
    # Check BondBoostModified events - one for each config
    logs = filter_logs(bond_booster, "BondBoostModified")
    assert len(logs) == 50
    
    # Verify first and last events to ensure all were processed
    assert logs[0].user == "0x" + f"{1:040x}"
    assert logs[0].ripePerUnit == 100 * EIGHTEEN_DECIMALS
    assert logs[0].maxUnitsAllowed == 50
    assert logs[0].expireBlock == 1000000
    
    assert logs[49].user == "0x" + f"{50:040x}"
    assert logs[49].ripePerUnit == 100 * EIGHTEEN_DECIMALS
    assert logs[49].maxUnitsAllowed == 50
    assert logs[49].expireBlock == 1000000


#########################
# Remove Booster Tests
#########################


def test_bond_booster_remove_bond_booster(bond_booster, alice, switchboard_delta, bond_room):
    """Test removeBondBooster removes config and resets units"""
    # Set config and use some units
    config = (alice, 100 * EIGHTEEN_DECIMALS, 50, 1000000)
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
    valid_config = (alice, 100 * EIGHTEEN_DECIMALS, 50, 1000000)
    assert bond_booster.isValidBooster(valid_config)
    
    # Invalid: empty user
    invalid_config1 = (ZERO_ADDRESS, 100 * EIGHTEEN_DECIMALS, 50, 1000000)
    assert not bond_booster.isValidBooster(invalid_config1)
    
    # Invalid: zero ripePerUnit
    invalid_config2 = (alice, 0, 50, 1000000)
    assert not bond_booster.isValidBooster(invalid_config2)
    
    # Invalid: ripePerUnit > MAX_BOOST
    invalid_config3 = (alice, 1001 * EIGHTEEN_DECIMALS, 50, 1000000)
    assert not bond_booster.isValidBooster(invalid_config3)
    
    # Invalid: expired block
    invalid_config4 = (alice, 100 * EIGHTEEN_DECIMALS, 50, 0)
    assert not bond_booster.isValidBooster(invalid_config4)
    
    # Invalid: zero maxUnitsAllowed
    invalid_config5 = (alice, 100 * EIGHTEEN_DECIMALS, 0, 1000000)
    assert not bond_booster.isValidBooster(invalid_config5)
    
    # Invalid: maxUnitsAllowed > MAX_UNITS
    invalid_config6 = (alice, 100 * EIGHTEEN_DECIMALS, 101, 1000000)
    assert not bond_booster.isValidBooster(invalid_config6)


#########################
# Integration Tests
#########################


def test_bond_booster_update_existing_config(bond_booster, alice, switchboard_delta, bond_room):
    """Test updating existing booster config preserves units used"""
    # Set initial config
    config1 = (alice, 100 * EIGHTEEN_DECIMALS, 50, 1000000)
    bond_booster.setBondBooster(config1, sender=switchboard_delta.address)
    
    # Use some units
    bond_booster.addNewUnitsUsed(alice, 20, sender=bond_room.address)
    assert bond_booster.unitsUsed(alice) == 20
    
    # Update config (change ripePerUnit and maxUnitsAllowed)
    config2 = (alice, 150 * EIGHTEEN_DECIMALS, 75, 2000000)
    bond_booster.setBondBooster(config2, sender=switchboard_delta.address)
    
    # Units used should be preserved
    assert bond_booster.unitsUsed(alice) == 20
    
    # New config should be active
    stored_config = bond_booster.config(alice)
    assert stored_config[1] == 150 * EIGHTEEN_DECIMALS
    assert stored_config[2] == 75


def test_bond_booster_workflow_complete(bond_booster, alice, bob, switchboard_delta, bond_room):
    """Test complete workflow of setting, using, and removing boosters"""
    # 1. Set boosters for multiple users
    configs = [
        (alice, 100 * EIGHTEEN_DECIMALS, 50, 1000000),
        (bob, 200 * EIGHTEEN_DECIMALS, 30, 1000000),
    ]
    bond_booster.setManyBondBoosters(configs, sender=switchboard_delta.address)
    
    # 2. Use some units for alice
    bond_booster.addNewUnitsUsed(alice, 20, sender=bond_room.address)
    
    # 3. Check boosted amounts
    alice_boost = bond_booster.getBoostedRipe(alice, 40)  # Request 40, get 30
    assert alice_boost == 100 * EIGHTEEN_DECIMALS * 30
    
    bob_boost = bond_booster.getBoostedRipe(bob, 20)  # Request 20, get 20
    assert bob_boost == 200 * EIGHTEEN_DECIMALS * 20
    
    # 4. Use more units for alice (exhaust)
    bond_booster.addNewUnitsUsed(alice, 30, sender=bond_room.address)
    alice_boost2 = bond_booster.getBoostedRipe(alice, 10)
    assert alice_boost2 == 0  # All units used
    
    # 5. Remove alice's booster
    bond_booster.removeBondBooster(alice, sender=switchboard_delta.address)
    
    # 6. Verify alice has no boost, bob still does
    assert bond_booster.getBoostedRipe(alice, 10) == 0
    assert bond_booster.getBoostedRipe(bob, 10) == 200 * EIGHTEEN_DECIMALS * 10


def test_bond_booster_edge_cases(bond_booster, alice, switchboard_delta, bond_room):
    """Test edge cases and boundary conditions"""
    # Set config at max values
    config = (alice, 1000 * EIGHTEEN_DECIMALS, 100, 1000000)  # Max boost and units
    bond_booster.setBondBooster(config, sender=switchboard_delta.address)
    
    # Use exactly max units
    bond_booster.addNewUnitsUsed(alice, 100, sender=bond_room.address)
    
    # Should get 0 boost
    assert bond_booster.getBoostedRipe(alice, 1) == 0
    
    # Reset for next test
    bond_booster.removeBondBooster(alice, sender=switchboard_delta.address)
    
    # Set config that expires next block
    current_block = boa.env.evm.patch.block_number
    config2 = (alice, 100 * EIGHTEEN_DECIMALS, 50, current_block + 1)
    bond_booster.setBondBooster(config2, sender=switchboard_delta.address)
    
    # Should work now
    assert bond_booster.getBoostedRipe(alice, 10) == 100 * EIGHTEEN_DECIMALS * 10
    
    # Move forward one block
    boa.env.evm.patch.block_number = current_block + 1
    
    # Should be expired
    assert bond_booster.getBoostedRipe(alice, 10) == 0