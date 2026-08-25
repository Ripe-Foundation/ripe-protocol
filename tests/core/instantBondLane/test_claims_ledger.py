import boa

from conf_utils import filter_logs
from constants import INSTANT_BOND_LANE_HQ_ID, MAX_UINT256, ZERO_ADDRESS
from tests.core.instantBondLane.conftest import travel_blocks


def create_position(ctx, payout, vesting_length, user=None):
    user = ctx.bob if user is None else user
    return ctx.claims.createVestingPosition(
        user,
        payout,
        vesting_length,
        sender=ctx.lane.address,
    )


def test_claims_constructor_and_department_flags(lane_env):
    claims = lane_env.claims
    assert claims.getRipeHq() == lane_env.ripe_hq.address
    assert claims.canMintGreen() is False
    assert claims.canMintRipe() is False
    assert claims.nextPositionId() == 1
    assert claims.totalAllocatedRipe() == 0
    assert claims.totalClaimedRipe() == 0
    assert claims.totalOutstandingRipe() == 0
    assert claims.getNumUserPositions(lane_env.bob) == 0
    assert claims.canRetire() is False


def test_budget_setter_is_switchboard_gated_and_resettable(lane_env, alice):
    claims = lane_env.claims
    with boa.reverts("no perms"):
        claims.setRemainingAllocationBudget(123, sender=alice)

    claims.setRemainingAllocationBudget(123, sender=lane_env.switchboard.address)
    assert filter_logs(claims, "RemainingAllocationBudgetSet")[-1].amount == 123
    claims.setRemainingAllocationBudget(0, sender=lane_env.switchboard.address)
    assert filter_logs(claims, "RemainingAllocationBudgetSet")[-1].amount == 0
    assert claims.remainingAllocationBudget() == 0


def test_position_creation_validates_lane_user_payout_budget_and_overflow(
    lane_env, alice
):
    claims = lane_env.claims
    with boa.reverts("invalid lane"):
        claims.createVestingPosition(alice, 1, 1, sender=alice)
    with boa.reverts("invalid user"):
        claims.createVestingPosition(
            ZERO_ADDRESS,
            1,
            1,
            sender=lane_env.lane.address,
        )
    with boa.reverts("invalid payout"):
        claims.createVestingPosition(
            alice,
            0,
            1,
            sender=lane_env.lane.address,
        )

    lane_env.set_budget(9)
    with boa.reverts("allocation budget"):
        claims.createVestingPosition(
            alice,
            10,
            1,
            sender=lane_env.lane.address,
        )

    lane_env.set_budget(MAX_UINT256)
    with boa.reverts("maturity overflow"):
        claims.createVestingPosition(
            alice,
            1,
            MAX_UINT256,
            sender=lane_env.lane.address,
        )


def test_create_position_stores_exact_terms_and_decrements_budget(lane_env):
    payout = 12_345
    length = 77
    budget_before = lane_env.claims.remainingAllocationBudget()
    creation_block = boa.env.evm.patch.block_number

    position_id = create_position(lane_env, payout, length)
    event = filter_logs(lane_env.claims, "VestingPositionCreated")[-1]
    position = lane_env.claims.positions(lane_env.bob, 1)

    assert position_id == 1
    assert tuple(position) == (
        position_id,
        payout,
        0,
        creation_block,
        creation_block + length,
    )
    assert lane_env.claims.indexOfPosition(lane_env.bob, position_id) == 1
    assert lane_env.claims.getNumUserPositions(lane_env.bob) == 1
    assert lane_env.claims.nextPositionId() == 2
    assert lane_env.claims.remainingAllocationBudget() == budget_before - payout
    assert lane_env.claims.totalAllocatedRipe() == payout
    assert lane_env.claims.totalClaimedRipe() == 0
    assert lane_env.claims.totalOutstandingRipe() == payout
    assert event.user == lane_env.bob
    assert event.positionId == position_id
    assert event.sourceLane == lane_env.lane.address
    assert event.ripePayout == payout
    assert event.creationBlock == creation_block
    assert event.maturityBlock == creation_block + length


def test_position_ids_are_global_while_indices_are_per_user(lane_env, alice):
    first = create_position(lane_env, 10, 5, lane_env.bob)
    second = create_position(lane_env, 20, 5, alice)
    third = create_position(lane_env, 30, 5, lane_env.bob)

    assert (first, second, third) == (1, 2, 3)
    assert lane_env.claims.indexOfPosition(lane_env.bob, first) == 1
    assert lane_env.claims.indexOfPosition(lane_env.bob, third) == 2
    assert lane_env.claims.indexOfPosition(alice, second) == 1
    assert lane_env.claims.getNumUserPositions(lane_env.bob) == 2
    assert lane_env.claims.getNumUserPositions(alice) == 1


def test_linear_vesting_boundaries_and_floor_rounding(lane_env):
    payout = 101
    position_id = create_position(lane_env, payout, 10)
    assert lane_env.claims.getVestedRipe(lane_env.bob, position_id) == 0
    assert lane_env.claims.getClaimableRipe(lane_env.bob, position_id) == 0

    travel_blocks(1)
    assert lane_env.claims.getVestedRipe(lane_env.bob, position_id) == 10
    travel_blocks(4)
    assert lane_env.claims.getVestedRipe(lane_env.bob, position_id) == 50
    travel_blocks(4)
    assert lane_env.claims.getVestedRipe(lane_env.bob, position_id) == 90
    travel_blocks(1)
    assert lane_env.claims.getVestedRipe(lane_env.bob, position_id) == payout
    assert lane_env.claims.getClaimableRipe(lane_env.bob, position_id) == payout


def test_zero_length_position_vests_after_creation_block(lane_env):
    position_id = create_position(lane_env, 99, 0)
    position = lane_env.claims.positions(lane_env.bob, 1)
    assert position.creationBlock == position.maturityBlock
    assert lane_env.claims.getVestedRipe(lane_env.bob, position_id) == 0
    travel_blocks(1)
    assert lane_env.claims.getVestedRipe(lane_env.bob, position_id) == 99


def test_full_precision_vesting_handles_512_bit_intermediate(lane_env):
    lane_env.set_budget(MAX_UINT256)
    position_id = create_position(lane_env, MAX_UINT256, 10)
    travel_blocks(5)
    expected = MAX_UINT256 * 5 // 10
    assert lane_env.claims.getVestedRipe(lane_env.bob, position_id) == expected


def test_partial_claim_updates_position_totals_and_event_without_refilling_budget(
    lane_env
):
    payout = 1_000
    position_id = create_position(lane_env, payout, 10)
    budget_after_allocation = lane_env.claims.remainingAllocationBudget()
    travel_blocks(4)

    claimed, total_for_position, ripe_payout = lane_env.claims.recordClaim(
        lane_env.bob,
        position_id,
        sender=lane_env.lane.address,
    )
    event = filter_logs(lane_env.claims, "ClaimRecorded")[-1]
    position = lane_env.claims.positions(lane_env.bob, 1)

    assert (claimed, total_for_position, ripe_payout) == (400, 400, payout)
    assert position.ripeClaimed == 400
    assert lane_env.claims.getClaimableRipe(lane_env.bob, position_id) == 0
    assert lane_env.claims.totalClaimedRipe() == 400
    assert lane_env.claims.totalOutstandingRipe() == 600
    assert lane_env.claims.remainingAllocationBudget() == budget_after_allocation
    assert event.user == lane_env.bob
    assert event.positionId == position_id
    assert event.amountClaimed == 400
    assert event.totalClaimedForPosition == 400
    assert event.ripePayout == payout
    assert event.fullyClaimed is False

    with boa.reverts("nothing to claim"):
        lane_env.claims.recordClaim(
            lane_env.bob,
            position_id,
            sender=lane_env.lane.address,
        )


def test_full_claim_removes_position_and_preserves_monotonic_totals(lane_env):
    position_id = create_position(lane_env, 777, 3)
    travel_blocks(3)
    assert lane_env.claims.recordClaim(
        lane_env.bob,
        position_id,
        sender=lane_env.lane.address,
    ) == (777, 777, 777)

    event = filter_logs(lane_env.claims, "ClaimRecorded")[-1]
    assert event.fullyClaimed is True
    assert lane_env.claims.getNumUserPositions(lane_env.bob) == 0
    assert lane_env.claims.indexOfPosition(lane_env.bob, position_id) == 0
    assert tuple(lane_env.claims.positions(lane_env.bob, 1)) == (0, 0, 0, 0, 0)
    assert lane_env.claims.getVestedRipe(lane_env.bob, position_id) == 0
    assert lane_env.claims.getClaimableRipe(lane_env.bob, position_id) == 0
    assert lane_env.claims.totalAllocatedRipe() == 777
    assert lane_env.claims.totalClaimedRipe() == 777
    assert lane_env.claims.totalOutstandingRipe() == 0


def test_swap_and_pop_compacts_positions_and_reuses_tail_index(lane_env):
    first = create_position(lane_env, 10, 1)
    middle = create_position(lane_env, 20, 1)
    last = create_position(lane_env, 30, 1)
    travel_blocks(1)

    lane_env.claims.recordClaim(
        lane_env.bob,
        middle,
        sender=lane_env.lane.address,
    )
    assert lane_env.claims.getNumUserPositions(lane_env.bob) == 2
    assert lane_env.claims.indexOfPosition(lane_env.bob, first) == 1
    assert lane_env.claims.indexOfPosition(lane_env.bob, middle) == 0
    assert lane_env.claims.indexOfPosition(lane_env.bob, last) == 2
    assert lane_env.claims.positions(lane_env.bob, 2).id == last
    assert tuple(lane_env.claims.positions(lane_env.bob, 3)) == (0, 0, 0, 0, 0)

    new_position = create_position(lane_env, 40, 1)
    assert new_position == 4
    assert lane_env.claims.indexOfPosition(lane_env.bob, new_position) == 3
    assert lane_env.claims.positions(lane_env.bob, 3).id == new_position


def test_record_claim_validates_lane_user_position_and_pause(lane_env, alice):
    position_id = create_position(lane_env, 100, 1)
    travel_blocks(1)
    with boa.reverts("invalid lane"):
        lane_env.claims.recordClaim(lane_env.bob, position_id, sender=alice)
    with boa.reverts("invalid user"):
        lane_env.claims.recordClaim(
            ZERO_ADDRESS,
            position_id,
            sender=lane_env.lane.address,
        )
    with boa.reverts("invalid position"):
        lane_env.claims.recordClaim(
            lane_env.bob,
            position_id + 1,
            sender=lane_env.lane.address,
        )

    lane_env.claims.pause(True, sender=lane_env.switchboard.address)
    with boa.reverts("paused"):
        lane_env.claims.recordClaim(
            lane_env.bob,
            position_id,
            sender=lane_env.lane.address,
        )
    with boa.reverts("paused"):
        lane_env.claims.createVestingPosition(
            lane_env.bob,
            1,
            1,
            sender=lane_env.lane.address,
        )


def test_can_retire_requires_pause_and_zero_outstanding(lane_env):
    assert lane_env.claims.canRetire() is False
    lane_env.claims.pause(True, sender=lane_env.switchboard.address)
    assert lane_env.claims.canRetire() is True
    lane_env.claims.pause(False, sender=lane_env.switchboard.address)

    position_id = create_position(lane_env, 100, 1)
    lane_env.claims.pause(True, sender=lane_env.switchboard.address)
    assert lane_env.claims.canRetire() is False
    lane_env.claims.pause(False, sender=lane_env.switchboard.address)
    travel_blocks(1)
    lane_env.claims.recordClaim(
        lane_env.bob,
        position_id,
        sender=lane_env.lane.address,
    )
    assert lane_env.claims.canRetire() is False
    lane_env.claims.pause(True, sender=lane_env.switchboard.address)
    assert lane_env.claims.canRetire() is True


def test_budget_reset_never_rewrites_allocation_or_claim_totals(lane_env):
    position_id = create_position(lane_env, 500, 2)
    lane_env.set_budget(7)
    assert lane_env.claims.totalAllocatedRipe() == 500
    assert lane_env.claims.totalClaimedRipe() == 0
    assert lane_env.claims.remainingAllocationBudget() == 7
    travel_blocks(2)
    lane_env.claims.recordClaim(
        lane_env.bob,
        position_id,
        sender=lane_env.lane.address,
    )
    lane_env.set_budget(99)
    assert lane_env.claims.totalAllocatedRipe() == 500
    assert lane_env.claims.totalClaimedRipe() == 500
    assert lane_env.claims.remainingAllocationBudget() == 99


def test_claims_authorizes_the_live_hq_lane(lane_env):
    replacement = boa.loads("# @version 0.4.3\n")
    lock = lane_env.ripe_hq.registryChangeTimeLock()
    assert lane_env.ripe_hq.startAddressUpdateToRegistry(
        INSTANT_BOND_LANE_HQ_ID,
        replacement,
        sender=lane_env.governance.address,
    )
    travel_blocks(lock)
    assert lane_env.ripe_hq.confirmAddressUpdateToRegistry(
        INSTANT_BOND_LANE_HQ_ID,
        sender=lane_env.governance.address,
    )

    with boa.reverts("invalid lane"):
        lane_env.claims.createVestingPosition(
            lane_env.bob,
            1,
            1,
            sender=lane_env.lane.address,
        )
    assert lane_env.claims.createVestingPosition(
        lane_env.bob,
        1,
        1,
        sender=replacement.address,
    ) == 1
