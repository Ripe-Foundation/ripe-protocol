# @dev Simple implementation of ERC-721 token standard for testing
# @version 0.4.3

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    tokenId: indexed(uint256)

event Approval:
    owner: indexed(address)
    approved: indexed(address)
    tokenId: indexed(uint256)

event ApprovalForAll:
    owner: indexed(address)
    operator: indexed(address)
    approved: bool

name: public(String[32])
symbol: public(String[32])

ownerOf: public(HashMap[uint256, address])
balanceOf: public(HashMap[address, uint256])
getApproved: public(HashMap[uint256, address])
isApprovedForAll: public(HashMap[address, HashMap[address, bool]])

# governance
hq: public(address)

nextTokenId: uint256


@deploy
def __init__(_hq: address, _name: String[32], _symbol: String[32]):
    assert _hq != empty(address) # dev: cannot be 0x0
    self.hq = _hq
    self.name = _name
    self.symbol = _symbol
    self.nextTokenId = 1


@external
def approve(_approved: address, _tokenId: uint256):
    owner: address = self.ownerOf[_tokenId]
    assert owner != empty(address) # dev: token doesn't exist
    assert msg.sender == owner or self.isApprovedForAll[owner][msg.sender] # dev: not authorized

    self.getApproved[_tokenId] = _approved
    log Approval(owner=owner, approved=_approved, tokenId=_tokenId)


@external
def setApprovalForAll(_operator: address, _approved: bool):
    self.isApprovedForAll[msg.sender][_operator] = _approved
    log ApprovalForAll(owner=msg.sender, operator=_operator, approved=_approved)


@external
def transferFrom(_from: address, _to: address, _tokenId: uint256):
    assert self.ownerOf[_tokenId] == _from # dev: not owner
    assert _to != empty(address) # dev: invalid recipient

    # Check authorization
    assert msg.sender == _from or self.getApproved[_tokenId] == msg.sender or self.isApprovedForAll[_from][msg.sender] # dev: not authorized

    # Clear approval
    self.getApproved[_tokenId] = empty(address)

    # Update balances
    self.balanceOf[_from] -= 1
    self.balanceOf[_to] += 1

    # Update owner
    self.ownerOf[_tokenId] = _to

    log Transfer(sender=_from, receiver=_to, tokenId=_tokenId)


@external
def safeTransferFrom(_from: address, _to: address, _tokenId: uint256, _data: Bytes[1024]=b""):
    # For testing, we just call regular transferFrom
    # In production, this would check if recipient is a contract and call onERC721Received
    assert self.ownerOf[_tokenId] == _from # dev: not owner
    assert _to != empty(address) # dev: invalid recipient

    # Check authorization
    assert msg.sender == _from or self.getApproved[_tokenId] == msg.sender or self.isApprovedForAll[_from][msg.sender] # dev: not authorized

    # Clear approval
    self.getApproved[_tokenId] = empty(address)

    # Update balances
    self.balanceOf[_from] -= 1
    self.balanceOf[_to] += 1

    # Update owner
    self.ownerOf[_tokenId] = _to

    log Transfer(sender=_from, receiver=_to, tokenId=_tokenId)


@view
@external
def supportsInterface(_interfaceId: bytes4) -> bool:
    # ERC165 interface support
    # 0x80ac58cd is the ERC721 interface ID
    # 0x01ffc9a7 is the ERC165 interface ID
    return _interfaceId == 0x80ac58cd or _interfaceId == 0x01ffc9a7


@external
def mint(_to: address) -> uint256:
    """
    @dev Mint a new NFT and assign it to an account.
    @param _to The account that will receive the NFT.
    @return The token ID of the minted NFT.
    """
    assert msg.sender == self.hq # dev: not authorized
    assert _to != empty(address) # dev: invalid recipient

    tokenId: uint256 = self.nextTokenId
    self.nextTokenId += 1

    self.ownerOf[tokenId] = _to
    self.balanceOf[_to] += 1

    log Transfer(sender=empty(address), receiver=_to, tokenId=tokenId)
    return tokenId


@external
def burn(_tokenId: uint256):
    """
    @dev Burn an NFT.
    @param _tokenId The token ID to burn.
    """
    owner: address = self.ownerOf[_tokenId]
    assert owner != empty(address) # dev: token doesn't exist
    assert msg.sender == owner or msg.sender == self.hq # dev: not authorized

    # Clear approval
    self.getApproved[_tokenId] = empty(address)

    # Update balance
    self.balanceOf[owner] -= 1

    # Clear owner
    self.ownerOf[_tokenId] = empty(address)

    log Transfer(sender=owner, receiver=empty(address), tokenId=_tokenId)
