import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT, ZERO_ADDRESS


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
    unsplit_usd = ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue
    assert whole_balance == 2
    assert unsplit_usd > 0

    performDeposit(alice, PRECISION_18, alpha_token, alpha_token_whale, simple_erc20_vault)
    performDeposit(sally, PRECISION_18, alpha_token, alpha_token_whale, simple_erc20_vault)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(sally, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    split_exact = (
        ledger.userDepositPoints(alice, vault_id, alpha_token).lastBalance
        + ledger.userDepositPoints(sally, vault_id, alpha_token).lastBalance
    )
    assert split_exact == whole_balance
    split_usd = (
        ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue - unsplit_usd
    )
    assert split_usd == unsplit_usd

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
    after_dust_usd = ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue
    assert after_dust_usd == unsplit_usd + split_usd + (unsplit_usd // 2)


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


def test_sc24_shares_vault_positive_rebase_funds_underlying_value(
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
    vault_id = vault_book.getRegId(rebase_erc20_vault)
    _configure_gen_rewards(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale, rebase_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == (
        rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token) // EIGHTEEN_DECIMALS
    )

    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=alpha_token_whale)
    lootbox.updateDepositPoints(bob, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)

    user_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    vault_amount = rebase_erc20_vault.getTotalAmountForVault(alpha_token)
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert user_amount > deposit_amount
    assert ap.lastUsdValue == user_amount // EIGHTEEN_DECIMALS
    assert ap.lastUsdValue == _usd_dollars(price_desk, alpha_token, user_amount)
    assert ap.lastUsdValue != deposit_amount // EIGHTEEN_DECIMALS
    assert ap.lastUsdValue <= vault_amount // EIGHTEEN_DECIMALS
    assert ap.lastUsdValue >= vault_amount // EIGHTEEN_DECIMALS - 1


def test_sc24_shares_vault_negative_rebase_reduces_funded_value(
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
):
    vault_id = vault_book.getRegId(rebase_erc20_vault)
    _configure_gen_rewards(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale, rebase_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)

    loss = deposit_amount // 2
    alpha_token.transfer(alpha_token_whale, loss, sender=rebase_erc20_vault.address)
    lootbox.updateDepositPoints(bob, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)

    user_amount = rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert user_amount < deposit_amount
    assert ap.lastUsdValue == user_amount // EIGHTEEN_DECIMALS
    assert ap.lastUsdValue < deposit_amount // EIGHTEEN_DECIMALS


def test_sc24_shares_vault_multiple_holders_rebase_and_split_do_not_inflate(
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
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
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    ledger.setRipeAvailForRewards(1_000 * EIGHTEEN_DECIMALS, sender=switchboard_alpha.address)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale, rebase_erc20_vault)
    performDeposit(alice, deposit_amount, alpha_token, alpha_token_whale, rebase_erc20_vault)
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=alpha_token_whale)
    lootbox.updateDepositPoints(bob, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)

    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    vault_amount = rebase_erc20_vault.getTotalAmountForVault(alpha_token)
    holder_sum = (
        rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token)
        + rebase_erc20_vault.getTotalAmountForUser(alice, alpha_token)
    )
    assert ap.lastUsdValue <= vault_amount // EIGHTEEN_DECIMALS
    assert ap.lastUsdValue == min(holder_sum, vault_amount) // EIGHTEEN_DECIMALS
    assert ap.lastUsdValue > (2 * deposit_amount) // EIGHTEEN_DECIMALS - 2
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).lastBalance > 0
    assert ledger.userDepositPoints(alice, vault_id, alpha_token).lastBalance > 0
    assert (
        ledger.userDepositPoints(bob, vault_id, alpha_token).lastBalance
        + ledger.userDepositPoints(alice, vault_id, alpha_token).lastBalance
        == ap.lastBalance
    )


def test_sc24_full_exit_funds_remaining_vault_not_share_units(
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
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
    """A fully exited holder must not switch funding back to share units."""
    vault_id = vault_book.getRegId(rebase_erc20_vault)
    _configure_gen_rewards(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale, rebase_erc20_vault)
    performDeposit(alice, deposit_amount, alpha_token, alpha_token_whale, rebase_erc20_vault)
    alpha_token.transfer(rebase_erc20_vault, deposit_amount, sender=alpha_token_whale)
    lootbox.updateDepositPoints(bob, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)
    both_usd = ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue
    assert both_usd <= rebase_erc20_vault.getTotalAmountForVault(alpha_token) // EIGHTEEN_DECIMALS
    assert both_usd > (2 * deposit_amount) // EIGHTEEN_DECIMALS - 2

    withdrawn = teller.withdraw(
        alpha_token,
        rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token),
        bob,
        rebase_erc20_vault,
        sender=bob,
    )
    assert withdrawn > 0
    assert rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0

    remaining = rebase_erc20_vault.getTotalAmountForUser(alice, alpha_token)
    vault_amount = rebase_erc20_vault.getTotalAmountForVault(alpha_token)
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    share_unit_guess = (
        ledger.userDepositPoints(alice, vault_id, alpha_token).lastBalance
        * ap.precision
    )
    assert remaining > deposit_amount
    assert ap.lastUsdValue <= vault_amount // EIGHTEEN_DECIMALS
    assert ap.lastUsdValue >= remaining // EIGHTEEN_DECIMALS - 1
    assert ap.lastUsdValue > deposit_amount // EIGHTEEN_DECIMALS
    assert share_unit_guess // EIGHTEEN_DECIMALS == deposit_amount // EIGHTEEN_DECIMALS
    assert ap.lastUsdValue != share_unit_guess // EIGHTEEN_DECIMALS


def test_sc24_full_exit_does_not_reinclude_subprecision_dust(
    charlie_token,
    charlie_token_whale,
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
    switchboard_delta,
):
    """A no-rate checkpoint must not restore dust the last holder pass excluded."""
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _configure_gen_rewards(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, charlie_token, vault_id)
    mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)

    whole = 10 ** 6
    dust = whole - 1
    performDeposit(alice, 100 * whole, charlie_token, charlie_token_whale)
    performDeposit(bob, 5 * whole, charlie_token, charlie_token_whale)
    dust_users = [boa.env.generate_address(f"sc24-dust-{i}") for i in range(10)]
    for user in dust_users:
        performDeposit(user, dust, charlie_token, charlie_token_whale)

    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, charlie_token, sender=teller.address)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, charlie_token, sender=teller.address)
    for user in dust_users:
        lootbox.updateDepositPoints(user, vault_id, simple_erc20_vault, charlie_token, sender=teller.address)

    before = ledger.assetDepositPoints(vault_id, charlie_token)
    vault_before = simple_erc20_vault.getTotalAmountForVault(charlie_token)
    assert before.precision == whole
    assert before.lastBalance == 105
    assert before.lastUsdValue == 105
    assert vault_before > 105 * whole
    assert before.lastUsdValue < vault_before // whole

    withdrawn = teller.withdraw(
        charlie_token,
        simple_erc20_vault.getTotalAmountForUser(alice, charlie_token),
        alice,
        simple_erc20_vault,
        sender=alice,
    )
    assert withdrawn == 100 * whole

    after_exit = ledger.assetDepositPoints(vault_id, charlie_token)
    vault_after = simple_erc20_vault.getTotalAmountForVault(charlie_token)
    assert after_exit.lastBalance == 5
    assert after_exit.lastUsdValue == 5
    assert after_exit.lastUsdValue != vault_after // whole
    assert after_exit.lastUsdValue < vault_after // whole

    lootbox.resetAssetPoints(charlie_token, vault_id, sender=switchboard_delta.address)
    after_reset = ledger.assetDepositPoints(vault_id, charlie_token)
    assert after_reset.lastUsdValue == 5
    assert after_reset.lastUsdValue < (
        simple_erc20_vault.getTotalAmountForVault(charlie_token) // whole
    )


def test_sc24_custody_shortfall_zeros_reward_usd_on_first_checkpoint(
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
    """A 1-wei custody deficit must stop gen-reward funding immediately."""
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _configure_gen_rewards(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(alice, 50 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue > 0
    alice_balance_before = ledger.userDepositPoints(alice, vault_id, alpha_token).lastBalance

    alpha_token.transfer(alpha_token_whale, 1, sender=simple_erc20_vault.address)
    assert simple_erc20_vault.getTotalAmountForVault(alpha_token) == 0

    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.lastUsdValue == 0
    assert ledger.userDepositPoints(alice, vault_id, alpha_token).lastBalance == alice_balance_before


def test_sc24_six_decimal_min_deposit_does_not_fund_rewards(
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
    """6-dec assets have precision 1e6 (one token). A sub-token deposit is zero weight."""
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _configure_gen_rewards(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, charlie_token, vault_id)
    mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)

    dust = 10 ** 6 - 1
    performDeposit(bob, dust, charlie_token, charlie_token_whale)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, charlie_token, sender=teller.address)

    ap = ledger.assetDepositPoints(vault_id, charlie_token)
    up = ledger.userDepositPoints(bob, vault_id, charlie_token)
    assert ap.precision == 10 ** 6
    assert up.lastBalance == 0
    assert ap.lastBalance == 0
    assert ap.lastUsdValue == 0

    whole = 10 ** 6
    performDeposit(bob, whole, charlie_token, charlie_token_whale)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, charlie_token, sender=teller.address)
    ap = ledger.assetDepositPoints(vault_id, charlie_token)
    assert ledger.userDepositPoints(bob, vault_id, charlie_token).lastBalance == 1
    assert ap.lastBalance == 1
    assert ap.lastUsdValue == 1


def test_sc24_dust_shares_holder_cannot_zero_aggregate_funding(
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
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
):
    """A dust SharesVault holder must not value the whole book at their rounded-zero amount."""
    vault_id = vault_book.getRegId(rebase_erc20_vault)
    _configure_gen_rewards(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    performDeposit(alice, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale, rebase_erc20_vault)
    performDeposit(bob, 1, alpha_token, alpha_token_whale, rebase_erc20_vault)
    lootbox.updateDepositPoints(alice, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)
    funded = ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue
    assert funded > 0

    leftover = EIGHTEEN_DECIMALS
    drain = alpha_token.balanceOf(rebase_erc20_vault) - leftover
    alpha_token.transfer(alpha_token_whale, drain, sender=rebase_erc20_vault.address)
    assert rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token) > 0
    assert rebase_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert rebase_erc20_vault.getTotalAmountForUser(alice, alpha_token) > 0

    lootbox.updateDepositPoints(bob, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    vault_usd = rebase_erc20_vault.getTotalAmountForVault(alpha_token) // EIGHTEEN_DECIMALS
    assert leftover == EIGHTEEN_DECIMALS
    assert vault_usd == 1
    assert ap.lastUsdValue == vault_usd
    assert ap.lastUsdValue != 0


def test_sc24_nonzero_staker_alloc_does_not_fund_gen_bucket(
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
    vault_id = vault_book.getRegId(simple_erc20_vault)
    setGeneralConfig()
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_id],
        _stakersPointsAlloc=25_00,
        _voterPointsAlloc=0,
    )
    setRipeRewardsConfig(True, 10, 0, 0, 0, HUNDRED_PERCENT)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 0
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).lastBalance > 0


def test_sc24_multi_holder_valuation_is_caller_independent(
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
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
):
    vault_id = vault_book.getRegId(rebase_erc20_vault)
    _configure_gen_rewards(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(alice, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale, rebase_erc20_vault)
    performDeposit(bob, 1, alpha_token, alpha_token_whale, rebase_erc20_vault)
    leftover = EIGHTEEN_DECIMALS
    alpha_token.transfer(
        alpha_token_whale,
        alpha_token.balanceOf(rebase_erc20_vault) - leftover,
        sender=rebase_erc20_vault.address,
    )
    lootbox.updateDepositPoints(alice, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)
    alice_usd = ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue
    lootbox.updateDepositPoints(bob, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == alice_usd
    assert alice_usd == leftover // EIGHTEEN_DECIMALS


def test_sc24_empty_book_does_not_probe_or_use_vault_total(
    alpha_token,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    ledger,
    lootbox,
    teller,
):
    # lastBalance is empty, but a converter would return 10 tokens if probed.
    mock = boa.load("contracts/mock/MockLootboxVaultAccounting.vy")
    vault_id = registerVault(mock, "sc24 empty book dust")
    _configure_gen_rewards(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock.configure(10 * EIGHTEEN_DECIMALS, 1, 0, 0, 10 * EIGHTEEN_DECIMALS)
    lootbox.updateDepositPoints(
        ZERO_ADDRESS,
        vault_id,
        mock,
        alpha_token,
        sender=teller.address,
    )
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastBalance == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 0


def test_sc24_share_decimal_offset_matches_vault_modules():
    import re
    from pathlib import Path

    def _const(path, name):
        text = Path(path).read_text()
        match = re.search(
            rf"{name}:\s*constant\(uint256\)\s*=\s*([^\n#]+)",
            text,
        )
        assert match, name
        expr = match.group(1).strip().replace("_", "")
        if "**" in expr:
            base, exp = expr.split("**")
            return int(base) ** int(exp)
        return int(expr)

    assert _const("contracts/core/Lootbox.vy", "SHARE_DECIMAL_OFFSET") == 10 ** 8
    assert _const("contracts/vaults/modules/SharesVault.vy", "DECIMAL_OFFSET") == 10 ** 8
    assert _const("contracts/vaults/modules/StabVault.vy", "DECIMAL_OFFSET") == 10 ** 8
