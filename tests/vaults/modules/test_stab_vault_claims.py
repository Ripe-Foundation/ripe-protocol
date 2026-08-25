import pytest
import boa
from boa.contracts.base_evm_contract import BoaError
from eth_utils import to_checksum_address

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from conf_utils import (
    assert_reverted_call,
    claim_from_stability_pool,
    filter_logs,
    sync_deployed_token,
)


ARB_SYS = to_checksum_address("0x0000000000000000000000000000000000000064")
LEDGER_ID = 4


def _replace_ledger_with_arb_source(
    ripe_hq_deploy,
    defaults,
    governance,
    child_identity,
):
    implementation = boa.loads(
        """# @version 0.4.3
actionBlock: uint256

@view
@external
def arbBlockNumber() -> uint256:
    return self.actionBlock
""",
        name="claim_many_arb_source",
    )
    boa.env.set_code(ARB_SYS, boa.env.get_code(implementation.address))
    boa.env.set_storage(ARB_SYS, 0, child_identity)

    arb_ledger = boa.load(
        "contracts/data/Ledger.vy",
        ripe_hq_deploy,
        defaults,
        ARB_SYS,
        name="claim_many_arb_ledger",
    )
    assert ripe_hq_deploy.startAddressUpdateToRegistry(
        LEDGER_ID,
        arb_ledger,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=ripe_hq_deploy.registryChangeTimeLock())
    assert ripe_hq_deploy.confirmAddressUpdateToRegistry(
        LEDGER_ID,
        sender=governance.address,
    )
    return arb_ledger


def _set_claim_many_child_identity(child_identity):
    boa.env.set_storage(ARB_SYS, 0, child_identity)


def test_stab_vault_claims_full(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # swap
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        deposit_amount,     # stab asset amount
        bravo_token,  # liq asset
        claimable_amount,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        alpha_token,  # green token
        savings_green,
        sender=auction_house.address
    )

    # claim!
    vault_id = vault_book.getRegId(stability_pool)
    usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)

    # test
    _test(claimable_amount, usd_value)
    assert stability_pool.getTotalUserValue(bob, alpha_token) <= 1
    assert stability_pool.getTotalValue(alpha_token) <= 1

    _test(claimable_amount, bravo_token.balanceOf(bob))


def test_stab_claim_credits_forward_value_of_zero_decimal_delivery(
    governance,
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    setGeneralConfig,
    setAssetConfig,
):
    coarse_token = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "Coarse Token",
        "COARSE",
        0,
        1,
    )
    sync_deployed_token(coarse_token)
    setGeneralConfig()
    setAssetConfig(coarse_token)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(coarse_token, 3 * EIGHTEEN_DECIMALS)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob, alpha_token, deposit_amount, sender=teller.address
    )
    coarse_token.transfer(stability_pool, 1, sender=governance.address)
    recipient_balance_before = alpha_token.balanceOf(governance)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        3 * EIGHTEEN_DECIMALS,
        coarse_token,
        1,
        governance,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    assert alpha_token.balanceOf(governance) - recipient_balance_before == (
        3 * EIGHTEEN_DECIMALS
    )

    vault_id = vault_book.getRegId(stability_pool)
    claimed_value = claim_from_stability_pool(
        teller,
        vault_id,
        alpha_token,
        coarse_token,
        5 * EIGHTEEN_DECIMALS,
        sender=bob,
    )

    assert claimed_value == 3 * EIGHTEEN_DECIMALS
    log = filter_logs(teller, "AssetClaimedInStabilityPool")[0]
    assert log.claimAmount == 1
    assert log.claimUsdValue == 3 * EIGHTEEN_DECIMALS
    assert coarse_token.balanceOf(bob) == 1


def test_stab_claim_coarse_full_quote_preserves_unpaid_share_value(
    governance,
    stability_pool,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    setGeneralConfig,
    setAssetConfig,
):
    coarse_token = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "Coarse Full Claim",
        "CFC",
        0,
        1,
    )
    sync_deployed_token(coarse_token)
    setGeneralConfig()
    setAssetConfig(coarse_token)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(coarse_token, 3 * EIGHTEEN_DECIMALS)

    deposit_amount = 5 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob, alpha_token, deposit_amount, sender=teller.address
    )
    coarse_token.transfer(stability_pool, 1, sender=governance.address)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        3 * EIGHTEEN_DECIMALS,
        coarse_token,
        1,
        governance,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    assert stability_pool.getTotalUserValue(bob, alpha_token) == deposit_amount

    vault_id = vault_book.getRegId(stability_pool)
    claimed_value = claim_from_stability_pool(
        teller,
        vault_id,
        alpha_token,
        coarse_token,
        deposit_amount,
        sender=bob,
    )

    assert claimed_value == 3 * EIGHTEEN_DECIMALS
    assert coarse_token.balanceOf(bob) == 1
    assert stability_pool.userBalances(bob, alpha_token) != 0
    assert stability_pool.getTotalUserValue(bob, alpha_token) == (
        2 * EIGHTEEN_DECIMALS
    )
    log = filter_logs(teller, "AssetClaimedInStabilityPool")[0]
    assert not log.isDepleted


def test_stability_claim_checkpoints_deposit_points_after_share_burn(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    lootbox,
    ledger,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
):
    """A claim accrues through the burn block, then stops at zero shares."""
    setGeneralConfig()
    vault_id = vault_book.getRegId(stability_pool)
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    setAssetConfig(bravo_token)
    setRipeRewardsConfig(True)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob, alpha_token, amount, sender=teller.address
    )
    lootbox.updateDepositPoints(
        bob, vault_id, stability_pool, alpha_token, sender=teller.address
    )
    points_before = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert points_before.lastBalance > 0
    assert points_before.balancePoints == 0

    boa.env.time_travel(blocks=10)
    bravo_token.transfer(stability_pool, amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        amount,
        bravo_token,
        amount,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )
    assert claim_from_stability_pool(
        teller, vault_id, alpha_token, bravo_token, sender=bob
    ) == amount

    points_after_claim = ledger.userDepositPoints(bob, vault_id, alpha_token)
    elapsed = points_after_claim.lastUpdate - points_before.lastUpdate
    assert elapsed == 10
    assert points_after_claim.balancePoints == points_before.lastBalance * elapsed
    assert points_after_claim.lastBalance == 0
    assert stability_pool.userBalances(bob, alpha_token) == 0

    boa.env.time_travel(blocks=10)
    lootbox.updateDepositPoints(
        bob, vault_id, stability_pool, alpha_token, sender=teller.address
    )
    points_after_zero_interval = ledger.userDepositPoints(
        bob, vault_id, alpha_token
    )
    assert points_after_zero_interval.balancePoints == (
        points_after_claim.balancePoints
    )
    assert points_after_zero_interval.lastBalance == 0


def test_stability_claim_batch_checkpoints_final_partial_share_once(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    lootbox,
    ledger,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
):
    """Duplicate and multi-asset successes checkpoint one final live share."""
    setGeneralConfig()
    vault_id = vault_book.getRegId(stability_pool)
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)
    setRipeRewardsConfig(True)
    for asset in (alpha_token, bravo_token, charlie_token):
        mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)

    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob, alpha_token, deposit_amount, sender=teller.address
    )
    lootbox.updateDepositPoints(
        bob, vault_id, stability_pool, alpha_token, sender=teller.address
    )
    points_before = ledger.userDepositPoints(bob, vault_id, alpha_token)
    boa.env.time_travel(blocks=10)

    bravo_amount = 80 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, 40 * EIGHTEEN_DECIMALS, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address,
    )
    charlie_amount = 60 * 10 ** charlie_token.decimals()
    charlie_token.transfer(
        stability_pool, charlie_amount, sender=charlie_token_whale
    )
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, 30 * EIGHTEEN_DECIMALS, charlie_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address,
    )

    claims = [
        (alpha_token.address, bravo_token.address, 40 * EIGHTEEN_DECIMALS),
        (alpha_token.address, bravo_token.address, MAX_UINT256),
        (alpha_token.address, bravo_token.address, MAX_UINT256),
        (alpha_token.address, charlie_token.address, MAX_UINT256),
    ]
    claimed_value = teller.claimManyFromStabilityPool(
        vault_id, claims, sender=bob
    )
    assert 140 * EIGHTEEN_DECIMALS <= claimed_value
    assert claimed_value <= 140 * EIGHTEEN_DECIMALS + 10**12

    points_after = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert points_after.balancePoints == points_before.lastBalance * 10
    precision = ledger.assetDepositPoints(vault_id, alpha_token).precision
    assert points_after.lastBalance == stability_pool.getUserLootBoxShare(
        bob, alpha_token
    ) // precision
    assert 0 < points_after.lastBalance < points_before.lastBalance

    boa.env.time_travel(blocks=10)
    lootbox.updateDepositPoints(
        bob, vault_id, stability_pool, alpha_token, sender=teller.address
    )
    final_points = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert final_points.balancePoints == (
        points_after.balancePoints + points_after.lastBalance * 10
    )


def test_stability_claim_checkpoint_failure_rolls_back_batch(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    lootbox,
    ledger,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
):
    """A failed deferred checkpoint rolls shares, custody, and points back."""
    setGeneralConfig()
    vault_id = vault_book.getRegId(stability_pool)
    setAssetConfig(alpha_token, _vaultIds=[vault_id])
    setAssetConfig(bravo_token)
    setRipeRewardsConfig(True)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob, alpha_token, amount, sender=teller.address
    )
    bravo_token.transfer(stability_pool, amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, amount, bravo_token, amount, ZERO_ADDRESS, alpha_token,
        savings_green, sender=auction_house.address,
    )
    before = (
        stability_pool.userBalances(bob, alpha_token),
        stability_pool.totalBalances(alpha_token),
        stability_pool.claimableBalances(alpha_token, bravo_token),
        stability_pool.totalClaimableBalances(bravo_token),
        bravo_token.balanceOf(stability_pool),
        bravo_token.balanceOf(bob),
        ledger.userDepositPoints(bob, vault_id, alpha_token),
    )

    lootbox.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        claim_from_stability_pool(
            teller, vault_id, alpha_token, bravo_token, sender=bob
        )
    assert (
        stability_pool.userBalances(bob, alpha_token),
        stability_pool.totalBalances(alpha_token),
        stability_pool.claimableBalances(alpha_token, bravo_token),
        stability_pool.totalClaimableBalances(bravo_token),
        bravo_token.balanceOf(stability_pool),
        bravo_token.balanceOf(bob),
        ledger.userDepositPoints(bob, vault_id, alpha_token),
    ) == before


def test_stab_vault_claims_partial(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # swap
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,  # stab asset
        deposit_amount,     # stab asset amount
        bravo_token,  # liq asset
        claimable_amount,  # liq amount
        ZERO_ADDRESS,  # recipient (burn)
        alpha_token,  # green token
        savings_green,
        sender=auction_house.address
    )

    bob_new_value = stability_pool.getTotalUserValue(bob, alpha_token)
    total_new_value = stability_pool.getTotalValue(alpha_token)

    # claim!
    vault_id = vault_book.getRegId(stability_pool)
    claim_usd_value = bob_new_value // 2
    usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, claim_usd_value, sender=bob)

    # test
    _test(claim_usd_value, usd_value)
    _test(bob_new_value // 2, stability_pool.getTotalUserValue(bob, alpha_token))
    _test(total_new_value // 2, stability_pool.getTotalValue(alpha_token))

    _test(claimable_amount // 2, bravo_token.balanceOf(bob))


def test_stab_vault_claims_validation(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bob,
    alice,
    teller,
    mock_price_source,
    vault_book,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
):
    """Test validation logic for claims"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    vault_id = vault_book.getRegId(stability_pool)

    # Test claim when paused
    stability_pool.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
    stability_pool.pause(False, sender=switchboard_alpha.address)

    # Test claim with no position - should revert with "nothing claimed"
    with boa.reverts("nothing claimed"):
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)

    # Test claim with no claimable assets
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    
    with boa.reverts("nothing claimed"):
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)

    # Test claim with zero max USD value
    with boa.reverts("nothing claimed"):
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, 0, sender=bob)

    # Test unauthorized caller
    with boa.reverts("only Teller allowed"):
        stability_pool.claimManyFromStabilityPool(
            bob,
            [(alpha_token.address, bravo_token.address, 100)],
            bob,
            False,
            sender=alice,
        )


def test_stab_vault_claims_no_shares(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims when user has no shares in the stability pool"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Only Bob deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Alice tries to claim but has no shares - should revert with "nothing claimed"
    vault_id = vault_book.getRegId(stability_pool)
    with boa.reverts("nothing claimed"):
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=alice)
    assert bravo_token.balanceOf(alice) == 0


def test_stab_vault_claims_insufficient_balance(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims when contract has insufficient claimable balance"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Remove most of the claimable tokens from the contract
    bravo_token.transfer(bravo_token_whale, claimable_amount - 1, sender=stability_pool.address)

    # A custody deficit must fail closed. Paying the remaining token would burn
    # the user's full recorded claim and socialize the missing custody.
    vault_id = vault_book.getRegId(stability_pool)
    claim_before = stability_pool.claimableBalances(alpha_token, bravo_token)
    liability_before = stability_pool.totalClaimableBalances(bravo_token)
    shares_before = stability_pool.userBalances(bob, alpha_token)
    with boa.reverts("claim custody deficit"):
        claim_from_stability_pool(
            teller, vault_id, alpha_token, bravo_token, sender=bob
        )
    assert bravo_token.balanceOf(bob) == 0
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == claim_before
    assert stability_pool.totalClaimableBalances(bravo_token) == liability_before
    assert stability_pool.userBalances(bob, alpha_token) == shares_before


def test_stab_vault_claims_multiple_users(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims with multiple users in the stability pool"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Both users deposit different amounts
    bob_deposit = 100 * EIGHTEEN_DECIMALS
    alice_deposit = 50 * EIGHTEEN_DECIMALS
    
    alpha_token.transfer(stability_pool, bob_deposit, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, bob_deposit, sender=teller.address)
    
    alpha_token.transfer(stability_pool, alice_deposit, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, alice_deposit, sender=teller.address)

    # Add claimable assets
    claimable_amount = 225 * EIGHTEEN_DECIMALS  # 1.5x the total deposits
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, bob_deposit + alice_deposit, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)
    
    # Bob claims first (should get 2/3 of claimable assets)
    stability_pool.getTotalUserValue(bob, alpha_token)
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
    bob_claimed = bravo_token.balanceOf(bob)
    
    # Alice claims second (should get 1/3 of remaining claimable assets)
    stability_pool.getTotalUserValue(alice, alpha_token)
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=alice)
    alice_claimed = bravo_token.balanceOf(alice)

    # Bob should get roughly 2/3, Alice should get roughly 1/3
    total_claimed = bob_claimed + alice_claimed
    _test(claimable_amount, total_claimed)
    
    # Check proportions (allowing for small rounding differences)
    bob_ratio = bob_claimed / total_claimed
    alice_ratio = alice_claimed / total_claimed
    assert abs(bob_ratio - 2/3) < 0.01  # Within 1% of expected ratio
    assert abs(alice_ratio - 1/3) < 0.01


def test_stab_vault_claims_multiple_assets(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims with multiple different claimable assets"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add first claimable asset (bravo)
    bravo_amount = 60 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Add second claimable asset (charlie)
    charlie_amount = 90 * (10 ** charlie_token.decimals())
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, charlie_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Claim bravo tokens
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
    bravo_claimed = bravo_token.balanceOf(bob)
    _test(bravo_amount, bravo_claimed)

    # Claim charlie tokens  
    claim_from_stability_pool(teller, vault_id, alpha_token, charlie_token, sender=bob)
    charlie_claimed = charlie_token.balanceOf(bob)
    assert charlie_claimed == charlie_amount - 1
    assert stability_pool.claimableBalances(alpha_token, charlie_token) == 1

    # The last raw 6-decimal unit is worth one micro-dollar. Before the strict
    # sub-micro-dollar exit tolerance, virtual-share rounding left the user one
    # USD wei below that unit with nonzero shares, while a retry quoted zero
    # tokens and reverted `nothing claimed`.
    assert stability_pool.userBalances(bob, alpha_token) == 0
    assert stability_pool.getTotalUserValue(bob, alpha_token) == 0


def test_claim_after_effects_guard_rejection_rolls_back_second_claim(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
    ledger,
    mission_control,
    switchboard_alpha,
):
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob,
        alpha_token,
        deposit_amount,
        sender=teller.address,
    )

    bravo_amount = 50 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        deposit_amount // 2,
        bravo_token,
        bravo_amount,
        bob,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )

    charlie_amount = 50 * 10 ** charlie_token.decimals()
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        deposit_amount // 2,
        charlie_token,
        charlie_amount,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )

    mission_control.setShouldCheckLastTouch(
        True,
        sender=switchboard_alpha.address,
    )
    vault_id = vault_book.getRegId(stability_pool)
    claim_from_stability_pool(teller,
        vault_id,
        alpha_token,
        bravo_token,
        sender=bob,
    )

    before = (
        charlie_token.balanceOf(bob),
        stability_pool.getTotalUserValue(bob, alpha_token),
        ledger.lastTouch(bob),
    )
    with boa.reverts("one action per block"):
        claim_from_stability_pool(teller,
            vault_id,
            alpha_token,
            charlie_token,
            sender=bob,
        )
    after = (
        charlie_token.balanceOf(bob),
        stability_pool.getTotalUserValue(bob, alpha_token),
        ledger.lastTouch(bob),
    )
    assert after == before


def test_stab_vault_claims_tiny_amounts(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims with very small amounts"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposit
    deposit_amount = 2  # Very small amount
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add tiny claimable assets
    claimable_amount = 3  # Even smaller
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, 1, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # A directly selected dormant balance remains claimable while raw NAV remains.
    vault_id = vault_book.getRegId(stability_pool)
    usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)

    assert usd_value == 1
    assert bravo_token.balanceOf(bob) == 1
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 2
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == 1


def test_stab_vault_claims_depletion(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test that claims properly deplete user positions"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Record initial shares
    initial_shares = stability_pool.userBalances(bob, alpha_token)
    assert initial_shares > 0

    # Add claimable assets equal to deposit
    claimable_amount = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Claim everything
    vault_id = vault_book.getRegId(stability_pool)
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)

    # User should be depleted
    final_shares = stability_pool.userBalances(bob, alpha_token)
    assert final_shares == 0
    assert stability_pool.getTotalUserValue(bob, alpha_token) == 0


def test_full_claim_depletes_active_pair_and_emits_deactivation_zero_reason_one(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
    green_token,
):
    setGeneralConfig()
    setAssetConfig(bravo_token)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, amount, sender=teller.address)
    bravo_token.transfer(stability_pool, amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        amount,
        bravo_token,
        amount,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 1
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 1
    shares_before = stability_pool.userBalances(bob, alpha_token)
    vault_id = vault_book.getRegId(stability_pool)

    claimed_value = claim_from_stability_pool(
        teller,
        vault_id,
        alpha_token,
        bravo_token,
        MAX_UINT256,
        sender=bob,
    )
    assert claimed_value == amount
    events = filter_logs(teller, "ClaimAssetDeactivated")
    assert len(events) == 1
    event = events[0]
    assert event.stabAsset == alpha_token.address
    assert event.claimAsset == bravo_token.address
    assert event.balance == 0
    assert event.activeCount == 0
    assert event.reason == 1
    assert bravo_token.balanceOf(bob) == amount
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
    assert stability_pool.totalClaimableBalances(bravo_token) == 0
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 0
    assert stability_pool.getNumActiveClaimAssets(alpha_token) == 0
    assert stability_pool.claimableAssets(alpha_token, 1) == ZERO_ADDRESS
    assert stability_pool.userBalances(bob, alpha_token) == 0
    assert stability_pool.totalBalances(alpha_token) == shares_before - shares_before


def test_dust_deactivated_pair_with_residual_balance_remains_claimable(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
    green_token,
):
    """Legacy node ID kept for external evidence links.

    Live prune is a no-op: no deactivation event is emitted, the row stays
    ACTIVE, and that active row remains claimable. It does not move to the
    dormant set. Exact microscopic deactivation-and-claim coverage is in
    ``test_g10_live_eighteen_decimal_inclusive_boundary_via_one_dollar_redeem``.
    """
    setGeneralConfig()
    setAssetConfig(bravo_token)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    residual = 3 * 10**17
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob,
        alpha_token,
        deposit_amount,
        sender=teller.address,
    )
    bravo_token.transfer(stability_pool, residual, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        1,
        bravo_token,
        residual,
        bob,
        green_token,
        savings_green,
        sender=auction_house.address,
    )
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 1
    mock_price_source.setPrice(bravo_token, 10**17)
    stability_pool.pruneClaimableAssets(alpha_token, [bravo_token], sender=bob)
    assert filter_logs(stability_pool, "ClaimAssetDeactivated") == []
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 1
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == 2  # ACTIVE
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == residual

    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(stability_pool)
    claimed_value = claim_from_stability_pool(
        teller,
        vault_id,
        alpha_token,
        bravo_token,
        MAX_UINT256,
        sender=bob,
    )
    assert claimed_value == residual
    assert bravo_token.balanceOf(bob) == residual
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
    assert stability_pool.totalClaimableBalances(bravo_token) == 0
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 0


def test_stab_vault_claim_many_basic(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
    ledger,
    mission_control,
    switchboard_alpha,
):
    """Test claimManyFromStabilityPool with multiple assets"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Initial deposit
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    bravo_amount = 80 * EIGHTEEN_DECIMALS
    charlie_amount = 120 * (10 ** charlie_token.decimals())
    
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, charlie_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Create claims array
    claims = [
        (alpha_token.address, bravo_token.address, MAX_UINT256),
        (alpha_token.address, charlie_token.address, MAX_UINT256)
    ]

    mission_control.setShouldCheckLastTouch(
        True,
        sender=switchboard_alpha.address,
    )
    boa.env.time_travel(blocks=1)

    # Claim many
    vault_id = vault_book.getRegId(stability_pool)
    total_usd_value = teller.claimManyFromStabilityPool(vault_id, claims, sender=bob)

    # Check results
    _test(bravo_amount, bravo_token.balanceOf(bob))
    _test(charlie_amount, charlie_token.balanceOf(bob))
    assert total_usd_value == 200 * EIGHTEEN_DECIMALS
    assert ledger.lastTouch(bob) == boa.env.evm.patch.block_number


def test_claim_many_arb_sys_rejects_second_same_action_block(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
    mission_control,
    switchboard_alpha,
    ripe_hq_deploy,
    defaults,
    governance,
):
    arb_ledger = _replace_ledger_with_arb_source(
        ripe_hq_deploy,
        defaults,
        governance,
        5_200,
    )
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    price = EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(
        stability_pool,
        deposit_amount,
        sender=alpha_token_whale,
    )
    stability_pool.depositTokensInVault(
        bob,
        alpha_token,
        deposit_amount,
        sender=teller.address,
    )

    bravo_amount = 80 * EIGHTEEN_DECIMALS
    bravo_token.transfer(
        stability_pool,
        bravo_amount,
        sender=bravo_token_whale,
    )
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        deposit_amount // 2,
        bravo_token,
        bravo_amount,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )

    charlie_amount = 120 * 10 ** charlie_token.decimals()
    charlie_token.transfer(
        stability_pool,
        charlie_amount,
        sender=charlie_token_whale,
    )
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        deposit_amount // 2,
        charlie_token,
        charlie_amount,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )

    mission_control.setShouldCheckLastTouch(
        True,
        sender=switchboard_alpha.address,
    )
    child_identity = 5_201
    _set_claim_many_child_identity(child_identity)
    vault_id = vault_book.getRegId(stability_pool)
    first_claims = [
        (
            alpha_token.address,
            bravo_token.address,
            40 * EIGHTEEN_DECIMALS,
        ),
        (
            alpha_token.address,
            charlie_token.address,
            60 * EIGHTEEN_DECIMALS,
        ),
    ]
    assert (
        teller.claimManyFromStabilityPool(
            vault_id,
            first_claims,
            sender=bob,
        )
        == 100 * EIGHTEEN_DECIMALS
    )
    assert arb_ledger.lastTouch(bob) == child_identity

    before = (
        bravo_token.balanceOf(bob),
        charlie_token.balanceOf(bob),
        bravo_token.balanceOf(stability_pool),
        charlie_token.balanceOf(stability_pool),
        stability_pool.getTotalUserValue(bob, alpha_token),
        arb_ledger.lastTouch(bob),
    )
    boa.env.time_travel(blocks=60)
    second_claims = [
        (
            alpha_token.address,
            bravo_token.address,
            MAX_UINT256,
        ),
        (
            alpha_token.address,
            charlie_token.address,
            MAX_UINT256,
        ),
    ]
    with boa.reverts("one action per block"):
        teller.claimManyFromStabilityPool(
            vault_id,
            second_claims,
            sender=bob,
        )
    after = (
        bravo_token.balanceOf(bob),
        charlie_token.balanceOf(bob),
        bravo_token.balanceOf(stability_pool),
        charlie_token.balanceOf(stability_pool),
        stability_pool.getTotalUserValue(bob, alpha_token),
        arb_ledger.lastTouch(bob),
    )
    assert after == before
    assert arb_ledger.lastTouch(bob) == child_identity


def test_stab_vault_claim_many_empty_array(
    stability_pool,
    bob,
    teller,
    vault_book,
):
    """Test claimManyFromStabilityPool with empty claims array"""
    vault_id = vault_book.getRegId(stability_pool)
    
    # Empty claims array should revert with "nothing claimed"
    with boa.reverts("nothing claimed"):
        teller.claimManyFromStabilityPool(vault_id, [], sender=bob)


def test_stab_vault_claim_many_partial_claims(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claimManyFromStabilityPool with partial claim amounts"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Initial deposit
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    bravo_amount = 100 * EIGHTEEN_DECIMALS
    charlie_amount = 100 * (10 ** charlie_token.decimals())
    
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, charlie_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Create claims array with partial amounts
    claims = [
        (alpha_token.address, bravo_token.address, bravo_amount // 2),  # Half of bravo
        (alpha_token.address, charlie_token.address, 33 * EIGHTEEN_DECIMALS)  # Third of charlie
    ]

    # Claim many
    vault_id = vault_book.getRegId(stability_pool)
    total_usd_value = teller.claimManyFromStabilityPool(vault_id, claims, sender=bob)

    # Check results
    expected_bravo = bravo_amount // 2
    expected_charlie = 33 * (10 ** charlie_token.decimals())
    
    _test(expected_bravo, bravo_token.balanceOf(bob))
    _test(expected_charlie, charlie_token.balanceOf(bob))
    _test(total_usd_value, expected_bravo + 33 * EIGHTEEN_DECIMALS)

    # User should still have remaining value
    remaining_value = stability_pool.getTotalUserValue(bob, alpha_token)
    assert remaining_value > 0


def test_stab_vault_claim_many_mixed_valid_invalid(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claimManyFromStabilityPool with mix of valid and invalid claims"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add only bravo as claimable asset (not charlie)
    bravo_amount = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Create claims array with valid and invalid claims
    claims = [
        (alpha_token.address, bravo_token.address, bravo_amount),      # Valid claim
        (alpha_token.address, charlie_token.address, 50 * EIGHTEEN_DECIMALS),  # Invalid - no claimable charlie
        (ZERO_ADDRESS, bravo_token.address, bravo_amount),            # Invalid - zero stab asset
        (alpha_token.address, ZERO_ADDRESS, bravo_amount),            # Invalid - zero claim asset
    ]

    # Claim many - should only process valid claims
    vault_id = vault_book.getRegId(stability_pool)
    total_usd_value = teller.claimManyFromStabilityPool(vault_id, claims, sender=bob)

    # Only bravo should be claimed
    _test(bravo_amount, bravo_token.balanceOf(bob))
    assert charlie_token.balanceOf(bob) == 0
    assert total_usd_value == bravo_amount


def test_stab_vault_claim_many_max_claims(
    stability_pool,
    bob,
    teller,
    vault_book,
):
    """Test claimManyFromStabilityPool with maximum number of claims"""
    # Get the MAX_STAB_CLAIMS constant (15)
    max_claims = 15
    
    # Create exactly max number of claims (all invalid to avoid setup complexity)
    claims = [(ZERO_ADDRESS, ZERO_ADDRESS, 0) for _ in range(max_claims)]
    
    vault_id = vault_book.getRegId(stability_pool)
    
    # Should revert with "nothing claimed" since all claims are invalid
    with boa.reverts("nothing claimed"):
        teller.claimManyFromStabilityPool(vault_id, claims, sender=bob)


def test_stab_vault_claim_many_exceeds_limit(
    stability_pool,
    bob,
    teller,
    vault_book,
):
    """Test claimManyFromStabilityPool fails when exceeding maximum number of claims"""
    # Get the MAX_STAB_CLAIMS constant (15)
    max_claims = 15
    
    # Create MORE than max number of claims (this should fail at bounds check)
    claims = [(ZERO_ADDRESS, ZERO_ADDRESS, 0) for _ in range(max_claims + 1)]
    
    vault_id = vault_book.getRegId(stability_pool)
    
    # Should fail with bounds check error when trying to pass 16 claims to DynArray[StabPoolClaim, 15]
    with boa.reverts("DynArray[StabPoolClaim, 15] bounds check"):  # Generic revert since it's a compiler bounds check
        teller.claimManyFromStabilityPool(vault_id, claims, sender=bob)


def test_stab_vault_claims_event_emission(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
    _test,
):
    """Test that AssetClaimedInStabilityPool events are properly emitted"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Claim and check for event
    vault_id = vault_book.getRegId(stability_pool)
    
    usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
    log = filter_logs(teller, "AssetClaimedInStabilityPool")[0]
    assert log.user == bob
    assert log.stabAsset == alpha_token.address
    assert log.claimAsset == bravo_token.address
    _test(log.claimAmount, claimable_amount)
    _test(log.claimUsdValue, usd_value)
    assert log.claimShares != 0
    assert log.isDepleted


def test_stab_vault_claims_claimable_balance_update(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test that claimable balances are properly updated after claims"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Two users deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 300 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount * 2, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Check initial claimable balances
    initial_claimable = stability_pool.claimableBalances(alpha_token, bravo_token)
    initial_total_claimable = stability_pool.totalClaimableBalances(bravo_token)
    _test(claimable_amount, initial_claimable)
    _test(claimable_amount, initial_total_claimable)

    vault_id = vault_book.getRegId(stability_pool)

    # Bob claims half
    bob_claim_amount = claimable_amount // 2
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, bob_claim_amount, sender=bob)

    # Check balances after Bob's claim
    after_bob_claimable = stability_pool.claimableBalances(alpha_token, bravo_token)
    after_bob_total_claimable = stability_pool.totalClaimableBalances(bravo_token)
    
    expected_remaining = claimable_amount - bob_claim_amount
    _test(expected_remaining, after_bob_claimable)
    _test(expected_remaining, after_bob_total_claimable)

    # Alice claims the rest
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=alice)

    # Check balances after Alice's claim - should be near zero
    final_claimable = stability_pool.claimableBalances(alpha_token, bravo_token)
    final_total_claimable = stability_pool.totalClaimableBalances(bravo_token)
    
    assert final_claimable <= 1  # Allow for rounding
    assert final_total_claimable <= 1


def test_stab_vault_claims_config_disabled(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims when different configuration flags are disabled"""
    # Setup with claims enabled first
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup deposit and claimable assets
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Test 1: Disable general claims config
    setGeneralConfig(_canClaimInStabPool=False)
    with boa.reverts("nothing claimed"):
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)

    # Re-enable general config
    setGeneralConfig()

    # Test 2: Disable asset-specific claims config
    setAssetConfig(bravo_token, _canClaimInStabPool=False)
    with boa.reverts("nothing claimed"):
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)

    # Re-enable asset config for final test
    setAssetConfig(bravo_token)
    
    # Verify claims work again when config is restored
    usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
    assert usd_value > 0


def test_stab_vault_claims_price_oracle_zero(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims when price oracle returns 0 for claim asset"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup deposit and claimable assets
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Set price of claim asset to 0 (simulating oracle failure or delisted asset)
    mock_price_source.setPrice(bravo_token, 0)

    vault_id = vault_book.getRegId(stability_pool)
    
    # Should raise an exception due to price oracle returning 0 with _shouldRaise=True
    with boa.reverts("has price config, no price"):
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)


def test_stab_vault_claims_max_usd_value_limit(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims with specific maxUsdValue limits (not MAX_UINT256)"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Claim with specific USD limit (less than total available)
    max_claim_usd = 50 * EIGHTEEN_DECIMALS
    usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, max_claim_usd, sender=bob)
    
    # Should respect the USD limit
    _test(max_claim_usd, usd_value)
    _test(max_claim_usd, bravo_token.balanceOf(bob))  # 1:1 price ratio
    
    # User should still have remaining value in the pool
    remaining_value = stability_pool.getTotalUserValue(bob, alpha_token)
    assert remaining_value > 0


def test_stab_vault_claims_asset_registry_removal(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test that claimable assets are properly removed from registry when depleted"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Setup
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add two different claimable assets
    bravo_amount = 80 * EIGHTEEN_DECIMALS
    charlie_amount = 120 * (10 ** charlie_token.decimals())
    
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, charlie_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Check initial registry state
    assert stability_pool.numClaimableAssets(alpha_token) == 3  # 0 index not used, so 3 total (1 bravo, 2 charlie)
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 1
    assert stability_pool.indexOfClaimableAsset(alpha_token, charlie_token) == 2
    assert stability_pool.claimableAssets(alpha_token, 1) == bravo_token.address
    assert stability_pool.claimableAssets(alpha_token, 2) == charlie_token.address

    vault_id = vault_book.getRegId(stability_pool)

    # Fully deplete bravo (should remove from registry)
    bravo_usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
    _test(bravo_amount, bravo_usd_value)

    # Check that bravo is removed from registry
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == 0
    assert stability_pool.indexOfClaimableAsset(alpha_token, bravo_token) == 0  # Removed
    
    # Charlie should still be in registry and moved to index 1
    assert stability_pool.numClaimableAssets(alpha_token) == 2  # One less
    assert stability_pool.indexOfClaimableAsset(alpha_token, charlie_token) == 1  # Moved to fill gap
    assert stability_pool.claimableAssets(alpha_token, 1) == charlie_token.address

    # Partially claim charlie (should NOT remove from registry)
    partial_charlie_usd = 60 * EIGHTEEN_DECIMALS
    claim_from_stability_pool(teller, vault_id, alpha_token, charlie_token, partial_charlie_usd, sender=bob)
    
    # Charlie should still be in registry
    assert stability_pool.claimableBalances(alpha_token, charlie_token) > 0
    assert stability_pool.indexOfClaimableAsset(alpha_token, charlie_token) == 1
    assert stability_pool.numClaimableAssets(alpha_token) == 2


def test_stab_vault_claims_precision_edge_cases(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims with precision/rounding edge cases"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup with odd amounts that might cause rounding issues
    deposit_amount1 = 333333333333333333  # ~0.33 tokens
    deposit_amount2 = 666666666666666667  # ~0.67 tokens
    
    alpha_token.transfer(stability_pool, deposit_amount1, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount1, sender=teller.address)
    
    alpha_token.transfer(stability_pool, deposit_amount2, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount2, sender=teller.address)

    # Add claimable assets with odd amount
    claimable_amount = 999999999999999999  # Just under 1 token
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount1 + deposit_amount2, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Claim with both users and ensure total is preserved
    bob_initial_value = stability_pool.getTotalUserValue(bob, alpha_token)
    alice_initial_value = stability_pool.getTotalUserValue(alice, alpha_token)
    bob_initial_value + alice_initial_value

    bob_usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
    alice_usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=alice)

    # Check that total claimed roughly equals claimable amount (within rounding tolerance)
    total_claimed = bob_usd_value + alice_usd_value
    assert abs(total_claimed - claimable_amount) <= 2  # Allow for 2 wei rounding difference

    # Check token balances
    bob_tokens = bravo_token.balanceOf(bob)
    alice_tokens = bravo_token.balanceOf(alice)
    total_tokens = bob_tokens + alice_tokens
    assert abs(total_tokens - claimable_amount) <= 2


def test_stab_vault_claims_multiple_stability_assets(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims when there are multiple stability pool assets"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Setup with both alpha and charlie as stability pool assets
    alpha_deposit = 100 * EIGHTEEN_DECIMALS
    charlie_deposit = 50 * (10 ** charlie_token.decimals())
    
    # Bob deposits alpha
    alpha_token.transfer(stability_pool, alpha_deposit, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, alpha_deposit, sender=teller.address)
    
    # Alice deposits charlie
    charlie_token.transfer(stability_pool, charlie_deposit, sender=charlie_token_whale)
    stability_pool.depositTokensInVault(alice, charlie_token, charlie_deposit, sender=teller.address)

    # Add bravo as claimable for both stability assets
    bravo_amount_for_alpha = 80 * EIGHTEEN_DECIMALS
    bravo_amount_for_charlie = 40 * EIGHTEEN_DECIMALS
    
    bravo_token.transfer(stability_pool, bravo_amount_for_alpha, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, alpha_deposit, bravo_token, bravo_amount_for_alpha,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    bravo_token.transfer(stability_pool, bravo_amount_for_charlie, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        charlie_token, charlie_deposit, bravo_token, bravo_amount_for_charlie,
        ZERO_ADDRESS, charlie_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Bob claims bravo from his alpha position
    bob_usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
    _test(bravo_amount_for_alpha, bob_usd_value)
    _test(bravo_amount_for_alpha, bravo_token.balanceOf(bob))

    # Alice claims bravo from her charlie position
    alice_usd_value = claim_from_stability_pool(teller, vault_id, charlie_token, bravo_token, sender=alice)
    _test(bravo_amount_for_charlie, alice_usd_value)
    _test(bravo_amount_for_charlie, bravo_token.balanceOf(alice))

    # Check that both users' stability positions are depleted
    assert stability_pool.getTotalUserValue(bob, alpha_token) <= 1
    assert stability_pool.getTotalUserValue(alice, charlie_token) <= 1


def test_stab_vault_claims_concurrent_claims_edge_case(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test edge case where claimable balance changes between calculation and execution"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup two users with equal deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 200 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount * 2, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Simulate scenario where available balance is less than recorded balance
    # (e.g. some tokens were transferred out externally)
    tokens_to_remove = claimable_amount // 4  # Remove 25%
    bravo_token.transfer(bravo_token_whale, tokens_to_remove, sender=stability_pool.address)

    vault_id = vault_book.getRegId(stability_pool)

    # Neither claimant may consume a partial aggregate reserve. Both attempts
    # revert atomically until custody again covers the recorded liability.
    claim_before = stability_pool.claimableBalances(alpha_token, bravo_token)
    liability_before = stability_pool.totalClaimableBalances(bravo_token)
    shares_before = {
        bob: stability_pool.userBalances(bob, alpha_token),
        alice: stability_pool.userBalances(alice, alpha_token),
    }
    for user in (bob, alice):
        with boa.reverts("claim custody deficit"):
            claim_from_stability_pool(
                teller, vault_id, alpha_token, bravo_token, sender=user
            )
    assert bravo_token.balanceOf(bob) == 0
    assert bravo_token.balanceOf(alice) == 0
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == claim_before
    assert stability_pool.totalClaimableBalances(bravo_token) == liability_before
    assert stability_pool.userBalances(bob, alpha_token) == shares_before[bob]
    assert stability_pool.userBalances(alice, alpha_token) == shares_before[alice]


def test_stab_vault_claims_claim_many_over_limit(
    stability_pool,
    bob,
    teller,
    vault_book,
):
    """Test claimManyFromStabilityPool with more than MAX_STAB_CLAIMS"""
    vault_id = vault_book.getRegId(stability_pool)
    
    # Try to create more than max claims (16 claims when max is 15)
    max_claims = 15
    try:
        # This should fail at compile/runtime due to DynArray size limit
        claims = [(ZERO_ADDRESS, ZERO_ADDRESS, 0) for _ in range(max_claims + 1)]
        teller.claimManyFromStabilityPool(vault_id, claims, sender=bob)
        assert False, "Should have failed due to exceeding max claims"
    except Exception:
        # Expected to fail
        pass


def test_stab_vault_claims_zero_total_shares_edge_case(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    """Test claims in edge case where total shares is very small"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup with minimal deposit
    deposit_amount = 1  # 1 wei
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add much larger claimable amount
    claimable_amount = EIGHTEEN_DECIMALS  # 1 full token
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)
    
    # Should be able to claim despite very small shares
    usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
    assert usd_value > 0
    assert bravo_token.balanceOf(bob) > 0


def test_stab_vault_claims_with_delegation_permission(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
    setUserDelegation,
):
    """Test that a delegate with permission can claim from stability pool for another user"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Bob deposits into stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Before delegation, Alice cannot claim for Bob
    with boa.reverts("cannot claim for user"):
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, MAX_UINT256, bob, sender=alice)

    # Bob delegates claim permission to Alice
    setUserDelegation(bob, alice, _canClaimFromStabPool=True)

    # Now Alice can claim for Bob
    usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, MAX_UINT256, bob, sender=alice)
    _test(claimable_amount, usd_value)
    
    # Verify the tokens went to Bob (not Alice)
    _test(claimable_amount, bravo_token.balanceOf(bob))
    assert bravo_token.balanceOf(alice) == 0

    # Verify Bob's position is depleted
    assert stability_pool.getTotalUserValue(bob, alpha_token) <= 1


def test_stab_vault_claims_without_delegation_permission(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
    setUserDelegation,
):
    """Test that users without delegation permission cannot claim for others"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Bob deposits into stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Alice has no delegation permission - should fail
    with boa.reverts("cannot claim for user"):
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, MAX_UINT256, bob, sender=alice)

    # Bob gives Alice delegation but NOT for claiming from stability pool
    setUserDelegation(
        bob, 
        alice, 
        _canWithdraw=True,
        _canBorrow=True,
        _canClaimFromStabPool=False,  # Explicitly NO permission for stability pool claims
        _canClaimLoot=True
    )

    # Alice still cannot claim for Bob (no stability pool claim permission)
    with boa.reverts("cannot claim for user"):
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, MAX_UINT256, bob, sender=alice)

    # Bob gives Sally full delegation including stability pool claims
    setUserDelegation(bob, sally, _canClaimFromStabPool=True)

    # Sally can claim for Bob
    usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, MAX_UINT256, bob, sender=sally)
    _test(claimable_amount, usd_value)
    
    # Verify the tokens went to Bob (not Sally)
    _test(claimable_amount, bravo_token.balanceOf(bob))
    assert bravo_token.balanceOf(sally) == 0
    
    # Alice still has no tokens
    assert bravo_token.balanceOf(alice) == 0

    # Test claim many with delegation
    # First setup another claimable asset
    deposit_amount2 = 50 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount2, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount2, sender=teller.address)
    
    charlie_amount = 75 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, charlie_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount2, bravo_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Sally can use claimManyFromStabilityPool for Alice with delegation
    setUserDelegation(alice, sally, _canClaimFromStabPool=True)
    
    claims = [(alpha_token.address, bravo_token.address, MAX_UINT256)]
    total_usd_value = teller.claimManyFromStabilityPool(vault_id, claims, alice, sender=sally)
    
    _test(charlie_amount, total_usd_value)
    _test(charlie_amount, bravo_token.balanceOf(alice))


##########################
# Stability Pool Rewards #
##########################


@pytest.fixture(scope="module")
def setupStabPoolClaimsRewards(mission_control, setAssetConfig, setGeneralConfig, setRipeRewardsConfig, switchboard_alpha, ripe_token):
    def setupStabPoolClaimsRewards(
        _ripePerDollar = 1 * EIGHTEEN_DECIMALS,
        _minLockDuration = 0,
        _maxLockDuration = 1000,
        _autoStakeDurationRatio = 0,
    ):
        setGeneralConfig()

        # Set RipeRewardsConfig with stab pool rewards
        setRipeRewardsConfig(
            _stabPoolRipePerDollarClaimed=_ripePerDollar,
            _autoStakeDurationRatio=_autoStakeDurationRatio,
        )

        # setup ripe gov vault
        lock_terms = (
            _minLockDuration,
            _maxLockDuration,
            100_00,
            False,
            0,
        )
        mission_control.setRipeGovVaultConfig(
            ripe_token, 
            100_00,
            False,
            lock_terms, 
            sender=switchboard_alpha.address
        )
        setAssetConfig(ripe_token, _vaultIds=[2])

    yield setupStabPoolClaimsRewards


def test_stability_claim_zero_share_ripe_reward_rolls_back_and_can_retry(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    whale,
    ledger,
    setAssetConfig,
    setRipeRewardsConfig,
    setupStabPoolClaimsRewards,
    cleanCoreRipeGovFixture,
):
    """AUD-024: reward mint and Ledger debit revert with the failed deposit."""
    setupStabPoolClaimsRewards(_ripePerDollar=1)
    setAssetConfig(bravo_token)
    finite_limit = 10 ** 40
    setAssetConfig(
        ripe_token,
        _vaultIds=[2],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
        _perUserDepositLimit=finite_limit,
        _globalDepositLimit=finite_limit,
    )
    core = cleanCoreRipeGovFixture()
    clean_vault = core["vault"]
    core_id = core["vault_id"]

    price = EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)
    deposit_amount = EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob, alpha_token, deposit_amount, sender=teller.address
    )
    claimable_amount = EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        deposit_amount,
        bravo_token,
        claimable_amount,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )
    vault_id = vault_book.getRegId(stability_pool)
    ripe_token.transfer(clean_vault, 10 ** 8, sender=whale)

    supply_before = ripe_token.totalSupply()
    rewards_available_before = ledger.ripeAvailForRewards()
    claimable_before = stability_pool.claimableBalances(alpha_token, bravo_token)
    total_claimable_before = stability_pool.totalClaimableBalances(bravo_token)
    stability_shares_before = stability_pool.userBalances(bob, alpha_token)
    stability_balance_before = alpha_token.balanceOf(stability_pool)
    claim_asset_custody_before = bravo_token.balanceOf(stability_pool)
    allowance_before = ripe_token.allowance(stability_pool, teller)
    gov_shares_before = clean_vault.userBalances(bob, ripe_token)
    ledger_data_before = ledger.getDepositLedgerData(bob, core_id)
    source_ledger_before = ledger.getDepositLedgerData(bob, vault_id)
    core_user_points_before = ledger.userDepositPoints(bob, core_id, ripe_token)
    core_asset_points_before = ledger.assetDepositPoints(core_id, ripe_token)
    source_user_points_before = ledger.userDepositPoints(bob, vault_id, alpha_token)
    source_asset_points_before = ledger.assetDepositPoints(vault_id, alpha_token)
    global_points_before = ledger.globalDepositPoints()
    ripe_rewards_before = ledger.ripeRewards()

    with pytest.raises(BoaError) as exc_info:
        claim_from_stability_pool(
            teller, vault_id, alpha_token, bravo_token, sender=bob
        )
    assert_reverted_call(exc_info.value, "cannot receive 0 shares", teller)

    assert ripe_token.totalSupply() == supply_before
    assert ledger.ripeAvailForRewards() == rewards_available_before
    assert stability_pool.claimableBalances(
        alpha_token, bravo_token
    ) == claimable_before
    assert stability_pool.totalClaimableBalances(bravo_token) == total_claimable_before
    assert stability_pool.userBalances(bob, alpha_token) == stability_shares_before
    assert alpha_token.balanceOf(stability_pool) == stability_balance_before
    assert bravo_token.balanceOf(stability_pool) == claim_asset_custody_before
    assert ripe_token.allowance(stability_pool, teller) == allowance_before
    assert clean_vault.userBalances(bob, ripe_token) == gov_shares_before
    assert ledger.getDepositLedgerData(bob, core_id) == ledger_data_before
    assert ledger.getDepositLedgerData(bob, vault_id) == source_ledger_before
    assert ledger.userDepositPoints(bob, core_id, ripe_token) == core_user_points_before
    assert ledger.assetDepositPoints(core_id, ripe_token) == core_asset_points_before
    assert ledger.userDepositPoints(
        bob, vault_id, alpha_token
    ) == source_user_points_before
    assert ledger.assetDepositPoints(
        vault_id, alpha_token
    ) == source_asset_points_before
    assert ledger.globalDepositPoints() == global_points_before
    assert ledger.ripeRewards() == ripe_rewards_before

    setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=2)
    assert claim_from_stability_pool(
        teller, vault_id, alpha_token, bravo_token, sender=bob
    ) == EIGHTEEN_DECIMALS
    assert clean_vault.userBalances(bob, ripe_token) == 1


def test_stab_vault_claim_rewards_basic(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    ledger,
    _test,
    setAssetConfig,
    setupStabPoolClaimsRewards,
):
    """Test basic Ripe rewards functionality when claiming from stability pool"""
    # Set up stability pool claim rewards configuration.
    # NOTE: the reward lock is derived by MissionControl._getLockDuration from
    # (maxLockDuration - minLockDuration) * autoStakeDurationRatio. This setup
    # leaves autoStakeDurationRatio at 0, so rewards land unlocked; the exact
    # lock behavior is proven by the WP8 tests at the end of this file.
    setupStabPoolClaimsRewards(
        _ripePerDollar = EIGHTEEN_DECIMALS // 10,  # 0.1 Ripe per dollar
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record Bob's initial balance in gov vault
    initial_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Claim from stability pool
    vault_id = vault_book.getRegId(stability_pool)
    claim_usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)

    # Verify claim worked
    _test(claimable_amount, claim_usd_value)
    _test(claimable_amount, bravo_token.balanceOf(bob))

    # Calculate expected Ripe rewards: 150 USD * 0.1 = 15 Ripe
    expected_ripe_rewards = claimable_amount * EIGHTEEN_DECIMALS // 10 // EIGHTEEN_DECIMALS
    
    # Verify Bob received Ripe rewards in gov vault
    final_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    actual_ripe_rewards = final_gov_balance - initial_gov_balance
    _test(expected_ripe_rewards, actual_ripe_rewards)

    # The reward creates a gov-vault position. It is NOT locked under this
    # configuration -- autoStakeDurationRatio and minLockDuration are both 0,
    # so MissionControl._getLockDuration returns 0. Asserted explicitly so the
    # test cannot be read as proving a lock. Lock behavior is proven by the WP8
    # tests at the end of this file.
    assert ripe_gov_vault.userBalances(bob, ripe_token) > 0
    assert ripe_gov_vault.userGovData(bob, ripe_token).unlock <= (
        boa.env.evm.patch.block_number
    )


def test_stab_vault_claim_rewards_different_rates(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    mission_control,
    switchboard_alpha,
    ripe_token,
    ripe_gov_vault,
    _test,
    setAssetConfig,
    setupStabPoolClaimsRewards,
    setRipeRewardsConfig,
):
    """Test Ripe rewards with different reward rates"""
    # Test 1: High reward rate (1 Ripe per dollar)
    setupStabPoolClaimsRewards(
        _ripePerDollar = EIGHTEEN_DECIMALS,  # 1 Ripe per dollar
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup for Bob
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 50 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    initial_bob_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    vault_id = vault_book.getRegId(stability_pool)
    claim_usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)

    final_bob_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    bob_rewards = final_bob_balance - initial_bob_balance
    expected_bob_rewards = claim_usd_value  # 1:1 ratio
    _test(expected_bob_rewards, bob_rewards)

    # Test 2: Low reward rate (0.01 Ripe per dollar)
    setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=EIGHTEEN_DECIMALS // 100)

    # Setup for Alice
    alpha_token.transfer(stability_pool, deposit_amount // 2, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount // 2, sender=teller.address)

    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    initial_alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    alice_claim_usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=alice)

    final_alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    alice_rewards = final_alice_balance - initial_alice_balance
    expected_alice_rewards = alice_claim_usd_value // 100  # 0.01 ratio
    _test(expected_alice_rewards, alice_rewards)

    # Bob should get 100x more rewards per dollar than Alice due to config change
    # Bob: 1 Ripe per dollar, Alice: 0.01 Ripe per dollar
    assert bob_rewards > 0, "Bob should have received rewards"
    assert alice_rewards > 0, "Alice should have received rewards"
    
    bob_rate = bob_rewards / claim_usd_value
    alice_rate = alice_rewards / alice_claim_usd_value
    actual_ratio = bob_rate / alice_rate
    
    # Bob gets 100x more per dollar (1.0 vs 0.01)
    _test(100, actual_ratio)


def test_stab_vault_claim_rewards_zero_config(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    setAssetConfig,
    setupStabPoolClaimsRewards,
):
    """Test that no rewards are given when reward rate is zero"""
    # Set up rewards configuration with zero rate
    setupStabPoolClaimsRewards(
        _ripePerDollar = 0,  # 0 Ripe per dollar (no rewards)
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial gov vault balance
    initial_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Claim from stability pool
    vault_id = vault_book.getRegId(stability_pool)
    claim_usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)

    # Verify claim worked but no rewards given
    assert claim_usd_value > 0
    final_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    assert final_gov_balance == initial_gov_balance  # No change in gov vault balance


def test_stab_vault_claim_rewards_many_claims(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    _test,
    setAssetConfig,
    setupStabPoolClaimsRewards,
):
    """Test Ripe rewards with claimManyFromStabilityPool"""
    # Set up rewards configuration
    setupStabPoolClaimsRewards(
        _ripePerDollar = EIGHTEEN_DECIMALS // 5,  # 0.2 Ripe per dollar
    )
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add multiple claimable assets
    bravo_amount = 80 * EIGHTEEN_DECIMALS  # 80 tokens with 18 decimals
    charlie_amount = 120 * (10 ** charlie_token.decimals())  # 120 tokens with 6 decimals
    
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, charlie_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial gov vault balance
    initial_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Create claims array
    claims = [
        (alpha_token.address, bravo_token.address, MAX_UINT256),
        (alpha_token.address, charlie_token.address, MAX_UINT256)
    ]

    # Claim many
    vault_id = vault_book.getRegId(stability_pool)
    total_usd_value = teller.claimManyFromStabilityPool(vault_id, claims, sender=bob)

    # Verify total claim value
    # Since both tokens are priced at $1: 80 tokens + 120 tokens = $200 USD value
    expected_total_usd_value = 200 * EIGHTEEN_DECIMALS
    _test(expected_total_usd_value, total_usd_value)

    # Calculate expected total Ripe rewards: $200 * 0.2 = 40 Ripe
    expected_total_ripe_rewards = total_usd_value // 5  # 0.2 Ripe per dollar
    
    # Verify Bob received the claimed tokens
    _test(bravo_amount, bravo_token.balanceOf(bob))
    _test(charlie_amount, charlie_token.balanceOf(bob))
    
    # Verify Bob received total Ripe rewards in gov vault
    final_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    actual_ripe_rewards = final_gov_balance - initial_gov_balance
    _test(expected_total_ripe_rewards, actual_ripe_rewards)


def test_stab_vault_claim_rewards_insufficient_ripe(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    ledger,
    setAssetConfig,
    setupStabPoolClaimsRewards,
    switchboard_alpha,
):
    """Test rewards are limited by available Ripe in ledger"""
    # Set up high rewards configuration
    setupStabPoolClaimsRewards(
        _ripePerDollar = 10 * EIGHTEEN_DECIMALS,  # 10 Ripe per dollar (very high)
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 50 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Set limited Ripe available for rewards (less than what would be needed)
    theoretical_rewards = claimable_amount * 10  # 50 * 10 = 500 Ripe demanded
    limited_ripe_available = 100 * EIGHTEEN_DECIMALS  # Only 100 Ripe available
    ledger.setRipeAvailForRewards(limited_ripe_available, sender=switchboard_alpha.address)
    
    # Verify the limit was set correctly
    ripe_available = ledger.ripeAvailForRewards()
    assert ripe_available == limited_ripe_available, "Ledger should have limited Ripe available"
    
    expected_actual_rewards = min(theoretical_rewards, ripe_available)

    # Record the exact canonical reward state before the real claim path.
    initial_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    initial_ripe_supply = ripe_token.totalSupply()
    initial_reward_budget = ledger.ripeAvailForRewards()

    # Claim from stability pool
    vault_id = vault_book.getRegId(stability_pool)
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)

    # Verify rewards are limited by available amount
    final_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    actual_rewards = final_gov_balance - initial_gov_balance
    
    # Should be limited to available Ripe (100 Ripe instead of 500 Ripe demanded)
    assert actual_rewards <= expected_actual_rewards
    assert actual_rewards == min(theoretical_rewards, ripe_available)
    assert actual_rewards == limited_ripe_available, "Should receive exactly the limited amount available"
    assert ripe_token.totalSupply() == initial_ripe_supply + limited_ripe_available
    assert ledger.ripeAvailForRewards() == initial_reward_budget - limited_ripe_available


def test_lootbox_emission_and_stability_claim_compete_for_one_ledger_budget(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    ledger,
    lootbox,
    setAssetConfig,
    setRipeRewardsConfig,
    setupStabPoolClaimsRewards,
    switchboard_alpha,
):
    reward_rate = 10 * EIGHTEEN_DECIMALS
    setupStabPoolClaimsRewards(_ripePerDollar=reward_rate)
    setRipeRewardsConfig(
        True,
        reward_rate,
        100_00,
        0,
        0,
        0,
        _stabPoolRipePerDollarClaimed=reward_rate,
    )
    setAssetConfig(bravo_token)
    price = EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    shared_budget = 150 * EIGHTEEN_DECIMALS
    ledger.setRipeAvailForRewards(shared_budget, sender=switchboard_alpha.address)
    lootbox.updateRipeRewards(sender=teller.address)
    boa.env.time_travel(blocks=5)
    emitted = lootbox.updateRipeRewards(sender=teller.address)
    assert emitted.newRipeRewards == 50 * EIGHTEEN_DECIMALS
    assert ledger.ripeAvailForRewards() == 100 * EIGHTEEN_DECIMALS

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob,
        alpha_token,
        deposit_amount,
        sender=teller.address,
    )
    claimable_amount = 50 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        deposit_amount,
        bravo_token,
        claimable_amount,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )

    initial_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    initial_ripe_supply = ripe_token.totalSupply()
    initial_reward_budget = ledger.ripeAvailForRewards()
    vault_id = vault_book.getRegId(stability_pool)
    claim_from_stability_pool(teller,
        vault_id,
        alpha_token,
        bravo_token,
        sender=bob,
    )
    claimed_reward = (
        ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) - initial_balance
    )
    assert claimed_reward == 100 * EIGHTEEN_DECIMALS
    assert ripe_token.totalSupply() == initial_ripe_supply + claimed_reward
    assert ledger.ripeAvailForRewards() == initial_reward_budget - claimed_reward
    assert ledger.ripeAvailForRewards() == 0


def test_stab_vault_claim_rewards_partial_claims(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    _test,
    setAssetConfig,
    setupStabPoolClaimsRewards,
):
    """Test Ripe rewards scale correctly with partial claims"""
    # Set up rewards configuration
    setupStabPoolClaimsRewards(
        _ripePerDollar = EIGHTEEN_DECIMALS // 4,  # 0.25 Ripe per dollar
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # First partial claim (25% of total)
    partial_claim_amount = 25 * EIGHTEEN_DECIMALS
    initial_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    
    claim_usd_value_1 = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, partial_claim_amount, sender=bob)
    
    mid_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    rewards_1 = mid_gov_balance - initial_gov_balance
    expected_rewards_1 = claim_usd_value_1 // 4  # 0.25 ratio
    _test(expected_rewards_1, rewards_1)

    # Second partial claim (remaining 75%)
    claim_usd_value_2 = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
    
    final_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    rewards_2 = final_gov_balance - mid_gov_balance
    expected_rewards_2 = claim_usd_value_2 // 4  # 0.25 ratio
    _test(expected_rewards_2, rewards_2)

    # Total rewards should equal what we'd get from claiming everything at once
    total_rewards = rewards_1 + rewards_2
    total_claim_value = claim_usd_value_1 + claim_usd_value_2
    expected_total_rewards = total_claim_value // 4
    _test(expected_total_rewards, total_rewards)


def test_stab_vault_claim_rewards_config_changes(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    mission_control,
    switchboard_alpha,
    ripe_token,
    ripe_gov_vault,
    _test,
    setAssetConfig,
    setupStabPoolClaimsRewards,
    setRipeRewardsConfig,
):
    """Test that reward configuration changes take effect immediately"""
    # Initial rewards configuration
    setupStabPoolClaimsRewards(
        _ripePerDollar = EIGHTEEN_DECIMALS // 10,  # 0.1 Ripe per dollar
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup for both users
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    
    # Bob setup
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    
    # Alice setup  
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(alice, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets for both
    claimable_amount = 50 * EIGHTEEN_DECIMALS
    
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Bob claims with initial config
    initial_bob_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    bob_claim_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
    mid_bob_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    bob_rewards = mid_bob_balance - initial_bob_balance
    expected_bob_rewards = bob_claim_value // 10  # 0.1 ratio
    _test(expected_bob_rewards, bob_rewards)

    # Change rewards configuration
    setRipeRewardsConfig(_stabPoolRipePerDollarClaimed=EIGHTEEN_DECIMALS // 2)  # 0.5 Ripe per dollar (higher rate)

    # Alice claims with new config
    initial_alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    alice_claim_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=alice)
    final_alice_balance = ripe_gov_vault.getTotalAmountForUser(alice, ripe_token)
    alice_rewards = final_alice_balance - initial_alice_balance
    expected_alice_rewards = alice_claim_value // 2  # 0.5 ratio (new config)
    _test(expected_alice_rewards, alice_rewards)

    # Alice should get 5x more rewards per dollar than Bob due to config change
    # Bob: 0.1 Ripe per dollar, Alice: 0.5 Ripe per dollar
    assert bob_claim_value > 0, "Bob should have claimed value"
    assert alice_claim_value > 0, "Alice should have claimed value"
    assert bob_rewards > 0, "Bob should have received rewards"
    assert alice_rewards > 0, "Alice should have received rewards"
    
    bob_rate = bob_rewards / bob_claim_value
    alice_rate = alice_rewards / alice_claim_value
    actual_ratio = alice_rate / bob_rate
    
    # Alice gets 5x more per dollar (0.5 vs 0.1)
    _test(5, actual_ratio)


def test_stab_vault_claim_rewards_integration(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    _test,
    setAssetConfig,
    setupStabPoolClaimsRewards,
):
    """Integration test for rewards: the complete flow from claim to gov-vault deposit.

    This configuration leaves autoStakeDurationRatio and minLockDuration at 0,
    so the reward lands UNLOCKED. The exact lock behavior is covered by the WP8
    tests at the end of this file; this one covers routing and amounts.
    """
    # Set up moderate rewards configuration
    setupStabPoolClaimsRewards(
        _ripePerDollar = EIGHTEEN_DECIMALS // 2,  # 0.5 Ripe per dollar
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial state
    initial_ripe_balance = ripe_token.balanceOf(bob)
    initial_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    initial_gov_shares = ripe_gov_vault.userBalances(bob, ripe_token)
    initial_bravo_balance = bravo_token.balanceOf(bob)

    # Verify Bob initially has no Ripe or gov vault position
    assert initial_ripe_balance == 0
    assert initial_gov_balance == 0
    assert initial_gov_shares == 0
    assert initial_bravo_balance == 0

    # Claim from stability pool
    vault_id = vault_book.getRegId(stability_pool)
    claim_usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)

    # Verify the claim itself worked
    _test(claimable_amount, claim_usd_value)
    _test(claimable_amount, bravo_token.balanceOf(bob))

    # Verify rewards were processed correctly
    expected_ripe_rewards = claim_usd_value // 2  # 0.5 ratio
    final_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    final_gov_shares = ripe_gov_vault.userBalances(bob, ripe_token)
    final_ripe_balance = ripe_token.balanceOf(bob)

    # Bob should have received rewards in the gov vault, not as liquid tokens
    _test(expected_ripe_rewards, final_gov_balance)
    assert final_gov_shares > 0  # Bob should have shares in gov vault
    assert final_ripe_balance == 0  # Bob should not have liquid Ripe tokens

    # The reward is routed into the gov vault rather than paid out liquid.
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) > initial_gov_balance
    # ... and it is explicitly NOT locked under this configuration.
    assert ripe_gov_vault.userGovData(bob, ripe_token).unlock <= (
        boa.env.evm.patch.block_number
    )


def test_stab_vault_claim_rewards_no_ripe_available(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    ledger,
    setAssetConfig,
    setupStabPoolClaimsRewards,
    switchboard_alpha,
):
    """Test that no rewards are given when no Ripe is available in ledger"""
    # Set up high rewards configuration
    setupStabPoolClaimsRewards(
        _ripePerDollar = 5 * EIGHTEEN_DECIMALS,  # 5 Ripe per dollar (very high rate)
    )
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    # Setup
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    claimable_amount = 50 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Set NO Ripe available for rewards
    ledger.setRipeAvailForRewards(0, sender=switchboard_alpha.address)
    
    # Verify no Ripe is available
    ripe_available = ledger.ripeAvailForRewards()
    assert ripe_available == 0, "No Ripe should be available for rewards"

    # Record initial balance
    initial_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Claim from stability pool
    vault_id = vault_book.getRegId(stability_pool)
    claim_usd_value = claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)

    # Verify claim worked but no rewards given
    assert claim_usd_value > 0, "Claim should have worked"
    final_gov_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    actual_rewards = final_gov_balance - initial_gov_balance
    
    # Should receive no rewards when no Ripe is available
    assert actual_rewards == 0, "User should receive no rewards when no Ripe available"
    assert final_gov_balance == initial_gov_balance, "Gov vault balance should be unchanged"


#############################
# Auto-Deposit Claims Tests #
#############################


def test_stab_vault_claims_auto_deposit_basic(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    simple_erc20_vault,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test basic auto-deposit functionality when claiming from stability pool"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balances
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)
    initial_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    vault_id = vault_book.getRegId(stability_pool)

    # Claim with auto-deposit enabled
    usd_value = claim_from_stability_pool(teller,
        vault_id, alpha_token, bravo_token, MAX_UINT256, bob, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify claim worked
    _test(claimable_amount, usd_value)

    # Verify tokens were auto-deposited (not sent directly to Bob)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    final_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    assert final_bob_bravo_balance == initial_bob_bravo_balance  # No direct token transfer
    _test(claimable_amount, final_bob_vault_balance - initial_bob_vault_balance)  # Auto-deposited

    # Verify Bob's stability pool position is depleted
    assert stability_pool.getTotalUserValue(bob, alpha_token) <= 1


def test_stab_claim_dynamic_zero_share_autodeposit_reverts_without_fallback(
    stability_pool,
    rebase_erc20_vault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ledger,
    governance,
    setGeneralConfig,
    setAssetConfig,
):
    """AUD-024: failed dynamic auto-deposit does not fall back to transfer."""
    setGeneralConfig()
    setAssetConfig(
        bravo_token,
        _vaultIds=[4],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    deposit_amount = EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob, alpha_token, deposit_amount, sender=teller.address
    )
    claimable_amount = EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        deposit_amount,
        bravo_token,
        claimable_amount,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )

    donation = claimable_amount * 10 ** 8
    bravo_token.mint(bravo_token_whale, donation, sender=governance.address)
    bravo_token.transfer(rebase_erc20_vault, donation, sender=bravo_token_whale)
    assert rebase_erc20_vault.amountToShares(
        bravo_token, claimable_amount, False
    ) == 0

    pool_id = vault_book.getRegId(stability_pool)
    user_wallet_before = bravo_token.balanceOf(bob)
    pool_claimable_before = stability_pool.claimableBalances(
        alpha_token, bravo_token
    )
    total_claimable_before = stability_pool.totalClaimableBalances(bravo_token)
    pool_shares_before = stability_pool.userBalances(bob, alpha_token)
    pool_asset_custody_before = bravo_token.balanceOf(stability_pool)
    target_custody_before = bravo_token.balanceOf(rebase_erc20_vault)
    target_allowance_before = bravo_token.allowance(stability_pool, teller)
    target_shares_before = rebase_erc20_vault.userBalances(bob, bravo_token)
    source_ledger_before = ledger.getDepositLedgerData(bob, pool_id)
    target_ledger_before = ledger.getDepositLedgerData(bob, 4)
    source_user_points_before = ledger.userDepositPoints(bob, pool_id, alpha_token)
    source_asset_points_before = ledger.assetDepositPoints(pool_id, alpha_token)
    target_user_points_before = ledger.userDepositPoints(bob, 4, bravo_token)
    target_asset_points_before = ledger.assetDepositPoints(4, bravo_token)
    global_points_before = ledger.globalDepositPoints()
    ripe_rewards_before = ledger.ripeRewards()

    with pytest.raises(BoaError) as exc_info:
        claim_from_stability_pool(
            teller,
            pool_id,
            alpha_token,
            bravo_token,
            MAX_UINT256,
            bob,
            True,
            sender=bob,
        )
    assert_reverted_call(exc_info.value, "cannot receive 0 shares", teller)

    assert bravo_token.balanceOf(bob) == user_wallet_before
    assert stability_pool.claimableBalances(
        alpha_token, bravo_token
    ) == pool_claimable_before
    assert stability_pool.totalClaimableBalances(bravo_token) == total_claimable_before
    assert stability_pool.userBalances(bob, alpha_token) == pool_shares_before
    assert bravo_token.balanceOf(stability_pool) == pool_asset_custody_before
    assert bravo_token.balanceOf(rebase_erc20_vault) == target_custody_before
    assert bravo_token.allowance(stability_pool, teller) == target_allowance_before
    assert rebase_erc20_vault.userBalances(bob, bravo_token) == target_shares_before
    assert ledger.getDepositLedgerData(bob, pool_id) == source_ledger_before
    assert ledger.getDepositLedgerData(bob, 4) == target_ledger_before
    assert ledger.userDepositPoints(
        bob, pool_id, alpha_token
    ) == source_user_points_before
    assert ledger.assetDepositPoints(
        pool_id, alpha_token
    ) == source_asset_points_before
    assert ledger.userDepositPoints(bob, 4, bravo_token) == target_user_points_before
    assert ledger.assetDepositPoints(4, bravo_token) == target_asset_points_before
    assert ledger.globalDepositPoints() == global_points_before
    assert ledger.ripeRewards() == ripe_rewards_before

    # The existing direct-transfer branch still works when auto-deposit is not
    # selected; it was not used as a fallback after the failed attempt above.
    assert claim_from_stability_pool(
        teller,
        pool_id,
        alpha_token,
        bravo_token,
        MAX_UINT256,
        bob,
        False,
        sender=bob,
    ) == claimable_amount
    assert bravo_token.balanceOf(bob) == user_wallet_before + claimable_amount
    assert rebase_erc20_vault.userBalances(bob, bravo_token) == target_shares_before


def test_stab_vault_claims_auto_deposit_no_vault(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit fallback when no vault exists for the asset"""
    setGeneralConfig()
    setAssetConfig(bravo_token, _vaultIds=[])  # Configure for claims but no vault, so getFirstVaultIdForAsset will return 0

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balance
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)

    vault_id = vault_book.getRegId(stability_pool)

    # Claim with auto-deposit enabled (should fallback to direct transfer)
    usd_value = claim_from_stability_pool(teller,
        vault_id, alpha_token, bravo_token, MAX_UINT256, bob, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify claim worked
    _test(claimable_amount, usd_value)

    # Verify tokens were sent directly to Bob (fallback due to no vault)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    _test(claimable_amount, final_bob_bravo_balance - initial_bob_bravo_balance)


def test_stab_vault_claims_auto_deposit_stability_pool_vault(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit fallback when vault ID is 1 (stability pool itself)"""
    setGeneralConfig()
    setAssetConfig(bravo_token, _vaultIds=[1])  # Vault ID 1 is stability pool

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balance
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)

    vault_id = vault_book.getRegId(stability_pool)

    # Claim with auto-deposit enabled (should fallback to direct transfer)
    usd_value = claim_from_stability_pool(teller,
        vault_id, alpha_token, bravo_token, MAX_UINT256, bob, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify claim worked
    _test(claimable_amount, usd_value)

    # Verify tokens were sent directly to Bob (fallback due to stability pool vault ID)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    _test(claimable_amount, final_bob_bravo_balance - initial_bob_bravo_balance)


def test_stab_vault_claims_auto_deposit_config_disabled(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit fallback when deposit config is disabled"""
    setGeneralConfig()
    setAssetConfig(bravo_token, _canDeposit=False)  # Deposit disabled

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balance
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)

    vault_id = vault_book.getRegId(stability_pool)

    # Claim with auto-deposit enabled (should fallback to direct transfer)
    usd_value = claim_from_stability_pool(teller,
        vault_id, alpha_token, bravo_token, MAX_UINT256, bob, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify claim worked
    _test(claimable_amount, usd_value)

    # Verify tokens were sent directly to Bob (fallback due to deposit config)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    _test(claimable_amount, final_bob_bravo_balance - initial_bob_bravo_balance)


def test_stab_vault_claims_auto_deposit_many_basic(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    simple_erc20_vault,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit with claimManyFromStabilityPool"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Setup stability pool
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    bravo_amount = 80 * EIGHTEEN_DECIMALS
    charlie_amount = 120 * (10 ** charlie_token.decimals())
    
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, charlie_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balances
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)
    initial_bob_charlie_balance = charlie_token.balanceOf(bob)
    initial_bob_bravo_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    initial_bob_charlie_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)

    # Create claims array
    claims = [
        (alpha_token.address, bravo_token.address, MAX_UINT256),
        (alpha_token.address, charlie_token.address, MAX_UINT256)
    ]

    vault_id = vault_book.getRegId(stability_pool)

    # Claim many with auto-deposit enabled
    total_usd_value = teller.claimManyFromStabilityPool(
        vault_id, claims, bob, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify claims worked
    _test(200 * EIGHTEEN_DECIMALS, total_usd_value)

    # Verify tokens were auto-deposited (not sent directly to Bob)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    final_bob_charlie_balance = charlie_token.balanceOf(bob)
    final_bob_bravo_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    final_bob_charlie_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, charlie_token)

    assert final_bob_bravo_balance == initial_bob_bravo_balance  # No direct transfer
    assert final_bob_charlie_balance == initial_bob_charlie_balance  # No direct transfer
    _test(bravo_amount, final_bob_bravo_vault_balance - initial_bob_bravo_vault_balance)  # Auto-deposited
    _test(charlie_amount, final_bob_charlie_vault_balance - initial_bob_charlie_vault_balance)  # Auto-deposited


def test_stab_vault_claims_auto_deposit_many_mixed(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    simple_erc20_vault,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit with claimManyFromStabilityPool where some assets auto-deposit and others don't"""
    setGeneralConfig()
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token, _vaultIds=[])  # Configure for claims but no vault, so it should fallback to direct transfer

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(charlie_token, price)

    # Setup stability pool
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    bravo_amount = 80 * EIGHTEEN_DECIMALS
    charlie_amount = 120 * (10 ** charlie_token.decimals())
    
    bravo_token.transfer(stability_pool, bravo_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, bravo_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )
    
    charlie_token.transfer(stability_pool, charlie_amount, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, charlie_token, charlie_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balances
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)
    initial_bob_charlie_balance = charlie_token.balanceOf(bob)
    initial_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    # Create claims array
    claims = [
        (alpha_token.address, bravo_token.address, MAX_UINT256),
        (alpha_token.address, charlie_token.address, MAX_UINT256)
    ]

    vault_id = vault_book.getRegId(stability_pool)

    # Claim many with auto-deposit enabled
    total_usd_value = teller.claimManyFromStabilityPool(
        vault_id, claims, bob, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify claims worked
    _test(200 * EIGHTEEN_DECIMALS, total_usd_value)

    # Verify bravo was auto-deposited, charlie was sent directly
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    final_bob_charlie_balance = charlie_token.balanceOf(bob)
    final_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    assert final_bob_bravo_balance == initial_bob_bravo_balance  # No direct transfer for bravo
    _test(charlie_amount, final_bob_charlie_balance - initial_bob_charlie_balance)  # Direct transfer for charlie
    _test(bravo_amount, final_bob_vault_balance - initial_bob_vault_balance)  # Auto-deposited bravo


def test_stab_vault_claims_auto_deposit_partial_claim(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    simple_erc20_vault,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Test auto-deposit works correctly with partial claims"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 100 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Record initial balance
    initial_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)

    vault_id = vault_book.getRegId(stability_pool)

    # Partial claim with auto-deposit enabled
    partial_claim_amount = 40 * EIGHTEEN_DECIMALS
    usd_value = claim_from_stability_pool(teller,
        vault_id, alpha_token, bravo_token, partial_claim_amount, bob, True, sender=bob  # _shouldAutoDeposit=True
    )

    # Verify partial claim worked
    _test(partial_claim_amount, usd_value)

    # Verify tokens were auto-deposited
    final_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    _test(partial_claim_amount, final_bob_vault_balance - initial_bob_vault_balance)

    # Verify Bob still has remaining position in stability pool
    remaining_value = stability_pool.getTotalUserValue(bob, alpha_token)
    assert remaining_value > 0


def test_stab_vault_claims_auto_deposit_with_delegation(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    simple_erc20_vault,
    _test,
    setGeneralConfig,
    setAssetConfig,
    setUserDelegation,
):
    """Test auto-deposit works correctly when someone claims for another user via delegation"""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # Setup stability pool
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        ZERO_ADDRESS, alpha_token, savings_green, sender=auction_house.address
    )

    # Bob delegates claim permission to Alice
    setUserDelegation(bob, alice, _canClaimFromStabPool=True)

    # Record initial balances
    initial_bob_bravo_balance = bravo_token.balanceOf(bob)
    initial_alice_bravo_balance = bravo_token.balanceOf(alice)
    initial_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    initial_alice_vault_balance = simple_erc20_vault.getTotalAmountForUser(alice, bravo_token)

    vault_id = vault_book.getRegId(stability_pool)

    # Alice claims for Bob with auto-deposit enabled
    usd_value = claim_from_stability_pool(teller,
        vault_id, alpha_token, bravo_token, MAX_UINT256, bob, True, sender=alice  # _shouldAutoDeposit=True
    )

    # Verify claim worked
    _test(claimable_amount, usd_value)

    # Verify tokens were auto-deposited to BOB's account (not Alice's)
    final_bob_bravo_balance = bravo_token.balanceOf(bob)
    final_alice_bravo_balance = bravo_token.balanceOf(alice)
    final_bob_vault_balance = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    final_alice_vault_balance = simple_erc20_vault.getTotalAmountForUser(alice, bravo_token)

    assert final_bob_bravo_balance == initial_bob_bravo_balance  # No direct token transfer to Bob
    assert final_alice_bravo_balance == initial_alice_bravo_balance  # No tokens to Alice
    _test(claimable_amount, final_bob_vault_balance - initial_bob_vault_balance)  # Auto-deposited to Bob
    assert final_alice_vault_balance == initial_alice_vault_balance  # No deposit to Alice


#################################
# Dust residual / live-share    #
#################################


DUST_USD_THRESHOLD = 5 * 10 ** 16  # $0.05 in 18-decimal USD
CLAIM_ASSET_ACTIVE = 2


def test_stab_vault_claims_meaningful_live_residual_stays_listed(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    setGeneralConfig,
    setAssetConfig,
):
    """Live-share partial claim below $0.05 stays listed unless the leftover is microscopic."""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices - bravo at $1
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add an active $0.30 balance so a partial claim can leave a dust residual.
    claimable_amount = 30 * 10 ** 16
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        alice, green_token, savings_green, sender=auction_house.address
    )

    # Verify bravo is in the claimable list (index > 0 means it's in the list)
    bravo_index_before = stability_pool.indexOfClaimableAsset(alpha_token, bravo_token)
    assert bravo_index_before > 0, "Bravo should be in claimable list"

    vault_id = vault_book.getRegId(stability_pool)

    # Claim $0.26, leaving $0.04.
    claim_usd_value = 26 * 10 ** 16
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, claim_usd_value, sender=bob)

    # Shares remain and the leftover is well above P // 10**10, so the row stays listed.
    bravo_index_after = stability_pool.indexOfClaimableAsset(alpha_token, bravo_token)
    assert bravo_index_after == bravo_index_before
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE

    remaining_balance = stability_pool.claimableBalances(alpha_token, bravo_token)
    assert remaining_balance > 0
    assert remaining_balance < claimable_amount


def test_stab_vault_claims_no_dust_removal_above_threshold(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    setGeneralConfig,
    setAssetConfig,
):
    """Test that claimable asset stays active at or above $0.05."""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices - bravo at $1
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add claimable assets - $1.00 worth
    claimable_amount = 1 * EIGHTEEN_DECIMALS  # 1 token at $1 = $1.00
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        alice, green_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Claim enough to leave $0.50 (above threshold)
    claim_usd_value = 5 * 10 ** 17  # $0.50
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, claim_usd_value, sender=bob)

    # Bravo should still be in the iterable list (not dust) - index > 0 means in list
    bravo_index_after = stability_pool.indexOfClaimableAsset(alpha_token, bravo_token)
    assert bravo_index_after > 0, "Non-dust should remain in list"

    # And balance should remain
    remaining_balance = stability_pool.claimableBalances(alpha_token, bravo_token)
    assert remaining_balance > 0


def test_stab_vault_claims_dust_balance_preserved(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    _test,
    setGeneralConfig,
    setAssetConfig,
):
    """Claim and total balances stay intact after a live-share sub-$0.05 residual."""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add an active $0.30 balance.
    claimable_amount = 30 * 10 ** 16
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        alice, green_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Claim $0.26, leaving a $0.04 residual that stays ACTIVE: below $0.05 but not microscopic.
    claim_usd_value = 26 * 10 ** 16
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, claim_usd_value, sender=bob)

    bravo_index_after = stability_pool.indexOfClaimableAsset(alpha_token, bravo_token)
    assert bravo_index_after > 0
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE

    # Verify balances are preserved (not zeroed)
    remaining_claimable = stability_pool.claimableBalances(alpha_token, bravo_token)
    remaining_total = stability_pool.totalClaimableBalances(bravo_token)

    expected_remaining = claimable_amount - claim_usd_value
    _test(expected_remaining, remaining_claimable)
    _test(expected_remaining, remaining_total)


def test_stab_vault_claims_receipt_accumulates_on_listed_live_residual(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    setGeneralConfig,
    setAssetConfig,
):
    """A later receipt adds onto a live-share sub-$0.05 residual that stayed listed."""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(green_token, price)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add small claimable assets - $0.15 worth
    claimable_amount = 15 * 10 ** 16
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, claimable_amount,
        alice, green_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Claim to leave dust
    claim_usd_value = 11 * 10 ** 16
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, claim_usd_value, sender=bob)

    bravo_index_after = stability_pool.indexOfClaimableAsset(alpha_token, bravo_token)
    assert bravo_index_after > 0
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE

    # Store the dust balance
    dust_balance = stability_pool.claimableBalances(alpha_token, bravo_token)
    assert dust_balance > 0

    # New liquidation adds more bravo - $1.00 worth
    new_claimable = 1 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, new_claimable, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount // 2, bravo_token, new_claimable,
        alice, green_token, savings_green, sender=auction_house.address
    )

    bravo_index_readded = stability_pool.indexOfClaimableAsset(alpha_token, bravo_token)
    assert bravo_index_readded == bravo_index_after
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE

    # Balance should be dust + new amount
    total_balance = stability_pool.claimableBalances(alpha_token, bravo_token)
    assert total_balance == dust_balance + new_claimable


def test_stab_vault_claims_precision_loss_retains_when_p_less_than_d(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    setGeneralConfig,
    setAssetConfig,
):
    """A one-wei residual after a live-share claim stays listed when P < 10**10."""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Ten wei is worth $0.30, allowing an active entry with a one-wei dust tail.
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 3 * 10 ** 34)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # Add very small claimable amount (10 wei)
    claimable_amount = 10
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        alice, green_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Claim $0.27, which is 9 of 10 token wei and leaves 1 wei. P < 10**10, so
    # no nonzero live residual is microscopic; remainingUsdValue=1 is not enough
    # to unlist while shares remain.
    claim_usd_value = 27 * 10 ** 16
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, claim_usd_value, sender=bob)

    bravo_index_after = stability_pool.indexOfClaimableAsset(alpha_token, bravo_token)
    assert bravo_index_after > 0
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE

    # But balance should remain
    remaining = stability_pool.claimableBalances(alpha_token, bravo_token)
    assert remaining == 1  # 1 wei left


def test_stab_vault_claims_dust_different_price_levels(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    green_token,
    setGeneralConfig,
    setAssetConfig,
):
    """A live-share residual below $0.05 stays listed at a high unit price."""
    setGeneralConfig()
    setAssetConfig(bravo_token)

    # Set mock prices - bravo at $2000 (like ETH)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 2000 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)

    # Initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)

    # 0.00015 tokens at $2000 = $0.30, which activates at receipt.
    claimable_amount = 15 * 10 ** 13
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token, deposit_amount, bravo_token, claimable_amount,
        alice, green_token, savings_green, sender=auction_house.address
    )

    vault_id = vault_book.getRegId(stability_pool)

    # Claim $0.26 to leave $0.04 below the retention threshold.
    claim_usd_value = 26 * 10 ** 16
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, claim_usd_value, sender=bob)

    bravo_index_after = stability_pool.indexOfClaimableAsset(alpha_token, bravo_token)
    assert bravo_index_after > 0
    assert stability_pool.getClaimAssetState(alpha_token, bravo_token) == CLAIM_ASSET_ACTIVE

    # Balance should remain
    remaining = stability_pool.claimableBalances(alpha_token, bravo_token)
    assert remaining > 0


def test_stability_pool_ripe_rewards_use_core_governance_vault_pointer(
    stability_pool,
    alternate_ripe_gov_vault,
    registerVault,
    mission_control,
    switchboard_alpha,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    setAssetConfig,
    setupStabPoolClaimsRewards,
):
    setupStabPoolClaimsRewards(_ripePerDollar=EIGHTEEN_DECIMALS // 10)
    core_id = registerVault(alternate_ripe_gov_vault, "Core RipeGov")
    setAssetConfig(ripe_token, _vaultIds=[core_id])
    setAssetConfig(bravo_token)
    mission_control.setCoreRipeGovVaultId(core_id, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(ripe_token, EIGHTEEN_DECIMALS)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        deposit_amount,
        bravo_token,
        claimable_amount,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )

    vault_id = vault_book.getRegId(stability_pool)
    claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)
    assert alternate_ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) > 0
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0


def test_stability_pool_ripe_rewards_fail_closed_when_core_pointer_is_unset(
    stability_pool,
    mission_control,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    setAssetConfig,
    setupStabPoolClaimsRewards,
):
    setupStabPoolClaimsRewards(_ripePerDollar=EIGHTEEN_DECIMALS // 10)
    setAssetConfig(bravo_token)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(ripe_token, EIGHTEEN_DECIMALS)
    mission_control.eval("self.coreRipeGovVaultId = 0")

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(bob, alpha_token, deposit_amount, sender=teller.address)
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        deposit_amount,
        bravo_token,
        claimable_amount,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )

    vault_id = vault_book.getRegId(stability_pool)
    with boa.reverts("invalid vault id"):
        claim_from_stability_pool(teller, vault_id, alpha_token, bravo_token, sender=bob)


def test_stability_pool_auto_deposit_rejects_its_own_dynamic_vault_id(
    alternate_stability_pool,
    registerVault,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    savings_green,
    setGeneralConfig,
    setAssetConfig,
):
    pool_id = registerVault(alternate_stability_pool, "Secondary Stability Pool")
    setGeneralConfig()
    setAssetConfig(bravo_token, _vaultIds=[pool_id])
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(alternate_stability_pool, deposit_amount, sender=alpha_token_whale)
    alternate_stability_pool.depositTokensInVault(
        bob,
        alpha_token,
        deposit_amount,
        sender=teller.address,
    )
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    bravo_token.transfer(alternate_stability_pool, claimable_amount, sender=bravo_token_whale)
    alternate_stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        deposit_amount,
        bravo_token,
        claimable_amount,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )

    claim_from_stability_pool(teller,
        pool_id,
        alpha_token,
        bravo_token,
        MAX_UINT256,
        bob,
        True,
        sender=bob,
    )
    assert bravo_token.balanceOf(bob) > 0
    assert alternate_stability_pool.getTotalAmountForUser(bob, bravo_token) == 0


def test_preferred_pointer_rotation_preserves_legacy_pool_state_and_explicit_access(
    stability_pool,
    alternate_stability_pool,
    registerVault,
    mission_control,
    switchboard_alpha,
    alpha_token,
    bravo_token,
    green_token,
    savings_green,
    alpha_token_whale,
    bravo_token_whale,
    whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    setGeneralConfig,
    setAssetConfig,
):
    preferred_id = registerVault(
        alternate_stability_pool,
        "Replacement Preferred Stability Pool",
    )
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[1], _stakersPointsAlloc=0)
    setAssetConfig(bravo_token, _vaultIds=[1], _stakersPointsAlloc=0)
    setAssetConfig(savings_green, _vaultIds=[1, preferred_id])
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    legacy_deposit = 100 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, legacy_deposit, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob,
        alpha_token,
        legacy_deposit,
        sender=teller.address,
    )

    swapped_amount = 40 * EIGHTEEN_DECIMALS
    claimable_amount = 60 * EIGHTEEN_DECIMALS
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        swapped_amount,
        bravo_token,
        claimable_amount,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )

    legacy_position_before = stability_pool.getTotalAmountForUser(bob, alpha_token)
    pair_claimable_before = stability_pool.claimableBalances(alpha_token, bravo_token)
    total_claimable_before = stability_pool.totalClaimableBalances(bravo_token)
    active_claim_assets_before = stability_pool.numClaimableAssets(alpha_token)
    assert legacy_position_before > 0
    assert pair_claimable_before > 0

    mission_control.setPreferredStabVaultId(
        preferred_id,
        sender=switchboard_alpha.address,
    )

    assert (
        stability_pool.getTotalAmountForUser(bob, alpha_token)
        == legacy_position_before
    )
    assert (
        stability_pool.claimableBalances(alpha_token, bravo_token)
        == pair_claimable_before
    )
    assert stability_pool.totalClaimableBalances(bravo_token) == total_claimable_before
    assert stability_pool.numClaimableAssets(alpha_token) == active_claim_assets_before

    new_deposit = 25 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, new_deposit, sender=whale)
    green_token.approve(teller, new_deposit, sender=bob)
    sgreen_deposited = teller.convertToSavingsGreenAndDepositIntoStabPool(
        bob,
        new_deposit,
        sender=bob,
    )
    assert (
        alternate_stability_pool.getTotalAmountForUser(bob, savings_green)
        == sgreen_deposited
    )
    assert stability_pool.getTotalAmountForUser(bob, savings_green) == 0
    assert (
        stability_pool.getTotalAmountForUser(bob, alpha_token)
        == legacy_position_before
    )
    assert (
        stability_pool.claimableBalances(alpha_token, bravo_token)
        == pair_claimable_before
    )

    bravo_balance_before = bravo_token.balanceOf(bob)
    claimed_usd_value = claim_from_stability_pool(teller,
        1,
        alpha_token,
        bravo_token,
        MAX_UINT256,
        bob,
        False,
        sender=bob,
    )
    assert claimed_usd_value > 0
    assert bravo_token.balanceOf(bob) > bravo_balance_before

    legacy_remaining = stability_pool.getTotalAmountForUser(bob, alpha_token)
    assert legacy_remaining > 0
    withdrawn = teller.withdraw(
        alpha_token,
        legacy_remaining,
        bob,
        stability_pool,
        1,
        sender=bob,
    )
    assert 0 <= legacy_remaining - withdrawn <= 1
    assert stability_pool.getTotalAmountForUser(bob, alpha_token) == 0
    assert (
        alternate_stability_pool.getTotalAmountForUser(bob, savings_green)
        == sgreen_deposited
    )


############################################################################
# WP8 (Section 15): stability-reward lock correctness
#
# The fixture argument `_stabRewardsLockDuration` was dead: production derives
# the reward lock in MissionControl._getLockDuration as
#   minLockDuration                      if ratio == 0 or maxLock <= minLock
#   (maxLock - minLock) * ratio / 100_00 otherwise
# Note the second branch does NOT add minLockDuration back; the floor is
# re-applied later by RipeGov._depositTokensInRipeGovVault, which clamps the
# requested duration into [minLockDuration, maxLockDuration].
# and StabVault._handleClaimRewards forwards that value to
# Teller.depositFromTrusted. With the old fixture defaults (minLock 0,
# ratio 0) every "reward lock" test asserted only that a position existed,
# which a completely unlocked position also satisfies. These tests configure
# a nonzero lock and assert the exact unlock block and the exact boundary.
############################################################################


@pytest.fixture
def setupStabRewardLock(
    mission_control,
    setAssetConfig,
    setGeneralConfig,
    setRipeRewardsConfig,
    switchboard_alpha,
    ripe_token,
):
    """Configure stab-pool claim rewards with an explicit gov-vault lock."""

    def setupStabRewardLock(
        _ripePerDollar=EIGHTEEN_DECIMALS,
        _minLockDuration=100,
        _maxLockDuration=1_100,
        _autoStakeDurationRatio=0,
        _maxLockBoost=0,
    ):
        setGeneralConfig()
        setRipeRewardsConfig(
            _stabPoolRipePerDollarClaimed=_ripePerDollar,
            _autoStakeDurationRatio=_autoStakeDurationRatio,
        )
        lock_terms = (
            _minLockDuration,
            _maxLockDuration,
            _maxLockBoost,
            False,
            0,
        )
        mission_control.setRipeGovVaultConfig(
            ripe_token,
            100_00,
            False,
            lock_terms,
            sender=switchboard_alpha.address,
        )
        setAssetConfig(ripe_token, _vaultIds=[2])

    return setupStabRewardLock


def _claim_for_stab_rewards(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    claimer,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    deposit_amount=100 * EIGHTEEN_DECIMALS,
    claimable_amount=150 * EIGHTEEN_DECIMALS,
):
    """Run one full stability-pool claim so the reward deposit is exercised."""
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        claimer, alpha_token, deposit_amount, sender=teller.address
    )
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        deposit_amount,
        bravo_token,
        claimable_amount,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )
    vault_id = vault_book.getRegId(stability_pool)
    return claim_from_stability_pool(
        teller, vault_id, alpha_token, bravo_token, sender=claimer
    )


@pytest.mark.parametrize(
    ("ratio", "expected_lock"),
    (
        (0, 100),        # ratio 0 -> minLockDuration only
        (33_00, 330),    # (1_100 - 100) * 33%
        (50_00, 500),    # (1_100 - 100) * 50%
        (100_00, 1_000), # (1_100 - 100) * 100%, still under maxLockDuration
    ),
)
def test_stab_reward_lock_matches_autostake_ratio_exactly(
    ratio,
    expected_lock,
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    setAssetConfig,
    setupStabRewardLock,
):
    """The reward lock is exactly the MissionControl-derived duration."""
    setupStabRewardLock(_autoStakeDurationRatio=ratio)
    setAssetConfig(bravo_token)

    _claim_for_stab_rewards(
        stability_pool,
        alpha_token,
        bravo_token,
        alpha_token_whale,
        bravo_token_whale,
        bob,
        teller,
        auction_house,
        mock_price_source,
        vault_book,
        savings_green,
        ripe_token,
    )

    assert ripe_gov_vault.userBalances(bob, ripe_token) > 0
    assert ripe_gov_vault.userGovData(bob, ripe_token).unlock == (
        boa.env.evm.patch.block_number + expected_lock
    )


def test_stab_reward_lock_blocks_withdrawal_until_the_exact_unlock_block(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    setAssetConfig,
    setupStabRewardLock,
):
    """One block before unlock the exit reverts; at unlock it succeeds.

    This is the assertion the old suite was missing: with ratio 0 and
    minLockDuration 0 the reward was never locked at all, so "a position
    exists" passed without proving any unlock boundary.
    """
    setupStabRewardLock(_autoStakeDurationRatio=50_00)
    setAssetConfig(bravo_token)

    _claim_for_stab_rewards(
        stability_pool,
        alpha_token,
        bravo_token,
        alpha_token_whale,
        bravo_token_whale,
        bob,
        teller,
        auction_house,
        mock_price_source,
        vault_book,
        savings_green,
        ripe_token,
    )

    unlock = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    assert unlock == boa.env.evm.patch.block_number + 500
    reward_shares = ripe_gov_vault.userBalances(bob, ripe_token)
    assert reward_shares > 0

    # One block before unlock.
    boa.env.time_travel(blocks=unlock - boa.env.evm.patch.block_number - 1)
    assert boa.env.evm.patch.block_number == unlock - 1
    with boa.reverts("not reached unlock"):
        ripe_gov_vault.withdrawTokensFromVault(
            bob, ripe_token, MAX_UINT256, bob, sender=teller.address
        )
    assert ripe_gov_vault.userBalances(bob, ripe_token) == reward_shares

    # Exactly at unlock.
    boa.env.time_travel(blocks=1)
    assert boa.env.evm.patch.block_number == unlock
    withdrawn, is_depleted = ripe_gov_vault.withdrawTokensFromVault(
        bob, ripe_token, MAX_UINT256, bob, sender=teller.address
    )
    assert withdrawn > 0
    assert is_depleted


def test_stab_reward_lock_never_shortens_a_later_existing_unlock(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    whale,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    switchboard_alpha,
    setAssetConfig,
    setupStabRewardLock,
):
    """A reward paid into an existing longer-locked position (Section 15).

    _getWeightedLockOnTokenDeposit blends the reward's lock with the existing
    one, so the resulting unlock must stay between the reward-only lock and the
    prior unlock -- never below the reward lock and never above the prior one.
    """
    setupStabRewardLock(_autoStakeDurationRatio=50_00)
    setAssetConfig(bravo_token)

    # Pre-existing position at the maximum lock.
    existing = 1_000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, existing, sender=whale)
    ripe_gov_vault.depositTokensWithLockDuration(
        bob, ripe_token, existing, 1_100, sender=teller.address
    )
    prior_unlock = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    assert prior_unlock == boa.env.evm.patch.block_number + 1_100

    _claim_for_stab_rewards(
        stability_pool,
        alpha_token,
        bravo_token,
        alpha_token_whale,
        bravo_token_whale,
        bob,
        teller,
        auction_house,
        mock_price_source,
        vault_book,
        savings_green,
        ripe_token,
    )

    unlock_after = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    reward_only_unlock = boa.env.evm.patch.block_number + 500
    assert reward_only_unlock <= unlock_after <= prior_unlock
    # The reward is small relative to the existing stake, so the blend stays
    # close to the prior unlock rather than collapsing to the reward lock.
    assert unlock_after > prior_unlock - 100


# ---- Section 15 remaining matrix -----------------------------------------


def _reward_points_after(vault, user, ripe_token, switchboard_alpha, blocks):
    """Accrue `blocks` of governance points and return the saved total."""
    boa.env.time_travel(blocks=blocks)
    vault.updateUserGovPoints(user, sender=switchboard_alpha.address)
    return vault.userGovData(user, ripe_token).govPoints


@pytest.mark.parametrize(
    ("ratio", "expected_lock"),
    ((0, 100), (33_00, 330), (50_00, 500), (100_00, 1_000)),
)
def test_stab_reward_lock_point_contribution_is_exact(
    ratio,
    expected_lock,
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    switchboard_alpha,
    setAssetConfig,
    setupStabRewardLock,
):
    """Section 15: the exact point contribution, not merely that a position exists.

    With a 100% maxLockBoost the reward's points are base points plus a lock
    bonus of maxLockBoost * (remaining - minLock) / (maxLock - minLock), so the
    contribution is fully determined by the derived lock duration.
    """
    max_lock_boost = 100_00
    setupStabRewardLock(
        _autoStakeDurationRatio=ratio, _maxLockBoost=max_lock_boost
    )
    setAssetConfig(bravo_token)

    _claim_for_stab_rewards(
        stability_pool, alpha_token, bravo_token, alpha_token_whale,
        bravo_token_whale, bob, teller, auction_house, mock_price_source,
        vault_book, savings_green, ripe_token,
    )

    shares = ripe_gov_vault.userBalances(bob, ripe_token)
    unlock = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    assert unlock == boa.env.evm.patch.block_number + expected_lock

    blocks = 10
    points = _reward_points_after(
        ripe_gov_vault, bob, ripe_token, switchboard_alpha, blocks
    )

    # Reproduce RipeGov._getLatestGovPoints exactly.
    min_lock, max_lock = 100, 1_100
    base = (shares // 10**18) * blocks
    base = base * 100_00 // 100_00  # assetWeight is 100.00%
    remaining = unlock - boa.env.evm.patch.block_number if unlock > boa.env.evm.patch.block_number else 0
    remaining = min(remaining, max_lock)
    bonus = 0
    if remaining > min_lock:
        bonus_ratio = max_lock_boost * (remaining - min_lock) // (max_lock - min_lock)
        bonus = base * bonus_ratio // 100_00
    assert points == base + bonus


@pytest.mark.parametrize(
    ("min_lock", "max_lock", "ratio", "expected_lock"),
    (
        (100, 1_100, 0, 100),
        (100, 1_100, 50_00, 500),
        (100, 1_100, 100_00, 1_000),
    ),
    ids=("minimum", "ordinary", "maximum"),
)
def test_stab_reward_lock_configured_duration_boundaries(
    min_lock,
    max_lock,
    ratio,
    expected_lock,
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    setAssetConfig,
    setupStabRewardLock,
):
    """Section 15: minimum, ordinary, and maximum configured duration."""
    setupStabRewardLock(
        _minLockDuration=min_lock,
        _maxLockDuration=max_lock,
        _autoStakeDurationRatio=ratio,
    )
    setAssetConfig(bravo_token)

    _claim_for_stab_rewards(
        stability_pool, alpha_token, bravo_token, alpha_token_whale,
        bravo_token_whale, bob, teller, auction_house, mock_price_source,
        vault_book, savings_green, ripe_token,
    )

    assert ripe_gov_vault.userBalances(bob, ripe_token) > 0
    unlock = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    assert unlock == boa.env.evm.patch.block_number + expected_lock


def test_stab_reward_claim_reverts_when_max_lock_duration_is_zero(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    setAssetConfig,
    setupStabRewardLock,
):
    """Section 15 zero-state regression.

    Zero maximum lock duration is now rejected by SwitchboardAlpha. Direct
    MissionControl setup is used only to model an uninitialized or legacy state.
    """
    setupStabRewardLock(
        _minLockDuration=0,
        _maxLockDuration=0,
        _autoStakeDurationRatio=0,
    )
    setAssetConfig(bravo_token)

    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    claimable_amount = 150 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(
        bob, alpha_token, deposit_amount, sender=teller.address
    )
    bravo_token.transfer(stability_pool, claimable_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        deposit_amount,
        bravo_token,
        claimable_amount,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )
    vault_id = vault_book.getRegId(stability_pool)
    gov_shares_before = ripe_gov_vault.userBalances(bob, ripe_token)
    claimable_before = stability_pool.claimableBalances(alpha_token, bravo_token)
    assert gov_shares_before == 0
    assert claimable_before > 0

    with pytest.raises(BoaError) as exc_info:
        claim_from_stability_pool(
            teller, vault_id, alpha_token, bravo_token, sender=bob
        )
    assert_reverted_call(exc_info.value, "no lock terms", teller)

    assert ripe_gov_vault.userBalances(bob, ripe_token) == gov_shares_before
    assert stability_pool.claimableBalances(alpha_token, bravo_token) == claimable_before


def test_stab_reward_added_to_an_existing_unlocked_position_creates_a_lock(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    whale,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    setAssetConfig,
    setupStabRewardLock,
):
    """Section 15: reward added to an existing unlocked position.

    The recipient already holds an unlocked RIPE position. The reward's derived
    lock is blended in by _getWeightedLockOnTokenDeposit, so the resulting
    unlock is strictly between "unlocked" and the reward-only lock.
    """
    setupStabRewardLock(_autoStakeDurationRatio=50_00)
    setAssetConfig(bravo_token)

    existing = 1_000 * EIGHTEEN_DECIMALS
    ripe_token.transfer(ripe_gov_vault, existing, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        bob, ripe_token, existing, sender=teller.address
    )
    prior_unlock = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    prior_remaining = (
        prior_unlock - boa.env.evm.patch.block_number
        if prior_unlock > boa.env.evm.patch.block_number
        else 0
    )

    _claim_for_stab_rewards(
        stability_pool, alpha_token, bravo_token, alpha_token_whale,
        bravo_token_whale, bob, teller, auction_house, mock_price_source,
        vault_book, savings_green, ripe_token,
    )

    unlock_after = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    remaining_after = unlock_after - boa.env.evm.patch.block_number
    assert prior_remaining <= remaining_after <= 500


def test_stab_reward_weighted_unlock_after_multiple_reward_deposits(
    stability_pool,
    alpha_token,
    bravo_token,
    charlie_token,
    alpha_token_whale,
    bravo_token_whale,
    charlie_token_whale,
    bob,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    setAssetConfig,
    setupStabRewardLock,
):
    """Section 15: exact weighted unlock after two successive reward deposits.

    Each reward deposit re-runs the weighted blend against the position that
    already exists, so a second reward can only move the unlock between the
    prior unlock and the reward-only lock -- never outside that band.
    """
    setupStabRewardLock(_autoStakeDurationRatio=50_00)
    setAssetConfig(bravo_token)
    setAssetConfig(charlie_token)

    _claim_for_stab_rewards(
        stability_pool, alpha_token, bravo_token, alpha_token_whale,
        bravo_token_whale, bob, teller, auction_house, mock_price_source,
        vault_book, savings_green, ripe_token,
    )
    first_unlock = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    assert first_unlock == boa.env.evm.patch.block_number + 500

    boa.env.time_travel(blocks=50)
    _claim_for_stab_rewards(
        stability_pool, alpha_token, charlie_token, alpha_token_whale,
        charlie_token_whale, bob, teller, auction_house, mock_price_source,
        vault_book, savings_green, ripe_token,
        deposit_amount=50 * EIGHTEEN_DECIMALS,
        claimable_amount=50 * 10**6,
    )

    second_unlock = ripe_gov_vault.userGovData(bob, ripe_token).unlock
    remaining = second_unlock - boa.env.evm.patch.block_number
    prior_remaining = first_unlock - boa.env.evm.patch.block_number
    low, high = sorted((prior_remaining, 500))
    assert low <= remaining <= high


MISSION_CONTROL_ID = 5


def _swap_mission_control(ripe_hq_deploy, governance, new_mission_control):
    assert ripe_hq_deploy.startAddressUpdateToRegistry(
        MISSION_CONTROL_ID, new_mission_control, sender=governance.address
    )
    boa.env.time_travel(blocks=ripe_hq_deploy.registryChangeTimeLock())
    assert ripe_hq_deploy.confirmAddressUpdateToRegistry(
        MISSION_CONTROL_ID, sender=governance.address
    )


def _clone_reward_source(
    source_mission_control,
    target_mission_control,
    switchboard_alpha,
    assets,
    *,
    auto_stake_duration_ratio,
    ripe_token,
    min_lock,
    max_lock,
):
    """Copy the live configuration into a second MissionControl, overriding
    only the two values that determine the reward lock.

    Cloning the structs straight off the active source keeps this test bound to
    the real config shape instead of a hand-written tuple that would silently
    drift from cs.AssetConfig.
    """
    target_mission_control.setGeneralConfig(
        source_mission_control.genConfig(), sender=switchboard_alpha.address
    )
    rewards = list(source_mission_control.rewardsConfig())
    rewards[7] = auto_stake_duration_ratio  # autoStakeDurationRatio
    target_mission_control.setRipeRewardsConfig(
        tuple(rewards), sender=switchboard_alpha.address
    )
    gov_cfg = source_mission_control.ripeGovVaultConfig(ripe_token)
    target_mission_control.setRipeGovVaultConfig(
        ripe_token,
        gov_cfg.assetWeight,
        gov_cfg.shouldFreezeWhenBadDebt,
        (min_lock, max_lock, gov_cfg.lockTerms.maxLockBoost,
         gov_cfg.lockTerms.canExit, gov_cfg.lockTerms.exitFee),
        sender=switchboard_alpha.address,
    )
    for asset in assets:
        target_mission_control.setAssetConfig(
            asset,
            source_mission_control.assetConfig(asset),
            sender=switchboard_alpha.address,
        )


def test_stab_reward_lock_follows_the_active_mission_control_source(
    stability_pool,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    mock_price_source,
    vault_book,
    savings_green,
    ripe_token,
    ripe_gov_vault,
    mission_control,
    switchboard_alpha,
    ripe_hq_deploy,
    governance,
    defaults,
    setAssetConfig,
    setupStabRewardLock,
):
    """Section 15 final row: replace the active config source, then restore it.

    Proves the reward lock is read from whichever MissionControl RipeHq
    currently resolves, and that restoring the original source restores the
    original lock -- so the derived lock is not cached anywhere.
    """
    # Original source: 50% auto-stake ratio over [100, 1_100] -> 500 blocks.
    setupStabRewardLock(_autoStakeDurationRatio=50_00)
    setAssetConfig(bravo_token)

    _claim_for_stab_rewards(
        stability_pool, alpha_token, bravo_token, alpha_token_whale,
        bravo_token_whale, bob, teller, auction_house, mock_price_source,
        vault_book, savings_green, ripe_token,
    )
    assert ripe_gov_vault.userGovData(bob, ripe_token).unlock == (
        boa.env.evm.patch.block_number + 500
    )

    # Second valid config contract: 100% ratio over [200, 1_200] -> 1_000 blocks.
    second_mission_control = boa.load(
        "contracts/data/MissionControl.vy",
        ripe_hq_deploy,
        defaults,
        name="second_mission_control",
        override_address=boa.env.generate_address(),
    )
    _clone_reward_source(
        mission_control,
        second_mission_control,
        switchboard_alpha,
        (ripe_token, bravo_token),
        auto_stake_duration_ratio=100_00,
        ripe_token=ripe_token,
        min_lock=200,
        max_lock=1_200,
    )
    _swap_mission_control(ripe_hq_deploy, governance, second_mission_control)

    _claim_for_stab_rewards(
        stability_pool, alpha_token, bravo_token, alpha_token_whale,
        bravo_token_whale, alice, teller, auction_house, mock_price_source,
        vault_book, savings_green, ripe_token,
    )
    alice_unlock = ripe_gov_vault.userGovData(alice, ripe_token).unlock
    assert alice_unlock == boa.env.evm.patch.block_number + 1_000

    # Restore the original source; subsequent rewards use the original values.
    _swap_mission_control(ripe_hq_deploy, governance, mission_control)

    _claim_for_stab_rewards(
        stability_pool, alpha_token, bravo_token, alpha_token_whale,
        bravo_token_whale, sally, teller, auction_house, mock_price_source,
        vault_book, savings_green, ripe_token,
    )
    restored_unlock = ripe_gov_vault.userGovData(sally, ripe_token).unlock
    assert restored_unlock == boa.env.evm.patch.block_number + 500
