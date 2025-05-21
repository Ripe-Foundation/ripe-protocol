import pytest
import boa

from constants import ZERO_ADDRESS
from conf_utils import filter_logs
from config.BluePrint import PARAMS


def test_mock_address_registry_deploy(
    mock_registry,
    fork,
):
    assert mock_registry.getRegistryDescription() == "MockRegistry.vy"
    assert mock_registry.registryChangeTimeLock() == PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"]
    assert mock_registry.numAddrs() == 1

    assert mock_registry.minRegistryTimeLock() == PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"]
    assert mock_registry.maxRegistryTimeLock() == PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"]


###############
# New Address #
###############


def test_add_new_address_basic(
    mock_registry,
    mock_rando_contract,
    governance,
    bob,
):
    time_lock = mock_registry.registryChangeTimeLock()

    # Start adding new address
    description = "Test Contract"

    # no perms
    with boa.reverts("no perms"):
        mock_registry.startAddNewAddressToRegistry(mock_rando_contract, description, sender=bob)

    # success
    assert mock_registry.startAddNewAddressToRegistry(mock_rando_contract, description, sender=governance.address)
    
    # Verify pending event
    pending_log = filter_logs(mock_registry, "NewAddressPending")[0]
    assert pending_log.addr == mock_rando_contract.address
    assert pending_log.description == description
    assert pending_log.confirmBlock == boa.env.evm.patch.block_number + time_lock
    assert pending_log.registry == "MockRegistry.vy"
    
    # Verify pending state
    pending = mock_registry.pendingNewAddr(mock_rando_contract)
    assert pending.description == description
    assert pending.initiatedBlock == boa.env.evm.patch.block_number
    assert pending.confirmBlock == pending_log.confirmBlock

    # time lock not reached
    with boa.reverts("time lock not reached"):
        mock_registry.confirmNewAddressToRegistry(mock_rando_contract, sender=governance.address)

    # time travel
    boa.env.time_travel(blocks=time_lock)

    # Confirm new address
    reg_id = mock_registry.confirmNewAddressToRegistry(mock_rando_contract, sender=governance.address)
    assert reg_id == 1

    # Verify confirmed event
    confirmed_log = filter_logs(mock_registry, "NewAddressConfirmed")[0]
    assert confirmed_log.addr == mock_rando_contract.address
    assert confirmed_log.regId == reg_id
    assert confirmed_log.description == description
    assert confirmed_log.registry == "MockRegistry.vy"

    # Verify address info
    addr_info = mock_registry.getAddrInfo(reg_id)
    assert addr_info.addr == mock_rando_contract.address
    assert addr_info.version == 1
    assert addr_info.description == description
    assert addr_info.lastModified == boa.env.evm.patch.timestamp

    # pending is cleared
    assert mock_registry.pendingNewAddr(mock_rando_contract).confirmBlock == 0

    # Verify mappings
    assert mock_registry.getRegId(mock_rando_contract) == reg_id
    assert mock_registry.isValidAddr(mock_rando_contract)
    assert mock_registry.getAddr(reg_id) == mock_rando_contract.address

    assert mock_registry.numAddrs() == 2


def test_cancel_new_address(
    mock_registry,
    mock_rando_contract,
    governance,
    bob,
):
    time_lock = mock_registry.registryChangeTimeLock()

    # Start new address
    mock_registry.startAddNewAddressToRegistry(mock_rando_contract, "Contract 1", sender=governance.address)
    
    # no perms
    with boa.reverts("no perms"):
        mock_registry.cancelNewAddressToRegistry(mock_rando_contract, sender=bob)

    # success
    assert mock_registry.cancelNewAddressToRegistry(mock_rando_contract, sender=governance.address)
    
    # Verify cancel event
    cancel_log = filter_logs(mock_registry, "NewAddressCancelled")[0]
    assert cancel_log.description == "Contract 1"
    assert cancel_log.addr == mock_rando_contract.address
    assert cancel_log.initiatedBlock == boa.env.evm.patch.block_number
    assert cancel_log.confirmBlock == boa.env.evm.patch.block_number + time_lock
    assert cancel_log.registry == "MockRegistry.vy"
    
    # Verify pending state is cleared
    assert mock_registry.pendingNewAddr(mock_rando_contract).confirmBlock == 0


def test_add_new_address_validation(
    mock_registry,
    governance,
    bob,
):
    # Test zero address
    with boa.reverts("invalid addy"):
        mock_registry.startAddNewAddressToRegistry(ZERO_ADDRESS, "Zero Address", sender=governance.address)

    # Test non-contract address
    with boa.reverts("invalid addy"):
        mock_registry.startAddNewAddressToRegistry(bob, "EOA", sender=governance.address)

    # Test duplicate address
    mock_registry.startAddNewAddressToRegistry(mock_registry, "Duplicate", sender=governance.address)
    boa.env.time_travel(blocks=mock_registry.registryChangeTimeLock())
    mock_registry.confirmNewAddressToRegistry(mock_registry, sender=governance.address)
    with boa.reverts("invalid addy"):
        mock_registry.startAddNewAddressToRegistry(mock_registry, "Duplicate Again", sender=governance.address)


def test_confirm_new_address_validation(
    mock_registry,
    mock_rando_contract,
    governance,
    bob,
):
    time_lock = mock_registry.registryChangeTimeLock()

    # Test no pending operation
    with boa.reverts("time lock not reached"):
        mock_registry.confirmNewAddressToRegistry(mock_rando_contract, sender=governance.address)

    # Add initial address that we'll update
    mock_registry.startAddNewAddressToRegistry(mock_registry, "Initial Contract", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    reg_id = mock_registry.confirmNewAddressToRegistry(mock_registry, sender=governance.address)

    # Start adding new address
    mock_registry.startAddNewAddressToRegistry(mock_rando_contract, "Contract 1", sender=governance.address)
    
    # Start updating existing address to use the same contract
    mock_registry.startAddressUpdateToRegistry(reg_id, mock_rando_contract, sender=governance.address)
    
    # Confirm the update first
    boa.env.time_travel(blocks=time_lock)
    assert mock_registry.confirmAddressUpdateToRegistry(reg_id, sender=governance.address)
    
    # Now try to confirm the new address - should fail as the address is now in use
    assert mock_registry.confirmNewAddressToRegistry(mock_rando_contract, sender=governance.address) == 0
    assert mock_registry.pendingNewAddr(mock_rando_contract).confirmBlock == 0


###################
# Address Updates #
###################


def test_update_address_basic(
    mock_registry,
    mock_rando_contract,
    governance,
    bob,
):
    time_lock = mock_registry.registryChangeTimeLock()

    # Add initial address
    mock_registry.startAddNewAddressToRegistry(mock_rando_contract, "Contract 1", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    reg_id = mock_registry.confirmNewAddressToRegistry(mock_rando_contract, sender=governance.address)

    # Start update
    # no perms
    with boa.reverts("no perms"):
        mock_registry.startAddressUpdateToRegistry(reg_id, governance, sender=bob)

    # success
    assert mock_registry.startAddressUpdateToRegistry(reg_id, governance, sender=governance.address)
    
    # Verify pending update event
    pending_log = filter_logs(mock_registry, "AddressUpdatePending")[0]
    assert pending_log.regId == reg_id
    assert pending_log.description == "Contract 1"
    assert pending_log.newAddr == governance.address
    assert pending_log.prevAddr == mock_rando_contract.address
    assert pending_log.version == 1
    assert pending_log.confirmBlock == boa.env.evm.patch.block_number + time_lock
    assert pending_log.registry == "MockRegistry.vy"
    
    # Verify pending state
    pending = mock_registry.pendingAddrUpdate(reg_id)
    assert pending.newAddr == governance.address
    assert pending.initiatedBlock == boa.env.evm.patch.block_number
    assert pending.confirmBlock == pending_log.confirmBlock

    # time lock not reached
    with boa.reverts("time lock not reached"):
        mock_registry.confirmAddressUpdateToRegistry(reg_id, sender=governance.address)

    # time travel
    boa.env.time_travel(blocks=time_lock)

    # Confirm update
    assert mock_registry.confirmAddressUpdateToRegistry(reg_id, sender=governance.address)

    # Verify confirmed update event
    confirmed_log = filter_logs(mock_registry, "AddressUpdateConfirmed")[0]
    assert confirmed_log.regId == reg_id
    assert confirmed_log.description == "Contract 1"
    assert confirmed_log.newAddr == governance.address
    assert confirmed_log.prevAddr == mock_rando_contract.address
    assert confirmed_log.version == 2
    assert confirmed_log.registry == "MockRegistry.vy"

    # Verify updated info
    addr_info = mock_registry.getAddrInfo(reg_id)
    assert addr_info.addr == governance.address
    assert addr_info.version == 2
    assert mock_registry.getRegId(governance) == reg_id

    assert not mock_registry.isValidAddr(mock_rando_contract)

    # pending is cleared
    assert mock_registry.pendingAddrUpdate(reg_id).confirmBlock == 0


def test_cancel_address_update(
    mock_registry,
    mock_rando_contract,
    governance,
    bob,
):
    time_lock = mock_registry.registryChangeTimeLock()

    # Add initial address
    mock_registry.startAddNewAddressToRegistry(mock_rando_contract, "Contract 1", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    reg_id = mock_registry.confirmNewAddressToRegistry(mock_rando_contract, sender=governance.address)

    # Start update
    mock_registry.startAddressUpdateToRegistry(reg_id, mock_registry, sender=governance.address)
    
    # no perms
    with boa.reverts("no perms"):
        mock_registry.cancelAddressUpdateToRegistry(reg_id, sender=bob)

    # success
    assert mock_registry.cancelAddressUpdateToRegistry(reg_id, sender=governance.address)
    
    # Verify cancel event
    cancel_update_log = filter_logs(mock_registry, "AddressUpdateCancelled")[0]
    assert cancel_update_log.regId == reg_id
    assert cancel_update_log.description == "Contract 1"
    assert cancel_update_log.newAddr == mock_registry.address
    assert cancel_update_log.prevAddr == mock_rando_contract.address
    assert cancel_update_log.initiatedBlock == boa.env.evm.patch.block_number
    assert cancel_update_log.confirmBlock == boa.env.evm.patch.block_number + time_lock
    assert cancel_update_log.registry == "MockRegistry.vy"
    
    # Verify pending state is cleared
    assert mock_registry.pendingAddrUpdate(reg_id).confirmBlock == 0


def test_update_address_validation(
    mock_registry,
    mock_rando_contract,
    governance,
):
    time_lock = mock_registry.registryChangeTimeLock()

    # Add initial address
    mock_registry.startAddNewAddressToRegistry(mock_rando_contract, "Contract 1", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    reg_id = mock_registry.confirmNewAddressToRegistry(mock_rando_contract, sender=governance.address)

    # Test invalid reg ID
    with boa.reverts("invalid update"):
        mock_registry.startAddressUpdateToRegistry(0, mock_rando_contract, sender=governance.address)
    with boa.reverts("invalid update"):
        mock_registry.startAddressUpdateToRegistry(999, mock_rando_contract, sender=governance.address)

    # Test same address
    with boa.reverts("invalid update"):
        mock_registry.startAddressUpdateToRegistry(reg_id, mock_rando_contract, sender=governance.address)

    # Test zero address
    with boa.reverts("invalid update"):
        mock_registry.startAddressUpdateToRegistry(reg_id, ZERO_ADDRESS, sender=governance.address)


def test_confirm_address_update_validation(
    mock_registry,
    mock_rando_contract,
    governance,
):
    time_lock = mock_registry.registryChangeTimeLock()

    # Add initial address
    mock_registry.startAddNewAddressToRegistry(mock_rando_contract, "Contract 1", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    reg_id = mock_registry.confirmNewAddressToRegistry(mock_rando_contract, sender=governance.address)

    # Test no pending operation
    with boa.reverts("time lock not reached"):
        mock_registry.confirmAddressUpdateToRegistry(reg_id, sender=governance.address)

    # Test invalid address after time lock
    mock_registry.startAddressUpdateToRegistry(reg_id, mock_registry, sender=governance.address)
    boa.env.time_travel(blocks=time_lock)

    # Make address invalid by adding it to registry
    mock_registry.startAddNewAddressToRegistry(mock_registry, "Contract 2", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    mock_registry.confirmNewAddressToRegistry(mock_registry, sender=governance.address)

    # Now try to confirm the update
    assert not mock_registry.confirmAddressUpdateToRegistry(reg_id, sender=governance.address)
    assert mock_registry.pendingAddrUpdate(reg_id).confirmBlock == 0


###################
# Disable Address #
###################


def test_disable_address_basic(
    mock_registry,
    mock_rando_contract,
    governance,
    bob,
):
    time_lock = mock_registry.registryChangeTimeLock()

    # Add address
    mock_registry.startAddNewAddressToRegistry(mock_rando_contract, "Contract 1", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    reg_id = mock_registry.confirmNewAddressToRegistry(mock_rando_contract, sender=governance.address)

    # Start disable
    # no perms
    with boa.reverts("no perms"):
        mock_registry.startAddressDisableInRegistry(reg_id, sender=bob)

    # success
    assert mock_registry.startAddressDisableInRegistry(reg_id, sender=governance.address)
    
    # Verify pending disable event
    pending_log = filter_logs(mock_registry, "AddressDisablePending")[0]
    assert pending_log.regId == reg_id
    assert pending_log.description == "Contract 1"
    assert pending_log.addr == mock_rando_contract.address
    assert pending_log.version == 1
    assert pending_log.confirmBlock == boa.env.evm.patch.block_number + time_lock
    assert pending_log.registry == "MockRegistry.vy"
    
    # Verify pending state
    pending = mock_registry.pendingAddrDisable(reg_id)
    assert pending.initiatedBlock == boa.env.evm.patch.block_number
    assert pending.confirmBlock == pending_log.confirmBlock

    # time lock not reached
    with boa.reverts("time lock not reached"):
        mock_registry.confirmAddressDisableInRegistry(reg_id, sender=governance.address)

    # time travel
    boa.env.time_travel(blocks=time_lock)

    # Confirm disable
    assert mock_registry.confirmAddressDisableInRegistry(reg_id, sender=governance.address)

    # Verify confirmed disable event
    confirmed_log = filter_logs(mock_registry, "AddressDisableConfirmed")[0]
    assert confirmed_log.regId == reg_id
    assert confirmed_log.description == "Contract 1"
    assert confirmed_log.addr == mock_rando_contract.address
    assert confirmed_log.version == 2
    assert confirmed_log.registry == "MockRegistry.vy"

    # Verify disabled state
    addr_info = mock_registry.getAddrInfo(reg_id)
    assert addr_info.addr == ZERO_ADDRESS
    assert addr_info.version == 2

    assert not mock_registry.isValidAddr(mock_rando_contract)
    assert mock_registry.getRegId(mock_rando_contract) == 0

    # pending is cleared
    assert mock_registry.pendingAddrDisable(reg_id).confirmBlock == 0


def test_disable_address_validation(
    mock_registry,
    mock_rando_contract,
    governance,
):
    time_lock = mock_registry.registryChangeTimeLock()

    # Add address
    mock_registry.startAddNewAddressToRegistry(mock_rando_contract, "Contract 1", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    reg_id = mock_registry.confirmNewAddressToRegistry(mock_rando_contract, sender=governance.address)

    # Test invalid reg ID
    with boa.reverts("invalid disable"):
        mock_registry.startAddressDisableInRegistry(0, sender=governance.address)
    with boa.reverts("invalid disable"):
        mock_registry.startAddressDisableInRegistry(999, sender=governance.address)

    # Disable address
    mock_registry.startAddressDisableInRegistry(reg_id, sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    mock_registry.confirmAddressDisableInRegistry(reg_id, sender=governance.address)

    # Test disabling already disabled address
    with boa.reverts("invalid disable"):
        mock_registry.startAddressDisableInRegistry(reg_id, sender=governance.address)


def test_cancel_address_disable(
    mock_registry,
    mock_rando_contract,
    governance,
    bob,
):
    time_lock = mock_registry.registryChangeTimeLock()

    # Add initial address
    mock_registry.startAddNewAddressToRegistry(mock_rando_contract, "Contract 1", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    reg_id = mock_registry.confirmNewAddressToRegistry(mock_rando_contract, sender=governance.address)

    # Start disable
    mock_registry.startAddressDisableInRegistry(reg_id, sender=governance.address)
    
    # no perms
    with boa.reverts("no perms"):
        mock_registry.cancelAddressDisableInRegistry(reg_id, sender=bob)

    # success
    assert mock_registry.cancelAddressDisableInRegistry(reg_id, sender=governance.address)
    
    # Verify cancel event
    cancel_disable_log = filter_logs(mock_registry, "AddressDisableCancelled")[0]
    assert cancel_disable_log.regId == reg_id
    assert cancel_disable_log.description == "Contract 1"
    assert cancel_disable_log.addr == mock_rando_contract.address
    assert cancel_disable_log.initiatedBlock == boa.env.evm.patch.block_number
    assert cancel_disable_log.confirmBlock == boa.env.evm.patch.block_number + time_lock
    assert cancel_disable_log.registry == "MockRegistry.vy"
    
    # Verify pending state is cleared
    assert mock_registry.pendingAddrDisable(reg_id).confirmBlock == 0


#########
# Other #
#########


def test_time_lock_management(
    mock_registry,
    governance,
    bob,
):
    # Test setting time lock
    prev_time_lock = mock_registry.registryChangeTimeLock()
    new_time_lock = prev_time_lock + 10

    # no perms
    with boa.reverts("no perms"):
        mock_registry.setRegistryTimeLock(new_time_lock, sender=bob)

    # no change
    with boa.reverts("invalid time lock"):
        mock_registry.setRegistryTimeLock(prev_time_lock, sender=governance.address)

    # success
    assert mock_registry.setRegistryTimeLock(new_time_lock, sender=governance.address)
    
    # Verify time lock modified event
    time_lock_log = filter_logs(mock_registry, "RegistryTimeLockModified")[0]
    assert time_lock_log.newTimeLock == new_time_lock
    assert time_lock_log.prevTimeLock == prev_time_lock
    assert time_lock_log.registry == "MockRegistry.vy"
    
    assert mock_registry.registryChangeTimeLock() == new_time_lock

    # Test invalid time locks
    with boa.reverts("invalid time lock"):
        mock_registry.setRegistryTimeLock(mock_registry.minRegistryTimeLock() - 1, sender=governance.address)
    with boa.reverts("invalid time lock"):
        mock_registry.setRegistryTimeLock(mock_registry.maxRegistryTimeLock() + 1, sender=governance.address)


def test_set_registry_time_lock_after_setup(
    ripe_hq_deploy,
    governance,
    fork,
):
    new_mock_registry = boa.load(
        "contracts/mock/MockRegistry.vy",
        ripe_hq_deploy,
        0, # setting zero as initial time lock
        PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
        PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
        name="mock_registry",
    )
    # Test default value
    assert new_mock_registry.setRegistryTimeLockAfterSetup(sender=governance.address)
    assert new_mock_registry.registryChangeTimeLock() == PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"]

    # Test custom value
    with boa.reverts("already set"):
        new_mock_registry.setRegistryTimeLockAfterSetup(PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"] + 10, sender=governance.address)


def test_view_functions(
    mock_registry,
    mock_rando_contract,
    governance,
):
    time_lock = mock_registry.registryChangeTimeLock()

    # Add address
    mock_registry.startAddNewAddressToRegistry(mock_rando_contract, "Contract 1", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    reg_id = mock_registry.confirmNewAddressToRegistry(mock_rando_contract, sender=governance.address)

    # Test getNumAddrs
    assert mock_registry.getNumAddrs() == 1

    # Test getLastAddr and getLastRegId
    assert mock_registry.getLastAddr() == mock_rando_contract.address
    assert mock_registry.getLastRegId() == reg_id

    # Test getAddrDescription
    assert mock_registry.getAddrDescription(reg_id) == "Contract 1"

    # Test isValidRegId
    assert mock_registry.isValidRegId(reg_id)
    assert not mock_registry.isValidRegId(0)
    assert not mock_registry.isValidRegId(999)

