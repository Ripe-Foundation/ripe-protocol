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

struct PsmInterval:
    start: uint256
    amount: uint256

struct UsdcYieldPosition:
    legoId: uint256
    vaultToken: address

event MintGreen:
    user: indexed(address)
    sender: indexed(address)
    usdcIn: uint256
    greenOut: uint256
    usdcFee: uint256

event RedeemGreen:
    user: indexed(address)
    sender: indexed(address)
    greenIn: uint256
    usdcOut: uint256
    usdcFee: uint256

event EndaomentPSMYieldDeposit:
    amount: uint256
    vaultToken: indexed(address)
    vaultTokenReceived: uint256
    usdValue: uint256

event EndaomentPSMYieldWithdrawal:
    vaultToken: indexed(address)
    vaultTokenBurned: uint256
    usdcReceived: uint256
    usdValue: uint256

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
globalMintInterval: public(PsmInterval)

# redeem config
canRedeem: public(bool)
redeemFee: public(uint256) # basis points
maxIntervalRedeem: public(uint256) # max GREEN redeemable per interval
redeemAllowlist: public(HashMap[address, bool])
shouldEnforceRedeemAllowlist: public(bool)
globalRedeemInterval: public(PsmInterval)

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
    if _usdcYieldLegoId != 0 and _usdcYieldVaultToken != empty(address):
        self.usdcYieldPosition = UsdcYieldPosition(legoId=_usdcYieldLegoId, vaultToken=_usdcYieldVaultToken)


##############
# GREEN Mint #
##############


# mint


@nonreentrant
@external
def mintGreen(_usdcAmount: uint256 = max_value(uint256), _recipient: address = msg.sender) -> uint256:
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

    log MintGreen(user=_recipient, sender=msg.sender, usdcIn=usdcAmount, greenOut=greenToMint, usdcFee=feeAmount)
    return greenToMint


# max mintable (front-end can use this to get max USDC amount)


@view
@external
def getMaxUsdcAmountForMint(_user: address = empty(address)) -> uint256:
    usdc: address = USDC
    a: addys.Addys = addys._getAddys()

    # convert interval capacity (GREEN) back to USDC needed
    intervalCapacity: uint256 = self._getAvailIntervalMint()

    # properly account for USDC price (may need more USDC if below peg)
    usdcFromPriceDesk: uint256 = staticcall PriceDesk(a.priceDesk).getAssetAmount(usdc, intervalCapacity, False)
    usdcInGreenDecimals: uint256 = intervalCapacity * ONE_USDC // ONE_GREEN
    usdcNeeded: uint256 = max(usdcFromPriceDesk, usdcInGreenDecimals)

    # account for mint fee: usdcAfterFee = usdcInput * (1 - fee)
    # reverse: usdcInput = usdcAfterFee * HUNDRED_PERCENT / (HUNDRED_PERCENT - fee)
    mintFee: uint256 = self.mintFee
    if mintFee != 0:
        feeMultiplier: uint256 = HUNDRED_PERCENT - mintFee
        usdcNeeded = usdcNeeded * HUNDRED_PERCENT // feeMultiplier

    # if user provided, also consider their usdc balance
    if _user != empty(address):
        usdcBalance: uint256 = staticcall IERC20(usdc).balanceOf(_user)
        usdcNeeded = min(usdcBalance, usdcNeeded)

    return usdcNeeded


# check interval availability


@view
@external
def getAvailIntervalMint() -> uint256:
    return self._getAvailIntervalMint()


@view
@internal
def _getAvailIntervalMint() -> uint256:
    data: PsmInterval = self.globalMintInterval
    maxIntervalMint: uint256 = self.maxIntervalMint
    if data.start != 0 and data.start + self.numBlocksPerInterval > block.number:
        maxIntervalMint -= min(data.amount, maxIntervalMint)
    return maxIntervalMint


# update mint interval


@internal
def _checkAndUpdateMintInterval(_amount: uint256):
    data: PsmInterval = self.globalMintInterval
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


#####################
# GREEN Redemptions #
#####################


# redeem


@nonreentrant
@external
def redeemGreen(_greenAmount: uint256 = max_value(uint256), _recipient: address = msg.sender) -> uint256:
    assert not deptBasics.isPaused # dev: contract paused
    assert self.canRedeem # dev: redemption disabled
    a: addys.Addys = addys._getAddys()

    # green amount to transfer
    green: address = a.greenToken
    greenAmount: uint256 = min(_greenAmount, staticcall IERC20(green).balanceOf(msg.sender))
    assert greenAmount != 0 # dev: zero amount

    # allowlist check (Underscore addresses bypass)
    isUnderscore: bool = self._isUnderscoreAddr(msg.sender, a.missionControl)
    if not isUnderscore and self.shouldEnforceRedeemAllowlist:
        assert self.redeemAllowlist[msg.sender] # dev: not on redeem allowlist

    # transfer green from user
    assert extcall IERC20(green).transferFrom(msg.sender, self, greenAmount, default_return_value=True) # dev: transfer failed

    # usdc to give
    usdc: address = USDC
    usdcFromPriceDesk: uint256 = staticcall PriceDesk(a.priceDesk).getAssetAmount(usdc, greenAmount, True)
    greenInUsdcDecimals: uint256 = greenAmount * ONE_USDC // ONE_GREEN
    usdcToGive: uint256 = min(usdcFromPriceDesk, greenInUsdcDecimals)
    assert usdcToGive != 0 # dev: zero redeem amount

    feeAmount: uint256 = 0
    usdcAfterFee: uint256 = usdcToGive

    # check and update interval limits (Underscore addresses bypass)
    if not isUnderscore:
        self._checkAndUpdateRedeemInterval(greenAmount)

        # redeem fee
        feeAmount = usdcToGive * self.redeemFee // HUNDRED_PERCENT
        usdcAfterFee = usdcToGive - feeAmount

    # ensure usdc liquidity (withdraw from yield if needed)
    usdcBalance: uint256 = staticcall IERC20(usdc).balanceOf(self)
    if usdcBalance < usdcAfterFee:
        usdcBalance += self._withdrawFromYield(a.missionControl)
        assert usdcBalance >= usdcAfterFee # dev: insufficient USDC

    # transfer usdc to recipient
    assert extcall IERC20(usdc).transfer(_recipient, usdcAfterFee, default_return_value=True) # dev: transfer failed

    # burn green
    assert extcall GreenToken(green).burn(greenAmount) # dev: burn failed

    log RedeemGreen(user=_recipient, sender=msg.sender, greenIn=greenAmount, usdcOut=usdcAfterFee, usdcFee=feeAmount)
    return usdcAfterFee


# max redeemable (front-end can use this to get max GREEN amount)


@view
@external
def getMaxRedeemableGreenAmount(_user: address = empty(address)) -> uint256:
    a: addys.Addys = addys._getAddys()
    usdc: address = USDC

    # interval capacity
    intervalCapacity: uint256 = self._getAvailIntervalRedemptions()

    # usdc available (idle + yield)
    usdcYieldPosition: UsdcYieldPosition = self.usdcYieldPosition
    usdcAvailable: uint256 = self._getAvailableUsdc(usdc, usdcYieldPosition.legoId, usdcYieldPosition.vaultToken, a.missionControl)

    # convert usdc to max green
    usdValue: uint256 = staticcall PriceDesk(a.priceDesk).getUsdValue(usdc, usdcAvailable, False)
    usdcInGreenDecimals: uint256 = usdcAvailable * ONE_GREEN // ONE_USDC
    maxGreenFromUsdc: uint256 = min(usdValue, usdcInGreenDecimals)

    # account for redeem fee: usdcAfterFee = usdcToGive * (1 - fee)
    # reverse: greenAmount = greenBeforeFee / (1 - fee)
    redeemFee: uint256 = self.redeemFee
    if redeemFee != 0:
        feeMultiplier: uint256 = HUNDRED_PERCENT - redeemFee
        maxGreenFromUsdc = maxGreenFromUsdc * HUNDRED_PERCENT // feeMultiplier

    # get limiting factor from interval and usdc
    maxRedeemable: uint256 = min(intervalCapacity, maxGreenFromUsdc)

    # if user provided, also consider their green balance
    if _user != empty(address):
        greenBalance: uint256 = staticcall IERC20(a.greenToken).balanceOf(_user)
        maxRedeemable = min(maxRedeemable, greenBalance)

    return maxRedeemable


# available interval redemptions


@view
@external
def getAvailIntervalRedemptions() -> uint256:
    return self._getAvailIntervalRedemptions()


@view
@internal
def _getAvailIntervalRedemptions() -> uint256:
    data: PsmInterval = self.globalRedeemInterval
    maxIntervalRedeem: uint256 = self.maxIntervalRedeem
    if data.start != 0 and data.start + self.numBlocksPerInterval > block.number:
        maxIntervalRedeem -= min(data.amount, maxIntervalRedeem)
    return maxIntervalRedeem


# update redeem interval


@internal
def _checkAndUpdateRedeemInterval(_amount: uint256):
    data: PsmInterval = self.globalRedeemInterval
    availToRedeem: uint256 = 0
    isFreshInterval: bool = True

    # check if in same interval or new interval
    if data.start != 0 and data.start + self.numBlocksPerInterval > block.number:
        maxIntervalRedeem: uint256 = self.maxIntervalRedeem
        availToRedeem = maxIntervalRedeem - min(data.amount, maxIntervalRedeem)
        isFreshInterval = False
    else:
        availToRedeem = self.maxIntervalRedeem

    assert _amount <= availToRedeem # dev: exceeds max interval redeem

    # update interval
    if isFreshInterval:
        data.start = block.number
        data.amount = _amount
    else:
        data.amount += _amount

    self.globalRedeemInterval = data


##################
# Yield Position #
##################


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


# withdraw from yield


@internal
def _withdrawFromYield(_missionControl: address) -> uint256:
    usdcYieldPosition: UsdcYieldPosition = self.usdcYieldPosition
    if usdcYieldPosition.legoId == 0 or usdcYieldPosition.vaultToken == empty(address):
        return 0

    # check vault token balance
    vaultTokenBalance: uint256 = staticcall IERC20(usdcYieldPosition.vaultToken).balanceOf(self)
    if vaultTokenBalance == 0:
        return 0

    # get lego address
    legoAddr: address = self._getLegoAddr(usdcYieldPosition.legoId, _missionControl)
    if legoAddr == empty(address):
        return 0

    # withdraw from yield position
    assert extcall IERC20(usdcYieldPosition.vaultToken).approve(legoAddr, vaultTokenBalance, default_return_value=True)
    vaultTokenBurned: uint256 = 0
    underlyingAsset: address = empty(address)
    underlyingAmount: uint256 = 0
    txUsdValue: uint256 = 0
    vaultTokenBurned, underlyingAsset, underlyingAmount, txUsdValue = extcall UndyLego(legoAddr).withdrawFromYield(usdcYieldPosition.vaultToken, vaultTokenBalance, empty(bytes32), self)
    assert extcall IERC20(usdcYieldPosition.vaultToken).approve(legoAddr, 0, default_return_value=True)

    log EndaomentPSMYieldWithdrawal(vaultToken=usdcYieldPosition.vaultToken, vaultTokenBurned=vaultTokenBurned, usdcReceived=underlyingAmount, usdValue=txUsdValue)
    return underlyingAmount


# underlying amount


@view
@external
def getUnderlyingYieldAmount() -> uint256:
    usdcYieldPosition: UsdcYieldPosition = self.usdcYieldPosition
    return self._getUnderlyingYieldAmount(usdcYieldPosition.legoId, usdcYieldPosition.vaultToken, addys._getMissionControlAddr())


@view
@internal
def _getUnderlyingYieldAmount(_legoId: uint256, _vaultToken: address, _missionControl: address) -> uint256:
    if _legoId == 0 or _vaultToken == empty(address):
        return 0
    vaultTokenBalance: uint256 = staticcall IERC20(_vaultToken).balanceOf(self)
    if vaultTokenBalance == 0:
        return 0
    legoAddr: address = self._getLegoAddr(_legoId, _missionControl)
    if legoAddr == empty(address):
        return 0
    return staticcall UndyLego(legoAddr).getUnderlyingAmountSafe(_vaultToken, vaultTokenBalance)


#############
# Utilities #
#############


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


# max usdc available


@view
@external
def getAvailableUsdc() -> uint256:
    usdcYieldPosition: UsdcYieldPosition = self.usdcYieldPosition
    return self._getAvailableUsdc(USDC, usdcYieldPosition.legoId, usdcYieldPosition.vaultToken, addys._getMissionControlAddr())


@view
@internal
def _getAvailableUsdc(_usdc: address, _legoId: uint256, _vaultToken: address, _missionControl: address) -> uint256:
    underlyingAmount: uint256 = self._getUnderlyingYieldAmount(_legoId, _vaultToken, _missionControl)
    return underlyingAmount + staticcall IERC20(_usdc).balanceOf(self)


###############
# Mint Config #
###############


# can mint


@external
def setCanMint(_canMint: bool):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _canMint != self.canMint # dev: no change
    self.canMint = _canMint
    log CanMintUpdated(canMint=_canMint)


# mint fee


@external
def setMintFee(_fee: uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _fee <= HUNDRED_PERCENT # dev: fee too high
    assert _fee != self.mintFee # dev: no change
    self.mintFee = _fee
    log MintFeeUpdated(fee=_fee)


# max interval mint


@external
def setMaxIntervalMint(_maxGreenAmount: uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _maxGreenAmount != self.maxIntervalMint # dev: no change
    assert _maxGreenAmount != 0 and _maxGreenAmount != max_value(uint256) # dev: invalid max
    self.maxIntervalMint = _maxGreenAmount
    log MaxIntervalMintUpdated(max=_maxGreenAmount)


# enforce mint allowlist


@external
def setShouldEnforceMintAllowlist(_shouldEnforce: bool):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _shouldEnforce != self.shouldEnforceMintAllowlist # dev: no change
    self.shouldEnforceMintAllowlist = _shouldEnforce
    log ShouldEnforceMintAllowlistUpdated(enforce=_shouldEnforce)


# update mint allowlist


@external
def updateMintAllowlist(_user: address, _isAllowed: bool):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _isAllowed != self.mintAllowlist[_user] # dev: no change
    self.mintAllowlist[_user] = _isAllowed
    log MintAllowlistUpdated(user=_user, allowed=_isAllowed)


#################
# Redeem Config #
#################


# can redeem


@external
def setCanRedeem(_canRedeem: bool):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _canRedeem != self.canRedeem # dev: no change
    self.canRedeem = _canRedeem
    log CanRedeemUpdated(canRedeem=_canRedeem)


# redeem fee


@external
def setRedeemFee(_fee: uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _fee <= HUNDRED_PERCENT # dev: fee too high
    assert _fee != self.redeemFee # dev: no change
    self.redeemFee = _fee
    log RedeemFeeUpdated(fee=_fee)


# max interval redeem


@external
def setMaxIntervalRedeem(_maxGreenAmount: uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _maxGreenAmount != self.maxIntervalRedeem # dev: no change
    assert _maxGreenAmount != 0 and _maxGreenAmount != max_value(uint256) # dev: invalid max
    self.maxIntervalRedeem = _maxGreenAmount
    log MaxIntervalRedeemUpdated(max=_maxGreenAmount)


# enforce redeem allowlist


@external
def setShouldEnforceRedeemAllowlist(_shouldEnforce: bool):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _shouldEnforce != self.shouldEnforceRedeemAllowlist # dev: no change
    self.shouldEnforceRedeemAllowlist = _shouldEnforce
    log ShouldEnforceRedeemAllowlistUpdated(enforce=_shouldEnforce)


# update redeem allowlist


@external
def updateRedeemAllowlist(_user: address, _isAllowed: bool):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _isAllowed != self.redeemAllowlist[_user] # dev: no change
    self.redeemAllowlist[_user] = _isAllowed
    log RedeemAllowlistUpdated(user=_user, allowed=_isAllowed)


##################
# General Config #
##################


# set yield position


@external
def setUsdcYieldPosition(_legoId: uint256, _vaultToken: address):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    currentPosition: UsdcYieldPosition = self.usdcYieldPosition
    assert _legoId != currentPosition.legoId or _vaultToken != currentPosition.vaultToken # dev: no change
    self.usdcYieldPosition = UsdcYieldPosition(legoId=_legoId, vaultToken=_vaultToken)
    log UsdcYieldPositionUpdated(legoId=_legoId, vaultToken=_vaultToken)


# num blocks per interval


@external
def setNumBlocksPerInterval(_blocks: uint256):
    assert not deptBasics.isPaused # dev: contract paused
    assert addys._isSwitchboardAddr(msg.sender) # dev: no perms
    assert _blocks != self.numBlocksPerInterval # dev: no change
    assert _blocks != 0 and _blocks != max_value(uint256) # dev: invalid interval
    self.numBlocksPerInterval = _blocks
    log NumBlocksPerIntervalUpdated(blocks=_blocks)