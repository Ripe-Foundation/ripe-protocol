# @version 0.4.1

from interfaces import Vault
from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed

interface Ledger:
    def userDepositPoints(_user: address, _vaultId: uint256, _asset: address) -> UserDepositPoints: view
    def assetDepositPoints(_vaultId: uint256, _asset: address) -> AssetDepositPoints: view
    def userBorrowPoints(_user: address) -> BorrowPoints: view
    def globalDepositPoints() -> GlobalDepositPoints: view
    def globalBorrowPoints() -> BorrowPoints: view
    def ripeAvailForRewards() -> uint256: view
    def ripeRewards() -> RipeRewards: view

interface ControlRoom:
    def getSpecificRipeAllocs(_vaultId: uint256, _asset: address) -> (uint256, uint256): view
    def getTotalRipeAllocs() -> (uint256, uint256): view
    def ripeRewardsAllocs() -> RipeRewardsAllocs: view
    def ripeRewardsStartBlock() -> uint256: view
    def ripePerBlock() -> uint256: view

interface VaultBook:
    def isNftVault(_vaultId: uint256) -> bool: view

interface AddyRegistry:
    def getAddy(_addyId: uint256) -> address: view

struct RipeRewards:
    stakers: uint256
    borrowers: uint256
    voteDepositors: uint256
    genDepositors: uint256
    newRipeRewards: uint256
    lastUpdate: uint256
    lastRewardsBlock: uint256

struct RipeRewardsAllocs:
    stakers: uint256
    borrowers: uint256
    voteDepositors: uint256
    genDepositors: uint256
    total: uint256

struct GlobalDepositPoints:
    lastUsdValue: uint256
    ripeStakerPoints: uint256
    ripeVotePoints: uint256
    ripeGenPoints: uint256
    lastUpdate: uint256

struct AssetDepositPoints:
    balancePoints: uint256
    lastBalance: uint256
    lastUsdValue: uint256
    ripeStakerPoints: uint256
    ripeVotePoints: uint256
    ripeGenPoints: uint256
    lastUpdate: uint256
    precision: uint256

struct UserDepositPoints:
    balancePoints: uint256
    lastBalance: uint256
    lastUpdate: uint256

struct BorrowPoints:
    lastPrincipal: uint256
    points: uint256
    lastUpdate: uint256

TELLER_ID: constant(uint256) = 1 # TODO: make sure this is correct
LEDGER_ID: constant(uint256) = 2 # TODO: make sure this is correct
VAULT_BOOK_ID: constant(uint256) = 3 # TODO: make sure this is correct
CONTROL_ROOM_ID: constant(uint256) = 6 # TODO: make sure this is correct

EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18

# config
isActivated: public(bool)
ADDY_REGISTRY: public(immutable(address))


@deploy
def __init__(_addyRegistry: address):
    assert _addyRegistry != empty(address) # dev: invalid addy registry
    ADDY_REGISTRY = _addyRegistry
    self.isActivated = True


@view
@internal
def _getAddys() -> address[3]:
    ar: address = ADDY_REGISTRY
    ledger: address = staticcall AddyRegistry(ar).getAddy(LEDGER_ID)
    vaultBook: address = staticcall AddyRegistry(ar).getAddy(VAULT_BOOK_ID)
    controlRoom: address = staticcall AddyRegistry(ar).getAddy(CONTROL_ROOM_ID)
    return [ledger, vaultBook, controlRoom]


################
# Ripe Rewards #
################


@view
@external
def getLatestRipeRewards() -> RipeRewards:
    addys: address[3] = self._getAddys()
    ledger: address = addys[0]
    controlRoom: address = addys[2]
    return self._getLatestRipeRewards(ledger, controlRoom)


@view
@internal
def _getLatestRipeRewards(_ledger: address, _controlRoom: address) -> RipeRewards:
    ripeRewards: RipeRewards = staticcall Ledger(_ledger).ripeRewards()
    ripeRewards.newRipeRewards = 0 # important to reset!

    # use most recent time between `lastUpdate` and `ripeRewardsStartBlock`
    ripeRewardsStartBlock: uint256 = staticcall ControlRoom(_controlRoom).ripeRewardsStartBlock()
    lastUpdateAdjusted: uint256 = max(ripeRewards.lastUpdate, ripeRewardsStartBlock)

    newRipeDistro: uint256 = 0
    if lastUpdateAdjusted != 0 and block.number > lastUpdateAdjusted:
        elapsedBlocks: uint256 = block.number - lastUpdateAdjusted
        newRipeDistro = min(staticcall ControlRoom(_controlRoom).ripePerBlock() * elapsedBlocks, staticcall Ledger(_ledger).ripeAvailForRewards())

    # nothing to do here
    if newRipeDistro == 0:
        ripeRewards.lastUpdate = block.number
        return ripeRewards

    # allocate ripe rewards to various buckets
    rewardsAllocs: RipeRewardsAllocs = staticcall ControlRoom(_controlRoom).ripeRewardsAllocs()
    if rewardsAllocs.total != 0:
        ripeRewards.stakers += newRipeDistro * rewardsAllocs.stakers // rewardsAllocs.total
        ripeRewards.borrowers += newRipeDistro * rewardsAllocs.borrowers // rewardsAllocs.total
        ripeRewards.voteDepositors += newRipeDistro * rewardsAllocs.voteDepositors // rewardsAllocs.total
        ripeRewards.genDepositors += newRipeDistro * rewardsAllocs.genDepositors // rewardsAllocs.total

        # rewards were distro'd, save important data
        ripeRewards.newRipeRewards = newRipeDistro
        ripeRewards.lastRewardsBlock = block.number

    ripeRewards.lastUpdate = block.number
    return ripeRewards


#################
# Global Points #
#################


# global deposit points


@view
@internal
def _getLatestGlobalDepositPoints(
    _lastRipeRewardsBlock: uint256,
    _ledger: address,
    _cr: address,
) -> GlobalDepositPoints:
    globalPoints: GlobalDepositPoints = staticcall Ledger(_ledger).globalDepositPoints()

    # get last ripe rewards block
    lastRipeRewardsBlock: uint256 = _lastRipeRewardsBlock
    if lastRipeRewardsBlock == 0:
        lastRipeRewardsBlock = self._getLatestRipeRewards(_ledger, _cr).lastRewardsBlock

    # nothing to do here
    if globalPoints.lastUpdate == 0 or lastRipeRewardsBlock <= globalPoints.lastUpdate:
        globalPoints.lastUpdate = block.number
        return globalPoints

    # total allocs (stakers + vote)
    stakerRipeTotalAlloc: uint256 = 0
    voteRipeTotalAlloc: uint256 = 0
    stakerRipeTotalAlloc, voteRipeTotalAlloc = staticcall ControlRoom(_cr).getTotalRipeAllocs()

    # update ripe rewards points
    elapsedBlocks: uint256 = lastRipeRewardsBlock - globalPoints.lastUpdate
    globalPoints.ripeStakerPoints += stakerRipeTotalAlloc * elapsedBlocks
    globalPoints.ripeVotePoints += voteRipeTotalAlloc * elapsedBlocks
    globalPoints.ripeGenPoints += globalPoints.lastUsdValue * elapsedBlocks

    # Note: will update `lastUsdValue` later in flow (after knowing AssetDepositPoints changes in usd value)

    globalPoints.lastUpdate = block.number
    return globalPoints


@view
@external
def getLatestGlobalDepositPoints() -> GlobalDepositPoints:
    # used mostly for testing
    addys: address[3] = self._getAddys()
    ledger: address = addys[0]
    controlRoom: address = addys[2]
    return self._getLatestGlobalDepositPoints(0, ledger, controlRoom)


# global borrow points


@view 
@internal 
def _getLatestGlobalBorrowPoints(
    _lastRipeRewardsBlock: uint256,
    _ledger: address,
    _cr: address,
) -> BorrowPoints:
    globalPoints: BorrowPoints = staticcall Ledger(_ledger).globalBorrowPoints()

    # get last ripe rewards block
    lastRipeRewardsBlock: uint256 = _lastRipeRewardsBlock
    if lastRipeRewardsBlock == 0:
        lastRipeRewardsBlock = self._getLatestRipeRewards(_ledger, _cr).lastRewardsBlock

    if globalPoints.lastUpdate != 0 and lastRipeRewardsBlock > globalPoints.lastUpdate:
        newBorrowPoints: uint256 = globalPoints.lastPrincipal * (lastRipeRewardsBlock - globalPoints.lastUpdate)
        globalPoints.points += newBorrowPoints

    # Note: will update `lastPrincipal` later in flow

    globalPoints.lastUpdate = block.number
    return globalPoints


@view
@external
def getLatestGlobalBorrowPoints() -> BorrowPoints:
    # used mostly for testing
    addys: address[3] = self._getAddys()
    ledger: address = addys[0]
    controlRoom: address = addys[2]
    return self._getLatestGlobalBorrowPoints(0, ledger, controlRoom)


########################
# Asset Deposit Points #
########################


@view
@internal
def _getLatestAssetDepositPoints(
    _vaultId: uint256,
    _asset: address,
    _lastRipeRewardsBlock: uint256,
    _ledger: address,
    _vaultBook: address,
    _cr: address,
) -> (AssetDepositPoints, bool):
    assetPoints: AssetDepositPoints = staticcall Ledger(_ledger).assetDepositPoints(_vaultId, _asset)

    # get precision to help normalize values later
    if assetPoints.precision == 0:
        assetPoints.precision = self._getAssetPrecision(_vaultId, _asset, _vaultBook)

    # balance points - how each user will split rewards for this vault/asset
    elapsedBlocks: uint256 = 0
    if assetPoints.lastUpdate != 0 and block.number > assetPoints.lastUpdate:
        elapsedBlocks = block.number - assetPoints.lastUpdate
        assetPoints.balancePoints += assetPoints.lastBalance * elapsedBlocks

    # asset allocs (staked + vote)
    stakedRipeAlloc: uint256 = 0
    voteRipeAlloc: uint256 = 0
    stakedRipeAlloc, voteRipeAlloc = staticcall ControlRoom(_cr).getSpecificRipeAllocs(_vaultId, _asset)

    # get last ripe rewards block
    lastRipeRewardsBlock: uint256 = _lastRipeRewardsBlock
    if lastRipeRewardsBlock == 0:
        lastRipeRewardsBlock = self._getLatestRipeRewards(_ledger, _cr).lastRewardsBlock

    # nothing else to do here
    if assetPoints.lastUpdate == 0 or lastRipeRewardsBlock <= assetPoints.lastUpdate:
        assetPoints.lastUpdate = block.number
        return assetPoints, stakedRipeAlloc != 0

    # update ripe rewards points
    elapsedBlocks = lastRipeRewardsBlock - assetPoints.lastUpdate
    assetPoints.ripeStakerPoints += stakedRipeAlloc * elapsedBlocks
    assetPoints.ripeVotePoints += voteRipeAlloc * elapsedBlocks
    assetPoints.ripeGenPoints += assetPoints.lastUsdValue * elapsedBlocks

    # Note: will update `lastUsdValue` later in flow

    assetPoints.lastUpdate = block.number
    return assetPoints, stakedRipeAlloc != 0


@view
@internal
def _getAssetPrecision(_vaultId: uint256, _asset: address, _vaultBook: address) -> uint256:
    if staticcall VaultBook(_vaultBook).isNftVault(_vaultId):
        return 1

    decimals: uint256 = convert(staticcall IERC20Detailed(_asset).decimals(), uint256)
    if decimals >= 8: # wbtc has 8 decimals
        return 10 ** (decimals // 2)

    return 10 ** decimals


@view
@external
def getLatestAssetDepositPoints(_vaultId: uint256, _asset: address) -> (AssetDepositPoints, bool):
    # used mostly for testing
    addys: address[3] = self._getAddys()
    ledger: address = addys[0]
    vaultBook: address = addys[1]
    controlRoom: address = addys[2]
    return self._getLatestAssetDepositPoints(_vaultId, _asset, 0, ledger, vaultBook, controlRoom)


###############
# User Points #
###############


# user deposit points


@view
@internal
def _getLatestUserDepositPoints(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _ledger: address,
) -> UserDepositPoints:
    userPoints: UserDepositPoints = staticcall Ledger(_ledger).userDepositPoints(_user, _vaultId, _asset)

    # add user balance points
    if userPoints.lastUpdate != 0 and block.number > userPoints.lastUpdate:
        elapsedBlocks: uint256 = block.number - userPoints.lastUpdate
        userPoints.balancePoints += userPoints.lastBalance * elapsedBlocks

    # Note: will update `lastBalance` later in flow (if necessary)

    userPoints.lastUpdate = block.number
    return userPoints


@view
@external
def getLatestUserDepositPoints(_user: address, _vaultId: uint256, _asset: address) -> UserDepositPoints:
    # used mostly for testing
    ledger: address = self._getAddys()[0]
    return self._getLatestUserDepositPoints(_user, _vaultId, _asset, ledger)


# user borrow points


@view 
@internal 
def _getLatestUserBorrowPoints(
    _user: address,
    _lastRipeRewardsBlock: uint256,
    _ledger: address,
    _cr: address,
) -> BorrowPoints:
    userPoints: BorrowPoints = staticcall Ledger(_ledger).userBorrowPoints(_user)

    # get last ripe rewards block
    lastRipeRewardsBlock: uint256 = _lastRipeRewardsBlock
    if lastRipeRewardsBlock == 0:
        lastRipeRewardsBlock = self._getLatestRipeRewards(_ledger, _cr).lastRewardsBlock

    # update borrow points
    if userPoints.lastUpdate != 0 and lastRipeRewardsBlock > userPoints.lastUpdate:
        elapsedBlocks: uint256 = lastRipeRewardsBlock - userPoints.lastUpdate
        userPoints.points += userPoints.lastPrincipal * elapsedBlocks

    # Note: will update `lastPrincipal` later in flow (if necessary)

    userPoints.lastUpdate = block.number
    return userPoints


@view
@external
def getLatestUserBorrowPoints(_user: address) -> BorrowPoints:
    # used mostly for testing
    addys: address[3] = self._getAddys()
    ledger: address = addys[0]
    controlRoom: address = addys[2]
    return self._getLatestUserBorrowPoints(_user, 0, ledger, controlRoom)


###################
# Points Combined #
###################


@external
def updatePoints(_user: address, _vaultId: uint256, _asset: address):
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(TELLER_ID) # dev: only Teller allowed
    # TODO: implement


# deposit points


@view
@internal
def _getLatestDepositPoints(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _lastRipeRewardsBlock: uint256,
    _asset: address,
    _addys: address[3],
) -> (GlobalDepositPoints, AssetDepositPoints, UserDepositPoints):
    ledger: address = _addys[0]
    vaultBook: address = _addys[1]
    controlRoom: address = _addys[2]

    # global deposit points
    globalPoints: GlobalDepositPoints = self._getLatestGlobalDepositPoints(_lastRipeRewardsBlock, ledger, controlRoom)

    # asset deposit points
    assetPoints: AssetDepositPoints = empty(AssetDepositPoints)
    isStakedAsset: bool = False
    assetPoints, isStakedAsset = self._getLatestAssetDepositPoints(_vaultId, _asset, _lastRipeRewardsBlock, ledger, vaultBook, controlRoom)

    # get latest asset value (staked assets not eligible for gen deposit rewards)
    newAssetUsdValue: uint256 = 0
    if not isStakedAsset:
        totalAmount: uint256 = staticcall Vault(_vaultAddr).getTotalAmountForVault(_asset)
        newAssetUsdValue = 0 # PriceDesk(_priceDesk). # TODO implement price desk
        if newAssetUsdValue != 0:
            newAssetUsdValue = newAssetUsdValue // EIGHTEEN_DECIMALS # normalize to help reduce risk of integer overflow

    # update `lastUsdValue` for global + asset
    if newAssetUsdValue != assetPoints.lastUsdValue:
        globalPoints.lastUsdValue -= assetPoints.lastUsdValue
        globalPoints.lastUsdValue += newAssetUsdValue
        assetPoints.lastUsdValue = newAssetUsdValue

    # nothing else to do here
    if _user == empty(address):
        return globalPoints, assetPoints, empty(UserDepositPoints)

    # get user loot share
    userLootShare: uint256 = staticcall Vault(_vaultAddr).getUserLootBoxShare(_user, _asset)
    userLootShare = userLootShare // assetPoints.precision

    # update `lastBalance`
    userPoints: UserDepositPoints = self._getLatestUserDepositPoints(_user, _vaultId, _asset, ledger)
    assetPoints.lastBalance -= userPoints.lastBalance
    assetPoints.lastBalance += userLootShare
    userPoints.lastBalance = userLootShare

    return globalPoints, assetPoints, userPoints


@view
@external
def getLatestDepositPoints(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
) -> (GlobalDepositPoints, AssetDepositPoints, UserDepositPoints):
    return self._getLatestDepositPoints(_user, _vaultId, _vaultAddr, 0, _asset, self._getAddys())


# borrow points


@view 
@internal 
def _getLatestBorrowPoints(
    _user: address,
    _didDebtChange: bool,
    _lastRipeRewardsBlock: uint256,
    _ledger: address,
    _cr: address,
) -> (BorrowPoints, BorrowPoints):

    # global points
    globalPoints: BorrowPoints = self._getLatestGlobalBorrowPoints(_lastRipeRewardsBlock, _ledger, _cr)
    if _user == empty(address):
        return empty(BorrowPoints), globalPoints

    # user borrow points
    userPoints: BorrowPoints = self._getLatestUserBorrowPoints(_user, _lastRipeRewardsBlock, _ledger, _cr)
    if not _didDebtChange:
        return userPoints, globalPoints

    # get user debt (principal only)
    userDebt: uint256 = 0 # TODO get user debt
    if userDebt != 0:
        userDebt = userDebt // EIGHTEEN_DECIMALS

    # update `lastPrincipal`
    globalPoints.lastPrincipal -= userPoints.lastPrincipal
    globalPoints.lastPrincipal += userDebt
    userPoints.lastPrincipal = userDebt

    return userPoints, globalPoints


@view
@external
def getLatestBorrowPoints(_user: address, _didDebtChange: bool) -> (BorrowPoints, BorrowPoints):
    addys: address[3] = self._getAddys()
    ledger: address = addys[0]
    controlRoom: address = addys[2]
    return self._getLatestBorrowPoints(_user, _didDebtChange, 0, ledger, controlRoom)


@external
def updateBorrowPoints(_user: address, _didDebtChange: bool):
    assert msg.sender == staticcall AddyRegistry(ADDY_REGISTRY).getAddy(TELLER_ID) # dev: only Teller allowed
    # TODO: implement