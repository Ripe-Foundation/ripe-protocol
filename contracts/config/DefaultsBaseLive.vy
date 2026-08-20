# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026

# @version 0.4.3

# GENERATED FILE -- do not edit by hand.
#
# Regenerate with:  python scripts/prepare_defaults.py --network base-mainnet --block-number 49896151
#
# Snapshot provenance:
#   repository: ripe-foundation/ripe-protocol
#   generator: scripts/prepare_defaults.py
#   generator sha256: 2fcce89099dcc4879002a4b7980b3d663185cff274cffb0793d61f7df5457b7f
#   manifest sha256: 90dc26ec5c854e5c7f46429c4020a997864bbfeeff2ba7f766a541839e791e09
#   Vyper compiler: 0.4.3+commit.bff19ea2
#   Vyper compiler identity sha256: 208c7c41102f13ea781980bf0647dd003d334d34fb02b48f043459c8584aafe0
#   MissionControl compiler-input integrity: 89384a3df18447d313fe3db1e007509adebb3e1a54fed7848cb727f3defb65ff
#   MissionControl canonical ABI sha256: 9778661b26a575626b7319a95f81281d39be6d4d081250f27be26f32de138903
#   Ledger compiler-input integrity: 78cb171dc351031f2addcf08eea17fc10c4e6b2763d92d32208fdc48f0806ef3
#   Ledger canonical ABI sha256: 2b055432f1f2e850866ace602e2a03354e7887815c7cab435cb14b9521dc3e3c
#   chain id: 8453
#   snapshot block: 49896151
#   snapshot block hash: 0x5c2723f65014f29460c81f889e418724772d4247335413a7844c30290889a3be
#   snapshot finality: verified against the provider finalized tag
#   MissionControl: 0x559E53F42b68b4995732Dba4aF300796761DBC19
#   MissionControl code sha256: 32432e24dd701d80430d70b59408d156d9a1a6b9d537224354b9f97dc22db008
#   Ledger: 0x365256e322a47Aa2015F6724783F326e9B24fA47
#   Ledger code sha256: a8cacd456cc038a74eba236eacbbe50cbde8af4d0f9cc4cb22f98653a67b0b5d
#
# This is the defaults contract for REPLACING a MissionControl or Ledger that
# already exists. DefaultsBase.vy remains the launch config for a
# brand-new chain; the two are not interchangeable.
#
# Every value below was read off the live Base deployment, so this is a
# snapshot of what governance has configured rather than a set of launch
# decisions. MissionControl and Ledger copy these into storage at
# construction, which is the only reason a replacement for either can come up
# matching what is already running.
#
# MissionControl state that Defaults has no slot for -- userConfig and
# userDelegation -- does NOT survive the redeploy and is not represented here.
#
# Percentages are basis points (100_00 == 100%). Durations are in
# `block.number`, which on this OP-stack L2 advances every 2s, so a day is
# 43_200 blocks.

implements: Defaults
from interfaces import Defaults
import interfaces.ConfigStructs as cs

# addresses -- all read from the live deployment, so there is no
# constructor and nothing to bind at deploy time
UNDY_USD: constant(address) = 0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf
USDC: constant(address) = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
SUSDE: constant(address) = 0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2
UNDY_EURC: constant(address) = 0x1cb8DAB80f19fC5Aca06C2552AECd79015008eA8
WETH: constant(address) = 0x4200000000000000000000000000000000000006
UNDY_ETH: constant(address) = 0x02981DB1a99A14912b204437e7a2E02679B57668
CB_ETH: constant(address) = 0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22
CB_BTC: constant(address) = 0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf
WSUPER_OETHB: constant(address) = 0x7FcD174E80f264448ebeE8c88a7C4476AAF58Ea6
UNDY_BTC: constant(address) = 0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493
VIRTUAL: constant(address) = 0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b
AERO: constant(address) = 0x940181a94A35A4569E4529A3CDfB74e38FD98631
USOL: constant(address) = 0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55
CB_DOGE: constant(address) = 0xcbD06E5A2B0C65597161de254AA074E489dEb510
UNDY_AERO: constant(address) = 0x96F1a7ce331F40afe866F3b707c223e377661087
CB_ADA: constant(address) = 0xcbADA732173e39521CDBE8bf59a6Dc85A9fc7b8c
CB_XRP: constant(address) = 0xcb585250f852C6c6bf90434AB21A00f02833a4af
CB_LTC: constant(address) = 0xcb17C9Db87B595717C857a08468793f5bAb6445F
VVV: constant(address) = 0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf
DEGEN: constant(address) = 0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed
WELL: constant(address) = 0xA88594D404727625A9437C3f886C7643872296AE
RIPE_TOKEN: constant(address) = 0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0
GREEN_USDC_LP: constant(address) = 0xd6c283655B42FA0eb2685F7AB819784F071459dc
SGREEN_TOKEN: constant(address) = 0xaa0f13488CE069A7B5a099457c753A7CFBE04d36
RIPE_WETH_LP: constant(address) = 0x765824aD2eD0ECB70ECc25B0Cf285832b335d6A9
GREEN_TOKEN: constant(address) = 0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707
UNDY_USDC: constant(address) = 0x99e65176F7FA8743E3fbaEF277d1Da448e361367
TRAINING_WHEELS: constant(address) = 0x2255b0006A3DA38AA184E0F9d5e056C2d0448065
CONTRIB_TEMPLATE: constant(address) = 0x4965578D80E54b5EbE3BB5D7b1B3E0425559C1D1


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
        perUserDebtLimit=1000000000000000000000,
        globalDebtLimit=40000000000000000000000,
        minDebtAmount=1000000000000000000,
        numAllowedBorrowers=1000,
        maxBorrowPerInterval=10000000000000000000000,
        numBlocksPerInterval=43200,
        minDynamicRateBoost=10000,
        maxDynamicRateBoost=50000,
        increasePerDangerBlock=10,
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
            duration=43200,
        ),
    )


@view
@external
def ripeAvailForRewards() -> uint256:
    return 879095205175239069433051


@view
@external
def ripeAvailForHr() -> uint256:
    return 800000000000000000000


@view
@external
def ripeAvailForBonds() -> uint256:
    return 288556649469530000000000


@view
@external
def ripeBondConfig() -> cs.RipeBondConfig:
    return cs.RipeBondConfig(
        asset=USDC,
        amountPerEpoch=2000000000,
        canBond=False,
        minRipePerUnit=0,
        maxRipePerUnit=1000000000000000000,
        maxRipePerUnitLockBonus=20000,
        epochLength=14400,
        shouldAutoRestart=True,
        restartDelayBlocks=0,
    )


@view
@external
def rewardsConfig() -> cs.RipeRewardsConfig:
    return cs.RipeRewardsConfig(
        arePointsEnabled=True,
        ripePerBlock=7500000000000000,
        borrowersAlloc=1000,
        stakersAlloc=9000,
        votersAlloc=0,
        genDepositorsAlloc=0,
        autoStakeRatio=7500,
        autoStakeDurationRatio=3300,
        stabPoolRipePerDollarClaimed=10000000000000000,
    )


@view
@external
def ripeGovVaultConfigs() -> DynArray[cs.RipeGovVaultConfigEntry, 5]:
    return [
        cs.RipeGovVaultConfigEntry(
            asset=RIPE_TOKEN,
            config=cs.RipeGovVaultConfig(
                lockTerms=cs.LockTerms(
                    minLockDuration=43200,
                    maxLockDuration=47304000,
                    maxLockBoost=20000,
                    canExit=True,
                    exitFee=8000,
                ),
                assetWeight=10000,
                shouldFreezeWhenBadDebt=True,
            ),
        ),
        cs.RipeGovVaultConfigEntry(
            asset=RIPE_WETH_LP,
            config=cs.RipeGovVaultConfig(
                lockTerms=cs.LockTerms(
                    minLockDuration=43200,
                    maxLockDuration=47304000,
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
    return 0x44Cf3c4f000DFD76a35d03298049D37bE688D6F9


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
        # UNDY_USD
        cs.AssetConfigEntry(asset=UNDY_USD, config=cs.AssetConfig(
            vaultIds=[],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=1,
            globalDepositLimit=1,
            minDepositBalance=0,
            debtTerms=cs.DebtTerms(
                ltv=8000,
                redemptionThreshold=8500,
                liqThreshold=9000,
                liqFee=500,
                borrowRate=500,
                daowry=25,
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
        # USDC
        cs.AssetConfigEntry(asset=USDC, config=cs.AssetConfig(
            vaultIds=[],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=1,
            globalDepositLimit=1,
            minDepositBalance=0,
            debtTerms=cs.DebtTerms(
                ltv=8000,
                redemptionThreshold=8500,
                liqThreshold=9000,
                liqFee=500,
                borrowRate=500,
                daowry=25,
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
        # SUSDE
        cs.AssetConfigEntry(asset=SUSDE, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=4138925278549878192670,
            globalDepositLimit=20694626392749390963353,
            minDepositBalance=82778505570997563,
            debtTerms=cs.DebtTerms(
                ltv=8000,
                redemptionThreshold=8500,
                liqThreshold=9000,
                liqFee=500,
                borrowRate=500,
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
        # UNDY_EURC
        cs.AssetConfigEntry(asset=UNDY_EURC, config=cs.AssetConfig(
            vaultIds=[5],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=4290904101,
            globalDepositLimit=21454520508,
            minDepositBalance=85818,
            debtTerms=cs.DebtTerms(
                ltv=8000,
                redemptionThreshold=8500,
                liqThreshold=9000,
                liqFee=500,
                borrowRate=500,
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
        cs.AssetConfigEntry(asset=WETH, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=1646052728169408091,
            globalDepositLimit=8230263640847040458,
            minDepositBalance=32921054563388,
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
        # UNDY_ETH
        cs.AssetConfigEntry(asset=UNDY_ETH, config=cs.AssetConfig(
            vaultIds=[5],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=16447676038471417830,
            globalDepositLimit=82238380192357089170,
            minDepositBalance=32895352076942,
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
        # CB_ETH
        cs.AssetConfigEntry(asset=CB_ETH, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=1478101461711344160,
            globalDepositLimit=7390507308556720802,
            minDepositBalance=29562029234226,
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
        # CB_BTC
        cs.AssetConfigEntry(asset=CB_BTC, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=5554381,
            globalDepositLimit=27771905,
            minDepositBalance=111,
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
        # WSUPER_OETHB
        cs.AssetConfigEntry(asset=WSUPER_OETHB, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=1518552436330112774,
            globalDepositLimit=7592762181650563870,
            minDepositBalance=30371048726602,
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
            canDeposit=False,
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
        # UNDY_BTC
        cs.AssetConfigEntry(asset=UNDY_BTC, config=cs.AssetConfig(
            vaultIds=[5],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=55541110,
            globalDepositLimit=277705550,
            minDepositBalance=111,
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
        # VIRTUAL
        cs.AssetConfigEntry(asset=VIRTUAL, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=6041731690803988944597,
            globalDepositLimit=30208658454019944722988,
            minDepositBalance=120834633816079778,
            debtTerms=cs.DebtTerms(
                ltv=5000,
                redemptionThreshold=6000,
                liqThreshold=6500,
                liqFee=1200,
                borrowRate=1100,
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
        cs.AssetConfigEntry(asset=AERO, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=7671774247547778735965,
            globalDepositLimit=38358871237738893679826,
            minDepositBalance=153435484950955574,
            debtTerms=cs.DebtTerms(
                ltv=5000,
                redemptionThreshold=6000,
                liqThreshold=6500,
                liqFee=1000,
                borrowRate=800,
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
        # USOL
        cs.AssetConfigEntry(asset=USOL, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=38021075364647256084,
            globalDepositLimit=190105376823236280420,
            minDepositBalance=760421507292945,
            debtTerms=cs.DebtTerms(
                ltv=5000,
                redemptionThreshold=6000,
                liqThreshold=6500,
                liqFee=1200,
                borrowRate=1100,
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
        # CB_DOGE
        cs.AssetConfigEntry(asset=CB_DOGE, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=3623605908216,
            globalDepositLimit=18118029541084,
            minDepositBalance=72472118,
            debtTerms=cs.DebtTerms(
                ltv=5000,
                redemptionThreshold=6000,
                liqThreshold=6500,
                liqFee=1200,
                borrowRate=1100,
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
        # UNDY_AERO
        cs.AssetConfigEntry(asset=UNDY_AERO, config=cs.AssetConfig(
            vaultIds=[5],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=7663356320898015168529,
            globalDepositLimit=38316781604490075842648,
            minDepositBalance=153267126417960303,
            debtTerms=cs.DebtTerms(
                ltv=5000,
                redemptionThreshold=6000,
                liqThreshold=6500,
                liqFee=1200,
                borrowRate=800,
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
        # CB_ADA
        cs.AssetConfigEntry(asset=CB_ADA, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=12008521246,
            globalDepositLimit=60042606233,
            minDepositBalance=240170,
            debtTerms=cs.DebtTerms(
                ltv=5000,
                redemptionThreshold=6000,
                liqThreshold=6500,
                liqFee=1200,
                borrowRate=1100,
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
        # CB_XRP
        cs.AssetConfigEntry(asset=CB_XRP, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=2458282938,
            globalDepositLimit=12291414692,
            minDepositBalance=49165,
            debtTerms=cs.DebtTerms(
                ltv=5000,
                redemptionThreshold=6000,
                liqThreshold=6500,
                liqFee=1200,
                borrowRate=1100,
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
        # CB_LTC
        cs.AssetConfigEntry(asset=CB_LTC, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=6169282648,
            globalDepositLimit=30846413240,
            minDepositBalance=123385,
            debtTerms=cs.DebtTerms(
                ltv=5000,
                redemptionThreshold=6000,
                liqThreshold=6500,
                liqFee=1200,
                borrowRate=1100,
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
        cs.AssetConfigEntry(asset=VVV, config=cs.AssetConfig(
            vaultIds=[],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=1,
            globalDepositLimit=1,
            minDepositBalance=0,
            debtTerms=cs.DebtTerms(
                ltv=4000,
                redemptionThreshold=4500,
                liqThreshold=5000,
                liqFee=1500,
                borrowRate=1300,
                daowry=25,
            ),
            shouldBurnAsPayment=False,
            shouldTransferToEndaoment=False,
            shouldSwapInStabPools=False,
            shouldAuctionInstantly=False,
            canDeposit=False,
            canWithdraw=False,
            canRedeemCollateral=True,
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
        # DEGEN
        cs.AssetConfigEntry(asset=DEGEN, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=3358702734655766556725130,
            globalDepositLimit=16793513673278832783625652,
            minDepositBalance=67174054693115331134,
            debtTerms=cs.DebtTerms(
                ltv=4000,
                redemptionThreshold=4500,
                liqThreshold=5000,
                liqFee=1500,
                borrowRate=1300,
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
        cs.AssetConfigEntry(asset=WELL, config=cs.AssetConfig(
            vaultIds=[3],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=509796764421895567113214,
            globalDepositLimit=2548983822109477835566073,
            minDepositBalance=10195935288437911342,
            debtTerms=cs.DebtTerms(
                ltv=4000,
                redemptionThreshold=4500,
                liqThreshold=5000,
                liqFee=1500,
                borrowRate=1300,
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
        # RipeToken
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
        # GreenPool
        cs.AssetConfigEntry(asset=GREEN_USDC_LP, config=cs.AssetConfig(
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
        # SavingsGreen
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
        # RipePoolAero
        cs.AssetConfigEntry(asset=RIPE_WETH_LP, config=cs.AssetConfig(
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
        # GreenToken
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
        # UNDY_USDC
        cs.AssetConfigEntry(asset=UNDY_USDC, config=cs.AssetConfig(
            vaultIds=[5],
            stakersPointsAlloc=0,
            voterPointsAlloc=0,
            perUserDepositLimit=50000000000,
            globalDepositLimit=250000000000,
            minDepositBalance=100000,
            debtTerms=cs.DebtTerms(
                ltv=8000,
                redemptionThreshold=8500,
                liqThreshold=9000,
                liqFee=500,
                borrowRate=500,
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
    ]


@view
@external
def priorityLiqAssetVaults() -> DynArray[cs.VaultLite, 20]:
    return [
        cs.VaultLite(vaultId=5, asset=UNDY_USDC),
        cs.VaultLite(vaultId=5, asset=UNDY_EURC),
        cs.VaultLite(vaultId=5, asset=UNDY_BTC),
        cs.VaultLite(vaultId=5, asset=UNDY_ETH),
        cs.VaultLite(vaultId=5, asset=UNDY_AERO),
        cs.VaultLite(vaultId=3, asset=WETH),
        cs.VaultLite(vaultId=3, asset=CB_ETH),
        cs.VaultLite(vaultId=3, asset=CB_BTC),
        cs.VaultLite(vaultId=3, asset=AERO),
        cs.VaultLite(vaultId=3, asset=CB_ADA),
        cs.VaultLite(vaultId=3, asset=CB_XRP),
        cs.VaultLite(vaultId=3, asset=CB_LTC),
        cs.VaultLite(vaultId=3, asset=USOL),
    ]


@view
@external
def priorityStabVaults() -> DynArray[cs.VaultLite, 20]:
    return [
        cs.VaultLite(vaultId=1, asset=GREEN_USDC_LP),
        cs.VaultLite(vaultId=1, asset=SGREEN_TOKEN),
    ]


@view
@external
def priorityPriceSourceIds() -> DynArray[uint256, 10]:
    return [1, 8, 2, 4, 5]


@view
@external
def liteSigners() -> DynArray[address, 10]:
    return [
        0x1c419AeF78b44F30D8F3Dfa2aB13D3538466dc48,
        0x6f5ef229d7F07183Bf91dF68702D01E9bDa37cA2,
        0x84edC07f0Cead3275059373F8FA47A566Dd429df,
    ]
