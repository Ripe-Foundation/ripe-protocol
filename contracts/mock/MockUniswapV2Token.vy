# @version 0.4.3

decimals: public(uint256)
balanceOf: public(HashMap[address, uint256])


@deploy
def __init__(_decimals: uint256):
    self.decimals = _decimals


@external
def setDecimals(_decimals: uint256):
    self.decimals = _decimals


@external
def mint(_account: address, _amount: uint256):
    self.balanceOf[_account] += _amount


@external
def setBalance(_account: address, _amount: uint256):
    self.balanceOf[_account] = _amount


@external
def transfer(_to: address, _amount: uint256) -> bool:
    self.balanceOf[msg.sender] -= _amount
    self.balanceOf[_to] += _amount
    return True
