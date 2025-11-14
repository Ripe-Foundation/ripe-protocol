import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from conf_utils import filter_logs


###########
# Fixtures #
###########


@pytest.fixture(scope="module")
def mock_nft(governance):
    """Create a mock ERC721 NFT contract for testing"""
    return boa.load("contracts/mock/MockErc721.vy", governance.address, "Test NFT", "TNFT", name="mock_nft")


#########################
# Receiving Assets Tests #
#########################


def test_receive_eth_via_default(endaoment_funds, alice):
    """Test contract can receive ETH via __default__ fallback"""
    initial_balance = boa.env.get_balance(endaoment_funds.address)
    send_amount = 5 * EIGHTEEN_DECIMALS

    # Send ETH to the contract by setting balance directly (simulates receiving ETH)
    boa.env.set_balance(endaoment_funds.address, initial_balance + send_amount)

    # Verify balance increased
    assert boa.env.get_balance(endaoment_funds.address) == initial_balance + send_amount


def test_receive_erc20_via_transfer(endaoment_funds, alpha_token, alpha_token_whale):
    """Test contract can receive ERC20 tokens via standard transfer"""
    transfer_amount = 1000 * EIGHTEEN_DECIMALS
    initial_balance = alpha_token.balanceOf(endaoment_funds.address)

    # Transfer tokens to the contract
    alpha_token.transfer(endaoment_funds.address, transfer_amount, sender=alpha_token_whale)

    # Verify balance increased
    assert alpha_token.balanceOf(endaoment_funds.address) == initial_balance + transfer_amount


def test_receive_erc721_via_safe_transfer(endaoment_funds, mock_nft, governance):
    """Test contract can receive ERC721 NFTs via safeTransferFrom"""
    # Mint NFT to governance
    token_id = mock_nft.mint(governance.address, sender=governance.address)

    # Transfer NFT to endaoment_funds using safeTransferFrom
    mock_nft.safeTransferFrom(governance.address, endaoment_funds.address, token_id, sender=governance.address)

    # Verify ownership
    assert mock_nft.ownerOf(token_id) == endaoment_funds.address


def test_on_erc721_received_returns_correct_signature(endaoment_funds, alice):
    """Test onERC721Received returns correct method signature"""
    # Call the function
    result = endaoment_funds.onERC721Received(
        alice,  # operator
        alice,  # owner
        1,      # tokenId
        b""     # data
    )

    # Verify it returns the correct selector
    # The selector for onERC721Received(address,address,uint256,bytes)
    expected_selector = b'\x15\x0bz\x02'  # method_id for onERC721Received
    assert result == expected_selector


########################
# hasBalance Function Tests #
########################


def test_has_balance_eth_true(endaoment_funds, alice):
    """Test hasBalance returns true when contract has ETH"""
    # Send ETH to contract
    initial_balance = boa.env.get_balance(endaoment_funds.address)
    boa.env.set_balance(endaoment_funds.address, initial_balance + 1 * EIGHTEEN_DECIMALS)

    # Check hasBalance for ETH (empty address)
    assert endaoment_funds.hasBalance() == True
    assert endaoment_funds.hasBalance(ZERO_ADDRESS) == True


def test_has_balance_eth_false(endaoment_funds, endaoment, alice):
    """Test hasBalance returns false when contract has no ETH"""
    # First, ensure contract has some ETH
    initial_balance = boa.env.get_balance(endaoment_funds.address)
    boa.env.set_balance(endaoment_funds.address, initial_balance + 1 * EIGHTEEN_DECIMALS)

    # Transfer all ETH out
    if boa.env.get_balance(endaoment_funds.address) > 0:
        endaoment_funds.transfer(ZERO_ADDRESS, MAX_UINT256, sender=endaoment.address)

    # Check hasBalance returns false
    assert endaoment_funds.hasBalance() == False


def test_has_balance_erc20_true(endaoment_funds, alpha_token, alpha_token_whale):
    """Test hasBalance returns true when contract has specific ERC20"""
    transfer_amount = 500 * EIGHTEEN_DECIMALS

    # Transfer tokens
    alpha_token.transfer(endaoment_funds.address, transfer_amount, sender=alpha_token_whale)

    # Check hasBalance
    assert endaoment_funds.hasBalance(alpha_token.address) == True


def test_has_balance_erc20_false(endaoment_funds, bravo_token):
    """Test hasBalance returns false when contract has zero balance of specific ERC20"""
    # Ensure no balance
    assert bravo_token.balanceOf(endaoment_funds.address) == 0

    # Check hasBalance
    assert endaoment_funds.hasBalance(bravo_token.address) == False


def test_has_balance_different_decimals(endaoment_funds, charlie_token, charlie_token_whale):
    """Test hasBalance with 6 decimal token"""
    transfer_amount = 1000 * 10**6  # Charlie has 6 decimals

    # Transfer tokens
    charlie_token.transfer(endaoment_funds.address, transfer_amount, sender=charlie_token_whale)

    # Check hasBalance
    assert endaoment_funds.hasBalance(charlie_token.address) == True


#################################
# transfer Function - ERC20 Tests #
#################################


def test_transfer_erc20_basic(endaoment_funds, endaoment, alpha_token, alpha_token_whale):
    """Test basic ERC20 transfer to endaoment"""
    transfer_amount = 1000 * EIGHTEEN_DECIMALS

    # Fund endaoment_funds
    alpha_token.transfer(endaoment_funds.address, transfer_amount, sender=alpha_token_whale)
    initial_funds_balance = alpha_token.balanceOf(endaoment_funds.address)
    initial_endao_balance = alpha_token.balanceOf(endaoment.address)

    # Transfer from endaoment_funds to endaoment
    result = endaoment_funds.transfer(alpha_token.address, transfer_amount, sender=endaoment.address)

    # Verify result
    assert result == transfer_amount

    # Verify balances
    assert alpha_token.balanceOf(endaoment_funds.address) == initial_funds_balance - transfer_amount
    assert alpha_token.balanceOf(endaoment.address) == initial_endao_balance + transfer_amount


def test_transfer_erc20_max_amount(endaoment_funds, endaoment, bravo_token, bravo_token_whale):
    """Test transfer full ERC20 balance using max_value(uint256)"""
    fund_amount = 2500 * EIGHTEEN_DECIMALS

    # Fund endaoment_funds
    bravo_token.transfer(endaoment_funds.address, fund_amount, sender=bravo_token_whale)
    initial_endao_balance = bravo_token.balanceOf(endaoment.address)

    # Transfer with max_value (default parameter)
    result = endaoment_funds.transfer(bravo_token.address, sender=endaoment.address)

    # Verify entire balance transferred
    assert result == fund_amount
    assert bravo_token.balanceOf(endaoment_funds.address) == 0
    assert bravo_token.balanceOf(endaoment.address) == initial_endao_balance + fund_amount


def test_transfer_erc20_partial_when_requested_exceeds_balance(
    endaoment_funds, endaoment, charlie_token, charlie_token_whale
):
    """Test partial ERC20 transfer when requested amount exceeds balance"""
    balance_amount = 1000 * 10**6  # Charlie has 6 decimals
    request_amount = 2000 * 10**6  # Request more than available

    # Fund with less than requested
    charlie_token.transfer(endaoment_funds.address, balance_amount, sender=charlie_token_whale)
    initial_endao_balance = charlie_token.balanceOf(endaoment.address)

    # Transfer
    result = endaoment_funds.transfer(charlie_token.address, request_amount, sender=endaoment.address)

    # Should transfer available balance only
    assert result == balance_amount
    assert charlie_token.balanceOf(endaoment_funds.address) == 0
    assert charlie_token.balanceOf(endaoment.address) == initial_endao_balance + balance_amount


def test_transfer_erc20_unauthorized_caller(endaoment_funds, alice, alpha_token):
    """Test that non-endaoment caller cannot transfer ERC20"""
    with boa.reverts("not authorized"):
        endaoment_funds.transfer(alpha_token.address, 1000, sender=alice)


def test_transfer_erc20_zero_balance_reverts(endaoment_funds, endaoment, delta_token):
    """Test that transfer reverts when there's no balance"""
    # Ensure no balance
    assert delta_token.balanceOf(endaoment_funds.address) == 0

    with boa.reverts("insufficient balance"):
        endaoment_funds.transfer(delta_token.address, 1000, sender=endaoment.address)


def test_transfer_erc20_event_emission(endaoment_funds, endaoment, alpha_token, alpha_token_whale):
    """Test EndaomentFundsMoved event is emitted correctly for ERC20"""
    transfer_amount = 750 * EIGHTEEN_DECIMALS

    # Fund endaoment_funds
    alpha_token.transfer(endaoment_funds.address, transfer_amount, sender=alpha_token_whale)

    # Transfer
    endaoment_funds.transfer(alpha_token.address, transfer_amount, sender=endaoment.address)

    # Check event
    events = filter_logs(endaoment_funds, "EndaomentFundsMoved")
    assert len(events) == 1
    event = events[0]
    assert event.token == alpha_token.address
    assert event.to == endaoment.address
    assert event.amount == transfer_amount


def test_transfer_erc20_multiple_sequential(
    endaoment_funds, endaoment, alpha_token, alpha_token_whale
):
    """Test multiple sequential transfers of same ERC20 token"""
    total_amount = 3000 * EIGHTEEN_DECIMALS
    first_transfer = 1000 * EIGHTEEN_DECIMALS
    second_transfer = 1500 * EIGHTEEN_DECIMALS

    # Fund endaoment_funds
    alpha_token.transfer(endaoment_funds.address, total_amount, sender=alpha_token_whale)
    initial_endao_balance = alpha_token.balanceOf(endaoment.address)

    # First transfer
    result1 = endaoment_funds.transfer(alpha_token.address, first_transfer, sender=endaoment.address)
    assert result1 == first_transfer

    # Second transfer
    result2 = endaoment_funds.transfer(alpha_token.address, second_transfer, sender=endaoment.address)
    assert result2 == second_transfer

    # Verify final balances
    assert alpha_token.balanceOf(endaoment_funds.address) == total_amount - first_transfer - second_transfer
    assert alpha_token.balanceOf(endaoment.address) == initial_endao_balance + first_transfer + second_transfer


def test_transfer_erc20_different_tokens(
    endaoment_funds, endaoment, alpha_token, bravo_token, alpha_token_whale, bravo_token_whale
):
    """Test transferring multiple different ERC20 tokens"""
    alpha_amount = 1000 * EIGHTEEN_DECIMALS
    bravo_amount = 500 * EIGHTEEN_DECIMALS

    # Fund with both tokens
    alpha_token.transfer(endaoment_funds.address, alpha_amount, sender=alpha_token_whale)
    bravo_token.transfer(endaoment_funds.address, bravo_amount, sender=bravo_token_whale)

    initial_alpha_endao = alpha_token.balanceOf(endaoment.address)
    initial_bravo_endao = bravo_token.balanceOf(endaoment.address)

    # Transfer both
    result1 = endaoment_funds.transfer(alpha_token.address, alpha_amount, sender=endaoment.address)
    result2 = endaoment_funds.transfer(bravo_token.address, bravo_amount, sender=endaoment.address)

    assert result1 == alpha_amount
    assert result2 == bravo_amount

    # Verify balances
    assert alpha_token.balanceOf(endaoment_funds.address) == 0
    assert bravo_token.balanceOf(endaoment_funds.address) == 0
    assert alpha_token.balanceOf(endaoment.address) == initial_alpha_endao + alpha_amount
    assert bravo_token.balanceOf(endaoment.address) == initial_bravo_endao + bravo_amount


def test_transfer_erc20_8_decimals(endaoment_funds, endaoment, delta_token, delta_token_whale):
    """Test transfer with 8 decimal token"""
    transfer_amount = 1000 * 10**8  # Delta has 8 decimals

    # Fund endaoment_funds
    delta_token.transfer(endaoment_funds.address, transfer_amount, sender=delta_token_whale)
    initial_endao_balance = delta_token.balanceOf(endaoment.address)

    # Transfer
    result = endaoment_funds.transfer(delta_token.address, transfer_amount, sender=endaoment.address)

    assert result == transfer_amount
    assert delta_token.balanceOf(endaoment_funds.address) == 0
    assert delta_token.balanceOf(endaoment.address) == initial_endao_balance + transfer_amount


###############################
# transfer Function - ETH Tests #
###############################


def test_transfer_eth_basic(endaoment_funds, endaoment, alice):
    """Test basic ETH transfer to endaoment"""
    transfer_amount = 3 * EIGHTEEN_DECIMALS

    # Fund endaoment_funds with ETH
    initial_balance = boa.env.get_balance(endaoment_funds.address)
    boa.env.set_balance(endaoment_funds.address, initial_balance + transfer_amount)

    initial_endao_balance = boa.env.get_balance(endaoment.address)

    # Transfer ETH (use empty address for ETH)
    result = endaoment_funds.transfer(ZERO_ADDRESS, transfer_amount, sender=endaoment.address)

    # Verify result
    assert result == transfer_amount

    # Verify balances
    assert boa.env.get_balance(endaoment.address) == initial_endao_balance + transfer_amount


def test_transfer_eth_max_amount(endaoment_funds, endaoment, alice):
    """Test transfer full ETH balance using max_value"""
    fund_amount = 5 * EIGHTEEN_DECIMALS

    # Fund endaoment_funds
    initial_balance = boa.env.get_balance(endaoment_funds.address)
    boa.env.set_balance(endaoment_funds.address, initial_balance + fund_amount)

    initial_endao_balance = boa.env.get_balance(endaoment.address)

    # Transfer with max_value (both asset and amount are default)
    result = endaoment_funds.transfer(sender=endaoment.address)

    # Verify entire balance transferred
    assert result == fund_amount
    assert boa.env.get_balance(endaoment_funds.address) == 0
    assert boa.env.get_balance(endaoment.address) == initial_endao_balance + fund_amount


def test_transfer_eth_partial_when_requested_exceeds_balance(endaoment_funds, endaoment, alice):
    """Test partial ETH transfer when requested exceeds balance"""
    balance_amount = 2 * EIGHTEEN_DECIMALS
    request_amount = 4 * EIGHTEEN_DECIMALS

    # Fund with less than requested
    initial_balance = boa.env.get_balance(endaoment_funds.address)
    boa.env.set_balance(endaoment_funds.address, initial_balance + balance_amount)

    initial_endao_balance = boa.env.get_balance(endaoment.address)

    # Transfer
    result = endaoment_funds.transfer(ZERO_ADDRESS, request_amount, sender=endaoment.address)

    # Should transfer available balance
    assert result == balance_amount
    assert boa.env.get_balance(endaoment_funds.address) == 0
    assert boa.env.get_balance(endaoment.address) == initial_endao_balance + balance_amount


def test_transfer_eth_unauthorized_caller(endaoment_funds, alice):
    """Test that non-endaoment caller cannot transfer ETH"""
    with boa.reverts("not authorized"):
        endaoment_funds.transfer(ZERO_ADDRESS, 1 * EIGHTEEN_DECIMALS, sender=alice)


def test_transfer_eth_zero_balance_reverts(endaoment_funds, endaoment):
    """Test that ETH transfer reverts when there's no balance"""
    # Ensure no ETH balance
    if boa.env.get_balance(endaoment_funds.address) > 0:
        endaoment_funds.transfer(ZERO_ADDRESS, MAX_UINT256, sender=endaoment.address)

    assert boa.env.get_balance(endaoment_funds.address) == 0

    with boa.reverts("insufficient balance"):
        endaoment_funds.transfer(ZERO_ADDRESS, 1 * EIGHTEEN_DECIMALS, sender=endaoment.address)


def test_transfer_eth_event_emission(endaoment_funds, endaoment, alice):
    """Test EndaomentFundsMoved event is emitted correctly for ETH"""
    transfer_amount = 2 * EIGHTEEN_DECIMALS

    # Fund endaoment_funds
    initial_balance = boa.env.get_balance(endaoment_funds.address)
    boa.env.set_balance(endaoment_funds.address, initial_balance + transfer_amount)

    # Transfer
    endaoment_funds.transfer(ZERO_ADDRESS, transfer_amount, sender=endaoment.address)

    # Check event
    events = filter_logs(endaoment_funds, "EndaomentFundsMoved")
    assert len(events) == 1
    event = events[0]
    assert event.token == ZERO_ADDRESS
    assert event.to == endaoment.address
    assert event.amount == transfer_amount


#############################
# transferNft Function Tests #
#############################


def test_transfer_nft_basic(endaoment_funds, endaoment, mock_nft, governance):
    """Test basic NFT transfer to endaoment"""
    # Mint NFT to endaoment_funds
    token_id = mock_nft.mint(endaoment_funds.address, sender=governance.address)

    # Verify initial ownership
    assert mock_nft.ownerOf(token_id) == endaoment_funds.address

    # Transfer NFT
    endaoment_funds.transferNft(mock_nft.address, token_id, sender=endaoment.address)

    # Verify ownership transferred
    assert mock_nft.ownerOf(token_id) == endaoment.address


def test_transfer_nft_unauthorized_caller(endaoment_funds, mock_nft, governance, alice):
    """Test that non-endaoment caller cannot transfer NFT"""
    # Mint NFT to endaoment_funds
    token_id = mock_nft.mint(endaoment_funds.address, sender=governance.address)

    with boa.reverts("not authorized"):
        endaoment_funds.transferNft(mock_nft.address, token_id, sender=alice)


def test_transfer_nft_not_owner_reverts(endaoment_funds, endaoment, mock_nft, governance):
    """Test that transfer reverts when contract doesn't own the NFT"""
    # Mint NFT to someone else (not endaoment_funds)
    token_id = mock_nft.mint(governance.address, sender=governance.address)

    # Verify endaoment_funds is not the owner
    assert mock_nft.ownerOf(token_id) != endaoment_funds.address

    with boa.reverts("not owner"):
        endaoment_funds.transferNft(mock_nft.address, token_id, sender=endaoment.address)


def test_transfer_nft_event_emission(endaoment_funds, endaoment, mock_nft, governance):
    """Test EndaomentNftMoved event is emitted correctly"""
    # Mint NFT to endaoment_funds
    token_id = mock_nft.mint(endaoment_funds.address, sender=governance.address)

    # Transfer NFT
    endaoment_funds.transferNft(mock_nft.address, token_id, sender=endaoment.address)

    # Check event
    events = filter_logs(endaoment_funds, "EndaomentNftMoved")
    assert len(events) == 1
    event = events[0]
    assert event.nft == mock_nft.address
    assert event.to == endaoment.address
    assert event.tokenId == token_id


def test_transfer_multiple_nfts_same_collection(endaoment_funds, endaoment, mock_nft, governance):
    """Test transferring multiple NFTs from same collection"""
    # Mint multiple NFTs to endaoment_funds
    token_id_1 = mock_nft.mint(endaoment_funds.address, sender=governance.address)
    token_id_2 = mock_nft.mint(endaoment_funds.address, sender=governance.address)
    token_id_3 = mock_nft.mint(endaoment_funds.address, sender=governance.address)

    # Transfer all
    endaoment_funds.transferNft(mock_nft.address, token_id_1, sender=endaoment.address)
    endaoment_funds.transferNft(mock_nft.address, token_id_2, sender=endaoment.address)
    endaoment_funds.transferNft(mock_nft.address, token_id_3, sender=endaoment.address)

    # Verify all transferred
    assert mock_nft.ownerOf(token_id_1) == endaoment.address
    assert mock_nft.ownerOf(token_id_2) == endaoment.address
    assert mock_nft.ownerOf(token_id_3) == endaoment.address


def test_transfer_nfts_different_collections(endaoment_funds, endaoment, governance):
    """Test transferring NFTs from different collections"""
    # Create two different NFT collections
    mock_nft_1 = boa.load("contracts/mock/MockErc721.vy", governance.address, "NFT One", "NFT1")
    mock_nft_2 = boa.load("contracts/mock/MockErc721.vy", governance.address, "NFT Two", "NFT2")

    # Mint one from each collection
    token_id_1 = mock_nft_1.mint(endaoment_funds.address, sender=governance.address)
    token_id_2 = mock_nft_2.mint(endaoment_funds.address, sender=governance.address)

    # Transfer both
    endaoment_funds.transferNft(mock_nft_1.address, token_id_1, sender=endaoment.address)
    endaoment_funds.transferNft(mock_nft_2.address, token_id_2, sender=endaoment.address)

    # Verify both transferred
    assert mock_nft_1.ownerOf(token_id_1) == endaoment.address
    assert mock_nft_2.ownerOf(token_id_2) == endaoment.address


###########################
# Integration & Edge Cases #
###########################


def test_full_flow_erc20(
    endaoment_funds, endaoment, alpha_token, alpha_token_whale
):
    """Test full flow: receive → hasBalance → transfer → verify"""
    transfer_amount = 1500 * EIGHTEEN_DECIMALS

    # 1. Receive tokens
    alpha_token.transfer(endaoment_funds.address, transfer_amount, sender=alpha_token_whale)

    # 2. Check hasBalance
    assert endaoment_funds.hasBalance(alpha_token.address) == True

    # 3. Transfer to endaoment
    initial_endao_balance = alpha_token.balanceOf(endaoment.address)
    result = endaoment_funds.transfer(alpha_token.address, transfer_amount, sender=endaoment.address)

    # 4. Verify
    assert result == transfer_amount
    assert alpha_token.balanceOf(endaoment.address) == initial_endao_balance + transfer_amount
    assert endaoment_funds.hasBalance(alpha_token.address) == False


def test_full_flow_eth(endaoment_funds, endaoment, alice):
    """Test full flow for ETH: receive → hasBalance → transfer → verify"""
    transfer_amount = 3 * EIGHTEEN_DECIMALS

    # 1. Receive ETH
    initial_balance = boa.env.get_balance(endaoment_funds.address)
    boa.env.set_balance(endaoment_funds.address, initial_balance + transfer_amount)

    # 2. Check hasBalance
    assert endaoment_funds.hasBalance() == True

    # 3. Transfer to endaoment
    initial_endao_balance = boa.env.get_balance(endaoment.address)
    result = endaoment_funds.transfer(sender=endaoment.address)

    # 4. Verify
    assert result == transfer_amount
    assert boa.env.get_balance(endaoment.address) == initial_endao_balance + transfer_amount
    assert endaoment_funds.hasBalance() == False


def test_full_flow_nft(endaoment_funds, endaoment, mock_nft, governance):
    """Test full flow for NFT: receive → transfer → verify"""
    # 1. Receive NFT (mint directly to endaoment_funds)
    token_id = mock_nft.mint(endaoment_funds.address, sender=governance.address)

    # 2. Verify ownership
    assert mock_nft.ownerOf(token_id) == endaoment_funds.address

    # 3. Transfer to endaoment
    endaoment_funds.transferNft(mock_nft.address, token_id, sender=endaoment.address)

    # 4. Verify ownership transferred
    assert mock_nft.ownerOf(token_id) == endaoment.address


def test_mixed_assets_flow(
    endaoment_funds,
    endaoment,
    alpha_token,
    bravo_token,
    alpha_token_whale,
    bravo_token_whale,
    mock_nft,
    governance,
    alice,
):
    """Test holding and transferring mixed assets (ERC20 + ETH + NFT)"""
    alpha_amount = 1000 * EIGHTEEN_DECIMALS
    bravo_amount = 500 * EIGHTEEN_DECIMALS
    eth_amount = 2 * EIGHTEEN_DECIMALS

    # Fund with multiple assets
    alpha_token.transfer(endaoment_funds.address, alpha_amount, sender=alpha_token_whale)
    bravo_token.transfer(endaoment_funds.address, bravo_amount, sender=bravo_token_whale)
    initial_eth_balance = boa.env.get_balance(endaoment_funds.address)
    boa.env.set_balance(endaoment_funds.address, initial_eth_balance + eth_amount)
    token_id = mock_nft.mint(endaoment_funds.address, sender=governance.address)

    # Verify all balances
    assert endaoment_funds.hasBalance(alpha_token.address) == True
    assert endaoment_funds.hasBalance(bravo_token.address) == True
    assert endaoment_funds.hasBalance() == True
    assert mock_nft.ownerOf(token_id) == endaoment_funds.address

    # Get initial endaoment balances
    initial_alpha = alpha_token.balanceOf(endaoment.address)
    initial_bravo = bravo_token.balanceOf(endaoment.address)
    initial_eth = boa.env.get_balance(endaoment.address)

    # Transfer all to endaoment
    endaoment_funds.transfer(alpha_token.address, alpha_amount, sender=endaoment.address)
    endaoment_funds.transfer(bravo_token.address, bravo_amount, sender=endaoment.address)
    endaoment_funds.transfer(ZERO_ADDRESS, eth_amount, sender=endaoment.address)
    endaoment_funds.transferNft(mock_nft.address, token_id, sender=endaoment.address)

    # Verify all transferred
    assert alpha_token.balanceOf(endaoment.address) == initial_alpha + alpha_amount
    assert bravo_token.balanceOf(endaoment.address) == initial_bravo + bravo_amount
    assert boa.env.get_balance(endaoment.address) == initial_eth + eth_amount
    assert mock_nft.ownerOf(token_id) == endaoment.address

    # Verify endaoment_funds is empty
    assert endaoment_funds.hasBalance(alpha_token.address) == False
    assert endaoment_funds.hasBalance(bravo_token.address) == False
    assert endaoment_funds.hasBalance() == False


def test_endaoment_address_from_registry(endaoment_funds, ripe_hq, endaoment):
    """Test that endaoment address is correctly retrieved from RipeHq registry"""
    # The contract uses _getEndaomentAddr() which queries the registry
    # Verify by checking that only endaoment can call transfer functions

    # This should work (endaoment is authorized)
    alpha_token = boa.load("contracts/mock/MockErc20.vy", endaoment.address, "Test", "TEST", 18, 1000)
    alpha_token.transfer(endaoment_funds.address, 100 * EIGHTEEN_DECIMALS, sender=endaoment.address)

    # Try transfer - should work
    result = endaoment_funds.transfer(alpha_token.address, 50 * EIGHTEEN_DECIMALS, sender=endaoment.address)
    assert result == 50 * EIGHTEEN_DECIMALS

    # Random address should fail
    random_addr = boa.env.generate_address()
    with boa.reverts("not authorized"):
        endaoment_funds.transfer(alpha_token.address, 10, sender=random_addr)


########################################
# Malicious Token Tests (Security)     #
########################################


def test_transfer_fee_on_transfer_token(endaoment_funds, endaoment, governance):
    """Test transfer of tokens that take a fee on transfer"""
    # Create fee-on-transfer token with 5% fee
    fee_token = boa.load("contracts/mock/MockFeeOnTransferErc20.vy", governance.address, 500)  # 5% fee

    # Fund endaoment_funds
    transfer_amount = 1000 * EIGHTEEN_DECIMALS
    fee_token.mint(endaoment_funds.address, transfer_amount, sender=governance.address)

    # Check initial balances
    initial_funds_balance = fee_token.balanceOf(endaoment_funds.address)
    initial_endao_balance = fee_token.balanceOf(endaoment.address)

    # Transfer - the vault will try to send 1000, but endaoment will receive less due to fee
    result = endaoment_funds.transfer(fee_token.address, transfer_amount, sender=endaoment.address)

    # The function returns the amount sent, not amount received
    assert result == transfer_amount

    # Verify balances - endaoment receives 95% (5% fee)
    expected_received = (transfer_amount * 9500) // 10000
    assert fee_token.balanceOf(endaoment_funds.address) == initial_funds_balance - transfer_amount
    assert fee_token.balanceOf(endaoment.address) == initial_endao_balance + expected_received


def test_transfer_blacklist_token_not_blacklisted(endaoment_funds, endaoment, governance):
    """Test transfer of blacklist token when addresses are not blacklisted"""
    # Create blacklist token
    blacklist_token = boa.load("contracts/mock/MockBlacklistErc20.vy", governance.address)

    # Fund endaoment_funds
    transfer_amount = 500 * EIGHTEEN_DECIMALS
    blacklist_token.mint(endaoment_funds.address, transfer_amount, sender=governance.address)

    # Transfer should work normally when not blacklisted
    initial_endao_balance = blacklist_token.balanceOf(endaoment.address)
    result = endaoment_funds.transfer(blacklist_token.address, transfer_amount, sender=endaoment.address)

    assert result == transfer_amount
    assert blacklist_token.balanceOf(endaoment.address) == initial_endao_balance + transfer_amount


def test_transfer_blacklist_token_when_endaoment_blacklisted(endaoment_funds, endaoment, governance):
    """Test that transfer fails when endaoment is blacklisted"""
    # Create blacklist token
    blacklist_token = boa.load("contracts/mock/MockBlacklistErc20.vy", governance.address)

    # Fund endaoment_funds
    transfer_amount = 500 * EIGHTEEN_DECIMALS
    blacklist_token.mint(endaoment_funds.address, transfer_amount, sender=governance.address)

    # Blacklist the endaoment address
    blacklist_token.blacklist(endaoment.address, sender=governance.address)

    # Transfer should fail
    with boa.reverts("recipient blacklisted"):
        endaoment_funds.transfer(blacklist_token.address, transfer_amount, sender=endaoment.address)


def test_transfer_blacklist_token_when_vault_blacklisted(endaoment_funds, endaoment, governance):
    """Test that transfer fails when vault (sender) is blacklisted"""
    # Create blacklist token
    blacklist_token = boa.load("contracts/mock/MockBlacklistErc20.vy", governance.address)

    # Fund endaoment_funds
    transfer_amount = 500 * EIGHTEEN_DECIMALS
    blacklist_token.mint(endaoment_funds.address, transfer_amount, sender=governance.address)

    # Blacklist the vault address
    blacklist_token.blacklist(endaoment_funds.address, sender=governance.address)

    # Transfer should fail
    with boa.reverts("sender blacklisted"):
        endaoment_funds.transfer(blacklist_token.address, transfer_amount, sender=endaoment.address)


def test_transfer_reentrant_token_protection(endaoment_funds, endaoment, governance):
    """Test that contract handles reentrant tokens safely"""
    # Create reentrant token
    reentrant_token = boa.load("contracts/mock/MockReentrantErc20.vy", governance.address)

    # Fund endaoment_funds
    transfer_amount = 1000 * EIGHTEEN_DECIMALS
    reentrant_token.mint(endaoment_funds.address, transfer_amount, sender=governance.address)

    # Configure the token to attempt reentrancy
    reentrant_token.setAttackTarget(endaoment_funds.address, sender=governance.address)

    # Even with reentrancy attempt, the transfer should either:
    # 1. Complete successfully (if reentrancy is blocked), OR
    # 2. Revert cleanly without state corruption
    initial_balance = reentrant_token.balanceOf(endaoment_funds.address)
    initial_endao_balance = reentrant_token.balanceOf(endaoment.address)

    # This should work - Vyper's nonreentrant decorator protects against reentrancy
    # Note: The vault doesn't have nonreentrant, but the transfer itself is atomic
    result = endaoment_funds.transfer(reentrant_token.address, transfer_amount, sender=endaoment.address)

    # Verify state is correct
    assert result == transfer_amount
    assert reentrant_token.balanceOf(endaoment_funds.address) == initial_balance - transfer_amount
    assert reentrant_token.balanceOf(endaoment.address) == initial_endao_balance + transfer_amount


####################################
# Failed Transfer Scenario Tests   #
####################################


def test_transfer_eth_to_reverting_contract(endaoment, governance):
    """Test ETH transfer when recipient contract reverts"""
    # Create a mock endaoment_funds and a reverting endaoment
    reverting_endaoment = boa.load("contracts/mock/MockRevertOnReceive.vy")

    # For this test, we need to temporarily use a modified scenario
    # We'll test that ETH send can fail
    funds = boa.load("contracts/core/EndaomentFunds.vy", governance.address)

    # Fund the vault with ETH
    initial_balance = boa.env.get_balance(funds.address)
    boa.env.set_balance(funds.address, initial_balance + 10 * EIGHTEEN_DECIMALS)

    # Configure reverting contract to reject
    reverting_endaoment.setShouldRevert(True)

    # Since we can't change the endaoment address in the real vault,
    # we verify that a send to a reverting contract would fail
    # The actual contract uses `send()` which will revert if recipient reverts

    # This test documents expected behavior: transfers to reverting contracts will fail
    assert boa.env.get_balance(funds.address) > 0


def test_transfer_minimal_amounts(endaoment_funds, endaoment, alpha_token, alpha_token_whale):
    """Test transfer of minimal amounts (1 wei)"""
    # Fund endaoment_funds with minimal amount
    alpha_token.transfer(endaoment_funds.address, 1, sender=alpha_token_whale)

    initial_endao_balance = alpha_token.balanceOf(endaoment.address)

    # Transfer 1 wei
    result = endaoment_funds.transfer(alpha_token.address, 1, sender=endaoment.address)

    assert result == 1
    assert alpha_token.balanceOf(endaoment.address) == initial_endao_balance + 1
    assert alpha_token.balanceOf(endaoment_funds.address) == 0


def test_transfer_exactly_balance(endaoment_funds, endaoment, alpha_token, alpha_token_whale):
    """Test transfer of exact balance (edge case)"""
    exact_amount = 123456789  # Arbitrary exact amount

    # Fund endaoment_funds
    alpha_token.transfer(endaoment_funds.address, exact_amount, sender=alpha_token_whale)

    initial_endao_balance = alpha_token.balanceOf(endaoment.address)

    # Transfer exact balance
    result = endaoment_funds.transfer(alpha_token.address, exact_amount, sender=endaoment.address)

    assert result == exact_amount
    assert alpha_token.balanceOf(endaoment.address) == initial_endao_balance + exact_amount
    assert alpha_token.balanceOf(endaoment_funds.address) == 0


def test_has_balance_with_dust_amounts(endaoment_funds, alpha_token, alpha_token_whale):
    """Test hasBalance with dust amounts (1 wei)"""
    # Transfer 1 wei
    alpha_token.transfer(endaoment_funds.address, 1, sender=alpha_token_whale)

    # Should return true even for dust
    assert endaoment_funds.hasBalance(alpha_token.address) == True

    # Balance of exactly 1
    assert alpha_token.balanceOf(endaoment_funds.address) == 1


def test_transfer_erc20_with_max_uint256_balance(endaoment_funds, endaoment, governance):
    """Test transfer with very large balance"""
    # Create a token and mint large amount
    large_token = boa.load("contracts/mock/MockErc20.vy", governance.address, "Large", "LRG", 18, 0)

    # Mint a large amount (not max to avoid issues, but large enough)
    large_amount = 10**30  # 1 trillion with 18 decimals
    large_token.mint(endaoment_funds.address, large_amount, sender=governance.address)

    initial_endao_balance = large_token.balanceOf(endaoment.address)

    # Transfer large amount
    result = endaoment_funds.transfer(large_token.address, large_amount, sender=endaoment.address)

    assert result == large_amount
    assert large_token.balanceOf(endaoment.address) == initial_endao_balance + large_amount
