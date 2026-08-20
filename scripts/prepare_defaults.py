"""Generate a live-snapshot Defaults contract from a deployed Ripe network.

MissionControl copies its defaults into storage at construction, so a
REPLACEMENT MissionControl built against a stale defaults contract comes up
holding launch values and silently forgets everything governance changed
since. This pulls the current values off chain and writes them into the
contract, so what gets deployed is visible in a diff and reviewable before it
ships -- rather than being resolved at runtime.

    python scripts/prepare_defaults.py --network base-mainnet --block-number N
    python scripts/prepare_defaults.py --network base-mainnet --block-number N --check
    python scripts/prepare_defaults.py --network base-mainnet --block-number N --dry-run

Run it, read the diff, then commit -- what gets deployed is reviewable.

This deliberately writes a SEPARATE contract rather than editing the launch
defaults for the network. On Robinhood, DefaultsRobinhood.vy is the launch
config for a brand-new chain and is governed by
scripts/params/generate_robinhood_defaults.py, which forbids address literals
in it and derives a parameter ledger from it; assets governance registered
after launch have no constructor bindings, so writing them there would break
that tooling. On Base the same separation keeps DefaultsBase.vy -- which the
launch migrations still reference -- out of the redeploy path.

The three ripeAvail* values live on Ledger rather than MissionControl and are
read from there, so a replacement Ledger inherits what has already been
emitted instead of resetting to the launch allocation.

Not everything MissionControl holds can travel through Defaults. The
interface has no slot for userConfig or userDelegation, and the vault-id
fields added since the live deployments (coreRipeGovVaultId,
preferredStabVaultId) are set by the constructor rather than read from
defaults. The run prints an explicit accounting of what it carried and what
it could not, so the gap is a decision rather than a surprise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_ID = "ripe-foundation/ripe-protocol"
GENERATOR_ID = "scripts/prepare_defaults.py"
MISSION_CONTROL_SOURCE = "contracts/data/MissionControl.vy"
LEDGER_SOURCE = "contracts/data/Ledger.vy"

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

# Preferred constant names, so common tokens read the same way they do
# elsewhere instead of using the deterministic address-derived fallback.
# Keyed by the name the address carries in the network manifest.
COMMON_PREFERRED_NAMES = {
    "RipeToken": "RIPE_TOKEN",
    "GreenToken": "GREEN_TOKEN",
    "SavingsGreen": "SGREEN_TOKEN",
    "Contributor": "CONTRIB_TEMPLATE",
    "TrainingWheels": "TRAINING_WHEELS",
}

# Every DynArray bound the Defaults interface declares. A live deployment that
# outgrew one of these cannot be expressed as a defaults contract at all, so
# the run fails with the count rather than emitting a file that will not
# compile.
DEFAULTS_CAPS = {
    "assetConfigs": 50,
    "ripeGovVaultConfigs": 5,
    "priorityLiqAssetVaults": 20,
    "priorityStabVaults": 20,
    "priorityPriceSourceIds": 10,
    "liteSigners": 10,
}

# Every getter this generator calls. The deployed ABI recorded in the manifest
# must agree with the compiled source on each one; MissionControl has already
# gained getters since the live deployments were cut, and a silent signature
# change would mis-decode a config rather than fail.
MISSION_CONTROL_READS = (
    "assetConfig",
    "assets",
    "genConfig",
    "genDebtConfig",
    "getPriorityLiqAssetVaults",
    "getPriorityPriceSourceIds",
    "getPriorityStabVaults",
    "hrConfig",
    "liteSigners",
    "numAssets",
    "numLiteSigners",
    "rewardsConfig",
    "ripeBondConfig",
    "ripeGovVaultConfig",
    "shouldCheckLastTouch",
    "trainingWheels",
    "underscoreRegistry",
)
LEDGER_READS = (
    "ripeAvailForBonds",
    "ripeAvailForHr",
    "ripeAvailForRewards",
)


@dataclass(frozen=True)
class Network:
    """Everything that differs between one deployed network and another."""

    key: str
    display_name: str
    chain_id: int
    rpc_env: str
    manifest_path: Path
    target_path: Path
    launch_defaults: str
    cadence_note: str
    # address -> constant name, for addresses the manifest does not name.
    name_overrides: Mapping[str, str] = field(default_factory=dict)
    # address -> comment label. Robinhood leaves this empty so its committed
    # snapshot keeps regenerating byte for byte.
    label_overrides: Mapping[str, str] = field(default_factory=dict)
    extra_preferred_names: Mapping[str, str] = field(default_factory=dict)

    @property
    def preferred_names(self) -> Mapping[str, str]:
        return {**COMMON_PREFERRED_NAMES, **self.extra_preferred_names}


# Live Base assets are mostly third-party tokens the manifest never names, so
# their symbols are bound here rather than read from chain: a symbol() call
# would put provider availability into the generated bytes.
BASE_ASSET_NAMES = {
    "0xb33852cfd0c22647aac501a6af59bc4210a686bf": "UNDY_USD",
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": "USDC",
    "0x211cc4dd073734da055fbf44a2b4667d5e5fe5d2": "SUSDE",
    "0x1cb8dab80f19fc5aca06c2552aecd79015008ea8": "UNDY_EURC",
    "0x4200000000000000000000000000000000000006": "WETH",
    "0x02981db1a99a14912b204437e7a2e02679b57668": "UNDY_ETH",
    "0x2ae3f1ec7f1f5012cfeab0185bfc7aa3cf0dec22": "CB_ETH",
    "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf": "CB_BTC",
    "0x7fcd174e80f264448ebee8c88a7c4476aaf58ea6": "WSUPER_OETHB",
    "0x3fb0fc9d3ddd543ad1b748ed2286a022f4638493": "UNDY_BTC",
    "0x0b3e328455c4059eeb9e3f84b5543f74e24e7e1b": "VIRTUAL",
    "0x940181a94a35a4569e4529a3cdfb74e38fd98631": "AERO",
    "0x9b8df6e244526ab5f6e6400d331db28c8fdddb55": "USOL",
    "0xcbd06e5a2b0c65597161de254aa074e489deb510": "CB_DOGE",
    "0x96f1a7ce331f40afe866f3b707c223e377661087": "UNDY_AERO",
    "0xcbada732173e39521cdbe8bf59a6dc85a9fc7b8c": "CB_ADA",
    "0xcb585250f852c6c6bf90434ab21a00f02833a4af": "CB_XRP",
    "0xcb17c9db87b595717c857a08468793f5bab6445f": "CB_LTC",
    "0xacfe6019ed1a7dc6f7b508c02d1b04ec88cc21bf": "VVV",
    "0x4ed4e862860bed51a9570b96d89af5e1b0efefed": "DEGEN",
    "0xa88594d404727625a9437c3f886c7643872296ae": "WELL",
    "0x99e65176f7fa8743e3fbaef277d1da448e361367": "UNDY_USDC",
}

NETWORKS: Mapping[str, Network] = {
    "robinhood-mainnet": Network(
        key="robinhood-mainnet",
        display_name="Robinhood",
        chain_id=4663,
        rpc_env="ROBINHOOD_MAINNET_RPC_URL",
        manifest_path=(
            ROOT / "migration_history/robinhood-mainnet/v1/current-manifest.json"
        ),
        target_path=ROOT / "contracts/config/DefaultsRobinhoodLive.vy",
        launch_defaults="DefaultsRobinhood.vy",
        cadence_note=(
            "# Percentages are basis points (100_00 == 100%). Durations are in\n"
            "# `block.number`, which on this Arbitrum L2 advances roughly every 12s -- it\n"
            "# is the L1 ancestor estimate and repeats across child blocks, so it is NOT\n"
            "# the ~100ms child cadence. The true child height is only reachable through\n"
            "# ArbSys(0x64).arbBlockNumber()."
        ),
        # The Uniswap pool is not a manifest contract, so bind its known name
        # rather than using the deterministic address-derived fallback.
        name_overrides={
            "0xba6f6cba1a4104000847d4fdccb676e99166cece": "RIPE_WETH_LP",
        },
        extra_preferred_names={"GreenUsdgPool": "GREEN_USDG_LP"},
    ),
    "base-mainnet": Network(
        key="base-mainnet",
        display_name="Base",
        chain_id=8453,
        rpc_env="BASE_MAINNET_RPC_URL",
        manifest_path=(
            ROOT / "migration_history/base-mainnet/v1/current-manifest.json"
        ),
        target_path=ROOT / "contracts/config/DefaultsBaseLive.vy",
        launch_defaults="DefaultsBase.vy",
        cadence_note=(
            "# Percentages are basis points (100_00 == 100%). Durations are in\n"
            "# `block.number`, which on this OP-stack L2 advances every 2s, so a day is\n"
            "# 43_200 blocks."
        ),
        name_overrides=BASE_ASSET_NAMES,
        label_overrides=BASE_ASSET_NAMES,
        extra_preferred_names={
            "GreenPool": "GREEN_USDC_LP",
            "RipePoolAero": "RIPE_WETH_LP",
        },
    ),
}

# Kept for callers and tests that predate --network.
DEFAULT_NETWORK = NETWORKS["robinhood-mainnet"]
EXPECTED_CHAIN_ID = DEFAULT_NETWORK.chain_id

HEADER = '''# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026

# @version 0.4.3

# GENERATED FILE -- do not edit by hand.
#
# Regenerate with:  python scripts/prepare_defaults.py --network {network_key} --block-number {block_number}
#
# Snapshot provenance:
#   repository: {repository_id}
#   generator: {generator_id}
#   generator sha256: {generator_sha256}
#   manifest sha256: {manifest_sha256}
#   Vyper compiler: {compiler_version}
#   Vyper compiler identity sha256: {compiler_identity_sha256}
#   MissionControl compiler-input integrity: {mission_control_input_integrity}
#   MissionControl canonical ABI sha256: {mission_control_abi_sha256}
#   Ledger compiler-input integrity: {ledger_input_integrity}
#   Ledger canonical ABI sha256: {ledger_abi_sha256}
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
# already exists. {launch_defaults} remains the launch config for a
# brand-new chain; the two are not interchangeable.
#
# Every value below was read off the live {display_name} deployment, so this is a
# snapshot of what governance has configured rather than a set of launch
# decisions. MissionControl and Ledger copy these into storage at
# construction, which is the only reason a replacement for either can come up
# matching what is already running.
#
# MissionControl state that Defaults has no slot for -- userConfig and
# userDelegation -- does NOT survive the redeploy and is not represented here.
#
{cadence_note}

implements: Defaults
from interfaces import Defaults
import interfaces.ConfigStructs as cs
'''


class SnapshotError(RuntimeError):
    """The requested live snapshot cannot be proven deterministic."""


@dataclass(frozen=True)
class AbiInputs:
    mission_control_abi_bytes: bytes
    ledger_abi_bytes: bytes
    compiler_version: str
    mission_control_input_integrity: str
    ledger_input_integrity: str

    def parsed_abis(self) -> tuple[list, list]:
        try:
            mission_control = json.loads(self.mission_control_abi_bytes)
            ledger = json.loads(self.ledger_abi_bytes)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise SnapshotError("bound ABI bytes are not valid JSON") from exc
        if not isinstance(mission_control, list) or not isinstance(ledger, list):
            raise SnapshotError("bound ABI JSON must contain lists")
        canonical_mission_control = json.dumps(
            mission_control, sort_keys=True, separators=(",", ":")
        ).encode()
        canonical_ledger = json.dumps(
            ledger, sort_keys=True, separators=(",", ":")
        ).encode()
        if (
            self.mission_control_abi_bytes != canonical_mission_control
            or self.ledger_abi_bytes != canonical_ledger
        ):
            raise SnapshotError("bound ABI bytes are not canonical JSON")
        if not self.compiler_version:
            raise SnapshotError("Vyper compiler identity is empty")
        _require_digest(
            self.mission_control_input_integrity,
            "MissionControl compiler-input integrity",
        )
        _require_digest(
            self.ledger_input_integrity,
            "Ledger compiler-input integrity",
        )
        return mission_control, ledger


@dataclass(frozen=True)
class SnapshotProvenance:
    network_key: str
    chain_id: int
    block_number: int
    block_hash: str
    manifest_sha256: str
    generator_sha256: str
    compiler_version: str
    compiler_identity_sha256: str
    mission_control_input_integrity: str
    mission_control_abi_sha256: str
    ledger_input_integrity: str
    ledger_abi_sha256: str
    mission_control_address: str
    mission_control_code_sha256: str
    ledger_address: str
    ledger_code_sha256: str

    def header(self, network: Network) -> str:
        if network.key != self.network_key:
            raise SnapshotError("network does not match snapshot provenance")
        return HEADER.format(
            network_key=network.key,
            display_name=network.display_name,
            launch_defaults=network.launch_defaults,
            cadence_note=network.cadence_note,
            repository_id=REPOSITORY_ID,
            generator_id=GENERATOR_ID,
            generator_sha256=self.generator_sha256,
            manifest_sha256=self.manifest_sha256,
            compiler_version=self.compiler_version,
            compiler_identity_sha256=self.compiler_identity_sha256,
            mission_control_input_integrity=self.mission_control_input_integrity,
            mission_control_abi_sha256=self.mission_control_abi_sha256,
            ledger_input_integrity=self.ledger_input_integrity,
            ledger_abi_sha256=self.ledger_abi_sha256,
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


def _require_digest(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise SnapshotError(f"{field} must be 64 lowercase hex characters")
    try:
        raw = bytes.fromhex(value)
    except (TypeError, ValueError) as exc:
        raise SnapshotError(f"{field} is not a hex digest") from exc
    if len(raw) != 32:
        raise SnapshotError(f"{field} must be 64 lowercase hex characters")


def _manifest_addresses(manifest_bytes: bytes) -> tuple[str, str]:
    from web3 import Web3

    try:
        manifest = json.loads(manifest_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SnapshotError("manifest bytes are not valid JSON") from exc
    if not isinstance(manifest, dict) or not isinstance(
        manifest.get("contracts"), dict
    ):
        raise SnapshotError("manifest is missing the contracts object")

    addresses = []
    for name in ("MissionControl", "Ledger"):
        entry = manifest["contracts"].get(name)
        if not isinstance(entry, dict) or not isinstance(entry.get("address"), str):
            raise SnapshotError(f"manifest is missing {name}.address")
        try:
            addresses.append(Web3.to_checksum_address(entry["address"]))
        except (TypeError, ValueError) as exc:
            raise SnapshotError(f"manifest {name}.address is invalid") from exc
    return addresses[0], addresses[1]


def _validate_manifest_addresses(
    manifest_bytes: bytes, mc_addr: str, ledger_addr: str
) -> tuple[str, str]:
    from web3 import Web3

    manifest_mc, manifest_ledger = _manifest_addresses(manifest_bytes)
    try:
        supplied_mc = Web3.to_checksum_address(mc_addr)
        supplied_ledger = Web3.to_checksum_address(ledger_addr)
    except (TypeError, ValueError) as exc:
        raise SnapshotError("supplied MissionControl or Ledger address is invalid") from exc
    if supplied_mc != manifest_mc:
        raise SnapshotError("MissionControl address does not match manifest")
    if supplied_ledger != manifest_ledger:
        raise SnapshotError("Ledger address does not match manifest")
    return manifest_mc, manifest_ledger


def _function_signatures(abi: list, wanted: tuple[str, ...]) -> dict[str, str]:
    found: dict[str, str] = {}
    for entry in abi:
        if not isinstance(entry, dict) or entry.get("type") != "function":
            continue
        name = entry.get("name")
        if name not in wanted:
            continue
        found[name] = json.dumps(
            {"inputs": entry.get("inputs", []), "outputs": entry.get("outputs", [])},
            sort_keys=True,
            separators=(",", ":"),
        )
    return found


def _validate_deployed_abi_agreement(
    manifest_bytes: bytes, mission_control_abi: list, ledger_abi: list
) -> None:
    """Fail if the deployed ABI disagrees with the source this run decoded with.

    The compiled source is the redeploy target, not necessarily what is live.
    Reading the live contract through a drifted ABI would decode a config into
    the wrong fields, so every getter this generator calls is checked against
    the ABI the manifest recorded for the deployed contract.
    """
    try:
        manifest = json.loads(manifest_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SnapshotError("manifest bytes are not valid JSON") from exc
    contracts = manifest.get("contracts") if isinstance(manifest, dict) else None
    if not isinstance(contracts, dict):
        raise SnapshotError("manifest is missing the contracts object")

    for label, source_abi, reads in (
        ("MissionControl", mission_control_abi, MISSION_CONTROL_READS),
        ("Ledger", ledger_abi, LEDGER_READS),
    ):
        deployed_abi = contracts.get(label, {}).get("abi")
        if not isinstance(deployed_abi, list):
            raise SnapshotError(f"manifest is missing the deployed {label} ABI")
        deployed = _function_signatures(deployed_abi, reads)
        compiled = _function_signatures(source_abi, reads)
        for name in reads:
            if name not in compiled:
                raise SnapshotError(f"compiled {label} ABI is missing {name}")
            if name not in deployed:
                raise SnapshotError(f"deployed {label} has no {name} getter")
            if deployed[name] != compiled[name]:
                raise SnapshotError(
                    f"deployed {label}.{name} does not match the compiled source"
                )


def _require_cap(name: str, count: int) -> None:
    cap = DEFAULTS_CAPS[name]
    if count > cap:
        raise SnapshotError(
            f"live {name} holds {count} entries but Defaults caps it at {cap}"
        )


def _run_vyper(*args: str) -> bytes:
    try:
        return subprocess.run(
            ["vyper", *args],
            capture_output=True,
            check=True,
            cwd=ROOT,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SnapshotError(f"Vyper command failed: {' '.join(args)}") from exc


def _compile_abi_inputs(source: str) -> tuple[bytes, str]:
    output = _run_vyper("-p", ".", "-f", "abi,integrity", source)
    lines = output.splitlines()
    if len(lines) != 2:
        raise SnapshotError(f"Vyper did not emit ABI and integrity for {source}")
    try:
        abi = json.loads(lines[0])
        integrity = lines[1].decode().strip()
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SnapshotError(f"Vyper ABI or integrity is invalid for {source}") from exc
    if not isinstance(abi, list):
        raise SnapshotError(f"Vyper ABI is not a list for {source}")
    _require_digest(integrity, f"{source} compiler-input integrity")
    canonical_abi = json.dumps(
        abi, sort_keys=True, separators=(",", ":")
    ).encode()
    return canonical_abi, integrity


def load_abi_inputs() -> AbiInputs:
    """Compile each ABI once and bind its complete Vyper input closure."""
    try:
        compiler_version = _run_vyper("--version").decode().strip()
    except UnicodeDecodeError as exc:
        raise SnapshotError("Vyper compiler identity is not UTF-8") from exc
    mission_control_abi_bytes, mc_integrity = _compile_abi_inputs(
        MISSION_CONTROL_SOURCE
    )
    ledger_abi_bytes, ledger_integrity = _compile_abi_inputs(LEDGER_SOURCE)
    inputs = AbiInputs(
        mission_control_abi_bytes=mission_control_abi_bytes,
        ledger_abi_bytes=ledger_abi_bytes,
        compiler_version=compiler_version,
        mission_control_input_integrity=mc_integrity,
        ledger_input_integrity=ledger_integrity,
    )
    inputs.parsed_abis()
    return inputs


def _validate_abi_binding(
    abi_inputs: AbiInputs, snapshot: SnapshotProvenance
) -> tuple[list, list]:
    mission_control_abi, ledger_abi = abi_inputs.parsed_abis()
    observed = (
        abi_inputs.compiler_version,
        _sha256(abi_inputs.compiler_version.encode()),
        abi_inputs.mission_control_input_integrity,
        _sha256(abi_inputs.mission_control_abi_bytes),
        abi_inputs.ledger_input_integrity,
        _sha256(abi_inputs.ledger_abi_bytes),
    )
    expected = (
        snapshot.compiler_version,
        snapshot.compiler_identity_sha256,
        snapshot.mission_control_input_integrity,
        snapshot.mission_control_abi_sha256,
        snapshot.ledger_input_integrity,
        snapshot.ledger_abi_sha256,
    )
    if observed != expected:
        raise SnapshotError("ABI/compiler inputs do not match snapshot provenance")
    return mission_control_abi, ledger_abi


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
    abi_inputs: AbiInputs,
    network: Network = DEFAULT_NETWORK,
) -> SnapshotProvenance:
    """Bind all reads to one provider-acknowledged finalized block."""
    if (
        isinstance(block_number, bool)
        or not isinstance(block_number, int)
        or block_number < 0
    ):
        raise SnapshotError("block number must be a non-negative integer")

    mission_control_address, ledger_address = _validate_manifest_addresses(
        manifest_bytes, mc_addr, ledger_addr
    )
    mission_control_abi, ledger_abi = abi_inputs.parsed_abis()
    _validate_deployed_abi_agreement(manifest_bytes, mission_control_abi, ledger_abi)

    chain_id = w3.eth.chain_id
    if isinstance(chain_id, bool) or chain_id != network.chain_id:
        raise SnapshotError(
            f"expected {network.display_name} chain id {network.chain_id}, "
            f"got {chain_id!r}"
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

    return SnapshotProvenance(
        network_key=network.key,
        chain_id=chain_id,
        block_number=block_number,
        block_hash=block_hash,
        manifest_sha256=_sha256(manifest_bytes),
        generator_sha256=_sha256(generator_bytes),
        compiler_version=abi_inputs.compiler_version,
        compiler_identity_sha256=_sha256(abi_inputs.compiler_version.encode()),
        mission_control_input_integrity=(
            abi_inputs.mission_control_input_integrity
        ),
        mission_control_abi_sha256=_sha256(
            abi_inputs.mission_control_abi_bytes
        ),
        ledger_input_integrity=abi_inputs.ledger_input_integrity,
        ledger_abi_sha256=_sha256(abi_inputs.ledger_abi_bytes),
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


def _address_label(
    address: str,
    manifest_name: str | None,
    label_overrides: Mapping[str, str] = {},
) -> str:
    """Return a deterministic label without optional token metadata calls."""
    override = label_overrides.get(address.lower())
    return override or manifest_name or f"ADDRESS_{address.lower().removeprefix('0x')}"


@dataclass(frozen=True)
class BuildResult:
    """The generated source plus what the snapshot could and could not carry."""

    source: str
    counts: Mapping[str, int]

    def coverage_report(self, network: Network) -> str:
        carried = "\n".join(
            f"  {name}: {self.counts[name]}" for name in sorted(self.counts)
        )
        return (
            "carried into the defaults contract:\n"
            f"{carried}\n"
            "NOT carried -- Defaults has no slot for these, so a replacement\n"
            "MissionControl starts empty and they need their own migration step:\n"
            "  userConfig (per-user deposit/repay/bond permissions)\n"
            "  userDelegation (per-user, per-delegate action grants)\n"
            "set by the replacement MissionControl constructor rather than read\n"
            f"from live {network.display_name} (the deployed contract has no such getter):\n"
            "  preferredStabVaultId = 1, coreRipeGovVaultId = 2\n"
            "rebuilt from the asset configs above, so no action needed:\n"
            "  totalPointsAllocs, indexOfAsset, numAssets, isStabVaultId"
        )


def build(
    w3,
    mc_addr: str,
    ledger_addr: str,
    snapshot: SnapshotProvenance,
    *,
    manifest_bytes: bytes,
    abi_inputs: AbiInputs,
    network: Network = DEFAULT_NETWORK,
) -> BuildResult:
    from web3 import Web3

    manifest_mc, manifest_ledger = _validate_manifest_addresses(
        manifest_bytes, mc_addr, ledger_addr
    )
    if _sha256(manifest_bytes) != snapshot.manifest_sha256:
        raise SnapshotError("manifest bytes do not match snapshot provenance")
    if manifest_mc != snapshot.mission_control_address:
        raise SnapshotError("MissionControl address does not match snapshot provenance")
    if manifest_ledger != snapshot.ledger_address:
        raise SnapshotError("Ledger address does not match snapshot provenance")

    if network.key != snapshot.network_key:
        raise SnapshotError("network does not match snapshot provenance")

    mc_abi, led_abi = _validate_abi_binding(abi_inputs, snapshot)
    _validate_deployed_abi_agreement(manifest_bytes, mc_abi, led_abi)
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
    _require_cap("assetConfigs", len(assets))

    bond_asset = call(mc, "ripeBondConfig")[0]
    first_liq_asset = None
    liq_vaults = call(mc, "getPriorityLiqAssetVaults")
    _require_cap("priorityLiqAssetVaults", len(liq_vaults))
    if liq_vaults:
        first_liq_asset = liq_vaults[0][1]

    # Every address the file needs a name for. All of them are live, so they
    # are emitted as constants and the contract takes no constructor at all.
    hr = call(mc, "hrConfig")
    wanted = list(assets) + [bond_asset, call(mc, "trainingWheels"), hr[0]]
    if first_liq_asset:
        wanted.append(first_liq_asset)

    preferred_names = network.preferred_names
    addr_names: dict[str, str] = {}
    consts: list[tuple[str, str]] = []
    for addr in wanted:
        low = addr.lower()
        if low in addr_names or int(low, 16) == 0:
            continue
        manifest_name = by_addr.get(low)
        if manifest_name in preferred_names:
            const = preferred_names[manifest_name]
        elif low in network.name_overrides:
            const = network.name_overrides[low]
        else:
            label = _address_label(addr, manifest_name, network.label_overrides)
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
    out = [snapshot.header(network)]

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
    _require_cap("ripeGovVaultConfigs", len(gov_entries))
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
        label = _address_label(
            addr, by_addr.get(addr.lower()), network.label_overrides
        )
        entries.append(
            f"        # {label}\n"
            f"        cs.AssetConfigEntry(asset={r.address(addr)}, "
            f"config={r.struct(cfg, ac_comps, 'cs.AssetConfig', 8)}),"
        )
    out.append(
        "\n\n@view\n@external\ndef assetConfigs()"
        " -> DynArray[cs.AssetConfigEntry, 50]:\n    return [\n"
        + "\n".join(entries) + "\n    ]\n"
    )

    # priority lists
    priority_counts = {}
    for name, fn in (("priorityLiqAssetVaults", "getPriorityLiqAssetVaults"),
                     ("priorityStabVaults", "getPriorityStabVaults")):
        vaults = call(mc, fn)
        _require_cap(name, len(vaults))
        priority_counts[name] = len(vaults)
        rows = [
            f"        cs.VaultLite(vaultId={v[0]}, asset={r.address(v[1])}),"
            for v in vaults
        ]
        body = "[\n" + "\n".join(rows) + "\n    ]" if rows else "[]"
        out.append(
            f"\n\n@view\n@external\ndef {name}() -> DynArray[cs.VaultLite, 20]:\n"
            f"    return {body}\n"
        )

    ids = call(mc, "getPriorityPriceSourceIds")
    _require_cap("priorityPriceSourceIds", len(ids))
    getter("priorityPriceSourceIds", "DynArray[uint256, 10]",
           "[" + ", ".join(str(i) for i in ids) + "]")

    num_signers = call(mc, "numLiteSigners")
    signers = [call(mc, "liteSigners", i) for i in range(1, num_signers)]
    signers = [s for s in signers if int(s, 16) != 0]
    _require_cap("liteSigners", len(signers))
    body = "[\n" + "\n".join(
        f"        {Web3.to_checksum_address(s)}," for s in signers
    ) + "\n    ]" if signers else "[]"
    out.append(
        "\n\n@view\n@external\ndef liteSigners() -> DynArray[address, 10]:\n"
        f"    return {body}\n"
    )

    return BuildResult(
        source="".join(out),
        counts={
            "assetConfigs": len(assets),
            "ripeGovVaultConfigs": len(gov_entries),
            "priorityPriceSourceIds": len(ids),
            "liteSigners": len(signers),
            **priority_counts,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--network",
        default=DEFAULT_NETWORK.key,
        choices=sorted(NETWORKS),
        help="Deployed network to snapshot.",
    )
    parser.add_argument(
        "--block-number",
        required=True,
        type=int,
        help="Exact snapshot block; it must already be finalized.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write somewhere other than the network's default target.",
    )
    parser.add_argument("--check", action="store_true",
                        help="Exit 1 if the contract is out of date.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    network = NETWORKS[args.network]
    target = args.output or network.target_path

    rpc = os.environ.get(network.rpc_env)
    if not rpc:
        print(f"{network.rpc_env} is not set (put it in .env).", file=sys.stderr)
        return 2

    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(rpc))
    manifest_bytes = network.manifest_path.read_bytes()
    try:
        mc_addr, ledger_addr = _manifest_addresses(manifest_bytes)
        abi_inputs = load_abi_inputs()
        snapshot = select_snapshot(
            w3,
            mc_addr,
            ledger_addr,
            block_number=args.block_number,
            manifest_bytes=manifest_bytes,
            generator_bytes=Path(__file__).read_bytes(),
            abi_inputs=abi_inputs,
            network=network,
        )
        # The URL carries a provider key, so it is never printed. Status goes
        # to stderr so `--dry-run > file` writes only the contract.
        print(
            f"reading {network.display_name} chain {snapshot.chain_id} at snapshot "
            f"block {snapshot.block_number} ({snapshot.block_hash}); "
            "verified finalized",
            file=sys.stderr,
        )
        result = build(
            w3,
            mc_addr,
            ledger_addr,
            snapshot,
            manifest_bytes=manifest_bytes,
            abi_inputs=abi_inputs,
            network=network,
        )
        verify_snapshot(w3, snapshot)
    except SnapshotError as exc:
        print(f"snapshot failed closed: {exc}", file=sys.stderr)
        return 2

    source = result.source
    if args.dry_run:
        print(result.coverage_report(network), file=sys.stderr)
        print(source)
        return 0

    print(result.coverage_report(network))

    current = target.read_text() if target.exists() else ""
    label = target.relative_to(ROOT) if target.is_relative_to(ROOT) else target
    if args.check:
        if current == source:
            print(f"{label} is up to date.")
            return 0
        print(f"{label} is STALE -- rerun without --check.", file=sys.stderr)
        return 1

    target.write_text(source)
    print(f"wrote {label}"
          f" ({'unchanged' if current == source else 'CHANGED -- review the diff'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
