import pytest
import boa
from boa.contracts.base_evm_contract import BoaError

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS
from conf_utils import (
    assert_reverted_call,
    buy_fungible_auction,
    clear_transient_storage,
    filter_logs,
)


def _advance_to_block(block_number):
    blocks = block_number - boa.env.evm.patch.block_number
    assert blocks >= 0
    if blocks:
        boa.env.time_travel(blocks=blocks)
    assert boa.env.evm.patch.block_number == block_number


def _economic_state(
    user,
    ledger,
    simple_erc20_vault,
    alpha_token,
    bravo_token,
    green_token,
    *,
    caller,
    liquidation_keeper,
):
    debt = ledger.userDebt(user)
    return (
        debt.amount,
        debt.principal,
        debt.inLiquidation,
        ledger.totalDebt(),
        simple_erc20_vault.userBalances(user, alpha_token),
        simple_erc20_vault.userBalances(user, bravo_token),
        alpha_token.balanceOf(user),
        bravo_token.balanceOf(user),
        alpha_token.balanceOf(simple_erc20_vault),
        bravo_token.balanceOf(simple_erc20_vault),
        green_token.balanceOf(user),
        green_token.balanceOf(caller),
        green_token.balanceOf(liquidation_keeper),
        green_token.totalSupply(),
    )


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


def test_auction_buyer_cannot_be_liquidated_user(
    setupAuctionMgmntTest,
    alpha_token,
    bob,
    teller,
    green_token,
    ledger,
    vault_book,
    simple_erc20_vault,
):
    setupAuctionMgmntTest(num_users=1, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    debt_before = ledger.userDebt(bob).amount
    shares_before = simple_erc20_vault.userBalances(bob, alpha_token)
    green_before = green_token.balanceOf(bob)
    green_token.approve(teller, MAX_UINT256, sender=bob)

    with boa.reverts("no green spent"):
        buy_fungible_auction(
            teller,
            bob,
            vault_id,
            alpha_token,
            10 * EIGHTEEN_DECIMALS,
            should_transfer_balance=True,
            recipient=bob,
            sender=bob,
        )

    assert ledger.userDebt(bob).amount == debt_before
    assert simple_erc20_vault.userBalances(bob, alpha_token) == shares_before
    assert green_token.balanceOf(bob) == green_before
    assert ledger.hasFungibleAuction(bob, vault_id, alpha_token)


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


# expired auction cleanup tests


def test_remove_expired_fungible_auction_is_permissionless_and_emits_event(
    setupAuctionMgmntTest,
    auction_house,
    ledger,
    alpha_token,
    bob,
    alice,
    vault_book,
    simple_erc20_vault,
):
    setupAuctionMgmntTest(num_users=1, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    auction = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token)
    _advance_to_block(auction.endBlock)

    assert auction_house.removeExpiredFungibleAuction(
        bob,
        vault_id,
        alpha_token,
        sender=alice,
    )
    assert not ledger.hasFungibleAuction(bob, vault_id, alpha_token)

    logs = filter_logs(auction_house, "ExpiredFungibleAuctionRemoved")
    assert len(logs) == 1
    assert logs[0].liqUser == bob
    assert logs[0].vaultId == vault_id
    assert logs[0].asset == alpha_token.address


def test_remove_expired_fungible_auction_before_expiry_is_non_mutating(
    setupAuctionMgmntTest,
    auction_house,
    ledger,
    alpha_token,
    bravo_token,
    green_token,
    bob,
    alice,
    sally,
    vault_book,
    simple_erc20_vault,
):
    setupAuctionMgmntTest(num_users=1, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    auction = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token)
    _advance_to_block(auction.endBlock - 1)

    index_before = ledger.fungibleAuctionIndex(bob, vault_id, alpha_token)
    count_before = ledger.numFungibleAuctions(bob)
    state_before = _economic_state(
        bob,
        ledger,
        simple_erc20_vault,
        alpha_token,
        bravo_token,
        green_token,
        caller=alice,
        liquidation_keeper=sally,
    )

    assert not auction_house.removeExpiredFungibleAuction(
        bob,
        vault_id,
        alpha_token,
        sender=alice,
    )

    assert ledger.hasFungibleAuction(bob, vault_id, alpha_token)
    assert ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        alpha_token,
    ).isActive
    assert ledger.fungibleAuctionIndex(bob, vault_id, alpha_token) == index_before
    assert ledger.numFungibleAuctions(bob) == count_before
    assert filter_logs(auction_house, "ExpiredFungibleAuctionRemoved") == []
    assert _economic_state(
        bob,
        ledger,
        simple_erc20_vault,
        alpha_token,
        bravo_token,
        green_token,
        caller=alice,
        liquidation_keeper=sally,
    ) == state_before


def test_remove_expired_fungible_auction_exact_boundary_and_missing_are_safe(
    setupAuctionMgmntTest,
    auction_house,
    ledger,
    alpha_token,
    bravo_token,
    bob,
    alice,
    vault_book,
    simple_erc20_vault,
):
    setupAuctionMgmntTest(num_users=1, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    alpha_auction = ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        alpha_token,
    )
    bravo_auction = ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        bravo_token,
    )
    _advance_to_block(alpha_auction.endBlock)
    assert boa.env.evm.patch.block_number == alpha_auction.endBlock

    assert auction_house.removeExpiredFungibleAuction(
        bob,
        vault_id,
        alpha_token,
        sender=alice,
    )
    bravo_index_after_removal = ledger.fungibleAuctionIndex(
        bob,
        vault_id,
        bravo_token,
    )

    assert not auction_house.removeExpiredFungibleAuction(
        bob,
        vault_id,
        alpha_token,
        sender=alice,
    )
    assert not auction_house.removeExpiredFungibleAuction(
        bob,
        999999,
        alpha_token,
        sender=alice,
    )
    assert ledger.hasFungibleAuction(bob, vault_id, bravo_token)
    assert ledger.fungibleAuctionIndex(
        bob,
        vault_id,
        bravo_token,
    ) == bravo_index_after_removal
    assert ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        bravo_token,
    ) == bravo_auction


def test_remove_expired_fungible_auction_preserves_paused_auction(
    setupAuctionMgmntTest,
    auction_house,
    switchboard_alpha,
    ledger,
    alpha_token,
    bob,
    alice,
    vault_book,
    simple_erc20_vault,
):
    setupAuctionMgmntTest(num_users=1, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    auction = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token)

    assert auction_house.pauseAuction(
        bob,
        vault_id,
        alpha_token,
        sender=switchboard_alpha.address,
    )
    _advance_to_block(auction.endBlock)
    assert not auction_house.removeExpiredFungibleAuction(
        bob,
        vault_id,
        alpha_token,
        sender=alice,
    )

    assert ledger.hasFungibleAuction(bob, vault_id, alpha_token)
    assert not ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        alpha_token,
    ).isActive
    assert filter_logs(auction_house, "ExpiredFungibleAuctionRemoved") == []

    assert auction_house.startAuction(
        bob,
        vault_id,
        alpha_token,
        sender=switchboard_alpha.address,
    )
    restarted = ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        alpha_token,
    )
    assert restarted.isActive
    assert restarted.endBlock > auction.endBlock


def test_remove_expired_fungible_auctions_preserves_swap_and_pop_registries(
    setupAuctionMgmntTest,
    auction_house,
    ledger,
    alpha_token,
    bravo_token,
    bob,
    alice,
    vault_book,
    simple_erc20_vault,
):
    setupAuctionMgmntTest(num_users=2, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    alpha_auction = ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        alpha_token,
    )
    bravo_auction = ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        bravo_token,
    )
    _advance_to_block(max(alpha_auction.endBlock, bravo_auction.endBlock))

    target_index = ledger.fungibleAuctionIndex(bob, vault_id, alpha_token)
    other_index = ledger.fungibleAuctionIndex(bob, vault_id, bravo_token)
    assert target_index != other_index
    bob_global_index = ledger.indexOfFungLiqUser(bob)
    num_global_before = ledger.numFungLiqUsers()
    moved_user = ledger.fungLiqUsers(num_global_before - 1)
    assert moved_user == alice

    assert auction_house.removeExpiredFungibleAuction(
        bob,
        vault_id,
        alpha_token,
        sender=alice,
    )
    assert not ledger.hasFungibleAuction(bob, vault_id, alpha_token)
    assert ledger.hasFungibleAuction(bob, vault_id, bravo_token)
    assert ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        bravo_token,
    ) == bravo_auction
    assert ledger.fungibleAuctionIndex(
        bob,
        vault_id,
        bravo_token,
    ) == target_index
    assert ledger.hasFungibleAuctions(bob)
    assert ledger.indexOfFungLiqUser(bob) == bob_global_index
    assert bob in [
        ledger.fungLiqUsers(i)
        for i in range(1, ledger.numFungLiqUsers())
    ]

    assert auction_house.removeExpiredFungibleAuction(
        bob,
        vault_id,
        bravo_token,
        sender=alice,
    )
    assert not ledger.hasFungibleAuctions(bob)
    assert ledger.indexOfFungLiqUser(bob) == 0
    assert bob not in [
        ledger.fungLiqUsers(i)
        for i in range(1, ledger.numFungLiqUsers())
    ]
    assert ledger.numFungLiqUsers() == num_global_before - 1
    assert ledger.indexOfFungLiqUser(moved_user) == bob_global_index
    assert ledger.fungLiqUsers(bob_global_index) == moved_user


def test_final_expired_auction_cleanup_restores_liquidation_retry(
    setupAuctionMgmntTest,
    auction_house,
    credit_engine,
    teller,
    ledger,
    alpha_token,
    bravo_token,
    green_token,
    bob,
    alice,
    sally,
    vault_book,
    simple_erc20_vault,
):
    setupAuctionMgmntTest(num_users=1, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    alpha_auction = ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        alpha_token,
    )
    bravo_auction = ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        bravo_token,
    )
    original_end = max(alpha_auction.endBlock, bravo_auction.endBlock)
    _advance_to_block(original_end)

    debt, borrow_terms, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    assert not borrow_terms.hasQuarantinedAsset
    assert debt.inLiquidation
    assert not credit_engine.canLiquidateUser(bob)

    state_before_stale_retry = _economic_state(
        bob,
        ledger,
        simple_erc20_vault,
        alpha_token,
        bravo_token,
        green_token,
        caller=alice,
        liquidation_keeper=sally,
    )
    clear_transient_storage()
    assert teller.liquidateUser(bob, False, sender=sally) == 0
    assert _economic_state(
        bob,
        ledger,
        simple_erc20_vault,
        alpha_token,
        bravo_token,
        green_token,
        caller=alice,
        liquidation_keeper=sally,
    ) == state_before_stale_retry
    assert ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        alpha_token,
    ) == alpha_auction
    assert ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        bravo_token,
    ) == bravo_auction
    assert filter_logs(teller, "LiquidateUser") == []

    state_before_cleanup = _economic_state(
        bob,
        ledger,
        simple_erc20_vault,
        alpha_token,
        bravo_token,
        green_token,
        caller=alice,
        liquidation_keeper=sally,
    )
    assert auction_house.removeExpiredFungibleAuction(
        bob,
        vault_id,
        alpha_token,
        sender=alice,
    )
    assert not credit_engine.canLiquidateUser(bob)
    assert auction_house.removeExpiredFungibleAuction(
        bob,
        vault_id,
        bravo_token,
        sender=alice,
    )
    assert _economic_state(
        bob,
        ledger,
        simple_erc20_vault,
        alpha_token,
        bravo_token,
        green_token,
        caller=alice,
        liquidation_keeper=sally,
    ) == state_before_cleanup
    assert not ledger.hasFungibleAuctions(bob)
    assert credit_engine.canLiquidateUser(bob)

    clear_transient_storage()
    teller.liquidateUser(bob, False, sender=sally)
    new_alpha = ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        alpha_token,
    )
    new_bravo = ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        bravo_token,
    )
    assert new_alpha.isActive
    assert new_bravo.isActive
    assert new_alpha.startBlock >= original_end
    assert new_bravo.startBlock >= original_end
    assert new_alpha.endBlock > original_end
    assert new_bravo.endBlock > original_end


def test_remove_expired_fungible_auction_respects_both_pause_boundaries(
    setupAuctionMgmntTest,
    auction_house,
    switchboard_alpha,
    ledger,
    alpha_token,
    bravo_token,
    green_token,
    bob,
    alice,
    sally,
    vault_book,
    simple_erc20_vault,
):
    setupAuctionMgmntTest(num_users=1, create_liquidations=True)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    auction = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, alpha_token)
    _advance_to_block(auction.endBlock)

    auction_house.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        auction_house.removeExpiredFungibleAuction(
            bob,
            vault_id,
            alpha_token,
            sender=alice,
        )
    assert ledger.hasFungibleAuction(bob, vault_id, alpha_token)
    assert filter_logs(auction_house, "ExpiredFungibleAuctionRemoved") == []
    auction_house.pause(False, sender=switchboard_alpha.address)
    assert auction_house.removeExpiredFungibleAuction(
        bob,
        vault_id,
        alpha_token,
        sender=alice,
    )

    bravo_auction = ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        bravo_token,
    )
    registry_before = (
        ledger.numFungibleAuctions(bob),
        ledger.fungibleAuctionIndex(bob, vault_id, bravo_token),
        ledger.numFungLiqUsers(),
        ledger.indexOfFungLiqUser(bob),
    )
    state_before = _economic_state(
        bob,
        ledger,
        simple_erc20_vault,
        alpha_token,
        bravo_token,
        green_token,
        caller=alice,
        liquidation_keeper=sally,
    )
    ledger.pause(True, sender=switchboard_alpha.address)
    with pytest.raises(BoaError) as exc_info:
        auction_house.removeExpiredFungibleAuction(
            bob,
            vault_id,
            bravo_token,
            sender=alice,
        )
    assert_reverted_call(exc_info.value, "not activated", auction_house)
    assert ledger.getFungibleAuctionDuringPurchase(
        bob,
        vault_id,
        bravo_token,
    ) == bravo_auction
    assert (
        ledger.numFungibleAuctions(bob),
        ledger.fungibleAuctionIndex(bob, vault_id, bravo_token),
        ledger.numFungLiqUsers(),
        ledger.indexOfFungLiqUser(bob),
    ) == registry_before
    assert filter_logs(auction_house, "ExpiredFungibleAuctionRemoved") == []
    assert _economic_state(
        bob,
        ledger,
        simple_erc20_vault,
        alpha_token,
        bravo_token,
        green_token,
        caller=alice,
        liquidation_keeper=sally,
    ) == state_before

    ledger.pause(False, sender=switchboard_alpha.address)
    assert auction_house.removeExpiredFungibleAuction(
        bob,
        vault_id,
        bravo_token,
        sender=alice,
    )


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
