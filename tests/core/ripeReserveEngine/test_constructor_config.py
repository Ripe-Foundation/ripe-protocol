import boa
import pytest
from vyper.compiler.output import build_abi_output

from conf_utils import filter_logs
from constants import MAX_UINT256, ZERO_ADDRESS
from tests.core.ripeReserveEngine.conftest import (
    DEFAULT_EPOCH_LENGTH,
    MIN_BASE_PAYOUT_RATE,
    make_config,
)


MAX_EPOCH_LENGTH = MAX_UINT256 // 10_000 + 1
MAX_VESTING_LENGTH = 7_884_000

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
def test_constructor_derives_payment_scale_without_storing_decimals(
    ripe_hq, governance, decimals
):
    with boa.env.anchor():
        token = deploy_token(governance.address, decimals)
        scale = 10**decimals
        config = make_config(scale)
        lane = boa.load(
            "contracts/core/RipeReserveEngine.vy",
            ripe_hq,
            token,
            config,
        )

        assert lane.paymentToken() == token.address
        assert lane.paymentScale() == scale
        assert lane.genesisBlock() == 0
        assert lane.isRunning() is False
        assert lane.isPaused() is True
        assert lane.canAcquireRipe() is False
        assert lane.epochLength() == DEFAULT_EPOCH_LENGTH
        assert tuple(lane.engineConfig()) == config
        assert lane.overrideTargetBasePayoutRate() == 0
        assert lane.overrideTargetEpoch() == 0
        assert tuple(lane.epochState()) == (0,) * 11 + (False,)
        assert "paymentDecimals" not in {
            entry.get("name") for entry in build_abi_output(lane.compiler_data)
        }


def test_constructor_rejects_invalid_payment_tokens(
    ripe_hq, governance, ripe_token, charlie_token
):
    with boa.env.anchor():
        scale = 10 ** charlie_token.decimals()
        config = make_config(scale)

        with boa.reverts("invalid payment token"):
            boa.load(
                "contracts/core/RipeReserveEngine.vy",
                ripe_hq,
                ZERO_ADDRESS,
                config,
            )
        with boa.reverts():
            boa.load(
                "contracts/core/RipeReserveEngine.vy",
                ripe_hq,
                governance.address,
                config,
            )
        with boa.reverts("invalid payment token"):
            boa.load(
                "contracts/core/RipeReserveEngine.vy",
                ripe_hq,
                ripe_token,
                make_config(10 ** ripe_token.decimals()),
            )


def test_constructor_rejects_reverting_or_excessive_decimals(ripe_hq, governance):
    with boa.env.anchor():
        reverting = boa.loads(REVERTING_DECIMALS)
        with boa.reverts():
            boa.load(
                "contracts/core/RipeReserveEngine.vy",
                ripe_hq,
                reverting,
                make_config(1),
            )

        excessive = deploy_token(governance.address, 74)
        with boa.reverts("invalid payment token"):
            boa.load(
                "contracts/core/RipeReserveEngine.vy",
                ripe_hq,
                excessive,
                make_config(10**74),
            )


def test_constructor_rejects_invalid_config(ripe_hq, charlie_token):
    with boa.env.anchor():
        scale = 10 ** charlie_token.decimals()
        with boa.reverts("invalid config"):
            boa.load(
                "contracts/core/RipeReserveEngine.vy",
                ripe_hq,
                charlie_token,
                make_config(scale, uLowBps=0),
            )
        with boa.reverts("invalid config"):
            boa.load(
                "contracts/core/RipeReserveEngine.vy",
                ripe_hq,
                charlie_token,
                make_config(scale, minVestingLength=0),
            )


def test_epoch_length_validation_boundaries(ripe_hq, charlie_token):
    with boa.env.anchor():
        scale = 10 ** charlie_token.decimals()
        lane = boa.load(
            "contracts/core/RipeReserveEngine.vy",
            ripe_hq,
            charlie_token,
            make_config(scale, epochLength=MAX_EPOCH_LENGTH),
        )
        assert lane.epochLength() == MAX_EPOCH_LENGTH
        assert lane.isValidEpochLength(1)
        assert lane.isValidEpochLength(MAX_EPOCH_LENGTH)
        assert lane.isValidEpochLength(0) is False
        assert lane.isValidEpochLength(MAX_EPOCH_LENGTH + 1) is False


def test_valid_config_boundaries(lane_env):
    lane = lane_env.lane
    scale = lane_env.scale
    minimum_nonzero_payout = (
        scale + MIN_BASE_PAYOUT_RATE - 1
    ) // MIN_BASE_PAYOUT_RATE
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
        lane_env.make_config(maxDecayEpochs=1),
        lane_env.make_config(maxDecayEpochs=32),
        lane_env.make_config(minPaymentAmount=minimum_nonzero_payout),
        lane_env.make_config(minPaymentAmount=scale - 1),
        lane_env.make_config(minPaymentAmount=scale),
        lane_env.make_config(minPaymentAmount=1_000 * scale),
        lane_env.make_config(maxVestingBonus=0),
        lane_env.make_config(
            maxVestingBonus=100_000,
            maxAllInPayoutRate=11 * 10**18,
            seedBasePayoutRate=10**18,
            minVestingLength=100,
            maxVestingLength=1_101,
        ),
        lane_env.make_config(
            maxVestingBonus=0,
            maxAllInPayoutRate=10_000,
            seedBasePayoutRate=10_000,
        ),
        lane_env.make_config(minVestingLength=1, maxVestingLength=1),
        lane_env.make_config(
            maxVestingBonus=5_000,
            minVestingLength=100,
            maxVestingLength=151,
        ),
        lane_env.make_config(
            minVestingLength=MAX_VESTING_LENGTH,
            maxVestingLength=MAX_VESTING_LENGTH,
        ),
    ]
    for config in valid_cases:
        assert lane.isValidConfig(config)


def test_invalid_config_matrix_is_total_and_returns_false(lane_env):
    lane = lane_env.lane
    scale = lane_env.scale
    cap = lane.engineConfig().paymentCapPerEpoch
    minimum_nonzero_payout = (
        scale + MIN_BASE_PAYOUT_RATE - 1
    ) // MIN_BASE_PAYOUT_RATE
    invalid_cases = [
        lane_env.make_config(uLowBps=0),
        lane_env.make_config(uLowBps=8_000, uHighBps=8_000),
        lane_env.make_config(uLowBps=8_001, uHighBps=8_000),
        lane_env.make_config(uHighBps=10_000),
        lane_env.make_config(minUpBps=0),
        lane_env.make_config(minUpBps=1_001, maxUpBps=1_000),
        lane_env.make_config(maxUpBps=10_001),
        lane_env.make_config(minDownBps=0),
        lane_env.make_config(minDownBps=501, maxDownBps=500),
        lane_env.make_config(maxDownBps=1_000, minUpBps=1_000),
        lane_env.make_config(decayBps=0),
        lane_env.make_config(decayBps=10_000),
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
        lane_env.make_config(maxAllInPayoutRate=0),
        lane_env.make_config(maxAllInPayoutRate=MAX_UINT256 // 10_000 + 1),
        lane_env.make_config(paymentCapPerEpoch=scale - 1),
        lane_env.make_config(paymentCapPerEpoch=MAX_UINT256 // 10_000 + 1),
        lane_env.make_config(minPaymentAmount=0),
        lane_env.make_config(minPaymentAmount=minimum_nonzero_payout - 1),
        lane_env.make_config(minPaymentAmount=cap + 1),
        lane_env.make_config(maxAllInPayoutRate=MAX_UINT256 // cap + 1),
        lane_env.make_config(maxVestingBonus=100_001),
        lane_env.make_config(minVestingLength=0),
        lane_env.make_config(minVestingLength=2, maxVestingLength=1),
        lane_env.make_config(maxVestingLength=MAX_VESTING_LENGTH + 1),
        lane_env.make_config(
            maxVestingBonus=5_000,
            minVestingLength=100,
            maxVestingLength=150,
        ),
        lane_env.make_config(
            maxVestingBonus=5_001,
            minVestingLength=100,
            maxVestingLength=150,
        ),
        lane_env.make_config(
            maxVestingBonus=0,
            maxAllInPayoutRate=9_999,
            seedBasePayoutRate=9_999,
        ),
        lane_env.make_config(seedBasePayoutRate=9_999),
        lane_env.make_config(epochLength=0),
        lane_env.make_config(epochLength=MAX_EPOCH_LENGTH + 1),
        lane_env.make_config(epochLength=lane.epochLength() + 1),
    ]
    for config in invalid_cases:
        assert lane.isValidConfig(config) is False


def test_release_velocity_validator_is_strict_and_skips_equal_durations(lane_env):
    assert lane_env.lane.isValidConfig(
        lane_env.make_config(
            maxVestingBonus=5_000,
            minVestingLength=100,
            maxVestingLength=151,
        )
    )
    assert lane_env.lane.isValidConfig(
        lane_env.make_config(
            maxVestingBonus=5_000,
            minVestingLength=100,
            maxVestingLength=150,
        )
    ) is False
    assert lane_env.lane.isValidConfig(
        lane_env.make_config(
            maxVestingBonus=5_001,
            minVestingLength=100,
            maxVestingLength=150,
        )
    ) is False
    assert lane_env.lane.isValidConfig(
        lane_env.make_config(
            maxVestingBonus=100_000,
            maxAllInPayoutRate=11 * 10**18,
            seedBasePayoutRate=10**18,
            minVestingLength=100,
            maxVestingLength=100,
        )
    )


def test_set_config_is_authorized_stored_and_emitted(lane_env, alice):
    config = lane_env.make_config(
        maxVestingBonus=0,
        minVestingLength=7,
        maxVestingLength=77,
    )
    with boa.reverts("no perms"):
        lane_env.lane.setConfig(config, sender=alice)

    lane_env.lane.setConfig(config, sender=lane_env.switchboard.address)
    event = filter_logs(lane_env.lane, "ReserveEngineConfigSet")[-1]
    assert tuple(lane_env.lane.engineConfig()) == config
    assert event.maxVestingBonus == 0
    assert event.minVestingLength == 7
    assert event.maxVestingLength == 77
    assert event.epochLength == lane_env.epoch_length


def test_set_config_cannot_change_live_epoch_length(lane_env):
    with boa.reverts("invalid config"):
        lane_env.lane.setConfig(
            lane_env.make_config(epochLength=lane_env.epoch_length + 1),
            sender=lane_env.switchboard.address,
        )


def test_set_config_works_while_paused_and_invalidates_override(lane_env):
    target = 9 * 10**17
    lane_env.set_rate_override(target)
    lane_env.lane.pause(True, sender=lane_env.switchboard.address)
    config = lane_env.make_config(maxVestingBonus=0)
    lane_env.lane.setConfig(config, sender=lane_env.switchboard.address)
    invalidated = filter_logs(lane_env.lane, "RateOverrideInvalidated")[-1]
    assert tuple(lane_env.lane.engineConfig()) == config
    assert lane_env.lane.overrideTargetBasePayoutRate() == 0
    assert invalidated.targetBasePayoutRate == target


def test_set_can_acquire_ripe_is_separate_from_config(lane_env, alice):
    before = tuple(lane_env.lane.engineConfig())
    with boa.reverts("no perms"):
        lane_env.lane.setCanAcquireRipe(False, sender=alice)
    with boa.reverts("no change"):
        lane_env.lane.setCanAcquireRipe(True, sender=lane_env.switchboard.address)

    lane_env.lane.setCanAcquireRipe(False, sender=lane_env.switchboard.address)
    assert filter_logs(lane_env.lane, "CanAcquireRipeSet")[-1].canAcquireRipe is False
    assert lane_env.lane.canAcquireRipe() is False
    assert tuple(lane_env.lane.engineConfig()) == before
    with boa.reverts("disabled"):
        lane_env.buy(lane_env.scale)

    lane_env.lane.setCanAcquireRipe(True, sender=lane_env.switchboard.address)
    assert lane_env.lane.canAcquireRipe() is True
    assert lane_env.quote(lane_env.scale).available is True


def test_empty_config_is_never_valid(lane_env):
    assert lane_env.lane.isValidConfig((0,) * 16) is False
