import boa

from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs
from tests.core.auctionHouse.test_auctionhouse_stock_delivery import (
    M4_WITHDRAWAL_GUARD_TOKEN_SOURCE,
)


ZERO_DECIMAL_WITHDRAWAL_GUARD_TOKEN_SOURCE = (
    M4_WITHDRAWAL_GUARD_TOKEN_SOURCE.replace("return 18", "return 0")
)


def _setup_rebase_redemption(
    transfer_mode,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    rebase_erc20_vault,
    vault_book,
    teller,
    green_token,
    whale,
    alpha_token_whale,
    bob,
    alice,
):
    token = boa.loads(
        ZERO_DECIMAL_WITHDRAWAL_GUARD_TOKEN_SOURCE,
        name=f"redemption_withdrawal_guard_{transfer_mode}",
        override_address=boa.env.generate_address(),
    )
    vault_id = vault_book.getRegId(rebase_erc20_vault)

    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=90_00,
        _liqFee=0,
        _borrowRate=0,
    )
    setAssetConfig(token, _vaultIds=[vault_id], _debtTerms=debt_terms)
    mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)

    token.mint(alpha_token_whale, 200)
    performDeposit(
        bob,
        200,
        token,
        alpha_token_whale,
        rebase_erc20_vault,
    )
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    # At $0.625, collateral is $125, debt LTV is 80%, and the target-LTV
    # redemption budget is exactly $75 = 120 whole tokens.
    mock_price_source.setPrice(token, 5 * EIGHTEEN_DECIMALS // 8)
    token.configure_transfer(transfer_mode)

    payment = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    redemptions = [(bob, vault_id, token.address, payment)]
    return token, vault_id, payment, redemptions


def _redemption_state(
    token,
    rebase_erc20_vault,
    green_token,
    credit_engine,
    bob,
    alice,
):
    return {
        "payer_green": green_token.balanceOf(alice),
        "green_supply": green_token.totalSupply(),
        "borrower_debt": credit_engine.getUserDebtAmount(bob),
        "vault_tokens": token.balanceOf(rebase_erc20_vault),
        "recipient_tokens": token.balanceOf(alice),
        "user_shares": rebase_erc20_vault.userBalances(bob, token),
        "total_shares": rebase_erc20_vault.totalBalances(token),
    }


def test_rebase_redemption_exact_outflow_reports_full_payer_debit(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    rebase_erc20_vault,
    vault_book,
    teller,
    green_token,
    credit_engine,
    whale,
    alpha_token_whale,
    bob,
    alice,
):
    token, vault_id, payment, redemptions = _setup_rebase_redemption(
        0,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        rebase_erc20_vault,
        vault_book,
        teller,
        green_token,
        whale,
        alpha_token_whale,
        bob,
        alice,
    )
    before = _redemption_state(
        token, rebase_erc20_vault, green_token, credit_engine, bob, alice
    )

    spent = teller.redeemCollateralFromMany(
        redemptions,
        payment,
        False,
        False,
        False,
        sender=alice,
    )
    after = _redemption_state(
        token, rebase_erc20_vault, green_token, credit_engine, bob, alice
    )
    logs = filter_logs(teller, "CollateralRedeemed")

    payer_debit = before["payer_green"] - after["payer_green"]
    burned = before["green_supply"] - after["green_supply"]
    debt_reduction = before["borrower_debt"] - after["borrower_debt"]
    vault_outflow = before["vault_tokens"] - after["vault_tokens"]
    recipient_delivery = after["recipient_tokens"] - before["recipient_tokens"]

    assert len(logs) == 1
    assert logs[0].vaultId == vault_id
    assert logs[0].amount == 120
    assert token.transfer_mode() == 0
    assert spent == 75 * EIGHTEEN_DECIMALS
    assert spent == payer_debit == burned == debt_reduction
    assert vault_outflow == recipient_delivery == logs[0].amount


def test_rebase_redemption_plus_one_outflow_caps_credit_and_burns_actual_outflow(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    rebase_erc20_vault,
    vault_book,
    teller,
    green_token,
    credit_engine,
    whale,
    alpha_token_whale,
    bob,
    alice,
):
    token, vault_id, payment, redemptions = _setup_rebase_redemption(
        1,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        rebase_erc20_vault,
        vault_book,
        teller,
        green_token,
        whale,
        alpha_token_whale,
        bob,
        alice,
    )
    intended_asset_cap = 120
    intended_green_cap = 75 * EIGHTEEN_DECIMALS
    assert token.transfer_mode() == 1
    assert mock_price_source.getPrice(token) == 5 * EIGHTEEN_DECIMALS // 8
    assert intended_asset_cap * (5 * EIGHTEEN_DECIMALS // 8) == intended_green_cap

    actual_outflow = intended_asset_cap + 1
    expected_shares = rebase_erc20_vault.amountToShares(
        token, actual_outflow, True
    )
    before = _redemption_state(
        token, rebase_erc20_vault, green_token, credit_engine, bob, alice
    )

    spent = teller.redeemCollateralFromMany(
        redemptions,
        payment,
        False,
        False,
        False,
        sender=alice,
    )

    after = _redemption_state(
        token, rebase_erc20_vault, green_token, credit_engine, bob, alice
    )
    logs = filter_logs(teller, "CollateralRedeemed")
    payer_debit = before["payer_green"] - after["payer_green"]
    burned = before["green_supply"] - after["green_supply"]
    debt_reduction = before["borrower_debt"] - after["borrower_debt"]
    vault_outflow = before["vault_tokens"] - after["vault_tokens"]
    recipient_delivery = after["recipient_tokens"] - before["recipient_tokens"]
    user_shares_burned = before["user_shares"] - after["user_shares"]
    total_shares_burned = before["total_shares"] - after["total_shares"]

    assert len(logs) == 1
    assert logs[0].vaultId == vault_id
    assert logs[0].amount == intended_asset_cap
    assert logs[0].repayValue == intended_green_cap
    assert spent == intended_green_cap
    assert spent == payer_debit == burned == debt_reduction
    assert vault_outflow == actual_outflow
    assert recipient_delivery == intended_asset_cap
    assert user_shares_burned == total_shares_burned == expected_shares
