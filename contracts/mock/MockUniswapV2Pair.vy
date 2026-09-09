# @version 0.4.3

interface MockToken:
    def balanceOf(_account: address) -> uint256: view
    def transfer(_to: address, _amount: uint256) -> bool: nonpayable


interface FlashCallee:
    def uniswapV2Call(
        _sender: address,
        _amount0Out: uint256,
        _amount1Out: uint256,
        _data: Bytes[256],
    ): nonpayable

pairFactory: address
pairToken0: address
pairToken1: address
reserve0: public(uint256)
reserve1: public(uint256)
pairTimestamp: public(uint256)
price0Cumulative: uint256
price1Cumulative: uint256
supply: uint256
shouldRevert: public(bool)
reserveResponseMode: public(uint256)
wordResponseModes: HashMap[uint256, uint256]

UINT32_MODULUS: constant(uint256) = 2 ** 32
UQ112: constant(uint256) = 2 ** 112
MAX_UINT112: constant(uint256) = 2 ** 112 - 1


@external
def configureIdentity(_factory: address, _token0: address, _token1: address):
    self.pairFactory = _factory
    self.pairToken0 = _token0
    self.pairToken1 = _token1


@external
def configureState(
    _reserve0: uint256,
    _reserve1: uint256,
    _pairTimestamp: uint256,
    _price0CumulativeLast: uint256,
    _price1CumulativeLast: uint256,
    _totalSupply: uint256,
):
    self.reserve0 = _reserve0
    self.reserve1 = _reserve1
    self.pairTimestamp = _pairTimestamp
    self.price0Cumulative = _price0CumulativeLast
    self.price1Cumulative = _price1CumulativeLast
    self.supply = _totalSupply


@internal
def _accumulate():
    currentTimestamp: uint256 = block.timestamp % UINT32_MODULUS
    elapsed: uint256 = 0
    if currentTimestamp >= self.pairTimestamp:
        elapsed = currentTimestamp - self.pairTimestamp
    else:
        elapsed = UINT32_MODULUS - self.pairTimestamp + currentTimestamp

    if elapsed != 0 and self.reserve0 != 0 and self.reserve1 != 0:
        price0: uint256 = self.reserve1 * UQ112 // self.reserve0
        price1: uint256 = self.reserve0 * UQ112 // self.reserve1
        self.price0Cumulative = unsafe_add(self.price0Cumulative, unsafe_mul(price0, elapsed))
        self.price1Cumulative = unsafe_add(self.price1Cumulative, unsafe_mul(price1, elapsed))
    self.pairTimestamp = currentTimestamp


@internal
def _update(_balance0: uint256, _balance1: uint256):
    assert _balance0 <= MAX_UINT112 and _balance1 <= MAX_UINT112
    self._accumulate()
    self.reserve0 = _balance0
    self.reserve1 = _balance1


@external
def sync():
    self._update(
        staticcall MockToken(self.pairToken0).balanceOf(self),
        staticcall MockToken(self.pairToken1).balanceOf(self),
    )


@external
def skim(_to: address):
    balance0: uint256 = staticcall MockToken(self.pairToken0).balanceOf(self)
    balance1: uint256 = staticcall MockToken(self.pairToken1).balanceOf(self)
    if balance0 > self.reserve0:
        assert extcall MockToken(self.pairToken0).transfer(_to, balance0 - self.reserve0)
    if balance1 > self.reserve1:
        assert extcall MockToken(self.pairToken1).transfer(_to, balance1 - self.reserve1)


@external
def mint(_to: address) -> uint256:
    assert _to != empty(address)
    balance0: uint256 = staticcall MockToken(self.pairToken0).balanceOf(self)
    balance1: uint256 = staticcall MockToken(self.pairToken1).balanceOf(self)
    added0: uint256 = balance0 - self.reserve0
    added1: uint256 = balance1 - self.reserve1
    liquidity: uint256 = min(added0, added1)
    assert liquidity != 0
    self.supply += liquidity
    self._update(balance0, balance1)
    return liquidity


@external
def burn(_to: address, _liquidity: uint256) -> (uint256, uint256):
    assert _to != empty(address) and _liquidity != 0 and _liquidity <= self.supply
    balance0: uint256 = staticcall MockToken(self.pairToken0).balanceOf(self)
    balance1: uint256 = staticcall MockToken(self.pairToken1).balanceOf(self)
    amount0: uint256 = balance0 * _liquidity // self.supply
    amount1: uint256 = balance1 * _liquidity // self.supply
    assert amount0 != 0 and amount1 != 0
    self.supply -= _liquidity
    assert extcall MockToken(self.pairToken0).transfer(_to, amount0)
    assert extcall MockToken(self.pairToken1).transfer(_to, amount1)
    self._update(balance0 - amount0, balance1 - amount1)
    return amount0, amount1


@external
def swap(
    _amount0Out: uint256,
    _amount1Out: uint256,
    _to: address,
    _data: Bytes[256],
):
    assert _amount0Out != 0 or _amount1Out != 0
    reserve0: uint256 = self.reserve0
    reserve1: uint256 = self.reserve1
    assert _amount0Out < reserve0 and _amount1Out < reserve1
    assert _to not in [self.pairToken0, self.pairToken1]

    if _amount0Out != 0:
        assert extcall MockToken(self.pairToken0).transfer(_to, _amount0Out)
    if _amount1Out != 0:
        assert extcall MockToken(self.pairToken1).transfer(_to, _amount1Out)
    if len(_data) != 0:
        extcall FlashCallee(_to).uniswapV2Call(msg.sender, _amount0Out, _amount1Out, _data)

    balance0: uint256 = staticcall MockToken(self.pairToken0).balanceOf(self)
    balance1: uint256 = staticcall MockToken(self.pairToken1).balanceOf(self)
    amount0In: uint256 = 0
    amount1In: uint256 = 0
    if balance0 > reserve0 - _amount0Out:
        amount0In = balance0 - (reserve0 - _amount0Out)
    if balance1 > reserve1 - _amount1Out:
        amount1In = balance1 - (reserve1 - _amount1Out)
    assert amount0In != 0 or amount1In != 0

    balance0Adjusted: uint256 = balance0 * 1_000 - amount0In * 3
    balance1Adjusted: uint256 = balance1 * 1_000 - amount1In * 3
    assert balance0Adjusted * balance1Adjusted >= reserve0 * reserve1 * 1_000_000
    self._update(balance0, balance1)


@external
def setShouldRevert(_shouldRevert: bool):
    self.shouldRevert = _shouldRevert


@external
def setReserveResponseMode(_responseMode: uint256):
    self.reserveResponseMode = _responseMode


@external
def setWordResponseMode(_kind: uint256, _responseMode: uint256):
    self.wordResponseModes[_kind] = _responseMode


@view
@internal
def _wordResponse(_value: uint256, _kind: uint256) -> Bytes[33]:
    mode: uint256 = self.wordResponseModes[_kind]
    if mode == 3:
        raise "forced revert"
    value: bytes32 = convert(_value, bytes32)
    if mode == 1:
        return slice(value, 0, 31)
    if mode == 2:
        return concat(value, b"x")
    return slice(value, 0, 32)


@view
@external
@raw_return
def factory() -> Bytes[33]:
    return self._wordResponse(convert(self.pairFactory, uint256), 1)


@view
@external
@raw_return
def token0() -> Bytes[33]:
    return self._wordResponse(convert(self.pairToken0, uint256), 2)


@view
@external
@raw_return
def token1() -> Bytes[33]:
    return self._wordResponse(convert(self.pairToken1, uint256), 3)


@view
@external
@raw_return
def price0CumulativeLast() -> Bytes[33]:
    return self._wordResponse(self.price0Cumulative, 4)


@view
@external
@raw_return
def price1CumulativeLast() -> Bytes[33]:
    return self._wordResponse(self.price1Cumulative, 5)


@view
@external
@raw_return
def totalSupply() -> Bytes[33]:
    return self._wordResponse(self.supply, 6)


@view
@external
def mockPrice0Cumulative() -> uint256:
    return self.price0Cumulative


@view
@external
def mockPrice1Cumulative() -> uint256:
    return self.price1Cumulative


@view
@external
def mockTotalSupply() -> uint256:
    return self.supply


@view
@external
@raw_return
def getReserves() -> Bytes[97]:
    assert not self.shouldRevert
    data: Bytes[96] = concat(
        convert(self.reserve0, bytes32),
        convert(self.reserve1, bytes32),
        convert(self.pairTimestamp, bytes32),
    )
    if self.reserveResponseMode == 1:
        return slice(data, 0, 95)
    if self.reserveResponseMode == 2:
        return concat(data, b"x")
    return data
