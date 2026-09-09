"""Focused Group 11 proofs for terms validation, HR config, and HR creation."""

import boa
import pytest

from constants import ZERO_ADDRESS
from conf_utils import filter_logs


UINT256_MAX = 2**256 - 1
WEEK = 7 * 24 * 60 * 60
MONTH = 30 * 24 * 60 * 60
YEAR = 365 * 24 * 60 * 60


def _advance_to_block(block_number):
    current = boa.env.evm.patch.block_number
    if current < block_number:
        boa.env.time_travel(blocks=block_number - current)
    assert boa.env.evm.patch.block_number >= block_number


def _execute_delta(switchboard_delta, governance, action_id):
    _advance_to_block(switchboard_delta.getActionConfirmationBlock(action_id))
    assert switchboard_delta.executePendingAction(action_id, sender=governance.address)


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


def _valid(human_resources, terms):
    return human_resources.areValidContributorTerms(
        terms["owner"],
        terms["manager"],
        terms["compensation"],
        terms["startDelay"],
        terms["vestingLength"],
        terms["cliffLength"],
        terms["unlockLength"],
        terms["depositLockDuration"],
    )


def test_g11_parallel_delta_fields_merge_into_global_hr_program_dos_then_recover(
    human_resources,
    switchboard_delta,
    governance,
    mission_control,
    ledger,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
):
    """Valid independent Delta actions can make all new HR terms impossible."""
    setupHrConfig(
        _minCliffLength=MONTH,
        _minVestingLength=YEAR,
        _maxVestingLength=4 * YEAR,
    )
    setupLedgerBalance(valid_contributor_terms["compensation"] * 2)
    terms = dict(valid_contributor_terms)
    pending = _initiate(human_resources, governance, terms)
    original = mission_control.hrConfig()

    # Both actions are valid alone.  Delta merges each pending field into the
    # live config at execution rather than replacing the whole struct.
    cliff_action = switchboard_delta.setMinCliffLength(
        31 * 24 * 60 * 60, sender=governance.address
    )
    vesting_action = switchboard_delta.setVestingLengthBoundaries(
        MONTH + 1, 31 * 24 * 60 * 60 - 1, sender=governance.address
    )
    _advance_to_block(
        max(
            switchboard_delta.getActionConfirmationBlock(cliff_action),
            switchboard_delta.getActionConfirmationBlock(vesting_action),
        )
    )
    assert switchboard_delta.executePendingAction(cliff_action, sender=governance.address)
    after_cliff = mission_control.hrConfig()
    assert after_cliff[0] == original[0]
    assert after_cliff[1] == original[1]
    assert after_cliff[3] == original[3]
    assert after_cliff[4:] == original[4:]
    with boa.reverts("infeasible hr config"):
        switchboard_delta.executePendingAction(vesting_action, sender=governance.address)
    assert switchboard_delta.actionType(vesting_action) != 0
    assert after_cliff[5] == mission_control.hrConfig()[5]
    assert not filter_logs(switchboard_delta, "HrVestingLengthBoundariesSet")

    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(pending, sender=governance.address) is True


def test_g11_single_delta_vesting_lower_can_also_make_hr_config_infeasible(
    human_resources,
    switchboard_delta,
    governance,
    mission_control,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
):
    """Lowering max vest below a live min cliff independently closes HR."""
    setupHrConfig(
        _minCliffLength=31 * 24 * 60 * 60,
        _minVestingLength=YEAR,
        _maxVestingLength=4 * YEAR,
    )
    setupLedgerBalance(valid_contributor_terms["compensation"])
    live = mission_control.hrConfig()
    action = switchboard_delta.setVestingLengthBoundaries(
        MONTH + 1, 31 * 24 * 60 * 60 - 1, sender=governance.address
    )
    _advance_to_block(switchboard_delta.getActionConfirmationBlock(action))
    with boa.reverts("infeasible hr config"):
        switchboard_delta.executePendingAction(action, sender=governance.address)
    config = mission_control.hrConfig()
    assert config[2] == live[2]
    assert config[5] == live[5]
    assert switchboard_delta.actionType(action) != 0


def test_g11_delta_hr_setter_boundaries_are_not_launch_config_boundaries(
    switchboard_delta,
    governance,
):
    """Exercise the documented setter-only acceptance asymmetries."""
    with boa.reverts("invalid max compensation"):
        switchboard_delta.setMaxCompensation(0, sender=governance.address)
    with boa.reverts("invalid min cliff length"):
        switchboard_delta.setMinCliffLength(WEEK, sender=governance.address)
    with boa.reverts("invalid min vesting length"):
        switchboard_delta.setVestingLengthBoundaries(WEEK, YEAR, sender=governance.address)
    with boa.reverts("invalid max vesting length"):
        switchboard_delta.setVestingLengthBoundaries(MONTH + 1, 10 * YEAR, sender=governance.address)

    # Week + 1 is accepted as an action even though launch uses exactly one
    # week, and zero is accepted for max-start-delay.
    cliff_action = switchboard_delta.setMinCliffLength(WEEK + 1, sender=governance.address)
    zero_start_action = switchboard_delta.setMaxStartDelay(0, sender=governance.address)
    assert switchboard_delta.hasPendingAction(cliff_action)
    assert switchboard_delta.hasPendingAction(zero_start_action)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda t: t.update(compensation=0),
        lambda t: t.update(cliffLength=0),
        lambda t: t.update(vestingLength=0),
        lambda t: t.update(unlockLength=t["vestingLength"] + 1),
        lambda t: t.update(cliffLength=t["unlockLength"] + 1),
        lambda t: t.update(owner=ZERO_ADDRESS),
        lambda t: t.update(manager=ZERO_ADDRESS),
        lambda t: t.update(compensation=t["compensation"] + 1),
        lambda t: t.update(startDelay=90 * 24 * 60 * 60 + 1),
        lambda t: t.update(cliffLength=1, unlockLength=1),
        lambda t: t.update(
            vestingLength=365 * 24 * 60 * 60 - 1,
            unlockLength=365 * 24 * 60 * 60 - 1,
        ),
        lambda t: t.update(vestingLength=4 * 365 * 24 * 60 * 60 + 1),
    ],
    ids=[
        "zero-compensation",
        "zero-cliff",
        "zero-vesting",
        "unlock-over-vesting",
        "cliff-over-unlock",
        "empty-owner",
        "empty-manager",
        "over-budget",
        "start-over-max",
        "cliff-below-min",
        "vesting-below-min",
        "vesting-over-max",
    ],
)
def test_g11_terms_validator_and_initiate_reject_documented_zero_and_order_cases(
    mutation,
    human_resources,
    governance,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
):
    """The public validator and state-changing initiation agree on rejection."""
    terms = dict(valid_contributor_terms)
    setupHrConfig()
    setupLedgerBalance(terms["compensation"])
    mutation(terms)
    assert not _valid(human_resources, terms)
    with boa.reverts("invalid terms"):
        _initiate(human_resources, governance, terms)


def test_g11_zero_max_start_delay_admits_constructor_overflow_and_then_stale_cancel(
    human_resources,
    switchboard_delta,
    governance,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
):
    """startDelay = uint256.max is rejected at initiate even when maxStartDelay is 0."""
    setupHrConfig(_maxStartDelay=1)
    setupLedgerBalance(valid_contributor_terms["compensation"])
    zero_cap = switchboard_delta.setMaxStartDelay(0, sender=governance.address)
    _execute_delta(switchboard_delta, governance, zero_cap)

    terms = dict(valid_contributor_terms)
    terms["startDelay"] = UINT256_MAX
    assert not _valid(human_resources, terms)
    with boa.reverts("invalid terms"):
        _initiate(human_resources, governance, terms)
