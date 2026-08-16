import hashlib
import json
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
EVIDENCE_DOCUMENT = EVIDENCE.parent / "curve-snapshot-remediation.md"
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

    scanned = [
        EVIDENCE / "evidence-manifest.yaml",
        EVIDENCE_DOCUMENT,
        EVIDENCE / MANIFEST["clock_packet"]["file"],
        *(EVIDENCE / record["file"] for record in MANIFEST["artifacts"]),
    ]
    for path in scanned:
        contents = path.read_text()
        assert all(value not in contents for value in FORBIDDEN_EVIDENCE_TEXT)


def test_curve_asset_lp_harness_fix_closes_candidate_and_retains_target_set():
    candidate = EVIDENCE / "base-curve-prices-candidate-junit.xml"
    target = EVIDENCE / "base-curve-prices-target-junit.xml"
    expected = set(MANIFEST["target_asset_lp_failed_nodes"])

    assert MANIFEST["candidate_asset_lp_harness_fixed"] is True
    assert _failed_names(candidate) == set()
    assert _failed_names(target) == expected


def test_curve_source_and_fail_first_overlay_hashes_match_manifest():
    curve_source = ROOT / "contracts" / "priceSources" / "CurvePrices.vy"
    green_tests = ROOT / "tests" / "priceSources" / "curve" / "test_green_ref_pool.py"
    curve_tests = ROOT / "tests" / "priceSources" / "curve" / "test_curve_prices.py"
    route_tests = (
        ROOT
        / "tests"
        / "priceSources"
        / "curve"
        / "test_robinhood_launch_route.py"
    )
    fail_first_overlay = EVIDENCE / "fail-first-overlay.patch"
    clock_script = ROOT / "scripts" / "capture_robinhood_curve_clock.py"

    assert _sha256(curve_source) == MANIFEST["source_binding"]["curve_source_sha256"]
    assert _sha256(green_tests) == MANIFEST["source_binding"][
        "green_ref_pool_test_sha256"
    ]
    assert _sha256(curve_tests) == MANIFEST["source_binding"][
        "curve_prices_test_sha256"
    ]
    assert _sha256(route_tests) == MANIFEST["source_binding"]["route_test_sha256"]
    assert _sha256(fail_first_overlay) == MANIFEST["source_binding"][
        "fail_first_overlay_sha256"
    ]
    assert _sha256(clock_script) == MANIFEST["source_binding"][
        "clock_capture_script_sha256"
    ]
    assert MANIFEST["source_binding"]["price_desk_commit"] == (
        "6634d73fd797f03b57501fcc1513b2e9ba1bd2b1"
    )
    assert MANIFEST["source_binding"]["price_desk_source_sha256"] == (
        "7fd7e8eedd883a10ee7a225cb666896324d7b9b47de3a136175f62e00267561c"
    )


def test_robinhood_clock_packet_binds_distinct_child_and_contract_domains():
    record = MANIFEST["clock_packet"]
    path = EVIDENCE / record["file"]
    packet = json.loads(path.read_text())

    assert path.stat().st_size == record["bytes"]
    assert _sha256(path) == record["sha256"]
    assert packet["chain_id"] == record["chain_id"] == 4663
    assert packet["sample_size"] == record["sample_size"] == 16
    assert packet["pinned_child_range"] == [
        record["pinned_child_start"],
        record["pinned_child_end"],
    ]

    samples = packet["samples"]
    assert [row["rpc_child_block"] for row in samples] == list(
        range(record["pinned_child_start"], record["pinned_child_end"] + 1)
    )
    assert {
        row["contract_visible_NUMBER"] for row in samples
    } == {record["contract_number"]}
    assert all(
        row["l1BlockNumber"] == row["contract_visible_NUMBER"]
        for row in samples
    )
    assert all(
        row["arbSys_arbBlockNumber"] == row["rpc_child_block"]
        for row in samples
    )
    assert [row["timestamp"] for row in samples] == sorted(
        row["timestamp"] for row in samples
    )
    assert len({row["timestamp"] for row in samples}) > 1
