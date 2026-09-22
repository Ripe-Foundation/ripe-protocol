"""Stage a PriceDesk backed by live sources; no HQ updates or feed changes."""

from scripts.utils import log
from scripts.utils.migration import Migration

ZERO = "0x" + "00" * 20
LABEL = "PriceDeskBridgeBaseUpgradeCandidate20260914"
SOURCE_NAMES = (
    "ChainlinkPrices", "CurvePrices", "BlueChipYieldPrices", "PythPrices",
    "StorkPrices", "AeroRipePrices", "wsuperOETHbPrices", "UndyVaultPrices", "RedStone",
)


def migrate(migration: Migration):
    if migration.chain() != "base-mainnet":
        raise RuntimeError("BASE_BRIDGE_WRONG_PROFILE")
    hq = migration.get_contract("RipeHq")
    old_address = hq.getAddr(7)
    old = migration.get_contract("PriceDesk", old_address)
    mc = migration.get_contract("MissionControl", hq.getAddr(5))
    params = migration.blueprint().PARAMS
    if int(old.numAddrs()) != 10 or str(old.getAddr(3)).lower() != ZERO:
        raise RuntimeError("BASE_BRIDGE_SOURCE_TOPOLOGY_DRIFT")

    log.h1("1. Deploy bridge PriceDesk with temporary setup governance")
    desk = migration.deploy(
        "PriceDesk", hq.address, migration.account(), old.ETH(),
        params["PRICE_DESK_MIN_REG_TIMELOCK"], params["PRICE_DESK_MAX_REG_TIMELOCK"],
        params["PRICE_DESK_PRICE_SOURCE_GAS"], params["PRICE_DESK_SNAPSHOT_SOURCE_GAS"],
        label=LABEL,
    )

    log.h1("2. Register CURRENT sources, retaining IDs and disabled BlueChip slot")
    assets = {str(mc.assets(i)).lower() for i in range(1, int(mc.numAssets()))
              if not mc.assetConfig(mc.assets(i))[-1]}
    for reg_id, name in enumerate(SOURCE_NAMES, 1):
        live_address = old.getAddr(reg_id)
        # A disabled slot still consumes its original ID. Register the historical
        # source only to reserve ID 3, then disable it before relinquishing.
        # Slot 6 is the legacy Aero source, NOT the new monitoring-only contract.
        # Use the shared source getters through the Chainlink ABI for that slot.
        source = migration.get_contract(name) if reg_id == 3 else migration.get_contract(
            "ChainlinkPrices" if reg_id == 6 else name, live_address
        )
        if reg_id != 3 and str(live_address).lower() == ZERO:
            raise RuntimeError(f"BASE_BRIDGE_UNEXPECTED_DISABLED_SOURCE:{reg_id}")
        migration.execute(desk.startAddNewAddressToRegistry, source.address, f"Retained {name}")
        migration.execute(desk.confirmNewAddressToRegistry, source.address)
        if reg_id == 3:
            migration.execute(desk.startAddressDisableInRegistry, reg_id)
            migration.execute(desk.confirmAddressDisableInRegistry, reg_id)
        else:
            assets.update(str(a).lower() for a in source.getPricedAssets())
        if str(desk.getAddr(reg_id)).lower() != str(live_address).lower():
            raise RuntimeError(f"BASE_BRIDGE_SOURCE_MISMATCH:{reg_id}")

    log.h1("3. Cache scales for current collateral and source-priced assets")
    # Deterministic ordering preserves the resumable journal. No feed settings,
    # stale times, observations, or live-source governance are modified.
    # ETH and BTC reference-feed sentinels are not ERC20 contracts. Their feeds
    # remain registered, but decimals() must never be called on the BTC sentinel.
    chainlink = migration.get_contract("ChainlinkPrices", old.getAddr(1))
    reference_assets = {ZERO, str(desk.ETH()).lower(), str(chainlink.BTC()).lower()}
    for asset in sorted(assets - reference_assets):
        migration.execute(desk.syncTokenScale, asset)
        if desk.tokenScale(asset) == 0:
            raise RuntimeError(f"BASE_BRIDGE_MISSING_SCALE:{asset}")

    log.h1("4. Relinquish setup governance; leave HQ unchanged")
    migration.execute(desk.relinquishGov)
    if str(desk.governance()).lower() != ZERO or int(desk.numAddrs()) != 10:
        raise RuntimeError("BASE_BRIDGE_SETUP_INCOMPLETE")
    if str(hq.getAddr(7)).lower() != str(old_address).lower():
        raise RuntimeError("BASE_BRIDGE_ACTIVE_DESK_CHANGED")
    log.info(f"STAGED BRIDGE PRICEDESK (HQ slot 7 candidate): {desk.address}")
    log.info("Existing feeds remain in existing sources. No HQ proposal or source replacement sent.")
