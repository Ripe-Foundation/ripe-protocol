"""Group 11 (Claude) -- remaining never-skip items: nested-deposit rollback,
the Ledger contributor-index convention, terminal-state reachability after each
cancel flavour, and the Delta lite wrappers' missing contributor check."""

import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from conf_utils import assert_reverted_call, filter_logs, get_boa_dev_reasons

from g11_claude_helpers import make_contributor, position, terms, travel_to


def _mk(hr, mc, sbd, tpl, ledger, gov_, **over):
    return make_contributor(hr, mc, sbd, tpl, ledger, gov_, terms(**over))


def test_g11c_nested_teller_failure_rolls_the_whole_cash_back_and_a_later_cash_works(
    human_resources, mission_control, switchboard_delta, switchboard_charlie,
    contributor_template, ledger, governance, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, teller, alice, bob,
):
    """The mint precedes the deposit inside HR.cashRipeCheck. A failure in the nested
    Teller leg must take the mint, the allowance and totalClaimed with it."""
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    travel_to(c.cliffTime())
    assert c.getClaimable() > 0

    supply, claimed = ripe_token.totalSupply(), c.totalClaimed()
    avail = ledger.ripeAvailForHr()

    # MEASURED: pausing Teller does NOT stop HR cash -- `depositFromTrusted` has no
    # `deptBasics.isPaused` guard (unlike `Teller.deposit`). Group 2 owns that gap.
    assert switchboard_charlie.pause(teller.address, True, sender=governance.address)
    assert teller.isPaused()
    probe = c.getClaimable()
    assert c.cashRipeCheck(sender=alice) == probe
    assert switchboard_charlie.pause(teller.address, False, sender=governance.address)
    supply, claimed = ripe_token.totalSupply(), c.totalClaimed()

    # the reachable nested failure is a paused RipeGov vault
    assert switchboard_charlie.pause(ripe_gov_vault.address, True, sender=governance.address)
    travel_to(boa.env.evm.patch.timestamp + 30 * 24 * 3600)
    assert c.getClaimable() > 0
    pos_before = position(ripe_gov_vault, c, ripe_token)
    with pytest.raises(BoaError) as err:
        c.cashRipeCheck(sender=alice)
    assert_reverted_call(err.value, "contract paused", c)

    assert ripe_token.totalSupply() == supply
    assert ripe_token.balanceOf(human_resources) == 0
    assert ripe_token.allowance(human_resources, teller) == 0
    assert c.totalClaimed() == claimed
    assert position(ripe_gov_vault, c, ripe_token) == pos_before
    assert ledger.ripeAvailForHr() == avail
    assert filter_logs(c, "RipeCheckCashed") == []

    assert switchboard_charlie.pause(ripe_gov_vault.address, False, sender=governance.address)
    claimable = c.getClaimable()
    assert c.cashRipeCheck(sender=alice) == claimable
    assert ripe_token.totalSupply() == supply + claimable
    assert position(ripe_gov_vault, c, ripe_token) == pos_before + claimable
    assert ripe_token.allowance(human_resources, teller) == 0   # reset to 0 on success


def test_g11c_ledger_contributor_index_convention_and_aggregate_walk(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, alice, bob, sally,
):
    """numContributors is `last 1-based index + 1`; the walks are range(1, n)."""
    n0 = ledger.numContributors()
    c1 = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
             ledger, governance, owner=alice, manager=bob)
    n1 = ledger.numContributors()
    assert n1 == max(n0, 1) + 1
    assert ledger.contributors(n1 - 1) == c1.address
    assert ledger.isHrContributor(c1.address)
    assert not ledger.isHrContributor(alice)

    c2 = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
             ledger, governance, owner=sally, manager=bob)
    n2 = ledger.numContributors()
    assert n2 == n1 + 1
    assert ledger.contributors(n2 - 1) == c2.address
    # the aggregate walk sees exactly the registered clones
    assert human_resources.getTotalCompensation() == c1.compensation() + c2.compensation()
    assert human_resources.getTotalClaimed() == 0


def test_g11c_aggregate_claimed_view_stays_stale_after_a_pre_cliff_burn(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token,
    alice, bob,
):
    """getTotalClaimed keeps counting RIPE that the pre-cliff cancel already burned.
    Monitoring drift, not a conservation break -- HR has no writer for totalClaimed."""
    setupRipeGovVaultConfig()
    c = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    travel_to(c.startTime() + (c.cliffTime() - c.startTime()) // 2)
    cashed = c.cashRipeCheck(sender=alice)
    before = human_resources.getTotalClaimed()
    assert before >= cashed

    aid = switchboard_delta.cancelPaycheckForContributor(c.address, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)

    assert position(ripe_gov_vault, c, ripe_token) == 0        # burned
    assert c.totalClaimed() == cashed                          # never rewound
    assert human_resources.getTotalClaimed() == before          # aggregate still counts it
    assert human_resources.getTotalCompensation() < before + c.compensation() + 1


def test_g11c_terminal_views_and_cash_stay_safe_after_each_cancel_flavour(
    human_resources, mission_control, switchboard_delta, contributor_template,
    ledger, governance, setupRipeGovVaultConfig, ripe_gov_vault, ripe_token,
    alice, bob, sally,
):
    setupRipeGovVaultConfig()
    # --- pre-cliff cancel after a cash: compensation 0 < totalClaimed
    a = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=alice, manager=bob)
    travel_to(a.startTime() + (a.cliffTime() - a.startTime()) // 2)
    cashed = a.cashRipeCheck(sender=alice)
    a.cancelPaycheck(sender=switchboard_delta.address)
    assert a.compensation() == 0 < a.totalClaimed() == cashed
    assert a.getTotalVested() == 0 and a.getClaimable() == 0 and a.getUnvestedComp() == 0
    assert a.getRemainingVestingLength() == 0
    assert a.cashRipeCheck(sender=alice) == 0
    travel_to(a.unlockTime() + 1)
    assert a.getTotalVested() == 0 and a.getUnvestedComp() == 0
    with boa.reverts("no balance"):
        a.initiateRipeTransfer(False, sender=alice)   # position was burned

    # --- after-cliff cancel: compensation == totalClaimed, endTime == cancel time
    b = _mk(human_resources, mission_control, switchboard_delta, contributor_template,
            ledger, governance, owner=sally, manager=bob)
    travel_to(b.cliffTime() + 10 * 24 * 3600)
    b.cancelPaycheck(sender=switchboard_delta.address)
    assert b.compensation() == b.totalClaimed() > 0
    assert b.endTime() == boa.env.evm.patch.timestamp
    assert b.getTotalVested() == b.compensation()
    assert b.getClaimable() == 0 and b.getUnvestedComp() == 0
    assert b.cashRipeCheck(sender=sally) == 0
    travel_to(b.endTime() + 5 * 24 * 3600)
    assert b.getTotalVested() == b.compensation()   # no division blow-up past endTime
    assert b.getClaimable() == 0


def test_g11c_delta_lite_wrappers_accept_any_address_unlike_the_governor_wrappers(
    human_resources, mission_control, switchboard_delta, switchboard_alpha,
    contributor_template, ledger, governance, alice, bob, sally,
):
    """`cancelPaycheckForContributor` / `setManagerForContributor` gate on
    `Ledger.isHrContributor`; the four lite wrappers do not."""
    with boa.reverts("not a contributor"):
        switchboard_delta.cancelPaycheckForContributor(alice, sender=governance.address)
    with boa.reverts("not a contributor"):
        switchboard_delta.setManagerForContributor(alice, bob, sender=governance.address)

    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_alpha.address)
    # no isHrContributor gate -- the call reaches an arbitrary target and only fails
    # on the callee side (here: no code / wrong selector)
    for fn in (switchboard_delta.cashRipeCheckForContributor,
               switchboard_delta.cancelRipeTransferForContributor,
               switchboard_delta.cancelOwnershipChangeForContributor,
               lambda a, sender: switchboard_delta.freezeContributor(a, True, sender=sender)):
        with pytest.raises(BoaError) as err:
            fn(alice, sender=sally)
        # the revert is the callee's, not Delta's `_hasPermsToEnable` gate
        assert "no perms" not in get_boa_dev_reasons(err.value)
