import boa
import pytest

from conf_utils import filter_logs
from constants import ZERO_ADDRESS


MAX_UINT256 = 2**256 - 1


REVERTING_DECIMALS = """
# @version 0.4.3

@view
@external
def decimals() -> uint8:
    raise "decimals unavailable"
"""


def deploy_token(governance, decimals):
    return boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "Payment Token",
        "PAY",
        decimals,
        0,
    )


@pytest.mark.parametrize("decimals", [0, 6, 18, 73])
def test_constructor_derives_payment_scale(ripe_hq, governance, decimals):
    with boa.env.anchor():
        token = deploy_token(governance.address, decimals)
        genesis = boa.env.evm.patch.block_number
        lane = boa.load(
            "contracts/core/InstantBondLane.vy",
            ripe_hq,
            token,
            genesis,
            100,
        )

        assert lane.PAYMENT_TOKEN() == token.address
        assert lane.PAYMENT_DECIMALS() == decimals
        assert lane.PAYMENT_SCALE() == 10**decimals
        assert lane.GENESIS_BLOCK() == genesis
        assert lane.EPOCH_LENGTH() == 100
        assert lane.isPaused()
        assert not lane.isInitialized()
        assert lane.configVersion() == 0
        assert lane.cumulativeMinted() == 0


def test_constructor_rejects_invalid_payment_token_and_epoch_length(
    ripe_hq, governance, alice, mock_rando_contract
):
    with boa.env.anchor():
        token = deploy_token(governance.address, 6)
        genesis = boa.env.evm.patch.block_number

        with boa.reverts("invalid payment token"):
            boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                ZERO_ADDRESS,
                genesis,
                100,
            )
        with boa.reverts("invalid payment token"):
            boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                alice,
                genesis,
                100,
            )
        with boa.reverts("invalid epoch length"):
            boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                token,
                genesis,
                0,
            )
        with boa.reverts():
            boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                mock_rando_contract,
                genesis,
                100,
            )


def test_constructor_rejects_reverting_or_excessive_decimals(ripe_hq, governance):
    with boa.env.anchor():
        genesis = boa.env.evm.patch.block_number
        reverting = boa.loads(REVERTING_DECIMALS)
        too_many = deploy_token(governance.address, 74)

        with boa.reverts("decimals unavailable"):
            boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                reverting,
                genesis,
                100,
            )
        with boa.reverts("invalid payment decimals"):
            boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                too_many,
                genesis,
                100,
            )


def test_constructor_rejects_ripe_as_payment_token(ripe_hq, ripe_token):
    with boa.env.anchor():
        with boa.reverts("payment token is ripe"):
            boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                ripe_token,
                boa.env.evm.patch.block_number,
                100,
            )


def test_valid_config_boundaries(lane_env):
    lane = lane_env.lane
    scale = lane_env.scale

    valid_cases = [
        lane_env.make_config(uLowBps=0, uHighBps=1),
        lane_env.make_config(uHighBps=10_000),
        lane_env.make_config(downBps=1, upBps=2, decayBps=1),
        lane_env.make_config(upBps=10_000),
        lane_env.make_config(decayBps=9_999),
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
    ]

    for config in valid_cases:
        assert lane.isValidConfig(config)


def test_invalid_config_matrix_is_total_and_returns_false(lane_env):
    lane = lane_env.lane
    scale = lane_env.scale
    cap = 1_000 * scale

    invalid_cases = [
        lane_env.make_config(uLowBps=8_000, uHighBps=8_000),
        lane_env.make_config(uLowBps=8_001, uHighBps=8_000),
        lane_env.make_config(uHighBps=10_001),
        lane_env.make_config(downBps=0),
        lane_env.make_config(downBps=1_000, upBps=1_000),
        lane_env.make_config(downBps=1_001, upBps=1_000),
        lane_env.make_config(upBps=10_001),
        lane_env.make_config(decayBps=0),
        lane_env.make_config(decayBps=10_000),
        lane_env.make_config(downBps=501, decayBps=500),
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
        lane_env.make_config(seedRate=2 * 10**18),
    ]

    for config in invalid_cases:
        assert lane.isValidConfig(config) is False


def test_low_decimal_bonus_intermediate_overflow_config_rejects(
    ripe_hq, governance
):
    with boa.env.anchor():
        token = deploy_token(governance.address, 0)
        lane = boa.load(
            "contracts/core/InstantBondLane.vy",
            ripe_hq,
            token,
            boa.env.evm.patch.block_number,
            100,
        )
        config = (
            True,
            1_000,
            1,
            MAX_UINT256,
            MAX_UINT256 // 10_000,
            10_000,
            8_000,
            2_000,
            1_000,
            500,
            1_000,
            4,
            100_000,
        )

        assert lane.isValidConfig(config) is False


def test_set_config_authorization_versioning_storage_and_event(lane_env, alice):
    lane = lane_env.lane
    config = lane_env.make_config()

    with boa.reverts("no perms"):
        lane.setConfig(config, 0, sender=alice)

    lane.setConfig(config, 0, sender=lane_env.switchboard.address)
    logs = filter_logs(lane, "InstantBondConfigSet")
    assert lane.configVersion() == 1
    assert tuple(lane.config()) == config

    assert len(logs) == 1
    event = logs[0]
    assert event.newVersion == 1
    assert event.canBuyNow == config[0]
    assert event.paymentCapPerEpoch == config[1]
    assert event.minPaymentAmount == config[2]
    assert event.mintBudget == config[3]
    assert event.maxEffectiveRate == config[4]
    assert event.seedRate == config[5]
    assert event.uHighBps == config[6]
    assert event.uLowBps == config[7]
    assert event.upBps == config[8]
    assert event.downBps == config[9]
    assert event.decayBps == config[10]
    assert event.maxDecayEpochs == config[11]
    assert event.maxLockBonus == config[12]

    with boa.reverts("stale config version"):
        lane.setConfig(config, 0, sender=lane_env.switchboard.address)
    with boa.reverts("invalid config"):
        lane.setConfig(
            lane_env.make_config(downBps=0),
            1,
            sender=lane_env.switchboard.address,
        )


def test_pause_and_recovery_remain_switchboard_gated(lane_env, alice):
    lane = lane_env.lane

    with boa.reverts("no perms"):
        lane.pause(True, sender=alice)
    lane.pause(True, sender=lane_env.switchboard.address)
    assert lane.isPaused()
    with boa.reverts("no change"):
        lane.pause(True, sender=lane_env.switchboard.address)

    amount = 7 * lane_env.scale
    lane_env.payment_token.transfer(lane, amount, sender=lane_env.bob)
    with boa.reverts("no perms"):
        lane.recoverFunds(alice, lane_env.payment_token, sender=alice)
    before = lane_env.payment_token.balanceOf(alice)
    lane.recoverFunds(alice, lane_env.payment_token, sender=lane_env.switchboard.address)
    assert lane_env.payment_token.balanceOf(alice) == before + amount
    assert lane_env.payment_token.balanceOf(lane) == 0


def test_recover_funds_many_recovers_each_asset_and_remains_gated(lane_env, alice):
    payment_amount = 7 * lane_env.scale
    ripe_amount = 11 * 10**18
    lane_env.payment_token.transfer(
        lane_env.lane,
        payment_amount,
        sender=lane_env.bob,
    )
    lane_env.ripe_token.transfer(
        lane_env.lane,
        ripe_amount,
        sender=lane_env.ripe_whale,
    )

    assets = [lane_env.payment_token, lane_env.ripe_token]
    with boa.reverts("no perms"):
        lane_env.lane.recoverFundsMany(alice, assets, sender=alice)

    payment_before = lane_env.payment_token.balanceOf(alice)
    ripe_before = lane_env.ripe_token.balanceOf(alice)
    lane_env.lane.recoverFundsMany(
        alice,
        assets,
        sender=lane_env.switchboard.address,
    )

    assert lane_env.payment_token.balanceOf(alice) == payment_before + payment_amount
    assert lane_env.ripe_token.balanceOf(alice) == ripe_before + ripe_amount
    assert lane_env.payment_token.balanceOf(lane_env.lane) == 0
    assert lane_env.ripe_token.balanceOf(lane_env.lane) == 0
