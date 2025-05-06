# @version 0.4.1

initializes: gov
initializes: registry

exports: gov.__interface__

import contracts.modules.LocalGov as gov
import contracts.modules.Registry as registry
from interfaces import Strategy


@deploy
def __init__(
    _addyRegistry: address,
    _minStratChangeDelay: uint256,
    _maxStratChangeDelay: uint256,
):
    assert _addyRegistry != empty(address) # dev: invalid addy registry

    # initialize gov
    gov.__init__(empty(address), _addyRegistry, 0, 0)

    # initialize registry
    registry.__init__(_minStratChangeDelay, _maxStratChangeDelay, "StratBook.vy")


##################
# Register Strat #
##################


@view
@external
def isValidNewStratAddr(_addr: address) -> bool:
    return registry._isValidNewAddy(_addr)


@external
def registerNewStrat(_addr: address, _description: String[64]) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._registerNewAddy(_addr, _description)


@external
def confirmNewStratRegistration(_addr: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    stratId: uint256 = registry._confirmNewAddy(_addr)
    if stratId != 0:
        assert extcall Strategy(_addr).setStratId(stratId) # dev: set id failed
    return stratId


@external
def cancelPendingNewStrat(_addr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelPendingNewAddy(_addr)


################
# Update Strat #
################


@view
@external
def isValidStratUpdate(_stratId: uint256, _newAddr: address) -> bool:
    if self._hasAnyFunds(_stratId):
        return False
    return registry._isValidAddyUpdate(_stratId, _newAddr, registry.addyInfo[_stratId].addr)


@external
def updateStratAddr(_stratId: uint256, _newAddr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    if self._hasAnyFunds(_stratId):
        return False
    return registry._updateAddyAddr(_stratId, _newAddr)


@external
def confirmStratUpdate(_stratId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    if self._hasAnyFunds(_stratId):
        return False
    didUpdate: bool = registry._confirmAddyUpdate(_stratId)
    if didUpdate:
        stratAddr: address = registry.addyInfo[_stratId].addr
        assert extcall Strategy(stratAddr).setStratId(_stratId) # dev: set id failed
    return didUpdate


@external
def cancelPendingStratUpdate(_stratId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelPendingAddyUpdate(_stratId)


#################
# Disable Strat #
#################


@view
@external
def isValidStratDisable(_stratId: uint256) -> bool:
    if self._hasAnyFunds(_stratId):
        return False
    return registry._isValidAddyDisable(_stratId, registry.addyInfo[_stratId].addr)


@external
def disableStratAddr(_stratId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    if self._hasAnyFunds(_stratId):
        return False
    return registry._disableAddyAddr(_stratId)


@external
def confirmStratDisable(_stratId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    if self._hasAnyFunds(_stratId):
        return False
    return registry._confirmAddyDisable(_stratId)


@external
def cancelPendingStratDisable(_stratId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelPendingAddyDisable(_stratId)


######################
# Strat Change Delay #
######################


@external
def setStratChangeDelay(_numBlocks: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._setAddyChangeDelay(_numBlocks)


@view
@external
def stratChangeDelay() -> uint256:
    return registry.addyChangeDelay


@external
def setStratChangeDelayToMin() -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._setAddyChangeDelay(registry.MIN_ADDY_CHANGE_DELAY)


#################
# Views / Utils #
#################


@view
@external
def numStratsRaw() -> uint256:
    return registry.numAddys


# is valid


@view
@external
def isValidStratAddr(_addr: address) -> bool:
    return registry._isValidAddyAddr(_addr)


@view
@external
def isValidStratId(_stratId: uint256) -> bool:
    return registry._isValidAddyId(_stratId)


# lego getters


@view
@external
def getStratId(_addr: address) -> uint256:
    return registry._getAddyId(_addr)


@view
@external
def getStratAddr(_stratId: uint256) -> address:
    return registry._getAddy(_stratId)


@view
@external
def getStratInfo(_stratId: uint256) -> registry.AddyInfo:
    return registry.addyInfo[_stratId]


@view
@external
def getStratDescription(_stratId: uint256) -> String[64]:
    return registry.addyInfo[_stratId].description


# high level


@view
@external
def getNumStrats() -> uint256:
    return registry._getNumAddys()


@view
@external
def getLastStratAddr() -> address:
    return registry._getLastAddyAddr()


@view
@external
def getLastStratId() -> uint256:
    return registry._getLastAddyId()


# other utils


@view
@external
def hasAnyFunds(_stratId: uint256) -> bool:
    return self._hasAnyFunds(_stratId)


@view
@internal
def _hasAnyFunds(_stratId: uint256) -> bool:
    stratAddr: address = registry._getAddy(_stratId)
    return staticcall Strategy(stratAddr).hasAnyFunds()