"""Generate DefaultsRobinhoodLive.vy from the live Robinhood deployment.

MissionControl copies its defaults into storage at construction, so a
REPLACEMENT MissionControl built against a stale defaults contract comes up
holding launch values and silently forgets everything governance changed
since. This pulls the current values off chain and writes them into the
contract, so what gets deployed is visible in a diff and reviewable before it
ships -- rather than being resolved at runtime.

    python scripts/prepare_defaults.py --block-number N
    python scripts/prepare_defaults.py --block-number N --check
    python scripts/prepare_defaults.py --block-number N --dry-run

Run it, read the diff, then commit -- what gets deployed is reviewable.

This deliberately writes a SEPARATE contract rather than editing
DefaultsRobinhood.vy. That file is the launch config for a brand-new chain and
is governed by scripts/params/generate_robinhood_defaults.py, which forbids
address literals in it and derives a parameter ledger from it. The eight
assets governance registered after launch have no constructor bindings, so
writing them there would break that tooling.

The three ripeAvail* values live on Ledger rather than MissionControl and are
read from there, so a replacement Ledger inherits what has already been
emitted instead of resetting to the launch allocation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "contracts/config/DefaultsRobinhoodLive.vy"
MANIFEST = ROOT / "migration_history/robinhood-mainnet/v1/current-manifest.json"
EXPECTED_CHAIN_ID = 4663
REPOSITORY_ID = "ripe-foundation/ripe-protocol"
GENERATOR_ID = "scripts/prepare_defaults.py"

# The ABI carries field names but not struct type names, so they are named
# here. Keyed by getter for the top level, and by field name for nested ones.
TOP_STRUCT = {
    "genConfig": "cs.GenConfig",
    "genDebtConfig": "cs.GenDebtConfig",
    "ripeBondConfig": "cs.RipeBondConfig",
    "rewardsConfig": "cs.RipeRewardsConfig",
    "hrConfig": "cs.HrConfig",
    "assetConfig": "cs.AssetConfig",
    "ripeGovVaultConfig": "cs.RipeGovVaultConfig",
}
NESTED_STRUCT = {
    "genAuctionParams": "cs.AuctionParams",
    "customAuctionParams": "cs.AuctionParams",
    "debtTerms": "cs.DebtTerms",
    "lockTerms": "cs.LockTerms",
}

# Preferred constant names, so the common tokens read the same way they do
# elsewhere in the codebase instead of being named off their ERC20 symbol.
PREFERRED_NAMES = {
    "RipeToken": "RIPE_TOKEN",
    "GreenToken": "GREEN_TOKEN",
    "SavingsGreen": "SGREEN_TOKEN",
    "Contributor": "CONTRIB_TEMPLATE",
    "TrainingWheels": "TRAINING_WHEELS",
    "GreenUsdgPool": "GREEN_USDG_LP",
}

# The Uniswap pool reports the generic "UNI-V2" symbol and is not a manifest
# contract, so it would otherwise generate an opaque name.
NAME_OVERRIDES = {
    "0xba6f6cba1a4104000847d4fdccb676e99166cece": "RIPE_WETH_LP",
}

HEADER = '''# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

# GENERATED FILE -- do not edit by hand.
#
# Regenerate with:  python scripts/prepare_defaults.py --block-number {block_number}
#
# Snapshot provenance:
#   repository: {repository_id}
#   generator: {generator_id}
#   generator sha256: {generator_sha256}
#   manifest sha256: {manifest_sha256}
#   chain id: {chain_id}
#   snapshot block: {block_number}
#   snapshot block hash: {block_hash}
#   snapshot finality: verified against the provider finalized tag
#   MissionControl: {mission_control_address}
#   MissionControl code sha256: {mission_control_code_sha256}
#   Ledger: {ledger_address}
#   Ledger code sha256: {ledger_code_sha256}
#
# This is the defaults contract for REPLACING a MissionControl or Ledger that
# already exists. DefaultsRobinhood.vy remains the launch config for a
# brand-new chain; the two are not interchangeable.
#
# Every value below was read off the live Robinhood deployment, so this is a
# snapshot of what governance has configured rather than a set of launch
# decisions. MissionControl and Ledger copy these into storage at
# construction, which is the only reason a replacement for either can come up
# matching what is already running.
#
# Percentages are basis points (100_00 == 100%). Durations are in
# `block.number`, which on this Arbitrum L2 advances roughly every 12s -- it
# is the L1 ancestor estimate and repeats across child blocks, so it is NOT
# the ~100ms child cadence. The true child height is only reachable through
# ArbSys(0x64).arbBlockNumber().

implements: Defaults
from interfaces import Defaults
import interfaces.ConfigStructs as cs
'''


class SnapshotError(RuntimeError):
    """The requested live snapshot cannot be proven deterministic."""


@dataclass(frozen=True)
class SnapshotProvenance:
    chain_id: int
    block_number: int
    block_hash: str
    manifest_sha256: str
    generator_sha256: str
    mission_control_address: str
    mission_control_code_sha256: str
    ledger_address: str
    ledger_code_sha256: str

    def header(self) -> str:
        return HEADER.format(
            repository_id=REPOSITORY_ID,
            generator_id=GENERATOR_ID,
            generator_sha256=self.generator_sha256,
            manifest_sha256=self.manifest_sha256,
            chain_id=self.chain_id,
            block_number=self.block_number,
            block_hash=self.block_hash,
            mission_control_address=self.mission_control_address,
            mission_control_code_sha256=self.mission_control_code_sha256,
            ledger_address=self.ledger_address,
            ledger_code_sha256=self.ledger_code_sha256,
        )


def _hex_hash(value, field: str) -> str:
    if isinstance(value, str):
        text = value.removeprefix("0x")
        try:
            raw = bytes.fromhex(text)
        except ValueError as exc:
            raise SnapshotError(f"{field} is not a hex hash") from exc
    else:
        try:
            raw = bytes(value)
        except (TypeError, ValueError) as exc:
            raise SnapshotError(f"{field} is not a byte hash") from exc
    if len(raw) != 32:
        raise SnapshotError(f"{field} must be exactly 32 bytes")
    return "0x" + raw.hex()


def _block_identity(block, label: str) -> tuple[int, str]:
    if block is None:
        raise SnapshotError(f"provider returned no {label}")
    try:
        number = block["number"]
        block_hash = block["hash"]
    except (KeyError, TypeError) as exc:
        raise SnapshotError(f"{label} is missing number or hash") from exc
    if isinstance(number, bool) or not isinstance(number, int) or number < 0:
        raise SnapshotError(f"{label} number is invalid")
    return number, _hex_hash(block_hash, f"{label} hash")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _code_sha256(w3, address: str, block_number: int, label: str) -> str:
    try:
        code = bytes(w3.eth.get_code(address, block_identifier=block_number))
    except Exception as exc:
        raise SnapshotError(
            f"could not read {label} code at {address} from snapshot block "
            f"{block_number}"
        ) from exc
    if not code:
        raise SnapshotError(f"{label} has no code at snapshot block {block_number}")
    return _sha256(code)


def select_snapshot(
    w3,
    mc_addr: str,
    ledger_addr: str,
    *,
    block_number: int,
    manifest_bytes: bytes,
    generator_bytes: bytes,
) -> SnapshotProvenance:
    """Bind all reads to one provider-acknowledged finalized RH block."""
    from web3 import Web3

    if (
        isinstance(block_number, bool)
        or not isinstance(block_number, int)
        or block_number < 0
    ):
        raise SnapshotError("block number must be a non-negative integer")

    chain_id = w3.eth.chain_id
    if isinstance(chain_id, bool) or chain_id != EXPECTED_CHAIN_ID:
        raise SnapshotError(
            f"expected Robinhood chain id {EXPECTED_CHAIN_ID}, got {chain_id!r}"
        )

    try:
        finalized = w3.eth.get_block("finalized")
    except Exception as exc:
        raise SnapshotError("provider did not return an explicit finalized block") from exc
    finalized_number, _ = _block_identity(finalized, "finalized block")
    if block_number > finalized_number:
        raise SnapshotError(
            f"requested block {block_number} is newer than finalized block "
            f"{finalized_number}"
        )
    try:
        selected = w3.eth.get_block(block_number)
    except Exception as exc:
        raise SnapshotError(f"requested block {block_number} is unavailable") from exc
    selected_number, block_hash = _block_identity(selected, "snapshot block")
    if selected_number != block_number:
        raise SnapshotError(
            f"provider returned block {selected_number} for requested block {block_number}"
        )

    mission_control_address = Web3.to_checksum_address(mc_addr)
    ledger_address = Web3.to_checksum_address(ledger_addr)
    return SnapshotProvenance(
        chain_id=chain_id,
        block_number=block_number,
        block_hash=block_hash,
        manifest_sha256=_sha256(manifest_bytes),
        generator_sha256=_sha256(generator_bytes),
        mission_control_address=mission_control_address,
        mission_control_code_sha256=_code_sha256(
            w3, mission_control_address, block_number, "MissionControl"
        ),
        ledger_address=ledger_address,
        ledger_code_sha256=_code_sha256(
            w3, ledger_address, block_number, "Ledger"
        ),
    )


def verify_snapshot(w3, snapshot: SnapshotProvenance) -> None:
    """Fail if the selected block no longer resolves to the same hash."""
    if w3.eth.chain_id != snapshot.chain_id:
        raise SnapshotError("provider chain id changed during collection")
    try:
        finalized = w3.eth.get_block("finalized")
    except Exception as exc:
        raise SnapshotError(
            "provider no longer returns an explicit finalized block"
        ) from exc
    finalized_number, _ = _block_identity(finalized, "finalized block")
    if finalized_number < snapshot.block_number:
        raise SnapshotError(
            f"selected block {snapshot.block_number} is no longer finalized"
        )
    try:
        selected = w3.eth.get_block(snapshot.block_number)
    except Exception as exc:
        raise SnapshotError(
            f"selected block {snapshot.block_number} is no longer available"
        ) from exc
    number, block_hash = _block_identity(selected, "snapshot block")
    if number != snapshot.block_number or block_hash != snapshot.block_hash:
        raise SnapshotError(
            f"selected block {snapshot.block_number} changed during collection"
        )


def _abi(source: str) -> list:
    out = subprocess.run(
        ["vyper", "-f", "abi", source],
        capture_output=True, text=True, check=True, cwd=ROOT,
    ).stdout
    return json.loads(out)


def _outputs(abi: list, name: str) -> list:
    fn = next(x for x in abi if x.get("name") == name and x.get("type") == "function")
    return fn["outputs"]


class Renderer:
    """Turns decoded on-chain values into Vyper literals."""

    def __init__(self, addr_names: dict):
        self.addr_names = addr_names

    def address(self, value: str) -> str:
        if int(value, 16) == 0:
            return "empty(address)"
        return self.addr_names.get(value.lower(), self._checksum(value))

    @staticmethod
    def _checksum(value: str) -> str:
        from web3 import Web3
        return Web3.to_checksum_address(value)

    def scalar(self, value, comp: dict) -> str:
        kind = comp["type"]
        if kind == "address":
            return self.address(value)
        if kind == "bool":
            return "True" if value else "False"
        if kind.endswith("[]"):
            return "[" + ", ".join(str(v) for v in value) + "]"
        return str(value)

    def struct(self, value, comps: list, type_name: str, indent: int) -> str:
        pad = " " * indent
        inner = " " * (indent + 4)
        lines = [f"{type_name}("]
        for val, comp in zip(value, comps):
            if comp["type"] == "tuple":
                nested = NESTED_STRUCT[comp["name"]]
                rendered = self.struct(val, comp["components"], nested, indent + 4)
                lines.append(f"{inner}{comp['name']}={rendered},")
            else:
                lines.append(f"{inner}{comp['name']}={self.scalar(val, comp)},")
        lines.append(f"{pad})")
        return "\n".join(lines)


def build(
    w3,
    mc_addr: str,
    ledger_addr: str,
    snapshot: SnapshotProvenance,
    *,
    manifest_bytes: bytes,
) -> str:
    from web3 import Web3

    if _sha256(manifest_bytes) != snapshot.manifest_sha256:
        raise SnapshotError("manifest bytes do not match snapshot provenance")
    if Web3.to_checksum_address(mc_addr) != snapshot.mission_control_address:
        raise SnapshotError("MissionControl address does not match snapshot provenance")
    if Web3.to_checksum_address(ledger_addr) != snapshot.ledger_address:
        raise SnapshotError("Ledger address does not match snapshot provenance")

    mc_abi = _abi("contracts/data/MissionControl.vy")
    led_abi = _abi("contracts/data/Ledger.vy")
    mc = w3.eth.contract(address=Web3.to_checksum_address(mc_addr), abi=mc_abi)
    led = w3.eth.contract(address=Web3.to_checksum_address(ledger_addr), abi=led_abi)

    def call(contract, name, *args):
        return getattr(contract.functions, name)(*args).call(
            block_identifier=snapshot.block_number
        )

    manifest = json.loads(manifest_bytes)["contracts"]
    by_addr = {v["address"].lower(): k for k, v in manifest.items() if v.get("address")}

    # Assets first: their addresses decide which constants the file needs.
    num_assets = call(mc, "numAssets")
    assets = [call(mc, "assets", i) for i in range(1, num_assets)]
    assets = [a for a in assets if int(a, 16) != 0]

    usdg = call(mc, "ripeBondConfig")[0]
    weth = None
    liq_vaults = call(mc, "getPriorityLiqAssetVaults")
    if liq_vaults:
        weth = liq_vaults[0][1]  # WETH is the liquidation-priority asset

    # Every address the file needs a name for. All of them are live, so they
    # are emitted as constants and the contract takes no constructor at all.
    hr = call(mc, "hrConfig")
    wanted = list(assets) + [usdg, call(mc, "trainingWheels"), hr[0]]
    if weth:
        wanted.append(weth)

    addr_names: dict[str, str] = {}
    consts: list[tuple[str, str]] = []
    for addr in wanted:
        low = addr.lower()
        if low in addr_names or int(low, 16) == 0:
            continue
        if low in NAME_OVERRIDES:
            const = NAME_OVERRIDES[low]
        else:
            manifest_name = by_addr.get(low)
            if manifest_name in PREFERRED_NAMES:
                const = PREFERRED_NAMES[manifest_name]
            else:
                label = (
                    manifest_name
                    or _symbol(w3, addr, snapshot.block_number)
                    or "ADDRESS"
                )
                # split camelCase so GreenUsdgPool reads as GREEN_USDG_POOL
                spaced = "".join(
                    f"_{ch}" if i and ch.isupper() and not label[i - 1].isupper() else ch
                    for i, ch in enumerate(label)
                )
                const = "".join(
                    ch if ch.isalnum() else "_" for ch in spaced.upper()
                ).strip("_")
        base, n = const, 2
        while const in [c for c, _ in consts]:
            const = f"{base}_{n}"
            n += 1
        consts.append((const, Web3.to_checksum_address(addr)))
        addr_names[low] = const

    r = Renderer(addr_names)
    out = [snapshot.header()]

    out.append(
        "\n# addresses -- all read from the live deployment, so there is no\n"
        "# constructor and nothing to bind at deploy time\n"
    )
    for const, addr in consts:
        out.append(f"{const}: constant(address) = {addr}\n")

    def getter(name, ret, body):
        out.append(f"\n\n@view\n@external\ndef {name}() -> {ret}:\n    return {body}\n")

    for name in ("genConfig", "genDebtConfig"):
        comps = _outputs(mc_abi, name)[0]["components"]
        getter(name, TOP_STRUCT[name].replace("cs.", "cs."),
               r.struct(call(mc, name), comps, TOP_STRUCT[name], 4))

    for name in ("ripeAvailForRewards", "ripeAvailForHr", "ripeAvailForBonds"):
        getter(name, "uint256", str(call(led, name)))

    for name in ("ripeBondConfig", "rewardsConfig"):
        comps = _outputs(mc_abi, name)[0]["components"]
        getter(name, TOP_STRUCT[name],
               r.struct(call(mc, name), comps, TOP_STRUCT[name], 4))

    # ripe gov vault configs -- keyed by asset on chain, with no list to read
    gov_comps = _outputs(mc_abi, "ripeGovVaultConfig")[0]["components"]
    gov_entries = []
    for addr in assets:
        cfg = call(mc, "ripeGovVaultConfig", addr)
        if cfg[1] == 0:  # assetWeight; unset entries are all-zero
            continue
        gov_entries.append(
            "        cs.RipeGovVaultConfigEntry(\n"
            f"            asset={r.address(addr)},\n"
            f"            config={r.struct(cfg, gov_comps, 'cs.RipeGovVaultConfig', 12)},\n"
            "        ),"
        )
    out.append(
        "\n\n@view\n@external\ndef ripeGovVaultConfigs()"
        " -> DynArray[cs.RipeGovVaultConfigEntry, 5]:\n    return [\n"
        + "\n".join(gov_entries) + "\n    ]\n"
    )

    comps = _outputs(mc_abi, "hrConfig")[0]["components"]
    getter("hrConfig", "cs.HrConfig",
           r.struct(call(mc, "hrConfig"), comps, "cs.HrConfig", 4))

    getter("underscoreRegistry", "address", r.address(call(mc, "underscoreRegistry")))
    getter("trainingWheels", "address", r.address(call(mc, "trainingWheels")))
    getter("shouldCheckLastTouch", "bool",
           "True" if call(mc, "shouldCheckLastTouch") else "False")

    # asset configs
    ac_comps = _outputs(mc_abi, "assetConfig")[0]["components"]
    entries = []
    for addr in assets:
        cfg = call(mc, "assetConfig", addr)
        sym = (
            _symbol(w3, addr, snapshot.block_number)
            or by_addr.get(addr.lower(), "")
        )
        entries.append(
            f"        # {sym}\n"
            f"        cs.AssetConfigEntry(asset={r.address(addr)}, "
            f"config={r.struct(cfg, ac_comps, 'cs.AssetConfig', 8)}),"
        )
    out.append(
        "\n\n@view\n@external\ndef assetConfigs()"
        " -> DynArray[cs.AssetConfigEntry, 50]:\n    return [\n"
        + "\n".join(entries) + "\n    ]\n"
    )

    # priority lists
    for name, fn in (("priorityLiqAssetVaults", "getPriorityLiqAssetVaults"),
                     ("priorityStabVaults", "getPriorityStabVaults")):
        rows = [
            f"        cs.VaultLite(vaultId={v[0]}, asset={r.address(v[1])}),"
            for v in call(mc, fn)
        ]
        body = "[\n" + "\n".join(rows) + "\n    ]" if rows else "[]"
        out.append(
            f"\n\n@view\n@external\ndef {name}() -> DynArray[cs.VaultLite, 20]:\n"
            f"    return {body}\n"
        )

    ids = call(mc, "getPriorityPriceSourceIds")
    getter("priorityPriceSourceIds", "DynArray[uint256, 10]",
           "[" + ", ".join(str(i) for i in ids) + "]")

    num_signers = call(mc, "numLiteSigners")
    signers = [call(mc, "liteSigners", i) for i in range(1, num_signers)]
    signers = [s for s in signers if int(s, 16) != 0]
    body = "[\n" + "\n".join(
        f"        {Web3.to_checksum_address(s)}," for s in signers
    ) + "\n    ]" if signers else "[]"
    out.append(
        "\n\n@view\n@external\ndef liteSigners() -> DynArray[address, 10]:\n"
        f"    return {body}\n"
    )

    return "".join(out)


def _symbol(w3, addr, block_number: int) -> str | None:
    from web3 import Web3
    try:
        raw = w3.eth.call(
            {
                "to": Web3.to_checksum_address(addr),
                "data": Web3.keccak(text="symbol()")[:4],
            },
            block_identifier=block_number,
        )
        if len(raw) > 64:
            length = int.from_bytes(raw[32:64], "big")
            return raw[64:64 + length].decode(errors="replace")
        return raw.rstrip(b"\x00").decode(errors="replace") or None
    except Exception:
        # A symbol is presentation-only and some assets do not implement it.
        # Never retry the read without the selected block identifier.
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--block-number",
        required=True,
        type=int,
        help="Exact Robinhood snapshot block; it must already be finalized.",
    )
    parser.add_argument("--check", action="store_true",
                        help="Exit 1 if the contract is out of date.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rpc = os.environ.get("ROBINHOOD_MAINNET_RPC_URL")
    if not rpc:
        print("ROBINHOOD_MAINNET_RPC_URL is not set (put it in .env).",
              file=sys.stderr)
        return 2

    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(rpc))
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)["contracts"]
    mc_addr = manifest["MissionControl"]["address"]
    ledger_addr = manifest["Ledger"]["address"]
    try:
        snapshot = select_snapshot(
            w3,
            mc_addr,
            ledger_addr,
            block_number=args.block_number,
            manifest_bytes=manifest_bytes,
            generator_bytes=Path(__file__).read_bytes(),
        )
        # The URL carries a provider key, so it is never printed.
        print(
            f"reading chain {snapshot.chain_id} at snapshot block "
            f"{snapshot.block_number} ({snapshot.block_hash}); verified finalized"
        )
        source = build(
            w3,
            mc_addr,
            ledger_addr,
            snapshot,
            manifest_bytes=manifest_bytes,
        )
        verify_snapshot(w3, snapshot)
    except SnapshotError as exc:
        print(f"snapshot failed closed: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(source)
        return 0

    current = TARGET.read_text() if TARGET.exists() else ""
    if args.check:
        if current == source:
            print(f"{TARGET.relative_to(ROOT)} is up to date.")
            return 0
        print(f"{TARGET.relative_to(ROOT)} is STALE -- rerun without --check.",
              file=sys.stderr)
        return 1

    TARGET.write_text(source)
    print(f"wrote {TARGET.relative_to(ROOT)}"
          f" ({'unchanged' if current == source else 'CHANGED -- review the diff'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
