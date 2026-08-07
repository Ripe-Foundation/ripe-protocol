# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

# GENERATED FILE -- do not edit by hand.
#
# Regenerate with:  python scripts/prepare_defaults.py
#
# This is the defaults contract for REPLACING a MissionControl or Ledger that
# already exists. DefaultsRobinhood.vy remains the launch config for a
# brand-new chain; the two are not interchangeable.
#
# Every value below was read off the live Robinhood deployment, so this is a
# snapshot of what governance has configured rather than a set of launch
# decisions. MissionControl and Ledger copy these into storage at
# construction, which is the only reason a replacement for either can come up
# matching what is already running.
#
# Percentages are basis points (100_00 == 100%). Durations are in
# `block.number`, which on this Arbitrum L2 advances roughly every 12s -- it
# is the L1 ancestor estimate and repeats across child blocks, so it is NOT
# the ~100ms child cadence. The true child height is only reachable through
# ArbSys(0x64).arbBlockNumber().

implements: Defaults
from interfaces import Defaults
import interfaces.ConfigStructs as cs

# addresses
UNDERSCORE_REGISTRY: constant(address) = empty(address)
CONTRIB_TEMPLATE: immutable(address)
TRAINING_WHEELS: immutable(address)
RIPE_TOKEN:  immutable(address)
GREEN_TOKEN: immutable(address)
SGREEN_TOKEN: immutable(address)
USDG_TOKEN: immutable(address)
WETH_TOKEN: immutable(address)

# Registered by governance after launch. Robinhood-only addresses, so they
# are constants here rather than constructor bindings.
ASSET_GREEN_USDG_POOL: constant(address) = 0x2fD13b49F970e8C6D89283056C1c6281214b7EB6
ASSET_SPCX: constant(address) = 0x4a0E65A3EcceC6dBe60AE065F2e7bb85Fae35eEa
ASSET_NVDA: constant(address) = 0xd0601CE157Db5bdC3162BbaC2a2C8aF5320D9EEC
ASSET_TSLA: constant(address) = 0x322F0929c4625eD5bAd873c95208D54E1c003b2d
ASSET_AAPL: constant(address) = 0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9
ASSET_GOOGL: constant(address) = 0x2e0847E8910a9732eB3fb1bb4b70a580ADAD4FE3
ASSET_GME: constant(address) = 0x1b0E319c6A659F002271B69dB8A7df2F911c153E
ASSET_RIPE_WETH_LP: constant(address) = 0xba6F6CBa1a4104000847d4fdccB676E99166CEcE


@deploy
def __init__(
    _contribTemplate: address,
    _trainingWheels: address,
    _ripeToken: address,
    _greenToken: address,
    _sgreenToken: address,
    _usdgToken: address,
    _wethToken: address,
):
    CONTRIB_TEMPLATE = _contribTemplate
    TRAINING_WHEELS = _trainingWheels
    RIPE_TOKEN = _ripeToken
    GREEN_TOKEN = _greenToken
    SGREEN_TOKEN = _sgreenToken
    USDG_TOKEN = _usdgToken
    WETH_TOKEN = _wethToken


@view
@external
def genConfig() -> cs.GenConfig:
    return cs.GenConfig(
        perUserMaxVaults=5,
        perUserMaxAssetsPerVault=15,
        priceStaleTime=86400,
        canDeposit=True,
        canWithdraw=True,
        canBorrow=True,
        canRepay=True,
        canClaimLoot=True,
        canLiquidate=True,
        canRedeemCollateral=True,
        canRedeemInStabPool=True,
        canBuyInAuction=True,
        canClaimInStabPool=True,
    )


@view
@external
def genDebtConfig() -> cs.GenDebtConfig:
    return cs.GenDebtConfig(
        perUserDebtLimit=50000000000000000000,
        globalDebtLimit=500000000000000000000,
        minDebtAmount=1000000000000000000,
        numAllowedBorrowers=20,
        maxBorrowPerInterval=25000000000000000000,
        numBlocksPerInterval=7200,
        minDynamicRateBoost=10000,
        maxDynamicRateBoost=50000,
        increasePerDangerBlock=60,
        maxBorrowRate=10000,
        maxLtvDeviation=1000,
        keeperFeeRatio=100,
        minKeeperFee=1000000000000000000,
        maxKeeperFee=25000000000000000000000,
        isDaowryEnabled=True,
        ltvPaybackBuffer=1000,
        genAuctionParams=cs.AuctionParams(
            hasParams=True,
            startDiscount=100,
            maxDiscount=5000,
            delay=0,
            duration=7200,
        ),
    )


@view
@external
def ripeAvailForRewards() -> uint256:
    return 999945968500000000000000


@view
@external
def ripeAvailForHr() -> uint256:
    return 0


@view
@external
def ripeAvailForBonds() -> uint256:
    return 1000000000000000000000000


@view
@external
def ripeBondConfig() -> cs.RipeBondConfig:
    return cs.RipeBondConfig(
        asset=USDG_TOKEN,
        amountPerEpoch=100000000,
        canBond=False,
        minRipePerUnit=0,
        maxRipePerUnit=50000000000000000000,
        maxRipePerUnitLockBonus=20000,
        epochLength=2400,
        shouldAutoRestart=True,
        restartDelayBlocks=600,
    )


@view
@external
def rewardsConfig() -> cs.RipeRewardsConfig:
    return cs.RipeRewardsConfig(
        arePointsEnabled=True,
        ripePerBlock=900000000000000,
        borrowersAlloc=1000,
        stakersAlloc=9000,
        votersAlloc=0,
        genDepositorsAlloc=0,
        autoStakeRatio=7500,
        autoStakeDurationRatio=3300,
        stabPoolRipePerDollarClaimed=1000000000000000000,
    )


@view
@external
def ripeGovVaultConfigs() -> DynArray[cs.RipeGovVaultConfigEntry, 5]:
    return [
        cs.RipeGovVaultConfigEntry(
            asset=RIPE_TOKEN,
            config=cs.RipeGovVaultConfig(
                lockTerms=cs.LockTerms(
                    minLockDuration=7200,
                    maxLockDuration=7884000,
                    maxLockBoost=20000,
                    canExit=True,
                    exitFee=8000,
                ),
                assetWeight=10000,
                shouldFreezeWhenBadDebt=True,
            ),
        ),
        cs.RipeGovVaultConfigEntry(
            asset=ASSET_RIPE_WETH_LP,
            config=cs.RipeGovVaultConfig(
                lockTerms=cs.LockTerms(
                    minLockDuration=7200,
                    maxLockDuration=7884000,
                    maxLockBoost=20000,
                    canExit=True,
                    exitFee=8000,
                ),
                assetWeight=15000,
                shouldFreezeWhenBadDebt=True,
            ),
        ),
    ]


@view
@external
def hrConfig() -> cs.HrConfig:
    return cs.HrConfig(
        contribTemplate=CONTRIB_TEMPLATE,
        maxCompensation=0,
        minCliffLength=604800,
        maxStartDelay=7776000,
        minVestingLength=604800,
        maxVestingLength=315360000,
    )


@view
@external
def underscoreRegistry() -> address:
    return empty(address)


@view
@external
def trainingWheels() -> address:
    return TRAINING_WHEELS


@view
@external
def shouldCheckLastTouch() -> bool:
    return True


@view
@external
def assetConfigs() -> DynArray[cs.AssetConfigEntry, 50]:
    return [
        # WETH
        cs.AssetConfigEntry(asset=WETH_TOKEN, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=2500000000000000000,
            globalDepositLimit=5000000000000000000,
            minDepositBalance=500000000000000,
            debtTerms=cs.DebtTerms(
                ltv=7000,
                redemptionThreshold=7700,
                liqThreshold=8000,
                liqFee=1000,
                borrowRate=700,
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
            stakersPointsAlloc=1500,
            voterPointsAlloc=0,
            perUserDepositLimit=100000000000000000000000000,
            globalDepositLimit=1000000000000000000000000000,
            minDepositBalance=100000000000000,
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
        cs.AssetConfigEntry(asset=SGREEN_TOKEN, config=cs.AssetConfig(
            vaultIds=[1],
            stakersPointsAlloc=1500,
            voterPointsAlloc=0,
            perUserDepositLimit=100000000000000000000000000,
            globalDepositLimit=1000000000000000000000000000,
            minDepositBalance=10000000000000000,
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
        cs.AssetConfigEntry(asset=GREEN_TOKEN, config=cs.AssetConfig(
            vaultIds=[],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=1,
            globalDepositLimit=2,
            minDepositBalance=1,
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
        # GREEN/USDG
        cs.AssetConfigEntry(asset=ASSET_GREEN_USDG_POOL, config=cs.AssetConfig(
            vaultIds=[1],
            stakersPointsAlloc=2500,
            voterPointsAlloc=0,
            perUserDepositLimit=100000000000000000000000000,
            globalDepositLimit=1000000000000000000000000000,
            minDepositBalance=10000000000000000,
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
        # SPCX
        cs.AssetConfigEntry(asset=ASSET_SPCX, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=46314045545307603265,
            globalDepositLimit=92628091090615206530,
            minDepositBalance=9262809109061520,
            debtTerms=cs.DebtTerms(
                ltv=7000,
                redemptionThreshold=7700,
                liqThreshold=8000,
                liqFee=1000,
                borrowRate=700,
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
        # NVDA
        cs.AssetConfigEntry(asset=ASSET_NVDA, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=22765715742720093248,
            globalDepositLimit=45531431485440186496,
            minDepositBalance=4553143148544018,
            debtTerms=cs.DebtTerms(
                ltv=7000,
                redemptionThreshold=7700,
                liqThreshold=8000,
                liqFee=1000,
                borrowRate=700,
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
        # TSLA
        cs.AssetConfigEntry(asset=ASSET_TSLA, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=15559843156780979647,
            globalDepositLimit=31119686313561959295,
            minDepositBalance=3111968631356195,
            debtTerms=cs.DebtTerms(
                ltv=7000,
                redemptionThreshold=7700,
                liqThreshold=8000,
                liqFee=1000,
                borrowRate=700,
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
        # AAPL
        cs.AssetConfigEntry(asset=ASSET_AAPL, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=16058176847738133529,
            globalDepositLimit=32116353695476267058,
            minDepositBalance=3211635369547626,
            debtTerms=cs.DebtTerms(
                ltv=7000,
                redemptionThreshold=7700,
                liqThreshold=8000,
                liqFee=1000,
                borrowRate=700,
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
        # GOOGL
        cs.AssetConfigEntry(asset=ASSET_GOOGL, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=13830638848272912804,
            globalDepositLimit=27661277696545825608,
            minDepositBalance=2766127769654582,
            debtTerms=cs.DebtTerms(
                ltv=7000,
                redemptionThreshold=7700,
                liqThreshold=8000,
                liqFee=1000,
                borrowRate=700,
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
        # GME
        cs.AssetConfigEntry(asset=ASSET_GME, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=262126633376584227840,
            globalDepositLimit=524253266753168455680,
            minDepositBalance=52425326675316845,
            debtTerms=cs.DebtTerms(
                ltv=7000,
                redemptionThreshold=7700,
                liqThreshold=8000,
                liqFee=1000,
                borrowRate=700,
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
        # UNI-V2
        cs.AssetConfigEntry(asset=ASSET_RIPE_WETH_LP, config=cs.AssetConfig(
            vaultIds=[2],
            stakersPointsAlloc=4500,
            voterPointsAlloc=0,
            perUserDepositLimit=100000000000000000000000000,
            globalDepositLimit=1000000000000000000000000000,
            minDepositBalance=1000000000000000,
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
    ]


@view
@external
def priorityLiqAssetVaults() -> DynArray[cs.VaultLite, 20]:
    return [
        cs.VaultLite(vaultId=3, asset=WETH_TOKEN),
    ]


@view
@external
def priorityStabVaults() -> DynArray[cs.VaultLite, 20]:
    return [
        cs.VaultLite(vaultId=1, asset=ASSET_GREEN_USDG_POOL),
        cs.VaultLite(vaultId=1, asset=SGREEN_TOKEN),
    ]


@view
@external
def priorityPriceSourceIds() -> DynArray[uint256, 10]:
    return [1, 2]


@view
@external
def liteSigners() -> DynArray[address, 10]:
    return [
        0xeAb5190bdb0cd9a01520e628B0205eD75A77e466,
        0xb7827a593b0BAfCEeFae1f318768b3BFe279EC71,
        0x55f56f74E006496E23aec96b3f72caDee805a1D8,
    ]
