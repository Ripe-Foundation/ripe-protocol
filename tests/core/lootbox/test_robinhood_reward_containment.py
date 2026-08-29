import boa

from constants import ZERO_ADDRESS


def _deploy_registered_robinhood_alpha(
    ripe_hq,
    switchboard,
    switchboard_alpha,
    governance,
):
    alpha = boa.load(
        "contracts/config/SwitchboardAlpha.vy",
        ripe_hq,
        ZERO_ADDRESS,
        switchboard_alpha.MIN_STALE_TIME(),
        switchboard_alpha.MAX_STALE_TIME(),
        600,
        50_400,
        0,  # Pyth is disabled in the Robinhood launch profile
        name="robinhood_reward_containment_alpha",
    )
    assert switchboard.startAddNewAddressToRegistry(
        alpha,
        "RH reward containment alpha",
        sender=governance.address,
    )
    boa.env.time_travel(blocks=switchboard.registryChangeTimeLock())
    assert switchboard.confirmNewAddressToRegistry(
        alpha,
        sender=governance.address,
    ) > 0
    assert alpha.setActionTimeLockAfterSetup(sender=governance.address)
    assert alpha.actionTimeLock() == 600
    return alpha


def test_lootbox_clock_continues_while_paused(
    setRipeRewardsConfig,
    lootbox,
    ledger,
    teller,
    switchboard_charlie,
    governance,
):
    rate = 9
    setRipeRewardsConfig(True, rate, 10_00, 90_00, 0, 0)
    first = lootbox.updateRipeRewards(sender=teller.address)
    assert first.newRipeRewards == 0

    boa.env.time_travel(blocks=5)
    assert switchboard_charlie.pause(lootbox, True, sender=governance.address)
    checkpoint = ledger.ripeRewards().lastUpdate
    boa.env.time_travel(blocks=11)
    updated = lootbox.updateRipeRewards(sender=teller.address)
    assert updated.newRipeRewards == rate * 16
    assert ledger.ripeRewards().lastUpdate > checkpoint

    assert switchboard_charlie.pause(lootbox, False, sender=governance.address)
    assert lootbox.updateRipeRewards(sender=teller.address).newRipeRewards == 0


def test_ordered_zero_then_pause_keeps_disabled_interval_reward_free(
    setRipeRewardsConfig,
    setGeneralConfig,
    lootbox,
    ledger,
    teller,
    mission_control,
    ripe_hq,
    switchboard,
    switchboard_alpha,
    switchboard_charlie,
    governance,
    bob,
    credit_engine,
):
    rate = 9
    setGeneralConfig()
    setRipeRewardsConfig(True, rate, 10_00, 90_00, 0, 0, 75_00, 33_00, 10)
    lootbox.updateRipeRewards(sender=teller.address)
    boa.env.time_travel(blocks=7)

    rh_alpha = _deploy_registered_robinhood_alpha(
        ripe_hq,
        switchboard,
        switchboard_alpha,
        governance,
    )
    mission_control.setCanPerformLiteAction(
        bob,
        True,
        sender=switchboard_charlie.address,
    )

    rewards = mission_control.rewardsConfig()
    with boa.reverts("no perms"):
        rh_alpha.setRipePerBlock(0, sender=bob)
    with boa.reverts("no perms"):
        rh_alpha.setAutoStakeParams(75_00, 33_00, 0, sender=bob)

    initial_ratios = (rewards.autoStakeRatio, rewards.autoStakeDurationRatio)
    initiated_block = boa.env.evm.patch.block_number
    ripe_action = rh_alpha.setRipePerBlock(0, sender=governance.address)
    stability_action = rh_alpha.setAutoStakeParams(
        initial_ratios[0],
        initial_ratios[1],
        0,
        sender=governance.address,
    )
    assert ripe_action != stability_action
    ripe_confirmation = rh_alpha.getActionConfirmationBlock(ripe_action)
    stability_confirmation = rh_alpha.getActionConfirmationBlock(stability_action)
    assert ripe_confirmation - initiated_block == 600
    assert stability_confirmation - initiated_block == 600

    boa.env.time_travel(blocks=599)
    assert not rh_alpha.executePendingAction(ripe_action, sender=governance.address)
    assert not rh_alpha.executePendingAction(stability_action, sender=governance.address)
    assert not lootbox.isPaused()
    assert rh_alpha.hasPendingAction(ripe_action)
    assert rh_alpha.hasPendingAction(stability_action)

    boa.env.time_travel(blocks=1)
    assert rh_alpha.executePendingAction(ripe_action, sender=governance.address)
    assert rh_alpha.executePendingAction(stability_action, sender=governance.address)
    assert not lootbox.isPaused()
    assert not rh_alpha.hasPendingAction(ripe_action)
    assert not rh_alpha.hasPendingAction(stability_action)
    zeroed = mission_control.rewardsConfig()
    assert zeroed.ripePerBlock == 0
    assert zeroed.stabPoolRipePerDollarClaimed == 0
    assert (zeroed.autoStakeRatio, zeroed.autoStakeDurationRatio) == initial_ratios

    # Alpha settles the old rate before writing zero. The lite signer can then
    # disable the user-facing paths and pause Lootbox.
    assert rh_alpha.setCanClaimLoot(False, sender=bob)
    assert rh_alpha.setCanClaimInStabPool(False, sender=bob)
    assert switchboard_charlie.pause(lootbox, True, sender=bob)
    assert lootbox.isPaused()
    gen = mission_control.genConfig()
    rewards = mission_control.rewardsConfig()
    assert not gen.canClaimLoot
    assert not gen.canClaimInStabPool
    assert rewards.arePointsEnabled

    # A qualified lite signer can pause but cannot unpause.
    with boa.reverts("no perms"):
        switchboard_charlie.pause(lootbox, False, sender=bob)

    # The clock remains callable while paused, but the zero rate keeps the
    # interval reward-free.
    boa.env.time_travel(blocks=11)
    budget_before = ledger.ripeAvailForRewards()
    checkpoint = lootbox.updateRipeRewards(sender=teller.address)
    assert checkpoint.newRipeRewards == 0
    assert ledger.ripeAvailForRewards() == budget_before
    assert switchboard_charlie.pause(lootbox, False, sender=governance.address)
    assert not mission_control.genConfig().canClaimLoot
    assert not mission_control.genConfig().canClaimInStabPool

    # RipeHq is a governance-only, system-wide last resort and does not erase accounting.
    stored = ledger.ripeRewards()
    with boa.reverts("no perms"):
        ripe_hq.setMintingEnabled(False, sender=bob)
    ripe_hq.setMintingEnabled(False, sender=governance.address)
    assert not ripe_hq.canMintGreen(credit_engine)
    assert not ripe_hq.canMintRipe(lootbox)
    assert ledger.ripeRewards() == stored

    # Every reversal is explicit and governance-only; the Stability gate is separate.
    with boa.reverts("no perms"):
        rh_alpha.setCanClaimLoot(True, sender=bob)
    with boa.reverts("no perms"):
        rh_alpha.setCanClaimInStabPool(True, sender=bob)
    ripe_hq.setMintingEnabled(True, sender=governance.address)
    assert rh_alpha.setCanClaimLoot(True, sender=governance.address)
    assert not mission_control.genConfig().canClaimInStabPool
    assert rh_alpha.setCanClaimInStabPool(True, sender=governance.address)
    assert mission_control.genConfig().canClaimLoot
    assert mission_control.genConfig().canClaimInStabPool
