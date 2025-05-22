import pytest
import boa

from constants import EIGHTEEN_DECIMALS


def test_loot_claim_basic(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig()

    # Setup deposit points
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # update deposit points
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # user points
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints != 0

    claimable = lootbox.getClaimableLoot(bob)
    assert claimable != 0

    asset_claimable = lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token)
    assert asset_claimable != 0

    # claim loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe != 0

    assert ripe_token.balanceOf(bob) == total_ripe

    # verify points are reset
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == 0
    
    # verify claimable amount is now zero
    claimable = lootbox.getClaimableLoot(bob)
    assert claimable == 0


def test_loot_claim_multiple_users(
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    setUserDelegation,
    sally,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig()

    setUserDelegation(bob, sally)
    setUserDelegation(alice, sally)

    # Setup deposit points for both users
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(alice, 50 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # update deposit points for both users
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # claim loot for both users
    total_ripe = teller.claimLootForManyUsers([bob, alice], False, sender=sally)
    assert total_ripe != 0

    # verify both users received their share
    bob_ripe = ripe_token.balanceOf(bob)
    alice_ripe = ripe_token.balanceOf(alice)
    assert bob_ripe + alice_ripe == total_ripe
    assert bob_ripe > alice_ripe  # Bob deposited more, should get more rewards


def test_loot_claim_specific_asset(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig()

    # Setup deposit points
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # update deposit points
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # claim loot for specific asset
    total_ripe = lootbox.claimDepositLootForAsset(bob, vault_id, alpha_token, sender=teller.address)
    assert total_ripe != 0

    assert ripe_token.balanceOf(bob) == total_ripe

    # verify points are reset for this asset
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == 0


def test_loot_claim_points_disabled(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    alpha_token,
    alpha_token_whale,
):
    # basic setup with points disabled
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig(_arePointsEnabled=False)

    # Setup deposit points
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # update deposit points
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # verify no points accumulated
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == 0

    # verify no claimable loot
    claimable = lootbox.getClaimableLoot(bob)
    assert claimable == 0

    # attempt to claim loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe == 0


def test_loot_claim_different_allocations(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    # basic setup with different reward allocations
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=80, _voterPointsAlloc=20)
    setRipeRewardsConfig(
        _borrowersAlloc=20,
        _stakersAlloc=40,
        _votersAlloc=20,
        _genDepositorsAlloc=20,
    )

    # Setup deposit points
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # update deposit points
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # claim loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe != 0

    assert ripe_token.balanceOf(bob) == total_ripe

    # verify points are reset
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == 0