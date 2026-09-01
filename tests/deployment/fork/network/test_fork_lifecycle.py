from __future__ import annotations

import os
from pathlib import Path

import pytest


class FakeProcess:
    next_pid = 1000

    def __init__(self):
        type(self).next_pid += 1
        self.pid = type(self).next_pid
        self.returncode = None

    def poll(self):
        return self.returncode

    def terminate(self):
        self.returncode = 0

    def wait(self, timeout=None):
        assert timeout == 10
        assert self.returncode == 0
        return self.returncode


def runtime(fork_framework, root: Path, factory):
    os.chmod(root, 0o700)
    spec = fork_framework.ForkRuntimeSpec(
        replay_identity="12" * 32,
        engine_name="injected-test-double",
        engine_version="1",
        chain_id=46630,
        block_number=123,
        block_hash="0x" + "34" * 32,
    )
    return fork_framework.DisposableForkRuntime(
        external_root=root,
        repository_root=fork_framework.REPOSITORY_ROOT,
        spec=spec,
        process_factory=factory,
    )


def test_runtime_creation_and_destruction_are_deterministic(
    fork_framework, tmp_path
):
    created = []

    def factory(spec, runtime_dir):
        assert runtime_dir.is_dir()
        created.append((spec, runtime_dir))
        return FakeProcess()

    first = runtime(fork_framework, tmp_path, factory)
    first.create()
    proof = first.destroy()
    assert proof.process_terminated is True
    assert proof.storage_disposed is True
    assert not first.runtime_dir.exists()

    second = runtime(fork_framework, tmp_path, factory)
    assert second.runtime_id == first.runtime_id
    second.create()
    second.destroy()
    assert len(created) == 2


def test_runtime_spec_is_bound_to_accepted_preflight_replay(
    fork_framework, synthetic_disposable_runtime, accepted_preflight
):
    spec = synthetic_disposable_runtime.spec
    owner = accepted_preflight.envelope.owner
    assert spec.chain_id == owner.expected_chain_id
    assert spec.block_number == owner.pin.number
    assert spec.block_hash == owner.pin.block_hash
    assert len(spec.replay_identity) == 64


def test_runtime_residue_fails_closed(fork_framework, tmp_path):
    controller = runtime(
        fork_framework, tmp_path, lambda spec, path: FakeProcess()
    )
    controller.runtime_dir.mkdir(mode=0o700)
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_RUNTIME_RESIDUE"
    ):
        controller.create()


def test_failed_factory_removes_runtime_storage(fork_framework, tmp_path):
    def fail(spec, path):
        raise RuntimeError("synthetic factory failure")

    controller = runtime(fork_framework, tmp_path, fail)
    with pytest.raises(RuntimeError, match="synthetic factory failure"):
        controller.create()
    assert not controller.runtime_dir.exists()


@pytest.mark.parametrize(
    (
        "action",
        "active",
        "local",
        "real_signer",
        "broadcast",
        "expected",
    ),
    (
        ("impersonate", True, True, False, False, None),
        (
            "impersonate",
            False,
            True,
            False,
            False,
            "H09_LOCAL_ACTION_SCOPE",
        ),
        (
            "impersonate",
            True,
            False,
            False,
            False,
            "H09_LOCAL_ACTION_SCOPE",
        ),
        (
            "impersonate",
            True,
            True,
            True,
            False,
            "H09_LOCAL_ACTION_SCOPE",
        ),
        (
            "set_storage",
            True,
            True,
            False,
            True,
            "H09_LOCAL_ACTION_SCOPE",
        ),
        (
            "send_transaction",
            True,
            True,
            False,
            False,
            "H09_LOCAL_ACTION_FORBIDDEN",
        ),
    ),
)
def test_impersonation_and_mutation_are_local_fork_only(
    fork_framework,
    action,
    active,
    local,
    real_signer,
    broadcast,
    expected,
):
    def call():
        fork_framework.validate_local_fork_action(
            action,
            disposable_runtime_active=active,
            targets_local_fork=local,
            requests_real_signer=real_signer,
            requests_broadcast=broadcast,
        )
    if expected is None:
        call()
    else:
        with pytest.raises(
            fork_framework.ForkFrameworkError, match=expected
        ):
            call()
