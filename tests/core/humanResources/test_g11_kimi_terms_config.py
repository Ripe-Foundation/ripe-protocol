"""Group 11 (kimi) proof tests — never-skip #5: terms, budget, create, Delta HR config.

- lock-duration acceptance set {0, below min, exact min, exact max, max+1}
  still creates; overflow-sized D is rejected at initiate
- compensation > ripeAvailForHr rejected; two overlapping pendings: second
  confirm returns False and leaves no extra clone
- Delta overwrite of ripeAvailForHr between initiate and confirm: False
  confirm, no clone, no NewContributorConfirmed, no NewContributorCancelled
- budget-liveness: MAX overwrite succeeds with a live grant; cancel clamps
  unrepresentable credit
- Delta setters: real initiate+execute validation boundaries
- cross-field feasibility: minCliff > maxVest execute reverts
- startDelay = uint256.max is rejected at initiate even when maxStartDelay is 0
- HR vs Delta timelock boundary semantics
- official create pause / Ledger pause atomicity
"""
import boa

from conf_utils import filter_logs
from constants import MAX_UINT256, ZERO_ADDRESS
from contracts.modules import Contributor


WEEK = 7 * 24 * 3600
MONTH = 30 * 24 * 3600
YEAR = 365 * 24 * 3600


def _ts():
    return boa.env.evm.patch.timestamp


def _bn():
    return boa.env.evm.patch.block_number


def _travel_to_ts(t):
    now = _ts()
    if now < t:
        boa.env.time_travel(seconds=t - now)


def _deploy(human_resources, setupHrConfig, setupLedgerBalance, governance,
            valid_contributor_terms, **overrides):
    terms = dict(valid_contributor_terms)
    terms.update(overrides)
    setupHrConfig()
    setupLedgerBalance(terms["compensation"])
    aid = human_resources.initiateNewContributor(
        terms["owner"], terms["manager"], terms["compensation"],
        terms["startDelay"], terms["vestingLength"], terms["cliffLength"],
        terms["unlockLength"], terms["depositLockDuration"],
        sender=governance.address,
    )
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid, sender=governance.address)
    events = filter_logs(human_resources, "NewContributorConfirmed")
    return Contributor.at(events[-1].contributorAddr)


def _delta_execute(switchboard_delta, governance, aid):
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    return switchboard_delta.executePendingAction(aid, sender=governance.address)


def test_g11_lock_duration_acceptance_set(
    human_resources, setupHrConfig, setupLedgerBalance, governance,
    valid_contributor_terms, owner_address, manager_address,
):
    """In-band and below-min D validate; zero, above live max, and overflow D are rejected."""
    setupHrConfig()
    setupLedgerBalance(10 * valid_contributor_terms["compensation"])
    t = valid_contributor_terms
    for dur in [1, 99, 100, 1000]:
        assert human_resources.areValidContributorTerms(
            t["owner"], t["manager"], t["compensation"], t["startDelay"],
            t["vestingLength"], t["cliffLength"], t["unlockLength"], dur,
        ), dur
        aid = human_resources.initiateNewContributor(
            t["owner"], t["manager"], t["compensation"], t["startDelay"],
            t["vestingLength"], t["cliffLength"], t["unlockLength"], dur,
            sender=governance.address,
        )
        assert aid != 0
        human_resources.cancelNewContributor(aid, sender=governance.address)
    for dur in [0, 1001, MAX_UINT256]:
        assert not human_resources.areValidContributorTerms(
            t["owner"], t["manager"], t["compensation"], t["startDelay"],
            t["vestingLength"], t["cliffLength"], t["unlockLength"], dur,
        )
        with boa.reverts("invalid terms"):
            human_resources.initiateNewContributor(
                t["owner"], t["manager"], t["compensation"], t["startDelay"],
                t["vestingLength"], t["cliffLength"], t["unlockLength"], dur,
                sender=governance.address,
            )


def test_g11_terms_rejections_and_overlapping_pendings(
    human_resources, setupHrConfig, setupLedgerBalance, governance,
    valid_contributor_terms, owner_address, manager_address,
):
    """Documented zeros/orderings rejected; compensation > ripeAvailForHr
    rejected; two overlapping pendings that each fit the pot at initiate: the
    second confirm returns False and leaves no extra clone."""
    setupHrConfig()
    t = valid_contributor_terms
    setupLedgerBalance(t["compensation"])

    # compensation > ripeAvailForHr
    assert not human_resources.areValidContributorTerms(
        t["owner"], t["manager"], t["compensation"] + 1, t["startDelay"],
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"])
    # zeros and orderings
    assert not human_resources.areValidContributorTerms(
        t["owner"], t["manager"], 0, t["startDelay"],
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"])
    assert not human_resources.areValidContributorTerms(
        t["owner"], t["manager"], t["compensation"], t["startDelay"],
        t["vestingLength"], 0, t["unlockLength"], t["depositLockDuration"])  # cliff 0
    assert not human_resources.areValidContributorTerms(
        t["owner"], t["manager"], t["compensation"], t["startDelay"],
        0, t["cliffLength"], t["unlockLength"], t["depositLockDuration"])  # vesting 0
    assert not human_resources.areValidContributorTerms(
        t["owner"], t["manager"], t["compensation"], t["startDelay"],
        t["vestingLength"], t["cliffLength"], t["vestingLength"] + 1, t["depositLockDuration"])  # unlock > vesting
    assert not human_resources.areValidContributorTerms(
        t["owner"], t["manager"], t["compensation"], t["startDelay"],
        t["vestingLength"], t["unlockLength"] + 1, t["unlockLength"], t["depositLockDuration"])  # cliff > unlock
    assert not human_resources.areValidContributorTerms(
        ZERO_ADDRESS, t["manager"], t["compensation"], t["startDelay"],
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"])

    # two overlapping pendings, each fits the pot at initiate
    aid1 = human_resources.initiateNewContributor(
        t["owner"], t["manager"], t["compensation"], t["startDelay"],
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"],
        sender=governance.address)
    aid2 = human_resources.initiateNewContributor(
        t["owner"], t["manager"], t["compensation"], t["startDelay"],
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"],
        sender=governance.address)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid1, sender=governance.address)
    confirmed = filter_logs(human_resources, "NewContributorConfirmed")
    assert len(confirmed) == 1
    n_contrib = human_resources.getTotalCompensation()  # one clone live
    # second confirm: revalidation fails (pot drained) -> False, pending cancelled
    assert human_resources.confirmNewContributor(aid2, sender=governance.address) is False
    # re-validation cancel emits NEITHER NewContributorConfirmed NOR
    # NewContributorCancelled (read immediately, same handle)
    assert len(filter_logs(human_resources, "NewContributorConfirmed")) == 0
    assert len(filter_logs(human_resources, "NewContributorCancelled")) == 0
    assert human_resources.getTotalCompensation() == n_contrib  # no extra clone


def test_g11_delta_overwrite_between_initiate_and_confirm(
    human_resources, setupHrConfig, setupLedgerBalance, governance,
    switchboard_delta, valid_contributor_terms,
):
    """Delta overwrite of ripeAvailForHr between initiate and confirm: confirm
    returns False, no clone, no Confirmed/Cancelled events."""
    setupHrConfig()
    t = valid_contributor_terms
    setupLedgerBalance(t["compensation"])
    aid = human_resources.initiateNewContributor(
        t["owner"], t["manager"], t["compensation"], t["startDelay"],
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"],
        sender=governance.address)
    # governance overwrites the budget below the pending compensation
    budget_aid = switchboard_delta.setRipeAvailableForHr(t["compensation"] - 1, sender=governance.address)
    assert _delta_execute(switchboard_delta, governance, budget_aid)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid, sender=governance.address) is False
    assert len(filter_logs(human_resources, "NewContributorConfirmed")) == 0
    assert len(filter_logs(human_resources, "NewContributorCancelled")) == 0


def test_g11_budget_liveness_near_uint256_overwrite_allows_cancel(
    human_resources, setupHrConfig, setupLedgerBalance, setupRipeGovVaultConfig,
    ripe_token, ledger, switchboard_delta, governance, valid_contributor_terms,
):
    """MAX budget write succeeds with a live grant; cancel at MAX clamps credit to 0."""
    setupRipeGovVaultConfig()
    c = _deploy(human_resources, setupHrConfig, setupLedgerBalance, governance, valid_contributor_terms)
    _travel_to_ts(c.startTime() + 10)

    big_aid = switchboard_delta.setRipeAvailableForHr(MAX_UINT256, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(big_aid, sender=governance.address)
    assert ledger.ripeAvailForHr() == MAX_UINT256

    cancel_aid = switchboard_delta.cancelPaycheckForContributor(c.address, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(cancel_aid, sender=governance.address)
    assert c.compensation() == 0
    assert ledger.ripeAvailForHr() == MAX_UINT256


def test_g11_delta_setters_validation_and_merge(
    human_resources, setupHrConfig, setupLedgerBalance, governance,
    switchboard_delta, mission_control, valid_contributor_terms,
):
    """Real Delta initiate+execute: setter validation boundaries and field merge."""
    setupHrConfig()
    # setMaxCompensation(0) rejected
    with boa.reverts("invalid max compensation"):
        switchboard_delta.setMaxCompensation(0, sender=governance.address)
    # setMinCliffLength(WEEK) rejected; WEEK+1 accepted
    with boa.reverts("invalid min cliff length"):
        switchboard_delta.setMinCliffLength(WEEK, sender=governance.address)
    aid_cliff = switchboard_delta.setMinCliffLength(WEEK + 1, sender=governance.address)
    # setVestingLengthBoundaries rejects launch's one-week min and a ten-year max
    with boa.reverts("invalid min vesting length"):
        switchboard_delta.setVestingLengthBoundaries(WEEK, 2 * YEAR, sender=governance.address)
    with boa.reverts("invalid max vesting length"):
        switchboard_delta.setVestingLengthBoundaries(MONTH + 1, 10 * YEAR, sender=governance.address)
    aid_vest = switchboard_delta.setVestingLengthBoundaries(MONTH + 1, 5 * YEAR, sender=governance.address)

    cfg0 = mission_control.hrConfig()
    assert _delta_execute(switchboard_delta, governance, aid_cliff)
    cfg1 = mission_control.hrConfig()
    # merge: only minCliffLength changed
    assert cfg1.minCliffLength == WEEK + 1
    assert cfg1.maxCompensation == cfg0.maxCompensation
    assert cfg1.maxStartDelay == cfg0.maxStartDelay
    assert cfg1.minVestingLength == cfg0.minVestingLength
    assert cfg1.maxVestingLength == cfg0.maxVestingLength
    assert cfg1.contribTemplate == cfg0.contribTemplate

    assert _delta_execute(switchboard_delta, governance, aid_vest)
    cfg2 = mission_control.hrConfig()
    assert cfg2.minVestingLength == MONTH + 1
    assert cfg2.maxVestingLength == 5 * YEAR
    assert cfg2.minCliffLength == WEEK + 1  # previous field not stomped


def test_g11_cross_field_infeasible_config_blocks_new_contributors(
    human_resources, setupHrConfig, setupLedgerBalance, governance,
    switchboard_delta, mission_control, valid_contributor_terms,
):
    """Infeasible minCliff > maxVest execute reverts; live config and a pending create stay intact."""
    setupHrConfig()
    t = valid_contributor_terms
    setupLedgerBalance(t["compensation"])
    # positive control: a clone confirms under the feasible config
    c0 = _deploy(human_resources, setupHrConfig, setupLedgerBalance, governance,
                 valid_contributor_terms)
    assert c0.address != ZERO_ADDRESS

    # pending contributor under the still-feasible config
    setupLedgerBalance(t["compensation"])
    aid_pending = human_resources.initiateNewContributor(
        t["owner"], t["manager"], t["compensation"], t["startDelay"],
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"],
        sender=governance.address)

    # raise minCliff above the live maxVestingLength (each arg individually valid)
    live = mission_control.hrConfig()
    aid_cliff = switchboard_delta.setMinCliffLength(4 * YEAR + WEEK, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    with boa.reverts("infeasible hr config"):
        switchboard_delta.executePendingAction(aid_cliff, sender=governance.address)
    cfg = mission_control.hrConfig()
    assert cfg.minCliffLength == live.minCliffLength
    assert cfg.maxVestingLength == live.maxVestingLength
    assert switchboard_delta.actionType(aid_cliff) != 0

    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid_pending, sender=governance.address)
    c1 = _deploy(human_resources, setupHrConfig, setupLedgerBalance, governance,
                 valid_contributor_terms)
    assert c1.address != ZERO_ADDRESS


def test_g11_max_start_delay_zero_constructor_overflow(
    human_resources, setupHrConfig, setupLedgerBalance, governance,
    switchboard_delta, mission_control, valid_contributor_terms,
):
    """startDelay = uint256.max is rejected at initiate even when maxStartDelay is 0."""
    setupHrConfig()
    t = valid_contributor_terms
    setupLedgerBalance(t["compensation"])

    # remove the cap via the real Delta path
    aid0 = switchboard_delta.setMaxStartDelay(0, sender=governance.address)
    assert _delta_execute(switchboard_delta, governance, aid0)
    assert mission_control.hrConfig().maxStartDelay == 0

    assert not human_resources.areValidContributorTerms(
        t["owner"], t["manager"], t["compensation"], MAX_UINT256,
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"])
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(
            t["owner"], t["manager"], t["compensation"], MAX_UINT256,
            t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"],
            sender=governance.address)

    now = _ts()
    max_ok = MAX_UINT256 - now - t["vestingLength"]
    assert human_resources.areValidContributorTerms(
        t["owner"], t["manager"], t["compensation"], max_ok,
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"])
    aid = human_resources.initiateNewContributor(
        t["owner"], t["manager"], t["compensation"], max_ok,
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"],
        sender=governance.address)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    boa.env.time_travel(seconds=1)
    assert human_resources.confirmNewContributor(aid, sender=governance.address) is False
    assert human_resources.pendingContributor(aid).owner == ZERO_ADDRESS
    assert len(filter_logs(human_resources, "NewContributorConfirmed")) == 0
    assert len(filter_logs(human_resources, "NewContributorCancelled")) == 0


def test_g11_hr_timelock_boundaries(
    human_resources, setupHrConfig, setupLedgerBalance, governance,
    valid_contributor_terms,
):
    """HR engine: confirmBlock-1 reverts (pending stays); exact confirmBlock
    confirms; exact expiration reverts (pending stays until explicit cancel);
    invalid terms -> False cancel even before confirmBlock."""
    setupHrConfig()
    t = valid_contributor_terms
    setupLedgerBalance(2 * t["compensation"])

    # early: confirmBlock - 1 reverts, pending stays
    aid = human_resources.initiateNewContributor(
        t["owner"], t["manager"], t["compensation"], t["startDelay"],
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"],
        sender=governance.address)
    confirm_block = human_resources.getActionConfirmationBlock(aid)
    boa.env.time_travel(blocks=confirm_block - 1 - _bn())
    with boa.reverts("time lock not reached"):
        human_resources.confirmNewContributor(aid, sender=governance.address)
    assert human_resources.pendingContributor(aid).owner == t["owner"]

    # exact confirmBlock: confirms
    boa.env.time_travel(blocks=1)
    assert human_resources.confirmNewContributor(aid, sender=governance.address)

    # expiration: valid terms, exact expiration -> revert, pending stays
    aid2 = human_resources.initiateNewContributor(
        t["owner"], t["manager"], t["compensation"], t["startDelay"],
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"],
        sender=governance.address)
    expiration = human_resources.pendingActions(aid2).expiration
    boa.env.time_travel(blocks=expiration - _bn())
    with boa.reverts("time lock not reached"):
        human_resources.confirmNewContributor(aid2, sender=governance.address)
    assert human_resources.pendingContributor(aid2).owner == t["owner"]
    # explicit cancelNewContributor cleanup after expiry
    assert human_resources.cancelNewContributor(aid2, sender=governance.address)
    assert len(filter_logs(human_resources, "NewContributorCancelled")) == 1

    # invalid terms -> False cancel even BEFORE confirmBlock
    aid3 = human_resources.initiateNewContributor(
        t["owner"], t["manager"], t["compensation"], t["startDelay"],
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"],
        sender=governance.address)
    # drain the budget so revalidation fails
    setupLedgerBalance(0)
    assert human_resources.confirmNewContributor(aid3, sender=governance.address) is False
    assert human_resources.pendingContributor(aid3).owner == ZERO_ADDRESS


def test_g11_create_pause_and_ledger_pause_atomicity(
    human_resources, setupHrConfig, setupLedgerBalance, governance,
    switchboard_charlie, ledger, valid_contributor_terms,
):
    """Charlie/HR pause blocks initiate/confirm/cancel; unpause retries.
    Ledger pause: create_from_blueprint then addHrContributor must revert
    atomically — no orphan clone, no contributor-list entry, no budget
    decrement, no NewContributorConfirmed, HR action not consumed."""
    setupHrConfig()
    t = valid_contributor_terms
    setupLedgerBalance(t["compensation"])

    # HR paused: initiate reverts
    assert switchboard_charlie.pause(human_resources.address, True, sender=governance.address)
    with boa.reverts("contract paused"):
        human_resources.initiateNewContributor(
            t["owner"], t["manager"], t["compensation"], t["startDelay"],
            t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"],
            sender=governance.address)
    assert switchboard_charlie.pause(human_resources.address, False, sender=governance.address)

    # Ledger paused at confirm: atomic revert, no orphan
    aid = human_resources.initiateNewContributor(
        t["owner"], t["manager"], t["compensation"], t["startDelay"],
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"],
        sender=governance.address)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    num0 = ledger.numContributors()  # 0 when empty; after one clone it is 2
    avail0 = ledger.ripeAvailForHr()
    assert switchboard_charlie.pause(ledger.address, True, sender=governance.address)
    with boa.reverts("not activated"):
        human_resources.confirmNewContributor(aid, sender=governance.address)
    assert ledger.numContributors() == num0  # no contributor-list entry
    assert ledger.ripeAvailForHr() == avail0  # no budget decrement
    assert human_resources.pendingContributor(aid).owner == t["owner"]  # action not consumed
    # unpause -> same pending confirms
    assert switchboard_charlie.pause(ledger.address, False, sender=governance.address)
    assert human_resources.confirmNewContributor(aid, sender=governance.address)
    assert len(filter_logs(human_resources, "NewContributorConfirmed")) == 1
    assert ledger.numContributors() == num0 + 1 + (1 if num0 == 0 else 0)


def test_g11_owner_eq_manager_allowed_owner_eq_clone_not(
    human_resources, setupHrConfig, setupLedgerBalance, governance,
    valid_contributor_terms, owner_address,
):
    """owner == manager is allowed; owner == clone is impossible (clone address
    does not exist at initiate; constructor rejects _owner == self)."""
    setupHrConfig()
    t = valid_contributor_terms
    setupLedgerBalance(t["compensation"])
    assert human_resources.areValidContributorTerms(
        owner_address, owner_address, t["compensation"], t["startDelay"],
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"])
    aid = human_resources.initiateNewContributor(
        owner_address, owner_address, t["compensation"], t["startDelay"],
        t["vestingLength"], t["cliffLength"], t["unlockLength"], t["depositLockDuration"],
        sender=governance.address)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid, sender=governance.address)
    events = filter_logs(human_resources, "NewContributorConfirmed")
    c = Contributor.at(events[-1].contributorAddr)
    assert c.owner() == c.manager() == owner_address
