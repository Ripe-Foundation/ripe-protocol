"""Stage the retained-only Base compatibility set; never propose or activate it.

Use a new journal and labels. The 20260914 migrations/manifests are historical.
Migration.deploy records each candidate and its constructor inputs; the normal
runner records the completed step manifest only after all readbacks pass.
"""

import boa

from scripts.utils import log
from scripts.utils.migration import Migration

ZERO = "0x" + "00" * 20
EXPECTED_HQ = "0x6162df1b329e157479f8f1407e888260e0ec3d2b"
EXPECTED_POOL = "0x2a157096af6337b2b4bd47de435520572ed5a439"
SUFFIX = "BaseLegacyCompatCandidate20260919"
PREVIOUS_SUFFIX = "BaseUpgradeCandidate20260914"
VAULT_BOOK_MIN_TIMELOCK = 21_600
BOARD_NAMES = ("Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf")
DELEVERAGE_PARAMS = (
    "minDeleverageBps", "deleverageBuffer", "deleverageCooldown", "underscoreSafeSpreadBps",
    "deleverageFullPayoffBuffer", "deleverageOverageBps", "deleverageDustThreshold", "deleverageDustBps",
)


def address(value):
    return str(getattr(value, "address", value)).lower()


def require(ok, reason):
    if not ok:
        raise RuntimeError("BASE_LEGACY_COMPAT_" + reason)


def verify_book(book, pool, retained):
    """Public readbacks required again against the final candidate at cutover."""
    require(address(book.LEGACY_POOL()) == address(pool), "BINDING_MISMATCH")
    require(book.getRegId(pool) == 1, "POOL_REVERSE_ROW")
    require(address(book.getAddr(1)) == address(pool), "POOL_FORWARD_ROW")
    require(book.isValidRegId(1), "POOL_INVALID_ROW")
    require(book.numAddrs() == 6 and book.getNumAddrs() == 5, "NOT_RETAINED_ONLY")
    for reg_id, vault in enumerate(retained, 1):
        require(address(book.getAddr(reg_id)) == address(vault), f"RETAINED_ROW:{reg_id}")
        require(book.getRegId(vault) == reg_id and book.isValidRegId(reg_id), f"RETAINED_IDENTITY:{reg_id}")
    for reg_id in range(6, 11):
        require(address(book.getAddr(reg_id)) == ZERO and not book.isValidRegId(reg_id), f"FUTURE_ROW:{reg_id}")
    probe_asset = pool.vaultAssets(1)
    require(address(probe_asset) != ZERO, "MISSING_PROBE_ASSET")
    require(book.hasStabilityPoolInterface(pool, probe_asset, ZERO), "MISSING_INTERFACE")
    require(not book.canAcceptLiquidationAsset(pool, probe_asset, ZERO), "READINESS_ABI")
    require(tuple(book.getDeleverageTraversalAsset(ZERO, pool, 0, True)) == (ZERO, 0), "TRAVERSAL_ABI")
    require(book.minRegistryTimeLock() == VAULT_BOOK_MIN_TIMELOCK, "REGISTRY_FLOOR")
    require(book.registryChangeTimeLock() == VAULT_BOOK_MIN_TIMELOCK, "REGISTRY_DELAY")
    require(address(book.governance()) == ZERO, "TEMP_GOV_RETAINED")


def migrate(migration: Migration):
    require(migration.chain() == "base-mainnet", "WRONG_PROFILE")
    hq = migration.get_contract("RipeHq")
    require(address(hq) == EXPECTED_HQ, "WRONG_HQ")
    active = tuple(hq.getAddr(i) for i in range(1, int(hq.numAddrs())))
    pending_book = tuple(hq.pendingAddrUpdate(8))
    old_book = migration.get_contract("VaultBook", hq.getAddr(8))
    require(old_book.numAddrs() == 6, "ACTIVE_TOPOLOGY_DRIFT")
    require(old_book.minRegistryTimeLock() == VAULT_BOOK_MIN_TIMELOCK, "ACTIVE_REGISTRY_FLOOR")
    retained = tuple(old_book.getAddr(i) for i in range(1, 6))
    require(len({address(v) for v in retained}) == 5 and all(address(v) != ZERO for v in retained), "ACTIVE_ROWS")
    for reg_id, vault in enumerate(retained, 1):
        require(old_book.getRegId(vault) == reg_id and old_book.isValidRegId(reg_id), f"ACTIVE_IDENTITY:{reg_id}")
    require(address(retained[0]) == EXPECTED_POOL, "WRONG_POOL")
    pool = migration.get_contract("StabilityPool", retained[0])
    require(address(pool.getRipeHq()) == address(hq), "POOL_HQ")
    require(address(pool.vaultAssets(1)) != ZERO, "MISSING_PROBE_ASSET")

    # Retain the staged economic parameters and the four unchanged controller
    # addresses. All dependencies are read before sending any deployment.
    old_dl = migration.get_contract("Deleverage" + PREVIOUS_SUFFIX)
    dl_params = tuple(getattr(old_dl, name)() for name in DELEVERAGE_PARAMS)
    old_switchboard = migration.get_contract("SwitchboardPopulated" + PREVIOUS_SUFFIX)
    require(old_switchboard.numAddrs() == 8, "STAGED_SWITCHBOARD_TOPOLOGY")
    old_boards = tuple(old_switchboard.getAddr(i) for i in range(1, 8))
    require(all(address(v) != ZERO and old_switchboard.isValidRegId(i)
                for i, v in enumerate(old_boards, 1)), "STAGED_SWITCHBOARD_ROWS")
    params = migration.blueprint().PARAMS
    min_lock, max_lock = params["MIN_SWITCHBOARD_CHANGE_TIMELOCK"], params["MAX_SWITCHBOARD_CHANGE_TIMELOCK"]
    candidates = {}

    log.h1("1. Deploy the compatible VaultBook and callers under fresh labels")
    candidates["VaultBook"] = migration.deploy(
        "VaultBook", hq.address, migration.account(), VAULT_BOOK_MIN_TIMELOCK,
        params["VAULT_BOOK_MAX_REG_TIMELOCK"], pool.address, label="VaultBook" + SUFFIX,
    )
    candidates["AuctionHouse"] = migration.deploy("AuctionHouse", hq.address, label="AuctionHouse" + SUFFIX)
    candidates["Deleverage"] = migration.deploy("Deleverage", hq.address, *dl_params, label="Deleverage" + SUFFIX)
    candidates["SwitchboardAlpha"] = migration.deploy(
        "SwitchboardAlpha", hq.address, ZERO, params["PRICE_DESK_MIN_STALE_TIME"],
        params["PRICE_DESK_MAX_STALE_TIME"], min_lock, max_lock, params["PYTH_PRICES_ID"],
        label="SwitchboardAlpha" + SUFFIX,
    )
    for suffix in ("Charlie", "Golf"):
        name = "Switchboard" + suffix
        candidates[name] = migration.deploy(name, hq.address, ZERO, min_lock, max_lock, label=name + SUFFIX)
    candidates["Switchboard"] = migration.deploy(
        "Switchboard", hq.address, migration.account(), min_lock, max_lock, label="Switchboard" + SUFFIX,
    )

    log.h1("2. Register only retained vaults 1-5 and the compatible controller set")
    book = candidates["VaultBook"]
    for reg_id, vault in enumerate(retained, 1):
        migration.execute(book.startAddNewAddressToRegistry, vault, f"Retained vault {reg_id}")
        migration.execute(book.confirmNewAddressToRegistry, vault)
    board = candidates["Switchboard"]
    final_boards = []
    for reg_id, suffix in enumerate(BOARD_NAMES, 1):
        candidate = candidates.get("Switchboard" + suffix, old_boards[reg_id - 1])
        candidate_address = getattr(candidate, "address", candidate)
        final_boards.append(candidate_address)
        migration.execute(board.startAddNewAddressToRegistry, candidate_address, "Switchboard " + suffix)
        migration.execute(board.confirmNewAddressToRegistry, candidate_address)
    for registry in (book, board):
        migration.execute(registry.setRegistryTimeLockAfterSetup)
        migration.execute(registry.relinquishGov)

    log.h1("3. Verify public binding, registry identities and inactive candidate set")
    verify_book(book, pool, retained)
    require(board.numAddrs() == 8 and address(board.governance()) == ZERO, "SWITCHBOARD_SETUP")
    require(board.registryChangeTimeLock() == min_lock, "SWITCHBOARD_DELAY")
    for reg_id, candidate in enumerate(final_boards, 1):
        require(address(board.getAddr(reg_id)) == address(candidate)
                and board.getRegId(candidate) == reg_id and board.isValidRegId(reg_id), f"SWITCHBOARD_ROW:{reg_id}")
    for name, candidate in candidates.items():
        size = len(boa.env.get_code(candidate.address))
        require(0 < size <= 24_576, f"RUNTIME_SIZE:{name}:{size}")
        log.info(f"STAGED ONLY {name + SUFFIX}: {candidate.address}; runtime bytes {size}")
    require(tuple(hq.getAddr(i) for i in range(1, int(hq.numAddrs()))) == active, "ACTIVE_HQ_CHANGED")
    require(tuple(hq.pendingAddrUpdate(8)) == pending_book, "PENDING_HQ_PROPOSAL_CHANGED")
    log.info("No HQ proposal or activation sent. Re-read and resolve pending HQ slot 8 before cutover.")
