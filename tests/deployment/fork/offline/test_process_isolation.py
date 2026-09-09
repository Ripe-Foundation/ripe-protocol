from __future__ import annotations

import os
import shutil
import socket
import stat
import subprocess
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


def test_repository_observation_uses_independent_git_and_detects_dirt(
    fork_framework, tmp_path: Path
):
    repository = tmp_path / "repository"
    repository.mkdir()
    git = shutil.which("git")
    assert git is not None
    subprocess.run((git, "init", "-q", str(repository)), check=True)
    tracked = repository / "tracked.txt"
    tracked.write_text("frozen\n", encoding="utf-8")
    (repository / ".gitignore").write_text("*.cache\n", encoding="utf-8")
    subprocess.run(
        (git, "-C", str(repository), "add", "tracked.txt", ".gitignore"),
        check=True,
    )
    subprocess.run(
        (
            git,
            "-C",
            str(repository),
            "-c",
            "user.name=H09 Test",
            "-c",
            "user.email=h09@example.invalid",
            "-c",
            "commit.gpgSign=false",
            "commit",
            "-q",
            "-m",
            "fixture",
        ),
        check=True,
    )
    clean = fork_framework.observe_repository_authority(repository)
    assert clean["changed_paths"] == ()
    assert clean["ignored_paths"] == ()
    assert clean["staged_paths"] == ()

    staged = repository / "staged.txt"
    staged.write_text("staged\n", encoding="utf-8")
    subprocess.run(
        (git, "-C", str(repository), "add", "staged.txt"), check=True
    )
    staged_observation = fork_framework.observe_repository_authority(
        repository
    )
    assert staged_observation["staged_paths"] == ("staged.txt",)
    assert staged_observation["changed_paths"] == ()
    subprocess.run(
        (
            git,
            "-C",
            str(repository),
            "-c",
            "user.name=H09 Test",
            "-c",
            "user.email=h09@example.invalid",
            "-c",
            "commit.gpgSign=false",
            "commit",
            "-q",
            "-m",
            "staged fixture",
        ),
        check=True,
    )

    tracked.write_text("unstaged\n", encoding="utf-8")
    unstaged = fork_framework.observe_repository_authority(repository)
    assert unstaged["changed_paths"] == ("tracked.txt",)
    assert unstaged["staged_paths"] == ()
    tracked.write_text("frozen\n", encoding="utf-8")

    untracked_path = repository / "untracked.txt"
    untracked_path.write_text(
        "candidate\n", encoding="utf-8"
    )
    untracked = fork_framework.observe_repository_authority(repository)
    assert untracked["changed_paths"] == ("untracked.txt",)
    untracked_path.unlink()

    (repository / "artifact.cache").write_text("ignored\n", encoding="utf-8")
    ignored = fork_framework.observe_repository_authority(repository)
    assert ignored["changed_paths"] == ()
    assert ignored["staged_paths"] == ()
    assert ignored["ignored_paths"] == ("artifact.cache",)


def test_repository_observation_failures_are_coded(
    fork_framework, monkeypatch, tmp_path
):
    monkeypatch.setattr(
        fork_framework.shutil, "which", lambda *args, **kwargs: None
    )
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_REPOSITORY_GIT_NOT_FOUND",
    ):
        fork_framework.observe_repository_authority(tmp_path)

    monkeypatch.setattr(
        fork_framework.shutil,
        "which",
        lambda *args, **kwargs: "/synthetic/git",
    )

    class Result:
        stdout = b"not-a-commit\n"

    monkeypatch.setattr(
        fork_framework.subprocess, "run", lambda *args, **kwargs: Result()
    )
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_REPOSITORY_IDENTITY_OUTPUT",
    ):
        fork_framework.observe_repository_authority(tmp_path)

    def command_failure(*args, **kwargs):
        raise subprocess.CalledProcessError(2, args[0])

    monkeypatch.setattr(
        fork_framework.subprocess, "run", command_failure
    )
    with pytest.raises(
        fork_framework.ForkFrameworkError,
        match="H09_REPOSITORY_OBSERVATION_FAILED",
    ):
        fork_framework.observe_repository_authority(tmp_path)
