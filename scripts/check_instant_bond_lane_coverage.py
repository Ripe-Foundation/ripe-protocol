#!/usr/bin/env python3
"""Enforce and report coverage for each Instant Bond Lane contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CONTRACT_THRESHOLDS = {
    "contracts/core/InstantBondLane.vy": 85.0,
    "contracts/core/InstantBondClaims.vy": 85.0,
    "contracts/config/SwitchboardFoxtrot.vy": 85.0,
}


def coverage_rows(report: dict) -> list[dict]:
    rows = []
    files = report.get("files", {})
    for path, threshold in CONTRACT_THRESHOLDS.items():
        if path not in files:
            raise ValueError(f"coverage report is missing {path}")
        summary = files[path]["summary"]
        rows.append(
            {
                "contract": path,
                "statements": summary["num_statements"],
                "missed_statements": summary["missing_lines"],
                "branches": summary["num_branches"],
                "partial_branches": summary["num_partial_branches"],
                "percent": float(summary["percent_covered"]),
                "threshold": threshold,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--github-summary", type=Path)
    args = parser.parse_args()

    rows = coverage_rows(json.loads(args.report.read_text()))
    failures = []
    lines = [
        "| Contract | Statements | Missed | Branches | Partial | Coverage | Gate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {contract} | {statements} | {missed_statements} | {branches} | "
            "{partial_branches} | {percent:.2f}% | {threshold:.2f}% |".format(**row)
        )
        if row["percent"] < row["threshold"]:
            failures.append(
                f"{row['contract']}: {row['percent']:.2f}% < {row['threshold']:.2f}%"
            )

    rendered = "\n".join(lines) + "\n"
    print(rendered, end="")
    if args.github_summary:
        with args.github_summary.open("a") as summary:
            summary.write("## Instant Bond Lane coverage\n\n")
            summary.write(rendered)
    if failures:
        print("per-contract coverage gate failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
