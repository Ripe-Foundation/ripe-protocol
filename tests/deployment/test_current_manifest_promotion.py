from __future__ import annotations

import copy
import errno
import fcntl
import multiprocessing
import os
from pathlib import Path
import stat
import sys

import pytest

from scripts.utils import json_file
import scripts.utils.manifest_schema as manifest_schema
from scripts.utils.manifest_schema import (
    F_FULLFSYNC,
    ManifestError,
    WriteState,
    _NativeMacOS,
    canonical_json_bytes,
    immutable_basename,
    plan_action_sha256,
    plan_sha256,
    promote_current_index,
    publish_immutable,
    read_history,
    seal_artifact,
)
from tests.deployment.test_manifest_schema import (
    COMMIT,
    TREE,
    make_attempt,
    make_index,
    make_plan,
    make_record,
    make_successor,
    make_two_step_plan,
)

ROOT = Path(__file__).resolve().parents[2]
_publish_immutable = publish_immutable
_promote_current_index = promote_current_index


def publish_immutable(
    history_root, artifact, *, semantic_plans=None, **kwargs
):
    return _publish_immutable(
        history_root,
        artifact,
        semantic_plans=(
            (make_plan(),)
            if semantic_plans is None
            else semantic_plans
        ),
        repository_root=ROOT,
        **kwargs,
    )


def promote_current_index(
    history_root, index, *, semantic_plans=None, **kwargs
):
    return _promote_current_index(
        history_root,
        index,
        semantic_plans=(
            (make_plan(),)
            if semantic_plans is None
            else semantic_plans
        ),
        **kwargs,
    )


def _private_root(tmp_path):
    root = tmp_path / "h06-private-root"
    root.mkdir(mode=0o700, parents=True)
    root.chmod(0o700)
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    return root


def _raise_at(target, calls):
    def fault(point):
        calls.append(point)
        if point == target:
            raise OSError("injected fault")

    return fault


def _two_step_records():
    plan = make_two_step_plan()
    first = make_record(plan=plan)
    second = make_successor(first, plan=plan)
    return plan, first, second


def _publish_child(root, record, queue):
    result = publish_immutable(
        root,
        record,
        expected_prior_record_sha256=None,
    )
    queue.put((result.state.value, result.code))
    queue.close()
    queue.join_thread()


def _promote_child(root, index, queue):
    result = promote_current_index(
        root,
        index,
        expected_prior_index_sha256=None,
    )
    queue.put((result.state.value, result.code))
    queue.close()
    queue.join_thread()


def _close_multiprocessing_resources(processes, queue):
    for process in processes:
        if process.is_alive():
            process.terminate()
        process.join(5)
        process.close()
    queue.close()
    queue.join_thread()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_native_renameatx_np_no_replace_on_local_apfs_without_skip(tmp_path):
    root = _private_root(tmp_path)
    directory_fd = os.open(
        root,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
    )
    try:
        native = _NativeMacOS()
        native.require_apfs(directory_fd)
        first_fd = os.open(
            "first",
            os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        second_fd = os.open(
            "second",
            os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        try:
            os.write(first_fd, b"first")
            os.write(second_fd, b"second")
            os.fsync(first_fd)
            fcntl.fcntl(first_fd, F_FULLFSYNC)
            native.publish_exclusive(directory_fd, "first", "published")
            with pytest.raises(FileExistsError):
                native.publish_exclusive(
                    directory_fd, "second", "published"
                )
            assert os.read(
                os.open(
                    "published",
                    os.O_RDONLY | os.O_NOFOLLOW,
                    dir_fd=directory_fd,
                ),
                5,
            ) == b"first"
            assert os.stat(
                "published",
                dir_fd=directory_fd,
                follow_symlinks=False,
            ).st_ino == os.fstat(first_fd).st_ino
        finally:
            os.close(first_fd)
            os.close(second_fd)
    finally:
        os.close(directory_fd)


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_native_primitive_can_publish_symlink_but_writer_never_supplies_one(
    tmp_path,
):
    root = _private_root(tmp_path)
    directory_fd = os.open(
        root,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
    )
    try:
        native = _NativeMacOS()
        native.require_apfs(directory_fd)
        (root / "referent").write_bytes(b"public")
        os.symlink("referent", root / "untrusted-source")
        native.publish_exclusive(
            directory_fd, "untrusted-source", "published-link"
        )
        published = os.stat(
            "published-link",
            dir_fd=directory_fd,
            follow_symlinks=False,
        )
        assert stat.S_ISLNK(published.st_mode)
    finally:
        os.close(directory_fd)


def test_publication_requires_explicit_valid_plan_before_root_access(
    tmp_path,
):
    record = make_record(plan=make_plan())
    missing_root = tmp_path / "must-not-exist"
    with pytest.raises(TypeError):
        _publish_immutable(
            missing_root,
            record,
            expected_prior_record_sha256=None,
            repository_root=ROOT,
        )
    with pytest.raises(
        ManifestError, match="H06_PLAN_PROOF_REQUIRED"
    ):
        _publish_immutable(
            missing_root,
            record,
            semantic_plans=(),
            expected_prior_record_sha256=None,
            repository_root=ROOT,
        )
    assert not missing_root.exists()


def test_wrong_plan_action_hashes_and_semantics_fail_before_write(tmp_path):
    plan = make_plan()
    digest = plan_sha256(plan)
    base = make_record(plan=plan)
    cases = {}

    arbitrary = copy.deepcopy(base)
    arbitrary["step"]["actions"][0]["transaction"]["request_identity"][
        "plan_action_sha256"
    ] = "cc" * 32
    cases["arbitrary"] = (arbitrary, "H06_PLAN_ACTION_HASH")

    another_action = copy.deepcopy(base)
    another_action["step"]["actions"][0]["transaction"][
        "request_identity"
    ]["plan_action_sha256"] = plan_action_sha256(
        digest, "0900:000001:other-action"
    )
    cases["another-action"] = (
        another_action,
        "H06_PLAN_ACTION_HASH",
    )

    another_plan = copy.deepcopy(base)
    another_plan["step"]["actions"][0]["transaction"]["request_identity"][
        "plan_action_sha256"
    ] = plan_action_sha256(
        plan_sha256(make_two_step_plan()),
        another_plan["step"]["actions"][0]["action_id"],
    )
    cases["another-plan"] = (another_plan, "H06_PLAN_ACTION_HASH")

    altered_semantics = copy.deepcopy(base)
    altered_semantics["step"]["actions"][0]["kind"] = "deployment"
    cases["altered-semantics"] = (
        altered_semantics,
        "H06_PLAN_ACTION_MISMATCH",
    )

    for name, (candidate, error_code) in cases.items():
        root = _private_root(tmp_path / name)
        candidate = seal_artifact(candidate)
        with pytest.raises(ManifestError, match=error_code):
            publish_immutable(
                root,
                candidate,
                semantic_plans=(plan,),
                expected_prior_record_sha256=None,
            )
        assert not list(root.iterdir())


def test_unknown_step_action_and_plan_hash_fail_before_write(tmp_path):
    plan = make_plan()
    base = make_record(plan=plan)

    unknown_step = copy.deepcopy(base)
    unknown_step["step"]["semantic_step_id"] = "unknown-step"
    unknown_step["record_id"] = (
        f"robinhood-mainnet:{base['source']['plan_sha256']}:"
        "0900:unknown-step"
    )
    unknown_step["plan_state"]["completed_step_ids"] = [
        "unknown-step"
    ]
    unknown_step = seal_artifact(unknown_step)

    unknown_action = copy.deepcopy(base)
    action = unknown_action["step"]["actions"][0]
    action["semantic_action_id"] = "unknown-action"
    action["action_id"] = "0900:000000:unknown-action"
    action["transaction"]["request_identity"][
        "semantic_request_id"
    ] = action["action_id"]
    action["transaction"]["request_identity"][
        "plan_action_sha256"
    ] = plan_action_sha256(
        base["source"]["plan_sha256"], action["action_id"]
    )
    unknown_action = seal_artifact(unknown_action)

    wrong_plan = make_record(plan=make_two_step_plan())
    for name, candidate, error_code, plans in (
        (
            "unknown-step",
            unknown_step,
            "H06_PLAN_STEP_IDENTITY",
            (plan,),
        ),
        (
            "unknown-action",
            unknown_action,
            "H06_PLAN_ACTION_UNKNOWN",
            (plan,),
        ),
        (
            "wrong-plan",
            wrong_plan,
            "H06_PLAN_HASH_MISMATCH",
            (plan,),
        ),
    ):
        root = _private_root(tmp_path / name)
        with pytest.raises(ManifestError, match=error_code):
            publish_immutable(
                root,
                candidate,
                semantic_plans=plans,
                expected_prior_record_sha256=None,
            )
        assert not list(root.iterdir())


def test_attempt_record_requires_the_same_plan_action_binding(tmp_path):
    plan = make_plan()
    attempt = make_attempt(plan=plan)
    attempt["step"]["actions"][0]["transaction"]["request_identity"][
        "plan_action_sha256"
    ] = "cc" * 32
    attempt = seal_artifact(attempt)
    root = _private_root(tmp_path)
    with pytest.raises(ManifestError, match="H06_PLAN_ACTION_HASH"):
        publish_immutable(
            root,
            attempt,
            semantic_plans=(plan,),
            expected_prior_record_sha256=None,
        )
    assert not list(root.iterdir())


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_correct_plan_action_hash_publishes_with_mandatory_proof(tmp_path):
    plan = make_plan()
    root = _private_root(tmp_path)
    result = publish_immutable(
        root,
        make_record(plan=plan),
        semantic_plans=(plan,),
        expected_prior_record_sha256=None,
    )
    assert result.state is WriteState.DURABLE


def test_cumulative_plan_state_mutations_fail_before_second_write(tmp_path):
    mutations = {
        "omitted-prior": lambda record: record["plan_state"].update(
            completed_step_ids=["finalize"]
        ),
        "dropped-remaining": lambda record: record["plan_state"].update(
            remaining_required_step_ids=[]
        ),
        "unknown-step": lambda record: record["plan_state"].update(
            remaining_required_step_ids=["finalize", "unknown-step"]
        ),
        "reintroduced-step": lambda record: record["plan_state"].update(
            completed_step_ids=["finalize"],
            remaining_required_step_ids=["configure"],
            status="in-progress",
        ),
        "false-empty-terminal": lambda record: record["plan_state"].update(
            completed_step_ids=["configure"],
            remaining_required_step_ids=[],
            status="complete",
        ),
    }
    for name, mutate in mutations.items():
        plan, first, second = _two_step_records()
        candidate = first if name in {
            "dropped-remaining",
            "unknown-step",
            "false-empty-terminal",
        } else second
        candidate = copy.deepcopy(candidate)
        mutate(candidate)
        candidate = seal_artifact(candidate)
        root = _private_root(tmp_path / name)
        if candidate["step"]["ordinal"] == 1:
            assert publish_immutable(
                root,
                first,
                semantic_plans=(plan,),
                expected_prior_record_sha256=None,
            ).state is WriteState.DURABLE
            prior = first["record_sha256"]
        else:
            prior = None
        with pytest.raises(
            ManifestError,
            match="H06_PLAN_STATE_(MISMATCH|UNKNOWN_STEP)",
        ):
            publish_immutable(
                root,
                candidate,
                semantic_plans=(plan,),
                expected_prior_record_sha256=prior,
            )
        assert not (
            root / immutable_basename(candidate)
        ).exists()


def test_duplicate_completion_and_skipped_ordinal_fail_closed(tmp_path):
    plan, first, second = _two_step_records()
    duplicate = copy.deepcopy(second)
    duplicate["plan_state"]["completed_step_ids"] = [
        "configure",
        "configure",
        "finalize",
    ]
    with pytest.raises(ManifestError):
        seal_artifact(duplicate)

    skipped = copy.deepcopy(second)
    skipped["step"]["ordinal"] = 2
    skipped = seal_artifact(skipped)
    root = _private_root(tmp_path)
    with pytest.raises(ManifestError, match="H06_PLAN_STEP_UNKNOWN"):
        publish_immutable(
            root,
            skipped,
            semantic_plans=(plan,),
            expected_prior_record_sha256=first["record_sha256"],
        )
    assert not list(root.iterdir())


def test_plan_transition_requires_complete_predecessor(tmp_path):
    predecessor = make_two_step_plan()
    first = make_record(plan=predecessor)
    successor_plan = make_plan()
    transition = make_record(plan=successor_plan)
    transition["step"]["previous_record_id"] = first["record_id"]
    transition["step"]["previous_record_sha256"] = first["record_sha256"]
    transition["plan_state"]["predecessor_plan_sha256"] = plan_sha256(
        predecessor
    )
    transition = seal_artifact(transition)
    root = _private_root(tmp_path)
    assert publish_immutable(
        root,
        first,
        semantic_plans=(predecessor,),
        expected_prior_record_sha256=None,
    ).state is WriteState.DURABLE
    with pytest.raises(
        ManifestError, match="H06_PLAN_TRANSITION_INCOMPLETE"
    ):
        publish_immutable(
            root,
            transition,
            semantic_plans=(predecessor, successor_plan),
            expected_prior_record_sha256=first["record_sha256"],
        )
    assert not (root / immutable_basename(transition)).exists()


def test_promotion_revalidates_injected_chain_against_full_plan(tmp_path):
    plan, first, second = _two_step_records()
    invalid = copy.deepcopy(second)
    invalid["plan_state"]["completed_step_ids"] = ["finalize"]
    invalid = seal_artifact(invalid)
    root = _private_root(tmp_path)
    (root / immutable_basename(first)).write_bytes(
        canonical_json_bytes(first)
    )
    (root / immutable_basename(invalid)).write_bytes(
        canonical_json_bytes(invalid)
    )
    index = make_index(invalid)
    with pytest.raises(ManifestError, match="H06_PLAN_STATE_MISMATCH"):
        promote_current_index(
            root,
            index,
            semantic_plans=(plan,),
            expected_prior_index_sha256=None,
        )
    assert not (root / "current-manifest.json").exists()


def test_promotion_cannot_bypass_semantic_plan_proof(tmp_path):
    plan = make_plan()
    record = make_record(plan=plan)
    root = _private_root(tmp_path)
    assert publish_immutable(
        root,
        record,
        semantic_plans=(plan,),
        expected_prior_record_sha256=None,
    ).state is WriteState.DURABLE
    with pytest.raises(
        ManifestError, match="H06_PLAN_PROOF_REQUIRED"
    ):
        _promote_current_index(
            root,
            make_index(record),
            semantic_plans=(),
            expected_prior_index_sha256=None,
        )
    assert not (root / "current-manifest.json").exists()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_immutable_writer_exact_durability_order_and_identity(tmp_path):
    root = _private_root(tmp_path)
    record = make_record()
    calls = []
    result = publish_immutable(
        root,
        record,
        expected_prior_record_sha256=None,
        fault=lambda point: calls.append(point),
    )
    assert result.state is WriteState.DURABLE
    assert result.code == "H06_IMMUTABLE_DURABLE"
    assert calls == [
        "after_lock",
        "before_temp_create",
        "after_temp_create",
        "after_write",
        "after_file_fsync",
        "after_file_fullfsync",
        "after_reread",
        "before_publish",
        "after_publish",
        "after_directory_fsync",
        "after_final_fullfsync",
        "after_final_identity",
    ]
    target = root / immutable_basename(record)
    assert target.read_bytes() == canonical_json_bytes(record)
    assert target.is_file()
    assert target.stat().st_nlink == 1
    assert not list(root.glob(".*.tmp.*"))


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
@pytest.mark.parametrize(
    "fault_point",
    (
        "before_temp_create",
        "after_temp_create",
        "after_write",
        "after_file_fsync",
        "after_file_fullfsync",
        "after_reread",
        "before_publish",
    ),
)
def test_prepublication_faults_never_expose_partial_canonical_file(
    tmp_path, fault_point
):
    root = _private_root(tmp_path)
    record = make_record()
    result = publish_immutable(
        root,
        record,
        expected_prior_record_sha256=None,
        fault=_raise_at(fault_point, []),
    )
    assert result.state is WriteState.PRE_PUBLICATION_FAILURE
    assert not (root / immutable_basename(record)).exists()
    assert not list(root.glob(".*.tmp.*"))


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_direct_short_write_is_completed_without_truncation(
    monkeypatch, tmp_path
):
    root = _private_root(tmp_path)
    record = make_record()
    real_write = json_file.os.write
    calls = []

    def short_write(fd, data):
        calls.append(len(data))
        return real_write(fd, data[: max(1, len(data) // 3)])

    monkeypatch.setattr(json_file.os, "write", short_write)
    result = publish_immutable(
        root, record, expected_prior_record_sha256=None
    )
    assert result.state is WriteState.DURABLE
    assert len(calls) > 1
    assert (root / immutable_basename(record)).read_bytes() == (
        canonical_json_bytes(record)
    )


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
@pytest.mark.parametrize("failure", ("write", "read"))
def test_direct_write_and_read_failures_are_prepublication(
    monkeypatch, tmp_path, failure
):
    root = _private_root(tmp_path)
    record = make_record()

    def fail(*_args, **_kwargs):
        raise OSError(errno.EIO, "injected primitive failure")

    monkeypatch.setattr(
        json_file,
        "write_all" if failure == "write" else "read_all",
        fail,
    )
    result = publish_immutable(
        root, record, expected_prior_record_sha256=None
    )
    assert result.state is WriteState.PRE_PUBLICATION_FAILURE
    assert not (root / immutable_basename(record)).exists()
    assert not list(root.glob(".*.tmp.*"))


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_direct_readback_byte_change_fails_before_publish(
    monkeypatch, tmp_path
):
    root = _private_root(tmp_path)
    record = make_record()
    real_read_all = json_file.read_all

    def changed(fd, **kwargs):
        return real_read_all(fd, **kwargs) + b"x"

    monkeypatch.setattr(json_file, "read_all", changed)
    with pytest.raises(ManifestError, match="H06_TEMP_BYTES_MISMATCH"):
        publish_immutable(
            root, record, expected_prior_record_sha256=None
        )
    assert not (root / immutable_basename(record)).exists()
    assert not list(root.glob(".*.tmp.*"))


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_direct_file_fsync_failure_is_prepublication(
    monkeypatch, tmp_path
):
    root = _private_root(tmp_path)
    record = make_record()
    real_fsync = manifest_schema.os.fsync

    def fail_regular(fd):
        if stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError(errno.EIO, "injected file fsync failure")
        return real_fsync(fd)

    monkeypatch.setattr(manifest_schema.os, "fsync", fail_regular)
    result = publish_immutable(
        root, record, expected_prior_record_sha256=None
    )
    assert result.state is WriteState.PRE_PUBLICATION_FAILURE
    assert not (root / immutable_basename(record)).exists()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_direct_full_fsync_failure_is_prepublication(
    monkeypatch, tmp_path
):
    root = _private_root(tmp_path)
    record = make_record()

    def fail(_fd):
        raise OSError(errno.EIO, "injected F_FULLFSYNC failure")

    monkeypatch.setattr(
        _NativeMacOS, "full_fsync", staticmethod(fail)
    )
    result = publish_immutable(
        root, record, expected_prior_record_sha256=None
    )
    assert result.state is WriteState.PRE_PUBLICATION_FAILURE
    assert not (root / immutable_basename(record)).exists()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
@pytest.mark.parametrize(
    "error_number",
    (
        errno.EXDEV,
        errno.EIO,
        errno.EPERM,
        errno.EINVAL,
        getattr(errno, "ENOTSUP", errno.EOPNOTSUPP),
    ),
)
def test_direct_native_rename_errno_classes_fail_before_publication(
    monkeypatch, tmp_path, error_number
):
    root = _private_root(tmp_path)
    record = make_record()

    def fail(*_args):
        raise OSError(error_number, os.strerror(error_number))

    monkeypatch.setattr(_NativeMacOS, "publish_exclusive", fail)
    result = publish_immutable(
        root, record, expected_prior_record_sha256=None
    )
    assert result.state is WriteState.PRE_PUBLICATION_FAILURE
    assert result.code == "H06_NATIVE_PUBLICATION_FAILURE"
    assert not (root / immutable_basename(record)).exists()
    assert not list(root.glob(".*.tmp.*"))


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_direct_directory_fsync_failure_never_returns_success(
    monkeypatch, tmp_path
):
    root = _private_root(tmp_path)
    record = make_record()
    real_fsync = manifest_schema.os.fsync

    def fail_directory(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError(errno.EIO, "injected directory fsync failure")
        return real_fsync(fd)

    monkeypatch.setattr(manifest_schema.os, "fsync", fail_directory)
    result = publish_immutable(
        root, record, expected_prior_record_sha256=None
    )
    assert result.state is WriteState.DURABILITY_AMBIGUITY
    assert result.code == "H06_POST_RENAME_DURABILITY_AMBIGUOUS"
    assert (root / immutable_basename(record)).is_file()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_direct_mismatching_native_collision_never_overwrites(
    monkeypatch, tmp_path
):
    root = _private_root(tmp_path)
    record = make_record()
    attacker_bytes = b"not-the-candidate"

    def collide(_native, directory_fd, _temporary, final):
        fd = os.open(
            final,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        try:
            os.write(fd, attacker_bytes)
        finally:
            os.close(fd)
        raise FileExistsError(errno.EEXIST, "injected collision")

    monkeypatch.setattr(_NativeMacOS, "publish_exclusive", collide)
    result = publish_immutable(
        root, record, expected_prior_record_sha256=None
    )
    assert result.state is WriteState.COLLISION
    assert (root / immutable_basename(record)).read_bytes() == (
        attacker_bytes
    )


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
@pytest.mark.parametrize(
    "replacement_kind", ("fifo", "symlink", "regular")
)
def test_source_swap_nonregular_and_held_identity_fail_closed(
    tmp_path, replacement_kind
):
    root = _private_root(tmp_path)
    record = make_record()
    swapped = None

    def swap(point):
        nonlocal swapped
        if point != "before_publish":
            return
        swapped = next(root.glob(".*.tmp.*"))
        swapped.unlink()
        if replacement_kind == "fifo":
            os.mkfifo(swapped, mode=0o600)
        elif replacement_kind == "symlink":
            swapped.symlink_to("missing-target")
        else:
            swapped.write_bytes(b"replacement")
            swapped.chmod(0o600)

    try:
        result = publish_immutable(
            root,
            record,
            expected_prior_record_sha256=None,
            fault=swap,
        )
        assert result.state is WriteState.CLEANUP_AMBIGUITY
        assert result.code == "H06_CLEANUP_AMBIGUOUS"
        assert not (root / immutable_basename(record)).exists()
        assert swapped is not None
        assert os.path.lexists(swapped)
    finally:
        if swapped is not None and os.path.lexists(swapped):
            swapped.unlink()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
@pytest.mark.parametrize(
    "nonregular_mode",
    (stat.S_IFCHR, stat.S_IFSOCK),
    ids=("device", "socket"),
)
def test_nonregular_mode_mutation_at_stat_boundary_fails_closed(
    monkeypatch, tmp_path, nonregular_mode
):
    root = _private_root(tmp_path)
    record = make_record()
    real_stat = manifest_schema.os.stat
    mutate = False

    def fake_device(path, *args, **kwargs):
        result = real_stat(path, *args, **kwargs)
        if (
            mutate
            and isinstance(path, str)
            and ".tmp." in path
            and kwargs.get("dir_fd") is not None
        ):
            values = list(result)
            values[0] = nonregular_mode | 0o600
            return os.stat_result(values)
        return result

    def arm(point):
        nonlocal mutate
        if point == "before_publish":
            mutate = True

    monkeypatch.setattr(manifest_schema.os, "stat", fake_device)
    result = publish_immutable(
        root,
        record,
        expected_prior_record_sha256=None,
        fault=arm,
    )
    assert result.state is WriteState.CLEANUP_AMBIGUITY
    assert not (root / immutable_basename(record)).exists()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_direct_cleanup_unlink_failure_is_distinct_ambiguity(
    monkeypatch, tmp_path
):
    root = _private_root(tmp_path)
    record = make_record()

    def fail_write(*_args):
        raise OSError(errno.EIO, "injected write failure")

    def fail_unlink(*_args, **_kwargs):
        raise OSError(errno.EPERM, "injected unlink failure")

    monkeypatch.setattr(json_file, "write_all", fail_write)
    monkeypatch.setattr(manifest_schema.os, "unlink", fail_unlink)
    result = publish_immutable(
        root, record, expected_prior_record_sha256=None
    )
    assert result.state is WriteState.CLEANUP_AMBIGUITY
    assert result.code == "H06_CLEANUP_AMBIGUOUS"
    assert not (root / immutable_basename(record)).exists()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_direct_lock_acquisition_failure_is_typed_and_write_free(
    monkeypatch, tmp_path
):
    root = _private_root(tmp_path)
    record = make_record()

    def fail(_directory_fd):
        raise OSError(errno.EACCES, "injected lock failure")

    monkeypatch.setattr(manifest_schema, "_acquire_writer_lock", fail)
    result = publish_immutable(
        root, record, expected_prior_record_sha256=None
    )
    assert result.state is WriteState.PRE_PUBLICATION_FAILURE
    assert result.code == "H06_LOCK_PERMISSION_FAILURE"
    assert not list(root.iterdir())


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_direct_lock_release_failure_never_returns_false_success(
    monkeypatch, tmp_path
):
    root = _private_root(tmp_path)
    record = make_record()
    real_flock = manifest_schema.fcntl.flock

    def fail_unlock(fd, operation):
        if operation == fcntl.LOCK_UN:
            raise OSError(errno.EIO, "injected unlock failure")
        return real_flock(fd, operation)

    monkeypatch.setattr(manifest_schema.fcntl, "flock", fail_unlock)
    with pytest.raises(OSError, match="injected unlock failure"):
        publish_immutable(
            root, record, expected_prior_record_sha256=None
        )
    assert (root / immutable_basename(record)).is_file()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_post_publish_fault_is_truthful_publication_ambiguity(tmp_path):
    root = _private_root(tmp_path)
    record = make_record()
    result = publish_immutable(
        root,
        record,
        expected_prior_record_sha256=None,
        fault=_raise_at("after_publish", []),
    )
    assert result.state is WriteState.PUBLICATION_AMBIGUITY
    assert result.code == "H06_PUBLICATION_AMBIGUOUS"
    assert (root / immutable_basename(record)).read_bytes() == (
        canonical_json_bytes(record)
    )


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_prepublication_cleanup_failure_is_distinct_ambiguity(tmp_path):
    root = _private_root(tmp_path)
    record = make_record()

    def fault(point):
        if point in {"after_write", "before_cleanup"}:
            raise OSError("injected cleanup fault")

    result = publish_immutable(
        root,
        record,
        expected_prior_record_sha256=None,
        fault=fault,
    )
    assert result.state is WriteState.CLEANUP_AMBIGUITY
    assert result.code == "H06_CLEANUP_AMBIGUOUS"
    assert not (root / immutable_basename(record)).exists()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
@pytest.mark.parametrize(
    "fault_point",
    ("after_directory_fsync", "after_final_fullfsync"),
)
def test_post_rename_sync_fault_is_durability_ambiguity(
    tmp_path, fault_point
):
    root = _private_root(tmp_path)
    record = make_record()
    result = publish_immutable(
        root,
        record,
        expected_prior_record_sha256=None,
        fault=_raise_at(fault_point, []),
    )
    assert result.state is WriteState.DURABILITY_AMBIGUITY
    assert result.code == "H06_POST_RENAME_DURABILITY_AMBIGUOUS"
    assert (root / immutable_basename(record)).is_file()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_final_revalidation_fault_is_not_success(tmp_path):
    root = _private_root(tmp_path)
    record = make_record()
    result = publish_immutable(
        root,
        record,
        expected_prior_record_sha256=None,
        fault=_raise_at("after_final_identity", []),
    )
    assert result.state is WriteState.FINAL_IDENTITY_MISMATCH
    assert result.code == "H06_FINAL_IDENTITY_MISMATCH"


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_exact_existing_record_is_idempotent_and_never_rewritten(tmp_path):
    root = _private_root(tmp_path)
    record = make_record()
    first = publish_immutable(
        root, record, expected_prior_record_sha256=None
    )
    path = root / immutable_basename(record)
    before = (
        path.stat().st_ino,
        path.stat().st_mtime_ns,
        path.read_bytes(),
    )
    second = publish_immutable(
        root, record, expected_prior_record_sha256=None
    )
    after = (
        path.stat().st_ino,
        path.stat().st_mtime_ns,
        path.read_bytes(),
    )
    assert first.state is WriteState.DURABLE
    assert second.state is WriteState.ALREADY_PRESENT
    assert after == before


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_two_concurrent_immutable_writers_have_one_durable_identity(tmp_path):
    root = _private_root(tmp_path)
    record = make_record()
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    processes = [
        context.Process(target=_publish_child, args=(root, record, queue))
        for _ in range(2)
    ]
    started = []
    try:
        for process in processes:
            process.start()
            started.append(process)
        for process in started:
            process.join(30)
            assert process.exitcode == 0
        results = [queue.get(timeout=5) for _ in started]
        states = sorted(item[0] for item in results)
        assert states == ["already-present", "durable"], results
        assert (root / immutable_basename(record)).read_bytes() == (
            canonical_json_bytes(record)
        )
    finally:
        _close_multiprocessing_resources(started, queue)


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_stale_prior_record_never_writes(tmp_path):
    root = _private_root(tmp_path)
    record = make_record()
    result = publish_immutable(
        root,
        record,
        expected_prior_record_sha256="aa" * 32,
    )
    assert result.state is WriteState.STALE_PRIOR
    assert not list(root.iterdir())


def test_linux_and_non_macos_platforms_fail_closed(monkeypatch, tmp_path):
    root = _private_root(tmp_path)
    monkeypatch.setattr(
        "scripts.utils.manifest_schema.sys.platform", "linux"
    )
    with pytest.raises(ManifestError, match="H06_PLATFORM_UNSUPPORTED"):
        publish_immutable(
            root,
            make_record(),
            expected_prior_record_sha256=None,
        )
    assert not list(root.iterdir())


def test_root_mode_and_root_symlink_are_rejected(tmp_path):
    record = make_record()
    broad = tmp_path / "broad"
    broad.mkdir(mode=0o755)
    broad.chmod(0o755)
    with pytest.raises(ManifestError, match="H06_HISTORY_ROOT_MODE"):
        publish_immutable(
            broad,
            record,
            expected_prior_record_sha256=None,
        )
    read_result = read_history(
        "robinhood-mainnet",
        4663,
        record["source"]["plan_sha256"],
        COMMIT,
        TREE,
        broad,
    )
    assert read_result.state.value == "corrupt"
    assert read_result.code == "H06_HISTORY_ROOT_MODE"
    real = _private_root(tmp_path)
    link = tmp_path / "linked"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ManifestError, match="H06_HISTORY_ROOT_INVALID"):
        publish_immutable(
            link,
            record,
            expected_prior_record_sha256=None,
        )


def test_reader_and_writer_reject_symlink_and_hardlinked_lock(tmp_path):
    root = _private_root(tmp_path)
    record = make_record()
    outside = tmp_path / "outside-lock"
    outside.touch(mode=0o600)
    outside.chmod(0o600)
    lock = root / ".manifest-v2.lock"

    lock.symlink_to(outside)
    read_result = read_history(
        "robinhood-mainnet",
        4663,
        record["source"]["plan_sha256"],
        COMMIT,
        TREE,
        root,
    )
    assert read_result.state.value == "corrupt"
    write_result = publish_immutable(
        root,
        record,
        expected_prior_record_sha256=None,
    )
    assert write_result.state is WriteState.PRE_PUBLICATION_FAILURE
    assert write_result.code == "H06_LOCK_SYMLINK"

    lock.unlink()
    os.link(outside, lock)
    read_result = read_history(
        "robinhood-mainnet",
        4663,
        record["source"]["plan_sha256"],
        COMMIT,
        TREE,
        root,
    )
    assert read_result.state.value == "corrupt"
    assert read_result.code == "H06_LOCK_INVALID"
    with pytest.raises(ManifestError, match="H06_LOCK_INVALID"):
        publish_immutable(
            root,
            record,
            expected_prior_record_sha256=None,
        )
    assert not (root / immutable_basename(record)).exists()


def test_reader_rejects_symlink_and_hardlinked_immutable_target(tmp_path):
    root = _private_root(tmp_path)
    record = make_record()
    outside = tmp_path / "outside"
    outside.write_bytes(canonical_json_bytes(record))
    (root / immutable_basename(record)).symlink_to(outside)
    result = read_history(
        "robinhood-mainnet",
        4663,
        record["source"]["plan_sha256"],
        COMMIT,
        TREE,
        root,
    )
    assert result.state.value == "corrupt"

    (root / immutable_basename(record)).unlink()
    os.link(outside, root / immutable_basename(record))
    result = read_history(
        "robinhood-mainnet",
        4663,
        record["source"]["plan_sha256"],
        COMMIT,
        TREE,
        root,
    )
    assert result.state.value == "corrupt"


def test_reader_never_creates_lock_and_classifies_held_lock_ambiguous(
    tmp_path,
):
    root = _private_root(tmp_path)
    absent = read_history(
        "robinhood-mainnet",
        4663,
        "aa" * 32,
        COMMIT,
        TREE,
        root,
    )
    assert absent.state.value == "absent-clean"
    assert list(root.iterdir()) == []
    lock = root / ".manifest-v2.lock"
    lock.touch(mode=0o600)
    lock.chmod(0o600)
    fd = os.open(lock, os.O_RDWR | os.O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        held = read_history(
            "robinhood-mainnet",
            4663,
            "aa" * 32,
            COMMIT,
            TREE,
            root,
        )
        assert held.state.value == "ambiguous"
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    clean = read_history(
        "robinhood-mainnet",
        4663,
        "aa" * 32,
        COMMIT,
        TREE,
        root,
    )
    assert clean.state.value == "absent-clean"
    assert [path.name for path in root.iterdir()] == [
        ".manifest-v2.lock"
    ]


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_complete_chain_promotes_current_and_reader_validates(tmp_path):
    root = _private_root(tmp_path)
    record = make_record()
    assert publish_immutable(
        root, record, expected_prior_record_sha256=None
    ).state is WriteState.DURABLE
    index = make_index(record)
    result = promote_current_index(
        root,
        index,
        expected_prior_index_sha256=None,
    )
    assert result.state is WriteState.DURABLE
    assert result.code == "H06_CURRENT_PROMOTED"
    assert (root / "current-manifest.json").read_bytes() == (
        canonical_json_bytes(index)
    )
    history = read_history(
        "robinhood-mainnet",
        4663,
        record["source"]["plan_sha256"],
        COMMIT,
        TREE,
        root,
    )
    assert history.state.value == "valid"


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_incomplete_plan_never_promotes_current(tmp_path):
    root = _private_root(tmp_path)
    plan = make_two_step_plan()
    record = make_record(plan=plan)
    assert publish_immutable(
        root,
        record,
        semantic_plans=(plan,),
        expected_prior_record_sha256=None,
    ).state is WriteState.DURABLE
    index = make_index(record)
    with pytest.raises(
        ManifestError, match="H06_PROMOTION_PLAN_INCOMPLETE"
    ):
        promote_current_index(
            root,
            index,
            semantic_plans=(plan,),
            expected_prior_index_sha256=None,
        )
    assert not (root / "current-manifest.json").exists()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_failed_pending_and_unreconciled_mutations_never_publish_or_promote(
    tmp_path,
):
    root = _private_root(tmp_path)
    for status in (
        "failed",
        "submitted",
        "confirmed",
        "finality-pending",
        "blocked",
    ):
        record = make_record()
        record["step"]["actions"][0]["status"] = status
        with pytest.raises(ManifestError):
            publish_immutable(
                root,
                record,
                expected_prior_record_sha256=None,
            )
    assert not list(root.iterdir())


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_stale_current_prior_never_replaces_index(tmp_path):
    root = _private_root(tmp_path)
    record = make_record()
    publish_immutable(
        root, record, expected_prior_record_sha256=None
    )
    index = make_index(record)
    promote_current_index(
        root, index, expected_prior_index_sha256=None
    )
    replacement = make_index(record, prior="ff" * 32)
    result = promote_current_index(
        root,
        replacement,
        expected_prior_index_sha256="ff" * 32,
    )
    assert result.state is WriteState.STALE_PRIOR
    assert (root / "current-manifest.json").read_bytes() == (
        canonical_json_bytes(index)
    )


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_two_concurrent_first_promotions_have_one_winner(tmp_path):
    root = _private_root(tmp_path)
    record = make_record()
    publish_immutable(
        root, record, expected_prior_record_sha256=None
    )
    index = make_index(record)
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    processes = [
        context.Process(target=_promote_child, args=(root, index, queue))
        for _ in range(2)
    ]
    started = []
    try:
        for process in processes:
            process.start()
            started.append(process)
        for process in started:
            process.join(30)
            assert process.exitcode == 0
        states = sorted(queue.get(timeout=5)[0] for _ in started)
        assert states == ["durable", "stale-prior"]
    finally:
        _close_multiprocessing_resources(started, queue)


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only H-06 release")
def test_current_post_replace_and_directory_sync_faults_are_ambiguous(
    tmp_path,
):
    for fault_point in (
        "after_current_replace",
        "after_current_directory_fsync",
    ):
        root = _private_root(tmp_path / fault_point)
        record = make_record()
        publish_immutable(
            root, record, expected_prior_record_sha256=None
        )
        index = make_index(record)
        result = promote_current_index(
            root,
            index,
            expected_prior_index_sha256=None,
            fault=_raise_at(fault_point, []),
        )
        assert result.state in {
            WriteState.PUBLICATION_AMBIGUITY,
            WriteState.DURABILITY_AMBIGUITY,
        }
        assert result.code == "H06_CURRENT_PROMOTION_AMBIGUOUS"
        assert (root / "current-manifest.json").read_bytes() == (
            canonical_json_bytes(index)
        )


def test_path_escape_and_nonbasename_current_targets_are_rejected():
    record = make_record()
    for path in (
        "../current",
        "/absolute",
        "nested/target",
        r"nested\target",
        "file://target",
    ):
        index = make_index(record)
        index["target"]["path"] = path
        with pytest.raises(ManifestError):
            promote_current_index(
                "/not-accessed",
                index,
                expected_prior_index_sha256=None,
            )


def test_immutable_writer_has_no_fallback_and_current_replace_is_isolated():
    source = (
        Path(__file__).resolve().parents[2]
        / "scripts/utils/manifest_schema.py"
    ).read_text()
    assert "os.rename(" not in source
    assert "os.link(" not in source
    assert "os.replace(" in source
    assert source.count("os.replace(") == 1
    assert "renameat2" not in source
    assert "syscall(" not in source
    replace_location = source.index("os.replace(")
    promotion_location = source.index("def promote_current_index(")
    assert replace_location > promotion_location
