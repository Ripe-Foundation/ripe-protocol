from __future__ import annotations

import os
import socket
import stat
from pathlib import Path

import pytest
import requests


def test_safe_default_blocks_socket_and_requests():
    with pytest.raises(
        AssertionError, match="H-09 default mode disables external networking"
    ):
        socket.create_connection(("127.0.0.1", 1))
    with pytest.raises(
        AssertionError, match="H-09 default mode disables external networking"
    ):
        requests.get("https://example.invalid")


def test_external_root_must_be_mode_0700_and_outside_repository(
    fork_framework, tmp_path: Path
):
    root = tmp_path / "external"
    root.mkdir(mode=0o700)
    os.chmod(root, 0o700)
    assert (
        stat.S_IMODE(
            fork_framework.validate_external_root(root).stat().st_mode
        )
        == 0o700
    )
    os.chmod(root, 0o755)
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_EXTERNAL_ROOT_MODE"
    ):
        fork_framework.validate_external_root(root)


def test_repository_paths_cannot_be_external_roots(
    fork_framework, tmp_path: Path
):
    repository = tmp_path / "repository"
    repository.mkdir(mode=0o700)
    child = repository / "cache"
    child.mkdir(mode=0o700)
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_EXTERNAL_ROOT_REPOSITORY",
    ):
        fork_framework.validate_external_root(
            child, repository_root=repository
        )


def test_qualification_mode_does_not_read_endpoint_during_selection(
    fork_framework
):
    class Spy(dict):
        def __init__(self):
            super().__init__(
                {"RIPE_RH_FORK_MODE": "read-only-archive-fork"}
            )
            self.accessed = []

        def get(self, name, default=None):
            self.accessed.append(name)
            return super().get(name, default)

    environment = Spy()
    assert fork_framework.qualification_mode(environment) == (
        "read-only-archive-fork"
    )
    assert environment.accessed == ["RIPE_RH_FORK_MODE"]
