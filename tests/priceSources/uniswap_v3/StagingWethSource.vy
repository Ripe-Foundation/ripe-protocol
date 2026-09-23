# @version 0.4.3
# Test WETH price source. While the unchanged desk prices WETH for the V3
# source's confirmation callback, it witnesses the V3 source's staged state.

struct Config:
    pool: address
    fee: uint24
    quoteAsset: address
    assetIsToken0: bool
    assetDecimals: uint256
    quoteDecimals: uint256
    baseLiquidity: uint128
    twapWindow: uint32
    maxObservationAge: uint32
    minLiquidity: uint128

struct Pending:
    actionId: uint256
    config: Config

interface Source:
    def pendingUpdates(asset: address) -> Pending: view
    def feedConfig(asset: address) -> Config: view
    def hasPendingAction(aid: uint256) -> bool: view
    def hasPendingPriceFeedUpdate(asset: address) -> bool: view
    def hasPriceFeed(asset: address) -> bool: view
    def getPricedAssets() -> DynArray[address, 50]: view

WETH: immutable(address)
source: address
asset: address
beforeCount: uint256
reject: bool


@deploy
def __init__(weth: address):
    WETH = weth


@external
def watch(source: address, asset: address, beforeCount: uint256, reject: bool):
    self.source = source
    self.asset = asset
    self.beforeCount = beforeCount
    self.reject = reject


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return _asset == WETH


@external
def addPriceSnapshot(_asset: address) -> bool:
    return False


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> uint256:
    return 10 ** 18 if _asset == WETH else 0


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _priceDesk: address = empty(address)) -> (uint256, bool):
    if _asset != WETH:
        return 0, False
    if self.source != empty(address):
        p: Pending = staticcall Source(self.source).pendingUpdates(self.asset)
        if p.actionId != 0 and not staticcall Source(self.source).hasPendingAction(p.actionId):
            # staged: the candidate is the live config, the proposal is still
            # readable, the action is consumed and enumeration is unchanged
            assert not staticcall Source(self.source).hasPendingPriceFeedUpdate(self.asset)
            assert staticcall Source(self.source).hasPriceFeed(self.asset)
            live: Config = staticcall Source(self.source).feedConfig(self.asset)
            assert keccak256(abi_encode(live)) == keccak256(abi_encode(p.config))
            assets: DynArray[address, 50] = staticcall Source(self.source).getPricedAssets()
            assert len(assets) == self.beforeCount
            if self.beforeCount == 0:
                assert self.asset not in assets
            else:
                assert self.asset in assets
            if self.reject:
                return 0, True
    return 10 ** 18, True
