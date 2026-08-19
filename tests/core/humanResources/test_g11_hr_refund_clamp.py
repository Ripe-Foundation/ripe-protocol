"""Group 11 HR refund clamp: credit min(F, MAX - budget); always call Ledger."""

import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from conf_utils import assert_reverted_call, filter_logs
from constants import MAX_UINT256, ZERO_ADDRESS
from tests.core.humanResources.g11_proof_helpers import (
    charlie_pause,
    clone_at,
    confirm_contributor,
    deploy_clone,
    initiate_contributor,
    official_delta_budget,
    official_delta_cancel,
    official_freeze,
    travel_to_block,
    travel_to_ts,
)


def _terms(valid_contributor_terms, **overrides):
    out = dict(valid_contributor_terms)
    out.update(overrides)
    return out


def _write_max_alpha(ledger, switchboard_alpha):
    ledger.setRipeAvailForHr(MAX_UINT256, sender=switchboard_alpha.address)
    assert ledger.ripeAvailForHr() == MAX_UINT256


def test_g11_full_headroom_credits_full_forfeiture(
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
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    orig = c.compensation()
    budget = ledger.ripeAvailForHr()
    assert budget <= MAX_UINT256 - orig
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.compensation() == 0
    assert ledger.ripeAvailForHr() == budget + orig


def test_g11_exact_ceiling_cancel_fills_budget_to_max(
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
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    orig = c.compensation()
    official_delta_budget(switchboard_delta, governance, MAX_UINT256 - orig)
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.compensation() == 0
    assert ledger.ripeAvailForHr() == MAX_UINT256


def test_g11_partial_headroom_cancel_clamps_to_max(
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
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    orig = c.compensation()
    start_budget = MAX_UINT256 - orig + 1
    official_delta_budget(switchboard_delta, governance, start_budget)
    credited = MAX_UINT256 - start_budget
    assert 0 < credited < orig
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.compensation() == 0
    assert ledger.ripeAvailForHr() == start_budget + credited
    assert ledger.ripeAvailForHr() == MAX_UINT256


def test_g11_zero_headroom_cancel_keeps_budget_max(
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
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    official_delta_budget(switchboard_delta, governance, MAX_UINT256)
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.compensation() == 0
    assert ledger.ripeAvailForHr() == MAX_UINT256


def test_g11_zero_credit_direct_hr_still_calls_paused_ledger(
    contributor_contract,
    human_resources,
    ledger,
    switchboard_alpha,
    switchboard_charlie,
    governance,
):
    c = contributor_contract
    f = c.compensation()
    assert f != 0
    _write_max_alpha(ledger, switchboard_alpha)
    charlie_pause(switchboard_charlie, governance, ledger.address, True)
    with pytest.raises(BoaError) as exc:
        human_resources.refundAfterCancelPaycheck(f, False, sender=c.address)
    assert_reverted_call(exc.value, "not activated", human_resources)
    assert ledger.ripeAvailForHr() == MAX_UINT256
    charlie_pause(switchboard_charlie, governance, ledger.address, False)


def test_g11_zero_credit_official_cancel_paused_ledger_rolls_back(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    switchboard_alpha,
    switchboard_charlie,
    governance,
    ledger,
):
    setupRipeGovVaultConfig()
    c = contributor_contract
    official_freeze(switchboard_delta, governance, c, True)
    travel_to_ts(c.cliffTime() + 1)
    orig = c.compensation()
    end0 = c.endTime()
    aid = switchboard_delta.cancelPaycheckForContributor(
        c.address, sender=governance.address
    )
    travel_to_block(switchboard_delta.getActionConfirmationBlock(aid))
    assert switchboard_delta.hasPendingAction(aid)
    _write_max_alpha(ledger, switchboard_alpha)
    charlie_pause(switchboard_charlie, governance, ledger.address, True)
    with pytest.raises(BoaError) as exc:
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert_reverted_call(exc.value, "not activated", switchboard_delta)
    assert c.compensation() == orig
    assert c.endTime() == end0
    assert switchboard_delta.hasPendingAction(aid)
    assert ledger.ripeAvailForHr() == MAX_UINT256
    charlie_pause(switchboard_charlie, governance, ledger.address, False)


def test_g11_two_clone_lifecycle_second_cancel_credits_zero(
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
    h = MAX_UINT256 // 2
    setupHrConfig(_maxCompensation=0)
    official_delta_budget(switchboard_delta, governance, h)
    terms_a = _terms(
        valid_contributor_terms,
        compensation=h,
        owner="0x" + "a1" * 20,
        manager="0x" + "a2" * 20,
    )
    aid_a = initiate_contributor(human_resources, governance, terms_a)
    assert confirm_contributor(human_resources, governance, aid_a) is True
    addr_a = filter_logs(human_resources, "NewContributorConfirmed")[0].contributorAddr
    a = clone_at(addr_a)
    assert a.compensation() == h
    assert ledger.ripeAvailForHr() == 0

    official_delta_budget(switchboard_delta, governance, MAX_UINT256)
    terms_b = _terms(
        valid_contributor_terms,
        compensation=h,
        owner="0x" + "b1" * 20,
        manager="0x" + "b2" * 20,
    )
    aid_b = initiate_contributor(human_resources, governance, terms_b)
    assert confirm_contributor(human_resources, governance, aid_b) is True
    addr_b = filter_logs(human_resources, "NewContributorConfirmed")[0].contributorAddr
    b = clone_at(addr_b)
    assert b.compensation() == h
    assert ledger.ripeAvailForHr() == h + 1

    _, ok_a = official_delta_cancel(switchboard_delta, governance, a)
    assert ok_a is True
    assert a.compensation() == 0
    assert ledger.ripeAvailForHr() == MAX_UINT256

    _, ok_b = official_delta_cancel(switchboard_delta, governance, b)
    assert ok_b is True
    assert b.compensation() == 0
    assert ledger.ripeAvailForHr() == MAX_UINT256


def test_g11_pre_cliff_cancel_after_cash_at_max(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    setupRipeGovVaultConfig,
    valid_contributor_terms,
    switchboard_delta,
    governance,
    ledger,
    ripe_token,
    ripe_gov_vault,
):
    setupRipeGovVaultConfig()
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    travel_to_ts(c.startTime() + 1)
    assert boa.env.evm.patch.timestamp < c.cliffTime()
    p = c.cashRipeCheck(sender=c.owner())
    assert p > 0
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == p
    official_delta_budget(switchboard_delta, governance, MAX_UINT256)
    supply = ripe_token.totalSupply()
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.compensation() == 0
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == 0
    assert ripe_token.totalSupply() == supply - p
    assert ledger.ripeAvailForHr() == MAX_UINT256


def test_g11_post_cliff_cancel_at_max(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    governance,
    ledger,
    ripe_token,
    ripe_gov_vault,
):
    setupRipeGovVaultConfig()
    c = contributor_contract
    travel_to_ts(c.cliffTime() + 1)
    official_delta_budget(switchboard_delta, governance, MAX_UINT256)
    supply = ripe_token.totalSupply()
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    claimed = c.totalClaimed()
    assert claimed > 0
    assert c.compensation() == claimed
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == claimed
    assert ripe_token.totalSupply() == supply + claimed
    assert ledger.ripeAvailForHr() == MAX_UINT256


def test_g11_frozen_post_cliff_cancel_at_max(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    governance,
    ledger,
    ripe_token,
    ripe_gov_vault,
):
    setupRipeGovVaultConfig()
    c = contributor_contract
    official_freeze(switchboard_delta, governance, c, True)
    travel_to_ts(c.cliffTime() + 1)
    official_delta_budget(switchboard_delta, governance, MAX_UINT256)
    supply = ripe_token.totalSupply()
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.totalClaimed() == 0
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == 0
    assert ripe_token.totalSupply() == supply
    assert ledger.ripeAvailForHr() == MAX_UINT256


def test_g11_partial_credit_event_reports_full_forfeiture(
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
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    orig = c.compensation()
    official_delta_budget(switchboard_delta, governance, MAX_UINT256 - orig + 1)
    credited = orig - 1
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    events = filter_logs(switchboard_delta, "RipePaycheckCancelled")
    assert events
    assert events[0].forfeitedAmount == orig
    assert events[0].forfeitedAmount != credited
    assert ledger.ripeAvailForHr() == MAX_UINT256


def test_g11_unregistered_caller_cannot_refund(human_resources, alice):
    with boa.reverts("not a contributor"):
        human_resources.refundAfterCancelPaycheck(1, False, sender=alice)
    with boa.reverts("not a contributor"):
        human_resources.refundAfterCancelPaycheck(1, False, sender=ZERO_ADDRESS)


def test_g11_max_budget_via_official_delta_cancel_succeeds(
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
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    official_delta_budget(switchboard_delta, governance, MAX_UINT256)
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.compensation() == 0
    assert ledger.ripeAvailForHr() == MAX_UINT256


def test_g11_max_budget_via_switchboard_alpha_cancel_succeeds(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    setupRipeGovVaultConfig,
    valid_contributor_terms,
    switchboard_delta,
    switchboard_alpha,
    governance,
    ledger,
):
    setupRipeGovVaultConfig()
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    _write_max_alpha(ledger, switchboard_alpha)
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.compensation() == 0
    assert ledger.ripeAvailForHr() == MAX_UINT256
