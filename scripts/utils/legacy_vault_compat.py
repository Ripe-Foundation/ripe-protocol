"""Read-only invariants shared by staging and the independent cutover command."""
from scripts.utils.migration import authenticate_deployed_record

ZERO = "0x" + "00" * 20
VAULT_BOOK_MIN_TIMELOCK = 21_600
PREVIOUS_SUFFIX = "BaseUpgradeCandidate20260914"
REUSED_CONTROLLERS = {2: "SwitchboardBravo", 4: "SwitchboardDelta", 5: "SwitchboardEcho", 6: "SwitchboardFoxtrotSetup"}
# Original constructor authority: migration_history/base-mainnet/v1/current-manifest.json,
# SwitchboardFoxtrotSetupBaseUpgradeCandidate20260914, second encoded constructor
# address in `args`; deployment address also pinned by 2026091401-manifest.json.
# The temporary authority was subsequently relinquished.
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
    verify_foxtrot_setup(resolved[6], get_record("MissionControl" + PREVIOUS_SUFFIX)["address"],
                        get_record("DefaultsBaseLive" + PREVIOUS_SUFFIX)["address"])
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


HQ_SLOTS = (5, 6, 8, 9, 18)
KNOWN_SLOT8_UPDATE = ("0x09f45f56b218756ab092f7470f8199db56849867", 49_890_175, 49_911_775)


def pending_actions(registry, rows):
    return {str(i): {"update": [address(registry.pendingAddrUpdate(i)[0]),
                                *map(int, registry.pendingAddrUpdate(i)[1:])],
                     "disable": list(map(int, registry.pendingAddrDisable(i)))} for i in rows}


def verify_registry_pending(registry, rows):
    state = pending_actions(registry, rows)
    for row, pending in state.items():
        require(pending == {"update": [ZERO, 0, 0], "disable": [0, 0]}, "REGISTRY_PENDING:" + row)
    return state


def review_hq_pending(hq):
    """Staging disposition: empty, or preserve the exact known slot-8 conflict.

    Preserving the conflict is explicitly not permission to activate. Any new
    proposal/disable requires a new reviewed baseline; it is never auto-adopted.
    """
    state = pending_actions(hq, HQ_SLOTS)
    for row, pending in state.items():
        require(pending["disable"] == [0, 0], "HQ_PENDING_DISABLE:" + row)
        require(pending["update"] == [ZERO, 0, 0]
                or (row == "8" and tuple(pending["update"]) == KNOWN_SLOT8_UPDATE), "HQ_PENDING_UPDATE:" + row)
    return {row: dict(value, disposition="hold_no_activation" if value["update"][0] != ZERO else "require_empty")
            for row, value in state.items()}


def verify_foxtrot_setup(controller, mission_control, defaults):
    state = {"missionControl": address(controller.missionControl()), "defaults": address(controller.defaults()),
             "initStep": int(controller.initStep()), "nextAssetIndex": int(controller.nextAssetIndex()),
             "rewardsInitialized": bool(controller.rewardsInitialized())}
    expected = {"missionControl": address(mission_control), "defaults": address(defaults),
                "initStep": 1, "nextAssetIndex": 0, "rewardsInitialized": False}
    for field, value in expected.items():
        require(state[field] == value, "FOXTROT_SETUP:" + field)
    return state


def retained_rows(book):
    require(book.numAddrs() == 6 and book.getNumAddrs() == 5, "ACTIVE_RETAINED_COUNT")
    rows = [address(book.getAddr(i)) for i in range(1, 6)]
    require(len(set(rows)) == 5 and ZERO not in rows, "ACTIVE_RETAINED_ADDRESSES")
    for i, value in enumerate(rows, 1):
        require(book.getRegId(value) == i and book.isValidRegId(i), "ACTIVE_RETAINED_IDENTITY:" + str(i))
    return rows


def source_state(hq, book, dl, get_record, board, lo, hi, dl_params):
    import hashlib
    import boa
    controllers = authenticate_reused_controllers(get_record, board, hq.address, lo, hi)
    return {"hq": {str(i): address(hq.getAddr(i)) for i in HQ_SLOTS},
            "pending": review_hq_pending(hq), "retained_rows": retained_rows(book),
            "deleverage": [int(getattr(dl, name)()) for name in dl_params[:4]],
            "controllers": {str(i): {"address": address(c), "runtime_sha256": hashlib.sha256(boa.env.get_code(c.address)).hexdigest(),
                                      "hq": address(c.getRipeHqFromGov()), "action_bounds": [c.minActionTimeLock(), c.maxActionTimeLock()],
                                      "governance": address(c.governance()), "pending_gov": [address(c.pendingGov()[0]), *c.pendingGov()[1:]]}
                            for i, c in controllers.items()},
            "foxtrot": verify_foxtrot_setup(controllers[6], get_record("MissionControl" + PREVIOUS_SUFFIX)["address"],
                                             get_record("DefaultsBaseLive" + PREVIOUS_SUFFIX)["address"])}
