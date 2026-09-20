"""Focused regressions for Base staging review; no RPC or real history writes."""

import ast
import json
import re
import runpy
from pathlib import Path
import subprocess
import sys

import boa
from eth_abi import encode
from eth_utils import event_abi_to_log_topic
import pytest

from config.BluePrint import PARAMS
from scripts.base_upgrade_fork import Rehearsal, permission_keys, remediation_sets
from scripts.base_full_update_fork import FullUpdate
from scripts.utils.fork_reports import require_new_report, sanitize
from scripts.verify_defaults import compare_mission_control_config, SCALAR_GETTERS

ROOT = Path(__file__).resolve().parents[1]


def bare_run(tmp_path):
    run = object.__new__(FullUpdate)
    run.rpc = "https://provider.invalid/v2/FAKE_REVIEW_SECRET"
    run.block = 100
    run.output = tmp_path / "report.json"
    run.report = {}
    return run


def test_sanitizer_handles_split_and_encoded_credentials():
    rpc = "https://provider.invalid/v2/FAKE_REVIEW_SECRET?key=QUERY_SECRET"
    value = {"error": "HTTPSConnectionPool(host='provider.invalid'): /v2/FAKE_REVIEW_SECRET",
             "frames": [rpc, "%2Fv2%2FFAKE_REVIEW_SECRET", "QUERY_SECRET"]}
    result = str(sanitize(value, rpc, ROOT))
    assert "FAKE_REVIEW_SECRET" not in result
    assert "QUERY_SECRET" not in result
    assert "provider.invalid" not in result


@pytest.mark.parametrize("saved", [False, True])
def test_remediation_population_preserves_locks_without_repaying_healthy(saved):
    rows = [dict(user="unhealthy", healthy=False, locked=False),
            dict(user="locked_borrower", healthy=True, locked=True),
            dict(user="healthy", healthy=True, locked=False)]
    # The saved renderer carries affected users; live input carries all borrowers.
    selected = [r for r in rows if not r["healthy"] or r["locked"]] if saved else rows
    debt, checks = remediation_sets(selected, ["locked_borrower", "locked_depositor_no_debt"])
    assert debt == ["unhealthy"]
    assert checks == ["unhealthy", "locked_borrower", "locked_depositor_no_debt"]


def test_nonempty_booster_replay_reads_back_config_and_usage(tmp_path):
    from types import SimpleNamespace
    run = bare_run(tmp_path)
    user = "0x" + "1" * 40
    config = (user, 1000, 3, boa.env.evm.patch.block_number + 100)
    old = SimpleNamespace(address="0x" + "2" * 40, config=lambda u: config, unitsUsed=lambda u: 0)
    event = {"type": "event", "name": "BondBoostModified", "inputs": [{"name": "user", "type": "address", "indexed": False}]}
    run.manifest = {"BondBooster": {"abi": [event]}}
    run.at = lambda *args: old
    run.old = {"BondRoom": SimpleNamespace(bondBooster=lambda: old.address)}
    run.logs = lambda *args: [{"data": "0x" + encode(["address"], [user]).hex()}]
    configs = {}
    new = SimpleNamespace(config=lambda u: configs[u], unitsUsed=lambda u: 0)
    def set_boosters(rows):
        for row in rows:
            configs[row[0]] = row
    delta = SimpleNamespace(setManyBondBoosters=set_boosters)
    run.new = {"BondBooster": new, "SwitchboardDelta": delta}
    run.action = lambda board, fn, rows: fn(rows)
    run.replay_boosters()
    assert configs[user] == config
    assert run.report["booster_replay_coverage"] == "nonempty readback"
    new.unitsUsed = lambda u: 1
    with pytest.raises(AssertionError, match="BOOSTER_USAGE_DRIFT"):
        run.replay_boosters()


@pytest.mark.parametrize("name", ["base_upgrade_fork", "base_full_update_fork", "diagnose_base_undy_prices", "diagnose_base_snapshot_refresh"])
def test_optimized_diagnostic_refuses_before_work(name):
    result = subprocess.run([sys.executable, "-O", "-m", "scripts." + name, "--help"],
                            cwd=ROOT, text=True, capture_output=True)
    assert result.returncode != 0
    assert "FORK_DIAGNOSTIC_OPTIMIZED_PYTHON_UNSUPPORTED" in result.stderr


def test_diagnostic_help_does_not_require_rpc():
    result = subprocess.run([sys.executable, "-m", "scripts.diagnose_base_undy_prices", "--help"],
                            cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0
    assert "--defaults" in result.stdout


def test_report_output_guard(tmp_path):
    path = tmp_path / "report.json"
    path.touch()
    with pytest.raises(RuntimeError, match="REPORT_EXISTS"):
        require_new_report(path)
    require_new_report(path, overwrite=True)


def test_anchor_restores_state_and_scopes_transactions(tmp_path):
    run = bare_run(tmp_path)
    contract = boa.loads("""# @version 0.4.3
value: public(uint256)
@external
def setValue(new_value: uint256):
    self.value = new_value
""")
    run.gov = boa.env.eoa
    with run.diagnostic_branch("alternate"):
        run.transact(contract.setValue, 12)
        assert contract.value() == 12
    assert contract.value() == 0
    assert run.report["fork_transactions"][0]["state_rolled_back"] is True
    assert run.report["fork_transactions"][0]["call_reverted"] is False
    assert run.report["fork_transactions"][0]["branch_id"] == "alternate"


def test_required_child_failure_fails_parent(tmp_path):
    run = bare_run(tmp_path)
    def fail():
        raise RuntimeError("required feed failed")
    run.attempt("parent", lambda: run.attempt("child", fail))
    assert run.report["checks"]["parent"] != "passed"
    assert "child" in run.report["blockers"]


def test_log_discovery_splits_deduplicates_and_records_failure(tmp_path):
    run = bare_run(tmp_path)
    calls = []
    def rpc(method, params):
        query = params[0]
        lo, hi = int(query["fromBlock"], 16), int(query["toBlock"], 16)
        calls.append((lo, hi))
        assert query["topics"] == ["0xtopic", None, "0xrecipient"]
        if hi - lo > 1:
            raise RuntimeError("block range limit")
        rows = [dict(blockNumber=hex(i), blockHash=hex(i), transactionHash=hex(i), logIndex="0x0") for i in range(lo, hi + 1)]
        return rows + rows
    run.rpc_read = rpc
    result = run.filtered_logs({"topics": ["0xtopic", None, "0xrecipient"]}, 0, 7)
    assert len(result) == 8 and len(calls) > 1
    assert run.report["log_discovery"][-1]["complete"]
    run.rpc_read = lambda *args: (_ for _ in ()).throw(RuntimeError("unrecoverable"))
    with pytest.raises(RuntimeError, match="unrecoverable"):
        run.filtered_logs({}, 0, 7)
    assert not run.report["log_discovery"][-1]["complete"]


def test_permission_logs_exclude_foreign_and_reject_bad_known_layout():
    known, foreign, user, caller = ["0x" + str(i) * 40 for i in range(1, 5)]
    abi = {"type": "event", "name": "UserConfigSet", "inputs": [
        {"name": name, "type": "address", "indexed": True} for name in ("user", "caller")]}
    topic = "0x" + event_abi_to_log_topic(abi).hex()
    emitters = {known: {topic: abi}}
    malicious = dict(address=foreign, topics=[topic], data="0x" + encode(["address", "address"], [user, caller]).hex())
    assert permission_keys([malicious], emitters) == (set(), set())
    with pytest.raises(RuntimeError, match="EVENT_TOPIC_SHAPE"):
        permission_keys([dict(malicious, address=known)], emitters)
    proper = dict(address=known, topics=[topic, "0x" + encode(["address"], [user]).hex(),
                                       "0x" + encode(["address"], [caller]).hex()], data="0x")
    assert permission_keys([proper], emitters) == ({user}, set())


def test_orphan_user_asset_cannot_pass_census(tmp_path):
    run = bare_run(tmp_path)
    asset = "0x" + "1" * 40
    run.report["vaults"] = {3: {"assets": {}}}
    class Vault:
        def totalBalances(self, asset):
            return 10
    run.vaults = {3: Vault()}
    with pytest.raises(RuntimeError, match="INCOMPLETE_CENSUS"):
        run.reconcile_positions(3, {"position": {"asset": asset, "shares": 10}})
    row = run.report["census_reconciliation"][3][asset]
    assert row["orphaned"] and row["authoritative_total"] == 10


def test_staging_timing_and_price_constructor_bindings():
    paths = [ROOT / "migrations/base-mainnet" / name for name in (
        "2026091400_StageBaseUpgrade.py", "2026091402_StageBaseOraclesPsmReserves.py")]
    calls = {}
    for path in paths:
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "deploy":
                calls[node.args[0].value] = node
    def argument(name, index):
        return ast.unparse(calls[name].args[index])
    assert argument("HumanResources", 2) == "params['MIN_HQ_CHANGE_TIMELOCK']"
    assert argument("HumanResources", 3) == "params['MAX_HQ_CHANGE_TIMELOCK']"
    assert PARAMS["base"]["MIN_HQ_CHANGE_TIMELOCK"] == 43_200
    assert PARAMS["base"]["MAX_HQ_CHANGE_TIMELOCK"] == 302_400
    assert argument("Lootbox", 2) == "BASE_MIN_UNDERSCORE_SEND_INTERVAL"
    assert argument("VaultBook", 3) == "BASE_ACTIVE_VAULT_BOOK_MIN_TIMELOCK"
    assert argument("PriceDesk", 6) == "params['PRICE_DESK_PRICE_SOURCE_GAS']"
    assert argument("PriceDesk", 7) == "params['PRICE_DESK_SNAPSHOT_SOURCE_GAS']"
    assert PARAMS["base"]["PRICE_DESK_PRICE_SOURCE_GAS"] == 1_500_000
    assert PARAMS["local"]["PRICE_DESK_PRICE_SOURCE_GAS"] == 250_000
    assert PARAMS["robinhood"]["PRICE_DESK_PRICE_SOURCE_GAS"] == 250_000


@pytest.mark.parametrize("drift", ["getPriorityPriceSourceIds", "ripeGovVaultConfig", "liteSigners"])
def test_full_config_comparison_identifies_drift(drift):
    asset = "0x" + "1" * 40
    class Config:
        def __init__(self, changed=False):
            self.changed = changed
        def __getattr__(self, name):
            def value(*args):
                if self.changed and name == drift:
                    return "drift"
                if name in ("numAssets", "numLiteSigners"):
                    return 2
                if name in ("assets", "liteSigners"):
                    return asset
                return (0,)
            return value
    old, new = Config(), Config(True)
    differences = []
    compare_mission_control_config(new, lambda name, *args: getattr(old, name)(*args),
                                  lambda field, got, want: differences.append(field) if got != want else None)
    assert any(field.startswith(drift) for field in differences)


def test_price_desk_current_constructor_bindings(price_desk):
    tree = ast.parse((ROOT / "tests/conf_core.py").read_text())
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == "load"
             and node.args and isinstance(node.args[0], ast.Constant)
             and node.args[0].value == "contracts/registries/PriceDesk.vy"]
    assert len(calls) == 1
    assert len(calls[0].args) == 10
    keys = ("PRICE_DESK_PRICE_SOURCE_GAS", "PRICE_DESK_SNAPSHOT_SOURCE_GAS",
            "PRICE_DESK_HAS_FEED_SOURCE_GAS", "PRICE_DESK_MAX_SOURCE_GAS")
    for index, key in enumerate(keys, 6):
        assert ast.unparse(calls[0].args[index]) == f"PARAMS[fork]['{key}']"
    for profile, budgets in (("base", (1_500_000, 1_500_000, 75_000, 6_000_000)),
                             ("local", (250_000, 150_000, 75_000, 6_000_000)),
                             ("robinhood", (250_000, 150_000, 75_000, 6_000_000))):
        assert tuple(PARAMS[profile][key] for key in keys) == budgets
    assert (price_desk.PRICE_SOURCE_PRICE_GAS(), price_desk.PRICE_SOURCE_SNAPSHOT_GAS(),
            price_desk.PRICE_SOURCE_HAS_FEED_GAS(), price_desk.MAX_SOURCE_GAS()) == (
                250_000, 150_000, 75_000, 6_000_000)


def test_legacy_compatibility_probe_rejects_before_first_mutation():
    run = object.__new__(Rehearsal)
    mutations = []
    run.transact = lambda *args: mutations.append(args)
    run.transact_expect = lambda *args: mutations.append(args)
    # Deliberately omit even the registry fields: validation must precede reads.
    with pytest.raises(RuntimeError, match="BASE_COMPATIBILITY_PROBE_REQUIRES_FULL_UPDATE") as error:
        run.compatibility_probe()
    assert "scripts/base_full_update_fork.py" in str(error.value)
    assert "BASE_ACTIVATION_REQUIRED_SLOT_MISSING:7" in str(error.value)
    assert mutations == []


@pytest.mark.parametrize("module", ("base_upgrade_fork", "base_full_update_fork"))
def test_base_harness_help_remains_available_without_rpc(module):
    result = subprocess.run([sys.executable, "-m", "scripts." + module, "--help"],
                            cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert "--defaults" in result.stdout
    if module == "base_upgrade_fork":
        help_text = " ".join(result.stdout.split())
        for flag in ("probe", "legacy-probe", "ordinary-probe", "stability-probe",
                     "stability-residual", "borrower-audit", "audit-blocker-migrations",
                     "remediate-blockers"):
            assert re.search(
                rf"--{flag} Unsupported here; use scripts/base_full_update_fork.py",
                help_text,
            ), flag


@pytest.mark.parametrize("flag", (
    "--probe", "--legacy-probe", "--ordinary-probe", "--stability-probe",
    "--stability-residual", "--borrower-audit", "--audit-blocker-migrations",
    "--remediate-blockers",
))
def test_legacy_probe_cli_rejects_before_setup(monkeypatch, capsys, flag):
    import scripts.base_upgrade_fork as legacy

    def forbidden(*args, **kwargs):
        pytest.fail("unsupported probe reached setup/RPC/staging")

    for name in ("load_dotenv", "Rehearsal", "fingerprint"):
        monkeypatch.setattr(legacy, name, forbidden)
    monkeypatch.setattr(sys, "argv", [
        "base_upgrade_fork.py", "--block", "1", "--defaults", "not-read.json",
        "--report", "not-written.json", flag,
    ])
    with pytest.raises(SystemExit) as error:
        legacy.main()
    assert error.value.code == 2
    diagnostic = capsys.readouterr().err
    assert "BASE_COMPATIBILITY_PROBE_REQUIRES_FULL_UPDATE" in diagnostic
    assert "scripts/base_full_update_fork.py" in diagnostic
    assert flag in diagnostic


def test_legacy_staging_selection_reaches_load_dotenv(monkeypatch):
    import scripts.base_upgrade_fork as legacy

    class ReachedSupportedSetup(Exception):
        pass

    def reached_setup(*args, **kwargs):
        raise ReachedSupportedSetup

    monkeypatch.setattr(legacy, "load_dotenv", reached_setup)
    monkeypatch.setattr(sys, "argv", [
        "base_upgrade_fork.py", "--block", "1", "--defaults", "not-read.json",
        "--report", "not-written.json", "--census", "--diagnose-replacing-pending",
    ])
    with pytest.raises(ReachedSupportedSetup):
        legacy.main()


ANVIL_ARCHIVE = ROOT / "docs/chains/base/pricedesk-gas-plan/evidence/anvil-estimator-smoke-v5.py"


@pytest.mark.parametrize("value", (None, ""), ids=("missing", "empty"))
def test_archived_anvil_requires_output_before_side_effects(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("PRICEDESK_REVIEW_OUTPUT", raising=False)
    else:
        monkeypatch.setenv("PRICEDESK_REVIEW_OUTPUT", value)

    def forbidden(*args, **kwargs):
        pytest.fail("missing output configuration reached mkdir or Anvil")

    monkeypatch.setattr(Path, "mkdir", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(ANVIL_ARCHIVE), run_name="__main__")
    assert str(error.value) == (
        'Set PRICEDESK_REVIEW_OUTPUT to a non-empty output directory, for example: '
        'export PRICEDESK_REVIEW_OUTPUT="/tmp/pr232 review"'
    )


def test_archived_anvil_output_path_with_spaces(monkeypatch, tmp_path):
    output = tmp_path / "review output with spaces"
    monkeypatch.setenv("PRICEDESK_REVIEW_OUTPUT", str(output))
    launches = []

    def blocked_launch(*args, **kwargs):
        launches.append(args)
        raise RuntimeError("test intercepted Anvil launch")

    monkeypatch.setattr(subprocess, "Popen", blocked_launch)
    runpy.run_path(str(ANVIL_ARCHIVE), run_name="__main__")
    assert len(launches) == 1
    report = json.loads((output / "pricedesk-v5-anvil-smoke.json").read_text())
    assert report["status"] == "blocked"
    assert report["error"] == "test intercepted Anvil launch"
