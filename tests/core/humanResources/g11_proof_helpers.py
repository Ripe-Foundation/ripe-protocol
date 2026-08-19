"""Local helpers for Group 11 proofs. Do not import from other groups' suites."""

import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS
from contracts.modules import Contributor


WEEK_IN_SECONDS = 7 * 24 * 3600
MONTH_IN_SECONDS = 30 * 24 * 3600
YEAR_IN_SECONDS = 365 * 24 * 3600
PRECISION = 10**18
HR_ID = 15


def travel_to_ts(ts):
    now = boa.env.evm.patch.timestamp
    if ts != now:
        boa.env.time_travel(seconds=ts - now)
    assert boa.env.evm.patch.timestamp == ts


def travel_to_block(block_number):
    current = boa.env.evm.patch.block_number
    if current < block_number:
        boa.env.time_travel(blocks=block_number - current)
    assert boa.env.evm.patch.block_number == block_number


def expected_vested(compensation, start, end, now):
    if now <= start or compensation == 0:
        return 0
    return min(compensation, compensation * (now - start) // (end - start))


def snapshot_econ(contributor, ripe_token, ripe_gov_vault, ledger, human_resources, owner, teller):
    return {
        "supply": ripe_token.totalSupply(),
        "hr_ripe": ripe_token.balanceOf(human_resources),
        "owner_ripe": ripe_token.balanceOf(owner),
        "clone_ripe": ripe_token.balanceOf(contributor.address),
        "clone_vault": ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token),
        "owner_vault": ripe_gov_vault.getTotalAmountForUser(owner, ripe_token),
        "clone_shares": ripe_gov_vault.userBalances(contributor, ripe_token),
        "owner_shares": ripe_gov_vault.userBalances(owner, ripe_token),
        "budget": ledger.ripeAvailForHr(),
        "claimed": contributor.totalClaimed(),
        "comp": contributor.compensation(),
        "end": contributor.endTime(),
        "unlock": contributor.unlockTime(),
        "allowance": ripe_token.allowance(human_resources, teller),
    }


def clone_at(addr):
    return Contributor.at(addr)


def terms_tuple(terms):
    return (
        terms["owner"],
        terms["manager"],
        terms["compensation"],
        terms["startDelay"],
        terms["vestingLength"],
        terms["cliffLength"],
        terms["unlockLength"],
        terms["depositLockDuration"],
    )


def initiate_contributor(human_resources, governance, terms):
    return human_resources.initiateNewContributor(
        *terms_tuple(terms),
        sender=governance.address,
    )


def confirm_contributor(human_resources, governance, aid):
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    ok = human_resources.confirmNewContributor(aid, sender=governance.address)
    return ok


def deploy_clone(human_resources, governance, setupHrConfig, setupLedgerBalance, terms, max_comp=1_000_000 * EIGHTEEN_DECIMALS):
    setupHrConfig(_maxCompensation=max_comp)
    setupLedgerBalance(terms["compensation"])
    aid = initiate_contributor(human_resources, governance, terms)
    assert confirm_contributor(human_resources, governance, aid) is True
    events = filter_logs(human_resources, "NewContributorConfirmed")
    return clone_at(events[0].contributorAddr), aid


def charlie_pause(switchboard_charlie, governance, addr, should_pause):
    assert switchboard_charlie.pause(addr, should_pause, sender=governance.address)


def grant_lite(mission_control, switchboard_delta, user):
    mission_control.setCanPerformLiteAction(user, True, sender=switchboard_delta.address)


def delta_confirm_and_execute(switchboard_delta, governance, aid):
    travel_to_block(switchboard_delta.getActionConfirmationBlock(aid))
    return switchboard_delta.executePendingAction(aid, sender=governance.address)


def official_delta_budget(switchboard_delta, governance, amount):
    aid = switchboard_delta.setRipeAvailableForHr(amount, sender=governance.address)
    assert delta_confirm_and_execute(switchboard_delta, governance, aid) is True
    return aid


def official_delta_cancel(switchboard_delta, governance, contributor):
    aid = switchboard_delta.cancelPaycheckForContributor(
        contributor.address, sender=governance.address
    )
    ok = delta_confirm_and_execute(switchboard_delta, governance, aid)
    return aid, ok


def official_freeze(switchboard_delta, governance, contributor, should_freeze=True):
    assert switchboard_delta.freezeContributor(
        contributor.address, should_freeze, sender=governance.address
    )


def seed_ripe_gov_position(ripe_gov_vault, ripe_token, whale, teller, user, amount):
    """Fixture route: Teller-impersonated vault deposit, not cashRipeCheck."""
    ripe_token.transfer(ripe_gov_vault, amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        user, ripe_token, amount, sender=teller.address
    )


def owner_self_deposit(teller, ripe_token, whale, owner, amount, vault_id=2):
    ripe_token.transfer(owner, amount, sender=whale)
    ripe_token.approve(teller, amount, sender=owner)
    return teller.deposit(ripe_token, amount, owner, ZERO_ADDRESS, vault_id, sender=owner)


def pending_transfer(contributor):
    data = contributor.pendingRipeTransfer()
    return data.recipient, data.initiatedBlock, data.confirmBlock


def pending_owner(contributor):
    data = contributor.pendingOwner()
    return data.newOwner, data.initiatedBlock, data.confirmBlock


def hr_pending_action(human_resources, aid):
    return human_resources.pendingActions(aid)


def owner_unlock(ripe_gov_vault, ripe_token, owner):
    return ripe_gov_vault.userGovData(owner, ripe_token).unlock


def clone_unlock(ripe_gov_vault, ripe_token, contributor):
    return ripe_gov_vault.userGovData(contributor, ripe_token).unlock


def cash_clamp(duration, min_lock, max_lock):
    locked = max(min_lock, duration)
    return min(locked, max_lock)


def overflow_compensation(elapsed=2):
    safe = MAX_UINT256 // elapsed
    return safe, safe + 1

