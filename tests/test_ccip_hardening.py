import hashlib
import json
from pathlib import Path
import time
from unittest import mock

import pytest
from click.testing import CliRunner

from config.Ccip import (
    CCIP_EVIDENCE_GATES,
    CCIP_HQ_APPEND_WINDOW_GATES,
    CCIP_LIVE_SEND_EVIDENCE_GATES,
    CCIP_OWNER_DISPOSITION_GATES,
    CCIP_REQUIRED_EVIDENCE_NAMES,
    CcipEvidenceRecord,
    CcipHqAppendWindow,
    CcipLanePolicy,
    CcipRateLimitPolicy,
    CcipReceiverControlProof,
    require_ccip_live_send_evidence,
)
from scripts.utils import ccip


ROOT = Path(__file__).resolve().parents[1]
WIRE_MIGRATIONS = (
    "migrations/base-mainnet/2026080701_CcipWire.py",
    "migrations/robinhood-mainnet/2026080701_CcipWire.py",
    "migrations/base-sepolia/0002_CcipWire.py",
    "migrations/robinhood-testnet/0002_CcipWire.py",
)
POOL_MIGRATIONS = (
    "migrations/base-mainnet/2026080700_CcipPools.py",
    "migrations/robinhood-mainnet/2026080700_CcipPools.py",
    "migrations/base-sepolia/0001_CcipPool.py",
    "migrations/robinhood-testnet/0001_CcipPool.py",
)


def _ccip_send_module():
    with mock.patch("dotenv.load_dotenv"):
        import scripts.ccip_send as module

    return module


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("1", 10**18),
        ("1.5", 15 * 10**17),
        ("0.000000000000000001", 1),
        ("123456789012345678.123456789012345678", 123456789012345678123456789012345678),
    ),
)
def test_ccip_amount_parser_is_exact(text, expected):
    module = _ccip_send_module()
    assert module._parse_amount(text) == expected
    assert module._parse_amount(module._format_amount(expected)) == expected


def test_ccip_amount_parser_accepts_exact_uint256_maximum():
    module = _ccip_send_module()
    text = module._format_amount(module.MAX_UINT256)
    assert module._parse_amount(text) == module.MAX_UINT256


@pytest.mark.parametrize(
    "text",
    (
        "",
        "0",
        "0.0",
        "-1",
        "+1",
        "1e18",
        ".1",
        "1.",
        "00",
        "1.0000000000000000001",
        " 1",
        "1 ",
    ),
)
def test_ccip_amount_parser_rejects_ambiguous_or_nonpositive_values(text):
    with pytest.raises(ValueError):
        _ccip_send_module()._parse_amount(text)


def test_ccip_amount_parser_rejects_uint256_overflow():
    module = _ccip_send_module()
    overflow = module._format_amount(module.MAX_UINT256 + 1)
    with pytest.raises(ValueError, match="exceeds uint256"):
        module._parse_amount(overflow)


def _live_args():
    return [
        "--chain",
        "base-mainnet",
        "--environment",
        "v1",
        "--amount",
        "1.000000000000000001",
        "--rpc",
        "https://rpc.invalid",
        "--to-rpc",
        "https://destination.invalid",
        "--receiver",
        "0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf",
    ]


def test_live_send_validates_chain_and_manifest_then_fails_at_backend(monkeypatch):
    module = _ccip_send_module()
    observed = []
    real_manifest = module._manifest

    monkeypatch.setattr(
        module,
        "_read_chain_id",
        lambda rpc: 8453 if rpc == "https://rpc.invalid" else 4663,
    )

    def manifest(chain, environment):
        observed.append((chain, environment))
        return real_manifest(chain, environment)

    monkeypatch.setattr(module, "_manifest", manifest)
    monkeypatch.setattr(module, "_read_code", lambda rpc, receiver: "0x")
    monkeypatch.setattr(module, "require_ccip_live_send_evidence", lambda *args: None)
    result = CliRunner().invoke(module.cli, _live_args())

    assert result.exit_code != 0
    assert "CCIP_LIVE_SIGNER_UNBOUND" in result.output
    assert observed == [("base-mainnet", "v1")]


def test_live_send_is_blocked_by_unresolved_receiver_control_proof(monkeypatch):
    module = _ccip_send_module()
    monkeypatch.setattr(
        module,
        "_read_chain_id",
        lambda rpc: 8453 if rpc == "https://rpc.invalid" else 4663,
    )
    monkeypatch.setattr(module, "_read_code", lambda rpc, receiver: "0x")

    result = CliRunner().invoke(module.cli, _live_args())

    assert result.exit_code != 0
    assert "CCIP_LIVE_SEND_EVIDENCE_REQUIRED" in result.output
    assert "DESTINATION_RECEIVER_CONTROL_PROOF" in result.output
    assert "CCIP_LIVE_SIGNER_UNBOUND" not in result.output


def test_destination_validation_precedes_manifest_and_sender_backend(monkeypatch):
    module = _ccip_send_module()
    observed = []
    real_manifest = module._manifest

    def read_chain_id(rpc):
        observed.append(("chain", rpc))
        return 8453 if rpc == "https://rpc.invalid" else 4663

    def read_code(rpc, receiver):
        observed.append(("code", rpc, receiver))
        return "0x"

    def manifest(chain, environment):
        observed.append(("manifest", chain, environment))
        return real_manifest(chain, environment)

    def select_sender(*args, **kwargs):
        observed.append(("sender",))
        raise ValueError("stop-before-backend")

    monkeypatch.setattr(module, "_read_chain_id", read_chain_id)
    monkeypatch.setattr(module, "_read_code", read_code)
    monkeypatch.setattr(module, "_manifest", manifest)
    monkeypatch.setattr(module, "_select_sender", select_sender)

    result = CliRunner().invoke(module.cli, _live_args())

    assert result.exit_code != 0
    assert "stop-before-backend" in result.output
    assert [entry[0] for entry in observed] == [
        "chain",
        "chain",
        "code",
        "manifest",
        "sender",
    ]


def test_live_receiver_control_proof_is_exactly_bound_and_fresh(monkeypatch, tmp_path):
    receiver = "0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf"
    evidence = {
        "schema_version": 1,
        "source_chain": "base-mainnet",
        "destination_chain": "robinhood-mainnet",
        "receiver": receiver.lower(),
        "issued_at": 100,
        "expires_at": 200,
    }
    evidence_path = tmp_path / "receiver-control.json"
    evidence_payload = json.dumps(evidence, sort_keys=True).encode()
    evidence_path.write_bytes(evidence_payload)
    proof = CcipReceiverControlProof(
        source_chain="base-mainnet",
        destination_chain="robinhood-mainnet",
        receiver=receiver,
        evidence_path=str(evidence_path),
        evidence_sha256=hashlib.sha256(evidence_payload).hexdigest(),
        issued_at=100,
        expires_at=200,
    )
    monkeypatch.setitem(
        CCIP_LIVE_SEND_EVIDENCE_GATES,
        "DESTINATION_RECEIVER_CONTROL_PROOF",
        proof,
    )

    assert (
        require_ccip_live_send_evidence(
            "base-mainnet",
            "robinhood-mainnet",
            receiver.upper().replace("0X", "0x"),
            now=150,
        )
        is proof
    )
    with pytest.raises(RuntimeError, match="BINDING_MISMATCH"):
        require_ccip_live_send_evidence(
            "base-mainnet",
            "robinhood-mainnet",
            "0x355bB7F0f6c730e4460d620420a300fa08FF82F3",
            now=150,
        )
    with pytest.raises(RuntimeError, match="STALE"):
        require_ccip_live_send_evidence(
            "base-mainnet", "robinhood-mainnet", receiver, now=200
        )

    tampered_evidence = dict(evidence)
    tampered_evidence["receiver"] = "0x355bb7f0f6c730e4460d620420a300fa08ff82f3"
    evidence_path.write_text(json.dumps(tampered_evidence, sort_keys=True))
    with pytest.raises(RuntimeError, match="DIGEST_MISMATCH"):
        require_ccip_live_send_evidence(
            "base-mainnet", "robinhood-mainnet", receiver, now=150
        )


def test_live_receiver_control_gate_rejects_untyped_acknowledgement(monkeypatch):
    monkeypatch.setitem(
        CCIP_LIVE_SEND_EVIDENCE_GATES,
        "DESTINATION_RECEIVER_CONTROL_PROOF",
        "operator-says-it-is-fine",
    )
    with pytest.raises(RuntimeError, match="CCIP_LIVE_SEND_EVIDENCE_INVALID"):
        require_ccip_live_send_evidence(
            "base-mainnet",
            "robinhood-mainnet",
            "0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf",
            now=150,
        )


def test_chain_id_mismatch_fails_before_live_backend(monkeypatch):
    module = _ccip_send_module()
    monkeypatch.setattr(module, "_read_chain_id", lambda rpc: 4663)

    result = CliRunner().invoke(module.cli, _live_args())

    assert result.exit_code != 0
    assert "H02_CHAIN_ID_MISMATCH" in result.output
    assert "expected_chain_id=8453" in result.output
    assert "observed_chain_id=4663" in result.output
    assert "CCIP_LIVE_SIGNER_UNBOUND" not in result.output


def test_invalid_amount_fails_before_any_rpc_read(monkeypatch):
    module = _ccip_send_module()
    reader = mock.Mock(side_effect=AssertionError("RPC must not be read"))
    monkeypatch.setattr(module, "_read_chain_id", reader)
    args = _live_args()
    args[args.index("1.000000000000000001")] = "1e18"

    result = CliRunner().invoke(module.cli, args)

    assert result.exit_code != 0
    assert "invalid --amount" in result.output
    reader.assert_not_called()


def test_receiver_is_explicit_and_required_before_any_rpc_read(monkeypatch):
    module = _ccip_send_module()
    reader = mock.Mock(side_effect=AssertionError("RPC must not be read"))
    monkeypatch.setattr(module, "_read_chain_id", reader)
    args = _live_args()
    receiver_index = args.index("--receiver")
    del args[receiver_index : receiver_index + 2]

    result = CliRunner().invoke(module.cli, args)

    assert result.exit_code != 0
    assert "Missing option '--receiver'" in result.output
    reader.assert_not_called()


def test_fork_requires_explicit_impersonated_address_before_rpc(monkeypatch):
    module = _ccip_send_module()
    reader = mock.Mock(side_effect=AssertionError("RPC must not be read"))
    monkeypatch.setattr(module, "_read_chain_id", reader)

    result = CliRunner().invoke(module.cli, [*_live_args(), "--fork"])

    assert result.exit_code != 0
    assert "--as-address is required in fork mode" in result.output
    reader.assert_not_called()


def test_fork_requires_receiver_control_acknowledgement_before_rpc(monkeypatch):
    module = _ccip_send_module()
    reader = mock.Mock(side_effect=AssertionError("RPC must not be read"))
    monkeypatch.setattr(module, "_read_chain_id", reader)

    result = CliRunner().invoke(
        module.cli,
        [
            *_live_args(),
            "--fork",
            "--as-address",
            "0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf",
        ],
    )

    assert result.exit_code != 0
    assert "--acknowledge-destination-control is required in fork mode" in result.output
    assert "not ownership proof" in result.output
    reader.assert_not_called()


def test_receiver_control_acknowledgement_cannot_authorize_live_mode(monkeypatch):
    module = _ccip_send_module()
    reader = mock.Mock(side_effect=AssertionError("RPC must not be read"))
    monkeypatch.setattr(module, "_read_chain_id", reader)

    result = CliRunner().invoke(
        module.cli,
        [*_live_args(), "--acknowledge-destination-control"],
    )

    assert result.exit_code != 0
    assert "--acknowledge-destination-control is fork-only" in result.output
    reader.assert_not_called()


def test_zero_gas_destination_requires_current_code_emptiness(monkeypatch):
    module = _ccip_send_module()
    receiver = "0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf"

    monkeypatch.setattr(module, "_read_code", lambda rpc, address: "0x")
    module._require_zero_gas_code_empty_destination(
        "https://destination.invalid", receiver
    )

    monkeypatch.setattr(module, "_read_code", lambda rpc, address: "0x6000")
    with pytest.raises(ValueError, match="CCIP_ZERO_GAS_DESTINATION_CODE_NOT_EMPTY"):
        module._require_zero_gas_code_empty_destination(
            "https://destination.invalid", receiver
        )

    with pytest.raises(ValueError, match="reserved low-address range"):
        module._require_zero_gas_code_empty_destination(
            "https://destination.invalid",
            "0x0000000000000000000000000000000000000001",
        )


def test_destination_chain_identity_is_verified_before_forking(monkeypatch):
    module = _ccip_send_module()
    monkeypatch.setattr(
        module,
        "_read_chain_id",
        lambda rpc: 8453,
    )
    code_reader = mock.Mock(side_effect=AssertionError("code read must not run"))
    monkeypatch.setattr(module, "_read_code", code_reader)

    result = CliRunner().invoke(
        module.cli,
        [
            *_live_args(),
            "--fork",
            "--as-address",
            "0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf",
            "--acknowledge-destination-control",
        ],
    )

    assert result.exit_code != 0
    assert "H02_CHAIN_ID_MISMATCH" in result.output
    assert "expected_chain_id=4663" in result.output
    assert "observed_chain_id=8453" in result.output
    code_reader.assert_not_called()


def test_fee_balance_exactness_distinguishes_erc20_from_native_gas():
    module = _ccip_send_module()
    assert not module._fee_balance_is_insufficient(100, 100, pays_in_erc20=True)
    assert module._fee_balance_is_insufficient(100, 100, pays_in_erc20=False)
    assert module._fee_balance_is_insufficient(99, 100, pays_in_erc20=True)


class _ConfiguredPool:
    def __init__(self, selector, remote_pool, remote_token, rate=(False, 0, 0)):
        self.selector = selector
        self.remote_pools = [ccip.encode_address(remote_pool)]
        self.remote_token = ccip.encode_address(remote_token)
        self.rate = rate
        self.rate_admin = "0x0000000000000000000000000000000000000000"
        self.calls = []

    def isSupportedChain(self, selector):
        self.calls.append("isSupportedChain")
        return selector == self.selector

    def getRemoteToken(self, selector):
        self.calls.append("getRemoteToken")
        return self.remote_token

    def getRemotePools(self, selector):
        self.calls.append("getRemotePools")
        return self.remote_pools

    def _bucket(self):
        enabled, capacity, rate = self.rate
        return (capacity, 1, enabled, capacity, rate)

    def getCurrentOutboundRateLimiterState(self, selector):
        self.calls.append("getCurrentOutboundRateLimiterState")
        return self._bucket()

    def getCurrentInboundRateLimiterState(self, selector):
        self.calls.append("getCurrentInboundRateLimiterState")
        return self._bucket()

    def getRateLimitAdmin(self):
        self.calls.append("getRateLimitAdmin")
        return self.rate_admin


def test_supported_lane_is_fully_revalidated():
    selector = 6180753054346818345
    remote_pool = "0xE51aF1311832818A6D366081Fc535CA56357a6EE"
    remote_token = "0x4D3f37a965b21aB4122e92Dd41D2693E742c883b"
    pool = _ConfiguredPool(selector, remote_pool, remote_token)

    ccip.assert_lane_configuration(
        pool,
        selector,
        remote_pool,
        remote_token,
        (False, 0, 0),
        (False, 0, 0),
        "0x0000000000000000000000000000000000000000",
    )

    assert pool.calls == [
        "isSupportedChain",
        "getRemoteToken",
        "getRemotePools",
        "getCurrentOutboundRateLimiterState",
        "getCurrentInboundRateLimiterState",
        "getRateLimitAdmin",
    ]


@pytest.mark.parametrize("mutation", ("token", "extra_pool", "rate", "rate_admin"))
def test_supported_lane_revalidation_rejects_stale_or_wrong_wiring(mutation):
    selector = 6180753054346818345
    remote_pool = "0xE51aF1311832818A6D366081Fc535CA56357a6EE"
    remote_token = "0x4D3f37a965b21aB4122e92Dd41D2693E742c883b"
    pool = _ConfiguredPool(selector, remote_pool, remote_token)
    if mutation == "token":
        pool.remote_token = ccip.encode_address(
            "0x355bB7F0f6c730e4460d620420a300fa08FF82F3"
        )
    elif mutation == "extra_pool":
        pool.remote_pools.append(
            ccip.encode_address("0x4B19f165Bb1Ce3f19Bbe828D150706B9deeEeC95")
        )
    elif mutation == "rate":
        pool.rate = (True, 10**18, 10**15)
    else:
        pool.rate_admin = "0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf"

    with pytest.raises(AssertionError):
        ccip.assert_lane_configuration(
            pool,
            selector,
            remote_pool,
            remote_token,
            (False, 0, 0),
            (False, 0, 0),
            "0x0000000000000000000000000000000000000000",
        )


@pytest.mark.parametrize("relative_path", WIRE_MIGRATIONS)
def test_wire_migration_revalidates_supported_lane_and_gates_new_mutation(
    relative_path,
):
    source = (ROOT / relative_path).read_text()
    supported_branch = source.index("if lane_is_configured:")
    revalidation = source.index("ccip.assert_lane_configuration(", supported_branch)
    mutation = source.index("ccip.execute_activation_mutation(", supported_branch)

    assert "continue" not in source[supported_branch:revalidation]
    assert mutation < revalidation
    assert "migration.execute(" not in source


def test_activation_mutation_wrapper_checks_gates_before_execute(monkeypatch):
    observed = []

    class _Migration:
        def chain(self):
            return "base-mainnet"

        def execute(self, action, *args):
            observed.append(("execute", action, args))
            return "result"

    monkeypatch.setattr(
        ccip,
        "require_ccip_wiring_gates",
        lambda *binding: observed.append(("gate", binding)) or "policy",
    )

    assert (
        ccip.execute_activation_mutation(
            _Migration(),
            "RIPE",
            "action",
            1,
            2,
            remote_chain="robinhood-mainnet",
        )
        == "result"
    )
    assert observed == [
        (
            "gate",
            ("base-mainnet", "robinhood-mainnet", "RIPE"),
        ),
        ("execute", "action", (1, 2)),
    ]


def test_typed_owner_policy_is_returned_for_its_exact_lane(
    monkeypatch, tmp_path
):
    binding = ("base-mainnet", "robinhood-mainnet", "RIPE")
    policy = CcipLanePolicy(
        *binding,
        outbound=CcipRateLimitPolicy(True, 1_000, 10),
        inbound=CcipRateLimitPolicy(True, 1_100, 11),
        rate_limit_admin="0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf",
    )
    monkeypatch.setitem(CCIP_OWNER_DISPOSITION_GATES, binding, policy)
    for name in CCIP_REQUIRED_EVIDENCE_NAMES:
        expires_at = 4_000_000_000 if name == "AUTOMATIC_EXECUTION_DESTINATION_GAS" else None
        evidence = {
            "schema_version": 1,
            "gate_name": name,
            "local_chain": binding[0],
            "remote_chain": binding[1],
            "token": binding[2],
            "approved_at": 1,
            "expires_at": expires_at,
        }
        path = tmp_path / f"{name}.json"
        payload = json.dumps(evidence, sort_keys=True).encode()
        path.write_bytes(payload)
        key = (*binding, name)
        monkeypatch.setitem(
            CCIP_EVIDENCE_GATES,
            key,
            CcipEvidenceRecord(
                name,
                *binding,
                evidence_path=str(path),
                evidence_sha256=hashlib.sha256(payload).hexdigest(),
                approved_at=1,
                expires_at=expires_at,
            ),
        )

    class _Migration:
        def chain(self):
            return "base-mainnet"

    assert (
        ccip.require_activation_policy(_Migration(), "RIPE", "robinhood-mainnet")
        is policy
    )
    assert ccip.lane_policy_for_revalidation(*binding) is policy


def test_rate_policy_rejects_values_chainlink_would_revert():
    with pytest.raises(ValueError, match="0 < rate < capacity"):
        CcipRateLimitPolicy(True, 10, 10)
    with pytest.raises(ValueError, match="zero capacity and zero rate"):
        CcipRateLimitPolicy(False, 10, 0)


def test_already_wired_revalidation_uses_observed_baseline_without_owner_choice():
    policy = ccip.lane_policy_for_revalidation(
        "base-mainnet", "robinhood-mainnet", "RIPE"
    )
    assert policy.outbound.as_tuple() == (False, 0, 0)
    assert policy.inbound.as_tuple() == (False, 0, 0)
    assert policy.rate_limit_admin == ("0x0000000000000000000000000000000000000000")


@pytest.mark.parametrize("relative_path", POOL_MIGRATIONS)
def test_every_ccip_pool_deployment_is_policy_gated(relative_path):
    source = (ROOT / relative_path).read_text()
    deploy_offsets = []
    start = 0
    while True:
        offset = source.find("migration.deploy_solidity(", start)
        if offset == -1:
            break
        deploy_offsets.append(offset)
        start = offset + 1

    assert deploy_offsets, f"{relative_path} has no pool deployment"
    gate_offsets = []
    start = 0
    while True:
        offset = source.find("ccip.require_activation_policy(", start)
        if offset == -1:
            break
        gate_offsets.append(offset)
        start = offset + 1

    assert len(gate_offsets) >= len(deploy_offsets)
    assert all(gate < deploy for gate, deploy in zip(gate_offsets, deploy_offsets))
    assert "migration.execute(" not in source


@pytest.mark.parametrize("relative_path", WIRE_MIGRATIONS)
def test_selected_policy_values_drive_wiring_and_revalidation(relative_path):
    source = (ROOT / relative_path).read_text()
    assert "policy.outbound.as_tuple()" in source
    assert "policy.inbound.as_tuple()" in source
    assert "policy.rate_limit_admin" in source
    assert "NO_RATE_LIMIT" not in source
    assert "CURRENT_RATE_LIMIT_ADMIN" not in source


@pytest.mark.parametrize("relative_path", WIRE_MIGRATIONS[:2])
def test_mainnet_safe_plan_binds_live_ccip_append_order(relative_path):
    source = (ROOT / relative_path).read_text()
    assert 'POOLS = (\n    ("RIPE"' in source
    preflight = source.index("ccip.require_mainnet_hq_append_preflight(")
    first_mutation = source.index("ccip.execute_activation_mutation(")
    assert preflight < first_mutation
    assert "expected_plan_sha256=hq_append_plan_sha256" in source
    assert "initiateHqConfigChange(uint256,bool,bool,bool)" in source
    assert "confirmHqConfigChange(uint256)" in source
    assert "AFTER registryChangeTimeLock" in source
    assert "AFTER a second registryChangeTimeLock" in source
    assert "must assign RipeHq id" not in source


def test_hq_append_preflight_requires_exact_empty_exclusive_window(monkeypatch):
    zero = "0x0000000000000000000000000000000000000000"

    class _Hq:
        def numAddrs(self):
            return 23

        def getAddr(self, registry_id):
            assert registry_id in (23, 24)
            return zero

    with pytest.raises(RuntimeError, match="CCIP_HQ_APPEND_WINDOW_REQUIRED"):
        ccip.require_mainnet_hq_append_preflight(
            "base-mainnet", _Hq(), ("RIPE", "GREEN")
        )

    window = CcipHqAppendWindow(
        chain="base-mainnet",
        assignments=(("RIPE", 23), ("GREEN", 24)),
        coordination_reference="safe-plan-approval-123",
        exclusive_governance_window=True,
        plan_sha256="ab" * 32,
        starts_at=int(time.time()) - 10,
        expires_at=int(time.time()) + 3600,
    )
    monkeypatch.setitem(CCIP_HQ_APPEND_WINDOW_GATES, "base-mainnet", window)
    assert (
        ccip.require_mainnet_hq_append_preflight(
            "base-mainnet", _Hq(), ("RIPE", "GREEN")
        )
        is window
    )

    with pytest.raises(RuntimeError, match="PARTIAL_STATE"):
        ccip.require_mainnet_hq_append_preflight("base-mainnet", _Hq(), ("GREEN",))
