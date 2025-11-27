# @dev Mock contract that reverts when receiving ETH or during specific calls
# Used to test failure scenarios
# @version 0.4.3

shouldRevert: public(bool)
owner: public(address)


@deploy
def __init__():
    self.owner = msg.sender
    self.shouldRevert = False


@external
def setShouldRevert(_shouldRevert: bool):
    """Configure whether to revert on receive"""
    assert msg.sender == self.owner
    self.shouldRevert = _shouldRevert


@payable
@external
def __default__():
    """Revert when receiving ETH if configured"""
    if self.shouldRevert:
        raise "RevertOnReceive: rejecting ETH"


@external
def onERC721Received(_operator: address, _owner: address, _tokenId: uint256, _data: Bytes[1024]) -> bytes4:
    """Conditionally reject NFTs"""
    if self.shouldRevert:
        raise "RevertOnReceive: rejecting NFT"

    return method_id("onERC721Received(address,address,uint256,bytes)", output_type=bytes4)
