"""Group 5 proof: convert-limit clamp used to strand sGREEN in Teller.

`convertToSavingsGreenAndDepositIntoStabPool` pulls the caller's full GREEN
and wraps it on Teller *before* `validateOnDeposit`. The limits used to
clamp instead of reverting, leaving leftover sGREEN on Teller with no
sweep. `validateOnDeposit` now fail-closes when funds are already on
Teller and the caller is not a Ripe department: a convert that would
exceed remaining headroom reverts in full and rolls back. Generic
`Teller.deposit` still clamps; Ripe migration still bypasses the limits.
"""

import boa
from constants import EIGHTEEN_DECIMALS, MAX_UINT256, VAULT_MIGRATOR_HQ_ID
from conf_utils import clear_transient_storage, filter_logs


GLOBAL_LIMIT = 60 * EIGHTEEN_DECIMALS
CONVERT_AMOUNT = 100 * EIGHTEEN_DECIMALS
STAB_POOL_ID = 1
DEPOSIT_AMOUNT = 100 * EIGHTEEN_DECIMALS


def _register_vault(source_path, ripe_hq, vault_book, governance, label):
    vault = boa.load(source_path, ripe_hq, name=label)
    assert vault_book.startAddNewAddressToRegistry(vault, label, sender=governance.address)
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    vault_id = vault_book.confirmNewAddressToRegistry(vault, sender=governance.address)
    assert vault_id != 0
    return vault, vault_id


def _migrate(teller, caller, user, token, source_id, target_id):
    hq = boa.load_partial("contracts/registries/RipeHq.vy").at(teller.getRipeHq())
    vault_migrator = boa.load_partial("contracts/core/VaultMigrator.vy").at(
        hq.getAddr(VAULT_MIGRATOR_HQ_ID)
    )
    caller_addr = caller.address if hasattr(caller, "address") else caller
    count = vault_migrator.migrateVaultPositions(
        [user], source_id, target_id, sender=caller_addr
    )
    logs = filter_logs(vault_migrator, "VaultPositionMigrationExecuted")
    assert len(logs) == count
    token_addr = token.address if hasattr(token, "address") else token
    matching = [log for log in logs if log.asset == token_addr]
    amount = matching[-1].amount if matching else 0
    clear_transient_storage()
    return amount


def _fund_green(green_token, whale, teller, user, amount):
    green_token.transfer(user, amount, sender=whale)
    green_token.approve(teller.address, amount, sender=user)


def _convert_rollback_state(stability_pool, green_token, savings_green, teller, bob):
    return (
        green_token.balanceOf(bob),
        savings_green.balanceOf(bob),
        green_token.balanceOf(teller.address),
        savings_green.balanceOf(teller.address),
        savings_green.balanceOf(stability_pool.address),
        stability_pool.userBalances(bob, savings_green),
        stability_pool.totalBalances(savings_green),
    )


def test_convert_partial_clamp_strands_sgreen_in_teller(
    stability_pool, green_token, savings_green, whale, bob, teller,
    setGeneralConfig, setAssetConfig,
):
    """Regression: a convert that exceeds the global deposit limit reverts in full.

    Historically the clamp debited the caller in full, credited only the
    headroom, and stranded the remainder on Teller. The call must now revert
    `cannot partially deposit held funds` with caller GREEN/sGREEN, Teller
    GREEN/sGREEN, pool custody, and pool shares all unchanged.
    """
    setGeneralConfig()
    setAssetConfig(savings_green, [1], _minDepositBalance=10 ** 16,
                   _globalDepositLimit=GLOBAL_LIMIT)

    _fund_green(green_token, whale, teller, bob, CONVERT_AMOUNT)
    before = _convert_rollback_state(
        stability_pool, green_token, savings_green, teller, bob)
    with boa.reverts("cannot partially deposit held funds"):
        teller.convertToSavingsGreenAndDepositIntoStabPool(
            bob, CONVERT_AMOUNT, sender=bob,
        )
    clear_transient_storage()
    assert _convert_rollback_state(
        stability_pool, green_token, savings_green, teller, bob) == before


def test_convert_without_clamp_is_the_adjacent_positive_control(
    stability_pool, green_token, savings_green, whale, bob, teller,
    setGeneralConfig, setAssetConfig,
):
    """Same fixture, headroom above the convert size: no residue, no loss."""
    setGeneralConfig()
    setAssetConfig(savings_green, [1], _minDepositBalance=10 ** 16,
                   _globalDepositLimit=1_000 * EIGHTEEN_DECIMALS)

    _fund_green(green_token, whale, teller, bob, CONVERT_AMOUNT)
    green_before = green_token.balanceOf(bob)

    deposited = teller.convertToSavingsGreenAndDepositIntoStabPool(
        bob, CONVERT_AMOUNT, sender=bob,
    )
    clear_transient_storage()

    assert green_before - green_token.balanceOf(bob) == CONVERT_AMOUNT
    assert deposited == CONVERT_AMOUNT
    assert savings_green.balanceOf(teller.address) == 0
    assert green_token.balanceOf(teller.address) == 0
    assert savings_green.balanceOf(stability_pool.address) == CONVERT_AMOUNT


def test_plain_stab_deposit_at_the_same_clamp_keeps_the_tokens_with_the_user(
    stability_pool, green_token, savings_green, whale, bob, teller,
    setGeneralConfig, setAssetConfig,
):
    """Control: the generic Teller.deposit route still clamps by pulling less.

    Convert used to strand the clamped remainder on Teller; it now reverts.
    This path keeps the surplus with the user.
    """
    setGeneralConfig()
    setAssetConfig(savings_green, [1], _minDepositBalance=10 ** 16,
                   _globalDepositLimit=GLOBAL_LIMIT)

    green_token.transfer(bob, CONVERT_AMOUNT, sender=whale)
    green_token.approve(savings_green.address, CONVERT_AMOUNT, sender=bob)
    shares = savings_green.deposit(CONVERT_AMOUNT, bob, sender=bob)
    savings_green.approve(teller.address, shares, sender=bob)

    sgreen_before = savings_green.balanceOf(bob)
    got = teller.deposit(savings_green, shares, bob, stability_pool, sender=bob)
    clear_transient_storage()

    assert got == GLOBAL_LIMIT
    assert sgreen_before - savings_green.balanceOf(bob) == GLOBAL_LIMIT
    assert savings_green.balanceOf(bob) == shares - GLOBAL_LIMIT
    assert savings_green.balanceOf(teller.address) == 0


def test_convert_partial_per_user_clamp_reverts_and_rolls_back(
    stability_pool, green_token, savings_green, whale, bob, teller,
    setGeneralConfig, setAssetConfig,
):
    """Regression: a convert that exceeds the per-user deposit limit reverts in full."""
    setGeneralConfig()
    setAssetConfig(savings_green, [1], _minDepositBalance=10 ** 16,
                   _perUserDepositLimit=GLOBAL_LIMIT,
                   _globalDepositLimit=1_000 * EIGHTEEN_DECIMALS)

    _fund_green(green_token, whale, teller, bob, CONVERT_AMOUNT)
    before = _convert_rollback_state(
        stability_pool, green_token, savings_green, teller, bob)
    with boa.reverts("cannot partially deposit held funds"):
        teller.convertToSavingsGreenAndDepositIntoStabPool(
            bob, CONVERT_AMOUNT, sender=bob,
        )
    clear_transient_storage()
    assert _convert_rollback_state(
        stability_pool, green_token, savings_green, teller, bob) == before


def test_ripe_migration_bypasses_target_deposit_limit(
    teller, stability_pool, green_token, savings_green, whale, bob,
    ripe_hq, vault_book, governance, setGeneralConfig, setAssetConfig,
    switchboard_alpha, switchboard_echo, mission_control,
):
    stab_vault, stab_id = _register_vault(
        "contracts/vaults/StabilityPool.vy", ripe_hq, vault_book, governance,
        "g5_migration_target_stab_pool",
    )
    setGeneralConfig()
    setAssetConfig(savings_green, _vaultIds=[STAB_POOL_ID, stab_id])

    green_token.transfer(bob, DEPOSIT_AMOUNT, sender=whale)
    green_token.approve(teller.address, DEPOSIT_AMOUNT, sender=bob)
    sgreen = teller.convertToSavingsGreenAndDepositIntoStabPool(bob, DEPOSIT_AMOUNT, sender=bob)
    assert sgreen > 0
    assert stability_pool.getTotalAmountForUser(bob, savings_green) == sgreen
    clear_transient_storage()

    mission_control.setPreferredStabVaultId(stab_id, sender=switchboard_alpha.address)
    assert mission_control.isStabVaultId(STAB_POOL_ID)
    assert mission_control.isStabVaultId(stab_id)

    setAssetConfig(
        savings_green,
        _vaultIds=[STAB_POOL_ID, stab_id],
        _perUserDepositLimit=1,
    )

    teller.pause(True, sender=switchboard_alpha.address)
    clear_transient_storage()
    migrated = _migrate(teller, switchboard_echo, bob, savings_green, STAB_POOL_ID, stab_id)

    assert migrated == sgreen
    assert stability_pool.getTotalAmountForUser(bob, savings_green) == 0
    assert savings_green.balanceOf(stab_vault) == sgreen
