from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github/workflows/python-tests.yml"
CHECKOUT_ACTION = (
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
)
SETUP_PYTHON_ACTION = (
    "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
)
CACHE_ACTION = (
    "actions/cache/{mode}@55cc8345863c7cc4c66a329aec7e433d2d1c52a9"
)


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep workflow source checks independent of protocol deployment."""


def _workflow():
    return yaml.load(WORKFLOW_PATH.read_text(), Loader=yaml.BaseLoader)


def _step(job, name):
    return next(step for step in job["steps"] if step.get("name") == name)


def test_python_workflow_routes_automatic_events_to_one_lean_lane():
    workflow = _workflow()
    assert workflow["on"]["pull_request"]["branches"] == ["rh"]
    assert workflow["on"]["merge_group"]["branches"] == ["rh"]
    assert workflow["on"]["push"]["branches"] == ["master"]
    assert workflow["permissions"] == {"contents": "read"}

    dispatch_lane = workflow["on"]["workflow_dispatch"]["inputs"]["lane"]
    assert dispatch_lane["default"] == "lean"
    assert dispatch_lane["options"] == ["lean", "comprehensive"]

    test_job = workflow["jobs"]["test"]
    lane_matrix = test_job["strategy"]["matrix"]["lane"]
    assert "github.event_name == 'workflow_dispatch'" in lane_matrix
    assert "inputs.lane" in lane_matrix
    assert "'[\"lean\"]'" in lane_matrix
    assert "lean\",\"comprehensive" not in lane_matrix


def test_python_workflow_uses_full_history_and_bounded_lane_timeouts():
    test_job = _workflow()["jobs"]["test"]
    checkout = _step(test_job, "Check out source")
    assert checkout["with"]["fetch-depth"] == "0"
    assert test_job["timeout-minutes"] == (
        "${{ matrix.lane == 'comprehensive' && 180 || 120 }}"
    )


def test_python_workflow_pins_node24_action_releases_by_commit():
    jobs = _workflow()["jobs"]
    test_job = jobs["test"]
    macos_job = jobs["manifest-promotion-macos"]

    assert _step(test_job, "Check out source")["uses"] == CHECKOUT_ACTION
    assert _step(macos_job, "Check out full source history")["uses"] == (
        CHECKOUT_ACTION
    )
    assert _step(test_job, "Use Python 3.12.0")["uses"] == (
        SETUP_PYTHON_ACTION
    )
    assert _step(macos_job, "Use Python 3.12.0")["uses"] == (
        SETUP_PYTHON_ACTION
    )
    assert _step(test_job, "Restore Titanoboa compiler artifacts")[
        "uses"
    ] == CACHE_ACTION.format(mode="restore")
    assert _step(test_job, "Save Titanoboa compiler artifacts")[
        "uses"
    ] == CACHE_ACTION.format(mode="save")


def test_python_workflow_cancels_superseded_pr_or_branch_runs():
    concurrency = _workflow()["concurrency"]
    assert concurrency["cancel-in-progress"] == "true"
    group = concurrency["group"]
    assert "github.event.pull_request.number || github.ref" in group
    assert "head.sha" not in group


def test_python_workflow_exposes_stable_rh_pr_gate():
    job = _workflow()["jobs"]["rh-pr-gate"]
    assert job["name"] == "rh-pr-gate"
    assert job["needs"] == ["test"]
    assert job["runs-on"] == "ubuntu-latest"
    assert job["timeout-minutes"] == "5"
    assert "always()" in job["if"]
    assert "github.event_name == 'pull_request'" in job["if"]
    assert "github.event_name == 'merge_group'" in job["if"]

    step = _step(job, "Require successful lean lane")
    assert step["env"]["TEST_RESULT"] == "${{ needs.test.result }}"
    assert 'if [ "$TEST_RESULT" != "success" ]' in step["run"]
    assert "exit 1" in step["run"]


def test_python_workflow_runs_manifest_promotion_only_for_manual_comprehensive():
    jobs = _workflow()["jobs"]
    job = jobs["manifest-promotion-macos"]
    assert job["runs-on"] == "macos-latest"
    assert job["timeout-minutes"] == "60"
    assert job["if"] == (
        "github.event_name == 'workflow_dispatch' && "
        "inputs.lane == 'comprehensive'"
    )
    checkout = _step(job, "Check out full source history")
    assert checkout["with"]["fetch-depth"] == "0"
    command = _step(job, "Run macOS manifest-promotion coverage")["run"]
    assert "-o addopts=''" in command
    assert "tests/deployment/test_current_manifest_promotion.py" in command
    linux_command = _step(jobs["test"], "Run comprehensive lane")["run"]
    assert (
        "--ignore=tests/deployment/test_current_manifest_promotion.py"
        in linux_command
    )
