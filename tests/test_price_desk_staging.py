"""Offline current-ABI staging checks; no RPC, manifest, or history writes."""
import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import boa
import pytest

from config.BluePrint import PARAMS, PRICE_DESK_SOURCE_GAS_OVERRIDES
from scripts.base_full_update_fork import (
    CANDIDATE_DIR, CURRENT_ORACLE_SUFFIX, DeploymentAdapter, STAGING_SCRIPTS, candidate_key,
    department_confirmation_order, staging_source_hashes,
)

ROOT = Path(__file__).resolve().parents[1]
ZERO = "0x" + "00" * 20
ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
BTC = "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"
ORACLES = CANDIDATE_DIR / "oracles_psm_reserves.py"
BRIDGE = CANDIDATE_DIR / "price_desk_gas_bridge.py"
NAMES = (
    "ChainlinkPrices", "CurvePrices", "BlueChipYieldPrices", "PythPrices",
    "StorkPrices", "AeroRipePrices", "wsuperOETHbPrices", "UndyVaultPrices", "RedStone",
)


def load_migration(filename):
    spec = importlib.util.spec_from_file_location(filename.stem, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StagingFixture:
    """Real PriceDesk/Teller; legacy dependency reads and journaling are local doubles."""
    def __init__(self, module, hq, deployer, token):
        self.deployer = deployer
        self.deployed = {}
        self.executed = []
        self.completed = set()
        self.cursor = 0
        self.labels = {}
        self.sources = {}
        addresses = getattr(load_migration(ORACLES), "REVIEWED_SOURCE_SLOTS")
        self.slots = dict(addresses)
        self.blue = "0x90c70acff302c8a7f00574ec3547b0221f39cd28"
        # These synthetic legacy contracts are used only for address/code checks.
        # Their getters below are explicit doubles, never asserted as fork evidence.
        for slot, name in enumerate(NAMES, 1):
            address = self.blue if slot == 3 else self.slots[slot]
            boa.env.set_code(address, b"\x00")
            self.sources[name] = SimpleNamespace(
                address=address, ETH=lambda: ETH, BTC=lambda: BTC,
                WETH=lambda: token.address,
                feedConfig=lambda asset: (token.address, 0, False, False, 86_400),
                minActionTimeLock=lambda slot=slot: 14_400 if slot == 2 else 21_600,
                FLUID_ADDR=lambda: token.address, COMPOUND_V3_ADDR=lambda: token.address,
                MOONWELL_ADDR=lambda: token.address, AAVE_V3_ADDR=lambda: token.address,
                PYTH=lambda: token.address, STORK=lambda: token.address,
                MCBETH=lambda: token.address, SUPER_OETH=lambda: token.address,
                WRAPPED_SUPER_OETH=lambda: token.address, VVV=lambda: token.address,
                getPricedAssets=lambda: [token.address, ETH, BTC],
            )
        old_desk = SimpleNamespace(
            address=boa.env.generate_address(), ETH=lambda: ETH,
            numAddrs=lambda: 10, getAddr=lambda slot: self.slots[slot],
        )
        psm = SimpleNamespace(
            address=boa.env.generate_address(), USDC=lambda: load_migration(ORACLES).USDC,
            usdcYieldPosition=lambda: (1, token.address), numBlocksPerInterval=lambda: 100,
            mintFee=lambda: 0, maxIntervalMint=lambda: 0, redeemFee=lambda: 0,
            maxIntervalRedeem=lambda: 0,
        )
        self.hq_slots = {i: hq.getAddr(i) for i in (1, 2, 3, 5, 17)}
        self.hq_slots.update({7: old_desk.address, 22: psm.address})
        self.hq = SimpleNamespace(address=hq.address, getAddr=lambda slot: self.hq_slots[slot])
        self.contracts = {
            "RipeHq": self.hq, "PriceDesk": old_desk, "EndaomentPSM": psm,
            "MissionControl": SimpleNamespace(numAssets=lambda: 2, assets=lambda i: token.address,
                                               assetConfig=lambda asset: (False,)),
            **self.sources,
        }

    def chain(self):
        return "base-mainnet"

    def account(self):
        return self.deployer

    def blueprint(self):
        return SimpleNamespace(PARAMS=PARAMS["base"],
                               PRICE_DESK_SOURCE_GAS_OVERRIDES=PRICE_DESK_SOURCE_GAS_OVERRIDES["base"], ADDYS={
            "CURVE_ADDRESS_PROVIDER": self.sources["CurvePrices"].address,
            "RIPE_WETH_POOL": self.sources["CurvePrices"].address,
        })

    def get_contract(self, name, address=None):
        if address is not None:
            for contract in self.contracts.values():
                if hasattr(contract, "address") and str(contract.address).lower() == str(address).lower():
                    return contract
        return self.contracts[name]

    def deploy(self, name, *args, label):
        if label in self.labels:
            return self.labels[label]
        if name in ("PriceDesk", "Teller"):
            directory = "registries" if name == "PriceDesk" else "core"
            contract = boa.load(str(ROOT / "contracts" / directory / (name + ".vy")), *args)
        else:
            code = boa.loads("# @version 0.4.3\n@external\ndef ping():\n    pass\n")
            contract = SimpleNamespace(
                address=code.address,
                minActionTimeLock=lambda: 14_400 if name == "CurvePrices" else 21_600,
                isMonitoringOnly=lambda: True, canMint=lambda: False, canRedeem=lambda: False,
                isPaused=lambda: True, isRunning=lambda: False, canAcquireRipe=lambda: False,
            )
        self.deployed[name] = contract
        self.labels[label] = contract
        return contract

    def execute(self, fn, *args):
        self.cursor += 1
        if self.cursor in self.completed:
            return None
        result = fn(*args, sender=self.deployer)
        self.completed.add(self.cursor)
        self.executed.append((fn, args))
        return result


@pytest.mark.parametrize("filename", (ORACLES, BRIDGE))
def test_current_staging_uses_real_abi_and_resumes_without_hq_changes(
    ripe_hq, deploy3r, alpha_token, monkeypatch, filename,
):
    module = load_migration(filename)
    if filename == ORACLES:
        arrays = SimpleNamespace(MORPHO_ADDRS=lambda i: alpha_token.address,
                                 EULER_ADDRS=lambda i: alpha_token.address)
        monkeypatch.setattr(module, "ABIContractFactory", lambda *args: SimpleNamespace(at=lambda address: arrays))
    migration = StagingFixture(module, ripe_hq, deploy3r, alpha_token)
    before = migration.hq_slots.copy()
    module.migrate(migration)
    desk = migration.deployed["PriceDesk"]
    assert (desk.PRICE_SOURCE_PRICE_GAS(), desk.PRICE_SOURCE_SNAPSHOT_GAS(),
            desk.PRICE_SOURCE_HAS_FEED_GAS(), desk.MAX_SOURCE_GAS()) == tuple(
        PARAMS["base"][key] for key in ("PRICE_DESK_PRICE_SOURCE_GAS", "PRICE_DESK_SNAPSHOT_SOURCE_GAS",
                                       "PRICE_DESK_HAS_FEED_SOURCE_GAS", "PRICE_DESK_MAX_SOURCE_GAS"))
    assert desk.numAddrs() == 10 and desk.getAddr(3) == ZERO
    assert desk.getAddr(6).lower() == migration.slots[6].lower()
    assert desk.governance() == ZERO
    for name, slot in (("CurvePrices", 2), ("UndyVaultPrices", 8)):
        floors = (desk.PRICE_SOURCE_PRICE_GAS(), desk.PRICE_SOURCE_SNAPSHOT_GAS(), desk.PRICE_SOURCE_HAS_FEED_GAS())
        expected = tuple(value or floor for value, floor in zip(PRICE_DESK_SOURCE_GAS_OVERRIDES["base"][name], floors))
        assert tuple(desk.getSourceGasBudgets(desk.getAddr(slot))) == expected
    names = [fn.fn_ast.name for fn, _ in migration.executed]
    assert max(i for i, name in enumerate(names) if name == "setSourceGasBudgets") < names.index("relinquishGov")
    assert migration.hq_slots == before
    if filename == BRIDGE:
        assert desk.tokenScale(alpha_token) == 10 ** alpha_token.decimals()
        assert migration.deployed["Teller"].isPaused()
        assert migration.deployed["Teller"].eval("CURVE_PRICES_ID") == 2
    count, labels = len(migration.executed), migration.labels.copy()
    migration.cursor = 0
    module.migrate(migration)
    assert len(migration.executed) == count and migration.labels == labels
    assert migration.hq_slots == before


def test_full_update_selects_current_migration_and_resolves_fresh_labels():
    assert STAGING_SCRIPTS[-1] == ORACLES
    assert Path("migrations/base-mainnet/2026091402_StageBaseOraclesPsmReserves.py") not in STAGING_SCRIPTS
    contract = object()
    adapter = DeploymentAdapter(SimpleNamespace(new={"PriceDesk": contract}), None)
    label = "PriceDesk" + CURRENT_ORACLE_SUFFIX
    assert candidate_key(label) == "PriceDesk"
    assert adapter.get_contract(label) is contract


@pytest.mark.parametrize("filename", (ORACLES, BRIDGE, Path("scripts/diagnose_base_snapshot_refresh.py")))
def test_current_price_desk_call_sites_compile_the_full_constructor(ripe_hq, deploy3r, filename):
    path = (ROOT / filename).resolve()
    calls = [node for node in ast.walk(ast.parse(path.read_text()))
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
             and node.func.attr == "deploy" and (
                 (node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == "PriceDesk")
                 or any(kw.arg == "path" and "PriceDesk.vy" in ast.unparse(kw.value) for kw in node.keywords))]
    assert len(calls) == (2 if path.name == "diagnose_base_snapshot_refresh.py" else 1)
    env = {"hq": SimpleNamespace(address=ripe_hq.address), "run": SimpleNamespace(hq=ripe_hq),
           "migration": SimpleNamespace(account=lambda: deploy3r), "ZERO": ZERO,
           "eth": ETH, "old": SimpleNamespace(ETH=lambda: ETH), "old_desk": SimpleNamespace(ETH=lambda: ETH),
           "params": PARAMS["base"], "budget": 150_000}
    for call in calls:
        args = [eval(compile(ast.Expression(arg), str(path), "eval"), {"__builtins__": {}}, env) for arg in call.args[1:]]
        assert len(args) == 9
        desk = boa.load("contracts/registries/PriceDesk.vy", *args)
        assert desk.PRICE_SOURCE_HAS_FEED_GAS() == 75_000 and desk.MAX_SOURCE_GAS() == 6_000_000


def test_drafts_do_not_enter_live_base_migration_queue(tmp_path):
    from scripts.utils.migration_runner import MigrationRunner

    def assert_no_drafts(runner):
        candidates = tuple((ROOT / CANDIDATE_DIR).glob("*.py"))
        drafts = {path.read_bytes() for path in candidates}
        prohibited_names = {path.stem for path in candidates}
        # Deployment identities survive renamed files and comment/format edits.
        # Fresh production labels remain eligible for a separately authorized migration.
        identifiers = {
            node.value.value
            for path in (ROOT / ORACLES, ROOT / BRIDGE)
            for node in ast.walk(ast.parse(path.read_text()))
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and any(isinstance(target, ast.Name) and target.id in ("LABEL", "TELLER_LABEL", "SUFFIX")
                    for target in node.targets)
        }
        assert len(identifiers) == 3
        for filename, _, _ in runner._filtered_migration_filenames(None, None):
            path = Path(filename)
            diagnostic = f"Rehearsal draft in live queue: {path.name}"
            assert path.read_bytes() not in drafts, diagnostic
            assert not any(name in path.stem for name in prohibited_names), diagnostic
            strings = [node.value for node in ast.walk(ast.parse(path.read_text()))
                       if isinstance(node, ast.Constant) and isinstance(node.value, str)]
            assert not any(identifier in value for identifier in identifiers for value in strings), diagnostic

    runner = MigrationRunner(str(ROOT / "migrations/base-mainnet"),
                             str(ROOT / "migration_history/base-mainnet/v1"), {})
    assert_no_drafts(runner)
    assert ORACLES.is_relative_to(CANDIDATE_DIR)
    assert BRIDGE.is_relative_to(CANDIDATE_DIR)

    # Completion/frontier behavior belongs to synthetic history, so valid new
    # production migrations can advance independently of this draft-exclusion test.
    queue, history = tmp_path / "migrations", tmp_path / "history"
    queue.mkdir()
    history.mkdir()
    for name in ("1000-manifest.json", "current-manifest.json"):
        (history / name).write_text("{}")
    (queue / "1000_Completed.py").write_text("# completed fixture migration")
    (queue / "1001_AuthorizedFutureStage.py").write_text("# ordinary future migration")
    future = MigrationRunner(str(queue), str(history), {})
    assert future._recorded_frontier() == "1000"
    future._require_start_point(None, "1001")
    assert [timestamp for _, timestamp, _ in
            future._filtered_migration_filenames("1000", None, inclusive=False)] == ["1001"]
    assert_no_drafts(future)
    fresh = queue / "1002_AuthorizedFreshLabels.py"
    fresh.write_text('LABEL = "PriceDeskAuthorizedProductionCandidate"\n'
                     'TELLER_LABEL = "TellerAuthorizedProductionCandidate"\n')
    assert_no_drafts(future)
    # Ordinary future migrations can also advance the synthetic recorded frontier.
    (history / "1001-manifest.json").write_text("{}")
    advanced = MigrationRunner(str(queue), str(history), {})
    assert advanced._recorded_frontier() == "1001"
    advanced._require_start_point(None, "1002")
    assert_no_drafts(advanced)
    for draft in (ORACLES, BRIDGE):
        copied = queue / "1003_AccidentalCamelStyleCopy.py"
        copied.write_bytes((ROOT / draft).read_bytes())
        with pytest.raises(AssertionError, match="Rehearsal draft in live queue"):
            assert_no_drafts(advanced)
        copied.write_text("# Irrelevant comment-only edit to a renamed draft.\n" + copied.read_text())
        with pytest.raises(AssertionError, match="Rehearsal draft in live queue"):
            assert_no_drafts(advanced)
        copied.unlink()


@pytest.mark.parametrize("missing", (6, 8, 5, 7, 17))
def test_department_activation_rejects_missing_dependency_before_any_calls(monkeypatch, missing):
    import scripts.base_full_update_fork as full_update

    slots = {slot: str(slot) for slot in (5, 6, 7, 8, 17) if slot != missing}
    monkeypatch.setattr(full_update, "HQ_IDS", slots)
    run = object.__new__(full_update.FullUpdate)
    # No RPC/HQ fields exist: dependency validation must precede any access.
    with pytest.raises(RuntimeError, match=f"BASE_ACTIVATION_REQUIRED_SLOT_MISSING:{missing}"):
        run.activate_departments()


def test_department_confirmation_order_is_complete_and_dependency_ordered():
    slots = [17, 27, 7, 5, 8, 6, 26]
    order = department_confirmation_order(slots)
    assert sorted(order) == sorted(slots)
    assert order.index(7) < order.index(17)
    assert order[:4] == [6, 8, 5, 7]
    with pytest.raises(RuntimeError, match="BASE_ACTIVATION_DUPLICATE_SLOT"):
        department_confirmation_order(slots + [17])


def test_staging_fingerprints_bind_historical_and_current_bridge(tmp_path):
    original = staging_source_hashes()
    for path in (ROOT / "migrations/base-mainnet").glob("20260914*.py"):
        assert path.relative_to(ROOT).as_posix() in original
    for path in (ORACLES, BRIDGE, CANDIDATE_DIR / "price_desk_budgets.py"):
        assert path.as_posix() in original
    for relative in original:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    (tmp_path / BRIDGE).write_text((tmp_path / BRIDGE).read_text() + "\n# changed bridge\n")
    changed = staging_source_hashes(tmp_path)
    assert original.keys() == changed.keys()
    assert [name for name in original if original[name] != changed[name]] == [BRIDGE.as_posix()]


@pytest.mark.parametrize("profile", ("base", "local", "robinhood"))
def test_profile_override_table_applies_to_real_desk(profile, ripe_hq, deploy3r):
    from scripts.rehearsal.base_candidates.price_desk_budgets import (
        BUDGET_KEYS, apply_source_gas_budgets,
    )
    from scripts.utils.deploy_args import BluePrint

    # Local tests use the lightweight dictionaries; DeployArgs.BluePrint also
    # requires deployment-only token/Curve dictionaries absent for local.
    blueprint = (BluePrint(profile) if profile != "local" else SimpleNamespace(
        PARAMS=PARAMS[profile], PRICE_DESK_SOURCE_GAS_OVERRIDES=PRICE_DESK_SOURCE_GAS_OVERRIDES[profile]))
    defaults = tuple(blueprint.PARAMS[key] for key in BUDGET_KEYS)
    desk = boa.load("contracts/registries/PriceDesk.vy", ripe_hq, deploy3r, ETH, 1, 2, *defaults)
    sources = {}
    for slot, name in enumerate(blueprint.PRICE_DESK_SOURCE_GAS_OVERRIDES, 1):
        source = boa.loads("# @version 0.4.3\n@external\ndef ping():\n    pass\n")
        desk.startAddNewAddressToRegistry(source, name, sender=deploy3r)
        assert desk.confirmNewAddressToRegistry(source, sender=deploy3r) == slot
        sources[name] = (slot, source.address)
    migration = SimpleNamespace(blueprint=lambda: blueprint,
                                execute=lambda fn, *args: fn(*args, sender=deploy3r))
    bad_binding = dict(sources)
    slot, address = bad_binding["CurvePrices"]
    bad_binding["CurvePrices"] = (slot + 99, address)
    with pytest.raises(RuntimeError, match="PRICEDESK_OVERRIDE_SOURCE_MISMATCH:CurvePrices"):
        apply_source_gas_budgets(migration, desk, bad_binding)
    apply_source_gas_budgets(migration, desk, sources)
    for name, (_, address) in sources.items():
        expected = tuple(value or floor for value, floor in zip(
            blueprint.PRICE_DESK_SOURCE_GAS_OVERRIDES[name], defaults[:3]))
        assert tuple(desk.getSourceGasBudgets(address)) == expected


@pytest.mark.parametrize("fault", ("missing_undy", "under_floor", "over_max", "dropped_write", "constructor_drift"))
def test_bridge_does_not_relinquish_governance_on_budget_failure(
    ripe_hq, deploy3r, alpha_token, fault,
):
    from copy import deepcopy

    module = load_migration(BRIDGE)
    migration = StagingFixture(module, ripe_hq, deploy3r, alpha_token)
    blueprint = deepcopy(migration.blueprint())
    migration.blueprint = lambda: blueprint
    if fault == "missing_undy":
        blueprint.PRICE_DESK_SOURCE_GAS_OVERRIDES.pop("UndyVaultPrices")
        expected = "PRICEDESK_OVERRIDE_SOURCE_SET_MISMATCH"
    elif fault in ("under_floor", "over_max"):
        blueprint.PRICE_DESK_SOURCE_GAS_OVERRIDES["CurvePrices"] = (0, 1 if fault == "under_floor" else 6_000_001, 0)
        expected = "PRICEDESK_OVERRIDE_BOUNDS:CurvePrices"
    elif fault == "dropped_write":
        execute = migration.execute
        migration.execute = lambda fn, *args: None if fn.fn_ast.name == "setSourceGasBudgets" else execute(fn, *args)
        expected = "PRICEDESK_OVERRIDE_READBACK_MISMATCH:UndyVaultPrices"
    else:
        deploy = migration.deploy
        def changed_constructor(name, *args, label):
            if name == "PriceDesk":
                args = (*args[:-1], args[-1] + 1)
            return deploy(name, *args, label=label)
        migration.deploy = changed_constructor
        expected = "PRICEDESK_CONSTRUCTOR_BUDGET_MISMATCH"
    with pytest.raises(RuntimeError, match=expected):
        module.migrate(migration)
    desk = migration.deployed["PriceDesk"]
    assert desk.governance() == deploy3r
    assert all(fn.fn_ast.name != "relinquishGov" for fn, _ in migration.executed)


def test_provisional_profile_overrides_have_independent_review_pins():
    assert PRICE_DESK_SOURCE_GAS_OVERRIDES == {
        "base": {"CurvePrices": (0, 1_500_000, 0), "UndyVaultPrices": (3_500_000, 1_500_000, 0)},
        "local": {"CurvePrices": (0, 500_000, 0)},
        "robinhood": {"CurvePrices": (0, 500_000, 0)},
    }


def test_oracle_draft_preserves_frozen_nonbudget_behavior():
    """Keep the historical body immutable while making copy drift reviewable."""
    historical = ast.parse((ROOT / "migrations/base-mainnet/2026091402_StageBaseOraclesPsmReserves.py").read_text())
    current = ast.parse((ROOT / ORACLES).read_text())

    class BudgetDelta(ast.NodeTransformer):
        def __init__(self, is_current):
            self.is_current = is_current
            self.calls = 0
            self.readbacks = 0
            self.overrides = 0

        def visit_ImportFrom(self, node):
            return None if node.module == "scripts.rehearsal.base_candidates.price_desk_budgets" else node

        def visit_Expr(self, node):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                return None  # module docstring
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                if node.value.func.id == "verify_price_desk_defaults":
                    self.readbacks += 1
                    return None
                if node.value.func.id == "apply_source_gas_budgets":
                    self.overrides += 1
                    return None
            return self.generic_visit(node)

        def visit_Assign(self, node):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "SUFFIX":
                return None
            return self.generic_visit(node)

        def visit_Assert(self, node):
            if (isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.Call)
                    and isinstance(node.test.left.func, ast.Attribute)
                    and node.test.left.func.attr in ("PRICE_SOURCE_PRICE_GAS", "PRICE_SOURCE_SNAPSHOT_GAS")):
                self.readbacks += 1
                return None
            return self.generic_visit(node)

        def visit_Call(self, node):
            if (isinstance(node.func, ast.Attribute) and node.func.attr == "deploy"
                    and node.args and isinstance(node.args[0], ast.Constant)
                    and node.args[0].value == "PriceDesk"):
                self.calls += 1
                assert len(node.args) == (10 if self.is_current else 8)
                if self.is_current:
                    node.args = node.args[:-2]
            return self.generic_visit(node)

    before, after = BudgetDelta(False), BudgetDelta(True)
    old_tree, new_tree = before.visit(historical), after.visit(current)
    assert (before.calls, before.readbacks, before.overrides) == (1, 2, 0)
    assert (after.calls, after.readbacks, after.overrides) == (1, 1, 1)
    assert ast.dump(old_tree) == ast.dump(new_tree)
