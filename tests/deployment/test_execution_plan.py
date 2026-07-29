from __future__ import annotations

import ast
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from config.network_profiles import (
    NETWORK_PROFILES,
    Operation,
    OperationOutcome,
    operation_decision,
)
from scripts import migrate
import scripts.utils.migration_runner as migration_runner
from scripts.utils.migration_runner import (
    MigrationPlanError,
    RESERVATION_DIGEST,
    ROBINHOOD_RESERVATIONS,
    build_blocked_migration_report,
    canonical_jcs_bytes,
    read_bound_h06_history,
    report_bytes,
    report_sha256,
)
from scripts.utils.manifest_schema import (
    HistoryState,
    canonical_json_bytes,
    immutable_basename,
    plan_sha256,
    read_history,
)
from tests.deployment.test_manifest_schema import (
    COMMIT,
    TREE,
    make_index,
    make_plan,
    make_record,
    make_successor,
    make_two_step_plan,
)


ROOT = Path(__file__).resolve().parents[2]
PYTHON = Path(sys.executable)
CURRENT_GLOBAL_BLOCKERS = [
    "B-H04-PARAMS",
    "B-H05-PLAN",
    "B-H05-SOURCE-ABSENT",
    "B-H06-HISTORIES-ABSENT",
    "B-H08-PROOF",
    "B-H09-RELEASE",
    "B-LP-ARTIFACTS",
    "B-ORACLE-FREEZE",
    "B-S5-LEDGER",
    "B-SECOPS-HANDOFF",
]


def _current_git_identity() -> tuple[str, str]:
    identities = []
    for revision in ("HEAD^{commit}", "HEAD^{tree}"):
        result = subprocess.run(
            ["/usr/bin/git", "rev-parse", "--verify", revision],
            cwd=ROOT,
            env={"LANG": "C", "LC_ALL": "C"},
            capture_output=True,
            check=True,
            encoding="ascii",
        )
        assert result.stderr == ""
        identities.append(result.stdout.strip())
    return identities[0], identities[1]


def _assert_current_report_git_identity(report) -> None:
    current_commit, current_tree = _current_git_identity()
    assert report["source_commit"] == current_commit
    assert report["source_tree"] == current_tree
    for identity in (report["source_commit"], report["source_tree"]):
        assert len(identity) == 40
        assert all(character in "0123456789abcdef" for character in identity)


def _report(profile_id="robinhood-mainnet"):
    return build_blocked_migration_report(
        profile_id, repository_root=ROOT
    )


def _run_plan(profile_id="robinhood-mainnet", *extra):
    environment = os.environ.copy()
    for name in tuple(environment):
        if (
            name.endswith("_RPC_URL")
            or "PRIVATE_KEY" in name
            or "SIGNER" in name
            or "ACCOUNT" in name
        ):
            environment.pop(name)
    return subprocess.run(
        [
            str(PYTHON),
            "-m",
            "scripts.migrate",
            "--profile",
            profile_id,
            "--plan",
            *extra,
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        check=False,
    )


def _private_root(path: Path) -> Path:
    path.mkdir(mode=0o700, parents=True)
    path.chmod(0o700)
    return path


def _write_artifact(root: Path, artifact) -> None:
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    root.chmod(0o700)
    if artifact["artifact_kind"] == "current_index":
        name = "current-manifest.json"
    else:
        name = immutable_basename(artifact)
    (root / name).write_bytes(canonical_json_bytes(artifact))


def _valid_history(root: Path, plan=None):
    selected_plan = plan or make_plan()
    record = make_record(plan=selected_plan)
    _write_artifact(root, record)
    _write_artifact(root, make_index(record))
    return selected_plan, record


def test_migration_plan_is_a_ninth_total_operation():
    assert len(Operation) == 9
    for profile in NETWORK_PROFILES:
        assert {policy.operation for policy in profile.operations} == set(
            Operation
        )


@pytest.mark.parametrize(
    ("profile_id", "outcome"),
    (
        ("local", OperationOutcome.UNSUPPORTED),
        ("base-mainnet", OperationOutcome.UNSUPPORTED),
        ("base-sepolia", OperationOutcome.UNSUPPORTED),
        ("robinhood-testnet", OperationOutcome.SUPPORTED),
        ("robinhood-mainnet", OperationOutcome.SUPPORTED),
    ),
)
def test_five_profile_migration_plan_policy(profile_id, outcome):
    profile = next(
        profile
        for profile in NETWORK_PROFILES
        if profile.identity.profile_id == profile_id
    )
    policy = operation_decision(profile, Operation.MIGRATION_PLAN)
    assert policy.outcome is outcome
    assert not policy.requires_rpc
    assert not policy.requires_identity
    assert not policy.requires_repository
    assert not policy.requires_account
    assert not policy.requires_verifier


def test_robinhood_paths_remain_proposed():
    for profile_id in ("robinhood-mainnet", "robinhood-testnet"):
        profile = next(
            profile
            for profile in NETWORK_PROFILES
            if profile.identity.profile_id == profile_id
        )
        assert profile.repository.migration_state.value == "proposed"
        assert profile.repository.history_state.value == "proposed"


@pytest.mark.parametrize(
    ("profile_id", "chain_id", "history_root"),
    (
        (
            "robinhood-mainnet",
            4663,
            "migration_history/robinhood-mainnet/v1",
        ),
        (
            "robinhood-testnet",
            46630,
            "migration_history/robinhood-testnet/v1",
        ),
    ),
)
def test_current_blocked_report_contract(
    profile_id, chain_id, history_root
):
    report = _report(profile_id)
    assert list(report) == [
        "schema",
        "mode",
        "status",
        "profile_id",
        "expected_chain_id",
        "source_root",
        "history_root",
        "source_commit",
        "source_tree",
        "source_digest",
        "reservation_digest",
        "prior_history_digest",
        "steps",
        "blockers",
        "plan_hash",
        "report_sha256",
    ]
    assert report["schema"] == "ripe.robinhood.migration-dry-plan.v1"
    assert report["mode"] == "dry-plan"
    assert report["status"] == "blocked"
    assert report["profile_id"] == profile_id
    assert report["expected_chain_id"] == chain_id
    assert report["source_root"] == "migrations/robinhood"
    assert report["history_root"] == history_root
    _assert_current_report_git_identity(report)
    assert report["source_digest"] is None
    assert report["reservation_digest"] == RESERVATION_DIGEST
    assert report["prior_history_digest"] is None
    assert report["plan_hash"] is None
    assert report["blockers"] == CURRENT_GLOBAL_BLOCKERS
    assert len(report["steps"]) == 18
    assert report["report_sha256"] == report_sha256(report)


@pytest.mark.parametrize("field", ("source_commit", "source_tree"))
def test_independent_git_identity_rejects_wrong_production_report(field):
    report = _report()
    report[field] = "0" * 40
    with pytest.raises(AssertionError):
        _assert_current_report_git_identity(report)


def test_profile_differences_are_limited_to_four_fields_and_hash():
    mainnet = _report("robinhood-mainnet")
    testnet = _report("robinhood-testnet")
    differing = {
        key for key in mainnet if mainnet[key] != testnet[key]
    }
    assert differing == {
        "profile_id",
        "expected_chain_id",
        "history_root",
        "report_sha256",
    }


def test_step_local_blockers_do_not_leak_global():
    report = _report()
    assert all(
        blocker not in report["blockers"]
        for blocker in (
            "B-T8-M5",
            "B-T8-FREEZE",
            "B-PSM-SEQUENCE",
            "B-REWARD-PROMOTION",
            "B-T1-CCIP",
            "B-T1-TOOLCHAIN",
        )
    )
    local = {
        step["migration_id"]: step["blockers"]
        for step in report["steps"]
        if step["blockers"]
    }
    assert local == {
        "0500": ["B-T8-FREEZE", "B-T8-M5"],
        "0600": ["B-REWARD-PROMOTION"],
        "0800": ["B-PSM-SEQUENCE"],
        "1000": ["B-T1-CCIP", "B-T1-TOOLCHAIN"],
    }


def test_historical_blockers_and_integrated_m4_are_not_current():
    rendered = json.dumps(_report(), sort_keys=True)
    for blocker in (
        "B-H03-R5-UNAPPROVED",
        "B-H04-NOT-STARTED",
        "B-S5-STAGE-B-NONCONTROLLING",
        "B-T8-M1-PHASE-B-UNAUTHORIZED",
        "B-T8-M4",
    ):
        assert blocker not in rendered


def test_report_has_no_runtime_or_host_identity():
    report = _report()
    rendered = report_bytes(report).decode("utf-8")
    forbidden_keys = {
        "rpc",
        "endpoint",
        "environment",
        "account",
        "signer",
        "timestamp",
        "hostname",
        "transaction",
        "deployment_args",
    }

    def walk(value):
        if isinstance(value, dict):
            assert forbidden_keys.isdisjoint(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(report)
    assert str(ROOT) not in rendered
    assert "://" not in rendered
    assert "0x" not in rendered


def test_report_self_hash_contract_and_single_lf():
    report = _report()
    payload = report_bytes(report)
    assert payload.endswith(b"\n")
    assert not payload.endswith(b"\n\n")
    parsed = json.loads(payload)
    supplied = parsed.pop("report_sha256")
    canonical_unsigned = canonical_jcs_bytes(parsed)
    assert supplied == hashlib.sha256(canonical_unsigned).hexdigest()
    assert canonical_jcs_bytes(json.loads(payload)) + b"\n" == payload


def test_report_hash_omits_any_supplied_self_hash():
    report = _report()
    expected = report["report_sha256"]
    report["report_sha256"] = "00" * 32
    assert report_sha256(report) == expected
    assert json.loads(report_bytes(report))["report_sha256"] == expected


def test_jcs_utf16_key_order_places_supplementary_before_private_use():
    value = {"\ue000": 1, "\U00010000": 2}
    assert canonical_jcs_bytes(value) == (
        '{"𐀀":2,"\ue000":1}'.encode("utf-8")
    )


def test_jcs_control_character_escaping_is_canonical():
    value = "\x00\b\t\n\f\r\x1f\"\\/"
    assert canonical_jcs_bytes(value) == (
        b'"\\u0000\\b\\t\\n\\f\\r\\u001f\\"\\\\/"'
    )


@pytest.mark.parametrize(
    "value",
    (0.0, 1.5, float("nan"), float("inf"), float("-inf")),
)
def test_jcs_rejects_all_floats_and_nonfinite_numbers(value):
    with pytest.raises(
        MigrationPlanError, match="H05_JCS_FLOAT_FORBIDDEN"
    ):
        canonical_jcs_bytes({"value": value})


def test_jcs_accepts_integers_booleans_and_null_only():
    assert canonical_jcs_bytes(
        {"positive": 2**256, "negative": -(2**255), "flag": True, "n": None}
    ) == (
        b'{"flag":true,"n":null,"negative":-'
        + str(2**255).encode()
        + b',"positive":'
        + str(2**256).encode()
        + b"}"
    )


def test_jcs_rejects_invalid_surrogates_and_nonstring_keys():
    with pytest.raises(MigrationPlanError, match="H05_JCS_UNICODE"):
        canonical_jcs_bytes({"\ud800": 1})
    with pytest.raises(MigrationPlanError, match="H05_JCS_KEY_TYPE"):
        canonical_jcs_bytes({1: "value"})


def test_reservation_digest_is_reproducible():
    assert RESERVATION_DIGEST == (
        "9e8a36c1ed85ce9f27a2b1319a9e0007"
        "8727380d0f4ba42f8d1920030e6cbd91"
    )
    assert [step["migration_id"] for step in _report()["steps"]] == [
        item.migration_id for item in ROBINHOOD_RESERVATIONS
    ]


@pytest.mark.parametrize(
    "profile_id", ("local", "base-mainnet", "base-sepolia")
)
def test_cli_plan_rejects_non_robinhood_profiles(profile_id):
    result = _run_plan(profile_id)
    assert result.returncode != 0
    assert b"H02_OPERATION_UNSUPPORTED" in result.stderr
    assert result.stdout == b""


@pytest.mark.parametrize(
    "flags",
    (
        ("--ask",),
        ("--safe", "0x1"),
        ("--fork",),
        ("--rpc", "https://rpc.invalid"),
        ("--single",),
        ("--environment", "other"),
        ("--start-timestamp", "1"),
        ("--end-timestamp", "1"),
        ("--blueprint", "base"),
        ("--account", "OTHER"),
        ("--ledger", "0"),
        ("--is-retry",),
    ),
)
def test_cli_plan_rejects_every_legacy_flag_family(flags):
    result = _run_plan("robinhood-mainnet", *flags)
    assert result.returncode != 0
    assert b"H05_PLAN_FLAGS_INCOMPATIBLE" in result.stderr
    assert result.stdout == b""


def test_cli_emits_only_the_canonical_report():
    result = _run_plan()
    assert result.returncode == 0, result.stderr.decode()
    assert result.stderr == b""
    assert result.stdout == report_bytes(_report())


def test_cli_is_deterministic_across_separate_processes():
    first = _run_plan()
    second = _run_plan()
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    assert hashlib.sha256(first.stdout).hexdigest() == hashlib.sha256(
        second.stdout
    ).hexdigest()


def test_real_plan_process_never_imports_boa_blueprint_executor_or_h06():
    code = (
        "import sys\n"
        "sys.argv = ['scripts.migrate', '--profile', "
        "'robinhood-mainnet', '--plan']\n"
        "from scripts import migrate\n"
        "for forbidden in ('boa', 'config.BluePrint', "
        "'scripts.utils.migration', 'scripts.utils.manifest_schema'):\n"
        "    assert forbidden not in sys.modules, forbidden\n"
        "migrate.cli.main(standalone_mode=False)\n"
        "for forbidden in ('boa', 'config.BluePrint', "
        "'scripts.utils.migration', 'scripts.utils.manifest_schema'):\n"
        "    assert forbidden not in sys.modules, forbidden\n"
    )
    result = subprocess.run(
        [str(PYTHON), "-c", code],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode()
    assert result.stderr == b""
    assert result.stdout == report_bytes(_report())


def test_plan_mode_does_not_read_environment_or_reach_legacy_setup(
    monkeypatch, capsys
):
    class Environment(dict):
        def __getitem__(self, key):
            raise AssertionError(f"environment read: {key}")

        def get(self, key, default=None):
            raise AssertionError(f"environment read: {key}")

        def __contains__(self, key):
            raise AssertionError(f"environment read: {key}")

    def forbidden(*_args, **_kwargs):
        raise AssertionError("legacy path reached")

    monkeypatch.setattr(migrate.os, "environ", Environment())
    for name in (
        "read_chain_id",
        "get_account",
        "repository_paths",
        "resolve_rpc_reference",
        "verify_chain_identity",
        "validate_fork_request",
        "load_vyper_files",
    ):
        monkeypatch.setattr(migrate, name, forbidden)
    monkeypatch.setattr(
        migrate.MigrationRunner, "_migrations", forbidden
    )
    monkeypatch.setattr(migrate.boa, "fork", forbidden)
    monkeypatch.setattr(
        migrate.boa.deployments, "set_deployments_db", forbidden
    )
    result = migrate.cli.callback(
        ask=False,
        safe="",
        fork=False,
        is_retry=False,
        rpc=None,
        single=False,
        environment="v1",
        start_timestamp="0",
        end_timestamp="0",
        profile_id="robinhood-mainnet",
        blueprint=None,
        account="DEPLOYER",
        ledger=-1,
        plan=True,
    )
    assert result is None
    assert capsys.readouterr().out.encode() == report_bytes(_report())


def test_plan_mode_does_not_import_execution_blueprint_or_h06(monkeypatch):
    source = (ROOT / "scripts/migrate.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "cli"
    )
    plan_branch = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "plan"
    )
    calls = {
        node.func.id
        for node in ast.walk(plan_branch)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
    }
    assert "build_blocked_migration_report" in calls
    assert "DeployArgs" not in calls
    assert "get_account" not in calls
    assert "read_chain_id" not in calls
    assert "MigrationRunner" not in calls
    assert any(isinstance(node, ast.Return) for node in plan_branch.body)
    assert source.index("if plan:") < source.index(
        "from scripts.utils.deploy_args import DeployArgs"
    )


def test_static_plan_call_graph_has_no_writer_or_execution_primitive():
    source = (
        ROOT / "scripts/utils/migration_runner.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    reachable = set()
    pending = ["build_blocked_migration_report", "report_bytes"]
    while pending:
        name = pending.pop()
        if name in reachable:
            continue
        reachable.add(name)
        node = functions[name]
        for call in (
            item for item in ast.walk(node) if isinstance(item, ast.Call)
        ):
            if (
                isinstance(call.func, ast.Name)
                and call.func.id in functions
                and call.func.id not in reachable
            ):
                pending.append(call.func.id)

    rendered = "\n".join(
        ast.unparse(functions[name]) for name in sorted(reachable)
    )
    for forbidden in (
        "DeployArgs",
        "get_account",
        "EthereumRPC",
        "boa.",
        "Migration(",
        "importlib.util",
        "exec_module",
        "publish_immutable",
        "promote_current_index",
        "os.makedirs",
        ".mkdir(",
        ".write_bytes(",
        ".write_text(",
        "open(",
        "transaction",
        "signer",
        "simulate",
        "broadcast",
    ):
        assert forbidden not in rendered
    assert "subprocess.run" in rendered
    assert ".read_bytes(" in rendered
    assert ".lstat(" in rendered


def test_source_absence_short_circuits_h06_import(monkeypatch):
    imported = []
    real_import = __import__

    def tracking(name, *args, **kwargs):
        imported.append(name)
        if name == "scripts.utils.manifest_schema":
            raise AssertionError("H-06 imported without a source plan")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", tracking)
    report = _report()
    assert report["source_digest"] is None
    assert "scripts.utils.manifest_schema" not in imported


def test_cli_creates_no_repository_state():
    before = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    result = _run_plan()
    after = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    assert result.returncode == 0
    assert after == before
    assert not (ROOT / "migrations/robinhood").exists()
    assert not (ROOT / "migration_history/robinhood-mainnet").exists()
    assert not (ROOT / "migration_history/robinhood-testnet").exists()


def test_h06_public_binding_validates_and_reads_valid_history(tmp_path):
    root = _private_root(tmp_path / "valid")
    plan, record = _valid_history(root)
    digest, result = read_bound_h06_history(
        plan,
        profile_id="robinhood-mainnet",
        expected_chain_id=4663,
        source_commit=COMMIT,
        source_tree=TREE,
        history_root=root,
    )
    assert digest == plan_sha256(plan)
    assert result.state is HistoryState.VALID
    assert result.head["record_sha256"] == record["record_sha256"]


def test_h06_binding_rejects_profile_and_source_substitution(tmp_path):
    plan = make_plan()
    with pytest.raises(
        MigrationPlanError, match="H05_PLAN_PROFILE_MISMATCH"
    ):
        read_bound_h06_history(
            plan,
            profile_id="robinhood-testnet",
            expected_chain_id=46630,
            source_commit=COMMIT,
            source_tree=TREE,
            history_root=tmp_path / "unused",
        )
    with pytest.raises(
        MigrationPlanError, match="H05_PLAN_SOURCE_MISMATCH"
    ):
        read_bound_h06_history(
            plan,
            profile_id="robinhood-mainnet",
            expected_chain_id=4663,
            source_commit="11" * 20,
            source_tree=TREE,
            history_root=tmp_path / "unused",
        )


def test_synthetic_h06_history_state_matrix(tmp_path):
    plan = make_plan()
    digest = plan_sha256(plan)

    valid_root = _private_root(tmp_path / "valid")
    _, valid_record = _valid_history(valid_root, plan)

    absent_root = tmp_path / "absent"

    incomplete_root = _private_root(tmp_path / "incomplete")
    _write_artifact(incomplete_root, make_record(plan=plan))

    corrupt_root = _private_root(tmp_path / "corrupt")
    (corrupt_root / "current-manifest.json").write_bytes(b"{broken")

    stale_root = _private_root(tmp_path / "stale")
    two_step = make_two_step_plan()
    first = make_record(plan=two_step, step_ordinal=0)
    second = make_successor(first, plan=two_step)
    _write_artifact(stale_root, first)
    _write_artifact(stale_root, second)
    _write_artifact(stale_root, make_index(first))

    ambiguous_root = _private_root(tmp_path / "ambiguous")
    lock = ambiguous_root / ".manifest-v2.lock"
    lock.touch(mode=0o600)
    lock.chmod(0o600)
    lock_fd = os.open(lock, os.O_RDWR | os.O_NOFOLLOW)
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        states = {
            "valid": read_history(
                "robinhood-mainnet",
                4663,
                digest,
                COMMIT,
                TREE,
                valid_root,
            ).state,
            "absent-clean": read_history(
                "robinhood-mainnet",
                4663,
                digest,
                COMMIT,
                TREE,
                absent_root,
            ).state,
            "incomplete": read_history(
                "robinhood-mainnet",
                4663,
                digest,
                COMMIT,
                TREE,
                incomplete_root,
            ).state,
            "corrupt": read_history(
                "robinhood-mainnet",
                4663,
                digest,
                COMMIT,
                TREE,
                corrupt_root,
            ).state,
            "stale": read_history(
                "robinhood-mainnet",
                4663,
                plan_sha256(two_step),
                COMMIT,
                TREE,
                stale_root,
            ).state,
            "wrong-profile": read_history(
                "robinhood-testnet",
                46630,
                digest,
                COMMIT,
                TREE,
                valid_root,
            ).state,
            "wrong-chain": read_history(
                "robinhood-mainnet",
                1,
                digest,
                COMMIT,
                TREE,
                valid_root,
            ).state,
            "wrong-plan": read_history(
                "robinhood-mainnet",
                4663,
                plan_sha256(two_step),
                COMMIT,
                TREE,
                valid_root,
            ).state,
            "ambiguous": read_history(
                "robinhood-mainnet",
                4663,
                digest,
                COMMIT,
                TREE,
                ambiguous_root,
            ).state,
        }
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)

    assert states == {
        "valid": HistoryState.VALID,
        "absent-clean": HistoryState.ABSENT_CLEAN,
        "incomplete": HistoryState.INCOMPLETE,
        "corrupt": HistoryState.CORRUPT,
        "stale": HistoryState.STALE,
        "wrong-profile": HistoryState.WRONG_PROFILE,
        "wrong-chain": HistoryState.WRONG_CHAIN,
        "wrong-plan": HistoryState.WRONG_PLAN,
        "ambiguous": HistoryState.AMBIGUOUS,
    }
    assert valid_record["source"]["plan_sha256"] == digest


def test_history_state_never_changes_phase_b_plan_hash(tmp_path):
    report = _report()
    for state in HistoryState:
        candidate = copy.deepcopy(report)
        candidate["blockers"] = sorted(
            set(candidate["blockers"])
            | {f"B-H06-SYNTHETIC-{state.value.upper()}"}
        )
        assert candidate["status"] == "blocked"
        assert candidate["plan_hash"] is None
        assert candidate["mode"] == "dry-plan"
