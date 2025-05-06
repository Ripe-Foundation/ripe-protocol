# SPDX-License-Identifier: MIT
# Underscore Protocol License: https://github.com/underscore-finance/underscore/blob/main/licenses/MIT_LICENSE
# Underscore Protocol (C) 2025 Hightop Financial, Inc.
# @version 0.4.1

from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    value: uint256

asset: public(address)
balanceOf: public(HashMap[address, uint256]) # user -> shares
totalSupply: public(uint256)
allowance: public(HashMap[address, HashMap[address, uint256]])

# NOTE: this does not include ALL required erc20/4626 methods. 
# This only includes what we use/need for our strats


@deploy
def __init__(_asset: address):
    self.asset = _asset


@external
def deposit(_amount: uint256, _receiver: address) -> uint256:
    shares: uint256 = self._calcSharesOnDeposit(_amount)
    assert extcall IERC20(self.asset).transferFrom(msg.sender, self, _amount, default_return_value=True) # dev: transfer failed
    self.balanceOf[_receiver] += shares
    self.totalSupply += shares
    return shares


@external
def redeem(_shares: uint256, _receiver: address, _owner: address) -> uint256:
    shares: uint256 = min(_shares, self.balanceOf[_owner])
    amount: uint256 = min(self._sharesToAmount(shares), staticcall IERC20(self.asset).balanceOf(self))
    assert extcall IERC20(self.asset).transfer(_receiver, amount, default_return_value=True) # dev: transfer failed
    self.balanceOf[_owner] -= shares
    self.totalSupply -= shares
    return amount


@view
@external
def convertToAssets(_shares: uint256) -> uint256:
    return self._sharesToAmount(_shares)


@view
@internal
def _sharesToAmount(_shares: uint256) -> uint256:
    if _shares == 0:
        return 0
    totalShares: uint256 = self.totalSupply
    if totalShares == 0:
        return _shares
    totalBalance: uint256 = staticcall IERC20(self.asset).balanceOf(self)
    if _shares == totalShares:
        return totalBalance
    return totalBalance * _shares // totalShares


@view
@external
def convertToShares(_amount: uint256) -> uint256:
    return self._amountToShares(_amount)


@view
@internal
def _calcSharesOnDeposit(_amount: uint256) -> uint256:
    # Note: share decimals are same as underlying asset decimals
    totalShares: uint256 = self.totalSupply
    shares: uint256 = 0
    if totalShares == 0:
        shares = _amount
         # see https://code4rena.com/reports/2022-01-sherlock/#h-01-first-user-can-steal-everyone-elses-tokens
        assert shares > 10 ** convert(staticcall IERC20Detailed(self.asset).decimals() // 2, uint256) # dev: amount too small
    else:
        shares = _amount * totalShares // staticcall IERC20(self.asset).balanceOf(self)
    assert shares != 0 # dev: did not calc shares
    return shares


@external
def totalAssets() -> uint256:
    return staticcall IERC20(self.asset).balanceOf(self)


@view
@internal
def _amountToShares(_amount: uint256) -> uint256:
    if _amount == 0:
        return 0
    totalBalance: uint256 = staticcall IERC20(self.asset).balanceOf(self)
    totalShares: uint256 = self.totalSupply
    if totalBalance == 0 or totalShares == 0:
        return 0
    return _amount * totalShares // totalBalance


# erc20 methods


@external
def transfer(_to: address, _value: uint256) -> bool:
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    log Transfer(sender=msg.sender, receiver=_to, value=_value)
    return True


@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    self.allowance[_from][msg.sender] -= _value
    log Transfer(sender=_from, receiver=_to, value=_value)
    return True


@external
def approve(_spender: address, _value: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _value
    log Approval(owner=msg.sender, spender=_spender, value=_value)
    return True