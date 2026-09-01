from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS

from config.robinhood_launch import (
    PRICE_CHANGE_MAX_TIMELOCK,
    PRICE_CHANGE_MIN_TIMELOCK,
    PRICE_MAX_TIMELOCK,
    PRICE_MIN_TIMELOCK,
    REGISTRY_MAX_DELAY,
    REGISTRY_MIN_DELAY,
    STALE_WINDOW_DEFAULT,
    STALE_WINDOW_USDG,
    address,
)


def _as_address(value) -> str:
    return str(getattr(value, "address", value)).lower()


def _asset_is_nft(config) -> bool:
    if hasattr(config, "isNft"):
        return bool(config.isNft)
    if isinstance(config, (tuple, list)):
        return bool(config[-1])
    return bool(config["isNft"])


def sync_existing_token_scales(execute, price_desk, mission_control, eth_sentinel):
    """Populate PriceDesk scales from MissionControl's live asset list."""
    eth = _as_address(eth_sentinel)
    num_assets = int(mission_control.numAssets())
    for index in range(1, num_assets):
        asset = mission_control.assets(index)
        asset_addr = _as_address(asset)
        if asset_addr in (_as_address(ZERO_ADDRESS), eth):
            continue
        if _asset_is_nft(mission_control.assetConfig(asset)):
            continue
        if int(price_desk.tokenScale(asset)) != 0:
            continue
        execute(price_desk.syncTokenScale, asset)
        assert int(price_desk.tokenScale(asset)) != 0, (
            f"token scale unset after sync for asset {asset_addr}"
        )


def sync_usdg_token_scale(execute, price_desk, usdg):
    if int(price_desk.tokenScale(usdg)) != 0:
        return
    execute(price_desk.syncTokenScale, usdg)
    assert int(price_desk.tokenScale(usdg)) != 0


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    green_token = migration.get_contract("GreenToken")
    savings_green = migration.get_contract("SavingsGreen")

    log.h1("Deploying PriceDesk")

    price_desk = migration.deploy(
        "PriceDesk",
        hq,
        ZERO_ADDRESS,
        address("NATIVE_ETH_SENTINEL"),
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
    )

    log.h1("Deploying ChainlinkPrices")

    chainlink = migration.deploy(
        "ChainlinkPrices",
        hq,
        ZERO_ADDRESS,
        PRICE_MIN_TIMELOCK,
        PRICE_MAX_TIMELOCK,
        address("WETH"),
        address("NATIVE_ETH_SENTINEL"),
        address("BTC_SENTINEL"),
        address("CHAINLINK_ETH_USD"),
        address("CHAINLINK_BTC_USD"),
        STALE_WINDOW_DEFAULT,
    )

    # USDG prices through Chainlink only. Every other price route depends on
    # this being live, including the GREEN pool route and the SteakHouse vault.
    usdg = address("USDG")
    migration.execute(
        chainlink.addNewPriceFeed,
        usdg,
        address("CHAINLINK_USDG_USD"),
        STALE_WINDOW_USDG,
        False,
        False,
    )
    migration.execute(chainlink.confirmNewPriceFeed, usdg)

    # Robinhood's assigned launch PriceDesk ids are Chainlink 1 and Curve 2.
    # Curve consumers receive this chain-local id as a constructor argument.
    migration.execute(price_desk.startAddNewAddressToRegistry, chainlink, "ChainlinkPrices")
    assert int(migration.execute(price_desk.confirmNewAddressToRegistry, chainlink)) == 1

    log.h1("Deploying CurvePrices")
    curve_prices = migration.deploy(
        "CurvePrices",
        hq,
        ZERO_ADDRESS,
        address("CURVE_ADDRESS_PROVIDER"),
        green_token,
        savings_green,
        PRICE_CHANGE_MIN_TIMELOCK,
        PRICE_CHANGE_MAX_TIMELOCK,
    )
    migration.execute(price_desk.startAddNewAddressToRegistry, curve_prices, "CurvePrices")
    assert int(migration.execute(price_desk.confirmNewAddressToRegistry, curve_prices)) == 2

    # MissionControl already loaded DefaultsRobinhood assets. Populate and
    # verify token scales from that live list before PriceDesk promotion.
    log.h1("Synchronizing PriceDesk token scales")
    sync_existing_token_scales(
        migration.execute,
        price_desk,
        migration.get_contract("MissionControl"),
        address("NATIVE_ETH_SENTINEL"),
    )
    sync_usdg_token_scale(
        migration.execute,
        price_desk,
        usdg,
    )

    # PriceDesk must be registered in RipeHq before any feed is added: the price
    # sources resolve PriceDesk through RipeHq when validating a new feed.
    migration.execute(hq.startAddNewAddressToRegistry, price_desk, "PriceDesk")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, price_desk)) == 7

    # BlueChipYield is owner-deferred and unassigned (ID 0). This launch stage
    # deliberately emits no deployment, registration, or activation action.
