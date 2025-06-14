from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS
import boa


def migrate(migration: Migration):
    blueprint = migration.blueprint()

    log.h1("Deploying Curve Pools")

    usdc = boa.from_etherscan(blueprint.ADDYS["USDC"])
    green_token = migration.get_contract("GreenToken")

    factory = boa.from_etherscan(blueprint.ADDYS["CURVE_STABLE_FACTORY"])
    green_pool_deploy = factory.deploy_plain_pool(
        blueprint.CURVE_PARAMS["GREEN_POOL_NAME"],
        blueprint.CURVE_PARAMS["GREEN_POOL_SYMBOL"],
        [blueprint.ADDYS["USDC"], green_token],
        blueprint.CURVE_PARAMS["GREEN_POOL_A"],
        blueprint.CURVE_PARAMS["GREEN_POOL_FEE"],
        blueprint.CURVE_PARAMS["GREEN_POOL_OFFPEG_MULTIPLIER"],
        blueprint.CURVE_PARAMS["GREEN_POOL_MA_EXP_TIME"],
        0,
        [0, 0],
        [b"", b""],
        [ZERO_ADDRESS, ZERO_ADDRESS],

    )
    migration.include_contract("GreenPool", green_pool_deploy)

    log.h2(f"Green Pool deployed at {green_pool_deploy}")

    log.h2(f"Adding liquidity to Green Pool")
    (boa.from_etherscan(factory.pool_implementations(0), "green pool").deployer).at(green_pool_deploy)
    green_pool = boa.env.lookup_contract(green_pool_deploy)

    usdc_amount = 100 * 10**6
    green_amount = 100 * 10**18
    usdc.approve(green_pool.address, usdc_amount, sender=migration.account().address)
    green_token.approve(green_pool.address, green_amount, sender=migration.account().address)
    green_pool.add_liquidity([usdc_amount, green_amount], 0, sender=migration.account().address)

    log.h2(f"Deploying Ripe Pool")

    weth = boa.from_etherscan(blueprint.ADDYS["WETH"])
    ripe_token = migration.get_contract("RipeToken")

    factory = boa.from_etherscan(blueprint.ADDYS["CURVE_CRYPTO_FACTORY"])
    ripe_pool_deploy = factory.deploy_pool(
        blueprint.CURVE_PARAMS["RIPE_POOL_NAME"],
        blueprint.CURVE_PARAMS["RIPE_POOL_SYMBOL"],
        [weth, ripe_token],
        0,
        blueprint.CURVE_PARAMS["RIPE_POOL_A"],
        blueprint.CURVE_PARAMS["RIPE_POOL_GAMMA"],
        blueprint.CURVE_PARAMS["RIPE_POOL_MID_FEE"],
        blueprint.CURVE_PARAMS["RIPE_POOL_OUT_FEE"],
        blueprint.CURVE_PARAMS["RIPE_POOL_FEE_GAMMA"],
        blueprint.CURVE_PARAMS["RIPE_POOL_EXTRA_PROFIT"],
        blueprint.CURVE_PARAMS["RIPE_POOL_ADJ_STEP"],
        blueprint.CURVE_PARAMS["RIPE_POOL_MA_EXP_TIME"],
        blueprint.CURVE_PARAMS["RIPE_POOL_INIT_PRICE"],
    )
    migration.include_contract("RipePool", ripe_pool_deploy)

    log.h2(f"Ripe Pool deployed at {ripe_pool_deploy}")

    log.h2(f"Adding liquidity to Ripe Pool")
    (boa.from_etherscan(factory.pool_implementations(0), "ripe pool").deployer).at(ripe_pool_deploy)
    ripe_pool = boa.env.lookup_contract(ripe_pool_deploy)

    weth_amount = 1 * 10**15
    ripe_amount = 1_000 * 10**18
    weth.approve(ripe_pool.address, weth_amount, sender=migration.account().address)
    ripe_token.approve(ripe_pool.address, ripe_amount, sender=migration.account().address)
    ripe_pool.add_liquidity([weth_amount, ripe_amount], 0, sender=migration.account().address)
