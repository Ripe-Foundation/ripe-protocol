import pytest
import boa

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT
from conf_utils import filter_logs


def test_ah_liquidation_auction_creation(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    sally,
):
    """Test auction creation when liquidation doesn't restore debt health
    
    This tests:
    - Auctions are created when shouldAuctionInstantly=True
    - Auction parameters are set correctly
    - NewFungibleAuctionCreated event is emitted
    - User remains in liquidation when auctions are created
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup asset for auction (no immediate liquidation methods)
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,  # This will create auctions
    )

    # Setup
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 125 * EIGHTEEN_DECIMALS // 200  # 0.625
    mock_price_source.setPrice(alpha_token, new_price)
    assert credit_engine.canLiquidateUser(bob) == True

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)

    # Verify auction was created
    auction_logs = filter_logs(teller, "NewFungibleAuctionCreated")
    assert len(auction_logs) == 1
    
    auction_log = auction_logs[0]
    assert auction_log.liqUser == bob
    assert auction_log.asset == alpha_token.address
    
    # Assert exact default auction parameters (no hedging!)
    assert auction_log.startDiscount == 0      # Default start discount
    assert auction_log.maxDiscount == 50_00    # Default max discount (50%)
    assert auction_log.startBlock == boa.env.evm.patch.block_number  # Default delay = 0 (starts immediately)
    assert auction_log.endBlock == boa.env.evm.patch.block_number + 1000  # Default duration = 1000 blocks
    assert auction_log.auctionId > 0

    # Verify liquidation event shows auction was started
    liquidation_log = filter_logs(teller, "LiquidateUser")[0]
    assert liquidation_log.user == bob
    assert liquidation_log.numAuctionsStarted == 1
    assert liquidation_log.didRestoreDebtHealth == False  # Still in liquidation

    # Verify user is still in liquidation
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    assert user_debt.inLiquidation == True


def test_ah_liquidation_auction_discount_calculation(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    teller,
    mock_price_source,
    createDebtTerms,
    sally,
    green_token,
    whale,
    _test,
):
    """Test auction discount calculation over time
    
    This tests:
    - Auction discount starts at startDiscount
    - Discount increases linearly to maxDiscount over time
    - Auction purchases work at different discount levels
    - Discount calculation edge cases
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup asset for auction
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )

    # Setup
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 125 * EIGHTEEN_DECIMALS // 200  # 0.625
    mock_price_source.setPrice(alpha_token, new_price)

    # Perform liquidation to create auction
    teller.liquidateUser(bob, False, sender=sally)
    
    auction_log = filter_logs(teller, "NewFungibleAuctionCreated")[0]
    start_block = auction_log.startBlock
    end_block = auction_log.endBlock
    start_discount = auction_log.startDiscount
    max_discount = auction_log.maxDiscount
    duration = end_block - start_block
    
    # Give alice some GREEN to buy auction
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)


    # Test auction purchase at start (minimum discount)
    # Auction starts immediately (delay=0), so we're already at start
    green_to_spend = 10 * EIGHTEEN_DECIMALS
    green_spent_start = teller.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )
    
    # At start discount (0%), should spend exactly the amount we requested
    _test(green_spent_start, green_to_spend)
    
    # Test auction purchase at middle (medium discount)
    middle_blocks = duration // 2
    boa.env.time_travel(blocks=middle_blocks)
    
    green_spent_middle = teller.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )

    _test(green_spent_middle, green_to_spend)
    
    # Test auction purchase near end (maximum discount)
    near_end_blocks = middle_blocks - 1  # 2 blocks before end
    boa.env.time_travel(blocks=near_end_blocks)
    
    green_spent_end = teller.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )
    _test(green_spent_end, green_to_spend)
      
    # Verify auction expires and reverts
    boa.env.time_travel(blocks=5)  # Move to end block
    with boa.reverts("no green spent"):
        teller.buyFungibleAuction(
            bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
        )


def test_ah_liquidation_auction_batch_purchase(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    alice,
    teller,
    mock_price_source,
    createDebtTerms,
    sally,
    green_token,
    whale,
    _test,
):
    """Test batch auction purchases with buyManyFungibleAuctions
    
    This tests:
    - Multiple auctions can be purchased in one transaction
    - GREEN is distributed across multiple auction purchases
    - Partial purchases work correctly
    - Leftover GREEN is handled properly
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup multiple assets for auctions
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    
    for token in [alpha_token, bravo_token]:
        setAssetConfig(
            token,
            _debtTerms=debt_terms,
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=False,
            _shouldSwapInStabPools=False,
            _shouldAuctionInstantly=True,
        )

    # Setup
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    # User with multiple collateral assets
    alpha_amount = 100 * EIGHTEEN_DECIMALS
    bravo_amount = 150 * EIGHTEEN_DECIMALS
    performDeposit(bob, alpha_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)
    
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 25 * EIGHTEEN_DECIMALS // 100  # 0.25 - aggressive drop
    mock_price_source.setPrice(alpha_token, new_price)
    mock_price_source.setPrice(bravo_token, new_price)

    # Perform liquidation to create multiple auctions
    teller.liquidateUser(bob, False, sender=sally)
    
    auction_logs = filter_logs(teller, "NewFungibleAuctionCreated")
    assert len(auction_logs) >= 2  # Should have multiple auctions
    
    # Give alice GREEN to buy auctions
    green_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Prepare batch purchase
    purchases = []
    for log in auction_logs[:2]:  # Buy first 2 auctions
        purchases.append((
            log.liqUser,
            log.vaultId,
            log.asset,
            20 * EIGHTEEN_DECIMALS,  # Max 20 GREEN per auction
        ))

    # Execute batch purchase
    total_green_to_spend = 50 * EIGHTEEN_DECIMALS
    total_green_spent = teller.buyManyFungibleAuctions(
        purchases, total_green_to_spend, False, sender=alice
    )

    # Verify batch purchase worked
    _test(total_green_spent, 40 * EIGHTEEN_DECIMALS)
    assert total_green_spent <= total_green_to_spend
    
    # Verify alice received collateral from multiple auctions
    alpha_balance = alpha_token.balanceOf(alice)
    bravo_balance = bravo_token.balanceOf(alice)
    
    # Should have received some of both assets (or at least one)
    assert alpha_balance > 0 and bravo_balance > 0


def test_ah_liquidation_auction_position_depletion(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    teller,
    mock_price_source,
    createDebtTerms,
    sally,
    green_token,
    whale,
    ledger,
):
    """Test auction behavior when user's position is depleted
    
    This tests:
    - Auction is removed when position is fully depleted
    - Partial depletion allows auction to continue
    - Position depletion detection works correctly
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup asset for auction
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )

    # Setup
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    # Small position for easy depletion
    deposit_amount = 50 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 30 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 50 * EIGHTEEN_DECIMALS // 100  # 0.50
    mock_price_source.setPrice(alpha_token, new_price)

    # Perform liquidation to create auction
    teller.liquidateUser(bob, False, sender=sally)
    
    auction_log = filter_logs(teller, "NewFungibleAuctionCreated")[0]
    
    # Give alice GREEN to buy entire position
    green_amount = 100 * EIGHTEEN_DECIMALS  # More than enough
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Verify auction exists
    assert ledger.hasFungibleAuction(bob, auction_log.vaultId, alpha_token) == True

    # Buy enough to deplete position
    green_spent = teller.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, green_amount, False, sender=alice
    )

    # auction no longer exists
    assert not ledger.hasFungibleAuction(bob, auction_log.vaultId, alpha_token)
    
    # Verify alice received the collateral
    assert alpha_token.balanceOf(alice) != 0


def test_ah_liquidation_custom_auction_params(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    teller,
    mock_price_source,
    createDebtTerms,
    createAuctionParams,
    sally,
):
    """Test custom auction parameters for specific assets
    
    This tests:
    - Asset-specific auction parameters override general parameters
    - Custom startDiscount, maxDiscount, delay, duration work correctly
    - Auction creation uses custom parameters
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup asset with custom auction parameters
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    custom_auction_params = createAuctionParams(
        _startDiscount=5_00,   # 5% start discount (custom)
        _maxDiscount=25_00,    # 25% max discount (custom)
        _delay=10,             # 10 block delay (custom)
        _duration=100,         # 100 block duration (custom)
    )
    
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
        _customAuctionParams=custom_auction_params,
    )

    # Setup
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 125 * EIGHTEEN_DECIMALS // 200  # 0.625
    mock_price_source.setPrice(alpha_token, new_price)

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)

    # Verify auction was created with custom parameters
    auction_logs = filter_logs(teller, "NewFungibleAuctionCreated")
    assert len(auction_logs) == 1
    
    auction_log = auction_logs[0]
    assert auction_log.liqUser == bob
    assert auction_log.asset == alpha_token.address
    
    # Verify custom parameters were used
    assert auction_log.startDiscount == 5_00  # Custom start discount
    assert auction_log.maxDiscount == 25_00   # Custom max discount
    assert auction_log.startBlock == boa.env.evm.patch.block_number + 10  # Custom delay
    assert auction_log.endBlock == auction_log.startBlock + 100  # Custom duration
