#!/usr/bin/env python3
"""REVISION 22 CURRENT-RH CANDIDATE — mechanism evidence; calibration not approved.

Deterministic integer model for the Ripe Reserve Engine controller. This
model is mechanism evidence only. It does not select production parameters and does
not authorize contract changes or deployment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


BPS = 10_000
RATE_SCALE = 10**18
SCHEMA = "ripe.reserve-engine.controller-simulation.v2"
REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_SOURCE = Path("contracts/core/RipeReserveEngine.vy")
VESTING_SOURCE = Path("contracts/core/RipeReserveVesting.vy")
FOXTROT_SOURCE = Path("contracts/config/SwitchboardFoxtrot.vy")
STATUS = (
    "REVISION 22 CURRENT-RH CANDIDATE — implemented and mechanism-validated; "
    "calibration and deployment not approved"
)
MAX_DECAY_EPOCHS = 32


def source_sha256(repo_root: Path, source: Path) -> str:
    """Hash the exact source bytes rooted at the checked repository."""

    return hashlib.sha256((repo_root / source).read_bytes()).hexdigest()


def bound_implementation(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    """Bind generated evidence to the contract sources, never copied constants."""

    return {
        "ripe_reserve_engine_source_sha256": source_sha256(
            repo_root, ENGINE_SOURCE
        ),
        "ripe_reserve_vesting_source_sha256": source_sha256(
            repo_root, VESTING_SOURCE
        ),
        "switchboard_foxtrot_source_sha256": source_sha256(
            repo_root, FOXTROT_SOURCE
        ),
    }


BOUND_IMPLEMENTATION = bound_implementation()


@dataclass(frozen=True)
class Params:
    epoch_length: int = 101
    payment_cap: int = 10_000
    min_payment_amount: int = 10
    u_low_bps: int = 2_000
    u_high_bps: int = 8_000
    min_up_bps: int = 200
    max_up_bps: int = 800
    min_down_bps: int = 50
    max_down_bps: int = 150
    decay_bps: int = 150
    max_decay_epochs: int = 4
    min_rate: int = 10_000
    rate_ceiling: int = 2 * RATE_SCALE
    initial_rate: int = RATE_SCALE


@dataclass(frozen=True)
class Signal:
    accepted: int
    utilization_bps: int
    average_lateness_bps: int
    earliness_bps: int
    timing_eligible: bool
    utilization_strength_bps: int
    demand_strength_bps: int
    weakness_bps: int
    direction: str
    effective_step_bps: int


@dataclass(frozen=True)
class OverrideState:
    """Pure model for one installed named-epoch rate override."""

    target_rate: int = 0
    target_epoch: int = 0

    @property
    def exists(self) -> bool:
        return self.target_rate != 0


@dataclass(frozen=True)
class OverrideProjection:
    status: str
    counterfactual_controller_rate: int
    final_rate: int


Acquisition = tuple[int, int]


def validate_params(p: Params) -> None:
    assert p.epoch_length > 0
    assert p.payment_cap > 0
    assert 0 < p.min_payment_amount <= p.payment_cap
    assert 0 < p.u_low_bps < p.u_high_bps < BPS
    assert 0 < p.min_up_bps <= p.max_up_bps <= BPS
    assert 0 < p.min_down_bps <= p.max_down_bps <= p.decay_bps < BPS
    assert p.max_down_bps < p.min_up_bps
    assert (BPS + p.min_up_bps) * (BPS - p.max_down_bps) >= BPS * BPS
    assert (BPS + p.min_up_bps) * (BPS - p.decay_bps) >= BPS * BPS
    assert 0 < p.max_decay_epochs <= MAX_DECAY_EPOCHS
    assert 0 < p.min_rate <= p.initial_rate <= p.rate_ceiling


def lateness_bps(offset: int, epoch_length: int) -> int:
    assert 0 <= offset < epoch_length
    if epoch_length == 1:
        return 0
    return offset * BPS // (epoch_length - 1)


def signal_for(
    acquisitions: Sequence[Acquisition],
    p: Params,
    *,
    timing_eligible: bool = True,
) -> Signal:
    accepted = sum(amount for _, amount in acquisitions)
    assert 0 <= accepted <= p.payment_cap
    assert all(amount >= p.min_payment_amount for _, amount in acquisitions)

    if accepted == 0:
        return Signal(
            0,
            0,
            0,
            0,
            timing_eligible,
            0,
            0,
            0,
            "decay",
            p.decay_bps,
        )

    weighted_lateness = sum(
        amount * lateness_bps(offset, p.epoch_length)
        for offset, amount in acquisitions
    )
    average_lateness = weighted_lateness // accepted
    earliness = BPS - average_lateness
    utilization = accepted * BPS // p.payment_cap

    if utilization >= p.u_high_bps:
        utilization_strength = (
            (utilization - p.u_high_bps) * BPS
            // (BPS - p.u_high_bps)
        )
        applied_earliness = earliness if timing_eligible else 0
        demand_strength = utilization_strength * applied_earliness // BPS
        step = p.min_up_bps + (
            (p.max_up_bps - p.min_up_bps) * demand_strength // BPS
        )
        return Signal(
            accepted,
            utilization,
            average_lateness,
            earliness,
            timing_eligible,
            utilization_strength,
            demand_strength,
            0,
            "up",
            step,
        )

    if utilization <= p.u_low_bps:
        weakness = (p.u_low_bps - utilization) * BPS // p.u_low_bps
        step = p.min_down_bps + (
            (p.max_down_bps - p.min_down_bps) * weakness // BPS
        )
        return Signal(
            accepted,
            utilization,
            average_lateness,
            earliness,
            timing_eligible,
            0,
            0,
            weakness,
            "down",
            step,
        )

    return Signal(
        accepted,
        utilization,
        average_lateness,
        earliness,
        timing_eligible,
        0,
        0,
        0,
        "hold",
        0,
    )


def apply_signal(rate: int, signal: Signal, p: Params) -> int:
    bounded_rate = min(rate, p.rate_ceiling)
    if signal.direction == "up":
        return max(
            bounded_rate * BPS // (BPS + signal.effective_step_bps),
            p.min_rate,
        )
    if signal.direction in {"down", "decay"}:
        return min(
            bounded_rate * BPS // (BPS - signal.effective_step_bps),
            p.rate_ceiling,
        )
    assert signal.direction == "hold"
    return bounded_rate


def apply_decay(rate: int, steps: int, p: Params) -> int:
    rate = min(rate, p.rate_ceiling)
    for _ in range(min(steps, p.max_decay_epochs)):
        rate = min(rate * BPS // (BPS - p.decay_bps), p.rate_ceiling)
    return rate


def price_index_bps(rate: int, initial_rate: int = RATE_SCALE) -> int:
    return initial_rate * BPS // rate


def scenario(
    name: str,
    acquisitions: Sequence[Acquisition],
    p: Params,
    *,
    timing_eligible: bool = True,
) -> dict:
    signal = signal_for(acquisitions, p, timing_eligible=timing_eligible)
    new_rate = apply_signal(p.initial_rate, signal, p)
    return {
        "name": name,
        "acquisitions": [list(item) for item in acquisitions],
        **asdict(signal),
        "old_rate": p.initial_rate,
        "new_rate": new_rate,
        "price_index_bps": price_index_bps(new_rate, p.initial_rate),
    }


def run_committed_epoch_path(
    name: str,
    epochs: Sequence[Sequence[Acquisition]],
    p: Params,
) -> dict:
    """Run consecutive committed epochs; entries never represent wall-clock gaps."""

    rate = p.initial_rate
    rows = []
    for epoch, acquisitions in enumerate(epochs):
        signal = signal_for(acquisitions, p)
        old_rate = rate
        rate = apply_signal(rate, signal, p)
        rows.append(
            {
                "epoch": epoch,
                "direction": signal.direction,
                "effective_step_bps": signal.effective_step_bps,
                "old_rate": old_rate,
                "new_rate": rate,
                "price_index_bps": price_index_bps(rate, p.initial_rate),
            }
        )
    return {
        "name": name,
        "epochs": rows,
        "final_rate": rate,
        "final_price_index_bps": price_index_bps(rate, p.initial_rate),
        "min_price_index_bps": min(row["price_index_bps"] for row in rows),
        "max_price_index_bps": max(row["price_index_bps"] for row in rows),
    }


def valid_override(target_rate: int, p: Params) -> bool:
    return p.min_rate <= target_rate <= p.rate_ceiling


def install_override(
    state: OverrideState,
    *,
    target_rate: int,
    target_epoch: int,
    p: Params,
) -> OverrideState:
    assert not state.exists
    assert valid_override(target_rate, p)
    assert target_epoch >= 0
    return OverrideState(target_rate=target_rate, target_epoch=target_epoch)


def project_installed_override(
    state: OverrideState,
    *,
    projected_epoch: int,
    controller_rate: int,
    p: Params,
) -> OverrideProjection:
    assert projected_epoch >= 0
    assert p.min_rate <= controller_rate <= p.rate_ceiling
    if not state.exists:
        return OverrideProjection("none", controller_rate, controller_rate)
    if projected_epoch < state.target_epoch:
        return OverrideProjection("pending", controller_rate, controller_rate)
    if projected_epoch == state.target_epoch:
        return OverrideProjection("apply", controller_rate, state.target_rate)
    return OverrideProjection("missed", controller_rate, controller_rate)


def commit_override(
    state: OverrideState,
    *,
    projected_epoch: int,
    controller_rate: int,
    successful: bool,
    p: Params,
) -> tuple[OverrideProjection, OverrideState]:
    projection = project_installed_override(
        state,
        projected_epoch=projected_epoch,
        controller_rate=controller_rate,
        p=p,
    )
    if not successful or projection.status not in ("apply", "missed"):
        return projection, state
    return projection, OverrideState()


def cancel_override(state: OverrideState) -> OverrideState:
    assert state.exists
    return OverrideState()


def invalidate_override_for_config_change(
    state: OverrideState,
) -> OverrideState:
    if not state.exists:
        return state
    return OverrideState()


def project_next_rollover_override(
    target_rate: int,
    target_epoch: int,
    projected_epoch: int,
    controller_rate: int,
    p: Params,
) -> tuple[str, int | None]:
    """Stateless arithmetic helper retained for compact scenario tables."""

    assert target_epoch >= 0 and projected_epoch >= 0
    assert p.min_rate <= controller_rate <= p.rate_ceiling
    if not valid_override(target_rate, p):
        return "reject", None
    if projected_epoch < target_epoch:
        return "pending", controller_rate
    if projected_epoch == target_epoch:
        return "apply", target_rate
    return "missed", controller_rate


def override_state_dict(state: OverrideState) -> dict:
    return {**asdict(state), "exists": state.exists}


def override_lifecycle_evidence(p: Params) -> dict:
    """Exercise the named-epoch state machine without EVM authorization."""

    empty = OverrideState()
    installed = install_override(
        empty,
        target_rate=925_000_000_000_000_000,
        target_epoch=5,
        p=p,
    )
    assert installed.exists

    earlier_epoch = project_installed_override(
        installed,
        projected_epoch=4,
        controller_rate=880_000_000_000_000_000,
        p=p,
    )
    target_epoch = project_installed_override(
        installed,
        projected_epoch=5,
        controller_rate=880_000_000_000_000_000,
        p=p,
    )
    later_epoch = project_installed_override(
        installed,
        projected_epoch=8,
        controller_rate=880_000_000_000_000_000,
        p=p,
    )
    assert earlier_epoch.status == "pending"
    assert target_epoch.status == "apply"
    assert target_epoch.final_rate == installed.target_rate
    assert later_epoch.status == "missed"
    assert later_epoch.final_rate == 880_000_000_000_000_000
    assert project_installed_override(
        installed,
        projected_epoch=5,
        controller_rate=880_000_000_000_000_000,
        p=p,
    ) == target_epoch

    failed_projection, after_failure = commit_override(
        installed,
        projected_epoch=5,
        controller_rate=880_000_000_000_000_000,
        successful=False,
        p=p,
    )
    assert failed_projection == target_epoch and after_failure == installed
    applied_projection, consumed = commit_override(
        installed,
        projected_epoch=5,
        controller_rate=880_000_000_000_000_000,
        successful=True,
        p=p,
    )
    assert applied_projection == target_epoch
    assert consumed == OverrideState()

    missed_projection, cleared_as_missed = commit_override(
        installed,
        projected_epoch=8,
        controller_rate=880_000_000_000_000_000,
        successful=True,
        p=p,
    )
    assert missed_projection == later_epoch
    assert cleared_as_missed == OverrideState()

    cancelled = cancel_override(installed)
    invalidated = invalidate_override_for_config_change(
        installed,
    )
    assert cancelled == OverrideState()
    assert invalidated == OverrideState()

    return {
        "status": "pass",
        "scope": "pure named-epoch lifecycle; not EVM authorization",
        "initial_state": override_state_dict(empty),
        "installed_state": override_state_dict(installed),
        "earlier_epoch_projection": asdict(earlier_epoch),
        "target_epoch_projection": asdict(target_epoch),
        "later_epoch_projection": asdict(later_epoch),
        "failed_commit_state": override_state_dict(after_failure),
        "consumed_state": override_state_dict(consumed),
        "missed_state": override_state_dict(cleared_as_missed),
        "cancelled_state": override_state_dict(cancelled),
        "config_invalidated_state": override_state_dict(invalidated),
        "repeat_preview": "pass",
        "failed_commit_preserves_state": "pass",
        "successful_commit_consumes_once": "pass",
        "earlier_epochs_preserve_target": "pass",
        "later_epoch_clears_missed_target": "pass",
        "config_invalidation": "pass",
        "installed_cancellation": "pass",
    }


def epochs_to_price_multiple(step_bps: int, numerator: int, denominator: int) -> int:
    rate = RATE_SCALE
    epochs = 0
    while price_index_bps(rate) * denominator < BPS * numerator:
        rate = max(rate * BPS // (BPS + step_bps), 1)
        epochs += 1
        assert epochs < 100_000
    return epochs


def epochs_to_half_price(step_bps: int) -> int:
    rate = RATE_SCALE
    epochs = 0
    while price_index_bps(rate) > BPS // 2:
        rate = rate * BPS // (BPS - step_bps)
        epochs += 1
        assert epochs < 100_000
    return epochs


def revision_19_positive_transition(
    rate: int,
    utilization: int,
    elapsed: int,
    old_up: int,
    old_down: int,
    p: Params,
) -> tuple[str, int, int]:
    assert elapsed > 0
    if utilization >= p.u_high_bps:
        direction, step = "up", old_up
    elif utilization <= p.u_low_bps:
        direction, step = "down", old_down
    else:
        direction, step = "hold", 0
    signal = Signal(
        0,
        utilization,
        0,
        0,
        True,
        0,
        0,
        0,
        direction,
        step,
    )
    transitioned_rate = apply_signal(rate, signal, p)
    return direction, step, apply_decay(transitioned_rate, elapsed - 1, p)


def mechanism_checks(p: Params) -> dict:
    validate_params(p)

    full_first = signal_for(((0, p.payment_cap),), p)
    full_mid = signal_for((((p.epoch_length - 1) // 2, p.payment_cap),), p)
    full_last = signal_for(((p.epoch_length - 1, p.payment_cap),), p)
    assert full_first.effective_step_bps == p.max_up_bps
    assert full_mid.effective_step_bps == (p.min_up_bps + p.max_up_bps) // 2
    assert full_last.effective_step_bps == p.min_up_bps

    one_block = Params(**{**asdict(p), "epoch_length": 1})
    assert signal_for(((0, one_block.payment_cap),), one_block).effective_step_bps == (
        one_block.max_up_bps
    )
    even_length = Params(**{**asdict(p), "epoch_length": 100})
    assert signal_for(((0, even_length.payment_cap),), even_length).effective_step_bps == (
        even_length.max_up_bps
    )
    assert signal_for(
        ((even_length.epoch_length - 1, even_length.payment_cap),),
        even_length,
    ).effective_step_bps == even_length.min_up_bps
    assert signal_for(
        ((0, p.payment_cap),),
        p,
        timing_eligible=False,
    ).effective_step_bps == p.min_up_bps

    split = signal_for(((50, p.payment_cap // 2), (50, p.payment_cap // 2)), p)
    merged = signal_for(((50, p.payment_cap),), p)
    assert split == merged
    assert signal_for(tuple(reversed(((0, 9_900), (100, 100)))), p) == signal_for(
        ((0, 9_900), (100, 100)), p
    )

    timing_monotonic_rows = 0
    for utilization in range(p.u_high_bps, BPS + 1, 10):
        previous = None
        amount = utilization * p.payment_cap // BPS
        for offset in range(p.epoch_length):
            step = signal_for(((offset, amount),), p).effective_step_bps
            if previous is not None:
                assert step <= previous
            previous = step
            timing_monotonic_rows += 1

    utilization_monotonic_rows = 0
    for offset in range(p.epoch_length):
        previous = None
        for utilization in range(p.u_high_bps, BPS + 1, 10):
            amount = utilization * p.payment_cap // BPS
            step = signal_for(((offset, amount),), p).effective_step_bps
            if previous is not None:
                assert step >= previous
            previous = step
            utilization_monotonic_rows += 1

    down_monotonic_rows = 0
    previous = None
    minimum_utilization = p.min_payment_amount * BPS // p.payment_cap
    for utilization in range(minimum_utilization, p.u_low_bps + 1):
        amount = max(
            p.min_payment_amount,
            utilization * p.payment_cap // BPS,
        )
        step = signal_for(((0, amount),), p).effective_step_bps
        if previous is not None:
            assert step <= previous
        previous = step
        down_monotonic_rows += 1

    collapsed = Params(
        **{
            **asdict(p),
            "min_up_bps": 400,
            "max_up_bps": 400,
            "min_down_bps": 150,
            "max_down_bps": 150,
        }
    )
    collapsed_mismatches = 0
    collapsed_rows = 0
    for utilization in range(minimum_utilization, BPS + 1):
        amount = max(
            collapsed.min_payment_amount,
            utilization * collapsed.payment_cap // BPS,
        )
        for offset in (0, 25, 50, 75, 100):
            signal = signal_for(((offset, amount),), collapsed)
            for rate in (
                collapsed.min_rate,
                collapsed.initial_rate,
                collapsed.rate_ceiling + 1,
            ):
                for elapsed in (1, 2, collapsed.max_decay_epochs + 1):
                    old_direction, old_step, old_rate = revision_19_positive_transition(
                        rate,
                        signal.utilization_bps,
                        elapsed,
                        400,
                        150,
                        collapsed,
                    )
                    new_rate = apply_decay(
                        apply_signal(rate, signal, collapsed),
                        elapsed - 1,
                        collapsed,
                    )
                    if (
                        signal.direction,
                        signal.effective_step_bps,
                        new_rate,
                    ) != (old_direction, old_step, old_rate):
                        collapsed_mismatches += 1
                    collapsed_rows += 1
    assert collapsed_mismatches == 0

    rate = p.initial_rate
    min_up_signal = Signal(
        0,
        p.u_high_bps,
        0,
        0,
        True,
        0,
        0,
        0,
        "up",
        p.min_up_bps,
    )
    max_down_signal = Signal(
        0,
        0,
        0,
        0,
        True,
        0,
        0,
        BPS,
        "down",
        p.max_down_bps,
    )
    rate = apply_signal(rate, min_up_signal, p)
    rate = apply_signal(rate, max_down_signal, p)
    assert rate <= p.initial_rate
    min_up_then_decay_rate = apply_signal(p.initial_rate, min_up_signal, p)
    min_up_then_decay_rate = apply_decay(min_up_then_decay_rate, 1, p)
    assert min_up_then_decay_rate <= p.initial_rate
    floor_bound_rate = apply_signal(p.min_rate, min_up_signal, p)
    floor_bound_rate = apply_signal(floor_bound_rate, max_down_signal, p)
    assert floor_bound_rate > p.min_rate

    full_signal = signal_for(((0, p.payment_cap),), p)
    assert apply_signal(p.min_rate, full_signal, p) == p.min_rate
    lowered_ceiling = Params(
        **{
            **asdict(p),
            "initial_rate": p.initial_rate // 2,
            "rate_ceiling": p.initial_rate // 2,
        }
    )
    expected_bounded_up = (
        lowered_ceiling.rate_ceiling
        * BPS
        // (BPS + lowered_ceiling.max_up_bps)
    )
    assert apply_signal(p.initial_rate, full_signal, lowered_ceiling) == (
        expected_bounded_up
    )
    assert apply_decay(p.initial_rate, p.max_decay_epochs, p) == apply_decay(
        p.initial_rate,
        p.max_decay_epochs + 10,
        p,
    )

    return {
        "status": "pass",
        "endpoint_and_epoch_length_checks": 7,
        "split_merge_and_order_checks": 2,
        "timing_monotonic_rows": timing_monotonic_rows,
        "utilization_monotonic_rows": utilization_monotonic_rows,
        "down_monotonic_rows": down_monotonic_rows,
        "conditional_collapsed_transition_rows": collapsed_rows,
        "conditional_collapsed_transition_mismatches": collapsed_mismatches,
        "floor_ceiling_and_decay_cap_checks": 3,
        "unclamped_round_trip_factor_check": "pass",
        "unclamped_min_up_then_decay_factor_check": "pass",
        "rate_bound_exception_check": "pass",
    }


def build_artifact(repo_root: Path = REPO_ROOT) -> dict:
    p = Params()
    validate_params(p)

    single = [
        scenario("full_first_block", ((0, 10_000),), p),
        scenario("full_midpoint", ((50, 10_000),), p),
        scenario("full_last_block", ((100, 10_000),), p),
        scenario("full_uniform_two_tranches", ((0, 5_000), (100, 5_000)), p),
        scenario("ninety_percent_first_block", ((0, 9_000),), p),
        scenario("ninety_nine_early_one_late", ((0, 9_900), (100, 100)), p),
        scenario("one_early_ninety_nine_late", ((0, 100), (100, 9_900)), p),
        scenario("exact_high_threshold_first_block", ((0, 8_000),), p),
        scenario(
            "first_partial_epoch_timing_ineligible",
            ((0, 10_000),),
            p,
            timing_eligible=False,
        ),
        scenario("dead_band_midpoint", ((0, 5_000),), p),
        scenario("exact_low_threshold", ((0, 2_000),), p),
        scenario("half_low_threshold", ((0, 1_000),), p),
        scenario(
            "minimum_reachable_positive",
            ((0, p.min_payment_amount),),
            p,
        ),
        scenario("empty_epoch_decay", (), p),
    ]

    fast = ((0, 10_000),)
    mid = ((50, 10_000),)
    late = ((100, 10_000),)
    empty: tuple[Acquisition, ...] = ()
    paths = [
        run_committed_epoch_path("repeated_fast_full", [fast] * 32, p),
        run_committed_epoch_path("repeated_mid_full", [mid] * 32, p),
        run_committed_epoch_path("repeated_late_full", [late] * 32, p),
        run_committed_epoch_path(
            "alternating_fast_full_and_empty", [fast, empty] * 16, p
        ),
        run_committed_epoch_path(
            "alternating_late_full_and_empty", [late, empty] * 16, p
        ),
    ]

    override_cases = []
    for name, target_rate, target_epoch, projected_epoch in (
        ("earlier_epoch_pending", 925_000_000_000_000_000, 5, 4),
        ("target_epoch_exact", 925_000_000_000_000_000, 5, 5),
        ("later_epoch_missed", 925_000_000_000_000_000, 5, 8),
        ("invalid_below_floor", 9_999, 5, 5),
        ("invalid_above_ceiling", p.rate_ceiling + 1, 5, 5),
    ):
        status, final_rate = project_next_rollover_override(
            target_rate,
            target_epoch,
            projected_epoch,
            880_000_000_000_000_000,
            p,
        )
        override_cases.append(
            {
                "name": name,
                "target_rate": target_rate,
                "target_epoch": target_epoch,
                "projected_epoch": projected_epoch,
                "counterfactual_controller_rate": 880_000_000_000_000_000,
                "status": status,
                "final_rate": final_rate,
            }
        )

    catch_up = {
        timing: {
            "+30%": epochs_to_price_multiple(step, 13, 10),
            "2x": epochs_to_price_multiple(step, 2, 1),
            "10x": epochs_to_price_multiple(step, 10, 1),
        }
        for timing, step in (
            ("fast", p.max_up_bps),
            ("mid", (p.min_up_bps + p.max_up_bps) // 2),
            ("late", p.min_up_bps),
        )
    }
    half_life = {
        "at_uLow": epochs_to_half_price(p.min_down_bps),
        "half_uLow": epochs_to_half_price(
            (p.min_down_bps + p.max_down_bps) // 2
        ),
        "minimum_reachable_positive": epochs_to_half_price(
            signal_for(((0, p.min_payment_amount),), p).effective_step_bps
        ),
        "max_configured_down_bound": epochs_to_half_price(p.max_down_bps),
        "empty": epochs_to_half_price(p.decay_bps),
    }

    checks = mechanism_checks(p)
    lifecycle = override_lifecycle_evidence(p)
    alternating = next(
        path for path in paths if path["name"] == "alternating_fast_full_and_empty"
    )
    repeated_fast = next(
        path for path in paths if path["name"] == "repeated_fast_full"
    )
    alternating_late = next(
        path for path in paths if path["name"] == "alternating_late_full_and_empty"
    )
    artifact = {
        "schema": SCHEMA,
        "status": STATUS,
        "authority": (
            "implemented mechanism evidence; not calibration, deployment, "
            "or integration authority"
        ),
        "bound_implementation": bound_implementation(repo_root),
        "calibration_status": "not_approved",
        "arithmetic": "uint256-style floor integer model; no floats",
        "fixture": asdict(p),
        "formula": {
            "preclamp": "boundedOldRate=min(oldRate,newBaseRateCeiling)",
            "up": (
                "utilStrength=(U-uHigh)*10000//(10000-uHigh); "
                "demandStrength=utilStrength*earliness//10000; "
                "step=minUp+(maxUp-minUp)*demandStrength//10000"
            ),
            "down": (
                "weakness=(uLow-U)*10000//uLow; "
                "step=minDown+(maxDown-minDown)*weakness//10000"
            ),
            "decay": "fixed decayBps per skipped epoch, capped by maxDecayEpochs",
            "price_up_rate": (
                "max(boundedOldRate*10000//(10000+effectiveUp),minRate)"
            ),
            "price_down_rate": (
                "min(boundedOldRate*10000//(10000-effectiveDown),rateCeiling)"
            ),
            "override": (
                "earlier epochs leave the named target pending; the target epoch "
                "uses the exact rate; a later epoch clears the override as missed"
            ),
        },
        "single_epoch_scenarios": single,
        "path_scenarios": paths,
        "manual_override_scenarios": override_cases,
        "manual_override_lifecycle": lifecycle,
        "economic_metrics": {
            "catch_up_epochs": catch_up,
            "price_down_half_life_epochs": half_life,
            "alternating_path_warning": {
                "fast_full_then_empty_pair_price_multiplier_bps": alternating[
                    "epochs"
                ][1]["price_index_bps"],
                "alternating_16_pairs_final_price_index_bps": alternating[
                    "final_price_index_bps"
                ],
                "late_full_then_empty_pair_price_multiplier_bps": alternating_late[
                    "epochs"
                ][1]["price_index_bps"],
                "alternating_late_16_pairs_final_price_index_bps": (
                    alternating_late["final_price_index_bps"]
                ),
                "repeated_fast_full_32_epochs_final_price_index_bps": repeated_fast[
                    "final_price_index_bps"
                ],
                "interpretation": (
                    "With 1.5% empty decay, both the illustrative 8% fast-up "
                    "and 2% late-up alternating paths retain a net upward price "
                    "response, as required by config validation; neither path "
                    "is calibrated or approved."
                ),
            },
            "parameter_acceptance_thresholds": "owner_not_pinned",
        },
        "mechanism_checks": checks,
        "implementation_boundaries": [
            "Vyper must bound or safely decompose offset*10000",
            "first partially exposed initialized epoch is timing-ineligible",
            "pause and disable intervals remain wall-clock time",
            "manual target is immediate, one-shot, and bound to one resolved epoch",
        ],
    }
    return artifact


def canonical_bytes(artifact: dict) -> bytes:
    return (
        json.dumps(
            artifact,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write", type=Path)
    action.add_argument("--check", type=Path)
    action.add_argument("--sha256", action="store_true")
    args = parser.parse_args()

    payload = canonical_bytes(build_artifact())
    if args.write:
        args.write.write_bytes(payload)
        print(f"wrote {args.write} ({len(payload)} bytes)")
        return 0
    if args.check:
        actual = args.check.read_bytes()
        if actual != payload:
            print(f"simulation artifact is stale: {args.check}")
            return 1
        print(f"simulation artifact is current: {args.check}")
        return 0
    if args.sha256:
        print(hashlib.sha256(payload).hexdigest())
        return 0

    print(json.dumps(build_artifact(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
