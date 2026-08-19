"""Group 11 (kimi) proof tests — never-skip #1: cash / vest identity.

All contributors are deployed through HumanResources (official path). Cash is
exercised as owner, manager, one Delta lite wrapper call (lite signer granted
through MissionControl), and one Delta governor wrapper call. Boundary times
are hit exactly; frozen / HR-paused / HQ mint-gate-off are exercised; the
individual vesting overflow is measured at elapsed >= 2.

Adjacent positive control: unfrozen, past start, honest getClaimable with
mint == vault credit == totalClaimed delta.
"""
import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from contracts.modules import Contributor


@pytest.fixture
def fresh_contributor(contributor_contract):
    """A fresh handle on the deployed clone -> fresh event-log cursor."""
    return Contributor.at(contributor_contract.address)


VESTING = 2 * 365 * 24 * 3600  # 2y fixture vesting


def _vault_assets(vault, user, asset):
    """RipeGov userBalances are shares (PRECISION offset); convert to asset."""
    shares = vault.userBalances(user, asset)
    if shares == 0:
        return 0
    return vault.sharesToAmount(asset, shares, False)


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


def _ts():
    return boa.env.evm.patch.timestamp


def _travel_to_ts(t):
    now = _ts()
    if now < t:
        boa.env.time_travel(seconds=t - now)
    assert _ts() >= t


def _fresh_log_events(c_handle, event_name):
    """Event cursors are per-handle (and a no-event tx can rewind a used one),
    so read logs through a brand-new handle after exactly one emitting tx."""
    return filter_logs(Contributor.at(c_handle.address), event_name)


def test_g11_cash_boundary_identity_owner_manager_delta(
    human_resources, fresh_contributor, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, ledger, teller,
    owner_address, manager_address, alice,
    switchboard_delta, switchboard_alpha, mission_control, governance,
    valid_contributor_terms,
):
    """Cash identity at vesting boundaries: owner, manager, Delta lite, Delta gov."""
    setupRipeGovVaultConfig()  # idempotent per test
    c = fresh_contributor
    terms = valid_contributor_terms

    # --- before startTime: 0 claimable, no mint, return 0
    assert _ts() < c.startTime()
    supply0 = ripe_token.totalSupply()
    assert c.cashRipeCheck(sender=owner_address) == 0
    assert ripe_token.totalSupply() == supply0
    assert c.totalClaimed() == 0
    assert _vault_assets(ripe_gov_vault, c.address, ripe_token) == 0

    # --- exact startTime: vested == 0 (timestamp <= startTime), no mint
    _travel_to_ts(c.startTime())
    assert c.getTotalVested() == 0
    assert c.cashRipeCheck(sender=manager_address) == 0
    assert ripe_token.totalSupply() == supply0

    # --- first second after start: floored vest, even though before cliff
    _travel_to_ts(c.startTime() + 1)
    expected1 = terms["compensation"] // terms["vestingLength"]
    assert c.getTotalVested() == expected1
    assert _ts() < c.cliffTime()  # pre-cliff cash is allowed by formula
    hr_avail0 = ledger.ripeAvailForHr()
    amt1 = c.cashRipeCheck(sender=owner_address)
    # NOTE: read the event immediately after the emitting tx — any later call
    # through this handle (even a view) can disturb titanoboa's log cursor.
    ev = filter_logs(c, "RipeCheckCashed")
    assert len(ev) == 1 and ev[0].amount == amt1 and ev[0].cashedBy == owner_address
    assert amt1 == expected1
    # conservation: mint == clone vault credit == totalClaimed delta; budget unchanged
    assert ripe_token.totalSupply() == supply0 + amt1
    assert _vault_assets(ripe_gov_vault, c.address, ripe_token) == amt1
    assert c.totalClaimed() == amt1
    assert ledger.ripeAvailForHr() == hr_avail0
    assert ripe_token.balanceOf(human_resources) == 0  # mint passes through to vault
    assert ripe_token.allowance(human_resources, teller) == 0
    # owner ERC-20 and owner vault unchanged
    assert ripe_token.balanceOf(owner_address) == 0
    assert _vault_assets(ripe_gov_vault, owner_address, ripe_token) == 0

    # (event was read above, immediately after the emitting tx)
    # --- second cash in the same timestamp: 0, no mint
    assert c.cashRipeCheck(sender=owner_address) == 0
    assert ripe_token.totalSupply() == supply0 + amt1
    assert c.totalClaimed() == amt1

    # --- exact cliffTime: no special behavior in formula (cliff not read)
    _travel_to_ts(c.cliffTime())
    vested_at_cliff = min(terms["compensation"],
                          terms["compensation"] * (c.cliffTime() - c.startTime()) // terms["vestingLength"])
    assert c.getTotalVested() == vested_at_cliff
    amt2 = c.cashRipeCheck(sender=manager_address)
    assert amt2 == vested_at_cliff - amt1
    assert _vault_assets(ripe_gov_vault, c.address, ripe_token) == amt1 + amt2

    # --- Delta lite wrapper cash: grant lite signer, cash via Delta extcall
    mission_control.setCanPerformLiteAction(alice, True, sender=switchboard_alpha.address)
    assert mission_control.canPerformLiteAction(alice)
    _travel_to_ts(c.cliffTime() + 100)
    claimable3 = c.getClaimable()
    assert claimable3 > 0
    assert switchboard_delta.cashRipeCheckForContributor(c.address, sender=alice)
    # clone-side RipeCheckCashed.cashedBy is the Delta address (the extcall caller);
    # Delta emits its own event with the lite signer as cashedBy
    ev = filter_logs(switchboard_delta, "RipeCheckCashedFromSwitchboard")
    assert len(ev) == 1
    assert ev[0].contributor == c.address
    assert ev[0].cashedBy == alice
    assert ev[0].amount == claimable3
    assert c.totalClaimed() == amt1 + amt2 + claimable3

    # --- Delta governor wrapper cash
    _travel_to_ts(c.cliffTime() + 200)
    claimable4 = c.getClaimable()
    assert claimable4 > 0
    assert switchboard_delta.cashRipeCheckForContributor(c.address, sender=governance.address)
    assert c.totalClaimed() == amt1 + amt2 + claimable3 + claimable4

    # --- unauthorized EOA reverts
    with boa.reverts("no perms"):
        c.cashRipeCheck(sender=boa.env.generate_address("rando"))

    # --- exact endTime: full remaining
    _travel_to_ts(c.endTime())
    claimed_before = c.totalClaimed()
    remaining = terms["compensation"] - claimed_before
    assert c.getTotalVested() == terms["compensation"]
    amt5 = c.cashRipeCheck(sender=owner_address)
    assert amt5 == remaining
    assert c.totalClaimed() == terms["compensation"]
    assert _vault_assets(ripe_gov_vault, c.address, ripe_token) == terms["compensation"]
    assert human_resources.hrGrant(c.address).settled

    # --- after end: 0, no mint
    _travel_to_ts(c.endTime() + 10_000)
    supply_end = ripe_token.totalSupply()
    assert c.cashRipeCheck(sender=owner_address) == 0
    assert ripe_token.totalSupply() == supply_end
    # budget never moved by cash
    assert ledger.ripeAvailForHr() == hr_avail0


def test_g11_cash_frozen_returns_zero_no_mint(
    human_resources, fresh_contributor, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, switchboard_delta, governance, owner_address,
):
    """Frozen cash returns 0 (not a revert), no mint, no event."""
    setupRipeGovVaultConfig()  # idempotent per test
    c = fresh_contributor
    _travel_to_ts(c.startTime() + 30 * 24 * 3600)
    pre_claimable = c.getClaimable()
    assert pre_claimable > 0
    assert switchboard_delta.freezeContributor(c.address, True, sender=governance.address)
    supply0 = ripe_token.totalSupply()
    assert c.cashRipeCheck(sender=owner_address) == 0
    assert ripe_token.totalSupply() == supply0
    assert c.totalClaimed() == 0
    assert _vault_assets(ripe_gov_vault, c.address, ripe_token) == 0
    # unfreeze restores cash (adjacent control)
    assert switchboard_delta.freezeContributor(c.address, False, sender=governance.address)
    amt = c.cashRipeCheck(sender=owner_address)
    assert len(filter_logs(c, "RipeCheckCashed")) == 1
    assert amt == pre_claimable
    assert c.totalClaimed() == pre_claimable


def test_g11_cash_hr_paused_reverts_production_path(
    human_resources, fresh_contributor, setupRipeGovVaultConfig,
    ripe_gov_vault, ripe_token, switchboard_charlie, governance, owner_address,
):
    """HR department pause via Charlie pause (production write) -> cash reverts, no mint."""
    setupRipeGovVaultConfig()  # idempotent per test
    c = fresh_contributor
    _travel_to_ts(c.startTime() + 30 * 24 * 3600)
    assert c.getClaimable() > 0
    assert switchboard_charlie.pause(human_resources.address, True, sender=governance.address)
    assert human_resources.isPaused()
    supply0 = ripe_token.totalSupply()
    with boa.reverts():  # HR.cashRipeCheck "contract paused" (Vyper dev-string propagation is unreliable)
        c.cashRipeCheck(sender=owner_address)
    assert ripe_token.totalSupply() == supply0
    assert c.totalClaimed() == 0
    # unpause -> cash works again
    assert switchboard_charlie.pause(human_resources.address, False, sender=governance.address)
    amt = c.cashRipeCheck(sender=owner_address)
    assert amt > 0
    assert ripe_token.totalSupply() == supply0 + amt


def test_g11_cash_hq_mint_gate_off_reverts_config_liveness(
    human_resources, fresh_contributor, setupRipeGovVaultConfig,
    ripe_token, ripe_hq, governance, owner_address,
):
    """HQ mint-gate off (setMintingEnabled False) -> cash reverts; no clone-side
    escape except governance re-enabling. Config-dependent liveness."""
    setupRipeGovVaultConfig()  # idempotent per test
    c = fresh_contributor
    _travel_to_ts(c.startTime() + 30 * 24 * 3600)
    assert c.getClaimable() > 0
    assert ripe_hq.canMintRipe(human_resources.address)
    ripe_hq.setMintingEnabled(False, sender=governance.address)
    assert not ripe_hq.canMintRipe(human_resources.address)
    supply0 = ripe_token.totalSupply()
    with boa.reverts():  # RipeToken.mint "cannot mint" via HQ gate
        c.cashRipeCheck(sender=owner_address)
    assert ripe_token.totalSupply() == supply0
    assert c.totalClaimed() == 0
    # re-enable -> cash works
    ripe_hq.setMintingEnabled(True, sender=governance.address)
    amt = c.cashRipeCheck(sender=owner_address)
    assert amt > 0


def test_g11_individual_vesting_overflow_bricks_cash_and_after_cliff_cancel(
    human_resources, setupHrConfig, setupLedgerBalance, governance,
    valid_contributor_terms,
):
    """Ranked 2**255 compensation is rejected at initiate."""
    comp = MAX_UINT256 // 2 + 1
    terms = dict(valid_contributor_terms)
    terms["compensation"] = comp
    setupHrConfig(_maxCompensation=0)
    setupLedgerBalance(comp)
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(
            terms["owner"], terms["manager"], comp, terms["startDelay"],
            terms["vestingLength"], terms["cliffLength"], terms["unlockLength"],
            terms["depositLockDuration"], sender=governance.address,
        )


def test_g11_aggregate_views_overflow_two_clones(
    human_resources, setupHrConfig, setupLedgerBalance, governance,
    valid_contributor_terms,
):
    """Two 2**255 stock clones are rejected at initiate."""
    comp = MAX_UINT256 // 2 + 1
    terms = dict(valid_contributor_terms)
    terms["compensation"] = comp
    setupHrConfig(_maxCompensation=0)
    setupLedgerBalance(comp)
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(
            terms["owner"], terms["manager"], comp, terms["startDelay"],
            terms["vestingLength"], terms["cliffLength"], terms["unlockLength"],
            terms["depositLockDuration"], sender=governance.address,
        )
