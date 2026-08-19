"""Group 11 (kimi) proof tests — rotated template + Delta timelock boundaries.

Rotated template (required four-step): initiate under template A; change
MissionControl to template B through the real Delta setContributorTemplate +
timelock + executePendingAction; confirm the original HR action; prove which
bytecode was deployed and that terms were revalidated against the LIVE config.

NOTE: two blueprints of the SAME Contributor.vy source have identical runtime
bytecode, so bytecode cannot distinguish template A from a fresh Contributor
template B. The functional proof uses an INCOMPATIBLE contract (Ledger) as
template B: confirm must revert inside create_from_blueprint, proving confirm
reads the live contribTemplate rather than the initiate-time one.

Delta timelock boundaries: executePendingAction before confirmBlock returns
False without cancelling; at exact expiration it clears the pending and returns
False.
"""
import boa

from conf_utils import filter_logs
from contracts.modules import Contributor


def _bn():
    return boa.env.evm.patch.block_number


def _delta_execute(switchboard_delta, governance, aid):
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    return switchboard_delta.executePendingAction(aid, sender=governance.address)


def test_g11_rotated_template_confirm_uses_live_config(
    human_resources, setupHrConfig, setupLedgerBalance, governance,
    switchboard_delta, mission_control, contributor_template, ledger,
    valid_contributor_terms,
):
    """Initiate under template A; Delta rotates to an incompatible template;
    confirm reverts (proving the live template is read); rotate back to a fresh
    Contributor blueprint; the same pending confirms."""
    t = valid_contributor_terms
    setupHrConfig()  # template A = contributor_template
    setupLedgerBalance(t["compensation"])

    # (1) initiate under template A
    aid = human_resources.initiateNewContributor(
        t["owner"], t["manager"], t["compensation"], t["startDelay"],
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"],
        sender=governance.address)

    # (2) rotate to an INCOMPATIBLE template (Ledger) through the real Delta path
    rot_aid = switchboard_delta.setContributorTemplate(ledger.address, sender=governance.address)
    assert _delta_execute(switchboard_delta, governance, rot_aid)
    assert mission_control.hrConfig().contribTemplate == ledger.address

    # (3) confirm the original HR action: reverts inside create_from_blueprint
    # (Ledger's constructor signature is incompatible) — proving confirm reads
    # the LIVE contribTemplate, not the initiate-time one
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    with boa.reverts():
        human_resources.confirmNewContributor(aid, sender=governance.address)
    # pending survives the revert (not the False-cancel path)
    assert human_resources.pendingContributor(aid).owner == t["owner"]

    # rotate back to a fresh valid Contributor blueprint; the same pending confirms
    template_b = boa.load_partial("contracts/modules/Contributor.vy").deploy_as_blueprint()
    assert template_b.address != contributor_template.address
    rot2_aid = switchboard_delta.setContributorTemplate(template_b.address, sender=governance.address)
    assert _delta_execute(switchboard_delta, governance, rot2_aid)
    assert mission_control.hrConfig().contribTemplate == template_b.address
    assert human_resources.confirmNewContributor(aid, sender=governance.address)
    events = filter_logs(human_resources, "NewContributorConfirmed")
    assert len(events) == 1
    c = Contributor.at(events[-1].contributorAddr)
    # and the clone is functional under the live config
    assert c.compensation() == t["compensation"]


def test_g11_delta_timelock_boundaries(
    human_resources, contributor_contract, switchboard_delta, governance,
):
    """Delta executePendingAction: before confirmBlock -> False, pending kept;
    at exact expiration -> False, pending CLEARED."""
    c = contributor_contract
    aid = switchboard_delta.cancelPaycheckForContributor(c.address, sender=governance.address)
    confirm_block = switchboard_delta.getActionConfirmationBlock(aid)
    expiration = switchboard_delta.pendingActions(aid).expiration

    # before confirmBlock: False, pending kept
    assert boa.env.evm.patch.block_number < confirm_block
    assert switchboard_delta.executePendingAction(aid, sender=governance.address) is False
    assert switchboard_delta.actionType(aid) != 0
    assert switchboard_delta.hasPendingAction(aid)

    # at exact expiration: False, pending cleared
    boa.env.time_travel(blocks=expiration - _bn())
    assert switchboard_delta.isExpired(aid)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address) is False
    assert not switchboard_delta.hasPendingAction(aid)
    assert switchboard_delta.actionType(aid) == 0
    # the contributor was NOT cancelled
    assert c.compensation() != 0
