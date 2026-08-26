import boa
import pytest

from constants import EIGHTEEN_DECIMALS


def _points_tuple(points):
    return (
        points.lastUsdValue,
        points.ripeStakerPoints,
        points.ripeVotePoints,
        points.ripeGenPoints,
        points.lastUpdate,
    )


@pytest.mark.parametrize("are_points_enabled", [False, True])
def test_live_allocation_change_is_rejected_regardless_of_points_flag(
    are_points_enabled,
    alpha_token,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    simple_erc20_vault,
    vault_book,
    mission_control,
    switchboard_bravo,
    governance,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    setGeneralConfig()
    setRipeRewardsConfig(are_points_enabled, 0, 0, 0, 0, 0)
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=20,
    )

    before = mission_control.assetConfig(alpha_token)
    action_id_before = switchboard_bravo.actionId()
    with boa.reverts("invalid asset deposit params"):
        switchboard_bravo.setAssetDepositParams(
            alpha_token,
            [vault_id],
            0,
            8,
            2_000 * EIGHTEEN_DECIMALS,
            20_000 * EIGHTEEN_DECIMALS,
            0,
            sender=governance.address,
        )

    assert mission_control.assetConfig(alpha_token) == before
    assert switchboard_bravo.actionId() == action_id_before


def test_live_allocation_head_decode_uses_distinct_staker_and_voter_words(
    alpha_token,
    setGeneralConfig,
    setAssetConfig,
    simple_erc20_vault,
    vault_book,
    switchboard_bravo,
    governance,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    vault_ids = [1, vault_id]
    setGeneralConfig()
    setAssetConfig(
        alpha_token,
        _vaultIds=vault_ids,
        _stakersPointsAlloc=17,
        _voterPointsAlloc=29,
    )

    action_id = switchboard_bravo.setAssetDepositParams(
        alpha_token,
        vault_ids,
        17,
        29,
        2_000 * EIGHTEEN_DECIMALS,
        20_000 * EIGHTEEN_DECIMALS,
        0,
        sender=governance.address,
    )
    assert action_id > 0

    with boa.reverts("invalid asset deposit params"):
        switchboard_bravo.setAssetDepositParams(
            alpha_token,
            vault_ids,
            29,
            17,
            2_000 * EIGHTEEN_DECIMALS,
            20_000 * EIGHTEEN_DECIMALS,
            0,
            sender=governance.address,
        )


def test_live_allocation_is_revalidated_at_execution(
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
        _vaultIds=[vault_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
    )
    action_id = switchboard_bravo.setAssetDepositParams(
        alpha_token,
        [vault_id],
        0,
        0,
        2_000 * EIGHTEEN_DECIMALS,
        20_000 * EIGHTEEN_DECIMALS,
        0,
        sender=governance.address,
    )

    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_id],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=7,
    )
    live_before = mission_control.assetConfig(alpha_token)
    pending_before = switchboard_bravo.pendingAssetConfig(action_id)
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    with boa.reverts("invalid asset config"):
        switchboard_bravo.executePendingAction(
            action_id,
            sender=governance.address,
        )

    assert mission_control.assetConfig(alpha_token) == live_before
    assert switchboard_bravo.pendingAssetConfig(action_id) == pending_before
    assert switchboard_bravo.hasPendingAction(action_id)


def test_live_new_asset_requires_zero_allocations(
    bravo_token,
    switchboard_bravo,
    governance,
):
    with boa.reverts("invalid asset"):
        switchboard_bravo.addAsset(
            bravo_token,
            [1],
            0,
            1,
            1_000,
            10_000,
            0,
            (0, 0, 0, 0, 0, 0),
            False,
            False,
            False,
            True,
            True,
            True,
            False,
            True,
            True,
            True,
            0,
            sender=governance.address,
        )

    action_id = switchboard_bravo.addAsset(
        bravo_token,
        [1],
        0,
        0,
        1_000,
        10_000,
        0,
        (0, 0, 0, 0, 0, 0),
        False,
        False,
        False,
        True,
        True,
        True,
        False,
        True,
        True,
        True,
        0,
        sender=governance.address,
    )
    assert action_id > 0


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
