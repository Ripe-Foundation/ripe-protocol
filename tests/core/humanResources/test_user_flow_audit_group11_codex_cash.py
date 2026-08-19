"""Focused Group 11 cash-path identities and production pause/gate controls."""

import boa

from conf_utils import filter_logs
from contracts.modules import Contributor


def _advance_to_timestamp(timestamp):
    current = boa.env.evm.patch.timestamp
    if current < timestamp:
        boa.env.time_travel(seconds=timestamp - current)
    assert boa.env.evm.patch.timestamp == timestamp


def _assert_cash_identity(contributor, caller, ripe_token, ripe_gov_vault, ledger, human_resources):
    claimable = contributor.getClaimable()
    supply_before = ripe_token.totalSupply()
    clone_before = ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
    owner_erc20_before = ripe_token.balanceOf(contributor.owner())
    owner_vault_before = ripe_gov_vault.getTotalAmountForUser(
        contributor.owner(), ripe_token
    )
    hr_before = ripe_token.balanceOf(human_resources)
    budget_before = ledger.ripeAvailForHr()
    claimed_before = contributor.totalClaimed()

    amount = contributor.cashRipeCheck(sender=caller)
    assert amount == claimable
    assert ripe_token.totalSupply() == supply_before + amount
    assert (
        ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
        == clone_before + amount
    )
    assert ripe_token.balanceOf(contributor.owner()) == owner_erc20_before
    assert (
        ripe_gov_vault.getTotalAmountForUser(contributor.owner(), ripe_token)
        == owner_vault_before
    )
    assert ripe_token.balanceOf(human_resources) == hr_before
    assert ledger.ripeAvailForHr() == budget_before
    assert contributor.totalClaimed() == claimed_before + amount
    return amount


def test_g11_cash_timing_identity_owner_manager_and_delta_governor(
    deployedContributor,
    valid_contributor_terms,
    setupRipeGovVaultConfig,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
    switchboard_delta,
    governance,
    owner_address,
    manager_address,
    alice,
):
    """Cash follows timestamp vesting, not the cliff, and preserves the budget."""
    setupRipeGovVaultConfig()
    contributor = Contributor.at(deployedContributor(dict(valid_contributor_terms)))

    with boa.reverts("no perms"):
        contributor.cashRipeCheck(sender=alice)

    _advance_to_timestamp(contributor.startTime() - 1)
    assert contributor.getClaimable() == 0
    assert contributor.cashRipeCheck(sender=owner_address) == 0

    _advance_to_timestamp(contributor.startTime())
    assert contributor.getClaimable() == 0
    assert contributor.cashRipeCheck(sender=owner_address) == 0

    # The first elapsed second is still before cliff but cashable.
    _advance_to_timestamp(contributor.startTime() + 1)
    assert boa.env.evm.patch.timestamp < contributor.cliffTime()
    owner_amount = _assert_cash_identity(
        contributor,
        owner_address,
        ripe_token,
        ripe_gov_vault,
        ledger,
        human_resources,
    )
    assert owner_amount > 0

    _advance_to_timestamp(contributor.cliffTime())
    manager_amount = _assert_cash_identity(
        contributor,
        manager_address,
        ripe_token,
        ripe_gov_vault,
        ledger,
        human_resources,
    )
    assert manager_amount > 0

    # Delta's governor is a real authorized caller; no lite permission is
    # granted for this proof.
    claimed_before = contributor.totalClaimed()
    assert switchboard_delta.cashRipeCheckForContributor(
        contributor.address, sender=governance.address
    )
    delta_amount = contributor.totalClaimed() - claimed_before
    assert delta_amount >= 0
    wrapper_events = filter_logs(switchboard_delta, "RipeCheckCashedFromSwitchboard")
    assert len(wrapper_events) == 1
    assert wrapper_events[0].contributor == contributor.address
    assert wrapper_events[0].cashedBy == governance.address
    assert wrapper_events[0].amount == delta_amount

    _advance_to_timestamp(contributor.endTime())
    end_amount = _assert_cash_identity(
        contributor,
        owner_address,
        ripe_token,
        ripe_gov_vault,
        ledger,
        human_resources,
    )
    assert end_amount == valid_contributor_terms["compensation"] - claimed_before - delta_amount
    assert contributor.getClaimable() == 0
    assert contributor.cashRipeCheck(sender=manager_address) == 0

    _advance_to_timestamp(contributor.endTime() + 1)
    assert contributor.cashRipeCheck(sender=owner_address) == 0


def test_g11_official_hr_pause_and_hq_mint_gate_roll_back_cash_then_retry(
    deployedContributor,
    valid_contributor_terms,
    setupRipeGovVaultConfig,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
    switchboard_charlie,
    ripe_hq_deploy,
    governance,
    owner_address,
):
    """Charlie pause and HQ mint disable both stop the official cash route."""
    setupRipeGovVaultConfig()
    contributor = Contributor.at(deployedContributor(dict(valid_contributor_terms)))
    _advance_to_timestamp(contributor.startTime() + 1)
    assert contributor.getClaimable() > 0

    baseline = (
        ripe_token.totalSupply(),
        ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token),
        contributor.totalClaimed(),
        ledger.ripeAvailForHr(),
    )
    assert switchboard_charlie.pause(
        human_resources.address, True, sender=governance.address
    )
    # Contributor's outer assertion intentionally hides the HR reason; the
    # stack reaches HumanResources.cashRipeCheck's paused guard.
    with boa.reverts():
        contributor.cashRipeCheck(sender=owner_address)
    assert (
        ripe_token.totalSupply(),
        ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token),
        contributor.totalClaimed(),
        ledger.ripeAvailForHr(),
    ) == baseline
    assert switchboard_charlie.pause(
        human_resources.address, False, sender=governance.address
    )

    assert ripe_hq_deploy.canMintRipe(human_resources.address)
    ripe_hq_deploy.setMintingEnabled(False, sender=governance.address)
    assert not ripe_hq_deploy.canMintRipe(human_resources.address)
    with boa.reverts():
        contributor.cashRipeCheck(sender=owner_address)
    assert (
        ripe_token.totalSupply(),
        ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token),
        contributor.totalClaimed(),
        ledger.ripeAvailForHr(),
    ) == baseline

    ripe_hq_deploy.setMintingEnabled(True, sender=governance.address)
    assert _assert_cash_identity(
        contributor,
        owner_address,
        ripe_token,
        ripe_gov_vault,
        ledger,
        human_resources,
    ) > 0
