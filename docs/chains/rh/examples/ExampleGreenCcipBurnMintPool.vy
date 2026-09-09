# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026
#
# REVIEWED REFERENCE EXAMPLE — NOT PRODUCTION READY.
#
# This is a pure-Vyper example of a Chainlink CCIP v1.6.1-shaped burn/mint
# pool that can be registered in RipeHq as a GREEN minter. Vyper cannot inherit
# Chainlink's Solidity TokenPool or BurnMintTokenPoolAbstract, so this file
# reimplements the relevant ABI and behavior. It does not inherit Chainlink's
# audits, support commitments, or future fixes.
#
# The example intentionally:
# - implements the standard v1.6.1 pool execution and administration ABI used
#   by the selected EVM-to-EVM lane, subject to bounded Vyper dynamic arrays;
# - keeps the pool as the direct caller of GreenToken.mint() and requires the
#   Ripe token's bool-returning mint/burn calls to return True;
# - exposes only GREEN mint capability;
# - omits the broader Ripe Department pause/recovery surface; and
# - requires an RMN *proxy* address, not RMNRemote directly;
# - rejects an enabled zero-rate bucket, matching the current v1.6.1 API docs
#   despite the pinned source revision's looser validation; and
# - requires token.decimals() to succeed and match the constructor value.
#
# The RIPE pool should use the same reviewed logic but return False from
# canMintGreen() and True from canMintRipe(). Do not deploy this example until
# Chainlink confirms custom pure-Vyper pool eligibility, an independent audit
# closes, the exact EVM target is verified on both chains, and destination gas
# is measured through the real OffRamp/Router/RMN/RipeHq path.

# @version 0.4.3
# pragma evm-version shanghai


#######################
# External Interfaces #
#######################


interface BurnMintToken:
    def decimals() -> uint8: view
    def burn(_amount: uint256) -> bool: nonpayable
    def mint(_recipient: address, _amount: uint256) -> bool: nonpayable


interface CcipRouter:
    def getOnRamp(_remoteChainSelector: uint64) -> address: view
    def isOffRamp(_remoteChainSelector: uint64, _offRamp: address) -> bool: view


interface RmnProxy:
    def isCursed(_subject: bytes16) -> bool: view


##########################
# CCIP v1.6.1 ABI Structs #
##########################


# The bounds do not change canonical ABI selectors, but inputs above a bound
# revert during Vyper calldata decoding. For the intended EVM-to-EVM lane:
# addresses are abi.encode(address) (32 bytes), decimals metadata is 32 bytes,
# and offchainTokenData must remain <= 2048 bytes.
MAX_REMOTE_CHAINS: constant(uint256) = 8
MAX_REMOTE_POOLS_PER_CHAIN: constant(uint256) = 8
MAX_ALLOWLIST: constant(uint256) = 256
MAX_REMOTE_ADDRESS_BYTES: constant(uint256) = 64


struct LockOrBurnInV1:
    receiver: Bytes[64]
    remoteChainSelector: uint64
    originalSender: address
    amount: uint256
    localToken: address


struct LockOrBurnOutV1:
    destTokenAddress: Bytes[64]
    destPoolData: Bytes[32]


struct ReleaseOrMintInV1:
    originalSender: Bytes[64]
    remoteChainSelector: uint64
    receiver: address
    sourceDenominatedAmount: uint256
    localToken: address
    sourcePoolAddress: Bytes[64]
    sourcePoolData: Bytes[64]
    offchainTokenData: Bytes[2048]


struct ReleaseOrMintOutV1:
    destinationAmount: uint256


# Field order and widths match Chainlink RateLimiter.Config.
struct RateLimitConfig:
    isEnabled: bool
    capacity: uint128
    rate: uint128


# Field order and widths match Chainlink RateLimiter.TokenBucket.
struct TokenBucket:
    tokens: uint128
    lastUpdated: uint32
    isEnabled: bool
    capacity: uint128
    rate: uint128


# Field order matches Chainlink TokenPool.ChainUpdate.
struct ChainUpdate:
    remoteChainSelector: uint64
    remotePoolAddresses: DynArray[Bytes[64], 8]
    remoteTokenAddress: Bytes[64]
    outboundRateLimiterConfig: RateLimitConfig
    inboundRateLimiterConfig: RateLimitConfig


##########
# Events #
##########


# Event parameter types and indexing match TokenPool v1.6.1.
event LockedOrBurned:
    remoteChainSelector: indexed(uint64)
    token: address
    sender: address
    amount: uint256


event ReleasedOrMinted:
    remoteChainSelector: indexed(uint64)
    token: address
    sender: address
    recipient: address
    amount: uint256


event ChainAdded:
    remoteChainSelector: uint64
    remoteToken: Bytes[64]
    outboundRateLimiterConfig: RateLimitConfig
    inboundRateLimiterConfig: RateLimitConfig


event ChainConfigured:
    remoteChainSelector: uint64
    outboundRateLimiterConfig: RateLimitConfig
    inboundRateLimiterConfig: RateLimitConfig


event ChainRemoved:
    remoteChainSelector: uint64


event RemotePoolAdded:
    remoteChainSelector: indexed(uint64)
    remotePoolAddress: Bytes[64]


event RemotePoolRemoved:
    remoteChainSelector: indexed(uint64)
    remotePoolAddress: Bytes[64]


event AllowListAdd:
    sender: address


event AllowListRemove:
    sender: address


event RouterUpdated:
    oldRouter: address
    newRouter: address


event RateLimitAdminSet:
    rateLimitAdmin: address


event OutboundRateLimitConsumed:
    remoteChainSelector: indexed(uint64)
    token: address
    amount: uint256


event InboundRateLimitConsumed:
    remoteChainSelector: indexed(uint64)
    token: address
    amount: uint256


# RateLimiter.ConfigChanged is emitted by the Solidity library from each bucket
# update. Vyper cannot namespace events, but this has the same canonical topic.
event ConfigChanged:
    config: RateLimitConfig


event OwnershipTransferRequested:
    sender: indexed(address)
    recipient: indexed(address)


event OwnershipTransferred:
    sender: indexed(address)
    recipient: indexed(address)


#################
# Configuration #
#################


# bytes4(keccak256("CCIP_POOL_V1"))
CCIP_POOL_V1: constant(bytes4) = 0xaff2afbf
# XOR of the v1.6.1 IPoolV1 function selectors:
# lockOrBurn, releaseOrMint, isSupportedChain, and isSupportedToken.
IPOOL_V1_INTERFACE_ID: constant(bytes4) = 0x0e64dd29
ERC165_INTERFACE_ID: constant(bytes4) = 0x01ffc9a7
TYPE_AND_VERSION: constant(String[64]) = "ExampleGreenCcipBurnMintPool 0.2.0"

TOKEN: public(immutable(address))
TOKEN_DECIMALS: public(immutable(uint8))
RMN_PROXY: public(immutable(address))
ALLOWLIST_ENABLED: immutable(bool)

owner: public(address)
pendingOwner: public(address)
router: address
rateLimitAdmin: address

supportedChains: DynArray[uint64, 8]
isSupportedRemoteChain: HashMap[uint64, bool]
remoteToken: HashMap[uint64, Bytes[64]]
remotePools: HashMap[uint64, DynArray[Bytes[64], 8]]
isApprovedRemotePool: HashMap[uint64, HashMap[bytes32, bool]]

allowList: DynArray[address, 256]
isAllowListed: HashMap[address, bool]

outboundRateLimit: HashMap[uint64, TokenBucket]
inboundRateLimit: HashMap[uint64, TokenBucket]


@deploy
def __init__(
    _token: address,
    _tokenDecimals: uint8,
    _initialAllowList: DynArray[address, 256],
    _rmnProxy: address,
    _router: address,
    _owner: address,
):
    if _owner == empty(address):
        self._revertOwnerCannotBeZero()
    if empty(address) in [_token, _rmnProxy, _router]:
        self._revertZeroAddressNotAllowed()

    actualDecimals: uint8 = staticcall BurnMintToken(_token).decimals()
    if actualDecimals != _tokenDecimals:
        self._revertInvalidDecimalArgs(_tokenDecimals, actualDecimals)

    TOKEN = _token
    TOKEN_DECIMALS = _tokenDecimals
    RMN_PROXY = _rmnProxy
    ALLOWLIST_ENABLED = len(_initialAllowList) > 0

    self.router = _router
    self.owner = _owner
    log OwnershipTransferred(sender=empty(address), recipient=_owner)

    for sender: address in _initialAllowList:
        if sender != empty(address) and not self.isAllowListed[sender]:
            self.isAllowListed[sender] = True
            self.allowList.append(sender)
            log AllowListAdd(sender=sender)

############################
# RipeHq Capability Surface #
############################


@view
@external
def canMintGreen() -> bool:
    # RipeHq rechecks this view when governance grants GREEN mint permission.
    return True


@view
@external
def canMintRipe() -> bool:
    # Fail closed if governance accidentally tries to grant RIPE minting.
    return False


#########################
# CCIP Interface Surface #
#########################


@view
@external
def typeAndVersion() -> String[64]:
    return TYPE_AND_VERSION


@pure
@external
def supportsInterface(_interfaceId: bytes4) -> bool:
    return _interfaceId in [CCIP_POOL_V1, IPOOL_V1_INTERFACE_ID, ERC165_INTERFACE_ID]


@view
@external
def isSupportedToken(_token: address) -> bool:
    return _token == TOKEN


@view
@external
def getToken() -> address:
    return TOKEN


@view
@external
def getTokenDecimals() -> uint8:
    return TOKEN_DECIMALS


@view
@external
def getRmnProxy() -> address:
    return RMN_PROXY


@view
@external
def getRouter() -> address:
    return self.router


@view
@external
def getRateLimitAdmin() -> address:
    return self.rateLimitAdmin


@view
@external
def getAllowListEnabled() -> bool:
    return ALLOWLIST_ENABLED


@view
@external
def getAllowList() -> DynArray[address, 256]:
    return self.allowList


@view
@external
def getSupportedChains() -> DynArray[uint64, 8]:
    return self.supportedChains


@view
@external
def isSupportedChain(_remoteChainSelector: uint64) -> bool:
    return self.isSupportedRemoteChain[_remoteChainSelector]


@view
@external
def getRemotePools(_remoteChainSelector: uint64) -> DynArray[Bytes[64], 8]:
    return self.remotePools[_remoteChainSelector]


@view
@external
def isRemotePool(_remoteChainSelector: uint64, _remotePoolAddress: Bytes[64]) -> bool:
    return self.isApprovedRemotePool[_remoteChainSelector][keccak256(_remotePoolAddress)]


@view
@external
def getRemoteToken(_remoteChainSelector: uint64) -> Bytes[64]:
    # Chainlink returns empty bytes for an unconfigured chain.
    return self.remoteToken[_remoteChainSelector]


@view
@external
def getCurrentOutboundRateLimiterState(
    _remoteChainSelector: uint64,
) -> TokenBucket:
    return self._currentTokenBucketState(
        self.outboundRateLimit[_remoteChainSelector]
    )


@view
@external
def getCurrentInboundRateLimiterState(
    _remoteChainSelector: uint64,
) -> TokenBucket:
    return self._currentTokenBucketState(
        self.inboundRateLimit[_remoteChainSelector]
    )


@nonreentrant
@external
def lockOrBurn(_input: LockOrBurnInV1) -> LockOrBurnOutV1:
    """
    @notice Called by the local OnRamp after GREEN reaches this pool.
    @dev The pool burns its own GREEN balance and returns the remote token plus
         local-decimal metadata.
    """
    self._validateLockOrBurn(_input)
    assert extcall BurnMintToken(TOKEN).burn(_input.amount), "burn failed"

    log LockedOrBurned(
        remoteChainSelector=_input.remoteChainSelector,
        token=TOKEN,
        sender=msg.sender,
        amount=_input.amount,
    )

    return LockOrBurnOutV1(
        destTokenAddress=self.remoteToken[_input.remoteChainSelector],
        destPoolData=abi_encode(convert(TOKEN_DECIMALS, uint256)),
    )


@nonreentrant
@external
def releaseOrMint(_input: ReleaseOrMintInV1) -> ReleaseOrMintOutV1:
    """
    @notice Called by the local OffRamp for a validated remote-chain message.
    @dev This pool is the direct caller of GreenToken.mint(). GreenToken then
         asks RipeHq whether this exact pool may mint GREEN.
    """
    localAmount: uint256 = self._calculateLocalAmount(
        _input.sourceDenominatedAmount,
        _input.sourcePoolData,
    )
    self._validateReleaseOrMint(_input, localAmount)

    assert extcall BurnMintToken(TOKEN).mint(
        _input.receiver,
        localAmount,
    ), "mint failed"

    log ReleasedOrMinted(
        remoteChainSelector=_input.remoteChainSelector,
        token=TOKEN,
        sender=msg.sender,
        recipient=_input.receiver,
        amount=localAmount,
    )

    return ReleaseOrMintOutV1(destinationAmount=localAmount)


###################
# CCIP Validation #
###################


@internal
def _validateLockOrBurn(_input: LockOrBurnInV1):
    if _input.localToken != TOKEN:
        self._revertInvalidToken(_input.localToken)
    if staticcall RmnProxy(RMN_PROXY).isCursed(
        convert(_input.remoteChainSelector, bytes16)
    ):
        self._revertCursedByRMN()
    if ALLOWLIST_ENABLED and not self.isAllowListed[_input.originalSender]:
        self._revertSenderNotAllowed(_input.originalSender)
    self._onlyOnRamp(_input.remoteChainSelector)
    self._consumeOutboundRateLimit(_input.remoteChainSelector, _input.amount)


@internal
def _validateReleaseOrMint(
    _input: ReleaseOrMintInV1,
    _localAmount: uint256,
):
    if _input.localToken != TOKEN:
        self._revertInvalidToken(_input.localToken)
    if staticcall RmnProxy(RMN_PROXY).isCursed(
        convert(_input.remoteChainSelector, bytes16)
    ):
        self._revertCursedByRMN()
    self._onlyOffRamp(_input.remoteChainSelector)
    if not self.isApprovedRemotePool[_input.remoteChainSelector][
        keccak256(_input.sourcePoolAddress)
    ]:
        self._revertInvalidSourcePoolAddress(_input.sourcePoolAddress)
    self._consumeInboundRateLimit(_input.remoteChainSelector, _localAmount)


@view
@internal
def _onlyOnRamp(_remoteChainSelector: uint64):
    if not self.isSupportedRemoteChain[_remoteChainSelector]:
        self._revertChainNotAllowed(_remoteChainSelector)
    if msg.sender != staticcall CcipRouter(self.router).getOnRamp(
        _remoteChainSelector
    ):
        self._revertCallerIsNotARampOnRouter(msg.sender)


@view
@internal
def _onlyOffRamp(_remoteChainSelector: uint64):
    if not self.isSupportedRemoteChain[_remoteChainSelector]:
        self._revertChainNotAllowed(_remoteChainSelector)
    if not staticcall CcipRouter(self.router).isOffRamp(
        _remoteChainSelector,
        msg.sender,
    ):
        self._revertCallerIsNotARampOnRouter(msg.sender)


@view
@internal
def _calculateLocalAmount(
    _sourceAmount: uint256,
    _sourcePoolData: Bytes[64],
) -> uint256:
    remoteDecimals: uint8 = TOKEN_DECIMALS

    if len(_sourcePoolData) != 0:
        if len(_sourcePoolData) != 32:
            self._revertInvalidRemoteChainDecimals(_sourcePoolData)

        remoteDecimals256: uint256 = abi_decode(_sourcePoolData, uint256)
        if remoteDecimals256 > convert(max_value(uint8), uint256):
            self._revertInvalidRemoteChainDecimals(_sourcePoolData)
        remoteDecimals = convert(remoteDecimals256, uint8)

    if remoteDecimals == TOKEN_DECIMALS:
        return _sourceAmount

    if remoteDecimals > TOKEN_DECIMALS:
        downscale: uint8 = remoteDecimals - TOKEN_DECIMALS
        if downscale > 77:
            self._revertOverflowDetected(
                remoteDecimals,
                TOKEN_DECIMALS,
                _sourceAmount,
            )
        return _sourceAmount // 10 ** convert(downscale, uint256)

    upscale: uint8 = TOKEN_DECIMALS - remoteDecimals
    if upscale > 77:
        self._revertOverflowDetected(
            remoteDecimals,
            TOKEN_DECIMALS,
            _sourceAmount,
        )
    factor: uint256 = 10 ** convert(upscale, uint256)
    if _sourceAmount > max_value(uint256) // factor:
        self._revertOverflowDetected(
            remoteDecimals,
            TOKEN_DECIMALS,
            _sourceAmount,
        )
    return _sourceAmount * factor


#################
# Rate Limiting #
#################


@view
@internal
def _currentTokenBucketState(_bucket: TokenBucket) -> TokenBucket:
    available: uint256 = convert(_bucket.tokens, uint256)
    capacity: uint256 = convert(_bucket.capacity, uint256)
    elapsed: uint256 = block.timestamp - convert(_bucket.lastUpdated, uint256)

    if elapsed != 0 and available < capacity:
        missing: uint256 = capacity - available
        rate: uint256 = convert(_bucket.rate, uint256)
        if rate == 0:
            pass
        elif elapsed > missing // rate:
            available = capacity
        else:
            available += elapsed * rate

    _bucket.tokens = convert(available, uint128)
    _bucket.lastUpdated = convert(block.timestamp, uint32)
    return _bucket


@internal
def _consumeRateLimit(_bucket: TokenBucket, _amount: uint256) -> TokenBucket:
    if not _bucket.isEnabled or _amount == 0:
        return _bucket

    if (
        block.timestamp != convert(_bucket.lastUpdated, uint256)
        and _bucket.tokens > _bucket.capacity
    ):
        self._revertBucketOverfilled()

    current: TokenBucket = self._currentTokenBucketState(_bucket)
    capacity: uint256 = convert(current.capacity, uint256)
    available: uint256 = convert(current.tokens, uint256)

    if _amount > capacity:
        self._revertTokenMaxCapacityExceeded(capacity, _amount, TOKEN)
    if _amount > available:
        deficit: uint256 = _amount - available
        rate: uint256 = convert(current.rate, uint256)
        minWait: uint256 = (deficit + rate - 1) // rate
        self._revertTokenRateLimitReached(minWait, available, TOKEN)

    current.tokens = convert(available - _amount, uint128)
    current.lastUpdated = convert(block.timestamp, uint32)
    return current


@internal
def _consumeOutboundRateLimit(
    _remoteChainSelector: uint64,
    _amount: uint256,
):
    self.outboundRateLimit[_remoteChainSelector] = self._consumeRateLimit(
        self.outboundRateLimit[_remoteChainSelector],
        _amount,
    )
    log OutboundRateLimitConsumed(
        remoteChainSelector=_remoteChainSelector,
        token=TOKEN,
        amount=_amount,
    )


@internal
def _consumeInboundRateLimit(
    _remoteChainSelector: uint64,
    _amount: uint256,
):
    self.inboundRateLimit[_remoteChainSelector] = self._consumeRateLimit(
        self.inboundRateLimit[_remoteChainSelector],
        _amount,
    )
    log InboundRateLimitConsumed(
        remoteChainSelector=_remoteChainSelector,
        token=TOKEN,
        amount=_amount,
    )


@pure
@internal
def _validateRateLimitConfig(_config: RateLimitConfig):
    if _config.isEnabled:
        # The current v1.6.1 API docs require a nonzero enabled rate, although
        # the pinned source checks only rate > capacity. Reject zero because a
        # depleted zero-rate bucket can panic in the wait-time calculation.
        if _config.rate == 0 or _config.rate > _config.capacity:
            self._revertInvalidRateLimitRate(_config)
    elif _config.rate != 0 or _config.capacity != 0:
        self._revertDisabledNonZeroRateLimit(_config)


@internal
def _newRateLimit(_config: RateLimitConfig) -> TokenBucket:
    self._validateRateLimitConfig(_config)
    return TokenBucket(
        tokens=_config.capacity,
        lastUpdated=convert(block.timestamp, uint32),
        isEnabled=_config.isEnabled,
        capacity=_config.capacity,
        rate=_config.rate,
    )


@internal
def _setRateLimitConfig(
    _bucket: TokenBucket,
    _config: RateLimitConfig,
) -> TokenBucket:
    self._validateRateLimitConfig(_config)

    # Refill at the old rate, then clamp. Reconfiguration never restores
    # already-consumed capacity.
    current: TokenBucket = self._currentTokenBucketState(_bucket)
    tokens: uint128 = current.tokens
    if tokens > _config.capacity:
        tokens = _config.capacity

    current.tokens = tokens
    current.lastUpdated = convert(block.timestamp, uint32)
    current.isEnabled = _config.isEnabled
    current.capacity = _config.capacity
    current.rate = _config.rate

    log ConfigChanged(config=_config)
    return current


#######################
# Chain Configuration #
#######################


@external
def applyChainUpdates(
    _remoteChainSelectorsToRemove: DynArray[uint64, 8],
    _chainsToAdd: DynArray[ChainUpdate, 8],
):
    self._checkOwner()

    for selector: uint64 in _remoteChainSelectorsToRemove:
        self._removeChain(selector)

    for newChain: ChainUpdate in _chainsToAdd:
        if self.isSupportedRemoteChain[newChain.remoteChainSelector]:
            self._revertChainAlreadyExists(newChain.remoteChainSelector)
        if len(newChain.remoteTokenAddress) == 0:
            self._revertZeroAddressNotAllowed()

        self._validateRateLimitConfig(newChain.outboundRateLimiterConfig)
        self._validateRateLimitConfig(newChain.inboundRateLimiterConfig)

        self.isSupportedRemoteChain[newChain.remoteChainSelector] = True
        self.supportedChains.append(newChain.remoteChainSelector)
        self.remoteToken[newChain.remoteChainSelector] = newChain.remoteTokenAddress
        self.outboundRateLimit[newChain.remoteChainSelector] = self._newRateLimit(
            newChain.outboundRateLimiterConfig
        )
        self.inboundRateLimit[newChain.remoteChainSelector] = self._newRateLimit(
            newChain.inboundRateLimiterConfig
        )

        for pool: Bytes[64] in newChain.remotePoolAddresses:
            self._setRemotePool(newChain.remoteChainSelector, pool)

        log ChainAdded(
            remoteChainSelector=newChain.remoteChainSelector,
            remoteToken=newChain.remoteTokenAddress,
            outboundRateLimiterConfig=newChain.outboundRateLimiterConfig,
            inboundRateLimiterConfig=newChain.inboundRateLimiterConfig,
        )


@internal
def _removeChain(_remoteChainSelector: uint64):
    if not self.isSupportedRemoteChain[_remoteChainSelector]:
        self._revertNonExistentChain(_remoteChainSelector)

    for pool: Bytes[64] in self.remotePools[_remoteChainSelector]:
        self.isApprovedRemotePool[_remoteChainSelector][keccak256(pool)] = False

    self.remotePools[_remoteChainSelector] = empty(DynArray[Bytes[64], 8])
    self.remoteToken[_remoteChainSelector] = empty(Bytes[64])
    self.outboundRateLimit[_remoteChainSelector] = empty(TokenBucket)
    self.inboundRateLimit[_remoteChainSelector] = empty(TokenBucket)
    self.isSupportedRemoteChain[_remoteChainSelector] = False

    count: uint256 = len(self.supportedChains)
    for i: uint256 in range(MAX_REMOTE_CHAINS):
        if i < count and self.supportedChains[i] == _remoteChainSelector:
            last: uint256 = count - 1
            if i != last:
                self.supportedChains[i] = self.supportedChains[last]
            self.supportedChains.pop()
            break

    log ChainRemoved(remoteChainSelector=_remoteChainSelector)


@external
def addRemotePool(
    _remoteChainSelector: uint64,
    _remotePoolAddress: Bytes[64],
):
    self._checkOwner()
    if not self.isSupportedRemoteChain[_remoteChainSelector]:
        self._revertNonExistentChain(_remoteChainSelector)
    self._setRemotePool(_remoteChainSelector, _remotePoolAddress)


@internal
def _setRemotePool(
    _remoteChainSelector: uint64,
    _remotePoolAddress: Bytes[64],
):
    if len(_remotePoolAddress) == 0:
        self._revertZeroAddressNotAllowed()

    poolHash: bytes32 = keccak256(_remotePoolAddress)
    if self.isApprovedRemotePool[_remoteChainSelector][poolHash]:
        self._revertPoolAlreadyAdded(
            _remoteChainSelector,
            _remotePoolAddress,
        )

    self.isApprovedRemotePool[_remoteChainSelector][poolHash] = True
    self.remotePools[_remoteChainSelector].append(_remotePoolAddress)

    log RemotePoolAdded(
        remoteChainSelector=_remoteChainSelector,
        remotePoolAddress=_remotePoolAddress,
    )


@external
def removeRemotePool(
    _remoteChainSelector: uint64,
    _remotePoolAddress: Bytes[64],
):
    self._checkOwner()
    if not self.isSupportedRemoteChain[_remoteChainSelector]:
        self._revertNonExistentChain(_remoteChainSelector)

    poolHash: bytes32 = keccak256(_remotePoolAddress)
    if not self.isApprovedRemotePool[_remoteChainSelector][poolHash]:
        self._revertInvalidRemotePoolForChain(
            _remoteChainSelector,
            _remotePoolAddress,
        )

    self.isApprovedRemotePool[_remoteChainSelector][poolHash] = False
    count: uint256 = len(self.remotePools[_remoteChainSelector])
    for i: uint256 in range(MAX_REMOTE_POOLS_PER_CHAIN):
        if (
            i < count
            and keccak256(self.remotePools[_remoteChainSelector][i]) == poolHash
        ):
            last: uint256 = count - 1
            if i != last:
                self.remotePools[_remoteChainSelector][i] = self.remotePools[
                    _remoteChainSelector
                ][last]
            self.remotePools[_remoteChainSelector].pop()
            break

    # Removing a pool while messages are in flight can strand those messages.
    log RemotePoolRemoved(
        remoteChainSelector=_remoteChainSelector,
        remotePoolAddress=_remotePoolAddress,
    )


############################
# Rate-Limit Configuration #
############################


@external
def setChainRateLimiterConfig(
    _remoteChainSelector: uint64,
    _outboundConfig: RateLimitConfig,
    _inboundConfig: RateLimitConfig,
):
    self._checkRateLimitAdmin()
    self._setChainRateLimiterConfig(
        _remoteChainSelector,
        _outboundConfig,
        _inboundConfig,
    )


@external
def setChainRateLimiterConfigs(
    _remoteChainSelectors: DynArray[uint64, 8],
    _outboundConfigs: DynArray[RateLimitConfig, 8],
    _inboundConfigs: DynArray[RateLimitConfig, 8],
):
    self._checkRateLimitAdmin()
    if (
        len(_remoteChainSelectors) != len(_outboundConfigs)
        or len(_remoteChainSelectors) != len(_inboundConfigs)
    ):
        self._revertMismatchedArrayLengths()

    for i: uint256 in range(MAX_REMOTE_CHAINS):
        if i < len(_remoteChainSelectors):
            self._setChainRateLimiterConfig(
                _remoteChainSelectors[i],
                _outboundConfigs[i],
                _inboundConfigs[i],
            )


@internal
def _setChainRateLimiterConfig(
    _remoteChainSelector: uint64,
    _outboundConfig: RateLimitConfig,
    _inboundConfig: RateLimitConfig,
):
    if not self.isSupportedRemoteChain[_remoteChainSelector]:
        self._revertNonExistentChain(_remoteChainSelector)

    self.outboundRateLimit[_remoteChainSelector] = self._setRateLimitConfig(
        self.outboundRateLimit[_remoteChainSelector],
        _outboundConfig,
    )
    self.inboundRateLimit[_remoteChainSelector] = self._setRateLimitConfig(
        self.inboundRateLimit[_remoteChainSelector],
        _inboundConfig,
    )

    log ChainConfigured(
        remoteChainSelector=_remoteChainSelector,
        outboundRateLimiterConfig=_outboundConfig,
        inboundRateLimiterConfig=_inboundConfig,
    )


#######################
# Allowlist Management #
#######################


@external
def applyAllowListUpdates(
    _removes: DynArray[address, 256],
    _adds: DynArray[address, 256],
):
    self._checkOwner()
    if not ALLOWLIST_ENABLED:
        self._revertAllowListNotEnabled()

    for sender: address in _removes:
        if self.isAllowListed[sender]:
            self.isAllowListed[sender] = False
            count: uint256 = len(self.allowList)
            for i: uint256 in range(MAX_ALLOWLIST):
                if i < count and self.allowList[i] == sender:
                    last: uint256 = count - 1
                    if i != last:
                        self.allowList[i] = self.allowList[last]
                    self.allowList.pop()
                    break
            log AllowListRemove(sender=sender)

    for sender: address in _adds:
        if sender != empty(address) and not self.isAllowListed[sender]:
            self.isAllowListed[sender] = True
            self.allowList.append(sender)
            log AllowListAdd(sender=sender)


########################
# Owner / Configuration #
########################


@view
@internal
def _checkOwner():
    if msg.sender != self.owner:
        self._revertOnlyCallableByOwner()


@view
@internal
def _checkRateLimitAdmin():
    if msg.sender != self.owner and msg.sender != self.rateLimitAdmin:
        self._revertUnauthorized(msg.sender)


@external
def setRouter(_newRouter: address):
    self._checkOwner()
    if _newRouter == empty(address):
        self._revertZeroAddressNotAllowed()

    oldRouter: address = self.router
    self.router = _newRouter
    log RouterUpdated(oldRouter=oldRouter, newRouter=_newRouter)


@external
def setRateLimitAdmin(_newAdmin: address):
    self._checkOwner()
    self.rateLimitAdmin = _newAdmin
    log RateLimitAdminSet(rateLimitAdmin=_newAdmin)


@external
def transferOwnership(_newOwner: address):
    self._checkOwner()
    if _newOwner == self.owner:
        self._revertCannotTransferToSelf()

    # A zero pending owner cancels an in-progress transfer.
    self.pendingOwner = _newOwner
    log OwnershipTransferRequested(
        sender=self.owner,
        recipient=_newOwner,
    )


@external
def acceptOwnership():
    if msg.sender == empty(address) or msg.sender != self.pendingOwner:
        self._revertMustBeProposedOwner()

    previousOwner: address = self.owner
    self.owner = msg.sender
    self.pendingOwner = empty(address)

    log OwnershipTransferred(sender=previousOwner, recipient=msg.sender)


#####################################
# Chainlink-Shaped Custom Revert ABI #
#####################################


@pure
@internal
def _revertCallerIsNotARampOnRouter(_caller: address):
    raw_revert(concat(
        method_id("CallerIsNotARampOnRouter(address)", output_type=Bytes[4]),
        abi_encode(_caller),
    ))


@pure
@internal
def _revertZeroAddressNotAllowed():
    raw_revert(method_id("ZeroAddressNotAllowed()", output_type=Bytes[4]))


@pure
@internal
def _revertSenderNotAllowed(_sender: address):
    raw_revert(concat(
        method_id("SenderNotAllowed(address)", output_type=Bytes[4]),
        abi_encode(_sender),
    ))


@pure
@internal
def _revertAllowListNotEnabled():
    raw_revert(method_id("AllowListNotEnabled()", output_type=Bytes[4]))


@pure
@internal
def _revertNonExistentChain(_remoteChainSelector: uint64):
    raw_revert(concat(
        method_id("NonExistentChain(uint64)", output_type=Bytes[4]),
        abi_encode(_remoteChainSelector),
    ))


@pure
@internal
def _revertChainNotAllowed(_remoteChainSelector: uint64):
    raw_revert(concat(
        method_id("ChainNotAllowed(uint64)", output_type=Bytes[4]),
        abi_encode(_remoteChainSelector),
    ))


@pure
@internal
def _revertCursedByRMN():
    raw_revert(method_id("CursedByRMN()", output_type=Bytes[4]))


@pure
@internal
def _revertChainAlreadyExists(_remoteChainSelector: uint64):
    raw_revert(concat(
        method_id("ChainAlreadyExists(uint64)", output_type=Bytes[4]),
        abi_encode(_remoteChainSelector),
    ))


@pure
@internal
def _revertInvalidSourcePoolAddress(_sourcePoolAddress: Bytes[64]):
    raw_revert(concat(
        method_id("InvalidSourcePoolAddress(bytes)", output_type=Bytes[4]),
        abi_encode(_sourcePoolAddress),
    ))


@pure
@internal
def _revertInvalidToken(_token: address):
    raw_revert(concat(
        method_id("InvalidToken(address)", output_type=Bytes[4]),
        abi_encode(_token),
    ))


@pure
@internal
def _revertUnauthorized(_caller: address):
    raw_revert(concat(
        method_id("Unauthorized(address)", output_type=Bytes[4]),
        abi_encode(_caller),
    ))


@pure
@internal
def _revertOnlyCallableByOwner():
    raw_revert(method_id("OnlyCallableByOwner()", output_type=Bytes[4]))


@pure
@internal
def _revertOwnerCannotBeZero():
    raw_revert(method_id("OwnerCannotBeZero()", output_type=Bytes[4]))


@pure
@internal
def _revertMustBeProposedOwner():
    raw_revert(method_id("MustBeProposedOwner()", output_type=Bytes[4]))


@pure
@internal
def _revertCannotTransferToSelf():
    raw_revert(method_id("CannotTransferToSelf()", output_type=Bytes[4]))


@pure
@internal
def _revertPoolAlreadyAdded(
    _remoteChainSelector: uint64,
    _remotePoolAddress: Bytes[64],
):
    raw_revert(concat(
        method_id("PoolAlreadyAdded(uint64,bytes)", output_type=Bytes[4]),
        abi_encode(_remoteChainSelector, _remotePoolAddress),
    ))


@pure
@internal
def _revertInvalidRemotePoolForChain(
    _remoteChainSelector: uint64,
    _remotePoolAddress: Bytes[64],
):
    raw_revert(concat(
        method_id(
            "InvalidRemotePoolForChain(uint64,bytes)",
            output_type=Bytes[4],
        ),
        abi_encode(_remoteChainSelector, _remotePoolAddress),
    ))


@pure
@internal
def _revertInvalidRemoteChainDecimals(_sourcePoolData: Bytes[64]):
    raw_revert(concat(
        method_id("InvalidRemoteChainDecimals(bytes)", output_type=Bytes[4]),
        abi_encode(_sourcePoolData),
    ))


@pure
@internal
def _revertMismatchedArrayLengths():
    raw_revert(method_id("MismatchedArrayLengths()", output_type=Bytes[4]))


@pure
@internal
def _revertOverflowDetected(
    _remoteDecimals: uint8,
    _localDecimals: uint8,
    _remoteAmount: uint256,
):
    raw_revert(concat(
        method_id(
            "OverflowDetected(uint8,uint8,uint256)",
            output_type=Bytes[4],
        ),
        abi_encode(_remoteDecimals, _localDecimals, _remoteAmount),
    ))


@pure
@internal
def _revertInvalidDecimalArgs(_expected: uint8, _actual: uint8):
    raw_revert(concat(
        method_id("InvalidDecimalArgs(uint8,uint8)", output_type=Bytes[4]),
        abi_encode(_expected, _actual),
    ))


@pure
@internal
def _revertTokenMaxCapacityExceeded(
    _capacity: uint256,
    _requested: uint256,
    _tokenAddress: address,
):
    raw_revert(concat(
        method_id(
            "TokenMaxCapacityExceeded(uint256,uint256,address)",
            output_type=Bytes[4],
        ),
        abi_encode(_capacity, _requested, _tokenAddress),
    ))


@pure
@internal
def _revertBucketOverfilled():
    raw_revert(method_id("BucketOverfilled()", output_type=Bytes[4]))


@pure
@internal
def _revertTokenRateLimitReached(
    _minWaitInSeconds: uint256,
    _available: uint256,
    _tokenAddress: address,
):
    raw_revert(concat(
        method_id(
            "TokenRateLimitReached(uint256,uint256,address)",
            output_type=Bytes[4],
        ),
        abi_encode(_minWaitInSeconds, _available, _tokenAddress),
    ))


@pure
@internal
def _revertInvalidRateLimitRate(_config: RateLimitConfig):
    raw_revert(concat(
        method_id(
            "InvalidRateLimitRate((bool,uint128,uint128))",
            output_type=Bytes[4],
        ),
        abi_encode(_config),
    ))


@pure
@internal
def _revertDisabledNonZeroRateLimit(_config: RateLimitConfig):
    raw_revert(concat(
        method_id(
            "DisabledNonZeroRateLimit((bool,uint128,uint128))",
            output_type=Bytes[4],
        ),
        abi_encode(_config),
    ))
