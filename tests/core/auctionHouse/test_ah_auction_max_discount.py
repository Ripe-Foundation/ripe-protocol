import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT, MAX_UINT256, ONE_YEAR
from conf_utils import buy_fungible_auction, filter_logs


def _old_progress(block_number, start_block, end_block):
    return (block_number - start_block) * HUNDRED_PERCENT // (end_block - start_block)


def _old_discount(block_number, start_block, end_block, start_discount, max_discount):
    if start_discount == max_discount:
        return start_discount
    progress = _old_progress(block_number, start_block, end_block)
    if progress == 0:
        return start_discount
    return start_discount + progress * (max_discount - start_discount) // HUNDRED_PERCENT


def _new_discount(block_number, start_block, end_block, start_discount, max_discount):
    if end_block <= start_block + 1:
        return max_discount
    return start_discount + (block_number - start_block) * (max_discount - start_discount) // (end_block - start_block - 1)


def _advance_to_block(block_number):
    blocks = block_number - boa.env.evm.patch.block_number
    assert blocks >= 0
    if blocks:
        boa.env.time_travel(blocks=blocks)
    assert boa.env.evm.patch.block_number == block_number


def _discount_from_purchase(green_spent, collateral_received, collateral_price):
    collateral_usd = collateral_received * collateral_price // EIGHTEEN_DECIMALS
    return HUNDRED_PERCENT - (green_spent * HUNDRED_PERCENT // collateral_usd)


def _assert_discount(actual, expected, tol=1):
    assert expected - tol <= actual <= expected + tol, (actual, expected)


def _open_auction(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    alpha_token,
    alpha_token_whale,
    green_token,
    bob,
    sally,
    start_discount,
    max_discount,
    duration,
    delay=0,
    deposit_amount=1_000 * EIGHTEEN_DECIMALS,
    debt_amount=400 * EIGHTEEN_DECIMALS,
    borrow_rate=0,
    liq_threshold=80_00,
    ltv=50_00,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=createDebtTerms(
            _liqThreshold=liq_threshold,
            _liqFee=0,
            _ltv=ltv,
            _borrowRate=borrow_rate,
        ),
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
        _customAuctionParams=createAuctionParams(
            _startDiscount=start_discount,
            _maxDiscount=max_discount,
            _delay=delay,
            _duration=duration,
        ),
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    teller.borrow(debt_amount, bob, False, sender=bob)
    mock_price_source.setPrice(alpha_token, 40 * EIGHTEEN_DECIMALS // 100)
    teller.liquidateUser(bob, False, sender=sally)
    return filter_logs(teller, "FungibleAuctionUpdated")[0]


def test_sc30_progress_formula_identity_reaches_max_at_last_purchasable_block():
    """Document the closed-form identity. Contract coverage is the live tests below."""
    start_discount = 0
    max_discount = 50_00
    start_block = 100
    duration = 100
    end_block = start_block + duration
    last_purchasable = end_block - 1
    old = _old_discount(last_purchasable, start_block, end_block, start_discount, max_discount)
    new = _new_discount(last_purchasable, start_block, end_block, start_discount, max_discount)
    assert old < max_discount
    assert new == max_discount
    assert _new_discount(start_block, start_block, end_block, start_discount, max_discount) == start_discount


def test_sc30_interpolation_guard_is_last_purchasable_not_duration_one():
    from pathlib import Path

    src = Path("contracts/core/AuctionHouse.vy").read_text()
    assert src.count("if auc.endBlock > auc.startBlock + 1:") == 1
    assert "(auc.endBlock - auc.startBlock - 1)" in src
    duration_one_only = "if auc.endBlock > auc.startBlock:"
    assert duration_one_only not in src.replace("if auc.endBlock > auc.startBlock + 1:", "")

    start_discount = 0
    max_discount = 50_00
    start_block = 100
    duration_one_end = start_block + 1
    assert _new_discount(start_block, start_block, duration_one_end, start_discount, max_discount) == max_discount
    try:
        _ = (start_block - start_block) * (max_discount - start_discount) // (duration_one_end - start_block - 1)
        raise AssertionError("duration-one-only denominator must be zero")
    except ZeroDivisionError:
        pass


def test_sc30_multi_block_window_reaches_exact_max_discount(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    auction_house,
    ledger,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    start_discount = 0
    max_discount = 50_00
    duration = 20
    auction = _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        start_discount,
        max_discount,
        duration,
        delay=2,
    )
    vault_id = auction.vaultId
    start_block = auction.startBlock
    end_block = auction.endBlock
    assert end_block - start_block == duration
    price = 40 * EIGHTEEN_DECIMALS // 100
    green_token.transfer(alice, 200 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 200 * EIGHTEEN_DECIMALS, sender=alice)
    spend = 5 * EIGHTEEN_DECIMALS

    with boa.reverts("no green spent"):
        buy_fungible_auction(teller, bob, vault_id, alpha_token, spend, False, sender=alice)
    assert not auction_house.removeExpiredFungibleAuction(bob, vault_id, alpha_token, sender=alice)

    _advance_to_block(start_block)
    before = alpha_token.balanceOf(alice)
    spent = buy_fungible_auction(teller, bob, vault_id, alpha_token, spend, False, sender=alice)
    _assert_discount(
        _discount_from_purchase(spent, alpha_token.balanceOf(alice) - before, price),
        start_discount,
    )
    assert not auction_house.removeExpiredFungibleAuction(bob, vault_id, alpha_token, sender=alice)

    previous = start_discount
    for block in (start_block + 1, start_block + duration // 2, end_block - 2):
        _advance_to_block(block)
        before = alpha_token.balanceOf(alice)
        spent = buy_fungible_auction(teller, bob, vault_id, alpha_token, spend, False, sender=alice)
        discount = _discount_from_purchase(spent, alpha_token.balanceOf(alice) - before, price)
        assert start_discount <= discount <= max_discount
        assert discount >= previous
        previous = discount
        assert not auction_house.removeExpiredFungibleAuction(bob, vault_id, alpha_token, sender=alice)

    _advance_to_block(end_block - 1)
    before = alpha_token.balanceOf(alice)
    spent = buy_fungible_auction(teller, bob, vault_id, alpha_token, spend, False, sender=alice)
    _assert_discount(
        _discount_from_purchase(spent, alpha_token.balanceOf(alice) - before, price),
        max_discount,
    )
    assert not auction_house.removeExpiredFungibleAuction(bob, vault_id, alpha_token, sender=alice)

    _advance_to_block(end_block)
    with boa.reverts("no green spent"):
        buy_fungible_auction(teller, bob, vault_id, alpha_token, spend, False, sender=alice)
    assert auction_house.removeExpiredFungibleAuction(bob, vault_id, alpha_token, sender=alice)
    assert not ledger.hasFungibleAuction(bob, vault_id, alpha_token)


def test_sc30_flat_discount_and_single_block_use_max_discount(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    auction_house,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    auction = _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        25_00,
        25_00,
        8,
    )
    price = 40 * EIGHTEEN_DECIMALS // 100
    green_token.transfer(alice, 50 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 50 * EIGHTEEN_DECIMALS, sender=alice)
    spend = 4 * EIGHTEEN_DECIMALS

    _advance_to_block(auction.startBlock)
    before = alpha_token.balanceOf(alice)
    spent = buy_fungible_auction(teller, bob, auction.vaultId, alpha_token, spend, False, sender=alice)
    _assert_discount(
        _discount_from_purchase(spent, alpha_token.balanceOf(alice) - before, price),
        25_00,
    )

    _advance_to_block(auction.endBlock - 1)
    before = alpha_token.balanceOf(alice)
    spent = buy_fungible_auction(teller, bob, auction.vaultId, alpha_token, spend, False, sender=alice)
    _assert_discount(
        _discount_from_purchase(spent, alpha_token.balanceOf(alice) - before, price),
        25_00,
    )
    assert not auction_house.removeExpiredFungibleAuction(
        bob,
        auction.vaultId,
        alpha_token,
        sender=alice,
    )


def test_sc30_duration_one_uses_max_discount_on_only_purchasable_block(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    auction_house,
    ledger,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    auction = _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        5_00,
        40_00,
        1,
    )
    assert auction.endBlock == auction.startBlock + 1
    price = 40 * EIGHTEEN_DECIMALS // 100
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)

    _advance_to_block(auction.startBlock)
    before = alpha_token.balanceOf(alice)
    spent = buy_fungible_auction(
        teller,
        bob,
        auction.vaultId,
        alpha_token,
        5 * EIGHTEEN_DECIMALS,
        False,
        sender=alice,
    )
    _assert_discount(
        _discount_from_purchase(spent, alpha_token.balanceOf(alice) - before, price),
        40_00,
    )
    assert not auction_house.removeExpiredFungibleAuction(
        bob,
        auction.vaultId,
        alpha_token,
        sender=alice,
    )

    _advance_to_block(auction.endBlock)
    with boa.reverts("no green spent"):
        buy_fungible_auction(
            teller,
            bob,
            auction.vaultId,
            alpha_token,
            5 * EIGHTEEN_DECIMALS,
            False,
            sender=alice,
        )
    assert auction_house.removeExpiredFungibleAuction(
        bob,
        auction.vaultId,
        alpha_token,
        sender=alice,
    )
    assert not ledger.hasFungibleAuction(bob, auction.vaultId, alpha_token)


def test_sc30_duration_two_starts_at_start_discount_and_ends_at_max(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    auction_house,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    start_discount = 10_00
    max_discount = 40_00
    auction = _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        start_discount,
        max_discount,
        2,
    )
    assert auction.endBlock == auction.startBlock + 2
    price = 40 * EIGHTEEN_DECIMALS // 100
    green_token.transfer(alice, 40 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 40 * EIGHTEEN_DECIMALS, sender=alice)
    spend = 5 * EIGHTEEN_DECIMALS

    _advance_to_block(auction.startBlock)
    before = alpha_token.balanceOf(alice)
    spent = buy_fungible_auction(teller, bob, auction.vaultId, alpha_token, spend, False, sender=alice)
    _assert_discount(
        _discount_from_purchase(spent, alpha_token.balanceOf(alice) - before, price),
        start_discount,
    )

    _advance_to_block(auction.endBlock - 1)
    before = alpha_token.balanceOf(alice)
    spent = buy_fungible_auction(teller, bob, auction.vaultId, alpha_token, spend, False, sender=alice)
    _assert_discount(
        _discount_from_purchase(spent, alpha_token.balanceOf(alice) - before, price),
        max_discount,
    )


def test_sc30_max_accepted_delay_creates_auction(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    alpha_token,
    alpha_token_whale,
    green_token,
    bob,
    sally,
    switchboard_alpha,
):
    # uint32 max is the Switchboard delay cap. Creation must not revert
    # on block.number + delay; the next value is rejected by the validator.
    max_auction_delay = 2**32 - 1
    assert switchboard_alpha.areValidAuctionParams(
        (True, 10_00, 40_00, max_auction_delay, 1)
    )
    assert not switchboard_alpha.areValidAuctionParams(
        (True, 10_00, 40_00, max_auction_delay + 1, 1)
    )
    before_block = boa.env.evm.patch.block_number
    auction = _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        10_00,
        40_00,
        1,
        delay=max_auction_delay,
    )
    assert auction.startBlock >= before_block + max_auction_delay
    assert auction.endBlock == auction.startBlock + 1


def test_sc30_zero_length_window_cannot_be_purchased(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    auction_house,
    ledger,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    auction = _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        5_00,
        40_00,
        20,
    )
    stored = ledger.getFungibleAuction(bob, auction.vaultId, alpha_token)
    assert ledger.setFungibleAuction(
        bob,
        auction.vaultId,
        alpha_token,
        (
            stored.liqUser,
            stored.vaultId,
            stored.asset,
            stored.startDiscount,
            stored.maxDiscount,
            stored.startBlock,
            stored.startBlock,
            stored.isActive,
        ),
        sender=auction_house.address,
    )
    mutated = ledger.getFungibleAuction(bob, auction.vaultId, alpha_token)
    assert mutated.endBlock == mutated.startBlock
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    _advance_to_block(mutated.startBlock)
    with boa.reverts("no green spent"):
        buy_fungible_auction(
            teller,
            bob,
            auction.vaultId,
            alpha_token,
            5 * EIGHTEEN_DECIMALS,
            False,
            sender=alice,
        )


def test_sc30_stored_overflowing_window_purchases_at_max_discount(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    auction_house,
    ledger,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    # Switchboard now rejects this duration. A stored auction in the old
    # overflowing domain must still settle at maxDiscount instead of revert.
    start_discount = 0
    max_discount = 50_00
    auction = _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        start_discount,
        max_discount,
        20,
    )
    overflowing_duration = MAX_UINT256 // max_discount + 2
    stored = ledger.getFungibleAuction(bob, auction.vaultId, alpha_token)
    assert ledger.setFungibleAuction(
        bob,
        auction.vaultId,
        alpha_token,
        (
            stored.liqUser,
            stored.vaultId,
            stored.asset,
            stored.startDiscount,
            stored.maxDiscount,
            stored.startBlock,
            stored.startBlock + overflowing_duration,
            stored.isActive,
        ),
        sender=auction_house.address,
    )
    overflow_block = stored.startBlock + MAX_UINT256 // max_discount + 1
    boa.env.evm.patch.block_number = overflow_block
    price = 40 * EIGHTEEN_DECIMALS // 100
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    before = alpha_token.balanceOf(alice)
    spent = buy_fungible_auction(
        teller,
        bob,
        auction.vaultId,
        alpha_token,
        4 * EIGHTEEN_DECIMALS,
        False,
        sender=alice,
    )
    _assert_discount(
        _discount_from_purchase(spent, alpha_token.balanceOf(alice) - before, price),
        max_discount,
    )


def test_sc30_max_duration_and_rounding_never_exceed_max_discount(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    auction_house,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    bob,
    alice,
    sally,
):
    # 1_000_000 is a large but ordinary governance-valid duration, not the
    # interpolation overflow boundary. That bound is covered by
    # areValidAuctionParams and the overflow-safe purchase path.
    start_discount = 1_00
    max_discount = 50_00
    duration = 1_000_000
    auction = _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        start_discount,
        max_discount,
        duration,
    )
    price = 40 * EIGHTEEN_DECIMALS // 100
    green_token.transfer(alice, 20 * EIGHTEEN_DECIMALS, sender=whale)
    green_token.approve(teller, 20 * EIGHTEEN_DECIMALS, sender=alice)
    spend = 4 * EIGHTEEN_DECIMALS

    _advance_to_block(auction.startBlock)
    before = alpha_token.balanceOf(alice)
    spent = buy_fungible_auction(
        teller,
        bob,
        auction.vaultId,
        alpha_token,
        spend,
        False,
        sender=alice,
    )
    _assert_discount(
        _discount_from_purchase(spent, alpha_token.balanceOf(alice) - before, price),
        start_discount,
    )

    mid = auction.startBlock + duration // 2
    _advance_to_block(mid)
    before = alpha_token.balanceOf(alice)
    spent = buy_fungible_auction(
        teller,
        bob,
        auction.vaultId,
        alpha_token,
        spend,
        False,
        sender=alice,
    )
    mid_discount = _discount_from_purchase(
        spent,
        alpha_token.balanceOf(alice) - before,
        price,
    )
    assert start_discount <= mid_discount <= max_discount

    _advance_to_block(auction.endBlock - 1)
    before = alpha_token.balanceOf(alice)
    spent = buy_fungible_auction(
        teller,
        bob,
        auction.vaultId,
        alpha_token,
        spend,
        False,
        sender=alice,
    )
    _assert_discount(
        _discount_from_purchase(spent, alpha_token.balanceOf(alice) - before, price),
        max_discount,
    )
    assert not auction_house.removeExpiredFungibleAuction(
        bob,
        auction.vaultId,
        alpha_token,
        sender=alice,
    )


def test_sc30_max_discount_purchase_preserves_live_debt_cap(
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
    alpha_token,
    alpha_token_whale,
    green_token,
    savings_green,
    whale,
    bob,
    alice,
    sally,
):
    auction = _open_auction(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        createAuctionParams,
        performDeposit,
        mock_price_source,
        teller,
        alpha_token,
        alpha_token_whale,
        green_token,
        bob,
        sally,
        0,
        50_00,
        25,
        deposit_amount=1_000 * EIGHTEEN_DECIMALS,
        debt_amount=100 * EIGHTEEN_DECIMALS,
        borrow_rate=10_00,
        liq_threshold=20_00,
        ltv=10_00,
    )
    _advance_to_block(auction.endBlock - 1)
    boa.env.evm.patch.timestamp += ONE_YEAR
    live_debt = credit_engine.getUserDebtAmount(bob)
    assert live_debt > 0

    payment = live_debt * 3
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    payer_before = green_token.balanceOf(alice)
    buyer_before = alpha_token.balanceOf(alice)
    borrower_sgreen_before = savings_green.balanceOf(bob)
    supply_before = green_token.totalSupply()

    green_spent = buy_fungible_auction(
        teller,
        bob,
        auction.vaultId,
        alpha_token,
        payment,
        False,
        False,
        False,
        sender=alice,
    )
    collateral_received = alpha_token.balanceOf(alice) - buyer_before
    collateral_value = collateral_received * 40 * EIGHTEEN_DECIMALS // (100 * EIGHTEEN_DECIMALS)
    net_rate = HUNDRED_PERCENT - 50_00
    expected_collateral_value = live_debt * HUNDRED_PERCENT // net_rate
    expected_spend = expected_collateral_value * net_rate // HUNDRED_PERCENT
    assert expected_spend <= live_debt
    assert green_spent == expected_spend
    assert payer_before - green_token.balanceOf(alice) == expected_spend
    assert collateral_value == expected_collateral_value
    assert savings_green.balanceOf(bob) == borrower_sgreen_before
    assert green_token.totalSupply() == supply_before - expected_spend
    remaining = ledger.userDebt(bob).amount
    assert remaining == live_debt - expected_spend
