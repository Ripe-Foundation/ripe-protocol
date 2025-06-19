import boa

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
