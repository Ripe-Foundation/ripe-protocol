# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department

event TrainingWheelsModified:
    user: indexed(address)
    shouldAllow: bool

# data
allowed: public(HashMap[address, bool]) # user -> allowed

MAX_INITIAL: constant(uint256) = 20


@deploy
def __init__(_ripeHq: address, _initialList: DynArray[address, MAX_INITIAL]):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting

    # set initial access
    if len(_initialList) != 0:
        for a: address in _initialList:
            if a == empty(address):
                continue
            self.allowed[a] = True
            log TrainingWheelsModified(user=a, shouldAllow=True)


@external
def setAllowed(_user: address, _shouldAllow: bool):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _user != empty(address) # dev: invalid user

    self.allowed[_user] = _shouldAllow
    log TrainingWheelsModified(user=_user, shouldAllow=_shouldAllow)


# NOTE: need to keep `_asset` to be compatible with other "whitelist" contracts


@view
@external
def isUserAllowed(_user: address, _asset: address) -> bool:
    return self.allowed[_user]