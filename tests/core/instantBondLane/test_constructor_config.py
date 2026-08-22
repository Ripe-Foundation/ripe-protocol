import boa
import pytest

from conf_utils import filter_logs, get_boa_dev_reasons
from constants import MAX_UINT256, ZERO_ADDRESS

from tests.core.instantBondLane.conftest import DEFAULT_EPOCH_LENGTH, make_config


MAX_EPOCH_LENGTH = MAX_UINT256 // 10_000 + 1

REVERTING_DECIMALS = """
# @version 0.4.3

@view
@external
def decimals() -> uint8:
    raise "decimals unavailable"
"""


def deploy_token(governance, decimals, supply=0):
    return boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "Payment Token",
        "PAY",
        decimals,
        supply,
    )


@pytest.mark.parametrize("decimals", [0, 6, 18, 73])
def test_constructor_derives_payment_scale(ripe_hq, governance, decimals):
    with boa.env.anchor():
        token = deploy_token(governance.address, decimals)
        scale = 10**decimals
        config = make_config(scale)
        lane = boa.load(
            "contracts/core/InstantBondLane.vy",
            ripe_hq,
            token,
            config,
        )

        assert lane.paymentToken() == token.address
        assert lane.paymentDecimals() == decimals
        assert lane.paymentScale() == scale
        assert lane.genesisBlock() == 0
        assert lane.isRunning() is False
        assert lane.epochLength() == DEFAULT_EPOCH_LENGTH
        assert tuple(lane.bondConfig()) == config
        assert lane.cumulativeMinted() == 0
        assert lane.rateOverride() == 0
        assert lane.epochState().rate == 0


def test_constructor_starts_paused_and_not_running(ripe_hq, governance, charlie_token):
    with boa.env.anchor():
        scale = 10 ** charlie_token.decimals()
        lane = boa.load(
            "contracts/core/InstantBondLane.vy",
            ripe_hq,
            charlie_token,
            make_config(scale),
        )
        assert lane.isPaused() is True
        assert lane.isRunning() is False
        assert lane.genesisBlock() == 0


def test_constructor_rejects_invalid_payment_token(
    ripe_hq, governance, ripe_token, charlie_token
):
    with boa.env.anchor():
        scale = 10 ** charlie_token.decimals()
        config = make_config(scale)

        with boa.reverts("invalid payment token"):
            boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                ZERO_ADDRESS,
                config,
            )
        with boa.reverts("invalid payment token"):
            boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                ripe_token,
                make_config(10 ** ripe_token.decimals()),
            )


def test_constructor_rejects_reverting_or_excessive_decimals(ripe_hq, governance):
    with boa.env.anchor():
        reverting = boa.loads(REVERTING_DECIMALS)
        with boa.reverts():
            boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                reverting,
                make_config(1),
            )

        excessive = deploy_token(governance.address, 74)
        with boa.reverts("invalid payment token"):
            boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                excessive,
                make_config(10**74),
            )


def test_constructor_rejects_invalid_config(ripe_hq, charlie_token):
    with boa.env.anchor():
        scale = 10 ** charlie_token.decimals()
        with boa.reverts("invalid config"):
            boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                charlie_token,
                make_config(scale, uLowBps=0),
            )
        with boa.reverts("invalid config"):
            boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                charlie_token,
                make_config(scale, epochLength=0),
            )


def test_constructor_accepts_largest_overflow_safe_epoch_length(
    ripe_hq, charlie_token
):
    with boa.env.anchor():
        scale = 10 ** charlie_token.decimals()
        config = make_config(scale, epochLength=MAX_EPOCH_LENGTH)
        lane = boa.load(
            "contracts/core/InstantBondLane.vy",
            ripe_hq,
            charlie_token,
            config,
        )
        assert lane.epochLength() == MAX_EPOCH_LENGTH
        assert lane.isValidEpochLength(MAX_EPOCH_LENGTH)
        assert not lane.isValidEpochLength(0)
        assert not lane.isValidEpochLength(MAX_EPOCH_LENGTH + 1)


def test_valid_config_boundaries(lane_env):
    lane = lane_env.lane
    scale = lane_env.scale

    valid_cases = [
        lane_env.make_config(uLowBps=1, uHighBps=2),
        lane_env.make_config(uHighBps=9_999),
        lane_env.make_config(
            minDownBps=1,
            maxDownBps=1,
            minUpBps=2,
            maxUpBps=2,
            decayBps=1,
        ),
        lane_env.make_config(maxUpBps=10_000),
        lane_env.make_config(decayBps=909),
        lane_env.make_config(
            minUpBps=10_000,
            maxUpBps=10_000,
            minDownBps=1,
            maxDownBps=1,
            decayBps=5_000,
        ),
        lane_env.make_config(maxDecayEpochs=1),
        lane_env.make_config(maxDecayEpochs=32),
        lane_env.make_config(minPaymentAmount=scale),
        lane_env.make_config(minPaymentAmount=1_000 * scale),
        lane_env.make_config(maxLockBonus=0),
        lane_env.make_config(
            maxLockBonus=100_000,
            maxEffectiveRate=11 * 10**18,
            seedRate=10**18,
        ),
        lane_env.make_config(
            maxLockBonus=0,
            maxEffectiveRate=10_000,
            seedRate=10_000,
        ),
        lane_env.make_config(mintBudget=0),
        lane_env.make_config(minLockDuration=0),
        lane_env.make_config(minLockDuration=1_000),
    ]

    for config in valid_cases:
        assert lane.isValidConfig(config)


def test_invalid_config_matrix_is_total_and_returns_false(lane_env):
    lane = lane_env.lane
    scale = lane_env.scale
    cap = 1_000 * scale

    invalid_cases = [
        lane_env.make_config(uLowBps=0),
        lane_env.make_config(uLowBps=8_000, uHighBps=8_000),
        lane_env.make_config(uLowBps=8_001, uHighBps=8_000),
        lane_env.make_config(uHighBps=10_000),
        lane_env.make_config(uHighBps=10_001),
        lane_env.make_config(minUpBps=0),
        lane_env.make_config(minUpBps=1_001, maxUpBps=1_000),
        lane_env.make_config(maxUpBps=10_001),
        lane_env.make_config(minDownBps=0),
        lane_env.make_config(minDownBps=501, maxDownBps=500),
        lane_env.make_config(maxDownBps=1_000, minUpBps=1_000),
        lane_env.make_config(decayBps=0),
        lane_env.make_config(decayBps=10_000),
        lane_env.make_config(decayBps=910),
        lane_env.make_config(maxDownBps=501, decayBps=500),
        lane_env.make_config(
            minUpBps=1,
            maxUpBps=1,
            minDownBps=1,
            maxDownBps=1,
            decayBps=1,
        ),
        lane_env.make_config(maxDecayEpochs=0),
        lane_env.make_config(maxDecayEpochs=33),
        lane_env.make_config(maxEffectiveRate=0),
        lane_env.make_config(maxEffectiveRate=MAX_UINT256 // 10_000 + 1),
        lane_env.make_config(paymentCapPerEpoch=scale - 1),
        lane_env.make_config(paymentCapPerEpoch=MAX_UINT256 // 10_000 + 1),
        lane_env.make_config(minPaymentAmount=scale - 1),
        lane_env.make_config(minPaymentAmount=cap + 1),
        lane_env.make_config(maxEffectiveRate=MAX_UINT256 // cap + 1),
        lane_env.make_config(maxLockBonus=100_001),
        lane_env.make_config(
            maxLockBonus=0,
            maxEffectiveRate=9_999,
            seedRate=9_999,
        ),
        lane_env.make_config(seedRate=9_999),
        lane_env.make_config(epochLength=0),
        lane_env.make_config(epochLength=MAX_EPOCH_LENGTH + 1),
        lane_env.make_config(epochLength=lane.epochLength() + 1),
    ]

    for config in invalid_cases:
        assert lane.isValidConfig(config) is False


def test_set_config_cannot_change_live_epoch_length(lane_env):
    with boa.reverts("invalid config"):
        lane_env.lane.setConfig(
            lane_env.make_config(epochLength=lane_env.epoch_length + 1),
            sender=lane_env.switchboard.address,
        )


def test_set_config_cannot_cut_budget_below_minted(lane_env):
    lane_env.buy(lane_env.scale)
    minted = lane_env.lane.cumulativeMinted()
    assert minted > 0
    with boa.reverts("invalid config"):
        lane_env.set_config(mintBudget=minted - 1)
    lane_env.set_config(mintBudget=minted)
    assert lane_env.lane.bondConfig().mintBudget == minted


def test_set_config_authorization_storage_and_event(lane_env, alice):
    with boa.reverts("no perms"):
        lane_env.lane.setConfig(lane_env.make_config(), sender=alice)

    config = lane_env.make_config(maxLockBonus=0, canBuyNow=True)
    lane_env.lane.setConfig(config, sender=lane_env.switchboard.address)
    logs = filter_logs(lane_env.lane, "InstantBondConfigSet")
    stored = tuple(lane_env.lane.bondConfig())
    assert stored == config
    assert len(logs) == 1
    event = logs[0]
    assert event.canBuyNow is True
    assert event.maxLockBonus == 0
    assert event.epochLength == lane_env.epoch_length
    assert event.minLockDuration == 0


def test_pause_and_recovery_remain_switchboard_gated(lane_env, alice):
    with boa.reverts("no perms"):
        lane_env.lane.pause(True, sender=alice)

    lane_env.lane.pause(True, sender=lane_env.switchboard.address)
    assert lane_env.lane.isPaused() is True
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale)
    assert "paused" in get_boa_dev_reasons(err.value)

    lane_env.lane.pause(False, sender=lane_env.switchboard.address)
    payout = lane_env.buy(lane_env.scale)
    assert payout > 0


def test_set_config_last_write_wins_and_works_while_paused(lane_env):
    first = lane_env.set_config(maxLockBonus=1_000)
    second = lane_env.make_config(maxLockBonus=0)
    lane_env.lane.pause(True, sender=lane_env.switchboard.address)
    lane_env.lane.setConfig(second, sender=lane_env.switchboard.address)
    assert tuple(lane_env.lane.bondConfig()) == second
    assert tuple(lane_env.lane.bondConfig()) != first
    lane_env.lane.pause(False, sender=lane_env.switchboard.address)
    assert lane_env.quote(lane_env.scale).available is True


def test_empty_config_is_never_valid(lane_env):
    empty = (False,) + (0,) * 16
    assert lane_env.lane.isValidConfig(empty) is False


def test_set_can_buy_now_toggles_only_the_switch(lane_env, alice):
    with boa.reverts("no perms"):
        lane_env.lane.setCanBuyNow(False, sender=alice)
    with boa.reverts("no change"):
        lane_env.lane.setCanBuyNow(True, sender=lane_env.switchboard.address)

    before = tuple(lane_env.lane.bondConfig())
    lane_env.buy(lane_env.scale)
    lane_env.set_rate_override(9 * 10**17)

    lane_env.lane.setCanBuyNow(False, sender=lane_env.switchboard.address)
    logs = filter_logs(lane_env.lane, "CanBuyNowSet")
    assert logs[-1].canBuyNow is False
    after = tuple(lane_env.lane.bondConfig())
    assert after[0] is False
    assert after[1:] == before[1:]
    assert lane_env.lane.rateOverride() == 9 * 10**17

    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale)
    assert "disabled" in get_boa_dev_reasons(err.value)
    quote = lane_env.quote(lane_env.scale)
    assert quote.available is False
    assert quote.rate == lane_env.lane.epochState().rate

    lane_env.lane.setCanBuyNow(True, sender=lane_env.switchboard.address)
    assert filter_logs(lane_env.lane, "CanBuyNowSet")[-1].canBuyNow is True
    assert lane_env.quote(lane_env.scale).available is True
    assert lane_env.buy(lane_env.scale) > 0
    assert lane_env.lane.rateOverride() == 9 * 10**17
