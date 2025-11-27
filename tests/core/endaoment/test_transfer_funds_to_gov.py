import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from conf_utils import filter_logs


def test_transfer_funds_basic(
    endaoment,
    endaoment_funds,
    switchboard_charlie,
    governance,
    alpha_token,
    alpha_token_whale,
):
    """Test basic transfer of funds to governance"""
    transfer_amount = 1000 * EIGHTEEN_DECIMALS

    # Fund endaoment_funds with ALPHA tokens
    alpha_token.transfer(endaoment_funds.address, transfer_amount, sender=alpha_token_whale)
    initial_balance = alpha_token.balanceOf(endaoment_funds.address)
    assert initial_balance == transfer_amount
    
    # Get initial governance balance
    initial_gov_balance = alpha_token.balanceOf(governance.address)
    
    # Execute transfer through switchboard
    tx = endaoment.transferFundsToGov(
        alpha_token.address,
        transfer_amount,
        sender=switchboard_charlie.address
    )
    
    # Check return values
    amount_transferred, usd_value = tx
    assert amount_transferred == transfer_amount
    # USD value will be 0 since price feed not configured for test token
    assert usd_value == 0
    
    # Verify balances
    assert alpha_token.balanceOf(endaoment_funds.address) == initial_balance - transfer_amount
    assert alpha_token.balanceOf(governance.address) == initial_gov_balance + transfer_amount
    
    # Check event
    events = filter_logs(endaoment, "WalletAction")
    assert len(events) == 1
    event = events[0]
    assert event.op == 1  # Transfer operation
    assert event.asset1 == alpha_token.address
    assert event.asset2 == governance.address
    assert event.amount1 == transfer_amount
    assert event.amount2 == 0
    assert event.usdValue == 0  # No price feed configured for test token
    assert event.legoId == 0


def test_transfer_funds_max_value(
    endaoment,
    endaoment_funds,
    switchboard_charlie,
    governance,
    bravo_token,
    bravo_token_whale,
):
    """Test transfer with max_value (transfers entire balance)"""
    fund_amount = 2500 * EIGHTEEN_DECIMALS

    # Fund endaoment_funds
    bravo_token.transfer(endaoment_funds.address, fund_amount, sender=bravo_token_whale)
    initial_balance = bravo_token.balanceOf(endaoment_funds.address)
    
    # Get initial governance balance
    initial_gov_balance = bravo_token.balanceOf(governance.address)
    
    # Execute transfer with max_value (default parameter)
    tx = endaoment.transferFundsToGov(
        bravo_token.address,
        sender=switchboard_charlie.address
    )
    
    amount_transferred, usd_value = tx
    assert amount_transferred == initial_balance
    assert usd_value == 0  # No price feed configured for test token
    assert bravo_token.balanceOf(endaoment_funds.address) == 0
    assert bravo_token.balanceOf(governance.address) == initial_gov_balance + initial_balance


def test_transfer_funds_partial_when_requested_exceeds_balance(
    endaoment,
    endaoment_funds,
    switchboard_charlie,
    governance,
    charlie_token,
    charlie_token_whale,
):
    """Test partial transfer when requested amount exceeds balance"""
    # Charlie token has 6 decimals
    balance_amount = 1000 * 10**6
    request_amount = 2000 * 10**6  # Request more than available

    # Fund endaoment_funds with less than requested
    charlie_token.transfer(endaoment_funds.address, balance_amount, sender=charlie_token_whale)
    initial_gov_balance = charlie_token.balanceOf(governance.address)
    
    # Execute transfer
    tx = endaoment.transferFundsToGov(
        charlie_token.address,
        request_amount,
        sender=switchboard_charlie.address
    )
    
    amount_transferred, _ = tx
    assert amount_transferred == balance_amount  # Should transfer available balance
    assert charlie_token.balanceOf(endaoment_funds.address) == 0
    assert charlie_token.balanceOf(governance.address) == initial_gov_balance + balance_amount


def test_transfer_funds_unauthorized_caller(
    endaoment,
    alice,
    alpha_token,
):
    """Test that non-switchboard addresses cannot call transferFundsToGov"""
    with boa.reverts("no perms"):
        endaoment.transferFundsToGov(
            alpha_token.address,
            1000 * EIGHTEEN_DECIMALS,
            sender=alice
        )


def test_transfer_funds_when_paused(
    endaoment,
    endaoment_funds,
    switchboard_charlie,
    governance,
    alpha_token,
    alpha_token_whale,
):
    """Test that transfer fails when contract is paused"""
    # Pause the contract
    switchboard_charlie.pause(endaoment.address, True, sender=governance.address)

    # Fund endaoment_funds
    alpha_token.transfer(endaoment_funds.address, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    
    # Try to transfer
    with boa.reverts("contract paused"):
        endaoment.transferFundsToGov(
            alpha_token.address,
            sender=switchboard_charlie.address
        )
    
    # Unpause for cleanup
    switchboard_charlie.pause(endaoment.address, False, sender=governance.address)


def test_transfer_funds_no_balance(
    endaoment,
    endaoment_funds,
    switchboard_charlie,
    delta_token,
):
    """Test that transfer fails when there's no balance"""
    # Ensure endaoment_funds has no delta tokens
    assert delta_token.balanceOf(endaoment_funds.address) == 0
    
    with boa.reverts("no amt"):
        endaoment.transferFundsToGov(
            delta_token.address,
            1000 * EIGHTEEN_DECIMALS,
            sender=switchboard_charlie.address
        )


def test_transfer_funds_multiple_tokens(
    endaoment,
    endaoment_funds,
    switchboard_charlie,
    governance,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
):
    """Test transferring multiple different tokens"""
    alpha_amount = 1000 * EIGHTEEN_DECIMALS
    bravo_amount = 500 * EIGHTEEN_DECIMALS

    # Fund endaoment_funds with both tokens
    alpha_token.transfer(endaoment_funds.address, alpha_amount, sender=alpha_token_whale)
    bravo_token.transfer(endaoment_funds.address, bravo_amount, sender=bravo_token_whale)
    
    initial_alpha_gov = alpha_token.balanceOf(governance.address)
    initial_bravo_gov = bravo_token.balanceOf(governance.address)
    
    # Transfer ALPHA
    tx1 = endaoment.transferFundsToGov(
        alpha_token.address,
        alpha_amount,
        sender=switchboard_charlie.address
    )
    assert tx1[0] == alpha_amount
    
    # Transfer BRAVO
    tx2 = endaoment.transferFundsToGov(
        bravo_token.address,
        bravo_amount,
        sender=switchboard_charlie.address
    )
    assert tx2[0] == bravo_amount
    
    # Verify both transfers completed
    assert alpha_token.balanceOf(endaoment_funds.address) == 0
    assert bravo_token.balanceOf(endaoment_funds.address) == 0
    assert alpha_token.balanceOf(governance.address) == initial_alpha_gov + alpha_amount
    assert bravo_token.balanceOf(governance.address) == initial_bravo_gov + bravo_amount


def test_transfer_funds_with_green_token(
    endaoment,
    endaoment_funds,
    switchboard_charlie,
    governance,
    green_token,
):
    """Test transfer with GREEN token (endaoment can mint green)"""
    green_amount = 10000 * EIGHTEEN_DECIMALS

    # Mint GREEN tokens and transfer to vault
    green_token.mint(endaoment_funds.address, green_amount, sender=endaoment.address)

    initial_gov_balance = green_token.balanceOf(governance.address)
    
    # Execute transfer
    tx = endaoment.transferFundsToGov(
        green_token.address,
        green_amount,
        sender=switchboard_charlie.address
    )
    
    amount_transferred, usd_value = tx
    assert amount_transferred == green_amount
    assert usd_value == 0  # No price feed configured for test token
    assert green_token.balanceOf(endaoment_funds.address) == 0
    assert green_token.balanceOf(governance.address) == initial_gov_balance + green_amount


def test_switchboard_transfer_initiate_and_execute(
    switchboard_echo,
    endaoment,
    endaoment_funds,
    governance,
    bravo_token,
    bravo_token_whale,
):
    """Test full governance flow: initiate and execute transfer through SwitchboardEcho"""
    transfer_amount = 1500 * EIGHTEEN_DECIMALS

    # Fund endaoment_funds
    bravo_token.transfer(endaoment_funds.address, transfer_amount, sender=bravo_token_whale)
    initial_endao_balance = bravo_token.balanceOf(endaoment_funds.address)
    initial_gov_balance = bravo_token.balanceOf(governance.address)

    # Initiate the transfer action
    switchboard_echo.performEndaomentTransfer(
        bravo_token.address,
        transfer_amount,
        sender=governance.address
    )

    # Get action ID from events
    events = filter_logs(switchboard_echo, "PendingEndaoTransferAction")
    assert len(events) == 1
    event = events[0]
    assert event.asset == bravo_token.address
    assert event.amount == transfer_amount
    action_id = event.actionId

    # Verify the pending action is stored
    pending_action = switchboard_echo.pendingEndaoTransfer(action_id)
    assert pending_action[0] == bravo_token.address  # asset
    assert pending_action[1] == transfer_amount  # amount

    # Verify action type is set correctly (ENDAO_TRANSFER is at position 6 in SwitchboardEcho, stored as flag)
    assert switchboard_echo.actionType(action_id) == 2**6  # ActionType.ENDAO_TRANSFER

    # Wait for timelock
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock() + 1)

    # Execute the action
    switchboard_echo.executePendingAction(action_id, sender=governance.address)

    # Verify the transfer was executed
    assert bravo_token.balanceOf(endaoment_funds.address) == initial_endao_balance - transfer_amount
    assert bravo_token.balanceOf(governance.address) == initial_gov_balance + transfer_amount

    # Check execution event
    exec_events = filter_logs(switchboard_echo, "EndaoTransferExecuted")
    assert len(exec_events) == 1
    assert exec_events[0].asset == bravo_token.address
    assert exec_events[0].amount == transfer_amount


def test_switchboard_transfer_max_amount(
    switchboard_echo,
    endaoment,
    endaoment_funds,
    governance,
    alpha_token,
    alpha_token_whale,
):
    """Test governance transfer with max amount through SwitchboardEcho"""
    fund_amount = 3000 * EIGHTEEN_DECIMALS

    # Fund endaoment_funds
    alpha_token.transfer(endaoment_funds.address, fund_amount, sender=alpha_token_whale)

    # Get initial governance balance to track exact change
    initial_gov_balance = alpha_token.balanceOf(governance.address)

    # Initiate transfer with max_value
    max_uint256 = 2**256 - 1
    switchboard_echo.performEndaomentTransfer(
        alpha_token.address,
        max_uint256,  # Use max value to transfer entire balance
        sender=governance.address
    )

    # Get action ID
    events = filter_logs(switchboard_echo, "PendingEndaoTransferAction")
    action_id = events[0].actionId

    # Wait for timelock and execute
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock() + 1)
    switchboard_echo.executePendingAction(action_id, sender=governance.address)

    # Verify entire balance was transferred
    assert alpha_token.balanceOf(endaoment_funds.address) == 0
    # Verify governance received exactly the fund_amount
    assert alpha_token.balanceOf(governance.address) == initial_gov_balance + fund_amount


def test_switchboard_transfer_cancel(
    switchboard_echo,
    governance,
    ripe_token,
):
    """Test cancelling a transfer action before execution"""
    transfer_amount = 500 * EIGHTEEN_DECIMALS

    # Initiate the transfer action
    switchboard_echo.performEndaomentTransfer(
        ripe_token.address,
        transfer_amount,
        sender=governance.address
    )

    # Get action ID
    events = filter_logs(switchboard_echo, "PendingEndaoTransferAction")
    action_id = events[0].actionId

    # Cancel the action
    switchboard_echo.cancelPendingAction(action_id, sender=governance.address)

    # Wait past timelock to try execution
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock() + 1)

    # Try to execute the cancelled action - should return False (action was deleted)
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert result == False  # Action no longer exists after cancellation


def test_switchboard_transfer_no_permission(
    switchboard_echo,
    alice,
    alpha_token,
):
    """Test that non-governance cannot initiate transfer through SwitchboardEcho"""
    with boa.reverts("no perms"):
        switchboard_echo.performEndaomentTransfer(
            alpha_token.address,
            1000,
            sender=alice
        )


def test_switchboard_transfer_invalid_asset(
    switchboard_echo,
    governance,
):
    """Test that initiating transfer with invalid asset fails"""
    with boa.reverts("invalid asset"):
        switchboard_echo.performEndaomentTransfer(
            ZERO_ADDRESS,
            1000,
            sender=governance.address
        )


def test_switchboard_transfer_zero_amount(
    switchboard_echo,
    governance,
    alpha_token,
):
    """Test that initiating transfer with zero amount fails"""
    with boa.reverts("invalid amount"):
        switchboard_echo.performEndaomentTransfer(
            alpha_token.address,
            0,
            sender=governance.address
        )


def test_switchboard_transfer_execute_too_early(
    switchboard_echo,
    governance,
    alpha_token,
):
    """Test that executing before timelock returns False"""
    # Initiate the transfer action
    switchboard_echo.performEndaomentTransfer(
        alpha_token.address,
        1000 * EIGHTEEN_DECIMALS,
        sender=governance.address
    )

    # Get action ID
    events = filter_logs(switchboard_echo, "PendingEndaoTransferAction")
    action_id = events[0].actionId

    # Try to execute immediately - should return False (timelock not met)
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert result == False  # Timelock not met


def test_switchboard_transfer_insufficient_balance(
    switchboard_echo,
    endaoment,
    endaoment_funds,
    governance,
    alpha_token,
):
    """Test that transfer fails gracefully when endaoment has insufficient balance"""
    transfer_amount = 1000 * EIGHTEEN_DECIMALS

    # Ensure endaoment_funds has no ALPHA
    assert alpha_token.balanceOf(endaoment_funds.address) == 0

    # Initiate the transfer action
    switchboard_echo.performEndaomentTransfer(
        alpha_token.address,
        transfer_amount,
        sender=governance.address
    )

    # Get action ID
    events = filter_logs(switchboard_echo, "PendingEndaoTransferAction")
    action_id = events[0].actionId

    # Wait for timelock
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock() + 1)

    # Execute should fail due to no balance in endaoment
    with boa.reverts("no amt"):
        switchboard_echo.executePendingAction(action_id, sender=governance.address)