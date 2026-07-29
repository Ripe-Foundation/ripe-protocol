"""Track 8 M4 composed stock delivery proof for unchanged AuctionHouse ordering."""

import boa
import pytest

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS
from tests.vaults.test_guarded_erc20 import (
    _register_guarded_vault,
    guarded_erc20_vault,
)

M4_WITHDRAWAL_GUARD_TOKEN_SOURCE = """
# @version 0.4.3

balances: HashMap[address, uint256]
allowances: HashMap[address, HashMap[address, uint256]]
transfer_mode: public(uint256)

@external
def mint(_to: address, _amount: uint256):
    self.balances[_to] += _amount

@external
def configure_transfer(_mode: uint256):
    self.transfer_mode = _mode

@view
@external
def balanceOf(_holder: address) -> uint256:
    return self.balances[_holder]

@view
@external
def decimals() -> uint8:
    return 18

@external
def approve(_spender: address, _amount: uint256) -> bool:
    self.allowances[msg.sender][_spender] = _amount
    return True

@internal
def _move(_from: address, _to: address, _amount: uint256):
    if self.transfer_mode == 1:
        self.balances[_from] -= _amount + 1
        self.balances[_to] += _amount
    elif self.transfer_mode == 2:
        self.balances[_from] -= _amount
        self.balances[_to] += _amount - 1
    else:
        self.balances[_from] -= _amount
        self.balances[_to] += _amount

@external
def transfer(_to: address, _amount: uint256) -> bool:
    self._move(msg.sender, _to, _amount)
    return True

@external
def transferFrom(_from: address, _to: address, _amount: uint256) -> bool:
    self.allowances[_from][msg.sender] -= _amount
    self._move(_from, _to, _amount)
    return True
"""


def _configure_guarded_auction_assets(
    tokens,
    vault_id,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createAuctionParams,
    createDebtTerms,
    mock_price_source,
    green_token,
):
    setGeneralConfig()
    setGeneralDebtConfig(
        _ltvPaybackBuffer=0,
        _genAuctionParams=createAuctionParams(
            _startDiscount=0,
            _maxDiscount=0,
        ),
    )
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=80_00,
        _liqFee=10_00,
        _borrowRate=0,
    )
    for token in tokens:
        setAssetConfig(
            token,
            _vaultIds=[vault_id],
            _debtTerms=debt_terms,
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=False,
            _shouldSwapInStabPools=False,
            _shouldAuctionInstantly=True,
        )
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    return debt_terms


def _open_guarded_auctions(
    deposits,
    debt_amount,
    vault,
    vault_id,
    performDeposit,
    teller,
    mock_price_source,
    liquidator,
):
    for token, whale, amount in deposits:
        performDeposit(
            liquidator["seller"],
            amount,
            token,
            whale,
            vault,
        )
    teller.borrow(
        debt_amount,
        liquidator["seller"],
        False,
        sender=liquidator["seller"],
    )
    for token, _, _ in deposits:
        mock_price_source.setPrice(
            token,
            EIGHTEEN_DECIMALS // 4,
        )
    teller.liquidateUser(
        liquidator["seller"],
        False,
        sender=liquidator["caller"],
    )
    for token, _, _ in deposits:
        assert liquidator["ledger"].hasFungibleAuction(
            liquidator["seller"],
            vault_id,
            token,
        )


def _fund_buyer(green_token, whale, teller, buyer, amount):
    green_token.transfer(buyer, amount, sender=whale)
    green_token.approve(teller, amount, sender=buyer)


def _auction_state(
    vault,
    tokens,
    green_token,
    teller,
    auction_house,
    credit_engine,
    ledger,
    seller,
    buyer,
    vault_id,
):
    debt = ledger.userDebt(seller)
    state = [
        green_token.balanceOf(buyer),
        green_token.balanceOf(auction_house),
        green_token.balanceOf(credit_engine),
        debt.amount,
        debt.inLiquidation,
        ledger.getNumUserVaults(buyer),
        ledger.isParticipatingInVault(buyer, vault_id),
    ]
    for token in tokens:
        auction = ledger.getFungibleAuctionDuringPurchase(
            seller,
            vault_id,
            token,
        )
        state.extend(
            (
                token.balanceOf(vault),
                token.balanceOf(buyer),
                vault.userBalances(seller, token),
                vault.userBalances(buyer, token),
                vault.totalBalances(token),
                auction.isActive,
                auction.startBlock,
                auction.endBlock,
            )
        )
    return tuple(state)


def test_guarded_internal_two_buyer_sequence_caps_over_request_and_depletes_seller(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createAuctionParams,
    createDebtTerms,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
    teller,
    credit_engine,
    mock_price_source,
    ledger,
    guarded_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_guarded_vault(
        vault_book,
        governance,
        guarded_erc20_vault,
    )
    _configure_guarded_auction_assets(
        (alpha_token,),
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createAuctionParams,
        createDebtTerms,
        mock_price_source,
        green_token,
    )
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    debt_amount = 100 * EIGHTEEN_DECIMALS
    _open_guarded_auctions(
        ((alpha_token, alpha_token_whale, deposit_amount),),
        debt_amount,
        guarded_erc20_vault,
        vault_id,
        performDeposit,
        teller,
        mock_price_source,
        {"seller": bob, "caller": sally, "ledger": ledger},
    )

    first_max = 10 * EIGHTEEN_DECIMALS
    _fund_buyer(green_token, whale, teller, alice, first_max)
    alice_green_before = green_token.balanceOf(alice)
    debt_before = credit_engine.getUserDebtAmount(bob)
    first_spent = teller.buyFungibleAuction(
        bob,
        vault_id,
        alpha_token,
        first_max,
        False,
        True,
        False,
        sender=alice,
    )
    first_delivery = 40 * EIGHTEEN_DECIMALS

    assert first_spent == first_max
    assert green_token.balanceOf(alice) == alice_green_before - first_spent
    assert credit_engine.getUserDebtAmount(bob) == debt_before - first_spent
    assert guarded_erc20_vault.userBalances(alice, alpha_token) == first_delivery
    assert alpha_token.balanceOf(alice) == 0
    assert ledger.isParticipatingInVault(alice, vault_id)

    second_max = 100 * EIGHTEEN_DECIMALS
    _fund_buyer(green_token, whale, teller, sally, second_max)
    sally_green_before = green_token.balanceOf(sally)
    debt_before = credit_engine.getUserDebtAmount(bob)
    second_spent = teller.buyFungibleAuction(
        bob,
        vault_id,
        alpha_token,
        second_max,
        False,
        True,
        False,
        sender=sally,
    )
    second_delivery = 160 * EIGHTEEN_DECIMALS

    assert second_spent == 40 * EIGHTEEN_DECIMALS
    assert second_spent < second_max
    assert green_token.balanceOf(sally) == sally_green_before - second_spent
    assert credit_engine.getUserDebtAmount(bob) == debt_before - second_spent
    assert guarded_erc20_vault.userBalances(bob, alpha_token) == 0
    assert guarded_erc20_vault.userBalances(alice, alpha_token) == first_delivery
    assert guarded_erc20_vault.userBalances(sally, alpha_token) == second_delivery
    assert guarded_erc20_vault.totalBalances(alpha_token) == deposit_amount
    assert alpha_token.balanceOf(guarded_erc20_vault) == deposit_amount
    assert alpha_token.balanceOf(sally) == 0
    assert not ledger.hasFungibleAuction(bob, vault_id, alpha_token)

    alice_terms = credit_engine.getUserBorrowTerms(alice, True)
    sally_terms = credit_engine.getUserBorrowTerms(sally, True)
    assert alice_terms.collateralVal == first_spent
    assert sally_terms.collateralVal == second_spent
    assert alice_terms.debtTerms.ltv == 50_00
    assert sally_terms.debtTerms.ltv == 50_00


def test_guarded_external_delivery_matches_recipient_vault_and_debt_deltas(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createAuctionParams,
    createDebtTerms,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
    teller,
    credit_engine,
    mock_price_source,
    ledger,
    guarded_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_guarded_vault(
        vault_book,
        governance,
        guarded_erc20_vault,
    )
    _configure_guarded_auction_assets(
        (alpha_token,),
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createAuctionParams,
        createDebtTerms,
        mock_price_source,
        green_token,
    )
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    _open_guarded_auctions(
        ((alpha_token, alpha_token_whale, deposit_amount),),
        100 * EIGHTEEN_DECIMALS,
        guarded_erc20_vault,
        vault_id,
        performDeposit,
        teller,
        mock_price_source,
        {"seller": bob, "caller": sally, "ledger": ledger},
    )

    max_green = 10 * EIGHTEEN_DECIMALS
    expected_delivery = 40 * EIGHTEEN_DECIMALS
    _fund_buyer(green_token, whale, teller, alice, max_green)
    buyer_green_before = green_token.balanceOf(alice)
    buyer_token_before = alpha_token.balanceOf(alice)
    vault_custody_before = alpha_token.balanceOf(guarded_erc20_vault)
    vault_nominal_before = guarded_erc20_vault.totalBalances(alpha_token)
    seller_nominal_before = guarded_erc20_vault.userBalances(bob, alpha_token)
    debt_before = credit_engine.getUserDebtAmount(bob)

    spent = teller.buyFungibleAuction(
        bob,
        vault_id,
        alpha_token,
        max_green,
        False,
        False,
        False,
        sender=alice,
    )

    assert spent == max_green
    assert green_token.balanceOf(alice) == buyer_green_before - spent
    assert credit_engine.getUserDebtAmount(bob) == debt_before - spent
    assert alpha_token.balanceOf(alice) - buyer_token_before == expected_delivery
    assert vault_custody_before - alpha_token.balanceOf(
        guarded_erc20_vault
    ) == expected_delivery
    assert vault_nominal_before - guarded_erc20_vault.totalBalances(
        alpha_token
    ) == expected_delivery
    assert seller_nominal_before - guarded_erc20_vault.userBalances(
        bob,
        alpha_token,
    ) == expected_delivery
    assert guarded_erc20_vault.userBalances(alice, alpha_token) == 0
    assert not ledger.isParticipatingInVault(alice, vault_id)

    purchase = filter_logs(teller, "FungAuctionPurchased")
    withdrawal = filter_logs(
        teller,
        "GuardedErc20VaultWithdrawal",
    )
    assert len(purchase) == len(withdrawal) == 1
    assert purchase[0].greenSpent == spent
    assert purchase[0].collateralAmountSent == expected_delivery
    assert withdrawal[0].amount == expected_delivery


@pytest.mark.parametrize(
    ("transfer_mode", "vault_surplus"),
    (
        pytest.param(1, 1, id="exact-vault-outflow"),
        pytest.param(2, 0, id="exact-recipient-delivery"),
    ),
)
def test_guarded_external_route_distinguishes_m2_movement_checks(
    transfer_mode,
    vault_surplus,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createAuctionParams,
    createDebtTerms,
    performDeposit,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    credit_engine,
    mock_price_source,
    ledger,
    guarded_erc20_vault,
    vault_book,
    governance,
):
    token = boa.loads(
        M4_WITHDRAWAL_GUARD_TOKEN_SOURCE,
        name=f"m4_withdrawal_guard_token_{transfer_mode}",
        override_address=boa.env.generate_address(),
    )
    vault_id = _register_guarded_vault(
        vault_book,
        governance,
        guarded_erc20_vault,
    )
    _configure_guarded_auction_assets(
        (token,),
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createAuctionParams,
        createDebtTerms,
        mock_price_source,
        green_token,
    )
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    token.mint(alpha_token_whale, deposit_amount)
    _open_guarded_auctions(
        ((token, alpha_token_whale, deposit_amount),),
        100 * EIGHTEEN_DECIMALS,
        guarded_erc20_vault,
        vault_id,
        performDeposit,
        teller,
        mock_price_source,
        {"seller": bob, "caller": sally, "ledger": ledger},
    )
    if vault_surplus:
        token.mint(guarded_erc20_vault, vault_surplus)
    token.configure_transfer(transfer_mode)

    max_green = 10 * EIGHTEEN_DECIMALS
    _fund_buyer(green_token, whale, teller, alice, max_green)
    before = _auction_state(
        guarded_erc20_vault,
        (token,),
        green_token,
        teller,
        auction_house,
        credit_engine,
        ledger,
        bob,
        alice,
        vault_id,
    )

    with boa.reverts():
        teller.buyFungibleAuction(
            bob,
            vault_id,
            token,
            max_green,
            False,
            False,
            False,
            sender=alice,
        )

    assert _auction_state(
        guarded_erc20_vault,
        (token,),
        green_token,
        teller,
        auction_house,
        credit_engine,
        ledger,
        bob,
        alice,
        vault_id,
    ) == before


@pytest.mark.parametrize(
    "should_transfer_balance",
    (
        pytest.param(False, id="external-delivery"),
        pytest.param(True, id="guarded-internal"),
    ),
)
def test_one_unit_deficit_preserves_terms_and_rolls_back_auction_roots(
    should_transfer_balance,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createAuctionParams,
    createDebtTerms,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    credit_engine,
    mock_price_source,
    ledger,
    guarded_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_guarded_vault(
        vault_book,
        governance,
        guarded_erc20_vault,
    )
    debt_terms = _configure_guarded_auction_assets(
        (alpha_token,),
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createAuctionParams,
        createDebtTerms,
        mock_price_source,
        green_token,
    )
    _open_guarded_auctions(
        ((alpha_token, alpha_token_whale, 200 * EIGHTEEN_DECIMALS),),
        100 * EIGHTEEN_DECIMALS,
        guarded_erc20_vault,
        vault_id,
        performDeposit,
        teller,
        mock_price_source,
        {"seller": bob, "caller": sally, "ledger": ledger},
    )
    alpha_token.burn(1, sender=guarded_erc20_vault.address)

    assert guarded_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1) == (
        alpha_token.address,
        0,
    )
    terms = credit_engine.getUserBorrowTerms(bob, True)
    assert terms.collateralVal == 0
    assert terms.totalMaxDebt == 0
    assert terms.debtTerms.ltv == debt_terms[0]
    assert terms.debtTerms.redemptionThreshold == debt_terms[1]
    assert terms.debtTerms.liqThreshold == debt_terms[2]
    assert terms.debtTerms.liqFee == debt_terms[3]
    assert terms.debtTerms.borrowRate == debt_terms[4]

    max_green = 10 * EIGHTEEN_DECIMALS
    _fund_buyer(green_token, whale, teller, alice, max_green)
    before = _auction_state(
        guarded_erc20_vault,
        (alpha_token,),
        green_token,
        teller,
        auction_house,
        credit_engine,
        ledger,
        bob,
        alice,
        vault_id,
    )

    with boa.reverts():
        teller.buyFungibleAuction(
            bob,
            vault_id,
            alpha_token,
            max_green,
            False,
            should_transfer_balance,
            False,
            sender=alice,
        )

    assert _auction_state(
        guarded_erc20_vault,
        (alpha_token,),
        green_token,
        teller,
        auction_house,
        credit_engine,
        ledger,
        bob,
        alice,
        vault_id,
    ) == before


def test_guarded_external_batch_delivers_each_row_exactly(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createAuctionParams,
    createDebtTerms,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
    teller,
    credit_engine,
    mock_price_source,
    ledger,
    guarded_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_guarded_vault(
        vault_book,
        governance,
        guarded_erc20_vault,
    )
    tokens = (alpha_token, bravo_token)
    _configure_guarded_auction_assets(
        tokens,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createAuctionParams,
        createDebtTerms,
        mock_price_source,
        green_token,
    )
    _open_guarded_auctions(
        (
            (alpha_token, alpha_token_whale, 100 * EIGHTEEN_DECIMALS),
            (bravo_token, bravo_token_whale, 150 * EIGHTEEN_DECIMALS),
        ),
        100 * EIGHTEEN_DECIMALS,
        guarded_erc20_vault,
        vault_id,
        performDeposit,
        teller,
        mock_price_source,
        {"seller": bob, "caller": sally, "ledger": ledger},
    )

    max_per_row = 10 * EIGHTEEN_DECIMALS
    total_limit = 25 * EIGHTEEN_DECIMALS
    expected_per_row = 40 * EIGHTEEN_DECIMALS
    _fund_buyer(green_token, whale, teller, alice, total_limit)
    buyer_green_before = green_token.balanceOf(alice)
    debt_before = credit_engine.getUserDebtAmount(bob)
    recipient_before = {
        token.address: token.balanceOf(alice)
        for token in tokens
    }
    custody_before = {
        token.address: token.balanceOf(guarded_erc20_vault)
        for token in tokens
    }

    spent = teller.buyManyFungibleAuctions(
        [
            (bob, vault_id, alpha_token, max_per_row),
            (bob, vault_id, bravo_token, max_per_row),
        ],
        total_limit,
        False,
        False,
        False,
        sender=alice,
    )

    assert spent == 2 * max_per_row
    assert green_token.balanceOf(alice) == buyer_green_before - spent
    assert credit_engine.getUserDebtAmount(bob) == debt_before - spent
    for token in tokens:
        assert token.balanceOf(alice) - recipient_before[
            token.address
        ] == expected_per_row
        assert custody_before[token.address] - token.balanceOf(
            guarded_erc20_vault
        ) == expected_per_row
        assert guarded_erc20_vault.userBalances(alice, token) == 0

    purchase_events = filter_logs(teller, "FungAuctionPurchased")
    withdrawal_events = filter_logs(
        teller,
        "GuardedErc20VaultWithdrawal",
    )
    assert [event.collateralAmountSent for event in purchase_events] == [
        expected_per_row,
        expected_per_row,
    ]
    assert [event.amount for event in withdrawal_events] == [
        expected_per_row,
        expected_per_row,
    ]


@pytest.mark.parametrize(
    "should_transfer_balance",
    (
        pytest.param(False, id="external-delivery"),
        pytest.param(True, id="guarded-internal"),
    ),
)
def test_guarded_batch_later_deficit_rolls_back_every_earlier_row(
    should_transfer_balance,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createAuctionParams,
    createDebtTerms,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
    teller,
    auction_house,
    credit_engine,
    mock_price_source,
    ledger,
    guarded_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_guarded_vault(
        vault_book,
        governance,
        guarded_erc20_vault,
    )
    tokens = (alpha_token, bravo_token)
    _configure_guarded_auction_assets(
        tokens,
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createAuctionParams,
        createDebtTerms,
        mock_price_source,
        green_token,
    )
    _open_guarded_auctions(
        (
            (alpha_token, alpha_token_whale, 100 * EIGHTEEN_DECIMALS),
            (bravo_token, bravo_token_whale, 150 * EIGHTEEN_DECIMALS),
        ),
        100 * EIGHTEEN_DECIMALS,
        guarded_erc20_vault,
        vault_id,
        performDeposit,
        teller,
        mock_price_source,
        {"seller": bob, "caller": sally, "ledger": ledger},
    )
    bravo_token.burn(1, sender=guarded_erc20_vault.address)

    total_limit = 25 * EIGHTEEN_DECIMALS
    _fund_buyer(green_token, whale, teller, alice, total_limit)
    before = _auction_state(
        guarded_erc20_vault,
        tokens,
        green_token,
        teller,
        auction_house,
        credit_engine,
        ledger,
        bob,
        alice,
        vault_id,
    )

    with boa.reverts():
        teller.buyManyFungibleAuctions(
            [
                (bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS),
                (bob, vault_id, bravo_token, 10 * EIGHTEEN_DECIMALS),
            ],
            total_limit,
            False,
            should_transfer_balance,
            False,
            sender=alice,
        )

    assert _auction_state(
        guarded_erc20_vault,
        tokens,
        green_token,
        teller,
        auction_house,
        credit_engine,
        ledger,
        bob,
        alice,
        vault_id,
    ) == before
