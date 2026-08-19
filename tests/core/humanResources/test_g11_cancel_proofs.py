import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from conf_utils import assert_reverted_call, filter_logs
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from contracts.modules import Contributor
from tests.core.humanResources.g11_proof_helpers import (
    release_live_hr_reserve,
    charlie_pause,
    deploy_clone,
    official_delta_cancel,
    official_freeze,
    seed_ripe_gov_position,
    snapshot_econ,
    travel_to_block,
    travel_to_ts,
)


def _prep(setupRipeGovVaultConfig):
    setupRipeGovVaultConfig()


def test_g11_official_delta_cancel_before_start_full_refund_terminal(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    governance,
    ledger,
    ripe_token,
    ripe_gov_vault,
    human_resources,
    teller,
    owner_address,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    assert boa.env.evm.patch.timestamp < c.startTime()
    before = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    orig = c.compensation()
    aid, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.compensation() == 0
    assert c.endTime() == boa.env.evm.patch.timestamp
    assert c.unlockTime() == before["unlock"]
    assert ledger.ripeAvailForHr() == before["budget"] + orig
    assert c.getTotalVested() == 0
    assert c.getClaimable() == 0
    assert c.getUnvestedComp() == 0
    ev = filter_logs(c, "RipePaycheckCancelled")
    if ev:
        assert ev[0].forfeitedAmount == orig
        assert ev[0].didReachCliff is False


def test_g11_official_delta_cancel_pre_cliff_no_cash(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    governance,
    ledger,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.startTime() + (c.cliffTime() - c.startTime()) // 2)
    assert c.getTotalVested() > 0
    orig = c.compensation()
    budget = ledger.ripeAvailForHr()
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.compensation() == 0
    assert ledger.ripeAvailForHr() == budget + orig
    assert c.totalClaimed() == 0


def test_g11_spoof_switchboard_cancel_is_not_production_path(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_alpha,
    ledger,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    orig = c.compensation()
    budget = ledger.ripeAvailForHr()
    c.cancelPaycheck(sender=switchboard_alpha.address)
    assert c.compensation() == 0
    assert ledger.ripeAvailForHr() == budget + orig


def test_g11_residue_b_plus_p_burns_only_comp_refunds(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    governance,
    owner_address,
    ripe_token,
    ripe_gov_vault,
    whale,
    teller,
    ledger,
    alice,
    human_resources,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    b = 1_000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(alice, b, sender=whale)
    with boa.reverts("cannot deposit for user"):
        teller.deposit(ripe_token, b, c.address, ZERO_ADDRESS, 2, sender=alice)
    seed_ripe_gov_position(ripe_gov_vault, ripe_token, whale, teller, c.address, b)
    travel_to_ts(c.startTime() + (c.cliffTime() - c.startTime()) // 2)
    p = c.cashRipeCheck(sender=owner_address)
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == b + p
    orig = c.compensation()
    supply = ripe_token.totalSupply()
    budget = ledger.ripeAvailForHr()
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == 0
    assert ledger.ripeAvailForHr() == budget + orig
    assert ripe_token.totalSupply() == supply - (b + p)


def test_g11_exact_cliff_cash_then_refund_remainder_no_burn(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    governance,
    owner_address,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
    teller,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.cliffTime())
    assert c.getClaimable() > 0
    supply = ripe_token.totalSupply()
    budget = ledger.ripeAvailForHr()
    orig = c.compensation()
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    claimed = c.totalClaimed()
    assert claimed > 0
    assert c.compensation() == claimed
    assert ledger.ripeAvailForHr() == budget + (orig - claimed)
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == claimed
    assert ripe_token.totalSupply() == supply + claimed
    assert c.endTime() == boa.env.evm.patch.timestamp
    assert c.unlockTime() != 0


def test_g11_cancel_path_cash_cashed_by_is_hr(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    human_resources,
):
    """Official Delta execute does not surface nested Contributor logs via filter_logs.
    Same cancel-path cash is `_cashRipeCheck(owner, hr, hr)` — cashedBy is HR.
    """
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.cliffTime())
    c.cancelPaycheck(sender=switchboard_delta.address)
    ev = filter_logs(c, "RipeCheckCashed")
    assert len(ev) == 1
    assert ev[0].cashedBy == human_resources.address
    assert ev[0].amount == c.totalClaimed()
    assert ev[0].amount > 0


def test_g11_after_cliff_cancel_keeps_cashed_position_unlock_unchanged(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    governance,
    owner_address,
    ripe_token,
    ripe_gov_vault,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.cliffTime() + 1)
    unlock = c.unlockTime()
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    pos = ripe_gov_vault.getTotalAmountForUser(c, ripe_token)
    assert pos == c.totalClaimed()
    assert pos > 0
    assert c.unlockTime() == unlock
    assert c.endTime() < unlock
    with boa.reverts("time not past unlock"):
        c.initiateRipeTransfer(False, sender=owner_address)
    travel_to_ts(unlock + 1)
    c.initiateRipeTransfer(False, sender=owner_address)
    travel_to_block(c.pendingRipeTransfer().confirmBlock)
    c.confirmRipeTransfer(False, sender=owner_address)
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token) == pos


def test_g11_cancel_at_and_after_end_reverts(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    governance,
    ledger,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.endTime())
    budget = ledger.ripeAvailForHr()
    orig = c.compensation()
    aid = switchboard_delta.cancelPaycheckForContributor(c.address, sender=governance.address)
    travel_to_block(switchboard_delta.getActionConfirmationBlock(aid))
    assert boa.env.evm.patch.timestamp >= c.endTime()
    try:
        ok = switchboard_delta.executePendingAction(aid, sender=governance.address)
        assert ok is False
    except BoaError:
        ok = False
    assert c.compensation() == orig
    assert ledger.ripeAvailForHr() == budget
    travel_to_ts(max(c.endTime() + 1, boa.env.evm.patch.timestamp))
    if switchboard_delta.actionType(aid) != 0:
        try:
            switchboard_delta.executePendingAction(aid, sender=governance.address)
        except BoaError:
            pass
    assert c.compensation() == orig
    assert ledger.ripeAvailForHr() == budget


def test_g11_second_official_cancel_reverts(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    governance,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    with boa.reverts("cannot cancel"):
        official_delta_cancel(switchboard_delta, governance, c)


def test_g11_frozen_after_cliff_forfeits_vested_uncashed_vs_unfrozen(
    valid_contributor_terms,
    deployedContributor,
    setupRipeGovVaultConfig,
    switchboard_delta,
    governance,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
    teller,
):
    _prep(setupRipeGovVaultConfig)
    terms = dict(valid_contributor_terms)
    terms["owner"] = "0x" + "a1" * 20
    c_frozen = Contributor.at(deployedContributor(terms))
    terms2 = dict(valid_contributor_terms)
    terms2["owner"] = "0x" + "a2" * 20
    c_open = Contributor.at(deployedContributor(terms2))
    target = max(c_frozen.cliffTime(), c_open.cliffTime()) + 1
    travel_to_ts(target)
    claimable = c_frozen.getClaimable()
    claimable_open = c_open.getClaimable()
    assert claimable > 0
    assert claimable_open > 0

    orig_frozen = c_frozen.compensation()
    orig_open = c_open.compensation()
    official_freeze(switchboard_delta, governance, c_frozen, True)
    supply_f = ripe_token.totalSupply()
    budget_f = ledger.ripeAvailForHr()
    _, ok_f = official_delta_cancel(switchboard_delta, governance, c_frozen)
    assert ok_f is True
    frozen_claimed = c_frozen.totalClaimed()
    frozen_pos = ripe_gov_vault.getTotalAmountForUser(c_frozen, ripe_token)
    frozen_supply = ripe_token.totalSupply()
    frozen_budget = ledger.ripeAvailForHr()

    supply_o = ripe_token.totalSupply()
    budget_o = ledger.ripeAvailForHr()
    _, ok_o = official_delta_cancel(switchboard_delta, governance, c_open)
    assert ok_o is True
    open_claimed = c_open.totalClaimed()
    open_pos = ripe_gov_vault.getTotalAmountForUser(c_open, ripe_token)
    open_supply = ripe_token.totalSupply()
    open_budget = ledger.ripeAvailForHr()

    assert frozen_claimed == 0
    assert frozen_pos == 0
    assert frozen_supply == supply_f
    assert frozen_budget == budget_f + orig_frozen
    assert open_claimed > 0
    assert open_pos == open_claimed
    assert open_supply == supply_o + open_claimed
    assert open_budget == budget_o + (orig_open - open_claimed)
    assert (open_pos - frozen_pos) == open_claimed
    assert (open_supply - supply_o) - (frozen_supply - supply_f) == open_claimed


def test_g11_official_pause_rolls_back_mature_delta_cancel_then_same_pending_executes(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    switchboard_charlie,
    governance,
    human_resources,
    ledger,
    ripe_token,
    ripe_gov_vault,
    teller,
    owner_address,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.cliffTime() + 1)
    aid = switchboard_delta.cancelPaycheckForContributor(c.address, sender=governance.address)
    travel_to_block(switchboard_delta.getActionConfirmationBlock(aid))
    before = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    pending_type = switchboard_delta.actionType(aid)
    charlie_pause(switchboard_charlie, governance, human_resources.address, True)
    with pytest.raises(BoaError) as exc:
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert_reverted_call(exc.value, "contract paused", switchboard_delta)
    after = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    assert after["comp"] == before["comp"]
    assert after["end"] == before["end"]
    assert after["unlock"] == before["unlock"]
    assert after["claimed"] == before["claimed"]
    assert after["budget"] == before["budget"]
    assert switchboard_delta.actionType(aid) == pending_type
    charlie_pause(switchboard_charlie, governance, human_resources.address, False)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert c.endTime() == boa.env.evm.patch.timestamp
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == c.totalClaimed()
    assert c.totalClaimed() > 0


def test_g11_unfrozen_after_cliff_does_not_burn_cashed_ripe(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    governance,
    ripe_token,
    ripe_gov_vault,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.cliffTime() + 1)
    supply = ripe_token.totalSupply()
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    pos = ripe_gov_vault.getTotalAmountForUser(c, ripe_token)
    assert pos == c.totalClaimed()
    assert ripe_token.totalSupply() == supply + pos


def _grant_snapshot(
    human_resources,
    ledger,
    contributor,
    ripe_gov_vault,
    ripe_token,
    switchboard_delta=None,
    aid=None,
):
    snap = {
        "reserved": ledger.hrReservedCompensation(),
        "budget": ledger.ripeAvailForHr(),
        "vault": ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token),
        "comp": contributor.compensation(),
        "claimed": contributor.totalClaimed(),
        "end": contributor.endTime(),
        "unlock": contributor.unlockTime(),
        "supply": ripe_token.totalSupply(),
        "hr_ripe": ripe_token.balanceOf(human_resources),
    }
    if switchboard_delta is not None and aid is not None:
        snap["action_type"] = switchboard_delta.actionType(aid)
        snap["pending_cancel"] = switchboard_delta.pendingCancelPaycheck(aid)
        snap["has_pending"] = switchboard_delta.hasPendingAction(aid)
        snap["confirm_block"] = switchboard_delta.getActionConfirmationBlock(aid)
    return snap



def _initiate_mature_cancel(switchboard_delta, governance, contributor):
    aid = switchboard_delta.cancelPaycheckForContributor(
        contributor.address, sender=governance.address
    )
    travel_to_block(switchboard_delta.getActionConfirmationBlock(aid))
    assert switchboard_delta.hasPendingAction(aid)
    assert switchboard_delta.pendingCancelPaycheck(aid) == contributor.address
    return aid


def test_g11_pre_cliff_cancel_ledger_pause_rolls_back_then_same_action_retries(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    switchboard_charlie,
    governance,
    owner_address,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.startTime() + 1)
    p = c.cashRipeCheck(sender=owner_address)
    assert p > 0
    aid = _initiate_mature_cancel(switchboard_delta, governance, c)
    snap = _grant_snapshot(
        human_resources, ledger, c, ripe_gov_vault, ripe_token, switchboard_delta, aid
    )
    charlie_pause(switchboard_charlie, governance, ledger.address, True)
    with pytest.raises(BoaError) as exc:
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert_reverted_call(exc.value, "not activated", switchboard_delta)
    assert _grant_snapshot(
        human_resources, ledger, c, ripe_gov_vault, ripe_token, switchboard_delta, aid
    ) == snap
    charlie_pause(switchboard_charlie, governance, ledger.address, False)
    budget = ledger.ripeAvailForHr()
    orig = c.compensation()
    assert switchboard_delta.executePendingAction(aid, sender=governance.address) is True
    assert ledger.ripeAvailForHr() == budget + orig
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == 0


def test_g11_pre_cliff_cancel_lootbox_revert_rolls_back(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    switchboard_charlie,
    governance,
    owner_address,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
    lootbox,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.startTime() + 1)
    p = c.cashRipeCheck(sender=owner_address)
    assert p > 0
    aid = _initiate_mature_cancel(switchboard_delta, governance, c)
    snap = _grant_snapshot(
        human_resources, ledger, c, ripe_gov_vault, ripe_token, switchboard_delta, aid
    )
    charlie_pause(switchboard_charlie, governance, lootbox.address, True)
    with pytest.raises(BoaError):
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert _grant_snapshot(
        human_resources, ledger, c, ripe_gov_vault, ripe_token, switchboard_delta, aid
    ) == snap
    charlie_pause(switchboard_charlie, governance, lootbox.address, False)


def test_g11_pre_cliff_cancel_vault_withdraw_revert_rolls_back(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    switchboard_charlie,
    governance,
    owner_address,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.startTime() + 1)
    p = c.cashRipeCheck(sender=owner_address)
    assert p > 0
    aid = _initiate_mature_cancel(switchboard_delta, governance, c)
    snap = _grant_snapshot(
        human_resources, ledger, c, ripe_gov_vault, ripe_token, switchboard_delta, aid
    )
    charlie_pause(switchboard_charlie, governance, ripe_gov_vault.address, True)
    with pytest.raises(BoaError):
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert _grant_snapshot(
        human_resources, ledger, c, ripe_gov_vault, ripe_token, switchboard_delta, aid
    ) == snap
    charlie_pause(switchboard_charlie, governance, ripe_gov_vault.address, False)




def test_g11_official_delta_cancel_pre_cliff_after_cash_refunds_full_and_burns(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    governance,
    owner_address,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
    teller,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.startTime() + (c.cliffTime() - c.startTime()) // 2)
    p = c.cashRipeCheck(sender=owner_address)
    assert p > 0
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == p
    orig = c.compensation()
    reserved = ledger.hrReservedCompensation()
    supply = ripe_token.totalSupply()
    budget = ledger.ripeAvailForHr()
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.compensation() == 0
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == 0
    assert ledger.ripeAvailForHr() == budget + orig
    assert ledger.hrReservedCompensation() == reserved - orig
    assert ripe_token.totalSupply() == supply - p


def test_g11_pre_cliff_cash_then_unfrozen_after_cliff_cancel_leaves_cashed_notional(
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
    p = c.cashRipeCheck(sender=c.owner())
    assert p > 0
    travel_to_ts(c.cliffTime() + 1)
    budget = ledger.ripeAvailForHr()
    orig = c.compensation()
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    claimed = c.totalClaimed()
    assert claimed >= p
    assert ledger.ripeAvailForHr() == budget + (orig - claimed)
    assert ledger.hrReservedCompensation() == claimed


def test_g11_frozen_after_pre_cliff_cash_refunds_c_minus_p_and_leaves_p(
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
    p = c.cashRipeCheck(sender=c.owner())
    assert p > 0
    official_freeze(switchboard_delta, governance, c, True)
    travel_to_ts(c.cliffTime() + 1)
    orig = c.compensation()
    budget = ledger.ripeAvailForHr()
    assert ledger.hrReservedCompensation() == orig
    pos = ripe_gov_vault.getTotalAmountForUser(c, ripe_token)
    assert pos == p
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.totalClaimed() == p
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == p
    assert ledger.ripeAvailForHr() == budget + (orig - p)
    assert ledger.hrReservedCompensation() == p


def test_g11_pre_cliff_cancel_with_empty_vault_still_refunds_full_c(
    contributor_contract,
    setupRipeGovVaultConfig,
    switchboard_delta,
    governance,
    owner_address,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
):
    """Trusted-clone cancel refunds full C even if the vault was already emptied."""
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.startTime() + 1)
    assert boa.env.evm.patch.timestamp < c.cliffTime()
    p = c.cashRipeCheck(sender=owner_address)
    assert p > 0
    ripe_gov_vault.withdrawContributorTokensToBurn(c.address, sender=human_resources.address)
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == 0
    orig = c.compensation()
    reserved = ledger.hrReservedCompensation()
    budget = ledger.ripeAvailForHr()
    _, ok = official_delta_cancel(switchboard_delta, governance, c)
    assert ok is True
    assert c.compensation() == 0
    assert ledger.ripeAvailForHr() == budget + orig
    assert ledger.hrReservedCompensation() == reserved - orig
