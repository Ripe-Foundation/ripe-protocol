from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/prepare_defaults.py"
MODULE_NAME = "prepare_defaults_snapshot_under_test"
SPEC = importlib.util.spec_from_file_location(MODULE_NAME, SCRIPT)
assert SPEC is not None and SPEC.loader is not None
prepare_defaults = importlib.util.module_from_spec(SPEC)
sys.modules[MODULE_NAME] = prepare_defaults
SPEC.loader.exec_module(prepare_defaults)

MC = "0x" + "11" * 20
LEDGER = "0x" + "22" * 20
ASSET = "0x" + "33" * 20
USDG = "0x" + "44" * 20
TRAINING_WHEELS = "0x" + "55" * 20
CONTRIBUTOR = "0x" + "66" * 20
UNDERSCORE = "0x" + "77" * 20
SIGNER = "0x" + "88" * 20
BLOCK_NUMBER = 100
BLOCK_HASH = bytes.fromhex("aa" * 32)


@pytest.fixture(scope="session", autouse=True)
def ripe_hq() -> None:
    """Keep this source-only test independent of protocol deployment."""


def _struct_abi(name: str, components: list[dict]) -> dict:
    return {
        "type": "function",
        "name": name,
        "outputs": [{"type": "tuple", "components": components}],
    }


MC_ABI = [
    _struct_abi("genConfig", [{"name": "value", "type": "uint256"}]),
    _struct_abi("genDebtConfig", [{"name": "value", "type": "uint256"}]),
    _struct_abi("ripeBondConfig", [{"name": "asset", "type": "address"}]),
    _struct_abi("rewardsConfig", [{"name": "value", "type": "uint256"}]),
    _struct_abi(
        "ripeGovVaultConfig",
        [
            {"name": "asset", "type": "address"},
            {"name": "assetWeight", "type": "uint256"},
        ],
    ),
    _struct_abi("hrConfig", [{"name": "contributor", "type": "address"}]),
    _struct_abi("assetConfig", [{"name": "value", "type": "uint256"}]),
    # The generator also reads these; the deployed-ABI agreement check requires
    # every one of them to be present on both sides.
    {"type": "function", "name": "assets", "inputs": [{"type": "uint256"}],
     "outputs": [{"type": "address"}]},
    {"type": "function", "name": "numAssets", "inputs": [],
     "outputs": [{"type": "uint256"}]},
    {"type": "function", "name": "numLiteSigners", "inputs": [],
     "outputs": [{"type": "uint256"}]},
    {"type": "function", "name": "liteSigners", "inputs": [{"type": "uint256"}],
     "outputs": [{"type": "address"}]},
    {"type": "function", "name": "getPriorityLiqAssetVaults", "inputs": [],
     "outputs": [{"type": "tuple[]"}]},
    {"type": "function", "name": "getPriorityStabVaults", "inputs": [],
     "outputs": [{"type": "tuple[]"}]},
    {"type": "function", "name": "getPriorityPriceSourceIds", "inputs": [],
     "outputs": [{"type": "uint256[]"}]},
    {"type": "function", "name": "underscoreRegistry", "inputs": [],
     "outputs": [{"type": "address"}]},
    {"type": "function", "name": "trainingWheels", "inputs": [],
     "outputs": [{"type": "address"}]},
    {"type": "function", "name": "shouldCheckLastTouch", "inputs": [],
     "outputs": [{"type": "bool"}]},
]

LEDGER_ABI = [
    {"type": "function", "name": name, "inputs": [], "outputs": [{"type": "uint256"}]}
    for name in prepare_defaults.LEDGER_READS
]

MANIFEST_BYTES = json.dumps(
    {
        "contracts": {
            "MissionControl": {"address": MC, "abi": MC_ABI},
            "Ledger": {"address": LEDGER, "abi": LEDGER_ABI},
            "GreenUsdgPool": {"address": USDG},
            "TrainingWheels": {"address": TRAINING_WHEELS},
            "Contributor": {"address": CONTRIBUTOR},
        }
    },
    sort_keys=True,
    separators=(",", ":"),
).encode()
ALTERNATE_MANIFEST_BYTES = json.dumps(
    {
        "contracts": json.loads(MANIFEST_BYTES)["contracts"],
        "review_note": "same addresses, different bound manifest bytes",
    },
    sort_keys=True,
    separators=(",", ":"),
).encode()
GENERATOR_BYTES = b"deterministic generator fixture"


def _canonical_abi(abi: list[dict]) -> bytes:
    return json.dumps(abi, sort_keys=True, separators=(",", ":")).encode()


ABI_INPUTS = prepare_defaults.AbiInputs(
    mission_control_abi_bytes=_canonical_abi(MC_ABI),
    ledger_abi_bytes=_canonical_abi(LEDGER_ABI),
    compiler_version="v0.4.3+commit.testfixture",
    mission_control_input_integrity="ab" * 32,
    ledger_input_integrity="cd" * 32,
)


MC_VALUES = {
    "numAssets": 2,
    "assets": lambda index: ASSET if index == 1 else "0x" + "00" * 20,
    "ripeBondConfig": (USDG,),
    "getPriorityLiqAssetVaults": [(1, ASSET)],
    "hrConfig": (CONTRIBUTOR,),
    "trainingWheels": TRAINING_WHEELS,
    "genConfig": (7,),
    "genDebtConfig": (8,),
    "rewardsConfig": (9,),
    "ripeGovVaultConfig": ("0x" + "00" * 20, 0),
    "underscoreRegistry": UNDERSCORE,
    "shouldCheckLastTouch": True,
    "assetConfig": (10,),
    "getPriorityStabVaults": [],
    "getPriorityPriceSourceIds": [3, 4],
    "numLiteSigners": 2,
    "liteSigners": lambda index: SIGNER if index == 1 else "0x" + "00" * 20,
}
LEDGER_VALUES = {
    "ripeAvailForRewards": 11,
    "ripeAvailForHr": 12,
    "ripeAvailForBonds": 13,
}


class FakeBoundCall:
    def __init__(self, eth, address: str, name: str, args: tuple):
        self.eth = eth
        self.address = address
        self.name = name
        self.args = args

    def call(self, *, block_identifier: int):
        self.eth.contract_reads.append(
            (self.address, self.name, self.args, block_identifier)
        )
        values = (
            MC_VALUES if self.address.lower() == MC.lower() else LEDGER_VALUES
        )
        value = values[self.name]
        return value(*self.args) if callable(value) else value


class FakeFunctions:
    def __init__(self, eth, address: str):
        self.eth = eth
        self.address = address

    def __getattr__(self, name: str):
        return lambda *args: FakeBoundCall(self.eth, self.address, name, args)


class FakeContract:
    def __init__(self, eth, address: str):
        self.functions = FakeFunctions(eth, address)


class FakeEth:
    def __init__(
        self,
        *,
        chain_id: int = prepare_defaults.EXPECTED_CHAIN_ID,
        finalized_number: int = 120,
        selected_hashes: tuple[bytes, ...] = (BLOCK_HASH, BLOCK_HASH),
        selected_available: bool = True,
        finalized_available: bool = True,
        symbol_available: bool = True,
        code_error: bool = False,
    ):
        self.chain_id = chain_id
        self.finalized_number = finalized_number
        self.selected_hashes = selected_hashes
        self.selected_available = selected_available
        self.finalized_available = finalized_available
        self.symbol_available = symbol_available
        self.code_error = code_error
        self.selected_reads = 0
        self.block_reads: list[str | int] = []
        self.code_reads: list[tuple[str, int]] = []
        self.contract_reads: list[tuple[str, str, tuple, int]] = []
        self.raw_reads: list[tuple[dict, int]] = []

    def get_block(self, identifier: str | int):
        self.block_reads.append(identifier)
        if identifier == "finalized":
            if not self.finalized_available:
                raise KeyError("finalized block unavailable")
            return {
                "number": self.finalized_number,
                "hash": bytes.fromhex("ff" * 32),
            }
        if identifier != BLOCK_NUMBER or not self.selected_available:
            raise KeyError("selected block unavailable")
        position = min(self.selected_reads, len(self.selected_hashes) - 1)
        self.selected_reads += 1
        return {"number": BLOCK_NUMBER, "hash": self.selected_hashes[position]}

    def get_code(self, address: str, *, block_identifier: int) -> bytes:
        self.code_reads.append((address, block_identifier))
        if self.code_error:
            raise RuntimeError("historical code unavailable")
        return b"mission-control-code" if address.lower() == MC.lower() else b"ledger-code"

    def contract(self, *, address: str, abi: list) -> FakeContract:
        del abi
        return FakeContract(self, address)

    def call(self, transaction: dict, *, block_identifier: int) -> bytes:
        self.raw_reads.append((transaction, block_identifier))
        if not self.symbol_available:
            raise RuntimeError("symbol() unavailable")
        symbol = b"FAKE"
        return (
            (32).to_bytes(32, "big")
            + len(symbol).to_bytes(32, "big")
            + symbol.ljust(32, b"\x00")
        )


class FakeWeb3:
    def __init__(self, eth: FakeEth):
        self.eth = eth


def _snapshot_and_source(eth: FakeEth) -> tuple[object, str]:
    w3 = FakeWeb3(eth)
    snapshot = prepare_defaults.select_snapshot(
        w3,
        MC,
        LEDGER,
        block_number=BLOCK_NUMBER,
        manifest_bytes=MANIFEST_BYTES,
        generator_bytes=GENERATOR_BYTES,
        abi_inputs=ABI_INPUTS,
    )
    result = prepare_defaults.build(
        w3,
        MC,
        LEDGER,
        snapshot,
        manifest_bytes=MANIFEST_BYTES,
        abi_inputs=ABI_INPUTS,
    )
    prepare_defaults.verify_snapshot(w3, snapshot)
    return snapshot, result.source


def test_every_live_read_is_pinned_and_provenance_is_embedded():
    eth = FakeEth()
    snapshot, source = _snapshot_and_source(eth)

    assert eth.block_reads == [
        "finalized",
        BLOCK_NUMBER,
        "finalized",
        BLOCK_NUMBER,
    ]
    assert eth.code_reads and all(read[-1] == BLOCK_NUMBER for read in eth.code_reads)
    assert eth.contract_reads and all(
        read[-1] == BLOCK_NUMBER for read in eth.contract_reads
    )
    assert eth.raw_reads == [
        (
            {"to": ASSET, "data": prepare_defaults.SYMBOL_SELECTOR},
            BLOCK_NUMBER,
        )
    ]
    assert snapshot.block_hash == "0x" + BLOCK_HASH.hex()
    assert f"#   chain id: {prepare_defaults.EXPECTED_CHAIN_ID}" in source
    assert f"#   snapshot block: {BLOCK_NUMBER}" in source
    assert (
        "# Regenerate with:  python scripts/prepare_defaults.py "
        f"--network {prepare_defaults.DEFAULT_NETWORK.key} "
        f"--block-number {BLOCK_NUMBER}"
    ) in source
    assert (
        f"#   manifest sha256: {hashlib.sha256(MANIFEST_BYTES).hexdigest()}"
        in source
    )
    assert (
        f"#   generator sha256: {hashlib.sha256(GENERATOR_BYTES).hexdigest()}"
        in source
    )
    assert f"#   Vyper compiler: {ABI_INPUTS.compiler_version}" in source
    assert (
        "#   Vyper compiler identity sha256: "
        f"{hashlib.sha256(ABI_INPUTS.compiler_version.encode()).hexdigest()}"
    ) in source
    assert (
        "#   MissionControl compiler-input integrity: "
        f"{ABI_INPUTS.mission_control_input_integrity}"
    ) in source
    assert (
        "#   MissionControl canonical ABI sha256: "
        f"{hashlib.sha256(ABI_INPUTS.mission_control_abi_bytes).hexdigest()}"
    ) in source
    assert (
        f"#   Ledger compiler-input integrity: {ABI_INPUTS.ledger_input_integrity}"
        in source
    )
    assert (
        "#   Ledger canonical ABI sha256: "
        f"{hashlib.sha256(ABI_INPUTS.ledger_abi_bytes).hexdigest()}"
    ) in source
    assert (
        "#   MissionControl code sha256: "
        f"{hashlib.sha256(b'mission-control-code').hexdigest()}"
    ) in source
    assert (
        f"#   Ledger code sha256: {hashlib.sha256(b'ledger-code').hexdigest()}"
        in source
    )
    assert "CONTRIB_TEMPLATE: immutable(address)" in source
    assert "def __init__(_contribTemplate: address):" in source
    assert "CONTRIB_TEMPLATE = _contribTemplate" in source
    assert f"CONTRIB_TEMPLATE: constant(address) = {CONTRIBUTOR}" not in source


def test_same_block_is_byte_identical_as_finalized_head_advances():
    _, first = _snapshot_and_source(FakeEth(finalized_number=120))
    _, second = _snapshot_and_source(FakeEth(finalized_number=140))

    assert first.encode() == second.encode()


def test_wrong_chain_fails_before_any_block_or_code_read():
    eth = FakeEth(chain_id=1)

    with pytest.raises(prepare_defaults.SnapshotError, match="expected Robinhood"):
        prepare_defaults.select_snapshot(
            FakeWeb3(eth),
            MC,
            LEDGER,
            block_number=BLOCK_NUMBER,
            manifest_bytes=MANIFEST_BYTES,
            generator_bytes=GENERATOR_BYTES,
            abi_inputs=ABI_INPUTS,
        )

    assert not eth.block_reads
    assert not eth.code_reads


@pytest.mark.parametrize("block_number", [-1, True, "100", None])
def test_invalid_block_number_fails_before_provider_reads(block_number):
    eth = FakeEth()

    with pytest.raises(prepare_defaults.SnapshotError, match="non-negative integer"):
        prepare_defaults.select_snapshot(
            FakeWeb3(eth),
            MC,
            LEDGER,
            block_number=block_number,
            manifest_bytes=MANIFEST_BYTES,
            generator_bytes=GENERATOR_BYTES,
            abi_inputs=ABI_INPUTS,
        )

    assert not eth.block_reads
    assert not eth.code_reads


@pytest.mark.parametrize("missing", ["finalized", "selected"])
def test_missing_block_fails_closed(missing):
    eth = FakeEth(
        finalized_available=missing != "finalized",
        selected_available=missing != "selected",
    )

    with pytest.raises(prepare_defaults.SnapshotError, match="block"):
        prepare_defaults.select_snapshot(
            FakeWeb3(eth),
            MC,
            LEDGER,
            block_number=BLOCK_NUMBER,
            manifest_bytes=MANIFEST_BYTES,
            generator_bytes=GENERATOR_BYTES,
            abi_inputs=ABI_INPUTS,
        )


def test_unfinalized_requested_block_fails_before_state_reads():
    eth = FakeEth(finalized_number=BLOCK_NUMBER - 1)

    with pytest.raises(prepare_defaults.SnapshotError, match="newer than finalized"):
        prepare_defaults.select_snapshot(
            FakeWeb3(eth),
            MC,
            LEDGER,
            block_number=BLOCK_NUMBER,
            manifest_bytes=MANIFEST_BYTES,
            generator_bytes=GENERATOR_BYTES,
            abi_inputs=ABI_INPUTS,
        )

    assert eth.block_reads == ["finalized"]
    assert not eth.code_reads


def test_provider_code_read_failure_has_snapshot_context():
    eth = FakeEth(code_error=True)

    with pytest.raises(
        prepare_defaults.SnapshotError,
        match=f"MissionControl code.*{MC}.*snapshot block {BLOCK_NUMBER}",
    ):
        prepare_defaults.select_snapshot(
            FakeWeb3(eth),
            MC,
            LEDGER,
            block_number=BLOCK_NUMBER,
            manifest_bytes=MANIFEST_BYTES,
            generator_bytes=GENERATOR_BYTES,
            abi_inputs=ABI_INPUTS,
        )

    assert eth.code_reads == [(MC, BLOCK_NUMBER)]


def test_selected_block_hash_change_fails_after_collection():
    eth = FakeEth(selected_hashes=(BLOCK_HASH, bytes.fromhex("bb" * 32)))

    with pytest.raises(prepare_defaults.SnapshotError, match="changed during collection"):
        _snapshot_and_source(eth)


def test_provider_switch_fails_before_final_verification_reads():
    eth = FakeEth()
    w3 = FakeWeb3(eth)
    snapshot = prepare_defaults.select_snapshot(
        w3,
        MC,
        LEDGER,
        block_number=BLOCK_NUMBER,
        manifest_bytes=MANIFEST_BYTES,
        generator_bytes=GENERATOR_BYTES,
        abi_inputs=ABI_INPUTS,
    )
    eth.chain_id = 1

    with pytest.raises(prepare_defaults.SnapshotError, match="chain id changed"):
        prepare_defaults.verify_snapshot(w3, snapshot)

    assert eth.block_reads == ["finalized", BLOCK_NUMBER]


def test_finality_regression_fails_before_selected_block_reread():
    eth = FakeEth()
    w3 = FakeWeb3(eth)
    snapshot = prepare_defaults.select_snapshot(
        w3,
        MC,
        LEDGER,
        block_number=BLOCK_NUMBER,
        manifest_bytes=MANIFEST_BYTES,
        generator_bytes=GENERATOR_BYTES,
        abi_inputs=ABI_INPUTS,
    )
    eth.finalized_number = BLOCK_NUMBER - 1

    with pytest.raises(prepare_defaults.SnapshotError, match="no longer finalized"):
        prepare_defaults.verify_snapshot(w3, snapshot)

    assert eth.block_reads == ["finalized", BLOCK_NUMBER, "finalized"]


@pytest.mark.parametrize(
    ("mc_addr", "ledger_addr", "manifest_bytes", "error"),
    [
        (MC, LEDGER, ALTERNATE_MANIFEST_BYTES, "manifest bytes"),
        ("0x" + "99" * 20, LEDGER, MANIFEST_BYTES, "MissionControl address"),
        (MC, "0x" + "99" * 20, MANIFEST_BYTES, "Ledger address"),
    ],
)
def test_build_rejects_inputs_that_do_not_match_provenance(
    mc_addr, ledger_addr, manifest_bytes, error
):
    eth = FakeEth()
    w3 = FakeWeb3(eth)
    snapshot = prepare_defaults.select_snapshot(
        w3,
        MC,
        LEDGER,
        block_number=BLOCK_NUMBER,
        manifest_bytes=MANIFEST_BYTES,
        generator_bytes=GENERATOR_BYTES,
        abi_inputs=ABI_INPUTS,
    )

    with pytest.raises(prepare_defaults.SnapshotError, match=error):
        prepare_defaults.build(
            w3,
            mc_addr,
            ledger_addr,
            snapshot,
            manifest_bytes=manifest_bytes,
            abi_inputs=ABI_INPUTS,
        )

    assert not eth.contract_reads
    assert not eth.raw_reads


def test_unnamed_asset_symbol_is_read_at_the_pinned_snapshot_block():
    eth = FakeEth(symbol_available=True)

    _, source = _snapshot_and_source(eth)

    assert eth.raw_reads == [
        (
            {"to": ASSET, "data": prepare_defaults.SYMBOL_SELECTOR},
            BLOCK_NUMBER,
        )
    ]
    assert "FAKE: constant(address)" in source
    assert "# FAKE" in source


def test_missing_unnamed_asset_symbol_fails_closed():
    eth = FakeEth(symbol_available=False)

    with pytest.raises(
        prepare_defaults.SnapshotError,
        match="token symbol unavailable at snapshot block",
    ):
        _snapshot_and_source(eth)

    assert eth.raw_reads


def test_token_symbol_decoder_accepts_legacy_bytes32():
    assert prepare_defaults._decode_token_symbol(
        b"SPCX".ljust(32, b"\x00"), ASSET
    ) == "SPCX"


@pytest.mark.parametrize(
    ("manifest_bytes", "mc_addr", "ledger_addr", "error"),
    [
        (b"{", MC, LEDGER, "not valid JSON"),
        (b"{}", MC, LEDGER, "contracts object"),
        (
            json.dumps({"contracts": {"Ledger": {"address": LEDGER}}}).encode(),
            MC,
            LEDGER,
            "MissionControl.address",
        ),
        (
            json.dumps(
                {"contracts": {"MissionControl": {"address": MC}}}
            ).encode(),
            MC,
            LEDGER,
            "Ledger.address",
        ),
        (MANIFEST_BYTES, "0x" + "99" * 20, LEDGER, "does not match manifest"),
        (MANIFEST_BYTES, MC, "0x" + "99" * 20, "does not match manifest"),
    ],
)
def test_manifest_binding_fails_before_provider_reads(
    manifest_bytes, mc_addr, ledger_addr, error
):
    eth = FakeEth()

    with pytest.raises(prepare_defaults.SnapshotError, match=error):
        prepare_defaults.select_snapshot(
            FakeWeb3(eth),
            mc_addr,
            ledger_addr,
            block_number=BLOCK_NUMBER,
            manifest_bytes=manifest_bytes,
            generator_bytes=GENERATOR_BYTES,
            abi_inputs=ABI_INPUTS,
        )

    assert not eth.block_reads
    assert not eth.code_reads


def test_abi_mutation_changes_provenance_and_cannot_reuse_snapshot():
    mutated_abi = MC_ABI + [
        {
            "type": "function",
            "name": "mutated",
            "inputs": [],
            "outputs": [],
            "stateMutability": "view",
        }
    ]
    mutated_inputs = replace(
        ABI_INPUTS, mission_control_abi_bytes=_canonical_abi(mutated_abi)
    )
    original_snapshot, _ = _snapshot_and_source(FakeEth())
    mutated_snapshot = prepare_defaults.select_snapshot(
        FakeWeb3(FakeEth()),
        MC,
        LEDGER,
        block_number=BLOCK_NUMBER,
        manifest_bytes=MANIFEST_BYTES,
        generator_bytes=GENERATOR_BYTES,
        abi_inputs=mutated_inputs,
    )

    assert (
        original_snapshot.mission_control_abi_sha256
        != mutated_snapshot.mission_control_abi_sha256
    )
    with pytest.raises(
        prepare_defaults.SnapshotError, match="ABI/compiler inputs"
    ):
        prepare_defaults.build(
            FakeWeb3(FakeEth()),
            MC,
            LEDGER,
            original_snapshot,
            manifest_bytes=MANIFEST_BYTES,
            abi_inputs=mutated_inputs,
        )


def test_compiler_input_integrity_cannot_reuse_snapshot():
    snapshot, _ = _snapshot_and_source(FakeEth())
    mutated_inputs = replace(
        ABI_INPUTS, mission_control_input_integrity="ef" * 32
    )

    with pytest.raises(
        prepare_defaults.SnapshotError, match="ABI/compiler inputs"
    ):
        prepare_defaults.build(
            FakeWeb3(FakeEth()),
            MC,
            LEDGER,
            snapshot,
            manifest_bytes=MANIFEST_BYTES,
            abi_inputs=mutated_inputs,
        )


def test_compiler_identity_cannot_reuse_snapshot():
    snapshot, _ = _snapshot_and_source(FakeEth())
    mutated_inputs = replace(ABI_INPUTS, compiler_version="v0.4.4+commit.changed")

    with pytest.raises(
        prepare_defaults.SnapshotError, match="ABI/compiler inputs"
    ):
        prepare_defaults.build(
            FakeWeb3(FakeEth()),
            MC,
            LEDGER,
            snapshot,
            manifest_bytes=MANIFEST_BYTES,
            abi_inputs=mutated_inputs,
        )


def test_load_abi_inputs_compiles_each_canonical_abi_once(monkeypatch):
    calls: list[tuple[str, ...]] = []

    def fake_vyper(*args: str) -> bytes:
        calls.append(args)
        if args == ("--version",):
            return b"v0.4.3+commit.fixture\n"
        abi = MC_ABI if args[-1] == prepare_defaults.MISSION_CONTROL_SOURCE else []
        integrity = b"ab" * 32 if abi else b"cd" * 32
        return json.dumps(abi, indent=None).encode() + b"\n" + integrity + b"\n"

    monkeypatch.setattr(prepare_defaults, "_run_vyper", fake_vyper)

    inputs = prepare_defaults.load_abi_inputs()

    assert calls == [
        ("--version",),
        (
            "-p",
            ".",
            "-f",
            "abi,integrity",
            prepare_defaults.MISSION_CONTROL_SOURCE,
        ),
        (
            "-p",
            ".",
            "-f",
            "abi,integrity",
            prepare_defaults.LEDGER_SOURCE,
        ),
    ]
    assert inputs.mission_control_abi_bytes == _canonical_abi(MC_ABI)
    assert inputs.ledger_abi_bytes == b"[]"


BASE = prepare_defaults.NETWORKS["base-mainnet"]
ROBINHOOD = prepare_defaults.NETWORKS["robinhood-mainnet"]


def _manifest(*, mc_abi=MC_ABI, ledger_abi=None) -> bytes:
    contracts = json.loads(MANIFEST_BYTES)["contracts"]
    contracts["MissionControl"] = {"address": MC, "abi": mc_abi}
    if ledger_abi is None:
        ledger_abi = LEDGER_ABI
    contracts["Ledger"] = {"address": LEDGER, "abi": ledger_abi}
    return json.dumps(
        {"contracts": contracts}, sort_keys=True, separators=(",", ":")
    ).encode()


def test_every_shipped_network_points_at_its_own_chain_and_manifest():
    assert {n.chain_id for n in prepare_defaults.NETWORKS.values()} == {4663, 8453}
    for network in prepare_defaults.NETWORKS.values():
        assert network.manifest_path.exists(), network.key
        assert network.target_path.suffix == ".vy"
        # A snapshot must never be written over the launch defaults.
        assert network.target_path.name != network.launch_defaults
    assert BASE.chain_id == 8453
    assert BASE.rpc_env == "BASE_MAINNET_RPC_URL"
    assert BASE.target_path.name == "DefaultsBaseLive.vy"


def test_wrong_chain_names_the_network_that_was_asked_for():
    # Base RPC URL pointed at the Robinhood chain, or any other mix-up.
    eth = FakeEth(chain_id=ROBINHOOD.chain_id)

    with pytest.raises(prepare_defaults.SnapshotError, match="expected Base chain id 8453"):
        prepare_defaults.select_snapshot(
            FakeWeb3(eth),
            MC,
            LEDGER,
            block_number=BLOCK_NUMBER,
            manifest_bytes=MANIFEST_BYTES,
            generator_bytes=GENERATOR_BYTES,
            abi_inputs=ABI_INPUTS,
            network=BASE,
        )

    assert not eth.block_reads
    assert not eth.code_reads


@pytest.mark.parametrize(
    ("manifest_bytes", "error"),
    [
        # MissionControl has gained getters since the live deployments were
        # cut, so a drifted getter must fail rather than mis-decode.
        (
            _manifest(mc_abi=[e for e in MC_ABI if e["name"] != "assetConfig"]),
            "deployed MissionControl has no assetConfig getter",
        ),
        (
            _manifest(
                mc_abi=[
                    e
                    if e["name"] != "numAssets"
                    else {**e, "outputs": [{"type": "uint128"}]}
                    for e in MC_ABI
                ]
            ),
            "deployed MissionControl.numAssets does not match",
        ),
        (
            _manifest(ledger_abi=[e for e in LEDGER_ABI if e["name"] != "ripeAvailForHr"]),
            "deployed Ledger has no ripeAvailForHr getter",
        ),
        (_manifest(mc_abi="not-a-list"), "missing the deployed MissionControl ABI"),
    ],
)
def test_deployed_abi_drift_fails_before_provider_reads(manifest_bytes, error):
    eth = FakeEth()

    with pytest.raises(prepare_defaults.SnapshotError, match=error):
        prepare_defaults.select_snapshot(
            FakeWeb3(eth),
            MC,
            LEDGER,
            block_number=BLOCK_NUMBER,
            manifest_bytes=manifest_bytes,
            generator_bytes=GENERATOR_BYTES,
            abi_inputs=ABI_INPUTS,
        )

    assert not eth.block_reads
    assert not eth.code_reads


def test_live_state_that_outgrew_a_defaults_cap_fails_closed(monkeypatch):
    # 59 registered assets cannot be expressed in DynArray[..., 50].
    monkeypatch.setitem(MC_VALUES, "numAssets", 60)
    monkeypatch.setitem(MC_VALUES, "assets", lambda index: f"0x{index:040x}")

    with pytest.raises(
        prepare_defaults.SnapshotError,
        match="live assetConfigs holds 59 entries but Defaults caps it at 50",
    ):
        _snapshot_and_source(FakeEth())


def test_require_cap_admits_exactly_the_declared_bound():
    for name, cap in prepare_defaults.DEFAULTS_CAPS.items():
        prepare_defaults._require_cap(name, cap)
        with pytest.raises(prepare_defaults.SnapshotError, match=name):
            prepare_defaults._require_cap(name, cap + 1)


def test_a_snapshot_cannot_be_rebuilt_as_another_network():
    snapshot, _ = _snapshot_and_source(FakeEth())

    with pytest.raises(prepare_defaults.SnapshotError, match="network does not match"):
        prepare_defaults.build(
            FakeWeb3(FakeEth()),
            MC,
            LEDGER,
            snapshot,
            manifest_bytes=MANIFEST_BYTES,
            abi_inputs=ABI_INPUTS,
            network=BASE,
        )

    with pytest.raises(prepare_defaults.SnapshotError, match="network does not match"):
        snapshot.header(BASE)


def test_coverage_report_names_what_defaults_cannot_carry():
    eth = FakeEth()
    w3 = FakeWeb3(eth)
    snapshot = prepare_defaults.select_snapshot(
        w3,
        MC,
        LEDGER,
        block_number=BLOCK_NUMBER,
        manifest_bytes=MANIFEST_BYTES,
        generator_bytes=GENERATOR_BYTES,
        abi_inputs=ABI_INPUTS,
    )
    result = prepare_defaults.build(
        w3,
        MC,
        LEDGER,
        snapshot,
        manifest_bytes=MANIFEST_BYTES,
        abi_inputs=ABI_INPUTS,
    )

    assert result.counts == {
        "assetConfigs": 1,
        "ripeGovVaultConfigs": 0,
        "priorityLiqAssetVaults": 1,
        "priorityStabVaults": 0,
        "priorityPriceSourceIds": 2,
        "liteSigners": 1,
    }
    report = result.coverage_report(ROBINHOOD)
    assert "userConfig" in report and "userDelegation" in report
    assert "preferredStabVaultId = 1, coreRipeGovVaultId = 2" in report
    assert "assetConfigs: 1" in report


def test_generated_source_warns_that_user_state_is_not_carried():
    _, source = _snapshot_and_source(FakeEth())

    assert "userConfig and" in source
    assert "does NOT survive the redeploy" in source
