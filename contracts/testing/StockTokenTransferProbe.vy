# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026

# @version 0.4.3

from ethereum.ercs import IERC20


event TokenDeposited:
    sender: indexed(address)
    token: indexed(address)
    amount: uint256
    balanceBefore: uint256
    balanceAfter: uint256

event TokenWithdrawn:
    owner: indexed(address)
    recipient: indexed(address)
    token: indexed(address)
    amount: uint256
    probeBalanceBefore: uint256
    probeBalanceAfter: uint256

event TokenRecovered:
    owner: indexed(address)
    recipient: indexed(address)
    token: indexed(address)
    amount: uint256
    probeBalanceBefore: uint256
    probeBalanceAfter: uint256


OWNER: public(immutable(address))
TOKEN: public(immutable(address))
RECIPIENT: public(immutable(address))


@deploy
def __init__(_owner: address, _token: address, _recipient: address):
    assert empty(address) not in [_owner, _token, _recipient]  # dev: invalid configuration
    assert _token.is_contract  # dev: invalid token
    OWNER = _owner
    TOKEN = _token
    RECIPIENT = _recipient


@nonreentrant
@external
def deposit(_amount: uint256) -> uint256:
    """
    @notice Pull the configured token from the caller and require an exact balance delta.
    """
    assert msg.sender == OWNER  # dev: only owner
    assert _amount != 0  # dev: invalid amount

    balanceBefore: uint256 = staticcall IERC20(TOKEN).balanceOf(self)
    assert extcall IERC20(TOKEN).transferFrom(
        msg.sender,
        self,
        _amount,
        default_return_value=True,
    )  # dev: token transfer failed
    balanceAfter: uint256 = staticcall IERC20(TOKEN).balanceOf(self)
    assert balanceAfter == balanceBefore + _amount  # dev: unexpected deposit delta

    log TokenDeposited(
        sender=msg.sender,
        token=TOKEN,
        amount=_amount,
        balanceBefore=balanceBefore,
        balanceAfter=balanceAfter,
    )
    return balanceAfter


@nonreentrant
@external
def withdraw(_amount: uint256) -> uint256:
    """
    @notice Send an exact amount of the configured token to the configured recipient.
    """
    assert msg.sender == OWNER  # dev: only owner
    assert _amount != 0  # dev: invalid amount

    probeBalanceBefore: uint256 = staticcall IERC20(TOKEN).balanceOf(self)
    recipientBalanceBefore: uint256 = staticcall IERC20(TOKEN).balanceOf(RECIPIENT)
    assert probeBalanceBefore >= _amount  # dev: insufficient probe balance

    assert extcall IERC20(TOKEN).transfer(
        RECIPIENT,
        _amount,
        default_return_value=True,
    )  # dev: token transfer failed

    probeBalanceAfter: uint256 = staticcall IERC20(TOKEN).balanceOf(self)
    recipientBalanceAfter: uint256 = staticcall IERC20(TOKEN).balanceOf(RECIPIENT)
    assert probeBalanceAfter == probeBalanceBefore - _amount  # dev: unexpected probe delta
    assert recipientBalanceAfter == recipientBalanceBefore + _amount  # dev: unexpected recipient delta

    log TokenWithdrawn(
        owner=msg.sender,
        recipient=RECIPIENT,
        token=TOKEN,
        amount=_amount,
        probeBalanceBefore=probeBalanceBefore,
        probeBalanceAfter=probeBalanceAfter,
    )
    return probeBalanceAfter


@nonreentrant
@external
def recoverToken(_token: address, _amount: uint256) -> uint256:
    """
    @notice Recover an accidentally retained ERC-20 to the configured recipient.
    """
    assert msg.sender == OWNER  # dev: only owner
    assert _token != empty(address) and _token.is_contract  # dev: invalid token
    assert _amount != 0  # dev: invalid amount

    probeBalanceBefore: uint256 = staticcall IERC20(_token).balanceOf(self)
    recipientBalanceBefore: uint256 = staticcall IERC20(_token).balanceOf(RECIPIENT)
    assert probeBalanceBefore >= _amount  # dev: insufficient probe balance

    assert extcall IERC20(_token).transfer(
        RECIPIENT,
        _amount,
        default_return_value=True,
    )  # dev: token transfer failed

    probeBalanceAfter: uint256 = staticcall IERC20(_token).balanceOf(self)
    recipientBalanceAfter: uint256 = staticcall IERC20(_token).balanceOf(RECIPIENT)
    assert probeBalanceAfter == probeBalanceBefore - _amount  # dev: unexpected probe delta
    assert recipientBalanceAfter == recipientBalanceBefore + _amount  # dev: unexpected recipient delta

    log TokenRecovered(
        owner=msg.sender,
        recipient=RECIPIENT,
        token=_token,
        amount=_amount,
        probeBalanceBefore=probeBalanceBefore,
        probeBalanceAfter=probeBalanceAfter,
    )
    return probeBalanceAfter
