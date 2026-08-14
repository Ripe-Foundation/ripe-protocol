import boa

from conf_utils import filter_logs
from tests.core.humanResources.contributor_test_utils import (
    initiate_transfer,
    prepare_transferable_position,
)


def test_pending_ripe_transfer_blocks_ownership_change(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    alice,
    valid_contributor_terms,
):
    initiate_transfer(
        contributor_contract,
        setupRipeGovVaultConfig,
        ripe_gov_vault,
        ripe_token,
        whale,
        teller,
        owner_address,
        valid_contributor_terms,
    )
    pending_transfer = contributor_contract.pendingRipeTransfer()

    with boa.reverts("cannot do with pending ripe transfer"):
        contributor_contract.changeOwnership(alice, sender=owner_address)

    assert contributor_contract.owner() == owner_address
    assert not contributor_contract.hasPendingOwnerChange()
    assert contributor_contract.pendingRipeTransfer() == pending_transfer


def test_cancelled_ripe_transfer_restores_ownership_change(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    alice,
    valid_contributor_terms,
):
    initiate_transfer(
        contributor_contract,
        setupRipeGovVaultConfig,
        ripe_gov_vault,
        ripe_token,
        whale,
        teller,
        owner_address,
        valid_contributor_terms,
    )

    with boa.reverts("cannot do with pending ripe transfer"):
        contributor_contract.changeOwnership(alice, sender=owner_address)

    contributor_contract.cancelRipeTransfer(sender=owner_address)
    assert not contributor_contract.hasPendingRipeTransfer()

    contributor_contract.changeOwnership(alice, sender=owner_address)
    assert contributor_contract.hasPendingOwnerChange()
    assert contributor_contract.pendingOwner()[0] == alice


def test_confirmed_ripe_transfer_restores_ownership_change(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    alice,
    valid_contributor_terms,
):
    initiate_transfer(
        contributor_contract,
        setupRipeGovVaultConfig,
        ripe_gov_vault,
        ripe_token,
        whale,
        teller,
        owner_address,
        valid_contributor_terms,
    )

    with boa.reverts("cannot do with pending ripe transfer"):
        contributor_contract.changeOwnership(alice, sender=owner_address)

    boa.env.time_travel(blocks=contributor_contract.keyActionDelay())
    contributor_contract.confirmRipeTransfer(sender=owner_address)
    assert not contributor_contract.hasPendingRipeTransfer()
    assert ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token) > 0

    contributor_contract.changeOwnership(alice, sender=owner_address)
    assert contributor_contract.hasPendingOwnerChange()
    assert contributor_contract.pendingOwner()[0] == alice


def test_pending_ownership_change_still_blocks_ripe_transfer(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    alice,
    valid_contributor_terms,
):
    prepare_transferable_position(
        contributor_contract,
        setupRipeGovVaultConfig,
        ripe_gov_vault,
        ripe_token,
        whale,
        teller,
        valid_contributor_terms,
    )
    contributor_contract.changeOwnership(alice, sender=owner_address)
    pending_owner = contributor_contract.pendingOwner()

    with boa.reverts("cannot do with pending ownership change"):
        contributor_contract.initiateRipeTransfer(sender=owner_address)

    assert contributor_contract.pendingOwner() == pending_owner
    assert not contributor_contract.hasPendingRipeTransfer()


def test_normal_ownership_handoff_still_works(
    contributor_contract,
    owner_address,
    alice,
):
    assert not contributor_contract.hasPendingRipeTransfer()
    contributor_contract.changeOwnership(alice, sender=owner_address)

    boa.env.time_travel(blocks=contributor_contract.keyActionDelay())
    contributor_contract.confirmOwnershipChange(sender=alice)

    assert contributor_contract.owner() == alice
    assert not contributor_contract.hasPendingOwnerChange()
    assert not contributor_contract.hasPendingRipeTransfer()


def test_normal_ripe_transfer_still_works(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    valid_contributor_terms,
):
    owner_balance_before = ripe_gov_vault.getTotalAmountForUser(
        owner_address, ripe_token
    )
    initiate_transfer(
        contributor_contract,
        setupRipeGovVaultConfig,
        ripe_gov_vault,
        ripe_token,
        whale,
        teller,
        owner_address,
        valid_contributor_terms,
    )
    initiated_events = filter_logs(contributor_contract, "RipeTransferInitiated")
    pending_transfer = contributor_contract.pendingRipeTransfer()

    assert len(initiated_events) == 1
    assert initiated_events[0].owner == owner_address
    assert initiated_events[0].initiatedBy == owner_address
    assert initiated_events[0].confirmBlock == pending_transfer[2]
    assert pending_transfer[0] == owner_address
    assert (
        pending_transfer[2]
        == pending_transfer[1] + contributor_contract.keyActionDelay()
    )

    boa.env.time_travel(blocks=contributor_contract.keyActionDelay())
    contributor_contract.confirmRipeTransfer(sender=owner_address)
    confirmed_events = filter_logs(contributor_contract, "RipeTransferConfirmed")

    assert len(confirmed_events) == 1
    assert confirmed_events[0].recipient == owner_address
    assert confirmed_events[0].confirmedBy == owner_address
    assert confirmed_events[0].initiatedBlock == pending_transfer[1]
    assert confirmed_events[0].amount > 0
    assert (
        ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
        == owner_balance_before + confirmed_events[0].amount
    )
    assert not ripe_gov_vault.doesUserHaveBalance(contributor_contract, ripe_token)
    assert not contributor_contract.hasPendingRipeTransfer()
    assert not contributor_contract.hasPendingOwnerChange()
