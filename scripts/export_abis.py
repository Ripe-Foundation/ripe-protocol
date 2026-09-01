"""Deterministically export production Vyper ABIs.

Unsupported Solidity inputs, output-name collisions, compile failures, and
stale checked outputs are all hard failures.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from vyper import compile_from_file_input
from vyper.compiler.input_bundle import FilesystemInputBundle


ROOT = Path(__file__).resolve().parents[1]
ABI_EXPORT_COMPLETION = ".abi-export-complete"
ABI_EXPORT_SCHEMA_VERSION = 1

# Test-only sources are excluded by directory. Importable modules are classified
# individually so the four standalone module ABIs already checked into the
# repository remain part of the deterministic export.
DEFAULT_EXCLUDE_DIRS = ("mock", "testing")
NON_STANDALONE_VYPER_SOURCES = frozenset(
    {
        "modules/DeptBasics.vy",
        "modules/TimeLock.vy",
        "priceSources/modules/PriceSourceData.vy",
        "registries/modules/AddressRegistry.vy",
        "tokens/modules/Erc4626Token.vy",
        "vaults/modules/BasicVault.vy",
        "vaults/modules/SharesVault.vy",
        "vaults/modules/StabVault.vy",
        "vaults/modules/VaultData.vy",
    }
)

# This source-less, block-clocked legacy output is explicitly preserved. It is
# allowed only for the repository's canonical contracts/output directory pair;
# stale outputs remain errors everywhere else.
REPOSITORY_LEGACY_OUTPUT_SHA256: Mapping[str, str] = {
    "DefaultsBaseSepolia.json": (
        "bcb820120926cc98370a05a54653179df55aa15d0e956bc19533ebb37b822fa0"
    ),
}
REPOSITORY_LEGACY_COMPILED_SHA256: Mapping[str, str] = {}


class AbiExportError(RuntimeError):
    """Raised when a deterministic ABI inventory cannot be produced."""


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _completion_bytes(expected: Mapping[str, bytes], status: str) -> bytes:
    value = {
        "schema_version": ABI_EXPORT_SCHEMA_VERSION,
        "status": status,
        "outputs": {
            name: hashlib.sha256(data).hexdigest()
            for name, data in sorted(expected.items())
        },
    }
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _completion_drift(
    output_dir: Path,
    expected: Mapping[str, bytes],
) -> tuple[str, ...]:
    path = output_dir / ABI_EXPORT_COMPLETION
    if not path.is_file() or path.is_symlink():
        return ("missing ABI export completion seal",)
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return ("invalid ABI export completion seal",)
    expected_value = json.loads(_completion_bytes(expected, "complete"))
    if value != expected_value:
        return ("stale or incomplete ABI export completion seal",)
    return ()


@dataclass(frozen=True)
class AbiExportReport:
    exported: tuple[Path, ...]
    skipped: tuple[Path, ...]


def _is_excluded(path: Path, contracts_dir: Path, exclude_dirs: set[str]) -> bool:
    relative = path.relative_to(contracts_dir)
    return (
        any(part in exclude_dirs for part in relative.parts)
        or relative.as_posix() in NON_STANDALONE_VYPER_SOURCES
    )


def _legacy_output_hashes(
    contracts_dir: Path,
    output_dir: Path,
    legacy_output_sha256: Mapping[str, str] | None,
) -> Mapping[str, str]:
    if legacy_output_sha256 is not None:
        return legacy_output_sha256
    if (
        contracts_dir.resolve() == (ROOT / "contracts").resolve()
        and output_dir.resolve() == (ROOT / "scripts" / "abis").resolve()
    ):
        return REPOSITORY_LEGACY_OUTPUT_SHA256
    return {}


def _legacy_compiled_hashes(
    contracts_dir: Path, output_dir: Path
) -> Mapping[str, str]:
    if (
        contracts_dir.resolve() == (ROOT / "contracts").resolve()
        and output_dir.resolve() == (ROOT / "scripts" / "abis").resolve()
    ):
        return REPOSITORY_LEGACY_COMPILED_SHA256
    return {}


def _legacy_compilation_drift(
    expected: Mapping[str, bytes],
    compiled_sha256: Mapping[str, str],
) -> tuple[str, ...]:
    failures = []
    for name, expected_sha256 in sorted(compiled_sha256.items()):
        data = expected.get(name)
        if data is None:
            failures.append(f"missing legacy ABI source output: {name}")
        elif hashlib.sha256(data).hexdigest() != expected_sha256:
            failures.append(f"changed compiled ABI for legacy output: {name}")
    return tuple(failures)


def discover_contracts(
    contracts_dir: Path,
    exclude_dirs: Sequence[str] | None = None,
) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    contracts_dir = contracts_dir.resolve()
    if not contracts_dir.is_dir():
        raise AbiExportError(f"contracts directory does not exist: {contracts_dir}")

    excluded = set(exclude_dirs or DEFAULT_EXCLUDE_DIRS)
    vyper_files = tuple(
        sorted(
            (
                path
                for path in contracts_dir.rglob("*.vy")
                if not _is_excluded(path, contracts_dir, excluded)
            ),
            key=lambda path: path.relative_to(contracts_dir).as_posix(),
        )
    )
    skipped = tuple(
        sorted(
            (
                path
                for path in contracts_dir.rglob("*.vy")
                if _is_excluded(path, contracts_dir, excluded)
            ),
            key=lambda path: path.relative_to(contracts_dir).as_posix(),
        )
    )

    solidity_files = tuple(
        sorted(
            (
                path
                for path in contracts_dir.rglob("*.sol")
                if not _is_excluded(path, contracts_dir, excluded)
            ),
            key=lambda path: path.relative_to(contracts_dir).as_posix(),
        )
    )
    if solidity_files:
        names = ", ".join(
            path.relative_to(contracts_dir).as_posix() for path in solidity_files
        )
        raise AbiExportError(f"unsupported Solidity ABI input(s): {names}")

    outputs: dict[str, Path] = {}
    for path in vyper_files:
        output_name = f"{path.stem}.json"
        if output_name in outputs:
            first = outputs[output_name].relative_to(contracts_dir).as_posix()
            second = path.relative_to(contracts_dir).as_posix()
            raise AbiExportError(
                f"ABI output collision for {output_name}: {first}, {second}"
            )
        outputs[output_name] = path
    return vyper_files, skipped


def _compile_abi(path: Path, contracts_dir: Path) -> bytes:
    search_root = contracts_dir.resolve().parent
    bundle = FilesystemInputBundle([search_root])
    relative_path = path.resolve().relative_to(search_root)
    try:
        file_input = bundle.load_file(relative_path)
        result = compile_from_file_input(
            file_input,
            input_bundle=bundle,
            output_formats=("abi",),
        )
    except Exception as exc:
        raise AbiExportError(
            f"Vyper ABI compilation failed for "
            f"{path.relative_to(contracts_dir).as_posix()}: {exc}"
        ) from exc
    # Preserve the historical checked-in serialization exactly: compiler order,
    # two-space indentation, and no trailing newline.
    return json.dumps(result["abi"], ensure_ascii=True, indent=2).encode()


def build_abi_outputs(
    contracts_dir: Path,
    exclude_dirs: Sequence[str] | None = None,
) -> tuple[Mapping[str, bytes], tuple[Path, ...]]:
    contracts_dir = contracts_dir.resolve()
    contract_files, skipped = discover_contracts(contracts_dir, exclude_dirs)
    outputs = {
        f"{path.stem}.json": _compile_abi(path, contracts_dir)
        for path in contract_files
    }
    return outputs, skipped


def _output_drift(
    output_dir: Path,
    expected: Mapping[str, bytes],
    legacy_output_sha256: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    actual_names = (
        {path.name for path in output_dir.glob("*.json")}
        if output_dir.is_dir()
        else set()
    )
    legacy = legacy_output_sha256 or {}
    expected_names = set(expected) | set(legacy)
    failures = [
        *(
            f"missing ABI output: {name}"
            for name in sorted(expected_names - actual_names)
        ),
        *(
            f"stale ABI output: {name}"
            for name in sorted(actual_names - expected_names)
        ),
    ]
    for name in sorted(actual_names & set(expected) - set(legacy)):
        if (output_dir / name).read_bytes() != expected[name]:
            failures.append(f"changed ABI output: {name}")
    for name, expected_sha256 in sorted(legacy.items()):
        path = output_dir / name
        if (
            path.is_file()
            and hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256
        ):
            failures.append(f"changed legacy ABI output: {name}")
    return tuple(failures)


def check_abis(
    contracts_dir: Path,
    output_dir: Path,
    exclude_dirs: Sequence[str] | None = None,
    legacy_output_sha256: Mapping[str, str] | None = None,
) -> AbiExportReport:
    expected, skipped = build_abi_outputs(contracts_dir, exclude_dirs)
    legacy = _legacy_output_hashes(
        contracts_dir, output_dir, legacy_output_sha256
    )
    generated = {name: data for name, data in expected.items() if name not in legacy}
    failures = (
        *_output_drift(output_dir, expected, legacy),
        *_legacy_compilation_drift(
            expected, _legacy_compiled_hashes(contracts_dir, output_dir)
        ),
        *_completion_drift(output_dir, generated),
    )
    if failures:
        raise AbiExportError("; ".join(failures))
    return AbiExportReport(
        exported=tuple(
            output_dir / name for name in sorted(set(expected) | set(legacy))
        ),
        skipped=skipped,
    )


def export_abis(
    contracts_dir: Path,
    output_dir: Path,
    exclude_dirs: Sequence[str] | None = None,
    legacy_output_sha256: Mapping[str, str] | None = None,
) -> AbiExportReport:
    contracts_dir = contracts_dir.resolve()
    output_dir = output_dir.resolve()
    expected, skipped = build_abi_outputs(contracts_dir, exclude_dirs)
    legacy = _legacy_output_hashes(
        contracts_dir, output_dir, legacy_output_sha256
    )
    generated = {name: data for name, data in expected.items() if name not in legacy}
    compiled_legacy_failures = _legacy_compilation_drift(
        expected, _legacy_compiled_hashes(contracts_dir, output_dir)
    )
    if compiled_legacy_failures:
        raise AbiExportError("; ".join(compiled_legacy_failures))

    stale = (
        sorted(
            path.name
            for path in output_dir.glob("*.json")
            if path.name not in expected and path.name not in legacy
        )
        if output_dir.is_dir()
        else []
    )
    if stale:
        raise AbiExportError(f"stale ABI output(s): {', '.join(stale)}")

    legacy_failures = []
    for name, expected_sha256 in sorted(legacy.items()):
        path = output_dir / name
        if not path.is_file():
            legacy_failures.append(f"missing ABI output: {name}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
            legacy_failures.append(f"changed legacy ABI output: {name}")
    if legacy_failures:
        raise AbiExportError("; ".join(legacy_failures))

    if expected or legacy:
        output_dir.mkdir(parents=True, exist_ok=True)
    completion = output_dir / ABI_EXPORT_COMPLETION
    _atomic_write_bytes(completion, _completion_bytes(generated, "in_progress"))
    for name, data in sorted(generated.items()):
        _atomic_write_bytes(output_dir / name, data)
    _atomic_write_bytes(completion, _completion_bytes(generated, "complete"))

    return AbiExportReport(
        exported=tuple(
            output_dir / name for name in sorted(set(expected) | set(legacy))
        ),
        skipped=skipped,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("scripts/abis"),
        help="output directory (default: scripts/abis)",
    )
    parser.add_argument(
        "--contracts-dir",
        "-c",
        type=Path,
        default=Path("contracts"),
        help="contracts directory (default: contracts)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if an output is missing, stale, or byte-different",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = (
            check_abis(args.contracts_dir, args.output_dir)
            if args.check
            else export_abis(args.contracts_dir, args.output_dir)
        )
    except (AbiExportError, OSError) as exc:
        print(f"ABI_EXPORT_FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"Exported {len(report.exported)} ABIs to {args.output_dir}")
    print(f"Skipped {len(report.skipped)} excluded Vyper contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
