import boa
import pytest


AMOUNT = 10**18
SUPPLY = 1_000_000 * AMOUNT


@pytest.fixture
def actors(env):
    return {
        "owner": env.generate_address("probe_owner"),
        "recipient": env.generate_address("probe_recipient"),
        "other": env.generate_address("probe_other"),
    }


@pytest.fixture
def token(actors):
    return boa.load(
        "contracts/mock/MockProbeErc20.vy",
        actors["owner"],
        SUPPLY,
        name="probe_token",
    )


@pytest.fixture
def probe(token, actors):
    return boa.load(
        "contracts/testing/StockTokenTransferProbe.vy",
        actors["owner"],
        token,
        actors["recipient"],
        name="stock_token_transfer_probe",
    )


def approve_and_deposit(token, probe, owner, amount=AMOUNT):
    assert token.approve(probe.address, amount, sender=owner)
    probe.deposit(amount, sender=owner)


def test_successful_round_trip_reconciles_exact_balances_and_events(token, probe, actors):
    owner = actors["owner"]
    recipient = actors["recipient"]
    sender_before = token.balanceOf(owner)
    recipient_before = token.balanceOf(recipient)

    approve_and_deposit(token, probe, owner)
    deposit_events = [
        event for event in probe.get_logs() if type(event).__name__ == "TokenDeposited"
    ]

    assert token.balanceOf(owner) == sender_before - AMOUNT
    assert token.balanceOf(probe.address) == AMOUNT
    assert token.allowance(owner, probe.address) == 0

    probe.withdraw(AMOUNT, sender=owner)
    withdrawal_events = [
        event for event in probe.get_logs() if type(event).__name__ == "TokenWithdrawn"
    ]

    assert token.balanceOf(owner) == sender_before - AMOUNT
    assert token.balanceOf(recipient) == recipient_before + AMOUNT
    assert token.balanceOf(probe.address) == 0
    assert token.approve(probe.address, 0, sender=owner)
    assert token.allowance(owner, probe.address) == 0

    assert len(deposit_events) == 1
    assert deposit_events[0].amount == AMOUNT
    assert deposit_events[0].balanceBefore == 0
    assert deposit_events[0].balanceAfter == AMOUNT
    assert len(withdrawal_events) == 1
    assert withdrawal_events[0].probeBalanceBefore == AMOUNT
    assert withdrawal_events[0].probeBalanceAfter == 0


def test_owner_only_withdrawal_and_recovery(token, probe, actors):
    owner = actors["owner"]
    other = actors["other"]
    recipient = actors["recipient"]
    approve_and_deposit(token, probe, owner)

    with boa.reverts("only owner"):
        probe.withdraw(AMOUNT, sender=other)

    recovery_token = boa.load(
        "contracts/mock/MockProbeErc20.vy",
        owner,
        AMOUNT,
        name="recovery_token",
    )
    recovery_token.transfer(probe.address, AMOUNT, sender=owner)
    with boa.reverts("only owner"):
        probe.recoverToken(recovery_token, AMOUNT, sender=other)

    recipient_before = recovery_token.balanceOf(recipient)
    probe.recoverToken(recovery_token, AMOUNT, sender=owner)
    assert recovery_token.balanceOf(probe.address) == 0
    assert recovery_token.balanceOf(recipient) == recipient_before + AMOUNT


def test_zero_amount_fails(token, probe, actors):
    owner = actors["owner"]
    with boa.reverts("invalid amount"):
        probe.deposit(0, sender=owner)
    with boa.reverts("invalid amount"):
        probe.withdraw(0, sender=owner)
    with boa.reverts("invalid amount"):
        probe.recoverToken(token, 0, sender=owner)


def test_insufficient_allowance_fails(token, probe, actors):
    with boa.reverts():
        probe.deposit(AMOUNT, sender=actors["owner"])
    assert token.balanceOf(probe.address) == 0


def test_insufficient_balance_fails(token, probe, actors):
    other = actors["other"]
    token.approve(probe.address, AMOUNT, sender=other)
    with boa.reverts():
        probe.deposit(AMOUNT, sender=other)
    assert token.balanceOf(probe.address) == 0


def test_wrong_token_cannot_be_substituted(token, probe, actors):
    owner = actors["owner"]
    wrong_token = boa.load(
        "contracts/mock/MockProbeErc20.vy",
        owner,
        AMOUNT,
        name="wrong_probe_token",
    )
    wrong_token.approve(probe.address, AMOUNT, sender=owner)

    with boa.reverts():
        probe.deposit(AMOUNT, sender=owner)

    assert wrong_token.balanceOf(owner) == AMOUNT
    assert wrong_token.balanceOf(probe.address) == 0
    assert token.balanceOf(probe.address) == 0


@pytest.mark.parametrize("failure_mode", ["false", "revert"])
def test_token_returning_false_or_reverting_fails_closed(token, probe, actors, failure_mode):
    owner = actors["owner"]
    token.approve(probe.address, AMOUNT, sender=owner)
    if failure_mode == "false":
        token.setReturnFalse(True, sender=owner)
        expected = "token transfer failed"
    else:
        token.setRevertTransfers(True, sender=owner)
        expected = "mock transfer reverted"

    with boa.reverts(expected):
        probe.deposit(AMOUNT, sender=owner)

    assert token.balanceOf(probe.address) == 0


def test_paused_token_blocks_deposit_and_withdraw(token, probe, actors):
    owner = actors["owner"]
    token.approve(probe.address, AMOUNT, sender=owner)
    token.setPaused(True, sender=owner)
    with boa.reverts("token paused"):
        probe.deposit(AMOUNT, sender=owner)

    token.setPaused(False, sender=owner)
    probe.deposit(AMOUNT, sender=owner)
    token.setPaused(True, sender=owner)
    with boa.reverts("token paused"):
        probe.withdraw(AMOUNT, sender=owner)

    token.setPaused(False, sender=owner)
    probe.withdraw(AMOUNT, sender=owner)
    assert token.balanceOf(probe.address) == 0


@pytest.mark.parametrize("blocked_party", ["sender", "probe", "recipient"])
def test_blocked_address_behavior(token, probe, actors, blocked_party):
    owner = actors["owner"]
    token.approve(probe.address, AMOUNT, sender=owner)

    if blocked_party == "sender":
        token.setBlocked(owner, True, sender=owner)
        with boa.reverts("sender blocked"):
            probe.deposit(AMOUNT, sender=owner)
        return

    if blocked_party == "probe":
        token.setBlocked(probe.address, True, sender=owner)
        with boa.reverts("recipient blocked"):
            probe.deposit(AMOUNT, sender=owner)
        return

    probe.deposit(AMOUNT, sender=owner)
    token.setBlocked(actors["recipient"], True, sender=owner)
    with boa.reverts("recipient blocked"):
        probe.withdraw(AMOUNT, sender=owner)


def test_unauthorized_withdrawal_does_not_change_balance(token, probe, actors):
    approve_and_deposit(token, probe, actors["owner"])
    with boa.reverts("only owner"):
        probe.withdraw(AMOUNT, sender=actors["other"])
    assert token.balanceOf(probe.address) == AMOUNT


def test_partial_withdraw_and_recovery_leave_no_balance(token, probe, actors):
    owner = actors["owner"]
    approve_and_deposit(token, probe, owner, 2 * AMOUNT)
    probe.withdraw(AMOUNT, sender=owner)
    assert token.balanceOf(probe.address) == AMOUNT
    probe.recoverToken(token, AMOUNT, sender=owner)
    assert token.balanceOf(probe.address) == 0
    assert token.allowance(owner, probe.address) == 0
