from types import SimpleNamespace

import boa
import pytest

from conf_utils import filter_logs
from constants import MAX_UINT256, ZERO_ADDRESS


def travel(blocks):
    if blocks:
        boa.env.time_travel(blocks=blocks)


def make_config(scale, **overrides):
    values = {
        "canBuyNow": True,
        "paymentCapPerEpoch": 1_000 * scale,
        "minPaymentAmount": scale,
        "mintBudget": 1_000_000 * 10**18,
        "maxEffectiveRate": 2 * 10**18,
        "seedRate": 10**18,
        "uHighBps": 8_000,
        "uLowBps": 2_000,
        "upBps": 1_000,
        "downBps": 500,
        "decayBps": 1_000,
        "maxDecayEpochs": 4,
        "maxLockBonus": 5_000,
    }
    values.update(overrides)
    return (
        values["canBuyNow"],
        values["paymentCapPerEpoch"],
        values["minPaymentAmount"],
        values["mintBudget"],
        values["maxEffectiveRate"],
        values["seedRate"],
        values["uHighBps"],
        values["uLowBps"],
        values["upBps"],
        values["downBps"],
        values["decayBps"],
        values["maxDecayEpochs"],
        values["maxLockBonus"],
    )


@pytest.fixture
def foxtrot_env(
    ripe_hq,
    switchboard,
    switchboard_alpha,
    governance,
    charlie_token,
    charlie_token_whale,
    bob,
):
    with boa.env.anchor():
        scale = 10 ** charlie_token.decimals()
        registry_lock = ripe_hq.registryChangeTimeLock()
        genesis = boa.env.evm.patch.block_number + registry_lock * 2 + 5
        lane = boa.load(
            "contracts/core/InstantBondLane.vy",
            ripe_hq,
            charlie_token,
            genesis,
            100,
            name="foxtrot_test_lane",
        )

        assert ripe_hq.startAddNewAddressToRegistry(
            lane, "Foxtrot Test Lane", sender=governance.address
        )
        travel(registry_lock)
        lane_reg_id = ripe_hq.confirmNewAddressToRegistry(
            lane, sender=governance.address
        )
        ripe_hq.initiateHqConfigChange(
            lane_reg_id, False, True, False, sender=governance.address
        )
        travel(registry_lock)
        assert ripe_hq.confirmHqConfigChange(
            lane_reg_id, sender=governance.address
        )
        travel(genesis - boa.env.evm.patch.block_number)
        lane.pause(False, sender=switchboard_alpha.address)

        foxtrot = boa.load(
            "contracts/config/SwitchboardFoxtrot.vy",
            ripe_hq,
            ZERO_ADDRESS,
            2,
            20,
            lane,
            name="switchboard_foxtrot",
        )
        assert switchboard.startAddNewAddressToRegistry(
            foxtrot, "Foxtrot", sender=governance.address
        )
        travel(switchboard.registryChangeTimeLock())
        foxtrot_reg_id = switchboard.confirmNewAddressToRegistry(
            foxtrot, sender=governance.address
        )

        charlie_token.transfer(
            bob,
            10_000 * scale,
            sender=charlie_token_whale,
        )
        charlie_token.approve(lane, MAX_UINT256, sender=bob)

        yield SimpleNamespace(
            lane=lane,
            foxtrot=foxtrot,
            scale=scale,
            governance=governance,
            bob=bob,
            switchboard_alpha=switchboard_alpha,
            lane_reg_id=lane_reg_id,
            foxtrot_reg_id=foxtrot_reg_id,
            payment_token=charlie_token,
        )


def enable_actions(ctx):
    assert ctx.foxtrot.setActionTimeLockAfterSetup(sender=ctx.governance.address)
    assert ctx.foxtrot.actionTimeLock() == 2


def test_constructor_target_and_immutables(ripe_hq, governance, alice, mock_rando_contract):
    with boa.env.anchor():
        with boa.reverts("invalid lane"):
            boa.load(
                "contracts/config/SwitchboardFoxtrot.vy",
                ripe_hq,
                ZERO_ADDRESS,
                2,
                20,
                ZERO_ADDRESS,
            )
        with boa.reverts("invalid lane"):
            boa.load(
                "contracts/config/SwitchboardFoxtrot.vy",
                ripe_hq,
                ZERO_ADDRESS,
                2,
                20,
                alice,
            )

        foxtrot = boa.load(
            "contracts/config/SwitchboardFoxtrot.vy",
            ripe_hq,
            ZERO_ADDRESS,
            2,
            20,
            mock_rando_contract,
        )
        assert foxtrot.LANE() == mock_rando_contract.address
        assert foxtrot.actionId() == 1
        assert foxtrot.actionTimeLock() == 0
        assert foxtrot.expiration() == 20


def test_initiation_requires_governance_nonzero_timelock_valid_config_and_version(
    foxtrot_env, alice
):
    ctx = foxtrot_env
    config = make_config(ctx.scale)

    with boa.reverts("no perms"):
        ctx.foxtrot.setInstantBondConfig(config, 0, sender=alice)
    with boa.reverts("action time lock not set"):
        ctx.foxtrot.setInstantBondConfig(config, 0, sender=ctx.governance.address)

    enable_actions(ctx)
    with boa.reverts("invalid config"):
        ctx.foxtrot.setInstantBondConfig(
            make_config(ctx.scale, downBps=0),
            0,
            sender=ctx.governance.address,
        )
    with boa.reverts("stale config version"):
        ctx.foxtrot.setInstantBondConfig(
            config,
            1,
            sender=ctx.governance.address,
        )


def test_pending_config_round_trip_and_execution_readback(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    config = make_config(
        ctx.scale,
        paymentCapPerEpoch=1_234 * ctx.scale,
        minPaymentAmount=2 * ctx.scale,
        mintBudget=987_654 * 10**18,
        maxEffectiveRate=7 * 10**18,
        seedRate=3 * 10**18,
        uHighBps=8_765,
        uLowBps=1_234,
        upBps=777,
        downBps=222,
        decayBps=333,
        maxDecayEpochs=17,
        maxLockBonus=4_321,
    )

    action_id = ctx.foxtrot.setInstantBondConfig(
        config, 0, sender=ctx.governance.address
    )
    pending_event = filter_logs(ctx.foxtrot, "PendingInstantBondConfigSet")[0]
    pending = ctx.foxtrot.pendingConfig(action_id)

    assert action_id == 1
    assert tuple(pending.config) == config
    assert pending.expectedVersion == 0
    assert pending_event.actionId == action_id
    assert pending_event.confirmationBlock == ctx.foxtrot.getActionConfirmationBlock(
        action_id
    )
    assert pending_event.expectedVersion == 0
    assert pending_event.paymentCapPerEpoch == config[1]
    assert pending_event.minPaymentAmount == config[2]
    assert pending_event.mintBudget == config[3]
    assert pending_event.maxEffectiveRate == config[4]
    assert pending_event.seedRate == config[5]
    assert pending_event.uHighBps == config[6]
    assert pending_event.uLowBps == config[7]
    assert pending_event.upBps == config[8]
    assert pending_event.downBps == config[9]
    assert pending_event.decayBps == config[10]
    assert pending_event.maxDecayEpochs == config[11]
    assert pending_event.maxLockBonus == config[12]

    assert not ctx.foxtrot.executePendingAction(
        action_id, sender=ctx.governance.address
    )
    assert ctx.foxtrot.hasPendingAction(action_id)

    travel(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(
        action_id, sender=ctx.governance.address
    )
    executed = filter_logs(ctx.foxtrot, "InstantBondConfigExecuted")[0]
    assert executed.actionId == action_id
    assert executed.newVersion == ctx.lane.configVersion() == 1
    assert tuple(ctx.lane.config()) == config
    assert not ctx.foxtrot.hasPendingAction(action_id)
    cleared = ctx.foxtrot.pendingConfig(action_id)
    assert cleared.expectedVersion == 0
    assert tuple(cleared.config) == (False,) + (0,) * 12


def test_stale_parallel_action_reverts_at_lane_and_can_be_cancelled(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    first = ctx.foxtrot.setInstantBondConfig(
        make_config(ctx.scale), 0, sender=ctx.governance.address
    )
    second = ctx.foxtrot.setInstantBondConfig(
        make_config(ctx.scale, mintBudget=2_000_000 * 10**18),
        0,
        sender=ctx.governance.address,
    )
    travel(ctx.foxtrot.actionTimeLock())

    assert ctx.foxtrot.executePendingAction(first, sender=ctx.governance.address)
    with boa.reverts("stale config version"):
        ctx.foxtrot.executePendingAction(second, sender=ctx.governance.address)
    assert ctx.foxtrot.hasPendingAction(second)
    assert ctx.foxtrot.cancelPendingAction(second, sender=ctx.governance.address)
    assert not ctx.foxtrot.hasPendingAction(second)


def test_out_of_order_parallel_execution_makes_earlier_action_stale(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    first = ctx.foxtrot.setInstantBondConfig(
        make_config(ctx.scale), 0, sender=ctx.governance.address
    )
    second_config = make_config(
        ctx.scale,
        mintBudget=2_000_000 * 10**18,
        maxDecayEpochs=17,
    )
    second = ctx.foxtrot.setInstantBondConfig(
        second_config, 0, sender=ctx.governance.address
    )
    travel(ctx.foxtrot.actionTimeLock())

    assert ctx.foxtrot.executePendingAction(second, sender=ctx.governance.address)
    assert tuple(ctx.lane.config()) == second_config
    assert ctx.lane.configVersion() == 1
    with boa.reverts("stale config version"):
        ctx.foxtrot.executePendingAction(first, sender=ctx.governance.address)
    assert ctx.foxtrot.hasPendingAction(first)
    assert ctx.foxtrot.cancelPendingAction(first, sender=ctx.governance.address)


def test_cancel_permissions_cleanup_and_event(foxtrot_env, alice):
    ctx = foxtrot_env
    enable_actions(ctx)
    action_id = ctx.foxtrot.setInstantBondConfig(
        make_config(ctx.scale), 0, sender=ctx.governance.address
    )

    with boa.reverts("no perms"):
        ctx.foxtrot.cancelPendingAction(action_id, sender=alice)
    assert ctx.foxtrot.cancelPendingAction(
        action_id, sender=ctx.governance.address
    )
    cancelled = filter_logs(ctx.foxtrot, "InstantBondConfigCancelled")[0]
    assert cancelled.actionId == action_id
    assert not ctx.foxtrot.hasPendingAction(action_id)
    assert ctx.foxtrot.pendingConfig(action_id).expectedVersion == 0
    with boa.reverts("cannot cancel action"):
        ctx.foxtrot.cancelPendingAction(action_id, sender=ctx.governance.address)


def test_expired_execution_auto_cancels_both_pending_records(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    action_id = ctx.foxtrot.setInstantBondConfig(
        make_config(ctx.scale), 0, sender=ctx.governance.address
    )
    pending_action = ctx.foxtrot.pendingActions(action_id)
    travel(pending_action.expiration - boa.env.evm.patch.block_number)

    assert ctx.foxtrot.isExpired(action_id)
    assert not ctx.foxtrot.executePendingAction(
        action_id, sender=ctx.governance.address
    )
    cancelled = filter_logs(ctx.foxtrot, "InstantBondConfigCancelled")[0]
    assert cancelled.actionId == action_id
    assert not ctx.foxtrot.hasPendingAction(action_id)
    assert ctx.foxtrot.pendingConfig(action_id).expectedVersion == 0


def test_execution_revalidates_budget_after_intervening_purchase(foxtrot_env):
    ctx = foxtrot_env
    initial = make_config(ctx.scale)
    ctx.lane.setConfig(initial, 0, sender=ctx.switchboard_alpha.address)
    enable_actions(ctx)

    proposed = make_config(ctx.scale, mintBudget=2 * 10**18)
    action_id = ctx.foxtrot.setInstantBondConfig(
        proposed, 1, sender=ctx.governance.address
    )

    amount = 3 * ctx.scale
    quote = ctx.lane.previewBuyNow(amount, 0)
    assert quote.totalRipe == 3 * 10**18
    ctx.lane.buyNow(
        amount,
        0,
        quote.epoch,
        quote.totalRipe,
        boa.env.evm.patch.block_number,
        sender=ctx.bob,
    )
    travel(ctx.foxtrot.actionTimeLock())

    with boa.reverts("invalid config"):
        ctx.foxtrot.executePendingAction(action_id, sender=ctx.governance.address)
    assert ctx.lane.configVersion() == 1
    assert ctx.foxtrot.hasPendingAction(action_id)
    assert ctx.foxtrot.pendingConfig(action_id).expectedVersion == 1
