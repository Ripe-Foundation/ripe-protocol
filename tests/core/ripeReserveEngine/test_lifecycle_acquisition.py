import boa

from conf_utils import filter_logs
from constants import MAX_UINT256


REENTRANT_PAYMENT = """
# @version 0.4.3

interface ReserveEngine:
    def acquireRipe(
        _paymentAmount: uint256,
        _requestedVestingLength: uint256,
        _expectedVestingLength: uint256,
        _expectedEpoch: uint256,
        _minRipeOut: uint256,
        _deadlineBlock: uint256,
    ) -> uint256: nonpayable
    def epochState() -> (uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256, bool): view

decimals: public(immutable(uint8))
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
owner: public(address)
attackTarget: public(address)
attackAttempted: public(bool)
attackSucceeded: public(bool)
attackAmount: public(uint256)
observedAccepted: public(uint256)

@deploy
def __init__(_owner: address, _decimals: uint8):
    decimals = _decimals
    self.owner = _owner
    self.balanceOf[_owner] = 10**30

@external
def arm(_target: address, _amount: uint256):
    assert msg.sender == self.owner
    self.attackTarget = _target
    self.attackAmount = _amount
    self.attackAttempted = False
    self.attackSucceeded = False

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
    if not self.attackAttempted and self.attackTarget != empty(address):
        self.attackAttempted = True
        state: (uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256, bool) = staticcall ReserveEngine(self.attackTarget).epochState()
        self.observedAccepted = state[9]
        success: bool = False
        response: Bytes[32] = b""
        success, response = raw_call(
            self.attackTarget,
            concat(
                method_id("acquireRipe(uint256,uint256,uint256,uint256,uint256,uint256)"),
                convert(self.attackAmount, bytes32),
                empty(bytes32),
                convert(100, bytes32),
                empty(bytes32),
                empty(bytes32),
                convert(max_value(uint256), bytes32),
            ),
            max_outsize=32,
            revert_on_failure=False,
        )
        self.attackSucceeded = success
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    return True
"""


def test_first_quote_matches_allocation_position_and_events(lane_env):
    amount = lane_env.scale
    quote = lane_env.quote(amount)
    budget_before = lane_env.claims.remainingAllocationBudget()
    buyer_ripe_before = lane_env.ripe_token.balanceOf(lane_env.bob)
    funds_before = lane_env.payment_token.balanceOf(lane_env.endaoment_funds)

    assert quote.available is True
    assert quote.epoch == 0
    assert quote.controllerBasePayoutRate == lane_env.lane.engineConfig().seedBasePayoutRate
    assert quote.basePayoutRate == quote.controllerBasePayoutRate
    assert quote.rateSource == lane_env.lane.RATE_SOURCE_SEED()
    assert quote.remainingPayment == lane_env.lane.engineConfig().paymentCapPerEpoch
    assert quote.minPaymentAmount == amount
    assert quote.vestingLength == lane_env.lane.engineConfig().minVestingLength
    assert quote.totalRipe == quote.baseRipe + quote.bonusRipe
    assert quote.claimStartBlock == (
        quote.creationBlock + lane_env.lane.engineConfig().minVestingLength
    )
    assert quote.maturityBlock == quote.creationBlock + quote.vestingLength

    payout = lane_env.buy(amount, min_ripe_out=quote.totalRipe)
    initialized = filter_logs(lane_env.lane, "EpochInitialized")[-1]
    purchased = filter_logs(lane_env.lane, "RipeAllocated")[-1]
    position = lane_env.claims.positions(lane_env.bob, 1)

    assert payout == quote.totalRipe
    assert lane_env.ripe_token.balanceOf(lane_env.bob) == buyer_ripe_before
    assert lane_env.payment_token.balanceOf(lane_env.endaoment_funds) == funds_before + amount
    assert lane_env.claims.remainingAllocationBudget() == budget_before - payout
    assert lane_env.claims.totalAllocatedRipe() == payout
    assert lane_env.claims.totalClaimedRipe() == 0
    assert tuple(position) == (
        1,
        payout,
        0,
        quote.creationBlock,
        quote.claimStartBlock,
        quote.maturityBlock,
    )
    assert initialized.epoch == quote.epoch
    assert initialized.basePayoutRate == quote.basePayoutRate
    assert purchased.acquirer == lane_env.bob
    assert purchased.positionId == 1
    assert purchased.paymentAmount == amount
    assert purchased.totalRipe == payout
    assert purchased.vestingLength == quote.vestingLength
    assert purchased.creationBlock == quote.creationBlock
    assert purchased.claimStartBlock == quote.claimStartBlock
    assert purchased.maturityBlock == quote.maturityBlock


def test_getters_are_stale_until_successful_purchase_but_snapshot_is_live(lane_env):
    live = lane_env.lane.getEpochSnapshot()
    stored = lane_env.lane.epochState()
    assert stored.basePayoutRate == 0
    assert live.basePayoutRate == lane_env.lane.engineConfig().seedBasePayoutRate
    assert live.epoch == 0

    lane_env.buy(lane_env.scale)
    assert lane_env.lane.epochState().basePayoutRate == live.basePayoutRate
    assert lane_env.lane.getEpochSnapshot().basePayoutRate == live.basePayoutRate


def test_purchase_constraint_reverts_are_exact(lane_env):
    amount = lane_env.scale
    quote = lane_env.quote(amount)
    block_number = boa.env.evm.patch.block_number

    with boa.reverts("below minimum payment"):
        lane_env.buy(amount - 1)
    with boa.reverts("exceeds available amount"):
        lane_env.buy(lane_env.lane.engineConfig().paymentCapPerEpoch + 1)
    with boa.reverts("epoch moved"):
        lane_env.lane.acquireRipe(
            amount,
            0,
            quote.vestingLength,
            quote.epoch + 1,
            0,
            block_number,
            sender=lane_env.bob,
        )
    with boa.reverts("vesting length moved"):
        lane_env.lane.acquireRipe(
            amount,
            0,
            quote.vestingLength + 1,
            quote.epoch,
            0,
            block_number,
            sender=lane_env.bob,
        )
    with boa.reverts("slippage"):
        lane_env.buy(amount, min_ripe_out=quote.totalRipe + 1)
    with boa.reverts("expired"):
        lane_env.buy(amount, deadline=block_number - 1)


def test_epoch_payment_cap_is_preserved(lane_env):
    cap = 10 * lane_env.scale
    lane_env.set_config(paymentCapPerEpoch=cap, minPaymentAmount=lane_env.scale)
    lane_env.buy(6 * lane_env.scale)
    assert lane_env.quote(lane_env.scale).remainingPayment == 4 * lane_env.scale
    with boa.reverts("exceeds available amount"):
        lane_env.buy(5 * lane_env.scale)
    lane_env.buy(4 * lane_env.scale)
    assert lane_env.lane.epochState().acceptedPayment == cap
    assert lane_env.quote(lane_env.scale).remainingPayment == 0


def test_claims_budget_is_authoritative_and_never_refilled_by_purchase(lane_env):
    quote = lane_env.quote(lane_env.scale)
    lane_env.set_budget(quote.totalRipe)
    first = lane_env.buy(lane_env.scale)
    assert first == quote.totalRipe
    assert lane_env.claims.remainingAllocationBudget() == 0
    assert lane_env.claims.totalAllocatedRipe() == first

    unavailable = lane_env.quote(lane_env.scale)
    assert unavailable.available is False
    assert unavailable.budgetRemaining == 0
    assert unavailable.totalRipe > 0
    with boa.reverts("allocation budget"):
        lane_env.buy(lane_env.scale)


def test_budget_changes_between_preview_and_buy_are_live(lane_env):
    quote = lane_env.quote(lane_env.scale)
    lane_env.set_budget(quote.totalRipe - 1)
    with boa.reverts("allocation budget"):
        lane_env.buy(lane_env.scale)

    lane_env.set_budget(quote.totalRipe)
    assert lane_env.buy(lane_env.scale) == quote.totalRipe


def test_paused_disabled_and_readiness_gates_leave_preview_math_visible(
    lane_env, governance
):
    amount = lane_env.scale
    lane_env.lane.setCanAcquireRipe(False, sender=lane_env.switchboard.address)
    quote = lane_env.quote(amount)
    assert quote.available is False
    assert quote.totalRipe > 0
    with boa.reverts("disabled"):
        lane_env.buy(amount)
    lane_env.lane.setCanAcquireRipe(True, sender=lane_env.switchboard.address)

    lane_env.lane.pause(True, sender=lane_env.switchboard.address)
    assert lane_env.quote(amount).available is False
    with boa.reverts("paused"):
        lane_env.buy(amount)
    lane_env.lane.pause(False, sender=lane_env.switchboard.address)

    lane_env.claims.pause(True, sender=lane_env.switchboard.address)
    assert lane_env.quote(amount).available is False
    with boa.reverts("mint not ready"):
        lane_env.buy(amount)
    lane_env.claims.pause(False, sender=lane_env.switchboard.address)

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
    assert lane_env.quote(amount).available is False
    with boa.reverts("mint not ready"):
        lane_env.buy(amount)


def test_purchase_requires_allowance_balance_and_exact_payment_receipt(
    lane_env, alice, charlie_token_whale
):
    amount = lane_env.scale
    lane_env.payment_token.transfer(alice, amount, sender=charlie_token_whale)
    with boa.reverts():
        lane_env.buy(amount, sender=alice)

    lane_env.payment_token.approve(lane_env.lane, MAX_UINT256, sender=alice)
    assert lane_env.buy(amount, sender=alice) > 0
    assert lane_env.claims.getNumUserPositions(alice) == 1

    with boa.reverts():
        lane_env.buy(amount, sender=alice)


def test_each_sender_buys_only_for_itself(lane_env, alice, charlie_token_whale):
    amount = lane_env.scale
    lane_env.payment_token.transfer(alice, amount, sender=charlie_token_whale)
    lane_env.payment_token.approve(lane_env.lane, amount, sender=alice)
    lane_env.buy(amount, sender=alice)
    assert lane_env.claims.getNumUserPositions(alice) == 1
    assert lane_env.claims.getNumUserPositions(lane_env.bob) == 0


def test_same_epoch_second_purchase_reuses_snapshot_and_adds_position(lane_env):
    first_quote = lane_env.quote(lane_env.scale)
    lane_env.buy(lane_env.scale)
    lane_env.set_config(seedBasePayoutRate=first_quote.basePayoutRate // 2)
    second_quote = lane_env.quote(lane_env.scale)
    lane_env.buy(lane_env.scale)

    assert second_quote.basePayoutRate == first_quote.basePayoutRate
    assert lane_env.lane.epochState().acceptedPayment == 2 * lane_env.scale
    assert lane_env.claims.getNumUserPositions(lane_env.bob) == 2
    assert lane_env.claims.nextPositionId() == 3
    assert filter_logs(lane_env.lane, "EpochInitialized") == []


def test_deadline_is_inclusive(lane_env):
    current = boa.env.evm.patch.block_number
    assert lane_env.buy(lane_env.scale, deadline=current) > 0


def test_payment_token_reentrancy_cannot_create_a_second_purchase(
    lane_factory, governance, bob
):
    token = boa.loads(REENTRANT_PAYMENT, governance.address, 18)
    ctx = lane_factory(payment_token=token, fund_buyer=False)
    amount = ctx.scale
    token.transfer(bob, 2 * amount, sender=governance.address)
    token.approve(ctx.lane, MAX_UINT256, sender=bob)
    token.arm(ctx.lane, amount, sender=governance.address)

    payout = ctx.buy(amount)
    assert payout > 0
    assert token.attackAttempted() is True
    assert token.attackSucceeded() is False
    assert token.observedAccepted() == amount
    assert ctx.lane.epochState().acceptedPayment == amount
    assert ctx.claims.getNumUserPositions(bob) == 1
    assert ctx.claims.totalAllocatedRipe() == payout
