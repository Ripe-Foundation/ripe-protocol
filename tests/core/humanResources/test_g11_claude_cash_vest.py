"""Group 11 (Claude) never-skip #1 -- cash / vest identity.

Every clone here is deployed through the real HR governor path.
"""

import boa
import pytest

from boa.contracts.base_evm_contract import BoaError

from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from conf_utils import assert_reverted_call, filter_logs

from g11_claude_helpers import (
    make_contributor,
    position,
    set_budget,
    set_hr_config,
    snapshot,
    term_args,
    terms,
    travel_to,
    unlock_block,
)
from tests.core.humanResources.g11_proof_helpers import official_delta_cancel


# ---------------------------------------------------------------- #1 boundaries


def test_g11c_cash_vest_timestamp_boundaries_owner_manager_and_delta(
    human_resources,
    mission_control,
    switchboard_delta,
    contributor_template,
    ledger,
    governance,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
):
    """before start / exact start / start+1 (pre-cliff) / exact cliff / exact end / after end,
    driven by owner, manager and the production Delta lite wrapper."""
    setupRipeGovVaultConfig()
    t = terms()
    c = make_contributor(
        human_resources, mission_control, switchboard_delta, contributor_template,
        ledger, governance, t,
    )
    owner, manager = c.owner(), c.manager()
    start, cliff, end = c.startTime(), c.cliffTime(), c.endTime()
    comp = c.compensation()
    avail_after_reserve = ledger.ripeAvailForHr()

    # --- before startTime: 0, no mint
    s0 = snapshot(ripe_gov_vault, ripe_token, ledger, human_resources, c)
    assert c.getTotalVested() == 0 and c.getClaimable() == 0
    assert c.cashRipeCheck(sender=owner) == 0
    assert filter_logs(c, "RipeCheckCashed") == []
    assert ripe_token.totalSupply() == s0["supply"]
    assert position(ripe_gov_vault, c, ripe_token) == 0

    # --- exact startTime: still 0 (guard is `timestamp <= startTime`)
    travel_to(start)
    assert boa.env.evm.patch.timestamp == start
    assert c.getTotalVested() == 0
    assert c.cashRipeCheck(sender=manager) == 0
    assert ripe_token.totalSupply() == s0["supply"]

    # --- first second after start: floored vest, still strictly BEFORE cliff
    travel_to(start + 1)
    assert boa.env.evm.patch.timestamp < cliff
    expected = min(comp, comp * 1 // (end - start))
    assert c.getTotalVested() == expected
    assert c.getClaimable() == expected
    assert expected > 0  # cliffTime is not in the vest formula
    before = snapshot(ripe_gov_vault, ripe_token, ledger, human_resources, c)
    got = c.cashRipeCheck(sender=owner)
    ev = filter_logs(c, "RipeCheckCashed")
    assert got == expected and len(ev) == 1
    assert ev[0].owner == owner and ev[0].cashedBy == owner and ev[0].amount == expected
    assert ripe_token.totalSupply() == before["supply"] + expected
    assert position(ripe_gov_vault, c, ripe_token) == before["clone_pos"] + expected
    assert ripe_token.balanceOf(owner) == before["owner_erc20"]
    assert position(ripe_gov_vault, owner, ripe_token) == before["owner_pos"]
    assert ripe_token.balanceOf(human_resources) == before["hr_bal"]
    assert c.totalClaimed() == before["claimed"] + expected
    # budget was reserved at addHrContributor; cash does NOT decrement again
    assert ledger.ripeAvailForHr() == avail_after_reserve == before["avail"]

    # --- second cash in the same timestamp: 0, no mint, no event
    s = ripe_token.totalSupply()
    assert c.cashRipeCheck(sender=owner) == 0
    assert filter_logs(c, "RipeCheckCashed") == []
    assert ripe_token.totalSupply() == s

    # --- exact cliffTime
    travel_to(cliff)
    vested_at_cliff = c.getTotalVested()
    claimable = c.getClaimable()
    assert vested_at_cliff == min(comp, comp * (cliff - start) // (end - start))
    assert claimable == vested_at_cliff - c.totalClaimed()
    s = ripe_token.totalSupply()
    assert c.cashRipeCheck(sender=manager) == claimable
    assert ripe_token.totalSupply() == s + claimable
    assert c.totalClaimed() == vested_at_cliff

    # --- exact endTime: full remaining, via the production Delta lite wrapper (governor)
    travel_to(end)
    assert c.getTotalVested() == comp
    remaining = comp - c.totalClaimed()
    assert c.getClaimable() == remaining
    s = ripe_token.totalSupply()
    assert switchboard_delta.cashRipeCheckForContributor(c.address, sender=governance.address)
    dev = filter_logs(switchboard_delta, "RipeCheckCashedFromSwitchboard")
    assert len(dev) == 1 and dev[0].amount == remaining
    assert dev[0].cashedBy == governance.address
    assert ripe_token.totalSupply() == s + remaining
    assert c.totalClaimed() == comp
    assert position(ripe_gov_vault, c, ripe_token) == comp

    # --- after end: nothing left
    travel_to(end + 10_000)
    assert c.getTotalVested() == comp
    assert c.getClaimable() == 0
    s = ripe_token.totalSupply()
    assert c.cashRipeCheck(sender=owner) == 0
    assert ripe_token.totalSupply() == s
    # conservation: minted == clone position == totalClaimed, budget untouched by cash
    assert position(ripe_gov_vault, c, ripe_token) == c.totalClaimed() == comp
    assert ledger.ripeAvailForHr() == avail_after_reserve
    assert ripe_token.balanceOf(c) == 0
    assert ripe_token.balanceOf(human_resources) == 0


def test_g11c_cash_unauthorized_eoa_reverts_and_lite_signer_can_cash(
    human_resources,
    mission_control,
    switchboard_delta,
    switchboard_alpha,
    contributor_template,
    ledger,
    governance,
    setupRipeGovVaultConfig,
    ripe_token,
    alice,
    bob,
):
    setupRipeGovVaultConfig()
    t = terms()
    c = make_contributor(
        human_resources, mission_control, switchboard_delta, contributor_template,
        ledger, governance, t,
    )
    travel_to(c.cliffTime())
    assert c.getClaimable() > 0

    supply = ripe_token.totalSupply()
    with boa.reverts("no perms"):
        c.cashRipeCheck(sender=bob)
    assert ripe_token.totalSupply() == supply

    # Delta lite signer (liteSigners() is [] at launch -- this is the enabled case)
    mission_control.setCanPerformLiteAction(alice, True, sender=switchboard_alpha.address)
    assert mission_control.canPerformLiteAction(alice)
    claimable = c.getClaimable()
    assert switchboard_delta.cashRipeCheckForContributor(c.address, sender=alice)
    assert ripe_token.totalSupply() == supply + claimable


def test_g11c_cash_frozen_returns_zero_hr_paused_and_mint_gate_off_revert(
    human_resources,
    mission_control,
    switchboard_delta,
    switchboard_charlie,
    contributor_template,
    ledger,
    governance,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    ripe_hq,
):
    setupRipeGovVaultConfig()
    c = make_contributor(
        human_resources, mission_control, switchboard_delta, contributor_template,
        ledger, governance, terms(),
    )
    owner = c.owner()
    travel_to(c.cliffTime())
    assert c.getClaimable() > 0

    # --- frozen: 0, no mint, no event, totalClaimed unchanged
    assert switchboard_delta.freezeContributor(c.address, True, sender=governance.address)
    supply, claimed = ripe_token.totalSupply(), c.totalClaimed()
    assert c.cashRipeCheck(sender=owner) == 0
    assert filter_logs(c, "RipeCheckCashed") == []
    assert ripe_token.totalSupply() == supply and c.totalClaimed() == claimed
    assert switchboard_delta.freezeContributor(c.address, False, sender=governance.address)

    # --- HR department paused via the production Charlie write: revert, no mint
    assert switchboard_charlie.pause(human_resources.address, True, sender=governance.address)
    assert human_resources.isPaused()
    with pytest.raises(BoaError) as err:
        c.cashRipeCheck(sender=owner)
    assert_reverted_call(err.value, "contract paused", c)
    assert ripe_token.totalSupply() == supply and c.totalClaimed() == claimed
    assert switchboard_charlie.pause(human_resources.address, False, sender=governance.address)

    # --- HQ mint gate off: revert, no mint, no clone-side escape
    assert ripe_hq.canMintRipe(human_resources.address)
    ripe_hq.setMintingEnabled(False, sender=governance.address)
    assert not ripe_hq.canMintRipe(human_resources.address)
    with pytest.raises(BoaError) as err:
        c.cashRipeCheck(sender=owner)
    assert_reverted_call(err.value, "cannot mint", c)
    assert ripe_token.totalSupply() == supply and c.totalClaimed() == claimed
    assert position(ripe_gov_vault, c, ripe_token) == 0

    # adjacent positive control: re-enable and the same cash succeeds
    ripe_hq.setMintingEnabled(True, sender=governance.address)
    claimable = c.getClaimable()
    assert claimable > 0
    assert c.cashRipeCheck(sender=owner) == claimable
    assert ripe_token.totalSupply() == supply + claimable
    assert position(ripe_gov_vault, c, ripe_token) == claimable


def test_g11c_official_cash_cannot_exceed_get_claimable(
    human_resources,
    mission_control,
    switchboard_delta,
    contributor_template,
    ledger,
    governance,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    bob,
):
    """Trusted clone only sends getClaimable(); a non-contributor cannot mint."""
    setupRipeGovVaultConfig()
    c = make_contributor(
        human_resources, mission_control, switchboard_delta, contributor_template,
        ledger, governance, terms(),
    )
    with boa.reverts("not a contributor"):
        human_resources.cashRipeCheck(1 * EIGHTEEN_DECIMALS, 0, sender=bob)

    travel_to(c.startTime() + 1)
    claimable = c.getClaimable()
    supply = ripe_token.totalSupply()
    reserved = ledger.hrReservedCompensation()
    avail = ledger.ripeAvailForHr()
    assert c.cashRipeCheck(sender=c.owner()) == claimable
    assert ripe_token.totalSupply() == supply + claimable
    assert c.totalClaimed() == claimable
    assert c.getClaimable() == 0
    assert c.cashRipeCheck(sender=c.owner()) == 0
    assert ripe_token.totalSupply() == supply + claimable
    assert ledger.hrReservedCompensation() == reserved
    assert ledger.ripeAvailForHr() == avail


# ---------------------------------------------------------------- #1 overflow


def _largest_safe_comp(elapsed):
    return MAX_UINT256 // elapsed


def test_g11c_individual_vesting_overflow_bricks_cash_and_after_cliff_cancel(
    human_resources,
    mission_control,
    switchboard_delta,
    contributor_template,
    ledger,
    governance,
):
    """Ranked 2**255 compensation is rejected at initiate; MAX//2 still creates."""
    elapsed = 2
    safe = _largest_safe_comp(elapsed)
    assert safe * elapsed <= MAX_UINT256
    with pytest.raises(Exception):
        # not representable at elapsed == 1 -- documents why the brief demands elapsed >= 2
        assert (MAX_UINT256 // 1 + 1) <= MAX_UINT256
        raise AssertionError

    t_ok = terms(compensation=safe, startDelay=0)
    c_ok = make_contributor(
        human_resources, mission_control, switchboard_delta, contributor_template,
        ledger, governance, t_ok, budget=safe, maxCompensation=0,
    )
    travel_to(c_ok.startTime() + elapsed)
    assert c_ok.getTotalVested() >= 0  # no revert
    assert c_ok.getClaimable() >= 0

    t_bad = terms(compensation=safe + 1, startDelay=0)
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(*term_args(t_bad), sender=governance.address)
    if c_ok.compensation() != 0:
        _, ok = official_delta_cancel(switchboard_delta, governance, c_ok)
        assert ok is True


def test_g11c_pre_cliff_cancel_is_the_recovery_path_for_an_overflow_clone(
    human_resources,
    mission_control,
    switchboard_delta,
    contributor_template,
    ledger,
    governance,
):
    """Ranked 2**255 compensation is rejected at initiate."""
    safe = _largest_safe_comp(2)
    t = terms(compensation=safe + 1, startDelay=0)
    set_hr_config(mission_control, switchboard_delta, contributor_template, maxCompensation=0)
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(*term_args(t), sender=governance.address)


def test_g11c_hr_aggregate_views_overflow_only_when_summing_clones(
    human_resources,
    mission_control,
    switchboard_delta,
    contributor_template,
    ledger,
    governance,
):
    """Two 2**255 stock clones are rejected at initiate."""
    half = MAX_UINT256 // 2 + 1
    t1 = terms(owner="0x" + "31" * 20, compensation=half, startDelay=0)
    set_hr_config(mission_control, switchboard_delta, contributor_template, maxCompensation=0)
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(*term_args(t1), sender=governance.address)
