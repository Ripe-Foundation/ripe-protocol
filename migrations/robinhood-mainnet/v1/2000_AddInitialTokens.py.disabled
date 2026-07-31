from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import EIGHTEEN_DECIMALS, MAX_UINT256
from scripts.utils.deploy_args import DEFAULT_AUCTION_PARAMS


WHITELIST = [
    '0x9c340456e7E3450Ec254B5b82448fB60D3633F0B',
    '0x2f537C2C1D263e66733DA492414359B6B70e1269',
    '0xB13D7d316Ff8B9db9cE8CD93d4D2DfD54b7A5419',
    '0x1567A3715C68c33383b375b07f39F9738a802C49',
]


def migrate(migration: Migration):
    blueprint = migration.blueprint()

    log.h1("Adding Initial Tokens")

    # Assets
    usdc = blueprint.CORE_TOKENS["USDC"]
    cbbtc = blueprint.CORE_TOKENS["CBBTC"]
    weth = blueprint.CORE_TOKENS["WETH"]
    sgreen = migration.get_address("SavingsGreen")

    tw = migration.get_address("TrainingWheels")

    sb_bravo = migration.get_contract("SwitchboardBravo")

    stability_pool_vault_id = 1
    simple_erc20_vault_id = 3

    actionId = migration.execute(
        sb_bravo.addAsset,
        usdc,
        [simple_erc20_vault_id],
        0,  # _stakersPointsAlloc
        0,  # _voterPointsAlloc
        100 * 10**6,  # _perUserDepositLimit
        1_000 * 10**6,  # _globalDepositLimit
        25 * 10**4,  # _minDepositBalance 0.25 USDC
        (
            80_00,  # ltv
            85_00,  # redemptionThreshold
            90_00,  # liqThreshold
            5_00,  # liqFee
            5_00,  # borrowRate
            25,  # daowry 0.25%
        ),  # _debtTerms
        False,  # _shouldBurnAsPayment
        True,  # _shouldTransferToEndaoment
        False,  # _shouldSwapInStabPools
        False,  # _shouldAuctionInstantly
        True,  # _canDeposit
        True,  # _canWithdraw
        False,  # _canRedeemCollateral
        True,  # _canRedeemInStabPool
        True,  # _canBuyInAuction
        True,  # _canClaimInStabPool
        0,  # _specialStabPoolId
        DEFAULT_AUCTION_PARAMS,  # _customAuctionParams
        tw,  # _whitelist
        False,  # _isNft
    )
    assert bool(migration.execute(sb_bravo.executePendingAction, int(actionId)))

    actionId = migration.execute(
        sb_bravo.addAsset,
        cbbtc,
        [simple_erc20_vault_id],
        0,  # _stakersPointsAlloc
        0,  # _voterPointsAlloc
        10 ** 5,  # _perUserDepositLimit 0.001 cbBTC -- 8 Decimals - $100
        10 ** 6,  # _globalDepositLimit 0.01 cbBTC -- 8 Decimals - $1000
        250,  # _minDepositBalance 0.0000025 cbBTC -- 8 Decimals - $0.25
        (
            40_00,  # ltv
            50_00,  # redemptionThreshold
            60_00,  # liqThreshold
            10_00,  # liqFee
            5_00,  # borrowRate
            25,  # daowry 0.25%
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
        DEFAULT_AUCTION_PARAMS,  # _customAuctionParams
        tw,  # _whitelist
        False,  # _isNft
    )

    assert bool(migration.execute(sb_bravo.executePendingAction, int(actionId)))

    actionId = migration.execute(
        sb_bravo.addAsset,
        weth,
        [simple_erc20_vault_id],
        0,  # _stakersPointsAlloc
        0,  # _voterPointsAlloc
        4 * 10**16,  # _perUserDepositLimit 0.04 WETH - $100
        4 * 10**17,  # _globalDepositLimit 0.4 WETH - $1000
        10 ** 14,  # _minDepositBalance 0.0001 WETH - $0.25
        (
            40_00,  # ltv
            50_00,  # redemptionThreshold
            60_00,  # liqThreshold
            10_00,  # liqFee
            5_00,  # borrowRate
            25,  # daowry 0.25%
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
        DEFAULT_AUCTION_PARAMS,  # _customAuctionParams
        tw,  # _whitelist
        False,  # _isNft
    )
    assert bool(migration.execute(sb_bravo.executePendingAction, int(actionId)))

    actionId = migration.execute(
        sb_bravo.addAsset,
        sgreen,
        [stability_pool_vault_id],
        10_00,  # _stakersPointsAlloc
        0,  # _voterPointsAlloc
        MAX_UINT256 - 1,  # _perUserDepositLimit
        MAX_UINT256 - 1,  # _globalDepositLimit
        EIGHTEEN_DECIMALS,  # _minDepositBalance
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
        DEFAULT_AUCTION_PARAMS,  # _customAuctionParams
        tw,  # _whitelist
        False,  # _isNft
    )
    assert bool(migration.execute(sb_bravo.executePendingAction, int(actionId)))
