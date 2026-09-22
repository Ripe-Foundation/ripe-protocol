"""Deploy only. Governance registers Foxtrot and initializes inactive MC later."""

from scripts.utils import log
from scripts.utils.migration import Migration

ZERO = "0x" + "00" * 20
HQ = "0x6162df1b329e157479f8f1407e888260e0ec3d2b"
SUFFIX = "BaseConfig20260921"


def migrate(migration: Migration):
    if migration.chain() != "base-mainnet":
        raise RuntimeError("BASE_CONFIG_WRONG_PROFILE")
    hq = migration.get_contract("RipeHq")
    if str(hq.address).lower() != HQ:
        raise RuntimeError("BASE_CONFIG_WRONG_HQ")
    active_mc = hq.getAddr(5)
    active_sb = hq.getAddr(6)
    live = migration.get_contract("MissionControl", active_mc)
    contributor_template = live.hrConfig()[0]
    params = migration.blueprint().PARAMS

    log.h1("1. Verify Defaults against current Base configuration")
    verified = migration.verify_base_defaults(mission_control_only=True)
    log.info(f"Defaults preflight block {verified.block}: {verified.block_hash}")

    log.h1("2. Deploy Defaults, preserving the current Contributor template")
    verified.require_unchanged()
    defaults = migration.deploy(
        "DefaultsBaseLive", contributor_template,
        label=f"DefaultsBaseLive{SUFFIX}",
    )
    if tuple(defaults.hrConfig()) != tuple(live.hrConfig()):
        raise RuntimeError("BASE_CONFIG_HR_DRIFT")

    log.h1("3. Deploy empty MissionControl")
    verified.require_unchanged()
    mc = migration.deploy(
        "MissionControl", hq.address, ZERO,
        label=f"MissionControl{SUFFIX}",
    )

    log.h1("4. Deploy Foxtrot with HQ governance only")
    verified.require_unchanged()
    foxtrot = migration.deploy(
        "SwitchboardFoxtrot", hq.address, ZERO,
        params["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        params["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
        label=f"SwitchboardFoxtrot{SUFFIX}",
    )
    if mc.numAssets() != 1 or mc.numLiteSigners() != 1 or foxtrot.initStep() != 0:
        raise RuntimeError("BASE_CONFIG_EXPECTED_EMPTY_CANDIDATES")
    if hq.getAddr(5) != active_mc or hq.getAddr(6) != active_sb:
        raise RuntimeError("BASE_CONFIG_ACTIVE_REGISTRY_CHANGED")

    log.info(f"Defaults: {defaults.address}")
    log.info(f"MissionControl (EMPTY, do not activate): {mc.address}")
    log.info(f"Foxtrot (UNREGISTERED): {foxtrot.address}")
    log.info("Next: governance registers/confirms Foxtrot in the CURRENT Switchboard.")
    log.info(f"Then call startDefaultsInitialization({mc.address}, {defaults.address}) on Foxtrot.")
    log.info("Call initConfig until initStep == 5, then review MC before proposing activation.")
    log.info("Rewards remain separate: initRewards can only run AFTER MC activation.")
