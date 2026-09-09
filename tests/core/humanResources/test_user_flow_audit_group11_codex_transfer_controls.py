"""Group 11 manager, restart, and frozen-cancellation transfer controls."""

import boa

from contracts.modules import Contributor


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


def _seed_position(contributor, ripe_gov_vault, ripe_token, whale, teller):
    amount = 1_000 * 10**18
    ripe_token.transfer(ripe_gov_vault, amount, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        contributor.address, ripe_token, amount, sender=teller.address
    )
    return amount


def test_g11_manager_can_initiate_and_confirm_but_only_stored_owner_receives(
    contributor_contract,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    manager_address,
    alice,
):
    """False cash check preserves unclaimed vest while manager moves only B."""
    setupRipeGovVaultConfig()
    seeded = _seed_position(contributor_contract, ripe_gov_vault, ripe_token, whale, teller)
    _advance_to_timestamp(contributor_contract.unlockTime() + 1)
    claimable = contributor_contract.getClaimable()
    assert claimable > 0
    contributor_contract.initiateRipeTransfer(False, sender=manager_address)
    pending = contributor_contract.pendingRipeTransfer()
    assert pending.recipient == owner_address
    assert contributor_contract.totalClaimed() == 0
    with boa.reverts("time delay not reached"):
        contributor_contract.confirmRipeTransfer(False, sender=manager_address)
    assert contributor_contract.pendingRipeTransfer() == pending
    _advance_to_block(pending.confirmBlock)
    owner_before = ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
    contributor_contract.confirmRipeTransfer(False, sender=manager_address)
    assert ripe_gov_vault.getTotalAmountForUser(contributor_contract, ripe_token) == 0
    assert (
        ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
        == owner_before + seeded
    )
    assert contributor_contract.totalClaimed() == 0
    # Confirmation consumes only the seeded position; vesting continues while
    # its block-delay elapses, so the still-uncashed amount may increase.
    assert contributor_contract.getClaimable() >= claimable

    # A completed transfer releases the owner-change exclusion; it does not
    # alter the historic recipient of the transfer that just completed.
    contributor_contract.changeOwnership(alice, sender=owner_address)
    handoff = contributor_contract.pendingOwner()
    _advance_to_block(handoff.confirmBlock)
    contributor_contract.confirmOwnershipChange(sender=alice)
    assert contributor_contract.owner() == alice


def test_g11_manager_restart_delay_owner_rotation_recovery_and_delay_nonretiming(
    contributor_contract,
    human_resources,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
    manager_address,
    alice,
):
    """Repeated initiate restarts the timer, but owner recovery is immediate."""
    setupRipeGovVaultConfig()
    _seed_position(contributor_contract, ripe_gov_vault, ripe_token, whale, teller)
    _advance_to_timestamp(contributor_contract.unlockTime() + 1)
    contributor_contract.initiateRipeTransfer(False, sender=manager_address)
    first = contributor_contract.pendingRipeTransfer()
    boa.env.time_travel(blocks=1)
    contributor_contract.initiateRipeTransfer(False, sender=manager_address)
    second = contributor_contract.pendingRipeTransfer()
    assert second.recipient == first.recipient == owner_address
    assert second.initiatedBlock == first.initiatedBlock + 1
    assert second.confirmBlock == first.confirmBlock + 1

    # The owner can remove the griefer immediately.  Changing delay after
    # initiation cannot retroactively alter the stored confirmation block.
    contributor_contract.setManager(alice, sender=owner_address)
    assert contributor_contract.manager() == alice
    with boa.reverts("no perms"):
        contributor_contract.initiateRipeTransfer(False, sender=manager_address)
    new_delay = human_resources.minActionTimeLock() + 1
    contributor_contract.setKeyActionDelay(new_delay, sender=owner_address)
    assert contributor_contract.keyActionDelay() == new_delay
    assert contributor_contract.pendingRipeTransfer().confirmBlock == second.confirmBlock

    _advance_to_block(second.confirmBlock)
    contributor_contract.confirmRipeTransfer(False, sender=owner_address)
    assert not contributor_contract.hasPendingRipeTransfer()


def test_g11_owner_manager_and_lite_wrapper_cancel_pending_transfer_while_frozen(
    deployedContributor,
    valid_contributor_terms,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    mission_control,
    switchboard_delta,
    governance,
    owner_address,
    manager_address,
    alice,
):
    """All three cancellation routes remain available while freeze blocks confirm."""

    with boa.env.anchor():
        setupRipeGovVaultConfig()
        contributor = Contributor.at(deployedContributor(dict(valid_contributor_terms)))
        _seed_position(contributor, ripe_gov_vault, ripe_token, whale, teller)
        _advance_to_timestamp(contributor.unlockTime() + 1)
        assert switchboard_delta.freezeContributor(
            contributor.address, True, sender=governance.address
        )
        with boa.reverts("contract frozen"):
            contributor.initiateRipeTransfer(False, sender=owner_address)
        assert not contributor.hasPendingRipeTransfer()

    def run_case(route):
        with boa.env.anchor():
            setupRipeGovVaultConfig()
            contributor = Contributor.at(deployedContributor(dict(valid_contributor_terms)))
            _seed_position(contributor, ripe_gov_vault, ripe_token, whale, teller)
            _advance_to_timestamp(contributor.unlockTime() + 1)
            contributor.initiateRipeTransfer(False, sender=owner_address)
            assert switchboard_delta.freezeContributor(
                contributor.address, True, sender=governance.address
            )
            with boa.reverts("contract frozen"):
                contributor.confirmRipeTransfer(False, sender=owner_address)
            if route == "owner":
                contributor.cancelRipeTransfer(sender=owner_address)
            elif route == "manager":
                contributor.cancelRipeTransfer(sender=manager_address)
            else:
                # Fixture-only lite enrollment; launch Defaults has no signer.
                mission_control.setCanPerformLiteAction(
                    alice, True, sender=switchboard_delta.address
                )
                assert switchboard_delta.cancelRipeTransferForContributor(
                    contributor.address, sender=alice
                )
            assert contributor.isFrozen()
            assert not contributor.hasPendingRipeTransfer()

    run_case("owner")
    run_case("manager")
    run_case("lite")
