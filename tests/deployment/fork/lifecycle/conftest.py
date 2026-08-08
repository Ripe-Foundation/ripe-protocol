from __future__ import annotations

import pytest


@pytest.fixture
def evidence_value(accepted_preflight):
    envelope = accepted_preflight.envelope
    return {
        "assertion_ids": ["assertion-a", "assertion-b"],
        "endpoint_fingerprint_sha256": (
            envelope.owner.endpoint.fingerprint_sha256
        ),
        "input_envelope_sha256": envelope.sha256,
        "observed_fork_facts": {
            "block_hash": envelope.owner.pin.block_hash,
            "block_number": envelope.owner.pin.number,
            "chain_id": envelope.owner.expected_chain_id,
        },
        "ordered_rpc_methods": ["eth_chainId", "eth_getBlockByHash"],
        "read_only": True,
        "runtime_destruction": {
            "process_terminated": True,
            "storage_disposed": True,
        },
        "scenario_ids": ["scenario-a"],
    }
