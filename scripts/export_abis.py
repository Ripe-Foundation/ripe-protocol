"""Deterministically export production Vyper ABIs.

Unsupported Solidity inputs, output-name collisions, compile failures, and
stale checked outputs are all hard failures.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from vyper import compile_from_file_input
from vyper.compiler.input_bundle import FilesystemInputBundle


ROOT = Path(__file__).resolve().parents[1]

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
    "Deleverage.json": (
        "d0480bf6b0d7d05c461b33b31dd0e85b48135fa66d850a4c8526e0d9fefaea8d"
    ),
    "EndaomentPSM.json": (
        "d6bab0783a4f1b98432d45b47d527f29599194c77bc90e772eb5f9f56ce214c0"
    ),
    "SwitchboardAlpha.json": (
        "73cf0c3180d4fe27049b11e27eca717995af0fe778ab05daed6275c4f85fb49b"
    ),
    "wsuperOETHbPrices.json": (
        "dbdcb0be1bd0bdc163643a57571efbb141caa167739f2471c514611585134beb"
    ),
}
REPOSITORY_LEGACY_COMPILED_SHA256: Mapping[str, str] = {
    "Deleverage.json": (
        "7de1944637565f5640169b879a13705706332cd171ae41579c45dfe5da72cb43"
    ),
    "EndaomentPSM.json": (
        "683e36ca7bf48f002afcb80d06dcb6a9540323cadc0647650c7ff3ddb9d7bec0"
    ),
    "SwitchboardAlpha.json": (
        "e5e33b9fd69ca649b3a7035f6f9f9afb3da88b80b57724907af388dce6edc747"
    ),
    "wsuperOETHbPrices.json": (
        "9fa66465471bfe016db2baec84a7caab1b7b4e49ab59e7aece531319d1956147"
    ),
}


class AbiExportError(RuntimeError):
    """Raised when a deterministic ABI inventory cannot be produced."""


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
    failures = (
        *_output_drift(output_dir, expected, legacy),
        *_legacy_compilation_drift(
            expected, _legacy_compiled_hashes(contracts_dir, output_dir)
        ),
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

    if expected:
        output_dir.mkdir(parents=True, exist_ok=True)
    for name in sorted(expected):
        if name in legacy:
            continue
        (output_dir / name).write_bytes(expected[name])

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
    except AbiExportError as exc:
        print(f"ABI_EXPORT_FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"Exported {len(report.exported)} ABIs to {args.output_dir}")
    print(f"Skipped {len(report.skipped)} excluded Vyper contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
