import pytest
import boa
from boa.contracts.base_evm_contract import BoaError

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS
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
):
    target, _ = target_ripe_gov_vault
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
):
    target, _ = target_ripe_gov_vault
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
    assert ledger.getNumUserVaults(bob) == 1
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
    assert not ledger.isParticipatingInVault(bob, SOURCE_VAULT_ID)
    assert ledger.isParticipatingInVault(bob, target_id)
    assert ledger.getNumUserVaults(bob) == 1

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


def test_migration_requires_source_ledger_entry_before_export_and_rolls_back(
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
    # migration cleanup now routes through Lootbox, which is the only contract Ledger
    # authorizes to remove a user's vault participation
    lootbox.removeVaultFromUserForMigration(
        bob,
        SOURCE_VAULT_ID,
        sender=teller.address,
    )
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    with boa.reverts("source vault missing from Ledger"):
        teller.migrateRipeGovPosition(
            bob,
            ripe_token,
            SOURCE_VAULT_ID,
            target_id,
            sender=switchboard_echo.address,
        )
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == amount
    assert target.getTotalAmountForUser(bob, ripe_token) == 0
    assert not ripe_gov_vault.positionMigratedOut(bob, ripe_token)


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

    teller.migrateRipeGovPosition(
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    )
    assert ledger.getNumUserVaults(bob) == 1
    assert not ledger.isParticipatingInVault(bob, SOURCE_VAULT_ID)
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
    assert teller.migrateRipeGovPosition(
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
    assert ledger.getNumUserVaults(bob) == 1
    assert not ledger.isParticipatingInVault(bob, SOURCE_VAULT_ID)
    assert ledger.isParticipatingInVault(bob, target_id)


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


def test_migrate_ripe_gov_position_rejects_unsupported_source_asset_atomically(
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
    source_snapshot = (
        ripe_token.balanceOf(ripe_gov_vault),
        ripe_gov_vault.userBalances(bob, ripe_token),
        ripe_gov_vault.userGovData(bob, ripe_token),
        ripe_gov_vault.totalUserGovPoints(bob),
        ripe_gov_vault.totalGovPoints(),
        ripe_gov_vault.positionMigratedOut(bob, ripe_token),
    )
    target_snapshot = (
        ripe_token.balanceOf(target),
        target.userBalances(bob, ripe_token),
        target.userGovData(bob, ripe_token),
        target.totalUserGovPoints(bob),
        target.totalGovPoints(),
    )
    ledger_snapshot = (
        ledger.isParticipatingInVault(bob, SOURCE_VAULT_ID),
        ledger.isParticipatingInVault(bob, target_id),
        ledger.userDepositPoints(bob, SOURCE_VAULT_ID, ripe_token),
        ledger.userDepositPoints(bob, target_id, ripe_token),
        ledger.globalDepositPoints(),
    )
    claimable_before = lootbox.getClaimableLoot(bob)

    with boa.reverts(dev="unsupported source asset"):
        teller.migrateRipeGovPosition(
            bob,
            ripe_token,
            SOURCE_VAULT_ID,
            target_id,
            sender=switchboard_echo.address,
        )
    assert source_snapshot == (
        ripe_token.balanceOf(ripe_gov_vault),
        ripe_gov_vault.userBalances(bob, ripe_token),
        ripe_gov_vault.userGovData(bob, ripe_token),
        ripe_gov_vault.totalUserGovPoints(bob),
        ripe_gov_vault.totalGovPoints(),
        ripe_gov_vault.positionMigratedOut(bob, ripe_token),
    )
    assert target_snapshot == (
        ripe_token.balanceOf(target),
        target.userBalances(bob, ripe_token),
        target.userGovData(bob, ripe_token),
        target.totalUserGovPoints(bob),
        target.totalGovPoints(),
    )
    assert ledger_snapshot == (
        ledger.isParticipatingInVault(bob, SOURCE_VAULT_ID),
        ledger.isParticipatingInVault(bob, target_id),
        ledger.userDepositPoints(bob, SOURCE_VAULT_ID, ripe_token),
        ledger.userDepositPoints(bob, target_id, ripe_token),
        ledger.globalDepositPoints(),
    )
    assert lootbox.getClaimableLoot(bob) == claimable_before
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == amount


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
    teller.migrateRipeGovPosition(
        bob,
        ripe_token,
        SOURCE_VAULT_ID,
        target_id,
        sender=switchboard_echo.address,
    )

    logs = filter_logs(teller, "RipeGovPositionMigrated")
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
    source_amount = 30 * EIGHTEEN_DECIMALS
    target_amount = 5 * EIGHTEEN_DECIMALS
    _direct_deposit(ripe_gov_vault, ripe_token, whale, bob, source_amount, teller)
    _direct_deposit(target, ripe_token, whale, bob, target_amount, teller)
    ledger.addVaultToUser(bob, SOURCE_VAULT_ID, sender=teller.address)
    _pause_pair(ripe_gov_vault, target, switchboard_alpha)

    with boa.reverts("target balance exists"):
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
    amount = 25 * EIGHTEEN_DECIMALS
    _direct_deposit(source, ripe_token, whale, bob, amount, teller)
    ledger.addVaultToUser(bob, source_id, sender=teller.address)
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
    assert not ledger.isParticipatingInVault(bob, source_id)
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
    ledger,
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
    ledger.addVaultToUser(bob, SOURCE_VAULT_ID, sender=teller.address)
    ledger.addVaultToUser(alice, SOURCE_VAULT_ID, sender=teller.address)
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

    with boa.reverts("no perms"):
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


def test_registered_non_teller_mints_gov_shares_from_existing_custody(
    ripe_gov_vault,
    ripe_token,
    bob,
    alice,
    switchboard_bravo,
    gov_position,
):
    """DV-01 characterization (SV-1, SV-4).

    depositTokensWithLockDuration accepts any addys._isValidRipeAddr caller and
    SharesVault mints against the vault's *current* token balance rather than a
    receipt proven in this transaction. A registered non-Teller contract can
    therefore mint shares for an arbitrary beneficiary against custody already
    attributed to another user, while moving no tokens at all.
    """
    custody_before = ripe_token.balanceOf(ripe_gov_vault.address)
    bob_shares_before = ripe_gov_vault.userBalances(bob, ripe_token)
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == gov_position
    assert ripe_gov_vault.userBalances(alice, ripe_token) == 0

    # The attacker sends no tokens to the vault.
    minted = ripe_gov_vault.depositTokensWithLockDuration(
        alice, ripe_token, MAX_UINT256, 1_000, sender=switchboard_bravo.address
    )

    assert minted == gov_position
    assert ripe_token.balanceOf(ripe_gov_vault.address) == custody_before

    alice_shares = ripe_gov_vault.userBalances(alice, ripe_token)
    assert alice_shares > bob_shares_before * 10**19  # near-total dilution
    assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) >= gov_position - 1
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0

    # Alice also receives an attacker-chosen lock she never asked for.
    assert ripe_gov_vault.userGovData(alice, ripe_token).unlock == (
        boa.env.evm.patch.block_number + 1_000
    )


@pytest.mark.parametrize("caller_name", REGISTERED_NON_TELLER_CALLERS)
@pytest.mark.xfail(
    strict=True,
    reason="DV-01: RipeGov.depositTokensWithLockDuration still uses the broad "
    "addys._isValidRipeAddr predicate; least-privilege fix is gated on RH-CHANGE-01",
)
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


def test_registered_non_teller_adjusts_another_users_lock(
    ripe_gov_vault, ripe_token, bob, stability_pool, gov_position
):
    """DV-02 characterization (SV-4, RG-4).

    An unrelated registered contract -- here the StabilityPool, which has no
    production reason to touch governance locks -- can extend Bob's lock.
    """
    unlock_before = ripe_gov_vault.userGovData(bob, ripe_token).unlock

    ripe_gov_vault.adjustLock(bob, ripe_token, 1_000, sender=stability_pool.address)

    unlock_after = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    assert unlock_after == boa.env.evm.patch.block_number + 1_000
    assert unlock_after > unlock_before


@pytest.mark.parametrize("caller_name", REGISTERED_NON_TELLER_CALLERS)
@pytest.mark.xfail(
    strict=True,
    reason="DV-02: RipeGov.adjustLock still uses the broad addys._isValidRipeAddr "
    "predicate; least-privilege fix is gated on RH-CHANGE-01",
)
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


def test_registered_non_teller_releases_another_users_lock_and_burns_exit_fee(
    ripe_gov_vault, ripe_token, bob, stability_pool, locked_gov_position
):
    """DV-03 characterization (SV-4, RG-4).

    releaseLock charges the configured exit fee out of the victim's shares and
    clears the lock. An unrelated registered contract can force this on a user
    who never asked to exit early.
    """
    shares_before = ripe_gov_vault.userBalances(bob, ripe_token)
    unlock_before = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    assert unlock_before > boa.env.evm.patch.block_number

    ripe_gov_vault.releaseLock(bob, ripe_token, sender=stability_pool.address)
    logs = filter_logs(ripe_gov_vault, "LockReleased")

    # LOCK_TERMS exit fee is 10.00%.
    expected_removed = shares_before * LOCK_TERMS[4] // 100_00
    assert ripe_gov_vault.userBalances(bob, ripe_token) == shares_before - expected_removed
    assert ripe_gov_vault.userGovData(bob, ripe_token).unlock == 0

    assert len(logs) == 1
    assert logs[0].user == bob
    assert logs[0].exitFee == LOCK_TERMS[4]


@pytest.mark.parametrize("caller_name", REGISTERED_NON_TELLER_CALLERS)
@pytest.mark.xfail(
    strict=True,
    reason="DV-03: RipeGov.releaseLock still uses the broad addys._isValidRipeAddr "
    "predicate; least-privilege fix is gated on RH-CHANGE-01",
)
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


# --------------------------------------------------------------------------
# DV-04: same-address transferBalanceWithinVault is not a no-op
# --------------------------------------------------------------------------


@pytest.mark.parametrize("caller_name", ("auction_house", "credit_engine"))
def test_gov_same_user_zero_amount_transfer_reverts_without_state_change(
    caller_name,
    ripe_gov_vault,
    ripe_token,
    bob,
    auction_house,
    credit_engine,
    locked_gov_position,
    switchboard_alpha,
):
    """DV-04 boundary: the zero-amount same-address case already fails closed.

    SharesVault._calcWithdrawalSharesAndAmount asserts a nonzero withdrawal
    amount, so this corner of the Section 8.2 matrix is safe today. It is a
    plain passing regression, not a checkpoint.
    """
    caller = {"auction_house": auction_house, "credit_engine": credit_engine}[caller_name]
    boa.env.time_travel(blocks=50)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    before = _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob])

    with boa.reverts("no withdrawal amount"):
        ripe_gov_vault.transferBalanceWithinVault(
            ripe_token, bob, bob, 0, sender=caller.address
        )

    assert _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob]) == before


@pytest.mark.parametrize("caller_name", ("auction_house", "credit_engine"))
@pytest.mark.parametrize("portion", ("partial", "full"))
def test_gov_same_user_transfer_mutates_lock_and_points(
    caller_name,
    portion,
    ripe_gov_vault,
    ripe_token,
    bob,
    auction_house,
    credit_engine,
    locked_gov_position,
    switchboard_alpha,
):
    """DV-04 characterization (RG-5).

    RipeGov.transferBalanceWithinVault has no owner-equals-recipient guard. The
    AuctionHouse and CreditEngine paths run the full withdrawal-then-deposit
    governance bookkeeping against a single user, so a same-address move burns
    the proportional point penalty and re-weights the unlock toward the
    configured minimum lock duration instead of being a no-op.

    A full same-address transfer destroys the user's entire point balance:
    _handleGovDataOnWithdrawal reduces all points when the moved shares equal
    lastShares, and transferBalanceWithinVault passes _shouldTransferPoints
    False, so nothing is credited back.
    """
    caller = {"auction_house": auction_house, "credit_engine": credit_engine}[caller_name]
    amount = locked_gov_position if portion == "full" else locked_gov_position // 4

    boa.env.time_travel(blocks=50)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    before = _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob])
    points_before = ripe_gov_vault.userGovData(bob, ripe_token).govPoints
    unlock_before = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    shares_before = ripe_gov_vault.userBalances(bob, ripe_token)
    assert points_before > 0

    ripe_gov_vault.transferBalanceWithinVault(
        ripe_token, bob, bob, amount, sender=caller.address
    )

    after = _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob])
    assert after != before

    data = ripe_gov_vault.userGovData(bob, ripe_token)
    # Shares are conserved (out and straight back in) ...
    assert ripe_gov_vault.userBalances(bob, ripe_token) == shares_before
    # ... but points were burned and the unlock was re-weighted down.
    assert data.govPoints < points_before
    assert data.unlock < unlock_before
    if portion == "full":
        assert data.govPoints == 0
        assert ripe_gov_vault.totalUserGovPoints(bob) == 0


@pytest.mark.parametrize("caller_name", ("auction_house", "credit_engine"))
@pytest.mark.parametrize("portion", ("partial", "full"))
@pytest.mark.xfail(
    strict=True,
    reason="DV-04: RipeGov has no same-address short-circuit in "
    "transferBalanceWithinVault; the Section 9.2 guard is gated on RH-CHANGE-01",
)
def test_gov_same_user_transfer_is_complete_noop(
    caller_name,
    portion,
    ripe_gov_vault,
    ripe_token,
    bob,
    auction_house,
    credit_engine,
    locked_gov_position,
    switchboard_alpha,
):
    """DV-04 hardening target (RG-5). One node per caller and per portion."""
    caller = {"auction_house": auction_house, "credit_engine": credit_engine}[caller_name]
    amount = locked_gov_position if portion == "full" else locked_gov_position // 4

    boa.env.time_travel(blocks=50)
    ripe_gov_vault.updateUserGovPoints(bob, sender=switchboard_alpha.address)
    before = _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob])

    ripe_gov_vault.transferBalanceWithinVault(
        ripe_token, bob, bob, amount, sender=caller.address
    )
    assert _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob]) == before


def test_gov_transfer_to_a_different_user_still_moves_shares(
    ripe_gov_vault,
    ripe_token,
    bob,
    alice,
    auction_house,
    locked_gov_position,
):
    """Section 8.2 control: the non-same-address case must keep working.

    Guards against a Section 9.2 fix that over-reaches and breaks the real
    AuctionHouse seizure path.
    """
    bob_shares_before = ripe_gov_vault.userBalances(bob, ripe_token)
    assert ripe_gov_vault.userBalances(alice, ripe_token) == 0

    ripe_gov_vault.transferBalanceWithinVault(
        ripe_token, bob, alice, locked_gov_position // 2, sender=auction_house.address
    )

    assert ripe_gov_vault.userBalances(alice, ripe_token) > 0
    assert ripe_gov_vault.userBalances(bob, ripe_token) < bob_shares_before


# --------------------------------------------------------------------------
# DV-05: contributor lock duration is not clamped to governance bounds
# --------------------------------------------------------------------------


def test_contributor_transfer_shortens_recipient_lock_below_minimum(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    sally,
    teller,
    human_resources,
    switchboard_bravo,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    """DV-05 characterization (RG-4).

    RipeGov.transferContributorRipeTokens forwards the contributor's configured
    depositLockDuration straight into _getWeightedLockOnTokenDeposit without
    clamping it to the governance lock bounds. A large contributor payout with
    a short (or zero) configured duration therefore drags the recipient's
    existing unlock down, and the result can land below minLockDuration.
    """
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
    )
    min_lock, max_lock = LOCK_TERMS[0], LOCK_TERMS[1]

    # Recipient holds a small position at the maximum lock.
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
    unlock_before = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    assert unlock_before == boa.env.evm.patch.block_number + max_lock

    # Contributor holds a much larger position.
    _direct_deposit(
        ripe_gov_vault, ripe_token, whale, sally, 1_000 * EIGHTEEN_DECIMALS, teller
    )

    # Contributor payout carries a 1-block lock duration -- far below min_lock.
    ripe_gov_vault.transferContributorRipeTokens(
        sally, bob, 1, sender=human_resources.address
    )

    unlock_after = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    remaining = unlock_after - boa.env.evm.patch.block_number
    assert unlock_after < unlock_before
    assert remaining < min_lock  # the unclamped duration wins the weighted average
    assert ripe_gov_vault.userBalances(sally, ripe_token) == 0


@pytest.mark.xfail(
    strict=True,
    reason="DV-05: contributor lock duration is still unclamped in "
    "RipeGov._handleGovDataOnTransfer; the Section 9.3 fix is gated on RH-CHANGE-01",
)
def test_contributor_transfer_cannot_shorten_existing_lock(
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    sally,
    teller,
    human_resources,
    switchboard_bravo,
    mission_control,
    setAssetConfig,
    switchboard_alpha,
):
    """DV-05 hardening target (RG-4, Section 9.3)."""
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
    )
    max_lock = LOCK_TERMS[1]
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
    unlock_before = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    _direct_deposit(
        ripe_gov_vault, ripe_token, whale, sally, 1_000 * EIGHTEEN_DECIMALS, teller
    )

    ripe_gov_vault.transferContributorRipeTokens(
        sally, bob, 1, sender=human_resources.address
    )

    assert ripe_gov_vault.userGovData(bob, ripe_token).unlock >= unlock_before


# Section 8.2 boundary set, split by whether the clamp invariant already holds.
# A raw duration that happens to sit inside [minLockDuration, maxLockDuration]
# trivially satisfies the clamp, so only the out-of-bounds boundaries are
# checkpoints. Keeping them in one loop would have hidden that distinction.
CONTRIBUTOR_DURATIONS_IN_BOUNDS = (
    ("at_min", LOCK_TERMS[0]),
    ("ordinary", (LOCK_TERMS[0] + LOCK_TERMS[1]) // 2),
    ("at_max", LOCK_TERMS[1]),
)
CONTRIBUTOR_DURATIONS_OUT_OF_BOUNDS = (
    ("zero", 0),
    ("one", 1),
    ("below_min", LOCK_TERMS[0] - 1),
    ("above_max", LOCK_TERMS[1] + 1),
    ("far_above_max", LOCK_TERMS[1] * 10),
)
CONTRIBUTOR_DURATIONS = CONTRIBUTOR_DURATIONS_IN_BOUNDS + CONTRIBUTOR_DURATIONS_OUT_OF_BOUNDS


@pytest.mark.parametrize(
    "duration", [d for _label, d in CONTRIBUTOR_DURATIONS], ids=[l for l, _d in CONTRIBUTOR_DURATIONS]
)
def test_contributor_duration_lands_unclamped_on_a_fresh_recipient(
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
    """DV-05 characterization at every Section 8.2 duration boundary.

    With no prior recipient balance, _getWeightedLockOnTokenDeposit returns
    block.number + the raw requested duration, so the resulting unlock is
    exactly the unclamped input at every boundary -- including zero and values
    far above maxLockDuration.
    """
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


@pytest.mark.parametrize(
    "duration",
    [d for _label, d in CONTRIBUTOR_DURATIONS_IN_BOUNDS],
    ids=[l for l, _d in CONTRIBUTOR_DURATIONS_IN_BOUNDS],
)
def test_contributor_duration_inside_bounds_already_satisfies_the_clamp(
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
    """DV-05 control half: an in-bounds duration trivially lands in bounds.

    These three boundaries pass on the bound baseline, so they are plain
    regressions. They exist so a Section 9.3 clamp cannot silently change the
    in-bounds behavior while fixing the out-of-bounds cases.
    """
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
    )
    min_lock, max_lock = LOCK_TERMS[0], LOCK_TERMS[1]
    _direct_deposit(
        ripe_gov_vault, ripe_token, whale, sally, 100 * EIGHTEEN_DECIMALS, teller
    )

    ripe_gov_vault.transferContributorRipeTokens(
        sally, bob, duration, sender=human_resources.address
    )

    remaining = (
        ripe_gov_vault.userGovData(bob, ripe_token).unlock - boa.env.evm.patch.block_number
    )
    assert min_lock <= remaining <= max_lock
    assert remaining == duration


@pytest.mark.parametrize(
    "duration",
    [d for _label, d in CONTRIBUTOR_DURATIONS_OUT_OF_BOUNDS],
    ids=[l for l, _d in CONTRIBUTOR_DURATIONS_OUT_OF_BOUNDS],
)
@pytest.mark.xfail(
    strict=True,
    reason="DV-05: contributor lock duration is still unclamped in "
    "RipeGov._handleGovDataOnTransfer; the Section 9.3 fix is gated on RH-CHANGE-01",
)
def test_contributor_duration_is_clamped_to_current_governance_bounds(
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
    """DV-05 hardening target, bounds half (RG-4, Section 9.3).

    A fresh recipient with no prior lock must end up inside
    [minLockDuration, maxLockDuration] for any contributor duration.
    """
    _configure_ripe_gov_asset(
        mission_control,
        setAssetConfig,
        switchboard_alpha,
        ripe_token,
        [SOURCE_VAULT_ID],
    )
    min_lock, max_lock = LOCK_TERMS[0], LOCK_TERMS[1]
    _direct_deposit(
        ripe_gov_vault, ripe_token, whale, sally, 100 * EIGHTEEN_DECIMALS, teller
    )

    ripe_gov_vault.transferContributorRipeTokens(
        sally, bob, duration, sender=human_resources.address
    )

    remaining = (
        ripe_gov_vault.userGovData(bob, ripe_token).unlock - boa.env.evm.patch.block_number
    )
    assert min_lock <= remaining <= max_lock


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
    ("updateUserGovPoints", False),
    ("adjustLock", False),
    ("releaseLock", False),
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
            bob, ripe_token, EIGHTEEN_DECIMALS, 500, sender=switchboard_bravo.address
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

    VaultData.isPaused is consulted only by SharesVault's deposit, withdraw,
    and transfer helpers. Everything else -- point updates, both point-disable
    setters, and crucially adjustLock and releaseLock -- stays live while the
    vault is paused. releaseLock is the sharpest case: it reduces balances via
    vaultData._reduceBalanceOnWithdrawal directly, bypassing SharesVault
    entirely, so it burns the exit fee out of a paused vault.
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


@pytest.mark.parametrize("method", ("adjustLock", "releaseLock"))
@pytest.mark.xfail(
    strict=True,
    reason="DV-06: RipeGov pause semantics for adjustLock/releaseLock are "
    "unchanged pending the Section 9.4 owner decision under RH-CHANGE-01",
)
def test_gov_lock_mutation_reverts_while_vault_is_paused(
    method,
    ripe_gov_vault,
    ripe_token,
    bob,
    teller,
    switchboard_alpha,
    locked_gov_position,
):
    """DV-06 hardening target (SV-5, Section 9.4 preferred rule)."""
    boa.env.time_travel(blocks=10)
    ripe_gov_vault.pause(True, sender=switchboard_alpha.address)
    before = _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob])

    with boa.reverts("contract paused"):
        if method == "adjustLock":
            ripe_gov_vault.adjustLock(bob, ripe_token, 1_000, sender=teller.address)
        else:
            ripe_gov_vault.releaseLock(bob, ripe_token, sender=teller.address)

    assert _gov_state_snapshot(ripe_gov_vault, ripe_token, [bob]) == before
