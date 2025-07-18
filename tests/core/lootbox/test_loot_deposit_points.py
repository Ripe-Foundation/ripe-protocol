import boa
import pytest

from constants import EIGHTEEN_DECIMALS


def test_loot_deposit_points_first_save(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)
    setAssetConfig(bravo_token, _stakersPointsAlloc=10, _voterPointsAlloc=20)
    setRipeRewardsConfig(True)

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # first update will be all zero
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    
    gp = ledger.globalDepositPoints()
    assert gp.lastUsdValue == deposit_amount // EIGHTEEN_DECIMALS
    assert gp.ripeStakerPoints == 0
    assert gp.ripeVotePoints == 0
    assert gp.ripeGenPoints == 0
    assert gp.lastUpdate == boa.env.evm.patch.block_number

    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.balancePoints == 0
    assert ap.lastBalance == deposit_amount // ap.precision
    assert ap.lastUsdValue == deposit_amount // EIGHTEEN_DECIMALS
    assert ap.ripeStakerPoints == 0
    assert ap.ripeVotePoints == 0
    assert ap.ripeGenPoints == 0
    assert ap.lastUpdate == boa.env.evm.patch.block_number
    assert ap.precision == 10 ** 9

    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == 0
    assert up.lastBalance == deposit_amount // ap.precision
    assert up.lastUpdate == boa.env.evm.patch.block_number


def test_loot_deposit_points_basic_elapsed(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # voter allocs
    alpha_voter_alloc = 20
    bravo_voter_alloc = 20
    total_voter_alloc = alpha_voter_alloc + bravo_voter_alloc

    # staker allocs
    alpha_staker_alloc = 0
    bravo_staker_alloc = 10
    total_staker_alloc = alpha_staker_alloc + bravo_staker_alloc

    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=alpha_staker_alloc, _voterPointsAlloc=alpha_voter_alloc)
    setAssetConfig(bravo_token, _stakersPointsAlloc=bravo_staker_alloc, _voterPointsAlloc=bravo_voter_alloc)
    setRipeRewardsConfig(True)

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # first update will be all zero
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # original
    gp1 = ledger.globalDepositPoints()
    ap1 = ledger.assetDepositPoints(vault_id, alpha_token)
    up1 = ledger.userDepositPoints(bob, vault_id, alpha_token)

    # time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # update again
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # check results
    gp = ledger.globalDepositPoints()
    assert gp.lastUsdValue == gp1.lastUsdValue
    assert gp.ripeStakerPoints == total_staker_alloc * elapsed
    assert gp.ripeVotePoints == total_voter_alloc * elapsed
    assert gp.ripeGenPoints == gp1.lastUsdValue * elapsed
    assert gp.lastUpdate == boa.env.evm.patch.block_number

    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.balancePoints == ap1.lastBalance * elapsed
    assert ap.lastBalance == ap1.lastBalance
    assert ap.lastUsdValue == ap1.lastUsdValue
    assert ap.ripeStakerPoints == 0
    assert ap.ripeVotePoints == alpha_voter_alloc * elapsed
    assert ap.ripeGenPoints == ap1.lastUsdValue * elapsed
    assert ap.lastUpdate == boa.env.evm.patch.block_number
    assert ap.precision == 10 ** 9

    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == up1.lastBalance * elapsed
    assert up.lastBalance == up1.lastBalance
    assert up.lastUpdate == boa.env.evm.patch.block_number


def test_loot_deposit_points_multiple_assets(
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # voter allocs
    alpha_voter_alloc = 20
    bravo_voter_alloc = 20
    total_voter_alloc = alpha_voter_alloc + bravo_voter_alloc

    # staker allocs
    alpha_staker_alloc = 0
    bravo_staker_alloc = 10
    total_staker_alloc = alpha_staker_alloc + bravo_staker_alloc

    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=alpha_staker_alloc, _voterPointsAlloc=alpha_voter_alloc)
    setAssetConfig(bravo_token, _stakersPointsAlloc=bravo_staker_alloc, _voterPointsAlloc=bravo_voter_alloc)
    setRipeRewardsConfig(True)

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_amount, bravo_token, bravo_token_whale)

    # first update will be all zero
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, bravo_token, sender=teller.address)

    # time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # update again
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, bravo_token, sender=teller.address)

    # check results
    gp = ledger.globalDepositPoints()
    assert gp.lastUsdValue == 100 # bravo doesn't count because has stake alloc
    assert gp.ripeStakerPoints == total_staker_alloc * elapsed
    assert gp.ripeVotePoints == total_voter_alloc * elapsed
    assert gp.ripeGenPoints == gp.lastUsdValue * elapsed

    # Check alpha token points
    ap_alpha = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap_alpha.balancePoints == (deposit_amount // ap_alpha.precision) * elapsed
    assert ap_alpha.lastBalance == deposit_amount // ap_alpha.precision
    assert ap_alpha.lastUsdValue == deposit_amount // EIGHTEEN_DECIMALS
    assert ap_alpha.ripeStakerPoints == 0  # No staker allocation
    assert ap_alpha.ripeVotePoints == alpha_voter_alloc * elapsed
    assert ap_alpha.ripeGenPoints == (deposit_amount // EIGHTEEN_DECIMALS) * elapsed

    # Check bravo token points
    ap_bravo = ledger.assetDepositPoints(vault_id, bravo_token)
    assert ap_bravo.balancePoints == (deposit_amount // ap_bravo.precision) * elapsed
    assert ap_bravo.lastBalance == deposit_amount // ap_bravo.precision
    assert ap_bravo.lastUsdValue == 0
    assert ap_bravo.ripeStakerPoints == bravo_staker_alloc * elapsed
    assert ap_bravo.ripeVotePoints == bravo_voter_alloc * elapsed
    assert ap_bravo.ripeGenPoints == 0 # no gen points for staked assets


def test_loot_deposit_points_points_disabled(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)
    setRipeRewardsConfig(False)  # Points disabled

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    # first update
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # update again
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # check results - no points should accumulate when disabled
    gp = ledger.globalDepositPoints()
    assert gp.lastUsdValue == deposit_amount // EIGHTEEN_DECIMALS
    assert gp.ripeStakerPoints == 0
    assert gp.ripeVotePoints == 0
    assert gp.ripeGenPoints == 0
    assert gp.lastUpdate == boa.env.evm.patch.block_number

    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.balancePoints == 0
    assert ap.lastBalance == deposit_amount // ap.precision
    assert ap.lastUsdValue == deposit_amount // EIGHTEEN_DECIMALS
    assert ap.ripeStakerPoints == 0
    assert ap.ripeVotePoints == 0
    assert ap.ripeGenPoints == 0
    assert ap.lastUpdate == boa.env.evm.patch.block_number
    assert ap.precision == 10 ** 9

    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == 0
    assert up.lastBalance == deposit_amount // ap.precision
    assert up.lastUpdate == boa.env.evm.patch.block_number


def test_loot_deposit_points_balance_changes(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)
    setRipeRewardsConfig(True)

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # initial deposit
    initial_deposit = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, initial_deposit, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # time travel and update
    elapsed1 = 10
    boa.env.time_travel(blocks=elapsed1)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # additional deposit
    additional_deposit = 50 * EIGHTEEN_DECIMALS
    performDeposit(bob, additional_deposit, alpha_token, alpha_token_whale)

    # time travel and update again
    elapsed2 = 10
    boa.env.time_travel(blocks=elapsed2)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # check results
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    expected_points1 = (initial_deposit // ap.precision) * elapsed1
    expected_points2 = ((initial_deposit + additional_deposit) // ap.precision) * elapsed2
    assert ap.balancePoints == expected_points1 + expected_points2

    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == expected_points1 + expected_points2
    assert up.lastBalance == (initial_deposit + additional_deposit) // ap.precision


def test_loot_deposit_points_price_changes(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=0)  # Only gen points
    setRipeRewardsConfig(True)

    # initial price
    initial_price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, initial_price)

    # deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # time travel and update
    elapsed1 = 10
    boa.env.time_travel(blocks=elapsed1)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # change price
    new_price = 2 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, new_price)

    # time travel and update again
    elapsed2 = 10
    boa.env.time_travel(blocks=elapsed2)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # time travel and update one more time
    elapsed3 = 10
    boa.env.time_travel(blocks=elapsed3)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # check results
    gp = ledger.globalDepositPoints()
    # Points are calculated based on the current price only
    expected_points2 = (deposit_amount * 2 // EIGHTEEN_DECIMALS) * elapsed2
    expected_points3 = (deposit_amount * 2 // EIGHTEEN_DECIMALS) * elapsed3
    assert gp.ripeGenPoints == expected_points2 + expected_points3
    assert gp.lastUsdValue == deposit_amount * 2 // EIGHTEEN_DECIMALS

    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.ripeGenPoints == expected_points2 + expected_points3
    assert ap.lastUsdValue == deposit_amount * 2 // EIGHTEEN_DECIMALS


def test_loot_deposit_points_multiple_users(
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)  # Only voter points
    setRipeRewardsConfig(True)

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # deposits - bob deposits more than alice
    bob_deposit = 100 * EIGHTEEN_DECIMALS
    alice_deposit = 50 * EIGHTEEN_DECIMALS
    performDeposit(bob, bob_deposit, alpha_token, alpha_token_whale)
    performDeposit(alice, alice_deposit, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # first update for both users
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # update again for both users
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # check results
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    total_balance = bob_deposit + alice_deposit
    assert ap.lastBalance == total_balance // ap.precision
    assert ap.lastUsdValue == total_balance // EIGHTEEN_DECIMALS

    # Check bob's points
    up_bob = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up_bob.lastBalance == bob_deposit // ap.precision
    assert up_bob.balancePoints == (bob_deposit // ap.precision) * elapsed

    # Check alice's points
    up_alice = ledger.userDepositPoints(alice, vault_id, alpha_token)
    assert up_alice.lastBalance == alice_deposit // ap.precision
    assert up_alice.balancePoints == (alice_deposit // ap.precision) * elapsed

    # Verify points are proportional to deposits
    assert up_bob.balancePoints == up_alice.balancePoints * 2  # Bob has 2x the deposit


def test_loot_deposit_points_different_precisions(
    alpha_token,
    alpha_token_whale,
    delta_token,
    delta_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)  # 18 decimals
    setAssetConfig(delta_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)  # 8 decimals (like WBTC)
    setRipeRewardsConfig(True)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    bravo_price = 50000 * EIGHTEEN_DECIMALS  # $50k like BTC
    mock_price_source.setPrice(alpha_token, alpha_price)
    mock_price_source.setPrice(delta_token, bravo_price)

    # deposits - same USD value but different token amounts
    alpha_deposit = 100 * EIGHTEEN_DECIMALS  # $100 worth
    bravo_deposit = 2 * 10**8  # $100 worth (2 BTC at $50k)
    performDeposit(bob, alpha_deposit, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_deposit, delta_token, delta_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # first update
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, delta_token, sender=teller.address)

    # time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # update again
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, delta_token, sender=teller.address)

    # check results
    # Alpha token (18 decimals)
    ap_alpha = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap_alpha.precision == 10**9
    assert ap_alpha.lastBalance == alpha_deposit // ap_alpha.precision
    assert ap_alpha.lastUsdValue == alpha_deposit // EIGHTEEN_DECIMALS
    assert ap_alpha.balancePoints == (alpha_deposit // ap_alpha.precision) * elapsed

    # Bravo token (8 decimals)
    ap_bravo = ledger.assetDepositPoints(vault_id, delta_token)
    assert ap_bravo.precision == 10**4  # Half precision for 8 decimals
    assert ap_bravo.lastBalance == bravo_deposit // ap_bravo.precision
    assert ap_bravo.lastUsdValue == 100_000
    assert ap_bravo.balancePoints == (bravo_deposit // ap_bravo.precision) * elapsed

    # Check global points
    gp = ledger.globalDepositPoints()
    total_usd_value = 100_100
    assert gp.lastUsdValue == total_usd_value
    assert gp.ripeGenPoints == total_usd_value * elapsed


def test_loot_deposit_points_smaller_precisions(
    alpha_token,
    alpha_token_whale,
    charlie_token,
    charlie_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)  # 18 decimals
    setAssetConfig(charlie_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)  # 6 decimals (like USDC)
    setRipeRewardsConfig(True)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    charlie_price = 1 * EIGHTEEN_DECIMALS  # $1 like USDC
    mock_price_source.setPrice(alpha_token, alpha_price)
    mock_price_source.setPrice(charlie_token, charlie_price)

    # deposits - same USD value but different token amounts
    alpha_deposit = 100 * EIGHTEEN_DECIMALS  # $100 worth
    charlie_deposit = 100 * 10**6  # $100 worth (100 USDC)
    performDeposit(bob, alpha_deposit, alpha_token, alpha_token_whale)
    performDeposit(bob, charlie_deposit, charlie_token, charlie_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # first update
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, charlie_token, sender=teller.address)

    # time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # update again
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, charlie_token, sender=teller.address)

    # check results
    # Alpha token (18 decimals)
    ap_alpha = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap_alpha.precision == 10**9  # Half precision for 18 decimals
    assert ap_alpha.lastBalance == alpha_deposit // ap_alpha.precision
    assert ap_alpha.lastUsdValue == alpha_deposit // EIGHTEEN_DECIMALS
    assert ap_alpha.balancePoints == (alpha_deposit // ap_alpha.precision) * elapsed

    # Charlie token (6 decimals)
    ap_charlie = ledger.assetDepositPoints(vault_id, charlie_token)
    assert ap_charlie.precision == 10**6  # Full precision for 6 decimals
    assert ap_charlie.lastBalance == charlie_deposit // ap_charlie.precision
    assert ap_charlie.lastUsdValue == 100
    assert ap_charlie.balancePoints == (charlie_deposit // ap_charlie.precision) * elapsed

    # Check global points
    gp = ledger.globalDepositPoints()
    total_usd_value = 200
    assert gp.lastUsdValue == total_usd_value
    assert gp.ripeGenPoints == total_usd_value * elapsed


def test_loot_deposit_points_zero_balance(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)
    setRipeRewardsConfig(True)

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # time travel and update
    elapsed1 = 10
    boa.env.time_travel(blocks=elapsed1)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # withdraw all funds
    teller.withdraw(alpha_token, deposit_amount, bob, simple_erc20_vault, sender=bob)

    # time travel and update with zero balance
    elapsed2 = 10
    boa.env.time_travel(blocks=elapsed2)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # check results
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.lastBalance == 0
    assert ap.lastUsdValue == 0
    # Points should not accumulate with zero balance
    assert ap.balancePoints == (deposit_amount // ap.precision) * elapsed1

    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.lastBalance == 0
    # User points should not accumulate with zero balance
    assert up.balancePoints == (deposit_amount // ap.precision) * elapsed1

    # Re-deposit and verify points start accumulating again
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    elapsed3 = 10
    boa.env.time_travel(blocks=elapsed3)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Check points after re-deposit
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.lastBalance == deposit_amount // ap.precision
    assert ap.lastUsdValue == deposit_amount // EIGHTEEN_DECIMALS
    # Points should accumulate from re-deposit
    assert ap.balancePoints == (deposit_amount // ap.precision) * (elapsed1 + elapsed3)

    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.lastBalance == deposit_amount // ap.precision
    # User points should accumulate from re-deposit
    assert up.balancePoints == (deposit_amount // ap.precision) * (elapsed1 + elapsed3)


def test_loot_deposit_points_ledger_updates(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)
    setRipeRewardsConfig(True)

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # initial deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Get initial Ledger state
    initial_gp = ledger.globalDepositPoints()
    initial_ap = ledger.assetDepositPoints(vault_id, alpha_token)
    initial_up = ledger.userDepositPoints(bob, vault_id, alpha_token)

    boa.env.time_travel(blocks=1)

    # First update
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Verify Ledger state after first update
    gp1 = ledger.globalDepositPoints()
    ap1 = ledger.assetDepositPoints(vault_id, alpha_token)
    up1 = ledger.userDepositPoints(bob, vault_id, alpha_token)

    assert gp1.lastUpdate > initial_gp.lastUpdate
    assert ap1.lastUpdate > initial_ap.lastUpdate
    assert up1.lastUpdate > initial_up.lastUpdate

    # Time travel and update again
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Verify Ledger state after second update
    gp2 = ledger.globalDepositPoints()
    ap2 = ledger.assetDepositPoints(vault_id, alpha_token)
    up2 = ledger.userDepositPoints(bob, vault_id, alpha_token)

    # Check points accumulation in Ledger
    assert gp2.ripeGenPoints > gp1.ripeGenPoints
    assert ap2.balancePoints > ap1.balancePoints
    assert up2.balancePoints > up1.balancePoints

    # Verify lastUpdate timestamps
    assert gp2.lastUpdate > gp1.lastUpdate
    assert ap2.lastUpdate > ap1.lastUpdate
    assert up2.lastUpdate > up1.lastUpdate


def test_loot_deposit_points_permission_checks(
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    switchboard_alpha,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)
    setRipeRewardsConfig(True)

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)

    # Test unauthorized caller
    with boa.reverts("no perms"):
        lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=alice)

    # Test paused state
    lootbox.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Unpause and verify it works
    lootbox.pause(False, sender=switchboard_alpha.address)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)


def test_loot_deposit_points_allocation_changes(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)  # Initial: no staker points, 20 voter points
    setRipeRewardsConfig(True)

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # First update with initial config
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Time travel
    elapsed1 = 10
    boa.env.time_travel(blocks=elapsed1)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Change allocation config
    setAssetConfig(alpha_token, _stakersPointsAlloc=10, _voterPointsAlloc=10)  # Change to: 10 staker points, 10 voter points

    # Time travel and update with new config
    elapsed2 = 10
    boa.env.time_travel(blocks=elapsed2)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Check results
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.ripeStakerPoints == 10 * elapsed2  # New staker points
    assert ap.ripeVotePoints == 20 * elapsed1 + 10 * elapsed2  # Old + new voter points


def test_loot_deposit_points_large_numbers(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)
    setRipeRewardsConfig(True)

    # set mock prices - very high price
    price = 1000000 * EIGHTEEN_DECIMALS  # $1M per token
    mock_price_source.setPrice(alpha_token, price)

    # deposit - large amount
    deposit_amount = 1000000 * EIGHTEEN_DECIMALS  # 1M tokens
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # First update
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Time travel - long period
    elapsed = 1000
    boa.env.time_travel(blocks=elapsed)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Check results - verify no overflow
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    expected_points = (deposit_amount // ap.precision) * elapsed
    assert ap.balancePoints == expected_points
    assert ap.lastUsdValue == deposit_amount * price // EIGHTEEN_DECIMALS // EIGHTEEN_DECIMALS


def test_loot_deposit_points_complex_scenario(
    alpha_token,
    alpha_token_whale,
    delta_token,
    delta_token_whale,
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)  # 18 decimals
    setAssetConfig(delta_token, _stakersPointsAlloc=10, _voterPointsAlloc=10)  # 8 decimals, staker points
    setRipeRewardsConfig(True)

    # set mock prices
    alpha_price = 1 * EIGHTEEN_DECIMALS
    delta_price = 50_000 * EIGHTEEN_DECIMALS  # $50k like BTC
    mock_price_source.setPrice(alpha_token, alpha_price)
    mock_price_source.setPrice(delta_token, delta_price)

    # deposits - different users, different assets
    bob_alpha_deposit = 100 * EIGHTEEN_DECIMALS
    bob_delta_deposit = 1 * 10**8  # 1 BTC
    alice_alpha_deposit = 50 * EIGHTEEN_DECIMALS
    alice_delta_deposit = 2 * 10**8  # 2 BTC

    performDeposit(bob, bob_alpha_deposit, alpha_token, alpha_token_whale)
    performDeposit(bob, bob_delta_deposit, delta_token, delta_token_whale)
    performDeposit(alice, alice_alpha_deposit, alpha_token, alpha_token_whale)
    performDeposit(alice, alice_delta_deposit, delta_token, delta_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # First update for all combinations
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, delta_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, delta_token, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, delta_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, delta_token, sender=teller.address)

    # Check results
    # Alpha token
    ap_alpha = ledger.assetDepositPoints(vault_id, alpha_token)
    total_alpha = bob_alpha_deposit + alice_alpha_deposit
    assert ap_alpha.lastBalance == total_alpha // ap_alpha.precision
    assert ap_alpha.lastUsdValue == total_alpha // EIGHTEEN_DECIMALS
    assert ap_alpha.ripeVotePoints == 20 * elapsed
    assert ap_alpha.ripeStakerPoints == 0

    # Bravo token
    ap_bravo = ledger.assetDepositPoints(vault_id, delta_token)
    total_bravo = bob_delta_deposit + alice_delta_deposit
    assert ap_bravo.lastBalance == total_bravo // ap_bravo.precision
    assert ap_bravo.lastUsdValue == total_bravo * delta_price // EIGHTEEN_DECIMALS // EIGHTEEN_DECIMALS
    assert ap_bravo.ripeVotePoints == 10 * elapsed
    assert ap_bravo.ripeStakerPoints == 10 * elapsed

    # Check user points
    up_bob_alpha = ledger.userDepositPoints(bob, vault_id, alpha_token)
    up_bob_bravo = ledger.userDepositPoints(bob, vault_id, delta_token)
    up_alice_alpha = ledger.userDepositPoints(alice, vault_id, alpha_token)
    up_alice_bravo = ledger.userDepositPoints(alice, vault_id, delta_token)

    assert up_bob_alpha.balancePoints == (bob_alpha_deposit // ap_alpha.precision) * elapsed
    assert up_bob_bravo.balancePoints == (bob_delta_deposit // ap_bravo.precision) * elapsed
    assert up_alice_alpha.balancePoints == (alice_alpha_deposit // ap_alpha.precision) * elapsed
    assert up_alice_bravo.balancePoints == (alice_delta_deposit // ap_bravo.precision) * elapsed

    # Check global points
    gp = ledger.globalDepositPoints()
    total_usd_value = (total_alpha + total_bravo * delta_price // EIGHTEEN_DECIMALS) // EIGHTEEN_DECIMALS
    assert gp.lastUsdValue == total_usd_value
    assert gp.ripeGenPoints == total_usd_value * elapsed
    assert gp.ripeStakerPoints == 10 * elapsed  # Only from bravo token
    assert gp.ripeVotePoints == 30 * elapsed  # 20 from alpha + 10 from bravo


def test_loot_deposit_points_nft_asset(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20, _isNft=True)  # Set as NFT
    setRipeRewardsConfig(True)

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # First update
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Check results
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.precision == 1  # NFT precision should be 1
    assert ap.lastBalance == deposit_amount  # No precision division for NFTs
    assert ap.balancePoints == deposit_amount * elapsed


def test_loot_deposit_points_state_transitions(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)
    setRipeRewardsConfig(True)

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # First update with points enabled
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Time travel and update
    elapsed1 = 10
    boa.env.time_travel(blocks=elapsed1)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Disable points
    setRipeRewardsConfig(False)

    # Time travel and update with points disabled
    elapsed2 = 10
    boa.env.time_travel(blocks=elapsed2)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Re-enable points
    setRipeRewardsConfig(True)

    # Time travel and update with points re-enabled
    elapsed3 = 10
    boa.env.time_travel(blocks=elapsed3)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Check results
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.balancePoints == (deposit_amount // ap.precision) * (elapsed1 + elapsed3)  # No points during disabled period


def test_loot_deposit_points_small_numbers(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)
    setRipeRewardsConfig(True)

    # set mock prices - very small price
    price = 1 * 10**6  # $0.000001 per token
    mock_price_source.setPrice(alpha_token, price)

    # deposit - very small amount
    deposit_amount = 1 * 10**6  # 0.000001 tokens
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # First update
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Time travel - long period to accumulate meaningful points
    elapsed = 1000
    boa.env.time_travel(blocks=elapsed)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Check results
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    expected_points = (deposit_amount // ap.precision) * elapsed
    assert ap.balancePoints == expected_points
    assert ap.lastUsdValue == deposit_amount * price // EIGHTEEN_DECIMALS // EIGHTEEN_DECIMALS


def test_loot_deposit_points_multiple_vaults(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    rebase_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    vault_id1 = vault_book.getRegId(simple_erc20_vault)
    vault_id2 = vault_book.getRegId(rebase_erc20_vault)

    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[vault_id1, vault_id2], _stakersPointsAlloc=0, _voterPointsAlloc=20)
    setRipeRewardsConfig(True)

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # deposits in both vaults
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale, rebase_erc20_vault)

   
    # First update for both vaults
    lootbox.updateDepositPoints(bob, vault_id1, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(bob, vault_id2, rebase_erc20_vault, alpha_token, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update both vaults again
    lootbox.updateDepositPoints(bob, vault_id1, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(bob, vault_id2, rebase_erc20_vault, alpha_token, sender=teller.address)

    # Check results
    # First vault
    ap1 = ledger.assetDepositPoints(vault_id1, alpha_token)
    assert ap1.lastBalance == deposit_amount // ap1.precision
    assert ap1.balancePoints == (deposit_amount // ap1.precision) * elapsed

    # Second vault
    ap2 = ledger.assetDepositPoints(vault_id2, alpha_token)
    assert ap2.lastBalance == deposit_amount // ap2.precision
    assert ap2.balancePoints == (deposit_amount // ap2.precision) * elapsed

    # Check user points in both vaults
    up1 = ledger.userDepositPoints(bob, vault_id1, alpha_token)
    up2 = ledger.userDepositPoints(bob, vault_id2, alpha_token)
    assert up1.balancePoints == (deposit_amount // ap1.precision) * elapsed
    assert up2.balancePoints == (deposit_amount // ap2.precision) * elapsed

    # Check global points
    gp = ledger.globalDepositPoints()
    total_usd_value = (deposit_amount * 2) // EIGHTEEN_DECIMALS  # Both vaults
    assert gp.lastUsdValue == total_usd_value
    assert gp.ripeGenPoints == total_usd_value * elapsed


def test_loot_deposit_points_price_source_failures(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)
    setRipeRewardsConfig(True)

    # initial price
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # First update with normal price
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Time travel
    elapsed1 = 10
    boa.env.time_travel(blocks=elapsed1)

    # Set price to zero
    mock_price_source.setPrice(alpha_token, 0)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Verify lastUsdValue is zero when price is zero
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.lastUsdValue == 0

    # Time travel
    elapsed2 = 10
    boa.env.time_travel(blocks=elapsed2)

    # Set price back to normal
    mock_price_source.setPrice(alpha_token, price)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Check results
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.lastUsdValue == deposit_amount // EIGHTEEN_DECIMALS  # Should use new price
    assert ap.balancePoints == (deposit_amount // ap.precision) * (elapsed1 + elapsed2)


def test_loot_deposit_points_concurrent_updates(
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)
    setRipeRewardsConfig(True)

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # deposits
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(alice, deposit_amount, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # First update for both users
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update both users in the same block
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Check results
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    total_balance = deposit_amount * 2
    assert ap.lastBalance == total_balance // ap.precision
    assert ap.balancePoints == (total_balance // ap.precision) * elapsed

    # Check individual user points
    up_bob = ledger.userDepositPoints(bob, vault_id, alpha_token)
    up_alice = ledger.userDepositPoints(alice, vault_id, alpha_token)
    assert up_bob.balancePoints == (deposit_amount // ap.precision) * elapsed
    assert up_alice.balancePoints == (deposit_amount // ap.precision) * elapsed


def test_loot_deposit_points_rapid_updates(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)
    setRipeRewardsConfig(True)

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # First update
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Update multiple times in quick succession
    for _ in range(5):
        lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Check results
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.balancePoints == (deposit_amount // ap.precision) * elapsed  # Should only count elapsed blocks


def test_loot_deposit_points_extreme_elapsed(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=0, _voterPointsAlloc=20)
    setRipeRewardsConfig(True)

    # set mock prices
    price = 1 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)

    # deposit
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)

    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # First update
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Test very short elapsed time (1 block)
    boa.env.time_travel(blocks=1)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Test very long elapsed time
    boa.env.time_travel(blocks=1000000)  # 1M blocks
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Check results
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    expected_points = (deposit_amount // ap.precision) * (1 + 1000000)
    assert ap.balancePoints == expected_points
    assert ap.lastUsdValue == deposit_amount // EIGHTEEN_DECIMALS


# calc specific loot


def test_calc_specific_loot_basic(lootbox):
    """Test basic functionality with normal values"""
    # 50% user share, asset has 50% of global points
    asset_points_after, global_points_after, rewards_after, user_rewards = lootbox.calcSpecificLoot(
        50_00,  # 50% user share
        1000,   # asset points
        2000,   # global points
        100 * EIGHTEEN_DECIMALS,  # 100 tokens available
    )
    
    # Asset gets 50% of rewards (1000/2000), user gets 50% of that
    assert user_rewards == 25 * EIGHTEEN_DECIMALS
    assert rewards_after == 75 * EIGHTEEN_DECIMALS
    assert asset_points_after == 500  # 1000 - (1000 * 50%)
    assert global_points_after == 1500  # 2000 - 500


def test_calc_specific_loot_100_percent_user_share(lootbox):
    """Test when user owns 100% of the asset"""
    asset_points_after, global_points_after, rewards_after, user_rewards = lootbox.calcSpecificLoot(
        100_00,  # 100% user share
        1000,    # asset points
        2000,    # global points
        100 * EIGHTEEN_DECIMALS,  # rewards available
    )
    
    # User gets all of asset's share
    assert user_rewards == 50 * EIGHTEEN_DECIMALS
    assert rewards_after == 50 * EIGHTEEN_DECIMALS
    assert asset_points_after == 0  # All points consumed
    assert global_points_after == 1000  # 2000 - 1000


def test_calc_specific_loot_small_user_share(lootbox):
    """Test with very small user share"""
    asset_points_after, global_points_after, rewards_after, user_rewards = lootbox.calcSpecificLoot(
        1,  # 0.01% user share
        1000000,  # asset points
        2000000,  # global points
        100 * EIGHTEEN_DECIMALS,  # rewards available
    )
    
    # User should get 0.01% of 50% = 0.005 tokens
    expected_user_rewards = 100 * EIGHTEEN_DECIMALS * 1000000 // 2000000 * 1 // 100_00
    assert user_rewards == expected_user_rewards
    assert rewards_after == 100 * EIGHTEEN_DECIMALS - user_rewards
    
    # Points reduced should be minimal
    points_reduced = 1000000 * 1 // 100_00
    assert asset_points_after == 1000000 - points_reduced
    assert global_points_after == 2000000 - points_reduced


def test_calc_specific_loot_asset_points_exceed_global(lootbox):
    """Test the edge case where asset points > global points"""
    asset_points_after, global_points_after, rewards_after, user_rewards = lootbox.calcSpecificLoot(
        100_00,  # 100% user share
        71555000,  # asset points (greater than global)
        21690000,  # global points
        4880250000000000000,  # rewards available
    )
    
    # Asset points should be capped to global points
    # So user gets 100% of all rewards
    assert user_rewards == 4880250000000000000
    assert rewards_after == 0
    assert asset_points_after == 0  # All points consumed
    assert global_points_after == 0  # All points consumed


def test_calc_specific_loot_zero_values(lootbox):
    """Test all zero value edge cases"""
    # Zero asset points
    ap, gp, ra, ur = lootbox.calcSpecificLoot(50_00, 0, 1000, 100 * EIGHTEEN_DECIMALS)
    assert (ap, gp, ra, ur) == (0, 1000, 100 * EIGHTEEN_DECIMALS, 0)
    
    # Zero global points
    ap, gp, ra, ur = lootbox.calcSpecificLoot(50_00, 1000, 0, 100 * EIGHTEEN_DECIMALS)
    assert (ap, gp, ra, ur) == (1000, 0, 100 * EIGHTEEN_DECIMALS, 0)
    
    # Zero rewards
    ap, gp, ra, ur = lootbox.calcSpecificLoot(50_00, 1000, 2000, 0)
    assert (ap, gp, ra, ur) == (1000, 2000, 0, 0)
    
    # Zero user share
    ap, gp, ra, ur = lootbox.calcSpecificLoot(0, 1000, 2000, 100 * EIGHTEEN_DECIMALS)
    assert (ap, gp, ra, ur) == (1000, 2000, 100 * EIGHTEEN_DECIMALS, 0)


def test_calc_specific_loot_precision_edge_cases(lootbox):
    """Test precision edge cases that might cause rounding issues"""
    # Test case where division might lose precision
    asset_points_after, global_points_after, rewards_after, user_rewards = lootbox.calcSpecificLoot(
        33_33,  # 33.33% user share
        3333,   # asset points
        10000,  # global points
        100 * EIGHTEEN_DECIMALS,  # rewards available
    )
    
    # Asset gets 3333/10000 of rewards, user gets 33.33% of that
    asset_rewards = 100 * EIGHTEEN_DECIMALS * 3333 // 10000
    expected_user_rewards = asset_rewards * 33_33 // 100_00
    assert user_rewards == expected_user_rewards
    
    # Points reduction calculation
    points_to_reduce = 3333 * 33_33 // 100_00
    assert asset_points_after == 3333 - points_to_reduce
    assert global_points_after == 10000 - points_to_reduce


def test_calc_specific_loot_maximum_values(lootbox):
    """Test with maximum uint256 values to check for overflows"""
    # Use large but safe values that won't overflow in calculations
    large_points = 10**18
    large_rewards = 10**30
    
    asset_points_after, global_points_after, rewards_after, user_rewards = lootbox.calcSpecificLoot(
        50_00,  # 50% user share
        large_points,
        large_points * 2,
        large_rewards,
    )
    
    # User should get 25% of total rewards (50% of 50%)
    assert user_rewards == large_rewards // 4
    assert rewards_after == large_rewards * 3 // 4
    assert asset_points_after == large_points // 2
    assert global_points_after == large_points * 3 // 2


def test_calc_specific_loot_user_gets_no_rewards(lootbox):
    """Test case where user share is so small they get 0 rewards"""
    asset_points_after, global_points_after, rewards_after, user_rewards = lootbox.calcSpecificLoot(
        1,  # 0.01% user share
        100,  # small asset points
        1000000,  # large global points
        100,  # small rewards available
    )
    
    # User rewards should round down to 0
    assert user_rewards == 0
    assert rewards_after == 100
    assert asset_points_after == 100  # No change
    assert global_points_after == 1000000  # No change


def test_calc_specific_loot_equal_asset_and_global_points(lootbox):
    """Test when asset points equal global points"""
    asset_points_after, global_points_after, rewards_after, user_rewards = lootbox.calcSpecificLoot(
        50_00,  # 50% user share
        1000,   # asset points
        1000,   # global points (same as asset)
        100 * EIGHTEEN_DECIMALS,  # rewards available
    )
    
    # Asset gets 100% of rewards, user gets 50% of that
    assert user_rewards == 50 * EIGHTEEN_DECIMALS
    assert rewards_after == 50 * EIGHTEEN_DECIMALS
    assert asset_points_after == 500
    assert global_points_after == 500


def test_calc_specific_loot_fractional_percentages(lootbox):
    """Test various fractional percentage scenarios"""
    test_cases = [
        (1, "0.01%"),      # 0.01%
        (10, "0.1%"),      # 0.1%
        (100, "1%"),       # 1%
        (1000, "10%"),     # 10%
        (2500, "25%"),     # 25%
        (7550, "75.5%"),   # 75.5%
        (9999, "99.99%"),  # 99.99%
    ]
    
    for user_share, description in test_cases:
        asset_points_after, global_points_after, rewards_after, user_rewards = lootbox.calcSpecificLoot(
            user_share,
            100000,  # asset points
            200000,  # global points
            1000 * EIGHTEEN_DECIMALS,  # rewards available
        )
        
        # Asset gets 50% of total rewards
        asset_rewards = 500 * EIGHTEEN_DECIMALS
        expected_user_rewards = asset_rewards * user_share // 100_00
        
        # Verify calculations
        assert user_rewards == expected_user_rewards, f"Failed for {description}"
        assert rewards_after == 1000 * EIGHTEEN_DECIMALS - user_rewards
        
        # Verify points reduction
        points_to_reduce = 100000 * user_share // 100_00
        assert asset_points_after == 100000 - points_to_reduce
        assert global_points_after == 200000 - points_to_reduce


def test_calc_specific_loot_consecutive_calls(lootbox):
    """Test multiple consecutive calls to simulate real usage"""
    # Initial state
    asset_points = 1000000
    global_points = 2000000
    rewards_available = 1000 * EIGHTEEN_DECIMALS
    
    # User 1 claims 25%
    ap1, gp1, ra1, ur1 = lootbox.calcSpecificLoot(
        25_00,  # 25% share
        asset_points,
        global_points,
        rewards_available,
    )
    
    # User 2 claims 30% of remaining
    ap2, gp2, ra2, ur2 = lootbox.calcSpecificLoot(
        30_00,  # 30% share
        ap1,
        gp1,
        ra1,
    )
    
    # User 3 claims 100% of remaining
    ap3, gp3, ra3, ur3 = lootbox.calcSpecificLoot(
        100_00,  # 100% share
        ap2,
        gp2,
        ra2,
    )
    
    # Verify total rewards distributed
    total_distributed = ur1 + ur2 + ur3
    assert total_distributed <= rewards_available
    
    # Verify final state
    assert ap3 == 0  # All asset points consumed
    # The remaining rewards should be significant due to the way points are reduced
    assert ra3 == rewards_available - total_distributed


def test_calc_specific_loot_boundary_values(lootbox):
    """Test boundary values for all parameters"""
    # Test with 1 wei values - user share is 0.01% which rounds to 0
    ap, gp, ra, ur = lootbox.calcSpecificLoot(1, 1, 1, 1)
    assert ur == 0  # 1 * 1 // 1 * 1 // 10000 = 0
    assert (ap, gp, ra) == (1, 1, 1)  # No change since no rewards
    
    # Test with 100% user share and 1 wei values
    ap, gp, ra, ur = lootbox.calcSpecificLoot(100_00, 1, 1, 1)
    assert ur == 1  # 100% of 1
    assert (ap, gp, ra) == (0, 0, 0)
    
    # Test with maximum percentage
    ap, gp, ra, ur = lootbox.calcSpecificLoot(
        100_00,  # 100%
        1000,
        1000,
        1000,
    )
    assert ur == 1000
    assert (ap, gp, ra) == (0, 0, 0)