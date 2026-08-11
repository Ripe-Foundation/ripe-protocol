#!/usr/bin/env python3
"""Regenerate governed Vyper artifact expectations from final local bytes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import check_contract_artifacts as checker


EXPECTATIONS = ROOT / "config" / "contract-artifact-expectations.json"
REMEDIATION_CONTRACTS = {
    "BlueChipYieldPrices",
    "DefaultsRobinhoodLive",
    "MissionControl",
    "RipeGov",
    "StabilityPool",
    "SwitchboardAlpha",
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


def _record(
    name: str,
    source: Path,
    prior: dict,
    vyper: Path,
    deployed_runtime: bytes | None,
) -> dict:
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
    deployed_runtime_size = (
        len(compiled.runtime_template)
        + checker._code_data_size(compiled.code_layout)
    )
    artifacts["deployed_runtime_size"] = deployed_runtime_size
    artifacts["deployed_eip170_headroom"] = (
        checker.EIP_170_LIMIT - deployed_runtime_size
    )
    prior_artifacts = prior.get("artifacts", {})
    prior_binding_fields = {
        "deployed_runtime_immutable_data_hex",
        "deployed_runtime_immutable_data_sha256",
        "deployed_runtime_immutable_data_size",
        "deployed_runtime_sha256",
    }.intersection(prior_artifacts)
    if deployed_runtime is None and deployed_runtime_size != len(
        compiled.runtime_template
    ) and prior_binding_fields:
        raise checker.ArtifactCheckError(
            f"{name}: refusing to discard an existing deployed runtime "
            "binding; supply fresh measured runtime bytes"
        )
    if deployed_runtime is not None:
        binding = checker._extract_deployed_runtime_binding(
            compiled,
            deployed_runtime,
        )
        artifacts.update(
            {
                "deployed_runtime_immutable_data_hex": (
                    binding.immutable_data.hex()
                ),
                "deployed_runtime_immutable_data_sha256": checker._sha256(
                    binding.immutable_data
                ),
                "deployed_runtime_immutable_data_size": len(
                    binding.immutable_data
                ),
                "deployed_runtime_sha256": checker._sha256(binding.runtime),
            }
        )
    elif not compiled.code_layout:
        # With no immutable/code-data layout, the compiler runtime template is
        # already the full deployed runtime identity.
        artifacts.update(
            {
                "deployed_runtime_immutable_data_hex": "",
                "deployed_runtime_immutable_data_sha256": checker._sha256(b""),
                "deployed_runtime_immutable_data_size": 0,
                "deployed_runtime_sha256": checker._sha256(
                    compiled.runtime_template
                ),
            }
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


def _parse_runtime_paths(values: list[str]) -> dict[str, Path]:
    paths = {}
    for value in values:
        if "=" not in value:
            raise checker.ArtifactCheckError(
                f"invalid --deployed-runtime {value!r}; expected Contract=path"
            )
        name, raw_path = value.split("=", 1)
        if not name or name in paths:
            raise checker.ArtifactCheckError(
                f"invalid or duplicate deployed runtime contract: {name!r}"
            )
        paths[name] = Path(raw_path).resolve()
    return paths


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contracts", nargs="*")
    parser.add_argument(
        "--deployed-runtime",
        action="append",
        default=[],
        help=(
            "raw constructor-bound runtime bytecode as Contract=path; "
            "repeat for each immutable-bearing refreshed contract"
        ),
    )
    parser.add_argument(
        "--require-deployed-runtime-bindings",
        action="store_true",
        help="refuse to write if any governed immutable runtime stays unbound",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    values = json.loads(EXPECTATIONS.read_text())
    governed_names = set(values["contracts"]) | REMEDIATION_CONTRACTS
    names = args.contracts or sorted(governed_names)
    unknown = sorted(set(names) - governed_names)
    if unknown:
        raise checker.ArtifactCheckError(
            f"unknown governed contract(s): {', '.join(unknown)}"
        )
    runtime_paths = _parse_runtime_paths(args.deployed_runtime)
    unknown_runtime_names = sorted(set(runtime_paths) - governed_names)
    if unknown_runtime_names:
        raise checker.ArtifactCheckError(
            "unknown deployed runtime contract(s): "
            + ", ".join(unknown_runtime_names)
        )
    unused_runtime_names = sorted(set(runtime_paths) - set(names))
    if unused_runtime_names:
        raise checker.ArtifactCheckError(
            "deployed runtime supplied for an unselected contract: "
            + ", ".join(unused_runtime_names)
        )
    vyper = checker._vyper_path()
    records = dict(values["contracts"])
    for name in names:
        records[name] = _record(
            name,
            _source_for(name),
            values["contracts"].get(name, {}),
            vyper,
            (
                runtime_paths[name].read_bytes()
                if name in runtime_paths
                else None
            ),
        )
        suffix = ""
        if (
            records[name]["constructor_bound_runtime_template"]
            and "deployed_runtime_sha256" not in records[name]["artifacts"]
        ):
            suffix = " (deployed runtime binding pending)"
        print(f"refreshed {name}{suffix}")
    values["contracts"] = {name: records[name] for name in sorted(records)}
    if args.require_deployed_runtime_bindings:
        pending = sorted(
            name
            for name, record in values["contracts"].items()
            if record.get("constructor_bound_runtime_template")
            and "deployed_runtime_sha256" not in record["artifacts"]
        )
        if pending:
            raise checker.ArtifactCheckError(
                "missing deployed runtime bindings: " + ", ".join(pending)
            )
    EXPECTATIONS.write_text(json.dumps(values, indent=2, sort_keys=True) + "\n")
    print(f"wrote {EXPECTATIONS.relative_to(ROOT)} ({len(records)} contracts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
