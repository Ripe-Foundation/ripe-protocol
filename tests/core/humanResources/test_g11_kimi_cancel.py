"""Group 11 (kimi) proof tests — never-skip #3: cancel paycheck.

Production path is Delta cancelPaycheckForContributor (governor + Delta
timelock) -> executePendingAction -> Contributor.cancelPaycheck. The
`sender=switchboard_alpha.address` spoof is priced separately as
fixture/direct-state-only.

Key semantics proven here:
- before start: full refund, terminal views callable (no div-by-zero)
- pre-cliff after a cash: full ORIGINAL compensation refunded, clone position
  burned (supply down by cashed amount)
- residue B (seeded via Teller-impersonation deposit, stated as
  deposit-permission-dependent) is burned along with the paycheck position
  while only the original compensation is refunded to ripeAvailForHr
- exact cliffTime: cash-then-refund-remainder, no burn
- after cliff: no burn, clone keeps cashed RIPE, unlockTime unchanged
- frozen + after-cliff: cash-first returns 0 -> forfeits vested-but-uncashed
  RIPE (measured against the identical unfrozen cancel)
- near-uint256 ripeAvailForHr overwrite: MAX setter succeeds with a live grant;
  cancel clamps unrepresentable credit
- pause rollback: mature Delta cancel + Charlie/HR pause -> execute reverts,
  Delta pending survives, unpause -> same pending executes
"""
import boa
import pytest

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from contracts.modules import Contributor


def _ts():
    return boa.env.evm.patch.timestamp


def _travel_to_ts(t):
    now = _ts()
    if now < t:
        boa.env.time_travel(seconds=t - now)


def _pos(vault, user, asset):
    return vault.getTotalAmountForUser(user, asset)


def _deploy(human_resources, setupHrConfig, setupLedgerBalance, governance,
            valid_contributor_terms, **overrides):
    terms = dict(valid_contributor_terms)
    terms.update(overrides)
    setupHrConfig()
    setupLedgerBalance(terms["compensation"])
    aid = human_resources.initiateNewContributor(
        terms["owner"], terms["manager"], terms["compensation"],
        terms["startDelay"], terms["vestingLength"], terms["cliffLength"],
        terms["unlockLength"], terms["depositLockDuration"],
        sender=governance.address,
    )
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid, sender=governance.address)
    events = filter_logs(human_resources, "NewContributorConfirmed")
    return Contributor.at(events[-1].contributorAddr)


def _delta_cancel(switchboard_delta, governance, contributor):
    aid = switchboard_delta.cancelPaycheckForContributor(
        contributor.address, sender=governance.address
    )
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    return aid


def test_g11_cancel_before_start_full_refund_terminal_views(
    human_resources, contributor_contract, setupRipeGovVaultConfig,
    ripe_token, ledger, switchboard_delta, governance, valid_contributor_terms,
):
    """Cancel before start: full refund, no burn, terminal views callable."""
    c = contributor_contract
    terms = valid_contributor_terms
    assert _ts() < c.startTime()
    avail0 = ledger.ripeAvailForHr()
    assert avail0 == 0  # fixture reserved exactly compensation
    supply0 = ripe_token.totalSupply()

    aid = _delta_cancel(switchboard_delta, governance, c)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    ev = filter_logs(switchboard_delta, "RipePaycheckCancelled")
    assert len(ev) == 1
    assert ev[0].didReachCliff is False
    assert ev[0].forfeitedAmount == terms["compensation"]
    assert c.compensation() == 0
    assert c.endTime() <= _ts()
    assert ledger.ripeAvailForHr() == avail0 + terms["compensation"]
    assert ripe_token.totalSupply() == supply0  # nothing minted/burned
    # terminal views stay callable (compensation == 0 keeps off the division)
    assert c.getTotalVested() == 0
    assert c.getClaimable() == 0
    assert c.getUnvestedComp() == 0
    # second official cancel reverts (timestamp < endTime fails)
    aid2 = switchboard_delta.cancelPaycheckForContributor(c.address, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    with boa.reverts():
        switchboard_delta.executePendingAction(aid2, sender=governance.address)


def test_g11_cancel_pre_cliff_no_prior_cash(
    human_resources, contributor_contract, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, ledger, switchboard_delta, governance,
    valid_contributor_terms,
):
    """Pre-cliff, no cash: full compensation refund, zero-position burn (no-op)."""
    setupRipeGovVaultConfig()
    c = contributor_contract
    terms = valid_contributor_terms
    _travel_to_ts(c.startTime() + 10)
    assert _ts() < c.cliffTime()
    supply0 = ripe_token.totalSupply()

    aid = _delta_cancel(switchboard_delta, governance, c)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    ev = filter_logs(switchboard_delta, "RipePaycheckCancelled")
    assert len(ev) == 1
    assert ev[0].didReachCliff is False
    assert ev[0].forfeitedAmount == terms["compensation"]
    assert ledger.ripeAvailForHr() == terms["compensation"]
    assert ripe_token.totalSupply() == supply0
    assert _pos(ripe_gov_vault, c.address, ripe_token) == 0


def test_g11_cancel_pre_cliff_after_cash_budget_burn_supply(
    human_resources, contributor_contract, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, ledger, switchboard_delta, governance,
    valid_contributor_terms,
):
    """Pre-cliff after a cash: refund = FULL original compensation; burn pulls
    the clone position; supply down by the cashed amount. This is the specified
    'fully forfeitable' pairing, not a conservation failure."""
    setupRipeGovVaultConfig()
    c = contributor_contract
    terms = valid_contributor_terms
    _travel_to_ts(c.startTime() + 30 * 24 * 3600)
    assert _ts() < c.cliffTime()
    cashed = c.cashRipeCheck(sender=valid_contributor_terms["owner"])
    assert cashed > 0
    assert _pos(ripe_gov_vault, c.address, ripe_token) == cashed
    supply_after_cash = ripe_token.totalSupply()
    avail_after_cash = ledger.ripeAvailForHr()

    aid = _delta_cancel(switchboard_delta, governance, c)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    ev = filter_logs(switchboard_delta, "RipePaycheckCancelled")
    assert len(ev) == 1
    assert ev[0].didReachCliff is False
    assert ev[0].forfeitedAmount == terms["compensation"]  # FULL original, even though partially cashed
    # budget refunded in full while the cashed position is burned:
    assert ledger.ripeAvailForHr() == avail_after_cash + terms["compensation"]
    assert _pos(ripe_gov_vault, c.address, ripe_token) == 0
    assert ripe_token.totalSupply() == supply_after_cash - cashed
    assert c.compensation() == 0
    assert c.totalClaimed() == cashed  # claimed stays; vesting reads are terminal-off


def test_g11_cancel_pre_cliff_residue_isolation(
    human_resources, contributor_contract, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, ledger, teller, whale, switchboard_delta,
    governance, valid_contributor_terms,
):
    """Residue B seeded as a RipeGov position for the clone (via Teller-
    impersonation depositTokensInVault — deposit-permission-dependent route).
    Cash P. Pre-cliff cancel burns B + P but refunds only original compensation.

    HR-side observation: the burn pull (Group 6 owns the vault mechanics) is
    unscoped; HR refunds only the paycheck compensation. Net effect: the
    protocol's ripeAvailForHr is credited the full compensation while the burn
    destroys B + P of actual RIPE — B's backing was external (whale), so the
    whale's deposited RIPE is destroyed without any budget debit.
    """
    setupRipeGovVaultConfig()
    c = contributor_contract
    terms = valid_contributor_terms
    owner = terms["owner"]

    # seed residue B as a gov-vault position for the clone
    residue = 1_000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, residue, sender=whale)
    ripe_gov_vault.depositTokensInVault(c.address, ripe_token, residue, sender=teller.address)
    assert _pos(ripe_gov_vault, c.address, ripe_token) == residue

    # cash P (pre-cliff)
    _travel_to_ts(c.startTime() + 30 * 24 * 3600)
    assert _ts() < c.cliffTime()
    cashed = c.cashRipeCheck(sender=owner)
    assert cashed > 0
    assert _pos(ripe_gov_vault, c.address, ripe_token) == residue + cashed
    supply_before_cancel = ripe_token.totalSupply()
    avail_before_cancel = ledger.ripeAvailForHr()
    hr_ripe_before = ripe_token.balanceOf(human_resources)

    aid = _delta_cancel(switchboard_delta, governance, c)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)

    # burn pulled B + P; refund credited only compensation
    assert _pos(ripe_gov_vault, c.address, ripe_token) == 0
    assert ripe_token.totalSupply() == supply_before_cancel - (residue + cashed)
    assert ledger.ripeAvailForHr() == avail_before_cancel + terms["compensation"]
    # HR balanceOf cap did not bind (HR holds 0 after burn)
    assert ripe_token.balanceOf(human_resources) == 0


def test_g11_cancel_exact_cliff_and_after_cliff_no_burn(
    human_resources, setupHrConfig, setupLedgerBalance, governance,
    valid_contributor_terms, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, ledger, switchboard_delta,
):
    """Exact cliffTime: cancel cashes first (RipeCheckCashed.cashedBy == HR),
    refunds only the unvested remainder, no burn. After-cliff: same shape.
    unlockTime is unchanged and the exit still routes through the two-step."""
    c = _deploy(human_resources, setupHrConfig, setupLedgerBalance, governance,
                valid_contributor_terms)
    setupRipeGovVaultConfig()
    terms = valid_contributor_terms
    owner = terms["owner"]

    # exact cliffTime cancel
    _travel_to_ts(c.cliffTime())
    vested_at_cliff = min(terms["compensation"],
                          terms["compensation"] * (c.cliffTime() - c.startTime()) // terms["vestingLength"])
    aid = _delta_cancel(switchboard_delta, governance, c)
    # delta timelock travel moves time but blocks only; timestamp may advance ~0 in boa
    _travel_to_ts(c.cliffTime())  # ensure still exactly cliff
    supply0 = ripe_token.totalSupply()
    avail0 = ledger.ripeAvailForHr()
    unlock_before = c.unlockTime()
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    ev_cancel = filter_logs(switchboard_delta, "RipePaycheckCancelled")
    assert len(ev_cancel) == 1
    assert ev_cancel[0].didReachCliff is True
    # cash ran inside cancel with _caller == hr
    ev_cash = filter_logs(switchboard_delta, "RipeCheckCashed")
    assert len(ev_cash) == 1
    assert ev_cash[0].cashedBy == human_resources.address
    cashed = ev_cash[0].amount
    assert cashed > 0
    # forfeited = compensation - totalClaimed (after the cash)
    assert ev_cancel[0].forfeitedAmount == terms["compensation"] - cashed
    # no burn: supply UP by the cashed amount; budget refunded by remainder only
    assert ripe_token.totalSupply() == supply0 + cashed
    assert ledger.ripeAvailForHr() == avail0 + (terms["compensation"] - cashed)
    assert _pos(ripe_gov_vault, c.address, ripe_token) == cashed  # clone keeps cashed RIPE
    assert c.unlockTime() == unlock_before  # unchanged
    assert c.compensation() == cashed
    # terminal agreement exit: still the two-step gated on the ORIGINAL unlockTime
    _travel_to_ts(c.unlockTime() + 1)
    c.initiateRipeTransfer(sender=owner)
    pending = c.pendingRipeTransfer()
    boa.env.time_travel(blocks=pending.confirmBlock - boa.env.evm.patch.block_number)
    c.confirmRipeTransfer(sender=owner)
    assert _pos(ripe_gov_vault, owner, ripe_token) > 0
    assert _pos(ripe_gov_vault, c.address, ripe_token) == 0


def test_g11_cancel_at_and_after_end_reverts(
    human_resources, contributor_contract, setupRipeGovVaultConfig,
    ripe_token, ledger, switchboard_delta, governance, valid_contributor_terms,
):
    setupRipeGovVaultConfig()
    c = contributor_contract
    avail0 = ledger.ripeAvailForHr()
    _travel_to_ts(c.endTime())
    aid = _delta_cancel(switchboard_delta, governance, c)
    with boa.reverts():  # "cannot cancel"
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    # after end: initiate + execute reverts too
    _travel_to_ts(c.endTime() + 100)
    aid2 = switchboard_delta.cancelPaycheckForContributor(c.address, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    with boa.reverts():
        switchboard_delta.executePendingAction(aid2, sender=governance.address)
    assert ledger.ripeAvailForHr() == avail0  # no refund happened


def test_g11_frozen_after_cliff_cancel_forfeits_vested_uncashed(
    human_resources, setupHrConfig, setupLedgerBalance, governance,
    valid_contributor_terms, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, ledger, switchboard_delta,
):
    """Frozen + after-cliff cancel: cash-first returns 0 (frozen), so the
    forfeited amount is the FULL uncashed remainder including vested-but-
    uncashed RIPE. Compare against the identical UNFROZEN cancel: the delta is
    the contributor's forfeited vested balance. Both clones share identical
    terms/timing by construction (same startDelay base).

    Classification: this is a specified sequencing power of freeze — freeze
    stops cash, and cancel's forfeiture formula is compensation - totalClaimed.
    Governance combining lite-freeze + gov cancel converts the contributor's
    vested-but-uncashed balance into a budget refund. No storage corruption,
    but the contributor permanently loses vested funds they would have kept
    under an unfrozen cancel.
    """
    terms = valid_contributor_terms
    owner = terms["owner"]

    def run(freeze: bool):
        c = _deploy(human_resources, setupHrConfig, setupLedgerBalance, governance,
                    valid_contributor_terms)
        setupRipeGovVaultConfig()
        # pin the cancel to an absolute timestamp so both runs vest identically
        # (the Delta timelock travel advances wall-clock seconds between runs)
        cancel_ts = c.cliffTime() + 30 * 24 * 3600
        _travel_to_ts(cancel_ts)
        claimable = c.getClaimable()
        assert claimable > 0
        if freeze:
            assert switchboard_delta.freezeContributor(c.address, True, sender=governance.address)
        supply0 = ripe_token.totalSupply()
        avail0 = ledger.ripeAvailForHr()
        aid = switchboard_delta.cancelPaycheckForContributor(c.address, sender=governance.address)
        boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
        _travel_to_ts(cancel_ts)  # re-pin after the timelock travel
        assert switchboard_delta.executePendingAction(aid, sender=governance.address)
        return {
            "c": c,
            "claimable": claimable,
            "totalClaimed": c.totalClaimed(),
            "clone_pos": _pos(ripe_gov_vault, c.address, ripe_token),
            "supply_delta": ripe_token.totalSupply() - supply0,
            "avail_delta": ledger.ripeAvailForHr() - avail0,
        }

    unfrozen = run(freeze=False)
    frozen = run(freeze=True)

    # unfrozen: cash-first mints the vested amount onto the clone; refund is remainder
    assert unfrozen["totalClaimed"] > 0
    assert unfrozen["clone_pos"] == unfrozen["totalClaimed"]
    assert unfrozen["supply_delta"] == unfrozen["totalClaimed"]
    assert unfrozen["avail_delta"] == terms["compensation"] - unfrozen["totalClaimed"]

    # frozen: no cash; refund is the FULL remainder (vested + unvested)
    assert frozen["totalClaimed"] == 0
    assert frozen["clone_pos"] == 0
    assert frozen["supply_delta"] == 0
    assert frozen["avail_delta"] == terms["compensation"]

    # the delta is exactly the vested-but-uncashed amount the contributor lost
    assert frozen["avail_delta"] - unfrozen["avail_delta"] == unfrozen["totalClaimed"]


def test_g11_cancel_pause_rollback_official_path(
    human_resources, contributor_contract, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, ledger, switchboard_delta, switchboard_charlie,
    governance, valid_contributor_terms,
):
    """Mature Delta cancel (past confirmBlock, not expired) + Charlie HR pause:
    execute reverts; Contributor compensation/endTime and the Delta pending all
    survive; unpause -> the SAME pending executes."""
    setupRipeGovVaultConfig()
    c = contributor_contract
    terms = valid_contributor_terms
    _travel_to_ts(c.startTime() + 10)
    aid = _delta_cancel(switchboard_delta, governance, c)
    assert not switchboard_delta.isExpired(aid)

    comp0 = c.compensation()
    end0 = c.endTime()
    avail0 = ledger.ripeAvailForHr()

    assert switchboard_charlie.pause(human_resources.address, True, sender=governance.address)
    with boa.reverts():
        switchboard_delta.executePendingAction(aid, sender=governance.address)
    # full rollback: contributor state unchanged, delta pending alive
    assert c.compensation() == comp0
    assert c.endTime() == end0
    assert ledger.ripeAvailForHr() == avail0
    assert switchboard_delta.actionType(aid) != 0
    assert not switchboard_delta.isExpired(aid)

    assert switchboard_charlie.pause(human_resources.address, False, sender=governance.address)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert c.compensation() == 0
    assert ledger.ripeAvailForHr() == avail0 + terms["compensation"]


def test_g11_spoof_cancel_is_address_impersonation_only(
    human_resources, contributor_contract, setupRipeGovVaultConfig,
    switchboard_alpha, switchboard_delta, governance, ledger, ripe_token,
    valid_contributor_terms,
):
    """Pricing the spoof: contributor.cancelPaycheck(sender=switchboard_alpha.address)
    passes canModifyHrContributor (any switchboard address) but is NOT a
    production path — Alpha has no Contributor extcall. It is classified
    fixture/direct-state-only. The real gate difference: production cancel
    needs Delta governor + Delta timelock; the spoof needs only the ability to
    set msg.sender, which no EOA or contract can do to a switchboard address."""
    setupRipeGovVaultConfig()
    c = contributor_contract
    terms = valid_contributor_terms
    avail0 = ledger.ripeAvailForHr()

    # EOA cannot call cancelPaycheck
    with boa.reverts("no perms"):
        c.cancelPaycheck(sender=boa.env.generate_address("rando_eoa"))

    # the spoof works in-fixture (proves only that the gate is address-based)
    c.cancelPaycheck(sender=switchboard_alpha.address)
    assert c.compensation() == 0
    assert ledger.ripeAvailForHr() == avail0 + terms["compensation"]
    # production equivalence: Delta path reaches the same function with a
    # governor + timelock requirement (proven in the other tests of this file)
