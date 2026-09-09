from __future__ import annotations

import contextlib
from importlib.metadata import version
from types import SimpleNamespace

import boa
import pytest

from utils.clock_profiles import (
    CLOCK_PROFILES,
    DEFAULT_NUMBER,
    DEFAULT_TIMESTAMP,
    EVIDENCE_DOCUMENTED_BASE,
    EVIDENCE_DOCUMENTED_ROBINHOOD,
    EVIDENCE_EMPIRICAL,
    EVIDENCE_REPRESENTATIVE,
    EVIDENCE_STRESS,
    PARAMETER_PROFILES,
    PROFILE_EVIDENCE_DETAILS,
    ArtifactMismatchError,
    ClockController,
    ClockHarnessError,
    ClockPoint,
    ClockProfile,
    ObservedCallOutcome,
    artifact_fingerprint,
    assert_identical_artifacts,
    clock_profile,
    installed_runtime_versions,
)


N = DEFAULT_NUMBER
T = DEFAULT_TIMESTAMP


class _NonRestoringEnv:
    """Small test double for the scenario restoration double-fault path."""

    def __init__(self):
        self.evm = SimpleNamespace(
            patch=SimpleNamespace(block_number=100, timestamp=200)
        )

    @contextlib.contextmanager
    def anchor(self):
        yield


CLOCK_OBSERVER_SOURCE = """
#pragma version 0.4.3

event ClockObserved:
    number: uint256
    timestamp: uint256

seen_number: public(uint256)
seen_timestamp: public(uint256)
call_count: public(uint256)

@external
def observe():
    self.seen_number = block.number
    self.seen_timestamp = block.timestamp
    self.call_count += 1
    log ClockObserved(number=block.number, timestamp=block.timestamp)

@external
def fail_at(_number: uint256):
    assert block.number != _number, "clock boundary"
"""

DIFFERENT_OBSERVER_SOURCE = """
#pragma version 0.4.3

seen_number: public(uint256)

@external
def observe():
    self.seen_number = block.number
"""


@pytest.fixture(scope="module", autouse=True)
def pinned_runtime_gate():
    """Every S1 test fails closed when either reviewed runtime pin drifts."""

    versions = installed_runtime_versions()
    assert versions == {"titanoboa": "0.2.7", "pytest": "8.4.2"}


@pytest.fixture(scope="module")
def observer_deployer():
    return boa.loads_partial(CLOCK_OBSERVER_SOURCE, name="ClockObserver")


@pytest.fixture(scope="module")
def different_observer_deployer():
    return boa.loads_partial(
        DIFFERENT_OBSERVER_SOURCE, name="DifferentClockObserver"
    )


def _pairs(profile: ClockProfile) -> tuple[tuple[int, int], ...]:
    return tuple((point.number, point.timestamp) for point in profile.points)


def test_00_installed_versions_and_direct_runtime_primitive_gate():
    assert version("titanoboa") == "0.2.7"
    assert version("pytest") == "8.4.2"

    baseline = ClockPoint(
        boa.env.evm.patch.block_number,
        boa.env.evm.patch.timestamp,
    )
    with boa.env.anchor():
        boa.env.evm.patch.block_number = baseline.number + 2
        assert boa.env.evm.patch.block_number == baseline.number + 2
        assert boa.env.evm.patch.timestamp == baseline.timestamp

        boa.env.evm.patch.timestamp = baseline.timestamp + 4
        assert boa.env.evm.patch.block_number == baseline.number + 2
        assert boa.env.evm.patch.timestamp == baseline.timestamp + 4

        boa.env.evm.patch.block_number = baseline.number + 60
        assert boa.env.evm.patch.block_number == baseline.number + 60
        assert boa.env.evm.patch.timestamp == baseline.timestamp + 4

    assert boa.env.evm.patch.block_number == baseline.number
    assert boa.env.evm.patch.timestamp == baseline.timestamp


def test_01_repeated_calls_hold_number_and_do_not_implicitly_mine(
    observer_deployer,
):
    baseline = ClockPoint(
        boa.env.evm.patch.block_number,
        boa.env.evm.patch.timestamp,
    )
    with boa.env.anchor():
        boa.env.evm.patch.block_number = baseline.number + 4
        boa.env.evm.patch.timestamp = baseline.timestamp + 10
        observer = observer_deployer.deploy()
        deployed_at = ClockPoint(
            boa.env.evm.patch.block_number,
            boa.env.evm.patch.timestamp,
        )

        observer.observe()
        after_first = ClockPoint(
            boa.env.evm.patch.block_number,
            boa.env.evm.patch.timestamp,
        )
        assert after_first == deployed_at
        assert observer.seen_number() == deployed_at.number
        assert observer.seen_timestamp() == deployed_at.timestamp

        boa.env.evm.patch.timestamp = deployed_at.timestamp + 11
        observer.observe()
        after_second = ClockPoint(
            boa.env.evm.patch.block_number,
            boa.env.evm.patch.timestamp,
        )
        assert after_second == ClockPoint(
            deployed_at.number, deployed_at.timestamp + 11
        )
        assert observer.seen_number() == deployed_at.number
        assert observer.seen_timestamp() == deployed_at.timestamp + 11
        assert observer.call_count() == 2

    assert boa.env.evm.patch.block_number == baseline.number
    assert boa.env.evm.patch.timestamp == baseline.timestamp


@pytest.mark.parametrize(
    ("name", "expected", "evidence"),
    [
        (
            "B-ORD",
            ((N, T), (N + 1, T + 2), (N + 2, T + 4), (N + 3, T + 6), (N + 4, T + 8)),
            EVIDENCE_DOCUMENTED_BASE,
        ),
        (
            "R-PLUS1",
            ((N, T), (N, T + 1), (N + 1, T + 12), (N + 1, T + 13)),
            EVIDENCE_DOCUMENTED_ROBINHOOD,
        ),
        (
            "R-J2-J4",
            ((N, T), (N, T + 1), (N + 2, T + 24), (N + 2, T + 25), (N + 4, T + 48)),
            EVIDENCE_REPRESENTATIVE,
        ),
        (
            "R-STRESS60",
            ((N, T), (N, T + 1), (N + 60, T + 720)),
            EVIDENCE_STRESS,
        ),
        (
            "MIXED",
            ((N, T), (N, T + 3_600), (N + 2, T + 3_600), (N + 2, T + 7_200)),
            EVIDENCE_DOCUMENTED_ROBINHOOD,
        ),
    ],
)
def test_every_static_profile_has_the_exact_points_and_evidence(
    name, expected, evidence
):
    profile = clock_profile(name)
    assert _pairs(profile) == expected
    assert profile.evidence == evidence
    assert profile.evidence_detail == PROFILE_EVIDENCE_DETAILS[name]
    assert CLOCK_PROFILES[name] == profile


def test_r_rep128_retains_all_128_exact_points():
    profile = clock_profile("R-REP128")
    assert len(profile.points) == 128
    assert profile.evidence == EVIDENCE_EMPIRICAL
    assert "2026-07-23T21:36:01Z" in profile.evidence_detail
    assert "88-block repeat" in profile.evidence_detail
    assert _pairs(profile) == tuple((N, T + (index // 4)) for index in range(128))
    assert len({point.number for point in profile.points}) == 1


def test_unknown_profile_evidence_detail_fails_clearly():
    profile = ClockProfile(
        "CUSTOM",
        (ClockPoint(N, T),),
        "custom evidence category",
    )
    with pytest.raises(
        ValueError,
        match=r"unknown clock profile 'CUSTOM'; no evidence detail is registered",
    ):
        _ = profile.evidence_detail


def test_boundary_profiles_are_derived_from_scenario_state():
    opening = 4_000
    start = 9_000
    end = 9_061
    open_profile = clock_profile("BOUNDARY-OPEN", boundary=opening)
    window_profile = clock_profile(
        "BOUNDARY-WINDOW", start=start, end=end
    )

    assert _pairs(open_profile) == (
        (opening - 1, T),
        (opening + 1, T + 24),
    )
    assert _pairs(window_profile) == (
        (start - 1, T),
        (end + 1, T + 24),
    )
    assert open_profile.evidence == EVIDENCE_DOCUMENTED_ROBINHOOD
    assert window_profile.evidence == EVIDENCE_DOCUMENTED_ROBINHOOD
    assert "synthetic" in open_profile.evidence_detail
    assert "synthetic" in window_profile.evidence_detail


def test_synthetic_mixed_profile_evidence_does_not_claim_observation():
    profile = clock_profile("MIXED")
    assert profile.evidence == EVIDENCE_DOCUMENTED_ROBINHOOD
    assert "synthetic independent-clock scenario" in profile.evidence_detail
    assert "empirical" not in profile.evidence_detail


@pytest.mark.parametrize(
    "profile",
    [
        clock_profile("B-ORD"),
        clock_profile("R-REP128"),
        clock_profile("R-PLUS1"),
        clock_profile("R-J2-J4"),
        clock_profile("BOUNDARY-OPEN", boundary=N + 20),
        clock_profile(
            "BOUNDARY-WINDOW", start=N + 20, end=N + 100
        ),
        clock_profile("R-STRESS60"),
        clock_profile("MIXED"),
    ],
    ids=lambda profile: profile.name,
)
def test_apply_reaches_every_exact_profile_point(clock_controller, profile):
    for step, expected in enumerate(profile.points):
        assert clock_controller.apply(profile, step) == expected

    assert clock_controller.sequence_index == len(profile.points)
    assert clock_controller.profile_step_index == len(profile.points)
    assert len(clock_controller.trace) == len(profile.points)
    assert all(entry["kind"] == "mutation" for entry in clock_controller.trace)
    assert clock_controller.trace[-1]["actual_after"] == {
        "number": profile.points[-1].number,
        "timestamp": profile.points[-1].timestamp,
    }


def test_profile_progress_is_independent_of_global_mutation_sequence(
    clock_controller,
):
    profile = clock_profile("B-ORD")

    clock_controller.set(number=N, timestamp=T)
    assert clock_controller.sequence_index == 1
    assert clock_controller.profile_step_index == 0

    assert clock_controller.apply(profile, 0) == profile.points[0]
    clock_controller.hold_number(seconds=0)
    assert clock_controller.sequence_index == 3
    assert clock_controller.profile_step_index == 1

    with pytest.raises(ClockHarnessError) as raised:
        clock_controller.apply(profile, 2)
    assert 'expected="next profile step 1"' in str(raised.value)
    assert 'actual="requested step 2"' in str(raised.value)

    assert clock_controller.apply(profile, 1) == profile.points[1]
    assert clock_controller.sequence_index == 4
    assert clock_controller.profile_step_index == 2
    assert [entry["profile_step"] for entry in clock_controller.trace] == [
        None,
        0,
        None,
        1,
    ]


def test_controller_moves_number_and_timestamp_independently(clock_controller):
    clock_controller.set(number=N, timestamp=T)
    assert clock_controller.hold_number(seconds=3_600) == ClockPoint(
        N, T + 3_600
    )
    assert clock_controller.hold_timestamp(numbers=2) == ClockPoint(
        N + 2, T + 3_600
    )

    trace = clock_controller.trace
    assert trace[1]["actual_before"] == {"number": N, "timestamp": T}
    assert trace[1]["actual_after"] == {
        "number": N,
        "timestamp": T + 3_600,
    }
    assert trace[2]["actual_after"] == {
        "number": N + 2,
        "timestamp": T + 3_600,
    }


@pytest.mark.parametrize(
    ("number", "timestamp"),
    [(N - 1, T), (N, T - 1), (N - 1, T - 1)],
)
def test_controller_rejects_backwards_movement(
    clock_controller, number, timestamp
):
    clock_controller.set(number=N, timestamp=T)
    with pytest.raises(ClockHarnessError, match=r"^CLOCK_FAIL id=HARNESS"):
        clock_controller.set(number=number, timestamp=timestamp)


def test_unknown_profile_invalid_step_and_tampered_profile_fail_clearly(
    clock_controller,
):
    with pytest.raises(ValueError, match="unknown"):
        clock_controller.apply("NOT-A-PROFILE", 0)

    profile = clock_profile("B-ORD")
    with pytest.raises(IndexError, match="out of range"):
        clock_controller.apply(profile, len(profile.points))

    tampered = ClockProfile(
        "B-ORD",
        (ClockPoint(N, T), ClockPoint(N + 2, T + 2)),
        EVIDENCE_DOCUMENTED_BASE,
    )
    with pytest.raises(ValueError, match="approved exact shape"):
        clock_controller.apply(tampered, 0)


def test_invalid_parameter_profile_fails_before_deployment(
    deployed_system, observer_deployer
):
    with pytest.raises(ValueError, match="unknown parameter profile"):
        deployed_system(
            "B-ORD",
            "unknown_chain",
            observer_deployer.deploy,
            artifact=observer_deployer,
        )


def test_boundary_helpers_construct_all_exact_points_and_skip_transitions(
    clock_controller,
):
    start = 1_200
    end = 1_260
    assert clock_controller.at_open(1_000, 200) == start
    assert clock_controller.at_expiry(start, 60) == end
    assert clock_controller.at_interval(1_000, 200) == start
    assert clock_controller.boundary_points(start, end) == {
        "before_open": start - 1,
        "start": start,
        "after_open": start + 1,
        "last_valid": end - 1,
        "end": end,
        "after_end": end + 1,
    }
    assert clock_controller.at_window(start, end, "before_open") == start - 1
    assert clock_controller.at_window(start, end, "exact_open") == start
    assert clock_controller.at_window(start, end, "after_open") == start + 1
    assert clock_controller.at_window(start, end, "last_valid") == end - 1
    assert clock_controller.at_window(start, end, "exact_end") == end
    assert clock_controller.at_window(start, end, "after_end") == end + 1
    assert clock_controller.skip_open(start, end) == (start - 1, start + 1)
    assert clock_controller.skip_window(start, end) == (start - 1, end + 1)


@pytest.mark.parametrize(
    "call",
    [
        lambda controller: controller.at_open(10, 2, -1),
        lambda controller: controller.at_expiry(10, 2, -1),
        lambda controller: controller.at_interval(10, 0),
        lambda controller: controller.at_window(10, 10),
        lambda controller: controller.at_window(10, 20, "unknown"),
    ],
)
def test_invalid_offsets_intervals_windows_and_boundaries_fail(
    clock_controller, call
):
    with pytest.raises(ValueError):
        call(clock_controller)


def test_mutation_trace_records_intended_and_actual_clocks(clock_controller):
    clock_controller.set(number=N, timestamp=T)
    entry = clock_controller.trace[0]
    assert set(entry) == {
        "kind",
        "sequence_index",
        "profile",
        "profile_evidence",
        "profile_evidence_detail",
        "profile_step",
        "step",
        "parameter_profile",
        "intended_before",
        "actual_before",
        "intended_after",
        "actual_after",
    }
    assert entry["intended_after"] == entry["actual_after"] == {
        "number": N,
        "timestamp": T,
    }
    assert entry["profile_step"] is None


def test_clock_points_do_not_expose_misleading_lexicographic_ordering():
    with pytest.raises(TypeError):
        ClockPoint(5, 10) < ClockPoint(6, 3)


def test_observed_call_success_trace_proves_persisted_clock_context(
    clock_controller, observer_deployer
):
    profile = clock_profile("R-J2-J4")
    clock_controller.apply(profile, 0)
    observer = observer_deployer.deploy()

    result = clock_controller.observed_call(
        "BN-026",
        "persist controlled clock",
        observer.observe,
        components=("CM-033", "CM-059"),
        seed=7,
        parameter_values={"underscore_interval": 7_200},
        parameter_bounds={"underscore_interval": [7_200, 50_400]},
        observed_by="state:seen_number,seen_timestamp",
        observation=lambda: (
            observer.seen_number(),
            observer.seen_timestamp(),
        ),
        expected_observation=(N, T),
        expected_result=None,
    )
    assert result is None

    entry = clock_controller.trace[-1]
    required = {
        "stable_id",
        "components",
        "profile",
        "profile_evidence_detail",
        "step",
        "seed",
        "intended_pre",
        "actual_before",
        "actual_after",
        "parameter_profile",
        "parameter_values",
        "parameter_bounds",
        "success",
        "normalized_reason",
        "target_address",
        "function_signature",
        "label",
        "observation",
    }
    assert required <= set(entry)
    assert entry["stable_id"] == "BN-026"
    assert entry["components"] == ["CM-033", "CM-059"]
    assert entry["profile"] == "R-J2-J4"
    assert entry["profile_evidence_detail"] == profile.evidence_detail
    assert entry["step"] == 0
    assert entry["seed"] == 7
    assert entry["intended_pre"] == entry["actual_before"]
    assert entry["actual_after"] == entry["actual_before"]
    assert entry["success"] is True
    assert entry["normalized_reason"] == "none"
    assert entry["target_address"] == str(observer.address)
    assert entry["function_signature"] == "observe()"
    assert entry["observation"] == {
        "assertion": "state:seen_number,seen_timestamp",
        "expected": [N, T],
        "actual": [N, T],
    }


def test_observed_call_expected_revert_trace_uses_boundary_assertion(
    clock_controller, observer_deployer
):
    profile = clock_profile("R-PLUS1")
    clock_controller.apply(profile, 0)
    observer = observer_deployer.deploy()

    outcome = clock_controller.observed_call(
        "BN-004",
        "exact boundary rejects",
        observer.fail_at,
        N,
        components=("CM-059",),
        parameter_values={"confirm_number": N},
        parameter_bounds={"expiration": [61, 50_400]},
        observed_by="boundary:block.number equals rejected boundary",
        expected_revert="clock boundary",
    )
    assert outcome == ObservedCallOutcome(False, "clock boundary")

    entry = clock_controller.trace[-1]
    assert entry["success"] is False
    assert entry["normalized_reason"] == "clock boundary"
    assert entry["actual_before"] == entry["actual_after"]
    assert entry["observed_by"].startswith("boundary:")


def test_observed_call_rejects_environment_only_claims(
    clock_controller, observer_deployer
):
    profile = clock_profile("B-ORD")
    clock_controller.apply(profile, 0)
    observer = observer_deployer.deploy()
    with pytest.raises(ValueError, match="state:, event:, or boundary:"):
        clock_controller.observed_call(
            "BN-001",
            "environment-only assertion",
            observer.observe,
            components=("CM-001",),
        )


@pytest.mark.parametrize(
    "observed_by",
    [
        "untyped proof",
        "state:",
        "state: ",
        "event:\t",
        "STATE:seen_number",
        "state:field\nextra",
        7,
    ],
)
def test_observed_call_rejects_invalid_observation_labels(
    clock_controller, observed_by
):
    with pytest.raises(ValueError, match="state:, event:, or boundary:"):
        clock_controller.observed_call(
            "BN-001",
            "invalid observation label",
            lambda: None,
            observed_by=observed_by,
        )


def test_expected_revert_matches_the_full_normalized_reason(
    clock_controller, observer_deployer
):
    profile = clock_profile("R-PLUS1")
    clock_controller.apply(profile, 0)
    observer = observer_deployer.deploy()

    with pytest.raises(ClockHarnessError) as raised:
        clock_controller.observed_call(
            "BN-004",
            "partial revert reason must not match",
            observer.fail_at,
            N,
            components=("CM-059",),
            observed_by="boundary:block.number equals rejected boundary",
            expected_revert="boundary",
        )

    message = str(raised.value)
    assert 'expected="revert:boundary"' in message
    assert 'actual="revert:clock boundary"' in message


def test_observed_call_failure_diagnostic_is_searchable_and_deterministic(
    clock_controller, observer_deployer
):
    profile = clock_profile("R-REP128")
    clock_controller.apply(profile, 0)
    observer = observer_deployer.deploy()

    with pytest.raises(ClockHarnessError) as raised:
        clock_controller.observed_call(
            "BN-012",
            "independent call blocked",
            observer.observe,
            components=("CM-044", "CM-014"),
            seed=123,
            parameter_values={"cooldown": 1_200},
            parameter_bounds={"cooldown": [0, 1_200]},
            observed_by="state:seen_number",
            observation=observer.seen_number,
            expected_observation=N + 1,
        )

    diagnostic = str(raised.value)
    assert diagnostic.startswith(
        "CLOCK_FAIL id=BN-012 components=CM-044,CM-014 profile=R-REP128"
    )
    assert "step=0 before=(1000000,2000000000)" in diagnostic
    assert "params=base_current seed=123 function=observe()" in diagnostic
    assert "label=independent call blocked" in diagnostic
    assert "expected=" in diagnostic
    assert "actual=" in diagnostic
    assert "prefix=[(1000000, 2000000000)]" in diagnostic

    entry = clock_controller.trace[-1]
    assert (
        clock_controller.format_failure(
            entry,
            expected={"observation": "state:seen_number", "value": N + 1},
            actual={"observation": "state:seen_number", "value": N},
        )
        == diagnostic
    )


def test_diagnostics_reject_secret_shaped_parameter_keys(
    clock_controller, observer_deployer
):
    profile = clock_profile("B-ORD")
    clock_controller.apply(profile, 0)
    observer = observer_deployer.deploy()
    with pytest.raises(ValueError, match="sensitive diagnostic key"):
        clock_controller.observed_call(
            "BN-001",
            "secret rejection",
            observer.observe,
            components=("CM-001",),
            parameter_values={"private_key": "must-not-appear"},
            observed_by="state:seen_number",
            observation=observer.seen_number,
            expected_observation=N,
        )


def test_nested_scenario_restores_clock_and_controller_after_success(
    clock_controller,
):
    baseline = clock_controller.current
    assert clock_controller.sequence_index == 0
    assert clock_controller.profile_step_index == 0
    assert clock_controller.trace == ()

    with clock_controller.scenario("R-STRESS60", "robinhood_candidate"):
        clock_controller.apply("R-STRESS60", 0)
        clock_controller.apply("R-STRESS60", 1)
        clock_controller.apply("R-STRESS60", 2)
        assert clock_controller.current == ClockPoint(N + 60, T + 720)

    assert clock_controller.current == baseline
    assert clock_controller.sequence_index == 0
    assert clock_controller.profile_step_index == 0
    assert clock_controller.trace == ()
    assert clock_controller.active_profile is None


def test_nested_scenario_restores_after_assertion_failure(clock_controller):
    baseline = clock_controller.current
    with pytest.raises(AssertionError, match="intentional scenario failure"):
        with clock_controller.scenario("B-ORD", "base_current"):
            clock_controller.apply("B-ORD", 0)
            raise AssertionError("intentional scenario failure")

    assert clock_controller.current == baseline
    assert clock_controller.sequence_index == 0
    assert clock_controller.profile_step_index == 0
    assert clock_controller.trace == ()


def test_nested_scenario_restores_after_caught_revert(
    clock_controller, observer_deployer
):
    baseline = clock_controller.current
    with clock_controller.scenario("R-PLUS1", "robinhood_candidate"):
        clock_controller.apply("R-PLUS1", 0)
        observer = observer_deployer.deploy()
        outcome = clock_controller.observed_call(
            "BN-004",
            "caught boundary revert",
            observer.fail_at,
            N,
            components=("CM-059",),
            observed_by="boundary:controlled equality",
            expected_revert="clock boundary",
        )
        assert outcome.success is False

    assert clock_controller.current == baseline
    assert clock_controller.sequence_index == 0
    assert clock_controller.profile_step_index == 0
    assert clock_controller.trace == ()


def test_scenario_restoration_failure_does_not_mask_body_exception():
    controller = ClockController(_NonRestoringEnv())
    with pytest.raises(AssertionError, match="primary scenario failure") as raised:
        with controller.scenario():
            controller.set(number=101, timestamp=201)
            raise AssertionError("primary scenario failure")

    notes = getattr(raised.value, "__notes__", ())
    assert len(notes) == 1
    assert notes[0].startswith(
        "CLOCK_FAIL id=HARNESS components=CM-059 profile=UNBOUND"
    )
    assert "function=boa.env.anchor label=restoration" in notes[0]


def test_scenario_restoration_failure_raises_without_body_exception():
    controller = ClockController(_NonRestoringEnv())
    with pytest.raises(
        ClockHarnessError,
        match=r"^CLOCK_FAIL id=HARNESS components=CM-059 profile=UNBOUND",
    ):
        with controller.scenario():
            controller.set(number=101, timestamp=201)


def test_cross_test_isolation_lifecycle_restores_absolute_baseline(
    clock_controller,
):
    baseline = clock_controller.current
    changed = ClockPoint(
        baseline.number + 2,
        baseline.timestamp + 4,
    )

    with clock_controller.scenario():
        clock_controller.assert_scenario_start()
        clock_controller.set(
            number=changed.number,
            timestamp=changed.timestamp,
        )
        assert clock_controller.current == changed
        assert clock_controller.trace

    assert clock_controller.current == baseline
    assert clock_controller.sequence_index == 0
    assert clock_controller.profile_step_index == 0
    assert clock_controller.trace == ()

    with clock_controller.scenario():
        clock_controller.assert_scenario_start()
        assert clock_controller.current == baseline
        assert clock_controller.sequence_index == 0
        assert clock_controller.profile_step_index == 0
        assert clock_controller.trace == ()


def test_deployed_system_exposes_equal_fingerprints_for_all_parameter_labels(
    deployed_system, clock_controller, observer_deployer
):
    fingerprints = {}
    for parameter_profile in sorted(PARAMETER_PROFILES):
        with deployed_system(
            "B-ORD",
            parameter_profile,
            observer_deployer.deploy,
            artifact=observer_deployer,
            artifact_id="clock-observer",
            parameter_values={"profile_label": parameter_profile},
            parameter_bounds={"delay": [0, 50_400]},
        ) as system:
            assert system.clock_profile.name == "B-ORD"
            assert system.parameter_profile == parameter_profile
            assert system.parameter_values == {
                "profile_label": parameter_profile
            }
            assert system.artifact_id == "clock-observer"
            assert system.clock_controller.sequence_index == 1
            assert system.clock_controller.profile_step_index == 1
            assert len(system.clock_controller.trace) == 1
            fingerprints[parameter_profile] = system.artifact_fingerprint

        assert clock_controller.sequence_index == 0
        assert clock_controller.profile_step_index == 0
        assert clock_controller.trace == ()

    assert len({fingerprint.digest for fingerprint in fingerprints.values()}) == 1
    first = fingerprints["base_current"]
    assert len(first.digest) == 64
    assert len(first.source_sha256) == 64
    assert first.compiler_version.startswith("vyper==0.4.3")
    assert len(first.abi_sha256) == 64
    assert len(first.creation_bytecode_sha256) == 64


def test_artifact_fingerprint_is_stable_for_same_compiler_data(
    observer_deployer,
):
    first = artifact_fingerprint(observer_deployer)
    second = artifact_fingerprint(observer_deployer)
    assert first == second
    assert_identical_artifacts(first, second)


def test_intentional_artifact_mismatch_fails_clearly(
    deployed_system, observer_deployer, different_observer_deployer
):
    with deployed_system(
        "B-ORD",
        "base_current",
        observer_deployer.deploy,
        artifact=observer_deployer,
        artifact_id="intentional-mismatch",
    ):
        pass

    with pytest.raises(ArtifactMismatchError) as raised:
        with deployed_system(
            "B-ORD",
            "robinhood_candidate",
            different_observer_deployer.deploy,
            artifact=different_observer_deployer,
            artifact_id="intentional-mismatch",
        ):
            pass

    message = str(raised.value)
    assert "ARTIFACT_MISMATCH artifact_id=intentional-mismatch" in message
    assert "baseline_profile=base_current" in message
    assert "candidate_profile=robinhood_candidate" in message
    assert "source_sha256" in message
    assert "creation_bytecode_sha256" in message


def test_failing_deployed_scenario_keeps_artifact_baseline_without_state_leak(
    deployed_system,
    clock_controller,
    observer_deployer,
    different_observer_deployer,
):
    baseline = clock_controller.current
    with pytest.raises(AssertionError, match="failed deployed case"):
        with deployed_system(
            "R-J2-J4",
            "robinhood_candidate",
            different_observer_deployer.deploy,
            artifact=different_observer_deployer,
            artifact_id="failure-isolation",
        ):
            raise AssertionError("failed deployed case")

    assert clock_controller.current == baseline
    assert clock_controller.sequence_index == 0
    assert clock_controller.profile_step_index == 0
    assert clock_controller.trace == ()

    with pytest.raises(ArtifactMismatchError) as raised:
        with deployed_system(
            "B-ORD",
            "base_canonical",
            observer_deployer.deploy,
            artifact=observer_deployer,
            artifact_id="failure-isolation",
        ):
            pass
    assert "baseline_profile=robinhood_candidate" in str(raised.value)
    assert "candidate_profile=base_canonical" in str(raised.value)

    assert clock_controller.current == baseline
    assert clock_controller.sequence_index == 0
    assert clock_controller.profile_step_index == 0
    assert clock_controller.trace == ()

    with deployed_system(
        "B-ORD",
        "base_canonical",
        different_observer_deployer.deploy,
        artifact=different_observer_deployer,
        artifact_id="failure-isolation",
    ) as system:
        assert system.clock_controller.current == ClockPoint(N, T)
        assert system.clock_controller.sequence_index == 1
        assert system.clock_controller.profile_step_index == 1
