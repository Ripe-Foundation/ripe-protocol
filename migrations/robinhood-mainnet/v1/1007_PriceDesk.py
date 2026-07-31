from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS

# BlueChipYieldPrices.Protocol is a Vyper flag, so members are bit positions:
# MORPHO=1, EULER=2, MOONWELL=4, SKY=8, FLUID=16, AAVE_V3=32, COMPOUND_V3=64,
# MORPHO_V2=128.
PROTOCOL_MORPHO_V2 = 128


# Minimum configuration price sources:
#   PriceDesk id 1 -- Chainlink       (ETH/BTC defaults + USDG feed)
#   PriceDesk id 2 -- BlueChipYield   (prices the SteakHouse USDG Morpho vault)
#
# Curve, Pyth and Stork are omitted; none has a confirmed Robinhood deployment.
# PriceDesk ids 3-5 stay empty and reserved to their canonical semantics.
#
# NOTE: DefaultsRobinHood ships priorityPriceSourceIds = [1, 2, 3]. Id 3 is not
# registered here, which is harmless rather than broken -- _getPriceFromPriceSource
# returns (0, False) for an unregistered id and the lookup falls through to the
# remaining sources. Trimming it to [1, 2] only saves a wasted iteration.
def migrate(migration: Migration):
    blueprint = migration.blueprint()
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying Price Desk")

    price_desk = migration.deploy(
        "PriceDesk",
        hq,
        ZERO_ADDRESS,
        blueprint.ADDYS["ETH"],
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
    )

    log.h1("Deploying Chainlink Prices")

    chainlink = migration.deploy(
        "ChainlinkPrices",
        hq,
        ZERO_ADDRESS,
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
        blueprint.ADDYS["WETH"],
        blueprint.ADDYS["ETH"],
        blueprint.ADDYS["BTC"],
        blueprint.ADDYS["CHAINLINK_ETH_USD"],
        blueprint.ADDYS["CHAINLINK_BTC_USD"],
        blueprint.PARAMS["CHAINLINK_DEFAULT_STALE_TIME"],
    )

    # USDG is the reserve stable behind the launch collateral
    usdg = blueprint.CORE_TOKENS["USDG"]
    migration.execute(
        chainlink.addNewPriceFeed,
        usdg,
        blueprint.ADDYS["CHAINLINK_USDG_USD"],
        blueprint.PARAMS["CHAINLINK_DEFAULT_STALE_TIME"],
    )
    assert bool(migration.execute(chainlink.confirmNewPriceFeed, usdg))

    migration.execute(price_desk.startAddNewAddressToRegistry, chainlink, "Chainlink")
    assert int(migration.execute(price_desk.confirmNewAddressToRegistry, chainlink)) == 1

    # Register PriceDesk in RipeHq BEFORE any BlueChip work.
    #
    # This registration was missing entirely, which shifted every later RipeHq id
    # by one and made 1008's `== 8` assertion unreachable. It also has to happen
    # here rather than at the end of this migration: BlueChipYieldPrices resolves
    # PriceDesk through RipeHq id 7 and its feed validation calls
    # PriceDesk.getPrice on the underlying asset, so registering a BlueChip feed
    # first would static-call a zero address.
    migration.execute(hq.startAddNewAddressToRegistry, price_desk, "Price Desk")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, price_desk)) == 7

    log.h1("Deploying BlueChip Yield Prices")

    # Morpho Vaults V2 is the only yield protocol confirmed on Robinhood, and it
    # is NOT MetaMorpho: the launch collateral is a `VaultV2` from
    # `VaultV2Factory`, so membership is isVaultV2 rather than isMetaMorpho.
    # Every other registry -- including the two MetaMorpho slots -- is zero,
    # which fails closed: registering an asset of any of those protocols reverts
    # on the static call instead of pricing against a foreign-chain address.
    morpho_v2_factory = blueprint.ADDYS["MORPHO_V2_FACTORY"]
    assert morpho_v2_factory != ZERO_ADDRESS  # dev: morpho v2 factory unresolved

    bluechip_yield_prices = migration.deploy(
        "BlueChipYieldPrices",
        hq,
        ZERO_ADDRESS,
        blueprint.PARAMS["PRICE_DESK_MIN_REG_TIMELOCK"],
        blueprint.PARAMS["PRICE_DESK_MAX_REG_TIMELOCK"],
        [blueprint.ADDYS["MORPHO_FACTORY"], blueprint.ADDYS["MORPHO_FACTORY_LEGACY"]],
        [blueprint.ADDYS["EULER_EVAULT_FACTORY"], blueprint.ADDYS["EULER_EARN_FACTORY"]],
        blueprint.ADDYS["FLUID_RESOLVER"],
        blueprint.ADDYS["COMPOUND_V3_CONFIGURATOR"],
        blueprint.ADDYS["MOONWELL_COMPTROLLER"],
        blueprint.ADDYS["AAVE_V3_ADDRESS_PROVIDER"],
        morpho_v2_factory,
    )
    migration.execute(price_desk.startAddNewAddressToRegistry, bluechip_yield_prices, "BlueChip Yield Prices")
    assert int(migration.execute(price_desk.confirmNewAddressToRegistry, bluechip_yield_prices)) == 2

    # Price the launch collateral: SteakHouse USDG, a Morpho Vault V2.
    #
    # Feed validation requires PriceDesk.getPrice(USDG) to be non-zero, which is
    # why the Chainlink USDG feed and the PriceDesk HQ registration both come
    # first.
    steakhouse_usdg = blueprint.YIELD_TOKENS["MORPHO_STEAKHOUSE_USDG"]
    migration.execute(bluechip_yield_prices.addNewPriceFeed, steakhouse_usdg, PROTOCOL_MORPHO_V2)
    assert bool(migration.execute(bluechip_yield_prices.confirmNewPriceFeed, steakhouse_usdg))
