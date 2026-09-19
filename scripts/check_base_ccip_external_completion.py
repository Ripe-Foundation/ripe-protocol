"""Read-only evidence for CCIP completed through the former migration system.

Prints JSON after the existing activation checker passes at a finalized Base pin.
Does not send transactions, edit manifests, or advance migration history.
Run: python -m scripts.check_base_ccip_external_completion
"""

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess

import boa
from dotenv import load_dotenv
from web3 import Web3

from scripts.utils import ccip, solidity
from scripts.utils.fork_reports import sanitize

ROOT = Path(__file__).resolve().parents[1]
POOLS = (
    ("RIPE", "RipeCcipBurnMintTokenPool", "RipeToken", False, True),
    ("GREEN", "GreenCcipBurnMintTokenPool", "GreenToken", True, False),
)


def plain(value):
    if isinstance(value, bytes):
        return "0x" + value.hex()
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return str(value)


def check(rpc):
    w3 = Web3(Web3.HTTPProvider(rpc))
    if w3.eth.chain_id != 8453:
        raise RuntimeError("WRONG_CHAIN")
    block = w3.eth.get_block("finalized")
    manifests, hashes, reads = {}, {}, []
    for chain in ("base-mainnet", "robinhood-mainnet"):
        path = ROOT / f"migration_history/{chain}/v1/current-manifest.json"
        content = path.read_bytes()
        manifests[chain] = json.loads(content)["contracts"]
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(content).hexdigest()
    for filename in ("scripts/utils/ccip.py", "config/Ccip.py", __file__):
        path = (ROOT / filename).resolve()
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()

    class Observed:
        def __init__(self, contract):
            self.contract, self.address = contract, contract.address

        def __getattr__(self, name):
            fn = getattr(self.contract, name)
            def read(*args):
                value = fn(*args)
                reads.append({"target": str(self.address), "method": name,
                              "args": plain(args), "result": plain(value)})
                return value
            return read

    class ReadOnlyMigration:
        def chain(self):
            return "base-mainnet"

        def get_address(self, name):
            return manifests["base-mainnet"][name]["address"]

        def get_address_on_chain(self, chain, name):
            return manifests[chain][name]["address"]

        def get_contract(self, name):
            entry = manifests["base-mainnet"][name]
            return Observed(boa.loads_abi(json.dumps(entry["abi"]), name=name).at(entry["address"]))

        def get_solidity_contract(self, name, source_file):
            return Observed(solidity.at(name, self.get_address(name), source_file))

    original_registry = ccip.token_admin_registry
    try:
        ccip.token_admin_registry = lambda chain: Observed(original_registry(chain))
        with boa.fork(rpc, block_identifier=block["number"]):
            ccip.require_mainnet_activation_finalized(
                ReadOnlyMigration(), POOLS, "RipeCcipBurnMintTokenPools.sol")
    finally:
        ccip.token_admin_registry = original_registry
    if w3.eth.get_block(block["number"])["hash"] != block["hash"]:
        raise RuntimeError("VERIFICATION_BLOCK_CHANGED")
    return {
        "kind": "external_completion_reconciliation", "chain_id": 8453,
        "block": block["number"], "block_hash": "0x" + bytes(block["hash"]).hex(),
        "finalized": True, "live_writes": False, "verification": "passed",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "input_sha256": hashes,
        "operator_attestation": "CCIP ran on the old migration system; operator requested recording completion.",
        "scope": "Current finalized activation state matches existing checker; not a claim these new migration bodies executed. Original transaction receipts are not reconstructed.",
        "reconciled_steps": ["2026082400", "2026082401"], "reads": reads,
    }


if __name__ == "__main__":
    load_dotenv(ROOT / ".env")
    rpc = os.environ["BASE_MAINNET_RPC_URL"]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            evidence = check(rpc)
        print(json.dumps(evidence))
    except Exception as exc:
        print(sanitize(str(exc), rpc, ROOT))
        raise SystemExit(1) from None
