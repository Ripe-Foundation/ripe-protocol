# @version 0.4.1

exports: gov.__interface__
exports: registry.__interface__

initializes: gov
initializes: registry[gov := gov]

import contracts.modules.LocalGov as gov
import contracts.modules.AddressRegistry as registry
from interfaces import Department

struct HqConfig:
    canMintGreen: bool
    canMintRipe: bool
    canSetTokenBlacklist: bool

struct PendingHqConfig:
    newHqConfig: HqConfig
    initiatedBlock: uint256
    confirmBlock: uint256

event HqConfigChangeInitiated:
    regId: uint256
    canMintGreen: bool
    canMintRipe: bool
    canSetTokenBlacklist: bool
    confirmBlock: uint256

event TokensSet:
    greenToken: address
    ripeToken: address

event CanSetTokenBlacklistSet:
    addyId: uint256
    canSet: bool

# hq config
hqConfig: public(HashMap[uint256, HqConfig])
pendingHqConfig: public(HashMap[uint256, PendingHqConfig])

# tokens
greenToken: public(address)
ripeToken: public(address)
tokensAreSet: public(bool)



# # green minting
# isGreenMinter: public(HashMap[uint256, bool]) # addy id -> can mint green
# pendingGreenMinter: public(HashMap[address, bool]) # addr -> pending can mint green

# # ripe minting
# isRipeMinter: public(HashMap[uint256, bool]) # addy id -> can mint ripe
# pendingRipeMinter: public(HashMap[address, bool]) # addr -> pending can mint ripe

# # blacklist
# canIdSetTokenBlacklist: public(HashMap[uint256, bool]) # addy id -> can set blacklist


@deploy
def __init__(
    _initialGov: address,
    _minGovTimeLock: uint256,
    _maxGovTimeLock: uint256,
    _minRegistryTimeLock: uint256,
    _maxRegistryTimeLock: uint256,
):
    gov.__init__(empty(address), _initialGov, _minGovTimeLock, _maxGovTimeLock, 0)
    registry.__init__(_minRegistryTimeLock, _maxRegistryTimeLock, 0, "RipeHq.vy")


#####################
# Hq Config Changes #
#####################


@view
@external
def hasPendingHqConfigChange() -> bool:
    return self.pendingHqConfig.confirmBlock != 0


@internal
def _isValidHqConfig(
    _regId: uint256,
    _hqConfig: HqConfig,
) -> bool:

    # invalid reg id
    if not registry._isValidRegId(_regId):
        return False

    # no reg addr
    addr: address = registry._getRegAddr(_regId)
    if addr == empty(address):
        return False

    # two-factor auth on minting
    if _hqConfig.canMintGreen and not Department(addr).canMintGreen():
        return False
    if _hqConfig.canMintRipe and not Department(addr).canMintRipe():
        return False

    return True


# start hq config change


@external
def initiateHqConfigChange(
    _regId: uint256,
    _canMintGreen: bool,
    _canMintRipe: bool,
    _canSetTokenBlacklist: bool,
):
    assert msg.sender == gov.governance # dev: no perms

    hqConfig: HqConfig = HqConfig(
        canMintGreen= _canMintGreen,
        canMintRipe= _canMintRipe,
        canSetTokenBlacklist= _canSetTokenBlacklist,
    )
    assert self._isValidHqConfig(_regId, hqConfig) # dev: invalid hq config

    # set pending hq config
    confirmBlock: uint256 = block.number + registry.registryChangeTimeLock
    self.pendingHqConfig[_regId] = PendingHqConfig(
        newHqConfig= hqConfig,
        initiatedBlock= block.number,
        confirmBlock= confirmBlock,
    )
    log HqConfigChangeInitiated(regId=_regId, canMintGreen=_canMintGreen, canMintRipe=_canMintRipe, canSetTokenBlacklist=_canSetTokenBlacklist, confirmBlock=confirmBlock)


# confirm gov change


@external
def confirmHqConfigChange(_regId: uint256):
    assert msg.sender == gov.governance # dev: no perms

    data: PendingHqConfig = self.pendingHqConfig[_regId]
    assert data.confirmBlock != 0 and block.number >= data.confirmBlock # dev: time lock not reached

    # check permissions
    if data.newGov != empty(address):
        assert msg.sender == data.newGov # dev: only new gov can confirm
    else:
        assert self._canGovern(msg.sender) # dev: no perms
        assert not self._isRipeHqGov() # dev: ripe hq cannot set 0x0

    # set new governance
    prevGov: address = self.governance
    self.governance = data.newGov
    self.pendingGov = empty(PendingGovernance)
    log GovChangeConfirmed(prevGov=prevGov, newGov=data.newGov, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock)


# cancel gov change


@external
def cancelGovernanceChange():
    assert self._canGovern(msg.sender) # dev: no perms
    data: PendingGovernance = self.pendingGov
    assert data.confirmBlock != 0 # dev: no pending change
    self.pendingGov = empty(PendingGovernance)
    log GovChangeCancelled(cancelledGov=data.newGov, initiatedBlock=data.initiatedBlock, confirmBlock=data.confirmBlock)




















############
# New Addy #
############


@external
def registerNewAddy(
    _addr: address,
    _description: String[64],
    _canMintGreen: bool = False,
    _canMintRipe: bool = False,
) -> bool:
    assert msg.sender == gov.governance # dev: no perms

    isPending: bool = registry._registerNewAddy(_addr, _description)
    if isPending:
        if _canMintGreen:
            self.pendingGreenMinter[_addr] = True
        if _canMintRipe:
            self.pendingRipeMinter[_addr] = True

    # TODO: log
    return isPending


@external
def confirmNewAddy(_addr: address) -> uint256:
    assert msg.sender == gov.governance # dev: no perms
    addyId: uint256 = registry._confirmNewAddy(_addr)
    if addyId == 0:
        self._cancelPendingAddy(_addr)
        return 0

    if self.pendingGreenMinter[_addr]:
        self.isGreenMinter[addyId] = True
        self.pendingGreenMinter[_addr] = False

    if self.pendingRipeMinter[_addr]:
        self.isRipeMinter[addyId] = True
        self.pendingRipeMinter[_addr] = False

    # TODO: log
    return addyId


@external
def cancelPendingNewAddy(_addr: address) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    self._cancelPendingAddy(_addr)
    # TODO: log
    return registry._cancelPendingNewAddy(_addr)


@internal
def _cancelPendingAddy(_addr: address):
    if self.pendingGreenMinter[_addr]:
        self.pendingGreenMinter[_addr] = False
    if self.pendingRipeMinter[_addr]:
        self.pendingRipeMinter[_addr] = False


###############
# Update Addy #
###############


@external
def updateAddyAddr(_addyId: uint256, _newAddr: address) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._updateAddyAddr(_addyId, _newAddr)


@external
def confirmAddyUpdate(_addyId: uint256) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._confirmAddyUpdate(_addyId)


@external
def cancelPendingAddyUpdate(_addyId: uint256) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._cancelPendingAddyUpdate(_addyId)


################
# Disable Addy #
################


@external
def disableAddyAddr(_addyId: uint256) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._disableAddyAddr(_addyId)


@external
def confirmAddyDisable(_addyId: uint256) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._confirmAddyDisable(_addyId)


@external
def cancelPendingAddyDisable(_addyId: uint256) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._cancelPendingAddyDisable(_addyId)


################
# Change Delay #
################


@external
def setAddyChangeDelay(_numBlocks: uint256) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._setAddyChangeDelay(_numBlocks)


@external
def setAddyChangeDelayToMin() -> bool:
    assert msg.sender == gov.governance # dev: no perms
    return registry._setAddyChangeDelay(registry.MIN_ADDY_CHANGE_DELAY)


##########
# Tokens #
##########


@external
def setTokens(_greenToken: address, _ripeToken: address) -> bool:
    assert msg.sender == gov.governance # dev: no perms

    assert not self.tokensAreSet # dev: tokens already set
    assert _greenToken != _ripeToken # dev: invalid tokens
    assert empty(address) not in [_greenToken, _ripeToken] # dev: cannot do 0x0
    assert _greenToken.is_contract and _ripeToken.is_contract # dev: not contracts 

    self.greenToken = _greenToken
    self.ripeToken = _ripeToken
    self.tokensAreSet = True

    log TokensSet(greenToken=_greenToken, ripeToken=_ripeToken)
    return True


###########
# Minting #
###########


@view
@external
def canMintGreen(_addr: address) -> bool:
    addyId: uint256 = registry._getAddyId(_addr)
    return self.isGreenMinter[addyId]


@view
@external
def canMintRipe(_addr: address) -> bool:
    addyId: uint256 = registry._getAddyId(_addr)
    return self.isRipeMinter[addyId]


#############
# Blacklist #
#############


@external
def setCanSetTokenBlacklist(_addyId: uint256, _canSetTokenBlacklist: bool) -> bool:
    assert msg.sender == gov.governance # dev: no perms
    assert registry._isValidAddyId(_addyId) # dev: invalid addy id
    self.canIdSetTokenBlacklist[_addyId] = _canSetTokenBlacklist
    log CanSetTokenBlacklistSet(addyId=_addyId, canSet=_canSetTokenBlacklist)
    return True


@view
@external
def canSetTokenBlacklist(_addr: address) -> bool:
    addyId: uint256 = registry._getAddyId(_addr)
    return self.canIdSetTokenBlacklist[addyId]
