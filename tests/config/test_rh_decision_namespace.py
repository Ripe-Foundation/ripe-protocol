from __future__ import annotations

import collections
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "docs" / "chains" / "rh" / "decision-register.md"
STATUS = ROOT / "docs" / "chains" / "rh" / "status.yaml"
RESERVATIONS = (
    ROOT / "docs" / "chains" / "rh" / "open-decision-id-reservations.yaml"
)
HEADING = re.compile(r"^### (RH-D\d{3}) — (.+)$", re.MULTILINE)
FULLY_RETIRED_STATUSES = {"retired_default_floor_restored"}


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
    status_entries = [
        (item["id"], item["title"])
        for item in status["decisions"]
    ]
    _assert_unique("register decision ids", [item[0] for item in register_entries])
    _assert_unique("status decision ids", [item[0] for item in status_entries])
    assert set(register_entries) == set(status_entries)

    counted = sum(
        item["status"] not in FULLY_RETIRED_STATUSES
        for item in status["decisions"]
    )
    assert status["counts"]["rh_d_decisions"] == counted


def test_open_pr_reservations_are_unique_and_do_not_collide_with_register():
    register_entries = HEADING.findall(REGISTER.read_text())
    value = yaml.safe_load(RESERVATIONS.read_text())
    reservations = value["open_pr_reservations"]
    reserved_ids = [item["id"] for item in reservations]
    _assert_unique("open-PR reservation ids", reserved_ids)
    assert set(reserved_ids).isdisjoint({item[0] for item in register_entries})

    stacked_ids = [
        decision_id
        for item in value["stacked_register_entries"]
        for decision_id in item["ids"]
    ]
    _assert_unique("stacked decision ids", stacked_ids)
    assert set(stacked_ids) <= {item[0] for item in register_entries}

    all_live_ids = [item[0] for item in register_entries] + reserved_ids
    _assert_unique("integrated, stacked, and reserved decision ids", all_live_ids)
