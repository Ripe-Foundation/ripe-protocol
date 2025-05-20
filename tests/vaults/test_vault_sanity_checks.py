import pytest
import boa

from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, MAX_UINT256
from conf_utils import filter_logs


def test_deposit_stability_pool_vault(
    stability_pool,
    mock_price_source,
    price_desk,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    _test,
):
    alpha_token.transfer(teller, 1_000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # set mock price
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    assert price_desk.getPrice(alpha_token) == price

    # setup -- teller will transfer tokens to vault before calling function
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=teller.address)

    # no perms
    with boa.reverts("only Teller allowed"):
        stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=alpha_token_whale)

    # 0x0 user
    with boa.reverts("invalid user or asset"):
        stability_pool.depositTokensInVault(ZERO_ADDRESS, alpha_token, deposit_amount, sender=teller.address)

    # 0 amount
    with boa.reverts("invalid deposit amount"):
        stability_pool.depositTokensInVault(bob, alpha_token, 0, sender=teller.address)

    # deposit into vault
    deposited = stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    log = filter_logs(stability_pool, "StabilityPoolDeposit")[0]
    assert log.user == bob
    assert log.asset == alpha_token.address
    assert log.amount == deposited == deposit_amount
    assert log.shares != 0

     # balances
    assert stability_pool.userBalances(bob, alpha_token) != 0
    assert stability_pool.totalBalances(alpha_token) != 0

    assert stability_pool.getTotalAmountForUser(bob, alpha_token) == deposit_amount
    assert stability_pool.getTotalAmountForVault(alpha_token) == deposit_amount

    # user data
    assert stability_pool.userAssets(bob, 1) == alpha_token.address
    assert stability_pool.indexOfUserAsset(bob, alpha_token) == 1
    assert stability_pool.numUserAssets(bob) == 2

    # vault data
    assert stability_pool.vaultAssets(1) == alpha_token.address
    assert stability_pool.indexOfAsset(alpha_token) == 1
    assert stability_pool.numAssets() == 2

    # try messing with vault data
    with boa.reverts("only Lootbox allowed"):
        stability_pool.deregisterUserAsset(bob, alpha_token, sender=teller.address)
    with boa.reverts("only ControlRoom allowed"):
        stability_pool.deregisterVaultAsset(alpha_token, sender=teller.address)

    # double the vault balance
    alpha_token.transfer(stability_pool, deposit_amount, sender=teller.address)

    _test(deposit_amount * 2, stability_pool.getTotalAmountForUser(bob, alpha_token))
    _test(deposit_amount * 2, stability_pool.getTotalAmountForVault(alpha_token))


def test_stability_pool_swap_for_liq_collateral(
    stability_pool,
    mock_price_source,
    auction_house,
    price_desk,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    sally,
    teller,
    _test,
):
    alpha_token.transfer(teller, 1_000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

    # set mock price for stab asset
    alpha_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, alpha_price)
    assert price_desk.getPrice(alpha_token) == alpha_price

    # set mock price for claimable asset
    bravo_price = 2 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(bravo_token, bravo_price)
    assert price_desk.getPrice(bravo_token) == bravo_price

    # deposit into vault
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=teller.address)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    assert stability_pool.getTotalUserValue(bob, alpha_token) == deposit_amount

    # swap for liq collateral
    stab_amount = 50 * EIGHTEEN_DECIMALS
    liq_amount = 200 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, liq_amount, sender=bravo_token_whale)
    received_amount = stability_pool.swapForLiquidatedCollateral(alpha_token, stab_amount, bravo_token, liq_amount, bob, ZERO_ADDRESS, sender=auction_house.address)
    assert received_amount == stab_amount

    # check balances
    assert alpha_token.balanceOf(stability_pool) == deposit_amount - stab_amount
    assert alpha_token.balanceOf(bob) == received_amount
    assert bravo_token.balanceOf(stability_pool) == liq_amount

    # test value
    expected_value = (deposit_amount // 2) + (liq_amount * 2) # 50 + 400
    _test(expected_value, stability_pool.getTotalUserValue(bob, alpha_token))

    # stab data
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == liq_amount
    assert stability_pool.totalClaimableBalances(bravo_token) == liq_amount

    assert stability_pool.claimableAssets(alpha_token, 1) == bravo_token.address
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 1
    assert stability_pool.numClaimableAssets(alpha_token) == 2

    # new deposit
    sally_deposit_amount = 450 * EIGHTEEN_DECIMALS # should get 50% of shares
    alpha_token.transfer(stability_pool, sally_deposit_amount, sender=teller.address)
    stability_pool.depositTokensInVault(sally, alpha_token, sally_deposit_amount, sender=teller.address)
    _test(sally_deposit_amount, stability_pool.getTotalUserValue(sally, alpha_token))

    # check shares, should be roughly equal
    _test(stability_pool.userBalances(sally, alpha_token), stability_pool.userBalances(bob, alpha_token))

    # claim assets
    stability_pool.claimFromStabilityPool(sally, alpha_token, bravo_token, MAX_UINT256, sender=teller.address)
    assert bravo_token.balanceOf(sally) == liq_amount

    # test value
    _test(50 * EIGHTEEN_DECIMALS, stability_pool.getTotalUserValue(sally, alpha_token))
    
    # stab data
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
    assert stability_pool.totalClaimableBalances(bravo_token) == 0

    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 0
    assert stability_pool.numClaimableAssets(alpha_token) == 1