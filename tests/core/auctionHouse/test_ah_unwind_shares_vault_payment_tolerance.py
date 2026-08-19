import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT
from conf_utils import clear_transient_storage, filter_logs
from tests.core.auctionHouse.test_auctionhouse_stock_delivery import (
    M4_WITHDRAWAL_GUARD_TOKEN_SOURCE,
)


ZERO_DECIMAL_CONSERVING_OVERDELIVERY_SOURCE = (
    M4_WITHDRAWAL_GUARD_TOKEN_SOURCE
    .replace("return 18", "return 0")
    .replace(
        "self.balances[_from] -= _amount + 1\n"
        "        self.balances[_to] += _amount\n"
        "    elif",
        "self.balances[_from] -= _amount + 1\n"
        "        self.balances[_to] += _amount + 1\n"
        "    elif",
    )
)

EIGHTEEN_DECIMAL_CONSERVING_OVERDELIVERY_SOURCE = (
    M4_WITHDRAWAL_GUARD_TOKEN_SOURCE.replace(
        "self.balances[_from] -= _amount + 1\n"
        "        self.balances[_to] += _amount\n"
        "    elif",
        "self.balances[_from] -= _amount + 1\n"
        "        self.balances[_to] += _amount + 1\n"
        "    elif",
    )
)

TEN_PERCENT = 10_00


def _setup_auction(
    transfer_mode,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createAuctionParams,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    rebase_erc20_vault,
    vault_book,
    teller,
    ledger,
    credit_engine,
    green_token,
    whale,
    alpha_token_whale,
    bob,
    alice,
    sally,
    token_source=ZERO_DECIMAL_CONSERVING_OVERDELIVERY_SOURCE,
    start_discount=0,
    max_discount=0,
    deposit_amount=200,
    initial_price=EIGHTEEN_DECIMALS,
    liq_price=EIGHTEEN_DECIMALS // 2,
):
    token = boa.loads(
        token_source,
        name=f"auction_overdelivery_{transfer_mode}_{deposit_amount}",
        override_address=boa.env.generate_address(),
    )
    vault_id = vault_book.getRegId(rebase_erc20_vault)
    setGeneralConfig()
    setGeneralDebtConfig(
        _ltvPaybackBuffer=0,
        _keeperFeeRatio=0,
        _minKeeperFee=0,
        _genAuctionParams=createAuctionParams(
            _startDiscount=start_discount,
            _maxDiscount=max_discount,
            _delay=0,
            _duration=100,
        ),
    )
    setAssetConfig(
        token,
        _vaultIds=[vault_id],
        _debtTerms=createDebtTerms(
            _ltv=50_00,
            _redemptionThreshold=70_00,
            _liqThreshold=80_00,
            _liqFee=0,
            _borrowRate=0,
        ),
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )
    mock_price_source.setPrice(token, initial_price)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    token.mint(alpha_token_whale, deposit_amount)
    performDeposit(
        bob,
        deposit_amount,
        token,
        alpha_token_whale,
        rebase_erc20_vault,
    )
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(token, liq_price)
    assert credit_engine.canLiquidateUser(bob)
    clear_transient_storage()
    teller.liquidateUser(bob, False, sender=sally)
    assert ledger.hasFungibleAuction(bob, vault_id, token)
    clear_transient_storage()

    token.configure_transfer(transfer_mode)
    payment = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    return token, vault_id, payment


def _state(
    token,
    rebase_erc20_vault,
    green_token,
    credit_engine,
    bob,
    alice,
    auction_house,
    teller,
):
    return {
        "payer_green": green_token.balanceOf(alice),
        "debt": credit_engine.getUserDebtAmount(bob),
        "vault_tokens": token.balanceOf(rebase_erc20_vault),
        "buyer_tokens": token.balanceOf(alice),
        "alice_teller_allowance": green_token.allowance(alice, teller),
        "auction_house_green": green_token.balanceOf(auction_house),
        "credit_engine_green": green_token.balanceOf(credit_engine),
    }


def _buy(
    teller,
    bob,
    vault_id,
    token,
    payment,
    alice,
):
    return teller.buyManyFungibleAuctions(
        [(bob, vault_id, token.address, payment)],
        payment,
        False,
        False,
        False,
        alice,
        sender=alice,
    )


def test_rebase_auction_exact_outflow_obeys_zero_discount_payment_cap(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createAuctionParams,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    rebase_erc20_vault,
    vault_book,
    teller,
    ledger,
    credit_engine,
    auction_house,
    green_token,
    whale,
    alpha_token_whale,
    bob,
    alice,
    sally,
):
    token, vault_id, payment = _setup_auction(
        0,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createAuctionParams,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        rebase_erc20_vault,
        vault_book,
        teller,
        ledger,
        credit_engine,
        green_token,
        whale,
        alpha_token_whale,
        bob,
        alice,
        sally,
    )
    before = _state(
        token,
        rebase_erc20_vault,
        green_token,
        credit_engine,
        bob,
        alice,
        auction_house,
        teller,
    )
    spent = _buy(teller, bob, vault_id, token, payment, alice)
    after = _state(
        token,
        rebase_erc20_vault,
        green_token,
        credit_engine,
        bob,
        alice,
        auction_house,
        teller,
    )
    logs = filter_logs(teller, "FungAuctionPurchased")

    assert len(logs) == 1
    assert token.transfer_mode() == 0
    assert logs[0].collateralAmountSent == 100
    assert logs[0].collateralUsdValueSent == payment
    assert spent == payment
    assert before["payer_green"] - after["payer_green"] == spent
    assert before["debt"] - after["debt"] == spent
    assert before["vault_tokens"] - after["vault_tokens"] == 100
    assert after["buyer_tokens"] - before["buyer_tokens"] == 100


def test_rebase_auction_plus_one_delivery_reverts_when_collateral_exceeds_cap(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createAuctionParams,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    rebase_erc20_vault,
    vault_book,
    teller,
    ledger,
    credit_engine,
    auction_house,
    green_token,
    whale,
    alpha_token_whale,
    bob,
    alice,
    sally,
):
    token, vault_id, payment = _setup_auction(
        1,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createAuctionParams,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        rebase_erc20_vault,
        vault_book,
        teller,
        ledger,
        credit_engine,
        green_token,
        whale,
        alpha_token_whale,
        bob,
        alice,
        sally,
    )
    assert token.transfer_mode() == 1
    assert payment == 50 * EIGHTEEN_DECIMALS
    before = _state(
        token,
        rebase_erc20_vault,
        green_token,
        credit_engine,
        bob,
        alice,
        auction_house,
        teller,
    )
    assert ledger.hasFungibleAuction(bob, vault_id, token)

    with boa.reverts("collateral exceeds buy cap"):
        _buy(teller, bob, vault_id, token, payment, alice)

    after = _state(
        token,
        rebase_erc20_vault,
        green_token,
        credit_engine,
        bob,
        alice,
        auction_house,
        teller,
    )
    assert ledger.hasFungibleAuction(bob, vault_id, token)
    assert after == before
    assert filter_logs(teller, "FungAuctionPurchased") == []


def test_rebase_auction_exact_outflow_at_ten_percent_discount_obeys_cap(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createAuctionParams,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    rebase_erc20_vault,
    vault_book,
    teller,
    ledger,
    credit_engine,
    auction_house,
    price_desk,
    green_token,
    whale,
    alpha_token_whale,
    bob,
    alice,
    sally,
):
    token, vault_id, payment = _setup_auction(
        0,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createAuctionParams,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        rebase_erc20_vault,
        vault_book,
        teller,
        ledger,
        credit_engine,
        green_token,
        whale,
        alpha_token_whale,
        bob,
        alice,
        sally,
        token_source=M4_WITHDRAWAL_GUARD_TOKEN_SOURCE,
        start_discount=TEN_PERCENT,
        max_discount=TEN_PERCENT,
        deposit_amount=100 * EIGHTEEN_DECIMALS,
        initial_price=2 * EIGHTEEN_DECIMALS,
        liq_price=EIGHTEEN_DECIMALS,
    )
    assert token.decimals() == 18
    assert token.transfer_mode() == 0
    # 50e18 * 10000 // 9000 leaves remainder 5000, so GREEN spend floors
    # one wei below the 50 GREEN payment cap.
    expected_collateral_usd = payment * HUNDRED_PERCENT // (
        HUNDRED_PERCENT - TEN_PERCENT
    )
    expected_collateral_amount = price_desk.getAssetAmount(
        token, expected_collateral_usd, True
    )
    expected_green = (
        expected_collateral_usd
        * (HUNDRED_PERCENT - TEN_PERCENT)
        // HUNDRED_PERCENT
    )
    assert expected_collateral_usd == 55_555_555_555_555_555_555
    assert expected_collateral_amount == 55_555_555_555_555_555_555
    assert expected_green == 49_999_999_999_999_999_999

    before = _state(
        token,
        rebase_erc20_vault,
        green_token,
        credit_engine,
        bob,
        alice,
        auction_house,
        teller,
    )
    spent = _buy(teller, bob, vault_id, token, payment, alice)
    after = _state(
        token,
        rebase_erc20_vault,
        green_token,
        credit_engine,
        bob,
        alice,
        auction_house,
        teller,
    )
    logs = filter_logs(teller, "FungAuctionPurchased")

    assert len(logs) == 1
    assert logs[0].collateralAmountSent == expected_collateral_amount
    assert logs[0].collateralUsdValueSent == expected_collateral_usd
    assert spent == expected_green
    assert before["payer_green"] - after["payer_green"] == spent
    assert before["debt"] - after["debt"] == spent
    assert before["vault_tokens"] - after["vault_tokens"] == expected_collateral_amount
    assert after["buyer_tokens"] - before["buyer_tokens"] == expected_collateral_amount


def test_rebase_auction_plus_one_delivery_at_ten_percent_discount_reverts_when_collateral_usd_exceeds_cap(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createAuctionParams,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    rebase_erc20_vault,
    vault_book,
    teller,
    ledger,
    credit_engine,
    auction_house,
    price_desk,
    green_token,
    whale,
    alpha_token_whale,
    bob,
    alice,
    sally,
):
    token, vault_id, payment = _setup_auction(
        1,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createAuctionParams,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        rebase_erc20_vault,
        vault_book,
        teller,
        ledger,
        credit_engine,
        green_token,
        whale,
        alpha_token_whale,
        bob,
        alice,
        sally,
        token_source=EIGHTEEN_DECIMAL_CONSERVING_OVERDELIVERY_SOURCE,
        start_discount=TEN_PERCENT,
        max_discount=TEN_PERCENT,
        deposit_amount=100 * EIGHTEEN_DECIMALS,
        initial_price=2 * EIGHTEEN_DECIMALS,
        liq_price=EIGHTEEN_DECIMALS,
    )
    assert token.decimals() == 18
    assert token.transfer_mode() == 1
    assert payment == 50 * EIGHTEEN_DECIMALS

    max_collateral_usd = payment * HUNDRED_PERCENT // (HUNDRED_PERCENT - TEN_PERCENT)
    max_asset = price_desk.getAssetAmount(token, max_collateral_usd, False)
    over_usd = (max_asset + 1) * max_collateral_usd // max_asset
    assert over_usd > max_collateral_usd
    assert over_usd * (HUNDRED_PERCENT - TEN_PERCENT) // HUNDRED_PERCENT == payment

    before = _state(
        token,
        rebase_erc20_vault,
        green_token,
        credit_engine,
        bob,
        alice,
        auction_house,
        teller,
    )
    assert ledger.hasFungibleAuction(bob, vault_id, token)

    with boa.reverts("collateral exceeds buy cap"):
        _buy(teller, bob, vault_id, token, payment, alice)

    after = _state(
        token,
        rebase_erc20_vault,
        green_token,
        credit_engine,
        bob,
        alice,
        auction_house,
        teller,
    )
    assert ledger.hasFungibleAuction(bob, vault_id, token)
    assert after == before
    assert filter_logs(teller, "FungAuctionPurchased") == []
