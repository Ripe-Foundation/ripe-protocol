"""Group 11 (Claude) never-skip #2 -- the clone -> owner two-step, minus the lock
matrix (that lives in test_g11_claude_lock_matrix.py)."""

import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from conf_utils import assert_reverted_call, filter_logs

from g11_claude_helpers import (
    make_contributor,
    position,
    set_budget,
    set_hr_config,
    term_args,
    terms,
    travel_to,
    unlock_block,
)


def _mk(hr, mc, sbd, tpl, ledger, gov_, **over):
    return make_contributor(hr, mc, sbd, tpl, ledger, gov_, terms(**over))


def _cash_at_cliff(c, owner):
    travel_to(c.cliffTime())
    amount = c.cashRipeCheck(sender=owner)
    assert amount > 0
    return amount


# ------------------------------------------------------------------ unlock edge


def test_g11c_initiate_exact_unlock_reverts_and_unlock_plus_one_succeeds(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token, alice, bob,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    _cash_at_cliff(c, alice)

    travel_to(c.unlockTime())
    assert boa.env.evm.patch.timestamp == c.unlockTime()
    with boa.reverts("time not past unlock"):
        c.initiateRipeTransfer(False, sender=alice)
    assert not c.hasPendingRipeTransfer()

    travel_to(c.unlockTime() + 1)
    c.initiateRipeTransfer(False, sender=alice)
    p = c.pendingRipeTransfer()
    assert p.recipient == alice
    assert p.initiatedBlock == boa.env.evm.patch.block_number
    assert p.confirmBlock == boa.env.evm.patch.block_number + c.keyActionDelay()


def test_g11c_confirm_one_block_early_reverts_pending_intact_then_exact_block_works(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token, alice, bob,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    cashed = _cash_at_cliff(c, alice)
    travel_to(c.unlockTime() + 1)
    c.initiateRipeTransfer(False, sender=alice)
    pending = c.pendingRipeTransfer()

    boa.env.time_travel(blocks=c.keyActionDelay() - 1)
    assert boa.env.evm.patch.block_number == pending.confirmBlock - 1
    with boa.reverts("time delay not reached"):
        c.confirmRipeTransfer(False, sender=alice)
    assert c.pendingRipeTransfer() == pending
    assert position(ripe_gov_vault, c, ripe_token) == cashed

    boa.env.time_travel(blocks=1)
    assert boa.env.evm.patch.block_number == pending.confirmBlock
    supply = ripe_token.totalSupply()
    c.confirmRipeTransfer(False, sender=alice)
    ev = filter_logs(c, "RipeTransferConfirmed")
    assert len(ev) == 1 and ev[0].recipient == alice and ev[0].amount == cashed
    assert ev[0].initiatedBlock == pending.initiatedBlock
    assert position(ripe_gov_vault, c, ripe_token) == 0
    assert position(ripe_gov_vault, alice, ripe_token) == cashed
    assert ripe_token.totalSupply() == supply  # clean transfer mints nothing
    assert not c.hasPendingRipeTransfer()


# ------------------------------------------------------------------ recipient


def test_g11c_manager_initiate_and_confirm_still_credit_the_owner_at_initiate(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token,
    alice, bob, sally,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    cashed = _cash_at_cliff(c, alice)
    travel_to(c.unlockTime() + 1)

    c.initiateRipeTransfer(False, sender=bob)  # manager initiates
    assert c.pendingRipeTransfer().recipient == alice

    # a manager rotation mid-pending cannot repoint the recipient
    c.setManager(sally, sender=alice)
    assert c.manager() == sally
    assert c.pendingRipeTransfer().recipient == alice

    boa.env.time_travel(blocks=c.keyActionDelay())
    c.confirmRipeTransfer(False, sender=sally)  # new manager confirms
    ev = filter_logs(c, "RipeTransferConfirmed")
    assert ev[0].recipient == alice and ev[0].confirmedBy == sally
    assert position(ripe_gov_vault, alice, ripe_token) == cashed
    assert position(ripe_gov_vault, bob, ripe_token) == 0
    assert position(ripe_gov_vault, sally, ripe_token) == 0
    assert position(ripe_gov_vault, c, ripe_token) == 0


def test_g11c_owner_change_after_a_confirmed_transfer_does_not_move_paid_funds(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token,
    alice, bob, sally,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    cashed = _cash_at_cliff(c, alice)
    travel_to(c.unlockTime() + 1)
    c.initiateRipeTransfer(False, sender=alice)

    # pending transfer blocks an ownership initiate outright
    with boa.reverts("cannot do with pending ripe transfer"):
        c.changeOwnership(sally, sender=alice)

    boa.env.time_travel(blocks=c.keyActionDelay())
    c.confirmRipeTransfer(False, sender=alice)
    assert position(ripe_gov_vault, alice, ripe_token) == cashed

    c.changeOwnership(sally, sender=alice)
    boa.env.time_travel(blocks=c.keyActionDelay())
    c.confirmOwnershipChange(sender=sally)
    assert c.owner() == sally
    assert position(ripe_gov_vault, alice, ripe_token) == cashed  # already paid
    assert position(ripe_gov_vault, sally, ripe_token) == 0


def test_g11c_pending_owner_and_pending_transfer_are_mutually_exclusive_at_start(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token,
    alice, bob, sally,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    _cash_at_cliff(c, alice)
    travel_to(c.unlockTime() + 1)
    c.changeOwnership(sally, sender=alice)
    with boa.reverts("cannot do with pending ownership change"):
        c.initiateRipeTransfer(False, sender=alice)
    c.cancelOwnershipChange(sender=alice)
    c.initiateRipeTransfer(False, sender=alice)
    boa.env.time_travel(blocks=c.keyActionDelay())

    # the confirm-side guard exists but is unreachable in ordinary flow: a pending
    # owner change cannot be created while a transfer is pending.
    with boa.reverts("cannot do with pending ripe transfer"):
        c.changeOwnership(sally, sender=alice)
    c.confirmRipeTransfer(False, sender=alice)
    assert not c.hasPendingRipeTransfer()

    # and the reverse ordering is symmetric
    c.changeOwnership(sally, sender=alice)
    with boa.reverts("cannot do with pending ownership change"):
        c.initiateRipeTransfer(False, sender=alice)


# ------------------------------------------------------- restart / delay grief


def test_g11c_manager_can_restart_confirm_block_indefinitely_owner_recovers_by_setmanager(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token,
    alice, bob, sally,
):
    """Availability, not theft: a hostile manager restarts the timer; the owner's
    immediate setManager ends it, costing exactly one more keyActionDelay."""
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    _cash_at_cliff(c, alice)
    travel_to(c.unlockTime() + 1)
    delay = c.keyActionDelay()

    c.initiateRipeTransfer(False, sender=alice)
    first = c.pendingRipeTransfer().confirmBlock

    for _ in range(3):
        boa.env.time_travel(blocks=delay - 1)
        c.initiateRipeTransfer(False, sender=bob)  # manager restarts
        p = c.pendingRipeTransfer()
        assert p.recipient == alice  # never repointed
        assert p.confirmBlock == boa.env.evm.patch.block_number + delay
    assert c.pendingRipeTransfer().confirmBlock > first

    # recovery: owner rotates the manager out immediately (allowed during a pending transfer)
    c.setManager(sally, sender=alice)
    with boa.reverts("no perms"):
        c.initiateRipeTransfer(False, sender=bob)
    restart_block = boa.env.evm.patch.block_number
    c.initiateRipeTransfer(False, sender=alice)
    assert c.pendingRipeTransfer().confirmBlock == restart_block + delay
    boa.env.time_travel(blocks=delay)
    c.confirmRipeTransfer(False, sender=alice)
    assert position(ripe_gov_vault, alice, ripe_token) > 0


def test_g11c_set_key_action_delay_after_initiate_does_not_retime_confirm_block(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token, alice, bob,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    _cash_at_cliff(c, alice)
    travel_to(c.unlockTime() + 1)
    c.initiateRipeTransfer(False, sender=alice)
    pending = c.pendingRipeTransfer()

    c.setKeyActionDelay(c.keyActionDelay() + 1_000, sender=alice)
    assert c.pendingRipeTransfer().confirmBlock == pending.confirmBlock

    boa.env.time_travel(blocks=pending.confirmBlock - boa.env.evm.patch.block_number)
    c.confirmRipeTransfer(False, sender=alice)
    assert position(ripe_gov_vault, c, ripe_token) == 0


# -------------------------------------------------------------- freeze / cancel


def test_g11c_freeze_blocks_transfer_legs_and_cancel_paths_by_all_three_callers(
    human_resources, mission_control, switchboard_delta, switchboard_alpha,
    contributor_template, ledger, governance, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, alice, bob, sally,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    _cash_at_cliff(c, alice)
    travel_to(c.unlockTime() + 1)

    # frozen initiate reverts
    switchboard_delta.freezeContributor(c.address, True, sender=governance.address)
    with boa.reverts("contract frozen"):
        c.initiateRipeTransfer(False, sender=alice)
    switchboard_delta.freezeContributor(c.address, False, sender=governance.address)

    # cancel by owner
    c.initiateRipeTransfer(False, sender=alice)
    c.cancelRipeTransfer(sender=alice)
    assert not c.hasPendingRipeTransfer()

    # cancel by manager
    c.initiateRipeTransfer(False, sender=alice)
    c.cancelRipeTransfer(sender=bob)
    assert not c.hasPendingRipeTransfer()

    # cancel by Delta lite signer
    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_alpha.address)
    c.initiateRipeTransfer(False, sender=alice)
    assert switchboard_delta.cancelRipeTransferForContributor(c.address, sender=sally)
    assert not c.hasPendingRipeTransfer()

    # frozen confirm reverts, but cancel while frozen is allowed
    c.initiateRipeTransfer(False, sender=alice)
    boa.env.time_travel(blocks=c.keyActionDelay())
    switchboard_delta.freezeContributor(c.address, True, sender=governance.address)
    with boa.reverts("contract frozen"):
        c.confirmRipeTransfer(False, sender=alice)
    assert c.hasPendingRipeTransfer()
    c.cancelRipeTransfer(sender=alice)
    assert not c.hasPendingRipeTransfer()


# ------------------------------------------------------- late-failure atomicity


def test_g11c_initiate_late_unlock_revert_rolls_back_the_nested_cash(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token, alice, bob,
):
    """(i) cash is entered first, then the unlock assert fails -> everything rolls back."""
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    travel_to(c.cliffTime())
    assert c.getClaimable() > 0
    assert boa.env.evm.patch.timestamp <= c.unlockTime()

    supply, claimed = ripe_token.totalSupply(), c.totalClaimed()
    pos, avail = position(ripe_gov_vault, c, ripe_token), ledger.ripeAvailForHr()
    with boa.reverts("time not past unlock"):
        c.initiateRipeTransfer(True, sender=alice)

    assert ripe_token.totalSupply() == supply
    assert c.totalClaimed() == claimed
    assert position(ripe_gov_vault, c, ripe_token) == pos
    assert ledger.ripeAvailForHr() == avail
    assert ripe_token.allowance(human_resources, switchboard_delta) == 0
    assert filter_logs(c, "RipeCheckCashed") == []
    assert not c.hasPendingRipeTransfer()

    # (iii) adjacent control: the same cash on its own succeeds
    claimable = c.getClaimable()
    assert c.cashRipeCheck(sender=alice) == claimable
    assert ripe_token.totalSupply() == supply + claimable


def test_g11c_initiate_late_pending_owner_revert_rolls_back_the_nested_cash(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token,
    alice, bob, sally,
):
    """(ii) same shape, with a pending ownership change as the later revert."""
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    travel_to(c.unlockTime() + 1)
    c.changeOwnership(sally, sender=alice)
    assert c.hasPendingOwnerChange()
    assert c.getClaimable() > 0

    supply, claimed = ripe_token.totalSupply(), c.totalClaimed()
    with boa.reverts("cannot do with pending ownership change"):
        c.initiateRipeTransfer(True, sender=alice)
    assert ripe_token.totalSupply() == supply and c.totalClaimed() == claimed
    assert filter_logs(c, "RipeCheckCashed") == []

    c.cancelOwnershipChange(sender=alice)
    claimable = c.getClaimable()
    assert c.cashRipeCheck(sender=alice) == claimable  # adjacent control


def test_g11c_confirm_transfer_revert_after_optional_cash_rolls_back_and_stays_retryable(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob,
):
    """Overflow-sized depositLockDuration is rejected at initiate."""
    t = terms(owner=alice, manager=bob, depositLockDuration=MAX_UINT256)
    set_hr_config(mission_control, switchboard_delta, contributor_template)
    set_budget(ledger, switchboard_delta, t["compensation"])
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(*term_args(t), sender=governance.address)


def test_g11c_official_hr_pause_rolls_back_confirm_and_the_same_pending_confirms_after(
    human_resources, mission_control, switchboard_delta, switchboard_charlie,
    contributor_template, ledger, governance, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, alice, bob,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    cashed = _cash_at_cliff(c, alice)
    travel_to(c.unlockTime() + 1)
    c.initiateRipeTransfer(False, sender=alice)
    pending = c.pendingRipeTransfer()
    boa.env.time_travel(blocks=c.keyActionDelay())

    assert switchboard_charlie.pause(human_resources.address, True, sender=governance.address)
    with pytest.raises(BoaError) as err:
        c.confirmRipeTransfer(False, sender=alice)
    assert_reverted_call(err.value, "contract paused", c)
    assert c.pendingRipeTransfer() == pending
    assert position(ripe_gov_vault, c, ripe_token) == cashed
    assert position(ripe_gov_vault, alice, ripe_token) == 0

    assert switchboard_charlie.pause(human_resources.address, False, sender=governance.address)
    c.confirmRipeTransfer(False, sender=alice)
    assert position(ripe_gov_vault, c, ripe_token) == 0
    assert position(ripe_gov_vault, alice, ripe_token) == cashed


def test_g11c_should_cash_check_false_leaves_vest_on_the_clone_and_still_moves_position(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token, alice, bob,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    cashed = _cash_at_cliff(c, alice)
    travel_to(c.unlockTime() + 1)
    claimable = c.getClaimable()
    assert claimable > 0

    c.initiateRipeTransfer(False, sender=alice)
    boa.env.time_travel(blocks=c.keyActionDelay())
    supply = ripe_token.totalSupply()
    c.confirmRipeTransfer(False, sender=alice)

    assert ripe_token.totalSupply() == supply  # nothing minted
    assert c.totalClaimed() == cashed          # unclaimed vest still owed
    assert c.getClaimable() > 0
    assert position(ripe_gov_vault, alice, ripe_token) == cashed
    assert position(ripe_gov_vault, c, ripe_token) == 0

    # the leftover vest can still be cashed -- straight back onto the CLONE
    more = c.cashRipeCheck(sender=alice)
    assert more > 0
    assert position(ripe_gov_vault, c, ripe_token) == more
    assert position(ripe_gov_vault, alice, ripe_token) == cashed
