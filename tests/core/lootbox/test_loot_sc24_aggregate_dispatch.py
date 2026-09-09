import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT, ZERO_ADDRESS


PRECISION_18 = 10 ** 9
SHARE_OFFSET = 10 ** 8
# lastBalance = loot // precision = 10e18 / 1e9 = 10e9
# eligibleNominal = 10e9 * 1e9 = 10e18 → $10 if priced at $1
LOOT_TEN_USD = 10 * EIGHTEEN_DECIMALS
USABLE_TEN = 10 * EIGHTEEN_DECIMALS
NOMINAL_USD = 10


def _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, asset, vault_id):
    setGeneralConfig()
    setAssetConfig(
        asset,
        _vaultIds=[vault_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=1,
    )
    setAssetConfig(
        asset,
        _vaultIds=[vault_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    setRipeRewardsConfig(True, 10, 0, 0, 0, HUNDRED_PERCENT)


def _mock_vault(registerVault, name="sc24 mock vault"):
    mock = boa.load("contracts/mock/MockLootboxVaultAccounting.vy")
    vault_id = registerVault(mock, name)
    return mock, vault_id


def test_sc24_shares_donation_collision_still_uses_conversion(
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
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    deposit = EIGHTEEN_DECIMALS
    performDeposit(bob, deposit, alpha_token, alpha_token_whale, rebase_erc20_vault)
    donation = deposit * (SHARE_OFFSET - 1)
    alpha_token.transfer(rebase_erc20_vault, donation, sender=alpha_token_whale)
    usable = rebase_erc20_vault.getTotalAmountForVault(alpha_token)
    assert rebase_erc20_vault.totalBalances(alpha_token) == usable
    lootbox.updateDepositPoints(bob, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    nominal = ap.lastBalance * ap.precision
    assert ap.lastBalance > 0
    assert ap.lastUsdValue >= usable // EIGHTEEN_DECIMALS - 1
    assert ap.lastUsdValue <= usable // EIGHTEEN_DECIMALS
    assert ap.lastUsdValue != nominal // EIGHTEEN_DECIMALS
    assert ap.lastUsdValue > nominal // EIGHTEEN_DECIMALS


def test_sc24_exact_32_byte_zero_does_not_use_nominal(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    ledger,
    lootbox,
    teller,
):
    mock, vault_id = _mock_vault(registerVault)
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock.configure(USABLE_TEN, 1, LOOT_TEN_USD, 4, 0)
    lootbox.updateDepositPoints(bob, vault_id, mock, alpha_token, sender=teller.address)
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).lastBalance == LOOT_TEN_USD // PRECISION_18
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue != NOMINAL_USD


def test_sc24_short_shares_response_funds_zero_not_nominal(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    ledger,
    lootbox,
    teller,
):
    mock = boa.load("contracts/mock/MockLootboxVaultVoidReturn.vy")
    vault_id = registerVault(mock, "sc24 void return")
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock.configure(USABLE_TEN, USABLE_TEN, LOOT_TEN_USD)
    lootbox.updateDepositPoints(bob, vault_id, mock, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue != NOMINAL_USD


def test_sc24_overlong_shares_response_funds_zero_not_nominal(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    ledger,
    lootbox,
    teller,
):
    mock = boa.load("contracts/mock/MockLootboxVaultMalformed.vy")
    vault_id = registerVault(mock, "sc24 overlong")
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock.configure(USABLE_TEN, USABLE_TEN, LOOT_TEN_USD, b"\xff" * 33)
    lootbox.updateDepositPoints(bob, vault_id, mock, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue != NOMINAL_USD


def test_sc24_unavailable_selector_with_nominal_equality_uses_fallback(
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
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, 10 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    amount = simple_erc20_vault.getTotalAmountForVault(alpha_token)
    assert simple_erc20_vault.totalBalances(alpha_token) == amount
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == amount // EIGHTEEN_DECIMALS


def test_sc24_unavailable_selector_with_mismatch_funds_zero_not_nominal(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    ledger,
    lootbox,
    teller,
):
    mock = boa.load("contracts/mock/MockLootboxVaultNoConverter.vy")
    vault_id = registerVault(mock, "sc24 no converter")
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock.configure(USABLE_TEN, 7, LOOT_TEN_USD)
    lootbox.updateDepositPoints(bob, vault_id, mock, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue != NOMINAL_USD


def test_sc24_missing_total_balances_funds_zero_without_revert(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    ledger,
    lootbox,
    teller,
):
    mock = boa.load("contracts/mock/MockLootboxVaultNoTotals.vy")
    vault_id = registerVault(mock, "sc24 no totals")
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock.configure(USABLE_TEN, LOOT_TEN_USD)
    lootbox.updateDepositPoints(bob, vault_id, mock, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue != NOMINAL_USD


def test_sc24_reverting_total_balances_funds_zero_without_revert(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    ledger,
    lootbox,
    teller,
):
    mock, vault_id = _mock_vault(registerVault)
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    # Mode 5 fails sharesToAmount and totalBalances so the fallback is reached
    # and must fund zero instead of reverting the checkpoint.
    mock.configure(USABLE_TEN, USABLE_TEN, LOOT_TEN_USD, 5, 0)
    lootbox.updateDepositPoints(bob, vault_id, mock, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue != NOMINAL_USD


def test_sc24_short_total_balances_funds_zero_without_revert(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    ledger,
    lootbox,
    teller,
):
    mock = boa.load("contracts/mock/MockLootboxVaultTotalsVoid.vy")
    vault_id = registerVault(mock, "sc24 totals void")
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock.configure(USABLE_TEN, LOOT_TEN_USD)
    lootbox.updateDepositPoints(bob, vault_id, mock, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue != NOMINAL_USD


def test_sc24_overlong_total_balances_funds_zero_without_revert(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    ledger,
    lootbox,
    teller,
):
    mock = boa.load("contracts/mock/MockLootboxVaultTotalsMalformed.vy")
    vault_id = registerVault(mock, "sc24 totals overlong")
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock.configure(USABLE_TEN, LOOT_TEN_USD, b"\xff" * 33)
    lootbox.updateDepositPoints(bob, vault_id, mock, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue != NOMINAL_USD


def test_sc24_checkpoint_then_basic_withdrawal_stays_live(
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
    lootbox,
    teller,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    amount = 10 * EIGHTEEN_DECIMALS
    performDeposit(bob, amount, alpha_token, alpha_token_whale)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    withdrawn = teller.withdraw(alpha_token, amount // 2, bob, simple_erc20_vault, sender=bob)
    assert withdrawn == amount // 2


def test_sc24_reverting_conversion_with_equality_is_nominal_compatible(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    ledger,
    lootbox,
    teller,
):
    mock, vault_id = _mock_vault(registerVault)
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock.configure(USABLE_TEN, USABLE_TEN, LOOT_TEN_USD, 1, 0)
    lootbox.updateDepositPoints(bob, vault_id, mock, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == NOMINAL_USD


def test_sc24_nominal_fallback_is_capped_at_usable(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    ledger,
    lootbox,
    teller,
):
    # Stale lastBalance can exceed live custody. Equality still selects the
    # nominal path; the result must cap at usable, not fund the full book.
    mock, vault_id = _mock_vault(registerVault)
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    half = 5 * EIGHTEEN_DECIMALS
    mock.configure(half, half, LOOT_TEN_USD, 1, 0)
    lootbox.updateDepositPoints(bob, vault_id, mock, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 5
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue != NOMINAL_USD


def test_sc24_converter_result_is_capped_at_usable(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    ledger,
    lootbox,
    teller,
):
    mock, vault_id = _mock_vault(registerVault)
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock.configure(USABLE_TEN, 1, LOOT_TEN_USD, 0, 100 * EIGHTEEN_DECIMALS)
    lootbox.updateDepositPoints(bob, vault_id, mock, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == NOMINAL_USD
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue != 100


def test_sc24_share_offset_overflow_funds_zero_without_revert(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    ledger,
    lootbox,
    teller,
):
    mock, vault_id = _mock_vault(registerVault)
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    # loot // 1e9 = 1e61; * 1e9 fits in uint256; * 1e8 share offset does not.
    mock.configure(USABLE_TEN, 1, 10 ** 70, 0, 100 * EIGHTEEN_DECIMALS)
    lootbox.updateDepositPoints(bob, vault_id, mock, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue != NOMINAL_USD


def test_sc24_empty_book_does_not_probe(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    ledger,
    lootbox,
    teller,
):
    mock, vault_id = _mock_vault(registerVault)
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock.configure(USABLE_TEN, 1, 0, 0, USABLE_TEN)
    lootbox.updateDepositPoints(ZERO_ADDRESS, vault_id, mock, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastBalance == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 0


def test_sc24_reset_paths_revalue_from_live_vault(
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
    switchboard_delta,
):
    vault_id = vault_book.getRegId(rebase_erc20_vault)
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale, rebase_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, rebase_erc20_vault, alpha_token, sender=teller.address)
    alpha_token.transfer(rebase_erc20_vault, 50 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    lootbox.resetUserBalancePoints(bob, alpha_token, vault_id, sender=switchboard_delta.address)
    after_user = ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue
    user_vault = rebase_erc20_vault.getTotalAmountForVault(alpha_token)
    assert after_user <= user_vault // EIGHTEEN_DECIMALS
    assert after_user >= user_vault // EIGHTEEN_DECIMALS - 1
    alpha_token.transfer(rebase_erc20_vault, 25 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)
    lootbox.resetAssetPoints(alpha_token, vault_id, sender=switchboard_delta.address)
    after_asset = ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue
    asset_vault = rebase_erc20_vault.getTotalAmountForVault(alpha_token)
    assert after_asset <= asset_vault // EIGHTEEN_DECIMALS
    assert after_asset >= asset_vault // EIGHTEEN_DECIMALS - 1
    assert after_asset > after_user


def test_sc24_fail_closed_recovers_on_next_supported_checkpoint(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    ledger,
    lootbox,
    teller,
):
    mock, vault_id = _mock_vault(registerVault)
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock.configure(USABLE_TEN, 3, LOOT_TEN_USD, 1, 0)
    lootbox.updateDepositPoints(bob, vault_id, mock, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 0
    mock.configure(USABLE_TEN, 3, LOOT_TEN_USD, 0, USABLE_TEN)
    lootbox.updateDepositPoints(bob, vault_id, mock, alpha_token, sender=teller.address)
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == NOMINAL_USD


def test_sc24_stab_pool_two_holders_prorata_and_rounds_down(
    savings_green,
    green_token,
    whale,
    sally,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    stability_pool,
    vault_book,
    ledger,
    lootbox,
    teller,
):
    vault_id = vault_book.getRegId(stability_pool)
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, savings_green, vault_id)
    mock_price_source.setPrice(savings_green, EIGHTEEN_DECIMALS)
    for user, amount in ((sally, 100 * EIGHTEEN_DECIMALS), (bob, 50 * EIGHTEEN_DECIMALS)):
        green_token.transfer(user, amount, sender=whale)
        green_token.approve(savings_green, amount, sender=user)
        shares = savings_green.deposit(amount, user, sender=user)
        savings_green.approve(teller, shares, sender=user)
        teller.deposit(savings_green, shares, user, stability_pool, sender=user)
    lootbox.updateDepositPoints(sally, vault_id, stability_pool, savings_green, sender=teller.address)
    lootbox.updateDepositPoints(bob, vault_id, stability_pool, savings_green, sender=teller.address)
    ap = ledger.assetDepositPoints(vault_id, savings_green)
    usable = stability_pool.getTotalAmountForVault(savings_green)
    total_shares = stability_pool.totalBalances(savings_green)
    eligible_nominal = ap.lastBalance * ap.precision
    eligible_shares = eligible_nominal * SHARE_OFFSET
    expected = eligible_shares * usable // total_shares
    assert expected <= usable
    assert ap.lastUsdValue == expected // EIGHTEEN_DECIMALS
    assert ap.lastUsdValue <= usable // EIGHTEEN_DECIMALS


def test_sc24_stab_pool_fractional_conversion_rounds_down(
    alpha_token,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    registerVault,
    mission_control,
    switchboard_alpha,
    ledger,
    lootbox,
    teller,
):
    mock, vault_id = _mock_vault(registerVault)
    _configure(setGeneralConfig, setAssetConfig, setRipeRewardsConfig, alpha_token, vault_id)
    mission_control.setPreferredStabVaultId(vault_id, sender=switchboard_alpha.address)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    usable = 10 * EIGHTEEN_DECIMALS
    eligible_shares = LOOT_TEN_USD * SHARE_OFFSET
    total_shares = eligible_shares + 1
    mock.configure(usable, total_shares, LOOT_TEN_USD, 0, 0)
    lootbox.updateDepositPoints(bob, vault_id, mock, alpha_token, sender=teller.address)
    expected = eligible_shares * usable // total_shares
    rounded_up = (eligible_shares * usable + total_shares - 1) // total_shares
    assert (eligible_shares * usable) % total_shares != 0
    assert expected == usable - 1
    assert rounded_up == usable
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == expected // EIGHTEEN_DECIMALS
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == NOMINAL_USD - 1
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue != NOMINAL_USD


def test_sc24_share_offset_matches_first_deposit_share_mint(
    alpha_token,
    alpha_token_whale,
    bob,
    performDeposit,
    rebase_erc20_vault,
    vault_book,
    setGeneralConfig,
    setAssetConfig,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _vaultIds=[vault_book.getRegId(rebase_erc20_vault)])
    deposit = EIGHTEEN_DECIMALS
    performDeposit(bob, deposit, alpha_token, alpha_token_whale, rebase_erc20_vault)
    minted = rebase_erc20_vault.totalBalances(alpha_token)
    assert minted == deposit * SHARE_OFFSET
    assert rebase_erc20_vault.getUserLootBoxShare(bob, alpha_token) == minted // SHARE_OFFSET


def test_sc24_stab_offset_matches_first_deposit_share_mint(
    savings_green,
    green_token,
    whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    mock_price_source,
    stability_pool,
    vault_book,
    teller,
):
    setGeneralConfig()
    setAssetConfig(savings_green, _vaultIds=[vault_book.getRegId(stability_pool)])
    mock_price_source.setPrice(savings_green, EIGHTEEN_DECIMALS)
    amount = EIGHTEEN_DECIMALS
    green_token.transfer(bob, amount, sender=whale)
    green_token.approve(savings_green, amount, sender=bob)
    shares = savings_green.deposit(amount, bob, sender=bob)
    savings_green.approve(teller, shares, sender=bob)
    before = stability_pool.totalBalances(savings_green)
    assert before == 0
    teller.deposit(savings_green, shares, bob, stability_pool, sender=bob)
    minted = stability_pool.totalBalances(savings_green)
    assert minted == amount * SHARE_OFFSET
    user_shares = stability_pool.userBalances(bob, savings_green)
    assert stability_pool.getUserLootBoxShare(bob, savings_green) == user_shares // SHARE_OFFSET


def test_sc24_ripegov_empty_holder_book_still_uses_vault_total(
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
):
    core_id = registerVault(alternate_ripe_gov_vault, "SC-24 RipeGov empty book")
    setGeneralConfig()
    setAssetConfig(
        ripe_token,
        _vaultIds=[core_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    mission_control.setRewardVaultId(
        ripe_token,
        core_id,
        sender=switchboard_alpha.address,
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
    donated = 100 * EIGHTEEN_DECIMALS
    ripe_token.transfer(alternate_ripe_gov_vault, donated, sender=whale)
    lootbox.updateDepositPoints(ZERO_ADDRESS, core_id, alternate_ripe_gov_vault, ripe_token, sender=teller.address)
    ap = ledger.assetDepositPoints(core_id, ripe_token)
    vault_amount = alternate_ripe_gov_vault.getTotalAmountForVault(ripe_token)
    assert vault_amount == donated
    assert ap.lastBalance == 0
    assert ap.lastUsdValue == donated // EIGHTEEN_DECIMALS
    assert ap.lastUsdValue > 0
