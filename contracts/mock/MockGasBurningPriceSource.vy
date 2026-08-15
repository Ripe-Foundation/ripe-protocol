# @version 0.4.3

# Test-only hostile PriceSource. Each external operation performs enough
# non-trivial work to exhaust any realistic forwarded allowance.

BURN_ITERATIONS: constant(uint256) = 1_000_000

price: public(uint256)
hasFeed: public(bool)
priceWorkIterations: public(uint256)
hasFeedWorkIterations: public(uint256)
snapshotWorkIterations: public(uint256)
exhaustPriceAllowance: public(bool)
exhaustHasFeedAllowance: public(bool)
exhaustSnapshotAllowance: public(bool)
priceBurnAsset: public(address)


@external
def configure(
    _price: uint256,
    _hasFeed: bool,
    _priceWorkIterations: uint256,
    _hasFeedWorkIterations: uint256,
    _snapshotWorkIterations: uint256,
    _exhaustPriceAllowance: bool,
    _exhaustHasFeedAllowance: bool,
    _exhaustSnapshotAllowance: bool,
):
    assert _priceWorkIterations <= BURN_ITERATIONS
    assert _hasFeedWorkIterations <= BURN_ITERATIONS
    assert _snapshotWorkIterations <= BURN_ITERATIONS
    self.price = _price
    self.hasFeed = _hasFeed
    self.priceWorkIterations = _priceWorkIterations
    self.hasFeedWorkIterations = _hasFeedWorkIterations
    self.snapshotWorkIterations = _snapshotWorkIterations
    self.exhaustPriceAllowance = _exhaustPriceAllowance
    self.exhaustHasFeedAllowance = _exhaustHasFeedAllowance
    self.exhaustSnapshotAllowance = _exhaustSnapshotAllowance


@external
def setPriceBurnAsset(_asset: address):
    self.priceBurnAsset = _asset


@view
@internal
def _burn(_workIterations: uint256) -> uint256:
    checksum: uint256 = 0
    for i: uint256 in range(BURN_ITERATIONS):
        if i == _workIterations:
            break
        checksum = unsafe_add(checksum, i)
    return checksum


@view
@external
def getPriceAndHasFeed(
    _asset: address,
    _staleTime: uint256 = 0,
    _priceDesk: address = empty(address),
) -> (uint256, bool):
    shouldExhaust: bool = self.exhaustPriceAllowance and (
        self.priceBurnAsset == empty(address) or self.priceBurnAsset == _asset
    )
    workIterations: uint256 = self.priceWorkIterations
    if self.exhaustPriceAllowance and not shouldExhaust:
        workIterations = 0
    checksum: uint256 = self._burn(workIterations)
    if shouldExhaust:
        assert checksum == max_value(uint256)
    return self.price, self.hasFeed


@view
@external
def hasPriceFeed(_asset: address) -> bool:
    checksum: uint256 = self._burn(self.hasFeedWorkIterations)
    if self.exhaustHasFeedAllowance:
        assert checksum == max_value(uint256)
    return self.hasFeed


@external
def addPriceSnapshot(_asset: address) -> bool:
    checksum: uint256 = self._burn(self.snapshotWorkIterations)
    if self.exhaustSnapshotAllowance:
        assert checksum == max_value(uint256)
    return True
