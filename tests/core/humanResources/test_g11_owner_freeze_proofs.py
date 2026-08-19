import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS
from tests.core.humanResources.g11_proof_helpers import (
    grant_lite,
    official_freeze,
    pending_owner,
    pending_transfer,
    travel_to_block,
    travel_to_ts,
)


def _prep(setupRipeGovVaultConfig):
    setupRipeGovVaultConfig()


def _position(contributor, owner):
    travel_to_ts(contributor.startTime() + 1)
    assert contributor.cashRipeCheck(sender=owner) > 0
    travel_to_ts(contributor.unlockTime() + 1)


def test_g11_confirm_ownership_is_new_owner_only(
    contributor_contract,
    owner_address,
    manager_address,
    alice,
    switchboard_delta,
    governance,
):
    c = contributor_contract
    c.changeOwnership(alice, sender=owner_address)
    travel_to_block(c.pendingOwner().confirmBlock)
    with boa.reverts("only new owner can confirm"):
        c.confirmOwnershipChange(sender=owner_address)
    with boa.reverts("only new owner can confirm"):
        c.confirmOwnershipChange(sender=manager_address)
    with boa.reverts("only new owner can confirm"):
        c.confirmOwnershipChange(sender=governance.address)
    c.confirmOwnershipChange(sender=alice)
    assert c.owner() == alice


def test_g11_change_ownership_rejects_empty_self_current(
    contributor_contract,
    owner_address,
):
    c = contributor_contract
    with boa.reverts("invalid new owner"):
        c.changeOwnership(ZERO_ADDRESS, sender=owner_address)
    with boa.reverts("invalid new owner"):
        c.changeOwnership(owner_address, sender=owner_address)
    with boa.reverts("invalid new owner"):
        c.changeOwnership(c.address, sender=owner_address)


def test_g11_pending_transfer_blocks_ownership_initiate(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    alice,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    _position(c, owner_address)
    c.initiateRipeTransfer(False, sender=owner_address)
    with boa.reverts("cannot do with pending ripe transfer"):
        c.changeOwnership(alice, sender=owner_address)


def test_g11_pending_owner_blocks_transfer_and_set_manager_including_delta(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    manager_address,
    alice,
    bob,
    switchboard_delta,
    governance,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    _position(c, owner_address)
    c.changeOwnership(alice, sender=owner_address)
    with boa.reverts("cannot do with pending ownership change"):
        c.initiateRipeTransfer(False, sender=owner_address)
    with boa.reverts("cannot do with pending ownership change"):
        c.setManager(bob, sender=owner_address)
    aid = switchboard_delta.setManagerForContributor(
        c.address, bob, sender=governance.address
    )
    travel_to_block(switchboard_delta.getActionConfirmationBlock(aid))
    with boa.reverts("cannot do with pending ownership change"):
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert switchboard_delta.actionType(aid) != 0
    c.cancelOwnershipChange(sender=owner_address)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert c.manager() == bob


def test_g11_owner_set_manager_during_pending_transfer_does_not_change_recipient(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    alice,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    _position(c, owner_address)
    c.initiateRipeTransfer(False, sender=owner_address)
    c.setManager(alice, sender=owner_address)
    assert c.manager() == alice
    assert pending_transfer(c)[0] == owner_address


def test_g11_lite_freeze_and_cancel_pending_handoff(
    contributor_contract,
    owner_address,
    alice,
    switchboard_delta,
    governance,
    mission_control,
):
    c = contributor_contract
    c.changeOwnership(alice, sender=owner_address)
    grant_lite(mission_control, switchboard_delta, alice)
    assert switchboard_delta.freezeContributor(c.address, True, sender=alice)
    assert c.isFrozen()
    assert switchboard_delta.cancelOwnershipChangeForContributor(c.address, sender=alice)
    assert not c.hasPendingOwnerChange()
    window = c.keyActionDelay()
    assert window == c.keyActionDelay()


def test_g11_freeze_then_initiate_confirm_handoff_no_pending_to_cancel(
    contributor_contract,
    owner_address,
    alice,
    switchboard_delta,
    governance,
):
    c = contributor_contract
    official_freeze(switchboard_delta, governance, c, True)
    initiate_block = boa.env.evm.patch.block_number
    c.changeOwnership(alice, sender=owner_address)
    confirm = c.pendingOwner().confirmBlock
    window = confirm - initiate_block
    assert window == c.keyActionDelay()
    travel_to_block(confirm)
    c.confirmOwnershipChange(sender=alice)
    assert c.owner() == alice
    assert not c.hasPendingOwnerChange()
    with boa.reverts("no pending change"):
        c.cancelOwnershipChange(sender=alice)
    with boa.reverts("no pending change"):
        switchboard_delta.cancelOwnershipChangeForContributor(
            c.address, sender=governance.address
        )


def test_g11_default_minimum_handoff_has_no_delay_event(
    contributor_contract,
    owner_address,
    alice,
    human_resources,
):
    c = contributor_contract
    assert c.keyActionDelay() == human_resources.minActionTimeLock()
    c.changeOwnership(alice, sender=owner_address)
    assert filter_logs(c, "KeyActionDelaySet") == []
    assert pending_owner(c)[2] == boa.env.evm.patch.block_number + c.keyActionDelay()


def test_g11_raised_then_lowered_delay_emits_before_initiate_same_block_ok(
    contributor_contract,
    owner_address,
    alice,
    human_resources,
):
    c = contributor_contract
    minimum = human_resources.minActionTimeLock()
    maximum = human_resources.maxActionTimeLock()
    c.setKeyActionDelay(maximum, sender=owner_address)
    assert filter_logs(c, "KeyActionDelaySet")[0].numBlocks == maximum
    c.setKeyActionDelay(minimum, sender=owner_address)
    assert filter_logs(c, "KeyActionDelaySet")[0].numBlocks == minimum
    c.changeOwnership(alice, sender=owner_address)
    assert c.pendingOwner().confirmBlock == boa.env.evm.patch.block_number + minimum


def test_g11_delay_change_after_initiate_does_not_retime(
    contributor_contract,
    owner_address,
    alice,
    human_resources,
):
    c = contributor_contract
    c.changeOwnership(alice, sender=owner_address)
    confirm = c.pendingOwner().confirmBlock
    c.setKeyActionDelay(human_resources.maxActionTimeLock(), sender=owner_address)
    assert c.pendingOwner().confirmBlock == confirm


def test_g11_key_action_delay_bounds_from_this_hr(
    contributor_contract,
    owner_address,
    human_resources,
):
    c = contributor_contract
    minimum = human_resources.minActionTimeLock()
    maximum = human_resources.maxActionTimeLock()
    assert (minimum, maximum) == (43_200, 302_400)
    with boa.reverts("invalid delay"):
        c.setKeyActionDelay(minimum - 1, sender=owner_address)
    with boa.reverts("invalid delay"):
        c.setKeyActionDelay(maximum + 1, sender=owner_address)
    c.setKeyActionDelay(minimum, sender=owner_address)
    c.setKeyActionDelay(maximum, sender=owner_address)


def test_g11_pending_ownership_is_cancel_replace_timer_restarts(
    contributor_contract,
    owner_address,
    alice,
    bob,
):
    c = contributor_contract
    c.changeOwnership(alice, sender=owner_address)
    first = c.pendingOwner().confirmBlock
    boa.env.time_travel(blocks=10)
    c.changeOwnership(bob, sender=owner_address)
    second = c.pendingOwner()
    assert second.newOwner == bob
    assert second.confirmBlock == boa.env.evm.patch.block_number + c.keyActionDelay()
    assert second.confirmBlock > first


def test_g11_manager_cannot_change_ownership_or_delay(
    contributor_contract,
    manager_address,
    alice,
    human_resources,
):
    c = contributor_contract
    with boa.reverts("no perms"):
        c.changeOwnership(alice, sender=manager_address)
    with boa.reverts("no perms"):
        c.setKeyActionDelay(human_resources.maxActionTimeLock(), sender=manager_address)


def test_g11_unfreeze_restores_cash_and_transfer(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    switchboard_delta,
    governance,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.startTime() + 1)
    official_freeze(switchboard_delta, governance, c, True)
    assert c.cashRipeCheck(sender=owner_address) == 0
    official_freeze(switchboard_delta, governance, c, False)
    assert c.cashRipeCheck(sender=owner_address) > 0
    travel_to_ts(c.unlockTime() + 1)
    official_freeze(switchboard_delta, governance, c, True)
    with boa.reverts("contract frozen"):
        c.initiateRipeTransfer(False, sender=owner_address)
    official_freeze(switchboard_delta, governance, c, False)
    c.initiateRipeTransfer(False, sender=owner_address)
    assert c.hasPendingRipeTransfer()
