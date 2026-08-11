#!/usr/bin/env python3
"""Fail-closed artifact checks for the reviewed RH production contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import cbor2


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPECTATIONS = ROOT / "config" / "contract-artifact-expectations.json"
EIP_170_LIMIT = 24_576
SCHEMA_VERSION = 1
PRAGMA_OPTIMIZE_RE = re.compile(r"^# pragma optimize ([a-z]+)$", re.MULTILINE)


class ArtifactCheckError(RuntimeError):
    """Raised when a frozen artifact invariant does not hold."""


@dataclass(frozen=True)
class CompiledContract:
    source_sha256: str
    source_git_blob: str
    integrity: str
    effective_optimization: str
    settings: Mapping[str, Any]
    creation: bytes
    runtime_template: bytes
    abi: Sequence[Mapping[str, Any]]
    method_identifiers: Mapping[str, str]
    storage_layout: Mapping[str, Any]
    transient_storage_layout: Mapping[str, Any]
    code_layout: Mapping[str, Any]


@dataclass(frozen=True)
class CreationBinding:
    executable_prefix: bytes
    compiler_metadata: bytes


@dataclass(frozen=True)
class DeployedRuntimeBinding:
    immutable_data: bytes
    runtime: bytes


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def _json_sha256(value: Any) -> str:
    return _sha256(_canonical_json_bytes(value))


def _iter_code_layout_entries(layout: Mapping[str, Any]):
    for value in layout.values():
        if isinstance(value, Mapping) and {"offset", "length", "type"} <= set(value):
            yield value
        elif isinstance(value, Mapping):
            yield from _iter_code_layout_entries(value)


def _code_data_size(layout: Mapping[str, Any]) -> int:
    entries = sorted(
        (
            int(item["offset"]),
            int(item["length"]),
        )
        for item in _iter_code_layout_entries(layout)
    )
    cursor = 0
    for offset, length in entries:
        if length <= 0 or offset != cursor:
            raise ArtifactCheckError(
                "immutable/code layout is not positive and contiguous: "
                f"expected offset {cursor}, got offset {offset}, length {length}"
            )
        cursor += length
    return cursor


def _deployed_runtime_binding(
    compiled: CompiledContract,
    immutable_data_hex: str,
) -> DeployedRuntimeBinding:
    """Bind a Vyper runtime template to exact constructor immutable bytes."""
    if not isinstance(immutable_data_hex, str) or not re.fullmatch(
        r"(?:[0-9a-f]{2})*",
        immutable_data_hex,
    ):
        raise ArtifactCheckError(
            "constructor immutable data must be canonical lowercase, "
            "unprefixed hex"
        )
    immutable_data = bytes.fromhex(immutable_data_hex)

    expected_size = _code_data_size(compiled.code_layout)
    if len(immutable_data) != expected_size:
        raise ArtifactCheckError(
            "constructor immutable data size mismatch: "
            f"expected {expected_size}, got {len(immutable_data)}"
        )
    return DeployedRuntimeBinding(
        immutable_data=immutable_data,
        runtime=compiled.runtime_template + immutable_data,
    )


def _extract_deployed_runtime_binding(
    compiled: CompiledContract,
    deployed_runtime: bytes,
) -> DeployedRuntimeBinding:
    """Validate measured deployed code and extract its immutable suffix."""
    expected_size = len(compiled.runtime_template) + _code_data_size(
        compiled.code_layout
    )
    if len(deployed_runtime) != expected_size:
        raise ArtifactCheckError(
            "measured deployed runtime size mismatch: "
            f"expected {expected_size}, got {len(deployed_runtime)}"
        )
    if not deployed_runtime.startswith(compiled.runtime_template):
        raise ArtifactCheckError(
            "measured deployed runtime does not start with compiler template"
        )
    immutable_data = deployed_runtime[len(compiled.runtime_template):]
    return DeployedRuntimeBinding(
        immutable_data=immutable_data,
        runtime=deployed_runtime,
    )


def _creation_binding(
    creation: bytes,
    *,
    integrity: str,
    runtime_template: bytes,
) -> CreationBinding:
    """Split metadata-bearing Vyper initcode; fail closed for other formats."""
    if len(creation) < 3:
        raise ArtifactCheckError("creation artifact is too short for Vyper metadata")

    metadata_size = int.from_bytes(creation[-2:], "big")
    if metadata_size < 3 or metadata_size >= len(creation):
        raise ArtifactCheckError(
            f"invalid Vyper compiler metadata size: {metadata_size}"
        )

    executable_prefix = creation[:-metadata_size]
    compiler_metadata = creation[-metadata_size:]
    encoded_metadata = compiler_metadata[:-2]
    try:
        decoded = cbor2.loads(encoded_metadata)
    except cbor2.CBORDecodeError as exc:
        raise ArtifactCheckError("invalid Vyper compiler metadata CBOR") from exc

    if cbor2.dumps(decoded) != encoded_metadata:
        raise ArtifactCheckError("non-canonical Vyper compiler metadata CBOR")
    if not isinstance(decoded, (list, tuple)) or len(decoded) != 5:
        raise ArtifactCheckError("unexpected Vyper compiler metadata shape")

    embedded_integrity = decoded[0]
    if not isinstance(embedded_integrity, bytes) or len(embedded_integrity) != 32:
        raise ArtifactCheckError(
            "unexpected Vyper compiler metadata integrity field"
        )
    if embedded_integrity.hex() != integrity:
        raise ArtifactCheckError(
            "Vyper compiler metadata integrity does not bind compiler inputs"
        )
    if decoded[1] != len(runtime_template):
        raise ArtifactCheckError(
            "Vyper compiler metadata runtime length does not bind runtime template"
        )

    return CreationBinding(
        executable_prefix=executable_prefix,
        compiler_metadata=compiler_metadata,
    )


def _run(command: Sequence[str], *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ArtifactCheckError(
            f"command failed ({completed.returncode}): {' '.join(command)}: {detail}"
        )
    return completed.stdout


def _vyper_path() -> Path:
    candidate = Path(sys.executable).with_name("vyper")
    if not candidate.is_file():
        raise ArtifactCheckError(
            f"exact-environment vyper sibling is missing: {candidate}"
        )
    return candidate


def _effective_optimization(source_text: str) -> str:
    match = PRAGMA_OPTIMIZE_RE.search(source_text)
    return match.group(1) if match else "gas"


def _compile(source_path: Path, vyper: Path) -> CompiledContract:
    source_bytes = source_path.read_bytes()
    source_text = source_bytes.decode()
    effective_optimization = _effective_optimization(source_text)

    # Canonical S1 artifact recipe. Never add an -O override here: the source
    # pragma, or Vyper's default in its absence, owns optimization selection.
    artifact_output = _run(
        [
            str(vyper),
            "-p",
            ".",
            "-f",
            "bytecode,bytecode_runtime",
            str(source_path),
        ]
    )
    artifact_lines = [
        line.strip() for line in artifact_output.splitlines() if line.strip()
    ]
    if len(artifact_lines) != 2:
        raise ArtifactCheckError(
            f"{source_path}: expected two artifact lines, got {len(artifact_lines)}"
        )
    try:
        creation = bytes.fromhex(artifact_lines[0].removeprefix("0x"))
        runtime_template = bytes.fromhex(artifact_lines[1].removeprefix("0x"))
    except ValueError as exc:
        raise ArtifactCheckError(f"{source_path}: non-hex artifact output") from exc

    combined = json.loads(
        _run(
            [
                str(vyper),
                "-p",
                ".",
                "-f",
                "combined_json",
                str(source_path),
            ]
        )
    )
    contract_outputs = [value for key, value in combined.items() if key != "version"]
    if len(contract_outputs) != 1:
        raise ArtifactCheckError(
            f"{source_path}: expected one combined-json contract output"
        )
    output = contract_outputs[0]
    layout = output["layout"]
    integrity = _run(
        [str(vyper), "-p", ".", "-f", "integrity", str(source_path)]
    ).strip()
    git_blob = _run(["git", "hash-object", str(source_path)]).strip()

    return CompiledContract(
        source_sha256=_sha256(source_bytes),
        source_git_blob=git_blob,
        integrity=integrity,
        effective_optimization=effective_optimization,
        settings=output["settings_dict"],
        creation=creation,
        runtime_template=runtime_template,
        abi=output["abi"],
        method_identifiers=output["method_identifiers"],
        storage_layout=layout.get("storage_layout", {}),
        transient_storage_layout=layout.get("transient_storage_layout", {}),
        code_layout=layout.get("code_layout", {}),
    )


def _assert_equal(contract: str, field: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise ArtifactCheckError(
            f"{contract}: {field} mismatch: expected {expected!r}, got {actual!r}"
        )


def _check_contract(
    name: str,
    expected: Mapping[str, Any],
    *,
    vyper: Path,
    source_override: Path | None,
    require_deployed_runtime_binding: bool,
) -> str:
    expected_source = ROOT / expected["source_path"]
    source_path = source_override or expected_source
    compiled = _compile(source_path, vyper)

    _assert_equal(name, "source_sha256", compiled.source_sha256, expected["source_sha256"])
    _assert_equal(
        name, "source_git_blob", compiled.source_git_blob, expected["source_git_blob"]
    )
    _assert_equal(
        name,
        "transitive_compiler_input_integrity",
        compiled.integrity,
        expected["transitive_compiler_input_integrity"],
    )
    _assert_equal(
        name,
        "effective_optimization",
        compiled.effective_optimization,
        expected["effective_optimization"],
    )
    _assert_equal(name, "compiler_settings", compiled.settings, expected["compiler_settings"])

    artifacts = expected["artifacts"]
    creation_binding = _creation_binding(
        compiled.creation,
        integrity=compiled.integrity,
        runtime_template=compiled.runtime_template,
    )
    _assert_equal(name, "creation_size", len(compiled.creation), artifacts["creation_size"])
    _assert_equal(
        name, "creation_sha256", _sha256(compiled.creation), artifacts["creation_sha256"]
    )
    _assert_equal(
        name,
        "creation executable-prefix size",
        len(creation_binding.executable_prefix),
        artifacts["creation_executable_prefix_size"],
    )
    _assert_equal(
        name,
        "creation executable-prefix SHA-256",
        _sha256(creation_binding.executable_prefix),
        artifacts["creation_executable_prefix_sha256"],
    )
    _assert_equal(
        name,
        "creation compiler-metadata size",
        len(creation_binding.compiler_metadata),
        artifacts["creation_metadata_size"],
    )
    _assert_equal(
        name,
        "creation compiler-metadata SHA-256",
        _sha256(creation_binding.compiler_metadata),
        artifacts["creation_metadata_sha256"],
    )
    _assert_equal(
        name,
        "runtime_template_size",
        len(compiled.runtime_template),
        artifacts["runtime_template_size"],
    )
    _assert_equal(
        name,
        "runtime_template_sha256",
        _sha256(compiled.runtime_template),
        artifacts["runtime_template_sha256"],
    )
    headroom = EIP_170_LIMIT - len(compiled.runtime_template)
    _assert_equal(name, "eip170_headroom", headroom, artifacts["eip170_headroom"])
    code_data_size = _code_data_size(compiled.code_layout)
    deployed_runtime_size = len(compiled.runtime_template) + code_data_size
    _assert_equal(
        name,
        "constructor-bound deployed runtime size",
        deployed_runtime_size,
        artifacts["deployed_runtime_size"],
    )
    _assert_equal(
        name,
        "constructor-bound deployed EIP-170 headroom",
        EIP_170_LIMIT - deployed_runtime_size,
        artifacts["deployed_eip170_headroom"],
    )
    if deployed_runtime_size >= EIP_170_LIMIT:
        raise ArtifactCheckError(
            f"{name}: deployed runtime {deployed_runtime_size} is not below EIP-170"
        )

    deployed_binding_fields = {
        "deployed_runtime_immutable_data_hex",
        "deployed_runtime_immutable_data_size",
        "deployed_runtime_immutable_data_sha256",
        "deployed_runtime_sha256",
    }
    present_binding_fields = deployed_binding_fields.intersection(artifacts)
    if present_binding_fields and present_binding_fields != deployed_binding_fields:
        missing = sorted(deployed_binding_fields - present_binding_fields)
        raise ArtifactCheckError(
            f"{name}: incomplete deployed runtime binding; missing "
            + ", ".join(missing)
        )

    immutable_data_hex = artifacts.get("deployed_runtime_immutable_data_hex")
    deployed_binding = None
    if immutable_data_hex is not None:
        deployed_binding = _deployed_runtime_binding(
            compiled,
            immutable_data_hex,
        )
        _assert_equal(
            name,
            "constructor immutable data size",
            len(deployed_binding.immutable_data),
            artifacts["deployed_runtime_immutable_data_size"],
        )
        _assert_equal(
            name,
            "constructor immutable data SHA-256",
            _sha256(deployed_binding.immutable_data),
            artifacts["deployed_runtime_immutable_data_sha256"],
        )
        _assert_equal(
            name,
            "constructor-bound deployed runtime SHA-256",
            _sha256(deployed_binding.runtime),
            artifacts["deployed_runtime_sha256"],
        )
        _assert_equal(
            name,
            "constructor-bound deployed runtime size",
            len(deployed_binding.runtime),
            artifacts["deployed_runtime_size"],
        )
    elif code_data_size and require_deployed_runtime_binding:
        raise ArtifactCheckError(
            f"{name}: missing constructor-bound deployed runtime binding"
        )
    accepted_ceiling = artifacts.get("accepted_runtime_ceiling")
    if accepted_ceiling is not None and len(compiled.runtime_template) > accepted_ceiling:
        raise ArtifactCheckError(
            f"{name}: runtime {len(compiled.runtime_template)} exceeds accepted "
            f"ceiling {accepted_ceiling}"
        )

    abi_expectation = expected["abi"]
    fresh_abi_hash = _json_sha256(compiled.abi)
    _assert_equal(
        name,
        "fresh canonical ABI versus frozen expectation",
        fresh_abi_hash,
        abi_expectation["canonical_sha256"],
    )
    committed_abi_path = ROOT / abi_expectation["committed_path"]
    committed_abi_bytes = committed_abi_path.read_bytes()
    committed_abi = json.loads(committed_abi_bytes)
    _assert_equal(
        name,
        "fresh compiler ABI versus committed ABI",
        _canonical_json_bytes(compiled.abi),
        _canonical_json_bytes(committed_abi),
    )
    _assert_equal(
        name,
        "committed ABI file hash",
        _sha256(committed_abi_bytes),
        abi_expectation["committed_file_sha256"],
    )

    selectors = expected["selectors"]
    _assert_equal(
        name,
        "selector count",
        len(compiled.method_identifiers),
        selectors["count"],
    )
    _assert_equal(
        name,
        "selectors",
        _json_sha256(compiled.method_identifiers),
        selectors["canonical_sha256"],
    )

    events = [entry for entry in compiled.abi if entry.get("type") == "event"]
    event_expectation = expected["events"]
    _assert_equal(name, "event count", len(events), event_expectation["count"])
    _assert_equal(
        name,
        "events",
        _json_sha256(events),
        event_expectation["canonical_sha256"],
    )
    constructors = [
        entry for entry in compiled.abi if entry.get("type") == "constructor"
    ]
    _assert_equal(name, "constructor", constructors, expected["constructor"])

    _assert_equal(
        name,
        "persistent storage layout",
        compiled.storage_layout,
        expected["storage_layout"],
    )
    _assert_equal(
        name,
        "transient storage layout",
        compiled.transient_storage_layout,
        expected["transient_storage_layout"],
    )
    _assert_equal(
        name, "immutable/code layout", compiled.code_layout, expected["code_layout"]
    )

    runtime_label = "runtime template"
    if deployed_binding is not None:
        runtime_label += " (full deployed-runtime identity bound)"
    elif expected.get("constructor_bound_runtime_template"):
        runtime_label += " (not a deployed-runtime identity; constructor immutables)"
    return (
        f"{name}: creation={len(compiled.creation)} "
        f"executable-prefix={len(creation_binding.executable_prefix)}/"
        f"{_sha256(creation_binding.executable_prefix)} "
        f"compiler-metadata={len(creation_binding.compiler_metadata)}/"
        f"{_sha256(creation_binding.compiler_metadata)} "
        f"{runtime_label}={len(compiled.runtime_template)} "
        f"headroom={headroom} optimize={compiled.effective_optimization} "
        f"integrity={compiled.integrity}"
    )


def _parse_source_overrides(values: Sequence[str]) -> Mapping[str, Path]:
    overrides: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise ArtifactCheckError(
                f"invalid --source-override {value!r}; expected Contract=path"
            )
        name, raw_path = value.split("=", 1)
        overrides[name] = Path(raw_path).resolve()
    return overrides


def check(
    expectations_path: Path,
    selected_contracts: Sequence[str],
    source_overrides: Mapping[str, Path],
    require_deployed_runtime_bindings: bool = False,
) -> Sequence[str]:
    expectations = json.loads(expectations_path.read_text())
    _assert_equal(
        "expectations", "schema_version", expectations.get("schema_version"), SCHEMA_VERSION
    )
    vyper = _vyper_path()
    version = _run([str(vyper), "--version"]).strip()
    _assert_equal(
        "compiler", "version", version, expectations["compiler"]["version"]
    )
    _assert_equal(
        "compiler",
        "artifact_recipe",
        expectations["compiler"]["artifact_recipe"],
        "vyper -p . -f bytecode,bytecode_runtime <file>",
    )

    contracts = expectations["contracts"]
    names = list(selected_contracts) if selected_contracts else list(contracts)
    unknown = sorted(set(names) - set(contracts))
    if unknown:
        raise ArtifactCheckError(f"unknown contracts: {', '.join(unknown)}")

    results = []
    for name in names:
        results.append(
            _check_contract(
                name,
                contracts[name],
                vyper=vyper,
                source_override=source_overrides.get(name),
                require_deployed_runtime_binding=(
                    require_deployed_runtime_bindings
                ),
            )
        )
    return results


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expectations",
        type=Path,
        default=DEFAULT_EXPECTATIONS,
        help="frozen expectations JSON",
    )
    parser.add_argument(
        "--contract",
        action="append",
        default=[],
        help="check one named contract (repeatable); default checks all",
    )
    parser.add_argument(
        "--source-override",
        action="append",
        default=[],
        help="negative-test source override as Contract=path",
    )
    parser.add_argument(
        "--require-deployed-runtime-bindings",
        action="store_true",
        help=(
            "fail if a constructor-immutable contract lacks a full deployed "
            "runtime binding"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        overrides = _parse_source_overrides(args.source_override)
        results = check(
            args.expectations.resolve(),
            args.contract,
            overrides,
            require_deployed_runtime_bindings=(
                args.require_deployed_runtime_bindings
            ),
        )
    except (ArtifactCheckError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"CONTRACT_ARTIFACTS_FAILED: {exc}", file=sys.stderr)
        return 1

    for result in results:
        print(result)
    print("CONTRACT_ARTIFACTS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
