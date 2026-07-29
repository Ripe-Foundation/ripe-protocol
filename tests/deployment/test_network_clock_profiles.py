"""H-04 parameter behavior across the eight approved dual-clock profiles."""

from __future__ import annotations

import pytest

from utils.clock_profiles import (
    DEFAULT_NUMBER,
    DEFAULT_TIMESTAMP,
    ClockPoint,
    clock_profile,
)


N = DEFAULT_NUMBER
T = DEFAULT_TIMESTAMP
EXPIRATION = 50_400
AUCTION_DURATION = 7_200
BORROW_INTERVAL = 7_200
GOVERNANCE_LOCK = 7_200
BOND_EPOCH = 2_400


def _can_confirm(number: int, confirm: int, expiration: int) -> bool:
    return confirm != 0 and number >= confirm and number < expiration


def _in_auction(number: int, start: int, duration: int) -> bool:
    return start <= number < start + duration


def _available_in_interval(
    number: int,
    start: int,
    duration: int,
    maximum: int,
    remaining: int,
) -> tuple[int, int]:
    if start != 0 and start + duration > number:
        return remaining, start
    return maximum, number


def _latest_epoch(
    number: int,
    start: int,
    end: int,
    duration: int,
) -> tuple[int, int]:
    if number < end:
        return start, end
    if number < end + duration:
        return end, end + duration
    ahead = (number - end) // duration
    next_start = (duration * ahead) + end
    return next_start, next_start + duration


def test_b_ord_strict_before_equality_after_boundaries():
    profile = clock_profile("B-ORD", number=N - 1, timestamp=T)
    numbers = [point.number for point in profile.points]
    assert numbers == [N - 1, N, N + 1, N + 2, N + 3]
    assert [_can_confirm(number, N, N + 2) for number in numbers] == [
        False,
        True,
        True,
        False,
        False,
    ]
    assert [_in_auction(number, N, 2) for number in numbers] == [
        False,
        True,
        True,
        False,
        False,
    ]


def test_r_rep128_repeated_numbers_never_create_block_progress():
    profile = clock_profile("R-REP128")
    assert len(profile.points) == 128
    assert {point.number for point in profile.points} == {N}
    assert profile.points[-1].timestamp > profile.points[0].timestamp
    assert all(
        not _can_confirm(point.number, N + 1, N + EXPIRATION)
        for point in profile.points
    )
    assert all(
        _in_auction(point.number, N, AUCTION_DURATION)
        for point in profile.points
    )


def test_r_plus1_repeats_then_advances_without_timestamp_carry():
    profile = clock_profile("R-PLUS1")
    assert [(p.number, p.timestamp) for p in profile.points] == [
        (N, T),
        (N, T + 1),
        (N + 1, T + 12),
        (N + 1, T + 13),
    ]
    assert [p.number >= N + 1 for p in profile.points] == [
        False,
        False,
        True,
        True,
    ]
    assert profile.points[2].timestamp - profile.points[1].timestamp == 11


def test_r_j2_j4_skips_openings_and_preserves_half_open_windows():
    profile = clock_profile("R-J2-J4")
    assert [point.number - N for point in profile.points] == [0, 0, 2, 2, 4]
    assert N + 1 not in {point.number for point in profile.points}
    start = N + 2
    end = N + 4
    assert [_in_auction(point.number, start, end - start) for point in profile.points] == [
        False,
        False,
        True,
        True,
        False,
    ]


def test_boundary_open_profile_proves_before_and_after_can_skip_equality():
    boundary = N + 20
    profile = clock_profile("BOUNDARY-OPEN", boundary=boundary)
    assert profile.points == (
        ClockPoint(boundary - 1, T),
        ClockPoint(boundary + 1, T + 24),
    )
    assert boundary not in {point.number for point in profile.points}
    assert [point.number >= boundary for point in profile.points] == [
        False,
        True,
    ]


def test_boundary_window_profile_can_skip_the_whole_window():
    start = N + 20
    end = start + 61
    profile = clock_profile("BOUNDARY-WINDOW", start=start, end=end)
    assert profile.points == (
        ClockPoint(start - 1, T),
        ClockPoint(end + 1, T + 24),
    )
    assert all(
        not _in_auction(point.number, start, end - start)
        for point in profile.points
    )
    assert end - start >= 61


def test_r_stress60_expiration_and_interval_refill_have_no_carry():
    profile = clock_profile("R-STRESS60")
    start = N
    maximum = 10_000
    remaining = 7
    before = _available_in_interval(
        profile.points[1].number,
        start,
        60,
        maximum,
        remaining,
    )
    after = _available_in_interval(
        profile.points[2].number,
        start,
        60,
        maximum,
        remaining,
    )
    assert before == (remaining, start)
    assert after == (maximum, N + 60)
    assert after[0] == maximum
    assert _can_confirm(N + 60, N, N + 61)
    assert not _can_confirm(N + 61, N, N + 61)


def test_mixed_profile_proves_strict_seconds_and_block_separation():
    profile = clock_profile("MIXED")
    assert profile.points[0].number == profile.points[1].number
    assert profile.points[1].timestamp - profile.points[0].timestamp == 3_600
    assert profile.points[2].number - profile.points[1].number == 2
    assert profile.points[2].timestamp == profile.points[1].timestamp
    assert profile.points[3].number == profile.points[2].number
    assert profile.points[3].timestamp - profile.points[2].timestamp == 3_600
    assert not _can_confirm(profile.points[1].number, N + 1, N + 10)
    assert profile.points[1].timestamp >= T + 3_600


@pytest.mark.parametrize(
    ("base_blocks", "robinhood_blocks"),
    [(0, 0), (1, 1), (6, 1), (7, 2), (43_200, 7_200), (14_400, 2_400)],
)
def test_conversion_preserves_zero_uses_ceil_and_has_nonzero_minimum(
    base_blocks,
    robinhood_blocks,
):
    converted = 0 if base_blocks == 0 else max(1, (base_blocks + 5) // 6)
    assert converted == robinhood_blocks


@pytest.mark.parametrize(
    "profile",
    [
        clock_profile("B-ORD"),
        clock_profile("R-REP128"),
        clock_profile("R-PLUS1"),
        clock_profile("R-J2-J4"),
        clock_profile("BOUNDARY-OPEN", boundary=N + 20),
        clock_profile("BOUNDARY-WINDOW", start=N + 20, end=N + 81),
        clock_profile("R-STRESS60"),
        clock_profile("MIXED"),
    ],
    ids=lambda profile: profile.name,
)
def test_absolute_block_heights_are_never_duration_converted(profile):
    assert all(point.number >= N for point in profile.points)
    assert profile.points[0].number != profile.points[0].number // 6


def test_approved_expirations_exceed_stress_jump_and_governance_lock():
    assert EXPIRATION >= 61
    assert EXPIRATION > GOVERNANCE_LOCK
    profile = clock_profile("R-STRESS60")
    confirm = profile.points[0].number + GOVERNANCE_LOCK
    expiration = profile.points[0].number + EXPIRATION
    assert profile.points[-1].number < confirm < expiration


def test_auction_and_interval_values_remain_block_domain():
    profile = clock_profile("MIXED")
    assert all(
        _in_auction(point.number, N, AUCTION_DURATION)
        for point in profile.points
    )
    assert all(
        _available_in_interval(
            point.number,
            N,
            BORROW_INTERVAL,
            10_000,
            1,
        )
        == (1, N)
        for point in profile.points
    )


def test_bond_epochs_follow_absolute_number_jumps_not_elapsed_seconds():
    start = N
    end = start + BOND_EPOCH
    mixed = clock_profile("MIXED")
    assert all(
        _latest_epoch(point.number, start, end, BOND_EPOCH) == (start, end)
        for point in mixed.points
    )
    far = end + BOND_EPOCH + 17
    assert _latest_epoch(far, start, end, BOND_EPOCH) == (
        end + BOND_EPOCH,
        end + (2 * BOND_EPOCH),
    )
