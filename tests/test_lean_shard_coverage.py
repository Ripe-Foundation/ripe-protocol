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


def _workflow_lean_shard_branches():
    command = _step(_workflow()["jobs"]["test"], "Run lean default lane")[
        "run"
    ]
    pattern = re.compile(
        r"^  (?P<shard>[a-z][a-z0-9-]*)\)\n"
        r"    shard_args=\((?P<arguments>.*?)\)\n"
        r"(?:    dist_mode=(?P<dist>[a-z]+)\n)?"
        r"    ;;$",
        flags=re.MULTILINE | re.DOTALL,
    )
    return [
        (match.group("shard"), tuple(shlex.split(match.group("arguments"))))
        for match in pattern.finditer(command)
    ]


def _workflow_lean_shard_arguments():
    branches = _workflow_lean_shard_branches()
    arguments = dict(branches)
    assert len(arguments) == len(branches), "Lean shard names must be unique"
    return arguments


def _workflow_scheduled_lean_shards():
    expression = _workflow()["jobs"]["test"]["strategy"]["matrix"][
        "include"
    ]
    encoded_matrices = re.findall(r"'(\[[^']*\])'", expression)
    assert encoded_matrices, "Test matrix must contain JSON lane definitions"

    entries = [
        entry
        for encoded_matrix in encoded_matrices
        for entry in json.loads(encoded_matrix)
    ]
    return [entry["shard"] for entry in entries if entry["lane"] == "lean"]


def _unset_tokens(script):
    tokens = set()
    for line in script.splitlines():
        stripped = line.strip()
        if stripped.startswith("unset "):
            tokens.update(shlex.split(stripped)[1:])
    return tokens


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


def test_python_workflow_routes_validation_jobs_on_automatic_events():
    workflow = _workflow()
    assert set(workflow["on"]) == {
        "pull_request",
        "merge_group",
        "push",
        "workflow_dispatch",
    }
    assert workflow["on"]["pull_request"]["branches"] == [
        "rh",
        "rh-audit-remediation",
    ]
    assert workflow["on"]["merge_group"]["branches"] == [
        "rh",
        "rh-audit-remediation",
    ]
    assert workflow["on"]["push"]["branches"] == [
        "master",
        "rh",
        "rh-audit-remediation",
    ]

    jobs = workflow["jobs"]
    for job_name in (
        "solidity",
        "test",
        "deployment-controls",
        "snapshot-gas",
    ):
        assert "if" not in jobs[job_name], (
            f"{job_name} must validate direct integration-branch pushes"
        )

    assert jobs["warm-boa-cache"]["if"] == (
        "${{ github.event_name == 'push' }}"
    )
    assert jobs["rh-pr-gate"]["if"] == (
        "${{ always() && (github.event_name == 'pull_request' || "
        "github.event_name == 'merge_group') }}"
    )


def test_python_workflow_schedules_every_lean_case_arm_once():
    scheduled = _workflow_scheduled_lean_shards()
    cased = [shard for shard, _ in _workflow_lean_shard_branches()]

    assert len(scheduled) == len(set(scheduled)), (
        f"Lean matrix contains duplicate shards: {scheduled}"
    )
    assert len(cased) == len(set(cased)), (
        f"Lean shell case contains duplicate shards: {cased}"
    )
    assert set(scheduled) == set(cased), (
        "Lean matrix and shell case schedule different shards: "
        f"scheduled={scheduled}, cased={cased}"
    )


def test_python_workflow_lean_shards_use_loadfile_distribution():
    command = _step(_workflow()["jobs"]["test"], "Run lean default lane")[
        "run"
    ]
    assignments = re.findall(
        r"^\s*dist_mode=(?P<mode>[a-z]+)\s*$",
        command,
        flags=re.MULTILINE,
    )
    assert assignments == ["loadfile"]
    assert command.count('--dist "$dist_mode"') == 1


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


def test_python_workflow_pins_every_external_action_to_a_commit():
    action_steps = [
        (job_name, step.get("name", "<unnamed>"), step["uses"])
        for job_name, job in _workflow()["jobs"].items()
        for step in job.get("steps", [])
        if "uses" in step and not step["uses"].startswith("./")
    ]
    assert any(job_name == "warm-boa-cache" for job_name, _, _ in action_steps)

    unpinned = {
        f"{job_name}/{step_name}": action
        for job_name, step_name, action in action_steps
        if re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", action) is None
    }
    assert unpinned == {}, f"External actions must use commit SHAs: {unpinned}"


def test_python_workflow_warm_cache_matches_lean_restore_prefix():
    jobs = _workflow()["jobs"]
    test_restore = _step(
        jobs["test"], "Restore Titanoboa compiler artifacts"
    )
    warm_restore = _step(
        jobs["warm-boa-cache"], "Restore Titanoboa compiler artifacts"
    )

    warm_key = warm_restore["with"]["key"]
    suffix = "warm-${{ github.run_id }}"
    assert warm_key.endswith(suffix)
    warm_prefix = warm_key.removesuffix(suffix)
    lean_restore_prefixes = [
        prefix.replace("${{ matrix.lane }}", "lean")
        for prefix in test_restore["with"]["restore-keys"].splitlines()
    ]
    assert warm_prefix in lean_restore_prefixes

    warm_save = _step(
        jobs["warm-boa-cache"], "Save Titanoboa compiler artifacts"
    )
    assert warm_save["with"]["key"] == (
        "${{ steps.boa-cache.outputs.cache-primary-key }}"
    )


def test_python_workflow_exposes_stable_rh_pr_gate():
    job = _workflow()["jobs"]["rh-pr-gate"]
    assert job["name"] == "rh-pr-gate"
    assert job["needs"] == ["test", "deployment-controls", "snapshot-gas"]

    expected_results = {
        "Require successful lean lane": (
            "TEST_RESULT",
            "${{ needs.test.result }}",
        ),
        "Require successful deployment controls": (
            "CONTROLS_RESULT",
            "${{ needs.deployment-controls.result }}",
        ),
        "Require successful snapshot gas budgets": (
            "GAS_RESULT",
            "${{ needs.snapshot-gas.result }}",
        ),
    }
    for step_name, (variable, expression) in expected_results.items():
        step = _step(job, step_name)
        assert step["env"] == {variable: expression}
        assert f'if [ "${variable}" != "success" ]' in step["run"]
        assert "exit 1" in step["run"]


def test_python_workflow_runs_deployment_controls_without_credentials():
    command = _step(
        _workflow()["jobs"]["deployment-controls"],
        "Run deployment control suites",
    )["run"]
    required = {
        "ETHERSCAN_API_KEY",
        "BASESCAN_API_KEY",
        "PRIVATE_KEY",
        "WEB3_ALCHEMY_API_KEY",
    }
    missing = required - _unset_tokens(command)

    assert not missing, f"Credentials not explicitly unset: {sorted(missing)}"
    assert "-o addopts=''" in command
    assert "tests/deployment" in shlex.split(command)
    assert "tests/deployment" in PYTEST_IGNORED_DIRECTORIES


def test_unset_parser_rejects_credentials_that_are_only_mentioned():
    required = {
        "ETHERSCAN_API_KEY",
        "BASESCAN_API_KEY",
        "PRIVATE_KEY",
        "WEB3_ALCHEMY_API_KEY",
    }
    for dropped in sorted(required):
        remaining = " ".join(sorted(required - {dropped}))
        script = f"  {dropped}: local-placeholder\n  unset {remaining}\n"
        assert required - _unset_tokens(script) == {dropped}, dropped


def test_python_workflow_enforces_all_snapshot_gas_suites():
    command = _step(
        _workflow()["jobs"]["snapshot-gas"],
        "Enforce snapshot gas budgets",
    )["run"]
    expected_test_files = {
        "tests/priceSources/blueChip/test_bluechip_local.py",
        "tests/priceSources/curve/test_robinhood_launch_route.py",
        "tests/core/test_sc24_gas_matrix.py",
    }
    command_tokens = shlex.split(command)

    assert "-m" in command_tokens
    assert "gas" in command_tokens
    for test_file in expected_test_files:
        assert command_tokens.count(test_file) == 1
