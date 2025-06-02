import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from conf_utils import filter_logs
from config.BluePrint import PARAMS


@pytest.fixture(scope="module")
def mock_ripe_hq(governance, fork, green_token, savings_green, ripe_token):
    return boa.load(
        "contracts/registries/RipeHq.vy",
        green_token,
        savings_green,
        ripe_token,
        governance,
        PARAMS[fork]["RIPE_HQ_MIN_GOV_TIMELOCK"],
        PARAMS[fork]["RIPE_HQ_MAX_GOV_TIMELOCK"],
        PARAMS[fork]["RIPE_HQ_MIN_REG_TIMELOCK"],
        PARAMS[fork]["RIPE_HQ_MAX_REG_TIMELOCK"],
    )


# Basic ERC20 Tests
def test_green_token_basic_info(green_token):
    """Test basic ERC20 token information for Green Token"""
    assert green_token.name() == "Green USD Stablecoin"
    assert green_token.symbol() == "GREEN"
    assert green_token.decimals() == 18
    assert green_token.totalSupply() == 1_000_000 * EIGHTEEN_DECIMALS


def test_green_token_transfer(green_token, whale, bob, alice):
    """Test basic ERC20 transfer functionality for Green Token"""
    initial_balance = green_token.balanceOf(whale)
    transfer_amount = 100 * EIGHTEEN_DECIMALS

    # Test successful transfer
    assert green_token.transfer(bob, transfer_amount, sender=whale)

    # Test transfer event
    log = filter_logs(green_token, "Transfer")[0]
    assert log.sender == whale
    assert log.recipient == bob
    assert log.amount == transfer_amount

    assert green_token.balanceOf(whale) == initial_balance - transfer_amount
    assert green_token.balanceOf(bob) == transfer_amount

    # Test transfer to zero address
    with boa.reverts("invalid recipient"):
        green_token.transfer(ZERO_ADDRESS, transfer_amount, sender=whale)

    # Test transfer to self
    with boa.reverts("invalid recipient"):
        green_token.transfer(green_token.address, transfer_amount, sender=whale)

    # Test transfer zero amount
    with boa.reverts("cannot transfer 0 amount"):
        green_token.transfer(bob, 0, sender=whale)

    # Test insufficient balance
    with boa.reverts("insufficient funds"):
        green_token.transfer(whale, transfer_amount, sender=alice)


def test_green_token_approve(green_token, whale, bob):
    """Test ERC20 approve functionality for Green Token"""
    approve_amount = 100 * EIGHTEEN_DECIMALS

    # Test successful approval
    assert green_token.approve(bob, approve_amount, sender=whale)

    # Test approval event
    log = filter_logs(green_token, "Approval")[0]
    assert log.owner == whale
    assert log.spender == bob
    assert log.amount == approve_amount

    assert green_token.allowance(whale, bob) == approve_amount

    # Test approve zero address
    with boa.reverts("invalid spender"):
        green_token.approve(ZERO_ADDRESS, approve_amount, sender=whale)


def test_green_token_transfer_from(green_token, whale, bob, alice):
    """Test ERC20 transferFrom functionality for Green Token"""
    approve_amount = 100 * EIGHTEEN_DECIMALS
    transfer_amount = 50 * EIGHTEEN_DECIMALS

    # Approve bob to spend governance's tokens
    green_token.approve(bob, approve_amount, sender=whale)

    # Test successful transferFrom
    assert green_token.transferFrom(whale, alice, transfer_amount, sender=bob)

    # Test transferFrom event
    log = filter_logs(green_token, "Transfer")[0]
    assert log.sender == whale
    assert log.recipient == alice
    assert log.amount == transfer_amount

    assert green_token.balanceOf(alice) == transfer_amount
    assert green_token.allowance(whale, bob) == approve_amount - transfer_amount

    # Test insufficient allowance
    with boa.reverts("insufficient allowance"):
        green_token.transferFrom(whale, alice, approve_amount, sender=bob)

    # Test transferFrom zero address
    with boa.reverts("invalid recipient"):
        green_token.transferFrom(whale, ZERO_ADDRESS, transfer_amount, sender=bob)

    # Test transferFrom to self
    with boa.reverts("invalid recipient"):
        green_token.transferFrom(whale, green_token.address, transfer_amount, sender=bob)

    # Test transferFrom zero amount
    with boa.reverts("cannot transfer 0 amount"):
        green_token.transferFrom(whale, alice, 0, sender=bob)


def test_green_token_increase_decrease_allowance(green_token, whale, bob):
    """Test increaseAllowance and decreaseAllowance functionality for Green Token"""
    initial_amount = 100 * EIGHTEEN_DECIMALS
    increase_amount = 50 * EIGHTEEN_DECIMALS
    decrease_amount = 30 * EIGHTEEN_DECIMALS

    # Set initial allowance
    green_token.approve(bob, initial_amount, sender=whale)

    # Test increaseAllowance
    assert green_token.increaseAllowance(bob, increase_amount, sender=whale)
    assert green_token.allowance(whale, bob) == initial_amount + increase_amount

    # Test decreaseAllowance
    assert green_token.decreaseAllowance(bob, decrease_amount, sender=whale)
    assert green_token.allowance(whale, bob) == initial_amount + increase_amount - decrease_amount

    # Test decreaseAllowance with amount greater than current allowance
    current_allowance = green_token.allowance(whale, bob)
    assert green_token.decreaseAllowance(bob, current_allowance + 1, sender=whale)
    assert green_token.allowance(whale, bob) == 0  # Should be capped at 0

    # Test increaseAllowance with max uint256
    max_uint = 2**256 - 1
    current_allowance = green_token.allowance(whale, bob)
    max_increase = max_uint - current_allowance
    assert green_token.increaseAllowance(bob, max_uint, sender=whale)
    assert green_token.allowance(whale, bob) == max_uint  # Should be capped at max_uint


def test_green_token_pause_functionality(green_token, whale, bob, governance):
    """Test token pause functionality"""
    # Test initial state
    assert not green_token.isPaused()

    # Test pause
    green_token.pause(True, sender=governance.address)
    assert green_token.isPaused()

    # Test operations when paused
    with boa.reverts("token paused"):
        green_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=whale)
    
    with boa.reverts("token paused"):
        green_token.approve(bob, 100 * EIGHTEEN_DECIMALS, sender=whale)
    
    with boa.reverts("token paused"):
        green_token.increaseAllowance(bob, 100 * EIGHTEEN_DECIMALS, sender=whale)
    
    with boa.reverts("token paused"):
        green_token.decreaseAllowance(bob, 100 * EIGHTEEN_DECIMALS, sender=whale)
    
    with boa.reverts("token paused"):
        green_token.burn(100 * EIGHTEEN_DECIMALS, sender=whale)

    # Test unpause
    green_token.pause(False, sender=governance.address)
    assert not green_token.isPaused()

    # Verify operations work again
    assert green_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=whale)
    assert green_token.approve(bob, 100 * EIGHTEEN_DECIMALS, sender=whale)


def test_green_token_blacklist_functionality(green_token, whale, bob, switchboard_one, governance):
    """Test token blacklist functionality"""
    # Test initial state
    assert not green_token.blacklisted(whale)
    assert not green_token.blacklisted(bob)

    # Test blacklist
    green_token.setBlacklist(whale, True, sender=switchboard_one.address)
    assert green_token.blacklisted(whale)

    # Test operations when blacklisted
    with boa.reverts("sender blacklisted"):
        green_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=whale)
    
    with boa.reverts("owner blacklisted"):
        green_token.approve(bob, 100 * EIGHTEEN_DECIMALS, sender=whale)

    # Test blacklist spender
    green_token.setBlacklist(bob, True, sender=switchboard_one.address)
    assert green_token.blacklisted(bob)

    green_token.setBlacklist(whale, False, sender=switchboard_one.address)

    # Test operations with blacklisted spender
    with boa.reverts("spender blacklisted"):
        green_token.approve(bob, 100 * EIGHTEEN_DECIMALS, sender=whale)

    green_token.setBlacklist(whale, True, sender=switchboard_one.address)

    # Test burn blacklisted tokens
    initial_balance = green_token.balanceOf(whale)
    green_token.burnBlacklistTokens(whale, sender=governance.address)
    assert green_token.balanceOf(whale) == 0
    assert green_token.totalSupply() == initial_balance - initial_balance

    # Test unblacklist
    green_token.setBlacklist(whale, False, sender=switchboard_one.address)
    assert not green_token.blacklisted(whale)


def test_green_token_ripe_hq_changes(green_token, governance, ripe_hq_deploy, mock_ripe_hq):
    """Test RipeHq change functionality"""

    # Test initial state
    assert not green_token.hasPendingHqChange()
    
    # Test initiate hq change
    green_token.initiateHqChange(mock_ripe_hq, sender=governance.address)
    assert green_token.hasPendingHqChange()
    
    # Test confirm before time lock
    with boa.reverts("time lock not reached"):
        green_token.confirmHqChange(sender=governance.address)
    
    # Time travel past time lock
    boa.env.time_travel(blocks=green_token.hqChangeTimeLock())
    
    # Test confirm hq change
    assert green_token.confirmHqChange(sender=governance.address)
    assert not green_token.hasPendingHqChange()
    assert green_token.ripeHq() == mock_ripe_hq.address
    
    # Test cancel hq change
    green_token.initiateHqChange(ripe_hq_deploy, sender=governance.address)
    green_token.cancelHqChange(sender=governance.address)
    assert not green_token.hasPendingHqChange()


def test_green_token_time_lock_config(green_token, governance):
    """Test time lock configuration"""
    min_time_lock = green_token.minHqTimeLock()
    max_time_lock = green_token.maxHqTimeLock()
    
    # Test invalid time locks
    with boa.reverts("invalid time lock"):
        green_token.setHqChangeTimeLock(min_time_lock - 1, sender=governance.address)
    
    with boa.reverts("invalid time lock"):
        green_token.setHqChangeTimeLock(max_time_lock + 1, sender=governance.address)
    
    # Test valid time lock
    new_time_lock = min_time_lock + 100
    assert green_token.setHqChangeTimeLock(new_time_lock, sender=governance.address)
    assert green_token.hqChangeTimeLock() == new_time_lock


def test_green_token_edge_cases(green_token, whale, bob, alice):
    """Test edge cases for token operations"""
    # Test transfer to self
    with boa.reverts("invalid recipient"):
        green_token.transfer(green_token.address, 100 * EIGHTEEN_DECIMALS, sender=whale)
    
    # Test transfer to zero address
    with boa.reverts("invalid recipient"):
        green_token.transfer(ZERO_ADDRESS, 100 * EIGHTEEN_DECIMALS, sender=whale)
    
    # Test approve zero address
    with boa.reverts("invalid spender"):
        green_token.approve(ZERO_ADDRESS, 100 * EIGHTEEN_DECIMALS, sender=whale)
    
    # Test transferFrom to self
    green_token.approve(bob, 100 * EIGHTEEN_DECIMALS, sender=whale)
    with boa.reverts("invalid recipient"):
        green_token.transferFrom(whale, green_token.address, 50 * EIGHTEEN_DECIMALS, sender=bob)
    
    # Test transferFrom to zero address
    with boa.reverts("invalid recipient"):
        green_token.transferFrom(whale, ZERO_ADDRESS, 50 * EIGHTEEN_DECIMALS, sender=bob)
    
    # Test transfer zero amount
    with boa.reverts("cannot transfer 0 amount"):
        green_token.transfer(bob, 0, sender=whale)
    
    # Test transferFrom zero amount
    with boa.reverts("cannot transfer 0 amount"):
        green_token.transferFrom(whale, alice, 0, sender=bob)
    
    # Test burn zero amount (should succeed)
    initial_balance = green_token.balanceOf(whale)
    initial_supply = green_token.totalSupply()
    assert green_token.burn(0, sender=whale)
    assert green_token.balanceOf(whale) == initial_balance
    assert green_token.totalSupply() == initial_supply


def test_green_token_minting_edge_cases(green_token, governance, whale, credit_engine, switchboard_one, alice):
    """Test minting edge cases"""
    # Test minting to zero address
    with boa.reverts("invalid recipient"):
        green_token.mint(ZERO_ADDRESS, 100 * EIGHTEEN_DECIMALS, sender=credit_engine.address)
    
    # Test minting to self
    with boa.reverts("invalid recipient"):
        green_token.mint(green_token.address, 100 * EIGHTEEN_DECIMALS, sender=credit_engine.address)
    
    # Test minting to blacklisted address
    green_token.setBlacklist(whale, True, sender=switchboard_one.address)
    with boa.reverts("blacklisted"):
        green_token.mint(whale, 100 * EIGHTEEN_DECIMALS, sender=credit_engine.address)
    
    # Test minting when paused
    green_token.pause(True, sender=governance.address)
    with boa.reverts("token paused"):
        green_token.mint(alice, 100 * EIGHTEEN_DECIMALS, sender=credit_engine.address)


def test_green_token_transfer_edge_cases(green_token, whale, bob, governance, switchboard_one):
    """Test transfer edge cases"""
    # Test transfer with insufficient balance
    with boa.reverts("insufficient funds"):
        green_token.transfer(whale, 100 * EIGHTEEN_DECIMALS, sender=bob)
    
    # Test transfer when paused
    green_token.pause(True, sender=governance.address)
    with boa.reverts("token paused"):
        green_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.pause(False, sender=governance.address)

    # Test transfer when sender is blacklisted
    green_token.setBlacklist(whale, True, sender=switchboard_one.address)
    with boa.reverts("sender blacklisted"):
        green_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=whale)
    
    # Test transfer when recipient is blacklisted
    green_token.setBlacklist(whale, False, sender=switchboard_one.address)
    green_token.setBlacklist(bob, True, sender=switchboard_one.address)
    with boa.reverts("recipient blacklisted"):
        green_token.transfer(bob, 100 * EIGHTEEN_DECIMALS, sender=whale)


def test_green_token_transfer_from_edge_cases(green_token, whale, bob, alice, governance, switchboard_one):
    """Test transferFrom edge cases"""
    # Set up initial state
    transfer_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(whale, transfer_amount, sender=whale)
    
    # Test transferFrom with infinite allowance
    green_token.approve(bob, MAX_UINT256, sender=whale)
    assert green_token.transferFrom(whale, alice, transfer_amount, sender=bob)
    assert green_token.allowance(whale, bob) == MAX_UINT256
    
    # Test transferFrom when spender is blacklisted
    green_token.setBlacklist(bob, True, sender=switchboard_one.address)
    with boa.reverts("spender blacklisted"):
        green_token.transferFrom(whale, alice, transfer_amount, sender=bob)
    
    # Test transferFrom when paused
    green_token.setBlacklist(bob, False, sender=switchboard_one.address)
    green_token.pause(True, sender=governance.address)
    with boa.reverts("token paused"):
        green_token.transferFrom(whale, alice, transfer_amount, sender=bob)
    green_token.pause(False, sender=governance.address)

    green_token.transfer(alice, green_token.balanceOf(whale), sender=whale)

    # Test transferFrom with insufficient balance
    with boa.reverts("insufficient funds"):
        green_token.transferFrom(whale, alice, transfer_amount, sender=bob)


def test_green_token_ripe_hq_edge_cases(green_token, governance, bob, mock_ripe_hq, mock_rando_contract):
    """Test RipeHq edge cases"""
    # Test invalid RipeHq address (zero address)
    with boa.reverts("invalid new hq"):
        green_token.initiateHqChange(ZERO_ADDRESS, sender=governance.address)
    
    # Test invalid RipeHq address (non-contract)
    with boa.reverts("invalid new hq"):
        green_token.initiateHqChange(bob, sender=governance.address)
    
    # Test invalid RipeHq address (same as current)
    with boa.reverts("invalid new hq"):
        green_token.initiateHqChange(green_token.ripeHq(), sender=governance.address)
    
    # Initiate a gov change in the mock RipeHq
    mock_ripe_hq.startGovernanceChange(mock_rando_contract, sender=governance.address)
    assert mock_ripe_hq.hasPendingGovChange()
    
    # Try to change to RipeHq with pending gov change
    with boa.reverts("invalid new hq"):
        green_token.initiateHqChange(mock_ripe_hq, sender=governance.address)


def test_green_token_blacklist_edge_cases(green_token, governance, switchboard_one, credit_engine):
    """Test blacklist edge cases"""
    # Test blacklisting self
    with boa.reverts("invalid blacklist recipient"):
        green_token.setBlacklist(green_token.address, True, sender=switchboard_one.address)
    
    # Test blacklisting zero address
    with boa.reverts("invalid blacklist recipient"):
        green_token.setBlacklist(ZERO_ADDRESS, True, sender=switchboard_one.address)
    
    # Test burning blacklisted tokens with specific amount
    test_address = boa.env.generate_address()
    green_token.mint(test_address, 1000 * EIGHTEEN_DECIMALS, sender=credit_engine.address)
    green_token.setBlacklist(test_address, True, sender=switchboard_one.address)
    
    burn_amount = 500 * EIGHTEEN_DECIMALS
    green_token.burnBlacklistTokens(test_address, burn_amount, sender=governance.address)
    assert green_token.balanceOf(test_address) == 500 * EIGHTEEN_DECIMALS


def test_green_token_time_lock_edge_cases(green_token, governance):
    """Test time lock edge cases"""
    min_time_lock = green_token.minHqTimeLock()
    max_time_lock = green_token.maxHqTimeLock()
    
    # Test time lock bounds
    with boa.reverts("invalid time lock"):
        green_token.setHqChangeTimeLock(min_time_lock - 1, sender=governance.address)
    
    with boa.reverts("invalid time lock"):
        green_token.setHqChangeTimeLock(max_time_lock + 1, sender=governance.address)
    
    # Test valid time lock changes
    new_time_lock = min_time_lock + 100
    assert green_token.setHqChangeTimeLock(new_time_lock, sender=governance.address)
    
    # Test time lock change event
    log = filter_logs(green_token, "HqChangeTimeLockModified")[0]
    assert log.newTimeLock == new_time_lock

    assert green_token.hqChangeTimeLock() == new_time_lock


def test_green_token_events(green_token, whale, bob, governance, switchboard_one, mock_ripe_hq):
    """Test token events"""
    # Test Transfer event
    transfer_amount = 100 * EIGHTEEN_DECIMALS
    assert green_token.transfer(bob, transfer_amount, sender=whale)
    
    transfer_log = filter_logs(green_token, "Transfer")[0]
    assert transfer_log.sender == whale
    assert transfer_log.recipient == bob
    assert transfer_log.amount == transfer_amount
    
    # Test Approval event
    approve_amount = 200 * EIGHTEEN_DECIMALS
    assert green_token.approve(bob, approve_amount, sender=whale)
    
    approval_log = filter_logs(green_token, "Approval")[0]
    assert approval_log.owner == whale
    assert approval_log.spender == bob
    assert approval_log.amount == approve_amount
    
    # Test BlacklistModified event
    assert green_token.setBlacklist(bob, True, sender=switchboard_one.address)
    
    blacklist_log = filter_logs(green_token, "BlacklistModified")[0]
    assert blacklist_log.addr == bob
    assert blacklist_log.isBlacklisted == True
    
    # Test TokenPauseModified event
    green_token.pause(True, sender=governance.address)
    
    pause_log = filter_logs(green_token, "TokenPauseModified")[0]
    assert pause_log.isPaused == True
      
    green_token.initiateHqChange(mock_ripe_hq, sender=governance.address)
    
    hq_change_log = filter_logs(green_token, "HqChangeInitiated")[0]
    assert hq_change_log.prevHq == green_token.ripeHq()
    assert hq_change_log.newHq == mock_ripe_hq.address
    assert hq_change_log.confirmBlock == boa.env.evm.patch.block_number + green_token.hqChangeTimeLock()

