from __future__ import annotations

import pytest


@pytest.fixture
def identity_manifest_value(digest):
    return {
        "artifact_kind": "rh_canonical_identity_manifest",
        "chain_id": 46630,
        "identities": [
            {
                "address": "0x1111111111111111111111111111111111111111",
                "authority": "owner-supplied",
                "identity_id": "synthetic-token-fixture",
                "implementation_address": None,
                "kind": "token",
                "provenance_sha256": digest,
                "proxy_address": None,
                "runtime_code_sha256": digest,
            }
        ],
        "owner_approval_sha256": digest,
        "profile": "robinhood-testnet",
        "schema_version": "owner-rh-canonical-identities-v1",
    }


@pytest.fixture
def parse_identity(fork_framework, identity_manifest_value):
    def parse(value=None):
        actual = identity_manifest_value if value is None else value
        return fork_framework.parse_identity_manifest(
            fork_framework.canonical_json_bytes(actual)
        )

    return parse
