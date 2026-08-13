"""Prove a generated defaults contract reproduces the live deployment.

prepare_defaults.py reads the live values and writes them into a contract.
This closes the loop: it forks the network at the snapshot block, deploys that
contract, builds a REPLACEMENT MissionControl against it, and then diffs every
value the replacement came up holding against the live one -- including the
state MissionControl derives rather than copies, like asset index order and
the points allocation totals.

    python scripts/verify_defaults.py --network base-mainnet

With no --block-number it verifies at the block pinned in the generated file's
provenance header, so it checks the same snapshot that was reviewed. A
mismatch exits 1 and prints the field.

What this cannot prove is the state Defaults has no slot for. userConfig and
userDelegation are per-user and do not survive the redeploy at all; see the
coverage report prepare_defaults.py prints.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=False)
except ImportError:
    pass

import os

from scripts.prepare_defaults import NETWORKS, DEFAULT_NETWORK, Network

MISSION_CONTROL_SOURCE = "contracts/data/MissionControl.vy"
SNAPSHOT_BLOCK_RE = re.compile(r"^#\s+snapshot block:\s*(\d+)\s*$", re.MULTILINE)

# Read straight off the live contract; every one of these is either copied
# from defaults or derived from them at construction.
SCALAR_GETTERS = (
    "genConfig",
    "genDebtConfig",
    "hrConfig",
    "ripeBondConfig",
    "rewardsConfig",
    "underscoreRegistry",
    "trainingWheels",
    "shouldCheckLastTouch",
    "numAssets",
    "numLiteSigners",
    "totalPointsAllocs",
    "getPriorityLiqAssetVaults",
    "getPriorityStabVaults",
    "getPriorityPriceSourceIds",
)
PER_ASSET_GETTERS = ("assetConfig", "ripeGovVaultConfig", "indexOfAsset")


class VerificationError(RuntimeError):
    """The generated defaults cannot be shown to reproduce the live state."""


def _normalize(value):
    """Flatten boa and web3 struct returns into plain comparable data."""
    if isinstance(value, str):
        return value.lower() if value.startswith("0x") else value
    if isinstance(value, bool) or isinstance(value, int):
        return value
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if hasattr(value, "_asdict"):
        return [_normalize(item) for item in value]
    if hasattr(value, "__dict__"):
        return [_normalize(item) for item in vars(value).values()]
    return value


def _pinned_block(source: str, defaults_path: Path) -> int:
    match = SNAPSHOT_BLOCK_RE.search(source)
    if not match:
        raise VerificationError(
            f"{defaults_path} has no snapshot block in its provenance header; "
            "pass --block-number explicitly"
        )
    return int(match.group(1))


def _manifest_address(manifest: dict, name: str) -> str:
    from web3 import Web3

    entry = manifest.get(name)
    if not isinstance(entry, dict) or not isinstance(entry.get("address"), str):
        raise VerificationError(f"manifest is missing {name}.address")
    return Web3.to_checksum_address(entry["address"])


def verify(network: Network, defaults_path: Path, block_number: int | None) -> int:
    import boa
    from web3 import Web3

    rpc = os.environ.get(network.rpc_env)
    if not rpc:
        raise VerificationError(f"{network.rpc_env} is not set (put it in .env).")
    if not defaults_path.exists():
        raise VerificationError(
            f"{defaults_path} does not exist; run prepare_defaults.py first"
        )

    source = defaults_path.read_text()
    block = block_number if block_number is not None else _pinned_block(
        source, defaults_path
    )

    manifest = json.loads(network.manifest_path.read_text())["contracts"]
    live_addr = _manifest_address(manifest, "MissionControl")
    hq_addr = _manifest_address(manifest, "RipeHq")

    w3 = Web3(Web3.HTTPProvider(rpc))
    chain_id = w3.eth.chain_id
    if chain_id != network.chain_id:
        raise VerificationError(
            f"expected {network.display_name} chain id {network.chain_id}, "
            f"got {chain_id!r}"
        )
    live = w3.eth.contract(address=live_addr, abi=manifest["MissionControl"]["abi"])

    def live_call(name, *args):
        return getattr(live.functions, name)(*args).call(block_identifier=block)

    print(
        f"forking {network.display_name} at block {block} to rebuild "
        f"MissionControl from {defaults_path.name}",
        file=sys.stderr,
    )
    boa.fork(rpc, block_identifier=block)
    defaults = boa.load(str(defaults_path))
    replacement = boa.load(MISSION_CONTROL_SOURCE, hq_addr, defaults.address)

    mismatches: list[tuple[str, object, object]] = []
    compared = 0

    def compare(label, got, want):
        nonlocal compared
        compared += 1
        if _normalize(got) != _normalize(want):
            mismatches.append((label, _normalize(got), _normalize(want)))

    for name in SCALAR_GETTERS:
        compare(name, getattr(replacement, name)(), live_call(name))

    num_assets = live_call("numAssets")
    assets = [live_call("assets", i) for i in range(1, num_assets)]
    assets = [a for a in assets if int(a, 16) != 0]
    for index, asset in enumerate(assets, start=1):
        # Index order matters: the replacement rebuilds it from the order the
        # defaults list the assets in, not from the live indices.
        compare(f"assets({index})", replacement.assets(index), asset)
        for name in PER_ASSET_GETTERS:
            compare(
                f"{name}({asset})",
                getattr(replacement, name)(asset),
                live_call(name, asset),
            )

    for i in range(1, live_call("numLiteSigners")):
        signer = live_call("liteSigners", i)
        compare(f"liteSigners({i})", replacement.liteSigners(i), signer)
        compare(
            f"canPerformLiteAction({signer})",
            replacement.canPerformLiteAction(signer),
            live_call("canPerformLiteAction", signer),
        )

    print(f"compared {compared} live values across {len(assets)} assets")
    if mismatches:
        print(f"\n{len(mismatches)} MISMATCH(ES):", file=sys.stderr)
        for label, got, want in mismatches:
            print(
                f"\n  {label}\n    replacement: {got}\n    live:        {want}",
                file=sys.stderr,
            )
        return 1
    print(
        f"a replacement MissionControl built from {defaults_path.name} comes up "
        f"matching live {network.display_name} at block {block}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--network",
        default=DEFAULT_NETWORK.key,
        choices=sorted(NETWORKS),
        help="Deployed network to verify against.",
    )
    parser.add_argument(
        "--block-number",
        type=int,
        help="Defaults to the block pinned in the generated file's header.",
    )
    parser.add_argument(
        "--defaults",
        type=Path,
        help="Verify a contract other than the network's default target.",
    )
    args = parser.parse_args()

    network = NETWORKS[args.network]
    defaults_path = args.defaults or network.target_path
    try:
        return verify(network, defaults_path, args.block_number)
    except VerificationError as exc:
        print(f"verification failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
