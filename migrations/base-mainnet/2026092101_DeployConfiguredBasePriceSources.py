"""Deploy/configure oracle candidates only; retain live HQ and all live sources."""

from scripts.utils import log
from scripts.utils.migration import Migration

ZERO = "0x" + "00" * 20
HQ = "0x6162df1b329e157479f8f1407e888260e0ec3d2b"
SUFFIX = "BasePrices20260921"
SOURCE_NAMES = (
    "ChainlinkPrices", "CurvePrices", "BlueChipYieldPrices", "PythPrices",
    "StorkPrices", "AeroRipePrices", "wsuperOETHbPrices", "UndyVaultPrices", "RedStone",
)


def address(value):
    return str(getattr(value, "address", value)).lower()


def migrate(migration: Migration):
    if migration.chain() != "base-mainnet":
        raise RuntimeError("BASE_PRICES_WRONG_PROFILE")
    hq = migration.get_contract("RipeHq")
    if address(hq) != HQ:
        raise RuntimeError("BASE_PRICES_WRONG_HQ")
    active_desk = hq.getAddr(7)
    desk = migration.get_contract("PriceDesk", active_desk)
    mc = migration.get_contract("MissionControl", hq.getAddr(5))
    params = migration.blueprint().PARAMS
    assert params["PRICE_DESK_PRICE_SOURCE_GAS"] == 3_000_000
    assert params["PRICE_DESK_SNAPSHOT_SOURCE_GAS"] == 3_000_000
    assert desk.numAddrs() == 10 and address(desk.getAddr(3)) == ZERO
    rows = [desk.getAddr(i) for i in range(1, 10)]

    log.h1("1. Read current feed configuration, source identities and timelocks")
    old = {}
    assets = {}
    locks = {}
    for i, name in enumerate(SOURCE_NAMES, 1):
        if i in (3, 6):  # disabled BlueChip and retained legacy Aero
            continue
        source = migration.get_contract(name, rows[i-1])
        old[name] = source
        assets[name] = list(source.getPricedAssets())
        locks[name] = (source.minActionTimeLock(), source.maxActionTimeLock(), source.actionTimeLock())
    for name in ("PythPrices", "StorkPrices", "RedStone"):
        if assets[name]:
            raise RuntimeError(f"BASE_PRICES_UNUSED_SOURCE_NOW_HAS_FEEDS:{name}")
    cl = old["ChainlinkPrices"]
    eth, btc = cl.ETH(), cl.BTC()
    chainlink_configs = [(a, tuple(cl.feedConfig(a))) for a in assets["ChainlinkPrices"]]
    # Feed anchors must precede conversion-dependent entries.
    chainlink_configs.sort(key=lambda item: 0 if address(item[0]) in (address(eth), address(btc)) else 1)
    initial_chainlink = [(a, c[0], c[4], c[2], c[3]) for a, c in chainlink_configs]
    curve = old["CurvePrices"]
    curve_configs = [(a, tuple(curve.curveConfig(a))) for a in assets["CurvePrices"]]
    initial_curve = [(a, c[0]) for a, c in curve_configs]
    green_ref = tuple(curve.greenRefPoolConfig())
    undy_configs = [(a, tuple(old["UndyVaultPrices"].priceConfigs(a))[:7]) for a in assets["UndyVaultPrices"]]
    for a, c in undy_configs:
        if desk.getPrice(c[0], False) == 0:
            raise RuntimeError(f"BASE_PRICES_UNDY_UNDERLYING_UNPRICEABLE:{a}:{c[0]}")

    log.h1("2. Deploy PriceDesk and constructor-configured Chainlink/Curve sources")
    new = {}
    new_desk = migration.deploy(
        "PriceDesk", hq.address, migration.account(), eth,
        desk.minRegistryTimeLock(), desk.maxRegistryTimeLock(),
        3_000_000, 3_000_000, label=f"PriceDesk{SUFFIX}",
    )
    new["ChainlinkPrices"] = migration.deploy(
        "ChainlinkPrices", hq.address, migration.account(), *locks["ChainlinkPrices"][:2],
        cl.WETH(), eth, btc, ZERO, ZERO, 0, initial_chainlink,
        label=f"ChainlinkPrices{SUFFIX}",
    )
    new["CurvePrices"] = migration.deploy(
        "CurvePrices", hq.address, migration.account(),
        migration.blueprint().ADDYS["CURVE_ADDRESS_PROVIDER"],
        hq.getAddr(1), hq.getAddr(2), *locks["CurvePrices"][:2],
        initial_curve, green_ref, label=f"CurvePrices{SUFFIX}",
    )

    log.h1("3. Deploy updated Undy source; retain current wrapped-OETH and Aero")
    new["UndyVaultPrices"] = migration.deploy(
        "UndyVaultPrices", hq.address, migration.account(), *locks["UndyVaultPrices"][:2],
        label=f"UndyVaultPrices{SUFFIX}",
    )

    log.h1("4. Configure remaining feeds and seed fresh Undy snapshots")
    # No historical snapshots are imported. Undy config confirmations seed
    # convertToAssets observations; policy/metadata must match live exactly.
    for a, c in undy_configs:
        migration.execute(new["UndyVaultPrices"].addNewPriceFeed, a, *c[3:7])
        migration.execute(new["UndyVaultPrices"].confirmNewPriceFeed, a)
        assert tuple(new["UndyVaultPrices"].priceConfigs(a))[:7] == c
    for a, c in chainlink_configs:
        assert tuple(new["ChainlinkPrices"].feedConfig(a)) == c
    for a, c in curve_configs:
        assert tuple(new["CurvePrices"].curveConfig(a)) == c
    assert tuple(new["CurvePrices"].greenRefPoolConfig()) == green_ref
    for name in ("ChainlinkPrices", "CurvePrices", "UndyVaultPrices"):
        assert {address(a) for a in new[name].getPricedAssets()} == {address(a) for a in assets[name]}

    log.h1("5. Populate PriceDesk, preserving source IDs")
    for i, name in enumerate(SOURCE_NAMES, 1):
        # Reserve unused IDs with the historical source, then disable the row.
        # Never renumber MC priority routes or deploy unused replacements.
        if i == 3:
            target = migration.get_contract("BlueChipYieldPrices").address
        elif i in (4, 5, 6, 7, 9):
            target = rows[i-1]
        else:
            target = new[name].address
        migration.execute(new_desk.startAddNewAddressToRegistry, target, name)
        migration.execute(new_desk.confirmNewAddressToRegistry, target)
        assert address(new_desk.getAddr(i)) == address(target)
        if i in (3, 4, 5, 9):
            migration.execute(new_desk.startAddressDisableInRegistry, i)
            migration.execute(new_desk.confirmAddressDisableInRegistry, i)
            assert address(new_desk.getAddr(i)) == ZERO

    log.h1("6. Cache token scales, restore delays, relinquish setup governance")
    tokens = {address(mc.assets(i)) for i in range(1, int(mc.numAssets()))}
    for name in new:
        tokens.update(address(a) for a in new[name].getPricedAssets())
    tokens.update(address(a) for a in assets["wsuperOETHbPrices"])
    tokens.update(address(c[0]) for _, c in undy_configs)
    for _, c in curve_configs:
        tokens.update(address(a) for a in c[3] if address(a) != ZERO)
    tokens.update((address(hq.getAddr(1)), address(hq.getAddr(2)), address(hq.getAddr(3))))
    for token in sorted(tokens - {ZERO, address(eth), address(btc)}):
        migration.execute(new_desk.syncTokenScale, token)
        assert new_desk.tokenScale(token) != 0
    for name, source in new.items():
        if locks[name][2] != 0:
            migration.execute(source.setActionTimeLockAfterSetup, locks[name][2])
        assert source.actionTimeLock() == locks[name][2]
        migration.execute(source.relinquishGov)
        assert address(source.governance()) == ZERO
    if desk.registryChangeTimeLock() != 0:
        migration.execute(new_desk.setRegistryTimeLockAfterSetup, desk.registryChangeTimeLock())
    migration.execute(new_desk.relinquishGov)
    assert address(new_desk.governance()) == ZERO
    assert new_desk.registryChangeTimeLock() == desk.registryChangeTimeLock()
    assert new_desk.PRICE_SOURCE_PRICE_GAS() == 3_000_000
    assert new_desk.PRICE_SOURCE_SNAPSHOT_GAS() == 3_000_000
    assert address(hq.getAddr(7)) == address(active_desk)
    assert rows == [desk.getAddr(i) for i in range(1, 10)]
    log.info(f"CONFIGURED, INACTIVE PRICEDESK: {new_desk.address}")
    for name, source in new.items():
        log.info(f"{name}: {source.address}")
    log.info("No HQ proposal sent. Unused slots disabled; live Aero and wrapped-OETH retained unchanged.")
    log.info("Existing retired mcbETH/VVV fallback behavior is unchanged, not newly enabled.")
    log.info("Fresh Curve/Undy snapshots only: recheck warmup and every collateral route before activation.")
