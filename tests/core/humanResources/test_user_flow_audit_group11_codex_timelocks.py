"""Focused Group 11 HR-versus-Delta TimeLock boundary proofs."""

import boa

from constants import ZERO_ADDRESS
from conf_utils import filter_logs


def _advance_to_block(block_number):
    current = boa.env.evm.patch.block_number
    if current < block_number:
        boa.env.time_travel(blocks=block_number - current)
    assert boa.env.evm.patch.block_number >= block_number


def _initiate(human_resources, governance, terms):
    return human_resources.initiateNewContributor(
        terms["owner"],
        terms["manager"],
        terms["compensation"],
        terms["startDelay"],
        terms["vestingLength"],
        terms["cliffLength"],
        terms["unlockLength"],
        terms["depositLockDuration"],
        sender=governance.address,
    )


def test_g11_hr_timelock_valid_early_exact_expiry_and_manual_cleanup(
    human_resources,
    governance,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
):
    """HR reverts on valid early/expired actions and does not auto-clear expiry."""
    terms = dict(valid_contributor_terms)
    setupHrConfig()
    setupLedgerBalance(terms["compensation"] * 3)

    early = _initiate(human_resources, governance, terms)
    early_data = human_resources.pendingActions(early)
    _advance_to_block(early_data[1] - 1)
    with boa.reverts("time lock not reached"):
        human_resources.confirmNewContributor(early, sender=governance.address)
    assert human_resources.pendingContributor(early).owner == terms["owner"]
    _advance_to_block(early_data[1])
    assert human_resources.confirmNewContributor(early, sender=governance.address)

    before_expiry = _initiate(human_resources, governance, terms)
    before_data = human_resources.pendingActions(before_expiry)
    _advance_to_block(before_data[2] - 1)
    assert human_resources.confirmNewContributor(
        before_expiry, sender=governance.address
    )

    expired = _initiate(human_resources, governance, terms)
    expired_data = human_resources.pendingActions(expired)
    _advance_to_block(expired_data[2])
    with boa.reverts("time lock not reached"):
        human_resources.confirmNewContributor(expired, sender=governance.address)
    assert human_resources.pendingContributor(expired).owner == terms["owner"]
    assert human_resources.cancelNewContributor(expired, sender=governance.address)
    assert human_resources.pendingContributor(expired).owner == ZERO_ADDRESS


def test_g11_stale_hr_action_cancels_before_timelock_even_early_or_expired(
    human_resources,
    switchboard_delta,
    governance,
    ledger,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
):
    """Invalid revalidation returns False before HR's early/expiry gate."""

    def run_case(target_index):
        with boa.env.anchor():
            terms = dict(valid_contributor_terms)
            setupHrConfig()
            setupLedgerBalance(terms["compensation"])
            assert human_resources.setActionTimeLock(
                human_resources.minActionTimeLock() * 2,
                sender=governance.address,
            )
            action = _initiate(human_resources, governance, terms)
            hr_data = human_resources.pendingActions(action)
            budget = switchboard_delta.setRipeAvailableForHr(
                0, sender=governance.address
            )
            _advance_to_block(switchboard_delta.getActionConfirmationBlock(budget))
            assert switchboard_delta.executePendingAction(budget, sender=governance.address)
            assert ledger.ripeAvailForHr() == 0
            target = hr_data[target_index]
            if target_index == 1:
                target -= 1
            _advance_to_block(target)
            assert human_resources.confirmNewContributor(
                action, sender=governance.address
            ) is False
            assert human_resources.pendingContributor(action).owner == ZERO_ADDRESS
            assert not human_resources.hasPendingAction(action)
            assert not filter_logs(human_resources, "NewContributorConfirmed")
            assert not filter_logs(human_resources, "NewContributorCancelled")

    run_case(1)  # confirmBlock - 1
    run_case(2)  # exact expiration


def test_g11_delta_timelock_early_returns_false_and_expiry_auto_clears(
    switchboard_delta,
    governance,
    ledger,
):
    """Delta differs from HR: no revert early, auto-cleanup at expiration."""
    early = switchboard_delta.setRipeAvailableForHr(123, sender=governance.address)
    early_data = switchboard_delta.pendingActions(early)
    _advance_to_block(early_data[1] - 1)
    assert switchboard_delta.executePendingAction(early, sender=governance.address) is False
    assert switchboard_delta.hasPendingAction(early)
    _advance_to_block(early_data[1])
    assert switchboard_delta.executePendingAction(early, sender=governance.address)
    assert ledger.ripeAvailForHr() == 123

    expired = switchboard_delta.setRipeAvailableForHr(456, sender=governance.address)
    expired_data = switchboard_delta.pendingActions(expired)
    _advance_to_block(expired_data[2])
    assert switchboard_delta.executePendingAction(expired, sender=governance.address) is False
    assert not switchboard_delta.hasPendingAction(expired)
    assert switchboard_delta.actionType(expired) == 0
    assert ledger.ripeAvailForHr() == 123
