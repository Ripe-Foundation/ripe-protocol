"""Standard-runner ordering only; synthetic histories never touch tracked history.

These do not qualify the actual deployments or interrupted Stage 2 recovery.
"""

import json
from types import SimpleNamespace

import pytest

from scripts.utils.migration import MigrationHistoryError
from scripts.utils.migration_runner import MigrationRunner


TIMESTAMPS = ("2026081200", "2026082400", "2026082401",
              "2026091400", "2026091401", "2026091402")


def synthetic_runner(tmp_path):
    scripts = tmp_path / "migrations"
    history = tmp_path / "history"
    scripts.mkdir()
    history.mkdir()
    for timestamp in TIMESTAMPS:
        # The actual runner performs loading, start validation and checkpointing.
        # Bodies have no contracts or RPC: this fixture isolates runner ordering.
        (scripts / f"{timestamp}_Synthetic.py").write_text(
            "def migrate(migration):\n"
            f"    assert migration.timestamp() == '{timestamp}'\n"
        )
    empty = {"contracts": {}}
    (history / "current-manifest.json").write_text(json.dumps(empty))
    (history / "2026081200-manifest.json").write_text(json.dumps(empty))
    args = SimpleNamespace(ignore_logs=False, rpc="unused", chain="base-mainnet")
    return MigrationRunner(str(scripts), str(history), {}), args, history


@pytest.mark.parametrize("start", TIMESTAMPS[3:])
def test_standard_runner_refuses_staging_before_ccip_prerequisites(tmp_path, start):
    runner, args, history = synthetic_runner(tmp_path)
    original = {p.name: p.read_bytes() for p in history.iterdir()}
    with pytest.raises(MigrationHistoryError, match="H06_START_TIMESTAMP_NOT_NEXT"):
        runner.run(args, start_timestamp=start)
    assert {p.name: p.read_bytes() for p in history.iterdir()} == original


def test_standard_runner_accepts_ordered_stages_after_synthetic_prerequisites(tmp_path):
    runner, args, history = synthetic_runner(tmp_path)
    # Let the runner create the synthetic prerequisite checkpoints itself.
    runner.run(args, start_timestamp="2026082400", end_timestamp="2026082401")
    for timestamp in TIMESTAMPS[3:]:
        runner.run(args, start_timestamp=timestamp, end_timestamp=timestamp)
        assert (history / f"{timestamp}-manifest.json").is_file()
    with pytest.raises(MigrationHistoryError, match="H06_START_TIMESTAMP_NOT_AFTER_FRONTIER"):
        runner.run(args, start_timestamp="2026091400")
