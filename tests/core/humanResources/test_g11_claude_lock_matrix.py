"""Group 11 (Claude) never-skip #2 -- the cash-clamps / transfer-raw lock matrix.

`depositLockDuration` is chosen once at `initiateNewContributor`, is never read by
`_areValidContributorTerms` or `Contributor.__init__`, and has no setter. This file
measures what the two legs actually do with it.
"""

import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS
from conf_utils import assert_reverted_call, filter_logs

from g11_claude_helpers import (
    make_contributor,
    position,
    set_budget,
    set_hr_config,
    term_args,
    terms,
    travel_to,
    unlock_block,
)

VAULT_MIN = 100
VAULT_MAX = 1_000
SEED = 10 * EIGHTEEN_DECIMALS


def _clamped(duration):
    return min(max(VAULT_MIN, duration), VAULT_MAX)


def _build(hr, mc, sbd, tpl, ledger, gov_, owner, duration):
    t = terms(owner=owner, depositLockDuration=duration)
    return make_contributor(hr, mc, sbd, tpl, ledger, gov_, t)


def _cash_and_initiate(c, ripe_gov_vault, ripe_token, owner):
    """Cash once past the cliff, then move past unlockTime and initiate."""
    travel_to(c.cliffTime())
    cashed = c.cashRipeCheck(sender=owner)
    assert cashed > 0
    cash_block = boa.env.evm.patch.block_number
    travel_to(c.unlockTime() + 1)
    c.initiateRipeTransfer(False, sender=owner)
    return cashed, cash_block


@pytest.mark.parametrize(
    "duration",
    [0, 50, VAULT_MIN, VAULT_MAX, VAULT_MAX + 1],
    ids=["zero", "below_min", "exact_min", "exact_max", "max_plus_one"],
)
def test_g11c_lock_matrix_fresh_owner_prevshares_below_precision(
    duration,
    human_resources,
    mission_control,
    switchboard_delta,
    contributor_template,
    ledger,
    governance,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    alice,
):
    """prevShares < PRECISION: owner unlock is `block.number + rawDuration`, unclamped
    on BOTH sides, while the clone's cash leg was clamped into [min, max]."""
    setupRipeGovVaultConfig(_minLockDuration=VAULT_MIN, _maxLockDuration=VAULT_MAX)
    c = _build(
        human_resources, mission_control, switchboard_delta, contributor_template,
        ledger, governance, alice, duration,
    )
    assert c.depositLockDuration() == duration
    assert ripe_gov_vault.userBalances(alice, ripe_token) == 0  # prevShares == 0 < PRECISION

    cashed, cash_block = _cash_and_initiate(c, ripe_gov_vault, ripe_token, alice)
    # cash leg: clamped by RipeGov
    assert unlock_block(ripe_gov_vault, c, ripe_token) == cash_block + _clamped(duration)

    boa.env.time_travel(blocks=c.keyActionDelay())
    c.confirmRipeTransfer(False, sender=alice)
    bn = boa.env.evm.patch.block_number

    # transfer leg: RAW, no clamp
    assert unlock_block(ripe_gov_vault, alice, ripe_token) == bn + duration
    assert position(ripe_gov_vault, alice, ripe_token) == cashed
    assert position(ripe_gov_vault, c, ripe_token) == 0

    if duration == 0:
        # the owner lands fully unlocked at the confirm block, under the vault minimum
        assert unlock_block(ripe_gov_vault, alice, ripe_token) == bn
        assert unlock_block(ripe_gov_vault, alice, ripe_token) < bn + VAULT_MIN
    if duration > VAULT_MAX:
        assert unlock_block(ripe_gov_vault, alice, ripe_token) > bn + VAULT_MAX


def test_g11c_lock_matrix_seeded_owner_prevshares_at_or_above_precision(
    human_resources,
    mission_control,
    switchboard_delta,
    contributor_template,
    ledger,
    governance,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    teller,
    whale,
    alice,
):
    """prevShares >= PRECISION: the weighted blend's NEW leg is not capped at
    maxLockDuration, so an over-max HR term extends the owner's whole position."""
    setupRipeGovVaultConfig(_minLockDuration=VAULT_MIN, _maxLockDuration=VAULT_MAX)
    over_max = 50 * VAULT_MAX
    c = _build(
        human_resources, mission_control, switchboard_delta, contributor_template,
        ledger, governance, alice, over_max,
    )

    # ordinary owner route: alice stakes her own RIPE into the gov vault
    ripe_token.transfer(alice, SEED, sender=whale)
    ripe_token.approve(teller, SEED, sender=alice)
    teller.depositIntoGovVault(ripe_token, SEED, 0, sender=alice)
    prev_shares = ripe_gov_vault.userBalances(alice, ripe_token)
    assert prev_shares >= 10**18  # >= PRECISION -> weighted branch
    assert unlock_block(ripe_gov_vault, alice, ripe_token) == (
        boa.env.evm.patch.block_number + VAULT_MIN
    )

    cashed, _ = _cash_and_initiate(c, ripe_gov_vault, ripe_token, alice)
    boa.env.time_travel(blocks=c.keyActionDelay())
    c.confirmRipeTransfer(False, sender=alice)
    bn = boa.env.evm.patch.block_number

    owner_unlock = unlock_block(ripe_gov_vault, alice, ripe_token)
    # the blend is dominated by the uncapped new leg
    assert owner_unlock > bn + VAULT_MAX
    assert position(ripe_gov_vault, alice, ripe_token) == SEED + cashed
    assert position(ripe_gov_vault, c, ripe_token) == 0


def test_g11c_lock_matrix_overflow_sized_term_permanently_strands_the_position(
    human_resources,
    mission_control,
    switchboard_delta,
    contributor_template,
    ledger,
    governance,
    alice,
):
    """Overflow-sized depositLockDuration is rejected at initiate."""
    t = terms(owner=alice, depositLockDuration=MAX_UINT256)
    set_hr_config(mission_control, switchboard_delta, contributor_template)
    set_budget(ledger, switchboard_delta, t["compensation"])
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(*term_args(t), sender=governance.address)


def test_g11c_after_cliff_cancel_does_not_release_an_overflow_stranded_position(
    human_resources,
    mission_control,
    switchboard_delta,
    contributor_template,
    ledger,
    governance,
    alice,
):
    """Overflow-sized depositLockDuration is rejected at initiate."""
    t = terms(owner=alice, depositLockDuration=MAX_UINT256)
    set_hr_config(mission_control, switchboard_delta, contributor_template)
    set_budget(ledger, switchboard_delta, t["compensation"])
    with boa.reverts("invalid terms"):
        human_resources.initiateNewContributor(*term_args(t), sender=governance.address)
