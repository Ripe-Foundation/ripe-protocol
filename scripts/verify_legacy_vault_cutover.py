"""Read-only, pinned-block checks for the retained-only compatibility candidates.

Run with python -m scripts.verify_legacy_vault_cutover --help. This module has
no NetworkEnv, wallet, transaction, deployment or governance execution path.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

import boa
from web3 import Web3

from config.BluePrint import PARAMS
from scripts.utils.legacy_vault_compat import (
    ZERO, address, require, verify_book, verify_local_governance,
    authenticate_controller, REUSED_CONTROLLERS, PREVIOUS_SUFFIX,
)
from scripts.utils.migration import authenticate_deployed_record
from scripts.utils.readonly_fork import readonly_fork
from scripts.utils.fork_reports import fingerprint, require_new_report, sanitize

ROOT = Path(__file__).resolve().parents[1]
HQ = "0x6162df1b329e157479f8f1407e888260e0ec3d2b"
POOL = "0x2a157096af6337b2b4bd47de435520572ed5a439"
SUFFIX = "BaseLegacyCompatCandidate20260919"
RETAINED = ("StabilityPool", "RipeGov", "SimpleErc20", "RebaseErc20", "Underscore Vault")
DL_PARAMS = ("minDeleverageBps", "deleverageBuffer", "deleverageCooldown", "underscoreSafeSpreadBps",
             "deleverageFullPayoffBuffer", "deleverageOverageBps", "deleverageDustThreshold", "deleverageDustBps")


def attach(records, name, target=None):
    record = records[name]
    return boa.loads_abi(json.dumps(record["abi"]), name=name).at(target or record["address"])


def verify_candidates(records, stager):
    """Checks active fork state; call independently before any simulation writes."""
    p = PARAMS["base"]
    require(address(records["RipeHq"]["address"]) == HQ, "WRONG_HQ")
    require(address(records["StabilityPool"]["address"]) == POOL, "WRONG_POOL")
    reference = json.loads((ROOT / "migration_history/base-mainnet/v1/current-manifest.json").read_text())["contracts"]
    for name in (*RETAINED, *(name + PREVIOUS_SUFFIX for name in REUSED_CONTROLLERS.values())):
        require(address(records[name]["address"]) == address(reference[name]["address"]), "RECORDED_ADDRESS:" + name)
    hq, pool = attach(records, "RipeHq"), attach(records, "StabilityPool")
    retained = [records[name]["address"] for name in RETAINED]
    require(address(pool.getRipeHq()) == HQ, "POOL_HQ")
    # Immutable historical sources have separate authenticated fixture pins.
    provenance = json.loads((ROOT / "tests/fixtures/legacy_pool/provenance.json").read_text())
    for name, pin in (("StabilityPool", "pool"), ("RipeGov", "ripe_gov")):
        require(hashlib.sha256(boa.env.get_code(records[name]["address"])).hexdigest()
                == provenance[pin]["deployed_sha256"], "RETAINED_RUNTIME:" + name)
    active_dl = attach(records, "Deleverage", hq.getAddr(18))
    dl_params = tuple(getattr(active_dl, name)() for name in DL_PARAMS[:4]) + (10**15, 100, 0, 0)
    lo, hi = p["MIN_SWITCHBOARD_CHANGE_TIMELOCK"], p["MAX_SWITCHBOARD_CHANGE_TIMELOCK"]
    args = {
        "VaultBook": (HQ, stager, 21_600, p["VAULT_BOOK_MAX_REG_TIMELOCK"], POOL),
        "AuctionHouse": (HQ,), "Deleverage": (HQ, *dl_params),
        "SwitchboardAlpha": (HQ, ZERO, p["PRICE_DESK_MIN_STALE_TIME"], p["PRICE_DESK_MAX_STALE_TIME"], lo, hi, p["PYTH_PRICES_ID"]),
        "SwitchboardCharlie": (HQ, ZERO, lo, hi), "SwitchboardGolf": (HQ, ZERO, lo, hi),
        "Switchboard": (HQ, stager, lo, hi),
    }
    candidates, evidence = {}, {}
    for name, constructor in args.items():
        record = records[name + SUFFIX]
        directory = "registries" if name in ("VaultBook", "Switchboard") else "config" if name.startswith("Switchboard") else "core"
        candidate = authenticate_deployed_record(record, expected_source_path=f"contracts/{directory}/{name}.vy", expected_constructor_args=constructor)
        is_controller = name.startswith("Switchboard") or name == "VaultBook"
        require(address(candidate.getRipeHqFromGov() if is_controller else candidate.getRipeHq()) == HQ, "CANDIDATE_HQ:" + name)
        if is_controller:
            verify_local_governance(candidate)
        if name in ("SwitchboardAlpha", "SwitchboardCharlie", "SwitchboardGolf"):
            require(candidate.minActionTimeLock() == lo and candidate.maxActionTimeLock() == hi, "ACTION_BOUNDS:" + name)
        if name == "SwitchboardAlpha":
            require(candidate.MIN_STALE_TIME() == p["PRICE_DESK_MIN_STALE_TIME"] and candidate.MAX_STALE_TIME() == p["PRICE_DESK_MAX_STALE_TIME"], "ALPHA_PRICE_BOUNDS")
        code = boa.env.get_code(candidate.address)
        require(0 < len(code) <= 24_576, "RUNTIME_SIZE:" + name)
        candidates[name] = candidate
        evidence[name] = {"address": str(candidate.address), "runtime_bytes": len(code), "runtime_sha256": hashlib.sha256(code).hexdigest(), "authenticated": True}
    book, board = candidates["VaultBook"], candidates["Switchboard"]
    verify_book(book, pool, retained)
    require(book.maxRegistryTimeLock() == p["VAULT_BOOK_MAX_REG_TIMELOCK"], "BOOK_MAX_DELAY")
    require(board.numAddrs() == 8 and board.getNumAddrs() == 7, "BOARD_COUNT")
    require(board.minRegistryTimeLock() == lo and board.maxRegistryTimeLock() == hi and board.registryChangeTimeLock() == lo, "BOARD_DELAY")
    rows = []
    for i, role in enumerate(("Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf"), 1):
        if i in REUSED_CONTROLLERS:
            name = REUSED_CONTROLLERS[i]
            controller = authenticate_controller(records[name + PREVIOUS_SUFFIX], name, HQ, lo, hi)
        else:
            controller = candidates["Switchboard" + role]
        require(address(board.getAddr(i)) == address(controller) and board.getRegId(controller.address) == i and board.isValidRegId(i), f"BOARD_ROW:{i}")
        rows.append(str(controller.address))
    require(tuple(getattr(candidates["Deleverage"], name)() for name in DL_PARAMS) == dl_params, "DELEVERAGE_PARAMS")
    return {"passed": True, "candidates": evidence, "retained_rows": retained, "switchboard_rows": rows,
            "deleverage_parameters": dict(zip(DL_PARAMS, dl_params)),
            "checks": ["manifest source/ABI/constructors/runtime", "historical Pool/RipeGov runtime pins", "HQ identities",
                       "legacy binding and all three row-1 identities", "retained rows 1-5 and absent/invalid 6-10",
                       "helper probes", "registry delays", "zero local and pending governance", "independent controller rows", "all eight Deleverage parameters"],
            "active_hq": [str(hq.getAddr(i)) for i in range(1, int(hq.numAddrs()))],
            "pending_hq_slot_8": list(hq.pendingAddrUpdate(8)),
            "active_candidate_slots": {str(i): address(hq.getAddr(i)) == address(candidates[name])
                                       for i, name in ((6, "Switchboard"), (8, "VaultBook"), (9, "AuctionHouse"), (18, "Deleverage"))}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--stager", required=True, help="Reviewed original candidate constructor authority")
    parser.add_argument("--block", type=int, required=True)
    parser.add_argument("--rpc-env", default="BASE_RPC_URL")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require_new_report(args.output)
    rpc = os.environ[args.rpc_env]
    w3 = Web3(Web3.HTTPProvider(rpc))
    require(w3.eth.chain_id == 8453, "CHAIN_ID")
    header = w3.eth.get_block(args.block)
    report = {"block": args.block, "block_hash": header.hash.hex(), "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
              "source": fingerprint(ROOT), "mode": "read-only fork", "live_transactions_sent": 0}
    try:
        with readonly_fork(rpc, args.block):
            report["verification"] = verify_candidates(json.loads(args.manifest.read_text())["contracts"], args.stager)
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        args.output.write_text(json.dumps(sanitize(report, rpc, ROOT), indent=2) + "\n")


if __name__ == "__main__":
    main()
