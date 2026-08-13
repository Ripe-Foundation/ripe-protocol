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
from types import SimpleNamespace

import pytest

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
def test_replay_does_not_bypass_the_start_point(tmp_path, start):
    """--force-replay is the dangerous mode, so it is not an escape hatch.

    An earlier version let `--is-retry` through, on the reading that retrying
    means resuming and is therefore safe. rh inverted that flag:
    `ignore_logs=is_retry`, so the default now resumes and --force-replay
    re-executes. Carried across unchanged, the bypass fired on the default and
    refused the explicit flag -- exactly backwards.
    """
    with pytest.raises(
        MigrationHistoryError, match="H06_DEPLOYED_HISTORY_NEEDS_START_TIMESTAMP"
    ):
        _runner(_history(tmp_path, deployed=True))._require_start_point(
            _args(force_replay=True), start
        )


def test_ccip_wire_is_invisible_to_the_resume_checkpoint():
    """A migration that deploys nothing leaves no numbered manifest.

    2026080701_CcipWire only calls execute() -- it wires the CCIP pools and
    hands them to the Safe -- so _append_manifest never runs. The resume
    checkpoint is derived from numbered manifests, so it cannot see that this
    migration completed, and it has completed: CCIP is live on both mainnets.

    Asserted as the durable fact rather than as "auto-resume selects X", which
    is a function of whatever has been deployed since. Adding a later migration
    that does record a manifest moves the checkpoint past this one and changes
    that answer without changing the hazard.
    """
    root = Path(__file__).resolve().parents[2]
    for chain in ("base-mainnet", "robinhood-mainnet"):
        assert (root / f"migrations/{chain}/2026080701_CcipWire.py").exists()
        assert not (
            root / f"migration_history/{chain}/v1/2026080701-manifest.json"
        ).exists()


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
    steps = list(root.glob("*/*/[0-9]*-manifest.json"))
    assert steps, "expected committed step manifests"

    for path in steps:
        for name, record in json.loads(path.read_text())["contracts"].items():
            where = f"{path.name}:{name}"
            assert set(record) <= {"address", "file"}, where
            assert "address" in record, where


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
            # Solidity deploys are recorded by address alone -- Foundry
            # artifacts have no Vyper compiler-output equivalent
            # (see Migration.deploy_solidity). Everything else keeps the lot.
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


def test_default_resume_consumes_recorded_receipts(tmp_path):
    # Default mode (no --force-replay) reads the journal and skips what it
    # records. This is the production default, so a re-run resumes.
    broadcast = []
    migration = _with_log(tmp_path, ["0xRECORDED"], force_replay=False)

    result = migration.execute(lambda **_: broadcast.append("sent") or "0xNEW")

    # The recorded receipt is returned and nothing is re-broadcast.
    assert result == "0xRECORDED"
    assert broadcast == []


def test_force_replay_ignores_the_journal_and_rebroadcasts(tmp_path):
    # --force-replay is the dangerous mode: it ignores recorded receipts.
    broadcast = []
    migration = _with_log(tmp_path, ["0xRECORDED"], force_replay=True)

    result = migration.execute(lambda **_: broadcast.append("sent") or "0xNEW")

    assert result == "0xNEW"
    assert broadcast == ["sent"]


def test_resume_restarts_at_the_first_incomplete_transaction(tmp_path):
    broadcast = []
    migration = _with_log(tmp_path, ["0xONE", "0xTWO"], force_replay=False)

    first = migration.execute(lambda **_: broadcast.append(1) or "new")
    second = migration.execute(lambda **_: broadcast.append(2) or "new")
    third = migration.execute(lambda **_: broadcast.append(3) or "0xTHREE")

    assert [first, second, third] == ["0xONE", "0xTWO", "0xTHREE"]
    assert broadcast == [3], "only the transaction past the log should run"

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
