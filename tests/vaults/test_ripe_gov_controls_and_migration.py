import pytest
import boa
from boa.contracts.base_evm_contract import BoaError

from constants import (
    EIGHTEEN_DECIMALS,
    MAX_UINT256,
    ZERO_ADDRESS,
    VAULT_MIGRATOR_HQ_ID,
)
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


def _classify_ripe_gov_vault(mission_control, switchboard_alpha, vault_id):
    """Model the governed pointer move that grants Boardroom callback authority."""
    mission_control.setCoreRipeGovVaultId(
        vault_id,
        sender=switchboard_alpha.address,
    )
    assert mission_control.isRipeGovVaultId(vault_id)


def _replace_hq_address(ripe_hq, governance, reg_id, new_address):
    assert ripe_hq.startAddressUpdateToRegistry(
        reg_id,
        new_address,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock())
    assert ripe_hq.confirmAddressUpdateToRegistry(
        reg_id,
        sender=governance.address,
    )


@pytest.fixture
def target_ripe_gov_vault(ripe_hq, vault_book, governance):
    return _register_ripe_gov_vault(
        ripe_hq,
        vault_book,
        governance,
        "migration_target_ripe_gov_vault",
    )


def _direct_deposit(vault, token, funder, user, amount, teller, lock_duration=0, switchboard=None):
    # `switchboard` is retained only so existing call sites keep working; RipeGov
    # now accepts these deposits from Teller alone.
    token.transfer(vault, amount, sender=funder)
    if lock_duration == 0:
        return vault.depositTokensInVault(user, token, amount, sender=teller.address)
    return vault.depositTokensWithLockDuration(
        user,
        token,
        amount,
        lock_duration,
        sender=teller.address,
    )


def _save_points(vault, user, asset, switchboard_alpha, blocks=25):
    boa.env.time_travel(blocks=blocks)
    vault.updateUserGovPoints(user, sender=switchboard_alpha.address)
    data = vault.userGovData(user, asset)
    assert data.govPoints > 0
    return data


def _pause_pair(source, target, switchboard_alpha):
    hq = boa.load_partial("contracts/registries/RipeHq.vy").at(source.getRipeHq())
    teller = boa.load_partial("contracts/core/Teller.vy").at(hq.getAddr(17))
    if not teller.isPaused():
        teller.pause(True, sender=switchboard_alpha.address)
    source.pause(True, sender=switchboard_alpha.address)
    target.pause(True, sender=switchboard_alpha.address)


def _migrate_ripe_gov(
    teller, user, token, source_id, target_id, *, sender, return_event=False,
):
    """Point core governance at the target, then migrate all supported user assets."""
    hq = boa.load_partial("contracts/registries/RipeHq.vy").at(teller.getRipeHq())
    vault_migrator = boa.load_partial("contracts/core/VaultMigrator.vy").at(
        hq.getAddr(VAULT_MIGRATOR_HQ_ID)
    )
    caller_addr = sender.address if hasattr(sender, "address") else sender
    switchboard = boa.load_partial("contracts/registries/Switchboard.vy").at(hq.getAddr(6))
    if switchboard.isSwitchboardAddr(caller_addr) and target_id != 0:
        mission_control = boa.load_partial("contracts/data/MissionControl.vy").at(hq.getAddr(5))
        mission_control.setCoreRipeGovVaultId(target_id, sender=caller_addr)
    count = vault_migrator.migrateRipeGovPositions(
        [user], source_id, sender=caller_addr
    )
    events = filter_logs(vault_migrator, "RipeGovPositionMigrationExecuted")
    assert len(events) == count
    token_addr = token.address if hasattr(token, "address") else token
    matching = [event for event in events if event.asset == token_addr]
    event = matching[-1] if matching else None
    if return_event:
        return (event.amount if event else 0), vault_migrator
    return event.amount if event else 0


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
    if not teller.isPaused():
        teller.pause(True, sender=switchboard_alpha.address)
    return amount, data


def _assert_lock_terms_equal(actual, expected):
    assert actual.minLockDuration == expected.minLockDuration
    assert actual.maxLockDuration == expected.maxLockDuration
    assert actual.maxLockBoost == expected.maxLockBoost
    assert actual.canExit == expected.canExit
    assert actual.exitFee == expected.exitFee


def _boardroom_recorder():
    return boa.loads(
        """# @version 0.4.3
count: public(uint256)
lastUser: public(address)
lastUserGovPoints: public(uint256)
lastTotalGovPoints: public(uint256)
shouldRevert: public(bool)

@external
def setShouldRevert(_shouldRevert: bool):
    self.shouldRevert = _shouldRevert

@external
def govPowerDidChangeForUser(
    _user: address,
    _userGovPoints: uint256,
    _totalGovPoints: uint256,
):
    assert not self.shouldRevert
    self.count += 1
    self.lastUser = _user
    self.lastUserGovPoints = _userGovPoints
    self.lastTotalGovPoints = _totalGovPoints
""",
        name="ripe_gov_boardroom_recorder",
    )


def _with_boardroom(vault, recorder):
    return vault.getAddys()._replace(boardroom=recorder.address)


def _assert_contributor_transfer_case(
    *,
    ripe_gov_vault,
    ripe_token,
    whale,
    sender,
    recipient,
    unrelated,
    teller,
    human_resources,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
    disable_sender,
    disable_recipient,
):
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
    )
    amount = 100 * EIGHTEEN_DECIMALS
    _direct_deposit(ripe_gov_vault, ripe_token, whale, sender, amount, teller)
    sender_data = _save_points(
        ripe_gov_vault,
        sender,
        ripe_token,
        switchboard_alpha,
    )
    points = sender_data.govPoints
    assert points > 0
    assert ripe_gov_vault.totalUserGovPoints(sender) == points
    assert ripe_gov_vault.totalGovPoints() == points

    if disable_sender:
        ripe_gov_vault.disableGovPointAccrualForUser(
            sender,
            sender=switchboard_echo.address,
        )
    if disable_recipient:
        ripe_gov_vault.disableGovPointAccrualForUser(
            recipient,
            sender=switchboard_echo.address,
        )

    custody_before = ripe_token.balanceOf(ripe_gov_vault)
    unrelated_before = (
        ripe_gov_vault.getTotalAmountForUser(unrelated, ripe_token),
        ripe_gov_vault.totalUserGovPoints(unrelated),
    )
    transferred = ripe_gov_vault.transferContributorRipeTokens(
        sender,
        recipient,
        500,
        sender=human_resources.address,
    )
    logs = filter_logs(ripe_gov_vault, "RipeTokensTransferred")
    assert transferred == amount
    assert ripe_token.balanceOf(ripe_gov_vault) == custody_before == amount
    assert ripe_gov_vault.getTotalAmountForUser(sender, ripe_token) == 0
    assert ripe_gov_vault.userBalances(sender, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(recipient, ripe_token) == amount
    assert ripe_gov_vault.userBalances(recipient, ripe_token) > 0

    # This is a full-position transfer. D-05 clears the sender's stored points
    # at the complete per-asset exit boundary, including for disabled users.
    expected_sender = 0
    expected_recipient = 0 if disable_sender or disable_recipient else points
    expected_global = expected_recipient
    assert ripe_gov_vault.totalUserGovPoints(sender) == expected_sender
    assert ripe_gov_vault.totalUserGovPoints(recipient) == expected_recipient
    assert ripe_gov_vault.totalGovPoints() == expected_global
    assert (
        ripe_gov_vault.totalUserGovPoints(sender)
        + ripe_gov_vault.totalUserGovPoints(recipient)
    ) == expected_sender + expected_recipient
    assert (
        ripe_gov_vault.getTotalAmountForUser(unrelated, ripe_token),
        ripe_gov_vault.totalUserGovPoints(unrelated),
    ) == unrelated_before

    assert len(logs) == 1
    assert logs[0].fromUser == sender
    assert logs[0].toUser == recipient
    assert logs[0].amount == amount


def test_contributor_transfer_enabled_users_moves_tokens_and_points(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    charlie,
    teller,
    human_resources,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    _assert_contributor_transfer_case(
        ripe_gov_vault=ripe_gov_vault,
        ripe_token=ripe_token,
        whale=whale,
        sender=bob,
        recipient=alice,
        unrelated=charlie,
        teller=teller,
        human_resources=human_resources,
        switchboard_alpha=switchboard_alpha,
        switchboard_echo=switchboard_echo,
        mission_control=mission_control,
        setAssetConfig=setAssetConfig,
        disable_sender=False,
        disable_recipient=False,
    )


def test_contributor_transfer_from_disabled_sender_moves_tokens_without_points(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    charlie,
    teller,
    human_resources,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    _assert_contributor_transfer_case(
        ripe_gov_vault=ripe_gov_vault,
        ripe_token=ripe_token,
        whale=whale,
        sender=bob,
        recipient=alice,
        unrelated=charlie,
        teller=teller,
        human_resources=human_resources,
        switchboard_alpha=switchboard_alpha,
        switchboard_echo=switchboard_echo,
        mission_control=mission_control,
        setAssetConfig=setAssetConfig,
        disable_sender=True,
        disable_recipient=False,
    )


def test_contributor_transfer_to_disabled_recipient_accounts_for_dropped_points_exactly(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    charlie,
    teller,
    human_resources,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    _assert_contributor_transfer_case(
        ripe_gov_vault=ripe_gov_vault,
        ripe_token=ripe_token,
        whale=whale,
        sender=bob,
        recipient=alice,
        unrelated=charlie,
        teller=teller,
        human_resources=human_resources,
        switchboard_alpha=switchboard_alpha,
        switchboard_echo=switchboard_echo,
        mission_control=mission_control,
        setAssetConfig=setAssetConfig,
        disable_sender=False,
        disable_recipient=True,
    )


def test_contributor_transfer_between_disabled_users_does_not_move_points(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    charlie,
    teller,
    human_resources,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    _assert_contributor_transfer_case(
        ripe_gov_vault=ripe_gov_vault,
        ripe_token=ripe_token,
        whale=whale,
        sender=bob,
        recipient=alice,
        unrelated=charlie,
        teller=teller,
        human_resources=human_resources,
        switchboard_alpha=switchboard_alpha,
        switchboard_echo=switchboard_echo,
        mission_control=mission_control,
        setAssetConfig=setAssetConfig,
        disable_sender=True,
        disable_recipient=True,
    )


def test_enabled_user_point_update_calls_boardroom_once_with_final_points(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
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
        50 * EIGHTEEN_DECIMALS,
        teller,
    )
    recorder = _boardroom_recorder()
    custom_addys = _with_boardroom(ripe_gov_vault, recorder)
    boa.env.time_travel(blocks=25)
    ripe_gov_vault.updateUserGovPoints(
        bob,
        custom_addys,
        sender=switchboard_alpha.address,
    )

    final_user_points = ripe_gov_vault.totalUserGovPoints(bob)
    final_total_points = ripe_gov_vault.totalGovPoints()
    assert final_user_points > 0
    assert recorder.count() == 1
    assert recorder.lastUser() == bob
    assert recorder.lastUserGovPoints() == final_user_points
    assert recorder.lastTotalGovPoints() == final_total_points

    recorder.setShouldRevert(True)
    boa.env.time_travel(blocks=1)
    data_before = ripe_gov_vault.userGovData(bob, ripe_token)
    with boa.reverts():
        ripe_gov_vault.updateUserGovPoints(
            bob,
            custom_addys,
            sender=switchboard_alpha.address,
        )
    assert ripe_gov_vault.userGovData(bob, ripe_token) == data_before
    assert ripe_gov_vault.totalUserGovPoints(bob) == final_user_points
    assert ripe_gov_vault.totalGovPoints() == final_total_points
    assert recorder.count() == 1


def test_disabled_user_point_update_skips_boardroom_and_point_mutation(
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
        50 * EIGHTEEN_DECIMALS,
        teller,
    )
    saved = _save_points(
        ripe_gov_vault,
        bob,
        ripe_token,
        switchboard_alpha,
    )
    recorder = _boardroom_recorder()
    custom_addys = _with_boardroom(ripe_gov_vault, recorder)
    ripe_gov_vault.disableGovPointAccrualForUser(
        bob,
        sender=switchboard_echo.address,
    )
    boa.env.time_travel(blocks=25)
    ripe_gov_vault.updateUserGovPoints(
        bob,
        custom_addys,
        sender=switchboard_alpha.address,
    )

    assert recorder.count() == 0
    assert ripe_gov_vault.userGovData(bob, ripe_token).govPoints == saved.govPoints
    assert ripe_gov_vault.totalUserGovPoints(bob) == saved.govPoints
    assert ripe_gov_vault.totalGovPoints() == saved.govPoints


def test_point_disable_setters_are_authorized_and_irreversible(
    ripe_gov_vault,
    switchboard_echo,
    vault_migrator,
    bob,
):
    with boa.reverts("no perms"):
        ripe_gov_vault.disableGovPointAccrualForUser(bob, sender=bob)
    with boa.reverts("no perms"):
        ripe_gov_vault.disableGovPointAccrualForUser(
            bob,
            sender=vault_migrator.address,
        )
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


def test_disabled_partial_withdrawal_preserves_points_and_full_exit_clears_them(
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
    assert emptied.govPoints == 0
    assert emptied.lastShares == 0
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert ripe_gov_vault.totalUserGovPoints(bob) == total_user_points - before.govPoints
    assert ripe_gov_vault.totalGovPoints() == total_points - before.govPoints


def test_early_release_preserves_points_that_equivalent_partial_withdrawal_reduces(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    sally,
    teller,
    switchboard_alpha,
    mission_control,
    setAssetConfig,
):
    """Pin the accepted early-release versus ordinary-withdrawal asymmetry."""
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
        lock_terms=(*LOCK_TERMS[:4], 50_00),
    )
    amount = 100 * EIGHTEEN_DECIMALS
    _direct_deposit(ripe_gov_vault, ripe_token, whale, bob, amount, teller, 500)
    _direct_deposit(ripe_gov_vault, ripe_token, whale, alice, amount, teller, 100)
    _direct_deposit(ripe_gov_vault, ripe_token, whale, sally, amount, teller)
    boa.env.time_travel(blocks=101)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    ripe_gov_vault.updateUserGovPoints(alice, sender=switchboard_alpha.address)

    bob_before = ripe_gov_vault.userGovData(bob, ripe_token)
    alice_before = ripe_gov_vault.userGovData(alice, ripe_token)
    assert bob_before.unlock > boa.env.evm.patch.block_number
    assert alice_before.unlock <= boa.env.evm.patch.block_number
    assert bob_before.govPoints > 0 and alice_before.govPoints > 0

    with boa.env.anchor():
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)
        bob_after = ripe_gov_vault.userGovData(bob, ripe_token)
        released_shares = bob_before.lastShares - bob_after.lastShares
        assert released_shares > 0
        assert bob_after.govPoints == bob_before.govPoints

    ordinary_amount = ripe_gov_vault.sharesToAmount(
        ripe_token,
        released_shares,
        False,
    )
    if (
        ripe_gov_vault.amountToShares(ripe_token, ordinary_amount, True)
        != released_shares
    ):
        ordinary_amount = ripe_gov_vault.sharesToAmount(
            ripe_token,
            released_shares,
            True,
        )
    assert (
        ripe_gov_vault.amountToShares(ripe_token, ordinary_amount, True)
        == released_shares
    )

    ripe_gov_vault.withdrawTokensFromVault(
        alice,
        ripe_token,
        ordinary_amount,
        alice,
        sender=teller.address,
    )
    alice_after = ripe_gov_vault.userGovData(alice, ripe_token)
    assert alice_before.lastShares - alice_after.lastShares == released_shares
    expected_reduction = (
        alice_before.govPoints * released_shares // alice_before.lastShares
    )
    assert alice_after.govPoints == alice_before.govPoints - expected_reduction
    assert alice_after.govPoints < alice_before.govPoints


def test_full_fee_point_stock_cannot_migrate_but_reattaches_and_final_exit_clears(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    switchboard_alpha,
    mission_control,
    setAssetConfig,
):
    target, _ = target_ripe_gov_vault
    full_fee_terms = (*LOCK_TERMS[:4], 100_00)
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
        lock_terms=full_fee_terms,
    )
    _direct_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        bob,
        60 * EIGHTEEN_DECIMALS,
        teller,
        500,
    )
    _direct_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        alice,
        40 * EIGHTEEN_DECIMALS,
        teller,
    )
    before = _save_points(
        ripe_gov_vault,
        bob,
        ripe_token,
        switchboard_alpha,
    )

    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)
    zero_share = ripe_gov_vault.userGovData(bob, ripe_token)
    assert zero_share.lastShares == 0
    assert zero_share.govPoints == before.govPoints
    assert ripe_gov_vault.totalUserGovPoints(bob) == before.govPoints

    boa.env.time_travel(blocks=25)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    assert ripe_gov_vault.userGovData(bob, ripe_token).govPoints == before.govPoints

    ripe_gov_vault.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("no position"):
        ripe_gov_vault.exportPositionForMigration(
            bob,
            ripe_token,
            target,
            sender=teller.address,
        )
    assert ripe_gov_vault.userGovData(bob, ripe_token).govPoints == before.govPoints

    ripe_gov_vault.pause(False, sender=switchboard_alpha.address)
    _direct_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        bob,
        20 * EIGHTEEN_DECIMALS,
        teller,
    )
    reattached = ripe_gov_vault.userGovData(bob, ripe_token)
    assert reattached.lastShares > 0
    assert reattached.govPoints == before.govPoints

    boa.env.time_travel(
        blocks=reattached.unlock - boa.env.evm.patch.block_number + 1
    )
    _, depleted = ripe_gov_vault.withdrawTokensFromVault(
        bob,
        ripe_token,
        MAX_UINT256,
        bob,
        sender=teller.address,
    )
    assert depleted
    final = ripe_gov_vault.userGovData(bob, ripe_token)
    assert final.lastShares == 0
    assert final.govPoints == 0
    assert ripe_gov_vault.totalUserGovPoints(bob) == 0


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
        400,
        switchboard_alpha,
    )
    _direct_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        alice,
        100 * EIGHTEEN_DECIMALS,
        teller,
    )
    before = _save_points(ripe_gov_vault, bob, ripe_token, switchboard_alpha)
    ripe_gov_vault.disableGovPointAccrualForUser(bob, sender=switchboard_echo.address)

    ripe_gov_vault.adjustLock(bob, ripe_token, 800, sender=teller.address)
    adjusted = ripe_gov_vault.userGovData(bob, ripe_token)
    assert adjusted.govPoints == before.govPoints
    assert adjusted.unlock > before.unlock

    ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)
    released = ripe_gov_vault.userGovData(bob, ripe_token)
    assert released.govPoints == before.govPoints
    assert released.unlock == 0
    assert released.lastShares < adjusted.lastShares


def test_disabled_sender_partial_transfer_preserves_and_full_transfer_clears_points(
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

    transferred, depleted = ripe_gov_vault.transferBalanceWithinVault(
        ripe_token,
        bob,
        alice,
        60 * EIGHTEEN_DECIMALS,
        sender=auction_house.address,
    )
    assert transferred == 60 * EIGHTEEN_DECIMALS
    assert depleted
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) == 100 * EIGHTEEN_DECIMALS
    assert ripe_gov_vault.userGovData(bob, ripe_token).govPoints == 0
    assert ripe_gov_vault.userGovData(alice, ripe_token).govPoints == 0
    assert ripe_gov_vault.totalUserGovPoints(bob) == 0
    assert ripe_gov_vault.totalGovPoints() == total_points - before.govPoints


def test_reverting_boardroom_cannot_block_disabled_sender_full_exit(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    auction_house,
    boardroom,
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
    )
    before = _save_points(ripe_gov_vault, bob, ripe_token, switchboard_alpha)
    total_points = ripe_gov_vault.totalGovPoints()
    ripe_gov_vault.disableGovPointAccrualForUser(
        bob,
        sender=switchboard_echo.address,
    )

    # Any call into this code reverts. The sender's callback is already skipped
    # by disabled accrual; this specifically proves the healthy recipient's
    # callback cannot strand the disabled sender's emergency exit.
    with boa.env.anchor():
        boa.env.set_code(boardroom.address, bytes.fromhex("60006000fd"))
        transferred, depleted = ripe_gov_vault.transferBalanceWithinVault(
            ripe_token,
            bob,
            alice,
            amount,
            sender=auction_house.address,
        )
        assert transferred == amount
        assert depleted
        assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
        assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) == amount
        assert ripe_gov_vault.userGovData(bob, ripe_token).govPoints == 0
        assert ripe_gov_vault.userGovData(alice, ripe_token).govPoints == 0
        assert ripe_gov_vault.totalUserGovPoints(bob) == 0
        assert ripe_gov_vault.totalGovPoints() == total_points - before.govPoints


def _prepare_direct_export(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
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
    amount = 60 * EIGHTEEN_DECIMALS
    _direct_deposit(ripe_gov_vault, ripe_token, whale, bob, amount, teller)
    data = _save_points(
        ripe_gov_vault,
        bob,
        ripe_token,
        switchboard_alpha,
    )
    return amount, data


def test_direct_export_rejects_invalid_migration_context_atomically(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    switchboard_alpha,
    mission_control,
    setAssetConfig,
):
    target, _ = target_ripe_gov_vault
    amount, data = _prepare_direct_export(
        ripe_gov_vault,
        ripe_token,
        whale,
        bob,
        teller,
        switchboard_alpha,
        mission_control,
        setAssetConfig,
    )

    def assert_source_unchanged():
        assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == amount
        assert ripe_gov_vault.userGovData(bob, ripe_token) == data
        assert ripe_gov_vault.totalUserGovPoints(bob) == data.govPoints
        assert ripe_gov_vault.totalGovPoints() == data.govPoints
        assert not ripe_gov_vault.positionMigratedOut(bob, ripe_token)
        assert ripe_token.balanceOf(target) == 0

    with boa.reverts("only Teller allowed"):
        ripe_gov_vault.exportPositionForMigration(
            bob,
            ripe_token,
            target,
            sender=alice,
        )
    assert_source_unchanged()
    with boa.reverts("vault not paused"):
        ripe_gov_vault.exportPositionForMigration(
            bob,
            ripe_token,
            target,
            sender=teller.address,
        )
    assert_source_unchanged()

    ripe_gov_vault.pause(True, sender=switchboard_alpha.address)
    invalid_targets = (
        (ZERO_ADDRESS, "invalid migration address"),
        (alice, "invalid target vault"),
        (ripe_gov_vault.address, "invalid target vault"),
    )
    for invalid_target, expected_dev in invalid_targets:
        with boa.reverts(dev=expected_dev):
            ripe_gov_vault.exportPositionForMigration(
                bob,
                ripe_token,
                invalid_target,
                sender=teller.address,
            )
        assert_source_unchanged()
    with boa.reverts("no position"):
        ripe_gov_vault.exportPositionForMigration(
            alice,
            ripe_token,
            target,
            sender=teller.address,
        )
    assert_source_unchanged()


def test_direct_export_moves_full_position_and_sets_tombstone(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
    mission_control,
    setAssetConfig,
):
    target, _ = target_ripe_gov_vault
    amount, data = _prepare_direct_export(
        ripe_gov_vault,
        ripe_token,
        whale,
        bob,
        teller,
        switchboard_alpha,
        mission_control,
        setAssetConfig,
    )
    source_shares = ripe_gov_vault.userBalances(bob, ripe_token)
    ripe_gov_vault.pause(True, sender=switchboard_alpha.address)

    migration = ripe_gov_vault.exportPositionForMigration(
        bob,
        ripe_token,
        target,
        sender=teller.address,
    )
    assert migration.amount == amount
    assert migration.govPoints == data.govPoints
    assert migration.unlock == data.unlock
    _assert_lock_terms_equal(migration.lastTerms, data.lastTerms)
    assert source_shares > 0
    assert ripe_gov_vault.userBalances(bob, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert ripe_gov_vault.totalUserGovPoints(bob) == 0
    assert ripe_gov_vault.totalGovPoints() == 0
    assert ripe_gov_vault.positionMigratedOut(bob, ripe_token)
    assert ripe_token.balanceOf(target) == amount
    with boa.reverts("position already migrated"):
        ripe_gov_vault.exportPositionForMigration(
            bob,
            ripe_token,
            target,
            sender=teller.address,
        )


def test_direct_export_emits_complete_event(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
    mission_control,
    setAssetConfig,
):
    target, _ = target_ripe_gov_vault
    amount, data = _prepare_direct_export(
        ripe_gov_vault,
        ripe_token,
        whale,
        bob,
        teller,
        switchboard_alpha,
        mission_control,
        setAssetConfig,
    )
    source_shares = ripe_gov_vault.userBalances(bob, ripe_token)
    ripe_gov_vault.pause(True, sender=switchboard_alpha.address)
    ripe_gov_vault.exportPositionForMigration(
        bob,
        ripe_token,
        target,
        sender=teller.address,
    )

    logs = filter_logs(ripe_gov_vault, "RipeGovPositionExported")
    assert len(logs) == 1
    event = logs[0]
    assert event.user == bob
    assert event.asset == ripe_token.address
    assert event.targetVault == target.address
    assert event.amount == amount
    assert event.sourceShares == source_shares
    assert event.govPoints == data.govPoints
    assert event.unlock == data.unlock


def _migration_payload(amount, points=123):
    return (amount, points, 777, LOCK_TERMS)


# Defensive migration guards that cannot be reached through the public RipeGov
# state machine are intentionally dispositioned here instead of manufactured by
# mutating production storage:
#
# - `inconsistent position shares`: every public share mutation updates
#   GovData.lastShares in the same transaction.
# - `inconsistent user gov points` / `inconsistent global gov points`: every
#   public point mutation updates the per-user and global aggregates atomically.
# - `partial migration`: export always asks `_calcWithdrawalSharesAndAmount` for
#   max_value(uint256), so the helper returns the full starting share balance.
# - `incomplete migration`: reducing that exact full balance necessarily removes
#   all shares and reports depletion while VaultData invariants hold.
# - `target balance exists`: public balance creation also creates the asset index,
#   so the earlier `target position exists` guard fires first.
# - `target gov data exists` / `target terms exist`: public GovData creation is
#   coupled to position creation, so the earlier position guard fires first.
#
# The reachable tombstone and zero-target-share guards have dedicated tests
# below. These dispositions are defensive-code reachability statements, not
# claims that the guards are unnecessary.


def test_direct_import_rejects_invalid_migration_context_atomically(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    switchboard_alpha,
    ledger,
):
    target, target_id = target_ripe_gov_vault
    amount = 25 * EIGHTEEN_DECIMALS

    def assert_target_empty():
        assert target.getTotalAmountForUser(bob, ripe_token) == 0
        assert target.userBalances(bob, ripe_token) == 0
        assert target.totalUserGovPoints(bob) == 0
        assert target.totalGovPoints() == 0
        assert not ledger.isParticipatingInVault(bob, target_id)

    with boa.reverts("only Teller allowed"):
        target.importPositionForMigration(
            bob,
            ripe_token,
            ripe_gov_vault,
            _migration_payload(amount),
            sender=alice,
        )
    assert_target_empty()
    with boa.reverts("vault not paused"):
        target.importPositionForMigration(
            bob,
            ripe_token,
            ripe_gov_vault,
            _migration_payload(amount),
            sender=teller.address,
        )
    assert_target_empty()

    target.pause(True, sender=switchboard_alpha.address)
    invalid_sources = (
        (ZERO_ADDRESS, "invalid migration address"),
        (alice, "invalid source vault"),
        (target.address, "invalid source vault"),
    )
    for source, expected_dev in invalid_sources:
        with boa.reverts(dev=expected_dev):
            target.importPositionForMigration(
                bob,
                ripe_token,
                source,
                _migration_payload(amount),
                sender=teller.address,
            )
        assert_target_empty()
    with boa.reverts("invalid migration amount"):
        target.importPositionForMigration(
            bob,
            ripe_token,
            ripe_gov_vault,
            _migration_payload(0),
            sender=teller.address,
        )
    assert_target_empty()
    with boa.reverts("migration funds not received"):
        target.importPositionForMigration(
            bob,
            ripe_token,
            ripe_gov_vault,
            _migration_payload(amount),
            sender=teller.address,
        )
    assert_target_empty()


def test_direct_import_rejects_partially_nonempty_target_position(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
    mission_control,
):
    target, target_id = target_ripe_gov_vault
    _classify_ripe_gov_vault(mission_control, switchboard_alpha, target_id)
    existing = 5 * EIGHTEEN_DECIMALS
    _direct_deposit(target, ripe_token, whale, bob, existing, teller)
    existing_shares = target.userBalances(bob, ripe_token)
    existing_total_shares = target.totalBalances(ripe_token)
    existing_data = target.userGovData(bob, ripe_token)
    target.pause(True, sender=switchboard_alpha.address)
    ripe_token.transfer(target, existing, sender=whale)
    custody_before = ripe_token.balanceOf(target)

    with boa.reverts(dev="target balance exists"):
        target.importPositionForMigration(
            bob,
            ripe_token,
            ripe_gov_vault,
            _migration_payload(existing),
            sender=teller.address,
        )
    assert target.userBalances(bob, ripe_token) == existing_shares
    assert target.totalBalances(ripe_token) == existing_total_shares
    assert target.userGovData(bob, ripe_token) == existing_data
    assert target.totalGovPoints() == 0
    assert ripe_token.balanceOf(target) == custody_before


def test_direct_import_rejects_position_already_migrated_out(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
    mission_control,
):
    target, target_id = target_ripe_gov_vault
    _classify_ripe_gov_vault(mission_control, switchboard_alpha, target_id)
    amount = 5 * EIGHTEEN_DECIMALS
    _direct_deposit(target, ripe_token, whale, bob, amount, teller)
    target.pause(True, sender=switchboard_alpha.address)
    target.exportPositionForMigration(
        bob,
        ripe_token,
        ripe_gov_vault,
        sender=teller.address,
    )
    assert target.positionMigratedOut(bob, ripe_token)
    custody_before = ripe_token.balanceOf(target)

    with boa.reverts(dev="position already migrated out"):
        target.importPositionForMigration(
            bob,
            ripe_token,
            ripe_gov_vault,
            _migration_payload(amount),
            sender=teller.address,
        )
    assert target.positionMigratedOut(bob, ripe_token)
    assert target.userBalances(bob, ripe_token) == 0
    assert target.totalUserGovPoints(bob) == 0
    assert target.totalGovPoints() == 0
    assert ripe_token.balanceOf(target) == custody_before


def test_direct_import_rejects_zero_share_result_atomically(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
):
    target, _ = target_ripe_gov_vault
    migration_amount = 1
    donation = EIGHTEEN_DECIMALS
    target.pause(True, sender=switchboard_alpha.address)
    ripe_token.transfer(target, donation + migration_amount, sender=whale)
    custody_before = ripe_token.balanceOf(target)

    with boa.reverts(dev="invalid target shares"):
        target.importPositionForMigration(
            bob,
            ripe_token,
            ripe_gov_vault,
            _migration_payload(migration_amount),
            sender=teller.address,
        )
    assert target.userBalances(bob, ripe_token) == 0
    assert target.totalBalances(ripe_token) == 0
    assert target.userGovData(bob, ripe_token).govPoints == 0
    assert target.totalUserGovPoints(bob) == 0
    assert target.totalGovPoints() == 0
    assert ripe_token.balanceOf(target) == custody_before


def test_direct_import_trusts_configured_teller_without_source_tombstone_lookup(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
    ledger,
):
    target, target_id = target_ripe_gov_vault
    amount = 25 * EIGHTEEN_DECIMALS
    points = 123
    target.pause(True, sender=switchboard_alpha.address)
    ripe_token.transfer(target, amount, sender=whale)
    assert not ripe_gov_vault.positionMigratedOut(bob, ripe_token)
    ledger_before = ledger.isParticipatingInVault(bob, target_id)

    shares = target.importPositionForMigration(
        bob,
        ripe_token,
        ripe_gov_vault,
        _migration_payload(amount, points),
        sender=teller.address,
    )
    assert shares > 0
    assert target.userBalances(bob, ripe_token) == shares
    assert target.getTotalAmountForUser(bob, ripe_token) == amount
    assert target.totalUserGovPoints(bob) == points
    assert target.totalGovPoints() == points
    assert ledger_before is False
    assert ledger.isParticipatingInVault(bob, target_id) is False


def test_direct_import_reconstructs_position_and_emits_complete_event(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
):
    target, _ = target_ripe_gov_vault
    amount = 25 * EIGHTEEN_DECIMALS
    points = 123
    unlock = 777
    target.pause(True, sender=switchboard_alpha.address)
    ripe_token.transfer(target, amount, sender=whale)
    shares = target.importPositionForMigration(
        bob,
        ripe_token,
        ripe_gov_vault,
        (amount, points, unlock, LOCK_TERMS),
        sender=teller.address,
    )
    logs = filter_logs(target, "RipeGovPositionImported")

    data = target.userGovData(bob, ripe_token)
    assert data.govPoints == points
    assert data.lastShares == shares
    assert data.lastPointsUpdate == boa.env.evm.patch.block_number
    assert data.unlock == unlock
    assert target.totalUserGovPoints(bob) == points
    assert target.totalGovPoints() == points
    assert len(logs) == 1
    event = logs[0]
    assert event.user == bob
    assert event.asset == ripe_token.address
    assert event.sourceVault == ripe_gov_vault.address
    assert event.amount == amount
    assert event.targetShares == shares
    assert event.govPoints == points
    assert event.unlock == unlock


def test_teller_migration_preserves_position_and_updates_ledger_and_deposit_points(
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
    setRipeRewardsConfig,
):
    setRipeRewardsConfig()
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
    assert ledger.getNumUserVaults(bob) == 1
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    migrated, vault_migrator = _migrate_ripe_gov(teller,
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
        return_event=True,
    )
    # Vault export/import events are child logs of the outer VaultMigrator transaction.
    export_logs = filter_logs(vault_migrator, "RipeGovPositionExported")
    import_logs = filter_logs(vault_migrator, "RipeGovPositionImported")
    migration_logs = filter_logs(vault_migrator, "RipeGovPositionMigrationExecuted")
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
    # Source participation is intentionally retained until Lootbox proves every
    # source asset and reward entitlement has been cleaned up.
    assert ledger.isParticipatingInVault(bob, SOURCE_VAULT_ID)
    assert ledger.isParticipatingInVault(bob, target_id)
    assert ledger.getNumUserVaults(bob) == 2

    source_bundle = ledger.getDepositPointsBundle(bob, SOURCE_VAULT_ID, ripe_token)
    target_bundle = ledger.getDepositPointsBundle(bob, target_id, ripe_token)
    assert source_bundle.userPoints.lastUpdate == boa.env.evm.patch.block_number
    assert source_bundle.userPoints.lastBalance == 0
    assert target_bundle.userPoints.lastUpdate == boa.env.evm.patch.block_number
    assert target_bundle.userPoints.lastBalance > 0

    assert len(export_logs) == len(import_logs) == len(migration_logs) == 1
    assert export_logs[0].amount == amount
    assert import_logs[0].govPoints == source_data.govPoints
    assert migration_logs[0].sourceVaultId == SOURCE_VAULT_ID
    assert migration_logs[0].targetVaultId == target_id


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

    _migrate_ripe_gov(teller,
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    )
    assert target.userGovData(bob, ripe_token).govPoints == before.govPoints + pending


def test_exporter_migration_preserves_pre_wind_down_terms_unlock_and_points(
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
    """A temporary one-block min-lock reduction must not become the imported
    position's permanent terms on the exporter-capable path."""
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
    original = ripe_gov_vault.userGovData(bob, ripe_token)
    assert original.unlock > boa.env.evm.patch.block_number
    pending = ripe_gov_vault.getLatestGovPoints(
        original.lastShares,
        original.lastPointsUpdate,
        original.unlock,
        original.lastTerms,
        ASSET_WEIGHT,
    )
    assert pending > 0

    wind_down_terms = (
        original.lastTerms.minLockDuration - 1,
        original.lastTerms.maxLockDuration,
        original.lastTerms.maxLockBoost,
        original.lastTerms.canExit,
        original.lastTerms.exitFee,
    )
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        ASSET_WEIGHT,
        False,
        wind_down_terms,
        sender=switchboard_alpha.address,
    )
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    assert _migrate_ripe_gov(
        teller,
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    ) > 0

    imported = target.userGovData(bob, ripe_token)
    assert imported.govPoints == original.govPoints + pending
    assert imported.unlock == original.unlock
    _assert_lock_terms_equal(imported.lastTerms, original.lastTerms)


def test_existing_target_ledger_entry_is_not_duplicated_during_migration(
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
    ledger.addVaultToUser(bob, target_id, sender=teller.address)
    assert ledger.getNumUserVaults(bob) == 2
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    _migrate_ripe_gov(teller,
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    )
    assert ledger.getNumUserVaults(bob) == 2
    assert ledger.isParticipatingInVault(bob, SOURCE_VAULT_ID)
    assert ledger.isParticipatingInVault(bob, target_id)


def test_migration_at_configured_vault_limit_retains_source_until_cleanup(
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
    max_vaults = mission_control.genConfig().perUserMaxVaults
    assert max_vaults == 5
    sentinel_ids = list(range(100, 100 + max_vaults - 1))
    for sentinel_id in sentinel_ids:
        ledger.addVaultToUser(bob, sentinel_id, sender=teller.address)
    assert ledger.getNumUserVaults(bob) == max_vaults
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    assert _migrate_ripe_gov(
        teller,
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    ) > 0

    # VaultMigrator must not forfeit unsettled source rewards merely to stay
    # under the ordinary deposit limit. Lootbox owns terminal source cleanup.
    assert ledger.getNumUserVaults(bob) == max_vaults + 1
    assert ledger.isParticipatingInVault(bob, SOURCE_VAULT_ID)
    assert ledger.isParticipatingInVault(bob, target_id)
    for sentinel_id in sentinel_ids:
        assert ledger.isParticipatingInVault(bob, sentinel_id)


def test_repeated_migration_is_a_noop_for_completed_position(
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
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)
    assert _migrate_ripe_gov(
        teller,
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    ) == amount

    assert _migrate_ripe_gov(
        teller,
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    ) == 0

    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert target.getTotalAmountForUser(bob, ripe_token) == amount
    assert ripe_gov_vault.positionMigratedOut(bob, ripe_token)
    assert ledger.getNumUserVaults(bob) == 2
    assert ledger.isParticipatingInVault(bob, SOURCE_VAULT_ID)
    assert ledger.isParticipatingInVault(bob, target_id)


def test_migration_accepts_exact_stale_zero_target_asset_registration(
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

    # Model the exact stale-zero state permitted by the import path: one
    # coherent internal registration with no balance, shares, or gov data.
    target.eval(
        f"vaultData.userAssets[{bob}][1] = {ripe_token.address}"
    )
    target.eval(
        f"vaultData.indexOfUserAsset[{bob}][{ripe_token.address}] = 1"
    )
    target.eval(f"vaultData.numUserAssets[{bob}] = 2")
    assert target.indexOfUserAsset(bob, ripe_token) == 1
    assert target.userAssets(bob, 1) == ripe_token.address
    assert target.numUserAssets(bob) == 2
    assert target.userBalances(bob, ripe_token) == 0
    assert target.userGovData(bob, ripe_token).govPoints == 0
    assert not ledger.isParticipatingInVault(bob, target_id)

    _pause_pair(ripe_gov_vault, target, switchboard_alpha)
    assert _migrate_ripe_gov(teller,
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    ) == amount

    assert target.indexOfUserAsset(bob, ripe_token) == 1
    assert target.userAssets(bob, 1) == ripe_token.address
    assert target.numUserAssets(bob) == 2
    assert target.getTotalAmountForUser(bob, ripe_token) == amount
    assert target.userGovData(bob, ripe_token).govPoints == source_data.govPoints
    assert ledger.getNumUserVaults(bob) == 2
    assert ledger.isParticipatingInVault(bob, SOURCE_VAULT_ID)
    assert ledger.isParticipatingInVault(bob, target_id)


@pytest.mark.parametrize("disable_globally", [False, True])
def test_migration_does_not_carry_source_point_disable_policy(
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
        disabled_block = ripe_gov_vault.govPointAccrualDisabledBlock()
    else:
        ripe_gov_vault.disableGovPointAccrualForUser(bob, sender=switchboard_echo.address)
        disabled_block = ripe_gov_vault.userGovPointAccrualDisabledBlock(bob)
    assert disabled_block != 0
    frozen_points = source_data.govPoints
    boa.env.time_travel(blocks=100)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    _migrate_ripe_gov(teller,
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    )
    assert target.userGovData(bob, ripe_token).govPoints == frozen_points
    assert target.totalUserGovPoints(bob) == frozen_points
    assert target.govPointAccrualDisabledBlock() == 0
    assert target.userGovPointAccrualDisabledBlock(bob) == 0

    target.pause(False, sender=switchboard_alpha.address)
    target_before = target.userGovData(bob, ripe_token)
    boa.env.time_travel(blocks=100)
    target.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    target_after = target.userGovData(bob, ripe_token)
    assert target_after.govPoints > target_before.govPoints
    assert target_after.lastPointsUpdate == boa.env.evm.patch.block_number


def test_teller_migration_validates_authority_users_and_route_ids(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    bob,
    teller,
    switchboard_echo,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    target, target_id = target_ripe_gov_vault
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID, target_id],
    )
    with boa.reverts("only switchboard allowed"):
        _migrate_ripe_gov(teller, bob, ripe_token, SOURCE_VAULT_ID, target_id, sender=bob)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)
    assert _migrate_ripe_gov(teller,
        ZERO_ADDRESS,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    ) == 0
    with boa.reverts("invalid vault id"):
        _migrate_ripe_gov(teller, bob, ripe_token, 0, target_id, sender=switchboard_echo.address)
    with boa.reverts("same vault"):
        _migrate_ripe_gov(teller,
            bob,
            ripe_token,
            SOURCE_VAULT_ID,
            SOURCE_VAULT_ID,
            sender=switchboard_echo.address,
        )
    with boa.reverts("invalid source vault id"):
        _migrate_ripe_gov(teller, bob, ripe_token, 999, target_id, sender=switchboard_echo.address)
    with boa.reverts("invalid target vault id"):
        _migrate_ripe_gov(teller, bob, ripe_token, SOURCE_VAULT_ID, 999, sender=switchboard_echo.address)


def test_teller_migration_requires_teller_and_both_vaults_paused(
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
    teller.pause(False, sender=switchboard_alpha.address)
    with boa.reverts("teller not paused"):
        _migrate_ripe_gov(
            teller,
            bob,
            ripe_token,
            SOURCE_VAULT_ID,
            target_id,
            sender=switchboard_echo.address,
        )
    teller.pause(True, sender=switchboard_alpha.address)

    with boa.reverts("source vault not paused"):
        _migrate_ripe_gov(teller,
            bob,
            ripe_token,
            SOURCE_VAULT_ID,
            target_id,
            sender=switchboard_echo.address,
        )

    ripe_gov_vault.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("target vault not paused"):
        _migrate_ripe_gov(teller,
            bob,
            ripe_token,
            SOURCE_VAULT_ID,
            target_id,
            sender=switchboard_echo.address,
        )

    target.pause(True, sender=switchboard_alpha.address)
    assert _migrate_ripe_gov(teller,
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    ) == amount


def test_unsupported_target_asset_is_skipped_without_mutating_source(
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

    assert _migrate_ripe_gov(teller,
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    ) == 0
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == amount
    assert not ripe_gov_vault.positionMigratedOut(bob, ripe_token)
    assert target.getTotalAmountForUser(bob, ripe_token) == 0


def test_migrate_ripe_gov_position_uses_live_source_position_when_config_deprecated(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    ledger,
    lootbox,
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
    setAssetConfig(ripe_token, _vaultIds=[target_id])
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)
    assert _migrate_ripe_gov(teller,
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    ) == amount
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert ripe_gov_vault.positionMigratedOut(bob, ripe_token)
    assert target.getTotalAmountForUser(bob, ripe_token) == amount
    assert ledger.isParticipatingInVault(bob, SOURCE_VAULT_ID)
    assert ledger.isParticipatingInVault(bob, target_id)


def test_migrate_ripe_gov_position_emits_complete_event(
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
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)
    _, vault_migrator = _migrate_ripe_gov(teller,
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
        return_event=True,
    )

    logs = filter_logs(vault_migrator, "RipeGovPositionMigrationExecuted")
    assert len(logs) == 1
    event = logs[0]
    assert event.user == bob
    assert event.asset == ripe_token.address
    assert event.sourceVaultId == SOURCE_VAULT_ID
    assert event.targetVaultId == target_id
    assert event.sourceVault == ripe_gov_vault.address
    assert event.targetVault == target.address
    assert event.amount == amount
    assert event.targetShares == target.userBalances(bob, ripe_token)
    assert event.govPoints == source_data.govPoints
    assert event.unlock == source_data.unlock


def test_existing_target_position_makes_entire_migration_atomic(
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
):
    target, target_id = target_ripe_gov_vault
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID, target_id],
    )
    _classify_ripe_gov_vault(mission_control, switchboard_alpha, target_id)
    source_amount = 30 * EIGHTEEN_DECIMALS
    target_amount = 5 * EIGHTEEN_DECIMALS
    _direct_deposit(ripe_gov_vault, ripe_token, whale, bob, source_amount, teller)
    _direct_deposit(target, ripe_token, whale, bob, target_amount, teller)
    ledger.addVaultToUser(bob, SOURCE_VAULT_ID, sender=teller.address)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    with boa.reverts("target balance exists"):
        _migrate_ripe_gov(teller,
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
    ledger,
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
    ledger.addVaultToUser(bob, SOURCE_VAULT_ID, sender=teller.address)
    fee_token.setTransferFee(500, sender=governance.address)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    with boa.reverts("inexact migration receipt"):
        _migrate_ripe_gov(teller,
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
    _migrate_ripe_gov(teller,
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
            sender=teller.address,
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


def test_only_historical_core_ripe_gov_vault_can_be_the_migration_source(
    ripe_hq,
    vault_book,
    governance,
    boardroom,
    ripe_token,
    whale,
    bob,
    teller,
    ledger,
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

    # Seed the deliberately non-core source without weakening the production
    # Boardroom gate. The permissive callback exists only while constructing the
    # fixture; the canonical Boardroom is restored before the migration check.
    permissive_boardroom = boa.loads(
        """
# pragma version 0.4.3

@external
def govPowerDidChangeForUser(
    _user: address,
    _userGovPoints: uint256,
    _totalGovPoints: uint256,
):
    pass
""",
        name="permissive_boardroom_for_non_core_source_setup",
    )
    _replace_hq_address(ripe_hq, governance, 11, permissive_boardroom)
    amount = 25 * EIGHTEEN_DECIMALS
    _direct_deposit(source, ripe_token, whale, bob, amount, teller)
    ledger.addVaultToUser(bob, source_id, sender=teller.address)
    _save_points(source, bob, ripe_token, switchboard_alpha)
    _replace_hq_address(ripe_hq, governance, 11, boardroom)
    _pause_pair(source, target, switchboard_alpha)

    # RipeGov bytecode alone is not authority to use the privileged exporter
    # route. The source must first have been recorded as a core governance vault.
    with boa.reverts("source is not ripe gov"):
        _migrate_ripe_gov(
            teller,
            bob,
            ripe_token,
            source_id,
            target_id,
            sender=switchboard_echo.address,
        )

    mission_control.setCoreRipeGovVaultId(source_id, sender=switchboard_alpha.address)
    assert mission_control.isRipeGovVaultId(source_id)

    assert _migrate_ripe_gov(teller,
        bob,
        ripe_token,
        source_id,
        target_id,
        sender=switchboard_echo.address,
    ) == amount
    assert source.positionMigratedOut(bob, ripe_token)
    assert target.getTotalAmountForUser(bob, ripe_token) == amount
    assert ledger.isParticipatingInVault(bob, source_id)
    assert ledger.isParticipatingInVault(bob, target_id)


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
    ledger.addVaultToUser(contributor, SOURCE_VAULT_ID, sender=teller.address)
    source_data = _save_points(
        ripe_gov_vault,
        contributor,
        ripe_token,
        switchboard_alpha,
    )
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    _migrate_ripe_gov(teller,
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


def test_echo_disable_validator_reverts_for_wrong_vault_interface(
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
    with boa.reverts():
        switchboard_echo.isValidRipeGovPointAccrualDisable(simple_vault_id, bob)
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


def test_disable_rejects_invalid_disable_type_without_state_change(
    switchboard_echo,
    governance,
    bob,
):
    next_action = switchboard_echo.actionId()
    with boa.reverts("invalid disable"):
        switchboard_echo.disableRipeGovPointAccrualGlobally(
            0,
            sender=governance.address,
        )
    with boa.reverts("invalid disable"):
        switchboard_echo.disableRipeGovPointAccrualForUser(
            999,
            bob,
            sender=governance.address,
        )
    assert switchboard_echo.actionId() == next_action
    assert switchboard_echo.actionType(next_action) == 0
    pending = switchboard_echo.pendingRipeGovPointAccrualDisableActions(next_action)
    assert pending.vaultId == 0
    assert pending.vaultAddr == ZERO_ADDRESS
    assert pending.user == ZERO_ADDRESS


def test_disable_rejects_when_vault_binding_changed_before_execution(
    switchboard_echo,
    ripe_gov_vault,
    vault_book,
    governance,
    bob,
):
    action_id = switchboard_echo.disableRipeGovPointAccrualForUser(
        SOURCE_VAULT_ID,
        bob,
        sender=governance.address,
    )
    pending_before = switchboard_echo.pendingRipeGovPointAccrualDisableActions(action_id)
    assert pending_before.vaultAddr == ripe_gov_vault.address

    replacement = boa.load(
        "contracts/vaults/RipeGov.vy",
        ripe_gov_vault.getRipeHq(),
        name="echo_rebound_ripe_gov_vault",
    )
    assert vault_book.startAddressUpdateToRegistry(
        SOURCE_VAULT_ID,
        replacement,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    assert vault_book.confirmAddressUpdateToRegistry(
        SOURCE_VAULT_ID,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())

    with boa.reverts(dev="vault binding changed"):
        switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert switchboard_echo.hasPendingAction(action_id)
    assert switchboard_echo.pendingRipeGovPointAccrualDisableActions(action_id) == pending_before
    assert ripe_gov_vault.userGovPointAccrualDisabledBlock(bob) == 0


def test_disable_rejects_already_disabled_target(
    switchboard_echo,
    ripe_gov_vault,
    governance,
    bob,
):
    action_id = switchboard_echo.disableRipeGovPointAccrualForUser(
        SOURCE_VAULT_ID,
        bob,
        sender=governance.address,
    )
    ripe_gov_vault.disableGovPointAccrualForUser(
        bob,
        sender=switchboard_echo.address,
    )
    disabled_block = ripe_gov_vault.userGovPointAccrualDisabledBlock(bob)
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())

    with boa.reverts("invalid disable"):
        switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert switchboard_echo.hasPendingAction(action_id)
    assert ripe_gov_vault.userGovPointAccrualDisabledBlock(bob) == disabled_block


def test_global_and_user_disable_states_compose_without_reenabling(
    switchboard_echo,
    ripe_gov_vault,
    governance,
    bob,
):
    user_action = switchboard_echo.disableRipeGovPointAccrualForUser(
        SOURCE_VAULT_ID,
        bob,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())
    assert switchboard_echo.executePendingAction(user_action, sender=governance.address)
    user_disabled_block = ripe_gov_vault.userGovPointAccrualDisabledBlock(bob)

    global_action = switchboard_echo.disableRipeGovPointAccrualGlobally(
        SOURCE_VAULT_ID,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())
    assert switchboard_echo.executePendingAction(global_action, sender=governance.address)

    assert user_disabled_block != 0
    assert ripe_gov_vault.userGovPointAccrualDisabledBlock(bob) == user_disabled_block
    assert ripe_gov_vault.govPointAccrualDisabledBlock() > user_disabled_block
    assert switchboard_echo.isValidRipeGovPointAccrualDisable(SOURCE_VAULT_ID, bob) is False


def test_disable_event_contains_complete_target_reason_and_scope(
    switchboard_echo,
    ripe_gov_vault,
    governance,
    bob,
):
    action_id = switchboard_echo.disableRipeGovPointAccrualForUser(
        SOURCE_VAULT_ID,
        bob,
        sender=governance.address,
    )
    pending_logs = filter_logs(switchboard_echo, "PendingRipeGovPointAccrualUserDisable")
    assert len(pending_logs) == 1
    confirmation_block = switchboard_echo.getActionConfirmationBlock(action_id)
    pending = pending_logs[0]
    assert pending.vaultId == SOURCE_VAULT_ID
    assert pending.vaultAddr == ripe_gov_vault.address
    assert pending.user == bob
    assert pending.confirmationBlock == confirmation_block
    assert pending.actionId == action_id

    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())
    assert switchboard_echo.executePendingAction(action_id, sender=governance.address)
    executed_logs = filter_logs(switchboard_echo, "RipeGovPointAccrualUserDisableExecuted")
    assert len(executed_logs) == 1
    executed = executed_logs[0]
    assert executed.vaultId == SOURCE_VAULT_ID
    assert executed.vaultAddr == ripe_gov_vault.address
    assert executed.user == bob


def test_echo_batch_migrates_many_users_and_emits_one_event_each(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    ledger,
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
        ledger.addVaultToUser(user, SOURCE_VAULT_ID, sender=teller.address)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)
    mission_control.setCoreRipeGovVaultId(target_id, sender=switchboard_alpha.address)

    assert switchboard_echo.migrateRipeGovPositions(
        list(amounts), SOURCE_VAULT_ID,
        sender=governance.address,
    ) == 2
    for user, amount in amounts.items():
        assert ripe_gov_vault.getTotalAmountForUser(user, ripe_token) == 0
        assert target.getTotalAmountForUser(user, ripe_token) == amount
    logs = filter_logs(switchboard_echo, "RipeGovPositionMigrationExecuted")
    assert len(logs) == 2
    assert {log.user for log in logs} == set(amounts)


def test_one_user_migrates_all_governance_assets_with_one_housekeeping_call(
    target_ripe_gov_vault,
    ripe_gov_vault,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    teller,
    governance,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
    setGeneralConfig,
):
    target, target_id = target_ripe_gov_vault
    setGeneralConfig()
    for asset in (alpha_token, bravo_token):
        _configure_ripe_gov_asset(
            mission_control,
            setAssetConfig,
            switchboard_alpha,
            asset,
            [SOURCE_VAULT_ID, target_id],
        )
    positions = (
        (alpha_token, alpha_token_whale, 20 * EIGHTEEN_DECIMALS),
        (bravo_token, bravo_token_whale, 30 * EIGHTEEN_DECIMALS),
    )
    for asset, funder, amount in positions:
        _deposit_through_teller(
            teller, ripe_gov_vault, asset, funder, bob, amount, 0
        )

    mission_control.setShouldCheckLastTouch(True, sender=switchboard_alpha.address)
    boa.env.time_travel(blocks=1)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)
    mission_control.setCoreRipeGovVaultId(target_id, sender=switchboard_alpha.address)

    assert switchboard_echo.migrateRipeGovPositions(
        [bob], SOURCE_VAULT_ID, sender=governance.address
    ) == 2
    for asset, _, amount in positions:
        assert ripe_gov_vault.getTotalAmountForUser(bob, asset) == 0
        assert target.getTotalAmountForUser(bob, asset) == amount
    logs = filter_logs(switchboard_echo, "RipeGovPositionMigrationExecuted")
    assert len(logs) == 2
    assert {log.asset for log in logs} == {alpha_token.address, bravo_token.address}


def test_governance_migration_rejects_more_than_five_source_asset_slots(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
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
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)
    ripe_gov_vault.eval(f"vaultData.numUserAssets[{bob}] = 6")
    assert _migrate_ripe_gov(
        teller,
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    ) == 0

    ripe_gov_vault.eval(f"vaultData.numUserAssets[{bob}] = 7")
    with pytest.raises(BoaError):
        _migrate_ripe_gov(
            teller,
            bob,
            ripe_token,
            SOURCE_VAULT_ID,
            target_id,
            sender=switchboard_echo.address,
        )


def test_echo_batch_is_governance_only_nonempty_and_skips_empty_users(
    target_ripe_gov_vault,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    ledger,
    governance,
    switchboard_alpha,
    switchboard_echo,
    mission_control,
    setAssetConfig,
):
    target, target_id = target_ripe_gov_vault
    with boa.reverts("no perms"):
        switchboard_echo.migrateRipeGovPositions([], SOURCE_VAULT_ID, sender=bob)
    with boa.reverts("no migrations"):
        switchboard_echo.migrateRipeGovPositions(
            [], SOURCE_VAULT_ID, sender=governance.address
        )

    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID, target_id],
    )
    amount = 40 * EIGHTEEN_DECIMALS
    _direct_deposit(ripe_gov_vault, ripe_token, whale, bob, amount, teller)
    ledger.addVaultToUser(bob, SOURCE_VAULT_ID, sender=teller.address)
    ledger.addVaultToUser(alice, SOURCE_VAULT_ID, sender=teller.address)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)
    mission_control.setCoreRipeGovVaultId(target_id, sender=switchboard_alpha.address)

    # Alice has no live source assets, so she is skipped after Bob migrates.
    assert switchboard_echo.migrateRipeGovPositions(
        [bob, alice], SOURCE_VAULT_ID, sender=governance.address
    ) == 1
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert target.getTotalAmountForUser(bob, ripe_token) == amount
    assert ripe_gov_vault.positionMigratedOut(bob, ripe_token)


############################################################################
# WP1 (Section 8.1/8.2/9.4): RipeGov privileged-caller, lock, and pause matrix
#
# Written against the bound RH baseline before any owner disposition of
# RH-CHANGE-01, GOV-WEIGHT-01, or RG-SIZE-01. Each finding gets a plain
# PASSING characterization of the exact behavior that exists today plus a
# strict-xfail HARDENING test stating the invariant the plan wants.
#
# Every caller, action, and boundary is an INDEPENDENT parametrized node. A
# loop inside one strict-xfail would stop at its first unexpected success and
# silently leave the rest of the matrix unexecuted, so the matrix would not
# actually be covered. The Section 6.1(B) expected-red table lists these node
# IDs individually.
#
# The strict xfails are preserved test-only checkpoints: remove the xfail (and
# require the plain test to pass) if the owner approves the corresponding
# production change, or delete it in favour of the characterization alone if
# the owner records an accepted residual risk.
############################################################################


# Registered RIPE addresses that are NOT Teller. Work Package 0 found Teller to
# be the only production caller of depositTokensWithLockDuration / adjustLock /
# releaseLock (contracts/core/Teller.vy:338, :826, :843). Every entry below is
# accepted today purely because addys._isValidRipeAddr returns True for it.
REGISTERED_NON_TELLER_CALLERS = (
    "auction_house",
    "credit_engine",
    "human_resources",
    "lootbox",
    "bond_room",
    "switchboard_alpha",
    "switchboard_bravo",
    "switchboard_charlie",
    "switchboard_delta",
    "switchboard_echo",
    "stability_pool",
    "other_vault_simple",
    "other_vault_rebase",
)

UNREGISTERED_CALLERS = ("alice", "sally", "mock_rando_contract")


def _gov_state_snapshot(vault, ripe_token, users):
    """Complete observable RipeGov state for the users under test.

    Covers every field Section 8.1 requires to be unchanged for a rejected
    caller: token custody, user and total shares, lastShares, lock duration and
    unlock time, user and global points, fee balances (the vault's own share
    balance, which releaseLock burns into), and timestamps/checkpoints.
    """
    state = {
        "vault_custody": ripe_token.balanceOf(vault.address),
        "total_shares": vault.totalBalances(ripe_token),
        "total_gov_points": vault.totalGovPoints(),
        "num_vault_assets": vault.numAssets(),
        "gov_disabled_block": vault.govPointAccrualDisabledBlock(),
    }
    for user in users:
        data = vault.userGovData(user, ripe_token)
        state[user] = (
            vault.userBalances(user, ripe_token),
            vault.getTotalAmountForUser(user, ripe_token),
            data.govPoints,
            data.lastShares,
            data.lastPointsUpdate,
            data.unlock,
            tuple(data.lastTerms),
            vault.totalUserGovPoints(user),
            vault.numUserAssets(user),
            vault.indexOfUserAsset(user, ripe_token),
            vault.positionMigratedOut(user, ripe_token),
            vault.getUserLootBoxShare(user, ripe_token),
            ripe_token.balanceOf(user),
        )
    return state


@pytest.fixture
def registered_non_teller_callers(
    auction_house,
    credit_engine,
    human_resources,
    lootbox,
    bond_room,
    switchboard_alpha,
    switchboard_bravo,
    switchboard_charlie,
    switchboard_delta,
    switchboard_echo,
    stability_pool,
    simple_erc20_vault,
    rebase_erc20_vault,
):
    return {
        "auction_house": auction_house,
        "credit_engine": credit_engine,
        "human_resources": human_resources,
        "lootbox": lootbox,
        "bond_room": bond_room,
        "switchboard_alpha": switchboard_alpha,
        "switchboard_bravo": switchboard_bravo,
        "switchboard_charlie": switchboard_charlie,
        "switchboard_delta": switchboard_delta,
        "switchboard_echo": switchboard_echo,
        "stability_pool": stability_pool,
        "other_vault_simple": simple_erc20_vault,
        "other_vault_rebase": rebase_erc20_vault,
    }


@pytest.fixture
def unregistered_callers(alice, sally, mock_rando_contract):
    return {
        "alice": alice,
        "sally": sally,
        "mock_rando_contract": mock_rando_contract.address,
    }


@pytest.fixture
def gov_position(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    """Bob holds a 100 RIPE unlocked RipeGov position; returns the amount."""
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
    )
    amount = 100 * EIGHTEEN_DECIMALS
    _direct_deposit(ripe_gov_vault, ripe_token, whale, bob, amount, teller)
    return amount


@pytest.fixture
def locked_gov_position(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_bravo,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    """Bob holds a 100 RIPE position locked for 1,000 blocks."""
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
        lock_duration=1_000,
        switchboard=switchboard_bravo,
    )
    return amount


# --------------------------------------------------------------------------
# DV-01/02/03 negative half -- already correct on the bound baseline
# --------------------------------------------------------------------------


@pytest.mark.parametrize("caller_name", UNREGISTERED_CALLERS)
@pytest.mark.parametrize(
    "method", ("depositTokensWithLockDuration", "adjustLock", "releaseLock", "updateUserGovPoints")
)
def test_unregistered_gov_privileged_call_is_rejected_and_fully_atomic(
    caller_name,
    method,
    ripe_gov_vault,
    ripe_token,
    bob,
    alice,
    unregistered_callers,
    gov_position,
):
    """Section 8.1: nothing moves for a rejected caller. Passes on the baseline."""
    boa.env.time_travel(blocks=10)
    caller = unregistered_callers[caller_name]
    before = _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob, alice])

    expected = (
        "no perms" if method == "updateUserGovPoints" else "only Teller allowed"
    )
    with boa.reverts(expected):
        if method == "depositTokensWithLockDuration":
            ripe_gov_vault.depositTokensWithLockDuration(
                alice, ripe_token, gov_position, 1_000, sender=caller
            )
        elif method == "adjustLock":
            ripe_gov_vault.adjustLock(bob, ripe_token, 1_000, sender=caller)
        elif method == "releaseLock":
            ripe_gov_vault.releaseLock(bob, ripe_token, sender=caller)
        else:
            ripe_gov_vault.updateUserGovPoints(bob, sender=caller)

    assert _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob, alice]) == before


# --------------------------------------------------------------------------
# DV-01: registered non-Teller can mint governance shares from existing custody
# --------------------------------------------------------------------------




@pytest.mark.parametrize("caller_name", REGISTERED_NON_TELLER_CALLERS)
def test_registered_non_teller_cannot_mint_gov_shares_from_existing_custody(
    caller_name,
    ripe_gov_vault,
    ripe_token,
    bob,
    alice,
    registered_non_teller_callers,
    gov_position,
):
    """DV-01 hardening target (SV-1, SV-4). One node per registered caller."""
    caller = registered_non_teller_callers[caller_name]
    before = _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob, alice])

    with boa.reverts():
        ripe_gov_vault.depositTokensWithLockDuration(
            alice, ripe_token, MAX_UINT256, 1_000, sender=caller.address
        )
    assert _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob, alice]) == before


# --------------------------------------------------------------------------
# DV-02: registered non-Teller can adjust another user's lock
# --------------------------------------------------------------------------




@pytest.mark.parametrize("caller_name", REGISTERED_NON_TELLER_CALLERS)
def test_registered_non_teller_cannot_adjust_another_users_lock(
    caller_name,
    ripe_gov_vault,
    ripe_token,
    bob,
    registered_non_teller_callers,
    gov_position,
):
    """DV-02 hardening target (SV-4, RG-4). One node per registered caller."""
    caller = registered_non_teller_callers[caller_name]
    before = _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob])

    with boa.reverts():
        ripe_gov_vault.adjustLock(bob, ripe_token, 1_000, sender=caller.address)
    assert _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob]) == before


# --------------------------------------------------------------------------
# DV-03: registered non-Teller can release another user's lock and burn the fee
# --------------------------------------------------------------------------




@pytest.mark.parametrize("caller_name", REGISTERED_NON_TELLER_CALLERS)
def test_registered_non_teller_cannot_release_another_users_lock(
    caller_name,
    ripe_gov_vault,
    ripe_token,
    bob,
    registered_non_teller_callers,
    locked_gov_position,
):
    """DV-03 hardening target (SV-4, RG-4). One node per registered caller."""
    caller = registered_non_teller_callers[caller_name]
    before = _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob])

    with boa.reverts():
        ripe_gov_vault.releaseLock(bob, ripe_token, sender=caller.address)
    assert _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob]) == before


def test_gov_transfer_to_a_different_user_still_moves_shares(
    ripe_gov_vault,
    ripe_token,
    bob,
    alice,
    auction_house,
    locked_gov_position,
):
    """A valid different-user AuctionHouse seizure still moves shares."""
    bob_shares_before = ripe_gov_vault.userBalances(bob, ripe_token)
    assert ripe_gov_vault.userBalances(alice, ripe_token) == 0

    ripe_gov_vault.transferBalanceWithinVault(
        ripe_token, bob, alice, locked_gov_position // 2, sender=auction_house.address
    )

    assert ripe_gov_vault.userBalances(alice, ripe_token) > 0
    assert ripe_gov_vault.userBalances(bob, ripe_token) < bob_shares_before


# --------------------------------------------------------------------------
# Contributor transfers retain their separately governed lock term
# --------------------------------------------------------------------------


CONTRIBUTOR_DURATIONS = (
    ("zero", 0),
    ("one", 1),
    ("below_general_min", LOCK_TERMS[0] - 1),
    ("at_min", LOCK_TERMS[0]),
    ("ordinary", (LOCK_TERMS[0] + LOCK_TERMS[1]) // 2),
    ("at_max", LOCK_TERMS[1]),
    ("above_general_max", LOCK_TERMS[1] + 1),
    ("far_above_max", LOCK_TERMS[1] * 10),
)


@pytest.mark.parametrize(
    "duration", [d for _label, d in CONTRIBUTOR_DURATIONS], ids=[l for l, _d in CONTRIBUTOR_DURATIONS]
)
def test_contributor_transfer_honors_configured_duration_on_fresh_recipient(
    duration,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    sally,
    teller,
    human_resources,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    """The contributor's block-based term is distinct from general deposit bounds."""
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
    )
    _direct_deposit(
        ripe_gov_vault, ripe_token, whale, sally, 100 * EIGHTEEN_DECIMALS, teller
    )
    assert ripe_gov_vault.userGovData(bob, ripe_token).unlock == 0

    ripe_gov_vault.transferContributorRipeTokens(
        sally, bob, duration, sender=human_resources.address
    )

    assert ripe_gov_vault.userGovData(bob, ripe_token).unlock == (
        boa.env.evm.patch.block_number + duration
    )


def test_contributor_transfer_uses_configured_duration_in_weighted_recipient_lock(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    sally,
    teller,
    human_resources,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
    switchboard_bravo,
):
    """An existing recipient lock is blended, not substituted for the HR term."""
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
    )

    max_lock = LOCK_TERMS[1]
    contributor_duration = 1
    _direct_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        bob,
        10 * EIGHTEEN_DECIMALS,
        teller,
        lock_duration=max_lock,
        switchboard=switchboard_bravo,
    )
    _direct_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        sally,
        1_000 * EIGHTEEN_DECIMALS,
        teller,
    )

    recipient_shares = ripe_gov_vault.userBalances(bob, ripe_token)
    contributor_shares = ripe_gov_vault.userBalances(sally, ripe_token)
    unlock_before = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    expected_unlock = ripe_gov_vault.getWeightedLockOnTokenDeposit(
        contributor_shares,
        contributor_duration,
        LOCK_TERMS,
        recipient_shares,
        unlock_before,
    )

    ripe_gov_vault.transferContributorRipeTokens(
        sally, bob, contributor_duration, sender=human_resources.address
    )
    unlock_after = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    assert unlock_after == expected_unlock
    assert unlock_after < unlock_before
    assert ripe_gov_vault.userBalances(sally, ripe_token) == 0


# --------------------------------------------------------------------------
# DV-06 / Section 9.4: pause matrix over every public RipeGov mutation
# --------------------------------------------------------------------------

# (method name, blocked-while-paused on the bound baseline)
GOV_PAUSE_MATRIX = (
    ("depositTokensInVault", True),
    ("depositTokensWithLockDuration", True),
    ("withdrawTokensFromVault", True),
    ("withdrawContributorTokensToBurn", True),
    ("transferBalanceWithinVault", True),
    ("transferContributorRipeTokens", True),
    ("updateUserGovPoints", True),
    ("adjustLock", True),
    ("releaseLock", True),
    ("disableGovPointAccrualForUser", False),
    ("disableGovPointAccrualGlobally", False),
)


def _invoke_gov_mutation(
    method, vault, ripe_token, whale, bob, alice, teller, auction_house,
    human_resources, switchboard_alpha, switchboard_bravo, amount,
):
    """Invoke one public state-changing RipeGov method with valid arguments."""
    if method == "depositTokensInVault":
        ripe_token.transfer(vault, EIGHTEEN_DECIMALS, sender=whale)
        vault.depositTokensInVault(bob, ripe_token, EIGHTEEN_DECIMALS, sender=teller.address)
    elif method == "depositTokensWithLockDuration":
        ripe_token.transfer(vault, EIGHTEEN_DECIMALS, sender=whale)
        vault.depositTokensWithLockDuration(
            bob, ripe_token, EIGHTEEN_DECIMALS, 500, sender=teller.address
        )
    elif method == "withdrawTokensFromVault":
        vault.withdrawTokensFromVault(bob, ripe_token, amount, bob, sender=teller.address)
    elif method == "withdrawContributorTokensToBurn":
        vault.withdrawContributorTokensToBurn(bob, sender=human_resources.address)
    elif method == "transferBalanceWithinVault":
        vault.transferBalanceWithinVault(
            ripe_token, bob, alice, amount // 4, sender=auction_house.address
        )
    elif method == "transferContributorRipeTokens":
        vault.transferContributorRipeTokens(bob, alice, 500, sender=human_resources.address)
    elif method == "updateUserGovPoints":
        vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    elif method == "adjustLock":
        vault.adjustLock(bob, ripe_token, 1_000, sender=teller.address)
    elif method == "releaseLock":
        vault.releaseLock(bob, ripe_token, sender=teller.address)
    elif method == "disableGovPointAccrualForUser":
        vault.disableGovPointAccrualForUser(bob, sender=switchboard_alpha.address)
    elif method == "disableGovPointAccrualGlobally":
        vault.disableGovPointAccrualGlobally(sender=switchboard_alpha.address)
    else:  # pragma: no cover - guards against a typo in the matrix
        raise AssertionError(f"unhandled method {method}")


def _reverted_with_pause(exc):
    return any(
        not isinstance(frame, str)
        and getattr(frame, "dev_reason", None) is not None
        and frame.dev_reason.reason_str == "contract paused"
        for frame in exc.stack_trace
    )


@pytest.mark.parametrize(
    ("method", "blocked_while_paused"),
    GOV_PAUSE_MATRIX,
    ids=[m for m, _b in GOV_PAUSE_MATRIX],
)
def test_ripe_gov_pause_matrix_while_paused(
    method,
    blocked_while_paused,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    auction_house,
    human_resources,
    switchboard_alpha,
    switchboard_bravo,
    locked_gov_position,
):
    """DV-06 characterization (SV-5, Section 9.4): exact pause policy per method.

    The owner-approved policy also pause-gates updateUserGovPoints, adjustLock,
    and releaseLock. The two point-disable escape setters remain available while
    paused; migration import/export and overflow-disable routes are separate.
    """
    boa.env.time_travel(blocks=10)
    ripe_gov_vault.pause(True, sender=switchboard_alpha.address)
    assert ripe_gov_vault.isPaused()

    if blocked_while_paused:
        with boa.reverts("contract paused"):
            _invoke_gov_mutation(
                method, ripe_gov_vault, ripe_token, whale, bob, alice, teller,
                auction_house, human_resources, switchboard_alpha,
                switchboard_bravo, locked_gov_position,
            )
    else:
        _invoke_gov_mutation(
            method, ripe_gov_vault, ripe_token, whale, bob, alice, teller,
            auction_house, human_resources, switchboard_alpha,
            switchboard_bravo, locked_gov_position,
        )


@pytest.mark.parametrize(
    ("method", "blocked_while_paused"),
    GOV_PAUSE_MATRIX,
    ids=[m for m, _b in GOV_PAUSE_MATRIX],
)
def test_ripe_gov_pause_matrix_while_unpaused(
    method,
    blocked_while_paused,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    teller,
    auction_house,
    human_resources,
    switchboard_alpha,
    switchboard_bravo,
    locked_gov_position,
):
    """Section 9.4 control half: no method is pause-blocked while unpaused."""
    if method == "releaseLock":
        _direct_deposit(
            ripe_gov_vault,
            ripe_token,
            whale,
            alice,
            EIGHTEEN_DECIMALS,
            teller,
        )
    boa.env.time_travel(blocks=10)
    assert not ripe_gov_vault.isPaused()
    try:
        _invoke_gov_mutation(
            method, ripe_gov_vault, ripe_token, whale, bob, alice, teller,
            auction_house, human_resources, switchboard_alpha,
            switchboard_bravo, locked_gov_position,
        )
    except BoaError as exc:
        # A method may still revert for an unrelated reason (for example a
        # locked withdrawal); it must never revert because of the pause flag.
        assert not _reverted_with_pause(exc), method
    if method == "releaseLock":
        assert ripe_gov_vault.userGovData(bob, ripe_token).unlock == 0


@pytest.mark.parametrize("method", ("adjustLock", "releaseLock"))
def test_gov_lock_mutation_reverts_while_vault_is_paused(
    method,
    ripe_gov_vault,
    ripe_token,
    bob,
    teller,
    switchboard_alpha,
    locked_gov_position,
):
    """DV-06 regression for the owner-approved Section 9.4 pause rule."""
    boa.env.time_travel(blocks=10)
    ripe_gov_vault.pause(True, sender=switchboard_alpha.address)
    before = _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob])

    with boa.reverts("contract paused"):
        if method == "adjustLock":
            ripe_gov_vault.adjustLock(bob, ripe_token, 1_000, sender=teller.address)
        else:
            ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

    assert _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob]) == before
