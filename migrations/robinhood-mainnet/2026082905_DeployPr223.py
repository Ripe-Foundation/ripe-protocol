"""Deploy PR #223 from a current-state Defaults snapshot.

This intentionally has no scheduled cutover block or parked intermediate
state.  It deploys the replacement generation, proves that the replacement
MissionControl reproduces the current live configuration, and prints one
atomic Safe registry update.
"""

from pathlib import Path

import boa

from config.robinhood_launch import (
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    ZERO_ADDRESS,
)
from scripts.utils import log
from scripts.utils.migration import Migration


STAGED_SUFFIX = "Pr223Candidate2026082905"
DEFAULTS_PATH = Path("contracts/config/DefaultsRobinhoodLive.vy")
SNAPSHOT_BLOCK = 49_396_516

RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
SWITCHBOARD = "0xA1872467AC4fb442aeA341163A65263915ce178a"
MISSION_CONTROL = "0x6445Faf17Bf8CE20ea8f038E028078F1E6B87faC"
LOOTBOX = "0xd116e21CeAa84D5Fa32263E2452DAa94a941DF13"
CONTRIBUTOR = "0x619DcD2d3a4Ef3146f0A9B132bF72A333B916E68"

SWITCHBOARD_BRAVO = "0x20857b906A5C35EFcae98bAfC83fEF91B5f49B1b"
SWITCHBOARD_CHARLIE = "0x27bC3A748d363f27094e0D21c7fDF4F42bf64c0F"
SWITCHBOARD_FOXTROT = "0x204352BDDEA8136b3eF5b738B8420C2E4aB08B4e"

LOOTBOX_ARGS = (1, 0, 0, 0)


def staged(name):
    return f"{name}{STAGED_SUFFIX}"


def migrate(migration: Migration):
    log.h1("1. Checking the current PR #223 source state")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    switchboard = migration.get_contract("Switchboard", SWITCHBOARD)
    old_mc = migration.get_contract("MissionControl", MISSION_CONTROL)

    require_slot(hq, 5, MISSION_CONTROL)
    require_slot(hq, 16, LOOTBOX)
    require_slot(switchboard, 2, SWITCHBOARD_BRAVO)
    require_slot(switchboard, 3, SWITCHBOARD_CHARLIE)
    require_slot(switchboard, 6, SWITCHBOARD_FOXTROT)
    assert int(hq.registryChangeTimeLock()) == 0
    assert int(switchboard.registryChangeTimeLock()) == 0
    assert int(switchboard.numAddrs()) == 7
    assert not bool(switchboard.isValidRegId(7))
    require_current_defaults_snapshot()

    log.h1("2. Deploying the PR #223 current-state generation")

    contributor = migration.get_contract("Contributor", CONTRIBUTOR)
    defaults = migration.deploy(
        "DefaultsRobinhoodLive",
        contributor,
        label=staged("DefaultsRobinhoodLive"),
    )
    mission_control = migration.deploy(
        "MissionControl",
        hq,
        defaults,
        label=staged("MissionControl"),
    )
    if not equivalent_mission_control(old_mc, mission_control):
        raise RuntimeError("PR223_DEFAULTS_DO_NOT_MATCH_LIVE")
    require_reward_vaults(mission_control)

    lootbox = migration.deploy(
        "Lootbox",
        hq,
        *LOOTBOX_ARGS,
        label=staged("Lootbox"),
    )
    bravo = deploy_board(migration, "SwitchboardBravo", hq)
    charlie = deploy_board(migration, "SwitchboardCharlie", hq)
    foxtrot = deploy_board(migration, "SwitchboardFoxtrot", hq)
    golf = deploy_board(migration, "SwitchboardGolf", hq)

    for contract in (lootbox, bravo, charlie, foxtrot, golf):
        if len(boa.env.get_code(contract.address)) > 24_576:
            raise RuntimeError(f"PR223_RUNTIME_TOO_LARGE:{contract.address}")

    log.h1("3. One atomic Safe registry update")
    print_safe_batch(
        mission_control=mission_control,
        lootbox=lootbox,
        bravo=bravo,
        charlie=charlie,
        foxtrot=foxtrot,
        golf=golf,
    )


def deploy_board(migration, name, hq):
    board = migration.deploy(
        name,
        hq,
        migration.account(),
        SWITCHBOARD_MIN_TIMELOCK,
        SWITCHBOARD_MAX_TIMELOCK,
        label=staged(name),
    )
    assert address(board.governance()) in (
        address(migration.account()),
        ZERO_ADDRESS,
    )
    assert migration.execute_reconciled(
        board.relinquishGov,
        lambda: address(board.governance()) == ZERO_ADDRESS,
    )
    assert address(board.governance()) == ZERO_ADDRESS
    assert int(board.actionTimeLock()) == 0
    return board


def require_current_defaults_snapshot():
    source = DEFAULTS_PATH.read_text()
    required = (
        f"#   snapshot block: {SNAPSHOT_BLOCK}",
        "#   snapshot finality: unfinalized current-state snapshot explicitly requested",
        f"#   MissionControl: {MISSION_CONTROL}",
    )
    missing = tuple(value for value in required if value not in source)
    if missing:
        raise RuntimeError("PR223_DEFAULTS_NOT_CURRENT:" + ",".join(missing))


def equivalent_mission_control(old, fresh):
    getters = (
        "genConfig",
        "genDebtConfig",
        "hrConfig",
        "ripeBondConfig",
        "rewardsConfig",
        "getPriorityLiqAssetVaults",
        "getPriorityStabVaults",
        "getPriorityPriceSourceIds",
        "underscoreRegistry",
        "trainingWheels",
        "shouldCheckLastTouch",
        "coreRipeGovVaultId",
        "preferredStabVaultId",
        "totalPointsAllocs",
    )
    if any(
        normalized(getattr(old, name)())
        != normalized(getattr(fresh, name)())
        for name in getters
    ):
        return False

    old_assets = tuple(old.assets(i) for i in range(1, int(old.numAssets())))
    fresh_assets = tuple(fresh.assets(i) for i in range(1, int(fresh.numAssets())))
    if tuple(map(address, old_assets)) != tuple(map(address, fresh_assets)):
        return False
    for asset in old_assets:
        if normalized(old.assetConfig(asset)) != normalized(
            fresh.assetConfig(asset)
        ):
            return False
        if normalized(old.ripeGovVaultConfig(asset)) != normalized(
            fresh.ripeGovVaultConfig(asset)
        ):
            return False

    old_signers = tuple(
        old.liteSigners(i) for i in range(1, int(old.numLiteSigners()))
    )
    fresh_signers = tuple(
        fresh.liteSigners(i) for i in range(1, int(fresh.numLiteSigners()))
    )
    if tuple(map(address, old_signers)) != tuple(map(address, fresh_signers)):
        return False

    for vault_id in range(1, 6):
        if bool(old.isStabVaultId(vault_id)) != bool(
            fresh.isStabVaultId(vault_id)
        ):
            return False
        if bool(old.isRipeGovVaultId(vault_id)) != bool(
            fresh.isRipeGovVaultId(vault_id)
        ):
            return False
    return True


def require_reward_vaults(mission_control):
    for index in range(1, int(mission_control.numAssets())):
        asset = mission_control.assets(index)
        vault_ids = tuple(map(int, mission_control.assetConfig(asset)[0]))
        expected = vault_ids[0] if len(vault_ids) == 1 else 0
        assert int(mission_control.rewardVaultId(asset)) == expected
        assert int(mission_control.accrualStartBlock(asset, expected)) == 0


def print_safe_batch(**fresh):
    log.info(f'const hq = c.Ripe_RH_RipeHq.at("{RIPE_HQ}")')
    log.info(
        f'const switchboard = c.Ripe_RH_Switchboard.at("{SWITCHBOARD}")'
    )
    log.info("")
    log.info("// PR #223 current-state cutover; execute as one atomic Safe batch.")
    log.info("// 1. Install the data layer before contracts that consume the new clock.")
    print_registry_update("hq", 5, fresh["mission_control"], "MissionControl")
    print_registry_update("hq", 16, fresh["lootbox"], "Lootbox")
    log.info("")
    log.info("// 2. Replace the three modified boards.")
    print_registry_update("switchboard", 2, fresh["bravo"], "SwitchboardBravo")
    print_registry_update("switchboard", 3, fresh["charlie"], "SwitchboardCharlie")
    print_registry_update("switchboard", 6, fresh["foxtrot"], "SwitchboardFoxtrot")
    log.info("")
    log.info("// 3. Register the new asset-configuration board as id 7.")
    log.info(
        "await switchboard.startAddNewAddressToRegistry("
        f'"{fresh["golf"].address}", "SwitchboardGolf")'
    )
    log.info(
        "await switchboard.confirmNewAddressToRegistry("
        f'"{fresh["golf"].address}")'
    )
    log.info("")
    log.info("// Then run migration 2026082906 to verify and publish manifest names.")


def print_registry_update(registry, registry_id, contract, name):
    log.info(
        f"await {registry}.startAddressUpdateToRegistry({registry_id}n, "
        f'"{contract.address}")  // {name}'
    )
    log.info(
        f"await {registry}.confirmAddressUpdateToRegistry({registry_id}n)  "
        f"// {name}"
    )


def require_slot(registry, registry_id, expected):
    if address(registry.getAddr(registry_id)) != address(expected):
        raise RuntimeError(f"PR223_ACTIVE_SLOT_MISMATCH:{registry_id}")


def normalized(value):
    if isinstance(value, str) and value.startswith("0x") and len(value) == 42:
        return value.lower()
    if isinstance(value, (tuple, list)):
        return tuple(normalized(item) for item in value)
    return value


def address(value):
    return str(getattr(value, "address", value)).lower()
