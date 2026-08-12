"""The already-deployed Robinhood histories refuse legacy execution.

`scripts/migrate.py` defaults to `--environment v1`, so
`--chain robinhood-mainnet` resolves to `migration_history/robinhood-mainnet/v1`
-- a history whose deployment has already happened. Executing against it would
re-broadcast every transaction and rewrite the committed manifest and logs.

The pre-cleanup tree carried this boundary on a flag named `_manifest_v2`,
which made it look like part of the unused H06 manifest-v2 planner. It was not,
and these tests pin the boundary independently of that planner so it cannot be
removed again as scaffolding.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.utils.migration import Migration, MigrationHistoryError


BLOCKED = (
    "migration_history/robinhood-mainnet/v1",
    "migration_history/robinhood-testnet/v1",
)
ALLOWED = (
    # Base is the actively deployed chain and must keep working.
    "migration_history/base-mainnet/v1",
    "migration_history/base-sepolia/v1",
    # Only v1 of the Robinhood histories is deployed.
    "migration_history/robinhood-mainnet/v2",
    "migration_history/robinhood-testnet/v2",
)


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep this suite independent of protocol deployment."""


def _migration(tmp_path: Path, history: str) -> Migration:
    resolved = tmp_path / history
    resolved.mkdir(parents=True, exist_ok=True)
    args = SimpleNamespace(
        sender=SimpleNamespace(address="0x" + "1" * 40),
        ignore_logs=True,
        rpc=None,
        chain=history.split("/")[1],
        blueprint=None,
    )
    return Migration(args, {}, "9999", None, str(resolved))


@pytest.mark.parametrize("history", BLOCKED)
def test_execute_is_refused_and_writes_no_log(tmp_path, history):
    migration = _migration(tmp_path, history)

    with pytest.raises(MigrationHistoryError, match="H06_LEGACY_EXECUTION_FORBIDDEN"):
        migration.execute(lambda **_: "BROADCASTABLE")

    assert not (tmp_path / history / "9999-log.json").exists()


@pytest.mark.parametrize("history", BLOCKED)
def test_solidity_deploy_is_refused(tmp_path, history):
    # deploy_solidity does not route through _run, so it needs its own gate.
    migration = _migration(tmp_path, history)

    with pytest.raises(MigrationHistoryError, match="H06_LEGACY_EXECUTION_FORBIDDEN"):
        migration.deploy_solidity("AnyContract")


@pytest.mark.parametrize("history", BLOCKED)
def test_manifest_write_is_refused(tmp_path, history):
    migration = _migration(tmp_path, history)

    with pytest.raises(
        MigrationHistoryError, match="H06_LEGACY_MANIFEST_WRITE_FORBIDDEN"
    ):
        migration._append_manifest("AnyContract")

    assert not (tmp_path / history / "current-manifest.json").exists()
    assert not (tmp_path / history / "9999-manifest.json").exists()


@pytest.mark.parametrize("history", BLOCKED)
def test_log_read_is_refused(tmp_path, history):
    migration = _migration(tmp_path, history)

    with pytest.raises(MigrationHistoryError, match="H06_LEGACY_LOG_FORBIDDEN"):
        migration._load_log_file()


@pytest.mark.parametrize("history", BLOCKED)
def test_end_reports_gas_without_touching_the_log(tmp_path, history):
    migration = _migration(tmp_path, history)
    stale_log = tmp_path / history / "9999-log.json"
    stale_log.write_text("{}")

    assert migration.end() == migration.gas
    # end() must not delete or rewrite anything in a deployed history.
    assert stale_log.read_text() == "{}"


@pytest.mark.parametrize("history", ALLOWED)
def test_other_histories_are_not_blocked(tmp_path, history):
    migration = _migration(tmp_path, history)

    assert migration._execution_blocked is False
    # The boundary must not be what stops these; reaching normal execution is
    # the point. Base is live and its migrations still have to run.
    assert migration.execute(lambda **_: "RECEIPT") == "RECEIPT"


def test_boundary_matches_on_path_suffix_not_absolute_prefix(tmp_path):
    # Migrations are invoked with paths relative to wherever migrate.py runs,
    # so the check has to hold on a suffix rather than an absolute location.
    nested = _migration(tmp_path / "deeply" / "nested", BLOCKED[0])
    assert nested._execution_blocked is True
