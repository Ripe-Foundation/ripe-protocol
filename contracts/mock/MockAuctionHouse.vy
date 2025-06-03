# @version 0.4.1

import contracts.modules.Addys as addys

# Storage for testing auction validation
canStartAuctionMap: public(HashMap[bytes32, bool])

struct FungAuctionConfig:
    liqUser: address
    vaultId: uint256
    asset: address

@external
def setCanStartAuction(_liqUser: address, _vaultId: uint256, _asset: address, _canStart: bool):
    """Set whether a specific auction can be started (for testing)"""
    key: bytes32 = keccak256(concat(convert(_liqUser, bytes32), convert(_vaultId, bytes32), convert(_asset, bytes32)))
    self.canStartAuctionMap[key] = _canStart

@view
@external
def canStartAuction(_liqUser: address, _vaultId: uint256, _asset: address) -> bool:
    """Check if auction can be started (mocked for testing)"""
    key: bytes32 = keccak256(concat(convert(_liqUser, bytes32), convert(_vaultId, bytes32), convert(_asset, bytes32)))
    return self.canStartAuctionMap[key]

@view
@internal
def _canStartAuction(_liqUser: address, _vaultId: uint256, _asset: address) -> bool:
    """Internal function to check if auction can be started"""
    key: bytes32 = keccak256(concat(convert(_liqUser, bytes32), convert(_vaultId, bytes32), convert(_asset, bytes32)))
    return self.canStartAuctionMap[key]

@external
def startAuction(_liqUser: address, _vaultId: uint256, _asset: address, _a: addys.Addys = empty(addys.Addys)) -> bool:
    """Mock start auction function"""
    return self._canStartAuction(_liqUser, _vaultId, _asset)

@external
def startManyAuctions(_auctions: DynArray[FungAuctionConfig, 20], _a: addys.Addys = empty(addys.Addys)) -> uint256:
    """Mock start many auctions function"""
    count: uint256 = 0
    for i: uint256 in range(20):
        if i >= len(_auctions):
            break
        auction: FungAuctionConfig = _auctions[i]
        if self._canStartAuction(auction.liqUser, auction.vaultId, auction.asset):
            count += 1
    return count

@external
def pauseAuction(_liqUser: address, _vaultId: uint256, _asset: address, _a: addys.Addys = empty(addys.Addys)) -> bool:
    """Mock pause auction function"""
    return True

@external
def pauseManyAuctions(_auctions: DynArray[FungAuctionConfig, 20], _a: addys.Addys = empty(addys.Addys)) -> uint256:
    """Mock pause many auctions function"""
    return len(_auctions) 