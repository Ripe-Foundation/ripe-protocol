"""Group 11 proofs for HR aggregate-view checked-addition liveness."""

import boa

from conf_utils import filter_logs
from tests.core.humanResources.g11_proof_helpers import (
    release_live_hr_reserve,
    official_delta_cancel,
)


UINT256_MAX = 2**256 - 1


def _advance_to_block(block_number):
    current = boa.env.evm.patch.block_number
    if current < block_number:
        boa.env.time_travel(blocks=block_number - current)
    assert boa.env.evm.patch.block_number >= block_number


def _set_hr_budget(switchboard_delta, governance, ledger, amount):
    action = switchboard_delta.setRipeAvailableForHr(amount, sender=governance.address)
    _advance_to_block(switchboard_delta.getActionConfirmationBlock(action))
    assert switchboard_delta.executePendingAction(action, sender=governance.address)


def _confirm(human_resources, governance, terms):
    action = human_resources.initiateNewContributor(
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
    _advance_to_block(human_resources.getActionConfirmationBlock(action))
    assert human_resources.confirmNewContributor(action, sender=governance.address)
    events = filter_logs(human_resources, "NewContributorConfirmed")
    assert len(events) == 1
    return events[0].contributorAddr


def test_g11_normal_clones_can_overflow_get_total_compensation_after_budget_overwrite(
    human_resources,
    switchboard_delta,
    governance,
    ledger,
    setupHrConfig,
    valid_contributor_terms,
):
    """Two 2**255 stock clones are rejected at initiate."""
    compensation = UINT256_MAX // 2 + 1
    terms = dict(valid_contributor_terms)
    terms["compensation"] = compensation
    setupHrConfig(_maxCompensation=0)

    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(
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


def test_g11_custom_template_can_overflow_both_aggregate_views(
    human_resources,
    switchboard_delta,
    governance,
    ledger,
    setupHrConfig,
    valid_contributor_terms,
):
    """Custom getters saturate both aggregate views without UINT256_MAX budget writes."""
    custom_template = boa.load_partial(
        "tests/core/humanResources/Group11OverflowViewContributor.vy"
    ).deploy_as_blueprint()
    terms = dict(valid_contributor_terms)
    setupHrConfig(_contribTemplate=custom_template.address, _maxCompensation=0)

    release_live_hr_reserve(switchboard_delta, governance, ledger)
    _set_hr_budget(switchboard_delta, governance, ledger, terms["compensation"] * 2)
    addr1 = _confirm(human_resources, governance, terms)
    terms2 = dict(terms)
    terms2["owner"] = "0x" + "33" * 20
    addr2 = _confirm(human_resources, governance, terms2)

    assert human_resources.getTotalCompensation() == UINT256_MAX
    assert human_resources.getTotalClaimed() == UINT256_MAX
    assert ledger.hrReservedCompensation() == terms["compensation"] * 2
    for addr in (addr1, addr2):
        _, ok = official_delta_cancel(
            switchboard_delta, governance, type("Handle", (), {"address": addr})()
        )
        assert ok is True
