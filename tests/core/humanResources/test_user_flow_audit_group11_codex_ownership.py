"""Focused Group 11 owner/manager pending-state exclusion proofs."""

import boa

from contracts.modules import Contributor


def _advance_to_block(block_number):
    current = boa.env.evm.patch.block_number
    if current < block_number:
        boa.env.time_travel(blocks=block_number - current)
    assert boa.env.evm.patch.block_number >= block_number


def _advance_to_timestamp(timestamp):
    current = boa.env.evm.patch.timestamp
    if current < timestamp:
        boa.env.time_travel(seconds=timestamp - current)
    assert boa.env.evm.patch.timestamp == timestamp


def test_g11_owner_change_new_owner_only_and_invalid_recipients(
    contributor_contract,
    owner_address,
    manager_address,
    alice,
    switchboard_delta,
):
    """No owner/manager/Switchboard caller can self-select a completed owner."""
    with boa.reverts("invalid new owner"):
        contributor_contract.changeOwnership("0x" + "00" * 20, sender=owner_address)
    with boa.reverts("invalid new owner"):
        contributor_contract.changeOwnership(owner_address, sender=owner_address)
    with boa.reverts("invalid new owner"):
        contributor_contract.changeOwnership(
            contributor_contract.address, sender=owner_address
        )

    contributor_contract.changeOwnership(alice, sender=owner_address)
    pending = contributor_contract.pendingOwner()
    _advance_to_block(pending.confirmBlock)
    with boa.reverts("only new owner can confirm"):
        contributor_contract.confirmOwnershipChange(sender=owner_address)
    with boa.reverts("only new owner can confirm"):
        contributor_contract.confirmOwnershipChange(sender=manager_address)
    with boa.reverts("only new owner can confirm"):
        contributor_contract.confirmOwnershipChange(sender=switchboard_delta.address)
    contributor_contract.confirmOwnershipChange(sender=alice)
    assert contributor_contract.owner() == alice


def test_g11_pending_transfer_keeps_recipient_through_manager_rotation(
    deployedContributor,
    valid_contributor_terms,
    setupRipeGovVaultConfig,
    ripe_token,
    ripe_gov_vault,
    owner_address,
    alice,
):
    """An owner may recover from manager grief but cannot change stored recipient."""
    setupRipeGovVaultConfig()
    contributor = Contributor.at(deployedContributor(dict(valid_contributor_terms)))
    _advance_to_timestamp(contributor.startTime() + 1)
    assert contributor.cashRipeCheck(sender=owner_address) > 0
    _advance_to_timestamp(contributor.unlockTime() + 1)
    contributor.initiateRipeTransfer(False, sender=owner_address)
    pending = contributor.pendingRipeTransfer()
    position = ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
    contributor.setManager(alice, sender=owner_address)
    assert contributor.pendingRipeTransfer() == pending
    assert pending.recipient == owner_address
    assert contributor.manager() == alice
    with boa.reverts("cannot do with pending ripe transfer"):
        contributor.changeOwnership(alice, sender=owner_address)

    _advance_to_block(pending.confirmBlock)
    owner_before = ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
    contributor.confirmRipeTransfer(False, sender=alice)
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == 0
    assert (
        ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
        == owner_before + position
    )
    assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) == 0


def test_g11_pending_owner_blocks_transfer_and_governed_manager_execution_until_cancel(
    contributor_contract,
    switchboard_delta,
    governance,
    owner_address,
    alice,
    bob,
):
    """A failed Delta manager execution is retryable once pending owner clears."""
    contributor_contract.changeOwnership(alice, sender=owner_address)
    with boa.reverts("cannot do with pending ownership change"):
        contributor_contract.initiateRipeTransfer(False, sender=owner_address)
    with boa.reverts("cannot do with pending ownership change"):
        contributor_contract.setManager(bob, sender=owner_address)

    manager_action = switchboard_delta.setManagerForContributor(
        contributor_contract.address, bob, sender=governance.address
    )
    _advance_to_block(switchboard_delta.getActionConfirmationBlock(manager_action))
    with boa.reverts():
        switchboard_delta.executePendingAction(manager_action, sender=governance.address)
    assert switchboard_delta.hasPendingAction(manager_action)

    contributor_contract.cancelOwnershipChange(sender=owner_address)
    assert switchboard_delta.executePendingAction(manager_action, sender=governance.address)
    assert contributor_contract.manager() == bob
