import boa
import pytest

from constants import EIGHTEEN_DECIMALS
from tests.core.humanResources.g11_proof_helpers import (
    official_delta_cancel,
    travel_to_ts,
)


def _cash_pre_cliff(contributor):
    target = contributor.startTime() + (
        contributor.cliffTime() - contributor.startTime()
    ) // 2
    travel_to_ts(target)
    assert boa.env.evm.patch.timestamp < contributor.cliffTime()
    claimed = contributor.cashRipeCheck(sender=contributor.owner())
    assert claimed == contributor.totalClaimed()
    assert claimed > 0
    return claimed


def _cancel(switchboard_delta, governance, contributor):
    _, ok = official_delta_cancel(switchboard_delta, governance, contributor)
    assert ok is True


def _rotate_core(
    alternate_ripe_gov_vault,
    registerVault,
    mission_control,
    switchboard_alpha,
):
    historical_vault_id = mission_control.coreRipeGovVaultId()
    replacement_vault_id = registerVault(
        alternate_ripe_gov_vault, "Replacement Core RipeGov"
    )
    mission_control.setCoreRipeGovVaultId(
        replacement_vault_id, sender=switchboard_alpha.address
    )
    assert mission_control.coreRipeGovVaultId() == replacement_vault_id
    return historical_vault_id, replacement_vault_id


def test_pre_cliff_cancel_does_not_refund_claimed_ripe_left_in_historical_vault(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    alternate_ripe_gov_vault,
    registerVault,
    mission_control,
    switchboard_alpha,
    switchboard_delta,
    governance,
    ripe_token,
    ledger,
):
    setupRipeGovVaultConfig()
    contributor = contributor_contract
    compensation = contributor.compensation()
    claimed = _cash_pre_cliff(contributor)
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == claimed

    _rotate_core(
        alternate_ripe_gov_vault,
        registerVault,
        mission_control,
        switchboard_alpha,
    )
    budget_before = ledger.ripeAvailForHr()
    supply_before = ripe_token.totalSupply()

    _cancel(switchboard_delta, governance, contributor)

    assert contributor.compensation() == 0
    assert contributor.totalClaimed() == claimed
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == claimed
    assert alternate_ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == 0
    assert ripe_token.totalSupply() == supply_before
    assert ledger.ripeAvailForHr() == budget_before + compensation - claimed


def test_burn_path_formula_zero_keeps_budget_when_claimed_position_is_elsewhere(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    alternate_ripe_gov_vault,
    registerVault,
    mission_control,
    switchboard_alpha,
    human_resources,
    ripe_token,
    ledger,
):
    setupRipeGovVaultConfig()
    contributor = contributor_contract
    compensation_before = contributor.compensation()
    claimed = _cash_pre_cliff(contributor)
    _rotate_core(
        alternate_ripe_gov_vault,
        registerVault,
        mission_control,
        switchboard_alpha,
    )
    budget_before = ledger.ripeAvailForHr()
    supply_before = ripe_token.totalSupply()

    human_resources.refundAfterCancelPaycheck(
        claimed,
        True,
        sender=contributor.address,
    )

    assert contributor.compensation() == compensation_before
    assert contributor.totalClaimed() == claimed
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == claimed
    assert alternate_ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == 0
    assert ripe_token.totalSupply() == supply_before
    assert ledger.ripeAvailForHr() == budget_before


def test_pre_cliff_cancel_refunds_full_compensation_when_historical_vault_is_selected(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    alternate_ripe_gov_vault,
    registerVault,
    mission_control,
    switchboard_alpha,
    switchboard_delta,
    governance,
    human_resources,
    ripe_token,
    ledger,
):
    setupRipeGovVaultConfig()
    contributor = contributor_contract
    compensation = contributor.compensation()
    claimed = _cash_pre_cliff(contributor)
    historical_vault_id, _ = _rotate_core(
        alternate_ripe_gov_vault,
        registerVault,
        mission_control,
        switchboard_alpha,
    )
    human_resources.setLegacyContributorRipeGovVaultId(
        contributor, historical_vault_id, sender=contributor.owner()
    )
    budget_before = ledger.ripeAvailForHr()
    supply_before = ripe_token.totalSupply()

    _cancel(switchboard_delta, governance, contributor)

    assert contributor.compensation() == 0
    assert contributor.totalClaimed() == claimed
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == 0
    assert alternate_ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == 0
    assert ripe_token.totalSupply() == supply_before - claimed
    assert ledger.ripeAvailForHr() == budget_before + compensation
    assert human_resources.legacyContributorRipeGovVaultId(contributor) == 0


def test_explicit_historical_vault_burn_does_not_clear_legacy_selection(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    alternate_ripe_gov_vault,
    registerVault,
    mission_control,
    switchboard_alpha,
    human_resources,
    ripe_token,
    ledger,
):
    setupRipeGovVaultConfig()
    contributor = contributor_contract
    compensation = contributor.compensation()
    claimed = _cash_pre_cliff(contributor)
    historical_vault_id, _ = _rotate_core(
        alternate_ripe_gov_vault,
        registerVault,
        mission_control,
        switchboard_alpha,
    )
    human_resources.setLegacyContributorRipeGovVaultId(
        contributor, historical_vault_id, sender=contributor.owner()
    )
    budget_before = ledger.ripeAvailForHr()
    supply_before = ripe_token.totalSupply()

    human_resources.refundAfterCancelPaycheck(
        compensation,
        True,
        historical_vault_id,
        sender=contributor.address,
    )

    assert contributor.compensation() == compensation
    assert contributor.totalClaimed() == claimed
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == 0
    assert alternate_ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == 0
    assert ripe_token.totalSupply() == supply_before - claimed
    assert ledger.ripeAvailForHr() == budget_before + compensation
    assert (
        human_resources.legacyContributorRipeGovVaultId(contributor)
        == historical_vault_id
    )


@pytest.mark.parametrize("residue_relation", ["below", "equal", "above"])
def test_pre_cliff_cancel_caps_recovered_claimed_amount_at_actual_residue_burned(
    residue_relation,
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    alternate_ripe_gov_vault,
    registerVault,
    mission_control,
    switchboard_alpha,
    switchboard_delta,
    governance,
    ripe_token,
    whale,
    teller,
    ledger,
):
    setupRipeGovVaultConfig()
    contributor = contributor_contract
    compensation = contributor.compensation()
    claimed = _cash_pre_cliff(contributor)
    _rotate_core(
        alternate_ripe_gov_vault,
        registerVault,
        mission_control,
        switchboard_alpha,
    )

    if residue_relation == "below":
        residue = claimed // 2
        assert residue < claimed
    elif residue_relation == "equal":
        residue = claimed
    else:
        residue = claimed + 1_000 * EIGHTEEN_DECIMALS
        assert residue > claimed

    ripe_token.transfer(alternate_ripe_gov_vault, residue, sender=whale)
    deposited = alternate_ripe_gov_vault.depositTokensInVault(
        contributor, ripe_token, residue, sender=teller.address
    )
    assert deposited == residue
    actual_burn_amount = alternate_ripe_gov_vault.getTotalAmountForUser(
        contributor, ripe_token
    )
    assert actual_burn_amount == residue
    budget_before = ledger.ripeAvailForHr()
    supply_before = ripe_token.totalSupply()

    _cancel(switchboard_delta, governance, contributor)

    expected_refund = compensation - claimed + min(claimed, actual_burn_amount)
    if residue_relation in ("equal", "above"):
        assert expected_refund == compensation
    assert contributor.compensation() == 0
    assert contributor.totalClaimed() == claimed
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == claimed
    assert alternate_ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == 0
    assert ripe_token.totalSupply() == supply_before - actual_burn_amount
    assert ledger.ripeAvailForHr() == budget_before + expected_refund


def test_pre_cliff_cancel_without_prior_claim_still_refunds_full_compensation(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    governance,
    ripe_token,
    ledger,
):
    setupRipeGovVaultConfig()
    contributor = contributor_contract
    compensation = contributor.compensation()
    assert contributor.totalClaimed() == 0
    assert boa.env.evm.patch.timestamp < contributor.cliffTime()
    budget_before = ledger.ripeAvailForHr()
    supply_before = ripe_token.totalSupply()

    _cancel(switchboard_delta, governance, contributor)

    assert contributor.compensation() == 0
    assert ledger.ripeAvailForHr() == budget_before + compensation
    assert ripe_token.totalSupply() == supply_before


def test_post_cliff_non_burn_cancel_behavior_is_unchanged(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    alternate_ripe_gov_vault,
    registerVault,
    setAssetConfig,
    mission_control,
    switchboard_alpha,
    switchboard_delta,
    governance,
    human_resources,
    ripe_token,
    ledger,
):
    setupRipeGovVaultConfig()
    contributor = contributor_contract
    compensation = contributor.compensation()
    claimed_before = _cash_pre_cliff(contributor)
    historical_vault_id, replacement_vault_id = _rotate_core(
        alternate_ripe_gov_vault,
        registerVault,
        mission_control,
        switchboard_alpha,
    )
    setAssetConfig(
        ripe_token, _vaultIds=[historical_vault_id, replacement_vault_id]
    )
    human_resources.setLegacyContributorRipeGovVaultId(
        contributor, historical_vault_id, sender=contributor.owner()
    )
    travel_to_ts(contributor.cliffTime() + 1)
    budget_before = ledger.ripeAvailForHr()
    supply_before = ripe_token.totalSupply()

    _cancel(switchboard_delta, governance, contributor)

    claimed = contributor.totalClaimed()
    assert claimed > claimed_before
    assert contributor.compensation() == claimed
    assert (
        ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
        == claimed_before
    )
    assert (
        alternate_ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
        == claimed - claimed_before
    )
    assert (
        human_resources.legacyContributorRipeGovVaultId(contributor)
        == historical_vault_id
    )
    assert ripe_token.totalSupply() == supply_before + claimed - claimed_before
    assert ledger.ripeAvailForHr() == budget_before + compensation - claimed
