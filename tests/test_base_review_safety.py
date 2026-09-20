"""Focused regressions for Base staging review; no RPC or real history writes."""

import ast
from pathlib import Path
import subprocess
import sys

import boa
from eth_abi import encode
from eth_utils import event_abi_to_log_topic
import pytest

from config.BluePrint import PARAMS
from scripts.base_upgrade_fork import Rehearsal, ZERO, permission_keys, remediation_sets
from scripts.base_full_update_fork import DeploymentAdapter, FullUpdate, SUFFIX
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


@pytest.mark.parametrize("key", ["VaultBook", "VaultBookPopulated"])
def test_full_update_adapter_binds_fresh_vault_book_to_retained_pool(tmp_path, legacy_env, key):
    e = legacy_env
    run = bare_run(tmp_path)
    run.vaults = {1: e.pool}
    run.new = {}
    run.report.update(deployments={}, constructor_profile="local review test")
    adapter = DeploymentAdapter(run, None)
    temp_gov = ZERO if key == "VaultBook" else e.alice
    registrar = e.gov.address if key == "VaultBook" else e.alice
    book = adapter.deploy("VaultBook", e.hq.address, temp_gov, 21_600, 100_000,
                          label=key + SUFFIX)
    assert book.address != e.book.address
    assert run.new["VaultBook"] is book
    assert run.report["deployments"][key]["constructor_args"] == [
        e.hq.address, temp_gov, 21_600, 100_000, e.pool.address]
    book.startAddNewAddressToRegistry(e.pool, "Retained Pool 1", sender=registrar)
    assert book.confirmNewAddressToRegistry(e.pool, sender=registrar) == 1
    assert book.hasStabilityPoolInterface(e.pool, e.sg, e.sg)
    assert not book.canAcceptLiquidationAsset(e.pool, e.lp, e.collateral)
    e.deposit(e.bob, 100 * 10**18)
    assert book.canAcceptLiquidationAsset(e.pool, e.lp, e.collateral)
    assert book.getDeleverageTraversalAsset(e.bob, e.pool, 1, True) == (e.lp.address, 100 * 10**18)
    # Explicitly supplied bindings are not silently replaced by the adapter.
    with pytest.raises(ValueError, match="UNEXPECTED_HISTORICAL_VAULTBOOK_CONSTRUCTOR"):
        adapter.deploy("VaultBook", e.hq.address, e.gov.address, 21_600, 100_000,
                       e.pool.address, label=key + SUFFIX)


@pytest.fixture
def legacy_compat_staging(legacy_env, switchboard, monkeypatch):
    """Exercise the production migration on real contracts, with local HQ/pool pins."""
    import importlib.util
    from types import SimpleNamespace
    e = legacy_env
    path = ROOT / "migrations/base-mainnet/2026091900_StageLegacyVaultCompatibility.py"
    spec = importlib.util.spec_from_file_location("legacy_compat_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "EXPECTED_HQ", str(e.hq.address).lower())
    monkeypatch.setattr(module, "EXPECTED_POOL", str(e.pool.address).lower())
    # The shared composition fixture has four rows. Add retained vault 5 and
    # use the production timelock floor before invoking the migration.
    fifth = boa.load("contracts/vaults/SimpleErc20.vy", e.hq)
    retained = [e.book.getAddr(i) for i in range(1, 5)] + [fifth.address]
    old_book = boa.load("contracts/registries/VaultBook.vy", e.hq, ZERO, 21_600, 302_400, e.pool)
    for reg_id, vault in enumerate(retained, 1):
        old_book.startAddNewAddressToRegistry(vault, f"Retained local vault {reg_id}", sender=e.gov.address)
        assert old_book.confirmNewAddressToRegistry(vault, sender=e.gov.address) == reg_id
    old_book.setRegistryTimeLockAfterSetup(sender=e.gov.address)
    e.hq.startAddressUpdateToRegistry(8, old_book, sender=e.gov.address)
    boa.env.time_travel(blocks=e.hq.registryChangeTimeLock())
    assert e.hq.confirmAddressUpdateToRegistry(8, sender=e.gov.address)
    e.book = old_book
    e.deposit(e.bob, 100 * 10**18)

    class LocalMigration:
        def __init__(self):
            self.deployed = {}
            self.calls = []
        def chain(self):
            return "base-mainnet"
        def account(self):
            return e.bob
        def blueprint(self):
            return SimpleNamespace(PARAMS=PARAMS["base"])
        def get_contract(self, name, address=None):
            return {"RipeHq": e.hq, "VaultBook": e.book, "StabilityPool": e.pool,
                    "Deleverage" + module.PREVIOUS_SUFFIX: e.dl,
                    "SwitchboardPopulated" + module.PREVIOUS_SUFFIX: switchboard}[name]
        def deploy(self, name, *args, label):
            directory = "registries" if name in ("VaultBook", "Switchboard") else "config" if name.startswith("Switchboard") else "core"
            contract = boa.load(f"contracts/{directory}/{name}.vy", *args)
            self.deployed[name] = contract
            assert label == name + module.SUFFIX
            return contract
        def execute(self, function, *args):
            self.calls.append((function.contract.address, function.fn_ast.name, args))
            return function(*args, sender=e.bob)
    return module, LocalMigration(), e


def test_legacy_compat_staging_executes_retained_only_without_activating(legacy_compat_staging):
    module, migration, e = legacy_compat_staging
    active = tuple(e.hq.getAddr(i) for i in range(1, e.hq.numAddrs()))
    pending = tuple(e.hq.pendingAddrUpdate(8))
    before = (e.lp.balanceOf(e.pool), e.pool.userBalances(e.bob, e.lp))
    module.migrate(migration)
    assert set(migration.deployed) == {"VaultBook", "AuctionHouse", "Deleverage", "SwitchboardAlpha", "SwitchboardCharlie", "SwitchboardGolf", "Switchboard"}
    candidate = migration.deployed["VaultBook"]
    assert candidate.numAddrs() == 6 and candidate.LEGACY_POOL() == e.pool.address
    assert candidate.getDeleverageTraversalAsset(e.bob, e.pool, 1, True) == (e.lp.address, 100 * 10**18)
    assert tuple(e.hq.getAddr(i) for i in range(1, e.hq.numAddrs())) == active
    assert tuple(e.hq.pendingAddrUpdate(8)) == pending
    assert (e.lp.balanceOf(e.pool), e.pool.userBalances(e.bob, e.lp)) == before
    assert {call[0] for call in migration.calls} == {candidate.address, migration.deployed["Switchboard"].address}
    assert all(call[1] in {"startAddNewAddressToRegistry", "confirmNewAddressToRegistry", "setRegistryTimeLockAfterSetup", "relinquishGov"} for call in migration.calls)
    assert len(migration.calls) == 28


@pytest.mark.parametrize("fault", ["profile", "hq", "pool", "future_row", "invalid_row"])
def test_legacy_compat_staging_rejects_drift_before_deployments(legacy_compat_staging, monkeypatch, fault):
    from conf_legacy_pool import storage_write
    module, migration, e = legacy_compat_staging
    if fault == "profile":
        monkeypatch.setattr(migration, "chain", lambda: "robinhood-mainnet")
        reason = "WRONG_PROFILE"
    elif fault == "hq":
        monkeypatch.setattr(module, "EXPECTED_HQ", str(e.bob).lower())
        reason = "WRONG_HQ"
    elif fault == "pool":
        monkeypatch.setattr(module, "EXPECTED_POOL", str(e.bob).lower())
        reason = "WRONG_POOL"
    elif fault == "future_row":
        storage_write(e.book, "registry", "numAddrs", [], 7)
        reason = "ACTIVE_TOPOLOGY_DRIFT"
    else:
        storage_write(e.book, "registry", "addrToRegId", [e.pool], 0)
        reason = "ACTIVE_IDENTITY:1"
    with pytest.raises(RuntimeError, match="BASE_LEGACY_COMPAT_" + reason):
        module.migrate(migration)
    assert not migration.deployed and not migration.calls


def test_legacy_compat_migration_is_the_next_recorded_base_step():
    from types import SimpleNamespace
    from scripts.utils.migration_runner import MigrationRunner
    runner = MigrationRunner(ROOT / "migrations/base-mainnet", ROOT / "migration_history/base-mainnet/v1", {})
    # Honor the normal runner guard; the fresh step must not skip an unfinished
    # historical migration or require force-replaying a frozen constructor.
    runner._require_start_point(SimpleNamespace(), "2026091900")
