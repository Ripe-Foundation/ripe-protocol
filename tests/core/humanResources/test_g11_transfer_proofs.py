import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from conf_utils import assert_reverted_call, filter_logs
from constants import MAX_UINT256
from contracts.modules import Contributor
from tests.core.humanResources.g11_proof_helpers import (
    PRECISION,
    cash_clamp,
    charlie_pause,
    clone_unlock,
    grant_lite,
    official_freeze,
    owner_self_deposit,
    owner_unlock,
    pending_transfer,
    snapshot_econ,
    travel_to_block,
    travel_to_ts,
)


def _prep(setupRipeGovVaultConfig, **kwargs):
    setupRipeGovVaultConfig(**kwargs)


def _cash_to_position(contributor, caller):
    travel_to_ts(contributor.startTime() + 1)
    amount = contributor.cashRipeCheck(sender=caller)
    assert amount > 0
    return amount


def test_g11_unlock_exact_reverts_plus_one_initiates(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    ripe_gov_vault,
    ripe_token,
    ledger,
    human_resources,
    teller,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    _cash_to_position(c, owner_address)
    travel_to_ts(c.unlockTime())
    with boa.reverts("time not past unlock"):
        c.initiateRipeTransfer(False, sender=owner_address)
    assert not c.hasPendingRipeTransfer()

    travel_to_ts(c.unlockTime() + 1)
    c.initiateRipeTransfer(False, sender=owner_address)
    recipient, _, confirm = pending_transfer(c)
    assert recipient == owner_address
    assert confirm == boa.env.evm.patch.block_number + c.keyActionDelay()


def test_g11_frozen_initiate_and_confirm_revert(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    switchboard_delta,
    governance,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    _cash_to_position(c, owner_address)
    travel_to_ts(c.unlockTime() + 1)
    official_freeze(switchboard_delta, governance, c, True)
    with boa.reverts("contract frozen"):
        c.initiateRipeTransfer(False, sender=owner_address)
    official_freeze(switchboard_delta, governance, c, False)
    c.initiateRipeTransfer(False, sender=owner_address)
    official_freeze(switchboard_delta, governance, c, True)
    travel_to_block(c.pendingRipeTransfer().confirmBlock)
    with boa.reverts("contract frozen"):
        c.confirmRipeTransfer(False, sender=owner_address)
    assert c.hasPendingRipeTransfer()


def test_g11_pending_owner_blocks_initiate(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    alice,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    _cash_to_position(c, owner_address)
    travel_to_ts(c.unlockTime() + 1)
    c.changeOwnership(alice, sender=owner_address)
    with boa.reverts("cannot do with pending ownership change"):
        c.initiateRipeTransfer(False, sender=owner_address)


def test_g11_manager_initiate_and_confirm_credit_owner(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    manager_address,
    ripe_gov_vault,
    ripe_token,
    ledger,
    human_resources,
    teller,
    alice,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    _cash_to_position(c, manager_address)
    travel_to_ts(c.unlockTime() + 1)
    clone_before = ripe_gov_vault.getTotalAmountForUser(c, ripe_token)
    owner_before = ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
    supply_before = ripe_token.totalSupply()
    c.initiateRipeTransfer(False, sender=manager_address)
    assert pending_transfer(c)[0] == owner_address
    travel_to_block(c.pendingRipeTransfer().confirmBlock)
    c.confirmRipeTransfer(False, sender=manager_address)
    ev = filter_logs(c, "RipeTransferConfirmed")[0]
    assert ev.recipient == owner_address
    assert ev.confirmedBy == manager_address
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token) == owner_before + clone_before
    assert ripe_token.totalSupply() == supply_before
    c.changeOwnership(alice, sender=owner_address)
    travel_to_block(c.pendingOwner().confirmBlock)
    c.confirmOwnershipChange(sender=alice)
    assert c.owner() == alice


def test_g11_reinitiate_restarts_confirm_block_owner_recovers_via_set_manager(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    manager_address,
    alice,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    _cash_to_position(c, owner_address)
    travel_to_ts(c.unlockTime() + 1)
    c.initiateRipeTransfer(False, sender=manager_address)
    first = c.pendingRipeTransfer().confirmBlock
    boa.env.time_travel(blocks=10)
    c.initiateRipeTransfer(False, sender=manager_address)
    second = c.pendingRipeTransfer().confirmBlock
    assert second == boa.env.evm.patch.block_number + c.keyActionDelay()
    assert second > first
    boa.env.time_travel(blocks=10)
    c.initiateRipeTransfer(False, sender=manager_address)
    third = c.pendingRipeTransfer().confirmBlock
    assert third > second
    extra = third - first
    assert extra > 0
    c.setManager(alice, sender=owner_address)
    assert c.manager() == alice
    assert pending_transfer(c)[0] == owner_address
    c.cancelRipeTransfer(sender=owner_address)
    assert not c.hasPendingRipeTransfer()
    c.initiateRipeTransfer(False, sender=owner_address)
    assert c.pendingRipeTransfer().confirmBlock == boa.env.evm.patch.block_number + c.keyActionDelay()


def test_g11_set_key_action_delay_after_initiate_does_not_retime(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    human_resources,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    _cash_to_position(c, owner_address)
    travel_to_ts(c.unlockTime() + 1)
    c.initiateRipeTransfer(False, sender=owner_address)
    confirm = c.pendingRipeTransfer().confirmBlock
    new_delay = min(c.keyActionDelay() + 100, human_resources.maxActionTimeLock())
    c.setKeyActionDelay(new_delay, sender=owner_address)
    assert c.pendingRipeTransfer().confirmBlock == confirm
    travel_to_block(confirm - 1)
    with boa.reverts("time delay not reached"):
        c.confirmRipeTransfer(False, sender=owner_address)
    assert c.hasPendingRipeTransfer()
    travel_to_block(confirm)
    c.confirmRipeTransfer(False, sender=owner_address)
    assert not c.hasPendingRipeTransfer()


def test_g11_should_cash_false_moves_existing_leaves_unclaimed(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    ripe_gov_vault,
    ripe_token,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    first = _cash_to_position(c, owner_address)
    travel_to_ts(c.unlockTime() + 1)
    unclaimed = c.getClaimable()
    assert unclaimed > 0
    pos = ripe_gov_vault.getTotalAmountForUser(c, ripe_token)
    assert pos == first
    c.initiateRipeTransfer(False, sender=owner_address)
    travel_to_block(c.pendingRipeTransfer().confirmBlock)
    c.confirmRipeTransfer(False, sender=owner_address)
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token) == pos
    assert c.totalClaimed() == first
    assert c.getClaimable() > 0


def test_g11_cancel_transfer_owner_manager_lite_and_frozen(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    manager_address,
    switchboard_delta,
    governance,
    mission_control,
    alice,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    _cash_to_position(c, owner_address)
    travel_to_ts(c.unlockTime() + 1)

    c.initiateRipeTransfer(False, sender=owner_address)
    c.cancelRipeTransfer(sender=owner_address)
    assert not c.hasPendingRipeTransfer()

    c.initiateRipeTransfer(False, sender=owner_address)
    c.cancelRipeTransfer(sender=manager_address)
    assert not c.hasPendingRipeTransfer()

    c.initiateRipeTransfer(False, sender=owner_address)
    grant_lite(mission_control, switchboard_delta, alice)
    assert switchboard_delta.cancelRipeTransferForContributor(c.address, sender=alice)
    assert not c.hasPendingRipeTransfer()

    c.initiateRipeTransfer(False, sender=owner_address)
    official_freeze(switchboard_delta, governance, c, True)
    c.cancelRipeTransfer(sender=owner_address)
    assert not c.hasPendingRipeTransfer()


def test_g11_late_failure_cash_then_unlock_reverts_rolls_back(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
    teller,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.startTime() + 1)
    assert c.getClaimable() > 0
    travel_to_ts(c.unlockTime())
    before = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    with boa.reverts("time not past unlock"):
        c.initiateRipeTransfer(True, sender=owner_address)
    after = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    assert after == before
    assert not c.hasPendingRipeTransfer()


def test_g11_late_failure_cash_then_pending_owner_rolls_back(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    alice,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
    teller,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.startTime() + 1)
    c.changeOwnership(alice, sender=owner_address)
    before = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    with boa.reverts("cannot do with pending ownership change"):
        c.initiateRipeTransfer(True, sender=owner_address)
    after = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    assert after == before


def test_g11_late_failure_adjacent_direct_cash_succeeds(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
    teller,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.unlockTime())
    before = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    minted = c.cashRipeCheck(sender=owner_address)
    assert minted > 0
    after = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    assert after["supply"] == before["supply"] + minted
    assert after["clone_vault"] == before["clone_vault"] + minted


def test_g11_confirm_overflow_duration_after_cash_rolls_back_pending_stays(
    valid_contributor_terms,
    setupHrConfig,
    setupLedgerBalance,
    setupRipeGovVaultConfig,
    human_resources,
    governance,
    ripe_token,
    ripe_gov_vault,
    ledger,
    teller,
):
    _prep(setupRipeGovVaultConfig)
    terms = dict(valid_contributor_terms)
    terms["depositLockDuration"] = MAX_UINT256
    setupHrConfig()
    setupLedgerBalance(terms["compensation"])
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


def test_g11_charlie_hr_pause_confirm_rolls_back_then_same_pending_confirms(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    switchboard_charlie,
    governance,
    ripe_gov_vault,
    ripe_token,
    human_resources,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    _cash_to_position(c, owner_address)
    travel_to_ts(c.unlockTime() + 1)
    c.initiateRipeTransfer(False, sender=owner_address)
    pending = pending_transfer(c)
    pos = ripe_gov_vault.getTotalAmountForUser(c, ripe_token)
    travel_to_block(c.pendingRipeTransfer().confirmBlock)
    charlie_pause(switchboard_charlie, governance, human_resources.address, True)
    with pytest.raises(BoaError) as exc:
        c.confirmRipeTransfer(False, sender=owner_address)
    assert_reverted_call(exc.value, "contract paused", c)
    assert pending_transfer(c) == pending
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == pos
    charlie_pause(switchboard_charlie, governance, human_resources.address, False)
    c.confirmRipeTransfer(False, sender=owner_address)
    ev = filter_logs(c, "RipeTransferConfirmed")[0]
    assert ev.recipient == owner_address
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token) == pos


@pytest.mark.parametrize("duration", [0, 50, 100, 1000, 1001, MAX_UINT256])
@pytest.mark.parametrize("branch", ["below_precision", "at_or_above_precision"])
def test_g11_lock_matrix_cash_clamped_transfer_raw(
    duration,
    branch,
    valid_contributor_terms,
    setupHrConfig,
    setupLedgerBalance,
    setupRipeGovVaultConfig,
    human_resources,
    governance,
    ripe_token,
    ripe_gov_vault,
    whale,
    teller,
    alice,
    bob,
):
    min_lock, max_lock = 100, 1000
    _prep(setupRipeGovVaultConfig, _minLockDuration=min_lock, _maxLockDuration=max_lock)
    terms = dict(valid_contributor_terms)
    terms["owner"] = alice
    terms["manager"] = bob
    terms["depositLockDuration"] = duration
    setupHrConfig()
    setupLedgerBalance(terms["compensation"])
    if duration in (0, 1001, MAX_UINT256):
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
        return
    aid = human_resources.initiateNewContributor(
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
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid, sender=governance.address)
    c = Contributor.at(filter_logs(human_resources, "NewContributorConfirmed")[0].contributorAddr)

    # Empty-vault first deposit mints amount * 1e8 shares. Seed share counts,
    # not 1:1 token amounts, so the RipeGov prevShares branch is the intended one.
    if branch == "at_or_above_precision":
        owner_self_deposit(teller, ripe_token, whale, alice, 2 * 10**10)
        assert ripe_gov_vault.userBalances(alice, ripe_token) >= PRECISION
    else:
        owner_self_deposit(teller, ripe_token, whale, alice, 1000)
        assert ripe_gov_vault.userBalances(alice, ripe_token) < PRECISION

    travel_to_ts(c.unlockTime() + 1)
    cash_block = boa.env.evm.patch.block_number
    c.initiateRipeTransfer(True, sender=alice)
    expected_cash = cash_clamp(duration, min_lock, max_lock)
    assert clone_unlock(ripe_gov_vault, ripe_token, c) == cash_block + expected_cash

    travel_to_block(c.pendingRipeTransfer().confirmBlock)
    confirm_block = boa.env.evm.patch.block_number
    c.confirmRipeTransfer(False, sender=alice)
    ev = filter_logs(c, "RipeTransferConfirmed")[0]
    assert ev.recipient == alice
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == 0
    unlock = owner_unlock(ripe_gov_vault, ripe_token, alice)
    if branch == "below_precision":
        # prev owner shares may still be < PRECISION after the transfer if
        # the incoming position is absorbed into the weighted branch.
        # Seed was < PRECISION; transfer uses raw block+duration when
        # prevShares < PRECISION at handle time.
        assert unlock == confirm_block + duration
    else:
        assert unlock >= confirm_block
