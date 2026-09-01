import boa
import pytest

from constants import EIGHTEEN_DECIMALS, VAULT_MIGRATOR_HQ_ID, ZERO_ADDRESS
from conf_utils import filter_logs


LEGACY_RIPE_GOV_VAULT_ID = 2
ASSET_WEIGHT = 100_00
LOCK_TERMS = (100, 1_000, 200_00, True, 10_00)

# These tests keep the current RipeGov as the VaultMigrator source stand-in.
# Deployed Base legacy releases on a one-block minLockDuration decrease through
# its old classifier. Current RipeGov releases on a one-block min increase
# through the courtesy predicate. Exact legacy-source and fork fidelity is
# deferred to issue #150.


def _register_target(ripe_hq, vault_book, governance):
    target = boa.load("contracts/vaults/RipeGov.vy", ripe_hq, name="legacy_migration_target")
    assert vault_book.startAddNewAddressToRegistry(
        target, "legacy migration target", sender=governance.address,
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    target_id = vault_book.confirmNewAddressToRegistry(target, sender=governance.address)
    return target, target_id


def _install_legacy_migrator(ripe_hq, source, governance):
    migrator = boa.load(
        "contracts/core/VaultMigrator.vy",
        ripe_hq,
        False,
        source,
        name="legacy_vault_migrator",
    )
    assert ripe_hq.startAddressUpdateToRegistry(
        VAULT_MIGRATOR_HQ_ID, migrator, sender=governance.address,
    )
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock())
    assert ripe_hq.confirmAddressUpdateToRegistry(
        VAULT_MIGRATOR_HQ_ID, sender=governance.address,
    )
    assert ripe_hq.getAddr(VAULT_MIGRATOR_HQ_ID) == migrator.address
    return migrator


def _pause_if_needed(contract, switchboard_alpha):
    if not contract.isPaused():
        contract.pause(True, sender=switchboard_alpha.address)


def _unpause_if_needed(contract, switchboard_alpha):
    if contract.isPaused():
        contract.pause(False, sender=switchboard_alpha.address)


def _set_legacy_asset_config(
    mission_control,
    setAssetConfig,
    switchboard_alpha,
    asset,
    target_id,
    lock_terms=LOCK_TERMS,
):
    mission_control.setRipeGovVaultConfig(
        asset,
        ASSET_WEIGHT,
        False,
        lock_terms,
        sender=switchboard_alpha.address,
    )
    setAssetConfig(
        asset,
        _vaultIds=[LEGACY_RIPE_GOV_VAULT_ID, target_id],
    )


def _seed_locked_legacy_position(source, asset, funder, user, teller, ledger, amount):
    asset.transfer(source, amount, sender=funder)
    source.depositTokensWithLockDuration(
        user,
        asset,
        amount,
        LOCK_TERMS[0],
        sender=teller.address,
    )
    if not ledger.isParticipatingInVault(user, LEGACY_RIPE_GOV_VAULT_ID):
        ledger.addVaultToUser(
            user,
            LEGACY_RIPE_GOV_VAULT_ID,
            sender=teller.address,
        )


def _current_source_courtesy_min_increase_terms():
    """Current RipeGov courtesy: minLockDuration 100 → 101.

    Deployed Base legacy released on a one-block min decrease through its old
    classifier. These tests cover VaultMigrator mechanics with the current
    source as a stand-in; exact legacy-source and fork fidelity is issue #150.
    """
    return (
        LOCK_TERMS[0] + 1,
        LOCK_TERMS[1],
        LOCK_TERMS[2],
        LOCK_TERMS[3],
        LOCK_TERMS[4],
    )


def test_default_vault_migrator_disables_base_legacy_route(
    switchboard_echo, governance, bob,
):
    with boa.reverts("legacy migration disabled"):
        switchboard_echo.migrateLegacyRipeGovPositions(
            [bob], sender=governance.address,
        )


def test_explicit_exporter_route_rejects_bound_legacy_source(
    ripe_hq,
    vault_book,
    governance,
    ripe_gov_vault,
    ripe_token,
    bob,
    teller,
    mission_control,
    switchboard_alpha,
    switchboard_echo,
):
    boa.env.evm.patch.chain_id = 8453
    _, target_id = _register_target(ripe_hq, vault_book, governance)
    _install_legacy_migrator(ripe_hq, ripe_gov_vault, governance)
    mission_control.setCoreRipeGovVaultId(
        target_id, sender=switchboard_alpha.address,
    )
    _pause_if_needed(teller, switchboard_alpha)

    with boa.reverts("use legacy ripe gov migration"):
        switchboard_echo.migrateRipeGovPositionsForUserByAssets(
            bob,
            [ripe_token.address],
            LEGACY_RIPE_GOV_VAULT_ID,
            sender=governance.address,
        )


def test_legacy_batch_caps_at_twenty_five_users(
    switchboard_echo, governance, bob,
):
    """The public wrapper cannot encode a twenty-sixth user."""
    with pytest.raises(Exception):
        switchboard_echo.migrateLegacyRipeGovPositions(
            [bob] * 26,
            sender=governance.address,
        )


def test_teller_identity_steps_are_vault_migrator_only(
    teller, switchboard_echo, ripe_gov_vault, ripe_token, bob,
):
    with boa.reverts("only vault migrator allowed"):
        teller.withdrawOnVaultMigration(
            bob,
            ripe_token,
            ripe_gov_vault,
            sender=switchboard_echo.address,
        )
    with boa.reverts("only vault migrator allowed"):
        teller.exportPositionForLegacyRipeGovMigration(
            bob,
            ripe_token,
            ripe_gov_vault,
            ripe_gov_vault,
            sender=switchboard_echo.address,
        )


def test_base_legacy_route_preserves_position_then_normal_claim_cleans_source(
    ripe_hq,
    vault_book,
    governance,
    ripe_gov_vault,
    ripe_token,
    whale,
    bravo_token,
    bravo_token_whale,
    bob,
    teller,
    ledger,
    lootbox,
    mission_control,
    switchboard_alpha,
    switchboard_echo,
    auction_house,
    credit_engine,
    human_resources,
    deleverage,
    setAssetConfig,
    setGeneralConfig,
):
    boa.env.evm.patch.chain_id = 8453
    source = ripe_gov_vault
    target, target_id = _register_target(ripe_hq, vault_book, governance)
    _install_legacy_migrator(ripe_hq, source, governance)

    mission_control.setRipeGovVaultConfig(
        ripe_token,
        ASSET_WEIGHT,
        False,
        LOCK_TERMS,
        sender=switchboard_alpha.address,
    )
    mission_control.setRipeGovVaultConfig(
        bravo_token,
        ASSET_WEIGHT,
        False,
        LOCK_TERMS,
        sender=switchboard_alpha.address,
    )
    setAssetConfig(
        ripe_token,
        _vaultIds=[LEGACY_RIPE_GOV_VAULT_ID, target_id],
    )
    setAssetConfig(
        bravo_token,
        _vaultIds=[LEGACY_RIPE_GOV_VAULT_ID, target_id],
    )
    setGeneralConfig()
    mission_control.setCoreRipeGovVaultId(target_id, sender=switchboard_alpha.address)

    amount = 100 * EIGHTEEN_DECIMALS
    ripe_token.transfer(source, amount, sender=whale)
    source.depositTokensWithLockDuration(
        bob,
        ripe_token,
        amount,
        LOCK_TERMS[0],
        sender=teller.address,
    )
    bravo_token.transfer(source, amount, sender=bravo_token_whale)
    source.depositTokensWithLockDuration(
        bob,
        bravo_token,
        amount,
        LOCK_TERMS[0],
        sender=teller.address,
    )
    ledger.addVaultToUser(bob, LEGACY_RIPE_GOV_VAULT_ID, sender=teller.address)
    boa.env.time_travel(blocks=LOCK_TERMS[0] + 25)
    source.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    ripe_source_data = source.userGovData(bob, ripe_token)
    bravo_source_data = source.userGovData(bob, bravo_token)
    assert ripe_source_data.govPoints > 0
    assert bravo_source_data.govPoints > 0

    target.pause(True, sender=switchboard_alpha.address)
    _pause_if_needed(teller, switchboard_alpha)
    assert not source.isPaused()
    assert not lootbox.isPaused()
    assert not auction_house.isPaused()
    assert not credit_engine.isPaused()
    assert not human_resources.isPaused()
    assert not deleverage.isPaused()

    assert switchboard_echo.migrateLegacyRipeGovPositions(
        [bob], sender=governance.address,
    ) == 2
    assert source.getTotalAmountForUser(bob, ripe_token) == 0
    assert source.getTotalAmountForUser(bob, bravo_token) == 0
    assert target.getTotalAmountForUser(bob, ripe_token) == amount
    assert target.getTotalAmountForUser(bob, bravo_token) == amount
    assert ledger.isParticipatingInVault(bob, LEGACY_RIPE_GOV_VAULT_ID)
    assert ledger.isParticipatingInVault(bob, target_id)
    migration_logs = filter_logs(
        switchboard_echo, "LegacyRipeGovPositionMigrationExecuted",
    )
    assert len(migration_logs) == 2
    assert {log.asset for log in migration_logs} == {
        ripe_token.address,
        bravo_token.address,
    }

    ripe_target_data = target.userGovData(bob, ripe_token)
    bravo_target_data = target.userGovData(bob, bravo_token)
    assert ripe_target_data.govPoints == ripe_source_data.govPoints
    assert ripe_target_data.unlock == ripe_source_data.unlock
    assert ripe_target_data.lastTerms == ripe_source_data.lastTerms
    assert bravo_target_data.govPoints == bravo_source_data.govPoints
    assert bravo_target_data.unlock == bravo_source_data.unlock
    assert bravo_target_data.lastTerms == bravo_source_data.lastTerms

    for contract in (target, teller):
        _unpause_if_needed(contract, switchboard_alpha)

    teller.claimLoot(bob, False, sender=bob)
    assert not source.isUserInVaultAsset(bob, ripe_token)
    assert not source.isUserInVaultAsset(bob, bravo_token)
    assert not ledger.isParticipatingInVault(bob, LEGACY_RIPE_GOV_VAULT_ID)
    assert ledger.isParticipatingInVault(bob, target_id)


def test_active_locks_migrate_for_many_users_and_all_assets_after_one_block_min_increase(
    ripe_hq,
    vault_book,
    governance,
    ripe_gov_vault,
    ripe_token,
    whale,
    bravo_token,
    bravo_token_whale,
    bob,
    alice,
    sally,
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    switchboard_echo,
    setAssetConfig,
    setGeneralConfig,
):
    """VaultMigrator mechanics with the current RipeGov as source stand-in.

    Every live lock remains active in the source snapshot. A one-block
    minLockDuration increase triggers current RipeGov courtesy so withdrawal
    is reachable, and import restores the original record. Deployed Base
    legacy instead released on a one-block min decrease through its old
    classifier. Exact legacy-source and fork fidelity is issue #150.
    """
    boa.env.evm.patch.chain_id = 8453
    source = ripe_gov_vault
    target, target_id = _register_target(ripe_hq, vault_book, governance)
    _install_legacy_migrator(ripe_hq, source, governance)

    assets = (
        (ripe_token, whale),
        (bravo_token, bravo_token_whale),
    )
    for asset, _ in assets:
        _set_legacy_asset_config(
            mission_control,
            setAssetConfig,
            switchboard_alpha,
            asset,
            target_id,
        )
    setGeneralConfig()
    mission_control.setCoreRipeGovVaultId(
        target_id,
        sender=switchboard_alpha.address,
    )

    amount = 40 * EIGHTEEN_DECIMALS
    users = (bob, alice)
    for user in users:
        for asset, funder in assets:
            _seed_locked_legacy_position(
                source,
                asset,
                funder,
                user,
                teller,
                ledger,
                amount,
            )

    boa.env.time_travel(blocks=25)
    expected = {}
    for user in users:
        for asset, _ in assets:
            data = source.userGovData(user, asset)
            assert data.unlock > boa.env.evm.patch.block_number
            pending = source.getLatestGovPoints(
                data.lastShares,
                data.lastPointsUpdate,
                data.unlock,
                data.lastTerms,
                ASSET_WEIGHT,
            )
            assert pending > 0
            expected[(user, asset.address)] = (data, data.govPoints + pending)

    # A one-block increase of minLockDuration is the current RipeGov courtesy
    # trigger. Deployed Base legacy instead released on a one-block min
    # decrease through its old classifier. These tests cover VaultMigrator
    # mechanics with the current source as a stand-in; exact legacy-source
    # and fork fidelity is issue #150.
    wind_down_terms = _current_source_courtesy_min_increase_terms()
    for asset, _ in assets:
        _set_legacy_asset_config(
            mission_control,
            setAssetConfig,
            switchboard_alpha,
            asset,
            target_id,
            wind_down_terms,
        )

    target.pause(True, sender=switchboard_alpha.address)
    _pause_if_needed(teller, switchboard_alpha)

    # Zero, duplicate, and no-position entries are harmless; every supported
    # position for each real user still moves atomically in the same call.
    assert switchboard_echo.migrateLegacyRipeGovPositions(
        [ZERO_ADDRESS, bob, bob, sally, alice],
        sender=governance.address,
    ) == 4

    for user in users:
        for asset, _ in assets:
            original, expected_points = expected[(user, asset.address)]
            imported = target.userGovData(user, asset)
            assert source.getTotalAmountForUser(user, asset) == 0
            assert target.getTotalAmountForUser(user, asset) == amount
            assert imported.govPoints == expected_points
            assert imported.unlock == original.unlock
            assert imported.lastTerms == original.lastTerms


def test_late_legacy_user_failure_rolls_back_earlier_users_atomically(
    ripe_hq,
    vault_book,
    governance,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    switchboard_echo,
    setAssetConfig,
    setGeneralConfig,
):
    boa.env.evm.patch.chain_id = 8453
    source = ripe_gov_vault
    target, target_id = _register_target(ripe_hq, vault_book, governance)
    _install_legacy_migrator(ripe_hq, source, governance)
    _set_legacy_asset_config(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        target_id,
    )
    setGeneralConfig()
    mission_control.setCoreRipeGovVaultId(target_id, sender=switchboard_alpha.address)

    amount = 30 * EIGHTEEN_DECIMALS
    for user in (bob, alice):
        _seed_locked_legacy_position(
            source,
            ripe_token,
            whale,
            user,
            teller,
            ledger,
            amount,
        )

    # Make only the later user's target non-virgin. Import must fail closed and
    # roll back Bob's earlier completed-looking export/import in the same tx.
    ripe_token.transfer(target, amount, sender=whale)
    target.depositTokensInVault(
        alice,
        ripe_token,
        amount,
        sender=teller.address,
    )
    existing_target = target.getTotalAmountForUser(alice, ripe_token)

    _set_legacy_asset_config(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        target_id,
        _current_source_courtesy_min_increase_terms(),
    )
    target.pause(True, sender=switchboard_alpha.address)
    _pause_if_needed(teller, switchboard_alpha)

    with boa.reverts("target balance exists"):
        switchboard_echo.migrateLegacyRipeGovPositions(
            [bob, alice],
            sender=governance.address,
        )

    assert source.getTotalAmountForUser(bob, ripe_token) == amount
    assert target.getTotalAmountForUser(bob, ripe_token) == 0
    assert source.getTotalAmountForUser(alice, ripe_token) == amount
    assert target.getTotalAmountForUser(alice, ripe_token) == existing_target
    assert filter_logs(
        switchboard_echo,
        "LegacyRipeGovPositionMigrationExecuted",
    ) == []


def test_legacy_migration_rejects_user_touched_in_same_action_block_and_rolls_back(
    ripe_hq,
    vault_book,
    governance,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    switchboard_echo,
    setAssetConfig,
    setGeneralConfig,
):
    boa.env.evm.patch.chain_id = 8453
    source = ripe_gov_vault
    target, target_id = _register_target(ripe_hq, vault_book, governance)
    _install_legacy_migrator(ripe_hq, source, governance)
    _set_legacy_asset_config(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        target_id,
    )
    setGeneralConfig()
    mission_control.setShouldCheckLastTouch(True, sender=switchboard_alpha.address)
    mission_control.setCoreRipeGovVaultId(target_id, sender=switchboard_alpha.address)
    amount = 20 * EIGHTEEN_DECIMALS
    _seed_locked_legacy_position(
        source,
        ripe_token,
        whale,
        bob,
        teller,
        ledger,
        amount,
    )
    _set_legacy_asset_config(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        target_id,
        _current_source_courtesy_min_increase_terms(),
    )

    # Stamp the user's last touch before Teller enters its migration pause.
    teller.performHousekeeping(
        True,
        bob,
        False,
        sender=switchboard_echo.address,
    )
    target.pause(True, sender=switchboard_alpha.address)
    _pause_if_needed(teller, switchboard_alpha)

    with boa.reverts("one action per block"):
        switchboard_echo.migrateLegacyRipeGovPositions(
            [bob],
            sender=governance.address,
        )
    assert source.getTotalAmountForUser(bob, ripe_token) == amount
    assert target.getTotalAmountForUser(bob, ripe_token) == 0


@pytest.mark.gas
@pytest.mark.parametrize("num_users", [1, 5, 10, 20])
def test_legacy_migration_batch_gas_characterization(
    num_users,
    ripe_hq,
    vault_book,
    governance,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    switchboard_echo,
    setAssetConfig,
    setGeneralConfig,
):
    """Record the gas curve through the enforced 20-slot aggregate limit."""
    boa.env.evm.patch.chain_id = 8453
    source = ripe_gov_vault
    target, target_id = _register_target(ripe_hq, vault_book, governance)
    _install_legacy_migrator(ripe_hq, source, governance)
    _set_legacy_asset_config(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        target_id,
    )
    setGeneralConfig()
    mission_control.setCoreRipeGovVaultId(target_id, sender=switchboard_alpha.address)

    users = [boa.env.generate_address() for _ in range(num_users)]
    amount = 10 * EIGHTEEN_DECIMALS
    for user in users:
        _seed_locked_legacy_position(
            source,
            ripe_token,
            whale,
            user,
            teller,
            ledger,
            amount,
        )
    _set_legacy_asset_config(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        target_id,
        _current_source_courtesy_min_increase_terms(),
    )
    target.pause(True, sender=switchboard_alpha.address)
    _pause_if_needed(teller, switchboard_alpha)

    assert switchboard_echo.migrateLegacyRipeGovPositions(
        users,
        sender=governance.address,
    ) == num_users
    gas_used = switchboard_echo._computation.get_gas_used()
    print(
        f"LEGACY_MIGRATION_GAS users={num_users} total={gas_used} "
        f"per_user={gas_used // num_users}"
    )
    if num_users == 1:
        assert gas_used < 30_000_000


@pytest.mark.gas
def test_legacy_dual_asset_twenty_slot_batch_fits_block_envelope(
    ripe_hq,
    vault_book,
    governance,
    ripe_gov_vault,
    ripe_token,
    whale,
    bravo_token,
    bravo_token_whale,
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    switchboard_echo,
    setAssetConfig,
    setGeneralConfig,
):
    """Measure the enforced 20-slot aggregate migration envelope."""
    boa.env.evm.patch.chain_id = 8453
    source = ripe_gov_vault
    target, target_id = _register_target(ripe_hq, vault_book, governance)
    _install_legacy_migrator(ripe_hq, source, governance)
    assets = (
        (ripe_token, whale),
        (bravo_token, bravo_token_whale),
    )
    for asset, _ in assets:
        _set_legacy_asset_config(
            mission_control,
            setAssetConfig,
            switchboard_alpha,
            asset,
            target_id,
        )
    setGeneralConfig()
    mission_control.setCoreRipeGovVaultId(
        target_id, sender=switchboard_alpha.address,
    )

    users = [boa.env.generate_address() for _ in range(10)]
    amount = 10 * EIGHTEEN_DECIMALS
    for user in users:
        for asset, funder in assets:
            _seed_locked_legacy_position(
                source,
                asset,
                funder,
                user,
                teller,
                ledger,
                amount,
            )
    for asset, _ in assets:
        _set_legacy_asset_config(
            mission_control,
            setAssetConfig,
            switchboard_alpha,
            asset,
            target_id,
            _current_source_courtesy_min_increase_terms(),
        )
    target.pause(True, sender=switchboard_alpha.address)
    _pause_if_needed(teller, switchboard_alpha)

    assert switchboard_echo.migrateLegacyRipeGovPositions(
        users, sender=governance.address,
    ) == 20
    gas_used = switchboard_echo._computation.get_gas_used()
    print(
        "LEGACY_MIGRATION_GAS users=10 assets=2 "
        f"positions=20 total={gas_used} per_user={gas_used // 10}"
    )
    assert gas_used < 30_000_000


@pytest.mark.parametrize("registered_slots", [20, 21])
def test_legacy_migration_registered_slot_boundary(
    registered_slots,
    ripe_hq,
    vault_book,
    governance,
    ripe_gov_vault,
    bob,
    teller,
    mission_control,
    switchboard_alpha,
    switchboard_echo,
):
    boa.env.evm.patch.chain_id = 8453
    target, target_id = _register_target(ripe_hq, vault_book, governance)
    _install_legacy_migrator(ripe_hq, ripe_gov_vault, governance)
    mission_control.setCoreRipeGovVaultId(
        target_id, sender=switchboard_alpha.address,
    )
    target.pause(True, sender=switchboard_alpha.address)
    _pause_if_needed(teller, switchboard_alpha)
    ripe_gov_vault.eval(
        f"vaultData.numUserAssets[{bob}] = {registered_slots + 1}"
    )

    if registered_slots == 20:
        assert switchboard_echo.migrateLegacyRipeGovPositions(
            [bob], sender=governance.address,
        ) == 0
    else:
        with boa.reverts("legacy user asset capacity exceeded"):
            switchboard_echo.migrateLegacyRipeGovPositions(
                [bob], sender=governance.address,
            )


def test_legacy_single_user_fills_twenty_position_snapshot_capacity(
    ripe_hq,
    vault_book,
    governance,
    ripe_gov_vault,
    bob,
    teller,
    ledger,
    mission_control,
    switchboard_alpha,
    switchboard_echo,
    setAssetConfig,
    setGeneralConfig,
):
    boa.env.evm.patch.chain_id = 8453
    source = ripe_gov_vault
    target, target_id = _register_target(ripe_hq, vault_book, governance)
    _install_legacy_migrator(ripe_hq, source, governance)
    setGeneralConfig()
    mission_control.setCoreRipeGovVaultId(
        target_id, sender=switchboard_alpha.address,
    )

    amount = EIGHTEEN_DECIMALS
    assets = []
    for i in range(20):
        asset = boa.load(
            "contracts/mock/MockErc20.vy",
            governance.address,
            f"Migration Legacy {i}",
            f"ML{i}",
            18,
            0,
            name=f"migration_legacy_{i}",
        )
        _set_legacy_asset_config(
            mission_control,
            setAssetConfig,
            switchboard_alpha,
            asset,
            target_id,
        )
        asset.mint(bob, amount, sender=governance.address)
        _seed_locked_legacy_position(
            source,
            asset,
            bob,
            bob,
            teller,
            ledger,
            amount,
        )
        assets.append(asset)

    assert source.numUserAssets(bob) == 21
    boa.env.time_travel(blocks=LOCK_TERMS[0] + 25)
    source.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    source_data = {
        asset.address: source.userGovData(bob, asset)
        for asset in assets
    }
    assert all(data.govPoints > 0 for data in source_data.values())

    mission_control.setShouldCheckLastTouch(True, sender=switchboard_alpha.address)
    target.pause(True, sender=switchboard_alpha.address)
    _pause_if_needed(teller, switchboard_alpha)
    boa.env.time_travel(blocks=1)
    expected_points = {
        asset.address: source_data[asset.address].govPoints
        + source.getLatestGovPoints(
            source_data[asset.address].lastShares,
            source_data[asset.address].lastPointsUpdate,
            source_data[asset.address].unlock,
            source_data[asset.address].lastTerms,
            ASSET_WEIGHT,
        )
        for asset in assets
    }

    assert switchboard_echo.migrateLegacyRipeGovPositions(
        [bob], sender=governance.address,
    ) == 20
    assert ledger.lastTouch(bob) == boa.env.evm.patch.block_number
    migration_logs = filter_logs(
        switchboard_echo, "LegacyRipeGovPositionMigrationExecuted",
    )
    assert len(migration_logs) == 20
    assert {log.asset for log in migration_logs} == {
        asset.address for asset in assets
    }

    for asset in assets:
        imported = target.userGovData(bob, asset)
        assert source.getTotalAmountForUser(bob, asset) == 0
        assert target.getTotalAmountForUser(bob, asset) == amount
        assert imported.govPoints == expected_points[asset.address]
        assert imported.unlock == source_data[asset.address].unlock
        assert imported.lastTerms == source_data[asset.address].lastTerms
        source_points = ledger.getDepositPointsBundle(
            bob, LEGACY_RIPE_GOV_VAULT_ID, asset
        ).userPoints
        target_points = ledger.getDepositPointsBundle(
            bob, target_id, asset
        ).userPoints
        assert source_points.lastBalance == 0
        assert source_points.lastUpdate != 0
        assert target_points.lastBalance > 0
        assert target_points.lastUpdate != 0


def test_base_legacy_route_skips_user_without_source_positions(
    ripe_hq,
    vault_book,
    governance,
    ripe_gov_vault,
    bob,
    teller,
    mission_control,
    switchboard_alpha,
    switchboard_echo,
):
    boa.env.evm.patch.chain_id = 8453
    target, target_id = _register_target(ripe_hq, vault_book, governance)
    _install_legacy_migrator(ripe_hq, ripe_gov_vault, governance)
    mission_control.setCoreRipeGovVaultId(
        target_id, sender=switchboard_alpha.address,
    )
    target.pause(True, sender=switchboard_alpha.address)
    _pause_if_needed(teller, switchboard_alpha)

    assert switchboard_echo.migrateLegacyRipeGovPositions(
        [bob], sender=governance.address,
    ) == 0
    assert filter_logs(
        switchboard_echo, "LegacyRipeGovPositionMigrationExecuted",
    ) == []


def test_legacy_binding_rejects_wrong_chain(
    ripe_hq,
    governance,
    ripe_gov_vault,
    ripe_token,
    bob,
    switchboard_echo,
):
    boa.env.evm.patch.chain_id = 8453
    _install_legacy_migrator(ripe_hq, ripe_gov_vault, governance)
    original_chain_id = boa.env.evm.patch.chain_id
    boa.env.evm.patch.chain_id = original_chain_id + 1
    try:
        with boa.reverts("legacy migration disabled"):
            switchboard_echo.migrateLegacyRipeGovPositions(
                [bob], sender=governance.address,
            )
    finally:
        boa.env.evm.patch.chain_id = original_chain_id
