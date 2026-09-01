import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS
from conf_utils import assert_reverted_call, filter_logs


TELLER_ID = 17


def _alternate_teller(name):
    return boa.loads(
        """
# pragma version ~=0.4.3

@external
def marker():
    pass
""",
        name=name,
    )


def _replace_teller_pointer(ripe_hq, governance, replacement):
    ripe_hq.startAddressUpdateToRegistry(
        TELLER_ID,
        replacement,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock())
    assert ripe_hq.confirmAddressUpdateToRegistry(
        TELLER_ID,
        sender=governance.address,
    )
    assert ripe_hq.getAddr(TELLER_ID) == replacement.address


def _disable_teller_pointer(ripe_hq, governance):
    ripe_hq.startAddressDisableInRegistry(TELLER_ID, sender=governance.address)
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock())
    assert ripe_hq.confirmAddressDisableInRegistry(
        TELLER_ID,
        sender=governance.address,
    )
    assert ripe_hq.getAddr(TELLER_ID) == ZERO_ADDRESS


def _seed_claimable_deposit_loot(
    user,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    asset,
    whale,
):
    setGeneralConfig()
    setAssetConfig(asset)
    setRipeRewardsConfig()
    performDeposit(user, 100 * EIGHTEEN_DECIMALS, asset, whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(
        user,
        vault_id,
        simple_erc20_vault,
        asset,
        sender=teller.address,
    )
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(
        user,
        vault_id,
        simple_erc20_vault,
        asset,
        sender=teller.address,
    )
    return vault_id


def _create_dust_ticket_position(
    user,
    asset,
    whale,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    teller,
    should_exit,
):
    amount = 100 * EIGHTEEN_DECIMALS
    performDeposit(user, amount, asset, whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    if should_exit:
        teller.withdraw(asset, amount, user, simple_erc20_vault, sender=user)
    return vault_id


def _seed_exact_dust_ticket(
    ledger,
    lootbox,
    user,
    vault_id,
    asset,
    staker_rewards=0,
    voter_rewards=0,
    gen_rewards=0,
    staker_points=0,
    voter_points=0,
    gen_points=0,
    user_balance_points=1,
    asset_balance_points=100,
    staker_global_points=None,
    voter_global_points=None,
    gen_global_points=None,
):
    block_number = boa.env.evm.patch.block_number
    if staker_global_points is None:
        staker_global_points = 100 if staker_points else 0
    if voter_global_points is None:
        voter_global_points = 100 if voter_points else 0
    if gen_global_points is None:
        gen_global_points = 100 if gen_points else 0
    ledger.setDepositPointsAndRipeRewards(
        user,
        vault_id,
        asset,
        (user_balance_points, 0, block_number),
        (
            asset_balance_points,
            0,
            0,
            staker_points,
            voter_points,
            gen_points,
            block_number,
            1,
        ),
        (
            0,
            staker_global_points,
            voter_global_points,
            gen_global_points,
            block_number,
        ),
        (0, staker_rewards, voter_rewards, gen_rewards, 0, block_number),
        sender=lootbox.address,
    )


CATEGORY_FIELDS = {
    "staker": ("stakers", "ripeStakerPoints", "staker_rewards", "staker_points"),
    "voter": ("voters", "ripeVotePoints", "voter_rewards", "voter_points"),
    "gen": ("genDepositors", "ripeGenPoints", "gen_rewards", "gen_points"),
}


def _category_asset_config(category):
    return {
        "_stakersPointsAlloc": 1 if category == "staker" else 0,
        "_voterPointsAlloc": 1 if category == "voter" else 0,
    }


def _category_rewards_config(category, ripe_per_block):
    return {
        "_arePointsEnabled": False,
        "_ripePerBlock": ripe_per_block,
        "_borrowersAlloc": 0,
        "_stakersAlloc": 100_00 if category == "staker" else 0,
        "_votersAlloc": 100_00 if category == "voter" else 0,
        "_genDepositorsAlloc": 100_00 if category == "gen" else 0,
    }


def _category_seed(category, rewards, points=1, **overrides):
    rewards_field, points_field = CATEGORY_FIELDS[category][2:]
    return {
        rewards_field: rewards,
        points_field: points,
        **overrides,
    }


def _category_value(value, category, field_type):
    field_index = 0 if field_type == "rewards" else 1
    return getattr(value, CATEGORY_FIELDS[category][field_index])


def _legacy_specific_loot_reference(
    user_share,
    asset_points,
    global_points,
    rewards,
):
    if asset_points == 0 or global_points == 0 or user_share == 0:
        return asset_points, global_points, rewards, 0
    if rewards == 0:
        return asset_points, global_points, 0, 0
    capped_asset_points = min(asset_points, global_points)
    asset_rewards = rewards * capped_asset_points // global_points
    user_rewards = asset_rewards * user_share // 100_00
    if user_rewards == 0:
        return capped_asset_points, global_points, rewards, 0
    points_to_reduce = capped_asset_points * user_share // 100_00
    return (
        capped_asset_points - points_to_reduce,
        global_points - points_to_reduce,
        rewards - user_rewards,
        user_rewards,
    )


def test_exited_funded_dust_gets_one_wei_and_inactive_category_exhausts(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=1, _voterPointsAlloc=1)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=0,
        _borrowersAlloc=0,
        _stakersAlloc=100_00,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        True,
    )
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        staker_rewards=1,
        staker_points=1,
        voter_points=1,
    )

    assert not simple_erc20_vault.doesUserHaveBalance(bob, alpha_token)
    assert lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token) == 1
    claimed = teller.claimLoot(bob, False, sender=bob)

    assert claimed == 1
    assert ripe_token.balanceOf(bob) == 1
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).ripeStakerPoints == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).ripeVotePoints == 0
    assert not simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
    assert not ledger.isParticipatingInVault(bob, vault_id)


def test_live_funded_dust_defers_without_repeated_one_wei_minimum(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=1)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=0,
        _borrowersAlloc=0,
        _stakersAlloc=100_00,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        False,
    )
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        staker_rewards=1,
        staker_points=1,
    )

    assert simple_erc20_vault.doesUserHaveBalance(bob, alpha_token)
    assert lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token) == 0
    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert ripe_token.balanceOf(bob) == 0
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 1
    assert ledger.getRipeRewardsBundle().ripeRewards.stakers == 1
    assert simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)


def test_live_inactive_categories_do_not_block_funded_category(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=1, _voterPointsAlloc=1)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=0,
        _borrowersAlloc=0,
        _stakersAlloc=100_00,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        False,
    )
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        staker_rewards=10_000,
        staker_points=1,
        voter_points=1,
        gen_points=1,
    )

    assert lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token) == 1
    assert teller.claimLoot(bob, False, sender=bob) == 1
    assert ripe_token.balanceOf(bob) == 1
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).ripeStakerPoints == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).ripeVotePoints == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).ripeGenPoints == 0
    assert simple_erc20_vault.doesUserHaveBalance(bob, alpha_token)
    assert simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
    assert ledger.isParticipatingInVault(bob, vault_id)


def test_live_active_empty_category_blocks_funded_category_atomically(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    switchboard_alpha,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=1, _voterPointsAlloc=1)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=1,
        _borrowersAlloc=0,
        _stakersAlloc=50_00,
        _votersAlloc=50_00,
        _genDepositorsAlloc=0,
    )
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        False,
    )
    ledger.setRipeAvailForRewards(10, sender=switchboard_alpha.address)
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        staker_rewards=10_000,
        staker_points=1,
        voter_points=1,
    )
    assert lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token) == 0
    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert ripe_token.balanceOf(bob) == 0
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 1
    assert ledger.assetDepositPoints(vault_id, alpha_token).ripeStakerPoints == 1
    assert ledger.assetDepositPoints(vault_id, alpha_token).ripeVotePoints == 1
    assert ledger.getRipeRewardsBundle().ripeRewards.stakers == 10_000


def test_exited_empty_active_category_defers_until_reward_flows(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    switchboard_alpha,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=1)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=1,
        _borrowersAlloc=0,
        _stakersAlloc=100_00,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        True,
    )
    ledger.setRipeAvailForRewards(10, sender=switchboard_alpha.address)
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        staker_points=1,
    )
    # Same-block zero rewards are not terminal: the configured category can receive RIPE next block.
    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 1
    assert simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)

    boa.env.time_travel(blocks=1)
    assert teller.claimLoot(bob, False, sender=bob) == 1
    assert ripe_token.balanceOf(bob) == 1
    assert ledger.ripeAvailForRewards() == 9
    assert not simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
    assert not ledger.isParticipatingInVault(bob, vault_id)


def test_exited_empty_inactive_category_exhausts_without_mint(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=1)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=0,
        _borrowersAlloc=0,
        _stakersAlloc=100_00,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        True,
    )
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        staker_points=1,
    )

    supply_before = ripe_token.totalSupply()
    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert ripe_token.totalSupply() == supply_before
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).ripeStakerPoints == 0
    assert not simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
    assert not ledger.isParticipatingInVault(bob, vault_id)


@pytest.mark.parametrize("category", ("staker", "voter", "gen"))
@pytest.mark.parametrize(
    (
        "scenario",
        "should_exit",
        "rewards",
        "can_refill",
        "expected_claim",
        "expected_ticket",
        "expected_category_points",
        "expected_global_points",
        "expected_rewards",
        "expected_registered",
    ),
    (
        ("live-funded-dust", False, 1, False, 0, 1, 1, 100, 1, True),
        ("exited-funded-dust", True, 1, False, 1, 0, 0, 99, 0, False),
        ("live-empty-refill", False, 0, True, 0, 1, 1, 100, 0, True),
        ("exited-empty-refill", True, 0, True, 0, 1, 1, 100, 0, True),
        ("live-empty-inactive", False, 0, False, 0, 0, 0, 99, 0, True),
        ("exited-empty-inactive", True, 0, False, 0, 0, 0, 99, 0, False),
        ("live-positive-payout", False, 10_000, False, 1, 0, 0, 99, 9_999, True),
    ),
)
def test_deposit_loot_terminal_matrix_is_identical_for_every_category(
    category,
    scenario,
    should_exit,
    rewards,
    can_refill,
    expected_claim,
    expected_ticket,
    expected_category_points,
    expected_global_points,
    expected_rewards,
    expected_registered,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    switchboard_alpha,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, **_category_asset_config(category))
    setRipeRewardsConfig(
        **_category_rewards_config(category, 1 if can_refill else 0)
    )
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        should_exit,
    )
    if can_refill:
        ledger.setRipeAvailForRewards(10, sender=switchboard_alpha.address)
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        **_category_seed(category, rewards),
    )

    supply_before = ripe_token.totalSupply()
    assert (
        lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token)
        == expected_claim
    )
    assert teller.claimLoot(bob, False, sender=bob) == expected_claim
    assert ripe_token.balanceOf(bob) == expected_claim
    assert ripe_token.totalSupply() == supply_before + expected_claim

    user_points = ledger.userDepositPoints(bob, vault_id, alpha_token)
    asset_points = ledger.assetDepositPoints(vault_id, alpha_token)
    global_points = ledger.globalDepositPoints()
    reward_state = ledger.getRipeRewardsBundle().ripeRewards
    assert user_points.balancePoints == expected_ticket, scenario
    assert (
        _category_value(asset_points, category, "points")
        == expected_category_points
    ), scenario
    assert (
        _category_value(global_points, category, "points")
        == expected_global_points
    ), scenario
    assert _category_value(reward_state, category, "rewards") == expected_rewards
    assert (
        simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
        is expected_registered
    )
    assert ledger.isParticipatingInVault(bob, vault_id) is expected_registered


@pytest.mark.parametrize("category", ("staker", "voter", "gen"))
@pytest.mark.parametrize("terminal_gate", ("zero-budget", "zero-allocation"))
@pytest.mark.parametrize("should_exit", (False, True))
def test_empty_category_terminal_detection_covers_every_reward_flow_gate(
    category,
    terminal_gate,
    should_exit,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    switchboard_alpha,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, **_category_asset_config(category))
    allocations = {"staker": 0, "voter": 0, "gen": 0}
    if terminal_gate == "zero-budget":
        allocations[category] = 100_00
        rewards_budget = 0
    else:
        fallback_category = "voter" if category == "staker" else "staker"
        allocations[fallback_category] = 100_00
        rewards_budget = 10
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=1,
        _borrowersAlloc=0,
        _stakersAlloc=allocations["staker"],
        _votersAlloc=allocations["voter"],
        _genDepositorsAlloc=allocations["gen"],
    )
    ledger.setRipeAvailForRewards(
        rewards_budget,
        sender=switchboard_alpha.address,
    )
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        should_exit,
    )
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        **_category_seed(category, 0),
    )

    assert lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token) == 0
    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert ripe_token.balanceOf(bob) == 0
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 0
    asset_after = ledger.assetDepositPoints(vault_id, alpha_token)
    global_after = ledger.globalDepositPoints()
    assert _category_value(asset_after, category, "points") == 0
    assert _category_value(global_after, category, "points") == 99
    assert ledger.ripeAvailForRewards() == rewards_budget
    assert (
        simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
        is (not should_exit)
    )
    assert ledger.isParticipatingInVault(bob, vault_id) is (not should_exit)


@pytest.mark.parametrize("should_exit", (False, True))
def test_final_reward_wei_that_rounds_out_of_every_bucket_is_terminal(
    should_exit,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    switchboard_alpha,
    mission_control,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=1, _voterPointsAlloc=1)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=1,
        _borrowersAlloc=0,
        _stakersAlloc=50_00,
        _votersAlloc=50_00,
        _genDepositorsAlloc=0,
    )
    ledger.setRipeAvailForRewards(1, sender=switchboard_alpha.address)
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        should_exit,
    )
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        staker_points=1,
        voter_points=1,
    )
    mission_control.setRewardVaultId(
        alpha_token,
        0,
        sender=switchboard_alpha.address,
    )

    boa.env.time_travel(blocks=1)
    latest = lootbox.getLatestGlobalRipeRewards()
    assert latest.newRipeRewards == 1
    assert latest.stakers == 0
    assert latest.voters == 0
    assert lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token) == 0
    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert ripe_token.balanceOf(bob) == 0
    assert ledger.ripeAvailForRewards() == 0
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 0
    asset_after = ledger.assetDepositPoints(vault_id, alpha_token)
    assert asset_after.ripeStakerPoints == 0
    assert asset_after.ripeVotePoints == 0
    assert (
        simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
        is (not should_exit)
    )
    assert ledger.isParticipatingInVault(bob, vault_id) is (not should_exit)


def test_rounding_zero_allocation_defers_only_until_finite_budget_is_exhausted(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    switchboard_alpha,
    mission_control,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=1)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=1,
        _borrowersAlloc=0,
        _stakersAlloc=1,
        _votersAlloc=9_999,
        _genDepositorsAlloc=0,
    )
    ledger.setRipeAvailForRewards(2, sender=switchboard_alpha.address)
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        True,
    )
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        staker_points=1,
    )
    mission_control.setRewardVaultId(
        alpha_token,
        0,
        sender=switchboard_alpha.address,
    )

    boa.env.time_travel(blocks=1)
    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert ledger.ripeAvailForRewards() == 1
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 1
    assert ledger.assetDepositPoints(vault_id, alpha_token).ripeStakerPoints == 1
    assert simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)

    boa.env.time_travel(blocks=1)
    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert ripe_token.balanceOf(bob) == 0
    assert ledger.ripeAvailForRewards() == 0
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 0
    assert ledger.assetDepositPoints(vault_id, alpha_token).ripeStakerPoints == 0
    assert not simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
    assert not ledger.isParticipatingInVault(bob, vault_id)


@pytest.mark.parametrize(
    (
        "user_points",
        "total_points",
        "asset_category_points",
        "global_category_points",
        "rewards",
    ),
    (
        (1, 10_001, 10_001, 10_001, 10_001),
        (3_333, 10_000, 9_000, 27_000, 81_000),
        (9_999, 10_000, 5_000, 20_000, 40_000),
        (1, 2, 200, 100, 100),
        (1, 1_000_000, 1, 1, 1_000_000),
        (10_000, 10_000, 5_000, 5_000, 7),
    ),
)
def test_internal_claim_math_uses_exact_point_ratio_and_conserves_state(
    user_points,
    total_points,
    asset_category_points,
    global_category_points,
    rewards,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=1)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=0,
        _borrowersAlloc=0,
        _stakersAlloc=100_00,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        False,
    )
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        staker_rewards=rewards,
        staker_points=asset_category_points,
        user_balance_points=user_points,
        asset_balance_points=total_points,
        staker_global_points=global_category_points,
    )

    capped_asset_points = min(asset_category_points, global_category_points)
    asset_rewards = rewards * capped_asset_points // global_category_points
    expected_claim = asset_rewards * user_points // total_points
    expected_point_reduction = capped_asset_points * user_points // total_points
    if expected_point_reduction == 0:
        expected_point_reduction = 1
    expected_point_reduction = min(expected_point_reduction, capped_asset_points)
    expected_point_reduction = min(
        expected_point_reduction, global_category_points
    )
    assert expected_claim > 0

    claimable = lootbox.getClaimableDepositLootForAsset(
        bob, vault_id, alpha_token
    )
    assert claimable == expected_claim
    assert teller.claimLoot(bob, False, sender=bob) == expected_claim
    assert ripe_token.balanceOf(bob) == expected_claim

    user_after = ledger.userDepositPoints(bob, vault_id, alpha_token)
    asset_after = ledger.assetDepositPoints(vault_id, alpha_token)
    global_after = ledger.globalDepositPoints()
    rewards_after = ledger.getRipeRewardsBundle().ripeRewards
    assert user_after.balancePoints == 0
    assert asset_after.balancePoints == total_points - user_points
    assert asset_after.ripeStakerPoints == (
        capped_asset_points - expected_point_reduction
    )
    assert global_after.ripeStakerPoints == (
        global_category_points - expected_point_reduction
    )
    assert rewards_after.stakers == rewards - expected_claim


def test_public_calc_specific_loot_preserves_legacy_basis_point_semantics(
    lootbox,
):
    cases = (
        (0, 10, 100, 1_000),
        (1, 0, 100, 1_000),
        (1, 10, 0, 1_000),
        (1, 10, 100, 0),
        (1, 1, 1, 1),
        (1, 1, 1, 10_000),
        (9_999, 10_000, 10_000, 10_000),
        (10_000, 10_000, 10_000, 10_000),
        (3_333, 9_000, 27_000, 81_000),
        (5_000, 200, 100, 100),
        (5_000, 1, MAX_UINT256, 2),
        (10_000, MAX_UINT256 // 10_000, MAX_UINT256 // 10_000, 1),
    )
    for case in cases:
        assert lootbox.calcSpecificLoot(*case) == _legacy_specific_loot_reference(
            *case
        ), case
    with boa.reverts("safemul"):
        lootbox.calcSpecificLoot(
            10_000,
            MAX_UINT256,
            MAX_UINT256,
            1,
        )


def test_two_users_receive_the_same_exact_total_in_either_claim_order(
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=1)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=0,
        _borrowersAlloc=0,
        _stakersAlloc=100_00,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    performDeposit(
        bob,
        1 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    performDeposit(
        alice,
        1 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    for user, points in ((bob, 1), (alice, 9_999)):
        _seed_exact_dust_ticket(
            ledger,
            lootbox,
            user,
            vault_id,
            alpha_token,
            staker_rewards=10_000,
            staker_points=10_000,
            user_balance_points=points,
            asset_balance_points=10_000,
            staker_global_points=10_000,
        )

    for first, second in ((bob, alice), (alice, bob)):
        with boa.env.anchor():
            supply_before = ripe_token.totalSupply()
            first_expected = 1 if first == bob else 9_999
            second_expected = 1 if second == bob else 9_999
            assert lootbox.claimDepositLootForAsset(
                first,
                vault_id,
                alpha_token,
                sender=teller.address,
            ) == first_expected
            assert lootbox.claimDepositLootForAsset(
                second,
                vault_id,
                alpha_token,
                sender=teller.address,
            ) == second_expected
            assert ripe_token.balanceOf(bob) == 1
            assert ripe_token.balanceOf(alice) == 9_999
            assert ripe_token.totalSupply() == supply_before + 10_000
            assert ledger.getRipeRewardsBundle().ripeRewards.stakers == 0
            assert ledger.globalDepositPoints().ripeStakerPoints == 0
            asset_after = ledger.assetDepositPoints(vault_id, alpha_token)
            assert asset_after.balancePoints == 0
            assert asset_after.ripeStakerPoints == 0
            assert ledger.userDepositPoints(
                bob,
                vault_id,
                alpha_token,
            ).balancePoints == 0
            assert ledger.userDepositPoints(
                alice,
                vault_id,
                alpha_token,
            ).balancePoints == 0


@pytest.mark.parametrize(
    ("funded_category", "empty_category"),
    (
        ("staker", "voter"),
        ("staker", "gen"),
        ("voter", "staker"),
        ("voter", "gen"),
        ("gen", "staker"),
        ("gen", "voter"),
    ),
)
def test_any_active_empty_category_blocks_every_funded_category_atomically(
    funded_category,
    empty_category,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    switchboard_alpha,
):
    setGeneralConfig()
    setAssetConfig(
        alpha_token,
        _stakersPointsAlloc=int(
            "staker" in (funded_category, empty_category)
        ),
        _voterPointsAlloc=int("voter" in (funded_category, empty_category)),
    )
    allocations = {
        "staker": 0,
        "voter": 0,
        "gen": 0,
    }
    allocations[funded_category] = 50_00
    allocations[empty_category] = 50_00
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=2,
        _borrowersAlloc=0,
        _stakersAlloc=allocations["staker"],
        _votersAlloc=allocations["voter"],
        _genDepositorsAlloc=allocations["gen"],
    )
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        False,
    )
    ledger.setRipeAvailForRewards(10, sender=switchboard_alpha.address)
    seed = {
        "staker_rewards": 0,
        "voter_rewards": 0,
        "gen_rewards": 0,
        "staker_points": 0,
        "voter_points": 0,
        "gen_points": 0,
        "user_balance_points": 1,
        "asset_balance_points": 1,
        "staker_global_points": int(
            "staker" in (funded_category, empty_category)
        ),
        "voter_global_points": int(
            "voter" in (funded_category, empty_category)
        ),
        "gen_global_points": int(
            "gen" in (funded_category, empty_category)
        ),
    }
    seed[CATEGORY_FIELDS[funded_category][2]] = 10
    seed[CATEGORY_FIELDS[funded_category][3]] = 1
    seed[CATEGORY_FIELDS[empty_category][3]] = 1
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        **seed,
    )

    points_before = ledger.getDepositPointsBundle(bob, vault_id, alpha_token)
    rewards_before = ledger.getRipeRewardsBundle().ripeRewards
    assert lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token) == 0
    assert teller.claimLoot(bob, False, sender=bob) == 0
    points_after = ledger.getDepositPointsBundle(bob, vault_id, alpha_token)
    assert points_after.userPoints.balancePoints == points_before.userPoints.balancePoints
    for category in (funded_category, empty_category):
        assert _category_value(
            points_after.assetPoints, category, "points"
        ) == _category_value(points_before.assetPoints, category, "points")
        assert _category_value(
            points_after.globalPoints, category, "points"
        ) == _category_value(points_before.globalPoints, category, "points")
    assert ledger.getRipeRewardsBundle().ripeRewards == rewards_before
    assert ripe_token.balanceOf(bob) == 0

    boa.env.time_travel(blocks=1)
    assert lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token) == 12
    assert teller.claimLoot(bob, False, sender=bob) == 12
    assert ripe_token.balanceOf(bob) == 12
    asset_after = ledger.assetDepositPoints(vault_id, alpha_token)
    assert _category_value(asset_after, funded_category, "points") == 0
    assert _category_value(asset_after, empty_category, "points") == 0
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 0


def test_exited_three_category_dust_pays_one_wei_each_exactly_once(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=1, _voterPointsAlloc=1)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=0,
        _borrowersAlloc=0,
        _stakersAlloc=34_00,
        _votersAlloc=33_00,
        _genDepositorsAlloc=33_00,
    )
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        True,
    )
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        staker_rewards=1,
        voter_rewards=1,
        gen_rewards=1,
        staker_points=1,
        voter_points=1,
        gen_points=1,
    )

    assert lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token) == 3
    assert lootbox.claimDepositLootForAsset(
        bob,
        vault_id,
        alpha_token,
        sender=teller.address,
    ) == 3
    logs = filter_logs(lootbox, "DepositLootClaimed")
    assert len(logs) == 1
    assert logs[0].user == bob
    assert logs[0].vaultId == vault_id
    assert logs[0].asset == alpha_token.address
    assert logs[0].ripeStakerLoot == 1
    assert logs[0].ripeVoteLoot == 1
    assert logs[0].ripeGenLoot == 1
    assert ripe_token.balanceOf(bob) == 3
    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert ripe_token.balanceOf(bob) == 3
    assert not simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
    assert not ledger.isParticipatingInVault(bob, vault_id)


@pytest.mark.parametrize("should_exit", (False, True))
def test_no_category_entitlement_preserves_live_ticket_but_exhausts_exited_ticket(
    should_exit,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    alpha_token,
    alpha_token_whale,
):
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=0,
        _borrowersAlloc=0,
        _stakersAlloc=0,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        should_exit,
    )
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
    )

    assert teller.claimLoot(bob, False, sender=bob) == 0
    expected_ticket = 0 if should_exit else 1
    assert (
        ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints
        == expected_ticket
    )
    assert (
        simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
        is (not should_exit)
    )
    assert ledger.isParticipatingInVault(bob, vault_id) is (not should_exit)


def test_zero_asset_balance_points_fails_closed_without_deregistering_entitlement(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=1)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=0,
        _borrowersAlloc=0,
        _stakersAlloc=100_00,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        True,
    )
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        staker_rewards=100,
        staker_points=100,
        asset_balance_points=0,
        staker_global_points=100,
    )
    bundle_before = ledger.getDepositPointsBundle(bob, vault_id, alpha_token)
    rewards_before = ledger.getRipeRewardsBundle().ripeRewards
    supply_before = ripe_token.totalSupply()

    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert ledger.getDepositPointsBundle(bob, vault_id, alpha_token) == bundle_before
    assert ledger.getRipeRewardsBundle().ripeRewards == rewards_before
    assert ripe_token.totalSupply() == supply_before
    assert simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
    assert ledger.isParticipatingInVault(bob, vault_id)


def test_user_points_above_asset_total_caps_subtract_and_consumes_ticket(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=1)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=0,
        _borrowersAlloc=0,
        _stakersAlloc=100_00,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        False,
    )
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        staker_rewards=100,
        staker_points=50,
        user_balance_points=99,
        asset_balance_points=100,
        staker_global_points=100,
    )
    bundle_before = ledger.getDepositPointsBundle(bob, vault_id, alpha_token)
    rewards_before = ledger.getRipeRewardsBundle().ripeRewards
    user_points = list(bundle_before.userPoints)
    user_points[0] = bundle_before.assetPoints.balancePoints + 1
    ledger.setDepositPointsAndRipeRewards(
        bob,
        vault_id,
        alpha_token,
        user_points,
        bundle_before.assetPoints,
        bundle_before.globalPoints,
        rewards_before,
        sender=lootbox.address,
    )
    inconsistent = ledger.getDepositPointsBundle(bob, vault_id, alpha_token)
    assert inconsistent.userPoints.balancePoints == 101
    assert inconsistent.assetPoints == bundle_before.assetPoints
    assert inconsistent.globalPoints == bundle_before.globalPoints
    supply_before = ripe_token.totalSupply()

    claimed = lootbox.claimDepositLootForAsset(
        bob,
        vault_id,
        alpha_token,
        sender=teller.address,
    )
    assert claimed == 50
    settled = ledger.getDepositPointsBundle(bob, vault_id, alpha_token)
    assert settled.userPoints.balancePoints == 0
    assert settled.assetPoints.balancePoints == 0
    assert ripe_token.totalSupply() == supply_before + claimed


def test_one_blocked_asset_does_not_prevent_other_asset_settlement_or_cleanup(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    switchboard_alpha,
):
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=1)
    setAssetConfig(bravo_token, _stakersPointsAlloc=1, _voterPointsAlloc=1)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=1,
        _borrowersAlloc=0,
        _stakersAlloc=100_00,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        True,
    )
    assert (
        _create_dust_ticket_position(
            bob,
            bravo_token,
            bravo_token_whale,
            performDeposit,
            simple_erc20_vault,
            vault_book,
            teller,
            True,
        )
        == vault_id
    )
    ledger.setRipeAvailForRewards(10, sender=switchboard_alpha.address)
    common_globals = {
        "staker_global_points": 100,
        "voter_global_points": 100,
    }
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        alpha_token,
        staker_points=1,
        **common_globals,
    )
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        vault_id,
        bravo_token,
        voter_rewards=10_000,
        voter_points=1,
        **common_globals,
    )

    assert teller.claimLoot(bob, False, sender=bob) == 1
    assert ripe_token.balanceOf(bob) == 1
    assert simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
    assert not simple_erc20_vault.isUserInVaultAsset(bob, bravo_token)
    assert ledger.isParticipatingInVault(bob, vault_id)
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 1
    assert ledger.userDepositPoints(bob, vault_id, bravo_token).balancePoints == 0

    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=0,
        _borrowersAlloc=0,
        _stakersAlloc=100_00,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )
    assert teller.claimLoot(bob, False, sender=bob) == 0
    assert not simple_erc20_vault.isUserInVaultAsset(bob, alpha_token)
    assert not ledger.isParticipatingInVault(bob, vault_id)


def test_claim_deposit_loot_uses_current_teller_pointer(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_hq,
    governance,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    vault_id = _seed_claimable_deposit_loot(
        bob,
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        lootbox,
        teller,
        alpha_token,
        alpha_token_whale,
    )
    alternate = _alternate_teller("alternate_loot_claim_teller")
    _replace_teller_pointer(ripe_hq, governance, alternate)
    points_before = ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints
    claimable = lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token)
    assert points_before > 0
    assert claimable > 0

    with boa.reverts("no perms"):
        lootbox.claimDepositLootForAsset(
            bob,
            vault_id,
            alpha_token,
            sender=teller.address,
        )
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == points_before
    assert ripe_token.balanceOf(bob) == 0

    claimed = lootbox.claimDepositLootForAsset(
        bob,
        vault_id,
        alpha_token,
        sender=alternate.address,
    )
    assert claimed == claimable
    assert ripe_token.balanceOf(bob) == claimed
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 0


def test_claim_deposit_loot_reverts_atomically_when_teller_pointer_is_unset(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_hq,
    governance,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    vault_id = _seed_claimable_deposit_loot(
        bob,
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        lootbox,
        teller,
        alpha_token,
        alpha_token_whale,
    )
    points_before = ledger.userDepositPoints(bob, vault_id, alpha_token)
    global_before = ledger.globalDepositPoints()
    last_touch_before = ledger.lastTouch(bob)
    ripe_before = ripe_token.balanceOf(bob)
    _disable_teller_pointer(ripe_hq, governance)

    # The aggregate view does not depend on the Teller pointer and remains
    # readable even though the state-changing claim path is now unavailable.
    assert lootbox.getClaimableLoot(bob) > 0

    with boa.reverts("no perms"):
        lootbox.claimDepositLootForAsset(
            bob,
            vault_id,
            alpha_token,
            sender=teller.address,
        )
    assert ledger.userDepositPoints(bob, vault_id, alpha_token) == points_before
    assert ledger.globalDepositPoints() == global_before
    assert ledger.lastTouch(bob) == last_touch_before
    assert ripe_token.balanceOf(bob) == ripe_before


# Plan-substitution record: getClaimableLoot does not read the Teller pointer,
# so an unset Teller cannot make this view revert. The state-changing Teller-
# pointer failure is bound above. This replacement exercises the actual
# position-dependent pointer lookup in the view: the core RipeGov vault ID.
def test_get_claimable_loot_with_position_reverts_when_core_vault_pointer_is_unset(
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    mission_control,
    alpha_token,
    alpha_token_whale,
):
    _seed_claimable_deposit_loot(
        bob,
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        lootbox,
        teller,
        alpha_token,
        alpha_token_whale,
    )
    # There is no public zeroing transition for this pointer. The direct state
    # setup isolates Lootbox's defensive read-time guard without pretending it
    # is a reachable governance transition.
    mission_control.eval("self.coreRipeGovVaultId = 0")

    assert lootbox.getClaimableLoot(alice) == 0
    with boa.reverts("invalid vault id"):
        lootbox.getClaimableLoot(bob)


def test_get_claimable_loot_from_alternate_pointer_matches_claimed_amount(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_hq,
    governance,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    vault_id = _seed_claimable_deposit_loot(
        bob,
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        lootbox,
        teller,
        alpha_token,
        alpha_token_whale,
    )
    alternate = _alternate_teller("alternate_loot_view_teller")
    _replace_teller_pointer(ripe_hq, governance, alternate)
    viewed = lootbox.getClaimableLoot(bob)
    assert viewed > 0

    claimed = lootbox.claimDepositLootForAsset(
        bob,
        vault_id,
        alpha_token,
        sender=alternate.address,
    )
    assert claimed == viewed
    assert ripe_token.balanceOf(bob) == viewed
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 0


def test_loot_claim_basic(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig()

    # Setup deposit points
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # update deposit points
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # user points
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints != 0

    claimable = lootbox.getClaimableLoot(bob)
    assert claimable != 0

    asset_claimable = lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token)
    assert asset_claimable != 0

    # claim loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe != 0

    assert ripe_token.balanceOf(bob) == total_ripe

    # verify points are reset
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == 0
    
    # verify claimable amount is now zero
    claimable = lootbox.getClaimableLoot(bob)
    assert claimable == 0


def test_accrued_loot_buckets_remain_claimable_when_stored_points_flag_is_false(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig(True)
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)

    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(
        bob,
        vault_id,
        simple_erc20_vault,
        alpha_token,
        sender=teller.address,
    )
    stored_points = ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints
    claimable_before_disable = lootbox.getClaimableLoot(bob)
    assert stored_points > 0
    assert claimable_before_disable > 0

    setRipeRewardsConfig(False)
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == stored_points
    claimed = teller.claimLoot(bob, False, sender=bob)
    assert claimed == claimable_before_disable
    assert ripe_token.balanceOf(bob) == claimed



def test_loot_claim_multiple_users(
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    setUserDelegation,
    sally,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig()

    setUserDelegation(bob, sally)
    setUserDelegation(alice, sally)

    # Setup deposit points for both users
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(alice, 50 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # update deposit points for both users
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateDepositPoints(alice, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # claim loot for both users
    total_ripe = teller.claimLootForManyUsers([bob, alice], False, sender=sally)
    assert total_ripe != 0

    # verify both users received their share
    bob_ripe = ripe_token.balanceOf(bob)
    alice_ripe = ripe_token.balanceOf(alice)
    assert bob_ripe + alice_ripe == total_ripe
    assert bob_ripe > alice_ripe  # Bob deposited more, should get more rewards


def test_loot_claim_specific_asset(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig()

    # Setup deposit points
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # update deposit points
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # claim loot for specific asset
    total_ripe = lootbox.claimDepositLootForAsset(bob, vault_id, alpha_token, sender=teller.address)
    assert total_ripe != 0

    assert ripe_token.balanceOf(bob) == total_ripe

    # verify points are reset for this asset
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == 0


def test_stored_points_flag_false_does_not_disable_deposit_points(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    alpha_token,
    alpha_token_whale,
):
    # The legacy field remains stored, but Clock ignores it.
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig(_arePointsEnabled=False)

    # Setup deposit points
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # update deposit points
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Points continue to accumulate.
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints > 0

    # The accrued points remain claimable.
    claimable = lootbox.getClaimableLoot(bob)
    assert claimable > 0

    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe == claimable


def test_loot_claim_different_allocations(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    # basic setup with different reward allocations
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=80, _voterPointsAlloc=20)
    setRipeRewardsConfig(
        _borrowersAlloc=20,
        _stakersAlloc=40,
        _votersAlloc=20,
        _genDepositorsAlloc=20,
    )

    # Setup deposit points
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # update deposit points
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # claim loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe != 0

    assert ripe_token.balanceOf(bob) == total_ripe

    # verify points are reset
    up = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert up.balancePoints == 0


def test_loot_claim_borrow_basic(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up user debt
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Check claimable amount
    claimable = lootbox.getClaimableBorrowLoot(bob)
    assert claimable != 0

    # Claim borrow loot
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe == claimable
    assert ripe_token.balanceOf(bob) == total_ripe

    # Verify points are reset
    up = ledger.userBorrowPoints(bob)
    assert up.points == 0


def test_loot_claim_borrow_multiple_users(
    bob,
    alice,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up user debts
    debt_terms = createDebtTerms()
    bob_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    alice_debt = (200 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, bob_debt, 0, (0, 0), sender=credit_engine.address)
    ledger.setUserDebt(alice, alice_debt, 0, (0, 0), sender=credit_engine.address)

    # First update for both users
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    lootbox.updateBorrowPoints(alice, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update both users again
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    lootbox.updateBorrowPoints(alice, sender=teller.address)

    # Claim borrow loot for both users
    bob_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    alice_ripe = lootbox.claimBorrowLoot(alice, sender=teller.address)

    # Verify rewards are proportional to debt
    assert bob_ripe > 0
    assert alice_ripe > 0
    assert alice_ripe > bob_ripe  # Alice has more debt, should get more rewards

    # Verify points are reset for both users
    up_bob = ledger.userBorrowPoints(bob)
    up_alice = ledger.userBorrowPoints(alice)
    assert up_bob.points == 0
    assert up_alice.points == 0


def test_stored_points_flag_false_does_not_disable_borrow_points(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
):
    # The legacy field remains stored, but Clock ignores it.
    setGeneralConfig()
    setRipeRewardsConfig(False)

    # set up user debt
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Borrow points and rewards continue to accrue.
    claimable = lootbox.getClaimableBorrowLoot(bob)
    assert claimable > 0

    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe == claimable
    assert ripe_token.balanceOf(bob) == total_ripe


def test_loot_claim_borrow_debt_changes(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # Initial debt
    debt_terms = createDebtTerms()
    initial_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, initial_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed1 = 10
    boa.env.time_travel(blocks=elapsed1)

    # Increase debt
    increased_debt = (200 * EIGHTEEN_DECIMALS, 200 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, increased_debt, 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed2 = 10
    boa.env.time_travel(blocks=elapsed2)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Claim borrow loot
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe > 0
    assert ripe_token.balanceOf(bob) == total_ripe

    # Verify points are reset
    up = ledger.userBorrowPoints(bob)
    assert up.points == 0


def test_loot_claim_borrow_zero_debt(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up initial debt
    debt_terms = createDebtTerms()
    initial_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, initial_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed1 = 10
    boa.env.time_travel(blocks=elapsed1)

    # Set debt to zero
    zero_debt = (0, 0, debt_terms, 0, False)
    ledger.setUserDebt(bob, zero_debt, 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed2 = 10
    boa.env.time_travel(blocks=elapsed2)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Claim borrow loot
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe > 0  # Should still get rewards for period with debt
    assert ripe_token.balanceOf(bob) == total_ripe

    # Verify points are reset
    up = ledger.userBorrowPoints(bob)
    assert up.points == 0


def test_loot_claim_borrow_different_allocations(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
):
    # basic setup with different reward allocations
    setGeneralConfig()
    setRipeRewardsConfig(
        True,
        _borrowersAlloc=50,  # Higher allocation for borrowers
        _stakersAlloc=20,
        _votersAlloc=20,
        _genDepositorsAlloc=10,
    )

    # set up user debt
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Claim borrow loot
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe > 0
    assert ripe_token.balanceOf(bob) == total_ripe

    # Verify points are reset
    up = ledger.userBorrowPoints(bob)
    assert up.points == 0


def test_loot_claim_borrow_large_debt(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up very large debt
    debt_terms = createDebtTerms()
    large_debt = (1000000 * EIGHTEEN_DECIMALS, 1000000 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, large_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed = 1000
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Claim borrow loot
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe > 0
    assert ripe_token.balanceOf(bob) == total_ripe

    # Verify points are reset
    up = ledger.userBorrowPoints(bob)
    assert up.points == 0


def test_loot_claim_borrow_permission_checks(
    bob,
    alice,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    switchboard_alpha,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up user debt
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Test unauthorized caller
    with boa.reverts("no perms"):
        lootbox.claimBorrowLoot(bob, sender=alice)

    # Test paused state
    lootbox.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("contract paused"):
        lootbox.claimBorrowLoot(bob, sender=teller.address)

    # Unpause and verify it works
    lootbox.pause(False, sender=switchboard_alpha.address)
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe > 0


def test_loot_claim_borrow_rapid_claims(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up user debt
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # First claim
    first_claim = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert first_claim > 0
    assert ripe_token.balanceOf(bob) == first_claim

    # Try to claim again immediately
    second_claim = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert second_claim == 0  # No new rewards to claim
    assert ripe_token.balanceOf(bob) == first_claim  # Balance shouldn't change

    # Time travel and update points again
    boa.env.time_travel(blocks=20)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Third claim after new points
    third_claim = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert third_claim > 0  # Should have new rewards
    assert ripe_token.balanceOf(bob) == first_claim + third_claim


def test_loot_claim_borrow_event_emission(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up user debt
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Claim borrow loot and check event
    ripe_amount = lootbox.claimBorrowLoot(bob, sender=teller.address)
    log = filter_logs(lootbox, "BorrowLootClaimed")[0]
    assert log.user == bob
    assert log.ripeAmount == ripe_amount


def test_loot_claim_borrow_empty_address(
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    ripe_token,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # Try to claim for empty address
    total_ripe = lootbox.claimBorrowLoot(ZERO_ADDRESS, sender=teller.address)
    assert total_ripe == 0
    assert ripe_token.balanceOf(ZERO_ADDRESS) == 0

    # Verify no points accumulated
    up = ledger.userBorrowPoints(ZERO_ADDRESS)
    assert up.points == 0


def test_loot_claim_borrow_no_debt(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    ripe_token,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # First update with no debt
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Try to claim
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe == 0
    assert ripe_token.balanceOf(bob) == 0

    # Verify no points accumulated
    up = ledger.userBorrowPoints(bob)
    assert up.points == 0


def test_loot_claim_combined_deposit_and_borrow(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
    alpha_token,
    alpha_token_whale,
):
    # basic setup
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig(True)

    # Setup deposit points
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    
    # Setup borrow points
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # first update
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel to accumulate points
    boa.env.time_travel(blocks=20)

    # Update both deposit and borrow points
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Get claimable amounts
    deposit_claimable = lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token)
    borrow_claimable = lootbox.getClaimableBorrowLoot(bob)
    total_claimable = lootbox.getClaimableLoot(bob)

    assert deposit_claimable > 0
    assert borrow_claimable > 0
    assert total_claimable == deposit_claimable + borrow_claimable

    # Claim all loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe == total_claimable
    assert ripe_token.balanceOf(bob) == total_ripe

    # Verify points are reset
    up_deposit = ledger.userDepositPoints(bob, vault_id, alpha_token)
    up_borrow = ledger.userBorrowPoints(bob)
    assert up_deposit.balancePoints == 0
    assert up_borrow.points == 0


def test_loot_claim_borrow_integer_overflow_protection(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
):
    # basic setup
    setGeneralConfig()
    setRipeRewardsConfig(True)

    # set up extremely large debt
    debt_terms = createDebtTerms()
    max_debt = (MAX_UINT256, MAX_UINT256, debt_terms, 0, False)
    ledger.setUserDebt(bob, max_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed = 1000
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Claim borrow loot - should not overflow
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe > 0
    assert total_ripe < MAX_UINT256  # Should not overflow
    assert ripe_token.balanceOf(bob) == total_ripe

    # Verify points are reset
    up = ledger.userBorrowPoints(bob)
    assert up.points == 0


def test_loot_claim_borrow_zero_rewards(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
):
    # basic setup with zero rewards
    setGeneralConfig()
    setRipeRewardsConfig(
        True,
        _borrowersAlloc=0,  # No rewards for borrowers
        _stakersAlloc=100,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
    )

    # set up user debt
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)

    # First update
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Time travel
    elapsed = 20
    boa.env.time_travel(blocks=elapsed)

    # Update again
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    # Try to claim
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe == 0  # No rewards allocated to borrowers
    assert ripe_token.balanceOf(bob) == 0

    # Verify points are still tracked
    up = ledger.userBorrowPoints(bob)
    assert up.points > 0  # Points should still accumulate even with no rewards


# auto-staking ripe claims


def test_loot_claim_zero_share_autostake_reverts_atomically_and_remains_claimable(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_alpha,
    whale,
    cleanCoreRipeGovFixture,
):
    """AUD-024: a dust auto-stake reverts the complete Lootbox claim."""
    setGeneralConfig()
    setAssetConfig(alpha_token, _stakersPointsAlloc=1)
    setRipeRewardsConfig(
        _arePointsEnabled=False,
        _ripePerBlock=0,
        _borrowersAlloc=0,
        _stakersAlloc=100_00,
        _votersAlloc=0,
        _genDepositorsAlloc=0,
        _autoStakeRatio=100_00,
        _autoStakeDurationRatio=0,
    )
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        100_00,
        False,
        (100, 1000, 200_00, True, 5_00),
        sender=switchboard_alpha.address,
    )
    finite_limit = 10 ** 40
    setAssetConfig(
        ripe_token,
        _vaultIds=[2],
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
        _perUserDepositLimit=finite_limit,
        _globalDepositLimit=finite_limit,
    )
    core = cleanCoreRipeGovFixture()
    clean_vault = core["vault"]

    source_vault_id = _create_dust_ticket_position(
        bob,
        alpha_token,
        alpha_token_whale,
        performDeposit,
        simple_erc20_vault,
        vault_book,
        teller,
        True,
    )
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        source_vault_id,
        alpha_token,
        staker_rewards=1,
        staker_points=1,
    )
    assert lootbox.getClaimableDepositLootForAsset(
        bob, source_vault_id, alpha_token
    ) == 1

    donation = 10 ** 8
    ripe_token.transfer(clean_vault, donation, sender=whale)
    supply_before = ripe_token.totalSupply()
    lootbox_balance_before = ripe_token.balanceOf(lootbox)
    allowance_before = ripe_token.allowance(lootbox, teller)
    user_points_before = ledger.userDepositPoints(
        bob, source_vault_id, alpha_token
    )
    asset_points_before = ledger.assetDepositPoints(source_vault_id, alpha_token)
    global_points_before = ledger.globalDepositPoints()
    rewards_before = ledger.ripeRewards()
    shares_before = clean_vault.userBalances(bob, ripe_token)

    with pytest.raises(BoaError) as exc_info:
        teller.claimLoot(bob, False, sender=bob)
    assert_reverted_call(exc_info.value, "cannot receive 0 shares", teller)

    assert ripe_token.totalSupply() == supply_before
    assert ripe_token.balanceOf(lootbox) == lootbox_balance_before
    assert ripe_token.allowance(lootbox, teller) == allowance_before
    assert clean_vault.userBalances(bob, ripe_token) == shares_before
    assert ledger.userDepositPoints(
        bob, source_vault_id, alpha_token
    ) == user_points_before
    assert ledger.assetDepositPoints(source_vault_id, alpha_token) == asset_points_before
    assert ledger.globalDepositPoints() == global_points_before
    assert ledger.ripeRewards() == rewards_before
    assert lootbox.getClaimableDepositLootForAsset(
        bob, source_vault_id, alpha_token
    ) == 1

    # Increase the still-live entitlement to the adjacent one-share boundary.
    _seed_exact_dust_ticket(
        ledger,
        lootbox,
        bob,
        source_vault_id,
        alpha_token,
        staker_rewards=2,
        staker_points=1,
        asset_balance_points=1,
        staker_global_points=1,
    )
    assert teller.claimLoot(bob, False, sender=bob) == 2
    assert clean_vault.userBalances(bob, ripe_token) == 1
    assert lootbox.getClaimableDepositLootForAsset(
        bob, source_vault_id, alpha_token
    ) == 0


def test_loot_claim_no_auto_staking(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_alpha,
    ripe_gov_vault,
):
    """Test that with autoStakeRatio=0, all rewards go directly to user"""
    # Setup with no auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig(_autoStakeRatio=0, _autoStakeDurationRatio=0)
    
    # Configure RipeGov vault for ripe token
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        100_00,  # 100% asset weight
        False,
        (86400, 2592000, 200_00, True, 5_00),  # 1 day min, 30 days max, 200% boost, can exit, 5% fee
        sender=switchboard_alpha.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Accumulate rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Record balances before claim
    initial_wallet_balance = ripe_token.balanceOf(bob)
    initial_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Claim loot without staking
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe > 0

    # Verify all rewards went to wallet, none to vault
    final_wallet_balance = ripe_token.balanceOf(bob)
    final_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    
    assert final_wallet_balance == initial_wallet_balance + total_ripe
    assert final_vault_balance == initial_vault_balance  # No change in vault


def test_loot_claim_full_auto_staking(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_alpha,
    ripe_gov_vault,
    _test,
):
    """Test that with autoStakeRatio=100%, all rewards get staked"""
    # Setup with full auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=100_00, _autoStakeDurationRatio=50_00)  # 100% stake, 50% duration
    
    # Configure RipeGov vault for ripe token
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        100_00,  # 100% asset weight
        False,
        (86400, 2592000, 200_00, True, 5_00),  # 1 day min, 30 days max, 200% boost, can exit, 5% fee
        sender=switchboard_alpha.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Accumulate rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Record balances before claim
    initial_wallet_balance = ripe_token.balanceOf(bob)
    initial_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Claim loot without explicit staking (auto-staking should kick in)
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe > 0

    # Verify all rewards went to vault, none to wallet
    final_wallet_balance = ripe_token.balanceOf(bob)
    final_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    
    assert final_wallet_balance == initial_wallet_balance  # No change in wallet
    assert final_vault_balance > initial_vault_balance  # Increased vault balance
    _test(final_vault_balance, initial_vault_balance + total_ripe)

    # Verify the lock duration was calculated correctly
    # Expected: 50% of (30 days - 1 day) = 50% of 29 days = ~14.5 days = ~1,252,800 blocks
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    expected_duration_range = 2592000 - 86400  # max - min
    expected_lock_duration = expected_duration_range * 50_00 // 100_00  # 50% of range
    _test(expected_lock_duration, userData.unlock)
    

def test_loot_claim_partial_auto_staking(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_alpha,
    ripe_gov_vault,
    _test,
):
    """Test that with autoStakeRatio=60%, 60% gets staked and 40% sent to user"""
    # Setup with partial auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=60_00, _autoStakeDurationRatio=25_00)  # 60% stake, 25% duration
    
    # Configure RipeGov vault for ripe token
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        100_00,  # 100% asset weight
        False,
        (100, 1000, 100_00, False, 0),  # 100 min, 1000 max, 100% boost, cannot exit, 0% fee
        sender=switchboard_alpha.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Accumulate rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Record balances before claim
    initial_wallet_balance = ripe_token.balanceOf(bob)
    initial_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Claim loot without explicit staking
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe > 0

    # Verify correct split between wallet and vault
    final_wallet_balance = ripe_token.balanceOf(bob)
    final_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    
    expected_staked = total_ripe * 60_00 // 100_00  # 60% staked
    expected_to_wallet = total_ripe - expected_staked  # 40% to wallet
    
    actual_to_wallet = final_wallet_balance - initial_wallet_balance
    actual_vault_increase = final_vault_balance - initial_vault_balance
    
    # Use _test for approximate comparisons (allowing small rounding differences)
    _test(expected_to_wallet, actual_to_wallet)
    _test(expected_staked, actual_vault_increase)

    # Verify the lock duration was calculated correctly
    # Expected: 25% of (1000 - 100) = 25% of 900 = 225 blocks
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    expected_duration_range = 1000 - 100  # max - min
    expected_lock_duration = expected_duration_range * 25_00 // 100_00  # 25% of range
    
    # Calculate the actual lock duration by looking at what was set
    current_block = boa.env.evm.patch.block_number
    actual_lock_duration = userData.unlock - current_block
    
    # The lock duration should be exactly what we expect (225 blocks)
    assert actual_lock_duration == expected_lock_duration


def test_loot_claim_explicit_staking_overrides_auto(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_alpha,
    ripe_gov_vault,
):
    """Test that _shouldStake=True overrides autoStakeRatio and stakes everything"""
    # Setup with low auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token.address, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=20_00, _autoStakeDurationRatio=30_00)  # Only 20% auto-stake
    
    # Configure RipeGov vault for ripe token
    mission_control.setRipeGovVaultConfig(
        ripe_token.address,
        100_00,  # 100% asset weight
        False,
        (100, 1000, 100_00, False, 0),  # 100 min, 1000 max, 100% boost, cannot exit, 0% fee
        sender=switchboard_alpha.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Accumulate rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Record balances before claim
    initial_wallet_balance = ripe_token.balanceOf(bob)
    initial_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Claim loot WITH explicit staking - should override autoStakeRatio
    total_ripe = teller.claimLoot(bob, True, sender=bob)  # _shouldStake=True
    assert total_ripe > 0

    # Verify ALL rewards went to vault (despite low autoStakeRatio)
    final_wallet_balance = ripe_token.balanceOf(bob)
    final_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    
    assert final_wallet_balance == initial_wallet_balance  # No change in wallet
    assert final_vault_balance > initial_vault_balance  # All rewards went to vault


def test_loot_claim_zero_lock_duration_range(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_alpha,
    ripe_gov_vault,
):
    """Test that when min=max lock duration, vault still enforces minimum lock duration"""
    # Setup with auto-staking but zero duration range
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token.address, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=100_00, _autoStakeDurationRatio=50_00)
    
    # Configure RipeGov vault with same min/max lock duration
    mission_control.setRipeGovVaultConfig(
        ripe_token.address,
        100_00,  # 100% asset weight
        False,
        (500, 500, 200_00, True, 5_00),  # min = max = 500 blocks
        sender=switchboard_alpha.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Accumulate rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Claim loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe > 0

    # Verify tokens were staked with minimum lock duration (vault enforces minimum)
    # When min=max, the vault still enforces the minimum lock duration for security
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    current_block = boa.env.evm.patch.block_number
    expected_unlock = current_block + 500  # Minimum lock duration of 500 blocks
    assert userData.unlock == expected_unlock


def test_loot_claim_max_lock_duration_ratio(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_alpha,
    ripe_gov_vault,
):
    """Test that autoStakeDurationRatio=100% uses the full lock duration range"""
    # Setup with auto-staking and max duration ratio
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token.address, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=100_00, _autoStakeDurationRatio=100_00)  # Max duration
    
    # Configure RipeGov vault
    mission_control.setRipeGovVaultConfig(
        ripe_token.address,
        100_00,  # 100% asset weight
        False,
        (200, 1000, 200_00, True, 5_00),  # 200 min, 1000 max
        sender=switchboard_alpha.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Accumulate rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Claim loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe > 0

    # Verify tokens were staked with maximum lock duration
    userData = ripe_gov_vault.userGovData(bob, ripe_token)
    expected_duration_range = 1000 - 200  # max - min = 800
    expected_lock_duration = expected_duration_range  # 100% of range
    
    current_block = boa.env.evm.patch.block_number
    expected_unlock = current_block + expected_lock_duration
    assert userData.unlock == expected_unlock


def test_loot_claim_zero_rewards_no_staking_calls(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    teller,
    ripe_token,
    alpha_token,
    mission_control,
    switchboard_alpha,
    ripe_gov_vault,
):
    """Test that zero rewards don't trigger any staking operations"""
    # Setup with auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token.address, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=100_00, _autoStakeDurationRatio=50_00)
    
    # Configure RipeGov vault
    mission_control.setRipeGovVaultConfig(
        ripe_token.address,
        100_00,  # 100% asset weight
        False,
        (100, 1000, 200_00, True, 5_00),
        sender=switchboard_alpha.address
    )

    # Don't setup any deposits or debt - no rewards to claim
    
    # Record balances before claim
    initial_wallet_balance = ripe_token.balanceOf(bob)
    initial_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    # Attempt to claim loot
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe == 0

    # Verify no changes occurred
    final_wallet_balance = ripe_token.balanceOf(bob)
    final_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    
    assert final_wallet_balance == initial_wallet_balance
    assert final_vault_balance == initial_vault_balance


def test_loot_claim_calculation_consistency_with_partial_auto_staking(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_alpha,
):
    """Test that getClaimableLoot() matches actual claimLoot() returns with partial auto-staking"""
    # Setup with partial auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token.address, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=50_00, _autoStakeDurationRatio=50_00)  # 50% stake, 50% send
    
    # Configure RipeGov vault
    mission_control.setRipeGovVaultConfig(
        ripe_token.address,
        100_00,  # 100% asset weight
        False,
        (100, 1000, 100_00, False, 0),
        sender=switchboard_alpha.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # Accumulate rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    # Get expected claimable amount
    claimable = lootbox.getClaimableLoot(bob)
    assert claimable > 0

    # Claim loot - should match the calculated claimable amount
    total_ripe = teller.claimLoot(bob, False, sender=bob)
    assert total_ripe == claimable

    # Verify the user received some tokens (50% should go to wallet with partial auto-staking)
    final_wallet_balance = ripe_token.balanceOf(bob)
    assert final_wallet_balance > 0  # Should have received 50% of claimed tokens


def test_loot_claim_multiple_claims_with_staking(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_alpha,
    ripe_gov_vault,
):
    """Test multiple claims with auto-staking to verify cumulative behavior"""
    # Setup with auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token.address, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=100_00, _autoStakeDurationRatio=50_00)
    
    # Configure RipeGov vault
    mission_control.setRipeGovVaultConfig(
        ripe_token.address,
        100_00,  # 100% asset weight
        False,
        (100, 1000, 200_00, True, 5_00),
        sender=switchboard_alpha.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # First claim cycle
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    
    first_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    first_claim = teller.claimLoot(bob, False, sender=bob)
    assert first_claim > 0
    
    after_first_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    assert after_first_vault_balance > first_vault_balance

    # Second claim cycle - accumulate more rewards
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    
    second_claim = teller.claimLoot(bob, False, sender=bob)
    assert second_claim > 0
    
    final_vault_balance = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
    assert final_vault_balance > after_first_vault_balance

    # Verify cumulative staking worked
    total_expected_staked = first_claim + second_claim
    total_actual_staked = final_vault_balance - first_vault_balance
    assert total_actual_staked == total_expected_staked

    # Verify wallet balance remained unchanged (all auto-staked)
    wallet_balance = ripe_token.balanceOf(bob)
    assert wallet_balance == 0


def test_loot_claim_auto_stake_configuration_updates(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_alpha,
    ripe_gov_vault,
):
    """Test that configuration changes affect subsequent claims correctly"""
    # Initial setup with no auto-staking
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token.address, _vaultIds=[2])  # Configure ripe token for vault 2
    setRipeRewardsConfig(_autoStakeRatio=0, _autoStakeDurationRatio=0)
    
    # Configure RipeGov vault
    mission_control.setRipeGovVaultConfig(
        ripe_token.address,
        100_00,  # 100% asset weight
        False,
        (100, 1000, 100_00, False, 0),
        sender=switchboard_alpha.address
    )

    # Setup deposit to earn rewards
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    
    # First claim with no auto-staking
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    
    first_claim = teller.claimLoot(bob, False, sender=bob)
    assert first_claim > 0
    assert ripe_token.balanceOf(bob) == first_claim  # All to wallet
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0  # None to vault

    # Update configuration to enable auto-staking
    setRipeRewardsConfig(_autoStakeRatio=100_00, _autoStakeDurationRatio=50_00)
    
    # Second claim with auto-staking enabled
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)
    
    second_claim = teller.claimLoot(bob, False, sender=bob)
    assert second_claim > 0
    assert ripe_token.balanceOf(bob) == first_claim  # Wallet unchanged from first claim
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) > 0  # Second claim went to vault


def test_lootbox_auto_stake_uses_core_governance_vault_pointer(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    mission_control,
    switchboard_alpha,
    ripe_gov_vault,
    alternate_ripe_gov_vault,
    registerVault,
):
    core_id = registerVault(alternate_ripe_gov_vault, "Core RipeGov")
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setAssetConfig(ripe_token, _vaultIds=[core_id])
    setRipeRewardsConfig(_autoStakeRatio=100_00, _autoStakeDurationRatio=50_00)
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        100_00,
        False,
        (100, 1_000, 100_00, False, 0),
        sender=switchboard_alpha.address,
    )
    mission_control.setCoreRipeGovVaultId(core_id, sender=switchboard_alpha.address)

    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    source_vault_id = vault_book.getRegId(simple_erc20_vault)
    boa.env.time_travel(blocks=20)
    lootbox.updateDepositPoints(
        bob,
        source_vault_id,
        simple_erc20_vault,
        alpha_token,
        sender=teller.address,
    )

    claimed = teller.claimLoot(bob, False, sender=bob)
    assert claimed > 0
    assert alternate_ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) > 0
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0


def test_lootbox_claim_routes_fail_closed_when_core_pointer_is_unset(
    mission_control,
    lootbox,
    bob,
    alpha_token,
):
    mission_control.eval("self.coreRipeGovVaultId = 0")

    assert lootbox.getClaimableLoot(bob) == 0
    with boa.reverts("invalid vault id"):
        lootbox.getClaimableDepositLootForAsset(bob, 3, alpha_token)


def test_lootbox_borrow_auto_stake_uses_core_governance_vault_pointer(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
    mission_control,
    switchboard_alpha,
    ripe_gov_vault,
    alternate_ripe_gov_vault,
    registerVault,
):
    core_id = registerVault(alternate_ripe_gov_vault, "Borrow Loot Core RipeGov")
    setGeneralConfig()
    setAssetConfig(ripe_token, _vaultIds=[core_id])
    setRipeRewardsConfig(
        True,
        _autoStakeRatio=100_00,
        _autoStakeDurationRatio=50_00,
    )
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        100_00,
        False,
        (100, 1_000, 100_00, False, 0),
        sender=switchboard_alpha.address,
    )
    mission_control.setCoreRipeGovVaultId(core_id, sender=switchboard_alpha.address)

    debt_terms = createDebtTerms()
    user_debt = (
        100 * EIGHTEEN_DECIMALS,
        100 * EIGHTEEN_DECIMALS,
        debt_terms,
        0,
        False,
    )
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    boa.env.time_travel(blocks=20)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    claimable = lootbox.getClaimableBorrowLoot(bob)
    assert claimable > 0
    assert lootbox.claimBorrowLoot(bob, sender=teller.address) == claimable
    assert (
        alternate_ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)
        == claimable
    )
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == 0
    assert ripe_token.balanceOf(bob) == 0


def test_lootbox_borrow_claim_unset_pointer_reverts_without_state_changes(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
    mission_control,
):
    setGeneralConfig()
    setRipeRewardsConfig(
        True,
        _autoStakeRatio=100_00,
        _autoStakeDurationRatio=50_00,
    )

    debt_terms = createDebtTerms()
    user_debt = (
        100 * EIGHTEEN_DECIMALS,
        100 * EIGHTEEN_DECIMALS,
        debt_terms,
        0,
        False,
    )
    ledger.setUserDebt(bob, user_debt, 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(bob, sender=teller.address)
    boa.env.time_travel(blocks=20)
    lootbox.updateBorrowPoints(bob, sender=teller.address)

    claimable_before = lootbox.getClaimableBorrowLoot(bob)
    user_points_before = ledger.userBorrowPoints(bob)
    global_points_before = ledger.globalBorrowPoints()
    rewards_available_before = ledger.ripeAvailForRewards()
    supply_before = ripe_token.totalSupply()
    user_balance_before = ripe_token.balanceOf(bob)
    allowance_before = ripe_token.allowance(lootbox, teller)
    assert claimable_before > 0

    mission_control.eval("self.coreRipeGovVaultId = 0")
    with boa.reverts("invalid vault id"):
        lootbox.claimBorrowLoot(bob, sender=teller.address)

    user_points_after = ledger.userBorrowPoints(bob)
    global_points_after = ledger.globalBorrowPoints()
    assert lootbox.getClaimableBorrowLoot(bob) == claimable_before
    assert (
        user_points_after.lastPrincipal,
        user_points_after.points,
        user_points_after.lastUpdate,
    ) == (
        user_points_before.lastPrincipal,
        user_points_before.points,
        user_points_before.lastUpdate,
    )
    assert (
        global_points_after.lastPrincipal,
        global_points_after.points,
        global_points_after.lastUpdate,
    ) == (
        global_points_before.lastPrincipal,
        global_points_before.points,
        global_points_before.lastUpdate,
    )
    assert ledger.ripeAvailForRewards() == rewards_available_before
    assert ripe_token.totalSupply() == supply_before
    assert ripe_token.balanceOf(bob) == user_balance_before
    assert ripe_token.allowance(lootbox, teller) == allowance_before
