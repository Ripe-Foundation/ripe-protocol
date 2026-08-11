"""Generate DefaultsRobinhoodLive.vy from the live Robinhood deployment.

MissionControl copies its defaults into storage at construction, so a
REPLACEMENT MissionControl built against a stale defaults contract comes up
holding launch values and silently forgets everything governance changed
since. This pulls the current values off chain and writes them into the
contract, so what gets deployed is visible in a diff and reviewable before it
ships -- rather than being resolved at runtime.

    python scripts/prepare_defaults.py              # write the contract
    python scripts/prepare_defaults.py --check      # exit 1 if out of date
    python scripts/prepare_defaults.py --dry-run    # print, write nothing

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
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "contracts/config/DefaultsRobinhoodLive.vy"
MANIFEST = ROOT / "migration_history/robinhood-mainnet/v1/current-manifest.json"
ROBINHOOD_CHAIN_ID = 4663

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
# Regenerate with:  python scripts/prepare_defaults.py
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


def _require_robinhood_chain_id(chain_id: int) -> None:
    if chain_id != ROBINHOOD_CHAIN_ID:
        raise RuntimeError(
            "DEFAULTS_CHAIN_MISMATCH "
            f"expected={ROBINHOOD_CHAIN_ID} observed={chain_id}"
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


def build(w3, mc_addr: str, ledger_addr: str) -> str:
    from web3 import Web3

    mc_abi = _abi("contracts/data/MissionControl.vy")
    led_abi = _abi("contracts/data/Ledger.vy")
    mc = w3.eth.contract(address=Web3.to_checksum_address(mc_addr), abi=mc_abi)
    led = w3.eth.contract(address=Web3.to_checksum_address(ledger_addr), abi=led_abi)
    call = lambda c, n, *a: getattr(c.functions, n)(*a).call()

    manifest = json.loads(MANIFEST.read_text())["contracts"]
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
                label = manifest_name or _symbol(w3, addr) or "ADDRESS"
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
    out = [HEADER]

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
        sym = _symbol(w3, addr) or by_addr.get(addr.lower(), "")
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


def _symbol(w3, addr) -> str | None:
    from web3 import Web3
    try:
        raw = w3.eth.call({
            "to": Web3.to_checksum_address(addr),
            "data": Web3.keccak(text="symbol()")[:4],
        })
        if len(raw) > 64:
            length = int.from_bytes(raw[32:64], "big")
            return raw[64:64 + length].decode(errors="replace")
        return raw.rstrip(b"\x00").decode(errors="replace") or None
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
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
    manifest = json.loads(MANIFEST.read_text())["contracts"]
    # The URL carries a provider key, so it is never printed.
    chain_id = w3.eth.chain_id
    try:
        _require_robinhood_chain_id(chain_id)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(f"reading chain {chain_id} at block {w3.eth.block_number}")

    source = build(w3, manifest["MissionControl"]["address"],
                   manifest["Ledger"]["address"])

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
