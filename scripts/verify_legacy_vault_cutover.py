"""Read-only, pinned-block checks for the retained-only compatibility candidates.

Run with python -m scripts.verify_legacy_vault_cutover --help. This module has
no NetworkEnv, wallet or broadcast path. --replay-staging explicitly deploys
only into a disposable local fork to verify candidates that are not live.
The selected historical block requires an archive-capable Base RPC.
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
    authenticate_controller, REUSED_CONTROLLERS, PREVIOUS_SUFFIX, HQ_SLOTS,
    retained_rows, pending_actions, verify_registry_pending, verify_foxtrot_setup,
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


def verify_candidates(records, stager, baseline, expected_phase):
    """Checks active fork state; call independently before any simulation writes."""
    p = PARAMS["base"]
    require(address(records["RipeHq"]["address"]) == HQ, "WRONG_HQ")
    require(address(records["StabilityPool"]["address"]) == POOL, "WRONG_POOL")
    require(expected_phase == "staged", "UNSUPPORTED_PHASE")
    require(baseline["schema"] == "legacy-vault-pre-stage-v1", "BASELINE_SCHEMA")
    reference = baseline["contracts"]
    require(address(reference["RipeHq"]["address"]) == HQ, "BASELINE_HQ")
    for name, record in reference.items():
        code = boa.env.get_code(record["address"])
        require(bool(code) and hashlib.sha256(code).hexdigest() == baseline["runtime_sha256"][name], "BASELINE_RUNTIME:" + name)
    for name in (*RETAINED, "MissionControl" + PREVIOUS_SUFFIX, "DefaultsBaseLive" + PREVIOUS_SUFFIX,
                 *(name + PREVIOUS_SUFFIX for name in REUSED_CONTROLLERS.values())):
        require(address(records[name]["address"]) == address(reference[name]["address"]), "RECORDED_ADDRESS:" + name)
    hq, pool = attach(reference, "RipeHq"), attach(reference, "StabilityPool")
    for slot in HQ_SLOTS:
        entry = baseline["hq_slots"][str(slot)]
        require(address(hq.getAddr(slot)) == address(entry["address"]), "PHASE_STAGED_SLOT:" + str(slot))
        require(hashlib.sha256(boa.env.get_code(entry["address"])).hexdigest() == entry["runtime_sha256"], "ACTIVE_RUNTIME:" + str(slot))
    pending = pending_actions(hq, HQ_SLOTS)
    for slot, state in pending.items():
        reviewed = baseline["hq_pending"][slot]
        require(reviewed["disposition"] in ("require_empty", "hold_no_activation"), "PENDING_DISPOSITION:" + slot)
        require(state == {key: reviewed[key] for key in ("update", "disable")}, "HQ_PENDING_DRIFT:" + slot)
        if reviewed["disposition"] == "require_empty":
            require(state == {"update": [ZERO, 0, 0], "disable": [0, 0]}, "HQ_PENDING_NOT_EMPTY:" + slot)
    active_book = attach(reference, "VaultBook", baseline["hq_slots"]["8"]["address"])
    active_rows = retained_rows(active_book)
    require(active_rows == baseline["retained_rows"], "ACTIVE_ROWS_DRIFT")
    retained = [records[name]["address"] for name in RETAINED]
    require(address(pool.getRipeHq()) == HQ, "POOL_HQ")
    # Immutable historical sources have separate authenticated fixture pins.
    provenance = json.loads((ROOT / "tests/fixtures/legacy_pool/provenance.json").read_text())
    for name, pin in (("StabilityPool", "pool"), ("RipeGov", "ripe_gov")):
        code = boa.env.get_code(records[name]["address"])
        require(code[-32:] == int(HQ, 16).to_bytes(32, "big"), "RETAINED_HQ_IMMUTABLE:" + name)
        canonical = code[:-32] + bytes.fromhex(provenance[pin]["immutable_word"])
        require(hashlib.sha256(canonical).hexdigest() == provenance[pin]["deployed_sha256"], "RETAINED_RUNTIME:" + name)
    active_dl = attach(reference, "Deleverage", baseline["hq_slots"]["18"]["address"])
    require([getattr(active_dl, name)() for name in DL_PARAMS[:4]] == baseline["inherited_deleverage"], "ACTIVE_DELEVERAGE_DRIFT")
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
    require(active_rows == [address(v) for v in retained], "ACTIVE_CANDIDATE_ROWS")
    verify_book(book, pool, retained)
    book_pending = verify_registry_pending(book, range(1, 6))
    board_pending = verify_registry_pending(board, range(1, 8))
    require(book.maxRegistryTimeLock() == p["VAULT_BOOK_MAX_REG_TIMELOCK"], "BOOK_MAX_DELAY")
    require(board.numAddrs() == 8 and board.getNumAddrs() == 7, "BOARD_COUNT")
    require(board.minRegistryTimeLock() == lo and board.maxRegistryTimeLock() == hi and board.registryChangeTimeLock() == lo, "BOARD_DELAY")
    rows = []
    for i, role in enumerate(("Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf"), 1):
        if i in REUSED_CONTROLLERS:
            name = REUSED_CONTROLLERS[i]
            controller = authenticate_controller(records[name + PREVIOUS_SUFFIX], name, HQ, lo, hi)
            if i == 6:
                foxtrot = verify_foxtrot_setup(controller, reference["MissionControl" + PREVIOUS_SUFFIX]["address"],
                                              reference["DefaultsBaseLive" + PREVIOUS_SUFFIX]["address"])
        else:
            controller = candidates["Switchboard" + role]
        require(address(board.getAddr(i)) == address(controller) and board.getRegId(controller.address) == i and board.isValidRegId(i), f"BOARD_ROW:{i}")
        rows.append(str(controller.address))
    require(tuple(getattr(candidates["Deleverage"], name)() for name in DL_PARAMS) == dl_params, "DELEVERAGE_PARAMS")
    require(all(address(hq.getAddr(i)) != address(candidates[name]) for i, name in
                ((6, "Switchboard"), (8, "VaultBook"), (9, "AuctionHouse"), (18, "Deleverage"))), "CANDIDATE_ALREADY_ACTIVE")
    return {"passed": True, "expected_phase": expected_phase,
            "active_retained_rows": active_rows, "candidate_retained_rows": [address(book.getAddr(i)) for i in range(1, 6)],
            "hq_pending": pending, "pending_dispositions": baseline["hq_pending"], "foxtrot_setup": foxtrot,
            "candidate_pending": {"VaultBook": book_pending, "Switchboard": board_pending}, "candidates": evidence, "retained_rows": retained, "switchboard_rows": rows,
            "deleverage_parameters": dict(zip(DL_PARAMS, dl_params)),
            "checks": ["manifest source/ABI/constructors/runtime", "historical Pool/RipeGov runtime pins", "HQ identities",
                       "legacy binding and all three row-1 identities", "retained rows 1-5 and absent/invalid 6-10",
                       "helper probes", "registry delays", "zero local and pending governance", "independent controller rows", "all eight Deleverage parameters"],
            "active_hq": [str(hq.getAddr(i)) for i in range(1, int(hq.numAddrs()))],
            "pending_hq_slot_8": list(hq.pendingAddrUpdate(8)),
            "active_candidate_slots": {str(i): address(hq.getAddr(i)) == address(candidates[name])
                                       for i, name in ((6, "Switchboard"), (8, "VaultBook"), (9, "AuctionHouse"), (18, "Deleverage"))}}


def load_inputs(baseline_path, baseline_sha256, manifest_path):
    baseline_path, manifest_path = Path(baseline_path).resolve(), Path(manifest_path).resolve()
    require(baseline_path != manifest_path and not baseline_path.samefile(manifest_path), "BASELINE_SAME_FILE")
    baseline_bytes = baseline_path.read_bytes()
    require(hashlib.sha256(baseline_bytes).hexdigest() == baseline_sha256.lower(), "BASELINE_HASH")
    candidate_bytes = manifest_path.read_bytes()
    return json.loads(baseline_bytes), json.loads(candidate_bytes)["contracts"], {
        "baseline_manifest_path": str(baseline_path), "baseline_sha256": baseline_sha256.lower(),
        "candidate_manifest_path": str(manifest_path), "candidate_manifest_sha256": hashlib.sha256(candidate_bytes).hexdigest()}


def run_verification(manifest, baseline_manifest, baseline_sha256, stager, expected_phase, block, rpc, output, replay_staging=False):
    require_new_report(output)
    report = {"passed": False, "block": block, "mode": "read-only fork", "live_transactions_sent": 0,
              "expected_phase": expected_phase, "source": fingerprint(ROOT)}
    try:
        baseline, records, inputs = load_inputs(baseline_manifest, baseline_sha256,
            ROOT / "migration_history/base-mainnet/v1/current-manifest.json" if replay_staging else manifest)
        report.update(inputs)
        if replay_staging:
            require(not report["source"]["dirty"], "CLEAN_CHECKOUT_REQUIRED")
            require(not Path(output).resolve().is_relative_to(ROOT), "EVIDENCE_OUTPUT_MUST_BE_OUTSIDE_CHECKOUT")
            require(baseline["block"] == block, "BASELINE_BLOCK")
        w3 = Web3(Web3.HTTPProvider(rpc))
        require(w3.eth.chain_id == 8453, "CHAIN_ID")
        report["block_hash"] = w3.eth.get_block(block).hash.hex()
        if replay_staging:
            from scripts.base_legacy_compat_fork import staged_fork
            require(report["block_hash"] == baseline["block_hash"], "BASELINE_BLOCK_HASH")
            report["mode"] = "standalone verifier; replay production staging on independent read-only upstream local fork"
            with staged_fork(rpc, block, report) as (candidate_path, fork_stager):
                baseline, records, inputs = load_inputs(baseline_manifest, baseline_sha256, candidate_path)
                report.update(inputs)
                report["verification"] = verify_candidates(records, fork_stager, baseline, expected_phase)
        else:
            with readonly_fork(rpc, block):
                report["verification"] = verify_candidates(records, stager, baseline, expected_phase)
        if replay_staging:
            after = fingerprint(ROOT)
            require(after == report["source"], "QUALIFICATION_INPUT_DRIFT")
            report["source_after"] = {k: v for k, v in after.items() if k != "sha256"}
        report["passed"] = True
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        Path(output).write_text(json.dumps(sanitize(report, rpc, ROOT), indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--replay-staging", action="store_true", help="Verify fork-only candidates by replaying production staging on a clean local fork")
    parser.add_argument("--baseline-manifest", type=Path, required=True)
    parser.add_argument("--baseline-sha256", required=True)
    parser.add_argument("--expected-phase", choices=("staged",), required=True)
    parser.add_argument("--stager", help="Reviewed original candidate constructor authority")
    parser.add_argument("--block", type=int, required=True)
    parser.add_argument("--rpc-env", default="BASE_RPC_URL")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.replay_staging:
        require(args.manifest is None and args.stager is None, "REPLAY_INPUTS")
    else:
        require(args.manifest is not None and args.stager is not None, "VERIFIER_INPUTS")
    run_verification(args.manifest, args.baseline_manifest, args.baseline_sha256, args.stager,
                     args.expected_phase, args.block, os.environ[args.rpc_env], args.output, args.replay_staging)


if __name__ == "__main__":
    main()
