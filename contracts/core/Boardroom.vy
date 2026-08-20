# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026

# @version 0.4.3

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department

interface MissionControl:
    def isRipeGovVaultId(_vaultId: uint256) -> bool: view

interface VaultBook:
    def getRegId(_vaultAddr: address) -> uint256: view


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting

    # NOTE: This is a temporary Boardroom contract. Real one coming soon.


@external
def govPowerDidChangeForUser(_user: address, _userGovPoints: uint256, _totalGovPoints: uint256):
    vaultId: uint256 = staticcall VaultBook(addys._getVaultBookAddr()).getRegId(msg.sender)
    assert vaultId != 0 # dev: no perms
    assert staticcall MissionControl(addys._getMissionControlAddr()).isRipeGovVaultId(vaultId) # dev: no perms
