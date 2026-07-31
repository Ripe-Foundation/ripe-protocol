#!/usr/bin/env python3
"""Check pre-collected deployment observations without RPC or mutation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.utils.deployment_assertions import (
    DeploymentAssertionInputError,
    ObservationMode,
    assert_deployment,
    expectations_template,
    observations_template,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Both JSON envelopes require schema_version, profile_id, and "
            "chain_id. Expectations also require profile_kind; observations "
            "require mode. local_deployment and deployed_observation require "
            "all component identity fields. Blueprint registry enforcement "
            "cannot be disabled."
        ),
    )
    parser.add_argument("--expectations", type=Path)
    parser.add_argument("--observations", type=Path)
    parser.add_argument(
        "--print-template",
        choices=("expectations", *(mode.value for mode in ObservationMode)),
        help="print a versioned envelope template and exit",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.print_template:
        template = (
            expectations_template()
            if args.print_template == "expectations"
            else observations_template(ObservationMode(args.print_template))
        )
        print(json.dumps(template, ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    if args.expectations is None or args.observations is None:
        parser.error("--expectations and --observations are required")
    try:
        expectations = json.loads(args.expectations.read_text())
        observations = json.loads(args.observations.read_text())
        report = assert_deployment(expectations, observations)
    except (
        DeploymentAssertionInputError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        print(f"DEPLOYMENT_ASSERTIONS_INPUT_FAILED: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            report.to_mapping(),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    if not report.ok:
        print(
            f"DEPLOYMENT_ASSERTIONS_FAILED: {len(report.failures)}",
            file=sys.stderr,
        )
        return 1
    print(
        "DEPLOYMENT_ASSERTIONS_OK "
        f"mode={report.mode.value} source=precollected-observations"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
