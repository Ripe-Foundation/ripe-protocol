import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS
from tests.vaults.ripe_gov_exit_fee_model import claim


VAULT_ID = 2
LOCK_TERMS = (100, 1_000, 200_00, True, 10_00)
UNDERSCORE_LEDGER_ID = 1
UNDERSCORE_LEGO_BOOK_ID = 3

UNDERSCORE_WALLET_SOURCE = """
# @version 0.4.3

owner: public(address)

@deploy
def __init__(_owner: address):
    self.owner = _owner

@view
@external
def walletConfig() -> address:
    return self
"""


def _configure_gov_asset(
    asset,
    mission_control,
    setAssetConfig,
    setGeneralConfig,
    switchboard_alpha,
):
    setGeneralConfig()
    mission_control.setRipeGovVaultConfig(
        asset,
        100_00,
        False,
        LOCK_TERMS,
        sender=switchboard_alpha.address,
    )
    setAssetConfig(asset, _vaultIds=[VAULT_ID])


def _direct_locked_deposit(vault, token, funder, user, amount, teller):
    token.transfer(vault, amount, sender=funder)
    return vault.depositTokensWithLockDuration(
        user,
        token,
        amount,
        500,
        sender=teller.address,
    )


def _set_registry(mission_control, mock_undy_v2, switchboard_alpha, *valid_addrs):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_undy_v2.setAllAddressesAreValid(False)
    for addr in valid_addrs:
        mock_undy_v2.setValidAddress(addr, True)


def _grant_full_access(user, lego, setUserConfig, setUserDelegation):
    setUserConfig(
        user,
        _canAnyoneDeposit=True,
        _canAnyoneRepayDebt=True,
    )
    setUserDelegation(
        user,
        lego,
        _canWithdraw=True,
        _canBorrow=True,
        _canClaimFromStabPool=True,
        _canClaimLoot=True,
    )


def _release_snapshot(vault, token, user, remaining_holder, ledger):
    custody = token.balanceOf(vault)
    total_shares = vault.totalBalances(token)
    user_shares = vault.userBalances(user, token)
    remaining_shares = vault.userBalances(remaining_holder, token)
    return (
        custody,
        total_shares,
        user_shares,
        remaining_shares,
        claim(user_shares, total_shares, custody),
        claim(remaining_shares, total_shares, custody),
        tuple(vault.userGovData(user, token)),
        tuple(ledger.getDepositLedgerData(user, VAULT_ID)),
        tuple(ledger.userDepositPoints(user, VAULT_ID, token)),
    )


def test_teller_utils_lego_path_is_registered_user_bound_and_revocable(
    teller_utils,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
    alice,
    bob,
    sally,
    setUserConfig,
    setUserDelegation,
):
    assert teller_utils.isUnderscoreOwnerOrLego(bob, alice) is False

    _set_registry(mission_control, mock_undy_v2, switchboard_alpha, alice)
    assert teller_utils.isUnderscoreOwnerOrLego(bob, alice) is False

    _grant_full_access(bob, alice, setUserConfig, setUserDelegation)
    assert teller_utils.isUnderscoreOwnerOrLego(bob, alice) is True
    assert teller_utils.isUnderscoreOwnerOrLego(sally, alice) is False

    setUserDelegation(bob, alice, _canBorrow=False)
    assert teller_utils.isUnderscoreOwnerOrLego(bob, alice) is False

    setUserDelegation(bob, alice)
    assert teller_utils.isUnderscoreOwnerOrLego(bob, alice) is True
    mock_undy_v2.setValidAddress(alice, False)
    assert teller_utils.isUnderscoreOwnerOrLego(bob, alice) is False


def test_teller_utils_owner_path_is_wallet_specific_and_missing_registry_fails_closed(
    teller_utils,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
    alice,
    bob,
):
    alice_wallet = boa.loads(UNDERSCORE_WALLET_SOURCE, alice, name="alice_undy_wallet")
    bob_wallet = boa.loads(UNDERSCORE_WALLET_SOURCE, bob, name="bob_undy_wallet")
    _set_registry(mission_control, mock_undy_v2, switchboard_alpha)
    mock_undy_v2.setUserWallet(alice_wallet, True)
    mock_undy_v2.setUserWallet(bob_wallet, True)

    assert teller_utils.isUnderscoreOwnerOrLego(alice_wallet, alice) is True
    assert teller_utils.isUnderscoreOwnerOrLego(bob_wallet, alice) is False

    mock_undy_v2.setMissingRegId(UNDERSCORE_LEDGER_ID)
    assert teller_utils.isUnderscoreOwnerOrLego(alice_wallet, alice) is False
    mock_undy_v2.setMissingRegId(UNDERSCORE_LEGO_BOOK_ID)
    assert teller_utils.isUnderscoreOwnerOrLego(bob_wallet, alice) is False


def test_gov_vault_deposit_requires_user_grant_and_rejection_is_atomic(
    teller,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    sally,
    ledger,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
    setAssetConfig,
    setGeneralConfig,
    setUserConfig,
    setUserDelegation,
):
    _configure_gov_asset(
        ripe_token,
        mission_control,
        setAssetConfig,
        setGeneralConfig,
        switchboard_alpha,
    )
    _set_registry(mission_control, mock_undy_v2, switchboard_alpha, alice)
    _grant_full_access(bob, alice, setUserConfig, setUserDelegation)

    amount = 100 * EIGHTEEN_DECIMALS
    ripe_token.transfer(alice, amount * 2, sender=whale)
    ripe_token.approve(teller, amount * 2, sender=alice)

    assert teller.depositIntoGovVault(
        ripe_token,
        amount,
        500,
        bob,
        sender=alice,
    ) == amount

    before = (
        ripe_token.balanceOf(alice),
        ripe_token.balanceOf(ripe_gov_vault),
        ripe_gov_vault.userBalances(sally, ripe_token),
        tuple(ripe_gov_vault.userGovData(sally, ripe_token)),
        tuple(ledger.getDepositLedgerData(sally, VAULT_ID)),
    )
    with boa.reverts("no perms"):
        teller.depositIntoGovVault(
            ripe_token,
            amount,
            500,
            sally,
            sender=alice,
        )
    assert filter_logs(teller, "TellerDeposit") == []
    after = (
        ripe_token.balanceOf(alice),
        ripe_token.balanceOf(ripe_gov_vault),
        ripe_gov_vault.userBalances(sally, ripe_token),
        tuple(ripe_gov_vault.userGovData(sally, ripe_token)),
        tuple(ledger.getDepositLedgerData(sally, VAULT_ID)),
    )
    assert after == before


def test_adjust_and_release_are_user_bound_and_rejections_are_atomic(
    teller,
    ripe_gov_vault,
    ripe_token,
    whale,
    bob,
    alice,
    sally,
    ledger,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
    setAssetConfig,
    setGeneralConfig,
    setUserConfig,
    setUserDelegation,
):
    _configure_gov_asset(
        ripe_token,
        mission_control,
        setAssetConfig,
        setGeneralConfig,
        switchboard_alpha,
    )
    _direct_locked_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        bob,
        100 * EIGHTEEN_DECIMALS,
        teller,
    )
    _direct_locked_deposit(
        ripe_gov_vault,
        ripe_token,
        whale,
        sally,
        100 * EIGHTEEN_DECIMALS,
        teller,
    )
    _set_registry(mission_control, mock_undy_v2, switchboard_alpha, alice)
    _grant_full_access(bob, alice, setUserConfig, setUserDelegation)

    teller.adjustLock(ripe_token, 800, bob, sender=alice)
    assert ripe_gov_vault.userGovData(bob, ripe_token).unlock == (
        boa.env.evm.patch.block_number + 800
    )

    adjust_before = tuple(ripe_gov_vault.userGovData(sally, ripe_token))
    with boa.reverts("no perms"):
        teller.adjustLock(ripe_token, 800, sally, sender=alice)
    assert filter_logs(teller, "LockModified") == []
    assert tuple(ripe_gov_vault.userGovData(sally, ripe_token)) == adjust_before

    release_before = _release_snapshot(
        ripe_gov_vault,
        ripe_token,
        sally,
        bob,
        ledger,
    )
    with boa.reverts("no perms"):
        teller.releaseLock(ripe_token, sally, sender=alice)
    assert filter_logs(teller, "LockReleased") == []
    assert _release_snapshot(
        ripe_gov_vault,
        ripe_token,
        sally,
        bob,
        ledger,
    ) == release_before

    teller.releaseLock(ripe_token, bob, sender=alice)
    release = filter_logs(teller, "LockReleased")[-1]
    assert release.user == bob
    assert release.exitFee == 10_00


def test_wallet_owner_self_and_switchboard_lock_paths_remain_valid(
    teller,
    ripe_gov_vault,
    ripe_token,
    whale,
    alice,
    bob,
    sally,
    mission_control,
    mock_undy_v2,
    switchboard_alpha,
    setAssetConfig,
    setGeneralConfig,
):
    _configure_gov_asset(
        ripe_token,
        mission_control,
        setAssetConfig,
        setGeneralConfig,
        switchboard_alpha,
    )
    wallet = boa.loads(UNDERSCORE_WALLET_SOURCE, alice, name="route_undy_wallet")
    _set_registry(mission_control, mock_undy_v2, switchboard_alpha)
    mock_undy_v2.setUserWallet(wallet, True)

    for user in (wallet.address, bob, sally):
        _direct_locked_deposit(
            ripe_gov_vault,
            ripe_token,
            whale,
            user,
            100 * EIGHTEEN_DECIMALS,
            teller,
        )

    with boa.env.anchor():
        teller.adjustLock(ripe_token, 800, wallet, sender=alice)
        teller.releaseLock(ripe_token, wallet, sender=alice)
        assert filter_logs(teller, "LockReleased")[-1].user == wallet.address

    with boa.env.anchor():
        teller.adjustLock(ripe_token, 800, bob, sender=bob)
        teller.releaseLock(ripe_token, bob, sender=bob)
        assert filter_logs(teller, "LockReleased")[-1].user == bob

    with boa.env.anchor():
        teller.adjustLock(
            ripe_token,
            800,
            sally,
            sender=switchboard_alpha.address,
        )
        teller.releaseLock(
            ripe_token,
            sally,
            sender=switchboard_alpha.address,
        )
        assert filter_logs(teller, "LockReleased")[-1].user == sally
