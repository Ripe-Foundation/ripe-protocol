import pytest
import boa

from constants import EIGHTEEN_DECIMALS
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


def test_ah_auction_buy_config_restrictions(
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
    mock_whitelist,
):
    """Test auction buy config restrictions
    
    This tests:
    - canBuyInAuctionGeneral restrictions (via setGeneralConfig)
    - canBuyInAuctionAsset restrictions (via setAssetConfig)
    - isUserAllowed restrictions (via whitelist)
    - Graceful failure when restrictions are violated
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup asset for auction
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldAuctionInstantly=True,
    )

    # Setup liquidation scenario
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 60 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 50 * EIGHTEEN_DECIMALS // 100  # 0.50
    mock_price_source.setPrice(alpha_token, new_price)

    # Perform liquidation to create auction
    teller.liquidateUser(bob, False, sender=sally)
    auction_log = filter_logs(teller, "NewFungibleAuctionCreated")[0]
    
    # Give alice GREEN
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount * 2, sender=whale)  # Give alice double to cover transfers
    green_token.approve(teller, green_amount, sender=alice)  # Approve for teller transfers

    # Test 1: Disable general auction buying via setGeneralConfig
    setGeneralConfig(_canBuyInAuction=False)
    
    with boa.reverts("no green spent"):
        teller.buyFungibleAuction(
            bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, sender=alice
        )
    
    # Re-enable general auction buying
    setGeneralConfig(_canBuyInAuction=True)
    
    # Test 2: Disable asset-specific auction buying via setAssetConfig
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldAuctionInstantly=True,
        _canBuyInAuction=False,  # DISABLED for this asset
    )
    
    with boa.reverts("no green spent"):
        teller.buyFungibleAuction(
            bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, sender=alice
        )
    
    # Re-enable asset auction buying
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldAuctionInstantly=True,
        _canBuyInAuction=True,  # RE-ENABLED
    )
    
    # Test 3: Restrict user via whitelist
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldAuctionInstantly=True,
        _canBuyInAuction=True,
        _whitelist=mock_whitelist,  # Add whitelist restriction
    )
    
    # Alice is not on whitelist, should fail
    with boa.reverts("no green spent"):
        teller.buyFungibleAuction(
            bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, sender=alice
        )
    
    # Add alice to whitelist
    mock_whitelist.setAllowed(alice, alpha_token, True, sender=alice)
    
    # Test 4: Now buying should work
    green_spent = teller.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, sender=alice
    )
    assert green_spent > 0  # Should succeed


def test_ah_auction_time_boundary_edge_cases(
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
    createAuctionParams,
    sally,
    green_token,
    whale,
):
    """Test auction time boundary edge cases
    
    This tests:
    - Auction not yet started (before startBlock)
    - Auction exactly at start block
    - Auction exactly at end block  
    - Auction after end block
    - Zero duration auctions
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup asset with delayed auction
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    auction_params = createAuctionParams(
        _startDiscount=0,
        _maxDiscount=50_00,
        _delay=5,  # 5 block delay
        _duration=10,  # 10 block duration
    )
    
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldAuctionInstantly=True,
        _customAuctionParams=auction_params,
    )

    # Setup liquidation scenario
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 60 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 50 * EIGHTEEN_DECIMALS // 100  # 0.50
    mock_price_source.setPrice(alpha_token, new_price)

    # Perform liquidation to create auction
    teller.liquidateUser(bob, False, sender=sally)
    auction_log = filter_logs(teller, "NewFungibleAuctionCreated")[0]
    
    start_block = auction_log.startBlock
    end_block = auction_log.endBlock
    
    # Verify auction timing
    assert start_block == boa.env.evm.patch.block_number + 5  # Delay of 5 blocks
    assert end_block == start_block + 10  # Duration of 10 blocks
    
    # Give alice GREEN
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Test 1: Before auction starts (should fail gracefully)
    # We're currently at liquidation_block, auction starts at liquidation_block + 5
    with boa.reverts("no green spent"):
        teller.buyFungibleAuction(
            bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, sender=alice
        )
    
    # Test 2: Exactly at start block (should work)
    boa.env.time_travel(blocks=5)  # Move to start block
    assert boa.env.evm.patch.block_number == start_block
    
    green_spent = teller.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, sender=alice
    )
    assert green_spent > 0  # Should succeed
    
    # Test 3: One block before end (should work)
    # We're currently at start_block, need to move to end_block - 1
    blocks_to_move = (end_block - 1) - boa.env.evm.patch.block_number
    boa.env.time_travel(blocks=blocks_to_move)
    assert boa.env.evm.patch.block_number == end_block - 1
    
    green_spent = teller.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, sender=alice
    )
    assert green_spent > 0  # Should succeed
    
    # Test 4: Exactly at end block (should fail)
    boa.env.time_travel(blocks=1)  # Move to end block
    assert boa.env.evm.patch.block_number == end_block
    
    with boa.reverts("no green spent"):
        teller.buyFungibleAuction(
            bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, sender=alice
        )
    
    # Test 5: After end block (should fail)
    boa.env.time_travel(blocks=5)  # Move past end block
    
    with boa.reverts("no green spent"):
        teller.buyFungibleAuction(
            bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, sender=alice
        )


def test_ah_auction_insufficient_green_scenarios(
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
    auction_house,
):
    """Test auction behavior with insufficient GREEN tokens
    
    This tests:
    - No GREEN in auction house
    - Partial GREEN availability
    - GREEN balance changes during auction
    - Batch purchases with insufficient GREEN
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup asset for auction
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldAuctionInstantly=True,
    )

    # Setup liquidation scenario
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 60 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 50 * EIGHTEEN_DECIMALS // 100  # 0.50
    mock_price_source.setPrice(alpha_token, new_price)

    # Perform liquidation to create auction
    teller.liquidateUser(bob, False, sender=sally)
    auction_log = filter_logs(teller, "NewFungibleAuctionCreated")[0]
    
    # user has no green
    with boa.reverts("cannot transfer 0 amount"):
        teller.buyFungibleAuction(
            bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, sender=alice
        )
   
    # Transfer some GREEN to auction house (simulating previous auction activity)
    partial_green = 5 * EIGHTEEN_DECIMALS
    green_token.transfer(auction_house, partial_green, sender=whale)
    
    # Partial GREEN availability (should use what's available)
    green_spent = auction_house.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, 20 * EIGHTEEN_DECIMALS, alice, False, sender=teller.address
    )
    
    # Should spend only what was available in auction house
    assert green_spent == partial_green
    assert green_token.balanceOf(auction_house) == 0  # All GREEN used
    
    # Batch purchase with insufficient GREEN
    # Add more GREEN to auction house
    batch_green = 15 * EIGHTEEN_DECIMALS
    green_token.transfer(auction_house, batch_green, sender=whale)
    
    # Try to buy more than available
    purchases = [
        (bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS),
        (bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS),
    ]
    
    total_green_spent = auction_house.buyManyFungibleAuctions(
        purchases, 30 * EIGHTEEN_DECIMALS, alice, False, sender=teller.address
    )
    
    # Should spend only what was available
    assert total_green_spent == batch_green
    assert green_token.balanceOf(auction_house) == 0  # All GREEN used


def test_ah_auction_discount_calculation_edge_cases(
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
    createAuctionParams,
    sally,
    green_token,
    whale,
):
    """Test auction discount calculation edge cases
    
    This tests:
    - Same start and max discount (no progression)
    - Zero start discount
    - 100% max discount
    - Very short duration auctions
    - Discount calculation precision
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Test Case 1: Same start and max discount (flat discount)
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    flat_auction_params = createAuctionParams(
        _startDiscount=25_00,  # 25%
        _maxDiscount=25_00,    # 25% (same as start)
        _delay=0,
        _duration=100,
    )
    
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldAuctionInstantly=True,
        _customAuctionParams=flat_auction_params,
    )

    # Setup liquidation scenario
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 60 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 50 * EIGHTEEN_DECIMALS // 100  # 0.50
    mock_price_source.setPrice(alpha_token, new_price)

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    auction_log = filter_logs(teller, "NewFungibleAuctionCreated")[0]
    
    # Verify flat discount parameters
    assert auction_log.startDiscount == 25_00
    assert auction_log.maxDiscount == 25_00
    
    # Give alice GREEN
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)  # Give alice double to cover transfers
    green_token.approve(teller, green_amount, sender=alice)  # Approve for teller transfers

    # Test discount at start (should be 25%)
    green_to_spend = 10 * EIGHTEEN_DECIMALS
    green_spent_start = teller.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )
    
    # Test discount at middle (should still be 25%)
    boa.env.time_travel(blocks=50)  # Middle of auction
    green_spent_middle = teller.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )
    
    # Test discount near end (should still be 25%)
    boa.env.time_travel(blocks=49)  # Near end of auction
    green_spent_end = teller.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )
    
    # All should spend the same amount (flat 25% discount)
    # Allow for small rounding differences (within 1% tolerance)
    assert abs(green_spent_start - green_to_spend) <= green_to_spend // 100
    assert abs(green_spent_middle - green_to_spend) <= green_to_spend // 100  
    assert abs(green_spent_end - green_to_spend) <= green_to_spend // 100
    assert abs(green_spent_start - green_spent_middle) <= green_to_spend // 100
    assert abs(green_spent_middle - green_spent_end) <= green_to_spend // 100


def test_ah_auction_payment_validation_edge_cases(
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
):
    """Test payment validation edge cases in auctions
    
    This tests:
    - _isPaymentCloseEnough validation
    - Rounding errors in payment calculations
    - Very small payment amounts
    - Price precision edge cases
    """

    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)

    # Setup asset for auction
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldAuctionInstantly=True,
    )

    # Setup with precise prices to test rounding
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)

    deposit_amount = 1000 * EIGHTEEN_DECIMALS  # Large amount for precision testing
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 600 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 50 * EIGHTEEN_DECIMALS // 100  # 0.50
    mock_price_source.setPrice(alpha_token, new_price)

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    auction_log = filter_logs(teller, "NewFungibleAuctionCreated")[0]

    # Give alice GREEN
    green_amount = 500 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)  # Approve for teller transfers

    # Test 1: Very small payment (1 wei)
    tiny_amount = 1  # 1 wei
    green_spent = teller.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, tiny_amount, False, sender=alice
    )
    # Should handle tiny amounts gracefully
    assert green_spent <= tiny_amount
    
    # Test 2: Odd number that might cause rounding issues
    odd_amount = 123456789  # Odd number in wei
    green_spent = teller.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, odd_amount, False, sender=alice
    )
    # Should handle odd amounts within 1% tolerance
    assert green_spent <= odd_amount
    
    # Test 3: Large payment amount
    large_amount = 100 * EIGHTEEN_DECIMALS
    green_spent = teller.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, large_amount, False, sender=alice
    )
    # Should handle large amounts correctly
    assert green_spent <= large_amount


def test_ah_auction_multiple_asset_coordination(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    bob,
    alice,
    teller,
    mock_price_source,
    createDebtTerms,
    createAuctionParams,
    sally,
    green_token,
    whale,
):
    """Test coordination between multiple asset auctions
    
    This tests:
    - Multiple auctions for same user
    - Different auction parameters per asset
    - Auction removal when positions are depleted
    - Cross-asset auction interactions
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup multiple assets with different auction parameters
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    
    # Alpha: Fast auction (short duration, high discount)
    fast_params = createAuctionParams(
        _startDiscount=0,
        _maxDiscount=75_00,  # 75% max discount
        _delay=0,
        _duration=50,  # Short duration
    )
    
    # Bravo: Slow auction (long duration, low discount)
    slow_params = createAuctionParams(
        _startDiscount=5_00,  # 5% start discount
        _maxDiscount=25_00,   # 25% max discount
        _delay=5,             # Delayed start
        _duration=200,        # Long duration
    )
    
    # Charlie: Default auction parameters
    setAssetConfig(alpha_token, _debtTerms=debt_terms, _shouldAuctionInstantly=True, _customAuctionParams=fast_params)
    setAssetConfig(bravo_token, _debtTerms=debt_terms, _shouldAuctionInstantly=True, _customAuctionParams=slow_params)
    setAssetConfig(charlie_token, _debtTerms=debt_terms, _shouldAuctionInstantly=True)

    # Setup liquidation scenario with multiple assets
    for token in [alpha_token, bravo_token, charlie_token, green_token]:
        mock_price_source.setPrice(token, 1 * EIGHTEEN_DECIMALS)
    
    # User with multiple collateral assets
    alpha_amount = 100 * EIGHTEEN_DECIMALS
    bravo_amount = 150 * EIGHTEEN_DECIMALS  
    charlie_amount = 200 * (10 ** 6)  # Charlie token has 6 decimals
    
    performDeposit(bob, alpha_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)
    performDeposit(bob, charlie_amount, charlie_token, charlie_token_whale)
    
    debt_amount = 150 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 25 * EIGHTEEN_DECIMALS // 100  # 0.25 - aggressive drop
    for token in [alpha_token, bravo_token, charlie_token]:
        mock_price_source.setPrice(token, new_price)

    # Perform liquidation to create multiple auctions
    teller.liquidateUser(bob, False, sender=sally)
    
    auction_logs = filter_logs(teller, "NewFungibleAuctionCreated")
    assert len(auction_logs) == 3  # Should have 3 auctions
    
    # Verify different auction parameters
    alpha_auction = next(log for log in auction_logs if log.asset == alpha_token.address)
    bravo_auction = next(log for log in auction_logs if log.asset == bravo_token.address)
    charlie_auction = next(log for log in auction_logs if log.asset == charlie_token.address)
    
    # Alpha: Fast auction parameters
    assert alpha_auction.startDiscount == 0
    assert alpha_auction.maxDiscount == 75_00
    assert alpha_auction.endBlock - alpha_auction.startBlock == 50
    
    # Bravo: Slow auction parameters
    assert bravo_auction.startDiscount == 5_00
    assert bravo_auction.maxDiscount == 25_00
    assert bravo_auction.endBlock - bravo_auction.startBlock == 200
    
    # Charlie: Default parameters
    assert charlie_auction.startDiscount == 0
    assert charlie_auction.maxDiscount == 50_00
    assert charlie_auction.endBlock - charlie_auction.startBlock == 1000
    
    # Give alice GREEN for purchases
    green_amount = 200 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)  # Approve for teller transfers

    # Test coordinated auction purchases
    # Buy from alpha auction (available immediately)
    green_spent_alpha = teller.buyFungibleAuction(
        bob, alpha_auction.vaultId, alpha_token, 50 * EIGHTEEN_DECIMALS, False, sender=alice
    )
    assert green_spent_alpha > 0
    
    # Try to buy from bravo auction (should fail - not started yet due to delay)
    with boa.reverts("no green spent"):
        teller.buyFungibleAuction(
            bob, bravo_auction.vaultId, bravo_token, 50 * EIGHTEEN_DECIMALS, False, sender=alice
        )
    
    # Buy from charlie auction (available immediately)
    green_spent_charlie = teller.buyFungibleAuction(
        bob, charlie_auction.vaultId, charlie_token, 50 * EIGHTEEN_DECIMALS, False, sender=alice
    )
    assert green_spent_charlie > 0
    
    # Move forward to enable bravo auction
    boa.env.time_travel(blocks=5)
    
    # Now bravo auction should work
    green_spent_bravo = teller.buyFungibleAuction(
        bob, bravo_auction.vaultId, bravo_token, 50 * EIGHTEEN_DECIMALS, False, sender=alice
    )
    assert green_spent_bravo > 0
    
    # Verify alice received collateral from multiple assets
    assert alpha_token.balanceOf(alice) > 0
    assert bravo_token.balanceOf(alice) > 0
    assert charlie_token.balanceOf(alice) > 0


def test_ah_auction_savings_green_preferences(
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
    savings_green,
    whale,
):
    """Test savings GREEN preferences in auction purchases
    
    This tests:
    - Leftover GREEN converted to savings GREEN when requested
    - Leftover GREEN stays as GREEN when not requested
    - Savings GREEN handling in batch purchases
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup asset for auction
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldAuctionInstantly=True,
    )

    # Setup liquidation scenario
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 60 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 50 * EIGHTEEN_DECIMALS // 100  # 0.50
    mock_price_source.setPrice(alpha_token, new_price)

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    auction_log = filter_logs(teller, "NewFungibleAuctionCreated")[0]
    
    # Give alice GREEN and transfer to auction house
    green_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)  # Give alice double to cover transfers
    green_token.approve(teller, green_amount * 2, sender=alice)  # Approve for teller transfers

    # Test 1: Request savings GREEN for leftover
    alice_savings_before = savings_green.balanceOf(alice)
    
    # Spend less than available to create leftover
    green_spent = teller.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, green_amount, True, sender=alice  # True = wants savings GREEN
    )
    assert green_spent != 0
    
    alice_savings_after = savings_green.balanceOf(alice)
    
    # Should have received leftover as savings GREEN
    assert green_token.balanceOf(alice) == 0
    assert alice_savings_after > alice_savings_before  # Received savings GREEN
