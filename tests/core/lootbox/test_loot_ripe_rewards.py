import pytest
import boa


################
# Ripe Rewards #
################


def test_loot_ripe_rewards_basic(
    setRipeRewardsConfig,
    lootbox,
    teller,
    ledger,
):
    ripe_per_block = 5

    borrowers_alloc = 25_00
    stakers_alloc = 25_00
    voters_alloc = 25_00
    gen_depositors_alloc = 25_00

    # set config
    setRipeRewardsConfig(True, ripe_per_block, borrowers_alloc, stakers_alloc, voters_alloc, gen_depositors_alloc)

    # first update
    rewards = lootbox.updateRipeRewards(sender=teller.address)
    ledger_data = ledger.ripeRewards()

    # all zeroes on first save
    assert rewards.borrowers == ledger_data.borrowers == 0
    assert rewards.stakers == ledger_data.stakers == 0
    assert rewards.voters == ledger_data.voters == 0
    assert rewards.genDepositors == ledger_data.genDepositors == 0

    assert rewards.newRipeRewards == ledger_data.newRipeRewards == 0
    assert rewards.lastUpdate == ledger_data.lastUpdate == boa.env.evm.patch.block_number # updated tho

    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # update again
    rewards = lootbox.updateRipeRewards(sender=teller.address)
    ledger_data = ledger.ripeRewards()

    # calc expected
    expected_total = elapsed * ripe_per_block
    
    assert rewards.borrowers == ledger_data.borrowers == (expected_total * borrowers_alloc // 100_00)
    assert rewards.stakers == ledger_data.stakers == (expected_total * stakers_alloc // 100_00)
    assert rewards.voters == ledger_data.voters == (expected_total * voters_alloc // 100_00)
    assert rewards.genDepositors == ledger_data.genDepositors == (expected_total * gen_depositors_alloc // 100_00)

    assert rewards.newRipeRewards == ledger_data.newRipeRewards == expected_total
    assert rewards.lastUpdate == ledger_data.lastUpdate == boa.env.evm.patch.block_number


def test_loot_ripe_rewards_time_edge_cases(
    setRipeRewardsConfig,
    lootbox,
    teller,
):
    ripe_per_block = 5
    alloc = 25_00  # 25% each

    # set config
    setRipeRewardsConfig(True, ripe_per_block, alloc, alloc, alloc, alloc)

    # Test no elapsed blocks
    rewards = lootbox.updateRipeRewards(sender=teller.address)
    assert rewards.newRipeRewards == 0
    assert rewards.lastUpdate == boa.env.evm.patch.block_number

    # Test single block
    boa.env.time_travel(blocks=1)
    rewards = lootbox.updateRipeRewards(sender=teller.address)
    assert rewards.newRipeRewards == ripe_per_block
    assert rewards.lastUpdate == boa.env.evm.patch.block_number

    # Test multiple updates in same block
    rewards1 = lootbox.updateRipeRewards(sender=teller.address)
    rewards2 = lootbox.updateRipeRewards(sender=teller.address)
    assert rewards1.newRipeRewards == rewards2.newRipeRewards == 0
    assert rewards1.lastUpdate == rewards2.lastUpdate == boa.env.evm.patch.block_number


def test_loot_ripe_rewards_allocation_configs(
    setRipeRewardsConfig,
    lootbox,
    teller,
):
    ripe_per_block = 10
    elapsed = 10
    expected_total = ripe_per_block * elapsed

    # Test uneven allocations
    borrowers_alloc = 40_00  # 40%
    stakers_alloc = 30_00    # 30%
    voters_alloc = 20_00     # 20%
    gen_depositors_alloc = 10_00  # 10%

    setRipeRewardsConfig(True, ripe_per_block, borrowers_alloc, stakers_alloc, voters_alloc, gen_depositors_alloc)
    
    # Initial update to set lastUpdate
    lootbox.updateRipeRewards(sender=teller.address)
    
    boa.env.time_travel(blocks=elapsed)
    rewards = lootbox.updateRipeRewards(sender=teller.address)

    assert rewards.borrowers == (expected_total * borrowers_alloc // 100_00)
    assert rewards.stakers == (expected_total * stakers_alloc // 100_00)
    assert rewards.voters == (expected_total * voters_alloc // 100_00)
    assert rewards.genDepositors == (expected_total * gen_depositors_alloc // 100_00)

    # Now set non-zero rewards per block but zero allocations
    setRipeRewardsConfig(True, ripe_per_block, 0, 0, 0, 0)
    boa.env.time_travel(blocks=elapsed)
    rewards_b = lootbox.updateRipeRewards(sender=teller.address)
    assert rewards_b.newRipeRewards == 0

    assert rewards_b.borrowers == rewards.borrowers # same as before
    assert rewards_b.stakers == rewards.stakers
    assert rewards_b.voters == rewards.voters
    assert rewards_b.genDepositors == rewards.genDepositors

    # Now set single allocation
    setRipeRewardsConfig(True, ripe_per_block, 100_00, 0, 0, 0)  # 100% to borrowers
    boa.env.time_travel(blocks=elapsed)
    rewards_c = lootbox.updateRipeRewards(sender=teller.address)
    assert rewards_c.newRipeRewards == expected_total

    assert rewards_c.borrowers == rewards_b.borrowers + expected_total
    assert rewards_c.stakers == rewards_b.stakers
    assert rewards_c.voters == rewards_b.voters
    assert rewards_c.genDepositors == rewards_b.genDepositors


def test_loot_ripe_rewards_uneven_allocations(
    setRipeRewardsConfig,
    lootbox,
    teller,
):
    ripe_per_block = 10
    elapsed = 10
    expected_total = ripe_per_block * elapsed

    # Test uneven allocations
    borrowers_alloc = 40_00  # 40%
    stakers_alloc = 30_00    # 30%
    voters_alloc = 20_00     # 20%
    gen_depositors_alloc = 10_00  # 10%

    setRipeRewardsConfig(True, ripe_per_block, borrowers_alloc, stakers_alloc, voters_alloc, gen_depositors_alloc)
    
    # Initial update to set lastUpdate
    lootbox.updateRipeRewards(sender=teller.address)
    
    boa.env.time_travel(blocks=elapsed)
    rewards = lootbox.updateRipeRewards(sender=teller.address)

    assert rewards.borrowers == (expected_total * borrowers_alloc // 100_00)
    assert rewards.stakers == (expected_total * stakers_alloc // 100_00)
    assert rewards.voters == (expected_total * voters_alloc // 100_00)
    assert rewards.genDepositors == (expected_total * gen_depositors_alloc // 100_00)


def test_loot_ripe_rewards_zero_allocations(
    setRipeRewardsConfig,
    lootbox,
    teller,
):
    ripe_per_block = 10
    elapsed = 10

    # Set non-zero rewards per block but zero allocations
    setRipeRewardsConfig(True, ripe_per_block, 0, 0, 0, 0)
    lootbox.updateRipeRewards(sender=teller.address)  # Set new lastUpdate

    boa.env.time_travel(blocks=elapsed)
    rewards = lootbox.updateRipeRewards(sender=teller.address)
    assert rewards.newRipeRewards == 0
    assert rewards.borrowers == rewards.stakers == rewards.voters == rewards.genDepositors == 0


def test_loot_ripe_rewards_single_allocation(
    setRipeRewardsConfig,
    lootbox,
    teller,
):
    ripe_per_block = 10
    elapsed = 10
    expected_total = ripe_per_block * elapsed

    # Set single allocation
    setRipeRewardsConfig(True, ripe_per_block, 100_00, 0, 0, 0)  # 100% to borrowers
    lootbox.updateRipeRewards(sender=teller.address)  # Set new lastUpdate

    boa.env.time_travel(blocks=elapsed)
    rewards = lootbox.updateRipeRewards(sender=teller.address)
    assert rewards.borrowers == expected_total
    assert rewards.stakers == rewards.voters == rewards.genDepositors == 0


def test_loot_ripe_rewards_zero_per_block(
    setRipeRewardsConfig,
    lootbox,
    teller,
):
    alloc = 25_00  # 25% each
    elapsed = 10

    setRipeRewardsConfig(True, 0, alloc, alloc, alloc, alloc)
    lootbox.updateRipeRewards(sender=teller.address) # initial update

    # Test with zero rewards per block
    boa.env.time_travel(blocks=elapsed)
    rewards = lootbox.updateRipeRewards(sender=teller.address)
    assert rewards.newRipeRewards == 0
    assert rewards.borrowers == rewards.stakers == rewards.voters == rewards.genDepositors == 0

    # Change to non-zero rewards and verify they start accumulating
    setRipeRewardsConfig(True, 5, alloc, alloc, alloc, alloc)
    rewards_b = lootbox.updateRipeRewards(sender=teller.address)
    assert rewards_b.newRipeRewards == 0  # No elapsed blocks since last update
    assert rewards_b.lastUpdate == boa.env.evm.patch.block_number

    boa.env.time_travel(blocks=elapsed)
    rewards_c = lootbox.updateRipeRewards(sender=teller.address)
    assert rewards_c.newRipeRewards == 5 * elapsed
    assert rewards_c.borrowers == rewards_c.stakers == rewards_c.voters == rewards_c.genDepositors == (5 * elapsed * alloc // 100_00)


def test_loot_ripe_rewards_ledger_state(
    setRipeRewardsConfig,
    lootbox,
    teller,
    ledger,
    switchboard_alpha,
):
    ripe_per_block = 5
    alloc = 25_00  # 25% each
    elapsed = 10
    expected_total = ripe_per_block * elapsed

    # Set initial available rewards
    initial_avail = 1000
    ledger.setRipeAvailForRewards(initial_avail, sender=switchboard_alpha.address)

    # Set config and update
    setRipeRewardsConfig(True, ripe_per_block, alloc, alloc, alloc, alloc)
    lootbox.updateRipeRewards(sender=teller.address)  # Initial update
    
    # Verify initial state
    ledger_data = ledger.ripeRewards()
    assert ledger_data.newRipeRewards == 0
    assert ledger.ripeAvailForRewards() == initial_avail

    # Time travel and update
    boa.env.time_travel(blocks=elapsed)
    rewards = lootbox.updateRipeRewards(sender=teller.address)
    ledger_data = ledger.ripeRewards()

    # Verify rewards are saved correctly
    assert ledger_data.borrowers == rewards.borrowers == (expected_total * alloc // 100_00)
    assert ledger_data.stakers == rewards.stakers == (expected_total * alloc // 100_00)
    assert ledger_data.voters == rewards.voters == (expected_total * alloc // 100_00)
    assert ledger_data.genDepositors == rewards.genDepositors == (expected_total * alloc // 100_00)
    assert ledger_data.newRipeRewards == rewards.newRipeRewards == expected_total

    # Verify available rewards are reduced
    assert ledger.ripeAvailForRewards() == initial_avail - expected_total


def test_loot_ripe_rewards_ledger_accumulation(
    setRipeRewardsConfig,
    lootbox,
    teller,
    ledger,
    switchboard_alpha,
):
    ripe_per_block = 5
    alloc = 25_00  # 25% each
    elapsed = 10
    expected_total = ripe_per_block * elapsed

    # Set initial available rewards
    initial_avail = 1000
    ledger.setRipeAvailForRewards(initial_avail, sender=switchboard_alpha.address)

    # Set config and do multiple updates
    setRipeRewardsConfig(True, ripe_per_block, alloc, alloc, alloc, alloc)
    lootbox.updateRipeRewards(sender=teller.address)  # Initial update
    
    # First update
    boa.env.time_travel(blocks=elapsed)
    lootbox.updateRipeRewards(sender=teller.address)
    ledger_data1 = ledger.ripeRewards()
    
    # Second update
    boa.env.time_travel(blocks=elapsed)
    lootbox.updateRipeRewards(sender=teller.address)
    ledger_data2 = ledger.ripeRewards()

    # Verify rewards accumulate in ledger
    assert ledger_data2.borrowers == ledger_data1.borrowers + (expected_total * alloc // 100_00)
    assert ledger_data2.stakers == ledger_data1.stakers + (expected_total * alloc // 100_00)
    assert ledger_data2.voters == ledger_data1.voters + (expected_total * alloc // 100_00)
    assert ledger_data2.genDepositors == ledger_data1.genDepositors + (expected_total * alloc // 100_00)
    assert ledger_data2.newRipeRewards == expected_total  # Only new rewards, not accumulated

    # Verify available rewards are reduced by total distributed
    total_distributed = expected_total * 2  # Two updates
    assert ledger.ripeAvailForRewards() == initial_avail - total_distributed


def test_loot_ripe_rewards_limits(
    setRipeRewardsConfig,
    lootbox,
    teller,
    ledger,
    switchboard_alpha,
):
    ripe_per_block = 5
    alloc = 25_00  # 25% each
    elapsed = 10
    expected_total = ripe_per_block * elapsed

    # Set available rewards less than what would be distributed
    initial_avail = expected_total // 2
    ledger.setRipeAvailForRewards(initial_avail, sender=switchboard_alpha.address)

    setRipeRewardsConfig(True, ripe_per_block, alloc, alloc, alloc, alloc)
    lootbox.updateRipeRewards(sender=teller.address)  # Initial update
    
    boa.env.time_travel(blocks=elapsed)
    rewards = lootbox.updateRipeRewards(sender=teller.address)
    ledger_data = ledger.ripeRewards()

    # Verify only available amount was distributed
    assert rewards.newRipeRewards == initial_avail
    assert ledger.ripeAvailForRewards() == 0
    assert ledger_data.borrowers == (initial_avail * alloc // 100_00)


def test_loot_ripe_rewards_permissions(
    setRipeRewardsConfig,
    lootbox,
    ledger,
    bob,
):
    ripe_per_block = 5
    alloc = 25_00  # 25% each

    setRipeRewardsConfig(True, ripe_per_block, alloc, alloc, alloc, alloc)
    
    # Only Teller can call updateRipeRewards
    with boa.reverts("no perms"):
        lootbox.updateRipeRewards(sender=bob)

    # Only Lootbox can call setRipeRewards
    with boa.reverts("only Lootbox allowed"):
        ledger.setRipeRewards((0, 0, 0, 0, 0, 0), sender=bob)

    # Only switchboards can call setRipeAvailForRewards
    with boa.reverts("no perms"):
        ledger.setRipeAvailForRewards(1000, sender=bob)


def test_loot_ripe_rewards_pause(
    setRipeRewardsConfig,
    lootbox,
    switchboard_alpha,
    teller,
):
    ripe_per_block = 5
    alloc = 25_00  # 25% each

    setRipeRewardsConfig(True, ripe_per_block, alloc, alloc, alloc, alloc)
    
    # Pause the contract
    lootbox.pause(True, sender=switchboard_alpha.address)
    
    # Cannot update rewards when paused
    with boa.reverts("contract paused"):
        lootbox.updateRipeRewards(sender=teller.address)


def test_loot_ripe_rewards_state_transitions(
    setRipeRewardsConfig,
    lootbox,
    teller,
):
    ripe_per_block = 5
    alloc = 25_00  # 25% each
    elapsed = 10

    # Start with zero rewards
    setRipeRewardsConfig(True, 0, alloc, alloc, alloc, alloc)
    lootbox.updateRipeRewards(sender=teller.address)
    
    # Change to non-zero rewards
    setRipeRewardsConfig(True, ripe_per_block, alloc, alloc, alloc, alloc)
    lootbox.updateRipeRewards(sender=teller.address)
    
    boa.env.time_travel(blocks=elapsed)
    rewards = lootbox.updateRipeRewards(sender=teller.address)
    
    # Verify rewards start accumulating from new config
    expected_rewards = ripe_per_block * elapsed
    assert rewards.newRipeRewards == expected_rewards
    assert rewards.borrowers == (expected_rewards * alloc // 100_00)
    assert rewards.stakers == (expected_rewards * alloc // 100_00)
    assert rewards.voters == (expected_rewards * alloc // 100_00)
    assert rewards.genDepositors == (expected_rewards * alloc // 100_00)

    # Store previous rewards for accumulation check
    prev_borrowers = rewards.borrowers
    prev_stakers = rewards.stakers
    prev_voters = rewards.voters
    prev_gen_depositors = rewards.genDepositors

    # Change allocations
    new_alloc = 100_00  # 100% to borrowers
    setRipeRewardsConfig(True, ripe_per_block, new_alloc, 0, 0, 0)
    lootbox.updateRipeRewards(sender=teller.address)
    
    boa.env.time_travel(blocks=elapsed)
    rewards = lootbox.updateRipeRewards(sender=teller.address)
    
    # Verify new allocations take effect while preserving previous rewards
    new_rewards = ripe_per_block * elapsed
    assert rewards.newRipeRewards == new_rewards
    assert rewards.borrowers == prev_borrowers + new_rewards
    assert rewards.stakers == prev_stakers  # No new rewards
    assert rewards.voters == prev_voters    # No new rewards
    assert rewards.genDepositors == prev_gen_depositors  # No new rewards
