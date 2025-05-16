# @version 0.4.1

uses: addys

import contracts.modules.Addys as addys
from ethereum.ercs import IERC20

event DeptIdSet:
    deptId: uint256

event DepartmentActivated:
    deptId: uint256
    isActivated: bool

event DepartmentFundsRecovered:
    deptId: uint256
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

# config
deptId: public(uint256)
isActivated: public(bool)

CAN_MINT_GREEN: immutable(bool)
CAN_MINT_RIPE: immutable(bool)

MAX_RECOVER_ASSETS: constant(uint256) = 20


@deploy
def __init__(_canMintGreen: bool, _canMintRipe: bool):
    CAN_MINT_GREEN = _canMintGreen
    CAN_MINT_RIPE = _canMintRipe
    self.isActivated = True


###########
# Minting #
###########


@view
@external
def canMintGreen() -> bool:
    return CAN_MINT_GREEN


@view
@external
def canMintRipe() -> bool:
    return CAN_MINT_RIPE


########
# Ripe #
########


@external
def setRegistryId(_regId: uint256) -> bool:
    assert msg.sender == addys._getRipeHq() # dev: only ripe hq allowed

    prevDeptId: uint256 = self.deptId
    assert prevDeptId == 0 or prevDeptId == _regId # dev: invalid dept id
    self.deptId = _regId
    log DeptIdSet(deptId=_regId)
    return True


@external
def activate(_shouldActivate: bool):
    assert msg.sender == addys._getControlRoomAddr() # dev: only ControlRoom allowed
    self.isActivated = _shouldActivate
    log DepartmentActivated(deptId=self.deptId, isActivated=_shouldActivate)


@external
def recoverFunds(_recipient: address, _asset: address):
    assert msg.sender == addys._getControlRoomAddr() # dev: only ControlRoom allowed
    self._recoverFunds(_recipient, _asset)


@external
def recoverFundsMany(_recipient: address, _assets: DynArray[address, MAX_RECOVER_ASSETS]):
    assert msg.sender == addys._getControlRoomAddr() # dev: only ControlRoom allowed
    for a: address in _assets:
        self._recoverFunds(_recipient, a)


@internal
def _recoverFunds(_recipient: address, _asset: address):
    assert empty(address) not in [_recipient, _asset] # dev: invalid recipient or asset
    balance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    assert balance != 0 # dev: nothing to recover

    assert extcall IERC20(_asset).transfer(_recipient, balance, default_return_value=True) # dev: recovery failed
    log DepartmentFundsRecovered(deptId=self.deptId, asset=_asset, recipient=_recipient, balance=balance)
