"""Group 11 (Claude) never-skip #4 -- ownership, manager, key-action delay, freeze."""

import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS
from conf_utils import assert_reverted_call, filter_logs

from g11_claude_helpers import make_contributor, position, terms, travel_to


def _mk(hr, mc, sbd, tpl, ledger, gov_, **over):
    return make_contributor(hr, mc, sbd, tpl, ledger, gov_, terms(**over))


def test_g11c_change_ownership_rejects_empty_self_and_current_owner(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob, sally,
):
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    for bad in (ZERO_ADDRESS, c.address, alice):
        with boa.reverts("invalid new owner"):
            c.changeOwnership(bad, sender=alice)
    with boa.reverts("no perms"):
        c.changeOwnership(sally, sender=bob)      # manager cannot
    with boa.reverts("no perms"):
        c.changeOwnership(sally, sender=sally)
    assert not c.hasPendingOwnerChange()


def test_g11c_confirm_ownership_change_is_new_owner_only(
    human_resources, mission_control, switchboard_delta, switchboard_alpha,
    contributor_template, ledger, governance, alice, bob, sally,
):
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    c.changeOwnership(sally, sender=alice)
    boa.env.time_travel(blocks=c.keyActionDelay())
    for caller in (alice, bob, switchboard_alpha.address, switchboard_delta.address):
        with boa.reverts("only new owner can confirm"):
            c.confirmOwnershipChange(sender=caller)
    c.confirmOwnershipChange(sender=sally)
    assert c.owner() == sally and c.numOwnerChanges() == 1
    assert not c.hasPendingOwnerChange()


def test_g11c_pending_owner_blocks_set_manager_including_the_delta_execute(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob, sally,
):
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    aid = switchboard_delta.setManagerForContributor(c.address, sally, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())

    c.changeOwnership(sally, sender=alice)
    with boa.reverts("cannot do with pending ownership change"):
        c.setManager(sally, sender=alice)
    with pytest.raises(BoaError) as err:
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert_reverted_call(err.value, "cannot do with pending ownership change", switchboard_delta)
    assert c.manager() == bob
    assert switchboard_delta.hasPendingAction(aid)

    # adjacent control: cancel the pending owner and the same Delta action executes
    c.cancelOwnershipChange(sender=alice)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert c.manager() == sally


def test_g11c_key_action_delay_bounds_come_from_this_hr_instance(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob,
):
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    lo = human_resources.minActionTimeLock()
    hi = human_resources.maxActionTimeLock()
    assert c.keyActionDelay() == lo          # a new clone starts at the constructor minimum
    c.setKeyActionDelay(lo, sender=alice)
    c.setKeyActionDelay(hi, sender=alice)
    assert c.keyActionDelay() == hi
    with boa.reverts("invalid delay"):
        c.setKeyActionDelay(lo - 1, sender=alice)
    with boa.reverts("invalid delay"):
        c.setKeyActionDelay(hi + 1, sender=alice)
    with boa.reverts("no perms"):
        c.setKeyActionDelay(lo, sender=bob)   # manager cannot


def test_g11c_default_minimum_handoff_has_no_prior_delay_event_and_a_measurable_window(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob, sally,
):
    """A brand-new clone hands off at the constructor minimum with NO KeyActionDelaySet
    warning; a raised-then-lowered clone emits one before the handoff."""
    lo = human_resources.minActionTimeLock()
    hi = human_resources.maxActionTimeLock()

    # --- scenario A: untouched delay
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    assert filter_logs(c, "KeyActionDelaySet") == []
    c.changeOwnership(sally, sender=alice)
    assert filter_logs(c, "KeyActionDelaySet") == []
    init = filter_logs(c, "OwnershipChangeInitiated")
    assert len(init) == 1
    window = c.pendingOwner().confirmBlock - boa.env.evm.patch.block_number
    assert window == lo                       # the real cancellation window, in blocks

    # --- scenario B: raised then lowered in the same block as the handoff
    c2 = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
             ledger, governance, owner=alice, manager=bob)
    c2.setKeyActionDelay(hi, sender=alice)
    assert len(filter_logs(c2, "KeyActionDelaySet")) == 1
    c2.setKeyActionDelay(lo, sender=alice)
    ev = filter_logs(c2, "KeyActionDelaySet")
    assert len(ev) == 1 and ev[0].numBlocks == lo
    lower_block = boa.env.evm.patch.block_number
    c2.changeOwnership(sally, sender=alice)          # same block as the lowering
    assert boa.env.evm.patch.block_number == lower_block
    assert c2.pendingOwner().confirmBlock == lower_block + lo

    # --- a delay change after initiation does not retime the pending handoff
    c2.setKeyActionDelay(hi, sender=alice)
    assert c2.pendingOwner().confirmBlock == lower_block + lo
    boa.env.time_travel(blocks=lo)
    c2.confirmOwnershipChange(sender=sally)
    assert c2.owner() == sally


def test_g11c_pending_ownership_initiate_is_cancel_replace_with_a_restarted_timer(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob, sally, whale,
):
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    delay = c.keyActionDelay()
    c.changeOwnership(sally, sender=alice)
    first = c.pendingOwner()
    boa.env.time_travel(blocks=delay - 5)
    c.changeOwnership(whale, sender=alice)
    second = c.pendingOwner()
    assert second.newOwner == whale
    assert second.confirmBlock == boa.env.evm.patch.block_number + delay > first.confirmBlock
    # the replaced pending is gone. At the ORIGINAL confirmBlock the delay guard
    # (checked before the identity guard) is what stops the old candidate.
    boa.env.time_travel(blocks=5)
    assert boa.env.evm.patch.block_number == first.confirmBlock
    with boa.reverts("time delay not reached"):
        c.confirmOwnershipChange(sender=sally)
    # and once the RESTARTED timer matures, only the replacement can confirm
    boa.env.time_travel(blocks=second.confirmBlock - boa.env.evm.patch.block_number)
    with boa.reverts("only new owner can confirm"):
        c.confirmOwnershipChange(sender=sally)
    c.confirmOwnershipChange(sender=whale)
    assert c.owner() == whale


def test_g11c_freeze_does_not_stop_a_handoff_only_the_pre_confirm_window_does(
    human_resources, mission_control, switchboard_delta, switchboard_alpha,
    contributor_template, ledger, governance, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, alice, bob, sally,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    delay = c.keyActionDelay()

    # lite signer freezes (True is a lite action; False is governor-only)
    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_alpha.address)
    assert switchboard_delta.freezeContributor(c.address, True, sender=sally)
    with boa.reverts("no perms"):
        switchboard_delta.freezeContributor(c.address, False, sender=sally)

    # ownership still moves while frozen
    c.changeOwnership(sally, sender=alice)
    window = c.pendingOwner().confirmBlock - boa.env.evm.patch.block_number
    assert window == delay

    # lite can cancel the pending handoff -- but only BEFORE confirm
    assert switchboard_delta.cancelOwnershipChangeForContributor(c.address, sender=sally)
    assert not c.hasPendingOwnerChange()

    c.changeOwnership(sally, sender=alice)
    boa.env.time_travel(blocks=delay)
    c.confirmOwnershipChange(sender=sally)
    assert c.owner() == sally
    with boa.reverts("no pending change"):
        switchboard_delta.cancelOwnershipChangeForContributor(c.address, sender=sally)

    # unfreeze restores cash and the transfer legs to the NEW owner
    assert switchboard_delta.freezeContributor(c.address, False, sender=governance.address)
    travel_to(c.cliffTime())
    cashed = c.cashRipeCheck(sender=sally)
    assert cashed > 0
    travel_to(c.unlockTime() + 1)
    c.initiateRipeTransfer(False, sender=sally)
    assert c.pendingRipeTransfer().recipient == sally
    boa.env.time_travel(blocks=c.keyActionDelay())
    c.confirmRipeTransfer(False, sender=sally)
    assert position(ripe_gov_vault, sally, ripe_token) > 0
    assert position(ripe_gov_vault, alice, ripe_token) == 0


def test_g11c_frozen_blocks_delegation_but_not_manager_or_delay_writes(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, ripe_gov_vault, alice, bob, sally,
):
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    switchboard_delta.freezeContributor(c.address, True, sender=governance.address)
    with boa.reverts("contract frozen"):
        c.delegateTo(ripe_gov_vault.address, sally, 100_00, sender=alice)
    with boa.reverts("contract frozen"):
        c.removeDelegationFor(ripe_gov_vault.address, sally, sender=bob)
    # these remain available while frozen
    c.setManager(sally, sender=alice)
    assert c.manager() == sally
    c.setKeyActionDelay(human_resources.maxActionTimeLock(), sender=alice)
    with boa.reverts("cannot be 0x0"):
        c.setManager(ZERO_ADDRESS, sender=alice)


def test_g11c_owner_equals_manager_is_accepted_but_owner_equals_clone_is_not(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice,
):
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=alice)
    assert c.owner() == c.manager() == alice
    with boa.reverts("invalid new owner"):
        c.changeOwnership(c.address, sender=alice)
