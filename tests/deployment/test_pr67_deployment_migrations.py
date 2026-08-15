from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

import pytest
from web3 import Web3 as RealWeb3

from scripts.utils import ledger_deployment
from scripts.utils.migration import PromotionSpec


ROOT = Path(__file__).resolve().parents[2]
ZERO_ADDRESS = "0x" + "0" * 40


def _addr(index: int) -> str:
    return f"0x{index:040x}"


def _load(relative_path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


UNISWAP = _load(
    "migrations/robinhood-mainnet/0008_UniswapV2Prices.py",
    "pr67_uniswap_deployment",
)
REDEPLOY = _load(
    "migrations/robinhood-mainnet/0009_RedeployStaleContracts.py",
    "pr67_redeploy_candidates",
)
LEDGER = _load(
    "migrations/robinhood-mainnet/0010_RedeployLedger.py",
    "pr67_ledger_candidates",
)
BLUECHIP = _load(
    "migrations/robinhood-mainnet/0011_BlueChipYieldPricesCandidate.py",
    "pr67_bluechip_candidate",
)
PROMOTE_BLUECHIP = _load(
    "migrations/robinhood-mainnet/0012_PromoteBlueChipYieldPrices.py",
    "pr67_bluechip_promotion",
)
VAULT_MIGRATOR = _load(
    "migrations/robinhood-mainnet/0013_VaultMigratorCandidate.py",
    "pr67_vault_migrator_candidate",
)
PROMOTE_VAULT_MIGRATOR = _load(
    "migrations/robinhood-mainnet/0014_PromoteVaultMigrator.py",
    "pr67_vault_migrator_promotion",
)


class _Contract:
    def __init__(self, address):
        self.address = address


class _Registry(_Contract):
    def __init__(self, address, slots=None, count=0):
        super().__init__(address)
        self.slots = dict(slots or {})
        self.count = count

    def getAddr(self, reg_id):
        return self.slots.get(reg_id, ZERO_ADDRESS)

    def numAddrs(self):
        return self.count


class _GovernedCandidate(_Contract):
    def __init__(self, address, account, minimum):
        super().__init__(address)
        self._account = account
        self._minimum = minimum
        self._timelock = 0
        self._governance = account

    def actionTimeLock(self):
        return self._timelock

    def minActionTimeLock(self):
        return self._minimum

    def setActionTimeLockAfterSetup(self, selected):
        assert self._governance == self._account
        assert self._timelock == 0
        self._timelock = selected
        return True

    def relinquishGov(self):
        assert self._governance == self._account
        self._governance = ZERO_ADDRESS

    def governance(self):
        return self._governance


class _VaultMigratorCandidate(_Contract):
    def __init__(self, address, should_pause):
        super().__init__(address)
        self._should_pause = should_pause

    def isPaused(self):
        return self._should_pause


class _UniswapMonitorCandidate(_Contract):
    def __init__(self, address, ripe_hq, pool, ripe, weth):
        super().__init__(address)
        self._ripe_hq = ripe_hq.address
        self._pool = pool
        self._ripe = ripe.address
        self._weth = weth

    def isMonitoringOnly(self):
        return True

    def RIPE_HQ(self):
        return self._ripe_hq

    def RIPE_WETH_POOL(self):
        return self._pool

    def RIPE_TOKEN(self):
        return self._ripe

    def WETH_TOKEN(self):
        return self._weth

    def getPriceAndHasFeed(self, _asset):
        return 0, False


class _MissionControlCandidate(_Contract):
    def __init__(self, address, ripe_hq):
        super().__init__(address)
        self._ripe_hq = ripe_hq

    def getRipeHq(self):
        return self._ripe_hq


class _FakeMigration:
    def __init__(
        self,
        contracts=None,
        addresses=None,
        account=None,
        manifest_contracts=None,
        rpc="boa",
    ):
        self.contracts = dict(contracts or {})
        self.addresses = dict(addresses or {})
        self._previous_manifest = {"contracts": dict(manifest_contracts or {})}
        self._account = account or _addr(900)
        self._rpc = rpc
        self.deployments = []
        self.executions = []
        self.promotions = []
        self.promotion_specs = []
        self.promotion_batch_sizes = []
        self._next_address = 1_000

    def get_contract(self, name):
        return self.contracts[name]

    def get_address(self, name):
        if name in self.addresses:
            return self.addresses[name]
        return self._previous_manifest["contracts"][name]["address"]

    def account(self):
        return self._account

    def rpc(self):
        return self._rpc

    def deploy(self, name, *args, **kwargs):
        label = kwargs.get("label", name)
        address = _addr(self._next_address)
        self._next_address += 1
        if name == "VaultMigrator":
            contract = _VaultMigratorCandidate(address, args[1])
        elif name == "UniswapV2Prices":
            contract = _UniswapMonitorCandidate(address, *args)
        elif name in {
            "BlueChipYieldPrices",
            "HumanResources",
            "SwitchboardAlpha",
            "SwitchboardBravo",
            "SwitchboardCharlie",
            "SwitchboardEcho",
        }:
            minimum = (
                REDEPLOY.HR_MIN_TIMELOCK
                if name == "HumanResources"
                else BLUECHIP.PRICE_CHANGE_MIN_TIMELOCK
            )
            contract = _GovernedCandidate(
                address,
                self._account,
                minimum,
            )
        else:
            contract = _Contract(address)
        self.deployments.append((name, label, args, contract))
        return contract

    def execute(self, transaction, *args):
        self.executions.append((transaction.__name__, args))
        return transaction(*args)

    def promote_candidate(
        self,
        canonical_name,
        candidate_label,
        registry,
        registry_id,
        *,
        expected_source_path,
        registry_name,
        expected_constructor_args,
        activation_candidate_label=None,
        activation_dependency_arg_index=None,
        activation_expected_constructor_args=None,
    ):
        return self.promote_candidates(
            [
                PromotionSpec(
                    canonical_name=canonical_name,
                    expected_source_path=expected_source_path,
                    candidate_label=candidate_label,
                    registry_name=registry_name,
                    registry=registry,
                    registry_id=registry_id,
                    expected_constructor_args=expected_constructor_args,
                    activation_candidate_label=activation_candidate_label,
                    activation_dependency_arg_index=(activation_dependency_arg_index),
                    activation_expected_constructor_args=(
                        activation_expected_constructor_args
                    ),
                )
            ]
        )[0]

    def promote_candidates(self, promotions):
        self.promotion_batch_sizes.append(len(promotions))
        addresses = []
        for spec in promotions:
            assert isinstance(spec, PromotionSpec)
            self.promotion_specs.append(spec)
            self.promotions.append(
                (
                    spec.canonical_name,
                    spec.candidate_label,
                    spec.registry.address,
                    spec.registry_id,
                    spec.activation_candidate_label,
                    spec.activation_dependency_arg_index,
                )
            )
            record = self._previous_manifest["contracts"].get(
                spec.candidate_label,
                {},
            )
            addresses.append(record.get("address"))
        return tuple(addresses)


def _bluechip_deploy_call(path: Path) -> ast.Call:
    tree = ast.parse(path.read_text(), filename=str(path))
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "deploy"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "BlueChipYieldPrices"
    ]
    assert len(matches) == 1
    return matches[0]


def test_base_bluechip_replay_calls_match_final_constructor_shape():
    for relative in (
        "migrations/base-mainnet/1007_PriceDesk.py",
        "migrations/base-mainnet/2025071503_PriceDesk.py",
    ):
        call = _bluechip_deploy_call(ROOT / relative)
        # Contract name plus the final 11 constructor arguments.
        assert len(call.args) == 12
        assert isinstance(call.args[-1], ast.Name)
        assert call.args[-1].id == "ZERO_ADDRESS"

    old_call = _bluechip_deploy_call(ROOT / "migrations/base-mainnet/1007_PriceDesk.py")
    assert isinstance(old_call.args[2], ast.Name)
    assert old_call.args[2].id == "ZERO_ADDRESS"


def test_safe_calldata_helpers_bind_the_expected_registry_calls():
    from eth_abi.abi import decode
    from web3 import Web3

    candidate = _addr(777)
    for module in (REDEPLOY, LEDGER):
        start, confirm = module._update_calldata(25, candidate)
        start_bytes = bytes.fromhex(start)
        confirm_bytes = bytes.fromhex(confirm)
        assert (
            start_bytes[:4]
            == Web3.keccak(text="startAddressUpdateToRegistry(uint256,address)")[:4]
        )
        assert decode(["uint256", "address"], start_bytes[4:]) == (
            25,
            candidate,
        )
        assert (
            confirm_bytes[:4]
            == Web3.keccak(text="confirmAddressUpdateToRegistry(uint256)")[:4]
        )
        assert decode(["uint256"], confirm_bytes[4:]) == (25,)

    setup = bytes.fromhex(
        REDEPLOY._setup_action_timelock_calldata(REDEPLOY.HR_MIN_TIMELOCK)
    )
    assert setup[:4] == Web3.keccak(text="setActionTimeLockAfterSetup(uint256)")[:4]
    assert decode(["uint256"], setup[4:]) == (REDEPLOY.HR_MIN_TIMELOCK,)

    for module in (BLUECHIP, VAULT_MIGRATOR):
        start, confirm = module._add_calldata(candidate, "candidate")
        start_bytes = bytes.fromhex(start)
        confirm_bytes = bytes.fromhex(confirm)
        assert (
            start_bytes[:4]
            == Web3.keccak(text="startAddNewAddressToRegistry(address,string)")[:4]
        )
        assert decode(["address", "string"], start_bytes[4:]) == (
            candidate,
            "candidate",
        )
        assert (
            confirm_bytes[:4]
            == Web3.keccak(text="confirmNewAddressToRegistry(address)")[:4]
        )
        assert decode(["address"], confirm_bytes[4:]) == (candidate,)


def test_accepted_teller_and_stability_pool_abi_removals_are_explicit():
    teller = json.loads((ROOT / "scripts/abis/Teller.json").read_text())
    stability = json.loads((ROOT / "scripts/abis/StabilityPool.json").read_text())

    teller_functions = {
        entry["name"] for entry in teller if entry.get("type") == "function"
    }
    assert {
        "buyFungibleAuction",
        "redeemCollateral",
        "claimFromStabilityPool",
        "redeemFromStabilityPool",
    }.isdisjoint(teller_functions)
    assert {
        "buyManyFungibleAuctions",
        "redeemCollateralFromMany",
        "claimManyFromStabilityPool",
        "redeemManyFromStabilityPool",
    } <= teller_functions

    stability_functions = {
        entry["name"] for entry in stability if entry.get("type") == "function"
    }
    assert {
        "sharesToValue",
        "valueToShares",
        "claimFromStabilityPool",
        "redeemFromStabilityPool",
    }.isdisjoint(stability_functions)
    assert {"getTotalValue", "getTotalUserValue"} <= stability_functions

    stability_events = {
        entry["name"] for entry in stability if entry.get("type") == "event"
    }
    assert "VaultFundsRecovered" not in stability_events
    assert {
        "ClaimAssetActivated",
        "ClaimAssetDeactivated",
        "ClaimAssetLeftDormant",
    } <= stability_events


def test_uniswap_deploys_stateless_monitor_with_inert_price_source_interface(
    monkeypatch,
):
    hq = _Contract(_addr(1))
    ripe = _Contract(_addr(2))
    weth = _addr(3)
    monkeypatch.setattr(UNISWAP, "address", lambda key: weth)
    migration = _FakeMigration(
        contracts={"RipeHq": hq, "RipeToken": ripe}
    )

    UNISWAP.migrate(migration)

    assert [row[0] for row in migration.deployments] == ["UniswapV2Prices"]
    args = migration.deployments[0][2]
    assert args == (hq, UNISWAP.RIPE_WETH_POOL, ripe, weth)
    assert migration.executions == []
    candidate = migration.deployments[0][3]
    assert candidate.isMonitoringOnly()
    assert candidate.getPriceAndHasFeed(ripe.address) == (0, False)
    assert "PriceDesk" not in migration.contracts


def test_0009_uses_candidate_labels_excludes_uniswap_and_emits_safe_calldata(
    monkeypatch,
):
    registries = {
        "RipeHq": _Registry(_addr(10), {i: _addr(100 + i) for i in range(30)}),
        "VaultBook": _Registry(_addr(11), {i: _addr(200 + i) for i in range(10)}),
        "Switchboard": _Registry(_addr(12), {i: _addr(300 + i) for i in range(10)}),
    }
    migration = _FakeMigration(
        contracts={
            **registries,
            "BondBooster": _Contract(_addr(13)),
        }
    )
    messages = []
    monkeypatch.setattr(REDEPLOY.log, "info", messages.append)

    REDEPLOY.migrate(migration)

    names = [row[0] for row in migration.deployments]
    assert "UniswapV2Prices" not in names
    assert names.count("DefaultsRobinhoodLive") == 1
    assert len(names) == 17  # defaults plus 16 registered replacements
    assert all(
        label.endswith("Candidate0009")
        for _name, label, _args, _contract in migration.deployments
    )
    assert sum("[1] 0x" in message for message in messages) == 16
    assert sum("[2] 0x" in message for message in messages) == 16
    assert sum("[setup] 0x" in message for message in messages) == 1
    switchboards = [
        contract
        for name, _label, _args, contract in migration.deployments
        if name.startswith("Switchboard")
    ]
    assert len(switchboards) == 4
    assert all(
        component.actionTimeLock() == REDEPLOY.SWITCHBOARD_MIN_TIMELOCK
        and component.governance() == ZERO_ADDRESS
        for component in switchboards
    )


def _make_0010_migration(*, rpc="boa"):
    from eth_abi.abi import encode

    registries = {
        "RipeHq": _Registry(_addr(20), {i: _addr(400 + i) for i in range(30)}),
        "VaultBook": _Registry(_addr(21), {i: _addr(500 + i) for i in range(10)}),
        "Switchboard": _Registry(_addr(22), {i: _addr(600 + i) for i in range(10)}),
    }
    finalized_candidates = {}
    for index, (label, minimum) in enumerate(LEDGER.FINALIZED_0009):
        candidate = _GovernedCandidate(
            _addr(700 + index),
            _addr(900),
            minimum,
        )
        candidate.setActionTimeLockAfterSetup(minimum)
        candidate.relinquishGov()
        finalized_candidates[label] = candidate

    defaults_candidate = _addr(23)
    mission_control_candidate = _MissionControlCandidate(
        registries["RipeHq"].getAddr(5),
        registries["RipeHq"].address,
    )

    migration = _FakeMigration(
        contracts={
            **registries,
            **finalized_candidates,
            "BondBooster": _Contract(_addr(901)),
            "MissionControlCandidate0009": mission_control_candidate,
        },
        addresses={"DefaultsRobinhoodLive": defaults_candidate},
        account=_addr(900),
        manifest_contracts={
            "MissionControlCandidate0009": {
                "address": mission_control_candidate.address,
                "args": encode(
                    ["address", "address"],
                    [registries["RipeHq"].address, defaults_candidate],
                ).hex(),
            },
            "DefaultsRobinhoodLiveCandidate0009": {
                "address": defaults_candidate,
            },
        },
        rpc=rpc,
    )
    return migration


def test_0010_promotes_0009_then_leaves_four_new_candidates_pending(
    monkeypatch,
):
    migration = _make_0010_migration()
    messages = []
    headings = []
    monkeypatch.setattr(LEDGER.log, "info", messages.append)
    monkeypatch.setattr(LEDGER.log, "h2", headings.append)
    validation_calls = []
    validate = LEDGER.validate_ledger_action_block_source

    def validate_before_instructions(*args, **kwargs):
        validation_calls.append(
            (
                args,
                kwargs,
                len(migration.deployments),
                sum("[1] 0x" in message for message in messages),
            )
        )
        return validate(*args, **kwargs)

    monkeypatch.setattr(
        LEDGER,
        "validate_ledger_action_block_source",
        validate_before_instructions,
    )

    LEDGER.migrate(migration)

    assert len(migration.promotions) == 17
    assert migration.promotion_batch_sizes == [17]
    assert migration.promotions[-1][0:2] == (
        "DefaultsRobinhoodLive",
        "DefaultsRobinhoodLiveCandidate0009",
    )
    assert migration.promotions[-1][-2:] == (
        "MissionControlCandidate0009",
        1,
    )
    intents = {spec.canonical_name: spec for spec in migration.promotion_specs}
    assert {
        name: spec.expected_source_path for name, spec in intents.items()
    } == LEDGER.CANONICAL_SOURCE_PATHS
    assert intents["MissionControl"].registry_name == "RipeHq"
    assert intents["MissionControl"].expected_constructor_args == (
        migration.contracts["RipeHq"],
        migration.addresses["DefaultsRobinhoodLive"],
    )
    assert intents["DefaultsRobinhoodLive"].expected_constructor_args == ()
    assert intents["DefaultsRobinhoodLive"].activation_expected_constructor_args == (
        migration.contracts["RipeHq"],
        migration.addresses["DefaultsRobinhoodLive"],
    )
    assert [row[0] for row in migration.deployments] == [
        "Ledger",
        "Lootbox",
        "Teller",
        "RipeGov",
    ]
    assert all(
        label.endswith("Candidate0010")
        for _name, label, _args, _contract in migration.deployments
    )
    assert validation_calls == [
        (
            (
                migration,
                migration.deployments[0][3].address,
                LEDGER.LEDGER_ACTION_BLOCK_SOURCE,
            ),
            {"allow_local_preview": True},
            1,
            0,
        )
    ]
    assert sum("[1] 0x" in message for message in messages) == 4
    assert sum("[2] 0x" in message for message in messages) == 4
    assert "Ledger node-backed validation skipped for local/fork preview" in headings


def test_0010_validation_failure_stops_before_update_instructions(monkeypatch):
    migration = _make_0010_migration()
    messages = []
    monkeypatch.setattr(LEDGER.log, "info", messages.append)

    def fail_validation(*_args, **_kwargs):
        raise AssertionError("Ledger action-block source mismatch")

    monkeypatch.setattr(
        LEDGER,
        "validate_ledger_action_block_source",
        fail_validation,
    )

    with pytest.raises(
        AssertionError,
        match="Ledger action-block source mismatch",
    ):
        LEDGER.migrate(migration)

    assert [row[0] for row in migration.deployments] == ["Ledger"]
    assert not any("[1] 0x" in message for message in messages)
    assert not any("[2] 0x" in message for message in messages)


@pytest.mark.parametrize(
    "source_read,action_block_read,message",
    [
        (
            (0x65).to_bytes(32, "big"),
            (99).to_bytes(32, "big"),
            "Ledger action-block source mismatch",
        ),
        (
            b"\x00" * 31,
            (99).to_bytes(32, "big"),
            r"malformed ACTION_BLOCK_SOURCE\(\) readback",
        ),
        (
            (0x64).to_bytes(32, "big"),
            b"\x00" * 31,
            r"malformed getArbActionBlock\(\) readback",
        ),
        (
            (0x64).to_bytes(32, "big"),
            (0).to_bytes(32, "big"),
            "ArbSys action block reads zero",
        ),
    ],
)
def test_0010_real_rpc_ledger_candidate_enforces_complete_node_validation(
    monkeypatch,
    source_read,
    action_block_read,
    message,
):
    migration = _make_0010_migration(rpc="https://rpc.example")

    class FakeEth:
        @staticmethod
        def get_code(_address):
            return b"\x01"

        @staticmethod
        def call(transaction):
            source_selector = RealWeb3.keccak(text="ACTION_BLOCK_SOURCE()")[:4]
            if transaction["data"] == source_selector:
                return source_read
            return action_block_read

    class FakeWeb3:
        eth = FakeEth()

        def __init__(self, _provider):
            self.eth = self.__class__.eth

        @staticmethod
        def HTTPProvider(rpc):
            return rpc

        @staticmethod
        def to_checksum_address(address):
            return address

        @staticmethod
        def keccak(*, text):
            return RealWeb3.keccak(text=text)

        @staticmethod
        def is_connected():
            return True

    monkeypatch.setattr(ledger_deployment, "_load_web3", lambda: FakeWeb3)

    with pytest.raises(AssertionError, match=message):
        LEDGER.migrate(migration)

    assert [row[0] for row in migration.deployments] == ["Ledger"]


def test_0010_defaults_dependency_mismatch_fails_before_any_write():
    from eth_abi.abi import encode

    registries = {
        "RipeHq": _Registry(_addr(24)),
        "VaultBook": _Registry(_addr(25)),
        "Switchboard": _Registry(_addr(26)),
    }
    defaults_candidate = _addr(27)
    mission_control_candidate = _MissionControlCandidate(
        _addr(28),
        registries["RipeHq"].address,
    )
    migration = _FakeMigration(
        contracts={
            **registries,
            "MissionControlCandidate0009": mission_control_candidate,
        },
        addresses={"DefaultsRobinhoodLive": defaults_candidate},
        manifest_contracts={
            "MissionControlCandidate0009": {
                "address": mission_control_candidate.address,
                "args": encode(
                    ["address", "address"],
                    [registries["RipeHq"].address, _addr(29)],
                ).hex(),
            },
            "DefaultsRobinhoodLiveCandidate0009": {
                "address": defaults_candidate,
            },
        },
    )

    with pytest.raises(
        RuntimeError,
        match="DEFAULTS_DEPENDENCY_CONSTRUCTOR_MISMATCH",
    ):
        LEDGER.migrate(migration)

    assert migration.promotions == []
    assert migration.deployments == []


def test_0011_promotes_0010_and_prepares_slot_three_without_registering(
    monkeypatch,
):
    selected_morpho_v2_factory = _addr(33)
    selected_chainlink = _addr(35)
    selected_curve = _addr(36)
    monkeypatch.setattr(
        BLUECHIP,
        "address",
        lambda key: selected_morpho_v2_factory if key == "MORPHO_V2_FACTORY" else None,
    )
    price_desk = _Registry(
        _addr(30),
        slots={1: selected_chainlink, 2: selected_curve},
        count=3,
    )
    migration = _FakeMigration(
        contracts={
            "RipeHq": _Registry(_addr(31)),
            "VaultBook": _Registry(_addr(32)),
            "PriceDesk": price_desk,
        },
        addresses={
            "DefaultsRobinhoodLive": _addr(34),
            "ChainlinkPrices": selected_chainlink,
            "CurvePrices": selected_curve,
        },
    )
    messages = []
    monkeypatch.setattr(BLUECHIP.log, "info", messages.append)

    BLUECHIP.migrate(migration)

    assert len(migration.promotions) == 4
    assert migration.promotion_batch_sizes == [4]
    intents = {spec.canonical_name: spec for spec in migration.promotion_specs}
    assert set(intents) == {"Ledger", "Lootbox", "Teller", "RipeGov"}
    assert {
        name: spec.expected_source_path for name, spec in intents.items()
    } == BLUECHIP.CANONICAL_SOURCE_PATHS
    assert all(
        spec.registry_name in {"RipeHq", "VaultBook"} for spec in intents.values()
    )
    assert intents["Ledger"].expected_constructor_args == (
        migration.contracts["RipeHq"],
        migration.addresses["DefaultsRobinhoodLive"],
        BLUECHIP.LEDGER_ACTION_BLOCK_SOURCE,
    )
    assert [row[0] for row in migration.deployments] == ["BlueChipYieldPrices"]
    name, label, args, candidate = migration.deployments[0]
    assert name == "BlueChipYieldPrices"
    assert label == BLUECHIP.BLUECHIP_CANDIDATE
    assert args[-1] == selected_morpho_v2_factory
    assert candidate.actionTimeLock() == BLUECHIP.PRICE_CHANGE_MIN_TIMELOCK
    assert candidate.governance() == ZERO_ADDRESS
    assert price_desk.slots == {1: selected_chainlink, 2: selected_curve}
    assert sum("[1] 0x" in message for message in messages) == 1
    assert sum("[2] 0x" in message for message in messages) == 1


def test_mock_governance_fixture_is_bound_to_the_session_environment():
    tree = ast.parse(
        (ROOT / "tests" / "conf_mock.py").read_text(),
        filename="tests/conf_mock.py",
    )
    governance = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "governance"
    )
    assert [argument.arg for argument in governance.args.args] == ["env"]


def test_0012_only_promotes_after_price_desk_readback(monkeypatch):
    selected_morpho_v2_factory = _addr(43)
    monkeypatch.setattr(
        PROMOTE_BLUECHIP,
        "address",
        lambda key: selected_morpho_v2_factory if key == "MORPHO_V2_FACTORY" else None,
    )
    price_desk = _Registry(_addr(40), {3: _addr(41)}, count=3)
    migration = _FakeMigration(
        contracts={"PriceDesk": price_desk, "RipeHq": _Contract(_addr(42))}
    )

    PROMOTE_BLUECHIP.migrate(migration)

    assert migration.deployments == []
    assert migration.promotions == [
        (
            "BlueChipYieldPrices",
            "BlueChipYieldPricesCandidate0011",
            price_desk.address,
            3,
            None,
            None,
        )
    ]
    assert migration.promotion_specs[0].registry_name == "PriceDesk"
    assert (
        migration.promotion_specs[0].expected_source_path
        == "contracts/priceSources/BlueChipYieldPrices.vy"
    )
    assert (
        migration.promotion_specs[0].expected_constructor_args[0]
        is (migration.contracts["RipeHq"])
    )
    assert (
        migration.promotion_specs[0].expected_constructor_args[-1]
        == selected_morpho_v2_factory
    )


def test_0013_prepares_unpaused_vault_migrator_for_exact_hq_id_25(
    monkeypatch,
):
    from eth_abi.abi import decode
    from web3 import Web3

    hq = _Registry(
        _addr(50),
        {23: _addr(51), 24: _addr(52)},
        count=25,
    )
    migration = _FakeMigration(contracts={"RipeHq": hq})
    messages = []
    monkeypatch.setattr(VAULT_MIGRATOR.log, "info", messages.append)

    VAULT_MIGRATOR.migrate(migration)

    assert migration.promotions == []
    assert len(migration.deployments) == 1
    name, label, args, candidate = migration.deployments[0]
    assert name == "VaultMigrator"
    assert label == "VaultMigratorCandidate0013"
    assert args == (
        hq,
        VAULT_MIGRATOR.VAULT_MIGRATOR_SHOULD_PAUSE,
        ZERO_ADDRESS,
    )
    assert candidate.isPaused() is False
    assert hq.slots == {23: _addr(51), 24: _addr(52)}
    assert sum("[1] 0x" in message for message in messages) == 1
    assert sum("[2] 0x" in message for message in messages) == 1

    start, confirm = VAULT_MIGRATOR._add_calldata(
        candidate.address,
        "VaultMigrator",
    )
    start_bytes = bytes.fromhex(start)
    confirm_bytes = bytes.fromhex(confirm)
    assert (
        start_bytes[:4]
        == Web3.keccak(text="startAddNewAddressToRegistry(address,string)")[:4]
    )
    assert decode(["address", "string"], start_bytes[4:]) == (
        candidate.address,
        "VaultMigrator",
    )
    assert (
        confirm_bytes[:4]
        == Web3.keccak(text="confirmNewAddressToRegistry(address)")[:4]
    )
    assert decode(["address"], confirm_bytes[4:]) == (candidate.address,)


def test_0013_fails_closed_until_ccip_slots_23_and_24_are_occupied():
    hq = _Registry(_addr(60), count=23)
    migration = _FakeMigration(contracts={"RipeHq": hq})

    with pytest.raises(
        AssertionError,
        match="next id is not VaultMigrator slot 25",
    ):
        VAULT_MIGRATOR.migrate(migration)

    assert migration.deployments == []


def test_0013_fails_closed_if_a_prior_ccip_slot_is_disabled():
    hq = _Registry(_addr(65), {23: _addr(66)}, count=25)
    migration = _FakeMigration(contracts={"RipeHq": hq})

    with pytest.raises(
        AssertionError,
        match="CCIP pool slot 24 is not active",
    ):
        VAULT_MIGRATOR.migrate(migration)

    assert migration.deployments == []


def test_0014_only_promotes_vault_migrator_after_hq_readback():
    candidate_address = _addr(71)
    hq = _Registry(_addr(70), {25: candidate_address}, count=26)
    migration = _FakeMigration(contracts={"RipeHq": hq})

    PROMOTE_VAULT_MIGRATOR.migrate(migration)

    assert migration.deployments == []
    assert migration.promotions == [
        (
            "VaultMigrator",
            "VaultMigratorCandidate0013",
            hq.address,
            25,
            None,
            None,
        )
    ]
    assert migration.promotion_specs[0].registry_name == "RipeHq"
    assert (
        migration.promotion_specs[0].expected_source_path
        == "contracts/core/VaultMigrator.vy"
    )
    assert migration.promotion_specs[0].expected_constructor_args == (
        hq,
        PROMOTE_VAULT_MIGRATOR.VAULT_MIGRATOR_SHOULD_PAUSE,
        ZERO_ADDRESS,
    )
