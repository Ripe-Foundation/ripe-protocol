# @version 0.4.1

exports: gov.__interface__
exports: registry.__interface__

initializes: gov
initializes: registry[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.registries.modules.AddressRegistry as registry


@deploy
def __init__(
    _ripeHq: address,
    _initialTimeLock: uint256,
    _minRegistryTimeLock: uint256,
    _maxRegistryTimeLock: uint256,
):
    gov.__init__(_ripeHq, empty(address), 0, 0, 0)
    registry.__init__(_minRegistryTimeLock, _maxRegistryTimeLock, _initialTimeLock, "MockRegistry.vy")


############
# Registry #
############


# new address


@external
def startAddNewAddressToRegistry(_addr: address, _description: String[64]) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._startAddNewAddressToRegistry(_addr, _description)


@external
def confirmNewAddressToRegistry(_addr: address) -> uint256:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._confirmNewAddressToRegistry(_addr)


@external
def cancelNewAddressToRegistry(_addr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelNewAddressToRegistry(_addr)


# address update


@external
def startAddressUpdateToRegistry(_regId: uint256, _newAddr: address) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._startAddressUpdateToRegistry(_regId, _newAddr)


@external
def confirmAddressUpdateToRegistry(_regId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._confirmAddressUpdateToRegistry(_regId)


@external
def cancelAddressUpdateToRegistry(_regId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelAddressUpdateToRegistry(_regId)


# address disable


@external
def startAddressDisableInRegistry(_regId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._startAddressDisableInRegistry(_regId)


@external
def confirmAddressDisableInRegistry(_regId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._confirmAddressDisableInRegistry(_regId)


@external
def cancelAddressDisableInRegistry(_regId: uint256) -> bool:
    assert gov._canGovern(msg.sender) # dev: no perms
    return registry._cancelAddressDisableInRegistry(_regId)
