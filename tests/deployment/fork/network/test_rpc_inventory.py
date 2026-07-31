from __future__ import annotations

import pytest


def test_only_explicit_read_only_rpc_methods_are_permitted(fork_framework):
    methods = tuple(sorted(fork_framework.READ_ONLY_RPC_METHODS))
    assert fork_framework.validate_rpc_inventory(methods) == methods


@pytest.mark.parametrize(
    "method",
    (
        "eth_sendRawTransaction",
        "eth_sendTransaction",
        "personal_unlockAccount",
        "wallet_addEthereumChain",
        "admin_addPeer",
        "miner_start",
    ),
)
def test_signing_broadcast_and_admin_rpc_methods_are_forbidden(
    fork_framework, method
):
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_RPC_METHOD_FORBIDDEN",
    ):
        fork_framework.validate_rpc_inventory((method,))


def test_unapproved_read_method_is_fail_closed(fork_framework):
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_RPC_METHOD_UNAPPROVED",
    ):
        fork_framework.validate_rpc_inventory(("debug_traceCall",))


def test_endpoint_fingerprint_omits_credentials_path_and_query(
    fork_framework,
):
    first = fork_framework.endpoint_fingerprint(
        "https://user:secret@archive.invalid/private/key?api_key=secret"
    )
    second = fork_framework.endpoint_fingerprint(
        "https://archive.invalid/another/path?token=different"
    )
    assert first == second
    assert "secret" not in first
    assert len(first) == 64


def test_endpoint_resolution_is_opaque_and_secret_free(fork_framework):
    raw = "https://user:secret@archive.invalid/private?key=secret"
    fingerprint = fork_framework.endpoint_fingerprint(raw)
    endpoint = fork_framework.EndpointIdentity(
        "OWNER_RH_ARCHIVE_TEST", fingerprint
    )
    resolved = fork_framework.resolve_endpoint(
        endpoint, {"OWNER_RH_ARCHIVE_TEST": raw}
    )
    assert resolved.value == raw
    assert raw not in str(resolved)
    assert raw not in repr(resolved)
    assert "secret" not in str(resolved)
    assert "secret" not in repr(resolved)


def test_endpoint_fingerprint_mismatch_does_not_log_secret(fork_framework):
    raw = "https://user:top-secret@archive.invalid/private"
    endpoint = fork_framework.EndpointIdentity(
        "OWNER_RH_ARCHIVE_TEST", "ab" * 32
    )
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_ENDPOINT_FINGERPRINT_MISMATCH",
    ) as caught:
        fork_framework.resolve_endpoint(
            endpoint, {"OWNER_RH_ARCHIVE_TEST": raw}
        )
    assert raw not in str(caught.value)
    assert "top-secret" not in str(caught.value)
