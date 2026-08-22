import boa
import pytest

from conf_utils import filter_logs, get_boa_dev_reasons
from constants import MAX_UINT256


REENTRANT_PAYMENT = """
# @version 0.4.3

interface Lane:
    def buyNow(
        _paymentAmount: uint256,
        _requestedLock: uint256,
        _expectedEpoch: uint256,
        _minRipeOut: uint256,
        _deadlineBlock: uint256,
    ) -> uint256: nonpayable
    def epochState() -> (uint256, uint256, uint256, uint256, uint256, uint256, uint256, bool): view
    def cumulativeMinted() -> uint256: view

decimals: public(immutable(uint8))
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)
owner: public(address)
attackTarget: public(address)
attackAttempted: public(bool)
attackSucceeded: public(bool)
attackAmount: public(uint256)
observedAccepted: public(uint256)
observedMinted: public(uint256)
shouldFail: public(bool)

@deploy
def __init__(_owner: address, _decimals: uint8):
    decimals = _decimals
    self.owner = _owner
    self.totalSupply = 10**30
    self.balanceOf[_owner] = self.totalSupply

@external
def arm(_target: address, _amount: uint256, _shouldFail: bool = False):
    assert msg.sender == self.owner
    self.attackTarget = _target
    self.attackAmount = _amount
    self.shouldFail = _shouldFail
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
        state: (uint256, uint256, uint256, uint256, uint256, uint256, uint256, bool) = staticcall Lane(self.attackTarget).epochState()
        self.observedAccepted = state[5]
        self.observedMinted = staticcall Lane(self.attackTarget).cumulativeMinted()
        success: bool = False
        response: Bytes[32] = b""
        success, response = raw_call(
            self.attackTarget,
            concat(
                method_id("buyNow(uint256,uint256,uint256,uint256,uint256)"),
                convert(self.attackAmount, bytes32),
                empty(bytes32),
                empty(bytes32),
                empty(bytes32),
                convert(max_value(uint256), bytes32),
            ),
            max_outsize=32,
            revert_on_failure=False,
        )
        self.attackSucceeded = success
    if self.shouldFail:
        return False
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    return True
"""


def test_first_quote_matches_initializing_purchase_and_events(lane_env):
    amount = lane_env.scale
    quote = lane_env.quote(amount)
    assert quote.available is True
    assert quote.epoch == 0
    assert quote.rate == lane_env.lane.bondConfig().seedRate
    assert quote.remainingPayment == lane_env.lane.bondConfig().paymentCapPerEpoch
    assert quote.minPaymentAmount == amount
    assert quote.actualLock == 0
    assert quote.bonusRipe == 0
    assert quote.totalRipe == amount * quote.rate // lane_env.scale

    ripe_before = lane_env.ripe_token.balanceOf(lane_env.bob)
    funds_before = lane_env.payment_token.balanceOf(lane_env.endaoment_funds)
    payout = lane_env.buy(amount, min_ripe_out=quote.totalRipe)
    initialized = filter_logs(lane_env.lane, "EpochInitialized")
    purchased = filter_logs(lane_env.lane, "InstantBondPurchased")
    assert payout == quote.totalRipe
    assert lane_env.ripe_token.balanceOf(lane_env.bob) == ripe_before + payout
    assert (
        lane_env.payment_token.balanceOf(lane_env.endaoment_funds)
        == funds_before + amount
    )
    assert lane_env.lane.cumulativeMinted() == payout

    state = lane_env.lane.epochState()
    assert state.epoch == 0
    assert state.rate == quote.rate
    assert state.acceptedPayment == amount
    assert state.timingEligible is True
    assert initialized[-1].epoch == 0
    assert initialized[-1].rate == quote.rate
    assert purchased[-1].buyer == lane_env.bob
    assert purchased[-1].paymentAmount == amount
    assert purchased[-1].totalRipe == payout
    assert purchased[-1].actualLock == 0
    assert purchased[-1].epoch == 0


def test_getters_are_stale_until_purchase_but_snapshot_is_live(lane_env):
    live = lane_env.lane.getEpochSnapshot()
    stored = lane_env.lane.epochState()
    assert stored.rate == 0
    assert live.rate == lane_env.lane.bondConfig().seedRate
    assert live.epoch == 0

    lane_env.buy(lane_env.scale)
    assert lane_env.lane.epochState().rate == live.rate
    assert lane_env.lane.getEpochSnapshot().rate == live.rate


def test_purchase_protections_min_cap_budget_deadline_epoch_slippage(lane_env):
    amount = lane_env.scale
    quote = lane_env.quote(amount)

    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(amount - 1)
    assert "below minimum payment" in get_boa_dev_reasons(err.value)

    cap = lane_env.lane.bondConfig().paymentCapPerEpoch
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(cap + 1)
    assert "exceeds available amount" in get_boa_dev_reasons(err.value)

    with pytest.raises(boa.BoaError) as err:
        lane_env.lane.buyNow(
            amount,
            0,
            quote.epoch + 1,
            0,
            boa.env.evm.patch.block_number,
            sender=lane_env.bob,
        )
    assert "epoch moved" in get_boa_dev_reasons(err.value)

    with pytest.raises(boa.BoaError) as err:
        lane_env.lane.buyNow(
            amount,
            0,
            quote.epoch,
            0,
            boa.env.evm.patch.block_number - 1,
            sender=lane_env.bob,
        )
    assert "expired" in get_boa_dev_reasons(err.value)

    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(amount, min_ripe_out=quote.totalRipe + 1)
    assert "slippage" in get_boa_dev_reasons(err.value)


def test_full_fill_only_and_remaining_capacity(lane_env):
    cap = 10 * lane_env.scale
    lane_env.set_config(paymentCapPerEpoch=cap, minPaymentAmount=lane_env.scale)
    lane_env.buy(6 * lane_env.scale)
    remaining = lane_env.quote(lane_env.scale).remainingPayment
    assert remaining == 4 * lane_env.scale
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(5 * lane_env.scale)
    assert "exceeds available amount" in get_boa_dev_reasons(err.value)
    lane_env.buy(4 * lane_env.scale)
    assert lane_env.lane.epochState().acceptedPayment == cap
    assert lane_env.quote(lane_env.scale).remainingPayment == 0


def test_budget_is_immediate_and_cannot_drop_below_minted(lane_env):
    first = lane_env.buy(lane_env.scale)
    lane_env.set_config(mintBudget=first)
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale)
    assert "mint budget" in get_boa_dev_reasons(err.value)
    quote = lane_env.quote(lane_env.scale)
    assert quote.available is False
    assert quote.totalRipe > 0
    assert quote.budgetRemaining == 0


def test_disabled_paused_and_mint_authority_block_buys(
    lane_env, governance
):
    lane_env.set_config(canBuyNow=False)
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale)
    assert "disabled" in get_boa_dev_reasons(err.value)
    quote = lane_env.quote(lane_env.scale)
    assert quote.available is False
    assert quote.rate == lane_env.lane.bondConfig().seedRate
    lane_env.set_config(canBuyNow=True)

    lane_env.lane.pause(True, sender=lane_env.switchboard.address)
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale)
    assert "paused" in get_boa_dev_reasons(err.value)
    lane_env.lane.pause(False, sender=lane_env.switchboard.address)

    registry_lock = lane_env.ripe_hq.registryChangeTimeLock()
    lane_env.ripe_hq.initiateHqConfigChange(
        lane_env.reg_id, False, False, False, sender=governance.address
    )
    boa.env.time_travel(blocks=registry_lock)
    assert lane_env.ripe_hq.confirmHqConfigChange(
        lane_env.reg_id, sender=governance.address
    )
    quote = lane_env.quote(lane_env.scale)
    assert quote.available is False
    with pytest.raises(boa.BoaError):
        lane_env.buy(lane_env.scale)


def test_buy_requires_allowance_and_balance(lane_env, alice, charlie_token_whale):
    with pytest.raises(boa.BoaError):
        lane_env.buy(lane_env.scale, sender=alice)

    lane_env.payment_token.transfer(
        alice, lane_env.scale, sender=charlie_token_whale
    )
    with pytest.raises(boa.BoaError):
        lane_env.buy(lane_env.scale, sender=alice)

    lane_env.payment_token.approve(
        lane_env.lane, MAX_UINT256, sender=alice
    )
    assert lane_env.buy(lane_env.scale, sender=alice) > 0


def test_anyone_can_buy_only_for_self(lane_env, alice, charlie_token_whale):
    lane_env.payment_token.transfer(
        alice, 100 * lane_env.scale, sender=charlie_token_whale
    )
    lane_env.payment_token.approve(
        lane_env.lane, MAX_UINT256, sender=alice
    )
    alice_before = lane_env.ripe_token.balanceOf(alice)
    bob_before = lane_env.ripe_token.balanceOf(lane_env.bob)
    payout = lane_env.buy(lane_env.scale, sender=alice)
    assert lane_env.ripe_token.balanceOf(alice) == alice_before + payout
    assert lane_env.ripe_token.balanceOf(lane_env.bob) == bob_before


def test_same_epoch_fill_does_not_change_snapshotted_rate(lane_env):
    first = lane_env.buy(lane_env.scale)
    state = lane_env.lane.epochState()
    second = lane_env.buy(2 * lane_env.scale)
    after = lane_env.lane.epochState()
    assert first > 0 and second > 0
    assert after.rate == state.rate
    assert after.paymentCap == state.paymentCap
    assert after.minPaymentAmount == state.minPaymentAmount
    assert after.maxLockBonus == state.maxLockBonus
    assert after.epoch == state.epoch
    assert after.acceptedPayment == 3 * lane_env.scale
    assert after.weightedLateness >= state.weightedLateness


def test_deadline_is_inclusive_of_the_current_block(lane_env):
    amount = lane_env.scale
    quote = lane_env.quote(amount)
    payout = lane_env.lane.buyNow(
        amount,
        0,
        quote.epoch,
        quote.totalRipe,
        boa.env.evm.patch.block_number,
        sender=lane_env.bob,
    )
    assert payout == quote.totalRipe


def test_same_epoch_second_buy_does_not_reinitialize(lane_env):
    first = lane_env.buy(lane_env.scale)
    second = lane_env.buy(2 * lane_env.scale)
    state = lane_env.lane.epochState()
    assert state.epoch == 0
    assert state.acceptedPayment == 3 * lane_env.scale
    assert lane_env.lane.cumulativeMinted() == first + second
    assert filter_logs(lane_env.lane, "EpochInitialized") == []
    assert filter_logs(lane_env.lane, "EpochRolled") == []


def test_set_cumulative_minted_is_switchboard_gated(lane_env, alice):
    with boa.reverts("no perms"):
        lane_env.lane.setCumulativeMinted(1, sender=alice)
    with boa.reverts("exceeds mint budget"):
        lane_env.lane.setCumulativeMinted(
            lane_env.lane.bondConfig().mintBudget + 1,
            sender=lane_env.switchboard.address,
        )
    lane_env.lane.setCumulativeMinted(123, sender=lane_env.switchboard.address)
    logs = filter_logs(lane_env.lane, "CumulativeMintedSet")
    assert logs[-1].amount == 123
    assert lane_env.lane.cumulativeMinted() == 123
    assert lane_env.lane.isValidCumulativeMinted(123)
    assert not lane_env.lane.isValidCumulativeMinted(
        lane_env.lane.bondConfig().mintBudget + 1
    )


@pytest.mark.parametrize("decimals", [6, 18])
def test_payment_token_reentrancy_cannot_create_a_second_purchase(
    lane_factory,
    governance,
    decimals,
):
    token = boa.loads(REENTRANT_PAYMENT, governance.address, decimals)
    scale = 10**decimals
    token.transfer(governance.address, 0, sender=governance.address)  # no-op touch
    ctx = lane_factory(
        payment_token=token,
        fund_buyer=False,
        config_overrides={
            "paymentCapPerEpoch": 1_000 * scale,
            "minPaymentAmount": scale,
        },
    )
    # factory tried to transfer from charlie whale; this token is owned by governance
    token.transfer(ctx.bob, 100 * scale, sender=governance.address)
    token.approve(ctx.lane, MAX_UINT256, sender=ctx.bob)
    token.arm(ctx.lane.address, scale, sender=governance.address)

    payout = ctx.buy(scale)
    assert payout > 0
    assert token.attackAttempted() is True
    assert token.attackSucceeded() is False
    assert token.observedAccepted() == scale
    assert token.observedMinted() == payout
    assert ctx.lane.epochState().acceptedPayment == scale
