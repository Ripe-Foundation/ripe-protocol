"""Deployed Robinhood histories may only be extended deliberately.

`scripts/migrate.py` defaults to `--environment v1`, so
`--chain robinhood-mainnet` resolves to `migration_history/robinhood-mainnet/v1`
-- a history whose deployment has already happened. Executing against it would
re-broadcast every transaction and rewrite the committed manifest and logs.

Running against one of these is allowed -- new migrations have to be able to
land -- but never from the default start point. `--start-timestamp` defaults to
"0", which selects every migration from the first, and the resume logic that
would skip ahead does not work here: the history holds only
current-manifest.json, so `_latest_manifest_timestamp()` yields "current" and
`int("current")` raises. Nothing records which migration ran last. So the
runner requires an explicit start point, and anything constructing a Migration
directly fails closed.

The pre-cleanup tree carried this boundary on a flag named `_manifest_v2`,
which made it look like part of the unused H06 manifest-v2 planner. It was not,
and these tests pin it independently of that planner so it cannot be removed
again as scaffolding.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.utils.migration import Migration, MigrationHistoryError
from scripts.utils.migration_runner import MigrationRunner


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


# --- extending a deployed history -----------------------------------------


def _runner(tmp_path: Path, history: str) -> MigrationRunner:
    resolved = tmp_path / history
    resolved.mkdir(parents=True, exist_ok=True)
    return MigrationRunner("migrations/robinhood-mainnet", str(resolved), {})


@pytest.mark.parametrize("history", BLOCKED)
@pytest.mark.parametrize("start", (None, "", "0", 0, "not-a-timestamp"))
def test_deployed_history_refuses_a_default_start_point(tmp_path, history, start):
    # "0" is the CLI default and means "every migration from the first one".
    # Against a live deployment that is a full redeploy, not a resume.
    with pytest.raises(
        MigrationHistoryError, match="H06_DEPLOYED_HISTORY_NEEDS_START_TIMESTAMP"
    ):
        _runner(tmp_path, history)._require_start_point(start)


@pytest.mark.parametrize("history", BLOCKED)
def test_deployed_history_accepts_an_explicit_start_point(tmp_path, history):
    # This is the case that has to work: landing a new migration.
    _runner(tmp_path, history)._require_start_point("2026081200")


@pytest.mark.parametrize("history", ALLOWED)
@pytest.mark.parametrize("start", (None, "0", "2026081200"))
def test_other_histories_need_no_start_point(tmp_path, history, start):
    # Base must keep working exactly as before, including the bare default.
    _runner(tmp_path, history)._require_start_point(start)


@pytest.mark.parametrize("history", BLOCKED)
def test_authorized_construction_executes_against_a_deployed_history(
    tmp_path, history
):
    # The runner passes this once it has established a start point; without it
    # a Migration built by any other caller still fails closed.
    resolved = tmp_path / history
    resolved.mkdir(parents=True, exist_ok=True)
    args = SimpleNamespace(
        sender=SimpleNamespace(address="0x" + "1" * 40),
        ignore_logs=True,
        rpc=None,
        chain=history.split("/")[1],
        blueprint=None,
    )
    migration = Migration(
        args, {}, "9999", None, str(resolved), allow_deployed_history=True
    )

    assert migration._execution_blocked is False
    assert migration.execute(lambda **_: "RECEIPT") == "RECEIPT"
