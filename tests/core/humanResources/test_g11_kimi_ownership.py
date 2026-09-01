"""Group 11 (kimi) proof tests — never-skip #4: ownership / manager / freeze.

confirmOwnershipChange is new-owner-only. changeOwnership rejects empty / self
/ current owner. Pending transfer blocks ownership initiate; pending owner
blocks transfer AND setManager (including the Delta execute path). Owner
setManager during a pending transfer does not change pending.recipient.
Freeze is not an ownership freeze: handoffs proceed while frozen; the real
cancellation window is measured in blocks.
"""
import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from contracts.modules import Contributor


def _ts():
    return boa.env.evm.patch.timestamp


def _bn():
    return boa.env.evm.patch.block_number


def _travel_to_ts(t):
    now = _ts()
    if now < t:
        boa.env.time_travel(seconds=t - now)


def _advance_blocks(n):
    if n > 0:
        boa.env.time_travel(blocks=n)


def _deploy(human_resources, setupHrConfig, setupLedgerBalance, governance,
            valid_contributor_terms, **overrides):
    terms = dict(valid_contributor_terms)
    terms.update(overrides)
    setupHrConfig()
    setupLedgerBalance(terms["compensation"])
    aid = human_resources.initiateNewContributor(
        terms["owner"], terms["manager"], terms["compensation"],
        terms["startDelay"], terms["vestingLength"], terms["cliffLength"],
        terms["unlockLength"], terms["depositLockDuration"],
        sender=governance.address,
    )
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid, sender=governance.address)
    events = filter_logs(human_resources, "NewContributorConfirmed")
    return Contributor.at(events[-1].contributorAddr)


def test_g11_ownership_change_gates(
    human_resources, contributor_contract, owner_address, manager_address,
    alice, bob, switchboard_delta, governance,
):
    """changeOwnership rejects empty/self/current; confirm is new-owner-only;
    pending ownership initiate is cancel-replace with a restarted timer."""
    c = contributor_contract
    with boa.reverts("invalid new owner"):
        c.changeOwnership(ZERO_ADDRESS, sender=owner_address)
    with boa.reverts("invalid new owner"):
        c.changeOwnership(c.address, sender=owner_address)
    with boa.reverts("invalid new owner"):
        c.changeOwnership(owner_address, sender=owner_address)
    # manager cannot initiate ownership change
    with boa.reverts("no perms"):
        c.changeOwnership(alice, sender=manager_address)

    c.changeOwnership(alice, sender=owner_address)
    p = c.pendingOwner()
    assert p.newOwner == alice
    assert p.confirmBlock == p.initiatedBlock + c.keyActionDelay()

    # confirm is new-owner-only: old owner / manager / switchboard all revert
    _advance_blocks(p.confirmBlock - _bn())
    with boa.reverts("only new owner can confirm"):
        c.confirmOwnershipChange(sender=owner_address)
    with boa.reverts("only new owner can confirm"):
        c.confirmOwnershipChange(sender=manager_address)
    with boa.reverts("only new owner can confirm"):
        c.confirmOwnershipChange(sender=governance.address)
    c.confirmOwnershipChange(sender=alice)
    assert c.owner() == alice
    assert c.numOwnerChanges() == 1

    # cancel-replace: new initiate overwrites and restarts the timer
    c.changeOwnership(bob, sender=alice)
    p1 = c.pendingOwner()
    _advance_blocks(5)
    c.changeOwnership(owner_address, sender=alice)
    p2 = c.pendingOwner()
    assert p2.newOwner == owner_address
    assert p2.initiatedBlock > p1.initiatedBlock
    assert p2.confirmBlock == p2.initiatedBlock + c.keyActionDelay()
    c.cancelOwnershipChange(sender=alice)
    assert not c.hasPendingOwnerChange()


def test_g11_pending_owner_blocks_transfer_and_delta_set_manager(
    human_resources, contributor_contract, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, teller, whale, owner_address, alice, bob,
    switchboard_delta, governance, valid_contributor_terms,
):
    """Pending owner blocks initiate AND setManager (including Delta execute)."""
    c = contributor_contract
    setupRipeGovVaultConfig()
    # seed a position via Teller impersonation (deposit-permission-dependent)
    seeded = 1_000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, seeded, sender=whale)
    ripe_gov_vault.depositTokensInVault(c.address, ripe_token, seeded, sender=teller.address)
    _travel_to_ts(c.unlockTime() + 1)

    c.changeOwnership(alice, sender=owner_address)
    # transfer blocked
    with boa.reverts("cannot do with pending ownership change"):
        c.initiateRipeTransfer(sender=owner_address)
    # direct setManager blocked
    with boa.reverts("cannot do with pending ownership change"):
        c.setManager(bob, sender=owner_address)
    # Delta gov+timelock setManager also blocked at execute
    aid = switchboard_delta.setManagerForContributor(c.address, bob, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    with boa.reverts("cannot do with pending ownership change"):
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert c.manager() == valid_contributor_terms["manager"]
    c.cancelOwnershipChange(sender=owner_address)
    # after cancel, the same Delta pending executes
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert c.manager() == bob


def test_g11_owner_set_manager_during_pending_transfer_keeps_recipient(
    human_resources, contributor_contract, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, teller, whale, owner_address, alice,
    valid_contributor_terms,
):
    """Owner setManager during a pending transfer does not change
    pending.recipient; the new manager cannot redirect it."""
    c = contributor_contract
    setupRipeGovVaultConfig()
    seeded = 1_000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, seeded, sender=whale)
    ripe_gov_vault.depositTokensInVault(c.address, ripe_token, seeded, sender=teller.address)
    _travel_to_ts(c.unlockTime() + 1)

    c.initiateRipeTransfer(False, sender=owner_address)
    pending = c.pendingRipeTransfer()
    assert pending.recipient == owner_address
    c.setManager(alice, sender=owner_address)
    assert c.manager() == alice
    assert c.pendingRipeTransfer().recipient == owner_address  # unchanged
    _advance_blocks(pending.confirmBlock - _bn())
    c.confirmRipeTransfer(False, sender=alice)  # new manager confirms
    ev = filter_logs(c, "RipeTransferConfirmed")
    assert len(ev) == 1
    assert ev[0].recipient == owner_address
    assert ev[0].confirmedBy == alice


def test_g11_frozen_handoff_window_and_lite_cancel(
    human_resources, contributor_contract, owner_address, alice,
    switchboard_delta, switchboard_alpha, mission_control, governance,
):
    """Freeze does NOT block ownership handoff. The real cancellation window is
    keyActionDelay blocks from initiate to confirmBlock; lite can cancel only
    while pending. After confirm there is nothing to cancel."""
    c = contributor_contract
    delay = c.keyActionDelay()
    assert delay == human_resources.minActionTimeLock()  # constructor min, no prior KeyActionDelaySet

    mission_control.setCanPerformLiteAction(alice, True, sender=switchboard_alpha.address)
    assert switchboard_delta.freezeContributor(c.address, True, sender=governance.address)

    # initiate while frozen: allowed
    c.changeOwnership(bob := boa.env.generate_address("new_owner"), sender=owner_address)
    p = c.pendingOwner()
    window = p.confirmBlock - p.initiatedBlock
    assert window == delay  # the real cancellation window in blocks

    # lite cancel of the pending handoff works while frozen
    assert switchboard_delta.cancelOwnershipChangeForContributor(c.address, sender=alice)
    assert not c.hasPendingOwnerChange()

    # re-initiate, let it mature, confirm while frozen: allowed
    c.changeOwnership(bob, sender=owner_address)
    p = c.pendingOwner()
    _advance_blocks(p.confirmBlock - _bn())
    c.confirmOwnershipChange(sender=bob)
    assert c.owner() == bob
    # after confirm, Delta cancel has nothing to cancel
    with boa.reverts("no pending change"):
        switchboard_delta.cancelOwnershipChangeForContributor(c.address, sender=alice)
    assert switchboard_delta.freezeContributor(c.address, False, sender=governance.address)


def test_g11_key_action_delay_bounds_from_this_hr(
    human_resources, contributor_contract, owner_address, manager_address,
):
    """Delay bounds come from THIS HR generation (fixture: HQ timelock numbers),
    not the launch 7_200/50_400. Manager cannot setKeyActionDelay."""
    c = contributor_contract
    min_d = human_resources.minActionTimeLock()
    max_d = human_resources.maxActionTimeLock()
    assert (min_d, max_d) == (43_200, 302_400)  # fixture generation
    assert c.keyActionDelay() == min_d

    with boa.reverts("invalid delay"):
        c.setKeyActionDelay(min_d - 1, sender=owner_address)
    with boa.reverts("invalid delay"):
        c.setKeyActionDelay(max_d + 1, sender=owner_address)
    c.setKeyActionDelay(min_d, sender=owner_address)
    c.setKeyActionDelay(max_d, sender=owner_address)
    assert c.keyActionDelay() == max_d
    with boa.reverts("no perms"):
        c.setKeyActionDelay(min_d, sender=manager_address)


def test_g11_unfreeze_restores_cash_and_transfer(
    human_resources, contributor_contract, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, owner_address, switchboard_delta, governance,
):
    """Unfreeze restores cash and transfer after a freeze."""
    setupRipeGovVaultConfig()
    c = contributor_contract
    _travel_to_ts(c.startTime() + 30 * 24 * 3600)
    assert switchboard_delta.freezeContributor(c.address, True, sender=governance.address)
    assert c.cashRipeCheck(sender=owner_address) == 0
    with boa.reverts("contract frozen"):
        c.initiateRipeTransfer(sender=owner_address)
    assert switchboard_delta.freezeContributor(c.address, False, sender=governance.address)
    amt = c.cashRipeCheck(sender=owner_address)
    assert amt > 0
    _travel_to_ts(c.unlockTime() + 1)
    c.initiateRipeTransfer(sender=owner_address)
    assert c.hasPendingRipeTransfer()
