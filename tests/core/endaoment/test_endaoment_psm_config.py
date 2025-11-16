import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from conf_utils import filter_logs


SIX_DECIMALS = 10**6  # For tokens like USDC that have 6 decimals
ONE_DAY_BLOCKS = 43_200
HUNDRED_PERCENT = 100_00


#############################
# Configuration Setter Tests #
#############################


def test_set_can_mint_access_control(endaoment_psm, switchboard_charlie):
    """Only switchboard should be able to set canMint"""
    random_user = boa.env.generate_address()

    # Random user should fail
    with boa.reverts("no perms"):
        endaoment_psm.setCanMint(True, sender=random_user)

    # Switchboard should succeed
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    assert endaoment_psm.canMint() == True


def test_set_can_mint_when_paused(endaoment_psm, switchboard_charlie):
    """Setting canMint should fail when contract is paused"""
    endaoment_psm.pause(True, sender=switchboard_charlie.address)

    with boa.reverts("contract paused"):
        endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)


def test_set_can_mint_emits_event(endaoment_psm, switchboard_charlie):
    """Setting canMint should emit CanMintUpdated event"""
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)

    logs = filter_logs(endaoment_psm, "CanMintUpdated")
    assert len(logs) == 1
    assert logs[0].canMint == True


def test_set_mint_fee_validation(endaoment_psm, switchboard_charlie):
    """Mint fee should not exceed 100%"""
    # Valid fee (10%)
    endaoment_psm.setMintFee(1000, sender=switchboard_charlie.address)
    assert endaoment_psm.mintFee() == 1000

    # Max fee (100%)
    endaoment_psm.setMintFee(HUNDRED_PERCENT, sender=switchboard_charlie.address)
    assert endaoment_psm.mintFee() == HUNDRED_PERCENT

    # Over 100% should fail
    with boa.reverts("fee too high"):
        endaoment_psm.setMintFee(HUNDRED_PERCENT + 1, sender=switchboard_charlie.address)


def test_set_mint_fee_access_control(endaoment_psm, switchboard_charlie):
    """Only switchboard should be able to set mint fee"""
    random_user = boa.env.generate_address()

    with boa.reverts("no perms"):
        endaoment_psm.setMintFee(500, sender=random_user)


def test_set_mint_fee_when_paused(endaoment_psm, switchboard_charlie):
    """Setting mint fee should fail when paused"""
    endaoment_psm.pause(True, sender=switchboard_charlie.address)

    with boa.reverts("contract paused"):
        endaoment_psm.setMintFee(500, sender=switchboard_charlie.address)


def test_set_mint_fee_emits_event(endaoment_psm, switchboard_charlie):
    """Setting mint fee should emit event"""
    endaoment_psm.setMintFee(500, sender=switchboard_charlie.address)

    logs = filter_logs(endaoment_psm, "MintFeeUpdated")
    assert len(logs) == 1
    assert logs[0].fee == 500


def test_set_max_interval_mint_validation(endaoment_psm, switchboard_charlie):
    """Max interval mint should not be 0 or max_value"""
    # Valid amount
    endaoment_psm.setMaxIntervalMint(1000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)
    assert endaoment_psm.maxIntervalMint() == 1000 * EIGHTEEN_DECIMALS

    # Zero should fail
    with boa.reverts("invalid max"):
        endaoment_psm.setMaxIntervalMint(0, sender=switchboard_charlie.address)

    # Max value should fail
    with boa.reverts("invalid max"):
        endaoment_psm.setMaxIntervalMint(MAX_UINT256, sender=switchboard_charlie.address)


def test_set_max_interval_mint_access_control(endaoment_psm, switchboard_charlie):
    """Only switchboard should be able to set max interval mint"""
    random_user = boa.env.generate_address()

    with boa.reverts("no perms"):
        endaoment_psm.setMaxIntervalMint(1000 * EIGHTEEN_DECIMALS, sender=random_user)


def test_set_max_interval_mint_emits_event(endaoment_psm, switchboard_charlie):
    """Setting max interval mint should emit event"""
    endaoment_psm.setMaxIntervalMint(1000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)

    logs = filter_logs(endaoment_psm, "MaxIntervalMintUpdated")
    assert len(logs) == 1
    assert logs[0].maxAmount == 1000 * EIGHTEEN_DECIMALS


def test_set_should_enforce_mint_allowlist(endaoment_psm, switchboard_charlie):
    """Should be able to toggle mint allowlist enforcement"""
    # Enable enforcement
    endaoment_psm.setShouldEnforceMintAllowlist(True, sender=switchboard_charlie.address)
    assert endaoment_psm.shouldEnforceMintAllowlist() == True

    # Disable enforcement
    endaoment_psm.setShouldEnforceMintAllowlist(False, sender=switchboard_charlie.address)
    assert endaoment_psm.shouldEnforceMintAllowlist() == False


def test_set_should_enforce_mint_allowlist_access_control(endaoment_psm, switchboard_charlie):
    """Only switchboard should be able to set allowlist enforcement"""
    random_user = boa.env.generate_address()

    with boa.reverts("no perms"):
        endaoment_psm.setShouldEnforceMintAllowlist(True, sender=random_user)


def test_set_should_enforce_mint_allowlist_emits_event(endaoment_psm, switchboard_charlie):
    """Setting allowlist enforcement should emit event"""
    endaoment_psm.setShouldEnforceMintAllowlist(True, sender=switchboard_charlie.address)

    logs = filter_logs(endaoment_psm, "ShouldEnforceMintAllowlistUpdated")
    assert len(logs) == 1
    assert logs[0].shouldEnforce == True


def test_update_mint_allowlist(endaoment_psm, switchboard_charlie):
    """Should be able to add/remove addresses from mint allowlist"""
    user = boa.env.generate_address()

    # Initially not on allowlist
    assert endaoment_psm.mintAllowlist(user) == False

    # Add to allowlist
    endaoment_psm.updateMintAllowlist(user, True, sender=switchboard_charlie.address)
    assert endaoment_psm.mintAllowlist(user) == True

    # Remove from allowlist
    endaoment_psm.updateMintAllowlist(user, False, sender=switchboard_charlie.address)
    assert endaoment_psm.mintAllowlist(user) == False


def test_update_mint_allowlist_access_control(endaoment_psm, switchboard_charlie):
    """Only switchboard should be able to update mint allowlist"""
    user = boa.env.generate_address()
    random_user = boa.env.generate_address()

    with boa.reverts("no perms"):
        endaoment_psm.updateMintAllowlist(user, True, sender=random_user)


def test_update_mint_allowlist_emits_event(endaoment_psm, switchboard_charlie):
    """Updating mint allowlist should emit event"""
    user = boa.env.generate_address()

    endaoment_psm.updateMintAllowlist(user, True, sender=switchboard_charlie.address)

    logs = filter_logs(endaoment_psm, "MintAllowlistUpdated")
    assert len(logs) == 1
    assert logs[0].user == user
    assert logs[0].isAllowed == True


# Redeem configuration tests


def test_set_can_redeem_access_control(endaoment_psm, switchboard_charlie):
    """Only switchboard should be able to set canRedeem"""
    random_user = boa.env.generate_address()

    with boa.reverts("no perms"):
        endaoment_psm.setCanRedeem(True, sender=random_user)

    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
    assert endaoment_psm.canRedeem() == True


def test_set_can_redeem_when_paused(endaoment_psm, switchboard_charlie):
    """Setting canRedeem should fail when paused"""
    endaoment_psm.pause(True, sender=switchboard_charlie.address)

    with boa.reverts("contract paused"):
        endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)


def test_set_can_redeem_emits_event(endaoment_psm, switchboard_charlie):
    """Setting canRedeem should emit event"""
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)

    logs = filter_logs(endaoment_psm, "CanRedeemUpdated")
    assert len(logs) == 1
    assert logs[0].canRedeem == True


def test_set_redeem_fee_validation(endaoment_psm, switchboard_charlie):
    """Redeem fee should not exceed 100%"""
    # Valid fee
    endaoment_psm.setRedeemFee(500, sender=switchboard_charlie.address)
    assert endaoment_psm.redeemFee() == 500

    # Max fee
    endaoment_psm.setRedeemFee(HUNDRED_PERCENT, sender=switchboard_charlie.address)
    assert endaoment_psm.redeemFee() == HUNDRED_PERCENT

    # Over 100% should fail
    with boa.reverts("fee too high"):
        endaoment_psm.setRedeemFee(HUNDRED_PERCENT + 1, sender=switchboard_charlie.address)


def test_set_redeem_fee_access_control(endaoment_psm, switchboard_charlie):
    """Only switchboard should be able to set redeem fee"""
    random_user = boa.env.generate_address()

    with boa.reverts("no perms"):
        endaoment_psm.setRedeemFee(500, sender=random_user)


def test_set_redeem_fee_emits_event(endaoment_psm, switchboard_charlie):
    """Setting redeem fee should emit event"""
    endaoment_psm.setRedeemFee(500, sender=switchboard_charlie.address)

    logs = filter_logs(endaoment_psm, "RedeemFeeUpdated")
    assert len(logs) == 1
    assert logs[0].fee == 500


def test_set_max_interval_redeem_validation(endaoment_psm, switchboard_charlie):
    """Max interval redeem should not be 0 or max_value"""
    # Valid amount
    endaoment_psm.setMaxIntervalRedeem(1000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)
    assert endaoment_psm.maxIntervalRedeem() == 1000 * EIGHTEEN_DECIMALS

    # Zero should fail
    with boa.reverts("invalid max"):
        endaoment_psm.setMaxIntervalRedeem(0, sender=switchboard_charlie.address)

    # Max value should fail
    with boa.reverts("invalid max"):
        endaoment_psm.setMaxIntervalRedeem(MAX_UINT256, sender=switchboard_charlie.address)


def test_set_max_interval_redeem_access_control(endaoment_psm, switchboard_charlie):
    """Only switchboard should be able to set max interval redeem"""
    random_user = boa.env.generate_address()

    with boa.reverts("no perms"):
        endaoment_psm.setMaxIntervalRedeem(1000 * EIGHTEEN_DECIMALS, sender=random_user)


def test_set_max_interval_redeem_emits_event(endaoment_psm, switchboard_charlie):
    """Setting max interval redeem should emit event"""
    endaoment_psm.setMaxIntervalRedeem(1000 * EIGHTEEN_DECIMALS, sender=switchboard_charlie.address)

    logs = filter_logs(endaoment_psm, "MaxIntervalRedeemUpdated")
    assert len(logs) == 1
    assert logs[0].maxAmount == 1000 * EIGHTEEN_DECIMALS


def test_set_should_enforce_redeem_allowlist(endaoment_psm, switchboard_charlie):
    """Should be able to toggle redeem allowlist enforcement"""
    # Enable
    endaoment_psm.setShouldEnforceRedeemAllowlist(True, sender=switchboard_charlie.address)
    assert endaoment_psm.shouldEnforceRedeemAllowlist() == True

    # Disable
    endaoment_psm.setShouldEnforceRedeemAllowlist(False, sender=switchboard_charlie.address)
    assert endaoment_psm.shouldEnforceRedeemAllowlist() == False


def test_set_should_enforce_redeem_allowlist_access_control(endaoment_psm, switchboard_charlie):
    """Only switchboard should be able to set redeem allowlist enforcement"""
    random_user = boa.env.generate_address()

    with boa.reverts("no perms"):
        endaoment_psm.setShouldEnforceRedeemAllowlist(True, sender=random_user)


def test_set_should_enforce_redeem_allowlist_emits_event(endaoment_psm, switchboard_charlie):
    """Setting redeem allowlist enforcement should emit event"""
    endaoment_psm.setShouldEnforceRedeemAllowlist(True, sender=switchboard_charlie.address)

    logs = filter_logs(endaoment_psm, "ShouldEnforceRedeemAllowlistUpdated")
    assert len(logs) == 1
    assert logs[0].shouldEnforce == True


def test_update_redeem_allowlist(endaoment_psm, switchboard_charlie):
    """Should be able to add/remove addresses from redeem allowlist"""
    user = boa.env.generate_address()

    # Initially not on allowlist
    assert endaoment_psm.redeemAllowlist(user) == False

    # Add to allowlist
    endaoment_psm.updateRedeemAllowlist(user, True, sender=switchboard_charlie.address)
    assert endaoment_psm.redeemAllowlist(user) == True

    # Remove from allowlist
    endaoment_psm.updateRedeemAllowlist(user, False, sender=switchboard_charlie.address)
    assert endaoment_psm.redeemAllowlist(user) == False


def test_update_redeem_allowlist_access_control(endaoment_psm, switchboard_charlie):
    """Only switchboard should be able to update redeem allowlist"""
    user = boa.env.generate_address()
    random_user = boa.env.generate_address()

    with boa.reverts("no perms"):
        endaoment_psm.updateRedeemAllowlist(user, True, sender=random_user)


def test_update_redeem_allowlist_emits_event(endaoment_psm, switchboard_charlie):
    """Updating redeem allowlist should emit event"""
    user = boa.env.generate_address()

    endaoment_psm.updateRedeemAllowlist(user, True, sender=switchboard_charlie.address)

    logs = filter_logs(endaoment_psm, "RedeemAllowlistUpdated")
    assert len(logs) == 1
    assert logs[0].user == user
    assert logs[0].isAllowed == True


# General configuration tests


def test_set_num_blocks_per_interval_validation(endaoment_psm, switchboard_charlie):
    """Num blocks per interval should not be 0 or max_value"""
    # Valid value (different from default ONE_DAY_BLOCKS)
    endaoment_psm.setNumBlocksPerInterval(ONE_DAY_BLOCKS * 2, sender=switchboard_charlie.address)
    assert endaoment_psm.numBlocksPerInterval() == ONE_DAY_BLOCKS * 2

    # Zero should fail
    with boa.reverts("invalid interval"):
        endaoment_psm.setNumBlocksPerInterval(0, sender=switchboard_charlie.address)

    # Max value should fail
    with boa.reverts("invalid interval"):
        endaoment_psm.setNumBlocksPerInterval(MAX_UINT256, sender=switchboard_charlie.address)


def test_set_num_blocks_per_interval_access_control(endaoment_psm, switchboard_charlie):
    """Only switchboard should be able to set num blocks per interval"""
    random_user = boa.env.generate_address()

    with boa.reverts("no perms"):
        endaoment_psm.setNumBlocksPerInterval(ONE_DAY_BLOCKS, sender=random_user)


def test_set_num_blocks_per_interval_emits_event(endaoment_psm, switchboard_charlie):
    """Setting num blocks per interval should emit event"""
    endaoment_psm.setNumBlocksPerInterval(ONE_DAY_BLOCKS * 2, sender=switchboard_charlie.address)

    logs = filter_logs(endaoment_psm, "NumBlocksPerIntervalUpdated")
    assert len(logs) == 1
    assert logs[0].blocks == ONE_DAY_BLOCKS * 2


def test_set_should_auto_deposit(endaoment_psm, switchboard_charlie):
    """Should be able to toggle auto deposit"""
    # Initially true (from fixture)
    assert endaoment_psm.shouldAutoDeposit() == True

    # Disable
    endaoment_psm.setShouldAutoDeposit(False, sender=switchboard_charlie.address)
    assert endaoment_psm.shouldAutoDeposit() == False

    # Enable
    endaoment_psm.setShouldAutoDeposit(True, sender=switchboard_charlie.address)
    assert endaoment_psm.shouldAutoDeposit() == True


def test_set_should_auto_deposit_access_control(endaoment_psm, switchboard_charlie):
    """Only switchboard should be able to set auto deposit"""
    random_user = boa.env.generate_address()

    with boa.reverts("no perms"):
        endaoment_psm.setShouldAutoDeposit(False, sender=random_user)


def test_set_should_auto_deposit_emits_event(endaoment_psm, switchboard_charlie):
    """Setting auto deposit should emit event"""
    endaoment_psm.setShouldAutoDeposit(False, sender=switchboard_charlie.address)

    logs = filter_logs(endaoment_psm, "ShouldAutoDepositUpdated")
    assert len(logs) == 1
    assert logs[0].shouldAutoDeposit == False
