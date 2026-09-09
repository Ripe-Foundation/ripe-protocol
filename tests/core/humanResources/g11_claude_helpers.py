"""Group 11 (Claude) proof helpers — Contributor / HR cash, transfer, cancel, admin.

Deliberately independent of the other Group 11 proof files: every helper here
drives the *real* HR governor path (initiateNewContributor -> HR timelock ->
confirmNewContributor) so the clone under test is a genuine registered
contributor, not a fixture-installed address.
"""

import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS
from contracts.modules import Contributor


# Fixture-band terms (tests/core/humanResources/conftest.py + config/BluePrint.py "local").
# NOT the RH launch band -- see the report for the launch-vs-fixture split.
BASE_TERMS = {
    "owner": "0x" + "11" * 20,
    "manager": "0x" + "22" * 20,
    "compensation": 500_000 * EIGHTEEN_DECIMALS,
    "startDelay": 7 * 24 * 3600,
    "vestingLength": 2 * 365 * 24 * 3600,
    "cliffLength": 90 * 24 * 3600,
    "unlockLength": 365 * 24 * 3600,
    "depositLockDuration": 100,
}

TERM_ORDER = (
    "owner",
    "manager",
    "compensation",
    "startDelay",
    "vestingLength",
    "cliffLength",
    "unlockLength",
    "depositLockDuration",
)


def terms(**overrides):
    t = dict(BASE_TERMS)
    t.update(overrides)
    return t


def term_args(t):
    return [t[k] for k in TERM_ORDER]


def set_hr_config(
    mission_control,
    switchboard_delta,
    contributor_template,
    contribTemplate=None,
    maxCompensation=1_000_000 * EIGHTEEN_DECIMALS,
    minCliffLength=30 * 24 * 3600,
    maxStartDelay=90 * 24 * 3600,
    minVestingLength=365 * 24 * 3600,
    maxVestingLength=4 * 365 * 24 * 3600,
):
    """MissionControl.setHrConfig via switchboard-address impersonation (suite setup shortcut)."""
    cfg = (
        contribTemplate if contribTemplate is not None else contributor_template.address,
        maxCompensation,
        minCliffLength,
        maxStartDelay,
        minVestingLength,
        maxVestingLength,
    )
    mission_control.setHrConfig(cfg, sender=switchboard_delta.address)
    return cfg


def set_budget(ledger, switchboard_delta, amount):
    """Ledger.setRipeAvailForHr via switchboard-address impersonation (suite setup shortcut)."""
    ledger.setRipeAvailForHr(amount, sender=switchboard_delta.address)
    return amount


def deploy_contributor(human_resources, governance, t):
    """Real HR governor path: initiate -> HR timelock -> confirm. Returns the clone."""
    aid = human_resources.initiateNewContributor(*term_args(t), sender=governance.address)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid, sender=governance.address)
    evs = filter_logs(human_resources, "NewContributorConfirmed")
    assert len(evs) == 1
    return Contributor.at(evs[0].contributorAddr)


def make_contributor(
    human_resources,
    mission_control,
    switchboard_delta,
    contributor_template,
    ledger,
    governance,
    t=None,
    budget=None,
    **hr_config_overrides,
):
    t = t if t is not None else terms()
    set_hr_config(mission_control, switchboard_delta, contributor_template, **hr_config_overrides)
    set_budget(ledger, switchboard_delta, budget if budget is not None else t["compensation"])
    return deploy_contributor(human_resources, governance, t)


def travel_to(ts):
    """Advance to an absolute timestamp (boa moves block.number in lockstep)."""
    delta = ts - boa.env.evm.patch.timestamp
    assert delta >= 0, f"cannot travel backwards ({delta})"
    if delta:
        boa.env.time_travel(seconds=delta)


def unlock_block(ripe_gov_vault, user, ripe_token):
    return ripe_gov_vault.userGovData(user, ripe_token).unlock


def position(ripe_gov_vault, user, ripe_token):
    return ripe_gov_vault.getTotalAmountForUser(user, ripe_token)


def shares(ripe_gov_vault, user, ripe_token):
    return ripe_gov_vault.userBalances(user, ripe_token)


def snapshot(ripe_gov_vault, ripe_token, ledger, human_resources, contributor):
    owner = contributor.owner()
    return {
        "supply": ripe_token.totalSupply(),
        "hr_bal": ripe_token.balanceOf(human_resources),
        "clone_pos": position(ripe_gov_vault, contributor, ripe_token),
        "owner_pos": position(ripe_gov_vault, owner, ripe_token),
        "owner_erc20": ripe_token.balanceOf(owner),
        "clone_erc20": ripe_token.balanceOf(contributor),
        "avail": ledger.ripeAvailForHr(),
        "claimed": contributor.totalClaimed(),
        "comp": contributor.compensation(),
        "end": contributor.endTime(),
        "unlock_ts": contributor.unlockTime(),
    }
