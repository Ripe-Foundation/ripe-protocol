# @version 0.4.1

implements: IERC4626
from ethereum.ercs import IERC4626

uses: token
from contracts.tokens.modules import Erc20Token as token
from ethereum.ercs import IERC20

event Deposit:
    sender: indexed(address)
    owner: indexed(address)
    assets: uint256
    shares: uint256

event Withdraw:
    sender: indexed(address)
    receiver: indexed(address)
    owner: indexed(address)
    assets: uint256
    shares: uint256

lastPricePerShare: public(uint256)

ASSET: immutable(address)
DECIMAL_OFFSET: constant(uint256) = 10 ** 8


@deploy
def __init__(_asset: address):
    assert _asset != empty(address) # dev: invalid asset
    ASSET = _asset


@view
@external
def asset() -> address:
    return ASSET


@view
@external
def totalAssets() -> uint256:
    return staticcall IERC20(ASSET).balanceOf(self)


############
# Deposits #
############


@view
@external
def maxDeposit(_receiver: address) -> uint256:
    return max_value(uint256)


@view
@external
def previewDeposit(_assets: uint256) -> uint256:
    return self._amountToShares(_assets, token.totalSupply, staticcall IERC20(ASSET).balanceOf(self), False)


@nonreentrant
@external
def deposit(_assets: uint256, _receiver: address = msg.sender) -> uint256:
    asset: address = ASSET

    amount: uint256 = _assets
    if amount == max_value(uint256):
        amount = staticcall IERC20(asset).balanceOf(msg.sender)

    shares: uint256 = self._amountToShares(amount, token.totalSupply, staticcall IERC20(asset).balanceOf(self), False)
    self._deposit(asset, amount, shares, _receiver)
    return shares


# mint


@view
@external
def maxMint(_receiver: address) -> uint256:
    return max_value(uint256)


@view
@external
def previewMint(_shares: uint256) -> uint256:
    return self._sharesToAmount(_shares, token.totalSupply, staticcall IERC20(ASSET).balanceOf(self), True)


@nonreentrant
@external
def mint(_shares: uint256, _receiver: address = msg.sender) -> uint256:
    asset: address = ASSET
    amount: uint256 = self._sharesToAmount(_shares, token.totalSupply, staticcall IERC20(asset).balanceOf(self), True)
    self._deposit(asset, amount, _shares, _receiver)
    return amount


# shared deposit logic


@internal
def _deposit(_asset: address, _amount: uint256, _shares: uint256, _recipient: address):
    assert _amount != 0 # dev: cannot deposit 0 amount
    assert _shares != 0 # dev: cannot receive 0 shares
    assert _recipient != empty(address) # dev: invalid recipient

    assert extcall IERC20(_asset).transferFrom(msg.sender, self, _amount, default_return_value=True) # dev: deposit failed
    token._mint(_recipient, _shares)

    # update last price per share
    self._updateLastPricePerShare(_asset)

    log Deposit(sender=msg.sender, owner=_recipient, assets=_amount, shares=_shares)


###############
# Withdrawals #
###############


@view
@external
def maxWithdraw(_owner: address) -> uint256:
    return staticcall IERC20(ASSET).balanceOf(self)


@view
@external
def previewWithdraw(_assets: uint256) -> uint256:
    return self._amountToShares(_assets, token.totalSupply, staticcall IERC20(ASSET).balanceOf(self), True)


@external
def withdraw(_assets: uint256, _receiver: address = msg.sender, _owner: address = msg.sender) -> uint256:
    asset: address = ASSET
    shares: uint256 = self._amountToShares(_assets, token.totalSupply, staticcall IERC20(asset).balanceOf(self), True)
    self._redeem(asset, _assets, shares, msg.sender, _receiver, _owner)
    return shares


# redeem


@view
@external
def maxRedeem(_owner: address) -> uint256:
    return token.balanceOf[_owner]


@view
@external
def previewRedeem(_shares: uint256) -> uint256:
    return self._sharesToAmount(_shares, token.totalSupply, staticcall IERC20(ASSET).balanceOf(self), False)


@external
def redeem(_shares: uint256, _receiver: address = msg.sender, _owner: address = msg.sender) -> uint256:
    asset: address = ASSET

    shares: uint256 = _shares
    if shares == max_value(uint256):
        shares = token.balanceOf[_owner]

    amount: uint256 = self._sharesToAmount(shares, token.totalSupply, staticcall IERC20(asset).balanceOf(self), False)
    return self._redeem(asset, amount, shares, msg.sender, _receiver, _owner)


# shared redeem logic


@internal
def _redeem(
    _asset: address,
    _amount: uint256,
    _shares: uint256, 
    _sender: address, 
    _recipient: address, 
    _owner: address,
) -> uint256:
    assert _amount != 0 # dev: cannot withdraw 0 amount
    assert _shares != 0 # dev: cannot redeem 0 shares
    assert _recipient != empty(address) # dev: invalid recipient

    assert token.balanceOf[_owner] >= _shares # dev: insufficient shares

    if _sender != _owner:
        token._spendAllowance(_owner, _sender, _shares)

    token._burn(_owner, _shares)
    assert extcall IERC20(_asset).transfer(_recipient, _amount, default_return_value=True) # dev: withdrawal failed

    # update last price per share
    self._updateLastPricePerShare(_asset)

    log Withdraw(sender=_sender, receiver=_recipient, owner=_owner, assets=_amount, shares=_shares)
    return _amount


##########
# Shares #
##########


@view
@external
def convertToShares(_assets: uint256) -> uint256:
    return self._amountToShares(_assets, token.totalSupply, staticcall IERC20(ASSET).balanceOf(self), False)


@view
@external
def convertToAssets(_shares: uint256) -> uint256:
    return self._sharesToAmount(_shares, token.totalSupply, staticcall IERC20(ASSET).balanceOf(self), False)


# amount -> shares


@view
@internal
def _amountToShares(
    _amount: uint256,
    _totalShares: uint256,
    _totalBalance: uint256,
    _shouldRoundUp: bool,
) -> uint256:
    totalBalance: uint256 = _totalBalance

    # dead shares / decimal offset -- preventing donation attacks
    totalBalance += 1
    totalShares: uint256 = _totalShares + DECIMAL_OFFSET

    # calc shares
    numerator: uint256 = _amount * totalShares
    shares: uint256 = numerator // totalBalance

    # rounding
    if _shouldRoundUp and (numerator % totalBalance != 0):
        shares += 1

    return shares


# shares -> amount


@view
@internal
def _sharesToAmount(
    _shares: uint256,
    _totalShares: uint256,
    _totalBalance: uint256,
    _shouldRoundUp: bool,
) -> uint256:
    totalBalance: uint256 = _totalBalance

    # dead shares / decimal offset -- preventing donation attacks
    totalBalance += 1
    totalShares: uint256 = _totalShares + DECIMAL_OFFSET

    # calc amount
    numerator: uint256 = _shares * totalBalance
    amount: uint256 = numerator // totalShares

    # rounding
    if _shouldRoundUp and (numerator % totalShares != 0):
        amount += 1

    return amount


# price per share


@internal
def _updateLastPricePerShare(_asset: address):
    newLastPricePerShare: uint256 = self._sharesToAmount(10 ** convert(token.TOKEN_DECIMALS, uint256), token.totalSupply, staticcall IERC20(_asset).balanceOf(self), False)
    self.lastPricePerShare = newLastPricePerShare


@view
@external
def getLastUnderlying(_shares: uint256) -> uint256:
    return self.lastPricePerShare * _shares // (10 ** convert(token.TOKEN_DECIMALS, uint256))


@view
@external
def pricePerShare() -> uint256:
    return self._sharesToAmount(10 ** convert(token.TOKEN_DECIMALS, uint256), token.totalSupply, staticcall IERC20(ASSET).balanceOf(self), False)