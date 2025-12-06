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
HOUR_IN_BLOCKS: constant(uint256) = 1_800
DAY_IN_BLOCKS: constant(uint256) = 24 * HOUR_IN_BLOCKS
WEEK_IN_BLOCKS: constant(uint256) = 7 * DAY_IN_BLOCKS
MONTH_IN_BLOCKS: constant(uint256) = 30 * DAY_IN_BLOCKS
YEAR_IN_BLOCKS: constant(uint256) = 365 * DAY_IN_BLOCKS

# addresses
CONTRIB_TEMPLATE: constant(address) = 0x4965578D80E54b5EbE3BB5D7b1B3E0425559C1D1
TRAINING_WHEELS: constant(address) = 0x2255b0006A3DA38AA184E0F9d5e056C2d0448065
UNDERSCORE_REGISTRY: constant(address) = 0x44Cf3c4f000DFD76a35d03298049D37bE688D6F9


@deploy
def __init__():
    pass


# general config


@view
@external
def genConfig() -> cs.GenConfig:
    return cs.GenConfig(
        perUserMaxVaults = 5,
        perUserMaxAssetsPerVault = 15,
        priceStaleTime = 0,
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
        perUserDebtLimit = 20_000 * EIGHTEEN_DECIMALS,
        globalDebtLimit = 200_000 * EIGHTEEN_DECIMALS,
        minDebtAmount = 1 * EIGHTEEN_DECIMALS,
        numAllowedBorrowers = 1000,
        maxBorrowPerInterval = 10_000 * EIGHTEEN_DECIMALS,
        numBlocksPerInterval = 1 * DAY_IN_BLOCKS,
        minDynamicRateBoost = 1 * HUNDRED_PERCENT,
        maxDynamicRateBoost = 5 * HUNDRED_PERCENT,
        increasePerDangerBlock = 10,
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
        asset = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913,
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
        ripePerBlock = 75 * 10**14,
        borrowersAlloc = 10_00,
        stakersAlloc = 90_00,
        votersAlloc = 0,
        genDepositorsAlloc = 0,
        autoStakeRatio = 75_00,
        autoStakeDurationRatio = 33_00,
        stabPoolRipePerDollarClaimed = 1 * 10**16,
    )



# ripe gov vault configs


@view
@external
def ripeGovVaultConfigs() -> DynArray[cs.RipeGovVaultConfigEntry, 5]:
    return [
        # RIPE
        cs.RipeGovVaultConfigEntry(
            asset=0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0,
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
        # vAMM-RIPE/WETH
        cs.RipeGovVaultConfigEntry(
            asset=0x765824aD2eD0ECB70ECc25B0Cf285832b335d6A9,
            config=cs.RipeGovVaultConfig(
                lockTerms=cs.LockTerms(
                    minLockDuration=1 * DAY_IN_BLOCKS,
                    maxLockDuration=3 * YEAR_IN_BLOCKS,
                    maxLockBoost=2 * HUNDRED_PERCENT,
                    canExit=True,
                    exitFee=80_00,
                ),
                assetWeight=150_00,
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
        # undyUSD
        # USD Value: $114.3k
        cs.AssetConfigEntry(asset=0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf, config=cs.AssetConfig(
            vaultIds=[5],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=5 * 10**10,  # $50.2k
            globalDepositLimit=25 * 10**10,  # $251.0k
            minDepositBalance=100_000,  # $0.1004
            debtTerms=cs.DebtTerms(
                ltv=80_00,
                redemptionThreshold=85_00,
                liqThreshold=90_00,
                liqFee=5_00,
                borrowRate=5_00,
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
        # USDC
        # USD Value: $762.41
        cs.AssetConfigEntry(asset=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=100_000_000,  # $99.99
            globalDepositLimit=1 * 10**9,  # $999.88
            minDepositBalance=250_000,  # $0.2500
            debtTerms=cs.DebtTerms(
                ltv=80_00,
                redemptionThreshold=85_00,
                liqThreshold=90_00,
                liqFee=5_00,
                borrowRate=5_00,
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
        # sUSDe
        # USD Value: $1.00
        cs.AssetConfigEntry(asset=0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=6_000 * EIGHTEEN_DECIMALS,  # $7.2k
            globalDepositLimit=60_000 * EIGHTEEN_DECIMALS,  # $72.4k
            minDepositBalance=1 * 10**16,  # $0.0121
            debtTerms=cs.DebtTerms(
                ltv=80_00,
                redemptionThreshold=85_00,
                liqThreshold=90_00,
                liqFee=5_00,
                borrowRate=5_00,
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
        # undyEURC
        # USD Value: $0.00
        cs.AssetConfigEntry(asset=0x1cb8DAB80f19fC5Aca06C2552AECd79015008eA8, config=cs.AssetConfig(
            vaultIds=[5],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=1 * 10**9,  # $1.2k
            globalDepositLimit=1 * 10**10,  # $11.7k
            minDepositBalance=100_000,  # $0.1165
            debtTerms=cs.DebtTerms(
                ltv=80_00,
                redemptionThreshold=85_00,
                liqThreshold=90_00,
                liqFee=5_00,
                borrowRate=5_00,
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
        # USD Value: $4.7k
        cs.AssetConfigEntry(asset=0x4200000000000000000000000000000000000006, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=8 * 10**17,  # $2.4k
            globalDepositLimit=8 * EIGHTEEN_DECIMALS,  # $24.3k
            minDepositBalance=8 * 10**13,  # $0.2430
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
        # undyETH
        # USD Value: $3.1k
        cs.AssetConfigEntry(asset=0x02981DB1a99A14912b204437e7a2E02679B57668, config=cs.AssetConfig(
            vaultIds=[5],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=25 * 10**16,  # $759.93
            globalDepositLimit=25 * 10**17,  # $7.6k
            minDepositBalance=25 * 10**12,  # $0.0760
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
        # cbETH
        # USD Value: $2.7k
        cs.AssetConfigEntry(asset=0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=8 * 10**17,  # $2.7k
            globalDepositLimit=8 * EIGHTEEN_DECIMALS,  # $27.1k
            minDepositBalance=8 * 10**13,  # $0.2707
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
        # cbBTC
        # USD Value: $1.8k
        cs.AssetConfigEntry(asset=0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=2_500_000,  # $2.2k
            globalDepositLimit=25_000_000,  # $22.3k
            minDepositBalance=25,  # $0.0223
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
        # wsuperOETHb
        # USD Value: $1.2k
        cs.AssetConfigEntry(asset=0x7FcD174E80f264448ebeE8c88a7C4476AAF58Ea6, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=16 * 10**17,  # $5.3k
            globalDepositLimit=16 * EIGHTEEN_DECIMALS,  # $52.7k
            minDepositBalance=8 * 10**13,  # $0.2634
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
        # undyBTC
        # USD Value: $106.52
        cs.AssetConfigEntry(asset=0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493, config=cs.AssetConfig(
            vaultIds=[5],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=1_000_000,  # $893.90
            globalDepositLimit=10_000_000,  # $8.9k
            minDepositBalance=100,  # $0.0894
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
        # VIRTUAL
        # USD Value: $1.1k
        cs.AssetConfigEntry(asset=0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=2_000 * EIGHTEEN_DECIMALS,  # $1.7k
            globalDepositLimit=20_000 * EIGHTEEN_DECIMALS,  # $17.0k
            minDepositBalance=1 * EIGHTEEN_DECIMALS,  # $0.8495
            debtTerms=cs.DebtTerms(
                ltv=50_00,
                redemptionThreshold=60_00,
                liqThreshold=65_00,
                liqFee=12_00,
                borrowRate=11_00,
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
        # AERO
        # USD Value: $881.58
        cs.AssetConfigEntry(asset=0x940181a94A35A4569E4529A3CDfB74e38FD98631, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=3_000 * EIGHTEEN_DECIMALS,  # $2.0k
            globalDepositLimit=30_000 * EIGHTEEN_DECIMALS,  # $20.4k
            minDepositBalance=1 * EIGHTEEN_DECIMALS,  # $0.6787
            debtTerms=cs.DebtTerms(
                ltv=50_00,
                redemptionThreshold=60_00,
                liqThreshold=65_00,
                liqFee=10_00,
                borrowRate=8_00,
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
        # uSOL
        # USD Value: $224.19
        cs.AssetConfigEntry(asset=0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=15 * EIGHTEEN_DECIMALS,  # $2.0k
            globalDepositLimit=150 * EIGHTEEN_DECIMALS,  # $19.8k
            minDepositBalance=15 * 10**14,  # $0.1983
            debtTerms=cs.DebtTerms(
                ltv=50_00,
                redemptionThreshold=60_00,
                liqThreshold=65_00,
                liqFee=12_00,
                borrowRate=11_00,
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
        # cbDOGE
        # USD Value: $39.94
        cs.AssetConfigEntry(asset=0xcbD06E5A2B0C65597161de254AA074E489dEb510, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=15 * 10**11,  # $2.1k
            globalDepositLimit=15 * 10**12,  # $21.0k
            minDepositBalance=150_000_000,  # $0.2100
            debtTerms=cs.DebtTerms(
                ltv=50_00,
                redemptionThreshold=60_00,
                liqThreshold=65_00,
                liqFee=12_00,
                borrowRate=11_00,
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
        # undyAERO
        # USD Value: $11.32
        cs.AssetConfigEntry(asset=0x96F1a7ce331F40afe866F3b707c223e377661087, config=cs.AssetConfig(
            vaultIds=[5],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=1_000 * EIGHTEEN_DECIMALS,  # $679.46
            globalDepositLimit=10_000 * EIGHTEEN_DECIMALS,  # $6.8k
            minDepositBalance=1 * 10**17,  # $0.0679
            debtTerms=cs.DebtTerms(
                ltv=50_00,
                redemptionThreshold=60_00,
                liqThreshold=65_00,
                liqFee=12_00,
                borrowRate=8_00,
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
        # cbADA
        # USD Value: $0.00
        cs.AssetConfigEntry(asset=0xcbADA732173e39521CDBE8bf59a6Dc85A9fc7b8c, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=375 * 10**7,  # $1.5k
            globalDepositLimit=375 * 10**8,  # $15.5k
            minDepositBalance=1_000_000,  # $0.4124
            debtTerms=cs.DebtTerms(
                ltv=50_00,
                redemptionThreshold=60_00,
                liqThreshold=65_00,
                liqFee=12_00,
                borrowRate=11_00,
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
        # cbXRP
        # USD Value: $0.00
        cs.AssetConfigEntry(asset=0xcb585250f852C6c6bf90434AB21A00f02833a4af, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=1 * 10**9,  # $2.0k
            globalDepositLimit=1 * 10**10,  # $20.3k
            minDepositBalance=333_333,  # $0.6753
            debtTerms=cs.DebtTerms(
                ltv=50_00,
                redemptionThreshold=60_00,
                liqThreshold=65_00,
                liqFee=12_00,
                borrowRate=11_00,
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
        # cbLTC
        # USD Value: $0.00
        cs.AssetConfigEntry(asset=0xcb17C9Db87B595717C857a08468793f5bAb6445F, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=25 * 10**8,  # $2.0k
            globalDepositLimit=25 * 10**9,  # $20.4k
            minDepositBalance=800_000,  # $0.6535
            debtTerms=cs.DebtTerms(
                ltv=50_00,
                redemptionThreshold=60_00,
                liqThreshold=65_00,
                liqFee=12_00,
                borrowRate=11_00,
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
        # VVV
        # USD Value: $325.24
        cs.AssetConfigEntry(asset=0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=1_100 * EIGHTEEN_DECIMALS,  # $1.2k
            globalDepositLimit=11_000 * EIGHTEEN_DECIMALS,  # $12.1k
            minDepositBalance=11 * 10**16,  # $0.1213
            debtTerms=cs.DebtTerms(
                ltv=40_00,
                redemptionThreshold=45_00,
                liqThreshold=50_00,
                liqFee=15_00,
                borrowRate=13_00,
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
        # DEGEN
        # USD Value: $202.52
        cs.AssetConfigEntry(asset=0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=750_000 * EIGHTEEN_DECIMALS,  # $1.0k
            globalDepositLimit=7_500_000 * EIGHTEEN_DECIMALS,  # $10.4k
            minDepositBalance=75 * EIGHTEEN_DECIMALS,  # $0.1043
            debtTerms=cs.DebtTerms(
                ltv=40_00,
                redemptionThreshold=45_00,
                liqThreshold=50_00,
                liqFee=15_00,
                borrowRate=13_00,
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
        # WELL
        # USD Value: $121.52
        cs.AssetConfigEntry(asset=0xA88594D404727625A9437C3f886C7643872296AE, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=100_000 * EIGHTEEN_DECIMALS,  # $1.0k
            globalDepositLimit=1_000_000 * EIGHTEEN_DECIMALS,  # $10.1k
            minDepositBalance=10 * EIGHTEEN_DECIMALS,  # $0.1014
            debtTerms=cs.DebtTerms(
                ltv=40_00,
                redemptionThreshold=45_00,
                liqThreshold=50_00,
                liqFee=15_00,
                borrowRate=13_00,
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
        # USD Value: $295.5k
        cs.AssetConfigEntry(asset=0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0, config=cs.AssetConfig(
            vaultIds=[2],
            stakersPointsAlloc=15_00,
            voterPointsAlloc=0,
            perUserDepositLimit=100_000_000 * EIGHTEEN_DECIMALS,  # $108.7M
            globalDepositLimit=1_000_000_000 * EIGHTEEN_DECIMALS,  # $1087.0M
            minDepositBalance=1 * 10**14,  # $0.000109
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
        # GREEN/USDC
        # USD Value: $59.5k
        cs.AssetConfigEntry(asset=0xd6c283655B42FA0eb2685F7AB819784F071459dc, config=cs.AssetConfig(
            vaultIds=[1],
            stakersPointsAlloc=25_00,
            voterPointsAlloc=0,
            perUserDepositLimit=100_000_000 * EIGHTEEN_DECIMALS,  # $100.2M
            globalDepositLimit=1_000_000_000 * EIGHTEEN_DECIMALS,  # $1001.9M
            minDepositBalance=1 * 10**16,  # $0.0100
            debtTerms=cs.DebtTerms(
                ltv=0,
                redemptionThreshold=0,
                liqThreshold=0,
                liqFee=0,
                borrowRate=0,
                daowry=0,
            ),
            shouldBurnAsPayment=False,
            shouldTransferToEndaoment=True,
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
        # sGREEN
        # USD Value: $58.3k
        cs.AssetConfigEntry(asset=0xaa0f13488CE069A7B5a099457c753A7CFBE04d36, config=cs.AssetConfig(
            vaultIds=[1],
            stakersPointsAlloc=15_00,
            voterPointsAlloc=0,
            perUserDepositLimit=100_000_000 * EIGHTEEN_DECIMALS,  # $106.3M
            globalDepositLimit=1_000_000_000 * EIGHTEEN_DECIMALS,  # $1062.7M
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
        # vAMM-RIPE/WETH
        # USD Value: $0.00
        cs.AssetConfigEntry(asset=0x765824aD2eD0ECB70ECc25B0Cf285832b335d6A9, config=cs.AssetConfig(
            vaultIds=[2],
            stakersPointsAlloc=45_00,
            voterPointsAlloc=0,
            perUserDepositLimit=100_000_000 * EIGHTEEN_DECIMALS,
            globalDepositLimit=1_000_000_000 * EIGHTEEN_DECIMALS,
            minDepositBalance=1 * 10**15,
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
        # GREEN
        # USD Value: $0.00
        cs.AssetConfigEntry(asset=0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707, config=cs.AssetConfig(
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
    cs.VaultLite(vaultId=3, asset=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913), # USDC
    cs.VaultLite(vaultId=3, asset=0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf), # cbBTC
    cs.VaultLite(vaultId=3, asset=0x4200000000000000000000000000000000000006), # WETH
    cs.VaultLite(vaultId=3, asset=0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55), # uSOL
    cs.VaultLite(vaultId=3, asset=0xcbD06E5A2B0C65597161de254AA074E489dEb510), # cbDOGE
    ]


@view
@external
def priorityStabVaults() -> DynArray[cs.VaultLite, 20]:
    return [
    cs.VaultLite(vaultId=1, asset=0xd6c283655B42FA0eb2685F7AB819784F071459dc), # GREEN/USDC
    cs.VaultLite(vaultId=1, asset=0xaa0f13488CE069A7B5a099457c753A7CFBE04d36), # sGREEN
    ]


@view
@external
def priorityPriceSourceIds() -> DynArray[uint256, 10]:
    return [1, 3, 4, 5, 2]

# lite signers


@view
@external
def liteSigners() -> DynArray[address, 10]:
    return []
