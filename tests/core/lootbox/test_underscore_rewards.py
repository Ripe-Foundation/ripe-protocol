import boa
import pytest
from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


# Constants
ONE_DAY_BLOCKS = 43_200  # One day in blocks on Base (2 second blocks)


# Fixtures

@pytest.fixture(scope="module")
def setup_underscore_rewards(mission_control, mock_undy_v2, switchboard_alpha, ledger):
    """Setup fixture for underscore rewards tests"""
    def _setup(ripe_available=1000 * EIGHTEEN_DECIMALS):
        # Set mock_undy_v2 as the underscore registry in MissionControl
        mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
        # Set available RIPE for rewards in Ledger
        ledger.setRipeAvailForRewards(ripe_available, sender=switchboard_alpha.address)
    return _setup


########################################
# Section 1: Basic Functionality Tests
########################################


def test_distribute_underscore_rewards_happy_path(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
    mock_undy_v2,
    ripe_token,
    ledger,
):
    """Test basic successful distribution with default values"""
    # Setup
    ripe_available = 1000 * EIGHTEEN_DECIMALS
    setup_underscore_rewards(ripe_available)

    # Get initial state
    initial_undy_balance = ripe_token.balanceOf(mock_undy_v2.address)
    initial_ripe_avail = ledger.ripeAvailForRewards()

    # Expected amounts (100 + 100 = 200 total)
    expected_deposit = 100 * EIGHTEEN_DECIMALS
    expected_yield = 100 * EIGHTEEN_DECIMALS
    expected_total = expected_deposit + expected_yield

    # Time travel past interval
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    # Distribute
    deposit_rewards, yield_bonus = lootbox.distributeUnderscoreRewards(
        sender=switchboard_alpha.address
    )

    # Assertions
    assert deposit_rewards == expected_deposit
    assert yield_bonus == expected_yield

    # Check mock received the tokens
    final_undy_balance = ripe_token.balanceOf(mock_undy_v2.address)
    assert final_undy_balance == initial_undy_balance + expected_total

    # Check ledger decremented ripeAvailForRewards
    final_ripe_avail = ledger.ripeAvailForRewards()
    assert final_ripe_avail == initial_ripe_avail - expected_total


def test_distribute_underscore_rewards_multiple_times(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
    mock_undy_v2,
    ripe_token,
):
    """Test sequential distributions after interval passes"""
    # Setup with plenty of RIPE
    setup_underscore_rewards(10000 * EIGHTEEN_DECIMALS)

    expected_per_distribution = 200 * EIGHTEEN_DECIMALS
    num_distributions = 3

    for i in range(num_distributions):
        # Time travel past interval
        boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

        # Get balance before
        balance_before = ripe_token.balanceOf(mock_undy_v2.address)

        # Distribute
        deposit, yield_bonus = lootbox.distributeUnderscoreRewards(
            sender=switchboard_alpha.address
        )

        # Check correct amount distributed
        assert deposit + yield_bonus == expected_per_distribution

        # Check balance increased
        balance_after = ripe_token.balanceOf(mock_undy_v2.address)
        assert balance_after == balance_before + expected_per_distribution


def test_distribute_returns_correct_amounts(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
):
    """Verify return values match deposit and yield amounts"""
    setup_underscore_rewards(500 * EIGHTEEN_DECIMALS)

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    # Distribute
    deposit_rewards, yield_bonus = lootbox.distributeUnderscoreRewards(
        sender=switchboard_alpha.address
    )

    # Expected values from default config
    assert deposit_rewards == 100 * EIGHTEEN_DECIMALS
    assert yield_bonus == 100 * EIGHTEEN_DECIMALS
    assert deposit_rewards + yield_bonus == 200 * EIGHTEEN_DECIMALS


def test_distribute_updates_last_send_block(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
):
    """Confirm lastUnderscoreSend updates correctly"""
    setup_underscore_rewards()

    # Initial state - should be 0 after deployment
    initial_last_send = lootbox.lastUnderscoreSend()

    # Time travel and distribute
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)
    current_block = boa.env.evm.patch.block_number

    lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)

    # Should update to current block
    assert lootbox.lastUnderscoreSend() == current_block

    # Distribute again after another interval
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)
    new_current_block = boa.env.evm.patch.block_number

    lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)

    # Should update again
    assert lootbox.lastUnderscoreSend() == new_current_block


def test_distribute_with_sufficient_ripe(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
    ripe_token,
    mock_undy_v2,
):
    """Full amount distributed when enough RIPE available"""
    # Setup with exactly enough RIPE
    setup_underscore_rewards(200 * EIGHTEEN_DECIMALS)

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    balance_before = ripe_token.balanceOf(mock_undy_v2.address)

    deposit, yield_bonus = lootbox.distributeUnderscoreRewards(
        sender=switchboard_alpha.address
    )

    # Should get full amounts
    assert deposit == 100 * EIGHTEEN_DECIMALS
    assert yield_bonus == 100 * EIGHTEEN_DECIMALS

    balance_after = ripe_token.balanceOf(mock_undy_v2.address)
    assert balance_after == balance_before + 200 * EIGHTEEN_DECIMALS


def test_distribute_with_limited_ripe(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
    ripe_token,
    mock_undy_v2,
):
    """Capped distribution when RIPE is limited (tests proportional split)"""
    # Setup with limited RIPE (only 50% of needed amount)
    limited_ripe = 100 * EIGHTEEN_DECIMALS  # Only 100 instead of 200 needed
    setup_underscore_rewards(limited_ripe)

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    balance_before = ripe_token.balanceOf(mock_undy_v2.address)

    deposit, yield_bonus = lootbox.distributeUnderscoreRewards(
        sender=switchboard_alpha.address
    )

    # Should get proportional split: 100 total, split 50/50
    # Since undyDepositRewardsAmount = undyYieldBonusAmount, split is equal
    expected_deposit = 50 * EIGHTEEN_DECIMALS
    expected_yield = 50 * EIGHTEEN_DECIMALS

    assert deposit == expected_deposit
    assert yield_bonus == expected_yield
    assert deposit + yield_bonus == limited_ripe

    balance_after = ripe_token.balanceOf(mock_undy_v2.address)
    assert balance_after == balance_before + limited_ripe


########################################
# Section 2: Permissions & Access Control
########################################


def test_distribute_requires_switchboard_permission(
    lootbox,
    alice,
    setup_underscore_rewards,
):
    """Non-switchboard caller reverts"""
    setup_underscore_rewards()

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    # Alice is not a switchboard
    with boa.reverts("no perms"):
        lootbox.distributeUnderscoreRewards(sender=alice)


def test_distribute_reverts_when_paused(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
):
    """Paused contract blocks distribution"""
    setup_underscore_rewards()

    # Pause the lootbox
    lootbox.pause(True, sender=switchboard_alpha.address)

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    with boa.reverts("contract paused"):
        lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)


def test_distribute_reverts_when_disabled(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
):
    """hasUnderscoreRewards=False blocks distribution"""
    setup_underscore_rewards()

    # Disable underscore rewards
    lootbox.setHasUnderscoreRewards(False, sender=switchboard_alpha.address)

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    with boa.reverts("no underscore rewards"):
        lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)


########################################
# Section 3: Interval Enforcement
########################################


def test_distribute_reverts_too_early(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
):
    """Block number < lastUnderscoreSend + interval"""
    setup_underscore_rewards()

    # First distribution
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)
    lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)

    # Try again too early (only 100 blocks later, need ONE_DAY_BLOCKS)
    boa.env.time_travel(blocks=100)

    with boa.reverts("too early"):
        lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)


def test_distribute_exactly_at_interval(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
):
    """Edge case: block number == lastUnderscoreSend + interval + 1"""
    setup_underscore_rewards()

    # First distribution
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)
    lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)

    last_send = lootbox.lastUnderscoreSend()

    # Travel exactly to the next allowed block
    # Need to be > lastUnderscoreSend + interval, so add interval + 1
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    # Should succeed
    lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)

    # Verify lastUnderscoreSend was updated
    assert lootbox.lastUnderscoreSend() > last_send


def test_distribute_long_after_interval(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
):
    """Works fine even if many intervals have passed"""
    setup_underscore_rewards(10000 * EIGHTEEN_DECIMALS)

    # First distribution
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)
    lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)

    # Wait for 10 intervals
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS * 10)

    # Should still work
    deposit, yield_bonus = lootbox.distributeUnderscoreRewards(
        sender=switchboard_alpha.address
    )

    # Should get normal amounts (not multiplied by missed intervals)
    assert deposit == 100 * EIGHTEEN_DECIMALS
    assert yield_bonus == 100 * EIGHTEEN_DECIMALS


def test_first_distribution_timing(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
):
    """First call after deployment (lastUnderscoreSend = 0)"""
    setup_underscore_rewards()

    # lastUnderscoreSend starts at 0
    assert lootbox.lastUnderscoreSend() == 0

    # Current block should be > 0 + interval for this to work
    current_block = boa.env.evm.patch.block_number
    interval = lootbox.underscoreSendInterval()

    if current_block <= interval:
        # Need to time travel
        boa.env.time_travel(blocks=interval + 1 - current_block)

    # Should succeed
    lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)

    # lastUnderscoreSend should now be updated
    assert lootbox.lastUnderscoreSend() > 0


########################################
# Section 4: Edge Cases & Bug Prevention
########################################


def test_distribute_reverts_both_amounts_zero(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
):
    """Tests division by zero protection - both amounts set to zero"""
    setup_underscore_rewards()

    # Set both amounts to zero
    lootbox.setUndyDepositRewardsAmount(0, sender=switchboard_alpha.address)
    lootbox.setUndyYieldBonusAmount(0, sender=switchboard_alpha.address)

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    # Should revert with assertion failure (totalRewardsAmount == 0)
    with boa.reverts("no rewards to distribute"):
        lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)


def test_distribute_with_only_deposit_rewards(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
    ripe_token,
    mock_undy_v2,
):
    """undyYieldBonusAmount = 0, only deposit rewards"""
    setup_underscore_rewards()

    # Set yield bonus to 0
    lootbox.setUndyYieldBonusAmount(0, sender=switchboard_alpha.address)

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    balance_before = ripe_token.balanceOf(mock_undy_v2.address)

    deposit, yield_bonus = lootbox.distributeUnderscoreRewards(
        sender=switchboard_alpha.address
    )

    # Only deposit rewards, no yield bonus
    assert deposit == 100 * EIGHTEEN_DECIMALS
    assert yield_bonus == 0

    balance_after = ripe_token.balanceOf(mock_undy_v2.address)
    assert balance_after == balance_before + 100 * EIGHTEEN_DECIMALS


def test_distribute_with_only_yield_bonus(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
    ripe_token,
    mock_undy_v2,
):
    """undyDepositRewardsAmount = 0, only yield bonus"""
    setup_underscore_rewards()

    # Set deposit rewards to 0
    lootbox.setUndyDepositRewardsAmount(0, sender=switchboard_alpha.address)

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    balance_before = ripe_token.balanceOf(mock_undy_v2.address)

    deposit, yield_bonus = lootbox.distributeUnderscoreRewards(
        sender=switchboard_alpha.address
    )

    # Only yield bonus, no deposit rewards
    assert deposit == 0
    assert yield_bonus == 100 * EIGHTEEN_DECIMALS

    balance_after = ripe_token.balanceOf(mock_undy_v2.address)
    assert balance_after == balance_before + 100 * EIGHTEEN_DECIMALS


def test_distribute_with_zero_available_ripe(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
):
    """No RIPE in ledger, should revert"""
    # Setup with 0 RIPE available
    setup_underscore_rewards(0)

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    with boa.reverts("no rewards to distribute"):
        lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)


def test_distribute_with_one_wei(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
    ripe_token,
    mock_undy_v2,
):
    """Minimal amounts - 1 wei scenario"""
    # Set both amounts to 1 wei
    lootbox.setUndyDepositRewardsAmount(1, sender=switchboard_alpha.address)
    lootbox.setUndyYieldBonusAmount(1, sender=switchboard_alpha.address)

    setup_underscore_rewards(100 * EIGHTEEN_DECIMALS)

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    balance_before = ripe_token.balanceOf(mock_undy_v2.address)

    deposit, yield_bonus = lootbox.distributeUnderscoreRewards(
        sender=switchboard_alpha.address
    )

    # Should get 2 wei total (1 + 1)
    assert deposit + yield_bonus == 2

    balance_after = ripe_token.balanceOf(mock_undy_v2.address)
    assert balance_after == balance_before + 2


def test_distribute_exact_ripe_match(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
):
    """ripeAvailForRewards exactly equals totalRewardsAmount"""
    # Setup with exactly the needed amount
    exact_amount = 200 * EIGHTEEN_DECIMALS
    setup_underscore_rewards(exact_amount)

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    deposit, yield_bonus = lootbox.distributeUnderscoreRewards(
        sender=switchboard_alpha.address
    )

    # Should get full amounts
    assert deposit == 100 * EIGHTEEN_DECIMALS
    assert yield_bonus == 100 * EIGHTEEN_DECIMALS


def test_distribute_reverts_no_underscore_distributor(
    lootbox,
    switchboard_alpha,
    ledger,
    mission_control,
):
    """Missing underscore registry setup"""
    # Setup RIPE but DON'T setup underscore registry
    ledger.setRipeAvailForRewards(1000 * EIGHTEEN_DECIMALS, sender=switchboard_alpha.address)

    # Make sure underscore registry is not set (or set to zero address)
    mission_control.setUnderscoreRegistry(ZERO_ADDRESS, sender=switchboard_alpha.address)

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    with boa.reverts("no underscore distributor"):
        lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)


########################################
# Section 5: Integration with Rewards System
########################################


def test_distribute_decrements_ripe_avail_for_rewards(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
    ledger,
):
    """Ledger accounting correct - ripeAvailForRewards decremented"""
    initial_ripe = 1000 * EIGHTEEN_DECIMALS
    setup_underscore_rewards(initial_ripe)

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    deposit, yield_bonus = lootbox.distributeUnderscoreRewards(
        sender=switchboard_alpha.address
    )

    distributed_amount = deposit + yield_bonus

    # Check ledger decremented by distributed amount
    final_ripe = ledger.ripeAvailForRewards()
    assert final_ripe == initial_ripe - distributed_amount


def test_distribute_after_global_rewards_update(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
    setRipeRewardsConfig,
    teller,
):
    """Integration with _getLatestGlobalRipeRewards()"""
    setup_underscore_rewards(10000 * EIGHTEEN_DECIMALS)

    # Configure regular RIPE rewards
    setRipeRewardsConfig(
        _arePointsEnabled=True,
        _ripePerBlock=10,
        _borrowersAlloc=25_00,
        _stakersAlloc=25_00,
        _votersAlloc=25_00,
        _genDepositorsAlloc=25_00
    )

    # Update global rewards first
    boa.env.time_travel(blocks=100)
    lootbox.updateRipeRewards(sender=teller.address)

    # Now distribute underscore rewards
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    deposit, yield_bonus = lootbox.distributeUnderscoreRewards(
        sender=switchboard_alpha.address
    )

    # Should succeed and return normal amounts
    assert deposit == 100 * EIGHTEEN_DECIMALS
    assert yield_bonus == 100 * EIGHTEEN_DECIMALS


def test_distribute_respects_pending_allocations(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
    setRipeRewardsConfig,
    ledger,
):
    """Doesn't double-count pending rewards"""
    # Setup with limited RIPE
    limited_ripe = 500 * EIGHTEEN_DECIMALS
    setup_underscore_rewards(limited_ripe)

    # Configure rewards that will consume some RIPE
    setRipeRewardsConfig(
        _arePointsEnabled=True,
        _ripePerBlock=1 * EIGHTEEN_DECIMALS,  # 1 RIPE per block
        _borrowersAlloc=25_00,
        _stakersAlloc=25_00,
        _votersAlloc=25_00,
        _genDepositorsAlloc=25_00
    )

    # Time travel to generate pending rewards
    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    # Get rewards state before distribution
    rewards_before = ledger.ripeRewards()

    # Distribute underscore rewards
    # This should account for pending allocations via _getLatestGlobalRipeRewards()
    deposit, yield_bonus = lootbox.distributeUnderscoreRewards(
        sender=switchboard_alpha.address
    )

    # Should successfully distribute (accounting for pending rewards)
    assert deposit + yield_bonus > 0


def test_distribute_updates_ledger_new_ripe_rewards(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
    ledger,
):
    """ripeRewards.newRipeRewards incremented correctly"""
    setup_underscore_rewards(1000 * EIGHTEEN_DECIMALS)

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    # Get initial state
    initial_rewards = ledger.ripeRewards()

    deposit, yield_bonus = lootbox.distributeUnderscoreRewards(
        sender=switchboard_alpha.address
    )

    distributed_amount = deposit + yield_bonus

    # Get final state
    final_rewards = ledger.ripeRewards()

    # newRipeRewards should have increased by distributed amount
    # Note: This gets reset/calculated in _getLatestGlobalRipeRewards,
    # but the distribute function adds to it
    assert final_rewards.newRipeRewards >= distributed_amount


########################################
# Section 6: Event Logging
########################################


def test_distribute_emits_correct_event(
    lootbox,
    switchboard_alpha,
    setup_underscore_rewards,
    mock_undy_v2,
):
    """Verify UnderscoreRewardsDistributed event with all fields"""
    setup_underscore_rewards()

    boa.env.time_travel(blocks=ONE_DAY_BLOCKS + 1)

    # Capture the block number
    current_block = boa.env.evm.patch.block_number

    # Distribute
    deposit, yield_bonus = lootbox.distributeUnderscoreRewards(
        sender=switchboard_alpha.address
    )

    # Get events
    events = lootbox.get_logs()

    # Find UnderscoreRewardsDistributed event
    underscore_events = [e for e in events if type(e).__name__ == "UnderscoreRewardsDistributed"]

    assert len(underscore_events) == 1

    event = underscore_events[0]
    assert event.underscoreAddr == mock_undy_v2.address
    assert event.depositAmount == deposit
    assert event.yieldAmount == yield_bonus
    assert event.blockNumber == current_block


########################################
# Section 7: Setter Functions Tests
########################################


# setHasUnderscoreRewards tests


def test_set_has_underscore_rewards_enable(
    lootbox,
    switchboard_alpha,
):
    """Successfully enable underscore rewards"""
    # Disable first
    lootbox.setHasUnderscoreRewards(False, sender=switchboard_alpha.address)
    assert lootbox.hasUnderscoreRewards() == False

    # Enable
    lootbox.setHasUnderscoreRewards(True, sender=switchboard_alpha.address)
    assert lootbox.hasUnderscoreRewards() == True


def test_set_has_underscore_rewards_requires_switchboard(
    lootbox,
    alice,
):
    """Non-switchboard cannot change hasUnderscoreRewards"""
    with boa.reverts("no perms"):
        lootbox.setHasUnderscoreRewards(False, sender=alice)


def test_set_has_underscore_rewards_reverts_when_paused(
    lootbox,
    switchboard_alpha,
):
    """Cannot change when contract is paused"""
    lootbox.pause(True, sender=switchboard_alpha.address)

    with boa.reverts("contract paused"):
        lootbox.setHasUnderscoreRewards(False, sender=switchboard_alpha.address)


def test_set_has_underscore_rewards_reverts_no_change(
    lootbox,
    switchboard_alpha,
):
    """Reverts if value doesn't change"""
    current_value = lootbox.hasUnderscoreRewards()

    with boa.reverts("no change"):
        lootbox.setHasUnderscoreRewards(current_value, sender=switchboard_alpha.address)


# setUnderscoreSendInterval tests


def test_set_underscore_send_interval_success(
    lootbox,
    switchboard_alpha,
):
    """Successfully update send interval"""
    new_interval = ONE_DAY_BLOCKS * 2  # 2 days

    lootbox.setUnderscoreSendInterval(new_interval, sender=switchboard_alpha.address)

    assert lootbox.underscoreSendInterval() == new_interval


def test_set_underscore_send_interval_requires_switchboard(
    lootbox,
    alice,
):
    """Non-switchboard cannot change interval"""
    with boa.reverts("no perms"):
        lootbox.setUnderscoreSendInterval(ONE_DAY_BLOCKS * 2, sender=alice)


def test_set_underscore_send_interval_reverts_when_paused(
    lootbox,
    switchboard_alpha,
):
    """Cannot change when contract is paused"""
    lootbox.pause(True, sender=switchboard_alpha.address)

    with boa.reverts("contract paused"):
        lootbox.setUnderscoreSendInterval(ONE_DAY_BLOCKS * 2, sender=switchboard_alpha.address)


def test_set_underscore_send_interval_validation(
    lootbox,
    switchboard_alpha,
):
    """Test validation rules for interval"""
    # Cannot set to MAX_UINT256
    with boa.reverts("invalid interval"):
        lootbox.setUnderscoreSendInterval(MAX_UINT256, sender=switchboard_alpha.address)

    # Cannot set below ONE_DAY
    with boa.reverts("invalid interval"):
        lootbox.setUnderscoreSendInterval(ONE_DAY_BLOCKS - 1, sender=switchboard_alpha.address)

    # Cannot set to same value
    current = lootbox.underscoreSendInterval()
    with boa.reverts("no change"):
        lootbox.setUnderscoreSendInterval(current, sender=switchboard_alpha.address)


# setUndyDepositRewardsAmount tests


def test_set_undy_deposit_rewards_amount_success(
    lootbox,
    switchboard_alpha,
):
    """Successfully update deposit rewards amount"""
    new_amount = 500 * EIGHTEEN_DECIMALS

    lootbox.setUndyDepositRewardsAmount(new_amount, sender=switchboard_alpha.address)

    assert lootbox.undyDepositRewardsAmount() == new_amount


def test_set_undy_deposit_rewards_amount_requires_switchboard(
    lootbox,
    alice,
):
    """Non-switchboard cannot change deposit amount"""
    with boa.reverts("no perms"):
        lootbox.setUndyDepositRewardsAmount(500 * EIGHTEEN_DECIMALS, sender=alice)


def test_set_undy_deposit_rewards_amount_reverts_when_paused(
    lootbox,
    switchboard_alpha,
):
    """Cannot change when contract is paused"""
    lootbox.pause(True, sender=switchboard_alpha.address)

    with boa.reverts("contract paused"):
        lootbox.setUndyDepositRewardsAmount(500 * EIGHTEEN_DECIMALS, sender=switchboard_alpha.address)


def test_set_undy_deposit_rewards_amount_validation(
    lootbox,
    switchboard_alpha,
):
    """Test validation rules for deposit amount"""
    # Cannot set to MAX_UINT256
    with boa.reverts("invalid amount"):
        lootbox.setUndyDepositRewardsAmount(MAX_UINT256, sender=switchboard_alpha.address)

    # Cannot set to same value
    current = lootbox.undyDepositRewardsAmount()
    with boa.reverts("no change"):
        lootbox.setUndyDepositRewardsAmount(current, sender=switchboard_alpha.address)

    # CAN set to 0 (tested in edge cases)
    lootbox.setUndyYieldBonusAmount(1, sender=switchboard_alpha.address)  # Ensure other is non-zero
    lootbox.setUndyDepositRewardsAmount(0, sender=switchboard_alpha.address)
    assert lootbox.undyDepositRewardsAmount() == 0


# setUndyYieldBonusAmount tests


def test_set_undy_yield_bonus_amount_success(
    lootbox,
    switchboard_alpha,
):
    """Successfully update yield bonus amount"""
    new_amount = 300 * EIGHTEEN_DECIMALS

    lootbox.setUndyYieldBonusAmount(new_amount, sender=switchboard_alpha.address)

    assert lootbox.undyYieldBonusAmount() == new_amount


def test_set_undy_yield_bonus_amount_requires_switchboard(
    lootbox,
    alice,
):
    """Non-switchboard cannot change yield amount"""
    with boa.reverts("no perms"):
        lootbox.setUndyYieldBonusAmount(300 * EIGHTEEN_DECIMALS, sender=alice)


def test_set_undy_yield_bonus_amount_reverts_when_paused(
    lootbox,
    switchboard_alpha,
):
    """Cannot change when contract is paused"""
    lootbox.pause(True, sender=switchboard_alpha.address)

    with boa.reverts("contract paused"):
        lootbox.setUndyYieldBonusAmount(300 * EIGHTEEN_DECIMALS, sender=switchboard_alpha.address)


def test_set_undy_yield_bonus_amount_validation(
    lootbox,
    switchboard_alpha,
):
    """Test validation rules for yield amount"""
    # Cannot set to MAX_UINT256
    with boa.reverts("invalid amount"):
        lootbox.setUndyYieldBonusAmount(MAX_UINT256, sender=switchboard_alpha.address)

    # Cannot set to same value
    current = lootbox.undyYieldBonusAmount()
    with boa.reverts("no change"):
        lootbox.setUndyYieldBonusAmount(current, sender=switchboard_alpha.address)

    # CAN set to 0 (tested in edge cases)
    lootbox.setUndyDepositRewardsAmount(1, sender=switchboard_alpha.address)  # Ensure other is non-zero
    lootbox.setUndyYieldBonusAmount(0, sender=switchboard_alpha.address)
    assert lootbox.undyYieldBonusAmount() == 0
