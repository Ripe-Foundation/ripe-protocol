# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

implements: Defaults
from interfaces import Defaults
import interfaces.ConfigStructs as cs

EIGHTEEN_DECIMALS: constant(uint256) = 10 ** 18
HUNDRED_PERCENT: constant(uint256) = 100_00

# seconds
DAY_IN_SECONDS: constant(uint256) = 60 * 60 * 24
WEEK_IN_SECONDS: constant(uint256) = 7 * DAY_IN_SECONDS
MONTH_IN_SECONDS: constant(uint256) = 30 * DAY_IN_SECONDS
YEAR_IN_SECONDS: constant(uint256) = 365 * DAY_IN_SECONDS

# blocks
# NOTE: Robinhood is an Arbitrum L2. Child blocks are produced in ~100ms, but EVM
# `block.number` is the ancestor (Ethereum L1) estimate, which advances every ~12s
# and repeats across many child blocks. Every duration below is denominated in
# `block.number`, so the clock here is 12s -- not the 100ms child cadence. The
# actual child height is only reachable via `ArbSys(0x64).arbBlockNumber()`, which
# is why Ledger takes an explicit action-block source.
BLOCKS_PER_MINUTE: constant(uint256) = 5 # 12s per `block.number`
HOUR_IN_BLOCKS: constant(uint256) = 60 * BLOCKS_PER_MINUTE
DAY_IN_BLOCKS: constant(uint256) = 24 * HOUR_IN_BLOCKS
WEEK_IN_BLOCKS: constant(uint256) = 7 * DAY_IN_BLOCKS
MONTH_IN_BLOCKS: constant(uint256) = 30 * DAY_IN_BLOCKS
YEAR_IN_BLOCKS: constant(uint256) = 365 * DAY_IN_BLOCKS

# addresses
UNDERSCORE_REGISTRY: constant(address) = empty(address)
CONTRIB_TEMPLATE: immutable(address)
TRAINING_WHEELS: immutable(address)
RIPE_TOKEN:  immutable(address)
GREEN_TOKEN: immutable(address)
SGREEN_TOKEN: immutable(address)

@deploy
def __init__(
    _contribTemplate: address,
    _trainingWheels: address,
    _ripeToken: address,
    _greenToken: address,
    _sgreenToken: address   
):
    CONTRIB_TEMPLATE = _contribTemplate
    TRAINING_WHEELS = _trainingWheels
    RIPE_TOKEN = _ripeToken
    GREEN_TOKEN = _greenToken
    SGREEN_TOKEN = _sgreenToken


# general config


@view
@external
def genConfig() -> cs.GenConfig:
    return cs.GenConfig(
        perUserMaxVaults = 5,
        perUserMaxAssetsPerVault = 15,
        priceStaleTime = 1 * DAY_IN_SECONDS,
        canDeposit = True,
        canWithdraw = True,
        canBorrow = True,
        canRepay = True,
        canClaimLoot = True,
        canLiquidate = True,
        canRedeemCollateral = True,
        canRedeemInStabPool = True,
        canBuyInAuction = True,
        canClaimInStabPool = True,
    )


# debt config


@view
@external
def genDebtConfig() -> cs.GenDebtConfig:
    return cs.GenDebtConfig(
        perUserDebtLimit = 50 * EIGHTEEN_DECIMALS,
        globalDebtLimit = 500 * EIGHTEEN_DECIMALS,
        minDebtAmount = 1 * EIGHTEEN_DECIMALS,
        numAllowedBorrowers = 20,
        maxBorrowPerInterval = 50 * EIGHTEEN_DECIMALS,
        numBlocksPerInterval = 1 * DAY_IN_BLOCKS,
        minDynamicRateBoost = 1 * HUNDRED_PERCENT,
        maxDynamicRateBoost = 5 * HUNDRED_PERCENT,
        increasePerDangerBlock = 60,
        maxBorrowRate = 1 * HUNDRED_PERCENT,
        maxLtvDeviation = 10_00,
        keeperFeeRatio = 1_00,
        minKeeperFee = 1 * EIGHTEEN_DECIMALS,
        maxKeeperFee = 25_000 * EIGHTEEN_DECIMALS,
        isDaowryEnabled = True,
        ltvPaybackBuffer = 10_00,
        genAuctionParams = cs.AuctionParams(
            hasParams = True,
            startDiscount = 1_00,
            maxDiscount = 50_00,
            delay = 0,
            duration = 1 * DAY_IN_BLOCKS,
        ),
    )


# ripe available


@view
@external
def ripeAvailForRewards() -> uint256:
    return 1_000 * EIGHTEEN_DECIMALS


@view
@external
def ripeAvailForHr() -> uint256:
    return 1_000 * EIGHTEEN_DECIMALS


@view
@external
def ripeAvailForBonds() -> uint256:
    return 1_000 * EIGHTEEN_DECIMALS


# ripe bond config


@view
@external
def ripeBondConfig() -> cs.RipeBondConfig:
    return cs.RipeBondConfig(
        asset = 0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168,
        amountPerEpoch = 2000 * (10 ** 6),
        canBond = False,
        minRipePerUnit = 0,
        maxRipePerUnit = 1 * EIGHTEEN_DECIMALS,
        maxRipePerUnitLockBonus = 2 * HUNDRED_PERCENT,
        epochLength = 8 * HOUR_IN_BLOCKS,
        shouldAutoRestart = True,
        restartDelayBlocks = 0,
    )


# ripe rewards config


@view
@external
def rewardsConfig() -> cs.RipeRewardsConfig:
    return cs.RipeRewardsConfig(
        arePointsEnabled = True,
        ripePerBlock = 9 * 10**15, #0.009 RIPE
        borrowersAlloc = 10_00,
        stakersAlloc = 90_00,
        votersAlloc = 0,
        genDepositorsAlloc = 0,
        autoStakeRatio = 75_00,
        autoStakeDurationRatio = 33_00,
        stabPoolRipePerDollarClaimed = 1 * 10**18, #1 RIPE per $1 claimed
    )



# ripe gov vault configs


@view
@external
def ripeGovVaultConfigs() -> DynArray[cs.RipeGovVaultConfigEntry, 5]:
    return [
        # RIPE
        cs.RipeGovVaultConfigEntry(
            asset=RIPE_TOKEN,
            config=cs.RipeGovVaultConfig(
                lockTerms=cs.LockTerms(
                    minLockDuration=1 * DAY_IN_BLOCKS,
                    maxLockDuration=3 * YEAR_IN_BLOCKS,
                    maxLockBoost=2 * HUNDRED_PERCENT,
                    canExit=True,
                    exitFee=80_00,
                ),
                assetWeight=1 * HUNDRED_PERCENT,
                shouldFreezeWhenBadDebt=True,
            ),
        ),
    ]


# hr config


@view
@external
def hrConfig() -> cs.HrConfig:
    return cs.HrConfig(
        contribTemplate = CONTRIB_TEMPLATE,
        maxCompensation = 0, # set this later, after core contributor vesting setup
        minCliffLength = 1 * WEEK_IN_SECONDS,
        maxStartDelay = 3 * MONTH_IN_SECONDS,
        minVestingLength = 1 * WEEK_IN_SECONDS,
        maxVestingLength = 10 * YEAR_IN_SECONDS,
    )


# underscore registry


@view
@external
def underscoreRegistry() -> address:
    return UNDERSCORE_REGISTRY


# training wheels


@view
@external
def trainingWheels() -> address:
    return TRAINING_WHEELS


# should check last touch


@view
@external
def shouldCheckLastTouch() -> bool:
    return True

# asset configs


@view
@external
def assetConfigs() -> DynArray[cs.AssetConfigEntry, 50]:
    return [
        # SteakHouse USDG (Morpho)
        # USD Value: $114.3k
        cs.AssetConfigEntry(asset=0xBeEff033F34C046626B8D0A041844C5d1A5409dd, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=5_000 * 10**18,  # $5.0k
            globalDepositLimit=10_000 * 10**18,  # $10.0k
            minDepositBalance=10**16,  # $0.1000
            debtTerms=cs.DebtTerms(
                ltv=70_00,
                redemptionThreshold=77_00,
                liqThreshold=80_00,
                liqFee=10_00,
                borrowRate=6_00,
                daowry=25,
            ),
            shouldBurnAsPayment=False,
            shouldTransferToEndaoment=True,
            shouldSwapInStabPools=False,
            shouldAuctionInstantly=False,
            canDeposit=True,
            canWithdraw=True,
            canRedeemCollateral=False,
            canRedeemInStabPool=True,
            canBuyInAuction=True,
            canClaimInStabPool=True,
            specialStabPoolId=0,
            customAuctionParams=cs.AuctionParams(
                hasParams=False,
                startDiscount=0,
                maxDiscount=0,
                delay=0,
                duration=0,
            ),
            whitelist=empty(address),
            isNft=False,
        )),
        # WETH
        # USD Value: ~$2k
        cs.AssetConfigEntry(asset=0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=25 * 10**17,  # ~$5.0k
            globalDepositLimit=5 * 10**18,  # ~$10.0k
            minDepositBalance=10**14,  # $0.2000
            debtTerms=cs.DebtTerms(
                ltv=70_00,
                redemptionThreshold=77_00,
                liqThreshold=80_00,
                liqFee=10_00,
                borrowRate=7_00,
                daowry=25,
            ),
            shouldBurnAsPayment=False,
            shouldTransferToEndaoment=False,
            shouldSwapInStabPools=True,
            shouldAuctionInstantly=True,
            canDeposit=True,
            canWithdraw=True,
            canRedeemCollateral=True,
            canRedeemInStabPool=True,
            canBuyInAuction=True,
            canClaimInStabPool=True,
            specialStabPoolId=0,
            customAuctionParams=cs.AuctionParams(
                hasParams=False,
                startDiscount=0,
                maxDiscount=0,
                delay=0,
                duration=0,
            ),
            whitelist=empty(address),
            isNft=False,
        )),
        # RIPE
        cs.AssetConfigEntry(asset=RIPE_TOKEN, config=cs.AssetConfig(
            vaultIds=[2],
            stakersPointsAlloc=15_00,
            voterPointsAlloc=0,
            perUserDepositLimit=100_000_000 * EIGHTEEN_DECIMALS,  
            globalDepositLimit=1_000_000_000 * EIGHTEEN_DECIMALS, 
            minDepositBalance=1 * 10**14,  
            debtTerms=cs.DebtTerms(
                ltv=0,
                redemptionThreshold=0,
                liqThreshold=0,
                liqFee=0,
                borrowRate=0,
                daowry=0,
            ),
            shouldBurnAsPayment=False,
            shouldTransferToEndaoment=False,
            shouldSwapInStabPools=False,
            shouldAuctionInstantly=False,
            canDeposit=True,
            canWithdraw=True,
            canRedeemCollateral=False,
            canRedeemInStabPool=True,
            canBuyInAuction=True,
            canClaimInStabPool=True,
            specialStabPoolId=0,
            customAuctionParams=cs.AuctionParams(
                hasParams=False,
                startDiscount=0,
                maxDiscount=0,
                delay=0,
                duration=0,
            ),
            whitelist=empty(address),
            isNft=False,
        )),
        # sGREEN
        # USD Value: $58.3k
        cs.AssetConfigEntry(asset=SGREEN_TOKEN, config=cs.AssetConfig(
            vaultIds=[1],
            stakersPointsAlloc=15_00,
            voterPointsAlloc=0,
            perUserDepositLimit=100_000_000 * EIGHTEEN_DECIMALS,  # $106.3M
            globalDepositLimit=1_000_000_000 * EIGHTEEN_DECIMALS,  # $1062.5M
            minDepositBalance=1 * 10**16,  # $0.0106
            debtTerms=cs.DebtTerms(
                ltv=0,
                redemptionThreshold=0,
                liqThreshold=0,
                liqFee=0,
                borrowRate=0,
                daowry=0,
            ),
            shouldBurnAsPayment=True,
            shouldTransferToEndaoment=False,
            shouldSwapInStabPools=False,
            shouldAuctionInstantly=False,
            canDeposit=True,
            canWithdraw=True,
            canRedeemCollateral=False,
            canRedeemInStabPool=False,
            canBuyInAuction=False,
            canClaimInStabPool=False,
            specialStabPoolId=0,
            customAuctionParams=cs.AuctionParams(
                hasParams=False,
                startDiscount=0,
                maxDiscount=0,
                delay=0,
                duration=0,
            ),
            whitelist=empty(address),
            isNft=False,
        )),
        # GREEN
        # USD Value: $0.00
        cs.AssetConfigEntry(asset=GREEN_TOKEN, config=cs.AssetConfig(
            vaultIds=[],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=1,  # $0.00
            globalDepositLimit=2,  # $0.00
            minDepositBalance=1,  # $0.00000000
            debtTerms=cs.DebtTerms(
                ltv=0,
                redemptionThreshold=0,
                liqThreshold=0,
                liqFee=0,
                borrowRate=0,
                daowry=0,
            ),
            shouldBurnAsPayment=False,
            shouldTransferToEndaoment=False,
            shouldSwapInStabPools=False,
            shouldAuctionInstantly=False,
            canDeposit=False,
            canWithdraw=False,
            canRedeemCollateral=False,
            canRedeemInStabPool=False,
            canBuyInAuction=False,
            canClaimInStabPool=True,
            specialStabPoolId=0,
            customAuctionParams=cs.AuctionParams(
                hasParams=False,
                startDiscount=0,
                maxDiscount=0,
                delay=0,
                duration=0,
            ),
            whitelist=empty(address),
            isNft=False,
        )),
    ]

# priority lists


@view
@external
def priorityLiqAssetVaults() -> DynArray[cs.VaultLite, 20]:
    return [
    cs.VaultLite(vaultId=3, asset=0xBeEff033F34C046626B8D0A041844C5d1A5409dd), # SteakHouse USDG
    cs.VaultLite(vaultId=3, asset=0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73), # WETH
    ]


@view
@external
def priorityStabVaults() -> DynArray[cs.VaultLite, 20]:
    return [
        cs.VaultLite(vaultId=1, asset=SGREEN_TOKEN), # sGREEN
    ]


@view
@external
def priorityPriceSourceIds() -> DynArray[uint256, 10]:
    return [1, 2, 3]

# lite signers


@view
@external
def liteSigners() -> DynArray[address, 10]:
    return []
