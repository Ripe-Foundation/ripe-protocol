from types import SimpleNamespace

import boa
import pytest
from vyper.compiler.output import build_abi_output

from conf_utils import filter_logs
from constants import (
    INSTANT_BOND_CLAIMS_HQ_ID,
    INSTANT_BOND_LANE_HQ_ID,
    ZERO_ADDRESS,
)
from tests.core.instantBondLane.conftest import (
    lane_factory,
    make_config,
    replace_config,
    travel_blocks,
)


ACTION_INSTANT_BOND_CONFIG = 1
ACTION_REMAINING_ALLOCATION_BUDGET_SET = 2
MIN_BASE_RATE = 10_000


def contract_abi():
    compiler_data = boa.load_partial(
        "contracts/config/SwitchboardFoxtrot.vy"
    ).compiler_data
    return build_abi_output(compiler_data)


def enable_actions(ctx):
    assert ctx.foxtrot.setActionTimeLockAfterSetup(
        2,
        sender=ctx.governance.address,
    )
    assert ctx.foxtrot.actionTimeLock() == 2


def assert_pending_cleared(ctx, action_id):
    assert ctx.foxtrot.hasPendingAction(action_id) is False
    assert ctx.foxtrot.actionType(action_id) == 0


def replace_hq_address(ctx, reg_id, replacement):
    assert ctx.ripe_hq.startAddressUpdateToRegistry(
        reg_id,
        replacement,
        sender=ctx.governance.address,
    )
    travel_blocks(ctx.ripe_hq.registryChangeTimeLock())
    assert ctx.ripe_hq.confirmAddressUpdateToRegistry(
        reg_id,
        sender=ctx.governance.address,
    )


@pytest.fixture
def foxtrot_env(lane_factory, switchboard, governance):
    with boa.env.anchor():
        ctx = lane_factory()
        foxtrot = boa.load(
            "contracts/config/SwitchboardFoxtrot.vy",
            ctx.ripe_hq,
            ZERO_ADDRESS,
            2,
            20,
            name="switchboard_foxtrot",
        )
        assert switchboard.startAddNewAddressToRegistry(
            foxtrot,
            "Foxtrot",
            sender=governance.address,
        )
        travel_blocks(switchboard.registryChangeTimeLock())
        foxtrot_reg_id = switchboard.confirmNewAddressToRegistry(
            foxtrot,
            sender=governance.address,
        )
        yield SimpleNamespace(
            **vars(ctx),
            foxtrot=foxtrot,
            foxtrot_reg_id=foxtrot_reg_id,
            switchboard_registry=switchboard,
        )


def test_constructor_uses_live_hq_addresses(ripe_hq, governance):
    foxtrot = boa.load(
        "contracts/config/SwitchboardFoxtrot.vy",
        ripe_hq,
        ZERO_ADDRESS,
        2,
        20,
    )
    functions = {
        item["name"] for item in contract_abi() if item.get("type") == "function"
    }
    assert "LANE" not in functions
    assert "CLAIMS" not in functions
    assert ripe_hq.getAddr(INSTANT_BOND_LANE_HQ_ID) == ZERO_ADDRESS
    assert ripe_hq.getAddr(INSTANT_BOND_CLAIMS_HQ_ID) == ZERO_ADDRESS
    with boa.reverts("invalid lane"):
        foxtrot.startInstantBond(0, 100, sender=governance.address)
    with boa.reverts("invalid claims"):
        foxtrot.setInstantBondRemainingAllocationBudget(
            1,
            sender=governance.address,
        )


def test_current_abi_exposes_timelocked_budget_and_immediate_override():
    abi = contract_abi()
    functions = {
        item["name"]: item for item in abi if item.get("type") == "function"
    }
    events = {item["name"]: item for item in abi if item.get("type") == "event"}

    assert [
        item["name"]
        for item in functions["setInstantBondRateOverride"]["inputs"]
    ] == ["_targetBasePayoutRate", "_targetEpoch"]
    assert functions["cancelInstantBondRateOverride"]["inputs"] == []
    assert [
        item["name"]
        for item in functions["setInstantBondRemainingAllocationBudget"]["inputs"]
    ] == ["_amount"]
    assert [
        item["name"] for item in events["InstantBondRateOverrideSet"]["inputs"]
    ] == ["targetEpoch", "targetBasePayoutRate"]
    assert [
        item["name"]
        for item in events["PendingInstantBondRemainingAllocationBudgetSet"][
            "inputs"
        ]
    ] == ["actionId", "confirmationBlock", "amount"]
    assert "pendingRateOverride" not in functions
    assert "setInstantBondCumulativeMinted" not in functions


def test_config_queue_execute_round_trip(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    config = replace_config(
        ctx.config,
        paymentCapPerEpoch=1_234 * ctx.scale,
        minPaymentAmount=2 * ctx.scale,
        seedBasePayoutRate=11 * 10**17,
        maxVestingBonus=4_000,
    )
    action_id = ctx.foxtrot.setInstantBondConfig(
        config,
        sender=ctx.governance.address,
    )
    pending = filter_logs(ctx.foxtrot, "PendingInstantBondConfigSet")[-1]
    assert pending.actionId == action_id
    assert pending.confirmationBlock == ctx.foxtrot.getActionConfirmationBlock(
        action_id
    )
    assert pending.seedBasePayoutRate == 11 * 10**17
    assert ctx.foxtrot.actionType(action_id) == ACTION_INSTANT_BOND_CONFIG
    assert tuple(ctx.foxtrot.pendingConfig(action_id)) == config

    assert ctx.foxtrot.executePendingAction(
        action_id,
        sender=ctx.governance.address,
    ) is False
    travel_blocks(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(
        action_id,
        sender=ctx.governance.address,
    )
    executed = filter_logs(ctx.foxtrot, "InstantBondConfigExecuted")[-1]
    assert executed.actionId == action_id
    assert tuple(ctx.lane.bondConfig()) == config
    assert tuple(ctx.foxtrot.pendingConfig(action_id)) == (0,) * 16
    assert_pending_cleared(ctx, action_id)


def test_config_queue_permissions_validation_and_last_write_wins(foxtrot_env, alice):
    ctx = foxtrot_env
    enable_actions(ctx)
    first = replace_config(ctx.config, seedBasePayoutRate=11 * 10**17)
    second = replace_config(ctx.config, seedBasePayoutRate=12 * 10**17)
    with boa.reverts("no perms"):
        ctx.foxtrot.setInstantBondConfig(first, sender=alice)
    with boa.reverts("invalid config"):
        ctx.foxtrot.setInstantBondConfig(
            replace_config(ctx.config, minDownBps=0),
            sender=ctx.governance.address,
        )
    first_id = ctx.foxtrot.setInstantBondConfig(
        first,
        sender=ctx.governance.address,
    )
    second_id = ctx.foxtrot.setInstantBondConfig(
        second,
        sender=ctx.governance.address,
    )
    travel_blocks(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(
        second_id,
        sender=ctx.governance.address,
    )
    assert ctx.lane.bondConfig().seedBasePayoutRate == 12 * 10**17
    assert ctx.foxtrot.executePendingAction(
        first_id,
        sender=ctx.governance.address,
    )
    assert ctx.lane.bondConfig().seedBasePayoutRate == 11 * 10**17


def test_config_execution_revalidates_against_live_payment_token(
    foxtrot_env,
    governance,
):
    ctx = foxtrot_env
    enable_actions(ctx)
    action_id = ctx.foxtrot.setInstantBondConfig(
        replace_config(ctx.config, minPaymentAmount=2 * ctx.scale),
        sender=ctx.governance.address,
    )
    ctx.foxtrot.stopInstantBond(sender=ctx.governance.address)
    other = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "Other",
        "OTH",
        8,
        1_000_000,
    )
    ctx.foxtrot.setInstantBondPaymentToken(
        other,
        sender=ctx.governance.address,
    )
    travel_blocks(ctx.foxtrot.actionTimeLock())
    with boa.reverts("invalid config"):
        ctx.foxtrot.executePendingAction(
            action_id,
            sender=ctx.governance.address,
        )
    assert ctx.foxtrot.hasPendingAction(action_id)


@pytest.mark.parametrize("cancel", [False, True])
def test_config_cancel_and_expiration_clear_payload(foxtrot_env, cancel):
    ctx = foxtrot_env
    enable_actions(ctx)
    action_id = ctx.foxtrot.setInstantBondConfig(
        ctx.config,
        sender=ctx.governance.address,
    )
    if cancel:
        assert ctx.foxtrot.cancelPendingAction(
            action_id,
            sender=ctx.governance.address,
        )
    else:
        travel_blocks(ctx.foxtrot.actionTimeLock() + ctx.foxtrot.expiration())
        assert ctx.foxtrot.executePendingAction(
            action_id,
            sender=ctx.governance.address,
        ) is False
    assert tuple(ctx.foxtrot.pendingConfig(action_id)) == (0,) * 16
    assert_pending_cleared(ctx, action_id)


def test_budget_queue_execute_and_reset_preserves_accounting(foxtrot_env):
    ctx = foxtrot_env
    ctx.buy(ctx.scale)
    position_id = ctx.claims.nextPositionId() - 1
    allocated = ctx.claims.totalAllocatedRipe()
    claimed = ctx.claims.totalClaimedRipe()
    enable_actions(ctx)
    action_id = ctx.foxtrot.setInstantBondRemainingAllocationBudget(
        777,
        sender=ctx.governance.address,
    )
    pending = filter_logs(
        ctx.foxtrot,
        "PendingInstantBondRemainingAllocationBudgetSet",
    )[-1]
    assert pending.actionId == action_id
    assert pending.amount == 777
    assert ctx.foxtrot.actionType(action_id) == (
        ACTION_REMAINING_ALLOCATION_BUDGET_SET
    )
    assert ctx.foxtrot.pendingRemainingAllocationBudget(action_id) == 777
    travel_blocks(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(
        action_id,
        sender=ctx.governance.address,
    )
    executed = filter_logs(
        ctx.foxtrot,
        "InstantBondRemainingAllocationBudgetExecuted",
    )[-1]
    assert executed.actionId == action_id
    assert ctx.claims.remainingAllocationBudget() == 777
    assert ctx.claims.totalAllocatedRipe() == allocated
    assert ctx.claims.totalClaimedRipe() == claimed
    position_index = ctx.claims.indexOfPosition(ctx.bob, position_id)
    assert ctx.claims.positions(ctx.bob, position_index).ripePayout != 0
    assert ctx.foxtrot.pendingRemainingAllocationBudget(action_id) == 0
    assert_pending_cleared(ctx, action_id)


def test_budget_queue_accepts_zero_and_requires_governance(foxtrot_env, alice):
    ctx = foxtrot_env
    with boa.reverts("no perms"):
        ctx.foxtrot.setInstantBondRemainingAllocationBudget(0, sender=alice)
    action_id = ctx.foxtrot.setInstantBondRemainingAllocationBudget(
        0,
        sender=ctx.governance.address,
    )
    assert ctx.foxtrot.executePendingAction(
        action_id,
        sender=ctx.governance.address,
    )
    assert ctx.claims.remainingAllocationBudget() == 0


@pytest.mark.parametrize("cancel", [False, True])
def test_budget_cancel_and_expiration_clear_payload(foxtrot_env, cancel):
    ctx = foxtrot_env
    enable_actions(ctx)
    action_id = ctx.foxtrot.setInstantBondRemainingAllocationBudget(
        123,
        sender=ctx.governance.address,
    )
    if cancel:
        assert ctx.foxtrot.cancelPendingAction(
            action_id,
            sender=ctx.governance.address,
        )
    else:
        travel_blocks(ctx.foxtrot.actionTimeLock() + ctx.foxtrot.expiration())
        assert ctx.foxtrot.executePendingAction(
            action_id,
            sender=ctx.governance.address,
        ) is False
    assert ctx.foxtrot.pendingRemainingAllocationBudget(action_id) == 0
    assert_pending_cleared(ctx, action_id)


def test_budget_action_targets_live_claims_registry_entry(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    replacement = boa.load(
        "contracts/core/InstantBondClaims.vy",
        ctx.ripe_hq,
        name="replacement_claims",
    )
    replace_hq_address(ctx, INSTANT_BOND_CLAIMS_HQ_ID, replacement)
    action_id = ctx.foxtrot.setInstantBondRemainingAllocationBudget(
        456,
        sender=ctx.governance.address,
    )
    travel_blocks(ctx.foxtrot.actionTimeLock())
    assert ctx.foxtrot.executePendingAction(
        action_id,
        sender=ctx.governance.address,
    )
    assert replacement.remainingAllocationBudget() == 456
    assert ctx.claims.remainingAllocationBudget() != 456


def test_rate_override_install_and_cancel_are_immediate(foxtrot_env, alice):
    ctx = foxtrot_env
    target = 11 * 10**17
    assert ctx.foxtrot.actionTimeLock() == 0
    with boa.reverts("no perms"):
        ctx.foxtrot.setInstantBondRateOverride(target, 0, sender=alice)
    resolved_epoch = ctx.foxtrot.setInstantBondRateOverride(
        target,
        0,
        sender=ctx.governance.address,
    )
    installed = filter_logs(ctx.foxtrot, "InstantBondRateOverrideSet")[-1]
    expected_epoch = (
        boa.env.evm.patch.block_number - ctx.lane.genesisBlock()
    ) // ctx.lane.epochLength()
    assert resolved_epoch == expected_epoch
    assert installed.targetEpoch == expected_epoch
    assert installed.targetBasePayoutRate == target
    assert ctx.lane.overrideTargetEpoch() == expected_epoch
    assert ctx.lane.overrideTargetBasePayoutRate() == target
    assert ctx.foxtrot.actionId() == 1

    with boa.reverts("no perms"):
        ctx.foxtrot.cancelInstantBondRateOverride(sender=alice)
    ctx.foxtrot.cancelInstantBondRateOverride(sender=ctx.governance.address)
    cancelled = filter_logs(
        ctx.foxtrot,
        "InstantBondRateOverrideCancelled",
    )[-1]
    assert cancelled.targetEpoch == expected_epoch
    assert cancelled.targetBasePayoutRate == target
    assert ctx.lane.overrideTargetBasePayoutRate() == 0
    assert ctx.foxtrot.actionId() == 1


def test_rate_override_validation_and_single_install(foxtrot_env):
    ctx = foxtrot_env
    with boa.reverts("invalid rate override"):
        ctx.foxtrot.setInstantBondRateOverride(
            MIN_BASE_RATE - 1,
            0,
            sender=ctx.governance.address,
        )
    ctx.foxtrot.setInstantBondRateOverride(
        11 * 10**17,
        0,
        sender=ctx.governance.address,
    )
    with boa.reverts("invalid rate override"):
        ctx.foxtrot.setInstantBondRateOverride(
            12 * 10**17,
            1,
            sender=ctx.governance.address,
        )
    ctx.foxtrot.cancelInstantBondRateOverride(sender=ctx.governance.address)
    with boa.reverts("no rate override"):
        ctx.foxtrot.cancelInstantBondRateOverride(sender=ctx.governance.address)


def test_config_execution_invalidates_installed_override(foxtrot_env):
    ctx = foxtrot_env
    ctx.foxtrot.setInstantBondRateOverride(
        11 * 10**17,
        0,
        sender=ctx.governance.address,
    )
    action_id = ctx.foxtrot.setInstantBondConfig(
        replace_config(ctx.config, maxVestingBonus=4_000),
        sender=ctx.governance.address,
    )
    assert ctx.foxtrot.executePendingAction(
        action_id,
        sender=ctx.governance.address,
    )
    assert ctx.lane.overrideTargetBasePayoutRate() == 0


def test_start_stop_payment_token_and_can_buy_are_immediate(
    foxtrot_env,
    governance,
    alice,
):
    ctx = foxtrot_env
    with boa.reverts("no perms"):
        ctx.foxtrot.stopInstantBond(sender=alice)
    ctx.foxtrot.setCanBuyNow(False, sender=ctx.governance.address)
    can_buy_event = filter_logs(ctx.foxtrot, "InstantBondCanBuyNowSet")[-1]
    assert can_buy_event.canBuyNow is False
    assert ctx.lane.canBuyNow() is False
    ctx.foxtrot.stopInstantBond(sender=ctx.governance.address)
    assert ctx.lane.isRunning() is False

    other = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "Other",
        "OTH",
        ctx.payment_token.decimals(),
        1_000_000,
    )
    ctx.foxtrot.setInstantBondPaymentToken(
        other,
        sender=ctx.governance.address,
    )
    token_event = filter_logs(ctx.foxtrot, "InstantBondPaymentTokenSet")[-1]
    assert token_event.token == other.address
    assert ctx.lane.paymentToken() == other.address

    before = boa.env.evm.patch.block_number
    ctx.foxtrot.startInstantBond(
        0,
        ctx.epoch_length,
        sender=ctx.governance.address,
    )
    started = filter_logs(ctx.foxtrot, "InstantBondStarted")[-1]
    assert started.genesisBlock == before
    assert started.epochLength == ctx.epoch_length
    assert ctx.lane.isRunning() is True


def test_immediate_actions_reject_invalid_state(foxtrot_env):
    ctx = foxtrot_env
    with boa.reverts("already running"):
        ctx.foxtrot.startInstantBond(
            0,
            ctx.epoch_length,
            sender=ctx.governance.address,
        )
    with boa.reverts("no change"):
        ctx.foxtrot.setCanBuyNow(True, sender=ctx.governance.address)
    with boa.reverts("invalid payment token"):
        ctx.foxtrot.setInstantBondPaymentToken(
            ctx.payment_token,
            sender=ctx.governance.address,
        )
    ctx.foxtrot.stopInstantBond(sender=ctx.governance.address)
    with boa.reverts("not running"):
        ctx.foxtrot.stopInstantBond(sender=ctx.governance.address)
    with boa.reverts("invalid epoch length"):
        ctx.foxtrot.startInstantBond(0, 0, sender=ctx.governance.address)


def test_immediate_start_targets_live_lane_registry_entry(foxtrot_env):
    ctx = foxtrot_env
    replacement = boa.load(
        "contracts/core/InstantBondLane.vy",
        ctx.ripe_hq,
        ctx.payment_token,
        ctx.config,
        name="replacement_lane",
    )
    replacement.pause(False, sender=ctx.switchboard.address)
    replace_hq_address(ctx, INSTANT_BOND_LANE_HQ_ID, replacement)
    ctx.foxtrot.startInstantBond(
        0,
        ctx.epoch_length,
        sender=ctx.governance.address,
    )
    assert replacement.isRunning() is True
    assert ctx.lane.genesisBlock() != replacement.genesisBlock()


def test_unknown_or_cancelled_action_cannot_execute(foxtrot_env):
    ctx = foxtrot_env
    enable_actions(ctx)
    assert ctx.foxtrot.executePendingAction(
        99,
        sender=ctx.governance.address,
    ) is False
    action_id = ctx.foxtrot.setInstantBondRemainingAllocationBudget(
        1,
        sender=ctx.governance.address,
    )
    assert ctx.foxtrot.cancelPendingAction(
        action_id,
        sender=ctx.governance.address,
    )
    assert ctx.foxtrot.executePendingAction(
        action_id,
        sender=ctx.governance.address,
    ) is False
