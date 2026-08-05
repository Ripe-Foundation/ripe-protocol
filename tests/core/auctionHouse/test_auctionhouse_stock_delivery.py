"""Track 8 M4 composed stock delivery proof for unchanged AuctionHouse ordering."""

import boa
import pytest

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS
from tests.vaults.test_basic_vault_safety import (
    _register_safe_nominal_vault,
    safe_simple_erc20_vault,
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


def _configure_safe_nominal_auction_assets(
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


def _open_standard_auctions(
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


def test_standard_internal_two_buyer_sequence_caps_over_request_and_depletes_seller(
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
    safe_simple_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_safe_nominal_vault(
        vault_book,
        governance,
        safe_simple_erc20_vault,
    )
    _configure_safe_nominal_auction_assets(
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
    _open_standard_auctions(
        ((alpha_token, alpha_token_whale, deposit_amount),),
        debt_amount,
        safe_simple_erc20_vault,
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
    assert safe_simple_erc20_vault.userBalances(alice, alpha_token) == first_delivery
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
    assert safe_simple_erc20_vault.userBalances(bob, alpha_token) == 0
    assert safe_simple_erc20_vault.userBalances(alice, alpha_token) == first_delivery
    assert safe_simple_erc20_vault.userBalances(sally, alpha_token) == second_delivery
    assert safe_simple_erc20_vault.totalBalances(alpha_token) == deposit_amount
    assert alpha_token.balanceOf(safe_simple_erc20_vault) == deposit_amount
    assert alpha_token.balanceOf(sally) == 0
    assert not ledger.hasFungibleAuction(bob, vault_id, alpha_token)

    alice_terms = credit_engine.getUserBorrowTerms(alice, True)
    sally_terms = credit_engine.getUserBorrowTerms(sally, True)
    assert alice_terms.collateralVal == first_spent
    assert sally_terms.collateralVal == second_spent
    assert alice_terms.debtTerms.ltv == 50_00
    assert sally_terms.debtTerms.ltv == 50_00


def test_standard_external_delivery_matches_recipient_vault_and_debt_deltas(
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
    safe_simple_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_safe_nominal_vault(
        vault_book,
        governance,
        safe_simple_erc20_vault,
    )
    _configure_safe_nominal_auction_assets(
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
    _open_standard_auctions(
        ((alpha_token, alpha_token_whale, deposit_amount),),
        100 * EIGHTEEN_DECIMALS,
        safe_simple_erc20_vault,
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
    vault_custody_before = alpha_token.balanceOf(safe_simple_erc20_vault)
    vault_nominal_before = safe_simple_erc20_vault.totalBalances(alpha_token)
    seller_nominal_before = safe_simple_erc20_vault.userBalances(bob, alpha_token)
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
        safe_simple_erc20_vault
    ) == expected_delivery
    assert vault_nominal_before - safe_simple_erc20_vault.totalBalances(
        alpha_token
    ) == expected_delivery
    assert seller_nominal_before - safe_simple_erc20_vault.userBalances(
        bob,
        alpha_token,
    ) == expected_delivery
    assert safe_simple_erc20_vault.userBalances(alice, alpha_token) == 0
    assert not ledger.isParticipatingInVault(alice, vault_id)

    purchase = filter_logs(teller, "FungAuctionPurchased")
    withdrawal = filter_logs(
        teller,
        "SimpleErc20VaultWithdrawal",
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
def test_standard_external_route_distinguishes_m2_movement_checks(
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
    safe_simple_erc20_vault,
    vault_book,
    governance,
):
    token = boa.loads(
        M4_WITHDRAWAL_GUARD_TOKEN_SOURCE,
        name=f"m4_withdrawal_guard_token_{transfer_mode}",
        override_address=boa.env.generate_address(),
    )
    vault_id = _register_safe_nominal_vault(
        vault_book,
        governance,
        safe_simple_erc20_vault,
    )
    _configure_safe_nominal_auction_assets(
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
    _open_standard_auctions(
        ((token, alpha_token_whale, deposit_amount),),
        100 * EIGHTEEN_DECIMALS,
        safe_simple_erc20_vault,
        vault_id,
        performDeposit,
        teller,
        mock_price_source,
        {"seller": bob, "caller": sally, "ledger": ledger},
    )
    if vault_surplus:
        token.mint(safe_simple_erc20_vault, vault_surplus)
    token.configure_transfer(transfer_mode)

    max_green = 10 * EIGHTEEN_DECIMALS
    _fund_buyer(green_token, whale, teller, alice, max_green)
    before = _auction_state(
        safe_simple_erc20_vault,
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
        safe_simple_erc20_vault,
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
        pytest.param(True, id="standard-internal"),
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
    safe_simple_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_safe_nominal_vault(
        vault_book,
        governance,
        safe_simple_erc20_vault,
    )
    debt_terms = _configure_safe_nominal_auction_assets(
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
    _open_standard_auctions(
        ((alpha_token, alpha_token_whale, 200 * EIGHTEEN_DECIMALS),),
        100 * EIGHTEEN_DECIMALS,
        safe_simple_erc20_vault,
        vault_id,
        performDeposit,
        teller,
        mock_price_source,
        {"seller": bob, "caller": sally, "ledger": ledger},
    )
    alpha_token.burn(1, sender=safe_simple_erc20_vault.address)

    assert safe_simple_erc20_vault.getUserAssetAndAmountAtIndex(bob, 1) == (
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
        safe_simple_erc20_vault,
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
        safe_simple_erc20_vault,
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


def test_standard_external_batch_delivers_each_row_exactly(
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
    safe_simple_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_safe_nominal_vault(
        vault_book,
        governance,
        safe_simple_erc20_vault,
    )
    tokens = (alpha_token, bravo_token)
    _configure_safe_nominal_auction_assets(
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
    _open_standard_auctions(
        (
            (alpha_token, alpha_token_whale, 100 * EIGHTEEN_DECIMALS),
            (bravo_token, bravo_token_whale, 150 * EIGHTEEN_DECIMALS),
        ),
        100 * EIGHTEEN_DECIMALS,
        safe_simple_erc20_vault,
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
        token.address: token.balanceOf(safe_simple_erc20_vault)
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
            safe_simple_erc20_vault
        ) == expected_per_row
        assert safe_simple_erc20_vault.userBalances(alice, token) == 0

    purchase_events = filter_logs(teller, "FungAuctionPurchased")
    withdrawal_events = filter_logs(
        teller,
        "SimpleErc20VaultWithdrawal",
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
        pytest.param(True, id="standard-internal"),
    ),
)
def test_standard_batch_later_deficit_preserves_earlier_healthy_purchase(
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
    safe_simple_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_safe_nominal_vault(
        vault_book,
        governance,
        safe_simple_erc20_vault,
    )
    tokens = (alpha_token, bravo_token)
    _configure_safe_nominal_auction_assets(
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
    _open_standard_auctions(
        (
            (alpha_token, alpha_token_whale, 100 * EIGHTEEN_DECIMALS),
            (bravo_token, bravo_token_whale, 150 * EIGHTEEN_DECIMALS),
        ),
        100 * EIGHTEEN_DECIMALS,
        safe_simple_erc20_vault,
        vault_id,
        performDeposit,
        teller,
        mock_price_source,
        {"seller": bob, "caller": sally, "ledger": ledger},
    )
    bravo_token.burn(1, sender=safe_simple_erc20_vault.address)

    total_limit = 25 * EIGHTEEN_DECIMALS
    _fund_buyer(green_token, whale, teller, alice, total_limit)
    expected_spent = 10 * EIGHTEEN_DECIMALS
    expected_alpha = 40 * EIGHTEEN_DECIMALS
    green_before = green_token.balanceOf(alice)
    debt_before = credit_engine.getUserDebtAmount(bob)
    alpha_custody_before = alpha_token.balanceOf(safe_simple_erc20_vault)
    alpha_recipient_before = alpha_token.balanceOf(alice)

    spent = teller.buyManyFungibleAuctions(
        [
            (bob, vault_id, alpha_token, expected_spent),
            (bob, vault_id, bravo_token, expected_spent),
        ],
        total_limit,
        False,
        should_transfer_balance,
        False,
        sender=alice,
    )

    assert spent == expected_spent
    assert green_token.balanceOf(alice) == green_before - expected_spent
    assert credit_engine.getUserDebtAmount(bob) == debt_before - expected_spent
    assert safe_simple_erc20_vault.userBalances(bob, alpha_token) == (
        100 * EIGHTEEN_DECIMALS - expected_alpha
    )
    assert safe_simple_erc20_vault.userBalances(bob, bravo_token) == (
        150 * EIGHTEEN_DECIMALS
    )
    assert safe_simple_erc20_vault.userBalances(alice, bravo_token) == 0
    assert bravo_token.balanceOf(safe_simple_erc20_vault) == (
        150 * EIGHTEEN_DECIMALS - 1
    )

    if should_transfer_balance:
        assert alpha_token.balanceOf(safe_simple_erc20_vault) == alpha_custody_before
        assert alpha_token.balanceOf(alice) == alpha_recipient_before
        assert safe_simple_erc20_vault.userBalances(alice, alpha_token) == expected_alpha
        delivery_events = filter_logs(teller, "SimpleErc20VaultTransfer")
    else:
        assert alpha_token.balanceOf(safe_simple_erc20_vault) == (
            alpha_custody_before - expected_alpha
        )
        assert alpha_token.balanceOf(alice) == alpha_recipient_before + expected_alpha
        assert safe_simple_erc20_vault.userBalances(alice, alpha_token) == 0
        delivery_events = filter_logs(teller, "SimpleErc20VaultWithdrawal")

    purchase_events = filter_logs(teller, "FungAuctionPurchased")
    assert len(purchase_events) == len(delivery_events) == 1
    assert purchase_events[0].liqAsset == alpha_token.address
    assert purchase_events[0].greenSpent == expected_spent
    assert purchase_events[0].collateralAmountSent == expected_alpha
    assert ledger.hasFungibleAuction(bob, vault_id, alpha_token)
    assert ledger.hasFungibleAuction(bob, vault_id, bravo_token)


def test_standard_deficit_does_not_block_cross_vault_auction_only_liquidation(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createAuctionParams,
    createDebtTerms,
    performDeposit,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    deploy3r,
    bob,
    sally,
    teller,
    auction_house,
    credit_engine,
    mock_price_source,
    ledger,
    mission_control,
    stability_pool,
    endaoment_funds,
    endaoment_psm,
    safe_simple_erc20_vault,
    simple_erc20_vault,
    vault_book,
    governance,
    switchboard_alpha,
):
    stock_token = boa.load(
        "contracts/mock/MockStockTokenControls.vy",
        deploy3r,
        18,
        name="auction_only_stock_token",
    )
    safe_nominal_id = _register_safe_nominal_vault(
        vault_book,
        governance,
        safe_simple_erc20_vault,
    )
    simple_id = vault_book.getRegId(simple_erc20_vault)
    stab_id = vault_book.getRegId(stability_pool)
    amount = 100 * EIGHTEEN_DECIMALS

    # Reachability control: the same Stock model must actually arrive in the
    # Stability pool when that route is enabled and its backing is healthy.
    with boa.env.anchor():
        setGeneralConfig()
        setGeneralDebtConfig(_ltvPaybackBuffer=0)
        control_terms = createDebtTerms(
            _ltv=50_00,
            _redemptionThreshold=60_00,
            _liqThreshold=80_00,
            _liqFee=0,
            _borrowRate=0,
        )
        setAssetConfig(
            stock_token,
            _vaultIds=[safe_nominal_id],
            _debtTerms=control_terms,
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=False,
            _shouldSwapInStabPools=True,
            _shouldAuctionInstantly=False,
        )
        stab_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
        setAssetConfig(
            green_token,
            _vaultIds=[stab_id],
            _debtTerms=stab_terms,
            _shouldBurnAsPayment=True,
        )
        mission_control.setPriorityStabVaults(
            [(stab_id, green_token)],
            sender=switchboard_alpha.address,
        )
        mock_price_source.setPrice(stock_token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
        green_token.transfer(sally, amount, sender=whale)
        green_token.approve(teller, amount, sender=sally)
        teller.deposit(
            green_token,
            amount,
            sally,
            stability_pool,
            0,
            sender=sally,
        )
        stock_token.mint(bob, amount, sender=deploy3r)
        stock_token.approve(teller, amount, sender=bob)
        assert teller.deposit(
            stock_token,
            amount,
            bob,
            safe_simple_erc20_vault,
            sender=bob,
        ) == amount
        teller.borrow(40 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
        mock_price_source.setPrice(
            stock_token,
            40 * EIGHTEEN_DECIMALS // 100,
        )
        assert credit_engine.canLiquidateUser(bob)
        assert not auction_house.canStartAuction(
            bob,
            safe_nominal_id,
            stock_token,
        )

        teller.liquidateUser(bob, False, sender=sally)

        control_logs = filter_logs(teller, "CollateralSwappedWithStabPool")
        assert len(control_logs) == 1
        assert control_logs[0].liqAsset == stock_token.address
        assert control_logs[0].collateralAmountOut > 0
        assert stock_token.balanceOf(stability_pool) == (
            control_logs[0].collateralAmountOut
        )
        assert not ledger.hasFungibleAuction(
            bob,
            safe_nominal_id,
            stock_token,
        )

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
        _liqFee=0,
        _borrowRate=0,
    )
    setAssetConfig(
        stock_token,
        _vaultIds=[safe_nominal_id],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=True,
    )
    setAssetConfig(
        bravo_token,
        _vaultIds=[simple_id],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )
    stab_terms = createDebtTerms(0, 0, 0, 0, 0, 0)
    setAssetConfig(
        green_token,
        _vaultIds=[stab_id],
        _debtTerms=stab_terms,
        _shouldBurnAsPayment=True,
    )
    mission_control.setPriorityLiqAssetVaults(
        [(safe_nominal_id, stock_token.address)],
        sender=switchboard_alpha.address,
    )
    mission_control.setPriorityStabVaults(
        [(stab_id, green_token)],
        sender=switchboard_alpha.address,
    )
    for token in (stock_token, bravo_token, green_token):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)

    stock_token.mint(bob, amount, sender=deploy3r)
    stock_token.approve(teller, amount, sender=bob)
    assert teller.deposit(
        stock_token,
        amount,
        bob,
        safe_simple_erc20_vault,
        sender=bob,
    ) == amount
    performDeposit(
        bob,
        amount,
        bravo_token,
        bravo_token_whale,
        simple_erc20_vault,
    )
    green_token.transfer(sally, amount, sender=whale)
    green_token.approve(teller, amount, sender=sally)
    teller.deposit(
        green_token,
        amount,
        sally,
        stability_pool,
        0,
        sender=sally,
    )
    teller.borrow(80 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    stock_token.adminBurn(
        safe_simple_erc20_vault,
        1,
        sender=deploy3r,
    )

    liq_config = mission_control.getAssetLiqConfig(stock_token)
    assert liq_config.shouldSwapInStabPools
    assert not liq_config.shouldTransferToEndaoment
    assert liq_config.shouldAuctionInstantly
    assert credit_engine.canLiquidateUser(bob)
    assert not auction_house.canStartAuction(
        bob,
        safe_nominal_id,
        stock_token,
    )
    assert not auction_house.canStartAuction(
        bob,
        simple_id,
        bravo_token,
    )

    teller.liquidateUser(bob, False, sender=sally)

    assert not ledger.hasFungibleAuction(bob, safe_nominal_id, stock_token)
    assert ledger.hasFungibleAuction(bob, simple_id, bravo_token)
    assert not auction_house.canStartAuction(
        bob,
        safe_nominal_id,
        stock_token,
    )
    assert auction_house.canStartAuction(
        bob,
        simple_id,
        bravo_token,
    )
    assert not auction_house.canStartAuction(
        bob,
        999_999,
        stock_token,
    )
    assert not auction_house.startAuction(
        bob,
        safe_nominal_id,
        stock_token,
        sender=switchboard_alpha.address,
    )
    assert stock_token.balanceOf(safe_simple_erc20_vault) == amount - 1
    assert bravo_token.balanceOf(simple_erc20_vault) == amount
    assert stock_token.balanceOf(stability_pool) == 0
    assert stock_token.balanceOf(endaoment_funds) == 0
    assert stock_token.balanceOf(endaoment_psm) == 0
    assert filter_logs(teller, "CollateralSwappedWithStabPool") == []
