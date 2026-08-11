"""Revision-20 mechanism evidence; calibration and deployment are not approved."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.simulations.instant_bond_lane_controller import (
    BPS,
    BOUND_IMPLEMENTATION,
    MAX_DECAY_EPOCHS,
    STATUS,
    OverrideState,
    Params,
    apply_decay,
    apply_signal,
    build_artifact,
    cancel_override,
    canonical_bytes,
    commit_override,
    install_override,
    invalidate_override_for_config_change,
    project_installed_override,
    project_next_rollover_override,
    signal_for,
    validate_params,
)


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = ROOT / "docs" / "instant-bond-lane" / "controller-simulation-v2.json"


def test_canonical_simulation_artifact_is_current():
    expected = canonical_bytes(build_artifact())
    assert ARTIFACT.read_bytes() == expected
    artifact = json.loads(expected)
    assert artifact["status"] == STATUS
    assert artifact["bound_implementation"] == BOUND_IMPLEMENTATION
    assert artifact["calibration_status"] == "not_approved"
    assert artifact["authority"].startswith("implemented mechanism evidence")
    assert artifact["manual_override_lifecycle"][
        "calendar_target_window_or_lead"
    ] == "not_applicable"
    assert artifact["manual_override_lifecycle"][
        "skipped_epochs_preserve_exact_target"
    ] == "pass"
    assert "target_epoch" not in expected.decode()


def test_upward_timing_and_utilization_endpoints():
    p = Params()

    first = signal_for(((0, p.payment_cap),), p)
    midpoint = signal_for((((p.epoch_length - 1) // 2, p.payment_cap),), p)
    last = signal_for(((p.epoch_length - 1, p.payment_cap),), p)
    threshold = signal_for(((0, p.payment_cap * p.u_high_bps // BPS),), p)

    assert first.effective_step_bps == p.max_up_bps
    assert midpoint.effective_step_bps == (p.min_up_bps + p.max_up_bps) // 2
    assert last.effective_step_bps == p.min_up_bps
    assert threshold.effective_step_bps == p.min_up_bps


def test_epoch_length_boundaries_and_partial_first_epoch():
    p = Params()

    one = replace(p, epoch_length=1)
    two = replace(p, epoch_length=2)
    even = replace(p, epoch_length=100)

    assert signal_for(((0, one.payment_cap),), one).effective_step_bps == (
        one.max_up_bps
    )
    assert signal_for(((0, two.payment_cap),), two).effective_step_bps == (
        two.max_up_bps
    )
    assert signal_for(((1, two.payment_cap),), two).effective_step_bps == (
        two.min_up_bps
    )
    assert signal_for(((0, even.payment_cap),), even).effective_step_bps == (
        even.max_up_bps
    )
    assert signal_for(((99, even.payment_cap),), even).effective_step_bps == (
        even.min_up_bps
    )

    partial_first = signal_for(
        ((0, p.payment_cap),),
        p,
        timing_eligible=False,
    )
    assert partial_first.average_lateness_bps == 0
    assert partial_first.earliness_bps == BPS
    assert not partial_first.timing_eligible
    assert partial_first.effective_step_bps == p.min_up_bps


def test_amount_weighting_prevents_late_tail_from_controlling_signal():
    p = Params()

    mostly_early = signal_for(((0, 9_900), (100, 100)), p)
    mostly_late = signal_for(((0, 100), (100, 9_900)), p)

    assert mostly_early.effective_step_bps > mostly_late.effective_step_bps
    assert mostly_early.effective_step_bps == 794
    assert mostly_late.effective_step_bps == 206


def test_downward_range_uses_utilization_not_purchase_timing():
    p = Params()

    at_low = signal_for(((0, 2_000),), p)
    half_low_first = signal_for(((0, 1_000),), p)
    half_low_last = signal_for(((100, 1_000),), p)

    assert at_low.effective_step_bps == p.min_down_bps
    assert half_low_first.effective_step_bps == 100
    assert half_low_last.effective_step_bps == half_low_first.effective_step_bps


def test_parameter_boundaries_remove_degenerate_thresholds():
    p = Params()

    validate_params(p)
    with pytest.raises(AssertionError):
        validate_params(replace(p, u_low_bps=0))
    with pytest.raises(AssertionError):
        validate_params(replace(p, u_high_bps=BPS))
    with pytest.raises(AssertionError):
        validate_params(replace(p, max_decay_epochs=MAX_DECAY_EPOCHS + 1))


def test_preclamp_floor_ceiling_and_bounded_decay():
    p = Params()
    full = signal_for(((0, p.payment_cap),), p)
    hold = signal_for(((0, p.payment_cap // 2),), p)
    lowered = replace(
        p,
        initial_rate=p.initial_rate // 2,
        rate_ceiling=p.initial_rate // 2,
    )

    assert apply_signal(p.min_rate, full, p) == p.min_rate
    assert apply_signal(p.initial_rate, hold, lowered) == lowered.rate_ceiling
    assert apply_signal(p.initial_rate, full, lowered) == (
        lowered.rate_ceiling * BPS // (BPS + lowered.max_up_bps)
    )
    assert apply_decay(p.initial_rate, p.max_decay_epochs, p) == apply_decay(
        p.initial_rate,
        p.max_decay_epochs + 1,
        p,
    )


def test_next_successful_rollover_override_is_exact_after_one_or_many_epochs():
    p = Params()
    target_rate = 925_000_000_000_000_000

    controller_rate = 880_000_000_000_000_000
    same_epoch = project_next_rollover_override(
        target_rate,
        4,
        4,
        controller_rate,
        p,
    )
    next_rollover = project_next_rollover_override(
        target_rate,
        4,
        5,
        controller_rate,
        p,
    )
    skipped_rollover = project_next_rollover_override(
        target_rate,
        4,
        8,
        controller_rate,
        p,
    )

    assert same_epoch == ("pending", controller_rate, 0)
    assert next_rollover == ("apply", target_rate, 1)
    assert skipped_rollover == ("apply", target_rate, 4)


def test_invalid_manual_override_rates_reject_instead_of_clamping():
    p = Params()

    controller_rate = 880_000_000_000_000_000
    assert project_next_rollover_override(
        p.min_rate - 1,
        4,
        5,
        controller_rate,
        p,
    ) == ("reject", None, 0)
    assert project_next_rollover_override(
        p.rate_ceiling + 1,
        4,
        5,
        controller_rate,
        p,
    ) == ("reject", None, 0)


def _install_fixture(
    state: OverrideState = OverrideState(),
    *,
    initialized: bool = True,
    target_rate: int = 925_000_000_000_000_000,
    config_version: int = 7,
    expected_config_version: int | None = None,
    expected_override_version: int | None = None,
) -> OverrideState:
    return install_override(
        state,
        initialized=initialized,
        target_rate=target_rate,
        config_version=config_version,
        expected_config_version=(
            config_version
            if expected_config_version is None
            else expected_config_version
        ),
        expected_override_version=(
            state.version
            if expected_override_version is None
            else expected_override_version
        ),
        p=Params(),
    )


def test_override_lifecycle_is_versioned_repeatable_and_one_shot():
    p = Params()
    installed = _install_fixture()
    assert installed.version == 1

    preview = project_installed_override(
        installed,
        stored_epoch=4,
        projected_epoch=5,
        controller_rate=880_000_000_000_000_000,
        config_version=7,
        p=p,
    )
    assert preview == project_installed_override(
        installed,
        stored_epoch=4,
        projected_epoch=5,
        controller_rate=880_000_000_000_000_000,
        config_version=7,
        p=p,
    )
    assert preview.final_rate == installed.target_rate
    assert preview.counterfactual_controller_rate == 880_000_000_000_000_000

    pending_projection, same_epoch_state = commit_override(
        installed,
        stored_epoch=4,
        projected_epoch=4,
        controller_rate=880_000_000_000_000_000,
        config_version=7,
        successful=True,
        p=p,
    )
    assert pending_projection.status == "pending"
    assert same_epoch_state == installed

    _, failed_state = commit_override(
        installed,
        stored_epoch=4,
        projected_epoch=8,
        controller_rate=880_000_000_000_000_000,
        config_version=7,
        successful=False,
        p=p,
    )
    assert failed_state == installed

    _, consumed = commit_override(
        installed,
        stored_epoch=4,
        projected_epoch=8,
        controller_rate=880_000_000_000_000_000,
        config_version=7,
        successful=True,
        p=p,
    )
    assert consumed == OverrideState(version=2)
    assert project_installed_override(
        consumed,
        stored_epoch=8,
        projected_epoch=8,
        controller_rate=880_000_000_000_000_000,
        config_version=7,
        p=p,
    ).status == "none"

    skipped = project_installed_override(
        installed,
        stored_epoch=4,
        projected_epoch=5 + p.max_decay_epochs + 10,
        controller_rate=880_000_000_000_000_000,
        config_version=7,
        p=p,
    )
    assert skipped.elapsed_epochs == p.max_decay_epochs + 11
    assert skipped.final_rate == installed.target_rate


def test_override_cancel_invalidation_and_stale_versions():
    installed = _install_fixture()

    assert cancel_override(
        installed,
        expected_override_version=installed.version,
    ) == OverrideState(version=2)
    assert invalidate_override_for_config_change(
        installed,
        old_config_version=7,
        new_config_version=8,
    ) == OverrideState(version=2)
    assert invalidate_override_for_config_change(
        OverrideState(version=2),
        old_config_version=7,
        new_config_version=8,
    ) == OverrideState(version=2)

    with pytest.raises(AssertionError):
        _install_fixture(installed)
    with pytest.raises(AssertionError):
        cancel_override(installed, expected_override_version=0)

    reinstalled = _install_fixture(
        OverrideState(version=2),
        expected_override_version=2,
    )
    assert reinstalled.version == 3
    with pytest.raises(AssertionError):
        cancel_override(reinstalled, expected_override_version=1)


def test_override_install_rejects_stale_or_impossible_inputs_without_clamping():
    p = Params()

    assert _install_fixture(target_rate=p.min_rate).target_rate == p.min_rate
    assert _install_fixture(target_rate=p.rate_ceiling).target_rate == p.rate_ceiling

    invalid_cases = (
        {"initialized": False},
        {"target_rate": p.min_rate - 1},
        {"target_rate": p.rate_ceiling + 1},
        {"expected_config_version": 6},
        {"expected_override_version": 1},
    )
    for changes in invalid_cases:
        with pytest.raises(AssertionError):
            _install_fixture(**changes)

    installed = _install_fixture()
    stale_config = project_installed_override(
        installed,
        stored_epoch=4,
        projected_epoch=5,
        controller_rate=880_000_000_000_000_000,
        config_version=8,
        p=p,
    )
    assert stale_config.status == "invalidated"
    assert stale_config.final_rate == stale_config.counterfactual_controller_rate
