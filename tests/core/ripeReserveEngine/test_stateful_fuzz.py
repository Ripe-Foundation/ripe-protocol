import boa
import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from constants import MAX_UINT256


ACTION = st.tuples(
    st.integers(min_value=0, max_value=120),
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=0, max_value=25),
    st.booleans(),
)


@given(actions=st.lists(ACTION, min_size=1, max_size=20))
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@pytest.mark.fuzz
def test_stateful_purchase_vesting_claim_accounting(lane_env, actions):
    with boa.env.anchor():
        lane_env.set_budget(MAX_UINT256)
        lane_env.set_config(
            paymentCapPerEpoch=50 * lane_env.scale,
            minPaymentAmount=lane_env.scale,
            maxVestingBonus=5_000,
            minVestingLength=1,
            maxVestingLength=20,
        )
        initial_ripe_balance = lane_env.ripe_token.balanceOf(lane_env.bob)
        allocated = 0
        claimed = 0
        purchases = 0
        active_ids = []

        for travel, payment_units, requested_vesting, should_claim in actions:
            if travel:
                boa.env.time_travel(blocks=travel)

            amount = payment_units * lane_env.scale
            epoch_before = tuple(lane_env.lane.epochState())
            budget_before = lane_env.claims.remainingAllocationBudget()
            next_id_before = lane_env.claims.nextPositionId()
            quote = lane_env.quote(amount, requested_vesting)
            assert tuple(lane_env.lane.epochState()) == epoch_before
            assert lane_env.claims.remainingAllocationBudget() == budget_before
            assert lane_env.claims.nextPositionId() == next_id_before

            if quote.available:
                payout = lane_env.buy(
                    amount,
                    requested_vesting=requested_vesting,
                    min_ripe_out=quote.totalRipe,
                )
                purchases += 1
                allocated += payout
                position_id = lane_env.claims.nextPositionId() - 1
                active_ids.append(position_id)
                assert payout == quote.totalRipe
                assert lane_env.claims.positions(
                    lane_env.bob,
                    lane_env.claims.indexOfPosition(lane_env.bob, position_id),
                ).maturityBlock == quote.maturityBlock

            if should_claim:
                for position_id in list(active_ids):
                    claimable = lane_env.claims.getClaimableRipe(
                        lane_env.bob,
                        position_id,
                    )
                    if claimable == 0:
                        continue
                    amount_claimed = lane_env.claim(position_id)
                    assert amount_claimed == claimable
                    claimed += amount_claimed
                    if lane_env.claims.indexOfPosition(lane_env.bob, position_id) == 0:
                        active_ids.remove(position_id)

            assert lane_env.claims.totalAllocatedRipe() == allocated
            assert lane_env.claims.totalClaimedRipe() == claimed
            assert lane_env.claims.totalOutstandingRipe() == allocated - claimed
            assert lane_env.claims.remainingAllocationBudget() == MAX_UINT256 - allocated
            assert lane_env.claims.nextPositionId() == purchases + 1
            assert lane_env.claims.getNumUserPositions(lane_env.bob) == len(active_ids)
            assert lane_env.ripe_token.balanceOf(lane_env.bob) == (
                initial_ripe_balance + claimed
            )
            state = lane_env.lane.epochState()
            if state.basePayoutRate != 0:
                assert state.acceptedPayment <= state.paymentCap

        boa.env.time_travel(blocks=20)
        for position_id in list(active_ids):
            claimable = lane_env.claims.getClaimableRipe(lane_env.bob, position_id)
            if claimable:
                claimed += lane_env.claim(position_id)
            active_ids.remove(position_id)

        assert claimed == allocated
        assert lane_env.claims.totalClaimedRipe() == allocated
        assert lane_env.claims.totalOutstandingRipe() == 0
        assert lane_env.claims.getNumUserPositions(lane_env.bob) == 0
