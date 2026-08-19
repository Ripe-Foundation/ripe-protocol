import boa

from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from conf_utils import filter_logs


def _auction_flags(createDebtTerms):
    return dict(
        _debtTerms=createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0),
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )


def _make_bob_auctionable_on_bravo(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    bob,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    bravo_amount,
    alpha_crash,
    gen_auction_params=None,
    extra_asset_flags=None,
):
    setGeneralConfig()
    if gen_auction_params is None:
        setGeneralDebtConfig(_ltvPaybackBuffer=0)
    else:
        setGeneralDebtConfig(_ltvPaybackBuffer=0, _genAuctionParams=gen_auction_params)
    flags = _auction_flags(createDebtTerms)
    if extra_asset_flags:
        flags.update(extra_asset_flags)
    setAssetConfig(alpha_token, **flags)
    setAssetConfig(bravo_token, **flags)

    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)

    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    mock_price_source.setPrice(alpha_token, alpha_crash)
    assert credit_engine.canLiquidateUser(bob)
    teller.liquidateUser(bob, False, sender=sally)
    mock_price_source.setPrice(bravo_token, 1)


def _fund_alice(green_token, whale, teller, alice, amount):
    green_token.transfer(alice, amount, sender=whale)
    green_token.approve(teller, amount, sender=alice)
    return green_token.balanceOf(alice)


def _snapshot_ah(
    credit_engine,
    ledger,
    green_token,
    bravo_token,
    simple_erc20_vault,
    lootbox,
    vault_id,
    bob,
    alice,
):
    return {
        "debt": credit_engine.getUserDebtAmount(bob),
        "alice_green": green_token.balanceOf(alice),
        "alice_bravo": bravo_token.balanceOf(alice),
        "bob_bravo": simple_erc20_vault.getTotalAmountForUser(bob, bravo_token),
        "has_auc": ledger.hasFungibleAuction(bob, vault_id, bravo_token),
        "points": lootbox.getLatestDepositPoints(bob, vault_id, bravo_token),
    }


def test_auction_house_multi_token_payment_scales_by_whole_tokens(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
):
    bravo_amount = 100 * EIGHTEEN_DECIMALS
    _make_bob_auctionable_on_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        sally,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        green_token,
        bravo_amount,
        12 * EIGHTEEN_DECIMALS // 100,
    )
    green_budget = 100 * EIGHTEEN_DECIMALS
    alice_green_before = _fund_alice(green_token, whale, teller, alice, green_budget)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_spent = teller.buyManyFungibleAuctions(
        [(bob, vault_id, bravo_token, MAX_UINT256)],
        green_budget,
        False,
        False,
        False,
        alice,
        sender=alice,
    )
    assert green_spent == 100
    logs = filter_logs(teller, "FungAuctionPurchased")
    bravo_logs = [lg for lg in logs if lg.liqAsset == bravo_token.address]
    assert len(bravo_logs) == 1
    assert bravo_logs[0].collateralAmountSent == bravo_amount
    assert bravo_logs[0].collateralUsdValueSent == 100
    assert bravo_logs[0].greenSpent == 100
    assert bravo_token.balanceOf(alice) == bravo_amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == 0
    assert green_token.balanceOf(alice) == alice_green_before - 100


def test_auction_house_one_wei_takes_one_token_from_multi_token_balance(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
):
    bravo_amount = 100 * EIGHTEEN_DECIMALS
    _make_bob_auctionable_on_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        sally,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        green_token,
        bravo_amount,
        12 * EIGHTEEN_DECIMALS // 100,
    )
    alice_green_before = _fund_alice(green_token, whale, teller, alice, 1)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_spent = teller.buyManyFungibleAuctions(
        [(bob, vault_id, bravo_token, MAX_UINT256)],
        1,
        False,
        False,
        False,
        alice,
        sender=alice,
    )
    assert green_spent == 1
    logs = filter_logs(teller, "FungAuctionPurchased")
    assert logs[0].collateralAmountSent == EIGHTEEN_DECIMALS
    assert logs[0].greenSpent == 1
    assert bravo_token.balanceOf(alice) == EIGHTEEN_DECIMALS
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == 99 * EIGHTEEN_DECIMALS
    assert green_token.balanceOf(alice) == alice_green_before - 1


def test_auction_house_sub_token_reverts_whole_tx(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    lootbox,
):
    bravo_amount = EIGHTEEN_DECIMALS // 2
    _make_bob_auctionable_on_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        sally,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        green_token,
        bravo_amount,
        60 * EIGHTEEN_DECIMALS // 100,
    )
    _fund_alice(green_token, whale, teller, alice, 100 * EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    before = _snapshot_ah(
        credit_engine, ledger, green_token, bravo_token, simple_erc20_vault, lootbox, vault_id, bob, alice
    )
    with boa.reverts("amounts do not match up"):
        teller.buyManyFungibleAuctions(
            [(bob, vault_id, bravo_token, MAX_UINT256)],
            100 * EIGHTEEN_DECIMALS,
            False,
            False,
            False,
            alice,
            sender=alice,
        )
    after = _snapshot_ah(
        credit_engine, ledger, green_token, bravo_token, simple_erc20_vault, lootbox, vault_id, bob, alice
    )
    assert after == before
    assert filter_logs(teller, "FungAuctionPurchased") == []


def test_auction_house_mixed_batch_reverts(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    lootbox,
):
    bravo_amount = EIGHTEEN_DECIMALS // 2
    _make_bob_auctionable_on_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        sally,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        green_token,
        bravo_amount,
        60 * EIGHTEEN_DECIMALS // 100,
    )
    green_budget = 100 * EIGHTEEN_DECIMALS
    _fund_alice(green_token, whale, teller, alice, green_budget)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    before = _snapshot_ah(
        credit_engine, ledger, green_token, bravo_token, simple_erc20_vault, lootbox, vault_id, bob, alice
    )
    alice_alpha = alpha_token.balanceOf(alice)
    bob_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    with boa.reverts("amounts do not match up"):
        teller.buyManyFungibleAuctions(
            [
                (bob, vault_id, bravo_token, MAX_UINT256),
                (bob, vault_id, alpha_token, MAX_UINT256),
            ],
            green_budget,
            False,
            False,
            False,
            alice,
            sender=alice,
        )
    after = _snapshot_ah(
        credit_engine, ledger, green_token, bravo_token, simple_erc20_vault, lootbox, vault_id, bob, alice
    )
    assert after == before
    assert alpha_token.balanceOf(alice) == alice_alpha
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == bob_alpha
    assert filter_logs(teller, "FungAuctionPurchased") == []


def test_auction_house_discounted_one_token_reverts_on_zero_green_transfer(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    price_desk,
):
    bravo_amount = 1 * EIGHTEEN_DECIMALS
    _make_bob_auctionable_on_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        sally,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        green_token,
        bravo_amount,
        60 * EIGHTEEN_DECIMALS // 100,
        gen_auction_params=createAuctionParams(_startDiscount=1, _maxDiscount=50_00),
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    auc = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, bravo_token)
    assert auc.isActive
    assert auc.startDiscount == 1
    collateral_usd = price_desk.getUsdValue(bravo_token, bravo_amount)
    assert collateral_usd == 1
    assert collateral_usd * 9999 // 10000 == 0
    _fund_alice(green_token, whale, teller, alice, 100 * EIGHTEEN_DECIMALS)
    with boa.reverts():
        teller.buyManyFungibleAuctions(
            [(bob, vault_id, bravo_token, MAX_UINT256)],
            100 * EIGHTEEN_DECIMALS,
            False,
            False,
            False,
            alice,
            sender=alice,
        )
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == bravo_amount
    assert bravo_token.balanceOf(alice) == 0


def test_auction_house_stab_swap_dust_reverts(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    bob,
    sally,
    alice,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    savings_green,
    whale,
    simple_erc20_vault,
    stability_pool,
    vault_book,
    mission_control,
    switchboard_alpha,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    simple_id = vault_book.getRegId(simple_erc20_vault)
    stab_id = vault_book.getRegId(stability_pool)
    setAssetConfig(
        alpha_token,
        _vaultIds=[simple_id],
        _debtTerms=terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )
    setAssetConfig(
        bravo_token,
        _vaultIds=[simple_id],
        _debtTerms=terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=True,
    )
    setAssetConfig(
        savings_green,
        _vaultIds=[stab_id],
        _debtTerms=createDebtTerms(0, 0, 0, 0, 0, 0),
        _shouldBurnAsPayment=True,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    mission_control.setPriorityStabVaults(
        [(stab_id, savings_green)], sender=switchboard_alpha.address
    )

    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(bob, EIGHTEEN_DECIMALS // 2, bravo_token, bravo_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    pool_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, pool_amount, sender=whale)
    green_token.approve(savings_green, pool_amount, sender=sally)
    pool_shares = savings_green.deposit(pool_amount, sally, sender=sally)
    savings_green.approve(teller, pool_shares, sender=sally)
    teller.deposit(savings_green, pool_shares, sally, stability_pool, sender=sally)

    mock_price_source.setPrice(alpha_token, 12 * EIGHTEEN_DECIMALS // 100)
    mock_price_source.setPrice(bravo_token, 1)
    assert credit_engine.canLiquidateUser(bob)
    bob_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    with boa.reverts("amounts do not match up"):
        teller.liquidateUser(bob, False, sender=sally)
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == bob_bravo
    assert bravo_token.balanceOf(stability_pool) == 0


def test_wsuper_price_desk_auction_house_tx(
    ripe_hq,
    mock_yield_registry,
    mock_price_source,
    price_desk,
    switchboard_alpha,
    mission_control,
    governance,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    teller,
    credit_engine,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
):
    src = boa.load(
        "contracts/priceSources/wsuperOETHbPrices.vy",
        ripe_hq,
        bravo_token.address,
        mock_yield_registry,
        mock_yield_registry,
        alpha_token.address,
        1,
        100,
        name="wsuper_ah_e2e",
    )
    assert price_desk.startAddNewAddressToRegistry(src, "wsuper ah e2e", sender=governance.address)
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    wsuper_id = price_desk.confirmNewAddressToRegistry(src, sender=governance.address)

    _make_bob_auctionable_on_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        sally,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        green_token,
        EIGHTEEN_DECIMALS,
        12 * EIGHTEEN_DECIMALS // 100,
    )
    mock_price_source.setPrice(bravo_token, 0)
    mission_control.setPriorityPriceSourceIds([wsuper_id], sender=switchboard_alpha.address)
    assert src.getPriceAndHasFeed(bravo_token) == (0, False)
    assert price_desk.getPrice(bravo_token) == 0
    _fund_alice(green_token, whale, teller, alice, 100 * EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    with boa.reverts():
        teller.buyManyFungibleAuctions(
            [(bob, vault_id, bravo_token, MAX_UINT256)],
            100 * EIGHTEEN_DECIMALS,
            False,
            False,
            False,
            alice,
            sender=alice,
        )
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == EIGHTEEN_DECIMALS
    assert bravo_token.balanceOf(alice) == 0

    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mission_control.setPriorityPriceSourceIds([6], sender=switchboard_alpha.address)
    assert price_desk.getPrice(bravo_token) == EIGHTEEN_DECIMALS
