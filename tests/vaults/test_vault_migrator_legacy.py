import boa
from constants import EIGHTEEN_DECIMALS, VAULT_MIGRATOR_HQ_ID
from conf_utils import filter_logs


LEGACY_RIPE_GOV_VAULT_ID = 2
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


def test_default_vault_migrator_disables_base_legacy_route(
    switchboard_echo, governance, bob,
):
    with boa.reverts("legacy migration disabled"):
        switchboard_echo.migrateLegacyRipeGovPositions(
            [bob], sender=governance.address,
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
