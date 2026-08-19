"""Group 11 (Claude) never-skip #5 (part 1) -- terms validation, budget, create,
HR-vs-Delta timelock semantics, and the create-time pause surfaces."""

import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS
from conf_utils import assert_reverted_call, filter_logs
from contracts.modules import Contributor

from g11_claude_helpers import (
    make_contributor,
    position,
    set_budget,
    set_hr_config,
    term_args,
    terms,
    travel_to,
)
from tests.core.humanResources.g11_proof_helpers import release_live_hr_reserve

BLOCK_DELTA = 12


def _valid(human_resources, t):
    return human_resources.areValidContributorTerms(*term_args(t))


# --------------------------------------------------------------- validation


def test_g11c_terms_validation_rejects_documented_zeros_and_orderings(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob,
):
    set_hr_config(mission_control, switchboard_delta, contributor_template)
    base = terms(owner=alice, manager=bob)
    set_budget(ledger, switchboard_delta, base["compensation"])
    assert _valid(human_resources, base)

    assert not _valid(human_resources, terms(**{**base, "compensation": 0}))
    assert not _valid(human_resources, terms(**{**base, "cliffLength": 0}))
    assert not _valid(human_resources, terms(**{**base, "owner": ZERO_ADDRESS}))
    assert not _valid(human_resources, terms(**{**base, "manager": ZERO_ADDRESS}))
    # unlock > vesting
    assert not _valid(human_resources, terms(**{**base, "unlockLength": base["vestingLength"] + 1}))
    # cliff > unlock
    assert not _valid(human_resources, terms(**{
        **base, "cliffLength": base["unlockLength"] + 1,
    }))
    # compensation > ripeAvailForHr
    assert not _valid(human_resources, terms(**{**base, "compensation": base["compensation"] + 1}))
    # bounds from hrConfig
    assert not _valid(human_resources, terms(**{**base, "cliffLength": 29 * 24 * 3600}))
    assert not _valid(human_resources, terms(**{**base, "vestingLength": 364 * 24 * 3600}))
    assert not _valid(human_resources, terms(**{**base, "startDelay": 91 * 24 * 3600}))
    # zero vestingLength is rejected by both the vesting-zero and the min-vesting rule
    assert not _valid(human_resources, terms(**{
        **base, "vestingLength": 0, "unlockLength": 0, "cliffLength": 0,
    }))
    # empty template
    set_hr_config(mission_control, switchboard_delta, contributor_template,
                  contribTemplate=ZERO_ADDRESS)
    assert not _valid(human_resources, base)
    set_hr_config(mission_control, switchboard_delta, contributor_template)

    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(
            *term_args(terms(**{**base, "compensation": 0})), sender=governance.address
        )
    # owner == manager is fine; the validator rejects empty, not equality
    assert _valid(human_resources, terms(**{**base, "manager": alice}))


def test_g11c_deposit_lock_duration_acceptance_set_is_completely_unchecked(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob,
):
    """{0, below min, exact min, exact max, max+1} validate and construct.
    Overflow-sized D is rejected at initiate."""
    set_hr_config(mission_control, switchboard_delta, contributor_template)
    base = terms(owner=alice, manager=bob)
    set_budget(ledger, switchboard_delta, base["compensation"])
    for d in (0, 50, 100, 1_000, 1_001):
        assert _valid(human_resources, terms(**{**base, "depositLockDuration": d})), d
    assert not _valid(human_resources, terms(**{**base, "depositLockDuration": MAX_UINT256}))

    c = make_contributor(
        human_resources, mission_control, switchboard_delta, contributor_template,
        ledger, governance, terms(**{**base, "depositLockDuration": 0}),
    )
    assert c.depositLockDuration() == 0
    assert not hasattr(c, "setDepositLockDuration")
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(
            *term_args(terms(**{**base, "depositLockDuration": MAX_UINT256})),
            sender=governance.address,
        )


# ------------------------------------------------------------ budget / create


def test_g11c_two_overlapping_pendings_second_confirm_returns_false_and_leaves_no_clone(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob, sally,
):
    set_hr_config(mission_control, switchboard_delta, contributor_template)
    comp = 500_000 * EIGHTEEN_DECIMALS
    set_budget(ledger, switchboard_delta, comp)
    t1 = terms(owner=alice, manager=bob, compensation=comp)
    t2 = terms(owner=sally, manager=bob, compensation=comp)

    aid1 = human_resources.initiateNewContributor(*term_args(t1), sender=governance.address)
    aid2 = human_resources.initiateNewContributor(*term_args(t2), sender=governance.address)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())

    n_before = ledger.numContributors()
    assert human_resources.confirmNewContributor(aid1, sender=governance.address)
    assert ledger.ripeAvailForHr() == 0
    assert ledger.numContributors() == max(n_before, 1) + 1

    n_mid = ledger.numContributors()
    assert human_resources.confirmNewContributor(aid2, sender=governance.address) is False
    assert ledger.numContributors() == n_mid            # no extra clone
    assert ledger.ripeAvailForHr() == 0                 # no over-reservation
    assert human_resources.pendingContributor(aid2).owner == ZERO_ADDRESS
    assert not human_resources.hasPendingAction(aid2)
    # the False path emits NEITHER event
    assert filter_logs(human_resources, "NewContributorConfirmed") == []
    assert filter_logs(human_resources, "NewContributorCancelled") == []


def test_g11c_real_delta_budget_overwrite_between_initiate_and_confirm_fails_closed(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob,
):
    set_hr_config(mission_control, switchboard_delta, contributor_template)
    comp = 500_000 * EIGHTEEN_DECIMALS
    set_budget(ledger, switchboard_delta, comp)
    t = terms(owner=alice, manager=bob, compensation=comp)

    aid_hr = human_resources.initiateNewContributor(*term_args(t), sender=governance.address)
    aid_d = switchboard_delta.setRipeAvailableForHr(0, sender=governance.address)
    boa.env.time_travel(blocks=max(human_resources.actionTimeLock(),
                                   switchboard_delta.actionTimeLock()))
    assert switchboard_delta.executePendingAction(aid_d, sender=governance.address)
    assert ledger.ripeAvailForHr() == 0

    n_before = ledger.numContributors()
    assert human_resources.confirmNewContributor(aid_hr, sender=governance.address) is False
    assert ledger.numContributors() == n_before
    assert filter_logs(human_resources, "NewContributorConfirmed") == []
    assert filter_logs(human_resources, "NewContributorCancelled") == []
    assert human_resources.pendingContributor(aid_hr).owner == ZERO_ADDRESS


def test_g11c_near_max_budget_overwrite_makes_cancel_revert_and_a_staged_fix_recovers(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_token, alice, bob,
):
    """MAX budget write reverts while cancel-credit liability > 0; a legal write then cancel succeeds."""
    setupRipeGovVaultConfig()
    release_live_hr_reserve(switchboard_delta, governance, ledger)
    c = make_contributor(human_resources, mission_control, switchboard_delta,
                         contributor_template, ledger, governance,
                         terms(owner=alice, manager=bob))
    comp = c.compensation()
    travel_to(c.startTime() + 10)  # pre-cliff

    budget_before = ledger.ripeAvailForHr()
    aid_hi = switchboard_delta.setRipeAvailableForHr(MAX_UINT256, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    with pytest.raises(BoaError):
        switchboard_delta.executePendingAction(aid_hi, sender=governance.address)
    assert ledger.ripeAvailForHr() == budget_before
    assert switchboard_delta.hasPendingAction(aid_hi)

    aid_fix = switchboard_delta.setRipeAvailableForHr(
        MAX_UINT256 - ledger.hrReservedCompensation(), sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(aid_fix, sender=governance.address)
    aid_cancel = switchboard_delta.cancelPaycheckForContributor(c.address, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(aid_cancel, sender=governance.address)
    assert c.compensation() == 0
    assert ledger.hrReservedCompensation() == 0
    assert ledger.ripeAvailForHr() == MAX_UINT256


def test_g11c_max_compensation_zero_does_not_cap_create(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob,
):
    """Launch DefaultsRobinhood ships `maxCompensation = 0` (= unlimited)."""
    huge = 10**30
    c = make_contributor(human_resources, mission_control, switchboard_delta,
                         contributor_template, ledger, governance,
                         terms(owner=alice, manager=bob, compensation=huge),
                         budget=huge, maxCompensation=0)
    assert c.compensation() == huge


# ------------------------------------------------- maxStartDelay = 0 arithmetic


def test_g11c_max_start_delay_zero_constructor_arithmetic_boundary(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob,
):
    """startDelay = uint256.max is rejected at initiate even when maxStartDelay is 0."""
    set_hr_config(mission_control, switchboard_delta, contributor_template, maxStartDelay=0)
    comp = 500_000 * EIGHTEEN_DECIMALS
    set_budget(ledger, switchboard_delta, comp)
    tl = human_resources.actionTimeLock()
    vesting = terms()["vestingLength"]

    # predicted confirm timestamp (boa advances 12s per block)
    ts_confirm = boa.env.evm.patch.timestamp + BLOCK_DELTA * tl
    boundary = MAX_UINT256 - ts_confirm - vesting

    worst = terms(owner=alice, manager=bob, compensation=comp, startDelay=MAX_UINT256)
    assert not _valid(human_resources, worst)
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(*term_args(worst), sender=governance.address)

    ok = terms(owner=alice, manager=bob, compensation=comp, startDelay=boundary)
    assert _valid(human_resources, ok)
    aid_ok = human_resources.initiateNewContributor(*term_args(ok), sender=governance.address)
    boa.env.time_travel(blocks=tl)
    boa.env.time_travel(seconds=1)
    assert human_resources.confirmNewContributor(aid_ok, sender=governance.address) is False
    assert human_resources.pendingContributor(aid_ok).owner == ZERO_ADDRESS
    assert filter_logs(human_resources, "NewContributorConfirmed") == []
    assert filter_logs(human_resources, "NewContributorCancelled") == []


def test_g11c_enormous_but_representable_start_delay_is_config_liveness_only(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob,
):
    hundred_years = 100 * 365 * 24 * 3600
    c = make_contributor(human_resources, mission_control, switchboard_delta,
                         contributor_template, ledger, governance,
                         terms(owner=alice, manager=bob, startDelay=hundred_years),
                         maxStartDelay=0)
    assert c.getTotalVested() == 0 and c.getClaimable() == 0
    comp, avail = c.compensation(), ledger.ripeAvailForHr()
    # still fully recoverable through the ordinary pre-cliff cancel
    aid = switchboard_delta.cancelPaycheckForContributor(c.address, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert ledger.ripeAvailForHr() == avail + comp


# --------------------------------------------------------- timelock semantics


def test_g11c_hr_timelock_edges_valid_terms_revert_and_leave_the_pending(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob,
):
    set_hr_config(mission_control, switchboard_delta, contributor_template)
    comp = 500_000 * EIGHTEEN_DECIMALS
    set_budget(ledger, switchboard_delta, comp)
    t = terms(owner=alice, manager=bob, compensation=comp)
    tl, exp = human_resources.actionTimeLock(), human_resources.expiration()

    aid = human_resources.initiateNewContributor(*term_args(t), sender=governance.address)
    confirm_block = human_resources.getActionConfirmationBlock(aid)
    assert confirm_block == boa.env.evm.patch.block_number + tl

    boa.env.time_travel(blocks=tl - 1)
    with boa.reverts("time lock not reached"):
        human_resources.confirmNewContributor(aid, sender=governance.address)
    assert human_resources.pendingContributor(aid).owner == alice
    assert human_resources.hasPendingAction(aid)

    # at exact expiration: revert, pending STAYS, and only cancelNewContributor clears it
    boa.env.time_travel(blocks=exp + 1)
    assert boa.env.evm.patch.block_number >= confirm_block + exp
    assert human_resources.isExpired(aid)
    with boa.reverts("time lock not reached"):
        human_resources.confirmNewContributor(aid, sender=governance.address)
    assert human_resources.hasPendingAction(aid)
    assert human_resources.cancelNewContributor(aid, sender=governance.address)
    ev = filter_logs(human_resources, "NewContributorCancelled")
    assert len(ev) == 1 and ev[0].actionId == aid
    assert not human_resources.hasPendingAction(aid)
    assert human_resources.pendingContributor(aid).owner == ZERO_ADDRESS

    # adjacent positive control: exact confirmBlock confirms
    aid2 = human_resources.initiateNewContributor(*term_args(t), sender=governance.address)
    boa.env.time_travel(blocks=tl)
    assert boa.env.evm.patch.block_number == human_resources.getActionConfirmationBlock(aid2)
    assert human_resources.confirmNewContributor(aid2, sender=governance.address)


def test_g11c_hr_stale_terms_return_false_before_confirm_block_and_after_expiration(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob,
):
    """Re-validation runs BEFORE the timelock check, so invalid terms cancel the
    pending and return False at ANY block -- with neither event."""
    set_hr_config(mission_control, switchboard_delta, contributor_template)
    comp = 500_000 * EIGHTEEN_DECIMALS
    set_budget(ledger, switchboard_delta, comp)
    t = terms(owner=alice, manager=bob, compensation=comp)

    aid_early = human_resources.initiateNewContributor(*term_args(t), sender=governance.address)
    set_budget(ledger, switchboard_delta, 0)
    assert boa.env.evm.patch.block_number < human_resources.getActionConfirmationBlock(aid_early)
    assert human_resources.confirmNewContributor(aid_early, sender=governance.address) is False
    assert not human_resources.hasPendingAction(aid_early)
    assert filter_logs(human_resources, "NewContributorConfirmed") == []
    assert filter_logs(human_resources, "NewContributorCancelled") == []

    set_budget(ledger, switchboard_delta, comp)
    aid_late = human_resources.initiateNewContributor(*term_args(t), sender=governance.address)
    boa.env.time_travel(blocks=human_resources.actionTimeLock() + human_resources.expiration() + 1)
    assert human_resources.isExpired(aid_late)
    set_budget(ledger, switchboard_delta, 0)
    assert human_resources.confirmNewContributor(aid_late, sender=governance.address) is False
    assert not human_resources.hasPendingAction(aid_late)


def test_g11c_delta_timelock_edges_return_false_and_expire_clears_the_pending(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob,
):
    c = make_contributor(human_resources, mission_control, switchboard_delta,
                         contributor_template, ledger, governance,
                         terms(owner=alice, manager=bob))
    tl, exp = switchboard_delta.actionTimeLock(), switchboard_delta.expiration()

    aid = switchboard_delta.cancelPaycheckForContributor(c.address, sender=governance.address)
    boa.env.time_travel(blocks=tl - 1)
    # early: False, and the pending is NOT cancelled
    assert switchboard_delta.executePendingAction(aid, sender=governance.address) is False
    assert switchboard_delta.hasPendingAction(aid)

    boa.env.time_travel(blocks=exp + 1)
    assert switchboard_delta.isExpired(aid)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address) is False
    assert not switchboard_delta.hasPendingAction(aid)   # expired -> cleared
    assert c.compensation() > 0


# ----------------------------------------------------------------- pauses


def test_g11c_charlie_pause_blocks_create_initiate_confirm_and_cancel(
    human_resources, mission_control, switchboard_delta, switchboard_charlie,
    contributor_template, ledger, governance, alice, bob,
):
    set_hr_config(mission_control, switchboard_delta, contributor_template)
    comp = 500_000 * EIGHTEEN_DECIMALS
    set_budget(ledger, switchboard_delta, comp)
    t = terms(owner=alice, manager=bob, compensation=comp)
    aid = human_resources.initiateNewContributor(*term_args(t), sender=governance.address)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())

    assert switchboard_charlie.pause(human_resources.address, True, sender=governance.address)
    with boa.reverts("contract paused"):
        human_resources.initiateNewContributor(*term_args(t), sender=governance.address)
    with boa.reverts("contract paused"):
        human_resources.confirmNewContributor(aid, sender=governance.address)
    with boa.reverts("contract paused"):
        human_resources.cancelNewContributor(aid, sender=governance.address)
    assert human_resources.hasPendingAction(aid)

    assert switchboard_charlie.pause(human_resources.address, False, sender=governance.address)
    assert human_resources.confirmNewContributor(aid, sender=governance.address)


def test_g11c_ledger_pause_makes_confirm_revert_atomically_with_no_orphan_clone(
    human_resources, mission_control, switchboard_delta, switchboard_charlie,
    contributor_template, ledger, governance, alice, bob,
):
    """create_from_blueprint runs before addHrContributor; a paused Ledger must take
    the whole transaction with it."""
    set_hr_config(mission_control, switchboard_delta, contributor_template)
    comp = 500_000 * EIGHTEEN_DECIMALS
    set_budget(ledger, switchboard_delta, comp)
    t = terms(owner=alice, manager=bob, compensation=comp)
    aid = human_resources.initiateNewContributor(*term_args(t), sender=governance.address)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())

    n_before = ledger.numContributors()
    avail_before = ledger.ripeAvailForHr()
    assert switchboard_charlie.pause(ledger.address, True, sender=governance.address)
    with pytest.raises(BoaError) as err:
        human_resources.confirmNewContributor(aid, sender=governance.address)
    assert_reverted_call(err.value, "not activated", human_resources)

    assert ledger.numContributors() == n_before          # no contributor-list entry
    assert ledger.ripeAvailForHr() == avail_before       # no budget decrement
    assert human_resources.hasPendingAction(aid)         # HR action not consumed
    assert human_resources.pendingContributor(aid).owner == alice
    assert filter_logs(human_resources, "NewContributorConfirmed") == []

    assert switchboard_charlie.pause(ledger.address, False, sender=governance.address)
    assert human_resources.confirmNewContributor(aid, sender=governance.address)
    assert ledger.ripeAvailForHr() == avail_before - comp


def test_g11c_near_max_budget_also_blocks_an_after_cliff_cancel(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_token, alice, bob,
):
    setupRipeGovVaultConfig()
    release_live_hr_reserve(switchboard_delta, governance, ledger)
    c = make_contributor(human_resources, mission_control, switchboard_delta,
                         contributor_template, ledger, governance,
                         terms(owner=alice, manager=bob))
    travel_to(c.cliffTime() + 24 * 3600)
    budget_before = ledger.ripeAvailForHr()
    aid_hi = switchboard_delta.setRipeAvailableForHr(MAX_UINT256, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    with pytest.raises(BoaError):
        switchboard_delta.executePendingAction(aid_hi, sender=governance.address)
    assert ledger.ripeAvailForHr() == budget_before
    aid_ok = switchboard_delta.setRipeAvailableForHr(
        MAX_UINT256 - ledger.hrReservedCompensation(), sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(aid_ok, sender=governance.address)
    claimed_before = c.totalClaimed()
    orig = c.compensation()
    aid_cancel = switchboard_delta.cancelPaycheckForContributor(c.address, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(aid_cancel, sender=governance.address)
    claimed = c.totalClaimed()
    assert claimed >= claimed_before
    assert ledger.hrReservedCompensation() == claimed
    assert c.compensation() == claimed
