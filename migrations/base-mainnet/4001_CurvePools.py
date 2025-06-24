from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS
import boa


def migrate(migration: Migration):
    blueprint = migration.blueprint()

    log.h1("Deploying Curve Pools")

    usdc = boa.from_etherscan(blueprint.CORE_TOKENS["USDC"])
    green_token = migration.get_contract("GreenToken")

    factory = boa.from_etherscan(blueprint.ADDYS["CURVE_STABLE_FACTORY"])
    green_pool_deploy = migration.execute(
        factory.deploy_plain_pool,
        blueprint.CURVE_PARAMS["GREEN_POOL_NAME"],
        blueprint.CURVE_PARAMS["GREEN_POOL_SYMBOL"],
        [blueprint.CORE_TOKENS["USDC"], green_token],
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
    migration.execute(usdc.approve, green_pool.address, usdc_amount)
    migration.execute(green_token.approve, green_pool.address, green_amount)
    migration.execute(green_pool.add_liquidity, [usdc_amount, green_amount], 0)

    # Add Green Prices
    curve_prices = migration.get_contract("CurvePrices")
    migration.execute(curve_prices.addNewPriceFeed, green_token, green_pool)
    migration.execute(curve_prices.confirmNewPriceFeed, green_token)
    migration.execute(curve_prices.addNewPriceFeed, green_pool, green_pool)
    migration.execute(curve_prices.confirmNewPriceFeed, green_pool)

    migration.execute(curve_prices.setActionTimeLockAfterSetup)

    sb_alpha = migration.get_contract("SwitchboardAlpha")
    actionId = migration.execute(
        sb_alpha.setPriorityStabVaults,
        [
            (1, migration.get_address("SavingsGreen")),
            (1, migration.get_address("GreenPool")),
        ],
    )
    assert bool(migration.execute(sb_alpha.executePendingAction, int(actionId)))
    migration.execute(sb_alpha.setActionTimeLockAfterSetup)
