# @version 0.4.1

initializes: gov
initializes: registry

exports: gov.__interface__
exports: registry.__interface__

import contracts.modules.LocalGov as gov
import contracts.modules.Registry as registry

event TokensSet:
    green: address
    ripe: address

# tokens
green: public(address)
ripe: public(address)
tokensAreSet: public(bool)

# green minting
isGreenMinter: public(HashMap[uint256, bool]) # addy id -> can mint green
pendingGreenMinter: public(HashMap[address, bool]) # addr -> pending can mint green

# ripe minting
isRipeMinter: public(HashMap[uint256, bool]) # addy id -> can mint ripe
pendingRipeMinter: public(HashMap[address, bool]) # addr -> pending can mint ripe


@deploy
def __init__(
    _initialGov: address,
    _minGovChangeDelay: uint256,
    _maxGovChangeDelay: uint256,
    _minRegistryChangeDelay: uint256,
    _maxRegistryChangeDelay: uint256,
):
    # initialize gov
    gov.__init__(_initialGov, empty(address), _minGovChangeDelay, _maxGovChangeDelay)

    # initialize registry
    registry.__init__(_minRegistryChangeDelay, _maxRegistryChangeDelay, "AddyRegistry.vy")


# TEMPORARY
# TELLER: 1
# LEDGER: 2
# VAULT_BOOK: 3
# VALIDATOR: 4
# LOOTBOX: 5
# CONTROL_ROOM: 6
# PRICE_DESK: 7
# CREDIT_ENGINE: 8


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
def setTokens(_green: address, _ripe: address) -> bool:
    assert msg.sender == gov.governance # dev: no perms

    assert not self.tokensAreSet # dev: tokens already set
    assert _green != _ripe # dev: invalid tokens
    assert empty(address) not in [_green, _ripe] # dev: cannot do 0x0
    assert _green.is_contract and _ripe.is_contract # dev: not contracts 

    self.green = _green
    self.ripe = _ripe
    self.tokensAreSet = True

    log TokensSet(green=_green, ripe=_ripe)
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
