import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from conf_utils import filter_logs


SOURCE_VAULT_ID = 2
ASSET_WEIGHT = 100_00
LOCK_TERMS = (100, 1_000, 200_00, True, 10_00)


def _configure_ripe_gov_asset(
    mission_control,
    setAssetConfig,
    switchboard_alpha,
    asset,
    vault_ids,
    *,
    should_freeze_when_bad_debt=False,
    lock_terms=LOCK_TERMS,
):
    mission_control.setRipeGovVaultConfig(
        asset,
        ASSET_WEIGHT,
        should_freeze_when_bad_debt,
        lock_terms,
        sender=switchboard_alpha.address,
    )
    setAssetConfig(asset, _vaultIds=vault_ids)


def _register_ripe_gov_vault(ripe_hq, vault_book, governance, label):
    vault = boa.load("contracts/vaults/RipeGov.vy", ripe_hq, name=label)
    assert vault_book.startAddNewAddressToRegistry(vault, label, sender=governance.address)
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    vault_id = vault_book.confirmNewAddressToRegistry(vault, sender=governance.address)
    assert vault_id != 0
    return vault, vault_id


@pytest.fixture
def target_ripe_gov_vault(ripe_hq, vault_book, governance):
    return _register_ripe_gov_vault(
        ripe_hq,
        vault_book,
        governance,
        "migration_target_ripe_gov_vault",
    )


def _direct_deposit(vault, token, funder, user, amount, teller, lock_duration=0, switchboard=None):
    token.transfer(vault, amount, sender=funder)
    if lock_duration == 0:
        return vault.depositTokensInVault(user, token, amount, sender=teller.address)
    return vault.depositTokensWithLockDuration(
        user,
        token,
        amount,
        lock_duration,
        sender=switchboard.address,
    )


def _save_points(vault, user, asset, switchboard_alpha, blocks=25):
    boa.env.time_travel(blocks=blocks)
    vault.updateUserGovPoints(user, sender=switchboard_alpha.address)
    data = vault.userGovData(user, asset)
    assert data.govPoints > 0
    return data


def _pause_pair(source, target, switchboard_alpha):
    source.pause(True, sender=switchboard_alpha.address)
    target.pause(True, sender=switchboard_alpha.address)


def _deposit_through_teller(
    teller,
    source,
    token,
    funder,
    user,
    amount,
    lock_duration,
):
    token.transfer(user, amount, sender=funder)
    token.approve(teller, amount, sender=user)
    deposited = teller.depositIntoGovVault(
        token,
        amount,
        lock_duration,
        user,
        sender=user,
    )
    assert deposited == amount
    assert source.getTotalAmountForUser(user, token) == amount


def _prepare_teller_migration(
    *,
    teller,
    source,
    target,
    target_id,
    token,
    funder,
    user,
    mission_control,
    setAssetConfig,
    setGeneralConfig,
    switchboard_alpha,
    amount=100 * EIGHTEEN_DECIMALS,
    lock_duration=600,
):
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        token,
        [SOURCE_VAULT_ID, target_id],
    )
    setGeneralConfig()
    _deposit_through_teller(
        teller,
        source,
        token,
        funder,
        user,
        amount,
        lock_duration,
    )
    data = _save_points(source, user, token, switchboard_alpha)
    return amount, data


def _assert_lock_terms_equal(actual, expected):
    assert actual.minLockDuration == expected.minLockDuration
    assert actual.maxLockDuration == expected.maxLockDuration
    assert actual.maxLockBoost == expected.maxLockBoost
    assert actual.canExit == expected.canExit
    assert actual.exitFee == expected.exitFee


def test_point_disable_setters_are_authorized_and_irreversible(
    ripe_gov_vault,
    switchboard_echo,
    bob,
):
    with boa.reverts("no perms"):
        ripe_gov_vault.disableGovPointAccrualForUser(bob, sender=bob)
    with boa.reverts("no perms"):
        ripe_gov_vault.disableGovPointAccrualGlobally(sender=bob)
    with boa.reverts("invalid user"):
        ripe_gov_vault.disableGovPointAccrualForUser(ZERO_ADDRESS, sender=switchboard_echo.address)

    ripe_gov_vault.disableGovPointAccrualForUser(bob, sender=switchboard_echo.address)
    user_logs = filter_logs(ripe_gov_vault, "GovPointAccrualDisabledForUser")
    disabled_block = ripe_gov_vault.userGovPointAccrualDisabledBlock(bob)
    assert disabled_block == boa.env.evm.patch.block_number
    assert len(user_logs) == 1
    assert user_logs[0].user == bob
    assert user_logs[0].disabledBlock == disabled_block
    assert user_logs[0].caller == switchboard_echo.address

    with boa.reverts("already disabled"):
        ripe_gov_vault.disableGovPointAccrualForUser(bob, sender=switchboard_echo.address)

    ripe_gov_vault.disableGovPointAccrualGlobally(sender=switchboard_echo.address)
    global_logs = filter_logs(ripe_gov_vault, "GovPointAccrualDisabledGlobally")
    global_block = ripe_gov_vault.govPointAccrualDisabledBlock()
    assert global_block == boa.env.evm.patch.block_number
    assert len(global_logs) == 1
    assert global_logs[0].disabledBlock == global_block

    with boa.reverts("already disabled"):
        ripe_gov_vault.disableGovPointAccrualGlobally(sender=switchboard_echo.address)
    with boa.reverts("globally disabled"):
        ripe_gov_vault.disableGovPointAccrualForUser(
            "0x" + "33" * 20,
            sender=switchboard_echo.address,
        )


def test_user_point_freeze_preserves_points_while_deposits_and_metadata_continue(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
    )
    _direct_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        bob,
        100 * EIGHTEEN_DECIMALS,
        teller,
        500,
        switchboard_alpha,
    )
    before = _save_points(ripe_gov_vault, bob, ripe_token, switchboard_alpha)
    before_user_total = ripe_gov_vault.totalUserGovPoints(bob)
    before_global_total = ripe_gov_vault.totalGovPoints()

    ripe_gov_vault.disableGovPointAccrualForUser(bob, sender=switchboard_echo.address)
    boa.env.time_travel(blocks=40)
    _direct_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        bob,
        50 * EIGHTEEN_DECIMALS,
        teller,
        700,
        switchboard_alpha,
    )

    after = ripe_gov_vault.userGovData(bob, ripe_token)
    assert after.govPoints == before.govPoints
    assert ripe_gov_vault.totalUserGovPoints(bob) == before_user_total
    assert ripe_gov_vault.totalGovPoints() == before_global_total
    assert after.lastShares > before.lastShares
    assert after.lastPointsUpdate == boa.env.evm.patch.block_number
    assert after.unlock > before.unlock
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 150 * EIGHTEEN_DECIMALS

    _direct_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        alice,
        20 * EIGHTEEN_DECIMALS,
        teller,
    )
    _save_points(ripe_gov_vault, alice, ripe_token, switchboard_alpha, blocks=10)
    assert ripe_gov_vault.totalUserGovPoints(alice) > 0


def test_global_point_freeze_stops_updates_for_every_user_without_zeroing(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
    )
    for user in (bob, alice):
        _direct_deposit(
            ripe_gov_vault,
            ripe_token,
            whale,
            user,
            40 * EIGHTEEN_DECIMALS,
            teller,
        )
    boa.env.time_travel(blocks=20)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    ripe_gov_vault.updateUserGovPoints(alice, sender=switchboard_alpha.address)
    bob_points = ripe_gov_vault.userGovData(bob, ripe_token).govPoints
    alice_points = ripe_gov_vault.userGovData(alice, ripe_token).govPoints
    total_points = ripe_gov_vault.totalGovPoints()
    assert bob_points > 0 and alice_points > 0

    ripe_gov_vault.disableGovPointAccrualGlobally(sender=switchboard_echo.address)
    boa.env.time_travel(blocks=50)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    ripe_gov_vault.updateUserGovPoints(alice, sender=switchboard_alpha.address)

    assert ripe_gov_vault.userGovData(bob, ripe_token).govPoints == bob_points
    assert ripe_gov_vault.userGovData(alice, ripe_token).govPoints == alice_points
    assert ripe_gov_vault.totalGovPoints() == total_points
    assert ripe_gov_vault.userGovData(bob, ripe_token).lastPointsUpdate == boa.env.evm.patch.block_number
    assert ripe_gov_vault.userGovData(alice, ripe_token).lastPointsUpdate == boa.env.evm.patch.block_number


def test_disabled_withdrawals_keep_points_frozen_and_still_enforce_unlock(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
    )
    amount = 100 * EIGHTEEN_DECIMALS
    _direct_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        bob,
        amount,
        teller,
        100,
        switchboard_alpha,
    )
    before = _save_points(ripe_gov_vault, bob, ripe_token, switchboard_alpha, blocks=20)
    total_user_points = ripe_gov_vault.totalUserGovPoints(bob)
    total_points = ripe_gov_vault.totalGovPoints()
    ripe_gov_vault.disableGovPointAccrualForUser(bob, sender=switchboard_echo.address)

    with boa.reverts("not reached unlock"):
        ripe_gov_vault.withdrawTokensFromVault(
            bob,
            ripe_token,
            10 * EIGHTEEN_DECIMALS,
            alice,
            sender=teller.address,
        )

    unlock = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    boa.env.time_travel(blocks=unlock - boa.env.evm.patch.block_number + 1)
    withdrawn, depleted = ripe_gov_vault.withdrawTokensFromVault(
        bob,
        ripe_token,
        40 * EIGHTEEN_DECIMALS,
        alice,
        sender=teller.address,
    )
    assert withdrawn == 40 * EIGHTEEN_DECIMALS
    assert not depleted
    partial = ripe_gov_vault.userGovData(bob, ripe_token)
    assert partial.govPoints == before.govPoints
    assert partial.lastShares < before.lastShares
    assert ripe_gov_vault.totalUserGovPoints(bob) == total_user_points
    assert ripe_gov_vault.totalGovPoints() == total_points

    withdrawn, depleted = ripe_gov_vault.withdrawTokensFromVault(
        bob,
        ripe_token,
        60 * EIGHTEEN_DECIMALS,
        alice,
        sender=teller.address,
    )
    assert withdrawn == 60 * EIGHTEEN_DECIMALS
    assert depleted
    emptied = ripe_gov_vault.userGovData(bob, ripe_token)
    assert emptied.govPoints == before.govPoints
    assert emptied.lastShares == 0
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert ripe_gov_vault.totalUserGovPoints(bob) == total_user_points
    assert ripe_gov_vault.totalGovPoints() == total_points


def test_disabled_points_do_not_bypass_bad_debt_withdrawal_freeze(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    ledger,
    switchboard_alpha,
    switchboard_delta,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
        should_freeze_when_bad_debt=True,
        lock_terms=(1, 1_000, 200_00, True, 10_00),
    )
    _direct_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        bob,
        50 * EIGHTEEN_DECIMALS,
        teller,
        1,
        switchboard_alpha,
    )
    ripe_gov_vault.disableGovPointAccrualForUser(bob, sender=switchboard_echo.address)
    boa.env.time_travel(blocks=2)
    ledger.setBadDebt(1, sender=switchboard_delta.address)

    with boa.reverts("cannot withdraw when bad debt"):
        ripe_gov_vault.withdrawTokensFromVault(
            bob,
            ripe_token,
            1,
            bob,
            sender=teller.address,
        )


def test_disabled_points_leave_lock_adjustment_and_release_operational(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
    )
    _direct_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        bob,
        100 * EIGHTEEN_DECIMALS,
        teller,
        400,
        switchboard_alpha,
    )
    before = _save_points(ripe_gov_vault, bob, ripe_token, switchboard_alpha)
    ripe_gov_vault.disableGovPointAccrualForUser(bob, sender=switchboard_echo.address)

    ripe_gov_vault.adjustLock(bob, ripe_token, 800, sender=switchboard_alpha.address)
    adjusted = ripe_gov_vault.userGovData(bob, ripe_token)
    assert adjusted.govPoints == before.govPoints
    assert adjusted.unlock > before.unlock

    ripe_gov_vault.releaseLock(bob, ripe_token, sender=switchboard_alpha.address)
    released = ripe_gov_vault.userGovData(bob, ripe_token)
    assert released.govPoints == before.govPoints
    assert released.unlock == 0
    assert released.lastShares < adjusted.lastShares


def test_disabled_sender_can_transfer_balance_without_moving_or_zeroing_points(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    auction_house,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
    )
    _direct_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        bob,
        100 * EIGHTEEN_DECIMALS,
        teller,
    )
    before = _save_points(ripe_gov_vault, bob, ripe_token, switchboard_alpha)
    total_points = ripe_gov_vault.totalGovPoints()
    ripe_gov_vault.disableGovPointAccrualForUser(bob, sender=switchboard_echo.address)
    boa.env.time_travel(blocks=20)

    transferred, depleted = ripe_gov_vault.transferBalanceWithinVault(
        ripe_token,
        bob,
        alice,
        40 * EIGHTEEN_DECIMALS,
        sender=auction_house.address,
    )
    assert transferred == 40 * EIGHTEEN_DECIMALS
    assert not depleted
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 60 * EIGHTEEN_DECIMALS
    assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) == 40 * EIGHTEEN_DECIMALS
    assert ripe_gov_vault.userGovData(bob, ripe_token).govPoints == before.govPoints
    assert ripe_gov_vault.userGovData(alice, ripe_token).govPoints == 0
    assert ripe_gov_vault.totalGovPoints() == total_points


def test_teller_migration_preserves_position_and_updates_ledger_and_lootbox(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    ledger,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
    setGeneralConfig,
):
    target, target_id = target_ripe_gov_vault
    amount, source_data = _prepare_teller_migration(
        teller=teller,
        source=ripe_gov_vault,
        target=target,
        target_id=target_id,
        token=ripe_token,
        funder=whale,
        user=bob,
        mission_control=mission_control,
        setAssetConfig=setAssetConfig,
        setGeneralConfig=setGeneralConfig,
        switchboard_alpha=switchboard_alpha,
    )
    assert ledger.isParticipatingInVault(bob, SOURCE_VAULT_ID)
    assert not ledger.isParticipatingInVault(bob, target_id)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    migrated = teller.migrateRipeGovPosition(
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    )
    # The source and target events are child logs of the outer Teller transaction.
    export_logs = filter_logs(teller, "RipeGovPositionExported")
    import_logs = filter_logs(teller, "RipeGovPositionImported")
    teller_logs = filter_logs(teller, "RipeGovPositionMigrated")
    assert migrated == amount
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert target.getTotalAmountForUser(bob, ripe_token) == amount
    assert ripe_gov_vault.positionMigratedOut(bob, ripe_token)
    assert ripe_gov_vault.totalUserGovPoints(bob) == 0
    assert ripe_gov_vault.totalGovPoints() == 0

    target_data = target.userGovData(bob, ripe_token)
    assert target_data.govPoints == source_data.govPoints
    assert target_data.unlock == source_data.unlock
    _assert_lock_terms_equal(target_data.lastTerms, source_data.lastTerms)
    assert target.totalUserGovPoints(bob) == source_data.govPoints
    assert target.totalGovPoints() == source_data.govPoints
    assert ledger.isParticipatingInVault(bob, target_id)

    source_bundle = ledger.getDepositPointsBundle(bob, SOURCE_VAULT_ID, ripe_token)
    target_bundle = ledger.getDepositPointsBundle(bob, target_id, ripe_token)
    assert source_bundle.userPoints.lastUpdate == boa.env.evm.patch.block_number
    assert source_bundle.userPoints.lastBalance == 0
    assert target_bundle.userPoints.lastUpdate == boa.env.evm.patch.block_number
    assert target_bundle.userPoints.lastBalance > 0

    assert len(export_logs) == len(import_logs) == len(teller_logs) == 1
    assert export_logs[0].amount == amount
    assert import_logs[0].govPoints == source_data.govPoints
    assert teller_logs[0].sourceVaultId == SOURCE_VAULT_ID
    assert teller_logs[0].targetVaultId == target_id


def test_enabled_migration_performs_one_final_governance_point_save(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
    setGeneralConfig,
):
    target, target_id = target_ripe_gov_vault
    _prepare_teller_migration(
        teller=teller,
        source=ripe_gov_vault,
        target=target,
        target_id=target_id,
        token=ripe_token,
        funder=whale,
        user=bob,
        mission_control=mission_control,
        setAssetConfig=setAssetConfig,
        setGeneralConfig=setGeneralConfig,
        switchboard_alpha=switchboard_alpha,
    )
    boa.env.time_travel(blocks=37)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)
    before = ripe_gov_vault.userGovData(bob, ripe_token)
    pending = ripe_gov_vault.getLatestGovPoints(
        before.lastShares,
        before.lastPointsUpdate,
        before.unlock,
        before.lastTerms,
        ASSET_WEIGHT,
    )
    assert pending > 0

    teller.migrateRipeGovPosition(
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    )
    assert target.userGovData(bob, ripe_token).govPoints == before.govPoints + pending


@pytest.mark.parametrize("disable_globally", [False, True])
def test_migration_carries_frozen_points_without_accruing_more(
    disable_globally,
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
    setGeneralConfig,
):
    target, target_id = target_ripe_gov_vault
    _, source_data = _prepare_teller_migration(
        teller=teller,
        source=ripe_gov_vault,
        target=target,
        target_id=target_id,
        token=ripe_token,
        funder=whale,
        user=bob,
        mission_control=mission_control,
        setAssetConfig=setAssetConfig,
        setGeneralConfig=setGeneralConfig,
        switchboard_alpha=switchboard_alpha,
    )
    if disable_globally:
        ripe_gov_vault.disableGovPointAccrualGlobally(sender=switchboard_echo.address)
    else:
        ripe_gov_vault.disableGovPointAccrualForUser(bob, sender=switchboard_echo.address)
    frozen_points = source_data.govPoints
    boa.env.time_travel(blocks=100)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    teller.migrateRipeGovPosition(
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    )
    assert target.userGovData(bob, ripe_token).govPoints == frozen_points
    assert target.totalUserGovPoints(bob) == frozen_points


def test_teller_migration_validates_authority_addresses_and_ids(
    target_ripe_gov_vault,
    ripe_token,
    bob,
    teller,
    switchboard_echo,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    _, target_id = target_ripe_gov_vault
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID, target_id],
    )
    with boa.reverts("only switchboard allowed"):
        teller.migrateRipeGovPosition(bob, ripe_token, SOURCE_VAULT_ID, target_id, sender=bob)
    with boa.reverts("invalid user or asset"):
        teller.migrateRipeGovPosition(
            ZERO_ADDRESS,
            ripe_token,
            SOURCE_VAULT_ID,
            target_id,
            sender=switchboard_echo.address,
        )
    with boa.reverts("invalid user or asset"):
        teller.migrateRipeGovPosition(
            bob,
            ZERO_ADDRESS,
            SOURCE_VAULT_ID,
            target_id,
            sender=switchboard_echo.address,
        )
    with boa.reverts("invalid vault id"):
        teller.migrateRipeGovPosition(bob, ripe_token, 0, target_id, sender=switchboard_echo.address)
    with boa.reverts("same vault"):
        teller.migrateRipeGovPosition(
            bob,
            ripe_token,
            SOURCE_VAULT_ID,
            SOURCE_VAULT_ID,
            sender=switchboard_echo.address,
        )
    with boa.reverts("invalid source vault id"):
        teller.migrateRipeGovPosition(bob, ripe_token, 999, target_id, sender=switchboard_echo.address)
    with boa.reverts("invalid target vault id"):
        teller.migrateRipeGovPosition(bob, ripe_token, SOURCE_VAULT_ID, 999, sender=switchboard_echo.address)


def test_teller_migration_requires_both_vaults_paused(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
    setGeneralConfig,
):
    target, target_id = target_ripe_gov_vault
    amount, _ = _prepare_teller_migration(
        teller=teller,
        source=ripe_gov_vault,
        target=target,
        target_id=target_id,
        token=ripe_token,
        funder=whale,
        user=bob,
        mission_control=mission_control,
        setAssetConfig=setAssetConfig,
        setGeneralConfig=setGeneralConfig,
        switchboard_alpha=switchboard_alpha,
    )
    with boa.reverts("source vault not paused"):
        teller.migrateRipeGovPosition(
            bob,
            ripe_token,
            SOURCE_VAULT_ID,
            target_id,
            sender=switchboard_echo.address,
        )

    ripe_gov_vault.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("target vault not paused"):
        teller.migrateRipeGovPosition(
            bob,
            ripe_token,
            SOURCE_VAULT_ID,
            target_id,
            sender=switchboard_echo.address,
        )

    target.pause(True, sender=switchboard_alpha.address)
    assert teller.migrateRipeGovPosition(
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    ) == amount


def test_unsupported_target_asset_reverts_without_mutating_source(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    target, target_id = target_ripe_gov_vault
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
    )
    amount = 20 * EIGHTEEN_DECIMALS
    _direct_deposit(ripe_gov_vault, ripe_token, whale, bob, amount, teller)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    with boa.reverts("unsupported target asset"):
        teller.migrateRipeGovPosition(
            bob,
            ripe_token,
            SOURCE_VAULT_ID,
            target_id,
            sender=switchboard_echo.address,
        )
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == amount
    assert not ripe_gov_vault.positionMigratedOut(bob, ripe_token)
    assert target.getTotalAmountForUser(bob, ripe_token) == 0


def test_existing_target_position_makes_entire_migration_atomic(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    target, target_id = target_ripe_gov_vault
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID, target_id],
    )
    source_amount = 30 * EIGHTEEN_DECIMALS
    target_amount = 5 * EIGHTEEN_DECIMALS
    _direct_deposit(ripe_gov_vault, ripe_token, whale, bob, source_amount, teller)
    _direct_deposit(target, ripe_token, whale, bob, target_amount, teller)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    with boa.reverts("target position exists"):
        teller.migrateRipeGovPosition(
            bob,
            ripe_token,
            SOURCE_VAULT_ID,
            target_id,
            sender=switchboard_echo.address,
        )
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == source_amount
    assert target.getTotalAmountForUser(bob, ripe_token) == target_amount
    assert not ripe_gov_vault.positionMigratedOut(bob, ripe_token)


def test_fee_on_transfer_receipt_check_reverts_atomically(
    target_ripe_gov_vault,
    ripe_hq,
    ripe_gov_vault,
    governance,
    bob,
    teller,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    target, target_id = target_ripe_gov_vault
    fee_token = boa.load(
        "contracts/mock/MockFeeOnTransferErc20.vy",
        governance.address,
        0,
        name="migration_fee_token",
    )
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        fee_token,
        [SOURCE_VAULT_ID, target_id],
    )
    amount = 100 * EIGHTEEN_DECIMALS
    _direct_deposit(ripe_gov_vault, fee_token, governance.address, bob, amount, teller)
    fee_token.setTransferFee(500, sender=governance.address)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    with boa.reverts("inexact migration receipt"):
        teller.migrateRipeGovPosition(
            bob,
            fee_token,
            SOURCE_VAULT_ID,
            target_id,
            sender=switchboard_echo.address,
        )
    assert ripe_gov_vault.getTotalAmountForUser(bob, fee_token) == amount
    assert fee_token.balanceOf(ripe_gov_vault) == amount
    assert fee_token.balanceOf(target) == 0
    assert not ripe_gov_vault.positionMigratedOut(bob, fee_token)


def test_migrated_source_position_is_permanently_tombstoned(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    auction_house,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
    setGeneralConfig,
):
    target, target_id = target_ripe_gov_vault
    _prepare_teller_migration(
        teller=teller,
        source=ripe_gov_vault,
        target=target,
        target_id=target_id,
        token=ripe_token,
        funder=whale,
        user=bob,
        mission_control=mission_control,
        setAssetConfig=setAssetConfig,
        setGeneralConfig=setGeneralConfig,
        switchboard_alpha=switchboard_alpha,
    )
    _direct_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        alice,
        10 * EIGHTEEN_DECIMALS,
        teller,
    )
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)
    teller.migrateRipeGovPosition(
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    )

    ripe_gov_vault.pause(False, sender=switchboard_alpha.address)
    with boa.reverts("position migrated"):
        ripe_gov_vault.depositTokensWithLockDuration(
            bob,
            ripe_token,
            1,
            100,
            sender=switchboard_alpha.address,
        )
    alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    with boa.reverts("recipient position migrated"):
        ripe_gov_vault.transferBalanceWithinVault(
            ripe_token,
            alice,
            bob,
            1,
            sender=auction_house.address,
        )
    assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) == alice_balance


def test_non_core_registered_ripe_gov_vault_can_be_the_migration_source(
    ripe_hq,
    vault_book,
    governance,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    source, source_id = _register_ripe_gov_vault(
        ripe_hq,
        vault_book,
        governance,
        "non_core_migration_source",
    )
    target, target_id = _register_ripe_gov_vault(
        ripe_hq,
        vault_book,
        governance,
        "non_core_migration_target",
    )
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID, source_id, target_id],
    )
    amount = 25 * EIGHTEEN_DECIMALS
    _direct_deposit(source, ripe_token, whale, bob, amount, teller)
    _save_points(source, bob, ripe_token, switchboard_alpha)
    _pause_pair(source, target, switchboard_alpha)

    assert teller.migrateRipeGovPosition(
        bob,
        ripe_token,
        source_id,
        target_id,
        sender=switchboard_echo.address,
    ) == amount
    assert source.positionMigratedOut(bob, ripe_token)
    assert target.getTotalAmountForUser(bob, ripe_token) == amount


def test_actual_hr_contributor_position_migrates_with_points_and_lock(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    alice,
    bob,
    teller,
    ledger,
    human_resources,
    contributor_template,
    governance,
    switchboard_alpha,
    switchboard_delta,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    target, target_id = target_ripe_gov_vault
    compensation = 1_000 * EIGHTEEN_DECIMALS
    mission_control.setHrConfig(
        (contributor_template, compensation, 1, 100, 100, 1_000),
        sender=switchboard_delta.address,
    )
    ledger.setRipeAvailForHr(compensation, sender=switchboard_delta.address)
    action_id = human_resources.initiateNewContributor(
        alice,
        bob,
        compensation,
        0,
        500,
        100,
        200,
        300,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=human_resources.actionTimeLock())
    assert human_resources.confirmNewContributor(action_id, sender=governance.address)
    contributor = filter_logs(human_resources, "NewContributorConfirmed")[0].contributorAddr
    assert ledger.isHrContributor(contributor)

    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID, target_id],
    )
    amount = 75 * EIGHTEEN_DECIMALS
    _direct_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        contributor,
        amount,
        teller,
        450,
        switchboard_alpha,
    )
    source_data = _save_points(
        ripe_gov_vault,
        contributor,
        ripe_token,
        switchboard_alpha,
    )
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    teller.migrateRipeGovPosition(
        contributor,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    )
    target_data = target.userGovData(contributor, ripe_token)
    assert target.getTotalAmountForUser(contributor, ripe_token) == amount
    assert target_data.govPoints == source_data.govPoints
    assert target_data.unlock == source_data.unlock
    _assert_lock_terms_equal(target_data.lastTerms, source_data.lastTerms)
    assert ledger.isHrContributor(contributor)
    assert ledger.isParticipatingInVault(contributor, target_id)


def test_echo_disable_validator_returns_false_instead_of_reverting(
    switchboard_echo,
    ripe_gov_vault,
    simple_erc20_vault,
    vault_book,
    bob,
):
    ripe_gov_id = vault_book.getRegId(ripe_gov_vault)
    simple_vault_id = vault_book.getRegId(simple_erc20_vault)
    assert ripe_gov_id == SOURCE_VAULT_ID
    assert switchboard_echo.isValidRipeGovPointAccrualDisable(0, bob) is False
    assert switchboard_echo.isValidRipeGovPointAccrualDisable(999, bob) is False
    assert switchboard_echo.isValidRipeGovPointAccrualDisable(simple_vault_id, bob) is False
    assert switchboard_echo.isValidRipeGovPointAccrualDisable(ripe_gov_id, bob) is True


def test_echo_user_disable_timelock_flow_and_revalidation(
    switchboard_echo,
    ripe_gov_vault,
    governance,
    bob,
    alice,
):
    with boa.reverts("no perms"):
        switchboard_echo.disableRipeGovPointAccrualForUser(SOURCE_VAULT_ID, bob, sender=alice)
    with boa.reverts("invalid user"):
        switchboard_echo.disableRipeGovPointAccrualForUser(
            SOURCE_VAULT_ID,
            ZERO_ADDRESS,
            sender=governance.address,
        )

    action_id = switchboard_echo.disableRipeGovPointAccrualForUser(
        SOURCE_VAULT_ID,
        bob,
        sender=governance.address,
    )
    pending_logs = filter_logs(switchboard_echo, "PendingRipeGovPointAccrualUserDisable")
    pending = switchboard_echo.pendingRipeGovPointAccrualDisableActions(action_id)
    assert pending.vaultId == SOURCE_VAULT_ID
    assert pending.vaultAddr == ripe_gov_vault.address
    assert pending.user == bob
    assert len(pending_logs) == 1
    assert pending_logs[0].actionId == action_id
    assert switchboard_echo.executePendingAction(action_id, sender=governance.address) is False

    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())
    assert switchboard_echo.executePendingAction(action_id, sender=governance.address) is True
    executed = filter_logs(switchboard_echo, "RipeGovPointAccrualUserDisableExecuted")
    assert ripe_gov_vault.userGovPointAccrualDisabledBlock(bob) != 0
    assert switchboard_echo.actionType(action_id) == 0
    assert switchboard_echo.isValidRipeGovPointAccrualDisable(SOURCE_VAULT_ID, bob) is False
    assert len(executed) == 1
    assert executed[0].user == bob


def test_echo_global_disable_timelock_flow(
    switchboard_echo,
    ripe_gov_vault,
    governance,
    bob,
):
    with boa.reverts("no perms"):
        switchboard_echo.disableRipeGovPointAccrualGlobally(SOURCE_VAULT_ID, sender=bob)
    action_id = switchboard_echo.disableRipeGovPointAccrualGlobally(
        SOURCE_VAULT_ID,
        sender=governance.address,
    )
    pending = switchboard_echo.pendingRipeGovPointAccrualDisableActions(action_id)
    assert pending.vaultId == SOURCE_VAULT_ID
    assert pending.vaultAddr == ripe_gov_vault.address
    assert pending.user == ZERO_ADDRESS
    assert switchboard_echo.executePendingAction(action_id, sender=governance.address) is False

    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())
    assert switchboard_echo.executePendingAction(action_id, sender=governance.address) is True
    executed = filter_logs(switchboard_echo, "RipeGovPointAccrualGlobalDisableExecuted")
    assert ripe_gov_vault.govPointAccrualDisabledBlock() != 0
    assert switchboard_echo.isValidRipeGovPointAccrualDisable(SOURCE_VAULT_ID, bob) is False
    assert len(executed) == 1


def test_echo_batch_migrates_many_users_and_emits_one_event_each(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    governance,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    target, target_id = target_ripe_gov_vault
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID, target_id],
    )
    amounts = {
        bob: 20 * EIGHTEEN_DECIMALS,
        alice: 35 * EIGHTEEN_DECIMALS,
    }
    for user, amount in amounts.items():
        _direct_deposit(ripe_gov_vault, ripe_token, whale, user, amount, teller)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)
    migrations = [
        (user, ripe_token.address, SOURCE_VAULT_ID, target_id)
        for user in amounts
    ]

    assert switchboard_echo.migrateRipeGovPositions(
        migrations,
        sender=governance.address,
    ) == 2
    for user, amount in amounts.items():
        assert ripe_gov_vault.getTotalAmountForUser(user, ripe_token) == 0
        assert target.getTotalAmountForUser(user, ripe_token) == amount
    logs = filter_logs(switchboard_echo, "RipeGovPositionMigrationExecuted")
    assert len(logs) == 2
    assert {log.user for log in logs} == set(amounts)


def test_echo_batch_is_governance_only_nonempty_and_atomic(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    governance,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    target, target_id = target_ripe_gov_vault
    with boa.reverts("no perms"):
        switchboard_echo.migrateRipeGovPositions([], sender=bob)
    with boa.reverts("no migrations"):
        switchboard_echo.migrateRipeGovPositions([], sender=governance.address)

    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID, target_id],
    )
    amount = 40 * EIGHTEEN_DECIMALS
    _direct_deposit(ripe_gov_vault, ripe_token, whale, bob, amount, teller)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)
    migrations = [
        (bob, ripe_token.address, SOURCE_VAULT_ID, target_id),
        (alice, ripe_token.address, SOURCE_VAULT_ID, target_id),
    ]

    with boa.reverts("no position"):
        switchboard_echo.migrateRipeGovPositions(migrations, sender=governance.address)
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == amount
    assert target.getTotalAmountForUser(bob, ripe_token) == 0
    assert not ripe_gov_vault.positionMigratedOut(bob, ripe_token)
