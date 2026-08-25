import boa
import pytest

from conf_utils import filter_logs


def _purchase(ctx, vesting_length=10, min_vesting_length=1, amount=None):
    amount = ctx.scale if amount is None else amount
    ctx.set_config(
        minVestingLength=min_vesting_length,
        maxVestingLength=vesting_length,
        maxVestingBonus=0,
    )
    payout = ctx.buy(amount, requested_vesting=vesting_length)
    position_id = ctx.claims.nextPositionId() - 1
    return position_id, payout


def _claim_state(ctx, position_id):
    index = ctx.claims.indexOfPosition(ctx.bob, position_id)
    position = (0, 0, 0, 0, 0, 0)
    if index:
        position = tuple(ctx.claims.positions(ctx.bob, index))
    return (
        ctx.claims.totalAllocatedRipe(),
        ctx.claims.totalClaimedRipe(),
        ctx.claims.remainingAllocationBudget(),
        ctx.claims.getNumUserPositions(ctx.bob),
        index,
        position,
        ctx.ripe_token.balanceOf(ctx.bob),
        ctx.ripe_token.balanceOf(ctx.lane),
        ctx.ripe_token.allowance(ctx.lane, ctx.teller),
    )


def test_direct_claim_mints_only_the_newly_vested_amount(lane_env):
    position_id, payout = _purchase(lane_env, 10)
    buyer_before = lane_env.ripe_token.balanceOf(lane_env.bob)
    budget_after_purchase = lane_env.claims.remainingAllocationBudget()
    boa.env.time_travel(blocks=4)

    first = lane_env.claim(position_id)
    expected_first = payout * 4 // 10
    lane_event = filter_logs(lane_env.lane, "VestedRipeClaimed")[-1]
    assert first == expected_first
    assert lane_env.ripe_token.balanceOf(lane_env.bob) == buyer_before + first
    assert lane_env.claims.totalClaimedRipe() == first
    assert lane_env.claims.totalOutstandingRipe() == payout - first
    assert lane_env.claims.remainingAllocationBudget() == budget_after_purchase
    assert lane_event.beneficiary == lane_env.bob
    assert lane_event.positionId == position_id
    assert lane_event.amountClaimed == first
    assert lane_event.totalClaimedForPosition == first
    assert lane_event.ripeAllocation == payout
    assert lane_event.autoDeposited is False
    assert lane_event.lockDuration == 0

    with boa.reverts("nothing to claim"):
        lane_env.claim(position_id)

    boa.env.time_travel(blocks=6)
    second = lane_env.claim(position_id, lock_duration=999)
    assert second == payout - first
    assert lane_env.ripe_token.balanceOf(lane_env.bob) == buyer_before + payout
    assert lane_env.claims.totalClaimedRipe() == payout
    assert lane_env.claims.totalOutstandingRipe() == 0
    assert lane_env.claims.getNumUserPositions(lane_env.bob) == 0
    assert filter_logs(lane_env.lane, "VestedRipeClaimed")[-1].lockDuration == 999


def test_claim_before_cliff_reverts_atomically(lane_env):
    position_id, _ = _purchase(
        lane_env,
        vesting_length=10,
        min_vesting_length=4,
    )
    before = _claim_state(lane_env, position_id)
    with boa.reverts("nothing to claim"):
        lane_env.claim(position_id)
    assert _claim_state(lane_env, position_id) == before

    boa.env.time_travel(blocks=3)
    with boa.reverts("nothing to claim"):
        lane_env.claim(position_id)
    assert _claim_state(lane_env, position_id) == before


def test_claim_at_cliff_catches_up_from_creation(lane_env):
    position_id, allocation = _purchase(
        lane_env,
        vesting_length=10,
        min_vesting_length=4,
    )
    boa.env.time_travel(blocks=4)
    assert lane_env.claim(position_id) == allocation * 4 // 10


def test_claims_continue_when_acquisitions_are_disabled_paused_and_stopped(lane_env):
    position_id, payout = _purchase(lane_env, 2)
    boa.env.time_travel(blocks=2)
    lane_env.lane.setCanAcquireRipe(False, sender=lane_env.switchboard.address)
    lane_env.lane.pause(True, sender=lane_env.switchboard.address)
    lane_env.stop()

    assert lane_env.lane.isRunning() is False
    assert lane_env.lane.isPaused() is True
    assert lane_env.lane.canAcquireRipe() is False
    assert lane_env.claim(position_id) == payout


def test_claim_readiness_checks_claims_pause_ripe_pause_and_mint_authority(
    lane_env, governance
):
    position_id, _ = _purchase(lane_env, 1)
    boa.env.time_travel(blocks=1)
    before = _claim_state(lane_env, position_id)

    lane_env.claims.pause(True, sender=lane_env.switchboard.address)
    with boa.reverts("claim not ready"):
        lane_env.claim(position_id)
    assert _claim_state(lane_env, position_id) == before
    lane_env.claims.pause(False, sender=lane_env.switchboard.address)

    lane_env.ripe_token.pause(True, sender=governance.address)
    with boa.reverts("claim not ready"):
        lane_env.claim(position_id)
    assert _claim_state(lane_env, position_id) == before
    lane_env.ripe_token.pause(False, sender=governance.address)

    lock = lane_env.ripe_hq.registryChangeTimeLock()
    lane_env.ripe_hq.initiateHqConfigChange(
        lane_env.lane_reg_id,
        False,
        False,
        False,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=lock)
    assert lane_env.ripe_hq.confirmHqConfigChange(
        lane_env.lane_reg_id,
        sender=governance.address,
    )
    with boa.reverts("claim not ready"):
        lane_env.claim(position_id)
    assert _claim_state(lane_env, position_id) == before


def test_claim_rejects_unknown_or_other_users_position(lane_env, alice):
    position_id, _ = _purchase(lane_env, 1)
    boa.env.time_travel(blocks=1)
    with boa.reverts("invalid position"):
        lane_env.claim(position_id + 1)
    with boa.reverts("invalid position"):
        lane_env.claim(position_id, sender=alice)


def test_batch_claim_sums_positions_and_emits_one_event_per_position(lane_env):
    lane_env.set_config(
        minVestingLength=5,
        maxVestingLength=5,
        maxVestingBonus=0,
    )
    payouts = [lane_env.buy(lane_env.scale) for _ in range(3)]
    position_ids = [1, 2, 3]
    boa.env.time_travel(blocks=5)
    balance_before = lane_env.ripe_token.balanceOf(lane_env.bob)

    total = lane_env.lane.claimVestedRipeMany(
        position_ids,
        False,
        0,
        sender=lane_env.bob,
    )
    events = filter_logs(lane_env.lane, "VestedRipeClaimed")
    assert total == sum(payouts)
    assert lane_env.ripe_token.balanceOf(lane_env.bob) == balance_before + total
    assert [event.positionId for event in events] == position_ids
    assert [event.amountClaimed for event in events] == payouts
    assert lane_env.claims.getNumUserPositions(lane_env.bob) == 0


def test_batch_claim_rejects_empty_and_abi_over_limit(lane_env):
    with boa.reverts("empty positions"):
        lane_env.lane.claimVestedRipeMany([], False, 0, sender=lane_env.bob)
    with pytest.raises(Exception):
        lane_env.lane.claimVestedRipeMany(
            list(range(1, lane_env.lane.MAX_BATCH_CLAIMS() + 2)),
            False,
            0,
            sender=lane_env.bob,
        )


@pytest.mark.parametrize("position_ids", ([1, 1], [1, 999]))
def test_batch_claim_is_atomic_when_a_later_item_fails(lane_env, position_ids):
    position_id, _ = _purchase(lane_env, 1)
    assert position_id == 1
    boa.env.time_travel(blocks=1)
    before = _claim_state(lane_env, position_id)
    with boa.reverts():
        lane_env.lane.claimVestedRipeMany(
            position_ids,
            False,
            0,
            sender=lane_env.bob,
        )
    assert _claim_state(lane_env, position_id) == before


def test_maximum_batch_of_twenty_claims_succeeds(lane_env):
    count = lane_env.lane.MAX_BATCH_CLAIMS()
    payout = 10**18
    for _ in range(count):
        lane_env.claims.createVestingPosition(
            lane_env.bob,
            payout,
            1,
            1,
            sender=lane_env.lane.address,
        )
    boa.env.time_travel(blocks=1)
    position_ids = list(range(1, count + 1))
    assert lane_env.lane.claimVestedRipeMany(
        position_ids,
        False,
        0,
        sender=lane_env.bob,
    ) == count * payout
    assert lane_env.claims.getNumUserPositions(lane_env.bob) == 0


def test_auto_deposit_claim_mints_to_lane_then_deposits_exactly(lane_env):
    lane_env.setup_ripe_vault(min_lock=100, max_lock=1_000)
    position_id, payout = _purchase(lane_env, 1)
    boa.env.time_travel(blocks=1)
    lane_balance_before = lane_env.ripe_token.balanceOf(lane_env.lane)
    vault_before = lane_env.ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob,
        lane_env.ripe_token,
    )

    claimed = lane_env.claim(
        position_id,
        auto_deposit=True,
        lock_duration=500,
    )
    event = filter_logs(lane_env.lane, "VestedRipeClaimed")[-1]
    assert claimed == payout
    assert event.autoDeposited is True
    assert event.lockDuration == 500
    assert lane_env.ripe_token.balanceOf(lane_env.lane) == lane_balance_before
    assert lane_env.ripe_token.allowance(lane_env.lane, lane_env.teller) == 0
    assert lane_env.ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob,
        lane_env.ripe_token,
    ) == vault_before + payout


@pytest.mark.parametrize(
    "setup_overrides,reason",
    [
        ({"can_deposit": False}, "protocol deposits disabled"),
        ({"asset_can_deposit": False}, "asset deposits disabled"),
    ],
)
def test_failed_auto_deposit_rolls_back_claim_ledger(
    lane_env, setup_overrides, reason
):
    lane_env.setup_ripe_vault(**setup_overrides)
    position_id, _ = _purchase(lane_env, 1)
    boa.env.time_travel(blocks=1)
    before = _claim_state(lane_env, position_id)

    with boa.reverts(reason):
        lane_env.claim(position_id, auto_deposit=True, lock_duration=500)
    assert _claim_state(lane_env, position_id) == before


def test_auto_deposit_rejects_zero_or_unknown_core_vault_atomically(lane_env):
    lane_env.setup_ripe_vault()
    position_id, _ = _purchase(lane_env, 1)
    boa.env.time_travel(blocks=1)
    before = _claim_state(lane_env, position_id)

    lane_env.mission_control.eval("self.coreRipeGovVaultId = 0")
    with boa.reverts("invalid ripe gov vault"):
        lane_env.claim(position_id, auto_deposit=True, lock_duration=1)
    assert _claim_state(lane_env, position_id) == before

    lane_env.mission_control.setCoreRipeGovVaultId(
        999,
        sender=lane_env.switchboard.address,
    )
    with boa.reverts("invalid vault id"):
        lane_env.claim(position_id, auto_deposit=True, lock_duration=1)
    assert _claim_state(lane_env, position_id) == before


def test_blacklist_enforcement_is_atomic_for_both_settlement_paths(
    lane_env, switchboard
):
    direct_id, _ = _purchase(lane_env, 1)
    boa.env.time_travel(blocks=1)
    lane_env.ripe_token.setBlacklist(
        lane_env.bob,
        True,
        sender=switchboard.address,
    )
    direct_before = _claim_state(lane_env, direct_id)
    with boa.reverts():
        lane_env.claim(direct_id)
    assert _claim_state(lane_env, direct_id) == direct_before
    lane_env.ripe_token.setBlacklist(
        lane_env.bob,
        False,
        sender=switchboard.address,
    )

    lane_env.setup_ripe_vault()
    auto_id = lane_env.claims.createVestingPosition(
        lane_env.bob,
        10**18,
        1,
        1,
        sender=lane_env.lane.address,
    )
    boa.env.time_travel(blocks=1)
    lane_env.ripe_token.setBlacklist(
        lane_env.lane,
        True,
        sender=switchboard.address,
    )
    auto_before = _claim_state(lane_env, auto_id)
    with boa.reverts():
        lane_env.claim(auto_id, auto_deposit=True, lock_duration=100)
    assert _claim_state(lane_env, auto_id) == auto_before
