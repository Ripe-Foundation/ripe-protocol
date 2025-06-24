# @version 0.4.3

exports: gov.__interface__
exports: timeLock.__interface__

initializes: gov
initializes: timeLock[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.TimeLock as timeLock

struct PendingData:
    actionId: uint256
    value: uint256

data: public(HashMap[address, uint256]) # asset -> value
pendingData: public(HashMap[address, PendingData]) # asset -> value


@deploy
def __init__(
    _ripeHq: address,
    _minTimeLock: uint256,
    _maxTimeLock: uint256,
    _initialTimeLock: uint256,
    _expiration: uint256,
):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    timeLock.__init__(_minTimeLock, _maxTimeLock, _initialTimeLock, _expiration)


# add thing


@external
def addThing(_asset: address, _value: uint256):
    assert gov._canGovern(msg.sender) # dev: no perms

    aid: uint256 = timeLock._initiateAction()
    self.pendingData[_asset] = PendingData(
        actionId=aid,
        value=_value,
    )


# confirm thing


@external
def confirmThing(_asset: address):
    assert gov._canGovern(msg.sender) # dev: no perms

    d: PendingData = self.pendingData[_asset]
    assert timeLock._confirmAction(d.actionId) # dev: time lock not reached

    # save new feed config
    self.data[_asset] = d.value
    self.pendingData[_asset] = empty(PendingData)


# cancel thing


@external
def cancelThing(_asset: address):
    assert gov._canGovern(msg.sender) # dev: no perms

    d: PendingData = self.pendingData[_asset]
    assert timeLock._cancelAction(d.actionId) # dev: cannot cancel action
    self.pendingData[_asset] = empty(PendingData)
