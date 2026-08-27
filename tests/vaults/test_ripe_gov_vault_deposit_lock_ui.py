"""Pins the RIPE gov-vault lock semantics the deposit UI must mirror.

Documents existing behaviour - no contract change. These cover the gaps left by
test_ripe_gov_vault.py, in particular that a top-up deposit can SHORTEN an
existing lock (the weighted average is assigned unconditionally), which
adjustLock explicitly forbids.
"""

import pytest
import boa

from constants import EIGHTEEN_DECIMALS


@pytest.fixture(scope="module")
def setupRipeGovVaultConfig(mission_control, setAssetConfig, switchboard_alpha, ripe_token):
    def _setup(
        _assetWeight=100_00,
        _minLockDuration=100,
        _maxLockDuration=1000,
        _maxLockBoost=200_00,
        _exitFee=10_00,
        _canExit=True,
        _shouldFreezeWhenBadDebt=False,
    ):
        lock_terms = (_minLockDuration, _maxLockDuration, _maxLockBoost, _canExit, _exitFee)
        mission_control.setRipeGovVaultConfig(
            ripe_token, _assetWeight, _shouldFreezeWhenBadDebt, lock_terms,
            sender=switchboard_alpha.address,
        )
        setAssetConfig(ripe_token, _vaultIds=[2])

    yield _setup


def test_plain_deposit_is_not_unlocked_it_floors_at_min(
    teller, ripe_gov_vault, ripe_token, whale, setupRipeGovVaultConfig, setGeneralConfig
):
    """Teller.deposit passes lockDuration=0, but the vault floors at minLockDuration.
    So today's UI deposits land at the MINIMUM lock, not unlocked."""
    setupRipeGovVaultConfig()
    setGeneralConfig()

    amount = 100 * EIGHTEEN_DECIMALS
    ripe_token.approve(teller, amount, sender=whale)
    teller.deposit(ripe_token, amount, whale, ripe_gov_vault, 0, sender=whale)

    userData = ripe_gov_vault.userGovData(whale, ripe_token)
    assert userData.unlock == boa.env.evm.patch.block_number + 100  # minLockDuration
    assert userData.unlock > boa.env.evm.patch.block_number


def test_topup_with_shorter_lock_SHORTENS_existing_lock(
    teller, ripe_gov_vault, ripe_token, whale, setupRipeGovVaultConfig, setGeneralConfig
):
    """A second deposit at the minimum duration drags the weighted average DOWN.
    _getWeightedLockOnTokenDeposit assigns block.number + weighted unconditionally -
    there is no max(prevUnlock, ...) guard, unlike adjustLock."""
    setupRipeGovVaultConfig()
    setGeneralConfig()

    first = 100 * EIGHTEEN_DECIMALS
    second = 900 * EIGHTEEN_DECIMALS
    ripe_token.approve(teller, first + second, sender=whale)

    # lock at the maximum
    teller.depositIntoGovVault(ripe_token, first, 1000, whale, sender=whale)
    unlock_before = ripe_gov_vault.userGovData(whale, ripe_token).unlock
    assert unlock_before == boa.env.evm.patch.block_number + 1000

    # large top-up at the minimum duration
    teller.depositIntoGovVault(ripe_token, second, 100, whale, sender=whale)
    unlock_after = ripe_gov_vault.userGovData(whale, ripe_token).unlock

    # the lock got SHORTER despite adding funds
    assert unlock_after < unlock_before
    # weighted: (100*~1000 + 900*100) / 1000 == ~190 blocks
    assert unlock_after < boa.env.evm.patch.block_number + 250


def test_plain_topup_also_shortens_existing_lock(
    teller, ripe_gov_vault, ripe_token, whale, setupRipeGovVaultConfig, setGeneralConfig
):
    """Same hazard on the path the UI uses TODAY: Teller.deposit sends 0, which
    floors to minLockDuration and still dilutes a longer existing lock."""
    setupRipeGovVaultConfig()
    setGeneralConfig()

    first = 100 * EIGHTEEN_DECIMALS
    second = 900 * EIGHTEEN_DECIMALS
    ripe_token.approve(teller, first + second, sender=whale)

    teller.depositIntoGovVault(ripe_token, first, 1000, whale, sender=whale)
    unlock_before = ripe_gov_vault.userGovData(whale, ripe_token).unlock

    teller.deposit(ripe_token, second, whale, ripe_gov_vault, 0, sender=whale)
    unlock_after = ripe_gov_vault.userGovData(whale, ripe_token).unlock

    assert unlock_after < unlock_before


def test_adjustLock_cannot_shorten(
    teller, ripe_gov_vault, ripe_token, whale, setupRipeGovVaultConfig, setGeneralConfig
):
    """adjustLock asserts newUnlockBlock > unlock - extend only. This is the
    guarantee the deposit path does NOT give."""
    setupRipeGovVaultConfig()
    setGeneralConfig()

    amount = 100 * EIGHTEEN_DECIMALS
    ripe_token.approve(teller, amount, sender=whale)
    teller.depositIntoGovVault(ripe_token, amount, 1000, whale, sender=whale)

    with boa.reverts():
        teller.adjustLock(ripe_token, 100, whale, sender=whale)


def test_adjustLock_reverts_without_position(
    teller, ripe_gov_vault, ripe_token, bob, setupRipeGovVaultConfig, setGeneralConfig
):
    """A first-time user cannot lock before depositing - lastTerms.maxLockDuration
    is 0 and lastShares is 0. So deposit-then-lock is mandatory today."""
    setupRipeGovVaultConfig()
    setGeneralConfig()

    assert ripe_gov_vault.userGovData(bob, ripe_token).lastShares == 0
    with boa.reverts():
        teller.adjustLock(ripe_token, 500, bob, sender=bob)


def test_deposit_lock_duration_silently_clamped_both_ends(
    teller, ripe_gov_vault, ripe_token, whale, bob, setupRipeGovVaultConfig, setGeneralConfig
):
    """Out-of-range durations clamp silently instead of reverting - the UI must
    clamp to lockTerms itself or it will display a duration the tx did not use."""
    setupRipeGovVaultConfig()
    setGeneralConfig()

    amount = 100 * EIGHTEEN_DECIMALS
    ripe_token.approve(teller, amount * 2, sender=whale)

    # above max -> clamped down to maxLockDuration
    teller.depositIntoGovVault(ripe_token, amount, 999_999, whale, sender=whale)
    assert ripe_gov_vault.userGovData(whale, ripe_token).unlock == boa.env.evm.patch.block_number + 1000

    # below min -> clamped up to minLockDuration
    ripe_token.transfer(bob, amount, sender=whale)
    ripe_token.approve(teller, amount, sender=bob)
    teller.depositIntoGovVault(ripe_token, amount, 1, bob, sender=bob)
    assert ripe_gov_vault.userGovData(bob, ripe_token).unlock == boa.env.evm.patch.block_number + 100
