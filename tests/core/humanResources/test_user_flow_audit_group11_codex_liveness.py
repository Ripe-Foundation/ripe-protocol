"""Focused Group 11 liveness proofs for Contributor / HumanResources.

These tests deliberately use the production Delta initiate/execute route for
budget changes.  Fixture-only MissionControl writes establish local terms;
they are not used as proof that an ordinary user can change a production
budget or template.
"""

import boa

from conf_utils import filter_logs
from contracts.modules import Contributor
from tests.core.humanResources.g11_proof_helpers import settle_unsettled_hr_grants


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


def test_g11_vesting_multiplication_overflow_bricks_cash_and_after_cliff_cancel(
    human_resources,
    governance,
    setupHrConfig,
    valid_contributor_terms,
):
    """Ranked 2**255 compensation is rejected at initiate."""
    terms = dict(valid_contributor_terms)
    terms["compensation"] = UINT256_MAX // 2 + 1
    terms["startDelay"] = 0
    setupHrConfig(_maxCompensation=0)
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(
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
    settle_unsettled_hr_grants(human_resources, ledger)
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


def test_g11_extreme_compensation_can_fail_nested_cash_math_at_elapsed_one(
    human_resources,
    governance,
    setupHrConfig,
    valid_contributor_terms,
):
    """Ranked 2**255 compensation is rejected at initiate."""
    terms = dict(valid_contributor_terms)
    terms["compensation"] = UINT256_MAX // 2 + 1
    terms["startDelay"] = 0
    terms["vestingLength"] = 365 * 24 * 60 * 60
    setupHrConfig(_maxCompensation=0)
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(
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


def test_g11_precliff_cancel_is_the_only_remaining_overflow_recovery(
    human_resources,
    governance,
    setupHrConfig,
    valid_contributor_terms,
):
    """Ranked 2**255 compensation is rejected at initiate."""
    terms = dict(valid_contributor_terms)
    terms["compensation"] = UINT256_MAX // 2 + 1
    terms["startDelay"] = 0
    setupHrConfig(_maxCompensation=0)
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(
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


def test_g11_near_uint_budget_overwrite_blocks_precliff_cancel_but_is_retryable(
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
    """MAX budget write reverts while cancel-credit liability > 0; a legal write then cancel succeeds."""
    terms = dict(valid_contributor_terms)
    terms["startDelay"] = 0
    setupHrConfig()
    settle_unsettled_hr_grants(human_resources, ledger)
    _set_hr_budget(switchboard_delta, governance, ledger, terms["compensation"])
    contributor = _deploy_contributor(human_resources, governance, terms)
    assert ledger.ripeAvailForHr() == 0

    budget_before = ledger.ripeAvailForHr()
    aid_max = switchboard_delta.setRipeAvailableForHr(
        UINT256_MAX, sender=governance.address
    )
    _advance_to_block(switchboard_delta.getActionConfirmationBlock(aid_max))
    with boa.reverts("exceeds hr budget headroom"):
        switchboard_delta.executePendingAction(aid_max, sender=governance.address)
    assert ledger.ripeAvailForHr() == budget_before
    assert switchboard_delta.hasPendingAction(aid_max)

    _set_hr_budget(
        switchboard_delta,
        governance,
        ledger,
        UINT256_MAX - ledger.hrCancelCreditLiability(),
    )
    action_id = switchboard_delta.cancelPaycheckForContributor(
        contributor.address, sender=governance.address
    )
    _advance_to_block(switchboard_delta.getActionConfirmationBlock(action_id))
    assert switchboard_delta.executePendingAction(action_id, sender=governance.address)
    assert contributor.compensation() == 0
    assert human_resources.hrGrant(contributor.address).settled
    assert ledger.hrReservedCompensation() == 0
    assert ledger.hrCancelCreditLiability() == 0


def test_g11_near_uint_budget_overwrite_rolls_back_after_cliff_cash_then_refund(
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
    """MAX budget write reverts while reserved > 0; after-cliff cancel still succeeds."""
    terms = dict(valid_contributor_terms)
    terms["startDelay"] = 0
    setupHrConfig()
    setupRipeGovVaultConfig()
    settle_unsettled_hr_grants(human_resources, ledger)
    _set_hr_budget(switchboard_delta, governance, ledger, terms["compensation"])
    contributor = _deploy_contributor(human_resources, governance, terms)

    target = contributor.cliffTime() + 1
    _advance_to_timestamp(target)
    claimable = contributor.getClaimable()
    assert 0 < claimable < terms["compensation"]
    budget_before = ledger.ripeAvailForHr()
    aid_max = switchboard_delta.setRipeAvailableForHr(
        UINT256_MAX, sender=governance.address
    )
    _advance_to_block(switchboard_delta.getActionConfirmationBlock(aid_max))
    with boa.reverts("exceeds hr budget headroom"):
        switchboard_delta.executePendingAction(aid_max, sender=governance.address)
    assert ledger.ripeAvailForHr() == budget_before
    assert switchboard_delta.hasPendingAction(aid_max)

    _set_hr_budget(
        switchboard_delta,
        governance,
        ledger,
        UINT256_MAX - ledger.hrCancelCreditLiability(),
    )
    action_id = switchboard_delta.cancelPaycheckForContributor(
        contributor.address, sender=governance.address
    )
    _advance_to_block(switchboard_delta.getActionConfirmationBlock(action_id))
    retry_claimable = contributor.getClaimable()
    assert retry_claimable >= claimable
    assert switchboard_delta.executePendingAction(action_id, sender=governance.address)
    assert contributor.compensation() == retry_claimable
    assert contributor.totalClaimed() == retry_claimable
    assert human_resources.hrGrant(contributor.address).settled
    assert ledger.hrReservedCompensation() == 0
    assert ledger.hrCancelCreditLiability() == 0
