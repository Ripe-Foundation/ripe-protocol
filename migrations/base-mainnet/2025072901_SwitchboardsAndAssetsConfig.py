from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Switchboard Alpha")
    switchboard_alpha = migration.deploy(
        "SwitchboardAlpha",
        hq,
        migration.account(),
        blueprint.PARAMS["PRICE_DESK_MIN_STALE_TIME"],
        blueprint.PARAMS["PRICE_DESK_MAX_STALE_TIME"],
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"]
    )

    log.h1("Deploying Switchboard Bravo")
    switchboard_bravo = migration.deploy(
        "SwitchboardBravo",
        hq,
        migration.account(),
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"]
    )

    # Setting assets config
    migration.execute(
        switchboard_bravo.setAssetDepositParams,
        blueprint.CORE_TOKENS["WETH"],
        [3],  # vault ids
        0,  # stakers points alloc
        0,  # voter points alloc
        8 * 10 ** 16,  # per user deposit limit
        8 * 10 ** 17,  # global deposit limit
        8 * 10 ** 13,  # min deposit balance
    )

    migration.execute(
        switchboard_bravo.setAssetDepositParams,
        blueprint.CORE_TOKENS["CBBTC"],
        [3],  # vault ids
        0,  # stakers points alloc
        0,  # voter points alloc
        25 * 10**4,  # per user deposit limit
        25 * 10**5,  # global deposit limit
        25,  # min deposit balance
    )

    migration.execute(
        switchboard_bravo.setAssetDepositParams,
        blueprint.CORE_TOKENS["USOL"],
        [3],  # vault ids
        0,  # stakers points alloc
        0,  # voter points alloc
        15 * 10**17,  # per user deposit limit
        15 * 10**18,  # global deposit limit
        15 * 10**14,  # min deposit balance
    )

    migration.execute(
        switchboard_bravo.setAssetDepositParams,
        blueprint.CORE_TOKENS["CBDOGE"],
        [3],  # vault ids
        0,  # stakers points alloc
        0,  # voter points alloc
        1500 * 10**8,  # per user deposit limit
        15000 * 10**8,  # global deposit limit
        15 * 10**7,  # min deposit balance
    )

    migration.execute(
        switchboard_bravo.setAssetDebtTerms,
        blueprint.CORE_TOKENS["WETH"],
        70_00,  # ltv,
        77_00,  # redemptionThreshold,
        80_00,  # liqThreshold,
        10_00,  # liqFee,
        7_00,  # borrowRate,
        25,  # daowry,
    )

    migration.execute(
        switchboard_bravo.setAssetDebtTerms,
        blueprint.CORE_TOKENS["CBBTC"],
        70_00,  # ltv,
        77_00,  # redemptionThreshold,
        80_00,  # liqThreshold,
        10_00,  # liqFee,
        7_00,  # borrowRate,
        25,  # daowry,
    )

    migration.execute(
        switchboard_bravo.setAssetDebtTerms,
        blueprint.CORE_TOKENS["USOL"],
        50_00,  # ltv,
        60_00,  # redemptionThreshold,
        65_00,  # liqThreshold,
        12_00,  # liqFee,
        11_00,  # borrowRate,
        25,  # daowry,
    )

    migration.execute(
        switchboard_bravo.setAssetDebtTerms,
        blueprint.CORE_TOKENS["CBDOGE"],
        50_00,  # ltv,
        60_00,  # redemptionThreshold,
        65_00,  # liqThreshold,
        12_00,  # liqFee,
        11_00,  # borrowRate,
        25,  # daowry,
    )

    migration.execute(
        switchboard_bravo.addAsset,
        blueprint.YIELD_TOKENS["MORPHO_SPARK_USDC"],
        [3],  # vaultIds
        0,  # stakersPointsAlloc
        0,  # voterPointsAlloc
        300 * 10**18,  # perUserDepositLimit
        3000 * 10**18,  # globalDepositLimit
        3 * 10**17,  # minDepositBalance
        (
            80_00,  # ltv
            82_00,  # redemptionThreshold
            85_00,  # liqThreshold
            5_00,  # liqFee
            5_00,  # borrowRate
            25,  # daowry 0.25%
        ),  # _debtTerms
        False,  # shouldBurnAsPayment
        True,  # shouldTransferToEndaoment
        False,  # shouldSwapInStabPools
        False,  # shouldAuctionInstantly
        False,  # canDeposit
        False,  # canWithdraw
        False,  # canRedeemCollateral
        True,  # canRedeemInStabPool
        True,  # canBuyInAuction
        True,  # canClaimInStabPool
    )

    log.h1("Deploying Switchboard Delta")
    switchboard_delta = migration.deploy(
        "SwitchboardDelta",
        hq,
        migration.account(),
        blueprint.PARAMS["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        blueprint.PARAMS["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
    )

    # Set time locks after setup
    migration.execute(switchboard_alpha.setActionTimeLockAfterSetup)
    migration.execute(switchboard_bravo.setActionTimeLockAfterSetup)
    migration.execute(switchboard_delta.setActionTimeLockAfterSetup)

    # Relinquish gov
    migration.execute(switchboard_alpha.relinquishGov)
    migration.execute(switchboard_bravo.relinquishGov)
    migration.execute(switchboard_delta.relinquishGov)
