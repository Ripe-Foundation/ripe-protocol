#!/usr/bin/env python3
"""Regenerate governed Vyper artifact expectations from final local bytes."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.artifact_expectations import load_artifact_expectations  # noqa: E402
from scripts import check_contract_artifacts as checker  # noqa: E402


EXPECTATIONS = ROOT / "config" / "contract-artifact-expectations.json"
REMEDIATION_CONTRACTS = {
    "MissionControl",
    "RipeGov",
    "StabilityPool",
    "SwitchboardBravo",
    "UniswapV2Prices",
    "VaultMigrator",
}


def _source_for(name: str) -> Path:
    matches = sorted((ROOT / "contracts").rglob(f"{name}.vy"))
    if len(matches) != 1:
        raise checker.ArtifactCheckError(
            f"{name}: expected one production source, got {len(matches)}"
        )
    return matches[0]


def _code_data_size(layout: dict) -> int:
    size = 0
    for value in layout.values():
        if isinstance(value, dict) and {"offset", "length", "type"} <= set(value):
            size += int(value["length"])
        elif isinstance(value, dict):
            size += _code_data_size(value)
    return size


def _record(name: str, source: Path, prior: dict, vyper: Path) -> dict:
    compiled = checker._compile(source, vyper)
    creation_binding = checker._creation_binding(
        compiled.creation,
        integrity=compiled.integrity,
        runtime_template=compiled.runtime_template,
    )
    abi_path = ROOT / "scripts" / "abis" / f"{name}.json"
    abi_bytes = abi_path.read_bytes()
    committed_abi = json.loads(abi_bytes)
    if checker._canonical_json_bytes(compiled.abi) != checker._canonical_json_bytes(
        committed_abi
    ):
        raise checker.ArtifactCheckError(f"{name}: committed ABI is not current")

    artifacts = {
        "creation_executable_prefix_sha256": checker._sha256(
            creation_binding.executable_prefix
        ),
        "creation_executable_prefix_size": len(
            creation_binding.executable_prefix
        ),
        "creation_metadata_sha256": checker._sha256(
            creation_binding.compiler_metadata
        ),
        "creation_metadata_size": len(creation_binding.compiler_metadata),
        "creation_sha256": checker._sha256(compiled.creation),
        "creation_size": len(compiled.creation),
        "eip170_headroom": checker.EIP_170_LIMIT - len(compiled.runtime_template),
        "runtime_template_sha256": checker._sha256(compiled.runtime_template),
        "runtime_template_size": len(compiled.runtime_template),
    }
    deployed_runtime_size = len(compiled.runtime_template) + _code_data_size(
        compiled.code_layout
    )
    artifacts["deployed_runtime_size"] = deployed_runtime_size
    artifacts["deployed_eip170_headroom"] = (
        checker.EIP_170_LIMIT - deployed_runtime_size
    )
    accepted_ceiling = prior.get("artifacts", {}).get("accepted_runtime_ceiling")
    if accepted_ceiling is not None:
        artifacts["accepted_runtime_ceiling"] = accepted_ceiling

    events = [entry for entry in compiled.abi if entry.get("type") == "event"]
    constructors = [
        entry for entry in compiled.abi if entry.get("type") == "constructor"
    ]
    return {
        "abi": {
            "canonical_sha256": checker._json_sha256(compiled.abi),
            "committed_file_sha256": checker._sha256(abi_bytes),
            "committed_path": abi_path.relative_to(ROOT).as_posix(),
        },
        "artifacts": artifacts,
        "code_layout": compiled.code_layout,
        "compiler_settings": compiled.settings,
        "constructor": constructors,
        "constructor_bound_runtime_template": bool(compiled.code_layout),
        "effective_optimization": compiled.effective_optimization,
        "events": {
            "canonical_sha256": checker._json_sha256(events),
            "count": len(events),
        },
        "selectors": {
            "canonical_sha256": checker._json_sha256(
                compiled.method_identifiers
            ),
            "count": len(compiled.method_identifiers),
        },
        "source_git_blob": compiled.source_git_blob,
        "source_path": source.relative_to(ROOT).as_posix(),
        "source_sha256": compiled.source_sha256,
        "storage_layout": compiled.storage_layout,
        "transient_storage_layout": compiled.transient_storage_layout,
        "transitive_compiler_input_integrity": compiled.integrity,
    }


def main() -> int:
    values = load_artifact_expectations(EXPECTATIONS, root=ROOT)
    governed_names = set(values["contracts"]) | REMEDIATION_CONTRACTS
    names = sys.argv[1:] or sorted(governed_names)
    unknown = sorted(set(names) - governed_names)
    if unknown:
        raise checker.ArtifactCheckError(
            f"unknown governed contract(s): {', '.join(unknown)}"
        )
    vyper = checker._vyper_path()
    records = dict(values["contracts"])
    for name in names:
        records[name] = _record(
            name,
            _source_for(name),
            values["contracts"].get(name, {}),
            vyper,
        )
        print(f"refreshed {name}")
    values["contracts"] = {name: records[name] for name in sorted(records)}
    EXPECTATIONS.write_text(json.dumps(values, indent=2, sort_keys=True) + "\n")
    print(f"wrote {EXPECTATIONS.relative_to(ROOT)} ({len(records)} contracts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
