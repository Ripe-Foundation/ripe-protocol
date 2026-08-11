"""Strict reader for monolithic and indexed contract artifact expectations."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


V1_SCHEMA_VERSION = 1
V2_SCHEMA_VERSION = 2
RECORD_SCHEMA_VERSION = 1
_V1_KEYS = frozenset({"compiler", "contracts", "schema_version"})
_V2_KEYS = frozenset({"compiler", "contracts", "records_root", "schema_version"})
_COMPILER_KEYS = frozenset(
    {
        "artifact_recipe",
        "integrity_recipe",
        "optimization_rule",
        "version",
    }
)
_REFERENCE_KEYS = frozenset({"path", "sha256"})
_RECORD_KEYS = frozenset({"contract", "expectation", "schema_version"})
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_CONTRACT_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_MAX_JSON_DEPTH = 100
_MAX_JSON_NODES = 100_000


class ArtifactExpectationsError(ValueError):
    """Raised when artifact expectations are ambiguous or unsafe to load."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ArtifactExpectationsError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_non_finite_constant(value: str) -> None:
    raise ArtifactExpectationsError(f"non-finite JSON constant: {value}")


def _parse_finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ArtifactExpectationsError(f"non-finite JSON float: {value}")
    return parsed


def _validate_json_complexity(value: Any, *, label: str) -> None:
    stack = [(value, 0)]
    nodes = 0
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > _MAX_JSON_NODES:
            raise ArtifactExpectationsError(
                f"{label}: JSON value exceeds maximum node count "
                f"{_MAX_JSON_NODES}"
            )
        if depth > _MAX_JSON_DEPTH:
            raise ArtifactExpectationsError(
                f"{label}: JSON nesting exceeds maximum depth "
                f"{_MAX_JSON_DEPTH}"
            )
        if isinstance(current, dict):
            stack.extend((nested, depth + 1) for nested in current.values())
        elif isinstance(current, list):
            stack.extend((nested, depth + 1) for nested in current)


def _load_json(raw: bytes, *, label: str) -> Any:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ArtifactExpectationsError(f"{label}: invalid UTF-8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite_constant,
            parse_float=_parse_finite_float,
        )
    except ArtifactExpectationsError:
        raise
    except (
        json.JSONDecodeError,
        ValueError,
        OverflowError,
        RecursionError,
    ) as exc:
        raise ArtifactExpectationsError(f"{label}: invalid JSON: {exc}") from exc
    _validate_json_complexity(value, label=label)
    return value


def _require_exact_keys(
    value: dict[str, Any], expected: frozenset[str], *, label: str
) -> None:
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        raise ArtifactExpectationsError(
            f"{label}: invalid keys; missing={missing}, extra={extra}"
        )


def _require_object(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ArtifactExpectationsError(f"{label}: expected JSON object")
    return value


def _validate_compiler(value: Any) -> dict[str, Any]:
    compiler = _require_object(value, label="compiler")
    _require_exact_keys(compiler, _COMPILER_KEYS, label="compiler")
    if not all(isinstance(compiler[key], str) and compiler[key] for key in compiler):
        raise ArtifactExpectationsError(
            "compiler: every field must be a non-empty string"
        )
    return compiler


def _validate_contracts(value: Any, *, label: str) -> dict[str, Any]:
    contracts = _require_object(value, label=label)
    if not contracts:
        raise ArtifactExpectationsError(f"{label}: no contract records")
    for name, record in contracts.items():
        if (
            not isinstance(name, str)
            or _CONTRACT_IDENTIFIER_RE.fullmatch(name) is None
        ):
            raise ArtifactExpectationsError(
                f"{label}: contract names must be identifier-safe"
            )
        _require_object(record, label=f"{label}.{name}")
    return contracts


def _path_text(value: Any, *, label: str) -> str:
    try:
        raw = os.fspath(value)
    except TypeError as exc:
        raise ArtifactExpectationsError(f"{label}: path must be path-like") from exc
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise ArtifactExpectationsError(
            f"{label}: path must be a non-empty text path"
        )
    return raw


def _exact_child(parent: Path, name: str, *, label: str) -> Path:
    try:
        names = {entry.name for entry in parent.iterdir()}
    except OSError as exc:
        raise ArtifactExpectationsError(
            f"{label}: cannot inspect anchor directory: {parent}"
        ) from exc
    if name not in names:
        case_matches = sorted(
            candidate for candidate in names if candidate.casefold() == name.casefold()
        )
        if case_matches:
            raise ArtifactExpectationsError(
                f"{label}: path component casing mismatch for {name!r}; "
                f"on disk={case_matches}"
            )
        raise ArtifactExpectationsError(
            f"{label}: missing path component {name!r} under {parent}"
        )
    return parent / name


def _canonical_absolute_anchor(
    value: Any, *, label: str, final_kind: str
) -> Path:
    raw = _path_text(value, label=label)
    if PureWindowsPath(raw).drive:
        raise ArtifactExpectationsError(
            f"{label}: Windows drive paths are forbidden"
        )
    path = Path(raw)
    if not path.is_absolute():
        raise ArtifactExpectationsError(f"{label}: anchor must be absolute")
    raw_components = raw.split("/")
    if any(component in {".", ".."} for component in raw_components):
        raise ArtifactExpectationsError(
            f"{label}: anchor may not contain . or .. spellings"
        )
    if raw != "/" and (raw.endswith("/") or "//" in raw):
        raise ArtifactExpectationsError(
            f"{label}: anchor must use canonical separators"
        )
    if path.as_posix() != raw:
        raise ArtifactExpectationsError(f"{label}: anchor spelling is not canonical")

    current = Path(path.anchor)
    try:
        mode = current.lstat().st_mode
    except OSError as exc:
        raise ArtifactExpectationsError(
            f"{label}: unreadable anchor root: {current}"
        ) from exc
    if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
        raise ArtifactExpectationsError(
            f"{label}: anchor root must be a real directory"
        )

    parts = path.parts[1:]
    for index, part in enumerate(parts):
        current = _exact_child(current, part, label=label)
        try:
            mode = current.lstat().st_mode
        except OSError as exc:
            raise ArtifactExpectationsError(
                f"{label}: unreadable anchor component: {current}"
            ) from exc
        if stat.S_ISLNK(mode):
            raise ArtifactExpectationsError(
                f"{label}: symlink anchor components are forbidden: {current}"
            )
        is_final = index == len(parts) - 1
        if not is_final and not stat.S_ISDIR(mode):
            raise ArtifactExpectationsError(
                f"{label}: non-directory anchor component: {current}"
            )

    mode = current.lstat().st_mode
    valid = stat.S_ISDIR(mode) if final_kind == "directory" else stat.S_ISREG(mode)
    if not valid:
        raise ArtifactExpectationsError(
            f"{label}: anchor is not a regular {final_kind}: {current}"
        )
    try:
        resolved = current.resolve(strict=True)
    except OSError as exc:
        raise ArtifactExpectationsError(f"{label}: anchor cannot resolve") from exc
    if resolved != current:
        raise ArtifactExpectationsError(f"{label}: anchor is not canonical")
    return current


def _require_native_containment(
    candidate: Path, root: Path, *, label: str
) -> None:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ArtifactExpectationsError(
            f"{label}: native path escapes repository root"
        ) from exc


def _read_regular_file(path: Path, *, label: str) -> bytes:
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise ArtifactExpectationsError(f"{label}: unreadable path: {path}") from exc
    if stat.S_ISLNK(mode):
        raise ArtifactExpectationsError(f"{label}: symlink paths are forbidden: {path}")
    if not stat.S_ISREG(mode):
        raise ArtifactExpectationsError(f"{label}: path is not a regular file: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ArtifactExpectationsError(f"{label}: unreadable path: {path}") from exc


def _normalized_relative_path(value: Any, *, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise ArtifactExpectationsError(f"{label}: path must be a non-empty string")
    if PureWindowsPath(value).drive:
        raise ArtifactExpectationsError(
            f"{label}: Windows drive paths are forbidden"
        )
    if "\\" in value:
        raise ArtifactExpectationsError(f"{label}: path must use POSIX separators")
    path = PurePosixPath(value)
    if path.is_absolute():
        raise ArtifactExpectationsError(f"{label}: absolute paths are forbidden")
    if any(component in {"", ".", ".."} for component in value.split("/")):
        raise ArtifactExpectationsError(
            f"{label}: path must be normalized and may not escape its root"
        )
    if path.as_posix() != value or any(part in {"", ".", ".."} for part in path.parts):
        raise ArtifactExpectationsError(
            f"{label}: path must be normalized and may not escape its root"
        )
    return path


def _path_under_root(
    root: Path,
    relative: PurePosixPath,
    *,
    label: str,
    final_kind: str,
) -> Path:
    candidate = root.joinpath(*relative.parts)
    _require_native_containment(candidate, root, label=label)
    current = root
    for index, part in enumerate(relative.parts):
        current = _exact_child(current, part, label=label)
        try:
            mode = current.lstat().st_mode
        except OSError as exc:
            raise ArtifactExpectationsError(
                f"{label}: missing path: {relative.as_posix()}"
            ) from exc
        if stat.S_ISLNK(mode):
            raise ArtifactExpectationsError(
                f"{label}: symlink paths are forbidden: {relative.as_posix()}"
            )
        is_final = index == len(relative.parts) - 1
        if not is_final and not stat.S_ISDIR(mode):
            raise ArtifactExpectationsError(
                f"{label}: non-directory path component: {relative.as_posix()}"
            )

    mode = current.lstat().st_mode
    valid = stat.S_ISDIR(mode) if final_kind == "directory" else stat.S_ISREG(mode)
    if not valid:
        raise ArtifactExpectationsError(
            f"{label}: path is not a regular {final_kind}: {relative.as_posix()}"
        )
    try:
        resolved = current.resolve(strict=True)
    except OSError as exc:
        raise ArtifactExpectationsError(f"{label}: path cannot resolve") from exc
    _require_native_containment(resolved, root, label=label)
    if resolved != current:
        raise ArtifactExpectationsError(f"{label}: path is not canonical")
    return current


def _load_v1(index: dict[str, Any]) -> dict[str, Any]:
    _require_exact_keys(index, _V1_KEYS, label="artifact expectations v1")
    compiler = _validate_compiler(index["compiler"])
    contracts = _validate_contracts(index["contracts"], label="contracts")
    return {
        "compiler": compiler,
        "contracts": contracts,
        "schema_version": V1_SCHEMA_VERSION,
    }


def _load_v2(index: dict[str, Any], *, root: Path) -> dict[str, Any]:
    _require_exact_keys(index, _V2_KEYS, label="artifact expectations v2")
    compiler = _validate_compiler(index["compiler"])
    references = _validate_contracts(index["contracts"], label="contract references")
    records_root_relative = _normalized_relative_path(
        index["records_root"], label="records_root"
    )
    records_root = _path_under_root(
        root,
        records_root_relative,
        label="records_root",
        final_kind="directory",
    )

    referenced_paths: dict[str, PurePosixPath] = {}
    seen_paths: set[PurePosixPath] = set()
    for name, raw_reference in references.items():
        reference = _require_object(raw_reference, label=f"contract references.{name}")
        _require_exact_keys(
            reference, _REFERENCE_KEYS, label=f"contract references.{name}"
        )
        relative = _normalized_relative_path(
            reference["path"], label=f"contract references.{name}.path"
        )
        if relative.parent != records_root_relative:
            raise ArtifactExpectationsError(
                f"contract references.{name}.path: record must be a direct child "
                "of records_root"
            )
        expected_filename = f"{name}.json"
        if relative.name != expected_filename:
            raise ArtifactExpectationsError(
                f"contract references.{name}.path: expected exact filename "
                f"{expected_filename!r}"
            )
        if relative in seen_paths:
            raise ArtifactExpectationsError(
                f"contract references.{name}.path: duplicate record path"
            )
        digest = reference["sha256"]
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            raise ArtifactExpectationsError(
                f"contract references.{name}.sha256: invalid SHA-256"
            )
        referenced_paths[name] = relative
        seen_paths.add(relative)

    expected_names = {path.name for path in seen_paths}
    actual_names = {entry.name for entry in records_root.iterdir()}
    missing = sorted(expected_names - actual_names)
    extra = sorted(actual_names - expected_names)
    if missing or extra:
        raise ArtifactExpectationsError(
            f"records_root: record set mismatch; missing={missing}, extra={extra}"
        )

    contracts: dict[str, Any] = {}
    for name, relative in referenced_paths.items():
        record_path = _path_under_root(
            root,
            relative,
            label=f"contract record {name}",
            final_kind="file",
        )
        raw = _read_regular_file(record_path, label=f"contract record {name}")
        expected_digest = references[name]["sha256"]
        actual_digest = hashlib.sha256(raw).hexdigest()
        if actual_digest != expected_digest:
            raise ArtifactExpectationsError(f"contract record {name}: SHA-256 mismatch")
        record = _require_object(
            _load_json(raw, label=f"contract record {name}"),
            label=f"contract record {name}",
        )
        _require_exact_keys(record, _RECORD_KEYS, label=f"contract record {name}")
        record_schema = record["schema_version"]
        if (
            not isinstance(record_schema, int)
            or isinstance(record_schema, bool)
            or record_schema != RECORD_SCHEMA_VERSION
        ):
            raise ArtifactExpectationsError(
                f"contract record {name}: unsupported record schema"
            )
        if record["contract"] != name:
            raise ArtifactExpectationsError(
                f"contract record {name}: contract name mismatch"
            )
        contracts[name] = _require_object(
            record["expectation"], label=f"contract record {name}.expectation"
        )

    return {
        "compiler": compiler,
        "contracts": contracts,
        "schema_version": V1_SCHEMA_VERSION,
    }


def load_artifact_expectations(
    path: str | Path,
    *,
    root: str | Path | None = None,
    allow_v2: bool = True,
) -> dict[str, Any]:
    """Load v1 or v2 expectations into the established v1 in-memory shape."""
    if root is None:
        raise ArtifactExpectationsError(
            "artifact expectations: canonical absolute repository root is required"
        )
    root_path = _canonical_absolute_anchor(
        root,
        label="artifact expectations repository root",
        final_kind="directory",
    )
    index_path = _canonical_absolute_anchor(
        path,
        label="artifact expectations index",
        final_kind="file",
    )
    index = _require_object(
        _load_json(
            _read_regular_file(index_path, label="artifact expectations"),
            label="artifact expectations",
        ),
        label="artifact expectations",
    )
    schema_version = index.get("schema_version")
    valid_integer_schema = isinstance(schema_version, int) and not isinstance(
        schema_version, bool
    )
    if valid_integer_schema and schema_version == V1_SCHEMA_VERSION:
        return _load_v1(index)
    if not valid_integer_schema or schema_version != V2_SCHEMA_VERSION:
        raise ArtifactExpectationsError(
            f"artifact expectations: unsupported schema_version {schema_version!r}"
        )
    if not allow_v2:
        raise ArtifactExpectationsError(
            "artifact expectations v2 updates require an atomic v2 writer"
        )
    _require_native_containment(
        index_path, root_path, label="artifact expectations index"
    )
    return _load_v2(index, root=root_path)
