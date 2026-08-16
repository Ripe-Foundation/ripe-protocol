import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT


PRECISION_18 = 10 ** 9
# Price that makes one normalization unit worth $2 so a sub-precision
# residual still produced a nonzero pre-fix lastUsdValue.
DUST_VISIBLE_PRICE = 2 * 10 ** 27


def _usd_dollars(price_desk, asset, amount):
    return price_desk.getUsdValue(asset, amount) // EIGHTEEN_DECIMALS


def _configure_gen_rewards(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, asset, vault_id):
    setGeneralConfig()
    setAssetConfig(
        asset,
        _vaultIds=[vault_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    setRipeRewardsConfig(
        True,
        10,
        0,
        0,
        0,
        HUNDRED_PERCENT,
    )


def test_sc24_fail_first_shares_dust_funded_without_holder_points(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    rebase_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    price_desk,
):
    """Pre-fix formula funds gen rewards from the full vault while dust lastBalance is 0."""
    vault_id = vault_book.getRegId(rebase_erc20_vault)
    _configure_gen_rewards(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, DUST_VISIBLE_PRICE)

    dust_amount = PRECISION_18 - 1
    performDeposit(bob, dust_amount, alpha_token, alpha_token_whale, rebase_erc20_vault)

    raw_share = rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token)
    assert raw_share > 0
    pre_fix_last_balance = raw_share // PRECISION_18
    assert pre_fix_last_balance == 0

    vault_amount = rebase_erc20_vault.getTotalAmountForVault(alpha_token)
    pre_fix_usd = _usd_dollars(price_desk, alpha_token, vault_amount)
    assert pre_fix_usd > 0

    lootbox.updateDepositPoints(
        bob,
        vault_id,
        rebase_erc20_vault,
        alpha_token,
        sender=teller.address,
    )
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.precision == PRECISION_18
    assert up.lastBalance == 0
    assert ap.lastBalance == 0
    assert ap.lastUsdValue == 0
    assert ap.lastUsdValue != pre_fix_usd


def test_sc24_dust_is_excluded_from_funded_reward_value(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    rebase_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    switchboard_alpha,
):
    vault_id = vault_book.getRegId(rebase_erc20_vault)
    _configure_gen_rewards(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, DUST_VISIBLE_PRICE)
    ledger.setRipeAvailForRewards(1_000 * EIGHTEEN_DECIMALS, sender=switchboard_alpha.address)

    performDeposit(bob, PRECISION_18 - 1, alpha_token, alpha_token_whale, rebase_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)

    elapsed = 20
    boa.env.time_travel(blocks=elapsed)
    lootbox.updateDepositPoints(bob, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)

    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    gp = ledger.globalDepositPoints()
    assert ap.lastUsdValue == 0
    assert ap.ripeGenPoints == 0
    assert gp.ripeGenPoints == 0
    assert up.balancePoints == 0
    assert ap.balancePoints == 0
    assert lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token) == 0
    assert teller.claimLoot(bob, False, sender=bob) == 0


def test_sc24_splitting_cannot_increase_aggregate_reward_weight(
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    sally,
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
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _configure_gen_rewards(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, DUST_VISIBLE_PRICE)

    whole = 2 * PRECISION_18
    performDeposit(bob, whole, alpha_token, alpha_token_whale, simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    whole_balance = ledger.userDepositPoints(bob, vault_id, alpha_token).lastBalance
    assert whole_balance == 2
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue > 0

    performDeposit(alice, PRECISION_18, alpha_token, alpha_token_whale, simple_erc20_vault)
    performDeposit(sally, PRECISION_18, alpha_token, alpha_token_whale, simple_erc20_vault)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(sally, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    split_exact = (
        ledger.userDepositPoints(alice, vault_id, alpha_token).lastBalance
        + ledger.userDepositPoints(sally, vault_id, alpha_token).lastBalance
    )
    assert split_exact == whole_balance

    dust_a = boa.env.generate_address("sc24-dust-a")
    dust_b = boa.env.generate_address("sc24-dust-b")
    performDeposit(dust_a, PRECISION_18 - 1, alpha_token, alpha_token_whale, simple_erc20_vault)
    performDeposit(dust_b, PRECISION_18 + 1, alpha_token, alpha_token_whale, simple_erc20_vault)
    lootbox.updateDepositPoints(dust_a, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(dust_b, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    split_round = (
        ledger.userDepositPoints(dust_a, vault_id, alpha_token).lastBalance
        + ledger.userDepositPoints(dust_b, vault_id, alpha_token).lastBalance
    )
    assert split_round <= whole_balance
    assert ledger.userDepositPoints(dust_a, vault_id, alpha_token).lastBalance == 0
    assert ledger.userDepositPoints(dust_b, vault_id, alpha_token).lastBalance == 1


def test_sc24_normalization_boundaries_and_multi_block_claim(
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    sally,
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
    switchboard_alpha,
    price_desk,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _configure_gen_rewards(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, DUST_VISIBLE_PRICE)
    ledger.setRipeAvailForRewards(1_000 * EIGHTEEN_DECIMALS, sender=switchboard_alpha.address)

    performDeposit(bob, PRECISION_18 - 1, alpha_token, alpha_token_whale, simple_erc20_vault)
    performDeposit(alice, PRECISION_18, alpha_token, alpha_token_whale, simple_erc20_vault)
    performDeposit(sally, PRECISION_18 + 1, alpha_token, alpha_token_whale, simple_erc20_vault)
    for user in (bob, alice, sally):
        lootbox.updateDepositPoints(user, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    assert ledger.userDepositPoints(bob, vault_id, alpha_token).lastBalance == 0
    assert ledger.userDepositPoints(alice, vault_id, alpha_token).lastBalance == 1
    assert ledger.userDepositPoints(sally, vault_id, alpha_token).lastBalance == 1

    eligible = 2 * PRECISION_18
    expected_usd = _usd_dollars(price_desk, alpha_token, eligible)
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.lastBalance == 2
    assert ap.lastUsdValue == expected_usd
    assert expected_usd > 0

    elapsed = 15
    boa.env.time_travel(blocks=elapsed)
    for user in (bob, alice, sally):
        lootbox.updateDepositPoints(user, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 0
    assert ledger.userDepositPoints(alice, vault_id, alpha_token).balancePoints == elapsed
    assert ledger.userDepositPoints(sally, vault_id, alpha_token).balancePoints == elapsed
    assert ledger.assetDepositPoints(vault_id, alpha_token).ripeGenPoints == expected_usd * elapsed

    assert lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token) == 0
    assert teller.claimLoot(alice, False, sender=alice) > 0
    assert teller.claimLoot(sally, False, sender=sally) > 0
    assert teller.claimLoot(bob, False, sender=bob) == 0


def test_sc24_normal_position_economics_unchanged(
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
    switchboard_alpha,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _configure_gen_rewards(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    ledger.setRipeAvailForRewards(1_000 * EIGHTEEN_DECIMALS, sender=switchboard_alpha.address)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale, simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert ap.precision == PRECISION_18
    assert up.lastBalance == deposit_amount // PRECISION_18
    assert ap.lastBalance == deposit_amount // PRECISION_18
    assert ap.lastUsdValue == deposit_amount // EIGHTEEN_DECIMALS

    elapsed = 20
    boa.env.time_travel(blocks=elapsed)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == (deposit_amount // PRECISION_18) * elapsed
    assert ap.balancePoints == (deposit_amount // PRECISION_18) * elapsed
    assert ap.ripeGenPoints == (deposit_amount // EIGHTEEN_DECIMALS) * elapsed
    assert teller.claimLoot(bob, False, sender=bob) > 0


def test_sc24_ripegov_already_normalized_share_and_vault_total_usd(
    alternate_ripe_gov_vault,
    registerVault,
    mission_control,
    switchboard_alpha,
    ripe_token,
    whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    teller,
    lootbox,
    ledger,
    price_desk,
):
    core_id = registerVault(alternate_ripe_gov_vault, "SC-24 RipeGov")
    setGeneralConfig()
    setAssetConfig(
        ripe_token,
        _vaultIds=[core_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    setRipeRewardsConfig(True, 10, 0, 0, 0, HUNDRED_PERCENT)
    mock_price_source.setPrice(ripe_token, EIGHTEEN_DECIMALS)
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        100_00,
        False,
        (100, 1_000, 100_00, False, 0),
        sender=switchboard_alpha.address,
    )
    mission_control.setCoreRipeGovVaultId(core_id, sender=switchboard_alpha.address)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    ripe_token.transfer(bob, deposit_amount, sender=whale)
    ripe_token.approve(teller, deposit_amount, sender=bob)
    teller.depositIntoGovVault(ripe_token, deposit_amount, 100, bob, sender=bob)

    user_points, asset_points, _ = lootbox.getLatestDepositPoints(bob, core_id, ripe_token)
    expected_gov_share = (
        alternate_ripe_gov_vault.userGovData(bob, ripe_token).lastShares // EIGHTEEN_DECIMALS
    )
    assert asset_points.precision == PRECISION_18
    assert user_points.lastBalance == expected_gov_share
    assert user_points.lastBalance != deposit_amount // PRECISION_18

    lootbox.updateDepositPoints(
        bob,
        core_id,
        alternate_ripe_gov_vault,
        ripe_token,
        sender=teller.address,
    )
    ap = ledger.assetDepositPoints(core_id, ripe_token)
    vault_amount = alternate_ripe_gov_vault.getTotalAmountForVault(ripe_token)
    assert ap.lastUsdValue == _usd_dollars(price_desk, ripe_token, vault_amount)
    assert ap.lastUsdValue != (user_points.lastBalance * PRECISION_18) // EIGHTEEN_DECIMALS
