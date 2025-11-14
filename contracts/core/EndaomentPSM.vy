#            ___          ___                       ___          ___          ___          ___          ___                 
#           /\__\        /\  \        _____        /\  \        /\  \        /\  \        /\__\        /\  \                
#          /:/ _/_       \:\  \      /::\  \      /::\  \      /::\  \      |::\  \      /:/ _/_       \:\  \       ___     
#         /:/ /\__\       \:\  \    /:/\:\  \    /:/\:\  \    /:/\:\  \     |:|:\  \    /:/ /\__\       \:\  \     /\__\    
#        /:/ /:/ _/_  _____\:\  \  /:/  \:\__\  /:/ /::\  \  /:/  \:\  \  __|:|\:\  \  /:/ /:/ _/_  _____\:\  \   /:/  /    
#       /:/_/:/ /\__\/::::::::\__\/:/__/ \:|__|/:/_/:/\:\__\/:/__/ \:\__\/::::|_\:\__\/:/_/:/ /\__\/::::::::\__\ /:/__/     
#       \:\/:/ /:/  /\:\~~\~~\/__/\:\  \ /:/  /\:\/:/  \/__/\:\  \ /:/  /\:\~~\  \/__/\:\/:/ /:/  /\:\~~\~~\/__//::\  \     
#        \::/_/:/  /  \:\  \       \:\  /:/  /  \::/__/      \:\  /:/  /  \:\  \       \::/_/:/  /  \:\  \     /:/\:\  \    
#         \:\/:/  /    \:\  \       \:\/:/  /    \:\  \       \:\/:/  /    \:\  \       \:\/:/  /    \:\  \    \/__\:\  \   
#          \::/  /      \:\__\       \::/  /      \:\__\       \::/  /      \:\__\       \::/  /      \:\__\        \:\__\  
#           \/__/        \/__/        \/__/        \/__/        \/__/        \/__/        \/__/        \/__/         \/__/  
#
#     ╔════════════════════════════════════════════════════╗
#     ║  ** Endaoment **                                   ║
#     ║  Handles protocol-owned liquidity, peg management  ║
#     ╚════════════════════════════════════════════════════╝
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
from interfaces import UndyLego

from ethereum.ercs import IERC20

interface PriceDesk:
    def getAssetAmount(_asset: address, _usdValue: uint256, _shouldRaise: bool = False) -> uint256: view
    def getUsdValue(_asset: address, _amount: uint256, _shouldRaise: bool = False) -> uint256: view

interface GreenToken:
    def mint(_to: address, _amount: uint256): nonpayable
    def burn(_amount: uint256) -> bool: nonpayable

interface Registry:
    def isValidAddr(_addr: address) -> bool: view
    def getAddr(_id: uint256) -> address: view

interface VaultRegistry:
    def isEarnVault(_addr: address) -> bool: view

interface MissionControl:
    def underscoreRegistry() -> address: view

struct IntervalBorrow:
    start: uint256
    amount: uint256

struct UsdcYieldPosition:
    legoId: uint256
    vaultToken: address

event MintGreen:
    user: indexed(address)
    sender: indexed(address)
    usdcAmount: uint256
    greenAmount: uint256
    feeAmount: uint256

event RedeemGreen:
    user: indexed(address)
    greenIn: uint256
    usdcOut: uint256
    fee: uint256

event EndaomentPSMYieldDeposit:
    amount: uint256
    vaultToken: indexed(address)
    vaultTokenReceived: uint256
    usdValue: uint256

event YieldWithdraw:
    vaultTokenBurned: uint256
    usdcReceived: uint256

event CanMintUpdated:
    canMint: bool

event CanRedeemUpdated:
    canRedeem: bool

event MintFeeUpdated:
    fee: uint256

event RedeemFeeUpdated:
    fee: uint256

event MaxIntervalMintUpdated:
    max: uint256

event MaxIntervalRedeemUpdated:
    max: uint256

event NumBlocksPerIntervalUpdated:
    blocks: uint256

event ShouldEnforceMintAllowlistUpdated:
    enforce: bool

event ShouldEnforceRedeemAllowlistUpdated:
    enforce: bool

event MintAllowlistUpdated:
    user: indexed(address)
    allowed: bool

event RedeemAllowlistUpdated:
    user: indexed(address)
    allowed: bool

event UsdcYieldPositionUpdated:
    legoId: uint256
    vaultToken: indexed(address)

event FeesWithdrawn:
    recipient: indexed(address)
    amount: uint256

# general config
numBlocksPerInterval: public(uint256) # shared interval duration
usdcYieldPosition: public(UsdcYieldPosition)

# mint config
canMint: public(bool)
mintFee: public(uint256) # basis points
maxIntervalMint: public(uint256) # max GREEN mintable per interval
mintAllowlist: public(HashMap[address, bool])
shouldEnforceMintAllowlist: public(bool)
globalMintInterval: public(IntervalBorrow)

# redeem config
canRedeem: public(bool)
redeemFee: public(uint256) # basis points
maxIntervalRedeem: public(uint256) # max GREEN redeemable per interval
redeemAllowlist: public(HashMap[address, bool])
shouldEnforceRedeemAllowlist: public(bool)
globalRedeemInterval: public(IntervalBorrow)

UNDERSCORE_LEGOBOOK_ID: constant(uint256) = 3
UNDERSCORE_VAULT_REGISTRY_ID: constant(uint256) = 10
HUNDRED_PERCENT: constant(uint256) = 100_00  # 100.00%
ONE_USDC: constant(uint256) = 10**6
ONE_GREEN: constant(uint256) = 10**18

USDC: public(immutable(address))


@deploy
def __init__(
    _ripeHq: address,
    _numBlocksPerInterval: uint256,
    _mintFee: uint256,
    _maxIntervalMint: uint256,
    _redeemFee: uint256,
    _maxIntervalRedeem: uint256,
    _usdc: address,
    _usdcYieldLegoId: uint256,
    _usdcYieldVaultToken: address,
):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, True, False) # (isPaused, canMintGreen, canMintRipe)

    assert _numBlocksPerInterval != 0 # dev: invalid interval
    self.numBlocksPerInterval = _numBlocksPerInterval

    # mint config
    self.canMint = False
    assert _mintFee <= HUNDRED_PERCENT # dev: invalid fee
    self.mintFee = _mintFee
    self.maxIntervalMint = _maxIntervalMint
    self.shouldEnforceMintAllowlist = False

    # redeem config
    self.canRedeem = False
    assert _redeemFee <= HUNDRED_PERCENT # dev: invalid fee
    self.redeemFee = _redeemFee
    self.maxIntervalRedeem = _maxIntervalRedeem
    self.shouldEnforceRedeemAllowlist = False

    assert _usdc != empty(address) # dev: invalid USDC address
    USDC = _usdc

    # yield config
    assert _usdcYieldLegoId != 0 # dev: invalid lego ID
    assert _usdcYieldVaultToken != empty(address) # dev: invalid vault token
    self.usdcYieldPosition = UsdcYieldPosition(legoId=_usdcYieldLegoId, vaultToken=_usdcYieldVaultToken)


##############
# GREEN Mint #
##############


# mint


@nonreentrant
@external
def mint(_usdcAmount: uint256 = max_value(uint256), _recipient: address = msg.sender) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    assert self.canMint # dev: minting disabled
    a: addys.Addys = addys._getAddys()

    # usdc amount to transfer
    usdc: address = USDC
    usdcAmount: uint256 = min(_usdcAmount, staticcall IERC20(usdc).balanceOf(msg.sender))
    assert usdcAmount != 0 # dev: zero amount

    # allowlist check (Underscore addresses bypass)
    isUnderscore: bool = self._isUnderscoreAddr(msg.sender, a.missionControl)
    if not isUnderscore and self.shouldEnforceMintAllowlist:
        assert self.mintAllowlist[msg.sender] # dev: not on mint allowlist

    # transfer usdc from user
    assert extcall IERC20(usdc).transferFrom(msg.sender, self, usdcAmount, default_return_value=True) # dev: transfer failed

    # mint fee
    feeAmount: uint256 = usdcAmount * self.mintFee // HUNDRED_PERCENT
    usdcAfterFee: uint256 = usdcAmount - feeAmount

    # green to mint
    usdValue: uint256 = staticcall PriceDesk(a.priceDesk).getUsdValue(usdc, usdcAfterFee, True)
    usdcInGreenDecimals: uint256 = usdcAfterFee * ONE_GREEN // ONE_USDC
    greenToMint: uint256 = min(usdValue, usdcInGreenDecimals)
    assert greenToMint != 0 # dev: zero mint amount

    # check and update interval limits (Underscore addresses bypass)
    if not isUnderscore:
        self._checkAndUpdateMintInterval(greenToMint)

    # mint green
    extcall GreenToken(a.greenToken).mint(_recipient, greenToMint)

    # deposit usdc into yield
    self._depositToYield(usdc, a.missionControl)

    log MintGreen(user=_recipient, sender=msg.sender, usdcAmount=usdcAmount, greenAmount=greenToMint, feeAmount=feeAmount)
    return greenToMint


# check interval availability


@view
@external
def getAvailableToMint() -> uint256:
    data: IntervalBorrow = self.globalMintInterval
    maxIntervalMint: uint256 = self.maxIntervalMint
    if data.start != 0 and data.start + self.numBlocksPerInterval > block.number:
        maxIntervalMint -= min(data.amount, maxIntervalMint)
    return maxIntervalMint


# update mint interval


@internal
def _checkAndUpdateMintInterval(_amount: uint256):
    data: IntervalBorrow = self.globalMintInterval
    availToMint: uint256 = 0
    isFreshInterval: bool = True

    # check if in same interval or new interval
    if data.start != 0 and data.start + self.numBlocksPerInterval > block.number:
        maxIntervalMint: uint256 = self.maxIntervalMint
        availToMint = maxIntervalMint - min(data.amount, maxIntervalMint)
        isFreshInterval = False
    else:
        availToMint = self.maxIntervalMint

    assert _amount <= availToMint # dev: exceeds max interval mint

    # update interval
    if isFreshInterval:
        data.start = block.number
        data.amount = _amount
    else:
        data.amount += _amount

    self.globalMintInterval = data


# deposit to yield


@internal
def _depositToYield(_usdc: address, _missionControl: address):
    usdcYieldPosition: UsdcYieldPosition = self.usdcYieldPosition
    if usdcYieldPosition.legoId == 0 or usdcYieldPosition.vaultToken == empty(address):
        return

    # get idle usdc balance
    usdcBalance: uint256 = staticcall IERC20(_usdc).balanceOf(self)
    if usdcBalance == 0:
        return

    # get lego address
    legoAddr: address = self._getLegoAddr(usdcYieldPosition.legoId, _missionControl)
    if legoAddr == empty(address):
        return

    # deposit into yield position
    assert extcall IERC20(_usdc).approve(legoAddr, usdcBalance, default_return_value=True)
    assetAmount: uint256 = 0
    vaultToken: address = empty(address)
    vaultTokenAmountReceived: uint256 = 0
    txUsdValue: uint256 = 0
    assetAmount, vaultToken, vaultTokenAmountReceived, txUsdValue = extcall UndyLego(legoAddr).depositForYield(_usdc, usdcBalance, usdcYieldPosition.vaultToken, empty(bytes32), self)
    assert extcall IERC20(_usdc).approve(legoAddr, 0, default_return_value=True)

    log EndaomentPSMYieldDeposit(amount=assetAmount, vaultToken=vaultToken, vaultTokenReceived=vaultTokenAmountReceived, usdValue=txUsdValue)


# lego addr


@view
@internal
def _getLegoAddr(_legoId: uint256, _missionControl: address) -> address:
    underscoreRegistry: address = staticcall MissionControl(_missionControl).underscoreRegistry()
    if underscoreRegistry == empty(address):
        return empty(address)
    legoBook: address = staticcall Registry(underscoreRegistry).getAddr(UNDERSCORE_LEGOBOOK_ID)
    if legoBook == empty(address):
        return empty(address)
    legoAddr: address = staticcall Registry(legoBook).getAddr(_legoId)
    return legoAddr


# is underscore addr


@view
@internal
def _isUnderscoreAddr(_addr: address, _missionControl: address) -> bool:
    underscore: address = staticcall MissionControl(_missionControl).underscoreRegistry()
    if underscore == empty(address):
        return False

    # check if underscore vault
    vaultRegistry: address = staticcall Registry(underscore).getAddr(UNDERSCORE_VAULT_REGISTRY_ID)
    if vaultRegistry != empty(address):
        if staticcall VaultRegistry(vaultRegistry).isEarnVault(_addr):
            return True

    # check if underscore lego
    undyLegoBook: address = staticcall Registry(underscore).getAddr(UNDERSCORE_LEGOBOOK_ID)
    if undyLegoBook != empty(address):
        return staticcall Registry(undyLegoBook).isValidAddr(_addr)

    return False


################
# GREEN Redeem #
################


# redeem interval


@view
@external
def getAvailableToRedeem() -> uint256:
    data: IntervalBorrow = self.globalRedeemInterval
    maxIntervalRedeem: uint256 = self.maxIntervalRedeem
    if data.start != 0 and data.start + self.numBlocksPerInterval > block.number:
        maxIntervalRedeem -= min(data.amount, maxIntervalRedeem)
    return maxIntervalRedeem


# @nonreentrant
# @external
# def redeem(_greenAmount: uint256 = max_value(uint256)) -> uint256:
#     """
#     @notice Redeem GREEN for USDC
#     @param _greenAmount Amount of GREEN to redeem (max_value for all)
#     @return Amount of USDC received
#     """
#     assert not deptBasics.isPaused  # dev: contract paused
#     assert self.canRedeem  # dev: redemption disabled

#     # Get actual amount to redeem
#     greenAmount: uint256 = _greenAmount
#     if _greenAmount == max_value(uint256):
#         greenAmount = staticcall IERC20(addys._getGreenTokenAddr(empty(addys.Addys))).balanceOf(msg.sender)

#     assert greenAmount > 0  # dev: zero amount

#     # Check allowlist (Underscore addresses bypass)
#     isUnderscore: bool = self._isUnderscoreAddr(msg.sender)
#     if self.shouldEnforceRedeemAllowlist and not isUnderscore:
#         assert self.redeemAllowlist[msg.sender]  # dev: not on redeem allowlist

#     # Transfer GREEN from user
#     a: addys.Addys = addys._getAddys(empty(addys.Addys))
#     assert extcall IERC20(a.greenToken).transferFrom(msg.sender, self, greenAmount, default_return_value=True)  # dev: transfer failed

#     # Calculate USDC to give
#     # min(PriceDesk.getAssetAmount(USDC, greenAmount), greenAmount in USDC decimals)
#     usdcFromPriceDesk: uint256 = staticcall PriceDesk(a.priceDesk).getAssetAmount(USDC, greenAmount, False)
#     greenInUsdcDecimals: uint256 = greenAmount * ONE_USDC // ONE_GREEN
#     usdcToGive: uint256 = min(usdcFromPriceDesk, greenInUsdcDecimals)

#     assert usdcToGive > 0  # dev: zero redeem amount

#     # Check and update interval limits (Underscore addresses bypass)
#     if not isUnderscore:
#         self._checkAndUpdateRedeemInterval(greenAmount)

#     # Apply redeem fee
#     feeAmount: uint256 = usdcToGive * self.redeemFee // HUNDRED_PERCENT
#     usdcAfterFee: uint256 = usdcToGive - feeAmount

#     # Ensure we have enough USDC (withdraw from yield if needed)
#     self._ensureUsdcLiquidity(usdcAfterFee)

#     # Transfer USDC to user
#     assert extcall IERC20(USDC).transfer(msg.sender, usdcAfterFee, default_return_value=True)  # dev: transfer failed

#     # Burn GREEN
#     assert extcall GreenToken(a.greenToken).burn(greenAmount)  # dev: burn failed

#     log RedeemGreen(msg.sender, greenAmount, usdcAfterFee, feeAmount)

#     return usdcAfterFee

# # ============================================
# # Internal Helper Functions
# # ============================================






# @internal
# def _checkAndUpdateRedeemInterval(_amount: uint256):
#     """
#     @notice Check and update global redeem interval for rate limiting
#     @param _amount Amount to redeem
#     """
#     globalInterval: IntervalBorrow = self.globalRedeemInterval
#     availToRedeem: uint256 = 0
#     isFreshInterval: bool = True

#     # Check if in same interval or new interval
#     if globalInterval.start != 0 and globalInterval.start + self.numBlocksPerInterval > block.number:
#         # Still in same interval
#         availToRedeem = self.maxIntervalRedeem - min(globalInterval.amount, self.maxIntervalRedeem)
#         isFreshInterval = False
#     else:
#         # Fresh interval
#         availToRedeem = self.maxIntervalRedeem

#     assert _amount <= availToRedeem  # dev: exceeds max interval redeem

#     # Update interval
#     if isFreshInterval:
#         self.globalRedeemInterval = IntervalBorrow(start=block.number, amount=_amount)
#     else:
#         self.globalRedeemInterval.amount += _amount


# @internal
# def _withdrawFromYield(_amount: uint256) -> uint256:
#     """
#     @notice Withdraw USDC from yield position
#     @param _amount Amount of USDC needed
#     @return Actual amount of USDC withdrawn
#     """
#     if self.usdcYieldPosition.legoId == 0:
#         return 0

#     if self.usdcYieldPosition.vaultToken == empty(address):
#         return 0

#     # Check vault token balance
#     vaultTokenBalance: uint256 = staticcall IERC20(self.usdcYieldPosition.vaultToken).balanceOf(self)
#     if vaultTokenBalance == 0:
#         return 0

#     # Get lego address
#     a: addys.Addys = addys._getAddys(empty(addys.Addys))
#     legoAddr: address = staticcall Registry(a.missionControl).getAddr(self.usdcYieldPosition.legoId)
#     assert legoAddr != empty(address)  # dev: invalid lego

#     # Approve vault token
#     assert extcall IERC20(self.usdcYieldPosition.vaultToken).approve(legoAddr, vaultTokenBalance, default_return_value=True)

#     # Withdraw from yield (withdraw all vault tokens, not specific amount)
#     vaultTokenBurned: uint256 = 0
#     underlyingAsset: address = empty(address)
#     underlyingAmount: uint256 = 0
#     txUsdValue: uint256 = 0

#     vaultTokenBurned, underlyingAsset, underlyingAmount, txUsdValue = extcall UndyLego(legoAddr).withdrawFromYield(
#         self.usdcYieldPosition.vaultToken,
#         vaultTokenBalance,
#         empty(bytes32),
#         self
#     )

#     # Reset approval
#     assert extcall IERC20(self.usdcYieldPosition.vaultToken).approve(legoAddr, 0, default_return_value=True)

#     log YieldWithdraw(vaultTokenBurned, underlyingAmount)

#     return underlyingAmount

# @internal
# def _ensureUsdcLiquidity(_amount: uint256):
#     """
#     @notice Ensure contract has enough USDC, withdraw from yield if needed
#     @param _amount Amount of USDC needed
#     """
#     usdcBalance: uint256 = staticcall IERC20(USDC).balanceOf(self)

#     if usdcBalance >= _amount:
#         return

#     # Need to withdraw from yield
#     neededAmount: uint256 = _amount - usdcBalance
#     withdrawnAmount: uint256 = self._withdrawFromYield(neededAmount)

#     # Verify we now have enough
#     usdcBalance = staticcall IERC20(USDC).balanceOf(self)
#     assert usdcBalance >= _amount  # dev: insufficient USDC

# # ============================================
# # Governance Functions (Switchboard-only)
# # ============================================

# @external
# def setCanMint(_canMint: bool):
#     """
#     @notice Enable/disable minting
#     @param _canMint New canMint value
#     """
#     assert addys._isSwitchboardAddr(msg.sender)  # dev: no perms
#     self.canMint = _canMint
#     log CanMintUpdated(_canMint)

# @external
# def setCanRedeem(_canRedeem: bool):
#     """
#     @notice Enable/disable redemptions
#     @param _canRedeem New canRedeem value
#     """
#     assert addys._isSwitchboardAddr(msg.sender)  # dev: no perms
#     self.canRedeem = _canRedeem
#     log CanRedeemUpdated(_canRedeem)

# @external
# def setMintFee(_fee: uint256):
#     """
#     @notice Set mint fee
#     @param _fee Fee in basis points (100_00 = 100%)
#     """
#     assert addys._isSwitchboardAddr(msg.sender)  # dev: no perms
#     assert _fee <= HUNDRED_PERCENT  # dev: fee too high
#     self.mintFee = _fee
#     log MintFeeUpdated(_fee)

# @external
# def setRedeemFee(_fee: uint256):
#     """
#     @notice Set redeem fee
#     @param _fee Fee in basis points (100_00 = 100%)
#     """
#     assert addys._isSwitchboardAddr(msg.sender)  # dev: no perms
#     assert _fee <= HUNDRED_PERCENT  # dev: fee too high
#     self.redeemFee = _fee
#     log RedeemFeeUpdated(_fee)

# @external
# def setMaxIntervalMint(_max: uint256):
#     """
#     @notice Set maximum mint amount per interval
#     @param _max Maximum amount
#     """
#     assert addys._isSwitchboardAddr(msg.sender)  # dev: no perms
#     self.maxIntervalMint = _max
#     log MaxIntervalMintUpdated(_max)

# @external
# def setMaxIntervalRedeem(_max: uint256):
#     """
#     @notice Set maximum redeem amount per interval
#     @param _max Maximum amount
#     """
#     assert addys._isSwitchboardAddr(msg.sender)  # dev: no perms
#     self.maxIntervalRedeem = _max
#     log MaxIntervalRedeemUpdated(_max)

# @external
# def setNumBlocksPerInterval(_blocks: uint256):
#     """
#     @notice Set interval duration in blocks
#     @param _blocks Number of blocks per interval
#     """
#     assert addys._isSwitchboardAddr(msg.sender)  # dev: no perms
#     assert _blocks > 0  # dev: invalid interval
#     self.numBlocksPerInterval = _blocks
#     log NumBlocksPerIntervalUpdated(_blocks)

# @external
# def setShouldEnforceMintAllowlist(_enforce: bool):
#     """
#     @notice Enable/disable mint allowlist enforcement
#     @param _enforce Whether to enforce allowlist
#     """
#     assert addys._isSwitchboardAddr(msg.sender)  # dev: no perms
#     self.shouldEnforceMintAllowlist = _enforce
#     log ShouldEnforceMintAllowlistUpdated(_enforce)

# @external
# def setShouldEnforceRedeemAllowlist(_enforce: bool):
#     """
#     @notice Enable/disable redeem allowlist enforcement
#     @param _enforce Whether to enforce allowlist
#     """
#     assert addys._isSwitchboardAddr(msg.sender)  # dev: no perms
#     self.shouldEnforceRedeemAllowlist = _enforce
#     log ShouldEnforceRedeemAllowlistUpdated(_enforce)

# @external
# def updateMintAllowlist(_user: address, _allowed: bool):
#     """
#     @notice Update mint allowlist for a user
#     @param _user User address
#     @param _allowed Whether user is allowed
#     """
#     assert addys._isSwitchboardAddr(msg.sender)  # dev: no perms
#     self.mintAllowlist[_user] = _allowed
#     log MintAllowlistUpdated(_user, _allowed)

# @external
# def updateRedeemAllowlist(_user: address, _allowed: bool):
#     """
#     @notice Update redeem allowlist for a user
#     @param _user User address
#     @param _allowed Whether user is allowed
#     """
#     assert addys._isSwitchboardAddr(msg.sender)  # dev: no perms
#     self.redeemAllowlist[_user] = _allowed
#     log RedeemAllowlistUpdated(_user, _allowed)

# @external
# def setUsdcYieldPosition(_legoId: uint256, _vaultToken: address):
#     """
#     @notice Configure USDC yield position
#     @param _legoId Lego ID for yield
#     @param _vaultToken Vault token address
#     """
#     assert addys._isSwitchboardAddr(msg.sender)  # dev: no perms
#     self.usdcYieldPosition = UsdcYieldPosition(legoId=_legoId, vaultToken=_vaultToken)
#     log UsdcYieldPositionUpdated(_legoId, _vaultToken)

# @external
# def withdrawFees(_recipient: address, _amount: uint256):
#     """
#     @notice Withdraw accumulated fees
#     @param _recipient Recipient address
#     @param _amount Amount to withdraw (max_value for all)
#     """
#     assert addys._isSwitchboardAddr(msg.sender)  # dev: no perms
#     assert _recipient != empty(address)  # dev: zero address

#     amount: uint256 = _amount
#     if _amount == max_value(uint256):
#         amount = staticcall IERC20(USDC).balanceOf(self)

#     assert amount > 0  # dev: zero amount
#     assert extcall IERC20(USDC).transfer(_recipient, amount, default_return_value=True)  # dev: transfer failed

#     log FeesWithdrawn(_recipient, amount)
