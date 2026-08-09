import boa
from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs


LEGACY_RIPE_GOV_VAULT_ID = 2
VAULT_MIGRATOR_ID = 23
ASSET_WEIGHT = 100_00
LOCK_TERMS = (100, 1_000, 200_00, True, 10_00)


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
        boa.env.evm.patch.chain_id,
        name="legacy_vault_migrator",
    )
    assert ripe_hq.startAddressUpdateToRegistry(
        VAULT_MIGRATOR_ID, migrator, sender=governance.address,
    )
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock())
    assert ripe_hq.confirmAddressUpdateToRegistry(
        VAULT_MIGRATOR_ID, sender=governance.address,
    )
    assert ripe_hq.getAddr(VAULT_MIGRATOR_ID) == migrator.address
    return migrator


def _pause_if_needed(contract, switchboard_alpha):
    if not contract.isPaused():
        contract.pause(True, sender=switchboard_alpha.address)


def test_legacy_binding_requires_both_vault_and_chain(ripe_hq):
    with boa.reverts("incomplete legacy binding"):
        boa.load(
            "contracts/core/VaultMigrator.vy",
            ripe_hq,
            False,
            ripe_hq,
            0,
            name="incomplete_legacy_vault_migrator",
        )


def test_default_vault_migrator_disables_base_legacy_route(
    switchboard_echo, governance, ripe_token,
):
    with boa.reverts("legacy migration disabled"):
        switchboard_echo.setLegacyRipeGovMigrationAsset(
            ripe_token, sender=governance.address,
        )


def test_teller_identity_steps_are_vault_migrator_only(
    teller, switchboard_echo, ripe_gov_vault, ripe_token, bob,
):
    with boa.reverts("only vault migrator allowed"):
        teller.executeVaultWithdrawal(
            bob,
            ripe_token,
            ripe_gov_vault,
            sender=switchboard_echo.address,
        )


def test_lootbox_migrated_source_settlement_is_vault_migrator_only(
    lootbox, ripe_gov_vault, bob,
):
    with boa.reverts("only vault migrator allowed"):
        lootbox.settleAndCleanupMigratedSource(
            bob,
            LEGACY_RIPE_GOV_VAULT_ID,
            ripe_gov_vault,
            sender=bob,
        )


def test_base_legacy_route_preserves_position_then_cleans_source(
    ripe_hq,
    vault_book,
    governance,
    ripe_gov_vault,
    ripe_token,
    whale,
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
    source = ripe_gov_vault
    target, target_id = _register_target(ripe_hq, vault_book, governance)
    migrator = _install_legacy_migrator(ripe_hq, source, governance)

    mission_control.setRipeGovVaultConfig(
        ripe_token,
        ASSET_WEIGHT,
        False,
        LOCK_TERMS,
        sender=switchboard_alpha.address,
    )
    setAssetConfig(
        ripe_token,
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
    ledger.addVaultToUser(bob, LEGACY_RIPE_GOV_VAULT_ID, sender=teller.address)
    boa.env.time_travel(blocks=LOCK_TERMS[0] + 25)
    source.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    source_data = source.userGovData(bob, ripe_token)
    assert source_data.govPoints > 0

    with boa.reverts("use legacy migration route"):
        switchboard_echo.migrateRipeGovPositions(
            [(bob, ripe_token, LEGACY_RIPE_GOV_VAULT_ID, target_id)],
            sender=governance.address,
        )

    target.pause(True, sender=switchboard_alpha.address)
    for contract in (
        teller,
        auction_house,
        credit_engine,
        human_resources,
        deleverage,
    ):
        _pause_if_needed(contract, switchboard_alpha)
    assert not source.isPaused()
    assert not lootbox.isPaused()

    assert switchboard_echo.setLegacyRipeGovMigrationAsset(
        ripe_token, sender=governance.address,
    )
    assert migrator.activeMigrationAsset() == ripe_token.address

    assert switchboard_echo.migrateLegacyRipeGovPositions(
        [bob], ripe_token, sender=governance.address,
    ) == 1
    assert source.getTotalAmountForUser(bob, ripe_token) == 0
    assert target.getTotalAmountForUser(bob, ripe_token) == amount
    assert ledger.isParticipatingInVault(bob, LEGACY_RIPE_GOV_VAULT_ID)
    assert ledger.isParticipatingInVault(bob, target_id)

    target_data = target.userGovData(bob, ripe_token)
    assert target_data.govPoints == source_data.govPoints
    assert target_data.unlock == source_data.unlock
    assert target_data.lastTerms == source_data.lastTerms

    migration_logs = filter_logs(
        switchboard_echo, "LegacyRipeGovPositionMigrationExecuted",
    )
    assert len(migration_logs) == 1
    assert migration_logs[0].caller == governance.address

    assert switchboard_echo.settleAndCleanupLegacyRipeGovSources(
        [bob], sender=governance.address,
    ) == 1
    assert not source.isUserInVaultAsset(bob, ripe_token)
    assert not ledger.isParticipatingInVault(bob, LEGACY_RIPE_GOV_VAULT_ID)
    assert ledger.isParticipatingInVault(bob, target_id)

    settlement_logs = filter_logs(
        switchboard_echo, "LegacyRipeGovSourceSettlementExecuted",
    )
    assert len(settlement_logs) == 1
    assert settlement_logs[0].caller == governance.address
    assert migrator.LEGACY_RIPE_GOV_VAULT() == source.address
    assert migrator.LEGACY_CHAIN_ID() == boa.env.evm.patch.chain_id


def test_legacy_binding_rejects_wrong_chain(
    ripe_hq,
    governance,
    ripe_gov_vault,
    ripe_token,
    switchboard_echo,
):
    _install_legacy_migrator(ripe_hq, ripe_gov_vault, governance)
    original_chain_id = boa.env.evm.patch.chain_id
    boa.env.evm.patch.chain_id = original_chain_id + 1
    try:
        with boa.reverts("legacy migration disabled"):
            switchboard_echo.setLegacyRipeGovMigrationAsset(
                ripe_token, sender=governance.address,
            )
    finally:
        boa.env.evm.patch.chain_id = original_chain_id
