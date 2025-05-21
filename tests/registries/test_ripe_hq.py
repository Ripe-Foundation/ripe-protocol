import pytest
import boa

from constants import ZERO_ADDRESS
from conf_utils import filter_logs
from config.BluePrint import PARAMS


def test_ripe_hq_and_tokens_setup(
    ripe_hq,
    green_token,
    ripe_token,
    savings_green,
    governance,
    vault_book,
    price_desk,
    chainlink,
    auction_house,
    credit_engine,
    lootbox,
    control_room,
    teller,
):
    # ripe hq tokens
    assert ripe_hq.greenToken() == green_token.address
    assert ripe_hq.savingsGreen() == savings_green.address
    assert ripe_hq.ripeToken() == ripe_token.address

    # registry
    assert ripe_hq.registryChangeTimeLock() != 0
    assert ripe_hq.getNumAddrs() == 14

    # governance
    assert ripe_hq.governance() == governance.address
    assert ripe_hq.govChangeTimeLock() != 0

    # tokens
    assert ripe_token.ripeHq() == ripe_hq.address
    assert ripe_token.hqChangeTimeLock() != 0
    assert green_token.ripeHq() == ripe_hq.address
    assert green_token.hqChangeTimeLock() != 0
    
    # vault book
    assert vault_book.registryChangeTimeLock() != 0
    assert vault_book.getNumAddrs() == 3
    assert vault_book.governance() == ZERO_ADDRESS

    # price desk
    assert price_desk.registryChangeTimeLock() != 0
    assert price_desk.getNumAddrs() == 2
    assert price_desk.governance() == ZERO_ADDRESS

    # chainlink
    assert chainlink.actionTimeLock() != 0
    assert chainlink.numAssets() == 3
    assert chainlink.governance() == ZERO_ADDRESS

    # minting capabilities
    assert ripe_hq.canMintGreen(auction_house)
    assert ripe_hq.canMintGreen(credit_engine)
    assert ripe_hq.canMintRipe(lootbox)
    assert ripe_hq.canSetTokenBlacklist(control_room)

    # cannot mint or set token blacklist
    assert not ripe_hq.canMintGreen(teller)
    assert not ripe_hq.canMintRipe(teller)
    assert not ripe_hq.canSetTokenBlacklist(teller)


#############
# Hq Config #
#############


def test_hq_config_change_basic(
    ripe_hq,
    mock_dept_can_mint_green,
    mock_dept_can_mint_ripe,
    governance,
    bob,
):
    time_lock = ripe_hq.registryChangeTimeLock()

    # Add departments that can mint
    ripe_hq.startAddNewAddressToRegistry(mock_dept_can_mint_green, "Green Minter", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    green_reg_id = ripe_hq.confirmNewAddressToRegistry(mock_dept_can_mint_green, sender=governance.address)

    # Test no perms
    with boa.reverts("no perms"):
        ripe_hq.initiateHqConfigChange(green_reg_id, True, False, False, sender=bob)

    # Start config change
    ripe_hq.initiateHqConfigChange(green_reg_id, True, False, False, sender=governance.address)
    
    # Verify pending event
    pending_log = filter_logs(ripe_hq, "HqConfigChangeInitiated")[0]
    assert pending_log.regId == green_reg_id
    assert pending_log.description == "Green Minter"
    assert pending_log.canMintGreen == True
    assert pending_log.canMintRipe == False
    assert pending_log.canSetTokenBlacklist == False
    assert pending_log.confirmBlock == boa.env.evm.patch.block_number + time_lock

    # Verify pending state
    assert ripe_hq.hasPendingHqConfigChange(green_reg_id)
    pending = ripe_hq.pendingHqConfig(green_reg_id)
    assert pending.newHqConfig.canMintGreen == True
    assert pending.newHqConfig.canMintRipe == False
    assert pending.newHqConfig.canSetTokenBlacklist == False
    assert pending.initiatedBlock == boa.env.evm.patch.block_number
    assert pending.confirmBlock == pending_log.confirmBlock

    # time lock not reached
    with boa.reverts("time lock not reached"):
        ripe_hq.confirmHqConfigChange(green_reg_id, sender=governance.address)

    # time travel
    boa.env.time_travel(blocks=time_lock)

    # Test no perms
    with boa.reverts("no perms"):
        ripe_hq.confirmHqConfigChange(green_reg_id, sender=bob)

    # Confirm config change
    assert ripe_hq.confirmHqConfigChange(green_reg_id, sender=governance.address)

    # Verify confirmed event
    confirmed_log = filter_logs(ripe_hq, "HqConfigChangeConfirmed")[0]
    assert confirmed_log.regId == green_reg_id
    assert confirmed_log.description == "Green Minter"
    assert confirmed_log.canMintGreen == True
    assert confirmed_log.canMintRipe == False
    assert confirmed_log.canSetTokenBlacklist == False
    assert confirmed_log.initiatedBlock == pending.initiatedBlock
    assert confirmed_log.confirmBlock == pending.confirmBlock

    # Verify config is set
    config = ripe_hq.hqConfig(green_reg_id)
    assert config.canMintGreen == True
    assert config.canMintRipe == False
    assert config.canSetTokenBlacklist == False

    # Verify pending is cleared
    assert not ripe_hq.hasPendingHqConfigChange(green_reg_id)


def test_hq_config_change_validation(
    ripe_hq,
    mock_dept_can_mint_green,
    mock_dept_can_mint_ripe,
    governance,
):
    time_lock = ripe_hq.registryChangeTimeLock()

    # Add departments that can mint
    ripe_hq.startAddNewAddressToRegistry(mock_dept_can_mint_green, "Green Minter", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    green_reg_id = ripe_hq.confirmNewAddressToRegistry(mock_dept_can_mint_green, sender=governance.address)

    ripe_hq.startAddNewAddressToRegistry(mock_dept_can_mint_ripe, "Ripe Minter", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    ripe_reg_id = ripe_hq.confirmNewAddressToRegistry(mock_dept_can_mint_ripe, sender=governance.address)

    # Test invalid reg ID
    with boa.reverts("invalid hq config"):
        ripe_hq.initiateHqConfigChange(0, True, False, False, sender=governance.address)
    with boa.reverts("invalid hq config"):
        ripe_hq.initiateHqConfigChange(999, True, False, False, sender=governance.address)

    # Test token reg IDs cannot mint
    with boa.reverts("invalid hq config"):
        ripe_hq.initiateHqConfigChange(1, True, False, False, sender=governance.address)  # green token
    with boa.reverts("invalid hq config"):
        ripe_hq.initiateHqConfigChange(2, True, False, False, sender=governance.address)  # savings green
    with boa.reverts("invalid hq config"):
        ripe_hq.initiateHqConfigChange(3, True, False, False, sender=governance.address)  # ripe token

    # Test department must support minting
    with boa.reverts("invalid hq config"):
        ripe_hq.initiateHqConfigChange(green_reg_id, False, True, False, sender=governance.address)  # can't mint ripe
    with boa.reverts("invalid hq config"):
        ripe_hq.initiateHqConfigChange(ripe_reg_id, True, False, False, sender=governance.address)  # can't mint green


def test_hq_config_change_cancel(
    ripe_hq,
    mock_dept_can_mint_green,
    governance,
    bob,
):
    time_lock = ripe_hq.registryChangeTimeLock()

    # Add department that can mint
    ripe_hq.startAddNewAddressToRegistry(mock_dept_can_mint_green, "Green Minter", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    green_reg_id = ripe_hq.confirmNewAddressToRegistry(mock_dept_can_mint_green, sender=governance.address)

    # Start config change
    ripe_hq.initiateHqConfigChange(green_reg_id, True, False, False, sender=governance.address)

    # Test no perms
    with boa.reverts("no perms"):
        ripe_hq.cancelHqConfigChange(green_reg_id, sender=bob)

    # Test no pending
    with boa.reverts("no pending change"):
        ripe_hq.cancelHqConfigChange(999, sender=governance.address)

    # Cancel config change
    assert ripe_hq.cancelHqConfigChange(green_reg_id, sender=governance.address)

    # Verify cancel event
    cancel_log = filter_logs(ripe_hq, "HqConfigChangeCancelled")[0]
    assert cancel_log.regId == green_reg_id
    assert cancel_log.description == "Green Minter"
    assert cancel_log.canMintGreen == True
    assert cancel_log.canMintRipe == False
    assert cancel_log.canSetTokenBlacklist == False
    assert cancel_log.initiatedBlock == boa.env.evm.patch.block_number
    assert cancel_log.confirmBlock == boa.env.evm.patch.block_number + time_lock

    # Verify pending is cleared
    assert not ripe_hq.hasPendingHqConfigChange(green_reg_id)


def test_hq_config_change_invalid_after_time_lock(
    ripe_hq,
    mock_dept_can_mint_green,
    mock_dept_can_mint_ripe,
    governance,
):
    time_lock = ripe_hq.registryChangeTimeLock()

    # Add initial department that can mint green
    ripe_hq.startAddNewAddressToRegistry(mock_dept_can_mint_green, "Green Minter", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    reg_id = ripe_hq.confirmNewAddressToRegistry(mock_dept_can_mint_green, sender=governance.address)

    # Start config change for green minting
    ripe_hq.initiateHqConfigChange(reg_id, True, False, False, sender=governance.address)

    # Update the address to one that can't mint green
    ripe_hq.startAddressUpdateToRegistry(reg_id, mock_dept_can_mint_ripe, sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    assert ripe_hq.confirmAddressUpdateToRegistry(reg_id, sender=governance.address)

    # Now try to confirm the config change - should fail as the address can no longer mint green
    assert not ripe_hq.confirmHqConfigChange(reg_id, sender=governance.address)
    assert not ripe_hq.hasPendingHqConfigChange(reg_id)


def test_token_specific_restrictions(
    ripe_hq,
    governance,
):
    # Test token getters
    assert ripe_hq.greenToken() == ripe_hq.getAddr(1)
    assert ripe_hq.savingsGreen() == ripe_hq.getAddr(2)
    assert ripe_hq.ripeToken() == ripe_hq.getAddr(3)

    # Test that token IDs cannot be configured for minting
    with boa.reverts("invalid hq config"):
        ripe_hq.initiateHqConfigChange(1, True, False, False, sender=governance.address)  # green token
    with boa.reverts("invalid hq config"):
        ripe_hq.initiateHqConfigChange(2, True, False, False, sender=governance.address)  # savings green
    with boa.reverts("invalid hq config"):
        ripe_hq.initiateHqConfigChange(3, True, False, False, sender=governance.address)  # ripe token

    # Test that token IDs cannot set their own blacklist
    with boa.reverts("invalid hq config"):
        ripe_hq.initiateHqConfigChange(1, False, False, True, sender=governance.address)  # green token
    with boa.reverts("invalid hq config"):
        ripe_hq.initiateHqConfigChange(2, False, False, True, sender=governance.address)  # savings green
    with boa.reverts("invalid hq config"):
        ripe_hq.initiateHqConfigChange(3, False, False, True, sender=governance.address)  # ripe token


def test_minting_capability_validation(
    ripe_hq,
    mock_dept_can_mint_green,
    governance,
):
    time_lock = ripe_hq.registryChangeTimeLock()

    # Add department that can mint green
    ripe_hq.startAddNewAddressToRegistry(mock_dept_can_mint_green, "Green Minter", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    reg_id = ripe_hq.confirmNewAddressToRegistry(mock_dept_can_mint_green, sender=governance.address)

    # Test that both contract config and department capability are required
    assert not ripe_hq.canMintGreen(mock_dept_can_mint_green)  # No config yet
    ripe_hq.initiateHqConfigChange(reg_id, True, False, False, sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    assert ripe_hq.confirmHqConfigChange(reg_id, sender=governance.address)
    assert ripe_hq.canMintGreen(mock_dept_can_mint_green)  # Both config and capability

    # Test that zero address cannot mint
    assert not ripe_hq.canMintGreen(ZERO_ADDRESS)
    assert not ripe_hq.canMintRipe(ZERO_ADDRESS)

    # Test that disabled addresses cannot mint
    ripe_hq.startAddressDisableInRegistry(reg_id, sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    assert ripe_hq.confirmAddressDisableInRegistry(reg_id, sender=governance.address)
    assert not ripe_hq.canMintGreen(mock_dept_can_mint_green)


def test_fund_recovery(
    ripe_hq,
    governance,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    charlie_token,
    bravo_token_whale,
    charlie_token_whale,
    sally,
):
    # Test no perms
    with boa.reverts("no perms"):
        ripe_hq.recoverFunds(bob, alpha_token, sender=bob)

    # Test invalid recipient
    with boa.reverts("invalid recipient or asset"):
        ripe_hq.recoverFunds(ZERO_ADDRESS, alpha_token, sender=governance.address)

    # Test invalid asset
    with boa.reverts("invalid recipient or asset"):
        ripe_hq.recoverFunds(bob, ZERO_ADDRESS, sender=governance.address)

    # Test zero balance
    with boa.reverts("nothing to recover"):
        ripe_hq.recoverFunds(bob, alpha_token, sender=governance.address)

    # Test successful recovery
    alpha_token.transfer(ripe_hq, 1000, sender=alpha_token_whale)
    ripe_hq.recoverFunds(bob, alpha_token, sender=governance.address)
    assert alpha_token.balanceOf(bob) == 1000

    # Test multiple asset recovery
    alpha_token.transfer(ripe_hq, 2000, sender=alpha_token_whale)
    bravo_token.transfer(ripe_hq, 2000, sender=bravo_token_whale)
    charlie_token.transfer(ripe_hq, 2000, sender=charlie_token_whale)

    assets = [alpha_token, bravo_token, charlie_token]
    ripe_hq.recoverFundsMany(sally, assets, sender=governance.address)
    assert alpha_token.balanceOf(sally) == 2000
    assert bravo_token.balanceOf(sally) == 2000
    assert charlie_token.balanceOf(sally) == 2000


def test_multiple_pending_configs(
    ripe_hq,
    mock_dept_can_mint_green,
    mock_dept_can_mint_ripe,
    governance,
):
    time_lock = ripe_hq.registryChangeTimeLock()

    # Add first department that can mint green
    ripe_hq.startAddNewAddressToRegistry(mock_dept_can_mint_green, "Green Minter", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    reg_id_1 = ripe_hq.confirmNewAddressToRegistry(mock_dept_can_mint_green, sender=governance.address)

    # Add second department that can mint ripe
    ripe_hq.startAddNewAddressToRegistry(mock_dept_can_mint_ripe, "Ripe Minter", sender=governance.address)
    boa.env.time_travel(blocks=time_lock)
    reg_id_2 = ripe_hq.confirmNewAddressToRegistry(mock_dept_can_mint_ripe, sender=governance.address)

    # Start multiple pending configs
    ripe_hq.initiateHqConfigChange(reg_id_1, True, False, False, sender=governance.address)
    ripe_hq.initiateHqConfigChange(reg_id_2, False, True, False, sender=governance.address)

    # Verify both are pending
    assert ripe_hq.hasPendingHqConfigChange(reg_id_1)
    assert ripe_hq.hasPendingHqConfigChange(reg_id_2)

    # Verify pending configs have correct values
    pending_1 = ripe_hq.pendingHqConfig(reg_id_1)
    assert pending_1.newHqConfig.canMintGreen == True
    assert pending_1.newHqConfig.canMintRipe == False
    assert pending_1.newHqConfig.canSetTokenBlacklist == False

    pending_2 = ripe_hq.pendingHqConfig(reg_id_2)
    assert pending_2.newHqConfig.canMintGreen == False
    assert pending_2.newHqConfig.canMintRipe == True
    assert pending_2.newHqConfig.canSetTokenBlacklist == False

    # Confirm both configs
    boa.env.time_travel(blocks=time_lock)
    assert ripe_hq.confirmHqConfigChange(reg_id_1, sender=governance.address)
    assert ripe_hq.confirmHqConfigChange(reg_id_2, sender=governance.address)

    # Verify final configs are set correctly
    config_1 = ripe_hq.hqConfig(reg_id_1)
    assert config_1.canMintGreen == True
    assert config_1.canMintRipe == False
    assert config_1.canSetTokenBlacklist == False

    config_2 = ripe_hq.hqConfig(reg_id_2)
    assert config_2.canMintGreen == False
    assert config_2.canMintRipe == True
    assert config_2.canSetTokenBlacklist == False
