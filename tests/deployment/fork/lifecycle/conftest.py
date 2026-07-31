from __future__ import annotations

import pytest


@pytest.fixture
def evidence_value():
    return {
        "assertion_ids": ["assertion-a", "assertion-b"],
        "endpoint_fingerprint_sha256": "12" * 32,
        "input_envelope_sha256": "34" * 32,
        "observed_fork_facts": {
            "block_hash": "0x" + "56" * 32,
            "block_number": 123,
            "chain_id": 46630,
        },
        "ordered_rpc_methods": ["eth_chainId", "eth_getBlockByHash"],
        "read_only": True,
        "runtime_destruction": {
            "process_terminated": True,
            "storage_disposed": True,
        },
        "scenario_ids": ["scenario-a"],
    }
