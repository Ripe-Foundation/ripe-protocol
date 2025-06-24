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
    asset: indexed(address)
    shouldAllow: bool

# data
allowed: public(HashMap[address, HashMap[address, bool]]) # user -> asset -> allowed


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting


@external
def setAllowed(_user: address, _asset: address, _shouldAllow: bool):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert empty(address) not in [_user, _asset] # dev: invalid user or asset

    self.allowed[_user][_asset] = _shouldAllow
    log TrainingWheelsModified(user=_user, asset=_asset, shouldAllow=_shouldAllow)


@view
@external
def isUserAllowed(_user: address, _asset: address) -> bool:
    return self.allowed[_user][_asset]