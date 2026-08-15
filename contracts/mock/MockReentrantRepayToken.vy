# @dev Test-only ERC20 that reenters a debt-mutating Teller route during transfer.
#      Used to reproduce the SC-07 stale-debt overwrite: while Deleverage is
#      moving this token as collateral, the transfer hook mutates the borrower's
#      debt (repay = decrease, borrow = increase) underneath the outer settlement.
# @version 0.4.3

from ethereum.ercs import IERC20

implements: IERC20

struct DeleverageUserRequest:
    user: address
    targetRepayAmount: uint256

interface Teller:
    def repay(_paymentAmount: uint256, _user: address, _isPaymentSavingsGreen: bool, _shouldRefundSavingsGreen: bool) -> bool: nonpayable
    def borrow(_greenAmount: uint256, _user: address, _wantsSavingsGreen: bool, _shouldEnterStabPool: bool) -> uint256: nonpayable
    def deleverageManyUsers(_users: DynArray[DeleverageUserRequest, 25]) -> uint256: nonpayable

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    value: uint256

name: public(constant(String[32])) = "Reentrant Repay Token"
symbol: public(constant(String[32])) = "RRPT"
decimals: public(constant(uint8)) = 18

balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

hq: public(address)

# attack config
teller: public(address)
attackUser: public(address)
attackAmount: public(uint256)
attackMode: public(uint256)   # 0 = repay, 1 = borrow, 2 = reenter deleverage, 3 = repay-then-borrow (same amount)
attackEnabled: public(bool)
attackExecuted: public(bool)


@deploy
def __init__(_hq: address):
    self.hq = _hq


@external
def configureAttack(_teller: address, _user: address, _amount: uint256):
    assert msg.sender == self.hq # dev: only hq
    self.teller = _teller
    self.attackUser = _user
    self.attackAmount = _amount
    self.attackMode = 0
    self.attackEnabled = True
    self.attackExecuted = False


@external
def configureBorrow(_teller: address, _user: address, _amount: uint256):
    assert msg.sender == self.hq # dev: only hq
    self.teller = _teller
    self.attackUser = _user
    self.attackAmount = _amount
    self.attackMode = 1
    self.attackEnabled = True
    self.attackExecuted = False


@external
def configureReenterDeleverage(_teller: address, _user: address):
    assert msg.sender == self.hq # dev: only hq
    self.teller = _teller
    self.attackUser = _user
    self.attackAmount = 1  # sentinel; unused for mode 2 but must be nonzero
    self.attackMode = 2
    self.attackEnabled = True
    self.attackExecuted = False


@external
def configureRepayThenBorrow(_teller: address, _user: address, _amount: uint256):
    # Restores the same final debt amount (repay X then borrow X) while mutating
    # non-amount fields (principal split, interest booking, borrow interval).
    assert msg.sender == self.hq # dev: only hq
    self.teller = _teller
    self.attackUser = _user
    self.attackAmount = _amount
    self.attackMode = 3
    self.attackEnabled = True
    self.attackExecuted = False


@external
def disableAttack():
    assert msg.sender == self.hq # dev: only hq
    self.attackEnabled = False


@internal
def _maybeAttack():
    if self.attackEnabled and not self.attackExecuted and self.attackAmount != 0 and self.teller != empty(address):
        self.attackExecuted = True
        # Teller's outer deleverage routes are not @nonreentrant, so its global
        # lock is free and reentry into repay/borrow can mutate debt. Deleverage
        # uses a separate lock domain that blocks only mode-2 cross-entry.
        if self.attackMode == 0:
            extcall Teller(self.teller).repay(self.attackAmount, self.attackUser, False, False)
        elif self.attackMode == 1:
            extcall Teller(self.teller).borrow(self.attackAmount, self.attackUser, False, False)
        elif self.attackMode == 3:
            # repay X then borrow X: net debt amount restored, other fields changed
            extcall Teller(self.teller).repay(self.attackAmount, self.attackUser, False, False)
            extcall Teller(self.teller).borrow(self.attackAmount, self.attackUser, False, False)
        else:
            # reenter a guarded Deleverage route (via the Teller entry point)
            extcall Teller(self.teller).deleverageManyUsers([DeleverageUserRequest(user=self.attackUser, targetRepayAmount=0)])


@external
def transfer(_to: address, _value: uint256) -> bool:
    self._maybeAttack()
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    log Transfer(sender=msg.sender, receiver=_to, value=_value)
    return True


@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    self.allowance[_from][msg.sender] -= _value
    self._maybeAttack()
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    log Transfer(sender=_from, receiver=_to, value=_value)
    return True


@external
def approve(_spender: address, _value: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _value
    log Approval(owner=msg.sender, spender=_spender, value=_value)
    return True


@external
def mint(_to: address, _value: uint256):
    assert msg.sender == self.hq # dev: only hq
    assert _to != empty(address) # dev: invalid recipient
    self.totalSupply += _value
    self.balanceOf[_to] += _value
    log Transfer(sender=empty(address), receiver=_to, value=_value)
