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
            perUserDepositLimit=49_796_932_480,  # $50.0k
            globalDepositLimit=248_984_662_440,  # $250.0k
            minDepositBalance=99_593,  # $0.1000
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
        # USD Value: $762.33
        cs.AssetConfigEntry(asset=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=100_000_000,  # $99.98
            globalDepositLimit=1 * 10**9,  # $999.77
            minDepositBalance=250_000,  # $0.2499
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
            perUserDepositLimit=4_138_925_278_549_878_192_670,  # $5.0k
            globalDepositLimit=20_694_626_392_749_390_963_353,  # $25.0k
            minDepositBalance=82_778_505_570_997_563,  # $0.1000
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
            perUserDepositLimit=4_290_904_101,  # $5.0k
            globalDepositLimit=21_454_520_508,  # $25.0k
            minDepositBalance=85_818,  # $0.1000
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
            perUserDepositLimit=1_646_052_728_169_408_091,  # $5.0k
            globalDepositLimit=8_230_263_640_847_040_458,  # $25.0k
            minDepositBalance=32_921_054_563_388,  # $0.1000
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
            perUserDepositLimit=16_447_676_038_471_417_830,  # $50.0k
            globalDepositLimit=82_238_380_192_357_089_170,  # $250.0k
            minDepositBalance=32_895_352_076_942,  # $0.1000
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
            perUserDepositLimit=1_478_101_461_711_344_160,  # $5.0k
            globalDepositLimit=7_390_507_308_556_720_802,  # $25.0k
            minDepositBalance=29_562_029_234_226,  # $0.1000
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
            perUserDepositLimit=5_554_381,  # $5.0k
            globalDepositLimit=27_771_905,  # $25.0k
            minDepositBalance=111,  # $0.0999
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
            perUserDepositLimit=1_518_552_436_330_112_774,  # $5.0k
            globalDepositLimit=7_592_762_181_650_563_870,  # $25.0k
            minDepositBalance=30_371_048_726_602,  # $0.1000
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
        # USD Value: $107.28
        cs.AssetConfigEntry(asset=0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493, config=cs.AssetConfig(
            vaultIds=[5],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=55_541_110,  # $50.0k
            globalDepositLimit=277_705_550,  # $250.0k
            minDepositBalance=111,  # $0.0999
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
        # USD Value: $1.0k
        cs.AssetConfigEntry(asset=0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=6_041_731_690_803_988_944_597,  # $5.0k
            globalDepositLimit=30_208_658_454_019_944_722_988,  # $25.0k
            minDepositBalance=120_834_633_816_079_778,  # $0.1000
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
        # USD Value: $846.54
        cs.AssetConfigEntry(asset=0x940181a94A35A4569E4529A3CDfB74e38FD98631, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=7_671_774_247_547_778_735_965,  # $5.0k
            globalDepositLimit=38_358_871_237_738_893_679_826,  # $25.0k
            minDepositBalance=153_435_484_950_955_574,  # $0.1000
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
        # USD Value: $222.96
        cs.AssetConfigEntry(asset=0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=38_021_075_364_647_256_084,  # $5.0k
            globalDepositLimit=190_105_376_823_236_280_420,  # $25.0k
            minDepositBalance=760_421_507_292_945,  # $0.1000
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
        # USD Value: $39.37
        cs.AssetConfigEntry(asset=0xcbD06E5A2B0C65597161de254AA074E489dEb510, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=3_623_605_908_216,  # $5.0k
            globalDepositLimit=18_118_029_541_084,  # $25.0k
            minDepositBalance=72_472_118,  # $0.1000
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
        # USD Value: $10.87
        cs.AssetConfigEntry(asset=0x96F1a7ce331F40afe866F3b707c223e377661087, config=cs.AssetConfig(
            vaultIds=[5],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=7_663_356_320_898_015_168_529,  # $5.0k
            globalDepositLimit=38_316_781_604_490_075_842_648,  # $25.0k
            minDepositBalance=153_267_126_417_960_303,  # $0.1000
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
            perUserDepositLimit=12_008_521_246,  # $5.0k
            globalDepositLimit=60_042_606_233,  # $25.0k
            minDepositBalance=240_170,  # $0.1000
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
            perUserDepositLimit=2_458_282_938,  # $5.0k
            globalDepositLimit=12_291_414_692,  # $25.0k
            minDepositBalance=49_165,  # $0.1000
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
            perUserDepositLimit=6_169_282_648,  # $5.0k
            globalDepositLimit=30_846_413_240,  # $25.0k
            minDepositBalance=123_385,  # $0.1000
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
        # USD Value: $320.26
        cs.AssetConfigEntry(asset=0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=4_606_534_640_251_433_505_211,  # $5.0k
            globalDepositLimit=23_032_673_201_257_167_526_057,  # $25.0k
            minDepositBalance=92_130_692_805_028_670,  # $0.1000
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
        # USD Value: $216.84
        cs.AssetConfigEntry(asset=0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=3_358_702_734_655_766_556_725_130,  # $5.0k
            globalDepositLimit=16_793_513_673_278_832_783_625_652,  # $25.0k
            minDepositBalance=67_174_054_693_115_331_134,  # $0.1000
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
        # USD Value: $117.56
        cs.AssetConfigEntry(asset=0xA88594D404727625A9437C3f886C7643872296AE, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=509_796_764_421_895_567_113_214,  # $5.0k
            globalDepositLimit=2_548_983_822_109_477_835_566_073,  # $25.0k
            minDepositBalance=10_195_935_288_437_911_342,  # $0.1000
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
        # USD Value: $295.7k
        cs.AssetConfigEntry(asset=0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0, config=cs.AssetConfig(
            vaultIds=[2],
            stakersPointsAlloc=15_00,
            voterPointsAlloc=0,
            perUserDepositLimit=100_000_000 * EIGHTEEN_DECIMALS,  # $108.7M
            globalDepositLimit=1_000_000_000 * EIGHTEEN_DECIMALS,  # $1086.5M
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
        # USD Value: $58.7k
        cs.AssetConfigEntry(asset=0xd6c283655B42FA0eb2685F7AB819784F071459dc, config=cs.AssetConfig(
            vaultIds=[1],
            stakersPointsAlloc=25_00,
            voterPointsAlloc=0,
            perUserDepositLimit=100_000_000 * EIGHTEEN_DECIMALS,  # $100.2M
            globalDepositLimit=1_000_000_000 * EIGHTEEN_DECIMALS,  # $1001.8M
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
    cs.VaultLite(vaultId=3, asset=0x4200000000000000000000000000000000000006), # WETH
    cs.VaultLite(vaultId=3, asset=0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22), # cbETH
    cs.VaultLite(vaultId=3, asset=0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf), # cbBTC
    cs.VaultLite(vaultId=5, asset=0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493), # undyBTC
    cs.VaultLite(vaultId=5, asset=0x02981DB1a99A14912b204437e7a2E02679B57668), # undyETH
    cs.VaultLite(vaultId=3, asset=0x940181a94A35A4569E4529A3CDfB74e38FD98631), # AERO
    cs.VaultLite(vaultId=5, asset=0x96F1a7ce331F40afe866F3b707c223e377661087), # undyAERO
    cs.VaultLite(vaultId=3, asset=0xcbADA732173e39521CDBE8bf59a6Dc85A9fc7b8c), # cbADA
    cs.VaultLite(vaultId=3, asset=0xcb585250f852C6c6bf90434AB21A00f02833a4af), # cbXRP
    cs.VaultLite(vaultId=3, asset=0xcb17C9Db87B595717C857a08468793f5bAb6445F), # cbLTC
    cs.VaultLite(vaultId=3, asset=0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55), # uSOL
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
    return [1, 8, 2, 9, 4, 5]

# lite signers


@view
@external
def liteSigners() -> DynArray[address, 10]:
    return [
        0x1c419AeF78b44F30D8F3Dfa2aB13D3538466dc48,
        0x6f5ef229d7F07183Bf91dF68702D01E9bDa37cA2
    ]
