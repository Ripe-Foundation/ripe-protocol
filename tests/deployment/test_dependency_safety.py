"""Supply-chain properties for the Python toolchain.

This replaces a 1,863-line dependency gate that pinned a sha256 of
`requirements.txt`, froze every selected version, and reconciled each one
against a 5,873-line evidence document. None of those dependencies reach a
deployed byte -- the on-chain artifacts come from `vyper` alone -- so that gate
failed on every routine dependency bump and taught nothing about the protocol.

What survives is the part that is a property rather than a record: dependencies
must come from public PyPI, and address checksumming must not touch the
network. Neither needs updating when a version changes; both fail only when
something is actually wrong. Version currency belongs to `pip check` in CI and
to a vulnerability scanner, not to a hand-maintained inventory.
"""

from __future__ import annotations

import re
import socket
from importlib import metadata
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
DIRECT_INPUT = ROOT / "requirements.in"
LOCK = ROOT / "requirements.txt"

REQUIREMENT_NAME = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep dependency checks independent of protocol deployment."""


def _requirement_lines(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _declared_packages() -> set[str]:
    names = set()
    for line in _requirement_lines(DIRECT_INPUT):
        match = REQUIREMENT_NAME.match(line)
        if match:
            names.add(match.group(1))
    return names


def test_dependency_sources_are_public_pypi_only():
    """No VCS checkouts, local paths, or private indexes in either file.

    A direct URL or an extra index is how a dependency stops being the package
    everyone else audits. This is the check worth keeping: it constrains
    *where* code comes from, and it stays true across every version bump.
    """
    for line in _requirement_lines(DIRECT_INPUT) + _requirement_lines(LOCK):
        assert "://" not in line, line
        assert " @ " not in line, line
        assert not line.startswith(("-e", "--editable", ".", "/", "~")), line
        assert not any(
            marker in line.lower()
            for marker in ("git+", "hg+", "svn+", "bzr+", "file:")
        ), line

    combined = DIRECT_INPUT.read_text() + LOCK.read_text()
    assert "--extra-index-url" not in combined
    assert "--find-links" not in combined
    assert "private-index" not in combined.lower()

    # Installed distributions must also carry no direct-URL provenance. Read
    # from the declared inputs rather than a frozen allowlist, so adding a
    # dependency extends the check instead of silently escaping it.
    for package in sorted(_declared_packages()):
        try:
            distribution = metadata.distribution(package)
        except metadata.PackageNotFoundError:
            continue
        assert distribution.read_text("direct_url.json") is None, package


def test_web3_checksum_and_keccak_make_no_network_attempt(monkeypatch):
    """Address checksumming and keccak must be pure local computation.

    A dependency that resolved addresses over the network would be both a
    correctness and a privacy problem on a deploy path. Every socket entry
    point is denied for the duration.
    """
    from web3 import Web3

    attempts: list[str] = []

    def deny(operation):
        def denied(*args, **kwargs):
            attempts.append(operation)
            raise AssertionError(f"network attempt through {operation}")

        return denied

    for operation in (
        "socket",
        "create_connection",
        "getaddrinfo",
        "gethostbyaddr",
        "gethostbyname",
        "gethostbyname_ex",
    ):
        monkeypatch.setattr(socket, operation, deny(f"socket.{operation}"))

    assert (
        Web3.to_checksum_address("0x52908400098527886e0f7030069857d2e4169ee7")
        == "0x52908400098527886E0F7030069857D2E4169EE7"
    )
    assert Web3.keccak(text="ripe-web3-offline-gate").hex() == (
        "1d17285abbb738ef53dadaa05ee534ef754ed12345f9c7c31b08c1819d611824"
    )
    assert attempts == []
