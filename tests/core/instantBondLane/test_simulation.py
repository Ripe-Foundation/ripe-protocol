"""Revision-22 current-RH mechanism evidence; calibration is not approved."""

import json
import shutil
from dataclasses import replace
from pathlib import Path

import boa
import pytest

from conf_utils import filter_logs
from scripts.simulations.instant_bond_lane_controller import (
    BPS,
    BOUND_IMPLEMENTATION,
    MAX_DECAY_EPOCHS,
    STATUS,
    OverrideState,
    Params,
    apply_decay,
    apply_signal,
    bound_implementation,
    build_artifact,
    cancel_override,
    canonical_bytes,
    commit_override,
    install_override,
    invalidate_override_for_config_change,
    lateness_bps,
    project_installed_override,
    project_lock_quote,
    project_next_rollover_override,
    signal_for,
    validate_params,
)


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = ROOT / "docs" / "instant-bond-lane" / "controller-simulation-v2.json"


def contract_params(ctx, config, initial_rate):
    return Params(
        epoch_length=ctx.epoch_length,
        payment_cap=config[1],
        min_payment_amount=config[2],
        u_low_bps=config[7],
        u_high_bps=config[6],
        min_up_bps=config[8],
        max_up_bps=config[9],
        min_down_bps=config[10],
        max_down_bps=config[11],
        decay_bps=config[12],
        max_decay_epochs=config[13],
        min_rate=BPS,
        rate_ceiling=config[4] * BPS // (BPS + config[14]),
        initial_rate=initial_rate,
    )


@pytest.mark.artifact
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


@pytest.mark.artifact
def test_artifact_binding_hashes_exact_contract_source_bytes(tmp_path):
    copied_root = tmp_path / "repo"
    lane_source = copied_root / "contracts" / "core" / "InstantBondLane.vy"
    foxtrot_source = (
        copied_root / "contracts" / "config" / "SwitchboardFoxtrot.vy"
    )
    lane_source.parent.mkdir(parents=True)
    foxtrot_source.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / lane_source.relative_to(copied_root), lane_source)
    shutil.copyfile(ROOT / foxtrot_source.relative_to(copied_root), foxtrot_source)

    original = bound_implementation(copied_root)
    assert original == BOUND_IMPLEMENTATION

    lane_source.write_bytes(lane_source.read_bytes() + b"\n# mutation\n")
    lane_mutation = bound_implementation(copied_root)
    assert lane_mutation["instant_bond_lane_source_sha256"] != original[
        "instant_bond_lane_source_sha256"
    ]
    assert lane_mutation["switchboard_foxtrot_source_sha256"] == original[
        "switchboard_foxtrot_source_sha256"
    ]
    assert build_artifact(copied_root)["bound_implementation"] == lane_mutation

    shutil.copyfile(ROOT / "contracts/core/InstantBondLane.vy", lane_source)
    foxtrot_source.write_bytes(foxtrot_source.read_bytes() + b"\n# mutation\n")
    foxtrot_mutation = bound_implementation(copied_root)
    assert foxtrot_mutation["instant_bond_lane_source_sha256"] == original[
        "instant_bond_lane_source_sha256"
    ]
    assert foxtrot_mutation["switchboard_foxtrot_source_sha256"] != original[
        "switchboard_foxtrot_source_sha256"
    ]


@pytest.mark.artifact
def test_source_binding_is_independent_of_invocation_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert bound_implementation() == BOUND_IMPLEMENTATION
    assert build_artifact()["bound_implementation"] == BOUND_IMPLEMENTATION


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
    with pytest.raises(AssertionError):
        validate_params(replace(p, decay_bps=197))


def test_minimum_up_then_empty_decay_cannot_lower_unclamped_price():
    p = Params()
    minimum_up = signal_for(((p.epoch_length - 1, p.payment_cap),), p)
    after_up = apply_signal(p.initial_rate, minimum_up, p)
    after_decay = apply_decay(after_up, 1, p)

    assert minimum_up.effective_step_bps == p.min_up_bps
    assert after_decay <= p.initial_rate


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
    expected_override_version: int | None = None,
) -> OverrideState:
    return install_override(
        state,
        initialized=initialized,
        target_rate=target_rate,
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
        p=p,
    )
    assert preview == project_installed_override(
        installed,
        stored_epoch=4,
        projected_epoch=5,
        controller_rate=880_000_000_000_000_000,
        p=p,
    )
    assert preview.final_rate == installed.target_rate
    assert preview.counterfactual_controller_rate == 880_000_000_000_000_000

    pending_projection, same_epoch_state = commit_override(
        installed,
        stored_epoch=4,
        projected_epoch=4,
        controller_rate=880_000_000_000_000_000,
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
        successful=False,
        p=p,
    )
    assert failed_state == installed

    _, consumed = commit_override(
        installed,
        stored_epoch=4,
        projected_epoch=8,
        controller_rate=880_000_000_000_000_000,
        successful=True,
        p=p,
    )
    assert consumed == OverrideState(version=2)
    assert project_installed_override(
        consumed,
        stored_epoch=8,
        projected_epoch=8,
        controller_rate=880_000_000_000_000_000,
        p=p,
    ).status == "none"

    skipped = project_installed_override(
        installed,
        stored_epoch=4,
        projected_epoch=5 + p.max_decay_epochs + 10,
        controller_rate=880_000_000_000_000_000,
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
    ) == OverrideState(version=2)
    assert invalidate_override_for_config_change(
        OverrideState(version=2),
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
        {"expected_override_version": 1},
    )
    for changes in invalid_cases:
        with pytest.raises(AssertionError):
            _install_fixture(**changes)

    installed = _install_fixture()
    with pytest.raises(AssertionError):
        cancel_override(installed, expected_override_version=0)


def test_repeated_first_midpoint_and_last_block_strategies_are_explicit():
    paths = {
        path["name"]: path for path in build_artifact()["path_scenarios"]
    }
    fast = paths["repeated_fast_full"]
    midpoint = paths["repeated_mid_full"]
    late = paths["repeated_late_full"]

    assert len(fast["epochs"]) == len(midpoint["epochs"]) == len(late["epochs"]) == 32
    assert fast["final_price_index_bps"] > midpoint["final_price_index_bps"]
    assert midpoint["final_price_index_bps"] > late["final_price_index_bps"]
    assert late["epochs"][0]["effective_step_bps"] == Params().min_up_bps
    assert late["final_price_index_bps"] > BPS


@pytest.mark.parametrize(
    "max_bonus,min_lock,max_lock,requested_lock",
    [
        (0, 100, 1_000, 550),
        (100, 100, 1_000, 550),
        (5_000, 100, 1_000, 100),
        (5_000, 100, 1_000, 550),
        (100_000, 100, 1_000, 1_000),
        (5_000, 500, 500, 499),
        (5_000, 500, 500, 500),
        (5_000, 100, 1_000, 5_000),
    ],
)
def test_published_lock_bonus_model_matches_contract(
    lane_factory,
    max_bonus,
    min_lock,
    max_lock,
    requested_lock,
):
    ctx = lane_factory()
    config = ctx.set_config(
        maxEffectiveRate=200 * 10**18,
        maxLockBonus=max_bonus,
    )
    ctx.setup_lock_terms(min_lock=min_lock, max_lock=max_lock)
    amount = 10 * ctx.scale
    quote = ctx.quote(amount, requested_lock)
    modeled = project_lock_quote(
        payment_amount=amount,
        payment_scale=ctx.scale,
        rate=quote.rate,
        max_lock_bonus_bps=max_bonus,
        requested_lock=requested_lock,
        min_lock=min_lock,
        max_lock=max_lock,
    )

    assert quote.available == modeled["valid_requested_lock"]
    assert quote.actualLock == modeled["actual_lock"]
    assert quote.bonusRatio == modeled["bonus_ratio_bps"]
    assert quote.baseRipe == modeled["base_ripe"]
    assert quote.bonusRipe == modeled["bonus_ripe"]
    assert quote.totalRipe == modeled["total_ripe"]
    # Independent oracle for a nonzero interior case; this must not reuse the
    # published helper's result to define the expected arithmetic.
    if (max_bonus, min_lock, max_lock, requested_lock) == (5_000, 100, 1_000, 550):
        assert quote.bonusRatio == 2_500
        assert quote.bonusRipe == quote.baseRipe // 4
    assert config[14] == max_bonus


def test_bonus_adjusted_base_rate_ceiling_matches_contract(lane_factory):
    ctx = lane_factory()
    config = ctx.set_config(
        maxEffectiveRate=3 * 10**18,
        seedRate=2 * 10**18,
        maxLockBonus=5_000,
    )
    ctx.setup_lock_terms(min_lock=100, max_lock=1_000)
    quote = ctx.quote(ctx.scale, 1_000)
    expected_ceiling = config[4] * BPS // (BPS + config[14])
    assert quote.rate == expected_ceiling
    assert quote.totalRipe * ctx.scale <= ctx.scale * config[4]


@pytest.mark.parametrize(
    "accepted_units, offset, expected_direction",
    [
        (100, 0, "up"),
        (100, 49, "up"),
        (100, 99, "up"),
        (10, 50, "down"),
        (50, 50, "hold"),
    ],
)
def test_published_controller_model_matches_lane_rollover(
    lane_factory,
    accepted_units,
    offset,
    expected_direction,
):
    ctx = lane_factory()
    cap = 100 * ctx.scale
    config = ctx.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=ctx.scale,
        maxEffectiveRate=2 * 10**18,
        seedRate=10**18,
        uHighBps=8_000,
        uLowBps=2_000,
        minUpBps=200,
        maxUpBps=800,
        minDownBps=50,
        maxDownBps=100,
        decayBps=100,
        maxDecayEpochs=4,
        maxLockBonus=0,
    )

    ctx.buy(50 * ctx.scale)
    boa.env.time_travel(blocks=ctx.epoch_length + offset)

    accepted = accepted_units * ctx.scale
    ctx.buy(accepted)
    old_rate = ctx.lane.epochState().rate
    p = contract_params(ctx, config, old_rate)
    signal = signal_for(((offset, accepted),), p)
    expected_rate = apply_signal(old_rate, signal, p)

    boa.env.time_travel(blocks=ctx.epoch_length - offset)
    quote = ctx.quote(ctx.scale)
    ctx.buy(ctx.scale, expected_epoch=quote.epoch)
    event = filter_logs(ctx.lane, "EpochRolled")[-1]

    assert signal.direction == expected_direction
    assert event.previousAcceptedPayment == signal.accepted
    assert event.previousWeightedLateness == accepted * lateness_bps(
        offset, ctx.epoch_length
    )
    assert event.utilizationBps == signal.utilization_bps
    assert event.effectiveAdjustmentBps == signal.effective_step_bps
    assert event.decaySteps == 0
    assert event.controllerRate == expected_rate
    assert event.newRate == quote.rate == expected_rate


@pytest.mark.parametrize("elapsed", [1, 2, 4, 5, 1_000])
def test_published_decay_model_matches_lane_skipped_epochs(
    lane_factory,
    elapsed,
):
    ctx = lane_factory()
    cap = 100 * ctx.scale
    config = ctx.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=ctx.scale,
        minUpBps=200,
        maxUpBps=800,
        minDownBps=50,
        maxDownBps=100,
        decayBps=100,
        maxDecayEpochs=4,
        maxLockBonus=0,
    )
    accepted = 50 * ctx.scale
    ctx.buy(accepted)
    old_rate = ctx.lane.epochState().rate
    p = contract_params(ctx, config, old_rate)
    signal = signal_for(((0, accepted),), p)
    expected_steps = min(elapsed - 1, p.max_decay_epochs)
    expected_rate = apply_decay(
        apply_signal(old_rate, signal, p),
        expected_steps,
        p,
    )

    boa.env.time_travel(blocks=elapsed * ctx.epoch_length)
    quote = ctx.quote(ctx.scale)
    ctx.buy(ctx.scale, expected_epoch=quote.epoch)
    event = filter_logs(ctx.lane, "EpochRolled")[-1]

    assert signal.direction == "hold"
    assert event.effectiveAdjustmentBps == 0
    assert event.decaySteps == expected_steps
    assert event.controllerRate == expected_rate
    assert event.newRate == quote.rate == expected_rate


def test_published_override_model_matches_lane_lifecycle(lane_factory):
    ctx = lane_factory()
    cap = 100 * ctx.scale
    config = ctx.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=ctx.scale,
        minUpBps=200,
        maxUpBps=800,
        minDownBps=50,
        maxDownBps=100,
        decayBps=100,
        maxDecayEpochs=4,
        maxLockBonus=0,
    )
    accepted = ctx.scale
    ctx.buy(accepted)
    old_rate = ctx.lane.epochState().rate
    p = contract_params(ctx, config, old_rate)
    controller_rate = apply_signal(
        old_rate,
        signal_for(((0, accepted),), p),
        p,
    )
    target_rate = 9 * 10**17

    model_state = install_override(
        OverrideState(),
        initialized=True,
        target_rate=target_rate,
        expected_override_version=0,
        p=p,
    )
    ctx.set_rate_override(target_rate)
    assert ctx.lane.rateOverride() == model_state.target_rate

    same_epoch = project_installed_override(
        model_state,
        stored_epoch=0,
        projected_epoch=0,
        controller_rate=old_rate,
        p=p,
    )
    assert same_epoch.status == "pending"
    assert ctx.quote(ctx.scale).rate == same_epoch.final_rate

    boa.env.time_travel(blocks=ctx.epoch_length)
    projected = project_installed_override(
        model_state,
        stored_epoch=0,
        projected_epoch=1,
        controller_rate=controller_rate,
        p=p,
    )
    quote = ctx.quote(ctx.scale)
    assert projected.status == "apply"
    assert quote.rate == projected.final_rate == target_rate

    projection, committed_state = commit_override(
        model_state,
        stored_epoch=0,
        projected_epoch=1,
        controller_rate=controller_rate,
        successful=True,
        p=p,
    )
    ctx.buy(ctx.scale, expected_epoch=quote.epoch)
    applied = filter_logs(ctx.lane, "RateOverrideApplied")[-1]

    assert applied.controllerRate == projection.counterfactual_controller_rate
    assert applied.targetRate == projection.final_rate
    assert ctx.lane.rateOverride() == committed_state.target_rate == 0
