# @version 0.4.1

implements: PriceSource

initializes: gov
initializes: psd
initializes: td

exports: gov.__interface__
exports: psd.__interface__
exports: td.__interface__

import contracts.modules.LocalGov as gov
import contracts.modules.PriceSourceData as psd
import contracts.modules.TimeDelay as td
import interfaces.PriceSource as PriceSource

interface PriceDesk:
    def MIN_PRICE_SOURCE_CHANGE_DELAY() -> uint256: view
    def MAX_PRICE_SOURCE_CHANGE_DELAY() -> uint256: view

interface ChainlinkFeed:
    def latestRoundData() -> ChainlinkRound: view
    def decimals() -> uint8: view 

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

struct ChainlinkRound:
    roundId: uint80
    answer: int256
    startedAt: uint256
    updatedAt: uint256
    answeredInRound: uint80

struct ChainlinkConfig:
    feed: address
    decimals: uint256
    needsEthToUsd: bool
    needsBtcToUsd: bool

struct PendingChainlinkConfig:
    actionId: uint256
    config: ChainlinkConfig

event NewChainlinkFeedPending:
    asset: indexed(address)
    feed: indexed(address)
    needsEthToUsd: bool
    needsBtcToUsd: bool
    confirmationBlock: uint256

event NewChainlinkFeedAdded:
    asset: indexed(address)
    feed: indexed(address)
    needsEthToUsd: bool
    needsBtcToUsd: bool

event NewChainlinkFeedCancelled:
    asset: indexed(address)
    feed: indexed(address)

event ChainlinkFeedUpdatePending:
    asset: indexed(address)
    feed: indexed(address)
    needsEthToUsd: bool
    needsBtcToUsd: bool
    confirmationBlock: uint256
    oldFeed: indexed(address)

event ChainlinkFeedUpdated:
    asset: indexed(address)
    feed: indexed(address)
    needsEthToUsd: bool
    needsBtcToUsd: bool
    oldFeed: indexed(address)

event ChainlinkFeedUpdateCancelled:
    asset: indexed(address)
    feed: indexed(address)
    oldFeed: indexed(address)

event DisableChainlinkFeedPending:
    asset: indexed(address)
    feed: indexed(address)
    confirmationBlock: uint256

event ChainlinkFeedDisabled:
    asset: indexed(address)
    feed: indexed(address)

event DisableChainlinkFeedCancelled:
    asset: indexed(address)
    feed: indexed(address)

# core config
feedConfig: public(HashMap[address, ChainlinkConfig]) # asset -> config

# pending changes
pendingUpdates: public(HashMap[address, PendingChainlinkConfig]) # asset -> config

# default assets
WETH: public(immutable(address))
ETH: public(immutable(address))
BTC: public(immutable(address))

ADDY_REGISTRY: public(immutable(address))
NORMALIZED_DECIMALS: constant(uint256) = 18
PRICE_DESK_ID: constant(uint256) = 7 # TODO: make sure this is correct


@deploy
def __init__(
    _wethAddr: address,
    _ethAddr: address,
    _btcAddr: address,
    _ethUsdFeed: address,
    _btcUsdFeed: address,
    _addyRegistry: address,
):
    assert empty(address) not in [_wethAddr, _ethAddr, _btcAddr, _addyRegistry] # dev: invalid addrs
    ADDY_REGISTRY = _addyRegistry

    # initialize modules
    gov.__init__(empty(address), _addyRegistry, 0, 0)
    psd.__init__()
    pd: address = staticcall AddyRegistry(ADDY_REGISTRY).getAddy(PRICE_DESK_ID)
    td.__init__(staticcall PriceDesk(pd).MIN_PRICE_SOURCE_CHANGE_DELAY(), staticcall PriceDesk(pd).MAX_PRICE_SOURCE_CHANGE_DELAY(), False)

    # set default assets
    WETH = _wethAddr
    ETH = _ethAddr
    BTC = _btcAddr

    # set default feeds
    if _ethUsdFeed != empty(address):
        assert self._setDefaultFeedOnDeploy(_ethAddr, _ethUsdFeed)
        assert self._setDefaultFeedOnDeploy(_wethAddr, _ethUsdFeed)
    if _btcUsdFeed != empty(address):
        assert self._setDefaultFeedOnDeploy(_btcAddr, _btcUsdFeed)


# set default feeds


@internal
def _setDefaultFeedOnDeploy(_asset: address, _newFeed: address) -> bool:
    decimals: uint256 = convert(staticcall ChainlinkFeed(_newFeed).decimals(), uint256)
    if not self._isValidNewFeed(_asset, _newFeed, decimals, False, False):
        return False
    self.feedConfig[_asset] = ChainlinkConfig(
        feed=_newFeed,
        decimals=decimals,
        needsEthToUsd=False,
        needsBtcToUsd=False,
    )
    psd._addPricedAsset(_asset)
    return True


########
# Core #
########


# get price


@view
@external
def getPrice(_asset: address, _staleTime: uint256 = 0, _oracleRegistry: address = empty(address)) -> uint256:
    config: ChainlinkConfig = self.feedConfig[_asset]
    if config.feed == empty(address):
        return 0
    return self._getPrice(config.feed, config.decimals, config.needsEthToUsd, config.needsBtcToUsd, _staleTime)


@view
@external
def getPriceAndHasFeed(_asset: address, _staleTime: uint256 = 0, _oracleRegistry: address = empty(address)) -> (uint256, bool):
    config: ChainlinkConfig = self.feedConfig[_asset]
    if config.feed == empty(address):
        return 0, False
    return self._getPrice(config.feed, config.decimals, config.needsEthToUsd, config.needsBtcToUsd, _staleTime), True


@view
@internal
def _getPrice(
    _feed: address, 
    _decimals: uint256,
    _needsEthToUsd: bool,
    _needsBtcToUsd: bool,
    _staleTime: uint256,
) -> uint256:
    price: uint256 = self._getChainlinkData(_feed, _decimals, _staleTime)
    if price == 0:
        return 0

    # if price needs ETH -> USD conversion
    if _needsEthToUsd:
        ethConfig: ChainlinkConfig = self.feedConfig[ETH]
        ethUsdPrice: uint256 = self._getChainlinkData(ethConfig.feed, ethConfig.decimals, _staleTime)
        price = price * ethUsdPrice // (10 ** NORMALIZED_DECIMALS)

    # if price needs BTC -> USD conversion
    elif _needsBtcToUsd:
        btcConfig: ChainlinkConfig = self.feedConfig[BTC]
        btcUsdPrice: uint256 = self._getChainlinkData(btcConfig.feed, btcConfig.decimals, _staleTime)
        price = price * btcUsdPrice // (10 ** NORMALIZED_DECIMALS)

    return price


# chainlink data


@view
@external
def getChainlinkData(_feed: address, _decimals: uint256, _staleTime: uint256 = 0) -> uint256:
    return self._getChainlinkData(_feed, _decimals, _staleTime)


@view
@internal
def _getChainlinkData(_feed: address, _decimals: uint256, _staleTime: uint256) -> uint256:
    oracle: ChainlinkRound = staticcall ChainlinkFeed(_feed).latestRoundData()

    # oracle has no price
    if oracle.answer <= 0:
        return 0

    # bad decimals
    if _decimals > NORMALIZED_DECIMALS:
        return 0

    # price is too stale
    if _staleTime != 0 and block.timestamp - oracle.updatedAt > _staleTime:
        return 0

    # handle decimal normalization
    price: uint256 = convert(oracle.answer, uint256)
    decimals: uint256 = _decimals
    if decimals < NORMALIZED_DECIMALS:
        decimals = NORMALIZED_DECIMALS - decimals
        price = price * (10 ** decimals)

    return price


# utilities


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self.feedConfig[_asset].feed != empty(address)


@view
@external
def hasPendingPriceFeedUpdate(_asset: address) -> bool:
    return td._hasPendingAction(self.pendingUpdates[_asset].actionId)


################
# Add New Feed #
################


# validation


@view
@external
def isValidNewFeed(_asset: address, _newFeed: address, _decimals: uint256, _needsEthToUsd: bool, _needsBtcToUsd: bool) -> bool:
    return self._isValidNewFeed(_asset, _newFeed, _decimals, _needsEthToUsd, _needsBtcToUsd)


@view
@internal
def _isValidNewFeed(_asset: address, _newFeed: address, _decimals: uint256, _needsEthToUsd: bool, _needsBtcToUsd: bool) -> bool:
    if psd.indexOfAsset[_asset] != 0 or self.feedConfig[_asset].feed != empty(address): # use the `updatePriceFeed` function instead
        return False
    return self._isValidFeedConfig(_asset, _newFeed, _decimals, _needsEthToUsd, _needsBtcToUsd)


# initiate


@external
def addNewPriceFeed(
    _asset: address, 
    _newFeed: address, 
    _needsEthToUsd: bool = False,
    _needsBtcToUsd: bool = False,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    # validation
    decimals: uint256 = convert(staticcall ChainlinkFeed(_newFeed).decimals(), uint256)
    assert self._isValidNewFeed(_asset, _newFeed, decimals, _needsEthToUsd, _needsBtcToUsd) # dev: invalid feed

    # set to pending state
    aid: uint256 = td._initiateAction()
    self.pendingUpdates[_asset] = PendingChainlinkConfig(
        actionId=aid,
        config=ChainlinkConfig(
            feed=_newFeed,
            decimals=decimals,
            needsEthToUsd=_needsEthToUsd,
            needsBtcToUsd=_needsBtcToUsd,
        ),
    )

    log NewChainlinkFeedPending(asset=_asset, feed=_newFeed, needsEthToUsd=_needsEthToUsd, needsBtcToUsd=_needsBtcToUsd, confirmationBlock=td._getConfirmationBlock(aid))
    return True


# confirm


@external
def confirmNewPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    # validate again
    d: PendingChainlinkConfig = self.pendingUpdates[_asset]
    if not self._isValidNewFeed(_asset, d.config.feed, d.config.decimals, d.config.needsEthToUsd, d.config.needsBtcToUsd):
        self._cancelNewPendingPriceFeed(_asset, d.actionId)
        return False

    # save new feed config
    assert td._confirmAction(d.actionId) # dev: time delay not reached
    self.feedConfig[_asset] = d.config
    self.pendingUpdates[_asset] = empty(PendingChainlinkConfig)
    psd._addPricedAsset(_asset)

    log NewChainlinkFeedAdded(asset=_asset, feed=d.config.feed, needsEthToUsd=d.config.needsEthToUsd, needsBtcToUsd=d.config.needsBtcToUsd)
    return True


# cancel


@external
def cancelNewPendingPriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    d: PendingChainlinkConfig = self.pendingUpdates[_asset]
    self._cancelNewPendingPriceFeed(_asset, d.actionId)
    log NewChainlinkFeedCancelled(asset=_asset, feed=d.config.feed)
    return True


@internal
def _cancelNewPendingPriceFeed(_asset: address, _aid: uint256):
    assert td._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingChainlinkConfig)


###############
# Update Feed #
###############


# validation


@view
@external
def isValidUpdateFeed(_asset: address, _newFeed: address, _decimals: uint256, _needsEthToUsd: bool, _needsBtcToUsd: bool) -> bool:
    return self._isValidUpdateFeed(_asset, _newFeed, self.feedConfig[_asset].feed, _decimals, _needsEthToUsd, _needsBtcToUsd)


@view
@internal
def _isValidUpdateFeed(_asset: address, _newFeed: address, _oldFeed: address, _decimals: uint256, _needsEthToUsd: bool, _needsBtcToUsd: bool) -> bool:
    if _newFeed == _oldFeed:
        return False
    if psd.indexOfAsset[_asset] == 0 or _oldFeed == empty(address): # use the `addNewPriceFeed` function instead
        return False
    return self._isValidFeedConfig(_asset, _newFeed, _decimals, _needsEthToUsd, _needsBtcToUsd)


@view
@internal
def _isValidFeedConfig(
    _asset: address, 
    _feed: address,
    _decimals: uint256,
    _needsEthToUsd: bool,
    _needsBtcToUsd: bool,
) -> bool:
    if empty(address) in [_asset, _feed]:
        return False
    if _needsEthToUsd and _needsBtcToUsd:
        return False
    return self._getPrice(_feed, _decimals, _needsEthToUsd, _needsBtcToUsd, 0) != 0


# initiate


@external
def updatePriceFeed(
    _asset: address, 
    _newFeed: address, 
    _needsEthToUsd: bool = False,
    _needsBtcToUsd: bool = False,
) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    # validation
    oldFeed: address = self.feedConfig[_asset].feed
    decimals: uint256 = convert(staticcall ChainlinkFeed(_newFeed).decimals(), uint256)
    assert self._isValidUpdateFeed(_asset, _newFeed, oldFeed, decimals, _needsEthToUsd, _needsBtcToUsd) # dev: invalid feed

    # set to pending state
    aid: uint256 = td._initiateAction()
    self.pendingUpdates[_asset] = PendingChainlinkConfig(
        actionId=aid,
        config=ChainlinkConfig(
            feed=_newFeed,
            decimals=decimals,
            needsEthToUsd=_needsEthToUsd,
            needsBtcToUsd=_needsBtcToUsd,
        ),
    )
    log ChainlinkFeedUpdatePending(asset=_asset, feed=_newFeed, needsEthToUsd=_needsEthToUsd, needsBtcToUsd=_needsBtcToUsd, confirmationBlock=td._getConfirmationBlock(aid), oldFeed=oldFeed)
    return True


# confirm


@external
def confirmPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    # validate again
    oldFeed: address = self.feedConfig[_asset].feed
    d: PendingChainlinkConfig = self.pendingUpdates[_asset]
    if not self._isValidUpdateFeed(_asset, d.config.feed, oldFeed, d.config.decimals, d.config.needsEthToUsd, d.config.needsBtcToUsd):
        self._cancelPriceFeedUpdate(_asset, d.actionId)
        return False

    # save new feed config
    assert td._confirmAction(d.actionId) # dev: time delay not reached
    self.feedConfig[_asset] = d.config
    self.pendingUpdates[_asset] = empty(PendingChainlinkConfig)

    log ChainlinkFeedUpdated(asset=_asset, feed=d.config.feed, needsEthToUsd=d.config.needsEthToUsd, needsBtcToUsd=d.config.needsBtcToUsd, oldFeed=oldFeed)
    return True


# cancel


@external
def cancelPriceFeedUpdate(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    d: PendingChainlinkConfig = self.pendingUpdates[_asset]
    self._cancelPriceFeedUpdate(_asset, d.actionId)
    log ChainlinkFeedUpdateCancelled(asset=_asset, feed=d.config.feed, oldFeed=self.feedConfig[_asset].feed)
    return True


@internal
def _cancelPriceFeedUpdate(_asset: address, _aid: uint256):
    assert td._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingChainlinkConfig)


################
# Disable Feed #
################


# validation


@view
@internal
def _isValidDisablePriceFeed(_asset: address, _oldFeed: address) -> bool:
    if psd.indexOfAsset[_asset] == 0:
        return False
    if _oldFeed == empty(address):
        return False
    return _asset not in [ETH, WETH, BTC]


# initiate


@external
def disablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    # validation
    oldFeed: address = self.feedConfig[_asset].feed
    assert self._isValidDisablePriceFeed(_asset, oldFeed) # dev: invalid asset

    # set to pending state
    aid: uint256 = td._initiateAction()
    self.pendingUpdates[_asset] = PendingChainlinkConfig(
        actionId=aid,
        config=empty(ChainlinkConfig),
    )

    log DisableChainlinkFeedPending(asset=_asset, feed=oldFeed, confirmationBlock=td._getConfirmationBlock(aid))
    return True


# confirm


@external
def confirmDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms

    # validate again
    oldFeed: address = self.feedConfig[_asset].feed
    d: PendingChainlinkConfig = self.pendingUpdates[_asset]
    if not self._isValidDisablePriceFeed(_asset, oldFeed):
        self._cancelDisablePriceFeed(_asset, d.actionId)
        return False

    # disable feed
    assert td._confirmAction(d.actionId) # dev: time delay not reached
    self.feedConfig[_asset] = empty(ChainlinkConfig)
    self.pendingUpdates[_asset] = empty(PendingChainlinkConfig)
    psd._removePricedAsset(_asset)
    
    log ChainlinkFeedDisabled(asset=_asset, feed=oldFeed)
    return True


# cancel


@external
def cancelDisablePriceFeed(_asset: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    self._cancelDisablePriceFeed(_asset, self.pendingUpdates[_asset].actionId)
    log DisableChainlinkFeedCancelled(asset=_asset, feed=self.feedConfig[_asset].feed)
    return True


@internal
def _cancelDisablePriceFeed(_asset: address, _aid: uint256):
    assert td._cancelAction(_aid) # dev: cannot cancel action
    self.pendingUpdates[_asset] = empty(PendingChainlinkConfig)


################
# Delay Config #
################


@view
@external
def priceFeedChangeDelay() -> uint256:
    return td.actionDelay


@external
def setPriceFeedChangeDelay(_numBlocks: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert td._setActionDelay(_numBlocks) # dev: invalid delay
    return True


@external
def setPriceFeedChangeDelayToMin() -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    assert td._setActionDelay(td.MIN_ACTION_DELAY) # dev: invalid delay
    return True


##########
# Config #
##########


@external
def setPriceSourceId(_priceSourceId: uint256) -> bool:
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(PRICE_DESK_ID) # dev: no perms
    return psd._setPriceSourceId(_priceSourceId)