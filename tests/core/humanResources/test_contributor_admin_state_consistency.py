import json
from pathlib import Path

import boa
import pytest
from eth_abi import decode

from conf_utils import filter_logs
from config.robinhood_launch import HR_MAX_TIMELOCK, HR_MIN_TIMELOCK
from constants import ZERO_ADDRESS
from tests.core.humanResources.contributor_test_utils import (
    initiate_transfer,
    prepare_transferable_position,
)


ROOT = Path(__file__).resolve().parents[3]


def _freeze(switchboard_delta, governance, contributor, should_freeze=True):
    assert switchboard_delta.freezeContributor(
        contributor.address,
        should_freeze,
        sender=governance.address,
    )
    events = filter_logs(switchboard_delta, "ContributorFrozenFromSwitchboard")
    assert len(events) == 1
    assert events[0].contributor == contributor.address
    assert events[0].shouldFreeze is should_freeze
    assert contributor.isFrozen() is should_freeze
    return events


def _advance_to(block_number):
    current = boa.env.evm.patch.block_number
    if current < block_number:
        boa.env.time_travel(blocks=block_number - current)
    assert boa.env.evm.patch.block_number >= block_number


def test_fixture_hr_provenance_and_default_delay(
    human_resources,
    contributor_contract,
):
    minimum = human_resources.minActionTimeLock()
    maximum = human_resources.maxActionTimeLock()

    assert minimum == 43_200
    assert maximum == 302_400
    assert contributor_contract.keyActionDelay() == minimum


def test_current_robinhood_hr_migration_source_declares_canonical_bounds():
    # Current migration text records source intent; later edits do not prove
    # which version executed or what the live deployment currently stores.
    migrations = ROOT / "migrations" / "robinhood-mainnet"
    launch = (migrations / "0005_Departments.py").read_text()
    replacement = (migrations / "0009_RedeployStaleContracts.py").read_text()
    for source in (launch, replacement):
        assert "HR_MIN_TIMELOCK" in source
        assert "HR_MAX_TIMELOCK" in source


def test_robinhood_manifest_records_hr_constructor_bounds():
    manifest = json.loads(
        (
            ROOT
            / "migration_history"
            / "robinhood-mainnet"
            / "v1"
            / "current-manifest.json"
        ).read_text()
    )
    record = manifest["contracts"]["HumanResources"]
    hq, minimum, maximum = decode(
        ["address", "uint256", "uint256"],
        bytes.fromhex(record["args"]),
    )
    assert hq.lower() == "0xd4e82ae1de673bba3b53386a2d2c630ae6630940"
    assert int(record["address"], 16) != 0
    assert (minimum, maximum) == (HR_MIN_TIMELOCK, HR_MAX_TIMELOCK)
    assert (minimum, maximum) == (7_200, 50_400)


def test_default_minimum_frozen_handoff_has_only_initiation_warning_and_can_cancel(
    contributor_contract,
    human_resources,
    switchboard_delta,
    governance,
    owner_address,
    alice,
):
    minimum = human_resources.minActionTimeLock()
    assert contributor_contract.keyActionDelay() == minimum
    freeze_logs = _freeze(switchboard_delta, governance, contributor_contract)
    assert contributor_contract.keyActionDelay() == minimum

    contributor_contract.changeOwnership(alice, sender=owner_address)
    handoff_logs = contributor_contract.get_logs()
    observed_events = [type(log).__name__ for log in [*freeze_logs, *handoff_logs]]
    assert "ContributorFrozenFromSwitchboard" in observed_events
    assert "OwnershipChangeInitiated" in observed_events
    assert "KeyActionDelaySet" not in observed_events
    assert contributor_contract.keyActionDelay() == minimum
    initiated = [
        log for log in handoff_logs if type(log).__name__ == "OwnershipChangeInitiated"
    ]
    assert len(initiated) == 1
    pending = contributor_contract.pendingOwner()
    assert pending[2] - pending[1] == minimum
    assert initiated[0].confirmBlock == pending[2]

    boa.env.time_travel(blocks=minimum - 1)
    assert boa.env.evm.patch.block_number == pending[2] - 1
    assert switchboard_delta.cancelOwnershipChangeForContributor(
        contributor_contract.address,
        sender=governance.address,
    )
    assert not contributor_contract.hasPendingOwnerChange()
    assert contributor_contract.owner() == owner_address
    assert contributor_contract.isFrozen()


def test_default_minimum_frozen_handoff_completes_without_economic_bypass(
    contributor_contract,
    human_resources,
    switchboard_delta,
    governance,
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
    contributor_position = ripe_gov_vault.getTotalAmountForUser(
        contributor_contract, ripe_token
    )
    owner_position = ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
    assert contributor_position > 0

    _freeze(switchboard_delta, governance, contributor_contract)
    contributor_contract.changeOwnership(alice, sender=owner_address)
    pending = contributor_contract.pendingOwner()
    assert pending[2] - pending[1] == human_resources.minActionTimeLock()
    _advance_to(pending[2])
    contributor_contract.confirmOwnershipChange(sender=alice)

    assert contributor_contract.owner() == alice
    assert contributor_contract.isFrozen()
    assert (
        ripe_gov_vault.getTotalAmountForUser(contributor_contract, ripe_token)
        == contributor_position
    )
    assert (
        ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
        == owner_position
    )
    claimable_before = contributor_contract.getClaimable()
    claimed_before = contributor_contract.totalClaimed()
    assert claimable_before > 0
    assert contributor_contract.cashRipeCheck(sender=alice) == 0
    assert contributor_contract.totalClaimed() == claimed_before
    with boa.reverts("contract frozen"):
        contributor_contract.initiateRipeTransfer(sender=alice)
    with boa.reverts("contract frozen"):
        contributor_contract.confirmRipeTransfer(sender=alice)
    with boa.reverts("contract frozen"):
        contributor_contract.delegateTo(
            ripe_gov_vault, owner_address, 10_000, sender=alice
        )
    with boa.reverts("contract frozen"):
        contributor_contract.removeDelegationFor(
            ripe_gov_vault,
            owner_address,
            sender=alice,
        )


def test_confirmed_hostile_handoff_is_irreversible_and_can_drain_after_unfreeze(
    contributor_contract,
    switchboard_delta,
    governance,
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
    contributor_position = ripe_gov_vault.getTotalAmountForUser(
        contributor_contract, ripe_token
    )
    attacker_position = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)

    _freeze(switchboard_delta, governance, contributor_contract)
    contributor_contract.changeOwnership(alice, sender=owner_address)
    _advance_to(contributor_contract.pendingOwner()[2])
    contributor_contract.confirmOwnershipChange(sender=alice)

    with boa.reverts("no pending change"):
        switchboard_delta.cancelOwnershipChangeForContributor(
            contributor_contract.address,
            sender=governance.address,
        )

    _freeze(switchboard_delta, governance, contributor_contract, False)
    contributor_contract.initiateRipeTransfer(False, sender=alice)
    pending = contributor_contract.pendingRipeTransfer()
    assert pending[0] == alice
    _advance_to(pending[2])
    contributor_contract.confirmRipeTransfer(False, sender=alice)

    assert ripe_gov_vault.getTotalAmountForUser(contributor_contract, ripe_token) == 0
    assert (
        ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
        == attacker_position + contributor_position
    )


@pytest.mark.parametrize("should_cancel", [True, False], ids=["cancel", "confirm"])
def test_scenario_b_raised_then_lowered_frozen_handoff(
    should_cancel,
    contributor_contract,
    human_resources,
    switchboard_delta,
    governance,
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
    contributor_position = ripe_gov_vault.getTotalAmountForUser(
        contributor_contract, ripe_token
    )
    owner_position = ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
    minimum = human_resources.minActionTimeLock()
    contributor_contract.setKeyActionDelay(minimum + 100, sender=owner_address)
    _freeze(switchboard_delta, governance, contributor_contract)

    contributor_contract.setKeyActionDelay(minimum, sender=owner_address)
    delay_events = filter_logs(contributor_contract, "KeyActionDelaySet")
    assert len(delay_events) == 1
    assert delay_events[0].numBlocks == minimum

    contributor_contract.changeOwnership(alice, sender=owner_address)
    pending = contributor_contract.pendingOwner()
    assert pending[2] - pending[1] == minimum
    boa.env.time_travel(blocks=minimum - 1)
    if should_cancel:
        assert switchboard_delta.cancelOwnershipChangeForContributor(
            contributor_contract.address,
            sender=governance.address,
        )
        assert contributor_contract.owner() == owner_address
    else:
        boa.env.time_travel(blocks=1)
        contributor_contract.confirmOwnershipChange(sender=alice)
        assert contributor_contract.owner() == alice
        assert contributor_contract.getClaimable() > 0
        assert contributor_contract.cashRipeCheck(sender=alice) == 0
        with boa.reverts("contract frozen"):
            contributor_contract.initiateRipeTransfer(False, sender=alice)
    assert contributor_contract.isFrozen()
    assert (
        ripe_gov_vault.getTotalAmountForUser(contributor_contract, ripe_token)
        == contributor_position
    )
    assert (
        ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
        == owner_position
    )


def test_ownership_initiated_before_freeze_can_confirm_after_freeze(
    contributor_contract,
    switchboard_delta,
    governance,
    owner_address,
    alice,
):
    contributor_contract.changeOwnership(alice, sender=owner_address)
    pending = contributor_contract.pendingOwner()
    _freeze(switchboard_delta, governance, contributor_contract)
    _advance_to(pending[2])

    contributor_contract.confirmOwnershipChange(sender=alice)
    assert contributor_contract.owner() == alice
    assert contributor_contract.isFrozen()


def test_lite_action_signer_can_freeze_and_cancel_frozen_handoff(
    contributor_contract,
    mission_control,
    switchboard_alpha,
    switchboard_delta,
    owner_address,
    alice,
):
    mission_control.setCanPerformLiteAction(
        alice,
        True,
        sender=switchboard_alpha.address,
    )
    assert mission_control.canPerformLiteAction(alice)
    assert switchboard_delta.freezeContributor(
        contributor_contract.address,
        True,
        sender=alice,
    )
    with boa.reverts("no perms"):
        switchboard_delta.freezeContributor(
            contributor_contract.address,
            False,
            sender=alice,
        )
    assert contributor_contract.isFrozen()

    contributor_contract.changeOwnership(alice, sender=owner_address)
    assert switchboard_delta.cancelOwnershipChangeForContributor(
        contributor_contract.address,
        sender=alice,
    )
    assert not contributor_contract.hasPendingOwnerChange()
    assert contributor_contract.owner() == owner_address
    assert contributor_contract.isFrozen()


@pytest.mark.parametrize("canceller", ["owner", "manager"])
def test_participant_cancellation_stays_available_while_frozen(
    canceller,
    contributor_contract,
    switchboard_delta,
    governance,
    owner_address,
    manager_address,
    alice,
):
    contributor_contract.changeOwnership(alice, sender=owner_address)
    _freeze(switchboard_delta, governance, contributor_contract)
    caller = owner_address if canceller == "owner" else manager_address

    contributor_contract.cancelOwnershipChange(sender=caller)
    assert not contributor_contract.hasPendingOwnerChange()
    assert contributor_contract.isFrozen()


def test_pending_transfer_freeze_blocks_confirmation_but_governance_can_cancel(
    contributor_contract,
    switchboard_delta,
    governance,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
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
    pending = contributor_contract.pendingRipeTransfer()
    position = ripe_gov_vault.getTotalAmountForUser(contributor_contract, ripe_token)
    _freeze(switchboard_delta, governance, contributor_contract)
    _advance_to(pending[2])

    with boa.reverts("contract frozen"):
        contributor_contract.confirmRipeTransfer(sender=owner_address)
    assert contributor_contract.pendingRipeTransfer() == pending
    assert (
        ripe_gov_vault.getTotalAmountForUser(contributor_contract, ripe_token)
        == position
    )
    assert switchboard_delta.cancelRipeTransferForContributor(
        contributor_contract.address,
        sender=governance.address,
    )
    assert not contributor_contract.hasPendingRipeTransfer()
    assert (
        ripe_gov_vault.getTotalAmountForUser(contributor_contract, ripe_token)
        == position
    )


@pytest.mark.parametrize("canceller", ["owner", "manager"])
def test_participant_can_cancel_pending_transfer_while_frozen(
    canceller,
    contributor_contract,
    switchboard_delta,
    governance,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    manager_address,
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
    _freeze(switchboard_delta, governance, contributor_contract)
    caller = owner_address if canceller == "owner" else manager_address

    contributor_contract.cancelRipeTransfer(sender=caller)
    assert not contributor_contract.hasPendingRipeTransfer()
    assert contributor_contract.isFrozen()


def test_owner_admin_and_governed_manager_recovery_stay_available_while_frozen(
    contributor_contract,
    human_resources,
    switchboard_delta,
    governance,
    owner_address,
    alice,
    bob,
):
    _freeze(switchboard_delta, governance, contributor_contract)
    contributor_contract.setManager(alice, sender=owner_address)
    contributor_contract.setKeyActionDelay(
        human_resources.minActionTimeLock() + 1,
        sender=owner_address,
    )
    assert contributor_contract.manager() == alice

    aid = switchboard_delta.setManagerForContributor(
        contributor_contract.address,
        bob,
        sender=governance.address,
    )
    _advance_to(switchboard_delta.getActionConfirmationBlock(aid))
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert contributor_contract.manager() == bob
    assert contributor_contract.isFrozen()


def test_frozen_paycheck_cancellation_forfeits_vested_unclaimed_compensation(
    contributor_contract,
    switchboard_delta,
    governance,
    valid_contributor_terms,
):
    boa.env.time_travel(
        seconds=(
            valid_contributor_terms["startDelay"]
            + valid_contributor_terms["cliffLength"]
            + 1
        )
    )
    claimable_before = contributor_contract.getClaimable()
    claimed_before = contributor_contract.totalClaimed()
    compensation_before = contributor_contract.compensation()
    assert claimable_before > 0
    assert compensation_before > claimable_before
    assert claimed_before == 0

    _freeze(switchboard_delta, governance, contributor_contract)
    aid = switchboard_delta.cancelPaycheckForContributor(
        contributor_contract.address,
        sender=governance.address,
    )
    _advance_to(switchboard_delta.getActionConfirmationBlock(aid))

    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    cancellation = filter_logs(switchboard_delta, "HrContributorCancelPaycheckSet")
    assert len(cancellation) == 1
    assert cancellation[0].contributor == contributor_contract.address
    assert contributor_contract.totalClaimed() == claimed_before
    assert contributor_contract.compensation() == claimed_before
    assert contributor_contract.getClaimable() == 0
    assert contributor_contract.isFrozen()


def test_unfreeze_preserves_pending_ownership_and_restores_normal_lifecycle(
    contributor_contract,
    switchboard_delta,
    governance,
    owner_address,
    alice,
):
    contributor_contract.changeOwnership(alice, sender=owner_address)
    pending = contributor_contract.pendingOwner()
    _freeze(switchboard_delta, governance, contributor_contract)
    _freeze(switchboard_delta, governance, contributor_contract, False)

    assert contributor_contract.pendingOwner() == pending
    _advance_to(pending[2])
    contributor_contract.confirmOwnershipChange(sender=alice)
    assert contributor_contract.owner() == alice


def test_unfreeze_restores_legitimate_economic_operations(
    contributor_contract,
    switchboard_delta,
    governance,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
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
    position = ripe_gov_vault.getTotalAmountForUser(contributor_contract, ripe_token)
    owner_before = ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
    _freeze(switchboard_delta, governance, contributor_contract)

    with boa.reverts("contract frozen"):
        contributor_contract.initiateRipeTransfer(False, sender=owner_address)

    _freeze(switchboard_delta, governance, contributor_contract, False)
    contributor_contract.initiateRipeTransfer(False, sender=owner_address)
    _advance_to(contributor_contract.pendingRipeTransfer()[2])
    contributor_contract.confirmRipeTransfer(False, sender=owner_address)

    assert (
        ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
        == owner_before + position
    )
    assert not contributor_contract.hasPendingRipeTransfer()


def test_delay_change_after_ownership_initiation_does_not_retime_pending_action(
    contributor_contract,
    human_resources,
    owner_address,
    alice,
):
    contributor_contract.changeOwnership(alice, sender=owner_address)
    pending = contributor_contract.pendingOwner()
    contributor_contract.setKeyActionDelay(
        human_resources.minActionTimeLock() + 100,
        sender=owner_address,
    )

    assert contributor_contract.pendingOwner() == pending
    assert contributor_contract.keyActionDelay() > pending[2] - pending[1]


def test_pending_ownership_initiation_is_cancel_replace_with_timer_restart(
    contributor_contract,
    owner_address,
    alice,
    bob,
):
    contributor_contract.changeOwnership(alice, sender=owner_address)
    first = contributor_contract.pendingOwner()
    boa.env.time_travel(blocks=1)
    contributor_contract.changeOwnership(bob, sender=owner_address)
    second = contributor_contract.pendingOwner()

    assert second[0] == bob
    assert second[1] == first[1] + 1
    assert second[2] == first[2] + 1


def test_pending_ripe_transfer_restart_preserves_recipient_and_position(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
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
    first = contributor_contract.pendingRipeTransfer()
    position = ripe_gov_vault.getTotalAmountForUser(contributor_contract, ripe_token)
    boa.env.time_travel(blocks=1)
    contributor_contract.initiateRipeTransfer(False, sender=owner_address)
    second = contributor_contract.pendingRipeTransfer()

    assert second[0] == first[0] == owner_address
    assert second[1] == first[1] + 1
    assert second[2] == first[2] + 1
    assert (
        ripe_gov_vault.getTotalAmountForUser(contributor_contract, ripe_token)
        == position
    )


def test_direct_manager_rotation_cannot_change_pending_transfer_economics(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    manager_address,
    alice,
    valid_contributor_terms,
):
    owner_before = ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
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
    pending = contributor_contract.pendingRipeTransfer()
    position = ripe_gov_vault.getTotalAmountForUser(contributor_contract, ripe_token)

    contributor_contract.setManager(alice, sender=owner_address)
    assert contributor_contract.pendingRipeTransfer() == pending
    assert contributor_contract.owner() == owner_address
    assert contributor_contract.manager() == alice
    assert (
        ripe_gov_vault.getTotalAmountForUser(contributor_contract, ripe_token)
        == position
    )
    with boa.reverts("no perms"):
        contributor_contract.confirmRipeTransfer(False, sender=manager_address)
    with boa.reverts("no perms"):
        contributor_contract.cancelRipeTransfer(sender=manager_address)

    _advance_to(pending[2])
    contributor_contract.confirmRipeTransfer(False, sender=alice)
    assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(manager_address, ripe_token) == 0
    assert (
        ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
        == owner_before + position
    )


@pytest.mark.parametrize("resolution", ["confirm", "cancel"])
def test_owner_can_resolve_transfer_after_manager_rotation_and_replace_manager_again(
    resolution,
    contributor_contract,
    switchboard_delta,
    governance,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    alice,
    bob,
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
    contributor_contract.setManager(alice, sender=owner_address)

    if resolution == "confirm":
        _advance_to(contributor_contract.pendingRipeTransfer()[2])
        contributor_contract.confirmRipeTransfer(False, sender=owner_address)
    else:
        contributor_contract.cancelRipeTransfer(sender=owner_address)
    assert not contributor_contract.hasPendingRipeTransfer()

    aid = switchboard_delta.setManagerForContributor(
        contributor_contract.address,
        bob,
        sender=governance.address,
    )
    _advance_to(switchboard_delta.getActionConfirmationBlock(aid))
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert contributor_contract.manager() == bob


def test_governed_manager_rotation_executes_when_transfer_predates_queue(
    contributor_contract,
    switchboard_delta,
    governance,
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
    pending = contributor_contract.pendingRipeTransfer()
    aid = switchboard_delta.setManagerForContributor(
        contributor_contract.address,
        alice,
        sender=governance.address,
    )
    _advance_to(switchboard_delta.getActionConfirmationBlock(aid))

    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert contributor_contract.manager() == alice
    assert contributor_contract.pendingRipeTransfer() == pending


def test_governed_manager_rotation_executes_when_transfer_appears_after_queue(
    contributor_contract,
    switchboard_delta,
    governance,
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
    aid = switchboard_delta.setManagerForContributor(
        contributor_contract.address,
        alice,
        sender=governance.address,
    )
    contributor_contract.initiateRipeTransfer(sender=owner_address)
    pending = contributor_contract.pendingRipeTransfer()
    _advance_to(switchboard_delta.getActionConfirmationBlock(aid))

    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert contributor_contract.manager() == alice
    assert contributor_contract.pendingRipeTransfer() == pending


def test_manager_rotation_is_available_for_frozen_pending_transfer_recovery(
    contributor_contract,
    switchboard_delta,
    governance,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    manager_address,
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
    pending = contributor_contract.pendingRipeTransfer()
    _freeze(switchboard_delta, governance, contributor_contract)
    aid = switchboard_delta.setManagerForContributor(
        contributor_contract.address,
        alice,
        sender=governance.address,
    )
    _advance_to(switchboard_delta.getActionConfirmationBlock(aid))

    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert contributor_contract.pendingRipeTransfer() == pending
    with boa.reverts("no perms"):
        contributor_contract.cancelRipeTransfer(sender=manager_address)
    contributor_contract.cancelRipeTransfer(sender=alice)
    assert not contributor_contract.hasPendingRipeTransfer()
    assert contributor_contract.isFrozen()


def test_pending_ownership_still_blocks_governed_manager_execution_and_is_retryable(
    contributor_contract,
    switchboard_delta,
    governance,
    owner_address,
    manager_address,
    alice,
    bob,
):
    aid = switchboard_delta.setManagerForContributor(
        contributor_contract.address,
        bob,
        sender=governance.address,
    )
    contributor_contract.changeOwnership(alice, sender=owner_address)
    _advance_to(switchboard_delta.getActionConfirmationBlock(aid))

    with boa.reverts("cannot do with pending ownership change"):
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert switchboard_delta.hasPendingAction(aid)
    pending_manager = switchboard_delta.pendingManager(aid)
    assert pending_manager[0] == contributor_contract.address
    assert pending_manager[1] == bob
    assert contributor_contract.manager() == manager_address

    assert switchboard_delta.cancelOwnershipChangeForContributor(
        contributor_contract.address,
        sender=governance.address,
    )
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert contributor_contract.manager() == bob
    assert not switchboard_delta.hasPendingAction(aid)


def test_owner_can_reinitiate_handoff_until_manager_action_expires(
    contributor_contract,
    switchboard_delta,
    governance,
    owner_address,
    manager_address,
    alice,
    bob,
):
    aid = switchboard_delta.setManagerForContributor(
        contributor_contract.address,
        bob,
        sender=governance.address,
    )
    contributor_contract.changeOwnership(alice, sender=owner_address)
    action = switchboard_delta.pendingActions(aid)
    _advance_to(action[1])

    with boa.reverts("cannot do with pending ownership change"):
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert switchboard_delta.cancelOwnershipChangeForContributor(
        contributor_contract.address,
        sender=governance.address,
    )

    contributor_contract.changeOwnership(alice, sender=owner_address)
    with boa.reverts("cannot do with pending ownership change"):
        switchboard_delta.executePendingAction(aid, sender=governance.address)

    _advance_to(action[2])
    assert not switchboard_delta.executePendingAction(
        aid,
        sender=governance.address,
    )
    assert not switchboard_delta.hasPendingAction(aid)
    assert contributor_contract.manager() == manager_address
    assert contributor_contract.hasPendingOwnerChange()


def test_manager_error_precedence_with_pending_ownership_is_unchanged(
    contributor_contract,
    owner_address,
    alice,
):
    contributor_contract.changeOwnership(alice, sender=owner_address)

    with boa.reverts("cannot do with pending ownership change"):
        contributor_contract.setManager(ZERO_ADDRESS, sender=owner_address)
