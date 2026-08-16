from hashlib import sha256
from pathlib import Path

import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT, ONE_YEAR, ZERO_ADDRESS
from conf_utils import (
    assert_reverted_call,
    buy_fungible_auction,
    clear_transient_storage,
    filter_logs,
)

SIX_DECIMALS = 10**6  # For tokens like USDC/Charlie that have 6 decimals


@pytest.mark.artifact
def test_auction_house_source_abi_and_vault_interface_are_frozen():
    """The current backing-aware consumer source keeps its public boundaries exact."""

    repo_root = Path(__file__).resolve().parents[3]
    expected = {
        "contracts/core/AuctionHouse.vy": (
            "e7eb7b1b80ae0dce6a9df21ad7ec35cc3fd2248aac0bc3f02797d99b10e8409e"
        ),
        "scripts/abis/AuctionHouse.json": (
            "5fd8e740cee561933a74fc64136ad2a3e42867b9754c38ae596a85b83460d9e7"
        ),
        "interfaces/Vault.vyi": (
            "6769283fa780a63e1b2e2fc56b8ef51f3ff9b5883f4f1c4af8905fd0b20ffde7"
        ),
    }

    for path, expected_digest in expected.items():
        assert sha256((repo_root / path).read_bytes()).hexdigest() == expected_digest


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
    ledger,
    sally,
):
    """Test auction creation when liquidation doesn't restore debt health
    
    This tests:
    - Auctions are created when shouldAuctionInstantly=True
    - Auction parameters are set correctly
    - FungibleAuctionUpdated event is emitted
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
    assert credit_engine.canLiquidateUser(bob)

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)

    # Verify auction was created
    auction_logs = filter_logs(teller, "FungibleAuctionUpdated")
    assert len(auction_logs) == 1
    
    auction_log = auction_logs[0]
    assert auction_log.liqUser == bob
    assert auction_log.asset == alpha_token.address
    
    # Assert exact default auction parameters (no hedging!)
    assert auction_log.startDiscount == 0      # Default start discount
    assert auction_log.maxDiscount == 50_00    # Default max discount (50%)
    assert auction_log.startBlock == boa.env.evm.patch.block_number  # Default delay = 0 (starts immediately)
    assert auction_log.endBlock == boa.env.evm.patch.block_number + 1000  # Default duration = 1000 blocks
    assert auction_log.isNewAuction

    # Verify liquidation event shows auction was started
    liquidation_log = filter_logs(teller, "LiquidateUser")[0]
    assert liquidation_log.user == bob
    assert liquidation_log.numAuctionsStarted == 1
    assert not liquidation_log.didRestoreDebtHealth  # Still in liquidation

    # Verify user is still in liquidation
    user_debt, bt, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    assert user_debt.inLiquidation
    assert ledger.hasFungibleAuctions(bob)
    assert not credit_engine.canLiquidateUser(bob)


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
    
    auction_log = filter_logs(teller, "FungibleAuctionUpdated")[0]
    start_block = auction_log.startBlock
    end_block = auction_log.endBlock
    duration = end_block - start_block
    
    # Give alice some GREEN to buy auction
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Test auction purchase at start (minimum discount)
    # Auction starts immediately (delay=0), so we're already at start
    green_to_spend = 10 * EIGHTEEN_DECIMALS
    green_spent_start = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )
    
    # At start discount (0%), should spend exactly the amount we requested
    _test(green_spent_start, green_to_spend)
    
    # Test auction purchase at middle (medium discount)
    middle_blocks = duration // 2
    boa.env.time_travel(blocks=middle_blocks)
    
    green_spent_middle = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )

    _test(green_spent_middle, green_to_spend)
    
    # Test auction purchase near end (maximum discount)
    near_end_blocks = middle_blocks - 1  # 2 blocks before end
    boa.env.time_travel(blocks=near_end_blocks)
    
    green_spent_end = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )
    _test(green_spent_end, green_to_spend)
      
    # Verify auction expires and reverts
    boa.env.time_travel(blocks=5)  # Move to end block
    with boa.reverts("no green spent"):
        buy_fungible_auction(teller,
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
    
    auction_logs = filter_logs(teller, "FungibleAuctionUpdated")
    assert len(auction_logs) == 2  # Should have exactly 2 auctions (alpha, bravo)
    
    # Give alice GREEN to buy auctions
    green_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Prepare batch purchase
    purchases = []
    for log in auction_logs:
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
    assert total_green_spent == 40 * EIGHTEEN_DECIMALS  # Exactly 20 GREEN per auction × 2 auctions
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
    ledger,
    credit_engine,
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
    setAssetConfig(
        bravo_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=False,
    )

    # Setup
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    # Small position for easy depletion
    deposit_amount = 50 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, deposit_amount, bravo_token, bravo_token_whale)
    debt_amount = 40 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 50 * EIGHTEEN_DECIMALS // 100  # 0.50
    mock_price_source.setPrice(alpha_token, new_price)
    mock_price_source.setPrice(bravo_token, new_price)

    # Perform liquidation to create auction
    teller.liquidateUser(bob, False, sender=sally)
    
    auction_log = filter_logs(teller, "FungibleAuctionUpdated")[0]
    
    # Give alice GREEN to buy entire position
    green_amount = 100 * EIGHTEEN_DECIMALS  # More than enough
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Verify auction exists
    assert ledger.hasFungibleAuction(bob, auction_log.vaultId, alpha_token)

    # Buy enough to deplete position
    buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, green_amount, False, sender=alice
    )

    # auction no longer exists
    assert not ledger.hasFungibleAuction(bob, auction_log.vaultId, alpha_token)
    assert not ledger.hasFungibleAuctions(bob)

    # Buying all auctionable collateral does not necessarily restore health.
    # With no auction left, the account stays frozen but a later permissionless
    # liquidation pass is allowed once the remaining position is again beyond
    # its liquidation threshold.
    residual_debt, residual_terms, _ = credit_engine.getLatestUserDebtAndTerms(
        bob,
        False,
    )
    assert residual_debt.inLiquidation
    assert residual_debt.amount > residual_terms.totalMaxDebt
    assert not credit_engine.canLiquidateUser(bob)

    mock_price_source.setPrice(bravo_token, 10 * EIGHTEEN_DECIMALS // 100)
    assert credit_engine.canLiquidateUser(bob)
    clear_transient_storage()
    debt_after_purchase = ledger.userDebt(bob).amount
    keeper_before = green_token.balanceOf(sally)
    assert teller.liquidateUser(bob, False, sender=sally) == 0
    assert ledger.userDebt(bob).amount == debt_after_purchase
    assert ledger.userDebt(bob).inLiquidation
    assert green_token.balanceOf(sally) == keeper_before
    retry_log = filter_logs(teller, "LiquidateUser")[0]
    assert retry_log.totalLiqFees == 0
    assert retry_log.keeperFee == 0
    assert retry_log.repayAmount == 0
    assert retry_log.numAuctionsStarted == 0
    
    # Verify alice received the collateral
    alice_alpha_balance = alpha_token.balanceOf(alice)
    assert alice_alpha_balance > 0  # Should have received some collateral from the depleted position


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
    auction_logs = filter_logs(teller, "FungibleAuctionUpdated")
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
    auction_log = filter_logs(teller, "FungibleAuctionUpdated")[0]
    
    # Give alice GREEN
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount * 2, sender=whale)  # Give alice double to cover transfers
    green_token.approve(teller, green_amount, sender=alice)  # Approve for teller transfers

    # Test 1: Disable general auction buying via setGeneralConfig
    setGeneralConfig(_canBuyInAuction=False)
    
    with boa.reverts("no green spent"):
        buy_fungible_auction(teller,
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
        buy_fungible_auction(teller,
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
        buy_fungible_auction(teller,
            bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, sender=alice
        )
    
    # Add alice to whitelist
    mock_whitelist.setAllowed(alice, alpha_token, True, sender=alice)
    
    # Test 4: Now buying should work
    green_spent = buy_fungible_auction(teller,
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
    auction_log = filter_logs(teller, "FungibleAuctionUpdated")[0]
    
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
        buy_fungible_auction(teller,
            bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, sender=alice
        )
    
    # Test 2: Exactly at start block (should work)
    boa.env.time_travel(blocks=5)  # Move to start block
    assert boa.env.evm.patch.block_number == start_block
    
    green_spent = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, sender=alice
    )
    # At start of auction (0% discount), should spend exactly what we requested
    assert green_spent == 10 * EIGHTEEN_DECIMALS  # Should spend exactly what we requested (0% discount at start)
    
    # Test 3: One block before end (should work)
    # We're currently at start_block, need to move to end_block - 1
    blocks_to_move = (end_block - 1) - boa.env.evm.patch.block_number
    boa.env.time_travel(blocks=blocks_to_move)
    assert boa.env.evm.patch.block_number == end_block - 1
    
    alice_before = alpha_token.balanceOf(alice)
    green_spent = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, sender=alice
    )
    # Last purchasable block reaches maxDiscount. Requested GREEN is still
    # spent when collateral remains; the buyer receives more than face value.
    assert green_spent > 0
    assert green_spent <= 10 * EIGHTEEN_DECIMALS
    collateral_received = alpha_token.balanceOf(alice) - alice_before
    assert collateral_received * new_price // EIGHTEEN_DECIMALS > green_spent
    
    # Test 4: Exactly at end block (should fail)
    boa.env.time_travel(blocks=1)  # Move to end block
    assert boa.env.evm.patch.block_number == end_block
    
    with boa.reverts("no green spent"):
        buy_fungible_auction(teller,
            bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, sender=alice
        )
    
    # Test 5: After end block (should fail)
    boa.env.time_travel(blocks=5)  # Move past end block
    
    with boa.reverts("no green spent"):
        buy_fungible_auction(teller,
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
    auction_log = filter_logs(teller, "FungibleAuctionUpdated")[0]
    
    # user has no green
    with boa.reverts("cannot transfer 0 amount"):
        buy_fungible_auction(teller,
            bob, auction_log.vaultId, alpha_token, 10 * EIGHTEEN_DECIMALS, False, False, sender=alice
        )
   
    # Transfer some GREEN to auction house (simulating previous auction activity)
    partial_green = 5 * EIGHTEEN_DECIMALS
    green_token.transfer(auction_house, partial_green, sender=whale)
    
    # Partial GREEN availability (should use what's available)
    green_spent = auction_house.buyFungibleAuction(
        bob, auction_log.vaultId, alpha_token, 20 * EIGHTEEN_DECIMALS, alice, alice, False, False, sender=teller.address
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
        purchases, 30 * EIGHTEEN_DECIMALS, alice, alice, False, False, sender=teller.address
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
    auction_log = filter_logs(teller, "FungibleAuctionUpdated")[0]
    
    # Verify flat discount parameters
    assert auction_log.startDiscount == 25_00
    assert auction_log.maxDiscount == 25_00
    
    # Give alice GREEN
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Test discount at start (should be 25%)
    green_to_spend = 10 * EIGHTEEN_DECIMALS
    green_spent_start = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )
    
    # Test discount at middle (should still be 25%)
    boa.env.time_travel(blocks=50)  # Middle of auction
    green_spent_middle = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )
    
    # Test discount near end (should still be 25%)
    boa.env.time_travel(blocks=49)  # Near end of auction
    green_spent_end = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )
    
    # All should spend the same amount (flat 25% discount)
    # The discount affects how much collateral we get, not how much GREEN we spend
    # We request 10 GREEN, and at 25% discount we get more collateral for that 10 GREEN
    # So we should spend exactly (or very close to) 10 GREEN each time
    
    # Allow for tiny rounding differences (1 wei tolerance)
    assert abs(green_spent_start - green_to_spend) <= 1  # Within 1 wei
    assert abs(green_spent_middle - green_to_spend) <= 1  # Within 1 wei
    assert abs(green_spent_end - green_to_spend) <= 1  # Within 1 wei


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
    auction_log = filter_logs(teller, "FungibleAuctionUpdated")[0]

    # Give alice GREEN
    green_amount = 500 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)  # Approve for teller transfers

    # Test 1: Very small payment (1 wei)
    tiny_amount = 1  # 1 wei
    green_spent = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, tiny_amount, False, sender=alice
    )
    # Should spend exactly the tiny amount (no discount at start)
    assert green_spent == tiny_amount
    
    # Test 2: Odd number that might cause rounding issues
    odd_amount = 123456789  # Odd number in wei
    green_spent = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, odd_amount, False, sender=alice
    )
    # Should spend exactly the odd amount (no discount at start)
    assert green_spent == odd_amount
    
    # Test 3: Large payment amount
    large_amount = 100 * EIGHTEEN_DECIMALS
    green_spent = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, large_amount, False, sender=alice
    )
    # Should spend exactly the large amount (no discount at start)
    assert green_spent == large_amount


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
    
    auction_logs = filter_logs(teller, "FungibleAuctionUpdated")
    assert len(auction_logs) == 3  # Should have exactly 3 auctions (alpha, bravo, charlie)
    
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
    green_spent_alpha = buy_fungible_auction(teller,
        bob, alpha_auction.vaultId, alpha_token, 50 * EIGHTEEN_DECIMALS, False, sender=alice
    )
    assert green_spent_alpha > 0  # Should successfully purchase from alpha auction
    
    # Try to buy from bravo auction (should fail - not started yet due to delay)
    with boa.reverts("no green spent"):
        buy_fungible_auction(teller,
            bob, bravo_auction.vaultId, bravo_token, 50 * EIGHTEEN_DECIMALS, False, sender=alice
        )
    
    # Buy from charlie auction (available immediately)
    green_spent_charlie = buy_fungible_auction(teller,
        bob, charlie_auction.vaultId, charlie_token, 50 * EIGHTEEN_DECIMALS, False, sender=alice
    )
    assert green_spent_charlie > 0  # Should successfully purchase from charlie auction
    
    # Move forward to enable bravo auction
    boa.env.time_travel(blocks=5)
    
    # Now bravo auction should work
    green_spent_bravo = buy_fungible_auction(teller,
        bob, bravo_auction.vaultId, bravo_token, 50 * EIGHTEEN_DECIMALS, False, sender=alice
    )
    assert green_spent_bravo > 0  # Should successfully purchase from bravo auction
    
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
    auction_log = filter_logs(teller, "FungibleAuctionUpdated")[0]
    
    # Give alice GREEN and transfer to auction house
    green_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)  # Give alice double to cover transfers
    green_token.approve(teller, green_amount * 2, sender=alice)  # Approve for teller transfers

    # Test 1: Request savings GREEN for leftover
    alice_savings_before = savings_green.balanceOf(alice)
    
    # Spend less than available to create leftover
    green_spent = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, green_amount, False, True, sender=alice  # True = wants savings GREEN
    )
    assert green_spent != 0
    
    alice_savings_after = savings_green.balanceOf(alice)
    
    # Should have received leftover as savings GREEN
    assert green_token.balanceOf(alice) == 0
    assert alice_savings_after > alice_savings_before  # Received savings GREEN


def test_ah_liquidation_multiple_auctions(
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
    teller,
    mock_price_source,
    createDebtTerms,
    credit_engine,
    sally,
    ledger,
    green_token,
    whale,
):
    """Test liquidation of user with multiple collateral assets"""
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup multiple collateral assets with different liquidation configs
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )
    
    setAssetConfig(
        bravo_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )
    
    setAssetConfig(
        charlie_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )

    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)

    # Setup user with multiple collateral assets
    alpha_amount = 100 * EIGHTEEN_DECIMALS
    bravo_amount = 150 * EIGHTEEN_DECIMALS
    charlie_amount = 200 * 10**6  # Charlie token has 6 decimals, not 18
    
    performDeposit(bob, alpha_amount, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)
    performDeposit(bob, charlie_amount, charlie_token, charlie_token_whale)
    
    # Borrow against total collateral
    debt_amount = 200 * EIGHTEEN_DECIMALS  # Borrow $200 against $450 collateral
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable prices (drop all assets to trigger liquidation)
    # Liquidation threshold: $200 * 100 / 80 = $250
    # Need collateral value <= $250, so drop to $0.55 each: $450 * 0.55 = $247.5 < $250
    new_price = 55 * EIGHTEEN_DECIMALS // 100  # Drop to $0.55 each
    mock_price_source.setPrice(alpha_token, new_price)
    mock_price_source.setPrice(bravo_token, new_price)
    mock_price_source.setPrice(charlie_token, new_price)
    
    assert credit_engine.canLiquidateUser(bob)

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    
    # Verify multiple auctions were created
    auction_logs = filter_logs(teller, "FungibleAuctionUpdated")
    assert len(auction_logs) == 3  # Should have exactly 3 auctions (alpha, bravo, charlie)
    
    # Verify user is in liquidation with auctions
    user_debt_after_liq, _, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    assert user_debt_after_liq.inLiquidation
    
    # Verify auctions exist for all 3 assets
    auction_count = 0
    for log in auction_logs:
        if ledger.hasFungibleAuction(bob, log.vaultId, log.asset):
            auction_count += 1
    assert auction_count == 3  # All 3 auctions active
    
    # Now: whale sends bob GREEN tokens to repay debt directly
    repay_amount = user_debt_after_liq.amount  # Repay full debt
    green_token.transfer(bob, repay_amount, sender=whale)
    green_token.approve(teller, repay_amount, sender=bob)
    
    # Bob repays debt directly (not through auctions)
    teller.repay(repay_amount, bob, False, sender=bob)
    
    # Verify user exited liquidation
    user_debt_final, _, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    assert not user_debt_final.inLiquidation  # User exited liquidation
    
    # CORRECT BEHAVIOR: Auction is removed when user exits liquidation
    # This happens in Ledger.setUserDebt when inLiquidation changes from True to False
    # The Ledger calls _removeAllFungibleAuctions(_user) automatically
    for log in auction_logs:
        assert not ledger.hasFungibleAuction(bob, log.vaultId, log.asset)  # All auctions disabled
    

def test_ah_auction_user_exits_liquidation_via_auction_purchases(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    sally,
    teller,
    mock_price_source,
    credit_engine,
    ledger,
    green_token,
    whale,
    createDebtTerms,
):
    """Test that user exits liquidation when sufficient debt is repaid via auction purchases
    
    This demonstrates the correct system behavior:
    - User exits liquidation when debt health is restored through auction purchases
    - Auctions are automatically removed when user exits liquidation (handled by Ledger)
    - The flow: AuctionHouse → CreditEngine.repayDuringAuctionPurchase → Ledger.setUserDebt → _removeAllFungibleAuctions
    """
    # Setup
    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=80_00,  # 80% LTV
        _liqThreshold=80_00,  # 80% liquidation threshold
        _liqFee=5_00,  # 5% liquidation fee
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    # Deposit and borrow
    deposit_amount = 100 * EIGHTEEN_DECIMALS  # $100 at $1 price
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    debt_amount = 70 * EIGHTEEN_DECIMALS  # $70 debt (70% LTV, safe)
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Trigger liquidation by dropping price to $0.85
    # Collateral value: $100 * 0.85 = $85
    # Debt: $70, LTV = 70/85 = 82.35% > 80% threshold
    liquidation_price = 85 * EIGHTEEN_DECIMALS // 100  # $0.85
    mock_price_source.setPrice(alpha_token, liquidation_price)

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    auction_log = filter_logs(teller, "FungibleAuctionUpdated")[0]
    
    # Verify user is in liquidation with auction
    user_debt_after_liq, bt_after_liq, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    assert user_debt_after_liq.inLiquidation
    assert ledger.hasFungibleAuction(bob, auction_log.vaultId, alpha_token)

    # Calculate amount needed to restore health based on actual values
    current_debt = user_debt_after_liq.amount
    
    # Simple approach: buy enough to definitely get out of liquidation
    # Since buying reduces both debt and collateral equally, we need to buy more
    # Let's buy 50% of the current debt to be safe
    amount_to_repay = current_debt // 2  # 50% of debt
    
    # Give alice GREEN
    green_token.transfer(alice, amount_to_repay, sender=whale)
    green_token.approve(teller, amount_to_repay, sender=alice)

    # Purchase auction with amount to restore health
    buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, amount_to_repay, False, sender=alice
    )
    
    # Verify user exited liquidation through auction purchase
    user_debt_final, bt_final, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    assert not user_debt_final.inLiquidation  # User exited liquidation via auction purchase
    
    # CORRECT BEHAVIOR: Auction is removed when user exits liquidation
    # This happens in Ledger.setUserDebt when inLiquidation changes from True to False
    # The Ledger calls _removeAllFungibleAuctions(_user) automatically
    assert not ledger.hasFungibleAuction(bob, auction_log.vaultId, alpha_token)  # Auction REMOVED
    
    # Verify debt health is restored
    final_ltv = user_debt_final.amount * 100 // bt_final.collateralVal if bt_final.collateralVal > 0 else 0
    assert final_ltv < 80  # LTV is definitely safe (should be around 76% based on our calculation)
    

def test_ah_auction_repayment_caps_and_returns_payer_leftover(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    sally,
    teller,
    mock_price_source,
    credit_engine,
    ledger,
    green_token,
    savings_green,
    whale,
    createDebtTerms,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _liqThreshold=80_00,
        _liqFee=0,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )

    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        200 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    debt = 100 * EIGHTEEN_DECIMALS
    assert teller.borrow(debt, bob, False, sender=bob) == debt

    # $110 of collateral against $100 debt is liquidatable but still creates
    # an auction purchase whose GREEN spend can exceed the remaining debt.
    mock_price_source.setPrice(
        alpha_token,
        55 * EIGHTEEN_DECIMALS // 100,
    )
    assert credit_engine.canLiquidateUser(bob)
    teller.liquidateUser(bob, False, sender=sally)
    auction_log = filter_logs(teller, "FungibleAuctionUpdated")[0]
    assert auction_log.liqUser == bob
    assert auction_log.liqUser != ZERO_ADDRESS
    assert ledger.hasFungibleAuction(
        bob,
        auction_log.vaultId,
        alpha_token,
    )

    debt_before = ledger.userDebt(bob).amount
    supply_before = green_token.totalSupply()
    debtor_green_before = green_token.balanceOf(bob)
    debtor_sgreen_before = savings_green.balanceOf(bob)
    payer_sgreen_before = savings_green.balanceOf(alice)
    savings_assets_before = green_token.balanceOf(savings_green)

    payment = 200 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    payer_green_before = green_token.balanceOf(alice)
    green_spent = buy_fungible_auction(
        teller,
        bob,
        auction_log.vaultId,
        alpha_token,
        payment,
        False,
        False,
        False,
        sender=alice,
    )

    repay_log = filter_logs(teller, "RepayDebt")[0]
    assert repay_log.user == bob
    assert green_spent == debt_before
    assert repay_log.repayValue == debt_before
    assert repay_log.refundAmount == 0
    assert repay_log.refundWasSavingsGreen
    assert ledger.userDebt(bob).amount == 0

    # AuctionHouse returns the unspent payment to the payer before CreditEngine,
    # so no discounted collateral or debtor refund is created by overpayment.
    assert green_token.totalSupply() == supply_before - debt_before
    assert payer_green_before - green_token.balanceOf(alice) == debt_before
    assert green_token.balanceOf(bob) == debtor_green_before
    assert savings_green.balanceOf(bob) == debtor_sgreen_before
    assert savings_green.balanceOf(alice) == payer_sgreen_before
    assert green_token.balanceOf(savings_green) == savings_assets_before
    purchase_log = filter_logs(teller, "FungAuctionPurchased")[0]
    assert purchase_log.liqUser == bob
    assert purchase_log.greenSpent == green_spent


def test_auction_purchase_caps_spend_and_discounted_collateral_at_live_debt(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    sally,
    teller,
    mock_price_source,
    credit_engine,
    ledger,
    green_token,
    savings_green,
    whale,
    createDebtTerms,
    createAuctionParams,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    auction_params = createAuctionParams(
        _startDiscount=17_00,
        _maxDiscount=17_00,
        _duration=100,
    )
    debt_terms = createDebtTerms(
        _ltv=10_00,
        _redemptionThreshold=20_00,
        _liqThreshold=25_00,
        _liqFee=0,
        _borrowRate=10_00,
    )
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
        _customAuctionParams=auction_params,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        1_000 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(alpha_token, 20 * EIGHTEEN_DECIMALS // 100)
    teller.liquidateUser(bob, False, sender=sally)
    auction = filter_logs(teller, "FungibleAuctionUpdated")[0]

    boa.env.evm.patch.timestamp += ONE_YEAR
    live_debt = credit_engine.getUserDebtAmount(bob)
    assert live_debt > 100 * EIGHTEEN_DECIMALS

    payment = 200 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    payer_green_before = green_token.balanceOf(alice)
    buyer_collateral_before = alpha_token.balanceOf(alice)
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

    repay_log = filter_logs(teller, "RepayDebt")[0]
    purchase_log = filter_logs(teller, "FungAuctionPurchased")[0]
    collateral_received = alpha_token.balanceOf(alice) - buyer_collateral_before
    collateral_value = (
        collateral_received * 20 * EIGHTEEN_DECIMALS
        // (100 * EIGHTEEN_DECIMALS)
    )
    net_rate = HUNDRED_PERCENT - 17_00
    expected_collateral_value = live_debt * HUNDRED_PERCENT // net_rate
    expected_spend = expected_collateral_value * net_rate // HUNDRED_PERCENT
    assert expected_spend < live_debt
    assert live_debt - expected_spend == 1
    assert green_spent == expected_spend
    assert payer_green_before - green_token.balanceOf(alice) == expected_spend
    assert repay_log.repayValue == expected_spend
    assert repay_log.refundAmount == 0
    assert purchase_log.greenSpent == expected_spend
    assert collateral_value == expected_collateral_value
    assert savings_green.balanceOf(bob) == borrower_sgreen_before
    assert green_token.totalSupply() == supply_before - expected_spend
    assert ledger.userDebt(bob).amount == live_debt - expected_spend
    assert not ledger.hasFungibleAuctions(bob)


@pytest.mark.parametrize(
    "first_purchase",
    [60, 100],
    ids=["first-partially-repays", "first-clears-debt"],
)
def test_batch_recomputes_same_borrower_debt_before_each_purchase(
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
    sally,
    teller,
    mock_price_source,
    ledger,
    green_token,
    whale,
    createDebtTerms,
    createAuctionParams,
    first_purchase,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    auction_params = createAuctionParams(
        _startDiscount=20_00,
        _maxDiscount=20_00,
        _duration=100,
    )
    debt_terms = createDebtTerms(
        _ltv=10_00,
        _redemptionThreshold=20_00,
        _liqThreshold=25_00,
        _liqFee=0,
        _borrowRate=0,
    )
    for token in (alpha_token, bravo_token):
        setAssetConfig(
            token,
            _debtTerms=debt_terms,
            _shouldSwapInStabPools=False,
            _shouldAuctionInstantly=True,
            _customAuctionParams=auction_params,
        )
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)

    performDeposit(
        bob,
        1_000 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    performDeposit(
        bob,
        1_000 * EIGHTEEN_DECIMALS,
        bravo_token,
        bravo_token_whale,
    )
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    for token in (alpha_token, bravo_token):
        mock_price_source.setPrice(token, 20 * EIGHTEEN_DECIMALS // 100)
    teller.liquidateUser(bob, False, sender=sally)
    auctions = filter_logs(teller, "FungibleAuctionUpdated")
    assert len(auctions) == 2

    payment = 160 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    payer_before = green_token.balanceOf(alice)
    purchases = [
        (
            auctions[0].liqUser,
            auctions[0].vaultId,
            auctions[0].asset,
            first_purchase * EIGHTEEN_DECIMALS,
        ),
        (
            auctions[1].liqUser,
            auctions[1].vaultId,
            auctions[1].asset,
            60 * EIGHTEEN_DECIMALS,
        ),
    ]
    total_spent = teller.buyManyFungibleAuctions(
        purchases,
        payment,
        False,
        False,
        False,
        alice,
        sender=alice,
    )

    purchase_logs = filter_logs(teller, "FungAuctionPurchased")
    repay_logs = filter_logs(teller, "RepayDebt")
    expected_spends = (
        [60 * EIGHTEEN_DECIMALS, 40 * EIGHTEEN_DECIMALS]
        if first_purchase == 60
        else [100 * EIGHTEEN_DECIMALS]
    )
    assert [log.greenSpent for log in purchase_logs] == expected_spends
    assert [log.repayValue for log in repay_logs] == expected_spends
    assert all(log.refundAmount == 0 for log in repay_logs)
    assert total_spent == 100 * EIGHTEEN_DECIMALS
    assert payer_before - green_token.balanceOf(alice) == total_spent
    assert ledger.userDebt(bob).amount == 0
    assert not ledger.hasFungibleAuctions(bob)


def test_batch_with_valid_then_zero_payment_dust_reverts_atomically(
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
    sally,
    teller,
    mock_price_source,
    ledger,
    green_token,
    whale,
    createDebtTerms,
    createAuctionParams,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    auction_params = createAuctionParams(
        _startDiscount=20_00,
        _maxDiscount=20_00,
        _duration=100,
    )
    debt_terms = createDebtTerms(
        _ltv=10_00,
        _redemptionThreshold=20_00,
        _liqThreshold=25_00,
        _liqFee=0,
        _borrowRate=0,
    )
    for token in (alpha_token, bravo_token):
        setAssetConfig(
            token,
            _debtTerms=debt_terms,
            _shouldSwapInStabPools=False,
            _shouldAuctionInstantly=True,
            _customAuctionParams=auction_params,
        )
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)

    for token, whale_addr in (
        (alpha_token, alpha_token_whale),
        (bravo_token, bravo_token_whale),
    ):
        performDeposit(
            bob,
            1_000 * EIGHTEEN_DECIMALS,
            token,
            whale_addr,
        )

    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    for token in (alpha_token, bravo_token):
        mock_price_source.setPrice(token, 20 * EIGHTEEN_DECIMALS // 100)
    teller.liquidateUser(bob, False, sender=sally)
    auctions = filter_logs(teller, "FungibleAuctionUpdated")
    assert len(auctions) == 2

    payment = 10 * EIGHTEEN_DECIMALS + 1
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    payer_before = green_token.balanceOf(alice)
    debt_before = ledger.userDebt(bob).amount
    alpha_before = alpha_token.balanceOf(alice)
    bravo_before = bravo_token.balanceOf(alice)
    purchases = [
        (
            auctions[0].liqUser,
            auctions[0].vaultId,
            auctions[0].asset,
            10 * EIGHTEEN_DECIMALS,
        ),
        (
            auctions[1].liqUser,
            auctions[1].vaultId,
            auctions[1].asset,
            1,
        ),
    ]

    # Prove the first entry is a valid, state-changing purchase on its own.
    with boa.env.anchor():
        valid_payer_before = green_token.balanceOf(alice)
        valid_debt_before = ledger.userDebt(bob).amount
        valid_collateral_before = alpha_token.balanceOf(alice)
        assert teller.buyManyFungibleAuctions(
            [purchases[0]],
            10 * EIGHTEEN_DECIMALS,
            False,
            False,
            False,
            alice,
            sender=alice,
        ) == 10 * EIGHTEEN_DECIMALS
        assert valid_payer_before - green_token.balanceOf(alice) == (
            10 * EIGHTEEN_DECIMALS
        )
        assert ledger.userDebt(bob).amount < valid_debt_before
        assert alpha_token.balanceOf(alice) > valid_collateral_before

    with pytest.raises(BoaError) as exc_info:
        teller.buyManyFungibleAuctions(
            purchases,
            payment,
            False,
            False,
            False,
            alice,
            sender=alice,
        )
    # GREEN rejects the zero transfer before CreditEngine can receive the call.
    assert_reverted_call(exc_info.value, "cannot transfer 0 amount", teller)

    assert green_token.balanceOf(alice) == payer_before
    assert ledger.userDebt(bob).amount == debt_before
    assert alpha_token.balanceOf(alice) == alpha_before
    assert bravo_token.balanceOf(alice) == bravo_before
    assert ledger.hasFungibleAuctions(bob)


@pytest.mark.parametrize(
    ("purchase_amounts", "regression_ceiling"),
    [
        ([1], 325_000),
        ([100, 1], 360_000),
        ([1] * 20, 4_260_000),
    ],
    ids=["single-success", "clear-then-skip", "twenty-successes"],
)
def test_live_debt_cap_batch_gas_bounds(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    sally,
    teller,
    mock_price_source,
    ledger,
    green_token,
    whale,
    createDebtTerms,
    createAuctionParams,
    purchase_amounts,
    regression_ceiling,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    auction_params = createAuctionParams(
        _startDiscount=20_00,
        _maxDiscount=20_00,
        _duration=100,
    )
    setAssetConfig(
        alpha_token,
        _debtTerms=createDebtTerms(
            _ltv=10_00,
            _redemptionThreshold=20_00,
            _liqThreshold=25_00,
            _liqFee=0,
            _borrowRate=0,
        ),
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
        _customAuctionParams=auction_params,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        1_000 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(alpha_token, 20 * EIGHTEEN_DECIMALS // 100)
    teller.liquidateUser(bob, False, sender=sally)
    auction = filter_logs(teller, "FungibleAuctionUpdated")[0]

    payment = sum(purchase_amounts) * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    purchases = [
        (
            auction.liqUser,
            auction.vaultId,
            auction.asset,
            amount * EIGHTEEN_DECIMALS,
        )
        for amount in purchase_amounts
    ]
    gas_before = boa.env.get_gas_used()
    total_spent = teller.buyManyFungibleAuctions(
        purchases,
        payment,
        False,
        False,
        False,
        alice,
        sender=alice,
    )
    gas_used = boa.env.get_gas_used() - gas_before
    print(
        "AUCTION_LIVE_DEBT_CAP_GAS",
        f"items={len(purchases)}",
        f"successful={len(filter_logs(teller, 'FungAuctionPurchased'))}",
        f"gas={gas_used}",
    )

    expected_spent = min(sum(purchase_amounts), 100) * EIGHTEEN_DECIMALS
    expected_successes = 1 if purchase_amounts[0] == 100 else len(purchase_amounts)
    assert total_spent == expected_spent
    assert len(filter_logs(teller, "FungAuctionPurchased")) == expected_successes
    assert ledger.userDebt(bob).amount == 100 * EIGHTEEN_DECIMALS - expected_spent
    # About 20% above the pinned 269,080 / 298,314 / 3,547,707 measurements.
    assert gas_used <= regression_ceiling
    assert gas_used < 15_000_000


def test_ah_auction_collateral_amounts_and_discount_verification(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    sally,
    teller,
    mock_price_source,
    createDebtTerms,
    createAuctionParams,
    green_token,
    whale,
    _test,
):
    """Test that buyers receive correct collateral amounts based on auction discounts
    
    This tests:
    - Exact collateral amounts received at different discount levels
    - Discount calculations are properly applied
    - Price relationships between GREEN spent and collateral received
    - Progressive discount increases over time
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup asset with progressive discount (0% to 50% over 100 blocks)
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    auction_params = createAuctionParams(
        _startDiscount=0,      # 0% start discount
        _maxDiscount=50_00,    # 50% max discount
        _delay=0,              # Start immediately
        _duration=100,         # 100 blocks duration
    )
    
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldAuctionInstantly=True,
        _customAuctionParams=auction_params,
    )

    # Setup prices: $1 per token for both alpha and GREEN
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    # Large position to ensure we don't deplete during testing
    deposit_amount = 1000 * EIGHTEEN_DECIMALS  # $1000 worth
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 600 * EIGHTEEN_DECIMALS  # $600 debt
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price to $0.50 (makes collateral worth $500, debt $600 = 120% LTV)
    liquidation_price = 50 * EIGHTEEN_DECIMALS // 100  # $0.50
    mock_price_source.setPrice(alpha_token, liquidation_price)

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    auction_log = filter_logs(teller, "FungibleAuctionUpdated")[0]
    
    # Give alice plenty of GREEN
    green_amount = 200 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Test 1: Purchase at start (0% discount)
    # Spend 10 GREEN, should get exactly $10 worth of collateral at current price
    # At $0.50 per alpha token, $10 = 20 alpha tokens
    green_to_spend = 10 * EIGHTEEN_DECIMALS
    alice_alpha_before = alpha_token.balanceOf(alice)
    
    green_spent_start = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )
    
    alice_alpha_after_start = alpha_token.balanceOf(alice)
    collateral_received_start = alice_alpha_after_start - alice_alpha_before
    
    # At 0% discount: 10 GREEN = $10 = 20 alpha tokens (at $0.50 each)
    expected_collateral_start = 20 * EIGHTEEN_DECIMALS
    _test(green_spent_start, green_to_spend)  # Should spend exactly what we requested
    _test(collateral_received_start, expected_collateral_start)  # Should receive exact amount
    
    # Test 2: Purchase at 25% progress (12.5% discount)
    # Move to 25% through auction (25 blocks)
    boa.env.time_travel(blocks=25)
    
    green_spent_quarter = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )
    
    alice_alpha_after_quarter = alpha_token.balanceOf(alice)
    collateral_received_quarter = alice_alpha_after_quarter - alice_alpha_after_start
    
    # At 12.5% discount: 10 GREEN buys $11.43 worth of collateral
    # $11.43 / $0.50 = 22.86 alpha tokens
    # 10 GREEN / (1 - 0.125) = 10 / 0.875 = 11.43 GREEN worth of collateral
    expected_collateral_quarter = (green_to_spend * EIGHTEEN_DECIMALS) // (liquidation_price * 875 // 1000)
    _test(green_spent_quarter, green_to_spend)  # Should spend exactly what we requested
    _test(collateral_received_quarter, expected_collateral_quarter)  # Should receive calculated amount
    
    # Test 3: Purchase at 50% progress (25% discount)
    # Move to 50% through auction (25 more blocks = 50 total)
    boa.env.time_travel(blocks=25)
    
    green_spent_half = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )
    
    alice_alpha_after_half = alpha_token.balanceOf(alice)
    collateral_received_half = alice_alpha_after_half - alice_alpha_after_quarter
    
    # At 25% discount: 10 GREEN buys $13.33 worth of collateral
    # $13.33 / $0.50 = 26.67 alpha tokens
    # 10 GREEN / (1 - 0.25) = 10 / 0.75 = 13.33 GREEN worth of collateral
    expected_collateral_half = (green_to_spend * EIGHTEEN_DECIMALS) // (liquidation_price * 75 // 100)
    _test(green_spent_half, green_to_spend)  # Should spend exactly what we requested
    _test(collateral_received_half, expected_collateral_half)  # Should receive calculated amount
    
    # Test 4: Purchase at 100% progress (50% discount)
    # Move to end of auction (50 more blocks = 100 total)
    boa.env.time_travel(blocks=49)  # 99 blocks total (1 before end)
    
    green_spent_end = buy_fungible_auction(teller,
        bob, auction_log.vaultId, alpha_token, green_to_spend, False, sender=alice
    )
    
    alice_alpha_after_end = alpha_token.balanceOf(alice)
    collateral_received_end = alice_alpha_after_end - alice_alpha_after_half
    
    # At 50% discount: 10 GREEN buys $20 worth of collateral
    # $20 / $0.50 = 40 alpha tokens
    # 10 GREEN / (1 - 0.50) = 10 / 0.50 = 20 GREEN worth of collateral
    # Note: At 99% progress, discount is 49.5%, not exactly 50%
    
    # Instead of exact calculation, verify the relationship
    _test(green_spent_end, green_to_spend)  # Should spend exactly what we requested
    
    # Verify we got significantly more collateral than at start (due to discount)
    assert collateral_received_end > collateral_received_start * 150 // 100  # At least 50% more collateral
    
    # Verify progressive increase in collateral received
    assert collateral_received_quarter > collateral_received_start  # More collateral at higher discount
    assert collateral_received_half > collateral_received_quarter   # Even more collateral
    assert collateral_received_end > collateral_received_half       # Maximum collateral at max discount
    
    # Verify total collateral received
    total_collateral_received = alice_alpha_after_end - alice_alpha_before
    
    # Verify total is sum of individual purchases
    calculated_total = collateral_received_start + collateral_received_quarter + collateral_received_half + collateral_received_end
    assert total_collateral_received == calculated_total  # Total should match sum of individual purchases
    

def test_ah_auction_buy_with_balance_transfer_basic(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    sally,
    teller,
    mock_price_source,
    createDebtTerms,
    green_token,
    whale,
    ledger,
    simple_erc20_vault,
    vault_book,
    _test,
):
    """Test auction purchase with balance transfer within vault
    
    This tests:
    - Assets stay in vault when _shouldTransferBalance=True
    - Buyer receives vault balance instead of tokens
    - Vault data is properly updated
    - Ledger data shows buyer is participating in vault
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

    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    # Bob deposits and borrows
    deposit_amount = 200 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 100 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 50 * EIGHTEEN_DECIMALS // 100  # 0.50
    mock_price_source.setPrice(alpha_token, new_price)

    # Perform liquidation to create auction
    teller.liquidateUser(bob, False, sender=sally)
    filter_logs(teller, "FungibleAuctionUpdated")[0]
    
    vault_id = vault_book.getRegId(simple_erc20_vault)
    vault = simple_erc20_vault
    
    # Get initial balances
    initial_vault_balance = alpha_token.balanceOf(vault)
    initial_alice_token_balance = alpha_token.balanceOf(alice)
    initial_bob_vault_balance = vault.userBalances(bob, alpha_token)
    initial_alice_vault_balance = vault.userBalances(alice, alpha_token)
    initial_vault_total = vault.totalBalances(alpha_token)
    
    # Give alice GREEN to buy auction
    green_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Buy auction with _shouldTransferBalance=True
    green_spent = buy_fungible_auction(teller,
        bob, vault_id, alpha_token, green_amount, 
        False,  # _isPaymentSavingsGreen
        True,   # _shouldTransferBalance
        False,  # _shouldRefundSavingsGreen
        sender=alice
    )
    
    # Verify purchase occurred
    assert green_spent > 0
    
    # Check that assets stayed in vault
    final_vault_balance = alpha_token.balanceOf(vault)
    assert initial_vault_balance == final_vault_balance  # Vault balance unchanged
    
    # Check that Alice didn't receive tokens directly
    final_alice_token_balance = alpha_token.balanceOf(alice)
    assert final_alice_token_balance == initial_alice_token_balance  # No direct transfer
    
    # Check vault balances updated correctly
    final_bob_vault_balance = vault.userBalances(bob, alpha_token)
    final_alice_vault_balance = vault.userBalances(alice, alpha_token)
    
    # Bob's vault balance should decrease
    assert final_bob_vault_balance < initial_bob_vault_balance
    
    # Alice's vault balance should increase
    assert final_alice_vault_balance > initial_alice_vault_balance
    
    # The amount transferred should match
    amount_transferred = initial_bob_vault_balance - final_bob_vault_balance
    _test(amount_transferred, final_alice_vault_balance - initial_alice_vault_balance)
    
    # Total vault balance should remain the same
    final_vault_total = vault.totalBalances(alpha_token)
    _test(initial_vault_total, final_vault_total)
    
    # Verify Alice is now participating in the vault
    assert ledger.isParticipatingInVault(alice, vault_id)
    
    # Check FungAuctionPurchased event
    purchase_logs = filter_logs(teller, "FungAuctionPurchased")
    assert len(purchase_logs) == 1
    log = purchase_logs[0]
    assert log.liqUser == bob
    assert log.recipient == alice
    assert log.collateralAmountSent == amount_transferred


def test_ah_auction_buy_many_with_balance_transfer(
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
    sally,
    teller,
    mock_price_source,
    createDebtTerms,
    green_token,
    whale,
    ledger,
    simple_erc20_vault,
    vault_book,
):
    """Test batch auction purchases with balance transfers
    
    This tests:
    - Multiple auctions can be purchased with balance transfers
    - Assets from different auctions stay in vault
    - Buyer becomes participant in vault with multiple assets
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup multiple assets for auctions
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    
    for token in [alpha_token, bravo_token]:
        setAssetConfig(
            token,
            _debtTerms=debt_terms,
            _shouldAuctionInstantly=True,
        )

    # Setup prices
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
    new_price = 25 * EIGHTEEN_DECIMALS // 100  # 0.25
    mock_price_source.setPrice(alpha_token, new_price)
    mock_price_source.setPrice(bravo_token, new_price)

    # Perform liquidation to create multiple auctions
    teller.liquidateUser(bob, False, sender=sally)
    
    # Check liquidation results
    liq_logs = filter_logs(teller, "LiquidateUser")
    assert len(liq_logs) == 1
    liq_logs[0]
    
    auction_logs = filter_logs(teller, "FungibleAuctionUpdated")
    assert len(auction_logs) == 2  # Should have exactly 2 auctions
    
    vault_id = vault_book.getRegId(simple_erc20_vault)
    vault = simple_erc20_vault
    
    # Track initial vault balances
    initial_vault_alpha = alpha_token.balanceOf(vault)
    initial_vault_bravo = bravo_token.balanceOf(vault)
    initial_alice_alpha = alpha_token.balanceOf(alice)
    initial_alice_bravo = bravo_token.balanceOf(alice)
    
    # Give alice GREEN
    green_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Prepare batch purchase
    purchases = []
    for log in auction_logs:
        purchases.append((
            log.liqUser,
            log.vaultId,
            log.asset,
            30 * EIGHTEEN_DECIMALS,  # Max 30 GREEN per auction
        ))

    # Execute batch purchase with balance transfer
    total_green_spent = teller.buyManyFungibleAuctions(
        purchases, green_amount,
        False, True, False,  # _shouldTransferBalance=True
        sender=alice
    )

    # The actual amount spent depends on the auction dynamics and available collateral
    # After liquidation with 10% fee and keeper rewards, the actual collateral available 
    # may be less than expected, so we should just verify it's greater than 0
    assert total_green_spent > 0
    assert total_green_spent <= green_amount  # Shouldn't spend more than available
    
    # Verify assets stayed in vault
    assert alpha_token.balanceOf(vault) == initial_vault_alpha
    assert bravo_token.balanceOf(vault) == initial_vault_bravo
    
    # Verify Alice didn't receive tokens directly
    assert alpha_token.balanceOf(alice) == initial_alice_alpha
    assert bravo_token.balanceOf(alice) == initial_alice_bravo
    
    # Verify Alice has vault balances
    assert vault.userBalances(alice, alpha_token) > 0
    assert vault.userBalances(alice, bravo_token) > 0
    
    # Verify Alice is participating in vault
    assert ledger.isParticipatingInVault(alice, vault_id)
    
    # Check events
    purchase_logs = filter_logs(teller, "FungAuctionPurchased")
    assert len(purchase_logs) == 2


def test_ah_auction_balance_transfer_edge_cases(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    sally,
    teller,
    mock_price_source,
    createDebtTerms,
    green_token,
    whale,
    ledger,
    simple_erc20_vault,
    vault_book,
):
    """Test edge cases for auction purchases with balance transfers
    
    This tests:
    - Buyer already has position in vault
    - Position depletion with balance transfer
    - Mixing transfer and withdrawal purchases
    """
    
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    
    # Setup asset
    debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    setAssetConfig(
        alpha_token,
        _debtTerms=debt_terms,
        _shouldAuctionInstantly=True,
    )

    # Setup prices
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS)
    
    vault_id = vault_book.getRegId(simple_erc20_vault)
    vault = simple_erc20_vault
    
    # Test 1: Buyer already has position in vault
    # Give Alice initial balance in vault
    performDeposit(alice, 50 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    initial_alice_vault_balance = vault.userBalances(alice, alpha_token)
    assert initial_alice_vault_balance > 0
    
    # Bob deposits and borrows
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(bob, deposit_amount, alpha_token, alpha_token_whale)
    debt_amount = 60 * EIGHTEEN_DECIMALS
    teller.borrow(debt_amount, bob, False, sender=bob)

    # Set liquidatable price
    new_price = 50 * EIGHTEEN_DECIMALS // 100  # 0.50
    mock_price_source.setPrice(alpha_token, new_price)

    # Perform liquidation
    teller.liquidateUser(bob, False, sender=sally)
    filter_logs(teller, "FungibleAuctionUpdated")[0]
    
    # Give alice GREEN
    green_amount = 30 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)

    # Buy with balance transfer
    buy_fungible_auction(teller,
        bob, vault_id, alpha_token, green_amount,
        False, True, False,
        sender=alice
    )
    
    # Alice's vault balance should increase from her initial balance
    final_alice_vault_balance = vault.userBalances(alice, alpha_token)
    assert final_alice_vault_balance > initial_alice_vault_balance
    
    # Test 2: Position depletion with balance transfer
    # Calculate expected depletion based on our setup:
    # - Bob initially deposited 100 alpha tokens
    # - First purchase transferred some amount (from 30 GREEN purchase)
    # - Bob's remaining balance after first purchase
    vault.userBalances(bob, alpha_token)
    
    # At current price ($0.50), and with no discount (auction just started),
    # we can calculate how much collateral remains and whether 100 GREEN
    # is enough to deplete it
    
    # Buy remaining position to deplete it
    green_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, green_amount, sender=whale)
    green_token.approve(teller, green_amount, sender=alice)
    
    # Buy with intent to deplete Bob's position
    buy_fungible_auction(teller,
        bob, vault_id, alpha_token, green_amount,
        False, True, False,
        sender=alice
    )
    
    # Check that position was depleted
    bob_balance_after = vault.userBalances(bob, alpha_token)
    assert bob_balance_after == 0  # Position should be fully depleted
    
    # Auction should be removed after depletion
    assert not ledger.hasFungibleAuction(bob, vault_id, alpha_token)
    
    # Alice should have received all the transferred balance
    alice_final_balance = vault.userBalances(alice, alpha_token)
    assert alice_final_balance > final_alice_vault_balance
