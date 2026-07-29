#!/usr/bin/env python3
"""Deterministically validate the reviewed block-clock inventory.

The checker intentionally uses only Python's standard library.  The JSON ledger is
the reviewed source of truth; this module discovers current source state and
refuses to create or update semantic classifications.
"""

from __future__ import annotations

import argparse
import copy
import fnmatch
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Mapping, Sequence


EXPECTED_SCHEMA_VERSION = 1
EXPECTED_PRODUCTION_COUNTS = (99, 94, 17)
EXPECTED_TIMESTAMP_COUNTS = (37, 37, 11)
EXPECTED_BN_IDS = {f"BN-{number:03d}" for number in range(1, 33)}
EXPECTED_CAD_IDS = {"CAD-001"}
EXPECTED_TS_IDS = {f"TS-{number:03d}" for number in range(1, 12)}
TRACK3_REVIEW_COMMIT = "c3040041a1254a774e0a305060330d6ab9cc04ca"
HARDENING_REVIEW_COMMIT = "db7ae895d1b32ae6708f2405274c32c1e3f5222e"
H04_REVIEW_COMMIT = "81ad3ff758c2a3a08577ce5b9dc0ae0eff31a038"
H04_CADENCE_RECORD_COUNT = 116
H04_CADENCE_RECORDS_SHA256 = (
    "d0d0e3ca3ac472b1a709a9525e9ad38d5b76c5337b4e540c3ca10b7c0dcddf05"
)
H04_CAD_SITE_COUNT = 6
H04_CAD_SITES_SHA256 = (
    "8ffb9dd92c225d4cacea6827194bf3b42eb5cb2efaf6729f6aa1f083503f42ee"
)
EXPECTED_PRODUCTION_ROOTS = ["contracts"]
EXPECTED_EXCLUDED_PRODUCTION_GLOBS = [
    "contracts/mock/**",
    "contracts/testing/**",
]
EXPECTED_ALLOWED_NONPRODUCTION_GLOBS = [
    "tests/**",
    "contracts/mock/**",
    "contracts/testing/**",
]
# Exact non-production reference examples excluded from every clock count.
# Both the path and the content SHA-256 are frozen: adding, moving, or
# editing an excluded example requires a reviewed checker change.
EXCLUDED_CCIP_EXAMPLE_PATH = (
    "docs/chains/rh/examples/ExampleGreenCcipBurnMintPool.vy"
)
EXCLUDED_CCIP_EXAMPLE_SHA256 = (
    "7f3b46af23b9456869b0a72578d3ae295cbfb8ff112d0f7bddd1d66a4afb1e18"
)
EXCLUDED_EXAMPLE_CONTENT_HASHES = {
    EXCLUDED_CCIP_EXAMPLE_PATH: EXCLUDED_CCIP_EXAMPLE_SHA256,
}
EXPECTED_INTERFACE_ROOTS = ["interfaces"]
EXPECTED_CADENCE_ROOTS = [
    "contracts",
    "config",
    "interfaces",
    "migrations",
    "migration_history",
    "scripts",
    "tests",
    "README.md",
]
EXPECTED_CADENCE_EXCLUDED_GLOBS = [
    "config/block-clock-inventory.json",
    "migration_history/base-mainnet/**",
    "scripts/check_block_clock_inventory.py",
    "tests/inventory/test_block_clock_inventory.py",
]
EXPECTED_REVIEW_AUTHORITIES = {
    "directOccurrences": "protocol/security",
    "timestampContext": "protocol/security",
    "cadenceCandidates": {
        "CAD-001": "risk/oracle",
        "other": "protocol/security",
    },
    "secondsUnitCandidates": "protocol/security",
    "allowedMixedClockFunctions": "protocol/security",
    "vyperPathClassifications": "engineering/tooling",
}
EXPECTED_REVIEW_PROVENANCE = {
    "track3ReviewCommit": TRACK3_REVIEW_COMMIT,
    "hardeningApprovalCommit": HARDENING_REVIEW_COMMIT,
}
S5_REVIEW_ARTIFACT_SHA256 = (
    "e2c7b92b3ca51f903e0cdb8eb5c5eda3d6c1f2e644a6ee424ea67fe8e8ea9a76"
)
S5_REVIEW_ARTIFACT_FIELD = "s5ReviewArtifactSha256"
S5_LEGACY_INVENTORY_SHA256 = (
    "924a559075d5b96bcac3f73d28390deee3b436fe5500adc4fb6bf769282217b4"
)
M2_GUARDED_ERC20_PATH = "contracts/vaults/GuardedErc20.vy"
M2_GUARDED_ERC20_SHA256 = (
    "0fcdb02a0b3adf56ef0fd04397c57ac40325a37c87a32f29979dadc5eaf353ed"
)
M3_CREDIT_ENGINE_PATH = "contracts/core/CreditEngine.vy"
M3_CREDIT_ENGINE_SHA256 = (
    "7de649cece6e076b75775bb4ff5f397bf5ffa0a50ccdc462a061ca047b888e3d"
)
# Exact pre-M3 CreditEngine ledger record content hash, used only to
# reconstruct the frozen S5 legacy fingerprint.  Any deviation from the one
# reviewed M3 record disables that reconstruction and fails closed.
M3_CREDIT_ENGINE_BASELINE_SHA256 = (
    "23129f8f6e87805bc47712d06f7ddf6c0de920866ad36ca78ee96e9c57ef96d8"
)
POST_S5_PRODUCTION_INVENTORY_SHA256 = (
    "f29e30aef76e01f77a74a910b07ba16204aabb6a0860add4a072da7de76035bd"
)
S5_REVIEW_DIRECT_KEYS = {
    ("contracts/data/Ledger.vy", "_getActionBlock", "block.number", 1),
}
S5_RECONCILED_DIRECT_KEYS = S5_REVIEW_DIRECT_KEYS | {
    (
        "contracts/data/Ledger.vy",
        "checkAndUpdateLastTouch",
        "block.number",
        1,
    ),
    (
        "contracts/data/Ledger.vy",
        "checkAndUpdateLastTouch",
        "block.number",
        2,
    ),
}
S5_REVIEW_CADENCE_KEYS = {
    (
        "contracts/data/Ledger.vy",
        "<module>",
        "cadence-comment",
        "per block",
        "# one action per block",
        1,
    ),
    (
        "contracts/data/Ledger.vy",
        "checkAndUpdateLastTouch",
        "cadence-comment",
        "per block",
        "assert self.lastTouch[_user] != actionBlock # dev: one action per block",
        1,
    ),
    (
        "contracts/testing/ActionBlockIdentityProbe.vy",
        "readActionBlocks",
        "block-unit-identifier",
        "readActionBlocks",
        "def readActionBlocks() -> (uint256, uint256):",
        1,
    ),
    (
        "scripts/probes/action_block_identity_probe.py",
        "preflight",
        "block-default-key",
        '"latest_block":',
        '"latest_block": {',
        1,
    ),
    (
        "scripts/probes/action_block_identity_probe.py",
        "analyze_observations",
        "block-default-key",
        '"child_block":',
        '"child_block": child,',
        1,
    ),
    (
        "scripts/probes/action_block_identity_probe.py",
        "analyze_observations",
        "block-default-key",
        '"first_child_block":',
        '"first_child_block": first_block,',
        1,
    ),
    (
        "scripts/probes/action_block_identity_probe.py",
        "analyze_observations",
        "block-default-key",
        '"second_child_block":',
        '"second_child_block": second_block,',
        1,
    ),
    (
        "scripts/probes/action_block_identity_probe.py",
        "analyze_observations",
        "block-default-key",
        '"distinct_child_blocks":',
        '"distinct_child_blocks": len(set(arb_values)),',
        1,
    ),
    (
        "tests/core/creditEngine/test_credit_borrow.py",
        "test_borrow_guard_runs_before_credit_effects_and_rejects_second_action",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/core/creditEngine/test_credit_repay.py",
        "test_repay_low_risk_succeeds_between_checked_actions_and_rearms_guard",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/core/teller/test_teller_action_block.py",
        "test_external_housekeeping_valid_caller_can_select_victim_and_risk_flag",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/core/teller/test_teller_rebalance.py",
        "test_rebalance_after_effects_guard_rejection_rolls_back_every_leg",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/core/teller/test_teller_withdraw.py",
        "test_low_risk_deposit_arms_same_action_block_withdraw_rejection",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/core/teller/test_teller_withdraw.py",
        "test_checked_withdraw_rejects_second_same_action_block_and_rolls_back",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/data/test_ledger.py",
        "test_ledger_check_and_update_last_touch_mixed_check_modes",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/data/test_ledger_action_block.py",
        "test_arb_sys_identity_not_native_block_controls_equality",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/data/test_ledger_action_block.py",
        "test_arb_sys_preserves_low_high_and_high_low_high_ordering",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/data/test_ledger_action_block.py",
        "test_arb_sys_preserves_low_high_and_high_low_high_ordering",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        2,
    ),
    (
        "tests/data/test_ledger_action_block.py",
        "test_arb_sys_keeps_users_isolated_within_one_action_block",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
    (
        "tests/data/test_ledger_action_block.py",
        "test_arb_sys_keeps_users_isolated_within_one_action_block",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        2,
    ),
    (
        "tests/probes/test_action_block_identity_probe.py",
        "test_probe_emits_native_and_arb_sys_values_from_compatible_double",
        "block-unit-identifier",
        "readActionBlocks",
        "native_view, arb_view = probe.readActionBlocks()",
        1,
    ),
    (
        "tests/vaults/modules/test_stab_vault_claims.py",
        "test_claim_after_effects_guard_rejection_rolls_back_second_claim",
        "cadence-comment",
        "per block",
        'with boa.reverts("one action per block"):',
        1,
    ),
}
S5_RECONCILED_CADENCE_KEYS = S5_REVIEW_CADENCE_KEYS | {
    (
        "contracts/data/Ledger.vy",
        "checkAndUpdateLastTouch",
        "cadence-comment",
        "per block",
        "assert self.lastTouch[_user] != block.number # dev: one action per block",
        1,
    ),
}
S5_REVIEW_PATHS = {"contracts/testing/ActionBlockIdentityProbe.vy"}
PLACEHOLDERS = {
    "",
    "-",
    "n/a",
    "na",
    "none",
    "not applicable",
    "placeholder",
    "skipped",
    "tbd",
    "todo",
    "unknown",
}
SOURCE_SUFFIXES = {".json", ".md", ".py", ".vy", ".vyi"}
VYPER_SUFFIXES = {".vy", ".vyi"}
DIRECT_PATTERN = re.compile(r"\bblock\s*\.\s*number\b")
TIMESTAMP_PATTERN = re.compile(r"\bblock\s*\.\s*timestamp\b")
FUNCTION_PATTERN = re.compile(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
IMPORT_PATTERN = re.compile(
    r"^\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_./]*)", re.MULTILINE
)
SECONDS_IDENTIFIER_PATTERN = re.compile(
    r"\b[A-Za-z_][A-Za-z0-9_]*_IN_SECONDS\b"
)
CADENCE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "block-unit-identifier",
        re.compile(
            r"\b(?:"
            r"[A-Z][A-Z0-9_]*_BLOCKS?|"
            r"[a-z][A-Za-z0-9_]*Blocks"
            r")\b"
        ),
    ),
    (
        "reviewed-cadence-identifier",
        re.compile(
            r"\b(?:MIN_UNDERSCORE_SEND_INTERVAL|ONE_DAY|staleBlocks|"
            r"numBlocksPerInterval|ripePerBlock|increasePerDangerBlock)\b"
        ),
    ),
    (
        "block-default-key",
        re.compile(
            r"""["'](?=[A-Za-z_][A-Za-z0-9_]*["']\s*:)[A-Za-z0-9_]*"""
            r"""(?:TIMELOCK|BLOCKS?|INTERVAL|DURATION|DELAY|EXPIRY|"""
            r"""EXPIRATION)["']\s*:""",
            re.IGNORECASE,
        ),
    ),
    (
        "cadence-comment",
        re.compile(
            r"(?:\b(?:Base|Robinhood)\b.{0,80}\bcadence\b|"
            r"\b\d+\s*(?:s|seconds?)\s*/\s*block\b|"
            r"\bblocks?\s+per\s+(?:day|hour|interval)\b|"
            r"\bper[- ]block\b)",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class Finding:
    code: str
    domain: str
    path: str = "-"
    function: str = "-"
    line: int = 0
    snippet: str = "-"
    candidate: str = "UNMAPPED"
    expected: str = "-"
    actual: str = "-"
    remediation: str = "obtain semantic review before updating the inventory"

    def render(self) -> str:
        snippet = json.dumps(self.snippet, ensure_ascii=True)
        remediation = json.dumps(self.remediation, ensure_ascii=True)
        return (
            f"CLOCK_INVENTORY_FAIL code={self.code} domain={self.domain} "
            f"path={self.path} function={self.function} line={self.line} "
            f"candidate={self.candidate} expected={self.expected} "
            f"actual={self.actual} snippet={snippet} remediation={remediation}"
        )


@dataclass(frozen=True)
class Occurrence:
    path: str
    function: str
    normalized_expression: str
    ordinal: int
    line: int
    column: int
    snippet: str

    @property
    def key(self) -> tuple[str, str, str, int]:
        return (
            self.path,
            self.function,
            self.normalized_expression,
            self.ordinal,
        )


@dataclass(frozen=True)
class Candidate:
    path: str
    function: str
    pattern: str
    matched_text: str
    normalized_snippet: str
    ordinal: int
    line: int
    classification: str

    @property
    def key(self) -> tuple[str, str, str, str, str, int]:
        return (
            self.path,
            self.function,
            self.pattern,
            self.matched_text,
            self.normalized_snippet,
            self.ordinal,
        )


@dataclass
class CheckResult:
    findings: list[Finding]
    success_lines: list[str]

    @property
    def ok(self) -> bool:
        return not self.findings

    @property
    def output(self) -> str:
        lines = (
            self.success_lines
            if self.ok
            else [finding.render() for finding in sorted(self.findings, key=_finding_key)]
        )
        return "\n".join(lines)


def _finding_key(finding: Finding) -> tuple[Any, ...]:
    return (
        finding.code,
        finding.domain,
        finding.path,
        finding.function,
        finding.line,
        finding.candidate,
        finding.snippet,
    )


def _normalize_whitespace(value: str) -> str:
    return " ".join(value.strip().split())


def _matches_glob(path: str, pattern: str) -> bool:
    if pattern.endswith("/**") and (
        path == pattern[:-3] or path.startswith(pattern[:-2])
    ):
        return True
    return fnmatch.fnmatchcase(path, pattern) or PurePosixPath(path).match(pattern)


def classify_path(
    path: str,
    production_roots: Sequence[str],
    excluded_production_globs: Sequence[str],
    interface_roots: Sequence[str] = EXPECTED_INTERFACE_ROOTS,
    allowed_nonproduction_globs: Sequence[str] = EXPECTED_ALLOWED_NONPRODUCTION_GLOBS,
) -> str:
    if path in EXCLUDED_EXAMPLE_CONTENT_HASHES:
        return "excluded"
    for root in interface_roots:
        normalized_root = root.rstrip("/")
        if path == normalized_root or path.startswith(f"{normalized_root}/"):
            return "interface"
    for glob in allowed_nonproduction_globs:
        if not _matches_glob(path, glob):
            continue
        parts = PurePosixPath(glob.lower()).parts
        if "mock" in parts:
            return "mock"
        if "testing" in parts:
            return "testing"
        if "tests" in parts:
            return "test"
        return "excluded"
    for glob in excluded_production_globs:
        if not _matches_glob(path, glob):
            continue
        normalized_glob = glob.lower()
        if "mock" in PurePosixPath(normalized_glob).parts:
            return "mock"
        if "testing" in PurePosixPath(normalized_glob).parts:
            return "testing"
        return "excluded"
    for root in production_roots:
        normalized_root = root.rstrip("/")
        if path == normalized_root or path.startswith(f"{normalized_root}/"):
            return "production"
    if Path(path).suffix in VYPER_SUFFIXES:
        return "unclassified"
    if path.startswith("config/"):
        return "config"
    if path.startswith("migrations/"):
        return "migration"
    if path.startswith("scripts/"):
        return "tooling"
    return "other"


def _iter_files(root: Path, relative_roots: Iterable[str]) -> list[Path]:
    files: set[Path] = set()
    for relative_root in relative_roots:
        base = root / relative_root
        if base.is_file():
            files.add(base)
        elif base.is_dir():
            for candidate in base.rglob("*"):
                if candidate.is_file() and not any(
                    part in {".git", ".hypothesis", ".pytest_cache", ".venv", "__pycache__", "out"}
                    for part in candidate.relative_to(root).parts
                ):
                    files.add(candidate)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _line_functions(lines: Sequence[str]) -> list[str]:
    current = "<module>"
    signature_depth = 0
    functions: list[str] = []
    for line in lines:
        match = FUNCTION_PATTERN.match(line)
        if match:
            current = match.group(1)
            signature_depth = line.count("(") - line.count(")")
        elif signature_depth:
            signature_depth += line.count("(") - line.count(")")
        elif line and not line[0].isspace():
            current = "<module>"
        functions.append(current)
    return functions


def _scan_expression_files(
    root: Path,
    paths: Iterable[Path],
    pattern: re.Pattern[str],
) -> list[Occurrence]:
    occurrences: list[Occurrence] = []
    ordinals: dict[tuple[str, str, str], int] = {}
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        lines = _read_text(path).splitlines()
        functions = _line_functions(lines)
        for line_number, (line, function) in enumerate(zip(lines, functions), start=1):
            for match in pattern.finditer(line):
                normalized = _normalize_whitespace(match.group(0))
                ordinal_key = (relative, function, normalized)
                ordinal = ordinals.get(ordinal_key, 0) + 1
                ordinals[ordinal_key] = ordinal
                occurrences.append(
                    Occurrence(
                        path=relative,
                        function=function,
                        normalized_expression=normalized,
                        ordinal=ordinal,
                        line=line_number,
                        column=match.start() + 1,
                        snippet=_normalize_whitespace(line),
                    )
                )
    return occurrences


def _scan_fixed_counts(paths: Iterable[Path], needle: str) -> tuple[int, int, int]:
    occurrences = 0
    matching_lines = 0
    matching_files = 0
    for path in paths:
        text = _read_text(path)
        file_occurrences = text.count(needle)
        if file_occurrences:
            matching_files += 1
            occurrences += file_occurrences
            matching_lines += sum(1 for line in text.splitlines() if needle in line)
    return occurrences, matching_lines, matching_files


def _candidate_from_record(record: Mapping[str, Any]) -> tuple[str, str, str, str, str, int]:
    return (
        str(record.get("path", "")),
        str(record.get("function", "")),
        str(record.get("pattern", "")),
        str(record.get("matchedText", "")),
        str(record.get("normalizedSnippet", "")),
        int(record.get("ordinalInFunction", 0)),
    )


def _candidate_semantic_ids(record: Mapping[str, Any]) -> tuple[str, ...]:
    semantic_ids = record.get("semanticIds", [])
    if not isinstance(semantic_ids, list):
        return ()
    return tuple(sorted(str(item) for item in semantic_ids if str(item)))


def _candidate_label(record: Mapping[str, Any]) -> str:
    semantic_ids = _candidate_semantic_ids(record)
    if semantic_ids:
        return ",".join(semantic_ids)
    return str(record.get("reviewDomain", record.get("id", "UNMAPPED")))


def _key_set_fingerprint(keys: set[Any]) -> str:
    serialized = json.dumps(
        [list(key) if isinstance(key, tuple) else key for key in sorted(keys)],
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _scan_candidates(
    root: Path,
    paths: Iterable[Path],
    production_roots: Sequence[str],
    excluded_production_globs: Sequence[str],
    excluded_globs: Sequence[str],
) -> list[Candidate]:
    candidates: list[Candidate] = []
    ordinals: dict[tuple[str, str, str, str, str], int] = {}
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.suffix not in SOURCE_SUFFIXES or any(
            _matches_glob(relative, glob) for glob in excluded_globs
        ):
            continue
        lines = _read_text(path).splitlines()
        functions = _line_functions(lines)
        classification = classify_path(
            relative, production_roots, excluded_production_globs
        )
        for line_number, (line, function) in enumerate(zip(lines, functions), start=1):
            normalized_snippet = _normalize_whitespace(line)
            for pattern_name, pattern in CADENCE_PATTERNS:
                for match in pattern.finditer(line):
                    matched_text = _normalize_whitespace(match.group(0))
                    key = (
                        relative,
                        function,
                        pattern_name,
                        matched_text,
                        normalized_snippet,
                    )
                    ordinal = ordinals.get(key, 0) + 1
                    ordinals[key] = ordinal
                    candidates.append(
                        Candidate(
                            path=relative,
                            function=function,
                            pattern=pattern_name,
                            matched_text=matched_text,
                            normalized_snippet=normalized_snippet,
                            ordinal=ordinal,
                            line=line_number,
                            classification=classification,
                        )
                    )
    return candidates


def _scan_seconds_candidates(
    root: Path,
    paths: Iterable[Path],
    production_roots: Sequence[str],
    excluded_production_globs: Sequence[str],
    excluded_globs: Sequence[str],
) -> list[Candidate]:
    candidates: list[Candidate] = []
    ordinals: dict[tuple[str, str, str, str], int] = {}
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.suffix not in SOURCE_SUFFIXES or any(
            _matches_glob(relative, glob) for glob in excluded_globs
        ):
            continue
        lines = _read_text(path).splitlines()
        functions = _line_functions(lines)
        classification = classify_path(
            relative, production_roots, excluded_production_globs
        )
        for line_number, (line, function) in enumerate(zip(lines, functions), start=1):
            normalized_snippet = _normalize_whitespace(line)
            for match in SECONDS_IDENTIFIER_PATTERN.finditer(line):
                matched_text = match.group(0)
                key = (relative, function, matched_text, normalized_snippet)
                ordinal = ordinals.get(key, 0) + 1
                ordinals[key] = ordinal
                candidates.append(
                    Candidate(
                        path=relative,
                        function=function,
                        pattern="seconds-unit-identifier",
                        matched_text=matched_text,
                        normalized_snippet=normalized_snippet,
                        ordinal=ordinal,
                        line=line_number,
                        classification=classification,
                    )
                )
    return candidates


def _record_key(record: Mapping[str, Any]) -> tuple[str, str, str, int]:
    return (
        str(record.get("path", "")),
        str(record.get("function", "")),
        str(record.get("normalizedExpression", "")),
        int(record.get("ordinalInFunction", 0)),
    )


def _validate_s5_review_value(
    record: Mapping[str, Any],
    *,
    expected: bool,
    domain: str,
    candidate: str,
    findings: list[Finding],
) -> None:
    has_field = S5_REVIEW_ARTIFACT_FIELD in record
    value = record.get(S5_REVIEW_ARTIFACT_FIELD)
    if expected and value != S5_REVIEW_ARTIFACT_SHA256:
        findings.append(
            Finding(
                code="INV-SCHEMA-S5-PROVENANCE",
                domain=domain,
                path=str(record.get("path", "-")),
                candidate=candidate,
                expected=S5_REVIEW_ARTIFACT_SHA256,
                actual=json.dumps(value, sort_keys=True),
                remediation=(
                    "restore the exact lowercase frozen Gate 1 artifact SHA-256 "
                    "for this enumerated S5 reconciliation record"
                ),
            )
        )
    elif not expected and has_field:
        findings.append(
            Finding(
                code="INV-SCHEMA-S5-PROVENANCE-SCOPE",
                domain=domain,
                path=str(record.get("path", "-")),
                candidate=candidate,
                expected="field-absent",
                actual=json.dumps(value, sort_keys=True),
                remediation=(
                    "remove S5 review provenance from records outside the exact "
                    "Gate 1 reconciliation set"
                ),
            )
        )


# The legacy-fingerprint exception is bound to the one reviewed CCIP record
# tuple; adding another path to EXCLUDED_EXAMPLE_CONTENT_HASHES does not
# remove that record from legacy fingerprint authority.
def _is_reviewed_ccip_excluded_record(record: Mapping[str, Any]) -> bool:
    return (
        str(record.get("path", "")) == EXCLUDED_CCIP_EXAMPLE_PATH
        and record.get("classification") == "excluded"
        and record.get("contentSha256") == EXCLUDED_CCIP_EXAMPLE_SHA256
    )


def _is_h04_cadence_path(path: str) -> bool:
    """Match only the three H-04 files with actual cadence candidates."""

    return (
        path == "config/robinhood-parameters.json"
        or path == "scripts/params/generate_robinhood_defaults.py"
        or path == "tests/config/test_defaults_robinhood.py"
    )


def _h04_cadence_records(data: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        record
        for record in data["cadenceCandidates"]
        if _is_h04_cadence_path(str(record.get("path", "")))
    ]


def _h04_cad_sites(data: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        site
        for record in data["indirectCadence"]
        for site in record.get("sites", [])
        if isinstance(site, Mapping)
        and _is_h04_cadence_path(str(site.get("path", "")))
    ]


def _records_fingerprint(records: Sequence[Mapping[str, Any]]) -> str:
    encoded = (
        json.dumps(records, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _record_fingerprint(record: Mapping[str, Any]) -> str:
    return _records_fingerprint([record])


def _is_exact_h04_cadence_batch(data: Mapping[str, Any]) -> bool:
    records = _h04_cadence_records(data)
    sites = _h04_cad_sites(data)
    return (
        len(records) == H04_CADENCE_RECORD_COUNT
        and _records_fingerprint(records) == H04_CADENCE_RECORDS_SHA256
        and len(sites) == H04_CAD_SITE_COUNT
        and _records_fingerprint(sites) == H04_CAD_SITES_SHA256
    )


def _exact_reviewed_h04_record_fingerprints(
    data: Mapping[str, Any],
) -> tuple[frozenset[str], frozenset[str]]:
    """Return exact tuple authority only for the fully frozen reviewed batch."""

    if not _is_exact_h04_cadence_batch(data):
        return frozenset(), frozenset()
    return (
        frozenset(
            _record_fingerprint(record)
            for record in _h04_cadence_records(data)
        ),
        frozenset(
            _record_fingerprint(site) for site in _h04_cad_sites(data)
        ),
    )


def _is_reviewed_m2_production_record(record: Mapping[str, Any]) -> bool:
    return dict(record) == {
        "path": M2_GUARDED_ERC20_PATH,
        "classification": "production",
        "contentSha256": M2_GUARDED_ERC20_SHA256,
        "semanticReview": {
            "owner": "engineering/tooling",
            "status": "reviewed",
            "commit": HARDENING_REVIEW_COMMIT,
        },
    }


def _is_reviewed_m3_production_record(record: Mapping[str, Any]) -> bool:
    return dict(record) == {
        "path": M3_CREDIT_ENGINE_PATH,
        "classification": "production",
        "contentSha256": M3_CREDIT_ENGINE_SHA256,
        "semanticReview": {
            "owner": "engineering/tooling",
            "status": "reviewed",
            "commit": HARDENING_REVIEW_COMMIT,
        },
    }


# CreditEngine predates S5, so its exact pre-M3 record is part of the frozen
# legacy fingerprint.  The reviewed M3 record is substituted back to the exact
# baseline record for that computation only; any other CreditEngine record is
# left in place so the legacy fingerprint fails closed.
def _m3_baseline_credit_engine_record() -> dict[str, Any]:
    return {
        "path": M3_CREDIT_ENGINE_PATH,
        "classification": "production",
        "contentSha256": M3_CREDIT_ENGINE_BASELINE_SHA256,
        "semanticReview": {
            "owner": "engineering/tooling",
            "status": "reviewed",
            "commit": HARDENING_REVIEW_COMMIT,
        },
    }


def _s5_legacy_inventory_fingerprint(data: Mapping[str, Any]) -> str:
    exact_h04_records, exact_h04_sites = (
        _exact_reviewed_h04_record_fingerprints(data)
    )
    legacy = copy.deepcopy(dict(data))
    legacy.pop("expectedProductionCounts", None)
    legacy["directOccurrences"] = [
        record
        for record in legacy["directOccurrences"]
        if _record_key(record) not in S5_RECONCILED_DIRECT_KEYS
    ]
    legacy["cadenceCandidates"] = [
        record
        for record in legacy["cadenceCandidates"]
        if _candidate_from_record(record) not in S5_RECONCILED_CADENCE_KEYS
        and _record_fingerprint(record) not in exact_h04_records
    ]
    if exact_h04_sites:
        for record in legacy["indirectCadence"]:
            record["sites"] = [
                site
                for site in record["sites"]
                if _record_fingerprint(site) not in exact_h04_sites
            ]
    legacy["vyperPathClassifications"] = [
        _m3_baseline_credit_engine_record()
        if _is_reviewed_m3_production_record(record)
        else record
        for record in legacy["vyperPathClassifications"]
        if str(record.get("path", "")) not in S5_REVIEW_PATHS
        and not _is_reviewed_ccip_excluded_record(record)
        and not _is_reviewed_m2_production_record(record)
    ]
    encoded = (
        json.dumps(legacy, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _post_s5_production_inventory_fingerprint(
    data: Mapping[str, Any],
) -> str:
    records = [
        record
        for record in data["vyperPathClassifications"]
        if record.get("classification") == "production"
    ]
    encoded = (
        json.dumps(records, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _check_post_s5_production_inventory_fingerprint(
    data: Mapping[str, Any],
) -> list[Finding]:
    fingerprint = _post_s5_production_inventory_fingerprint(data)
    if fingerprint == POST_S5_PRODUCTION_INVENTORY_SHA256:
        return []
    return [
        Finding(
            code="INV-SCHEMA-POST-S5-PRODUCTION-FINGERPRINT",
            domain="schema",
            expected=POST_S5_PRODUCTION_INVENTORY_SHA256,
            actual=fingerprint,
            remediation=(
                "restore the exact current production-classification ledger "
                "or obtain review for a new controlling fingerprint"
            ),
        )
    ]


def _validate_s5_review_provenance(
    data: Mapping[str, Any],
    findings: list[Finding],
) -> None:
    direct_records = data["directOccurrences"]
    cadence_records = data["cadenceCandidates"]
    path_records = data["vyperPathClassifications"]

    direct_keys = {_record_key(record) for record in direct_records}
    cadence_keys = {_candidate_from_record(record) for record in cadence_records}
    path_keys = {str(record.get("path", "")) for record in path_records}
    for domain, expected, actual in (
        ("direct", S5_REVIEW_DIRECT_KEYS, direct_keys),
        ("cadence", S5_REVIEW_CADENCE_KEYS, cadence_keys),
        ("classification", S5_REVIEW_PATHS, path_keys),
    ):
        missing = expected - actual
        if missing:
            findings.append(
                Finding(
                    code="INV-SCHEMA-S5-SET",
                    domain=domain,
                    candidate=f"missing={len(missing)}",
                    expected=_key_set_fingerprint(expected),
                    actual=_key_set_fingerprint(actual & expected),
                    remediation=(
                        "restore every exact record covered by the 28 reviewed "
                        "S5 inventory dispositions"
                    ),
                )
            )

    for record in direct_records:
        key = _record_key(record)
        _validate_s5_review_value(
            record,
            expected=key in S5_REVIEW_DIRECT_KEYS,
            domain="direct",
            candidate=str(record.get("id", "UNMAPPED")),
            findings=findings,
        )
    for record in cadence_records:
        key = _candidate_from_record(record)
        _validate_s5_review_value(
            record,
            expected=key in S5_REVIEW_CADENCE_KEYS,
            domain="cadence",
            candidate=_candidate_label(record),
            findings=findings,
        )
    for record in path_records:
        path = str(record.get("path", ""))
        _validate_s5_review_value(
            record,
            expected=path in S5_REVIEW_PATHS,
            domain="classification",
            candidate=path,
            findings=findings,
        )
    for domain, collection in (
        ("indirect", data["indirectCadence"]),
        ("timestamp", data["timestampContext"]),
        ("seconds", data["secondsUnitCandidates"]),
        ("mixed", data["allowedMixedClockFunctions"]),
    ):
        for record in collection:
            _validate_s5_review_value(
                record,
                expected=False,
                domain=domain,
                candidate=str(record.get("id", _candidate_label(record))),
                findings=findings,
            )


def _check_s5_legacy_inventory_fingerprint(
    data: Mapping[str, Any],
) -> list[Finding]:
    fingerprint = _s5_legacy_inventory_fingerprint(data)
    if fingerprint == S5_LEGACY_INVENTORY_SHA256:
        return []
    return [
        Finding(
            code="INV-SCHEMA-S5-LEGACY-FINGERPRINT",
            domain="schema",
            expected=S5_LEGACY_INVENTORY_SHA256,
            actual=fingerprint,
            remediation=(
                "restore every inventory byte outside the exact S5 "
                "reconciliation set"
            ),
        )
    ]


def _placeholder(value: Any) -> bool:
    return not isinstance(value, str) or value.strip().lower() in PLACEHOLDERS


def _validate_semantic_review(
    record: Mapping[str, Any],
    domain: str,
    candidate: str,
    findings: list[Finding],
    expected_owner: str | None = None,
    expected_commit: str | None = None,
) -> None:
    review = record.get("semanticReview")
    if not isinstance(review, Mapping):
        findings.append(
            Finding(
                code="INV-SCHEMA-REVIEW",
                domain=domain,
                path=str(record.get("path", "-")),
                candidate=candidate,
                actual="missing",
                remediation="add the immutable reviewed owner, status, and commit",
            )
        )
        return
    if expected_owner is not None and review.get("owner") != expected_owner:
        findings.append(
            Finding(
                code="INV-SCHEMA-OWNER",
                domain=domain,
                path=str(record.get("path", "-")),
                candidate=candidate,
                expected=expected_owner,
                actual=str(review.get("owner", "missing")),
                remediation="restore the approved semantic-review authority",
            )
        )
    if expected_commit is not None and review.get("commit") != expected_commit:
        findings.append(
            Finding(
                code="INV-SCHEMA-PROVENANCE",
                domain=domain,
                path=str(record.get("path", "-")),
                candidate=candidate,
                expected=expected_commit,
                actual=str(review.get("commit", "missing")),
                remediation="restore the immutable commit that actually reviewed this record",
            )
        )
    for field in ("owner", "status", "commit"):
        value = review.get(field)
        invalid = _placeholder(value)
        if field == "commit" and isinstance(value, str):
            invalid = invalid or re.fullmatch(r"[0-9a-f]{40}", value) is None
        if invalid:
            findings.append(
                Finding(
                    code="INV-SCHEMA-PLACEHOLDER",
                    domain=domain,
                    path=str(record.get("path", "-")),
                    candidate=candidate,
                    expected=f"reviewed-{field}",
                    actual=json.dumps(value, sort_keys=True),
                    remediation="obtain the named semantic owner's review; do not self-approve",
                )
            )
    status = str(review.get("status", "")).strip().lower()
    if status == "ignore":
        justification = review.get("justification")
        if _placeholder(justification):
            findings.append(
                Finding(
                    code="INV-SCHEMA-IGNORE",
                    domain=domain,
                    path=str(record.get("path", "-")),
                    candidate=candidate,
                    actual="ignore-without-reviewed-justification",
                    remediation="obtain semantic-owner review and a non-placeholder justification",
                )
            )
    elif status != "reviewed":
        findings.append(
            Finding(
                code="INV-SCHEMA-STATUS",
                domain=domain,
                path=str(record.get("path", "-")),
                candidate=candidate,
                expected="reviewed",
                actual=status or "missing",
                remediation="obtain semantic-owner review; skipped or invented statuses are invalid",
            )
        )


def _load_inventory(path: Path) -> tuple[dict[str, Any] | None, list[Finding]]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [
            Finding(
                code="INV-SCHEMA-READ",
                domain="schema",
                path=path.as_posix(),
                actual=type(exc).__name__,
                remediation="restore the reviewed inventory file",
            )
        ]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, [
            Finding(
                code="INV-SCHEMA-JSON",
                domain="schema",
                path=path.as_posix(),
                line=exc.lineno,
                actual=exc.msg.replace(" ", "_"),
                remediation="repair JSON without changing semantic classifications",
            )
        ]
    if not isinstance(data, dict):
        return None, [
            Finding(
                code="INV-SCHEMA-TYPE",
                domain="schema",
                path=path.as_posix(),
                expected="object",
                actual=type(data).__name__,
            )
        ]
    return data, []


def _validate_schema(data: Mapping[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    version = data.get("schemaVersion")
    if version != EXPECTED_SCHEMA_VERSION:
        findings.append(
            Finding(
                code="INV-SCHEMA-VERSION",
                domain="schema",
                expected=str(EXPECTED_SCHEMA_VERSION),
                actual=str(version),
                remediation="use a separately reviewed checker/schema migration",
            )
        )
        return findings
    expected_counts = data.get("expectedProductionCounts")
    actual_counts = (
        expected_counts.get("occurrences") if isinstance(expected_counts, Mapping) else None,
        expected_counts.get("lines") if isinstance(expected_counts, Mapping) else None,
        expected_counts.get("files") if isinstance(expected_counts, Mapping) else None,
    )
    if actual_counts != EXPECTED_PRODUCTION_COUNTS:
        findings.append(
            Finding(
                code="INV-SCHEMA-BASELINE",
                domain="schema",
                expected="/".join(map(str, EXPECTED_PRODUCTION_COUNTS)),
                actual="/".join(map(str, actual_counts)),
                remediation="reconcile source drift with the semantic owner; do not update counts mechanically",
            )
        )
    collections = {
        "direct": data.get("directOccurrences"),
        "indirect": data.get("indirectCadence"),
        "timestamp": data.get("timestampContext"),
        "cadence": data.get("cadenceCandidates"),
        "seconds": data.get("secondsUnitCandidates"),
        "mixed": data.get("allowedMixedClockFunctions"),
        "classification": data.get("vyperPathClassifications"),
    }
    for domain, value in collections.items():
        if not isinstance(value, list) or not value:
            findings.append(
                Finding(
                    code="INV-SCHEMA-COLLECTION",
                    domain=domain,
                    expected="nonempty-list",
                    actual=type(value).__name__,
                )
            )
        elif any(not isinstance(record, Mapping) for record in value):
            findings.append(
                Finding(
                    code="INV-SCHEMA-RECORD",
                    domain=domain,
                    expected="object-records",
                    actual="non-object-record",
                )
            )
    if findings:
        return findings
    h04_records = _h04_cadence_records(data)
    h04_sites = _h04_cad_sites(data)
    exact_h04_batch = _is_exact_h04_cadence_batch(data)
    if not exact_h04_batch:
        findings.append(
            Finding(
                code="INV-SCHEMA-H04-CADENCE-BATCH",
                domain="cadence",
                expected=(
                    f"records={H04_CADENCE_RECORD_COUNT}/"
                    f"{H04_CADENCE_RECORDS_SHA256},"
                    f"cad_sites={H04_CAD_SITE_COUNT}/{H04_CAD_SITES_SHA256}"
                ),
                actual=(
                    f"records={len(h04_records)}/"
                    f"{_records_fingerprint(h04_records)},"
                    f"cad_sites={len(h04_sites)}/"
                    f"{_records_fingerprint(h04_sites)}"
                ),
                remediation=(
                    "restore the exact reviewed H-04 cadence records and CAD-001 "
                    "mirrors; no registry or path expansion inherits authority"
                ),
            )
        )
    expected_path_config = (
        EXPECTED_PRODUCTION_ROOTS,
        EXPECTED_EXCLUDED_PRODUCTION_GLOBS,
        EXPECTED_ALLOWED_NONPRODUCTION_GLOBS,
        EXPECTED_INTERFACE_ROOTS,
        EXPECTED_CADENCE_ROOTS,
        EXPECTED_CADENCE_EXCLUDED_GLOBS,
    )
    actual_path_config = (
        data.get("productionRoots"),
        data.get("excludedProductionGlobs"),
        data.get("allowedNonProductionGlobs"),
        data.get("interfaceRoots"),
        data.get("cadenceRoots"),
        data.get("cadenceExcludedGlobs"),
    )
    if actual_path_config != expected_path_config:
        findings.append(
            Finding(
                code="INV-SCHEMA-PATH-CONFIG",
                domain="classification",
                expected=json.dumps(expected_path_config, separators=(",", ":")),
                actual=json.dumps(actual_path_config, separators=(",", ":")),
                remediation="restore the reviewed path roots and exclusions; paths may not evade discovery",
            )
        )
    if data.get("reviewAuthorities") != EXPECTED_REVIEW_AUTHORITIES:
        findings.append(
            Finding(
                code="INV-SCHEMA-AUTHORITY",
                domain="schema",
                expected=json.dumps(
                    EXPECTED_REVIEW_AUTHORITIES, sort_keys=True, separators=(",", ":")
                ),
                actual=json.dumps(
                    data.get("reviewAuthorities"), sort_keys=True, separators=(",", ":")
                ),
                remediation="restore the approved semantic-review ownership mapping",
            )
        )
    if data.get("reviewProvenance") != EXPECTED_REVIEW_PROVENANCE:
        findings.append(
            Finding(
                code="INV-SCHEMA-PROVENANCE",
                domain="schema",
                expected=json.dumps(
                    EXPECTED_REVIEW_PROVENANCE,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                actual=json.dumps(
                    data.get("reviewProvenance"),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                remediation="restore the Track 3 review and owner-approval commit references",
            )
        )
    documentation = data.get("schemaDocumentation")
    required_documentation = {
        "pathModel",
        "cadenceCoverage",
        "historicalExclusions",
        "functionAttribution",
        "reviewAuthorities",
        "reviewProvenance",
    }
    if not isinstance(documentation, Mapping) or any(
        _placeholder(documentation.get(field))
        for field in required_documentation
    ):
        findings.append(
            Finding(
                code="INV-SCHEMA-DOCUMENTATION",
                domain="schema",
                expected="non-placeholder-discovery-and-review-caveats",
                actual=type(documentation).__name__,
                remediation="restore the reviewed schema documentation and declared exclusions",
            )
        )
    expected_pattern_config = [
        {"name": name, "expression": pattern.pattern}
        for name, pattern in CADENCE_PATTERNS
    ]
    if data.get("cadencePatterns") != expected_pattern_config:
        findings.append(
            Finding(
                code="INV-SCHEMA-PATTERNS",
                domain="indirect",
                expected="reviewed-pattern-definitions",
                actual="changed",
                remediation="obtain semantic and tooling review before changing cadence discovery",
            )
        )
    _validate_s5_review_provenance(data, findings)

    direct_records = data["directOccurrences"]
    direct_keys: dict[tuple[str, str, str, int], list[Mapping[str, Any]]] = {}
    for record in direct_records:
        if not isinstance(record, Mapping):
            findings.append(
                Finding(code="INV-SCHEMA-RECORD", domain="direct", actual=type(record).__name__)
            )
            continue
        key = _record_key(record)
        direct_keys.setdefault(key, []).append(record)
        _validate_semantic_review(
            record,
            "direct",
            str(record.get("id", "UNMAPPED")),
            findings,
            "protocol/security",
            TRACK3_REVIEW_COMMIT,
        )
    for key, records in direct_keys.items():
        if len(records) != 1:
            findings.append(
                Finding(
                    code="INV-SCHEMA-DUPLICATE",
                    domain="direct",
                    path=key[0],
                    function=key[1],
                    candidate=",".join(sorted(str(record.get("id")) for record in records)),
                    expected="1",
                    actual=str(len(records)),
                )
            )
    duplicate_domains: tuple[
        tuple[
            str,
            Sequence[Mapping[str, Any]],
            Callable[[Mapping[str, Any]], tuple[Any, ...]],
        ],
        ...,
    ] = (
        ("timestamp", data["timestampContext"], _record_key),
        (
            "indirect",
            data["indirectCadence"],
            lambda record: (str(record.get("id", "")),),
        ),
        ("cadence", data["cadenceCandidates"], _candidate_from_record),
        ("seconds", data["secondsUnitCandidates"], _candidate_from_record),
        (
            "mixed",
            data["allowedMixedClockFunctions"],
            lambda record: (
                str(record.get("path", "")),
                str(record.get("function", "")),
            ),
        ),
    )
    for domain, records, key_function in duplicate_domains:
        records_by_key: dict[tuple[Any, ...], list[Mapping[str, Any]]] = {}
        for record in records:
            records_by_key.setdefault(key_function(record), []).append(record)
        for key, duplicate_records in records_by_key.items():
            if len(duplicate_records) == 1:
                continue
            first = duplicate_records[0]
            findings.append(
                Finding(
                    code="INV-SCHEMA-DUPLICATE",
                    domain=domain,
                    path=str(first.get("path", "-")),
                    function=str(first.get("function", "-")),
                    candidate=_candidate_label(first),
                    expected="1",
                    actual=str(len(duplicate_records)),
                    snippet=json.dumps(key, ensure_ascii=True),
                )
            )

    bn_ids = {str(record.get("id")) for record in direct_records if isinstance(record, Mapping)}
    cad_ids = {
        str(record.get("id"))
        for record in data["indirectCadence"]
        if isinstance(record, Mapping)
    }
    ts_ids = {
        str(record.get("id"))
        for record in data["timestampContext"]
        if isinstance(record, Mapping)
    }
    for domain, expected, actual in (
        ("direct", EXPECTED_BN_IDS, bn_ids),
        ("indirect", EXPECTED_CAD_IDS, cad_ids),
        ("timestamp", EXPECTED_TS_IDS, ts_ids),
    ):
        if actual != expected:
            findings.append(
                Finding(
                    code="INV-SCHEMA-ID-SET",
                    domain=domain,
                    expected=",".join(sorted(expected)),
                    actual=",".join(sorted(actual)),
                    remediation="reconcile stable IDs with the reviewed Track 3 inventory; never renumber",
                )
            )
    for domain, records, expected_owner, expected_commit in (
        (
            "indirect",
            data["indirectCadence"],
            "risk/oracle",
            TRACK3_REVIEW_COMMIT,
        ),
        (
            "timestamp",
            data["timestampContext"],
            "protocol/security",
            TRACK3_REVIEW_COMMIT,
        ),
        (
            "seconds",
            data["secondsUnitCandidates"],
            "protocol/security",
            HARDENING_REVIEW_COMMIT,
        ),
        (
            "mixed",
            data["allowedMixedClockFunctions"],
            "protocol/security",
            HARDENING_REVIEW_COMMIT,
        ),
        (
            "classification",
            data["vyperPathClassifications"],
            "engineering/tooling",
            HARDENING_REVIEW_COMMIT,
        ),
    ):
        for record in records:
            if isinstance(record, Mapping):
                _validate_semantic_review(
                    record,
                    domain,
                    str(record.get("id", _candidate_label(record))),
                    findings,
                    expected_owner,
                    expected_commit,
                )
    for record in data["cadenceCandidates"]:
        semantic_ids = _candidate_semantic_ids(record)
        expected_owner = "risk/oracle" if "CAD-001" in semantic_ids else "protocol/security"
        expected_commit = (
            TRACK3_REVIEW_COMMIT
            if "CAD-001" in semantic_ids
            else (
                H04_REVIEW_COMMIT
                if exact_h04_batch
                and _is_h04_cadence_path(str(record.get("path", "")))
                else HARDENING_REVIEW_COMMIT
            )
        )
        _validate_semantic_review(
            record,
            "cadence",
            _candidate_label(record),
            findings,
            expected_owner,
            expected_commit,
        )
    reviewed_semantic_ids = EXPECTED_BN_IDS | EXPECTED_CAD_IDS | EXPECTED_TS_IDS
    for domain, records in (
        ("cadence", data["cadenceCandidates"]),
        ("seconds", data["secondsUnitCandidates"]),
    ):
        for record in records:
            semantic_ids_value = record.get("semanticIds")
            semantic_ids = _candidate_semantic_ids(record)
            invalid_semantic_ids = (
                not isinstance(semantic_ids_value, list)
                or len(semantic_ids) != len(semantic_ids_value)
                or len(semantic_ids) != len(set(semantic_ids))
                or not set(semantic_ids).issubset(reviewed_semantic_ids)
            )
            if (
                "semanticId" in record
                or invalid_semantic_ids
                or record.get("reviewDomain") != "cadence-surface"
            ):
                findings.append(
                    Finding(
                        code="INV-SCHEMA-SEMANTIC-LINK",
                        domain=domain,
                        path=str(record.get("path", "-")),
                        candidate=_candidate_label(record),
                        expected="semanticIds-list+cadence-surface-domain",
                        actual=(
                            f"semanticId={record.get('semanticId', 'absent')},"
                            f"semanticIds={json.dumps(semantic_ids_value)},"
                            f"reviewDomain={record.get('reviewDomain')}"
                        ),
                        remediation="use reviewed stable IDs only; do not invent pseudo-identifiers",
                    )
                )
    cad_sites_by_key: dict[
        tuple[str, str, str, str, str, int],
        list[tuple[str, Mapping[str, Any]]],
    ] = {}
    for record in data["indirectCadence"]:
        sites_value = record.get("sites")
        if not isinstance(sites_value, list) or not sites_value:
            findings.append(
                Finding(
                    code="INV-SCHEMA-COLLECTION",
                    domain="indirect",
                    candidate=str(record.get("id", "UNMAPPED")),
                    expected="nonempty-sites-list",
                    actual=type(sites_value).__name__,
                )
            )
            continue
        for site in sites_value:
            if not isinstance(site, Mapping):
                findings.append(
                    Finding(
                        code="INV-SCHEMA-RECORD",
                        domain="indirect",
                        candidate=str(record.get("id", "UNMAPPED")),
                        expected="object-site-record",
                        actual=type(site).__name__,
                    )
                )
                continue
            cad_sites_by_key.setdefault(
                _candidate_from_record(site), []
            ).append((str(record.get("id", "UNMAPPED")), site))
    for key, sites in cad_sites_by_key.items():
        if len(sites) == 1:
            continue
        stable_id, first = sites[0]
        findings.append(
            Finding(
                code="INV-SCHEMA-DUPLICATE",
                domain="indirect",
                path=str(first.get("path", "-")),
                function=str(first.get("function", "-")),
                candidate=stable_id,
                expected="1",
                actual=str(len(sites)),
                snippet=json.dumps(key, ensure_ascii=True),
                remediation="remove the redundant reviewed cadence-site row",
            )
        )
    cad_site_keys = set(cad_sites_by_key)
    reviewed_cad_keys = {
        _candidate_from_record(record)
        for record in data["cadenceCandidates"]
        if isinstance(record, Mapping)
        and "CAD-001" in _candidate_semantic_ids(record)
    }
    if cad_site_keys != reviewed_cad_keys:
        findings.append(
            Finding(
                code="INV-SCHEMA-CAD-SITES",
                domain="indirect",
                candidate="CAD-001",
                expected=(
                    f"count={len(reviewed_cad_keys)},"
                    f"sha256={_key_set_fingerprint(reviewed_cad_keys)}"
                ),
                actual=(
                    f"count={len(cad_site_keys)},"
                    f"sha256={_key_set_fingerprint(cad_site_keys)}"
                ),
                remediation="restore the reviewed CAD-001 site mapping; do not suppress cadence candidates",
            )
        )
    path_records = [
        record
        for record in data["vyperPathClassifications"]
        if isinstance(record, Mapping)
    ]
    path_names = [str(record.get("path", "")) for record in path_records]
    if len(path_names) != len(set(path_names)) or any(not name for name in path_names):
        findings.append(
            Finding(
                code="INV-SCHEMA-PATH-RECORD",
                domain="classification",
                expected="unique-nonempty-paths",
                actual=str(len(path_names)),
            )
        )
    for record in path_records:
        classification = record.get("classification")
        content_hash = record.get("contentSha256")
        reviewed_excluded = classification == "excluded" and (
            content_hash
            == EXCLUDED_EXAMPLE_CONTENT_HASHES.get(str(record.get("path", "")))
        )
        if (
            classification not in {
                "production",
                "mock",
                "testing",
                "test",
                "interface",
            }
            and not reviewed_excluded
        ) or not (
            isinstance(content_hash, str)
            and re.fullmatch(r"[0-9a-f]{64}", content_hash)
        ):
            findings.append(
                Finding(
                    code="INV-SCHEMA-PATH-RECORD",
                    domain="classification",
                    path=str(record.get("path", "-")),
                    expected="reviewed-classification+sha256",
                    actual=f"{classification}:{content_hash}",
                )
            )
    return findings


def _current_vyper_classifications(
    root: Path,
    production_roots: Sequence[str],
    excluded_production_globs: Sequence[str],
) -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for path in _iter_files(root, ["."]):
        if path.suffix not in VYPER_SUFFIXES:
            continue
        relative = path.relative_to(root).as_posix()
        records[relative] = {
            "classification": classify_path(
                relative, production_roots, excluded_production_globs
            ),
            "contentSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    return records


def _check_path_classifications(
    root: Path,
    records: Sequence[Mapping[str, Any]],
    production_roots: Sequence[str],
    excluded_production_globs: Sequence[str],
) -> list[Finding]:
    findings: list[Finding] = []
    expected = {
        str(record.get("path")): {
            "classification": str(record.get("classification")),
            "contentSha256": str(record.get("contentSha256")),
        }
        for record in records
    }
    actual = _current_vyper_classifications(
        root, production_roots, excluded_production_globs
    )
    missing = set(expected) - set(actual)
    added = set(actual) - set(expected)
    consumed_missing: set[str] = set()
    consumed_added: set[str] = set()
    for old_path in sorted(missing):
        old_hash = expected[old_path]["contentSha256"]
        matches = [
            new_path
            for new_path in sorted(added)
            if actual[new_path]["contentSha256"] == old_hash
        ]
        if len(matches) != 1:
            continue
        new_path = matches[0]
        consumed_missing.add(old_path)
        consumed_added.add(new_path)
        findings.append(
            Finding(
                code="INV-PATH-MOVED",
                domain="classification",
                path=new_path,
                snippet=f"{old_path}->{new_path}",
                expected=expected[old_path]["classification"],
                actual=actual[new_path]["classification"],
                remediation=(
                    "obtain engineering/tooling path review and protocol/security "
                    "review for any production-boundary move"
                ),
            )
        )
    for path in sorted(added - consumed_added):
        findings.append(
            Finding(
                code="INV-PATH-NEW",
                domain="classification",
                path=path,
                actual=actual[path]["classification"],
                remediation=(
                    "obtain engineering/tooling path review and semantic-owner "
                    "review before adding the Vyper source"
                ),
            )
        )
    for path in sorted(missing - consumed_missing):
        findings.append(
            Finding(
                code="INV-PATH-MISSING",
                domain="classification",
                path=path,
                expected=expected[path]["classification"],
                actual="missing",
                remediation=(
                    "obtain engineering/tooling path review and semantic-owner "
                    "review before removing the Vyper source"
                ),
            )
        )
    for path in sorted(set(expected) & set(actual)):
        if expected[path]["classification"] != actual[path]["classification"]:
            findings.append(
                Finding(
                    code="INV-PATH-CLASSIFICATION",
                    domain="classification",
                    path=path,
                    expected=expected[path]["classification"],
                    actual=actual[path]["classification"],
                    remediation=(
                        "obtain engineering/tooling path review and protocol/security "
                        "review for any production-boundary classification change"
                    ),
                )
            )
        if (
            expected[path]["classification"] == "excluded"
            and expected[path]["contentSha256"] != actual[path]["contentSha256"]
        ):
            findings.append(
                Finding(
                    code="INV-PATH-EXCLUDED-CONTENT",
                    domain="classification",
                    path=path,
                    expected=expected[path]["contentSha256"],
                    actual=actual[path]["contentSha256"],
                    remediation=(
                        "obtain engineering/tooling review before changing an "
                        "excluded reference example; its content hash is frozen"
                    ),
                )
            )
        if (
            path == M2_GUARDED_ERC20_PATH
            and actual[path]["contentSha256"] != M2_GUARDED_ERC20_SHA256
        ):
            findings.append(
                Finding(
                    code="INV-PATH-M2-CONTENT",
                    domain="classification",
                    path=path,
                    expected=M2_GUARDED_ERC20_SHA256,
                    actual=actual[path]["contentSha256"],
                    remediation=(
                        "restore the exact reviewed GuardedErc20 source bytes; "
                        "changing the M2 production identity requires new review"
                    ),
                )
            )
        if (
            path == M3_CREDIT_ENGINE_PATH
            and actual[path]["contentSha256"] != M3_CREDIT_ENGINE_SHA256
        ):
            findings.append(
                Finding(
                    code="INV-PATH-M3-CONTENT",
                    domain="classification",
                    path=path,
                    expected=M3_CREDIT_ENGINE_SHA256,
                    actual=actual[path]["contentSha256"],
                    remediation=(
                        "restore the exact reviewed CreditEngine source bytes; "
                        "changing the M3 production identity requires new review"
                    ),
                )
            )
    return findings


def _production_vyper_files(
    root: Path,
    production_roots: Sequence[str],
    excluded_production_globs: Sequence[str],
) -> tuple[list[Path], list[Finding]]:
    production: list[Path] = []
    findings: list[Finding] = []
    for path in _iter_files(root, ["."]):
        if path.suffix not in VYPER_SUFFIXES:
            continue
        relative = path.relative_to(root).as_posix()
        classification = classify_path(
            relative, production_roots, excluded_production_globs
        )
        if classification == "production" and path.suffix == ".vy":
            production.append(path)
        elif classification == "unclassified":
            findings.append(
                Finding(
                    code="INV-PATH-UNCLASSIFIED",
                    domain="classification",
                    path=relative,
                    actual="vyper",
                    remediation="obtain path-classification review before adding or moving the contract",
                )
            )
    return sorted(production), findings


def _check_imports(root: Path, production_paths: Sequence[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in production_paths:
        relative = path.relative_to(root).as_posix()
        text = _read_text(path)
        lines = text.splitlines()
        for match in IMPORT_PATTERN.finditer(text):
            target = match.group(1).replace("/", ".")
            if "contracts.mock" not in target and "contracts.testing" not in target:
                continue
            line = text.count("\n", 0, match.start()) + 1
            findings.append(
                Finding(
                    code="INV-IMPORT-PROD-NONPROD",
                    domain="import",
                    path=relative,
                    line=line,
                    snippet=_normalize_whitespace(lines[line - 1]),
                    actual=target,
                    remediation="remove the production dependency on mock/testing code and obtain review",
                )
            )
    return findings


def _compare_occurrences(
    actual: Sequence[Occurrence],
    expected_records: Sequence[Mapping[str, Any]],
    domain: str,
    new_code: str,
    missing_code: str,
    move_code: str,
) -> list[Finding]:
    findings: list[Finding] = []
    actual_by_key = {occurrence.key: occurrence for occurrence in actual}
    expected_by_key = {_record_key(record): record for record in expected_records}

    for key in sorted(actual_by_key):
        occurrence = actual_by_key[key]
        record = expected_by_key.get(key)
        if record is None:
            findings.append(
                Finding(
                    code=new_code,
                    domain=domain,
                    path=occurrence.path,
                    function=occurrence.function,
                    line=occurrence.line,
                    snippet=occurrence.snippet,
                    actual=occurrence.normalized_expression,
                )
            )
            continue
        reviewed_line = int(record.get("reviewedLine", 0))
        if reviewed_line != occurrence.line:
            findings.append(
                Finding(
                    code=move_code,
                    domain=domain,
                    path=occurrence.path,
                    function=occurrence.function,
                    line=occurrence.line,
                    snippet=occurrence.snippet,
                    candidate=str(record.get("id", "UNMAPPED")),
                    expected=str(reviewed_line),
                    actual=str(occurrence.line),
                    remediation="obtain semantic review of the moved occurrence; line remains diagnostic, not identity",
                )
            )

    for key in sorted(expected_by_key):
        if key in actual_by_key:
            continue
        record = expected_by_key[key]
        findings.append(
            Finding(
                code=missing_code,
                domain=domain,
                path=key[0],
                function=key[1],
                line=int(record.get("reviewedLine", 0)),
                snippet=str(record.get("reviewedSnippet", key[2])),
                candidate=str(record.get("id", "UNMAPPED")),
                expected=key[2],
                actual="missing",
            )
        )
    return findings


def _compare_candidates(
    actual: Sequence[Candidate],
    expected_records: Sequence[Mapping[str, Any]],
    domain: str,
    new_code: str,
    missing_code: str,
    move_code: str,
) -> list[Finding]:
    findings: list[Finding] = []
    actual_by_key = {candidate.key: candidate for candidate in actual}
    expected_by_key: dict[tuple[str, str, str, str, str, int], Mapping[str, Any]] = {}
    for record in expected_records:
        key = _candidate_from_record(record)
        if key in expected_by_key:
            findings.append(
                Finding(
                    code="INV-SCHEMA-DUPLICATE",
                    domain=domain,
                    path=key[0],
                    function=key[1],
                    snippet=key[4],
                )
            )
        expected_by_key[key] = record
    for key in sorted(actual_by_key):
        candidate = actual_by_key[key]
        record = expected_by_key.get(key)
        if record is None:
            findings.append(
                Finding(
                    code=new_code,
                    domain=domain,
                    path=candidate.path,
                    function=candidate.function,
                    line=candidate.line,
                    snippet=candidate.normalized_snippet,
                    actual=(
                        f"{candidate.classification}:"
                        f"{candidate.pattern}:{candidate.matched_text}"
                    ),
                    remediation=(
                        "obtain probe/mock review before inventorying this non-production cadence dependency"
                        if candidate.classification in {"mock", "testing", "test"}
                        else "obtain semantic-owner review before inventorying this cadence dependency"
                    ),
                )
            )
            continue
        reviewed_line = int(record.get("reviewedLine", 0))
        if reviewed_line != candidate.line:
            findings.append(
                Finding(
                    code=move_code,
                    domain=domain,
                    path=candidate.path,
                    function=candidate.function,
                    line=candidate.line,
                    snippet=candidate.normalized_snippet,
                    candidate=_candidate_label(record),
                    expected=str(reviewed_line),
                    actual=str(candidate.line),
                )
            )
    for key in sorted(expected_by_key):
        if key in actual_by_key:
            continue
        record = expected_by_key[key]
        findings.append(
            Finding(
                code=missing_code,
                domain=domain,
                path=key[0],
                function=key[1],
                line=int(record.get("reviewedLine", 0)),
                snippet=key[4],
                candidate=_candidate_label(record),
                expected=f"{key[2]}:{key[3]}",
                actual="missing",
            )
        )
    return findings


def _mixed_clock_functions(
    root: Path, production_paths: Sequence[Path]
) -> list[tuple[str, str]]:
    mixed: list[tuple[str, str]] = []
    for path in production_paths:
        relative = path.relative_to(root).as_posix()
        text = _read_text(path)
        lines = text.splitlines()
        functions = _line_functions(lines)
        bodies: dict[str, list[str]] = {}
        for function, line in zip(functions, lines):
            bodies.setdefault(function, []).append(line)
        for function, body_lines in bodies.items():
            body = "\n".join(body_lines)
            if DIRECT_PATTERN.search(body) and TIMESTAMP_PATTERN.search(body):
                mixed.append((relative, function))
    return sorted(mixed)


def _nonproduction_counts(
    root: Path,
    all_files: Sequence[Path],
    production_roots: Sequence[str],
    excluded_production_globs: Sequence[str],
) -> dict[str, tuple[int, int, int]]:
    grouped: dict[str, list[Path]] = {"mock": [], "testing": [], "test": []}
    for path in all_files:
        relative = path.relative_to(root).as_posix()
        classification = classify_path(
            relative, production_roots, excluded_production_globs
        )
        if classification in grouped and path.suffix in SOURCE_SUFFIXES:
            grouped[classification].append(path)
    return {
        classification: _scan_fixed_counts(paths, "block.number")
        for classification, paths in grouped.items()
    }


def check_repository(
    repository_root: Path | str,
    inventory_path: Path | str | None = None,
) -> CheckResult:
    root = Path(repository_root).resolve()
    inventory = (
        Path(inventory_path).resolve()
        if inventory_path is not None
        else root / "config" / "block-clock-inventory.json"
    )
    data, findings = _load_inventory(inventory)
    if data is None:
        return CheckResult(findings=findings, success_lines=[])
    findings.extend(_validate_schema(data))
    if findings:
        return CheckResult(findings=findings, success_lines=[])

    production_roots = [str(item) for item in data["productionRoots"]]
    excluded_production_globs = [
        str(item) for item in data["excludedProductionGlobs"]
    ]
    findings.extend(
        _check_path_classifications(
            root,
            data["vyperPathClassifications"],
            production_roots,
            excluded_production_globs,
        )
    )
    production_paths, classification_findings = _production_vyper_files(
        root, production_roots, excluded_production_globs
    )
    findings.extend(classification_findings)
    findings.extend(_check_imports(root, production_paths))

    direct_actual = _scan_expression_files(
        root, production_paths, DIRECT_PATTERN
    )
    fixed_counts = _scan_fixed_counts(production_paths, "block.number")
    expected_counts = data["expectedProductionCounts"]
    active_expected = (
        int(expected_counts["occurrences"]),
        int(expected_counts["lines"]),
        int(expected_counts["files"]),
    )
    if fixed_counts != active_expected:
        findings.append(
            Finding(
                code="INV-DIRECT-COUNT",
                domain="direct",
                expected="/".join(map(str, active_expected)),
                actual="/".join(map(str, fixed_counts)),
                remediation="reconcile the fixed-string source delta with protocol/security",
            )
        )
    if len(direct_actual) != fixed_counts[0]:
        first = next(
            (
                occurrence
                for occurrence in direct_actual
                if occurrence.normalized_expression != "block.number"
            ),
            direct_actual[0] if direct_actual else None,
        )
        findings.append(
            Finding(
                code="INV-PARSER-FIXED-DISAGREE",
                domain="direct",
                path=first.path if first else "-",
                function=first.function if first else "-",
                line=first.line if first else 0,
                snippet=first.snippet if first else "-",
                expected=str(fixed_counts[0]),
                actual=str(len(direct_actual)),
                remediation="repair discovery so the parser cannot suppress a fixed-string delta",
            )
        )
    findings.extend(
        _compare_occurrences(
            direct_actual,
            data["directOccurrences"],
            "direct",
            "INV-DIRECT-NEW",
            "INV-DIRECT-MISSING",
            "INV-DIRECT-MOVE",
        )
    )

    timestamp_actual = _scan_expression_files(
        root, production_paths, TIMESTAMP_PATTERN
    )
    timestamp_counts = _scan_fixed_counts(production_paths, "block.timestamp")
    expected_timestamp_counts = data.get("expectedTimestampCounts", {})
    timestamp_expected = (
        int(expected_timestamp_counts.get("occurrences", -1)),
        int(expected_timestamp_counts.get("lines", -1)),
        int(expected_timestamp_counts.get("files", -1)),
    )
    if timestamp_expected != EXPECTED_TIMESTAMP_COUNTS:
        findings.append(
            Finding(
                code="INV-SCHEMA-TIMESTAMP-BASELINE",
                domain="timestamp",
                expected="/".join(map(str, EXPECTED_TIMESTAMP_COUNTS)),
                actual="/".join(map(str, timestamp_expected)),
            )
        )
    if timestamp_counts != timestamp_expected:
        findings.append(
            Finding(
                code="INV-TIMESTAMP-COUNT",
                domain="timestamp",
                expected="/".join(map(str, timestamp_expected)),
                actual="/".join(map(str, timestamp_counts)),
            )
        )
    findings.extend(
        _compare_occurrences(
            timestamp_actual,
            data["timestampContext"],
            "timestamp",
            "INV-TIMESTAMP-NEW",
            "INV-TIMESTAMP-MISSING",
            "INV-TIMESTAMP-MOVE",
        )
    )

    cadence_roots = [str(item) for item in data["cadenceRoots"]]
    cadence_paths = _iter_files(root, cadence_roots)
    cadence_excluded_globs = [
        str(item) for item in data.get("cadenceExcludedGlobs", [])
    ]
    cadence_actual = _scan_candidates(
        root,
        cadence_paths,
        production_roots,
        excluded_production_globs,
        cadence_excluded_globs,
    )
    findings.extend(
        _compare_candidates(
            cadence_actual,
            data["cadenceCandidates"],
            "indirect",
            "INV-CADENCE-NEW",
            "INV-CADENCE-MISSING",
            "INV-CADENCE-MOVE",
        )
    )
    seconds_actual = _scan_seconds_candidates(
        root,
        cadence_paths,
        production_roots,
        excluded_production_globs,
        cadence_excluded_globs,
    )
    findings.extend(
        _compare_candidates(
            seconds_actual,
            data.get("secondsUnitCandidates", []),
            "timestamp-units",
            "INV-SECONDS-UNIT-NEW",
            "INV-SECONDS-UNIT-MISSING",
            "INV-SECONDS-UNIT-MOVE",
        )
    )

    actual_mixed = set(_mixed_clock_functions(root, production_paths))
    expected_mixed = {
        (str(record["path"]), str(record["function"]))
        for record in data.get("allowedMixedClockFunctions", [])
    }
    for path, function in sorted(actual_mixed - expected_mixed):
        findings.append(
            Finding(
                code="INV-MIXED-CLOCK-NEW",
                domain="timestamp",
                path=path,
                function=function,
                actual="NUMBER+timestamp",
                remediation="obtain protocol/security review of the cross-domain dependency",
            )
        )
    for path, function in sorted(expected_mixed - actual_mixed):
        findings.append(
            Finding(
                code="INV-MIXED-CLOCK-MISSING",
                domain="timestamp",
                path=path,
                function=function,
                expected="reviewed-NUMBER+timestamp",
                actual="missing",
            )
        )

    all_files = _iter_files(root, ["."])
    nonproduction = _nonproduction_counts(
        root, all_files, production_roots, excluded_production_globs
    )
    nonproduction_cadence = {
        classification: sum(
            1
            for candidate in cadence_actual
            if candidate.classification == classification
        )
        for classification in ("mock", "testing", "test")
    }
    findings.extend(_check_s5_legacy_inventory_fingerprint(data))
    findings.extend(_check_post_s5_production_inventory_fingerprint(data))
    success_lines = [
        (
            "CLOCK_INVENTORY_OK "
            f"schema={data['schemaVersion']} "
            f"production_occurrences={fixed_counts[0]} "
            f"production_lines={fixed_counts[1]} "
            f"production_files={fixed_counts[2]} "
            f"bn_ids={len(EXPECTED_BN_IDS)} "
            f"bn_records={len(data['directOccurrences'])} "
            f"indirect_ids={len(EXPECTED_CAD_IDS)} "
            f"cadence_candidates={len(cadence_actual)} "
            f"seconds_unit_candidates={len(seconds_actual)} "
            f"timestamp_ids={len(EXPECTED_TS_IDS)} "
            f"timestamp_occurrences={timestamp_counts[0]} "
            f"mixed_clock_functions={len(actual_mixed)} "
            f"vyper_paths={len(data['vyperPathClassifications'])} "
            "post_s5_production_records="
            f"{sum(record.get('classification') == 'production' for record in data['vyperPathClassifications'])} "
            "post_s5_production_sha256="
            f"{_post_s5_production_inventory_fingerprint(data)}"
        ),
        (
            "CLOCK_INVENTORY_NONPROD "
            + " ".join(
                (
                    f"{classification}="
                    f"{nonproduction[classification][0]}/"
                    f"{nonproduction[classification][1]}/"
                    f"{nonproduction[classification][2]}"
                )
                for classification in ("mock", "testing", "test")
            )
        ),
        (
            "CLOCK_INVENTORY_NONPROD_CADENCE "
            + " ".join(
                f"{classification}={nonproduction_cadence[classification]}"
                for classification in ("mock", "testing", "test")
            )
        ),
    ]
    return CheckResult(findings=findings, success_lines=success_lines)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the reviewed block-clock inventory"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="check the repository and exit nonzero on drift",
    )
    args = parser.parse_args(argv)
    if not args.check:
        parser.error("--check is required")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    _parse_args(sys.argv[1:] if argv is None else argv)
    repository_root = Path(__file__).resolve().parents[1]
    result = check_repository(repository_root)
    print(result.output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
