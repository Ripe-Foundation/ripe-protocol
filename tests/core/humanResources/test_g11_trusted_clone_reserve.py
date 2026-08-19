"""Trusted-clone / one-reserve Group 11 proofs."""

import boa

from constants import MAX_UINT256
from tests.core.humanResources.g11_proof_helpers import (
    release_live_hr_reserve,
    deploy_clone,
    official_delta_budget,
    official_delta_cancel,
    official_freeze,
    travel_to_ts,
)


def test_g11_create_bumps_reserved_cash_does_not(
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
    assert ledger.hrReservedCompensation() == 0
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    orig = c.compensation()
    assert ledger.hrReservedCompensation() == orig
    budget = ledger.ripeAvailForHr()
    travel_to_ts(c.startTime() + 1)
    p = c.cashRipeCheck(sender=c.owner())
    assert 0 < p < orig
    assert ledger.hrReservedCompensation() == orig
    assert ledger.ripeAvailForHr() == budget
    assert c.totalClaimed() == p


def test_g11_official_cash_cannot_exceed_get_claimable(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    ripe_token,
):
    setupRipeGovVaultConfig()
    c = contributor_contract
    travel_to_ts(c.startTime() + 1)
    claimable = c.getClaimable()
    supply = ripe_token.totalSupply()
    assert c.cashRipeCheck(sender=owner_address) == claimable
    assert ripe_token.totalSupply() == supply + claimable
    assert c.totalClaimed() == claimable
    assert c.getClaimable() == 0
    assert c.cashRipeCheck(sender=owner_address) == 0
    assert ripe_token.totalSupply() == supply + claimable


def test_g11_pre_cliff_cancel_after_cash_credits_full_c(
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
    release_live_hr_reserve(switchboard_delta, governance, ledger)
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    travel_to_ts(c.startTime() + 1)
    assert boa.env.evm.patch.timestamp < c.cliffTime()
    p = c.cashRipeCheck(sender=c.owner())
    orig = c.compensation()
    budget = ledger.ripeAvailForHr()
    supply = ripe_token.totalSupply()
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.compensation() == 0
    assert ledger.ripeAvailForHr() == budget + orig
    assert ledger.hrReservedCompensation() == 0
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == 0
    assert ripe_token.totalSupply() == supply - p


def test_g11_frozen_post_cliff_cancel_credits_c_minus_p(
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
    travel_to_ts(c.startTime() + 1)
    p = c.cashRipeCheck(sender=c.owner())
    official_freeze(switchboard_delta, governance, c, True)
    travel_to_ts(c.cliffTime() + 1)
    orig = c.compensation()
    budget = ledger.ripeAvailForHr()
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.totalClaimed() == p
    assert ledger.ripeAvailForHr() == budget + (orig - p)
    assert ledger.hrReservedCompensation() == p


def test_g11_max_setter_blocked_while_reserved_live(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
    switchboard_delta,
    governance,
    ledger,
):
    release_live_hr_reserve(switchboard_delta, governance, ledger)
    c, _ = deploy_clone(
        human_resources, governance, setupHrConfig, setupLedgerBalance, valid_contributor_terms
    )
    budget_before = ledger.ripeAvailForHr()
    aid = switchboard_delta.setRipeAvailableForHr(MAX_UINT256, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    with boa.reverts("exceeds hr budget headroom"):
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert ledger.ripeAvailForHr() == budget_before
    official_delta_budget(switchboard_delta, governance, MAX_UINT256 - ledger.hrReservedCompensation())
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert ledger.hrReservedCompensation() == 0
    official_delta_budget(switchboard_delta, governance, MAX_UINT256)
    assert ledger.ripeAvailForHr() == MAX_UINT256
