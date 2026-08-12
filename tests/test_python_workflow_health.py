import ast
import json
import re
import shlex
from configparser import ConfigParser
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github/workflows/python-tests.yml"
PYTEST_INI_PATH = ROOT / "pytest.ini"
CHECKOUT_ACTION = (
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
)
SETUP_PYTHON_ACTION = (
    "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
)
CACHE_ACTION = (
    "actions/cache/{mode}@55cc8345863c7cc4c66a329aec7e433d2d1c52a9"
)
BOA_CACHE_PREFIX = "boa-${{ runner.os }}-py312-${{ matrix.lane }}"
BOA_INPUT_HASH = (
    "${{ hashFiles('requirements.txt', 'contracts/**/*.vy', "
    "'interfaces/**/*.vyi') }}"
)
LEAN_SHARD_ARGUMENTS = {
    "core": ("tests/core",),
    "vaults-tokens": ("tests/vaults", "tests/tokens"),
    "supporting": (
        "tests",
        "--ignore=tests/core",
        "--ignore=tests/vaults",
        "--ignore=tests/tokens",
    ),
}
LEAN_MATRIX = [
    {"lane": "lean", "shard": shard} for shard in LEAN_SHARD_ARGUMENTS
]
COMPREHENSIVE_MATRIX = [{"lane": "comprehensive", "shard": "all"}]
LEAN_MATRIX_JSON = json.dumps(LEAN_MATRIX, separators=(",", ":"))
COMPREHENSIVE_MATRIX_JSON = json.dumps(COMPREHENSIVE_MATRIX, separators=(",", ":"))
MATRIX_INCLUDE_EXPRESSION = (
    "${{ fromJSON(github.event_name == 'workflow_dispatch' && "
    "inputs.lane == 'comprehensive' && "
    f"'{COMPREHENSIVE_MATRIX_JSON}' || '{LEAN_MATRIX_JSON}') }}}}"
)
PYTEST_IGNORED_DIRECTORIES = {
    "tests/deployment",
}


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep workflow source checks independent of protocol deployment."""


def _workflow():
    return yaml.load(WORKFLOW_PATH.read_text(), Loader=yaml.BaseLoader)


def _step(job, name):
    return next(step for step in job["steps"] if step.get("name") == name)


def _pytest_addopts():
    config = ConfigParser()
    config.read(PYTEST_INI_PATH)
    return shlex.split(config["pytest"]["addopts"])


def _workflow_lean_shard_arguments():
    command = _step(_workflow()["jobs"]["test"], "Run lean default lane")[
        "run"
    ]
    pattern = re.compile(
        r"^  (?P<shard>[a-z][a-z-]*)\)\n"
        r"    shard_args=\((?P<arguments>.*?)\)\n"
        r"    ;;$",
        flags=re.MULTILINE | re.DOTALL,
    )
    branches = [
        (match.group("shard"), tuple(shlex.split(match.group("arguments"))))
        for match in pattern.finditer(command)
    ]
    arguments = dict(branches)
    assert len(arguments) == len(branches), "Lean shard names must be unique"
    return arguments


def _partition_shard_arguments(arguments):
    targets = []
    ignores = []
    for argument in arguments:
        if argument.startswith("--ignore="):
            ignores.append(argument.removeprefix("--ignore="))
        else:
            assert not argument.startswith("-"), (
                f"Unsupported lean shard argument: {argument}"
            )
            targets.append(argument)
    assert targets, "Each lean shard must have at least one test target"
    return tuple(targets), tuple(ignores)


def _is_within(path, target):
    return path == target or path.startswith(f"{target}/")


def _shard_selects_path(path, arguments):
    targets, ignores = _partition_shard_arguments(arguments)
    return any(_is_within(path, target) for target in targets) and not any(
        _is_within(path, ignored) for ignored in ignores
    )


def _uses_serial_pytest_marker(path):
    tree = ast.parse(path.read_text(), filename=path)
    pytest_names = set()
    mark_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            pytest_names.update(
                alias.asname or alias.name
                for alias in node.names
                if alias.name == "pytest"
            )
        elif isinstance(node, ast.ImportFrom) and node.module == "pytest":
            mark_names.update(
                alias.asname or alias.name
                for alias in node.names
                if alias.name == "mark"
            )

    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or node.attr != "serial":
            continue
        marker = node.value
        if isinstance(marker, ast.Name) and marker.id in mark_names:
            return True
        if (
            isinstance(marker, ast.Attribute)
            and marker.attr == "mark"
            and isinstance(marker.value, ast.Name)
            and marker.value.id in pytest_names
        ):
            return True
    return False


def test_python_workflow_routes_automatic_events_to_one_lean_lane():
    workflow = _workflow()
    assert set(workflow["on"]) == {
        "pull_request",
        "merge_group",
        "push",
        "workflow_dispatch",
    }
    assert workflow["on"]["pull_request"]["branches"] == ["rh"]
    assert workflow["on"]["merge_group"]["branches"] == ["rh"]
    assert workflow["on"]["push"]["branches"] == ["master"]
    assert workflow["permissions"] == {"contents": "read"}

    dispatch_lane = workflow["on"]["workflow_dispatch"]["inputs"]["lane"]
    assert dispatch_lane["default"] == "lean"
    assert dispatch_lane["options"] == ["lean", "comprehensive"]

    test_job = workflow["jobs"]["test"]
    assert test_job["name"] == (
        "Python 3.12.0 / ${{ matrix.lane }} / ${{ matrix.shard }}"
    )
    assert test_job["strategy"]["fail-fast"] == "false"
    assert test_job["strategy"]["matrix"] == {"include": MATRIX_INCLUDE_EXPRESSION}


def test_python_workflow_lean_shards_fail_closed_with_exact_targets():
    test_job = _workflow()["jobs"]["test"]
    step = _step(test_job, "Run lean default lane")
    assert step["if"] == "matrix.lane == 'lean'"
    assert step["env"] == {"TEST_SHARD": "${{ matrix.shard }}"}

    assert _workflow_lean_shard_arguments() == LEAN_SHARD_ARGUMENTS

    command = step["run"]
    assert command.count('case "$TEST_SHARD" in') == 1
    assert command.count("\nesac\n") == 1
    assert (
        '  *)\n    echo "Unknown lean test shard: $TEST_SHARD"\n'
        "    exit 2\n    ;;\nesac"
    ) in command
    assert command.count('"${shard_args[@]}"') == 1


def test_python_workflow_lean_shards_cover_each_test_file_exactly_once():
    configured_ignores = {
        option.removeprefix("--ignore=")
        for option in _pytest_addopts()
        if option.startswith("--ignore=")
    }
    assert configured_ignores == PYTEST_IGNORED_DIRECTORIES

    test_files = {
        path.relative_to(ROOT).as_posix()
        for pattern in ("test_*.py", "*_test.py")
        for path in (ROOT / "tests").rglob(pattern)
    }
    lean_test_files = {
        path
        for path in test_files
        if not any(
            path == ignored or path.startswith(f"{ignored}/")
            for ignored in PYTEST_IGNORED_DIRECTORIES
        )
    }

    shard_arguments = _workflow_lean_shard_arguments()
    unmatched = []
    multiply_matched = {}
    for path in sorted(lean_test_files):
        matches = [
            shard
            for shard, arguments in shard_arguments.items()
            if _shard_selects_path(path, arguments)
        ]
        if not matches:
            unmatched.append(path)
        elif len(matches) != 1:
            multiply_matched[path] = matches

    assert unmatched == [], f"Add new lean tests to one shard: {unmatched}"
    assert multiply_matched == {}, (
        f"Lean tests belong to multiple shards: {multiply_matched}"
    )

    future_root_test = "tests/test_future_lean_guard.py"
    matches = [
        shard
        for shard, arguments in _workflow_lean_shard_arguments().items()
        if _shard_selects_path(future_root_test, arguments)
    ]
    assert matches == ["supporting"]


def test_python_workflow_lean_shards_reject_unisolated_serial_tests():
    serial_tests = []
    for pattern in ("test_*.py", "*_test.py"):
        for path in (ROOT / "tests").rglob(pattern):
            relative_path = path.relative_to(ROOT).as_posix()
            if any(
                relative_path == ignored or relative_path.startswith(f"{ignored}/")
                for ignored in PYTEST_IGNORED_DIRECTORIES
            ):
                continue
            if _uses_serial_pytest_marker(path):
                serial_tests.append(relative_path)

    assert sorted(set(serial_tests)) == [], (
        "Move serial tests into a dedicated nonparallel lane before marking "
        f"them serial: {sorted(set(serial_tests))}"
    )


def test_python_workflow_cache_is_partitioned_by_shard():
    step = _step(
        _workflow()["jobs"]["test"],
        "Restore Titanoboa compiler artifacts",
    )
    assert step["with"]["key"] == (
        f"{BOA_CACHE_PREFIX}-{BOA_INPUT_HASH}-"
        "${{ matrix.shard }}-${{ github.run_id }}"
    )
    assert step["with"]["restore-keys"].splitlines() == [
        f"{BOA_CACHE_PREFIX}-{BOA_INPUT_HASH}-${{{{ matrix.shard }}}}-",
        f"{BOA_CACHE_PREFIX}-{BOA_INPUT_HASH}-",
        f"{BOA_CACHE_PREFIX}-",
        "boa-${{ runner.os }}-py312-",
    ]


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

    assert _step(test_job, "Check out source")["uses"] == CHECKOUT_ACTION
    assert _step(test_job, "Use Python 3.12.0")["uses"] == (
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
    assert job["if"] == (
        "${{ always() && (github.event_name == 'pull_request' || "
        "github.event_name == 'merge_group') }}"
    )

    step = _step(job, "Require successful lean lane")
    assert step["env"]["TEST_RESULT"] == "${{ needs.test.result }}"
    assert 'if [ "$TEST_RESULT" != "success" ]' in step["run"]
    assert "exit 1" in step["run"]
