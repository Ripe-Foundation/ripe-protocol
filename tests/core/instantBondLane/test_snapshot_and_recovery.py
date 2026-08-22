import boa
import pytest

from conf_utils import filter_logs, get_boa_dev_reasons
from constants import MAX_UINT256


FEE_ON_TRANSFER = """
# @version 0.4.3

decimals: public(immutable(uint8))
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)
owner: public(address)
feeBps: public(uint256)

@deploy
def __init__(_owner: address, _decimals: uint8, _feeBps: uint256):
    decimals = _decimals
    self.owner = _owner
    self.feeBps = _feeBps
    self.totalSupply = 10**30
    self.balanceOf[_owner] = self.totalSupply

@external
def transfer(_to: address, _value: uint256) -> bool:
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    return True

@external
def approve(_spender: address, _value: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _value
    return True

@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    self.allowance[_from][msg.sender] -= _value
    fee: uint256 = _value * self.feeBps // 10_000
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value - fee
    return True
"""


def test_epoch_cap_min_and_bonus_are_snapshotted(lane_env):
    first_cap = 100 * lane_env.scale
    lane_env.set_config(
        paymentCapPerEpoch=first_cap,
        minPaymentAmount=lane_env.scale,
        maxLockBonus=5_000,
    )
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    lane_env.buy(10 * lane_env.scale)

    lane_env.set_config(
        paymentCapPerEpoch=20 * lane_env.scale,
        minPaymentAmount=5 * lane_env.scale,
        maxLockBonus=0,
    )
    state = lane_env.lane.epochState()
    assert state.paymentCap == first_cap
    assert state.minPaymentAmount == lane_env.scale
    assert state.maxLockBonus == 5_000

    quote = lane_env.quote(lane_env.scale, 1_000)
    assert quote.remainingPayment == first_cap - 10 * lane_env.scale
    assert quote.minPaymentAmount == lane_env.scale
    assert quote.bonusRatio == 5_000
    assert quote.available is True

    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(first_cap)
    assert "exceeds available amount" in get_boa_dev_reasons(err.value)

    boa.env.time_travel(blocks=lane_env.epoch_length)
    next_quote = lane_env.quote(5 * lane_env.scale, 1_000)
    assert next_quote.remainingPayment == 20 * lane_env.scale
    assert next_quote.minPaymentAmount == 5 * lane_env.scale
    assert next_quote.bonusRatio == 0


def test_min_lock_duration_is_live_not_snapshotted(lane_env):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    lane_env.set_config(minLockDuration=0, maxLockBonus=5_000)
    unlocked = lane_env.quote(lane_env.scale, 0)
    assert unlocked.actualLock == 0

    lane_env.set_config(minLockDuration=400, maxLockBonus=5_000)
    forced = lane_env.quote(lane_env.scale, 0)
    assert forced.actualLock == 400
    assert forced.bonusRatio == 0
    payout = lane_env.buy(lane_env.scale, requested_lock=0)
    assert payout == forced.totalRipe
    purchased = filter_logs(lane_env.lane, "InstantBondPurchased")[-1]
    assert purchased.actualLock == 400


def test_pause_keeps_clock_snapshot_and_override(lane_env):
    lane_env.buy(lane_env.scale)
    lane_env.set_rate_override(9 * 10**17)
    genesis = lane_env.lane.genesisBlock()
    state = lane_env.lane.epochState()

    lane_env.lane.pause(True, sender=lane_env.switchboard.address)
    assert lane_env.lane.isPaused() is True
    assert lane_env.lane.isRunning() is True
    assert lane_env.lane.genesisBlock() == genesis
    assert lane_env.lane.epochState().acceptedPayment == state.acceptedPayment
    assert lane_env.lane.rateOverride() == 9 * 10**17

    quote = lane_env.quote(lane_env.scale)
    assert quote.available is False
    assert quote.rate == state.rate

    lane_env.lane.pause(False, sender=lane_env.switchboard.address)
    assert lane_env.quote(lane_env.scale).available is True
    lane_env.buy(lane_env.scale)
    assert lane_env.lane.epochState().acceptedPayment == state.acceptedPayment + lane_env.scale


def test_seed_rate_change_does_not_move_a_committed_epoch(lane_env):
    lane_env.buy(lane_env.scale)
    committed = lane_env.lane.epochState().rate
    lane_env.set_config(seedRate=11 * 10**17)
    assert lane_env.lane.getEpochSnapshot().rate == committed
    assert lane_env.quote(lane_env.scale).rate == committed


def test_set_cumulative_minted_consumes_budget_immediately(lane_env):
    quote = lane_env.quote(lane_env.scale)
    lane_env.lane.setCumulativeMinted(
        quote.budgetRemaining - quote.totalRipe + 1,
        sender=lane_env.switchboard.address,
    )
    blocked = lane_env.quote(lane_env.scale)
    assert blocked.available is False
    assert blocked.totalRipe == quote.totalRipe
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale)
    assert "mint budget" in get_boa_dev_reasons(err.value)

    lane_env.lane.setCumulativeMinted(0, sender=lane_env.switchboard.address)
    assert lane_env.quote(lane_env.scale).available is True
    assert lane_env.buy(lane_env.scale) == quote.totalRipe


def test_recover_funds_is_switchboard_gated(lane_env, alice):
    stranded = 25 * lane_env.scale
    lane_env.payment_token.transfer(
        lane_env.lane, stranded, sender=lane_env.bob
    )
    with boa.reverts("no perms"):
        lane_env.lane.recoverFunds(
            alice, lane_env.payment_token, sender=alice
        )
    before = lane_env.payment_token.balanceOf(alice)
    lane_env.lane.recoverFunds(
        alice,
        lane_env.payment_token,
        sender=lane_env.switchboard.address,
    )
    recovered = filter_logs(lane_env.lane, "DepartmentFundsRecovered")[-1]
    assert recovered.asset == lane_env.payment_token.address
    assert recovered.recipient == alice
    assert recovered.balance == stranded
    assert lane_env.payment_token.balanceOf(alice) == before + stranded
    assert lane_env.payment_token.balanceOf(lane_env.lane) == 0


def test_recover_funds_many(lane_env, alice, ripe_token, whale):
    payment_amount = 11 * lane_env.scale
    ripe_amount = 7 * 10**18
    lane_env.payment_token.transfer(
        lane_env.lane, payment_amount, sender=lane_env.bob
    )
    ripe_token.transfer(lane_env.lane, ripe_amount, sender=whale)
    alice_pay = lane_env.payment_token.balanceOf(alice)
    alice_ripe = ripe_token.balanceOf(alice)
    lane_env.lane.recoverFundsMany(
        alice,
        [lane_env.payment_token.address, ripe_token.address],
        sender=lane_env.switchboard.address,
    )
    assert lane_env.payment_token.balanceOf(alice) == alice_pay + payment_amount
    assert ripe_token.balanceOf(alice) == alice_ripe + ripe_amount
    assert lane_env.payment_token.balanceOf(lane_env.lane) == 0
    assert ripe_token.balanceOf(lane_env.lane) == 0


def test_fee_on_transfer_payment_is_rejected(lane_factory, governance):
    token = boa.loads(FEE_ON_TRANSFER, governance.address, 6, 100)
    scale = 10**6
    ctx = lane_factory(payment_token=token, fund_buyer=False)
    token.transfer(ctx.bob, 100 * scale, sender=governance.address)
    token.approve(ctx.lane, MAX_UINT256, sender=ctx.bob)
    with pytest.raises(boa.BoaError) as err:
        ctx.buy(scale)
    assert "payment receipt mismatch" in get_boa_dev_reasons(err.value)
    assert ctx.lane.epochState().rate == 0
    assert ctx.lane.cumulativeMinted() == 0


def test_last_write_wins_rate_override(lane_env):
    lane_env.buy(lane_env.scale)
    lane_env.set_rate_override(8 * 10**17)
    lane_env.set_rate_override(9 * 10**17)
    assert lane_env.lane.rateOverride() == 9 * 10**17
    boa.env.time_travel(blocks=lane_env.epoch_length)
    assert lane_env.quote(lane_env.scale).rate == 9 * 10**17


def test_high_utilization_late_fill_weakens_up_step(lane_env):
    cap = 100 * lane_env.scale
    lane_env.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=lane_env.scale,
        minUpBps=200,
        maxUpBps=1_000,
        minDownBps=50,
        maxDownBps=100,
        decayBps=196,
    )
    seed = lane_env.lane.bondConfig().seedRate

    lane_env.buy(90 * lane_env.scale)
    boa.env.time_travel(blocks=lane_env.epoch_length)
    early_quote = lane_env.quote(lane_env.scale)

    lane_env.stop()
    lane_env.start(0)
    lane_env.buy(10 * lane_env.scale)
    boa.env.time_travel(blocks=lane_env.epoch_length - 1)
    lane_env.buy(80 * lane_env.scale)
    boa.env.time_travel(blocks=1)
    late_quote = lane_env.quote(lane_env.scale)

    assert early_quote.rate < seed
    assert late_quote.rate < seed
    assert late_quote.rate > early_quote.rate
