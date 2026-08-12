"""A deployed history may be extended, but not redeployed by accident.

`_append_manifest` writes `current-manifest.json` on the first successful step,
so its presence is the evidence that migrations have already run against a
history, and the one signal every history has: the mainnet step manifests were
recovered from git, but the testnet ones were not, `end()` deletes the
transaction log on success, and the current manifest records contracts with no
step attribution.

That matters because extending and redoing are the same command.
`--start-timestamp` defaults to `"0"`, and the runner selects every migration
with a timestamp `>= 0` — all 13 for `robinhood-mainnet`, all 66 for
`base-mainnet`. So a bare run against a deployed history is a full redeploy, not
a resume.

`MigrationRunner` therefore requires either an explicit `--start-timestamp` or
`--is-retry`, and `Migration` fails closed for any other caller. A history with
no current manifest is a first deployment and is unaffected.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.utils.migration import (CURRENT_MANIFEST, Migration,
                                     MigrationHistoryError,
                                     history_has_deployment)
from scripts.utils.migration_runner import MigrationRunner


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep this suite independent of protocol deployment."""


def _args(is_retry: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        sender=SimpleNamespace(address="0x" + "1" * 40),
        # migrate.py passes ignore_logs=not is_retry.
        ignore_logs=not is_retry,
        rpc=None,
        chain="robinhood-mainnet",
        blueprint=None,
    )


def _history(tmp_path: Path, *, deployed: bool) -> Path:
    resolved = tmp_path / "migration_history/robinhood-mainnet/v1"
    resolved.mkdir(parents=True, exist_ok=True)
    if deployed:
        (resolved / CURRENT_MANIFEST).write_text(json.dumps({"contracts": {}}))
    return resolved


def _migration(history: Path, **kwargs) -> Migration:
    return Migration(_args(), {}, "9999", None, str(history), **kwargs)


def _runner(history: Path) -> MigrationRunner:
    return MigrationRunner("migrations/robinhood-mainnet", str(history), {})


# --- what counts as deployed ----------------------------------------------


def test_current_manifest_is_what_marks_a_history_deployed(tmp_path):
    fresh = _history(tmp_path / "fresh", deployed=False)
    deployed = _history(tmp_path / "deployed", deployed=True)

    assert history_has_deployment(fresh) is False
    assert history_has_deployment(deployed) is True


def test_every_committed_history_is_recognised_as_deployed():
    root = Path(__file__).resolve().parents[2] / "migration_history"
    histories = [p for p in root.glob("*/*") if p.is_dir()]
    assert histories, "expected committed histories"
    for history in histories:
        assert history_has_deployment(history), history


def test_mainnet_step_manifests_are_retained():
    """Per-step history is kept for the mainnets.

    An earlier revision pruned every numbered manifest, leaving only
    `current-manifest.json`. That discarded per-step attribution — which
    migration deployed which contract, and each generation of a redeployed one
    — and it is the reason `_latest_manifest_timestamp()` had nothing to
    resume from. The mainnet manifests were recovered from git; the testnet
    ones were not retained.
    """
    root = Path(__file__).resolve().parents[2] / "migration_history"
    steps = {
        f"{p.parent.name}/{p.name}": len(list(p.glob("[0-9]*-manifest.json")))
        for p in root.glob("*/*")
        if p.is_dir()
    }
    assert steps["base-mainnet/v1"] >= 60
    assert steps["robinhood-mainnet/v1"] >= 11


# --- the runner decides ----------------------------------------------------


@pytest.mark.parametrize("start", (None, "", "0", 0, "not-a-timestamp"))
def test_deployed_history_refuses_a_default_start_point(tmp_path, start):
    # "0" is the CLI default and means "every migration from the first one".
    with pytest.raises(
        MigrationHistoryError, match="H06_DEPLOYED_HISTORY_NEEDS_START_TIMESTAMP"
    ):
        _runner(_history(tmp_path, deployed=True))._require_start_point(
            _args(), start
        )


def test_deployed_history_accepts_an_explicit_start_point(tmp_path):
    # The case that has to work: landing a new migration.
    _runner(_history(tmp_path, deployed=True))._require_start_point(
        _args(), "2026081200"
    )


@pytest.mark.parametrize("start", (None, "", "0"))
def test_deployed_history_accepts_is_retry(tmp_path, start):
    # Resuming a run that failed partway. --is-retry is also what makes the
    # per-step skip read the transaction log at all.
    _runner(_history(tmp_path, deployed=True))._require_start_point(
        _args(is_retry=True), start
    )


@pytest.mark.parametrize("start", (None, "0", "2026081200"))
def test_first_deployment_needs_no_start_point(tmp_path, start):
    # No current manifest means nothing has run here yet.
    _runner(_history(tmp_path, deployed=False))._require_start_point(
        _args(), start
    )


# --- Migration fails closed for any other caller ---------------------------


def test_execute_is_refused_and_writes_no_log(tmp_path):
    history = _history(tmp_path, deployed=True)
    migration = _migration(history)

    with pytest.raises(MigrationHistoryError, match="H06_LEGACY_EXECUTION_FORBIDDEN"):
        migration.execute(lambda **_: "BROADCASTABLE")

    assert not (history / "9999-log.json").exists()


def test_solidity_deploy_is_refused(tmp_path):
    # deploy_solidity does not route through _run, so it needs its own gate.
    with pytest.raises(MigrationHistoryError, match="H06_LEGACY_EXECUTION_FORBIDDEN"):
        _migration(_history(tmp_path, deployed=True)).deploy_solidity("AnyContract")


def test_manifest_write_is_refused(tmp_path):
    history = _history(tmp_path, deployed=True)

    with pytest.raises(
        MigrationHistoryError, match="H06_LEGACY_MANIFEST_WRITE_FORBIDDEN"
    ):
        _migration(history)._append_manifest("AnyContract")

    assert not (history / "9999-manifest.json").exists()
    # The committed manifest must be exactly as it was.
    assert json.loads((history / CURRENT_MANIFEST).read_text()) == {"contracts": {}}


def test_log_read_is_refused(tmp_path):
    with pytest.raises(MigrationHistoryError, match="H06_LEGACY_LOG_FORBIDDEN"):
        _migration(_history(tmp_path, deployed=True))._load_log_file()


def test_end_reports_gas_without_touching_the_log(tmp_path):
    history = _history(tmp_path, deployed=True)
    migration = _migration(history)
    stale_log = history / "9999-log.json"
    stale_log.write_text("{}")

    assert migration.end() == migration.gas
    assert stale_log.read_text() == "{}"


def test_authorized_construction_executes(tmp_path):
    # What the runner passes once it has established a deliberate start point.
    migration = _migration(
        _history(tmp_path, deployed=True), allow_deployed_history=True
    )

    assert migration._execution_blocked is False
    assert migration.execute(lambda **_: "RECEIPT") == "RECEIPT"


def test_first_deployment_is_never_blocked(tmp_path):
    migration = _migration(_history(tmp_path, deployed=False))

    assert migration._execution_blocked is False
    assert migration.execute(lambda **_: "RECEIPT") == "RECEIPT"


# --- resuming must not re-run the completed migration ----------------------


def _mainnet_runner(chain: str) -> MigrationRunner:
    root = Path(__file__).resolve().parents[2]
    return MigrationRunner(
        str(root / f"migrations/{chain}"),
        str(root / f"migration_history/{chain}/v1"),
        {},
    )


@pytest.mark.parametrize("chain", ("base-mainnet", "robinhood-mainnet"))
def test_inclusive_flag_actually_changes_selection(chain):
    """`inclusive=False` must exclude the start timestamp.

    It was declared, documented and passed by the auto-resume call, but never
    read: both modes compared with `>=`, so they returned identical lists. No
    test asserted they differ, and none could while the step manifests were
    pruned -- with no numbered manifest on disk the resume point was None,
    which selects everything regardless of the flag.
    """
    runner = _mainnet_runner(chain)
    resume = runner._latest_manifest_timestamp()
    assert resume is not None, "needs committed step manifests"

    inclusive = [t for _, t, _ in runner._filtered_migration_filenames(
        resume, "0", inclusive=True)]
    exclusive = [t for _, t, _ in runner._filtered_migration_filenames(
        resume, "0", inclusive=False)]

    assert resume in inclusive
    assert resume not in exclusive
    assert exclusive == [t for t in inclusive if t != resume]


@pytest.mark.parametrize("chain", ("base-mainnet", "robinhood-mainnet"))
def test_auto_resume_does_not_rerun_the_last_completed_migration(chain):
    # The concrete hazard: 2026080700 deploys the CCIP token pools, so
    # re-running it would deploy a second set against a live chain.
    runner = _mainnet_runner(chain)
    resume = runner._latest_manifest_timestamp()

    selected = [timestamp for _, timestamp, _ in runner._migrations(None, "0")]

    assert resume not in selected
    assert all(int(t) > int(resume) for t in selected)
