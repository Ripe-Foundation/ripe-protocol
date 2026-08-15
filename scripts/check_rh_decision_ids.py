#!/usr/bin/env python3
"""Validate RH decision parity and concurrent integration-set allocations."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import re
import subprocess
from typing import Mapping

import yaml


ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs/chains/rh/decision-register.md"
STATUS = ROOT / "docs/chains/rh/status.yaml"
REGISTER_IN_REPO = "docs/chains/rh/decision-register.md"
HEADING_RE = re.compile(r"^### (RH-D\d{3}) — (.+)$", re.MULTILINE)
FULLY_RETIRED_DECISION_IDS = frozenset({"RH-D026"})


class DecisionIdError(RuntimeError):
    pass


def parse_register(text: str, label: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for decision_id, title in HEADING_RE.findall(text):
        if decision_id in pairs:
            raise DecisionIdError(
                f"{label}: duplicate decision ID {decision_id}: "
                f"{pairs[decision_id]!r} and {title!r}"
            )
        pairs[decision_id] = title
    if not pairs:
        raise DecisionIdError(f"{label}: no RH decision headings found")
    return pairs


def parse_status(path: Path) -> dict[str, str]:
    data = yaml.safe_load(path.read_text())
    rows = data.get("decisions")
    if not isinstance(rows, list):
        raise DecisionIdError(f"{path}: decisions must be a list")
    pairs: dict[str, str] = {}
    for row in rows:
        decision_id = row.get("id") if isinstance(row, dict) else None
        title = row.get("title") if isinstance(row, dict) else None
        if not isinstance(decision_id, str) or not isinstance(title, str):
            raise DecisionIdError(f"{path}: invalid decision row {row!r}")
        if decision_id in pairs:
            raise DecisionIdError(f"{path}: duplicate decision ID {decision_id}")
        pairs[decision_id] = title
    return pairs


def require_exact_parity(register: Mapping[str, str], status: Mapping[str, str]) -> None:
    if register == status:
        return
    missing = sorted(set(register) - set(status))
    extra = sorted(set(status) - set(register))
    mismatched = sorted(
        decision_id
        for decision_id in set(register) & set(status)
        if register[decision_id] != status[decision_id]
    )
    raise DecisionIdError(
        "decision register/status parity failure: "
        f"missing={missing}, extra={extra}, title_mismatches={mismatched}"
    )


def require_count_consistency(path: Path, status: Mapping[str, str]) -> int:
    data = yaml.safe_load(path.read_text())
    configured_count = data.get("counts", {}).get("rh_d_decisions")
    if not isinstance(configured_count, int):
        raise DecisionIdError(f"{path}: counts.rh_d_decisions must be an integer")

    missing_retired = sorted(FULLY_RETIRED_DECISION_IDS - set(status))
    if missing_retired:
        raise DecisionIdError(
            f"{path}: fully retired decision IDs are missing: {missing_retired}"
        )

    expected_count = len(status) - len(FULLY_RETIRED_DECISION_IDS)
    if configured_count != expected_count:
        raise DecisionIdError(
            f"{path}: counts.rh_d_decisions={configured_count}, "
            f"expected {expected_count} after excluding "
            f"{sorted(FULLY_RETIRED_DECISION_IDS)}"
        )
    return expected_count


def _git_register(ref: str) -> dict[str, str]:
    result = subprocess.run(
        ["git", "show", f"{ref}:{REGISTER_IN_REPO}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return parse_register(result.stdout, ref)


def require_unique_integration_claims(
    base: Mapping[str, str], candidates: Mapping[str, Mapping[str, str]]
) -> None:
    claims: dict[str, list[tuple[str, str]]] = defaultdict(list)
    base_conflicts: list[str] = []
    for label, candidate in candidates.items():
        for decision_id, title in candidate.items():
            if decision_id in base:
                if title != base[decision_id]:
                    base_conflicts.append(
                        f"{label}:{decision_id}={title!r} conflicts with base={base[decision_id]!r}"
                    )
                continue
            claims[decision_id].append((label, title))

    duplicates = {
        decision_id: rows for decision_id, rows in claims.items() if len(rows) > 1
    }
    if base_conflicts or duplicates:
        raise DecisionIdError(
            "integration decision-ID collision: "
            f"base_conflicts={base_conflicts}, duplicate_claims={duplicates}"
        )


def _labeled_ref(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("expected LABEL=GIT_REF")
    label, ref = value.split("=", 1)
    if not label or not ref:
        raise argparse.ArgumentTypeError("expected non-empty LABEL=GIT_REF")
    return label, ref


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref")
    parser.add_argument(
        "--integration-ref",
        action="append",
        default=[],
        type=_labeled_ref,
        help="candidate decision register as LABEL=GIT_REF; repeatable",
    )
    args = parser.parse_args()

    register = parse_register(REGISTER.read_text(), str(REGISTER))
    status = parse_status(STATUS)
    require_exact_parity(register, status)
    counted_decisions = require_count_consistency(STATUS, status)
    print(
        f"local parity ok: {len(register)} exact ID/title pairs; "
        f"{counted_decisions} counted decisions"
    )

    if args.integration_ref:
        if not args.base_ref:
            parser.error("--base-ref is required with --integration-ref")
        candidates = {
            label: _git_register(ref) for label, ref in args.integration_ref
        }
        require_unique_integration_claims(_git_register(args.base_ref), candidates)
        print(
            "integration allocation ok: "
            + ", ".join(sorted(candidates))
        )
    elif args.base_ref:
        parser.error("--base-ref requires at least one --integration-ref")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
