# @version 0.4.3
# A test anchor witnesses staged state while the unchanged desk calls the source.
struct FeedParams:
    pool: address
    twapWindowSeconds: uint32
    minCurrentLiquidity: uint128
    minHarmonicLiquidity: uint128
    maxObservationAgeSeconds: uint32
    quoteStaleTime: uint256
struct Config:
    params: FeedParams
    assetIsToken0: bool
    assetDecimals: uint8
    fee: uint24
struct Pending:
    actionId: uint256
    kind: uint256
    config: Config
interface Source:
    def getPendingFeed(asset: address) -> Pending: view
    def getFeedConfig(asset: address) -> Config: view
    def getBoundAssetDecimals(asset: address) -> (bool,uint8): view
    def hasPendingAction(aid: uint256) -> bool: view
    def hasPendingPriceFeedUpdate(asset: address) -> bool: view
    def hasPriceFeed(asset: address) -> bool: view
    def getPricedAssets() -> DynArray[address,50]: view
source: address
asset: address
beforeCount: uint256
reject: bool
@external
def watch(source: address, asset: address, beforeCount: uint256, reject: bool):
    self.source=source
    self.asset=asset
    self.beforeCount=beforeCount
    self.reject=reject
@view
@external
def decimals() -> uint8:
    return 8
@view
@external
def latestRoundData() -> (uint80,int256,uint256,uint256,uint80):
    if self.source != empty(address):
        p: Pending = staticcall Source(self.source).getPendingFeed(self.asset)
        if p.actionId != 0 and not staticcall Source(self.source).hasPendingAction(p.actionId):
            assert staticcall Source(self.source).hasPendingPriceFeedUpdate(self.asset)
            assert staticcall Source(self.source).hasPriceFeed(self.asset)
            live: Config = staticcall Source(self.source).getFeedConfig(self.asset)
            assert keccak256(abi_encode(live)) == keccak256(abi_encode(p.config))
            bound: bool = False
            decimals: uint8 = 0
            bound, decimals = staticcall Source(self.source).getBoundAssetDecimals(self.asset)
            assert bound and decimals == p.config.assetDecimals
            assets: DynArray[address,50] = staticcall Source(self.source).getPricedAssets()
            assert len(assets) == self.beforeCount
            if p.kind == 1:
                assert self.asset not in assets
            else:
                assert self.asset in assets
            if self.reject:
                return 1,0,0,block.timestamp,1
    return 1,100000000,0,block.timestamp,1
