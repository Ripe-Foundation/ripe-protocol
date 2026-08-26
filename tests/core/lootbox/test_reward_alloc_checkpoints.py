import boa

from constants import EIGHTEEN_DECIMALS


def _points_tuple(points):
    return (
        points.lastUsdValue,
        points.ripeStakerPoints,
        points.ripeVotePoints,
        points.ripeGenPoints,
        points.lastUpdate,
    )


def test_live_allocation_change_is_allowed_at_proposal_and_execution(
    alpha_token,
    setGeneralConfig,
    setAssetConfig,
    simple_erc20_vault,
    vault_book,
    mission_control,
    switchboard_bravo,
    governance,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    setGeneralConfig()
    setAssetConfig(
        alpha_token,
        _vaultIds=[1, vault_id],
        _stakersPointsAlloc=17,
        _voterPointsAlloc=29,
    )

    action_id = switchboard_bravo.setAssetDepositParams(
        alpha_token,
        [1, vault_id],
        23,
        31,
        2_000 * EIGHTEEN_DECIMALS,
        20_000 * EIGHTEEN_DECIMALS,
        0,
        sender=governance.address,
    )
    assert action_id > 0

    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    assert switchboard_bravo.executePendingAction(
        action_id,
        sender=governance.address,
    )
    config = mission_control.assetConfig(alpha_token)
    assert config.stakersPointsAlloc == 23
    assert config.voterPointsAlloc == 31


def test_update_ripe_rewards_leaves_global_deposit_points_unchanged(
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
):
    setRipeRewardsConfig(True, 12, 25_00, 25_00, 25_00, 25_00)
    lootbox.updateRipeRewards(sender=teller.address)

    ledger.eval("self.globalDepositPoints.lastUsdValue = 17")
    ledger.eval("self.globalDepositPoints.ripeStakerPoints = 23")
    ledger.eval("self.globalDepositPoints.ripeVotePoints = 29")
    ledger.eval("self.globalDepositPoints.ripeGenPoints = 31")
    ledger.eval("self.globalDepositPoints.lastUpdate = 37")
    points_before = _points_tuple(ledger.globalDepositPoints())
    reward_last_update_before = ledger.ripeRewards().lastUpdate

    boa.env.time_travel(blocks=7)
    lootbox.updateRipeRewards(sender=teller.address)

    assert _points_tuple(ledger.globalDepositPoints()) == points_before
    assert ledger.ripeRewards().lastUpdate == boa.env.evm.patch.block_number
    assert ledger.ripeRewards().lastUpdate > reward_last_update_before
