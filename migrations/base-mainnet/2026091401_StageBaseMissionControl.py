"""Resume the partial Base config deployment, then await Safe initialization.

Keep deployment slots 1 and 2 unchanged: Contributor and DefaultsBaseLive
already exist on Base and are authenticated/reused by the migration journal.
Only the not-yet-deployed MC constructor and subsequent steps are changed.
"""

import boa

from scripts.utils import log
from scripts.utils.migration import Migration
from scripts.verify_defaults import compare_mission_control_config, _normalize


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

    log.h1("2. Verify exact defaults in an isolated fork before any deployment")
    verified = migration.verify_base_defaults()
    log.info(f"Defaults preflight block {verified.block}: {verified.block_hash}")
    # Never invoke the verifier's boa.fork inside this deployment process.
    # This snapshot is NOT the final cutover configuration.
    verified.require_unchanged()
    # Journal slot 1: retain the original label and call order for resume.
    contributor = migration.deploy_bp("Contributor", label=f"Contributor{SUFFIX}")
    verified.require_unchanged()
    # Journal slot 2: retain the deployed snapshot and its constructor argument.
    defaults = migration.deploy(
        "DefaultsBaseLive",
        contributor.address,  # template for FUTURE contributors only
        label=f"DefaultsBaseLive{SUFFIX}",
    )
    log.info(f"Contributor snapshot dependency: {contributor.address}")
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

    log.h1("3. Deploy empty MissionControl and its fixed defaults switchboard")
    verified.require_unchanged()
    candidate = migration.deploy(
        "MissionControl", hq.address, ZERO,
        label=f"MissionControl{SUFFIX}",
    )
    size = len(boa.env.get_code(candidate.address))
    if not 0 < size <= 24576:
        raise RuntimeError(f"BASE_UPGRADE_RUNTIME_SIZE:MissionControl:{size}")
    log.info(f"STAGED ONLY MissionControl: {candidate.address}")

    verified.require_unchanged()
    params = migration.blueprint().PARAMS
    # Stage 1 Foxtrot is already deployed. Preserve that historical record and
    # deploy its replacement under a NEW label, never overwrite/replay Stage 1.
    initializer = migration.deploy(
        "SwitchboardFoxtrot", hq.address, ZERO,
        params["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        params["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
        label=f"SwitchboardFoxtrotWithDefaults{SUFFIX}",
    )
    log.info(f"REPLACEMENT FOXTROT: {initializer.address}")
    # Deployment journal remains resumable while governance registers and runs
    # the initializer. Never impersonate governance or switch RPCs here.
    if initializer.initStep() != 5:
        raise RuntimeError(
            f"BASE_MC_AWAITING_SAFE_INIT:{initializer.address}: "
            f"register Foxtrot in active Switchboard, call startDefaultsInitialization("
            f"{candidate.address}, {defaults.address}) ONCE, then initConfig until initStep=5, "
            "then resume this migration. Do not activate MC yet."
        )
    if (address(initializer.missionControl()) != address(candidate.address)
            or address(initializer.defaults()) != address(defaults.address)):
        raise RuntimeError("BASE_MC_FOXTROT_DEFAULTS_BINDING_MISMATCH")

    log.h1("4. Compare the staged configuration with the live configuration")

    def compare(field, actual, expected):
        if field == "rewardsConfig":
            # MC's existing setter requires the candidate to be active.
            # The fixed snapshot was checked above; load it after confirmation.
            if any(actual):
                raise RuntimeError("BASE_UPGRADE_REWARDS_SET_BEFORE_ACTIVATION")
            return
        if _normalize(actual) != _normalize(expected):
            raise RuntimeError(f"BASE_UPGRADE_CONFIG_DRIFT:{field}")
    compare_mission_control_config(candidate, lambda name, *args: getattr(old, name)(*args),
                                   compare, contributor.address)
    if address(hq.getAddr(5)) != address(active_address):
        raise RuntimeError("BASE_UPGRADE_ACTIVE_ADDRESS_CHANGED:MissionControl")

    log.info("MissionControl staged only. Reconcile all live state again at cutover.")
    log.info("After HQ confirms this MC, call initializer.initRewards() before reopening. "
             "The initializer must still be registered in the then-active Switchboard.")


def address(value):
    return str(getattr(value, "address", value)).lower()
