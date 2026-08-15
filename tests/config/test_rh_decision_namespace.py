from __future__ import annotations

import collections
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "docs" / "chains" / "rh" / "decision-register.md"
STATUS = ROOT / "docs" / "chains" / "rh" / "status.yaml"
RESERVATIONS = ROOT / "docs" / "chains" / "rh" / "open-decision-id-reservations.yaml"
HEADING = re.compile(r"^### (RH-D\d{3}) — (.+)$", re.MULTILINE)
FULLY_RETIRED_STATUSES = {"retired_default_floor_restored"}
D042_TITLE = "PriceDesk source isolation uses bounded policy-only admission"
D042_REGISTER_STATUS = (
    "**Status:** Proposed candidate policy boundary pending explicit owner approval."
)
D042_STATUS_VALUE = "proposed_candidate_policy_boundary_pending_owner_approval"


def _assert_unique(label: str, values: list[str]) -> None:
    duplicates = sorted(
        value for value, count in collections.Counter(values).items() if count != 1
    )
    assert not duplicates, f"duplicate {label}: {duplicates}"


def test_decision_register_and_status_have_exact_unique_id_title_parity():
    # Check list uniqueness before any dictionary conversion, which would hide
    # the exact collision this guard is intended to detect.
    register_entries = HEADING.findall(REGISTER.read_text())
    status = yaml.safe_load(STATUS.read_text())
    status_entries = [(item["id"], item["title"]) for item in status["decisions"]]
    _assert_unique("register decision ids", [item[0] for item in register_entries])
    _assert_unique("status decision ids", [item[0] for item in status_entries])
    assert set(register_entries) == set(status_entries)

    counted = sum(
        item["status"] not in FULLY_RETIRED_STATUSES for item in status["decisions"]
    )
    assert status["counts"]["rh_d_decisions"] == counted


def test_rh_d042_authority_status_is_proposed_in_register_and_status():
    register = REGISTER.read_text()
    start = register.index(f"### RH-D042 — {D042_TITLE}")
    end = (
        register.index("\n### ", start + 1)
        if "\n### " in register[start + 1 :]
        else len(register)
    )
    assert D042_REGISTER_STATUS in register[start:end]

    status = yaml.safe_load(STATUS.read_text())
    entry = next(item for item in status["decisions"] if item["id"] == "RH-D042")
    assert entry["title"] == D042_TITLE
    assert entry["status"] == D042_STATUS_VALUE


def _decision_number(decision_id: str) -> int:
    assert re.fullmatch(r"RH-D\d{3}", decision_id)
    return int(decision_id.removeprefix("RH-D"))


def test_decision_reservation_lifecycle_is_current_unique_and_complete():
    register_entries = HEADING.findall(REGISTER.read_text())
    value = yaml.safe_load(RESERVATIONS.read_text())
    assert value["schema_version"] == 2
    assert value["integrated_target"]["branch"] == "rh-audit-remediation"
    assert "commit" not in value["integrated_target"]
    assert value["reservation_scope"] == (
        "identifiers_only_titles_are_coordination_hints"
    )

    reservations = value["open_pr_reservations"]
    reserved_ids = [item["id"] for item in reservations]
    _assert_unique("open-PR reservation ids", reserved_ids)
    assert set(reserved_ids).isdisjoint({item[0] for item in register_entries})

    integrated_ids = [
        decision_id
        for item in value["recent_integrated_register_entries"]
        for decision_id in item["ids"]
    ]
    _assert_unique("recent integrated decision ids", integrated_ids)
    assert set(integrated_ids) <= {item[0] for item in register_entries}
    assert {"RH-D033", "RH-D034", "RH-D035", "RH-D036"} <= set(integrated_ids)

    candidate_ids = [
        decision_id
        for item in value["current_candidate_register_entries"]
        for decision_id in item["ids"]
    ]
    _assert_unique("current candidate decision ids", candidate_ids)
    assert set(candidate_ids) <= {item[0] for item in register_entries}
    assert set(candidate_ids).isdisjoint(integrated_ids)

    integrated_register_ids = {item[0] for item in register_entries} - set(
        candidate_ids
    )
    highest = value["integrated_target"]["highest_decision_id"]
    assert _decision_number(highest) == max(
        _decision_number(decision_id) for decision_id in integrated_register_ids
    )

    all_live_ids = [item[0] for item in register_entries] + reserved_ids
    _assert_unique("integrated, candidate, and reserved decision ids", all_live_ids)

    assert set(value["lifecycle"]) == {
        "reserved",
        "current_candidate",
        "on_merge",
        "stale_branch",
    }
    assert all(value["lifecycle"].values())
