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


# ========================================
# Endaoment Transfer Tests
# ========================================


def test_perform_endaoment_transfer_permissions(switchboard_echo, governance, alice, alpha_token):
    """Test that only governance can call performEndaomentTransfer"""
    with boa.reverts("no perms"):
        switchboard_echo.performEndaomentTransfer(alpha_token.address, 1000, sender=alice)


def test_perform_endaoment_transfer_creates_timelock(switchboard_echo, governance, alpha_token):
    """Test performEndaomentTransfer creates timelock action correctly"""
    asset = alpha_token.address
    amount = 1000

    aid = switchboard_echo.performEndaomentTransfer(asset, amount, sender=governance.address)
    assert aid > 0

    # Check event was emitted
    logs = filter_logs(switchboard_echo, "PendingEndaoTransferAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.asset == asset
    assert log.amount == amount
    assert log.actionId == aid

    # Check action type (ENDAO_TRANSFER is 2^6 = 64)
    action_type = switchboard_echo.actionType(aid)
    assert action_type == 64


def test_perform_endaoment_transfer_validation(switchboard_echo, governance, alpha_token):
    """Test performEndaomentTransfer validation"""
    # Empty asset should fail
    with boa.reverts("invalid asset"):
        switchboard_echo.performEndaomentTransfer(ZERO_ADDRESS, 1000, sender=governance.address)

    # Zero amount should fail
    with boa.reverts("invalid amount"):
        switchboard_echo.performEndaomentTransfer(alpha_token.address, 0, sender=governance.address)


# ========================================
# Endaoment Swap Tests
# ========================================


def test_perform_endaoment_swap_permissions(switchboard_echo, governance, alice):
    """Test that only governance can call performEndaomentSwap"""
    # Empty instructions for permission test
    instructions = []

    with boa.reverts("no perms"):
        switchboard_echo.performEndaomentSwap(instructions, sender=alice)


def test_perform_endaoment_swap_creates_timelock(switchboard_echo, governance, alpha_token, ripe_token):
    """Test performEndaomentSwap creates timelock action correctly"""
    # Create a sample swap instruction tuple
    # SwapInstruction: (legoId, amountIn, minAmountOut, tokenPath, poolPath)
    instructions = [
        (1, 1000, 900, [alpha_token.address, ripe_token.address], [])
    ]

    aid = switchboard_echo.performEndaomentSwap(instructions, sender=governance.address)
    assert aid > 0

    # Check event was emitted
    logs = filter_logs(switchboard_echo, "PendingEndaoSwapAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.numSwapInstructions == 1
    assert log.actionId == aid

    # Check action type (ENDAO_SWAP is 2^0 = 1)
    action_type = switchboard_echo.actionType(aid)
    assert action_type == 1


def test_perform_endaoment_swap_validation(switchboard_echo, governance):
    """Test performEndaomentSwap validation"""
    # Empty instructions should fail
    with boa.reverts("no swap instructions provided"):
        switchboard_echo.performEndaomentSwap([], sender=governance.address)


# ========================================
# Add Liquidity In Endaoment Tests
# ========================================


def test_add_liquidity_in_endaoment_permissions(switchboard_echo, governance, alice, alpha_token, ripe_token):
    """Test that only governance can call addLiquidityInEndaoment"""
    with boa.reverts("no perms"):
        switchboard_echo.addLiquidityInEndaoment(
            1,  # legoId
            alpha_token.address,  # pool
            alpha_token.address,  # tokenA
            ripe_token.address,  # tokenB
            sender=alice
        )


def test_add_liquidity_in_endaoment_creates_timelock(switchboard_echo, governance, alpha_token, ripe_token):
    """Test addLiquidityInEndaoment creates timelock action correctly"""
    lego_id = 1
    pool = alpha_token.address
    token_a = alpha_token.address
    token_b = ripe_token.address

    aid = switchboard_echo.addLiquidityInEndaoment(
        lego_id,
        pool,
        token_a,
        token_b,
        sender=governance.address
    )
    assert aid > 0

    # Check event was emitted
    logs = filter_logs(switchboard_echo, "PendingEndaoAddLiquidityAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.legoId == lego_id
    assert log.pool == pool
    assert log.tokenA == token_a
    assert log.tokenB == token_b
    assert log.actionId == aid

    # Check action type (ENDAO_ADD_LIQUIDITY is 2^1 = 2)
    action_type = switchboard_echo.actionType(aid)
    assert action_type == 2


def test_add_liquidity_in_endaoment_validation(switchboard_echo, governance, alpha_token, ripe_token):
    """Test addLiquidityInEndaoment validation"""
    # Zero lego ID should fail
    with boa.reverts("invalid lego id"):
        switchboard_echo.addLiquidityInEndaoment(
            0,  # invalid legoId
            alpha_token.address,
            alpha_token.address,
            ripe_token.address,
            sender=governance.address
        )


# ========================================
# Remove Liquidity In Endaoment Tests
# ========================================


def test_remove_liquidity_in_endaoment_permissions(switchboard_echo, governance, alice, alpha_token, ripe_token):
    """Test that only governance can call removeLiquidityInEndaoment"""
    with boa.reverts("no perms"):
        switchboard_echo.removeLiquidityInEndaoment(
            1,  # legoId
            alpha_token.address,  # pool
            alpha_token.address,  # tokenA
            ripe_token.address,  # tokenB
            alpha_token.address,  # lpToken
            sender=alice
        )


def test_remove_liquidity_in_endaoment_creates_timelock(switchboard_echo, governance, alpha_token, ripe_token):
    """Test removeLiquidityInEndaoment creates timelock action correctly"""
    lego_id = 1
    pool = alpha_token.address
    token_a = alpha_token.address
    token_b = ripe_token.address
    lp_token = alpha_token.address

    aid = switchboard_echo.removeLiquidityInEndaoment(
        lego_id,
        pool,
        token_a,
        token_b,
        lp_token,
        sender=governance.address
    )
    assert aid > 0

    # Check event was emitted
    logs = filter_logs(switchboard_echo, "PendingEndaoRemoveLiquidityAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.legoId == lego_id
    assert log.pool == pool
    assert log.tokenA == token_a
    assert log.tokenB == token_b
    assert log.actionId == aid

    # Check action type (ENDAO_REMOVE_LIQUIDITY is 2^2 = 4)
    action_type = switchboard_echo.actionType(aid)
    assert action_type == 4


def test_remove_liquidity_in_endaoment_validation(switchboard_echo, governance, alpha_token, ripe_token):
    """Test removeLiquidityInEndaoment validation"""
    # Zero lego ID should fail
    with boa.reverts("invalid lego id"):
        switchboard_echo.removeLiquidityInEndaoment(
            0,  # invalid legoId
            alpha_token.address,
            alpha_token.address,
            ripe_token.address,
            alpha_token.address,
            sender=governance.address
        )


# ========================================
# Mint Partner Liquidity In Endaoment Tests
# ========================================


def test_mint_partner_liquidity_in_endaoment_permissions(switchboard_echo, governance, alice, bob, alpha_token):
    """Test that only governance can call mintPartnerLiquidityInEndaoment"""
    with boa.reverts("no perms"):
        switchboard_echo.mintPartnerLiquidityInEndaoment(
            bob,  # partner
            alpha_token.address,  # asset
            1000,  # amount
            sender=alice
        )


def test_mint_partner_liquidity_in_endaoment_creates_timelock(switchboard_echo, governance, bob, alpha_token):
    """Test mintPartnerLiquidityInEndaoment creates timelock action correctly"""
    partner = bob
    asset = alpha_token.address
    amount = 1000

    aid = switchboard_echo.mintPartnerLiquidityInEndaoment(
        partner,
        asset,
        amount,
        sender=governance.address
    )
    assert aid > 0

    # Check event was emitted
    logs = filter_logs(switchboard_echo, "PendingEndaoPartnerMintAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.partner == partner
    assert log.asset == asset
    assert log.amount == amount
    assert log.actionId == aid

    # Check action type (ENDAO_PARTNER_MINT is 2^3 = 8)
    action_type = switchboard_echo.actionType(aid)
    assert action_type == 8


def test_mint_partner_liquidity_in_endaoment_validation(switchboard_echo, governance, alpha_token):
    """Test mintPartnerLiquidityInEndaoment validation"""
    # Empty partner should fail
    with boa.reverts("invalid partner"):
        switchboard_echo.mintPartnerLiquidityInEndaoment(
            ZERO_ADDRESS,
            alpha_token.address,
            1000,
            sender=governance.address
        )

    # Empty asset should fail
    with boa.reverts("invalid asset"):
        switchboard_echo.mintPartnerLiquidityInEndaoment(
            governance.address,
            ZERO_ADDRESS,
            1000,
            sender=governance.address
        )


# ========================================
# Add Partner Liquidity In Endaoment Tests
# ========================================


def test_add_partner_liquidity_in_endaoment_permissions(switchboard_echo, governance, alice, bob, alpha_token):
    """Test that only governance can call addPartnerLiquidityInEndaoment"""
    with boa.reverts("no perms"):
        switchboard_echo.addPartnerLiquidityInEndaoment(
            1,  # legoId
            alpha_token.address,  # pool
            bob,  # partner
            alpha_token.address,  # asset
            1000,  # amount
            900,  # minLpAmount
            sender=alice
        )


def test_add_partner_liquidity_in_endaoment_creates_timelock(switchboard_echo, governance, bob, alpha_token):
    """Test addPartnerLiquidityInEndaoment creates timelock action correctly"""
    lego_id = 1
    pool = alpha_token.address
    partner = bob
    asset = alpha_token.address
    amount = 1000
    min_lp = 900

    aid = switchboard_echo.addPartnerLiquidityInEndaoment(
        lego_id,
        pool,
        partner,
        asset,
        amount,
        min_lp,
        sender=governance.address
    )
    assert aid > 0

    # Check event was emitted
    logs = filter_logs(switchboard_echo, "PendingEndaoPartnerPoolAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.legoId == lego_id
    assert log.pool == pool
    assert log.partner == partner
    assert log.asset == asset
    assert log.actionId == aid

    # Check action type (ENDAO_PARTNER_POOL is 2^4 = 16)
    action_type = switchboard_echo.actionType(aid)
    assert action_type == 16


def test_add_partner_liquidity_in_endaoment_validation(switchboard_echo, governance, bob, alpha_token):
    """Test addPartnerLiquidityInEndaoment validation"""
    # Zero lego ID should fail
    with boa.reverts("invalid lego id"):
        switchboard_echo.addPartnerLiquidityInEndaoment(
            0,  # invalid legoId
            alpha_token.address,
            bob,
            alpha_token.address,
            1000,
            900,
            sender=governance.address
        )

    # Empty partner should fail
    with boa.reverts("invalid partner"):
        switchboard_echo.addPartnerLiquidityInEndaoment(
            1,
            alpha_token.address,
            ZERO_ADDRESS,  # invalid partner
            alpha_token.address,
            1000,
            900,
            sender=governance.address
        )


# ========================================
# Repay Pool Debt In Endaoment Tests
# ========================================


def test_repay_pool_debt_in_endaoment_permissions(switchboard_echo, governance, alice, alpha_token):
    """Test that only governance can call repayPoolDebtInEndaoment"""
    with boa.reverts("no perms"):
        switchboard_echo.repayPoolDebtInEndaoment(
            alpha_token.address,  # pool
            1000,  # amount
            sender=alice
        )


def test_repay_pool_debt_in_endaoment_creates_timelock(switchboard_echo, governance, alpha_token):
    """Test repayPoolDebtInEndaoment creates timelock action correctly"""
    pool = alpha_token.address
    amount = 1000

    aid = switchboard_echo.repayPoolDebtInEndaoment(pool, amount, sender=governance.address)
    assert aid > 0

    # Check event was emitted
    logs = filter_logs(switchboard_echo, "PendingEndaoRepayAction")
    assert len(logs) == 1
    log = logs[0]
    assert log.pool == pool
    assert log.amount == amount
    assert log.actionId == aid

    # Check action type (ENDAO_REPAY is 2^5 = 32)
    action_type = switchboard_echo.actionType(aid)
    assert action_type == 32


def test_repay_pool_debt_in_endaoment_validation(switchboard_echo, governance):
    """Test repayPoolDebtInEndaoment validation"""
    # Empty pool should fail
    with boa.reverts("invalid pool"):
        switchboard_echo.repayPoolDebtInEndaoment(ZERO_ADDRESS, 1000, sender=governance.address)


# ========================================
# PSM Timelock Flow Tests (Complete)
# ========================================


def test_psm_can_redeem_timelock_flow(switchboard_echo, governance):
    """Test complete timelock flow for setPsmCanRedeem"""
    # Create pending action
    action_id = switchboard_echo.setPsmCanRedeem(True, sender=governance.address)

    # Verify event was emitted
    logs = filter_logs(switchboard_echo, "PendingPsmSetCanRedeemAction")
    assert len(logs) == 1
    assert logs[0].canRedeem == True
    assert logs[0].actionId == action_id

    # Verify action is stored
    action_type = switchboard_echo.actionType(action_id)
    assert action_type == 2**12  # PSM_SET_CAN_REDEEM

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


def test_psm_redeem_fee_timelock_flow(switchboard_echo, governance):
    """Test complete timelock flow for setPsmRedeemFee"""
    fee = 150

    # Create pending action
    action_id = switchboard_echo.setPsmRedeemFee(fee, sender=governance.address)

    # Verify event was emitted
    logs = filter_logs(switchboard_echo, "PendingPsmSetRedeemFeeAction")
    assert len(logs) == 1
    assert logs[0].fee == fee
    assert logs[0].actionId == action_id

    # Execution should fail before timelock
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert not result

    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())

    # Now execution should succeed
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert result


def test_psm_max_interval_mint_timelock_flow(switchboard_echo, governance):
    """Test complete timelock flow for setPsmMaxIntervalMint"""
    max_amount = 10000

    # Create pending action
    action_id = switchboard_echo.setPsmMaxIntervalMint(max_amount, sender=governance.address)

    # Verify event was emitted
    logs = filter_logs(switchboard_echo, "PendingPsmSetMaxIntervalMintAction")
    assert len(logs) == 1
    assert logs[0].maxGreenAmount == max_amount
    assert logs[0].actionId == action_id

    # Execution should fail before timelock
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert not result

    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())

    # Now execution should succeed
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert result


def test_psm_max_interval_redeem_timelock_flow(switchboard_echo, governance):
    """Test complete timelock flow for setPsmMaxIntervalRedeem"""
    max_amount = 8000

    # Create pending action
    action_id = switchboard_echo.setPsmMaxIntervalRedeem(max_amount, sender=governance.address)

    # Verify event was emitted
    logs = filter_logs(switchboard_echo, "PendingPsmSetMaxIntervalRedeemAction")
    assert len(logs) == 1
    assert logs[0].maxGreenAmount == max_amount
    assert logs[0].actionId == action_id

    # Execution should fail before timelock
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert not result

    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())

    # Now execution should succeed
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert result


def test_psm_usdc_yield_position_timelock_flow(switchboard_echo, governance, alpha_token):
    """Test complete timelock flow for setPsmUsdcYieldPosition"""
    lego_id = 1
    vault_token = alpha_token.address

    # Create pending action
    action_id = switchboard_echo.setPsmUsdcYieldPosition(lego_id, vault_token, sender=governance.address)

    # Verify event was emitted
    logs = filter_logs(switchboard_echo, "PendingPsmSetUsdcYieldPositionAction")
    assert len(logs) == 1
    assert logs[0].legoId == lego_id
    assert logs[0].vaultToken == vault_token
    assert logs[0].actionId == action_id

    # Execution should fail before timelock
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert not result

    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())

    # Now execution should succeed
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert result


def test_psm_num_blocks_per_interval_timelock_flow(switchboard_echo, governance):
    """Test complete timelock flow for setPsmNumBlocksPerInterval"""
    blocks = 200

    # Create pending action
    action_id = switchboard_echo.setPsmNumBlocksPerInterval(blocks, sender=governance.address)

    # Verify event was emitted
    logs = filter_logs(switchboard_echo, "PendingPsmSetNumBlocksPerIntervalAction")
    assert len(logs) == 1
    assert logs[0].blocks == blocks
    assert logs[0].actionId == action_id

    # Execution should fail before timelock
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert not result

    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())

    # Now execution should succeed
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert result


def test_psm_should_auto_deposit_timelock_flow(switchboard_echo, governance):
    """Test complete timelock flow for setPsmShouldAutoDeposit"""
    # Create pending action - set to False (PSM defaults to True)
    action_id = switchboard_echo.setPsmShouldAutoDeposit(False, sender=governance.address)

    # Verify event was emitted
    logs = filter_logs(switchboard_echo, "PendingPsmSetShouldAutoDepositAction")
    assert len(logs) == 1
    assert logs[0].shouldAutoDeposit == False
    assert logs[0].actionId == action_id

    # Execution should fail before timelock
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert not result

    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())

    # Now execution should succeed
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert result


def test_update_psm_redeem_allowlist_timelock_flow(switchboard_echo, governance, alice):
    """Test complete timelock flow for updatePsmRedeemAllowlist"""
    user = alice
    is_allowed = True

    # Create pending action
    action_id = switchboard_echo.updatePsmRedeemAllowlist(user, is_allowed, sender=governance.address)

    # Verify event was emitted
    logs = filter_logs(switchboard_echo, "PendingPsmUpdateRedeemAllowlistAction")
    assert len(logs) == 1
    assert logs[0].user == user
    assert logs[0].isAllowed == is_allowed
    assert logs[0].actionId == action_id

    # Execution should fail before timelock
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert not result

    # Time travel past timelock
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())

    # Now execution should succeed
    result = switchboard_echo.executePendingAction(action_id, sender=governance.address)
    assert result


# ========================================
# Endaoment ActionType Values Tests
# ========================================


def test_endaoment_action_type_flag_values(
    switchboard_echo, governance, alpha_token, ripe_token, bob
):
    """Test that Endaoment ActionType flags have correct values"""
    # ENDAO_SWAP should be 2^0 = 1
    # SwapInstruction: (legoId, amountIn, minAmountOut, tokenPath, poolPath)
    instructions = [(1, 100, 90, [alpha_token.address, ripe_token.address], [])]
    aid1 = switchboard_echo.performEndaomentSwap(instructions, sender=governance.address)
    assert switchboard_echo.actionType(aid1) == 1

    # ENDAO_ADD_LIQUIDITY should be 2^1 = 2
    aid2 = switchboard_echo.addLiquidityInEndaoment(1, alpha_token.address, alpha_token.address, ripe_token.address, sender=governance.address)
    assert switchboard_echo.actionType(aid2) == 2

    # ENDAO_REMOVE_LIQUIDITY should be 2^2 = 4
    aid3 = switchboard_echo.removeLiquidityInEndaoment(1, alpha_token.address, alpha_token.address, ripe_token.address, alpha_token.address, sender=governance.address)
    assert switchboard_echo.actionType(aid3) == 4

    # ENDAO_PARTNER_MINT should be 2^3 = 8
    aid4 = switchboard_echo.mintPartnerLiquidityInEndaoment(bob, alpha_token.address, 100, sender=governance.address)
    assert switchboard_echo.actionType(aid4) == 8

    # ENDAO_PARTNER_POOL should be 2^4 = 16
    aid5 = switchboard_echo.addPartnerLiquidityInEndaoment(1, alpha_token.address, bob, alpha_token.address, 100, 90, sender=governance.address)
    assert switchboard_echo.actionType(aid5) == 16

    # ENDAO_REPAY should be 2^5 = 32
    aid6 = switchboard_echo.repayPoolDebtInEndaoment(alpha_token.address, 100, sender=governance.address)
    assert switchboard_echo.actionType(aid6) == 32

    # ENDAO_TRANSFER should be 2^6 = 64
    aid7 = switchboard_echo.performEndaomentTransfer(alpha_token.address, 100, sender=governance.address)
    assert switchboard_echo.actionType(aid7) == 64
