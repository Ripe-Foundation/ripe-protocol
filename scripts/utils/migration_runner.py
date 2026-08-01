from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import importlib.util
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import Any, Mapping, Sequence, TYPE_CHECKING

from scripts.utils import log

if TYPE_CHECKING:
    from scripts.utils.deploy_args import DeployArgs


class MigrationPlanError(ValueError):
    """Stable, sanitized H-05 discovery or planning failure."""

    def __init__(self, code: str):
        if re.fullmatch(r"H05_[A-Z0-9_]+", code) is None:
            raise ValueError("invalid H-05 error code")
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class MigrationReservation:
    migration_id: str
    filename: str
    semantic_id: str
    disposition: str
    local_blockers: tuple[str, ...] = ()
    input_bindings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SourceExpectation:
    migration_id: str
    filename: str
    semantic_id: str
    sha256: str | None = None


@dataclass(frozen=True, slots=True)
class DiscoveredSource:
    migration_id: str
    filename: str
    semantic_id: str
    sha256: str


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    members: tuple[DiscoveredSource, ...]
    source_digest: str


ROBINHOOD_RESERVATIONS: tuple[MigrationReservation, ...] = (
    MigrationReservation(
        "0010",
        "0010_Track6S3LootboxFloor.py",
        "track6-s3-lootbox-floor",
        "assertion",
    ),
    MigrationReservation(
        "0020",
        "0020_Track6S4DeleverageCooldown.py",
        "track6-s4-deleverage-cooldown",
        "omitted",
    ),
    MigrationReservation(
        "0030",
        "0030_Track6S5LedgerGuard.py",
        "track6-s5-ledger-guard",
        "assertion",
    ),
    MigrationReservation(
        "0040",
        "0040_Track6S6DefaultsAndParameters.py",
        "track6-s6-defaults-and-parameters",
        "assertion",
    ),
    MigrationReservation(
        "0050",
        "0050_Track6S7TimelockRegistryValidation.py",
        "track6-s7-timelock-registry-validation",
        "assertion",
    ),
    MigrationReservation(
        "0060",
        "0060_Track6S8LifecycleCapacity.py",
        "track6-s8-lifecycle-capacity",
        "assertion",
    ),
    MigrationReservation(
        "0070",
        "0070_Track6S9DisabledIntegrationAssertions.py",
        "track6-s9-disabled-integration-assertions",
        "assertion",
    ),
    MigrationReservation(
        "0080",
        "0080_Track6S10CadReportAssertion.py",
        "track6-s10-cad-report-assertion",
        "tooling_only",
    ),
    MigrationReservation(
        "0100",
        "0100_TokensAndRipeHq.py",
        "tokens-and-ripe-hq",
        "blocked",
    ),
    MigrationReservation(
        "0200",
        "0200_DataAndConfigRegistries.py",
        "data-and-config-registries",
        "blocked",
    ),
    MigrationReservation(
        "0300",
        "0300_Switchboards.py",
        "switchboards",
        "blocked",
    ),
    MigrationReservation(
        "0400",
        "0400_PriceSources.py",
        "price-sources",
        "blocked",
    ),
    MigrationReservation(
        "0500",
        "0500_VaultsAndAssets.py",
        "vaults-and-assets",
        "blocked",
        ("B-T8-FREEZE", "B-T8-M5"),
        (
            "Deployment.DP-10.aapl.identity",
            "Deployment.DP-10.aapl.feed",
            "Deployment.DP-10.aapl.decimals",
            "Deployment.DP-10.aapl.P8",
            "Deployment.DP-10.aapl.perUserCap",
            "Deployment.DP-10.aapl.globalCap",
            "Deployment.DP-10.aapl.vault",
            "Deployment.DP-10.aapl.risk",
            "Deployment.DP-10.aapl.auction",
            "Deployment.DP-10.aapl.route",
            "Deployment.DP-11.stock.vaultArtifact",
            "Deployment.DP-11.stock.vaultSlot",
            "Deployment.DP-11.stock.m2Movement",
            "Deployment.DP-11.stock.m3CreditContainment",
            "Deployment.DP-11.stock.m4ComposedProof",
            "Deployment.DP-11.stock.m5ActivationBinding",
        ),
    ),
    MigrationReservation(
        "0600",
        "0600_CoreDepartments.py",
        "core-departments",
        "blocked",
        ("B-REWARD-PROMOTION",),
    ),
    MigrationReservation(
        "0700",
        "0700_SavingsGreenPath.py",
        "savings-green-path",
        "blocked",
    ),
    MigrationReservation(
        "0800",
        "0800_EndaomentPsmDisabled.py",
        "endaoment-psm-disabled",
        "blocked",
        ("B-PSM-SEQUENCE",),
    ),
    MigrationReservation(
        "0900",
        "0900_CapabilitiesRolesAndHandoff.py",
        "capabilities-roles-and-handoff",
        "blocked",
    ),
    MigrationReservation(
        "1000",
        "1000_CcipPoolsAndRegistration.py",
        "ccip-pools-and-registration",
        "deferred",
        ("B-T1-CCIP", "B-T1-TOOLCHAIN"),
    ),
)

_CURRENT_GLOBAL_BLOCKERS = (
    "B-H04-PARAMS",
    "B-H05-PLAN",
    "B-H05-SOURCE-ABSENT",
    "B-H06-HISTORIES-ABSENT",
    "B-H08-PROOF",
    "B-H09-RELEASE",
    "B-LP-ARTIFACTS",
    "B-ORACLE-FREEZE",
    "B-S5-LEDGER",
    "B-SECOPS-HANDOFF",
)
_REPORT_SCHEMA = "ripe.robinhood.migration-dry-plan.v2"
_CANONICAL_FILENAME = re.compile(
    r"(?P<migration_id>[0-9]{4})_"
    r"(?P<semantic_name>[A-Za-z][A-Za-z0-9]*)\.py",
    re.ASCII,
)
_HEX64 = re.compile(r"[0-9a-f]{64}", re.ASCII)
_GIT = "/usr/bin/git"
_GIT_ENV = {"LANG": "C", "LC_ALL": "C"}


def _validate_unicode_string(value: str) -> None:
    try:
        value.encode("utf-8", "strict")
        value.encode("utf-16-be", "strict")
    except UnicodeEncodeError as error:
        raise MigrationPlanError("H05_JCS_UNICODE") from error


def _jcs_string(value: str) -> str:
    _validate_unicode_string(value)
    pieces = ['"']
    short_escapes = {
        "\b": "\\b",
        "\t": "\\t",
        "\n": "\\n",
        "\f": "\\f",
        "\r": "\\r",
        '"': '\\"',
        "\\": "\\\\",
    }
    for character in value:
        if character in short_escapes:
            pieces.append(short_escapes[character])
        elif ord(character) < 0x20:
            pieces.append(f"\\u{ord(character):04x}")
        else:
            pieces.append(character)
    pieces.append('"')
    return "".join(pieces)


def _jcs_text(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        raise MigrationPlanError("H05_JCS_FLOAT_FORBIDDEN")
    if isinstance(value, str):
        return _jcs_string(value)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_jcs_text(item) for item in value) + "]"
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise MigrationPlanError("H05_JCS_KEY_TYPE")
        for key in value:
            _validate_unicode_string(key)
        keys = sorted(value, key=lambda key: key.encode("utf-16-be"))
        return (
            "{"
            + ",".join(
                f"{_jcs_string(key)}:{_jcs_text(value[key])}"
                for key in keys
            )
            + "}"
        )
    raise MigrationPlanError("H05_JCS_TYPE")


def canonical_jcs_bytes(value: Any) -> bytes:
    """Canonicalize the integer-only H-05 JSON domain without a final LF."""

    return _jcs_text(value).encode("utf-8")


def report_bytes(report: Mapping[str, Any]) -> bytes:
    """Seal a report with its H-05 self-hash and one terminal LF."""

    unsigned = dict(report)
    unsigned.pop("report_sha256", None)
    digest = hashlib.sha256(canonical_jcs_bytes(unsigned)).hexdigest()
    sealed = dict(unsigned)
    sealed["report_sha256"] = digest
    return canonical_jcs_bytes(sealed) + b"\n"


def report_sha256(report: Mapping[str, Any]) -> str:
    """Return the report self-hash without confusing it with H-06 plan_sha256."""

    unsigned = dict(report)
    unsigned.pop("report_sha256", None)
    return hashlib.sha256(canonical_jcs_bytes(unsigned)).hexdigest()


def _reservation_records() -> list[dict[str, Any]]:
    return [
        {
            "migration_id": item.migration_id,
            "filename": item.filename,
            "semantic_id": item.semantic_id,
            "disposition": item.disposition,
            "blockers": list(item.local_blockers),
            "input_bindings": list(item.input_bindings),
        }
        for item in ROBINHOOD_RESERVATIONS
    ]


RESERVATION_DIGEST = hashlib.sha256(
    canonical_jcs_bytes(_reservation_records())
).hexdigest()


def _safe_repository_path(value: PurePosixPath | str) -> PurePosixPath:
    raw = str(value)
    if (
        not raw
        or "\\" in raw
        or raw.startswith("/")
        or "://" in raw
    ):
        raise MigrationPlanError("H05_PATH_INVALID")
    normalized = PurePosixPath(raw)
    if (
        raw != normalized.as_posix()
        or normalized.is_absolute()
        or any(
        part in {"", ".", ".."} for part in normalized.parts
        )
    ):
        raise MigrationPlanError("H05_PATH_INVALID")
    return normalized


def _absolute_repository_root(value: str | os.PathLike[str]) -> Path:
    root = Path(value)
    if not root.is_absolute():
        raise MigrationPlanError("H05_REPOSITORY_ROOT_INVALID")
    try:
        details = root.lstat()
    except OSError as error:
        raise MigrationPlanError("H05_REPOSITORY_ROOT_INVALID") from error
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISDIR(details.st_mode):
        raise MigrationPlanError("H05_REPOSITORY_ROOT_INVALID")
    return root


def _join_repository_path(root: Path, relative: PurePosixPath | str) -> Path:
    path = _safe_repository_path(relative)
    selected = root.joinpath(*path.parts)
    try:
        selected.relative_to(root)
    except ValueError as error:
        raise MigrationPlanError("H05_PATH_ESCAPE") from error
    return selected


def _validate_expectations(
    expectations: Sequence[SourceExpectation],
) -> tuple[SourceExpectation, ...]:
    items = tuple(expectations)
    ids = [item.migration_id for item in items]
    semantics = [item.semantic_id for item in items]
    if any(
        re.fullmatch(r"[0-9]{4}", migration_id, re.ASCII) is None
        for migration_id in ids
    ):
        raise MigrationPlanError("H05_RESERVATION_ID")
    if len(ids) != len(set(ids)):
        raise MigrationPlanError("H05_DUPLICATE_NUMERIC_ID")
    if len(semantics) != len(set(semantics)):
        raise MigrationPlanError("H05_DUPLICATE_SEMANTIC_ID")
    if ids != sorted(ids, key=int):
        raise MigrationPlanError("H05_RESERVATION_ORDER")
    for item in items:
        match = _CANONICAL_FILENAME.fullmatch(item.filename)
        if match is None or match.group("migration_id") != item.migration_id:
            raise MigrationPlanError("H05_RESERVATION_MISMATCH")
        if item.sha256 is not None and _HEX64.fullmatch(item.sha256) is None:
            raise MigrationPlanError("H05_SOURCE_HASH_INVALID")
    return items


def _git_blob(root: Path, relative_path: str) -> bytes:
    tracked = subprocess.run(
        [_GIT, "ls-files", "--error-unmatch", "--", relative_path],
        cwd=root,
        env=_GIT_ENV,
        capture_output=True,
        check=False,
    )
    if tracked.returncode != 0:
        raise MigrationPlanError("H05_SOURCE_UNTRACKED")
    blob = subprocess.run(
        [_GIT, "cat-file", "blob", f"HEAD:{relative_path}"],
        cwd=root,
        env=_GIT_ENV,
        capture_output=True,
        check=False,
    )
    if blob.returncode != 0:
        raise MigrationPlanError("H05_SOURCE_UNTRACKED")
    return blob.stdout


def _base_source_digests(root: Path) -> frozenset[str]:
    base_root = root / "migrations/base-mainnet"
    try:
        details = base_root.lstat()
    except FileNotFoundError:
        return frozenset()
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISDIR(details.st_mode):
        raise MigrationPlanError("H05_BASE_NAMESPACE_INVALID")
    digests = set()
    with os.scandir(base_root) as entries:
        for entry in entries:
            if entry.is_symlink():
                raise MigrationPlanError("H05_BASE_NAMESPACE_INVALID")
            if entry.is_file(follow_symlinks=False) and entry.name.endswith(
                ".py"
            ):
                digests.add(
                    hashlib.sha256(Path(entry.path).read_bytes()).hexdigest()
                )
    return frozenset(digests)


def discover_migration_sources(
    repository_root: str | os.PathLike[str],
    source_root: PurePosixPath | str,
    expectations: Sequence[SourceExpectation],
    *,
    require_tracked: bool = True,
    forbid_base_blobs: bool = True,
) -> DiscoveryResult:
    """Discover one exact, flat migration set without importing any module."""

    root = _absolute_repository_root(repository_root)
    source_relative = _safe_repository_path(source_root)
    if source_relative.parts[:2] == ("migrations", "base-mainnet"):
        raise MigrationPlanError("H05_BASE_NAMESPACE_FORBIDDEN")
    source = _join_repository_path(root, source_relative)
    expected = _validate_expectations(expectations)
    expected_by_name = {item.filename: item for item in expected}
    try:
        root_details = source.lstat()
    except FileNotFoundError as error:
        raise MigrationPlanError("H05_SOURCE_ABSENT") from error
    if stat.S_ISLNK(root_details.st_mode) or not stat.S_ISDIR(
        root_details.st_mode
    ):
        raise MigrationPlanError("H05_SOURCE_ROOT_INVALID")

    observed: list[tuple[str, str, str, bytes]] = []
    with os.scandir(source) as entries:
        for entry in entries:
            if entry.is_symlink():
                raise MigrationPlanError("H05_SOURCE_SYMLINK")
            if not entry.is_file(follow_symlinks=False):
                raise MigrationPlanError("H05_RECURSIVE_SOURCE_FORBIDDEN")
            match = _CANONICAL_FILENAME.fullmatch(entry.name)
            if match is None:
                raise MigrationPlanError("H05_FILENAME_NONCANONICAL")
            payload = Path(entry.path).read_bytes()
            try:
                ast.parse(payload, filename=entry.name)
            except (SyntaxError, UnicodeDecodeError) as error:
                raise MigrationPlanError("H05_SOURCE_SYNTAX") from error
            observed.append(
                (
                    entry.name,
                    match.group("migration_id"),
                    match.group("semantic_name"),
                    payload,
                )
            )

    numeric_ids = [item[1] for item in observed]
    semantic_names = [item[2] for item in observed]
    if len(numeric_ids) != len(set(numeric_ids)):
        raise MigrationPlanError("H05_DUPLICATE_NUMERIC_ID")
    if len(semantic_names) != len(set(semantic_names)):
        raise MigrationPlanError("H05_DUPLICATE_SEMANTIC_ID")
    if set(name for name, *_ in observed) != set(expected_by_name):
        raise MigrationPlanError("H05_SOURCE_SET_MISMATCH")

    base_digests = (
        _base_source_digests(root) if forbid_base_blobs else frozenset()
    )
    observed_by_name = {item[0]: item for item in observed}
    discovered: list[DiscoveredSource] = []
    for expectation in expected:
        name, migration_id, semantic_name, payload = observed_by_name[
            expectation.filename
        ]
        if migration_id != expectation.migration_id:
            raise MigrationPlanError("H05_RESERVATION_MISMATCH")
        if semantic_name.casefold() == "ledger":
            raise MigrationPlanError("H05_BASE_SEMANTIC_FORBIDDEN")
        digest = hashlib.sha256(payload).hexdigest()
        if digest in base_digests:
            raise MigrationPlanError("H05_BASE_BLOB_FORBIDDEN")
        relative_path = (
            source_relative / expectation.filename
        ).as_posix()
        if require_tracked and _git_blob(root, relative_path) != payload:
            raise MigrationPlanError("H05_SOURCE_BYTE_MISMATCH")
        if expectation.sha256 is not None and digest != expectation.sha256:
            raise MigrationPlanError("H05_SOURCE_BYTE_MISMATCH")
        discovered.append(
            DiscoveredSource(
                expectation.migration_id,
                name,
                expectation.semantic_id,
                digest,
            )
        )

    records = [
        {
            "migration_id": item.migration_id,
            "filename": item.filename,
            "semantic_id": item.semantic_id,
            "sha256": item.sha256,
        }
        for item in discovered
    ]
    return DiscoveryResult(
        tuple(discovered),
        hashlib.sha256(canonical_jcs_bytes(records)).hexdigest(),
    )


def _git_identity(root: Path) -> tuple[str, str]:
    commit = subprocess.run(
        [_GIT, "rev-parse", "--verify", "HEAD^{commit}"],
        cwd=root,
        env=_GIT_ENV,
        capture_output=True,
        text=True,
        check=False,
    )
    tree = subprocess.run(
        [_GIT, "rev-parse", "HEAD^{tree}"],
        cwd=root,
        env=_GIT_ENV,
        capture_output=True,
        text=True,
        check=False,
    )
    if (
        commit.returncode != 0
        or tree.returncode != 0
        or re.fullmatch(r"[0-9a-f]{40}", commit.stdout.strip()) is None
        or re.fullmatch(r"[0-9a-f]{40}", tree.stdout.strip()) is None
    ):
        raise MigrationPlanError("H05_SOURCE_GIT_IDENTITY")
    return commit.stdout.strip(), tree.stdout.strip()


def read_bound_h06_history(
    semantic_plan: Mapping[str, Any],
    *,
    profile_id: str,
    expected_chain_id: int,
    source_commit: str,
    source_tree: str,
    history_root: str | os.PathLike[str],
):
    """Use only the H-06 public semantic-plan hash and reader APIs."""

    from scripts.utils.manifest_schema import (
        plan_sha256,
        read_history,
        validate_semantic_plan,
    )

    validated = validate_semantic_plan(semantic_plan)
    if validated["profile"] != {
        "profile_id": profile_id,
        "expected_chain_id": expected_chain_id,
    }:
        raise MigrationPlanError("H05_PLAN_PROFILE_MISMATCH")
    if (
        validated["source"]["commit"] != source_commit
        or validated["source"]["tree"] != source_tree
    ):
        raise MigrationPlanError("H05_PLAN_SOURCE_MISMATCH")
    digest = plan_sha256(validated)
    return digest, read_history(
        profile_id,
        expected_chain_id,
        digest,
        source_commit,
        source_tree,
        history_root,
    )


def _path_presence(path: Path) -> bool:
    try:
        details = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as error:
        raise MigrationPlanError("H05_PATH_UNVERIFIABLE") from error
    if stat.S_ISLNK(details.st_mode):
        raise MigrationPlanError("H05_PATH_SYMLINK")
    return True


def build_blocked_migration_report(
    profile_id: str,
    *,
    repository_root: str | os.PathLike[str],
    semantic_plan: Mapping[str, Any] | None = None,
    expectations: Sequence[SourceExpectation] = (),
) -> dict[str, Any]:
    """Build the deterministic, non-executing Robinhood Phase B report."""

    from config.network_profiles import (
        Operation,
        OperationOutcome,
        get_profile,
        operation_decision,
    )

    root = _absolute_repository_root(repository_root)
    profile = get_profile(profile_id)
    if profile.identity.profile_id != profile_id:
        raise MigrationPlanError("H05_PROFILE_ALIAS_FORBIDDEN")
    decision = operation_decision(profile, Operation.MIGRATION_PLAN)
    if decision.outcome is not OperationOutcome.SUPPORTED:
        raise MigrationPlanError("H05_PLAN_UNSUPPORTED")
    if any(
        (
            decision.requires_rpc,
            decision.requires_identity,
            decision.requires_repository,
            decision.requires_account,
            decision.requires_verifier,
        )
    ):
        raise MigrationPlanError("H05_PLAN_RUNTIME_DEPENDENCY")
    repository = profile.repository
    if (
        repository.migration_dir is None
        or repository.history_dir is None
        or profile.identity.chain_id is None
    ):
        raise MigrationPlanError("H05_PLAN_UNSUPPORTED")
    source_relative = _safe_repository_path(repository.migration_dir)
    history_relative = _safe_repository_path(repository.history_dir)
    if source_relative == history_relative:
        raise MigrationPlanError("H05_SOURCE_HISTORY_COLLISION")
    if source_relative.parts[:2] == ("migrations", "base-mainnet"):
        raise MigrationPlanError("H05_BASE_NAMESPACE_FORBIDDEN")
    if history_relative.parts[:2] == (
        "migration_history",
        "base-mainnet",
    ):
        raise MigrationPlanError("H05_BASE_HISTORY_FORBIDDEN")

    source_path = _join_repository_path(root, source_relative)
    history_path = _join_repository_path(root, history_relative)
    other_profile_id = (
        "robinhood-testnet"
        if profile_id == "robinhood-mainnet"
        else "robinhood-mainnet"
    )
    other_history_relative = _safe_repository_path(
        get_profile(other_profile_id).repository.history_dir
    )
    other_history_path = _join_repository_path(
        root, other_history_relative
    )
    commit, tree = _git_identity(root)
    source_present = _path_presence(source_path)
    history_present = _path_presence(history_path)
    other_history_present = _path_presence(other_history_path)

    blockers = set(_CURRENT_GLOBAL_BLOCKERS)
    source_digest = None
    prior_history_digest = None
    if source_present:
        if semantic_plan is None or not expectations:
            raise MigrationPlanError("H05_SOURCE_PLAN_REQUIRED")
        discovery = discover_migration_sources(
            root,
            source_relative,
            expectations,
            require_tracked=True,
            forbid_base_blobs=True,
        )
        source_digest = discovery.source_digest
        blockers.discard("B-H05-SOURCE-ABSENT")
        _, history = read_bound_h06_history(
            semantic_plan,
            profile_id=profile_id,
            expected_chain_id=profile.identity.chain_id,
            source_commit=commit,
            source_tree=tree,
            history_root=history_path,
        )
        if history.state.value == "valid" and history.head is not None:
            prior_history_digest = history.head["record_sha256"]
            blockers.discard("B-H06-HISTORIES-ABSENT")
        elif history.state.value != "absent-clean":
            blockers.add("B-H06-HISTORY-UNVERIFIABLE")
    elif history_present or other_history_present:
        blockers.add("B-H06-HISTORY-UNVERIFIABLE")
        if other_history_present:
            blockers.add("B-H06-CROSS-PROFILE-HISTORY")

    report = {
        "schema": _REPORT_SCHEMA,
        "mode": "dry-plan",
        "status": "blocked",
        "profile_id": profile_id,
        "expected_chain_id": profile.identity.chain_id,
        "source_root": source_relative.as_posix(),
        "history_root": history_relative.as_posix(),
        "source_commit": commit,
        "source_tree": tree,
        "source_digest": source_digest,
        "reservation_digest": RESERVATION_DIGEST,
        "prior_history_digest": prior_history_digest,
        "steps": _reservation_records(),
        "blockers": sorted(blockers),
        "plan_hash": None,
    }
    report["report_sha256"] = report_sha256(report)
    return report


class MigrationError(Exception):
    """
    Error representing an exception that occurs while executing a migration.
    Provides a `failure_timestamp` to identify the migration in which the
    failure occurred, which can be used to resume execution later on.
    """

    def __init__(
        self, failure_timestamp, message="An error occurred while executing migration"
    ):
        self.failure_timestamp = failure_timestamp
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}. Timestamp of failed migration script: {self.failure_timestamp}"


class MigrationRunner:
    """
    Facilitates the execution of migration scripts.
    """

    def __init__(self, migrations_dir, history_dir, files):
        self.migrations_dir = migrations_dir
        self.history_dir = history_dir
        self.files = files
        self.gas = 0

    def run(self, deploy_args: DeployArgs, start_timestamp=None, end_timestamp=None, continue_running=True):
        """
        Run migrations starting at `start_timestamp`. If no start timestamp is provided,
        the history directory is checked for existing timestamps, and migrations will
        start after the latest recorded manifest timestamp.

        The `migrate` function of each migration is called with the manifest generated
        by the previous migration. Manifests returned by each migration are stored in
        the history directory. For shared deployments, they should be included in version
        control.

        To make it easy for other utilities to obtain the current manifest, a manifest
        named `current-manifest.json` will be also be saved in the history directory,
        duplicating the manifest of the latest migration.
        """
        from scripts.utils.migration import Migration

        for migrate, timestamp, prev_timestamp in self._migrations(start_timestamp, end_timestamp):
            log.h1(f"Running migration with timestamp {timestamp}...")
            try:
                migration = Migration(
                    deploy_args, self.files, timestamp, prev_timestamp, self.history_dir
                )
                migrate(migration)
                self.gas += migration.end()

                if not continue_running:
                    break
            except Exception as exception:
                raise MigrationError(timestamp) from exception
        return self.gas

    def _migrations(self, start_timestamp=None, end_timestamp=None):
        # Generator that returns a `(migration, timestamp, prev_timestamp)` tuple for
        # each migration script, starting ON OR AFTER `start_timestamp`.
        #
        # If no start timestamp is provided, the history directory is checked for existing
        # timestamps, and migrations will start after the latest recorded manifest timestamp.

        migrations = []
        if start_timestamp == None:
            start_timestamp = self._latest_manifest_timestamp()
            migrations = self._filtered_migration_filenames(
                start_timestamp, end_timestamp, inclusive=False
            )
        else:
            migrations = self._filtered_migration_filenames(
                start_timestamp, end_timestamp)

        for filename, timestamp, prev_timestamp in migrations:
            migration = importlib.util.spec_from_file_location('migration', filename)
            module = importlib.util.module_from_spec(migration)
            migration.loader.exec_module(module)
            yield module.migrate, timestamp, prev_timestamp

    def _filtered_migration_filenames(self, start_timestamp, end_timestamp, inclusive=True):
        # Get a list of migration scripts having timestamps greater than or equal
        # to the value of `start_timestamp`.
        #
        # If `inclusive` == False, only timestamps AFTER the start timestamp will be
        # included.
        #
        # Returns a list of `(filename, timestamp, prev_timestamp)` tuples.
        # `prev_timestamp` is included so that the manifest from the previous
        # migration can be retrieved and passed to the next migration.

        timestamped_migrations = []
        for file in os.listdir(self.migrations_dir):
            # timestamp of the filename is the initial string of numbers,
            # up to the first non-digit character
            match = re.fullmatch(r"(\d+).*\.py$", file)
            if match:
                timestamp = match.group(1)
                filename = os.path.join(self.migrations_dir, file)
                timestamped_migrations.append((filename, timestamp))

        # sort order of `os.listdir` is not guaranteed, so we sort on timestamp
        # Convert timestamps to integers for proper numerical sorting
        timestamped_migrations = sorted(
            timestamped_migrations, key=lambda x: int(x[1]))

        # include previous timestamp in migration tuples
        migrations = []
        prev_timestamp = None
        for filename, timestamp in timestamped_migrations:
            # Convert timestamps to integers for proper numerical comparison
            timestamp_int = int(timestamp)
            end_timestamp_int = int(end_timestamp) if end_timestamp and end_timestamp != '0' else None
            start_timestamp_int = int(start_timestamp) if start_timestamp else None

            if end_timestamp_int is not None and timestamp_int > end_timestamp_int:
                break
            if start_timestamp_int is None or timestamp_int >= start_timestamp_int:
                migrations.append((filename, timestamp, prev_timestamp))
            prev_timestamp = timestamp

        return migrations

    def _latest_manifest_timestamp(self):
        # get the timestamp of the most recently executed migration
        # (returns None if no migrations have been run)

        latest_timestamp = None

        # create the history directory if it doesn't already exist
        os.makedirs(self.history_dir, exist_ok=True)

        # scan each file to get the latest timestamp
        for file in os.listdir(self.history_dir):
            match = re.fullmatch(r"(.*)\-manifest\.json$", file)
            if match:
                timestamp = match.group(1)
                # Convert timestamps to integers for proper numerical comparison
                if latest_timestamp == None or int(timestamp) > int(latest_timestamp):
                    latest_timestamp = timestamp

        return latest_timestamp
