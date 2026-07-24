"""Deterministic dual-clock test infrastructure.

The public surface in this module is intentionally test-only.  It controls the
EVM ``NUMBER`` and timestamp patches independently, records every mutation and
observed call, and restores both Boa and controller state through anchors.

Later Track 6 slices should use :class:`ClockController` and the
``deployed_system`` fixture instead of selecting chain-specific contract source.
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from importlib.metadata import version
from typing import Any, Callable, Iterator, Mapping, Sequence

import boa
import pytest
import vyper
from vyper.compiler.output import build_abi_output


DEFAULT_NUMBER = 1_000_000
DEFAULT_TIMESTAMP = 2_000_000_000

PARAMETER_PROFILES = frozenset(
    {"base_current", "base_canonical", "robinhood_candidate"}
)

EVIDENCE_DOCUMENTED_BASE = "documented Base model"
EVIDENCE_DOCUMENTED_ROBINHOOD = "documented Robinhood/Arbitrum model"
EVIDENCE_EMPIRICAL = "dated empirical observation"
EVIDENCE_REPRESENTATIVE = "owner-approved representative assumption"
EVIDENCE_STRESS = "owner-approved conservative stress assumption"

PROFILE_EVIDENCE = {
    "B-ORD": EVIDENCE_DOCUMENTED_BASE,
    "R-REP128": EVIDENCE_EMPIRICAL,
    "R-PLUS1": EVIDENCE_DOCUMENTED_ROBINHOOD,
    "R-J2-J4": EVIDENCE_REPRESENTATIVE,
    "BOUNDARY-OPEN": EVIDENCE_DOCUMENTED_ROBINHOOD,
    "BOUNDARY-WINDOW": EVIDENCE_DOCUMENTED_ROBINHOOD,
    "R-STRESS60": EVIDENCE_STRESS,
    "MIXED": EVIDENCE_DOCUMENTED_ROBINHOOD,
}

_STATIC_PROFILE_NAMES = frozenset(
    {
        "B-ORD",
        "R-REP128",
        "R-PLUS1",
        "R-J2-J4",
        "R-STRESS60",
        "MIXED",
    }
)
_STABLE_ID_RE = re.compile(r"^(?:BN|CAD|TS)-\d{3}$")
_SENSITIVE_KEY_RE = re.compile(
    r"(?:secret|private.?key|mnemonic|password|credential|api.?key|access.?token)",
    re.IGNORECASE,
)
_UNSET = object()


class ClockHarnessError(AssertionError):
    """A deterministic, machine-searchable clock harness failure."""


class ArtifactMismatchError(ClockHarnessError):
    """Raised when two parameter labels use different compilation artifacts."""


@dataclass(frozen=True, order=True)
class ClockPoint:
    """One exact EVM-observed NUMBER/timestamp pair."""

    number: int
    timestamp: int

    def __post_init__(self) -> None:
        _require_nonnegative_int("number", self.number)
        _require_nonnegative_int("timestamp", self.timestamp)


@dataclass(frozen=True)
class ClockProfile:
    """A named, evidence-labelled sequence of controlled clock points."""

    name: str
    points: tuple[ClockPoint, ...]
    evidence: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("clock profile name must not be empty")
        if not self.points:
            raise ValueError(f"clock profile {self.name!r} must contain points")
        for before, after in zip(self.points, self.points[1:]):
            if after.number < before.number or after.timestamp < before.timestamp:
                raise ValueError(
                    f"clock profile {self.name!r} moves backwards: "
                    f"{_format_point(before)} -> {_format_point(after)}"
                )


@dataclass(frozen=True)
class ArtifactFingerprint:
    """Canonical compiler-input and unbound-creation artifact fingerprint."""

    digest: str
    source_sha256: str
    compiler_version: str
    compiler_settings: str
    abi_sha256: str
    creation_bytecode_sha256: str


@dataclass(frozen=True)
class ObservedCallOutcome:
    """Result metadata for an expected, caught revert."""

    success: bool
    normalized_reason: str


@dataclass(frozen=True)
class DeployedSystem:
    """Minimal S1 deployment boundary returned to later test slices."""

    deployment: Any
    clock_profile: ClockProfile
    parameter_profile: str
    parameter_values: Mapping[str, Any]
    parameter_bounds: Mapping[str, Any]
    artifact_id: str
    artifact_fingerprint: ArtifactFingerprint
    clock_controller: "ClockController"


def clock_profile(
    name: str,
    *,
    number: int = DEFAULT_NUMBER,
    timestamp: int = DEFAULT_TIMESTAMP,
    boundary: int | None = None,
    start: int | None = None,
    end: int | None = None,
) -> ClockProfile:
    """Build one approved exact profile.

    ``number`` and ``timestamp`` may be raised when an existing absolute value
    needs headroom.  Boundary profiles always derive their NUMBER values from
    caller-supplied scenario state.
    """

    _require_nonnegative_int("number", number)
    _require_nonnegative_int("timestamp", timestamp)
    if name not in PROFILE_EVIDENCE:
        raise ValueError(f"unknown clock profile: {name}")

    if name == "B-ORD":
        points = tuple(
            ClockPoint(number + index, timestamp + (index * 2))
            for index in range(5)
        )
    elif name == "R-REP128":
        points = tuple(
            ClockPoint(number, timestamp + (index // 4)) for index in range(128)
        )
    elif name == "R-PLUS1":
        points = (
            ClockPoint(number, timestamp),
            ClockPoint(number, timestamp + 1),
            ClockPoint(number + 1, timestamp + 12),
            ClockPoint(number + 1, timestamp + 13),
        )
    elif name == "R-J2-J4":
        points = (
            ClockPoint(number, timestamp),
            ClockPoint(number, timestamp + 1),
            ClockPoint(number + 2, timestamp + 24),
            ClockPoint(number + 2, timestamp + 25),
            ClockPoint(number + 4, timestamp + 48),
        )
    elif name == "BOUNDARY-OPEN":
        if boundary is None:
            raise ValueError("BOUNDARY-OPEN requires a scenario-derived boundary")
        _require_positive_int("boundary", boundary)
        points = (
            ClockPoint(boundary - 1, timestamp),
            ClockPoint(boundary + 1, timestamp + 24),
        )
    elif name == "BOUNDARY-WINDOW":
        if start is None or end is None:
            raise ValueError(
                "BOUNDARY-WINDOW requires scenario-derived start and end"
            )
        _validate_window(start, end)
        points = (
            ClockPoint(start - 1, timestamp),
            ClockPoint(end + 1, timestamp + 24),
        )
    elif name == "R-STRESS60":
        points = (
            ClockPoint(number, timestamp),
            ClockPoint(number, timestamp + 1),
            ClockPoint(number + 60, timestamp + 720),
        )
    else:
        assert name == "MIXED"
        points = (
            ClockPoint(number, timestamp),
            ClockPoint(number, timestamp + 3_600),
            ClockPoint(number + 2, timestamp + 3_600),
            ClockPoint(number + 2, timestamp + 7_200),
        )

    return ClockProfile(name, points, PROFILE_EVIDENCE[name])


def artifact_fingerprint(artifact: Any) -> ArtifactFingerprint:
    """Fingerprint source, compiler inputs, ABI, and unbound creation bytecode."""

    compiler_data = getattr(artifact, "compiler_data", None)
    if compiler_data is None:
        raise TypeError("artifact must expose Vyper compiler_data")

    source = compiler_data.source_code.encode("utf-8")
    abi = build_abi_output(compiler_data)
    settings = _canonical_json(
        {
            key: _jsonable(value)
            for key, value in vars(compiler_data.settings).items()
        }
    )
    compiler_version = (
        f"vyper=={vyper.__version__}+commit.{getattr(vyper, '__commit__', 'unknown')}"
    )
    abi_json = _canonical_json(abi).encode("utf-8")
    creation_bytecode = bytes(compiler_data.bytecode)

    components = {
        "source_sha256": _sha256(source),
        "compiler_version": compiler_version,
        "compiler_settings": settings,
        "abi_sha256": _sha256(abi_json),
        "creation_bytecode_sha256": _sha256(creation_bytecode),
    }
    digest = _sha256(_canonical_json(components).encode("utf-8"))
    return ArtifactFingerprint(digest=digest, **components)


def assert_identical_artifacts(
    expected: ArtifactFingerprint,
    actual: ArtifactFingerprint,
    *,
    artifact_id: str = "deployed-system",
    baseline_profile: str = "baseline",
    candidate_profile: str = "candidate",
) -> None:
    """Fail clearly if a parameter label selects different source/artifacts."""

    if expected == actual:
        return
    differing = [
        field
        for field in (
            "source_sha256",
            "compiler_version",
            "compiler_settings",
            "abi_sha256",
            "creation_bytecode_sha256",
            "digest",
        )
        if getattr(expected, field) != getattr(actual, field)
    ]
    raise ArtifactMismatchError(
        "CLOCK_FAIL id=ARTIFACT components=CM-059 "
        f"profile={candidate_profile}\n"
        "step=0 before=(0,0) after=(0,0)\n"
        f"params={candidate_profile} seed=none function=artifact_fingerprint "
        f"label={artifact_id}\n"
        f'expected="{expected.digest}" actual="{actual.digest}"\n'
        "prefix=[]\n"
        "ARTIFACT_MISMATCH "
        f"artifact_id={artifact_id} baseline_profile={baseline_profile} "
        f"candidate_profile={candidate_profile} "
        f"fields={','.join(differing)}"
    )


class ClockController:
    """Control Boa NUMBER/timestamp without mining and retain searchable traces."""

    def __init__(
        self,
        env: Any | None = None,
        *,
        parameter_profile: str = "base_current",
        parameter_values: Mapping[str, Any] | None = None,
        parameter_bounds: Mapping[str, Any] | None = None,
    ) -> None:
        self.env = env if env is not None else boa.env
        self._validate_parameter_profile(parameter_profile)
        self.parameter_profile = parameter_profile
        self.parameter_values = _public_mapping(parameter_values)
        self.parameter_bounds = _public_mapping(parameter_bounds)
        self.sequence_index = 0
        self._trace: list[dict[str, Any]] = []
        self._active_profile: ClockProfile | None = None
        self._intended = self._actual()
        self._scenario_initial = self._intended

    @property
    def trace(self) -> tuple[dict[str, Any], ...]:
        return tuple(copy.deepcopy(self._trace))

    @property
    def active_profile(self) -> ClockProfile | None:
        return self._active_profile

    @property
    def current(self) -> ClockPoint:
        return self._actual()

    def assert_scenario_start(self) -> None:
        """Assert the required clean controller state at scenario index zero."""

        actual = self._actual()
        if (
            self.sequence_index != 0
            or self._trace
            or self._active_profile is not None
            or actual != self._scenario_initial
            or self._intended != self._scenario_initial
        ):
            self._fail(
                expected=(
                    "initial clocks, sequence_index=0, empty trace, "
                    "no active profile"
                ),
                actual={
                    "clock": actual,
                    "sequence_index": self.sequence_index,
                    "trace_length": len(self._trace),
                    "profile": self._profile_name(),
                },
            )

    @contextlib.contextmanager
    def scenario(
        self,
        profile: ClockProfile | str | None = None,
        parameter_profile: str | None = None,
        *,
        parameter_values: Mapping[str, Any] | None = None,
        parameter_bounds: Mapping[str, Any] | None = None,
    ) -> Iterator["ClockController"]:
        """Run a clean scenario and restore Boa plus all controller state."""

        resolved_profile = (
            self._resolve_profile(profile) if profile is not None else None
        )
        selected_parameter_profile = (
            parameter_profile
            if parameter_profile is not None
            else self.parameter_profile
        )
        self._validate_parameter_profile(selected_parameter_profile)
        public_values = _public_mapping(
            self.parameter_values
            if parameter_values is None
            else parameter_values
        )
        public_bounds = _public_mapping(
            self.parameter_bounds
            if parameter_bounds is None
            else parameter_bounds
        )
        saved_state = self._snapshot_state()
        environment_before = self._actual()

        try:
            with self.env.anchor():
                self.sequence_index = 0
                self._trace = []
                self._active_profile = None
                self.parameter_profile = selected_parameter_profile
                self.parameter_values = public_values
                self.parameter_bounds = public_bounds
                self._intended = self._actual()
                self._scenario_initial = self._intended
                self.assert_scenario_start()
                if resolved_profile is not None:
                    self._validate_profile(resolved_profile)
                yield self
        finally:
            environment_after = self._actual()
            self._restore_state(saved_state)
            if environment_after != environment_before:
                raise ClockHarnessError(
                    "CLOCK_FAIL id=HARNESS components=CM-059 profile=UNBOUND\n"
                    f"step=0 before={_format_point(environment_before)} "
                    f"after={_format_point(environment_after)}\n"
                    "params=none seed=none function=boa.env.anchor label=restoration\n"
                    f'expected="{_format_point(environment_before)}" '
                    f'actual="{_format_point(environment_after)}"\n'
                    "prefix=[]"
                )

    def set(
        self,
        *,
        number: int | None = None,
        timestamp: int | None = None,
        _profile_step: int | None = None,
    ) -> ClockPoint:
        """Set either or both clocks directly; omitted values are held exactly."""

        if number is None and timestamp is None:
            raise ValueError("set requires number and/or timestamp")
        if number is not None:
            _require_nonnegative_int("number", number)
        if timestamp is not None:
            _require_nonnegative_int("timestamp", timestamp)

        before = self._actual()
        if before != self._intended:
            self._fail(
                expected={"controlled_clock": self._intended},
                actual={"controlled_clock": before},
                before=before,
                after=before,
            )

        target = ClockPoint(
            before.number if number is None else number,
            before.timestamp if timestamp is None else timestamp,
        )
        if target.number < before.number or target.timestamp < before.timestamp:
            self._fail(
                expected="nondecreasing NUMBER and timestamp",
                actual=f"backwards transition {_format_point(before)} -> "
                f"{_format_point(target)}",
                before=before,
                after=target,
            )

        intended_before = self._intended
        if number is not None:
            self.env.evm.patch.block_number = number
        if timestamp is not None:
            self.env.evm.patch.timestamp = timestamp
        after = self._actual()

        entry = {
            "kind": "mutation",
            "sequence_index": self.sequence_index,
            "profile": self._profile_name(),
            "profile_evidence": self._profile_evidence(),
            "step": (
                self.sequence_index if _profile_step is None else _profile_step
            ),
            "parameter_profile": self.parameter_profile,
            "intended_before": _point_dict(intended_before),
            "actual_before": _point_dict(before),
            "intended_after": _point_dict(target),
            "actual_after": _point_dict(after),
        }
        self._trace.append(entry)
        if after != target:
            self._fail(
                expected={"controlled_clock": target},
                actual={"controlled_clock": after},
                before=before,
                after=after,
            )

        self._intended = target
        self.sequence_index += 1
        return after

    def apply(self, profile: ClockProfile | str, step: int) -> ClockPoint:
        """Apply the exact next point from one approved profile."""

        resolved = self._resolve_profile(profile)
        self._validate_profile(resolved)
        _require_nonnegative_int("step", step)
        if step >= len(resolved.points):
            raise IndexError(
                f"profile {resolved.name} step {step} out of range "
                f"for {len(resolved.points)} points"
            )
        if step != self.sequence_index:
            self._fail(
                expected=f"next profile step {self.sequence_index}",
                actual=f"requested step {step}",
            )
        if self._active_profile is not None and self._active_profile != resolved:
            self._fail(
                expected=f"active profile {self._active_profile.name}",
                actual=f"profile switch to {resolved.name}",
            )

        self._active_profile = resolved
        expected = resolved.points[step]
        actual = self.set(
            number=expected.number,
            timestamp=expected.timestamp,
            _profile_step=step,
        )
        if actual != expected:
            self._fail(
                expected={"profile_point": expected},
                actual={"profile_point": actual},
                before=actual,
                after=actual,
            )
        return actual

    def hold_number(self, *, seconds: int) -> ClockPoint:
        """Advance timestamp by ``seconds`` while holding NUMBER exactly."""

        _require_nonnegative_int("seconds", seconds)
        before = self._actual()
        return self.set(
            number=before.number,
            timestamp=before.timestamp + seconds,
        )

    def hold_timestamp(self, *, numbers: int) -> ClockPoint:
        """Advance NUMBER by ``numbers`` while holding timestamp exactly."""

        _require_nonnegative_int("numbers", numbers)
        before = self._actual()
        return self.set(
            number=before.number + numbers,
            timestamp=before.timestamp,
        )

    def at_open(self, init_number: int, delay: int, offset: int = 0) -> int:
        """Return exact opening NUMBER plus a nonnegative diagnostic offset."""

        _require_nonnegative_int("init_number", init_number)
        _require_nonnegative_int("delay", delay)
        _require_nonnegative_int("offset", offset)
        return init_number + delay + offset

    def at_expiry(
        self, confirm_number: int, expiration: int, offset: int = 0
    ) -> int:
        """Return exact expiry NUMBER plus a nonnegative diagnostic offset."""

        _require_nonnegative_int("confirm_number", confirm_number)
        _require_positive_int("expiration", expiration)
        _require_nonnegative_int("offset", offset)
        return confirm_number + expiration + offset

    def at_interval(
        self, start_number: int, interval: int, offset: int = 0
    ) -> int:
        """Return the exact next interval boundary."""

        _require_nonnegative_int("start_number", start_number)
        _require_positive_int("interval", interval)
        _require_nonnegative_int("offset", offset)
        return start_number + interval + offset

    def at_window(
        self,
        start_number: int,
        end_number: int,
        boundary: str = "start",
        offset: int = 0,
    ) -> int:
        """Return one named point around the exact half-open window."""

        _validate_window(start_number, end_number)
        _require_nonnegative_int("offset", offset)
        points = self.boundary_points(start_number, end_number)
        aliases = {
            "exact_open": "start",
            "exact_end": "end",
            "before_start": "before_open",
            "after_start": "after_open",
        }
        canonical = aliases.get(boundary, boundary)
        if canonical not in points:
            allowed = ",".join(points)
            raise ValueError(
                f"invalid window boundary {boundary!r}; expected one of {allowed}"
            )
        return points[canonical] + offset

    def boundary_points(
        self, start_number: int, end_number: int
    ) -> dict[str, int]:
        """Construct every exact boundary required by later contract slices."""

        _validate_window(start_number, end_number)
        return {
            "before_open": start_number - 1,
            "start": start_number,
            "after_open": start_number + 1,
            "last_valid": end_number - 1,
            "end": end_number,
            "after_end": end_number + 1,
        }

    def skip_open(
        self, start_number: int, end_number: int
    ) -> tuple[int, int]:
        """Return the exact ``start-1 -> start+1`` transition."""

        points = self.boundary_points(start_number, end_number)
        return points["before_open"], points["after_open"]

    def skip_window(
        self, start_number: int, end_number: int
    ) -> tuple[int, int]:
        """Return the exact ``start-1 -> end+1`` transition."""

        points = self.boundary_points(start_number, end_number)
        return points["before_open"], points["after_end"]

    def observed_call(
        self,
        stable_id: str,
        label: str,
        callable: Callable[..., Any],
        *args: Any,
        components: Sequence[str] = (),
        seed: int | str | None = None,
        parameter_values: Mapping[str, Any] | None = None,
        parameter_bounds: Mapping[str, Any] | None = None,
        target_address: str | None = None,
        function_signature: str | None = None,
        observed_by: str | None = None,
        observation: Callable[[], Any] | None = None,
        expected_observation: Any = _UNSET,
        expected_result: Any = _UNSET,
        expected_revert: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Call a target and record proof that it observed the controlled clock.

        Successful calls require a state/event observation callback and expected
        value.  Expected reverts use the named ``observed_by`` boundary assertion
        as behavioral proof.  Environment state alone is never accepted.
        """

        if not _STABLE_ID_RE.fullmatch(stable_id):
            raise ValueError(f"invalid stable clock ID: {stable_id!r}")
        if not label:
            raise ValueError("observed call label must not be empty")
        component_ids = tuple(components)
        if any(not component.startswith("CM-") for component in component_ids):
            raise ValueError("component IDs must use CM-* stable identifiers")
        if not observed_by:
            raise ValueError(
                "observed_call requires a persisted field, event, "
                "or boundary assertion"
            )
        if expected_revert is None and (
            observation is None or expected_observation is _UNSET
        ):
            raise ValueError(
                "successful observed_call requires observation and "
                "expected_observation"
            )

        public_values = _public_mapping(
            self.parameter_values if parameter_values is None else parameter_values
        )
        public_bounds = _public_mapping(
            self.parameter_bounds if parameter_bounds is None else parameter_bounds
        )
        actual_before = self._actual()
        intended_before = self._intended
        if actual_before != intended_before:
            self._fail(
                stable_id=stable_id,
                components=component_ids,
                expected={"controlled_clock": intended_before},
                actual={"controlled_clock": actual_before},
                before=actual_before,
                after=actual_before,
                label=label,
                seed=seed,
            )

        inferred_address, inferred_signature = _target_metadata(callable)
        address = target_address or inferred_address
        signature = function_signature or inferred_signature
        expected_text = (
            f"revert:{expected_revert}"
            if expected_revert is not None
            else (
                _diagnostic_value(expected_result)
                if expected_result is not _UNSET
                else "success"
            )
        )

        try:
            result = callable(*args, **kwargs)
        except Exception as exc:
            reason = _normalize_reason(exc)
            actual_after = self._actual()
            entry = self._observation_entry(
                stable_id=stable_id,
                components=component_ids,
                label=label,
                seed=seed,
                intended_before=intended_before,
                actual_before=actual_before,
                actual_after=actual_after,
                public_values=public_values,
                public_bounds=public_bounds,
                success=False,
                reason=reason,
                address=address,
                signature=signature,
                expected=expected_text,
                actual=f"revert:{reason}",
                observed_by=observed_by,
                observed_value=reason,
            )
            self._trace.append(entry)
            if actual_after != actual_before:
                self._fail_from_entry(
                    entry,
                    expected=f"clock held at {_format_point(actual_before)}",
                    actual=f"clock advanced to {_format_point(actual_after)}",
                )
            if expected_revert is None or expected_revert not in reason:
                self._fail_from_entry(
                    entry,
                    expected=expected_text,
                    actual=f"revert:{reason}",
                    cause=exc,
                )
            return ObservedCallOutcome(False, reason)

        actual_after = self._actual()
        if actual_after != actual_before:
            entry = self._observation_entry(
                stable_id=stable_id,
                components=component_ids,
                label=label,
                seed=seed,
                intended_before=intended_before,
                actual_before=actual_before,
                actual_after=actual_after,
                public_values=public_values,
                public_bounds=public_bounds,
                success=True,
                reason="none",
                address=address,
                signature=signature,
                expected=f"clock held at {_format_point(actual_before)}",
                actual=f"clock advanced to {_format_point(actual_after)}",
                observed_by=observed_by,
                observed_value="not evaluated",
            )
            self._trace.append(entry)
            self._fail_from_entry(
                entry,
                expected=f"clock held at {_format_point(actual_before)}",
                actual=f"clock advanced to {_format_point(actual_after)}",
            )

        if expected_revert is not None:
            entry = self._observation_entry(
                stable_id=stable_id,
                components=component_ids,
                label=label,
                seed=seed,
                intended_before=intended_before,
                actual_before=actual_before,
                actual_after=actual_after,
                public_values=public_values,
                public_bounds=public_bounds,
                success=True,
                reason="none",
                address=address,
                signature=signature,
                expected=expected_text,
                actual="success",
                observed_by=observed_by,
                observed_value="unexpected success",
            )
            self._trace.append(entry)
            self._fail_from_entry(entry, expected=expected_text, actual="success")

        observed_value = observation()
        final_clock = self._actual()
        actual_text = (
            _diagnostic_value(result)
            if expected_result is not _UNSET
            else "success"
        )
        entry = self._observation_entry(
            stable_id=stable_id,
            components=component_ids,
            label=label,
            seed=seed,
            intended_before=intended_before,
            actual_before=actual_before,
            actual_after=final_clock,
            public_values=public_values,
            public_bounds=public_bounds,
            success=True,
            reason="none",
            address=address,
            signature=signature,
            expected=expected_text,
            actual=actual_text,
            observed_by=observed_by,
            observed_value=observed_value,
        )
        entry["observation"] = {
            "assertion": observed_by,
            "expected": _jsonable(expected_observation),
            "actual": _jsonable(observed_value),
        }
        self._trace.append(entry)

        if final_clock != actual_before:
            self._fail_from_entry(
                entry,
                expected=f"clock held at {_format_point(actual_before)}",
                actual=f"clock advanced to {_format_point(final_clock)}",
            )
        if observed_value != expected_observation:
            self._fail_from_entry(
                entry,
                expected={
                    "observation": observed_by,
                    "value": expected_observation,
                },
                actual={
                    "observation": observed_by,
                    "value": observed_value,
                },
            )
        if expected_result is not _UNSET and result != expected_result:
            self._fail_from_entry(
                entry,
                expected={"result": expected_result},
                actual={"result": result},
            )
        return result

    def format_failure(
        self,
        entry: Mapping[str, Any],
        *,
        expected: Any,
        actual: Any,
    ) -> str:
        """Render the stable CLOCK_FAIL prefix and required core fields."""

        before = _point_from_mapping(entry.get("actual_before"))
        after = _point_from_mapping(entry.get("actual_after"))
        components = ",".join(entry.get("components", ())) or "none"
        profile = entry.get("profile") or self._profile_name()
        step = entry.get("step", max(self.sequence_index - 1, 0))
        seed = entry.get("seed")
        seed_text = "none" if seed is None else _single_line(seed)
        signature = entry.get("function_signature", "unknown")
        label = entry.get("label", "unknown")
        parameter_profile = entry.get(
            "parameter_profile", self.parameter_profile
        )
        prefix = self._profile_prefix(step)
        return "\n".join(
            (
                f"CLOCK_FAIL id={entry.get('stable_id', 'HARNESS')} "
                f"components={components} profile={profile}",
                f"step={step} before={_format_point(before)} "
                f"after={_format_point(after)}",
                f"params={parameter_profile} seed={seed_text} "
                f"function={_single_line(signature)} "
                f"label={_single_line(label)}",
                f'expected="{_single_line(expected)}" '
                f'actual="{_single_line(actual)}"',
                f"values={_single_line(entry.get('parameter_values', {}))} "
                f"bounds={_single_line(entry.get('parameter_bounds', {}))} "
                f"observed_by={_single_line(entry.get('observed_by', 'none'))}",
                f"prefix={_single_line(prefix)}",
            )
        )

    def _observation_entry(self, **values: Any) -> dict[str, Any]:
        return {
            "kind": "observed_call",
            "stable_id": values["stable_id"],
            "components": list(values["components"]),
            "profile": self._profile_name(),
            "profile_evidence": self._profile_evidence(),
            "step": max(self.sequence_index - 1, 0),
            "seed": values["seed"],
            "parameter_profile": self.parameter_profile,
            "parameter_values": values["public_values"],
            "parameter_bounds": values["public_bounds"],
            "intended_pre": _point_dict(values["intended_before"]),
            "actual_before": _point_dict(values["actual_before"]),
            "actual_after": _point_dict(values["actual_after"]),
            "success": values["success"],
            "normalized_reason": values["reason"],
            "target_address": values["address"],
            "function_signature": values["signature"],
            "label": values["label"],
            "expected_result": values["expected"],
            "actual_result": values["actual"],
            "observed_by": values["observed_by"],
            "observed_value": _jsonable(values["observed_value"]),
        }

    def _resolve_profile(self, profile: ClockProfile | str) -> ClockProfile:
        if isinstance(profile, str):
            if profile not in _STATIC_PROFILE_NAMES:
                raise ValueError(
                    f"unknown or scenario-derived clock profile: {profile}"
                )
            return clock_profile(profile)
        if not isinstance(profile, ClockProfile):
            raise TypeError("profile must be a ClockProfile or approved name")
        return profile

    def _validate_profile(self, profile: ClockProfile) -> None:
        if profile.name not in PROFILE_EVIDENCE:
            raise ValueError(f"unknown clock profile: {profile.name}")
        if profile.evidence != PROFILE_EVIDENCE[profile.name]:
            raise ValueError(
                f"profile {profile.name} has invalid evidence label "
                f"{profile.evidence!r}"
            )
        if not _matches_approved_shape(profile):
            raise ValueError(
                f"profile {profile.name} does not match its approved exact shape"
            )

    def _validate_parameter_profile(self, parameter_profile: str) -> None:
        if parameter_profile not in PARAMETER_PROFILES:
            raise ValueError(
                f"unknown parameter profile {parameter_profile!r}; expected one "
                f"of {','.join(sorted(PARAMETER_PROFILES))}"
            )

    def _actual(self) -> ClockPoint:
        return ClockPoint(
            self.env.evm.patch.block_number,
            self.env.evm.patch.timestamp,
        )

    def _profile_name(self) -> str:
        return (
            self._active_profile.name
            if self._active_profile is not None
            else "UNBOUND"
        )

    def _profile_evidence(self) -> str:
        return (
            self._active_profile.evidence
            if self._active_profile is not None
            else "none"
        )

    def _profile_prefix(self, step: int) -> list[tuple[int, int]]:
        if self._active_profile is None:
            return []
        upper = min(max(step + 1, 0), len(self._active_profile.points))
        return [
            (point.number, point.timestamp)
            for point in self._active_profile.points[:upper]
        ]

    def _snapshot_state(self) -> dict[str, Any]:
        return {
            "sequence_index": self.sequence_index,
            "trace": copy.deepcopy(self._trace),
            "active_profile": self._active_profile,
            "intended": self._intended,
            "scenario_initial": self._scenario_initial,
            "parameter_profile": self.parameter_profile,
            "parameter_values": copy.deepcopy(self.parameter_values),
            "parameter_bounds": copy.deepcopy(self.parameter_bounds),
        }

    def _restore_state(self, state: Mapping[str, Any]) -> None:
        self.sequence_index = state["sequence_index"]
        self._trace = state["trace"]
        self._active_profile = state["active_profile"]
        self._intended = state["intended"]
        self._scenario_initial = state["scenario_initial"]
        self.parameter_profile = state["parameter_profile"]
        self.parameter_values = state["parameter_values"]
        self.parameter_bounds = state["parameter_bounds"]

    def _fail_from_entry(
        self,
        entry: Mapping[str, Any],
        *,
        expected: Any,
        actual: Any,
        cause: Exception | None = None,
    ) -> None:
        error = ClockHarnessError(
            self.format_failure(entry, expected=expected, actual=actual)
        )
        if cause is not None:
            raise error from cause
        raise error

    def _fail(
        self,
        *,
        expected: Any,
        actual: Any,
        stable_id: str = "HARNESS",
        components: Sequence[str] = ("CM-059",),
        before: ClockPoint | None = None,
        after: ClockPoint | None = None,
        label: str = "clock_controller",
        seed: int | str | None = None,
    ) -> None:
        before_point = before or self._actual()
        after_point = after or self._actual()
        entry = {
            "stable_id": stable_id,
            "components": list(components),
            "profile": self._profile_name(),
            "step": max(self.sequence_index - 1, 0),
            "seed": seed,
            "parameter_profile": self.parameter_profile,
            "actual_before": _point_dict(before_point),
            "actual_after": _point_dict(after_point),
            "function_signature": "clock_controller",
            "label": label,
        }
        self._fail_from_entry(entry, expected=expected, actual=actual)


class DeployedSystemBoundary:
    """Callable fixture boundary for isolated, identical-artifact deployments."""

    def __init__(self, controller: ClockController) -> None:
        self.controller = controller
        self._artifact_baselines: dict[
            str, tuple[str, ArtifactFingerprint]
        ] = {}

    def __call__(
        self,
        clock_profile: ClockProfile | str,
        parameter_profile: str,
        deployment_factory: Callable[[], Any],
        *,
        artifact: Any | None = None,
        artifact_id: str = "deployed-system",
        parameter_values: Mapping[str, Any] | None = None,
        parameter_bounds: Mapping[str, Any] | None = None,
    ) -> contextlib.AbstractContextManager[DeployedSystem]:
        """Open one isolated deployment scenario."""

        if not callable(deployment_factory):
            raise TypeError("deployment_factory must be callable")
        if not artifact_id:
            raise ValueError("artifact_id must not be empty")
        resolved = self.controller._resolve_profile(clock_profile)
        self.controller._validate_profile(resolved)
        self.controller._validate_parameter_profile(parameter_profile)
        public_values = _public_mapping(parameter_values)
        public_bounds = _public_mapping(parameter_bounds)
        return self._open(
            resolved,
            parameter_profile,
            deployment_factory,
            artifact=artifact,
            artifact_id=artifact_id,
            parameter_values=public_values,
            parameter_bounds=public_bounds,
        )

    @contextlib.contextmanager
    def _open(
        self,
        selected_clock_profile: ClockProfile | str,
        parameter_profile: str,
        deployment_factory: Callable[[], Any],
        *,
        artifact: Any | None,
        artifact_id: str,
        parameter_values: Mapping[str, Any] | None,
        parameter_bounds: Mapping[str, Any] | None,
    ) -> Iterator[DeployedSystem]:
        if not callable(deployment_factory):
            raise TypeError("deployment_factory must be callable")
        if not artifact_id:
            raise ValueError("artifact_id must not be empty")

        resolved = self.controller._resolve_profile(selected_clock_profile)
        self.controller._validate_profile(resolved)
        self.controller._validate_parameter_profile(parameter_profile)
        public_values = _public_mapping(parameter_values)
        public_bounds = _public_mapping(parameter_bounds)

        with self.controller.scenario(
            resolved,
            parameter_profile,
            parameter_values=public_values,
            parameter_bounds=public_bounds,
        ):
            self.controller.apply(resolved, 0)
            clock_before_deploy = self.controller.current
            deployment = deployment_factory()
            clock_after_deploy = self.controller.current
            if clock_after_deploy != clock_before_deploy:
                self.controller._fail(
                    expected=(
                        "deployment does not implicitly advance controlled clocks"
                    ),
                    actual=(
                        f"{_format_point(clock_before_deploy)} -> "
                        f"{_format_point(clock_after_deploy)}"
                    ),
                    before=clock_before_deploy,
                    after=clock_after_deploy,
                    label="deployed_system",
                )

            deployment_fingerprint = artifact_fingerprint(deployment)
            if artifact is not None:
                declared_fingerprint = artifact_fingerprint(artifact)
                assert_identical_artifacts(
                    declared_fingerprint,
                    deployment_fingerprint,
                    artifact_id=artifact_id,
                    baseline_profile=f"{parameter_profile}:declared",
                    candidate_profile=f"{parameter_profile}:deployed",
                )
            fingerprint = deployment_fingerprint
            if artifact_id in self._artifact_baselines:
                baseline_profile, baseline = self._artifact_baselines[artifact_id]
                assert_identical_artifacts(
                    baseline,
                    fingerprint,
                    artifact_id=artifact_id,
                    baseline_profile=baseline_profile,
                    candidate_profile=parameter_profile,
                )

            yield DeployedSystem(
                deployment=deployment,
                clock_profile=resolved,
                parameter_profile=parameter_profile,
                parameter_values=public_values,
                parameter_bounds=public_bounds,
                artifact_id=artifact_id,
                artifact_fingerprint=fingerprint,
                clock_controller=self.controller,
            )
            if artifact_id not in self._artifact_baselines:
                self._artifact_baselines[artifact_id] = (
                    parameter_profile,
                    fingerprint,
                )


@pytest.fixture
def clock_controller() -> Iterator[ClockController]:
    """Fresh controller fixture with explicit Boa and internal-state isolation."""

    controller = ClockController()
    with controller.scenario():
        controller.assert_scenario_start()
        yield controller


@pytest.fixture
def deployed_system(
    clock_controller: ClockController,
) -> DeployedSystemBoundary:
    """Expose the minimal S1 identical-artifact deployment boundary."""

    return DeployedSystemBoundary(clock_controller)


def installed_runtime_versions() -> dict[str, str]:
    """Return the exact dependency versions protected by the fail-closed gate."""

    return {
        "titanoboa": version("titanoboa"),
        "pytest": version("pytest"),
    }


def _matches_approved_shape(profile: ClockProfile) -> bool:
    points = profile.points
    first = points[0]
    try:
        if profile.name in _STATIC_PROFILE_NAMES:
            expected = clock_profile(
                profile.name,
                number=first.number,
                timestamp=first.timestamp,
            )
            return points == expected.points
        if profile.name == "BOUNDARY-OPEN":
            if len(points) != 2:
                return False
            boundary = first.number + 1
            expected = clock_profile(
                profile.name,
                timestamp=first.timestamp,
                boundary=boundary,
            )
            return points == expected.points
        if profile.name == "BOUNDARY-WINDOW":
            if len(points) != 2:
                return False
            start = first.number + 1
            end = points[1].number - 1
            expected = clock_profile(
                profile.name,
                timestamp=first.timestamp,
                start=start,
                end=end,
            )
            return points == expected.points
    except ValueError:
        return False
    return False


def _target_metadata(target: Callable[..., Any]) -> tuple[str, str]:
    contract = getattr(target, "contract", None)
    address = str(getattr(contract, "address", "unknown"))
    function_type = getattr(target, "func_t", None)
    signature = str(function_type) if function_type is not None else ""
    signature = signature.removeprefix("contract function ").strip()
    match = re.search(r"(?:def\s+)?([A-Za-z_]\w*\([^)]*\))", signature)
    if match is not None:
        signature = match.group(1)
    if not signature:
        signature = getattr(target, "__qualname__", None) or getattr(
            target, "__name__", "unknown"
        )
    return address, signature


def _normalize_reason(exc: Exception) -> str:
    text = str(exc).replace("\x1b", "")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[E]") and stripped.endswith(">"):
            start = stripped.rfind("<")
            if start >= 0:
                return _single_line(stripped[start + 1 : -1])
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and set(stripped) != {"="}:
            return _single_line(stripped)
    return type(exc).__name__


def _validate_window(start: int, end: int) -> None:
    _require_positive_int("start", start)
    _require_nonnegative_int("end", end)
    if end <= start:
        raise ValueError(
            f"impossible window: end ({end}) must be greater than start ({start})"
        )


def _require_nonnegative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


def _require_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _public_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError("diagnostic values and bounds must be mappings")
    result: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError("diagnostic mapping keys must be strings")
        if _SENSITIVE_KEY_RE.search(key):
            raise ValueError(
                f"sensitive diagnostic key rejected: {key!r}"
            )
        result[key] = _jsonable(item)
    return result


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, ClockPoint):
        return _point_dict(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return f"0x{value.hex()}"
    if isinstance(value, Mapping):
        normalized = {}
        for key, item in value.items():
            key_text = str(key)
            if _SENSITIVE_KEY_RE.search(key_text):
                raise ValueError(
                    f"sensitive diagnostic key rejected: {key_text!r}"
                )
            normalized[key_text] = _jsonable(item)
        return normalized
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    raise TypeError(
        f"diagnostic/artifact value {type(value).__name__} is not deterministic"
    )


def _point_dict(point: ClockPoint) -> dict[str, int]:
    return {"number": point.number, "timestamp": point.timestamp}


def _point_from_mapping(value: Any) -> ClockPoint:
    if isinstance(value, ClockPoint):
        return value
    if isinstance(value, Mapping):
        return ClockPoint(value["number"], value["timestamp"])
    return ClockPoint(0, 0)


def _format_point(point: ClockPoint) -> str:
    return f"({point.number},{point.timestamp})"


def _diagnostic_value(value: Any) -> str:
    return _canonical_json(_jsonable(value))


def _single_line(value: Any) -> str:
    text = str(value).replace("\n", "\\n").replace("\r", "\\r")
    return text.replace('"', "'")


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


CLOCK_PROFILES = {
    name: clock_profile(name) for name in sorted(_STATIC_PROFILE_NAMES)
}
