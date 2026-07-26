import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import boa
import pytest
from eth_abi import encode
from eth_account import Account
from eth_utils import keccak, to_checksum_address

from scripts.export_abis import export_abis
from scripts.probes import action_block_identity_probe as runner
from scripts.probes.action_block_identity_probe import (
    ARB_SYS,
    OBSERVED_EVENT_TOPIC,
    ApprovalError,
    _decode_observation,
    _predict_create_address,
    _transaction,
    analyze_observations,
    compile_probe_artifacts,
    local_dry_run,
    parse_approval,
    preflight,
)
from scripts.utils.migration_helpers import load_vyper_files


PROBE_PATH = "contracts/testing/ActionBlockIdentityProbe.vy"
RPC_URL = "https://approved.invalid"
SIGNER = to_checksum_address("0x0000000000000000000000000000000000000a11")
MAINNET_PUBLIC_RPC = "https://rpc.mainnet.chain.robinhood.com"
FORK_PINS = [
    (100, "0x" + "11" * 32),
    (101, "0x" + "22" * 32),
]


def _install_compatible_arb_sys():
    implementation = boa.loads(
        """# @version 0.4.3
@view
@external
def arbBlockNumber() -> uint256:
    return block.number
""",
        name="compatible_arb_sys",
    )
    boa.env.set_code(ARB_SYS, boa.env.get_code(implementation.address))


def _install_incompatible_arb_sys():
    implementation = boa.loads(
        """# @version 0.4.3
@view
@external
def wrongBlockNumber() -> uint256:
    return block.number
""",
        name="incompatible_arb_sys",
    )
    boa.env.set_code(ARB_SYS, boa.env.get_code(implementation.address))


def _install_failure(kind):
    if kind == "missing":
        boa.env.set_code(ARB_SYS, b"")
    elif kind == "reverting":
        boa.env.set_code(ARB_SYS, bytes.fromhex("60006000fd"))
    elif kind == "malformed":
        # Return one byte, which cannot decode as the required uint256 ABI.
        boa.env.set_code(ARB_SYS, bytes.fromhex("600160005360016000f3"))
    else:
        assert kind == "incompatible"
        _install_incompatible_arb_sys()


def _approval_data():
    artifacts = compile_probe_artifacts()
    nonce = 0
    max_fee_per_gas = 10
    deployment_gas_limit = 500_000
    observation_gas_limit = 100_000
    observation_count = 4
    worst_case = (
        deployment_gas_limit + observation_gas_limit * observation_count
    ) * max_fee_per_gas
    return {
        "schema_version": 2,
        "scope": "robinhood-testnet-action-block-proof",
        "network": "Robinhood Chain testnet",
        "chain_id": 46630,
        "robinhood_published_arb_os_profile": 61,
        "expected_arb_sys_arb_os_version_return": 116,
        "live_testnet_approved": True,
        "owner_approval_reference": "unit-test-owner-approval",
        "approval_provenance": {
            "owner": {
                "approved": True,
                "decision_date": "2026-07-25",
                "reference": "unit-test-owner-approval",
            },
            "independent_security": {
                "approved": True,
                "decision_date": "2026-07-25",
                "reference": "unit-test-security-approval",
            },
            "deployment": {
                "approved": True,
                "decision_date": "2026-07-25",
                "reference": "unit-test-deployment-approval",
            },
        },
        "rpc": {
            "approved": True,
            "label": "unit-test-rpc",
            "url_environment_variable": "ROBINHOOD_TESTNET_RPC_URL",
            "url_sha256": (
                "0x" + hashlib.sha256(RPC_URL.encode("utf-8")).hexdigest()
            ),
        },
        "signer": {
            "approved": True,
            "funding_approved": True,
            "address": SIGNER,
            "private_key_environment_variable": "ROBINHOOD_TESTNET_PRIVATE_KEY",
            "expected_nonce": nonce,
        },
        "probe": {
            "expected_address": _predict_create_address(SIGNER, nonce),
            "source_sha256": runner.EXPECTED_PROBE_SOURCE_SHA256,
            "abi_sha256": runner.EXPECTED_PROBE_ABI_SHA256,
            "compiler_inputs_sha256": (
                runner.EXPECTED_PROBE_COMPILER_INPUTS_SHA256
            ),
            "creation_bytecode_keccak256": (
                artifacts.creation_bytecode_keccak256
            ),
            "runtime_bytecode_keccak256": artifacts.runtime_bytecode_keccak256,
            "arb_sys_address": ARB_SYS,
            "arb_block_number_selector": runner.ARB_BLOCK_SELECTOR,
            "arb_os_version_selector": runner.ARB_OS_VERSION_SELECTOR,
        },
        "fees": {
            "owner_approved": True,
            "deployment_gas_limit": deployment_gas_limit,
            "observation_gas_limit": observation_gas_limit,
            "max_fee_per_gas_wei": max_fee_per_gas,
            "max_priority_fee_per_gas_wei": 1,
            "max_total_fee_wei": worst_case,
        },
        "execution": {
            "max_observation_transactions": observation_count,
            "receipt_timeout_seconds": 30,
            "topology_cases": list(runner.REQUIRED_TOPOLOGY_CASES),
            "stop_on_inconclusive_bound": True,
            "native_value_wei": 0,
            "token_transfer": False,
        },
        "source_pins": {
            "evidence_date": runner.SOURCE_PIN_DATE,
            "robinhood_node_image": runner.ROBINHOOD_NODE_IMAGE,
            "nitro_commit": runner.NITRO_COMMIT,
            "arb_sys_interface_commit": runner.ARB_SYS_INTERFACE_COMMIT,
            "pinned_nitro_arb_sys_version_offset": (
                runner.PINNED_NITRO_ARB_SYS_VERSION_OFFSET
            ),
            "version_return_derivation": (
                runner.ARB_SYS_VERSION_RETURN_DERIVATION
            ),
        },
    }


def _successful_preflight_rpc(
    approved,
    *,
    pending_nonce=None,
    predicted_address_code="0x",
    signer_balance=None,
):
    nonce = approved.expected_nonce if pending_nonce is None else pending_nonce
    balance = (
        approved.max_total_fee_wei
        if signer_balance is None
        else signer_balance
    )

    def fake_rpc(_rpc_url, method, params):
        assert _rpc_url == RPC_URL
        if method == "eth_chainId":
            return hex(46630)
        if method == "web3_clientVersion":
            return "unit-test-client"
        if method == "eth_getBlockByNumber":
            return {
                "number": hex(123),
                "hash": "0x" + "12" * 32,
                "timestamp": hex(1_700_000_000),
                "baseFeePerGas": hex(1),
            }
        if method == "eth_call":
            assert params[0]["to"] == ARB_SYS
            assert params[0]["value"] == "0x0"
            if params[0]["data"] == runner.ARB_BLOCK_SELECTOR:
                return "0x" + (123).to_bytes(32, "big").hex()
            assert params[0]["data"] == runner.ARB_OS_VERSION_SELECTOR
            return "0x" + (116).to_bytes(32, "big").hex()
        if method == "eth_getTransactionCount":
            return hex(nonce)
        if method == "eth_getCode":
            return predicted_address_code
        if method == "eth_getBalance":
            return hex(balance)
        if method == "eth_estimateGas":
            assert params[0]["value"] == "0x0"
            return hex(approved.deployment_gas_limit - 1)
        raise AssertionError(method)

    return fake_rpc


def _successful_fork_rpc(**overrides):
    states = {
        100: {
            "number": hex(100),
            "hash": FORK_PINS[0][1],
            "parentHash": "0x" + "00" * 32,
            "timestamp": hex(1_700_000_000),
            "l1BlockNumber": hex(50),
        },
        101: {
            "number": hex(101),
            "hash": FORK_PINS[1][1],
            "parentHash": FORK_PINS[0][1],
            "timestamp": hex(1_700_000_001),
            "l1BlockNumber": hex(50),
        },
    }
    for number, changes in overrides.get("state_overrides", {}).items():
        states[number].update(changes)
    state_results = overrides.get("state_results", {})

    def fake_rpc(_rpc_url, method, params):
        assert _rpc_url == MAINNET_PUBLIC_RPC
        if method == "eth_chainId":
            return hex(
                overrides.get(
                    "chain_id",
                    runner.ROBINHOOD_MAINNET_CHAIN_ID,
                )
            )
        if method == "web3_clientVersion":
            return "unit-test-public-client"
        if method == "eth_getBlockByNumber":
            number = int(params[0], 16)
            if number in state_results:
                return state_results[number]
            return states[number]
        number = int(params[-1], 16)
        if method == "eth_getCode":
            return overrides.get("code", "0xfe")
        assert method == "eth_call"
        selector = params[0]["data"]
        if selector == overrides.get("revert_selector"):
            raise ApprovalError("simulated pinned ArbSys reversion")
        if selector == runner.ARB_BLOCK_SELECTOR:
            if "action_raw" in overrides:
                return overrides["action_raw"]
            action = number + overrides.get("action_offset", 0)
            return "0x" + action.to_bytes(32, "big").hex()
        assert selector == runner.ARB_OS_VERSION_SELECTOR
        if "version_raw" in overrides:
            return overrides["version_raw"]
        version = overrides.get(
            "version",
            runner.EXPECTED_ARB_SYS_ARB_OS_VERSION_RETURN,
        )
        return "0x" + version.to_bytes(32, "big").hex()

    return fake_rpc


def _observation(
    observation_id,
    transaction_hash,
    child_block,
    native_block,
):
    return {
        "observation_id": observation_id,
        "transaction_hash": transaction_hash,
        "receipt_block_number": child_block,
        "receipt_block_timestamp": 1_700_000_000 + child_block,
        "native_block_number": native_block,
        "arb_block_number": child_block,
        "contract_observed_at": 1_700_000_000 + child_block,
        "gas_used": 25_000,
        "effective_gas_price_wei": 1,
        "fee_paid_wei": 25_000,
    }


def test_probe_emits_native_and_arb_sys_values_from_compatible_double():
    _install_compatible_arb_sys()
    probe = boa.load(PROBE_PATH)

    native_view, arb_view = probe.readActionBlocks()
    assert native_view == boa.env.evm.patch.block_number
    assert arb_view == boa.env.evm.patch.block_number

    native_observed, arb_observed = probe.observe(7)
    assert native_observed == boa.env.evm.patch.block_number
    assert arb_observed == boa.env.evm.patch.block_number

    events = [
        event
        for event in probe.get_logs()
        if type(event).__name__ == "ActionBlockObserved"
    ]
    assert len(events) == 1
    assert events[0].observationId == 7
    assert events[0].nativeBlockNumber == native_observed
    assert events[0].arbBlockNumber == arb_observed


@pytest.mark.parametrize(
    "failure_kind",
    ["missing", "reverting", "malformed", "incompatible"],
)
def test_constructor_fails_closed_for_invalid_arb_sys(failure_kind):
    _install_failure(failure_kind)
    with boa.reverts():
        boa.load(PROBE_PATH)


@pytest.mark.parametrize(
    "failure_kind",
    ["missing", "reverting", "malformed", "incompatible"],
)
def test_observation_fails_closed_without_native_fallback(failure_kind):
    _install_compatible_arb_sys()
    probe = boa.load(PROBE_PATH)

    _install_failure(failure_kind)
    with boa.reverts():
        probe.observe(1)

    assert not [
        event
        for event in probe.get_logs()
        if type(event).__name__ == "ActionBlockObserved"
    ]


def test_local_dry_run_is_secret_free_and_non_networked():
    report = local_dry_run()
    serialized = json.dumps(report, sort_keys=True)

    assert report["mode"] == "local-dry-run"
    assert report["broadcast_enabled"] is False
    assert report["rpc_contacted"] is False
    assert report["rpc_endpoint_read"] is False
    assert report["signing_secret_read"] is False
    assert report["required_chain_id"] == 46630
    assert report["arb_sys"]["address"] == ARB_SYS
    assert "private_key" not in serialized.lower()
    assert "rpc_url" not in serialized.lower()
    assert report["arb_sys"]["robinhood_published_arb_os_profile"] == 61
    assert report["arb_sys"]["pinned_nitro_arb_sys_version_offset"] == 55
    assert (
        report["arb_sys"][
            "required_approved_arb_sys_arb_os_version_return"
        ]
        == 116
    )
    assert report["arb_sys"]["version_return_derivation"] == "61 + 55 = 116"
    assert len(report["pending_approvals"]) == 8


def test_fork_evidence_uses_pins_without_live_approval_or_signer(monkeypatch):
    monkeypatch.setattr(runner, "_rpc", _successful_fork_rpc())

    def fake_fork(_rpc_url, network, snapshot):
        return {
            "boa_chain_id": network.chain_id,
            "boa_visible_native_number": snapshot["number"],
            "rpc_l1_number": snapshot["rpc_l1_number"],
            "same_pinned_identity_equal": True,
            "actions": [
                {"action_identity": snapshot["arb_sys"]["arb_block_number"]},
                {"action_identity": snapshot["arb_sys"]["arb_block_number"]},
            ],
        }

    monkeypatch.setattr(runner, "_exercise_pinned_fork", fake_fork)
    report = runner.collect_fork_evidence(
        "robinhood-mainnet",
        MAINNET_PUBLIC_RPC,
        FORK_PINS,
    )
    serialized = json.dumps(report, sort_keys=True)

    assert report["mode"] == "credential-free-pinned-fork-evidence"
    assert report["chain_id"] == runner.ROBINHOOD_MAINNET_CHAIN_ID
    assert report["broadcast_enabled"] is False
    assert report["approval_packet_read"] is False
    assert report["signing_secret_read"] is False
    assert report["signer_used"] is False
    assert report["relationships"]["parent_child_pair"] is True
    assert report["relationships"]["same_pinned_action_identity_equal"] is True
    assert report["relationships"]["advanced_action_identity_different"] is True
    assert report["relationships"]["shared_rpc_l1_number"] is True
    assert report["pinned_states"][0]["arb_sys"]["observed_raw_version"] == 116
    assert report["pinned_states"][0]["arb_sys"]["code_hex"] == "0xfe"
    assert report["provider"]["client_version_queried"] is False
    assert "private_key" not in serialized.lower()
    assert MAINNET_PUBLIC_RPC not in serialized
    assert report["row_2_closed"] is False
    assert report["stage_b_authorized"] is False


def test_fork_controlled_actions_hold_same_identity_then_advance():
    runner._install_fork_arb_sys_double(
        100,
        runner.EXPECTED_ARB_SYS_ARB_OS_VERSION_RETURN,
    )
    probe = boa.load(PROBE_PATH)
    _, first = probe.observe(1)
    _, second = probe.observe(2)
    assert first == second == 100

    runner._install_fork_arb_sys_double(
        101,
        runner.EXPECTED_ARB_SYS_ARB_OS_VERSION_RETURN,
    )
    _, advanced = probe.observe(3)
    assert advanced == 101
    assert advanced != first


def test_fork_rejects_nonofficial_endpoint_before_rpc(monkeypatch):
    called = False

    def unexpected_rpc(*_args):
        nonlocal called
        called = True
        raise AssertionError("RPC must not be called")

    monkeypatch.setattr(runner, "_rpc", unexpected_rpc)
    with pytest.raises(ApprovalError, match="credential-free official"):
        runner.collect_fork_evidence(
            "robinhood-mainnet",
            "https://wrong.invalid",
            FORK_PINS,
        )
    assert called is False


def test_fork_rejects_wrong_endpoint_chain_before_snapshot(monkeypatch):
    monkeypatch.setattr(
        runner,
        "_rpc",
        _successful_fork_rpc(chain_id=1),
    )
    monkeypatch.setattr(
        runner,
        "_exercise_pinned_fork",
        lambda *_args: pytest.fail("local fork must not run"),
    )
    with pytest.raises(ApprovalError, match="chain identity mismatch"):
        runner.collect_fork_evidence(
            "robinhood-mainnet",
            MAINNET_PUBLIC_RPC,
            FORK_PINS,
        )


@pytest.mark.parametrize(
    ("state_result", "error_match"),
    [
        (None, "pinned fork state is unavailable"),
        ({"number": "not-hex"}, "pinned state number is not a hex quantity"),
        (
            {"number": "0xzz"},
            "pinned state number is a malformed hex quantity",
        ),
    ],
)
def test_fork_rejects_unavailable_or_malformed_pinned_block_before_local_fork(
    monkeypatch,
    state_result,
    error_match,
):
    monkeypatch.setattr(
        runner,
        "_rpc",
        _successful_fork_rpc(state_results={100: state_result}),
    )
    monkeypatch.setattr(
        runner,
        "_exercise_pinned_fork",
        lambda *_args: pytest.fail("local fork must not run"),
    )
    with pytest.raises(ApprovalError, match=error_match):
        runner.collect_fork_evidence(
            "robinhood-mainnet",
            MAINNET_PUBLIC_RPC,
            FORK_PINS,
        )


@pytest.mark.parametrize(
    ("state_overrides", "error_match"),
    [
        ({100: {"number": hex(99)}}, "pinned fork state number mismatch"),
        (
            {100: {"hash": "0x" + "44" * 32}},
            "pinned fork state hash mismatch",
        ),
    ],
)
def test_fork_rejects_wrong_pinned_number_or_hash_before_local_fork(
    monkeypatch,
    state_overrides,
    error_match,
):
    monkeypatch.setattr(
        runner,
        "_rpc",
        _successful_fork_rpc(state_overrides=state_overrides),
    )
    monkeypatch.setattr(
        runner,
        "_exercise_pinned_fork",
        lambda *_args: pytest.fail("local fork must not run"),
    )
    with pytest.raises(ApprovalError, match=error_match):
        runner.collect_fork_evidence(
            "robinhood-mainnet",
            MAINNET_PUBLIC_RPC,
            FORK_PINS,
        )


def test_fork_rejects_nonconsecutive_pins_before_artifact_or_rpc_access(
    monkeypatch,
):
    monkeypatch.setattr(
        runner,
        "compile_probe_artifacts",
        lambda: pytest.fail("artifacts must not be compiled"),
    )
    monkeypatch.setattr(
        runner,
        "_rpc",
        lambda *_args: pytest.fail("RPC must not be called"),
    )
    with pytest.raises(ApprovalError, match="states must be consecutive"):
        runner.collect_fork_evidence(
            "robinhood-mainnet",
            MAINNET_PUBLIC_RPC,
            [
                FORK_PINS[0],
                (102, FORK_PINS[1][1]),
            ],
        )


def test_fork_rejects_parent_child_hash_mismatch_before_local_fork(monkeypatch):
    monkeypatch.setattr(
        runner,
        "_rpc",
        _successful_fork_rpc(
            state_overrides={
                101: {"parentHash": "0x" + "55" * 32},
            }
        ),
    )
    monkeypatch.setattr(
        runner,
        "_exercise_pinned_fork",
        lambda *_args: pytest.fail("local fork must not run"),
    )
    with pytest.raises(ApprovalError, match="not a parent-child pair"):
        runner.collect_fork_evidence(
            "robinhood-mainnet",
            MAINNET_PUBLIC_RPC,
            FORK_PINS,
        )


def test_fork_rejects_differing_provider_l1_number_before_local_fork(monkeypatch):
    monkeypatch.setattr(
        runner,
        "_rpc",
        _successful_fork_rpc(
            state_overrides={
                101: {"l1BlockNumber": hex(51)},
            }
        ),
    )
    monkeypatch.setattr(
        runner,
        "_exercise_pinned_fork",
        lambda *_args: pytest.fail("local fork must not run"),
    )
    with pytest.raises(ApprovalError, match="does not share one provider"):
        runner.collect_fork_evidence(
            "robinhood-mainnet",
            MAINNET_PUBLIC_RPC,
            FORK_PINS,
        )


def test_fork_rejects_false_same_pinned_state_result_before_completion(
    monkeypatch,
):
    monkeypatch.setattr(runner, "_rpc", _successful_fork_rpc())

    def false_same_identity(_rpc_url, network, snapshot):
        return {
            "boa_chain_id": network.chain_id,
            "boa_visible_native_number": snapshot["number"],
            "rpc_l1_number": snapshot["rpc_l1_number"],
            "same_pinned_identity_equal": False,
        }

    monkeypatch.setattr(
        runner,
        "_exercise_pinned_fork",
        false_same_identity,
    )
    with pytest.raises(
        ApprovalError,
        match="same pinned identity equality evidence failed",
    ):
        runner.collect_fork_evidence(
            "robinhood-mainnet",
            MAINNET_PUBLIC_RPC,
            FORK_PINS,
        )


@pytest.mark.parametrize(
    ("overrides", "error_match"),
    [
        ({"code": "0x"}, "code identity mismatch or missing code"),
        ({"code": "0x60"}, "code identity mismatch or missing code"),
        (
            {"revert_selector": runner.ARB_BLOCK_SELECTOR},
            "simulated pinned ArbSys reversion",
        ),
        ({"action_raw": "0x01"}, "incompatible ABI length"),
        ({"version_raw": "0x01"}, "incompatible ABI length"),
        (
            {"action_raw": "0x" + "00" * 31 + "zz"},
            "malformed hex data",
        ),
        (
            {"version_raw": "0x" + "00" * 31 + "zz"},
            "malformed hex data",
        ),
        ({"version": 61}, "version disagrees"),
        ({"version": 117}, "version disagrees"),
        ({"action_offset": 1}, "action identity disagrees"),
    ],
)
def test_fork_snapshot_failures_stop_before_local_fork(
    monkeypatch,
    overrides,
    error_match,
):
    monkeypatch.setattr(runner, "_rpc", _successful_fork_rpc(**overrides))
    monkeypatch.setattr(
        runner,
        "_exercise_pinned_fork",
        lambda *_args: pytest.fail("local fork must not run"),
    )
    with pytest.raises(ApprovalError, match=error_match):
        runner.collect_fork_evidence(
            "robinhood-mainnet",
            MAINNET_PUBLIC_RPC,
            FORK_PINS,
        )


def test_approval_parser_requires_every_explicit_authorization():
    valid = _approval_data()
    approved = parse_approval(valid)
    assert approved.chain_id == 46630
    assert approved.robinhood_published_arb_os_profile == 61
    assert approved.expected_arb_sys_arb_os_version_return == 116
    assert approved.max_observation_transactions == 4
    assert approved.max_transaction_count == 5
    assert approved.worst_case_total_fee_wei == approved.max_total_fee_wei
    assert approved.owner_approval_reference == "unit-test-owner-approval"
    assert approved.security_approval_reference == "unit-test-security-approval"
    assert (
        approved.deployment_approval_reference
        == "unit-test-deployment-approval"
    )

    cases = [
        ("live_testnet_approved",),
        ("approval_provenance", "owner", "approved"),
        ("approval_provenance", "independent_security", "approved"),
        ("approval_provenance", "deployment", "approved"),
        ("rpc", "approved"),
        ("signer", "approved"),
        ("signer", "funding_approved"),
        ("fees", "owner_approved"),
    ]
    for path in cases:
        invalid = copy.deepcopy(valid)
        target = invalid
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = False
        with pytest.raises(ApprovalError):
            parse_approval(invalid)


@pytest.mark.parametrize(
    ("role", "field", "value", "error_match"),
    [
        ("owner", "decision_date", None, "must be nonempty"),
        ("owner", "decision_date", "07/25/2026", "YYYY-MM-DD"),
        ("owner", "reference", None, "must be nonempty"),
        ("independent_security", "decision_date", None, "must be nonempty"),
        ("independent_security", "reference", None, "must be nonempty"),
        ("deployment", "decision_date", None, "must be nonempty"),
        ("deployment", "reference", None, "must be nonempty"),
    ],
)
def test_approval_parser_requires_dated_provenance_references(
    role,
    field,
    value,
    error_match,
):
    invalid = _approval_data()
    invalid["approval_provenance"][role][field] = value
    with pytest.raises(ApprovalError, match=error_match):
        parse_approval(invalid)


def test_owner_reference_must_match_owner_provenance():
    invalid = _approval_data()
    invalid["owner_approval_reference"] = "different-owner-reference"
    with pytest.raises(ApprovalError, match="owner provenance reference"):
        parse_approval(invalid)


@pytest.mark.parametrize(
    "field",
    [
        "source_sha256",
        "abi_sha256",
        "compiler_inputs_sha256",
        "creation_bytecode_keccak256",
        "runtime_bytecode_keccak256",
    ],
)
@pytest.mark.parametrize(
    ("value", "error_match"),
    [
        ("0x1234", "invalid lowercase"),
        ("0x" + "A" * 64, "invalid lowercase"),
    ],
)
def test_approval_parser_rejects_malformed_or_nonlowercase_artifact_hashes(
    field,
    value,
    error_match,
):
    invalid = _approval_data()
    invalid["probe"][field] = value
    with pytest.raises(ApprovalError, match=error_match):
        parse_approval(invalid)


@pytest.mark.parametrize(
    ("path", "value", "error_match"),
    [
        (
            ("probe", "source_sha256"),
            "0x" + "00" * 32,
            "probe.source_sha256",
        ),
        (
            ("probe", "abi_sha256"),
            "0x" + "00" * 32,
            "probe.abi_sha256",
        ),
        (
            ("probe", "compiler_inputs_sha256"),
            "0x" + "00" * 32,
            "probe.compiler_inputs_sha256",
        ),
        (
            ("probe", "creation_bytecode_keccak256"),
            "0x" + "00" * 32,
            "probe.creation_bytecode_keccak256",
        ),
        (
            ("probe", "runtime_bytecode_keccak256"),
            "0x" + "00" * 32,
            "probe.runtime_bytecode_keccak256",
        ),
        (
            ("probe", "arb_sys_address"),
            "0x0000000000000000000000000000000000000001",
            "probe.arb_sys_address",
        ),
        (
            ("probe", "arb_block_number_selector"),
            "0x00000000",
            "probe.arb_block_number_selector",
        ),
        (
            ("probe", "arb_os_version_selector"),
            "0x00000000",
            "probe.arb_os_version_selector",
        ),
        (
            ("source_pins", "evidence_date"),
            "2026-07-23",
            "source_pins.evidence_date",
        ),
        (
            ("source_pins", "robinhood_node_image"),
            "wrong-image",
            "source_pins.robinhood_node_image",
        ),
        (
            ("source_pins", "nitro_commit"),
            "0" * 40,
            "source_pins.nitro_commit",
        ),
        (
            ("source_pins", "arb_sys_interface_commit"),
            "0" * 40,
            "source_pins.arb_sys_interface_commit",
        ),
        (
            ("source_pins", "pinned_nitro_arb_sys_version_offset"),
            54,
            "source_pins.pinned_nitro_arb_sys_version_offset",
        ),
        (
            ("source_pins", "version_return_derivation"),
            "61 + 54 = 115",
            "source_pins.version_return_derivation",
        ),
        (
            ("execution", "topology_cases"),
            [],
            "execution.topology_cases",
        ),
        (
            ("execution", "stop_on_inconclusive_bound"),
            False,
            "execution.stop_on_inconclusive_bound",
        ),
        (
            ("execution", "native_value_wei"),
            1,
            "execution.native_value_wei",
        ),
        (
            ("execution", "token_transfer"),
            True,
            "execution.token_transfer",
        ),
    ],
)
def test_approval_parser_rejects_reviewed_packet_fact_mismatches(
    path,
    value,
    error_match,
):
    invalid = _approval_data()
    invalid[path[0]][path[1]] = value
    with pytest.raises(ApprovalError, match=error_match):
        parse_approval(invalid)


def test_approval_parser_rejects_wrong_chain_address_and_fee_bound():
    valid = _approval_data()

    wrong_chain = copy.deepcopy(valid)
    wrong_chain["chain_id"] = 4663
    with pytest.raises(ApprovalError, match="46630"):
        parse_approval(wrong_chain)

    wrong_address = copy.deepcopy(valid)
    wrong_address["probe"]["expected_address"] = (
        "0x0000000000000000000000000000000000000001"
    )
    with pytest.raises(ApprovalError, match="do not predict"):
        parse_approval(wrong_address)

    excessive_fee = copy.deepcopy(valid)
    excessive_fee["fees"]["max_total_fee_wei"] -= 1
    with pytest.raises(ApprovalError, match="exceed total fee cap"):
        parse_approval(excessive_fee)

    wrong_profile = copy.deepcopy(valid)
    wrong_profile["robinhood_published_arb_os_profile"] = 62
    with pytest.raises(ApprovalError, match="pinned profile 61"):
        parse_approval(wrong_profile)

    raw_profile_value = copy.deepcopy(valid)
    raw_profile_value["expected_arb_sys_arb_os_version_return"] = 61
    with pytest.raises(ApprovalError, match="pinned Nitro offset 55"):
        parse_approval(raw_profile_value)

    incompatible_return = copy.deepcopy(valid)
    incompatible_return["expected_arb_sys_arb_os_version_return"] = 117
    with pytest.raises(ApprovalError, match="pinned Nitro offset 55"):
        parse_approval(incompatible_return)


def test_transaction_builder_hardcodes_zero_value_and_testnet_chain():
    approved = parse_approval(_approval_data())
    transaction = _transaction(
        approved,
        nonce=approved.expected_nonce,
        gas=approved.deployment_gas_limit,
        data="0x1234",
    )

    assert transaction["chainId"] == 46630
    assert transaction["value"] == 0
    assert "to" not in transaction


def test_ambiguous_rpc_failure_cannot_hide_prebroadcast_journal(
    monkeypatch,
    tmp_path,
):
    approved = parse_approval(_approval_data())
    ephemeral_signer = Account.create()
    output = tmp_path / "progress.json"
    report = {"result": "test", "signed_transactions": []}
    transaction = _transaction(
        approved,
        nonce=approved.expected_nonce,
        gas=approved.deployment_gas_limit,
        data="0x1234",
    )

    def ambiguous_after_possible_acceptance(_rpc_url, method, params):
        assert method == "eth_sendRawTransaction"
        persisted = json.loads(output.read_text())
        assert len(persisted["signed_transactions"]) == 1
        entry = persisted["signed_transactions"][0]
        raw_transaction = bytes.fromhex(params[0][2:])
        assert entry["transaction_hash"] == "0x" + keccak(raw_transaction).hex()
        assert entry["nonce"] == approved.expected_nonce
        assert entry["intended_action"] == "deploy-probe"
        assert entry["broadcast_status"] == (
            "signed-and-persisted-before-broadcast"
        )
        raise ApprovalError("simulated ambiguous RPC failure")

    monkeypatch.setattr(runner, "_rpc", ambiguous_after_possible_acceptance)
    with pytest.raises(ApprovalError, match="ambiguous RPC failure"):
        runner._journal_and_broadcast(
            report,
            output,
            RPC_URL,
            transaction,
            ephemeral_signer.key,
            "deploy-probe",
        )

    persisted = json.loads(output.read_text())
    entry = persisted["signed_transactions"][0]
    assert entry["broadcast_status"] == (
        "rpc-error-after-submit-acceptance-ambiguous"
    )
    assert persisted["result"] == "stopped-ambiguous-broadcast-outcome"
    assert ephemeral_signer.key.hex() not in output.read_text()


def test_second_burst_broadcast_failure_preserves_both_transactions(
    monkeypatch,
    tmp_path,
):
    approved = parse_approval(_approval_data())
    ephemeral_signer = Account.create()
    output = tmp_path / "progress.json"
    report = {"result": "test", "signed_transactions": []}
    call_count = 0

    def fail_second_broadcast(_rpc_url, method, params):
        nonlocal call_count
        assert method == "eth_sendRawTransaction"
        call_count += 1
        raw_transaction = bytes.fromhex(params[0][2:])
        local_hash = "0x" + keccak(raw_transaction).hex()
        persisted = json.loads(output.read_text())
        assert len(persisted["signed_transactions"]) == call_count
        if call_count == 1:
            return local_hash
        assert persisted["signed_transactions"][1]["intended_action"] == "observe:1"
        raise ApprovalError("simulated second-burst failure")

    monkeypatch.setattr(runner, "_rpc", fail_second_broadcast)
    first_hash = runner._journal_and_broadcast(
        report,
        output,
        RPC_URL,
        _transaction(
            approved,
            nonce=approved.expected_nonce + 1,
            gas=approved.observation_gas_limit,
            data="0x1234",
            to=approved.expected_probe_address,
        ),
        ephemeral_signer.key,
        "observe:0",
    )
    with pytest.raises(ApprovalError, match="second-burst failure"):
        runner._journal_and_broadcast(
            report,
            output,
            RPC_URL,
            _transaction(
                approved,
                nonce=approved.expected_nonce + 2,
                gas=approved.observation_gas_limit,
                data="0x5678",
                to=approved.expected_probe_address,
            ),
            ephemeral_signer.key,
            "observe:1",
        )

    persisted = json.loads(output.read_text())
    assert len(persisted["signed_transactions"]) == 2
    first, second = persisted["signed_transactions"]
    assert first["transaction_hash"] == first_hash
    assert first["nonce"] == approved.expected_nonce + 1
    assert first["intended_action"] == "observe:0"
    assert first["broadcast_status"] == "rpc-hash-matched"
    assert first["rpc_returned_hash"] == first["transaction_hash"]
    assert second["nonce"] == approved.expected_nonce + 2
    assert second["intended_action"] == "observe:1"
    assert second["broadcast_status"] == (
        "rpc-error-after-submit-acceptance-ambiguous"
    )


def test_rpc_returned_hash_mismatch_is_persisted_and_rejected(
    monkeypatch,
    tmp_path,
):
    approved = parse_approval(_approval_data())
    ephemeral_signer = Account.create()
    output = tmp_path / "progress.json"
    report = {"result": "test", "signed_transactions": []}
    rpc_hash = "0x" + "ff" * 32
    monkeypatch.setattr(runner, "_rpc", lambda *_args: rpc_hash)

    with pytest.raises(ApprovalError, match="locally derived hash"):
        runner._journal_and_broadcast(
            report,
            output,
            RPC_URL,
            _transaction(
                approved,
                nonce=approved.expected_nonce,
                gas=approved.deployment_gas_limit,
                data="0x1234",
            ),
            ephemeral_signer.key,
            "deploy-probe",
        )

    persisted = json.loads(output.read_text())
    entry = persisted["signed_transactions"][0]
    assert entry["rpc_returned_hash"] == rpc_hash
    assert entry["rpc_returned_hash"] != entry["transaction_hash"]
    assert entry["broadcast_status"] == "rpc-returned-hash-mismatch"
    assert persisted["result"] == "stopped-rpc-transaction-hash-mismatch"


def test_mixed_case_rpc_returned_hash_is_normalized_before_exact_match(
    monkeypatch,
    tmp_path,
):
    approved = parse_approval(_approval_data())
    ephemeral_signer = Account.create()
    output = tmp_path / "progress.json"
    report = {"result": "test", "signed_transactions": []}

    def mixed_case_matching_hash(_rpc_url, method, params):
        assert method == "eth_sendRawTransaction"
        raw_transaction = bytes.fromhex(params[0][2:])
        local_hash = keccak(raw_transaction).hex()
        mixed = "".join(
            character.upper() if index % 2 else character.lower()
            for index, character in enumerate(local_hash)
        )
        assert mixed.lower() == local_hash
        assert mixed != local_hash
        return "0x" + mixed

    monkeypatch.setattr(runner, "_rpc", mixed_case_matching_hash)
    transaction_hash = runner._journal_and_broadcast(
        report,
        output,
        RPC_URL,
        _transaction(
            approved,
            nonce=approved.expected_nonce,
            gas=approved.deployment_gas_limit,
            data="0x1234",
        ),
        ephemeral_signer.key,
        "deploy-probe",
    )

    persisted = json.loads(output.read_text())
    entry = persisted["signed_transactions"][0]
    assert transaction_hash == entry["transaction_hash"]
    assert entry["rpc_returned_hash"] == entry["transaction_hash"]
    assert entry["rpc_returned_hash"] == entry["rpc_returned_hash"].lower()
    assert entry["broadcast_status"] == "rpc-hash-matched"


@pytest.mark.parametrize(
    "value",
    [
        None,
        "0x1234",
        "0x" + "gg" * 32,
        "not-hex",
    ],
)
def test_malformed_rpc_runtime_hashes_remain_rejected(value):
    with pytest.raises(ApprovalError, match="invalid RPC/runtime hash"):
        runner._runtime_hash(value, "test RPC hash")


def test_rpc_disables_http_redirects(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {"jsonrpc": "2.0", "id": 1, "result": "0x1"}

    def fake_post(url, **kwargs):
        assert url == RPC_URL
        assert kwargs["allow_redirects"] is False
        assert kwargs["timeout"] == 30
        return FakeResponse()

    monkeypatch.setattr(runner.requests, "post", fake_post)
    assert runner._rpc(RPC_URL, "eth_chainId", []) == "0x1"


def test_rpc_rejects_302_before_parsing_valid_looking_json(monkeypatch):
    json_calls = []

    class FakeResponse:
        status_code = 302

        def json(self):
            json_calls.append(True)
            return {"jsonrpc": "2.0", "id": 1, "result": "0x1"}

    def fake_post(url, **kwargs):
        assert url == RPC_URL
        assert kwargs["allow_redirects"] is False
        return FakeResponse()

    monkeypatch.setattr(runner.requests, "post", fake_post)
    with pytest.raises(ApprovalError, match="non-2xx HTTP status"):
        runner._rpc(RPC_URL, "eth_chainId", [])
    assert json_calls == []


@pytest.mark.parametrize(
    "payload",
    [
        ["not", "an", "object"],
        {"jsonrpc": "1.0", "id": 1, "result": "0x1"},
        {"jsonrpc": "2.0", "id": 2, "result": "0x1"},
    ],
)
def test_rpc_rejects_invalid_json_rpc_envelope(monkeypatch, payload):
    class FakeResponse:
        status_code = 200

        def json(self):
            return payload

    monkeypatch.setattr(
        runner.requests,
        "post",
        lambda *_args, **_kwargs: FakeResponse(),
    )
    with pytest.raises(ApprovalError, match="invalid JSON-RPC envelope"):
        runner._rpc(RPC_URL, "eth_chainId", [])


def test_preflight_matches_endpoint_chain_artifacts_nonce_address_and_fee(monkeypatch):
    approved = parse_approval(_approval_data())
    monkeypatch.setattr(runner, "_rpc", _successful_preflight_rpc(approved))
    report = preflight(approved, RPC_URL)

    assert report["chain_id"] == 46630
    assert report["broadcast_enabled"] is False
    assert report["rpc_endpoint_read"] is True
    assert report["signing_secret_read"] is False
    assert (
        report["arb_sys_preflight"]["robinhood_published_arb_os_profile"]
        == 61
    )
    assert (
        report["arb_sys_preflight"]["pinned_nitro_arb_sys_version_offset"]
        == 55
    )
    assert (
        report["arb_sys_preflight"][
            "expected_arb_sys_arb_os_version_return"
        ]
        == 116
    )
    assert (
        report["arb_sys_preflight"][
            "observed_arb_sys_arb_os_version_return"
        ]
        == 116
    )
    assert (
        report["arb_sys_preflight"]["version_return_derivation"]
        == "61 + 55 = 116"
    )
    assert "not proof" in (
        report["rpc_identity"]["client_version_evidence_limit"]
    )
    assert report["probe"]["predicted_address"] == approved.expected_probe_address
    assert report["probe"]["source_path"] == PROBE_PATH
    assert report["source_pins"]["nitro_commit"] == runner.NITRO_COMMIT
    assert (
        report["approval_provenance"]["owner"]["reference"]
        == approved.owner_approval_reference
    )
    assert (
        report["approval_provenance"]["independent_security"]["reference"]
        == approved.security_approval_reference
    )
    assert (
        report["approval_provenance"]["deployment"]["reference"]
        == approved.deployment_approval_reference
    )
    assert report["ready_for_live_testnet_execution"] is True
    assert RPC_URL not in json.dumps(report)


@pytest.mark.parametrize(
    ("rpc_overrides", "error_match"),
    [
        (
            {"pending_nonce": 1},
            "pending signer nonce mismatch",
        ),
        (
            {"predicted_address_code": "0x6000"},
            "already contains code",
        ),
        (
            {"signer_balance": 1},
            "balance is below the total fee cap",
        ),
    ],
)
def test_preflight_rejects_nonce_code_and_balance_mismatches(
    monkeypatch,
    rpc_overrides,
    error_match,
):
    approved = parse_approval(_approval_data())
    monkeypatch.setattr(
        runner,
        "_rpc",
        _successful_preflight_rpc(approved, **rpc_overrides),
    )

    with pytest.raises(ApprovalError, match=error_match):
        preflight(approved, RPC_URL)


def test_preflight_rejects_wrong_endpoint_before_rpc(monkeypatch):
    approved = parse_approval(_approval_data())
    called = False

    def unexpected_rpc(*_args):
        nonlocal called
        called = True
        raise AssertionError("RPC must not be called")

    monkeypatch.setattr(runner, "_rpc", unexpected_rpc)
    with pytest.raises(ApprovalError, match="endpoint fingerprint"):
        preflight(approved, "https://wrong.invalid")
    assert called is False


def test_preflight_stops_after_wrong_chain_identity(monkeypatch):
    approved = parse_approval(_approval_data())
    methods = []

    def wrong_chain_rpc(_rpc_url, method, _params):
        methods.append(method)
        return hex(4663)

    monkeypatch.setattr(runner, "_rpc", wrong_chain_rpc)
    with pytest.raises(ApprovalError, match="not approved Robinhood testnet"):
        preflight(approved, RPC_URL)
    assert methods == ["eth_chainId"]


@pytest.mark.parametrize(
    ("arb_os_result", "error_match"),
    [
        (61, "approved derived return"),
        (117, "approved derived return"),
        ("malformed", "incompatible ABI length"),
        ("reverting", "simulated ArbSys reversion"),
    ],
)
def test_preflight_stops_on_invalid_arb_sys_arb_os_version_return(
    monkeypatch,
    arb_os_result,
    error_match,
):
    approved = parse_approval(_approval_data())
    methods = []

    def wrong_arb_os_rpc(_rpc_url, method, params):
        methods.append(method)
        if method == "eth_chainId":
            return hex(46630)
        if method == "web3_clientVersion":
            return "observed-client-only"
        if method == "eth_getBlockByNumber":
            return {
                "number": hex(123),
                "hash": "0x" + "12" * 32,
                "timestamp": hex(1_700_000_000),
                "baseFeePerGas": hex(1),
            }
        assert method == "eth_call"
        if params[0]["data"] == runner.ARB_BLOCK_SELECTOR:
            return "0x" + (123).to_bytes(32, "big").hex()
        assert params[0]["data"] == runner.ARB_OS_VERSION_SELECTOR
        if arb_os_result == "malformed":
            return "0x01"
        if arb_os_result == "reverting":
            raise ApprovalError("simulated ArbSys reversion")
        return "0x" + arb_os_result.to_bytes(32, "big").hex()

    monkeypatch.setattr(runner, "_rpc", wrong_arb_os_rpc)
    with pytest.raises(ApprovalError, match=error_match):
        preflight(approved, RPC_URL)
    assert "eth_getTransactionCount" not in methods


def test_live_mode_requires_progress_output_before_rpc_or_secret_read(
    monkeypatch,
    tmp_path,
):
    approval_path = tmp_path / "approval.json"
    approval_path.write_text(json.dumps(_approval_data()))
    monkeypatch.setattr(
        runner.sys,
        "argv",
        [
            "action_block_identity_probe.py",
            "--execute",
            "--confirm-live-testnet",
            "--approval-file",
            str(approval_path),
        ],
    )
    monkeypatch.setattr(
        runner,
        "_rpc_url_from_environment",
        lambda _approved: pytest.fail("RPC URL must not be read without --output"),
    )

    with pytest.raises(ApprovalError, match="requires --output"):
        runner.main()


@pytest.mark.parametrize(
    "mode_args",
    [
        ["--preflight"],
        [
            "--execute",
            "--confirm-live-testnet",
            "--output",
            "sanitized-output.json",
        ],
    ],
)
@pytest.mark.parametrize(
    ("invalidator", "error_match"),
    [
        (
            lambda data: data["probe"].__setitem__(
                "source_sha256",
                "0x" + "A" * 64,
            ),
            "invalid lowercase",
        ),
        (
            lambda data: data["rpc"].__setitem__(
                "url_sha256",
                "0x" + "A" * 64,
            ),
            "invalid lowercase",
        ),
        (
            lambda data: data["approval_provenance"][
                "independent_security"
            ].__setitem__("approved", False),
            "independent_security approval",
        ),
    ],
)
def test_cli_rejects_packet_before_artifact_environment_rpc_or_secret_access(
    monkeypatch,
    tmp_path,
    mode_args,
    invalidator,
    error_match,
):
    approval = _approval_data()
    invalidator(approval)
    approval_path = tmp_path / "approval.json"
    approval_path.write_text(json.dumps(approval))
    monkeypatch.setattr(
        runner.sys,
        "argv",
        [
            "action_block_identity_probe.py",
            *mode_args,
            "--approval-file",
            str(approval_path),
        ],
    )
    monkeypatch.setattr(
        runner,
        "compile_probe_artifacts",
        lambda: pytest.fail("artifacts must not compile before packet rejection"),
    )
    monkeypatch.setattr(
        runner,
        "_rpc_url_from_environment",
        lambda _approved: pytest.fail("RPC endpoint must not be read"),
    )
    monkeypatch.setattr(
        runner,
        "_signing_secret_from_environment",
        lambda _approved: pytest.fail("signing secret must not be read"),
    )

    with pytest.raises(ApprovalError, match=error_match):
        runner.main()


def test_execution_reports_endpoint_and_signing_secret_reads_separately(
    monkeypatch,
    tmp_path,
):
    ephemeral_signer = Account.create()
    approval_data = _approval_data()
    approval_data["signer"]["address"] = ephemeral_signer.address
    approval_data["probe"]["expected_address"] = _predict_create_address(
        ephemeral_signer.address,
        approval_data["signer"]["expected_nonce"],
    )
    approved = parse_approval(approval_data)
    output = tmp_path / "progress.json"
    preflight_completed = False

    def successful_preflight(*_args, **_kwargs):
        nonlocal preflight_completed
        preflight_completed = True
        return {
            "mode": "rpc-preflight",
            "broadcast_enabled": False,
            "rpc_endpoint_read": True,
            "signing_secret_read": False,
            "probe": {},
        }

    monkeypatch.setattr(runner, "preflight", successful_preflight)

    def stop_before_broadcast(report, *_args):
        assert report["rpc_endpoint_read"] is True
        assert report["signing_secret_read"] is True
        persisted = json.loads(output.read_text())
        assert persisted["rpc_endpoint_read"] is True
        assert persisted["signing_secret_read"] is True
        raise ApprovalError("stop before local test broadcast")

    monkeypatch.setattr(runner, "_journal_and_broadcast", stop_before_broadcast)

    def load_signing_secret():
        assert preflight_completed is True
        return ephemeral_signer.key

    with pytest.raises(ApprovalError, match="stop before local test broadcast"):
        runner.execute_live_testnet(
            approved,
            RPC_URL,
            progress_output=output,
            signing_secret_loader=load_signing_secret,
        )


def test_fee_cap_stop_persists_final_result_and_projection(tmp_path):
    output = tmp_path / "progress.json"
    report = {
        "result": "deployment-confirmed",
        "fees": {"actual_total_fee_paid_wei": 40},
    }

    with pytest.raises(
        ApprovalError,
        match="next observation burst would exceed total fee cap",
    ):
        runner._enforce_observation_burst_fee_cap(
            report,
            output,
            actual_fee=40,
            batch_worst_case=20,
            max_total_fee=50,
        )

    persisted = json.loads(output.read_text())
    assert (
        persisted["result"]
        == "stopped-before-observation-burst-total-fee-cap"
    )
    assert persisted["fees"]["next_observation_burst_worst_case_wei"] == 20
    assert persisted["fees"]["projected_total_fee_wei"] == 60


def test_topology_analysis_proves_all_required_relationships():
    observations = [
        _observation(0, "0x01", 100, 50),
        _observation(1, "0x02", 100, 50),
        _observation(2, "0x03", 101, 50),
        _observation(3, "0x04", 102, 51),
    ]
    result = analyze_observations(observations)

    assert result["proof_complete"] is True
    assert result["direct_arb_receipt_agreement"] is True
    assert result["same_child_block_groups"][0]["child_block"] == 100
    assert result["successive_child_block_pairs"]
    repeated = result["successive_child_blocks_with_repeated_native_number"]
    assert repeated[0]["first_child_block"] == 100
    assert repeated[0]["second_child_block"] == 101
    assert "protocol maximum" in result["bounded_observation"]["interpretation"]


def test_topology_analysis_reports_inconclusive_without_fabrication():
    observations = [
        _observation(0, "0x01", 100, 50),
        _observation(1, "0x02", 102, 51),
    ]
    result = analyze_observations(observations)

    assert result["proof_complete"] is False
    assert result["status"] == "inconclusive"
    assert "two separate transactions in one child block" in result["missing_topologies"]
    assert "observations in successive child blocks" in result["missing_topologies"]


def test_receipt_disagreement_is_recorded_for_immediate_hard_stop(monkeypatch):
    expected_probe = "0x0000000000000000000000000000000000000042"
    receipt_block = 100
    receipt = {
        "status": "0x1",
        "transactionHash": "0x" + "ab" * 32,
        "blockNumber": hex(receipt_block),
        "gasUsed": hex(25_000),
        "effectiveGasPrice": hex(2),
        "logs": [
            {
                "address": expected_probe,
                "topics": [OBSERVED_EVENT_TOPIC],
                "data": "0x"
                + encode(
                    ["uint256", "address", "uint256", "uint256", "uint256"],
                    [7, SIGNER, 50, receipt_block + 1, 1_700_000_000],
                ).hex(),
            }
        ],
    }

    monkeypatch.setattr(
        runner,
        "_rpc",
        lambda *_args: {"timestamp": hex(1_700_000_000)},
    )
    observation = _decode_observation(
        RPC_URL,
        receipt,
        expected_probe=expected_probe,
        expected_signer=SIGNER,
        expected_observation_id=7,
    )

    assert observation["arb_block_number"] == receipt_block + 1
    assert observation["receipt_block_number"] == receipt_block
    assert observation["arb_receipt_agreement"] is False


def test_probe_is_excluded_from_production_discovery_and_abi_export(tmp_path):
    files = load_vyper_files()
    assert "ActionBlockIdentityProbe" not in files
    assert all("contracts/testing/" not in path for path in files.values())

    contracts = tmp_path / "contracts"
    output = tmp_path / "abis"
    (contracts / "testing").mkdir(parents=True)
    (contracts / "testing" / "ActionBlockIdentityProbe.vy").write_text(
        Path(PROBE_PATH).read_text()
    )
    export_abis(contracts, output)
    assert not output.exists() or not list(output.glob("*.json"))


def test_artifact_hashes_are_keccak_of_exact_compiler_outputs():
    artifacts = compile_probe_artifacts()
    deployer = boa.load_partial(PROBE_PATH)

    runner._validate_compiled_artifacts(artifacts)
    assert artifacts.source_sha256 == runner.EXPECTED_PROBE_SOURCE_SHA256
    assert artifacts.abi_sha256 == runner.EXPECTED_PROBE_ABI_SHA256
    assert (
        artifacts.compiler_inputs_sha256
        == runner.EXPECTED_PROBE_COMPILER_INPUTS_SHA256
    )
    assert artifacts.creation_bytecode_keccak256 == (
        "0x" + keccak(bytes(deployer.compiler_data.bytecode)).hex()
    )
    assert (
        artifacts.creation_bytecode_keccak256
        == runner.EXPECTED_PROBE_CREATION_BYTECODE_KECCAK256
    )
    assert artifacts.runtime_bytecode_keccak256 == (
        "0x" + keccak(bytes(deployer.compiler_data.bytecode_runtime)).hex()
    )
    assert (
        artifacts.runtime_bytecode_keccak256
        == runner.EXPECTED_PROBE_RUNTIME_BYTECODE_KECCAK256
    )


@pytest.mark.parametrize(
    "field",
    [
        "source_sha256",
        "abi_sha256",
        "compiler_inputs_sha256",
        "creation_bytecode_keccak256",
        "runtime_bytecode_keccak256",
    ],
)
def test_compiled_artifact_drift_stops_before_rpc(monkeypatch, field):
    artifacts = compile_probe_artifacts()
    drifted = replace(artifacts, **{field: "0x" + "00" * 32})
    approved = parse_approval(_approval_data())
    monkeypatch.setattr(
        runner,
        "_rpc",
        lambda *_args: pytest.fail("RPC must not run after artifact drift"),
    )

    with pytest.raises(ApprovalError, match="reviewed hardcoded identity"):
        preflight(approved, RPC_URL, artifacts=drifted)
