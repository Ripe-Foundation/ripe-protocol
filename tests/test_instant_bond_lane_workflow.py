import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.check_instant_bond_lane_coverage import CONTRACT_THRESHOLDS


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "instant-bond-lane.yml"


@pytest.fixture(scope="session")
def ripe_hq():
    """Keep source-only workflow checks independent of protocol deployment."""


def _workflow():
    return yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)


def _step(name):
    return next(
        step
        for step in _workflow()["jobs"]["validate"]["steps"]
        if step.get("name") == name
    )


def test_feature_workflow_is_permanent_and_deduplicates_branch_and_pr_runs():
    workflow = _workflow()
    assert set(workflow["on"]) == {
        "pull_request",
        "merge_group",
        "push",
        "workflow_dispatch",
    }
    assert workflow["on"]["pull_request"]["branches"] == ["rh"]
    assert workflow["on"]["merge_group"]["branches"] == ["rh"]
    assert workflow["on"]["push"]["branches"] == ["instant-bond-lane"]
    concurrency = workflow["concurrency"]
    assert concurrency["cancel-in-progress"] == "true"
    assert "github.event.pull_request.head.ref || github.ref_name" in concurrency[
        "group"
    ]


def test_feature_workflow_restores_pinned_caches_and_keeps_manual_full_run():
    setup = _step("Use Python 3.12")
    assert setup["with"]["cache"] == "pip"
    assert setup["with"]["cache-dependency-path"] == "requirements.txt"
    restore = _step("Restore Titanoboa compiler artifacts")
    save = _step("Save Titanoboa compiler artifacts")
    assert restore["uses"] == (
        "actions/cache/restore@55cc8345863c7cc4c66a329aec7e433d2d1c52a9"
    )
    assert save["uses"] == (
        "actions/cache/save@55cc8345863c7cc4c66a329aec7e433d2d1c52a9"
    )
    assert "workflow_dispatch" in _workflow()["on"]


def test_feature_workflow_runs_all_critical_suites_and_per_contract_coverage():
    command = _step("Run the complete focused feature gate")["run"]
    for required in (
        "tests/core/instantBondLane",
        "tests/config/test_switchboard_foxtrot.py",
        "tests/deployment/test_instant_bond_lane_activation.py",
        "tests/deployment/test_abi_export.py",
        "tests/test_instant_bond_lane_workflow.py",
        "-o addopts=''",
        "--cov=contracts",
        "--cov-branch",
        "--cov-report=json:",
    ):
        assert required in command
    coverage = _step("Enforce per-contract coverage and publish evidence")["run"]
    assert "scripts/check_instant_bond_lane_coverage.py" in coverage
    assert "$GITHUB_STEP_SUMMARY" in coverage
    assert CONTRACT_THRESHOLDS == {
        "contracts/core/InstantBondLane.vy": 85.0,
        "contracts/core/InstantBondClaims.vy": 85.0,
        "contracts/config/SwitchboardFoxtrot.vy": 85.0,
    }


def test_feature_workflow_checks_sources_artifacts_activation_and_sizes():
    artifacts = _step("Verify generated artifacts and source binding")["run"]
    assert "scripts/export_abis.py --check" in artifacts
    assert "instant_bond_lane_controller.py" in artifacts
    assert "--check" in artifacts
    activation = _step("Verify fail-closed activation draft")["run"]
    assert "qualify_instant_bond_lane_activation.py --check-draft" in activation
    env = _step("Run the complete focused feature gate")["env"]
    assert env["INSTANT_BOND_FOXTROT_GAS_REPORT"].endswith("foxtrot-gas.json")
    assert env["INSTANT_BOND_GAS_REPORT"].endswith("gas.json")
    assert env["INSTANT_BOND_SIZE_REPORT"].endswith("runtime-sizes.json")


def test_per_contract_coverage_gate_fails_closed(tmp_path):
    def summary(percent):
        return {
            "covered_lines": 90,
            "num_statements": 100,
            "percent_covered": percent,
            "percent_covered_display": str(percent),
            "missing_lines": 10,
            "excluded_lines": 0,
            "num_branches": 20,
            "num_partial_branches": 2,
            "covered_branches": 18,
            "missing_branches": 2,
        }

    report = tmp_path / "coverage.json"
    report.write_text(
        json.dumps(
            {
                "files": {
                    "contracts/core/InstantBondLane.vy": {
                        "summary": summary(84.99)
                    },
                    "contracts/core/InstantBondClaims.vy": {
                        "summary": summary(95.0)
                    },
                    "contracts/config/SwitchboardFoxtrot.vy": {
                        "summary": summary(95.0)
                    },
                }
            }
        )
    )
    command = [
        sys.executable,
        str(ROOT / "scripts" / "check_instant_bond_lane_coverage.py"),
        str(report),
    ]
    failed = subprocess.run(command, text=True, capture_output=True, check=False)
    assert failed.returncode == 1
    assert "InstantBondLane.vy: 84.99% < 85.00%" in failed.stdout

    payload = json.loads(report.read_text())
    payload["files"]["contracts/core/InstantBondLane.vy"]["summary"][
        "percent_covered"
    ] = 85.0
    report.write_text(json.dumps(payload))
    assert subprocess.run(command, check=False).returncode == 0

    del payload["files"]["contracts/config/SwitchboardFoxtrot.vy"]
    report.write_text(json.dumps(payload))
    assert subprocess.run(command, check=False).returncode != 0
