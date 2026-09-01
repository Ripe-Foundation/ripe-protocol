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

`MigrationRunner` therefore requires an explicit `--start-timestamp` before it
will run against such a history. `--force-replay` is not a bypass: it ignores
the transaction journal and rebroadcasts, which is the more dangerous mode. It is
the only production constructor of `Migration`, so that is where the check
lives; `Migration` itself does not gate, because rh's resume suite legitimately
builds one directly against temporary histories that carry a current manifest.
A history with no current manifest is a first deployment and is unaffected.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest

import scripts.utils.migration as migration_module
from scripts.utils.migration import (CURRENT_MANIFEST, Migration,
                                     MigrationHistoryError,
                                     history_has_deployment)
from scripts.utils.migration_runner import MigrationRunner


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep this suite independent of protocol deployment."""


def _args(force_replay: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        sender=SimpleNamespace(address="0x" + "1" * 40),
        # Production mapping, from scripts/migrate.py: ignore_logs=is_retry,
        # exposed as --force-replay (legacy alias --is-retry). Setting it
        # ignores the journal and rebroadcasts; the default resumes from it.
        ignore_logs=force_replay,
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


def test_migration_exposes_the_immediate_source_predecessor(tmp_path):
    history = _history(tmp_path, deployed=False)
    migration = Migration(_args(), {}, "2026082405", "2026082101", str(history))

    assert migration.timestamp() == "2026082405"
    assert migration.previous_timestamp() == "2026082101"


def test_every_committed_history_is_recognised_as_deployed():
    root = Path(__file__).resolve().parents[2] / "migration_history"
    histories = [p for p in root.glob("*/*") if p.is_dir()]
    assert histories, "expected committed histories"
    for history in histories:
        assert history_has_deployment(history), history


def test_optimized_python_cannot_import_or_execute_a_migration(tmp_path):
    migrations = tmp_path / "migrations"
    history = tmp_path / "history"
    sentinel = tmp_path / "migration-imported"
    migrations.mkdir()
    history.mkdir()
    (migrations / "0001_probe.py").write_text(
        f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('reached')\n"
        "def migrate(_migration):\n    raise AssertionError('must not run')\n"
    )
    code = """
import sys
from scripts.utils.migration_runner import MigrationRunner
try:
    MigrationRunner(sys.argv[1], sys.argv[2], {}).run(None, "0001")
except Exception as exc:
    if "MIGRATION_OPTIMIZED_MODE_FORBIDDEN" in str(exc):
        raise SystemExit(0)
    print(repr(exc), file=sys.stderr)
    raise SystemExit(2)
raise SystemExit(3)
"""
    result = subprocess.run(
        [sys.executable, "-O", "-c", code, str(migrations), str(history)],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert not sentinel.exists()


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


def test_a_history_without_a_checkpoint_cannot_be_continued(tmp_path):
    # A current manifest with no numeric completion marker proves nothing is
    # finished, so no start point can be shown to be safe.
    with pytest.raises(MigrationHistoryError, match="H06_NO_RECORDED_FRONTIER"):
        _runner(_history(tmp_path, deployed=True))._require_start_point(
            _args(), "2026082405"
        )


@pytest.mark.parametrize("start", (None, "", "0", "1", "2026080700"))
def test_replay_does_not_bypass_the_start_point(tmp_path, start):
    """--force-replay is the dangerous mode, so it is not an escape hatch.

    An earlier version let `--is-retry` through, on the reading that retrying
    means resuming and is therefore safe. rh inverted that flag:
    `ignore_logs=is_retry`, so the default now resumes and --force-replay
    re-executes. Carried across unchanged, the bypass fired on the default and
    refused the explicit flag -- exactly backwards.

    Each value fails for its own reason (no start point, unknown migration, no
    recorded frontier); what matters here is that replay never unlocks one.
    """
    with pytest.raises(MigrationHistoryError):
        _runner(_history(tmp_path, deployed=True))._require_start_point(
            _args(force_replay=True), start
        )


def test_ccip_plan_and_activation_completion_are_separate_migrations():
    """Safe-pending preparation cannot stand in for activation completion."""
    root = Path(__file__).resolve().parents[2]
    stages = {
        "base-mainnet": ("2026082400_CcipWirePlan.py", "2026082401_CcipActivationFinalized.py"),
    }
    for chain, (plan_name, final_name) in stages.items():
        plan = (root / "migrations" / chain / plan_name).read_text()
        final = (root / "migrations" / chain / final_name).read_text()
        assert "records only that the preparation stage ran" in plan
        assert "require_mainnet_activation_finalized" in final


def test_new_mainnet_migrations_are_strictly_after_the_recorded_frontier():
    root = Path(__file__).resolve().parents[2]
    for chain in ("base-mainnet", "robinhood-mainnet"):
        history = root / "migration_history" / chain / "v1"
        frontier = max(
            int(path.name.removesuffix("-manifest.json"))
            for path in history.glob("*-manifest.json")
            if path.name != "current-manifest.json"
        )
        pending = [
            path
            for path in (root / "migrations" / chain).glob("*.py")
            if int(path.name.split("_", 1)[0]) >= 2026080701
            and not (history / f"{path.name.split('_', 1)[0]}-manifest.json").exists()
        ]
        required_frontier = max(frontier, 2026082101)
        assert all(
            int(path.name.split("_", 1)[0]) > required_frontier for path in pending
        )


@pytest.mark.parametrize("chain", ("base-mainnet", "robinhood-mainnet"))
def test_no_deployed_history_can_be_auto_resumed(chain):
    # Whatever the checkpoint currently reports, a bare run against a deployed
    # history is refused. This is the invariant; the selection is not.
    root = Path(__file__).resolve().parents[2]
    runner = MigrationRunner(
        str(root / f"migrations/{chain}"),
        str(root / f"migration_history/{chain}/v1"),
        {},
    )

    with pytest.raises(
        MigrationHistoryError, match="H06_DEPLOYED_HISTORY_NEEDS_START_TIMESTAMP"
    ):
        runner._require_start_point(_args(), None)


@pytest.mark.parametrize("start", (None, "0", "2026081200"))
def test_first_deployment_needs_no_start_point(tmp_path, start):
    # No current manifest means nothing has run here yet.
    _runner(_history(tmp_path, deployed=False))._require_start_point(
        _args(), start
    )


# --- Migration fails closed for any other caller ---------------------------


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


# --- step manifests carry the record, not the bulk -------------------------


def test_step_manifests_keep_the_record_and_drop_the_bulk():
    """Step manifests record what was deployed; they do not carry compiler output.

    `deployed_contracts_manifest` emits address/abi/solc_json/args/file. A step
    manifest keeps address+file: which contract, deployed where, from which
    source. That is the attribution `verify --migration` and the checklist run
    on, and it is all anything reads from one.

    The rest is dropped because nothing reads it from a step manifest. `abi`
    has no manifest reader anywhere. `solc_json` and `args` are consumed only
    by the Etherscan verifier, and verification runs against
    `current-manifest.json` by owner decision -- `verify` refuses a numbered
    manifest outright and redirects to `--migration`.
    """
    root = Path(__file__).resolve().parents[2] / "migration_history"
    steps = [
        path
        for path in root.glob("*/*/[0-9]*-manifest.json")
        if re.fullmatch(r"\d+-manifest\.json", path.name)
    ]
    assert steps, "expected committed step manifests"

    for path in steps:
        for name, record in json.loads(path.read_text())["contracts"].items():
            where = f"{path.name}:{name}"
            assert set(record) <= {"address", "file"}, where
            assert "address" in record, where


def test_end_writes_a_slim_step_manifest_scoped_to_this_migration(tmp_path, monkeypatch):
    """The producer, not just the committed data, matches the documented schema.

    A prior revision documented the address/file-only, this-step-only shape
    but never implemented it: `end()` copied the full cumulative manifest --
    same bytes as current-manifest.json -- to the numbered file too. It read
    as slim only because the committed step manifests had been hand-trimmed
    after the fact; the next real migration would have silently written the
    bulk format again. This exercises the actual write path.
    """
    history = _history(tmp_path, deployed=False)
    (history / "current-manifest.json").write_text(json.dumps({
        "contracts": {
            "Existing": {
                "address": "0x" + "1" * 40,
                "file": "Existing.vy",
                "abi": [{"name": "old"}],
                "solc_json": {"old": True},
                "args": "old",
            }
        }
    }))

    def fake_manifest(contracts, contract_files, args, files):
        return {
            "contracts": {
                name: {
                    "address": value,
                    "file": "New.vy",
                    "abi": [{"name": "new"}],
                    "solc_json": {"language": "Vyper"},
                    "args": "encoded",
                }
                for name, value in contracts.items()
            }
        }

    monkeypatch.setattr(migration_module, "deployed_contracts_manifest", fake_manifest)
    migration = _migration(history)
    migration._contracts["New"] = "0x" + "2" * 40
    migration._append_manifest("New")
    migration.end()

    step = json.loads((history / "9999-manifest.json").read_text())
    current = json.loads((history / "current-manifest.json").read_text())

    # current-manifest.json is untouched: cumulative, full record, both
    # contracts.
    assert set(current["contracts"]) == {"Existing", "New"}
    assert current["contracts"]["New"]["abi"] == [{"name": "new"}]

    # The step manifest attributes only what *this* migration deployed --
    # "New", not the pre-existing "Existing" -- and only address/file.
    assert step == {"contracts": {"New": {"address": "0x" + "2" * 40, "file": "New.vy"}}}


def test_end_writes_an_empty_step_manifest_when_nothing_was_deployed(tmp_path):
    """An execute-only migration attributes nothing, not everything before it.

    CcipWire-shaped migrations call only `execute()`, which never reaches
    `_append_manifest`. Before this, `end()` fell back to
    `self._previous_manifest` -- the full cumulative history -- and wrote
    that to the numbered manifest, so an execute-only step would have claimed
    every contract ever deployed as its own.
    """
    history = _history(tmp_path, deployed=False)
    (history / "current-manifest.json").write_text(json.dumps({
        "contracts": {"Existing": {"address": "0x" + "1" * 40, "file": "Existing.vy"}}
    }))

    migration = _migration(history)
    migration.end()

    step = json.loads((history / "9999-manifest.json").read_text())
    assert step == {"contracts": {}}


def test_current_manifests_keep_everything():
    # current-manifest.json is the runtime authority -- prepare_defaults,
    # verify, verify_blockscout, console and Migration.__init__ all read it.
    root = Path(__file__).resolve().parents[2] / "migration_history"
    currents = list(root.glob("*/*/current-manifest.json"))
    assert currents

    vyper_fields = {"abi", "solc_json", "args", "file"}
    kept = 0
    for path in currents:
        for name, record in json.loads(path.read_text())["contracts"].items():
            where = f"{path.parent.parent.name}/{path.parent.name}:{name}"
            assert "address" in record, where
            # Solidity deploys keep their authenticated artifact/runtime intent
            # in the transaction journal. The manifest remains the address
            # index and has no Vyper compiler-output equivalent.
            if vyper_fields & set(record):
                assert vyper_fields <= set(record), where
                kept += 1
    assert kept, "expected current manifests to retain Vyper compiler output"


# --- retrying a migration that failed partway ------------------------------


def _with_log(tmp_path: Path, recorded, *, force_replay: bool):
    history = _history(tmp_path, deployed=True)
    (history / "9999-log.json").write_text(json.dumps({"transactions": recorded}))
    args = SimpleNamespace(
        sender=SimpleNamespace(address="0x" + "1" * 40),
        ignore_logs=force_replay,
        rpc=None,
        chain="robinhood-mainnet",
        blueprint=None,
    )
    return Migration(
        args, {}, "9999", None, str(history)
    )


class _JournalCall:
    def __init__(self, target: str, calldata: bytes, result, broadcasts):
        self.contract = SimpleNamespace(address=target)
        self._calldata = calldata
        self._result = result
        self._broadcasts = broadcasts

    def prepare_calldata(self):
        return self._calldata

    def __call__(self, **_kwargs):
        self._broadcasts.append(self._calldata)
        return self._result


def _record(migration: Migration, call: _JournalCall, receipt, **kwargs):
    return {
        **migration._transaction_intent(call, (), kwargs),
        "receipt": receipt,
    }


def test_default_resume_consumes_recorded_receipts(tmp_path):
    # Default mode (no --force-replay) reads the journal and skips what it
    # records. This is the production default, so a re-run resumes.
    broadcast = []
    call = _JournalCall("0x" + "2" * 40, b"\x01", "0xNEW", broadcast)
    migration = _with_log(
        tmp_path,
        [],
        force_replay=False,
    )
    migration._transactions = [_record(migration, call, "0xRECORDED")]

    result = migration.execute(call)

    # The recorded receipt is returned and nothing is re-broadcast.
    assert result == "0xRECORDED"
    assert broadcast == []


def test_force_replay_ignores_the_journal_and_rebroadcasts(tmp_path):
    # --force-replay is the dangerous mode: it ignores recorded receipts.
    broadcast = []
    call = _JournalCall("0x" + "2" * 40, b"\x01", "0xNEW", broadcast)
    migration = _with_log(
        tmp_path,
        [],
        force_replay=True,
    )

    result = migration.execute(call)

    assert result == "0xNEW"
    assert broadcast == [b"\x01"]


def test_resume_restarts_at_the_first_incomplete_transaction(tmp_path):
    broadcast = []
    first_call = _JournalCall("0x" + "2" * 40, b"\x01", "new", broadcast)
    second_call = _JournalCall("0x" + "3" * 40, b"\x02", "new", broadcast)
    third_call = _JournalCall("0x" + "4" * 40, b"\x03", "0xTHREE", broadcast)
    migration = _with_log(
        tmp_path,
        [],
        force_replay=False,
    )
    migration._transactions = [
        _record(migration, first_call, "0xONE"),
        _record(migration, second_call, "0xTWO"),
    ]

    first = migration.execute(first_call)
    second = migration.execute(second_call)
    third = migration.execute(third_call)

    assert [first, second, third] == ["0xONE", "0xTWO", "0xTHREE"]
    assert broadcast == [b"\x03"], "only the transaction past the log should run"


def test_end_rejects_unconsumed_authenticated_journal_entries(tmp_path):
    first_call = _JournalCall("0x" + "2" * 40, b"\x01", "new", [])
    second_call = _JournalCall("0x" + "3" * 40, b"\x02", "new", [])
    seed = _with_log(tmp_path, [], force_replay=False)
    records = [
        _record(seed, first_call, "0xONE"),
        _record(seed, second_call, "0xTWO"),
    ]
    migration = _with_log(tmp_path, records, force_replay=False)
    history = Path(migration._history_path)
    current_before = (history / CURRENT_MANIFEST).read_bytes()

    assert migration.execute(first_call) == "0xONE"
    log_before = (history / "9999-log.json").read_bytes()
    with pytest.raises(
        RuntimeError,
        match="MIGRATION_TRANSACTION_LOG_UNCONSUMED",
    ):
        migration.end()

    assert (history / CURRENT_MANIFEST).read_bytes() == current_before
    assert (history / "9999-log.json").read_bytes() == log_before
    assert not (history / "9999-manifest.json").exists()


def test_force_replay_replaces_the_journal_and_can_complete(tmp_path):
    broadcasts = []
    call = _JournalCall("0x" + "2" * 40, b"\x01", "0xNEW", broadcasts)
    migration = _with_log(tmp_path, ["legacy-entry"], force_replay=True)
    history = Path(migration._history_path)

    assert migration.execute(call) == "0xNEW"
    assert migration.end() == 0
    assert broadcasts == [b"\x01"]
    assert not (history / "9999-log.json").exists()
    assert (history / "9999-manifest.json").exists()


@pytest.mark.parametrize(
    ("field", "replacement", "error"),
    (
        (
            "target",
            "0x" + "9" * 40,
            "MIGRATION_TRANSACTION_TARGET_MISMATCH",
        ),
        (
            "calldata_sha256",
            "0" * 64,
            "MIGRATION_TRANSACTION_CALLDATA_MISMATCH",
        ),
        (
            "chain",
            "base-mainnet",
            "MIGRATION_TRANSACTION_CHAIN_MISMATCH",
        ),
        (
            "sender",
            "0x" + "8" * 40,
            "MIGRATION_TRANSACTION_SENDER_MISMATCH",
        ),
        (
            "value",
            1,
            "MIGRATION_TRANSACTION_VALUE_MISMATCH",
        ),
    ),
)
def test_resume_rejects_changed_execution_intent(
    tmp_path,
    field,
    replacement,
    error,
):
    call = _JournalCall("0x" + "2" * 40, b"\x01", "new", [])
    migration = _with_log(tmp_path, [], force_replay=False)
    record = _record(migration, call, "0xRECORDED")
    record[field] = replacement
    migration._transactions = [record]

    with pytest.raises(RuntimeError, match=error):
        migration.execute(call)


def test_resume_rejects_legacy_position_only_transaction_log(tmp_path):
    call = _JournalCall("0x" + "2" * 40, b"\x01", "new", [])
    migration = _with_log(tmp_path, ["0xRECORDED"], force_replay=False)

    with pytest.raises(
        RuntimeError,
        match="MIGRATION_TRANSACTION_LOG_UNAUTHENTICATED",
    ):
        migration.execute(call)


@pytest.mark.parametrize("recorded", ({}, "", 0, False))
def test_resume_rejects_falsey_malformed_transaction_log(tmp_path, recorded):
    call = _JournalCall("0x" + "2" * 40, b"\x01", "new", [])
    migration = _with_log(tmp_path, [recorded], force_replay=False)

    with pytest.raises(
        RuntimeError,
        match="MIGRATION_TRANSACTION_LOG_UNAUTHENTICATED",
    ):
        migration.execute(call)


@pytest.mark.parametrize(
    ("filename", "payload", "error"),
    (
        ("current-manifest.json", "{broken", "MIGRATION_CURRENT_MANIFEST_INVALID"),
        (
            "current-manifest.json",
            json.dumps({}),
            "MIGRATION_CURRENT_MANIFEST_INVALID",
        ),
        (
            "current-manifest.json",
            json.dumps([]),
            "MIGRATION_CURRENT_MANIFEST_INVALID",
        ),
        ("9999-log.json", "{broken", "MIGRATION_TRANSACTION_LOG_INVALID"),
        (
            "9999-log.json",
            json.dumps({"transactions": {}}),
            "MIGRATION_TRANSACTION_LOG_INVALID",
        ),
    ),
)
def test_malformed_resume_state_fails_closed(tmp_path, filename, payload, error):
    history = _history(tmp_path, deployed=False)
    (history / filename).write_text(payload)

    with pytest.raises(RuntimeError, match=error):
        _migration(history)


@pytest.mark.parametrize(
    "payload",
    (
        "{broken",
        json.dumps({}),
        json.dumps([]),
        json.dumps({"contracts": []}),
    ),
)
def test_end_revalidates_pending_checkpoint_before_any_completion_write(
    tmp_path,
    payload,
):
    history = _history(tmp_path, deployed=True)
    pending = history / "9999-pending-manifest.json"
    transaction_log = history / "9999-log.json"
    pending.write_text(json.dumps({"contracts": {}}))
    transaction_log.write_text(json.dumps({"transactions": []}))
    migration = _migration(history)

    pending.write_text(payload)
    current_before = (history / CURRENT_MANIFEST).read_bytes()
    pending_before = pending.read_bytes()
    log_before = transaction_log.read_bytes()

    with pytest.raises(
        RuntimeError,
        match="MIGRATION_PENDING_MANIFEST_INVALID",
    ):
        migration.end()

    assert (history / CURRENT_MANIFEST).read_bytes() == current_before
    assert pending.read_bytes() == pending_before
    assert transaction_log.read_bytes() == log_before
    assert not (history / "9999-manifest.json").exists()


def test_solidity_deployment_resume_binds_artifact_args_sender_and_runtime(
    tmp_path, monkeypatch
):
    history = _history(tmp_path, deployed=False)
    address = "0x" + "7" * 40
    runtime = b"runtime-v1"
    contract = SimpleNamespace(address=address)
    base_intent = {
        "version": 1,
        "kind": "solidity_deploy",
        "chain": "robinhood-mainnet",
        "sender": "0x" + "1" * 40,
        "contract": "Synthetic",
        "source_file": "Synthetic.sol",
        "artifact_sha256": "a" * 64,
        "creation_sha256": "b" * 64,
    }
    monkeypatch.setattr(
        migration_module.solidity,
        "deployment_intent",
        lambda *_args, **_kwargs: dict(base_intent),
    )
    monkeypatch.setattr(
        migration_module.solidity, "deploy", lambda *_args, **_kwargs: contract
    )
    monkeypatch.setattr(
        migration_module.solidity, "at", lambda *_args, **_kwargs: contract
    )
    monkeypatch.setattr(migration_module.boa.env, "get_code", lambda _address: runtime)

    migration = _migration(history)
    assert migration.deploy_solidity("Synthetic") is contract

    resumed = _migration(history)
    assert resumed.deploy_solidity("Synthetic") is contract

    changed_intent = dict(base_intent, creation_sha256="c" * 64)
    monkeypatch.setattr(
        migration_module.solidity,
        "deployment_intent",
        lambda *_args, **_kwargs: dict(changed_intent),
    )
    with pytest.raises(
        RuntimeError, match="MIGRATION_SOLIDITY_DEPLOYMENT_INTENT_MISMATCH"
    ):
        _migration(history).deploy_solidity("Synthetic")

    monkeypatch.setattr(
        migration_module.solidity,
        "deployment_intent",
        lambda *_args, **_kwargs: dict(base_intent),
    )
    monkeypatch.setattr(
        migration_module.boa.env, "get_code", lambda _address: b"runtime-v2"
    )
    with pytest.raises(
        RuntimeError, match="MIGRATION_SOLIDITY_DEPLOYMENT_RUNTIME_MISMATCH"
    ):
        _migration(history).deploy_solidity("Synthetic")

# --- one boundary, and it is the runner's -----------------------------------


def test_migration_advertises_no_second_boundary():
    """There is exactly one execution boundary and it lives in the runner.

    An earlier revision left `Migration` carrying an `allow_deployed_history`
    kwarg defaulted to True and `_execution_blocked` assigned False, with
    branches that could never fire -- a safety API that read as enforcement and
    was inert. Enforcement is `MigrationRunner._require_start_point`; the class
    makes no claim of its own.
    """
    import inspect

    from scripts.utils import migration as module

    assert "allow_deployed_history" not in inspect.signature(
        module.Migration.__init__
    ).parameters
    source = Path(module.__file__).read_text()
    assert "_execution_blocked" not in source

    # And the migrations no longer promise a protection that was removed.
    root = Path(__file__).resolve().parents[2]
    for path in (root / "migrations/robinhood-mainnet").glob("*.py"):
        text = path.read_text()
        assert "H-06 Robinhood runner intentionally rejects" not in text, path
        assert "H-06 Robinhood runner deliberately forbids" not in text, path


def test_direct_construction_cannot_bypass_the_runner_boundary(tmp_path):
    """Constructing a Migration directly is not a way around the check.

    The runner is the only production constructor, so the boundary sits there.
    This pins the fact the reviewer asked for: the deployed-history refusal
    cannot be sidestepped by building a Migration yourself and calling run
    logic, because the refusal is what stands between a caller and a Migration
    at all.
    """
    history = _history(tmp_path, deployed=True)
    runner = MigrationRunner("migrations/robinhood-mainnet", str(history), {})

    with pytest.raises(
        MigrationHistoryError, match="H06_DEPLOYED_HISTORY_NEEDS_START_TIMESTAMP"
    ):
        runner.run(_args(), None, "0", True)


def test_attaching_an_old_generation_hides_only_the_boa_bytecode_dump(
    monkeypatch, tmp_path
):
    import warnings

    migration = _migration(_history(tmp_path, deployed=False))
    address = "0x" + "2" * 40
    migration._previous_manifest = {
        "contracts": {
            "OldGeneration": {
                "file": "contracts/core/OldGeneration.vy",
                "address": address,
            }
        }
    }

    attached = object()

    class Partial:
        def at(self, observed_address):
            assert observed_address == address
            warnings.warn(
                "casted bytecode does not match compiled bytecode at <old>",
                UserWarning,
            )
            warnings.warn("separate useful warning", UserWarning)
            return attached

    monkeypatch.setattr(migration_module.boa, "load_partial", lambda _file: Partial())

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert migration.get_contract("OldGeneration") is attached

    assert [str(item.message) for item in caught] == ["separate useful warning"]


def test_accepted_start_constructs_and_runs_migration(tmp_path):
    """The accepted runner path must construct the current Migration API.

    The deployed-history boundary is owned by MigrationRunner. After that
    boundary accepted an explicit start, run() still passed the removed
    ``allow_deployed_history`` keyword to Migration and failed before invoking
    the selected migration. Exercise a complete no-deployment step so this
    constructor call cannot drift out of sync again.
    """
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "0002_Accepted.py").write_text(
        "def migrate(migration):\n"
        "    assert migration.timestamp() == '0002'\n"
    )

    history = tmp_path / "history"
    history.mkdir()
    manifest = {"contracts": {}}
    (history / CURRENT_MANIFEST).write_text(json.dumps(manifest))
    (history / "0001-manifest.json").write_text(json.dumps(manifest))

    runner = MigrationRunner(str(migrations), str(history), {})
    assert runner.run(_args(), "0002", "0002", False) == 0

    assert json.loads((history / CURRENT_MANIFEST).read_text()) == manifest
    assert json.loads((history / "0002-manifest.json").read_text()) == manifest


# --- the start point has to name something, and be after the frontier -------


def _real_runner(chain="robinhood-mainnet"):
    root = Path(__file__).resolve().parents[2]
    return MigrationRunner(
        str(root / f"migrations/{chain}"),
        str(root / f"migration_history/{chain}/v1"),
        {},
    )


def _ordered_runner(tmp_path):
    """A deployed history with one required next step and one later step."""
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    for filename in ("0001_First.py", "0002_Completed.py", "0003_Next.py", "0004_Later.py"):
        (migrations / filename).write_text("def migrate(migration):\n    pass\n")

    history = _history(tmp_path, deployed=True)
    (history / "0002-manifest.json").write_text(json.dumps({"contracts": {}}))
    return MigrationRunner(str(migrations), str(history), {})


@pytest.mark.parametrize(
    ("start", "code"),
    (
        (None, "H06_DEPLOYED_HISTORY_NEEDS_START_TIMESTAMP"),
        ("", "H06_DEPLOYED_HISTORY_NEEDS_START_TIMESTAMP"),
        ("0", "H06_DEPLOYED_HISTORY_NEEDS_START_TIMESTAMP"),
        ("nonsense", "H06_DEPLOYED_HISTORY_NEEDS_START_TIMESTAMP"),
        # `1` satisfied int(value) > 0 and selected 16 migrations on
        # robinhood-mainnet -- the redeployment the guard exists to prevent.
        ("1", "H06_START_TIMESTAMP_UNKNOWN"),
        ("9", "H06_START_TIMESTAMP_UNKNOWN"),
        ("99999999999", "H06_START_TIMESTAMP_UNKNOWN"),
        # Names real migrations, but ones this history already completed.
        ("0001", "H06_START_TIMESTAMP_NOT_AFTER_FRONTIER"),
        ("0002", "H06_START_TIMESTAMP_NOT_AFTER_FRONTIER"),
        ("0000", "H06_DEPLOYED_HISTORY_NEEDS_START_TIMESTAMP"),
    ),
)
def test_unsafe_start_points_are_refused(tmp_path, start, code):
    with pytest.raises(MigrationHistoryError, match=code):
        _ordered_runner(tmp_path)._require_start_point(_args(), start)


def test_the_earliest_unfinished_start_point_is_accepted(tmp_path):
    runner = _ordered_runner(tmp_path)
    frontier = runner._latest_manifest_timestamp()

    runner._require_start_point(_args(), "0003")
    assert int("0003") > int(frontier)


def test_a_later_unfinished_start_point_cannot_skip_the_next_stage(tmp_path):
    with pytest.raises(
        MigrationHistoryError,
        match=r"H06_START_TIMESTAMP_NOT_NEXT: .* would skip 0003",
    ):
        _ordered_runner(tmp_path)._require_start_point(_args(), "0004")


@pytest.mark.parametrize("chain", ("base-mainnet", "robinhood-mainnet"))
def test_run_rejects_before_importing_or_writing_anything(tmp_path, chain):
    """The refusal binds to run(), not just the helper.

    A guard that only holds when called directly proves nothing about the
    execution path: run() imports the migration module, invokes its callback,
    writes a log and can broadcast. Nothing of that may happen.
    """
    root = Path(__file__).resolve().parents[2]
    history = tmp_path / "history"
    history.mkdir()
    # A deployed history, copied so the real one cannot be written to.
    (history / CURRENT_MANIFEST).write_text(
        (root / f"migration_history/{chain}/v1/{CURRENT_MANIFEST}").read_text()
    )
    (history / "2026080700-manifest.json").write_text(json.dumps({"contracts": {}}))
    runner = MigrationRunner(str(root / f"migrations/{chain}"), str(history), {})

    with pytest.raises(MigrationHistoryError):
        runner.run(_args(), "1", "0", True)

    # No log, no manifest, nothing executed.
    assert sorted(p.name for p in history.iterdir()) == [
        "2026080700-manifest.json",
        CURRENT_MANIFEST,
    ]
