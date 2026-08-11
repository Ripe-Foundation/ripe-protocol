import boa
import pytest

from conf_utils import filter_logs
from constants import MAX_UINT256


MOCK_HQ = """
# @version 0.4.3

addrs: public(HashMap[uint256, address])
mintable: public(bool)

@external
def setAddr(_id: uint256, _addr: address):
    self.addrs[_id] = _addr

@external
def setMintable(_mintable: bool):
    self.mintable = _mintable

@view
@external
def getAddr(_id: uint256) -> address:
    return self.addrs[_id]

@view
@external
def isValidAddr(_addr: address) -> bool:
    return False

@view
@external
def canMintRipe(_addr: address) -> bool:
    return self.mintable
"""


MOCK_SWITCHBOARD = """
# @version 0.4.3

allowed: immutable(address)

@deploy
def __init__(_allowed: address):
    allowed = _allowed

@view
@external
def isSwitchboardAddr(_addr: address) -> bool:
    return _addr == allowed
"""


MOCK_MISSION_CONTROL = """
# @version 0.4.3

import interfaces.ConfigStructs as cs

@view
@external
def ripeGovVaultConfig(_asset: address) -> cs.RipeGovVaultConfig:
    return empty(cs.RipeGovVaultConfig)
"""


REENTRANT_PAYMENT = """
# @version 0.4.3

decimals: public(immutable(uint8))
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)
owner: public(address)
attackTarget: public(address)
attackAttempted: public(bool)
attackSucceeded: public(bool)

@deploy
def __init__(_owner: address, _decimals: uint8):
    decimals = _decimals
    self.owner = _owner
    self.totalSupply = 10**30
    self.balanceOf[_owner] = self.totalSupply

@external
def arm(_target: address):
    assert msg.sender == self.owner
    self.attackTarget = _target
    self.attackAttempted = False
    self.attackSucceeded = False
    self.allowance[self][_target] = max_value(uint256)

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
        payload: Bytes[164] = concat(
            method_id(
                "buyNow(uint256,uint256,uint256,uint256,uint256)",
                output_type=Bytes[4],
            ),
            convert(convert(1_000_000, uint256), bytes32),
            empty(bytes32),
            empty(bytes32),
            empty(bytes32),
            convert(max_value(uint256), bytes32),
        )
        success: bool = False
        response: Bytes[32] = b""
        success, response = raw_call(
            self.attackTarget,
            payload,
            max_outsize=32,
            revert_on_failure=False,
        )
        self.attackSucceeded = success

    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    return True
"""


def test_preview_zeroed_before_config_and_before_genesis(lane_env, lane_factory):
    amount = lane_env.scale
    quote = lane_env.quote(amount)
    assert not quote.available
    assert quote.epoch == 0
    assert quote.rate == 0
    assert quote.totalRipe == 0

    pre_genesis = lane_factory(start_at_genesis=False, genesis_delay=50)
    pre_genesis.set_config()
    quote = pre_genesis.quote(pre_genesis.scale)
    assert boa.env.evm.patch.block_number < pre_genesis.genesis
    assert not quote.available
    assert quote.epoch == 0
    assert quote.rate == 0
    assert quote.totalRipe == 0

    with boa.reverts("before genesis"):
        pre_genesis.buy(
            pre_genesis.scale,
            expected_epoch=0,
            deadline=pre_genesis.genesis,
        )


def test_first_quote_matches_initializing_purchase_and_events(lane_env):
    lane_env.set_config()
    amount = 25 * lane_env.scale
    quote = lane_env.quote(amount)

    assert quote.available
    assert quote.epoch == 0
    assert quote.pricingConfigVersion == 1
    assert quote.liveConfigVersion == 1
    assert quote.rate == 10**18
    assert quote.remainingPayment == 1_000 * lane_env.scale
    assert quote.minPaymentAmount == lane_env.scale
    assert quote.baseRipe == 25 * 10**18
    assert quote.bonusRipe == 0
    assert quote.totalRipe == quote.baseRipe
    assert not lane_env.lane.isInitialized()

    payment_before = lane_env.payment_token.balanceOf(lane_env.endaoment_funds)
    ripe_before = lane_env.ripe_token.balanceOf(lane_env.bob)
    payout = lane_env.buy(
        amount,
        expected_epoch=quote.epoch,
        min_ripe_out=quote.totalRipe,
    )
    logs = lane_env.lane.get_logs()

    assert payout == quote.totalRipe
    assert lane_env.payment_token.balanceOf(lane_env.endaoment_funds) == payment_before + amount
    assert lane_env.ripe_token.balanceOf(lane_env.bob) == ripe_before + payout
    assert lane_env.payment_token.balanceOf(lane_env.lane) == 0
    assert lane_env.ripe_token.balanceOf(lane_env.lane) == 0
    assert lane_env.ripe_token.allowance(lane_env.lane, lane_env.teller) == 0
    assert lane_env.lane.isInitialized()
    assert lane_env.lane.currentEpoch() == quote.epoch
    assert lane_env.lane.epochRate() == quote.rate
    assert lane_env.lane.epochPaymentCap() == quote.remainingPayment
    assert lane_env.lane.epochMinPaymentAmount() == quote.minPaymentAmount
    assert lane_env.lane.epochMaxLockBonus() == 5_000
    assert lane_env.lane.epochPricingVersion() == quote.pricingConfigVersion
    assert lane_env.lane.epochAcceptedPayment() == amount
    assert lane_env.lane.epochWeightedLateness() == 0
    assert lane_env.lane.epochTimingEligible()
    assert lane_env.lane.cumulativeMinted() == payout

    init = [log for log in logs if type(log).__name__ == "EpochInitialized"]
    purchase = [log for log in logs if type(log).__name__ == "InstantBondPurchased"]
    assert len(init) == 1
    assert len(purchase) == 1
    assert init[0].epoch == quote.epoch
    assert init[0].rate == quote.rate
    assert init[0].paymentCap == 1_000 * lane_env.scale
    assert init[0].minPaymentAmount == lane_env.scale
    assert init[0].maxLockBonus == 5_000
    assert init[0].timingEligible
    assert init[0].pricingConfigVersion == 1
    assert purchase[0].buyer == lane_env.bob
    assert purchase[0].paymentAmount == amount
    assert purchase[0].baseRipe == quote.baseRipe
    assert purchase[0].bonusRipe == 0
    assert purchase[0].totalRipe == payout
    assert purchase[0].epoch == quote.epoch
    assert purchase[0].pricingConfigVersion == 1
    assert purchase[0].liveConfigVersion == 1
    assert purchase[0].ripeGovVaultId == 0


def test_failed_first_purchase_is_fully_atomic(lane_env, alice):
    lane_env.set_config()
    amount = lane_env.scale
    quote = lane_env.quote(amount)
    payment_before = lane_env.payment_token.balanceOf(lane_env.endaoment_funds)

    with boa.reverts("epoch moved"):
        lane_env.buy(amount, expected_epoch=quote.epoch + 1)
    assert not lane_env.lane.isInitialized()
    assert lane_env.lane.cumulativeMinted() == 0

    with boa.reverts("slippage"):
        lane_env.buy(
            amount,
            expected_epoch=quote.epoch,
            min_ripe_out=quote.totalRipe + 1,
        )
    assert not lane_env.lane.isInitialized()

    lane_env.payment_token.approve(lane_env.lane, 0, sender=lane_env.bob)
    with boa.reverts():
        lane_env.buy(amount, expected_epoch=quote.epoch)
    assert not lane_env.lane.isInitialized()
    assert lane_env.lane.epochAcceptedPayment() == 0
    assert lane_env.lane.cumulativeMinted() == 0
    assert lane_env.payment_token.balanceOf(lane_env.endaoment_funds) == payment_before

    lane_env.payment_token.approve(lane_env.lane, MAX_UINT256, sender=alice)
    with boa.reverts():
        lane_env.buy(amount, expected_epoch=quote.epoch, sender=alice)
    assert not lane_env.lane.isInitialized()
    assert lane_env.ripe_token.balanceOf(alice) == 0


def test_public_getters_are_stale_until_next_successful_purchase(lane_env):
    lane_env.set_config()
    lane_env.buy(lane_env.scale)

    stored_epoch = lane_env.lane.currentEpoch()
    stored_rate = lane_env.lane.epochRate()
    stored_accepted = lane_env.lane.epochAcceptedPayment()
    stored_weighted_lateness = lane_env.lane.epochWeightedLateness()
    stored_timing_eligible = lane_env.lane.epochTimingEligible()

    boa.env.time_travel(blocks=lane_env.epoch_length)
    projected = lane_env.quote(lane_env.scale)

    assert projected.epoch == stored_epoch + 1
    assert projected.rate > stored_rate
    assert projected.remainingPayment == 1_000 * lane_env.scale
    assert lane_env.lane.currentEpoch() == stored_epoch
    assert lane_env.lane.epochRate() == stored_rate
    assert lane_env.lane.epochAcceptedPayment() == stored_accepted
    assert lane_env.lane.epochWeightedLateness() == stored_weighted_lateness
    assert lane_env.lane.epochTimingEligible() == stored_timing_eligible

    lane_env.buy(
        lane_env.scale,
        expected_epoch=projected.epoch,
        min_ripe_out=projected.totalRipe,
    )
    assert lane_env.lane.currentEpoch() == projected.epoch
    assert lane_env.lane.epochRate() == projected.rate
    assert lane_env.lane.epochAcceptedPayment() == lane_env.scale


def test_purchase_protections_minimum_cap_budget_deadline_epoch_and_slippage(lane_env):
    cap = 10 * lane_env.scale
    minimum = 2 * lane_env.scale
    lane_env.set_config(paymentCapPerEpoch=cap, minPaymentAmount=minimum)
    quote = lane_env.quote(minimum)

    with boa.reverts("below minimum payment"):
        lane_env.buy(minimum - 1, expected_epoch=quote.epoch)
    with boa.reverts("exceeds epoch cap"):
        lane_env.buy(cap + 1, expected_epoch=quote.epoch)
    with boa.reverts("expired"):
        lane_env.buy(
            minimum,
            expected_epoch=quote.epoch,
            deadline=boa.env.evm.patch.block_number - 1,
        )
    with boa.reverts("epoch moved"):
        lane_env.buy(minimum, expected_epoch=quote.epoch + 1)
    with boa.reverts("slippage"):
        lane_env.buy(
            minimum,
            expected_epoch=quote.epoch,
            min_ripe_out=quote.totalRipe + 1,
        )

    assert lane_env.lane.epochAcceptedPayment() == 0
    assert lane_env.lane.cumulativeMinted() == 0

    lane_env.buy(cap, expected_epoch=quote.epoch)
    assert lane_env.lane.epochAcceptedPayment() == cap
    assert not lane_env.quote(minimum).available
    with boa.reverts("exceeds epoch cap"):
        lane_env.buy(minimum, expected_epoch=quote.epoch)


def test_budget_is_immediate_and_cannot_drop_below_minted(lane_env):
    lane_env.set_config()
    payout = lane_env.buy(lane_env.scale)

    with boa.reverts("invalid config"):
        lane_env.set_config(mintBudget=payout - 1)

    lane_env.set_config(mintBudget=payout)
    quote = lane_env.quote(lane_env.scale)
    assert quote.budgetRemaining == 0
    assert quote.totalRipe > 0
    assert not quote.available
    with boa.reverts("mint budget"):
        lane_env.buy(lane_env.scale, expected_epoch=quote.epoch)

    lane_env.set_config(mintBudget=payout + quote.totalRipe)
    assert lane_env.quote(lane_env.scale).available


def test_availability_controls_disabled_paused_global_and_lane_minting(
    lane_env, lane_factory
):
    amount = lane_env.scale
    lane_env.set_config(canBuyNow=False)
    assert not lane_env.quote(amount).available
    with boa.reverts("disabled"):
        lane_env.buy(amount, expected_epoch=0)

    lane_env.set_config(canBuyNow=True)
    lane_env.lane.pause(True, sender=lane_env.switchboard.address)
    assert not lane_env.quote(amount).available
    with boa.reverts("paused"):
        lane_env.buy(amount, expected_epoch=0)

    lane_env.lane.pause(False, sender=lane_env.switchboard.address)
    lane_env.ripe_hq.setMintingEnabled(False, sender=lane_env.governance.address)
    assert not lane_env.quote(amount).available
    with boa.reverts("mint unavailable"):
        lane_env.buy(amount, expected_epoch=0)

    lane_env.ripe_hq.setMintingEnabled(True, sender=lane_env.governance.address)

    unregistered = lane_factory(register_lane=False)
    unregistered.set_config()
    quote = unregistered.quote(unregistered.scale)
    assert quote.totalRipe > 0
    assert not quote.available
    with boa.reverts("mint unavailable"):
        unregistered.buy(unregistered.scale, expected_epoch=quote.epoch)

    mint_disabled = lane_factory(enable_mint=False)
    mint_disabled.set_config()
    quote = mint_disabled.quote(mint_disabled.scale)
    assert not quote.available
    with boa.reverts("mint unavailable"):
        mint_disabled.buy(mint_disabled.scale, expected_epoch=quote.epoch)


def test_anyone_can_buy_only_for_self(lane_env, alice, charlie_token_whale):
    lane_env.set_config()
    amount = 3 * lane_env.scale
    lane_env.payment_token.transfer(alice, amount, sender=charlie_token_whale)
    lane_env.payment_token.approve(lane_env.lane, amount, sender=alice)

    before_alice = lane_env.ripe_token.balanceOf(alice)
    before_bob = lane_env.ripe_token.balanceOf(lane_env.bob)
    quote = lane_env.quote(amount)
    payout = lane_env.buy(
        amount,
        expected_epoch=quote.epoch,
        min_ripe_out=quote.totalRipe,
        sender=alice,
    )

    assert lane_env.ripe_token.balanceOf(alice) == before_alice + payout
    assert lane_env.ripe_token.balanceOf(lane_env.bob) == before_bob


@pytest.mark.parametrize("decimals", [6, 18])
def test_payment_token_reentrancy_cannot_create_a_second_purchase(
    lane_factory,
    charlie_token_whale,
    decimals,
):
    token = boa.loads(REENTRANT_PAYMENT, charlie_token_whale, decimals)
    ctx = lane_factory(payment_token=token)
    ctx.set_config()

    token.transfer(token, ctx.scale, sender=charlie_token_whale)
    token.arm(ctx.lane, sender=charlie_token_whale)
    amount = ctx.scale
    quote = ctx.quote(amount)
    payment_before = token.balanceOf(ctx.endaoment_funds)

    payout = ctx.buy(
        amount,
        expected_epoch=quote.epoch,
        min_ripe_out=quote.totalRipe,
    )

    assert token.attackAttempted()
    assert not token.attackSucceeded()
    assert ctx.lane.epochAcceptedPayment() == amount
    assert ctx.lane.cumulativeMinted() == payout
    assert token.balanceOf(ctx.endaoment_funds) == payment_before + amount
    assert ctx.ripe_token.balanceOf(token) == 0


def test_prospective_pricing_config_and_live_version_separation(lane_env):
    old = lane_env.set_config()
    lane_env.buy(lane_env.scale)
    old_rate = lane_env.lane.epochRate()

    new_cap = 2_000 * lane_env.scale
    new_minimum = 2 * lane_env.scale
    lane_env.set_config(
        paymentCapPerEpoch=new_cap,
        minPaymentAmount=new_minimum,
        maxLockBonus=0,
        maxEffectiveRate=3 * 10**18,
        seedRate=2 * 10**18,
    )

    running = lane_env.quote(lane_env.scale)
    assert running.pricingConfigVersion == 1
    assert running.liveConfigVersion == 2
    assert running.rate == old_rate
    assert running.minPaymentAmount == old[2]
    assert running.remainingPayment == old[1] - lane_env.scale

    boa.env.time_travel(blocks=lane_env.epoch_length)
    rolled = lane_env.quote(new_minimum)
    assert rolled.pricingConfigVersion == 2
    assert rolled.liveConfigVersion == 2
    assert rolled.remainingPayment == new_cap
    assert rolled.minPaymentAmount == new_minimum

    lane_env.buy(new_minimum, expected_epoch=rolled.epoch)
    event = filter_logs(lane_env.lane, "EpochRolled")[0]
    assert event.fromEpoch == 0
    assert event.toEpoch == 1
    assert event.oldRate == old_rate
    assert event.newRate == rolled.rate
    assert event.newPaymentCap == new_cap
    assert event.newMinPaymentAmount == new_minimum
    assert event.newMaxLockBonus == 0
    assert event.previousAcceptedPayment == lane_env.scale
    assert event.previousPaymentCap == old[1]
    assert event.previousWeightedLateness == 0
    assert event.previousTimingEligible
    assert event.pricingConfigVersion == 2


def test_one_shot_override_waits_for_next_successful_rollover_and_preview_is_pure(
    lane_env,
):
    lane_env.set_config(
        paymentCapPerEpoch=100 * lane_env.scale,
        maxLockBonus=0,
    )
    lane_env.buy(50 * lane_env.scale)
    stored_rate = lane_env.lane.epochRate()
    target_rate = 777_777_777_777_777_777

    assert lane_env.set_rate_override(target_rate) == 1
    assert lane_env.lane.rateOverride() == target_rate
    assert lane_env.lane.overrideVersion() == 1

    same_epoch = lane_env.quote(lane_env.scale)
    assert same_epoch.rate == stored_rate
    lane_env.buy(lane_env.scale, expected_epoch=same_epoch.epoch)
    assert lane_env.lane.rateOverride() == target_rate
    assert lane_env.lane.overrideVersion() == 1

    boa.env.time_travel(blocks=3 * lane_env.epoch_length)
    first_preview = lane_env.quote(lane_env.scale)
    second_preview = lane_env.quote(lane_env.scale)
    assert first_preview.rate == second_preview.rate == target_rate
    assert first_preview.epoch == 3
    assert lane_env.lane.currentEpoch() == 0
    assert lane_env.lane.rateOverride() == target_rate
    assert lane_env.lane.overrideVersion() == 1

    lane_env.lane.pause(True, sender=lane_env.switchboard.address)
    assert not lane_env.quote(lane_env.scale).available
    with boa.reverts("paused"):
        lane_env.buy(lane_env.scale, expected_epoch=first_preview.epoch)
    assert lane_env.lane.rateOverride() == target_rate
    assert lane_env.lane.overrideVersion() == 1
    assert lane_env.lane.currentEpoch() == 0
    lane_env.lane.pause(False, sender=lane_env.switchboard.address)

    payout = lane_env.buy(
        lane_env.scale,
        expected_epoch=first_preview.epoch,
        min_ripe_out=first_preview.totalRipe,
    )
    applied = filter_logs(lane_env.lane, "RateOverrideApplied")[0]
    rolled = filter_logs(lane_env.lane, "EpochRolled")[0]
    assert payout == first_preview.totalRipe
    assert lane_env.lane.currentEpoch() == 3
    assert lane_env.lane.epochRate() == target_rate
    assert lane_env.lane.rateOverride() == 0
    assert lane_env.lane.overrideVersion() == 2

    assert applied.newVersion == 2
    assert applied.fromEpoch == 0
    assert applied.toEpoch == 3
    assert applied.targetRate == target_rate
    assert applied.controllerRate == rolled.controllerRate
    assert rolled.newRate == target_rate
    assert rolled.controllerRate != target_rate


def test_events_reconstruct_config_and_epoch_history_from_indexed_keys(lane_env):
    config_events = []
    initialized_events = []
    rolled_events = []
    purchase_events = []

    config_v1 = lane_env.set_config(
        paymentCapPerEpoch=100 * lane_env.scale,
        minPaymentAmount=lane_env.scale,
        maxLockBonus=0,
    )
    config_events.extend(filter_logs(lane_env.lane, "InstantBondConfigSet"))

    first = lane_env.quote(10 * lane_env.scale)
    lane_env.buy(
        10 * lane_env.scale,
        expected_epoch=first.epoch,
        min_ripe_out=first.totalRipe,
    )
    initialized_events.extend(filter_logs(lane_env.lane, "EpochInitialized"))
    purchase_events.extend(filter_logs(lane_env.lane, "InstantBondPurchased"))

    config_v2 = lane_env.set_config(
        paymentCapPerEpoch=200 * lane_env.scale,
        minPaymentAmount=2 * lane_env.scale,
        maxLockBonus=5_000,
        maxEffectiveRate=3 * 10**18,
        seedRate=2 * 10**18,
    )
    config_events.extend(filter_logs(lane_env.lane, "InstantBondConfigSet"))

    same_epoch = lane_env.quote(5 * lane_env.scale)
    lane_env.buy(
        5 * lane_env.scale,
        expected_epoch=same_epoch.epoch,
        min_ripe_out=same_epoch.totalRipe,
    )
    purchase_events.extend(filter_logs(lane_env.lane, "InstantBondPurchased"))

    boa.env.time_travel(blocks=lane_env.epoch_length)
    second_epoch = lane_env.quote(2 * lane_env.scale)
    lane_env.buy(
        2 * lane_env.scale,
        expected_epoch=second_epoch.epoch,
        min_ripe_out=second_epoch.totalRipe,
    )
    rolled_events.extend(filter_logs(lane_env.lane, "EpochRolled"))
    purchase_events.extend(filter_logs(lane_env.lane, "InstantBondPurchased"))

    config_v3 = lane_env.set_config(
        paymentCapPerEpoch=300 * lane_env.scale,
        minPaymentAmount=3 * lane_env.scale,
        maxLockBonus=0,
        maxEffectiveRate=4 * 10**18,
        seedRate=3 * 10**18,
    )
    config_events.extend(filter_logs(lane_env.lane, "InstantBondConfigSet"))

    boa.env.time_travel(blocks=lane_env.epoch_length)
    third_epoch = lane_env.quote(3 * lane_env.scale)
    lane_env.buy(
        3 * lane_env.scale,
        expected_epoch=third_epoch.epoch,
        min_ripe_out=third_epoch.totalRipe,
    )
    rolled_events.extend(filter_logs(lane_env.lane, "EpochRolled"))
    purchase_events.extend(filter_logs(lane_env.lane, "InstantBondPurchased"))

    assert [event.newVersion for event in config_events] == [1, 2, 3]
    assert [event.paymentCapPerEpoch for event in config_events] == [
        config_v1[1],
        config_v2[1],
        config_v3[1],
    ]
    assert [
        (event.epoch, event.pricingConfigVersion)
        for event in initialized_events
    ] == [(0, 1)]
    assert [
        (event.fromEpoch, event.toEpoch, event.pricingConfigVersion)
        for event in rolled_events
    ] == [(0, 1, 2), (1, 2, 3)]
    assert [
        (event.buyer, event.epoch, event.pricingConfigVersion)
        for event in purchase_events
    ] == [
        (lane_env.bob, 0, 1),
        (lane_env.bob, 0, 1),
        (lane_env.bob, 1, 2),
        (lane_env.bob, 2, 3),
    ]
    assert [event.liveConfigVersion for event in purchase_events] == [1, 2, 2, 3]

    latest_roll = rolled_events[-1]
    assert lane_env.lane.currentEpoch() == latest_roll.toEpoch == third_epoch.epoch
    assert lane_env.lane.epochRate() == latest_roll.newRate == third_epoch.rate
    assert lane_env.lane.epochPaymentCap() == latest_roll.newPaymentCap == config_v3[1]
    assert lane_env.lane.epochMinPaymentAmount() == latest_roll.newMinPaymentAmount == config_v3[2]
    assert lane_env.lane.epochMaxLockBonus() == latest_roll.newMaxLockBonus == config_v3[14]
    assert lane_env.lane.epochPricingVersion() == latest_roll.pricingConfigVersion == 3
    assert lane_env.lane.epochAcceptedPayment() == 3 * lane_env.scale


def test_preview_is_narrow_when_endaoment_destination_is_unset(lane_env):
    hq = boa.loads(MOCK_HQ)
    switchboard = boa.loads(MOCK_SWITCHBOARD, lane_env.bob)
    mission_control = boa.loads(MOCK_MISSION_CONTROL)
    hq.setAddr(3, lane_env.ripe_token)
    hq.setAddr(5, mission_control)
    hq.setAddr(6, switchboard)
    hq.setMintable(True)

    lane = boa.load(
        "contracts/core/InstantBondLane.vy",
        hq,
        lane_env.payment_token,
        boa.env.evm.patch.block_number,
        100,
    )
    config = lane_env.make_config()
    lane.setConfig(config, 0, sender=lane_env.bob)
    lane.pause(False, sender=lane_env.bob)

    quote = lane.previewBuyNow(lane_env.scale, 0)
    assert quote.available
    assert quote.totalRipe > 0
    with boa.reverts("no destination"):
        lane.buyNow(
            lane_env.scale,
            0,
            quote.epoch,
            quote.totalRipe,
            boa.env.evm.patch.block_number,
            sender=lane_env.bob,
        )
    assert not lane.isInitialized()
    assert lane.cumulativeMinted() == 0
