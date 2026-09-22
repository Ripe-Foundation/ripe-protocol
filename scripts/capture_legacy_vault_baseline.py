"""Capture a pre-stage baseline for independent review; archive-capable Base RPC required.

Capturing is not approval. Record/review the printed SHA separately before using
this file as --baseline-manifest. Never capture from a post-staging manifest.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

import boa
from web3 import Web3

from scripts.utils.legacy_vault_compat import (
    PREVIOUS_SUFFIX, REUSED_CONTROLLERS, HQ_SLOTS, address, require, retained_rows, review_hq_pending,
)
from scripts.utils.readonly_fork import readonly_fork
from scripts.utils.fork_reports import require_new_report

ROLES = {5: "MissionControl", 6: "Switchboard", 8: "VaultBook", 9: "AuctionHouse", 18: "Deleverage"}
RETAINED = ("StabilityPool", "RipeGov", "SimpleErc20", "RebaseErc20", "Underscore Vault")


def attach(records, name, target=None):
    record = records[name]
    return boa.loads_abi(json.dumps(record["abi"]), name=name).at(target or record["address"])


def capture(records):
    hq = attach(records, "RipeHq")
    names = {"RipeHq", *RETAINED, *ROLES.values(), "MissionControl" + PREVIOUS_SUFFIX,
             "DefaultsBaseLive" + PREVIOUS_SUFFIX,
             *(name + PREVIOUS_SUFFIX for name in REUSED_CONTROLLERS.values())}
    baseline = {"schema": "legacy-vault-pre-stage-v1", "review_required": True,
                "contracts": {name: {"address": address(records[name]["address"]), "abi": records[name]["abi"]} for name in sorted(names)},
                "hq_slots": {}, "hq_pending": review_hq_pending(hq)}
    for slot in HQ_SLOTS:
        target = hq.getAddr(slot)
        code = boa.env.get_code(target)
        require(bool(code), "BASELINE_CODE:" + str(slot))
        baseline["hq_slots"][str(slot)] = {"role": ROLES[slot], "address": address(target),
                                           "runtime_sha256": hashlib.sha256(code).hexdigest()}
        baseline["contracts"][ROLES[slot]]["address"] = address(target)
    book = attach(baseline["contracts"], "VaultBook")
    baseline["retained_rows"] = retained_rows(book)
    for name, expected in zip(RETAINED, baseline["retained_rows"]):
        require(address(records[name]["address"]) == expected, "BASELINE_RETAINED_MANIFEST:" + name)
    baseline["runtime_sha256"] = {name: hashlib.sha256(boa.env.get_code(record["address"])).hexdigest()
                                  for name, record in baseline["contracts"].items()}
    dl = attach(baseline["contracts"], "Deleverage")
    baseline["inherited_deleverage"] = [getattr(dl, n)() for n in
        ("minDeleverageBps", "deleverageBuffer", "deleverageCooldown", "underscoreSafeSpreadBps")]
    return baseline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--block", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rpc-env", default="BASE_RPC_URL")
    args = parser.parse_args()
    require_new_report(args.output)
    rpc = os.environ[args.rpc_env]
    w3 = Web3(Web3.HTTPProvider(rpc))
    require(w3.eth.chain_id == 8453, "CHAIN_ID")
    header = w3.eth.get_block(args.block)
    with readonly_fork(rpc, args.block):
        result = capture(json.loads(args.manifest.read_text())["contracts"])
    result.update(block=args.block, block_hash=header.hash.hex(), source_manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
                  source_manifest_path=str(args.manifest.resolve()), live_transactions_sent=0)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
