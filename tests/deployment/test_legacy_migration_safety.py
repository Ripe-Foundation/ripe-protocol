from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.utils.migration as migration_module
from scripts.utils.migration import Migration
from scripts.utils.migration_runner import MigrationRunner


def _args(*, ignore_logs: bool = False):
    return SimpleNamespace(ignore_logs=ignore_logs, rpc="redacted")


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value))


def _migration(tmp_path: Path, *, timestamp: str = "2") -> Migration:
    return Migration(_args(), {}, timestamp, "1", str(tmp_path))


def test_deployment_stays_pending_until_migration_end(
    tmp_path, monkeypatch
):
    active = {
        "contracts": {
            "Service": {"address": "0x" + "1" * 40, "file": "old.vy"}
        }
    }
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)

    def manifest(contracts, contract_files, args, files):
        return {
            "contracts": {
                name: {"address": value, "file": "new.vy"}
                for name, value in contracts.items()
            }
        }

    monkeypatch.setattr(
        migration_module, "deployed_contracts_manifest", manifest
    )
    migration = _migration(tmp_path)
    migration._contracts["Service"] = "0x" + "2" * 40
    migration._append_manifest("Service")

    assert json.loads((tmp_path / "current-manifest.json").read_text()) == active
    assert not (tmp_path / "2-manifest.json").exists()
    pending = json.loads(
        (tmp_path / "2-pending-manifest.json").read_text()
    )
    assert pending["contracts"]["Service"]["address"] == "0x" + "2" * 40

    migration.end()

    assert not (tmp_path / "2-pending-manifest.json").exists()
    assert json.loads((tmp_path / "2-manifest.json").read_text()) == pending
    assert json.loads((tmp_path / "current-manifest.json").read_text()) == pending


def test_pending_manifest_without_transaction_log_fails_closed(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        migration_module,
        "deployed_contracts_manifest",
        lambda contracts, *args: {
            "contracts": {
                name: {"address": value, "file": "new.vy"}
                for name, value in contracts.items()
            }
        },
    )
    first = _migration(tmp_path)
    first._contracts["Service"] = "0x" + "2" * 40
    first._append_manifest("Service")

    with pytest.raises(
        RuntimeError, match="MIGRATION_RESUME_STATE_INCOMPLETE"
    ):
        _migration(tmp_path)


def test_force_replay_refuses_an_existing_pending_journal(tmp_path):
    _write_json(tmp_path / "2-pending-manifest.json", {"contracts": {}})
    _write_json(tmp_path / "2-log.json", {"transactions": ["0xabc"]})

    with pytest.raises(RuntimeError, match="MIGRATION_FORCE_REPLAY_PENDING"):
        Migration(_args(ignore_logs=True), {}, "2", "1", str(tmp_path))


def _migration_source(path: Path, name: str) -> None:
    path.joinpath(name).write_text("def migrate(migration):\n    return None\n")


def test_auto_resume_requires_a_numeric_completion_checkpoint(tmp_path):
    source = tmp_path / "source"
    history = tmp_path / "history"
    source.mkdir()
    history.mkdir()
    _migration_source(source, "001_first.py")
    _migration_source(source, "002_second.py")
    _write_json(history / "current-manifest.json", {"contracts": {}})

    runner = MigrationRunner(str(source), str(history), {})
    with pytest.raises(
        RuntimeError, match="MIGRATION_RESUME_CHECKPOINT_REQUIRED"
    ):
        list(runner._migrations())

    # An explicit start remains an intentional operator override.
    assert [row[1] for row in runner._migrations("0")] == ["001", "002"]


def test_auto_resume_uses_only_finalized_numeric_manifests(tmp_path):
    source = tmp_path / "source"
    history = tmp_path / "history"
    source.mkdir()
    history.mkdir()
    _migration_source(source, "001_first.py")
    _migration_source(source, "002_second.py")
    _write_json(history / "current-manifest.json", {"contracts": {}})
    _write_json(history / "001-manifest.json", {"contracts": {}})
    _write_json(
        history / "999-pending-manifest.json", {"contracts": {}}
    )

    runner = MigrationRunner(str(source), str(history), {})
    assert [row[1] for row in runner._migrations()] == ["002"]


def test_empty_history_starts_from_first_migration(tmp_path):
    source = tmp_path / "source"
    history = tmp_path / "history"
    source.mkdir()
    history.mkdir()
    _migration_source(source, "001_first.py")

    runner = MigrationRunner(str(source), str(history), {})
    assert [row[1] for row in runner._migrations()] == ["001"]
