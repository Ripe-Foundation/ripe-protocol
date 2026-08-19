import random

import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from conf_utils import assert_reverted_call, filter_logs
from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS
from contracts.modules import Contributor
from tests.core.humanResources.g11_proof_helpers import (
    HR_ID,
    charlie_pause,
    expected_vested,
    initiate_contributor,
    official_delta_budget,
    official_freeze,
    overflow_compensation,
    settle_unsettled_hr_grants,
    snapshot_econ,
    terms_tuple,
    travel_to_ts,
)


def _prep(setupRipeGovVaultConfig):
    setupRipeGovVaultConfig()


def _cash_ok(contributor, caller, ripe_token, ripe_gov_vault, ledger, human_resources, teller):
    owner = contributor.owner()
    before = snapshot_econ(
        contributor, ripe_token, ripe_gov_vault, ledger, human_resources, owner, teller
    )
    claimable = contributor.getClaimable()
    vested = contributor.getTotalVested()
    assert claimable == max(vested - contributor.totalClaimed(), 0)
    minted = contributor.cashRipeCheck(sender=caller)
    events = filter_logs(contributor, "RipeCheckCashed")
    after = snapshot_econ(
        contributor, ripe_token, ripe_gov_vault, ledger, human_resources, owner, teller
    )
    assert minted == claimable
    assert after["supply"] == before["supply"] + minted
    assert after["clone_vault"] == before["clone_vault"] + minted
    assert after["owner_ripe"] == before["owner_ripe"]
    assert after["owner_vault"] == before["owner_vault"]
    assert after["budget"] == before["budget"]
    assert after["claimed"] == before["claimed"] + minted
    assert after["hr_ripe"] == before["hr_ripe"]
    assert after["allowance"] == 0
    if minted:
        assert len(events) == 1
        assert events[0].owner == owner
        assert events[0].cashedBy == caller
        assert events[0].amount == minted
    else:
        assert events == []
    return minted, before, after


def test_g11_cash_identity_owner_timestamp_walk(
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
    start, cliff, end = c.startTime(), c.cliffTime(), c.endTime()
    comp = c.compensation()

    travel_to_ts(start - 1)
    assert c.getTotalVested() == 0
    minted, _, _ = _cash_ok(
        c, owner_address, ripe_token, ripe_gov_vault, ledger, human_resources, teller
    )
    assert minted == 0

    travel_to_ts(start)
    assert c.getTotalVested() == 0
    minted, _, _ = _cash_ok(
        c, owner_address, ripe_token, ripe_gov_vault, ledger, human_resources, teller
    )
    assert minted == 0

    travel_to_ts(start + 1)
    assert boa.env.evm.patch.timestamp < cliff
    vested = expected_vested(comp, start, end, start + 1)
    assert c.getTotalVested() == vested
    assert vested > 0
    minted, _, _ = _cash_ok(
        c, owner_address, ripe_token, ripe_gov_vault, ledger, human_resources, teller
    )
    assert minted == vested

    travel_to_ts(cliff)
    remaining_at_cliff = expected_vested(comp, start, end, cliff) - c.totalClaimed()
    minted, _, after_cliff = _cash_ok(
        c, owner_address, ripe_token, ripe_gov_vault, ledger, human_resources, teller
    )
    assert minted == remaining_at_cliff
    assert after_cliff["claimed"] == expected_vested(comp, start, end, cliff)

    travel_to_ts(end)
    remaining_at_end = comp - c.totalClaimed()
    minted, _, after = _cash_ok(
        c, owner_address, ripe_token, ripe_gov_vault, ledger, human_resources, teller
    )
    assert minted == remaining_at_end
    assert after["claimed"] == comp
    assert human_resources.hrGrant(c.address).settled

    travel_to_ts(end + 1)
    minted, _, _ = _cash_ok(
        c, owner_address, ripe_token, ripe_gov_vault, ledger, human_resources, teller
    )
    assert minted == 0

    minted2, _, _ = _cash_ok(
        c, owner_address, ripe_token, ripe_gov_vault, ledger, human_resources, teller
    )
    assert minted2 == 0


def test_g11_cash_identity_manager_and_delta_governor(
    contributor_contract,
    setupRipeGovVaultConfig,
    manager_address,
    owner_address,
    switchboard_delta,
    governance,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
    teller,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.startTime() + 1)
    minted, _, _ = _cash_ok(
        c, manager_address, ripe_token, ripe_gov_vault, ledger, human_resources, teller
    )
    assert minted > 0

    travel_to_ts(c.cliffTime())
    before = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    claimable = c.getClaimable()
    assert claimable > 0
    assert switchboard_delta.cashRipeCheckForContributor(
        c.address, sender=governance.address
    )
    cash_logs = filter_logs(c, "RipeCheckCashed")
    sb_logs = filter_logs(switchboard_delta, "RipeCheckCashedFromSwitchboard")
    assert len(sb_logs) == 1
    assert sb_logs[0].cashedBy == governance.address
    assert sb_logs[0].amount == claimable
    if cash_logs:
        assert cash_logs[0].cashedBy == switchboard_delta.address
        assert cash_logs[0].amount == claimable
    after = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    assert after["supply"] == before["supply"] + claimable
    assert after["clone_vault"] == before["clone_vault"] + claimable
    assert after["budget"] == before["budget"]
    assert after["owner_ripe"] == before["owner_ripe"]


def test_g11_cash_frozen_returns_zero_no_mint(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    switchboard_delta,
    governance,
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
    official_freeze(switchboard_delta, governance, c, True)
    before = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    assert c.cashRipeCheck(sender=owner_address) == 0
    after = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    assert after == before
    assert filter_logs(c, "RipeCheckCashed") == []


def test_g11_cash_charlie_hr_pause_reverts_no_mint(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    switchboard_charlie,
    governance,
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
    before = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    charlie_pause(switchboard_charlie, governance, human_resources.address, True)
    with pytest.raises(BoaError) as exc:
        c.cashRipeCheck(sender=owner_address)
    assert_reverted_call(exc.value, "contract paused", c)
    after = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    assert after == before
    charlie_pause(switchboard_charlie, governance, human_resources.address, False)
    minted, _, _ = _cash_ok(
        c, owner_address, ripe_token, ripe_gov_vault, ledger, human_resources, teller
    )
    assert minted > 0


def test_g11_cash_hq_mint_gate_off_reverts_no_mint(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    ripe_hq,
    governance,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
    teller,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.startTime() + 1)
    assert ripe_hq.canMintRipe(human_resources.address)
    ripe_hq.setMintingEnabled(False, sender=governance.address)
    assert not ripe_hq.canMintRipe(human_resources.address)
    before = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    with pytest.raises(BoaError) as exc:
        c.cashRipeCheck(sender=owner_address)
    assert_reverted_call(exc.value, "cannot mint", c)
    after = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    assert after == before
    ripe_hq.setMintingEnabled(True, sender=governance.address)
    minted, _, _ = _cash_ok(
        c, owner_address, ripe_token, ripe_gov_vault, ledger, human_resources, teller
    )
    assert minted > 0


def test_g11_cash_unauthorized_eoa_reverts(contributor_contract, setupRipeGovVaultConfig, alice):
    _prep(setupRipeGovVaultConfig)
    with boa.reverts("no perms"):
        contributor_contract.cashRipeCheck(sender=alice)


def test_g11_hr_layer_uncapped_cash_is_clone_impersonation(
    contributor_contract,
    setupRipeGovVaultConfig,
    human_resources,
    ripe_token,
    ripe_gov_vault,
    ledger,
    switchboard_delta,
    governance,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    extra = c.compensation() * 2
    budget_before = ledger.ripeAvailForHr()
    reserved_before = ledger.hrReservedCompensation()
    liability_before = ledger.hrCancelCreditLiability()
    g_before = human_resources.hrGrant(c.address)
    pos_before = ripe_gov_vault.getTotalAmountForUser(c, ripe_token)
    with boa.reverts("hr reserve underflow"):
        human_resources.cashRipeCheck(extra, c.depositLockDuration(), sender=c.address)
    assert ripe_gov_vault.getTotalAmountForUser(c, ripe_token) == pos_before
    assert c.totalClaimed() == 0
    assert ledger.ripeAvailForHr() == budget_before
    assert ledger.hrReservedCompensation() == reserved_before
    assert ledger.hrCancelCreditLiability() == liability_before
    assert human_resources.hrGrant(c.address) == g_before


def test_g11_nested_ripegov_pause_rolls_back_then_retry(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    switchboard_charlie,
    governance,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
    teller,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.startTime() + 1)
    before = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    charlie_pause(switchboard_charlie, governance, ripe_gov_vault.address, True)
    with pytest.raises(BoaError) as exc:
        c.cashRipeCheck(sender=owner_address)
    assert_reverted_call(exc.value, "contract paused", c)
    after = snapshot_econ(
        c, ripe_token, ripe_gov_vault, ledger, human_resources, owner_address, teller
    )
    assert after == before
    charlie_pause(switchboard_charlie, governance, ripe_gov_vault.address, False)
    minted, _, _ = _cash_ok(
        c, owner_address, ripe_token, ripe_gov_vault, ledger, human_resources, teller
    )
    assert minted > 0


def test_g11_teller_pause_does_not_block_trusted_cash(
    contributor_contract,
    setupRipeGovVaultConfig,
    owner_address,
    switchboard_charlie,
    governance,
    ripe_token,
    ripe_gov_vault,
    ledger,
    human_resources,
    teller,
):
    _prep(setupRipeGovVaultConfig)
    c = contributor_contract
    travel_to_ts(c.startTime() + 1)
    charlie_pause(switchboard_charlie, governance, teller.address, True)
    minted, _, _ = _cash_ok(
        c, owner_address, ripe_token, ripe_gov_vault, ledger, human_resources, teller
    )
    assert minted > 0
    charlie_pause(switchboard_charlie, governance, teller.address, False)


def test_g11_overflow_compensation_safe_cash_control(
    deployedContributor,
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
    # Vest-safe and share-safe: first empty-vault deposit does amount * 1e8.
    safe = 10**40
    terms = dict(valid_contributor_terms)
    terms["compensation"] = safe
    setupHrConfig(_maxCompensation=0)
    setupLedgerBalance(safe)
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
    c = Contributor.at(
        filter_logs(human_resources, "NewContributorConfirmed")[0].contributorAddr
    )
    travel_to_ts(c.startTime() + 2)
    vested = c.getTotalVested()
    assert vested == expected_vested(safe, c.startTime(), c.endTime(), c.startTime() + 2)
    minted, _, _ = _cash_ok(
        c, terms["owner"], ripe_token, ripe_gov_vault, ledger, human_resources, teller
    )
    assert minted == vested


def test_g11_overflow_compensation_cash_stays_callable(
    valid_contributor_terms,
    setupHrConfig,
    setupLedgerBalance,
    human_resources,
    governance,
):
    """Create-gate: ranked 2**255 compensation is rejected at initiate."""
    _, overflow_comp = overflow_compensation(2)
    terms = dict(valid_contributor_terms)
    terms["compensation"] = overflow_comp
    setupHrConfig(_maxCompensation=0)
    setupLedgerBalance(overflow_comp)
    assert human_resources.areValidContributorTerms(*terms_tuple(terms)) is False
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


def test_g11_overflow_clone_pre_cliff_cancel_still_recovers(
    valid_contributor_terms,
    setupHrConfig,
    setupLedgerBalance,
    human_resources,
    governance,
):
    """Ranked 2**255 compensation is rejected at initiate."""
    _, overflow_comp = overflow_compensation(2)
    terms = dict(valid_contributor_terms)
    terms["compensation"] = overflow_comp
    setupHrConfig(_maxCompensation=0)
    setupLedgerBalance(overflow_comp)
    assert human_resources.areValidContributorTerms(*terms_tuple(terms)) is False
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


def test_g11_overflow_clone_after_cliff_cancel_also_bricks(
    valid_contributor_terms,
    setupHrConfig,
    setupLedgerBalance,
    human_resources,
    governance,
):
    """Ranked 2**255 compensation is rejected at initiate."""
    _, overflow_comp = overflow_compensation(2)
    terms = dict(valid_contributor_terms)
    terms["compensation"] = overflow_comp
    setupHrConfig(_maxCompensation=0)
    setupLedgerBalance(overflow_comp)
    assert human_resources.areValidContributorTerms(*terms_tuple(terms)) is False
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


def test_g11_aggregate_compensation_sum_two_clones(
    valid_contributor_terms,
    setupHrConfig,
    setupLedgerBalance,
    human_resources,
    governance,
    ledger,
    switchboard_delta,
):
    setupHrConfig(_maxCompensation=0)
    overflow = 2**255
    terms_bad = dict(valid_contributor_terms)
    terms_bad["compensation"] = overflow
    setupLedgerBalance(overflow)
    assert human_resources.areValidContributorTerms(*terms_tuple(terms_bad)) is False
    with boa.reverts("invalid terms"):
        initiate_contributor(human_resources, governance, terms_bad)

    cap = MAX_UINT256 // 2
    for i in range(2):
        setupLedgerBalance(cap)
        terms = dict(valid_contributor_terms)
        terms["owner"] = "0x" + f"{0x31 + i:02x}" * 20
        terms["manager"] = "0x" + f"{0x41 + i:02x}" * 20
        terms["compensation"] = cap
        aid = initiate_contributor(human_resources, governance, terms)
        boa.env.time_travel(blocks=human_resources.actionTimeLock())
        assert human_resources.confirmNewContributor(aid, sender=governance.address)
    assert ledger.numContributors() == 3
    total = human_resources.getTotalCompensation()
    assert total == cap * 2
    assert total == MAX_UINT256 - 1
    assert human_resources.getTotalClaimed() == 0


def _confirm_clone(human_resources, governance, terms):
    aid = initiate_contributor(human_resources, governance, terms)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid, sender=governance.address)
    return Contributor.at(
        filter_logs(human_resources, "NewContributorConfirmed")[0].contributorAddr
    )


def test_g11_vest_helper_matches_python_muldiv(
    valid_contributor_terms,
    setupHrConfig,
    setupLedgerBalance,
    human_resources,
    governance,
    switchboard_delta,
    ledger,
):
    setupHrConfig(
        _maxCompensation=0,
        _minCliffLength=0,
        _maxStartDelay=0,
        _minVestingLength=0,
        _maxVestingLength=0,
    )
    fixture_l = valid_contributor_terms["vestingLength"]
    cases = [
        (10**40, fixture_l, 2),
        (20_000_000 * EIGHTEEN_DECIMALS, 2, 1),
        (2**128 - 1, 2**128, 2**128 - 1),
        (1, 2**128, 1),
        (MAX_UINT256 // 2, fixture_l, 2),
    ]
    rng = random.Random(11)
    for _ in range(5):
        vest_len = rng.randint(2, 10**6)
        compensation = rng.randint(1, 10**30)
        elapsed = rng.randint(1, vest_len - 1)
        cases.append((compensation, vest_len, elapsed))

    for compensation, vest_len, elapsed in cases:
        with boa.env.anchor():
            setupLedgerBalance(compensation)
            terms = dict(valid_contributor_terms)
            terms["compensation"] = compensation
            terms["startDelay"] = 0
            terms["vestingLength"] = vest_len
            terms["unlockLength"] = vest_len
            terms["cliffLength"] = 1
            c = _confirm_clone(human_resources, governance, terms)
            travel_to_ts(c.startTime() + elapsed)
            expected = compensation * elapsed // vest_len
            assert c.getTotalVested() == expected


def test_g11_custom_template_saturates_both_aggregate_views(
    valid_contributor_terms,
    setupHrConfig,
    setupLedgerBalance,
    human_resources,
    governance,
    switchboard_delta,
    ledger,
):
    settle_unsettled_hr_grants(human_resources, ledger)
    template = boa.load_partial(
        "tests/core/humanResources/Group11OverflowViewContributor.vy"
    ).deploy_as_blueprint()
    setupHrConfig(_contribTemplate=template.address, _maxCompensation=0)
    official_delta_budget(switchboard_delta, governance, valid_contributor_terms["compensation"] * 2)
    addrs = []
    for i in range(2):
        terms = dict(valid_contributor_terms)
        terms["owner"] = "0x" + f"{0x51 + i:02x}" * 20
        terms["manager"] = "0x" + f"{0x61 + i:02x}" * 20
        aid = initiate_contributor(human_resources, governance, terms)
        boa.env.time_travel(blocks=human_resources.actionTimeLock())
        assert human_resources.confirmNewContributor(aid, sender=governance.address)
        addrs.append(filter_logs(human_resources, "NewContributorConfirmed")[0].contributorAddr)
    assert human_resources.getTotalCompensation() == MAX_UINT256
    assert human_resources.getTotalClaimed() == MAX_UINT256
    assert ledger.hrReservedCompensation() == valid_contributor_terms["compensation"] * 2
    assert ledger.hrCancelCreditLiability() == valid_contributor_terms["compensation"] * 2
    for addr in addrs:
        g = human_resources.hrGrant(addr)
        assert g.initialized and not g.settled
        assert g.remainingMintable == valid_contributor_terms["compensation"]


def test_g11_hq_mint_gate_is_hr_id_15(ripe_hq, human_resources):
    assert ripe_hq.getAddr(HR_ID) == human_resources.address
    assert ripe_hq.canMintRipe(human_resources.address)


def test_g11_hostile_cash_is_per_clone_not_global_mintable(
    valid_contributor_terms,
    setupHrConfig,
    setupLedgerBalance,
    setupRipeGovVaultConfig,
    human_resources,
    governance,
    ledger,
):
    """A exhausted clone cannot mint against B's remaining mintable."""
    setupRipeGovVaultConfig()
    settle_unsettled_hr_grants(human_resources, ledger)
    setupHrConfig()
    a_terms = dict(valid_contributor_terms)
    a_terms["owner"] = "0x" + "e1" * 20
    a_terms["manager"] = "0x" + "e2" * 20
    b_terms = dict(valid_contributor_terms)
    b_terms["owner"] = "0x" + "e3" * 20
    b_terms["manager"] = "0x" + "e4" * 20
    setupLedgerBalance(a_terms["compensation"] + b_terms["compensation"])
    a = _confirm_clone(human_resources, governance, a_terms)
    b = _confirm_clone(human_resources, governance, b_terms)
    g_a = human_resources.hrGrant(a.address)
    g_b = human_resources.hrGrant(b.address)
    assert g_a.remainingMintable == a.compensation() > 0
    assert g_b.remainingMintable == b.compensation() > 0

    assert human_resources.cashRipeCheck(
        g_a.remainingMintable, a.depositLockDuration(), sender=a.address
    )
    g_a_after = human_resources.hrGrant(a.address)
    assert g_a_after.remainingMintable == 0
    assert ledger.hrReservedCompensation() == g_b.remainingMintable
    assert ledger.hrReservedCompensation() > 0

    reserved = ledger.hrReservedCompensation()
    liability = ledger.hrCancelCreditLiability()
    budget = ledger.ripeAvailForHr()
    g_b_snap = human_resources.hrGrant(b.address)
    g_a_snap = human_resources.hrGrant(a.address)
    with boa.reverts("hr reserve underflow"):
        human_resources.cashRipeCheck(1, a.depositLockDuration(), sender=a.address)
    assert ledger.hrReservedCompensation() == reserved
    assert ledger.hrCancelCreditLiability() == liability
    assert ledger.ripeAvailForHr() == budget
    assert human_resources.hrGrant(b.address) == g_b_snap
    assert human_resources.hrGrant(a.address) == g_a_snap


def test_g11_custom_template_max_cliff_still_consumes_mintable(
    valid_contributor_terms,
    setupHrConfig,
    setupLedgerBalance,
    setupRipeGovVaultConfig,
    human_resources,
    governance,
    ledger,
    switchboard_delta,
):
    """Stored cliff, not clone cliffTime()=MAX, governs mintable and liability."""
    setupRipeGovVaultConfig()
    settle_unsettled_hr_grants(human_resources, ledger)
    template = boa.load_partial(
        "tests/core/humanResources/Group11OverflowViewContributor.vy"
    ).deploy_as_blueprint()
    setupHrConfig(_contribTemplate=template.address, _maxCompensation=0)
    a_terms = dict(valid_contributor_terms)
    a_terms["owner"] = "0x" + "f1" * 20
    a_terms["manager"] = "0x" + "f2" * 20
    b_terms = dict(valid_contributor_terms)
    b_terms["owner"] = "0x" + "f3" * 20
    b_terms["manager"] = "0x" + "f4" * 20
    official_delta_budget(
        switchboard_delta, governance, a_terms["compensation"] + b_terms["compensation"]
    )
    aid_a = initiate_contributor(human_resources, governance, a_terms)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid_a, sender=governance.address)
    confirm_ts = boa.env.evm.patch.timestamp
    addr_a = filter_logs(human_resources, "NewContributorConfirmed")[0].contributorAddr
    aid_b = initiate_contributor(human_resources, governance, b_terms)
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(aid_b, sender=governance.address)
    addr_b = filter_logs(human_resources, "NewContributorConfirmed")[0].contributorAddr

    clone_a = boa.load_partial(
        "tests/core/humanResources/Group11OverflowViewContributor.vy"
    ).at(addr_a)
    g_a = human_resources.hrGrant(addr_a)
    expected_cliff = confirm_ts + a_terms["startDelay"] + a_terms["cliffLength"]
    assert g_a.cliffTime == expected_cliff
    assert clone_a.cliffTime() == MAX_UINT256
    assert g_a.remainingMintable == a_terms["compensation"]
    assert g_a.cancelCreditLiability == a_terms["compensation"]

    p = a_terms["compensation"] // 10
    assert p > 0
    assert boa.env.evm.patch.timestamp < g_a.cliffTime
    reserved_before = ledger.hrReservedCompensation()
    liability_before = ledger.hrCancelCreditLiability()
    assert human_resources.cashRipeCheck(
        p, a_terms["depositLockDuration"], sender=addr_a
    )
    g_pre = human_resources.hrGrant(addr_a)
    assert g_pre.remainingMintable == a_terms["compensation"] - p
    assert g_pre.cancelCreditLiability == a_terms["compensation"]
    assert ledger.hrReservedCompensation() == reserved_before - p
    assert ledger.hrCancelCreditLiability() == liability_before
    assert clone_a.cliffTime() == MAX_UINT256

    travel_to_ts(g_a.cliffTime)
    p2 = a_terms["compensation"] // 10
    assert human_resources.cashRipeCheck(
        p2, a_terms["depositLockDuration"], sender=addr_a
    )
    g_post = human_resources.hrGrant(addr_a)
    g_b = human_resources.hrGrant(addr_b)
    assert g_post.remainingMintable == a_terms["compensation"] - p - p2
    assert g_post.cancelCreditLiability == g_post.remainingMintable
    assert ledger.hrReservedCompensation() == reserved_before - p - p2
    assert ledger.hrCancelCreditLiability() == g_post.remainingMintable + g_b.cancelCreditLiability
    assert clone_a.cliffTime() == MAX_UINT256

    leftover = g_post.remainingMintable
    g_b_snap = human_resources.hrGrant(addr_b)
    reserved = ledger.hrReservedCompensation()
    liability = ledger.hrCancelCreditLiability()
    with boa.reverts("hr reserve underflow"):
        human_resources.cashRipeCheck(
            leftover + 1, a_terms["depositLockDuration"], sender=addr_a
        )
    assert human_resources.hrGrant(addr_a) == g_post
    assert human_resources.hrGrant(addr_b) == g_b_snap
    assert ledger.hrReservedCompensation() == reserved
    assert ledger.hrCancelCreditLiability() == liability
