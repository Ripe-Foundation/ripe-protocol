"""Shared PriceDesk construction; sources retain caller-specified order."""
import boa

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


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
