"""Group 11 (Claude) never-skip #3 -- cancel paycheck: production Delta path,
the spoof priced separately, burn/refund conservation, residue isolation, and the
frozen-vs-unfrozen after-cliff comparison."""

import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS
from conf_utils import assert_reverted_call, filter_logs

from g11_claude_helpers import (
    make_contributor,
    position,
    terms,
    travel_to,
)


def _mk(hr, mc, sbd, tpl, ledger, gov_, **over):
    return make_contributor(hr, mc, sbd, tpl, ledger, gov_, terms(**over))


def _delta_cancel(switchboard_delta, governance, c):
    """The production cancel: Delta governor initiate + Delta timelock + execute."""
    aid = switchboard_delta.cancelPaycheckForContributor(c.address, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.canConfirmAction(aid)
    return aid


def _delta_cancel_matured_at(switchboard_delta, governance, c, target_ts):
    """Land a *confirmable* Delta cancel exactly at `target_ts`.

    Delta actions expire at `confirmBlock + expiration` (MAX_HQ_CHANGE_TIMELOCK
    blocks here), so a long time-travel to a distant vest boundary must happen
    BEFORE the action is initiated, not after.
    """
    tl = switchboard_delta.actionTimeLock()
    travel_to(target_ts - 12 * tl - 240)
    aid = switchboard_delta.cancelPaycheckForContributor(c.address, sender=governance.address)
    boa.env.time_travel(blocks=tl)
    travel_to(target_ts)
    assert switchboard_delta.canConfirmAction(aid)
    return aid


# ------------------------------------------------------- production vs spoof


def test_g11c_production_delta_cancel_vs_switchboard_address_spoof(
    human_resources, mission_control, switchboard_delta, switchboard_alpha,
    contributor_template, ledger, governance, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, alice, bob,
):
    """Delta gov+timelock+execute is the only production cancel. Alpha has no
    Contributor extcall -- `sender=switchboard_alpha.address` is address impersonation."""
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    comp = c.compensation()
    avail = ledger.ripeAvailForHr()

    travel_to(c.startTime() + 10)
    assert boa.env.evm.patch.timestamp < c.cliffTime()

    aid = _delta_cancel(switchboard_delta, governance, c)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    ev = filter_logs(switchboard_delta, "HrContributorCancelPaycheckSet")
    assert len(ev) == 1 and ev[0].contributor == c.address

    assert c.compensation() == 0
    assert c.endTime() == boa.env.evm.patch.timestamp
    assert ledger.ripeAvailForHr() == avail + comp
    # the Alpha spoof reaches the same gate but is not a production caller
    assert human_resources.canModifyHrContributor(switchboard_alpha.address)
    with boa.reverts("cannot cancel"):
        c.cancelPaycheck(sender=switchboard_alpha.address)


# ------------------------------------------------------------- time windows


def test_g11c_cancel_before_start_full_refund_no_burn_terminal_views_callable(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token, alice, bob,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    comp, avail = c.compensation(), ledger.ripeAvailForHr()
    start, supply = c.startTime(), ripe_token.totalSupply()
    assert boa.env.evm.patch.timestamp < start

    aid = _delta_cancel(switchboard_delta, governance, c)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    ev = filter_logs(switchboard_delta, "RipePaycheckCancelled")
    assert len(ev) == 1 and ev[0].forfeitedAmount == comp and ev[0].didReachCliff is False

    assert c.compensation() == 0
    assert c.endTime() == boa.env.evm.patch.timestamp < start  # endTime now BEFORE startTime
    assert c.unlockTime() > c.endTime()                        # unlockTime is NOT rewritten
    assert ledger.ripeAvailForHr() == avail + comp
    assert ripe_token.totalSupply() == supply  # nothing was ever minted, burn pulled 0
    # no division by (endTime - startTime) -- the compensation==0 guard holds
    assert c.getTotalVested() == 0 and c.getClaimable() == 0 and c.getUnvestedComp() == 0
    travel_to(start + 10_000)
    assert c.getTotalVested() == 0 and c.getClaimable() == 0 and c.getUnvestedComp() == 0

    # second cancel is blocked
    aid2 = _delta_cancel(switchboard_delta, governance, c)
    with pytest.raises(BoaError) as err:
        switchboard_delta.executePendingAction(aid2, sender=governance.address)
    assert_reverted_call(err.value, "cannot cancel", switchboard_delta)


def test_g11c_cancel_after_start_before_cliff_with_no_prior_cash(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token, alice, bob,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    comp, avail = c.compensation(), ledger.ripeAvailForHr()
    travel_to(c.startTime() + (c.cliffTime() - c.startTime()) // 2)
    assert c.getTotalVested() > 0          # vested even before the cliff
    assert c.totalClaimed() == 0
    supply = ripe_token.totalSupply()

    aid = _delta_cancel(switchboard_delta, governance, c)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    # full original compensation refunded, nothing minted, nothing burned
    assert ledger.ripeAvailForHr() == avail + comp
    assert ripe_token.totalSupply() == supply
    assert c.compensation() == 0 and c.totalClaimed() == 0
    assert position(ripe_gov_vault, c, ripe_token) == 0


def test_g11c_pre_cliff_cancel_after_a_cash_refunds_full_original_and_burns_the_position(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token, alice, bob,
):
    """The specified 'fully forfeitable' pairing, measured on all four quantities."""
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    comp, avail = c.compensation(), ledger.ripeAvailForHr()
    travel_to(c.startTime() + (c.cliffTime() - c.startTime()) // 2)
    cashed = c.cashRipeCheck(sender=alice)
    assert cashed > 0
    supply_after_cash = ripe_token.totalSupply()
    assert position(ripe_gov_vault, c, ripe_token) == cashed

    aid = _delta_cancel(switchboard_delta, governance, c)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)

    assert c.compensation() == 0
    assert c.totalClaimed() == cashed                    # NOT rolled back
    assert position(ripe_gov_vault, c, ripe_token) == 0  # burned
    assert ripe_token.totalSupply() == supply_after_cash - cashed
    assert ledger.ripeAvailForHr() == avail + comp       # full ORIGINAL compensation
    assert ripe_token.balanceOf(human_resources) == 0
    assert ripe_token.balanceOf(alice) == 0
    # 'transferred already, then pre-cliff cancel' is unreachable: cliff <= unlock
    assert c.cliffTime() <= c.unlockTime()


def test_g11c_residue_isolation_pre_cliff_burn_destroys_third_party_ripe(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, setUserConfig,
    ripe_gov_vault, ripe_token, teller, whale, alice, bob, sally,
):
    """`withdrawContributorTokensToBurn` pulls the clone's ENTIRE RipeGov position.
    Any non-paycheck RIPE parked on the clone is burned too, while the refund only
    credits the paycheck compensation."""
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    comp, avail = c.compensation(), ledger.ripeAvailForHr()
    vault_id = mission_control.coreRipeGovVaultId()

    residue = 1_234 * EIGHTEEN_DECIMALS
    ripe_token.transfer(sally, residue, sender=whale)
    ripe_token.approve(teller, residue, sender=sally)

    # a fresh clone's userConfig defaults to canAnyoneDeposit == False
    with boa.reverts("cannot deposit for user"):
        teller.deposit(ripe_token, residue, c.address, ZERO_ADDRESS, vault_id, sender=sally)

    # production route for this flip is Charlie setUserConfig (governor + timelock);
    # any Ripe department deposit for the clone (bond recipient, loot auto-stake)
    # reaches the same state without it.
    setUserConfig(c.address, _canAnyoneDeposit=True)
    teller.deposit(ripe_token, residue, c.address, ZERO_ADDRESS, vault_id, sender=sally)
    assert position(ripe_gov_vault, c, ripe_token) == residue

    travel_to(c.startTime() + (c.cliffTime() - c.startTime()) // 2)
    paycheck = c.cashRipeCheck(sender=alice)
    assert paycheck > 0
    assert position(ripe_gov_vault, c, ripe_token) == residue + paycheck
    supply = ripe_token.totalSupply()

    aid = _delta_cancel(switchboard_delta, governance, c)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)

    # B + P destroyed; only `compensation` credited back to the HR budget
    assert position(ripe_gov_vault, c, ripe_token) == 0
    assert ripe_token.totalSupply() == supply - (residue + paycheck)
    assert ledger.ripeAvailForHr() == avail + comp
    assert ripe_token.balanceOf(sally) == 0          # sally's RIPE is gone
    assert ripe_token.balanceOf(c) == 0
    assert ripe_token.balanceOf(human_resources) == 0


def test_g11c_plain_erc20_on_the_clone_is_not_pulled_by_the_burn(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token,
    whale, alice, bob,
):
    """Adjacent control for the residue case: the burn is a VAULT pull, not balanceOf."""
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    stray = 77 * EIGHTEEN_DECIMALS
    ripe_token.transfer(c.address, stray, sender=whale)
    travel_to(c.startTime() + 10)
    supply = ripe_token.totalSupply()

    aid = _delta_cancel(switchboard_delta, governance, c)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert ripe_token.balanceOf(c) == stray       # untouched
    assert ripe_token.totalSupply() == supply


def test_g11c_cancel_at_exact_cliff_cashes_then_refunds_remainder_without_burning(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token, alice, bob,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    comp, avail = c.compensation(), ledger.ripeAvailForHr()

    aid = _delta_cancel_matured_at(switchboard_delta, governance, c, c.cliffTime())
    assert boa.env.evm.patch.timestamp == c.cliffTime()
    vested = c.getTotalVested()
    supply = ripe_token.totalSupply()

    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    ev = filter_logs(switchboard_delta, "RipePaycheckCancelled")
    assert len(ev) == 1 and ev[0].didReachCliff is True
    cash_ev = filter_logs(switchboard_delta, "RipeCheckCashed")
    assert len(cash_ev) == 1
    assert cash_ev[0].cashedBy == human_resources.address  # NOT the canceller
    assert cash_ev[0].owner == alice

    assert c.totalClaimed() == vested
    assert c.compensation() == vested
    assert ev[0].forfeitedAmount == comp - vested
    assert ledger.ripeAvailForHr() == avail + (comp - vested)
    assert ripe_token.totalSupply() == supply + vested       # minted, NOT burned
    assert position(ripe_gov_vault, c, ripe_token) == vested


def test_g11c_after_cliff_cancel_keeps_the_cashed_position_and_the_original_unlock(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token, alice, bob,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    comp, avail = c.compensation(), ledger.ripeAvailForHr()
    unlock_ts = c.unlockTime()
    travel_to(c.cliffTime() + 30 * 24 * 3600)
    early = c.cashRipeCheck(sender=alice)
    assert early > 0

    aid = _delta_cancel(switchboard_delta, governance, c)
    supply = ripe_token.totalSupply()
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)

    claimed = c.totalClaimed()
    assert claimed > early                                  # cash-first topped up
    assert ripe_token.totalSupply() == supply + (claimed - early)
    assert position(ripe_gov_vault, c, ripe_token) == claimed   # NOT burned
    assert c.compensation() == claimed
    assert ledger.ripeAvailForHr() == avail + (comp - claimed)
    assert c.unlockTime() == unlock_ts                      # cancel never rewrites unlock
    assert c.endTime() == boa.env.evm.patch.timestamp

    # exit is still the ordinary two-step, still gated on the ORIGINAL unlockTime
    with boa.reverts("time not past unlock"):
        c.initiateRipeTransfer(False, sender=alice)
    travel_to(unlock_ts + 1)
    c.initiateRipeTransfer(False, sender=alice)
    boa.env.time_travel(blocks=c.keyActionDelay())
    c.confirmRipeTransfer(False, sender=alice)
    assert position(ripe_gov_vault, alice, ripe_token) == claimed
    assert position(ripe_gov_vault, c, ripe_token) == 0


def test_g11c_cancel_at_exact_end_and_after_end_revert_with_no_refund(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_token, alice, bob,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    avail = ledger.ripeAvailForHr()
    aid = _delta_cancel_matured_at(switchboard_delta, governance, c, c.endTime())
    assert boa.env.evm.patch.timestamp == c.endTime()
    with pytest.raises(BoaError) as err:
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert_reverted_call(err.value, "cannot cancel", switchboard_delta)
    assert ledger.ripeAvailForHr() == avail

    travel_to(c.endTime() + 1_000)
    assert switchboard_delta.canConfirmAction(aid)
    with pytest.raises(BoaError):
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert ledger.ripeAvailForHr() == avail
    assert c.compensation() > 0


# ------------------------------------------------- frozen vs unfrozen after cliff


def test_g11c_frozen_after_cliff_cancel_forfeits_vested_but_uncashed_ripe(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token,
    alice, bob, sally,
):
    """Same terms, same vest point, same cancel -- once frozen and once not.
    The delta is exactly the contributor's vested-but-uncashed balance."""
    setupRipeGovVaultConfig()
    t_free = terms(owner=alice, manager=bob)
    t_frozen = terms(owner=sally, manager=bob)
    c_free = make_contributor(human_resources, mission_control, switchboard_delta,
                              contributor_template, ledger, governance, t_free)
    c_frozen = make_contributor(human_resources, mission_control, switchboard_delta,
                                contributor_template, ledger, governance, t_frozen)
    comp = c_free.compensation()
    assert c_frozen.compensation() == comp

    travel_to(max(c_free.cliffTime(), c_frozen.cliffTime()) + 45 * 24 * 3600)
    assert c_free.getTotalVested() > 0 and c_frozen.getTotalVested() > 0
    assert c_free.totalClaimed() == c_frozen.totalClaimed() == 0

    switchboard_delta.freezeContributor(c_frozen.address, True, sender=governance.address)
    aid_a = switchboard_delta.cancelPaycheckForContributor(c_free.address, sender=governance.address)
    aid_b = switchboard_delta.cancelPaycheckForContributor(c_frozen.address, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    vested_frozen = c_frozen.getTotalVested()
    assert vested_frozen > 0

    supply0, avail0 = ripe_token.totalSupply(), ledger.ripeAvailForHr()
    assert switchboard_delta.executePendingAction(aid_a, sender=governance.address)
    free_claimed = c_free.totalClaimed()
    free_pos = position(ripe_gov_vault, c_free, ripe_token)
    free_supply_delta = ripe_token.totalSupply() - supply0
    free_avail_delta = ledger.ripeAvailForHr() - avail0

    supply1, avail1 = ripe_token.totalSupply(), ledger.ripeAvailForHr()
    assert switchboard_delta.executePendingAction(aid_b, sender=governance.address)
    frozen_claimed = c_frozen.totalClaimed()
    frozen_pos = position(ripe_gov_vault, c_frozen, ripe_token)
    frozen_supply_delta = ripe_token.totalSupply() - supply1
    frozen_avail_delta = ledger.ripeAvailForHr() - avail1

    # unfrozen: vested minted onto the clone, only the unvested remainder refunded
    assert free_claimed > 0 and free_pos == free_claimed
    assert free_supply_delta == free_claimed
    assert free_avail_delta == comp - free_claimed
    assert c_free.compensation() == free_claimed

    # frozen: cash returned 0, nothing minted, the WHOLE compensation refunded
    assert frozen_claimed == 0 and frozen_pos == 0
    assert frozen_supply_delta == 0
    assert frozen_avail_delta == comp
    assert c_frozen.compensation() == 0
    assert filter_logs(c_frozen, "RipeCheckCashed") == []

    # the forfeiture is exactly the frozen clone's vested-but-uncashed balance
    assert frozen_avail_delta == comp
    assert free_avail_delta == comp - free_claimed
    assert frozen_avail_delta - (comp - vested_frozen) == vested_frozen

    # neither cancel burned: shouldBurn is False for BOTH (post-cliff)
    evs = filter_logs(switchboard_delta, "RipePaycheckCancelled")
    assert len(evs) == 1 and evs[0].didReachCliff is True


def test_g11c_official_pause_rolls_back_a_mature_delta_cancel_and_it_re_executes(
    human_resources, mission_control, switchboard_delta, switchboard_charlie,
    contributor_template, ledger, governance, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, alice, bob,
):
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    comp, avail = c.compensation(), ledger.ripeAvailForHr()
    end_before = c.endTime()
    travel_to(c.startTime() + 10)

    aid = _delta_cancel(switchboard_delta, governance, c)
    assert switchboard_delta.hasPendingAction(aid)

    assert switchboard_charlie.pause(human_resources.address, True, sender=governance.address)
    with pytest.raises(BoaError) as err:
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert_reverted_call(err.value, "contract paused", switchboard_delta)

    # everything rolled back
    assert c.compensation() == comp
    assert c.endTime() == end_before
    assert ledger.ripeAvailForHr() == avail
    assert switchboard_delta.hasPendingAction(aid)

    assert switchboard_charlie.pause(human_resources.address, False, sender=governance.address)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert c.compensation() == 0
    assert ledger.ripeAvailForHr() == avail + comp
    assert not switchboard_delta.hasPendingAction(aid)
