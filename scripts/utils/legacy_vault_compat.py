"""Read-only invariants shared by staging and the independent cutover command."""
from scripts.utils.migration import authenticate_deployed_record

ZERO = "0x" + "00" * 20
VAULT_BOOK_MIN_TIMELOCK = 21_600
PREVIOUS_SUFFIX = "BaseUpgradeCandidate20260914"
REUSED_CONTROLLERS = {2: "SwitchboardBravo", 4: "SwitchboardDelta", 5: "SwitchboardEcho", 6: "SwitchboardFoxtrotSetup"}
# Constructor authority recorded for the setup-only Foxtrot, since relinquished.
SETUP_DEPLOYER = "0xef3cb7750ff6158d9f9b27651bbba2299096483b"


def verify_local_governance(contract):
    require(address(contract.governance()) == ZERO, "TEMP_GOV_RETAINED")
    pending = tuple(contract.pendingGov())
    require(address(pending[0]) == ZERO and pending[1:] == (0, 0), "PENDING_LOCAL_GOV")


def authenticate_controller(record, name, hq, min_lock, max_lock):
    args = (str(hq), SETUP_DEPLOYER if name == "SwitchboardFoxtrotSetup" else ZERO, min_lock, max_lock)
    contract = authenticate_deployed_record(record, expected_source_path=f"contracts/config/{name}.vy", expected_constructor_args=args)
    require(address(contract.getRipeHqFromGov()) == address(hq), "CONTROLLER_HQ")
    require(contract.minActionTimeLock() == min_lock and contract.maxActionTimeLock() == max_lock, "CONTROLLER_ACTION_BOUNDS")
    verify_local_governance(contract)
    return contract


def authenticate_reused_controllers(get_record, old_switchboard, hq, min_lock, max_lock):
    resolved = {}
    for reg_id, name in REUSED_CONTROLLERS.items():
        record = get_record(name + PREVIOUS_SUFFIX)
        require(address(old_switchboard.getAddr(reg_id)) == address(record["address"]), f"CONTROLLER_ADDRESS:{reg_id}")
        require(old_switchboard.isValidRegId(reg_id) and old_switchboard.getRegId(record["address"]) == reg_id, f"CONTROLLER_ROW:{reg_id}")
        resolved[reg_id] = authenticate_controller(record, name, hq, min_lock, max_lock)
    return resolved


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
    verify_local_governance(book)
