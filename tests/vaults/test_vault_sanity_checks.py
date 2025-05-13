import pytest
import boa

from constants import ZERO_ADDRESS
from conf_utils import filter_logs


def test_deposit_simple_erc20_vault(
    simple_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
):
    alpha_token.transfer(teller, 1_000 * (10 ** alpha_token.decimals()), sender=alpha_token_whale)

    # setup -- teller will transfer tokens to vault before calling function
    deposit_amount = 100 * (10 ** alpha_token.decimals())
    alpha_token.transfer(simple_erc20_vault, deposit_amount, sender=teller.address)

    # no perms
    with boa.reverts("only Teller allowed"):
        simple_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=alpha_token_whale)

    # 0x0 user
    with boa.reverts("invalid user or asset"):
        simple_erc20_vault.depositTokensInVault(ZERO_ADDRESS, alpha_token, deposit_amount, sender=teller.address)

    # 0 amount
    with boa.reverts("invalid deposit amount"):
        simple_erc20_vault.depositTokensInVault(bob, alpha_token, 0, sender=teller.address)

    # deposit into vault
    deposited = simple_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    log = filter_logs(simple_erc20_vault, "SimpleErc20VaultDeposit")[0]
    assert log.user == bob
    assert log.asset == alpha_token.address
    assert log.amount == deposited == deposit_amount

    # balances
    assert simple_erc20_vault.userBalances(bob, alpha_token) == deposit_amount
    assert simple_erc20_vault.totalBalances(alpha_token) == deposit_amount

    # user data
    assert simple_erc20_vault.userAssets(bob, 1) == alpha_token.address
    assert simple_erc20_vault.indexOfUserAsset(bob, alpha_token) == 1
    assert simple_erc20_vault.numUserAssets(bob) == 2

    # vault data
    assert simple_erc20_vault.vaultAssets(1) == alpha_token.address
    assert simple_erc20_vault.indexOfAsset(alpha_token) == 1
    assert simple_erc20_vault.numAssets() == 2

    # try messing with vault data
    with boa.reverts("only Lootbox allowed"):
        simple_erc20_vault.deregisterUserAsset(bob, alpha_token, sender=teller.address)
    with boa.reverts("only ControlRoom allowed"):
        simple_erc20_vault.deregisterVaultAsset(alpha_token, sender=teller.address)


def test_deposit_rebase_erc20_vault(
    rebase_erc20_vault,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    _test,
):
    alpha_token.transfer(teller, 1_000 * (10 ** alpha_token.decimals()), sender=alpha_token_whale)

    # setup -- teller will transfer tokens to vault before calling function
    deposit_amount = 100 * (10 ** alpha_token.decimals())
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=teller.address)

    # no perms
    with boa.reverts("only Teller allowed"):
        rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=alpha_token_whale)

    # 0x0 user
    with boa.reverts("invalid user or asset"):
        rebase_erc20_vault.depositTokensInVault(ZERO_ADDRESS, alpha_token, deposit_amount, sender=teller.address)

    # 0 amount
    with boa.reverts("invalid deposit amount"):
        rebase_erc20_vault.depositTokensInVault(bob, alpha_token, 0, sender=teller.address)

    # deposit into vault
    deposited = rebase_erc20_vault.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    log = filter_logs(rebase_erc20_vault, "RebaseErc20VaultDeposit")[0]
    assert log.user == bob
    assert log.asset == alpha_token.address
    assert log.amount == deposited == deposit_amount
    assert log.shares != 0

     # balances
    assert rebase_erc20_vault.userBalances(bob, alpha_token) != 0
    assert rebase_erc20_vault.totalBalances(alpha_token) != 0

    assert rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token) == deposit_amount
    assert rebase_erc20_vault.getTotalAmountForVault(alpha_token) == deposit_amount

    # user data
    assert rebase_erc20_vault.userAssets(bob, 1) == alpha_token.address
    assert rebase_erc20_vault.indexOfUserAsset(bob, alpha_token) == 1
    assert rebase_erc20_vault.numUserAssets(bob) == 2

    # vault data
    assert rebase_erc20_vault.vaultAssets(1) == alpha_token.address
    assert rebase_erc20_vault.indexOfAsset(alpha_token) == 1
    assert rebase_erc20_vault.numAssets() == 2

    # try messing with vault data
    with boa.reverts("only Lootbox allowed"):
        rebase_erc20_vault.deregisterUserAsset(bob, alpha_token, sender=teller.address)
    with boa.reverts("only ControlRoom allowed"):
        rebase_erc20_vault.deregisterVaultAsset(alpha_token, sender=teller.address)

    # double the vault balance
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=teller.address)

    _test(deposit_amount * 2, rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token))
    _test(deposit_amount * 2, rebase_erc20_vault.getTotalAmountForVault(alpha_token))
