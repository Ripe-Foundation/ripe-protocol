"""Read-only retained-pool diagnostics, keeper dry-run and receipt reconciliation.

Archive-capable Base RPC is required. No wallet or broadcast path exists. User
inventory must carry a pinned-block completeness attestation from its indexer.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

import boa
from eth_abi import encode, decode
from eth_utils import keccak
from web3 import Web3

from scripts.capture_legacy_vault_baseline import attach
from scripts.utils.legacy_vault_compat import ZERO, address, require
from scripts.utils.readonly_fork import readonly_fork
from scripts.utils.fork_reports import require_new_report, sanitize

READ_GAS = 8_000_000
DIAGNOSTIC_GAS = 12_000_000
BATCH_GAS = 12_800_000  # 20% remains in the separate 16M submission budget.
EVENT = keccak(text="DeleverageUser(address,address,uint256,uint256,uint256,uint256,bool)")
INTENTIONAL = {"executable", "rounding_residue", "paused", "unavailable_custody"}


def walk(computation):
    yield computation
    for child in computation.children:
        yield from walk(child)


def revert_reason(output, error):
    try:
        if output[:4] == keccak(text="Error(string)")[:4]:
            return decode(["string"], output[4:])[0]
    except Exception:
        pass  # Malformed revert payload remains a failed call, never decoder success.
    return str(error)


def probe(target, signature, types, values, gas=READ_GAS, outputs=("uint256",)):
    call = boa.env.execute_code(to_address=target, data=keccak(text=signature)[:4] + encode(types, values),
                                gas=gas, is_modifying=False, simulate=True)
    result = {"gas_limit": gas, "gas_used": call.get_gas_used(), "return_bytes": len(call.output)}
    if call.is_error:
        result["status"] = "gas_exhaustion" if any(c.is_error and c.get_gas_remaining() == 0 for c in walk(call)) else "revert"
        result["revert_data"] = bytes(call.output).hex()
        result["error"] = revert_reason(call.output, call.error)
        result["failed_calls"] = [{"target": "0x" + c.msg.code_address.hex(), "selector": bytes(c.msg.data)[:4].hex(),
                                   "gas_limit": c.msg.gas, "gas_left": c.get_gas_remaining()} for c in walk(call) if c.is_error]
    elif len(call.output) != 32 * len(outputs):
        result["status"] = "malformed_response"
    else:
        try:
            result["values"] = list(decode(outputs, call.output))
            result["status"] = "ok"
        except Exception:
            result["status"] = "malformed_response"
    return result


def classify(nav, value, traversal, custody, reserved, custody_value, paused, price_faults):
    if paused:
        expected = "paused"
    elif custody <= reserved:
        expected = "unavailable_custody"
    elif any(p["status"] == "gas_exhaustion" for p in (nav, value)):
        expected = "gas_exhaustion"
    elif any(p["status"] == "malformed_response" for p in (nav, value)):
        expected = "malformed_response"
    elif price_faults or not custody_value:
        expected = "missing_price"
    elif any(p["status"] != "ok" for p in (nav, value)):
        expected = "unexplained_read_failure"
    else:
        n, v = nav["values"][0], value["values"][0]
        raw = v * custody // custody_value if custody_value else 0
        expected = "executable" if n and v and raw and raw * custody_value // custody else "rounding_residue"
        if v * custody >= 2**256:
            expected = "arithmetic_overflow"
    if traversal["status"] != "ok":
        return "unexplained_traversal_failure"
    amount = traversal["values"][1]
    if (expected == "executable" and amount != nav["values"][0]) or (expected != "executable" and amount != 0):
        return "unexplained_traversal_mismatch"
    if expected == "executable" and any(p.get("gas_used", 0) > READ_GAS * 8 // 10 for p in (nav, value)):
        return "expensive_read"
    return expected


def diagnose(records, users, book_address):
    hq, pool = attach(records, "RipeHq"), attach(records, "StabilityPool")
    # The modern helper ABI is explicit even when the canonical manifest label
    # still refers to a historical book. Code binding is read back separately.
    book = boa.load_partial("contracts/registries/VaultBook.vy").at(book_address)
    require(address(book.LEGACY_POOL()) == address(pool), "MONITOR_BINDING")
    pd, mc = attach(records, "PriceDesk", hq.getAddr(7)), attach(records, "MissionControl", hq.getAddr(5))
    sg, green = address(hq.getAddr(2)), address(hq.getAddr(1))
    users = [address(u) for u in users]
    require(len(users) == len(set(users)) and ZERO not in users, "MONITOR_USER_INVENTORY")
    result = {"passed": False, "keeper_ready": False, "book": address(book), "active_book": address(hq.getAddr(8)),
              "price_desk": address(pd), "mission_control": address(mc), "price_config": list(mc.getPriceConfig()),
              "teller": address(hq.getAddr(17)), "deleverage": address(hq.getAddr(18)),
              "runtime_sha256": {name: hashlib.sha256(boa.env.get_code(target)).hexdigest() for name, target in
                                  (("book", book.address), ("price_desk", pd.address), ("mission_control", mc.address))},
              "users": users, "cohorts": [], "incidents": [], "live_transactions_sent": 0}
    for index in range(1, pool.numAssets()):
        asset = address(pool.vaultAssets(index))
        members = [(u, int(pool.userBalances(u, asset))) for u in users if pool.userBalances(u, asset)]
        if not members:
            continue
        custody_probe = probe(asset, "balanceOf(address)", ["address"], [pool.address])
        require(custody_probe["status"] == "ok", "MONITOR_CUSTODY_READ")
        custody = custody_probe["values"][0]
        reserved, paused = int(pool.totalClaimableBalances(asset)), bool(pool.isPaused())
        price_faults, prices = [], []
        priced = {asset}
        for i in range(1, pool.numClaimableAssets(asset)):
            claim = address(pool.claimableAssets(asset, i))
            if pool.claimableBalances(asset, claim):
                priced.add(claim)
        for claim in sorted(priced - {sg, green}):
            quote = probe(pd.address, "getPrice(address,bool)", ["address", "bool"], [claim, True])
            prices.append(dict(asset=claim, probe=quote))
            if quote["status"] != "ok" or quote["values"][0] == 0:
                price_faults.append(claim)
        if asset == sg:
            cv = probe(asset, "convertToAssets(uint256)", ["uint256"], [custody])
        elif asset == green:
            cv = {"status": "ok", "values": [custody]}
        else:
            cv = probe(pd.address, "getUsdValue(address,uint256,bool)", ["address", "uint256", "bool"], [asset, custody, True])
        if cv["status"] != "ok" or not cv["values"][0]:
            price_faults.append(asset)
        row = {"asset": asset, "custody": custody, "reserved": reserved, "paused": paused, "prices": prices,
               "claim_count": int(pool.numClaimableAssets(asset)) - 1, "custody_value_probe": cv,
               "price_review_required": [p["asset"] for p in prices if p["probe"].get("values") == [1]], "positions": []}
        for user, shares in members:
            reads = [probe(pool.address, getter + "(address,address)", ["address", "address"], [user, asset])
                     for getter in ("getTotalAmountForUser", "getTotalUserValue")]
            traversal = probe(book.address, "getDeleverageTraversalAsset(address,address,uint256,bool)",
                              ["address", "address", "uint256", "bool"], [user, pool.address, pool.indexOfUserAsset(user, asset), True],
                              gas=32_000_000, outputs=("address", "uint256"))
            reason = classify(*reads, traversal, custody, reserved, cv.get("values", [0])[0], paused, price_faults)
            if not paused and custody > reserved and cv["status"] in ("gas_exhaustion", "malformed_response"):
                reason = cv["status"]
            if reason == "executable" and cv.get("gas_used", 0) > READ_GAS * 8 // 10:
                reason = "expensive_read"
            if traversal.get("values", [asset])[0].lower() != asset:
                reason = "unexplained_asset_mismatch"
            diagnostic = {}
            for getter, read in zip(("getTotalAmountForUser", "getTotalUserValue"), reads):
                if read["status"] == "gas_exhaustion":
                    diagnostic[getter] = probe(pool.address, getter + "(address,address)", ["address", "address"], [user, asset], gas=DIAGNOSTIC_GAS)
            row["positions"].append({"user": user, "shares": shares, "classification": reason,
                                     "nav": reads[0], "user_value": reads[1], "traversal": traversal, "higher_gas_diagnostic": diagnostic})
        failures = [p for p in row["positions"] if p["classification"] not in INTENTIONAL]
        if row["price_review_required"]:
            result["incidents"].append({"cohort": asset, "reasons": ["one_wei_price_requires_review"],
                                       "assets": row["price_review_required"], "action": "review economic validity of quotes before keeper use"})
        if failures:
            result["incidents"].append({"cohort": asset, "affected_users": [p["user"] for p in failures],
                                        "reasons": sorted({p["classification"] for p in failures}), "action": "quarantine cohort and inspect strict probes"})
        result["cohorts"].append(row)
    result["passed"] = not result["incidents"]
    return result


def reconcile(intended, emitter, logs):
    """Require a positive-credit event for every unique intended user."""
    expected = {address(item["user"]): item for item in intended}
    require(len(expected) == len(intended) and bool(expected), "KEEPER_INTENDED_USERS")
    actual = {}
    for log in logs:
        if address(log["address"]) != address(emitter) or not log["topics"] or bytes(log["topics"][0]) != EVENT:
            continue
        require(len(log["topics"]) == 3, "KEEPER_EVENT_TOPICS")
        user = "0x" + bytes(log["topics"][1])[-20:].hex()
        target, buffered, credit, cleared, healthy = decode(["uint256", "uint256", "uint256", "uint256", "bool"], bytes(log["data"]))
        require(user not in actual, "KEEPER_DUPLICATE_EVENT:" + user)
        actual[user] = {"target": target, "credit": credit, "debt_cleared": cleared}
    require(set(actual) == set(expected), "KEEPER_OMITTED_OR_UNEXPECTED_USERS")
    for user, item in expected.items():
        require(actual[user]["target"] == int(item["target"]) and actual[user]["credit"] >= max(int(item["target"]), int(item.get("minimum_credit", item["target"]))) > 0
                and actual[user]["debt_cleared"] >= int(item["target"]),
                "KEEPER_INCOMPLETE_REPAYMENT:" + user)
    return actual


def dry_run(records, report, intended, keeper, gas_limit=BATCH_GAS):
    require(report["passed"] and report["book"] == report["active_book"], "KEEPER_PREFLIGHT_NOT_ACTIVE_OR_HEALTHY")
    require(0 < gas_limit <= BATCH_GAS, "KEEPER_GAS_BUDGET")
    require(all(address(i["user"]) in report["users"] for i in intended), "KEEPER_USER_NOT_PROBED")
    teller = attach(records, "Teller", report["teller"])
    with boa.env.anchor():
        teller.deleverageManyUsers([(i["user"], int(i["target"])) for i in intended], sender=keeper, gas=gas_limit)
        computation = teller._computation
        logs = [{"address": "0x" + a.hex(), "topics": [t.to_bytes(32, "big") for t in topics], "data": data}
                for a, topics, data in computation.get_log_entries()]
        report["reconciliation"] = reconcile(intended, report["deleverage"], logs)
        report["simulation"] = {"gas_limit": gas_limit, "gas_used": computation.get_gas_used(), "submission_budget": 16_000_000}
    report["intended"] = intended
    report["keeper"] = address(keeper)
    report["calldata_sha256"] = hashlib.sha256(keccak(text="deleverageManyUsers((address,uint256)[])")[:4] +
        encode(["(address,uint256)[]"], [[(i["user"], int(i["target"])) for i in intended]])).hexdigest()
    report["keeper_ready"] = True
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--users-json", type=Path)
    parser.add_argument("--intended-json", type=Path)
    parser.add_argument("--keeper")
    parser.add_argument("--book")
    parser.add_argument("--block", type=int)
    parser.add_argument("--preflight", type=Path, help="Previously saved preflight when reconciling a live receipt")
    parser.add_argument("--receipt-tx-hash")
    parser.add_argument("--rpc-env", default="BASE_RPC_URL")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require_new_report(args.output)
    rpc = os.environ.get(args.rpc_env, "")
    report = {"passed": False, "keeper_ready": False, "live_transactions_sent": 0}
    try:
        require(bool(rpc), "RPC_ENV_REQUIRED")
        w3 = Web3(Web3.HTTPProvider(rpc))
        require(w3.eth.chain_id == 8453, "CHAIN_ID")
        if args.receipt_tx_hash:
            require(args.preflight is not None, "KEEPER_PREFLIGHT_REQUIRED")
            previous = json.loads(args.preflight.read_text())
            require(previous["keeper_ready"], "KEEPER_PREFLIGHT_NOT_READY")
            receipt = w3.eth.get_transaction_receipt(args.receipt_tx_hash)
            require(receipt.status == 1 and address(receipt.to) == previous["teller"], "KEEPER_RECEIPT_STATUS_OR_TARGET")
            require(receipt.blockNumber >= previous["block"], "KEEPER_RECEIPT_BEFORE_PREFLIGHT")
            require(receipt.blockNumber <= w3.eth.get_block("finalized").number, "KEEPER_RECEIPT_NOT_FINALIZED")
            transaction = w3.eth.get_transaction(args.receipt_tx_hash)
            require(address(transaction["from"]) == previous["keeper"] and
                    hashlib.sha256(bytes(transaction["input"])).hexdigest() == previous["calldata_sha256"], "KEEPER_RECEIPT_INTENT")
            report.update(receipt_tx_hash=args.receipt_tx_hash, receipt_block=receipt.blockNumber,
                          reconciliation=reconcile(previous["intended"], previous["deleverage"], receipt.logs), passed=True)
        else:
            require(args.manifest is not None and args.users_json is not None and args.block is not None, "MONITOR_INPUTS")
            inventory = json.loads(args.users_json.read_text())
            require(inventory["complete_at_block"] == args.block and bool(inventory["attested_by"]), "MONITOR_COMPLETENESS_ATTESTATION")
            header = w3.eth.get_block(args.block)
            report.update(block=args.block, block_hash=header.hash.hex(), user_inventory_sha256=hashlib.sha256(args.users_json.read_bytes()).hexdigest(),
                          manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(), completeness_attestation=inventory["attested_by"])
            records = json.loads(args.manifest.read_text())["contracts"]
            with readonly_fork(rpc, args.block):
                hq = attach(records, "RipeHq")
                report.update(diagnose(records, inventory["users"], args.book or hq.getAddr(8)))
                if args.intended_json:
                    require(args.keeper is not None, "KEEPER_CALLER_REQUIRED")
                    dry_run(records, report, json.loads(args.intended_json.read_text()), args.keeper)
    except Exception as error:
        report.update(passed=False, keeper_ready=False, error=str(error))
    args.output.write_text(json.dumps(sanitize(report, rpc, Path(__file__).resolve().parents[1]), indent=2, default=str) + "\n")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
