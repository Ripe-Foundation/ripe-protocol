import boa
import pytest

from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs


DEPOSIT_AMOUNT = 1_000 * EIGHTEEN_DECIMALS
REFUND_AMOUNT = 25_000 * EIGHTEEN_DECIMALS


def _user_points_state(points):
    return points.balancePoints, points.lastBalance, points.lastUpdate


def _asset_points_state(points):
    return (
        points.balancePoints,
        points.lastBalance,
        points.lastUsdValue,
        points.ripeStakerPoints,
        points.ripeVotePoints,
        points.ripeGenPoints,
        points.lastUpdate,
        points.precision,
    )


@pytest.fixture
def hr_position_factory(
    human_resources,
    mission_control,
    setAssetConfig,
    setGeneralConfig,
    setRipeRewardsConfig,
    switchboard_alpha,
    switchboard_delta,
    contributor_template,
    ledger,
    governance,
    ripe_token,
):
    def create_position(_with_position=True):
        vault_id = mission_control.coreRipeGovVaultId()
        setGeneralConfig()
        setAssetConfig(ripe_token, _vaultIds=[vault_id])
        setRipeRewardsConfig(True)
        mission_control.setRipeGovVaultConfig(
            ripe_token,
            100_00,
            False,
            (100, 1_000, 200_00, True, 10_00),
            sender=switchboard_alpha.address,
        )

        compensation = 500_000 * EIGHTEEN_DECIMALS
        mission_control.setHrConfig(
            (
                contributor_template.address,
                1_000_000 * EIGHTEEN_DECIMALS,
                30 * 24 * 3600,
                90 * 24 * 3600,
                365 * 24 * 3600,
                4 * 365 * 24 * 3600,
            ),
            sender=switchboard_delta.address,
        )
        ledger.setRipeAvailForHr(compensation, sender=switchboard_delta.address)

        action_id = human_resources.initiateNewContributor(
            "0x" + "11" * 20,
            "0x" + "22" * 20,
            compensation,
            7 * 24 * 3600,
            2 * 365 * 24 * 3600,
            90 * 24 * 3600,
            365 * 24 * 3600,
            100,
            sender=governance.address,
        )
        boa.env.time_travel(blocks=human_resources.actionTimeLock())
        human_resources.confirmNewContributor(action_id, sender=governance.address)
        contributor = filter_logs(
            human_resources,
            "NewContributorConfirmed",
        )[-1].contributorAddr

        if _with_position:
            assert human_resources.cashRipeCheck(
                DEPOSIT_AMOUNT,
                200,
                sender=contributor,
            )
            assert ledger.userDepositPoints(
                contributor,
                vault_id,
                ripe_token,
            ).lastBalance > 0
        return contributor, vault_id

    return create_position


def test_full_transfer_checkpoints_depleted_contributor(
    hr_position_factory,
    human_resources,
    ripe_gov_vault,
    ripe_token,
    ledger,
    lootbox,
    teller,
    alice,
):
    contributor, vault_id = hr_position_factory()
    source_before = ledger.userDepositPoints(contributor, vault_id, ripe_token)
    raw_shares_before = ripe_gov_vault.userBalances(contributor, ripe_token)
    asset_amount_before = ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
    assert raw_shares_before > 0
    assert asset_amount_before > 0

    boa.env.time_travel(blocks=10)
    transferred_assets = human_resources.transferContributorRipeTokens(
        alice,
        200,
        sender=contributor,
    )

    source_after = ledger.userDepositPoints(contributor, vault_id, ripe_token)
    recipient_after = ledger.userDepositPoints(alice, vault_id, ripe_token)
    asset_after = ledger.assetDepositPoints(vault_id, ripe_token)

    assert transferred_assets == asset_amount_before
    assert ripe_gov_vault.userBalances(contributor, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(alice, ripe_token) == transferred_assets
    assert source_after.lastBalance == 0
    # Both values are lock-weighted Lootbox-share units. They are equal because
    # the source deposit and recipient transfer each apply the same fresh
    # 200-block lock; a different transfer lock should intentionally fail here.
    assert recipient_after.lastBalance == source_before.lastBalance
    assert recipient_after.lastBalance > 0
    assert asset_after.lastBalance == source_after.lastBalance + recipient_after.lastBalance
    assert source_after.balancePoints > source_before.balancePoints

    historical_points = source_after.balancePoints
    boa.env.time_travel(blocks=10)
    lootbox.updateDepositPoints(
        contributor,
        vault_id,
        ripe_gov_vault,
        ripe_token,
        sender=teller.address,
    )
    assert ledger.userDepositPoints(
        contributor,
        vault_id,
        ripe_token,
    ).balancePoints == historical_points


def test_cancel_and_burn_checkpoints_before_asset_unit_burn(
    hr_position_factory,
    human_resources,
    ripe_gov_vault,
    ripe_token,
    ledger,
    lootbox,
    teller,
):
    contributor, vault_id = hr_position_factory()
    source_before = ledger.userDepositPoints(contributor, vault_id, ripe_token)

    boa.env.time_travel(blocks=10)
    position_assets = ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
    raw_shares = ripe_gov_vault.userBalances(contributor, ripe_token)
    total_supply_before = ripe_token.totalSupply()
    assert position_assets > 0
    assert raw_shares > 0

    human_resources.refundAfterCancelPaycheck(
        REFUND_AMOUNT,
        True,
        sender=contributor,
    )

    source_after = ledger.userDepositPoints(contributor, vault_id, ripe_token)
    asset_after = ledger.assetDepositPoints(vault_id, ripe_token)
    actual_burn_assets = total_supply_before - ripe_token.totalSupply()

    assert ripe_gov_vault.userBalances(contributor, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == 0
    assert source_after.lastBalance == 0
    assert asset_after.lastBalance == source_after.lastBalance == 0
    assert actual_burn_assets == position_assets
    assert source_after.balancePoints > source_before.balancePoints

    historical_points = source_after.balancePoints
    boa.env.time_travel(blocks=10)
    lootbox.updateDepositPoints(
        contributor,
        vault_id,
        ripe_gov_vault,
        ripe_token,
        sender=teller.address,
    )
    assert ledger.userDepositPoints(
        contributor,
        vault_id,
        ripe_token,
    ).balancePoints == historical_points


def test_non_burn_cancellation_does_not_checkpoint(
    hr_position_factory,
    human_resources,
    ripe_gov_vault,
    ripe_token,
    ledger,
):
    contributor, vault_id = hr_position_factory()
    raw_shares_before = ripe_gov_vault.userBalances(contributor, ripe_token)
    position_assets_before = ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
    user_points_before = _user_points_state(
        ledger.userDepositPoints(contributor, vault_id, ripe_token)
    )
    asset_points_before = _asset_points_state(
        ledger.assetDepositPoints(vault_id, ripe_token)
    )
    ripe_available_before = ledger.ripeAvailForHr()
    total_supply_before = ripe_token.totalSupply()

    boa.env.time_travel(blocks=10)
    human_resources.refundAfterCancelPaycheck(
        REFUND_AMOUNT,
        False,
        sender=contributor,
    )

    assert ledger.ripeAvailForHr() == ripe_available_before + REFUND_AMOUNT
    assert ripe_gov_vault.userBalances(contributor, ripe_token) == raw_shares_before
    assert (
        ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
        == position_assets_before
    )
    assert _user_points_state(
        ledger.userDepositPoints(contributor, vault_id, ripe_token)
    ) == user_points_before
    assert _asset_points_state(
        ledger.assetDepositPoints(vault_id, ripe_token)
    ) == asset_points_before
    assert ripe_token.totalSupply() == total_supply_before


def test_paused_lootbox_rolls_back_cancel_and_burn(
    hr_position_factory,
    human_resources,
    ripe_gov_vault,
    ripe_token,
    ledger,
    lootbox,
    switchboard_alpha,
):
    contributor, vault_id = hr_position_factory()
    boa.env.time_travel(blocks=10)

    ripe_available_before = ledger.ripeAvailForHr()
    raw_shares_before = ripe_gov_vault.userBalances(contributor, ripe_token)
    position_assets_before = ripe_gov_vault.getTotalAmountForUser(
        contributor,
        ripe_token,
    )
    user_points_before = _user_points_state(
        ledger.userDepositPoints(contributor, vault_id, ripe_token)
    )
    asset_points_before = _asset_points_state(
        ledger.assetDepositPoints(vault_id, ripe_token)
    )
    hr_ripe_balance_before = ripe_token.balanceOf(human_resources)
    total_supply_before = ripe_token.totalSupply()

    lootbox.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        human_resources.refundAfterCancelPaycheck(
            REFUND_AMOUNT,
            True,
            sender=contributor,
        )

    assert ledger.ripeAvailForHr() == ripe_available_before
    assert ripe_gov_vault.userBalances(contributor, ripe_token) == raw_shares_before
    assert (
        ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
        == position_assets_before
    )
    assert _user_points_state(
        ledger.userDepositPoints(contributor, vault_id, ripe_token)
    ) == user_points_before
    assert _asset_points_state(
        ledger.assetDepositPoints(vault_id, ripe_token)
    ) == asset_points_before
    assert ripe_token.balanceOf(human_resources) == hr_ripe_balance_before
    assert ripe_token.totalSupply() == total_supply_before

    lootbox.pause(False, sender=switchboard_alpha.address)
    human_resources.refundAfterCancelPaycheck(
        REFUND_AMOUNT,
        True,
        sender=contributor,
    )

    assert ledger.ripeAvailForHr() == ripe_available_before + REFUND_AMOUNT
    assert ripe_gov_vault.userBalances(contributor, ripe_token) == 0
    user_points_after = ledger.userDepositPoints(
        contributor,
        vault_id,
        ripe_token,
    )
    assert user_points_after.lastBalance == 0
    assert user_points_after.lastUpdate > user_points_before[2]
    assert ledger.assetDepositPoints(vault_id, ripe_token).lastBalance == 0
    assert ripe_token.balanceOf(human_resources) == hr_ripe_balance_before
    assert total_supply_before - ripe_token.totalSupply() == position_assets_before


def test_zero_position_cancel_and_burn_still_requires_unpaused_lootbox(
    hr_position_factory,
    human_resources,
    ripe_gov_vault,
    ripe_token,
    ledger,
    lootbox,
    switchboard_alpha,
):
    contributor, vault_id = hr_position_factory(_with_position=False)
    ripe_available_before = ledger.ripeAvailForHr()
    user_points_before = _user_points_state(
        ledger.userDepositPoints(contributor, vault_id, ripe_token)
    )
    asset_points_before = _asset_points_state(
        ledger.assetDepositPoints(vault_id, ripe_token)
    )
    hr_ripe_balance_before = ripe_token.balanceOf(human_resources)
    total_supply_before = ripe_token.totalSupply()

    assert ripe_gov_vault.userBalances(contributor, ripe_token) == 0
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == 0

    lootbox.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        human_resources.refundAfterCancelPaycheck(
            REFUND_AMOUNT,
            True,
            sender=contributor,
        )

    assert ledger.ripeAvailForHr() == ripe_available_before
    assert _user_points_state(
        ledger.userDepositPoints(contributor, vault_id, ripe_token)
    ) == user_points_before
    assert _asset_points_state(
        ledger.assetDepositPoints(vault_id, ripe_token)
    ) == asset_points_before
    assert ripe_token.balanceOf(human_resources) == hr_ripe_balance_before
    assert ripe_token.totalSupply() == total_supply_before

    lootbox.pause(False, sender=switchboard_alpha.address)
    human_resources.refundAfterCancelPaycheck(
        REFUND_AMOUNT,
        True,
        sender=contributor,
    )

    assert ledger.ripeAvailForHr() == ripe_available_before + REFUND_AMOUNT
    user_points_after = ledger.userDepositPoints(
        contributor,
        vault_id,
        ripe_token,
    )
    assert user_points_after.lastBalance == 0
    assert user_points_after.lastUpdate > user_points_before[2]
    assert ledger.assetDepositPoints(vault_id, ripe_token).lastBalance == 0
    assert ripe_token.balanceOf(human_resources) == hr_ripe_balance_before
    assert ripe_token.totalSupply() == total_supply_before
