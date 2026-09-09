import boa

from constants import (
    RIPE_RESERVE_VESTING_HQ_ID,
    MAX_UINT256,
)
from tests.core.ripeReserveEngine.conftest import make_config, travel_blocks


REPLACEMENT_RIPE_TOKEN = """
# pragma version 0.4.3

ripeHq: public(address)
balanceOf: public(HashMap[address, uint256])
blacklisted: public(HashMap[address, bool])

@deploy
def __init__(_ripeHq: address):
    self.ripeHq = _ripeHq

@view
@external
def isPaused() -> bool:
    return False

@external
def mint(_recipient: address, _amount: uint256) -> bool:
    self.balanceOf[_recipient] += _amount
    return True
"""


def test_stop_new_seed_restart_uses_new_seed_without_rewriting_claims(lane_env):
    first = lane_env.buy(lane_env.scale)
    assert lane_env.lane.epochState().basePayoutRate == 10**18
    lane_env.stop()
    lane_env.set_config(seedBasePayoutRate=11 * 10**17)
    lane_env.start(0)
    assert lane_env.lane.epochState().basePayoutRate == 0
    quote = lane_env.quote(lane_env.scale)
    assert quote.basePayoutRate == 11 * 10**17
    second = lane_env.buy(lane_env.scale)
    assert second != first
    assert lane_env.lane.epochState().basePayoutRate == 11 * 10**17
    assert lane_env.claims.totalAllocatedRipe() == first + second
    assert lane_env.claims.getNumUserPositions(lane_env.bob) == 2


def test_payment_token_swap_requires_valid_cap_units(lane_env, governance):
    other = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "Other",
        "OTH",
        10,
        1_000_000,
    )
    old_funds = lane_env.payment_token.balanceOf(lane_env.endaoment_funds)
    lane_env.stop()
    lane_env.lane.setPaymentToken(other.address, sender=lane_env.switchboard.address)
    assert lane_env.lane.paymentScale() == 10**10
    assert lane_env.lane.isValidConfig(lane_env.lane.engineConfig()) is False
    with boa.reverts("not configured"):
        lane_env.lane.start(
            0,
            lane_env.epoch_length,
            sender=lane_env.switchboard.address,
        )

    new_scale = 10**10
    config = make_config(new_scale, epoch_length=lane_env.epoch_length)
    lane_env.lane.setConfig(config, sender=lane_env.switchboard.address)
    lane_env.lane.start(0, lane_env.epoch_length, sender=lane_env.switchboard.address)
    other.transfer(lane_env.bob, 100 * new_scale, sender=governance.address)
    other.approve(lane_env.lane, MAX_UINT256, sender=lane_env.bob)

    quote = lane_env.lane.previewAcquireRipe(new_scale, 0, sender=lane_env.bob)
    payout = lane_env.lane.acquireRipe(
        new_scale,
        0,
        quote.vestingLength,
        quote.epoch,
        quote.totalRipe,
        boa.env.evm.patch.block_number,
        sender=lane_env.bob,
    )
    assert payout == quote.totalRipe
    assert other.balanceOf(lane_env.endaoment_funds) == new_scale
    assert lane_env.payment_token.balanceOf(lane_env.endaoment_funds) == old_funds


def test_live_ripe_pause_fails_preview_and_acquisition_closed(lane_env):
    quote = lane_env.quote(lane_env.scale)
    assert quote.available is True
    lane_env.ripe_token.pause(True, sender=lane_env.governance.address)
    blocked = lane_env.quote(lane_env.scale)
    assert blocked.available is False
    assert blocked.totalRipe == quote.totalRipe
    with boa.reverts("mint not ready"):
        lane_env.buy(lane_env.scale)


def test_engine_reads_replacement_vesting_from_ripe_hq(lane_env):
    original = lane_env.claims
    replacement = boa.load(
        "contracts/core/RipeReserveVesting.vy",
        lane_env.ripe_hq,
        name="replacement_ripe_reserve_vesting",
    )
    replacement.pause(False, sender=lane_env.switchboard.address)
    replacement.setRemainingAllocationBudget(
        123 * 10**18,
        sender=lane_env.switchboard.address,
    )
    lock = lane_env.ripe_hq.registryChangeTimeLock()
    assert lane_env.ripe_hq.startAddressUpdateToRegistry(
        RIPE_RESERVE_VESTING_HQ_ID,
        replacement,
        sender=lane_env.governance.address,
    )
    travel_blocks(lock)
    assert lane_env.ripe_hq.confirmAddressUpdateToRegistry(
        RIPE_RESERVE_VESTING_HQ_ID,
        sender=lane_env.governance.address,
    )

    quote = lane_env.quote(lane_env.scale)
    assert quote.available is True
    assert quote.budgetRemaining == 123 * 10**18
    payout = lane_env.buy(lane_env.scale)
    assert replacement.totalAllocatedRipe() == payout
    assert replacement.getNumUserPositions(lane_env.bob) == 1
    assert original.totalAllocatedRipe() == 0


def test_claim_settlement_reads_replacement_ripe_token_from_hq(lane_env):
    lane_env.set_config(
        minVestingLength=1,
        maxVestingLength=1,
        maxVestingBonus=0,
    )
    payout = lane_env.buy(lane_env.scale)
    replacement = boa.loads(
        REPLACEMENT_RIPE_TOKEN,
        lane_env.ripe_hq,
        name="replacement_ripe_token",
    )
    lock = lane_env.ripe_hq.registryChangeTimeLock()
    assert lane_env.ripe_hq.startAddressUpdateToRegistry(
        3,
        replacement,
        sender=lane_env.governance.address,
    )
    travel_blocks(lock)
    assert lane_env.ripe_hq.confirmAddressUpdateToRegistry(
        3,
        sender=lane_env.governance.address,
    )
    travel_blocks(1)

    assert lane_env.claim(1) == payout
    assert replacement.balanceOf(lane_env.bob) == payout
    assert lane_env.ripe_token.balanceOf(lane_env.bob) == 0
