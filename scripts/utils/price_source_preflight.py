"""Live, fail-closed Robinhood PriceDesk admission observations."""

from config.price_source_admission import (
    LiveCurveRoute,
    LivePriceSourceTopology,
    PriceSourceAdmissionError,
    require_hardened_price_desk_runtime,
    require_selected_live_topology,
)
from config.robinhood_launch import address


PRICE_DESK_HQ_ID = 7


def require_active_hardened_price_desk(migration, hq, price_desk) -> None:
    """Bind both the HQ reference and runtime to the governed PriceDesk."""
    if str(hq.getAddr(PRICE_DESK_HQ_ID)).lower() != str(price_desk.address).lower():
        raise PriceSourceAdmissionError(
            "RipeHq does not reference the selected active PriceDesk"
        )
    require_hardened_price_desk_runtime(migration.get_deployed_code(price_desk.address))


def observe_live_topology(migration, price_desk, candidate=None):
    """Enumerate the complete live Curve graph and its source resolutions."""
    mission_control = migration.get_contract("MissionControl")
    next_registry_id = int(price_desk.numAddrs())
    all_slots = tuple(
        price_desk.getAddr(source_id) for source_id in range(1, next_registry_id)
    )
    zero = "0x" + "0" * 40
    slots = tuple((*all_slots, zero, zero, zero)[:3])
    chainlink = migration.get_contract("ChainlinkPrices", address=slots[0])
    curve = migration.get_contract("CurvePrices", address=slots[1])
    usdg = address("USDG")
    savings_green = curve.SGREEN()

    source_contracts = []
    for source_id, source_address in enumerate(all_slots, start=1):
        if int(str(source_address), 16) == 0:
            continue
        source_contracts.append(
            (
                source_id,
                migration.get_contract("ChainlinkPrices", address=source_address),
            )
        )
    if candidate is not None:
        source_contracts.append((3, candidate))

    priced_assets = tuple(curve.getPricedAssets())
    routes = []
    for feed_asset in priced_assets:
        curve_config = curve.curveConfig(feed_asset)
        underlyings = tuple(curve_config.underlying)
        resolutions = []
        for underlying in underlyings[: int(curve_config.numUnderlying)]:
            if str(underlying).lower() == str(feed_asset).lower():
                continue
            source_ids = tuple(
                source_id
                for source_id, source in source_contracts
                if bool(source.hasPriceFeed(underlying))
            )
            resolutions.append((underlying, source_ids))
        routes.append(
            LiveCurveRoute(
                feed_asset=feed_asset,
                pool=curve_config.pool,
                num_underlying=int(curve_config.numUnderlying),
                underlyings=underlyings,
                underlying_price_source_ids=tuple(resolutions),
            )
        )

    chainlink_config = chainlink.feedConfig(usdg)
    gen_config = mission_control.genConfig()
    return LivePriceSourceTopology(
        next_registry_id=next_registry_id,
        registry_addresses=slots,
        priority_source_ids=tuple(
            int(source_id) for source_id in mission_control.getPriorityPriceSourceIds()
        ),
        curve_priced_assets=priced_assets,
        curve_routes=tuple(routes),
        curve_green_address=curve.GREEN(),
        savings_green_address=savings_green,
        savings_green_has_feed=bool(curve.hasPriceFeed(savings_green)),
        chainlink_usdg_feed=chainlink_config.feed,
        max_vaults_per_user=int(gen_config.perUserMaxVaults),
        max_assets_per_vault=int(gen_config.perUserMaxAssetsPerVault),
    )


def require_live_topology(migration, price_desk, candidate=None):
    """Compare the complete observed graph with the governed manifest."""
    observed = observe_live_topology(migration, price_desk, candidate)
    require_selected_live_topology(
        observed=observed,
        selected_chainlink_address=migration.get_address("ChainlinkPrices"),
        selected_curve_address=migration.get_address("CurvePrices"),
        selected_green_address=migration.get_address("GreenToken"),
        selected_savings_green_address=migration.get_address("SavingsGreen"),
        selected_usdg_address=address("USDG"),
        selected_curve_pool_address=migration.get_address("GreenUsdgPool"),
        selected_usdg_chainlink_feed=address("CHAINLINK_USDG_USD"),
    )
    return observed
