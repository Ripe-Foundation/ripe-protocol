#!/usr/bin/env python3
"""DRAFT — owner approval required before integration or use.

Canonical manifest-driven local-Boa profiles for the current five-argument
Lootbox constructor. This module does not migrate, register, enable, sign, or
broadcast anything.
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
from eth_utils import keccak

from scripts.proposals import ledger_robinhood_profile as shared


ROOT = shared.ROOT
MANIFEST_PATH = Path(__file__).with_name("lootbox-deployment-profiles.json")
EXPECTATIONS_PATH = ROOT / "config" / "contract-artifact-expectations.json"
LOOTBOX_PATH = ROOT / "contracts" / "core" / "Lootbox.vy"
PINNED_VYPER_VERSION = shared.PINNED_VYPER_VERSION
CONSTRUCTOR_ORDER = (
    "ripe_hq",
    "minimum_send_floor",
    "underscore_send_interval",
    "deposit_rewards_amount",
    "yield_bonus_amount",
)
POSTURE_RULES = {
    "base_preserving_disabled": {
        "deposit_rewards_amount": 0,
        "minimum_send_floor": 43_200,
        "underscore_send_interval": 0,
        "semantics": (
            "Base-preserving DISABLED: floor 43_200, interval 0, "
            "rewards flag false, stored amounts zero"
        ),
        "yield_bonus_amount": 0,
    },
    "base_preserving_enabled": {
        "deposit_rewards_amount": 879_534_349_288_889_048,
        "minimum_send_floor": 43_200,
        "underscore_send_interval": 43_200,
        "semantics": (
            "Base-preserving ENABLED: floor 43_200, interval 43_200, "
            "nonzero placeholder amounts, rewards flag true"
        ),
        "yield_bonus_amount": 676_534_693_169_268_285,
    },
    "robinhood": {
        "deposit_rewards_amount": 0,
        "minimum_send_floor": 7_200,
        "underscore_send_interval": 0,
        "semantics": (
            "Robinhood: floor 7200, interval 0, rewards flag false, "
            "stored amounts zero"
        ),
        "yield_bonus_amount": 0,
    },
}
REQUIRED_EVIDENCE = frozenset(
    {
        "deposit_rewards_amount_readback",
        "has_rewards_readback",
        "minimum_send_interval_readback",
        "ripe_hq_readback",
        "send_interval_readback",
        "yield_bonus_amount_readback",
    }
)


class LootboxProfileError(RuntimeError):
    """The draft Lootbox profile or its post-deploy evidence is invalid."""


@dataclass(frozen=True)
class CompiledLootbox:
    creation: bytes
    runtime_template: bytes
    integrity: str


@dataclass(frozen=True)
class LocalPostureDeployment:
    contract: Any
    posture: str
    arguments: tuple[Any, ...]
    evidence: Mapping[str, bool]
    compiled: CompiledLootbox


def deterministic_placeholder_amount(label: str) -> int:
    return int.from_bytes(keccak(text=label), "big") % 10**18 + 1


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
        raise LootboxProfileError(
            f"command failed ({completed.returncode}): "
            f"{' '.join(command)}: {detail}"
        )
    return completed.stdout


def load_manifest(path: Path = MANIFEST_PATH) -> Mapping[str, Any]:
    raw = path.read_bytes()
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LootboxProfileError(f"invalid profile JSON: {exc}") from exc
    if raw != shared.canonical_json_bytes(manifest):
        raise LootboxProfileError(
            "profile manifest is not canonical sorted JSON + LF"
        )
    return manifest


def ordered_arguments(
    manifest: Mapping[str, Any],
    posture: str,
) -> tuple[Any, ...]:
    try:
        inputs = manifest["postures"][posture]["inputs"]
        ripe_hq = manifest["shared_inputs"]["ripe_hq"]["value"]
    except (KeyError, TypeError) as exc:
        raise LootboxProfileError(f"missing posture inputs: {posture}") from exc
    values = {"ripe_hq": ripe_hq}
    values.update({name: entry["value"] for name, entry in inputs.items()})
    try:
        return tuple(values[name] for name in manifest["constructor_order"])
    except KeyError as exc:
        raise LootboxProfileError(
            f"constructor input missing: {exc.args[0]}"
        ) from exc


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema_version") != 1:
        raise LootboxProfileError("unsupported profile schema")
    if manifest.get("status") != (
        "DRAFT — owner approval required before integration or use"
    ):
        raise LootboxProfileError("missing draft status")
    if tuple(manifest.get("constructor_order", ())) != CONSTRUCTOR_ORDER:
        raise LootboxProfileError("five-argument constructor order mismatch")

    ripe_hq = manifest.get("shared_inputs", {}).get("ripe_hq", {})
    label = "rh-lootbox-profile:ripe-hq"
    if ripe_hq != {
        "approval_status": "unapproved_placeholder",
        "label": label,
        "value": shared.deterministic_placeholder_address(label),
    }:
        raise LootboxProfileError("RipeHq placeholder mismatch")

    postures = manifest.get("postures")
    if not isinstance(postures, Mapping) or set(postures) != set(POSTURE_RULES):
        raise LootboxProfileError("posture set mismatch")
    for posture, rule in POSTURE_RULES.items():
        entry = postures[posture]
        if entry.get("semantics") != rule["semantics"]:
            raise LootboxProfileError(f"{posture} semantics label mismatch")
        inputs = entry.get("inputs")
        if not isinstance(inputs, Mapping) or set(inputs) != set(
            CONSTRUCTOR_ORDER[1:]
        ):
            raise LootboxProfileError(f"{posture} input set mismatch")
        for name in ("minimum_send_floor", "underscore_send_interval"):
            if inputs[name] != {
                "approval_status": "owner_approved_profile_value",
                "value": rule[name],
            }:
                raise LootboxProfileError(f"{posture} {name} mismatch")
        for name in ("deposit_rewards_amount", "yield_bonus_amount"):
            if inputs[name] != {
                "approval_status": "unapproved_placeholder",
                "value": rule[name],
            }:
                raise LootboxProfileError(f"{posture} {name} mismatch")
        if ordered_arguments(manifest, posture) != (
            ripe_hq["value"],
            rule["minimum_send_floor"],
            rule["underscore_send_interval"],
            rule["deposit_rewards_amount"],
            rule["yield_bonus_amount"],
        ):
            raise LootboxProfileError(f"{posture} argument decoding mismatch")


def compile_reviewed_lootbox() -> CompiledLootbox:
    expectations = json.loads(EXPECTATIONS_PATH.read_text())["contracts"][
        "Lootbox"
    ]
    source = LOOTBOX_PATH.read_bytes()
    if _sha256(source) != expectations["source_sha256"]:
        raise LootboxProfileError("reviewed Lootbox source identity mismatch")
    if b"# pragma optimize codesize" not in source:
        raise LootboxProfileError("Lootbox codesize pragma is missing")
    if expectations["compiler_settings"] != {
        "experimental_codegen": False,
        "optimize": "codesize",
    }:
        raise LootboxProfileError("Lootbox compiler settings mismatch")

    vyper = Path(sys.executable).with_name("vyper")
    if not vyper.is_file():
        raise LootboxProfileError(f"pinned-environment vyper missing: {vyper}")
    version = _run([str(vyper), "--version"]).strip()
    if version != PINNED_VYPER_VERSION:
        raise LootboxProfileError(
            f"Vyper version mismatch: expected {PINNED_VYPER_VERSION}, "
            f"got {version}"
        )

    # Never pass -O: the source pragma owns the codesize setting.
    output = _run(
        [
            str(vyper),
            "-p",
            ".",
            "-f",
            "bytecode,bytecode_runtime",
            str(LOOTBOX_PATH.relative_to(ROOT)),
        ]
    )
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if len(lines) != 2:
        raise LootboxProfileError("Vyper did not emit two Lootbox artifacts")
    try:
        creation = bytes.fromhex(lines[0].removeprefix("0x"))
        runtime_template = bytes.fromhex(lines[1].removeprefix("0x"))
    except ValueError as exc:
        raise LootboxProfileError(
            "Vyper emitted non-hex Lootbox artifacts"
        ) from exc
    integrity = _run(
        [
            str(vyper),
            "-p",
            ".",
            "-f",
            "integrity",
            str(LOOTBOX_PATH.relative_to(ROOT)),
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
            raise LootboxProfileError(
                f"reviewed Lootbox {label} mismatch: "
                f"expected {expected}, got {actual}"
            )
    return CompiledLootbox(creation, runtime_template, integrity)


def _require_complete_evidence(evidence: Mapping[str, bool]) -> None:
    if set(evidence) != REQUIRED_EVIDENCE:
        raise LootboxProfileError(
            "incomplete Lootbox post-deploy evidence: "
            f"expected {sorted(REQUIRED_EVIDENCE)}, got {sorted(evidence)}"
        )
    failed = sorted(name for name, passed in evidence.items() if not passed)
    if failed:
        raise LootboxProfileError(
            f"Lootbox post-deploy assertions failed: {failed}"
        )


def deploy_local_posture(
    posture: str,
    *,
    manifest: Mapping[str, Any] | None = None,
    compiled: CompiledLootbox | None = None,
) -> LocalPostureDeployment:
    selected = manifest or load_manifest()
    validate_manifest(selected)
    compiled = compiled or compile_reviewed_lootbox()
    arguments = ordered_arguments(selected, posture)

    boa.loads(
        shared.RIPE_HQ_DOUBLE_SOURCE,
        name=f"draft_lootbox_{posture}_ripe_hq",
        override_address=arguments[0],
    )
    contract = boa.load(
        LOOTBOX_PATH,
        *arguments,
        name=f"draft_lootbox_{posture}",
    )
    enabled = arguments[2] != 0
    expected_deposit = arguments[3] if enabled else 0
    expected_yield = arguments[4] if enabled else 0
    evidence = {
        "deposit_rewards_amount_readback": (
            contract.undyDepositRewardsAmount() == expected_deposit
        ),
        "has_rewards_readback": (
            contract.hasUnderscoreRewards() is enabled
        ),
        "minimum_send_interval_readback": (
            contract.minUnderscoreSendInterval() == arguments[1]
        ),
        "ripe_hq_readback": contract.getRipeHq() == arguments[0],
        "send_interval_readback": (
            contract.underscoreSendInterval() == arguments[2]
        ),
        "yield_bonus_amount_readback": (
            contract.undyYieldBonusAmount() == expected_yield
        ),
    }
    _require_complete_evidence(evidence)
    return LocalPostureDeployment(
        contract,
        posture,
        arguments,
        evidence,
        compiled,
    )


def main() -> int:
    manifest = load_manifest()
    compiled = compile_reviewed_lootbox()
    result = {}
    for posture in POSTURE_RULES:
        deployment = deploy_local_posture(
            posture,
            manifest=manifest,
            compiled=compiled,
        )
        result[posture] = {
            "arguments": deployment.arguments,
            "evidence": deployment.evidence,
        }
    sys.stdout.buffer.write(shared.canonical_json_bytes(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
