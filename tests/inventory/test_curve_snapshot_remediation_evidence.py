import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

import yaml


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT
    / "docs"
    / "chains"
    / "rh"
    / "evidence"
    / "curve-snapshot-remediation"
)
MANIFEST = yaml.safe_load((EVIDENCE / "evidence-manifest.yaml").read_text())
FORBIDDEN_EVIDENCE_TEXT = (
    "alchemy.com",
    "Private Keys",
    "Mnemonic:",
    "WEB3_ALCHEMY_API_KEY",
    "ETHERSCAN_API_KEY",
    "/Users/wigglez",
    "Wigglez-MacStudio",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cases(path: Path):
    return ET.parse(path).findall(".//testcase")


def _failed_names(path: Path) -> set[str]:
    return {
        case.attrib["name"]
        for case in _cases(path)
        if case.find("failure") is not None
    }


def test_curve_evidence_artifacts_match_manifest_and_are_sanitized():
    for record in MANIFEST["artifacts"]:
        path = EVIDENCE / record["file"]
        assert path.stat().st_size == record["bytes"]
        assert _sha256(path) == record["sha256"]

        cases = _cases(path)
        failures = sum(case.find("failure") is not None for case in cases)
        skipped = sum(case.find("skipped") is not None for case in cases)
        assert len(cases) == record["tests"]
        assert failures == record["failed"]
        assert skipped == record["skipped"]
        assert len(cases) - failures - skipped == record["passed"]

        contents = path.read_text()
        assert all(value not in contents for value in FORBIDDEN_EVIDENCE_TEXT)


def test_curve_asset_lp_failure_parity_matches_exact_manifest_set():
    candidate = EVIDENCE / "base-curve-prices-candidate-junit.xml"
    target = EVIDENCE / "base-curve-prices-target-junit.xml"
    expected = set(MANIFEST["asset_lp_failed_nodes"])

    assert MANIFEST["candidate_target_failure_sets_equal"] is True
    assert _failed_names(candidate) == expected
    assert _failed_names(target) == expected


def test_curve_source_and_fail_first_overlay_hashes_match_manifest():
    curve_source = ROOT / "contracts" / "priceSources" / "CurvePrices.vy"
    fail_first_overlay = EVIDENCE / "fail-first-overlay.patch"

    assert _sha256(curve_source) == MANIFEST["source_binding"]["curve_source_sha256"]
    assert _sha256(fail_first_overlay) == MANIFEST["source_binding"][
        "fail_first_overlay_sha256"
    ]
