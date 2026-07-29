from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path, PurePosixPath

import pytest

from config.network_profiles import get_profile
import scripts.utils.migration_runner as migration_runner
from scripts.utils.migration_runner import (
    MigrationPlanError,
    ROBINHOOD_RESERVATIONS,
    SourceExpectation,
    build_blocked_migration_report,
    canonical_jcs_bytes,
    discover_migration_sources,
)


ROOT = Path(__file__).resolve().parents[2]


def _source(root: Path, name: str, body: str = "VALUE = 1\n") -> Path:
    path = root / "migrations/robinhood" / name
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _expect(
    migration_id: str,
    semantic_name: str,
    *,
    semantic_id: str | None = None,
    sha256: str | None = None,
) -> SourceExpectation:
    return SourceExpectation(
        migration_id,
        f"{migration_id}_{semantic_name}.py",
        semantic_id or semantic_name.lower(),
        sha256,
    )


def _discover(
    root: Path,
    expectations,
    *,
    require_tracked: bool = False,
    forbid_base_blobs: bool = False,
):
    return discover_migration_sources(
        root,
        PurePosixPath("migrations/robinhood"),
        expectations,
        require_tracked=require_tracked,
        forbid_base_blobs=forbid_base_blobs,
    )


def test_canonical_reservations_are_exact_and_ordered():
    assert [
        (item.migration_id, item.filename, item.disposition)
        for item in ROBINHOOD_RESERVATIONS
    ] == [
        ("0010", "0010_Track6S3LootboxFloor.py", "assertion"),
        ("0020", "0020_Track6S4DeleverageCooldown.py", "omitted"),
        ("0030", "0030_Track6S5LedgerGuard.py", "assertion"),
        (
            "0040",
            "0040_Track6S6DefaultsAndParameters.py",
            "assertion",
        ),
        (
            "0050",
            "0050_Track6S7TimelockRegistryValidation.py",
            "assertion",
        ),
        ("0060", "0060_Track6S8LifecycleCapacity.py", "assertion"),
        (
            "0070",
            "0070_Track6S9DisabledIntegrationAssertions.py",
            "assertion",
        ),
        (
            "0080",
            "0080_Track6S10CadReportAssertion.py",
            "tooling_only",
        ),
        ("0100", "0100_TokensAndRipeHq.py", "blocked"),
        ("0200", "0200_DataAndConfigRegistries.py", "blocked"),
        ("0300", "0300_Switchboards.py", "blocked"),
        ("0400", "0400_PriceSources.py", "blocked"),
        ("0500", "0500_VaultsAndAssets.py", "blocked"),
        ("0600", "0600_CoreDepartments.py", "blocked"),
        ("0700", "0700_SavingsGreenPath.py", "blocked"),
        ("0800", "0800_EndaomentPsmDisabled.py", "blocked"),
        (
            "0900",
            "0900_CapabilitiesRolesAndHandoff.py",
            "blocked",
        ),
        (
            "1000",
            "1000_CcipPoolsAndRegistration.py",
            "deferred",
        ),
    ]


def test_reservations_are_typed_data_not_repository_files():
    for reservation in ROBINHOOD_RESERVATIONS:
        assert not (
            ROOT / "migrations/robinhood" / reservation.filename
        ).exists()
    assert not (ROOT / "migrations/robinhood").exists()


def test_flat_discovery_is_canonical_and_import_free(tmp_path):
    first = _source(
        tmp_path,
        "0010_First.py",
        "raise RuntimeError('must never execute')\n",
    )
    second = _source(
        tmp_path,
        "0020_Second.py",
        "import definitely_missing_h05_module\n",
    )
    result = _discover(
        tmp_path,
        (_expect("0010", "First"), _expect("0020", "Second")),
    )
    assert [item.filename for item in result.members] == [
        first.name,
        second.name,
    ]
    assert [item.sha256 for item in result.members] == [
        hashlib.sha256(first.read_bytes()).hexdigest(),
        hashlib.sha256(second.read_bytes()).hexdigest(),
    ]
    assert len(result.source_digest) == 64


def test_filesystem_enumeration_order_does_not_change_result(tmp_path):
    _source(tmp_path, "0020_Second.py")
    _source(tmp_path, "0010_First.py")
    expected = (_expect("0010", "First"), _expect("0020", "Second"))
    first = _discover(tmp_path, expected)
    second = _discover(tmp_path, expected)
    assert first == second
    assert [item.migration_id for item in first.members] == [
        "0010",
        "0020",
    ]


def test_duplicate_numeric_id_is_rejected_before_set_mismatch(tmp_path):
    _source(tmp_path, "0010_First.py")
    _source(tmp_path, "0010_Second.py")
    with pytest.raises(
        MigrationPlanError, match="H05_DUPLICATE_NUMERIC_ID"
    ):
        _discover(
            tmp_path,
            (_expect("0010", "First"), _expect("0020", "Second")),
        )


def test_duplicate_semantic_name_is_rejected_before_set_mismatch(tmp_path):
    _source(tmp_path, "0010_Same.py")
    _source(tmp_path, "0020_Same.py")
    with pytest.raises(
        MigrationPlanError, match="H05_DUPLICATE_SEMANTIC_ID"
    ):
        _discover(
            tmp_path,
            (_expect("0010", "Same"), _expect("0020", "Other")),
        )


@pytest.mark.parametrize(
    "filename",
    (
        "10_Short.py",
        "00010_Long.py",
        "１２３４_Unicode.py",
        "0010-hyphen.py",
        "0010_lower_name.py",
        "0010_.py",
        "0010_Name.PY",
        "0010_Name.pyc",
        "readme.txt",
    ),
)
def test_noncanonical_filename_grammar_is_rejected(tmp_path, filename):
    _source(tmp_path, filename)
    with pytest.raises(
        MigrationPlanError, match="H05_FILENAME_NONCANONICAL"
    ):
        _discover(tmp_path, (_expect("0010", "Name"),))


@pytest.mark.parametrize(
    "expectations",
    (
        (
            SourceExpectation("010", "010_Bad.py", "bad"),
        ),
        (
            SourceExpectation("0010", "0020_Bad.py", "bad"),
        ),
        (
            SourceExpectation("0020", "0020_Second.py", "second"),
            SourceExpectation("0010", "0010_First.py", "first"),
        ),
        (
            SourceExpectation("0010", "0010_First.py", "same"),
            SourceExpectation("0020", "0020_Second.py", "same"),
        ),
    ),
)
def test_invalid_reservation_ledgers_fail_closed(tmp_path, expectations):
    _source(tmp_path, "0010_First.py")
    with pytest.raises(MigrationPlanError):
        _discover(tmp_path, expectations)


def test_missing_id_is_rejected(tmp_path):
    _source(tmp_path, "0010_First.py")
    with pytest.raises(
        MigrationPlanError, match="H05_SOURCE_SET_MISMATCH"
    ):
        _discover(
            tmp_path,
            (_expect("0010", "First"), _expect("0020", "Second")),
        )


def test_unexpected_id_is_rejected(tmp_path):
    _source(tmp_path, "0010_First.py")
    _source(tmp_path, "0020_Second.py")
    with pytest.raises(
        MigrationPlanError, match="H05_SOURCE_SET_MISMATCH"
    ):
        _discover(tmp_path, (_expect("0010", "First"),))


def test_reservation_gap_alias_is_rejected(tmp_path):
    _source(tmp_path, "0010_First.py")
    _source(tmp_path, "0030_Third.py")
    with pytest.raises(
        MigrationPlanError, match="H05_SOURCE_SET_MISMATCH"
    ):
        _discover(
            tmp_path,
            (_expect("0010", "First"), _expect("0020", "Second")),
        )


@pytest.mark.parametrize(
    "source_root",
    (
        "/absolute",
        "../escape",
        "migrations/../base-mainnet",
        "./migrations/robinhood",
        "migrations//robinhood",
        "migrations/robinhood/",
        r"migrations\robinhood",
        "file://migrations/robinhood",
    ),
)
def test_path_alias_absolute_and_escape_forms_are_rejected(
    tmp_path, source_root
):
    with pytest.raises(MigrationPlanError, match="H05_PATH_INVALID"):
        discover_migration_sources(
            tmp_path,
            source_root,
            (),
            require_tracked=False,
            forbid_base_blobs=False,
        )


def test_source_root_symlink_is_rejected(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    (tmp_path / "migrations").mkdir()
    (tmp_path / "migrations/robinhood").symlink_to(
        target, target_is_directory=True
    )
    with pytest.raises(
        MigrationPlanError, match="H05_SOURCE_ROOT_INVALID"
    ):
        _discover(tmp_path, ())


def test_source_member_symlink_is_rejected(tmp_path):
    outside = tmp_path / "outside.py"
    outside.write_text("VALUE = 1\n")
    source = tmp_path / "migrations/robinhood"
    source.mkdir(mode=0o700, parents=True)
    (source / "0010_First.py").symlink_to(outside)
    with pytest.raises(
        MigrationPlanError, match="H05_SOURCE_SYMLINK"
    ):
        _discover(tmp_path, (_expect("0010", "First"),))


def test_recursive_fallback_is_rejected(tmp_path):
    nested = tmp_path / "migrations/robinhood/nested"
    nested.mkdir(mode=0o700, parents=True)
    _source(tmp_path, "0010_First.py")
    with pytest.raises(
        MigrationPlanError, match="H05_RECURSIVE_SOURCE_FORBIDDEN"
    ):
        _discover(tmp_path, (_expect("0010", "First"),))


def test_invalid_source_syntax_is_rejected_without_import(tmp_path):
    _source(tmp_path, "0010_First.py", "def broken(:\n")
    with pytest.raises(
        MigrationPlanError, match="H05_SOURCE_SYNTAX"
    ):
        _discover(tmp_path, (_expect("0010", "First"),))


def test_base_namespace_is_never_a_robinhood_source(tmp_path):
    with pytest.raises(
        MigrationPlanError, match="H05_BASE_NAMESPACE_FORBIDDEN"
    ):
        discover_migration_sources(
            tmp_path,
            "migrations/base-mainnet",
            (),
            require_tracked=False,
        )


def test_exact_base_blob_is_rejected(tmp_path):
    base = tmp_path / "migrations/base-mainnet/0010_Base.py"
    base.parent.mkdir(mode=0o700, parents=True)
    base.write_text("VALUE = 1\n")
    _source(tmp_path, "0010_First.py", "VALUE = 1\n")
    with pytest.raises(
        MigrationPlanError, match="H05_BASE_BLOB_FORBIDDEN"
    ):
        _discover(
            tmp_path,
            (_expect("0010", "First"),),
            forbid_base_blobs=True,
        )


def test_exact_ledger_semantic_input_is_rejected(tmp_path):
    _source(tmp_path, "0010_Ledger.py")
    with pytest.raises(
        MigrationPlanError, match="H05_BASE_SEMANTIC_FORBIDDEN"
    ):
        _discover(tmp_path, (_expect("0010", "Ledger"),))


def test_expected_byte_hash_mismatch_is_rejected(tmp_path):
    _source(tmp_path, "0010_First.py", "VALUE = 1\n")
    with pytest.raises(
        MigrationPlanError, match="H05_SOURCE_BYTE_MISMATCH"
    ):
        _discover(
            tmp_path,
            (_expect("0010", "First", sha256="00" * 32),),
        )


def test_untracked_source_is_rejected(monkeypatch, tmp_path):
    _source(tmp_path, "0010_First.py")

    def untracked(*_args, **_kwargs):
        raise MigrationPlanError("H05_SOURCE_UNTRACKED")

    monkeypatch.setattr(migration_runner, "_git_blob", untracked)
    with pytest.raises(
        MigrationPlanError, match="H05_SOURCE_UNTRACKED"
    ):
        _discover(
            tmp_path,
            (_expect("0010", "First"),),
            require_tracked=True,
        )


def test_tracked_blob_byte_mismatch_is_rejected(monkeypatch, tmp_path):
    _source(tmp_path, "0010_First.py")
    monkeypatch.setattr(
        migration_runner, "_git_blob", lambda *_args: b"different\n"
    )
    with pytest.raises(
        MigrationPlanError, match="H05_SOURCE_BYTE_MISMATCH"
    ):
        _discover(
            tmp_path,
            (_expect("0010", "First"),),
            require_tracked=True,
        )


def test_source_and_history_collision_fails_before_path_access(
    monkeypatch, tmp_path
):
    original = get_profile("robinhood-mainnet")
    repository = replace(
        original.repository,
        history_dir=original.repository.migration_dir,
    )
    collided = replace(original, repository=repository)
    monkeypatch.setattr(
        "config.network_profiles.get_profile",
        lambda profile_id: (
            collided
            if profile_id == "robinhood-mainnet"
            else get_profile(profile_id)
        ),
    )
    with pytest.raises(
        MigrationPlanError, match="H05_SOURCE_HISTORY_COLLISION"
    ):
        build_blocked_migration_report(
            "robinhood-mainnet", repository_root=tmp_path
        )


def test_history_without_source_is_unverifiable_and_cross_profile(
    monkeypatch, tmp_path
):
    mainnet = get_profile("robinhood-mainnet")
    testnet = get_profile("robinhood-testnet")
    monkeypatch.setattr(
        migration_runner,
        "_git_identity",
        lambda _root: ("11" * 20, "22" * 20),
    )
    other = tmp_path.joinpath(*testnet.repository.history_dir.parts)
    other.mkdir(mode=0o700, parents=True)
    report = build_blocked_migration_report(
        mainnet.identity.profile_id,
        repository_root=tmp_path,
    )
    assert report["source_digest"] is None
    assert report["prior_history_digest"] is None
    assert "B-H06-HISTORY-UNVERIFIABLE" in report["blockers"]
    assert "B-H06-CROSS-PROFILE-HISTORY" in report["blockers"]


def test_current_repository_has_no_robinhood_operational_state():
    forbidden = (
        ROOT / "migrations/robinhood",
        ROOT / "migration_history/robinhood-mainnet",
        ROOT / "migration_history/robinhood-testnet",
    )
    assert all(not path.exists() for path in forbidden)
    names = {
        path.name
        for path in ROOT.rglob("*")
        if path.name
        in {
            ".manifest-v2.lock",
            "current-manifest.json",
        }
        and "robinhood" in path.as_posix()
    }
    assert names == set()


def test_discovery_digest_uses_integer_only_jcs_records(tmp_path):
    path = _source(tmp_path, "0010_First.py")
    result = _discover(tmp_path, (_expect("0010", "First"),))
    expected = hashlib.sha256(
        canonical_jcs_bytes(
            [
                {
                    "migration_id": "0010",
                    "filename": "0010_First.py",
                    "semantic_id": "first",
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            ]
        )
    ).hexdigest()
    assert result.source_digest == expected
