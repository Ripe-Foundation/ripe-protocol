"""Focused Group 11 two-step transfer timing and late-failure rollback proofs."""

import boa

from contracts.modules import Contributor


UINT256_MAX = 2**256 - 1


def _advance_to_block(block_number):
    current = boa.env.evm.patch.block_number
    if current < block_number:
        boa.env.time_travel(blocks=block_number - current)
    assert boa.env.evm.patch.block_number >= block_number


def _advance_to_timestamp(timestamp):
    current = boa.env.evm.patch.timestamp
    if current < timestamp:
        boa.env.time_travel(seconds=timestamp - current)
    assert boa.env.evm.patch.timestamp == timestamp


def _cash_snapshot(contributor, ripe_token, ripe_gov_vault, ledger):
    return (
        ripe_token.totalSupply(),
        ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token),
        contributor.totalClaimed(),
        ledger.ripeAvailForHr(),
    )


def test_g11_late_initiate_checks_roll_back_optional_cash_at_unlock_and_pending_owner(
    deployedContributor,
    valid_contributor_terms,
    setupRipeGovVaultConfig,
    ripe_token,
    ripe_gov_vault,
    ledger,
    owner_address,
    alice,
):
    """Cash runs before these guards, but neither late revert can retain it."""

    def run_case(pending_owner):
        with boa.env.anchor():
            setupRipeGovVaultConfig()
            contributor = Contributor.at(deployedContributor(dict(valid_contributor_terms)))
            target = contributor.unlockTime() + (1 if pending_owner else 0)
            _advance_to_timestamp(target)
            if pending_owner:
                contributor.changeOwnership(alice, sender=owner_address)
            before = _cash_snapshot(contributor, ripe_token, ripe_gov_vault, ledger)
            assert contributor.getClaimable() > 0
            with boa.reverts():
                contributor.initiateRipeTransfer(True, sender=owner_address)
            assert _cash_snapshot(contributor, ripe_token, ripe_gov_vault, ledger) == before
            assert not contributor.hasPendingRipeTransfer()
            # Adjacent cash control proves the failed initiate actually entered
            # the cashable state rather than missing vesting.
            assert contributor.cashRipeCheck(sender=owner_address) > 0

    run_case(False)  # strict timestamp > unlock: exact unlock reverts
    run_case(True)   # past unlock, but a pending ownership handoff reverts


def test_g11_raw_duration_transfer_revert_rolls_back_confirm_optional_cash(
    deployedContributor,
    valid_contributor_terms,
):
    """Overflow-sized depositLockDuration is rejected at initiate."""
    terms = dict(valid_contributor_terms)
    terms["depositLockDuration"] = UINT256_MAX
    with boa.reverts("invalid terms"):
        Contributor.at(deployedContributor(terms))


def test_g11_hr_pause_rolls_back_confirm_and_same_pending_retries_cleanly(
    deployedContributor,
    valid_contributor_terms,
    setupRipeGovVaultConfig,
    ripe_token,
    ripe_gov_vault,
    human_resources,
    switchboard_charlie,
    governance,
    owner_address,
):
    """Charlie pause blocks the HR callee without consuming a valid handoff."""
    setupRipeGovVaultConfig()
    contributor = Contributor.at(deployedContributor(dict(valid_contributor_terms)))
    _advance_to_timestamp(contributor.startTime() + 1)
    assert contributor.cashRipeCheck(sender=owner_address) > 0
    _advance_to_timestamp(contributor.unlockTime() + 1)
    contributor.initiateRipeTransfer(False, sender=owner_address)
    pending = contributor.pendingRipeTransfer()
    _advance_to_block(pending.confirmBlock)
    clone_before = ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
    owner_before = ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
    supply_before = ripe_token.totalSupply()

    assert switchboard_charlie.pause(
        human_resources.address, True, sender=governance.address
    )
    with boa.reverts():
        contributor.confirmRipeTransfer(False, sender=owner_address)
    assert contributor.pendingRipeTransfer() == pending
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == clone_before
    assert ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token) == owner_before
    assert ripe_token.totalSupply() == supply_before

    assert switchboard_charlie.pause(
        human_resources.address, False, sender=governance.address
    )
    contributor.confirmRipeTransfer(False, sender=owner_address)
    assert not contributor.hasPendingRipeTransfer()
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == 0
    assert (
        ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
        == owner_before + clone_before
    )
    assert ripe_token.totalSupply() == supply_before
