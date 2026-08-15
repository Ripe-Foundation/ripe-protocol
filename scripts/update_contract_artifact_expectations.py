#!/usr/bin/env python3
"""Regenerate governed Vyper artifact expectations from final local bytes."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.artifact_expectations import load_artifact_expectations  # noqa: E402
from scripts import check_contract_artifacts as checker
from scripts import capture_contract_runtimes as runtime_capture


EXPECTATIONS = ROOT / "config" / "contract-artifact-expectations.json"
GOVERNED_SOURCES = checker.GOVERNED_SOURCES
GOVERNED_CONTRACTS = checker.GOVERNED_CONTRACTS
DEPLOYED_RUNTIME_CONTRACTS = checker.DEPLOYED_RUNTIME_CONTRACTS


def _source_for(name: str) -> Path:
    try:
        relative = GOVERNED_SOURCES[name]
    except KeyError as exc:
        raise checker.ArtifactCheckError(
            f"{name}: no canonical governed source path"
        ) from exc
    source = ROOT / relative
    if not source.is_file():
        raise checker.ArtifactCheckError(
            f"{name}: canonical governed source is missing: {relative}"
        )
    return source


def _record(
    name: str,
    source: Path,
    prior: dict,
    vyper: Path,
    deployed_runtime: bytes | None,
) -> dict:
    compiled = checker._compile(source, vyper)
    constructor_bound = bool(checker._code_data_size(compiled.code_layout))
    expected_constructor_bound = name in DEPLOYED_RUNTIME_CONTRACTS
    if constructor_bound != expected_constructor_bound:
        raise checker.ArtifactCheckError(
            f"{name}: deployed-runtime capture classification changed; "
            "review the exact 18-contract capture policy"
        )
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
    if deployed_runtime_size >= checker.EIP_170_LIMIT:
        raise checker.ArtifactCheckError(
            f"{name}: deployed runtime {deployed_runtime_size} is not below "
            "EIP-170"
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
        if len(compiled.runtime_template) > accepted_ceiling:
            raise checker.ArtifactCheckError(
                f"{name}: runtime {len(compiled.runtime_template)} exceeds "
                f"accepted ceiling {accepted_ceiling}"
            )
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
        "constructor_bound_runtime_template": constructor_bound,
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
        path = Path(raw_path)
        if path.is_symlink():
            raise checker.ArtifactCheckError(
                f"deployed runtime path must not be a symlink: {path}"
            )
        paths[name] = path.resolve()
    return paths


def _git(*arguments: str) -> str:
    return checker._run(["git", *arguments], cwd=ROOT).strip()


def _validate_capture_manifest(
    manifest_path: Path,
    runtime_paths: dict[str, Path],
    expected_vyper_version: str,
) -> dict:
    if manifest_path.is_symlink():
        raise checker.ArtifactCheckError(
            f"capture completion manifest must not be a symlink: {manifest_path}"
        )
    manifest_path = manifest_path.resolve()
    if not manifest_path.is_file():
        raise checker.ArtifactCheckError(
            f"capture completion manifest is not a regular file: {manifest_path}"
        )
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise checker.ArtifactCheckError(
            f"invalid capture completion manifest: {manifest_path}"
        ) from exc
    if manifest.get("schema_version") != runtime_capture.CAPTURE_SCHEMA_VERSION:
        raise checker.ArtifactCheckError("capture manifest schema mismatch")
    if manifest.get("status") != "complete":
        raise checker.ArtifactCheckError("capture manifest is not complete")

    expected_files = {
        runtime_capture.CAPTURE_MANIFEST,
        *(f"{name}.runtime" for name in DEPLOYED_RUNTIME_CONTRACTS),
    }
    actual_files = {path.name for path in manifest_path.parent.iterdir()}
    if actual_files != expected_files:
        missing = sorted(expected_files - actual_files)
        unexpected = sorted(actual_files - expected_files)
        raise checker.ArtifactCheckError(
            "capture directory census mismatch: "
            f"missing={missing}, unexpected={unexpected}"
        )

    repository = manifest.get("repository")
    if not isinstance(repository, dict):
        raise checker.ArtifactCheckError("capture repository provenance is missing")
    expected_repository = {
        "root": str(ROOT.resolve()),
        "head": _git("rev-parse", "HEAD^{commit}"),
        "tree": _git("rev-parse", "HEAD^{tree}"),
        "source_status": "",
    }
    if repository != expected_repository:
        raise checker.ArtifactCheckError(
            "capture repository provenance does not match the current source freeze"
        )
    current_source_status = _git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        "contracts",
        "interfaces",
    )
    if current_source_status:
        raise checker.ArtifactCheckError(
            "artifact refresh requires clean contract/interface sources"
        )

    script_record = manifest.get("capture_script")
    expected_script_record = {
        "path": "scripts/capture_contract_runtimes.py",
        "sha256": checker._sha256(Path(runtime_capture.__file__).read_bytes()),
    }
    if script_record != expected_script_record:
        raise checker.ArtifactCheckError("capture script provenance mismatch")

    expected_toolchain = {
        "python": os.path.realpath(sys.executable),
        "titanoboa": importlib.metadata.version("titanoboa"),
        "vyper": expected_vyper_version,
    }
    if manifest.get("toolchain") != expected_toolchain:
        raise checker.ArtifactCheckError("capture toolchain provenance mismatch")
    if manifest.get("governed_contracts") != sorted(GOVERNED_CONTRACTS):
        raise checker.ArtifactCheckError("capture governed-contract census mismatch")
    if manifest.get("runtime_contracts") != sorted(DEPLOYED_RUNTIME_CONTRACTS):
        raise checker.ArtifactCheckError("capture runtime-contract census mismatch")
    if manifest.get("template_identity_contracts") != ["DefaultsRobinhoodLive"]:
        raise checker.ArtifactCheckError("capture template-identity census mismatch")

    records = manifest.get("contracts")
    if not isinstance(records, dict) or set(records) != DEPLOYED_RUNTIME_CONTRACTS:
        raise checker.ArtifactCheckError("capture contract-record census mismatch")
    expected_provenance = runtime_capture.expected_capture_provenance()
    for name in sorted(DEPLOYED_RUNTIME_CONTRACTS):
        record = records[name]
        if not isinstance(record, dict):
            raise checker.ArtifactCheckError(f"{name}: invalid capture record")
        for field, expected in expected_provenance[name].items():
            if record.get(field) != expected:
                raise checker.ArtifactCheckError(
                    f"{name}: capture {field} provenance mismatch"
                )
        source = ROOT / GOVERNED_SOURCES[name]
        if record.get("source_sha256") != checker._sha256(source.read_bytes()):
            raise checker.ArtifactCheckError(f"{name}: capture source hash mismatch")
        expected_runtime_name = f"{name}.runtime"
        if record.get("runtime_file") != expected_runtime_name:
            raise checker.ArtifactCheckError(f"{name}: capture runtime filename mismatch")
        expected_runtime_path = manifest_path.parent / expected_runtime_name
        supplied_runtime_path = runtime_paths[name]
        if supplied_runtime_path != expected_runtime_path.resolve():
            raise checker.ArtifactCheckError(
                f"{name}: supplied runtime is outside the authenticated capture"
            )
        if not supplied_runtime_path.is_file():
            raise checker.ArtifactCheckError(
                f"{name}: captured runtime is not a regular file"
            )
        runtime = supplied_runtime_path.read_bytes()
        if record.get("runtime_size") != len(runtime):
            raise checker.ArtifactCheckError(f"{name}: captured runtime size mismatch")
        if record.get("runtime_sha256") != checker._sha256(runtime):
            raise checker.ArtifactCheckError(f"{name}: captured runtime hash mismatch")
    return manifest


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
    parser.add_argument(
        "--capture-manifest",
        type=Path,
        help=(
            "completion manifest emitted by scripts/capture_contract_runtimes.py; "
            "required by strict refresh"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    values = load_artifact_expectations(
        EXPECTATIONS, root=ROOT, allow_v2=False
    )
    existing_names = set(values["contracts"])
    unexpected_existing_names = sorted(existing_names - GOVERNED_CONTRACTS)
    if unexpected_existing_names:
        raise checker.ArtifactCheckError(
            "unexpected contract(s) in governed expectations: "
            + ", ".join(unexpected_existing_names)
        )
    governed_names = set(GOVERNED_CONTRACTS)
    if args.require_deployed_runtime_bindings and args.contracts:
        raise checker.ArtifactCheckError(
            "strict artifact refresh forbids positional contract filters"
        )
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
    if args.require_deployed_runtime_bindings:
        supplied_runtime_names = set(runtime_paths)
        missing_runtime_names = sorted(
            DEPLOYED_RUNTIME_CONTRACTS - supplied_runtime_names
        )
        unexpected_runtime_names = sorted(
            supplied_runtime_names - DEPLOYED_RUNTIME_CONTRACTS
        )
        if missing_runtime_names or unexpected_runtime_names:
            raise checker.ArtifactCheckError(
                "strict deployed-runtime input census mismatch: "
                f"missing={missing_runtime_names}, "
                f"unexpected={unexpected_runtime_names}"
            )
        if args.capture_manifest is None:
            raise checker.ArtifactCheckError(
                "strict artifact refresh requires --capture-manifest"
            )
    elif args.capture_manifest is not None:
        raise checker.ArtifactCheckError(
            "--capture-manifest is only valid for strict artifact refresh"
        )
    vyper = checker._vyper_path()
    checker._validate_compiler_envelope(values, vyper)
    if args.require_deployed_runtime_bindings:
        _validate_capture_manifest(
            args.capture_manifest,
            runtime_paths,
            values["compiler"]["version"],
        )
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
    if args.require_deployed_runtime_bindings:
        missing_records = sorted(GOVERNED_CONTRACTS - set(records))
        if missing_records:
            raise checker.ArtifactCheckError(
                "missing governed contract records: " + ", ".join(missing_records)
            )
        pending = sorted(
            name
            for name, record in records.items()
            if record.get("constructor_bound_runtime_template")
            and "deployed_runtime_sha256" not in record["artifacts"]
        )
        if pending:
            raise checker.ArtifactCheckError(
                "missing deployed runtime bindings: " + ", ".join(pending)
            )
    values["contracts"] = {name: records[name] for name in sorted(records)}
    checker._atomic_write_bytes(
        EXPECTATIONS,
        (json.dumps(values, indent=2, sort_keys=True) + "\n").encode(),
    )
    print(f"wrote {EXPECTATIONS.relative_to(ROOT)} ({len(records)} contracts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
