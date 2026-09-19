"""Offline current-ABI staging checks; no RPC, manifest, or history writes."""
import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import boa
import pytest

from config.BluePrint import PARAMS
from scripts.base_full_update_fork import (
    CURRENT_ORACLE_SUFFIX, DeploymentAdapter, STAGING_MIGRATIONS, candidate_key,
)

ROOT = Path(__file__).resolve().parents[1]
ZERO = "0x" + "00" * 20
ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
BTC = "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"
ORACLES = "2026091900_StageBaseOraclesPsmReserves.py"
BRIDGE = "2026091901_StageBasePriceDeskGasBridge.py"
NAMES = (
    "ChainlinkPrices", "CurvePrices", "BlueChipYieldPrices", "PythPrices",
    "StorkPrices", "AeroRipePrices", "wsuperOETHbPrices", "UndyVaultPrices", "RedStone",
)


def load_migration(filename):
    spec = importlib.util.spec_from_file_location(filename[:-3], ROOT / "migrations/base-mainnet" / filename)
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
        return SimpleNamespace(PARAMS=PARAMS["base"], ADDYS={
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
    assert STAGING_MIGRATIONS[-1] == ORACLES
    assert "2026091402_StageBaseOraclesPsmReserves.py" not in STAGING_MIGRATIONS
    contract = object()
    adapter = DeploymentAdapter(SimpleNamespace(new={"PriceDesk": contract}), None)
    label = "PriceDesk" + CURRENT_ORACLE_SUFFIX
    assert candidate_key(label) == "PriceDesk"
    assert adapter.get_contract(label) is contract


@pytest.mark.parametrize("filename", (ORACLES, BRIDGE, "../../scripts/diagnose_base_snapshot_refresh.py"))
def test_current_price_desk_call_sites_compile_the_full_constructor(ripe_hq, deploy3r, filename):
    path = (ROOT / "migrations/base-mainnet" / filename).resolve()
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
