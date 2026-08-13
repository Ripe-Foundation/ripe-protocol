import boa
import pytest

from constants import EIGHTEEN_DECIMALS


@pytest.fixture(scope="module")
def setupRipeGovVaultConfig(
    mission_control,
    setGeneralConfig,
    setAssetConfig,
    switchboard_alpha,
    vault_book,
    ripe_gov_vault,
    ripe_token,
):
    def setupRipeGovVaultConfig():
        canonical_id = vault_book.getRegId(ripe_gov_vault)
        assert canonical_id == mission_control.coreRipeGovVaultId()
        setGeneralConfig()
        mission_control.setRipeGovVaultConfig(
            ripe_token,
            100_00,
            False,
            (100, 1000, 200_00, True, 10_00),
            sender=switchboard_alpha.address,
        )
        setAssetConfig(ripe_token, _vaultIds=[canonical_id])

    return setupRipeGovVaultConfig


def _register_vault(vault_book, governance, vault, description):
    assert vault_book.startAddNewAddressToRegistry(
        vault,
        description,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    return vault_book.confirmNewAddressToRegistry(
        vault,
        sender=governance.address,
    )


def _boardroom_state(boardroom):
    return boardroom.isPaused(), boardroom.getRipeHq()


def _call_boardroom(boardroom, sender):
    boardroom.govPowerDidChangeForUser(sender, 123, 456, sender=sender)


def _assert_canonical_ripe_gov_is_live(
    vault_book,
    mission_control,
    ripe_gov_vault,
):
    canonical_id = vault_book.getRegId(ripe_gov_vault)
    assert canonical_id == mission_control.coreRipeGovVaultId()
    assert vault_book.getAddr(canonical_id) == ripe_gov_vault.address
    assert mission_control.isRipeGovVaultId(canonical_id)


def test_rejects_unauthorized_eoa(boardroom, bob):
    with boa.reverts("no perms"):
        _call_boardroom(boardroom, bob)


def test_rejects_unregistered_contract(
    boardroom,
    vault_book,
    mock_rando_contract,
):
    assert vault_book.getRegId(mock_rando_contract) == 0

    with boa.reverts("no perms"):
        _call_boardroom(boardroom, mock_rando_contract.address)


def test_rejects_registered_non_ripe_gov_vault(
    boardroom,
    vault_book,
    mission_control,
    simple_erc20_vault,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    assert vault_id != 0
    assert not mission_control.isRipeGovVaultId(vault_id)

    with boa.reverts("no perms"):
        _call_boardroom(boardroom, simple_erc20_vault.address)


def test_accepts_current_registered_ripe_gov_and_remains_noop(
    boardroom,
    vault_book,
    mission_control,
    ripe_gov_vault,
):
    vault_id = vault_book.getRegId(ripe_gov_vault)
    assert vault_id != 0
    assert mission_control.isRipeGovVaultId(vault_id)

    state_before = _boardroom_state(boardroom)
    _call_boardroom(boardroom, ripe_gov_vault.address)
    assert _boardroom_state(boardroom) == state_before


def test_real_ripe_gov_callback_succeeds(
    boardroom,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    teller,
    switchboard_alpha,
):
    setupRipeGovVaultConfig()
    assert ripe_gov_vault.getAddys().boardroom == boardroom.address
    amount = 100 * EIGHTEEN_DECIMALS
    ripe_token.transfer(bob, amount, sender=whale)
    ripe_token.approve(teller, amount, sender=bob)

    state_before = _boardroom_state(boardroom)
    assert teller.deposit(
        ripe_token,
        amount,
        bob,
        ripe_gov_vault,
        sender=bob,
    ) == amount
    boa.env.time_travel(blocks=100)
    ripe_gov_vault.updateUserGovPoints(
        bob,
        sender=switchboard_alpha.address,
    )

    user_points = ripe_gov_vault.totalUserGovPoints(bob)
    assert user_points > 0
    assert ripe_gov_vault.totalGovPoints() == user_points
    assert _boardroom_state(boardroom) == state_before


def test_old_ripe_gov_stays_authorized_during_new_id_pointer_migration(
    boardroom,
    vault_book,
    mission_control,
    alternate_ripe_gov_vault,
    governance,
    switchboard_alpha,
    ripe_gov_vault,
):
    old_id = vault_book.getRegId(ripe_gov_vault)
    assert old_id == mission_control.coreRipeGovVaultId()
    new_id = _register_vault(
        vault_book,
        governance,
        alternate_ripe_gov_vault,
        "New core RipeGov",
    )
    mission_control.setCoreRipeGovVaultId(
        new_id,
        sender=switchboard_alpha.address,
    )

    assert old_id != new_id
    assert vault_book.getRegId(ripe_gov_vault) == old_id
    assert vault_book.getRegId(alternate_ripe_gov_vault) == new_id
    assert mission_control.isRipeGovVaultId(old_id)
    assert mission_control.isRipeGovVaultId(new_id)
    _call_boardroom(boardroom, ripe_gov_vault.address)
    _call_boardroom(boardroom, alternate_ripe_gov_vault.address)

    mission_control.setCoreRipeGovVaultId(
        old_id,
        sender=switchboard_alpha.address,
    )
    _assert_canonical_ripe_gov_is_live(
        vault_book,
        mission_control,
        ripe_gov_vault,
    )


def test_live_historical_ripe_gov_id_is_authorized_until_same_id_update(
    boardroom,
    vault_book,
    mission_control,
    alternate_ripe_gov_vault,
    governance,
    switchboard_alpha,
    ripe_gov_vault,
):
    old_vault = alternate_ripe_gov_vault
    canonical_id = mission_control.coreRipeGovVaultId()
    assert vault_book.getRegId(ripe_gov_vault) == canonical_id
    old_id = _register_vault(
        vault_book,
        governance,
        old_vault,
        "Historical RipeGov",
    )
    mission_control.setCoreRipeGovVaultId(
        old_id,
        sender=switchboard_alpha.address,
    )
    mission_control.setCoreRipeGovVaultId(
        canonical_id,
        sender=switchboard_alpha.address,
    )

    assert mission_control.isRipeGovVaultId(old_id)
    assert vault_book.getRegId(old_vault) == old_id
    _call_boardroom(boardroom, old_vault.address)

    replacement = boa.load(
        "contracts/vaults/RipeGov.vy",
        old_vault.getRipeHq(),
        name="same_id_replacement_ripe_gov_vault",
    )
    assert vault_book.startAddressUpdateToRegistry(
        old_id,
        replacement,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    assert vault_book.confirmAddressUpdateToRegistry(
        old_id,
        sender=governance.address,
    )

    assert vault_book.getRegId(old_vault) == 0
    assert vault_book.getRegId(replacement) == old_id
    assert mission_control.isRipeGovVaultId(old_id)
    with boa.reverts("no perms"):
        _call_boardroom(boardroom, old_vault.address)
    _call_boardroom(boardroom, replacement.address)
    _assert_canonical_ripe_gov_is_live(
        vault_book,
        mission_control,
        ripe_gov_vault,
    )


def test_disabled_ripe_gov_loses_authorization_when_registration_is_cleared(
    boardroom,
    vault_book,
    mission_control,
    alternate_ripe_gov_vault,
    governance,
    switchboard_alpha,
    ripe_gov_vault,
):
    old_vault = alternate_ripe_gov_vault
    canonical_id = mission_control.coreRipeGovVaultId()
    assert vault_book.getRegId(ripe_gov_vault) == canonical_id
    old_id = _register_vault(
        vault_book,
        governance,
        old_vault,
        "Disabled RipeGov",
    )
    mission_control.setCoreRipeGovVaultId(
        old_id,
        sender=switchboard_alpha.address,
    )
    mission_control.setCoreRipeGovVaultId(
        canonical_id,
        sender=switchboard_alpha.address,
    )

    assert not old_vault.doesVaultHaveAnyFunds()
    assert mission_control.isRipeGovVaultId(old_id)
    _call_boardroom(boardroom, old_vault.address)
    assert vault_book.startAddressDisableInRegistry(
        old_id,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    assert vault_book.confirmAddressDisableInRegistry(
        old_id,
        sender=governance.address,
    )

    assert vault_book.getRegId(old_vault) == 0
    assert mission_control.isRipeGovVaultId(old_id)
    with boa.reverts("no perms"):
        _call_boardroom(boardroom, old_vault.address)
    _assert_canonical_ripe_gov_is_live(
        vault_book,
        mission_control,
        ripe_gov_vault,
    )


def test_funded_ripe_gov_cannot_be_disabled_at_confirmation(
    vault_book,
    mission_control,
    alternate_ripe_gov_vault,
    ripe_gov_vault,
    governance,
    switchboard_alpha,
    ripe_token,
    whale,
    bob,
    teller,
):
    funded_vault = alternate_ripe_gov_vault
    canonical_id = mission_control.coreRipeGovVaultId()
    assert vault_book.getRegId(ripe_gov_vault) == canonical_id
    vault_id = _register_vault(
        vault_book,
        governance,
        funded_vault,
        "Funded RipeGov",
    )
    mission_control.setCoreRipeGovVaultId(
        vault_id,
        sender=switchboard_alpha.address,
    )
    mission_control.setCoreRipeGovVaultId(
        canonical_id,
        sender=switchboard_alpha.address,
    )
    assert vault_book.startAddressDisableInRegistry(
        vault_id,
        sender=governance.address,
    )

    amount = EIGHTEEN_DECIMALS
    ripe_token.transfer(funded_vault, amount, sender=whale)
    funded_vault.depositTokensInVault(
        bob,
        ripe_token,
        amount,
        sender=teller.address,
    )
    assert funded_vault.doesVaultHaveAnyFunds()

    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
    with boa.reverts("vault has funds"):
        vault_book.confirmAddressDisableInRegistry(
            vault_id,
            sender=governance.address,
        )
    assert vault_book.getRegId(funded_vault) == vault_id

    withdrawal_amount, is_depleted = funded_vault.withdrawTokensFromVault(
        bob,
        ripe_token,
        amount,
        bob,
        sender=teller.address,
    )
    assert withdrawal_amount == amount
    assert is_depleted
    assert not funded_vault.doesVaultHaveAnyFunds()
    assert vault_book.confirmAddressDisableInRegistry(
        vault_id,
        sender=governance.address,
    )
    assert vault_book.getRegId(funded_vault) == 0
    _assert_canonical_ripe_gov_is_live(
        vault_book,
        mission_control,
        ripe_gov_vault,
    )
