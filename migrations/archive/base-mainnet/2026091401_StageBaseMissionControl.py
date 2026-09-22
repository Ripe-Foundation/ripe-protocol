"""Finish staging Base config; defer initialization to governance cutover.

Keep deployment slots 1 and 2 unchanged: Contributor and DefaultsBaseLive
already exist on Base and are authenticated/reused by the migration journal.
Recorded slots 1 through 44 are retained. MC remains uninitialized.
"""

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
    migration.deploy(
        "SwitchboardFoxtrot", hq.address, ZERO,
        params["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        params["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
        label=f"SwitchboardFoxtrotWithDefaults{SUFFIX}",
    )
    # Journal slot 4 above is already deployed: keep its source/args unchanged.
    # New setup-enabled Foxtrot accepts temporary governance for inactive MC init.
    initializer = migration.deploy(
        "SwitchboardFoxtrotSetup", hq.address, migration.account(),
        params["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        params["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
        label=f"SwitchboardFoxtrotSetup{SUFFIX}",
    )
    log.info(f"REPLACEMENT FOXTROT: {initializer.address}")
    log.h1("4. Deploy and populate the replacement Switchboard")
    # The Stage 1 registry had no temporary governor and remains untouched.
    # Follow 2025071502: deployer configures this NEW registry, then relinquishes.
    verified.require_unchanged()
    switchboard = migration.deploy(
        "Switchboard", hq.address, migration.account(),
        params["MIN_SWITCHBOARD_CHANGE_TIMELOCK"],
        params["MAX_SWITCHBOARD_CHANGE_TIMELOCK"],
        label=f"SwitchboardPopulated{SUFFIX}",
    )
    for reg_id, suffix in enumerate(
        ("Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf"), 1
    ):
        board = initializer if suffix == "Foxtrot" else migration.get_contract(
            f"Switchboard{suffix}{SUFFIX}"
        )
        # Keep every journalled call in the same order on resume.
        migration.execute(
            switchboard.startAddNewAddressToRegistry, board.address, f"Switchboard {suffix}"
        )
        migration.execute(switchboard.confirmNewAddressToRegistry, board.address)
        if address(switchboard.getAddr(reg_id)) != address(board.address):
            raise RuntimeError(f"BASE_SWITCHBOARD_SLOT_MISMATCH:{reg_id}")
    migration.execute(switchboard.relinquishGov)
    if address(switchboard.governance()) != ZERO or int(switchboard.numAddrs()) != 8:
        raise RuntimeError("BASE_SWITCHBOARD_SETUP_INCOMPLETE")
    log.info(f"POPULATED SWITCHBOARD (HQ slot 6 candidate): {switchboard.address}")

    log.h1("5. Deploy and populate the replacement VaultBook")
    old_book = migration.get_contract("VaultBook", hq.getAddr(8))
    if int(old_book.numAddrs()) != 6 or int(old_book.minRegistryTimeLock()) != 21_600:
        raise RuntimeError("BASE_VAULTBOOK_TOPOLOGY_DRIFT")
    book = migration.deploy(
        "VaultBook", hq.address, migration.account(), 21_600,
        params["VAULT_BOOK_MAX_REG_TIMELOCK"],
        label=f"VaultBookPopulated{SUFFIX}",
    )
    vaults = [(i, old_book.getAddr(i), f"Retained vault {i}") for i in range(1, 6)]
    vaults += [
        (i, migration.get_contract(f"{name}{SUFFIX}").address, name)
        for i, name in enumerate(
            ("StabilityPool", "RipeGov", "SimpleErc20", "RebaseErc20", "UnderscoreVault"), 6
        )
    ]
    for reg_id, vault, description in vaults:
        if address(vault) == ZERO:
            raise RuntimeError(f"BASE_VAULTBOOK_EMPTY_RETAINED_SLOT:{reg_id}")
        migration.execute(book.startAddNewAddressToRegistry, vault, description)
        migration.execute(book.confirmNewAddressToRegistry, vault)
        if address(book.getAddr(reg_id)) != address(vault):
            raise RuntimeError(f"BASE_VAULTBOOK_SLOT_MISMATCH:{reg_id}")
    migration.execute(book.relinquishGov)
    if address(book.governance()) != ZERO or int(book.numAddrs()) != 11:
        raise RuntimeError("BASE_VAULTBOOK_SETUP_INCOMPLETE")
    log.info(f"POPULATED VAULTBOOK (HQ slot 8 candidate): {book.address}")
    migration.execute(
        initializer.startDefaultsInitialization, candidate.address, defaults.address
    )
    if (address(initializer.missionControl()) != address(candidate.address)
            or address(initializer.defaults()) != address(defaults.address)):
        raise RuntimeError("BASE_MC_FOXTROT_DEFAULTS_BINDING_MISMATCH")
    if initializer.initStep() != 1 or candidate.numAssets() != 1:
        raise RuntimeError("BASE_MC_EXPECTED_UNINITIALIZED_CANDIDATE")

    # Slot 45: no initialization or HQ activation during staging. The Safe can
    # use the bound loader at cutover; deployer authority is no longer needed.
    migration.execute(initializer.relinquishGov)
    if address(initializer.governance()) != ZERO:
        raise RuntimeError("BASE_MC_FOXTROT_GOVERNANCE_NOT_RELINQUISHED")
    if address(hq.getAddr(5)) != address(active_address):
        raise RuntimeError("BASE_UPGRADE_ACTIVE_ADDRESS_CHANGED:MissionControl")

    log.info("Staging complete. MC is UNINITIALIZED and must not be activated yet.")
    log.info("No HQ updates were proposed. At cutover: activate Switchboard, "
             "initialize inactive MC via governance, verify configuration, "
             "then confirm MC and initialize rewards.")

def address(value):
    return str(getattr(value, "address", value)).lower()
