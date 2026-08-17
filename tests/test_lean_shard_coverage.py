import ast
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


def _workflow_lean_shard_arguments():
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
