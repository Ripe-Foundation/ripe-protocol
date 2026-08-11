from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import boa
import pytest

import scripts.utils.migration as migration_module
from scripts.utils.migration import Migration
from scripts.utils.migration_helpers import (
    NO_OUTPUT_TRANSACTION_RESULT,
    TransactionExecutionError,
    execute_transaction,
)
from scripts.utils.migration_runner import MigrationRunner


def _args(*, ignore_logs: bool = False):
    return SimpleNamespace(ignore_logs=ignore_logs, rpc="redacted")


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value))


def _migration(tmp_path: Path, *, timestamp: str = "2") -> Migration:
    return Migration(_args(), {}, timestamp, "1", str(tmp_path))


class _AbiCallable:
    def __init__(self, outputs, result=None, error=None):
        self._abi = {
            "type": "function",
            "name": "synthetic",
            "inputs": [],
            "outputs": outputs,
        }
        self._result = result
        self._error = error
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self._error is not None:
            raise self._error
        return self._result


class _Registry:
    def __init__(self, address: str):
        self.address = address

    def getAddr(self, registry_id: int) -> str:
        assert registry_id == 7
        return self.address


def test_vyper_zero_output_success_is_durably_logged_and_resumable(tmp_path):
    contract = boa.loads(
        """
stored: public(uint256)

@external
def set_stored(new_value: uint256):
    self.stored = new_value
"""
    )
    deploy_args = SimpleNamespace(
        ignore_logs=False,
        rpc="redacted",
        sender=SimpleNamespace(address=boa.env.eoa),
    )

    migration = Migration(deploy_args, {}, "2", "1", str(tmp_path))
    result = migration.execute(contract.set_stored, 41)

    assert result == NO_OUTPUT_TRANSACTION_RESULT
    assert result
    assert contract.stored() == 41
    assert json.loads((tmp_path / "2-log.json").read_text()) == {
        "transactions": [NO_OUTPUT_TRANSACTION_RESULT]
    }

    resumed = Migration(deploy_args, {}, "2", "1", str(tmp_path))
    assert resumed.execute(contract.set_stored, 99) == NO_OUTPUT_TRANSACTION_RESULT
    assert contract.stored() == 41


def test_abi_none_requires_explicit_zero_outputs():
    no_output_transaction = _AbiCallable([])
    assert (
        execute_transaction(no_output_transaction, no_retry=True)
        == NO_OUTPUT_TRANSACTION_RESULT
    )
    assert no_output_transaction.calls == 1

    transaction = _AbiCallable([{"name": "", "type": "uint256"}])

    with pytest.raises(
        TransactionExecutionError, match="MIGRATION_TRANSACTION_FAILED"
    ):
        execute_transaction(transaction, no_retry=True)

    assert transaction.calls == 1


def test_raised_zero_output_function_remains_fail_closed():
    transaction = _AbiCallable([], error=RuntimeError("synthetic failure"))

    with pytest.raises(
        TransactionExecutionError, match="MIGRATION_TRANSACTION_FAILED"
    ):
        execute_transaction(transaction, no_retry=True)

    assert transaction.calls == 1


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


def test_candidate_promotion_copies_complete_record_after_registry_readback(
    tmp_path,
):
    old = {
        "address": "0x" + "1" * 40,
        "file": "old.vy",
        "abi": [{"name": "old"}],
        "args": ["stale"],
        "old_only": True,
    }
    candidate = {
        "address": "0x" + "2" * 40,
        "file": "new.vy",
        "abi": [{"name": "new"}],
        "args": ["fresh"],
        "solc_json": {"compiler": "exact"},
        "future_field": {"preserve": [1, 2, 3]},
    }
    active = {
        "contracts": {
            "Service": old,
            "ServiceCandidate": candidate,
        }
    }
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)

    migration = _migration(tmp_path)
    promoted = migration.promote_candidate(
        "Service", "ServiceCandidate", _Registry(candidate["address"]), 7
    )

    assert promoted == candidate["address"]
    pending = json.loads(
        (tmp_path / "2-pending-manifest.json").read_text()
    )
    assert pending["contracts"]["Service"] == candidate
    assert pending["contracts"]["ServiceCandidate"] == candidate
    assert "old_only" not in pending["contracts"]["Service"]
    assert json.loads(
        (tmp_path / "current-manifest.json").read_text()
    ) == active

    migration.end()
    assert json.loads(
        (tmp_path / "current-manifest.json").read_text()
    ) == pending
    assert json.loads((tmp_path / "2-manifest.json").read_text()) == pending


def test_candidate_promotion_mismatch_is_write_free(tmp_path):
    active = {
        "contracts": {
            "Service": {
                "address": "0x" + "1" * 40,
                "file": "old.vy",
            },
            "ServiceCandidate": {
                "address": "0x" + "2" * 40,
                "file": "new.vy",
                "abi": [{"name": "new"}],
            },
        }
    }
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    _write_json(tmp_path / "2-manifest.json", {"sentinel": True})
    current_before = (tmp_path / "current-manifest.json").read_bytes()
    timestamp_before = (tmp_path / "2-manifest.json").read_bytes()

    migration = _migration(tmp_path)
    with pytest.raises(
        RuntimeError, match="MIGRATION_CANDIDATE_REGISTRY_MISMATCH"
    ):
        migration.promote_candidate(
            "Service",
            "ServiceCandidate",
            _Registry("0x" + "3" * 40),
            7,
        )

    assert (tmp_path / "current-manifest.json").read_bytes() == current_before
    assert (tmp_path / "2-manifest.json").read_bytes() == timestamp_before
    assert not (tmp_path / "2-pending-manifest.json").exists()


def test_candidate_promotion_accepts_distinct_activation_witness(tmp_path):
    defaults = {
        "address": "0x" + "2" * 40,
        "file": "DefaultsRobinhoodLive.vy",
        "args": [],
    }
    mission_control = {
        "address": "0x" + "3" * 40,
        "file": "MissionControl.vy",
        "args": [defaults["address"]],
    }
    active = {
        "contracts": {
            "Defaults": {
                "address": "0x" + "1" * 40,
                "file": "old.vy",
            },
            "DefaultsCandidate": defaults,
            "MissionControlCandidate": mission_control,
        }
    }
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)

    migration = _migration(tmp_path)
    migration.promote_candidate(
        "Defaults",
        "DefaultsCandidate",
        _Registry(mission_control["address"]),
        7,
        activation_candidate_label="MissionControlCandidate",
    )

    pending = json.loads(
        (tmp_path / "2-pending-manifest.json").read_text()
    )
    assert pending["contracts"]["Defaults"] == defaults
    assert pending["contracts"]["DefaultsCandidate"] == defaults
    assert (
        pending["contracts"]["MissionControlCandidate"] == mission_control
    )


def test_candidate_promotion_can_create_first_canonical_label(tmp_path):
    candidate = {
        "address": "0x" + "2" * 40,
        "file": "BlueChipYieldPrices.vy",
        "abi": [{"name": "getPrice"}],
        "args": ["0x" + "3" * 40],
        "future_field": {"preserve": True},
    }
    active = {
        "contracts": {
            "BlueChipYieldPricesCandidate": candidate,
        }
    }
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)

    migration = _migration(tmp_path)
    migration.promote_candidate(
        "BlueChipYieldPrices",
        "BlueChipYieldPricesCandidate",
        _Registry(candidate["address"]),
        7,
    )

    pending = json.loads(
        (tmp_path / "2-pending-manifest.json").read_text()
    )
    assert pending["contracts"]["BlueChipYieldPrices"] == candidate
    assert pending["contracts"]["BlueChipYieldPricesCandidate"] == candidate
    assert "BlueChipYieldPrices" not in active["contracts"]


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
