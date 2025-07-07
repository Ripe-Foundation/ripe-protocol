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
    ripePerUnit: uint256
    maxUnitsAllowed: uint256
    expireBlock: uint256

event BondBoostModified:
    user: address
    ripePerUnit: uint256
    maxUnitsAllowed: uint256
    expireBlock: uint256

event ManyBondBoostersSet:
    numBoosters: uint256

event BondBoostRemoved:
    user: address

# data
config: public(HashMap[address, BoosterConfig]) # user -> config
unitsUsed: public(HashMap[address, uint256]) # user -> units used

MAX_BOOSTERS: constant(uint256) = 50
MAX_BOOST: immutable(uint256)
MAX_UNITS: immutable(uint256)


@deploy
def __init__(
    _ripeHq: address,
    _maxBoost: uint256,
    _maxUnits: uint256,
    _initialBoosts: DynArray[BoosterConfig, MAX_BOOSTERS],
):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting

    MAX_BOOST = _maxBoost
    MAX_UNITS = _maxUnits

    # set initial access
    if len(_initialBoosts) != 0:
        for b: BoosterConfig in _initialBoosts:
            assert self._setBondBooster(b) # dev: invalid booster


####################
# Get Boosted Ripe #
####################


@view
@external
def getBoostedRipe(_user: address, _units: uint256) -> uint256:
    config: BoosterConfig = self.config[_user]
    if config.user == empty(address) or config.expireBlock <= block.number:
        return 0
    unitsUsed: uint256 = self.unitsUsed[_user]
    if unitsUsed >= config.maxUnitsAllowed:
        return 0
    availUnits: uint256 = min(config.maxUnitsAllowed - unitsUsed, _units)
    return config.ripePerUnit * availUnits


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


# set single


@external
def setBondBooster(_config: BoosterConfig):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert self._setBondBooster(_config) # dev: invalid booster


# set many


@external
def setManyBondBoosters(_boosters: DynArray[BoosterConfig, MAX_BOOSTERS]):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert len(_boosters) != 0 # dev: no boosters
    for b: BoosterConfig in _boosters:
        assert self._setBondBooster(b) # dev: invalid booster
    log ManyBondBoostersSet(numBoosters = len(_boosters))


@internal
def _setBondBooster(_config: BoosterConfig) -> bool:
    if not self._isValidBooster(_config):
        return False

    self.config[_config.user] = _config
    log BondBoostModified(
        user=_config.user,
        ripePerUnit=_config.ripePerUnit,
        maxUnitsAllowed=_config.maxUnitsAllowed,
        expireBlock=_config.expireBlock,
    )
    return True


# remove booster config


@external
def removeBondBooster(_user: address):
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    self.config[_user] = empty(BoosterConfig)
    self.unitsUsed[_user] = 0
    log BondBoostRemoved(user = _user)


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
    if _config.ripePerUnit == 0 or _config.ripePerUnit > MAX_BOOST:
        return False
    if _config.expireBlock <= block.number:
        return False
    if _config.maxUnitsAllowed == 0 or _config.maxUnitsAllowed > MAX_UNITS:
        return False
    return True
