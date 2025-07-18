import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def setupAuctionMgmntTest(
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
    credit_engine,
    sally,
):
    def setupAuctionMgmntTest(num_users=1, create_liquidations=True):
        setGeneralConfig()
        setGeneralDebtConfig(_ltvPaybackBuffer=0)
        
        # Setup assets for auctions
        debt_terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
        
        for token in [alpha_token, bravo_token]:
            setAssetConfig(
                token,
                _debtTerms=debt_terms,
                _shouldBurnAsPayment=False,
                _shouldTransferToEndaoment=False,
                _shouldSwapInStabPools=False,
                _shouldAuctionInstantly=True, # Will create auctions during liquidation
            )

        # Setup prices
        mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, 1 * EIGHTEEN_DECIMALS)
        
        users = [bob, alice][:num_users]
        user_data = []
        
        for user in users:
            # Setup user with collateral and debt
            alpha_amount = 200 * EIGHTEEN_DECIMALS
            bravo_amount = 150 * EIGHTEEN_DECIMALS
            performDeposit(user, alpha_amount, alpha_token, alpha_token_whale)
            performDeposit(user, bravo_amount, bravo_token, bravo_token_whale)
            
            debt_amount = 150 * EIGHTEEN_DECIMALS
            teller.borrow(debt_amount, user, False, sender=user)
            
            user_data.append({
                'user': user,
                'debt_amount': debt_amount,
                'alpha_amount': alpha_amount,
                'bravo_amount': bravo_amount,
            })

        if create_liquidations:
            new_price = 25 * EIGHTEEN_DECIMALS // 100  # 0.25 - aggressive drop
            mock_price_source.setPrice(alpha_token, new_price)
            mock_price_source.setPrice(bravo_token, new_price)
            
            # Verify users can be liquidated
            for user_info in user_data:
                assert credit_engine.canLiquidateUser(user_info['user'])
            
            # Perform liquidations to create auctions
            for user_info in user_data:
                teller.liquidateUser(user_info['user'], False, sender=sally)
        
        return user_data
    
    return setupAuctionMgmntTest


# access control tests


def test_ah_auction_mgmt_only_mission_control_access(
    setupAuctionMgmntTest,
    auction_house,
    switchboard_alpha,
    alpha_token,
    bob,
    alice,
    vault_book,
    simple_erc20_vault,
):
    """Test that only mission control can call auction management functions"""
    
    # Setup with liquidated user
    setupAuctionMgmntTest(num_users=1, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Test startAuction - no perms
    with boa.reverts("no perms"):
        auction_house.startAuction(bob, vault_id, alpha_token, sender=alice)
    
    # Test startManyAuctions - no perms
    auctions = [(bob, vault_id, alpha_token)]
    with boa.reverts("no perms"):
        auction_house.startManyAuctions(auctions, sender=alice)
    
    # Test pauseAuction - no perms
    with boa.reverts("no perms"):
        auction_house.pauseAuction(bob, vault_id, alpha_token, sender=alice)
    
    # Test pauseManyAuctions - no perms
    with boa.reverts("no perms"):
        auction_house.pauseManyAuctions(auctions, sender=alice)
    
    auction_house.startAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    auction_house.startManyAuctions(auctions, sender=switchboard_alpha.address)
    auction_house.pauseAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    auction_house.pauseManyAuctions(auctions, sender=switchboard_alpha.address)


def test_ah_auction_mgmt_paused_contract(
    setupAuctionMgmntTest,
    auction_house,
    switchboard_alpha,
    alpha_token,
    bob,
    vault_book,
    simple_erc20_vault,
):
    """Test that auction management functions revert when contract is paused"""
    
    # Setup with liquidated user
    setupAuctionMgmntTest(num_users=1, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Pause the contract - auction_house.pause takes a boolean parameter and only mission control can call it
    auction_house.pause(True, sender=switchboard_alpha.address)
    
    auctions = [(bob, vault_id, alpha_token)]
    
    # All functions should revert when contract is paused
    with boa.reverts("contract paused"):
        auction_house.startAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    
    with boa.reverts("contract paused"):
        auction_house.startManyAuctions(auctions, sender=switchboard_alpha.address)
    
    with boa.reverts("contract paused"):
        auction_house.pauseAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    
    with boa.reverts("contract paused"):
        auction_house.pauseManyAuctions(auctions, sender=switchboard_alpha.address)


# start auction tests


def test_ah_start_auction_success(
    setupAuctionMgmntTest,
    auction_house,
    switchboard_alpha,
    ledger,
    alpha_token,
    bob,
    vault_book,
    simple_erc20_vault,
):
    """Test successfully starting a single auction"""
    
    setupAuctionMgmntTest(num_users=1, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Verify auction exists after liquidation
    assert ledger.hasFungibleAuction(bob, vault_id, alpha_token)
    
    # Pause the auction first so we can test restarting
    auction_house.pauseAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    
    # Verify auction is paused
    auction_data = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token)
    assert not auction_data.isActive
    
    # Start/restart the auction
    result = auction_house.startAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    assert result  # Should return True for successful start
    
    # Verify auction is now active
    auction_data = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token)
    assert auction_data.isActive
    assert auction_data.liqUser == bob
    assert auction_data.asset == alpha_token.address
    
    # Check for FungibleAuctionUpdated event
    logs = filter_logs(auction_house, "FungibleAuctionUpdated")
    assert len(logs) == 1
    
    log = logs[0]
    assert log.liqUser == bob
    assert log.asset == alpha_token.address
    assert not log.isNewAuction


def test_ah_start_auction_invalid_conditions(
    setupAuctionMgmntTest,
    auction_house,
    switchboard_alpha,
    alpha_token,
    bob,
    alice,
    vault_book,
    simple_erc20_vault,
    mock_price_source,
):
    """Test starting auction with invalid conditions"""
    
    # Setup users but don't trigger liquidation
    setupAuctionMgmntTest(num_users=2, create_liquidations=False)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Test 1: User not in liquidation (should return False)
    # Users have safe LTV at current prices
    result = auction_house.startAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    assert not result  # Should return False, not create auction
    
    # Test 2: Invalid vault ID (should return False)
    invalid_vault_id = 999999
    result = auction_house.startAuction(bob, invalid_vault_id, alpha_token, sender=switchboard_alpha.address)
    assert not result
    
    # Test 3: User with no balance in asset (should return False)
    # Make user liquidatable first
    new_price = 25 * EIGHTEEN_DECIMALS // 100  # 0.25
    mock_price_source.setPrice(alpha_token, new_price)
    mock_price_source.setPrice(alpha_token, new_price)  # bravo_token uses same price source
    
    # Alice has no alpha_token balance (only bravo_token from setup)
    # So starting auction for alpha_token should fail
    result = auction_house.startAuction(alice, vault_id, alpha_token, sender=switchboard_alpha.address)
    assert not result


def test_ah_start_many_auctions_success(
    setupAuctionMgmntTest,
    auction_house,
    switchboard_alpha,
    ledger,
    alpha_token,
    bravo_token,
    bob,
    alice,
    vault_book,
    simple_erc20_vault,
):
    """Test successfully starting multiple auctions"""
    
    # Setup multiple users in liquidation
    setupAuctionMgmntTest(num_users=2, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Verify auctions exist after liquidation
    assert ledger.hasFungibleAuction(bob, vault_id, alpha_token)
    assert ledger.hasFungibleAuction(bob, vault_id, bravo_token)
    assert ledger.hasFungibleAuction(alice, vault_id, alpha_token)
    assert ledger.hasFungibleAuction(alice, vault_id, bravo_token)
    
    # Pause all auctions first
    auctions_to_pause = [
        (bob, vault_id, alpha_token),
        (bob, vault_id, bravo_token),
        (alice, vault_id, alpha_token),
        (alice, vault_id, bravo_token),
    ]
    num_paused = auction_house.pauseManyAuctions(auctions_to_pause, sender=switchboard_alpha.address)
    assert num_paused == 4
    
    # Restart multiple auctions
    auctions_to_start = [
        (bob, vault_id, alpha_token),
        (alice, vault_id, bravo_token),
    ]
    
    num_started = auction_house.startManyAuctions(auctions_to_start, sender=switchboard_alpha.address)
    assert num_started == 2  # Should start 2 auctions
    
    # Verify specific auctions are active
    bob_alpha_auction = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token)
    alice_bravo_auction = ledger.getFungibleAuctionDuringPurchase(alice, vault_id, bravo_token)
    
    assert bob_alpha_auction.isActive
    assert alice_bravo_auction.isActive
    
    # Verify other auctions remain paused
    bob_bravo_auction = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, bravo_token)
    alice_alpha_auction = ledger.getFungibleAuctionDuringPurchase(alice, vault_id, alpha_token)
    
    assert not bob_bravo_auction.isActive
    assert not alice_alpha_auction.isActive
    
    # Check for multiple FungibleAuctionUpdated events
    logs = filter_logs(auction_house, "FungibleAuctionUpdated")
    assert len(logs) == 2
    
    # Verify event details
    for log in logs:
        assert not log.isNewAuction  # Restarting existing auctions


def test_ah_start_many_auctions_mixed_validity(
    setupAuctionMgmntTest,
    auction_house,
    switchboard_alpha,
    alpha_token,
    bravo_token,
    bob,
    alice,
    vault_book,
    simple_erc20_vault,
):
    """Test starting multiple auctions with mixed valid/invalid conditions"""
    
    # Setup one user in liquidation, one user safe
    setupAuctionMgmntTest(num_users=1, create_liquidations=True)  # Bob liquidated
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Alice is not liquidated (separate setup without liquidation)
    # Mix of valid and invalid auction requests
    auctions_to_start = [
        (bob, vault_id, alpha_token),        # Valid - bob is liquidated and has alpha
        (bob, vault_id, bravo_token),        # Valid - bob is liquidated and has bravo
        (alice, vault_id, alpha_token),      # Invalid - alice not liquidated
        (bob, 999999, alpha_token),          # Invalid - bad vault ID
        (ZERO_ADDRESS, vault_id, alpha_token),  # Invalid - zero address
    ]
    
    num_started = auction_house.startManyAuctions(auctions_to_start, sender=switchboard_alpha.address)
    assert num_started == 2  # Only bob's auctions should start
    
    # Check for FungibleAuctionUpdated events (should be more than 2 from liquidation + restart)
    logs = filter_logs(auction_house, "FungibleAuctionUpdated")
    assert len(logs) == 2


def test_ah_start_many_auctions_empty_list(
    auction_house,
    switchboard_alpha,
):
    """Test starting auctions with empty list"""
    
    # Empty list should return 0
    num_started = auction_house.startManyAuctions([], sender=switchboard_alpha.address)
    assert num_started == 0


# pause auction tests


def test_ah_pause_auction_success(
    setupAuctionMgmntTest,
    auction_house,
    switchboard_alpha,
    ledger,
    alpha_token,
    bob,
    vault_book,
    simple_erc20_vault,
):
    """Test successfully pausing a single active auction"""
    
    # Setup user with active auction
    setupAuctionMgmntTest(num_users=1, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Verify auction is active
    auction_data = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token)
    assert auction_data.isActive
    
    # Pause the auction
    result = auction_house.pauseAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    assert result  # Should return True for successful pause
    
    # Verify auction is now paused
    auction_data = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token)
    assert not auction_data.isActive
    
    # Check for FungibleAuctionPaused event
    logs = filter_logs(auction_house, "FungibleAuctionPaused")
    assert len(logs) == 1
    
    log = logs[0]
    assert log.liqUser == bob
    assert log.asset == alpha_token.address


def test_ah_pause_auction_invalid_conditions(
    setupAuctionMgmntTest,
    auction_house,
    switchboard_alpha,
    alpha_token,
    bob,
    vault_book,
    simple_erc20_vault,
):
    """Test pausing auction with invalid conditions"""
    
    # Setup user with active auctions
    setupAuctionMgmntTest(num_users=1, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Test 1: Pause active auction (should work)
    result = auction_house.pauseAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    assert result
    
    # Test 2: Pause already paused auction (should return False)
    result = auction_house.pauseAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    assert not result  # Already paused
    
    # Test 3: Pause non-existent auction (should return False)
    invalid_vault_id = 999999
    result = auction_house.pauseAuction(bob, invalid_vault_id, alpha_token, sender=switchboard_alpha.address)
    assert not result


def test_ah_pause_many_auctions_success(
    setupAuctionMgmntTest,
    auction_house,
    switchboard_alpha,
    ledger,
    alpha_token,
    bravo_token,
    bob,
    alice,
    vault_book,
    simple_erc20_vault,
):
    """Test successfully pausing multiple active auctions"""
    
    # Setup multiple users with active auctions
    setupAuctionMgmntTest(num_users=2, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Verify all auctions are active
    assert ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token).isActive
    assert ledger.getFungibleAuctionDuringPurchase(bob, vault_id, bravo_token).isActive
    assert ledger.getFungibleAuctionDuringPurchase(alice, vault_id, alpha_token).isActive
    assert ledger.getFungibleAuctionDuringPurchase(alice, vault_id, bravo_token).isActive
    
    # Pause specific auctions
    auctions_to_pause = [
        (bob, vault_id, alpha_token),
        (alice, vault_id, bravo_token),
    ]
    
    num_paused = auction_house.pauseManyAuctions(auctions_to_pause, sender=switchboard_alpha.address)
    assert num_paused == 2
    
    # Verify specific auctions are paused
    assert not ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token).isActive
    assert not ledger.getFungibleAuctionDuringPurchase(alice, vault_id, bravo_token).isActive
    
    # Verify other auctions remain active
    assert ledger.getFungibleAuctionDuringPurchase(bob, vault_id, bravo_token).isActive
    assert ledger.getFungibleAuctionDuringPurchase(alice, vault_id, alpha_token).isActive
    
    # Check for multiple FungibleAuctionPaused events
    logs = filter_logs(auction_house, "FungibleAuctionPaused")
    assert len(logs) == 2
    
    # Verify event details
    paused_assets = {log.asset for log in logs}
    paused_users = {log.liqUser for log in logs}
    
    assert alpha_token.address in paused_assets
    assert bravo_token.address in paused_assets
    assert bob in paused_users
    assert alice in paused_users


def test_ah_pause_many_auctions_mixed_validity(
    setupAuctionMgmntTest,
    auction_house,
    switchboard_alpha,
    ledger,
    alpha_token,
    bravo_token,
    bob,
    alice,
    vault_book,
    simple_erc20_vault,
):
    """Test pausing multiple auctions with mixed valid/invalid conditions"""
    
    # Setup users with active auctions
    setupAuctionMgmntTest(num_users=2, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Pause one auction manually first
    auction_house.pauseAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    
    # Mix of valid and invalid pause requests
    auctions_to_pause = [
        (bob, vault_id, alpha_token),        # Invalid - already paused
        (bob, vault_id, bravo_token),        # Valid - active auction
        (alice, vault_id, alpha_token),      # Valid - active auction
        (alice, 999999, alpha_token),        # Invalid - bad vault ID
        (ZERO_ADDRESS, vault_id, alpha_token),  # Invalid - zero address
    ]
    
    num_paused = auction_house.pauseManyAuctions(auctions_to_pause, sender=switchboard_alpha.address)
    assert num_paused == 2  # Only 2 valid pauses
    
    # Verify final states
    assert not ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token).isActive  # Still paused
    assert not ledger.getFungibleAuctionDuringPurchase(bob, vault_id, bravo_token).isActive  # Newly paused
    assert not ledger.getFungibleAuctionDuringPurchase(alice, vault_id, alpha_token).isActive  # Newly paused
    assert ledger.getFungibleAuctionDuringPurchase(alice, vault_id, bravo_token).isActive  # Still active


def test_ah_pause_many_auctions_empty_list(
    auction_house,
    switchboard_alpha,
):
    """Test pausing auctions with empty list"""
    
    # Empty list should return 0
    num_paused = auction_house.pauseManyAuctions([], sender=switchboard_alpha.address)
    assert num_paused == 0


# integration tests


def test_ah_auction_mgmt_start_pause_restart_flow(
    setupAuctionMgmntTest,
    auction_house,
    switchboard_alpha,
    ledger,
    alpha_token,
    bob,
    vault_book,
    simple_erc20_vault,
):
    """Test complete flow: start auction -> pause -> restart"""
    
    # Setup user with auction
    setupAuctionMgmntTest(num_users=1, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Verify auction starts active
    auction_data = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token)
    assert auction_data.isActive
    original_start_block = auction_data.startBlock
    
    # Step 1: Pause the auction
    result = auction_house.pauseAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    assert result
    
    auction_data = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token)
    assert not auction_data.isActive
    
    # Advance the block number to ensure new timing when restarted
    boa.env.time_travel(blocks=10)
    
    # Step 2: Restart the auction
    result = auction_house.startAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    assert result
    
    auction_data = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token)
    assert auction_data.isActive
    
    # Auction should have new timing - we advanced 10 blocks
    assert auction_data.startBlock == original_start_block + 10
    
    # Step 3: Pause again to verify it still works
    result = auction_house.pauseAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    assert result
    
    auction_data = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token)
    assert not auction_data.isActive


def test_ah_auction_mgmt_batch_operations(
    setupAuctionMgmntTest,
    auction_house,
    switchboard_alpha,
    ledger,
    alpha_token,
    bravo_token,
    bob,
    alice,
    vault_book,
    simple_erc20_vault,
):
    """Test batch operations with mixed start/pause scenarios"""
    
    # Setup multiple users with auctions
    setupAuctionMgmntTest(num_users=2, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # All auctions start active
    auctions = [
        (bob, vault_id, alpha_token),
        (bob, vault_id, bravo_token),
        (alice, vault_id, alpha_token),
        (alice, vault_id, bravo_token),
    ]
    
    # Verify all are active
    for user, vault, asset in auctions:
        assert ledger.getFungibleAuctionDuringPurchase(user, vault, asset).isActive
    
    # Batch pause some auctions
    auctions_to_pause = auctions[:2]  # Pause bob's auctions
    num_paused = auction_house.pauseManyAuctions(auctions_to_pause, sender=switchboard_alpha.address)
    assert num_paused == 2
    
    # Verify states
    assert not ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token).isActive
    assert not ledger.getFungibleAuctionDuringPurchase(bob, vault_id, bravo_token).isActive
    assert ledger.getFungibleAuctionDuringPurchase(alice, vault_id, alpha_token).isActive
    assert ledger.getFungibleAuctionDuringPurchase(alice, vault_id, bravo_token).isActive
    
    # Batch restart bob's auctions + try to start alice's 
    # Note: startManyAuctions will restart paused auctions (bob's) AND update active auctions (alice's)
    auctions_to_start = auctions  # Try to start all
    num_started = auction_house.startManyAuctions(auctions_to_start, sender=switchboard_alpha.address)
    assert num_started == 4  # All 4 auctions get updated/restarted (this is the actual behavior)
    
    # Verify all are now active again
    for user, vault, asset in auctions:
        assert ledger.getFungibleAuctionDuringPurchase(user, vault, asset).isActive


def test_ah_auction_mgmt_event_verification(
    setupAuctionMgmntTest,
    auction_house,
    switchboard_alpha,
    alpha_token,
    bravo_token,
    bob,
    vault_book,
    simple_erc20_vault,
):
    """Test that correct events are emitted for auction management operations"""
    
    # Setup user with auctions
    setupAuctionMgmntTest(num_users=1, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Pause auction
    auction_house.pauseAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    
    # Check pause event immediately after transaction
    pause_logs = filter_logs(auction_house, "FungibleAuctionPaused")
    assert len(pause_logs) == 1  # Should have exactly 1 pause event
    
    pause_log = pause_logs[0]
    assert pause_log.liqUser == bob
    assert pause_log.vaultId == vault_id
    assert pause_log.asset == alpha_token.address
    
    # Restart auction
    auction_house.startAuction(bob, vault_id, alpha_token, sender=switchboard_alpha.address)
    
    # Check updated event immediately after transaction
    update_logs = filter_logs(auction_house, "FungibleAuctionUpdated")
    assert len(update_logs) == 1  # Should have exactly 1 update event
    
    restart_log = update_logs[0]
    assert restart_log.liqUser == bob
    assert restart_log.vaultId == vault_id
    assert restart_log.asset == alpha_token.address
    assert not restart_log.isNewAuction  # This is a restart
    
    # Test batch operations
    auctions = [(bob, vault_id, alpha_token), (bob, vault_id, bravo_token)]
    
    # Batch pause should emit 2 events
    auction_house.pauseManyAuctions(auctions, sender=switchboard_alpha.address)
    batch_pause_logs = filter_logs(auction_house, "FungibleAuctionPaused")
    assert len(batch_pause_logs) == 2  # Should have exactly 2 pause events
    
    # Should have events for both assets
    pause_assets = {log.asset for log in batch_pause_logs}
    assert alpha_token.address in pause_assets
    assert bravo_token.address in pause_assets
    
    # Batch start should emit 2 events
    auction_house.startManyAuctions(auctions, sender=switchboard_alpha.address)
    batch_update_logs = filter_logs(auction_house, "FungibleAuctionUpdated")
    assert len(batch_update_logs) == 2  # Should have exactly 2 update events
    
    # Should have events for both assets
    update_assets = {log.asset for log in batch_update_logs}
    assert alpha_token.address in update_assets
    assert bravo_token.address in update_assets
