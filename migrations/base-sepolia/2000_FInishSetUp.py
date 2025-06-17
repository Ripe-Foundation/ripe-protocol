from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import EIGHTEEN_DECIMALS, MAX_UINT256


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Finishing Ripe Hq Setup")

    # finish ripe hq setup
    migration.execute(hq.setRegistryTimeLockAfterSetup)

    log.h1("Setting Mission Control Config")

    sb_alpha = migration.get_contract("SwitchboardAlpha")

    # Set general config
    actionId = migration.execute(sb_alpha.setVaultLimits, 5, 10)
    assert migration.execute(sb_alpha.executePendingAction, actionId)

    assert migration.execute(sb_alpha.setCanDeposit, True)
    assert migration.execute(sb_alpha.setCanWithdraw, True)
    assert migration.execute(sb_alpha.setCanBorrow, True)
    assert migration.execute(sb_alpha.setCanRepay, True)
    assert migration.execute(sb_alpha.setCanClaimLoot, True)
    assert migration.execute(sb_alpha.setCanLiquidate, True)
    assert migration.execute(sb_alpha.setCanRedeemCollateral, True)
    assert migration.execute(sb_alpha.setCanRedeemInStabPool, True)
    assert migration.execute(sb_alpha.setCanBuyInAuction, True)
    assert migration.execute(sb_alpha.setCanClaimInStabPool, True)

    # Set general debt config
    actionId = migration.execute(
        sb_alpha.setGlobalDebtLimits,
        1_000_000 * EIGHTEEN_DECIMALS,
        100_000_000 * EIGHTEEN_DECIMALS,
        100 * EIGHTEEN_DECIMALS,
        100,
    )
    assert migration.execute(sb_alpha.executePendingAction, actionId)

    actionId = migration.execute(
        sb_alpha.setBorrowIntervalConfig,
        100_000 * EIGHTEEN_DECIMALS,
        100,
    )
    assert migration.execute(sb_alpha.executePendingAction, actionId)

    actionId = migration.execute(
        sb_alpha.setKeeperConfig,
        100,
        100,
    )
    assert migration.execute(sb_alpha.executePendingAction, actionId)

    assert migration.execute(sb_alpha.setIsDaowryEnabled, True)

    actionId = migration.execute(sb_alpha.setLtvPaybackBuffer, 100)
    assert migration.execute(sb_alpha.executePendingAction, actionId)

    actionId = migration.execute(sb_alpha.setGenAuctionParams, 10_00, 50_00, 10, 1_000)
    assert migration.execute(sb_alpha.executePendingAction, actionId)

    sb_bravo = migration.get_contract("SwitchboardBravo")

    vault_book = migration.get_contract("VaultBook")
    simple_erc20 = migration.get_contract("SimpleErc20")
    simple_erc20_vault_id = vault_book.addrToRegId(simple_erc20)
    stability_pool = migration.get_contract("StabilityPool")
    stability_pool_vault_id = vault_book.addrToRegId(stability_pool)
    ripe_gov_vault = migration.get_contract("RipeGov")
    ripe_gov_vault_id = vault_book.addrToRegId(ripe_gov_vault)

    actionId = migration.execute(
        sb_bravo.addAsset,
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
    assert migration.execute(sb_bravo.executePendingAction, actionId)

    actionId = migration.execute(
        sb_bravo.addAsset,
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
    assert migration.execute(sb_bravo.executePendingAction, actionId)

    actionId = migration.execute(
        sb_bravo.addAsset,
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
    assert migration.execute(sb_bravo.executePendingAction, actionId)

    actionId = migration.execute(
        sb_bravo.addAsset,
        migration.get_address("SavingsGreen"),
        [stability_pool_vault_id],
        10_00,  # _stakersPointsAlloc
        10_00,  # _voterPointsAlloc
        MAX_UINT256 - 1,  # _perUserDepositLimit
        MAX_UINT256 - 1,  # _globalDepositLimit
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
    assert migration.execute(sb_bravo.executePendingAction, actionId)

    actionId = migration.execute(
        sb_bravo.addAsset,
        migration.get_address("RipeToken"),
        [ripe_gov_vault_id],
        10_00,  # _stakersPointsAlloc
        10_00,  # _voterPointsAlloc
        MAX_UINT256 - 1,  # _perUserDepositLimit
        MAX_UINT256 - 1,  # _globalDepositLimit
        (
            0,  # ltv
            0,  # redemptionThreshold
            0,  # liqThreshold
            0,  # liqFee
            0,  # borrowRate
            0,  # daowry
        ),  # _debtTerms
        False,  # _shouldBurnAsPayment
        False,  # _shouldTransferToEndaoment
        False,  # _shouldSwapInStabPools
        False,  # _shouldAuctionInstantly
        True,  # _canDeposit
        True,  # _canWithdraw
        False,  # _canRedeemInStabPool
        False,  # _canRedeemCollateral
        False,  # _canBuyInAuction
        False,  # _canClaimInStabPool
    )
    assert migration.execute(sb_bravo.executePendingAction, actionId)

    actionId = migration.execute(
        sb_bravo.addAsset,
        migration.get_address("GreenPool"),
        [stability_pool_vault_id],
        10_00,  # _stakersPointsAlloc
        10_00,  # _voterPointsAlloc
        MAX_UINT256 - 1,  # _perUserDepositLimit
        MAX_UINT256 - 1,  # _globalDepositLimit
        (
            0,  # ltv
            0,  # redemptionThreshold
            0,  # liqThreshold
            0,  # liqFee
            0,  # borrowRate
            0,  # daowry
        ),  # _debtTerms
        False,  # _shouldBurnAsPayment
        True,  # _shouldTransferToEndaoment
        False,  # _shouldSwapInStabPools
        False,  # _shouldAuctionInstantly
        True,  # _canDeposit
        True,  # _canWithdraw
        False,  # _canRedeemCollateral
    )
    assert migration.execute(sb_bravo.executePendingAction, actionId)

    actionId = migration.execute(
        sb_bravo.addAsset,
        migration.get_address("RipePool"),
        [ripe_gov_vault_id],
        10_00,  # _stakersPointsAlloc
        10_00,  # _voterPointsAlloc
        MAX_UINT256 - 1,  # _perUserDepositLimit
        MAX_UINT256 - 1,  # _globalDepositLimit
        (
            0,  # ltv
            0,  # redemptionThreshold
            0,  # liqThreshold
            0,  # liqFee
            0,  # borrowRate
            0,  # daowry
        ),  # _debtTerms
        False,  # _shouldBurnAsPayment
        False,  # _shouldTransferToEndaoment
        False,  # _shouldSwapInStabPools
        False,  # _shouldAuctionInstantly
        True,  # _canDeposit
        True,  # _canWithdraw
        False,  # _canRedeemCollateral
        False,  # _canRedeemInStabPool
        False,  # _canBuyInAuction
        False,  # _canClaimInStabPool
    )
    assert migration.execute(sb_bravo.executePendingAction, actionId)

    actionId = migration.execute(
        sb_alpha.setPriorityStabVaults,
        [
            (stability_pool_vault_id, migration.get_address("SavingsGreen")),
            (stability_pool_vault_id, migration.get_address("GreenPool")),
        ],
    )
    assert migration.execute(sb_alpha.executePendingAction, actionId)

    # migration.execute(hq.finishRipeHqSetup, migration.blueprint().ADDYS["GOVERNANCE"])
