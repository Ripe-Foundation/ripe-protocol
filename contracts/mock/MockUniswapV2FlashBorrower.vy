# @version 0.4.3

interface MockToken:
    def transfer(_to: address, _amount: uint256) -> bool: nonpayable


pair: public(address)
token0: public(address)
token1: public(address)
repay0: public(uint256)
repay1: public(uint256)


@external
def configure(
    _pair: address,
    _token0: address,
    _token1: address,
    _repay0: uint256,
    _repay1: uint256,
):
    self.pair = _pair
    self.token0 = _token0
    self.token1 = _token1
    self.repay0 = _repay0
    self.repay1 = _repay1


@external
def uniswapV2Call(
    _sender: address,
    _amount0Out: uint256,
    _amount1Out: uint256,
    _data: Bytes[256],
):
    assert msg.sender == self.pair
    assert _sender != empty(address) and (_amount0Out != 0 or _amount1Out != 0)
    assert len(_data) != 0
    if self.repay0 != 0:
        assert extcall MockToken(self.token0).transfer(self.pair, self.repay0)
    if self.repay1 != 0:
        assert extcall MockToken(self.token1).transfer(self.pair, self.repay1)
