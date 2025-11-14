import pytest
import boa

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS
from conf_utils import filter_logs


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
    switchboard,
    teller,
):
    # ripe hq tokens
    assert ripe_hq.greenToken() == green_token.address
    assert ripe_hq.savingsGreen() == savings_green.address
    assert ripe_hq.ripeToken() == ripe_token.address

    # registry
    assert ripe_hq.registryChangeTimeLock() != 0
    assert ripe_hq.getNumAddrs() == 21

    # governance
    assert ripe_hq.governance() == governance.address
    assert ripe_hq.govChangeTimeLock() != 0

    # tokens
    assert ripe_token.ripeHq() == ripe_hq.address
    assert ripe_token.hqChangeTimeLock() != 0
    assert green_token.ripeHq() == ripe_hq.address
    assert green_token.hqChangeTimeLock() != 0

    # switchboard
    assert switchboard.registryChangeTimeLock() != 0
    assert switchboard.getNumAddrs() == 4
    assert switchboard.governance() == ZERO_ADDRESS

    # vault book
    assert vault_book.registryChangeTimeLock() != 0
    assert vault_book.getNumAddrs() == 4
    assert vault_book.governance() == ZERO_ADDRESS

    # price desk
    assert price_desk.registryChangeTimeLock() != 0
    assert price_desk.getNumAddrs() == 10
    assert price_desk.governance() == ZERO_ADDRESS

    # chainlink
    assert chainlink.actionTimeLock() != 0
    assert chainlink.numAssets() == 3
    assert chainlink.governance() == ZERO_ADDRESS

    # minting capabilities
    assert ripe_hq.canMintGreen(auction_house)
    assert ripe_hq.canMintGreen(credit_engine)
    assert ripe_hq.canMintRipe(lootbox)
    assert ripe_hq.canSetTokenBlacklist(switchboard)

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
    assert pending_log.canMintGreen
    assert not pending_log.canMintRipe
    assert not pending_log.canSetTokenBlacklist
    assert pending_log.confirmBlock == boa.env.evm.patch.block_number + time_lock

    # Verify pending state
    assert ripe_hq.hasPendingHqConfigChange(green_reg_id)
    pending = ripe_hq.pendingHqConfig(green_reg_id)
    assert pending.newHqConfig.canMintGreen
    assert not pending.newHqConfig.canMintRipe
    assert not pending.newHqConfig.canSetTokenBlacklist
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
    assert confirmed_log.canMintGreen
    assert not confirmed_log.canMintRipe
    assert not confirmed_log.canSetTokenBlacklist
    assert confirmed_log.initiatedBlock == pending.initiatedBlock
    assert confirmed_log.confirmBlock == pending.confirmBlock

    # Verify config is set
    config = ripe_hq.hqConfig(green_reg_id)
    assert config.canMintGreen
    assert not config.canMintRipe
    assert not config.canSetTokenBlacklist

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
    assert cancel_log.canMintGreen
    assert not cancel_log.canMintRipe
    assert not cancel_log.canSetTokenBlacklist
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
    assert pending_1.newHqConfig.canMintGreen
    assert not pending_1.newHqConfig.canMintRipe
    assert not pending_1.newHqConfig.canSetTokenBlacklist

    pending_2 = ripe_hq.pendingHqConfig(reg_id_2)
    assert not pending_2.newHqConfig.canMintGreen
    assert pending_2.newHqConfig.canMintRipe
    assert not pending_2.newHqConfig.canSetTokenBlacklist

    # Confirm both configs
    boa.env.time_travel(blocks=time_lock)
    assert ripe_hq.confirmHqConfigChange(reg_id_1, sender=governance.address)
    assert ripe_hq.confirmHqConfigChange(reg_id_2, sender=governance.address)

    # Verify final configs are set correctly
    config_1 = ripe_hq.hqConfig(reg_id_1)
    assert config_1.canMintGreen
    assert not config_1.canMintRipe
    assert not config_1.canSetTokenBlacklist

    config_2 = ripe_hq.hqConfig(reg_id_2)
    assert not config_2.canMintGreen
    assert config_2.canMintRipe
    assert not config_2.canSetTokenBlacklist


###########################
# Minting Circuit Breaker #
###########################


def test_mint_enabled_by_default(ripe_hq):
    """Test that minting is enabled by default"""
    assert ripe_hq.mintEnabled() == True


def test_disable_minting(ripe_hq, governance):
    """Test that governance can disable minting"""
    # Disable minting
    ripe_hq.setMintingEnabled(False, sender=governance.address)
    assert ripe_hq.mintEnabled() == False


def test_enable_minting(ripe_hq, governance):
    """Test that governance can re-enable minting"""
    # First disable
    ripe_hq.setMintingEnabled(False, sender=governance.address)
    assert ripe_hq.mintEnabled() == False
    
    # Then enable
    ripe_hq.setMintingEnabled(True, sender=governance.address)
    assert ripe_hq.mintEnabled() == True


def test_only_governance_can_toggle_minting(ripe_hq, alice):
    """Test that only governance can enable/disable minting"""
    # Non-governance cannot disable
    with boa.reverts("no perms"):
        ripe_hq.setMintingEnabled(False, sender=alice)
    
    # Non-governance cannot enable  
    with boa.reverts("no perms"):
        ripe_hq.setMintingEnabled(True, sender=alice)


def test_cannot_set_same_state(ripe_hq, governance):
    """Test that setting the same state fails"""
    # Minting is enabled by default, try to enable again
    with boa.reverts("already set"):
        ripe_hq.setMintingEnabled(True, sender=governance.address)
    
    # Disable minting
    ripe_hq.setMintingEnabled(False, sender=governance.address)
    
    # Try to disable again
    with boa.reverts("already set"):
        ripe_hq.setMintingEnabled(False, sender=governance.address)


def test_mint_circuit_breaker_affects_green_minting(ripe_hq, credit_engine, governance):
    """Test that disabling minting prevents GREEN token minting"""
    # Credit engine should be able to mint when enabled
    assert ripe_hq.canMintGreen(credit_engine.address) == True
    
    # Disable minting
    ripe_hq.setMintingEnabled(False, sender=governance.address)
    
    # Credit engine should not be able to mint when disabled
    assert ripe_hq.canMintGreen(credit_engine.address) == False
    
    # Re-enable minting
    ripe_hq.setMintingEnabled(True, sender=governance.address)
    
    # Should be able to mint again
    assert ripe_hq.canMintGreen(credit_engine.address) == True


def test_mint_circuit_breaker_affects_ripe_minting(ripe_hq, lootbox, governance):
    """Test that disabling minting prevents RIPE token minting"""
    # Lootbox should be able to mint when enabled
    assert ripe_hq.canMintRipe(lootbox.address) == True
    
    # Disable minting
    ripe_hq.setMintingEnabled(False, sender=governance.address)
    
    # Lootbox should not be able to mint when disabled
    assert ripe_hq.canMintRipe(lootbox.address) == False
    
    # Re-enable minting
    ripe_hq.setMintingEnabled(True, sender=governance.address)
    
    # Should be able to mint again
    assert ripe_hq.canMintRipe(lootbox.address) == True


def test_events_emitted_correctly(ripe_hq, governance):
    """Test that events are emitted with correct data"""
    # Test disable event
    ripe_hq.setMintingEnabled(False, sender=governance.address)
    events = filter_logs(ripe_hq, "MintingEnabled")
    
    assert len(events) == 1
    assert events[0].isEnabled == False
    
    # Test enable event
    ripe_hq.setMintingEnabled(True, sender=governance.address)
    events = filter_logs(ripe_hq, "MintingEnabled")
    
    assert len(events) == 1
    assert events[0].isEnabled == True


def test_mint_circuit_breaker_with_actual_minting(ripe_hq, performDeposit, credit_engine, teller, alice, governance, setGeneralConfig, setAssetConfig, alpha_token, alpha_token_whale, setGeneralDebtConfig, mock_price_source):
    """Test that the circuit breaker actually prevents token minting"""
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()

    # Setup: Alice deposits collateral and borrows
    performDeposit(alice, 1000 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Set mock price
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)
    
    # Alice can borrow when minting is enabled
    max_borrow = credit_engine.getMaxBorrowAmount(alice)
    assert max_borrow > 0
    teller.borrow(max_borrow // 2, alice, False, sender=alice)
    
    # Disable minting
    ripe_hq.setMintingEnabled(False, sender=governance.address)
    
    # Alice cannot borrow more when minting is disabled
    with boa.reverts("cannot mint"):
        teller.borrow(max_borrow // 4, alice, False, sender=alice)
    
    # Re-enable minting
    ripe_hq.setMintingEnabled(True, sender=governance.address)
    
    # Alice can borrow again
    teller.borrow(max_borrow // 4, alice, False, sender=alice)


def test_circuit_breaker_blocks_all_minters(ripe_hq, auction_house, endaoment, governance):
    """Test that circuit breaker blocks all contracts from minting"""
    # All minters should be able to mint initially
    assert ripe_hq.canMintGreen(auction_house.address) == True
    assert ripe_hq.canMintGreen(endaoment.address) == True
    
    # Disable minting
    ripe_hq.setMintingEnabled(False, sender=governance.address)
    
    # No contract should be able to mint
    assert ripe_hq.canMintGreen(auction_house.address) == False
    assert ripe_hq.canMintGreen(endaoment.address) == False
    
    # Even if a contract has permission in hqConfig, circuit breaker overrides
    assert ripe_hq.canMintGreen(ZERO_ADDRESS) == False



