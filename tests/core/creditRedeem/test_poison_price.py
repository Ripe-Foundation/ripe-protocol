import boa

from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from conf_utils import filter_logs, redeem_collateral


def _redeem_terms(createDebtTerms):
    return createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
        _liqFee=10_00,
        _borrowRate=0,
        _daowry=0,
    )


def _make_bob_redeemable_on_poisoned_bravo(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bravo_amount,
):
    setGeneralConfig()
    debt_terms = _redeem_terms(createDebtTerms)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setAssetConfig(bravo_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)
    mock_price_source.setPrice(bravo_token, 1)
    assert credit_engine.canRedeemUserCollateral(bob)
    assert not credit_engine.getLatestUserDebtAndTerms(bob, False)[0].inLiquidation


def _fund_alice(green_token, whale, teller, alice, amount):
    green_token.transfer(alice, amount, sender=whale)
    green_token.approve(teller, amount, sender=alice)
    return green_token.balanceOf(alice)


def _snapshot_redeem_state(
    credit_engine,
    green_token,
    bravo_token,
    simple_erc20_vault,
    lootbox,
    vault_id,
    bob,
    alice,
):
    debt, _, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    return {
        "debt": debt.amount,
        "alice_green": green_token.balanceOf(alice),
        "alice_bravo": bravo_token.balanceOf(alice),
        "bob_bravo": simple_erc20_vault.getTotalAmountForUser(bob, bravo_token),
        "points": lootbox.getLatestDepositPoints(bob, vault_id, bravo_token),
    }


def test_credit_redeem_price_one_takes_full_token_burns_one_wei(
    ripe_hq,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    whale,
    credit_engine,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
    price_desk,
):
    bravo_amount = 1 * EIGHTEEN_DECIMALS
    _make_bob_redeemable_on_poisoned_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        bravo_amount,
    )

    assert price_desk.getPrice(bravo_token) == 1
    assert price_desk.getAssetAmount(bravo_token, 60 * EIGHTEEN_DECIMALS, False) == 60 * 10**36

    green_budget = 100 * EIGHTEEN_DECIMALS
    alice_green_before = _fund_alice(green_token, whale, teller, alice, green_budget)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_spent = redeem_collateral(
        teller,
        bob,
        vault_id,
        bravo_token,
        green_budget,
        should_refund_savings_green=False,
        sender=alice,
    )

    assert green_spent == 1
    logs = filter_logs(teller, "CollateralRedeemed")
    assert len(logs) == 1
    log = logs[0]
    assert log.amount == bravo_amount
    assert log.repayValue == 1
    assert log.user == bob
    assert log.recipient == alice

    assert bravo_token.balanceOf(alice) == bravo_amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == 0
    assert green_token.balanceOf(alice) == alice_green_before - 1

    user_debt, _, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    assert user_debt.amount == 100 * EIGHTEEN_DECIMALS - 1


def test_credit_redeem_multi_token_payment_scales_by_whole_tokens(
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
    _make_bob_redeemable_on_poisoned_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        bravo_amount,
    )
    green_budget = 100 * EIGHTEEN_DECIMALS
    alice_green_before = _fund_alice(green_token, whale, teller, alice, green_budget)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_spent = redeem_collateral(
        teller,
        bob,
        vault_id,
        bravo_token,
        green_budget,
        should_refund_savings_green=False,
        sender=alice,
    )
    assert green_spent == 100
    logs = filter_logs(teller, "CollateralRedeemed")
    assert len(logs) == 1
    assert logs[0].amount == bravo_amount
    assert logs[0].repayValue == 100
    assert bravo_token.balanceOf(alice) == bravo_amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == 0
    assert green_token.balanceOf(alice) == alice_green_before - 100


def test_credit_redeem_one_wei_takes_one_token_from_multi_token_balance(
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
    _make_bob_redeemable_on_poisoned_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        bravo_amount,
    )
    alice_green_before = _fund_alice(green_token, whale, teller, alice, 1)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_spent = redeem_collateral(
        teller,
        bob,
        vault_id,
        bravo_token,
        1,
        should_refund_savings_green=False,
        sender=alice,
    )
    assert green_spent == 1
    logs = filter_logs(teller, "CollateralRedeemed")
    assert logs[0].amount == EIGHTEEN_DECIMALS
    assert logs[0].repayValue == 1
    assert bravo_token.balanceOf(alice) == EIGHTEEN_DECIMALS
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == 99 * EIGHTEEN_DECIMALS
    assert green_token.balanceOf(alice) == alice_green_before - 1


def test_credit_redeem_sub_token_reverts_whole_tx(
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
    _make_bob_redeemable_on_poisoned_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        bravo_amount,
    )
    _fund_alice(green_token, whale, teller, alice, 100 * EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    before = _snapshot_redeem_state(
        credit_engine, green_token, bravo_token, simple_erc20_vault, lootbox, vault_id, bob, alice
    )
    with boa.reverts("could not burn green"):
        redeem_collateral(
            teller,
            bob,
            vault_id,
            bravo_token,
            100 * EIGHTEEN_DECIMALS,
            should_refund_savings_green=False,
            sender=alice,
        )
    after = _snapshot_redeem_state(
        credit_engine, green_token, bravo_token, simple_erc20_vault, lootbox, vault_id, bob, alice
    )
    assert after == before
    assert filter_logs(teller, "CollateralRedeemed") == []


def test_credit_redeem_mixed_batch_reverts(
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
    _make_bob_redeemable_on_poisoned_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        bravo_amount,
    )
    green_budget = 100 * EIGHTEEN_DECIMALS
    _fund_alice(green_token, whale, teller, alice, green_budget)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    before = _snapshot_redeem_state(
        credit_engine, green_token, bravo_token, simple_erc20_vault, lootbox, vault_id, bob, alice
    )
    alice_alpha = alpha_token.balanceOf(alice)
    bob_alpha = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    with boa.reverts("could not burn green"):
        teller.redeemCollateralFromMany(
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
    after = _snapshot_redeem_state(
        credit_engine, green_token, bravo_token, simple_erc20_vault, lootbox, vault_id, bob, alice
    )
    assert after == before
    assert alpha_token.balanceOf(alice) == alice_alpha
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == bob_alpha
    assert filter_logs(teller, "CollateralRedeemed") == []


def test_wsuper_price_desk_credit_redeem_tx(
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
        name="wsuper_cr_e2e",
    )
    assert price_desk.startAddNewAddressToRegistry(src, "wsuper e2e", sender=governance.address)
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    wsuper_id = price_desk.confirmNewAddressToRegistry(src, sender=governance.address)
    mock_price_source.setPrice(bravo_token, 0)
    mission_control.setPriorityPriceSourceIds([wsuper_id], sender=switchboard_alpha.address)
    assert src.getPriceAndHasFeed(bravo_token) == (0, False)
    assert price_desk.getPrice(bravo_token) == 0

    _make_bob_redeemable_on_poisoned_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        EIGHTEEN_DECIMALS,
    )
    mock_price_source.setPrice(bravo_token, 0)
    mission_control.setPriorityPriceSourceIds([wsuper_id], sender=switchboard_alpha.address)
    assert price_desk.getPrice(bravo_token) == 0
    _fund_alice(green_token, whale, teller, alice, 100 * EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    with boa.reverts():
        redeem_collateral(
            teller,
            bob,
            vault_id,
            bravo_token,
            100 * EIGHTEEN_DECIMALS,
            should_refund_savings_green=False,
            sender=alice,
        )
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == EIGHTEEN_DECIMALS
    assert bravo_token.balanceOf(alice) == 0

    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mission_control.setPriorityPriceSourceIds([6], sender=switchboard_alpha.address)
    assert price_desk.getPrice(bravo_token) == EIGHTEEN_DECIMALS
