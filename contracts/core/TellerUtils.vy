#                     ___                                    ___          ___     
#            ___     /  /\                                  /  /\        /  /\    
#           /  /\   /  /:/_                                /  /:/_      /  /::\   
#          /  /:/  /  /:/ /\   ___     ___  ___     ___   /  /:/ /\    /  /:/\:\  
#         /  /:/  /  /:/ /:/_ /__/\   /  /\/__/\   /  /\ /  /:/ /:/_  /  /:/~/:/  
#        /  /::\ /__/:/ /:/ /\\  \:\ /  /:/\  \:\ /  /://__/:/ /:/ /\/__/:/ /:/___
#       /__/:/\:\\  \:\/:/ /:/ \  \:\  /:/  \  \:\  /:/ \  \:\/:/ /:/\  \:\/:::::/
#       \__\/  \:\\  \::/ /:/   \  \:\/:/    \  \:\/:/   \  \::/ /:/  \  \::/~~~~ 
#            \  \:\\  \:\/:/     \  \::/      \  \::/     \  \:\/:/    \  \:\     
#             \__\/ \  \::/       \__\/        \__\/       \  \::/      \  \:\    
#                    \__\/                                  \__\/        \__\/    
#
#     ╔═══════════════════════════════════════════════════════════════════════╗
#     ║  ** Teller **                                                         ║
#     ║  Handles deposits, withdrawals, and entry-point for all user actions  ║
#     ╚═══════════════════════════════════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department
from interfaces import Vault

from ethereum.ercs import IERC20

interface MissionControl:
    def getTellerDepositConfig(_vaultId: uint256, _asset: address, _user: address) -> TellerDepositConfig: view
    def getFirstVaultIdForAsset(_asset: address) -> uint256: view
    def underscoreRegistry() -> address: view

interface AddressRegistry:
    def getRegId(_addr: address) -> uint256: view
    def getAddr(_regId: uint256) -> address: view
    def isValidAddr(_addr: address) -> bool: view

interface CreditEngine:
    def getMaxWithdrawableForAsset(_user: address, _vaultId: uint256, _asset: address, _vaultAddr: address = empty(address), _a: addys.Addys = empty(addys.Addys)) -> uint256: view

interface VaultRegistry:
    def isEarnVault(_vaultAddr: address) -> bool: view

interface UnderscoreLedger:
    def isUserWallet(_addr: address) -> bool: view

interface UnderscoreWallet:
    def walletConfig() -> address: view

interface UnderscoreWalletConfig:
    def owner() -> address: view

struct DepositLedgerData:
    isParticipatingInVault: bool
    numUserVaults: uint256

struct TellerDepositConfig:
    canDepositGeneral: bool
    canDepositAsset: bool
    doesVaultSupportAsset: bool
    isUserAllowed: bool
    perUserDepositLimit: uint256
    globalDepositLimit: uint256
    perUserMaxAssetsPerVault: uint256
    perUserMaxVaults: uint256
    canAnyoneDeposit: bool
    minDepositBalance: uint256

struct TellerWithdrawConfig:
    canWithdrawGeneral: bool
    canWithdrawAsset: bool
    isUserAllowed: bool
    canWithdrawForUser: bool
    minDepositBalance: uint256

UNDERSCORE_LEDGER_ID: constant(uint256) = 1
UNDERSCORE_LEGOBOOK_ID: constant(uint256) = 3
UNDERSCORE_VAULT_REGISTRY_ID: constant(uint256) = 10


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting


######################
# Deposit Validation #
######################


@view
@external
def validateOnDeposit(
    _asset: address,
    _amount: uint256,
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _depositor: address,
    _didAlreadyValidateSender: bool,
    _areFundsHereAlready: bool,
    _d: DepositLedgerData,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    a: addys.Addys = addys._getAddys(_a)

    config: TellerDepositConfig = staticcall MissionControl(a.missionControl).getTellerDepositConfig(_vaultId, _asset, _user)
    assert config.canDepositGeneral # dev: protocol deposits disabled
    assert config.canDepositAsset # dev: asset deposits disabled
    assert config.doesVaultSupportAsset # dev: vault does not support asset
    assert config.isUserAllowed # dev: user not on whitelist

    # trusted depositor
    isRipeDepartment: bool = addys._isValidRipeAddr(_depositor)

    # make sure depositor is allowed to deposit for user
    if not _didAlreadyValidateSender and _user != _depositor and not config.canAnyoneDeposit:
        assert isRipeDepartment or self._isUnderscoreWalletOwner(_user, _depositor, staticcall MissionControl(a.missionControl).underscoreRegistry()) # dev: cannot deposit for user

    # avail amount
    holder: address = _depositor
    if _areFundsHereAlready:
        holder = a.teller
    amount: uint256 = min(_amount, staticcall IERC20(_asset).balanceOf(holder))
    assert amount != 0 # dev: cannot deposit 0

    # if depositing from ripe dept, skip these limits
    if isRipeDepartment:
        return amount
    
    # vault data
    vd: Vault.VaultDataOnDeposit = staticcall Vault(_vaultAddr).getVaultDataOnDeposit(_user, _asset)

    # check max vaults, max assets per vault
    if not _d.isParticipatingInVault:
        assert _d.numUserVaults < config.perUserMaxVaults # dev: reached max vaults

    elif not vd.hasPosition:
        assert vd.numAssets < config.perUserMaxAssetsPerVault # dev: reached max assets per vault

    # per user deposit limit
    availPerUserDeposit: uint256 = self._getAvailPerUserDepositLimit(vd.userBalance, config.perUserDepositLimit)
    assert availPerUserDeposit != 0 # dev: cannot deposit, reached user limit
    amount = min(amount, availPerUserDeposit)

    # global deposit limit
    availGlobalDeposit: uint256 = self._getAvailGlobalDepositLimit(vd.totalBalance, config.globalDepositLimit)
    assert availGlobalDeposit != 0 # dev: cannot deposit, reached global limit
    amount = min(amount, availGlobalDeposit)

    # min balance
    assert amount + vd.userBalance >= config.minDepositBalance # dev: too small a balance

    return amount


# per user deposit limit


@view 
@internal 
def _getAvailPerUserDepositLimit(_userDepositBal: uint256, _perUserDepositLimit: uint256) -> uint256:
    if _perUserDepositLimit == max_value(uint256):
        return max_value(uint256)
    availDeposits: uint256 = 0
    if _perUserDepositLimit > _userDepositBal:
        availDeposits = _perUserDepositLimit - _userDepositBal
    return availDeposits


# global deposit limit


@view 
@internal 
def _getAvailGlobalDepositLimit(_totalDepositBal: uint256, _globalDepositLimit: uint256) -> uint256:
    availDeposits: uint256 = 0
    if _globalDepositLimit > _totalDepositBal:
        availDeposits = _globalDepositLimit - _totalDepositBal
    return availDeposits


#########################
# Withdrawal Validation #
#########################


@view
@external
def validateOnWithdrawal(
    _asset: address,
    _amount: uint256,
    _user: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _caller: address,
    _config: TellerWithdrawConfig,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    a: addys.Addys = addys._getAddys(_a)
    assert _amount != 0 # dev: cannot withdraw 0

    assert _config.canWithdrawGeneral # dev: protocol withdrawals disabled
    assert _config.canWithdrawAsset # dev: asset withdrawals disabled
    assert _config.isUserAllowed # dev: user not on whitelist

    # make sure caller is allowed to withdraw for user
    if _user != _caller and not _config.canWithdrawForUser:
        assert self._isUnderscoreWalletOwner(_user, _caller, staticcall MissionControl(a.missionControl).underscoreRegistry()) # dev: not allowed to withdraw for user

    # max withdrawable
    maxWithdrawable: uint256 = staticcall CreditEngine(a.creditEngine).getMaxWithdrawableForAsset(_user, _vaultId, _asset, _vaultAddr, a)
    assert maxWithdrawable != 0 # dev: cannot withdraw anything

    return min(_amount, maxWithdrawable)


##############
# Vault Info #
##############


@view
@external
def getVaultAddrAndId(
    _asset: address,
    _vaultAddr: address,
    _vaultId: uint256,
    _vaultBook: address,
    _missionControl: address,
) -> (address, uint256):
    vaultAddr: address = empty(address)
    vaultId: uint256 = 0

    # if no vault data specified, get first vault id for asset
    if _vaultAddr == empty(address) and _vaultId == 0:
        vaultId = staticcall MissionControl(_missionControl).getFirstVaultIdForAsset(_asset)
        assert vaultId != 0 # dev: invalid asset
        vaultAddr = staticcall AddressRegistry(_vaultBook).getAddr(vaultId)
        assert vaultAddr != empty(address) # dev: invalid vault id

    # vault id
    elif _vaultId != 0:
        vaultAddr = staticcall AddressRegistry(_vaultBook).getAddr(_vaultId)
        assert vaultAddr != empty(address) # dev: invalid vault id
        vaultId = _vaultId
        if _vaultAddr != empty(address):
            assert vaultAddr == _vaultAddr # dev: vault id and vault addr mismatch

    # vault addr
    elif _vaultAddr != empty(address):
        vaultId = staticcall AddressRegistry(_vaultBook).getRegId(_vaultAddr) # dev: invalid vault addr
        assert vaultId != 0 # dev: invalid vault addr
        vaultAddr = _vaultAddr

    return vaultAddr, vaultId


##############
# Underscore #
##############


@view
@external
def isUnderscoreWalletOrVault(_addr: address, _mc: address = empty(address)) -> bool:
    missionControl: address = _mc
    if _mc == empty(address):
        missionControl = addys._getMissionControlAddr()
    underscore: address = staticcall MissionControl(missionControl).underscoreRegistry()
    return self._isUnderscoreWallet(_addr, underscore) or self._isUnderscoreVault(_addr, underscore)


# underscore wallet


@view
@external
def isUnderscoreWallet(_user: address, _mc: address = empty(address)) -> bool:
    missionControl: address = _mc
    if _mc == empty(address):
        missionControl = addys._getMissionControlAddr()
    underscore: address = staticcall MissionControl(missionControl).underscoreRegistry()
    return self._isUnderscoreWallet(_user, underscore)


@view
@internal
def _isUnderscoreWallet(_user: address, _underscore: address) -> bool:
    if _underscore == empty(address):
        return False
    undyLedger: address = staticcall AddressRegistry(_underscore).getAddr(UNDERSCORE_LEDGER_ID)
    if undyLedger == empty(address):
        return False

    # check if user is underscore wallet
    return staticcall UnderscoreLedger(undyLedger).isUserWallet(_user)


# underscore vault check


@view
@external
def isUnderscoreVault(_user: address, _mc: address = empty(address)) -> bool:
    missionControl: address = _mc
    if _mc == empty(address):
        missionControl = addys._getMissionControlAddr()
    underscore: address = staticcall MissionControl(missionControl).underscoreRegistry()
    return self._isUnderscoreVault(_user, underscore)


@view
@internal
def _isUnderscoreVault(_user: address, _underscore: address) -> bool:
    if _underscore == empty(address):
        return False

    # check if underscore vault
    vaultRegistry: address = staticcall AddressRegistry(_underscore).getAddr(UNDERSCORE_VAULT_REGISTRY_ID)
    if vaultRegistry == empty(address):
        return False

    # check if vault is an earn vault
    return staticcall VaultRegistry(vaultRegistry).isEarnVault(_user)


# underscore wallet owner check


@view
@external
def isUnderscoreWalletOwner(_user: address, _caller: address, _mc: address = empty(address)) -> bool:
    missionControl: address = _mc
    if _mc == empty(address):
        missionControl = addys._getMissionControlAddr()
    underscore: address = staticcall MissionControl(missionControl).underscoreRegistry()
    return self._isUnderscoreWalletOwner(_user, _caller, underscore)


@view
@internal
def _isUnderscoreWalletOwner(_user: address, _caller: address, _underscore: address) -> bool:
    if _underscore == empty(address):
        return False

    if not self._isUnderscoreWallet(_user, _underscore):
        return False

    walletConfig: address = staticcall UnderscoreWallet(_user).walletConfig()
    if walletConfig == empty(address):
        return False

    # check if caller is owner
    return staticcall UnderscoreWalletConfig(walletConfig).owner() == _caller


# underscore address check


@view
@external
def isUnderscoreAddr(_addr: address, _mc: address = empty(address)) -> bool:
    missionControl: address = _mc
    if _mc == empty(address):
        missionControl = addys._getMissionControlAddr()
    underscore: address = staticcall MissionControl(_mc).underscoreRegistry()
    return self._isUnderscoreAddr(_addr, underscore)


@view
@internal
def _isUnderscoreAddr(_addr: address, _underscore: address) -> bool:
    if _underscore == empty(address):
        return False

    # check if addr is in underscore registry (Loot Distributor)
    if staticcall AddressRegistry(_underscore).isValidAddr(_addr):
        return True

    # check if addr is an underscore lego
    undyLegoBook: address = staticcall AddressRegistry(_underscore).getAddr(UNDERSCORE_LEGOBOOK_ID)
    if undyLegoBook == empty(address):
        return False
    return staticcall AddressRegistry(undyLegoBook).isValidAddr(_addr)


# owner or lego


@view
@external
def isUnderscoreOwnerOrLego(_user: address, _caller: address, _mc: address = empty(address)) -> bool:
    missionControl: address = _mc
    if _mc == empty(address):
        missionControl = addys._getMissionControlAddr()
    underscore: address = staticcall MissionControl(missionControl).underscoreRegistry()
    return self._isUnderscoreWalletOwner(_user, _caller, underscore) or self._isUnderscoreAddr(_caller, underscore)
