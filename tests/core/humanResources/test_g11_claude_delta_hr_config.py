"""Group 11 (Claude) never-skip #5 (part 2) -- the Delta HR config setters through
their REAL initiate + timelock + executePendingAction path, cross-field feasibility,
and the rotated-template sequence."""

import boa

from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs

from g11_claude_helpers import (
    set_budget,
    set_hr_config,
    term_args,
    terms,
)

DAY = 60 * 60 * 24
WEEK = 7 * DAY
MONTH = 30 * DAY
YEAR = 365 * DAY


def _exec(switchboard_delta, governance, aid):
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.canConfirmAction(aid)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)


def _cfg(mission_control):
    return mission_control.hrConfig()


# ------------------------------------------------------------- setter bounds


def test_g11c_delta_hr_setters_reject_the_launch_values_they_can_never_restore(
    mission_control, switchboard_delta, contributor_template, governance,
):
    set_hr_config(mission_control, switchboard_delta, contributor_template)

    # maxCompensation: launch ships 0 (= unlimited); the setter refuses 0 forever
    with boa.reverts("invalid max compensation"):
        switchboard_delta.setMaxCompensation(0, sender=governance.address)
    with boa.reverts("invalid max compensation"):
        switchboard_delta.setMaxCompensation(20_000_001 * EIGHTEEN_DECIMALS,
                                             sender=governance.address)
    switchboard_delta.setMaxCompensation(20_000_000 * EIGHTEEN_DECIMALS,
                                         sender=governance.address)

    # minCliffLength: launch ships exactly one week; the setter requires strictly >
    with boa.reverts("invalid min cliff length"):
        switchboard_delta.setMinCliffLength(WEEK, sender=governance.address)
    switchboard_delta.setMinCliffLength(WEEK + 1, sender=governance.address)

    # vesting boundaries: launch ships (1 week, 10 years); BOTH are unreachable
    with boa.reverts("invalid min vesting length"):
        switchboard_delta.setVestingLengthBoundaries(WEEK, 10 * YEAR, sender=governance.address)
    with boa.reverts("invalid max vesting length"):
        switchboard_delta.setVestingLengthBoundaries(MONTH + 1, 10 * YEAR,
                                                     sender=governance.address)
    with boa.reverts("invalid min vesting length"):
        switchboard_delta.setVestingLengthBoundaries(MONTH, 5 * YEAR, sender=governance.address)
    switchboard_delta.setVestingLengthBoundaries(MONTH + 1, 5 * YEAR, sender=governance.address)

    # maxStartDelay: 0 IS accepted and removes the validator cap
    switchboard_delta.setMaxStartDelay(0, sender=governance.address)
    with boa.reverts("invalid max start delay"):
        switchboard_delta.setMaxStartDelay(3 * MONTH + 1, sender=governance.address)


def test_g11c_two_parallel_delta_hr_config_pendings_merge_without_stomping(
    mission_control, switchboard_delta, contributor_template, governance,
):
    set_hr_config(mission_control, switchboard_delta, contributor_template)
    before = _cfg(mission_control)

    aid_comp = switchboard_delta.setMaxCompensation(7_000_000 * EIGHTEEN_DECIMALS,
                                                    sender=governance.address)
    aid_cliff = switchboard_delta.setMinCliffLength(40 * DAY, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(aid_comp, sender=governance.address)
    mid = _cfg(mission_control)
    assert mid.maxCompensation == 7_000_000 * EIGHTEEN_DECIMALS
    assert mid.minCliffLength == before.minCliffLength      # untouched by the first execute
    assert switchboard_delta.executePendingAction(aid_cliff, sender=governance.address)

    after = _cfg(mission_control)
    assert after.maxCompensation == 7_000_000 * EIGHTEEN_DECIMALS   # NOT stomped back
    assert after.minCliffLength == 40 * DAY
    assert after.contribTemplate == before.contribTemplate
    assert after.maxStartDelay == before.maxStartDelay
    assert after.minVestingLength == before.minVestingLength
    assert after.maxVestingLength == before.maxVestingLength


# ---------------------------------------------------- cross-field feasibility


def test_g11c_infeasible_min_cliff_execute_reverts_and_keeps_pending(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob, sally,
):
    """minCliffLength has no maximum. Terms need
    minCliff <= cliff <= unlock <= vesting <= maxVesting, so `minCliff > maxVesting`
    closes the whole HR program. Both directions and the two-parallel-pending merge."""
    set_hr_config(mission_control, switchboard_delta, contributor_template)
    comp = 500_000 * EIGHTEEN_DECIMALS
    set_budget(ledger, switchboard_delta, comp * 4)

    # positive control: a clone can be created right now
    good = terms(owner=alice, manager=bob, compensation=comp)
    assert human_resources.areValidContributorTerms(*term_args(good))
    pending_aid = human_resources.initiateNewContributor(*term_args(good),
                                                         sender=governance.address)

    live = _cfg(mission_control)
    aid = switchboard_delta.setMinCliffLength(5 * YEAR, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    with boa.reverts("infeasible hr config"):
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    cfg = _cfg(mission_control)
    assert cfg.minCliffLength == live.minCliffLength
    assert cfg.maxVestingLength == live.maxVestingLength
    assert switchboard_delta.actionType(aid) != 0

    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(pending_aid, sender=governance.address)

    aid_eq = switchboard_delta.setMinCliffLength(live.maxVestingLength, sender=governance.address)
    _exec(switchboard_delta, governance, aid_eq)
    assert _cfg(mission_control).minCliffLength == live.maxVestingLength

    set_hr_config(mission_control, switchboard_delta, contributor_template)
    aid_cliff = switchboard_delta.setMinCliffLength(YEAR, sender=governance.address)
    aid_vest = switchboard_delta.setVestingLengthBoundaries(MONTH + 1, 2 * MONTH,
                                                            sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(aid_vest, sender=governance.address)
    with boa.reverts("infeasible hr config"):
        switchboard_delta.executePendingAction(aid_cliff, sender=governance.address)
    assert switchboard_delta.actionType(aid_cliff) != 0

    aid_cliff = switchboard_delta.setMinCliffLength(30 * DAY, sender=governance.address)
    aid_vest = switchboard_delta.setVestingLengthBoundaries(YEAR, 4 * YEAR,
                                                            sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(aid_cliff, sender=governance.address)
    assert switchboard_delta.executePendingAction(aid_vest, sender=governance.address)
    assert human_resources.areValidContributorTerms(*term_args(good))
    aid2 = human_resources.initiateNewContributor(*term_args(good), sender=governance.address)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid2, sender=governance.address)


# ------------------------------------------------------------ rotated template


def test_g11c_confirm_uses_the_template_live_at_confirm_not_at_initiate(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob, tmp_path,
):
    """(1) initiate under template A, (2) real Delta setContributorTemplate to B,
    (3) confirm the ORIGINAL action, (4) prove B's bytecode was deployed."""
    marker_path = tmp_path / "ContributorTemplateB.vy"
    body = open("contracts/modules/Contributor.vy").read()
    body += (
        "\n\n@view\n@external\ndef g11ClaudeTemplateMarker() -> uint256:\n"
        "    return 20260818\n"
    )
    marker_path.write_text(body)
    template_b = boa.load_partial(str(marker_path)).deploy_as_blueprint()
    assert template_b.address != contributor_template.address

    set_hr_config(mission_control, switchboard_delta, contributor_template)
    comp = 500_000 * EIGHTEEN_DECIMALS
    set_budget(ledger, switchboard_delta, comp)
    t = terms(owner=alice, manager=bob, compensation=comp)
    assert _cfg(mission_control).contribTemplate == contributor_template.address

    aid_hr = human_resources.initiateNewContributor(*term_args(t), sender=governance.address)
    aid_tpl = switchboard_delta.setContributorTemplate(template_b.address,
                                                       sender=governance.address)
    boa.env.time_travel(blocks=max(switchboard_delta.actionTimeLock(),
                                   human_resources.actionTimeLock()))
    assert switchboard_delta.executePendingAction(aid_tpl, sender=governance.address)
    assert _cfg(mission_control).contribTemplate == template_b.address

    assert human_resources.confirmNewContributor(aid_hr, sender=governance.address)
    ev = filter_logs(human_resources, "NewContributorConfirmed")
    assert len(ev) == 1
    deployed = ev[0].contributorAddr

    # (4) which bytecode: the marker only exists in template B
    marker = boa.load_partial(str(marker_path)).at(deployed)
    assert marker.g11ClaudeTemplateMarker() == 20260818
    assert marker.owner() == alice
    # and the terms were revalidated against the LIVE config, not the initiate-time one
    assert marker.compensation() == comp
    assert ledger.isHrContributor(deployed)


def test_g11c_zero_max_vesting_uses_2_128_effective_ceiling(
    mission_control,
    switchboard_delta,
    contributor_template,
    governance,
):
    """Live maxVestingLength == 0 is treated as 2**128, not unbounded."""
    set_hr_config(
        mission_control,
        switchboard_delta,
        contributor_template,
        minCliffLength=WEEK + 1,
        minVestingLength=0,
        maxVestingLength=0,
    )
    live = _cfg(mission_control)
    assert live.maxVestingLength == 0

    over = switchboard_delta.setMinCliffLength(2**128 + 1, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    with boa.reverts("infeasible hr config"):
        switchboard_delta.executePendingAction(over, sender=governance.address)
    cfg = _cfg(mission_control)
    assert cfg.minCliffLength == live.minCliffLength
    assert cfg.maxVestingLength == 0
    assert switchboard_delta.actionType(over) != 0

    equal = switchboard_delta.setMinCliffLength(2**128, sender=governance.address)
    _exec(switchboard_delta, governance, equal)
    assert _cfg(mission_control).minCliffLength == 2**128
    assert _cfg(mission_control).maxVestingLength == 0


def test_g11c_oversize_nonzero_max_vesting_still_caps_at_2_128(
    mission_control,
    switchboard_delta,
    switchboard_alpha,
    contributor_template,
    governance,
):
    """A nonzero maxVestingLength above 2**128 is still capped at 2**128."""
    set_hr_config(
        mission_control,
        switchboard_delta,
        contributor_template,
        minCliffLength=WEEK + 1,
        minVestingLength=0,
        maxVestingLength=4 * YEAR,
    )
    live = _cfg(mission_control)
    seeded = (
        live.contribTemplate,
        live.maxCompensation,
        live.minCliffLength,
        live.maxStartDelay,
        live.minVestingLength,
        2**129,
    )
    mission_control.setHrConfig(seeded, sender=switchboard_alpha.address)
    assert _cfg(mission_control).maxVestingLength == 2**129

    over = switchboard_delta.setMinCliffLength(2**128 + 1, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    with boa.reverts("infeasible hr config"):
        switchboard_delta.executePendingAction(over, sender=governance.address)
    cfg = _cfg(mission_control)
    assert cfg.minCliffLength == live.minCliffLength
    assert cfg.maxVestingLength == 2**129
    assert switchboard_delta.actionType(over) != 0

    equal = switchboard_delta.setMinCliffLength(2**128, sender=governance.address)
    _exec(switchboard_delta, governance, equal)
    assert _cfg(mission_control).minCliffLength == 2**128
    assert _cfg(mission_control).maxVestingLength == 2**129
