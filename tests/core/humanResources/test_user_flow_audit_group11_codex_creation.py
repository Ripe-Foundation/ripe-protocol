"""Group 11 HR create races and confirm-time template selection proofs."""

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


def test_g11_two_overlapping_hr_pendings_fail_closed_at_second_confirm(
    human_resources,
    ledger,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
    governance,
):
    """Each pending fits at initiation; only the first may reserve the budget."""
    terms = dict(valid_contributor_terms)
    setupHrConfig()
    setupLedgerBalance(terms["compensation"])
    first = _initiate(human_resources, governance, terms)
    second = _initiate(human_resources, governance, terms)
    _advance_to_block(
        max(
            human_resources.getActionConfirmationBlock(first),
            human_resources.getActionConfirmationBlock(second),
        )
    )

    assert human_resources.confirmNewContributor(first, sender=governance.address)
    confirmed = filter_logs(human_resources, "NewContributorConfirmed")
    assert len(confirmed) == 1
    assert ledger.ripeAvailForHr() == 0
    contributors_after_first = ledger.numContributors()
    assert human_resources.confirmNewContributor(second, sender=governance.address) is False
    assert human_resources.pendingContributor(second).owner == ZERO_ADDRESS
    assert ledger.numContributors() == contributors_after_first
    assert ledger.ripeAvailForHr() == 0
    assert not filter_logs(human_resources, "NewContributorConfirmed")
    assert not filter_logs(human_resources, "NewContributorCancelled")


def test_g11_delta_budget_overwrite_revalidates_pending_hr_creation_without_terminal_event(
    human_resources,
    switchboard_delta,
    governance,
    ledger,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
):
    """A live Delta budget reduction self-cancels a still-pending HR action."""
    terms = dict(valid_contributor_terms)
    setupHrConfig()
    setupLedgerBalance(terms["compensation"])
    pending = _initiate(human_resources, governance, terms)
    budget_action = switchboard_delta.setRipeAvailableForHr(0, sender=governance.address)
    _advance_to_block(switchboard_delta.getActionConfirmationBlock(budget_action))
    assert switchboard_delta.executePendingAction(budget_action, sender=governance.address)
    assert ledger.ripeAvailForHr() == 0

    contributors_before = ledger.numContributors()
    assert human_resources.confirmNewContributor(pending, sender=governance.address) is False
    assert human_resources.pendingContributor(pending).owner == ZERO_ADDRESS
    assert ledger.numContributors() == contributors_before
    assert not filter_logs(human_resources, "NewContributorConfirmed")
    assert not filter_logs(human_resources, "NewContributorCancelled")


def test_g11_confirm_uses_delta_rotated_live_template_not_initiate_time_template(
    human_resources,
    switchboard_delta,
    governance,
    mission_control,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
):
    """The required A -> Delta B -> confirm sequence deploys B's runtime."""
    setupHrConfig()
    setupLedgerBalance(valid_contributor_terms["compensation"])
    pending = _initiate(human_resources, governance, dict(valid_contributor_terms))

    template_b = boa.load_partial(
        "tests/core/humanResources/Group11RotatedTemplate.vy"
    ).deploy_as_blueprint()
    rotate = switchboard_delta.setContributorTemplate(
        template_b.address, sender=governance.address
    )
    # Change a separate live field too; Delta execution must merge rather than
    # stomp the template before HR revalidates the original terms.
    start_cap = switchboard_delta.setMaxStartDelay(0, sender=governance.address)
    _advance_to_block(
        max(
            switchboard_delta.getActionConfirmationBlock(rotate),
            switchboard_delta.getActionConfirmationBlock(start_cap),
        )
    )
    assert switchboard_delta.executePendingAction(rotate, sender=governance.address)
    assert switchboard_delta.executePendingAction(start_cap, sender=governance.address)
    assert mission_control.hrConfig()[0] == template_b.address
    assert mission_control.hrConfig()[3] == 0

    assert human_resources.confirmNewContributor(pending, sender=governance.address)
    deployed = filter_logs(human_resources, "NewContributorConfirmed")
    assert len(deployed) == 1
    rotated = boa.load_partial(
        "tests/core/humanResources/Group11RotatedTemplate.vy"
    ).at(deployed[0].contributorAddr)
    assert rotated.templateMarker() == 11


def test_g11_owner_equal_manager_is_valid_contributor_terms(
    human_resources,
    governance,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
):
    """The validator rejects empty principals, not an owner/manager match."""
    terms = dict(valid_contributor_terms)
    terms["manager"] = terms["owner"]
    setupHrConfig()
    setupLedgerBalance(terms["compensation"])
    action = _initiate(human_resources, governance, terms)
    _advance_to_block(human_resources.getActionConfirmationBlock(action))
    assert human_resources.confirmNewContributor(action, sender=governance.address)
