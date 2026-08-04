from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS
import boa

from config.robinhood_launch import (
    POOL_MIN_MINTED_LP,
    POOL_SEED_GREEN,
    POOL_SEED_USDG,
    address,
)

# StableSwap-NG factory, read from the Curve AddressProvider at launch rather
# than hard-coded: id 12 is the factory, and CurvePrices already proved ids
# 7/11/12/13 resolve on this chain when it was constructed.
STABLESWAP_NG_FACTORY_ID = 12

ADDRESS_PROVIDER_ABI = (
    '[{"type":"function","name":"get_address","stateMutability":"view",'
    '"inputs":[{"name":"_id","type":"uint256"}],'
    '"outputs":[{"name":"","type":"address"}]}]'
)


def migrate(migration: Migration):
    blueprint = migration.blueprint()
    deployer = migration.account()

    green_token = migration.get_contract("GreenToken")
    curve_prices = migration.get_contract("CurvePrices")
    endaoment_funds = migration.get_contract("EndaomentFunds")
    usdg = boa.loads_abi(
        '[{"type":"function","name":"approve","stateMutability":"nonpayable",'
        '"inputs":[{"name":"s","type":"address"},{"name":"a","type":"uint256"}],'
        '"outputs":[{"name":"","type":"bool"}]},'
        '{"type":"function","name":"balanceOf","stateMutability":"view",'
        '"inputs":[{"name":"o","type":"address"}],'
        '"outputs":[{"name":"","type":"uint256"}]}]'
    ).at(address("USDG"))

    log.h1("Deploying GREEN/USDG Curve pool")

    provider = boa.loads_abi(ADDRESS_PROVIDER_ABI).at(
        address("CURVE_ADDRESS_PROVIDER")
    )
    factory_address = provider.get_address(STABLESWAP_NG_FACTORY_ID)
    assert factory_address != ZERO_ADDRESS, "StableSwap-NG factory not registered"

    factory = boa.loads_abi(
        '[{"type":"function","name":"deploy_plain_pool","stateMutability":"nonpayable",'
        '"inputs":['
        '{"name":"_name","type":"string"},{"name":"_symbol","type":"string"},'
        '{"name":"_coins","type":"address[]"},{"name":"_A","type":"uint256"},'
        '{"name":"_fee","type":"uint256"},'
        '{"name":"_offpeg_fee_multiplier","type":"uint256"},'
        '{"name":"_ma_exp_time","type":"uint256"},'
        '{"name":"_implementation_idx","type":"uint256"},'
        '{"name":"_asset_types","type":"uint8[]"},'
        '{"name":"_method_ids","type":"bytes4[]"},'
        '{"name":"_oracles","type":"address[]"}],'
        '"outputs":[{"name":"","type":"address"}]}]'
    ).at(factory_address)

    # Coin order is (USDG, GREEN) and must stay that way: CurvePrices reads
    # index 0 as the stable side when it prices GREEN.
    pool_address = migration.execute(
        factory.deploy_plain_pool,
        blueprint.CURVE_PARAMS["GREEN_POOL_NAME"],
        blueprint.CURVE_PARAMS["GREEN_POOL_SYMBOL"],
        [address("USDG"), green_token],
        blueprint.CURVE_PARAMS["GREEN_POOL_A"],
        blueprint.CURVE_PARAMS["GREEN_POOL_FEE"],
        blueprint.CURVE_PARAMS["GREEN_POOL_OFFPEG_MULTIPLIER"],
        blueprint.CURVE_PARAMS["GREEN_POOL_MA_EXP_TIME"],
        0,
        [0, 0],
        [b"", b""],
        [ZERO_ADDRESS, ZERO_ADDRESS],
    )
    migration.include_contract("GreenUsdgPool", pool_address)
    log.h2(f"GREEN/USDG pool deployed at {pool_address}")

    pool = boa.loads_abi(
        '[{"type":"function","name":"add_liquidity","stateMutability":"nonpayable",'
        '"inputs":[{"name":"_amounts","type":"uint256[]"},'
        '{"name":"_min_mint_amount","type":"uint256"}],'
        '"outputs":[{"name":"","type":"uint256"}]},'
        '{"type":"function","name":"balanceOf","stateMutability":"view",'
        '"inputs":[{"name":"o","type":"address"}],'
        '"outputs":[{"name":"","type":"uint256"}]},'
        '{"type":"function","name":"transfer","stateMutability":"nonpayable",'
        '"inputs":[{"name":"t","type":"address"},{"name":"v","type":"uint256"}],'
        '"outputs":[{"name":"","type":"bool"}]}]'
    ).at(pool_address)

    log.h1("Seeding GREEN/USDG pool")

    assert int(usdg.balanceOf(deployer)) >= POOL_SEED_USDG, "deployer holds no USDG"

    migration.execute(usdg.approve, pool_address, POOL_SEED_USDG)
    migration.execute(green_token.approve, pool_address, POOL_SEED_GREEN)
    # Seeding an empty pool mints LP equal to the invariant D, ~200e18 at a 1:1
    # peg. Base passed 0 here; the floor aborts if the pool is not what we think.
    minted = migration.execute(
        pool.add_liquidity,
        [POOL_SEED_USDG, POOL_SEED_GREEN],
        POOL_MIN_MINTED_LP,
    )
    log.h2(f"minted {int(minted) / 10**18:.6f} LP")

    # The whole LP balance goes to EndaomentFunds; the deployer retains none.
    migration.execute(
        pool.transfer, endaoment_funds, pool.balanceOf(deployer)
    )
    assert int(pool.balanceOf(deployer)) == 0, "deployer still holds LP"

    log.h1("Adding GREEN price feed")

    # CurvePrices is PriceDesk id 2 and USDG already prices through Chainlink,
    # so GREEN resolves through this pool composed with the USDG feed.
    migration.execute(curve_prices.addNewPriceFeed, green_token, pool_address)
    migration.execute(curve_prices.confirmNewPriceFeed, green_token)
