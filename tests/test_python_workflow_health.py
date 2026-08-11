from pathlib import Path

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


