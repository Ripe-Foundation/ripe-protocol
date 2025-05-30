from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


CUSTOM_AUCTION_PARAMS = (
    False,  # hasParams
    0,  # startDiscount
    0,  # maxDiscount
    0,  # delay
    0,  # duration
)


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Finishing Ripe Hq Setup")

    # finish ripe hq setup
    migration.execute(hq.setRegistryTimeLockAfterSetup)

    log.h1("Setting Mission Control Config")

    mission_control = migration.get_contract("MissionControl")
    migration.execute(
        mission_control.setGeneralConfig,
        5,  # _perUserMaxVaults
        10,  # _perUserMaxAssetsPerVault
        0,  # _priceStaleTime
        True,  # _canDeposit
        True,  # _canWithdraw
        True,  # _canBorrow
        True,  # _canRepay
        True,  # _canClaimLoot
        True,  # _canLiquidate
        True,  # _canRedeemCollateral
        True,  # _canRedeemInStabPool
        True,  # _canBuyInAuction
        True,  # _canClaimInStabPool
    )

    migration.execute(
        mission_control.setGeneralDebtConfig,
        10_000 * EIGHTEEN_DECIMALS,  # _perUserDebtLimit
        1_000_000 * EIGHTEEN_DECIMALS,  # _globalDebtLimit
        100 * EIGHTEEN_DECIMALS,  # _minDebtAmount
        100,  # _numAllowedBorrowers
        1_000 * EIGHTEEN_DECIMALS,  # _maxBorrowPerInterval
        100,  # _numBlocksPerInterval
        100,  # _keeperFeeRatio
        100,  # _minKeeperFee
        True,  # _isDaowryEnabled
        100,  # _ltvPaybackBuffer
        (
            True,  # _hasParams
            10_00,  # _startDiscount
            50_00,  # _maxDiscount
            10,  # _delay
            1_000,  # _duration
        ),  # _genAuctionParams
    )

    migration.execute(
        mission_control.setAssetConfig,
        migration.blueprint().ADDYS["USDC"],
        100,  # _stakersPointsAlloc
        100,  # _voterPointsAlloc
        100_000 * EIGHTEEN_DECIMALS,  # _perUserDepositLimit
        1_000_000 * EIGHTEEN_DECIMALS,  # _globalDepositLimit
        (
            90_00,  # ltv
            80_00,  # redemptionThreshold
            70_00,  # liqThreshold
            10_00,  # liqFee
            3_00,  # borrowRate
            1,  # daowry
        ),  # _debtTerms
        False,  # _shouldBurnAsPayment
        True,  # _shouldTransferToEndaoment
        True,  # _shouldSwapInStabPools
        True,  # _shouldAuctionInstantly
        True,  # _canDeposit
        True,  # _canWithdraw
        True,  # _canRedeemCollateral
        True,  # _canRedeemInStabPool
        True,  # _canBuyInAuction
        True,  # _canClaimInStabPool
        0,  # _specialStabPoolId
        CUSTOM_AUCTION_PARAMS,  # _customAuctionParams
        ZERO_ADDRESS,  # _whitelist
        False,  # _isNft
    )

    migration.execute(
        mission_control.setAssetConfig,
        migration.blueprint().ADDYS["CBBTC"],
        100,  # _stakersPointsAlloc
        100,  # _voterPointsAlloc
        100 * EIGHTEEN_DECIMALS,  # _perUserDepositLimit
        10_000 * EIGHTEEN_DECIMALS,  # _globalDepositLimit
        (
            50_00,  # ltv
            40_00,  # redemptionThreshold
            30_00,  # liqThreshold
            10_00,  # liqFee
            5_00,  # borrowRate
            1,  # daowry
        ),  # _debtTerms
        False,  # _shouldBurnAsPayment
        False,  # _shouldTransferToEndaoment
        True,  # _shouldSwapInStabPools
        True,  # _shouldAuctionInstantly
        True,  # _canDeposit
        True,  # _canWithdraw
        True,  # _canRedeemCollateral
        True,  # _canRedeemInStabPool
        True,  # _canBuyInAuction
        True,  # _canClaimInStabPool
        0,  # _specialStabPoolId
        CUSTOM_AUCTION_PARAMS,  # _customAuctionParams
        ZERO_ADDRESS,  # _whitelist
        False,  # _isNft
    )

    migration.execute(
        mission_control.setAssetConfig,
        migration.blueprint().ADDYS["WETH"],
        100,  # _stakersPointsAlloc
        100,  # _voterPointsAlloc
        1_000 * EIGHTEEN_DECIMALS,  # _perUserDepositLimit
        100_000 * EIGHTEEN_DECIMALS,  # _globalDepositLimit
        (
            50_00,  # ltv
            40_00,  # redemptionThreshold
            30_00,  # liqThreshold
            10_00,  # liqFee
            5_00,  # borrowRate
            1,  # daowry
        ),  # _debtTerms
        False,  # _shouldBurnAsPayment
        False,  # _shouldTransferToEndaoment
        True,  # _shouldSwapInStabPools
        True,  # _shouldAuctionInstantly
        True,  # _canDeposit
        True,  # _canWithdraw
        True,  # _canRedeemCollateral
        True,  # _canRedeemInStabPool
        True,  # _canBuyInAuction
        True,  # _canClaimInStabPool
        0,  # _specialStabPoolId
        CUSTOM_AUCTION_PARAMS,  # _customAuctionParams
        ZERO_ADDRESS,  # _whitelist
        False,  # _isNft
    )

    migration.execute(
        mission_control.setAssetConfig,
        migration.get_address("SavingsGreen"),
        1_000,  # _stakersPointsAlloc
        1_000,  # _voterPointsAlloc
        1_000_000 * EIGHTEEN_DECIMALS,  # _perUserDepositLimit
        100_000_000 * EIGHTEEN_DECIMALS,  # _globalDepositLimit
        (
            0,  # ltv
            0,  # redemptionThreshold
            0,  # liqThreshold
            0,  # liqFee
            0,  # borrowRate
            0,  # daowry
        ),  # _debtTerms
        True,  # _shouldBurnAsPayment
        False,  # _shouldTransferToEndaoment
        False,  # _shouldSwapInStabPools
        False,  # _shouldAuctionInstantly
        True,  # _canDeposit
        True,  # _canWithdraw
        False,  # _canRedeemCollateral
        False,  # _canRedeemInStabPool
        False,  # _canBuyInAuction
        False,  # _canClaimInStabPool
        0,  # _specialStabPoolId
        CUSTOM_AUCTION_PARAMS,  # _customAuctionParams
        ZERO_ADDRESS,  # _whitelist
        False,  # _isNft
    )

    # When we have a governance address, we can uncomment this
    migration.execute(hq.finishRipeHqSetup, migration.blueprint().ADDYS["GOVERNANCE"])
