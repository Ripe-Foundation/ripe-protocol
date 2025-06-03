# @version 0.4.1

exports: gov.__interface__
exports: registry.__interface__

initializes: gov
initializes: registry[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.registries.modules.AddressRegistry as registry

from interfaces import Department
from ethereum.ercs import IERC20

struct HqConfig:
    description: String[64]
    canMintGreen: bool
    canMintRipe: bool
    canSetTokenBlacklist: bool
    canModifyMissionControl: bool

struct PendingHqConfig:
    newHqConfig: HqConfig
    initiatedBlock: uint256
    confirmBlock: uint256

event HqConfigChangeInitiated:
    regId: uint256
    description: String[64]
    canMintGreen: bool
    canMintRipe: bool
    canSetTokenBlacklist: bool
    canModifyMissionControl: bool
    confirmBlock: uint256

event HqConfigChangeConfirmed:
    regId: uint256
    description: String[64]
    canMintGreen: bool
    canMintRipe: bool
    canSetTokenBlacklist: bool
    canModifyMissionControl: bool
    initiatedBlock: uint256
    confirmBlock: uint256

event HqConfigChangeCancelled:
    regId: uint256
    description: String[64]
    canMintGreen: bool
    canMintRipe: bool
    canSetTokenBlacklist: bool
    canModifyMissionControl: bool
    initiatedBlock: uint256
    confirmBlock: uint256

event RipeHqFundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

# hq config
hqConfig: public(HashMap[uint256, HqConfig]) # reg id -> hq config
pendingHqConfig: public(HashMap[uint256, PendingHqConfig]) # reg id -> pending hq config

MAX_RECOVER_ASSETS: constant(uint256) = 20


@deploy
def __init__(
    _greenToken: address,
    _savingsGreen: address,
    _ripeToken: address,
    _initialGov: address,
    _minGovTimeLock: uint256,
    _maxGovTimeLock: uint256,
    _minRegistryTimeLock: uint256,
    _maxRegistryTimeLock: uint256,
):
    gov.__init__(empty(address), _initialGov, _minGovTimeLock, _maxGovTimeLock, 0)
    registry.__init__(_minRegistryTimeLock, _maxRegistryTimeLock, 0, "RipeHq.vy")

    # green token
    assert registry._startAddNewAddressToRegistry(_greenToken, "Green Token") # dev: failed to register green token
    assert registry._confirmNewAddressToRegistry(_greenToken) == 1 # dev: failed to confirm green token

    # savings green
    assert registry._startAddNewAddressToRegistry(_savingsGreen, "Savings Green") # dev: failed to register savings green
    assert registry._confirmNewAddressToRegistry(_savingsGreen) == 2 # dev: failed to confirm savings green

    # ripe token
    assert registry._startAddNewAddressToRegistry(_ripeToken, "Ripe Token") # dev: failed to register ripe token
    assert registry._confirmNewAddressToRegistry(_ripeToken) == 3 # dev: failed to confirm ripe token


############
# Registry #
############


# new address


@external
def startAddNewAddressToRegistry(_addr: address, _description: String[64]) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._startAddNewAddressToRegistry(_addr, _description)


@external
def confirmNewAddressToRegistry(_addr: address) -> uint256:
    assert msg.sender == gov.governance # dev: no perms
    return registry._confirmNewAddressToRegistry(_addr)


@external
def cancelNewAddressToRegistry(_addr: address) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._cancelNewAddressToRegistry(_addr)


# address update


@external
def startAddressUpdateToRegistry(_regId: uint256, _newAddr: address) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._startAddressUpdateToRegistry(_regId, _newAddr)


@external
def confirmAddressUpdateToRegistry(_regId: uint256) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._confirmAddressUpdateToRegistry(_regId)


@external
def cancelAddressUpdateToRegistry(_regId: uint256) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._cancelAddressUpdateToRegistry(_regId)


# address disable


@external
def startAddressDisableInRegistry(_regId: uint256) -> bool:
    assert not self._isTokenId(_regId) # dev: cannot disable token

    assert msg.sender == gov.governance # dev: no perms
    return registry._startAddressDisableInRegistry(_regId)


@external
def confirmAddressDisableInRegistry(_regId: uint256) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._confirmAddressDisableInRegistry(_regId)


@external
def cancelAddressDisableInRegistry(_regId: uint256) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._cancelAddressDisableInRegistry(_regId)


#############
# Hq Config #
#############


@view
@external
def hasPendingHqConfigChange(_regId: uint256) -> bool:
    return self.pendingHqConfig[_regId].confirmBlock != 0


# start hq config change


@external
def initiateHqConfigChange(
    _regId: uint256,
    _canMintGreen: bool,
    _canMintRipe: bool,
    _canSetTokenBlacklist: bool,
    _canModifyMissionControl: bool,
):
    assert msg.sender == gov.governance # dev: no perms

    assert self._isValidHqConfig(_regId, _canMintGreen, _canMintRipe) # dev: invalid hq config
    hqConfig: HqConfig = HqConfig(
        description= registry._getAddrDescription(_regId),
        canMintGreen= _canMintGreen,
        canMintRipe= _canMintRipe,
        canSetTokenBlacklist= _canSetTokenBlacklist,
        canModifyMissionControl= _canModifyMissionControl,
    )

    # set pending hq config
    confirmBlock: uint256 = block.number + registry.registryChangeTimeLock
    self.pendingHqConfig[_regId] = PendingHqConfig(
        newHqConfig= hqConfig,
        initiatedBlock= block.number,
        confirmBlock= confirmBlock,
    )
    log HqConfigChangeInitiated(
        regId=_regId,
        description=hqConfig.description,
        canMintGreen=_canMintGreen,
        canMintRipe=_canMintRipe,
        canSetTokenBlacklist=_canSetTokenBlacklist,
        canModifyMissionControl=_canModifyMissionControl,
        confirmBlock=confirmBlock,
    )


# confirm hq config change


@external
def confirmHqConfigChange(_regId: uint256) -> bool:
    assert msg.sender == gov.governance # dev: no perms

    data: PendingHqConfig = self.pendingHqConfig[_regId]
    assert data.confirmBlock != 0 and block.number >= data.confirmBlock # dev: time lock not reached

    # invalid hq config
    newConfig: HqConfig = data.newHqConfig
    if not self._isValidHqConfig(_regId, newConfig.canMintGreen, newConfig.canMintRipe):
        self.pendingHqConfig[_regId] = empty(PendingHqConfig)
        return False

    # set hq config
    self.hqConfig[_regId] = newConfig
    self.pendingHqConfig[_regId] = empty(PendingHqConfig)

    log HqConfigChangeConfirmed(
        regId=_regId,
        description=newConfig.description,
        canMintGreen=newConfig.canMintGreen,
        canMintRipe=newConfig.canMintRipe,
        canSetTokenBlacklist=newConfig.canSetTokenBlacklist,
        canModifyMissionControl=newConfig.canModifyMissionControl,
        initiatedBlock=data.initiatedBlock,
        confirmBlock=data.confirmBlock,
    )
    return True


# cancel hq config change


@external
def cancelHqConfigChange(_regId: uint256) -> bool:
    assert msg.sender == gov.governance # dev: no perms

    data: PendingHqConfig = self.pendingHqConfig[_regId]
    assert data.confirmBlock != 0 # dev: no pending change

    self.pendingHqConfig[_regId] = empty(PendingHqConfig)
    log HqConfigChangeCancelled(
        regId=_regId,
        description=data.newHqConfig.description,
        canMintGreen=data.newHqConfig.canMintGreen,
        canMintRipe=data.newHqConfig.canMintRipe,
        canSetTokenBlacklist=data.newHqConfig.canSetTokenBlacklist,
        canModifyMissionControl=data.newHqConfig.canModifyMissionControl,
        initiatedBlock=data.initiatedBlock,
        confirmBlock=data.confirmBlock
    )
    return True


# validation


@external
def isValidHqConfig(
    _regId: uint256,
    _canMintGreen: bool,
    _canMintRipe: bool,
) -> bool:
    return self._isValidHqConfig(_regId, _canMintGreen, _canMintRipe)


@internal
def _isValidHqConfig(
    _regId: uint256,
    _canMintGreen: bool,
    _canMintRipe: bool,
) -> bool:

    # tokens cannot mint, cannot set their own blacklist, cannot modify mission control
    if self._isTokenId(_regId):
        return False

    # invalid reg id
    if not registry._isValidRegId(_regId):
        return False

    # no addr
    addr: address = registry._getAddr(_regId)
    if addr == empty(address):
        return False

    # two-factor auth on minting
    if _canMintGreen and not staticcall Department(addr).canMintGreen():
        return False

    if _canMintRipe and not staticcall Department(addr).canMintRipe():
        return False

    return True


@view
@internal
def _isTokenId(_regId: uint256) -> bool:
    return _regId in [1, 2, 3]


##########
# Tokens #
##########


@view
@external
def greenToken() -> address:
    return registry._getAddr(1)


@view
@external
def savingsGreen() -> address:
    return registry._getAddr(2)


@view
@external
def ripeToken() -> address:
    return registry._getAddr(3)


@view
@external
def canMintGreen(_addr: address) -> bool:
    if _addr == empty(address):
        return False
    regId: uint256 = registry._getRegId(_addr)
    if regId == 0 or not self.hqConfig[regId].canMintGreen:
        return False
    return staticcall Department(_addr).canMintGreen()


@view
@external
def canMintRipe(_addr: address) -> bool:
    if _addr == empty(address):
        return False
    regId: uint256 = registry._getRegId(_addr)
    if regId == 0 or not self.hqConfig[regId].canMintRipe:
        return False
    return staticcall Department(_addr).canMintRipe()


@view
@external
def canSetTokenBlacklist(_addr: address) -> bool:
    if _addr == empty(address):
        return False
    regId: uint256 = registry._getRegId(_addr)
    if regId == 0:
        return False
    return self.hqConfig[regId].canSetTokenBlacklist


@view
@external
def canModifyMissionControl(_addr: address) -> bool:
    if _addr == empty(address):
        return False
    regId: uint256 = registry._getRegId(_addr)
    if regId == 0:
        return False
    return self.hqConfig[regId].canModifyMissionControl


############
# Recovery #
############


@external
def recoverFunds(_recipient: address, _asset: address):
    assert msg.sender == gov.governance # dev: no perms
    self._recoverFunds(_recipient, _asset)


@external
def recoverFundsMany(_recipient: address, _assets: DynArray[address, MAX_RECOVER_ASSETS]):
    assert msg.sender == gov.governance # dev: no perms
    for a: address in _assets:
        self._recoverFunds(_recipient, a)


@internal
def _recoverFunds(_recipient: address, _asset: address):
    assert empty(address) not in [_recipient, _asset] # dev: invalid recipient or asset
    balance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    assert balance != 0 # dev: nothing to recover

    assert extcall IERC20(_asset).transfer(_recipient, balance, default_return_value=True) # dev: recovery failed
    log RipeHqFundsRecovered(asset=_asset, recipient=_recipient, balance=balance)