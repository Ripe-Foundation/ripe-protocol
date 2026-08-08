#!/usr/bin/env python3
"""DRAFT — owner approval required before integration or use.

Build deterministic local reproduction evidence for the Robinhood Ledger
profile. This is not deployment evidence and performs no registration,
activation, live-network access, signing, or broadcasting.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import boa

from scripts.proposals import ledger_robinhood_profile as profile


BASELINE = "a86650b187c523f27c92f05bfe959d06840025a6"
ROOT = profile.ROOT
DEFAULT_OUTPUT = (
    ROOT
    / "docs"
    / "chains"
    / "rh"
    / "hardening"
    / "ledger-local-artifact-bundle.json"
)
ABI_PATH = ROOT / "scripts" / "abis" / "Ledger.json"
GENERATOR_PATH = Path(__file__).resolve()
LABEL = "local reproduction evidence, not deployment evidence"


class BundleBuildError(RuntimeError):
    """The local reproduction bundle could not be built safely."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_output(arguments: list[str]) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise BundleBuildError(
            f"git {' '.join(arguments)} failed: {detail}"
        )
    return completed.stdout


def resolve_builder_head(*, require_clean: bool) -> str:
    head = _git_output(["rev-parse", "HEAD"]).strip()
    if len(head) != 40 or any(char not in "0123456789abcdef" for char in head):
        raise BundleBuildError(f"invalid builder HEAD: {head!r}")
    if require_clean:
        status = _git_output(["status", "--short"])
        if status:
            raise BundleBuildError(
                "bundle generation requires a clean worktree; "
                f"git status --short was:\n{status}"
            )
        relative_generator = GENERATOR_PATH.relative_to(ROOT)
        tracked = _git_output(
            ["ls-files", "--error-unmatch", str(relative_generator)]
        ).strip()
        if tracked != str(relative_generator):
            raise BundleBuildError("generator is not tracked at builder_head")
    return head


def encode_constructor(arguments: list[str]) -> str:
    if len(arguments) != 3:
        raise BundleBuildError("Ledger constructor requires three arguments")
    encoded = bytearray()
    for value in arguments:
        try:
            raw = bytes.fromhex(value.removeprefix("0x"))
        except ValueError as exc:
            raise BundleBuildError(
                f"invalid constructor address: {value!r}"
            ) from exc
        if len(raw) != 20:
            raise BundleBuildError(
                f"constructor address is not 20 bytes: {value!r}"
            )
        encoded.extend(raw.rjust(32, b"\x00"))
    return "0x" + bytes(encoded).hex()


def _fresh_abi() -> list[dict[str, Any]]:
    vyper = Path(sys.executable).with_name("vyper")
    output = profile._run(
        [
            str(vyper),
            "-p",
            ".",
            "-f",
            "abi",
            str(profile.LEDGER_PATH.relative_to(ROOT)),
        ]
    )
    value = json.loads(output)
    if not isinstance(value, list):
        raise BundleBuildError("fresh Ledger ABI was not a list")
    return value


def build_bundle(
    *,
    builder_head: str | None = None,
    require_clean: bool = True,
) -> dict[str, Any]:
    if builder_head is None:
        builder_head = resolve_builder_head(require_clean=require_clean)
    elif require_clean:
        actual_head = resolve_builder_head(require_clean=True)
        if builder_head != actual_head:
            raise BundleBuildError(
                f"builder_head mismatch: expected {actual_head}, "
                f"got {builder_head}"
            )
    if len(builder_head) != 40:
        raise BundleBuildError("builder_head must be a literal 40-hex commit")

    manifest = profile.load_manifest()
    profile.validate_manifest(manifest)
    compiled = profile.compile_reviewed_ledger()
    deployed = profile.deploy_local_robinhood_profile(manifest)
    runtime = bytes(boa.env.get_code(deployed.ledger.address))
    if not runtime:
        raise BundleBuildError("local Ledger deployment has no runtime code")

    fresh_abi = _fresh_abi()
    committed_abi_bytes = ABI_PATH.read_bytes()
    committed_abi = json.loads(committed_abi_bytes)
    fresh_abi_canonical = json.dumps(
        fresh_abi,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    committed_abi_canonical = json.dumps(
        committed_abi,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    if fresh_abi_canonical != committed_abi_canonical:
        raise BundleBuildError("fresh and committed Ledger ABIs differ")

    arguments = manifest["constructor"]["ordered_arguments"]
    return {
        "abi": {
            "canonical_sha256": _sha256(fresh_abi_canonical),
            "committed_file_sha256": _sha256(committed_abi_bytes),
            "committed_path": "scripts/abis/Ledger.json",
        },
        "artifacts": {
            "creation_bytecode": {
                "sha256": _sha256(compiled.creation),
                "size": len(compiled.creation),
            },
            "immutable_bound_runtime": {
                "action_block_source_readback": (
                    deployed.ledger.ACTION_BLOCK_SOURCE()
                ),
                "sha256": _sha256(runtime),
                "size": len(runtime),
            },
            "runtime_template": {
                "deployed_runtime_identity": False,
                "sha256": _sha256(compiled.runtime_template),
                "size": len(compiled.runtime_template),
            },
        },
        "baseline": BASELINE,
        "builder_head": builder_head,
        "compiler": {
            "command": (
                "vyper -p . -f bytecode,bytecode_runtime "
                "contracts/data/Ledger.vy"
            ),
            "effective_optimization": "gas",
            "experimental_codegen": False,
            "transitive_compiler_input_integrity": compiled.integrity,
            "version": profile.PINNED_VYPER_VERSION,
        },
        "constructor": {
            "encoded_arguments": encode_constructor(arguments),
            "ordered_arguments": arguments,
        },
        "identity": {
            "profile_manifest_sha256": _sha256(
                profile.MANIFEST_PATH.read_bytes()
            ),
            "profile_name": manifest["profile"],
            "registry_input": manifest["inputs"]["ripe_hq"],
        },
        "label": LABEL,
        "schema_version": 1,
        "source": {
            "path": "contracts/data/Ledger.vy",
            "sha256": _sha256(profile.LEDGER_PATH.read_bytes()),
        },
        "status": "DRAFT — owner approval required before integration or use",
    }


def write_bundle(bundle: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(profile.canonical_json_bytes(bundle))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="bundle destination",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle = build_bundle(require_clean=True)
    write_bundle(bundle, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
