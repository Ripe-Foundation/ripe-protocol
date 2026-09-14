"""Stage a fresh Defaults/MissionControl snapshot without activating either."""

import boa

from scripts.utils import log
from scripts.utils.migration import Migration


ZERO = "0x" + "00" * 20
SUFFIX = "BaseUpgradeCandidate20260914"


def migrate(migration: Migration):
    log.h1("1. Read the active Base MissionControl")
    if migration.chain() != "base-mainnet":
        raise RuntimeError("BASE_UPGRADE_WRONG_PROFILE")
    hq = migration.get_contract("RipeHq")
    active_address = hq.getAddr(5)
    if address(active_address) == ZERO:
        raise RuntimeError("BASE_UPGRADE_MISSING_ACTIVE:MissionControl")
    old = migration.get_contract("MissionControl", active_address)

    log.h1("2. Deploy the freshly generated defaults snapshot")
    # Run prepare_defaults.py and verify_defaults.py immediately before this
    # stage. This snapshot is NOT the final cutover configuration.
    contributor = migration.deploy_bp("Contributor", label=f"Contributor{SUFFIX}")
    defaults = migration.deploy(
        "DefaultsBaseLive",
        contributor.address,  # template for FUTURE contributors only
        label=f"DefaultsBaseLive{SUFFIX}",
    )
    size = len(boa.env.get_code(defaults.address))
    if not 0 < size <= 24576:
        raise RuntimeError(f"BASE_UPGRADE_RUNTIME_SIZE:DefaultsBaseLive:{size}")
    log.info(f"STAGED ONLY DefaultsBaseLive: {defaults.address}")
    for getter in ("genConfig", "genDebtConfig", "hrConfig", "ripeBondConfig",
                   "rewardsConfig"):
        expected = list(getattr(old, getter)())
        if getter == "hrConfig":
            expected[0] = contributor.address
        if tuple(getattr(defaults, getter)()) != tuple(expected):
            raise RuntimeError(f"BASE_UPGRADE_REFRESH_DEFAULTS:{getter}")

    log.h1("3. Deploy MissionControl using that snapshot")
    candidate = migration.deploy(
        "MissionControl", hq.address, defaults.address,
        label=f"MissionControl{SUFFIX}",
    )
    size = len(boa.env.get_code(candidate.address))
    if not 0 < size <= 24576:
        raise RuntimeError(f"BASE_UPGRADE_RUNTIME_SIZE:MissionControl:{size}")
    log.info(f"STAGED ONLY MissionControl: {candidate.address}")

    log.h1("4. Compare the staged configuration with the live configuration")
    for getter in ("genConfig", "genDebtConfig", "hrConfig", "ripeBondConfig",
                   "rewardsConfig", "totalPointsAllocs"):
        expected = list(getattr(old, getter)())
        if getter == "hrConfig":
            expected[0] = contributor.address
        if tuple(getattr(candidate, getter)()) != tuple(expected):
            raise RuntimeError(f"BASE_UPGRADE_CONFIG_DRIFT:{getter}")
    if int(candidate.numAssets()) != int(old.numAssets()):
        raise RuntimeError("BASE_UPGRADE_ASSET_COUNT_DRIFT")
    for i in range(1, int(old.numAssets())):
        asset = old.assets(i)
        if (address(candidate.assets(i)) != address(asset)
                or tuple(candidate.assetConfig(asset)) != tuple(old.assetConfig(asset))):
            raise RuntimeError(f"BASE_UPGRADE_ASSET_DRIFT:{asset}")
    if address(hq.getAddr(5)) != address(active_address):
        raise RuntimeError("BASE_UPGRADE_ACTIVE_ADDRESS_CHANGED:MissionControl")

    log.info("MissionControl staged only. Reconcile all live state again at cutover.")


def address(value):
    return str(getattr(value, "address", value)).lower()
