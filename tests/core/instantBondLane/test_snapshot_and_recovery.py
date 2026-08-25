import boa

from conf_utils import filter_logs
from constants import MAX_UINT256


FEE_ON_TRANSFER = """
# @version 0.4.3

decimals: public(immutable(uint8))
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
owner: public(address)
feeBps: public(uint256)

@deploy
def __init__(_owner: address, _decimals: uint8, _feeBps: uint256):
    decimals = _decimals
    self.owner = _owner
    self.feeBps = _feeBps
    self.balanceOf[_owner] = 10**30

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


def test_epoch_cap_minimum_bonus_and_vesting_bounds_are_snapshotted(lane_env):
    first_cap = 100 * lane_env.scale
    lane_env.set_config(
        paymentCapPerEpoch=first_cap,
        minPaymentAmount=lane_env.scale,
        maxVestingBonus=5_000,
        minVestingLength=100,
        maxVestingLength=1_000,
    )
    lane_env.buy(10 * lane_env.scale, requested_vesting=1_000)

    lane_env.set_config(
        paymentCapPerEpoch=20 * lane_env.scale,
        minPaymentAmount=5 * lane_env.scale,
        maxVestingBonus=0,
        minVestingLength=400,
        maxVestingLength=500,
    )
    state = lane_env.lane.epochState()
    assert state.paymentCap == first_cap
    assert state.minPaymentAmount == lane_env.scale
    assert state.maxVestingBonus == 5_000
    assert state.minVestingLength == 100
    assert state.maxVestingLength == 1_000

    quote = lane_env.quote(lane_env.scale, 1_000)
    assert quote.remainingPayment == first_cap - 10 * lane_env.scale
    assert quote.minPaymentAmount == lane_env.scale
    assert quote.vestingLength == 1_000
    assert quote.bonusRatio == 5_000

    boa.env.time_travel(blocks=lane_env.epoch_length)
    next_quote = lane_env.quote(5 * lane_env.scale, 1_000)
    assert next_quote.remainingPayment == 20 * lane_env.scale
    assert next_quote.minPaymentAmount == 5 * lane_env.scale
    assert next_quote.vestingLength == 500
    assert next_quote.bonusRatio == 0


def test_pause_keeps_clock_snapshot_and_override(lane_env):
    lane_env.buy(lane_env.scale)
    lane_env.set_rate_override(9 * 10**17)
    genesis = lane_env.lane.genesisBlock()
    state = lane_env.lane.epochState()

    lane_env.lane.pause(True, sender=lane_env.switchboard.address)
    assert lane_env.lane.isRunning() is True
    assert lane_env.lane.genesisBlock() == genesis
    assert tuple(lane_env.lane.epochState()) == tuple(state)
    assert lane_env.lane.overrideTargetBasePayoutRate() == 9 * 10**17
    quote = lane_env.quote(lane_env.scale)
    assert quote.available is False
    assert quote.basePayoutRate == state.basePayoutRate

    lane_env.lane.pause(False, sender=lane_env.switchboard.address)
    lane_env.buy(lane_env.scale)
    assert lane_env.lane.epochState().acceptedPayment == (
        state.acceptedPayment + lane_env.scale
    )


def test_seed_change_does_not_move_committed_epoch(lane_env):
    lane_env.buy(lane_env.scale)
    committed = lane_env.lane.epochState().basePayoutRate
    lane_env.set_config(seedBasePayoutRate=11 * 10**17)
    assert lane_env.lane.getEpochSnapshot().basePayoutRate == committed
    assert lane_env.quote(lane_env.scale).basePayoutRate == committed


def test_recover_funds_is_switchboard_gated(lane_env, alice):
    stranded = 25 * lane_env.scale
    lane_env.payment_token.transfer(lane_env.lane, stranded, sender=lane_env.bob)
    with boa.reverts("no perms"):
        lane_env.lane.recoverFunds(alice, lane_env.payment_token, sender=alice)

    before = lane_env.payment_token.balanceOf(alice)
    lane_env.lane.recoverFunds(
        alice,
        lane_env.payment_token,
        sender=lane_env.switchboard.address,
    )
    event = filter_logs(lane_env.lane, "DepartmentFundsRecovered")[-1]
    assert event.asset == lane_env.payment_token.address
    assert event.recipient == alice
    assert event.balance == stranded
    assert lane_env.payment_token.balanceOf(alice) == before + stranded
    assert lane_env.payment_token.balanceOf(lane_env.lane) == 0


def test_recover_funds_many(lane_env, alice, ripe_token, whale):
    payment_amount = 11 * lane_env.scale
    ripe_amount = 7 * 10**18
    lane_env.payment_token.transfer(
        lane_env.lane,
        payment_amount,
        sender=lane_env.bob,
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


def test_fee_on_transfer_payment_reverts_all_purchase_state(
    lane_factory, governance
):
    token = boa.loads(FEE_ON_TRANSFER, governance.address, 6, 100)
    scale = 10**6
    ctx = lane_factory(payment_token=token, fund_buyer=False)
    token.transfer(ctx.bob, 100 * scale, sender=governance.address)
    token.approve(ctx.lane, MAX_UINT256, sender=ctx.bob)
    budget_before = ctx.claims.remainingAllocationBudget()
    funds_before = token.balanceOf(ctx.endaoment_funds)

    with boa.reverts("payment receipt mismatch"):
        ctx.buy(scale)
    assert ctx.lane.epochState().basePayoutRate == 0
    assert ctx.claims.totalAllocatedRipe() == 0
    assert ctx.claims.nextPositionId() == 1
    assert ctx.claims.remainingAllocationBudget() == budget_before
    assert token.balanceOf(ctx.endaoment_funds) == funds_before


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
    seed = lane_env.lane.bondConfig().seedBasePayoutRate

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

    assert early_quote.basePayoutRate < seed
    assert late_quote.basePayoutRate < seed
    assert late_quote.basePayoutRate > early_quote.basePayoutRate
