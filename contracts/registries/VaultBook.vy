#        _          _       _             _                  _           _                _               _            _            _        
#       /\ \    _ / /\     / /\          /\_\               _\ \        /\ \             / /\            /\ \         /\ \         /\_\      
#       \ \ \  /_/ / /    / /  \        / / /         _    /\__ \       \_\ \           / /  \          /  \ \       /  \ \       / / /  _   
#        \ \ \ \___\/    / / /\ \       \ \ \__      /\_\ / /_ \_\      /\__ \         / / /\ \        / /\ \ \     / /\ \ \     / / /  /\_\ 
#        / / /  \ \ \   / / /\ \ \       \ \___\    / / // / /\/_/     / /_ \ \       / / /\ \ \      / / /\ \ \   / / /\ \ \   / / /__/ / / 
#        \ \ \   \_\ \ / / /  \ \ \       \__  /   / / // / /         / / /\ \ \     / / /\ \_\ \    / / /  \ \_\ / / /  \ \_\ / /\_____/ /  
#         \ \ \  / / // / /___/ /\ \      / / /   / / // / /         / / /  \/_/    / / /\ \ \___\  / / /   / / // / /   / / // /\_______/   
#          \ \ \/ / // / /_____/ /\ \    / / /   / / // / / ____    / / /          / / /  \ \ \__/ / / /   / / // / /   / / // / /\ \ \      
#           \ \ \/ // /_________/\ \ \  / / /___/ / // /_/_/ ___/\ / / /          / / /____\_\ \  / / /___/ / // / /___/ / // / /  \ \ \     
#            \ \  // / /_       __\ \_\/ / /____\/ //_______/\__\//_/ /          / / /__________\/ / /____\/ // / /____\/ // / /    \ \ \    
#             \_\/ \_\___\     /____/_/\/_________/ \_______\/    \_\/           \/_____________/\/_________/ \/_________/ \/_/      \_\_\   

#     ╔═══════════════════════════════════╗
#     ║  ** Vault Book **                 ║
#     ║  Registry for all deposit vaults  ║
#     ╚═══════════════════════════════════╝

# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026

# @version 0.4.3

implements: Department

exports: gov.__interface__
exports: registry.__interface__
exports: addys.__interface__
exports: deptBasics.__interface__

initializes: gov
initializes: registry[gov := gov]
initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.LocalGov as gov
import contracts.registries.modules.AddressRegistry as registry
import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics

from interfaces import Vault
from interfaces import Department

interface Ledger:
    def didGetRewardsFromStabClaims(_amount: uint256): nonpayable
    def ripeAvailForRewards() -> uint256: view

interface RipeToken:
    def mint(_to: address, _amount: uint256): nonpayable

interface MissionControl:
    def isStabVaultId(_vaultId: uint256) -> bool: view
    def isRipeGovVaultId(_vaultId: uint256) -> bool: view

interface RipeGovVault:
    def totalGovPoints() -> uint256: view

@deploy
def __init__(
    _ripeHq: address,
    _tempGov: address,
    _minRegistryTimeLock: uint256,
    _maxRegistryTimeLock: uint256,
):
    gov.__init__(_ripeHq, _tempGov, 0, 0, 0)
    registry.__init__(_minRegistryTimeLock, _maxRegistryTimeLock, 0, "VaultBook.vy")
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, True) # can mint ripe only


@view
@external
def isVaultBookAddr(_addr: address) -> bool:
    return registry._isValidAddr(_addr)


############
# Registry #
############


# new address


@external
def startAddNewAddressToRegistry(_addr: address, _description: String[64]) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._startAddNewAddressToRegistry(_addr, _description)


@external
def confirmNewAddressToRegistry(_addr: address) -> uint256:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._confirmNewAddressToRegistry(_addr)


@external
def cancelNewAddressToRegistry(_addr: address) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._cancelNewAddressToRegistry(_addr)


# address update


@external
def startAddressUpdateToRegistry(_regId: uint256, _newAddr: address) -> bool:
    assert not self._doesVaultIdHaveAnyFunds(_regId) # dev: vault has funds

    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._startAddressUpdateToRegistry(_regId, _newAddr)


@external
def confirmAddressUpdateToRegistry(_regId: uint256) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    assert not self._doesVaultIdHaveAnyFunds(_regId) # dev: vault has funds
    return registry._confirmAddressUpdateToRegistry(_regId)


@external
def cancelAddressUpdateToRegistry(_regId: uint256) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._cancelAddressUpdateToRegistry(_regId)


# address disable


@external
def startAddressDisableInRegistry(_regId: uint256) -> bool:
    assert not self._doesVaultIdHaveAnyFunds(_regId) # dev: vault has funds

    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._startAddressDisableInRegistry(_regId)


@external
def confirmAddressDisableInRegistry(_regId: uint256) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    assert not self._doesVaultIdHaveAnyFunds(_regId) # dev: vault has funds
    return registry._confirmAddressDisableInRegistry(_regId)


@external
def cancelAddressDisableInRegistry(_regId: uint256) -> bool:
    assert self._canPerformAction(msg.sender) # dev: no perms
    return registry._cancelAddressDisableInRegistry(_regId)


# check if vault has funds


@view
@internal
def _doesVaultIdHaveAnyFunds(_vaultId: uint256) -> bool:
    vaultAddr: address = registry._getAddr(_vaultId)
    if vaultAddr == empty(address):
        return False
    if staticcall Vault(vaultAddr).doesVaultHaveAnyFunds():
        return True

    missionControl: address = addys._getMissionControlAddr()
    if missionControl != empty(address) and staticcall MissionControl(missionControl).isRipeGovVaultId(_vaultId):
        # Zero-share governance points cannot be migrated; clear them before
        # retiring or repointing a historical RipeGov vault.
        return staticcall RipeGovVault(vaultAddr).totalGovPoints() != 0
    return False


######################
# Stab Claim Rewards #
######################


# pass thru from stability pool


@external
def mintRipeForStabPoolClaims(_amount: uint256, _ripeToken: address, _ledger: address) -> bool:
    vaultId: uint256 = registry._getRegId(msg.sender)
    assert vaultId != 0 # dev: no perms

    missionControl: address = addys._getMissionControlAddr()
    assert staticcall MissionControl(missionControl).isStabVaultId(vaultId) # dev: not stab vault

    ripeToken: address = addys._getRipeToken()
    ledger: address = addys._getLedgerAddr()
    assert _ripeToken == ripeToken # dev: invalid ripe token
    assert _ledger == ledger # dev: invalid ledger
    assert _amount <= staticcall Ledger(ledger).ripeAvailForRewards() # dev: insufficient rewards

    extcall RipeToken(ripeToken).mint(msg.sender, _amount)
    extcall Ledger(ledger).didGetRewardsFromStabClaims(_amount)
    return True


#############
# Utilities #
#############


@view
@internal
def _canPerformAction(_caller: address) -> bool:
    return gov._canGovern(_caller) and not deptBasics.isPaused
