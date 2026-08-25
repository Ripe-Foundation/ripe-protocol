import boa
import pytest

from conf_utils import filter_logs, get_boa_dev_reasons
from constants import ZERO_ADDRESS

from tests.core.instantBondLane.conftest import DEFAULT_EPOCH_LENGTH, make_config


def test_start_zero_genesis_means_now(lane_factory):
    ctx = lane_factory(auto_start=False)
    before = boa.env.evm.patch.block_number
    ctx.start(0)
    logs = filter_logs(ctx.lane, "ReserveEngineStarted")
    assert ctx.lane.isRunning() is True
    assert ctx.lane.genesisBlock() == before
    assert ctx.lane.epochLength() == DEFAULT_EPOCH_LENGTH
    assert logs[-1].genesisBlock == before
    assert logs[-1].epochLength == DEFAULT_EPOCH_LENGTH


def test_start_future_genesis_blocks_buys_and_zeros_snapshot(lane_factory):
    ctx = lane_factory(auto_start=False, unpause_lane=True)
    future = boa.env.evm.patch.block_number + 20
    ctx.start(future)
    assert ctx.lane.genesisBlock() == future
    snap = ctx.lane.getEpochSnapshot()
    assert snap.basePayoutRate == 0
    assert snap.epoch == 0

    quote = ctx.quote(ctx.scale)
    assert quote.available is False
    assert quote.epoch == 0

    with pytest.raises(boa.BoaError) as err:
        ctx.lane.acquireRipe(
            ctx.scale,
            0,
            0,
            0,
            0,
            future + 100,
            sender=ctx.bob,
        )
    assert "before genesis" in get_boa_dev_reasons(err.value)

    boa.env.time_travel(blocks=20)
    quote = ctx.quote(ctx.scale)
    assert quote.available is True
    assert quote.basePayoutRate == ctx.lane.engineConfig().seedBasePayoutRate
    payout = ctx.buy(ctx.scale)
    assert payout > 0


def test_start_past_genesis_is_allowed(lane_factory):
    ctx = lane_factory(auto_start=False)
    past = max(boa.env.evm.patch.block_number - 50, 1)
    ctx.start(past)
    assert ctx.lane.genesisBlock() == past
    epoch = (boa.env.evm.patch.block_number - past) // ctx.epoch_length
    quote = ctx.quote(ctx.scale)
    assert quote.available is True
    assert quote.epoch == epoch
    assert quote.basePayoutRate == ctx.lane.engineConfig().seedBasePayoutRate
    ctx.buy(ctx.scale)
    assert ctx.lane.epochState().epoch == epoch
    assert ctx.lane.epochState().basePayoutRate == ctx.lane.engineConfig().seedBasePayoutRate


def test_start_can_change_epoch_length(lane_factory):
    ctx = lane_factory(auto_start=False, epoch_length=100)
    assert ctx.lane.epochLength() == 100
    ctx.start(0, 250)
    assert ctx.lane.epochLength() == 250
    ctx.buy(ctx.scale)
    boa.env.time_travel(blocks=250)
    next_quote = ctx.quote(ctx.scale)
    assert next_quote.epoch == 1


def test_can_start_while_paused_but_buys_wait_for_unpause(lane_factory):
    ctx = lane_factory(auto_start=False, unpause_lane=False)
    assert ctx.lane.isPaused() is True
    ctx.start(0)
    assert ctx.lane.isRunning() is True
    with pytest.raises(boa.BoaError) as err:
        ctx.buy(ctx.scale)
    assert "paused" in get_boa_dev_reasons(err.value)
    ctx.lane.pause(False, sender=ctx.switchboard.address)
    assert ctx.buy(ctx.scale) > 0


def test_start_requires_switchboard_and_valid_length(lane_factory, alice):
    ctx = lane_factory(auto_start=False)
    with boa.reverts("no perms"):
        ctx.lane.start(0, 100, sender=alice)
    with boa.reverts("invalid epoch length"):
        ctx.lane.start(0, 0, sender=ctx.switchboard.address)
    ctx.start(0)
    with boa.reverts("already running"):
        ctx.start(0)


def test_start_requires_valid_installed_config(lane_factory, governance):
    other = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "Other",
        "OTH",
        18,
        1_000_000,
    )
    ctx = lane_factory(auto_start=False)
    ctx.lane.setPaymentToken(other.address, sender=ctx.switchboard.address)
    # 6-decimal cap/min are now illegal against an 18-decimal scale
    with boa.reverts("not configured"):
        ctx.lane.start(0, ctx.epoch_length, sender=ctx.switchboard.address)


def test_stop_clears_clock_and_epoch_but_keeps_config_and_claim_liabilities(lane_env):
    payout = lane_env.buy(lane_env.scale)
    lane_env.set_rate_override(9 * 10**17)
    assert lane_env.lane.overrideTargetBasePayoutRate() != 0

    lane_env.stop()
    logs = filter_logs(lane_env.lane, "ReserveEngineStopped")
    assert logs[-1].epochLength == lane_env.epoch_length

    assert lane_env.lane.isRunning() is False
    assert lane_env.lane.genesisBlock() == 0
    assert lane_env.lane.epochState().basePayoutRate == 0
    assert lane_env.lane.overrideTargetBasePayoutRate() == 0
    assert lane_env.claims.totalAllocatedRipe() == payout
    assert lane_env.claims.totalClaimedRipe() == 0
    assert lane_env.lane.epochLength() == lane_env.epoch_length
    assert lane_env.lane.paymentToken() == lane_env.payment_token.address

    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale)
    assert "not running" in get_boa_dev_reasons(err.value)

    with boa.reverts("not running"):
        lane_env.lane.stop(sender=lane_env.switchboard.address)


def test_stop_then_start_is_a_fresh_clock(lane_env):
    lane_env.buy(lane_env.scale)
    allocated = lane_env.claims.totalAllocatedRipe()
    lane_env.stop()
    lane_env.start(0, 80)
    assert lane_env.lane.isRunning() is True
    assert lane_env.lane.epochState().basePayoutRate == 0
    assert lane_env.claims.totalAllocatedRipe() == allocated
    assert lane_env.lane.epochLength() == 80
    lane_env.buy(lane_env.scale)
    assert lane_env.lane.epochState().epoch == 0
    assert lane_env.lane.epochState().basePayoutRate == lane_env.lane.engineConfig().seedBasePayoutRate


def test_payment_token_only_while_stopped(lane_env, governance):
    other = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "Other",
        "OTH",
        8,
        1_000_000,
    )
    assert lane_env.lane.isValidPaymentToken(other.address) is False
    with boa.reverts("running"):
        lane_env.lane.setPaymentToken(other.address, sender=lane_env.switchboard.address)

    lane_env.stop()
    assert lane_env.lane.isValidPaymentToken(other.address) is True
    lane_env.lane.setPaymentToken(other.address, sender=lane_env.switchboard.address)
    logs = filter_logs(lane_env.lane, "PaymentTokenSet")
    assert logs[-1].token == other.address
    assert logs[-1].decimals == 8
    assert logs[-1].scale == 10**8
    assert lane_env.lane.paymentToken() == other.address

    # old 6-decimal cap is illegal; install matching units then start
    scale = 10**8
    lane_env.lane.setConfig(
        make_config(scale, epoch_length=lane_env.lane.epochLength()),
        sender=lane_env.switchboard.address,
    )
    lane_env.start(0)


def test_set_payment_token_rejects_ripe_and_eoa(lane_factory, ripe_token, alice):
    ctx = lane_factory(auto_start=False)
    with boa.reverts("invalid payment token"):
        ctx.lane.setPaymentToken(ripe_token.address, sender=ctx.switchboard.address)
    with boa.reverts("invalid payment token"):
        ctx.lane.setPaymentToken(alice, sender=ctx.switchboard.address)
    with boa.reverts("invalid payment token"):
        ctx.lane.setPaymentToken(ZERO_ADDRESS, sender=ctx.switchboard.address)
