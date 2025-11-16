import boa
from conf_utils import filter_logs

SIX_DECIMALS = 10**6  # For tokens like USDC that have 6 decimals


def test_transfer_funds_basic_switchboard(
    endaoment,
    endaoment_funds,
    endaoment_psm,
    switchboard_charlie,
    charlie_token,
    governance,
):
    """Test basic transfer of USDC to EndaomentPSM via switchboard"""
    transfer_amount = 1000 * SIX_DECIMALS  # charlie_token has 6 decimals (like USDC)

    # Fund endaoment_funds with charlie_token (USDC)
    charlie_token.mint(endaoment_funds.address, transfer_amount, sender=governance.address)
    initial_funds_balance = charlie_token.balanceOf(endaoment_funds.address)
    assert initial_funds_balance == transfer_amount

    # Get initial EndaomentPSM balance
    initial_psm_balance = charlie_token.balanceOf(endaoment_psm.address)

    # Execute transfer through switchboard
    tx = endaoment.transferFundsToEndaomentPSM(
        transfer_amount,
        sender=switchboard_charlie.address
    )

    # Check return values
    amount_transferred, usd_value = tx
    assert amount_transferred == transfer_amount
    # USD value will be 0 since price feed not configured for charlie_token in tests
    assert usd_value == 0

    # Verify balances
    assert charlie_token.balanceOf(endaoment_funds.address) == initial_funds_balance - transfer_amount
    assert charlie_token.balanceOf(endaoment_psm.address) == initial_psm_balance + transfer_amount

    # Check event
    events = filter_logs(endaoment, "WalletAction")
    assert len(events) == 1
    event = events[0]
    assert event.op == 1  # Transfer operation
    assert event.asset1 == charlie_token.address
    assert event.asset2 == endaoment_psm.address
    assert event.amount1 == transfer_amount
    assert event.amount2 == 0
    assert event.usdValue == 0
    assert event.legoId == 0


def test_transfer_funds_basic_governance(
    endaoment,
    endaoment_funds,
    endaoment_psm,
    governance,
    charlie_token,
):
    """Test basic transfer of USDC to EndaomentPSM via governance"""
    transfer_amount = 2000 * SIX_DECIMALS  # charlie_token has 6 decimals

    # Fund endaoment_funds with charlie_token (USDC)
    charlie_token.mint(endaoment_funds.address, transfer_amount, sender=governance.address)
    initial_funds_balance = charlie_token.balanceOf(endaoment_funds.address)

    # Get initial EndaomentPSM balance
    initial_psm_balance = charlie_token.balanceOf(endaoment_psm.address)

    # Execute transfer through governance
    tx = endaoment.transferFundsToEndaomentPSM(
        transfer_amount,
        sender=governance.address
    )

    # Check return values
    amount_transferred, usd_value = tx
    assert amount_transferred == transfer_amount

    # Verify balances
    assert charlie_token.balanceOf(endaoment_funds.address) == initial_funds_balance - transfer_amount
    assert charlie_token.balanceOf(endaoment_psm.address) == initial_psm_balance + transfer_amount


def test_transfer_funds_max_value(
    endaoment,
    endaoment_funds,
    endaoment_psm,
    switchboard_charlie,
    charlie_token,
    governance,
):
    """Test transfer with max_value (transfers entire balance)"""
    fund_amount = 5000 * SIX_DECIMALS  # charlie_token has 6 decimals

    # Fund endaoment_funds
    charlie_token.mint(endaoment_funds.address, fund_amount, sender=governance.address)
    initial_balance = charlie_token.balanceOf(endaoment_funds.address)

    # Get initial EndaomentPSM balance
    initial_psm_balance = charlie_token.balanceOf(endaoment_psm.address)

    # Execute transfer with max_value (default parameter)
    tx = endaoment.transferFundsToEndaomentPSM(
        sender=switchboard_charlie.address
    )

    amount_transferred, usd_value = tx
    assert amount_transferred == initial_balance
    assert charlie_token.balanceOf(endaoment_funds.address) == 0
    assert charlie_token.balanceOf(endaoment_psm.address) == initial_psm_balance + initial_balance


def test_transfer_funds_partial_when_requested_exceeds_balance(
    endaoment,
    endaoment_funds,
    endaoment_psm,
    switchboard_charlie,
    charlie_token,
    governance,
):
    """Test partial transfer when requested amount exceeds balance"""
    balance_amount = 1000 * SIX_DECIMALS
    request_amount = 2000 * SIX_DECIMALS  # Request more than available

    # Fund endaoment_funds with less than requested
    charlie_token.mint(endaoment_funds.address, balance_amount, sender=governance.address)

    # Get initial EndaomentPSM balance
    initial_psm_balance = charlie_token.balanceOf(endaoment_psm.address)

    # Should transfer only what's available
    tx = endaoment.transferFundsToEndaomentPSM(
        request_amount,
        sender=switchboard_charlie.address
    )

    amount_transferred, usd_value = tx
    assert amount_transferred == balance_amount  # Only what was available
    assert charlie_token.balanceOf(endaoment_funds.address) == 0
    assert charlie_token.balanceOf(endaoment_psm.address) == initial_psm_balance + balance_amount


def test_transfer_funds_unauthorized_caller(
    endaoment,
    endaoment_funds,
    charlie_token,
    governance,
    alice,
):
    """Test that unauthorized caller cannot transfer funds"""
    transfer_amount = 1000 * SIX_DECIMALS

    # Fund endaoment_funds
    charlie_token.mint(endaoment_funds.address, transfer_amount, sender=governance.address)

    # Try to transfer as unauthorized user (should fail)
    with boa.reverts("no perms"):
        endaoment.transferFundsToEndaomentPSM(
            transfer_amount,
            sender=alice
        )


def test_transfer_funds_when_paused(
    endaoment,
    endaoment_funds,
    switchboard_charlie,
    governance,
    charlie_token,
):
    """Test that transfer fails when contract is paused"""
    transfer_amount = 1000 * SIX_DECIMALS

    # Fund endaoment_funds
    charlie_token.mint(endaoment_funds.address, transfer_amount, sender=governance.address)

    # Pause the contract
    endaoment.pause(True, sender=switchboard_charlie.address)

    # Try to transfer while paused (should fail)
    with boa.reverts("contract paused"):
        endaoment.transferFundsToEndaomentPSM(
            transfer_amount,
            sender=switchboard_charlie.address
        )


def test_transfer_funds_no_balance(
    endaoment,
    endaoment_funds,
    switchboard_charlie,
    charlie_token,
):
    """Test that transfer fails when no USDC balance in vault"""
    transfer_amount = 1000 * SIX_DECIMALS

    # Ensure endaoment_funds has no charlie_token (USDC)
    assert charlie_token.balanceOf(endaoment_funds.address) == 0

    # Try to transfer with no balance (should fail)
    with boa.reverts("no amt"):
        endaoment.transferFundsToEndaomentPSM(
            transfer_amount,
            sender=switchboard_charlie.address
        )


def test_transfer_funds_multiple_calls(
    endaoment,
    endaoment_funds,
    endaoment_psm,
    switchboard_charlie,
    charlie_token,
    governance,
):
    """Test multiple transfers to EndaomentPSM"""
    first_amount = 1000 * SIX_DECIMALS
    second_amount = 500 * SIX_DECIMALS

    # Fund endaoment_funds with enough for both transfers
    total_amount = first_amount + second_amount
    charlie_token.mint(endaoment_funds.address, total_amount, sender=governance.address)

    # Get initial EndaomentPSM balance
    initial_psm_balance = charlie_token.balanceOf(endaoment_psm.address)

    # First transfer
    tx1 = endaoment.transferFundsToEndaomentPSM(
        first_amount,
        sender=switchboard_charlie.address
    )
    amount1, _ = tx1
    assert amount1 == first_amount

    # Second transfer
    tx2 = endaoment.transferFundsToEndaomentPSM(
        second_amount,
        sender=switchboard_charlie.address
    )
    amount2, _ = tx2
    assert amount2 == second_amount

    # Verify final balances
    assert charlie_token.balanceOf(endaoment_funds.address) == 0
    assert charlie_token.balanceOf(endaoment_psm.address) == initial_psm_balance + total_amount
