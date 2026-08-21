"""Focused Group 11 liveness proofs for Contributor / HumanResources.

These tests deliberately use the production Delta initiate/execute route for
budget changes.  Fixture-only MissionControl writes establish local terms;
they are not used as proof that an ordinary user can change a production
budget or template.
"""

import boa

from conf_utils import filter_logs
from contracts.modules import Contributor


UINT256_MAX = 2**256 - 1


def _advance_to_block(block_number):
    current = boa.env.evm.patch.block_number
    if current < block_number:
        boa.env.time_travel(blocks=block_number - current)
    assert boa.env.evm.patch.block_number >= block_number


def _set_hr_budget(switchboard_delta, governance, ledger, amount):
    action_id = switchboard_delta.setRipeAvailableForHr(
        amount, sender=governance.address
    )
    _advance_to_block(switchboard_delta.getActionConfirmationBlock(action_id))
    assert switchboard_delta.executePendingAction(action_id, sender=governance.address)
    assert ledger.ripeAvailForHr() == amount
    return action_id


def _deploy_contributor(human_resources, governance, terms):
    action_id = human_resources.initiateNewContributor(
        terms["owner"],
        terms["manager"],
        terms["compensation"],
        terms["startDelay"],
        terms["vestingLength"],
        terms["cliffLength"],
        terms["unlockLength"],
        terms["depositLockDuration"],
        sender=governance.address,
    )
    _advance_to_block(human_resources.getActionConfirmationBlock(action_id))
    assert human_resources.confirmNewContributor(action_id, sender=governance.address)
    events = filter_logs(human_resources, "NewContributorConfirmed")
    assert len(events) == 1
    return Contributor.at(events[0].contributorAddr)


def _advance_to_timestamp(timestamp):
    current = boa.env.evm.patch.timestamp
    if current < timestamp:
        boa.env.time_travel(seconds=timestamp - current)
    assert boa.env.evm.patch.timestamp == timestamp


def test_g11_vesting_product_boundary_predecessor_cashes_and_records_live_position(
    human_resources,
    switchboard_delta,
    governance,
    ledger,
    setupHrConfig,
    setupRipeGovVaultConfig,
    valid_contributor_terms,
    ripe_token,
    ripe_gov_vault,
):
    """A safe vesting-product predecessor still reaches the cash success path.

    A four-year duration keeps the first cash amount itself below the RipeGov
    share-conversion range, isolating the Contributor vesting multiplication
    boundary from independent downstream arithmetic.

    On the audit pin the later amount view and within-vault transfer reverted
    (Group 6 SharesVault product). Current ``rh`` no longer overflows that
    view; this node keeps the Group 11 cash proof and records the live
    position instead of requiring the old revert.
    """
    terms = dict(valid_contributor_terms)
    terms["compensation"] = UINT256_MAX // 2
    terms["startDelay"] = 0
    terms["vestingLength"] = 4 * 365 * 24 * 60 * 60
    setupHrConfig(_maxCompensation=0)
    setupRipeGovVaultConfig()
    _set_hr_budget(switchboard_delta, governance, ledger, terms["compensation"])
    contributor = _deploy_contributor(human_resources, governance, terms)

    _advance_to_timestamp(contributor.startTime() + 2)
    expected = terms["compensation"] * 2 // terms["vestingLength"]
    assert contributor.getTotalVested() == expected
    assert contributor.getClaimable() == expected
    supply_before = ripe_token.totalSupply()
    vault_token_before = ripe_token.balanceOf(ripe_gov_vault)
    assert contributor.cashRipeCheck(sender=terms["owner"]) == expected
    assert ripe_token.totalSupply() == supply_before + expected
    assert ripe_token.balanceOf(ripe_gov_vault) == vault_token_before + expected
    assert ripe_gov_vault.userGovData(contributor, ripe_token).lastShares > 0
    assert contributor.totalClaimed() == expected
    assert ledger.ripeAvailForHr() == 0
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == expected


def test_g11_near_uint_budget_overwrite_allows_precliff_cancel(
    human_resources,
    switchboard_delta,
    governance,
    ledger,
    setupHrConfig,
    valid_contributor_terms,
    ripe_token,
    ripe_gov_vault,
    teller,
):
    """MAX budget write succeeds with a live grant; cancel at MAX clamps credit to 0."""
    terms = dict(valid_contributor_terms)
    terms["startDelay"] = 0
    setupHrConfig()
    _set_hr_budget(switchboard_delta, governance, ledger, terms["compensation"])
    contributor = _deploy_contributor(human_resources, governance, terms)
    assert ledger.ripeAvailForHr() == 0

    _set_hr_budget(switchboard_delta, governance, ledger, UINT256_MAX)
    action_id = switchboard_delta.cancelPaycheckForContributor(
        contributor.address, sender=governance.address
    )
    _advance_to_block(switchboard_delta.getActionConfirmationBlock(action_id))
    assert switchboard_delta.executePendingAction(action_id, sender=governance.address)
    assert contributor.compensation() == 0
    assert ledger.ripeAvailForHr() == UINT256_MAX




def test_g11_near_uint_budget_overwrite_allows_after_cliff_cancel(
    human_resources,
    switchboard_delta,
    governance,
    ledger,
    setupHrConfig,
    setupRipeGovVaultConfig,
    valid_contributor_terms,
    ripe_token,
    ripe_gov_vault,
    teller,
):
    """MAX budget write succeeds with a live grant; after-cliff cancel clamps credit."""
    terms = dict(valid_contributor_terms)
    terms["startDelay"] = 0
    setupHrConfig()
    setupRipeGovVaultConfig()
    _set_hr_budget(switchboard_delta, governance, ledger, terms["compensation"])
    contributor = _deploy_contributor(human_resources, governance, terms)

    target = contributor.cliffTime() + 1
    _advance_to_timestamp(target)
    claimable = contributor.getClaimable()
    assert 0 < claimable < terms["compensation"]
    _set_hr_budget(switchboard_delta, governance, ledger, UINT256_MAX)
    action_id = switchboard_delta.cancelPaycheckForContributor(
        contributor.address, sender=governance.address
    )
    _advance_to_block(switchboard_delta.getActionConfirmationBlock(action_id))
    retry_claimable = contributor.getClaimable()
    assert retry_claimable >= claimable
    assert switchboard_delta.executePendingAction(action_id, sender=governance.address)
    assert contributor.compensation() == retry_claimable
    assert contributor.totalClaimed() == retry_claimable
    assert ledger.ripeAvailForHr() == UINT256_MAX
