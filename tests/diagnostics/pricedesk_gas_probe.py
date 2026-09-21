"""Read-only Base fork probe for the simple immutable PriceDesk allowances.

Run from the repository root with PYTHONPATH=. and --help. All code/pointer
changes occur in Boa's local VM; the upstream transport rejects writes. This
checks contract behavior, not a deployment or activation procedure.
"""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

import boa
from boa.environment import Env
from boa.rpc import EthereumRPC
from eth_abi import decode
from eth_utils import keccak
from vyper.cli.vyper_json import compile_json

ROOT = Path(__file__).resolve().parents[2]
SUFFIX = "BaseUpgradeCandidate20260914"
ASSET = "0x99e65176F7FA8743E3fbaEF277d1Da448e361367"


class ReadOnlyRPC(EthereumRPC):
    ALLOWED = {
        "eth_chainId",
        "eth_getBlockByNumber",
        "eth_getCode",
        "eth_getBalance",
        "eth_getStorageAt",
        "eth_getTransactionCount",
        "eth_getProof",
        "eth_call",
    }

    def fetch(self, method, params):
        if method not in self.ALLOWED:
            raise RuntimeError("upstream writes forbidden")
        return super().fetch(method, params)

    def fetch_multi(self, payloads):
        payloads = list(payloads)
        if any(method not in self.ALLOWED for method, _ in payloads):
            raise RuntimeError("upstream writes forbidden")
        return super().fetch_multi(payloads)


def attach(records, name, target=None):
    return boa.loads_abi(json.dumps(records[name]["abi"]), name=name).at(
        target or records[name]["address"]
    )


def storage_layout(record):
    output = compile_json(copy.deepcopy(record["solc_json"]))
    errors = [e for e in output.get("errors", []) if e.get("severity") == "error"]
    assert not errors, errors
    return next(iter(output["contracts"][record["file"]].values()))["layout"][
        "storage_layout"
    ]


def set_pointer(hq, layout, slot, target):
    """Explicit local-only graph substitution, preserving all non-pointer state."""

    def write(name, key, value):
        base = layout["registry"][name]["slot"]
        key = int(str(key), 16) if isinstance(key, str) else key
        position = int.from_bytes(
            keccak(base.to_bytes(32, "big") + key.to_bytes(32, "big")), "big"
        )
        value = int(str(value), 16) if isinstance(value, str) else value
        boa.env.set_storage(hq.address, position, value)

    old = hq.getAddr(slot)
    write("addrInfo", slot, str(target))
    write("addrToRegId", str(old), 0)
    write("addrToRegId", str(target), slot)
    assert str(hq.getAddr(slot)).lower() == str(target).lower()
    assert hq.getRegId(target) == slot


def configure_local_graph(records):
    hq = attach(records, "RipeHq")
    layout = storage_layout(records["RipeHq"])
    setup = attach(records, "SwitchboardFoxtrotSetup" + SUFFIX)
    mc = attach(records, "MissionControl" + SUFFIX)
    set_pointer(hq, layout, 6, records["SwitchboardPopulated" + SUFFIX]["address"])
    while setup.initStep() < 5:
        setup.initConfig(sender=hq.governance(), gas=16_000_000)
    assert setup.initStep() == 5
    set_pointer(hq, layout, 5, mc.address)
    set_pointer(hq, layout, 7, records["PriceDeskBridge" + SUFFIX]["address"])
    return hq, mc, setup, layout


def cold():
    boa.env.evm.reset_access_counters()
    boa.env.evm.vm.state.clear_transient_storage()


def walk(computation):
    yield computation
    for child in computation.children:
        yield from walk(child)


def outcome(contract, call):
    result = {}
    try:
        result["value"] = call()
        result["passed"] = True
    except Exception:
        result["passed"] = False
    trace = contract._computation
    result["execution_gas"] = trace.get_gas_used()
    result["failures"] = [
        {
            "target": "0x" + c.msg.code_address.hex(),
            "selector": bytes(c.msg.data)[:4].hex(),
            "gas_limit": c.msg.gas,
            "gas_left": c.get_gas_remaining(),
            "error": str(c._error),
        }
        for c in walk(trace)
        if c.is_error
    ]
    return result


def install_desk(records, quote_gas, snapshot_gas):
    record = records["PriceDeskBridge" + SUFFIX]
    args = list(
        decode(
            [
                "address",
                "address",
                "address",
                "uint256",
                "uint256",
                "uint256",
                "uint256",
            ],
            bytes.fromhex(record["args"]),
        )
    )
    args[-2:] = [quote_gas, snapshot_gas]
    desk = boa.load(str(ROOT / "contracts/registries/PriceDesk.vy"), *args)
    assert desk.compiler_data.storage_layout["storage_layout"] == storage_layout(record)
    # Local code substitution retains actual source/config/token-scale storage.
    boa.env.set_code(record["address"], boa.env.get_code(desk.address))
    desk = desk.deployer.at(record["address"])
    assert desk.PRICE_SOURCE_PRICE_GAS() == quote_gas
    assert desk.PRICE_SOURCE_SNAPSHOT_GAS() == snapshot_gas
    return desk


def probe(records, allowances):
    hq, mc, setup, _ = configure_local_graph(records)
    results = []
    for allowance in allowances:
        desk = install_desk(records, allowance, 1_500_000)
        row = {
            "quote_allowance": allowance,
            "runtime_sha256": hashlib.sha256(
                boa.env.get_code(desk.address)
            ).hexdigest(),
        }
        cold()
        row.update(outcome(desk, lambda: desk.getPrice(ASSET, True, gas=16_000_000)))
        results.append(row)
        print(json.dumps(row), flush=True)
    snapshots = []
    source = attach(records, "UndyVaultPrices", desk.getAddr(8))
    config = source.priceConfigs(ASSET)
    for allowance in allowances:
        desk = install_desk(records, 3_000_000, allowance)
        before = list(source.priceConfigs(ASSET)[7])
        cold()
        with boa.env.anchor():
            boa.env.time_travel(seconds=int(config[3]) + 1)
            row = {"snapshot_allowance": allowance, "before": before}
            row.update(
                outcome(
                    desk,
                    lambda: desk.addPriceSnapshot(
                        ASSET, sender=hq.getAddr(17), gas=16_000_000
                    ),
                )
            )
            row["after"] = list(source.priceConfigs(ASSET)[7])
            row["advanced"] = row["after"] != before
            row["call_succeeded"] = row.pop("passed")
            row["passed"] = (
                row["call_succeeded"] and row.get("value") is True and row["advanced"]
            )
            snapshots.append(row)
            print(json.dumps(row), flush=True)
    return {
        "scope": "local source/configuration diagnostic; no production activation proof",
        "local_overrides": [
            "HQ slots 5,6,7",
            "candidate MC configured with recorded Defaults",
            "PriceDesk runtime; unchanged registry and token-scale storage",
        ],
        "asset": ASSET,
        "price_config": list(mc.getPriceConfig()),
        "quotes": results,
        "snapshots": snapshots,
        "source_sha256": hashlib.sha256(
            (ROOT / "contracts/registries/PriceDesk.vy").read_bytes()
        ).hexdigest(),
        "price_sources": [
            {
                "id": i,
                "address": str(desk.getAddr(i)),
                "runtime_sha256": hashlib.sha256(
                    boa.env.get_code(desk.getAddr(i))
                ).hexdigest(),
            }
            for i in range(1, desk.numAddrs())
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block", type=int)
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Read-only Base manifest containing the recorded MC/setup/source dependencies",
    )
    parser.add_argument("--rpc-env", default="BASE_RPC_URL")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--allowances",
        type=int,
        nargs="+",
        default=[1_500_000, 2_000_000, 3_000_000, 4_000_000, 6_000_000],
    )
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists")
    boa.interpret.set_cache_dir(str(args.output.parent / ".boa-cache"))
    rpc = ReadOnlyRPC(os.environ.get(args.rpc_env, "https://mainnet.base.org"))
    block = rpc.fetch(
        "eth_getBlockByNumber", [hex(args.block) if args.block else "finalized", False]
    )
    assert int(rpc.fetch("eth_chainId", []), 16) == 8453
    env = Env()
    env.fork_rpc(rpc, block_identifier=int(block["number"], 16))
    records = json.loads(args.manifest.read_text())["contracts"]
    with boa.set_env(env):
        result = probe(records, args.allowances)
    result.update(
        block=int(block["number"], 16),
        block_hash=block["hash"],
        live_transactions=0,
        manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
    )
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
