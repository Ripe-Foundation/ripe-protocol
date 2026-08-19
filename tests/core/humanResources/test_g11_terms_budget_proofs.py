import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS
from contracts.modules import Contributor
from tests.core.humanResources.g11_proof_helpers import (
    release_live_hr_reserve,
    MONTH_IN_SECONDS,
    WEEK_IN_SECONDS,
    YEAR_IN_SECONDS,
    charlie_pause,
    delta_confirm_and_execute,
    deploy_clone,
    initiate_contributor,
    official_delta_budget,
    official_delta_cancel,
    overflow_compensation,
    terms_tuple,
    travel_to_block,
    travel_to_ts,
)


def _valid(terms, **overrides):
    out = dict(terms)
    out.update(overrides)
    return out


def test_g11_are_valid_rejects_documented_zeros_and_orderings(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
    governance,
):
    setupHrConfig()
    setupLedgerBalance(valid_contributor_terms["compensation"])
    t = valid_contributor_terms
    assert human_resources.areValidContributorTerms(*terms_tuple(t))
    assert not human_resources.areValidContributorTerms(*terms_tuple(_valid(t, compensation=0)))
    assert not human_resources.areValidContributorTerms(
        *terms_tuple(_valid(t, compensation=t["compensation"] + 1))
    )
    assert not human_resources.areValidContributorTerms(*terms_tuple(_valid(t, cliffLength=0)))
    assert not human_resources.areValidContributorTerms(*terms_tuple(_valid(t, vestingLength=0)))
    assert not human_resources.areValidContributorTerms(
        *terms_tuple(_valid(t, unlockLength=t["vestingLength"] + 1))
    )
    assert not human_resources.areValidContributorTerms(
        *terms_tuple(_valid(t, cliffLength=t["unlockLength"] + 1))
    )
    assert not human_resources.areValidContributorTerms(*terms_tuple(_valid(t, owner=ZERO_ADDRESS)))
    assert not human_resources.areValidContributorTerms(*terms_tuple(_valid(t, manager=ZERO_ADDRESS)))
    assert not human_resources.areValidContributorTerms(
        *terms_tuple(_valid(t, startDelay=91 * 24 * 3600))
    )
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(
            *terms_tuple(_valid(t, compensation=0)),
            sender=governance.address,
        )


def test_g11_deposit_lock_duration_acceptance_set(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
    governance,
):
    setupHrConfig()
    setupLedgerBalance(valid_contributor_terms["compensation"])
    t = valid_contributor_terms
    for duration in (0, 50, 100, 1000, 1001):
        terms = _valid(t, depositLockDuration=duration)
        setupLedgerBalance(terms["compensation"])
        assert human_resources.areValidContributorTerms(*terms_tuple(terms))
        aid = human_resources.initiateNewContributor(
            *terms_tuple(terms), sender=governance.address
        )
        boa.env.time_travel(blocks=human_resources.actionTimeLock())
        assert human_resources.confirmNewContributor(aid, sender=governance.address)
        c = Contributor.at(filter_logs(human_resources, "NewContributorConfirmed")[0].contributorAddr)
        assert c.depositLockDuration() == duration
    terms_max = _valid(t, depositLockDuration=MAX_UINT256)
    setupLedgerBalance(terms_max["compensation"])
    assert human_resources.areValidContributorTerms(*terms_tuple(terms_max)) is False
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(
            *terms_tuple(terms_max), sender=governance.address
        )


def test_g11_two_overlapping_pendings_second_confirm_false_no_extra_clone(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
    governance,
    ledger,
):
    setupHrConfig()
    pot = valid_contributor_terms["compensation"]
    setupLedgerBalance(pot)
    t1 = _valid(valid_contributor_terms, owner="0x" + "b1" * 20, manager="0x" + "c1" * 20)
    t2 = _valid(valid_contributor_terms, owner="0x" + "b2" * 20, manager="0x" + "c2" * 20)
    aid1 = initiate_contributor(human_resources, governance, t1)
    aid2 = initiate_contributor(human_resources, governance, t2)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    num_before = ledger.numContributors()
    budget_before = ledger.ripeAvailForHr()
    assert human_resources.confirmNewContributor(aid1, sender=governance.address) is True
    after_first = ledger.numContributors()
    assert after_first == (2 if num_before == 0 else num_before + 1)
    result = human_resources.confirmNewContributor(aid2, sender=governance.address)
    assert result is False
    assert filter_logs(human_resources, "NewContributorConfirmed") == []
    assert filter_logs(human_resources, "NewContributorCancelled") == []
    assert human_resources.pendingContributor(aid2).owner == ZERO_ADDRESS
    assert ledger.ripeAvailForHr() == budget_before - pot
    assert ledger.numContributors() == after_first


def test_g11_delta_budget_overwrite_between_initiate_and_confirm_false_no_events(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
    governance,
    switchboard_delta,
    ledger,
):
    setupHrConfig()
    setupLedgerBalance(valid_contributor_terms["compensation"])
    aid = initiate_contributor(human_resources, governance, valid_contributor_terms)
    official_delta_budget(switchboard_delta, governance, 0)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    num = ledger.numContributors()
    result = human_resources.confirmNewContributor(aid, sender=governance.address)
    assert result is False
    assert filter_logs(human_resources, "NewContributorConfirmed") == []
    assert filter_logs(human_resources, "NewContributorCancelled") == []
    assert ledger.numContributors() == num
    assert human_resources.pendingContributor(aid).owner == ZERO_ADDRESS


def test_g11_near_uint256_budget_overwrite_keeps_cancel_live(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    setupRipeGovVaultConfig,
    valid_contributor_terms,
    switchboard_delta,
    governance,
    ledger,
):
    """MAX setter reverts while cancel-credit liability > 0; a legal write then cancel succeeds."""
    setupRipeGovVaultConfig()
    release_live_hr_reserve(switchboard_delta, governance, ledger)
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    liability = ledger.hrReservedCompensation()
    assert liability == c.compensation()
    assert ledger.hrReservedCompensation() == c.compensation()
    budget_before = ledger.ripeAvailForHr()
    aid_max = switchboard_delta.setRipeAvailableForHr(MAX_UINT256, sender=governance.address)
    travel_to_block(switchboard_delta.getActionConfirmationBlock(aid_max))
    with boa.reverts("exceeds hr budget headroom"):
        switchboard_delta.executePendingAction(aid_max, sender=governance.address)
    assert ledger.ripeAvailForHr() == budget_before
    assert switchboard_delta.actionType(aid_max) != 0
    assert filter_logs(switchboard_delta, "RipeAvailableForHrSet") == []

    cap = MAX_UINT256 - liability
    official_delta_budget(switchboard_delta, governance, cap)
    assert ledger.ripeAvailForHr() == cap
    aid_over = switchboard_delta.setRipeAvailableForHr(cap + 1, sender=governance.address)
    travel_to_block(switchboard_delta.getActionConfirmationBlock(aid_over))
    with boa.reverts("exceeds hr budget headroom"):
        switchboard_delta.executePendingAction(aid_over, sender=governance.address)

    aid, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.compensation() == 0
    assert ledger.hrReservedCompensation() == 0
    official_delta_budget(switchboard_delta, governance, MAX_UINT256)
    assert ledger.ripeAvailForHr() == MAX_UINT256


def test_g11_near_uint256_budget_overwrite_cancel_rolls_back_then_retry_after_correction(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    setupRipeGovVaultConfig,
    valid_contributor_terms,
    switchboard_delta,
    governance,
    ledger,
):
    """MAX setter reverts while liability > 0; a legal write then cancel succeeds."""
    setupRipeGovVaultConfig()
    release_live_hr_reserve(switchboard_delta, governance, ledger)
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    orig = c.compensation()
    budget_before = ledger.ripeAvailForHr()
    aid_max = switchboard_delta.setRipeAvailableForHr(MAX_UINT256, sender=governance.address)
    travel_to_block(switchboard_delta.getActionConfirmationBlock(aid_max))
    with boa.reverts("exceeds hr budget headroom"):
        switchboard_delta.executePendingAction(aid_max, sender=governance.address)
    assert ledger.ripeAvailForHr() == budget_before
    assert switchboard_delta.actionType(aid_max) != 0
    official_delta_budget(
        switchboard_delta, governance, MAX_UINT256 - ledger.hrReservedCompensation()
    )
    aid, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.compensation() == 0
    assert ledger.hrReservedCompensation() == 0
    assert ledger.ripeAvailForHr() == MAX_UINT256 - orig + orig


def test_g11_overflow_compensation_create_succeeds_under_uncapped_max(
    valid_contributor_terms,
    setupHrConfig,
    setupLedgerBalance,
    human_resources,
    governance,
):
    _, overflow_comp = overflow_compensation(2)
    setupHrConfig(_maxCompensation=0)
    setupLedgerBalance(overflow_comp)
    terms = _valid(valid_contributor_terms, compensation=overflow_comp)
    assert human_resources.areValidContributorTerms(*terms_tuple(terms)) is False
    with boa.reverts("invalid terms"):
        initiate_contributor(human_resources, governance, terms)


def test_g11_max_compensation_zero_does_not_cap_create(
    valid_contributor_terms,
    setupHrConfig,
    setupLedgerBalance,
    human_resources,
    governance,
):
    setupHrConfig(_maxCompensation=0)
    fat = 2_000_000 * EIGHTEEN_DECIMALS
    setupLedgerBalance(fat)
    terms = _valid(valid_contributor_terms, compensation=fat)
    assert human_resources.areValidContributorTerms(*terms_tuple(terms))
    aid = initiate_contributor(human_resources, governance, terms)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid, sender=governance.address)


def test_g11_rotated_template_confirm_uses_live_template(
    valid_contributor_terms,
    setupHrConfig,
    setupLedgerBalance,
    human_resources,
    governance,
    switchboard_delta,
    mission_control,
    contributor_template,
):
    setupHrConfig(_contribTemplate=contributor_template.address)
    setupLedgerBalance(valid_contributor_terms["compensation"])
    aid = initiate_contributor(human_resources, governance, valid_contributor_terms)
    template_b = boa.load_partial("contracts/modules/Contributor.vy").deploy_as_blueprint()
    tid = switchboard_delta.setContributorTemplate(template_b.address, sender=governance.address)
    assert delta_confirm_and_execute(switchboard_delta, governance, tid) is True
    assert mission_control.hrConfig().contribTemplate == template_b.address
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid, sender=governance.address) is True
    clone = filter_logs(human_resources, "NewContributorConfirmed")[0].contributorAddr
    c = Contributor.at(clone)
    assert c.owner() == valid_contributor_terms["owner"]
    assert mission_control.hrConfig().contribTemplate == template_b.address


def test_g11_delta_setters_reject_launch_and_zero_accept_legal(
    switchboard_delta,
    governance,
    mission_control,
    setupHrConfig,
):
    setupHrConfig()
    live = mission_control.hrConfig()
    with boa.reverts("invalid max compensation"):
        switchboard_delta.setMaxCompensation(0, sender=governance.address)
    with boa.reverts("invalid min cliff length"):
        switchboard_delta.setMinCliffLength(WEEK_IN_SECONDS, sender=governance.address)
    aid_cliff = switchboard_delta.setMinCliffLength(WEEK_IN_SECONDS + 1, sender=governance.address)
    assert delta_confirm_and_execute(switchboard_delta, governance, aid_cliff)
    assert mission_control.hrConfig().minCliffLength == WEEK_IN_SECONDS + 1
    assert mission_control.hrConfig().maxCompensation == live.maxCompensation
    with boa.reverts("invalid min vesting length"):
        switchboard_delta.setVestingLengthBoundaries(
            WEEK_IN_SECONDS, 4 * YEAR_IN_SECONDS, sender=governance.address
        )
    with boa.reverts("invalid max vesting length"):
        switchboard_delta.setVestingLengthBoundaries(
            MONTH_IN_SECONDS + 1, 10 * YEAR_IN_SECONDS, sender=governance.address
        )


def test_g11_two_parallel_hr_config_pendings_merge(
    switchboard_delta,
    governance,
    mission_control,
    setupHrConfig,
):
    setupHrConfig()
    live = mission_control.hrConfig()
    aid_comp = switchboard_delta.setMaxCompensation(2_000_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    aid_cliff = switchboard_delta.setMinCliffLength(WEEK_IN_SECONDS + 5, sender=governance.address)
    assert delta_confirm_and_execute(switchboard_delta, governance, aid_comp)
    assert delta_confirm_and_execute(switchboard_delta, governance, aid_cliff)
    cfg = mission_control.hrConfig()
    assert cfg.maxCompensation == 2_000_000 * EIGHTEEN_DECIMALS
    assert cfg.minCliffLength == WEEK_IN_SECONDS + 5
    assert cfg.minVestingLength == live.minVestingLength
    assert cfg.maxVestingLength == live.maxVestingLength
    assert cfg.maxStartDelay == live.maxStartDelay
    assert cfg.contribTemplate == live.contribTemplate


def test_g11_cross_field_min_cliff_gt_max_vest_blocks_all_terms(
    switchboard_delta,
    governance,
    mission_control,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
    human_resources,
    contributor_template,
):
    setupHrConfig()
    setupLedgerBalance(valid_contributor_terms["compensation"])
    assert human_resources.areValidContributorTerms(*terms_tuple(valid_contributor_terms))
    live = mission_control.hrConfig()
    raise_cliff = switchboard_delta.setMinCliffLength(5 * YEAR_IN_SECONDS, sender=governance.address)
    travel_to_block(switchboard_delta.getActionConfirmationBlock(raise_cliff))
    with boa.reverts("infeasible hr config"):
        switchboard_delta.executePendingAction(raise_cliff, sender=governance.address)
    cfg = mission_control.hrConfig()
    assert cfg.minCliffLength == live.minCliffLength
    assert cfg.maxVestingLength == live.maxVestingLength
    assert switchboard_delta.actionType(raise_cliff) != 0
    assert filter_logs(switchboard_delta, "HrMinCliffLengthSet") == []

    equal = switchboard_delta.setMinCliffLength(live.maxVestingLength, sender=governance.address)
    assert delta_confirm_and_execute(switchboard_delta, governance, equal)
    assert mission_control.hrConfig().minCliffLength == live.maxVestingLength

    setupHrConfig()
    assert human_resources.areValidContributorTerms(*terms_tuple(valid_contributor_terms))
    restore_terms = _valid(valid_contributor_terms, owner="0x" + "c1" * 20, manager="0x" + "c2" * 20)
    setupLedgerBalance(restore_terms["compensation"])
    aid_restore = initiate_contributor(human_resources, governance, restore_terms)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid_restore, sender=governance.address) is True


def test_g11_two_parallel_pendings_combine_into_infeasible_config(
    switchboard_delta,
    governance,
    mission_control,
    setupHrConfig,
    valid_contributor_terms,
    human_resources,
    setupLedgerBalance,
):
    setupHrConfig()
    setupLedgerBalance(valid_contributor_terms["compensation"])
    live = mission_control.hrConfig()
    aid_cliff = switchboard_delta.setMinCliffLength(4 * YEAR_IN_SECONDS, sender=governance.address)
    aid_vest = switchboard_delta.setVestingLengthBoundaries(
        MONTH_IN_SECONDS + 1, YEAR_IN_SECONDS, sender=governance.address
    )
    assert delta_confirm_and_execute(switchboard_delta, governance, aid_cliff)
    assert mission_control.hrConfig().minCliffLength == 4 * YEAR_IN_SECONDS
    travel_to_block(switchboard_delta.getActionConfirmationBlock(aid_vest))
    with boa.reverts("infeasible hr config"):
        switchboard_delta.executePendingAction(aid_vest, sender=governance.address)
    cfg = mission_control.hrConfig()
    assert cfg.minCliffLength == 4 * YEAR_IN_SECONDS
    assert cfg.maxVestingLength == live.maxVestingLength
    assert switchboard_delta.actionType(aid_vest) != 0
    assert filter_logs(switchboard_delta, "HrVestingLengthBoundariesSet") == []
    setupHrConfig()
    assert human_resources.areValidContributorTerms(*terms_tuple(valid_contributor_terms))


def test_g11_max_start_delay_zero_constructor_overflow_pending_stays_then_revalidate_cancels(
    switchboard_delta,
    governance,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
    human_resources,
    mission_control,
):
    """startDelay = uint256.max is rejected at initiate even when maxStartDelay is 0."""
    setupHrConfig()
    setupLedgerBalance(valid_contributor_terms["compensation"] * 2)
    aid0 = switchboard_delta.setMaxStartDelay(0, sender=governance.address)
    assert delta_confirm_and_execute(switchboard_delta, governance, aid0)
    assert mission_control.hrConfig().maxStartDelay == 0

    terms_max = _valid(valid_contributor_terms, startDelay=MAX_UINT256)
    assert human_resources.areValidContributorTerms(*terms_tuple(terms_max)) is False
    with boa.reverts("invalid terms"):
        initiate_contributor(human_resources, governance, terms_max)

    vest = valid_contributor_terms["vestingLength"]
    now = boa.env.evm.patch.timestamp
    boundary = MAX_UINT256 - now - vest
    terms_ok = _valid(valid_contributor_terms, startDelay=boundary)
    assert human_resources.areValidContributorTerms(*terms_tuple(terms_ok))
    aid_ok = initiate_contributor(human_resources, governance, terms_ok)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    boa.env.time_travel(seconds=1)
    assert human_resources.confirmNewContributor(aid_ok, sender=governance.address) is False
    assert filter_logs(human_resources, "NewContributorConfirmed") == []
    assert filter_logs(human_resources, "NewContributorCancelled") == []
    assert human_resources.pendingContributor(aid_ok).owner == ZERO_ADDRESS

    enormous = 10**18
    terms_huge = _valid(valid_contributor_terms, startDelay=enormous)
    assert human_resources.areValidContributorTerms(*terms_tuple(terms_huge))
    aid_huge = initiate_contributor(human_resources, governance, terms_huge)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid_huge, sender=governance.address) is True
    c = Contributor.at(filter_logs(human_resources, "NewContributorConfirmed")[0].contributorAddr)
    assert c.startTime() == boa.env.evm.patch.timestamp + enormous


def test_g11_hr_vs_delta_timelock_valid_and_invalid(
    human_resources,
    switchboard_delta,
    governance,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
    ledger,
):
    setupHrConfig()
    setupLedgerBalance(valid_contributor_terms["compensation"] * 4)

    aid_hr = initiate_contributor(human_resources, governance, valid_contributor_terms)
    hr_action = human_resources.pendingActions(aid_hr)
    travel_to_block(hr_action.confirmBlock - 1)
    with boa.reverts("time lock not reached"):
        human_resources.confirmNewContributor(aid_hr, sender=governance.address)
    assert human_resources.pendingContributor(aid_hr).owner != ZERO_ADDRESS
    assert human_resources.pendingActions(aid_hr).confirmBlock == hr_action.confirmBlock

    travel_to_block(hr_action.confirmBlock)
    assert human_resources.confirmNewContributor(aid_hr, sender=governance.address) is True

    t2 = _valid(valid_contributor_terms, owner="0x" + "d1" * 20, manager="0x" + "d2" * 20)
    aid_hr2 = initiate_contributor(human_resources, governance, t2)
    hr2 = human_resources.pendingActions(aid_hr2)
    travel_to_block(hr2.expiration - 1)
    assert human_resources.confirmNewContributor(aid_hr2, sender=governance.address) is True

    t3 = _valid(valid_contributor_terms, owner="0x" + "d3" * 20, manager="0x" + "d4" * 20)
    aid_hr3 = initiate_contributor(human_resources, governance, t3)
    hr3 = human_resources.pendingActions(aid_hr3)
    travel_to_block(hr3.expiration)
    with boa.reverts("time lock not reached"):
        human_resources.confirmNewContributor(aid_hr3, sender=governance.address)
    assert human_resources.pendingContributor(aid_hr3).owner != ZERO_ADDRESS
    assert human_resources.cancelNewContributor(aid_hr3, sender=governance.address)
    ev = filter_logs(human_resources, "NewContributorCancelled")
    assert len(ev) == 1

    t4 = _valid(valid_contributor_terms, owner="0x" + "d5" * 20, manager="0x" + "d6" * 20)
    aid_hr4 = initiate_contributor(human_resources, governance, t4)
    ledger.setRipeAvailForHr(0, sender=switchboard_delta.address)
    travel_to_block(human_resources.pendingActions(aid_hr4).confirmBlock - 1)
    result = human_resources.confirmNewContributor(aid_hr4, sender=governance.address)
    assert result is False
    assert filter_logs(human_resources, "NewContributorConfirmed") == []
    assert filter_logs(human_resources, "NewContributorCancelled") == []
    assert human_resources.pendingContributor(aid_hr4).owner == ZERO_ADDRESS

    setupLedgerBalance(valid_contributor_terms["compensation"] * 4)
    aid_delta = switchboard_delta.setMaxCompensation(3_000_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    d_action = switchboard_delta.pendingActions(aid_delta)
    travel_to_block(d_action.confirmBlock - 1)
    assert switchboard_delta.executePendingAction(aid_delta, sender=governance.address) is False
    assert switchboard_delta.actionType(aid_delta) != 0
    travel_to_block(d_action.confirmBlock)
    assert switchboard_delta.executePendingAction(aid_delta, sender=governance.address) is True

    aid_delta2 = switchboard_delta.setMaxCompensation(4_000_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    d2 = switchboard_delta.pendingActions(aid_delta2)
    travel_to_block(d2.expiration - 1)
    assert switchboard_delta.executePendingAction(aid_delta2, sender=governance.address) is True

    aid_delta3 = switchboard_delta.setMaxCompensation(5_000_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    d3 = switchboard_delta.pendingActions(aid_delta3)
    travel_to_block(d3.expiration)
    assert switchboard_delta.executePendingAction(aid_delta3, sender=governance.address) is False
    assert switchboard_delta.actionType(aid_delta3) == 0


def test_g11_charlie_hr_pause_blocks_create_unpause_retries(
    human_resources,
    switchboard_charlie,
    governance,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
):
    setupHrConfig()
    setupLedgerBalance(valid_contributor_terms["compensation"])
    charlie_pause(switchboard_charlie, governance, human_resources.address, True)
    with boa.reverts("contract paused"):
        initiate_contributor(human_resources, governance, valid_contributor_terms)
    charlie_pause(switchboard_charlie, governance, human_resources.address, False)
    aid = initiate_contributor(human_resources, governance, valid_contributor_terms)
    charlie_pause(switchboard_charlie, governance, human_resources.address, True)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    with boa.reverts("contract paused"):
        human_resources.confirmNewContributor(aid, sender=governance.address)
    with boa.reverts("contract paused"):
        human_resources.cancelNewContributor(aid, sender=governance.address)
    charlie_pause(switchboard_charlie, governance, human_resources.address, False)
    assert human_resources.confirmNewContributor(aid, sender=governance.address) is True


def test_g11_ledger_pause_during_confirm_no_orphan_clone(
    human_resources,
    switchboard_charlie,
    governance,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
    ledger,
):
    setupHrConfig()
    setupLedgerBalance(valid_contributor_terms["compensation"])
    aid = initiate_contributor(human_resources, governance, valid_contributor_terms)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    num = ledger.numContributors()
    budget = ledger.ripeAvailForHr()
    pending = human_resources.pendingContributor(aid)
    action = human_resources.pendingActions(aid)
    charlie_pause(switchboard_charlie, governance, ledger.address, True)
    with boa.reverts("not activated"):
        human_resources.confirmNewContributor(aid, sender=governance.address)
    assert filter_logs(human_resources, "NewContributorConfirmed") == []
    assert ledger.numContributors() == num
    assert ledger.ripeAvailForHr() == budget
    assert human_resources.pendingContributor(aid).owner == pending.owner
    assert human_resources.pendingActions(aid).confirmBlock == action.confirmBlock
    charlie_pause(switchboard_charlie, governance, ledger.address, False)
    assert human_resources.confirmNewContributor(aid, sender=governance.address) is True


def test_g11_owner_equals_manager_allowed_owner_equals_clone_rejected_at_init(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
    governance,
):
    setupHrConfig()
    same = "0x" + "ab" * 20
    terms = _valid(valid_contributor_terms, owner=same, manager=same)
    setupLedgerBalance(terms["compensation"])
    assert human_resources.areValidContributorTerms(*terms_tuple(terms))
    aid = initiate_contributor(human_resources, governance, terms)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid, sender=governance.address)
    c = Contributor.at(filter_logs(human_resources, "NewContributorConfirmed")[0].contributorAddr)
    assert c.owner() == c.manager()
    with boa.reverts("invalid new owner"):
        c.changeOwnership(c.address, sender=same)


def test_g11_are_valid_accepts_and_rejects_overflow_bounds(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
    governance,
):
    setupHrConfig(_maxCompensation=0, _maxStartDelay=0)
    t = valid_contributor_terms
    setupLedgerBalance(MAX_UINT256 // 2 + 1)
    assert human_resources.areValidContributorTerms(
        *terms_tuple(_valid(t, compensation=MAX_UINT256 // 2))
    )
    assert not human_resources.areValidContributorTerms(
        *terms_tuple(_valid(t, compensation=MAX_UINT256 // 2 + 1))
    )
    setupHrConfig(
        _maxCompensation=0,
        _maxStartDelay=0,
        _minVestingLength=0,
        _maxVestingLength=0,
        _minCliffLength=0,
    )
    setupLedgerBalance(t["compensation"])
    assert human_resources.areValidContributorTerms(
        *terms_tuple(_valid(t, vestingLength=2**128, unlockLength=2**128))
    )
    assert not human_resources.areValidContributorTerms(
        *terms_tuple(_valid(t, vestingLength=2**128 + 1, unlockLength=2**128 + 1))
    )
    d_ok = MAX_UINT256 - 2**64
    assert human_resources.areValidContributorTerms(
        *terms_tuple(_valid(t, depositLockDuration=d_ok))
    )
    assert not human_resources.areValidContributorTerms(
        *terms_tuple(_valid(t, depositLockDuration=d_ok + 1))
    )
    assert not human_resources.areValidContributorTerms(
        *terms_tuple(_valid(t, depositLockDuration=MAX_UINT256))
    )
    assert not human_resources.areValidContributorTerms(
        *terms_tuple(_valid(t, startDelay=MAX_UINT256))
    )
    with boa.reverts("invalid terms"):
        initiate_contributor(
            human_resources, governance, _valid(t, startDelay=MAX_UINT256)
        )


def test_g11_no_clones_allows_max_budget_write(
    human_resources,
    switchboard_delta,
    governance,
    ledger,
):
    release_live_hr_reserve(switchboard_delta, governance, ledger)
    assert ledger.hrReservedCompensation() == 0
    official_delta_budget(switchboard_delta, governance, MAX_UINT256)
    assert ledger.ripeAvailForHr() == MAX_UINT256




def test_g11_full_cash_leaves_reserved_and_blocks_max_budget(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    setupRipeGovVaultConfig,
    valid_contributor_terms,
    switchboard_delta,
    governance,
    ledger,
):
    """Finished vest does not release reserved. MAX setter stays blocked."""
    setupRipeGovVaultConfig()
    release_live_hr_reserve(switchboard_delta, governance, ledger)
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    orig = c.compensation()
    travel_to_ts(c.endTime())
    assert c.cashRipeCheck(sender=c.owner()) == orig
    assert c.totalClaimed() == orig
    assert ledger.hrReservedCompensation() == orig
    budget_before = ledger.ripeAvailForHr()
    aid = switchboard_delta.setRipeAvailableForHr(MAX_UINT256, sender=governance.address)
    travel_to_block(switchboard_delta.getActionConfirmationBlock(aid))
    with boa.reverts("exceeds hr budget headroom"):
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert ledger.ripeAvailForHr() == budget_before


def test_g11_after_cliff_partial_cash_cancel_leaves_cashed_notional(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    setupRipeGovVaultConfig,
    valid_contributor_terms,
    switchboard_delta,
    governance,
    ledger,
):
    """Post-cliff cancel refunds C-P and leaves leftover P in reserved."""
    setupRipeGovVaultConfig()
    release_live_hr_reserve(switchboard_delta, governance, ledger)
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    orig = c.compensation()
    travel_to_ts(c.cliffTime() + 1)
    p = c.cashRipeCheck(sender=c.owner())
    assert p > 0
    budget = ledger.ripeAvailForHr()
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    claimed = c.totalClaimed()
    assert claimed >= p
    assert ledger.ripeAvailForHr() == budget + (orig - claimed)
    assert ledger.hrReservedCompensation() == claimed


def test_g11_pre_cliff_cash_then_rest_at_end_leaves_reserved(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    setupRipeGovVaultConfig,
    valid_contributor_terms,
    switchboard_delta,
    governance,
    ledger,
):
    setupRipeGovVaultConfig()
    release_live_hr_reserve(switchboard_delta, governance, ledger)
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    orig = c.compensation()
    travel_to_ts(c.startTime() + 1)
    p = c.cashRipeCheck(sender=c.owner())
    assert p > 0
    travel_to_ts(c.endTime())
    rest = c.cashRipeCheck(sender=c.owner())
    assert rest == orig - p
    assert c.totalClaimed() == orig
    assert ledger.hrReservedCompensation() == orig
    budget_before = ledger.ripeAvailForHr()
    aid = switchboard_delta.setRipeAvailableForHr(MAX_UINT256, sender=governance.address)
    travel_to_block(switchboard_delta.getActionConfirmationBlock(aid))
    with boa.reverts("exceeds hr budget headroom"):
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert ledger.ripeAvailForHr() == budget_before


def test_g11_hr_layer_over_refund_reverts_and_leaves_reserve_and_budget(
    contributor_contract,
    human_resources,
    ledger,
):
    c = contributor_contract
    reserved = ledger.hrReservedCompensation()
    budget = ledger.ripeAvailForHr()
    with boa.reverts("hr reserve underflow"):
        human_resources.refundAfterCancelPaycheck(reserved + 1, False, sender=c.address)
    assert ledger.hrReservedCompensation() == reserved
    assert ledger.ripeAvailForHr() == budget
    assert c.compensation() != 0


def test_g11_setter_after_pre_cliff_cash_still_uses_full_grant_notional(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    setupRipeGovVaultConfig,
    valid_contributor_terms,
    switchboard_delta,
    governance,
    ledger,
):
    """After pre-cliff cash P, setter headroom is still C+B, not C-P+B."""
    setupRipeGovVaultConfig()
    release_live_hr_reserve(switchboard_delta, governance, ledger)
    a_terms = _valid(
        valid_contributor_terms,
        owner="0x" + "d1" * 20,
        manager="0x" + "d2" * 20,
    )
    b_terms = _valid(
        valid_contributor_terms,
        owner="0x" + "d3" * 20,
        manager="0x" + "d4" * 20,
    )
    setupHrConfig()
    setupLedgerBalance(a_terms["compensation"] + b_terms["compensation"])
    aid_a = initiate_contributor(human_resources, governance, a_terms)
    aid_b = initiate_contributor(human_resources, governance, b_terms)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid_a, sender=governance.address)
    addr_a = filter_logs(human_resources, "NewContributorConfirmed")[0].contributorAddr
    assert human_resources.confirmNewContributor(aid_b, sender=governance.address)
    addr_b = filter_logs(human_resources, "NewContributorConfirmed")[0].contributorAddr
    a = Contributor.at(addr_a)
    b = Contributor.at(addr_b)
    c_amt = a.compensation()
    travel_to_ts(a.startTime() + 1)
    assert boa.env.evm.patch.timestamp < a.cliffTime()
    p = a.cashRipeCheck(sender=a.owner())
    assert p > 0
    assert ledger.hrReservedCompensation() == c_amt + b.compensation()

    budget_before = ledger.ripeAvailForHr()
    aid_max = switchboard_delta.setRipeAvailableForHr(MAX_UINT256, sender=governance.address)
    travel_to_block(switchboard_delta.getActionConfirmationBlock(aid_max))
    with boa.reverts("exceeds hr budget headroom"):
        switchboard_delta.executePendingAction(aid_max, sender=governance.address)
    assert ledger.ripeAvailForHr() == budget_before

    gap_write = MAX_UINT256 - (c_amt - p)
    aid_gap = switchboard_delta.setRipeAvailableForHr(gap_write, sender=governance.address)
    travel_to_block(switchboard_delta.getActionConfirmationBlock(aid_gap))
    with boa.reverts("exceeds hr budget headroom"):
        switchboard_delta.executePendingAction(aid_gap, sender=governance.address)

    legal = MAX_UINT256 - (c_amt + b.compensation())
    official_delta_budget(switchboard_delta, governance, legal)
    assert ledger.ripeAvailForHr() == legal
    budget_pre_cancel = ledger.ripeAvailForHr()
    _, ok = official_delta_cancel(switchboard_delta, governance, a)
    assert ok is True
    assert a.compensation() == 0
    assert ledger.ripeAvailForHr() == budget_pre_cancel + c_amt
    assert ledger.hrReservedCompensation() == b.compensation()
