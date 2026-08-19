"""Group 11 lock-split proofs: HR cash clamps; final transfer passes raw terms."""

import boa
import pytest

from contracts.modules import Contributor


UINT256_MAX = 2**256 - 1
MIN_LOCK = 100
MAX_LOCK = 1_000
PRECISION = 10**18


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


@pytest.mark.parametrize(
    "duration",
    [0, MIN_LOCK - 1, MIN_LOCK, MAX_LOCK, MAX_LOCK + 1, UINT256_MAX],
    ids=["zero", "below-min", "exact-min", "exact-max", "above-max", "overflow"],
)
@pytest.mark.parametrize("seed_owner_position", [False, True], ids=["dust-branch", "weighted-branch"])
def test_g11_cash_clamp_and_final_transfer_raw_duration_matrix(
    duration,
    seed_owner_position,
    deployedContributor,
    valid_contributor_terms,
    setupRipeGovVaultConfig,
    setupHrConfig,
    setupLedgerBalance,
    human_resources,
    governance,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner_address,
):
    """Below-min through live max create; zero, above-max, and overflow D are rejected."""
    setupRipeGovVaultConfig(_minLockDuration=MIN_LOCK, _maxLockDuration=MAX_LOCK)
    terms = dict(valid_contributor_terms)
    terms["depositLockDuration"] = duration
    if duration in (0, MAX_LOCK + 1, UINT256_MAX):
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
        return
    contributor = Contributor.at(deployedContributor(terms))

    _advance_to_timestamp(contributor.unlockTime() + 1)
    contributor.initiateRipeTransfer(True, sender=owner_address)
    pending = contributor.pendingRipeTransfer()
    clone_data = ripe_gov_vault.userGovData(contributor, ripe_token)
    cash_clamp = min(max(duration, MIN_LOCK), MAX_LOCK)
    assert clone_data.unlock == boa.env.evm.patch.block_number + cash_clamp
    clone_amount = ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
    assert clone_amount > 0

    _advance_to_block(pending.confirmBlock)
    owner_before = ripe_gov_vault.userGovData(owner_address, ripe_token)
    if seed_owner_position:
        seed = 1_000 * 10**18
        ripe_token.transfer(ripe_gov_vault, seed, sender=whale)
        ripe_gov_vault.depositTokensInVault(
            owner_address, ripe_token, seed, sender=teller.address
        )
        owner_before = ripe_gov_vault.userGovData(owner_address, ripe_token)
        assert owner_before.lastShares >= PRECISION
    else:
        assert owner_before.lastShares < PRECISION

    clone_before = ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
    owner_amount_before = ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
    if duration == UINT256_MAX:
        with boa.reverts():
            contributor.confirmRipeTransfer(False, sender=owner_address)
        assert contributor.pendingRipeTransfer() == pending
        assert (
            ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
            == clone_before
        )
        assert (
            ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
            == owner_amount_before
        )
        return

    # The RipeGov public helper is used only to record the raw-duration branch
    # result.  It is not a RipeGov product assertion.
    lock_terms = (MIN_LOCK, MAX_LOCK, 200_00, True, 10_00)
    expected_unlock = ripe_gov_vault.getWeightedLockOnTokenDeposit(
        clone_data.lastShares,
        duration,
        lock_terms,
        owner_before.lastShares,
        owner_before.unlock,
    )
    contributor.confirmRipeTransfer(False, sender=owner_address)
    owner_after = ripe_gov_vault.userGovData(owner_address, ripe_token)
    assert owner_after.unlock == expected_unlock
    assert not contributor.hasPendingRipeTransfer()
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == 0
    assert (
        ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
        == owner_amount_before + clone_before
    )

    if not seed_owner_position:
        # In the < PRECISION branch this is an exact raw term, including zero;
        # no RipeGov min/max clamp is applied to the final owner position.
        assert owner_after.unlock == boa.env.evm.patch.block_number + duration
