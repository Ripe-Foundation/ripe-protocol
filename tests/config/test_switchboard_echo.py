import pytest
import boa

from constants import ZERO_ADDRESS
from conf_utils import filter_logs


###################################
# EndaomentPSM Function Tests
###################################


def test_switchboard_echo_psm_lite_access_deposit_to_yield(
    switchboard_echo,
    alice,
    bob,
    sally,
    mission_control,
):
    """Test access control for depositToYieldInPsm (lite action)"""
    # Users without lite access should be rejected
    with boa.reverts("no perms"):
        switchboard_echo.depositToYieldInPsm(sender=alice)

    with boa.reverts("no perms"):
        switchboard_echo.depositToYieldInPsm(sender=bob)

    # Give sally lite access
    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_echo.address)

    # Sally should now be able to call (will fail in PSM mock, but passes access control)
    # Note: This would succeed with a proper PSM mock


def test_switchboard_echo_psm_lite_access_withdraw_from_yield(
    switchboard_echo,
    alice,
    bob,
    sally,
    mission_control,
):
    """Test access control for withdrawFromYieldInPsm (lite action)"""
    # Users without lite access should be rejected
    with boa.reverts("no perms"):
        switchboard_echo.withdrawFromYieldInPsm(sender=alice)

    with boa.reverts("no perms"):
        switchboard_echo.withdrawFromYieldInPsm(100, False, False, sender=bob)

    # Give sally lite access
    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_echo.address)

    # Sally should now be able to call (will fail in PSM mock, but passes access control)


def test_switchboard_echo_psm_lite_access_transfer_usdc(
    switchboard_echo,
    alice,
    bob,
    sally,
    mission_control,
):
    """Test access control for transferUsdcToEndaomentFundsInPsm (lite action)"""
    # Users without lite access should be rejected
    with boa.reverts("no perms"):
        switchboard_echo.transferUsdcToEndaomentFundsInPsm(100, sender=alice)

    with boa.reverts("no perms"):
        switchboard_echo.transferUsdcToEndaomentFundsInPsm(200, sender=bob)

    # Give sally lite access
    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_echo.address)

    # Sally should now be able to call (will fail in PSM mock, but passes access control)


def test_switchboard_echo_psm_set_can_mint_access_control(
    switchboard_echo,
    alice,
    bob,
    governance,
):
    """Test access control for setPsmCanMint - governance required when setting to True"""
    # Non-governance users should be rejected when setting to True
    with boa.reverts("no perms"):
        switchboard_echo.setPsmCanMint(True, sender=alice)

    with boa.reverts("no perms"):
        switchboard_echo.setPsmCanMint(True, sender=bob)

    # Governance should be able to set to True
    action_id = switchboard_echo.setPsmCanMint(True, sender=governance.address)
    assert action_id > 0


def test_switchboard_echo_psm_set_can_mint_conditional_access(
    switchboard_echo,
    alice,
    sally,
    mission_control,
    governance,
):
    """Test conditional access for setPsmCanMint - lite access allowed when setting to False"""
    # Non-lite user cannot set to False
    with boa.reverts("no perms"):
        switchboard_echo.setPsmCanMint(False, sender=alice)

    # Give sally lite access
    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_echo.address)

    # Sally with lite access should be able to set to False
    action_id = switchboard_echo.setPsmCanMint(False, sender=sally)
    assert action_id > 0

    # Governance should also be able to set to False
    action_id2 = switchboard_echo.setPsmCanMint(False, sender=governance.address)
    assert action_id2 > 0


def test_switchboard_echo_psm_set_can_mint_timelock_flow(
    switchboard_echo,
    governance,
):
    """Test timelock flow for setPsmCanMint"""
    # Create pending action
    action_id = switchboard_echo.setPsmCanMint(True, sender=governance.address)

    # Verify event was emitted
    logs = filter_logs(switchboard_echo, "PendingPsmSetCanMintAction")
    assert len(logs) == 1
    assert logs[0].canMint == True
    assert logs[0].actionId == action_id

    # Verify action is stored correctly
    action_type_value = 2**7  # PSM_SET_CAN_MINT is the 8th flag (index 7) in SwitchboardEcho
    assert switchboard_echo.actionType(action_id) == action_type_value
    stored_action = switchboard_echo.pendingPsmSetCanMintActions(action_id)
    assert stored_action[0] == True  # canMint field

    # Execution should fail before timelock
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert not result

    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())

    # Now execution should succeed
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert result

    # Verify action was cleared
    assert switchboard_echo.actionType(action_id) == 0


def test_switchboard_echo_psm_set_can_redeem_conditional_access(
    switchboard_echo,
    alice,
    sally,
    mission_control,
    governance,
):
    """Test conditional access for setPsmCanRedeem - lite access allowed when setting to False"""
    # Non-lite user cannot set to False
    with boa.reverts("no perms"):
        switchboard_echo.setPsmCanRedeem(False, sender=alice)

    # Give sally lite access
    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_echo.address)

    # Sally with lite access should be able to set to False
    action_id = switchboard_echo.setPsmCanRedeem(False, sender=sally)
    assert action_id > 0

    # Non-lite user cannot set to True
    with boa.reverts("no perms"):
        switchboard_echo.setPsmCanRedeem(True, sender=alice)

    # Governance should be able to set to True
    action_id2 = switchboard_echo.setPsmCanRedeem(True, sender=governance.address)
    assert action_id2 > 0


def test_switchboard_echo_psm_set_should_auto_deposit_conditional_access(
    switchboard_echo,
    alice,
    sally,
    mission_control,
    governance,
):
    """Test conditional access for setPsmShouldAutoDeposit - lite access allowed when setting to False"""
    # Non-lite user cannot set to False
    with boa.reverts("no perms"):
        switchboard_echo.setPsmShouldAutoDeposit(False, sender=alice)

    # Give sally lite access
    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_echo.address)

    # Sally with lite access should be able to set to False
    action_id = switchboard_echo.setPsmShouldAutoDeposit(False, sender=sally)
    assert action_id > 0

    # Non-lite user cannot set to True
    with boa.reverts("no perms"):
        switchboard_echo.setPsmShouldAutoDeposit(True, sender=alice)

    # Governance should be able to set to True
    action_id2 = switchboard_echo.setPsmShouldAutoDeposit(True, sender=governance.address)
    assert action_id2 > 0


def test_switchboard_echo_psm_set_mint_fee_access_control(
    switchboard_echo,
    alice,
    bob,
    governance,
):
    """Test access control for setPsmMintFee - governance required"""
    # Non-governance users should be rejected
    with boa.reverts("no perms"):
        switchboard_echo.setPsmMintFee(100, sender=alice)

    with boa.reverts("no perms"):
        switchboard_echo.setPsmMintFee(200, sender=bob)

    # Governance should be able to call
    action_id = switchboard_echo.setPsmMintFee(150, sender=governance.address)
    assert action_id > 0


def test_switchboard_echo_psm_set_mint_fee_timelock_flow(
    switchboard_echo,
    governance,
):
    """Test timelock flow for setPsmMintFee"""
    fee = 100

    # Create pending action
    action_id = switchboard_echo.setPsmMintFee(fee, sender=governance.address)

    # Verify event was emitted
    logs = filter_logs(switchboard_echo, "PendingPsmSetMintFeeAction")
    assert len(logs) == 1
    assert logs[0].fee == fee
    assert logs[0].actionId == action_id

    # Verify action is stored
    stored_action = switchboard_echo.pendingPsmSetMintFeeActions(action_id)
    assert stored_action[0] == fee

    # Execution should fail before timelock
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert not result

    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())

    # Now execution should succeed
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert result


def test_switchboard_echo_psm_update_mint_allowlist_access_control(
    switchboard_echo,
    alice,
    bob,
    governance,
):
    """Test access control for updatePsmMintAllowlist"""
    user = alice

    # Non-governance users should be rejected
    with boa.reverts("no perms"):
        switchboard_echo.updatePsmMintAllowlist(user, True, sender=alice)

    with boa.reverts("no perms"):
        switchboard_echo.updatePsmMintAllowlist(user, False, sender=bob)

    # Governance should be able to call
    action_id = switchboard_echo.updatePsmMintAllowlist(user, True, sender=governance.address)
    assert action_id > 0


def test_switchboard_echo_psm_update_mint_allowlist_parameter_validation(
    switchboard_echo,
    governance,
):
    """Test parameter validation for updatePsmMintAllowlist"""
    # Empty address should be rejected
    with boa.reverts("invalid user"):
        switchboard_echo.updatePsmMintAllowlist(ZERO_ADDRESS, True, sender=governance.address)


def test_switchboard_echo_psm_update_redeem_allowlist_parameter_validation(
    switchboard_echo,
    governance,
):
    """Test parameter validation for updatePsmRedeemAllowlist"""
    # Empty address should be rejected
    with boa.reverts("invalid user"):
        switchboard_echo.updatePsmRedeemAllowlist(ZERO_ADDRESS, True, sender=governance.address)


def test_switchboard_echo_psm_set_usdc_yield_position_access_control(
    switchboard_echo,
    alice,
    bob,
    governance,
    alpha_token,
):
    """Test access control for setPsmUsdcYieldPosition"""
    lego_id = 1
    vault_token = alpha_token.address

    # Non-governance users should be rejected
    with boa.reverts("no perms"):
        switchboard_echo.setPsmUsdcYieldPosition(lego_id, vault_token, sender=alice)

    with boa.reverts("no perms"):
        switchboard_echo.setPsmUsdcYieldPosition(lego_id, vault_token, sender=bob)

    # Governance should be able to call
    action_id = switchboard_echo.setPsmUsdcYieldPosition(lego_id, vault_token, sender=governance.address)
    assert action_id > 0


def test_switchboard_echo_psm_set_usdc_yield_position_parameter_validation(
    switchboard_echo,
    governance,
    alpha_token,
):
    """Test parameter validation for setPsmUsdcYieldPosition"""
    vault_token = alpha_token.address

    # Zero lego ID should be rejected
    with boa.reverts("invalid lego id"):
        switchboard_echo.setPsmUsdcYieldPosition(0, vault_token, sender=governance.address)


def test_switchboard_echo_psm_set_num_blocks_per_interval_access_control(
    switchboard_echo,
    alice,
    governance,
):
    """Test access control for setPsmNumBlocksPerInterval"""
    blocks = 100

    # Non-governance users should be rejected
    with boa.reverts("no perms"):
        switchboard_echo.setPsmNumBlocksPerInterval(blocks, sender=alice)

    # Governance should be able to call
    action_id = switchboard_echo.setPsmNumBlocksPerInterval(blocks, sender=governance.address)
    assert action_id > 0


def test_switchboard_echo_psm_all_governance_functions_access_control(
    switchboard_echo,
    alice,
    governance,
):
    """Test that all PSM governance functions reject non-governance users"""
    user = alice

    # All these should revert with "no perms"
    with boa.reverts("no perms"):
        switchboard_echo.setPsmMaxIntervalMint(1000, sender=alice)

    with boa.reverts("no perms"):
        switchboard_echo.setPsmShouldEnforceMintAllowlist(True, sender=alice)

    with boa.reverts("no perms"):
        switchboard_echo.setPsmRedeemFee(100, sender=alice)

    with boa.reverts("no perms"):
        switchboard_echo.setPsmMaxIntervalRedeem(2000, sender=alice)

    with boa.reverts("no perms"):
        switchboard_echo.setPsmShouldEnforceRedeemAllowlist(False, sender=alice)


def test_switchboard_echo_psm_action_type_flag_values(
    switchboard_echo,
    governance,
    alpha_token,
):
    """Test that PSM ActionType flags have correct values"""
    # Create various PSM actions and verify their ActionType values
    # In SwitchboardEcho, PSM flags start at index 7 (after 7 Endaoment flags)

    # PSM_SET_CAN_MINT should be 2^7 = 128
    aid1 = switchboard_echo.setPsmCanMint(True, sender=governance.address)
    assert switchboard_echo.actionType(aid1) == 2**7

    # PSM_SET_MINT_FEE should be 2^8 = 256
    aid2 = switchboard_echo.setPsmMintFee(100, sender=governance.address)
    assert switchboard_echo.actionType(aid2) == 2**8

    # PSM_SET_MAX_INTERVAL_MINT should be 2^9 = 512
    aid3 = switchboard_echo.setPsmMaxIntervalMint(1000, sender=governance.address)
    assert switchboard_echo.actionType(aid3) == 2**9

    # PSM_UPDATE_MINT_ALLOWLIST should be 2^11 = 2048
    aid4 = switchboard_echo.updatePsmMintAllowlist(alpha_token.address, True, sender=governance.address)
    assert switchboard_echo.actionType(aid4) == 2**11

    # PSM_SET_CAN_REDEEM should be 2^12 = 4096
    aid5 = switchboard_echo.setPsmCanRedeem(False, sender=governance.address)
    assert switchboard_echo.actionType(aid5) == 2**12


def test_switchboard_echo_psm_event_emission_pending_actions(
    switchboard_echo,
    governance,
    alice,
):
    """Test that pending PSM actions emit correct events"""
    # Test setPsmMintFee event
    fee = 200
    aid1 = switchboard_echo.setPsmMintFee(fee, sender=governance.address)
    logs = filter_logs(switchboard_echo, "PendingPsmSetMintFeeAction")
    assert len(logs) == 1
    assert logs[0].fee == fee
    assert logs[0].actionId == aid1

    # Test setPsmMaxIntervalMint event
    max_amount = 5000
    aid2 = switchboard_echo.setPsmMaxIntervalMint(max_amount, sender=governance.address)
    logs = filter_logs(switchboard_echo, "PendingPsmSetMaxIntervalMintAction")
    assert len(logs) == 1
    assert logs[0].maxGreenAmount == max_amount
    assert logs[0].actionId == aid2

    # Test updatePsmMintAllowlist event
    aid3 = switchboard_echo.updatePsmMintAllowlist(alice, True, sender=governance.address)
    logs = filter_logs(switchboard_echo, "PendingPsmUpdateMintAllowlistAction")
    assert len(logs) == 1
    assert logs[0].user == alice
    assert logs[0].isAllowed == True
    assert logs[0].actionId == aid3

    # Test setPsmNumBlocksPerInterval event
    blocks = 150
    aid4 = switchboard_echo.setPsmNumBlocksPerInterval(blocks, sender=governance.address)
    logs = filter_logs(switchboard_echo, "PendingPsmSetNumBlocksPerIntervalAction")
    assert len(logs) == 1
    assert logs[0].blocks == blocks
    assert logs[0].actionId == aid4


def test_switchboard_echo_psm_multiple_pending_actions_storage(
    switchboard_echo,
    governance,
    alice,
    bob,
):
    """Test that multiple pending PSM actions can be stored simultaneously"""
    # Create multiple pending actions
    aid1 = switchboard_echo.setPsmCanMint(True, sender=governance.address)
    aid2 = switchboard_echo.setPsmMintFee(100, sender=governance.address)
    aid3 = switchboard_echo.updatePsmMintAllowlist(alice, True, sender=governance.address)
    aid4 = switchboard_echo.setPsmCanRedeem(False, sender=governance.address)
    aid5 = switchboard_echo.updatePsmRedeemAllowlist(bob, False, sender=governance.address)

    # Verify all are stored correctly
    assert switchboard_echo.pendingPsmSetCanMintActions(aid1)[0] == True
    assert switchboard_echo.pendingPsmSetMintFeeActions(aid2)[0] == 100
    assert switchboard_echo.pendingPsmUpdateMintAllowlistActions(aid3)[0] == alice
    assert switchboard_echo.pendingPsmSetCanRedeemActions(aid4)[0] == False
    assert switchboard_echo.pendingPsmUpdateRedeemAllowlistActions(aid5)[0] == bob

    # Verify ActionType is set correctly for each
    assert switchboard_echo.actionType(aid1) > 0
    assert switchboard_echo.actionType(aid2) > 0
    assert switchboard_echo.actionType(aid3) > 0
    assert switchboard_echo.actionType(aid4) > 0
    assert switchboard_echo.actionType(aid5) > 0
