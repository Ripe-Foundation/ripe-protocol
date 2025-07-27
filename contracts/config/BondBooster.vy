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

struct BoosterConfig:
    user: address
    boostRatio: uint256
    maxUnitsAllowed: uint256
    expireBlock: uint256

event BondBoostModified:
    user: address
    boostRatio: uint256
    maxUnitsAllowed: uint256
    expireBlock: uint256

event ManyBondBoostersSet:
    numBoosters: uint256

event BondBoostRemoved:
    user: address

event MaxBoostAndMaxUnitsSet:
    maxBoostRatio: uint256
    maxUnits: uint256

# data
config: public(HashMap[address, BoosterConfig]) # user -> config
unitsUsed: public(HashMap[address, uint256]) # user -> units used

maxBoostRatio: public(uint256)
maxUnits: public(uint256)

MAX_BOOSTERS: constant(uint256) = 50


@deploy
def __init__(
    _ripeHq: address,
    _maxBoostRatio: uint256,
    _maxUnits: uint256,
):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting

    self.maxBoostRatio = _maxBoostRatio
    self.maxUnits = _maxUnits


####################
# Get Boosted Ripe #
####################


@view
@external
def getBoostRatio(_user: address, _units: uint256) -> uint256:
    config: BoosterConfig = self.config[_user]
    if config.user == empty(address) or config.expireBlock <= block.number:
        return 0
    unitsUsed: uint256 = self.unitsUsed[_user]
    if unitsUsed + _units > config.maxUnitsAllowed:
        return 0
    return config.boostRatio


#######################
# Update Booster Data #
#######################


@external
def addNewUnitsUsed(_user: address, _newUnits: uint256):
    assert msg.sender == addys._getBondRoomAddr() # dev: no perms
    self.unitsUsed[_user] += _newUnits


######################
# Set Booster Config #
######################


# add booster config


@external
def setBondBooster(_config: BoosterConfig):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert self._setBondBooster(_config) # dev: invalid booster


@external
def setManyBondBoosters(_boosters: DynArray[BoosterConfig, MAX_BOOSTERS]):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert len(_boosters) != 0 # dev: no boosters
    for b: BoosterConfig in _boosters:
        assert self._setBondBooster(b) # dev: invalid booster


@internal
def _setBondBooster(_config: BoosterConfig) -> bool:
    if not self._isValidBooster(_config):
        return False

    self.config[_config.user] = _config
    log BondBoostModified(
        user=_config.user,
        boostRatio=_config.boostRatio,
        maxUnitsAllowed=_config.maxUnitsAllowed,
        expireBlock=_config.expireBlock,
    )
    return True


# remove booster config


@external
def removeManyBondBoosters(_users: DynArray[address, MAX_BOOSTERS]):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    for user: address in _users:
        if user == empty(address):
            continue
        self._removeBondBooster(user)


@external
def removeBondBooster(_user: address):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _user != empty(address) # dev: invalid user
    self._removeBondBooster(_user)


@internal
def _removeBondBooster(_user: address):
    self.config[_user] = empty(BoosterConfig)
    self.unitsUsed[_user] = 0
    log BondBoostRemoved(user = _user)


# set max boost and max units


@external
def setMaxBoostAndMaxUnits(_maxBoostRatio: uint256, _maxUnitsAvail: uint256):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert max_value(uint256) not in [_maxBoostRatio, _maxUnitsAvail] # dev: invalid max values
    assert 0 not in [_maxBoostRatio, _maxUnitsAvail] # dev: invalid max values
    self.maxBoostRatio = _maxBoostRatio
    self.maxUnits = _maxUnitsAvail
    log MaxBoostAndMaxUnitsSet(maxBoostRatio = _maxBoostRatio, maxUnits = _maxUnitsAvail)


######################
# Booster Validation #
######################


@view
@external
def isValidBooster(_config: BoosterConfig) -> bool:
    return self._isValidBooster(_config)


@view
@internal
def _isValidBooster(_config: BoosterConfig) -> bool:
    if _config.user == empty(address):
        return False
    if _config.boostRatio == 0 or _config.boostRatio > self.maxBoostRatio:
        return False
    if _config.expireBlock <= block.number:
        return False
    if _config.maxUnitsAllowed == 0 or _config.maxUnitsAllowed > self.maxUnits:
        return False
    return True
