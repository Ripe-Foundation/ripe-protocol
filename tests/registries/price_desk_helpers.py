"""Shared PriceDesk fixtures; sources retain caller-specified order."""
import boa

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def _isolated_price_desk(ripe_hq, deploy3r, sources, price_gas=250_000, snapshot_gas=150_000):
    desk = boa.load(
        "contracts/registries/PriceDesk.vy",
        ripe_hq,
        deploy3r,
        ETH,
        1,
        2,
        price_gas,
        snapshot_gas,
        75_000,
        6_000_000,
        name="isolated_price_desk",
    )
    for index, source in enumerate(sources, start=1):
        assert desk.startAddNewAddressToRegistry(
            source,
            f"source {index}",
            sender=deploy3r,
        )
        assert desk.confirmNewAddressToRegistry(source, sender=deploy3r) == index
    return desk


def _raw_source(
    price=0,
    has_feed=False,
    price_mode=0,
    has_feed_mode=0,
    snapshot_mode=0,
):
    source = boa.load(
        "contracts/mock/MockRawPriceSource.vy",
        name="raw_price_source",
    )
    source.configure(
        price,
        has_feed,
        price_mode,
        has_feed_mode,
        snapshot_mode,
    )
    return source


def _gas_source(
    price=0,
    has_feed=False,
    price_iterations=0,
    has_feed_iterations=0,
    snapshot_iterations=0,
    exhaust_price=False,
    exhaust_has_feed=False,
    exhaust_snapshot=False,
):
    source = boa.load(
        "contracts/mock/MockGasBurningPriceSource.vy",
        name="gas_burning_price_source",
    )
    source.configure(
        price,
        has_feed,
        price_iterations,
        has_feed_iterations,
        snapshot_iterations,
        exhaust_price,
        exhaust_has_feed,
        exhaust_snapshot,
    )
    return source


def _set_priorities(mission_control, switchboard_alpha, source_ids):
    mission_control.setPriorityPriceSourceIds(
        source_ids,
        sender=switchboard_alpha.address,
    )
