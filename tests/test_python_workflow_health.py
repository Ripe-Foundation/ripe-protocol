from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github/workflows/python-tests.yml"


def _workflow():
    return yaml.load(WORKFLOW_PATH.read_text(), Loader=yaml.BaseLoader)


def _step(job, name):
    return next(step for step in job["steps"] if step.get("name") == name)


def test_python_workflow_uses_full_history_and_bounded_lane_timeouts():
    workflow = _workflow()
    assert workflow["on"]["push"]["branches"] == ["master", "rh"]
    assert "pull_request" in workflow["on"]

    test_job = workflow["jobs"]["test"]
    checkout = _step(test_job, "Check out source")
    assert checkout["with"]["fetch-depth"] == "0"
    assert test_job["timeout-minutes"] == (
        "${{ matrix.lane == 'comprehensive' && 180 || 120 }}"
    )


def test_python_workflow_cancels_superseded_pr_or_branch_runs():
    concurrency = _workflow()["concurrency"]
    assert concurrency["cancel-in-progress"] == "true"
    group = concurrency["group"]
    assert "github.event.pull_request.number || github.ref" in group
    assert "head.sha" not in group


def test_python_workflow_runs_manifest_promotion_on_macos():
    job = _workflow()["jobs"]["manifest-promotion-macos"]
    assert job["runs-on"] == "macos-latest"
    assert job["timeout-minutes"] == "60"
    assert job["if"] == (
        "github.event_name != 'workflow_dispatch' || "
        "inputs.lane == 'comprehensive'"
    )
    checkout = _step(job, "Check out full source history")
    assert checkout["with"]["fetch-depth"] == "0"
    command = _step(job, "Run macOS manifest-promotion coverage")["run"]
    assert "-o addopts=''" in command
    assert "tests/deployment/test_current_manifest_promotion.py" in command
