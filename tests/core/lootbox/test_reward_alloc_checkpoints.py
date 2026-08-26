import boa
import pytest

from conf_utils import has_dev_reason
from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


DEBT_TERMS = (50_00, 60_00, 70_00, 10_00, 5_00, 0)
ALLOC_TOTAL = 100_00


def _rewards_tuple(cfg, **overrides):
    values = {
        "arePointsEnabled": cfg[0],
        "ripePerBlock": cfg[1],
        "borrowersAlloc": cfg[2],
        "stakersAlloc": cfg[3],
        "votersAlloc": cfg[4],
        "genDepositorsAlloc": cfg[5],
        "autoStakeRatio": cfg[6],
        "autoStakeDurationRatio": cfg[7],
        "stabPoolRipePerDollarClaimed": cfg[8],
    }
    values.update(overrides)
    return (
        values["arePointsEnabled"],
        values["ripePerBlock"],
        values["borrowersAlloc"],
        values["stakersAlloc"],
        values["votersAlloc"],
        values["genDepositorsAlloc"],
        values["autoStakeRatio"],
        values["autoStakeDurationRatio"],
        values["stabPoolRipePerDollarClaimed"],
    )


def _asset_tuple(vault_ids, stakers, voters):
    return (
        vault_ids,
        stakers,
        voters,
        MAX_UINT256,
        MAX_UINT256,
        0,
        DEBT_TERMS,
        False,
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        0,
        (False, 0, 0, 0, 0),
        ZERO_ADDRESS,
        False,
    )


def _write_asset(mission_control, switchboard_bravo, asset, vault_ids, stakers, voters):
    mission_control.setAssetConfig(
        asset,
        _asset_tuple(vault_ids, stakers, voters),
        sender=switchboard_bravo.address,
    )


def _write_rewards(mission_control, switchboard_alpha, **overrides):
    mission_control.setRipeRewardsConfig(
        _rewards_tuple(mission_control.rewardsConfig(), **overrides),
        sender=switchboard_alpha.address,
    )


def _bucket(amount, alloc):
    return amount * alloc // ALLOC_TOTAL


def _ripe_snapshot(ledger):
    rewards = ledger.ripeRewards()
    return {
        "borrowers": rewards.borrowers,
        "stakers": rewards.stakers,
        "voters": rewards.voters,
        "genDepositors": rewards.genDepositors,
        "lastUpdate": rewards.lastUpdate,
        "avail": ledger.ripeAvailForRewards(),
    }


def _assert_ripe_delta(ledger, before, elapsed, ripe_per_block, allocs):
    expected = elapsed * ripe_per_block
    after = ledger.ripeRewards()
    assert after.borrowers - before["borrowers"] == _bucket(expected, allocs[0])
    assert after.stakers - before["stakers"] == _bucket(expected, allocs[1])
    assert after.voters - before["voters"] == _bucket(expected, allocs[2])
    assert after.genDepositors - before["genDepositors"] == _bucket(expected, allocs[3])
    assert before["avail"] - ledger.ripeAvailForRewards() == expected
    assert after.lastUpdate == boa.env.evm.patch.block_number
    return expected


def _setup_points(
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mock_price_source,
    asset,
    vault_ids,
    stakers=0,
    voters=20,
    ripe_per_block=0,
):
    setGeneralConfig()
    setRipeRewardsConfig(
        True,
        ripe_per_block,
        25_00,
        25_00,
        25_00,
        25_00,
    )
    setAssetConfig(
        asset,
        _vaultIds=vault_ids,
        _stakersPointsAlloc=stakers,
        _voterPointsAlloc=voters,
    )
    mock_price_source.setPrice(asset, EIGHTEEN_DECIMALS)


def _init_row(
    performDeposit,
    lootbox,
    teller,
    user,
    amount,
    asset,
    whale,
    vault,
    vault_id,
):
    performDeposit(user, amount, asset, whale, vault)
    lootbox.updateDepositPoints(user, vault_id, vault, asset, sender=teller.address)


def test_old_alloc_applies_exactly_before_mutation_block(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    mission_control,
    switchboard_bravo,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _setup_points(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        mock_price_source,
        alpha_token,
        [vault_id],
        stakers=0,
        voters=20,
    )
    _init_row(
        performDeposit,
        lootbox,
        teller,
        bob,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        simple_erc20_vault,
        vault_id,
    )

    elapsed = 13
    boa.env.time_travel(blocks=elapsed)
    _write_asset(mission_control, switchboard_bravo, alpha_token, [vault_id], 10, 10)

    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.lastUpdate == boa.env.evm.patch.block_number
    assert ap.ripeVotePoints == 20 * elapsed
    assert ap.ripeStakerPoints == 0
    assert ap.lastUsdValue == 0

    later = 7
    boa.env.time_travel(blocks=later)
    lootbox.updateDepositPoints(
        ZERO_ADDRESS,
        vault_id,
        simple_erc20_vault,
        alpha_token,
        sender=teller.address,
    )
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.ripeVotePoints == 20 * elapsed + 10 * later
    assert ap.ripeStakerPoints == 10 * later


def test_bravo_pending_asset_alloc_uses_old_rate_through_execute(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    switchboard_bravo,
    governance,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _setup_points(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        mock_price_source,
        alpha_token,
        [vault_id],
        stakers=0,
        voters=20,
    )
    _init_row(
        performDeposit,
        lootbox,
        teller,
        bob,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        simple_erc20_vault,
        vault_id,
    )

    gap = 4
    boa.env.time_travel(blocks=gap)
    action_id = switchboard_bravo.setAssetDepositParams(
        alpha_token,
        [vault_id],
        0,
        8,
        2_000 * EIGHTEEN_DECIMALS,
        20_000 * EIGHTEEN_DECIMALS,
        0,
        sender=governance.address,
    )
    timelock = switchboard_bravo.actionTimeLock()
    boa.env.time_travel(blocks=timelock)
    assert switchboard_bravo.executePendingAction(action_id, sender=governance.address)

    settled = gap + timelock
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.lastUpdate == boa.env.evm.patch.block_number
    assert ap.ripeStakerPoints == 0
    assert ap.ripeVotePoints == 20 * settled

    later = 5
    boa.env.time_travel(blocks=later)
    lootbox.updateDepositPoints(
        ZERO_ADDRESS,
        vault_id,
        simple_erc20_vault,
        alpha_token,
        sender=teller.address,
    )
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.ripeStakerPoints == 0
    assert ap.ripeVotePoints == 20 * settled + 8 * later


def test_alpha_pending_ripe_per_block_and_bucket_allocs_are_exact(
    setRipeRewardsConfig,
    lootbox,
    teller,
    ledger,
    switchboard_alpha,
    governance,
    mission_control,
):
    ripe_per_block = 12
    allocs = (40_00, 20_00, 30_00, 10_00)
    setRipeRewardsConfig(True, ripe_per_block, *allocs)
    lootbox.updateRipeRewards(sender=teller.address)
    before = _ripe_snapshot(ledger)

    gap = 6
    boa.env.time_travel(blocks=gap)
    action_id = switchboard_alpha.setRipePerBlock(24, sender=governance.address)
    timelock = switchboard_alpha.actionTimeLock()
    boa.env.time_travel(blocks=timelock)
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    _assert_ripe_delta(ledger, before, gap + timelock, ripe_per_block, allocs)
    assert mission_control.rewardsConfig().ripePerBlock == 24

    after_block = _ripe_snapshot(ledger)
    later = 3
    boa.env.time_travel(blocks=later)
    alloc_action = switchboard_alpha.setRipeRewardsAllocs(
        10_00,
        20_00,
        30_00,
        40_00,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=timelock)
    assert switchboard_alpha.executePendingAction(alloc_action, sender=governance.address)
    _assert_ripe_delta(ledger, after_block, later + timelock, 24, allocs)
    cfg = mission_control.rewardsConfig()
    assert (cfg.borrowersAlloc, cfg.stakersAlloc, cfg.votersAlloc, cfg.genDepositorsAlloc) == (
        10_00,
        20_00,
        30_00,
        40_00,
    )

    after_allocs = _ripe_snapshot(ledger)
    tail = 2
    boa.env.time_travel(blocks=tail)
    lootbox.updateRipeRewards(sender=teller.address)
    _assert_ripe_delta(ledger, after_allocs, tail, 24, (10_00, 20_00, 30_00, 40_00))


def test_staker_zero_crossing_refreshes_last_usd_value_both_directions(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    mission_control,
    switchboard_bravo,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _setup_points(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        mock_price_source,
        alpha_token,
        [vault_id],
        stakers=0,
        voters=15,
    )
    deposit = 100 * EIGHTEEN_DECIMALS
    _init_row(
        performDeposit,
        lootbox,
        teller,
        bob,
        deposit,
        alpha_token,
        alpha_token_whale,
        simple_erc20_vault,
        vault_id,
    )
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 100
    global_usd = ledger.globalDepositPoints().lastUsdValue

    boa.env.time_travel(blocks=4)
    _write_asset(mission_control, switchboard_bravo, alpha_token, [vault_id], 12, 15)
    crossed_on = ledger.assetDepositPoints(vault_id, alpha_token)
    assert crossed_on.lastUsdValue == 0
    assert crossed_on.ripeVotePoints == 15 * 4
    assert crossed_on.ripeStakerPoints == 0
    assert ledger.globalDepositPoints().lastUsdValue == global_usd - 100

    boa.env.time_travel(blocks=5)
    _write_asset(mission_control, switchboard_bravo, alpha_token, [vault_id], 0, 15)
    crossed_off = ledger.assetDepositPoints(vault_id, alpha_token)
    assert crossed_off.lastUsdValue == 100
    assert crossed_off.ripeStakerPoints == 12 * 5
    assert crossed_off.ripeVotePoints == 15 * 4 + 15 * 5
    assert ledger.globalDepositPoints().lastUsdValue == global_usd


def test_voter_only_and_nonzero_to_nonzero_do_not_need_second_checkpoint(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    mission_control,
    switchboard_bravo,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _setup_points(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        mock_price_source,
        alpha_token,
        [vault_id],
        stakers=10,
        voters=10,
    )
    _init_row(
        performDeposit,
        lootbox,
        teller,
        bob,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        simple_erc20_vault,
        vault_id,
    )
    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUsdValue == 0

    boa.env.time_travel(blocks=6)
    _write_asset(mission_control, switchboard_bravo, alpha_token, [vault_id], 10, 25)
    voter_only = ledger.assetDepositPoints(vault_id, alpha_token)
    assert voter_only.lastUsdValue == 0
    assert voter_only.ripeStakerPoints == 10 * 6
    assert voter_only.ripeVotePoints == 10 * 6

    boa.env.time_travel(blocks=3)
    _write_asset(mission_control, switchboard_bravo, alpha_token, [vault_id], 18, 25)
    nonzero = ledger.assetDepositPoints(vault_id, alpha_token)
    assert nonzero.lastUsdValue == 0
    assert nonzero.ripeStakerPoints == 10 * 6 + 10 * 3
    assert nonzero.ripeVotePoints == 10 * 6 + 25 * 3


def test_removed_historical_vault_row_is_checkpointed_not_repriced(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    rebase_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    mission_control,
    switchboard_bravo,
):
    vault_a = vault_book.getRegId(simple_erc20_vault)
    vault_b = vault_book.getRegId(rebase_erc20_vault)
    _setup_points(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        mock_price_source,
        alpha_token,
        [vault_a],
        stakers=0,
        voters=20,
    )
    _init_row(
        performDeposit,
        lootbox,
        teller,
        bob,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        simple_erc20_vault,
        vault_a,
    )
    last_before_remove = ledger.assetDepositPoints(vault_a, alpha_token).lastUpdate

    boa.env.time_travel(blocks=5)
    _write_asset(mission_control, switchboard_bravo, alpha_token, [vault_b], 0, 20)
    removed = ledger.assetDepositPoints(vault_a, alpha_token)
    assert list(mission_control.assetConfig(alpha_token).vaultIds) == [vault_b]
    assert removed.lastUpdate == last_before_remove
    assert removed.ripeVotePoints == 0

    boa.env.time_travel(blocks=9)
    _write_asset(mission_control, switchboard_bravo, alpha_token, [vault_b], 10, 8)
    historical = ledger.assetDepositPoints(vault_a, alpha_token)
    assert historical.lastUpdate == boa.env.evm.patch.block_number
    assert historical.ripeVotePoints == 20 * 14
    assert historical.ripeStakerPoints == 0
    assert historical.lastUsdValue == 0
    assert ledger.assetDepositPoints(vault_b, alpha_token).lastUpdate == 0

    later = 4
    boa.env.time_travel(blocks=later)
    lootbox.updateDepositPoints(
        ZERO_ADDRESS,
        vault_a,
        simple_erc20_vault,
        alpha_token,
        sender=teller.address,
    )
    after = ledger.assetDepositPoints(vault_a, alpha_token)
    assert after.ripeVotePoints == 20 * 14 + 8 * later
    assert after.ripeStakerPoints == 10 * later


def test_empty_row_allocation_change_checkpoints_global_only(
    charlie_token,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    mission_control,
    switchboard_bravo,
    simple_erc20_vault,
    vault_book,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    setGeneralConfig()
    setRipeRewardsConfig(True, 10, 25_00, 25_00, 25_00, 25_00)
    lootbox.updateRipeRewards(sender=teller.address)
    before = _ripe_snapshot(ledger)
    assert ledger.assetDepositPoints(vault_id, charlie_token).lastUpdate == 0
    empty_row = ledger.assetDepositPoints(0, ZERO_ADDRESS)

    elapsed = 8
    boa.env.time_travel(blocks=elapsed)
    _write_asset(mission_control, switchboard_bravo, charlie_token, [vault_id], 7, 9)
    _assert_ripe_delta(ledger, before, elapsed, 10, (25_00, 25_00, 25_00, 25_00))

    assert ledger.assetDepositPoints(vault_id, charlie_token).lastUpdate == 0
    assert ledger.assetDepositPoints(0, ZERO_ADDRESS) == empty_row
    assert ledger.globalDepositPoints().lastUpdate == boa.env.evm.patch.block_number
    totals = mission_control.totalPointsAllocs()
    assert totals.stakersPointsAllocTotal >= 7
    assert totals.voterPointsAllocTotal >= 9


def test_disabled_points_and_paused_checkpoints_revert_without_writes(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    mission_control,
    switchboard_bravo,
    switchboard_alpha,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _setup_points(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        mock_price_source,
        alpha_token,
        [vault_id],
        stakers=8,
        voters=8,
    )
    _init_row(
        performDeposit,
        lootbox,
        teller,
        bob,
        50 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        simple_erc20_vault,
        vault_id,
    )

    def _snapshot():
        return (
            mission_control.assetConfig(alpha_token).stakersPointsAlloc,
            mission_control.assetConfig(alpha_token).voterPointsAlloc,
            tuple(mission_control.totalPointsAllocs()),
            tuple(ledger.assetDepositPoints(vault_id, alpha_token)),
            tuple(ledger.globalDepositPoints()),
            tuple(ledger.ripeRewards()),
            ledger.ripeAvailForRewards(),
        )

    _write_rewards(mission_control, switchboard_alpha, arePointsEnabled=False)
    before_disabled = _snapshot()
    with pytest.raises(boa.BoaError) as err:
        _write_asset(mission_control, switchboard_bravo, alpha_token, [vault_id], 9, 8)
    assert has_dev_reason(err.value, "points disabled")
    assert _snapshot() == before_disabled

    _write_rewards(mission_control, switchboard_alpha, arePointsEnabled=True)
    lootbox.pause(True, sender=switchboard_alpha.address)
    before_lootbox = _snapshot()
    with pytest.raises(boa.BoaError) as err:
        _write_asset(mission_control, switchboard_bravo, alpha_token, [vault_id], 9, 8)
    assert has_dev_reason(err.value, "contract paused")
    assert _snapshot() == before_lootbox
    lootbox.pause(False, sender=switchboard_alpha.address)

    ledger.pause(True, sender=switchboard_alpha.address)
    before_ledger = _snapshot()
    with pytest.raises(boa.BoaError) as err:
        _write_asset(mission_control, switchboard_bravo, alpha_token, [vault_id], 9, 8)
    assert has_dev_reason(err.value, "not activated")
    assert _snapshot() == before_ledger
    ledger.pause(False, sender=switchboard_alpha.address)


def test_constructor_and_staged_mission_control_do_not_touch_live_lootbox(
    ripe_hq,
    defaults,
    switchboard_bravo,
    ledger,
    charlie_token,
    vault_book,
    simple_erc20_vault,
):
    before_points = tuple(ledger.globalDepositPoints())
    before_rewards = tuple(ledger.ripeRewards())
    before_avail = ledger.ripeAvailForRewards()

    defaults_base = boa.load("contracts/config/DefaultsBase.vy", name="ctor_defaults_base")
    boa.load(
        "contracts/data/MissionControl.vy",
        ripe_hq,
        defaults_base,
        name="ctor_mission_control",
    )
    staged = boa.load(
        "contracts/data/MissionControl.vy",
        ripe_hq,
        defaults,
        name="staged_mission_control",
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    staged.setAssetConfig(
        charlie_token,
        _asset_tuple([vault_id], 11, 13),
        sender=switchboard_bravo.address,
    )
    staged.setRipeRewardsConfig(
        (True, 33, 10_00, 20_00, 30_00, 40_00, 0, 0, 0),
        sender=switchboard_bravo.address,
    )

    assert tuple(ledger.globalDepositPoints()) == before_points
    assert tuple(ledger.ripeRewards()) == before_rewards
    assert ledger.ripeAvailForRewards() == before_avail
    assert staged.assetConfig(charlie_token).stakersPointsAlloc == 11
    assert staged.assetConfig(charlie_token).voterPointsAlloc == 13
    assert staged.rewardsConfig().ripePerBlock == 33


def test_unchanged_allocs_and_unrelated_reward_fields_skip_checkpoints(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    mission_control,
    switchboard_bravo,
    switchboard_alpha,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _setup_points(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        mock_price_source,
        alpha_token,
        [vault_id],
        stakers=6,
        voters=6,
        ripe_per_block=10,
    )
    _init_row(
        performDeposit,
        lootbox,
        teller,
        bob,
        40 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        simple_erc20_vault,
        vault_id,
    )
    lootbox.updateRipeRewards(sender=teller.address)
    row_last = ledger.assetDepositPoints(vault_id, alpha_token).lastUpdate
    ripe_last = ledger.ripeRewards().lastUpdate
    global_last = ledger.globalDepositPoints().lastUpdate

    boa.env.time_travel(blocks=7)
    mission_control.setAssetConfig(
        alpha_token,
        (
            [vault_id],
            6,
            6,
            123 * EIGHTEEN_DECIMALS,
            MAX_UINT256,
            0,
            DEBT_TERMS,
            False,
            False,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            0,
            (False, 0, 0, 0, 0),
            ZERO_ADDRESS,
            False,
        ),
        sender=switchboard_bravo.address,
    )
    _write_rewards(mission_control, switchboard_alpha, autoStakeRatio=40_00)

    assert ledger.assetDepositPoints(vault_id, alpha_token).lastUpdate == row_last
    assert ledger.ripeRewards().lastUpdate == ripe_last
    assert ledger.globalDepositPoints().lastUpdate == global_last
    assert mission_control.assetConfig(alpha_token).perUserDepositLimit == 123 * EIGHTEEN_DECIMALS
    assert mission_control.rewardsConfig().autoStakeRatio == 40_00

    lootbox.updateDepositPoints(
        ZERO_ADDRESS,
        vault_id,
        simple_erc20_vault,
        alpha_token,
        sender=teller.address,
    )
    ap = ledger.assetDepositPoints(vault_id, alpha_token)
    assert ap.ripeStakerPoints == 6 * 7
    assert ap.ripeVotePoints == 6 * 7


def test_unresolvable_historical_row_fails_closed(
    alpha_token,
    alpha_token_whale,
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    mock_price_source,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    mission_control,
    switchboard_bravo,
):
    vault_id = vault_book.getRegId(simple_erc20_vault)
    _setup_points(
        setGeneralConfig,
        setAssetConfig,
        setRipeRewardsConfig,
        mock_price_source,
        alpha_token,
        [vault_id],
        stakers=4,
        voters=4,
    )
    _init_row(
        performDeposit,
        lootbox,
        teller,
        bob,
        20 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
        simple_erc20_vault,
        vault_id,
    )
    before_alloc = mission_control.assetConfig(alpha_token).stakersPointsAlloc
    before_totals = tuple(mission_control.totalPointsAllocs())
    vault_book.eval(f"registry.addrInfo[{vault_id}].addr = empty(address)")

    with pytest.raises(boa.BoaError) as err:
        _write_asset(mission_control, switchboard_bravo, alpha_token, [vault_id], 5, 4)
    assert has_dev_reason(err.value, "unresolvable reward row")
    assert mission_control.assetConfig(alpha_token).stakersPointsAlloc == before_alloc
    assert tuple(mission_control.totalPointsAllocs()) == before_totals
