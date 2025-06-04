from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Finishing Ripe Hq Setup")

    # finish ripe hq setup
    migration.execute(hq.setRegistryTimeLockAfterSetup)

    log.h1("Setting Mission Control Config")

    switchboard_one = migration.get_contract("SwitchboardOne")

    # Set general config
    actionId = migration.execute(switchboard_one.setVaultLimits, 5, 10)
    assert migration.execute(switchboard_one.executePendingAction, actionId)

    assert migration.execute(switchboard_one.setCanDeposit, True)
    assert migration.execute(switchboard_one.setCanWithdraw, True)
    assert migration.execute(switchboard_one.setCanBorrow, True)
    assert migration.execute(switchboard_one.setCanRepay, True)
    assert migration.execute(switchboard_one.setCanClaimLoot, True)
    assert migration.execute(switchboard_one.setCanLiquidate, True)
    assert migration.execute(switchboard_one.setCanRedeemCollateral, True)
    assert migration.execute(switchboard_one.setCanRedeemInStabPool, True)
    assert migration.execute(switchboard_one.setCanBuyInAuction, True)
    assert migration.execute(switchboard_one.setCanClaimInStabPool, True)

    # Set general debt config
    actionId = migration.execute(
        switchboard_one.setGlobalDebtLimits,
        10_000 * EIGHTEEN_DECIMALS,
        1_000_000 * EIGHTEEN_DECIMALS,
        100 * EIGHTEEN_DECIMALS,
        100,
    )
    assert migration.execute(switchboard_one.executePendingAction, actionId)

    actionId = migration.execute(
        switchboard_one.setBorrowIntervalConfig,
        1_000 * EIGHTEEN_DECIMALS,
        100,
    )
    assert migration.execute(switchboard_one.executePendingAction, actionId)

    actionId = migration.execute(
        switchboard_one.setKeeperConfig,
        100,
        100,
    )
    assert migration.execute(switchboard_one.executePendingAction, actionId)

    assert migration.execute(switchboard_one.setIsDaowryEnabled, True)

    actionId = migration.execute(switchboard_one.setLtvPaybackBuffer, 100)
    assert migration.execute(switchboard_one.executePendingAction, actionId)

    actionId = migration.execute(switchboard_one.setGenAuctionParams, 10_00, 50_00, 10, 1_000)
    assert migration.execute(switchboard_one.executePendingAction, actionId)

    switchboard_two = migration.get_contract("SwitchboardTwo")

    vault_book = migration.get_contract("VaultBook")
    simple_erc20 = migration.get_contract("SimpleErc20")
    simple_erc20_vault_id = migration.execute(vault_book.addrToRegId, simple_erc20)
    stability_pool = migration.get_contract("StabilityPool")
    stability_pool_vault_id = migration.execute(vault_book.addrToRegId, stability_pool)

    actionId = migration.execute(
        switchboard_two.addAsset,
        blueprint.ADDYS["USDC"],
        [simple_erc20_vault_id],
        100,  # _stakersPointsAlloc
        100,  # _voterPointsAlloc
        100_000 * EIGHTEEN_DECIMALS,  # _perUserDepositLimit
        10_000_000 * EIGHTEEN_DECIMALS,  # _globalDepositLimit
        (
            85_00,  # ltv
            90_00,  # redemptionThreshold
            95_00,  # liqThreshold
            5_00,  # liqFee
            3_00,  # borrowRate
            1,  # daowry
        ),  # _debtTerms
        False,  # _shouldBurnAsPayment
        True,  # _shouldTransferToEndaoment
        False,  # _shouldSwapInStabPools
        True,  # _shouldAuctionInstantly
        True,  # _canDeposit
        True,  # _canWithdraw
        False,  # _canRedeemCollateral
    )
    assert migration.execute(switchboard_two.executePendingAction, actionId)

    actionId = migration.execute(
        switchboard_two.addAsset,
        blueprint.ADDYS["CBBTC"],
        [simple_erc20_vault_id],
        100,  # _stakersPointsAlloc
        100,  # _voterPointsAlloc
        100 * EIGHTEEN_DECIMALS,  # _perUserDepositLimit
        10_000 * EIGHTEEN_DECIMALS,  # _globalDepositLimit
        (
            50_00,  # ltv
            60_00,  # redemptionThreshold
            70_00,  # liqThreshold
            10_00,  # liqFee
            5_00,  # borrowRate
            1,  # daowry
        ),  # _debtTerms
    )
    assert migration.execute(switchboard_two.executePendingAction, actionId)

    actionId = migration.execute(
        switchboard_two.addAsset,
        blueprint.ADDYS["WETH"],
        [simple_erc20_vault_id],
        100,  # _stakersPointsAlloc
        100,  # _voterPointsAlloc
        1_000 * EIGHTEEN_DECIMALS,  # _perUserDepositLimit
        100_000 * EIGHTEEN_DECIMALS,  # _globalDepositLimit
        (
            50_00,  # ltv
            60_00,  # redemptionThreshold
            70_00,  # liqThreshold
            10_00,  # liqFee
            5_00,  # borrowRate
            1,  # daowry
        ),  # _debtTerms
    )
    assert migration.execute(switchboard_two.executePendingAction, actionId)

    actionId = migration.execute(
        switchboard_two.addAsset,
        migration.get_address("SavingsGreen"),
        [stability_pool_vault_id],
        10_00,  # _stakersPointsAlloc
        10_00,  # _voterPointsAlloc
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
    )
    assert migration.execute(switchboard_two.executePendingAction, actionId)

    migration.execute(hq.finishRipeHqSetup, migration.blueprint().ADDYS["GOVERNANCE"])
