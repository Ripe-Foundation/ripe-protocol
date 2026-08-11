#!/usr/bin/env python3
"""DRAFT — owner approval required before integration or use.

Executable local-Boa proposal for the Robinhood Ledger constructor profile.
This module neither registers nor activates the resulting contract.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import boa
from eth_utils import keccak, to_checksum_address


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path(__file__).with_name("ledger-robinhood-profile.json")
EXPECTATIONS_PATH = ROOT / "config" / "contract-artifact-expectations.json"
LEDGER_PATH = ROOT / "contracts" / "data" / "Ledger.vy"

ARB_SYS = to_checksum_address(
    "0x0000000000000000000000000000000000000064"
)
ZERO_ADDRESS = to_checksum_address(
    "0x0000000000000000000000000000000000000000"
)
PINNED_VYPER_VERSION = "0.4.3+commit.bff19ea2"
PLACEHOLDER_LABELS = {
    "defaults": "rh-ledger-profile:defaults",
    "ripe_hq": "rh-ledger-profile:ripe-hq",
}
REQUIRED_EVIDENCE = frozenset(
    {
        "action_block_source_readback",
        "constructor_defaults_readback",
        "placeholder_code_readback",
        "ripe_hq_readback",
    }
)
RIPE_HQ_DOUBLE_SOURCE = """# DRAFT — owner approval required before integration or use.
# Local-only deterministic RipeHq double for deployment-profile evidence.
# @version 0.4.3

@view
@external
def getAddr(_regId: uint256) -> address:
    return empty(address)

@view
@external
def isValidAddr(_addr: address) -> bool:
    return False
"""
DEFAULTS_DOUBLE_SOURCE = """# DRAFT — owner approval required before integration or use.
# Local-only Defaults-compatible double for Ledger construction.
# @version 0.4.3

@view
@external
def ripeAvailForRewards() -> uint256:
    return 11

@view
@external
def ripeAvailForHr() -> uint256:
    return 22

@view
@external
def ripeAvailForBonds() -> uint256:
    return 33
"""
ARB_SYS_DOUBLE_SOURCE = """# DRAFT — owner approval required before integration or use.
# Local-only deterministic ArbSys double installed at exact address 0x64.
# @version 0.4.3

actionBlock: uint256

@deploy
def __init__(_actionBlock: uint256):
    self.actionBlock = _actionBlock

@view
@external
def arbBlockNumber() -> uint256:
    return self.actionBlock

@external
def setActionBlock(_actionBlock: uint256):
    self.actionBlock = _actionBlock
"""


class ProfileGateError(RuntimeError):
    """The draft profile is malformed or its local post-deploy gate failed."""


@dataclass(frozen=True)
class CompiledLedger:
    creation: bytes
    runtime_template: bytes
    integrity: str


@dataclass(frozen=True)
class LocalProfileDeployment:
    ledger: Any
    manifest: Mapping[str, Any]
    compiled: CompiledLedger
    evidence: Mapping[str, bool]


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode()


def deterministic_placeholder_address(label: str) -> str:
    return to_checksum_address(keccak(text=label)[-20:])


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ProfileGateError(
            f"command failed ({completed.returncode}): "
            f"{' '.join(command)}: {detail}"
        )
    return completed.stdout


def load_manifest(path: Path = MANIFEST_PATH) -> Mapping[str, Any]:
    raw = path.read_bytes()
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProfileGateError(f"invalid profile JSON: {exc}") from exc
    if raw != canonical_json_bytes(manifest):
        raise ProfileGateError("profile manifest is not canonical sorted JSON + LF")
    return manifest


def _expected_source_metadata() -> dict[str, Any]:
    expectations = json.loads(EXPECTATIONS_PATH.read_text())["contracts"][
        "Ledger"
    ]
    return {
        "compiler_settings": expectations["compiler_settings"],
        "effective_optimization": expectations["effective_optimization"],
        "path": str(LEDGER_PATH.relative_to(ROOT)),
        "sha256": expectations["source_sha256"],
        "transitive_compiler_input_integrity": expectations[
            "transitive_compiler_input_integrity"
        ],
        "vyper_version": PINNED_VYPER_VERSION,
    }


def validate_robinhood_source(source: str) -> str:
    try:
        normalized = to_checksum_address(source)
    except ValueError as exc:
        raise ProfileGateError("invalid action-block source address") from exc
    if normalized != ARB_SYS:
        raise ProfileGateError(
            "Robinhood profile requires exact action-block source 0x64"
        )
    return normalized


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema_version") != 1:
        raise ProfileGateError("unsupported profile schema")
    if manifest.get("status") != (
        "DRAFT — owner approval required before integration or use"
    ):
        raise ProfileGateError("missing draft status")
    if manifest.get("profile") != "robinhood":
        raise ProfileGateError("not the Robinhood Ledger profile")
    if manifest.get("source") != _expected_source_metadata():
        raise ProfileGateError(
            "profile source metadata does not match governed expectations"
        )

    constructor = manifest.get("constructor", {})
    source = validate_robinhood_source(
        constructor.get("action_block_source", ZERO_ADDRESS)
    )
    ordered = constructor.get("ordered_arguments")
    if not isinstance(ordered, list) or len(ordered) != 3:
        raise ProfileGateError("Ledger constructor requires three ordered arguments")

    inputs = manifest.get("inputs")
    if not isinstance(inputs, Mapping):
        raise ProfileGateError("profile inputs must be an object")
    expected_addresses = {
        name: deterministic_placeholder_address(label)
        for name, label in PLACEHOLDER_LABELS.items()
    }
    for name, address in expected_addresses.items():
        entry = inputs.get(name)
        if not isinstance(entry, Mapping):
            raise ProfileGateError(f"missing {name} input")
        if entry.get("label") != PLACEHOLDER_LABELS[name]:
            raise ProfileGateError(f"{name} placeholder label mismatch")
        if entry.get("address") != address:
            raise ProfileGateError(f"{name} placeholder address mismatch")
        if entry.get("approval_status") != "unapproved_placeholder":
            raise ProfileGateError(f"{name} approval status mismatch")

    expected_order = [
        expected_addresses["ripe_hq"],
        expected_addresses["defaults"],
        source,
    ]
    if ordered != expected_order:
        raise ProfileGateError("constructor order/value mismatch")
    if manifest.get("required_post_deploy_evidence") != sorted(
        REQUIRED_EVIDENCE
    ):
        raise ProfileGateError("post-deploy evidence set is incomplete")


def compile_reviewed_ledger() -> CompiledLedger:
    expectations = json.loads(EXPECTATIONS_PATH.read_text())["contracts"][
        "Ledger"
    ]
    if _sha256(LEDGER_PATH.read_bytes()) != expectations["source_sha256"]:
        raise ProfileGateError("reviewed Ledger source identity mismatch")
    if expectations["effective_optimization"] != "gas":
        raise ProfileGateError("Ledger optimization expectation is not gas")
    if expectations["compiler_settings"] != {
        "experimental_codegen": False,
        "optimize": "gas",
    }:
        raise ProfileGateError("Ledger compiler settings mismatch")

    vyper = Path(sys.executable).with_name("vyper")
    if not vyper.is_file():
        raise ProfileGateError(f"pinned-environment vyper missing: {vyper}")
    version = _run([str(vyper), "--version"]).strip()
    if version != PINNED_VYPER_VERSION:
        raise ProfileGateError(
            f"Vyper version mismatch: expected {PINNED_VYPER_VERSION}, got {version}"
        )

    # Never pass -O: Ledger has no pragma, so Vyper's default gas mode governs.
    output = _run(
        [
            str(vyper),
            "-p",
            ".",
            "-f",
            "bytecode,bytecode_runtime",
            str(LEDGER_PATH.relative_to(ROOT)),
        ]
    )
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if len(lines) != 2:
        raise ProfileGateError("Vyper did not emit two Ledger artifacts")
    try:
        creation = bytes.fromhex(lines[0].removeprefix("0x"))
        runtime_template = bytes.fromhex(lines[1].removeprefix("0x"))
    except ValueError as exc:
        raise ProfileGateError("Vyper emitted non-hex Ledger artifacts") from exc
    integrity = _run(
        [
            str(vyper),
            "-p",
            ".",
            "-f",
            "integrity",
            str(LEDGER_PATH.relative_to(ROOT)),
        ]
    ).strip()

    artifacts = expectations["artifacts"]
    checks = {
        "creation SHA-256": (
            _sha256(creation),
            artifacts["creation_sha256"],
        ),
        "runtime-template SHA-256": (
            _sha256(runtime_template),
            artifacts["runtime_template_sha256"],
        ),
        "compiler-input integrity": (
            integrity,
            expectations["transitive_compiler_input_integrity"],
        ),
    }
    for label, (actual, expected) in checks.items():
        if actual != expected:
            raise ProfileGateError(
                f"reviewed Ledger {label} mismatch: "
                f"expected {expected}, got {actual}"
            )
    return CompiledLedger(creation, runtime_template, integrity)


def _install_local_doubles(manifest: Mapping[str, Any]) -> None:
    inputs = manifest["inputs"]
    boa.loads(
        RIPE_HQ_DOUBLE_SOURCE,
        name="draft_profile_ripe_hq",
        override_address=inputs["ripe_hq"]["address"],
    )
    boa.loads(
        DEFAULTS_DOUBLE_SOURCE,
        name="draft_profile_defaults",
        override_address=inputs["defaults"]["address"],
    )
    boa.loads(
        ARB_SYS_DOUBLE_SOURCE,
        7_777,
        name="draft_profile_arb_sys",
        override_address=ARB_SYS,
    )


def _post_deploy_assertions(ledger: Any, manifest: Mapping[str, Any]) -> dict[str, bool]:
    inputs = manifest["inputs"]
    return {
        "constructor_defaults_readback": (
            ledger.ripeAvailForRewards() == 11
            and ledger.ripeAvailForHr() == 22
            and ledger.ripeAvailForBonds() == 33
        ),
        "placeholder_code_readback": (
            bool(boa.env.get_code(inputs["ripe_hq"]["address"]))
            and bool(boa.env.get_code(inputs["defaults"]["address"]))
            and bool(boa.env.get_code(ARB_SYS))
        ),
        "ripe_hq_readback": (
            ledger.getRipeHq() == inputs["ripe_hq"]["address"]
        ),
    }


def _require_complete_evidence(evidence: Mapping[str, bool]) -> None:
    if set(evidence) != REQUIRED_EVIDENCE:
        missing = sorted(REQUIRED_EVIDENCE - set(evidence))
        extra = sorted(set(evidence) - REQUIRED_EVIDENCE)
        raise ProfileGateError(
            f"incomplete profile evidence: missing={missing}, extra={extra}"
        )
    failed = sorted(name for name, passed in evidence.items() if not passed)
    if failed:
        raise ProfileGateError(f"profile post-deploy assertions failed: {failed}")


def deploy_local_robinhood_profile(
    manifest: Mapping[str, Any] | None = None,
) -> LocalProfileDeployment:
    selected = manifest or load_manifest()
    validate_manifest(selected)
    compiled = compile_reviewed_ledger()
    _install_local_doubles(selected)

    arguments = selected["constructor"]["ordered_arguments"]
    ledger = boa.load(
        LEDGER_PATH,
        *arguments,
        name="draft_robinhood_ledger",
    )

    evidence: dict[str, bool] = {}
    evidence["action_block_source_readback"] = (
        ledger.ACTION_BLOCK_SOURCE() == ARB_SYS
    )
    evidence.update(_post_deploy_assertions(ledger, selected))
    _require_complete_evidence(evidence)
    return LocalProfileDeployment(ledger, selected, compiled, evidence)


def main() -> int:
    deployment = deploy_local_robinhood_profile()
    output = {
        "action_block_source": deployment.ledger.ACTION_BLOCK_SOURCE(),
        "evidence": deployment.evidence,
        "label": "local reproduction evidence, not deployment evidence",
        "ledger": deployment.ledger.address,
    }
    sys.stdout.buffer.write(canonical_json_bytes(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
